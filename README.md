# DigitalTwin.ai — Frontend

## File Structure
```
Accenture/
├── design/
│   ├── index.html          ← Landing / Upload page
│   ├── dashboard.html      ← Main dashboard (Batch 2+)
│   ├── styles.css          ← Global styles (all pages share this)
│   └── components/
│       ├── timeline.js     ← Interactive heatmap (Batch 3)
│       ├── table.js        ← Station table + sorting (Batch 4)
│       └── insight.js      ← Right-side insight panel (Batch 4)
├── twin_ai_PRD.txt
└── Readme.md
```

## Pages
- `index.html` — Upload page with drag & drop, demo dataset, processing animation
- `dashboard.html` — Twin dashboard with heatmap, KPIs, table, insight panel

## Run Locally
Just open `index.html` in a browser. No build step needed — pure HTML/CSS/JS.

## Design System
All CSS variables are in `styles.css` under `:root`.
Risk colour scale: `--risk-low` (green) → `--risk-medium` (yellow) → `--risk-high` (orange) → `--risk-critical` (red)