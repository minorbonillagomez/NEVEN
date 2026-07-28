// ═══════════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Task Pane JavaScript (Office.js + API Client)
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = window.location.protocol === 'file:' ? 'http://localhost:5555' : window.location.origin;
const CHUNK_SIZE = 50000;

let loadedData = null;      // { columns: [], types: {}, rows: [] } — SINGLE dataset, always the latest
let currentSqlPage = 1;
let lastSqlQuery = '';

// ─── Office.js Initialization ────────────────────────────────────────────────

// Try Office.js if available, otherwise initialize standalone
if (typeof Office !== 'undefined' && Office.onReady) {
  Office.onReady(function(info) {
    if (info.host === Office.HostType.Excel) {
      initializeApp(true);
    } else {
      initializeApp(false);
    }
  });
} else {
  // Standalone mode (browser or WebView2 without Office.js)
  document.addEventListener('DOMContentLoaded', function() {
    initializeApp(false);
  });
}

function initializeApp(hasOfficeJs) {
  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Buttons
  document.getElementById('btn-analyze').addEventListener('click', analyzeData);
  document.getElementById('btn-sql-run').addEventListener('click', runSQL);
  document.getElementById('btn-sql-export').addEventListener('click', exportSQLToSheet);
  document.getElementById('btn-sql-prev').addEventListener('click', () => navigateSQL(-1));
  document.getElementById('btn-sql-next').addEventListener('click', () => navigateSQL(1));
  document.getElementById('btn-bridge-read').addEventListener('click', loadBridgeData);

  // Viewer buttons
  document.getElementById('btn-load-viewer').addEventListener('click', loadActiveViewerFromBridge);

  // SQL: Ctrl+Enter shortcut
  document.getElementById('sql-input').addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); runSQL(); }
  });

  // GROUP BY dropdowns — auto-execute on change
  ['grp-col', 'grp-metric', 'grp-val'].forEach(id => {
    document.getElementById(id).addEventListener('change', executeGroupBy);
  });

  // Viewer buttons (existing HTML viewers)
  document.querySelectorAll('[data-viewer]').forEach(btn => {
    btn.addEventListener('click', () => {
      window.open(API_BASE + '/viewers/' + btn.dataset.viewer, '_blank');
    });
  });

  // Selection change handler (only with Office.js)
  if (hasOfficeJs) {
    registerSelectionHandler();
    document.getElementById('data-info').textContent = 'Seleccione un rango y presione "Cargar"';
    document.getElementById('btn-load').addEventListener('click', loadDataFromSelection);
  } else {
    document.getElementById('data-info').textContent = 'Cargue un archivo CSV/Parquet para analizar (DuckDB)';
    document.getElementById('btn-load').textContent = 'Cargar CSV';
    document.getElementById('btn-load').addEventListener('click', loadCSVPrompt);
  }

  // Check server health
  checkServerHealth();
}

// ─── Tab Switching ───────────────────────────────────────────────────────────

function switchTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.toggle('active', t.id === tabId));
}

// ─── Reset State (clear previous data on new load) ───────────────────────────

function resetState() {
  loadedData = null;
  lastSqlQuery = '';
  currentSqlPage = 1;

  // Clear UI
  document.getElementById('preview-area').innerHTML = '';
  document.getElementById('stats-card').style.display = 'none';
  document.getElementById('stats-table').innerHTML = '';
  document.getElementById('groupby-card').style.display = 'none';
  document.getElementById('grp-chart').innerHTML = '';
  document.getElementById('grp-table').innerHTML = '';
  document.getElementById('sql-results-card').style.display = 'none';
  document.getElementById('sql-results').innerHTML = '';
  document.getElementById('sql-error').style.display = 'none';
  document.getElementById('viz-chart').style.display = 'none';
  document.getElementById('viz-chart').innerHTML = '';
  document.getElementById('viz-table').innerHTML = '';

  // Reset viewers detection
  document.getElementById('viewers-detect-msg').textContent = 'Cargue datos primero';
  document.getElementById('viewer-nav-ct').style.display = 'none';
  document.getElementById('viewer-nav-st').style.display = 'none';
  document.getElementById('viewer-nav-gs').style.display = 'none';
  document.getElementById('viewer-nav-rel').style.display = 'none';
  document.getElementById('viewer-nav-existing').style.display = 'none';
}

// ─── Server Health ───────────────────────────────────────────────────────────

async function checkServerHealth() {
  try {
    const resp = await fetch(API_BASE + '/health');
    const data = await resp.json();
    document.getElementById('status-server').style.color = '#4caf50';
    document.getElementById('status-server').title = `Server OK (port ${data.port})`;
  } catch (e) {
    document.getElementById('status-server').style.color = '#ff4444';
    document.getElementById('status-server').title = 'Server unavailable';
  }
}

// ─── Load CSV Prompt (standalone mode) ───────────────────────────────────────

function loadCSVPrompt() {
  const path = document.getElementById('csv-path').value.trim();
  if (!path) {
    document.getElementById('data-info').textContent = 'Ingrese una ruta de archivo';
    return;
  }
  loadCSVFile(path);
}

async function loadCSVFile(path) {
  const info = document.getElementById('data-info');
  resetState();
  info.innerHTML = '<span class="spinner"></span> Cargando con DuckDB...';
  try {
    const result = await apiCall('/api/load_file', { path: path });
    info.textContent = `${result.rows_loaded.toLocaleString()} filas × ${result.columns.length} cols cargadas`;
    loadedData = { columns: result.columns, types: result.types, rows: [] };
    populateGroupByControls(result.columns, result.types);
    document.getElementById('groupby-card').style.display = 'block';
    updateViewersTab();
  } catch (e) {
    info.innerHTML = `<span class="msg-error">${e.message}</span>`;
  }
}

// ─── Selection Change ────────────────────────────────────────────────────────

async function registerSelectionHandler() {
  try {
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      sheet.onSelectionChanged.add(onSelectionChanged);
      await context.sync();
    });
  } catch (e) {
    console.warn('Selection handler not registered:', e);
  }
}

async function onSelectionChanged(event) {
  document.getElementById('status-range').textContent = event.address;
  if (document.getElementById('auto-load').checked) {
    await loadDataFromSelection();
  }
}

// ─── Load Data from Excel ────────────────────────────────────────────────────

async function loadDataFromSelection() {
  const info = document.getElementById('data-info');
  info.innerHTML = '<span class="spinner"></span> Cargando...';

  try {
    await Excel.run(async (context) => {
      const range = context.workbook.getSelectedRange();
      range.load('values, address, rowCount, columnCount');
      await context.sync();

      if (range.rowCount < 2 || range.columnCount < 1) {
        info.textContent = 'Seleccione al menos 2 filas y 1 columna';
        return;
      }

      document.getElementById('status-range').textContent =
        `${range.address} (${(range.rowCount-1).toLocaleString()}×${range.columnCount})`;

      const values = range.values;
      const headers = values[0].map(v => String(v || 'Col'));
      const rows = values.slice(1);

      // Detect types from first 100 rows
      const types = {};
      headers.forEach((h, i) => {
        const sample = rows.slice(0, 100).map(r => r[i]);
        const numCount = sample.filter(v => typeof v === 'number' || !isNaN(parseFloat(v))).length;
        types[h] = numCount > sample.length * 0.7 ? 'numeric' : 'text';
      });

      loadedData = { columns: headers, types: types, rows: rows };

      // Show preview (first 20 rows)
      showPreview(headers, rows.slice(0, 20));
      info.textContent = `${(rows.length).toLocaleString()} filas × ${headers.length} columnas cargadas`;

      // Populate GROUP BY dropdowns
      populateGroupByControls(headers, types);

      // Send to server
      await sendDataToServer(headers, types, rows);
    });
  } catch (e) {
    info.textContent = 'Error: ' + e.message;
  }
}

function showPreview(headers, rows) {
  let html = '<table class="data-table"><tr>';
  headers.forEach(h => html += `<th>${h}</th>`);
  html += '</tr>';
  rows.forEach(row => {
    html += '<tr>';
    row.forEach(v => html += `<td>${v !== null && v !== undefined ? v : ''}</td>`);
    html += '</tr>';
  });
  html += '</table>';
  document.getElementById('preview-area').innerHTML = html;
}

function populateGroupByControls(headers, types) {
  const grpCol = document.getElementById('grp-col');
  const grpVal = document.getElementById('grp-val');
  grpCol.innerHTML = '';
  grpVal.innerHTML = '';

  headers.forEach(h => {
    if (types[h] === 'text') grpCol.innerHTML += `<option value="${h}">${h}</option>`;
    if (types[h] === 'numeric') grpVal.innerHTML += `<option value="${h}">${h}</option>`;
  });

  document.getElementById('groupby-card').style.display = grpCol.options.length > 0 && grpVal.options.length > 0 ? 'block' : 'none';
}

// ─── API Communication ───────────────────────────────────────────────────────

async function apiCall(endpoint, body) {
  const response = await fetch(API_BASE + endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await response.json();
  if (data.status === 'error') throw new Error(data.message);
  return data;
}

async function sendDataToServer(columns, types, rows) {
  try {
    await apiCall('/api/load', { columns, types, data: rows });
  } catch (e) {
    console.error('Failed to send data to server:', e);
  }
}

// ─── Analyze ─────────────────────────────────────────────────────────────────

async function analyzeData() {
  if (!loadedData) { alert('Cargue datos primero'); return; }

  const statsCard = document.getElementById('stats-card');
  statsCard.style.display = 'block';
  document.getElementById('stats-table').innerHTML = '<span class="spinner"></span>';

  try {
    const result = await apiCall('/api/analyze', {});
    renderStatistics(result.statistics);
  } catch (e) {
    document.getElementById('stats-table').innerHTML = `<div class="msg-error">${e.message}</div>`;
  }
}

function renderStatistics(stats) {
  let html = '<table class="data-table"><tr><th>Variable</th><th>Tipo</th><th>N</th><th>NA%</th><th>Min</th><th>Q25</th><th>Media</th><th>Mediana</th><th>Q75</th><th>Max</th><th>σ</th></tr>';
  stats.forEach(s => {
    if (s.numeric) {
      html += `<tr><td>${s.column}</td><td>num</td><td>${s.count}</td><td>${s.na_pct}%</td>
        <td>${s.min.toFixed(2)}</td><td>${s.q25.toFixed(2)}</td><td>${s.mean.toFixed(2)}</td>
        <td>${s.median.toFixed(2)}</td><td>${s.q75.toFixed(2)}</td><td>${s.max.toFixed(2)}</td>
        <td>${s.std.toFixed(2)}</td></tr>`;
    } else {
      html += `<tr><td>${s.column}</td><td>cat</td><td colspan="2">${s.na_pct}% NA</td>
        <td colspan="5" style="color:#888;text-align:center">únicos: ${s.unique} | moda: ${s.mode}</td>
        <td colspan="2"></td></tr>`;
    }
  });
  html += '</table>';
  document.getElementById('stats-table').innerHTML = html;
}

// ─── GROUP BY ────────────────────────────────────────────────────────────────

async function executeGroupBy() {
  const grpCol = document.getElementById('grp-col').value;
  const grpVal = document.getElementById('grp-val').value;
  const metric = document.getElementById('grp-metric').value;
  if (!grpCol || !grpVal) return;

  try {
    const result = await apiCall('/api/groupby', {
      group_column: grpCol, value_column: grpVal, metric: metric
    });
    renderGroupBy(result, grpCol, grpVal, metric);
  } catch (e) {
    document.getElementById('grp-table').innerHTML = `<div class="msg-error">${e.message}</div>`;
  }
}

function renderGroupBy(result, grpCol, grpVal, metric) {
  // Chart
  const labels = result.results.map(r => r.group);
  const values = result.results.map(r => r.value);

  Plotly.newPlot('grp-chart', [{
    x: labels, y: values, type: 'bar',
    marker: { color: 'rgba(168,230,0,0.7)', line: { color: '#a8e600', width: 0.5 } }
  }], {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 9 },
    xaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: grpCol },
    yaxis: { gridcolor: 'rgba(255,255,255,0.08)', title: `${metric}(${grpVal})` },
    margin: { t: 8, r: 10, b: 35, l: 50 }
  }, { responsive: true, displayModeBar: false });

  // Table
  let html = `<table class="data-table"><tr><th>${grpCol}</th><th>${metric}(${grpVal})</th></tr>`;
  result.results.forEach(r => {
    html += `<tr><td>${r.group}</td><td>${r.value.toFixed(4)}</td></tr>`;
  });
  html += '</table>';
  document.getElementById('grp-table').innerHTML = html;
}

// ─── SQL ─────────────────────────────────────────────────────────────────────

async function runSQL() {
  const sql = document.getElementById('sql-input').value.trim();
  if (!sql) return;

  lastSqlQuery = sql;
  currentSqlPage = 1;
  await executeSQLPage(sql, 1);
}

async function executeSQLPage(sql, page) {
  const statusEl = document.getElementById('sql-status');
  const errorEl = document.getElementById('sql-error');
  const resultsCard = document.getElementById('sql-results-card');

  statusEl.innerHTML = '<span class="spinner"></span>';
  errorEl.style.display = 'none';

  try {
    const result = await apiCall('/api/query', { sql, page, page_size: 100 });
    statusEl.textContent = `${result.total_rows} filas (${result.total_pages} pág)`;
    resultsCard.style.display = 'block';
    document.getElementById('sql-results-title').textContent = `Resultados — página ${result.page}/${result.total_pages}`;
    renderSQLResults(result);

    // Pagination
    const pagEl = document.getElementById('sql-pagination');
    if (result.total_pages > 1) {
      pagEl.style.display = 'flex';
      document.getElementById('sql-page-info').textContent = `${result.page} / ${result.total_pages}`;
      document.getElementById('btn-sql-prev').disabled = result.page <= 1;
      document.getElementById('btn-sql-next').disabled = result.page >= result.total_pages;
    } else {
      pagEl.style.display = 'none';
    }
    currentSqlPage = result.page;
  } catch (e) {
    statusEl.textContent = '';
    errorEl.style.display = 'block';
    errorEl.textContent = e.message;
    resultsCard.style.display = 'none';
  }
}

function navigateSQL(direction) {
  const newPage = currentSqlPage + direction;
  if (newPage < 1) return;
  executeSQLPage(lastSqlQuery, newPage);
}

function renderSQLResults(result) {
  let html = '<table class="data-table"><tr>';
  result.columns.forEach(c => html += `<th>${c}</th>`);
  html += '</tr>';
  result.rows.forEach(row => {
    html += '<tr>';
    row.forEach(v => html += `<td>${v !== null ? v : 'NULL'}</td>`);
    html += '</tr>';
  });
  html += '</table>';
  document.getElementById('sql-results').innerHTML = html;
}

// ─── Export to Sheet ─────────────────────────────────────────────────────────

async function exportSQLToSheet() {
  if (!lastSqlQuery) return;

  try {
    // Get all results (no pagination)
    const result = await apiCall('/api/query', { sql: lastSqlQuery, page: 1, page_size: 1000000 });

    await Excel.run(async (context) => {
      const sheets = context.workbook.worksheets;
      const name = 'Query_' + new Date().toISOString().replace(/[:.]/g, '').slice(0, 15);
      const newSheet = sheets.add(name);

      // Write headers + data
      const allData = [result.columns, ...result.rows];
      const range = newSheet.getRangeByIndexes(0, 0, allData.length, result.columns.length);
      range.values = allData;
      range.format.autofitColumns();
      newSheet.activate();
      await context.sync();

      document.getElementById('sql-status').innerHTML = `<span class="msg-success">Exportado a "${name}"</span>`;
    });
  } catch (e) {
    document.getElementById('sql-status').innerHTML = `<span class="msg-error">Export error: ${e.message}</span>`;
  }
}

// ─── NEVEN Bridge (Excel <-> TaskPane without Office.js) ─────────────────────

let _bridgePolling = null;

/**
 * Read data from the bridge buffer (data pushed by Excel).
 * @param {string} key - Buffer key name (default: "default")
 * @returns {Promise<object|null>} The data or null
 */
async function bridgeRead(key) {
  key = key || 'default';
  try {
    const resp = await fetch(API_BASE + '/api/bridge/pull?key=' + encodeURIComponent(key));
    const result = await resp.json();
    if (result.status === 'ok' && result.data) {
      return result.data;
    }
    return null;
  } catch (e) {
    console.error('Bridge read error:', e);
    return null;
  }
}

/**
 * Write data to the bridge buffer (for Excel to read via =P.Receive()).
 * @param {*} data - Any JSON-serializable data
 * @param {string} key - Buffer key name (default: "result")
 */
async function bridgeWrite(key, data) {
  key = key || 'result';
  try {
    await apiCall('/api/bridge/write', { key: key, data: data });
    return true;
  } catch (e) {
    console.error('Bridge write error:', e);
    return false;
  }
}

/**
 * Get list of available bridge keys.
 * @returns {Promise<string[]>}
 */
async function bridgeStatus() {
  try {
    const resp = await fetch(API_BASE + '/api/bridge/status');
    const result = await resp.json();
    return result.keys || [];
  } catch (e) {
    return [];
  }
}

/**
 * Start polling the bridge for data from Excel.
 * When data arrives, calls the callback with {columns, rows, timestamp}.
 * @param {string} key - Key to poll
 * @param {function} callback - Called with data when available
 * @param {number} intervalMs - Poll interval (default 2000ms)
 */
function bridgeStartPolling(key, callback, intervalMs) {
  intervalMs = intervalMs || 2000;
  let lastTimestamp = 0;

  if (_bridgePolling) clearInterval(_bridgePolling);

  _bridgePolling = setInterval(async function() {
    const data = await bridgeRead(key);
    if (data && data.timestamp && data.timestamp > lastTimestamp) {
      lastTimestamp = data.timestamp;
      callback(data);
    }
  }, intervalMs);
}

/**
 * Stop polling the bridge.
 */
function bridgeStopPolling() {
  if (_bridgePolling) {
    clearInterval(_bridgePolling);
    _bridgePolling = null;
  }
}

/**
 * Load data from bridge into the TaskPane (same as loading CSV).
 * Called when Excel pushes data via =P.Send().
 */
async function loadFromBridge(key) {
  key = key || 'default';
  const info = document.getElementById('data-info');
  resetState();
  info.innerHTML = '<span class="spinner"></span> Leyendo datos del bridge...';

  const data = await bridgeRead(key);
  if (!data || !data.columns) {
    info.textContent = 'No hay datos en el bridge (key: ' + key + ')';
    return;
  }

  const columns = data.columns;
  const rows = data.rows || [];

  // Detect types
  const types = {};
  columns.forEach(function(h, i) {
    var sample = rows.slice(0, 100).map(function(r) { return r[i]; });
    var numCount = sample.filter(function(v) { return typeof v === 'number' || !isNaN(parseFloat(v)); }).length;
    types[h] = numCount > sample.length * 0.7 ? 'numeric' : 'text';
  });

  loadedData = { columns: columns, types: types, rows: rows };

  // Show preview
  showPreview(columns, rows.slice(0, 20));
  info.textContent = rows.length.toLocaleString() + ' filas x ' + columns.length + ' cols (desde Excel)';

  // Populate GROUP BY
  populateGroupByControls(columns, types);
  document.getElementById('groupby-card').style.display = 'block';

  // Also load into DuckDB for SQL
  try {
    await apiCall('/api/load', { columns: columns, types: types, data: rows });
  } catch (e) {
    console.warn('Failed to load bridge data into DuckDB:', e);
  }

  // Update Viewers tab
  updateViewersTab();
}

/**
 * Send current analysis results back to Excel via bridge.
 * Excel reads with =P.Receive("result")
 */
async function sendToExcel(data, key) {
  key = key || 'result';
  const success = await bridgeWrite(key, data);
  if (success) {
    document.getElementById('data-info').innerHTML =
      '<span class="msg-success">Datos enviados a Excel (key: ' + key + '). Use =P.Receive("' + key + '") para leer.</span>';
  }
}


// ─── Data Type Detection & Viewers ───────────────────────────────────────────

/**
 * Detect the data family based on column names and content.
 * Returns: 'CT', 'ST', 'GS', 'REL', or 'unknown'
 */
function detectDataFamily(columns, types, rows) {
  var colsLower = columns.map(function(c) { return c.toLowerCase(); });

  // GS: has lat/lon columns
  var hasLat = colsLower.some(function(c) { return c.match(/^(lat|latitude|latitud)$/); });
  var hasLon = colsLower.some(function(c) { return c.match(/^(lon|lng|long|longitude|longitud)$/); });
  if (hasLat && hasLon) return 'GS';

  // REL: has origin/destination or source/target columns
  var hasSource = colsLower.some(function(c) { return c.match(/^(source|origen|from|de|nodo_a|source_id)$/); });
  var hasTarget = colsLower.some(function(c) { return c.match(/^(target|destino|to|a|nodo_b|target_id)$/); });
  if (hasSource && hasTarget) return 'REL';

  // ST: has a time/date column
  var hasTime = colsLower.some(function(c) { return c.match(/^(fecha|date|time|periodo|year|mes|month|dia|day|timestamp|t)$/); });
  if (hasTime) return 'ST';

  // Default: CT (cross-sectional)
  return 'CT';
}

/**
 * Update the Viewers tab based on detected data family.
 */
function updateViewersTab() {
  if (!loadedData || !loadedData.columns) return;

  var family = detectDataFamily(loadedData.columns, loadedData.types, loadedData.rows);
  var msg = document.getElementById('viewers-detect-msg');

  var labels = { 'CT': 'Corte Transversal', 'ST': 'Serie de Tiempo', 'GS': 'Geoespacial', 'REL': 'Relaciones' };
  msg.innerHTML = '<span style="color:var(--accent);font-weight:700">' + (labels[family] || family) + '</span> detectado (' + loadedData.columns.length + ' columnas)';

  // Show/hide nav groups
  document.getElementById('viewer-nav-ct').style.display = (family === 'CT') ? 'flex' : 'none';
  document.getElementById('viewer-nav-st').style.display = (family === 'ST') ? 'flex' : 'none';
  document.getElementById('viewer-nav-gs').style.display = (family === 'GS') ? 'flex' : 'none';
  document.getElementById('viewer-nav-rel').style.display = (family === 'REL') ? 'flex' : 'none';
  document.getElementById('viewer-nav-existing').style.display = 'flex';

  loadedData._family = family;
}

/**
 * Render a visualization based on type.
 */
function renderViz(vizType) {
  if (!loadedData || !loadedData.columns) { alert('Cargue datos primero'); return; }

  var chartEl = document.getElementById('viz-chart');
  chartEl.style.display = 'block';

  var cols = loadedData.columns;
  var types = loadedData.types;
  var rows = loadedData.rows;

  if (vizType === 'ct-bars') renderCTBars(cols, types, rows, chartEl);
  else if (vizType === 'ct-scatter') renderCTScatter(cols, types, rows, chartEl);
  else if (vizType === 'ct-heatmap') renderCTHeatmap(cols, types, rows, chartEl);
  else if (vizType === 'ct-boxplot') renderCTBoxplot(cols, types, rows, chartEl);
  else if (vizType === 'st-line') renderSTLine(cols, types, rows, chartEl);
  else if (vizType === 'st-area') renderSTArea(cols, types, rows, chartEl);
  else if (vizType === 'st-multi') renderSTMulti(cols, types, rows, chartEl);
  else if (vizType === 'gs-map') renderGSMap(cols, types, rows);
  else if (vizType === 'gs-cluster') renderGSCluster(cols, types, rows);
  else if (vizType === 'rel-graph') renderRELGraph(cols, types, rows, chartEl);
  else if (vizType === 'rel-sankey') renderRELSankey(cols, types, rows, chartEl);
}

// ─── CT Visualizations ───────────────────────────────────────────────────────

function _getNumericCols(cols, types) {
  return cols.filter(function(c) { return types[c] === 'numeric'; });
}
function _getTextCols(cols, types) {
  return cols.filter(function(c) { return types[c] === 'text'; });
}
function _getColValues(rows, cols, colName) {
  var idx = cols.indexOf(colName);
  return rows.map(function(r) { return r[idx]; });
}

function renderCTBars(cols, types, rows, el) {
  var numCols = _getNumericCols(cols, types);
  var textCols = _getTextCols(cols, types);
  if (numCols.length === 0) { el.innerHTML = '<div class="msg-error">No hay columnas numericas</div>'; return; }

  var catCol = textCols.length > 0 ? textCols[0] : null;
  var valCol = numCols[0];
  var x = catCol ? _getColValues(rows, cols, catCol) : rows.map(function(_, i) { return i + 1; });
  var y = _getColValues(rows, cols, valCol).map(Number);

  Plotly.newPlot(el, [{ x: x, y: y, type: 'bar', marker: { color: 'rgba(168,230,0,0.7)' } }], {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 10 },
    xaxis: { title: catCol || 'Index', gridcolor: 'rgba(255,255,255,0.05)' },
    yaxis: { title: valCol, gridcolor: 'rgba(255,255,255,0.08)' },
    margin: { t: 10, r: 10, b: 40, l: 50 }
  }, { responsive: true, displayModeBar: false });
}

function renderCTScatter(cols, types, rows, el) {
  var numCols = _getNumericCols(cols, types);
  if (numCols.length < 2) { el.innerHTML = '<div class="msg-error">Necesita al menos 2 columnas numericas</div>'; return; }

  var x = _getColValues(rows, cols, numCols[0]).map(Number);
  var y = _getColValues(rows, cols, numCols[1]).map(Number);

  Plotly.newPlot(el, [{ x: x, y: y, mode: 'markers', type: 'scatter',
    marker: { color: '#a8e600', size: 6, opacity: 0.7 } }], {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 10 },
    xaxis: { title: numCols[0], gridcolor: 'rgba(255,255,255,0.05)' },
    yaxis: { title: numCols[1], gridcolor: 'rgba(255,255,255,0.08)' },
    margin: { t: 10, r: 10, b: 40, l: 50 }
  }, { responsive: true, displayModeBar: false });
}

function renderCTHeatmap(cols, types, rows, el) {
  var numCols = _getNumericCols(cols, types);
  if (numCols.length < 2) { el.innerHTML = '<div class="msg-error">Necesita al menos 2 columnas numericas</div>'; return; }

  // Compute correlation matrix
  var data = numCols.map(function(c) { return _getColValues(rows, cols, c).map(Number); });
  var n = numCols.length;
  var corr = [];
  for (var i = 0; i < n; i++) {
    corr[i] = [];
    for (var j = 0; j < n; j++) {
      corr[i][j] = _pearson(data[i], data[j]);
    }
  }

  Plotly.newPlot(el, [{ z: corr, x: numCols, y: numCols, type: 'heatmap',
    colorscale: [[0,'#1a1a1a'],[0.5,'#444'],[1,'#a8e600']], zmin: -1, zmax: 1 }], {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 9 },
    margin: { t: 10, r: 10, b: 80, l: 80 }
  }, { responsive: true, displayModeBar: false });
}

function renderCTBoxplot(cols, types, rows, el) {
  var numCols = _getNumericCols(cols, types);
  if (numCols.length === 0) { el.innerHTML = '<div class="msg-error">No hay columnas numericas</div>'; return; }

  var traces = numCols.slice(0, 6).map(function(c) {
    return { y: _getColValues(rows, cols, c).map(Number), type: 'box', name: c,
      marker: { color: '#a8e600' }, line: { color: '#a8e600' } };
  });

  Plotly.newPlot(el, traces, {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 10 },
    yaxis: { gridcolor: 'rgba(255,255,255,0.08)' },
    margin: { t: 10, r: 10, b: 30, l: 50 }, showlegend: false
  }, { responsive: true, displayModeBar: false });
}

// ─── ST Visualizations ───────────────────────────────────────────────────────

function _getTimeCol(cols) {
  var patterns = /^(fecha|date|time|periodo|year|mes|month|dia|day|timestamp|t)$/i;
  return cols.find(function(c) { return c.match(patterns); }) || cols[0];
}

function renderSTLine(cols, types, rows, el) {
  var timeCol = _getTimeCol(cols);
  var numCols = _getNumericCols(cols, types);
  if (numCols.length === 0) { el.innerHTML = '<div class="msg-error">No hay columnas numericas</div>'; return; }

  var x = _getColValues(rows, cols, timeCol);
  var traces = [{ x: x, y: _getColValues(rows, cols, numCols[0]).map(Number),
    type: 'scatter', mode: 'lines', line: { color: '#a8e600', width: 2 }, name: numCols[0] }];

  Plotly.newPlot(el, traces, {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 10 },
    xaxis: { title: timeCol, gridcolor: 'rgba(255,255,255,0.05)' },
    yaxis: { title: numCols[0], gridcolor: 'rgba(255,255,255,0.08)' },
    margin: { t: 10, r: 10, b: 40, l: 50 }
  }, { responsive: true, displayModeBar: false });
}

function renderSTArea(cols, types, rows, el) {
  var timeCol = _getTimeCol(cols);
  var numCols = _getNumericCols(cols, types);
  if (numCols.length === 0) return;

  var x = _getColValues(rows, cols, timeCol);
  var traces = [{ x: x, y: _getColValues(rows, cols, numCols[0]).map(Number),
    type: 'scatter', mode: 'lines', fill: 'tozeroy',
    line: { color: '#a8e600' }, fillcolor: 'rgba(168,230,0,0.2)', name: numCols[0] }];

  Plotly.newPlot(el, traces, {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 10 },
    xaxis: { title: timeCol, gridcolor: 'rgba(255,255,255,0.05)' },
    yaxis: { gridcolor: 'rgba(255,255,255,0.08)' },
    margin: { t: 10, r: 10, b: 40, l: 50 }
  }, { responsive: true, displayModeBar: false });
}

function renderSTMulti(cols, types, rows, el) {
  var timeCol = _getTimeCol(cols);
  var numCols = _getNumericCols(cols, types);
  if (numCols.length === 0) return;

  var x = _getColValues(rows, cols, timeCol);
  var colors = ['#a8e600', '#ff6b6b', '#4ecdc4', '#ffa502', '#a29bfe', '#fd79a8'];
  var traces = numCols.slice(0, 6).map(function(c, i) {
    return { x: x, y: _getColValues(rows, cols, c).map(Number),
      type: 'scatter', mode: 'lines', name: c, line: { color: colors[i % colors.length], width: 2 } };
  });

  Plotly.newPlot(el, traces, {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 10 },
    xaxis: { title: timeCol, gridcolor: 'rgba(255,255,255,0.05)' },
    yaxis: { gridcolor: 'rgba(255,255,255,0.08)' },
    margin: { t: 10, r: 10, b: 40, l: 50 },
    legend: { font: { color: '#888' } }
  }, { responsive: true, displayModeBar: false });
}

// ─── GS Visualizations ───────────────────────────────────────────────────────

function renderGSMap(cols, types, rows) {
  // Try to load geolive data from bridge
  bridgeRead('geolive').then(function(data) {
    if (data && data.points) {
      _renderGeoPlotly(data);
    } else {
      alert('Use =P.GeoLive(lat, lon, datos, encabezados) para enviar datos geoespaciales');
    }
  });
}

function renderGSCluster(cols, types, rows) {
  bridgeRead('geolive').then(function(data) {
    if (data && data.points) {
      _renderGeoPlotly(data, true);
    } else {
      alert('Use =P.GeoLive(lat, lon, datos, encabezados) para enviar datos geoespaciales');
    }
  });
}

function _renderGeoPlotly(data, showClusters) {
  var el = document.getElementById('viz-chart');
  el.style.display = 'block';
  el.style.height = '400px';

  var points = data.points;
  var lats = points.map(function(p) { return p.lat; });
  var lons = points.map(function(p) { return p.lon; });

  // Build hover text from all data columns
  var dataCols = data.columns.filter(function(c) { return c !== 'lat' && c !== 'lon'; });
  var hoverTexts = points.map(function(p) {
    var parts = [];
    dataCols.forEach(function(c) {
      if (p[c] !== undefined) parts.push(c + ': ' + p[c]);
    });
    return parts.join('<br>') || ('(' + p.lat.toFixed(4) + ', ' + p.lon.toFixed(4) + ')');
  });

  // Color by first numeric data column if available
  var colorValues = null;
  var colorCol = dataCols.find(function(c) {
    return points.some(function(p) { return typeof p[c] === 'number'; });
  });
  if (colorCol) {
    colorValues = points.map(function(p) { return typeof p[colorCol] === 'number' ? p[colorCol] : 0; });
  }

  var trace = {
    type: 'scattergeo',
    lat: lats,
    lon: lons,
    text: hoverTexts,
    hoverinfo: 'text',
    mode: 'markers',
    marker: {
      size: 10,
      color: colorValues || '#a8e600',
      colorscale: colorValues ? [[0,'#1a1a1a'],[0.5,'#4ecdc4'],[1,'#a8e600']] : undefined,
      showscale: !!colorValues,
      opacity: 0.8,
      line: { color: '#a8e600', width: 1 }
    }
  };

  var layout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#888', size: 10 },
    geo: {
      scope: 'world',
      bgcolor: '#1a1a1a',
      landcolor: '#2a2a2a',
      lakecolor: '#1a1a1a',
      oceancolor: '#1a1a1a',
      showland: true,
      showocean: true,
      showlakes: true,
      projection: { type: 'natural earth' },
      center: { lat: data.center_lat, lon: data.center_lon },
      lonaxis: { range: [data.center_lon - 5, data.center_lon + 5] },
      lataxis: { range: [data.center_lat - 3, data.center_lat + 3] }
    },
    margin: { t: 0, r: 0, b: 0, l: 0 }
  };

  Plotly.newPlot(el, [trace], layout, { responsive: true, displayModeBar: false });
}

// ─── REL Visualizations ──────────────────────────────────────────────────────

function renderRELGraph(cols, types, rows, el) {
  alert('Grafo de relaciones: Use =P.Red() para generar el grafo D3.js');
}

function renderRELSankey(cols, types, rows, el) {
  var colsLower = cols.map(function(c) { return c.toLowerCase(); });
  var srcIdx = colsLower.findIndex(function(c) { return c.match(/^(source|origen|from|de)$/); });
  var tgtIdx = colsLower.findIndex(function(c) { return c.match(/^(target|destino|to|a)$/); });
  var valIdx = cols.findIndex(function(c) { return types[c] === 'numeric'; });

  if (srcIdx < 0 || tgtIdx < 0) { el.innerHTML = '<div class="msg-error">Necesita columnas source/target</div>'; return; }

  var labels = [];
  var labelMap = {};
  rows.forEach(function(r) {
    [r[srcIdx], r[tgtIdx]].forEach(function(v) {
      if (!(v in labelMap)) { labelMap[v] = labels.length; labels.push(String(v)); }
    });
  });

  var sources = rows.map(function(r) { return labelMap[r[srcIdx]]; });
  var targets = rows.map(function(r) { return labelMap[r[tgtIdx]]; });
  var values = valIdx >= 0 ? rows.map(function(r) { return Number(r[valIdx]) || 1; }) : rows.map(function() { return 1; });

  Plotly.newPlot(el, [{ type: 'sankey', orientation: 'h',
    node: { label: labels, color: '#a8e600', pad: 15, thickness: 20 },
    link: { source: sources, target: targets, value: values, color: 'rgba(168,230,0,0.3)' }
  }], {
    paper_bgcolor: 'rgba(0,0,0,0)', font: { color: '#888', size: 10 },
    margin: { t: 10, r: 10, b: 10, l: 10 }
  }, { responsive: true, displayModeBar: false });
}

// ─── Utility: Pearson correlation ────────────────────────────────────────────

function _pearson(x, y) {
  var n = Math.min(x.length, y.length);
  if (n < 3) return 0;
  var sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0, valid = 0;
  for (var i = 0; i < n; i++) {
    if (isNaN(x[i]) || isNaN(y[i])) continue;
    sx += x[i]; sy += y[i];
    sxx += x[i] * x[i]; syy += y[i] * y[i];
    sxy += x[i] * y[i]; valid++;
  }
  if (valid < 3) return 0;
  var num = valid * sxy - sx * sy;
  var den = Math.sqrt((valid * sxx - sx * sx) * (valid * syy - sy * sy));
  return den === 0 ? 0 : Math.round(num / den * 1000) / 1000;
}


// --- Viewer and Bridge functions (clean) ---

function loadViewerHTML(filename) {
  var el = document.getElementById('viz-chart');
  el.style.display = 'block';
  el.innerHTML = '<iframe src="' + API_BASE + '/viewers/' + filename + '?t=' + Date.now() + '" style="width:100%;height:100%;border:none;border-radius:6px;"></iframe>';
  document.getElementById('viewers-msg').innerHTML = '<span style="color:var(--accent)">' + filename.replace('.html','').replace(/-/g,' ').toUpperCase() + '</span>';
}

async function loadActiveViewerFromBridge() {
  var msg = document.getElementById('viewers-msg');
  msg.innerHTML = '<span class="spinner"></span> Cargando...';
  try {
    var resp = await fetch(API_BASE + '/api/bridge/pull?key=active_viewer');
    var result = await resp.json();
    if (result.status === 'ok' && result.data && result.data.file) {
      loadViewerHTML(result.data.file);
    } else {
      msg.textContent = 'No hay viewer activo. Ejecute =P.Geodata(), =P.Dashboard(), etc.';
    }
  } catch(e) {
    msg.textContent = 'Error: ' + e.message;
  }
}

async function loadBridgeData() {
  var info = document.getElementById('data-info');
  resetState();
  info.innerHTML = '<span class="spinner"></span> Cargando datos del bridge...';
  try {
    var resp = await fetch(API_BASE + '/api/bridge/pull?key=geolive');
    var result = await resp.json();
    var bridgeData = (result.status === 'ok' && result.data) ? result.data : null;
    if (!bridgeData || (!bridgeData.points && !bridgeData.columns)) {
      resp = await fetch(API_BASE + '/api/bridge/pull?key=default');
      result = await resp.json();
      bridgeData = (result.status === 'ok' && result.data) ? result.data : null;
    }
    if (!bridgeData) {
      info.textContent = 'No hay datos. Use =P.Send() o =P.GeoLive() en Excel.';
      return;
    }
    var cols, rows;
    if (bridgeData.points) {
      cols = bridgeData.columns;
      rows = bridgeData.points.map(function(p) {
        return cols.map(function(c) { return p[c] !== undefined ? p[c] : ''; });
      });
    } else {
      cols = bridgeData.columns;
      rows = bridgeData.rows || [];
    }
    var types = {};
    cols.forEach(function(c, ci) {
      var sample = rows.slice(0, 50).map(function(r) { return r[ci]; });
      var numCount = sample.filter(function(v) { return typeof v === 'number' || !isNaN(parseFloat(v)); }).length;
      types[c] = numCount > sample.length * 0.5 ? 'numeric' : 'text';
    });
    loadedData = { columns: cols, types: types, rows: rows };
    showPreview(cols, rows.slice(0, 20));
    populateGroupByControls(cols, types);
    document.getElementById('groupby-card').style.display = 'block';
    info.textContent = rows.length + ' filas x ' + cols.length + ' cols cargadas desde Excel';
    await apiCall('/api/load', { columns: cols, types: types, data: rows });
  } catch(e) {
    info.textContent = 'Error: ' + e.message;
  }
}