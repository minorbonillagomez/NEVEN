# Design Document: NEVEN Studio Standalone

## Overview

NEVEN Studio Standalone decouples the existing browser-based NEVEN Studio UI from
Microsoft Excel. Instead of running inside ControlPython.exe as a daemon thread, the
Studio becomes a fully self-contained environment launched with `python start_studio.py`.

Three new Python modules are introduced:

- **`start_studio.py`** — Launcher: reads config, starts Control processes, starts the
  HTTP server, opens the browser.
- **`pipe_client.py`** — Named Pipe client: speaks the existing 4-byte-framed Protobuf
  `CallResponse` protocol directly to ControlR.exe, ControlPython.exe, and
  ControlJulia.exe.
- **`neven_http_server.py`** (extended) — Existing server gains `/api/r`, `/api/python`,
  `/api/julia`, `/api/rpivot`, `/api/engines`, and `/api/functions` endpoints, all
  wired to `pipe_client.py`.

The existing `taskpane.html` / `taskpane.js` / `taskpane.css` gain a fourth **Run
Script** tab; no other structural changes are needed.

Excel remains supported: when the server is started by ControlPython.exe in the
traditional Excel flow the new endpoints are simply inactive (no Control processes
are registered with them). On Windows, Control processes are started; on macOS/Linux,
only the HTTP server starts and all Script endpoints return HTTP 503.


---

## Architecture

```mermaid
flowchart TD
    Browser["Browser\ntaskpane.html"]
    HTTP["neven_http_server.py\nlocalhost:5555"]
    PC_R["PipeClient(neven_r)"]
    PC_PY["PipeClient(neven_python)"]
    PC_JL["PipeClient(neven_julia)"]
    CR["ControlR.exe\n\\\\.\\pipe\\neven_r"]
    CP["ControlPython.exe\n\\\\.\\pipe\\neven_python"]
    CJ["ControlJulia.exe\n\\\\.\\pipe\\neven_julia"]
    DuckDB["DuckDB in-memory"]
    Launcher["start_studio.py"]

    Launcher -->|subprocess| CR
    Launcher -->|subprocess| CP
    Launcher -->|subprocess| CJ
    Launcher -->|start_server()| HTTP
    Browser -->|REST JSON| HTTP
    HTTP -->|framed Protobuf| PC_R --> CR
    HTTP -->|framed Protobuf| PC_PY --> CP
    HTTP -->|framed Protobuf| PC_JL --> CJ
    HTTP --- DuckDB
```

### Data Flow for Script Execution

1. Browser POSTs `{ "code": "...", "timeout_ms": 60000 }` to `/api/r`.
2. `NEVENHandler` validates payload (rate limit, size limit, non-empty `code`).
3. Handler calls `PipeClient("\\\\.\pipe\\neven_r").send_code(lines)`.
4. `PipeClient` serializes a `CallResponse { code: Code { line: [...] } }`, prepends a
   4-byte LE int32 length (matching `MessageUtilities::Frame`), writes to pipe.
5. `PipeClient` reads the 4-byte response length prefix, reads exactly that many bytes,
   deserializes `CallResponse`.
6. Handler maps the `CallResponse.result` oneof variant to JSON and returns HTTP 200.


---

## Components and Interfaces

### 1. `start_studio.py` — Standalone Launcher

**Location:** `C:\NEVEN\taskpane\start_studio.py`  
**Entry point:** `python start_studio.py [--config PATH] [--port INT] [--languages LIST] [--no-browser]`

#### CLI arguments

| Argument | Default | Description |
|---|---|---|
| `--config PATH` | `C:\NEVEN\neven-config.json` | Path to config file |
| `--port INT` | from config / 5555 | HTTP server port (overrides config) |
| `--languages r,python,julia` | from config | Comma-separated subset |
| `--no-browser` | absent = open browser | Skip `webbrowser.open` |

#### Startup sequence

```
parse_args()
config = load_config(args.config)
enabled_langs = resolve_languages(config, args.languages)
processes = {}
for lang in enabled_langs:
    exe = find_exe(config, lang)       # checks controlDir
    proc = launch_control(exe, lang, config)
    processes[lang] = proc
wait_for_pipes(processes, timeout=10)  # poll \\.\pipe\neven_{lang}
thread, port = start_server(config, pipe_clients)
write_pid_file(config, processes, os.getpid())
print(f"http://localhost:{port}/taskpane.html")
if not args.no_browser: webbrowser.open(url)
monitor_processes(processes)   # background thread, logs exits
wait_for_signal()              # SIGINT / SIGTERM
shutdown(processes)
remove_pid_file(config)
```

#### Pipe readiness check

Uses `CreateFile` with `OPEN_EXISTING` on the pipe name in a polling loop (100 ms
interval, 10 s max). On non-Windows the check is skipped; `processes` is empty and
all script endpoints return 503.

#### PID file

Written to `<NEVEN_HOME>/studio.pid` as JSON:
```json
{ "launcher": 12345, "r": 12346, "python": 12347, "julia": 12348 }
```
Removed on clean exit; if present at startup it is overwritten (no lock required
because only one Launcher runs at a time per installation).


---

### 2. `pipe_client.py` — Named Pipe Client

**Location:** `C:\NEVEN\taskpane\pipe_client.py`  
**Dependencies:** `pywin32` (Windows only) or `ctypes` Win32 fallback; generated
`variable_pb2.py` (from `variable.proto`).

#### Public API

```python
class PipeClientError(Exception): pass
class PipeTimeoutError(PipeClientError): pass
class PipeProtocolError(PipeClientError): pass

class PipeClient:
    MAX_RESPONSE_BYTES = 256 * 1024  # kMaxDynamicBufferSize

    def __init__(self, pipe_name: str, timeout_ms: int = 60_000): ...

    # Context manager support
    def __enter__(self) -> "PipeClient": ...
    def __exit__(self, *_): self.close()

    def connect(self) -> None:
        """Open CreateFile on pipe_name. Raises OSError on failure."""

    def send_code(self, lines: list[str], wait: bool = True) -> "variable_pb2.Variable":
        """Build CallResponse{code=Code{line=lines}}, frame, send, receive, return Variable."""

    def send_function_call(
        self,
        function: str,
        arguments: list,
        target: int = variable_pb2.CallTarget.language
    ) -> "variable_pb2.Variable":
        """Build CallResponse{function_call=CompositeFunctionCall{...}}, frame, send, receive."""

    def close(self) -> None:
        """CloseHandle on the pipe."""
```

#### Framing (matches `MessageUtilities::Frame` exactly)

```python
import struct
import variable_pb2

def _frame(msg: variable_pb2.CallResponse) -> bytes:
    payload = msg.SerializeToString()          # binary wire format, not JSON
    length = struct.pack('<i', len(payload))   # signed 32-bit LE
    return length + payload

def _unframe(data: bytes) -> variable_pb2.CallResponse:
    if len(data) < 4:
        raise PipeProtocolError("Response too short")
    (length,) = struct.unpack('<i', data[:4])
    if length > PipeClient.MAX_RESPONSE_BYTES:
        raise PipeProtocolError(f"Response size {length} exceeds 256 KB limit")
    payload = data[4:4 + length]
    msg = variable_pb2.CallResponse()
    if not msg.ParseFromString(payload):
        raise PipeProtocolError("Failed to deserialize CallResponse")
    return msg
```

#### Read loop

```python
def _read_response(self) -> variable_pb2.CallResponse:
    # 1. Read 4-byte length prefix
    header = self._read_exact(4)
    (length,) = struct.unpack('<i', header)
    if length > self.MAX_RESPONSE_BYTES:
        raise PipeProtocolError(...)
    # 2. Read exactly 'length' bytes
    payload = self._read_exact(length)
    # 3. Deserialize
    msg = variable_pb2.CallResponse()
    if not msg.ParseFromString(payload):
        raise PipeProtocolError(...)
    return msg
```

Timeout is enforced by setting the pipe handle to overlapped I/O or by running the
read in a `threading.Thread` with `join(timeout=timeout_ms/1000)`.

#### Variable → Python type conversion

| Protobuf `Variable` oneof | Python return type |
|---|---|
| `integer` | `int` |
| `real` | `float` |
| `str` | `str` |
| `boolean` | `bool` |
| `nil` / `missing` | `None` |
| `arr` | `dict` with keys `columns`, `rows` |
| `html_content` | `dict` with keys `html`, `title` |
| `err` | raises `PipeClientError(err.message)` |


---

### 3. `neven_http_server.py` — Extended HTTP Server

All existing endpoints remain unchanged. Six new endpoints are added.

#### New POST endpoints

| Path | Description |
|---|---|
| `POST /api/r` | Execute R code via `PipeClient("neven_r")` |
| `POST /api/python` | Execute Python code via `PipeClient("neven_python")` |
| `POST /api/julia` | Execute Julia code via `PipeClient("neven_julia")` |
| `POST /api/rpivot` | Query DuckDB `dataset`, render RPivot via R |

#### New GET endpoints

| Path | Description |
|---|---|
| `GET /api/engines` | Pipe-probe each language; return `{"r": bool, ...}` |
| `GET /api/functions` | `list-functions` system call per language |

#### Script endpoint request/response contract

**Request body** (all three language endpoints share the same schema):
```json
{ "code": "1 + 1", "timeout_ms": 60000 }
```

**Success responses:**

| `Variable` oneof | HTTP | Body |
|---|---|---|
| scalar (str/int/float/bool) | 200 | `{"status":"ok","type":"<type>","result":<value>,"console":"..."}` |
| `html_content` | 200 | `{"status":"ok","type":"html","html":"...","title":"..."}` |
| `arr` | 200 | `{"status":"ok","type":"array","columns":[...],"rows":[[...],...]}` |

**Error responses:**

| Condition | HTTP | Body |
|---|---|---|
| `code` absent/empty | 400 | `{"status":"error","message":"Missing 'code' field"}` |
| `PipeClientError` | 200 | `{"status":"error","message":"<text>"}` |
| `PipeTimeoutError` | 408 | `{"status":"error","message":"Script execution timed out"}` |
| Engine not running | 503 | `{"status":"error","message":"<lang> engine not available"}` |

Rate limiter and `maxPayloadMB` check are applied in `do_POST` before routing,
consistent with existing endpoints.

#### `/api/engines` — pipe probe logic

```python
def _probe_pipe(pipe_name: str) -> bool:
    """Returns True if the named pipe exists (CreateFile succeeds)."""
    try:
        h = win32file.CreateFile(pipe_name, ...)
        win32api.CloseHandle(h)
        return True
    except:
        return False
```

On non-Windows, always returns `False` for all languages.

#### `/api/rpivot` — R pivot table generation

1. Probe R engine; return 503 if unavailable.
2. Check `dataset` table exists; return 400 if not.
3. `SELECT * FROM dataset LIMIT <max_rows>` → list of dicts → JSON string.
4. Build R code string:
   ```r
   if (!requireNamespace("rpivotTable", quietly=TRUE)) stop("rpivotTable required")
   if (!requireNamespace("htmlwidgets", quietly=TRUE)) stop("htmlwidgets required")
   library(rpivotTable); library(htmlwidgets)
   data <- jsonlite::fromJSON('<json>')
   widget <- rpivotTable(data)
   tmp <- tempfile(fileext=".html")
   htmlwidgets::saveWidget(widget, tmp, selfcontained=TRUE)
   readLines(tmp) |> paste(collapse="\n")
   ```
5. Send code via `PipeClient("neven_r").send_code(lines)`.
6. The returned `Variable` is `html_content`; forward as `{"status":"ok","type":"html","html":"..."}`.


---

### 4. `taskpane.html` / `taskpane.js` — Run Script Tab

#### HTML addition (fourth tab, after "SQL")

```html
<!-- Tab button — added to existing .tabs div -->
<div class="tab" data-tab="run-script">Run Script</div>

<!-- Tab content panel -->
<div class="tab-content" id="run-script">
  <div class="card">
    <div class="card-title">Run Script</div>
    <div class="controls">
      <label>Language:</label>
      <select id="script-lang">
        <option value="r" selected>R</option>
        <option value="python">Python</option>
        <option value="julia">Julia</option>
      </select>
      <span id="engine-status-r"  class="engine-dot" title="R">●</span>
      <span id="engine-status-python" class="engine-dot" title="Python">●</span>
      <span id="engine-status-julia"  class="engine-dot" title="Julia">●</span>
    </div>
    <textarea class="sql-editor" id="script-input" style="min-height:120px"></textarea>
    <div class="controls" style="margin-top:6px">
      <button class="btn btn-primary"   id="btn-run-script">Execute</button>
      <button class="btn btn-secondary" id="btn-open-rpivot">Open RPivot</button>
      <span   id="script-status"></span>
    </div>
  </div>

  <!-- Available Functions panel -->
  <details class="card" id="functions-panel">
    <summary class="card-title" style="cursor:pointer">Available Functions</summary>
    <input type="text" id="func-search" placeholder="Search..." style="width:100%;margin:4px 0">
    <div id="func-list"></div>
  </details>

  <!-- Output area -->
  <div class="card" id="script-output-card" style="display:none">
    <div class="card-title">Output</div>
    <iframe id="script-iframe"  style="width:100%;height:400px;display:none;border:0"></iframe>
    <div    id="script-table"   style="display:none"></div>
    <pre    id="script-scalar"  style="display:none;background:#111;padding:8px;color:#a8e600"></pre>
    <div    id="script-error"   class="msg-error" style="display:none"></div>
    <pre    id="script-console" style="display:none;background:#1a1a2e;padding:6px;font-size:10px;color:#888"></pre>
  </div>
</div>
```

#### CSS additions (to `taskpane.css`)

```css
.engine-dot { font-size: 14px; margin: 0 2px; }
.engine-dot.available   { color: var(--success); }
.engine-dot.unavailable { color: var(--error); }
```


#### JavaScript additions (to `taskpane.js`)

Key functions added in `initializeApp`:

```javascript
// Default snippets per language
const SNIPPETS = {
  r:      '# R\nsummary(dataset)\n',
  python: '# Python\nprint("hello from NEVEN")\n',
  julia:  '# Julia\nprintln("hello from NEVEN")\n'
};

// Wire up Run Script tab on activation
function initRunScriptTab() {
  document.getElementById('btn-run-script').addEventListener('click', runScript);
  document.getElementById('btn-open-rpivot').addEventListener('click', openRPivot);
  document.getElementById('script-input').addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); runScript(); }
  });
  document.getElementById('script-lang').addEventListener('change', e => {
    document.getElementById('script-input').value = SNIPPETS[e.target.value] || '';
  });
  document.getElementById('func-search').addEventListener('input', filterFunctions);
}

// Called when Run Script tab becomes active (switchTab extended)
async function onRunScriptTabActivated() {
  await refreshEngineStatus();
  await loadAvailableFunctions();
}

async function refreshEngineStatus() {
  try {
    const data = await fetch(API_BASE + '/api/engines').then(r => r.json());
    ['r', 'python', 'julia'].forEach(lang => {
      const dot = document.getElementById(`engine-status-${lang}`);
      dot.className = 'engine-dot ' + (data[lang] ? 'available' : 'unavailable');
    });
  } catch (_) {}
}

async function runScript() {
  const lang = document.getElementById('script-lang').value;
  const code = document.getElementById('script-input').value.trim();
  if (!code) return;
  setScriptBusy(true);
  try {
    const res = await apiCall(`/api/${lang}`, { code });
    renderScriptResult(res);
  } catch (e) {
    showScriptError(e.message);
  } finally {
    setScriptBusy(false);
  }
}
```

`renderScriptResult` dispatches on `res.type`:
- `"html"` → sets `script-iframe` `srcdoc`, shows iframe.
- `"array"` → calls existing `renderSQLResults`-style function, shows `script-table`.
- scalar → sets `script-scalar.textContent`, shows it.
- error → shows `script-error`.
- non-empty `res.console` → shows `script-console`.

`switchTab` is extended to call `onRunScriptTabActivated()` when `tabId === 'run-script'`.


---

## Data Models

### `neven-config.json` — new `Standalone` section

```json
{
  "Standalone": {
    "controlDir":  "C:\\NEVEN\\",
    "startupDir":  "C:\\NEVEN\\startup\\",
    "staticDir":   "C:\\NEVEN\\taskpane\\",
    "functionsDir":"C:\\NEVEN\\functions\\"
  }
}
```

All four keys are optional; the Launcher falls back to the defaults shown above when
the section or any individual key is absent.

### `studio.pid` — PID file schema

```json
{ "launcher": 12345, "r": 12346, "python": 12347, "julia": 12348 }
```

Languages that were not started are omitted from the object. Written atomically by
overwriting the file; removed on clean exit via `atexit` registration.

### Script endpoint request schema

```json
{ "code": "string (required)", "timeout_ms": 60000 }
```

### Script endpoint response schema (success)

```json
{
  "status":  "ok",
  "type":    "scalar | html | array",
  "result":  "<value>",      // scalar only
  "html":    "<string>",     // html only
  "title":   "<string>",     // html only
  "columns": ["..."],        // array only
  "rows":    [["..."]],      // array only
  "console": "<stdout text>" // all types (may be empty string)
}
```

### `/api/functions` response schema

```json
{
  "status": "ok",
  "languages": {
    "r":      [{ "name": "...", "description": "...", "arguments": [...] }],
    "python": [{ "name": "...", "description": "...", "arguments": [...] }],
    "julia":  [{ "name": "...", "description": "...", "arguments": [...] }]
  }
}
```

Each entry comes from the `FunctionDescriptor` returned by the `list-functions`
`CompositeFunctionCall` system call (target = `system`). If a language engine is not
running, its list is `[]`.

### `/api/engines` response schema

```json
{ "r": true, "python": false, "julia": true }
```

### `PipeClient` internal state

```
pipe_name:   str
timeout_ms:  int
_handle:     HANDLE | None   (pywin32) or ctypes c_void_p
```

The handle is opened lazily on the first call to `send_code` / `send_function_call`,
or eagerly if `connect()` is called explicitly.


---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid
executions of a system — essentially, a formal statement about what the system should
do. Properties serve as the bridge between human-readable specifications and
machine-verifiable correctness guarantees.*

**Property Reflection before writing:**

After prework, the properties identified fall into these clusters:

- **Round-trip framing** (Req 2.4, 2.10, 10.1–10.4): all test the same underlying
  `frame → unframe = identity` invariant, just with different message shapes. These are
  combined into two properties: one for `code` messages, one for `function_call`
  messages. The byte-level prefix correctness (10.1) is a sub-consequence of the
  round-trip and need not be a separate property.

- **Language resolution** (Req 1.2, 1.3): these are related. "The set of processes
  launched equals the set of enabled languages" subsumes "each launched process has
  the correct pipe name". Combined into one property.

- **Script response shape** (Req 3.5, 3.6, 3.7): three separate type-dispatch cases.
  Kept as one combined property since they share the "response fields are correct for
  the Variable type" invariant.

- **Rate-limiting + payload-size** (Req 3.11, 3.12): both test that existing guards
  apply to new endpoints. Combined into one property.

- Properties about `/api/engines` (Req 8.1), `/api/functions` (Req 7.3), PID lifecycle
  (Req 8.6), config defaults (Req 9.1), and `--languages` override (Req 9.6) each
  cover distinct invariants and are kept separate.

- **Variable conversion** (Req 2.5): independent of framing; kept separate.

- **Empty code rejection** (Req 3.3): "empty or whitespace-only code → 400" is its own
  property.

This reflection yields **10 properties** with no redundancy.

---

### Property 1: Framing round-trip for code messages

*For any* `CallResponse` with a `code` field containing between 1 and 500 lines of
up to 1,000 characters each, calling `_frame()` on the message and then `_unframe()`
on the resulting bytes SHALL produce a `CallResponse` that is field-for-field
identical to the original message.

**Validates: Requirements 2.2, 2.4, 2.10, 10.1, 10.2, 10.3**

---

### Property 2: Framing round-trip for function_call messages

*For any* `CallResponse` with a `function_call` field containing an arbitrary
function name string and between 0 and 20 `Variable` arguments of any supported
scalar type (nil, integer, real, str, boolean), calling `_frame()` and then
`_unframe()` SHALL produce a `CallResponse` identical to the original.

**Validates: Requirements 2.3, 2.4, 10.4**

---

### Property 3: Enabled languages control exactly which processes are launched

*For any* subset S of {r, python, julia} marked as enabled in `neven-config.json`,
the Launcher SHALL start exactly the Control processes in S — no more, no less — and
each started process SHALL receive `-p \\.\pipe\neven_{lang}` as its pipe name
argument and SHALL have `RJ2XCL_HOME` set in its environment.

**Validates: Requirements 1.2, 1.3, 1.4, 7.1**

---

### Property 4: SIGINT/SIGTERM terminates all launched processes

*For any* non-empty set of Control processes started by the Launcher, when the
Launcher receives SIGINT or SIGTERM, every process in that set SHALL be terminated
before the Launcher exits.

**Validates: Requirements 1.9**

---

### Property 5: Variable-to-JSON mapping is correct for all scalar types

*For any* `Variable` message whose oneof is set to `integer`, `real`, `str`,
`boolean`, `nil`, `arr`, or `html_content`, the HTTP response JSON produced by
`NEVENHandler` SHALL contain the correct `type` field and SHALL correctly populate
the type-specific fields (`result`, `html`/`title`, or `columns`/`rows`) with values
equal to the original `Variable` payload.

**Validates: Requirements 2.5, 3.5, 3.6, 3.7**

---

### Property 6: Empty or whitespace-only code is rejected with HTTP 400

*For any* string `s` composed entirely of whitespace characters (including the empty
string), POSTing `{"code": s}` to `/api/r`, `/api/python`, or `/api/julia` SHALL
return HTTP 400 with `{"status": "error", "message": "Missing 'code' field"}`.

**Validates: Requirements 3.3**

---

### Property 7: Rate limiter and payload size limit apply to all Script endpoints

*For any* sequence of POST requests to `/api/r`, `/api/python`, or `/api/julia`
that exceeds the rate limit threshold, each request beyond the threshold SHALL
return HTTP 429. *For any* request body whose byte size exceeds `maxPayloadMB × 1024²`,
the server SHALL return HTTP 413 — regardless of which Script endpoint is targeted.

**Validates: Requirements 3.11, 3.12**

---

### Property 8: Engine status accurately reflects pipe availability

*For any* combination of available/unavailable Named Pipes for the three languages,
`GET /api/engines` SHALL return a JSON object in which each language key maps to
`true` if and only if a `CreateFile` probe on that language's pipe name succeeds.

**Validates: Requirements 8.1**

---

### Property 9: `/api/functions` returns lists for running engines, empty for stopped ones

*For any* subset R of {r, python, julia} for which the corresponding Control process
is running, `GET /api/functions` SHALL return a `languages` object in which each
language in R maps to a non-null list (possibly empty if no functions are registered)
and each language not in R maps to `[]`.

**Validates: Requirements 7.3, 7.4**

---

### Property 10: `--languages` CLI argument exactly controls which engines start

*For any* comma-separated `--languages` argument specifying a non-empty subset of
{r, python, julia}, the Launcher SHALL start Control processes for exactly that
subset, regardless of what the `languages` section of `neven-config.json` specifies.

**Validates: Requirements 9.6**


---

## Error Handling

### Launcher errors

| Situation | Behavior |
|---|---|
| `neven-config.json` missing | Use all defaults; log warning to stderr |
| Control binary not found in `controlDir` | Log `[NEVEN Launcher] WARNING: <exe> not found — skipping <lang>`; continue |
| Control process doesn't create pipe within 10 s | Log `[NEVEN Launcher] WARNING: <lang> pipe timeout — skipping`; continue |
| Control process exits unexpectedly | Log `[NEVEN Launcher] ERROR: <name> exited with code <N>` to stderr |
| HTTP server cannot bind on port 5555 or 5556 | Log fatal error; `sys.exit(1)` |
| Non-Windows platform | Log `[NEVEN Launcher] INFO: Non-Windows platform — scripting engines not started`; start HTTP server only |

### `PipeClient` errors

| Situation | Exception |
|---|---|
| `CreateFile` fails | `OSError` (let caller handle) |
| Response length prefix > 256 KB | `PipeProtocolError("Response size N exceeds 256 KB limit")` |
| Payload fails `ParseFromString` | `PipeProtocolError("Failed to deserialize CallResponse")` |
| Read doesn't complete within `timeout_ms` | `PipeTimeoutError("Pipe read timed out after N ms")` |
| `err` field set in `CallResponse` | `PipeClientError(err_message)` |
| Pipe broken / `ReadFile` returns 0 bytes | `PipeClientError("Pipe closed by server")` |

### HTTP Server new endpoint errors

All existing error handling remains unchanged. The new routing additions follow the
same pattern as existing handlers:

- `PipeClientError` → `_send_json({"status":"error","message":...}, 200)`
- `PipeTimeoutError` → `_send_json({"status":"error","message":"Script execution timed out"}, 408)`
- Engine unavailable → `_send_json({"status":"error","message":"<lang> engine not available"}, 503)`
- Missing `dataset` table (rpivot) → `_send_json({...}, 400)`
- Reconnect attempt (Req 8.4): one retry via `client.close(); client.connect()` before
  returning 503.

### UI error handling

- Network failure during `runScript()` → caught in `try/catch`, displayed via
  `showScriptError()` with the exception message.
- `status: "error"` in response → rendered with `.msg-error` CSS class.
- `/api/engines` failure (server unreachable) → engine dots remain at previous state;
  no exception thrown to user.


---

## Testing Strategy

### Technology choices

| Layer | Framework | Notes |
|---|---|---|
| Python unit/property tests | `pytest` + `hypothesis` | Already available in Python ecosystem |
| Browser UI | Manual / `pytest` + `httpx` for API contract tests | No browser automation required for logic tests |
| Integration | `pytest` with real `ControlR.exe` / `ControlPython.exe` | Optional, run in CI with Windows runner |

Property tests use **`hypothesis`** (`@given` + `st.*` strategies). Each property test
is configured with `@settings(max_examples=200)` to get thorough coverage.

### Unit tests (example-based)

Tests for specific scenarios that are not universal over input:

- Launcher: `--config` argument present vs absent (Req 1.1)
- Launcher: `--port` overrides config (Req 9.2)
- Launcher: missing binary → skips language, logs warning (Req 9.3)
- Launcher: `--no-browser` suppresses `webbrowser.open` (Req 1.8)
- Launcher: stdout URL printed (Req 1.7)
- PipeClient: `with` statement calls `close()` (Req 2.9)
- PipeClient: `err` field in response raises `PipeClientError` (Req 2.6)
- PipeClient: mock slow pipe raises `PipeTimeoutError` (Req 2.7)
- HTTP: `/api/r` with no PipeClient registered → 503 (Req 3.10)
- HTTP: `/api/rpivot` with no dataset → 400 (Req 5.7)
- HTTP: `/api/rpivot` with R engine down → 503 (Req 5.5)
- HTTP: PipeClientError → 200 with `status: error` (Req 3.8)
- HTTP: PipeTimeoutError → 408 (Req 3.9)
- Launcher: PID file written and removed (Req 8.6) — also covered by Property 11
- Non-Windows: processes not started, script endpoints return 503 (Req 4.7)
- `/api/functions` with no engine running → all empty lists (Req 7.4)

### Property-based tests

Each corresponds to a numbered Correctness Property above.

```python
# Property 1 — Framing round-trip for code messages
@given(
    lines=st.lists(
        st.text(max_size=1000),
        min_size=1, max_size=500
    )
)
@settings(max_examples=200)
def test_frame_roundtrip_code(lines):
    msg = variable_pb2.CallResponse()
    msg.code.line.extend(lines)
    framed = _frame(msg)
    recovered = _unframe(framed)
    assert list(recovered.code.line) == lines
```

```python
# Property 2 — Framing round-trip for function_call messages
@given(
    fname=st.text(min_size=1, max_size=100),
    args=st.lists(scalar_variable_strategy(), max_size=20)
)
@settings(max_examples=200)
def test_frame_roundtrip_function_call(fname, args):
    msg = variable_pb2.CallResponse()
    msg.function_call.function = fname
    msg.function_call.arguments.extend(args)
    framed = _frame(msg)
    recovered = _unframe(framed)
    assert recovered.function_call.function == fname
    assert len(recovered.function_call.arguments) == len(args)
```

```python
# Property 3 — Language selection
@given(enabled=st.sets(st.sampled_from(['r', 'python', 'julia'])))
@settings(max_examples=50)
def test_launcher_starts_correct_processes(enabled, mock_subprocess):
    config = make_config(enabled_languages=enabled)
    launched = run_launcher_dry(config, mock_subprocess)
    assert {p.language for p in launched} == enabled
    for p in launched:
        assert f'-p \\\\.\\pipe\\neven_{p.language}' in p.args
        assert p.env.get('RJ2XCL_HOME') == config['installDir']
```

```python
# Property 5 — Variable-to-JSON mapping
@given(var=variable_strategy())
@settings(max_examples=200)
def test_variable_to_json_mapping(var, mock_pipe_client):
    mock_pipe_client.returns(var)
    resp = post_api('/api/r', {'code': 'x <- 1'})
    assert resp.status_code == 200
    body = resp.json()
    assert body['status'] == 'ok'
    assert body['type'] == expected_type_for(var)
    assert body[expected_field_for(var)] == expected_value_for(var)
```

```python
# Property 6 — Empty code rejected
@given(code=st.one_of(st.just(''), st.text(alphabet=' \t\n\r', min_size=1)))
@settings(max_examples=100)
def test_empty_code_rejected(code):
    for endpoint in ['/api/r', '/api/python', '/api/julia']:
        resp = post_api(endpoint, {'code': code})
        assert resp.status_code == 400
        assert resp.json()['status'] == 'error'
```

```python
# Property 8 — Engine status reflects pipe availability
@given(available=st.sets(st.sampled_from(['r', 'python', 'julia'])))
@settings(max_examples=50)
def test_engines_endpoint_accuracy(available, mock_pipe_probe):
    mock_pipe_probe.available = available
    resp = get_api('/api/engines')
    data = resp.json()
    for lang in ['r', 'python', 'julia']:
        assert data[lang] == (lang in available)
```

```python
# Property 9 — /api/functions lists
@given(running=st.sets(st.sampled_from(['r', 'python', 'julia'])))
@settings(max_examples=50)
def test_functions_lists_running_engines(running, mock_engine_registry):
    mock_engine_registry.running = running
    resp = get_api('/api/functions')
    data = resp.json()['languages']
    for lang in ['r', 'python', 'julia']:
        if lang in running:
            assert isinstance(data[lang], list)
        else:
            assert data[lang] == []
```

```python
# Property 10 — --languages override
@given(
    config_langs=st.sets(st.sampled_from(['r', 'python', 'julia'])),
    cli_langs=st.frozensets(st.sampled_from(['r', 'python', 'julia']), min_size=1)
)
@settings(max_examples=50)
def test_languages_flag_overrides_config(config_langs, cli_langs, mock_subprocess):
    config = make_config(enabled_languages=config_langs)
    launched = run_launcher_dry(config, mock_subprocess, languages=','.join(cli_langs))
    assert {p.language for p in launched} == set(cli_langs)
```

### Integration tests

Run against real Control processes (Windows CI runner only):

- Full startup and pipe round-trip for each language (R, Python, Julia)
- `/api/rpivot` with a small CSV dataset loaded
- Browser open with `--no-browser` suppression (smoke)

### Test tagging convention

Each property test file includes a comment block:
```python
# Feature: neven-studio-standalone, Property N: <property_title>
```
This enables filtering with `pytest -k "neven-studio-standalone"`.

