// ═══════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Diccionario de Internacionalización (Español)
// ═══════════════════════════════════════════════════════════════════════════
// Archivo: lang/es.js
// Uso: const text = LANG.tabs.dataStudio; // "Data Studio"
// ═══════════════════════════════════════════════════════════════════════════

const LANG_ES = {

  // ─────────────────────────────────────────────────────────────────────────
  // TABS
  // ─────────────────────────────────────────────────────────────────────────
  tabs: {
    dataStudio: "Data Studio",
    dataLab: "Data Lab",
    dataIA: "Data IA",
    econometria: "Econometría",
    presentaciones: "Presentaciones",
    runScript: "Run Script",
    settings: "Configuración",
    ayuda: "Ayuda"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // BOTONES COMUNES
  // ─────────────────────────────────────────────────────────────────────────
  buttons: {
    run: "Ejecutar",
    load: "Cargar",
    save: "Guardar",
    cancel: "Cancelar",
    close: "Cerrar",
    send: "Enviar",
    sendToSlide: "Enviar a Slide",
    openFile: "Abrir archivo",
    readFromExcel: "Leer de Excel",
    pasteFromExcel: "Pegar de Excel",
    connectDB: "Conectar DB",
    newScript: "Nuevo",
    openPivot: "Abrir Pivot",
    generate: "Generar",
    download: "Descargar",
    copy: "Copiar",
    refresh: "Actualizar",
    retry: "Reintentar",
    start: "Iniciar",
    stop: "Detener",
    restart: "Reiniciar",
    test: "Probar",
    apply: "Aplicar"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ETIQUETAS Y TÍTULOS
  // ─────────────────────────────────────────────────────────────────────────
  labels: {
    language: "Idioma",
    examples: "Ejemplos...",
    loadExample: "Cargar ejemplo...",
    output: "Output",
    console: "Consola",
    preview: "Vista previa",
    rows: "filas",
    columns: "columnas",
    data: "Datos",
    chart: "Gráfico",
    table: "Tabla",
    recent: "Recientes",
    availableFunctions: "Funciones disponibles",
    search: "Buscar...",
    noData: "Sin datos",
    selectFile: "Seleccionar archivo",
    dragDropHere: "Arrastra archivos aquí",
    or: "o",
    connected: "Conectado",
    disconnected: "Desconectado",
    excelConnected: "Excel conectado",
    listeningChanges: "Escuchando cambios",
    pivotTable: "Pivot Table",
    xAxis: "- Eje X -",
    yAxis: "- Eje Y -",
    trend: "Tendencia",
    linear: "Lineal",
    polynomial: "Polinomial",
    poly2: "Polinómica (grado 2)"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // MENSAJES DE ESTADO
  // ─────────────────────────────────────────────────────────────────────────
  messages: {
    loading: "Cargando...",
    executing: "Ejecutando...",
    processing: "Procesando...",
    saving: "Guardando...",
    success: "Éxito",
    error: "Error",
    warning: "Advertencia",
    info: "Información",
    timeout: "Tiempo de espera agotado",
    connectionError: "Error de conexión",
    noResults: "Sin resultados",
    confirmDelete: "¿Está seguro de eliminar?",
    unsavedChanges: "Hay cambios sin guardar",
    loadExampleConfirm: "Hay cambios sin guardar. ¿Cargar ejemplo?",
    serverUnavailable: "Servidor no disponible",
    engineNotRunning: "Motor no está ejecutándose"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // DATA STUDIO
  // ─────────────────────────────────────────────────────────────────────────
  dataStudio: {
    title: "Datos",
    openFileHint: "Abra un archivo CSV, TSV o JSON",
    recentFiles: "Recientes",
    listeningChanges: "Escuchando cambios",
    disconnect: "Desconectar",
    quickChart: "Gráfico Rápido",
    chartType: "Tipo de gráfico",
    xAxis: "Eje X",
    yAxis: "Eje Y",
    selectColumns: "Seleccionar columnas",
    generateChart: "Generar gráfico",
    // Tipos de gráfico
    chartTypes: {
      bar: "Barras",
      line: "Líneas",
      scatter: "Dispersión",
      pie: "Pastel",
      area: "Área",
      histogram: "Histograma",
      boxplot: "Box Plot",
      heatmap: "Heatmap",
      timeseries: "Serie Temporal",
      map: "Mapa (Lat/Lon)",
      bubble: "Burbujas",
      radar: "Radar",
      treemap: "Treemap",
      sankey: "Sankey",
      sunburst: "Sunburst",
      funnel: "Embudo"
    },
    // Opciones
    showTrend: "Mostrar tendencia",
    trendType: "Tipo de tendencia",
    linear: "Lineal",
    polynomial: "Polinomial"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // DATA LAB
  // ─────────────────────────────────────────────────────────────────────────
  dataLab: {
    title: "Data Lab",
    selectFunction: "Seleccionar función",
    selectFamily: "-- Seleccione una familia --",
    aboutMethod: "Sobre este método",
    goToWikipedia: "🌐 Ir a Wikipedia",
    selectProcedure: "Seleccionar procedimiento",
    familyPlaceholder: "- Familia -",
    parameters: "Parámetros",
    runAnalysis: "Ejecutar análisis",
    verifyPackages: "Verificar paquetes",
    results: "Resultados",
    groupBy: "Agrupar por",
    groupColumn: "Columna de grupo",
    valueColumn: "Columna de valor",
    aggregation: "Agregación",
    
    // Familias de funciones
    families: {
      graficos: "Gráficos",
      estadistica: "Estadística",
      econometria: "Econometría",
      ml: "Machine Learning",
      datasets: "Datasets",
      analisis_datos: "Análisis de Datos",
      regresion: "Regresión",
      series_tiempo: "Series de Tiempo",
      mis_funciones: "Mis Funciones",
      text_mining: "Text Mining",
      julia: "Julia"
    },
    
    // Funciones individuales (nombre y descripción)
    functions: {
      GR_Barras: {
        name: "Gráfico de Barras",
        description: "Gráfico de barras con soporte para modo agrupado, apilado, horizontal y vertical. Permite mostrar etiquetas de valores y ordenar las categorías."
      },
      GR_BoxPlot: {
        name: "Box Plot (Diagrama de Caja)",
        description: "Diagrama de caja y bigotes. Muestra la distribución estadística (mediana, cuartiles, outliers) por grupo o categoría."
      },
      GR_Correlaciones: {
        name: "Mapa de Correlaciones",
        description: "Heatmap de la matriz de correlaciones entre variables numéricas. Muestra la fuerza y dirección de las relaciones lineales (o de rango)."
      },
      GR_Histograma: {
        name: "Histograma",
        description: "Distribución de frecuencias de una variable numérica. Muestra la forma de la distribución, moda y dispersión."
      },
      GR_Lineas: {
        name: "Gráfico de Líneas",
        description: "Gráfico de líneas para visualizar tendencias y evolución. Permite múltiples series usando una variable de color/grupo."
      },
      GR_Scatter: {
        name: "Scatter Plot",
        description: "Gráfico de dispersión interactivo. Muestra la relación entre dos variables numéricas. Soporte para color por categoría, tamaño de punto y etiquetas de hover."
      },
      GR_SerieTiempo: {
        name: "Serie de Tiempo",
        description: "Gráfico de líneas para series temporales. Permite visualizar la evolución de una o más métricas en el tiempo, con opción de línea de tendencia."
      },
      GR_Mapa: {
        name: "Mapa Interactivo (Leaflet)",
        description: "Mapa interactivo con Leaflet.js usando tiles CartoDB oscuros. Soporta marcadores con popup, mapa de calor e intensidad, y círculos proporcionales a un valor."
      },
      GR_Bubble: {
        name: "Ejemplo Avanzado (Gráfico de Burbujas)",
        description: "Plantilla completa para gráficos en Data Lab. Muestra el patrón avanzado: 4 roles (2 opcionales), hovertemplate personalizado, escala de tamaño, parámetros tier 1 y tier 2. Cópialo para crear gráficos con más complejidad."
      },
      GR_Basico: {
        name: "Ejemplo Básico (Scatter Mínimo)",
        description: "Plantilla mínima para crear gráficos en Data Lab. Muestra el patrón básico: 2 roles X e Y, parámetros simples, y retorno con r_object_to_slots. Cópialo como punto de partida para tu propio tipo de gráfico."
      }
    }
  },

  // ─────────────────────────────────────────────────────────────────────────
  // DATA IA
  // ─────────────────────────────────────────────────────────────────────────
  dataIA: {
    title: "Asistente IA",
    assistant: "ASISTENTE IA",
    guidePrompts: "PROMPTS GUÍA",
    promptPlaceholder: "Escribe tu pregunta... (Enter envía, Shift+Enter nueva línea)",
    analyzing: "Analizando con IA...",
    thinking: "pensando...",
    suggestions: "Sugerencias",
    applyCode: "Aplicar código",
    explainMore: "Explicar más",
    send: "Enviar",
    addDataset: "+ Dataset",
    analyzeSheet: "Analizar Hoja",
    analyzeWorkbook: "Analizar Libro",
    clear: "Limpiar",
    exportChat: "Exportar Chat",
    excelConsultant: "Consultor Excel"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ECONOMETRÍA
  // ─────────────────────────────────────────────────────────────────────────
  econometria: {
    title: "Econometría",
    labTitle: "Laboratorio Geométrico: Álgebra Lineal y Econometría",
    labSubtitle: "Interactúa con los deslizadores y pregunta al Profesor IA.",
    tab1: "1. Proyección OLS",
    tab2: "2. Panel / FWL",
    tab3: "3. GLS / Cholesky",
    tab4: "4. Raíz Unitaria",
    model: "Modelo",
    dependent: "Variable dependiente",
    independent: "Variables independientes",
    estimate: "Estimar",
    diagnostics: "Diagnósticos",
    residuals: "Residuos",
    coefficients: "Coeficientes",
    professor: "Profesor de Econometría",
    professorHint: "usa RAG con 10 libros indexados",
    askPlaceholder: "Pregunta sobre lo que ves...",
    askButton: "Preguntar",
    // OLS Projection
    subspaceAngle: "Ángulo del Subespacio C(X)",
    degrees: "grados",
    regressorPlane: "Inclinación del plano de regresores. Ángulos pequeños = multicolinealidad.",
    vectorYDirection: "Dirección del Vector y",
    dependentVar: "Variable dependiente. Más cerca de C(X) = mayor R².",
    geometryOLS: "Geometría OLS",
    geometryOLSDesc: "El vector y se proyecta sobre C(X). La proyección es y-hat (verde), el residuo es epsilon (rojo, siempre perpendicular).",
    experiment: "Experimento",
    experimentOLS: "Acerca y a C(X) y observa como sube el R².",
    // Panel / FWL
    withinOperator: "Operador Within",
    pooledOLS: "0 = Pooled OLS, 1 = Efectos Fijos (centra cada grupo).",
    trueBeta: "verdadero",
    bias: "Sesgo",
    simpsonParadox: "Paradoja de Simpson",
    simpsonDesc: "Tres individuos con diferentes interceptos. Pooled OLS ve pendiente negativa porque confunde efectos individuales con el efecto de X.",
    solution: "Solución",
    solutionFWL: "Sube theta a 1. El operador Within centra cada grupo, revelando la verdadera pendiente +0.80.",
    // GLS / Cholesky
    heteroskedasticity: "Heterocedasticidad",
    varianceRatio: "Ratio de varianzas. 1x = homocedástico.",
    autocorrelation: "Autocorrelación",
    serialCorr: "Correlación serial. Inclina el elipsoide.",
    choleskyTransform: "Transformación Cholesky",
    applyC: "Aplica C tal que Omega^-1 = CC.",
    glsTransforms: "GLS transforma el espacio",
    glsDesc: "Las elipses son curvas de isodensidad de epsilon. Con heterocedasticidad/autocorrelación, OLS pierde eficiencia.",
    solutionGLS: "Desliza Cholesky al 100%. El elipsoide se vuelve esfera: OLS = GLS.",
    // Unit Root
    dominantEigenvalue: "Autovalor Dominante",
    lambdaPosition: "Posición de lambda en el plano complejo.",
    integration: "Integración",
    spectrum: "Espectro",
    unitCircle: "Círculo unitario",
    unitCircleDesc: "Si |lambda| < 1, la serie es estacionaria I(0). Si |lambda| = 1, es raíz unitaria I(1) con memoria infinita.",
    danger: "Peligro",
    dangerDesc: "Con I(1), OLS produce regresión espuria (R² alto sin causalidad).",
    experimentUR: "Lleva lambda a 1.0 y observa como la trayectoria deja de revertir a la media."
  },

  // ─────────────────────────────────────────────────────────────────────────
  // PRESENTACIONES
  // ─────────────────────────────────────────────────────────────────────────
  presentaciones: {
    title: "Presentaciones",
    newSlide: "+ Slide",
    preview: "Preview",
    export: "Exportar",
    slideTitle: "Título de diapositiva",
    addContent: "Agregar contenido",
    exportPPT: "Exportar a PowerPoint",
    exportPDF: "Exportar a PDF",
    slides: "SLIDES",
    content: "CONTENIDO",
    position: "POSICIÓN",
    style: "ESTILO",
    text: "TEXTO",
    slideContent: "Contenido del slide",
    slideType: "TIPO DE SLIDE",
    textType: "Texto",
    sendToSlide: "Enviar a Slide",
    sent: "Enviado"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RUN SCRIPT
  // ─────────────────────────────────────────────────────────────────────────
  runScript: {
    title: "Run Script",
    language: "Lenguaje:",
    untitled: "sin título",
    newScript: "Nuevo script",
    runCode: "Ejecutar",
    open: "Abrir",
    saveAs: "Guardar como",
    new: "Nuevo",
    examples: "Ejemplos...",
    availableFunctions: "FUNCIONES DISPONIBLES",
    outputTitle: "Output",
    consoleTitle: "Consola",
    timeoutMessage: "Tiempo de espera agotado (120s). El script puede seguir ejecutándose en el motor.",
    fallbackMessage: "Usando fallback Office.js",
    // Grupos de ejemplos
    exampleGroups: {
      r: "R",
      python: "Python",
      julia: "Julia",
      sql: "SQL (DuckDB)"
    }
  },

  // ─────────────────────────────────────────────────────────────────────────
  // SETTINGS
  // ─────────────────────────────────────────────────────────────────────────
  settings: {
    title: "Configuración",
    general: "General",
    language: "Idioma",
    languageHint: "El cambio se aplica inmediatamente",
    theme: "Tema",
    engines: "Motores",
    engineStatus: "Estado de motores",
    autoStart: "Inicio automático",
    rEngine: "Motor R",
    juliaEngine: "Motor Julia",
    pythonEngine: "Motor Python",
    running: "Ejecutándose",
    stopped: "Detenido",
    starting: "Iniciando...",
    version: "Versión",
    about: "Acerca de",
    checkUpdates: "Buscar actualizaciones",
    serverPort: "Puerto del servidor",
    dataPath: "Ruta de datos",
    
    // Sub-tabs
    subtabs: {
      general: "General",
      aiEngine: "Motor IA",
      dbConnections: "Conexiones DB",
      prompts: "Prompts",
      knowledge: "Conocimiento",
      rag: "RAG",
      notebooks: "Notebooks",
      engines: "Motores",
      charts: "Gráficos"
    }
  },

  // ─────────────────────────────────────────────────────────────────────────
  // AYUDA
  // ─────────────────────────────────────────────────────────────────────────
  ayuda: {
    title: "Ayuda",
    documentation: "Documentación",
    tutorials: "Tutoriales",
    shortcuts: "Atajos de teclado",
    about: "Acerca de NEVEN",
    version: "Versión",
    reportBug: "Reportar error",
    searchHelp: "Buscar en ayuda..."
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ERRORES ESPECÍFICOS
  // ─────────────────────────────────────────────────────────────────────────
  errors: {
    fileNotFound: "Archivo no encontrado",
    invalidFormat: "Formato inválido",
    parseError: "Error al procesar",
    networkError: "Error de red",
    permissionDenied: "Permiso denegado",
    engineNotAvailable: "Motor no disponible",
    sqlError: "Error SQL"
  }

};

// Exportar para uso global
if (typeof window !== 'undefined') {
  window.LANG_ES = LANG_ES;
}
