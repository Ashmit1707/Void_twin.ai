import pandas as pd
import networkx as nx
from sklearn.ensemble import IsolationForest
from typing import List, Tuple, Optional

class LatentDefectTracker:
    def __init__(self, feature_columns: List[str]):
        # contamination is the expected percentage of anomalies in normal data
        self.anomaly_detector = IsolationForest(contamination=0.05, random_state=42)
        self.features = feature_columns

    def train_healthy_baseline(self, historical_df: pd.DataFrame):
        print(f"Training Isolation Forest on features: {self.features}")
        # We ONLY train on the specific features discovered by loader.py
        # This prevents the AI from "cheating" by looking at target labels
        X = historical_df[self.features].fillna(-1)
        self.anomaly_detector.fit(X)
        print("Baseline established.")

    def get_temporal_upstream_path(self, dag: nx.DiGraph, final_station: str, defect_time_step: int) -> List[Tuple[str, int]]:
        """
        Executes a Time-Space Reverse BFS.
        Moves backward through the factory graph AND backward in time simultaneously.
        """
        path_tuples = []
        # Queue stores: (station_id, time_step)
        queue = [(final_station, defect_time_step)]
        visited = set()

        while queue:
            current_station, current_time = queue.pop(0)
            
            if (current_station, current_time) in visited:
                continue
                
            visited.add((current_station, current_time))
            path_tuples.append((current_station, current_time))

            # If we hit the beginning of the simulation (time 0), we can't look further back
            if current_time <= 0:
                continue

            # Find machines that fed into this one, and schedule them for 1 time step ago
            if current_station in dag:
                for pred in dag.predecessors(current_station):
                    queue.append((pred, current_time - 1))

        return path_tuples

    def trace_root_cause(self, telemetry_df: pd.DataFrame, dag: nx.DiGraph, final_station: str, defect_time_step: int) -> Optional[str]:
        """
        Isolates the historical data for the specific flawed timeline and finds the anomaly.
        """
        # 1. Get the exact coordinates (Station + Time) the flawed part existed in
        target_coordinates = self.get_temporal_upstream_path(dag, final_station, defect_time_step)
        
        # 2. Extract ONLY those specific rows from the massive CSV using an inner merge
        coord_df = pd.DataFrame(target_coordinates, columns=['station_id', 'time_step'])
        path_df = pd.merge(telemetry_df, coord_df, on=['station_id', 'time_step'], how='inner')
        
        if path_df.empty:
            print("No historical telemetry found for this temporal path.")
            return None
            
        # Sort chronologically so we find the FIRST thing that broke
        path_df = path_df.sort_values(by='time_step')
        
        # 3. Anomaly Detection
        X_vehicle = path_df[self.features].fillna(-1)
        path_df['is_anomaly'] = self.anomaly_detector.predict(X_vehicle)
        
        # Isolation Forest outputs -1 for anomalies and 1 for normal
        anomalies = path_df[path_df['is_anomaly'] == -1]
        
        if not anomalies.empty:
            root_cause = anomalies.iloc[0]
            print(f"ROOT CAUSE FOUND: Station {root_cause['station_id']} at Time Step {root_cause['time_step']}")
            return str(root_cause['station_id'])
        else:
            print("No anomaly detected in this upstream temporal path.")
            return None