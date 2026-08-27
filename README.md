# DigitalTwin.ai — Predictive Digital Twin for Vehicle Assembly Lines
> **Accenture Innovation Challenge 2026 — Round 2 Project**

---

## ⬡ Overview

**DigitalTwin.ai** is an AI-powered predictive digital twin for complex vehicle assembly lines. It forecasts production line bottlenecks and traces latent quality defects back to their upstream root cause **hours before line blockage occurs**.

Unplanned assembly line stoppages cost up to **$22,000 per minute**. Traditional monitoring systems only react *after* a bottleneck or breakdown has already happened. DigitalTwin.ai combines **PyTorch Multi-Task Learning (MTL)** sequence models, **NetworkX Directed Acyclic Graphs (DAG)**, and **Isolation Forest multivariate anomaly detection** to enable proactive floor management.

---

## 🔥 Key Features

1. **PyTorch Dual-Head Multi-Task Learning (MTL) Engine**:
   - Evaluates rolling 10-timestep sequence windows across 40 assembly stations.
   - Predicts **Bottleneck Risk** and **Latent Defect Risk** simultaneously with real-time confidence scores.
2. **Upstream Latent Defect Root Cause Tracer**:
   - Traverses factory topology DAGs using NetworkX and Isolation Forest anomaly paths.
   - Traces downstream quality failures back to their originating station (e.g., *“Defect at Paint-14 originating 3 steps upstream at Body-07”*).
3. **Interactive Shift Playback & Animation**:
   - Live play/pause ticker loop stepping through shift time slots (`08:00` → `15:40`).
   - Visual active time cursor highlighting station risk drifts (e.g., Paint-12 drifting Green → Yellow → Orange → Red).
4. **Flexible Telemetry & CSV Dataset Parsing**:
   - Native support for industrial CSV datasets like `plant_twin_data.csv` (20,000+ telemetry rows over 40 stations).
   - Color-coded **Confidence %** parameters rendered across table views, timeline tooltips, and detail drawers.

---

## 📂 Project Architecture

```
Accenture/
├── design/                          ✅ Frontend Interface (HTML5 / CSS3 / Vanilla JS)
│   ├── index.html                   ← Landing page, CSV upload & processing animation
│   ├── dashboard.html               ← Real-time Digital Twin command dashboard
│   ├── styles.css                   ← Complete dark industrial design system
│   └── components/
│       ├── data.js                  ← State management & live API polling ticker
│       ├── timeline.js              ← Scrollable 24-step risk heatmap component
│       ├── table.js                 ← Sortable 40-station table with Confidence metrics
│       ├── insight.js               ← Right-side detail drawer & DAG defect root cause trace
│       └── csv.js                   ← Client-side CSV parser & heuristic evaluator
│
├── backend/                         ✅ Lightweight Backend Service
│   ├── main.py                      ← FastAPI upload parser service
│   ├── predictor.py                 ← Isolation Forest scoring engine
│   └── demo_stations.json           ← Pre-built demo station datasets
│
├── digital-twin-ai/                 ✅ Primary PyTorch AI & Simulation Engine
│   ├── main.py                      ← Main AI FastAPI Backend (`/api/v1/...`)
│   ├── twin_mtl_model.pth           ← Trained PyTorch Dual-Head MTL weights
│   └── src/
│       ├── twin_engine/             ← PyTorch MTL model architecture & inference runner
│       ├── models/                  ← Latent defect tracker & Isolation Forest baseline
│       └── simulation/              ← Plant simulator & anomaly injector
│
├── plant_twin_data.csv              ✅ 40-Station Telemetry Dataset (20,000 rows)
├── CONTEXT.md                       ✅ Project Context & AI Assistant Blueprint
└── README.md                        ✅ System Overview & Quickstart Guide (This file)
```

---

## ⚡ Quickstart — Running Locally

### 1. Launch the AI Backend Service
Ensure Python dependencies are installed and start the FastAPI server:

```powershell
cd d:\Hackathons\Accenture\digital-twin-ai
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*The AI server will initialize the PyTorch MTL model and start serving at `http://127.0.0.1:8000`.*

### 2. Open the Dashboard UI
Open `design/index.html` directly in any web browser (no Node build step required):
- Double click [design/index.html](file:///d:/Hackathons/Accenture/design/index.html) in your file explorer, OR
- Open directly in Chrome / Edge / Firefox.

---

## 📡 API Endpoints Summary

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/predict/status` | `GET` | Runs rolling 10-step telemetry window through PyTorch Dual-Head MTL model; returns live bottleneck & defect predictions. |
| `/api/v1/trace/defect` | `POST` | Traverses upstream topology DAG to isolate temporal anomaly root causes for a specific station defect. |
| `/api/v1/topology` | `GET` | Returns full 40-station directed graph (nodes, edges, sensor maturity flags). |
| `/api/upload` | `POST` | Uploads production CSV files and returns Isolation Forest scored station objects. |

---

## 🎬 Presentation Demo Script

1. **Launch App**: Open `design/index.html` in browser.
2. **Start Demo**: Click **"Try Demo Dataset"** (or upload `plant_twin_data.csv`).
3. **Animate Shift**: Click **`▶ Play Shift`** in the top right of the timeline panel.
4. **Observe Drift**: Watch station **Paint-12** drift live from Green (`12`) → Yellow (`48`) → Orange (`74`) → Red (`91`).
5. **Trace Root Cause**: Click **Paint-12** or **Paint-14** to open the **Insight Engine** drawer and inspect the **Upstream Defect Trace (DAG)** card isolating upstream root causes (e.g. *“Body-07”*).