// ============================================================
// DigitalTwin.ai — Timeline Component (dot / connecting-line style)
// Renders into the classes already defined in styles.css:
//   .tl-row, .tl-connecting-line, .tl-milestone-dot, .dot--<level>,
//   .dot-inner, .pulse-ring, .tl-minor-tick, .tl-header-row,
//   .tl-time-label, .tl-station-label, .sensor-poor-dot
//
// A "milestone" dot is drawn wherever a station's risk LEVEL
// changes from the previous step (or at the very first / last
// step, so every row always shows a clear start and current
// state). Every other step is a small minor tick — still
// hoverable/clickable, just visually quieter.
//
// NOTE: STATIONS, getRiskLevel, getRiskColor, getRiskLabel are
// defined in data.js, which must load before this file.
// ============================================================

const TL_TIMES = [
  '08:00','08:20','08:40','09:00','09:20','09:40',
  '10:00','10:20','10:40','11:00','11:20','11:40',
  '12:00','12:20','12:40','13:00','13:20','13:40',
  '14:00','14:20','14:40','15:00','15:20','15:40'
];

const CELL_W  = 36;  // px per time-step column
const CELL_G  = 5;   // gap between columns
const LABEL_W = 82;  // station name column width

// Extend a 10-point base risk array to 24 points with momentum + noise,
// so the timeline is wider than the panel and scrolls horizontally.
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

STATIONS.forEach(s => {
  if (!s._risk24) s._risk24 = extendRisk(s.risk);
});

// Which indices in a risk array should render as full milestone dots:
// the first step, the last step, and any step where the risk LEVEL
// (low/medium/high/critical) differs from the step before it.
function getMilestoneIndices(risks) {
  const milestones = new Set([0, risks.length - 1]);
  for (let i = 1; i < risks.length; i++) {
    if (getRiskLevel(risks[i]) !== getRiskLevel(risks[i - 1])) {
      milestones.add(i);
    }
  }
  return milestones;
}

// ── RENDER ────────────────────────────────────────────────────
function renderTimeline(stations) {
  stations = stations || STATIONS;
  const container = document.getElementById('timelineContainer');
  if (!container) return;

  const totalW = LABEL_W + TL_TIMES.length * (CELL_W + CELL_G);

  let html = `<div class="tl-scroll-wrap"><div class="tl-inner" style="width:${totalW}px;">`;

  // Header — time labels every 3rd step to avoid crowding
  html += `<div class="tl-header-row">`;
  html += `<div style="width:${LABEL_W}px;flex-shrink:0;"></div>`;
  TL_TIMES.forEach((t, i) => {
    const isActive = (typeof currentTimeIndex !== 'undefined' && i === currentTimeIndex);
    const activeStyle = isActive ? 'color:var(--brand-cyan);font-weight:700;border-bottom:2px solid var(--brand-cyan);' : '';
    html += `<div class="tl-time-label" style="width:${CELL_W}px;${activeStyle}">${i % 3 === 0 || isActive ? t : ''}</div>`;
  });
  html += `</div>`;

  // Station rows
  stations.forEach(s => {
    const risks      = s._risk24;
    const milestones = getMilestoneIndices(risks);
    const badge = s.sensor
      ? ''
      : `<span class="sensor-poor-dot" title="Estimated — sensor-poor">~</span>`;

    html += `<div class="tl-row">`;
    html += `<div class="tl-station-label" style="width:${LABEL_W}px;">${badge}<span>${s.name}</span></div>`;

    // Connecting line spans only the dot area, not the label column
    html += `<div class="tl-connecting-line" style="left:${LABEL_W}px;right:0;"></div>`;

    risks.forEach((score, ti) => {
      const level    = getRiskLevel(score);
      const isMile   = milestones.has(ti);
      const isActive = (typeof currentTimeIndex !== 'undefined' && ti === currentTimeIndex);
      const activeHalo = isActive ? 'box-shadow: 0 0 10px var(--brand-cyan), 0 0 4px #ffffff;' : '';

      const handlers = `
        onmouseenter="showTooltip(event,'${s.id}',${ti})"
        onmouseleave="hideTooltip()"
        onclick="openInsight('${s.id}')"`;

      if (isMile) {
        const pulse = level === 'critical' ? ' pulse-ring' : '';
        html += `
          <div style="width:${CELL_W}px;display:flex;justify-content:center;position:relative;z-index:2;">
            <div class="tl-milestone-dot dot--${level}${pulse}" style="${activeHalo}" ${handlers}>
              <span class="dot-inner"></span>
            </div>
          </div>`;
      } else {
        html += `
          <div style="width:${CELL_W}px;display:flex;justify-content:center;position:relative;z-index:2;">
            <div class="tl-minor-tick" style="${activeHalo}" ${handlers}></div>
          </div>`;
      }
    });

    html += `</div>`;
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
      ? `<span style="color:var(--risk-critical)">▲ +${d}</span>`
      : d < 0
      ? `<span style="color:var(--risk-low)">▼ ${d}</span>`
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
    <div><span class="tooltip-risk-badge badge--${level}">${getRiskLabel(level)}</span></div>
    ${sensorNote}
  `;
  positionTooltip(e);
  tooltip.classList.add('visible');
}

function hideTooltip() {
  tooltip.classList.remove('visible');
}

function positionTooltip(e) {
  const pad = 14, tw = 210, th = 180;
  let left = e.clientX + pad;
  let top  = e.clientY + pad;
  if (left + tw > window.innerWidth)  left = e.clientX - tw - pad;
  if (top  + th > window.innerHeight) top  = e.clientY - th - pad;
  tooltip.style.left = left + 'px';
  tooltip.style.top  = top  + 'px';
}

document.addEventListener('mousemove', e => {
  if (tooltip.classList.contains('visible')) positionTooltip(e);
});
