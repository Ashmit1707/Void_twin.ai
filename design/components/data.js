// ============================================================
// DigitalTwin.ai — Shared Data
// All components read from this file.
// ============================================================

// STATIONS — 12 shown in the heatmap (representative sample of 40-station line)
// risk[] = bottleneck risk score 0–100 at each time step (10 base steps)
// sensor: true = fully instrumented, false = sensor-poor (estimated)
const STATIONS = [
  {
    id: 'B-01', name: 'Body-01', zone: 'Body',
    queue: 1.2, takt: 52, util: 71, sensor: true,
    risk: [8, 10, 9, 11, 10, 12, 11, 13, 12, 14],
    factors: { queueGrowth: 12, cycleDeviation: 9,  utilisation: 71, anomaly: 5  },
    confidence: 94
  },
  {
    id: 'B-04', name: 'Body-04', zone: 'Body',
    queue: 2.1, takt: 54, util: 78, sensor: true,
    risk: [14, 16, 18, 20, 22, 25, 28, 30, 33, 36],
    factors: { queueGrowth: 28, cycleDeviation: 32, utilisation: 78, anomaly: 18 },
    confidence: 91
  },
  {
    id: 'B-07', name: 'Body-07', zone: 'Body',
    queue: 5.1, takt: 48, util: 89, sensor: true,
    risk: [22, 28, 35, 42, 50, 58, 64, 70, 74, 76],
    factors: { queueGrowth: 71, cycleDeviation: 68, utilisation: 89, anomaly: 44 },
    confidence: 88
  },
  {
    id: 'B-11', name: 'Body-11', zone: 'Body',
    queue: 1.8, takt: 55, util: 74, sensor: false,
    risk: [10, 11, 13, 12, 14, 15, 14, 16, 15, 17],
    factors: { queueGrowth: 15, cycleDeviation: 12, utilisation: 74, anomaly: 8  },
    confidence: 67
  },
  {
    id: 'P-03', name: 'Paint-03', zone: 'Paint',
    queue: 2.4, takt: 60, util: 76, sensor: true,
    risk: [18, 20, 22, 24, 26, 28, 30, 32, 34, 36],
    factors: { queueGrowth: 30, cycleDeviation: 26, utilisation: 76, anomaly: 14 },
    confidence: 89
  },
  {
    id: 'P-12', name: 'Paint-12', zone: 'Paint',
    queue: 8.2, takt: 52, util: 94, sensor: true,
    risk: [12, 18, 31, 48, 62, 67, 74, 81, 87, 91],
    factors: { queueGrowth: 87, cycleDeviation: 79, utilisation: 94, anomaly: 61 },
    confidence: 78
  },
  {
    id: 'P-14', name: 'Paint-14', zone: 'Paint',
    queue: 3.9, takt: 58, util: 81, sensor: false,
    risk: [8, 9, 10, 14, 22, 38, 51, 62, 68, 72],
    factors: { queueGrowth: 62, cycleDeviation: 38, utilisation: 81, anomaly: 29 },
    confidence: 64
  },
  {
    id: 'P-16', name: 'Paint-16', zone: 'Paint',
    queue: 2.7, takt: 56, util: 79, sensor: true,
    risk: [10, 12, 14, 18, 28, 41, 53, 59, 63, 65],
    factors: { queueGrowth: 54, cycleDeviation: 45, utilisation: 79, anomaly: 22 },
    confidence: 85
  },
  {
    id: 'F-02', name: 'Final-02', zone: 'Final',
    queue: 1.5, takt: 62, util: 69, sensor: true,
    risk: [9, 10, 11, 10, 12, 13, 12, 14, 13, 15],
    factors: { queueGrowth: 13, cycleDeviation: 11, utilisation: 69, anomaly: 6  },
    confidence: 93
  },
  {
    id: 'F-03', name: 'Final-03', zone: 'Final',
    queue: 3.2, takt: 55, util: 81, sensor: true,
    risk: [28, 30, 33, 36, 40, 44, 48, 50, 52, 52],
    factors: { queueGrowth: 44, cycleDeviation: 48, utilisation: 81, anomaly: 31 },
    confidence: 87
  },
  {
    id: 'F-08', name: 'Final-08', zone: 'Final',
    queue: 1.1, takt: 60, util: 66, sensor: false,
    risk: [6, 7, 8, 7, 9, 8, 10, 9, 11, 10],
    factors: { queueGrowth: 9, cycleDeviation: 7, utilisation: 66, anomaly: 4   },
    confidence: 61
  },
  {
    id: 'F-15', name: 'Final-15', zone: 'Final',
    queue: 2.0, takt: 58, util: 73, sensor: true,
    risk: [15, 16, 18, 20, 22, 24, 26, 28, 30, 32],
    factors: { queueGrowth: 26, cycleDeviation: 22, utilisation: 73, anomaly: 12 },
    confidence: 90
  },
];

// ── LOAD UPLOADED DATA (if the user came from index.html with a CSV) ──
// index.html stores parsed stations in localStorage before redirecting
// here. If present, it fully replaces the built-in demo stations —
// STATIONS stays a const binding, only its contents are swapped.
let uploadMeta = null; // { filename, uploadedAt, engine } — read by dashboard.html for the badge

(function loadUploadedStations() {
  try {
    const raw = localStorage.getItem('dt_upload');
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (parsed && Array.isArray(parsed.stations) && parsed.stations.length > 0) {
      STATIONS.length = 0;
      parsed.stations.forEach(s => STATIONS.push(s));
      uploadMeta = { filename: parsed.filename, uploadedAt: parsed.uploadedAt, engine: parsed.engine || 'local' };
    }
  } catch (e) {
    console.warn('Could not load uploaded station data — using demo dataset.', e);
  }
})();

// ── HELPERS ───────────────────────────────────────────────────
function getRiskLevel(score) {
  if (score >= 75) return 'critical';
  if (score >= 50) return 'high';
  if (score >= 25) return 'medium';
  return 'low';
}

function getRiskColor(score) {
  if (score >= 75) return 'var(--risk-critical)';
  if (score >= 50) return 'var(--risk-high)';
  if (score >= 25) return 'var(--risk-medium)';
  return 'var(--risk-low)';
}

function getRiskLabel(level) {
  return { low: 'Low', medium: 'Medium', high: 'High', critical: 'Critical' }[level];
}

// ── LIVE PLAYBACK STATE ──────────────────────────────────────
// currentTimeIndex points into each station's extended 24-step
// risk array (station._risk24, built by timeline.js). Every
// component reads "now" through getCurrentRisk() so the whole
// dashboard — heatmap, table, KPIs, insight panel — advances
// together when the timeline is played or scrubbed.
let currentTimeIndex = 23; // starts at the latest step (full shift)

function getRiskArray(station) {
  return station._risk24 || station.risk;
}

function getCurrentRisk(station) {
  const arr = getRiskArray(station);
  const idx = Math.min(currentTimeIndex, arr.length - 1);
  return arr[idx];
}

// Active filters state
let activeFilters = { risk: 'all', zone: 'all', time: 'all' };

function getFilteredStations() {
  return STATIONS.filter(s => {
    const level = getRiskLevel(getCurrentRisk(s));
    if (activeFilters.risk !== 'all' && level !== activeFilters.risk) return false;
    if (activeFilters.zone !== 'all' && !s.zone.startsWith(activeFilters.zone)) return false;
    return true;
  });
}

function applyFilters() {
  activeFilters.risk = document.getElementById('filterRisk').value;
  activeFilters.zone = document.getElementById('filterZone').value;
  activeFilters.time = document.getElementById('filterTime').value;
  refreshAll();
}

// Recompute and re-render everything for the current time step.
// Called by filters, by the play loop, and by the scrubber.
function refreshAll() {
  const filtered = getFilteredStations();
  renderTimeline(filtered);
  renderTable(filtered);
  updateKPIs(filtered);

  // Keep an open insight panel live-updating as time advances
  if (window._lastOpenedStationId) {
    openInsight(window._lastOpenedStationId);
  }
}

function updateKPIs(filtered) {
  const all = filtered && filtered.length ? filtered : STATIONS;

  const highRisk = all.filter(s => {
    const lvl = getRiskLevel(getCurrentRisk(s));
    return lvl === 'high' || lvl === 'critical';
  }).length;

  const avgUtil = all.reduce((sum, s) => sum + s.util, 0) / all.length;

  // Queue time nudges up as more stations go into high/critical risk —
  // simple illustrative correlation, not a real queueing model.
  const baseQueue = 1.6;
  const avgQueue = baseQueue + highRisk * 0.28;

  const elHighRisk = document.getElementById('kpiHighRisk');
  const elUtil      = document.getElementById('kpiUtil');
  const elQueue      = document.getElementById('kpiQueue');
  const elTimeLabel  = document.getElementById('kpiTimeLabel');

  if (elHighRisk) elHighRisk.textContent = highRisk;
  if (elUtil)      elUtil.textContent = avgUtil.toFixed(1) + '%';
  if (elQueue)      elQueue.textContent = avgQueue.toFixed(1) + 'm';
  if (elTimeLabel && typeof TL_TIMES !== 'undefined') {
    elTimeLabel.textContent = TL_TIMES[currentTimeIndex] || '';
  }
}
