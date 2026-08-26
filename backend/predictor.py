# ============================================================
# DigitalTwin.ai — Prediction Engine
#
# Two layers, matching what was agreed for the demo:
#
#   1. Rule-based risk score (SPC-style) — the same formula the
#      frontend already computes client-side in csv.js, kept
#      IDENTICAL here so numbers agree whichever path a station's
#      data takes. This is the explainable, floor-supervisor-
#      trustable layer.
#
#   2. Isolation Forest anomaly score — real ML, computed here
#      because it needs a fitted model per station's own signal
#      history. This replaces the placeholder "anomaly" heuristic
#      the frontend uses when it doesn't have a backend to call.
#
# A station needs at least MIN_ROWS_FOR_ANOMALY rows of its own
# history before Isolation Forest is used; below that, anomaly
# falls back to 0 (not enough history to say what's "normal" for
# that station yet) — this mirrors the sensor-poor / data-gap
# story from the brief: partial data still produces a usable,
# clearly-lower-confidence result rather than an error.
# ============================================================

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MIN_ROWS_FOR_ANOMALY = 4


def compute_rule_based_risk(cycle: float, queue: float, util: float, takt: float) -> dict:
    """Same three-signal formula as csv.js's computeRiskForRow — kept
    in lockstep so frontend-only and backend-scored stations agree."""
    cycle_dev_pct = max(0.0, ((cycle - takt) / takt) * 100)
    cycle_dev_score = min(100.0, cycle_dev_pct * 2)
    queue_score = min(100.0, (queue / 8) * 100)
    util_score = min(100.0, max(0.0, util - 60) * 2.5)

    risk = round(0.40 * cycle_dev_score + 0.35 * queue_score + 0.25 * util_score)
    return {
        "risk": max(0, min(100, risk)),
        "cycle_dev_score": round(cycle_dev_score),
        "queue_score": round(queue_score),
        "util_score": round(util_score),
    }


def compute_anomaly_scores(station_df: pd.DataFrame) -> list[int]:
    """Fits an Isolation Forest on this station's own (cycle_time,
    queue_depth, utilization) history and returns a 0-100 anomaly
    score per row — higher means further from that station's own
    normal operating envelope.

    Falls back to zeros when there isn't enough history yet.
    """
    n = len(station_df)
    if n < MIN_ROWS_FOR_ANOMALY:
        return [0] * n

    X = station_df[["cycle_time_sec", "queue_depth", "utilization_pct"]].values

    # contamination is an assumption about what fraction of points
    # are anomalous — 0.2 is a reasonable default for a short window
    # of production data without labelled ground truth
    model = IsolationForest(
        n_estimators=100,
        contamination=0.2,
        random_state=42,
    )
    model.fit(X)

    # decision_function: higher = more normal. Flip and rescale to 0-100.
    raw_scores = model.decision_function(X)
    inverted = -raw_scores  # higher now = more anomalous
    lo, hi = inverted.min(), inverted.max()
    if hi - lo < 1e-9:
        return [0] * n  # all points identical — nothing anomalous

    scaled = ((inverted - lo) / (hi - lo) * 100).round().astype(int)
    return scaled.tolist()


def normalise_zone(raw: str) -> str:
    z = (raw or "").strip().lower()
    if z.startswith("body"):
        return "Body"
    if z.startswith("paint"):
        return "Paint"
    if z.startswith("final"):
        return "Final"
    return "Body"


def parse_sensor_flag(raw) -> bool:
    v = str(raw).strip().lower() if raw is not None else ""
    return v not in ("no", "false", "0", "n")


def build_stations_from_dataframe(df: pd.DataFrame) -> tuple[list[dict], list[str]]:
    """Mirrors csv.js's buildStationsFromRows, plus real anomaly
    scoring. Returns (stations, warnings)."""
    warnings: list[str] = []
    stations: list[dict] = []

    required = {"station_id", "zone", "cycle_time_sec", "queue_depth", "utilization_pct"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing))}")

    # Coerce numeric columns; rows that fail become NaN and get dropped with a warning
    for col in ["cycle_time_sec", "queue_depth", "utilization_pct", "takt_target_sec", "time_step"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["cycle_time_sec", "queue_depth", "utilization_pct", "station_id", "zone"])
    dropped = before - len(df)
    if dropped > 0:
        warnings.append(f"{dropped} row(s) skipped — missing or non-numeric required values.")

    if df.empty:
        raise ValueError("No valid data rows after validation.")

    for station_id, group in df.groupby("station_id", sort=False):
        group = group.copy()
        if "time_step" in group.columns and group["time_step"].notna().any():
            group = group.sort_values("time_step")
        # else: keep original file order (groupby preserves it with sort=False)

        takt = group["takt_target_sec"].iloc[0] if "takt_target_sec" in group.columns and pd.notna(group["takt_target_sec"].iloc[0]) else 60.0
        zone = normalise_zone(group["zone"].iloc[0])
        sensor = parse_sensor_flag(group["sensor_coverage"].iloc[0]) if "sensor_coverage" in group.columns else True
        name = group["station_name"].iloc[0] if "station_name" in group.columns and pd.notna(group["station_name"].iloc[0]) else station_id

        anomaly_scores = compute_anomaly_scores(group)

        risk_arr = []
        rule_scores = []
        for _, row in group.iterrows():
            computed = compute_rule_based_risk(row["cycle_time_sec"], row["queue_depth"], row["utilization_pct"], takt)
            rule_scores.append(computed)
            risk_arr.append(computed["risk"])

        # Blend the rule-based risk with the real anomaly score for the
        # final risk value — anomaly acts as a 15% adjustment on top of
        # the explainable SPC-style base, matching the weighting agreed
        # in the parameters discussion (rule-based signals + anomaly).
        blended_risk = []
        for base, anomaly in zip(risk_arr, anomaly_scores):
            blended = round(base * 0.85 + anomaly * 0.15)
            blended_risk.append(max(0, min(100, blended)))

        last_rule = rule_scores[-1]
        last_anomaly = anomaly_scores[-1]

        confidence = (82 + int(np.random.randint(0, 13))) if sensor else (55 + int(np.random.randint(0, 16)))

        stations.append({
            "id": str(station_id),
            "name": str(name),
            "zone": zone,
            "queue": float(group["queue_depth"].iloc[-1]),
            "takt": float(takt),
            "util": float(group["utilization_pct"].iloc[-1]),
            "sensor": sensor,
            "risk": blended_risk,
            "factors": {
                "queueGrowth": last_rule["queue_score"],
                "cycleDeviation": last_rule["cycle_dev_score"],
                "utilisation": round(float(group["utilization_pct"].iloc[-1])),
                "anomaly": int(last_anomaly),
            },
            "confidence": confidence,
        })

    return stations, warnings
