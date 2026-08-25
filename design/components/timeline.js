// ============================================================
// DigitalTwin.ai — Timeline Component (Line + Milestone Dots)
// Renders station performance as horizontal lines with coloured
// milestone dots whenever bottleneck probability shifts levels.
// ============================================================

const TL_TIMES = [
  '08:00','08:20','08:40','09:00','09:20','09:40',
  '10:00','10:20','10:40','11:00','11:20','11:40',
  '12:00','12:20','12:40','13:00','13:20','13:40',
  '14:00','14:20','14:40','15:00','15:20','15:40'
];

const CELL_W  = 36;  // px per time step
const CELL_G  = 5;   // gap between steps
const LABEL_W = 82;  // station name column

// Extend a 10-point risk array to 24 points with momentum + noise
function extendRisk(base) {
  const r = [...base];
  while (r.length < TL_TIMES.length) {
    const last  = r[r.length - 1];
    const prev  = r[r.length - 2] ?? last;
    const delta = last - prev;
    const noise = (Math.random() - 0.48) * 4;
    r.push(Math.min(100, Math.max(0, Math.round(last + delta * 0.6 + noise))));
  }
  return r;
}

// Attach extended arrays once
STATIONS.forEach(s => {
  if (!s._risk24) s._risk24 = extendRisk(s.risk);
});

// ── RENDER ────────────────────────────────────────────────────
function renderTimeline(stations) {
  stations = stations || STATIONS;
  const container = document.getElementById('timelineContainer');
  if (!container) return;

  const totalW = LABEL_W + TL_TIMES.length * (CELL_W + CELL_G);
  let html = `<div class="tl-scroll-wrap"><div class="tl-inner" style="width:${totalW}px;">`;

  // Header row (Time Labels)
  html += `<div class="tl-header-row">`;
  html += `<div style="width:${LABEL_W}px;flex-shrink:0;"></div>`;
  TL_TIMES.forEach((t, i) => {
    html += `<div class="tl-time-label" style="width:${CELL_W}px;">${i % 3 === 0 ? t : ''}</div>`;
  });
  html += `</div>`;

  // Station rows (Line + Milestone Dots)
  stations.forEach(s => {
    const risks = s._risk24;
    const badge = s.sensor ? '' : `<span class="sensor-poor-dot" title="Estimated — sensor-poor">~</span>`;

    html += `<div class="tl-row tl-line-row">`;
    html += `<div class="tl-station-label" style="width:${LABEL_W}px;">${badge}<span>${s.name}</span></div>`;

    // Track container for horizontal line & milestone dots
    html += `<div class="tl-track-container" style="flex:1; display:flex; gap:${CELL_G}px; position:relative; align-items:center;">`;
    
    // Background connecting line across row
    html += `<div class="tl-connecting-line"></div>`;

    let prevLevel = null;

    risks.forEach((score, ti) => {
      const level = getRiskLevel(score);
      // Determine if this timestamp is a milestone (initial point, risk level change, or critical peak)
      const isMilestone = (ti === 0) || (level !== prevLevel) || (level === 'critical' && score >= 85);
      prevLevel = level;

      if (isMilestone) {
        html += `
          <div class="tl-step-node" style="width:${CELL_W}px; justify-content:center; display:flex; position:relative; z-index:2;">
            <div class="tl-milestone-dot dot--${level} ${level === 'critical' ? 'pulse-ring' : ''}"
              onmouseenter="showTooltip(event,'${s.id}',${ti})"
              onmouseleave="hideTooltip()"
              onclick="openInsight('${s.id}')"
              title="${s.name} @ ${TL_TIMES[ti]}: ${score}% (${level.toUpperCase()})">
              <span class="dot-inner"></span>
            </div>
          </div>`;
      } else {
        // Minor tick along line for continuous hover accessibility
        html += `
          <div class="tl-step-node" style="width:${CELL_W}px; justify-content:center; display:flex; position:relative; z-index:1;">
            <div class="tl-minor-tick tick--${level}"
              onmouseenter="showTooltip(event,'${s.id}',${ti})"
              onmouseleave="hideTooltip()"
              onclick="openInsight('${s.id}')">
            </div>
          </div>`;
      }
    });

    html += `</div>`; // end tl-track-container
    html += `</div>`; // end tl-row
  });

  html += `</div></div>`;
  container.innerHTML = html;
}

// ── TOOLTIP ───────────────────────────────────────────────────
const tooltip = document.getElementById('tooltip');

function showTooltip(e, stationId, ti) {
  const s = STATIONS.find(x => x.id === stationId);
  if (!s) return;

  const score = s._risk24[ti];
  const level = getRiskLevel(score);
  const time  = TL_TIMES[ti] || '';

  let trend = '';
  if (ti > 0) {
    const d = score - s._risk24[ti - 1];
    trend = d > 0
      ? `<span style="color:var(--risk-critical)">▲ +${d}%</span>`
      : d < 0
      ? `<span style="color:var(--risk-low)">▼ ${d}%</span>`
      : `<span style="color:var(--text-muted)">— stable</span>`;
  }

  const sensorNote = s.sensor ? '' : `
    <div style="margin-top:0.5rem;font-size:0.68rem;color:var(--risk-medium);">
      ~ Estimated — sensor-poor station
    </div>`;

  tooltip.innerHTML = `
    <div class="tooltip-station">${s.name}</div>
    <div class="tooltip-time">${time} &nbsp;·&nbsp; ${trend}</div>
    <div class="tooltip-row"><span class="tooltip-key">Queue Time</span><span class="tooltip-val">${s.queue} min</span></div>
    <div class="tooltip-row"><span class="tooltip-key">Takt Time</span><span class="tooltip-val">${s.takt}s</span></div>
    <div class="tooltip-row"><span class="tooltip-key">Utilisation</span><span class="tooltip-val">${s.util}%</span></div>
    <div class="tooltip-row">
      <span class="tooltip-key">Bottleneck Risk</span>
      <span class="tooltip-val" style="color:${getRiskColor(score)}">${score} / 100</span>
    </div>
    <div><span class="tooltip-risk-badge badge--${level}">${getRiskLabel(level)} Milestone</span></div>
    ${sensorNote}
  `;
  positionTooltip(e);
  tooltip.classList.add('visible');
}

function hideTooltip() {
  if (tooltip) tooltip.classList.remove('visible');
}

function positionTooltip(e) {
  if (!tooltip) return;
  const pad = 14, tw = 210, th = 180;
  let left = e.clientX + pad;
  let top  = e.clientY + pad;
  if (left + tw > window.innerWidth)  left = e.clientX - tw - pad;
  if (top  + th > window.innerHeight) top  = e.clientY - th - pad;
  tooltip.style.left = left + 'px';
  tooltip.style.top  = top  + 'px';
}

document.addEventListener('mousemove', e => {
  if (tooltip && tooltip.classList.contains('visible')) positionTooltip(e);
});

