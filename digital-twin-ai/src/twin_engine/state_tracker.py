import pandas as pd


class FactoryStateTracker:
    """
    Reconstructs the state of the factory from telemetry data.

    The tracker is deliberately independent of the factory topology.
    Topology is handled separately by the topology/graph layer.

    Main responsibilities:
        - Track station state
        - Track queues
        - Track sensor availability
        - Track bottleneck status
        - Calculate factory-level WIP
        - Compare current state with previous time step
    """

    def __init__(self, data):

        self.data = data.copy()

        # --------------------------------------------------
        # Normalize station IDs
        # --------------------------------------------------

        self.data["station_id"] = (
            self.data["station_id"]
            .apply(self._normalize_station_id)
        )

        # --------------------------------------------------
        # Sort data chronologically
        # --------------------------------------------------

        self.data = self.data.sort_values(
            ["time_step", "station_id"]
        ).reset_index(drop=True)

        # --------------------------------------------------
        # Available stations
        # --------------------------------------------------

        self.stations = sorted(
            self.data["station_id"].unique()
        )

        # --------------------------------------------------
        # Available time steps
        # --------------------------------------------------

        self.time_steps = sorted(
            self.data["time_step"].unique()
        )

        # --------------------------------------------------
        # Current state
        # --------------------------------------------------

        self.current_time_step = None

        self.station_states = {}

        # --------------------------------------------------
        # Previous state
        # --------------------------------------------------

        self.previous_station_states = {}

        # --------------------------------------------------
        # Initialize
        # --------------------------------------------------

        self._initialize_station_states()

    # ======================================================
    # STATION ID NORMALIZATION
    # ======================================================

    @staticmethod
    def _normalize_station_id(station_id):

        """
        Convert numeric station IDs into the standard format.

        Example:

            1  -> S01
            5  -> S05
            40 -> S40

        Existing string IDs are preserved.
        """

        try:

            station_number = int(station_id)

            return f"S{station_number:02d}"

        except (ValueError, TypeError):

            return str(station_id)

    # ======================================================
    # INITIALIZE STATION STATES
    # ======================================================

    def _initialize_station_states(self):

        """
        Create an empty state object for every station.
        """

        for station_id in self.stations:

            self.station_states[station_id] = {

                "station_id": station_id,

                "cycle_time": None,

                "queue_length": 0,

                "throughput": 0.0,

                "torque_nm": None,

                "vibration_hz": None,

                "temperature_c": None,

                "sensor_available": False,

                "bottleneck_risk": 0,

                "queue_change": 0,

                "cycle_time_change": 0.0,

                "throughput_change": 0.0,

                "last_updated": None,
            }

    # ======================================================
    # GET ROW FOR STATION + TIME
    # ======================================================

    def _get_station_row(
        self,
        station_id,
        time_step
    ):

        rows = self.data[
            (self.data["station_id"] == station_id)
            &
            (self.data["time_step"] == time_step)
        ]

        if rows.empty:

            return None

        return rows.iloc[0]

        # ======================================================
        # UPDATE FACTORY STATE
        # ======================================================

    def update(self, time_step):

        """
        Reconstruct the factory state at a given time step.
        """

        if time_step not in self.time_steps:

            raise ValueError(
                f"Time step {time_step} "
                f"does not exist in dataset."
            )

        # --------------------------------------------------
        # Save previous state
        # --------------------------------------------------

        if self.current_time_step is None:

            # First update: there is no previous state yet
            self.previous_station_states = {}

        else:

            self.previous_station_states = {
                station_id: state.copy()
                for station_id, state
                in self.station_states.items()
            }

        # --------------------------------------------------
        # Set current time
        # --------------------------------------------------

        self.current_time_step = time_step

        # --------------------------------------------------
        # Update every station
        # --------------------------------------------------

        for station_id in self.stations:

            row = self._get_station_row(
                station_id,
                time_step
            )

            if row is None:
                continue

            state = self.station_states[station_id]

            # --------------------------------------------------
            # Production data
            # --------------------------------------------------

            state["cycle_time"] = float(
                row["cycle_time"]
            )

            state["queue_length"] = int(
                row["queue_length"]
            )

            state["throughput"] = float(
                row["throughput"]
            )

            # --------------------------------------------------
            # Sensor data
            # --------------------------------------------------

            state["torque_nm"] = row["torque_nm"]

            state["vibration_hz"] = row["vibration_hz"]

            state["temperature_c"] = row["temperature_c"]

            # --------------------------------------------------
            # Sensor availability
            # --------------------------------------------------

            sensor_values = [
                row["torque_nm"],
                row["vibration_hz"],
                row["temperature_c"],
            ]

            state["sensor_available"] = not all(
                pd.isna(value)
                for value in sensor_values
            )

            # --------------------------------------------------
            # Bottleneck risk
            # --------------------------------------------------

            state["bottleneck_risk"] = int(
                row["bottleneck_risk"]
            )

            # --------------------------------------------------
            # Calculate changes from previous timestep
            # --------------------------------------------------

            if station_id in self.previous_station_states:

                previous = (
                    self.previous_station_states[
                        station_id
                    ]
                )

                # Queue change
                if previous["queue_length"] is not None:

                    state["queue_change"] = (
                        state["queue_length"]
                        -
                        previous["queue_length"]
                    )

                else:

                    state["queue_change"] = 0

                # Cycle-time change
                if previous["cycle_time"] is not None:

                    state["cycle_time_change"] = (
                        state["cycle_time"]
                        -
                        previous["cycle_time"]
                    )

                else:

                    state["cycle_time_change"] = 0.0

                # Throughput change
                if previous["throughput"] is not None:

                    state["throughput_change"] = (
                        state["throughput"]
                        -
                        previous["throughput"]
                    )

                else:

                    state["throughput_change"] = 0.0

            else:

                # First observation of this station
                state["queue_change"] = 0

                state["cycle_time_change"] = 0.0

                state["throughput_change"] = 0.0

            # --------------------------------------------------
            # Last update
            # --------------------------------------------------

            state["last_updated"] = time_step

    # ======================================================
    # GET STATION STATE
    # ======================================================

    def get_station_state(
        self,
        station_id
    ):

        station_id = self._normalize_station_id(
            station_id
        )

        if station_id not in self.station_states:

            raise ValueError(
                f"Unknown station: {station_id}"
            )

        return self.station_states[
            station_id
        ].copy()

    # ======================================================
    # GET COMPLETE FACTORY STATE
    # ======================================================

    def get_factory_state(self):

        """
        Return a copy of the complete current
        factory state.
        """

        return {
            station_id: state.copy()
            for station_id, state
            in self.station_states.items()
        }

    # ======================================================
    # GET WIP
    # ======================================================

    def get_total_wip(self):

        """
        Calculate total station-level WIP.

        Since this dataset contains queue lengths,
        the first version uses:

            WIP = sum(queue_length)
        """

        return sum(
            state["queue_length"]
            for state
            in self.station_states.values()
        )

    # ======================================================
    # GET BOTTLENECK STATIONS
    # ======================================================

    def get_bottleneck_stations(self):

        """
        Return stations whose current bottleneck label
        is 1.
        """

        return [
            station_id
            for station_id, state
            in self.station_states.items()
            if state["bottleneck_risk"] == 1
        ]

    # ======================================================
    # GET SENSOR-DARK STATIONS
    # ======================================================

    def get_sensor_dark_stations(self):

        """
        Return stations where all three sensor
        measurements are unavailable.
        """

        return [
            station_id
            for station_id, state
            in self.station_states.items()
            if not state["sensor_available"]
        ]

    # ======================================================
    # GET HIGHEST QUEUES
    # ======================================================

    def get_highest_queue_stations(
        self,
        top_n=5
    ):

        """
        Return the stations with the largest queues.
        """

        sorted_stations = sorted(
            self.station_states.items(),
            key=lambda item:
                item[1]["queue_length"],
            reverse=True
        )

        return sorted_stations[:top_n]

    # ======================================================
    # GET FASTEST / SLOWEST STATIONS
    # ======================================================

    def get_slowest_stations(
        self,
        top_n=5
    ):

        """
        Return stations with the highest cycle times.
        """

        sorted_stations = sorted(
            self.station_states.items(),
            key=lambda item:
                item[1]["cycle_time"],
            reverse=True
        )

        return sorted_stations[:top_n]

    # ======================================================
    # GET QUEUE GROWTH
    # ======================================================

    def get_queue_growth_stations(
        self,
        top_n=5
    ):

        """
        Return stations where queues are increasing
        most rapidly between consecutive observations.
        """

        sorted_stations = sorted(
            self.station_states.items(),
            key=lambda item:
                item[1]["queue_change"],
            reverse=True
        )

        return sorted_stations[:top_n]

    # ======================================================
    # FACTORY SUMMARY
    # ======================================================

    def get_summary(self):

        """
        Return a compact factory-level summary.
        """

        total_wip = self.get_total_wip()

        bottlenecks = (
            self.get_bottleneck_stations()
        )

        dark_stations = (
            self.get_sensor_dark_stations()
        )

        highest_queue = (
            self.get_highest_queue_stations(1)
        )

        if highest_queue:

            highest_queue_station = (
                highest_queue[0][0]
            )

            highest_queue_value = (
                highest_queue[0][1]["queue_length"]
            )

        else:

            highest_queue_station = None

            highest_queue_value = 0

        return {

            "time_step": self.current_time_step,

            "total_wip": total_wip,

            "bottleneck_stations": bottlenecks,

            "sensor_dark_stations": dark_stations,

            "highest_queue_station":
                highest_queue_station,

            "highest_queue":
                highest_queue_value,
        }

    # ======================================================
    # PRINT STATE
    # ======================================================

    def print_state(self):

        """
        Print a readable Digital Twin snapshot.
        """

        print()

        print("=" * 90)

        print(
            "                     DIGITAL TWIN STATE"
        )

        print("=" * 90)

        print(
            f"Time step: {self.current_time_step}"
        )

        print(
            f"Total WIP: {self.get_total_wip()}"
        )

        print(
            f"Bottlenecks: "
            f"{self.get_bottleneck_stations()}"
        )

        print(
            f"Sensor-dark stations: "
            f"{self.get_sensor_dark_stations()}"
        )

        print()

        print(
            f"{'Station':<10}"
            f"{'Cycle':<12}"
            f"{'Queue':<10}"
            f"{'ΔQueue':<10}"
            f"{'Throughput':<14}"
            f"{'Sensors':<12}"
            f"{'Risk'}"
        )

        print("-" * 90)

        for station_id in self.stations:

            state = self.station_states[
                station_id
            ]

            sensor_status = (
                "YES"
                if state["sensor_available"]
                else "DARK"
            )

            print(
                f"{station_id:<10}"
                f"{state['cycle_time']:<12.2f}"
                f"{state['queue_length']:<10}"
                f"{state['queue_change']:<10}"
                f"{state['throughput']:<14.2f}"
                f"{sensor_status:<12}"
                f"{state['bottleneck_risk']}"
            )