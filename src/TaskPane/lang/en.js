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
    retry: "Retry",
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
    polynomial: "Polynomial",
    poly2: "Polynomial (degree 2)"
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
      ml: "Machine Learning",
      datasets: "Datasets",
      analisis_datos: "Data Analysis",
      regresion: "Regression",
      series_tiempo: "Time Series",
      mis_funciones: "My Functions",
      text_mining: "Text Mining",
      julia: "Julia"
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
      },
      
      // === ANALYSIS FUNCTIONS ===
      AD_ACP: {
        name: "Principal Components",
        description: "Reduces dataset dimensionality by projecting variables onto orthogonal principal components that maximize explained variance. Ideal for exploring structure, removing multicollinearity and visualizing multivariate data."
      },
      AD_ClusteringJerarquico: {
        name: "Hierarchical Clustering",
        description: "Groups observations using agglomerative hierarchical algorithm. Unlike K-Means, doesn't require specifying K beforehand and produces a dendrogram revealing clustering structure at multiple levels."
      },
      AD_KMedias: {
        name: "K-Means",
        description: "Groups observations into K clusters using K-Means algorithm. Allows data scaling and centroid update algorithm selection."
      },
      
      // === DATASETS ===
      DS_Wooldridge: {
        name: "Wooldridge Data",
        description: "Loads one of 115 datasets from Jeffrey M. Wooldridge's 'Introductory Econometrics' book directly into the analysis environment. Once loaded, the dataset is available for Regression, Data Analysis and Time Series."
      },
      DS_Wooldridge_Benchmark: {
        name: "Wooldridge Benchmark Suite",
        description: "STEP 1: Select the example and run WITHOUT assigning columns — dataset loads automatically. STEP 2: Assign Y and X with dataset columns and run again to see your estimation alongside the textbook's."
      },
      
      // === JULIA FUNCTIONS ===
      J_AD_Descriptiva: {
        name: "Descriptive Statistics (Julia)",
        description: "Calculates complete descriptive statistics (mean, median, std dev, quartiles, skewness, kurtosis) and correlation matrix for numeric columns. Implemented natively in Julia without external dependencies."
      },
      J_RG_Lineal: {
        name: "Linear Regression (Julia)",
        description: "OLS Linear Regression implemented with Julia's native linear algebra (no external dependencies). Returns coefficients, standard errors, t-stats, p-values, R², AIC, BIC and residuals table."
      },
      
      // === NEVEN CHART ===
      NEVEN_Chart: {
        name: "NEVEN.Chart — Embedded Charts",
        description: "Creates charts embedded directly in Excel as Shapes, using data from a range. Supports R (ggplot2), Python (matplotlib) and Julia (Plots.jl). Chart is inserted as image in active sheet and updates automatically when cell recalculates."
      },
      
      // === REGRESSION FUNCTIONS ===
      RG_2SLS: {
        name: "2SLS — Instrumental Variables (IV)",
        description: "Corrects endogeneity bias using external instruments Z. Includes automatic diagnostics: first-stage F (weak instruments if F<10), Wu-Hausman (confirms endogeneity) and Sargan (validates instruments). Wooldridge Ch. 15."
      },
      RG_ArbolDecision: {
        name: "Decision Tree",
        description: "Builds a decision tree for classification or regression using CART algorithm. Shows variable importance, performance metrics and tree rules."
      },
      RG_DatosPanel: {
        name: "Panel Data",
        description: "Estimates panel data models: OLS, Pooling, Within (fixed effects), Between, Random (random effects) and Pooled Fixed(t). Includes Hausman, Breusch-Pagan and autocorrelation tests."
      },
      RG_Davidson_MacKinnon: {
        name: "Davidson-MacKinnon J-Test",
        description: "Selection between two NON-nested linear models (alternative models with different specifications). Indicates which model better captures Y variation. Wooldridge Ch. 9."
      },
      RG_FGLS: {
        name: "FGLS — Feasible Generalized Least Squares",
        description: "Efficient heteroskedasticity correction when its structure depends on regressors. Unlike Newey-West (which only corrects SE), FGLS produces more efficient coefficients. Implemented as WLS weighted by estimated variance. Wooldridge Ch. 8."
      },
      RG_HECKIT: {
        name: "Heckman (Heckit) — Selection Bias Correction",
        description: "Corrects bias when sample is not random (e.g., we only observe wages for those who work). 2-stage model: Selection Probit → OLS with Inverse Mills Ratio (λ). If λ is significant, there's selection bias. Wooldridge Ch. 17."
      },
      RG_Lineal: {
        name: "Linear Regression",
        description: "Estimates the linear relationship between a numeric dependent variable and one or more independent variables. Returns coefficients, fit metrics (R2, AIC, BIC) and residuals plot."
      },
      RG_Logistica: {
        name: "Logistic Regression",
        description: "Models the probability of a binary event (0/1) using Logit or Probit models. Returns coefficients, Odds Ratios, fit metrics (McFadden R2, accuracy) and probability curve."
      },
      RG_Newey_West: {
        name: "Newey-West Robust Standard Errors (HAC)",
        description: "Corrects OLS standard errors for unknown heteroskedasticity and autocorrelation. Coefficients don't change, only SE, t-stats and p-values. Essential for time series and panel data. Wooldridge Ch. 12/15."
      },
      RG_Poisson: {
        name: "Poisson Regression",
        description: "Models count variables using Poisson distribution with log link. Includes overdispersion test and returns IRR (Incidence Rate Ratios) in addition to standard coefficients."
      },
      RG_RESET: {
        name: "Ramsey RESET Test",
        description: "Detects functional form errors in an OLS model. A small p-value indicates the model is misspecified (omitted variables, non-linearities). Wooldridge Ch. 9."
      },
      RG_SeriesTiempo: {
        name: "Time Series Analysis",
        description: "Analyzes a univariate time series or with exogenous variables (Y_t ~ X_t): descriptive statistics, Augmented Dickey-Fuller (ADF) unit root test, autocorrelation function (ACF/PACF) and interactive plot. If X variables assigned, additionally estimates dynamic regression with Stargazer table."
      },
      RG_SVM: {
        name: "Support Vector Machines",
        description: "Applies SVM for binary classification or regression. Supports Linear, Polynomial, RBF and Sigmoid kernels. Requires e1071 package."
      },
      RG_Tobit: {
        name: "Tobit Regression",
        description: "Models dependent variables with censoring or truncation (e.g., expenses >= 0, hours worked). Estimates latent coefficients and actual marginal effects using maximum likelihood. Requires VGAM package."
      },
      
      // === TIME SERIES ===
      ST_ECM: {
        name: "ECM / VECM — Error Correction Model",
        description: "Detects cointegration and estimates speed of adjustment to long-run equilibrium. Complete flow: ADF for unit roots → Johansen for cointegration → VECM if cointegrated, VAR in differences if not. Wooldridge Ch. 18."
      },
      ST_VAR: {
        name: "VAR — Vector Autoregression",
        description: "Models the joint dynamics of 2+ time series. Automatically selects optimal order p (AIC/BIC/HQ/FPE), estimates the system and generates forecasts with 95% confidence intervals. Wooldridge Ch. 18."
      },
      
      // === TEXT MINING ===
      TM_TextAnalysis: {
        name: "Text Analysis (PDF/TXT/DOCX)",
        description: "Analyzes a document from PDF, TXT or DOCX file. Enter the full file path and get: lexical statistics, sentiment, automatic extractive summary and word frequency with interactive chart. No prior dataset required."
      },
      
      // === USER CREATED EXAMPLES ===
      UC_EjemploAvanzado: {
        name: "Advanced Example (Y~X Correlations)",
        description: "Advanced example function: calculates correlations between a Y variable and multiple X variables, with interactive bar chart. Shows complete pattern with Y~X roles, select-type parameters and plotly chart."
      },
      UC_EjemploBasico: {
        name: "Basic Example (Statistics)",
        description: "Example function: calculates descriptive statistics for any set of numeric columns. Serves as starting point for creating your own Data Lab functions."
      },
      UC_EjemploFactoMineR: {
        name: "PCA with FactoMineR (Library Example)",
        description: "Example demonstrating how to integrate an external library (FactoMineR) in Data Lab. Performs complete PCA: explained variance, variable coordinates, contributions, cos2 (representation quality) and interactive biplot with individuals and variables overlaid."
      }
    }
  },

  // ─────────────────────────────────────────────────────────────────────────
  // DATA AI
  // ─────────────────────────────────────────────────────────────────────────
  dataIA: {
    title: "AI Assistant",
    assistant: "AI ASSISTANT",
    guidePrompts: "GUIDE PROMPTS",
    promptPlaceholder: "Type your question... (Enter sends, Shift+Enter new line)",
    analyzing: "Analyzing with AI...",
    thinking: "thinking...",
    suggestions: "Suggestions",
    applyCode: "Apply code",
    explainMore: "Explain more",
    send: "Send",
    addDataset: "+ Dataset",
    analyzeSheet: "Analyze Sheet",
    analyzeWorkbook: "Analyze Workbook",
    clear: "Clear",
    exportChat: "Export Chat",
    excelConsultant: "Excel Consultant"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ECONOMETRICS
  // ─────────────────────────────────────────────────────────────────────────
  econometria: {
    title: "Econometrics",
    labTitle: "Geometric Lab: Linear Algebra and Econometrics",
    labSubtitle: "Interact with the sliders and ask the AI Professor.",
    tab1: "1. OLS Projection",
    tab2: "2. Panel / FWL",
    tab3: "3. GLS / Cholesky",
    tab4: "4. Unit Root",
    model: "Model",
    dependent: "Dependent variable",
    independent: "Independent variables",
    estimate: "Estimate",
    diagnostics: "Diagnostics",
    residuals: "Residuals",
    coefficients: "Coefficients",
    professor: "Econometrics Professor",
    professorHint: "uses RAG with 10 indexed books",
    askPlaceholder: "Ask about what you see...",
    askButton: "Ask",
    // OLS Projection
    subspaceAngle: "Subspace Angle C(X)",
    degrees: "degrees",
    regressorPlane: "Regressor plane inclination. Small angles = multicollinearity.",
    vectorYDirection: "Vector y Direction",
    dependentVar: "Dependent variable. Closer to C(X) = higher R².",
    geometryOLS: "OLS Geometry",
    geometryOLSDesc: "The vector y is projected onto C(X). The projection is y-hat (green), the residual is epsilon (red, always perpendicular).",
    experiment: "Experiment",
    experimentOLS: "Move y closer to C(X) and watch R² increase.",
    // Panel / FWL
    withinOperator: "Within Operator",
    pooledOLS: "0 = Pooled OLS, 1 = Fixed Effects (centers each group).",
    trueBeta: "true",
    bias: "Bias",
    simpsonParadox: "Simpson's Paradox",
    simpsonDesc: "Three individuals with different intercepts. Pooled OLS sees negative slope because it confuses individual effects with the effect of X.",
    solution: "Solution",
    solutionFWL: "Raise theta to 1. The Within operator centers each group, revealing the true slope +0.80.",
    // GLS / Cholesky
    heteroskedasticity: "Heteroskedasticity",
    varianceRatio: "Variance ratio. 1x = homoskedastic.",
    autocorrelation: "Autocorrelation",
    serialCorr: "Serial correlation. Tilts the ellipsoid.",
    choleskyTransform: "Cholesky Transformation",
    applyC: "Apply C such that Omega^-1 = CC.",
    glsTransforms: "GLS transforms the space",
    glsDesc: "The ellipses are isodensity curves of epsilon. With heteroskedasticity/autocorrelation, OLS loses efficiency.",
    solutionGLS: "Slide Cholesky to 100%. The ellipsoid becomes a sphere: OLS = GLS.",
    // Unit Root
    dominantEigenvalue: "Dominant Eigenvalue",
    lambdaPosition: "Position of lambda in the complex plane.",
    integration: "Integration",
    spectrum: "Spectrum",
    unitCircle: "Unit circle",
    unitCircleDesc: "If |lambda| < 1, the series is stationary I(0). If |lambda| = 1, it's unit root I(1) with infinite memory.",
    danger: "Danger",
    dangerDesc: "With I(1), OLS produces spurious regression (high R² without causality).",
    experimentUR: "Move lambda to 1.0 and observe how the trajectory stops reverting to the mean."
  },

  // ─────────────────────────────────────────────────────────────────────────
  // PRESENTATIONS
  // ─────────────────────────────────────────────────────────────────────────
  presentaciones: {
    title: "Presentations",
    newSlide: "+ Slide",
    preview: "Preview",
    export: "Export",
    slideTitle: "Slide title",
    addContent: "Add content",
    exportPPT: "Export to PowerPoint",
    exportPDF: "Export to PDF",
    slides: "SLIDES",
    content: "CONTENT",
    position: "POSITION",
    style: "STYLE",
    text: "TEXT",
    slideContent: "Slide content",
    slideType: "SLIDE TYPE",
    textType: "Text",
    sendToSlide: "Send to Slide",
    sent: "Sent"
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RUN SCRIPT
  // ─────────────────────────────────────────────────────────────────────────
  runScript: {
    title: "Run Script",
    language: "Language:",
    untitled: "untitled",
    newScript: "New script",
    runCode: "Run",
    open: "Open",
    saveAs: "Save as",
    new: "New",
    examples: "Examples...",
    availableFunctions: "AVAILABLE FUNCTIONS",
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
