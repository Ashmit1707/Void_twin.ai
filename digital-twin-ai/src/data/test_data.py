from src.data.loader import load_plant_data
from src.data.validator import validate_plant_data


def main():

    print("Loading factory dataset...")

    df = load_plant_data()

    print(
        f"Loaded {len(df):,} rows."
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    print()

    print("Validating dataset...")

    validate_plant_data(df)

    print("Dataset validation PASSED.")

    print()

    print("Stations:")

    stations = sorted(
        df["station_id"].unique()
    )

    print(stations)

    print()

    print(
        f"Time steps: "
        f"{df['time_step'].min()} → "
        f"{df['time_step'].max()}"
    )


if __name__ == "__main__":
    main()