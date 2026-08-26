import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

class PlantWideDataset(Dataset):
    def __init__(self, csv_file: str, window_size: int = 10):
        self.window_size = window_size
        df = pd.read_csv(csv_file)
        
        # 1. Handle Missing Data (Imputation + Sensor Availability Mask)
        # Identify columns with missing readings
        numeric_cols = ['cycle_time', 'queue_length', 'throughput', 'torque_nm', 'vibration_hz', 'temperature_c']
        
        # Add a confidence mask: 1.0 = sensor present, 0.0 = imputed
        df['sensor_available'] = (~df['vibration_hz'].isna()).astype(float)
        
        # Fill missing values with historical defaults
        df.fillna(df.mean(numeric_only=True), inplace=True)
        
        # 2. Pivot so each row contains all 40 stations' features at timestamp t
        feature_pivot = df.pivot(
            index='time_step', 
            columns='station_id', 
            values=numeric_cols + ['sensor_available']
        )
        
# 3. Targets: Extract both bottleneck and defect risks
        risk_pivot = df.pivot(index='time_step', columns='station_id', values='bottleneck_risk')
        defect_pivot = df.pivot(index='time_step', columns='station_id', values='defect_risk')
        
        self.y_bn, self.y_def = [], []
        
        for idx in range(len(risk_pivot)):
            # Find the station ID (1-40) or 0 if normal
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
        # Now returns THREE items instead of two!
        return self.X[idx], self.y_bn_window[idx], self.y_def_window[idx]

if __name__ == "__main__":
    dataset = PlantWideDataset("plant_twin_data.csv", window_size=10)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
    
    for batch_x, batch_y in dataloader:
        print(f"Input Tensor Shape: {batch_x.shape}")
        print("Exact Target Station IDs in this batch:")
        print(batch_y)
        break