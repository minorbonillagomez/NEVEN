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
    or: "or",
    connected: "Connected",
    disconnected: "Disconnected",
    listeningChanges: "Listening for changes",
    pivotTable: "Pivot Table",
    xAxis: "- X Axis -",
    yAxis: "- Y Axis -",
    trend: "Trend",
    linear: "Linear",
    polynomial: "Polynomial"
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
    selectFunction: "Select function",
    selectFamily: "-- Select a family --",
    aboutMethod: "About this method",
    goToWikipedia: "🌐 Go to Wikipedia",
    selectProcedure: "Select procedure",
    familyPlaceholder: "- Family -",
    parameters: "Parameters",
    runAnalysis: "Run analysis",
    verifyPackages: "Verify packages",
    results: "Results",
    groupBy: "Group by",
    groupColumn: "Group column",
    valueColumn: "Value column",
    aggregation: "Aggregation",
    
    // Function families
    families: {
      graficos: "Charts",
      estadistica: "Statistics",
      econometria: "Econometrics",
      ml: "Machine Learning"
    },
    
    // Individual functions (name and description)
    functions: {
      GR_Barras: {
        name: "Bar Chart",
        description: "Bar chart with support for grouped, stacked, horizontal and vertical modes. Shows value labels and allows category sorting."
      },
      GR_BoxPlot: {
        name: "Box Plot",
        description: "Box and whisker plot. Shows statistical distribution (median, quartiles, outliers) by group or category."
      },
      GR_Correlaciones: {
        name: "Correlation Map",
        description: "Heatmap of correlation matrix between numeric variables. Shows strength and direction of linear (or rank) relationships."
      },
      GR_Histograma: {
        name: "Histogram",
        description: "Frequency distribution of a numeric variable. Shows distribution shape, mode and dispersion."
      },
      GR_Lineas: {
        name: "Line Chart",
        description: "Line chart to visualize trends and evolution. Supports multiple series using a color/group variable."
      },
      GR_Scatter: {
        name: "Scatter Plot",
        description: "Interactive scatter plot. Shows relationship between two numeric variables. Supports color by category, point size and hover labels."
      },
      GR_SerieTiempo: {
        name: "Time Series",
        description: "Line chart for time series data. Visualize evolution of one or more metrics over time, with optional trend line."
      },
      GR_Mapa: {
        name: "Interactive Map (Leaflet)",
        description: "Interactive map with Leaflet.js using dark CartoDB tiles. Supports markers with popup, heatmap intensity, and circles proportional to a value."
      },
      GR_Bubble: {
        name: "Advanced Example (Bubble Chart)",
        description: "Complete template for Data Lab charts. Shows advanced pattern: 4 roles (2 optional), custom hovertemplate, size scale, tier 1 and tier 2 parameters. Copy it to create more complex charts."
      },
      GR_Basico: {
        name: "Basic Example (Minimal Scatter)",
        description: "Minimal template for Data Lab charts. Shows basic pattern: 2 roles X and Y, simple parameters, return with r_object_to_slots. Copy as starting point for your own chart type."
      }
    }
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
    dataPath: "Data path",
    
    // Sub-tabs
    subtabs: {
      general: "General",
      aiEngine: "AI Engine",
      dbConnections: "DB Connections",
      prompts: "Prompts",
      knowledge: "Knowledge",
      rag: "RAG",
      notebooks: "Notebooks",
      engines: "Engines",
      charts: "Charts"
    }
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
