import random
import math
import numpy as np

class AnomalyInjector:
    """
    Generates realistic, stateful variations in cycle times 
    AND sensor readings (temperature, voltage, etc.) to generate the CSV dataset.
    """

    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)
            
        self.station_drift_states = {}

    def generate_station_telemetry(self, station):
        """
        Calculates the cycle time and sensor values for a single vehicle passing through.
        Returns a dictionary that will be appended to the CSV.
        """
        # 1. Initialize station state
        if station.station_id not in self.station_drift_states:
            self.station_drift_states[station.station_id] = 0.0
            
        current_drift = self.station_drift_states[station.station_id]

        # 2. Anomaly Trigger & Progression (The Drift)
        if current_drift == 0.0 and random.random() < 0.02:
            self.station_drift_states[station.station_id] = 0.10
        elif current_drift > 0.0:
            self.station_drift_states[station.station_id] += random.uniform(0.01, 0.05)
            # Cap at 80% degradation
            if self.station_drift_states[station.station_id] > 0.80:
                self.station_drift_states[station.station_id] = 0.80

        # Update the variable after progression
        current_drift = self.station_drift_states[station.station_id]

        # 3. Calculate Final Cycle Time
        degraded_base_time = station.expected_cycle_time * (1 + current_drift)
        actual_time = random.gauss(mu=degraded_base_time, sigma=(station.expected_cycle_time * 0.02))

        # 4. Generate Sensor Data based on the blueprint and the drift
        telemetry = {
            "station_id": station.station_id,
            "cycle_time": round(actual_time, 2)
        }

        for sensor in station.active_sensors:
            if current_drift >= 0.80:
                # SENSOR BURNOUT: Maximum degradation reached, hardware fails.
                telemetry[sensor] = np.nan
            else:
                # SENSOR WORKING: Generate normal data + degradation heat/noise
                if "temperature" in sensor:
                    # Baseline 85C, goes up as drift goes up
                    base_temp = 85.0 + (current_drift * 100) 
                    telemetry[sensor] = round(random.gauss(mu=base_temp, sigma=2.0), 1)
                elif "voltage" in sensor:
                    # Baseline 220V, drops slightly as drift goes up
                    base_volt = 220.0 - (current_drift * 20)
                    telemetry[sensor] = round(random.gauss(mu=base_volt, sigma=1.5), 1)
                else:
                    # Generic random data for any other sensor type
                    telemetry[sensor] = round(random.uniform(10.0, 50.0), 2)

        return telemetry

    def repair_station(self, station_id):
        """External method to reset a station's health back to normal."""
        if station_id in self.station_drift_states:
            self.station_drift_states[station_id] = 0.0