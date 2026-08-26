import pandas as pd
import networkx as nx

# Direct import since they are in the same folder
from defect_tracker import LatentDefectTracker

def run_dag_defect_test():
    print("--- Starting Latent Defect Tracker Test ---")
    
    # 1. Load factory data
    # Path assumes you are running the script from the root 'digital-twin-ai' folder
    csv_path = 'data/raw/plant_twin_data.csv'
    
    try:
        raw_data = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find CSV at {csv_path}. Ensure you run this from the project root.")
        return

    # 2. Initialize and train the detector on the "healthy" baseline
    tracker = LatentDefectTracker()
    tracker.train_healthy_baseline(raw_data)
    
    # 3. Build a test DAG simulating a branching factory floor
    test_dag = nx.DiGraph()
    test_dag.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 4)])
    
    # 4. Simulate a vehicle that traveled through stations: 1 -> 3 -> 4
    vehicle_path = raw_data[raw_data['station_id'].isin([1, 3, 4])].head(3).copy()
    
    # 5. The Sabotage! 
    # We artificially spike the vibration at Station 3 to simulate a failing tool.
    vehicle_path.loc[vehicle_path['station_id'] == 3, 'vibration_hz'] = 300.0 
    
    print("\n--- Traversing DAG and Tracing Root Cause ---")
    
    # 6. Trace it starting from the final inspection point (Station 4)
    root_cause = tracker.trace_root_cause(vehicle_path, test_dag, final_station=4)
    
    # 7. Evaluate the result
    if root_cause == 3.0 or root_cause == 3:
        print("\n✅ TEST PASSED: Successfully isolated the hidden defect at Station 3!")
    else:
        print(f"\n❌ TEST FAILED: Expected Station 3, but the model flagged {root_cause}.")

if __name__ == "__main__":
    run_dag_defect_test()