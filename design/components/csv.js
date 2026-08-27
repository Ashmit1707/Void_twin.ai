// ============================================================
// DigitalTwin.ai — CSV Upload Pipeline
// Parses a production-floor CSV, validates it, and transforms
// it into the same STATIONS shape data.js uses, so uploaded
// data flows through the exact same dashboard as the demo data.
//
// EXPECTED CSV COLUMNS (header row required):
//   station_id        (required) — e.g. "P-12"
//   station_name       (optional) — defaults to station_id
//   zone               (required) — Body | Paint | Final
//   time_step          (optional) — number, order per station. If
//                                    omitted, row order is used.
//   cycle_time_sec      (required) — measured cycle time
//   queue_depth         (required) — vehicles queued upstream
//   utilization_pct     (required) — 0–100
//   takt_target_sec     (optional) — defaults to 60
//   sensor_coverage     (optional) — yes/no, defaults to yes
//
// One row = one station at one point in time. A station with
// multiple rows becomes a real time-series; a station with one
// row still works — the timeline extrapolates from a single point.
// ============================================================

const CSV_REQUIRED_COLUMNS = ['station_id', 'zone', 'cycle_time_sec', 'queue_depth', 'utilization_pct'];

// ── PARSE ─────────────────────────────────────────────────────
// Minimal CSV parser: handles quoted fields and commas inside quotes.
function parseCSVText(text) {
  const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n').filter(l => l.trim().length > 0);
  if (lines.length < 2) return { header: [], rows: [] };

  const parseLine = (line) => {
    const out = [];
    let cur = '', inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') {
        inQuotes = !inQuotes;
      } else if (c === ',' && !inQuotes) {
        out.push(cur.trim());
        cur = '';
      } else {
        cur += c;
      }
    }
    out.push(cur.trim());
    return out;
  };

  const header = parseLine(lines[0]).map(h => h.trim().toLowerCase());
  const rows = lines.slice(1).map(line => {
    const cells = parseLine(line);
    const row = {};
    header.forEach((h, i) => { row[h] = (cells[i] ?? '').trim(); });
    return row;
  });

  return { header, rows };
}

// ── VALIDATE ──────────────────────────────────────────────────
function validateCSV(header, rows) {
  const errors = [];
  const warnings = [];

  // Alias maps to support plant_twin_data.csv format seamlessly
  const hasCycle = header.includes('cycle_time_sec') || header.includes('cycle_time');
  const hasQueue = header.includes('queue_depth') || header.includes('queue_length');
  const hasStation = header.includes('station_id');

  if (!hasStation || !hasCycle || !hasQueue) {
    const missing = [];
    if (!hasStation) missing.push('station_id');
    if (!hasCycle) missing.push('cycle_time_sec / cycle_time');
    if (!hasQueue) missing.push('queue_depth / queue_length');
    errors.push(`Missing required column(s): ${missing.join(', ')}`);
    return { errors, warnings, validRows: [] };
  }

  if (rows.length === 0) {
    errors.push('No data rows found below the header.');
    return { errors, warnings, validRows: [] };
  }

  const validRows = [];
  rows.forEach((row, i) => {
    const lineNo = i + 2; // +1 header, +1 for 1-indexing
    if (!row.station_id) { warnings.push(`Row ${lineNo}: missing station_id — skipped.`); return; }

    const cycle = parseFloat(row.cycle_time_sec || row.cycle_time);
    const queue = parseFloat(row.queue_depth || row.queue_length);

    // Infer utilization if missing (e.g., from cycle vs 60s takt)
    let util = parseFloat(row.utilization_pct);
    if (isNaN(util)) {
      const takt = parseFloat(row.takt_target_sec) || 60;
      util = Math.min(100, Math.max(40, Math.round((cycle / takt) * 85)));
    }

    // Infer zone from station_id if zone is missing (1-15: Body, 16-25: Paint, 26-40: Final)
    let zone = row.zone;
    if (!zone) {
      const stNum = parseInt(row.station_id, 10);
      if (!isNaN(stNum)) {
        zone = stNum <= 15 ? 'Body' : stNum <= 25 ? 'Paint' : 'Final';
      } else {
        zone = 'Body';
      }
    }

    if (isNaN(cycle) || isNaN(queue)) {
      warnings.push(`Row ${lineNo}: non-numeric cycle_time / queue_length — skipped.`);
      return;
    }

    validRows.push({ ...row, zone, _cycle: cycle, _queue: queue, _util: util, _line: lineNo });
  });

  if (validRows.length === 0) {
    errors.push('No valid data rows after validation — check column values.');
  }

  return { errors, warnings, validRows };
}


// ── TRANSFORM ─────────────────────────────────────────────────
// Simple, explainable rule-based risk score — the same three
// signals agreed as parameters: cycle time deviation from takt,
// queue growth, and utilisation. This is a stand-in for the
// SPC + Isolation Forest engine the backend will compute; the
// frontend just needs something honest and consistent to render.
function computeRiskForRow(cycle, queue, util, takt) {
  const cycleDevPct   = Math.max(0, ((cycle - takt) / takt) * 100);
  const cycleDevScore = Math.min(100, cycleDevPct * 2);
  const queueScore    = Math.min(100, (queue / 8) * 100);
  const utilScore     = Math.min(100, Math.max(0, util - 60) * 2.5);

  const risk = Math.round(0.40 * cycleDevScore + 0.35 * queueScore + 0.25 * utilScore);
  return {
    risk: Math.max(0, Math.min(100, risk)),
    cycleDevScore: Math.round(cycleDevScore),
    queueScore: Math.round(queueScore),
    utilScore: Math.round(utilScore),
  };
}

function normaliseZone(raw) {
  const z = (raw || '').trim().toLowerCase();
  if (z.startsWith('body'))  return 'Body';
  if (z.startsWith('paint')) return 'Paint';
  if (z.startsWith('final')) return 'Final';
  return 'Body'; // soft fallback — flagged as a warning by the caller if needed
}

function parseSensorFlag(raw) {
  const v = (raw || '').trim().toLowerCase();
  if (['no', 'false', '0', 'n'].includes(v)) return false;
  return true; // default: sensor-equipped
}

// Groups validated rows by station, sorts each by time_step (or
// file order), and builds one STATIONS-shaped object per station.
function buildStationsFromRows(validRows) {
  const byStation = new Map();

  validRows.forEach((row, fileOrder) => {
    const id = row.station_id;
    if (!byStation.has(id)) byStation.set(id, []);
    byStation.get(id).push({ ...row, _fileOrder: fileOrder });
  });

  const stations = [];

  byStation.forEach((rows, id) => {
    rows.sort((a, b) => {
      const ta = parseFloat(a.time_step);
      const tb = parseFloat(b.time_step);
      if (!isNaN(ta) && !isNaN(tb)) return ta - tb;
      return a._fileOrder - b._fileOrder;
    });

    const first = rows[0];
    const last  = rows[rows.length - 1];
    const takt  = parseFloat(first.takt_target_sec) || 60;
    const zone  = normaliseZone(first.zone);
    const sensor = parseSensorFlag(first.sensor_coverage);

    const riskArr = [];
    let lastComputed = null;
    rows.forEach(r => {
      const computed = computeRiskForRow(r._cycle, r._queue, r._util, takt);
      riskArr.push(computed.risk);
      lastComputed = computed;
    });

    const confidence = sensor
      ? 82 + Math.round(Math.random() * 12)   // 82–94
      : 55 + Math.round(Math.random() * 15);  // 55–70

    stations.push({
      id,
      name: first.station_name || id,
      zone,
      queue: last._queue,
      takt,
      util: last._util,
      sensor,
      risk: riskArr,
      factors: {
        queueGrowth:    lastComputed.queueScore,
        cycleDeviation: lastComputed.cycleDevScore,
        utilisation:    Math.round(last._util),
        anomaly:        Math.round(Math.abs(last._cycle - takt) / takt * 50),
      },
      confidence,
    });
  });

  return stations;
}

// ── PUBLIC ENTRY POINT ───────────────────────────────────────
// Returns { ok: true, stations, warnings } or { ok: false, errors }
function processCSVFile(text) {
  const { header, rows } = parseCSVText(text);
  const { errors, warnings, validRows } = validateCSV(header, rows);

  if (errors.length > 0) {
    return { ok: false, errors, warnings };
  }

  const stations = buildStationsFromRows(validRows);
  return { ok: true, stations, warnings };
}

// ── SAMPLE CSV (for teammates to test the pipeline) ─────────────
function downloadSampleCSV() {
  const header = 'station_id,station_name,zone,time_step,cycle_time_sec,queue_depth,utilization_pct,takt_target_sec,sensor_coverage';
  const rows = [
    // Paint-12 drift scenario, same shape as the built-in demo
    ['P-12','Paint-12','Paint',0,54,2.1,70,52,'yes'],
    ['P-12','Paint-12','Paint',1,58,3.0,75,52,'yes'],
    ['P-12','Paint-12','Paint',2,66,4.4,82,52,'yes'],
    ['P-12','Paint-12','Paint',3,74,5.8,88,52,'yes'],
    ['P-12','Paint-12','Paint',4,82,7.1,92,52,'yes'],
    ['P-12','Paint-12','Paint',5,86,8.2,94,52,'yes'],
    ['B-01','Body-01','Body',0,52,1.0,68,52,'yes'],
    ['B-01','Body-01','Body',1,53,1.2,70,52,'yes'],
    ['B-01','Body-01','Body',2,52,1.1,71,52,'yes'],
    ['F-08','Final-08','Final',0,60,0.9,64,60,'no'],
    ['F-08','Final-08','Final',1,61,1.0,66,60,'no'],
  ].map(r => r.join(','));

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'digitaltwin_sample.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
