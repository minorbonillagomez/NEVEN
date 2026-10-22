// ═══════════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Chart Gallery (Ontología de Gráficos anyplot)
// ═══════════════════════════════════════════════════════════════════════════════
// Modal de galería para explorar 325+ tipos de gráficos con búsqueda semántica,
// filtrado por categoría/librería, y generación de código.
//
// Endpoints API:
//   GET /api/charts             → Lista todos los gráficos
//   GET /api/charts/search?q=   → Búsqueda por texto
//   GET /api/charts/recommend   → Recomendación por datos
//   GET /api/charts/stats       → Estadísticas
//   GET /api/charts/{id}        → Detalles de un gráfico
//   GET /api/charts/{id}/code   → Código de implementación
// ═══════════════════════════════════════════════════════════════════════════════

(function() {
  'use strict';
  
  // API_BASE: usar la misma lógica que taskpane.js
  const API_BASE = window.location.protocol === 'file:'
    ? (window._NEVEN_API_BASE || 'http://localhost:5555')
    : (window.API_BASE || window.location.origin);
  
  console.log('[ChartGallery] API_BASE:', API_BASE, 'protocol:', window.location.protocol);
  
  // Estado del módulo
  let _galleryModal = null;
  let _allCharts = [];
  let _filteredCharts = [];
  let _currentFilter = { category: 'all', library: 'all', search: '', classification: 'standard' };
  let _stats = null;
  let _currentLang = 'es';
  
  // Estado del gráfico actualmente renderizado (para re-ejecutar al cambiar paleta)
  let _currentRenderedChart = null; // { library, code, previewSection }
  
  // Categorías de gráficos (mapeadas desde los tipos)
  const CATEGORIES = {
    user: { en: 'My Charts', es: 'Mis Gráficos', types: [], isUserCategory: true },
    basic: { en: 'Basic', es: 'Básicos', types: ['bar', 'line', 'scatter', 'pie', 'area'] },
    statistical: { en: 'Statistical', es: 'Estadísticos', types: ['histogram', 'boxplot', 'violin', 'density', 'qq'] },
    correlation: { en: 'Correlation', es: 'Correlación', types: ['heatmap', 'correlogram', 'bubble'] },
    distribution: { en: 'Distribution', es: 'Distribución', types: ['histogram', 'density', 'ridge', 'joy'] },
    comparison: { en: 'Comparison', es: 'Comparación', types: ['bar', 'grouped', 'stacked', 'lollipop', 'dumbbell'] },
    timeseries: { en: 'Time Series', es: 'Series Temporales', types: ['line', 'area', 'candlestick', 'ohlc'] },
    hierarchy: { en: 'Hierarchy', es: 'Jerarquía', types: ['treemap', 'sunburst', 'dendrogram', 'tree'] },
    flow: { en: 'Flow', es: 'Flujo', types: ['sankey', 'chord', 'alluvial'] },
    geospatial: { en: 'Geospatial', es: 'Geoespacial', types: ['map', 'choropleth', 'bubble-map'] },
    other: { en: 'Other', es: 'Otros', types: [] }
  };
  
  // Estado de gráficos del usuario
  let _userCharts = [];
  
  // Librerías soportadas
  const LIBRARIES = {
    python: ['matplotlib', 'plotly', 'seaborn', 'altair', 'bokeh', 'plotnine', 'pygal', 'letsplot'],
    r: ['ggplot2'],
    julia: ['makie'],
    javascript: ['chartjs', 'd3', 'echarts', 'highcharts', 'muix']
  };
  
  // ─── Inicialización ────────────────────────────────────────────────────────
  
  async function init() {
    // Detectar idioma
    _currentLang = (typeof i18n !== 'undefined' && i18n.currentLang) || 'es';
    
    // Cargar estadísticas
    try {
      const resp = await fetch(`${API_BASE}/api/charts/stats`);
      if (resp.ok) {
        _stats = await resp.json();
        console.log('[ChartGallery] Stats loaded:', _stats.total_charts, 'charts');
      }
    } catch (e) {
      console.warn('[ChartGallery] Could not load stats:', e);
    }
    
    // Escuchar cambios de paleta para re-renderizar el gráfico activo
    if (window.ColorPalettes && ColorPalettes.onPaletteChange) {
      ColorPalettes.onPaletteChange(async function() {
        if (_currentRenderedChart && _currentRenderedChart.previewSection) {
          console.log('[ChartGallery] Palette changed, re-rendering chart...');
          await executeJsChart(
            _currentRenderedChart.library,
            _currentRenderedChart.code,
            _currentRenderedChart.previewSection
          );
        }
      });
    }
  }
  
  // ─── Modal HTML ────────────────────────────────────────────────────────────
  
  function createModal() {
    if (_galleryModal) return _galleryModal;
    
    // Helper para traducir - usa i18n si está disponible
    const t = (key) => {
      if (typeof i18n !== 'undefined' && i18n.t) return i18n.t(key);
      // Fallback si i18n no está cargado
      return key.split('.').pop();
    };
    
    const overlay = document.createElement('div');
    overlay.id = 'chart-gallery-overlay';
    overlay.className = 'chart-gallery-overlay';
    overlay.innerHTML = `
      <div class="chart-gallery-modal">
        <div class="chart-gallery-header">
          <h2>${t('chartGallery.title')}</h2>
          <span class="chart-gallery-stats"></span>
          <button class="chart-gallery-close" title="${t('chartGallery.close')}">&times;</button>
        </div>
        
        <div class="chart-gallery-tabs">
          <button class="chart-gallery-tab active" data-tab="standard">${t('chartGallery.standardCharts') || 'Graficos Estandar'}</button>
          <button class="chart-gallery-tab" data-tab="advanced">${t('chartGallery.advancedCharts') || 'Graficos Avanzados'}</button>
        </div>
        
        <div class="chart-gallery-toolbar">
          <input type="text" class="chart-gallery-search" placeholder="${t('chartGallery.searchPlaceholder')}">
          <select class="chart-gallery-category">
            <option value="all">${t('chartGallery.allCategories')}</option>
          </select>
          <select class="chart-gallery-library">
            <option value="all">${t('chartGallery.allLibraries')}</option>
          </select>
        </div>
        
        <div class="chart-gallery-content">
          <div class="chart-gallery-grid">
            <div class="chart-gallery-loading">${t('messages.loading')}</div>
          </div>
          <div class="chart-gallery-detail" style="display:none">
            <!-- Detail view -->
          </div>
        </div>
      </div>
    `;
    
    // Eventos
    overlay.querySelector('.chart-gallery-close').onclick = () => hideGallery();
    overlay.onclick = (e) => { if (e.target === overlay) hideGallery(); };
    
    // Eventos de tabs
    const tabs = overlay.querySelectorAll('.chart-gallery-tab');
    tabs.forEach(tab => {
      tab.onclick = () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        _currentFilter.classification = tab.dataset.tab;
        filterCharts();
      };
    });
    
    const searchInput = overlay.querySelector('.chart-gallery-search');
    let searchTimeout;
    searchInput.oninput = () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        _currentFilter.search = searchInput.value.trim();
        filterCharts();
      }, 300);
    };
    
    const categorySelect = overlay.querySelector('.chart-gallery-category');
    categorySelect.onchange = () => {
      _currentFilter.category = categorySelect.value;
      filterCharts();
    };
    
    const librarySelect = overlay.querySelector('.chart-gallery-library');
    librarySelect.onchange = () => {
      _currentFilter.library = librarySelect.value;
      filterCharts();
    };
    
    // Agregar estilos si no existen
    if (!document.getElementById('chart-gallery-styles')) {
      const styles = document.createElement('style');
      styles.id = 'chart-gallery-styles';
      styles.textContent = getStyles();
      document.head.appendChild(styles);
    }
    
    document.body.appendChild(overlay);
    _galleryModal = overlay;
    
    // Poblar filtros
    populateFilters();
    
    return overlay;
  }
  
  function getStyles() {
    return `
      .chart-gallery-overlay {
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.8);
        z-index: 10000;
        align-items: center;
        justify-content: center;
      }
      .chart-gallery-overlay.visible {
        display: flex;
      }
      
      .chart-gallery-modal {
        background: var(--bg-secondary, #242424);
        border-radius: 8px;
        width: 95%;
        max-width: 900px;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        border: 1px solid var(--border, rgba(215,165,56,0.12));
      }
      
      .chart-gallery-header {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid var(--border, rgba(215,165,56,0.12));
        gap: 12px;
      }
      .chart-gallery-header h2 {
        color: var(--accent, #d7a538);
        font-size: 14px;
        font-weight: 600;
        margin: 0;
      }
      .chart-gallery-stats {
        color: var(--text-secondary, #888);
        font-size: 10px;
        margin-left: auto;
      }
      .chart-gallery-close {
        background: none;
        border: none;
        color: var(--text-secondary, #888);
        font-size: 20px;
        cursor: pointer;
        padding: 0 4px;
        line-height: 1;
      }
      .chart-gallery-close:hover { color: var(--text-primary, #e0e0e0); }
      
      .chart-gallery-tabs {
        display: flex;
        gap: 0;
        padding: 0 16px;
        border-bottom: 1px solid var(--border, rgba(215,165,56,0.12));
        background: var(--bg-primary, #1a1a1a);
      }
      .chart-gallery-tab {
        padding: 10px 20px;
        border: none;
        background: transparent;
        color: var(--text-secondary, #888);
        font-size: 11px;
        font-weight: 500;
        cursor: pointer;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
      }
      .chart-gallery-tab:hover {
        color: var(--text-primary, #e0e0e0);
        background: rgba(215,165,56,0.05);
      }
      .chart-gallery-tab.active {
        color: var(--accent, #d7a538);
        border-bottom-color: var(--accent, #d7a538);
        background: rgba(215,165,56,0.1);
      }
      
      .chart-gallery-toolbar {
        display: flex;
        gap: 8px;
        padding: 10px 16px;
        border-bottom: 1px solid var(--border, rgba(215,165,56,0.12));
        flex-wrap: wrap;
      }
      .chart-gallery-search {
        flex: 1;
        min-width: 150px;
        padding: 6px 10px;
        border: 1px solid var(--border, rgba(215,165,56,0.2));
        border-radius: 4px;
        background: var(--bg-primary, #1a1a1a);
        color: var(--text-primary, #e0e0e0);
        font-size: 11px;
      }
      .chart-gallery-search:focus {
        outline: none;
        border-color: var(--accent, #d7a538);
      }
      .chart-gallery-category,
      .chart-gallery-library {
        padding: 6px 10px;
        border: 1px solid var(--border, rgba(215,165,56,0.2));
        border-radius: 4px;
        background: var(--bg-primary, #1a1a1a);
        color: var(--text-primary, #e0e0e0);
        font-size: 11px;
        cursor: pointer;
      }
      
      .chart-gallery-content {
        flex: 1;
        overflow: auto;
        padding: 12px;
      }
      
      .chart-gallery-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 10px;
      }
      
      .chart-gallery-card {
        background: var(--bg-card, rgba(40,40,40,0.85));
        border: 1px solid var(--border, rgba(215,165,56,0.12));
        border-radius: 6px;
        padding: 10px;
        cursor: pointer;
        transition: all 0.15s;
      }
      .chart-gallery-card:hover {
        border-color: var(--accent, #d7a538);
        transform: translateY(-2px);
      }
      .chart-gallery-card-icon {
        width: 32px;
        height: 32px;
        margin: 0 auto 6px;
        color: var(--accent, #d7a538);
        opacity: 0.85;
      }
      .chart-gallery-card-icon svg {
        width: 100%;
        height: 100%;
      }
      .chart-gallery-card-name {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-primary, #e0e0e0);
        text-align: center;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .chart-gallery-card-libs {
        font-size: 9px;
        color: var(--text-secondary, #888);
        text-align: center;
      }
      
      .chart-gallery-loading,
      .chart-gallery-empty {
        grid-column: 1 / -1;
        text-align: center;
        padding: 40px;
        color: var(--text-secondary, #888);
      }
      
      /* Detail View */
      .chart-gallery-detail {
        padding: 0 4px;
      }
      .chart-gallery-detail-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
      }
      .chart-gallery-back {
        background: none;
        border: none;
        color: var(--accent, #d7a538);
        cursor: pointer;
        font-size: 11px;
        padding: 4px 8px;
        border-radius: 4px;
      }
      .chart-gallery-back:hover {
        background: var(--accent-dim, rgba(215,165,56,0.15));
      }
      .chart-gallery-detail-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary, #e0e0e0);
      }
      .chart-gallery-detail-icon {
        width: 24px;
        height: 24px;
        color: var(--accent, #d7a538);
        flex-shrink: 0;
      }
      .chart-gallery-detail-icon svg {
        width: 100%;
        height: 100%;
      }
      
      .chart-gallery-section {
        margin-bottom: 12px;
      }
      .chart-gallery-section-title {
        font-size: 10px;
        font-weight: 600;
        color: var(--accent, #d7a538);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
      }
      .chart-gallery-section-content {
        font-size: 11px;
        color: var(--text-secondary, #888);
        line-height: 1.5;
      }
      .chart-gallery-section-content ul {
        margin: 0;
        padding-left: 16px;
      }
      .chart-gallery-section-content li {
        margin-bottom: 2px;
      }
      
      .chart-gallery-impl-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 6px;
      }
      .chart-gallery-impl-btn {
        padding: 6px 10px;
        border: 1px solid var(--border, rgba(215,165,56,0.2));
        border-radius: 4px;
        background: var(--bg-primary, #1a1a1a);
        color: var(--text-primary, #e0e0e0);
        font-size: 10px;
        cursor: pointer;
        text-align: center;
      }
      .chart-gallery-impl-btn:hover {
        border-color: var(--accent, #d7a538);
        background: var(--accent-dim, rgba(215,165,56,0.15));
      }
      .chart-gallery-impl-btn .lang {
        font-weight: 600;
        color: var(--accent, #d7a538);
      }
      
      .chart-gallery-code {
        margin-top: 12px;
        background: var(--bg-primary, #1a1a1a);
        border: 1px solid var(--border, rgba(215,165,56,0.12));
        border-radius: 4px;
        overflow: hidden;
      }
      .chart-gallery-code-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 10px;
        background: rgba(0,0,0,0.2);
        border-bottom: 1px solid var(--border, rgba(215,165,56,0.12));
      }
      .chart-gallery-code-lang {
        font-size: 10px;
        font-weight: 600;
        color: var(--accent, #d7a538);
      }
      .chart-gallery-code-actions {
        display: flex;
        gap: 6px;
      }
      .chart-gallery-code-actions button {
        padding: 3px 8px;
        border: 1px solid var(--border, rgba(215,165,56,0.2));
        border-radius: 3px;
        background: transparent;
        color: var(--text-secondary, #888);
        font-size: 9px;
        cursor: pointer;
      }
      .chart-gallery-code-actions button:hover {
        background: var(--accent-dim, rgba(215,165,56,0.15));
        color: var(--text-primary, #e0e0e0);
      }
      .chart-gallery-code pre {
        margin: 0;
        padding: 10px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 11px;
        color: var(--text-primary, #e0e0e0);
        overflow-x: auto;
        max-height: 300px;
      }
      
      /* Preview de gráfico */
      .chart-gallery-preview {
        margin-top: 12px;
        border: 1px solid var(--border, rgba(215,165,56,0.2));
        border-radius: 4px;
        background: #1e1e1e;
        overflow: hidden;
      }
      .chart-gallery-preview-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 10px;
        background: rgba(0,0,0,0.3);
        border-bottom: 1px solid var(--border, rgba(215,165,56,0.12));
        font-size: 10px;
        font-weight: 600;
        color: var(--accent, #d7a538);
      }
      .chart-gallery-preview-header button {
        background: none;
        border: none;
        color: var(--text-secondary, #888);
        font-size: 14px;
        cursor: pointer;
        padding: 0 4px;
      }
      .chart-gallery-preview-header button:hover {
        color: var(--text-primary, #e0e0e0);
      }
      .chart-gallery-preview-container {
        min-height: 300px;
        max-height: 450px;
        overflow: auto;
      }
      .btn-run {
        background: var(--accent, #d7a538) !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
      }
      .btn-run:hover {
        background: var(--accent-bright, #e5b84a) !important;
      }
      .btn-save {
        background: #2a9d8f !important;
        color: #fff !important;
        font-weight: 600 !important;
      }
      .btn-save:hover {
        background: #34b8a8 !important;
      }
      .btn-slide {
        background: #4a9eff !important;
        color: #fff !important;
        font-weight: 600 !important;
      }
      .btn-slide:hover {
        background: #6ab0ff !important;
      }
      .btn-use-data {
        background: #9b59b6 !important;
        color: #fff !important;
        font-weight: 600 !important;
      }
      .btn-use-data:hover {
        background: #a569bd !important;
      }
    `;
  }
  
  // ─── Poblar Filtros ────────────────────────────────────────────────────────
  
  function populateFilters() {
    const modal = _galleryModal;
    if (!modal) return;
    
    // Categorías
    const catSelect = modal.querySelector('.chart-gallery-category');
    Object.entries(CATEGORIES).forEach(([key, cat]) => {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = cat[_currentLang] || cat.en;
      catSelect.appendChild(opt);
    });
    
    // Librerías
    const libSelect = modal.querySelector('.chart-gallery-library');
    const allLibs = new Set();
    Object.values(LIBRARIES).forEach(libs => libs.forEach(l => allLibs.add(l)));
    Array.from(allLibs).sort().forEach(lib => {
      const opt = document.createElement('option');
      opt.value = lib;
      opt.textContent = lib;
      libSelect.appendChild(opt);
    });
  }
  
  // ─── Cargar Gráficos ───────────────────────────────────────────────────────
  
  async function loadCharts() {
    const grid = _galleryModal.querySelector('.chart-gallery-grid');
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    grid.innerHTML = `<div class="chart-gallery-loading">${t('messages.loadingCharts')}</div>`;
    
    try {
      const resp = await fetch(`${API_BASE}/api/charts?lang=${_currentLang}`);
      if (!resp.ok) throw new Error('API error');
      
      const data = await resp.json();
      _allCharts = data.charts || [];
      _filteredCharts = [..._allCharts];
      
      // Actualizar stats
      const statsEl = _galleryModal.querySelector('.chart-gallery-stats');
      if (statsEl) {
        statsEl.textContent = `${_allCharts.length} ${t('chartGallery.chartsAvailable')}`;
      }
      
      renderGrid();
    } catch (e) {
      console.error('[ChartGallery] Error loading charts:', e);
      grid.innerHTML = `<div class="chart-gallery-empty">${t('chartGallery.errorLoading')}</div>`;
    }
  }
  
  // ─── Filtrar Gráficos ──────────────────────────────────────────────────────
  
  async function filterCharts() {
    const { category, library, search, classification } = _currentFilter;
    
    // Si hay búsqueda, usar API de búsqueda
    if (search && search.length >= 2) {
      try {
        const resp = await fetch(`${API_BASE}/api/charts/search?q=${encodeURIComponent(search)}&lang=${_currentLang}&limit=50`);
        if (resp.ok) {
          const data = await resp.json();
          let results = (data.results || []).map(r => ({ id: r.id, name: r.name[_currentLang] || r.name.en || r.id }));
          
          // Filtrar por clasificación si ChartClassification está disponible
          if (window.ChartClassification && classification) {
            results = results.filter(chart => 
              ChartClassification.classifyChart(chart.id) === classification
            );
          }
          
          _filteredCharts = results;
          renderGrid();
          updateStats();
          return;
        }
      } catch (e) {
        console.warn('[ChartGallery] Search error:', e);
      }
    }
    
    // Filtrado local
    _filteredCharts = _allCharts.filter(chart => {
      // Filtro por clasificación (standard/advanced)
      if (window.ChartClassification && classification) {
        if (ChartClassification.classifyChart(chart.id) !== classification) {
          return false;
        }
      }
      
      // Filtro por categoría
      if (category !== 'all') {
        const catTypes = CATEGORIES[category]?.types || [];
        const matchesCat = catTypes.some(t => chart.id.toLowerCase().includes(t));
        if (!matchesCat && category !== 'other') return false;
      }
      
      // Filtro por librería (necesitaría más datos del chart)
      // Por ahora solo filtramos por nombre
      
      // Filtro por texto
      if (search && search.length > 0) {
        const searchLower = search.toLowerCase();
        if (!chart.id.toLowerCase().includes(searchLower) && 
            !chart.name.toLowerCase().includes(searchLower)) {
          return false;
        }
      }
      
      return true;
    });
    
    renderGrid();
    updateStats();
  }
  
  // ─── Actualizar estadísticas ───────────────────────────────────────────────
  
  function updateStats() {
    const statsEl = _galleryModal.querySelector('.chart-gallery-stats');
    if (!statsEl) return;
    
    const classification = _currentFilter.classification;
    const label = classification === 'standard' ? 'estandar' : 'avanzados';
    statsEl.textContent = `${_filteredCharts.length} graficos ${label}`;
  }
  
  // ─── Renderizar Grid ───────────────────────────────────────────────────────
  
  function renderGrid() {
    const grid = _galleryModal.querySelector('.chart-gallery-grid');
    const detail = _galleryModal.querySelector('.chart-gallery-detail');
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    grid.style.display = 'grid';
    detail.style.display = 'none';
    
    if (_filteredCharts.length === 0) {
      grid.innerHTML = `<div class="chart-gallery-empty">${t('chartGallery.noResults')}</div>`;
      return;
    }
    
    grid.innerHTML = _filteredCharts.map(chart => {
      const icon = getChartIcon(chart.id);
      return `
        <div class="chart-gallery-card" data-id="${chart.id}">
          <div class="chart-gallery-card-icon">${icon}</div>
          <div class="chart-gallery-card-name" title="${chart.name}">${chart.name}</div>
          <div class="chart-gallery-card-libs">${t('chartGallery.librariesCount')}</div>
        </div>
      `;
    }).join('');
    
    // Eventos de click
    grid.querySelectorAll('.chart-gallery-card').forEach(card => {
      card.onclick = () => showChartDetail(card.dataset.id);
    });
  }
  
  // ─── Iconos de Gráficos (SVG) ───────────────────────────────────────────────
  // Paleta NEVEN: dorado #d7a538, grises #888, #555
  
  const CHART_ICONS = {
    bar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="12" width="4" height="9"/><rect x="10" y="6" width="4" height="15"/><rect x="17" y="9" width="4" height="12"/></svg>',
    line: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17l6-6 4 4 8-8"/><circle cx="9" cy="11" r="1.5" fill="currentColor"/><circle cx="13" cy="15" r="1.5" fill="currentColor"/><circle cx="21" cy="7" r="1.5" fill="currentColor"/></svg>',
    scatter: '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="6" cy="14" r="2"/><circle cx="10" cy="8" r="2"/><circle cx="14" cy="16" r="2"/><circle cx="18" cy="10" r="2"/><circle cx="12" cy="12" r="2"/></svg>',
    pie: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 3v9l6.5 6.5"/></svg>',
    area: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 20l5-8 4 4 5-6 4 2v8H3z" fill="currentColor" opacity="0.3"/><path d="M3 20l5-8 4 4 5-6 4 2"/></svg>',
    histogram: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="14" width="3" height="7"/><rect x="6" y="10" width="3" height="11"/><rect x="10" y="6" width="3" height="15"/><rect x="14" y="10" width="3" height="11"/><rect x="18" y="14" width="3" height="7"/></svg>',
    box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="8" width="12" height="10" rx="1"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="12" y1="18" x2="12" y2="21"/><line x1="6" y1="13" x2="18" y2="13"/></svg>',
    violin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2c-3 3-4 6-4 10s1 7 4 10c3-3 4-6 4-10s-1-7-4-10z"/><line x1="8" y1="12" x2="16" y2="12"/></svg>',
    heatmap: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="2" y="2" width="6" height="6" opacity="0.3"/><rect x="9" y="2" width="6" height="6" opacity="0.6"/><rect x="16" y="2" width="6" height="6" opacity="0.9"/><rect x="2" y="9" width="6" height="6" opacity="0.5"/><rect x="9" y="9" width="6" height="6" opacity="0.8"/><rect x="16" y="9" width="6" height="6" opacity="0.4"/><rect x="2" y="16" width="6" height="6" opacity="0.7"/><rect x="9" y="16" width="6" height="6" opacity="0.4"/><rect x="16" y="16" width="6" height="6" opacity="0.6"/></svg>',
    treemap: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="1"/><line x1="12" y1="2" x2="12" y2="14"/><line x1="2" y1="14" x2="22" y2="14"/><line x1="7" y1="14" x2="7" y2="22"/></svg>',
    sunburst: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="8"/><path d="M12 4v4M12 16v4M4 12h4M16 12h4"/></svg>',
    sankey: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 6h4c6 0 6 6 12 6h4"/><path d="M2 12h4c6 0 6 6 12 6h4"/><path d="M2 18h4c6 0 6-6 12-6h4"/></svg>',
    map: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C8 2 5 5.5 5 9.5c0 5.5 7 12.5 7 12.5s7-7 7-12.5C19 5.5 16 2 12 2z"/><circle cx="12" cy="9" r="2.5"/></svg>',
    radar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12,2 20,8 18,18 6,18 4,8"/><polygon points="12,6 16,10 15,15 9,15 8,10" fill="currentColor" opacity="0.3"/></svg>',
    bubble: '<svg viewBox="0 0 24 24" fill="currentColor" opacity="0.6"><circle cx="8" cy="14" r="4"/><circle cx="16" cy="10" r="5"/><circle cx="12" cy="18" r="3"/></svg>',
    funnel: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 4h18l-6 8v6l-4 2V12L3 4z"/></svg>',
    gauge: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20a8 8 0 1 1 0-16 8 8 0 0 1 0 16z"/><path d="M12 12l4-4"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/></svg>',
    default: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 5-6"/></svg>'
  };
  
  function getChartIcon(chartId) {
    const id = chartId.toLowerCase();
    
    if (id.includes('bar') || id.includes('column')) return CHART_ICONS.bar;
    if (id.includes('line')) return CHART_ICONS.line;
    if (id.includes('scatter')) return CHART_ICONS.scatter;
    if (id.includes('pie') || id.includes('donut')) return CHART_ICONS.pie;
    if (id.includes('area')) return CHART_ICONS.area;
    if (id.includes('histogram') || id.includes('density')) return CHART_ICONS.histogram;
    if (id.includes('box')) return CHART_ICONS.box;
    if (id.includes('violin')) return CHART_ICONS.violin;
    if (id.includes('heat') || id.includes('corr')) return CHART_ICONS.heatmap;
    if (id.includes('tree')) return CHART_ICONS.treemap;
    if (id.includes('sun')) return CHART_ICONS.sunburst;
    if (id.includes('sankey') || id.includes('alluvial')) return CHART_ICONS.sankey;
    if (id.includes('map') || id.includes('geo') || id.includes('chor')) return CHART_ICONS.map;
    if (id.includes('radar') || id.includes('spider') || id.includes('polar')) return CHART_ICONS.radar;
    if (id.includes('bubble')) return CHART_ICONS.bubble;
    if (id.includes('funnel')) return CHART_ICONS.funnel;
    if (id.includes('gauge')) return CHART_ICONS.gauge;
    
    return CHART_ICONS.default;
  }
  
  // ─── Mostrar Detalle ───────────────────────────────────────────────────────
  
  async function showChartDetail(chartId) {
    const grid = _galleryModal.querySelector('.chart-gallery-grid');
    const detail = _galleryModal.querySelector('.chart-gallery-detail');
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    grid.style.display = 'none';
    detail.style.display = 'block';
    detail.innerHTML = `<div class="chart-gallery-loading">${t('messages.loadingDetails')}</div>`;
    
    try {
      const resp = await fetch(`${API_BASE}/api/charts/${chartId}`);
      if (!resp.ok) throw new Error('Chart not found');
      
      const data = await resp.json();
      const chart = data.chart;
      
      const name = chart.name?.[_currentLang] || chart.name?.en || chartId;
      const useWhen = chart.use_when?.[_currentLang] || chart.use_when?.en || [];
      const avoidWhen = chart.avoid_when?.[_currentLang] || chart.avoid_when?.en || [];
      const dataReqs = chart.data_requirements || {};
      const impls = chart.implementations || {};
      
      detail.innerHTML = `
        <div class="chart-gallery-detail-header">
          <button class="chart-gallery-back">&larr; ${t('chartGallery.back')}</button>
          <span class="chart-gallery-detail-icon">${getChartIcon(chartId)}</span>
          <span class="chart-gallery-detail-title">${name}</span>
        </div>
        
        ${useWhen.length > 0 ? `
        <div class="chart-gallery-section">
          <div class="chart-gallery-section-title">${t('chartGallery.useWhen')}</div>
          <div class="chart-gallery-section-content">
            <ul>${useWhen.map(u => `<li>${u}</li>`).join('')}</ul>
          </div>
        </div>
        ` : ''}
        
        ${avoidWhen.length > 0 ? `
        <div class="chart-gallery-section">
          <div class="chart-gallery-section-title">${t('chartGallery.avoidWhen')}</div>
          <div class="chart-gallery-section-content">
            <ul>${avoidWhen.map(a => `<li>${a}</li>`).join('')}</ul>
          </div>
        </div>
        ` : ''}
        
        ${Object.keys(dataReqs).length > 0 ? `
        <div class="chart-gallery-section">
          <div class="chart-gallery-section-title">${t('chartGallery.dataRequirements')}</div>
          <div class="chart-gallery-section-content">
            ${dataReqs.min_columns ? `<div>${_currentLang === 'en' ? 'Min columns' : 'Columnas mínimas'}: ${dataReqs.min_columns}</div>` : ''}
            ${dataReqs.column_types?.length ? `<div>${_currentLang === 'en' ? 'Types' : 'Tipos'}: ${dataReqs.column_types.join(', ')}</div>` : ''}
          </div>
        </div>
        ` : ''}
        
        <div class="chart-gallery-section">
          <div class="chart-gallery-section-title">${t('chartGallery.implementations')}</div>
          <div class="chart-gallery-impl-grid">
            ${Object.entries(impls).map(([lang, libs]) => 
              Object.keys(libs).map(lib => `
                <button class="chart-gallery-impl-btn" data-chart="${chartId}" data-lang="${lang}" data-lib="${lib}">
                  <span class="lang">${lang}</span> / ${lib}
                </button>
              `).join('')
            ).join('')}
          </div>
        </div>
        
        <div class="chart-gallery-code" style="display:none">
          <div class="chart-gallery-code-header">
            <span class="chart-gallery-code-lang"></span>
            <div class="chart-gallery-code-actions">
              <button class="btn-use-data" style="display:none">${t('chartGallery.useMyData') || 'Usar mis datos'}</button>
              <button class="btn-run" style="display:none">${t('chartGallery.run')}</button>
              <button class="btn-save" style="display:none">${t('chartGallery.saveAs')}</button>
              <button class="btn-slide" style="display:none">${t('chartGallery.sendToSlide')}</button>
              <button class="btn-copy">${t('chartGallery.copy')}</button>
              <button class="btn-insert">${t('chartGallery.insertInEditor')}</button>
            </div>
          </div>
          <pre><code></code></pre>
          <div class="chart-gallery-preview" style="display:none">
            <div class="chart-gallery-preview-header">
              <span>${t('chartGallery.preview')}</span>
              <button class="btn-close-preview">&times;</button>
            </div>
            <div class="chart-gallery-preview-container" id="chart-preview-container"></div>
          </div>
        </div>
      `;
      
      // Evento volver
      detail.querySelector('.chart-gallery-back').onclick = () => {
        grid.style.display = 'grid';
        detail.style.display = 'none';
      };
      
      // Eventos de implementación
      detail.querySelectorAll('.chart-gallery-impl-btn').forEach(btn => {
        btn.onclick = () => loadImplementation(btn.dataset.chart, btn.dataset.lang, btn.dataset.lib);
      });
      
    } catch (e) {
      console.error('[ChartGallery] Error loading detail:', e);
      detail.innerHTML = `
        <button class="chart-gallery-back">&larr; ${t('chartGallery.back')}</button>
        <div class="chart-gallery-empty">${t('chartGallery.errorLoading')}</div>
      `;
      detail.querySelector('.chart-gallery-back').onclick = () => {
        grid.style.display = 'grid';
        detail.style.display = 'none';
      };
    }
  }
  
  // ─── Leer Seleccion de Excel via Office.js ──────────────────────────────────
  
  /**
   * Lee la seleccion actual de Excel usando Office.js
   * @returns {Promise<{columns: string[], rows: any[][], rangeAddress: string}>}
   */
  async function readExcelSelection() {
    // Verificar que Office.js este disponible
    if (typeof Excel === 'undefined' || !window._officeReady) {
      console.warn('[ChartGallery] Office.js not available');
      // Fallback a datos en cache si existen
      if (window._nevenCurrentData && window._nevenCurrentData.rows) {
        return window._nevenCurrentData;
      }
      return null;
    }
    
    return new Promise((resolve, reject) => {
      Excel.run(async function(context) {
        try {
          const selection = context.workbook.getSelectedRange();
          selection.load(['values', 'address', 'columnCount', 'rowCount']);
          await context.sync();
          
          const values = selection.values;
          if (!values || values.length === 0) {
            resolve(null);
            return;
          }
          
          // Detectar headers (primera fila con mas texto que numeros)
          const firstRow = values[0];
          const stringCount = firstRow.filter(function(v) { 
            return typeof v === 'string' && isNaN(parseFloat(v)); 
          }).length;
          const hasHeaders = stringCount > firstRow.length / 2;
          
          const columns = hasHeaders ? firstRow : firstRow.map(function(_, i) { return 'Col' + (i+1); });
          const rows = hasHeaders ? values.slice(1) : values;
          
          console.log('[ChartGallery] Excel data read:', columns.length, 'cols,', rows.length, 'rows');
          
          resolve({
            columns: columns,
            rows: rows,
            rangeAddress: selection.address,
            hasHeaders: hasHeaders
          });
        } catch (e) {
          console.error('[ChartGallery] Excel.run error:', e);
          reject(e);
        }
      }).catch(reject);
    });
  }
  
  // ─── Inyectar Datos de Excel en Codigo ──────────────────────────────────────
  
  /**
   * Inyecta los datos de Excel en el codigo del grafico.
   * Los datos originales quedan comentados como ejemplo.
   * 
   * @param {string} code - Codigo original del grafico
   * @param {string} chartId - ID del grafico (para determinar tipo)
   * @param {string} library - Libreria (echarts, chartjs, d3)
   * @param {Object} excelData - Datos de Excel {columns, rows, rangeAddress}
   * @returns {string} - Codigo con datos inyectados
   */
  function injectExcelData(code, chartId, library, excelData) {
    if (!excelData || !excelData.columns || excelData.columns.length === 0) {
      return code;
    }
    
    const cols = excelData.columns;
    const rows = excelData.rows || [];
    
    if (rows.length === 0) {
      return code;
    }
    
    // Extraer datos de Excel: primera columna = categorias, resto = series de valores
    const categories = rows.map(r => String(r[0]));
    const seriesData = [];
    for (let i = 1; i < cols.length; i++) {
      seriesData.push({
        name: cols[i],
        values: rows.map(r => {
          const v = r[i];
          return typeof v === 'number' ? v : parseFloat(v) || 0;
        })
      });
    }
    
    // Generar header con datos de Excel
    const header = `// ══════════════════════════════════════════════════════════════════════════════
// DATOS DE EXCEL (${excelData.rangeAddress || 'seleccion'})
// Columnas: ${cols.join(', ')} | Filas: ${rows.length}
// ══════════════════════════════════════════════════════════════════════════════

// Categorias (${cols[0]}):
const EXCEL_CATEGORIES = ${JSON.stringify(categories)};

// Series de datos:
${seriesData.map((s, i) => `const EXCEL_SERIES_${i + 1} = ${JSON.stringify(s.values)}; // ${s.name}`).join('\n')}

`;
    
    // Buscar patrones de datos simples para reemplazar
    // El regex permite arrays multilinea usando [\s\S] en lugar de [^\]]
    const simpleArrayPattern = /const\s+(\w+)\s*=\s*\[([\s\S]*?)\];/g;
    let matches = [];
    let m;
    while ((m = simpleArrayPattern.exec(code)) !== null) {
      // Excluir variables del sistema y arrays con logica (funciones, map, etc.)
      const fullMatch = m[0];
      const varName = m[1];
      const arrayContent = m[2];
      
      // Saltar si es variable del sistema
      if (fullMatch.includes('ANYPLOT') || fullMatch.includes('palette') || 
          fullMatch.includes('TOKENS') || fullMatch.includes('config')) {
        continue;
      }
      
      // Saltar si el array contiene logica (funciones, llamadas, operaciones)
      if (arrayContent.includes('(') || arrayContent.includes('=>') ||
          arrayContent.includes('Math.') || arrayContent.includes('new ') ||
          arrayContent.includes('function')) {
        continue;
      }
      
      // Solo aceptar arrays con valores literales (strings, numeros)
      // Verificar que el contenido sea principalmente literales y NO vacio
      const cleanContent = arrayContent.replace(/\s+/g, ' ').trim();
      
      // Saltar arrays vacios (se llenan dinamicamente)
      if (cleanContent === '' || cleanContent.length < 2) {
        continue;
      }
      
      const hasOnlyLiterals = /^[\s\d.,\-"'`\w\n\r]*$/.test(cleanContent);
      
      if (hasOnlyLiterals) {
        matches.push({ full: fullMatch, varName: varName, index: m.index });
      }
    }
    
    // Estrategia 1: Si encontramos arrays simples, reemplazarlos
    if (matches.length >= 2) {
      let modifiedCode = code;
      
      if (matches[0]) {
        modifiedCode = modifiedCode.replace(matches[0].full, `const ${matches[0].varName} = EXCEL_CATEGORIES;`);
      }
      if (matches[1] && seriesData.length > 0) {
        modifiedCode = modifiedCode.replace(matches[1].full, `const ${matches[1].varName} = EXCEL_SERIES_1;`);
      }
      if (matches[2] && seriesData.length > 1) {
        modifiedCode = modifiedCode.replace(matches[2].full, `const ${matches[2].varName} = EXCEL_SERIES_2;`);
      }
      
      return header + modifiedCode;
    }
    
    // Estrategia 2: Para graficos complejos, comentar el codigo de datos y crear aliases
    
    // Encontrar donde empieza la creacion del grafico (para separar datos de renderizado)
    const chartInitPatterns = [
      /const\s+chart\s*=/,
      /new\s+Chart\s*\(/,
      /d3\.select\s*\(/,
      /echarts\.init\s*\(/,
      /const\s+\w+\s*=\s*echarts/,
      /svg\.append/,
    ];
    
    let chartStartIndex = -1;
    for (const pattern of chartInitPatterns) {
      const match = code.search(pattern);
      if (match !== -1 && (chartStartIndex === -1 || match < chartStartIndex)) {
        chartStartIndex = match;
      }
    }
    
    if (chartStartIndex === -1) {
      // No encontramos donde empieza el grafico
      return header + `// NOTA: Reemplaza manualmente las variables de datos.\n\n` + code;
    }
    
    // Encontrar donde termina el header de comentarios
    const lines = code.split('\n');
    let dataStartLine = 0;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith('//') || line.startsWith('/*') || line.startsWith('*') || line === '') {
        continue;
      }
      // Saltar const t = window.ANYPLOT_TOKENS
      if (line.includes('ANYPLOT_TOKENS') || line.match(/^const\s+t\s*=/)) {
        dataStartLine = i + 1;
        continue;
      }
      dataStartLine = i;
      break;
    }
    
    // Calcular indices de caracteres
    let dataStartIdx = 0;
    for (let i = 0; i < dataStartLine; i++) {
      dataStartIdx += lines[i].length + 1;
    }
    
    // Separar las partes del codigo
    const headerPart = code.slice(0, dataStartIdx);
    const dataPart = code.slice(dataStartIdx, chartStartIndex);
    const chartPart = code.slice(chartStartIndex);
    
    // Comentar el bloque de datos original
    const commentedData = `// ══════════════════════════════════════════════════════════════════════════════
// CODIGO ORIGINAL DE DATOS (COMENTADO)
// ══════════════════════════════════════════════════════════════════════════════
${dataPart.split('\n').map(line => '// ' + line).join('\n')}

// ══════════════════════════════════════════════════════════════════════════════
// ALIASES PARA COMPATIBILIDAD CON EL GRAFICO
// ══════════════════════════════════════════════════════════════════════════════
`;
    
    // Detectar variables usadas en chartPart para crear aliases
    const commonVars = ['data', 'values', 'labels', 'categories', 'xData', 'yData', 
                        'dates', 'dateLabels', 'months', 'series', 'dataset', 'items'];
    let aliasCode = '';
    
    for (const varName of commonVars) {
      const regex = new RegExp(`\\b${varName}\\b`);
      if (regex.test(chartPart) && !regex.test(headerPart)) {
        // Esta variable se usa en el grafico, crear alias
        if (['dateLabels', 'dates', 'labels', 'months', 'categories', 'xData'].includes(varName)) {
          aliasCode += `const ${varName} = EXCEL_CATEGORIES;\n`;
        } else {
          aliasCode += `const ${varName} = EXCEL_SERIES_1;\n`;
        }
      }
    }
    
    // Si no detectamos aliases, usar nombres genericos
    if (aliasCode === '') {
      aliasCode = `const dateLabels = EXCEL_CATEGORIES;\nconst data = EXCEL_SERIES_1;\n`;
      if (seriesData.length > 1) aliasCode += `const data2 = EXCEL_SERIES_2;\n`;
    }
    
    return headerPart + header + commentedData + aliasCode + '\n' + chartPart;
  }
  
  // ─── Cargar Implementación ─────────────────────────────────────────────────
  
  async function loadImplementation(chartId, language, library) {
    const codeSection = _galleryModal.querySelector('.chart-gallery-code');
    const codeEl = codeSection.querySelector('code');
    const langEl = codeSection.querySelector('.chart-gallery-code-lang');
    const useDataBtn = codeSection.querySelector('.btn-use-data');
    const runBtn = codeSection.querySelector('.btn-run');
    const saveBtn = codeSection.querySelector('.btn-save');
    const slideBtn = codeSection.querySelector('.btn-slide');
    const previewSection = codeSection.querySelector('.chart-gallery-preview');
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    codeSection.style.display = 'block';
    codeEl.textContent = t('messages.loadingCode');
    langEl.textContent = `${language} / ${library}`;
    previewSection.style.display = 'none';
    
    // Mostrar botón Run para:
    // - JavaScript: librerías ejecutables en browser (echarts, chartjs, d3)
    // - R/Python/Julia: todas las librerías (ejecutan en backend via ControlR/ControlPython/ControlJulia)
    const jsExecutableLibs = ['echarts', 'chartjs', 'd3'];
    const canRunJs = language === 'javascript' && jsExecutableLibs.includes(library);
    const canRunBackend = ['r', 'python', 'julia'].includes(language);
    const canRun = canRunJs || canRunBackend;
    
    runBtn.style.display = canRun ? 'inline-block' : 'none';
    saveBtn.style.display = canRunJs ? 'inline-block' : 'none'; // Save solo para JS por ahora
    slideBtn.style.display = 'none'; // Se muestra solo después de ejecutar
    
    // Mostrar botón "Usar mis datos" para graficos JS estandar
    // Los datos se leen de Excel en el momento del click
    const isStandardChart = window.ChartClassification && ChartClassification.classifyChart(chartId) === 'standard';
    console.log('[ChartGallery] useDataBtn check:', { chartId, language, library, canRun, canRunJs, canRunBackend, isStandardChart, hasClassification: !!window.ChartClassification });
    useDataBtn.style.display = (canRunJs && isStandardChart) ? 'inline-block' : 'none';
    
    // Guardar el codigo original para inyeccion
    let _originalCode = '';
    
    try {
      const resp = await fetch(`${API_BASE}/api/charts/${chartId}/code?language=${language}&library=${library}`);
      if (!resp.ok) throw new Error('Code not found');
      
      const data = await resp.json();
      _originalCode = data.code || '# No code available';
      codeEl.textContent = _originalCode;
      
      // Hacer el código editable para lenguajes ejecutables
      if (canRun) {
        codeEl.contentEditable = 'true';
        codeEl.style.outline = 'none';
        codeEl.style.cursor = 'text';
      } else {
        codeEl.contentEditable = 'false';
      }
      
      // Evento Run - JavaScript en browser, R/Python/Julia en backend
      if (canRun) {
        runBtn.onclick = async () => {
          const currentCode = codeEl.textContent;
          if (canRunJs) {
            await executeJsChart(library, currentCode, previewSection);
          } else if (canRunBackend) {
            await executeBackendChart(language, library, currentCode, previewSection);
          }
          // Mostrar botón de slide después de ejecutar
          slideBtn.style.display = 'inline-block';
        };
        
        // Evento Save (solo JS por ahora)
        if (canRunJs) {
          saveBtn.onclick = () => {
            const currentCode = codeEl.textContent;
            showSaveDialog(library, currentCode, chartId);
          };
        }
        
        // Evento Send to Slide
        slideBtn.onclick = () => {
          const container = previewSection.querySelector('#chart-preview-container');
          if (container) {
            sendChartToSlide(container);
          }
        };
        
        // Evento Usar mis datos - Lee directamente de Excel (solo JS por ahora)
        if (canRunJs) {
          useDataBtn.onclick = async () => {
            try {
              // Leer datos frescos de Excel via Office.js
              const excelData = await readExcelSelection();
              if (!excelData || !excelData.rows || excelData.rows.length === 0) {
                if (typeof showToast === 'function') {
                  showToast(t('chartGallery.noDataAvailable') || 'No hay datos seleccionados en Excel');
                }
                return;
              }
              
              const injectedCode = injectExcelData(_originalCode, chartId, library, excelData);
              codeEl.textContent = injectedCode;
              
              if (typeof showToast === 'function') {
                showToast((t('chartGallery.dataInjected') || 'Datos inyectados') + ` (${excelData.rows.length} filas)`);
              }
            } catch (e) {
              console.error('[ChartGallery] Error reading Excel data:', e);
              if (typeof showToast === 'function') {
                showToast('Error al leer datos de Excel');
              }
            }
          };
        }
      }
      
      // Evento cerrar preview
      const closePreviewBtn = previewSection.querySelector('.btn-close-preview');
      if (closePreviewBtn) {
        closePreviewBtn.onclick = () => {
          previewSection.style.display = 'none';
          slideBtn.style.display = 'none';
        };
      }
      
      // Eventos de botones
      const copyBtn = codeSection.querySelector('.btn-copy');
      const insertBtn = codeSection.querySelector('.btn-insert');
      
      copyBtn.onclick = async () => {
        try {
          const currentCode = codeEl.textContent;
          await navigator.clipboard.writeText(currentCode);
          copyBtn.textContent = t('chartGallery.copied');
          setTimeout(() => { copyBtn.textContent = t('chartGallery.copy'); }, 2000);
        } catch (e) {
          console.error('Copy failed:', e);
        }
      };
      
      insertBtn.onclick = () => {
        // Insertar en el editor de Run Script si está disponible
        const editor = document.getElementById('script-code');
        if (editor) {
          const currentCode = codeEl.textContent;
          editor.value = currentCode;
          // Cambiar lenguaje del editor
          const langSelect = document.getElementById('script-lang');
          if (langSelect) {
            const langMap = { python: 'python', r: 'r', julia: 'julia', javascript: 'python' };
            langSelect.value = langMap[language] || 'python';
          }
          hideGallery();
          // Cambiar al tab Run Script
          if (typeof switchTab === 'function') {
            switchTab('run-script');
          }
          if (typeof showToast === 'function') {
            showToast(t('chartGallery.inserted'));
          }
        }
      };
      
    } catch (e) {
      console.error('[ChartGallery] Error loading code:', e);
      codeEl.textContent = '# Error loading code';
    }
  }
  
  // ─── Ejecutar Gráfico JavaScript en Browser ─────────────────────────────────
  
  // Cache de scripts cargados
  const _loadedScripts = {};
  
  // Tokens de tema NEVEN (compatible con anyplot)
  // Usa ColorPalettes si está disponible, si no usa valores por defecto
  function getNEVEN_TOKENS() {
    if (window.ColorPalettes) {
      var palette = ColorPalettes.getCurrentPalette();
      return {
        pageBg: '#1e1e1e',
        elevatedBg: '#2d2d2d',
        ink: '#e0e0e0',
        inkSoft: '#a0a0a0',
        grid: '#404040',
        amber: palette.primary,
        palette: palette.colors
      };
    }
    return {
      pageBg: '#1e1e1e',
      elevatedBg: '#2d2d2d',
      ink: '#e0e0e0',
      inkSoft: '#a0a0a0',
      grid: '#404040',
      amber: '#d7a538',
      palette: ['#d7a538', '#4a9eff', '#50c878', '#ff6b6b', '#9b59b6', '#1abc9c']
    };
  }
  
  async function loadScript(url) {
    if (_loadedScripts[url]) return _loadedScripts[url];
    
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = url;
      script.onload = () => {
        _loadedScripts[url] = true;
        resolve(true);
      };
      script.onerror = () => reject(new Error(`Failed to load: ${url}`));
      document.head.appendChild(script);
    });
  }
  
  async function executeJsChart(library, code, previewSection) {
    const container = previewSection.querySelector('#chart-preview-container');
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    // Guardar estado para re-renderizar al cambiar paleta
    _currentRenderedChart = { library, code, previewSection };
    
    // Limpiar container
    container.innerHTML = '<div style="color:#a0a0a0;padding:20px;">Loading chart...</div>';
    previewSection.style.display = 'block';
    
    try {
      // Cargar librería si no está disponible
      const cdnUrls = {
        echarts: 'https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js',
        chartjs: 'https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js',
        d3: 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js'
      };
      
      if (cdnUrls[library]) {
        const libCheck = {
          echarts: () => typeof echarts !== 'undefined',
          chartjs: () => typeof Chart !== 'undefined',
          d3: () => typeof d3 !== 'undefined'
        };
        
        if (!libCheck[library]()) {
          console.log(`[ChartGallery] Loading ${library} from CDN...`);
          await loadScript(cdnUrls[library]);
        }
      }
      
      // Preparar container
      container.innerHTML = '';
      const chartDiv = document.createElement('div');
      chartDiv.id = 'container';
      chartDiv.style.width = '100%';
      chartDiv.style.height = '400px';
      container.appendChild(chartDiv);
      
      // Inyectar tokens de tema y tamaño
      window.ANYPLOT_TOKENS = getNEVEN_TOKENS();
      window.ANYPLOT_SIZE = { width: 800, height: 400 };
      
      // Adaptar código para ejecución en sandbox
      // - Quitar cualquier document.getElementById que no sea 'container'
      // - Envolver en función para evitar conflictos de scope
      
      const wrappedCode = `
        (function() {
          try {
            ${code}
          } catch(e) {
            console.error('[ChartGallery] Execution error:', e);
            document.getElementById('container').innerHTML = 
              '<div style="color:#ff6b6b;padding:20px;">Error: ' + e.message + '</div>';
          }
        })();
      `;
      
      // Ejecutar
      eval(wrappedCode);
      
      console.log(`[ChartGallery] Chart rendered with ${library}`);
      
    } catch (e) {
      console.error('[ChartGallery] Error executing chart:', e);
      container.innerHTML = `<div style="color:#ff6b6b;padding:20px;">Error: ${e.message}</div>`;
    }
  }
  
  // ─── Ejecutar Gráfico R/Python/Julia en Backend ────────────────────────────
  // Usa los endpoints /api/r, /api/python, /api/julia que comunican con 
  // ControlR.exe, ControlPython.exe, ControlJulia.exe via Named Pipes
  // El TaskPane usa HTTP → neven_http_server.py → PipeClient → ControlX.exe
  // Es el MISMO motor que usa la hoja de Excel (XLL → pipe → ControlX.exe)
  
  async function executeBackendChart(language, library, code, previewSection) {
    const container = previewSection.querySelector('#chart-preview-container');
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    // Mostrar estado de carga
    container.innerHTML = `<div style="color:#a0a0a0;padding:20px;text-align:center;">
      <div style="margin-bottom:8px;">⏳ ${t('chartGallery.executingCode') || 'Ejecutando código'}...</div>
      <div style="font-size:10px;color:#666;">${language.toUpperCase()} / ${library}</div>
    </div>`;
    previewSection.style.display = 'block';
    
    try {
      // Mapear lenguaje a endpoint
      const langEndpoint = {
        r: 'r',
        python: 'python',
        julia: 'julia'
      };
      
      const endpoint = langEndpoint[language.toLowerCase()];
      if (!endpoint) {
        throw new Error(`Lenguaje no soportado: ${language}`);
      }
      
      // ═══════════════════════════════════════════════════════════════════════
      // ESTRATEGIA: Usar SIEMPRE HTTP → ControlR.exe via named pipes
      // Es el MISMO mecanismo que usa la hoja de Excel
      // Ventaja en TaskPane: podemos mostrar gráficos interactivos (Plotly)
      // ═══════════════════════════════════════════════════════════════════════
      
      const graphicsDir = 'C:/Users/Minor Bonilla G/Documents/NEVEN/graphics';
      
      // Construir wrapper según lenguaje:
      // 1. Crea directorio si no existe
      // 2. Cambia al directorio
      // 3. Ejecuta el código del gráfico
      // 4. Devuelve la ruta del PNG generado
      let fullCode = code;
      
      if (endpoint === 'r') {
        // ─── Wrapper R ─────────────────────────────────────────────────────────
        fullCode = `
# NEVEN Chart Gallery - Wrapper
.graphics_dir <- "${graphicsDir}"
if (!dir.exists(.graphics_dir)) dir.create(.graphics_dir, recursive = TRUE)
.old_wd <- getwd()
setwd(.graphics_dir)
tryCatch({
${code}
}, finally = {
  setwd(.old_wd)
})
# Devolver ruta del PNG más reciente (soporta plot-*.png y neven_plot_*.png)
.pngs <- list.files("${graphicsDir}", pattern = "(plot-|neven_plot_).*\\\\.png$", full.names = TRUE)
if (length(.pngs) > 0) normalizePath(.pngs[which.max(file.mtime(.pngs))], winslash = "/") else "No PNG"
`;
      } else if (endpoint === 'python') {
        // ─── Wrapper Python ────────────────────────────────────────────────────
        // NOTA: ControlPython solo evalúa expresiones de UNA línea.
        // Código multilinea cae a PyRun_SimpleString → devuelve boolean True.
        // Estrategia: ejecutar código y al final usar expresión de una línea para PNG.
        const escapedGraphicsDir = graphicsDir.replace(/\\/g, '/');
        const indentedCode = code.split('\n').map(line => '    ' + line).join('\n');
        fullCode = `
import os
import glob

_graphics_dir = "${escapedGraphicsDir}"
os.makedirs(_graphics_dir, exist_ok=True)
_old_cwd = os.getcwd()
os.chdir(_graphics_dir)
try:
${indentedCode}
finally:
    os.chdir(_old_cwd)

# Guardar path del PNG más reciente en variable global para recuperarlo
_pngs = glob.glob(os.path.join("${escapedGraphicsDir}", "*.png"))
_NEVEN_LAST_PNG = max(_pngs, key=os.path.getmtime).replace("\\\\", "/") if _pngs else "No PNG"
`;
        // NOTA: Este código devuelve boolean True, pero el PNG está en _NEVEN_LAST_PNG
        // El renderizador buscará el PNG directamente del directorio
      } else if (endpoint === 'julia') {
        // ─── Wrapper Julia ─────────────────────────────────────────────────────
        // PROBLEMA: Los archivos anyplot usan colorant"#..." que es una macro de Colors.
        // Julia parsea TODO el código antes de ejecutarlo, y las macros deben existir
        // al momento del parseo. Si Colors no está cargado, @colorant_str no existe.
        //
        // SOLUCIÓN: Usar Base.include_string para evaluar el código del gráfico
        // DESPUÉS de que using Colors se haya ejecutado.
        const escapedGraphicsDir = graphicsDir.replace(/\\/g, '/');
        
        // Escapar el código para ponerlo en un string de Julia
        const escapedCode = code
          .replace(/\\/g, '\\\\')  // backslashes
          .replace(/"/g, '\\"')    // quotes
          .replace(/\$/g, '\\$');  // dollar signs
        
        fullCode = `
# Paso 1: Cargar paquetes (esto hace que las macros estén disponibles)
using CairoMakie
using Colors
using ColorSchemes

# Paso 2: Configurar directorio
_graphics_dir = "${escapedGraphicsDir}"
isdir(_graphics_dir) || mkpath(_graphics_dir)
_old_cwd = pwd()
cd(_graphics_dir)

# Paso 3: Evaluar el código del gráfico DESPUÉS de cargar Colors
# Usamos include_string para que se parsee con Colors ya cargado
_chart_code = raw"""
${code}
"""

try
    Base.include_string(Main, _chart_code)
finally
    cd(_old_cwd)
end

# Paso 4: Devolver ruta del PNG más reciente
_pngs = filter(f -> endswith(f, ".png"), readdir("${escapedGraphicsDir}"; join=true))
if !isempty(_pngs)
    replace(_pngs[argmax(mtime.(_pngs))], "\\\\" => "/")
else
    "No PNG generated"
end
`;
      }
      
      // ─── Ejecutar via HTTP → PipeClient → ControlR.exe ───────────────────────
      console.log(`[ChartGallery] Executing ${language}/${library} via /api/${endpoint}`);
      console.log(`[ChartGallery] Code length: ${fullCode.length} chars`);
      console.log(`[ChartGallery] First 200 chars:`, fullCode.substring(0, 200));
      
      const requestBody = JSON.stringify({ 
        code: fullCode,
        timeout_ms: 120000
      });
      console.log(`[ChartGallery] Request body length: ${requestBody.length} chars`);
      
      const resp = await fetch(`${API_BASE}/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
        body: requestBody
      });
      
      const data = await resp.json();
      console.log('[ChartGallery] HTTP response:', data);
      
      // Manejar error del servidor
      if (data.status === 'error') {
        // Mensajes de error específicos para mejor diagnóstico
        let errorMsg = data.message || 'Error ejecutando código';
        let suggestion = `💡 Verifica que el motor ${language.toUpperCase()} esté corriendo y que las librerías estén instaladas.`;
        
        if (errorMsg.includes('engine not available')) {
          errorMsg = `Motor ${language.toUpperCase()} no disponible`;
          suggestion = `💡 El motor ${language.toUpperCase()} no está iniciado. Abre Excel con NEVEN cargado para activar los motores de ejecución.`;
        } else if (errorMsg.includes('Failed to deserialize')) {
          errorMsg = `Error de comunicación con ${language.toUpperCase()}`;
          suggestion = `💡 Hubo un problema al ejecutar el código. Posibles causas:\n` +
            `• El paquete de gráficos (${library}) no está instalado\n` +
            `• El código generó una excepción\n` +
            `• Problema de comunicación con el motor`;
        } else if (errorMsg.includes('timeout') || errorMsg.includes('Timeout')) {
          errorMsg = `Timeout ejecutando ${language.toUpperCase()}`;
          suggestion = `💡 El código tardó demasiado. Esto puede ocurrir la primera vez que se carga una librería pesada como ${library}.`;
        }
        
        throw { message: errorMsg, suggestion: suggestion };
      }
      
      // Renderizar según el tipo de resultado
      _renderBackendResult(data, container, language, library);
      
    } catch (e) {
      console.error('[ChartGallery] Backend execution error:', e);
      const errorMsg = e.message || String(e);
      const suggestion = e.suggestion || `💡 Verifica que el motor ${language.toUpperCase()} esté corriendo y que las librerías estén instaladas.`;
      
      container.innerHTML = `
        <div style="color:#ff6b6b;padding:20px;">
          <div style="font-weight:600;margin-bottom:8px;">❌ Error</div>
          <div style="font-size:11px;font-family:monospace;white-space:pre-wrap;background:#1a1a1a;padding:12px;border-radius:4px;max-height:200px;overflow:auto;">${_escapeHtml(errorMsg)}</div>
          <div style="margin-top:12px;font-size:10px;color:#888;white-space:pre-wrap;">
            ${_escapeHtml(suggestion)}
          </div>
        </div>
      `;
    }
  }
  
  // Renderizar resultado del backend según su tipo
  function _renderBackendResult(data, container, language, library) {
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    switch (data.type) {
      case 'html':
        // Gráficos HTML (plotly, ggplotly, etc.)
        // Detectar si es JSON de plotly envuelto en <neven-plotly>
        if (typeof data.html === 'string' && data.html.indexOf('<neven-plotly>') !== -1) {
          // Usar el renderer de Plotly si está disponible
          if (typeof _renderPlotlyJSON === 'function') {
            const plotlyEl = _renderPlotlyJSON(data.html, data.title || 'Chart');
            container.innerHTML = '';
            container.appendChild(plotlyEl);
          } else {
            // Fallback: renderizar como iframe
            _renderHtmlInIframe(container, data.html);
          }
        } else {
          // HTML genérico - renderizar en iframe con sandbox
          _renderHtmlInIframe(container, data.html);
        }
        break;
        
      case 'array':
        // Tablas de datos - usar renderSlotTable si está disponible
        if (typeof renderSlotTable === 'function') {
          const tableEl = renderSlotTable(data.rows || [], 'Result');
          container.innerHTML = '';
          container.appendChild(tableEl);
        } else {
          // Fallback: mostrar como JSON
          container.innerHTML = `<pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:4px;overflow:auto;max-height:400px;">${JSON.stringify(data.rows, null, 2)}</pre>`;
        }
        break;
        
      case 'string':
      case 'integer':
      case 'real':
        // Detectar si es un path a una imagen PNG/SVG
        const strResult = String(data.result || '');
        if (data.type === 'string' && (strResult.endsWith('.png') || strResult.endsWith('.svg') || strResult.endsWith('.jpg'))) {
          // Es un path a una imagen - intentar mostrarla
          _showImageFromPath(container, strResult);
        } else {
          // Resultados escalares normales
          container.innerHTML = `
            <div style="padding:20px;text-align:center;">
              <div style="font-size:10px;color:#888;margin-bottom:4px;">${data.type}</div>
              <div style="font-size:18px;font-family:monospace;color:#e0e0e0;">${_escapeHtml(strResult)}</div>
            </div>
          `;
        }
        break;
      
      case 'boolean':
        // Para Python/Julia: boolean true significa que el código ejecutó OK
        // pero no devuelve el path del PNG directamente. Intentamos buscarlo.
        if (data.result === true) {
          // Consultar el endpoint que devuelve el PNG más reciente
          fetch(`${API_BASE}/api/latest-png`)
            .then(resp => resp.json())
            .then(pngData => {
              if (pngData.status === 'ok' && pngData.path) {
                _showImageFromPath(container, pngData.path);
              } else {
                // No se encontró PNG, mostrar mensaje de éxito genérico
                container.innerHTML = `
                  <div style="padding:20px;text-align:center;color:#4caf50;">
                    <div style="font-size:24px;margin-bottom:8px;">✓</div>
                    <div>Código ejecutado correctamente</div>
                    <div style="font-size:10px;margin-top:4px;color:#888;">(No se generó imagen PNG)</div>
                  </div>
                `;
              }
            })
            .catch(() => {
              // Error al buscar PNG
              container.innerHTML = `
                <div style="padding:20px;text-align:center;">
                  <div style="font-size:10px;color:#888;margin-bottom:4px;">boolean</div>
                  <div style="font-size:18px;font-family:monospace;color:#e0e0e0;">true</div>
                </div>
              `;
            });
        } else {
          // boolean false - mostrar como está
          container.innerHTML = `
            <div style="padding:20px;text-align:center;">
              <div style="font-size:10px;color:#888;margin-bottom:4px;">boolean</div>
              <div style="font-size:18px;font-family:monospace;color:#e0e0e0;">false</div>
            </div>
          `;
        }
        break;
        
      case 'nil':
        // Sin resultado (pero código ejecutó exitosamente)
        container.innerHTML = `
          <div style="padding:20px;text-align:center;color:#888;">
            <div style="font-size:24px;margin-bottom:8px;">✓</div>
            <div>${t('chartGallery.codeExecuted') || 'Código ejecutado'}</div>
            <div style="font-size:10px;margin-top:4px;">(${t('chartGallery.noVisualOutput') || 'Sin salida visual'})</div>
          </div>
        `;
        break;
        
      default:
        // Tipo desconocido - mostrar raw
        container.innerHTML = `<pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:4px;overflow:auto;max-height:400px;">${JSON.stringify(data, null, 2)}</pre>`;
    }
    
    // Mostrar console output si existe
    if (data.console && data.console.trim()) {
      const consoleDiv = document.createElement('div');
      consoleDiv.style.cssText = 'margin-top:12px;padding:8px 12px;background:#0d0d0d;border:1px solid #333;border-radius:4px;font-size:10px;font-family:monospace;color:#888;max-height:100px;overflow:auto;';
      consoleDiv.innerHTML = `<div style="color:#666;margin-bottom:4px;">Console:</div>${_escapeHtml(data.console)}`;
      container.appendChild(consoleDiv);
    }
  }
  
  // Renderizar HTML en un iframe sandboxed
  function _renderHtmlInIframe(container, html) {
    container.innerHTML = '';
    const iframe = document.createElement('iframe');
    iframe.setAttribute('srcdoc', html);
    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
    iframe.style.width = '100%';
    iframe.style.height = '420px';
    iframe.style.border = 'none';
    iframe.style.background = '#1e1e1e';
    container.appendChild(iframe);
  }
  
  // Mostrar imagen desde path del filesystem
  function _showImageFromPath(container, imagePath) {
    const normalizedPath = imagePath.replace(/\\/g, '/');
    
    // Si es un path absoluto de Windows, usar endpoint de archivo estático
    let imageUrl;
    if (normalizedPath.match(/^[A-Za-z]:\//)) {
      imageUrl = `${API_BASE}/file?path=${encodeURIComponent(imagePath)}`;
    } else {
      imageUrl = normalizedPath;
    }
    
    container.innerHTML = `
      <div style="padding:10px;text-align:center;">
        <img src="${imageUrl}" style="max-width:100%;max-height:400px;border-radius:4px;" 
             onerror="this.parentElement.innerHTML='<div style=\\'color:#888;padding:20px\\'>No se pudo cargar: ${_escapeHtml(imagePath)}</div>'" />
        <div style="font-size:9px;color:#666;margin-top:8px;">${_escapeHtml(imagePath)}</div>
      </div>
    `;
  }
  
  // Escapar HTML para prevenir XSS
  function _escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
  
  // ─── Office.js Raw Execution (sin wrapper) ─────────────────────────────────
  // Ejecuta código R directamente via =NEVEN.r() sin envolver en capture.output
  // Usado por Chart Gallery para ejecutar scripts que generan archivos PNG
  async function runRawRCodeViaOfficeJS(code) {
    // Verificar que Office.js esté disponible
    if (typeof Office === 'undefined' || !window._officeReady) {
      return { status: 'error', message: 'Office.js no disponible. Abre el Task Pane desde Excel.' };
    }

    return new Promise(function(resolve) {
      Excel.run(async function(context) {
        // Usar una celda temporal oculta para ejecutar la fórmula
        var sheet = context.workbook.worksheets.getActiveWorksheet();
        var tempCell = sheet.getRange('XFD1048576');
        
        // Escapar comillas en el código para la fórmula
        var escapedCode = code.replace(/\\/g, '\\\\').replace(/"/g, '""');
        var formula = '=NEVEN.r("' + escapedCode + '")';
        
        console.log('[ChartGallery] Formula:', formula.substring(0, 100) + '...');
        
        tempCell.formulas = [[formula]];
        tempCell.load('values');
        
        await context.sync();
        
        var result = tempCell.values[0][0];
        console.log('[ChartGallery] Raw result:', result);
        
        // Limpiar la celda temporal
        tempCell.clear();
        context.sync(); // Fire and forget
        
        // Interpretar el resultado
        if (result === null || result === undefined) {
          resolve({ status: 'ok', type: 'nil', result: null });
        } else if (typeof result === 'number') {
          resolve({ status: 'ok', type: 'numeric', result: result });
        } else if (typeof result === 'string') {
          // Detectar errores de Excel
          if (result.startsWith('#') && (result.includes('ERROR') || result.includes('VALUE') || result.includes('DESBORD'))) {
            resolve({ status: 'error', message: 'Error de Excel: ' + result });
          } else if (result.trim().startsWith('<') && result.includes('</')) {
            // HTML pass-through
            resolve({ status: 'ok', type: 'html', html: result });
          } else if (result.match(/^[A-Za-z]:[\\/].*\.(png|jpg|jpeg|gif|svg)$/i)) {
            // Detectar paths de imagen
            resolve({ status: 'ok', type: 'string', result: result });
          } else {
            resolve({ status: 'ok', type: 'string', result: result });
          }
        } else if (typeof result === 'boolean') {
          resolve({ status: 'ok', type: 'boolean', result: result });
        } else {
          resolve({ status: 'ok', type: 'scalar', result: String(result) });
        }
      }).catch(function(err) {
        console.error('[ChartGallery] Office.js error:', err);
        resolve({ status: 'error', message: 'Office.js error: ' + err.message });
      });
    });
  }
  
  // ─── User Charts Functions ─────────────────────────────────────────────────
  
  async function loadUserCharts() {
    try {
      const resp = await fetch(`${API_BASE}/api/user-charts`);
      if (resp.ok) {
        const data = await resp.json();
        _userCharts = data.charts || [];
        console.log(`[ChartGallery] User charts loaded: ${_userCharts.length}`);
      }
    } catch (e) {
      console.warn('[ChartGallery] Could not load user charts:', e);
      _userCharts = [];
    }
  }
  
  async function saveUserChart(name, library, code, basedOn) {
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    try {
      const resp = await fetch(`${API_BASE}/api/user-charts/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, library, code, basedOn })
      });
      
      const data = await resp.json();
      if (data.status === 'ok') {
        // Recargar lista de user charts
        await loadUserCharts();
        if (typeof showToast === 'function') {
          showToast(t('chartGallery.chartSaved') || `Chart "${name}" saved`);
        }
        return data.chart;
      } else {
        throw new Error(data.message || 'Save failed');
      }
    } catch (e) {
      console.error('[ChartGallery] Error saving chart:', e);
      if (typeof showToast === 'function') {
        showToast('Error: ' + e.message);
      }
      return null;
    }
  }
  
  async function deleteUserChart(chartId) {
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    try {
      const resp = await fetch(`${API_BASE}/api/user-charts/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: chartId })
      });
      
      const data = await resp.json();
      if (data.status === 'ok') {
        await loadUserCharts();
        if (typeof showToast === 'function') {
          showToast(t('chartGallery.chartDeleted') || 'Chart deleted');
        }
        return true;
      } else {
        throw new Error(data.message || 'Delete failed');
      }
    } catch (e) {
      console.error('[ChartGallery] Error deleting chart:', e);
      return false;
    }
  }
  
  function showSaveDialog(library, code, basedOn) {
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    // Crear modal de diálogo personalizado en lugar de prompt()
    const existingDialog = document.getElementById('chart-save-dialog');
    if (existingDialog) existingDialog.remove();
    
    const dialog = document.createElement('div');
    dialog.id = 'chart-save-dialog';
    dialog.style.cssText = `
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.7); z-index: 30000;
      display: flex; align-items: center; justify-content: center;
    `;
    dialog.innerHTML = `
      <div style="background:#242424;border-radius:8px;padding:20px;width:300px;border:1px solid var(--accent,#d7a538)">
        <div style="font-size:12px;font-weight:600;color:#e0e0e0;margin-bottom:12px">
          ${t('chartGallery.saveAs') || 'Save as...'}
        </div>
        <input type="text" id="chart-save-name" placeholder="${t('chartGallery.enterChartName') || 'Enter chart name'}"
          value="My ${library} chart"
          style="width:100%;padding:8px;border:1px solid #555;border-radius:4px;background:#1a1a1a;color:#e0e0e0;font-size:11px;box-sizing:border-box">
        <div style="display:flex;gap:8px;margin-top:12px;justify-content:flex-end">
          <button id="chart-save-cancel" style="padding:6px 12px;border:1px solid #555;border-radius:4px;background:#333;color:#888;cursor:pointer;font-size:11px">
            ${t('buttons.cancel') || 'Cancel'}
          </button>
          <button id="chart-save-confirm" style="padding:6px 12px;border:none;border-radius:4px;background:#2a9d8f;color:#fff;cursor:pointer;font-size:11px;font-weight:600">
            ${t('buttons.save') || 'Save'}
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    
    const input = dialog.querySelector('#chart-save-name');
    const cancelBtn = dialog.querySelector('#chart-save-cancel');
    const confirmBtn = dialog.querySelector('#chart-save-confirm');
    
    input.focus();
    input.select();
    
    const closeDialog = () => dialog.remove();
    
    cancelBtn.onclick = closeDialog;
    dialog.onclick = (e) => { if (e.target === dialog) closeDialog(); };
    
    confirmBtn.onclick = async () => {
      const name = input.value.trim();
      if (name) {
        await saveUserChart(name, library, code, basedOn);
        closeDialog();
      }
    };
    
    input.onkeydown = (e) => {
      if (e.key === 'Enter') confirmBtn.click();
      if (e.key === 'Escape') closeDialog();
    };
  }
  
  // ─── Send to Slide ─────────────────────────────────────────────────────────
  
  function sendChartToSlide(container) {
    // Usar la función global _nevenSendToSlide del TaskPane
    // Orden de prioridad: Plotly > SVG > Canvas > IMG
    
    // 1. Plotly — buscar div con id que empiece con "plotly-"
    const plotlyDiv = container.querySelector('[id^="plotly-"]');
    if (plotlyDiv && typeof Plotly !== 'undefined') {
      // Exportar Plotly como PNG usando su API
      Plotly.toImage(plotlyDiv.id, { format: 'png', width: 1200, height: 600 })
        .then(dataUrl => {
          const imgHtml = '<html><head><meta charset="UTF-8"><style>body{background:#1e1e1e;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box}img{max-width:100%;height:auto}</style></head><body><img src="' + dataUrl + '"></body></html>';
          _sendToSlideInternal('Chart from Gallery', imgHtml);
        })
        .catch(err => {
          console.error('[ChartGallery] Error exporting Plotly:', err);
          if (typeof showToast === 'function') showToast('Error al exportar gráfico Plotly');
        });
      return;
    }
    
    // 2. SVG — para gráficos D3
    const svg = container.querySelector('svg');
    if (svg) {
      const svgHtml = '<html><head><meta charset="UTF-8"><style>body{background:#1e1e1e;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box}svg{max-width:100%;height:auto}</style></head><body>' + svg.outerHTML + '</body></html>';
      _sendToSlideInternal('Chart from Gallery', svgHtml);
      return;
    }
    
    // 3. Canvas — para Chart.js/ECharts
    const canvas = container.querySelector('canvas');
    if (canvas) {
      try {
        const dataUrl = canvas.toDataURL('image/png');
        const imgHtml = '<html><head><meta charset="UTF-8"><style>body{background:#1e1e1e;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box}img{max-width:100%;height:auto}</style></head><body><img src="' + dataUrl + '"></body></html>';
        _sendToSlideInternal('Chart from Gallery', imgHtml);
      } catch (e) {
        console.error('[ChartGallery] Error capturing canvas:', e);
        if (typeof showToast === 'function') showToast('Error al capturar gráfico');
      }
      return;
    }
    
    // 4. IMG — para R/Python/Julia (imágenes PNG del servidor)
    const img = container.querySelector('img');
    if (img && img.src) {
      _convertImageToDataUrl(img.src)
        .then(dataUrl => {
          const imgHtml = '<html><head><meta charset="UTF-8"><style>body{background:#1e1e1e;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box}img{max-width:100%;height:auto}</style></head><body><img src="' + dataUrl + '"></body></html>';
          _sendToSlideInternal('Chart from Gallery', imgHtml);
        })
        .catch(err => {
          console.error('[ChartGallery] Error converting image:', err);
          if (typeof showToast === 'function') showToast('Error al procesar imagen');
        });
      return;
    }
    
    // 5. Ningún gráfico encontrado
    if (typeof showToast === 'function') {
      showToast('No hay gráfico para exportar');
    }
  }
  
  // Helper interno para enviar a slide
  function _sendToSlideInternal(title, html) {
    if (typeof window._nevenSendToSlide === 'function') {
      window._nevenSendToSlide(title, html, null);
      if (typeof showToast === 'function') {
        showToast('Enviado a Presentaciones');
      }
    } else {
      console.error('[ChartGallery] _nevenSendToSlide not available');
      if (typeof showToast === 'function') {
        showToast('Error: Función de slides no disponible');
      }
    }
  }
  
  // Convertir URL de imagen a data URL (base64)
  async function _convertImageToDataUrl(imageUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous'; // Necesario para CORS
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        try {
          const dataUrl = canvas.toDataURL('image/png');
          resolve(dataUrl);
        } catch (e) {
          reject(e);
        }
      };
      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = imageUrl;
    });
  }
  
  // ─── Mostrar/Ocultar ───────────────────────────────────────────────────────
  
  function showGallery() {
    const modal = createModal();
    modal.classList.add('visible');
    loadUserCharts().then(() => loadCharts());
    
    // Focus en búsqueda
    setTimeout(() => {
      modal.querySelector('.chart-gallery-search')?.focus();
    }, 100);
  }
  
  function hideGallery() {
    if (_galleryModal) {
      _galleryModal.classList.remove('visible');
    }
  }
  
  // ─── API Pública ───────────────────────────────────────────────────────────
  
  window.ChartGallery = {
    show: showGallery,
    hide: hideGallery,
    init: init
  };
  
  // Auto-init cuando DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
})();
