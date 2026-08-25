// ============================================================
// DigitalTwin.ai — Station Table Component
// Sortable table of all stations
// ============================================================

let sortKey = 'risk';
let sortDir = -1; // -1 = descending, 1 = ascending

function sortTable(key) {
  if (sortKey === key) {
    sortDir *= -1;
  } else {
    sortKey = key;
    sortDir = key === 'risk' ? -1 : 1;
  }

  // Update header arrows
  document.querySelectorAll('thead th').forEach(th => {
    th.classList.remove('sorted');
    th.querySelector('.sort-arrow').textContent = '↕';
  });
  const activeHeader = document.getElementById(`th-${key}`);
  if (activeHeader) {
    activeHeader.classList.add('sorted');
    activeHeader.querySelector('.sort-arrow').textContent = sortDir === -1 ? '↓' : '↑';
  }

  const filtered = getFilteredStations();
  renderTable(filtered);
}

function getFilteredStations() {
  return STATIONS.filter(s => {
    const currentRisk = s.risk[s.risk.length - 1];
    const level = getRiskLevel(currentRisk);
    if (activeFilters.risk !== 'all' && level !== activeFilters.risk) return false;
    if (activeFilters.zone !== 'all' && !s.zone.startsWith(activeFilters.zone)) return false;
    return true;
  });
}

function renderTable(stations) {
  stations = stations || STATIONS;

  // Sort
  const sorted = [...stations].sort((a, b) => {
    let av, bv;
    switch (sortKey) {
      case 'name':  av = a.name;  bv = b.name;  break;
      case 'zone':  av = a.zone;  bv = b.zone;  break;
      case 'queue': av = a.queue; bv = b.queue; break;
      case 'takt':  av = a.takt;  bv = b.takt;  break;
      case 'util':  av = a.util;  bv = b.util;  break;
      case 'risk':
      default:
        av = a.risk[a.risk.length - 1];
        bv = b.risk[b.risk.length - 1];
    }
    if (av < bv) return -1 * sortDir;
    if (av > bv) return  1 * sortDir;
    return 0;
  });

  const tbody = document.getElementById('stationTableBody');
  if (!tbody) return;

  tbody.innerHTML = sorted.map(station => {
    const currentRisk = station.risk[station.risk.length - 1];
    const prevRisk    = station.risk[station.risk.length - 2];
    const level       = getRiskLevel(currentRisk);
    const color       = getRiskColor(currentRisk);

    // Trend vs previous step
    const delta = currentRisk - prevRisk;
    let trendHtml;
    if      (delta > 3)  trendHtml = `<span style="color:var(--risk-critical);font-size:0.72rem;">▲ +${delta}</span>`;
    else if (delta < -3) trendHtml = `<span style="color:var(--risk-low);font-size:0.72rem;">▼ ${delta}</span>`;
    else                 trendHtml = `<span style="color:var(--text-muted);font-size:0.72rem;">—</span>`;

    // Sensor badge
    const sensorBadge = station.sensor
      ? ''
      : `<span style="font-size:0.65rem;color:var(--risk-medium);margin-left:4px;" title="Estimated — sensor-poor">~est</span>`;

    // Risk bar colour
    const barColor = color;

    return `
      <tr onclick="openInsight('${station.id}')" title="Click for detailed analysis">
        <td class="td-station">
          ${station.name}${sensorBadge}
        </td>
        <td>
          <span style="
            display:inline-block;
            padding:0.15rem 0.45rem;
            border-radius:4px;
            font-size:0.68rem;
            font-weight:600;
            background:${zoneColor(station.zone)};
            color:var(--text-primary);
          ">${station.zone}</span>
        </td>
        <td>${station.queue} min</td>
        <td>${station.takt}s</td>
        <td>${station.util}%</td>
        <td class="td-risk">
          <div class="risk-bar-wrap">
            <div class="risk-bar-bg">
              <div class="risk-bar-fill" style="width:${currentRisk}%;background:${barColor};"></div>
            </div>
            <span style="color:${color};min-width:28px;">${currentRisk}</span>
            ${trendHtml}
            <span class="risk-tag" style="background:${color}22;color:${color};">${getRiskLabel(level)}</span>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function zoneColor(zone) {
  switch (zone) {
    case 'Body':  return 'rgba(99,102,241,0.25)';
    case 'Paint': return 'rgba(20,184,166,0.25)';
    case 'Final': return 'rgba(245,158,11,0.20)';
    default:      return 'rgba(255,255,255,0.08)';
  }
}
