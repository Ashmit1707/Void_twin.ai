import pandas as pd


REQUIRED_COLUMNS = {
    "time_step",
    "station_id",
    "cycle_time",
    "queue_length",
    "throughput",
    "torque_nm",
    "vibration_hz",
    "temperature_c",
    "bottleneck_risk",
}


def validate_plant_data(df):
    """
    Validate the structure of the factory dataset.

    Returns
    -------
    bool
        True if the dataset passes validation.
    """

    # --------------------------------------------------
    # Check columns
    # --------------------------------------------------

    missing_columns = (
        REQUIRED_COLUMNS - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # --------------------------------------------------
    # Check station IDs
    # --------------------------------------------------

    if df["station_id"].isna().any():

        raise ValueError(
            "station_id contains missing values."
        )

    # --------------------------------------------------
    # Check time steps
    # --------------------------------------------------

    if df["time_step"].isna().any():

        raise ValueError(
            "time_step contains missing values."
        )

    # --------------------------------------------------
    # Check cycle time
    # --------------------------------------------------

    if (df["cycle_time"] <= 0).any():

        raise ValueError(
            "cycle_time must be greater than zero."
        )

    # --------------------------------------------------
    # Check queue length
    # --------------------------------------------------

    if (df["queue_length"] < 0).any():

        raise ValueError(
            "queue_length cannot be negative."
        )

    # --------------------------------------------------
    # Check bottleneck labels
    # --------------------------------------------------

    valid_risk_values = {0, 1}

    actual_values = set(
        df["bottleneck_risk"].dropna().unique()
    )

    if not actual_values.issubset(
        valid_risk_values
    ):

        raise ValueError(
            "bottleneck_risk must contain "
            "only 0 or 1."
        )

    return True

