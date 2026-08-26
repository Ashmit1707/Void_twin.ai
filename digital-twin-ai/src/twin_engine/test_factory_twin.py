from src.twin_engine.factory_twin import (
    FactoryDigitalTwin
)


def main():

    print("=" * 70)
    print("             FACTORY DIGITAL TWIN")
    print("=" * 70)

    # --------------------------------------------------
    # Create Digital Twin
    # --------------------------------------------------

    twin = FactoryDigitalTwin()

    print()
    print(
        "Digital Twin initialized."
    )

    print(
        f"Stations: "
        f"{len(twin.topology.nodes)}"
    )

    print(
        f"Connections: "
        f"{len(twin.topology.edges)}"
    )

    # --------------------------------------------------
    # Update state
    # --------------------------------------------------

    twin.update(400)

    print()
    print(
        "Digital Twin updated to "
        "time step 400."
    )

    # --------------------------------------------------
    # Test S03
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("STATION S03")
    print("=" * 70)

    s03 = twin.get_station("S03")

    print(
        "State:"
    )

    print(
        s03["state"]
    )

    print()

    print(
        "Upstream:"
    )

    print(
        s03["upstream"]
    )

    print()

    print(
        "Downstream:"
    )

    print(
        s03["downstream"]
    )

    # --------------------------------------------------
    # Test S08
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("STATION S08")
    print("=" * 70)

    s08 = twin.get_station("S08")

    print(
        "Upstream:"
    )

    print(
        s08["upstream"]
    )

    print(
        "Downstream:"
    )

    print(
        s08["downstream"]
    )

    # --------------------------------------------------
    # All downstream from S03
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("ALL DOWNSTREAM FROM S03")
    print("=" * 70)

    downstream = (
        twin.get_all_downstream_stations(
            "S03"
        )
    )

    print(
        sorted(downstream)
    )

    # --------------------------------------------------
    # Bottlenecks
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("CURRENT BOTTLENECKS")
    print("=" * 70)

    print(
        twin.get_bottlenecks()
    )

    # --------------------------------------------------
    # Bottleneck impact
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("S20 BOTTLENECK IMPACT")
    print("=" * 70)

    impact = (
        twin.get_bottleneck_impact(
            "S20"
        )
    )

    for key, value in impact.items():

        print(
            f"{key}: {value}"
        )

    # --------------------------------------------------
    # Factory summary
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("FACTORY SUMMARY")
    print("=" * 70)

    summary = (
        twin.get_factory_summary()
    )

    for key, value in summary.items():

        print(
            f"{key}: {value}"
        )


if __name__ == "__main__":

    main()