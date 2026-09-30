# Implementation Plan: NEVEN Studio Standalone

## Overview

Implementation proceeds in four layers, each building on the previous:

1. **Protobuf + framing foundation** (`pipe_client.py`) — the lowest layer that everything else depends on.
2. **Standalone Launcher** (`start_studio.py`) — process management, PID file, CLI, signal handling.
3. **HTTP Server extensions** (`neven_http_server.py`) — six new endpoints wired to `PipeClient`.
4. **Run Script UI tab** (`taskpane.html` / `taskpane.js` / `taskpane.css`) — browser-side wiring.

All Python code targets the existing CPython environment in `C:\NEVEN\`. Tests use `pytest` + `hypothesis`. No C++ code is modified.

---

## Tasks

- [x] 1. Set up `pipe_client.py` — exceptions, framing, and read loop
  - [x] 1.1 Create `C:\NEVEN\taskpane\pipe_client.py` with exception hierarchy and `_frame` / `_unframe` helpers
    - Define `PipeClientError`, `PipeTimeoutError`, `PipeProtocolError` (all subclass `Exception`).
    - Implement `_frame(msg: CallResponse) -> bytes`: `struct.pack('<i', len(payload)) + payload`.
    - Implement `_unframe(data: bytes) -> CallResponse`: reads 4-byte LE prefix, enforces `MAX_RESPONSE_BYTES = 256 * 1024`, calls `msg.ParseFromString(payload)`.
    - Import `variable_pb2` (already generated from `variable.proto`).
    - _Requirements: 2.2, 2.3, 2.4, 10.1, 10.2, 10.5, 10.6_

  - [x] 1.2 Write property test for framing round-trip — code messages (Property 1)
    - **Property 1: Framing round-trip for code messages**
    - **Validates: Requirements 2.2, 2.4, 2.10, 10.1, 10.2, 10.3**
    - Use `@given(lines=st.lists(st.text(max_size=1000), min_size=1, max_size=500))` with `@settings(max_examples=200)`.
    - Build `CallResponse{code=Code{line=lines}}`, call `_frame`, call `_unframe`, assert `list(recovered.code.line) == lines`.

  - [x] 1.3 Write property test for framing round-trip — function_call messages (Property 2)
    - **Property 2: Framing round-trip for function_call messages**
    - **Validates: Requirements 2.3, 2.4, 10.4**
    - Use `@given(fname=st.text(min_size=1, max_size=100), args=st.lists(scalar_variable_strategy(), max_size=20))`.
    - Build `CallResponse{function_call=CompositeFunctionCall{function=fname, arguments=args}}`, frame, unframe, assert equality.

- [x] 2. Implement `PipeClient` class — connection, send/receive, Variable conversion
  - [x] 2.1 Add `PipeClient` class to `pipe_client.py` with `connect`, `close`, and `_read_exact`
    - Constructor: `__init__(self, pipe_name: str, timeout_ms: int = 60_000)`.
    - `connect()`: calls `win32file.CreateFile` (or `ctypes` Win32 fallback) on `pipe_name`; stores handle; raises `OSError` on failure.
    - `close()`: calls `win32api.CloseHandle`; sets handle to `None`; is idempotent.
    - `_read_exact(n: int) -> bytes`: reads exactly `n` bytes from the pipe handle, enforcing `timeout_ms` via a `threading.Thread` join.
    - Context manager: `__enter__` returns `self`; `__exit__` calls `self.close()`.
    - _Requirements: 2.1, 2.7, 2.8, 2.9, 9.4_

  - [x] 2.2 Implement `send_code`, `send_function_call`, and `_read_response` in `PipeClient`
    - `send_code(lines, wait=True)`: builds `CallResponse{code=Code{line=lines}}`, calls `_frame`, writes to pipe, calls `_read_response`, returns converted `Variable`.
    - `send_function_call(function, arguments, target)`: builds `CallResponse{function_call=CompositeFunctionCall{...}}`, same pipeline.
    - `_read_response()`: calls `_read_exact(4)` for header, unpacks length, enforces `MAX_RESPONSE_BYTES`, calls `_read_exact(length)`, deserializes `CallResponse`.
    - Handles `CallResponse.result` oneof `err` → raises `PipeClientError(err.message)`.
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 2.3 Implement Variable → Python type conversion helper
    - `variable_to_python(var: Variable) -> any`: dispatches on `var.WhichOneof("value")`.
    - Mapping: `integer→int`, `real→float`, `str→str`, `boolean→bool`, `nil/missing→None`, `arr→dict(columns, rows)`, `html_content→dict(html, title)`.
    - `err` case: raises `PipeClientError(var.err.message)`.
    - _Requirements: 2.5, 3.5, 3.6, 3.7_

  - [x] 2.4 Write property test for Variable-to-Python mapping (Property 5)
    - **Property 5: Variable-to-JSON mapping is correct for all scalar types**
    - **Validates: Requirements 2.5, 3.5, 3.6, 3.7**
    - Use `@given(var=variable_strategy())` drawing from all scalar oneofs.
    - Call `variable_to_python(var)`, assert returned Python type and value match the Protobuf field.

  - [x] 2.5 Write unit tests for `PipeClient` error paths
    - Test: `err` field in `CallResponse` → `PipeClientError` raised (Req 2.6).
    - Test: mock pipe that never responds → `PipeTimeoutError` after `timeout_ms` (Req 2.7).
    - Test: response length > 256 KB → `PipeProtocolError` (Req 10.5).
    - Test: unparseable payload → `PipeProtocolError` (Req 10.6).
    - Test: `with PipeClient(...) as c:` calls `close()` on exit (Req 2.9).

- [x] 3. Checkpoint — pipe_client.py complete
  - Ensure all tests in tasks 1 and 2 pass. Verify `_frame`/`_unframe` are importable and round-trip correctly with a live `variable_pb2` import. Ask the user if questions arise.

- [x] 4. Implement `start_studio.py` — CLI, config, process launch, and pipe readiness
  - [x] 4.1 Create `C:\NEVEN\taskpane\start_studio.py` with CLI argument parsing and config loading
    - Use `argparse` to accept `--config PATH`, `--port INT`, `--languages LIST`, `--no-browser`.
    - `load_config(path)`: loads `neven-config.json`; returns dict with defaults when file missing or `Standalone` section absent. Log warning to stderr if file not found.
    - `resolve_languages(config, arg)`: returns set from `--languages` if provided, else from config `languages` section; validates against `{r, python, julia}`.
    - `find_exe(config, lang)`: constructs path from `controlDir`; returns path or `None` if binary absent (log warning, skip language).
    - _Requirements: 1.1, 1.2, 9.1, 9.2, 9.3, 9.6_

  - [x] 4.2 Implement process launch, pipe readiness polling, and PID file
    - `launch_control(exe, lang, config)`: calls `subprocess.Popen([exe, '-p', pipe_name], env={**os.environ, 'RJ2XCL_HOME': install_dir})`.
    - `wait_for_pipes(processes, timeout=10)`: polls `CreateFile` on each `\\.\pipe\neven_{lang}` every 100 ms up to 10 s; logs warning and removes from `processes` on timeout.
    - `write_pid_file(config, processes, launcher_pid)`: writes JSON `{launcher: N, r: N, ...}` to `<NEVEN_HOME>/studio.pid`; registers `remove_pid_file` via `atexit`.
    - Non-Windows: skip pipe polling; log `[NEVEN Launcher] INFO: Non-Windows platform — scripting engines not started`.
    - _Requirements: 1.3, 1.4, 1.5, 8.5, 8.6, 9.3_

  - [x] 4.3 Implement startup sequence wiring, URL print, browser open, and signal handling
    - `start_server(config, pipe_clients)`: calls existing `start_server()` from `neven_http_server.py` with injected `pipe_client_factory`; returns `(thread, port)`.
    - Print `http://localhost:{port}/taskpane.html` to stdout (Req 1.7).
    - Call `webbrowser.open(url)` unless `--no-browser` (Req 1.8).
    - `monitor_processes(processes)`: background thread; logs `[NEVEN Launcher] ERROR: <name> exited with code <N>` on unexpected exits (Req 1.10).
    - `wait_for_signal()`: blocks on `signal.signal(SIGINT, ...)` / `signal.signal(SIGTERM, ...)`.
    - `shutdown(processes)`: calls `proc.terminate()` then `proc.wait(timeout=5)` for each; falls back to `proc.kill()`.
    - _Requirements: 1.6, 1.7, 1.8, 1.9, 1.10_

  - [x] 4.4 Write property test for enabled languages controlling process launch (Property 3)
    - **Property 3: Enabled languages control exactly which processes are launched**
    - **Validates: Requirements 1.2, 1.3, 1.4, 7.1**
    - Use `@given(enabled=st.frozensets(st.sampled_from(['r', 'python', 'julia'])))` with `@settings(max_examples=50)`.
    - Mock `subprocess.Popen`; call `run_launcher_dry(config, mock_subprocess)`.
    - Assert `{p.language for p in launched} == enabled`.
    - Assert each launched process has `-p \\.\pipe\neven_{lang}` in args and `RJ2XCL_HOME` in env.

  - [x] 4.5 Write property test for SIGINT/SIGTERM terminating all processes (Property 4)
    - **Property 4: SIGINT/SIGTERM terminates all launched processes**
    - **Validates: Requirements 1.9**
    - Use `@given(enabled=st.frozensets(st.sampled_from(['r', 'python', 'julia']), min_size=1))`.
    - Mock processes; send SIGINT to launcher; assert `terminate()` called on every mock process.

  - [x] 4.6 Write property test for `--languages` CLI override (Property 10)
    - **Property 10: `--languages` CLI argument exactly controls which engines start**
    - **Validates: Requirements 9.6**
    - Use `@given(cli_langs=st.frozensets(st.sampled_from(['r', 'python', 'julia']), min_size=1))`.
    - Build config with a different languages set; run launcher with `--languages <cli_langs>`; assert only `cli_langs` processes are launched.

  - [x] 4.7 Write unit tests for Launcher edge cases
    - Test: `--config` present → uses that path; absent → uses `C:\NEVEN\neven-config.json` (Req 1.1).
    - Test: `--port` overrides config port (Req 9.2).
    - Test: missing binary → logs warning, skips language (Req 9.3).
    - Test: `--no-browser` → `webbrowser.open` not called (Req 1.8).
    - Test: stdout URL is printed (Req 1.7).
    - Test: PID file written on start, removed on exit (Req 8.6).
    - Test: Non-Windows → processes not started, script endpoints return 503 (Req 4.7).

- [x] 5. Checkpoint — start_studio.py complete
  - Ensure all tasks 4.x tests pass. Verify `python start_studio.py --help` prints correct usage. Ask the user if questions arise.

- [x] 6. Extend `neven_http_server.py` — script execution endpoints
  - [x] 6.1 Add `pipe_client_factory` injection to `NEVENHandler` / server configuration
    - Extend the server's configuration object to accept `pipe_client_factory: dict[str, Callable[[], PipeClient]]`.
    - Add a `_get_pipe_client(lang) -> PipeClient` helper that calls the factory or raises `KeyError` for unregistered languages.
    - Wire factory into the `do_POST` and `do_GET` dispatch tables.
    - _Requirements: 9.5_

  - [x] 6.2 Implement `POST /api/r`, `POST /api/python`, `POST /api/julia` endpoints
    - Parse JSON body; validate `code` field (non-empty after strip) → 400 if missing/blank.
    - Apply existing rate limiter and `maxPayloadMB` check before routing.
    - Retrieve `PipeClient` for language; send code with optional `timeout_ms`; convert `Variable` via `variable_to_python`.
    - Response dispatch: scalar → `{status, type, result, console}`, html → `{status, type, html, title, console}`, array → `{status, type, columns, rows, console}`.
    - Error mapping: `PipeClientError` → 200 error, `PipeTimeoutError` → 408, engine absent → 503.
    - One reconnect attempt (`client.close(); client.connect()`) on broken pipe before returning 503.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 8.4_

  - [x] 6.3 Write property test for empty/whitespace code rejection (Property 6)
    - **Property 6: Empty or whitespace-only code is rejected with HTTP 400**
    - **Validates: Requirements 3.3**
    - Use `@given(code=st.text(alphabet=st.characters(whitespace=True), max_size=200))`.
    - Filter to strings where `code.strip() == ""`.
    - POST to `/api/r`, `/api/python`, `/api/julia`; assert HTTP 400 and `{"status":"error","message":"Missing 'code' field"}`.

  - [x] 6.4 Write property test for rate limiter and payload size limit (Property 7)
    - **Property 7: Rate limiter and payload size limit apply to all Script endpoints**
    - **Validates: Requirements 3.11, 3.12**
    - Use `@given(endpoint=st.sampled_from(['/api/r', '/api/python', '/api/julia']))`.
    - Sub-test A: send `rate_limit + 1` rapid requests; assert last returns HTTP 429.
    - Sub-test B: send body of size `maxPayloadMB × 1024² + 1`; assert HTTP 413.

  - [x] 6.5 Write unit tests for script endpoint error paths
    - Test: `/api/r` with no PipeClient registered → 503 (Req 3.10).
    - Test: `PipeClientError` → 200 with `status: error` (Req 3.8).
    - Test: `PipeTimeoutError` → 408 (Req 3.9).
    - Test: broken pipe → one reconnect attempt before 503 (Req 8.4).

- [x] 7. Extend `neven_http_server.py` — engines, functions, and rpivot endpoints
  - [x] 7.1 Implement `GET /api/engines` with `_probe_pipe` helper
    - `_probe_pipe(pipe_name: str) -> bool`: on Windows calls `win32file.CreateFile` and immediately closes; returns `True` on success, `False` on any exception. On non-Windows returns `False`.
    - `GET /api/engines` handler: calls `_probe_pipe` for `neven_r`, `neven_python`, `neven_julia`; returns `{"r": bool, "python": bool, "julia": bool}`.
    - _Requirements: 8.1, 8.2_

  - [x] 7.2 Implement `GET /api/functions`
    - For each language in `{r, python, julia}`: if PipeClient registered, call `send_function_call("list-functions", [], target=system)`; convert result to list of `{name, description, arguments}` dicts.
    - If language not registered or `PipeClientError` raised → return `[]` for that language.
    - Return `{"status": "ok", "languages": {"r": [...], "python": [...], "julia": [...]}}`.
    - _Requirements: 7.3, 7.4_

  - [x] 7.3 Implement `POST /api/rpivot`
    - Parse optional `max_rows` (default 10,000).
    - Probe R engine → 503 if unavailable.
    - `SELECT * FROM dataset LIMIT <max_rows>` via DuckDB → 400 if table missing.
    - Convert result rows to JSON string; build R code string (requireNamespace checks, rpivotTable, htmlwidgets::saveWidget, readLines).
    - Send via `PipeClient("neven_r").send_code(lines)`; return `{"status":"ok","type":"html","html":"..."}`.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x] 7.4 Write property test for engine status accuracy (Property 8)
    - **Property 8: Engine status accurately reflects pipe availability**
    - **Validates: Requirements 8.1**
    - Use `@given(available=st.frozensets(st.sampled_from(['r', 'python', 'julia'])))`.
    - Mock `_probe_pipe` to return `True` iff language in `available`.
    - Assert `GET /api/engines` returns `{lang: (lang in available) for lang in [...]}`.

  - [x] 7.5 Write property test for `/api/functions` empty lists for stopped engines (Property 9)
    - **Property 9: `/api/functions` returns lists for running engines, empty for stopped ones**
    - **Validates: Requirements 7.3, 7.4**
    - Use `@given(running=st.frozensets(st.sampled_from(['r', 'python', 'julia'])))`.
    - Register PipeClient mocks only for `running` languages.
    - Assert each language in `running` returns a list (possibly `[]`); each language not in `running` returns `[]`.

  - [x] 7.6 Write unit tests for rpivot and engines edge cases
    - Test: `/api/rpivot` with R engine down → 503 (Req 5.5).
    - Test: `/api/rpivot` with no dataset → 400 (Req 5.7).
    - Test: `/api/functions` with no engine running → all empty lists (Req 7.4).
    - Test: Non-Windows `_probe_pipe` always returns `False`.

- [x] 8. Checkpoint — neven_http_server.py extensions complete
  - Ensure all tasks 6.x and 7.x tests pass. Verify that existing endpoints (`/api/load_file`, `/api/query`, etc.) still pass their original tests unchanged. Ask the user if questions arise.

- [x] 9. Add Run Script tab to `taskpane.html` and `taskpane.css`
  - [x] 9.1 Add fourth tab button and tab content panel to `taskpane.html`
    - Add `<div class="tab" data-tab="run-script">Run Script</div>` to the existing `.tabs` div.
    - Add the full `<div class="tab-content" id="run-script">` panel (language selector, engine-dot spans, `<textarea id="script-input">`, Execute button, Open RPivot button, `#functions-panel` details element, output card with iframe / table / scalar / error / console divs).
    - No other structural changes to existing tabs.
    - _Requirements: 6.1, 6.2, 6.3, 6.10, 6.12_

  - [x] 9.2 Add CSS rules to `taskpane.css` for engine dots
    - Add `.engine-dot`, `.engine-dot.available`, `.engine-dot.unavailable` rules using existing CSS variables `--success` and `--error`.
    - _Requirements: 8.3_

- [x] 10. Implement Run Script tab JavaScript in `taskpane.js`
  - [x] 10.1 Add `initRunScriptTab`, `SNIPPETS`, and tab activation hook
  - [x] 10.2 Implement `refreshEngineStatus` and `onRunScriptTabActivated`
  - [x] 10.3 Implement `runScript` with spinner and error handling
  - [x] 10.4 Implement `renderScriptResult` output dispatch
  - [x] 10.5 Implement `openRPivot`, `loadAvailableFunctions`, and `filterFunctions`

- [x] 11. Update `neven-config.json` — add `Standalone` section

- [x] 12. Final checkpoint — full integration

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they validate correctness properties and edge cases but are not required for the feature to function.
- `variable_pb2.py` is assumed to be pre-generated from `variable.proto` and present at `C:\NEVEN\taskpane\variable_pb2.py`.
- `pywin32` is assumed installed in the production Python environment; `ctypes` fallback is a secondary option.
- Property tests (tasks 1.2, 1.3, 2.4, 4.4, 4.5, 4.6, 6.3, 6.4, 7.4, 7.5) each correspond to a numbered Correctness Property in the design document and use `hypothesis` with `@settings(max_examples=200)`.
- The `pipe_client_factory` injection pattern (Req 9.5) is essential for all HTTP server property tests — no real Control processes are needed.
- Tasks 9.x touch only HTML/CSS/JS; they have no Python dependencies and can be parallelized with tasks 6.x–7.x once task 2 is complete.
- Existing NEVEN GTest suite in `tests/` is not modified.

---

## Integration Test Results (2026-07-29)

All three scripting engines verified working end-to-end in NEVEN Studio Standalone:

| Engine | Status | Response |
|--------|--------|---------|
| Python | ✅ | `True` (import sys; sys.version) |
| R      | ✅ | `"R version 4.4.1 (2024-06-14 ucrt)"` |
| Julia  | ✅ | `"1.12.6"` (string(VERSION)) |

### Integration bugs found and fixed during testing

| # | Bug | Root cause | Fix |
|---|-----|-----------|-----|
| 1 | Pipe name doble-prefijo | `Pipe::Start` en C++ agrega `\\.\pipe\` automáticamente; launcher pasaba path completo | `_pipe_arg_for()` — pasa solo nombre corto (e.g. `neven_python`) |
| 2 | R home con espacios se truncaba | `C:\Program Files\R\R-4.4.1` se partía en argv parser de ControlR | `_short_path()` convierte a 8.3 (`C:\PROGRA~1\R\R-44~1.1`) |
| 3 | libR.dll / libjulia.dll no encontradas | PATH del subproceso no incluía el directorio bin del runtime | `launch_control` prepend runtime bin al PATH del subproceso |
| 4 | Factory dict copiado en vez de referenciado | `start_server` creaba un nuevo dict `factory` en vez de pasar `pipe_factory` por referencia | `server_config["pipe_client_factory"]` apunta al mismo objeto que el background thread actualiza |
| 5 | Múltiples servidores en el mismo puerto | Launcher previo no era detectado | Mutex de Windows `Global\NEVEN_Studio_Launcher` |
| 6 | Servidor bloqueado esperando Julia sin sysimage | Julia JIT frío tarda 10+ min | Servidor arranca inmediatamente; engines se conectan en background thread (300s timeout) |

### Julia sysimage

La sysimage `C:\NEVEN\neven_julia.dll` (467.6 MB) fue generada con:

```cmd
set NEVEN_HOME=C:\NEVEN\
julia f:\ANTIGRAVITY\2026\NEVEN\NEVEN\scripts\build-julia-sysimage.jl
```

Con sysimage: Julia arranca en ~3 segundos. Sin sysimage: 5-15 minutos de JIT frío.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3"] },
    { "id": 3, "tasks": ["2.4", "2.5", "4.1", "9.1", "9.2"] },
    { "id": 4, "tasks": ["4.2", "6.1", "10.1"] },
    { "id": 5, "tasks": ["4.3", "6.2", "7.1", "7.2", "7.3", "10.2"] },
    { "id": 6, "tasks": ["4.4", "4.5", "4.6", "4.7", "6.3", "6.4", "6.5", "7.4", "7.5", "7.6", "10.3", "10.4"] },
    { "id": 7, "tasks": ["10.5"] }
  ]
}
```
