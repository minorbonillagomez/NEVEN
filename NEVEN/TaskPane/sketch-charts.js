// =============================================================================
// NEVEN Sketch Charts - sketch-charts.js
// Modulo para convertir graficos Plotly a estilo sketchy usando Chart.js + plugin-rough
// Integrado con la paleta de NEVEN Studio
// =============================================================================

// Configuracion global del modulo
var SKETCH_CONFIG = {
  enabled: true,  // Se puede desactivar desde configuracion
  roughness: 2,   // Nivel de "temblor" en las lineas (1-4)
  fillStyle: 'hachure',  // hachure, cross-hatch, zigzag, solid
  fillWeight: 1,
  bowing: 1,      // Curvatura de lineas rectas
  
  // Paletas disponibles (sincronizadas con Quick Chart)
  palettes: {
    neven:   ['#a8e600', '#ff6b6b', '#4ecdc4', '#ffe66d', '#95e1d3', '#f38181', '#aa96da', '#fcbad3'],
    viridis: ['#440154', '#482878', '#3e4989', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6ece58'],
    plasma:  ['#0d0887', '#46039f', '#7201a8', '#9c179e', '#bd3786', '#d8576b', '#ed7953', '#fb9f3a'],
    rainbow: ['#e6194b', '#f58231', '#ffe119', '#3cb44b', '#42d4f4', '#4363d8', '#911eb4', '#f032e6'],
    pastel:  ['#ffb3ba', '#ffdfba', '#ffffba', '#baffc9', '#bae1ff', '#e8baff', '#ffbae8', '#baffff'],
    dark:    ['#1a535c', '#4ecdc4', '#ff6b6b', '#ffe66d', '#6b5b95', '#88d8b0', '#feb236', '#034f84'],
    ocean:   ['#05445e', '#189ab4', '#75e6da', '#d4f1f9', '#0077b6', '#00b4d8', '#90e0ef', '#caf0f8'],
    earth:   ['#8d6e63', '#a1887f', '#bcaaa4', '#d7ccc8', '#795548', '#6d4c41', '#5d4037', '#4e342e'],
    anthropic: ['#D97757', '#C46686', '#6A9BBC', '#BCD1CA', '#D4883A', '#8B7355', '#9B8AA6', '#A3B18A']
  }
};

// Storage key para persistir preferencias
var SKETCH_STORAGE_KEY = 'neven_sketch_enabled';

// Instancias de Chart.js activas (para destruir al cambiar)
var _sketchChartInstances = {};

// =============================================================================
// Inicializacion - cargar preferencia del usuario
// =============================================================================
function initSketchCharts() {
  var stored = localStorage.getItem(SKETCH_STORAGE_KEY);
  if (stored !== null) {
    SKETCH_CONFIG.enabled = stored === 'true';
  }
  // Cargar preferencias de estilo guardadas
  var savedRoughness = localStorage.getItem('neven_sketch_roughness');
  if (savedRoughness) SKETCH_CONFIG.roughness = parseFloat(savedRoughness);
  
  var savedFillStyle = localStorage.getItem('neven_sketch_fillstyle');
  if (savedFillStyle) SKETCH_CONFIG.fillStyle = savedFillStyle;
  
  var savedBowing = localStorage.getItem('neven_sketch_bowing');
  if (savedBowing) SKETCH_CONFIG.bowing = parseFloat(savedBowing);
  
  console.log('[SketchCharts] Initialized with Chart.js + plugin-rough, enabled:', SKETCH_CONFIG.enabled);
}

// =============================================================================
// Toggle para habilitar/deshabilitar el feature
// =============================================================================
function setSketchEnabled(enabled) {
  SKETCH_CONFIG.enabled = enabled;
  localStorage.setItem(SKETCH_STORAGE_KEY, enabled ? 'true' : 'false');
  console.log('[SketchCharts] Feature', enabled ? 'enabled' : 'disabled');
}

function isSketchEnabled() {
  return SKETCH_CONFIG.enabled;
}

// =============================================================================
// Obtener paleta activa del selector de Quick Chart o usar default
// =============================================================================
function _getSketchPalette() {
  var paletteSelect = document.getElementById('qc-palette');
  var paletteName = paletteSelect ? paletteSelect.value : 'neven';
  return SKETCH_CONFIG.palettes[paletteName] || SKETCH_CONFIG.palettes.neven;
}

// =============================================================================
// Detectar tipo de grafico desde datos Plotly
// =============================================================================
function _detectChartType(traces) {
  if (!traces || traces.length === 0) return 'unknown';
  
  var firstTrace = traces[0];
  var type = firstTrace.type || 'scatter';
  
  if (type === 'bar') return 'bar';
  if (type === 'scatter' && firstTrace.mode && firstTrace.mode.indexOf('lines') !== -1) return 'line';
  if (type === 'scatter') return 'scatter';
  if (type === 'pie') return 'pie';
  if (type === 'histogram') return 'bar';
  
  return type;
}

// =============================================================================
// Convertir datos Plotly a formato Chart.js
// =============================================================================
function _convertPlotlyToChartJS(plotlyData, chartType) {
  var traces = plotlyData.data || [];
  var layout = plotlyData.layout || {};
  var colors = _getSketchPalette();
  
  if (traces.length === 0) return null;
  
  var title = layout.title ? (typeof layout.title === 'string' ? layout.title : layout.title.text || '') : '';
  var xLabel = layout.xaxis && layout.xaxis.title ? (typeof layout.xaxis.title === 'string' ? layout.xaxis.title : layout.xaxis.title.text || '') : '';
  var yLabel = layout.yaxis && layout.yaxis.title ? (typeof layout.yaxis.title === 'string' ? layout.yaxis.title : layout.yaxis.title.text || '') : '';
  
  var labels = [];
  var datasets = [];
  
  switch (chartType) {
    case 'bar':
      // Usar labels del primer trace
      labels = traces[0].x || [];
      
      // Crear dataset por cada trace
      traces.forEach(function(trace, i) {
        var color = colors[i % colors.length];
        datasets.push({
          label: trace.name || ('Serie ' + (i + 1)),
          data: trace.y || [],
          backgroundColor: color,
          borderColor: color,
          borderWidth: 2,
          rough: {
            roughness: SKETCH_CONFIG.roughness,
            bowing: SKETCH_CONFIG.bowing,
            fillStyle: SKETCH_CONFIG.fillStyle,
            fillWeight: SKETCH_CONFIG.fillWeight
          }
        });
      });
      break;
      
    case 'line':
    case 'scatter':
      // Para lineas/scatter, usar x como labels
      labels = traces[0].x || [];
      
      traces.forEach(function(trace, i) {
        var color = colors[i % colors.length];
        datasets.push({
          label: trace.name || ('Serie ' + (i + 1)),
          data: trace.y || [],
          backgroundColor: 'transparent',
          borderColor: color,
          borderWidth: 3,
          fill: false,
          pointBackgroundColor: color,
          pointBorderColor: color,
          pointRadius: chartType === 'scatter' ? 6 : 3,
          rough: {
            roughness: SKETCH_CONFIG.roughness,
            bowing: SKETCH_CONFIG.bowing
          }
        });
      });
      break;
      
    case 'pie':
      var firstTrace = traces[0];
      labels = firstTrace.labels || [];
      var values = firstTrace.values || [];
      var pieColors = colors.slice(0, labels.length);
      
      datasets.push({
        data: values,
        backgroundColor: pieColors,
        borderColor: pieColors,
        borderWidth: 2,
        rough: {
          roughness: SKETCH_CONFIG.roughness,
          bowing: SKETCH_CONFIG.bowing,
          fillStyle: SKETCH_CONFIG.fillStyle,
          fillWeight: SKETCH_CONFIG.fillWeight
        }
      });
      break;
      
    default:
      return null;
  }
  
  return {
    type: chartType === 'scatter' ? 'line' : chartType,  // Chart.js usa 'line' para scatter
    data: {
      labels: labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      // Deshabilitar tooltips para evitar error de fillOptions en plugin-rough
      tooltips: {
        enabled: false
      },
      title: {
        display: !!title,
        text: title,
        fontColor: '#e0e0e0',
        fontSize: 14
      },
      legend: {
        display: datasets.length > 1 || chartType === 'pie',
        position: chartType === 'pie' ? 'right' : 'top',
        labels: {
          fontColor: '#ccc',
          fontSize: 11
        }
      },
      scales: chartType !== 'pie' ? {
        xAxes: [{
          scaleLabel: {
            display: !!xLabel,
            labelString: xLabel,
            fontColor: '#aaa'
          },
          ticks: {
            fontColor: '#999'
          },
          gridLines: {
            color: 'rgba(255,255,255,0.1)'
          }
        }],
        yAxes: [{
          scaleLabel: {
            display: !!yLabel,
            labelString: yLabel,
            fontColor: '#aaa'
          },
          ticks: {
            fontColor: '#999',
            beginAtZero: true
          },
          gridLines: {
            color: 'rgba(255,255,255,0.1)'
          }
        }]
      } : undefined,
      plugins: {
        rough: {
          roughness: SKETCH_CONFIG.roughness,
          bowing: SKETCH_CONFIG.bowing,
          fillStyle: SKETCH_CONFIG.fillStyle,
          fillWeight: SKETCH_CONFIG.fillWeight
        }
      }
    },
    plugins: [ChartRough]
  };
}

// =============================================================================
// Renderizar grafico sketchy con Chart.js
// =============================================================================
function renderSketchChart(containerId, plotlyData, options) {
  options = options || {};
  
  var container = document.getElementById(containerId);
  if (!container) {
    console.error('[SketchCharts] Container not found:', containerId);
    return false;
  }
  
  // Detectar tipo de grafico
  var chartType = _detectChartType(plotlyData.data);
  console.log('[SketchCharts] Rendering', chartType, 'chart with', plotlyData.data.length, 'series');
  
  // Convertir datos
  var chartConfig = _convertPlotlyToChartJS(plotlyData, chartType);
  if (!chartConfig) {
    console.error('[SketchCharts] Could not convert data for chart type:', chartType);
    container.innerHTML = '<p style="color:#888;padding:20px;text-align:center">Este tipo de grafico no soporta vista Sketch</p>';
    return false;
  }
  
  // Destruir instancia anterior si existe
  if (_sketchChartInstances[containerId]) {
    _sketchChartInstances[containerId].destroy();
    delete _sketchChartInstances[containerId];
  }
  
  // Preparar contenedor
  container.innerHTML = '';
  container.style.background = '#2a2a2a';
  container.style.borderRadius = '8px';
  container.style.padding = '12px';
  container.style.position = 'relative';
  
  // Crear canvas para Chart.js
  var canvas = document.createElement('canvas');
  canvas.id = containerId + '-canvas';
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  container.appendChild(canvas);
  
  // Configurar altura del contenedor
  container.style.height = (options.height || 350) + 'px';
  
  try {
    // Crear grafico Chart.js con plugin rough
    var ctx = canvas.getContext('2d');
    var chart = new Chart(ctx, chartConfig);
    
    // Guardar referencia para destruir despues
    _sketchChartInstances[containerId] = chart;
    
    console.log('[SketchCharts] Chart rendered successfully');
    return true;
    
  } catch (e) {
    console.error('[SketchCharts] Error rendering chart:', e);
    container.innerHTML = '<p style="color:#f66;padding:20px;text-align:center">Error al renderizar: ' + e.message + '</p>';
    return false;
  }
}

// =============================================================================
// Crear panel flotante de configuracion Sketch
// =============================================================================
function _createSketchConfigPanel(containerId, plotlyData, onUpdate) {
  var panelId = containerId + '-config';
  
  // Remover panel existente si hay
  var existing = document.getElementById(panelId);
  if (existing) existing.remove();
  
  var panel = document.createElement('div');
  panel.id = panelId;
  panel.style.cssText = 'position:absolute;top:8px;right:8px;z-index:100;font-size:10px;color:#ccc';
  
  // Estado colapsado desde localStorage
  var isCollapsed = localStorage.getItem('neven_sketch_panel_collapsed') === 'true';
  
  panel.innerHTML = 
    // Boton toggle siempre visible
    '<button id="' + panelId + '-toggle" style="background:#333;border:1px solid #555;border-radius:4px;padding:4px 8px;color:#a8e600;font-size:10px;cursor:pointer" title="Mostrar/ocultar opciones">' +
      (isCollapsed ? '+ Estilo' : '- Estilo') +
    '</button>' +
    // Contenido colapsable
    '<div id="' + panelId + '-body" style="background:#333;border:1px solid #555;border-radius:6px;padding:8px 10px;margin-top:4px;min-width:140px;' + (isCollapsed ? 'display:none' : '') + '">' +
    // Textura (fillStyle)
    '<label style="display:block;margin-bottom:4px">Textura</label>' +
    '<select id="' + panelId + '-fill" style="width:100%;background:#222;color:#ccc;border:1px solid #555;border-radius:3px;padding:3px;font-size:10px;margin-bottom:8px">' +
      '<option value="hachure"' + (SKETCH_CONFIG.fillStyle === 'hachure' ? ' selected' : '') + '>Lineas</option>' +
      '<option value="solid"' + (SKETCH_CONFIG.fillStyle === 'solid' ? ' selected' : '') + '>Solido</option>' +
      '<option value="zigzag"' + (SKETCH_CONFIG.fillStyle === 'zigzag' ? ' selected' : '') + '>Zigzag</option>' +
      '<option value="cross-hatch"' + (SKETCH_CONFIG.fillStyle === 'cross-hatch' ? ' selected' : '') + '>Cruzado</option>' +
      '<option value="dots"' + (SKETCH_CONFIG.fillStyle === 'dots' ? ' selected' : '') + '>Puntos</option>' +
    '</select>' +
    // Roughness
    '<label style="display:block;margin-bottom:4px">Temblor: <span id="' + panelId + '-rv">' + SKETCH_CONFIG.roughness + '</span></label>' +
    '<input type="range" id="' + panelId + '-rough" min="0.5" max="4" step="0.5" value="' + SKETCH_CONFIG.roughness + '" style="width:100%;margin-bottom:8px">' +
    // Bowing
    '<label style="display:block;margin-bottom:4px">Curvatura: <span id="' + panelId + '-bv">' + SKETCH_CONFIG.bowing + '</span></label>' +
    '<input type="range" id="' + panelId + '-bow" min="0" max="3" step="0.5" value="' + SKETCH_CONFIG.bowing + '" style="width:100%">' +
    '</div>';  // Cierra body colapsable
  
  // Event listeners
  setTimeout(function() {
    // Toggle colapsar/expandir
    var toggleBtn = document.getElementById(panelId + '-toggle');
    var bodyDiv = document.getElementById(panelId + '-body');
    if (toggleBtn && bodyDiv) {
      toggleBtn.addEventListener('click', function() {
        var isHidden = bodyDiv.style.display === 'none';
        bodyDiv.style.display = isHidden ? 'block' : 'none';
        toggleBtn.textContent = isHidden ? '- Estilo' : '+ Estilo';
        localStorage.setItem('neven_sketch_panel_collapsed', isHidden ? 'false' : 'true');
      });
    }
    
    var fillSel = document.getElementById(panelId + '-fill');
    var roughSlider = document.getElementById(panelId + '-rough');
    var bowSlider = document.getElementById(panelId + '-bow');
    var roughVal = document.getElementById(panelId + '-rv');
    var bowVal = document.getElementById(panelId + '-bv');
    
    if (fillSel) {
      fillSel.addEventListener('change', function() {
        SKETCH_CONFIG.fillStyle = fillSel.value;
        localStorage.setItem('neven_sketch_fillstyle', fillSel.value);
        if (onUpdate) onUpdate();
      });
    }
    
    if (roughSlider) {
      roughSlider.addEventListener('input', function() {
        roughVal.textContent = roughSlider.value;
      });
      roughSlider.addEventListener('change', function() {
        SKETCH_CONFIG.roughness = parseFloat(roughSlider.value);
        localStorage.setItem('neven_sketch_roughness', roughSlider.value);
        if (onUpdate) onUpdate();
      });
    }
    
    if (bowSlider) {
      bowSlider.addEventListener('input', function() {
        bowVal.textContent = bowSlider.value;
      });
      bowSlider.addEventListener('change', function() {
        SKETCH_CONFIG.bowing = parseFloat(bowSlider.value);
        localStorage.setItem('neven_sketch_bowing', bowSlider.value);
        if (onUpdate) onUpdate();
      });
    }
  }, 10);
  
  return panel;
}

// =============================================================================
// Crear boton "Sketch" - ESTILO ALINEADO CON LA APP
// =============================================================================
function createSketchButton(plotlyData, plotlyContainerId, slotName) {
  if (!SKETCH_CONFIG.enabled) return null;
  
  var btn = document.createElement('button');
  btn.className = 'btn btn-secondary';
  btn.style.cssText = 'font-size:10px;padding:4px 10px;margin-left:6px';
  btn.textContent = 'Sketch';
  btn.title = 'Ver grafico con estilo sketchy/tiza';
  
  // Estado del toggle
  var isSketchMode = false;
  var originalContainer = null;
  var sketchContainer = null;
  var configPanel = null;
  
  btn.addEventListener('click', function() {
    isSketchMode = !isSketchMode;
    
    originalContainer = document.getElementById(plotlyContainerId);
    if (!originalContainer) return;
    
    var parent = originalContainer.parentElement;
    
    if (isSketchMode) {
      // Cambiar a modo Sketch
      btn.textContent = 'Plotly';
      btn.title = 'Volver a grafico Plotly';
      btn.classList.remove('btn-secondary');
      btn.classList.add('btn-primary');
      
      // Ocultar Plotly
      originalContainer.style.display = 'none';
      
      // Crear contenedor para sketch si no existe
      var sketchId = plotlyContainerId + '-sketch';
      sketchContainer = document.getElementById(sketchId);
      if (!sketchContainer) {
        sketchContainer = document.createElement('div');
        sketchContainer.id = sketchId;
        sketchContainer.style.cssText = 'width:100%;min-height:300px;position:relative';
        parent.insertBefore(sketchContainer, originalContainer.nextSibling);
      }
      sketchContainer.style.display = 'block';
      
      // Funcion para re-renderizar cuando cambian opciones
      var rerender = function() {
        // Preservar el panel de config
        var existingPanel = document.getElementById(sketchId + '-config');
        renderSketchChart(sketchId, plotlyData);
        // Re-agregar panel despues de re-render
        if (existingPanel) {
          var container = document.getElementById(sketchId);
          if (container) {
            container.appendChild(_createSketchConfigPanel(sketchId, plotlyData, rerender));
          }
        }
      };
      
      // Cargar Chart.js + plugin si no estan cargados
      loadChartJsRough(function() {
        renderSketchChart(sketchId, plotlyData);
        // Agregar panel de configuracion flotante
        var container = document.getElementById(sketchId);
        if (container) {
          configPanel = _createSketchConfigPanel(sketchId, plotlyData, rerender);
          container.appendChild(configPanel);
        }
      });
      
    } else {
      // Volver a modo Plotly
      btn.textContent = 'Sketch';
      btn.title = 'Ver grafico con estilo sketchy/tiza';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-secondary');
      
      // Mostrar Plotly
      originalContainer.style.display = 'block';
      
      // Ocultar sketch (el panel se oculta con el contenedor)
      if (sketchContainer) {
        sketchContainer.style.display = 'none';
      }
    }
  });
  
  return btn;
}

// =============================================================================
// Cargar Chart.js 2.x + Rough.js + plugin desde CDN (lazy loading)
// =============================================================================
var _chartJsRoughLoading = false;
var _chartJsRoughCallbacks = [];

function loadChartJsRough(callback) {
  // Ya cargado
  if (typeof Chart !== 'undefined' && typeof ChartRough !== 'undefined') {
    if (callback) callback();
    return;
  }
  
  // En proceso de carga
  if (_chartJsRoughLoading) {
    if (callback) _chartJsRoughCallbacks.push(callback);
    return;
  }
  
  _chartJsRoughLoading = true;
  if (callback) _chartJsRoughCallbacks.push(callback);
  
  console.log('[SketchCharts] Loading Chart.js + Rough.js + plugin from CDN...');
  
  // Secuencia: Chart.js 2.9.4 -> Rough.js -> Plugin
  _loadScript('https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js', function() {
    console.log('[SketchCharts] Chart.js 2.9.4 loaded');
    
    _loadScript('https://cdn.jsdelivr.net/npm/roughjs@4.5.2/bundled/rough.min.js', function() {
      console.log('[SketchCharts] Rough.js loaded');
      
      _loadScript('https://cdn.jsdelivr.net/npm/chartjs-plugin-rough@0.2.0/dist/chartjs-plugin-rough.min.js', function() {
        console.log('[SketchCharts] chartjs-plugin-rough loaded');
        
        // Configurar defaults para tema oscuro
        if (typeof Chart !== 'undefined') {
          Chart.defaults.global.defaultFontColor = '#ccc';
          Chart.defaults.global.defaultFontFamily = 'system-ui, -apple-system, sans-serif';
        }
        
        _chartJsRoughLoading = false;
        for (var i = 0; i < _chartJsRoughCallbacks.length; i++) {
          _chartJsRoughCallbacks[i]();
        }
        _chartJsRoughCallbacks = [];
      });
    });
  });
}

function _loadScript(src, onload) {
  var script = document.createElement('script');
  script.src = src;
  script.onload = onload;
  script.onerror = function() {
    console.error('[SketchCharts] Failed to load:', src);
    _chartJsRoughLoading = false;
  };
  document.head.appendChild(script);
}

// Inicializar al cargar
if (typeof window !== 'undefined') {
  initSketchCharts();
}
