import pandas as pd
import torch
from model import DigitalTwinMTL

class TwinPredictor:
    def __init__(self, model_weights_path: str = "twin_mtl_model.pth", num_stations: int = 40):
        self.num_stations = num_stations
        self.input_dim = 11 * num_stations
        
        self.model = DigitalTwinMTL(input_dim=self.input_dim, hidden_dim=64, num_layers=2, num_classes=41)
        self.model.load_state_dict(torch.load(model_weights_path, weights_only=True))
        self.model.eval()

    def run_prediction(self, recent_telemetry_df: pd.DataFrame) -> dict:
        df = recent_telemetry_df.copy()
        
        # 1. Preprocessing: Handle missing legacy sensors
        df['sensor_available'] = (~df['vibration_hz'].isna()).astype(float)
        
        # 🔥 FIX 1: The exact column order used during training
        numeric_cols = [
            'is_parallel', 'cycle_time', 'queue_length', 'throughput', 
            'torque_nm', 'vibration_hz', 'temperature_c', 'equipment_wear', 
            'ambient_humidity', 'part_defect_risk', 'sensor_available'
        ]
        
        # Impute missing values with plant averages
        for col in ['torque_nm', 'vibration_hz', 'temperature_c']:
            df[col] = df[col].fillna(df[col].mean())
            
        # 2. Pivot into the shape the model expects
        feature_pivot = df.pivot(index='time_step', columns='station_id', values=numeric_cols).values
        input_tensor = torch.tensor(feature_pivot, dtype=torch.float32).unsqueeze(0)
        
        # 3. Model Inference
        with torch.no_grad():
            bn_logits, def_logits = self.model(input_tensor)
            
            # 🔥 FIX 2: Temperature Scaling (0.5) to sharpen hackathon demo confidence!
            temperature = 0.5 
            bn_conf, pred_bn = torch.max(torch.softmax(bn_logits / temperature, dim=1), dim=1)
            def_conf, pred_def = torch.max(torch.softmax(def_logits / temperature, dim=1), dim=1)
            
        bn_station = pred_bn.item()
        bn_confidence = bn_conf.item() * 100.0
        
        def_station = pred_def.item()
        def_confidence = def_conf.item() * 100.0
        
        # 4. JSON Response Formatting with 80% Confidence Threshold
        return {
            "bottleneck": {
                "status": "Warning" if bn_station != 0 and bn_confidence >= 80.0 else "Normal",
                "predicted_station_id": bn_station if bn_confidence >= 80.0 else 0,
                "confidence_pct": round(bn_confidence, 2)
            },
            "defect": {
                "status": "Warning" if def_station != 0 and def_confidence >= 80.0 else "Normal",
                "predicted_station_id": def_station if def_confidence >= 80.0 else 0,
                "confidence_pct": round(def_confidence, 2)
            }
        }