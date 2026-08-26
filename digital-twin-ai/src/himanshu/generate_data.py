import pandas as pd
import numpy as np

np.random.seed(42)

NUM_STATIONS = 40
TIME_STEPS = 500

# 10 stations with legacy/uneven sensor coverage
sensor_poor_stations = np.random.choice(range(1, NUM_STATIONS + 1), 10, replace=False)

# Parallel branch definitions
parallel_stations = {18, 19, 33, 34}

data = []

for t in range(TIME_STEPS):
    # Environmental shifts
    ambient_temp = 24.0 + 3.0 * np.sin(2 * np.pi * t / 250) + np.random.normal(0, 0.5)
    ambient_humidity = 55.0 + 10.0 * np.cos(2 * np.pi * t / 250) + np.random.normal(0, 1.0)
    
    # Intermittent batch defect spikes
    batch_defect_severity = 0.8 if (140 <= t <= 170 or 380 <= t <= 410) else 0.05
    
    for station_id in range(1, NUM_STATIONS + 1):
        # Equipment wear
        base_wear = (t / TIME_STEPS) * 0.4
        equipment_wear = np.clip(base_wear + np.random.normal(0.05, 0.02), 0.0, 1.0)
        
        # Operator variation
        operator_jitter = np.random.normal(0, 1.8) if (26 <= station_id <= 40) else np.random.normal(0, 0.6)
        
        base_cycle_time = 45.0 + operator_jitter + (equipment_wear * 8.0)
        queue_length = max(0, int(np.random.normal(3, 1)))
        
        if station_id in parallel_stations:
            throughput = np.random.normal(5.0, 0.5)
            is_parallel = 1
        else:
            throughput = np.random.normal(10.0, 1.0)
            is_parallel = 0

        if station_id in sensor_poor_stations:
            torque, vibration, temp = np.nan, np.nan, np.nan
        else:
            torque = np.random.normal(50.0, 4.0) + (equipment_wear * 12.0)
            vibration = np.random.normal(120.0, 8.0) + (equipment_wear * 25.0)
            temp = ambient_temp + 45.0 + np.random.normal(0, 1.5)

        # Bottleneck simulation
        bottleneck_risk = 0
        if t > 300:
            if station_id == 20:
                base_cycle_time += (t - 300) * 0.12
                queue_length += int((t - 300) * 0.06)
                equipment_wear = np.clip(equipment_wear + 0.4, 0.0, 1.0)
                bottleneck_risk = 1
            elif station_id == 21:
                queue_length = 0
                throughput = 0.0

        # Physical defect simulation
        defect_risk = 0
        if equipment_wear > 0.8 and (torque > 55.0 or vibration > 140.0):
            defect_risk = 1

        data.append([
            t, station_id, is_parallel, base_cycle_time, queue_length, throughput,
            torque, vibration, temp, equipment_wear, ambient_humidity,
            batch_defect_severity, bottleneck_risk, defect_risk
        ])

# IMPORTANT: defect_risk is now included here!
columns = [
    'time_step', 'station_id', 'is_parallel', 'cycle_time', 'queue_length',
    'throughput', 'torque_nm', 'vibration_hz', 'temperature_c',
    'equipment_wear', 'ambient_humidity', 'part_defect_risk', 
    'bottleneck_risk', 'defect_risk'
]

df = pd.DataFrame(data, columns=columns)
df.to_csv("plant_twin_data.csv", index=False)
print(f"Data generated successfully: {len(df)} records saved to 'plant_twin_data.csv'.")