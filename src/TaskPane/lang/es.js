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
    or: "o"
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
      timeseries: "Serie de Tiempo"
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
    selectProcedure: "Seleccionar procedimiento",
    parameters: "Parámetros",
    runAnalysis: "Ejecutar análisis",
    results: "Resultados",
    groupBy: "Agrupar por",
    groupColumn: "Columna de grupo",
    valueColumn: "Columna de valor",
    aggregation: "Agregación"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // DATA IA
  // ─────────────────────────────────────────────────────────────────────────
  dataIA: {
    title: "Asistente IA",
    promptPlaceholder: "Describe qué análisis deseas realizar...",
    analyzing: "Analizando con IA...",
    suggestions: "Sugerencias",
    applyCode: "Aplicar código",
    explainMore: "Explicar más"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ECONOMETRÍA
  // ─────────────────────────────────────────────────────────────────────────
  econometria: {
    title: "Econometría",
    model: "Modelo",
    dependent: "Variable dependiente",
    independent: "Variables independientes",
    estimate: "Estimar",
    diagnostics: "Diagnósticos",
    residuals: "Residuos",
    coefficients: "Coeficientes"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // PRESENTACIONES
  // ─────────────────────────────────────────────────────────────────────────
  presentaciones: {
    title: "Presentaciones",
    newSlide: "Nueva diapositiva",
    slideTitle: "Título de diapositiva",
    addContent: "Agregar contenido",
    exportPPT: "Exportar a PowerPoint",
    exportPDF: "Exportar a PDF"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RUN SCRIPT
  // ─────────────────────────────────────────────────────────────────────────
  runScript: {
    title: "Run Script",
    language: "Lenguaje",
    newScript: "Nuevo script",
    runCode: "Ejecutar",
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
    dataPath: "Ruta de datos"
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
