import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import json
from pathlib import Path

NUMERIC_COLS = ['cycle_time', 'queue_length', 'throughput', 'torque_nm', 'vibration_hz', 'temperature_c']

class PlantWideDataset(Dataset):
    def __init__(self, csv_file: str, window_size: int = 10, scaler_params_path: str = None, is_training: bool = True):
        self.window_size = window_size
        df = pd.read_csv(csv_file)
        
        # 1. Handle Missing Data (Imputation + Sensor Availability Mask)
        df['sensor_available'] = (~df['vibration_hz'].isna()).astype(float)
        
        # Compute plant defaults for imputation
        numeric_means = df[NUMERIC_COLS].mean()
        df[NUMERIC_COLS] = df[NUMERIC_COLS].fillna(numeric_means)
        
        # Determine or load standardization parameters
        params_file = Path(scaler_params_path) if scaler_params_path else (Path(__file__).parent / "scaler_params.json")
        
        if is_training or not params_file.exists():
            means = df[NUMERIC_COLS].mean().to_dict()
            stds = df[NUMERIC_COLS].std().replace(0, 1.0).fillna(1.0).to_dict()
            self.scaler_params = {
                "means": means,
                "stds": stds,
                "impute_means": numeric_means.to_dict()
            }
            try:
                with open(params_file, "w") as f:
                    json.dump(self.scaler_params, f, indent=2)
            except Exception:
                pass
        else:
            with open(params_file, "r") as f:
                self.scaler_params = json.load(f)
                
        # Normalize numeric columns to prevent LSTM gradient saturation
        for col in NUMERIC_COLS:
            mean_val = self.scaler_params["means"][col]
            std_val = self.scaler_params["stds"][col] if self.scaler_params["stds"][col] > 1e-6 else 1.0
            df[col] = (df[col] - mean_val) / std_val
        
        # 2. Pivot so each row contains all 40 stations' features at timestamp t
        feature_pivot = df.pivot(
            index='time_step', 
            columns='station_id', 
            values=NUMERIC_COLS + ['sensor_available']
        )
        
        # 3. Targets: Extract both bottleneck and defect risks
        risk_pivot = df.pivot(index='time_step', columns='station_id', values='bottleneck_risk')
        defect_pivot = df.pivot(index='time_step', columns='station_id', values='defect_risk')
        
        self.y_bn, self.y_def = [], []
        
        for idx in range(len(risk_pivot)):
            active_bn = risk_pivot.iloc[idx][risk_pivot.iloc[idx] == 1].index.tolist()
            self.y_bn.append(int(active_bn[0]) if active_bn else 0)
            
            active_def = defect_pivot.iloc[idx][defect_pivot.iloc[idx] == 1].index.tolist()
            self.y_def.append(int(active_def[0]) if active_def else 0)
                
        # 4. Create sliding temporal windows
        feature_matrix = feature_pivot.values
        self.X, self.y_bn_window, self.y_def_window = [], [], []
        
        for i in range(len(feature_matrix) - window_size):
            self.X.append(feature_matrix[i : i + window_size])
            self.y_bn_window.append(self.y_bn[i + window_size])
            self.y_def_window.append(self.y_def[i + window_size])
            
        self.X = torch.tensor(np.array(self.X), dtype=torch.float32)
        self.y_bn_window = torch.tensor(np.array(self.y_bn_window), dtype=torch.long)
        self.y_def_window = torch.tensor(np.array(self.y_def_window), dtype=torch.long)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int):
        return self.X[idx], self.y_bn_window[idx], self.y_def_window[idx]

if __name__ == "__main__":
    dataset = PlantWideDataset("data/raw/plant_twin_data.csv", window_size=10)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
    
    for batch_x, batch_bn, batch_def in dataloader:
        print(f"Input Tensor Shape: {batch_x.shape}")
        print(f"Batch Bottleneck Targets: {batch_bn[:5]}")
        print(f"Batch Defect Targets: {batch_def[:5]}")
        break