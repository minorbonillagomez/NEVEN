// ═══════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Tab Ayuda / Diccionario de Funciones NevenX
// Archivo: ayuda.js
// ═══════════════════════════════════════════════════════════════════════════

console.log('[AYUDA] Cargando ayuda.js...');

var _ayudaCatalogo = null;
var _ayudaFunciones = {};

// Cargar catálogo desde el servidor
function _ayudaLoadCatalogo() {
  console.log('[AYUDA] Iniciando carga de catálogo...');
  var loading = document.getElementById('ayuda-loading');
  var errorEl = document.getElementById('ayuda-error');
  var catalogo = document.getElementById('ayuda-catalogo');
  var detalle = document.getElementById('ayuda-detalle');
  
  if (!loading || !catalogo) {
    console.error('[AYUDA] Elementos DOM no encontrados');
    return;
  }
  
  loading.style.display = 'block';
  errorEl.style.display = 'none';
  catalogo.innerHTML = '';
  detalle.style.display = 'none';
  
  var url = (window.API || window.location.origin) + '/api/ayuda/funciones';
  console.log('[AYUDA] Fetching:', url);
  
  fetch(url)
    .then(function(r) { 
      console.log('[AYUDA] Response status:', r.status);
      return r.json(); 
    })
    .then(function(data) {
      console.log('[AYUDA] Data recibida:', data.status, 'Total:', data.total);
      loading.style.display = 'none';
      
      if (data.status !== 'ok') {
        errorEl.textContent = data.error || 'Error desconocido';
        errorEl.style.display = 'block';
        return;
      }
      
      _ayudaCatalogo = data;
      _ayudaFunciones = {};
      
      Object.keys(data.familias).forEach(function(fam) {
        data.familias[fam].funciones.forEach(function(fn) {
          _ayudaFunciones[fn.id] = fn;
          _ayudaFunciones[fn.id]._familia = fam;
          _ayudaFunciones[fn.id]._familiaLabel = data.familias[fam].label;
        });
      });
      
      console.log('[AYUDA] Renderizando', Object.keys(_ayudaFunciones).length, 'funciones');
      _ayudaRenderCatalogo(data);
    })
    .catch(function(e) {
      console.error('[AYUDA] Error:', e);
      loading.style.display = 'none';
      errorEl.textContent = 'Error de conexión: ' + e.message;
      errorEl.style.display = 'block';
    });
}

function _ayudaRenderCatalogo(data, filtro) {
  var catalogo = document.getElementById('ayuda-catalogo');
  catalogo.innerHTML = '';
  
  var familias = Object.keys(data.familias).sort();
  var totalVisible = 0;
  
  familias.forEach(function(famId) {
    var familia = data.familias[famId];
    var funciones = familia.funciones;
    
    if (filtro) {
      var f = filtro.toLowerCase();
      funciones = funciones.filter(function(fn) {
        return fn.name.toLowerCase().indexOf(f) !== -1 ||
               fn.description.toLowerCase().indexOf(f) !== -1 ||
               fn.function_name_xll.toLowerCase().indexOf(f) !== -1 ||
               fn.id.toLowerCase().indexOf(f) !== -1 ||
               fn.id.toLowerCase().replace(/_/g, '').indexOf(f.replace(/[_.\s]/g, '')) !== -1 ||
               fn.function_name_xll.toLowerCase().replace(/[_.]/g, '').indexOf(f.replace(/[_.\s()]/g, '')) !== -1;
      });
    }
    
    if (funciones.length === 0) return;
    totalVisible += funciones.length;
    
    var details = document.createElement('details');
    details.className = 'ayuda-familia';
    details.open = false;  // Cerrado por defecto, usuario decide abrir
    
    var summary = document.createElement('summary');
    summary.className = 'ayuda-familia-header';
    summary.innerHTML = '<span class="ayuda-familia-label">' + familia.label + '</span>' +
                        '<span class="ayuda-familia-count">' + funciones.length + '</span>';
    details.appendChild(summary);
    
    var lista = document.createElement('div');
    lista.className = 'ayuda-funciones-lista';
    
    funciones.forEach(function(fn) {
      var item = document.createElement('div');
      item.className = 'ayuda-funcion-item';
      item.setAttribute('data-fn-id', fn.id);
      
      var langIcon = '[R]';
      if (fn.languages && fn.languages.length > 0) {
        var lang = fn.languages[0].toLowerCase();
        if (lang === 'r') langIcon = '[R]';
        else if (lang === 'python') langIcon = '[Py]';
        else if (lang === 'julia') langIcon = '[Jl]';
      }
      
      item.innerHTML = 
        '<div class="ayuda-funcion-header">' +
          '<span class="ayuda-funcion-icon">' + langIcon + '</span>' +
          '<span class="ayuda-funcion-nombre">' + fn.name + '</span>' +
          '<code class="ayuda-funcion-xll">' + fn.function_name_xll + '</code>' +
        '</div>' +
        '<div class="ayuda-funcion-desc">' + _truncate(fn.description, 100) + '</div>';
      
      item.onclick = function() { _ayudaMostrarDetalle(fn.id); };
      lista.appendChild(item);
    });
    
    details.appendChild(lista);
    catalogo.appendChild(details);
  });
  
  if (totalVisible === 0 && filtro) {
    catalogo.innerHTML = '<div class="msg-info" style="margin-top:10px">No se encontraron funciones para "' + filtro + '"</div>';
  }
}

function _truncate(text, maxLen) {
  if (!text) return '';
  return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
}

function _ayudaMostrarDetalle(fnId) {
  var fn = _ayudaFunciones[fnId];
  if (!fn) return;
  
  var detalle = document.getElementById('ayuda-detalle');
  
  document.getElementById('ayuda-detalle-nombre').textContent = fn.name;
  document.getElementById('ayuda-detalle-familia').textContent = fn._familiaLabel + ' (' + fn._familia + ')';
  document.getElementById('ayuda-detalle-desc').textContent = fn.description || '';
  
  var sintaxis = _ayudaBuildSintaxis(fn);
  document.getElementById('ayuda-detalle-sintaxis').textContent = sintaxis;
  
  document.getElementById('ayuda-detalle-params').innerHTML = _ayudaRenderParams(fn.nevenx_positions);
  document.getElementById('ayuda-detalle-outputs').innerHTML = _ayudaRenderOutputs(fn.tipo_outputs);
  
  var rolesSection = document.getElementById('ayuda-detalle-roles-section');
  if (fn.variable_roles && Object.keys(fn.variable_roles).length > 0) {
    document.getElementById('ayuda-detalle-roles').innerHTML = _ayudaRenderRoles(fn.variable_roles);
    rolesSection.style.display = 'block';
  } else {
    rolesSection.style.display = 'none';
  }
  
  var wikiDiv = document.getElementById('ayuda-detalle-wiki');
  if (fn.wikipedia_url) {
    document.getElementById('ayuda-detalle-wiki-link').href = fn.wikipedia_url;
    wikiDiv.style.display = 'block';
  } else {
    wikiDiv.style.display = 'none';
  }
  
  detalle.style.display = 'block';
  detalle.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function _ayudaBuildSintaxis(fn) {
  var xll = fn.function_name_xll;
  var params = fn.nevenx_positions || {};
  
  var positions = Object.keys(params).sort(function(a, b) {
    return parseInt(a.replace('a', ''), 10) - parseInt(b.replace('a', ''), 10);
  });
  
  var paramList = positions.map(function(pos) {
    var p = params[pos];
    var name = p.name || pos;
    return p.required ? name : '[' + name + ']';
  });
  
  var motor = 'R';
  if (fn.languages && fn.languages.length > 0) {
    var lang = fn.languages[0].toLowerCase();
    if (lang === 'python') motor = 'P';
    else if (lang === 'julia') motor = 'J';
  }
  
  return '=NEVEN.' + motor + '("' + xll + '", ' + paramList.join(', ') + ', TipoOutput)';
}

function _ayudaRenderParams(params) {
  if (!params || Object.keys(params).length === 0) {
    return '<div style="color:var(--text-muted);font-style:italic">Sin parámetros adicionales</div>';
  }
  
  var positions = Object.keys(params).sort(function(a, b) {
    return parseInt(a.replace('a', ''), 10) - parseInt(b.replace('a', ''), 10);
  });
  
  var html = '<table class="ayuda-params-table">' +
    '<tr><th>Pos</th><th>Nombre</th><th>Descripción</th><th>Tipo</th><th>Req</th><th>Default</th></tr>';
  
  positions.forEach(function(pos) {
    var p = params[pos];
    var req = p.required ? '✓' : '';
    var def = p.default !== null && p.default !== undefined ? String(p.default) : '—';
    html += '<tr>' +
      '<td style="color:var(--accent)">' + pos + '</td>' +
      '<td><strong>' + (p.name || '—') + '</strong></td>' +
      '<td>' + (p.label || '—') + '</td>' +
      '<td>' + (p.type || '—') + '</td>' +
      '<td style="text-align:center">' + req + '</td>' +
      '<td>' + def + '</td>' +
    '</tr>';
  });
  
  return html + '</table>';
}

function _ayudaRenderOutputs(outputs) {
  if (!outputs || outputs.length === 0) {
    return '<div style="color:var(--text-muted);font-style:italic">Sin tipos de output definidos</div>';
  }
  
  var html = '<table class="ayuda-outputs-table">' +
    '<tr><th style="width:40px">ID</th><th>Descripción</th></tr>';
  
  outputs.forEach(function(o) {
    html += '<tr>' +
      '<td style="color:var(--accent);font-weight:600;text-align:center">' + o.id + '</td>' +
      '<td>' + o.label + '</td>' +
    '</tr>';
  });
  
  return html + '</table>';
}

function _ayudaRenderRoles(roles) {
  var html = '<table class="ayuda-roles-table">' +
    '<tr><th>Rol</th><th>Descripción</th><th>Tipos</th><th>Múltiple</th><th>Req</th></tr>';
  
  Object.keys(roles).forEach(function(rolId) {
    var r = roles[rolId];
    var tipos = (r.types || []).join(', ');
    html += '<tr>' +
      '<td style="color:var(--accent);font-weight:600">' + rolId + '</td>' +
      '<td>' + (r.label || '—') + '</td>' +
      '<td>' + (tipos || '—') + '</td>' +
      '<td style="text-align:center">' + (r.multiple ? '✓' : '') + '</td>' +
      '<td style="text-align:center">' + (r.required ? '✓' : '') + '</td>' +
    '</tr>';
  });
  
  return html + '</table>';
}

// Inicializar cuando el DOM esté listo
(function initAyudaTab() {
  console.log('[AYUDA] Inicializando tab...');
  
  var reloadBtn = document.getElementById('ayuda-reload-btn');
  if (reloadBtn) {
    reloadBtn.onclick = function() { _ayudaLoadCatalogo(); };
  }
  
  var searchInput = document.getElementById('ayuda-search');
  var searchTimeout = null;
  if (searchInput) {
    searchInput.oninput = function() {
      clearTimeout(searchTimeout);
      var val = searchInput.value.trim();
      searchTimeout = setTimeout(function() {
        if (_ayudaCatalogo) {
          _ayudaRenderCatalogo(_ayudaCatalogo, val || null);
        }
      }, 250);
    };
  }
  
  var cerrarBtn = document.getElementById('ayuda-detalle-cerrar');
  if (cerrarBtn) {
    cerrarBtn.onclick = function() {
      document.getElementById('ayuda-detalle').style.display = 'none';
    };
  }
  
  var copiarBtn = document.getElementById('ayuda-copiar-sintaxis');
  if (copiarBtn) {
    copiarBtn.onclick = function() {
      var sintaxis = document.getElementById('ayuda-detalle-sintaxis').textContent;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(sintaxis).then(function() {
          if (typeof showToast === 'function') showToast('✓ Sintaxis copiada');
        });
      }
    };
  }
  
  // Cargar automáticamente cuando se hace clic en el tab
  document.querySelectorAll('.tab').forEach(function(t) {
    if (t.dataset.tab === 'ayuda') {
      t.addEventListener('click', function() {
        console.log('[AYUDA] Click en tab detectado');
        if (!_ayudaCatalogo) {
          _ayudaLoadCatalogo();
        }
      });
    }
  });
  
  // Cargar automáticamente si el tab ya está visible
  setTimeout(function() {
    var ayudaContent = document.getElementById('ayuda');
    if (ayudaContent && ayudaContent.classList.contains('active') && !_ayudaCatalogo) {
      console.log('[AYUDA] Tab activo al cargar');
      _ayudaLoadCatalogo();
    }
  }, 1000);
  
  console.log('[AYUDA] Tab inicializado correctamente');
})();

// Exponer función globalmente
window.recargarAyuda = function() {
  _ayudaCatalogo = null;
  _ayudaLoadCatalogo();
};

console.log('[AYUDA] ayuda.js cargado completamente');
