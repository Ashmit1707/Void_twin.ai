import pandas as pd
import numpy as np

# Number of time steps you want to generate (e.g., 50 steps * 40 stations = 2000 rows)
TIME_STEPS = 50 
NUM_STATIONS = 40

print(f"Generating pure random noise for {TIME_STEPS} time steps...")

data = []
# Randomly select 10 stations to act as "legacy" stations missing sensor data
sensor_poor_stations = np.random.choice(range(1, NUM_STATIONS + 1), 10, replace=False)

for t in range(TIME_STEPS):
    for station_id in range(1, NUM_STATIONS + 1):
        
        # Completely random values for every metric
        is_parallel = np.random.choice([0, 1], p=[0.9, 0.1])
        cycle_time = np.random.uniform(35.0, 75.0)
        queue_length = np.random.randint(0, 10)
        throughput = np.random.uniform(2.0, 15.0)
        
        equipment_wear = np.random.uniform(0.0, 1.0)
        ambient_humidity = np.random.uniform(40.0, 70.0)
        part_defect_risk = np.random.uniform(0.0, 0.9)
        
        # Inject random NaNs for legacy stations
        if station_id in sensor_poor_stations:
            torque, vibration, temp = np.nan, np.nan, np.nan
        else:
            torque = np.random.uniform(40.0, 70.0)
            vibration = np.random.uniform(90.0, 160.0)
            temp = np.random.uniform(20.0, 60.0)

        # Randomize the target columns (mostly 0, rare 1s) just to fill the CSV shape
        bottleneck_risk = np.random.choice([0, 1], p=[0.95, 0.05])
        defect_risk = np.random.choice([0, 1], p=[0.95, 0.05])

        data.append([
            t, station_id, is_parallel, cycle_time, queue_length, throughput,
            torque, vibration, temp, equipment_wear, ambient_humidity,
            part_defect_risk, bottleneck_risk, defect_risk
        ])

columns = [
    'time_step', 'station_id', 'is_parallel', 'cycle_time', 'queue_length',
    'throughput', 'torque_nm', 'vibration_hz', 'temperature_c',
    'equipment_wear', 'ambient_humidity', 'part_defect_risk', 
    'bottleneck_risk', 'defect_risk'
]

df = pd.DataFrame(data, columns=columns)
df.to_csv("random_test_data.csv", index=False)

print(f"Done! {len(df)} rows of complete random noise saved to 'random_test_data.csv'.")