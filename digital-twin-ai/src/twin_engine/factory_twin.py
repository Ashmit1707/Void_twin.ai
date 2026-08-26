from src.data.loader import load_plant_data
from src.data.validator import validate_plant_data
from src.data.topology_loader import build_topology_graph

from src.twin_engine.state_tracker import (
    FactoryStateTracker
)


class FactoryDigitalTwin:
    """
    Combines:

        1. Factory telemetry
        2. Station state tracking
        3. Factory topology

    into a single Digital Twin representation.
    """

    def __init__(
        self,
        data=None,
        topology_graph=None
    ):

        # ==================================================
        # LOAD DATA
        # ==================================================

        if data is None:

            data = load_plant_data()

        validate_plant_data(data)

        # ==================================================
        # STATE TRACKER
        # ==================================================

        self.state_tracker = (
            FactoryStateTracker(data)
        )

        # ==================================================
        # TOPOLOGY
        # ==================================================

        if topology_graph is None:

            topology_graph = (
                build_topology_graph()
            )

        self.topology = topology_graph

        # ==================================================
        # CURRENT TIME
        # ==================================================

        self.current_time_step = None

    # ======================================================
    # UPDATE DIGITAL TWIN
    # ======================================================

    def update(self, time_step):

        """
        Update the complete Digital Twin to a
        particular time step.
        """

        self.state_tracker.update(
            time_step
        )

        self.current_time_step = (
            time_step
        )

    # ======================================================
    # STATION STATE
    # ======================================================

    def get_station(self, station_id):

        """
        Return both:

            - current station state
            - upstream stations
            - downstream stations
        """

        state = (
            self.state_tracker
            .get_station_state(station_id)
        )

        station_id = (
            self.state_tracker
            ._normalize_station_id(station_id)
        )

        # --------------------------------------------------
        # Topology relationships
        # --------------------------------------------------

        upstream = list(
            self.topology.predecessors(
                station_id
            )
        )

        downstream = list(
            self.topology.successors(
                station_id
            )
        )

        return {

            "state": state,

            "upstream": upstream,

            "downstream": downstream,
        }

    # ======================================================
    # UPSTREAM STATIONS
    # ======================================================

    def get_upstream_stations(
        self,
        station_id
    ):

        station_id = (
            self.state_tracker
            ._normalize_station_id(station_id)
        )

        return list(
            self.topology.predecessors(
                station_id
            )
        )

    # ======================================================
    # DOWNSTREAM STATIONS
    # ======================================================

    def get_downstream_stations(
        self,
        station_id
    ):

        station_id = (
            self.state_tracker
            ._normalize_station_id(station_id)
        )

        return list(
            self.topology.successors(
                station_id
            )
        )

    # ======================================================
    # FIND ALL UPSTREAM STATIONS
    # ======================================================

    def get_all_upstream_stations(
        self,
        station_id
    ):

        station_id = (
            self.state_tracker
            ._normalize_station_id(station_id)
        )

        if station_id not in self.topology:

            raise ValueError(
                f"Unknown station: {station_id}"
            )

        return list(
            self._ancestors(station_id)
        )

    # ======================================================
    # FIND ALL DOWNSTREAM STATIONS
    # ======================================================

    def get_all_downstream_stations(
        self,
        station_id
    ):

        station_id = (
            self.state_tracker
            ._normalize_station_id(station_id)
        )

        if station_id not in self.topology:

            raise ValueError(
                f"Unknown station: {station_id}"
            )

        return list(
            self._descendants(station_id)
        )

    # ======================================================
    # GRAPH TRAVERSAL
    # ======================================================

    def _ancestors(self, station_id):

        visited = set()

        stack = list(
            self.topology.predecessors(
                station_id
            )
        )

        while stack:

            station = stack.pop()

            if station in visited:

                continue

            visited.add(station)

            stack.extend(
                self.topology.predecessors(
                    station
                )
            )

        return visited

    def _descendants(self, station_id):

        visited = set()

        stack = list(
            self.topology.successors(
                station_id
            )
        )

        while stack:

            station = stack.pop()

            if station in visited:

                continue

            visited.add(station)

            stack.extend(
                self.topology.successors(
                    station
                )
            )

        return visited

    # ======================================================
    # CURRENT BOTTLENECKS
    # ======================================================

    def get_bottlenecks(self):

        return (
            self.state_tracker
            .get_bottleneck_stations()
        )

    # ======================================================
    # BOTTLENECK IMPACT
    # ======================================================

    def get_bottleneck_impact(
        self,
        station_id
    ):

        station_id = (
            self.state_tracker
            ._normalize_station_id(station_id)
        )

        state = (
            self.state_tracker
            .get_station_state(station_id)
        )

        downstream = (
            self.get_all_downstream_stations(
                station_id
            )
        )

        return {

            "station": station_id,

            "is_bottleneck":
                state["bottleneck_risk"] == 1,

            "queue_length":
                state["queue_length"],

            "cycle_time":
                state["cycle_time"],

            "downstream_impact":
                sorted(downstream),
        }

    # ======================================================
    # FACTORY SUMMARY
    # ======================================================

    def get_factory_summary(self):

        summary = (
            self.state_tracker
            .get_summary()
        )

        summary["current_time_step"] = (
            self.current_time_step
        )

        summary["stations"] = (
            len(self.topology.nodes)
        )

        summary["connections"] = (
            len(self.topology.edges)
        )

        return summary