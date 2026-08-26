from src.data.loader import load_plant_data
from src.data.validator import validate_plant_data

from src.twin_engine.state_tracker import (
    FactoryStateTracker
)


def main():

    # ==================================================
    # LOAD DATA
    # ==================================================

    print("Loading factory data...")

    data = load_plant_data()

    print(
        f"Loaded {len(data):,} rows."
    )

    # ==================================================
    # VALIDATE DATA
    # ==================================================

    print("Validating data...")

    validate_plant_data(data)

    print(
        "Dataset validation PASSED."
    )

    # ==================================================
    # CREATE DIGITAL TWIN
    # ==================================================

    tracker = FactoryStateTracker(
        data
    )

    print(
        f"Stations detected: "
        f"{len(tracker.stations)}"
    )

    print(
        f"Time steps detected: "
        f"{len(tracker.time_steps)}"
    )

    # ==================================================
    # TEST EARLY STATE
    # ==================================================

    print()
    print(
        "Loading time step 100..."
    )

    tracker.update(100)

    tracker.print_state()

    # ==================================================
    # SUMMARY
    # ==================================================

    print()
    print("FACTORY SUMMARY")
    print("-" * 50)

    summary = tracker.get_summary()

    for key, value in summary.items():

        print(
            f"{key}: {value}"
        )

    # ==================================================
    # TEST BOTTLENECK PERIOD
    # ==================================================

    print()
    print(
        "Loading time step 400..."
    )

    tracker.update(400)

    tracker.print_state()

    # ==================================================
    # S20
    # ==================================================

    print()
    print("STATION S20 STATE")
    print("-" * 50)

    s20 = tracker.get_station_state(
        "S20"
    )

    for key, value in s20.items():

        print(
            f"{key}: {value}"
        )

    # ==================================================
    # HIGHEST QUEUES
    # ==================================================

    print()
    print(
        "TOP 5 QUEUES"
    )

    print("-" * 50)

    for station_id, state in (
        tracker.get_highest_queue_stations()
    ):

        print(
            f"{station_id}: "
            f"queue={state['queue_length']}"
        )

    # ==================================================
    # QUEUE GROWTH
    # ==================================================

    print()
    print(
        "TOP 5 QUEUE GROWTH"
    )

    print("-" * 50)

    for station_id, state in (
        tracker.get_queue_growth_stations()
    ):

        print(
            f"{station_id}: "
            f"Δqueue={state['queue_change']}"
        )


if __name__ == "__main__":

    main()