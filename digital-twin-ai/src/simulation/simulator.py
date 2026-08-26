import simpy
import pandas as pd

from src.simulation.plant_config import STATIONS
from src.simulation.anomaly_injector import AnomalyInjector


class FactorySimulator:

    def __init__(self, env):

        self.env = env

        # ==================================================
        # Anomaly generator
        # ==================================================

        # Fixed seed makes the simulation reproducible.
        #
        # Later we can remove the seed to generate
        # different factory runs.
        self.anomaly_injector = AnomalyInjector(
            seed=42
        )

        # ==================================================
        # Station resources
        # ==================================================

        # Each station has one machine.
        self.station_resources = {}

        # Each station has an input buffer.
        self.station_buffers = {}

        # ==================================================
        # Runtime statistics
        # ==================================================

        self.station_stats = {}

        for station in STATIONS:

            # ------------------------------------------
            # Machine
            # ------------------------------------------

            self.station_resources[
                station.station_id
            ] = simpy.Resource(
                env,
                capacity=1
            )

            # ------------------------------------------
            # Input buffer
            # ------------------------------------------

            self.station_buffers[
                station.station_id
            ] = simpy.Store(
                env,
                capacity=station.buffer_capacity
            )

            # ------------------------------------------
            # Statistics
            # ------------------------------------------

            self.station_stats[
                station.station_id
            ] = {
                "processed": 0,
                "busy_time": 0.0,
                "queue_max": 0,
            }

        # ==================================================
        # Event log
        # ==================================================

        # Every important simulation event will be stored here.
        #
        # Later this becomes the telemetry dataset consumed
        # by the Digital Twin engine.

        self.events = []

        # ==================================================
        # Start station processes
        # ==================================================

        for station in STATIONS:

            self.env.process(
                self.station_process(station)
            )

    # ======================================================
    # EVENT LOGGER
    # ======================================================

    def log_event(
        self,
        vehicle_id,
        station_id,
        event_type,
        cycle_time=None
    ):
        """
        Store one simulation event.

        Example:

        {
            "timestamp": 120.0,
            "vehicle_id": 3,
            "station_id": "S03",
            "event_type": "START",
            "cycle_time": 180.5
        }
        """

        self.events.append(
            {
                "timestamp": self.env.now,
                "vehicle_id": vehicle_id,
                "station_id": station_id,
                "event_type": event_type,
                "cycle_time": cycle_time,
            }
        )

    # ======================================================
    # STATION PROCESS
    # ======================================================

    def station_process(self, station):
        """
        Continuously process vehicles at one station.

        Each station:

        1. Waits for a vehicle.
        2. Acquires its machine.
        3. Processes the vehicle.
        4. Sends the vehicle to the next station.
        """

        buffer = self.station_buffers[
            station.station_id
        ]

        resource = self.station_resources[
            station.station_id
        ]

        while True:

            # ------------------------------------------------
            # Wait for vehicle
            # ------------------------------------------------

            vehicle_id = yield buffer.get()

            # Current queue size
            queue_length = len(buffer.items)

            # Update maximum queue length
            if queue_length > self.station_stats[
                station.station_id
            ]["queue_max"]:

                self.station_stats[
                    station.station_id
                ]["queue_max"] = queue_length

            # ------------------------------------------------
            # Request machine
            # ------------------------------------------------

            with resource.request() as request:

                yield request

                # ------------------------------------------------
                # Determine actual cycle time
                # ------------------------------------------------

                actual_cycle_time = (
                    self.anomaly_injector.get_cycle_time(
                        station
                    )
                )

                start_time = self.env.now

                # ------------------------------------------------
                # START event
                # ------------------------------------------------

                self.log_event(
                    vehicle_id,
                    station.station_id,
                    "START",
                    actual_cycle_time
                )

                print(
                    f"[{self.env.now:7.1f}s] "
                    f"Vehicle {vehicle_id:02d} "
                    f"START {station.station_id} "
                    f"({station.name}) "
                    f"cycle={actual_cycle_time:.1f}s"
                )

                # ------------------------------------------------
                # Process vehicle
                # ------------------------------------------------

                yield self.env.timeout(
                    actual_cycle_time
                )

                # ------------------------------------------------
                # Calculate actual processing time
                # ------------------------------------------------

                processing_time = (
                    self.env.now - start_time
                )

                # ------------------------------------------------
                # Update statistics
                # ------------------------------------------------

                stats = self.station_stats[
                    station.station_id
                ]

                stats["processed"] += 1

                stats["busy_time"] += (
                    processing_time
                )

                # ------------------------------------------------
                # FINISH event
                # ------------------------------------------------

                self.log_event(
                    vehicle_id,
                    station.station_id,
                    "FINISH",
                    actual_cycle_time
                )

                print(
                    f"[{self.env.now:7.1f}s] "
                    f"Vehicle {vehicle_id:02d} "
                    f"FINISH {station.station_id}"
                )

            # =================================================
            # Send vehicle to next station
            # =================================================

            station_index = STATIONS.index(
                station
            )

            # -------------------------------------------------
            # There is a next station
            # -------------------------------------------------

            if station_index < len(STATIONS) - 1:

                next_station = STATIONS[
                    station_index + 1
                ]

                next_buffer = self.station_buffers[
                    next_station.station_id
                ]

                # This automatically waits if the
                # downstream buffer is full.

                yield next_buffer.put(
                    vehicle_id
                )

                self.log_event(
                    vehicle_id,
                    station.station_id,
                    "BUFFER_EXIT",
                    None
                )

            # -------------------------------------------------
            # Last station
            # -------------------------------------------------

            else:

                self.log_event(
                    vehicle_id,
                    station.station_id,
                    "FACTORY_EXIT",
                    None
                )

                print(
                    f"[{self.env.now:7.1f}s] "
                    f"Vehicle {vehicle_id:02d} "
                    f"COMPLETED FACTORY"
                )

    # ======================================================
    # VEHICLE GENERATOR
    # ======================================================

    def generate_vehicles(
        self,
        number_of_vehicles
    ):
        """
        Generate vehicles at the factory entrance.

        Currently a new vehicle enters every 60 seconds.

        Later this can be replaced by real production
        arrival patterns.
        """

        for vehicle_id in range(
            1,
            number_of_vehicles + 1
        ):

            first_station = STATIONS[0]

            first_buffer = self.station_buffers[
                first_station.station_id
            ]

            # Put vehicle into first station buffer.

            yield first_buffer.put(
                vehicle_id
            )

            # Log factory entry.

            self.log_event(
                vehicle_id,
                first_station.station_id,
                "FACTORY_ENTRY",
                None
            )

            print(
                f"[{self.env.now:7.1f}s] "
                f"Vehicle {vehicle_id:02d} "
                f"ENTERED FACTORY"
            )

            # ---------------------------------------------
            # Takt time
            # ---------------------------------------------

            yield self.env.timeout(
                60
            )

    # ======================================================
    # PRINT STATISTICS
    # ======================================================

    def print_statistics(self):
        """
        Print summary statistics for every station.
        """

        print()
        print("=" * 60)
        print("                 STATION STATISTICS")
        print("=" * 60)

        for station in STATIONS:

            stats = self.station_stats[
                station.station_id
            ]

            print()

            print(
                f"{station.station_id} - "
                f"{station.name}"
            )

            print(
                f"    Cycle time: "
                f"{station.cycle_time:.1f}s"
            )

            print(
                f"    Buffer capacity: "
                f"{station.buffer_capacity}"
            )

            print(
                f"    Vehicles processed: "
                f"{stats['processed']}"
            )

            print(
                f"    Maximum queue: "
                f"{stats['queue_max']}"
            )

            print(
                f"    Machine busy time: "
                f"{stats['busy_time']:.1f}s"
            )

    # ======================================================
    # EXPORT EVENTS
    # ======================================================

    def export_events(
        self,
        filepath="data/raw/simulation_events.csv"
    ):
        """
        Convert the event log into a pandas DataFrame
        and save it as CSV.
        """

        df = pd.DataFrame(
            self.events
        )

        df.to_csv(
            filepath,
            index=False
        )

        print()
        print(
            f"Event data saved to: {filepath}"
        )

        print(
            f"Total events: {len(df)}"
        )


# ==========================================================
# RUN SIMULATION
# ==========================================================

def run_simulation(
    number_of_vehicles
):

    # ------------------------------------------------------
    # Create SimPy environment
    # ------------------------------------------------------

    env = simpy.Environment()

    # ------------------------------------------------------
    # Create factory
    # ------------------------------------------------------

    factory = FactorySimulator(
        env
    )

    # ------------------------------------------------------
    # Start vehicle generator
    # ------------------------------------------------------

    env.process(
        factory.generate_vehicles(
            number_of_vehicles
        )
    )

    # ------------------------------------------------------
    # Simulation header
    # ------------------------------------------------------

    print()
    print("=" * 60)
    print("             DIGITAL TWIN SIMULATOR")
    print("=" * 60)
    print()

    # ------------------------------------------------------
    # Run simulation
    # ------------------------------------------------------

    env.run()

    # ------------------------------------------------------
    # Statistics
    # ------------------------------------------------------

    factory.print_statistics()

    # ------------------------------------------------------
    # Export event data
    # ------------------------------------------------------

    factory.export_events()

    # ------------------------------------------------------
    # Final information
    # ------------------------------------------------------

    print()
    print("=" * 60)

    print(
        f"Total simulation time: "
        f"{env.now:.1f}s"
    )

    print(
        f"Vehicles simulated: "
        f"{number_of_vehicles}"
    )

    print("=" * 60)


# ==========================================================
# PROGRAM ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    run_simulation(
        number_of_vehicles=10
    )