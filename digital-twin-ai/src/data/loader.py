import pandas as pd
import numpy as np
from pathlib import Path
from src.simulation.plant_config import StationConfig, StationType, SensorMaturity

# Navigate up two directories to reach the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "plant_twin_data.csv"
)

def load_plant_data(filepath=None):
    """Loads the raw telemetry CSV and normalizes station IDs safely."""
    if filepath is None:
        filepath = DEFAULT_DATA_PATH

    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    df = pd.read_csv(filepath)
    
    # --- BULLETPROOF ID CONVERSION ---
    if 'station_id' in df.columns:
        def format_id(x):
            if pd.isna(x):
                return x
            try:
                num = float(x)
                return f"S{int(num):02d}"  # Converts 1.0 -> S01
            except ValueError:
                return str(x).strip()
                
        df['station_id'] = df['station_id'].apply(format_id)
    # ---------------------------------
    
    return df

def load_station_configs(filepath=None):
    """
    Dynamically builds the factory architecture by scanning the final CSV schema.
    """
    df = load_plant_data(filepath)
    
    # Explicitly list ALL business metrics and labels so they aren't marked as physical sensors
    non_sensor_cols = [
        'time_step', 'station_id', 'is_parallel', 'cycle_time', 
        'queue_length', 'throughput', 'equipment_wear', 
        'ambient_humidity', 'part_defect_risk', 'bottleneck_risk', 'defect_risk'
    ]
    
    potential_sensors = [col for col in df.columns if col not in non_sensor_cols]

    factory_stations = {}

    for station_id in df['station_id'].dropna().unique():
        station_data = df[df['station_id'] == station_id]
        
        # Calculate baseline speed
        baseline_time = station_data['cycle_time'].median()
        if pd.isna(baseline_time):
            baseline_time = 60.0
            
        # Auto-detect active hardware sensors (torque, vibration, temperature)
        active_sensors = []
        for sensor in potential_sensors:
            if station_data[sensor].notna().any():
                active_sensors.append(sensor)
                
        # Auto-calculate maturity
        sensor_count = len(active_sensors)
        if sensor_count == 0:
            maturity = SensorMaturity.DARK
        elif sensor_count < 3:
            maturity = SensorMaturity.PARTIAL
        else:
            maturity = SensorMaturity.FULL

        # Guess station type for UI
        s_type = StationType.UNKNOWN
        s_id_lower = str(station_id).lower()
        if "weld" in s_id_lower:
            s_type = StationType.WELDING
        elif "paint" in s_id_lower:
            s_type = StationType.PAINT
        elif "inspect" in s_id_lower or "s05" in s_id_lower:
            s_type = StationType.INSPECTION
        else:
            s_type = StationType.ASSEMBLY

        # Build config
        station = StationConfig(
            station_id=str(station_id),
            expected_cycle_time=round(baseline_time, 2),
            sensor_maturity=maturity,
            active_sensors=active_sensors,
            station_type=s_type,
            buffer_capacity=5
        )
        
        factory_stations[str(station_id)] = station

    return factory_stations