# DigitalTwin.ai — Project Context Document
> For handoff to other AI assistants. Last updated: Day 1 of 8.

---

## What This Is

A hackathon submission for **Accenture Innovation Challenge 2026 — Round 2**.

The project is called **DigitalTwin.ai** — a web-based predictive digital twin for vehicle assembly lines. It is a **proof-of-concept prototype**, not a production system.

The core demo: upload a CSV of production data → the system predicts which assembly stations are about to become bottlenecks → shows it visually before it happens.

---

## Team

- 3 people
- 8 days total (currently Day 1)
- Frontend is being built first; backend (FastAPI + ML) comes later

---

## The One Demo Scenario (freeze this, don't change it)

Paint-12 gradually drifts from risk score 12 → 91 over a shift.
Downstream stations Paint-14 and Paint-16 show cascading starvation risk.
The system catches this before it becomes a full bottleneck.

---

## Parameters We Decided On

- **40 stations** total: Body (15) → Paint (10) → Final Assembly (15)
- **Takt time**: 60 seconds baseline
- **Sensor coverage**: 28 stations fully instrumented, 12 sensor-poor (estimated)
- **Bottleneck thresholds**:
  - Cycle time > 72s (>20% over takt) → alert
  - Queue depth grows >3 vehicles in 5 min → alert
  - Utilisation >90% sustained 3+ min → alert
- **Amber** = 1 signal breached. **Red** = 2+ signals breached
- **Buffer** between stations: 5 vehicles
- **Starvation risk** fires when buffer drains below 2 vehicles

---

## Tech Stack (Lean — 3 people, 8 days)

| Layer | Tool |
|---|---|
| Frontend | Plain HTML + CSS + Vanilla JS (no framework) |
| Charts/viz | Custom built — no chart library |
| Backend (not yet built) | FastAPI (Python) |
| ML (not yet built) | Scikit-learn — Isolation Forest + SPC thresholds |
| Data | Synthetic — hardcoded in data.js, no real DB |
| "Streaming" | Pre-generated JSON array, frontend polls every 2s |

No Kafka, no InfluxDB, no React, no build step. Everything opens directly in a browser.

---

## File Structure

```
Accenture/
├── design/
│   ├── index.html           ✅ Done — Landing/upload page
│   ├── dashboard.html       ✅ Done — Main dashboard shell
│   ├── styles.css           ✅ Done — Full design system
│   └── components/
│       ├── data.js          ✅ Done — All station data + helpers
│       ├── timeline.js      ✅ Done — Heatmap viz (pill style, scrollable)
│       ├── table.js         ✅ Done — Sortable station table
│       └── insight.js       ✅ Done — Right-side detail panel
├── twin_ai_PRD.txt          ✅ Reference
├── CONTEXT.md               ✅ This file
└── Readme.md                ✅ Done
```

---

## What Each File Does

### `index.html`
- Landing page with drag & drop CSV upload
- "Try Demo Dataset" button (skips upload, goes straight to processing)
- Animated processing overlay: 6 steps (Reading → Validating → Engineering → Processing → Predicting → Building)
- Redirects to `dashboard.html` on completion

### `styles.css`
Full design system. Dark industrial aesthetic. Key CSS variables:
```css
--bg-base:       #0a0e1a
--bg-surface:    #0f1526
--bg-card:       #141b2d
--brand-cyan:    #00d4ff
--risk-low:      #22c55e   (green)
--risk-medium:   #eab308   (yellow)
--risk-high:     #f97316   (orange)
--risk-critical: #ef4444   (red)
```
Risk scale: 0–24 = low, 25–49 = medium, 50–74 = high, 75–100 = critical.

### `dashboard.html`
Shell page. Loads all 4 component scripts in order:
1. `data.js` (must be first — defines STATIONS and helpers)
2. `timeline.js`
3. `table.js`
4. `insight.js`

Contains:
- Nav bar (Upload / Dashboard / Analytics tabs)
- Line Alpha live badge with pulsing green dot
- 3 filter dropdowns: Risk Level / Zone / Time Range
- 4 KPI cards: Active Stations (42), High Risk Bottlenecks (5), Avg Utilisation (78.4%), Avg Queue Time (2.8m)
- Panel slot for timeline heatmap
- Panel slot for station table
- Right-side insight panel

### `data.js`
Single source of truth. Defines:
- `STATIONS` array — 12 stations (representative sample of the 40-station line)
- Each station has: `id, name, zone, queue, takt, util, sensor, risk[], factors{}, confidence`
- `getRiskLevel(score)` → 'low' | 'medium' | 'high' | 'critical'
- `getRiskColor(score)` → CSS variable string
- `getRiskLabel(level)` → display string
- `activeFilters` object + `applyFilters()` function

**Key stations:**
| Station | Zone | Current Risk | Notes |
|---|---|---|---|
| Paint-12 | Paint | 91 | THE scenario station — drifts green→red |
| Body-07 | Body | 76 | Secondary high-risk |
| Paint-14 | Paint | 72 | Downstream cascade from Paint-12 |
| Paint-16 | Paint | 65 | Also affected by cascade |
| Final-03 | Final | 52 | Medium-high |
| Body-11 | Body | 17 | Sensor-poor example |
| Paint-14 | Paint | 72 | Sensor-poor example |
| Final-08 | Final | 10 | Sensor-poor example |

### `timeline.js`
- Renders the heatmap as pill-shaped cells (rounded, not blocky squares)
- 24 time steps (08:00–15:40, every 20 min) — horizontally scrollable
- Base 10-point risk arrays extended to 24 via momentum extrapolation
- Uses `TL_TIMES` (not `TIME_LABELS`) to avoid conflict with data.js
- Each cell: hover shows tooltip, click opens insight panel
- Sensor-poor stations show `~` badge on their label
- Tooltip shows: station name, time, trend arrow, queue/takt/util/risk, sensor warning

### `table.js`
- Renders sortable station table
- Default sort: Bottleneck Risk descending
- Columns: Station, Zone, Queue, Takt, Utilisation, Bottleneck Risk
- Each row has: zone colour badge, risk bar, trend arrow, risk level tag
- Click any row → opens insight panel
- Sensor-poor stations show `~est` badge

### `insight.js`
- Right-side panel, opens when a cell or table row is clicked
- Shows: station name + zone, current risk score + level badge
- Predicted next-window risk (linear extrapolation of last 3 steps)
- Trend: Increasing / Decreasing / Stable
- Contributing factors (sorted by impact): Queue Growth Rate, Cycle Time Deviation, Utilisation, Anomaly Score — each with a bar and description
- Prediction confidence % (lower for sensor-poor stations)
- Station metrics snapshot (queue, takt, util)

---

## Risk Score Formula (from PRD)

```
Risk = 0.30 × cycle_time_deviation
     + 0.25 × queue_growth
     + 0.20 × utilisation
     + 0.15 × anomaly_score
     + 0.10 × upstream_risk
```
(Currently hardcoded in data.js. Backend will compute this properly.)

---

## What Is NOT Built Yet

| Thing | Status | Notes |
|---|---|---|
| Backend (FastAPI) | ❌ Not started | Person B's job |
| ML prediction engine | ❌ Not started | Person A's job — Isolation Forest + SPC |
| CSV upload → processing | ❌ Not wired | Frontend upload works visually, not functionally |
| Real data pipeline | ❌ Not started | All data is hardcoded in data.js |
| Analytics tab | ❌ Placeholder | Nav link exists, no page |
| Live polling / animation | ❌ Not started | Risk scores are static, not animating over time yet |

---

## Known Issues / Fixed Bugs

- `TIME_LABELS` was declared with `const` in both `data.js` and `timeline.js` — caused browser to throw error and render nothing. Fixed by renaming to `TL_TIMES` in timeline.js and removing it from data.js entirely.

---

## Design Decisions Made

- **No framework** — plain HTML/CSS/JS only. Opens in browser with no build step.
- **No chart library** — custom CSS grid heatmap is sufficient and faster to build.
- **Pill-shaped cells** in heatmap (not blocky rectangles) — user preference.
- **Horizontal scroll** on timeline — 24 time steps wider than viewport.
- **Pre-generated data** — no real-time complexity; all risk scores are pre-computed arrays.
- **Sensor-poor stations** shown with `~` badge — key differentiator for the pitch.
- **Single demo scenario** — Paint-12 drift, frozen, demos cleanly every time.

---

## What To Build Next (in order)

1. **Animate the timeline** — step through time steps automatically, simulating live monitoring (setTimeout loop advancing a "current time" cursor across the heatmap)
2. **Wire the CSV upload** — parse uploaded CSV, map columns to STATIONS format, replace hardcoded data
3. **FastAPI backend** — POST /api/upload, GET /api/predictions/{job_id}
4. **ML pipeline** — Isolation Forest anomaly detection + SPC thresholds on simulated data
5. **Analytics page** — trend charts, station ranking, shift summary

---

## Coding Rules (follow these)

- All JS goes in `components/` as separate files
- `data.js` MUST load before all other scripts (it defines globals everything else uses)
- Never redeclare `const STATIONS` or any helper from `data.js` in other files
- CSS variables only — never hardcode hex colours in JS or HTML
- No `npm`, no build step, no frameworks
- Keep it openable by double-clicking the HTML file in any browser
