// ═══════════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Clasificación de Gráficos (Estándar vs Avanzados)
// ═══════════════════════════════════════════════════════════════════════════════
// Define qué gráficos siguen el patrón Y~X (estándar) y cuáles requieren
// estructuras de datos especiales (avanzados).
//
// Criterio de clasificación:
//   ESTÁNDAR: Gráficos que funcionan con datos tabulares simples (columnas X, Y, grupo)
//   AVANZADOS: Gráficos que requieren estructuras específicas (flujos, jerarquías, OHLC, etc.)
// ═══════════════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ─── Prefijos de gráficos ESTÁNDAR (patrón Y~X) ────────────────────────────
  // Estos gráficos funcionan con datos tabulares simples:
  // - Una o más columnas numéricas (Y)
  // - Una columna categórica o numérica (X)
  // - Opcionalmente una columna de agrupación
  
  const STANDARD_PREFIXES = [
    'area',           // area-basic, area-stacked, etc.
    'bar',            // bar-basic, bar-grouped, bar-stacked, etc.
    'band',           // band-basic
    'box',            // box-basic, box-grouped, box-notched
    'boxen',          // boxen-basic
    'bubble',         // bubble-basic (no bubble-map)
    'cat',            // cat-box-strip
    'count',          // count-basic
    'density',        // density-basic, density-rug
    'donut',          // donut-basic, donut-nested
    'dumbbell',       // dumbbell-basic
    'ecdf',           // ecdf-basic
    'errorbar',       // errorbar-basic, errorbar-asymmetric
    'frequency',      // frequency-polygon-basic
    'histogram',      // histogram-basic, histogram-kde, etc.
    'line',           // line-basic, line-multi, line-timeseries, etc.
    'lollipop',       // lollipop-basic, lollipop-grouped
    'pie',            // pie-basic
    'point',          // point-basic (no point-and-figure)
    'polar',          // polar-basic, polar-bar, polar-line, polar-scatter
    'pp',             // pp-basic (probability plot)
    'qq',             // qq-basic
    'raincloud',      // raincloud-basic
    'range',          // range-interval
    'ridgeline',      // ridgeline-basic
    'rose',           // rose-basic
    'rug',            // rug-basic
    'scatter',        // scatter-basic, scatter-regression, etc. (no scatter-map)
    'slope',          // slope-basic
    'span',           // span-basic
    'sparkline',      // sparkline-basic
    'stem',           // stem-basic
    'step',           // step-basic
    'strip',          // strip-basic
    'swarm',          // swarm-basic
    'violin',         // violin-basic, violin-grouped, etc.
    'waterfall',      // waterfall-basic
  ];

  // ─── Gráficos ESTÁNDAR específicos (excepciones a prefijos avanzados) ──────
  const STANDARD_SPECIFIC = [
    'bubble-basic',
    'bubble-packed',
    'heatmap-basic',
    'heatmap-annotated',
    'heatmap-correlation',
    'heatmap-clustered',
    'point-basic',
    'scatter-basic',
    'scatter-annotated',
    'scatter-categorical',
    'scatter-color-mapped',
    'scatter-marginal',
    'scatter-regression-linear',
    'scatter-regression-lowess',
    'scatter-regression-polynomial',
    'scatter-text',
  ];
  
  // ─── Gráficos AVANZADOS específicos (excepciones a prefijos estándar) ──────
  // Estos graficos tienen prefijo estandar pero datos algoritmicos complejos
  const ADVANCED_SPECIFIC = [
    // Area charts con datos algoritmicos
    'area-basic',               // Datos con LCG seed aleatorio
    'area-cumulative-flow',     // Datos algoritmicos con logica de bottleneck
    'area-elevation-profile',   // Datos de elevacion geografica
    'area-mountain-panorama',   // Datos de silueta de montanas
    'area-stacked-confidence',  // Intervalos de confianza
    // Bar charts especializados
    'bar-3d-categorical',       // Superficie 3D
    'bar-feature-importance',   // ML feature importance
    'bar-heart-rate-zones',     // Zonas HR especificas
    'bar-pareto',               // Requiere calculo de porcentaje acumulado
    'bar-permutation-importance', // ML permutation importance
    'bar-tornado-sensitivity',  // Analisis de sensibilidad
    // Histogram especializados
    'histogram-capability',     // Analisis de capacidad de proceso
    'histogram-epidemic',       // Curva epidemica
    'histogram-returns-distribution', // Distribucion financiera
    // Line charts especializados
    'line-3d-trajectory',       // Trayectoria 3D
    'line-annotated-events',    // Eventos anotados
    'line-arrhenius',           // Ecuacion de Arrhenius
    'line-confidence',          // Intervalos de confianza
    'line-cycle-seasonal',      // Descomposicion estacional
    'line-growth-percentile',   // Percentiles de crecimiento
    'line-impurity-comparison', // ML impurity
    'line-load-duration',       // Curva de duracion de carga
    'line-loss-training',       // ML training loss
    'line-parametric',          // Curvas parametricas
    'line-pca-variance-cumulative', // PCA varianza
    'line-reaction-coordinate', // Quimica - coordenada de reaccion
    'line-retention-cohort',    // Retencion de cohorte
    'line-stock-comparison',    // Comparacion de stocks
    'line-stress-strain',       // Curva stress-strain
    'line-tanabe-sugano',       // Diagrama Tanabe-Sugano
    'line-timeseries-rolling',  // Media movil
    'line-training-load-pmc',   // PMC training load
    'line-win-probability',     // Probabilidad de ganar
    'line-yield-curve',         // Curva de rendimiento financiero
    // Scatter especializados
    'scatter-complex-plane',    // Plano complejo
    'scatter-connected-temporal', // Scatter temporal conectado
    'scatter-embedding',        // ML embeddings
    'scatter-lag',              // Scatter con lag
    'scatter-matrix',           // Matriz de scatter plots
    // Violin especializados
    'violin-grouped-swarm',     // Violin con swarm
    'violin-split',             // Violin dividido
  ];

  // ─── Prefijos de gráficos AVANZADOS ────────────────────────────────────────
  // Estos gráficos requieren estructuras de datos específicas
  
  const ADVANCED_PREFIXES = [
    'acf',            // ACF/PACF - requiere serie temporal
    'alluvial',       // Flujo - requiere source/target/value
    'andrews',        // Andrews curves - requiere múltiples variables
    'arc',            // Arc diagram - requiere conexiones
    'audiogram',      // Audiograma clínico - formato específico
    'barcode',        // Códigos de barras - no es visualización de datos
    'bifurcation',    // Diagramas de bifurcación - matemático
    'biplot',         // PCA biplot - requiere análisis previo
    'bland',          // Bland-Altman - requiere pares de mediciones
    'bode',           // Diagramas de Bode - ingeniería de control
    'bullet',         // Bullet chart - formato específico
    'bump',           // Bump chart - rankings temporales
    'burndown',       // Burndown chart - sprints
    'calibration',    // Curvas de calibración
    'campbell',       // Diagrama de Campbell
    'candlestick',    // OHLC financiero
    'cartogram',      // Cartogramas - geoespacial
    'chernoff',       // Chernoff faces - multivariable
    'chessboard',     // Tablero de ajedrez - no es datos
    'chord',          // Chord diagram - flujo circular
    'choropleth',     // Mapas coropléticos - geoespacial
    'circlepacking',  // Circle packing - jerárquico
    'circos',         // Circos plot - genómica
    'climograph',     // Climogramas - formato específico
    'coefficient',    // Intervalos de confianza
    'column',         // Columnas estratigráficas
    'confusion',      // Matriz de confusión - ML
    'contour',        // Contornos - 3D/superficies
    'crossword',      // Crucigrama - no es datos
    'curve',          // Curvas especializadas (OC, dose-response)
    'dashboard',      // Dashboards - composición
    'datamatrix',     // Códigos DataMatrix - no es datos
    'dendrogram',     // Dendrogramas - jerárquico
    'depth',          // Order book - finanzas
    'diagnostic',     // Paneles de diagnóstico
    'dot',            // Dot matrix - proporcional
    'drawdown',       // Drawdown - finanzas
    'ecg',            // ECG - médico
    'elbow',          // Elbow curve - ML clustering
    'energy',         // Niveles de energía - física
    'eye',            // Eye diagram - telecomunicaciones
    'facet',          // Facet grid - composición
    'feynman',        // Diagramas de Feynman - física
    'flamegraph',     // Flamegraphs - profiling
    'flowmap',        // Flow maps - geoespacial
    'forest',         // Forest plot - meta-análisis
    'frontier',       // Frontera eficiente - finanzas
    'funnel',         // Funnel plots
    'gain',           // Gain curve - ML
    'gantt',          // Gantt - gestión de proyectos
    'gauge',          // Gauges - indicadores
    'genome',         // Genome tracks - genómica
    'heatmap',        // La mayoría son avanzados (calendar, geographic, etc.)
    'hexbin',         // Hexbin - requiere binning
    'hive',           // Hive plots - redes
    'horizon',        // Horizon charts - series temporales densas
    'ice',            // ICE plots - ML interpretability
    'icicle',         // Icicle charts - jerárquico
    'indicator',      // Indicadores técnicos - finanzas
    'kagi',           // Kagi charts - finanzas
    'ks',             // KS test - estadístico
    'learning',       // Learning curves - ML
    'lift',           // Lift curve - ML
    'lightcurve',     // Light curves - astronomía
    'logistic',       // Regresión logística
    'ma',             // MA plot - genómica
    'manhattan',      // Manhattan plot - GWAS
    'map',            // Mapas - geoespacial
    'marimekko',      // Marimekko - proporcional
    'maze',           // Laberintos - no es datos
    'mohr',           // Círculo de Mohr - ingeniería
    'mosaic',         // Mosaic plots - categórico
    'network',        // Redes/grafos
    'nyquist',        // Diagramas de Nyquist
    'ohlc',           // OHLC - finanzas
    'parallel',       // Coordenadas paralelas
    'parliament',     // Parliament charts
    'pdp',            // PDP - ML interpretability
    'phase',          // Diagramas de fase
    'piano',          // Piano roll - música
    'pictogram',      // Pictogramas
    'precision',      // Precision-Recall - ML
    'probability',    // Weibull probability
    'psychrometric',  // Carta psicrométrica
    'pyramid',        // Pirámides poblacionales
    'qrcode',         // Códigos QR - no es datos
    'quiver',         // Quiver plots - vectores
    'radar',          // Radar/spider - múltiples ejes
    'recurrence',     // Recurrence plots
    'renko',          // Renko - finanzas
    'residual',       // Residuales - diagnóstico
    'roc',            // ROC curve - ML
    'root',           // Root locus - control
    'sankey',         // Sankey - flujo
    'sequence',       // Sequence logos - bioinformática
    'shap',           // SHAP - ML interpretability
    'silhouette',     // Silhouette - clustering
    'skewt',          // Skew-T - meteorología
    'smith',          // Smith chart - RF
    'sn',             // S-N curve - fatiga
    'spc',            // SPC charts - control de calidad
    'spectrogram',    // Espectrogramas - audio
    'spectrum',       // Espectros
    'spiral',         // Spiral plots
    'spirometry',     // Espirometría - médico
    'star',           // Star charts - astronomía
    'stereonet',      // Stereonet - geología
    'stock',          // Stock charts con eventos
    'streamgraph',    // Streamgraphs
    'streamline',     // Streamlines - fluidos
    'subplot',        // Subplots - composición
    'sudoku',         // Sudoku - no es datos
    'sunburst',       // Sunburst - jerárquico
    'surface',        // Superficies 3D
    'survival',       // Kaplan-Meier - supervivencia
    'swimmer',        // Swimmer plots - clínico
    'ternary',        // Diagramas ternarios
    'timeline',       // Timelines
    'timeseries',     // Descomposición/forecast
    'titration',      // Curvas de titulación
    'tree',           // Árboles (decisión, filogenia)
    'treemap',        // Treemaps - jerárquico
    'upset',          // UpSet plots - intersecciones
    'venn',           // Venn diagrams
    'volcano',        // Volcano plots - genómica
    'voronoi',        // Voronoi - geométrico
    'waffle',         // Waffle charts
    'waveform',       // Waveforms - audio
    'windbarb',       // Wind barbs - meteorología
    'windrose',       // Wind rose - meteorología
    'wireframe',      // Wireframe 3D
    'wordcloud',      // Word clouds - texto
  ];

  // ─── Función de clasificación ──────────────────────────────────────────────
  
  function classifyChart(chartId) {
    // Primero verificar si está en la lista específica de avanzados
    // (excepciones a prefijos estándar)
    if (ADVANCED_SPECIFIC.includes(chartId)) {
      return 'advanced';
    }
    
    // Luego verificar si está en la lista específica de estándar
    if (STANDARD_SPECIFIC.includes(chartId)) {
      return 'standard';
    }
    
    // Obtener el prefijo (primera parte antes del guión)
    const prefix = chartId.split('-')[0];
    
    // Verificar por prefijo
    if (STANDARD_PREFIXES.includes(prefix)) {
      return 'standard';
    }
    
    if (ADVANCED_PREFIXES.includes(prefix)) {
      return 'advanced';
    }
    
    // Por defecto, clasificar como avanzado (conservador)
    console.warn('[ChartClassification] Unknown chart type:', chartId, '- defaulting to advanced');
    return 'advanced';
  }
  
  // ─── Función para filtrar lista de gráficos ────────────────────────────────
  
  function filterByClassification(charts, classification) {
    return charts.filter(chart => {
      const chartId = typeof chart === 'string' ? chart : chart.id;
      return classifyChart(chartId) === classification;
    });
  }
  
  // ─── Función para obtener estadísticas ─────────────────────────────────────
  
  function getClassificationStats(charts) {
    let standard = 0;
    let advanced = 0;
    
    charts.forEach(chart => {
      const chartId = typeof chart === 'string' ? chart : chart.id;
      if (classifyChart(chartId) === 'standard') {
        standard++;
      } else {
        advanced++;
      }
    });
    
    return { standard, advanced, total: charts.length };
  }

  // ─── Exportar API ──────────────────────────────────────────────────────────
  
  window.ChartClassification = {
    classifyChart: classifyChart,
    filterByClassification: filterByClassification,
    getClassificationStats: getClassificationStats,
    STANDARD_PREFIXES: STANDARD_PREFIXES,
    ADVANCED_PREFIXES: ADVANCED_PREFIXES,
    STANDARD_SPECIFIC: STANDARD_SPECIFIC,
    ADVANCED_SPECIFIC: ADVANCED_SPECIFIC
  };
  
  console.log('[ChartClassification] Module loaded');

})();
