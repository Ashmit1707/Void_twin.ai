# ============================================================
# DigitalTwin.ai — Backend API
#
# Endpoints:
#   GET  /api/health          — liveness check
#   POST /api/upload          — upload a production CSV, get
#                                back the same STATIONS shape
#                                the frontend already uses,
#                                but scored with real Isolation
#                                Forest anomaly detection
#   GET  /api/demo             — the built-in 12-station demo
#                                scenario (Paint-12 drift), as
#                                a single source of truth the
#                                frontend's data.js can eventually
#                                fetch instead of hardcoding
#
# Run locally:
#   pip install -r requirements.txt
#   uvicorn main:app --reload --port 8000
#
# The frontend currently parses CSVs entirely client-side
# (design/components/csv.js) so it works with zero backend.
# This service is the next step: once a teammate wants real
# anomaly detection instead of the frontend's placeholder
# heuristic, point the upload flow at POST /api/upload instead
# of (or in addition to) the local parse.
# ============================================================

import io
import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from predictor import build_stations_from_dataframe

app = FastAPI(title="DigitalTwin.ai API", version="0.1.0")

# Wide open for hackathon demo purposes — the frontend is static
# files with no build step, so it may be opened from file:// or
# a variety of local ports. Tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_PATH = Path(__file__).parent / "demo_stations.json"


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "digitaltwin-api"}


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")  # handles Excel's BOM-prefixed CSVs too
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Could not decode file as UTF-8 text.")

    try:
        df = pd.read_csv(io.StringIO(text))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV has no data rows.")

    df.columns = [c.strip().lower() for c in df.columns]

    try:
        stations, warnings = build_stations_from_dataframe(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "ok": True,
        "filename": file.filename,
        "station_count": len(stations),
        "stations": stations,
        "warnings": warnings,
    }


@app.get("/api/demo")
def get_demo():
    if not DEMO_PATH.exists():
        raise HTTPException(status_code=404, detail="Demo dataset not found.")
    with open(DEMO_PATH) as f:
        return json.load(f)
