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
  
  const API_BASE = window.API_BASE || window.location.origin;
  
  // Estado del módulo
  let _galleryModal = null;
  let _allCharts = [];
  let _filteredCharts = [];
  let _currentFilter = { category: 'all', library: 'all', search: '' };
  let _stats = null;
  let _currentLang = 'es';
  
  // Categorías de gráficos (mapeadas desde los tipos)
  const CATEGORIES = {
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
    const { category, library, search } = _currentFilter;
    
    // Si hay búsqueda, usar API de búsqueda
    if (search && search.length >= 2) {
      try {
        const resp = await fetch(`${API_BASE}/api/charts/search?q=${encodeURIComponent(search)}&lang=${_currentLang}&limit=50`);
        if (resp.ok) {
          const data = await resp.json();
          _filteredCharts = (data.results || []).map(r => ({ id: r.id, name: r.name[_currentLang] || r.name.en || r.id }));
          renderGrid();
          return;
        }
      } catch (e) {
        console.warn('[ChartGallery] Search error:', e);
      }
    }
    
    // Filtrado local
    _filteredCharts = _allCharts.filter(chart => {
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
              <button class="btn-copy">${t('chartGallery.copy')}</button>
              <button class="btn-insert">${t('chartGallery.insertInEditor')}</button>
            </div>
          </div>
          <pre><code></code></pre>
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
  
  // ─── Cargar Implementación ─────────────────────────────────────────────────
  
  async function loadImplementation(chartId, language, library) {
    const codeSection = _galleryModal.querySelector('.chart-gallery-code');
    const codeEl = codeSection.querySelector('code');
    const langEl = codeSection.querySelector('.chart-gallery-code-lang');
    const t = (key) => (typeof i18n !== 'undefined' && i18n.t) ? i18n.t(key) : key.split('.').pop();
    
    codeSection.style.display = 'block';
    codeEl.textContent = t('messages.loadingCode');
    langEl.textContent = `${language} / ${library}`;
    
    try {
      const resp = await fetch(`${API_BASE}/api/charts/${chartId}/code?language=${language}&library=${library}`);
      if (!resp.ok) throw new Error('Code not found');
      
      const data = await resp.json();
      codeEl.textContent = data.code || '# No code available';
      
      // Eventos de botones
      const copyBtn = codeSection.querySelector('.btn-copy');
      const insertBtn = codeSection.querySelector('.btn-insert');
      
      copyBtn.onclick = async () => {
        try {
          await navigator.clipboard.writeText(data.code);
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
          editor.value = data.code;
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
  
  // ─── Mostrar/Ocultar ───────────────────────────────────────────────────────
  
  function showGallery() {
    const modal = createModal();
    modal.classList.add('visible');
    loadCharts();
    
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
