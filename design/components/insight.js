// ============================================================
// DigitalTwin.ai — Insight Panel Component
// Right-side detail panel, opens on station click
// ============================================================

function openInsight(stationId) {
  window._lastOpenedStationId = stationId;
  const station = STATIONS.find(s => s.id === stationId);
  if (!station) return;

  const currentRisk = typeof getCurrentRisk === 'function' ? getCurrentRisk(station) : station.risk[station.risk.length - 1];
  const arr = typeof getRiskArray === 'function' ? getRiskArray(station) : station.risk;
  const curIdx = typeof currentTimeIndex !== 'undefined' ? Math.min(currentTimeIndex, arr.length - 1) : arr.length - 1;
  const prevIdx = Math.max(0, curIdx - 1);
  const prevRisk = arr[prevIdx];
  const level       = getRiskLevel(currentRisk);
  const color       = getRiskColor(currentRisk);

  // Predicted next risk (simple linear extrapolation of last 3 steps)
  const last3   = arr.slice(Math.max(0, curIdx - 2), curIdx + 1);
  const avgDelta = last3.length >= 3 ? ((last3[2] - last3[1]) + (last3[1] - last3[0])) / 2 : (currentRisk - prevRisk);
  const predicted = Math.min(100, Math.max(0, Math.round(currentRisk + avgDelta)));

  // Trend
  const delta = currentRisk - prevRisk;
  let trendClass, trendIcon, trendText;
  if (delta > 3) {
    trendClass = 'trend--up';
    trendIcon  = '▲';
    trendText  = `Increasing (+${delta} from prev)`;
  } else if (delta < -3) {
    trendClass = 'trend--down';
    trendIcon  = '▼';
    trendText  = `Decreasing (${delta} from prev)`;
  } else {
    trendClass = 'trend--flat';
    trendIcon  = '—';
    trendText  = 'Stable';
  }

  // Contributing factors — sorted descending
  const factors = [
    { name: 'Queue Growth Rate',    pct: station.factors.queueGrowth,    desc: 'Input queue is growing significantly faster than processing output, indicating a structural blockage upstream.' },
    { name: 'Cycle Time Deviation', pct: station.factors.cycleDeviation,  desc: 'Robotic arm calibration phase taking longer than standard baseline parameters.' },
    { name: 'Utilisation',          pct: station.factors.utilisation,     desc: 'Station is running near capacity with insufficient slack to absorb variation.' },
    { name: 'Anomaly Score',        pct: station.factors.anomaly,         desc: 'Isolation Forest detected multivariate signal pattern diverging from normal operating envelope.' },
  ].sort((a, b) => b.pct - a.pct);

  // Sensor note
  const sensorHtml = station.sensor
    ? `<div class="confidence-row">
         <span class="confidence-label">Prediction Confidence</span>
         <span class="confidence-value">${station.confidence}%</span>
       </div>`
    : `<div class="confidence-row" style="flex-direction:column;align-items:flex-start;gap:0.3rem;">
         <div style="display:flex;justify-content:space-between;width:100%;">
           <span class="confidence-label">Prediction Confidence</span>
           <span class="confidence-value" style="color:var(--risk-medium);">${station.confidence}%</span>
         </div>
         <span style="font-size:0.68rem;color:var(--risk-medium);">
           ~ Estimated — station has partial sensor coverage. Confidence reduced.
         </span>
       </div>`;

  // Predicted risk display
  const predColor   = getRiskColor(predicted);
  const predLevel   = getRiskLabel(getRiskLevel(predicted));
  const predDelta   = predicted - currentRisk;
  const predDeltaStr = predDelta >= 0 ? `+${predDelta}` : `${predDelta}`;

  document.getElementById('insightBody').innerHTML = `
    <!-- Station name + zone -->
    <div>
      <div class="insight-station-name">${station.name}</div>
      <div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.15rem;">${station.zone} Zone</div>
    </div>

    <!-- Current risk score -->
    <div>
      <div class="insight-section-label">Current Risk</div>
      <div class="insight-risk-score">
        <span class="insight-risk-number" style="color:${color};">${currentRisk}</span>
        <span class="insight-risk-denom">/ 100</span>
        <span class="risk-tag" style="background:${color}22;color:${color};margin-left:0.4rem;">${getRiskLabel(level)}</span>
      </div>
    </div>

    <!-- Predicted risk -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;">
      <div style="background:var(--bg-card-2);border-radius:var(--radius-sm);padding:0.6rem 0.75rem;">
        <div style="font-size:0.65rem;color:var(--text-muted);margin-bottom:0.25rem;text-transform:uppercase;letter-spacing:0.08em;">Predicted</div>
        <div style="font-size:1.3rem;font-weight:700;color:${predColor};">${predicted}</div>
        <div style="font-size:0.7rem;color:${predColor};">${predDeltaStr} next window</div>
      </div>
      <div style="background:var(--bg-card-2);border-radius:var(--radius-sm);padding:0.6rem 0.75rem;">
        <div style="font-size:0.65rem;color:var(--text-muted);margin-bottom:0.25rem;text-transform:uppercase;letter-spacing:0.08em;">Trend</div>
        <div class="insight-trend ${trendClass}" style="margin-top:0.1rem;">
          ${trendIcon} ${trendText.split(' ')[0]}
        </div>
        <div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.3rem;">${trendText}</div>
      </div>
    </div>

    <!-- Contributing factors -->
    <div>
      <div class="insight-section-label">Primary Risk Factors</div>
      ${factors.map(f => {
        const fColor = f.pct >= 70
          ? 'var(--risk-critical)'
          : f.pct >= 45
          ? 'var(--risk-high)'
          : f.pct >= 25
          ? 'var(--risk-medium)'
          : 'var(--risk-low)';
        return `
          <div class="factor-row">
            <div class="factor-top">
              <span class="factor-name">${f.name}</span>
              <span class="factor-pct" style="color:${fColor};">${f.pct}%</span>
            </div>
            <div class="factor-bar-bg">
              <div class="factor-bar-fill" style="width:${f.pct}%;background:${fColor};"></div>
            </div>
            <div class="factor-desc">${f.desc}</div>
          </div>`;
      }).join('')}
    </div>

    <!-- Confidence -->
    ${sensorHtml}

    <!-- Metrics snapshot -->
    <div>
      <div class="insight-section-label">Station Metrics</div>
      <div style="display:flex;flex-direction:column;gap:0.3rem;">
        ${[
          ['Queue Time',   station.queue + ' min'],
          ['Takt Time',    station.takt + 's'],
          ['Utilisation',  station.util + '%'],
        ].map(([k,v]) => `
          <div class="confidence-row">
            <span class="confidence-label">${k}</span>
            <span style="font-weight:600;color:var(--text-primary);">${v}</span>
          </div>`).join('')}
      </div>
    </div>
  `;
}

function closeInsight() {
  document.getElementById('insightBody').innerHTML = `
    <p style="font-size:0.8rem;color:var(--text-muted);text-align:center;padding:1.5rem 0;">
      Click any station or heatmap cell to see detailed analysis.
    </p>
  `;
}
