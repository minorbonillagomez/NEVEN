// ═══════════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Task Pane JavaScript (Office.js + API Client)
// ═══════════════════════════════════════════════════════════════════════════════
console.log('[TASKPANE.JS] ========== ARCHIVO CARGADO v20260930 ==========');

// Si ya existe API (definida en el HTML inline), solo exponer funciones de gráficos
// y no reinicializar la app
const _TASKPANE_JS_LOADED_FOR_CHARTS_ONLY = typeof API !== 'undefined';

const API_BASE = window.location.protocol === 'file:'
  ? (window._NEVEN_API_BASE || 'http://localhost:5555')
  : window.location.origin;
const CHUNK_SIZE = 50000;

let loadedData = null;      // { columns: [], types: {}, rows: [] } — SINGLE dataset, always the latest
let currentSqlPage = 1;
let lastSqlQuery = '';

// ─── Initialization ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
  // Solo inicializar si este archivo es el principal (no cargado como complemento)
  if (!_TASKPANE_JS_LOADED_FOR_CHARTS_ONLY) {
    initializeApp();
  }
});

function initializeApp() {
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

  // CSV load button
  document.getElementById('btn-load').addEventListener('click', loadCSVPrompt);
  document.getElementById('data-info').textContent = 'Cargue un archivo CSV/Parquet o use "Leer de Excel"';

  // Check server health
  checkServerHealth();

  // Run Script tab
  initRunScriptTab();

  // Start polling for show-taskpane signal from Ribbon
  startShowTaskpanePolling();
}

// ─── Show TaskPane Polling ───────────────────────────────────────────────────
// El Ribbon (C++) envía POST /api/show-taskpane cuando el usuario hace clic
// en el botón AGENTE IA. Este polling detecta la señal y llama a
// Office.addin.showAsTaskpane() para mostrar el panel.

let _showTaskpanePollingId = null;

function startShowTaskpanePolling() {
  // Solo polling si estamos en el contexto de Office Add-in
  if (typeof Office === 'undefined' || !Office.addin) {
    console.log('[ShowTaskpane] Office.addin no disponible - polling desactivado');
    return;
  }

  // Poll cada 500ms
  _showTaskpanePollingId = setInterval(async () => {
    try {
      const resp = await fetch(API_BASE + '/api/show-taskpane/poll');
      if (resp.ok) {
        const data = await resp.json();
        if (data.shouldShow) {
          console.log('[ShowTaskpane] Señal recibida - mostrando TaskPane');
          Office.addin.showAsTaskpane().catch(err => {
            console.warn('[ShowTaskpane] Error en showAsTaskpane:', err);
          });
        }
      }
    } catch (err) {
      // Ignorar errores de red (servidor puede no estar listo)
    }
  }, 500);
}

// ─── Tab Switching ───────────────────────────────────────────────────────────

function switchTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.toggle('active', t.id === tabId));
  if (tabId === 'run-script') onRunScriptTabActivated();
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
  // Funcion para formatear numeros: miles con coma, siempre 2 decimales
  function formatNum(v) {
    if (v === null || v === undefined || v === '') return '';
    if (typeof v === 'number' || !isNaN(parseFloat(v))) {
      var num = typeof v === 'number' ? v : parseFloat(v);
      return num.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }
    return v;
  }
  let html = '<table class="data-table"><tr>';
  headers.forEach(h => html += `<th>${h}</th>`);
  html += '</tr>';
  rows.forEach(row => {
    html += '<tr>';
    row.forEach(v => html += `<td>${formatNum(v)}</td>`);
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

// ─── Run Script Tab ───────────────────────────────────────────────────────────

// Default code snippets per language
const SNIPPETS = {
  r:      '# R\nsummary(dataset)\n',
  python: '# Python\nprint("hello from NEVEN")\n',
  julia:  '# Julia\nprintln("hello from NEVEN")\n'
};

// Wire up all Run Script tab controls
function initRunScriptTab() {
  document.getElementById('btn-run-script').addEventListener('click', runScript);
  document.getElementById('btn-open-rpivot').addEventListener('click', openRPivot);

  // Ctrl+Enter shortcut in script textarea (mirrors SQL tab behavior)
  document.getElementById('script-input').addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); runScript(); }
  });

  // Language selector → update textarea with snippet
  document.getElementById('script-lang').addEventListener('change', e => {
    document.getElementById('script-input').value = SNIPPETS[e.target.value] || '';
  });

  // Function search filter
  document.getElementById('func-search').addEventListener('input', filterFunctions);

  // Pre-populate with the default R snippet
  document.getElementById('script-input').value = SNIPPETS['r'];
}

// Called when the Run Script tab becomes active (wired from switchTab)
async function onRunScriptTabActivated() {
  await Promise.all([
    refreshEngineStatus(),
    loadAvailableFunctions()
  ]);
}

// Stub — full implementation in task 10.2
async function refreshEngineStatus() {
  // Mark all dots as "checking" while the request is in flight
  ['r', 'python', 'julia'].forEach(lang => {
    const dot = document.getElementById(`engine-status-${lang}`);
    if (dot) dot.className = 'engine-dot checking';
  });
  try {
    const resp = await fetch(API_BASE + '/api/engines');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    ['r', 'python', 'julia'].forEach(lang => {
      const dot = document.getElementById(`engine-status-${lang}`);
      if (dot) {
        dot.className = 'engine-dot ' + (data[lang] ? 'available' : 'unavailable');
        dot.title = lang.toUpperCase() + ': ' + (data[lang] ? 'running' : 'stopped');
      }
    });
  } catch (err) {
    // Server unreachable — mark all as unavailable and log for debugging
    ['r', 'python', 'julia'].forEach(lang => {
      const dot = document.getElementById(`engine-status-${lang}`);
      if (dot) {
        dot.className = 'engine-dot unavailable';
        dot.title = lang.toUpperCase() + ': server unreachable';
      }
    });
    console.warn('[NEVEN] refreshEngineStatus failed:', err.message);
  }
}

// ─── Run Script: Execute ────────────────────────────────────────────────────

async function runScript() {
  const lang = document.getElementById('script-lang').value;
  const code = document.getElementById('script-input').value.trim();
  if (!code) return;
  setScriptBusy(true);
  try {
    const res = await apiCall('/api/' + lang, { code });
    renderScriptResult(res);
  } catch (e) {
    showScriptError(e.message);
  } finally {
    setScriptBusy(false);
  }
}

function setScriptBusy(busy) {
  const btn = document.getElementById('btn-run-script');
  const status = document.getElementById('script-status');
  btn.disabled = busy;
  status.textContent = busy ? '⏳' : '';
}

function showScriptError(msg) {
  const card = document.getElementById('script-output-card');
  const errEl = document.getElementById('script-error');
  // Hide all sub-elements first
  ['script-iframe', 'script-table', 'script-scalar', 'script-console'].forEach(id => {
    document.getElementById(id).style.display = 'none';
  });
  errEl.textContent = msg;
  errEl.style.display = '';
  card.style.display = '';
}

// ─── Run Script: Render Result ──────────────────────────────────────────────

function renderScriptResult(res) {
  const card   = document.getElementById('script-output-card');
  const iframe = document.getElementById('script-iframe');
  const table  = document.getElementById('script-table');
  const scalar = document.getElementById('script-scalar');
  const errEl  = document.getElementById('script-error');
  const cons   = document.getElementById('script-console');

  // Hide all sub-elements first
  [iframe, table, scalar, errEl, cons].forEach(el => el.style.display = 'none');
  card.style.display = '';

  if (res.status === 'error') {
    errEl.textContent = res.message || 'Unknown error';
    errEl.style.display = '';
  } else if (res.type === 'html') {
    iframe.srcdoc = res.html;
    iframe.style.display = '';
  } else if (res.type === 'array') {
    renderSQLResults(res);   // reuse existing function
    table.style.display = '';
  } else {
    // scalar types: string, integer, real, boolean
    scalar.textContent = String(res.result ?? '');
    scalar.style.display = '';
  }

  if (res.console) {
    cons.textContent = res.console;
    cons.style.display = '';
  }
}

// ─── Run Script: RPivot, Functions, Filter ──────────────────────────────────

async function openRPivot() {
  setScriptBusy(true);
  try {
    const res = await apiCall('/api/rpivot', {});
    renderScriptResult(res);
  } catch (e) {
    showScriptError(e.message);
  } finally {
    setScriptBusy(false);
  }
}

async function loadAvailableFunctions() {
  try {
    const data = await fetch(API_BASE + '/api/functions').then(r => r.json());
    const list = document.getElementById('func-list');
    list.innerHTML = '';
    const langs = data.languages || {};
    for (const [lang, fns] of Object.entries(langs)) {
      if (!fns.length) continue;
      const section = document.createElement('div');
      section.dataset.lang = lang;
      section.innerHTML = `<strong>${lang.toUpperCase()}</strong>`;
      fns.forEach(fn => {
        const entry = document.createElement('div');
        entry.className = 'func-entry';
        entry.dataset.name = fn.name || '';
        entry.dataset.desc = fn.description || '';
        entry.innerHTML = `<code>${fn.name}</code> — <span class="func-desc">${fn.description || ''}</span>`;
        section.appendChild(entry);
      });
      list.appendChild(section);
    }
  } catch (_) {}
}

function filterFunctions() {
  const q = (document.getElementById('func-search').value || '').toLowerCase();
  document.querySelectorAll('#func-list .func-entry').forEach(el => {
    const match = el.dataset.name.toLowerCase().includes(q) ||
                  el.dataset.desc.toLowerCase().includes(q);
    el.style.display = match ? '' : 'none';
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// Sheet Analyzer — Excel Consultant Feature
// ═══════════════════════════════════════════════════════════════════════════════
// Captures formulas from the active sheet and sends them to Python for analysis.
// The AI agent can then act as consultant/auditor/documentator.

/**
 * Capture all formulas from the active worksheet and send to /api/sheet/analyze.
 * 
 * @param {Object} options - Optional configuration
 * @param {boolean} options.selectedOnly - If true, only capture from selection (default: false = entire used range)
 * @param {boolean} options.includeGraph - Include Mermaid dependency graph (default: true)
 * @returns {Promise<Object>} Analysis result from Python backend
 */
async function captureSheetForAnalysis(options = {}) {
  const { selectedOnly = false, includeGraph = true } = options;
  
  try {
    // Capture data from Excel
    const sheetData = await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      sheet.load('name');
      
      // Get Excel's display language for formula localization
      const app = context.workbook.application;
      app.load('calculationMode'); // We can't get displayLanguage directly, but we'll detect from formulas
      
      // Determine which range to analyze
      let range;
      if (selectedOnly) {
        range = context.workbook.getSelectedRange();
      } else {
        range = sheet.getUsedRange();
      }
      
      // Load formulas AND values (values needed for input cells like parameters)
      range.load(['address', 'formulas', 'values', 'rowCount', 'columnCount', 'cellCount']);
      
      await context.sync();
      
      // Extract formula cells and build a values map for non-formula cells
      const formulas = [];
      const cellValues = {};  // Map of address -> value for non-formula cells
      const formulaGrid = range.formulas;
      const valueGrid = range.values;
      const startAddress = range.address; // e.g., "Sheet1!A1:Z100"
      
      // Parse starting cell from address
      // FIX: The previous regex captured sheet name (e.g., "Hoja1") as column
      // causing impossible addresses like "IVQH10" (column 173506)
      // Solution: Split on "!" first, then parse the cell reference part
      let cellRefPart = startAddress;
      if (startAddress.includes('!')) {
        cellRefPart = startAddress.split('!').pop();  // Take part after "!"
      }
      // Match cell reference: optional $, 1-3 letters, optional $, digits
      const match = cellRefPart.match(/\$?([A-Z]{1,3})\$?(\d+)/i);
      const startCol = match ? columnToNumber(match[1]) : 1;
      const startRow = match ? parseInt(match[2], 10) : 1;
      
      // ═══════════════════════════════════════════════════════════════════════
      // NEW: Extract column headers (first row) and build column name map
      // This allows the AI to understand "SALARIOS" = column D
      // ═══════════════════════════════════════════════════════════════════════
      const columnHeaders = {};  // Map: column letter -> header name
      const headerRow = valueGrid[0];  // First row = headers
      if (headerRow) {
        for (let c = 0; c < headerRow.length; c++) {
          const headerValue = headerRow[c];
          if (headerValue && typeof headerValue === 'string' && headerValue.trim()) {
            const colLetter = numberToColumn(startCol + c);
            columnHeaders[colLetter] = headerValue.trim();
          }
        }
      }
      
      // Build data range info (excluding header row)
      const dataRowCount = Math.max(0, range.rowCount - 1);
      const dataStartRow = startRow + 1;  // Data starts after header
      const dataEndRow = startRow + range.rowCount - 1;
      
      for (let r = 0; r < formulaGrid.length; r++) {
        for (let c = 0; c < formulaGrid[r].length; c++) {
          const cellFormula = formulaGrid[r][c];
          const cellValue = valueGrid[r][c];
          const cellAddress = numberToColumn(startCol + c) + (startRow + r);
          
          // Only include cells that have formulas (start with =)
          if (typeof cellFormula === 'string' && cellFormula.startsWith('=')) {
            formulas.push({
              address: cellAddress,
              formula: cellFormula
            });
          } else if (cellValue !== null && cellValue !== '' && cellValue !== undefined) {
            // Store non-formula cell values (potential input parameters)
            cellValues[cellAddress] = cellValue;
          }
        }
      }
      
      return {
        sheet_name: sheet.name,
        formulas: formulas,
        cell_values: cellValues,
        column_headers: columnHeaders,  // NEW: Map of column letter -> header name
        data_range: {
          start_row: dataStartRow,
          end_row: dataEndRow,
          row_count: dataRowCount,
          columns: Object.keys(columnHeaders).length
        },
        total_cells: range.cellCount,
        range_address: startAddress
      };
    });
    
    // If no formulas found, return early
    if (sheetData.formulas.length === 0) {
      return {
        status: 'ok',
        sheet_name: sheetData.sheet_name,
        summary: {
          total_formulas: 0,
          message: 'No formulas found in ' + (selectedOnly ? 'selection' : 'the sheet')
        }
      };
    }
    
    // Send to Python backend for analysis
    const response = await fetch(API_BASE + '/api/sheet/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sheet_name: sheetData.sheet_name,
        formulas: sheetData.formulas,
        cell_values: sheetData.cell_values,  // NEW: Include cell values for input cells
        total_cells: sheetData.total_cells,
        include_graph: includeGraph
        // language will be auto-detected by Python from formula patterns
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const analysis = await response.json();
    
    // Store for AI context (can be used by the IA tab)
    window._lastSheetAnalysis = analysis;
    
    return analysis;
    
  } catch (error) {
    console.error('[NEVEN] captureSheetForAnalysis error:', error);
    return {
      status: 'error',
      message: error.message || 'Failed to analyze sheet'
    };
  }
}

/**
 * Convert column letter(s) to number (A=1, B=2, ..., Z=26, AA=27, etc.)
 */
function columnToNumber(col) {
  let num = 0;
  for (let i = 0; i < col.length; i++) {
    num = num * 26 + (col.charCodeAt(i) - 64);
  }
  return num;
}

/**
 * Convert column number to letter(s) (1=A, 2=B, ..., 26=Z, 27=AA, etc.)
 */
function numberToColumn(num) {
  let col = '';
  while (num > 0) {
    const mod = (num - 1) % 26;
    col = String.fromCharCode(65 + mod) + col;
    num = Math.floor((num - 1) / 26);
  }
  return col;
}

/**
 * Quick analysis: Get a summary suitable for AI context.
 * Returns a condensed string for the AI prompt.
 */
async function getSheetAnalysisSummary() {
  const analysis = await captureSheetForAnalysis({ includeGraph: false });
  
  if (analysis.status === 'error') {
    return `Error analyzing sheet: ${analysis.message}`;
  }
  
  if (!analysis.summary || analysis.summary.total_formulas === 0) {
    return `Sheet "${analysis.sheet_name}" has no formulas.`;
  }
  
  const s = analysis.summary;
  const funcs = (analysis.functions || []).slice(0, 10).map(f => f.name).join(', ');
  const complexity = analysis.complexity?.level || 'unknown';
  
  return `Sheet "${analysis.sheet_name}": ${s.total_formulas} formulas, ` +
         `${s.unique_patterns} patterns, complexity: ${complexity}. ` +
         `Top functions: ${funcs || 'none'}. ` +
         `Inputs: ${(analysis.critical_cells?.inputs || []).length}, ` +
         `Outputs: ${(analysis.critical_cells?.outputs || []).length}.`;
}

// Expose to global scope for use from console or other modules
window.captureSheetForAnalysis = captureSheetForAnalysis;
window.getSheetAnalysisSummary = getSheetAnalysisSummary;


// ═══════════════════════════════════════════════════════════════════════════════
// Excel Consultant — AI Integration
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Analyze the current sheet and inject the analysis as AI context.
 * This enables "Excel Consultant" mode in the IA tab.
 * 
 * @param {Object} options - Same options as captureSheetForAnalysis
 * @returns {Promise<boolean>} True if context was injected successfully
 */
async function analyzeSheetForAI(options = {}) {
  try {
    const analysis = await captureSheetForAnalysis(options);
    
    if (analysis.status === 'error') {
      console.error('[NEVEN] analyzeSheetForAI: error =', analysis.message);
      showToast('Error: ' + analysis.message);
      return false;
    }
    
    if (!analysis.summary || analysis.summary.total_formulas === 0) {
      console.warn('[NEVEN] analyzeSheetForAI: no hay fórmulas en la hoja');
      showToast('La hoja no tiene fórmulas para analizar');
      return false;
    }
    
    // Format analysis as context for AI
    const contextText = formatAnalysisForAI(analysis);
    
    // Inject into AI state (same pattern as _aiAttachDataset)
    if (typeof _aiState !== 'undefined') {
      _aiState.context = contextText;
      
      // Update context card
      const ctxCard = document.getElementById('ai-context-card');
      const ctxSummary = document.getElementById('ai-context-summary');
      if (ctxCard && ctxSummary) {
        ctxCard.style.display = '';
        ctxSummary.textContent = ` ${analysis.sheet_name}: ${analysis.summary.total_formulas} fórmulas`;
      }
      
      // Add system message to chat history
      const history = document.getElementById('ai-chat-history');
      if (history) {
        const div = document.createElement('div');
        div.style.cssText = 'margin:8px 0;padding:7px 10px;background:rgba(100,180,100,0.08);' +
          'border-left:3px solid #6b6;border-radius:4px;font-size:11px;color:var(--text-secondary)';
        div.innerHTML = `<span style="color:#6b6;font-weight:600">Modo Consultor Excel activado</span>` +
          ` — Hoja "${analysis.sheet_name}": ${analysis.summary.total_formulas} fórmulas, ` +
          `complejidad ${analysis.complexity?.level || 'N/A'}. Pregunta lo que necesites.` +
          ` <button onclick="downloadSheetAnalysisMD()" style="margin-left:8px;background:#6b6;color:#fff;border:none;border-radius:3px;padding:2px 6px;font-size:9px;cursor:pointer" title="Descargar análisis como Markdown">⬇ MD</button>`;
        history.appendChild(div);
        history.scrollTop = history.scrollHeight;
      }
      
      // Show Excel Consultant chips
      showExcelConsultantChips(analysis);
      
      showToast(' Análisis de hoja cargado — Modo Consultor activo');
      return true;
    }
    
    return false;
    
  } catch (error) {
    console.error('[NEVEN] analyzeSheetForAI error:', error);
    showToast('Error al analizar: ' + error.message);
    return false;
  }
}

/**
 * Format sheet analysis as structured text for AI context.
 */
function formatAnalysisForAI(analysis) {
  const lines = ['=== ANÁLISIS DE HOJA EXCEL ==='];
  lines.push(`Hoja: ${analysis.sheet_name}`);
  
  if (analysis.detected_language) {
    lines.push(`Idioma Excel: ${analysis.detected_language === 'es' ? 'Español' : 'Inglés'}`);
  }
  
  // ═══════════════════════════════════════════════════════════════════════════
  // COLUMN STRUCTURE — Critical for AI to understand data layout
  // Shows: column letter = header name (data range)
  // ═══════════════════════════════════════════════════════════════════════════
  const columnHeaders = analysis.column_headers || {};
  const dataRange = analysis.data_range || {};
  
  if (Object.keys(columnHeaders).length > 0) {
    lines.push('');
    lines.push('## Estructura de columnas');
    lines.push(`Datos en filas ${dataRange.start_row || 2} a ${dataRange.end_row || '?'} (${dataRange.row_count || '?'} filas de datos)`);
    lines.push('');
    
    // Sort columns by letter (A, B, C, ...)
    const sortedCols = Object.keys(columnHeaders).sort((a, b) => {
      return columnToNumber(a) - columnToNumber(b);
    });
    
    sortedCols.forEach(colLetter => {
      const headerName = columnHeaders[colLetter];
      const dataStart = `${colLetter}${dataRange.start_row || 2}`;
      const dataEnd = `${colLetter}${dataRange.end_row || '?'}`;
      lines.push(`- Columna ${colLetter} = "${headerName}" → datos en ${dataStart}:${dataEnd}`);
    });
  }
  
  // Summary
  const s = analysis.summary || {};
  lines.push('');
  lines.push('## Resumen');
  lines.push(`- Total fórmulas: ${s.total_formulas || 0}`);
  lines.push(`- Celdas totales: ${s.total_cells || 0}`);
  lines.push(`- Densidad de fórmulas: ${s.formula_density || 0}%`);
  lines.push(`- Patrones únicos: ${s.unique_patterns || 0}`);
  lines.push(`- Funciones distintas: ${s.functions_used || 0}`);
  lines.push(`- Complejidad: ${s.complexity_level || 'N/A'}`);
  
  // ═══════════════════════════════════════════════════════════════════════════
  // Cell Map — Shows content and relationships clearly
  // ═══════════════════════════════════════════════════════════════════════════
  const inputValues = (analysis.critical_cells && analysis.critical_cells.input_values) || {};
  const inputs = (analysis.critical_cells && analysis.critical_cells.inputs) || [];
  const outputs = (analysis.critical_cells && analysis.critical_cells.outputs) || [];
  const edges = (analysis.dependencies && analysis.dependencies.edges) || [];
  const nodes = (analysis.dependencies && analysis.dependencies.nodes) || {};
  
  // Build reverse dependency map: cell -> list of cells that reference it
  const referencedBy = {};
  edges.forEach(e => {
    const src = e.source;
    if (!referencedBy[src]) referencedBy[src] = [];
    referencedBy[src].push(e.target);
  });
  
  // Show input cells (constants/parameters) with their values and who uses them
  if (inputs.length > 0) {
    lines.push('');
    lines.push('## Celdas de entrada (parámetros y constantes)');
    inputs.slice(0, 15).forEach(addr => {
      const value = inputValues[addr];
      const usedBy = referencedBy[addr] || [];
      let line = `- ${addr}`;
      if (value !== undefined) {
        line += ` = ${value}`;
      }
      if (usedBy.length > 0) {
        const sample = usedBy.slice(0, 5).join(', ');
        line += ` → usado por: ${sample}`;
        if (usedBy.length > 5) line += ` (+${usedBy.length - 5} más)`;
      }
      lines.push(line);
    });
    if (inputs.length > 15) lines.push(`  ... y ${inputs.length - 15} inputs más`);
  }
  
  // Show formula cells with their formulas and dependencies
  const formulaCells = Object.keys(nodes);
  if (formulaCells.length > 0) {
    lines.push('');
    lines.push('## Celdas con fórmulas (primeras 20)');
    formulaCells.slice(0, 20).forEach(addr => {
      const node = nodes[addr];
      const formula = node.formula || '';
      // Extract dependencies from edges
      const deps = edges.filter(e => e.target === addr).map(e => e.source);
      let line = `- ${addr} = ${formula}`;
      if (deps.length > 0) {
        line += ` | depende de: ${deps.slice(0, 5).join(', ')}`;
        if (deps.length > 5) line += ` (+${deps.length - 5} más)`;
      }
      lines.push(line);
    });
    if (formulaCells.length > 20) lines.push(`  ... y ${formulaCells.length - 20} fórmulas más`);
  }
  
  // Show output cells (final results)
  if (outputs.length > 0) {
    lines.push('');
    lines.push('## Celdas de salida (resultados finales)');
    lines.push(`Celdas que no son referenciadas por otras fórmulas: ${outputs.slice(0, 10).join(', ')}`);
    if (outputs.length > 10) lines.push(`  ... y ${outputs.length - 10} más`);
  }
  
  // Functions used
  if (analysis.functions && analysis.functions.length > 0) {
    lines.push('');
    lines.push('## Funciones utilizadas');
    analysis.functions.slice(0, 15).forEach(f => {
      let line = `- ${f.name}: ${f.count}x`;
      if (f.category) line += ` [${f.category}]`;
      if (f.description) line += ` — ${f.description}`;
      lines.push(line);
    });
    if (analysis.functions.length > 15) {
      lines.push(`- ... y ${analysis.functions.length - 15} funciones más`);
    }
  }
  
  // Patterns
  if (analysis.patterns && analysis.patterns.length > 0) {
    lines.push('');
    lines.push('## Patrones de fórmulas (top 10)');
    analysis.patterns.slice(0, 10).forEach(p => {
      lines.push(`- "${p.pattern}" (${p.count}x) — ejemplos: ${(p.examples || []).slice(0, 3).join(', ')}`);
    });
  }
  
  // Complexity details
  if (analysis.complexity) {
    const c = analysis.complexity;
    lines.push('');
    lines.push('## Métricas de complejidad');
    lines.push(`- Nivel: ${c.level || 'N/A'}`);
    lines.push(`- Score: ${c.score || 0}/100`);
    
    if (c.details) {
      if (c.details.max_nesting_depth) lines.push(`- Anidamiento máximo: ${c.details.max_nesting_depth} niveles`);
      if (c.details.unique_functions) lines.push(`- Funciones únicas: ${c.details.unique_functions}`);
    }
  }
  
  // Dependency stats
  if (analysis.dependencies && analysis.dependencies.stats) {
    const d = analysis.dependencies.stats;
    lines.push('');
    lines.push('## Estadísticas de dependencias');
    lines.push(`- Total conexiones: ${d.total_edges || 0}`);
    if (d.max_in_degree) lines.push(`- Celda más referenciada: grado de entrada ${d.max_in_degree}`);
    if (d.max_out_degree) lines.push(`- Celda con más dependencias: grado de salida ${d.max_out_degree}`);
  }
  
  return lines.join('\n');
}

// Expose to global scope
window.analyzeSheetForAI = analyzeSheetForAI;
window.formatAnalysisForAI = formatAnalysisForAI;


// ═══════════════════════════════════════════════════════════════════════════════
// Excel Consultant — Workbook-Level Analysis
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Capture all sheets in the workbook for analysis.
 * 
 * @param {Object} options - Configuration options
 * @param {number} options.maxSheets - Maximum sheets to capture (default: 20)
 * @param {boolean} options.includeHiddenSheets - Include hidden sheets (default: false)
 * @param {boolean} options.includeGraph - Include Mermaid data flow graph (default: true)
 * @returns {Promise<Object>} Workbook data for Python backend
 */
async function captureWorkbookForAnalysis(options = {}) {
  const { 
    maxSheets = 20, 
    includeHiddenSheets = false,
    includeGraph = true 
  } = options;
  
  try {
    return await Excel.run(async (context) => {
      const workbook = context.workbook;
      workbook.load("name");
      
      const sheets = workbook.worksheets;
      sheets.load("items/name,items/visibility");
      await context.sync();
      
      const sheetDataList = [];
      let capturedCount = 0;
      
      for (const sheet of sheets.items) {
        // Skip hidden sheets unless requested
        if (!includeHiddenSheets && 
            sheet.visibility !== Excel.SheetVisibility.visible) {
          continue;
        }
        
        // Limit to maxSheets to avoid timeout
        if (capturedCount >= maxSheets) {
          console.log(`[NEVEN] captureWorkbookForAnalysis: limite de ${maxSheets} hojas alcanzado`);
          break;
        }
        
        try {
          // Capture this sheet's data
          const sheetData = await captureSheetData(context, sheet);
          sheetDataList.push(sheetData);
          capturedCount++;
        } catch (sheetError) {
          console.warn(`[NEVEN] Error capturing sheet "${sheet.name}":`, sheetError);
          // Add minimal entry for failed sheet
          sheetDataList.push({
            name: sheet.name,
            formulas: [],
            cell_values: {},
            total_cells: 0,
            error: sheetError.message
          });
          capturedCount++;
        }
      }
      
      return {
        workbook_name: workbook.name,
        sheets: sheetDataList,
        total_sheets: sheets.items.length,
        captured_sheets: capturedCount,
        include_graph: includeGraph
      };
    });
    
  } catch (error) {
    console.error('[NEVEN] captureWorkbookForAnalysis error:', error);
    return {
      status: 'error',
      message: error.message || 'Failed to capture workbook'
    };
  }
}

/**
 * Capture data from a single sheet (helper for workbook analysis).
 * @private
 */
async function captureSheetData(context, sheet) {
  sheet.load('name');
  
  const range = sheet.getUsedRange();
  range.load(['address', 'formulas', 'values', 'rowCount', 'columnCount', 'cellCount']);
  
  await context.sync();
  
  const formulas = [];
  const cellValues = {};
  const formulaGrid = range.formulas;
  const valueGrid = range.values;
  const startAddress = range.address;
  
  // Parse starting cell
  let cellRefPart = startAddress;
  if (startAddress.includes('!')) {
    cellRefPart = startAddress.split('!').pop();
  }
  const match = cellRefPart.match(/\$?([A-Z]{1,3})\$?(\d+)/i);
  const startCol = match ? columnToNumber(match[1]) : 1;
  const startRow = match ? parseInt(match[2], 10) : 1;
  
  // Extract column headers
  const columnHeaders = {};
  const headerRow = valueGrid[0];
  if (headerRow) {
    for (let c = 0; c < headerRow.length; c++) {
      const headerValue = headerRow[c];
      if (headerValue && typeof headerValue === 'string' && headerValue.trim()) {
        const colLetter = numberToColumn(startCol + c);
        columnHeaders[colLetter] = headerValue.trim();
      }
    }
  }
  
  // Extract formulas and cell values
  for (let r = 0; r < formulaGrid.length; r++) {
    for (let c = 0; c < formulaGrid[r].length; c++) {
      const cellFormula = formulaGrid[r][c];
      const cellValue = valueGrid[r][c];
      const cellAddress = numberToColumn(startCol + c) + (startRow + r);
      
      if (typeof cellFormula === 'string' && cellFormula.startsWith('=')) {
        formulas.push({
          address: cellAddress,
          formula: cellFormula
        });
      } else if (cellValue !== null && cellValue !== '' && cellValue !== undefined) {
        cellValues[cellAddress] = cellValue;
      }
    }
  }
  
  return {
    name: sheet.name,
    formulas: formulas,
    cell_values: cellValues,
    column_headers: columnHeaders,
    total_cells: range.cellCount
  };
}

/**
 * Analyze entire workbook and inject as AI context.
 * Enables "Excel Consultant" mode at workbook level.
 * 
 * @param {Object} options - Same options as captureWorkbookForAnalysis
 * @returns {Promise<boolean>} True if analysis was successful
 */
async function analyzeWorkbookForAI(options = {}) {
  try {
    showToast(' Analizando libro de trabajo...');
    
    const workbookData = await captureWorkbookForAnalysis(options);
    
    if (workbookData.status === 'error') {
      console.error('[NEVEN] analyzeWorkbookForAI: error =', workbookData.message);
      showToast('Error: ' + workbookData.message);
      return false;
    }
    
    // Check if we have any data
    const totalFormulas = workbookData.sheets.reduce(
      (sum, s) => sum + (s.formulas ? s.formulas.length : 0), 0
    );
    
    if (totalFormulas === 0) {
      console.warn('[NEVEN] analyzeWorkbookForAI: no hay fórmulas en el libro');
      showToast('El libro no tiene fórmulas para analizar');
      return false;
    }
    
    // Send to Python backend for analysis
    const response = await fetch(API_BASE + '/api/workbook/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workbookData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const analysis = await response.json();
    
    if (analysis.status !== 'ok') {
      throw new Error(analysis.message || 'Analysis failed');
    }
    
    // Store for reference
    window._lastWorkbookAnalysis = analysis;
    
    // Format as AI context
    const contextText = formatWorkbookAnalysisForAI(analysis);
    
    // Inject into AI state
    if (typeof _aiState !== 'undefined') {
      _aiState.context = contextText;
      
      // Update context card
      const ctxCard = document.getElementById('ai-context-card');
      const ctxSummary = document.getElementById('ai-context-summary');
      if (ctxCard && ctxSummary) {
        ctxCard.style.display = '';
        const stats = analysis.aggregated_stats || {};
        ctxSummary.textContent = ` ${analysis.workbook_name}: ${analysis.captured_sheets} hojas, ${stats.total_formulas || 0} fórmulas`;
      }
      
      // Add system message to chat history
      const history = document.getElementById('ai-chat-history');
      if (history) {
        const div = document.createElement('div');
        div.style.cssText = 'margin:8px 0;padding:7px 10px;background:rgba(100,100,200,0.08);' +
          'border-left:3px solid #66b;border-radius:4px;font-size:11px;color:var(--text-secondary)';
        
        const pattern = analysis.workbook_pattern || {};
        const stats = analysis.aggregated_stats || {};
        
        div.innerHTML = `<span style="color:#66b;font-weight:600">Modo Consultor de Libro activo</span>` +
          ` — "${analysis.workbook_name}": ${analysis.captured_sheets} hojas, ` +
          `${stats.total_formulas || 0} fórmulas, ` +
          `patrón: ${pattern.pattern || 'N/A'} (${Math.round((pattern.confidence || 0) * 100)}% conf.). ` +
          `Pregunta sobre cualquier hoja o relación entre ellas.` +
          ` <button onclick="downloadWorkbookAnalysisMD()" style="margin-left:8px;background:#66b;color:#fff;border:none;border-radius:3px;padding:2px 6px;font-size:9px;cursor:pointer" title="Descargar análisis como Markdown">MD</button>`;
        history.appendChild(div);
        
        // Mostrar grafo D3 de flujo de datos (interactivo, arrastrable)
        const flow = analysis.data_flow || {};
        if (flow.nodes && flow.nodes.length > 0) {
          const graphDiv = document.createElement('div');
          graphDiv.style.cssText = 'margin:8px 0;padding:10px;background:rgba(100,100,200,0.05);' +
            'border:1px solid rgba(100,100,200,0.2);border-radius:6px';
          graphDiv.innerHTML = '<div style="font-size:11px;color:#66b;margin-bottom:8px;font-weight:600">Flujo de datos entre hojas <span style="font-weight:400;color:#888">(arrastra los nodos)</span></div>';
          
          // Contenedor para el SVG
          const svgContainer = document.createElement('div');
          svgContainer.id = 'workbook-graph-' + Date.now();
          svgContainer.style.cssText = 'background:#1a1a2e;border-radius:6px;min-height:300px;position:relative';
          graphDiv.appendChild(svgContainer);
          
          // Botones de accion
          const btnBar = document.createElement('div');
          btnBar.style.cssText = 'margin-top:8px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap';
          btnBar.innerHTML = `
            <button id="${svgContainer.id}-download-html" style="background:#3a3a2a;color:#d7a538;border:1px solid #d7a538;border-radius:4px;padding:4px 10px;font-size:10px;cursor:pointer">Descargar HTML</button>
            <button id="${svgContainer.id}-download-svg" style="background:#2a2a3a;color:#aaa;border:1px solid #555;border-radius:4px;padding:4px 10px;font-size:10px;cursor:pointer">Descargar SVG</button>
            <button id="${svgContainer.id}-slide" style="background:#2a2a3a;color:#aaa;border:1px solid #555;border-radius:4px;padding:4px 10px;font-size:10px;cursor:pointer">Enviar a Slide</button>
          `;
          graphDiv.appendChild(btnBar);
          
          history.appendChild(graphDiv);
          
          // Renderizar grafo D3 despues de agregar al DOM
          setTimeout(() => {
            renderWorkbookGraphD3(svgContainer, flow.nodes, flow.edges || []);
            
            // Configurar boton HTML (interactivo)
            document.getElementById(svgContainer.id + '-download-html').onclick = () => {
              if (svgContainer._graphData) {
                const html = generateGraphHTML(svgContainer._graphData, 'Flujo de datos: ' + (analysis.workbook_name || 'Workbook'));
                const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'flujo_datos_' + (analysis.workbook_name || 'workbook') + '.html';
                a.click();
                URL.revokeObjectURL(url);
                showToast('HTML interactivo descargado');
              }
            };
            
            // Configurar boton SVG (estatico)
            document.getElementById(svgContainer.id + '-download-svg').onclick = () => {
              const svg = svgContainer.querySelector('svg');
              if (svg) {
                const blob = new Blob([svg.outerHTML], { type: 'image/svg+xml' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'flujo_datos_' + (analysis.workbook_name || 'workbook') + '.svg';
                a.click();
                URL.revokeObjectURL(url);
              }
            };
            
            document.getElementById(svgContainer.id + '-slide').onclick = () => {
              const svg = svgContainer.querySelector('svg');
              if (svg && typeof _nevenSendToSlide === 'function') {
                const svgHtml = '<html><head><meta charset="UTF-8"><style>body{background:#1e1e2e;margin:0;padding:20px;display:flex;justify-content:center;align-items:center;min-height:100vh}</style></head><body>' + svg.outerHTML + '</body></html>';
                _nevenSendToSlide('Flujo de datos: ' + (analysis.workbook_name || 'Workbook'), svgHtml, null);
                showToast('Enviado a Presentaciones');
              }
            };
          }, 100);
        }
        
        history.scrollTop = history.scrollHeight;
      }
      
      // Show workbook consultant chips
      showWorkbookConsultantChips(analysis);
      
      showToast('Analisis de libro cargado — Modo Consultor activo');
      return true;
    }
    
    return false;
    
  } catch (error) {
    console.error('[NEVEN] analyzeWorkbookForAI error:', error);
    showToast('Error al analizar libro: ' + error.message);
    return false;
  }
}

/**
 * Format workbook analysis as structured text for AI context.
 */
function formatWorkbookAnalysisForAI(analysis) {
  const lines = ['=== ANÁLISIS DE LIBRO DE TRABAJO ==='];
  lines.push(`Libro: ${analysis.workbook_name}`);
  lines.push(`Hojas analizadas: ${analysis.captured_sheets} de ${analysis.sheet_count}`);
  
  // Workbook pattern
  const pattern = analysis.workbook_pattern || {};
  if (pattern.pattern) {
    lines.push('');
    lines.push('## Patrón arquitectural');
    lines.push(`- Tipo: ${pattern.pattern} (confianza: ${Math.round((pattern.confidence || 0) * 100)}%)`);
    if (pattern.characteristics) {
      pattern.characteristics.filter(c => c).forEach(c => {
        lines.push(`- ${c}`);
      });
    }
  }
  
  // Aggregated stats
  const stats = analysis.aggregated_stats || {};
  lines.push('');
  lines.push('## Resumen del libro');
  lines.push(`- Total hojas: ${stats.total_sheets || 0}`);
  lines.push(`- Total fórmulas: ${stats.total_formulas || 0}`);
  lines.push(`- Funciones únicas: ${stats.unique_functions || 0}`);
  lines.push(`- Referencias entre hojas: ${stats.cross_sheet_references || 0}`);
  lines.push(`- Referencias externas: ${stats.external_references || 0}`);
  lines.push(`- Hojas huérfanas: ${stats.orphan_sheets || 0}`);
  lines.push(`- Complejidad máxima: ${stats.max_complexity_score || 0}/100`);
  
  // Cross-sheet dependencies
  const deps = analysis.cross_sheet_dependencies || {};
  if (deps.edges && deps.edges.length > 0) {
    lines.push('');
    lines.push('## Referencias entre hojas (principales)');
    deps.edges.slice(0, 10).forEach(e => {
      lines.push(`- ${e.from_sheet} → ${e.to_sheet}: ${e.formula_count} referencias`);
    });
    if (deps.edges.length > 10) {
      lines.push(`  ... y ${deps.edges.length - 10} conexiones más`);
    }
  }
  
  // Hub sheets
  if (deps.hub_sheets && deps.hub_sheets.length > 0) {
    lines.push('');
    lines.push('## Hojas centrales (hubs)');
    deps.hub_sheets.forEach(h => {
      lines.push(`- ${h.sheet}: ${h.total_refs} refs (${h.in} entrantes, ${h.out} salientes)`);
    });
  }
  
  // Orphan sheets
  if (deps.orphan_sheets && deps.orphan_sheets.length > 0) {
    lines.push('');
    lines.push('## Hojas sin conexiones');
    lines.push(`- ${deps.orphan_sheets.join(', ')}`);
  }
  
  // Data flow
  const flow = analysis.data_flow || {};
  if (flow.nodes && flow.nodes.length > 0) {
    lines.push('');
    lines.push('## Flujo de datos');
    
    const inputs = flow.nodes.filter(n => n.role === 'input');
    const processing = flow.nodes.filter(n => n.role === 'processing');
    const outputs = flow.nodes.filter(n => n.role === 'output');
    const isolated = flow.nodes.filter(n => n.role === 'isolated');
    
    if (inputs.length > 0) {
      lines.push(`- Hojas de entrada: ${inputs.map(n => n.name).join(', ')}`);
    }
    if (processing.length > 0) {
      lines.push(`- Hojas de proceso: ${processing.map(n => n.name).join(', ')}`);
    }
    if (outputs.length > 0) {
      lines.push(`- Hojas de salida: ${outputs.map(n => n.name).join(', ')}`);
    }
    if (isolated.length > 0) {
      lines.push(`- Hojas aisladas: ${isolated.map(n => n.name).join(', ')}`);
    }
    
    if (flow.critical_path && flow.critical_path.length > 1) {
      lines.push(`- Ruta crítica: ${flow.critical_path.join(' → ')}`);
    }
  }
  
  // Per-sheet summaries
  if (analysis.sheets && analysis.sheets.length > 0) {
    lines.push('');
    lines.push('## Resumen por hoja');
    analysis.sheets.forEach((sheet, idx) => {
      const s = sheet.summary || {};
      const c = sheet.complexity || {};
      lines.push(`${idx + 1}. **${sheet.sheet_name}**: ${s.total_formulas || 0} fórmulas, ` +
                 `complejidad: ${c.level || 'N/A'} (${c.score || 0}/100)`);
    });
  }
  
  // Recommendations
  if (analysis.recommendations && analysis.recommendations.length > 0) {
    lines.push('');
    lines.push('## Recomendaciones');
    analysis.recommendations.forEach(r => {
      const icon = r.priority === 'high' ? '' : (r.priority === 'medium' ? '' : '');
      lines.push(`- ${icon} [${r.type}] ${r.message}`);
    });
  }
  
  // NOTE: Mermaid graph is shown directly in UI, not sent to AI (AI tends to modify it)
  // if (flow.mermaid) { ... }
  
  return lines.join('\n');
}

/**
 * Predefined prompts for Workbook Consultant mode.
 */
const WORKBOOK_CONSULTANT_CHIPS = [
  { label: '¿Cómo funciona este libro?', prompt: 'Explica la arquitectura general de este libro de trabajo. ¿Cuál es el flujo de datos entre hojas? ¿Cuál es el propósito de cada una?' },
  { label: 'Relaciones entre hojas', prompt: 'Analiza las relaciones y dependencias entre las hojas de este libro. ¿Qué hojas alimentan a otras? ¿Hay referencias circulares?' },
  { label: 'Auditar estructura', prompt: 'Audita la estructura de este libro: ¿hay hojas huérfanas sin conexión? ¿Hay complejidad excesiva en alguna hoja? ¿La organización es clara?' },
  { label: 'Hojas críticas', prompt: 'Identifica las hojas más críticas de este libro: ¿cuáles son los puntos centrales que si fallan afectan todo el modelo?' },
  { label: 'Simplificar estructura', prompt: '¿Se podría simplificar la estructura de este libro? ¿Hay hojas que podrían combinarse o separarse para mejor mantenimiento?' },
  { label: 'Documentar libro', prompt: 'Genera documentación técnica de este libro: propósito general, flujo de datos, hojas principales, dependencias críticas y guía para mantenerlo.' },
];

/**
 * Show the Workbook Consultant chips card.
 */
function showWorkbookConsultantChips(analysis) {
  const card = document.getElementById('ai-excel-consultant-card');
  const chipsContainer = document.getElementById('ai-excel-chips');
  
  if (!card || !chipsContainer) return;
  
  // Clear previous chips
  chipsContainer.innerHTML = '';
  
  // Create chips with workbook-specific prompts (same style as Prompts Guia)
  WORKBOOK_CONSULTANT_CHIPS.forEach(chip => {
    const btn = document.createElement('button');
    btn.textContent = chip.label;
    btn.title = chip.prompt.substring(0, 100) + '...';
    btn.style.cssText = 
      'background:var(--bg-secondary);' +
      'border:1px solid var(--border);' +
      'color:var(--text-secondary);' +
      'border-radius:12px;' +
      'padding:3px 10px;' +
      'font-size:10px;' +
      'cursor:pointer;' +
      'transition:all 0.15s;';
    
    btn.onmouseover = function() {
      this.style.borderColor = 'var(--accent)';
      this.style.color = 'var(--accent)';
    };
    btn.onmouseout = function() {
      this.style.borderColor = 'var(--border)';
      this.style.color = 'var(--text-secondary)';
    };
    
    btn.addEventListener('click', function() {
      sendExcelConsultantPrompt(chip.prompt);
    });
    
    chipsContainer.appendChild(btn);
  });
  
  // Show the card
  card.style.display = '';
}

// Expose workbook functions to global scope
window.captureWorkbookForAnalysis = captureWorkbookForAnalysis;
window.analyzeWorkbookForAI = analyzeWorkbookForAI;
window.formatWorkbookAnalysisForAI = formatWorkbookAnalysisForAI;

/**
 * Render workbook data flow as interactive D3 hierarchical graph.
 * Layout: Input (left) → Processing (center) → Output (right)
 * Features: drag nodes, zoom/pan, color by role, weighted edges.
 * 
 * @param {HTMLElement} container - Container element for the SVG
 * @param {Array} nodes - [{name, role, ...}] from data_flow.nodes
 * @param {Array} edges - [{source, target, weight}] from data_flow.edges
 */
function renderWorkbookGraphD3(container, nodes, edges) {
  if (!nodes || nodes.length === 0) {
    container.innerHTML = '<div style="color:#888;text-align:center;padding:40px">Sin datos de flujo</div>';
    return;
  }
  
  // Dimensions - wider for hierarchical layout
  const width = container.clientWidth || 500;
  const height = Math.max(350, Math.min(600, nodes.length * 30));
  
  // Color scale by role - NEVEN palette (amber/gold tones)
  const roleColors = {
    input: '#d7a538',      // Gold/Amber (accent)
    output: '#c9302c',     // Muted red
    processing: '#5a7a9a', // Steel blue-gray
    isolated: '#666666'    // Gray
  };
  
  // Group nodes by role for hierarchical layout
  const inputNodes = nodes.filter(n => n.role === 'input');
  const outputNodes = nodes.filter(n => n.role === 'output');
  const processingNodes = nodes.filter(n => n.role === 'processing' || n.role === 'isolated');
  
  // Calculate initial positions (hierarchical: left → center → right)
  const margin = 60;
  const colWidth = (width - 2 * margin) / 3;
  
  const nodeData = nodes.map(n => {
    let x, y;
    const role = n.role || 'processing';
    
    if (role === 'input') {
      const idx = inputNodes.findIndex(inp => inp.name === n.name);
      x = margin + colWidth * 0.5;
      y = margin + (idx + 0.5) * (height - 2 * margin) / Math.max(1, inputNodes.length);
    } else if (role === 'output') {
      const idx = outputNodes.findIndex(out => out.name === n.name);
      x = width - margin - colWidth * 0.5;
      y = margin + (idx + 0.5) * (height - 2 * margin) / Math.max(1, outputNodes.length);
    } else {
      const idx = processingNodes.findIndex(p => p.name === n.name);
      x = margin + colWidth * 1.5;
      y = margin + (idx + 0.5) * (height - 2 * margin) / Math.max(1, processingNodes.length);
    }
    
    return {
      id: n.name,
      name: n.name,
      role: role,
      complexity: n.complexity_score || 0,
      x: x,
      y: y,
      fx: null,  // Will be set on drag
      fy: null
    };
  });
  
  const nodeMap = new Map(nodeData.map(n => [n.id, n]));
  
  const linkData = edges.map(e => ({
    source: e.source,
    target: e.target,
    weight: e.weight || 1
  })).filter(e => nodeMap.has(e.source) && nodeMap.has(e.target));
  
  // Clear container
  container.innerHTML = '';
  
  // Create SVG with zoom support
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height])
    .attr('xmlns', 'http://www.w3.org/2000/svg')
    .style('background', '#1e1e2e')
    .style('border-radius', '8px');
  
  // Zoom behavior
  const g = svg.append('g');
  
  const zoom = d3.zoom()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    });
  
  svg.call(zoom);
  
  // Arrow marker for directed edges
  svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '-0 -5 10 10')
    .attr('refX', 18)
    .attr('refY', 0)
    .attr('orient', 'auto')
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .append('path')
    .attr('d', 'M 0,-5 L 10,0 L 0,5')
    .attr('fill', '#aaa');
  
  // Force simulation - gentler forces for hierarchical layout
  const simulation = d3.forceSimulation(nodeData)
    .force('link', d3.forceLink(linkData).id(d => d.id).distance(100).strength(0.3))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('x', d3.forceX(d => {
      if (d.role === 'input') return margin + colWidth * 0.5;
      if (d.role === 'output') return width - margin - colWidth * 0.5;
      return margin + colWidth * 1.5;
    }).strength(0.5))
    .force('y', d3.forceY(height / 2).strength(0.1))
    .force('collision', d3.forceCollide().radius(40));
  
  // Draw links (edges) - curved for better visibility
  const link = g.append('g')
    .selectAll('path')
    .data(linkData)
    .join('path')
    .attr('fill', 'none')
    .attr('stroke', '#6a9ec9')
    .attr('stroke-opacity', 0.7)
    .attr('stroke-width', d => Math.min(4, Math.max(1.5, Math.log(d.weight + 1))))
    .attr('marker-end', 'url(#arrowhead)');
  
  // Draw link labels (weight) - only for significant weights
  const linkLabels = g.append('g')
    .selectAll('text')
    .data(linkData.filter(d => d.weight > 5))
    .join('text')
    .attr('font-size', '9px')
    .attr('fill', '#aaa')
    .attr('text-anchor', 'middle')
    .attr('dy', -5)
    .text(d => d.weight);
  
  // Draw nodes
  const node = g.append('g')
    .selectAll('g')
    .data(nodeData)
    .join('g')
    .call(drag(simulation));
  
  // Node circles with glow effect
  node.append('circle')
    .attr('r', 14)
    .attr('fill', d => roleColors[d.role] || '#4682B4')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'grab')
    .style('filter', 'drop-shadow(0 0 3px rgba(255,255,255,0.3))');
  
  // Node labels - truncate long names
  node.append('text')
    .attr('x', 18)
    .attr('y', 4)
    .attr('font-size', '11px')
    .attr('fill', '#e0e0e0')
    .attr('font-family', 'Segoe UI, sans-serif')
    .text(d => d.name.length > 18 ? d.name.substring(0, 18) + '...' : d.name);
  
  // Tooltip on hover
  node.append('title')
    .text(d => `${d.name}\nRol: ${d.role}\nComplejidad: ${d.complexity}`);
  
  // Update positions on tick - use curved paths
  simulation.on('tick', () => {
    link.attr('d', d => {
      const dx = d.target.x - d.source.x;
      const dy = d.target.y - d.source.y;
      const dr = Math.sqrt(dx * dx + dy * dy) * 0.8; // Curve radius
      return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
    });
    
    linkLabels
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2 - 10);
    
    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });
  
  // Legend
  const legend = svg.append('g')
    .attr('transform', `translate(10, ${height - 70})`);
  
  const legendData = [
    { role: 'input', label: 'Entrada', color: roleColors.input },
    { role: 'processing', label: 'Proceso', color: roleColors.processing },
    { role: 'output', label: 'Salida', color: roleColors.output }
  ];
  
  legendData.forEach((item, i) => {
    const lg = legend.append('g').attr('transform', `translate(0, ${i * 18})`);
    lg.append('circle').attr('r', 6).attr('fill', item.color);
    lg.append('text').attr('x', 12).attr('y', 4).attr('font-size', '10px').attr('fill', '#ccc').text(item.label);
  });
  
  // Drag behavior (sticky)
  function drag(simulation) {
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }
    
    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      // Keep node fixed where dropped (sticky)
    }
    
    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }
  
  // Store data for HTML export
  container._graphData = { nodes: nodeData, edges: linkData, width, height, roleColors };
}

/**
 * Generate standalone HTML file with interactive D3 graph.
 * @param {Object} graphData - {nodes, edges, width, height, roleColors}
 * @param {string} title - Title for the HTML page
 * @returns {string} Complete HTML document
 */
function generateGraphHTML(graphData, title) {
  const { nodes, edges, width, height, roleColors } = graphData;
  
  // Serialize data
  const nodesJSON = JSON.stringify(nodes.map(n => ({
    id: n.id, name: n.name, role: n.role, complexity: n.complexity
  })));
  const edgesJSON = JSON.stringify(edges.map(e => ({
    source: typeof e.source === 'object' ? e.source.id : e.source,
    target: typeof e.target === 'object' ? e.target.id : e.target,
    weight: e.weight
  })));
  
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: 'Segoe UI', sans-serif; 
      background: #1a1a2e; 
      color: #e0e0e0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      padding: 16px 24px;
      background: #161b22;
      border-bottom: 1px solid #30363d;
    }
    h1 { font-size: 18px; font-weight: 500; }
    .subtitle { font-size: 12px; color: #8b949e; margin-top: 4px; }
    #graph-container { 
      flex: 1; 
      display: flex; 
      justify-content: center; 
      align-items: center;
      padding: 20px;
    }
    svg { border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
    .legend { position: fixed; bottom: 20px; left: 20px; background: #161b22; padding: 12px 16px; border-radius: 8px; }
    .legend-item { display: flex; align-items: center; margin: 6px 0; font-size: 12px; }
    .legend-circle { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
    .controls { position: fixed; top: 80px; right: 20px; background: #1e1e2e; padding: 12px; border-radius: 8px; border: 1px solid #333; }
    .controls button { 
      display: block; width: 100%; margin: 4px 0; padding: 8px 12px; 
      background: #3a3a2a; border: 1px solid #d7a538; border-radius: 6px; color: #d7a538; cursor: pointer;
      font-size: 12px;
    }
    .controls button:hover { background: #4a4a3a; }
  </style>
</head>
<body>
  <header>
    <h1>${title}</h1>
    <div class="subtitle">Grafo interactivo de flujo de datos - Generado por NEVEN</div>
  </header>
  <div id="graph-container"></div>
  <div class="legend">
    <div class="legend-item"><div class="legend-circle" style="background:#d7a538"></div>Entrada (Input)</div>
    <div class="legend-item"><div class="legend-circle" style="background:#5a7a9a"></div>Procesamiento</div>
    <div class="legend-item"><div class="legend-circle" style="background:#c9302c"></div>Salida (Output)</div>
  </div>
  <div class="controls">
    <button onclick="resetZoom()">Resetear Vista</button>
    <button onclick="releaseNodes()">Liberar Nodos</button>
  </div>
  <script>
    const nodes = ${nodesJSON};
    const edges = ${edgesJSON};
    const roleColors = { input: '#d7a538', output: '#c9302c', processing: '#5a7a9a', isolated: '#666666' };
    
    const width = Math.max(800, window.innerWidth - 100);
    const height = Math.max(500, window.innerHeight - 150);
    const margin = 80;
    const colWidth = (width - 2 * margin) / 3;
    
    // Group by role
    const inputNodes = nodes.filter(n => n.role === 'input');
    const outputNodes = nodes.filter(n => n.role === 'output');
    const processingNodes = nodes.filter(n => n.role === 'processing' || n.role === 'isolated');
    
    // Initial positions
    nodes.forEach(n => {
      if (n.role === 'input') {
        const idx = inputNodes.indexOf(n);
        n.x = margin + colWidth * 0.5;
        n.y = margin + (idx + 0.5) * (height - 2 * margin) / Math.max(1, inputNodes.length);
      } else if (n.role === 'output') {
        const idx = outputNodes.indexOf(n);
        n.x = width - margin - colWidth * 0.5;
        n.y = margin + (idx + 0.5) * (height - 2 * margin) / Math.max(1, outputNodes.length);
      } else {
        const idx = processingNodes.indexOf(n);
        n.x = margin + colWidth * 1.5;
        n.y = margin + (idx + 0.5) * (height - 2 * margin) / Math.max(1, processingNodes.length);
      }
    });
    
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const links = edges.filter(e => nodeMap.has(e.source) && nodeMap.has(e.target));
    
    const svg = d3.select('#graph-container')
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', '#1e1e2e');
    
    const g = svg.append('g');
    
    const zoomBehavior = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoomBehavior);
    
    svg.append('defs').append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .append('path')
      .attr('d', 'M 0,-5 L 10,0 L 0,5')
      .attr('fill', '#6a9ec9');
    
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(120).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-250))
      .force('x', d3.forceX(d => {
        if (d.role === 'input') return margin + colWidth * 0.5;
        if (d.role === 'output') return width - margin - colWidth * 0.5;
        return margin + colWidth * 1.5;
      }).strength(0.4))
      .force('y', d3.forceY(height / 2).strength(0.05))
      .force('collision', d3.forceCollide().radius(50));
    
    const link = g.append('g')
      .selectAll('path')
      .data(links)
      .join('path')
      .attr('fill', 'none')
      .attr('stroke', '#6a9ec9')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.min(5, Math.max(1.5, Math.log(d.weight + 1))))
      .attr('marker-end', 'url(#arrow)');
    
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(links.filter(d => d.weight > 5))
      .join('text')
      .attr('font-size', '10px')
      .attr('fill', '#aaa')
      .attr('text-anchor', 'middle')
      .text(d => d.weight);
    
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag()
        .on('start', (e) => { if (!e.active) simulation.alphaTarget(0.3).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; })
        .on('drag', (e) => { e.subject.fx = e.x; e.subject.fy = e.y; })
        .on('end', (e) => { if (!e.active) simulation.alphaTarget(0); }));
    
    node.append('circle')
      .attr('r', 16)
      .attr('fill', d => roleColors[d.role] || '#4682B4')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2.5)
      .style('cursor', 'grab')
      .style('filter', 'drop-shadow(0 0 4px rgba(255,255,255,0.3))');
    
    node.append('text')
      .attr('x', 22)
      .attr('y', 5)
      .attr('font-size', '13px')
      .attr('fill', '#e0e0e0')
      .text(d => d.name.length > 20 ? d.name.substring(0, 20) + '...' : d.name);
    
    node.append('title').text(d => d.name + ' (' + d.role + ')');
    
    simulation.on('tick', () => {
      link.attr('d', d => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const dr = Math.sqrt(dx * dx + dy * dy) * 0.7;
        return 'M' + d.source.x + ',' + d.source.y + 'A' + dr + ',' + dr + ' 0 0,1 ' + d.target.x + ',' + d.target.y;
      });
      linkLabel.attr('x', d => (d.source.x + d.target.x) / 2).attr('y', d => (d.source.y + d.target.y) / 2 - 8);
      node.attr('transform', d => 'translate(' + d.x + ',' + d.y + ')');
    });
    
    window.resetZoom = () => svg.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity);
    window.releaseNodes = () => { nodes.forEach(n => { n.fx = null; n.fy = null; }); simulation.alpha(0.5).restart(); };
  </script>
</body>
</html>`;
}

// Expose to global
window.renderWorkbookGraphD3 = renderWorkbookGraphD3;
window.generateGraphHTML = generateGraphHTML;

/**
 * Download the last workbook analysis as a Markdown file.
 */
function downloadWorkbookAnalysisMD() {
  const analysis = window._lastWorkbookAnalysis;
  if (!analysis) {
    showToast('No hay análisis de libro disponible');
    return;
  }
  
  // Generate markdown content
  const md = formatWorkbookAnalysisForAI(analysis);
  
  // Create filename from workbook name
  const safeName = (analysis.workbook_name || 'workbook')
    .replace(/\.[^/.]+$/, '')  // Remove extension
    .replace(/[^a-zA-Z0-9_-]/g, '_');  // Sanitize
  const filename = `analisis_${safeName}_${new Date().toISOString().slice(0,10)}.md`;
  
  // Download
  downloadTextFile(md, filename, 'text/markdown');
  showToast(` Descargado: ${filename}`);
}

/**
 * Download the last sheet analysis as a Markdown file.
 */
function downloadSheetAnalysisMD() {
  const analysis = window._lastSheetAnalysis;
  if (!analysis) {
    showToast('No hay análisis de hoja disponible');
    return;
  }
  
  // Generate markdown content
  const md = formatAnalysisForAI(analysis);
  
  // Create filename from sheet name
  const safeName = (analysis.sheet_name || 'sheet')
    .replace(/[^a-zA-Z0-9_-]/g, '_');
  const filename = `analisis_${safeName}_${new Date().toISOString().slice(0,10)}.md`;
  
  // Download
  downloadTextFile(md, filename, 'text/markdown');
  showToast(` Descargado: ${filename}`);
}

/**
 * Utility: Download text content as a file.
 */
function downloadTextFile(content, filename, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType + ';charset=utf-8' });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  
  // Cleanup
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}

// Expose download functions
window.downloadWorkbookAnalysisMD = downloadWorkbookAnalysisMD;
window.downloadSheetAnalysisMD = downloadSheetAnalysisMD;


// ═══════════════════════════════════════════════════════════════════════════════
// Excel Consultant — Contextual Chips
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Predefined prompts for Excel Consultant mode.
 * Each chip sends a specific question to the AI.
 */
const EXCEL_CONSULTANT_CHIPS = [
  { label: '¿Qué hace esta hoja?', prompt: 'Explica qué hace esta hoja de cálculo. Describe el propósito general, el flujo de datos y las principales operaciones que realiza.' },
  { label: 'Auditar errores', prompt: 'Audita esta hoja en busca de errores potenciales: fórmulas frágiles, referencias hardcodeadas, funciones obsoletas, riesgos de #REF o #N/A.' },
  { label: 'Optimizar fórmulas', prompt: 'Sugiere optimizaciones para las fórmulas de esta hoja: funciones más eficientes, reducción de volatilidad, patrones modernos (BUSCARX, LET, LAMBDA).' },
  { label: 'Documentar', prompt: 'Genera documentación técnica de esta hoja: inputs, outputs, fórmulas clave, dependencias entre celdas y notas importantes para quien la mantenga.' },
  { label: 'Celdas críticas', prompt: 'Identifica las celdas más críticas de esta hoja: inputs principales que afectan muchos cálculos y outputs finales que son el resultado del modelo.' },
  { label: 'Simplificar', prompt: '¿Hay fórmulas demasiado complejas que podrían simplificarse? Muestra ejemplos de fórmulas anidadas y cómo reescribirlas más claramente.' },
];

/**
 * Show the Excel Consultant chips card with contextual prompts.
 * @param {Object} analysis - The sheet analysis result
 */
function showExcelConsultantChips(analysis) {
  const card = document.getElementById('ai-excel-consultant-card');
  const chipsContainer = document.getElementById('ai-excel-chips');
  
  if (!card || !chipsContainer) return;
  
  // Clear previous chips
  chipsContainer.innerHTML = '';
  
  // Create chips (same style as Prompts Guia)
  EXCEL_CONSULTANT_CHIPS.forEach(chip => {
    const btn = document.createElement('button');
    btn.textContent = chip.label;
    btn.title = chip.prompt.substring(0, 100) + '...';
    btn.style.cssText = 
      'background:var(--bg-secondary);' +
      'border:1px solid var(--border);' +
      'color:var(--text-secondary);' +
      'border-radius:12px;' +
      'padding:3px 10px;' +
      'font-size:10px;' +
      'cursor:pointer;' +
      'transition:all 0.15s;';
    
    btn.onmouseover = function() {
      this.style.borderColor = 'var(--accent)';
      this.style.color = 'var(--accent)';
    };
    btn.onmouseout = function() {
      this.style.borderColor = 'var(--border)';
      this.style.color = 'var(--text-secondary)';
    };
    
    btn.addEventListener('click', function() {
      sendExcelConsultantPrompt(chip.prompt);
    });
    
    chipsContainer.appendChild(btn);
  });
  
  // Show the card
  card.style.display = '';
}

/**
 * Send a predefined prompt to the AI chat.
 * @param {string} promptText - The prompt to send
 */
function sendExcelConsultantPrompt(promptText) {
  // Add as user message and call LLM
  if (typeof _aiAddMessage === 'function' && typeof _aiCallLLM === 'function') {
    _aiAddMessage('user', promptText);
    _aiCallLLM();
  } else {
    // Fallback: put in input and let user send
    const input = document.getElementById('ai-input');
    if (input) {
      input.value = promptText;
      input.focus();
    }
  }
}

/**
 * Hide the Excel Consultant chips (call when clearing context).
 */
function hideExcelConsultantChips() {
  const card = document.getElementById('ai-excel-consultant-card');
  if (card) card.style.display = 'none';
}

// Expose to global scope
window.showExcelConsultantChips = showExcelConsultantChips;
window.hideExcelConsultantChips = hideExcelConsultantChips;
window.sendExcelConsultantPrompt = sendExcelConsultantPrompt;

// =============================================================================
// AI Chart Generation System — Multi-Library Support
// =============================================================================

/**
 * Keywords para detectar tipo de gráfico solicitado
 */
const CHART_KEYWORDS = {
  line: /línea|linea|line|tendencia|serie|temporal/i,
  bar: /barra|bar|columna|column/i,
  pie: /pastel|pie|torta|circular|proporción/i,
  scatter: /dispersión|scatter|puntos|correlación/i,
  heatmap: /calor|heat|matriz/i,
  map: /mapa|map|ubicación|geográfico|coordenadas|latitud|longitud/i,
  histogram: /histograma|distribución|frecuencia/i,
  boxplot: /caja|box|bigotes|whisker|outlier/i,
  network: /red|network|grafo|nodos|conexiones/i,
  sankey: /flujo|sankey|flow/i,
  treemap: /árbol|treemap|jerárquico/i,
  radar: /radar|araña|spider/i,
  funnel: /embudo|funnel|conversión/i,
  gauge: /medidor|gauge|velocímetro/i,
  surface: /superficie|3d|tridimensional/i,
  area: /área|area|apilado|stacked/i,
  bubble: /burbuja|bubble/i,
  candlestick: /vela|candlestick|ohlc|bolsa/i
};

const CHART_GENERIC_PATTERN = /gráfico|grafico|gráfica|grafica|chart|visualiza|dibuja|muestra|plot|representa/i;

/**
 * Captura datos para generación de gráficos.
 * Estrategia:
 * 1. Si Office.js está disponible (Excel Add-in), captura la selección directamente
 * 2. Si no, usa datos cargados en DuckDB (fallback)
 * 
 * @returns {Promise<{address, headers, data, columns, rows, types, error?}>}
 */
async function captureSelectedRangeForChart() {
  const apiBase = typeof API !== 'undefined' ? API : API_BASE;
  
  // ═══ Estrategia 1: Usar Office.js si está disponible ═══
  if (typeof Office !== 'undefined' && typeof Excel !== 'undefined') {
    try {
      const result = await Excel.run(async (context) => {
        const selection = context.workbook.getSelectedRange();
        selection.load(['values', 'address', 'columnCount', 'rowCount']);
        await context.sync();

        const values = selection.values;
        if (!values || values.length === 0) {
          return { error: 'No hay datos seleccionados en Excel' };
        }

        // Detectar si primera fila son headers
        const hasHeaders = _detectHeadersFromValues(values[0]);
        const headers = hasHeaders ? values[0] : null;
        const data = hasHeaders ? values.slice(1) : values;

        // Detectar tipos de columnas
        const types = _detectColumnTypesFromData(data, headers ? headers.length : values[0].length);

        return {
          address: selection.address,
          headers: headers,
          data: data,
          columns: selection.columnCount,
          rows: data.length,
          types: types
        };
      });
      
      // Si Office.js funcionó, retornar el resultado
      if (result && !result.error && result.data && result.data.length > 0) {
        return result;
      }
    } catch (e) {
      console.warn('[NEVEN] Office.js no disponible o error:', e.message);
      // Continuar con fallback
    }
  }

  // ═══ Estrategia 2: Fallback a DuckDB ═══
  try {
    const response = await fetch(apiBase + '/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql: 'SELECT * FROM dataset LIMIT 2000', page: 1, page_size: 2000 })
    });
    const result = await response.json();
    
    if (result.status === 'ok' && result.rows && result.rows.length > 0) {
      const headers = result.columns || [];
      const data = result.rows;
      const types = _detectColumnTypesFromData(data, headers.length);
      
      return {
        address: 'DuckDB (Data Studio)',
        headers: headers,
        data: data,
        columns: headers.length,
        rows: data.length,
        types: types
      };
    }
  } catch (e) {
    console.warn('[NEVEN] DuckDB query failed:', e);
  }

  // ═══ Estrategia 3: Fallback al bridge ═══
  try {
    const response = await fetch(apiBase + '/api/bridge/pull?key=default');
    const result = await response.json();
    
    if (result.status === 'ok' && result.data) {
      const bridgeData = result.data;
      const headers = bridgeData.columns || [];
      const rows = bridgeData.rows || [];
      
      if (rows.length > 0) {
        const types = _detectColumnTypesFromData(rows, headers.length);
        return {
          address: 'Excel Bridge',
          headers: headers,
          data: rows,
          columns: headers.length,
          rows: rows.length,
          types: types
        };
      }
    }
  } catch (e) {
    console.warn('[NEVEN] Bridge pull failed:', e);
  }

  // ═══ Sin datos disponibles ═══
  return { 
    error: 'No hay datos disponibles. Selecciona datos en Excel o carga un archivo.' 
  };
}

/**
 * Detecta si la primera fila contiene headers (más strings que números)
 */
function _detectHeadersFromValues(firstRow) {
  if (!firstRow || firstRow.length === 0) return false;
  const strings = firstRow.filter(v => typeof v === 'string' && isNaN(parseFloat(v))).length;
  return strings > firstRow.length / 2;
}

/**
 * Detecta tipos de columnas a partir de datos ya cargados
 */
function _detectColumnTypesFromData(data, numCols) {
  const types = [];
  for (let c = 0; c < numCols; c++) {
    const colValues = data.map(row => row[c]).filter(v => v !== null && v !== undefined && v !== '');
    types.push(_inferColumnType(colValues));
  }
  return types;
}

/**
 * Infiere el tipo de una columna basándose en sus valores
 */
function _inferColumnType(values) {
  if (values.length === 0) return 'text';

  let numericCount = 0;
  let dateCount = 0;
  let geoCount = 0;

  for (const v of values.slice(0, 50)) { // Sample primeros 50
    if (typeof v === 'number') {
      numericCount++;
      // Detectar coordenadas geográficas
      if (v >= -180 && v <= 180) geoCount++;
    } else if (typeof v === 'string') {
      // Intentar parsear como fecha
      const d = new Date(v);
      if (!isNaN(d.getTime()) && v.match(/\d{4}|\d{1,2}\/\d{1,2}/)) {
        dateCount++;
      }
    }
  }

  const total = values.slice(0, 50).length;
  if (numericCount / total > 0.8) {
    // Si parece coordenada geográfica
    if (geoCount / numericCount > 0.8) return 'geo';
    return 'numeric';
  }
  if (dateCount / total > 0.5) return 'date';
  return 'text';
}

/**
 * Detecta si el prompt del usuario solicita un gráfico.
 * @param {string} prompt - Texto del usuario
 * @returns {string|null} - Tipo de gráfico o null si no es solicitud de gráfico
 */
function detectChartIntent(prompt) {
  if (!CHART_GENERIC_PATTERN.test(prompt)) {
    return null;
  }

  for (const [type, regex] of Object.entries(CHART_KEYWORDS)) {
    if (regex.test(prompt)) {
      return type;
    }
  }

  return 'auto'; // Es solicitud de gráfico pero sin tipo específico
}

/**
 * Genera un gráfico usando el endpoint de IA.
 * @param {string} prompt - Solicitud del usuario
 * @param {object} rangeData - Datos capturados con captureSelectedRangeForChart()
 * @returns {Promise<{html, chart_type, library}>}
 */
async function generateChart(prompt, rangeData) {
  if (!rangeData || rangeData.error) {
    throw new Error(rangeData?.error || 'No hay datos para graficar');
  }

  const response = await fetch(API_BASE + '/api/ai/chart', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      range_address: rangeData.address,
      headers: rangeData.headers,
      data: rangeData.data,
      prompt: prompt
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Error ${response.status}: ${errorText}`);
  }

  return await response.json();
}

/**
 * Renderiza un gráfico HTML en el contenedor de preview.
 * @param {string} htmlContent - HTML completo del gráfico
 * @param {string} title - Título para mostrar
 * @param {string} library - Nombre de la librería usada
 */
function renderChartInPreview(htmlContent, title = 'Gráfico generado', library = '') {
  // Buscar o crear contenedor de preview
  let previewContainer = document.getElementById('chart-preview-container');
  if (!previewContainer) {
    previewContainer = document.createElement('div');
    previewContainer.id = 'chart-preview-container';
    previewContainer.style.cssText = `
      margin: 10px 0;
      border: 1px solid #444;
      border-radius: 8px;
      overflow: hidden;
      background: #1e1e1e;
    `;
    // Insertar en el área de respuesta del chat
    const chatArea = document.getElementById('ai-response-area') || 
                     document.getElementById('ai-chat-messages');
    if (chatArea) {
      chatArea.appendChild(previewContainer);
    }
  }

  // Header con título y librería
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 8px 12px;
    background: #2d2d2d;
    border-bottom: 1px solid #444;
    display: flex;
    justify-content: space-between;
    align-items: center;
  `;
  header.innerHTML = `
    <span style="font-weight: 500; color: #e0e0e0;">${title}</span>
    <span style="font-size: 11px; color: #888;">${library}</span>
  `;

  // Iframe sandboxed para el gráfico
  const iframe = document.createElement('iframe');
  iframe.style.cssText = `
    width: 100%;
    height: 400px;
    border: none;
    background: white;
  `;
  iframe.sandbox = 'allow-scripts allow-same-origin';

  // Botones de acción
  const actions = document.createElement('div');
  actions.style.cssText = `
    padding: 8px 12px;
    background: #2d2d2d;
    border-top: 1px solid #444;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  `;

  // Botón: Enviar a Slide
  const btnSlide = _createChartActionButton(' Enviar a Slide', () => {
    sendChartToPresentation(htmlContent, title);
  });

  // Botón: Guardar PNG
  const btnPng = _createChartActionButton(' Guardar PNG', () => {
    _exportChartAsPng(iframe, title);
  });

  // Botón: Copiar HTML
  const btnCopy = _createChartActionButton(' Copiar HTML', () => {
    navigator.clipboard.writeText(htmlContent).then(() => {
      showToast('HTML copiado al portapapeles');
    });
  });

  // Botón: Expandir
  const btnExpand = _createChartActionButton(' Expandir', () => {
    _openChartInNewWindow(htmlContent, title);
  });

  actions.appendChild(btnSlide);
  actions.appendChild(btnPng);
  actions.appendChild(btnCopy);
  actions.appendChild(btnExpand);

  // Limpiar y armar contenedor
  previewContainer.innerHTML = '';
  previewContainer.appendChild(header);
  previewContainer.appendChild(iframe);
  previewContainer.appendChild(actions);

  // Escribir HTML en el iframe
  const doc = iframe.contentDocument || iframe.contentWindow.document;
  doc.open();
  doc.write(htmlContent);
  doc.close();

  // Guardar referencia para uso posterior
  previewContainer._chartHtml = htmlContent;
  previewContainer._chartTitle = title;

  // Scroll al gráfico
  previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Crea un botón de acción para el gráfico
 */
function _createChartActionButton(text, onClick) {
  const btn = document.createElement('button');
  btn.textContent = text;
  btn.style.cssText = `
    background: rgba(100, 180, 255, 0.1);
    border: 1px solid rgba(100, 180, 255, 0.3);
    color: #6af;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
  `;
  btn.onmouseover = function() {
    this.style.background = 'rgba(100, 180, 255, 0.2)';
    this.style.borderColor = 'rgba(100, 180, 255, 0.5)';
  };
  btn.onmouseout = function() {
    this.style.background = 'rgba(100, 180, 255, 0.1)';
    this.style.borderColor = 'rgba(100, 180, 255, 0.3)';
  };
  btn.onclick = onClick;
  return btn;
}

/**
 * Exporta el gráfico como PNG usando html2canvas (si disponible)
 */
async function _exportChartAsPng(iframe, title) {
  try {
    // Intentar usar html2canvas si está disponible
    if (typeof html2canvas === 'function') {
      const canvas = await html2canvas(iframe.contentDocument.body);
      const link = document.createElement('a');
      link.download = `${title.replace(/[^a-z0-9]/gi, '_')}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } else {
      // Fallback: abrir en nueva ventana para captura manual
      showToast('Abre el gráfico y usa captura de pantalla');
      _openChartInNewWindow(iframe.srcdoc || iframe.contentDocument.documentElement.outerHTML, title);
    }
  } catch (e) {
    console.error('[NEVEN] Error exportando PNG:', e);
    showToast('Error al exportar PNG');
  }
}

/**
 * Abre el gráfico en una nueva ventana
 */
function _openChartInNewWindow(htmlContent, title) {
  const win = window.open('', '_blank', 'width=1000,height=700');
  if (win) {
    win.document.write(htmlContent);
    win.document.title = title;
    win.document.close();
  }
}

/**
 * Envía el gráfico al Creador de Presentaciones (Impress.js)
 * @param {string} htmlContent - HTML del gráfico
 * @param {string} title - Título del slide
 */
function sendChartToPresentation(htmlContent, title = 'Gráfico') {
  // Crear objeto de slide
  const slideObject = {
    type: 'chart',
    content: htmlContent,
    title: title,
    timestamp: new Date().toISOString()
  };

  // Intentar enviar al tab de Presentaciones vía postMessage
  window.postMessage({
    action: 'addSlideObject',
    payload: slideObject
  }, '*');

  // Si existe la función global del creador de presentaciones, usarla
  if (typeof window.addChartToPresentation === 'function') {
    window.addChartToPresentation(slideObject);
  }

  // Guardar en localStorage para persistencia
  try {
    const pending = JSON.parse(localStorage.getItem('neven_pending_slides') || '[]');
    pending.push(slideObject);
    localStorage.setItem('neven_pending_slides', JSON.stringify(pending));
  } catch (e) {
    console.warn('[NEVEN] No se pudo guardar en localStorage:', e);
  }

  // Cambiar a la pestaña de Presentaciones si existe
  const presTab = document.querySelector('[data-tab="presentations"]');
  if (presTab) {
    presTab.click();
  }

  showToast(' Gráfico enviado a la presentación');
}

/**
 * Procesa un mensaje del chat para detectar y manejar solicitudes de gráficos.
 * Llama automáticamente cuando se detecta intención de gráfico.
 * 
 * @param {string} userPrompt - Mensaje del usuario
 * @returns {Promise<boolean>} - true si se procesó como gráfico, false si no
 */
async function processChartRequest(userPrompt) {
  const chartIntent = detectChartIntent(userPrompt);
  
  if (!chartIntent) {
    return false; // No es una solicitud de gráfico
  }

  try {
    // Mostrar indicador de carga
    showToast(' Capturando datos y generando gráfico...');

    // Capturar datos seleccionados
    const rangeData = await captureSelectedRangeForChart();
    
    if (rangeData.error) {
      showToast('️ ' + rangeData.error);
      return false;
    }

    if (!rangeData.data || rangeData.data.length === 0) {
      showToast('️ Selecciona un rango de datos primero');
      return false;
    }

    // Generar gráfico
    const result = await generateChart(userPrompt, rangeData);

    if (result.status === 'ok' && result.html) {
      // Renderizar gráfico
      const title = `Gráfico ${result.chart_type || 'generado'}`;
      renderChartInPreview(result.html, title, result.library);
      
      showToast(` Gráfico generado con ${result.library}`);
      return true;
    } else {
      throw new Error(result.error || 'Error desconocido');
    }

  } catch (error) {
    console.error('[NEVEN] Error generando gráfico:', error);
    showToast(' Error: ' + error.message);
    return false;
  }
}

/**
 * Muestra indicador de rango seleccionado para gráficos
 */
function showChartRangeIndicator(rangeData) {
  let indicator = document.getElementById('chart-range-indicator');
  if (!indicator) {
    indicator = document.createElement('div');
    indicator.id = 'chart-range-indicator';
    indicator.style.cssText = `
      padding: 8px 12px;
      background: rgba(100, 200, 100, 0.1);
      border: 1px solid rgba(100, 200, 100, 0.3);
      border-radius: 6px;
      margin: 8px 0;
      font-size: 12px;
      color: #8c8;
    `;
    const chatInput = document.getElementById('ai-input-area');
    if (chatInput) {
      chatInput.parentNode.insertBefore(indicator, chatInput);
    }
  }

  const headers = rangeData.headers ? rangeData.headers.join(', ') : '(sin headers)';
  indicator.innerHTML = `
     <strong>Rango seleccionado:</strong> ${rangeData.address} 
    (${rangeData.rows} filas × ${rangeData.columns} columnas)<br>
    <small>Headers: ${headers}</small>
  `;
}

// Exponer funciones al scope global
window.captureSelectedRangeForChart = captureSelectedRangeForChart;
window.detectChartIntent = detectChartIntent;
window.generateChart = generateChart;
window.renderChartInPreview = renderChartInPreview;
window.sendChartToPresentation = sendChartToPresentation;
window.processChartRequest = processChartRequest;
window.showChartRangeIndicator = showChartRangeIndicator;


// ═══════════════════════════════════════════════════════════════════════════════
// NEVEN Settings Tab — Config Manager UI
// ═══════════════════════════════════════════════════════════════════════════════

// Modelos disponibles por proveedor (se actualizan desde el servidor)
let _aiModels = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  azure: ['gpt-4o', 'gpt-4.1', 'gpt-4-turbo', 'gpt-35-turbo'],
  anthropic: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229'],
  ollama: ['llama3', 'llama3.1', 'mistral', 'codellama']
};

// Puertos default por tipo de DB
let _dbDefaultPorts = {
  postgresql: 5432,
  mysql: 3306,
  sqlserver: 1433,
  sqlite: null,
  duckdb: null
};

// Estado actual de edicion
let _editingAiProfile = null;  // null = nuevo, string = ID existente
let _editingDbConn = null;
let _editingPrompt = null;

// ─── Inicializacion del Tab Settings ─────────────────────────────────────────

function initSettingsTab() {
  console.log('[Settings] initSettingsTab() INICIANDO...');
  // Sub-tabs de settings
  document.querySelectorAll('.settings-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.settingsTab;
      document.querySelectorAll('.settings-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.settingsTab === target);
        t.style.color = t.classList.contains('active') ? 'var(--accent)' : 'var(--text-secondary)';
        t.style.borderBottomColor = t.classList.contains('active') ? 'var(--accent)' : 'transparent';
      });
      document.querySelectorAll('.settings-panel').forEach(p => {
        p.style.display = p.id === 'settings-' + target ? 'block' : 'none';
      });
      // Cargar datos del panel activo
      if (target === 'ai') loadAiProfiles();
      else if (target === 'db') loadDbConnections();
      else if (target === 'prompts') loadPromptsList();
      else if (target === 'ontology') loadOntologyDomains();
      else if (target === 'notebooks') loadNotebooksList();
      else if (target === 'engines') loadEnginesStatus();
    });
  });

  // ── AI Profile handlers ────────────────────────────────────────────────────
  document.getElementById('btn-ai-add')?.addEventListener('click', () => showAiProfileForm(null));
  document.getElementById('btn-ai-cancel')?.addEventListener('click', hideAiProfileForm);
  document.getElementById('btn-ai-save')?.addEventListener('click', saveAiProfile);
  document.getElementById('btn-ai-test')?.addEventListener('click', testAiProfile);
  
  // Toggle password visibility
  document.getElementById('btn-ai-show-key')?.addEventListener('click', () => {
    const inp = document.getElementById('ai-apikey');
    inp.type = inp.type === 'password' ? 'text' : 'password';
  });
  
  // Cambio de proveedor actualiza modelos
  document.getElementById('ai-provider')?.addEventListener('change', (e) => {
    updateAiModels(e.target.value);
    // Mostrar/ocultar campos segun proveedor
    const provider = e.target.value;
    document.getElementById('ai-endpoint-row').style.display = 
      (provider === 'azure' || provider === 'ollama') ? 'block' : 'none';
    document.getElementById('ai-version-row').style.display = 
      provider === 'azure' ? 'block' : 'none';
  });
  
  // Slider temperatura
  document.getElementById('ai-temperature')?.addEventListener('input', (e) => {
    document.getElementById('ai-temp-value').textContent = e.target.value;
  });

  // ── DB Connection handlers ─────────────────────────────────────────────────
  document.getElementById('btn-db-add')?.addEventListener('click', () => showDbConnectionForm(null));
  document.getElementById('btn-db-cancel-settings')?.addEventListener('click', hideDbConnectionForm);
  document.getElementById('btn-db-save-settings')?.addEventListener('click', saveDbConnection);
  document.getElementById('btn-db-test-settings')?.addEventListener('click', testDbConnection);
  
  // Cambio de tipo DB
  document.getElementById('db-conn-type')?.addEventListener('change', (e) => {
    const dbType = e.target.value;
    const isFile = dbType === 'sqlite' || dbType === 'duckdb';
    const isSqlServer = dbType === 'sqlserver';
    
    document.getElementById('db-conn-server-row').style.display = isFile ? 'none' : 'flex';
    document.getElementById('db-conn-auth-row').style.display = isFile ? 'none' : 'flex';
    document.getElementById('db-conn-winauth-row').style.display = isSqlServer ? 'block' : 'none';
    document.getElementById('db-conn-database-label').textContent = isFile ? 'Ruta del Archivo' : 'Base de Datos';
    document.getElementById('db-conn-database').placeholder = isFile ? 'C:/ruta/archivo.db' : 'nombre_db';
    
    // Actualizar puerto default
    if (_dbDefaultPorts[dbType]) {
      document.getElementById('db-conn-port').value = _dbDefaultPorts[dbType];
    }
  });

  // ── Prompts handlers ───────────────────────────────────────────────────────
  document.getElementById('btn-prompt-new')?.addEventListener('click', () => showPromptEditor(null));
  document.getElementById('btn-prompt-cancel')?.addEventListener('click', hidePromptEditor);
  document.getElementById('btn-prompt-save')?.addEventListener('click', savePrompt);
  document.getElementById('btn-prompt-activate')?.addEventListener('click', activatePrompt);

  // ── Ontology / Knowledge Base handlers ─────────────────────────────────────
  document.getElementById('btn-ontology-refresh')?.addEventListener('click', loadOntologyDomains);
  document.getElementById('btn-ontology-browse')?.addEventListener('click', browseOntologyFile);
  document.getElementById('btn-ontology-process')?.addEventListener('click', processOntologyBook);
  document.getElementById('ontology-target-domain')?.addEventListener('change', onOntologyDomainChange);

  // ── Notebooks / Pluto.jl handlers ──────────────────────────────────────────
  document.getElementById('btn-pluto-start')?.addEventListener('click', startPlutoServer);
  document.getElementById('btn-pluto-stop')?.addEventListener('click', stopPlutoServer);
  document.getElementById('btn-notebooks-refresh')?.addEventListener('click', loadNotebooksList);

  // ── Engines / Motores handlers ─────────────────────────────────────────────
  document.getElementById('btn-engines-refresh')?.addEventListener('click', loadEnginesStatus);
  document.getElementById('btn-engines-save')?.addEventListener('click', saveEnginesConfig);
  document.getElementById('toggle-engine-r')?.addEventListener('change', onEngineToggleChange);
  document.getElementById('toggle-engine-julia')?.addEventListener('change', onEngineToggleChange);
  document.getElementById('toggle-engine-python')?.addEventListener('change', onEngineToggleChange);

  // Cargar proveedores/modelos desde servidor
  console.log('[Settings] Llamando loadConfigMetadata()...');
  loadConfigMetadata();
  
  // Cargar perfiles AI al inicio (es el sub-tab activo por defecto)
  console.log('[Settings] Llamando loadAiProfiles()...');
  loadAiProfiles();
  console.log('[Settings] initSettingsTab() COMPLETADO');
}

// ─── Cargar metadata de configuracion ────────────────────────────────────────

async function loadConfigMetadata() {
  try {
    const resp = await fetch(API_BASE + '/api/config/providers');
    if (resp.ok) {
      const data = await resp.json();
      if (data.models) _aiModels = data.models;
    }
  } catch (e) {
    console.log('[Settings] No se pudo cargar metadata de proveedores');
  }
  
  try {
    const resp = await fetch(API_BASE + '/api/config/db-types');
    if (resp.ok) {
      const data = await resp.json();
      if (data.default_ports) _dbDefaultPorts = data.default_ports;
    }
  } catch (e) {
    console.log('[Settings] No se pudo cargar metadata de DB');
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// AI Profiles
// ═══════════════════════════════════════════════════════════════════════════════

async function loadAiProfiles() {
  console.log('[Settings] loadAiProfiles() INICIANDO...');
  const list = document.getElementById('ai-profiles-list');
  console.log('[Settings] ai-profiles-list element:', list);
  if (!list) {
    console.error('[Settings] ERROR: ai-profiles-list NO EXISTE EN DOM');
    return;
  }
  list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">Cargando...</div>';
  
  try {
    console.log('[Settings] Fetch a:', API_BASE + '/api/config/ai-profiles');
    const resp = await fetch(API_BASE + '/api/config/ai-profiles');
    console.log('[Settings] Response status:', resp.status);
    if (!resp.ok) throw new Error('Error ' + resp.status);
    const data = await resp.json();
    
    if (!data.profiles || data.profiles.length === 0) {
      list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">No hay perfiles configurados</div>';
      return;
    }
    
    list.innerHTML = data.profiles.map(p => `
      <div class="ai-profile-item" data-id="${p.id}" style="display:flex;align-items:center;gap:8px;padding:6px 8px;
           background:${p.active ? 'rgba(215,165,56,0.1)' : 'var(--bg-primary)'};
           border:1px solid ${p.active ? 'var(--accent)' : '#333'};border-radius:4px;cursor:pointer">
        <input type="radio" name="ai-profile-active" ${p.active ? 'checked' : ''} 
               style="accent-color:var(--accent)" data-id="${p.id}">
        <div style="flex:1;min-width:0">
          <div style="font-size:11px;font-weight:600;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${p.name}</div>
          <div style="font-size:9px;color:var(--text-secondary)">${p.provider} / ${p.model}</div>
        </div>
        <span style="font-size:8px;color:${p.has_api_key ? '#6c6' : '#f66'}">${p.has_api_key ? 'KEY OK' : 'SIN KEY'}</span>
        <button class="btn-ai-edit" data-id="${p.id}" style="background:none;border:none;color:var(--text-secondary);cursor:pointer;padding:2px" title="Editar"></button>
        <button class="btn-ai-delete" data-id="${p.id}" style="background:none;border:none;color:#f66;cursor:pointer;padding:2px" title="Eliminar"></button>
      </div>
    `).join('');
    
    // Event listeners
    list.querySelectorAll('input[name="ai-profile-active"]').forEach(radio => {
      radio.addEventListener('change', () => activateAiProfile(radio.dataset.id));
    });
    list.querySelectorAll('.btn-ai-edit').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); showAiProfileForm(btn.dataset.id); });
    });
    list.querySelectorAll('.btn-ai-delete').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); deleteAiProfile(btn.dataset.id); });
    });
    list.querySelectorAll('.ai-profile-item').forEach(item => {
      item.addEventListener('click', () => showAiProfileForm(item.dataset.id));
    });
  } catch (e) {
    list.innerHTML = `<div class="msg-error" style="padding:8px;font-size:10px">Error: ${e.message}</div>`;
  }
}

function updateAiModels(provider) {
  const select = document.getElementById('ai-model');
  const models = _aiModels[provider] || [];
  select.innerHTML = models.map(m => `<option value="${m}">${m}</option>`).join('');
}

async function showAiProfileForm(profileId) {
  _editingAiProfile = profileId;
  const form = document.getElementById('ai-profile-form');
  const title = document.getElementById('ai-form-title');
  
  if (profileId) {
    // Cargar perfil existente
    title.textContent = 'Editar Perfil';
    try {
      const resp = await fetch(API_BASE + '/api/config/ai-profiles/' + profileId);
      if (!resp.ok) throw new Error('Perfil no encontrado');
      const data = await resp.json();
      const p = data.profile;
      
      document.getElementById('ai-name').value = p.name || '';
      document.getElementById('ai-provider').value = p.provider || 'openai';
      updateAiModels(p.provider || 'openai');
      document.getElementById('ai-model').value = p.model || '';
      document.getElementById('ai-apikey').value = '';  // No mostrar API key existente
      document.getElementById('ai-apikey').placeholder = p.has_api_key ? '(key guardada - dejar vacio para mantener)' : 'sk-...';
      document.getElementById('ai-endpoint').value = p.endpoint || '';
      document.getElementById('ai-version').value = p.api_version || '2025-01-01-preview';
      document.getElementById('ai-temperature').value = p.temperature || 0.7;
      document.getElementById('ai-temp-value').textContent = p.temperature || 0.7;
      document.getElementById('ai-maxtokens').value = p.max_tokens || 4096;
      
      // Mostrar/ocultar campos segun proveedor
      const provider = p.provider || 'openai';
      document.getElementById('ai-endpoint-row').style.display = 
        (provider === 'azure' || provider === 'ollama') ? 'block' : 'none';
      document.getElementById('ai-version-row').style.display = 
        provider === 'azure' ? 'block' : 'none';
    } catch (e) {
      showToast('Error cargando perfil: ' + e.message);
      return;
    }
  } else {
    // Nuevo perfil
    title.textContent = 'Nuevo Perfil';
    document.getElementById('ai-name').value = '';
    document.getElementById('ai-provider').value = 'openai';
    updateAiModels('openai');
    document.getElementById('ai-apikey').value = '';
    document.getElementById('ai-apikey').placeholder = 'sk-...';
    document.getElementById('ai-endpoint').value = '';
    document.getElementById('ai-version').value = '2025-01-01-preview';
    document.getElementById('ai-temperature').value = 0.7;
    document.getElementById('ai-temp-value').textContent = '0.7';
    document.getElementById('ai-maxtokens').value = 4096;
    document.getElementById('ai-endpoint-row').style.display = 'none';
    document.getElementById('ai-version-row').style.display = 'none';
  }
  
  document.getElementById('ai-test-result').style.display = 'none';
  form.style.display = 'block';
}

function hideAiProfileForm() {
  document.getElementById('ai-profile-form').style.display = 'none';
  _editingAiProfile = null;
}

async function saveAiProfile() {
  const body = {
    name: document.getElementById('ai-name').value.trim() || 'Sin nombre',
    provider: document.getElementById('ai-provider').value,
    model: document.getElementById('ai-model').value,
    endpoint: document.getElementById('ai-endpoint').value.trim() || null,
    api_version: document.getElementById('ai-version').value.trim() || null,
    temperature: parseFloat(document.getElementById('ai-temperature').value),
    max_tokens: parseInt(document.getElementById('ai-maxtokens').value),
  };
  
  const apiKey = document.getElementById('ai-apikey').value.trim();
  if (apiKey) body.api_key = apiKey;
  
  try {
    let url = API_BASE + '/api/config/ai-profiles';
    if (_editingAiProfile) url += '/' + _editingAiProfile;
    
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    if (!resp.ok) throw new Error('Error guardando perfil');
    
    showToast(_editingAiProfile ? 'Perfil actualizado' : 'Perfil creado');
    hideAiProfileForm();
    loadAiProfiles();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

async function testAiProfile() {
  const result = document.getElementById('ai-test-result');
  result.style.display = 'block';
  result.style.background = 'rgba(100,100,100,0.2)';
  result.style.color = 'var(--text-secondary)';
  result.textContent = 'Probando conexion...';
  
  // Si es nuevo perfil, guardar primero
  if (!_editingAiProfile) {
    await saveAiProfile();
    if (!_editingAiProfile) return;  // Fallo el guardado
  }
  
  try {
    const resp = await fetch(API_BASE + '/api/config/ai-profiles/' + _editingAiProfile + '/test', {
      method: 'POST'
    });
    const data = await resp.json();
    
    if (data.success) {
      result.style.background = 'rgba(100,200,100,0.15)';
      result.style.color = '#6c6';
      result.textContent = data.message;
    } else {
      result.style.background = 'rgba(255,100,100,0.15)';
      result.style.color = '#f66';
      result.textContent = data.message;
    }
  } catch (e) {
    result.style.background = 'rgba(255,100,100,0.15)';
    result.style.color = '#f66';
    result.textContent = 'Error: ' + e.message;
  }
}

async function activateAiProfile(profileId) {
  try {
    const resp = await fetch(API_BASE + '/api/config/ai-profiles/' + profileId + '/activate', {
      method: 'POST'
    });
    if (!resp.ok) throw new Error('Error activando perfil');
    showToast('Perfil activado');
    loadAiProfiles();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

async function deleteAiProfile(profileId) {
  if (!confirm('Eliminar este perfil de IA?')) return;
  
  try {
    const resp = await fetch(API_BASE + '/api/config/ai-profiles/' + profileId + '/delete', {
      method: 'POST'
    });
    if (!resp.ok) throw new Error('Error eliminando perfil');
    showToast('Perfil eliminado');
    hideAiProfileForm();
    loadAiProfiles();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DB Connections
// ═══════════════════════════════════════════════════════════════════════════════

async function loadDbConnections() {
  const list = document.getElementById('db-connections-list');
  list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">Cargando...</div>';
  
  try {
    const resp = await fetch(API_BASE + '/api/config/db-connections');
    if (!resp.ok) throw new Error('Error ' + resp.status);
    const data = await resp.json();
    
    if (!data.connections || data.connections.length === 0) {
      list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">No hay conexiones configuradas</div>';
      return;
    }
    
    list.innerHTML = data.connections.map(c => `
      <div class="db-conn-item" data-id="${c.id}" style="display:flex;align-items:center;gap:8px;padding:6px 8px;
           background:${c.active ? 'rgba(215,165,56,0.1)' : 'var(--bg-primary)'};
           border:1px solid ${c.active ? 'var(--accent)' : '#333'};border-radius:4px;cursor:pointer">
        <input type="radio" name="db-conn-active" ${c.active ? 'checked' : ''} 
               style="accent-color:var(--accent)" data-id="${c.id}">
        <div style="flex:1;min-width:0">
          <div style="font-size:11px;font-weight:600;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c.name}</div>
          <div style="font-size:9px;color:var(--text-secondary)">${c.db_type} ${c.host ? '@ ' + c.host : ''}</div>
        </div>
        <button class="btn-db-edit" data-id="${c.id}" style="background:none;border:none;color:var(--text-secondary);cursor:pointer;padding:2px" title="Editar"></button>
        <button class="btn-db-delete" data-id="${c.id}" style="background:none;border:none;color:#f66;cursor:pointer;padding:2px" title="Eliminar"></button>
      </div>
    `).join('');
    
    // Event listeners
    list.querySelectorAll('input[name="db-conn-active"]').forEach(radio => {
      radio.addEventListener('change', () => activateDbConnection(radio.dataset.id));
    });
    list.querySelectorAll('.btn-db-edit').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); showDbConnectionForm(btn.dataset.id); });
    });
    list.querySelectorAll('.btn-db-delete').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); deleteDbConnection(btn.dataset.id); });
    });
    list.querySelectorAll('.db-conn-item').forEach(item => {
      item.addEventListener('click', () => showDbConnectionForm(item.dataset.id));
    });
  } catch (e) {
    list.innerHTML = `<div class="msg-error" style="padding:8px;font-size:10px">Error: ${e.message}</div>`;
  }
}

async function showDbConnectionForm(connId) {
  _editingDbConn = connId;
  const form = document.getElementById('db-connection-form');
  const title = document.getElementById('db-form-title');
  
  if (connId) {
    title.textContent = 'Editar Conexion';
    try {
      const resp = await fetch(API_BASE + '/api/config/db-connections/' + connId);
      if (!resp.ok) throw new Error('Conexion no encontrada');
      const data = await resp.json();
      const c = data.connection;
      
      document.getElementById('db-conn-name').value = c.name || '';
      document.getElementById('db-conn-type').value = c.db_type || 'postgresql';
      document.getElementById('db-conn-host').value = c.host || 'localhost';
      document.getElementById('db-conn-port').value = c.port || _dbDefaultPorts[c.db_type] || 5432;
      document.getElementById('db-conn-database').value = c.database || '';
      document.getElementById('db-conn-user').value = c.username || '';
      document.getElementById('db-conn-password').value = '';
      document.getElementById('db-conn-password').placeholder = c.has_password ? '(guardada)' : '';
      document.getElementById('db-conn-winauth').checked = c.use_windows_auth || false;
      
      // Mostrar/ocultar campos
      const isFile = c.db_type === 'sqlite' || c.db_type === 'duckdb';
      document.getElementById('db-conn-server-row').style.display = isFile ? 'none' : 'flex';
      document.getElementById('db-conn-auth-row').style.display = isFile ? 'none' : 'flex';
      document.getElementById('db-conn-winauth-row').style.display = c.db_type === 'sqlserver' ? 'block' : 'none';
    } catch (e) {
      showToast('Error cargando conexion: ' + e.message);
      return;
    }
  } else {
    title.textContent = 'Nueva Conexion';
    document.getElementById('db-conn-name').value = '';
    document.getElementById('db-conn-type').value = 'postgresql';
    document.getElementById('db-conn-host').value = 'localhost';
    document.getElementById('db-conn-port').value = 5432;
    document.getElementById('db-conn-database').value = '';
    document.getElementById('db-conn-user').value = '';
    document.getElementById('db-conn-password').value = '';
    document.getElementById('db-conn-password').placeholder = '';
    document.getElementById('db-conn-winauth').checked = false;
    document.getElementById('db-conn-server-row').style.display = 'flex';
    document.getElementById('db-conn-auth-row').style.display = 'flex';
    document.getElementById('db-conn-winauth-row').style.display = 'none';
  }
  
  document.getElementById('db-test-result').style.display = 'none';
  form.style.display = 'block';
}

function hideDbConnectionForm() {
  document.getElementById('db-connection-form').style.display = 'none';
  _editingDbConn = null;
}

async function saveDbConnection() {
  const dbType = document.getElementById('db-conn-type').value;
  const body = {
    name: document.getElementById('db-conn-name').value.trim() || 'Sin nombre',
    db_type: dbType,
    database: document.getElementById('db-conn-database').value.trim(),
  };
  
  // Solo incluir campos de servidor si no es file-based
  if (dbType !== 'sqlite' && dbType !== 'duckdb') {
    body.host = document.getElementById('db-conn-host').value.trim();
    body.port = parseInt(document.getElementById('db-conn-port').value) || null;
    body.username = document.getElementById('db-conn-user').value.trim();
    const pwd = document.getElementById('db-conn-password').value;
    if (pwd) body.password = pwd;
    if (dbType === 'sqlserver') {
      body.use_windows_auth = document.getElementById('db-conn-winauth').checked;
    }
  }
  
  try {
    let url = API_BASE + '/api/config/db-connections';
    if (_editingDbConn) url += '/' + _editingDbConn;
    
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    if (!resp.ok) throw new Error('Error guardando conexion');
    
    showToast(_editingDbConn ? 'Conexion actualizada' : 'Conexion creada');
    hideDbConnectionForm();
    loadDbConnections();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

async function testDbConnection() {
  const result = document.getElementById('db-test-result');
  result.style.display = 'block';
  result.style.background = 'rgba(100,100,100,0.2)';
  result.style.color = 'var(--text-secondary)';
  result.textContent = 'Probando conexion...';
  
  if (!_editingDbConn) {
    await saveDbConnection();
    if (!_editingDbConn) return;
  }
  
  try {
    const resp = await fetch(API_BASE + '/api/config/db-connections/' + _editingDbConn + '/test', {
      method: 'POST'
    });
    const data = await resp.json();
    
    if (data.success) {
      result.style.background = 'rgba(100,200,100,0.15)';
      result.style.color = '#6c6';
      result.textContent = data.message;
    } else {
      result.style.background = 'rgba(255,100,100,0.15)';
      result.style.color = '#f66';
      result.textContent = data.message;
    }
  } catch (e) {
    result.style.background = 'rgba(255,100,100,0.15)';
    result.style.color = '#f66';
    result.textContent = 'Error: ' + e.message;
  }
}

async function activateDbConnection(connId) {
  try {
    const resp = await fetch(API_BASE + '/api/config/db-connections/' + connId + '/activate', {
      method: 'POST'
    });
    if (!resp.ok) throw new Error('Error activando conexion');
    showToast('Conexion activada');
    loadDbConnections();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

async function deleteDbConnection(connId) {
  if (!confirm('Eliminar esta conexion de base de datos?')) return;
  
  try {
    const resp = await fetch(API_BASE + '/api/config/db-connections/' + connId + '/delete', {
      method: 'POST'
    });
    if (!resp.ok) throw new Error('Error eliminando conexion');
    showToast('Conexion eliminada');
    hideDbConnectionForm();
    loadDbConnections();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Prompts
// ═══════════════════════════════════════════════════════════════════════════════

async function loadPromptsList() {
  const list = document.getElementById('prompts-list');
  list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">Cargando...</div>';
  
  try {
    const resp = await fetch(API_BASE + '/api/config/prompts');
    if (!resp.ok) throw new Error('Error ' + resp.status);
    const data = await resp.json();
    
    const categories = data.categories || {};
    const catIds = Object.keys(categories);
    
    if (catIds.length === 0) {
      list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">No hay prompts configurados</div>';
      return;
    }
    
    // Renderizar con acordeones como en Ayuda
    list.innerHTML = catIds.map(catId => {
      const cat = categories[catId];
      const prompts = cat.prompts || [];
      if (prompts.length === 0 && catId !== 'custom') return '';
      
      return `
        <details class="prompt-categoria" ${prompts.some(p => p.id === data.active) ? 'open' : ''}>
          <summary style="display:flex;align-items:center;gap:6px;padding:6px 8px;background:var(--bg-secondary);
                         border-radius:4px;cursor:pointer;font-size:11px;font-weight:600;color:var(--text-primary);
                         list-style:none;user-select:none">
            <span style="flex:1">${cat.label}</span>
            <span style="font-size:9px;color:var(--text-muted);background:var(--bg-primary);padding:1px 6px;border-radius:8px">${prompts.length}</span>
          </summary>
          <div style="display:flex;flex-direction:column;gap:2px;padding:4px 0 4px 16px;margin-top:2px">
            ${prompts.length === 0 
              ? '<div style="font-size:9px;color:var(--text-muted);padding:4px 8px">Sin prompts en esta categoria</div>'
              : prompts.map(p => `
                <div class="prompt-item" data-id="${p.id}" data-type="${p.type}" style="display:flex;align-items:center;gap:6px;padding:5px 8px;
                     background:${p.id === data.active ? 'rgba(215,165,56,0.15)' : 'transparent'};
                     border-left:2px solid ${p.id === data.active ? 'var(--accent)' : 'transparent'};
                     border-radius:0 4px 4px 0;cursor:pointer;transition:background 0.15s">
                  <input type="radio" name="prompt-active" ${p.id === data.active ? 'checked' : ''} 
                         style="accent-color:var(--accent);margin:0" data-id="${p.id}">
                  <div style="flex:1;min-width:0">
                    <div style="font-size:10px;color:var(--text-primary)">${p.name}</div>
                  </div>
                  <button class="btn-prompt-edit" data-id="${p.id}" style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:2px;font-size:10px" title="Editar">[edit]</button>
                </div>
              `).join('')}
          </div>
        </details>
      `;
    }).join('');
    
    // Event listeners
    list.querySelectorAll('input[name="prompt-active"]').forEach(radio => {
      radio.addEventListener('change', () => activatePromptById(radio.dataset.id));
    });
    list.querySelectorAll('.btn-prompt-edit').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); showPromptEditor(btn.dataset.id); });
    });
    list.querySelectorAll('.prompt-item').forEach(item => {
      item.addEventListener('click', () => showPromptEditor(item.dataset.id));
    });
  } catch (e) {
    list.innerHTML = `<div class="msg-error" style="padding:8px;font-size:10px">Error: ${e.message}</div>`;
  }
}

async function showPromptEditor(promptId) {
  _editingPrompt = promptId;
  const editor = document.getElementById('prompt-editor');
  const title = document.getElementById('prompt-editor-title');
  const idRow = document.getElementById('prompt-id-row');
  
  // Remover nota anterior si existe
  const oldNote = document.getElementById('prompt-edit-note');
  if (oldNote) oldNote.remove();
  
  if (promptId) {
    title.textContent = 'Editar Prompt';
    idRow.style.display = 'none';  // No se puede cambiar ID de existente
    
    try {
      const resp = await fetch(API_BASE + '/api/config/prompts/' + promptId);
      if (!resp.ok) throw new Error('Prompt no encontrado');
      const data = await resp.json();
      
      document.getElementById('prompt-id').value = promptId;
      document.getElementById('prompt-content').value = data.content || '';
      document.getElementById('prompt-content').readOnly = false;
      document.getElementById('btn-prompt-save').style.display = 'block';
      
      // Mostrar nota informativa para prompts del sistema
      if (data.type === 'system') {
        const note = document.createElement('div');
        note.id = 'prompt-edit-note';
        note.style.cssText = 'font-size:9px;color:var(--accent);background:rgba(215,165,56,0.1);padding:6px 8px;border-radius:4px;margin-bottom:8px;border:1px solid rgba(215,165,56,0.3)';
        note.innerHTML = 'Nota: Se creara un backup automatico antes de guardar cambios.';
        editor.querySelector('.card-title').after(note);
      }
    } catch (e) {
      showToast('Error cargando prompt: ' + e.message);
      return;
    }
  } else {
    title.textContent = 'Nuevo Prompt';
    idRow.style.display = 'block';
    document.getElementById('prompt-id').value = '';
    document.getElementById('prompt-content').value = '';
    document.getElementById('prompt-content').readOnly = false;
    document.getElementById('btn-prompt-save').style.display = 'block';
  }
  
  editor.style.display = 'block';
}

function hidePromptEditor() {
  document.getElementById('prompt-editor').style.display = 'none';
  _editingPrompt = null;
}

async function savePrompt() {
  const id = _editingPrompt || document.getElementById('prompt-id').value.trim();
  const content = document.getElementById('prompt-content').value;
  
  if (!id) {
    showToast('ID de prompt requerido');
    return;
  }
  
  try {
    const resp = await fetch(API_BASE + '/api/config/prompts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, content })
    });
    
    if (!resp.ok) throw new Error('Error guardando prompt');
    
    showToast('Prompt guardado');
    hidePromptEditor();
    loadPromptsList();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

async function activatePrompt() {
  const id = _editingPrompt || document.getElementById('prompt-id').value.trim();
  if (!id) return;
  await activatePromptById(id);
}

async function activatePromptById(promptId) {
  try {
    const resp = await fetch(API_BASE + '/api/config/prompts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: promptId, content: '', set_active: true })
    });
    if (!resp.ok) throw new Error('Error activando prompt');
    showToast('Prompt activado');
    loadPromptsList();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ONTOLOGY / KNOWLEDGE BASE FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

let _selectedOntologyDomain = null;

async function loadOntologyDomains() {
  const list = document.getElementById('ontology-domains-list');
  const select = document.getElementById('ontology-target-domain');
  
  list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">Cargando dominios...</div>';
  
  try {
    const resp = await fetch(API_BASE + '/api/ontology/domains');
    if (!resp.ok) throw new Error('Error cargando dominios');
    const data = await resp.json();
    
    if (!data.domains || data.domains.length === 0) {
      list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">No hay dominios configurados</div>';
      return;
    }
    
    // Renderizar lista de dominios
    list.innerHTML = data.domains.map(d => `
      <div class="ontology-domain-item" data-domain="${d.id}" 
           style="display:flex;justify-content:space-between;align-items:center;padding:6px 8px;
                  background:var(--bg-tertiary);border-radius:4px;cursor:pointer;
                  border:1px solid ${_selectedOntologyDomain === d.id ? 'var(--accent)' : 'transparent'}">
        <div style="display:flex;flex-direction:column;gap:2px">
          <span style="font-size:11px;font-weight:600;color:var(--text-primary)">${d.id}</span>
          <span style="font-size:9px;color:var(--text-muted)">${d.entity_count || 0} entidades</span>
        </div>
        <span style="font-size:10px;color:var(--accent)">${d.book_count || 0} libros</span>
      </div>
    `).join('');
    
    // Event listeners para seleccionar dominio
    list.querySelectorAll('.ontology-domain-item').forEach(item => {
      item.addEventListener('click', () => {
        _selectedOntologyDomain = item.dataset.domain;
        // Actualizar visual
        list.querySelectorAll('.ontology-domain-item').forEach(i => {
          i.style.borderColor = i.dataset.domain === _selectedOntologyDomain ? 'var(--accent)' : 'transparent';
        });
        // Cargar libros del dominio
        loadOntologyBooks();
      });
    });
    
    // Actualizar dropdown de dominios (incluyendo opción para crear nuevo)
    select.innerHTML = '<option value="">Seleccionar dominio...</option>' + 
      data.domains.map(d => `<option value="${d.id}">${d.id}</option>`).join('') +
      '<option value="__new__" style="font-style:italic;color:var(--accent)">+ Crear nuevo dominio...</option>';
    
    // Si hay dominio seleccionado, seleccionarlo en dropdown
    if (_selectedOntologyDomain && _selectedOntologyDomain !== '__new__') {
      select.value = _selectedOntologyDomain;
    }
    
  } catch (e) {
    console.error('[Ontology] Error:', e);
    list.innerHTML = `<div class="msg-error" style="padding:8px;font-size:10px">Error: ${e.message}</div>`;
  }
}

function onOntologyDomainChange() {
  const select = document.getElementById('ontology-target-domain');
  const newDomainRow = document.getElementById('ontology-new-domain-row');
  const newDomainInput = document.getElementById('ontology-new-domain-name');
  
  if (select.value === '__new__') {
    // Mostrar campo para nuevo dominio
    newDomainRow.style.display = 'block';
    newDomainInput.focus();
    // Limpiar selección de dominio existente
    _selectedOntologyDomain = null;
  } else {
    // Ocultar campo de nuevo dominio
    newDomainRow.style.display = 'none';
    newDomainInput.value = '';
    // Cargar libros del dominio seleccionado
    loadOntologyBooks();
  }
}

async function loadOntologyBooks() {
  const list = document.getElementById('ontology-books-list');
  const select = document.getElementById('ontology-target-domain');
  
  // Sincronizar dominio seleccionado con dropdown si cambió (ignorar __new__)
  if (select.value && select.value !== '__new__' && select.value !== _selectedOntologyDomain) {
    _selectedOntologyDomain = select.value;
  }
  
  if (!_selectedOntologyDomain || _selectedOntologyDomain === '__new__') {
    list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">Selecciona un dominio para ver libros</div>';
    return;
  }
  
  list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">Cargando libros...</div>';
  
  try {
    const resp = await fetch(API_BASE + `/api/ontology/books?domain=${encodeURIComponent(_selectedOntologyDomain)}`);
    if (!resp.ok) throw new Error('Error cargando libros');
    const data = await resp.json();
    
    if (!data.books || data.books.length === 0) {
      list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">No hay libros procesados en este dominio</div>';
      return;
    }
    
    // Renderizar lista de libros
    list.innerHTML = data.books.map(b => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 8px;
                  background:var(--bg-tertiary);border-radius:4px;font-size:10px">
        <div style="display:flex;flex-direction:column;gap:1px;overflow:hidden">
          <span style="font-weight:600;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis" 
                title="${b.filename}">${b.filename}</span>
          <span style="color:var(--text-muted)">${b.pages || '?'} págs · ${b.entities || 0} entidades</span>
        </div>
        <span style="color:var(--text-muted);flex-shrink:0">${b.processed_date || ''}</span>
      </div>
    `).join('');
    
  } catch (e) {
    console.error('[Ontology] Error:', e);
    list.innerHTML = `<div class="msg-error" style="padding:8px;font-size:10px">Error: ${e.message}</div>`;
  }
}

async function browseOntologyFile() {
  // Usar Office.js para abrir diálogo de archivo si está disponible
  // De lo contrario, mostrar mensaje indicando que debe escribir la ruta
  const input = document.getElementById('ontology-file-path');
  
  if (window._officeReady && Office.context.ui && Office.context.ui.displayDialogAsync) {
    // No hay API nativa de file picker en Office.js - mostrar instrucción
    showToast('Escribe la ruta completa del archivo PDF');
    input.focus();
  } else {
    // Fuera de Office, intentar usar input file hidden
    let fileInput = document.getElementById('_ontology-file-input');
    if (!fileInput) {
      fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.id = '_ontology-file-input';
      fileInput.accept = '.pdf';
      fileInput.style.display = 'none';
      fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          // En browser, no podemos obtener la ruta real, solo el nombre
          input.value = e.target.files[0].name;
          showToast('Nota: En browser solo se muestra el nombre. Escribe la ruta completa.');
        }
      });
      document.body.appendChild(fileInput);
    }
    fileInput.click();
  }
}

async function processOntologyBook() {
  const filePath = document.getElementById('ontology-file-path').value.trim();
  let domain = document.getElementById('ontology-target-domain').value;
  const newDomainName = document.getElementById('ontology-new-domain-name').value.trim();
  const maxPages = document.getElementById('ontology-max-pages').value;
  const chunkSize = document.getElementById('ontology-chunk-size').value || 4000;
  
  // Si es nuevo dominio, usar el nombre ingresado
  if (domain === '__new__') {
    if (!newDomainName) {
      showToast('Ingresa un nombre para el nuevo dominio');
      document.getElementById('ontology-new-domain-name').focus();
      return;
    }
    // Validar formato: solo letras, números y guiones bajos
    if (!/^[a-z][a-z0-9_]*$/.test(newDomainName)) {
      showToast('El nombre debe empezar con letra minúscula y solo contener letras, números y guiones bajos');
      return;
    }
    domain = newDomainName;
  }
  
  // Validaciones
  if (!filePath) {
    showToast('Selecciona un archivo PDF');
    return;
  }
  if (!domain) {
    showToast('Selecciona un dominio destino');
    return;
  }
  if (!filePath.toLowerCase().endsWith('.pdf')) {
    showToast('El archivo debe ser un PDF');
    return;
  }
  
  // Mostrar progreso
  const progressDiv = document.getElementById('ontology-progress');
  const progressBar = document.getElementById('ontology-progress-bar');
  const progressText = document.getElementById('ontology-progress-text');
  const progressPercent = document.getElementById('ontology-progress-percent');
  const resultDiv = document.getElementById('ontology-result');
  const processBtn = document.getElementById('btn-ontology-process');
  
  progressDiv.style.display = 'block';
  resultDiv.style.display = 'none';
  processBtn.disabled = true;
  processBtn.textContent = 'Procesando...';
  
  progressText.textContent = 'Iniciando extracción...';
  progressBar.style.width = '10%';
  progressPercent.textContent = '10%';
  
  try {
    const body = {
      file_path: filePath,
      domain: domain
    };
    if (maxPages) body.max_pages = parseInt(maxPages);
    if (chunkSize) body.chunk_size = parseInt(chunkSize);
    
    progressText.textContent = 'Extrayendo texto del PDF...';
    progressBar.style.width = '30%';
    progressPercent.textContent = '30%';
    
    const resp = await fetch(API_BASE + '/api/ontology/process-book', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    progressText.textContent = 'Procesando con LLM...';
    progressBar.style.width = '70%';
    progressPercent.textContent = '70%';
    
    const data = await resp.json();
    
    if (!resp.ok) {
      throw new Error(data.error || 'Error procesando libro');
    }
    
    progressBar.style.width = '100%';
    progressPercent.textContent = '100%';
    progressText.textContent = '¡Completado!';
    
    // Mostrar resultado
    resultDiv.style.display = 'block';
    resultDiv.style.background = 'var(--success-bg, #1a3320)';
    resultDiv.style.color = 'var(--success-text, #4ade80)';
    resultDiv.innerHTML = `
      <strong>✓ Libro procesado exitosamente</strong><br>
      <span style="font-size:9px;color:var(--text-muted)">
        ${data.pages_processed || '?'} páginas · 
        ${data.entities_added || 0} entidades extraídas · 
        ${data.relations_added || 0} relaciones
      </span>
    `;
    
    // Limpiar formulario
    document.getElementById('ontology-file-path').value = '';
    
    // Recargar dominios y libros
    await loadOntologyDomains();
    _selectedOntologyDomain = domain;
    await loadOntologyBooks();
    
    showToast('Libro procesado: ' + (data.entities_added || 0) + ' entidades añadidas');
    
  } catch (e) {
    console.error('[Ontology] Error procesando:', e);
    
    resultDiv.style.display = 'block';
    resultDiv.style.background = 'var(--error-bg, #3d1f1f)';
    resultDiv.style.color = 'var(--error-text, #f87171)';
    resultDiv.innerHTML = `<strong>✗ Error:</strong> ${e.message}`;
    
    showToast('Error: ' + e.message);
    
  } finally {
    processBtn.disabled = false;
    processBtn.textContent = 'Procesar Libro';
    
    // Ocultar progreso después de un momento
    setTimeout(() => {
      progressDiv.style.display = 'none';
      progressBar.style.width = '0%';
    }, 2000);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Notebooks / Pluto.jl
// ═══════════════════════════════════════════════════════════════════════════════

async function loadNotebooksList() {
  const list = document.getElementById('notebooks-list');
  if (!list) return;
  
  list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">Cargando notebooks...</div>';
  
  try {
    const resp = await fetch(API_BASE + '/api/notebooks/list');
    if (!resp.ok) throw new Error('Error ' + resp.status);
    const data = await resp.json();
    
    if (!data.notebooks || data.notebooks.length === 0) {
      list.innerHTML = '<div class="msg-info" style="padding:8px;font-size:10px">No hay notebooks en C:\\NEVEN\\notebooks\\</div>';
      return;
    }
    
    list.innerHTML = data.notebooks.map(nb => `
      <div class="notebook-item" data-path="${nb.path}" style="display:flex;align-items:center;gap:8px;padding:6px 8px;
           background:var(--bg-primary);border:1px solid #333;border-radius:4px;cursor:pointer;transition:border-color 0.15s"
           onmouseover="this.style.borderColor='var(--accent)'" onmouseout="this.style.borderColor='#333'">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
        <div style="flex:1;min-width:0">
          <div style="font-size:11px;font-weight:600;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${nb.name}</div>
          <div style="font-size:9px;color:var(--text-secondary)">${nb.size || ''}</div>
        </div>
        <button class="btn-notebook-open" data-path="${nb.path}" style="background:var(--accent);color:#000;border:none;border-radius:3px;padding:3px 8px;font-size:9px;cursor:pointer">Abrir</button>
      </div>
    `).join('');
    
    // Event listeners para abrir notebooks
    list.querySelectorAll('.btn-notebook-open').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        openNotebook(btn.dataset.path);
      });
    });
    list.querySelectorAll('.notebook-item').forEach(item => {
      item.addEventListener('click', () => openNotebook(item.dataset.path));
    });
    
  } catch (e) {
    list.innerHTML = `<div class="msg-error" style="padding:8px;font-size:10px">Error: ${e.message}</div>`;
  }
  
  // También actualizar estado de Pluto
  checkPlutoStatus();
}

async function checkPlutoStatus() {
  const indicator = document.getElementById('pluto-status-indicator');
  const text = document.getElementById('pluto-status-text');
  if (!indicator || !text) return;
  
  try {
    const resp = await fetch(API_BASE + '/api/pluto/status');
    const data = await resp.json();
    
    if (data.running) {
      indicator.style.background = '#4ade80';
      indicator.title = 'Pluto corriendo';
      text.textContent = 'Corriendo en puerto ' + (data.port || '1234');
    } else {
      indicator.style.background = '#666';
      indicator.title = 'Pluto detenido';
      text.textContent = 'Detenido';
    }
  } catch (e) {
    indicator.style.background = '#f66';
    indicator.title = 'Error verificando';
    text.textContent = 'Error';
  }
}

async function startPlutoServer() {
  const msgDiv = document.getElementById('pluto-message');
  const startBtn = document.getElementById('btn-pluto-start');
  
  startBtn.disabled = true;
  startBtn.textContent = 'Iniciando...';
  msgDiv.style.display = 'block';
  msgDiv.style.background = 'var(--info-bg, #1e3a5f)';
  msgDiv.style.color = 'var(--info-text, #60a5fa)';
  msgDiv.textContent = 'Iniciando servidor Pluto.jl...';
  
  try {
    const resp = await fetch(API_BASE + '/api/pluto/start', { method: 'POST' });
    const data = await resp.json();
    
    if (resp.ok && data.success) {
      msgDiv.style.background = 'var(--success-bg, #1a3320)';
      msgDiv.style.color = 'var(--success-text, #4ade80)';
      msgDiv.textContent = '✓ Pluto iniciado en puerto ' + (data.port || '1234');
      showToast('Pluto.jl iniciado');
    } else {
      throw new Error(data.error || 'Error al iniciar');
    }
    
    checkPlutoStatus();
    
  } catch (e) {
    msgDiv.style.background = 'var(--error-bg, #3d1f1f)';
    msgDiv.style.color = 'var(--error-text, #f87171)';
    msgDiv.textContent = '✗ ' + e.message;
  } finally {
    startBtn.disabled = false;
    startBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg> Iniciar Pluto';
    
    setTimeout(() => { msgDiv.style.display = 'none'; }, 5000);
  }
}

async function stopPlutoServer() {
  const msgDiv = document.getElementById('pluto-message');
  const stopBtn = document.getElementById('btn-pluto-stop');
  
  stopBtn.disabled = true;
  stopBtn.textContent = 'Deteniendo...';
  
  try {
    const resp = await fetch(API_BASE + '/api/pluto/stop', { method: 'POST' });
    const data = await resp.json();
    
    if (resp.ok) {
      msgDiv.style.display = 'block';
      msgDiv.style.background = 'var(--success-bg, #1a3320)';
      msgDiv.style.color = 'var(--success-text, #4ade80)';
      msgDiv.textContent = '✓ Pluto detenido';
      showToast('Pluto.jl detenido');
    } else {
      throw new Error(data.error || 'Error al detener');
    }
    
    checkPlutoStatus();
    
  } catch (e) {
    msgDiv.style.display = 'block';
    msgDiv.style.background = 'var(--error-bg, #3d1f1f)';
    msgDiv.style.color = 'var(--error-text, #f87171)';
    msgDiv.textContent = '✗ ' + e.message;
  } finally {
    stopBtn.disabled = false;
    stopBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12"/></svg> Detener';
    
    setTimeout(() => { msgDiv.style.display = 'none'; }, 3000);
  }
}

async function openNotebook(path) {
  showToast('Abriendo notebook...');
  
  try {
    const resp = await fetch(API_BASE + '/api/pluto/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: path })
    });
    const data = await resp.json();
    
    if (resp.ok && data.url) {
      // Abrir en nueva ventana/pestaña
      window.open(data.url, '_blank');
    } else {
      throw new Error(data.error || 'Error abriendo notebook');
    }
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Engines / Motores de Lenguaje
// ═══════════════════════════════════════════════════════════════════════════════

async function loadEnginesStatus() {
  const engines = ['r', 'julia', 'python'];
  
  for (const eng of engines) {
    const indicator = document.getElementById('engine-' + eng + '-indicator');
    const version = document.getElementById('engine-' + eng + '-version');
    const status = document.getElementById('engine-' + eng + '-status');
    
    if (!indicator) continue;
    
    indicator.style.background = '#666';
    status.textContent = 'Verificando...';
  }
  
  try {
    const resp = await fetch(API_BASE + '/api/engines/status');
    if (!resp.ok) throw new Error('Error ' + resp.status);
    const data = await resp.json();
    
    for (const eng of engines) {
      const indicator = document.getElementById('engine-' + eng + '-indicator');
      const version = document.getElementById('engine-' + eng + '-version');
      const status = document.getElementById('engine-' + eng + '-status');
      const toggle = document.getElementById('toggle-engine-' + eng);
      
      if (!indicator) continue;
      
      const engData = data[eng] || {};
      
      if (engData.connected) {
        indicator.style.background = '#4ade80';
        indicator.title = 'Conectado';
        status.textContent = 'Conectado';
        version.textContent = engData.version || '—';
      } else if (engData.enabled === false) {
        indicator.style.background = '#888';
        indicator.title = 'Deshabilitado';
        status.textContent = 'Deshabilitado';
        version.textContent = '—';
      } else {
        indicator.style.background = '#f66';
        indicator.title = 'Desconectado';
        status.textContent = 'Desconectado';
        version.textContent = '—';
      }
      
      // Actualizar toggles según config
      if (toggle && engData.enabled !== undefined) {
        toggle.checked = engData.enabled;
      }
    }
    
  } catch (e) {
    console.error('[Engines] Error cargando estado:', e);
    for (const eng of engines) {
      const status = document.getElementById('engine-' + eng + '-status');
      if (status) status.textContent = 'Error';
    }
  }
}

function onEngineToggleChange(e) {
  // Solo marcar que hay cambios pendientes
  const saveBtn = document.getElementById('btn-engines-save');
  if (saveBtn) {
    saveBtn.style.background = 'var(--accent)';
    saveBtn.textContent = 'Guardar Configuración *';
  }
}

async function saveEnginesConfig() {
  const resultDiv = document.getElementById('engines-save-result');
  const saveBtn = document.getElementById('btn-engines-save');
  
  const config = {
    r: document.getElementById('toggle-engine-r')?.checked ?? true,
    julia: document.getElementById('toggle-engine-julia')?.checked ?? true,
    python: document.getElementById('toggle-engine-python')?.checked ?? true
  };
  
  saveBtn.disabled = true;
  saveBtn.textContent = 'Guardando...';
  
  try {
    const resp = await fetch(API_BASE + '/api/engines/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    const data = await resp.json();
    
    if (resp.ok) {
      resultDiv.style.display = 'block';
      resultDiv.style.background = 'var(--success-bg, #1a3320)';
      resultDiv.style.color = 'var(--success-text, #4ade80)';
      resultDiv.textContent = '✓ Configuración guardada. Los cambios se aplicarán al reiniciar Excel.';
      
      saveBtn.style.background = '';
      saveBtn.textContent = 'Guardar Configuración';
      
      showToast('Configuración de motores guardada');
    } else {
      throw new Error(data.error || 'Error guardando');
    }
    
  } catch (e) {
    resultDiv.style.display = 'block';
    resultDiv.style.background = 'var(--error-bg, #3d1f1f)';
    resultDiv.style.color = 'var(--error-text, #f87171)';
    resultDiv.textContent = '✗ ' + e.message;
  } finally {
    saveBtn.disabled = false;
    
    setTimeout(() => { resultDiv.style.display = 'none'; }, 5000);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Tab Ayuda - Handlers
// ═══════════════════════════════════════════════════════════════════════════════

function initAyudaTab() {
  // Botón Documentación - abrir visor embebido
  document.getElementById('btn-ayuda-docs')?.addEventListener('click', () => {
    const container = document.getElementById('docs-viewer-container');
    const iframe = document.getElementById('docs-viewer-iframe');
    if (container && iframe) {
      // Cargar documentación en iframe
      iframe.src = API_BASE + '/docs/neven-docs.html?t=' + Date.now();
      container.style.display = 'flex';
    }
  });
  
  // Botón cerrar visor de documentación
  document.getElementById('btn-docs-close')?.addEventListener('click', () => {
    const container = document.getElementById('docs-viewer-container');
    const iframe = document.getElementById('docs-viewer-iframe');
    if (container) {
      container.style.display = 'none';
      if (iframe) iframe.src = 'about:blank'; // Liberar recursos
    }
  });
  
  // Botón abrir en navegador externo
  document.getElementById('btn-docs-external')?.addEventListener('click', () => {
    window.open(API_BASE + '/docs/neven-docs.html', '_blank');
  });
  
  // Botón Videos
  document.getElementById('btn-ayuda-videos')?.addEventListener('click', () => {
    showToast('Videos tutoriales próximamente disponibles');
    // TODO: Implementar cuando estén disponibles
  });
}

// Inicializar handlers de Ayuda cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAyudaTab);
} else {
  initAyudaTab();
}

// ─── Inicializar Settings al cargar ──────────────────────────────────────────

console.log('[Settings] Configurando inicializacion...');
console.log('[Settings] document.readyState:', document.readyState);

// Llamar initSettingsTab cuando el DOM esté listo
function _initSettingsWhenReady() {
  console.log('[Settings] _initSettingsWhenReady llamado');
  if (document.getElementById('ai-profiles-list')) {
    console.log('[Settings] Elemento encontrado, llamando initSettingsTab');
    initSettingsTab();
  } else {
    console.log('[Settings] Elemento NO encontrado, reintentando en 200ms');
    setTimeout(_initSettingsWhenReady, 200);
  }
}

if (document.readyState === 'loading') {
  console.log('[Settings] DOM loading, registrando DOMContentLoaded');
  document.addEventListener('DOMContentLoaded', _initSettingsWhenReady);
} else {
  console.log('[Settings] DOM ya listo, llamando _initSettingsWhenReady');
  _initSettingsWhenReady();
}
