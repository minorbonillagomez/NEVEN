// =============================================================================
// NEVEN Data Lab — datalab.js
// Módulo JavaScript para la UI del Data Lab (pestaña en taskpane.html)
// Vanilla JS — sin dependencias externas
// =============================================================================

// Task 8.1 — Estado global y constante de API
var _DL_API = window.location.origin;

var _dlState = {
  catalog:        null,   // Catálogo recibido del servidor {lang:{family:[card,...]}}
  selectedCard:   null,   // FunctionCard seleccionada actualmente
  columnRoles:    {},     // {roleKey: [colName, ...]}
  parameters:     {},     // {paramName: value}
  datasetColumns: [],     // [{name, type}] columnas del dataset activo
  language:       'r',    // Idioma seleccionado para la ejecución
  pendingColumn:  null    // {name, type} — columna clickeada pendiente de asignar
};

// =============================================================================
// Task 8.2 — initDataLab
// =============================================================================
function initDataLab() {
  var retryBtn = document.getElementById('dl-retry-catalog');
  if (retryBtn) {
    retryBtn.addEventListener('click', function onRetryClick() {
      loadCatalog();
    });
  }

  var familySelect = document.getElementById('dl-family-select');
  if (familySelect) {
    familySelect.addEventListener('change', function onFamilySelectChange() {
      onFamilyChange();
    });
  }

  var runBtn = document.getElementById('dl-run-btn');
  if (runBtn) {
    runBtn.addEventListener('click', function onRunBtnClick() {
      runAnalysis();
    });
  }

  loadCatalog();
}

// =============================================================================
// Task 8.3 — onDataLabTabActivated
// =============================================================================
async function onDataLabTabActivated() {
  await introspectDataset();
  // Load catalog only if not yet loaded; re-render column panel if a card is selected
  if (_dlState.catalog === null) {
    await loadCatalog();
  } else if (_dlState.selectedCard) {
    // Re-render column panel to reflect any dataset changes (e.g. after Wooldridge load)
    renderColumnPanel(_dlState.selectedCard);
  }
}

// =============================================================================
// Task 8.4 — loadCatalog
// =============================================================================
async function loadCatalog() {
  var spinner = document.getElementById('dl-catalog-spinner');
  var errorBox = document.getElementById('dl-catalog-error');
  var retryBtn = document.getElementById('dl-retry-catalog');

  if (spinner)  spinner.style.display  = 'block';
  if (errorBox) errorBox.style.display = 'none';
  if (retryBtn) retryBtn.style.display = 'none';

  try {
    var response = await fetch(_DL_API + '/api/datalab/catalog');
    if (!response.ok) {
      throw new Error('HTTP ' + response.status + ': ' + response.statusText);
    }
    var data = await response.json();
    _dlState.catalog = data.catalog;
    renderFamilyDropdown(data.catalog);
  } catch (err) {
    if (errorBox) {
      errorBox.textContent = 'Error al cargar el catálogo: ' + err.message;
      errorBox.style.display = 'block';
    }
    if (retryBtn) retryBtn.style.display = 'inline-block';
  } finally {
    if (spinner) spinner.style.display = 'none';
  }
}

// =============================================================================
// Task 8.5 — renderFamilyDropdown
// =============================================================================
function renderFamilyDropdown(catalog) {
  var select = document.getElementById('dl-family-select');
  if (!select) return;

  select.innerHTML = '<option value="">-- Seleccione una familia --</option>';

  // Deduplicate families across all languages
  var seen = {};
  var langEntries = Object.values(catalog);
  for (var li = 0; li < langEntries.length; li++) {
    var lang = langEntries[li];
    var familyEntries = Object.entries(lang);
    for (var fi = 0; fi < familyEntries.length; fi++) {
      var familyKey   = familyEntries[fi][0];
      var familyCards = familyEntries[fi][1];
      if (!seen[familyKey] && familyCards && familyCards.length > 0) {
        seen[familyKey] = true;
        var label = familyCards[0].family_label || familyKey;
        var opt = document.createElement('option');
        opt.value       = familyKey;
        opt.textContent = label;
        select.appendChild(opt);
      }
    }
  }

  select.disabled = false;
}

// =============================================================================
// Task 8.6 — onFamilyChange
// =============================================================================
function onFamilyChange() {
  clearFunctionSelection();

  var select = document.getElementById('dl-family-select');
  if (!select) return;
  var selectedFamily = select.value;
  if (!selectedFamily) return;

  var catalog = _dlState.catalog;
  if (!catalog) return;

  // Collect cards from all languages matching the selected family
  var cards = [];
  var langEntries = Object.values(catalog);
  for (var li = 0; li < langEntries.length; li++) {
    var lang = langEntries[li];
    if (lang[selectedFamily]) {
      var familyCards = lang[selectedFamily];
      for (var ci = 0; ci < familyCards.length; ci++) {
        cards.push(familyCards[ci]);
      }
    }
  }

  var list = document.getElementById('dl-function-list');
  if (!list) return;
  list.innerHTML = '';

  for (var i = 0; i < cards.length; i++) {
    (function(card) {
      var btn = document.createElement('button');
      btn.className = 'btn btn-secondary dl-fn-btn';
      btn.style.textAlign   = 'left';
      btn.style.padding     = '8px 12px';
      btn.style.minWidth    = '140px';
      btn.style.transition  = 'all 0.15s';
      btn.style.borderLeft  = '3px solid transparent';
      btn.innerHTML =
        '<div style="font-weight:700;font-size:11px;color:var(--text-primary)">' + _escapeHtml(card.name) + '</div>' +
        '<div style="font-size:9px;color:var(--text-secondary);margin-top:2px">' + _escapeHtml(card.description || '') + '</div>';
      btn.addEventListener('click', function onFnBtnClick() {
        selectFunction(card);
      });
      list.appendChild(btn);
    })(cards[i]);
  }
}

// =============================================================================
// Task 8.7 — selectFunction
// =============================================================================
function selectFunction(card) {
  _dlState.selectedCard = card;
  // Reset parameters and roles so previous function's state doesn't bleed in
  _dlState.parameters   = {};
  _dlState.columnRoles  = {};
  console.log('[DataLab] selectFunction:', card.id, 'params:', card.parameters ? card.parameters.length : 0, 'roles:', Object.keys(card.variable_roles||{}).length);

  // Clear previous results immediately
  var resultsContent = document.getElementById('dl-results-content');
  if (resultsContent) resultsContent.innerHTML = '';
  var resultsError = document.getElementById('dl-results-error');
  if (resultsError) { resultsError.textContent = ''; resultsError.style.display = 'none'; }

  // Highlight the clicked button, remove active from others
  var buttons = document.querySelectorAll('.dl-fn-btn');
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].classList.remove('active');
    buttons[i].style.borderLeft = '3px solid transparent';
    buttons[i].style.background = '';
  }
  // Find the button for this card by name and highlight
  for (var j = 0; j < buttons.length; j++) {
    var nameDiv = buttons[j].querySelector('div');
    if (nameDiv && nameDiv.textContent === card.name) {
      buttons[j].classList.add('active');
      buttons[j].style.borderLeft  = '3px solid var(--accent)';
      buttons[j].style.background  = 'var(--accent-dim)';
      break;
    }
  }

  renderLanguageSelector(card);
  renderColumnPanel(card);
  renderParameterForm(card);
  renderDescriptionCard(card);
  renderOntologyPanel(card);   // ← Knowledge Graph: marco metodológico + supuestos

  var filterCard = document.getElementById('dl-filter-card');
  var runRow     = document.getElementById('dl-run-row');
  if (filterCard) filterCard.style.display = 'block';
  if (runRow)     runRow.style.display     = 'flex';

  updateRunButtonState();

  // Verificar paquetes para esta función (no bloquea)
  if (typeof window._pkgCheckFunction === 'function' && card.id) {
    window._pkgCheckFunction(card.id, _dlState.language || 'r');
  }
}

// =============================================================================
// Task 8.8 — clearFunctionSelection
// =============================================================================
function clearFunctionSelection() {
  _dlState.selectedCard  = null;
  _dlState.columnRoles   = {};
  _dlState.parameters    = {};
  _dlState.pendingColumn = null;

  var ids = [
    'dl-column-panel',
    'dl-param-card',
    'dl-filter-card',
    'dl-run-row'
  ];
  for (var i = 0; i < ids.length; i++) {
    var el = document.getElementById(ids[i]);
    if (el) el.style.display = 'none';
  }

  var resultsContent = document.getElementById('dl-results-content');
  if (resultsContent) resultsContent.innerHTML = '';

  var resultsError = document.getElementById('dl-results-error');
  if (resultsError) resultsError.innerHTML = '';

  var functionList = document.getElementById('dl-function-list');
  if (functionList) functionList.innerHTML = '';

  var tier1 = document.getElementById('dl-param-tier1');
  if (tier1) tier1.innerHTML = '';

  var tier2 = document.getElementById('dl-param-tier2');
  if (tier2) tier2.innerHTML = '';

  // Clear checkbox panel content
  var colPanel = document.getElementById('dl-column-panel');
  if (colPanel) colPanel.innerHTML = '';

  var descCard = document.getElementById('dl-desc-card');
  if (descCard) descCard.remove();
}

// =============================================================================
// Task 8.9 — introspectDataset
// =============================================================================
async function introspectDataset() {
  _dlState.datasetColumns = [];

  try {
    // Step 1: Query with LIMIT 0 to test existence
    var queryResp = await fetch(_DL_API + '/api/query', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ sql: 'SELECT * FROM dataset LIMIT 0' })
    });
    if (!queryResp.ok) throw new Error('query failed');

    // Step 2: Analyze to get column metadata
    var analyzeResp = await fetch(_DL_API + '/api/analyze', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({})
    });
    if (!analyzeResp.ok) throw new Error('analyze failed');

    var analyzeData = await analyzeResp.json();
    var statistics  = analyzeData.statistics || analyzeData.columns || [];

    var cols = [];
    for (var i = 0; i < statistics.length; i++) {
      var stat = statistics[i];
      cols.push({
        name: stat.name || stat.column || '',
        type: stat.numeric ? 'numeric' : 'text'
      });
    }
    _dlState.datasetColumns = cols;

    var noDataset = document.getElementById('dl-no-dataset');
    if (noDataset) noDataset.style.display = 'none';

    return true;
  } catch (err) {
    var noDataset2 = document.getElementById('dl-no-dataset');
    if (noDataset2) noDataset2.style.display = 'block';
    return false;
  }
}

// =============================================================================
// renderColumnPanel — checkboxes + "Seleccionar todas" + "Usar seleccionadas"
// =============================================================================
function renderColumnPanel(card) {
  var panel = document.getElementById('dl-column-panel');
  if (!panel) return;

  panel.innerHTML = '';

  var variable_roles = card.variable_roles || {};
  var roleKeys       = Object.keys(variable_roles);
  var allCols        = _dlState.datasetColumns;
  var hasY           = roleKeys.indexOf('Y') !== -1;
  var hasX           = roleKeys.indexOf('X') !== -1;

  // If no roles at all, hide the panel completely
  if (roleKeys.length === 0) {
    panel.style.display = 'none';
    return;
  }

  // Cuando hay Y y X: layout horizontal Y | ~ | X
  // Si además hay I y T (panel): Y|~|X en la primera fila, I|T debajo
  if (hasY && hasX) {
    // Fila principal Y ~ X
    var row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:flex-start;gap:0;margin-bottom:8px';

    var colY = document.createElement('div');
    colY.style.cssText = 'flex:1;min-width:0;border:1px solid var(--border);border-radius:6px;padding:8px;background:var(--bg-card)';
    _buildRoleSection(colY, 'Y', variable_roles['Y'], allCols);

    var sep = document.createElement('div');
    sep.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;' +
                        'padding:0 10px;color:var(--accent);font-size:18px;font-weight:700;min-width:36px;margin-top:28px';
    sep.innerHTML = '<span>~</span><span style="font-size:9px;color:var(--text-secondary);margin-top:4px">Y ~ X</span>';

    var colX = document.createElement('div');
    colX.style.cssText = 'flex:2;min-width:0;border:1px solid var(--border);border-radius:6px;padding:8px;background:var(--bg-card)';
    _buildRoleSection(colX, 'X', variable_roles['X'], allCols);

    row.appendChild(colY);
    row.appendChild(sep);
    row.appendChild(colX);
    panel.appendChild(row);

    // Fila secundaria: roles restantes (I, T, etc.) en horizontal
    var otherKeys = roleKeys.filter(function(k) { return k !== 'Y' && k !== 'X'; });
    if (otherKeys.length > 0) {
      var row2 = document.createElement('div');
      row2.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap';

      // Etiqueta informativa
      var infoLbl = document.createElement('div');
      infoLbl.style.cssText = 'width:100%;font-size:10px;color:var(--text-secondary);' +
                               'text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px';
      infoLbl.textContent = 'Identificadores de panel';
      row2.appendChild(infoLbl);

      for (var ok = 0; ok < otherKeys.length; ok++) {
        var colOther = document.createElement('div');
        colOther.style.cssText = 'flex:1;min-width:140px;border:1px solid var(--border);' +
                                  'border-radius:6px;padding:8px;background:var(--bg-card)';
        _buildRoleSection(colOther, otherKeys[ok], variable_roles[otherKeys[ok]], allCols);
        row2.appendChild(colOther);
      }
      panel.appendChild(row2);
    }
  } else {
    // Layout vertical por defecto (sin Y, o más de 2 roles)
    for (var ri = 0; ri < roleKeys.length; ri++) {
      _buildRoleSection(panel, roleKeys[ri], variable_roles[roleKeys[ri]], allCols);
    }
  }

  panel.style.display = 'block';
}

function _buildRoleSection(panel, roleKey, roleDef, allCols) {
  var allowedTypes = roleDef.types || [];
  var section      = document.createElement('div');
  section.style.marginBottom = '10px';

  // ── Header row ────────────────────────────────────────────────────────────
  var headerRow = document.createElement('div');
  headerRow.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:6px';

  var roleLabel = document.createElement('span');
  roleLabel.style.cssText = 'font-weight:700;font-size:12px;color:var(--text-primary)';
  roleLabel.textContent   = (roleDef.label || roleKey) + (roleDef.required ? ' *' : '');
  headerRow.appendChild(roleLabel);

  // "Seleccionar todas" — solo para roles que NO son Y (Y es única por definición)
  var selAllCb = null;
  if (roleKey !== 'Y') {
    var selAllLabel = document.createElement('label');
    selAllLabel.style.cssText = 'display:flex;align-items:center;gap:5px;font-size:11px;color:var(--text-secondary);cursor:pointer';

    selAllCb = document.createElement('input');
    selAllCb.type = 'checkbox';
    selAllCb.id   = 'dl-selall-' + roleKey;
    selAllCb.style.cssText = 'accent-color:var(--accent);width:14px;height:14px';

    selAllLabel.appendChild(selAllCb);
    selAllLabel.appendChild(document.createTextNode('Seleccionar todas'));
    headerRow.appendChild(selAllLabel);
  }

  section.appendChild(headerRow);

  // ── Checkbox list ─────────────────────────────────────────────────────────
  var checkList = document.createElement('div');
  checkList.id            = 'dl-checklist-' + roleKey;
  checkList.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px';

  // Para el rol X: excluir columnas ya asignadas a Y
  var excludedCols = [];
  if (roleKey === 'X' && _dlState.columnRoles['Y']) {
    excludedCols = _dlState.columnRoles['Y'];
  }

  var visibleCols = allCols.filter(function(c) {
    return excludedCols.indexOf(c.name) === -1;
  });

  if (visibleCols.length === 0) {
    var msg = document.createElement('span');
    msg.style.cssText = 'font-size:11px;color:var(--text-secondary)';
    msg.textContent   = roleKey === 'X'
      ? 'Asigne primero la variable Y para habilitar las X.'
      : 'No hay columnas disponibles.';
    checkList.appendChild(msg);
  }

  for (var ci = 0; ci < visibleCols.length; ci++) {
    (function(col) {
      var isEligible = allowedTypes.length === 0 || allowedTypes.indexOf(col.type) !== -1;
      var prev       = _dlState.columnRoles[roleKey] || [];
      var isChecked  = prev.indexOf(col.name) !== -1;

      var lbl = document.createElement('label');
      lbl.style.cssText = 'display:flex;align-items:center;gap:5px;padding:4px 10px;' +
        'border:1px solid var(--border);border-radius:12px;font-size:11px;' +
        'cursor:pointer;user-select:none;transition:all 0.12s';
      lbl.title = col.type + (isEligible ? '' : ' — tipo no compatible');

      var cb = document.createElement('input');
      cb.type    = 'checkbox';
      cb.checked = isChecked;
      cb.style.cssText = 'accent-color:#d7a538;width:13px;height:13px';
      cb.setAttribute('data-col-name', col.name);
      cb.setAttribute('data-col-type', col.type);
      cb.setAttribute('data-role-key', roleKey);

      _applyColStyle(lbl, isChecked, isEligible);

      cb.addEventListener('change', function() {
        _applyColStyle(lbl, cb.checked, isEligible);
        if (selAllCb) _updateSelectAllState(roleKey);
        updateRunButtonState();
      });

      lbl.appendChild(cb);
      lbl.appendChild(document.createTextNode(col.name));
      checkList.appendChild(lbl);
    })(visibleCols[ci]);
  }

  section.appendChild(checkList);

  // "Seleccionar todas" listener (solo para X)
  if (selAllCb) {
    var checkListId = 'dl-checklist-' + roleKey;
    selAllCb.addEventListener('change', function() {
      var cl  = document.getElementById(checkListId);
      if (!cl) return;
      var cbs = cl.querySelectorAll('input[type=checkbox]');
      var val = selAllCb.checked;
      for (var k = 0; k < cbs.length; k++) {
        cbs[k].checked = val;
        var parentLbl = cbs[k].parentNode;
        if (parentLbl && parentLbl.tagName === 'LABEL') {
          var eligible = allowedTypes.length === 0 ||
                         allowedTypes.indexOf(cbs[k].getAttribute('data-col-type')) !== -1;
          _applyColStyle(parentLbl, val, eligible);
        }
      }
      selAllCb.checked       = val;
      selAllCb.indeterminate = false;
      updateRunButtonState();
    });
  }

  // ── Error div ─────────────────────────────────────────────────────────────
  var errDiv = document.createElement('div');
  errDiv.id             = 'dl-role-err-' + roleKey;
  errDiv.style.cssText  = 'color:#ff4444;font-size:11px;margin-bottom:4px';
  section.appendChild(errDiv);

  // ── "Usar seleccionadas" button ───────────────────────────────────────────
  var applyBtn = document.createElement('button');
  applyBtn.className   = 'btn btn-primary';
  applyBtn.style.cssText = 'font-size:11px;margin-top:4px';
  applyBtn.textContent = roleKey === 'Y' ? '✓ Usar como Y' : '✓ Usar seleccionadas';
  applyBtn.addEventListener('click', function() {
    _applyColumnSelection(roleKey, roleDef, checkList, errDiv);
    // Si se acaba de asignar Y, re-render el panel completo para
    // excluir la variable Y de las opciones disponibles en X
    if (roleKey === 'Y' && _dlState.selectedCard) {
      renderColumnPanel(_dlState.selectedCard);
    }
  });
  section.appendChild(applyBtn);

  // ── Assigned chips ────────────────────────────────────────────────────────
  var assignedRow = document.createElement('div');
  assignedRow.id           = 'dl-role-chips-' + roleKey;
  assignedRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;margin-top:6px';
  section.appendChild(assignedRow);

  panel.appendChild(section);

  if (selAllCb) _updateSelectAllState(roleKey);
  renderRoleChips(roleKey);
}

function _applyColStyle(lbl, isChecked, isEligible) {
  lbl.style.background  = isChecked ? 'var(--accent-dim)' : '';
  lbl.style.borderColor = isChecked ? 'var(--accent)'     : 'var(--border)';
  lbl.style.color       = isChecked ? 'var(--accent)'     :
                          (isEligible ? 'var(--text-primary)' : 'var(--text-secondary)');
}

// Helper — syncs the "select all" checkbox state (checked / indeterminate)
function _updateSelectAllState(roleKey) {
  var selAllCb  = document.getElementById('dl-selall-' + roleKey);
  var checkList = document.getElementById('dl-checklist-' + roleKey);
  if (!selAllCb || !checkList) return;

  var cbs     = checkList.querySelectorAll('input[type=checkbox]');
  var total   = cbs.length;
  var checked = 0;
  for (var i = 0; i < cbs.length; i++) {
    if (cbs[i].checked) checked++;
  }
  if (checked === 0) {
    selAllCb.checked = false; selAllCb.indeterminate = false;
  } else if (checked === total) {
    selAllCb.checked = true;  selAllCb.indeterminate = false;
  } else {
    selAllCb.checked = false; selAllCb.indeterminate = true;
  }
}

// Helper — reads checked boxes and commits to _dlState.columnRoles
function _applyColumnSelection(roleKey, roleDef, checkList, errDiv) {
  // checkList and errDiv may be passed directly or looked up by id
  if (!checkList) checkList = document.getElementById('dl-checklist-' + roleKey);
  if (!errDiv)    errDiv    = document.getElementById('dl-role-err-' + roleKey);

  var cbs      = checkList ? checkList.querySelectorAll('input[type=checkbox]') : [];
  var selected = [];
  for (var i = 0; i < cbs.length; i++) {
    if (cbs[i].checked) selected.push(cbs[i].getAttribute('data-col-name'));
  }

  if (selected.length === 0) {
    if (errDiv) errDiv.textContent = 'Selecciona al menos una columna.';
    return;
  }
  if (errDiv) errDiv.textContent = '';

  // For single-column roles keep only the last selected
  if (roleDef && roleDef.multiple === false) {
    selected = [selected[selected.length - 1]];
  }

  _dlState.columnRoles[roleKey] = selected;
  renderRoleChips(roleKey);
  updateRunButtonState();
}

// onColumnChipClick and onRoleSlotClick are kept as no-ops for compatibility
function onColumnChipClick() {}
function onRoleSlotClick() {}

// =============================================================================
// Task 8.13 — renderRoleChips
// =============================================================================
function renderRoleChips(roleKey) {
  var container = document.getElementById('dl-role-chips-' + roleKey);
  if (!container) return;
  container.innerHTML = '';

  var assigned = _dlState.columnRoles[roleKey] || [];
  for (var i = 0; i < assigned.length; i++) {
    (function(colName) {
      var chip = document.createElement('span');
      chip.className = 'dl-assigned-chip';
      chip.textContent = colName + ' ';

      var removeBtn = document.createElement('button');
      removeBtn.textContent = '×';
      removeBtn.className   = 'dl-chip-remove';
      removeBtn.setAttribute('aria-label', 'Quitar ' + colName);
      removeBtn.addEventListener('click', function onRemoveClick(e) {
        e.stopPropagation(); // prevent triggering the slot click
        removeRoleColumn(roleKey, colName);
      });

      chip.appendChild(removeBtn);
      container.appendChild(chip);
    })(assigned[i]);
  }
}

// =============================================================================
// Task 8.14 — removeRoleColumn
// =============================================================================
function removeRoleColumn(roleKey, colName) {
  var current = _dlState.columnRoles[roleKey] || [];
  _dlState.columnRoles[roleKey] = current.filter(function(c) {
    return c !== colName;
  });
  renderRoleChips(roleKey);
  updateRunButtonState();
}

// =============================================================================
// Task 8.15 — renderParameterForm
// =============================================================================
function renderParameterForm(card) {
  var tier1Container = document.getElementById('dl-param-tier1');
  var tier2Container = document.getElementById('dl-param-tier2');
  if (tier1Container) tier1Container.innerHTML = '';
  if (tier2Container) tier2Container.innerHTML = '';

  var params = card.parameters || [];
  var hasTier2 = false;

  for (var i = 0; i < params.length; i++) {
    (function(param) {
      // Initialize state with default value
      _dlState.parameters[param.name] = param.default !== undefined ? param.default : null;

      var row = document.createElement('div');
      row.className = 'dl-param-row';
      row.style.display        = 'flex';
      row.style.alignItems     = param.type === 'palette' ? 'flex-start' : 'center';
      row.style.flexDirection  = param.type === 'palette' ? 'column'     : 'row';
      row.style.justifyContent = 'space-between';
      row.style.padding        = '5px 0';
      row.style.borderBottom   = '1px solid var(--border)';

      var label = document.createElement('label');
      label.textContent  = param.label || param.name;
      label.htmlFor      = 'dl-param-' + param.name;
      label.style.color  = 'var(--text-primary)';
      label.style.fontSize = '11px';
      label.style.flex   = param.type === 'palette' ? 'none' : '1';
      label.style.marginBottom = param.type === 'palette' ? '6px' : '0';
      row.appendChild(label);

      var control;

      if (param.type === 'text') {
        control = document.createElement('input');
        control.type        = 'text';
        control.id          = 'dl-param-' + param.name;
        control.value       = param.default !== undefined ? String(param.default) : '';
        control.placeholder = param.placeholder || 'Ej: C:\\ruta\\archivo.pdf';
        control.style.cssText = 'width:240px;background:var(--bg-secondary);' +
          'color:var(--text-primary);border:1px solid var(--border);border-radius:4px;' +
          'padding:4px 10px;font-size:11px;font-family:Consolas,monospace';
        _dlState.parameters[param.name] = param.default !== undefined ? String(param.default) : '';
        control.addEventListener('input', function onTextChange() {
          _dlState.parameters[param.name] = control.value;
          updateRunButtonState();
        });
        control.onfocus = function() { control.style.borderColor = 'var(--accent)'; };
        control.onblur  = function() { control.style.borderColor = 'var(--border)'; };

      } else if (param.type === 'integer') {
        control = document.createElement('input');
        control.type      = 'number';
        control.step      = '1';
        control.id        = 'dl-param-' + param.name;
        control.value     = param.default !== undefined ? param.default : '';
        control.className = 'dl-param-input';
        control.style.width      = '90px';
        control.style.textAlign  = 'right';
        control.style.background = 'var(--bg-secondary)';
        control.style.color      = 'var(--accent)';
        control.style.border     = '1px solid var(--border)';
        control.style.borderRadius = '4px';
        control.style.padding    = '3px 8px';
        control.style.fontSize   = '11px';
        control.style.fontWeight = '600';
        control.addEventListener('change', function onIntChange() {
          var raw = control.value;
          var parsed = parseInt(raw, 10);
          // null if not an integer (empty, float, NaN)
          if (raw === '' || isNaN(parsed) || String(parsed) !== String(raw.trim())) {
            _dlState.parameters[param.name] = null;
          } else {
            _dlState.parameters[param.name] = parsed;
          }
          updateRunButtonState();
        });

      } else if (param.type === 'boolean') {
        control = document.createElement('input');
        control.type      = 'checkbox';
        control.id        = 'dl-param-' + param.name;
        control.checked   = param.default === true;
        control.className = 'dl-param-checkbox';
        control.style.accentColor = 'var(--accent)';
        control.style.width  = '16px';
        control.style.height = '16px';
        _dlState.parameters[param.name] = param.default === true;
        control.addEventListener('change', function onBoolChange() {
          _dlState.parameters[param.name] = control.checked;
          updateRunButtonState();
        });

      } else if (param.type === 'select') {
        control = document.createElement('select');
        control.id        = 'dl-param-' + param.name;
        control.className = 'dl-param-select';
        control.style.background    = 'var(--bg-secondary)';
        control.style.color         = 'var(--accent)';
        control.style.border        = '1px solid var(--border)';
        control.style.borderRadius  = '4px';
        control.style.padding       = '3px 6px';
        control.style.fontSize      = '11px';
        control.style.fontWeight    = '600';
        control.style.minWidth      = '120px';
        var options = param.options || [];
        for (var oi = 0; oi < options.length; oi++) {
          var opt = document.createElement('option');
          opt.value       = options[oi].value;
          opt.textContent = options[oi].label;
          if (options[oi].value == param.default) {
            opt.selected = true;
          }
          control.appendChild(opt);
        }
        // Set initial state: use param.default to ensure correct value even before DOM insertion
        _dlState.parameters[param.name] = (param.default !== undefined && param.default !== null)
          ? String(param.default) : (control.options.length > 0 ? control.options[0].value : "");
        control.addEventListener('change', function onSelectChange() {
          _dlState.parameters[param.name] = control.value;
          updateRunButtonState();
        });

      } else if (param.type === 'palette') {
        // ── Selector visual de paleta de colores ──────────────────────────
        // Muestra swatches con los colores reales de cada paleta.
        // El valor que llega a R sigue siendo el entero 1-5.
        var _PALETTES = {
          1: { label: 'NEVEN',   colors: ['#d7a538','#888888','#c08820','#aaaaaa','#e8c060','#666666'] },
          2: { label: 'Viridis', colors: ['#440154','#3b528b','#21908c','#5dc963','#fde725','#b5de2b'] },
          3: { label: 'Plasma',  colors: ['#0d0887','#6a00a8','#b12a90','#e16462','#fca636','#f0f921'] },
          4: { label: 'Set1',    colors: ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#a65628'] },
          5: { label: 'Pastel',  colors: ['#fbb4ae','#b3cde3','#ccebc5','#decbe4','#fed9a6','#ffffcc'] }
        };

        var currentVal = (param.default !== undefined && param.default !== null)
          ? parseInt(param.default, 10) : 1;
        _dlState.parameters[param.name] = currentVal;

        control = document.createElement('div');
        control.id = 'dl-param-' + param.name;
        control.style.cssText = 'display:flex;flex-direction:column;gap:4px;align-items:flex-end';

        function _makePaletteBtn(palId, pal, paramName, container) {
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.dataset.palId = palId;
          btn.style.cssText = [
            'display:flex;align-items:center;gap:5px;',
            'background:var(--bg-secondary);',
            'border:2px solid ' + (palId === currentVal ? 'var(--accent)' : 'var(--border)') + ';',
            'border-radius:6px;padding:3px 6px;cursor:pointer;',
            'transition:border-color 0.15s;'
          ].join('');

          // Swatches
          var swatchRow = document.createElement('div');
          swatchRow.style.cssText = 'display:flex;gap:2px';
          pal.colors.forEach(function(hex) {
            var s = document.createElement('span');
            s.style.cssText = 'width:12px;height:12px;border-radius:2px;background:' + hex;
            swatchRow.appendChild(s);
          });

          // Label
          var lbl = document.createElement('span');
          lbl.textContent = pal.label;
          lbl.style.cssText = 'font-size:10px;color:var(--text-secondary);min-width:44px;text-align:left';

          btn.appendChild(swatchRow);
          btn.appendChild(lbl);

          btn.addEventListener('click', function() {
            // Deselect all
            container.querySelectorAll('button[data-pal-id]').forEach(function(b) {
              b.style.borderColor = 'var(--border)';
            });
            // Select this
            btn.style.borderColor = 'var(--accent)';
            _dlState.parameters[paramName] = parseInt(palId, 10);
            updateRunButtonState();
          });

          return btn;
        }

        Object.keys(_PALETTES).forEach(function(palId) {
          control.appendChild(_makePaletteBtn(
            parseInt(palId, 10), _PALETTES[palId], param.name, control
          ));
        });
      }

      if (control) row.appendChild(control);

      var tier = param.tier || 1;
      if (tier === 2) {
        hasTier2 = true;
        if (tier2Container) tier2Container.appendChild(row);
      } else {
        if (tier1Container) tier1Container.appendChild(row);
      }
    })(params[i]);
  }

  // Show/hide advanced section
  var advancedSection = document.getElementById('dl-param-advanced');
  if (advancedSection) {
    advancedSection.style.display = hasTier2 ? 'block' : 'none';
  }

  var paramCard = document.getElementById('dl-param-card');
  if (paramCard) paramCard.style.display = 'block';

  // Trigger button state after all parameters are initialized
  updateRunButtonState();
}

// =============================================================================
// Task 8.16 — renderLanguageSelector
// =============================================================================
function renderLanguageSelector(card) {
  var langRow    = document.getElementById('dl-language-row');
  var langSelect = document.getElementById('dl-language-select');

  var languages = card.languages || [];

  if (languages.length <= 1) {
    if (langRow) langRow.style.display = 'none';
    _dlState.language = languages[0] || 'r';
    return;
  }

  // Multiple languages: show selector
  if (langRow) langRow.style.display = 'flex';

  if (langSelect) {
    langSelect.innerHTML = '';
    for (var i = 0; i < languages.length; i++) {
      var opt = document.createElement('option');
      opt.value       = languages[i];
      opt.textContent = languages[i].toUpperCase();
      langSelect.appendChild(opt);
    }
    _dlState.language = langSelect.value;

    // Remove previous listener by cloning node
    var freshSelect = langSelect.cloneNode(true);
    langSelect.parentNode.replaceChild(freshSelect, langSelect);
    freshSelect.addEventListener('change', function onLangChange() {
      _dlState.language = freshSelect.value;
    });
  }
}

// =============================================================================
// renderDescriptionCard — descripción del método + botón Wikipedia
// =============================================================================
function renderDescriptionCard(card) {
  var existing = document.getElementById('dl-desc-card');
  if (existing) existing.remove();

  if (!card.description) return;

  var desc = document.createElement('div');
  desc.id              = 'dl-desc-card';
  desc.className       = 'card';
  desc.style.marginBottom = '8px';
  desc.style.borderLeft = '3px solid var(--accent)';

  var title = document.createElement('div');
  title.className   = 'card-title';
  title.textContent = 'Sobre este método';
  desc.appendChild(title);

  var text = document.createElement('p');
  text.style.color    = 'var(--text-secondary)';
  text.style.fontSize = '11px';
  text.style.lineHeight = '1.5';
  text.style.marginBottom = card.wikipedia_url ? '8px' : '0';
  text.textContent = card.description;
  desc.appendChild(text);

  if (card.wikipedia_url) {
    var wikiBtn = document.createElement('a');
    wikiBtn.href        = card.wikipedia_url;
    wikiBtn.target      = '_blank';
    wikiBtn.rel         = 'noopener noreferrer';
    wikiBtn.className   = 'btn btn-secondary';
    wikiBtn.style.fontSize    = '10px';
    wikiBtn.style.display     = 'inline-flex';
    wikiBtn.style.alignItems  = 'center';
    wikiBtn.style.gap         = '5px';
    wikiBtn.style.textDecoration = 'none';
    wikiBtn.innerHTML = '🌐 Ir a Wikipedia';
    desc.appendChild(wikiBtn);
  }

  // Insert: before column panel if visible, else before param card, else at top of results area
  var inserted = false;
  var colPanel = document.getElementById('dl-column-panel');
  // Only insert before column panel if it's actually visible (has roles)
  if (colPanel && colPanel.parentNode && colPanel.style.display !== 'none') {
    colPanel.parentNode.insertBefore(desc, colPanel);
    inserted = true;
  }
  if (!inserted) {
    // Fallback: insert before param card (covers functions with no roles like TM)
    var paramCard = document.getElementById('dl-param-card');
    if (paramCard && paramCard.parentNode) {
      paramCard.parentNode.insertBefore(desc, paramCard);
      inserted = true;
    }
  }
  if (!inserted) {
    // Last resort: append to data-lab tab
    var dataLabDiv = document.getElementById('data-lab');
    if (dataLabDiv) dataLabDiv.appendChild(desc);
  }
}

// =============================================================================
// renderOntologyPanel — panel del Knowledge Graph econométrico
// Se llama desde selectFunction(card) cada vez que el usuario elige una función.
// Consulta GET /api/kg/method/{function_id} y rellena los tres sub-cards:
//   #dl-kg-method-card     → marco metodológico (descripción + referencia)
//   #dl-kg-assumptions-card → supuestos a verificar (chips expandibles)
//   #dl-kg-alternatives-card → métodos alternativos (chips)
// Si la función no tiene nodo en el grafo, oculta el panel discretamente.
// =============================================================================
function renderOntologyPanel(card) {
  var panel = document.getElementById('dl-ontology-panel');
  if (!panel) return;

  // Ocultar mientras carga (evita flash de contenido anterior)
  panel.style.display = 'none';
  _hideOntologyCards();

  if (!card || !card.id) return;

  fetch(_DL_API + '/api/kg/method/' + encodeURIComponent(card.id))
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data || !data.found) return;  // Sin nodo → panel permanece oculto

      panel.style.display = 'block';

      // ── Marco metodológico ────────────────────────────────────────────────
      var method = data.method || {};
      if (method.name || method.description) {
        var methodCard  = document.getElementById('dl-kg-method-card');
        var methodBadge = document.getElementById('dl-kg-method-badge');
        var methodText  = document.getElementById('dl-kg-method-text');
        var methodRef   = document.getElementById('dl-kg-method-ref');

        if (methodCard)  methodCard.style.display  = 'block';
        if (methodBadge) methodBadge.textContent    = method.type || 'Method';

        if (methodText) {
          // Mostrar solo la primera oración de la descripción (conciso en panel)
          var desc = method.description || '';
          var firstSentence = desc.split('.')[0];
          methodText.textContent = firstSentence
            ? firstSentence + '.'
            : desc.substring(0, 150) + (desc.length > 150 ? '…' : '');
        }

        if (methodRef) {
          var ref = method.reference || {};
          if (ref.book) {
            // Formato corto: "Hanck et al. · Cap. 4 & 6 · pp. 85-160"
            var bookShort = _kgShortBook(ref.book);
            methodRef.textContent = '📖 ' + bookShort +
              (ref.chapter ? ' · ' + _kgShortChapter(ref.chapter) : '') +
              (ref.pages   ? ' · ' + ref.pages : '');
          }
        }
      }

      // ── Supuestos a verificar ────────────────────────────────────────────
      var assumptions = data.assumptions || [];
      if (assumptions.length > 0) {
        var assCard  = document.getElementById('dl-kg-assumptions-card');
        var assChips = document.getElementById('dl-kg-assumption-chips');
        if (assCard)  assCard.style.display  = 'block';
        if (assChips) {
          assChips.innerHTML = '';
          assumptions.forEach(function(a) {
            assChips.appendChild(_kgAssumptionChip(a));
          });
        }
      }

      // ── Métodos alternativos ──────────────────────────────────────────────
      var alternatives = data.alternatives || [];
      if (alternatives.length > 0) {
        var altCard  = document.getElementById('dl-kg-alternatives-card');
        var altChips = document.getElementById('dl-kg-alternative-chips');
        if (altCard)  altCard.style.display  = 'block';
        if (altChips) {
          altChips.innerHTML = '';
          alternatives.forEach(function(alt) {
            altChips.appendChild(_kgAlternativeChip(alt));
          });
        }
      }
    })
    .catch(function() {
      // Error de red o servidor — panel permanece oculto, sin romper el flujo
    });
}

// ── Helpers internos del panel ontológico ─────────────────────────────────────

function _hideOntologyCards() {
  ['dl-kg-method-card', 'dl-kg-assumptions-card', 'dl-kg-alternatives-card']
    .forEach(function(id) {
      var el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });
}

function _kgShortBook(book) {
  // "Introduction to Econometrics with R (Hanck et al.)" → "Hanck et al."
  var m = book.match(/\(([^)]+)\)/);
  return m ? m[1] : book.split(' ').slice(0, 3).join(' ');
}

function _kgShortChapter(chapter) {
  // "Chapter 4 & 6: Linear Regression..." → "Cap. 4 & 6"
  var m = chapter.match(/[Cc]hapter\s+([\d\s&,]+)/);
  return m ? 'Cap. ' + m[1].trim() : chapter.split(':')[0].trim();
}

function _kgAssumptionChip(assumption) {
  var chip = document.createElement('div');
  chip.style.cssText =
    'position:relative;display:inline-block;' +
    'background:var(--bg-secondary);border:1px solid var(--border);' +
    'border-radius:12px;padding:3px 10px;font-size:10px;' +
    'color:var(--text-secondary);cursor:pointer;transition:all .15s;' +
    'max-width:100%;user-select:none';

  var label = document.createElement('span');
  label.textContent = assumption.name || assumption.id || '';
  chip.appendChild(label);

  // Tooltip expandido con definición + referencia
  var tooltip = document.createElement('div');
  tooltip.style.cssText =
    'display:none;position:absolute;z-index:200;bottom:calc(100% + 6px);left:0;' +
    'min-width:260px;max-width:320px;padding:10px 12px;' +
    'background:var(--bg-card);border:1px solid rgba(215,165,56,0.35);' +
    'border-radius:6px;box-shadow:0 4px 20px rgba(0,0,0,0.5);' +
    'font-size:11px;line-height:1.6;color:var(--text-primary);' +
    'pointer-events:none;white-space:normal;word-break:break-word';

  var defText = assumption.definition || '';
  var ref     = assumption.reference  || {};
  var refStr  = '';
  if (ref.book) {
    refStr = '<div style="margin-top:6px;font-size:9px;color:var(--text-secondary);' +
             'font-style:italic;border-top:1px solid var(--border);padding-top:5px">' +
             '📖 ' + _kgShortBook(ref.book) +
             (ref.chapter ? ' · ' + _kgShortChapter(ref.chapter) : '') +
             (ref.pages   ? ' · ' + ref.pages : '') +
             '</div>';
  }

  tooltip.innerHTML =
    '<div style="font-weight:700;color:var(--accent);margin-bottom:4px;font-size:10px">' +
    (assumption.name || '') + '</div>' +
    '<div>' + defText.substring(0, 220) + (defText.length > 220 ? '…' : '') + '</div>' +
    refStr;

  chip.appendChild(tooltip);

  // Mostrar/ocultar tooltip al hacer hover
  chip.addEventListener('mouseenter', function() {
    chip.style.borderColor = 'rgba(215,165,56,0.6)';
    chip.style.color       = 'var(--accent)';
    tooltip.style.display  = 'block';
  });
  chip.addEventListener('mouseleave', function() {
    chip.style.borderColor = 'var(--border)';
    chip.style.color       = 'var(--text-secondary)';
    tooltip.style.display  = 'none';
  });

  return chip;
}

function _kgAlternativeChip(alt) {
  var chip = document.createElement('div');
  chip.style.cssText =
    'display:inline-block;background:var(--bg-secondary);' +
    'border:1px solid var(--border);border-radius:12px;' +
    'padding:3px 10px;font-size:10px;color:var(--text-secondary);' +
    'cursor:default;transition:border-color .15s';
  chip.textContent = alt.name || alt.id || '';
  chip.title       = alt.name || '';
  chip.addEventListener('mouseenter', function() {
    chip.style.borderColor = 'var(--border)';
    chip.style.color       = 'var(--text-primary)';
  });
  chip.addEventListener('mouseleave', function() {
    chip.style.borderColor = 'var(--border)';
    chip.style.color       = 'var(--text-secondary)';
  });
  return chip;
}

// =============================================================================
// Task 8.17 — updateRunButtonState
// =============================================================================
function updateRunButtonState() {
  var btn = document.getElementById('dl-run-btn');
  if (!btn) return;

  if (!_dlState.selectedCard) { btn.disabled = true; return; }

  // Check required roles have committed columns OR checked checkboxes
  var roles    = _dlState.selectedCard.variable_roles || {};
  var roleKeys = Object.keys(roles);
  var hasColumns = true;

  for (var ri = 0; ri < roleKeys.length; ri++) {
    var rk      = roleKeys[ri];
    var roleDef = roles[rk];
    if (!roleDef.required) continue;

    // Committed?
    if ((_dlState.columnRoles[rk] || []).length > 0) continue;

    // Any checked in DOM?
    var checkList = document.getElementById('dl-checklist-' + rk);
    if (checkList) {
      var cbs     = checkList.querySelectorAll('input[type=checkbox]');
      var anyChk  = false;
      for (var ci = 0; ci < cbs.length; ci++) {
        if (cbs[ci].checked) { anyChk = true; break; }
      }
      if (anyChk) continue;
    }
    hasColumns = false;
    break;
  }

  if (!hasColumns) { btn.disabled = true; return; }

  // All parameters valid? Only block on explicit null (false/0/"" are valid values)
  // Exception: text params with empty string are allowed (optional path)
  var params    = _dlState.parameters;
  var paramKeys = Object.keys(params);
  for (var pi = 0; pi < paramKeys.length; pi++) {
    if (params[paramKeys[pi]] === null) { btn.disabled = true; return; }
  }

  btn.disabled = false;
}

// =============================================================================
// Task 8.18 — validateRoles
// =============================================================================
function validateRoles(showErrors) {
  if (!_dlState.selectedCard) return false;

  var variable_roles = _dlState.selectedCard.variable_roles || {};
  var roleKeys = Object.keys(variable_roles);
  var valid = true;

  for (var i = 0; i < roleKeys.length; i++) {
    var roleKey = roleKeys[i];
    var roleDef = variable_roles[roleKey];
    var errDiv  = document.getElementById('dl-role-err-' + roleKey);

    if (roleDef.required) {
      var assigned = _dlState.columnRoles[roleKey];
      if (!assigned || assigned.length === 0) {
        valid = false;
        if (showErrors && errDiv) {
          errDiv.textContent = 'Este rol es obligatorio (*). Asigne al menos una columna.';
        }
      } else {
        if (showErrors && errDiv) errDiv.textContent = '';
      }
    } else {
      if (showErrors && errDiv) errDiv.textContent = '';
    }
  }

  return valid;
}

// =============================================================================
// Task 8.19 — runAnalysis
// =============================================================================
async function runAnalysis() {
  // Auto-apply any checked columns that haven't been committed yet
  if (_dlState.selectedCard) {
    var roles    = _dlState.selectedCard.variable_roles || {};
    var roleKeys = Object.keys(roles);
    for (var ri = 0; ri < roleKeys.length; ri++) {
      var rk        = roleKeys[ri];
      var checkList = document.getElementById('dl-checklist-' + rk);
      if (checkList) {
        var cbs     = checkList.querySelectorAll('input[type=checkbox]');
        var checked = [];
        for (var ci = 0; ci < cbs.length; ci++) {
          if (cbs[ci].checked) checked.push(cbs[ci].getAttribute('data-col-name'));
        }
        if (checked.length > 0) _dlState.columnRoles[rk] = checked;
      }
    }
  }

  if (!validateRoles(true)) return;

  var btn     = document.getElementById('dl-run-btn');
  var spinner = document.getElementById('dl-run-spinner');
  var errDiv  = document.getElementById('dl-results-error');

  if (btn)    btn.disabled           = true;
  if (spinner) spinner.style.display = 'inline-block';
  if (errDiv) { errDiv.textContent = ''; errDiv.style.display = 'none'; }

  // Limpiar resultados anteriores inmediatamente al iniciar nueva ejecución
  var resultsContent = document.getElementById('dl-results-content');
  if (resultsContent) resultsContent.innerHTML = '';

  var filterInput  = document.getElementById('dl-filter-input');
  var filterClause = filterInput ? filterInput.value.trim() : '';

  var body = {
    function_id:   _dlState.selectedCard.id,
    language:      _dlState.language,
    column_roles:  _dlState.columnRoles,
    parameters:    _dlState.parameters,
    filter_clause: filterClause
  };

  // ACP: siempre usar la cantidad de columnas asignadas como N_Componentes
  // (el usuario puede ajustar manualmente si quiere menos)
  if (_dlState.selectedCard.id === 'AD_ACP') {
    var xCols = (body.column_roles['X'] || []).length;
    if (xCols > 0 && (!body.parameters['N_Componentes'] || body.parameters['N_Componentes'] === 0)) {
      body.parameters['N_Componentes'] = xCols;
    }
  }

  try {
    var response = await fetch(_DL_API + '/api/datalab/run', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body)
    });

    var data = await response.json();

    if (response.ok && data.status === 'ok') {
      renderResults(data.slots || []);
      // Guardar slots del último análisis para el botón + Resultados del Tab IA
      window._dlLastSlots      = data.slots || [];
      window._dlLastFunctionId = _dlState.selectedCard ? _dlState.selectedCard.id : null;
      window._dlLastCard       = _dlState.selectedCard || null;
      // Acumular en historial de modelos
      if (typeof _dlAddToHistory === 'function') {
        _dlAddToHistory({
          function_id:  window._dlLastFunctionId,
          source:       'user',
          context_note: '',
          column_roles: JSON.parse(JSON.stringify(_dlState.columnRoles  || {})),
          parameters:   JSON.parse(JSON.stringify(_dlState.parameters   || {})),
          slots:        data.slots || []
        });
      }
      // Si se cargó un dataset Wooldridge, re-introspect para actualizar columnas
      var loadSlots = (data.slots || []).filter(function(s) { return s.name === 'dataset_cargado'; });
      if (loadSlots.length > 0) {
        setTimeout(function() {
          introspectDataset().then(function() {
            // Mostrar notificación de éxito en el panel
            var msg = document.createElement('div');
            msg.className = 'msg-info';
            msg.style.cssText = 'background:var(--accent-dim);border:1px solid var(--accent);' +
                                'border-radius:6px;padding:10px;margin-top:8px;font-size:11px;color:var(--accent)';
            msg.innerHTML = '✓ Dataset cargado en DuckDB. Ya puedes ir a <strong>Regresión</strong>, ' +
                            '<strong>Análisis de Datos</strong> o <strong>Series de Tiempo</strong> ' +
                            'para analizarlo.';
            var resultsDiv = document.getElementById('dl-results-content');
            if (resultsDiv) resultsDiv.appendChild(msg);
          });
        }, 300);
      }
    } else {
      var msg = (data && data.message) ? data.message : ('HTTP ' + response.status);
      if (errDiv) { errDiv.textContent = msg; errDiv.style.display = 'block'; }
    }
  } catch (err) {
    if (errDiv) { errDiv.textContent = 'Error de red: ' + err.message; errDiv.style.display = 'block'; }
  } finally {
    if (btn)    btn.disabled           = false;
    if (spinner) spinner.style.display = 'none';
  }
}

// =============================================================================
// Task 8.20 — renderResults
// =============================================================================
function renderResults(slots) {
  console.log('[DataLab] renderResults llamado con', slots ? slots.length : 0, 'slots');
  var container = document.getElementById('dl-results-content');
  if (!container) return;
  container.innerHTML = '';

  var tier1 = slots.filter(function(s) { return s.tier === 1 || s.tier === '1'; });
  var tier2 = slots.filter(function(s) { return s.tier === 2 || s.tier === '2'; });

  // Auto-cargar dataset en DuckDB si hay un slot dataset_*
  // Esto permite que los chips Y/X se pueblen con las columnas del dataset elegido
  var datasetSlot = slots.find(function(s) {
    return s.name && s.name.indexOf('dataset_') === 0 &&
           Array.isArray(s.value) && s.value.length > 0 &&
           s.value[0] && typeof s.value[0] === 'object';
  });
  if (datasetSlot) {
    try {
      var rows = datasetSlot.value;
      var cols = Object.keys(rows[0]);
      if (cols.length > 0) {
        var types = cols.map(function(c) {
          var sample = rows.find(function(r) { return r[c] !== null && r[c] !== undefined; });
          return (sample && typeof sample[c] === 'number') ? 'numeric' : 'text';
        });
        var dataForLoad = rows.map(function(r) {
          return cols.map(function(c) { return r[c] !== undefined ? r[c] : null; });
        });
        fetch(API + '/api/load', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ columns: cols, types: types, data: dataForLoad })
        }).then(function(resp) {
          if (resp.ok) {
            var info = document.getElementById('data-info');
            if (info) {
              info.textContent = datasetSlot.name.replace('dataset_', '') +
                ' cargado (' + rows.length + ' obs, ' + cols.length + ' vars)';
            }
            // Repoblar columnas si hay funcion activa
            if (window._dlCurrentCard && typeof renderColumnPanel === 'function') {
              renderColumnPanel(window._dlCurrentCard);
            }
          }
        }).catch(function(e) {
          console.warn('[Benchmark] Auto-load DuckDB fallo silenciosamente:', e);
        });
      }
    } catch(e) {
      console.warn('[Benchmark] Error en auto-load:', e);
    }
  }

  // Render tier 1 directly
  for (var i = 0; i < tier1.length; i++) {
    container.appendChild(buildSlotElement(tier1[i]));
  }

  // Render tier 2 in styled collapsible
  if (tier2.length > 0) {
    var details = document.createElement('details');
    details.style.marginTop   = '8px';
    details.style.border      = '1px solid var(--border)';
    details.style.borderRadius = 'var(--radius)';
    details.style.padding     = '8px';
    details.style.background  = 'var(--bg-card)';

    var summary = document.createElement('summary');
    summary.style.cursor      = 'pointer';
    summary.style.color       = 'var(--text-secondary)';
    summary.style.fontSize    = '10px';
    summary.style.fontWeight  = '600';
    summary.style.textTransform = 'uppercase';
    summary.style.letterSpacing = '0.6px';
    summary.textContent = 'Detalles técnicos';
    details.appendChild(summary);

    var detailsContent = document.createElement('div');
    detailsContent.style.marginTop = '8px';
    for (var j = 0; j < tier2.length; j++) {
      detailsContent.appendChild(buildSlotElement(tier2[j]));
    }
    details.appendChild(detailsContent);
    container.appendChild(details);
  }
}

// =============================================================================
// Task 8.21 — buildSlotElement
// =============================================================================
function buildSlotElement(slot) {
  console.log('[DataLab] buildSlotElement:', slot.name, 'type='+slot.type, 'tier='+slot.tier, 'value=', slot.value);
  var container = document.createElement('div');
  container.className = 'dl-slot';
  container.style.marginBottom = '12px';

  // Heading
  var heading = document.createElement('h4');
  heading.textContent = slot.label || slot.name;
  heading.style.color        = 'var(--accent)';
  heading.style.fontSize     = '10px';
  heading.style.textTransform = 'uppercase';
  heading.style.letterSpacing = '0.8px';
  heading.style.marginBottom  = '6px';
  container.appendChild(heading);

  var content;

  switch (slot.type) {
    case 'table':
      content = renderSlotTable(slot.value, slot.name);
      // Si el slot es un dataset de Wooldridge, agregar boton "Cargar en Data Studio"
      if (slot.name && slot.name.indexOf('dataset_') === 0) {
        var btnLoad = document.createElement('button');
        btnLoad.textContent = 'Cargar en Data Studio';
        btnLoad.style.cssText = 'margin-top:8px;padding:5px 12px;background:var(--accent);' +
          'color:var(--bg-primary);border:none;border-radius:4px;font-size:10px;' +
          'font-weight:700;cursor:pointer;display:block';
        btnLoad.addEventListener('click', function() {
          // Convertir array-of-objects a CSV para _loadFromContent
          var rows = Array.isArray(slot.value) ? slot.value : [];
          if (!rows.length) return;
          var cols = Object.keys(rows[0]);
          var csv  = cols.join(',') + '\n' +
                     rows.map(function(r) {
                       return cols.map(function(c) {
                         var v = r[c];
                         if (v === null || v === undefined) return '';
                         var s = String(v);
                         return s.indexOf(',') >= 0 || s.indexOf('"') >= 0
                           ? '"' + s.replace(/"/g,'""') + '"' : s;
                       }).join(',');
                     }).join('\n');
          var dsName = slot.name.replace('dataset_', '') + '.csv';
          if (typeof _loadFromContent === 'function') {
            _loadFromContent(dsName, csv);
            btnLoad.textContent = 'Cargado en Data Studio';
            btnLoad.style.background = 'var(--success, #4caf50)';
          } else {
            alert('_loadFromContent no disponible -- abra Data Studio primero');
          }
        });
        content.appendChild(btnLoad);
      }
      break;

    case 'vector':
      content = renderVectorAsTable(slot.value, slot.name);
      break;

    case 'html':
      // Detectar si es JSON de plotly envuelto en <neven-plotly>
      if (typeof slot.value === 'string' && slot.value.indexOf('<neven-plotly>') !== -1) {
        content = _renderPlotlyJSON(slot.value, slot.name);
      } else {
        content = document.createElement('iframe');
        content.setAttribute('srcdoc', typeof slot.value === 'string' ? slot.value : '');
        content.setAttribute('sandbox', 'allow-scripts allow-same-origin');
        content.style.width  = '100%';
        content.style.height = '420px';
        content.style.border = 'none';
      }
      break;

    case 'warning_pedagogy':
      content = _renderPedagogyWarning(slot.value);
      break;

    case 'scalar':
    case 'text':
    default: {
      var displayVal2;
      if (typeof slot.value === 'object' && slot.value !== null) {
        displayVal2 = JSON.stringify(slot.value, null, 2);
      } else {
        displayVal2 = String(slot.value !== undefined ? slot.value : '');
      }
      // Always render as plain text in a styled pre block
      content = document.createElement('pre');
      content.style.cssText = 'background:#1e1e1e;border:1px solid var(--border);' +
        'border-radius:var(--radius);padding:12px 16px;font-family:Consolas,\'Cascadia Code\',monospace;' +
        'font-size:11.5px;color:#d4d4d4;white-space:pre-wrap;line-height:1.5;' +
        'max-height:520px;overflow-y:auto;overflow-x:auto;word-break:normal;margin:0';
      content.textContent = displayVal2;
      break;
    }
  }

  container.appendChild(content);
  return container;
}

// =============================================================================
// _renderPedagogyWarning — renderer para slots de tipo 'warning_pedagogy'
// Muestra el texto compacto siempre visible + panel expandible de 5 capas.
// Las 5 capas son: fenómeno, implicación, acción, referencia, reflexión.
// =============================================================================
function _renderPedagogyWarning(warning) {
  // warning puede llegar como objeto o como string JSON (fallback de seguridad)
  var w = warning;
  if (typeof w === 'string') {
    try { w = JSON.parse(w); } catch(e) {
      var fb = document.createElement('div');
      fb.style.cssText = 'padding:8px 12px;font-size:11px;color:var(--accent);' +
                         'border:1px solid rgba(215,165,56,0.3);border-radius:6px';
      fb.textContent = '⚠ ' + w;
      return fb;
    }
  }
  if (!w || typeof w !== 'object') {
    var fb2 = document.createElement('div');
    fb2.textContent = '⚠ Advertencia metodológica';
    return fb2;
  }

  var wrap = document.createElement('div');
  wrap.style.cssText =
    'border:1px solid rgba(215,165,56,0.35);border-radius:6px;' +
    'background:rgba(215,165,56,0.04);overflow:hidden;margin-bottom:2px';

  // ── Nivel compacto (siempre visible, clicable) ───────────────────────────
  var compact = document.createElement('div');
  compact.style.cssText =
    'padding:8px 12px;cursor:pointer;display:flex;align-items:center;' +
    'justify-content:space-between;user-select:none;gap:8px';

  var compactText = document.createElement('span');
  compactText.style.cssText = 'font-size:11px;color:var(--accent);flex:1;line-height:1.4';
  compactText.textContent = w.compact || '⚠ Advertencia metodológica';

  var compactToggle = document.createElement('span');
  compactToggle.style.cssText =
    'font-size:9px;color:var(--text-secondary);white-space:nowrap;' +
    'padding:2px 6px;border:1px solid var(--border);border-radius:4px;' +
    'transition:all .15s;flex-shrink:0';
  compactToggle.textContent = 'Ver más ▼';

  compact.appendChild(compactText);
  compact.appendChild(compactToggle);

  // ── Nivel expandido (oculto por defecto) ─────────────────────────────────
  var expanded = document.createElement('div');
  expanded.style.cssText =
    'display:none;padding:10px 14px 14px;' +
    'border-top:1px solid rgba(215,165,56,0.2)';
  expanded.innerHTML = _buildExpandedWarning(w);

  // Toggle
  var _isOpen = false;
  compact.addEventListener('click', function() {
    _isOpen = !_isOpen;
    expanded.style.display    = _isOpen ? 'block' : 'none';
    compactToggle.textContent = _isOpen ? 'Ver menos ▲' : 'Ver más ▼';
    compactToggle.style.borderColor = _isOpen
      ? 'rgba(215,165,56,0.5)' : 'var(--border)';
    compactToggle.style.color = _isOpen
      ? 'var(--accent)' : 'var(--text-secondary)';
  });
  compact.addEventListener('mouseenter', function() {
    compact.style.background = 'rgba(215,165,56,0.06)';
  });
  compact.addEventListener('mouseleave', function() {
    compact.style.background = '';
  });

  wrap.appendChild(compact);
  wrap.appendChild(expanded);
  return wrap;
}

function _buildExpandedWarning(w) {
  var ref = (w && w.reference) ? w.reference : {};
  var accentHex = 'var(--accent)';
  var mutedHex  = 'var(--text-secondary)';

  function _section(title, body) {
    if (!body || !body.trim()) return '';
    return '<div style="margin-bottom:10px">' +
      '<div style="font-size:9px;font-weight:700;color:' + accentHex + ';' +
        'text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px">' +
        title + '</div>' +
      '<div style="font-size:11px;line-height:1.65;color:var(--text-primary)">' +
        body + '</div>' +
      '</div>';
  }

  var refBlock = '';
  if (ref.book) {
    var bookShort = '';
    var bm = ref.book.match(/\(([^)]+)\)/);
    bookShort = bm ? bm[1] : ref.book.split(' ').slice(0, 3).join(' ');
    var chapShort = '';
    if (ref.chapter) {
      var cm = ref.chapter.match(/[Cc]hapter\s+([\d\s&,]+)/);
      chapShort = cm ? 'Cap. ' + cm[1].trim() : ref.chapter.split(':')[0].trim();
    }
    var refText = (w.reference && w.reference.text) ? w.reference.text : 'Referencia canónica:';
    refBlock =
      '<div style="margin-bottom:10px;padding:8px 10px;' +
        'background:rgba(215,165,56,0.06);border-radius:4px;' +
        'border-left:2px solid rgba(215,165,56,0.4)">' +
        '<div style="font-size:9px;font-weight:700;color:' + accentHex + ';' +
          'text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px">Para profundizar</div>' +
        '<div style="font-size:11px;line-height:1.6;font-style:italic;color:var(--text-primary)">' +
          refText + '</div>' +
        '<div style="font-size:10px;color:' + mutedHex + ';margin-top:5px">' +
          '📖 ' + bookShort +
          (chapShort ? ' · ' + chapShort : '') +
          (ref.pages  ? ' · ' + ref.pages : '') +
        '</div>' +
      '</div>';
  }

  var reflectionBlock = '';
  if (w.reflection_question && w.reflection_question.trim()) {
    reflectionBlock =
      '<div style="padding:8px 10px;background:rgba(255,255,255,0.03);' +
        'border-radius:4px;border-left:2px solid rgba(215,165,56,0.3)">' +
        '<div style="font-size:9px;font-weight:700;color:' + accentHex + ';' +
          'text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px">Para reflexionar</div>' +
        '<div style="font-size:11px;line-height:1.65;font-style:italic;color:var(--text-primary)">' +
          w.reflection_question + '</div>' +
      '</div>';
  }

  return (
    _section('El fenómeno', w.phenomenon || '') +
    _section('Por qué importa', w.implication || '') +
    _section('Lo que NEVEN hará', w.action || '') +
    refBlock +
    reflectionBlock
  );
}

// =============================================================================
// Helper — render a vector as an indexed table with TOP 10 + Show all + Download
// =============================================================================
function renderVectorAsTable(arr, slotName) {
  if (!arr || (Array.isArray(arr) && arr.length === 0)) {
    var empty = document.createElement('p');
    empty.style.color = 'var(--text-secondary)';
    empty.textContent = 'Sin datos.';
    return empty;
  }

  var items = Array.isArray(arr) ? arr : [arr];
  var TOP = 10;
  var showing = Math.min(TOP, items.length);

  var wrapper = document.createElement('div');

  // Table
  var tableWrap = document.createElement('div');
  tableWrap.style.overflow  = 'auto';
  tableWrap.style.maxHeight = '220px';

  var table = document.createElement('table');
  table.className = 'data-table';

  var thead = document.createElement('thead');
  var hrow  = document.createElement('tr');
  ['#', 'Valor'].forEach(function(h) {
    var th = document.createElement('th');
    th.textContent = h;
    th.style.textAlign = h === '#' ? 'center' : 'right';
    hrow.appendChild(th);
  });
  thead.appendChild(hrow);
  table.appendChild(thead);

  var tbody = document.createElement('tbody');
  tbody.id = 'dl-vec-body-' + slotName;

  function fillRows(limit) {
    tbody.innerHTML = '';
    for (var i = 0; i < Math.min(limit, items.length); i++) {
      var tr = document.createElement('tr');
      var tdIdx = document.createElement('td');
      tdIdx.textContent = i + 1;
      tdIdx.style.textAlign = 'center';
      tdIdx.style.color = 'var(--text-secondary)';
      var tdVal = document.createElement('td');
      tdVal.textContent = items[i] !== null && items[i] !== undefined ? String(items[i]) : '';
      tr.appendChild(tdIdx);
      tr.appendChild(tdVal);
      tbody.appendChild(tr);
    }
  }

  fillRows(showing);
  table.appendChild(tbody);
  tableWrap.appendChild(table);
  wrapper.appendChild(tableWrap);

  // Count label
  var meta = document.createElement('div');
  meta.style.fontSize   = '10px';
  meta.style.color      = 'var(--text-secondary)';
  meta.style.marginTop  = '4px';
  meta.textContent      = 'Mostrando ' + showing + ' de ' + items.length + ' registros';
  wrapper.appendChild(meta);

  // Buttons row
  var btnRow = document.createElement('div');
  btnRow.style.display  = 'flex';
  btnRow.style.gap      = '6px';
  btnRow.style.marginTop = '6px';

  if (items.length > TOP) {
    var showAllBtn = document.createElement('button');
    showAllBtn.className   = 'btn btn-primary';
    showAllBtn.style.fontSize = '10px';
    showAllBtn.textContent = '▼ Mostrar todo (' + items.length + ')';
    var expanded = false;
    showAllBtn.addEventListener('click', function() {
      expanded = !expanded;
      if (expanded) {
        fillRows(items.length);
        tableWrap.style.maxHeight = '400px';
        meta.textContent = 'Mostrando ' + items.length + ' de ' + items.length + ' registros';
        showAllBtn.textContent = '▲ Mostrar menos';
      } else {
        fillRows(TOP);
        tableWrap.style.maxHeight = '220px';
        meta.textContent = 'Mostrando ' + TOP + ' de ' + items.length + ' registros';
        showAllBtn.textContent = '▼ Mostrar todo (' + items.length + ')';
      }
    });
    btnRow.appendChild(showAllBtn);
  }

  var dlBtn = document.createElement('button');
  dlBtn.className   = 'btn btn-primary';
  dlBtn.style.fontSize = '10px';
  dlBtn.textContent = '⬇ Descargar CSV';
  dlBtn.addEventListener('click', function() {
    var csv = '#,Valor\n' + items.map(function(v, i) {
      return (i+1) + ',' + (v !== null && v !== undefined ? String(v) : '');
    }).join('\n');
    var blob = new Blob([csv], {type:'text/csv'});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (slotName || 'data') + '.csv';
    a.click();
  });
  btnRow.appendChild(dlBtn);

  wrapper.appendChild(btnRow);
  return wrapper;
}

// =============================================================================
// Helper — render plotly JSON using the Plotly.js already loaded in taskpane
// =============================================================================
function _renderPlotlyJSON(jsonStr, slotName) {
  var wrapper = document.createElement('div');
  wrapper.style.cssText = 'width:100%;height:380px;background:var(--bg-secondary);border-radius:var(--radius)';

  var divId = 'plotly-' + slotName + '-' + Date.now();
  wrapper.id = divId;

  // Defer rendering until element is in DOM
  setTimeout(function() {
    try {
      // Extract content from <neven-plotly>...</neven-plotly> wrapper
      var tagStart = jsonStr.indexOf('<neven-plotly>');
      var tagEnd   = jsonStr.indexOf('</neven-plotly>');
      if (tagStart === -1 || tagEnd === -1) throw new Error('Tag not found');
      var encoded = jsonStr.substring(tagStart + 14, tagEnd).trim();

      // Decode base64 → JSON string → parse
      var jsonStr2;
      try {
        jsonStr2 = atob(encoded);
      } catch(e) {
        jsonStr2 = encoded; // fallback: treat as raw JSON
      }

      var figData = JSON.parse(jsonStr2);
      var traces  = figData.data  || [];
      var layout  = figData.layout || {};

      // Force dark theme regardless of what R produced
      layout.paper_bgcolor = '#373434';
      layout.plot_bgcolor  = '#373434';
      layout.font          = { color: '#888', size: 11 };
      layout.margin        = layout.margin || { t: 40, r: 20, b: 50, l: 60 };
      layout.autosize      = true;

      if (typeof Plotly !== 'undefined') {
        Plotly.newPlot(divId, traces, layout, {
          responsive:     true,
          displayModeBar: true,
          displaylogo:    false,
          modeBarButtonsToRemove: ['sendDataToCloud', 'editInChartStudio']
        });

        // Botón de descarga debajo del gráfico
        var dlRow = document.createElement('div');
        dlRow.style.cssText = 'display:flex;gap:6px;margin-top:6px;justify-content:flex-end';

        var btnPng = document.createElement('button');
        btnPng.className   = 'btn btn-primary';
        btnPng.style.fontSize = '10px';
        btnPng.textContent = '⬇ PNG';
        btnPng.addEventListener('click', function() {
          Plotly.downloadImage(divId, {
            format: 'png', width: 1200, height: 600,
            filename: slotName || 'neven-grafico'
          });
        });

        var btnSvg = document.createElement('button');
        btnSvg.className   = 'btn btn-secondary';
        btnSvg.style.fontSize = '10px';
        btnSvg.textContent = '⬇ SVG';
        btnSvg.addEventListener('click', function() {
          Plotly.downloadImage(divId, {
            format: 'svg', width: 1200, height: 600,
            filename: slotName || 'neven-grafico'
          });
        });

        dlRow.appendChild(btnPng);
        dlRow.appendChild(btnSvg);

        // Botón "Enviar a Slide"
        var btnPresent = document.createElement('button');
        btnPresent.className   = 'btn btn-secondary';
        btnPresent.style.fontSize = '10px';
        btnPresent.style.borderColor = 'var(--accent)';
        btnPresent.textContent = 'Enviar a Slide';
        // Capturar el HTML del slot (incluye el tag neven-plotly con el JSON base64)
        var _slotHtml = jsonStr;
        btnPresent.addEventListener('click', function() {
          // Construir HTML standalone del gráfico para el slide
          var slideHtml = [
            '<!DOCTYPE html><html><head>',
            '<meta charset="UTF-8">',
            '<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"><\/script>',
            '<style>',
            'body{margin:0;background:#373434;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden;}',
            '#chart{width:100%;height:100%;}',
            '<\/style>',
            '</head><body>',
            '<div id="chart"></div>',
            '<script>',
            'var encoded="' + encoded + '";',
            'var fig=JSON.parse(atob(encoded));',
            'var layout=fig.layout||{};',
            'layout.paper_bgcolor="#373434";layout.plot_bgcolor="#373434";',
            'layout.font={color:"#888"};layout.autosize=true;layout.margin={t:40,r:20,b:50,l:60};',
            'Plotly.newPlot("chart",fig.data||[],layout,{responsive:true,displayModeBar:true,displaylogo:false});',
            '<\/script>',
            '</body></html>'
          ].join('\n');

          // Enviar al padre (taskpane.html) que lo reenvía al iframe del editor
          window.parent.postMessage({
            type:       'NEVEN_ADD_SLIDE',
            plotlyData: JSON.parse(jsonStr2),   // JSON del gráfico Plotly
            slideTitle: slotName || 'Gráfico'
          }, window.location.origin);

          // Feedback visual
          btnPresent.textContent = '✓ Enviado';
          btnPresent.style.color = 'var(--accent)';
          setTimeout(function() {
            btnPresent.textContent = 'Enviar a Slide';
            btnPresent.style.color = '';
          }, 2000);
        });
        dlRow.appendChild(btnPresent);

        // El wrapper ya está en el DOM (adjuntado por buildSlotElement antes del setTimeout)
        if (wrapper.parentElement) {
          wrapper.parentElement.appendChild(dlRow);
        } else {
          // fallback: adjuntar al propio wrapper para que buildSlotElement lo mueva
          wrapper.appendChild(dlRow);
        }
      } else {
        wrapper.innerHTML = '<p style="color:#888;padding:12px">Plotly no disponible</p>';
      }
    } catch (e) {
      wrapper.innerHTML = '<p style="color:#ff4444;padding:12px">Error al renderizar gráfico: ' + e.message + '</p>';
    }
  }, 50);

  return wrapper;
}

// =============================================================================
// Helper — simple Markdown to HTML converter (no external deps)
// Supports: # headers, **bold**, *italic*, - bullets, • bullets, blank lines, LaTeX $...$ $$...$$
// =============================================================================
function _markdownToHtml(md) {
  var accent = 'var(--accent)';

  // ── Paso 1: extraer bloques LaTeX antes de escapar HTML ──────────────────
  var mathBlocks  = [];   // display math
  var mathInlines = [];   // inline math

  // Display math: $$...$$ o \[...\]
  md = md.replace(/\$\$([\s\S]+?)\$\$/g, function(_, tex) {
    var idx = mathBlocks.length;
    mathBlocks.push(tex.trim());
    return '\x00MATHD' + idx + '\x00';
  });
  md = md.replace(/\\\[([\s\S]+?)\\\]/g, function(_, tex) {
    var idx = mathBlocks.length;
    mathBlocks.push(tex.trim());
    return '\x00MATHD' + idx + '\x00';
  });

  // Inline math: $...$ (solo si parece fórmula) o \(...\)
  md = md.replace(/\$([^$\n]{1,300}?)\$/g, function(full, tex) {
    if (!/[\\^_{}=]/.test(tex)) return full;
    var idx = mathInlines.length;
    mathInlines.push(tex.trim());
    return '\x00MATHI' + idx + '\x00';
  });
  md = md.replace(/\\\(([^)]{1,500}?)\\\)/g, function(_, tex) {
    var idx = mathInlines.length;
    mathInlines.push(tex.trim());
    return '\x00MATHI' + idx + '\x00';
  });

  // Líneas sueltas de LaTeX sin delimitadores — el LLM las emite sin $...$
  // Detectar: línea que contiene 2+ comandos \cmd o 1 comando + signo =
  // Usar split por línea en lugar de regex multiline para evitar backtracking
  var mdLines2 = md.split('\n');
  md = mdLines2.map(function(line) {
    // Saltar líneas vacías, encabezados Markdown y placeholders ya procesados
    if (!line.trim()) return line;
    if (/^#{1,6}\s/.test(line.trim())) return line;
    if (line.indexOf('\x00MATH') !== -1) return line;
    // Contar comandos LaTeX \cmd en la línea
    var texCmdCount = (line.match(/\\[a-zA-Z]+/g) || []).length;
    if (texCmdCount === 0) return line;
    var hasEqual = line.indexOf('=') !== -1;

    // Caso A: línea que es MAYORMENTE LaTeX (empieza con \ o tiene pocos words no-LaTeX)
    // → tratar como display block
    var trimmed = line.trim();
    var startsWithCmd = /^\\[a-zA-Z]/.test(trimmed);
    var nonCmdWords = (trimmed.replace(/\\[a-zA-Z]+\{[^}]*\}/g, '')
                               .replace(/\\[a-zA-Z]+/g, '')
                               .match(/[a-zA-Z]{4,}/g) || []).length;
    var isPureFormula = startsWithCmd
                     || (texCmdCount >= 2 && nonCmdWords <= 1)
                     || (texCmdCount >= 2 && hasEqual);

    if (isPureFormula && (texCmdCount >= 2 || (texCmdCount >= 1 && hasEqual))) {
      var idx = mathBlocks.length;
      mathBlocks.push(trimmed);
      return '\x00MATHD' + idx + '\x00';
    }

    // Caso B: línea mixta con texto + fragmento(s) LaTeX
    // Estrategia: buscar secuencias \cmd... que no estén ya entre delimitadores
    // y envolverlas en $...$ para que KaTeX las renderice inline
    if (texCmdCount >= 1) {
      // Extraer fragmentos LaTeX: secuencias contiguas de \cmd, {}, ^, _, espacios y símbolos matemáticos
      // Separados del texto normal por espacios o puntuación
      var converted = line.replace(/((?:\\[a-zA-Z]+(?:\{[^}]*\})?(?:[_^][{a-zA-Z0-9}]+)?[\s]*)+(?:[=<>≈×%+\-\/][\s]*(?:\\[a-zA-Z]+(?:\{[^}]*\})?(?:[_^][{a-zA-Z0-9}]+)?[\s]*|[\d.]+[\s]*))*)/g, function(match) {
        var m = match.trim();
        if (!m || m.length < 2) return match;
        var inlineIdx = mathInlines.length;
        mathInlines.push(m);
        return ' \x00MATHI' + inlineIdx + '\x00 ';
      });
      if (converted !== line) return converted;
    }

    return line;
  }).join('\n');

  // ── Paso 2: parseo Markdown normal ───────────────────────────────────────
  var lines  = md.split('\n');
  var html   = '';
  var inList = false;
  var tableBuffer = [];  // acumula líneas de tabla GFM

  var _flushTable = function() {
    if (tableBuffer.length < 2) {
      // No es tabla válida — volcar como párrafos
      tableBuffer.forEach(function(l) {
        html += '<p style="margin:3px 0;color:var(--text-primary)">' + _inlineMd(l) + '</p>';
      });
      tableBuffer = [];
      return;
    }
    var header = tableBuffer[0];
    var sep    = tableBuffer[1];
    // Verificar que la segunda línea es un separador (---|:---|---)
    if (!/^[\|\s\-:]+$/.test(sep)) {
      tableBuffer.forEach(function(l) {
        html += '<p style="margin:3px 0;color:var(--text-primary)">' + _inlineMd(l) + '</p>';
      });
      tableBuffer = [];
      return;
    }
    var parseRow = function(line) {
      return line.replace(/^\||\|$/g, '').split('|').map(function(c){ return c.trim(); });
    };
    var headers = parseRow(header);
    var rows    = tableBuffer.slice(2).map(parseRow);

    var thtml = '<div style="overflow-x:auto;margin:8px 0">' +
      '<table style="width:100%;border-collapse:collapse;font-size:10px">' +
      '<thead><tr>' +
      headers.map(function(h) {
        return '<th style="background:rgba(215,165,56,0.12);color:var(--accent);' +
               'padding:4px 8px;text-align:left;border-bottom:1px solid rgba(215,165,56,0.3);' +
               'font-weight:600;white-space:nowrap">' + _inlineMd(h) + '</th>';
      }).join('') +
      '</tr></thead><tbody>' +
      rows.map(function(row, ri) {
        return '<tr style="background:' + (ri%2===0?'transparent':'rgba(255,255,255,0.02)') + '">' +
          row.map(function(cell) {
            return '<td style="padding:4px 8px;border-bottom:1px solid rgba(255,255,255,0.05);' +
                   'color:var(--text-primary)">' + _inlineMd(cell) + '</td>';
          }).join('') +
        '</tr>';
      }).join('') +
      '</tbody></table></div>';

    html += thtml;
    tableBuffer = [];
  };

  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];

    // Detectar líneas de tabla GFM (empiezan y/o terminan con |)
    var isTableLine = /^\s*\|/.test(line) || (/\|/.test(line) && /\|/.test(line.replace(/[^|]/g,'')));
    if (isTableLine && line.trim().startsWith('|')) {
      // Volcar lista si estaba abierta
      if (inList) { html += '</ul>'; inList = false; }
      tableBuffer.push(line);
      continue;
    } else if (tableBuffer.length > 0) {
      _flushTable();
    }

    // Close list if needed
    if (inList && !/^[\-\*•]\s/.test(line.trim()) && line.trim() !== '') {
      html += '</ul>';
      inList = false;
    }

    // H1
    if (/^#\s+/.test(line)) {
      html += '<h3 style="color:' + accent + ';font-size:13px;margin:10px 0 4px;font-weight:700">' +
              _inlineMd(line.replace(/^#+\s+/, '')) + '</h3>';
    // H2
    } else if (/^##\s+/.test(line)) {
      html += '<h4 style="color:' + accent + ';font-size:12px;margin:8px 0 3px;font-weight:600">' +
              _inlineMd(line.replace(/^#+\s+/, '')) + '</h4>';
    // H3-H6 → mismo nivel que H2 visualmente
    } else if (/^#{3,6}\s+/.test(line)) {
      html += '<h4 style="color:' + accent + ';font-size:12px;margin:8px 0 3px;font-weight:600">' +
              _inlineMd(line.replace(/^#+\s+/, '')) + '</h4>';
    // Bullet
    } else if (/^[\-\*•]\s/.test(line.trim())) {
      if (!inList) { html += '<ul style="margin:6px 0 6px 16px;padding:0">'; inList = true; }
      var bullet = line.trim().replace(/^[\-\*•]\s/, '');
      html += '<li style="margin:3px 0;color:var(--text-primary)">' + _inlineMd(bullet) + '</li>';
    // Blank line
    } else if (line.trim() === '') {
      if (!inList) html += '<div style="height:4px"></div>';
    // Normal paragraph
    } else {
      html += '<p style="margin:3px 0;color:var(--text-primary)">' + _inlineMd(line) + '</p>';
    }
  }
  if (inList) html += '</ul>';
  if (tableBuffer.length > 0) _flushTable();

  // ── Post-proceso: bloques especiales del agente IA ────────────────────────
  // neven-run: sugerencia ejecutable
  html = html.replace(
    /<pre[^>]*><code[^>]*class="language-neven-run"[^>]*>([\s\S]+?)<\/code><\/pre>/g,
    function(_, enc) {
      try {
        function dec(s){return s.replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').trim();}
        var spec = JSON.parse(dec(enc));
        return typeof _buildRunSuggestionCard === 'function'
          ? _buildRunSuggestionCard(spec)
          : '<pre><code>' + enc + '</code></pre>';
      } catch(e) { return '<pre><code>' + enc + '</code></pre>'; }
    }
  );

  // neven-create-function: el agente propone crear una función nueva
  html = html.replace(
    /<pre[^>]*><code[^>]*class="language-neven-create-function"[^>]*>([\s\S]+?)<\/code><\/pre>/g,
    function(_, enc) {
      return typeof window !== 'undefined' && typeof window._renderCreateFunctionBlock === 'function'
        ? window._renderCreateFunctionBlock(enc)
        : '<pre><code>' + enc + '</code></pre>';
    }
  );

  // ── Paso 3: reinyectar LaTeX renderizado con KaTeX ───────────────────────
  mathBlocks.forEach(function(tex, idx) {
    html = html.replace('\x00MATHD' + idx + '\x00', _renderKatex(tex, true));
  });
  mathInlines.forEach(function(tex, idx) {
    html = html.replace('\x00MATHI' + idx + '\x00', _renderKatex(tex, false));
  });

  return html;
}

function _renderKatex(tex, displayMode) {
  if (typeof katex !== 'undefined') {
    try {
      return katex.renderToString(tex, {
        displayMode:  displayMode,
        throwOnError: false,
        output:       'html',
        macros: { '\\R': '\\mathbb{R}', '\\E': '\\mathbb{E}',
                  '\\hat': '\\hat', '\\beta': '\\beta' }
      });
    } catch(e) { /* caer al fallback */ }
  }
  // Fallback: mostrar LaTeX como código coloreado si KaTeX no está listo
  var delim = displayMode ? '$$' : '$';
  var tag   = displayMode ? 'div' : 'span';
  var style = displayMode
    ? 'display:block;text-align:center;padding:6px 2px;' +
      'font-family:\'Cascadia Code\',Consolas,monospace;font-size:12px;color:var(--accent)'
    : 'font-family:\'Cascadia Code\',Consolas,monospace;font-size:11px;color:var(--accent)';
  return '<' + tag + ' style="' + style + '">' + delim + tex + delim + '</' + tag + '>';
}

function _inlineMd(text) {
  text = _escMd(text);
  // **bold**
  text = text.replace(/\*\*([^*]+)\*\*/g,
    '<strong style="color:var(--accent);font-weight:700">$1</strong>');
  // *italic*
  text = text.replace(/\*([^*]+)\*/g,
    '<em style="color:var(--text-secondary)">$1</em>');
  // `code`
  text = text.replace(/`([^`]+)`/g,
    '<code style="background:#2a2a2a;padding:1px 5px;border-radius:3px;' +
    'font-family:Consolas,monospace;font-size:11px;color:var(--accent)">$1</code>');
  return text;
}

function _escMd(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// =============================================================================
// Task 8.22 — renderSlotTable — TOP 10 + Mostrar todo + Descargar CSV
// =============================================================================
function renderSlotTable(rows, slotName) {
  if (!rows || rows.length === 0) {
    var empty = document.createElement('p');
    empty.style.color = 'var(--text-secondary)';
    empty.textContent = 'Sin datos.';
    return empty;
  }

  var TOP = 10;
  var columns = Object.keys(rows[0]);
  var wrapper = document.createElement('div');

  var tableWrap = document.createElement('div');
  tableWrap.style.overflow  = 'auto';
  tableWrap.style.maxHeight = '240px';

  var table = document.createElement('table');
  table.className = 'data-table';

  // thead
  var thead = document.createElement('thead');
  var hrow  = document.createElement('tr');
  columns.forEach(function(c) {
    var th = document.createElement('th');
    th.textContent = c;
    hrow.appendChild(th);
  });
  thead.appendChild(hrow);
  table.appendChild(thead);

  // tbody
  var tbody = document.createElement('tbody');

  function fillRows(limit) {
    tbody.innerHTML = '';
    for (var ri = 0; ri < Math.min(limit, rows.length); ri++) {
      var tr = document.createElement('tr');
      columns.forEach(function(c) {
        var td = document.createElement('td');
        var v  = rows[ri][c];
        td.textContent = v !== null && v !== undefined ? String(v) : '';
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    }
  }

  fillRows(Math.min(TOP, rows.length));
  table.appendChild(tbody);
  tableWrap.appendChild(table);
  wrapper.appendChild(tableWrap);

  // Meta
  var meta = document.createElement('div');
  meta.style.fontSize  = '10px';
  meta.style.color     = 'var(--text-secondary)';
  meta.style.marginTop = '4px';
  meta.textContent     = 'Mostrando ' + Math.min(TOP, rows.length) + ' de ' + rows.length + ' filas';
  wrapper.appendChild(meta);

  // Buttons
  var btnRow = document.createElement('div');
  btnRow.style.display   = 'flex';
  btnRow.style.gap       = '6px';
  btnRow.style.marginTop = '6px';

  if (rows.length > TOP) {
    var showAllBtn = document.createElement('button');
    showAllBtn.className   = 'btn btn-primary';
    showAllBtn.style.fontSize = '10px';
    showAllBtn.textContent = '▼ Mostrar todo (' + rows.length + ')';
    var expanded = false;
    showAllBtn.addEventListener('click', function() {
      expanded = !expanded;
      if (expanded) {
        fillRows(rows.length);
        tableWrap.style.maxHeight = '400px';
        meta.textContent = 'Mostrando ' + rows.length + ' de ' + rows.length + ' filas';
        showAllBtn.textContent = '▲ Mostrar menos';
      } else {
        fillRows(TOP);
        tableWrap.style.maxHeight = '240px';
        meta.textContent = 'Mostrando ' + TOP + ' de ' + rows.length + ' filas';
        showAllBtn.textContent = '▼ Mostrar todo (' + rows.length + ')';
      }
    });
    btnRow.appendChild(showAllBtn);
  }

  var dlBtn = document.createElement('button');
  dlBtn.className      = 'btn btn-primary';
  dlBtn.style.fontSize = '10px';
  dlBtn.textContent    = '⬇ Descargar CSV';
  dlBtn.addEventListener('click', function() {
    var header = columns.join(',');
    var csvRows = rows.map(function(row) {
      return columns.map(function(c) {
        var v = row[c];
        v = (v !== null && v !== undefined) ? String(v) : '';
        if (v.indexOf(',') !== -1 || v.indexOf('"') !== -1) v = '"' + v.replace(/"/g, '""') + '"';
        return v;
      }).join(',');
    });
    var csv  = header + '\n' + csvRows.join('\n');
    var blob = new Blob([csv], {type:'text/csv'});
    var a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = (slotName || 'data') + '.csv';
    a.click();
  });
  btnRow.appendChild(dlBtn);

  wrapper.appendChild(btnRow);
  return wrapper;
}

// =============================================================================
// Utility: HTML escaping helper
// =============================================================================
function _escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;')
    .replace(/'/g,  '&#39;');
}

// =============================================================================
// Initialize Data Lab when DOM is ready
// =============================================================================
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDataLab);
} else {
  initDataLab();
}
