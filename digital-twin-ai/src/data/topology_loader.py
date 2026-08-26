from pathlib import Path

import pandas as pd
import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TOPOLOGY_PATH = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "factory_topology.csv"
)


def load_topology(filepath=None):

    if filepath is None:
        filepath = TOPOLOGY_PATH

    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(
            f"Topology file not found: {filepath}"
        )

    df = pd.read_csv(filepath)

    required_columns = {
        "from_station",
        "to_station",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing topology columns: {missing}"
        )

    return df


def build_topology_graph(filepath=None):

    df = load_topology(filepath)

    graph = nx.DiGraph()

    for _, row in df.iterrows():

        graph.add_edge(
            row["from_station"],
            row["to_station"]
        )

    return graph


if __name__ == "__main__":

    graph = build_topology_graph()

    print("Topology loaded successfully.")

    print(
        f"Stations: {graph.number_of_nodes()}"
    )

    print(
        f"Connections: {graph.number_of_edges()}"
    )

    print()

    print("Branch points:")

    for station in graph.nodes:

        if graph.out_degree(station) > 1:

            print(
                f"  {station} → "
                f"{list(graph.successors(station))}"
            )

    print()

    print("Merge points:")

    for station in graph.nodes:

        if graph.in_degree(station) > 1:

            print(
                f"  {station} ← "
                f"{list(graph.predecessors(station))}"
            )