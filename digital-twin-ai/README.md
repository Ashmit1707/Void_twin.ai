# DigitalTwin.ai — PyTorch AI & Simulation Engine

This directory contains the primary AI engine, deep learning models, topology graph traversal, and plant simulation pipeline.

---

## ⬡ Components Overview

### 1. PyTorch Multi-Task Learning (MTL) Model (`src/twin_engine/`)
- **Architecture**: `DigitalTwinMTL` — 2-layer LSTM with Dual Task Heads.
  - **Head 1 (Bottleneck Prediction)**: Regression & probabilistic bottleneck risk score (0.0 to 1.0) across 40 stations.
  - **Head 2 (Latent Defect Risk)**: Multi-station classification predicting defect risk vector.
- **Inference Runner**: `TwinPredictor` (`src/twin_engine/inference.py`). Evaluates rolling 10-timestep sequences of plant telemetry (cycle times, queue depths, throughput, torque, vibration, temperature).
- **Weights**: Saved in `twin_mtl_model.pth`.

### 2. Latent Defect Tracker (`src/models/defect_tracker.py`)
- **Factory Topology DAG**: Built with NetworkX from `data/reference/factory_topology.csv` (Body 1–15 → Paint 16–25 → Final Assembly 26–40).
- **Temporal Traversal**: Combines healthy baseline Isolation Forest anomaly scoring with temporal lag graph search to trace downstream quality failures back to their originating station.

### 3. Plant Simulator & Anomaly Injector (`src/simulation/`)
- **Simulator**: `PlantSimulator` (`src/simulation/simulator.py`) generates synthetic telemetry modeling Takt time (60s baseline), buffer capacities (5 vehicles), sensor coverage masks, and station cycle times.
- **Anomaly Injector**: `AnomalyInjector` injects gradual cycle time drift scenarios (e.g. Paint-12 drift) for training and evaluation.

---

## 📡 Microservice Endpoints (`main.py`)

Run server:
```bash
uvicorn main:app --reload --port 8000
```

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/predict/status` | Feeds current 10-step telemetry sequence to PyTorch MTL model; returns live bottleneck & defect predictions. |
| `POST` | `/api/v1/trace/defect` | Accepts `{ final_station_id, defect_time_step }` and returns the upstream root cause station. |
| `GET` | `/api/v1/topology` | Returns enriched 40-station DAG nodes and edges. |

---

## 🧪 Testing & Execution

- **Run Inference Check**:
  ```powershell
  python -c "import pandas as pd; from src.twin_engine.inference import TwinPredictor; p = TwinPredictor('twin_mtl_model.pth', 40); df = pd.read_csv('data/raw/plant_twin_data.csv'); print(p.run_prediction(df[df['time_step'] >= df['time_step'].max() - 9]))"
  ```
- **Retrain PyTorch Model**:
  ```powershell
  python src/twin_engine/model.py
  ```
