# Implementation Plan: WebView2 Embedded Viewer for RJ2XCL

## Overview

This plan implements an embedded WebView2 viewer within the RJ2XCL XLL add-in, enabling interactive HTML content (Plotly, D3.js, htmlwidgets, DT, leaflet) to render directly in floating windows associated with Excel. The implementation follows an incremental approach: CMake/SDK integration first, then core components (ViewerManager, ViewerWindow), content pipeline, communication bridge, Excel functions, security, configuration, and finally the PresentationBuilder. Each task builds on the previous ones, with property-based tests placed close to the code they validate.

## Tasks

- [x] 1. CMake integration and WebView2 SDK setup
  - [x] 1.1 Add WebView2 SDK via FetchContent to root `RJ2XCL/CMakeLists.txt`
    - Add `FetchContent_Declare` for `Microsoft.Web.WebView2` NuGet package (v1.0.2903.40)
    - Set `WEBVIEW2_INCLUDE_DIR` and `WEBVIEW2_LOADER_DIR` variables pointing to the extracted SDK paths
    - Call `FetchContent_MakeAvailable(webview2)`
    - _Requirements: Design — CMake Integration section_

  - [x] 1.2 Update `RJ2XCL/RJ2XCL/CMakeLists.txt` to link WebView2
    - Add `target_include_directories` for `${WEBVIEW2_INCLUDE_DIR}` on `RJ2XCL_Core_Objects`
    - Link `WebView2LoaderStatic.lib` from `${WEBVIEW2_LOADER_DIR}` to `RJ2XCL_Core`
    - Verify the build compiles with `#include <WebView2.h>` in a stub source file
    - _Requirements: Design — CMake Integration section_

  - [x] 1.3 Extend Protobuf schema with `HtmlContent` message
    - Add `HtmlContent` message to `RJ2XCL/PB/variable.proto` with fields: `html` (string, 1), `title` (string, 2), `source_language` (string, 3), `mime_type` (string, 4)
    - Add `HtmlContent html_content = 16` to the `Variable.value` oneof
    - Regenerate protobuf C++ sources and verify compilation
    - _Requirements: 3.1_

- [x] 2. ViewerManager singleton — runtime detection and lifecycle
  - [x] 2.1 Create `RJ2XCL/Common/ViewerManager.h` and `RJ2XCL/Common/ViewerManager.cc`
    - Implement singleton pattern (`Instance()`) consistent with `ConfigService` and `WindowManager`
    - Implement `Initialize()`: call `GetAvailableCoreWebView2BrowserVersionString` to detect runtime; set `available_` flag
    - Implement `IsAvailable()` returning `available_`
    - Implement `Shutdown()`: send `WM_QUIT` to STA thread, wait with timeout, cleanup
    - Log WARNING via LogService when runtime not found: "WebView2 runtime not found — interactive viewer disabled"
    - Log ERROR with HRESULT when environment creation fails
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.2 Implement STA thread with message pump
    - Create dedicated thread in `Initialize()` with `CoInitializeEx(NULL, COINIT_APARTMENTTHREADED)`
    - Implement `STAThreadProc()` with `GetMessage`/`DispatchMessage` loop
    - Define custom window messages: `WM_APP_CREATE_VIEWER`, `WM_APP_NAVIGATE_STRING`, `WM_APP_NAVIGATE_FILE`, `WM_APP_SEND_MESSAGE`, `WM_APP_CLOSE_VIEWER`
    - Use `PostThreadMessage` from Excel UI thread to communicate with STA thread
    - Signal `environment_ready_event_` after successful `CreateCoreWebView2EnvironmentWithOptions`
    - _Requirements: 8.1, 8.3_

  - [x] 2.3 Implement viewer registry (create, close, list, lookup)
    - Implement `CreateViewer()` and `CreateViewerFromFile()` — assign unique IDs in format `"viewer-[N]"` with monotonically increasing counter
    - Implement `CloseViewer(viewer_id)` — destroy window, release COM resources, remove from registry
    - Implement `CloseAllViewers()` — iterate and close all entries
    - Implement `ListViewers()` — return vector of active viewer IDs
    - Protect `viewers_` vector with `viewers_mutex_`
    - Store `ViewerEntry` with id, language, title, window pointer, created_at, content_size_bytes
    - _Requirements: 7.3, 7.4, 7.5_

  - [ ]* 2.4 Write property test: Viewer Registry Invariants (Property 7)
    - **Property 7: Viewer Registry Invariants**
    - For any sequence of CreateViewer and CloseViewer operations, verify: (a) unique IDs in "viewer-[N]" format, (b) ListViewers() matches active set, (c) count is correct, (d) lookup returns correct entry
    - Use custom random generators with `std::mt19937` (consistent with existing PBT pattern in `reliability_pbt.cc`)
    - Minimum 100 iterations
    - **Validates: Requirements 7.3, 7.5, 5.5**

  - [x] 2.5 Implement FIFO eviction when max viewers reached
    - Read `WebView2.maxViewers` from ConfigService (default 8, range 1–16)
    - When active count equals max, close the viewer with earliest `created_at` before creating new one
    - Ensure active count never exceeds configured maximum
    - _Requirements: 7.1, 7.2_

  - [ ]* 2.6 Write property test: FIFO Eviction Policy (Property 8)
    - **Property 8: FIFO Eviction Policy**
    - For any sequence of CreateViewer calls exceeding max, verify oldest viewer is evicted and count never exceeds max
    - Minimum 100 iterations
    - **Validates: Requirements 7.2**

- [x] 3. Checkpoint — Verify ViewerManager builds and tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. ViewerWindow — Win32 window with WebView2 controller
  - [x] 4.1 Create `RJ2XCL/Common/ViewerWindow.h` and `RJ2XCL/Common/ViewerWindow.cc`
    - Register Win32 window class with `WindowProc` static callback
    - Create modeless window owned by Excel HWND (`WS_OVERLAPPEDWINDOW`, `WS_EX_TOOLWINDOW`)
    - Default size 800×600, positioned adjacent to Excel window (right side)
    - Store `this` pointer via `SetWindowLongPtr(hwnd, GWLP_USERDATA, ...)`
    - Implement `Show()`, `Hide()`, `Resize()`, `SetTitle()`, `GetHwnd()`
    - _Requirements: 2.1, 2.2, 2.7_

  - [x] 4.2 Integrate WebView2 controller into ViewerWindow
    - Call `CreateCoreWebView2Controller` with the ViewerWindow HWND
    - Implement `NavigateToString(html)` for content < 2 MB
    - Implement `NavigateToFile(file_path)` using `Navigate(file:// URI)` for content ≥ 2 MB
    - Handle `OnSize()` to adjust `ICoreWebView2Controller` bounds via `put_Bounds`
    - _Requirements: 3.3, 3.4_

  - [x] 4.3 Implement window title format and parent window tracking
    - Set title bar to `"[Language] — [Title]"` format
    - Handle `WM_SIZE` from parent (Excel) — hide on minimize, show on restore
    - Implement `OnParentMinimize()` and `OnParentRestore()`
    - Handle close button: destroy controller, release COM, notify ViewerManager
    - _Requirements: 2.3, 2.4, 2.5, 2.6_

  - [ ]* 4.4 Write property test: Window Title Format (Property 10)
    - **Property 10: Window Title Format**
    - For any language ∈ {"R", "Julia", "Python"} and any non-empty title, verify title bar equals `L + " — " + T`
    - Minimum 100 iterations
    - **Validates: Requirements 2.5**

- [x] 5. ContentPipeline — route HTML to viewer or fallback
  - [x] 5.1 Create `RJ2XCL/Common/ContentPipeline.h` and `RJ2XCL/Common/ContentPipeline.cc`
    - Implement `RouteHtmlContent(html, language, title, application_dispatch)` — check `ViewerManager::IsAvailable()`, route to viewer or fallback
    - Implement size-based routing: `content.size() < 2 * 1024 * 1024` → `NavigateToString`, else temp file + `Navigate(file://)`
    - Implement `FallbackHyperlink()` — save HTML file + return HYPERLINK formula (existing behavior)
    - Implement `IsHtmlFile(file_path)` — check `.html`/`.htm` extension (case-insensitive)
    - Implement `ReadHtmlFile(file_path)` — read file content as string
    - Return cell value in format `"📊 [Title] (viewer-[N])"` on success
    - Handle empty/null HTML: log WARNING, don't create viewer
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 9.1, 9.2, 9.6_

  - [ ]* 5.2 Write property test: Size-Based Routing Threshold (Property 2)
    - **Property 2: Size-Based Routing Threshold**
    - For any HTML content string, verify routing decision: < 2,097,152 bytes → NavigateToString, ≥ 2,097,152 bytes → temp file
    - Minimum 100 iterations with random string sizes (0 bytes – 4 MB)
    - **Validates: Requirements 3.3, 3.4**

  - [ ]* 5.3 Write property test: Content Type Detection (Property 3)
    - **Property 3: Content Type Detection**
    - For any string: ends with `.html`/`.htm` → file path; starts with `<!DOCTYPE`/`<html` → inline HTML; otherwise → file path
    - Minimum 100 iterations
    - **Validates: Requirements 5.2, 5.3**

  - [ ]* 5.4 Write property test: Cell Value Format (Property 11)
    - **Property 11: Cell Value Format**
    - For any non-empty title and viewer ID "viewer-[N]", verify cell return equals `"📊 " + T + " (" + viewer_id + ")"`
    - Minimum 100 iterations
    - **Validates: Requirements 9.6**

  - [x] 5.5 Integrate ContentPipeline with existing GraphicsHandler
    - Modify `GraphicsHandler` to detect `html_content` field in Protobuf `CallResponse`
    - Delegate HTML content to `ContentPipeline::RouteHtmlContent()`
    - Support R `htmlwidgets::saveWidget` pattern (detect HTML file output)
    - Support Python `rj2xcl_plotly_export` (detect HTML file output)
    - Support Julia MIME display system (`text/html` MIME type from `MIMEData`)
    - _Requirements: 3.1, 3.2, 3.7, 9.3, 9.4, 9.5_

- [x] 6. Checkpoint — Verify ContentPipeline integration and tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Protobuf HtmlContent round-trip validation
  - [ ]* 7.1 Write property test: HtmlContent Protobuf Round-Trip (Property 1)
    - **Property 1: HtmlContent Protobuf Round-Trip**
    - For any valid HtmlContent message (random HTML, title, source_language, mime_type), serialize to wire format and deserialize — verify identical field values
    - Minimum 100 iterations
    - **Validates: Requirements 3.1**

- [x] 8. PostMessageBridge — bidirectional JS↔C++ communication
  - [x] 8.1 Create `RJ2XCL/Common/PostMessageBridge.h` and `RJ2XCL/Common/PostMessageBridge.cc`
    - Implement `OnWebMessageReceived(viewer_id, json_message, application_dispatch)` — parse JSON via `json11::Json::parse`
    - Implement `HandleWriteCell(payload, application_dispatch)` — extract sheet, cell, value; write to Excel cell
    - Implement `HandleNotify(payload, application_dispatch)` — display message in Excel status bar
    - Discard invalid JSON or unrecognized actions with WARNING log
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

  - [x] 8.2 Inject JavaScript bridge into ViewerWindow
    - In `ViewerWindow`, call `AddScriptToExecuteOnDocumentCreated` to inject `window.rj2xcl.sendToExcel(data)` bridge
    - Register `WebMessageReceived` event handler on `ICoreWebView2` to route messages to `PostMessageBridge`
    - Implement `PostWebMessage(json)` on ViewerWindow calling `PostWebMessageAsJson`
    - Wire `ViewerManager::SendToViewer(viewer_id, json_message)` to the correct ViewerWindow
    - _Requirements: 4.1, 4.6_

  - [ ]* 8.3 Write property test: PostMessage JSON Parsing (Property 4)
    - **Property 4: PostMessage JSON Parsing**
    - For any valid JSON-serializable object with an `action` field, verify PostMessageBridge parses correctly and extracts the action without data loss
    - Minimum 100 iterations
    - **Validates: Requirements 4.2**

  - [ ]* 8.4 Write property test: Invalid Message Handling (Property 5)
    - **Property 5: Invalid Message Handling**
    - For any invalid JSON string or valid JSON with unrecognized action, verify message is discarded, WARNING logged, Excel state unchanged
    - Minimum 100 iterations
    - **Validates: Requirements 4.5**

- [x] 9. Security policy — navigation filtering and DevTools control
  - [x] 9.1 Implement navigation filter in ViewerWindow
    - In `ViewerWindow::SetupNavigationFilter()`, register `NavigationStarting` event handler
    - Allow only `about:blank` and `file://` URIs within the configured User_Data_Folder
    - Cancel all other navigation attempts and log blocked URI at WARNING level
    - _Requirements: 6.1, 6.2_

  - [x] 9.2 Apply security settings to WebView2 controller
    - Call `put_AreDevToolsEnabled(FALSE)` by default
    - Call `put_AreDefaultContextMenusEnabled(FALSE)`
    - Call `put_IsStatusBarEnabled(FALSE)`
    - Call `put_IsBuiltInErrorPageEnabled(FALSE)`
    - Call `put_IsScriptEnabled(TRUE)` to preserve JavaScript interactivity
    - Allow `data:` and `blob:` URIs for Plotly image export and D3.js SVG generation
    - Read `WebView2.security.devToolsEnabled` from ConfigService; if true, enable DevTools
    - _Requirements: 6.3, 6.4, 6.5, 6.6, 6.7, 11.1, 11.5_

  - [ ]* 9.3 Write property test: Navigation URI Filtering (Property 6)
    - **Property 6: Navigation URI Filtering**
    - For any URI string, verify: allow if `about:blank` or `file://` within User_Data_Folder; block all others
    - Minimum 100 iterations with random URI strings
    - **Validates: Requirements 6.2**

- [x] 10. Excel function registration — =RJ2XCL.VIEW, VIEWER.CLOSE, VIEWER.LIST
  - [x] 10.1 Register `=RJ2XCL.VIEW(content_or_path)` worksheet function
    - Add function descriptor to `MapFunctions()` in `rj2xcl.cc`
    - Implement handler: detect file path (`.html`/`.htm` suffix) vs inline HTML (`<!DOCTYPE`/`<html` prefix)
    - For file paths: read file content via `ContentPipeline::ReadHtmlFile()`, then route to viewer
    - For inline HTML: route directly to `ViewerManager::CreateViewer()`
    - Return viewer ID string on success, error string if unavailable
    - _Requirements: 5.1, 5.2, 5.3, 5.6_

  - [x] 10.2 Register `=RJ2XCL.VIEWER.CLOSE(viewer_id)` and `=RJ2XCL.VIEWER.LIST()` functions
    - `VIEWER.CLOSE`: call `ViewerManager::CloseViewer(viewer_id)`, return "OK" on success
    - `VIEWER.LIST`: call `ViewerManager::ListViewers()`, return comma-separated string of active IDs
    - Add function descriptors to `MapFunctions()`
    - _Requirements: 5.4, 5.5_

- [x] 11. Checkpoint — Verify Excel functions, security, and communication work end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Configuration integration — WebView2 settings in ConfigService
  - [x] 12.1 Add WebView2 configuration getters to ConfigService
    - Add `IsWebView2Enabled()` — read `WebView2.enabled` (default true)
    - Add `GetMaxViewers()` — read `WebView2.maxViewers`, validate range 1–16, clamp with WARNING log
    - Add `GetMaxMemoryMB()` — read `WebView2.maxMemoryMB`, validate range 128–2048, clamp with WARNING log
    - Add `GetWebView2UserDataFolder()` — read `WebView2.userDataFolder`, default `%RJ2XCL_HOME%/webview2-data`
    - Add `GetDefaultViewerWidth()` — read `WebView2.defaultWidth`, validate range 400–3840, clamp
    - Add `GetDefaultViewerHeight()` — read `WebView2.defaultHeight`, validate range 300–2160, clamp
    - Add `IsDevToolsEnabled()` — read `WebView2.security.devToolsEnabled` (default false)
    - Log WARNING when values are out of range with key name, provided value, and clamped value
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 12.2 Wire ConfigService getters into ViewerManager and ViewerWindow
    - `ViewerManager::Initialize()` — check `IsWebView2Enabled()` before runtime detection
    - Use `GetMaxViewers()` for eviction threshold
    - Use `GetMaxMemoryMB()` for memory pressure monitoring
    - Use `GetWebView2UserDataFolder()` for environment creation
    - Use `GetDefaultViewerWidth()`/`GetDefaultViewerHeight()` for initial window size
    - Use `IsDevToolsEnabled()` in `ViewerWindow::ApplySecurityPolicy()`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 12.3 Write property test: Configuration Integer Clamping (Property 9)
    - **Property 9: Configuration Integer Clamping**
    - For any integer V, verify: `maxViewers` clamped to [1, 16], `maxMemoryMB` clamped to [128, 2048], using `clamp(V, lo, hi) == max(lo, min(hi, V))`
    - Minimum 100 iterations with random integers (INT_MIN – INT_MAX)
    - **Validates: Requirements 10.3, 10.4**

- [x] 13. Memory management and performance
  - [x] 13.1 Implement memory pressure monitoring in ViewerManager
    - Track `content_size_bytes` per viewer in `ViewerEntry`
    - Implement `ProcessMemoryPressure()` — when total exceeds `maxMemoryMB`, evict oldest viewer
    - Log navigation duration in milliseconds at DEBUG level on `NavigationCompleted`
    - Handle controller creation failure: return error "Viewer creation failed — too many active viewers or insufficient memory", log at ERROR level
    - Verify COM reference count reaches zero on viewer close; log WARNING if not
    - _Requirements: 8.2, 8.4, 8.5, 8.6_

  - [x] 13.2 Implement temporary file cleanup
    - Delete temp files in `NavigationCompleted` event handler
    - Log WARNING if deletion fails (non-fatal)
    - _Requirements: 3.5_

- [x] 14. PresentationBuilder — reveal.js presentation composition
  - [x] 14.1 Create `RJ2XCL/Common/PresentationBuilder.h` and `RJ2XCL/Common/PresentationBuilder.cc`
    - Implement constructor with title, generate unique presentation ID
    - Implement `AddTextSlide(markdown_content)` — store as TEXT type slide
    - Implement `AddViewerSlide(viewer_id)` — capture current HTML from ViewerWindow via `ViewerManager::CaptureViewerContent()`
    - Implement `AddHtmlSlide(html_content)` — store as HTML type slide
    - Implement `GetId()` and `GetSlideCount()`
    - _Requirements: 12.1, 12.2_

  - [x] 14.2 Implement `Build()` and reveal.js HTML generation
    - Implement `GenerateRevealHtml()` — compose slides in order, embed reveal.js CSS+JS inline as string constants
    - Implement `EmbedAssets(html)` — convert referenced images/fonts to base64 data URIs
    - Implement `Base64Encode(data)` utility
    - Write output to `output_path`; if empty, generate filename as `presentation_[sanitized_title]_[YYYYMMDD_HHMMSS].html` in User_Data_Folder
    - On success, open the generated file in a ViewerWindow for preview and return absolute file path
    - Handle errors: skip missing viewer slides with WARNING, return error string on write failure, generate empty slide HTML for empty presentations
    - _Requirements: 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_

  - [ ]* 14.3 Write property test: Presentation Slide Ordering (Property 12)
    - **Property 12: Presentation Slide Ordering**
    - For any sequence of AddSlide calls with types {"text", "viewer", "html"} and arbitrary content, verify slides appear in exact order added and content is preserved
    - Minimum 100 iterations
    - **Validates: Requirements 12.2**

  - [ ]* 14.4 Write property test: Default Presentation Filename Format (Property 13)
    - **Property 13: Default Presentation Filename Format**
    - For any title string, when output_path is empty, verify filename matches `presentation_[sanitized_T]_\d{8}_\d{6}\.html`
    - Minimum 100 iterations
    - **Validates: Requirements 12.8**

- [x] 15. Register presentation Excel functions
  - [x] 15.1 Register `=RJ2XCL.PRESENTATION.NEW`, `ADD.SLIDE`, and `BUILD` functions
    - `=RJ2XCL.PRESENTATION.NEW(title)` — create PresentationBuilder, return presentation ID
    - `=RJ2XCL.PRESENTATION.ADD.SLIDE(presentation_id, content, slide_type)` — delegate to PresentationBuilder based on slide_type ("text", "viewer", "html")
    - `=RJ2XCL.PRESENTATION.BUILD(presentation_id, output_path)` — call `Build()`, return file path
    - Add function descriptors to `MapFunctions()`
    - _Requirements: 12.1, 12.2, 12.3, 12.7_

- [x] 16. Wire ViewerManager into engine lifecycle
  - [x] 16.1 Integrate ViewerManager with RJ2XCL_Engine Init/Close
    - Call `ViewerManager::Instance().Initialize()` from `RJ2XCL_Engine::Init()` after ConfigService initialization
    - Call `ViewerManager::Instance().Shutdown()` from `xlAutoClose`
    - Add `#include "ViewerManager.h"` to `rj2xcl.h`
    - _Requirements: 1.1, 7.4, 8.1_

- [ ] 17. Test infrastructure setup
  - [ ] 17.1 Create test CMake configuration and mock headers
    - Create `RJ2XCL/tests/webview2/` directory with `CMakeLists.txt`
    - Add rapidcheck via FetchContent (or continue with `std::mt19937` pattern if rapidcheck integration is complex)
    - Create mock headers: `mock_webview2.h` (mock `ICoreWebView2*` interfaces), `mock_win32.h` (mock Win32 API calls)
    - Add new test sources to the test build
    - _Requirements: Design — Testing Strategy section_

  - [ ]* 17.2 Write unit tests for ViewerManager, ContentPipeline, PostMessageBridge
    - Test runtime detection mock (available/not available)
    - Test environment creation mock (success/failure with HRESULT codes)
    - Test `IsAvailable()` combinations
    - Test error messages returned to cells
    - Test empty HTML handling (empty/null/whitespace)
    - Test fallback behavior when ViewerManager unavailable
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 3.6, 9.2_

  - [ ]* 17.3 Write unit tests for PresentationBuilder
    - Test build with mixed slide types (text, viewer, html)
    - Test missing viewer ID handling (skip slide with WARNING)
    - Test empty presentation (generate HTML with empty slide)
    - Test write failure error handling
    - _Requirements: 12.2, 12.3, 12.7, 12.8_

- [x] 18. Final checkpoint — Full build and all tests pass (Requirements 1–12)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. PlutoManager — Pluto.jl server lifecycle management
  - [x] 19.1 Create `RJ2XCL/Common/PlutoManager.h` and `RJ2XCL/Common/PlutoManager.cc`
    - Implement singleton pattern (`Instance()`) consistent with ViewerManager and ConfigService
    - Define `State` enum: `STOPPED`, `STARTING`, `RUNNING`
    - Implement `Initialize()`: resolve Julia path via `DiscoveryService::FindJulia()`, read `Pluto.port` from ConfigService (default 1234, range 1024–65535, clamp with WARNING)
    - Implement `Shutdown()`: terminate Pluto process if `started_by_this_session_` is true, use `TerminateProcess` if process doesn't respond within 5 seconds
    - Implement `GetConfiguredPort()` returning the validated port
    - Implement `IsRunning()` and `WasStartedByThisSession()` accessors
    - _Requirements: 13.1, 13.6, 13.8_

  - [x] 19.2 Implement `StartPluto()` with port probe and process launch
    - Implement `ProbePort(port)`: attempt HTTP connection to `localhost:[port]` to detect if Pluto is already running
    - If port is already in use: log INFO "Pluto server already running on port [port]", set `started_by_this_session_ = false`, set state to `RUNNING`, reuse existing server
    - If port is available: build Julia command `julia --project=@pluto -e "import Pluto; Pluto.run(host=\"127.0.0.1\", port=[port], launch_browser=false, auto_reload_from_file=true)"`
    - Launch process via `CreateProcess`, store `pluto_process_handle_` and `pluto_process_id_`
    - Set state to `STARTING`
    - Implement `WaitForReady(timeout_ms=30000)`: poll HTTP probe every 500ms until success or timeout
    - On success: set state to `RUNNING`, return "Pluto started on port [port]"
    - On timeout: terminate process, set state to `STOPPED`, log ERROR, return "Pluto server failed to start — check Julia installation"
    - If Julia not found: log ERROR, return error string without attempting launch
    - _Requirements: 13.1, 13.2, 13.5, 13.9_

  - [x] 19.3 Implement `StopPluto()` and `GetStatus()`
    - `StopPluto()`: terminate Pluto process, close associated ViewerWindow via `ViewerManager::CloseViewer(pluto_viewer_id_)`, set state to `STOPPED`, return "Pluto stopped"
    - `GetStatus()`: return "running", "stopped", or "starting" based on current `state_` (protected by `state_mutex_`)
    - Handle unexpected process termination: monitor process handle, update state to `STOPPED` if process exits unexpectedly
    - _Requirements: 13.7, 13.10_

  - [x] 19.4 Integrate PlutoManager with ViewerManager for notebook display
    - After successful `StartPluto()`, call `ViewerManager::CreateViewer()` with URL `http://localhost:[port]`
    - Store returned `pluto_viewer_id_` for later cleanup
    - Implement `OpenNotebook(notebook_path)`: construct URL `http://localhost:[port]/open?path=[encoded_path]` and navigate existing Pluto viewer
    - _Requirements: 13.3, 13.5_

  - [x] 19.5 Register `=RJ2XCL.PLUTO.START()`, `=RJ2XCL.PLUTO.STOP()`, and `=RJ2XCL.PLUTO.STATUS()` Excel functions
    - Add function descriptors to `MapFunctions()` in `rj2xcl.cc`
    - `PLUTO.START`: call `PlutoManager::Instance().StartPluto()`, return result string
    - `PLUTO.STOP`: call `PlutoManager::Instance().StopPluto()`, return result string
    - `PLUTO.STATUS`: call `PlutoManager::Instance().GetStatus()`, return status string
    - _Requirements: 13.1, 13.7, 13.10_

  - [x] 19.6 Add Pluto port configuration to ConfigService
    - Add `GetPlutoPort()` getter: read `Pluto.port` from `rj2xcl-config.json`, validate range 1024–65535, clamp with WARNING log
    - Wire into `PlutoManager::Initialize()`
    - _Requirements: 13.6_

  - [ ]* 19.7 Write property test: Pluto Status State Machine (Property 15)
    - **Property 15: Pluto Status State Machine Consistency**
    - For any sequence of `StartPluto()` and `StopPluto()` operations, verify `GetStatus()` always returns one of exactly three strings: "running", "stopped", or "starting"
    - After successful `StartPluto()`, status SHALL be "running"; after successful `StopPluto()`, status SHALL be "stopped"
    - Use mock process launch to simulate success/failure/timeout scenarios
    - Minimum 100 iterations
    - **Validates: Requirements 13.10**

  - [ ]* 19.8 Write property test: Pluto Port Clamping (Property 16)
    - **Property 16: Pluto Port Configuration Clamping**
    - For any integer value V provided for `Pluto.port`, verify ConfigService returns: V if 1024 ≤ V ≤ 65535, 1024 if V < 1024, 65535 if V > 65535
    - Formally: `clamp(V, 1024, 65535) == max(1024, min(65535, V))`
    - Minimum 100 iterations with random integers (INT_MIN – INT_MAX)
    - **Validates: Requirements 13.6**

  - [ ]* 19.9 Write unit tests for PlutoManager
    - Test start with mock process launch → verify state transitions (STOPPED → STARTING → RUNNING)
    - Test start when port already in use → verify reuse behavior and INFO log
    - Test stop → verify process termination and state transition to STOPPED
    - Test 30-second timeout → verify error string and process cleanup
    - Test Julia not found → verify error string without process launch
    - Test shutdown on xlAutoClose → verify process termination only if started by this session
    - _Requirements: 13.1, 13.2, 13.7, 13.8, 13.9_

- [x] 20. RCall.jl integration — mixed Julia+R pipelines
  - [x] 20.1 Extend `startup.jl` with RCall.jl conditional loading
    - Add `_rcall_available` and `_rcall_status_reason` module-level refs
    - Implement `_init_rcall()`: check `ENV["R_HOME"]`, conditionally `using RCall; RCall.Rinit()`
    - On success: set `_rcall_available[] = true`, log "RCall.jl initialized — R bridge available"
    - On failure: set `_rcall_status_reason[]` with error details, log WARNING "R not found — RCall.jl disabled; R-dependent notebooks will not function"
    - Call `_init_rcall()` at end of `startup.jl` loading
    - _Requirements: 14.1, 14.2_

  - [x] 20.2 Set `R_HOME` in ControlJulia.exe based on DiscoveryService
    - In ControlJulia.exe initialization (before Julia runtime starts), call `DiscoveryService::FindR()`
    - If R is found: set `ENV["R_HOME"]` to the discovered R installation path
    - If R is not found: do not set `R_HOME` (RCall.jl will detect absence and skip loading)
    - _Requirements: 14.1, 14.2_

  - [x] 20.3 Implement `rcall_status()` and `pipeline_regression()` Julia functions
    - `rcall_status()`: return "available" when `_rcall_available[] == true`, or "unavailable: [reason]" otherwise
    - `pipeline_regression(data, params)`: Julia preprocessing → `@rput` data → `R"lm(formula, data=df)"` → `@rget` coefficients → return
    - Error handling: catch `RCall.REvalError`, format combined R error + Julia stack trace, rethrow as Julia error
    - Guard pipeline functions with `_rcall_available[]` check, error if not available
    - _Requirements: 14.3, 14.4, 14.5, 14.6, 14.7_

  - [x] 20.4 Register `=J.rcall_status()` and `=J.pipeline_*()` Excel functions
    - Add function descriptors to `MapFunctions()` for Julia pipeline functions
    - `=J.rcall_status()`: invoke `rcall_status()` via ControlJulia.exe Named Pipe
    - `=J.pipeline_regression(data, params)`: invoke `pipeline_regression()` via ControlJulia.exe Named Pipe
    - _Requirements: 14.3, 14.7_

  - [ ]* 20.5 Write property test: RCall Error Formatting (Property 17)
    - **Property 17: RCall Error Message Formatting**
    - For any R error message string E and Julia stack trace, verify the formatted error string contains both the original R error text E (untruncated) and a Julia stack trace marker
    - Minimum 100 iterations with random error strings
    - **Validates: Requirements 14.6**

  - [ ]* 20.6 Write unit tests for RCall.jl integration
    - Test R detected → verify `_init_rcall()` loads RCall.jl and sets `_rcall_available = true`
    - Test R not detected → verify WARNING log and `_rcall_available = false`
    - Test `rcall_status()` returns correct strings in both states
    - Test pipeline execution with mock RCall → verify Julia+R data flow
    - Test pipeline when RCall unavailable → verify error message
    - _Requirements: 14.1, 14.2, 14.6, 14.7_

- [x] 21. Checkpoint — Verify PlutoManager and RCall integration build and tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 22. NotebookLibrary — preconfigured notebook management
  - [x] 22.1 Create `RJ2XCL/Common/NotebookLibrary.h` and `RJ2XCL/Common/NotebookLibrary.cc`
    - Define `NotebookInfo` struct: name, filename, full_path, category, is_custom, requires_rcall
    - Define static `PRECONFIGURED_NOTEBOOKS` registry with 13 entries (7 R via RCall, 5 Julia native, 1 Mixed R+Julia)
    - Implement `GetNotebooksDirectory()`, `GetCustomDirectory()`, `GetExportsDirectory()` returning paths under `%RJ2XCL_HOME%/notebooks/`
    - Implement `RequiresRCall(filename)` static method: return true for notebooks in "R via RCall" or "Mixed R+Julia" categories
    - _Requirements: 15.1, 15.2_

  - [x] 22.2 Create 13 preconfigured notebook `.jl` template files
    - Create Pluto.jl notebook templates for each of the 13 notebooks: `stats_regression.jl`, `lme4_mixed_models.jl`, `survival_analysis.jl`, `forecast_arima.jl`, `psych_factor_analysis.jl`, `plm_panel_econometrics.jl`, `rstanarm_bayes.jl`, `jump_optimization.jl`, `diffeq_simulation.jl`, `turing_hierarchical.jl`, `montecarlo_risk.jl`, `linalg_decomposition.jl`, `multilang_pipeline.jl`
    - Each file follows Pluto.jl notebook format with cell markers (`# ╔═╡`)
    - Include placeholder code and documentation cells appropriate to each analysis category
    - _Requirements: 15.1, 15.2_

  - [x] 22.3 Implement `ListNotebooks()` and `FindNotebook()`
    - `ListNotebooks()`: scan `notebooks/` directory for `.jl` files, merge with `notebooks/custom/` directory, return vector of `NotebookInfo`
    - `ListNotebooksFormatted()`: return comma-separated string with custom notebooks suffixed with " [custom]"
    - `FindNotebook(name)`: search preconfigured registry first, then custom directory; return `NotebookInfo` or throw if not found
    - `NotebookExists(name)`: return true if notebook found in either directory
    - Handle missing directories gracefully: log WARNING, return empty list
    - _Requirements: 15.4, 15.6, 15.7_

  - [x] 22.4 Implement custom notebook directory management
    - Ensure `notebooks/custom/` directory exists on first access (create if missing)
    - Ensure `notebooks/exports/` directory exists on first access (create if missing)
    - When Pluto saves a modified preconfigured notebook, it writes to `notebooks/custom/` preserving the original template
    - _Requirements: 15.5_

  - [x] 22.5 Register `=RJ2XCL.NOTEBOOK.OPEN(notebook_name)` and `=RJ2XCL.NOTEBOOK.LIST()` Excel functions
    - Add function descriptors to `MapFunctions()` in `rj2xcl.cc`
    - `NOTEBOOK.OPEN`: find notebook via `NotebookLibrary::FindNotebook()`, start Pluto if not running via `PlutoManager::StartPluto()`, open notebook via `PlutoManager::OpenNotebook(path)`, return viewer ID
    - If notebook not found: return "Notebook not found: [notebook_name]"
    - If notebook requires RCall and RCall unavailable: return viewer ID with suffix " (R unavailable)"
    - `NOTEBOOK.LIST`: call `NotebookLibrary::ListNotebooksFormatted()`, return comma-separated string
    - _Requirements: 15.3, 15.4, 15.6, 15.7, 15.8_

  - [ ]* 22.6 Write property test: Notebook Listing Completeness (Property 18)
    - **Property 18: Notebook Listing Completeness**
    - For any set of `.jl` files in `notebooks/` and any set of `.jl` files in `notebooks/custom/`, verify `ListNotebooksFormatted()` contains every filename from both directories
    - Custom notebook names SHALL be suffixed with " [custom]"
    - No notebook SHALL be omitted or duplicated
    - Use mock filesystem to generate random sets of `.jl` filenames
    - Minimum 100 iterations
    - **Validates: Requirements 15.4, 15.6**

  - [ ]* 22.7 Write unit tests for NotebookLibrary
    - Test `ListNotebooks()` returns all 13 preconfigured notebooks
    - Test `FindNotebook()` with valid name → verify correct `NotebookInfo`
    - Test `FindNotebook()` with invalid name → verify error string "Notebook not found: [name]"
    - Test custom notebook listing with "[custom]" suffix
    - Test `RequiresRCall()` classification for each category
    - Test missing directories → verify WARNING log and empty list
    - Test notebook open when RCall unavailable → verify " (R unavailable)" suffix
    - _Requirements: 15.1, 15.2, 15.4, 15.6, 15.7, 15.8_

- [x] 23. NotebookExporter — analysis reproducibility
  - [x] 23.1 Create `RJ2XCL/Common/NotebookExporter.h` and `RJ2XCL/Common/NotebookExporter.cc`
    - Define `AnalysisContext` struct: function_name, language, code, input_data_json, parameters_json, result_json, executed_at
    - Implement `CaptureAnalysis(context)`: store context in `last_analysis_` (protected by `analysis_mutex_`)
    - Implement `HasAnalysis()`: return true if `last_analysis_` has been set in current session
    - _Requirements: 16.1, 16.2_

  - [x] 23.2 Implement `ExportNotebook(title)` with Pluto format generation
    - Implement `GeneratePlutoNotebook(title, context)`: compose valid Pluto.jl notebook with cell markers (`# ╔═╡ UUID`)
    - Include cells for: title/metadata markdown, input data (JSON → Julia literal), parameters (JSON → Dict), analysis code, expected results
    - Implement `PlutoCellMarker()`, `PlutoHeader()`, `PlutoDataCell()`, `PlutoCodeCell()`, `PlutoResultCell()` helpers
    - Write output to `%RJ2XCL_HOME%/notebooks/exports/[filename]`
    - Return absolute file path on success
    - If no analysis captured: return "No analysis to export — execute an analysis first"
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

  - [x] 23.3 Implement filename sanitization and generation
    - `SanitizeTitle(title)`: replace non-alphanumeric characters with underscores, handle empty title as "untitled"
    - `GenerateFilename(title)`: produce `[sanitized_title]_[YYYYMMDD_HHMMSS].jl` format
    - _Requirements: 16.7_

  - [x] 23.4 Register `=RJ2XCL.NOTEBOOK.EXPORT(title)` Excel function
    - Add function descriptor to `MapFunctions()` in `rj2xcl.cc`
    - Call `NotebookExporter::ExportNotebook(title)`, return file path or error string
    - _Requirements: 16.1, 16.5, 16.6_

  - [x] 23.5 Wire analysis capture into Content Pipeline
    - After a Julia or R pipeline function executes successfully, call `NotebookExporter::CaptureAnalysis()` with the execution context
    - Capture function name, language, source code, input data, parameters, and results
    - _Requirements: 16.2_

  - [ ]* 23.6 Write property test: Export Validity (Property 19)
    - **Property 19: Notebook Export Validity**
    - For any valid `AnalysisContext` (with non-empty function name, code, input data, parameters, and results), verify the generated notebook: (a) contains Pluto cell markers (`# ╔═╡`), (b) includes input data, (c) includes parameters, (d) includes analysis code, (e) includes results, and (f) is a valid plain-text `.jl` file
    - Use random generators for AnalysisContext fields
    - Minimum 100 iterations
    - **Validates: Requirements 16.2, 16.3, 16.4**

  - [ ]* 23.7 Write property test: Filename Sanitization (Property 20)
    - **Property 20: Export Filename Sanitization**
    - For any title string T, verify `GenerateFilename()` produces a filename matching `[a-zA-Z0-9_]+_\d{8}_\d{6}\.jl` where all non-alphanumeric characters in T are replaced with underscores
    - Test with Unicode, special characters, empty strings, very long strings
    - Minimum 100 iterations
    - **Validates: Requirements 16.7**

  - [ ]* 23.8 Write unit tests for NotebookExporter
    - Test export with valid analysis context → verify `.jl` file content and Pluto format
    - Test export without prior analysis → verify error string "No analysis to export — execute an analysis first"
    - Test empty title → verify "untitled" default
    - Test filename sanitization with special characters
    - Test write failure to exports directory → verify error handling
    - _Requirements: 16.1, 16.2, 16.5, 16.6, 16.7_

- [x] 24. Python formal deprecation
  - [x] 24.1 Update CMakeLists.txt with `RJ2XCL_ENABLE_PYTHON` flag
    - Add `option(RJ2XCL_ENABLE_PYTHON "Build ControlPython.exe (deprecated)" OFF)` to root `CMakeLists.txt`
    - Wrap `add_subdirectory(ControlPython)` inside `if(RJ2XCL_ENABLE_PYTHON)` guard
    - ControlPython source code remains in repository, only excluded from default build
    - _Requirements: 17.3_

  - [x] 24.2 Update default `rj2xcl-languages.json` to R + Julia only
    - Remove Python entry from default `rj2xcl-languages.json`, keeping only R and Julia
    - When Python is not listed: XLL SHALL NOT start ControlPython_Process and SHALL NOT register `=PY.*` functions
    - _Requirements: 17.1, 17.2_

  - [x] 24.3 Add deprecation error message for `=PY.*` functions
    - When a user calls any `=PY.*` function and Python is not configured, return: "Python is deprecated — use Julia (=J.*) functions instead. See documentation for migration guide."
    - _Requirements: 17.7_

  - [x] 24.4 Guard Python-specific Content Pipeline logic with `#ifdef RJ2XCL_ENABLE_PYTHON`
    - Wrap `rj2xcl_plotly_export` detection logic in `ContentPipeline` behind `#ifdef RJ2XCL_ENABLE_PYTHON`
    - Preserve full backward compatibility when flag is enabled
    - _Requirements: 17.5_

  - [x] 24.5 Preserve backward compatibility for manual Python re-enablement
    - Verify that adding Python back to `rj2xcl-languages.json` manually causes XLL to load and start ControlPython_Process as before
    - Verify that building with `-DRJ2XCL_ENABLE_PYTHON=ON` includes ControlPython.exe in the build
    - _Requirements: 17.4_

  - [ ]* 24.6 Write unit tests for Python deprecation
    - Test `=PY.*` function call without Python → verify deprecation error string
    - Test Python added back to `rj2xcl-languages.json` → verify ControlPython loads normally
    - Test build with `RJ2XCL_ENABLE_PYTHON=ON` → verify ControlPython.exe is built
    - Test Content Pipeline with Python disabled → verify `rj2xcl_plotly_export` logic is excluded
    - _Requirements: 17.2, 17.4, 17.5, 17.7_

- [x] 25. Extended security, integration wiring, and final checkpoint
  - [x] 25.1 Extend navigation filter for Advanced Mode (localhost:port)
    - Modify `ViewerWindow::SetupNavigationFilter()` to accept `advanced_mode_active` and `pluto_port` parameters
    - When Advanced Mode is active: allow `http://localhost:[port]` and subpaths in addition to existing `about:blank` and `file://` rules
    - When Advanced Mode is NOT active: only allow `about:blank` and `file://` (existing behavior unchanged)
    - Implement `IsLocalhostUri(uri, port)` helper for URI validation
    - _Requirements: 13.4_

  - [ ]* 25.2 Write property test: Extended Navigation URI Filtering (Property 14)
    - **Property 14: Extended Navigation URI Filtering (Advanced Mode)**
    - For any URI string, when Advanced_Mode is active with port P: allow if (a) `about:blank`, (b) `file://` within User_Data_Folder, or (c) `http://localhost:P` or subpath; block all others
    - When Advanced_Mode is NOT active: only (a) and (b) apply
    - Minimum 100 iterations with random URIs and random ports
    - **Validates: Requirements 13.4, 6.2**

  - [x] 25.3 Wire PlutoManager into engine lifecycle
    - Call `PlutoManager::Instance().Initialize()` from `RJ2XCL_Engine::Init()` after ViewerManager initialization
    - Call `PlutoManager::Instance().Shutdown()` from `xlAutoClose` before ViewerManager shutdown
    - Ensure Pluto process is terminated when Excel closes if started by this session
    - _Requirements: 13.8_

  - [x] 25.4 Update test infrastructure for new components
    - Add `pluto_manager_test.cc`, `notebook_library_test.cc`, `notebook_exporter_test.cc`, `rcall_error_test.cc`, `python_deprecation_test.cc` to `tests/webview2/CMakeLists.txt`
    - Add mock headers: `mock_process.h` (for PlutoManager process launch/terminate), `mock_filesystem.h` (for NotebookLibrary/Exporter file operations)
    - Verify all 20 property tests compile and link
    - _Requirements: Design — Testing Strategy section_

  - [x] 25.5 Final checkpoint — Full build with all 20 property tests and all unit tests pass
    - Ensure all tests pass (properties 1–20 and all unit tests), ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document (20 properties total)
- Unit tests validate specific examples and edge cases
- The project uses GTest with custom `std::mt19937` random generators for PBT (see `reliability_pbt.cc` for the established pattern)
- All new source files go in `RJ2XCL/Common/` consistent with existing architecture
- WebView2 COM interfaces require STA thread — all WebView2 operations must be marshalled to the dedicated STA thread
- Tasks 1–18 cover Requirements 1–12 (WebView2 core viewer, content pipeline, presentations)
- Tasks 19–25 cover Requirements 13–17 (Pluto.jl Advanced Mode, RCall.jl, NotebookLibrary, NotebookExporter, Python deprecation)
