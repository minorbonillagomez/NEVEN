# Documento de Diseño: Visor WebView2 Embebido para RJ2XCL

## Overview

Este diseño integra el runtime Microsoft Edge WebView2 dentro del add-in XLL de RJ2XCL para renderizar contenido HTML interactivo (Plotly, D3.js, htmlwidgets, DT, leaflet) directamente en ventanas flotantes asociadas a Excel, eliminando la necesidad de abrir el navegador externo.

El flujo actual genera archivos HTML y devuelve fórmulas HYPERLINK a la celda. El nuevo flujo intercepta el contenido HTML en el Content Pipeline, lo transmite vía Protobuf con un nuevo campo `html_content`, y lo renderiza en una ventana Win32 modeless que hospeda un `ICoreWebView2Controller`. Cuando WebView2 no está disponible, el sistema degrada al comportamiento actual (HYPERLINK).

Adicionalmente, el visor WebView2 sirve como plataforma para un **Modo Avanzado** basado en Pluto.jl, donde usuarios técnicos pueden abrir notebooks interactivos directamente dentro de Excel. Este modo integra: (1) PlutoManager para gestionar el servidor Pluto.jl como proceso separado, (2) RCall.jl cargado dentro del runtime Julia de ControlJulia.exe para pipelines mixtos Julia+R, (3) una biblioteca de 13 notebooks precargados, y (4) exportación de análisis como notebooks reproducibles. Python (ControlPython.exe) queda formalmente deprecado — Julia cubre toda la funcionalidad previamente planificada.

### Decisiones de Diseño

| Decisión | Elección | Justificación |
|------------------------|------------------------|------------------------|
| Modelo de threading | STA thread dedicado con message pump | WebView2 COM requiere STA; el hilo principal de Excel no debe bloquearse |
| Gestión de ventanas | Ventanas Win32 modeless owned por Excel HWND | Permite múltiples visores simultáneos sin bloquear Excel |
| Contenido grande (≥2 MB) | Archivo temporal + `Navigate(file://)` | `NavigateToString` tiene límite práctico de \~2 MB |
| SDK WebView2 | NuGet `Microsoft.Web.WebView2` vía CMake FetchContent | Consistente con el patrón existente de FetchContent para protobuf y googletest |
| Comunicación JS↔C++ | PostMessage bridge con JSON | API estándar de WebView2, sin dependencias adicionales |
| Presentaciones | reveal.js embebido inline | Archivo HTML autocontenido, portable, sin dependencias externas |
| Seguridad | Navegación restringida + DevTools deshabilitado por defecto | Sandbox mínimo viable; configurable para debugging |
| Pluto.jl como proceso separado | Proceso Julia independiente (no dentro de ControlJulia.exe) | Aislamiento de fallos; Pluto requiere su propio event loop y servidor HTTP |
| RCall.jl dentro de ControlJulia.exe | Cargado en el runtime Julia existente vía `startup.jl` | Evita un proceso R adicional; RCall.jl embebe R dentro de Julia nativamente |
| Notebooks precargados | 13 archivos `.jl` en `%RJ2XCL_HOME%/notebooks/` | Plantillas listas para usar; modificaciones se guardan en `notebooks/custom/` |
| Deprecación de Python | Excluido del build por defecto vía flag CMake | Reduce superficie de mantenimiento; Julia cubre ML, datos, AI |

### Restricciones

| Restricción | Detalle |
|------------------------------------|------------------------------------|
| Compilador | MSVC 2022, C++17, Windows x64 |
| Build system | CMake 3.15+ con FetchContent |
| Runtime | WebView2 Evergreen (preinstalado en Windows 10/11 con Edge) |
| Compatibilidad Excel | Excel 2019, 2021, Microsoft 365 |
| Callback thread | Actualmente deshabilitado — toda comunicación Excel es síncrona desde el hilo UI |
| Protobuf | v3.21.12 (proto3 syntax), ya integrado |
| Pluto.jl | Proceso Julia separado; NO se ejecuta dentro de ControlJulia.exe |
| RCall.jl | Se carga DENTRO del runtime Julia de ControlJulia.exe; requiere R instalado |
| ControlPython.exe | Código preservado en repositorio; excluido del build por defecto |

## Architecture

### Diagrama de Componentes

``` mermaid
graph TB
    subgraph "Excel Process"
        subgraph "XLL (RJ2XCL_Core.dll)"
            CF["Cell Functions<br/>=RJ2XCL.VIEW()<br/>=RJ2XCL.VIEWER.CLOSE()<br/>=RJ2XCL.VIEWER.LIST()"]
            PF["Presentation Functions<br/>=RJ2XCL.PRESENTATION.NEW()<br/>=RJ2XCL.PRESENTATION.ADD.SLIDE()<br/>=RJ2XCL.PRESENTATION.BUILD()"]
            PLF["Pluto Functions<br/>=RJ2XCL.PLUTO.START/STOP/STATUS()<br/>=RJ2XCL.NOTEBOOK.OPEN/LIST()<br/>=RJ2XCL.NOTEBOOK.EXPORT()"]
            JPF["Pipeline Functions<br/>=J.pipeline_*(data, params)<br/>=J.rcall_status()"]
            CP["ContentPipeline<br/>(GraphicsHandler ext.)"]
            VM["ViewerManager<br/>(singleton)"]
            PM["PlutoManager<br/>(singleton)"]
            NL["NotebookLibrary"]
            NE["NotebookExporter"]
            PMB["PostMessageBridge"]
            PB_BUILD["PresentationBuilder"]
            CS["ConfigService"]
            LS["LogService"]
        end

        subgraph "STA Thread"
            WV_ENV["WebView2Environment"]
            VW1["ViewerWindow 1<br/>+ WebView2Controller"]
            VW2["ViewerWindow 2<br/>+ WebView2Controller"]
            VWN["ViewerWindow N<br/>+ WebView2Controller"]
            MP["Message Pump"]
        end

        EXCEL["Excel Main Window<br/>(HWND owner)"]
    end

    subgraph "Child Processes"
        CR["ControlR.exe"]
        CJ["ControlJulia.exe<br/>+ RCall.jl Bridge"]
        PLUTO["Pluto.jl Server<br/>(separate Julia process)<br/>localhost:1234"]
    end

    subgraph "Deprecated (behind RJ2XCL_ENABLE_PYTHON)"
        CPY["ControlPython.exe"]
    end

    CR -->|"Named Pipe<br/>Protobuf + html_content"| CP
    CJ -->|"Named Pipe<br/>Protobuf + html_content"| CP
    CPY -.->|"Named Pipe<br/>(if enabled)"| CP

    CP --> VM
    CF --> VM
    PF --> PB_BUILD
    PB_BUILD --> VM
    PLF --> PM
    PLF --> NL
    PLF --> NE
    JPF -->|"Named Pipe"| CJ

    PM -->|"Start/Stop<br/>Process"| PLUTO
    PM -->|"Navigate to<br/>localhost:port"| VM
    NL -->|"Open notebook"| PM
    NE -->|"Generate .jl"| NL

    VM -->|"PostMessage"| PMB
    PMB -->|"WebMessageReceived"| VM

    VM -->|"Create/Destroy"| VW1
    VM -->|"Create/Destroy"| VW2
    VM -->|"Create/Destroy"| VWN

    VW1 --- WV_ENV
    VW2 --- WV_ENV
    VWN --- WV_ENV

    EXCEL -.->|"Owner HWND"| VW1
    EXCEL -.->|"Owner HWND"| VW2

    VM -->|"Config"| CS
    PM -->|"Config"| CS
    VM -->|"Log"| LS
    PM -->|"Log"| LS
```

### Flujo de Datos: Content Pipeline

``` mermaid
sequenceDiagram
    participant Lang as ControlX Process
    participant Pipe as Named Pipe
    participant GH as GraphicsHandler
    participant CP as ContentPipeline
    participant VM as ViewerManager
    participant STA as STA Thread
    participant VW as ViewerWindow

    Lang->>Pipe: CallResponse { result.html_content = "<html>..." }
    Pipe->>GH: Protobuf message received
    GH->>CP: Delegate html_content
    
    alt ViewerManager available
        CP->>VM: RouteHtmlContent(html, language, title)
        VM->>VM: Check size < 2MB?
        
        alt Size < 2MB
            VM->>STA: PostMessage(WM_APP_NAVIGATE_STRING, html)
            STA->>VW: CreateViewerWindow() if needed
            STA->>VW: NavigateToString(html)
        else Size ≥ 2MB
            VM->>VM: Write temp file
            VM->>STA: PostMessage(WM_APP_NAVIGATE_FILE, path)
            STA->>VW: Navigate(file:// URI)
            VW-->>VM: NavigationCompleted
            VM->>VM: Delete temp file
        end
        
        VM-->>CP: viewer_id
        CP-->>GH: "📊 [Title] (viewer-N)"
    else ViewerManager not available
        CP->>CP: Fallback: save HTML + HYPERLINK
    end
```

### Modelo de Threading

``` mermaid
graph LR
    subgraph "Excel UI Thread (MTA)"
        A["xlAutoOpen / Init()"]
        B["Cell function calls"]
        C["Callback dispatch"]
    end

    subgraph "STA Thread (CoInitializeEx COINIT_APARTMENTTHREADED)"
        D["Message Pump<br/>GetMessage/DispatchMessage"]
        E["WebView2 Environment creation"]
        F["WebView2 Controller creation"]
        G["Navigation events"]
        H["PostMessage events"]
        I["Window management"]
    end

    B -->|"PostThreadMessage<br/>WM_APP_CREATE_VIEWER"| D
    B -->|"PostThreadMessage<br/>WM_APP_NAVIGATE"| D
    C -->|"PostThreadMessage<br/>WM_APP_SEND_MESSAGE"| D

    D --> E
    D --> F
    D --> G
    D --> H
    D --> I

    G -->|"SetEvent<br/>navigation_complete_"| B
    H -->|"PostMessage to Excel<br/>via marshalled dispatch"| C
```

El hilo STA es necesario porque las interfaces COM de WebView2 (`ICoreWebView2`, `ICoreWebView2Controller`, `ICoreWebView2Environment`) requieren un Single-Threaded Apartment. El hilo principal de Excel opera en MTA. La comunicación entre hilos se realiza mediante `PostThreadMessage` (UI→STA) y eventos Win32 + marshalled COM pointers (STA→UI).

### Flujo de Datos: Pluto.jl Advanced Mode

``` mermaid
sequenceDiagram
    participant User as Excel User
    participant XLL as XLL (Cell Function)
    participant PM as PlutoManager
    participant VM as ViewerManager
    participant PLUTO as Pluto.jl Process
    participant VW as ViewerWindow

    User->>XLL: =RJ2XCL.PLUTO.START()
    XLL->>PM: StartPluto()
    PM->>PM: Check port availability (HTTP probe)
    
    alt Port already in use
        PM->>PM: Log INFO "Pluto already running"
        PM-->>XLL: Reuse existing server
    else Port available
        PM->>PLUTO: Launch julia -e "using Pluto; Pluto.run(port=1234)"
        PM->>PM: Wait for HTTP readiness (max 30s)
        
        alt Startup success
            PLUTO-->>PM: HTTP 200 on localhost:1234
        else Timeout
            PM-->>XLL: "Pluto server failed to start"
            Note over XLL: Return error to cell
        end
    end

    PM->>VM: CreateViewer(url="http://localhost:1234")
    VM->>VM: Extend Security_Policy for localhost:1234
    VM->>VW: Navigate("http://localhost:1234")
    VW-->>User: Pluto notebook interface

    Note over User,VW: User edits notebook cells...
    
    User->>XLL: =RJ2XCL.PLUTO.STOP()
    XLL->>PM: StopPluto()
    PM->>VM: CloseViewer(pluto_viewer_id)
    PM->>PLUTO: Terminate process
    PM-->>XLL: "Pluto stopped"
```

### Flujo de Datos: RCall.jl Pipeline

``` mermaid
sequenceDiagram
    participant User as Excel User
    participant XLL as XLL
    participant CJ as ControlJulia.exe
    participant JRT as Julia Runtime
    participant RB as RCall.jl Bridge
    participant RRT as R Runtime (embedded)

    Note over CJ,RRT: During startup.jl loading
    CJ->>JRT: Load startup.jl
    JRT->>JRT: Check DiscoveryService for R
    
    alt R available
        JRT->>RB: using RCall; RCall.Rinit()
        RB->>RRT: Initialize embedded R
        RRT-->>RB: R ready
        JRT->>JRT: rcall_available = true
    else R not available
        JRT->>JRT: Log WARNING "R not found"
        JRT->>JRT: rcall_available = false
    end

    Note over User,RRT: During pipeline execution
    User->>XLL: =J.pipeline_regression(data, params)
    XLL->>CJ: Named Pipe: CallRequest
    CJ->>JRT: Execute pipeline_regression()
    JRT->>JRT: Julia preprocessing (DataFrames.jl)
    JRT->>RB: @rput data; R"lm(y ~ x, data=data)"
    RB->>RRT: Execute R code
    RRT-->>RB: R result
    RB-->>JRT: Julia DataFrame
    JRT->>JRT: Julia postprocessing
    JRT-->>CJ: CallResponse with result
    CJ-->>XLL: Named Pipe: result
    XLL-->>User: Result in cell
```

## Components and Interfaces

### ViewerManager (Singleton)

Gestiona el ciclo de vida completo del subsistema WebView2: detección del runtime, creación del environment, y registro de ventanas activas.

``` cpp
namespace rj2xcl {

class ViewerManager {
public:
    static ViewerManager& Instance();

    // Lifecycle
    void Initialize();   // Called from RJ2XCL_Engine::Init()
    void Shutdown();      // Called from xlAutoClose

    // Runtime detection
    bool IsAvailable() const;

    // Viewer operations
    std::string CreateViewer(const std::string& html_content,
                             const std::string& language,
                             const std::string& title);
    std::string CreateViewerFromFile(const std::string& file_path,
                                     const std::string& language,
                                     const std::string& title);
    bool CloseViewer(const std::string& viewer_id);
    void CloseAllViewers();
    std::vector<std::string> ListViewers() const;

    // Communication
    bool SendToViewer(const std::string& viewer_id,
                      const std::string& json_message);

    // Viewer content capture (for PresentationBuilder)
    std::string CaptureViewerContent(const std::string& viewer_id);

private:
    ViewerManager();
    ~ViewerManager();

    void STAThreadProc();
    void InitializeEnvironment();
    void ProcessMemoryPressure();

    bool available_;
    DWORD sta_thread_id_;
    HANDLE sta_thread_handle_;
    HANDLE environment_ready_event_;

    ICoreWebView2Environment* environment_;

    struct ViewerEntry {
        std::string id;
        std::string language;
        std::string title;
        ViewerWindow* window;
        FILETIME created_at;
    };

    std::vector<ViewerEntry> viewers_;
    std::mutex viewers_mutex_;
    uint32_t next_viewer_id_;
    uint32_t max_viewers_;       // from config
    uint32_t max_memory_mb_;     // from config
};

} // namespace rj2xcl
```

### ViewerWindow

Encapsula una ventana Win32 modeless y su `ICoreWebView2Controller` asociado.

``` cpp
namespace rj2xcl {

class ViewerWindow {
public:
    ViewerWindow(HWND parent_hwnd,
                 ICoreWebView2Environment* environment,
                 const std::string& title);
    ~ViewerWindow();

    // Navigation
    HRESULT NavigateToString(const std::string& html);
    HRESULT NavigateToFile(const std::string& file_path);

    // Communication
    HRESULT PostWebMessage(const std::string& json);

    // Window management
    void Show();
    void Hide();
    void Resize(int width, int height);
    void SetTitle(const std::string& title);
    HWND GetHwnd() const;

    // Content capture
    std::string GetCurrentContent() const;

    // Security
    void ApplySecurityPolicy(bool dev_tools_enabled);

private:
    static LRESULT CALLBACK WindowProc(HWND hwnd, UINT msg,
                                        WPARAM wParam, LPARAM lParam);
    void OnSize();
    void OnParentMinimize();
    void OnParentRestore();
    void SetupNavigationFilter(const std::string& user_data_folder);
    void InjectBridgeScript();

    HWND hwnd_;
    HWND parent_hwnd_;
    ICoreWebView2Controller* controller_;
    ICoreWebView2* webview_;
    std::string current_html_;
    std::string viewer_id_;
};

} // namespace rj2xcl
```

### ContentPipeline

Extensión del `GraphicsHandler` existente para interceptar contenido HTML y enrutarlo al `ViewerManager`.

``` cpp
namespace rj2xcl {

class ContentPipeline {
public:
    // Route HTML content to viewer or fallback
    static std::string RouteHtmlContent(
        const std::string& html_content,
        const std::string& language,
        const std::string& title,
        LPDISPATCH application_dispatch);

    // Detect HTML content from file output (R htmlwidgets, Python plotly)
    static bool IsHtmlFile(const std::string& file_path);
    static std::string ReadHtmlFile(const std::string& file_path);

private:
    static std::string FallbackHyperlink(
        const std::string& html_content,
        const std::string& file_path,
        LPDISPATCH application_dispatch);
};

} // namespace rj2xcl
```

### PostMessageBridge

Maneja la comunicación bidireccional entre JavaScript (en WebView2) y C++ (en el XLL).

``` cpp
namespace rj2xcl {

class PostMessageBridge {
public:
    // Process incoming message from JavaScript
    static void OnWebMessageReceived(
        const std::string& viewer_id,
        const std::string& json_message,
        LPDISPATCH application_dispatch);

private:
    // Action handlers
    static void HandleWriteCell(
        const json11::Json& payload,
        LPDISPATCH application_dispatch);
    static void HandleNotify(
        const json11::Json& payload,
        LPDISPATCH application_dispatch);
};

} // namespace rj2xcl
```

**JavaScript Bridge (inyectado en cada página):**

``` javascript
// Injected via AddScriptToExecuteOnDocumentCreated
window.rj2xcl = {
    sendToExcel: function(data) {
        window.chrome.webview.postMessage(JSON.stringify(data));
    }
};
```

### PresentationBuilder

Compone presentaciones reveal.js a partir de contenido de viewers activos y texto Markdown.

``` cpp
namespace rj2xcl {

class PresentationBuilder {
public:
    PresentationBuilder(const std::string& title);

    // Slide management
    void AddTextSlide(const std::string& markdown_content);
    void AddViewerSlide(const std::string& viewer_id);
    void AddHtmlSlide(const std::string& html_content);

    // Build
    std::string Build(const std::string& output_path);

    // Accessors
    std::string GetId() const;
    int GetSlideCount() const;

private:
    struct Slide {
        enum Type { TEXT, VIEWER, HTML };
        Type type;
        std::string content;
    };

    std::string id_;
    std::string title_;
    std::vector<Slide> slides_;

    std::string GenerateRevealHtml() const;
    std::string EmbedAssets(const std::string& html) const;
    std::string Base64Encode(const std::vector<uint8_t>& data) const;

    // reveal.js CSS+JS embedded as string constants
    static const char* REVEAL_JS_BUNDLE;
    static const char* REVEAL_CSS_BUNDLE;
};

} // namespace rj2xcl
```

### PlutoManager (Singleton)

Gestiona el ciclo de vida del servidor Pluto.jl como proceso Julia separado. Pluto.jl NO se ejecuta dentro de ControlJulia.exe — es un proceso independiente que sirve notebooks en `localhost:[port]`. El PlutoManager se encarga de lanzar, monitorear y terminar este proceso.

**Decisión de diseño**: Pluto.jl requiere su propio event loop HTTP y servidor web. Ejecutarlo dentro de ControlJulia.exe bloquearía el Named Pipe de comunicación con Excel. Un proceso separado permite que Pluto sirva notebooks mientras ControlJulia.exe sigue procesando funciones de celda normalmente.

``` cpp
namespace rj2xcl {

class PlutoManager {
public:
    static PlutoManager& Instance();

    // Lifecycle
    void Initialize();   // Read config, resolve Julia path
    void Shutdown();      // Terminate Pluto if running

    // Server control
    std::string StartPluto();    // Returns "Pluto started on port [port]" or error
    std::string StopPluto();     // Returns "Pluto stopped"
    std::string GetStatus() const; // "running", "stopped", "starting"

    // Notebook operations (delegates to ViewerManager for display)
    std::string OpenNotebook(const std::string& notebook_path);

    // Port configuration
    uint16_t GetConfiguredPort() const;

    // Query
    bool IsRunning() const;
    bool WasStartedByThisSession() const;

private:
    PlutoManager();
    ~PlutoManager();

    bool ProbePort(uint16_t port) const;  // HTTP probe to check if port is in use
    bool WaitForReady(uint32_t timeout_ms = 30000);
    std::string BuildPlutoCommand() const;

    enum class State { STOPPED, STARTING, RUNNING };
    State state_;

    HANDLE pluto_process_handle_;
    DWORD pluto_process_id_;
    uint16_t port_;
    std::string julia_path_;       // Resolved via DiscoveryService
    std::string pluto_viewer_id_;  // ViewerWindow showing Pluto UI
    bool started_by_this_session_;

    mutable std::mutex state_mutex_;
};

} // namespace rj2xcl
```

**Comando de lanzamiento**: El PlutoManager ejecuta Pluto.jl como:
```
julia --project=@pluto -e "import Pluto; Pluto.run(host=\"127.0.0.1\", port=1234, launch_browser=false, auto_reload_from_file=true)"
```

El flag `launch_browser=false` evita que Pluto abra un navegador externo (el WebView2 es el visor). El flag `auto_reload_from_file=true` permite que notebooks modificados externamente se recarguen automáticamente.

### RCallBridge (Módulo Julia en startup.jl)

La integración de RCall.jl se realiza como extensión del módulo `RJ2XCL` existente en `startup.jl`. RCall.jl se carga DENTRO del runtime Julia de ControlJulia.exe, no como proceso separado. Esto permite que funciones Julia invoquen R directamente vía `@rput`/`@rget`/`R""` sin IPC adicional.

**Decisión de diseño**: RCall.jl embebe el runtime R dentro del proceso Julia usando la API C de R. Esto es más eficiente que comunicarse con ControlR.exe vía Named Pipes para cada operación R, y permite transferencia de datos in-memory entre Julia y R.

**Extensión de `startup.jl`:**

``` julia
# === RCall.jl Bridge ===
# Loaded conditionally when R is detected by DiscoveryService

const _rcall_available = Ref{Bool}(false)
const _rcall_status_reason = Ref{String}("")

function _init_rcall()
    r_home = get(ENV, "R_HOME", "")
    if isempty(r_home)
        _rcall_status_reason[] = "R_HOME not set — R not detected by DiscoveryService"
        @warn "R not found — RCall.jl disabled; R-dependent notebooks will not function"
        return
    end

    try
        @eval using RCall
        RCall.Rinit()
        _rcall_available[] = true
        println("RCall.jl initialized — R bridge available")
    catch e
        _rcall_status_reason[] = "RCall.jl loading failed: $(sprint(showerror, e))"
        @warn "RCall.jl initialization failed" exception=(e, catch_backtrace())
    end
end

"""
    rcall_status()

Returns "available" when RCall.jl is loaded and R is connected,
or "unavailable: [reason]" when RCall.jl is not loaded.
"""
function rcall_status()
    if _rcall_available[]
        return "available"
    else
        return "unavailable: $(_rcall_status_reason[])"
    end
end

"""
    pipeline_regression(data, params)

Example mixed Julia+R pipeline: Julia preprocessing → R lm() → Julia postprocessing.
"""
function pipeline_regression(data, params)
    if !_rcall_available[]
        error("RCall.jl not available — cannot execute R pipeline. Reason: $(_rcall_status_reason[])")
    end

    try
        # Julia preprocessing
        df = _to_dataframe(data)

        # Transfer to R and execute
        @rput df
        formula_str = get(params, "formula", "y ~ .")
        R"""
        model <- lm($(formula_str), data=df)
        result <- summary(model)
        coefficients <- coef(result)
        """
        @rget coefficients

        return coefficients
    catch e
        if e isa RCall.REvalError
            # Format combined R error + Julia stack trace
            r_msg = sprint(showerror, e)
            julia_trace = sprint(Base.show_backtrace, catch_backtrace())
            error("R error in pipeline: $r_msg\nJulia trace: $julia_trace")
        end
        rethrow()
    end
end
```

**Integración con ControlJulia.exe**: El proceso ControlJulia.exe ya carga `startup.jl` durante su inicialización. La extensión RCall.jl se activa condicionalmente: ControlJulia.exe establece `ENV["R_HOME"]` basándose en el resultado de `DiscoveryService::FindR()` antes de inicializar Julia. Si R no está disponible, `R_HOME` no se establece y RCall.jl no se carga.

### NotebookLibrary

Gestiona la colección de notebooks Pluto precargados y personalizados. Los 13 notebooks precargados se instalan en `%RJ2XCL_HOME%/notebooks/` y las modificaciones del usuario se guardan en `%RJ2XCL_HOME%/notebooks/custom/`.

``` cpp
namespace rj2xcl {

class NotebookLibrary {
public:
    struct NotebookInfo {
        std::string name;           // e.g., "stats_regression"
        std::string filename;       // e.g., "stats_regression.jl"
        std::string full_path;      // Absolute path
        std::string category;       // "R via RCall", "Julia native", "Mixed R+Julia"
        bool is_custom;             // true if from notebooks/custom/
        bool requires_rcall;        // true if notebook uses RCall.jl
    };

    // Discovery
    std::vector<NotebookInfo> ListNotebooks() const;
    std::string ListNotebooksFormatted() const;  // Comma-separated for =NOTEBOOK.LIST()

    // Lookup
    NotebookInfo FindNotebook(const std::string& notebook_name) const;
    bool NotebookExists(const std::string& notebook_name) const;

    // Paths
    std::string GetNotebooksDirectory() const;
    std::string GetCustomDirectory() const;
    std::string GetExportsDirectory() const;

    // Category classification
    static bool RequiresRCall(const std::string& filename);

private:
    std::string notebooks_dir_;  // %RJ2XCL_HOME%/notebooks/
    std::string custom_dir_;     // %RJ2XCL_HOME%/notebooks/custom/
    std::string exports_dir_;    // %RJ2XCL_HOME%/notebooks/exports/

    // Preconfigured notebook registry
    static const std::vector<std::pair<std::string, std::string>> PRECONFIGURED_NOTEBOOKS;
};

// Static registry of the 13 preconfigured notebooks
const std::vector<std::pair<std::string, std::string>>
NotebookLibrary::PRECONFIGURED_NOTEBOOKS = {
    // R via RCall.jl (7)
    {"stats_regression.jl",        "R via RCall"},
    {"lme4_mixed_models.jl",       "R via RCall"},
    {"survival_analysis.jl",       "R via RCall"},
    {"forecast_arima.jl",          "R via RCall"},
    {"psych_factor_analysis.jl",   "R via RCall"},
    {"plm_panel_econometrics.jl",  "R via RCall"},
    {"rstanarm_bayes.jl",          "R via RCall"},
    // Julia native (5)
    {"jump_optimization.jl",       "Julia native"},
    {"diffeq_simulation.jl",       "Julia native"},
    {"turing_hierarchical.jl",     "Julia native"},
    {"montecarlo_risk.jl",         "Julia native"},
    {"linalg_decomposition.jl",    "Julia native"},
    // Mixed R+Julia (1)
    {"multilang_pipeline.jl",      "Mixed R+Julia"},
};

} // namespace rj2xcl
```

### NotebookExporter

Captura el contexto de un análisis ejecutado desde Excel y genera un archivo `.jl` de notebook Pluto reproducible.

``` cpp
namespace rj2xcl {

class NotebookExporter {
public:
    // Analysis context captured during execution
    struct AnalysisContext {
        std::string function_name;     // e.g., "pipeline_regression"
        std::string language;          // "Julia" or "R"
        std::string code;              // Source code executed
        std::string input_data_json;   // Input data as JSON
        std::string parameters_json;   // Parameters as JSON
        std::string result_json;       // Result as JSON
        FILETIME executed_at;
    };

    // Capture the last analysis
    static void CaptureAnalysis(const AnalysisContext& context);
    static bool HasAnalysis();

    // Export
    static std::string ExportNotebook(const std::string& title);

    // Filename generation
    static std::string SanitizeTitle(const std::string& title);
    static std::string GenerateFilename(const std::string& title);

private:
    static AnalysisContext last_analysis_;
    static std::mutex analysis_mutex_;

    static std::string GeneratePlutoNotebook(
        const std::string& title,
        const AnalysisContext& context);

    // Pluto notebook format helpers
    static std::string PlutoCellMarker();  // "# ╔═╡ UUID"
    static std::string PlutoHeader();
    static std::string PlutoDataCell(const std::string& data_json);
    static std::string PlutoCodeCell(const std::string& code);
    static std::string PlutoResultCell(const std::string& result_json);
};

} // namespace rj2xcl
```

**Formato de notebook Pluto generado:**

```julia
### A Pluto.jl notebook ###
# v0.19.x

# ╔═╡ <uuid1>
md"""
# [Title]
Exported from RJ2XCL on [date]
"""

# ╔═╡ <uuid2>
# Input data
data = [... JSON parsed to Julia literal ...]

# ╔═╡ <uuid3>
# Parameters
params = Dict(...)

# ╔═╡ <uuid4>
# Analysis code
[original Julia/R code]

# ╔═╡ <uuid5>
# Expected results (for verification)
expected = [... result ...]
```

## Data Models

### Extensión Protobuf: Campo `html_content`

Se extiende el mensaje `Variable` en `variable.proto` para transportar contenido HTML:

``` protobuf
// Adición al oneof value en message Variable
message HtmlContent {
    string html = 1;           // HTML completo (inline CSS/JS)
    string title = 2;          // Título derivado del contenido
    string source_language = 3; // "R", "Julia", "Python"
    string mime_type = 4;      // "text/html" (extensible)
}

message Variable {
    oneof value {
        // ... campos existentes (1-14) ...
        HtmlContent html_content = 16;  // Nuevo: contenido HTML para viewer
    }
    string name = 15;
}
```

El field number 16 se elige porque 15 ya está ocupado por `name` y los números 1-15 son más eficientes en protobuf wire format. El campo 16 usa 2 bytes para el tag, lo cual es aceptable dado que los mensajes HTML son inherentemente grandes.

### Esquema de Configuración WebView2

Extensión de `rj2xcl-config.json`:

``` json
{
    "RJ2XCL": {
        "...existing config..."
    },
    "WebView2": {
        "enabled": true,
        "maxViewers": 8,
        "maxMemoryMB": 512,
        "userDataFolder": "%RJ2XCL_HOME%/webview2-data",
        "defaultWidth": 800,
        "defaultHeight": 600,
        "security": {
            "devToolsEnabled": false
        }
    },
    "Pluto": {
        "port": 1234
    }
}
```

**Validación de configuración en ConfigService:**

| Clave | Tipo | Rango válido | Default | Comportamiento fuera de rango |
|---------------|---------------|---------------|---------------|---------------|
| `WebView2.enabled` | bool | true/false | true | N/A |
| `WebView2.maxViewers` | int | 1–16 | 8 | Clamp al límite más cercano + WARNING |
| `WebView2.maxMemoryMB` | int | 128–2048 | 512 | Clamp al límite más cercano + WARNING |
| `WebView2.userDataFolder` | string | Path válido | `%RJ2XCL_HOME%/webview2-data` | Validación de path traversal |
| `WebView2.defaultWidth` | int | 400–3840 | 800 | Clamp + WARNING |
| `WebView2.defaultHeight` | int | 300–2160 | 600 | Clamp + WARNING |
| `WebView2.security.devToolsEnabled` | bool | true/false | false | N/A |
| `Pluto.port` | int | 1024–65535 | 1234 | Clamp al límite más cercano + WARNING |

### Registro Interno de Viewers

``` cpp
struct ViewerEntry {
    std::string id;              // "viewer-1", "viewer-2", ...
    std::string language;        // "R", "Julia", "Python"
    std::string title;           // Derived from HTML <title> or function name
    ViewerWindow* window;        // Owning pointer
    FILETIME created_at;         // For FIFO eviction
    size_t content_size_bytes;   // For memory tracking
};
```

### PostMessage JSON Protocol

**JavaScript → C++ (sendToExcel):**

``` json
{
    "action": "write-cell",
    "sheet": "Sheet1",
    "cell": "A1",
    "value": 42.5
}
```

``` json
{
    "action": "notify",
    "message": "Selection: 3 data points"
}
```

**C++ → JavaScript (SendToViewer):**

``` json
{
    "action": "update-data",
    "data": { "x": [1,2,3], "y": [4,5,6] }
}
```

### Integración CMake: WebView2 SDK

Se agrega WebView2 al `CMakeLists.txt` raíz usando FetchContent para descargar el paquete NuGet:

``` cmake
# En CMakeLists.txt raíz, después de FetchContent para protobuf/googletest:

# WebView2 SDK (NuGet package)
FetchContent_Declare(
    webview2
    URL "https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/1.0.2903.40"
    URL_HASH SHA256=<hash>
)
FetchContent_MakeAvailable(webview2)

# WebView2 headers and loader
set(WEBVIEW2_INCLUDE_DIR "${webview2_SOURCE_DIR}/build/native/include")
set(WEBVIEW2_LOADER_DIR "${webview2_SOURCE_DIR}/build/native/x64")
```

En `RJ2XCL/CMakeLists.txt` del XLL:

``` cmake
# Link WebView2
target_include_directories(RJ2XCL_Core_Objects PUBLIC ${WEBVIEW2_INCLUDE_DIR})
target_link_libraries(RJ2XCL_Core PRIVATE
    Common PB libprotobuf
    "${WEBVIEW2_LOADER_DIR}/WebView2LoaderStatic.lib"
)
```

Se usa `WebView2LoaderStatic.lib` (enlace estático) para evitar distribuir `WebView2Loader.dll` por separado, consistente con la política de static runtime (`/MT`) del proyecto.

### Estructura de Directorios: Notebooks

```
%RJ2XCL_HOME%/
├── notebooks/
│   ├── stats_regression.jl          # R via RCall
│   ├── lme4_mixed_models.jl         # R via RCall
│   ├── survival_analysis.jl         # R via RCall
│   ├── forecast_arima.jl            # R via RCall
│   ├── psych_factor_analysis.jl     # R via RCall
│   ├── plm_panel_econometrics.jl    # R via RCall
│   ├── rstanarm_bayes.jl            # R via RCall
│   ├── jump_optimization.jl         # Julia native
│   ├── diffeq_simulation.jl         # Julia native
│   ├── turing_hierarchical.jl       # Julia native
│   ├── montecarlo_risk.jl           # Julia native
│   ├── linalg_decomposition.jl      # Julia native
│   ├── multilang_pipeline.jl        # Mixed R+Julia
│   ├── custom/                      # User-modified notebooks
│   │   └── (copies of modified preconfigured notebooks)
│   └── exports/                     # Exported analysis notebooks
│       └── (generated .jl files)
├── webview2-data/                   # WebView2 user data folder
└── rj2xcl-config.json
```

### Extensión de Security_Policy para Advanced Mode

Cuando el Advanced_Mode está activo, el filtro de navegación se extiende para permitir `http://localhost:[port]`:

``` cpp
// Extended navigation filter in ViewerWindow
void ViewerWindow::SetupNavigationFilter(
    const std::string& user_data_folder,
    bool advanced_mode_active,
    uint16_t pluto_port)
{
    webview_->add_NavigationStarting(
        Callback<ICoreWebView2NavigationStartingEventArgs>(
            [=](ICoreWebView2* sender,
                ICoreWebView2NavigationStartingEventArgs* args) -> HRESULT
            {
                wil::unique_cotaskmem_string uri;
                args->get_Uri(&uri);
                std::wstring uri_str(uri.get());

                // Always allow about:blank
                if (uri_str == L"about:blank") return S_OK;

                // Allow file:// within user_data_folder
                if (IsFileUriInFolder(uri_str, user_data_folder)) return S_OK;

                // Allow localhost:port when Advanced Mode is active
                if (advanced_mode_active &&
                    IsLocalhostUri(uri_str, pluto_port)) return S_OK;

                // Block everything else
                args->put_Cancel(TRUE);
                LogService::Instance().Log(LogLevel::WARNING,
                    "Navigation blocked: " + WideToUtf8(uri_str));
                return S_OK;
            }).Get(), nullptr);
}
```

### Cambios CMake: Deprecación de Python

En el `CMakeLists.txt` raíz, ControlPython se mueve detrás de un flag:

``` cmake
# En CMakeLists.txt raíz — reemplaza la sección existente de language targets
option(SKIP_LANGUAGE_TARGETS "Skip ControlR/ControlJulia (for CI without R/Julia)" OFF)
option(RJ2XCL_ENABLE_PYTHON "Build ControlPython.exe (deprecated)" OFF)

if(NOT SKIP_LANGUAGE_TARGETS)
    add_subdirectory(ControlR)
    add_subdirectory(ControlJulia)
    if(RJ2XCL_ENABLE_PYTHON)
        add_subdirectory(ControlPython)
    endif()
endif()
```

En el código C++ del ContentPipeline, la lógica Python-específica se guarda detrás de `#ifdef`:

``` cpp
std::string ContentPipeline::RouteHtmlContent(...) {
    // ... existing routing logic ...

#ifdef RJ2XCL_ENABLE_PYTHON
    // Python-specific: detect rj2xcl_plotly_export output
    if (language == "Python" && IsHtmlFile(file_path)) {
        return ReadHtmlFile(file_path);
    }
#endif

    // ... rest of routing ...
}
```

### Esquema de `rj2xcl-languages.json` (actualizado)

``` json
{
    "languages": [
        {
            "name": "R",
            "executable": "ControlR.exe",
            "prefix": "R",
            "enabled": true
        },
        {
            "name": "Julia",
            "executable": "ControlJulia.exe",
            "prefix": "J",
            "enabled": true
        }
    ]
}
```

Python se omite del archivo por defecto. Si un administrador lo agrega manualmente:

``` json
{
    "name": "Python",
    "executable": "ControlPython.exe",
    "prefix": "PY",
    "enabled": true
}
```

El XLL lo cargará normalmente, manteniendo compatibilidad hacia atrás.

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas de un sistema — esencialmente, una declaración formal sobre lo que el sistema debe hacer. Las propiedades sirven como puente entre especificaciones legibles por humanos y garantías de corrección verificables por máquina.*

### Property 1: HtmlContent Protobuf Round-Trip

*For any* valid `HtmlContent` message (with arbitrary HTML string, title, source language, and MIME type), serializing the message to the Protobuf wire format and then deserializing it SHALL produce a message with identical field values.

**Validates: Requirements 3.1**

### Property 2: Size-Based Routing Threshold

*For any* HTML content string, the ContentPipeline routing decision SHALL be: if `content.size() < 2 * 1024 * 1024` then route via `NavigateToString`, otherwise route via temporary file + `Navigate(file://)`. The threshold is exactly 2,097,152 bytes.

**Validates: Requirements 3.3, 3.4**

### Property 3: Content Type Detection

*For any* string passed to `RJ2XCL.VIEW()`, if the string ends with `.html` or `.htm` (case-insensitive) it SHALL be classified as a file path; if the string starts with `<!DOCTYPE` or `<html` (case-insensitive) it SHALL be classified as inline HTML; otherwise it SHALL be treated as a file path.

**Validates: Requirements 5.2, 5.3**

### Property 4: PostMessage JSON Parsing

*For any* valid JSON-serializable object sent via `window.rj2xcl.sendToExcel(data)`, the PostMessageBridge SHALL parse the JSON payload and extract the `action` field without data loss or corruption.

**Validates: Requirements 4.2**

### Property 5: Invalid Message Handling

*For any* string that is either invalid JSON or valid JSON with an `action` field not in the recognized set {"write-cell", "notify"}, the PostMessageBridge SHALL discard the message, log a WARNING, and leave Excel state unchanged.

**Validates: Requirements 4.5**

### Property 6: Navigation URI Filtering

*For any* URI string, the navigation filter SHALL allow navigation if and only if the URI is `about:blank` or a `file://` URI whose resolved path is within the configured User_Data_Folder. All other URIs SHALL be blocked.

**Validates: Requirements 6.2**

### Property 7: Viewer Registry Invariants

*For any* sequence of `CreateViewer` and `CloseViewer` operations, the ViewerManager registry SHALL maintain these invariants: (a) every viewer ID is unique and follows the format `"viewer-[N]"` where N is monotonically increasing, (b) `ListViewers()` returns exactly the set of currently active viewer IDs, (c) `ListViewers().size()` equals the count of active viewers, and (d) lookup by any active ID returns the correct ViewerEntry.

**Validates: Requirements 7.3, 7.5, 5.5**

### Property 8: FIFO Eviction Policy

*For any* sequence of `CreateViewer` calls where the active viewer count reaches the configured maximum, the ViewerManager SHALL close the viewer with the earliest `created_at` timestamp before creating the new one, and the active count SHALL never exceed the configured maximum.

**Validates: Requirements 7.2**

### Property 9: Configuration Integer Clamping

*For any* integer value V provided for `WebView2.maxViewers` (valid range 1–16) or `WebView2.maxMemoryMB` (valid range 128–2048), the ConfigService SHALL return: V if V is within the valid range, the lower bound if V < lower bound, or the upper bound if V > upper bound. Formally: `clamp(V, lo, hi) == max(lo, min(hi, V))`.

**Validates: Requirements 10.3, 10.4**

### Property 10: Window Title Format

*For any* language string L ∈ {"R", "Julia", "Python"} and any non-empty title string T, the ViewerWindow title bar text SHALL equal `L + " — " + T`.

**Validates: Requirements 2.5**

### Property 11: Cell Value Format

*For any* non-empty title string T and viewer ID string in format `"viewer-[N]"`, the cell return value from ContentPipeline SHALL equal `"📊 " + T + " (" + viewer_id + ")"`.

**Validates: Requirements 9.6**

### Property 12: Presentation Slide Ordering

*For any* sequence of `AddSlide` calls with types in {"text", "viewer", "html"} and arbitrary content, the built presentation HTML SHALL contain the slides in the exact order they were added, and each slide's content SHALL be preserved.

**Validates: Requirements 12.2**

### Property 13: Default Presentation Filename Format

*For any* presentation title string T, when `output_path` is empty, the generated filename SHALL match the regex pattern `presentation_[sanitized_T]_\d{8}_\d{6}\.html` where `sanitized_T` is T with non-alphanumeric characters replaced.

**Validates: Requirements 12.8**

### Property 14: Extended Navigation URI Filtering (Advanced Mode)

*For any* URI string, when Advanced_Mode is active with a configured Pluto port P, the navigation filter SHALL allow navigation if and only if the URI is: (a) `about:blank`, (b) a `file://` URI whose resolved path is within the configured User_Data_Folder, or (c) an `http://localhost:P` URI or any subpath thereof. All other URIs SHALL be blocked. When Advanced_Mode is NOT active, only conditions (a) and (b) apply.

**Validates: Requirements 13.4, 6.2**

### Property 15: Pluto Status State Machine Consistency

*For any* sequence of `StartPluto()` and `StopPluto()` operations, the `GetStatus()` return value SHALL always be one of exactly three strings: "running", "stopped", or "starting". After a successful `StartPluto()`, the status SHALL be "running". After a successful `StopPluto()`, the status SHALL be "stopped". The status SHALL never be any other value.

**Validates: Requirements 13.10**

### Property 16: Pluto Port Configuration Clamping

*For any* integer value V provided for `Pluto.port`, the ConfigService SHALL return: V if V is within the valid range 1024–65535, 1024 if V < 1024, or 65535 if V > 65535. Formally: `clamp(V, 1024, 65535) == max(1024, min(65535, V))`.

**Validates: Requirements 13.6**

### Property 17: RCall Error Message Formatting

*For any* R error message string E and Julia stack trace, when an R function invoked via RCall.jl raises an error, the formatted error string returned to the XLL SHALL contain both the original R error text E and a Julia stack trace marker. The R error text SHALL not be truncated or modified.

**Validates: Requirements 14.6**

### Property 18: Notebook Listing Completeness

*For any* set of `.jl` files in the `%RJ2XCL_HOME%/notebooks/` directory and any set of `.jl` files in the `%RJ2XCL_HOME%/notebooks/custom/` directory, the `ListNotebooksFormatted()` return value SHALL contain every filename from both directories. Custom notebook names SHALL be suffixed with " [custom]". No notebook SHALL be omitted or duplicated.

**Validates: Requirements 15.4, 15.6**

### Property 19: Notebook Export Validity

*For any* valid AnalysisContext (with non-empty function name, code, input data, parameters, and results), the generated Pluto notebook file SHALL: (a) contain Pluto cell markers (`# ╔═╡`), (b) include the input data, (c) include the parameters, (d) include the analysis code, and (e) include the results. The file SHALL be a valid plain-text `.jl` file.

**Validates: Requirements 16.2, 16.3, 16.4**

### Property 20: Export Filename Sanitization

*For any* title string T, the `GenerateFilename()` function SHALL produce a filename matching the regex pattern `[a-zA-Z0-9_]+_\d{8}_\d{6}\.jl` where all non-alphanumeric characters in T are replaced with underscores, and the timestamp portion represents a valid date-time.

**Validates: Requirements 16.7**

## Error Handling

### Estrategia General

Todos los errores se manejan con degradación graceful: el sistema nunca debe crashear Excel. Los errores se clasifican en tres niveles:

| Nivel | Acción | Ejemplo |
|---|---|---|
| **Recoverable** | Log WARNING + continuar | Navegación bloqueada, JSON inválido en PostMessage |
| **Degraded** | Log ERROR + deshabilitar feature | WebView2 runtime no encontrado, environment creation falla |
| **Fatal** | Log ERROR + cleanup + return error string | Fallo de creación de controller por recursos agotados |

### Errores Específicos por Componente

**ViewerManager:**

| Error | HRESULT / Condición | Manejo |
|---|---|---|
| Runtime no detectado | `GetAvailableCoreWebView2BrowserVersionString` falla | `available_ = false`, WARNING log, funciones retornan "WebView2 not available" |
| Environment creation falla | `CreateCoreWebView2EnvironmentWithOptions` retorna error | `available_ = false`, ERROR log con HRESULT |
| Controller creation falla | `CreateCoreWebView2Controller` retorna error | ERROR log, retorna "Viewer creation failed" |
| Navegación falla | `NavigateToString` / `Navigate` retorna error | WARNING log, no se muestra ventana |
| Memoria excedida | Total browser memory > `maxMemoryMB` | Evict oldest viewer, WARNING log |

**ContentPipeline:**

| Error | Condición | Manejo |
|---|---|---|
| HTML vacío/null | `html_content` field vacío | WARNING log, no crear viewer |
| Archivo HTML no encontrado | File path no existe | WARNING log, retornar error string a celda |
| Archivo HTML no legible | Permisos insuficientes | WARNING log, retornar error string a celda |

**PostMessageBridge:**

| Error | Condición | Manejo |
|---|---|---|
| JSON inválido | `json11::Json::parse` falla | WARNING log, descartar mensaje |
| Acción no reconocida | `action` no es "write-cell" ni "notify" | WARNING log, descartar mensaje |
| Celda inválida | Sheet/cell reference no existe | WARNING log, descartar mensaje |

**PresentationBuilder:**

| Error | Condición | Manejo |
|---|---|---|
| Viewer no encontrado | `viewer_id` no existe en registry | WARNING log, skip slide |
| Escritura falla | No se puede escribir `output_path` | ERROR log, retornar error string |
| Contenido vacío | Presentación sin slides | WARNING log, generar HTML con slide vacío |

**PlutoManager:**

| Error | Condición | Manejo |
|---|---|---|
| Julia no encontrada | `DiscoveryService::FindJulia()` retorna vacío | ERROR log, retornar "Pluto server failed to start — check Julia installation" |
| Puerto en uso (no Pluto) | `ProbePort()` detecta servicio no-Pluto | WARNING log, retornar "Port [port] in use by another service" |
| Timeout de inicio | Pluto no responde en 30 segundos | ERROR log, terminar proceso, retornar error string |
| Proceso terminó inesperadamente | `WaitForSingleObject` retorna antes de `StopPluto()` | WARNING log, actualizar estado a STOPPED |
| Pluto ya corriendo (otra sesión) | Puerto en uso por Pluto externo | INFO log, reusar servidor existente |

**RCallBridge (en startup.jl):**

| Error | Condición | Manejo |
|---|---|---|
| R no detectado | `R_HOME` no establecido | WARNING log, `_rcall_available = false`, notebooks R no funcionan |
| RCall.jl no instalado | `using RCall` falla | WARNING log con excepción, `_rcall_available = false` |
| R inicialización falla | `RCall.Rinit()` falla | WARNING log, `_rcall_available = false` |
| Error R en pipeline | `RCall.REvalError` durante ejecución | Catch, formatear error R + Julia trace, retornar error combinado |

**NotebookLibrary:**

| Error | Condición | Manejo |
|---|---|---|
| Notebook no encontrado | Nombre no coincide con ningún archivo | WARNING log, retornar "Notebook not found: [name]" |
| Directorio no existe | `%RJ2XCL_HOME%/notebooks/` no existe | WARNING log, retornar lista vacía |
| RCall no disponible | Notebook requiere RCall pero no está cargado | Abrir notebook con sufijo " (R unavailable)" en return value |

**NotebookExporter:**

| Error | Condición | Manejo |
|---|---|---|
| Sin análisis previo | `HasAnalysis()` retorna false | WARNING log, retornar "No analysis to export — execute an analysis first" |
| Escritura falla | No se puede escribir en `exports/` | ERROR log, retornar error string |
| Título vacío | Título es empty string | Usar "untitled" como título por defecto |

**Python Deprecation:**

| Error | Condición | Manejo |
|---|---|---|
| Función PY.* sin Python | Usuario llama `=PY.*` y Python no configurado | Retornar "Python is deprecated — use Julia (=J.*) functions instead. See documentation for migration guide." |

### Cleanup y Recursos

- **COM Release**: Cada `ViewerWindow` destructor llama `controller_->Release()` y verifica ref count = 0. Si no, WARNING log.
- **Archivos temporales**: Eliminados en el handler de `NavigationCompleted`. Si la eliminación falla, WARNING log (no es fatal).
- **STA Thread**: `Shutdown()` envía `WM_QUIT` al message pump y espera con `WaitForSingleObject(sta_thread_handle_, 5000)`. Si timeout, `TerminateThread` como último recurso + ERROR log.
- **Pluto Process**: `PlutoManager::Shutdown()` termina el proceso Pluto.jl si fue iniciado por esta sesión. Usa `TerminateProcess` si el proceso no responde a señal de cierre en 5 segundos.
- **xlAutoClose**: `ViewerManager::Shutdown()` cierra todos los viewers, destruye el environment, y termina el STA thread. `PlutoManager::Shutdown()` termina el servidor Pluto si está corriendo.

## Testing Strategy

### Enfoque Dual: Unit Tests + Property Tests

Este feature requiere ambos tipos de tests:

- **Unit tests**: Verifican ejemplos específicos, edge cases, y condiciones de error. Cubren integración con Win32 API y WebView2 COM (mockeados).
- **Property tests**: Verifican propiedades universales que deben cumplirse para todas las entradas válidas. Cubren lógica pura como parsing, formatting, routing, y gestión de registry.

### Property-Based Testing

**Librería**: [rapidcheck](https://github.com/emil-e/rapidcheck) — librería PBT para C++ compatible con GoogleTest (ya integrado en el proyecto).

**Configuración**:
- Mínimo 100 iteraciones por property test
- Cada test referencia su propiedad del documento de diseño
- Tag format: `Feature: webview2-viewer, Property N: [description]`

**Properties a implementar:**

| Property | Componente bajo test | Generadores necesarios |
|---|---|---|
| 1: HtmlContent Round-Trip | `variable.pb` serialization | Random strings (HTML, title, language) |
| 2: Size-Based Routing | `ContentPipeline::RouteHtmlContent` | Random strings de tamaño variable (0 bytes – 4 MB) |
| 3: Content Type Detection | `ContentPipeline` input classifier | Random strings con prefijos/sufijos variados |
| 4: PostMessage JSON Parsing | `PostMessageBridge::OnWebMessageReceived` | Random JSON objects con campos válidos |
| 5: Invalid Message Handling | `PostMessageBridge::OnWebMessageReceived` | Random invalid JSON + random unrecognized actions |
| 6: Navigation URI Filtering | `ViewerWindow::SetupNavigationFilter` | Random URI strings |
| 7: Registry Invariants | `ViewerManager` create/close sequences | Random operation sequences |
| 8: FIFO Eviction | `ViewerManager` with max viewers | Random create sequences exceeding max |
| 9: Config Clamping | `ConfigService` WebView2 validation | Random integers (INT_MIN – INT_MAX) |
| 10: Window Title Format | `ViewerWindow::SetTitle` | Random language + title strings |
| 11: Cell Value Format | `ContentPipeline` return value | Random title + viewer_id strings |
| 12: Slide Ordering | `PresentationBuilder` | Random slide sequences |
| 13: Filename Format | `PresentationBuilder::Build` | Random title strings |
| 14: Extended Navigation Filter | `ViewerWindow::SetupNavigationFilter` (Advanced Mode) | Random URIs + random ports |
| 15: Pluto Status State Machine | `PlutoManager` start/stop sequences | Random operation sequences |
| 16: Pluto Port Clamping | `ConfigService` Pluto validation | Random integers (INT_MIN – INT_MAX) |
| 17: RCall Error Formatting | RCallBridge error handler | Random R error strings |
| 18: Notebook Listing | `NotebookLibrary::ListNotebooksFormatted` | Random sets of .jl filenames |
| 19: Export Validity | `NotebookExporter::ExportNotebook` | Random AnalysisContext instances |
| 20: Export Filename Sanitization | `NotebookExporter::GenerateFilename` | Random title strings (Unicode, special chars) |

### Unit Tests

| Área | Tests | Tipo |
|---|---|---|
| Runtime detection | Mock `GetAvailableCoreWebView2BrowserVersionString` → available/not available | Example |
| Environment creation | Mock success/failure con HRESULT codes | Example |
| IsAvailable() | Combinaciones de detection + environment status | Example |
| Error messages | Verify exact error strings returned to cells | Example |
| Window creation | Mock Win32 `CreateWindowEx` + verify owner/style | Integration |
| Window minimize/restore | Simulate `WM_SIZE` messages | Example |
| Viewer close + cleanup | Verify COM Release calls | Integration |
| Empty HTML handling | Pass empty/null/whitespace content | Edge case |
| Config defaults | Missing keys → verify defaults | Example |
| Config validation | Path traversal, invalid characters | Example |
| DevTools toggle | Config flag → verify `put_AreDevToolsEnabled` call | Example |
| Presentation build | Build with mixed slide types → verify output HTML | Integration |
| Fallback behavior | ViewerManager unavailable → verify HYPERLINK fallback | Example |
| Pluto start/stop | Mock process launch → verify state transitions | Example |
| Pluto port probe | Mock HTTP connection → verify reuse vs. new launch | Example |
| Pluto timeout | Mock process that never starts → verify 30s timeout + error | Example |
| Pluto shutdown on xlAutoClose | Verify process termination during Shutdown() | Integration |
| RCall available | Mock R detected → verify startup.jl loads RCall | Integration |
| RCall unavailable | Mock R not detected → verify WARNING + skip | Example |
| RCall status function | Both states → verify return strings | Example |
| Pipeline execution | Mock RCall → verify Julia+R pipeline flow | Integration |
| Notebook open | Mock Pluto server → verify notebook URL construction | Example |
| Notebook open (Pluto not running) | Verify auto-start of Pluto before opening | Example |
| Notebook not found | Invalid name → verify error string format | Edge case |
| Notebook RCall unavailable | R-dependent notebook + no RCall → verify suffix | Example |
| Export with analysis | Mock analysis context → verify .jl file content | Integration |
| Export without analysis | No prior analysis → verify error string | Edge case |
| Python deprecation error | Call PY.* without Python → verify error string | Example |
| Python backward compat | Add Python to config → verify it loads | Example |

### Integración con CMake

```cmake
# En tests/CMakeLists.txt
add_subdirectory(webview2)

# En tests/webview2/CMakeLists.txt
FetchContent_Declare(
    rapidcheck
    GIT_REPOSITORY https://github.com/emil-e/rapidcheck.git
    GIT_TAG master
)
FetchContent_MakeAvailable(rapidcheck)

add_executable(webview2_tests
    viewer_manager_test.cc
    content_pipeline_test.cc
    post_message_bridge_test.cc
    presentation_builder_test.cc
    config_validation_test.cc
    protobuf_roundtrip_test.cc
    pluto_manager_test.cc
    notebook_library_test.cc
    notebook_exporter_test.cc
    python_deprecation_test.cc
)

target_link_libraries(webview2_tests
    PRIVATE
        RJ2XCL_Core_Objects
        Common
        PB
        libprotobuf
        gtest_main
        rapidcheck
        rapidcheck_gtest
)
```

### Estructura de Archivos de Test

```
tests/webview2/
├── CMakeLists.txt
├── viewer_manager_test.cc      # Properties 7, 8 + unit tests
├── content_pipeline_test.cc    # Properties 2, 3, 11 + unit tests
├── post_message_bridge_test.cc # Properties 4, 5 + unit tests
├── navigation_filter_test.cc   # Properties 6, 14
├── config_validation_test.cc   # Properties 9, 16 + unit tests
├── protobuf_roundtrip_test.cc  # Property 1
├── presentation_builder_test.cc # Properties 12, 13 + unit tests
├── window_title_test.cc        # Property 10
├── pluto_manager_test.cc       # Property 15 + unit tests (start/stop/status/timeout)
├── notebook_library_test.cc    # Property 18 + unit tests (open/list/not found/RCall)
├── notebook_exporter_test.cc   # Properties 19, 20 + unit tests (export/sanitize)
├── rcall_error_test.cc         # Property 17
├── python_deprecation_test.cc  # Unit tests (deprecation error, backward compat)
└── mocks/
    ├── mock_webview2.h          # Mock ICoreWebView2* interfaces
    ├── mock_excel_bridge.h      # Mock IExcelBridge
    ├── mock_win32.h             # Mock Win32 API calls
    ├── mock_process.h           # Mock process launch/terminate (for PlutoManager)
    └── mock_filesystem.h        # Mock file operations (for NotebookLibrary/Exporter)
```
