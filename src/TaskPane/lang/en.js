// ═══════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Internationalization Dictionary (English)
// ═══════════════════════════════════════════════════════════════════════════
// File: lang/en.js
// Usage: const text = LANG.tabs.dataStudio; // "Data Studio"
// ═══════════════════════════════════════════════════════════════════════════

const LANG_EN = {

  // ─────────────────────────────────────────────────────────────────────────
  // TABS
  // ─────────────────────────────────────────────────────────────────────────
  tabs: {
    dataStudio: "Data Studio",
    dataLab: "Data Lab",
    dataIA: "Data AI",
    econometria: "Econometrics",
    presentaciones: "Presentations",
    runScript: "Run Script",
    settings: "Settings",
    ayuda: "Help"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // COMMON BUTTONS
  // ─────────────────────────────────────────────────────────────────────────
  buttons: {
    run: "Run",
    load: "Load",
    save: "Save",
    cancel: "Cancel",
    close: "Close",
    send: "Send",
    sendToSlide: "Send to Slide",
    openFile: "Open file",
    readFromExcel: "Read from Excel",
    pasteFromExcel: "Paste from Excel",
    connectDB: "Connect DB",
    newScript: "New",
    openPivot: "Open Pivot",
    generate: "Generate",
    download: "Download",
    copy: "Copy",
    refresh: "Refresh",
    start: "Start",
    stop: "Stop",
    restart: "Restart",
    test: "Test",
    apply: "Apply"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // LABELS AND TITLES
  // ─────────────────────────────────────────────────────────────────────────
  labels: {
    language: "Language",
    examples: "Examples...",
    loadExample: "Load example...",
    output: "Output",
    console: "Console",
    preview: "Preview",
    rows: "rows",
    columns: "columns",
    data: "Data",
    chart: "Chart",
    table: "Table",
    recent: "Recent",
    availableFunctions: "Available Functions",
    search: "Search...",
    noData: "No data",
    selectFile: "Select file",
    dragDropHere: "Drag files here",
    or: "or"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // STATUS MESSAGES
  // ─────────────────────────────────────────────────────────────────────────
  messages: {
    loading: "Loading...",
    executing: "Executing...",
    processing: "Processing...",
    saving: "Saving...",
    success: "Success",
    error: "Error",
    warning: "Warning",
    info: "Information",
    timeout: "Request timed out",
    connectionError: "Connection error",
    noResults: "No results",
    confirmDelete: "Are you sure you want to delete?",
    unsavedChanges: "There are unsaved changes",
    loadExampleConfirm: "There are unsaved changes. Load example?",
    serverUnavailable: "Server unavailable",
    engineNotRunning: "Engine is not running"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // DATA STUDIO
  // ─────────────────────────────────────────────────────────────────────────
  dataStudio: {
    title: "Data",
    openFileHint: "Open a CSV, TSV or JSON file",
    recentFiles: "Recent",
    listeningChanges: "Listening for changes",
    disconnect: "Disconnect",
    quickChart: "Quick Chart",
    chartType: "Chart type",
    xAxis: "X Axis",
    yAxis: "Y Axis",
    selectColumns: "Select columns",
    generateChart: "Generate chart",
    // Chart types
    chartTypes: {
      bar: "Bar",
      line: "Line",
      scatter: "Scatter",
      pie: "Pie",
      area: "Area",
      histogram: "Histogram",
      boxplot: "Box Plot",
      heatmap: "Heatmap",
      timeseries: "Time Series",
      map: "Map (Lat/Lon)",
      bubble: "Bubble",
      radar: "Radar",
      treemap: "Treemap",
      sankey: "Sankey",
      sunburst: "Sunburst",
      funnel: "Funnel"
    },
    // Options
    showTrend: "Show trend",
    trendType: "Trend type",
    linear: "Linear",
    polynomial: "Polynomial"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // DATA LAB
  // ─────────────────────────────────────────────────────────────────────────
  dataLab: {
    title: "Data Lab",
    selectProcedure: "Select procedure",
    parameters: "Parameters",
    runAnalysis: "Run analysis",
    results: "Results",
    groupBy: "Group by",
    groupColumn: "Group column",
    valueColumn: "Value column",
    aggregation: "Aggregation"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // DATA AI
  // ─────────────────────────────────────────────────────────────────────────
  dataIA: {
    title: "AI Assistant",
    promptPlaceholder: "Describe what analysis you want to perform...",
    analyzing: "Analyzing with AI...",
    suggestions: "Suggestions",
    applyCode: "Apply code",
    explainMore: "Explain more"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ECONOMETRICS
  // ─────────────────────────────────────────────────────────────────────────
  econometria: {
    title: "Econometrics",
    model: "Model",
    dependent: "Dependent variable",
    independent: "Independent variables",
    estimate: "Estimate",
    diagnostics: "Diagnostics",
    residuals: "Residuals",
    coefficients: "Coefficients"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // PRESENTATIONS
  // ─────────────────────────────────────────────────────────────────────────
  presentaciones: {
    title: "Presentations",
    newSlide: "New slide",
    slideTitle: "Slide title",
    addContent: "Add content",
    exportPPT: "Export to PowerPoint",
    exportPDF: "Export to PDF"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RUN SCRIPT
  // ─────────────────────────────────────────────────────────────────────────
  runScript: {
    title: "Run Script",
    language: "Language",
    newScript: "New script",
    runCode: "Run",
    outputTitle: "Output",
    consoleTitle: "Console",
    timeoutMessage: "Request timed out (120s). The script may still be running in the engine.",
    fallbackMessage: "Using Office.js fallback",
    // Example groups
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
    title: "Settings",
    general: "General",
    language: "Language",
    languageHint: "Changes apply immediately",
    theme: "Theme",
    engines: "Engines",
    engineStatus: "Engine status",
    autoStart: "Auto-start",
    rEngine: "R Engine",
    juliaEngine: "Julia Engine",
    pythonEngine: "Python Engine",
    running: "Running",
    stopped: "Stopped",
    starting: "Starting...",
    version: "Version",
    about: "About",
    checkUpdates: "Check for updates",
    serverPort: "Server port",
    dataPath: "Data path"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // HELP
  // ─────────────────────────────────────────────────────────────────────────
  ayuda: {
    title: "Help",
    documentation: "Documentation",
    tutorials: "Tutorials",
    shortcuts: "Keyboard shortcuts",
    about: "About NEVEN",
    version: "Version",
    reportBug: "Report a bug",
    searchHelp: "Search help..."
  },

  // ─────────────────────────────────────────────────────────────────────────
  // SPECIFIC ERRORS
  // ─────────────────────────────────────────────────────────────────────────
  errors: {
    fileNotFound: "File not found",
    invalidFormat: "Invalid format",
    parseError: "Parse error",
    networkError: "Network error",
    permissionDenied: "Permission denied",
    engineNotAvailable: "Engine not available",
    sqlError: "SQL error"
  }

};

// Export for global use
if (typeof window !== 'undefined') {
  window.LANG_EN = LANG_EN;
}
