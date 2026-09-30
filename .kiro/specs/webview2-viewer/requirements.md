# Requirements Document

## Introduction

Este documento especifica los requerimientos para integrar un visor WebView2 embebido dentro de Excel, como parte del add-in RJ2XCL. Actualmente, las visualizaciones interactivas generadas por R, Julia y Python (Plotly, D3.js, Sankey, etc.) se abren en el navegador predeterminado mediante un workaround con HYPERLINK. Esta funcionalidad reemplaza ese flujo con un visor embebido que renderiza contenido HTML directamente dentro del entorno de Excel, proporcionando una experiencia integrada y sin cambio de contexto.

El visor soportará contenido HTML generado por los motores de lenguaje soportados (R y Julia), reportes HTML, y tablas de datos interactivas. La integración se realiza a nivel del XLL usando el SDK de WebView2 de Microsoft, con comunicación bidireccional entre Excel y el contenido web renderizado.

Adicionalmente, el visor WebView2 sirve como plataforma para un **Modo Avanzado** basado en Pluto.jl, donde usuarios técnicos pueden abrir notebooks interactivos directamente dentro de Excel. Este modo avanzado integra Pluto.jl como servidor de notebooks, RCall.jl para pipelines mixtos Julia+R, una biblioteca de 13 notebooks precargados, y capacidades de reproducibilidad mediante exportación de análisis como notebooks. Python (ControlPython.exe) queda formalmente deprecado — Julia cubre toda la funcionalidad previamente planificada para Python (ML, conectividad de datos, AI).

## Glossary

- **XLL**: El add-in de Excel RJ2XCL compilado como DLL, cargado por Microsoft Excel.
- **WebView2_Runtime**: El runtime de Microsoft Edge WebView2 que proporciona el motor de renderizado Chromium embebido. Puede estar preinstalado (Evergreen) o distribuirse como Fixed Version.
- **WebView2_Controller**: El objeto COM `ICoreWebView2Controller` que gestiona la instancia del visor WebView2, incluyendo su ventana, visibilidad y tamaño.
- **WebView2_Environment**: El objeto COM `ICoreWebView2Environment` que representa la configuración del runtime WebView2, incluyendo el directorio de datos de usuario y opciones de inicialización.
- **Viewer_Window**: La ventana Win32 modeless (no modal) que hospeda el WebView2_Controller y se muestra como panel flotante asociado a la ventana de Excel.
- **Content_Pipeline**: El flujo de datos desde la generación de HTML en un ControlX_Process hasta su renderizado en el WebView2_Controller, pasando por el Named_Pipe y el XLL.
- **ControlX_Process**: Un proceso hijo (ControlR.exe, ControlJulia.exe, o ControlPython.exe) que hospeda un runtime de lenguaje y se comunica con el XLL vía Named Pipes.
- **Named_Pipe**: El mecanismo IPC de Windows usado para comunicación bidireccional entre el XLL y cada ControlX_Process.
- **GraphicsHandler**: La clase C++ existente (`GraphicsHandler.cc`) que procesa callbacks de gráficos desde los ControlX_Process.
- **HTML_Content**: Contenido HTML completo (incluyendo CSS y JavaScript inline) generado por librerías de visualización (Plotly, D3.js, htmlwidgets) en R, Julia o Python.
- **Viewer_Manager**: El nuevo componente singleton que gestiona el ciclo de vida de todas las instancias de Viewer_Window, incluyendo creación, destrucción y enumeración.
- **PostMessage_Bridge**: El mecanismo de comunicación bidireccional entre el código JavaScript ejecutándose en WebView2 y el código C++ del XLL, usando `window.chrome.webview.postMessage` y `ICoreWebView2::PostWebMessageAsJson`.
- **User_Data_Folder**: El directorio donde WebView2 almacena caché, cookies y datos de sesión. Se ubica dentro del directorio home de RJ2XCL.
- **ConfigService**: El singleton (`ConfigService.cc`) que lee `rj2xcl-config.json` y expone getters tipados para configuración.
- **LogService**: El singleton thread-safe (`LogService.cc`) que escribe mensajes con timestamp y severidad al archivo de log.
- **Security_Policy**: El conjunto de restricciones aplicadas al WebView2_Environment para limitar la navegación, acceso a archivos y ejecución de scripts al contenido generado por RJ2XCL.
- **Reveal_Presentation**: Una presentación HTML autocontenida generada con reveal.js, que incluye slides con texto, visualizaciones interactivas y otros objetos embebidos. El archivo resultante es un único `.html` que puede abrirse en cualquier navegador sin dependencias externas.
- **Presentation_Builder**: El componente que permite al usuario componer una presentación reveal.js seleccionando contenido de los Viewer_Window activos y añadiendo slides de texto.
- **Pluto_Server**: El servidor Pluto.jl que ejecuta notebooks Julia reactivos en `localhost`, configurable en el puerto 1234 por defecto. Actúa como entorno de notebooks interactivos accesible desde el Viewer_Window en Modo Avanzado.
- **Advanced_Mode**: Modo opcional del visor WebView2 que carga la interfaz de Pluto.jl en un Viewer_Window, permitiendo a usuarios técnicos ver y editar el código Julia/R que ejecuta los análisis.
- **RCall_Bridge**: La integración de RCall.jl dentro del proceso Julia que permite invocar funciones R directamente desde código Julia, habilitando pipelines mixtos Julia+R sin requerir un proceso R separado.
- **Notebook_Library**: La colección de 13 notebooks Pluto precargados almacenados en `%RJ2XCL_HOME%/notebooks/`, organizados por categoría de análisis (R via RCall, Julia nativo, mixto R+Julia).
- **Notebook_Export**: La funcionalidad que captura un análisis ejecutado desde Excel y lo exporta como un archivo `.jl` de notebook Pluto reproducible, incluyendo datos, parámetros, código y resultados.
- **ControlPython_Process**: El proceso hijo ControlPython.exe que hospeda el runtime de Python. Formalmente deprecado en favor de Julia, que cubre toda la funcionalidad previamente planificada para Python.

## Requirements

### Requirement 1: WebView2 Runtime Detection and Initialization

**User Story:** As an Excel user, I want the add-in to detect and initialize the WebView2 runtime automatically, so that I can view interactive visualizations without manual setup.

#### Acceptance Criteria

1. WHEN the XLL is loaded by Excel, THE Viewer_Manager SHALL detect whether the WebView2_Runtime is installed by querying the registry or calling `GetAvailableCoreWebView2BrowserVersionString`.
2. WHEN the WebView2_Runtime is detected as available, THE Viewer_Manager SHALL create a WebView2_Environment using the User_Data_Folder located at `%RJ2XCL_HOME%/webview2-data`.
3. IF the WebView2_Runtime is not detected, THEN THE Viewer_Manager SHALL log a WARNING via LogService with the message "WebView2 runtime not found — interactive viewer disabled" and set its availability status to false.
4. WHEN the WebView2_Environment creation fails, THE Viewer_Manager SHALL log the HRESULT error code at ERROR level via LogService and set its availability status to false.
5. THE Viewer_Manager SHALL expose an `IsAvailable()` method that returns true only when the WebView2_Runtime has been detected and the WebView2_Environment has been created successfully.
6. WHEN a user invokes a viewer function while the Viewer_Manager availability status is false, THE XLL SHALL return the cell value "WebView2 not available — install Edge WebView2 Runtime" instead of attempting to create a Viewer_Window.

### Requirement 2: Viewer Window Creation and Excel Integration

**User Story:** As an Excel user, I want the interactive viewer to appear as a floating panel near my Excel window, so that I can see visualizations alongside my spreadsheet data.

#### Acceptance Criteria

1. WHEN HTML_Content is ready for display, THE Viewer_Manager SHALL create a Viewer_Window as a modeless Win32 dialog owned by the Excel main window handle.
2. THE Viewer_Window SHALL be positioned adjacent to the Excel window, defaulting to the right side with a width of 800 pixels and a height of 600 pixels.
3. WHEN the Excel window is minimized, THE Viewer_Window SHALL be hidden automatically.
4. WHEN the Excel window is restored from minimized state, THE Viewer_Window SHALL be shown automatically.
5. THE Viewer_Window SHALL include a title bar displaying the format "[Language] — [Title]" where Language is R, Julia, or Python and Title is derived from the HTML content or the generating function name.
6. WHEN the user closes a Viewer_Window via the close button, THE Viewer_Manager SHALL destroy the associated WebView2_Controller and release all COM resources for that instance.
7. THE Viewer_Window SHALL be resizable by the user via standard Win32 window resize handles, and THE WebView2_Controller SHALL adjust its bounds to match the new window size.

### Requirement 3: HTML Content Loading from Language Engines

**User Story:** As an Excel user, I want visualizations generated by R, Julia, or Python to appear automatically in the embedded viewer, so that I do not need to open a browser manually.

#### Acceptance Criteria

1. WHEN a ControlX_Process generates HTML_Content (via Plotly, D3.js, htmlwidgets, or similar libraries), THE Content_Pipeline SHALL transmit the content to the XLL via the existing Named_Pipe as a Protobuf message with a new `html_content` field.
2. WHEN the XLL receives a Protobuf message containing `html_content`, THE GraphicsHandler SHALL delegate the content to the Viewer_Manager for rendering.
3. WHEN the HTML_Content size is less than 2 MB, THE Viewer_Manager SHALL load the content into the WebView2_Controller using `NavigateToString`.
4. WHEN the HTML_Content size is 2 MB or greater, THE Viewer_Manager SHALL write the content to a temporary file in the User_Data_Folder and load it using `Navigate` with a `file://` URI.
5. WHEN temporary HTML files are created for large content, THE Viewer_Manager SHALL delete the temporary file after the WebView2_Controller has completed navigation (detected via the `NavigationCompleted` event).
6. IF the HTML_Content is empty or null, THEN THE Viewer_Manager SHALL log a WARNING via LogService and not create a Viewer_Window.
7. THE Content_Pipeline SHALL support HTML_Content generated by the existing `rj2xcl_plotly_export` function in Python, the `htmlwidgets::saveWidget` pattern in R, and the MIME display system (`text/html`) in Julia.

### Requirement 4: Bidirectional Communication Between Excel and WebView2

**User Story:** As an Excel user, I want interactive visualizations to be able to send data back to Excel (e.g., selected data points), so that I can use visualization interactions to drive spreadsheet calculations.

#### Acceptance Criteria

1. THE Viewer_Manager SHALL inject a JavaScript bridge object into every loaded HTML page that exposes the function `window.rj2xcl.sendToExcel(data)` where data is a JSON-serializable object.
2. WHEN JavaScript code calls `window.rj2xcl.sendToExcel(data)`, THE PostMessage_Bridge SHALL receive the message via the `WebMessageReceived` event handler and parse the JSON payload.
3. WHEN a valid PostMessage_Bridge message is received with action "write-cell", THE XLL SHALL write the specified value to the target Excel cell identified by sheet name and cell reference in the JSON payload.
4. WHEN a valid PostMessage_Bridge message is received with action "notify", THE XLL SHALL display the message text in the Excel status bar.
5. IF a PostMessage_Bridge message contains invalid JSON or an unrecognized action, THEN THE Viewer_Manager SHALL log the error at WARNING level via LogService and discard the message without affecting Excel state.
6. THE Viewer_Manager SHALL provide a method `SendToViewer(viewer_id, json_message)` that calls `PostWebMessageAsJson` on the specified WebView2_Controller to send data from Excel to the JavaScript context.

### Requirement 5: Excel Function Interface for Viewer Operations

**User Story:** As an Excel user, I want dedicated worksheet functions to control the embedded viewer, so that I can open visualizations and manage viewer windows from formulas.

#### Acceptance Criteria

1. THE XLL SHALL register a worksheet function `=RJ2XCL.VIEW(content_or_path)` that opens HTML_Content in a Viewer_Window and returns the viewer identifier string.
2. WHEN `=RJ2XCL.VIEW` receives a file path ending in `.html` or `.htm`, THE Viewer_Manager SHALL load the file content and display it in a new Viewer_Window.
3. WHEN `=RJ2XCL.VIEW` receives a string that starts with `<!DOCTYPE` or `<html`, THE Viewer_Manager SHALL treat the string as inline HTML_Content and display it directly.
4. THE XLL SHALL register a worksheet function `=RJ2XCL.VIEWER.CLOSE(viewer_id)` that closes the specified Viewer_Window and returns "OK" on success.
5. THE XLL SHALL register a worksheet function `=RJ2XCL.VIEWER.LIST()` that returns a comma-separated list of active viewer identifiers.
6. IF `=RJ2XCL.VIEW` is called when the Viewer_Manager availability status is false, THEN THE function SHALL return the error string "WebView2 not available" without attempting to create a window.

### Requirement 6: Security and Sandboxing

**User Story:** As a system administrator, I want the embedded viewer to be sandboxed so that it cannot navigate to arbitrary websites or access the local filesystem beyond the generated content, protecting the organization's security posture.

#### Acceptance Criteria

1. THE Viewer_Manager SHALL configure the WebView2_Environment with navigation restrictions that block all navigation except `file://` URIs within the User_Data_Folder and `about:blank`.
2. WHEN the WebView2_Controller attempts to navigate to a URI outside the allowed set, THE Viewer_Manager SHALL cancel the navigation via the `NavigationStarting` event handler and log the blocked URI at WARNING level via LogService.
3. THE Viewer_Manager SHALL disable the following WebView2 features on every WebView2_Controller: DevTools (`put_AreDevToolsEnabled(FALSE)`), context menu (`put_AreDefaultContextMenusEnabled(FALSE)`), and status bar (`put_IsStatusBarEnabled(FALSE)`).
4. THE Viewer_Manager SHALL disable the built-in error page via `put_IsBuiltInErrorPageEnabled(FALSE)` on every WebView2_Controller.
5. WHEN HTML_Content contains `<script>` tags, THE WebView2_Controller SHALL execute the scripts within the Chromium sandbox, preserving full JavaScript interactivity (Plotly hover/zoom/pan, D3.js transitions, htmlwidgets event handlers) without access to the host filesystem or network beyond the allowed navigation set.
6. THE Security_Policy configuration SHALL be readable from `rj2xcl-config.json` under the key `WebView2.security`, allowing administrators to enable DevTools for debugging via a `devToolsEnabled` boolean flag.
7. WHERE the `WebView2.security.devToolsEnabled` flag is set to true in ConfigService, THE Viewer_Manager SHALL enable DevTools on WebView2_Controller instances.

### Requirement 7: Multiple Viewer Instance Management

**User Story:** As an Excel user, I want to open multiple visualizations simultaneously in separate viewer windows, so that I can compare charts and results side by side.

#### Acceptance Criteria

1. THE Viewer_Manager SHALL support a configurable maximum number of concurrent Viewer_Window instances, defaulting to 8, readable from `rj2xcl-config.json` under the key `WebView2.maxViewers`.
2. WHEN the number of active Viewer_Window instances equals the configured maximum, THE Viewer_Manager SHALL close the oldest Viewer_Window (FIFO order) before creating a new one.
3. THE Viewer_Manager SHALL assign a unique string identifier to each Viewer_Window in the format "viewer-[N]" where N is a monotonically increasing integer.
4. WHEN the XLL is unloaded (xlAutoClose), THE Viewer_Manager SHALL close all active Viewer_Window instances and release all WebView2 COM resources.
5. THE Viewer_Manager SHALL maintain an internal registry of active Viewer_Window instances that supports enumeration, lookup by identifier, and count queries.

### Requirement 8: Performance and Memory Management

**User Story:** As an Excel user, I want the embedded viewer to be responsive and not degrade Excel performance, so that my spreadsheet workflow remains smooth.

#### Acceptance Criteria

1. THE Viewer_Manager SHALL create the WebView2_Environment asynchronously during XLL initialization so that Excel startup is not blocked by WebView2 initialization.
2. WHEN a Viewer_Window is closed, THE Viewer_Manager SHALL release the associated WebView2_Controller and verify that the COM reference count reaches zero, logging a WARNING via LogService if it does not.
3. THE Viewer_Manager SHALL create WebView2_Controller instances on a dedicated STA (Single-Threaded Apartment) thread separate from the Excel main thread, using a message pump to process COM callbacks.
4. WHEN the WebView2_Controller fires the `NavigationCompleted` event, THE Viewer_Manager SHALL log the navigation duration in milliseconds at DEBUG level via LogService.
5. THE Viewer_Manager SHALL limit the total memory footprint of all WebView2 browser processes to a configurable threshold (default 512 MB), readable from `rj2xcl-config.json` under the key `WebView2.maxMemoryMB`. WHEN the threshold is exceeded, THE Viewer_Manager SHALL close the oldest Viewer_Window to reclaim memory.
6. IF WebView2_Controller creation fails due to resource exhaustion, THEN THE Viewer_Manager SHALL return an error message "Viewer creation failed — too many active viewers or insufficient memory" and log the failure at ERROR level via LogService.

### Requirement 9: Content Pipeline Integration with Existing Graphics System

**User Story:** As an Excel user, I want my existing R and Julia interactive graphics workflows (Plotly, D3.js) to automatically use the embedded viewer instead of opening a browser, so that the transition is seamless.

#### Acceptance Criteria

1. WHEN the Viewer_Manager availability status is true, THE Content_Pipeline SHALL route HTML_Content to the Viewer_Manager instead of writing a HYPERLINK formula to the cell.
2. WHEN the Viewer_Manager availability status is false, THE Content_Pipeline SHALL fall back to the existing behavior of saving the HTML file and returning a HYPERLINK formula.
3. THE Content_Pipeline SHALL support the Julia MIME display system by intercepting `text/html` MIME type callbacks from the `RJ2XCLDisplay` in `startup.jl` and routing the HTML data to the Viewer_Manager.
4. THE Content_Pipeline SHALL support the Python `rj2xcl_plotly_export` function by detecting HTML file output and loading the file content into the Viewer_Manager.
5. THE Content_Pipeline SHALL support the R `htmlwidgets::saveWidget` pattern by detecting HTML file output from R interactive graphics functions and loading the file content into the Viewer_Manager.
6. WHEN HTML_Content is routed to the Viewer_Manager, THE XLL SHALL return a cell value in the format "📊 [Title] (viewer-[N])" indicating the content is displayed in the embedded viewer.

### Requirement 10: Configuration and Feature Toggle

**User Story:** As a system administrator, I want to enable or disable the WebView2 viewer via configuration, so that I can control the feature rollout and troubleshoot issues.

#### Acceptance Criteria

1. THE ConfigService SHALL read a boolean flag `WebView2.enabled` from `rj2xcl-config.json`, defaulting to true when the key is absent.
2. WHEN `WebView2.enabled` is set to false, THE Viewer_Manager SHALL not attempt to detect or initialize the WebView2_Runtime and SHALL report its availability status as false.
3. THE ConfigService SHALL read the `WebView2.maxViewers` integer value, validating it is within the range 1–16 and clamping to the nearest bound if out of range.
4. THE ConfigService SHALL read the `WebView2.maxMemoryMB` integer value, validating it is within the range 128–2048 and clamping to the nearest bound if out of range.
5. THE ConfigService SHALL read the `WebView2.userDataFolder` string value, defaulting to `%RJ2XCL_HOME%/webview2-data` when the key is absent.
6. WHEN any WebView2 configuration value is out of range, THE ConfigService SHALL log a WARNING via LogService with the key name, the provided value, and the clamped value.

### Requirement 11: Interactive Visualization Support

**User Story:** As an Excel user, I want my Plotly, D3.js, and htmlwidgets visualizations to be fully interactive in the embedded viewer (zoom, pan, hover tooltips, click events, brush selection), so that I get the same experience as in a browser.

#### Acceptance Criteria

1. THE WebView2_Controller SHALL enable JavaScript execution (`put_IsScriptEnabled(TRUE)`) on all Viewer_Window instances to support interactive visualization libraries.
2. WHEN Plotly HTML_Content is loaded, THE Viewer_Window SHALL support all standard Plotly interactions: hover tooltips, zoom, pan, lasso selection, box selection, and toolbar buttons (download PNG, autoscale, reset axes).
3. WHEN D3.js HTML_Content is loaded, THE Viewer_Window SHALL support mouse and touch event handlers registered by the D3.js visualization, including drag, zoom, and click interactions.
4. WHEN htmlwidgets HTML_Content (e.g., DT, leaflet, highcharter) is loaded, THE Viewer_Window SHALL support the widget's native interactivity including sorting, filtering, pagination, and event callbacks.
5. THE WebView2_Controller SHALL allow inline `data:` URIs and `blob:` URIs within loaded HTML_Content to support Plotly's image export and D3.js dynamic SVG generation.
6. WHEN a Plotly chart's "Download plot as PNG" toolbar button is clicked, THE WebView2_Controller SHALL allow the download and save the file to the User_Data_Folder, logging the saved file path at INFO level via LogService.

### Requirement 12: Reveal.js Presentation Builder

**User Story:** As an Excel user, I want to create self-contained HTML presentations using reveal.js that embed my interactive visualizations and custom text slides, so that I can share my analysis results as a portable presentation.

#### Acceptance Criteria

1. THE XLL SHALL register a worksheet function `=RJ2XCL.PRESENTATION.NEW(title)` that creates a new Reveal_Presentation with the specified title and returns a presentation identifier string.
2. THE XLL SHALL register a worksheet function `=RJ2XCL.PRESENTATION.ADD.SLIDE(presentation_id, content, slide_type)` where slide_type is "text", "viewer", or "html". WHEN slide_type is "viewer", THE Presentation_Builder SHALL capture the current HTML_Content from the Viewer_Window identified by the content parameter. WHEN slide_type is "text", THE Presentation_Builder SHALL create a slide with the text content formatted as Markdown. WHEN slide_type is "html", THE Presentation_Builder SHALL embed the raw HTML content as a slide.
3. THE XLL SHALL register a worksheet function `=RJ2XCL.PRESENTATION.BUILD(presentation_id, output_path)` that generates a self-contained HTML file at the specified output_path containing the reveal.js framework and all added slides.
4. THE Presentation_Builder SHALL embed the reveal.js library (CSS and JavaScript) inline in the output HTML file so that the presentation is fully self-contained with no external dependencies.
5. WHEN a slide of type "viewer" contains interactive Plotly or D3.js content, THE Presentation_Builder SHALL embed the visualization's HTML, CSS, and JavaScript inline in the slide, preserving interactivity in the output presentation.
6. THE Presentation_Builder SHALL embed all referenced assets (images, fonts, data) as base64-encoded data URIs in the output HTML file to ensure the presentation is portable.
7. WHEN `=RJ2XCL.PRESENTATION.BUILD` completes successfully, THE Presentation_Builder SHALL open the generated HTML file in a Viewer_Window for preview and return the absolute file path.
8. IF the output_path is not specified or is empty, THEN THE Presentation_Builder SHALL save the presentation to the User_Data_Folder with the filename format "presentation_[title]_[YYYYMMDD_HHMMSS].html".

### Requirement 13: Pluto.jl Advanced Mode

**User Story:** As a technical user (data scientist, researcher, quantitative analyst), I want to open Pluto.jl notebooks directly inside the WebView2 viewer within Excel, so that I can view and edit the Julia/R code that executes analyses without leaving the Excel environment.

#### Acceptance Criteria

1. WHEN the user activates Advanced_Mode via the function `=RJ2XCL.PLUTO.START()`, THE XLL SHALL launch the Pluto_Server as a background process on the configured port (default 1234) and return the string "Pluto started on port [port]".
2. WHEN the Pluto_Server is starting, THE XLL SHALL detect whether a Pluto_Server is already running on the configured port by attempting an HTTP connection to `localhost:[port]`. IF a server is already running, THEN THE XLL SHALL reuse the existing server and log an INFO message "Pluto server already running on port [port]" via LogService.
3. WHEN the Pluto_Server has started successfully, THE Viewer_Manager SHALL open a Viewer_Window navigated to `http://localhost:[port]` displaying the Pluto notebook interface.
4. THE Security_Policy SHALL allow navigation to `http://localhost:[port]` and its subpaths when Advanced_Mode is active, in addition to the existing allowed URIs (`file://` within User_Data_Folder and `about:blank`).
5. WHEN the user edits code in a Pluto notebook loaded in the Viewer_Window, THE Pluto_Server SHALL execute the modified cells reactively, and the changes SHALL be reflected in subsequent Excel function calls that invoke the same analysis.
6. THE ConfigService SHALL read the Pluto_Server port from `rj2xcl-config.json` under the key `Pluto.port`, defaulting to 1234 when the key is absent, and validating it is within the range 1024–65535.
7. THE XLL SHALL register a worksheet function `=RJ2XCL.PLUTO.STOP()` that sends a shutdown signal to the Pluto_Server, closes the associated Viewer_Window, and returns "Pluto stopped".
8. WHEN Excel is closed (xlAutoClose), THE Viewer_Manager SHALL terminate the Pluto_Server process if it was started by the current Excel session, ensuring clean process lifecycle management.
9. IF the Pluto_Server fails to start within 30 seconds, THEN THE XLL SHALL log an ERROR via LogService with the failure reason and return the error string "Pluto server failed to start — check Julia installation".
10. THE XLL SHALL register a worksheet function `=RJ2XCL.PLUTO.STATUS()` that returns "running" when the Pluto_Server is active, "stopped" when the Pluto_Server is not running, or "starting" when the Pluto_Server is in the initialization phase.

### Requirement 14: RCall.jl Integration for Mixed Pipelines

**User Story:** As a technical user, I want Julia functions to call R internally via RCall.jl, so that I can build pipelines that combine Julia optimization with R statistical analysis and visualization without leaving the Excel workflow.

#### Acceptance Criteria

1. WHEN ControlJulia.exe starts and R is detected as available by the DiscoveryService, THE Julia startup script (`startup.jl`) SHALL load the RCall.jl package and initialize the R bridge.
2. IF R is not detected as available during ControlJulia.exe startup, THEN THE Julia startup script SHALL log a WARNING via the Julia logging system with the message "R not found — RCall.jl disabled; R-dependent notebooks will not function" and skip RCall.jl loading.
3. THE XLL SHALL register worksheet functions following the pattern `=J.pipeline_[name](data, params)` that invoke Julia functions combining both Julia native computation and R via RCall.jl in a single pipeline.
4. WHEN a pipeline function is invoked, THE ControlJulia.exe process SHALL execute the Julia code that internally calls R functions via RCall.jl, without requiring any changes to the existing ControlR.exe architecture.
5. THE RCall_Bridge SHALL support data transfer between Julia and R using RCall.jl's built-in type conversion for DataFrames, vectors, matrices, and scalar values, without writing intermediate files.
6. WHEN an R function invoked via RCall.jl raises an error, THE ControlJulia.exe process SHALL catch the RCall exception, format the R error message with a Julia stack trace, and return the combined error string to the XLL via the Named_Pipe.
7. THE RCall_Bridge loading status SHALL be queryable via the worksheet function `=J.rcall_status()` that returns "available" when RCall.jl is loaded and R is connected, or "unavailable" with a reason string when RCall.jl is not loaded.

### Requirement 15: Notebook Library

**User Story:** As an Excel user, I want access to a library of preconfigured Pluto notebooks covering common analysis categories, so that I can open ready-to-use analysis templates in the WebView2 viewer and customize them for my data.

#### Acceptance Criteria

1. THE RJ2XCL installation SHALL include 13 preconfigured Pluto notebook files stored in the directory `%RJ2XCL_HOME%/notebooks/`.
2. THE Notebook_Library SHALL contain notebooks organized by engine category: 7 notebooks using R via RCall.jl (`stats_regression.jl`, `lme4_mixed_models.jl`, `survival_analysis.jl`, `forecast_arima.jl`, `psych_factor_analysis.jl`, `plm_panel_econometrics.jl`, `rstanarm_bayes.jl`), 5 notebooks using Julia native (`jump_optimization.jl`, `diffeq_simulation.jl`, `turing_hierarchical.jl`, `montecarlo_risk.jl`, `linalg_decomposition.jl`), and 1 mixed R+Julia notebook (`multilang_pipeline.jl`).
3. THE XLL SHALL register a worksheet function `=RJ2XCL.NOTEBOOK.OPEN(notebook_name)` that opens the specified notebook in the Pluto_Server and displays it in a Viewer_Window. IF the Pluto_Server is not running, THEN THE function SHALL start the Pluto_Server before opening the notebook.
4. THE XLL SHALL register a worksheet function `=RJ2XCL.NOTEBOOK.LIST()` that returns a comma-separated list of available notebook names from the `%RJ2XCL_HOME%/notebooks/` directory.
5. WHEN a user modifies a preconfigured notebook in the Pluto interface, THE Pluto_Server SHALL save the modified version to `%RJ2XCL_HOME%/notebooks/custom/` with the original filename, preserving the original template in the `notebooks/` directory.
6. WHEN `=RJ2XCL.NOTEBOOK.LIST()` is called, THE function SHALL include both preconfigured notebooks from `%RJ2XCL_HOME%/notebooks/` and custom notebooks from `%RJ2XCL_HOME%/notebooks/custom/`, with custom notebooks indicated by a "[custom]" suffix.
7. IF the specified notebook_name does not match any file in the notebooks directory or the custom directory, THEN THE `=RJ2XCL.NOTEBOOK.OPEN` function SHALL return the error string "Notebook not found: [notebook_name]" and log a WARNING via LogService.
8. WHEN a notebook that requires RCall.jl is opened and the RCall_Bridge is not available, THE Pluto_Server SHALL display a warning in the notebook interface indicating that R-dependent cells will not execute, and THE `=RJ2XCL.NOTEBOOK.OPEN` function SHALL return the viewer identifier with the suffix " (R unavailable)".

### Requirement 16: Analysis Reproducibility

**User Story:** As a researcher, I want to export any analysis executed from Excel as a standalone Pluto notebook, so that I can reproduce, share, and version-control my analytical work.

#### Acceptance Criteria

1. THE XLL SHALL register a worksheet function `=RJ2XCL.NOTEBOOK.EXPORT(title)` that captures the last analysis executed from Excel and generates a Pluto notebook file (`.jl`) in the `%RJ2XCL_HOME%/notebooks/exports/` directory.
2. WHEN `=RJ2XCL.NOTEBOOK.EXPORT(title)` is called, THE Notebook_Export SHALL include in the generated notebook: the input data used in the analysis, the parameters passed to the function, the Julia or R code that executed the analysis, and the results produced.
3. THE generated notebook file SHALL be a valid Pluto.jl notebook that can be opened and executed standalone in any Pluto.jl environment without requiring the RJ2XCL add-in.
4. THE generated notebook file SHALL be a plain-text `.jl` file compatible with Git version control, following the standard Pluto notebook format with cell markers.
5. WHEN `=RJ2XCL.NOTEBOOK.EXPORT(title)` completes successfully, THE function SHALL return the absolute file path of the generated notebook.
6. IF no analysis has been executed in the current Excel session, THEN THE `=RJ2XCL.NOTEBOOK.EXPORT` function SHALL return the error string "No analysis to export — execute an analysis first" and log a WARNING via LogService.
7. THE Notebook_Export SHALL sanitize the title parameter by replacing non-alphanumeric characters with underscores and use the filename format "[sanitized_title]_[YYYYMMDD_HHMMSS].jl".

### Requirement 17: Python Formal Deprecation

**User Story:** As a system maintainer, I want Python (ControlPython.exe) to be formally deprecated and removed from the default configuration, so that the system focuses on the supported R + Julia engines and reduces maintenance burden.

#### Acceptance Criteria

1. THE default `rj2xcl-languages.json` configuration file SHALL include only R and Julia as supported language engines, excluding Python from the default language list.
2. WHEN the XLL loads `rj2xcl-languages.json` and Python is not listed, THE XLL SHALL not attempt to start the ControlPython_Process and SHALL not register any `=PY.*` worksheet functions.
3. THE ControlPython_Process source code SHALL be preserved in the repository under its existing directory structure, but THE CMake build system SHALL exclude ControlPython.exe from the default build targets.
4. WHERE an administrator adds Python back to `rj2xcl-languages.json` manually, THE XLL SHALL load and start the ControlPython_Process as before, maintaining backward compatibility for environments that require Python.
5. THE Content_Pipeline SHALL remove Python-specific detection logic (the `rj2xcl_plotly_export` function) from the default code path, while preserving the code behind a compile-time flag `RJ2XCL_ENABLE_PYTHON` for backward compatibility.
6. THE project documentation (README, CHANGELOG, user guides) SHALL state that Python is deprecated in favor of Julia, listing the Julia equivalents for previously planned Python functionality: ML (Flux.jl), data connectivity (CSV.jl, DataFrames.jl, ODBC.jl), and AI (Transformers.jl, HuggingFaceHub.jl).
7. WHEN a user calls a `=PY.*` function and Python is not configured, THE XLL SHALL return the error string "Python is deprecated — use Julia (=J.*) functions instead. See documentation for migration guide."
