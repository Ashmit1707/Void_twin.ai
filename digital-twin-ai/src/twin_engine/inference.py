import json
from pathlib import Path
import pandas as pd
import torch
from src.twin_engine.model import DigitalTwinMTL

NUMERIC_COLS = ['cycle_time', 'queue_length', 'throughput', 'torque_nm', 'vibration_hz', 'temperature_c']

class TwinPredictor:
    def __init__(self, model_weights_path: str = "twin_mtl_model.pth", num_stations: int = 40):
        self.num_stations = num_stations
        
        # 7 features per station (6 numeric + 1 sensor_available mask) * 40 stations = 280
        self.input_dim = len(NUMERIC_COLS + ['sensor_available']) * num_stations
        
        self.model = DigitalTwinMTL(input_dim=self.input_dim, hidden_dim=64, num_layers=2, num_classes=41)
        self.model.load_state_dict(torch.load(model_weights_path, weights_only=True, map_location=torch.device('cpu')))
        self.model.eval()
        
        # Load standardization parameters
        params_file = Path(__file__).parent / "scaler_params.json"
        if params_file.exists():
            with open(params_file, "r") as f:
                self.scaler_params = json.load(f)
        else:
            self.scaler_params = None

    def run_prediction(self, recent_telemetry_df: pd.DataFrame) -> dict:
        df = recent_telemetry_df.copy()
        
        # 1. Preprocessing: Handle missing legacy sensors
        df['sensor_available'] = (~df['vibration_hz'].isna()).astype(float)
        
        # Impute missing values with learned plant defaults
        if self.scaler_params and "impute_means" in self.scaler_params:
            for col in NUMERIC_COLS:
                if col in self.scaler_params["impute_means"]:
                    df[col] = df[col].fillna(self.scaler_params["impute_means"][col])
        df[NUMERIC_COLS] = df[NUMERIC_COLS].fillna(df[NUMERIC_COLS].mean())
        
        # Standardize numeric columns
        if self.scaler_params and "means" in self.scaler_params:
            for col in NUMERIC_COLS:
                mean_val = self.scaler_params["means"].get(col, 0.0)
                std_val = self.scaler_params["stds"].get(col, 1.0)
                std_val = std_val if std_val > 1e-6 else 1.0
                df[col] = (df[col] - mean_val) / std_val
            
        # 2. Pivot into tensor shape [1, sequence_length, 280]
        values_to_pivot = NUMERIC_COLS + ['sensor_available']
        feature_pivot = df.pivot(index='time_step', columns='station_id', values=values_to_pivot).values
        
        input_tensor = torch.tensor(feature_pivot, dtype=torch.float32).unsqueeze(0)
        
        # 3. Model Inference
        with torch.no_grad():
            bn_logits, def_logits = self.model(input_tensor)
            
            bn_conf, pred_bn = torch.max(torch.softmax(bn_logits, dim=1), dim=1)
            def_conf, pred_def = torch.max(torch.softmax(def_logits, dim=1), dim=1)
            
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