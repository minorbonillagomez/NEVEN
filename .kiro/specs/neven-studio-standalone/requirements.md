# Requirements Document

## Introduction

NEVEN Studio Standalone is a browser-based data analysis environment that runs independently of Microsoft Excel. It reuses the existing Control*.exe scripting processes (ControlR.exe, ControlJulia.exe, ControlPython.exe) and the existing neven_http_server.py/DuckDB stack. A new launcher (`start_studio.py`) starts all processes, a Python Named Pipe client connects to the Control*.exe processes directly (bypassing the XLL), and new HTTP endpoints expose script execution to the existing taskpane.html UI, which gains a "Run Script" tab and an RPivot integration button.

Excel becomes an optional data source rather than a hard dependency: users can load CSV, Parquet, and JSON files directly into DuckDB without opening Excel at all. On any OS that runs Python (Windows, macOS, Linux), `python start_studio.py` opens the full Studio experience in the browser.

---

## Glossary

- **Studio**: The browser-based NEVEN Studio UI served at `http://localhost:5555/taskpane.html`.
- **Launcher**: `start_studio.py` — the standalone entry point that starts the Control processes and the HTTP server.
- **Pipe_Client**: The Python module (`pipe_client.py`) that opens a Named Pipe connection to a Control*.exe process and exchanges framed Protobuf messages.
- **Pipe_Server**: A running Control*.exe process (ControlR.exe, ControlJulia.exe, or ControlPython.exe) that listens on its Named Pipe and executes code.
- **Frame**: A 4-byte little-endian signed int32 length prefix followed by a serialized Protobuf `CallResponse` payload, as implemented in `MessageUtilities::Frame` / `MessageUtilities::Unframe`.
- **CallResponse**: The top-level Protobuf message in `variable.proto` (package `RJ2XCLBuffers`) used for both requests and responses on the Named Pipe.
- **Pipe_Name**: The Windows Named Pipe identifier. Follows the pattern `\\.\pipe\neven_{language}` (e.g., `\\.\pipe\neven_r`, `\\.\pipe\neven_python`, `\\.\pipe\neven_julia`).
- **HTTP_Server**: `neven_http_server.py` — the existing Python HTTP server running on `localhost:5555`.
- **DuckDB**: The in-memory analytical database already embedded in the HTTP_Server, used as the primary data layer.
- **Script_Endpoint**: One of the new REST endpoints `/api/r`, `/api/python`, or `/api/julia` added to the HTTP_Server.
- **RPivot**: The R `rpivotTable` htmlwidget that produces a self-contained HTML pivot table. Executed via ControlR.exe.
- **Run_Script_Tab**: The new "Run Script" tab added to `taskpane.html`, containing a code editor, language selector, Execute button, and output area.
- **Functions_Dir**: The directory `C:\NEVEN\functions\` where users place `.R`, `.py`, and `.jl` files for auto-loading.
- **NEVEN_HOME**: The environment variable `RJ2XCL_HOME` (production value: `C:\NEVEN\`) that points to the NEVEN installation directory.
- **Startup_Script**: The per-language script executed by a Control process at init (`startup.r`, `startup.py`, `startup.jl`).

---

## Requirements

### Requirement 1: Standalone Launcher

**User Story:** As a data analyst, I want to run `python start_studio.py` from a terminal to start the full NEVEN Studio environment without opening Microsoft Excel, so that I can use NEVEN on machines without Excel or in headless server scenarios.

#### Acceptance Criteria

1. THE Launcher SHALL accept a `--config` command-line argument specifying the path to `neven-config.json`; when omitted, THE Launcher SHALL use the default path `C:\NEVEN\neven-config.json`.
2. WHEN the Launcher starts, THE Launcher SHALL read `neven-config.json` and determine which Control processes (R, Python, Julia) are enabled via the `languages` section of the config.
3. WHEN the Launcher starts, THE Launcher SHALL launch each enabled Control process (ControlR.exe, ControlJulia.exe, ControlPython.exe) as a subprocess, passing the appropriate `-p <Pipe_Name>` argument.
4. WHEN a Control process is launched, THE Launcher SHALL set the `RJ2XCL_HOME` environment variable for that subprocess to the NEVEN installation directory.
5. WHEN the Launcher starts, THE Launcher SHALL wait up to 10 seconds for each enabled Control process to create its Named Pipe before starting the HTTP_Server; IF a Control process does not create its pipe within 10 seconds, THEN THE Launcher SHALL log a warning and continue without that language.
6. AFTER all Control processes are ready, THE Launcher SHALL start the HTTP_Server on `localhost:5555` (with fallback to `5556` as implemented in the existing server).
7. WHEN all services are running, THE Launcher SHALL print the Studio URL (`http://localhost:<port>/taskpane.html`) to stdout.
8. THE Launcher SHALL accept a `--no-browser` flag; WHERE that flag is absent, THE Launcher SHALL open the Studio URL in the system default browser using `webbrowser.open`.
9. WHEN the Launcher receives SIGINT or SIGTERM, THE Launcher SHALL terminate all Control subprocesses before exiting.
10. IF a Control process exits unexpectedly after startup, THEN THE Launcher SHALL log the exit code and the process name to stderr.

---

### Requirement 2: Named Pipe Client

**User Story:** As a developer, I want a Python module that can connect to any Control*.exe process via its Named Pipe and send code for execution, so that the HTTP_Server can invoke R, Python, and Julia without going through the XLL.

#### Acceptance Criteria

1. THE Pipe_Client SHALL open a Named Pipe connection to a Pipe_Server by calling `CreateFile` on the Pipe_Name (Windows) using the `pywin32` or `ctypes` Win32 API.
2. WHEN sending a code execution request, THE Pipe_Client SHALL serialize a `CallResponse` Protobuf message with the `code` field set to a `Code` message containing the script lines, then prepend the serialized payload with a 4-byte little-endian signed int32 length prefix (matching `MessageUtilities::Frame`).
3. WHEN sending a function call request, THE Pipe_Client SHALL serialize a `CallResponse` Protobuf message with the `function_call` field set to a `CompositeFunctionCall` message and frame it identically to the code request.
4. AFTER sending a framed message, THE Pipe_Client SHALL read the response by first reading 4 bytes to determine the payload length, then reading exactly that many bytes, then deserializing the `CallResponse` Protobuf message (matching `MessageUtilities::Unframe`).
5. WHEN the Pipe_Server returns a `result` field in the response, THE Pipe_Client SHALL return the result value converted to a Python-native type (str, int, float, bool, list, or dict as appropriate to the Protobuf `Variable` oneof).
6. WHEN the Pipe_Server returns an `err` field in the response, THE Pipe_Client SHALL raise a `PipeClientError` exception containing the error string.
7. THE Pipe_Client SHALL include a `timeout_ms` parameter (default: 60,000 ms); IF a response is not received within `timeout_ms`, THEN THE Pipe_Client SHALL raise a `PipeTimeoutError` exception and close the pipe connection.
8. THE Pipe_Client SHALL expose a `connect(pipe_name)` method, a `send_code(lines: list[str], wait: bool = True) -> Variable` method, a `send_function_call(function: str, arguments: list, target: CallTarget = language) -> Variable` method, and a `close()` method.
9. THE Pipe_Client SHALL be usable as a context manager (`with PipeClient(pipe_name) as client:`), closing the connection automatically on exit.
10. FOR ALL valid `CallResponse` messages serialized by the Pipe_Client, deserializing the framed bytes using `MessageUtilities::Unframe` in the Pipe_Server SHALL produce an equivalent `CallResponse` message (round-trip framing property).

---

### Requirement 3: Script Execution HTTP Endpoints

**User Story:** As a Studio user, I want to send R, Python, or Julia code from the browser and receive text results or rendered HTML, so that I can run analysis scripts interactively without writing to files.

#### Acceptance Criteria

1. THE HTTP_Server SHALL expose three POST endpoints: `/api/r`, `/api/python`, and `/api/julia`.
2. WHEN a POST request is received at a Script_Endpoint, THE HTTP_Server SHALL expect a JSON body with a required `code` field (string) and an optional `timeout_ms` field (integer, default 60,000).
3. WHEN the `code` field is absent or empty, THE HTTP_Server SHALL return HTTP 400 with `{"status": "error", "message": "Missing 'code' field"}`.
4. WHEN a Script_Endpoint receives valid code, THE HTTP_Server SHALL forward the code to the corresponding Pipe_Client and await the response.
5. WHEN the Pipe_Server returns a scalar result (string, number, boolean), THE HTTP_Server SHALL return HTTP 200 with `{"status": "ok", "type": "<type>", "result": <value>, "console": "<stdout_text>"}`.
6. WHEN the Pipe_Server returns an `HtmlContent` result, THE HTTP_Server SHALL return HTTP 200 with `{"status": "ok", "type": "html", "html": "<complete_html_string>", "title": "<title>"}`.
7. WHEN the Pipe_Server returns an `Array` result, THE HTTP_Server SHALL serialize the array as `{"status": "ok", "type": "array", "columns": [...], "rows": [[...], ...]}` compatible with the existing DuckDB query response format.
8. WHEN the Pipe_Server returns an error or the Pipe_Client raises `PipeClientError`, THE HTTP_Server SHALL return HTTP 200 with `{"status": "error", "message": "<error_text>"}`.
9. WHEN the Pipe_Client raises `PipeTimeoutError`, THE HTTP_Server SHALL return HTTP 408 with `{"status": "error", "message": "Script execution timed out"}`.
10. WHEN the corresponding Control process is not running, THE HTTP_Server SHALL return HTTP 503 with `{"status": "error", "message": "<language> engine not available"}`.
11. THE HTTP_Server SHALL apply the existing rate limiter to Script_Endpoint requests.
12. THE HTTP_Server SHALL apply the existing payload size limit (`maxPayloadMB`) to Script_Endpoint request bodies.

---

### Requirement 4: Direct File Loading (Excel-Free Data Ingestion)

**User Story:** As a data analyst, I want to load CSV, Parquet, and JSON files directly into the Studio without opening Excel, so that I can analyze local data files independently.

#### Acceptance Criteria

1. THE HTTP_Server SHALL already support loading files via `POST /api/load_file` with a `path` field — this existing endpoint SHALL continue to work unchanged for CSV, Parquet, JSON, JSONL, and TSV formats.
2. WHEN the Studio is opened in standalone mode (no Excel), THE Run_Script_Tab SHALL display a file picker section in the Data Studio tab allowing the user to enter a file path and load it.
3. WHEN a file is loaded successfully via `/api/load_file`, THE HTTP_Server SHALL return the `columns`, `types`, and `rows_loaded` fields as already implemented.
4. WHEN a file is loaded in standalone mode, THE DuckDB instance SHALL make the data available under the table name `dataset` for subsequent SQL queries and GROUP BY operations without any modification to the existing query endpoints.
5. IF the provided file path does not exist or is not readable, THEN THE HTTP_Server SHALL return HTTP 200 with `{"status": "error", "message": "File not found: <path>"}`.
6. THE HTTP_Server SHALL accept file paths using both forward slashes and backslashes on Windows.
7. WHERE the Studio is running on macOS or Linux, THE Launcher SHALL not attempt to start Control*.exe processes and SHALL start only the HTTP_Server, with all Script_Endpoints returning HTTP 503.

---

### Requirement 5: RPivot Integration

**User Story:** As a data analyst, I want to click a button in Studio to open an RPivot interactive pivot table on the currently loaded dataset, so that I can explore data visually without writing R code manually.

#### Acceptance Criteria

1. THE HTTP_Server SHALL expose a POST endpoint `/api/rpivot` that accepts an optional `max_rows` integer field (default: 10,000).
2. WHEN `/api/rpivot` is called, THE HTTP_Server SHALL query `SELECT * FROM dataset LIMIT <max_rows>` via DuckDB and convert the result to a JSON array of objects.
3. WHEN the dataset query succeeds, THE HTTP_Server SHALL forward R code to ControlR.exe via the Pipe_Client that: (a) installs `rpivotTable` if absent, (b) loads the JSON data into an R data frame, (c) calls `rpivotTable::rpivotTable()` to generate an htmlwidget, (d) uses `htmlwidgets::saveWidget` to serialize the widget to a self-contained HTML string, and (e) returns the HTML string as an `HtmlContent` Protobuf result.
4. WHEN ControlR.exe returns the HTML content, THE HTTP_Server SHALL return HTTP 200 with `{"status": "ok", "type": "html", "html": "<self_contained_html>"}`.
5. WHEN ControlR.exe is not running, THE HTTP_Server SHALL return HTTP 503 with `{"status": "error", "message": "R engine not available for RPivot"}`.
6. IF the `rpivotTable` or `htmlwidgets` R packages are not installed, THEN THE HTTP_Server SHALL return HTTP 200 with `{"status": "error", "message": "R packages rpivotTable and htmlwidgets are required"}`.
7. WHEN the dataset table does not exist in DuckDB, THE HTTP_Server SHALL return HTTP 400 with `{"status": "error", "message": "No dataset loaded — load data first"}`.

---

### Requirement 6: Run Script Tab in the Studio UI

**User Story:** As a Studio user, I want a "Run Script" tab in the browser UI where I can write R, Python, or Julia code, execute it, and see the result or chart, so that I have an interactive scripting environment in the browser.

#### Acceptance Criteria

1. THE Run_Script_Tab SHALL be added as a fourth tab labeled "Run Script" in `taskpane.html`, following the existing "Viewers", "SQL", and "Data Studio" tabs using the existing tab pattern.
2. THE Run_Script_Tab SHALL display a language selector with options "R", "Python", and "Julia"; THE Run_Script_Tab SHALL default to "R".
3. THE Run_Script_Tab SHALL display a multi-line code editor (`<textarea>`) pre-populated with a language-appropriate example snippet.
4. THE Run_Script_Tab SHALL display an "Execute" button; WHEN the Execute button is clicked, THE Run_Script_Tab SHALL POST the code and selected language to the corresponding Script_Endpoint (`/api/r`, `/api/python`, or `/api/julia`).
5. WHILE a script is executing, THE Run_Script_Tab SHALL display a spinner and disable the Execute button.
6. WHEN the Script_Endpoint returns `"type": "html"`, THE Run_Script_Tab SHALL render the HTML in an `<iframe>` within the output area, sized to fill the available tab height.
7. WHEN the Script_Endpoint returns `"type": "array"`, THE Run_Script_Tab SHALL render the data as an HTML table using the existing `data-table` CSS class.
8. WHEN the Script_Endpoint returns a scalar result, THE Run_Script_Tab SHALL display the result value as pre-formatted text in the output area.
9. WHEN the Script_Endpoint returns `"status": "error"`, THE Run_Script_Tab SHALL display the error message with the existing `.msg-error` CSS class.
10. THE Run_Script_Tab SHALL display an "Open RPivot" button; WHEN clicked, THE Run_Script_Tab SHALL call `/api/rpivot` and render the returned HTML in the output iframe.
11. THE Run_Script_Tab SHALL support the keyboard shortcut Ctrl+Enter to trigger execution, consistent with the existing SQL tab behavior.
12. WHEN the Script_Endpoint returns a non-empty `console` field, THE Run_Script_Tab SHALL display the console output below the main result in a separate `<pre>` element with a distinct background.

---

### Requirement 7: User Function Auto-Loading

**User Story:** As a developer, I want the Control processes started by the Launcher to auto-load my function files from `C:\NEVEN\functions\`, so that my custom R, Python, and Julia functions are available in the Studio without any extra configuration.

#### Acceptance Criteria

1. THE Launcher SHALL set the `RJ2XCL_HOME` environment variable to the NEVEN installation directory before starting each Control process, so that the existing Startup_Scripts (startup.r, startup.py, startup.jl) run and auto-load function files from `C:\NEVEN\functions\` as they already do in Excel mode.
2. WHEN ControlPython.exe is started by the Launcher, THE ControlPython process SHALL execute `startup.py`, which calls `_autoload_functions()` to load all `.py` files from Functions_Dir — this behavior is already implemented and SHALL be preserved unchanged.
3. THE HTTP_Server SHALL expose a GET endpoint `/api/functions` that returns `{"status": "ok", "languages": {"r": [...], "python": [...], "julia": [...]}}` where each list contains the function descriptors returned by the `list-functions` system call sent via the corresponding Pipe_Client.
4. WHEN a Control process is not running, THE HTTP_Server SHALL return an empty list for that language's function list rather than an error.
5. THE Run_Script_Tab SHALL display a collapsible "Available Functions" panel that calls `/api/functions` on tab activation and renders the returned function names and descriptions as a searchable list.

---

### Requirement 8: Process Lifecycle and Health Monitoring

**User Story:** As a Studio user, I want the Studio to show me which scripting engines are available and automatically handle process failures, so that I always know what I can run.

#### Acceptance Criteria

1. THE HTTP_Server SHALL expose a GET endpoint `/api/engines` that returns the running status of each Control process: `{"r": true|false, "python": true|false, "julia": true|false}`.
2. THE HTTP_Server SHALL determine engine availability by checking whether a Named Pipe connection can be opened to each Pipe_Name, without sending a full execution request.
3. THE Run_Script_Tab SHALL call `/api/engines` when the tab is first activated and display a status indicator (●) per language using green for available and red for unavailable, consistent with the existing status bar style.
4. WHEN a Script_Endpoint receives a request for a language whose Control process has died, THE HTTP_Server SHALL attempt one reconnection via the Pipe_Client before returning HTTP 503.
5. IF ControlPython.exe is started by the Launcher (and therefore starts the HTTP_Server), THE Launcher SHALL detect this and not start a second HTTP_Server instance; THE Launcher SHALL instead connect to the already-running server.
6. THE Launcher SHALL write a PID file to `<NEVEN_HOME>/studio.pid` containing the PIDs of all started processes; WHEN the Launcher exits, THE Launcher SHALL remove the PID file.

---

### Requirement 9: Configuration and Portability

**User Story:** As a developer deploying NEVEN Studio on a non-Windows machine or a custom installation path, I want the Launcher and HTTP_Server to be configurable without editing source code, so that the studio works in different environments.

#### Acceptance Criteria

1. THE Launcher SHALL read the `Standalone` section of `neven-config.json`; WHEN the section is absent, THE Launcher SHALL use defaults: `controlDir = C:\NEVEN\`, `startupDir = C:\NEVEN\startup\`, `staticDir = C:\NEVEN\taskpane\`, `functionsDir = C:\NEVEN\functions\`.
2. THE Launcher SHALL accept a `--port` command-line argument (integer) to override the HTTP server port; WHEN `--port` is absent, THE Launcher SHALL use the port configured in `neven-config.json` (default: 5555).
3. WHERE the `controlDir` path does not contain Control*.exe binaries, THE Launcher SHALL log an error per missing binary and skip that language engine.
4. THE Pipe_Client SHALL accept the Pipe_Name as a constructor argument, allowing it to connect to non-default pipe names for testing.
5. THE HTTP_Server SHALL accept a `pipe_client_factory` parameter in its configuration object, allowing the Pipe_Client implementations to be injected — this enables unit testing without real Control processes.
6. THE Launcher SHALL support a `--languages` command-line argument accepting a comma-separated list (e.g., `--languages r,python`) to start only the specified Control processes, overriding the config file.

---

### Requirement 10: Protobuf Framing Correctness

**User Story:** As a developer, I want the Python Named Pipe framing to be bit-for-bit compatible with the C++ `MessageUtilities::Frame` / `MessageUtilities::Unframe` functions, so that the Pipe_Client can communicate with any version of the Control processes without protocol errors.

#### Acceptance Criteria

1. THE Pipe_Client SHALL serialize the 4-byte length prefix as a signed 32-bit integer in native little-endian byte order, matching the `memcpy` / `reinterpret_cast<char*>(&bytes)` approach in `message_utilities.cc`.
2. THE Pipe_Client SHALL serialize the Protobuf payload using `SerializeToString()` (the binary wire format), not JSON.
3. FOR ALL `CallResponse` messages with a `code` field containing between 1 and 500 lines of up to 1,000 characters each, framing then unframing the message SHALL produce an identical `CallResponse` (round-trip property).
4. FOR ALL `CallResponse` messages with a `function_call` field containing a `function` string and between 0 and 20 `Variable` arguments of any supported scalar type (nil, integer, real, str, boolean), framing then unframing the message SHALL produce an identical `CallResponse` (round-trip property).
5. IF the Pipe_Server sends a response where the 4-byte length prefix indicates a size larger than 256 KB (the `kMaxDynamicBufferSize` constant), THEN THE Pipe_Client SHALL raise a `PipeProtocolError` with a descriptive message rather than attempting to allocate that buffer.
6. IF the Pipe_Server sends a response where the Protobuf payload cannot be deserialized into a `CallResponse` message, THEN THE Pipe_Client SHALL raise a `PipeProtocolError` rather than returning a partially populated object.
