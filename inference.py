import torch
import pandas as pd
from model import BottleneckPredictorLSTM

def run_prediction(recent_telemetry_df: pd.DataFrame, model_path="bottleneck_lstm_model.pth"):
    """
    Backend calls this function with a DataFrame containing the last 10 time steps 
    across all 40 stations.
    """
    # 1. Define the features we used in training
    numeric_cols = [
        'cycle_time', 'queue_length', 'throughput', 'torque_nm', 
        'vibration_hz', 'temperature_c', 'equipment_wear', 
        'ambient_humidity', 'part_defect_risk'
    ]
    
    # 2. Preprocess just like in dataset.py
    recent_telemetry_df['sensor_available'] = (~recent_telemetry_df['vibration_hz'].isna()).astype(float)
    recent_telemetry_df.fillna(recent_telemetry_df.mean(numeric_only=True), inplace=True)
    
    # Pivot to get shape (TimeSteps, Stations * Features)
    feature_pivot = recent_telemetry_df.pivot(
        index='time_step', columns='station_id', 
        values=numeric_cols + ['sensor_available']
    ).values
    
    # 3. Convert to PyTorch Tensor: Shape (1 Batch, 10 TimeSteps, TotalFeatures)
    input_tensor = torch.tensor(feature_pivot, dtype=torch.float32).unsqueeze(0)
    
    # 4. Load Model and Predict
    input_dim = input_tensor.shape[2]
    model = BottleneckPredictorLSTM(input_dim=input_dim, hidden_dim=64, num_layers=2, num_classes=41)
    model.load_state_dict(torch.load(model_path, weights_only=True))
    model.eval()
    
    with torch.no_grad():
        logits = model(input_tensor)
        confidence, pred_station = torch.max(torch.softmax(logits, dim=1), dim=1)
        
    # 5. Return clean data for the backend to send to the frontend
    return {
        "predicted_station": pred_station.item(),
        "confidence_pct": round(confidence.item() * 100.0, 2),
        "status": "Warning" if pred_station.item() != 0 and confidence.item() > 0.8 else "Normal"
    }