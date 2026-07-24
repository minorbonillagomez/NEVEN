// ═══════════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Task Pane JavaScript (Office.js + API Client)
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = window.location.protocol === 'file:' ? 'http://localhost:5555' : window.location.origin;
const CHUNK_SIZE = 50000;

let loadedData = null;      // { columns: [], types: {}, rows: [] }
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

  // SQL: Ctrl+Enter shortcut
  document.getElementById('sql-input').addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); runSQL(); }
  });

  // GROUP BY dropdowns — auto-execute on change
  ['grp-col', 'grp-metric', 'grp-val'].forEach(id => {
    document.getElementById(id).addEventListener('change', executeGroupBy);
  });

  // Viewer buttons
  document.querySelectorAll('[data-viewer]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('viewer-frame').src = API_BASE + '/viewers/' + btn.dataset.viewer;
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
  info.innerHTML = '<span class="spinner"></span> Cargando con DuckDB...';
  try {
    const result = await apiCall('/api/load_file', { path: path });
    info.textContent = `${result.rows_loaded.toLocaleString()} filas × ${result.columns.length} cols cargadas`;
    loadedData = { columns: result.columns, types: result.types, rows: [] };
    populateGroupByControls(result.columns, result.types);
    document.getElementById('groupby-card').style.display = 'block';
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
