# DigitalTwin.ai — Project Context Document
> For handoff to team members and AI assistants. Last updated: Current Stage.

---

## What This Is

A hackathon submission for **Accenture Innovation Challenge 2026 — Round 2**.

The project is called **DigitalTwin.ai** — a predictive digital twin for complex vehicle assembly lines. It provides real-time bottleneck prediction, latent defect tracing across station dependencies, and interactive visual management.

The core capabilities:
1. **Interactive Frontend Dashboard**: Drag & drop production CSVs or launch pre-loaded demo shifts, showing visual bottleneck prediction before line blockage occurs.
2. **PyTorch Multi-Task Learning (MTL) Model**: Dual-head LSTM deep learning model predicting bottleneck risks and defect risks across all 40 line stations over rolling telemetry windows.
3. **Latent Defect & Root Cause Tracker**: Isolates upstream temporal anomaly signals using DAG factory topology traversal (NetworkX + Isolation Forest).
4. **Plant Simulation & Event Injector**: Dynamic simulator modeling Takt time, buffer sizes, sensor maturity, and parallel station lines with anomaly injection.

---

## Team & Architecture

- **Frontend & Visual Management**: Pure HTML5 / CSS3 / Vanilla JS (responsive industrial dark theme design system).
- **Backend Services**: FastAPI microservices for live telemetry scoring, topology graph retrieval, and anomaly tracing.
- **AI & Deep Learning Engine**: PyTorch dual-head MTL network + Random Forest & Isolation Forest baselines.

---

## The One Demo Scenario

- **Paint-12** gradually drifts from risk score 12 → 91 over a shift.
- Downstream stations **Paint-14** and **Paint-16** show cascading starvation risk.
- The system predicts the bottleneck build-up and pinpoints upstream root causes before a total line shutdown.

---

## Line & Parameter Specifications

- **40 stations total**: Body (15) → Paint (10) → Final Assembly (15)
- **Takt time**: 60 seconds baseline
- **Sensor coverage**: Fully instrumented high-maturity stations + sensor-poor estimated stations
- **Bottleneck thresholds**:
  - Cycle time > 72s (>20% over takt) → alert
  - Queue depth grows >3 vehicles in 5 min → alert
  - Utilisation >90% sustained 3+ min → alert
- **Amber** = 1 signal breached. **Red** = 2+ signals breached
- **Buffer** between stations: 5 vehicles
- **Starvation risk** fires when buffer drains below 2 vehicles

---

## Complete Tech Stack

| Layer | Tool / Technology |
|---|---|
| Frontend | HTML5, CSS3 (CSS Variables, Dark Aesthetic), Vanilla JS |
| Charts & Heatmaps | Custom Grid & Canvas heatmaps (No third-party chart Bloat) |
| Primary AI Server | FastAPI + Uvicorn (`digital-twin-ai/main.py`) |
| Lightweight API | FastAPI (`backend/main.py`) for client-side CSV parsing |
| Deep Learning | PyTorch (Dual-head Multi-Task Learning LSTM Network) |
| Classical ML | Scikit-learn (Isolation Forest & Random Forest Bottleneck Classifier) |
| Graph Topology | NetworkX (Directed Acyclic Graph for 40-station line topology) |
| Data & Simulation | Pandas, NumPy, Synthetic Plant Simulator & Anomaly Injector |

---

## File Structure

```
Accenture/
├── design/                          ✅ Frontend Interface
│   ├── index.html                   ← Landing & CSV drag/drop upload page
│   ├── dashboard.html               ← Main Digital Twin dashboard shell
│   ├── styles.css                   ← Complete design system (industrial dark theme)
│   └── components/
│       ├── data.js                  ← Station definitions & state helpers
│       ├── timeline.js              ← Scrollable timeline heatmap viz
│       ├── table.js                 ← Sortable station table component
│       ├── insight.js               ← Right-side detail & root-cause insight panel
│       └── csv.js                   ← Client-side CSV parser & heuristic evaluator
│
├── backend/                         ✅ Lightweight Backend Service
│   ├── main.py                      ← FastAPI server for CSV upload scoring & demo endpoints
│   ├── predictor.py                 ← Isolation Forest anomaly scorer for uploaded CSVs
│   ├── demo_stations.json           ← Pre-built demo station data
│   └── requirements.txt             ← Python dependencies for backend
│
├── digital-twin-ai/                 ✅ Full PyTorch AI & Simulation Engine
│   ├── main.py                      ← Main AI Backend API (v2.5)
│   ├── twin_mtl_model.pth           ← Trained PyTorch Dual-Head MTL weights
│   ├── data/
│   │   ├── raw/                     ← Telemetry CSV datasets (plant_twin_data.csv)
│   │   └── reference/               ← Factory topology & station config specifications
│   └── src/
│       ├── data/                    ← Dataset loaders, DAG builders, and validators
│       ├── models/                  ← Latent defect tracker & Random Forest models
│       ├── simulation/              ← Plant simulator & anomaly injector
│       └── twin_engine/             ← PyTorch MTL model definition, dataset & inference runner
│
├── twin_ai_PRD.txt                  ✅ Product Requirements Document
├── CONTEXT.md                       ✅ Project Context & Blueprint (This document)
└── README.md                        ✅ System Overview & Quickstart Guide
```

---

## Component Details

### Frontend (`design/`)
- `index.html`: Drag & drop upload flow, interactive demo mode, multi-stage processing simulation.
- `dashboard.html`: Main real-time command dashboard featuring KPIs, station table, heatmap timeline, and detail panels.
- `styles.css`: Dark industrial theme using defined CSS variables (`--bg-base`, `--brand-cyan`, `--risk-low`, etc.).
- `components/data.js`: Central state & station data definitions.
- `components/timeline.js`: Scrollable 24-step risk heatmap with cell tooltips.
- `components/table.js`: Sortable, filterable 40-station data table.
- `components/insight.js`: Detailed drawer showing risk breakdown, contributing factors, and confidence metrics.
- `components/csv.js`: Client-side fallback parser for CSV files.

### Lightweight Backend (`backend/`)
- `GET /api/health`: Health check endpoint.
- `POST /api/upload`: Receives uploaded factory CSV and computes station risk scores via Isolation Forest.
- `GET /api/demo`: Returns standard 12/40-station demo payload.

### Primary AI Engine (`digital-twin-ai/`)
- `GET /api/v1/topology`: Returns enriched factory station graph (nodes & directed edges).
- `GET /api/v1/predict/status`: Runs rolling 10-step telemetry window through PyTorch Dual-Head MTL model to return live bottleneck and defect risk scores across all 40 stations.
- `POST /api/v1/trace/defect`: Performs upstream temporal DAG search via `LatentDefectTracker` to find exact root-cause station for a reported defect.

---

## AI Model Specifications

### 1. Dual-Head MTL LSTM Model (`digital-twin-ai/src/twin_engine/model.py`)
- **Inputs**: Rolling 10-timestep sequence of station telemetry (cycle times, queue depths, utilisation, error rates).
- **Head 1**: Bottleneck Risk Score (Regression / Probabilistic Risk 0.0 - 1.0).
- **Head 2**: Latent Defect Risk Score (Multi-station probability vector).
- **Weights**: Saved in `twin_mtl_model.pth`.

### 2. Upstream Latent Defect Tracker (`digital-twin-ai/src/models/defect_tracker.py`)
- Traverses factory DAG built with NetworkX.
- Combines healthy baseline Isolation Forest scoring with upstream temporal lag traversal to trace downstream quality failures back to their originating station.

---

## Risk Score Formula Baseline

```
Risk = 0.30 × cycle_time_deviation
     + 0.25 × queue_growth
     + 0.20 × utilisation
     + 0.15 × anomaly_score
     + 0.10 × upstream_risk
```

---

## Current Status & Next Recommendations

| Component | Status | Description |
|---|---|---|
| Frontend UI | ✅ Complete | Industrial dark mode dashboard, heatmap, station table, and insight drawer |
| Lightweight Backend | ✅ Complete | FastAPI upload parser (`backend/main.py`) with Isolation Forest scoring |
| PyTorch Dual-Head Model | ✅ Complete | Multi-Task LSTM engine (`digital-twin-ai/main.py`) for bottleneck & defect prediction |
| Defect Root Cause Tracing | ✅ Complete | Upstream DAG temporal search module (`/api/v1/trace/defect`) wired to `insight.js` drawer |
| Live API Polling | ✅ Complete | `data.js` polls `/api/v1/predict/status` every 3s to reflect PyTorch MTL predictions |
| Shift Playback & Animation | ✅ Complete | Interactive Play/Pause (`▶` / `❚❚`) shift ticker advancing `08:00` → `15:40` with live Paint-12 drift |
| `plant_twin_data.csv` Support | ✅ Complete | Extended client & backend parsers (`csv.js`, `predictor.py`) to parse `plant_twin_data.csv` format seamlessly |
| UI Confidence Parameter | ✅ Complete | Added sortable **Confidence %** column to Station Table, timeline tooltips, and insight drawer |
| End-to-End Verification | ✅ Complete | Verified backend execution on `http://127.0.0.1:8000` with full 40-station dataset |


---

## What To Do Next

1. **Analytics & Historical Reporting Page**:
   - Create an `analytics.html` page featuring shift summaries, station risk ranking, and bottleneck frequency metrics over historical shifts.
2. **Interactive What-If Simulation Mode**:
   - Add a UI control allowing floor managers to simulate interventions (e.g. *"What if we add +1 buffer vehicle at Paint-12 or reduce takt time by 5s?"*) and see predicted risk drop in real time.
3. **Export Shift Summary Report**:
   - Add PDF / CSV export of the full shift timeline and detected defect root causes for factory management handoff.


