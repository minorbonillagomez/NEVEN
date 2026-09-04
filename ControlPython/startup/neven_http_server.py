# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN v3.0 — HTTP Server for Task Pane
# ═══════════════════════════════════════════════════════════════════════════════
# Serves the Task Pane HTML/JS and exposes REST API endpoints for DuckDB queries.
# Runs on a dedicated daemon thread inside ControlPython.exe.
# Binds to localhost:5555 (HTTPS) with fallback to 5556.
#
# Endpoints:
#   GET  /health           → Server status
#   GET  /taskpane.html    → Main Task Pane UI
#   GET  /assets/*         → Static assets (CSS, JS, icons)
#   GET  /viewers/*        → Existing viewer HTML files
#   POST /api/analyze      → Descriptive statistics via DuckDB
#   POST /api/groupby      → Live GROUP BY aggregation
#   POST /api/query        → Arbitrary SQL execution (SELECT only)
#   POST /api/r            → Execute R code via PipeClient (task 6.2)
#   POST /api/python       → Execute Python code via PipeClient (task 6.2)
#   POST /api/julia        → Execute Julia code via PipeClient (task 6.2)
#   POST /api/rpivot       → RPivot table generation via R (task 7.3)
#   GET  /api/engines      → Pipe-probe each language engine (task 7.1)
#   GET  /api/functions    → List registered functions per language (task 7.2)

import os
import sys
import json
import ssl
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

# ─── pipe_client imports (optional — only needed for Script endpoints) ────────
# pipe_client.py lives in TaskPane/, which is one level up from ControlPython/startup/.
# We add TaskPane to sys.path lazily so the server can still start without it.
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _TASKPANE = os.path.normpath(os.path.join(_HERE, "..", "..", "TaskPane"))
    if _TASKPANE not in sys.path and os.path.isdir(_TASKPANE):
        sys.path.insert(0, _TASKPANE)
    from pipe_client import (  # type: ignore[import]
        PipeClientError as _PipeClientError,
        PipeTimeoutError as _PipeTimeoutError,
        variable_to_python as _variable_to_python,
    )
    _PIPE_CLIENT_AVAILABLE = True
except ImportError:
    # In environments without pipe_client (e.g. production before TaskPane is
    # installed) the Script endpoints return 503 anyway because no factory is
    # registered, so these stubs are only reached in unit tests that mock
    # _handle_script directly.
    class _PipeClientError(Exception):  # type: ignore[no-redef]
        pass

    class _PipeTimeoutError(_PipeClientError):  # type: ignore[no-redef]
        pass

    def _variable_to_python(var):  # type: ignore[misc]
        return None

    _PIPE_CLIENT_AVAILABLE = False

# Data Lab handler (nuevo en Data Lab V1)
try:
    from datalab_handler import DataLabHandler as _DataLabHandler  # type: ignore
    _datalab_handler = _DataLabHandler()
    _DATALAB_AVAILABLE = True
except ImportError:
    _DATALAB_AVAILABLE = False

# Package Manager Service
try:
    from package_manager_service import (  # type: ignore
        init_pkg_service as _init_pkg_service,
        PackageManagerService as _PackageManagerService,
    )
    _PKG_IMPORT_OK = True
except ImportError:
    _PKG_IMPORT_OK = False

_pkg_service: object = None
_PKG_SERVICE_AVAILABLE = False


def _is_broken_pipe(exc: Exception, msg: str) -> bool:
    """Return True when *exc* indicates the Named Pipe connection was lost.

    Req 8.4: triggers the single reconnect attempt inside ``_handle_script``.
    """
    if isinstance(exc, OSError):
        return True
    lowered = msg.lower()
    return "pipe closed" in lowered or "broken pipe" in lowered

# ─── Win32 pipe-probe imports (Windows only) ──────────────────────────────────
try:
    import win32file  # type: ignore
    import win32con   # type: ignore
    import pywintypes  # type: ignore
    _WIN32_AVAILABLE = True
except ImportError:
    win32file = None   # type: ignore
    win32con = None    # type: ignore
    pywintypes = None  # type: ignore
    _WIN32_AVAILABLE = False


# ─── Pipe probe helper ────────────────────────────────────────────────────────

def _probe_pipe(pipe_name: str) -> bool:
    """Return True if the named pipe exists (CreateFile succeeds), False otherwise.

    On non-Windows (or when pywin32 is unavailable) always returns False.

    Args:
        pipe_name: Full pipe path, e.g. ``\\\\.\\pipe\\neven_r``.

    Returns:
        True if a CreateFile call on the pipe succeeds; False on any exception
        or on non-Windows platforms.
    """
    if not _WIN32_AVAILABLE:
        return False
    try:
        handle = win32file.CreateFile(
            pipe_name,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0,           # no sharing
            None,        # default security
            win32con.OPEN_EXISTING,
            0,           # default attributes
            None,        # no template
        )
        win32file.CloseHandle(handle)
        return True
    except Exception:
        return False

# ─── Configuration ────────────────────────────────────────────────────────────

_server_instance = None
_server_port = None
_config = {}

# ── Estado global del contexto Excel → Tab IA ─────────────────────────────
# Almacena el último contexto publicado por =NEVEN.IA.Contexto()
# Se consume al ser leído por GET /api/ai/context/pending
_excel_context_lock    = threading.Lock()
_excel_context_pending = None   # {text, timestamp, source, columns, n_rows}

DEFAULT_CONFIG = {
    "enabled": True,
    "port": 5555,
    "fallbackPort": 5556,
    "certPath": "",
    "keyPath": "",
    "staticDir": "C:\\NEVEN\\taskpane",
    "viewersDir": "C:\\NEVEN\\workspace",
    "queryTimeoutSec": 30,
    "maxPayloadMB": 50,
    # pipe_client_factory: dict[str, Callable[[], PipeClient]]
    # Maps language name ("r", "python", "julia") to a zero-argument callable
    # that returns a connected PipeClient instance.  Injected by start_studio.py
    # (task 4.3) or by unit tests.  When absent, all Script endpoints return 503.
    "pipe_client_factory": {},
    "functions_dir": r"C:\NEVEN\functions",  # Directorio de sidecar JSONs
}


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Token-bucket rate limiter: max_requests per window_sec."""
    def __init__(self, max_requests=60, window_sec=60):
        self.max_requests = max_requests
        self.window_sec = window_sec
        self.requests = []
        self.lock = threading.Lock()

    def allow(self):
        now = time.time()
        with self.lock:
            self.requests = [t for t in self.requests if now - t < self.window_sec]
            if len(self.requests) >= self.max_requests:
                return False
            self.requests.append(now)
            return True


_rate_limiter = RateLimiter(max_requests=300, window_sec=60)


# ─── DuckDB Engine ────────────────────────────────────────────────────────────

_db = None
_db_lock = threading.Lock()


def _get_db():
    """Get or create the DuckDB in-memory connection."""
    global _db
    if _db is None:
        import duckdb
        _db = duckdb.connect(database=':memory:')
    return _db


def load_data(columns, types, rows):
    """Create/replace the 'dataset' table from received data."""
    db = _get_db()
    with _db_lock:
        db.execute("DROP TABLE IF EXISTS dataset")
        # Map types
        type_map = {"numeric": "DOUBLE", "text": "VARCHAR", "date": "VARCHAR"}
        col_defs = ", ".join(
            f'"{c}" {type_map.get(types.get(c, "text"), "VARCHAR")}'
            for c in columns
        )
        db.execute(f"CREATE TABLE dataset ({col_defs})")
        if rows:
            placeholders = ", ".join(["?"] * len(columns))
            db.executemany(f"INSERT INTO dataset VALUES ({placeholders})", rows)
    return len(rows)


def execute_analyze():
    """Compute descriptive statistics for all columns in dataset."""
    db = _get_db()
    with _db_lock:
        cols_info = db.execute("DESCRIBE dataset").fetchall()
        row_count = db.execute("SELECT COUNT(*) FROM dataset").fetchone()[0]

    statistics = []
    for col_name, col_type, *_ in cols_info:
        dtype = col_type.upper()
        is_numeric = any(t in dtype for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC', 'BIGINT', 'REAL'])

        stat = {"column": col_name, "type": col_type, "numeric": is_numeric}

        with _db_lock:
            na_count = db.execute(f'SELECT COUNT(*) - COUNT("{col_name}") FROM dataset').fetchone()[0]

        stat["na_count"] = int(na_count)
        stat["na_pct"] = round(na_count / max(row_count, 1) * 100, 2)

        if is_numeric:
            with _db_lock:
                r = db.execute(f'''SELECT
                    COUNT("{col_name}"), MIN("{col_name}"), MAX("{col_name}"),
                    AVG("{col_name}"), MEDIAN("{col_name}"), STDDEV("{col_name}"),
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col_name}"),
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY "{col_name}"),
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col_name}"),
                    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY "{col_name}"),
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY "{col_name}"),
                    MODE() WITHIN GROUP (ORDER BY "{col_name}")
                    FROM dataset WHERE "{col_name}" IS NOT NULL''').fetchone()
            stat.update({
                "count": int(r[0] or 0), "min": float(r[1] or 0), "max": float(r[2] or 0),
                "mean": float(r[3] or 0), "median": float(r[4] or 0), "std": float(r[5] or 0),
                "q25": float(r[6] or 0), "q50": float(r[7] or 0), "q75": float(r[8] or 0),
                "q90": float(r[9] or 0), "q99": float(r[10] or 0), "mode": float(r[11] or 0)
            })
        else:
            with _db_lock:
                r = db.execute(f'SELECT COUNT(DISTINCT "{col_name}"), MODE("{col_name}") FROM dataset WHERE "{col_name}" IS NOT NULL').fetchone()
            stat.update({"unique": int(r[0] or 0), "mode": str(r[1] or "")})

        statistics.append(stat)

    return {"status": "ok", "statistics": statistics, "row_count": row_count, "col_count": len(cols_info)}


VALID_METRICS = {'SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'MEDIAN'}


def _is_numeric(v):
    """Return True if string v looks like a number."""
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def execute_groupby(group_column, value_column, metric):
    """Execute GROUP BY with validated metric on full dataset."""
    metric_upper = metric.upper()
    if metric_upper not in VALID_METRICS:
        raise ValueError(f"Invalid metric: {metric}. Valid: {', '.join(VALID_METRICS)}")

    if metric_upper == 'MEDIAN':
        agg_expr = f'MEDIAN("{value_column}")'
    else:
        agg_expr = f'{metric_upper}("{value_column}")'

    sql = f'SELECT "{group_column}" as grp, {agg_expr} as val FROM dataset GROUP BY "{group_column}" ORDER BY val DESC'

    db = _get_db()
    with _db_lock:
        result = db.execute(sql).fetchall()

    return {
        "status": "ok",
        "results": [{"group": str(r[0]) if r[0] is not None else "NULL", "value": float(r[1] or 0)} for r in result],
        "metric": metric_upper,
        "row_count": len(result)
    }


def execute_query(sql, page=1, page_size=100):
    """Execute SQL with timeout and pagination. SELECT only."""
    # Ignorar comentarios -- al validar el tipo de sentencia
    sql_clean = '\n'.join(
        line for line in sql.splitlines()
        if not line.strip().startswith('--')
    ).strip()
    sql_stripped = sql_clean.upper()
    if not sql_stripped.startswith(("SELECT", "WITH", "SHOW", "DESCRIBE")):
        raise ValueError("Only SELECT/WITH statements are allowed")

    timeout_sec = _config.get("queryTimeoutSec", 30)
    result_holder = {}
    error_holder = {}

    def run_query():
        try:
            db = _get_db()
            with _db_lock:
                res = db.execute(sql)
                result_holder["columns"] = [desc[0] for desc in res.description]
                result_holder["data"] = res.fetchall()
        except Exception as e:
            error_holder["message"] = str(e)

    thread = threading.Thread(target=run_query)
    thread.start()
    thread.join(timeout=timeout_sec)

    if thread.is_alive():
        return None, "Query exceeded 30 second timeout"

    if "message" in error_holder:
        return None, error_holder["message"]

    all_rows = result_holder["data"]
    total = len(all_rows)
    start = (page - 1) * page_size
    end = min(start + page_size, total)

    return {
        "status": "ok",
        "columns": result_holder["columns"],
        "rows": [[str(v) if v is not None else None for v in row] for row in all_rows[start:end]],
        "total_rows": total,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size
    }, None


# ─── HTTP Request Handler ─────────────────────────────────────────────────────

class NEVENHandler(BaseHTTPRequestHandler):
    """HTTP handler for NEVEN Task Pane server."""

    def log_message(self, format, *args):
        """Suppress default stderr logging."""
        pass

    def _get_pipe_client(self, lang: str):
        """Return a PipeClient for *lang* by calling the injected factory.

        Args:
            lang: Language key — "r", "python", or "julia".

        Returns:
            A PipeClient instance produced by the registered factory callable.

        Raises:
            KeyError: If *lang* has no factory registered in ``pipe_client_factory``.
                      Callers should map this to an HTTP 503 response.
        """
        factory = _config.get("pipe_client_factory", {})
        if lang not in factory:
            raise KeyError(f"No pipe_client_factory registered for language: {lang!r}")
        return factory[lang]()

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self._add_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message, status=400):
        self._send_json({"status": "error", "message": message}, status)

    def _add_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self._add_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Serve static files and health endpoint."""
        if not _rate_limiter.allow():
            self._send_error_json("Rate limit exceeded (60 req/min)", 429)
            return

        parsed = urlparse(self.path)
        path = unquote(parsed.path).lstrip('/')

        # Health check
        if path == 'health':
            self._send_json({"status": "ok", "version": "3.0.0", "port": _server_port})
            return

        # ── Script engine endpoints (implemented in tasks 7.1 and 7.2) ──────
        if path == 'api/engines':
            self._handle_engines()
            return

        if path == 'api/functions':
            self._handle_functions()
            return

        # Bridge pull (TaskPane reads data that Excel pushed)
        if path == 'api/bridge/pull':
            key = unquote(parsed.query.split('=')[1]) if '=' in (parsed.query or '') else 'default'
            bridge_dir = os.path.join(os.path.dirname(_config.get("staticDir", "C:\\NEVEN\\taskpane")), "bridge")
            filepath = os.path.join(bridge_dir, f"{key}.json")
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._send_json({"status": "ok", "key": key, "data": data})
            else:
                self._send_json({"status": "empty", "key": key, "data": None})
            return

        # Bridge status (list all keys in buffer)
        if path == 'api/bridge/status':
            bridge_dir = os.path.join(os.path.dirname(_config.get("staticDir", "C:\\NEVEN\\taskpane")), "bridge")
            keys = []
            if os.path.isdir(bridge_dir):
                keys = [f[:-5] for f in os.listdir(bridge_dir) if f.endswith('.json')]
            self._send_json({"status": "ok", "keys": keys})
            return

        # ── Data Lab catalog ──────────────────────────────────────────────────
        if path == 'api/datalab/catalog':
            if not _DATALAB_AVAILABLE:
                self._send_error_json("DataLab no disponible", 503)
                return
            result = _datalab_handler.handle_catalog(_config)
            self._send_json(result)
            return

        # ── Package Manager endpoints ─────────────────────────────────────────
        if path == 'api/packages/status':
            self._handle_pkg_status(None)
            return

        if path.startswith('api/packages/status/'):
            motor = path.split('api/packages/status/', 1)[1]
            self._handle_pkg_status(motor)
            return

        if path == 'api/packages/progress':
            if not _PKG_SERVICE_AVAILABLE:
                self._send_json({"status": "unavailable"})
            else:
                self._send_json(_pkg_service.get_progress())
            return

        if path.startswith('api/packages/function/'):
            fn_id = path.split('api/packages/function/', 1)[1]
            self._handle_pkg_function(fn_id)
            return

        # ── AI config ─────────────────────────────────────────────────────────
        if path == 'api/ai/config':
            config_path = os.path.join(
                os.path.dirname(_config.get("staticDir", r"C:\NEVEN\taskpane")), "..",
                "neven-config.json"
            )
            if not os.path.isfile(config_path):
                config_path = r"C:\NEVEN\neven-config.json"
            try:
                with open(config_path, "r", encoding="utf-8") as _f:
                    full_cfg = json.load(_f)
                ai = full_cfg.get("AI", {})
                prompts_dir = ai.get("promptsDirectory", r"C:\NEVEN\prompts")
                prompt_ids = []
                if os.path.isdir(prompts_dir):
                    prompt_ids = [
                        os.path.splitext(f)[0]
                        for f in sorted(os.listdir(prompts_dir))
                        if f.endswith(".txt")
                    ]
                self._send_json({
                    "status":    "ok",
                    "enabled":   ai.get("enabled", False),
                    "provider":  ai.get("provider", "lmstudio"),
                    "model":     ai.get("model", ""),
                    "endpoint":  ai.get("endpoint", ""),
                    "prompts":   prompt_ids,
                })
            except Exception as exc:
                self._send_error_json(f"Error leyendo config AI: {exc}", 500)
            return

        # ── AI context/pending — GET consume el contexto pendiente de Excel ──
        if path == 'api/ai/context/pending':
            global _excel_context_pending
            with _excel_context_lock:
                ctx = _excel_context_pending
                _excel_context_pending = None   # consumible — se borra al leerse
            if ctx:
                self._send_json({"status": "ok", "context": ctx})
            else:
                self._send_json({"status": "empty"})
            return

        # Serve viewers
        if path.startswith('viewers/'):
            viewers_dir = _config.get("viewersDir", "C:\\NEVEN\\workspace")
            file_path = os.path.join(viewers_dir, path[8:])
            self._serve_file(file_path)
            return

        # Serve static files (taskpane, assets)
        static_dir = _config.get("staticDir", "C:\\NEVEN\\taskpane")
        if path == '' or path == 'taskpane.html':
            path = 'taskpane.html'
        file_path = os.path.join(static_dir, path)
        self._serve_file(file_path)

    def _serve_file(self, file_path):
        """Serve a file from disk."""
        if not os.path.isfile(file_path):
            self.send_response(404)
            self._add_cors_headers()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
            return

        # Detect content type
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
            '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon'
        }
        ctype = content_types.get(ext, 'application/octet-stream')

        with open(file_path, 'rb') as f:
            content = f.read()

        self.send_response(200)
        self._add_cors_headers()
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        """Handle API endpoints."""
        if not _rate_limiter.allow():
            self._send_error_json("Rate limit exceeded (60 req/min)", 429)
            return

        # Check payload size
        content_length = int(self.headers.get('Content-Length', 0))
        max_bytes = _config.get("maxPayloadMB", 50) * 1024 * 1024
        if content_length > max_bytes:
            self._send_error_json(f"Payload exceeds {_config.get('maxPayloadMB', 50)} MB limit", 413)
            return

        parsed = urlparse(self.path)
        path = parsed.path.lstrip('/')

        try:
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}
        except json.JSONDecodeError:
            self._send_error_json("Invalid JSON body")
            return

        # Route to endpoint
        if path == 'api/analyze':
            self._handle_analyze(body)
        elif path == 'api/groupby':
            self._handle_groupby(body)
        elif path == 'api/query':
            self._handle_query(body)
        elif path == 'api/load' or path == 'api/load_file':
            self._handle_load(body)
        elif path == 'api/bridge/push':
            self._handle_bridge_push(body)
        elif path == 'api/bridge/write':
            self._handle_bridge_write(body)
        # ── Script execution endpoints (implemented in task 6.2) ─────────────
        elif path in ('api/r', 'api/python', 'api/julia'):
            self._handle_script(path.split('/')[1], body)
        elif path == 'api/rpivot':
            self._handle_rpivot(body)
        elif path == 'api/datalab/run':
            if not _DATALAB_AVAILABLE:
                self._send_error_json("DataLab no disponible", 503)
                return
            result = _datalab_handler.handle_run(
                body, _config,
                _get_db(), _db_lock,
                self._get_pipe_client
            )
            status_code = 200 if result.get("status") == "ok" else 400
            self._send_json(result, status_code)
        elif path == 'api/db_connect':
            self._handle_db_connect(body)
        elif path == 'api/save_script':
            self._handle_save_script(body)
        elif path == 'api/ai/chat':
            self._handle_ai_chat(body)
        elif path == 'api/ai/context':
            self._handle_ai_context(body)
        elif path == 'api/packages/install':
            self._handle_pkg_install(body)
        else:
            self._send_error_json(f"Unknown endpoint: /{path}", 404)

    # ── Package Manager endpoints ──────────────────────────────────────────────

    def _handle_pkg_status(self, motor: str = None):
        """GET /api/packages/status[/{motor}][?refresh=true]"""
        if not _PKG_SERVICE_AVAILABLE:
            self._send_json({"status": "ok", "fuente": "unavailable", "paquetes": []})
            return

        # ?refresh=true fuerza re-verificación en vivo (no usa caché)
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(self.path).query)
        force_refresh = query.get("refresh", ["false"])[0].lower() == "true"

        if force_refresh:
            # Verificación en vivo — actualiza el caché al terminar
            try:
                results = _pkg_service.verificar_todos(timeout_s=60)
                _pkg_service.save_cache(results)
                estado = results
                fuente = "live"
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)})
                return
        else:
            cache = _pkg_service.load_cache()
            estado = cache.get("estado", [])
            fuente = "cache"

        if motor:
            estado = [e for e in estado if e.get("motor", "").lower() == motor.lower()]
            if not estado:
                estado = [{"motor": motor, "motor_disponible": False,
                           "paquete": None, "instalado": None,
                           "version_instalada": None, "version_requerida": None,
                           "funciones_afectadas": []}]
        ts = _pkg_service.load_cache().get("ultima_verificacion", {})
        self._send_json({"status": "ok", "fuente": fuente,
                         "timestamp_cache": ts, "paquetes": estado})

    def _handle_pkg_function(self, function_id: str):
        """GET /api/packages/function/{id}"""
        if not _PKG_SERVICE_AVAILABLE:
            self._send_json({"status": "ok", "function_id": function_id, "paquetes": []})
            return
        try:
            results = _pkg_service.verificar_funcion(function_id)
            self._send_json({"status": "ok", "function_id": function_id, "paquetes": results})
        except Exception as e:
            self._send_json({"status": "ok", "function_id": function_id,
                             "paquetes": [], "error": str(e)})

    def _handle_pkg_install(self, body: dict):
        """POST /api/packages/install"""
        if not _PKG_SERVICE_AVAILABLE:
            self._send_error_json("Package Manager no disponible", 503)
            return
        items = body.get("paquetes", [])
        if not items or not isinstance(items, list):
            self._send_error_json("Se requiere 'paquetes': [{motor, nombre}, ...]", 400)
            return
        # Validar estructura mínima
        valid = [i for i in items if isinstance(i, dict) and "motor" in i and "nombre" in i]
        if not valid:
            self._send_error_json("Cada paquete debe tener 'motor' y 'nombre'", 400)
            return
        _pkg_service.encolar_instalacion(valid)
        self._send_json({"status": "ok", "encolados": len(valid)})

    # ── AI/Chat endpoint ──────────────────────────────────────────────────────

    def _handle_ai_chat(self, body: dict):
        """POST /api/ai/chat — proxies a conversational message to the LLM.

        Body:
          messages   : list of {role, content} — full conversation history
          context    : optional str — dataset summary injected as system context
          prompt_id  : optional str — load a prompt template from promptsDirectory
          stream     : always False (streaming not supported via this endpoint)

        Returns:
          {status, reply, model, tokens_used}   on success
          {status, message, code}               on error
        """
        import urllib.request as _url_req

        # ── Load AI config from neven-config.json ────────────────────────────
        config_path = os.path.join(
            os.path.dirname(_config.get("staticDir", r"C:\NEVEN\taskpane")), "..",
            "neven-config.json"
        )
        # Fallback to canonical production path
        if not os.path.isfile(config_path):
            config_path = r"C:\NEVEN\neven-config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as _f:
                full_cfg = json.load(_f)
        except Exception as exc:
            self._send_error_json(f"No se pudo leer neven-config.json: {exc}", 503)
            return

        ai = full_cfg.get("AI", {})
        if not ai.get("enabled", False):
            self._send_error_json(
                "AI.enabled=false en neven-config.json. Habilite la integración AI primero.",
                503
            )
            return

        endpoint    = ai.get("endpoint", "http://localhost:1234/v1/chat/completions")
        model       = ai.get("model", "local-model")
        max_tokens  = int(ai.get("maxTokens", 1000))
        temperature = float(ai.get("temperature", 0.3))
        timeout_sec = int(ai.get("timeout", 60))
        api_key     = ai.get("apiKey", "")
        provider    = ai.get("provider", "lmstudio")
        prompts_dir = ai.get("promptsDirectory", r"C:\NEVEN\prompts")

        # ── Build messages array ──────────────────────────────────────────────
        messages = body.get("messages", [])
        context  = body.get("context", "").strip()

        # Resolve prompt template if requested
        prompt_id = body.get("prompt_id", "").strip()
        if prompt_id:
            tmpl_path = os.path.join(prompts_dir, f"{prompt_id}.txt")
            if os.path.isfile(tmpl_path):
                try:
                    template = open(tmpl_path, "r", encoding="utf-8").read()
                    # Replace {{resultado}} and {{datos}} placeholders with context
                    template = template.replace("{{resultado}}", context)
                    template = template.replace("{{datos}}", context)
                    template = template.replace("{{contexto}}", "")
                    # Inject as first user message if messages is empty
                    if not messages:
                        messages = [{"role": "user", "content": template}]
                except Exception:
                    pass  # Fall through to plain messages

        if not messages:
            self._send_error_json("El campo 'messages' no puede estar vacío.", 400)
            return

        # Validate messages structure
        valid_roles = {"user", "assistant", "system"}
        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                self._send_error_json("Cada mensaje debe tener 'role' y 'content'.", 400)
                return
            if msg["role"] not in valid_roles:
                self._send_error_json(f"Rol inválido '{msg['role']}'. Use: user, assistant, system.", 400)
                return

        # Inject dataset context as system message (first in list)
        if context:
            sys_msg = {"role": "system", "content": (
                "Eres un analista de datos experto. El usuario está trabajando con NEVEN, "
                "un add-in de Excel con R, Julia y Python. "
                f"Contexto del dataset actual:\n\n{context}\n\n"
                "Responde siempre en español a menos que el usuario escriba en otro idioma. "
                "Usa Markdown para formatear tu respuesta."
            )}
            messages = [sys_msg] + [m for m in messages if m.get("role") != "system"]

        # ── HTTP request to LLM ───────────────────────────────────────────────
        headers = {"Content-Type": "application/json"}

        if provider == "azure":
            # Azure OpenAI usa api-key en header y endpoint con deployment + api-version
            headers["api-key"] = api_key
            api_version = ai.get("apiVersion", "2025-01-01-preview")
            azure_base  = endpoint.rstrip("/")
            endpoint = (
                f"{azure_base}/openai/deployments/{model}"
                f"/chat/completions?api-version={api_version}"
            )
            req_body = json.dumps({
                "messages":    messages,
                "max_tokens":  max_tokens,
                "temperature": temperature,
            }, ensure_ascii=False).encode("utf-8")
        else:
            # OpenRouter, LM Studio, Ollama, OpenAI compatible
            if api_key and provider not in ("ollama", "lmstudio"):
                headers["Authorization"] = f"Bearer {api_key}"
            if provider == "openrouter":
                headers["HTTP-Referer"] = "https://neven-studio.app"
                headers["X-Title"]      = "NEVEN Studio"
            req_body = json.dumps({
                "model":       model,
                "messages":    messages,
                "max_tokens":  max_tokens,
                "temperature": temperature,
            }, ensure_ascii=False).encode("utf-8")

        try:
            req = _url_req.Request(
                endpoint, data=req_body, headers=headers, method="POST"
            )
            with _url_req.urlopen(req, timeout=timeout_sec) as resp:
                raw_body = resp.read()
                # Defensive decode — strip BOM si existe
                raw_str = raw_body.decode("utf-8-sig").strip()
                if not raw_str:
                    self._send_error_json(
                        f"El LLM ({provider}) retornó respuesta vacía. "
                        f"Verifica el modelo '{model}' y la apiVersion en neven-config.json.",
                        502
                    )
                    return
                data = json.loads(raw_str)
        except _url_req.HTTPError as exc:
            try:
                err_body = exc.read().decode("utf-8", errors="replace")
                try:
                    err_json = json.loads(err_body)
                    detail = (err_json.get("error", {}).get("message")
                              or err_json.get("message") or err_body[:300])
                except Exception:
                    detail = err_body[:300]
            except Exception:
                detail = str(exc)
            self._send_error_json(
                f"El LLM ({provider}) retornó HTTP {exc.code}: {detail}", 502)
            return
        except _url_req.URLError as exc:
            reason = str(exc.reason) if hasattr(exc, "reason") else str(exc)
            self._send_error_json(
                f"No se pudo conectar al LLM ({provider}). "
                f"Verifique que {endpoint} esté activo. Detalle: {reason}",
                503
            )
            return
        except Exception as exc:
            self._send_error_json(f"Error al llamar al LLM: {exc}", 500)
            return

        # ── Parse response ────────────────────────────────────────────────────
        try:
            reply  = data["choices"][0]["message"]["content"].strip()
            usage  = data.get("usage", {})
            tokens = usage.get("total_tokens", 0)
        except (KeyError, IndexError) as exc:
            self._send_error_json(f"Respuesta inesperada del LLM: {exc}. Raw: {str(data)[:200]}", 500)
            return

        self._send_json({
            "status":      "ok",
            "reply":       reply,
            "model":       model,
            "tokens_used": tokens,
        })

    def _handle_ai_context(self, body: dict):
        """POST /api/ai/context — recibe contexto de Excel para el Tab IA.

        Llamado por =NEVEN.IA.Contexto() desde el XLL.
        Body: { dataset_text, results_text, source, n_rows, n_cols, columns }
        """
        import datetime as _dt
        global _excel_context_pending

        dataset_text  = body.get("dataset_text",  "").strip()
        results_text  = body.get("results_text",  "").strip()
        source        = body.get("source",        "excel_xll")
        n_rows        = body.get("n_rows",        0)
        columns       = body.get("columns",       [])

        if not dataset_text and not results_text:
            self._send_error_json("dataset_text o results_text requerido", 400)
            return

        # Construir texto de contexto con marcadores reconocibles
        parts = ["=== DATOS DE EXCEL ==="]
        if n_rows:
            parts.append(f"Filas: {n_rows}")
        if columns:
            parts.append(f"Variables: {', '.join(str(c) for c in columns)}")
        parts.append("")
        if dataset_text:
            parts.append(dataset_text)
        if results_text:
            parts.append("\n=== RESULTADOS DEL ANÁLISIS ===")
            parts.append(results_text)

        context_text = "\n".join(parts)

        with _excel_context_lock:
            _excel_context_pending = {
                "text":      context_text,
                "timestamp": _dt.datetime.utcnow().isoformat() + "Z",
                "source":    source,
                "columns":   columns,
                "n_rows":    n_rows,
            }

        self._send_json({
            "status":  "ok",
            "message": f"Contexto almacenado ({len(context_text)} chars)",
        })

    def _handle_save_script(self, body):
        """POST /api/save_script — guarda contenido en un archivo del filesystem.

        Body: { path, content }
        Seguridad: solo permite extensiones de script (.r, .py, .jl, .R).
        """
        import os as _os
        path    = body.get("path", "").strip()
        content = body.get("content", "")

        if not path:
            self._send_error_json("Falta el campo 'path'")
            return

        ext = _os.path.splitext(path)[1].lower()
        if ext not in (".r", ".py", ".jl", ".R", ".python"):
            self._send_error_json(f"Extensión '{ext}' no permitida. Use .r, .py o .jl")
            return

        try:
            # Crear directorio si no existe
            dirpath = _os.path.dirname(path)
            if dirpath:
                _os.makedirs(dirpath, exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            self._send_json({"status": "ok", "path": path,
                             "bytes": len(content.encode("utf-8"))})
        except PermissionError:
            self._send_error_json(f"Sin permiso para escribir en: {path}")
        except Exception as e:
            self._send_error_json(f"Error al guardar: {e}")

    def _handle_db_connect(self, body):
        """POST /api/db_connect — conectar a DB externa y cargar query en DuckDB.

        Body: { engine, host, port, database, user, password, query, sqlite_path }
        Engines: postgresql, mysql, sqlite, sqlserver
        """
        engine   = body.get("engine", "").lower().strip()
        host     = body.get("host", "localhost").strip()
        database = body.get("database", "").strip()
        user     = body.get("user", "").strip()
        password = body.get("password", "")
        query    = body.get("query", "SELECT 1").strip()
        sqlite_path = body.get("sqlite_path", "").strip()

        try:
            port_default = {"postgresql": 5432, "mysql": 3306,
                            "mariadb": 3306, "sqlserver": 1433}.get(engine, 5432)
            port = int(body.get("port", port_default))
        except (TypeError, ValueError):
            port = 5432

        if not engine:
            self._send_error_json("Falta el campo 'engine'")
            return
        if not query:
            self._send_error_json("Falta el campo 'query'")
            return

        # Solo SELECT permitido
        if not query.strip().upper().startswith(("SELECT", "WITH", "SHOW", "DESCRIBE")):
            self._send_error_json("Solo se permiten consultas SELECT/WITH")
            return

        try:
            conn = None

            if engine == "postgresql":
                import importlib
                pg = importlib.import_module("psycopg2")
                conn = pg.connect(
                    host=host, port=port, dbname=database,
                    user=user, password=password,
                    connect_timeout=10
                )

            elif engine in ("mysql", "mariadb"):
                import importlib
                pymysql = importlib.import_module("pymysql")
                conn = pymysql.connect(
                    host=host, port=port, database=database,
                    user=user, password=password,
                    connect_timeout=10,
                    cursorclass=pymysql.cursors.DictCursor
                )

            elif engine == "sqlite":
                import sqlite3, os
                if not sqlite_path or not os.path.isfile(sqlite_path):
                    self._send_error_json(f"Archivo SQLite no encontrado: {sqlite_path}")
                    return
                conn = sqlite3.connect(sqlite_path)
                conn.row_factory = sqlite3.Row

            elif engine == "sqlserver":
                import importlib
                pyodbc = importlib.import_module("pyodbc")
                cs = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={host},{port};DATABASE={database};"
                    f"UID={user};PWD={password};Timeout=10"
                )
                conn = pyodbc.connect(cs)

            else:
                self._send_error_json(f"Motor '{engine}' no soportado. Use: postgresql, mysql, sqlite, sqlserver")
                return

            # Ejecutar query
            cursor = conn.cursor()
            cursor.execute(query)

            # Obtener columnas
            if hasattr(cursor, 'description') and cursor.description:
                col_names = [d[0] for d in cursor.description]
            else:
                col_names = []

            raw_rows = cursor.fetchall()
            conn.close()

            if not col_names:
                self._send_error_json("La query no retornó columnas")
                return

            # Convertir a lista de listas
            rows_as_lists = []
            for row in raw_rows:
                try:
                    rows_as_lists.append([str(v) if v is not None else None for v in row])
                except Exception:
                    rows_as_lists.append(list(row))

            # Detectar tipos
            types = {}
            for i, col in enumerate(col_names):
                sample = [rows_as_lists[j][i] for j in range(min(50, len(rows_as_lists)))
                          if rows_as_lists[j][i] is not None]
                num_count = sum(1 for v in sample if v is not None and _is_numeric(v))
                types[col] = "numeric" if sample and num_count > len(sample) * 0.7 else "text"

            # Cargar en DuckDB
            n = load_data(col_names, types, rows_as_lists)

            self._send_json({
                "status": "ok",
                "rows_loaded": n,
                "columns": col_names,
                "types": types,
                "engine": engine,
                "database": database,
            })

        except ImportError as e:
            pkg = str(e).replace("No module named ", "").strip("'")
            self._send_json({
                "status": "error",
                "message": f"Paquete '{pkg}' no instalado. Ejecute: pip install {pkg}",
                "code": "MISSING_PACKAGE"
            })
        except Exception as e:
            self._send_error_json(f"Error de conexión ({engine}): {e}")

    def _handle_load(self, body):
        """Load data into DuckDB — from array or file path."""
        # If 'path' provided, load file directly with DuckDB
        if "path" in body:
            return self._handle_load_file(body)
        columns = body.get("columns", [])
        types = body.get("types", {})
        rows = body.get("data", [])
        if not columns or not rows:
            self._send_error_json("Missing 'columns' or 'data'")
            return
        try:
            n = load_data(columns, types, rows)
            self._send_json({"status": "ok", "rows_loaded": n})
        except Exception as e:
            self._send_error_json(f"Load error: {e}")

    def _handle_load_file(self, body):
        """Load a CSV/Parquet/JSON file directly into DuckDB."""
        path = body.get("path", "").strip()
        if not path or not os.path.isfile(path):
            self._send_error_json(f"File not found: {path}")
            return
        try:
            db = _get_db()
            fmt = path.lower()
            with _db_lock:
                db.execute("DROP TABLE IF EXISTS dataset")
                if fmt.endswith('.parquet') or fmt.endswith('.pq'):
                    db.execute(f"CREATE TABLE dataset AS SELECT * FROM read_parquet('{path}')")
                elif fmt.endswith('.json') or fmt.endswith('.jsonl'):
                    db.execute(f"CREATE TABLE dataset AS SELECT * FROM read_json_auto('{path}')")
                elif fmt.endswith('.tsv'):
                    db.execute(f"CREATE TABLE dataset AS SELECT * FROM read_csv_auto('{path}', delim='\\t')")
                else:
                    db.execute(f"CREATE TABLE dataset AS SELECT * FROM read_csv_auto('{path}')")
                n_rows = db.execute("SELECT COUNT(*) FROM dataset").fetchone()[0]
                cols_info = db.execute("DESCRIBE dataset").fetchall()
            columns = [c[0] for c in cols_info]
            types = {}
            for c in cols_info:
                dtype = c[1].upper()
                is_num = any(t in dtype for t in ['INT','FLOAT','DOUBLE','DECIMAL','NUMERIC','BIGINT','REAL'])
                types[c[0]] = 'numeric' if is_num else 'text'
            self._send_json({"status": "ok", "rows_loaded": n_rows, "columns": columns, "types": types})
        except Exception as e:
            self._send_error_json(f"Load file error: {e}")

    def _handle_analyze(self, body):
        """Analyze the loaded dataset."""
        try:
            result = execute_analyze()
            self._send_json(result)
        except Exception as e:
            self._send_error_json(f"Analysis error: {e}")

    def _handle_groupby(self, body):
        """Execute GROUP BY."""
        group_col = body.get("group_column", "")
        value_col = body.get("value_column", "")
        metric = body.get("metric", "COUNT")
        if not group_col or not value_col:
            self._send_error_json("Missing 'group_column' or 'value_column'")
            return
        try:
            result = execute_groupby(group_col, value_col, metric)
            self._send_json(result)
        except Exception as e:
            self._send_error_json(str(e))

    def _handle_query(self, body):
        """Execute SQL query."""
        sql = body.get("sql", "").strip()
        page = int(body.get("page", 1))
        page_size = int(body.get("page_size", 100))
        if not sql:
            self._send_error_json("Missing 'sql' field")
            return
        try:
            result, error = execute_query(sql, page, page_size)
            if error:
                status = 408 if "timeout" in error.lower() else 400
                self._send_error_json(error, status)
            else:
                self._send_json(result)
        except ValueError as e:
            self._send_error_json(str(e), 400)
        except Exception as e:
            self._send_error_json(f"Query error: {e}")

    def _handle_bridge_push(self, body):
        """Excel pushes data to bridge buffer (Excel → TaskPane) via file."""
        key = body.get("key", "default")
        columns = body.get("columns", [])
        rows = body.get("rows", [])
        if not columns:
            self._send_error_json("Missing 'columns'")
            return
        bridge_dir = os.path.join(os.path.dirname(_config.get("staticDir", "C:\\NEVEN\\taskpane")), "bridge")
        os.makedirs(bridge_dir, exist_ok=True)
        filepath = os.path.join(bridge_dir, f"{key}.json")
        data = {"columns": columns, "rows": rows, "timestamp": time.time(), "source": "excel"}
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        self._send_json({"status": "ok", "key": key, "rows_pushed": len(rows)})

    def _handle_bridge_write(self, body):
        """TaskPane writes data to bridge buffer (TaskPane → Excel) via file."""
        key = body.get("key", "result")
        data = body.get("data")
        if data is None:
            self._send_error_json("Missing 'data'")
            return
        bridge_dir = os.path.join(os.path.dirname(_config.get("staticDir", "C:\\NEVEN\\taskpane")), "bridge")
        os.makedirs(bridge_dir, exist_ok=True)
        filepath = os.path.join(bridge_dir, f"{key}.json")
        payload = {"data": data, "timestamp": time.time(), "source": "taskpane"}
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
        self._send_json({"status": "ok", "key": key})

    # ── Script endpoint placeholders ─────────────────────────────────────────
    # Full implementations are added in tasks 6.2, 7.1, 7.2, and 7.3.

    def _handle_script(self, lang: str, body: dict):
        """POST /api/{r,python,julia} — execute code via PipeClient.

        Validates the request body, retrieves the PipeClient for *lang*,
        sends the code, converts the Variable result, and returns the
        appropriate JSON response.

        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10,
                      3.11, 3.12, 8.4
        """
        # Req 3.2, 3.3 — validate 'code' field
        code = body.get("code", "")
        if not isinstance(code, str) or not code.strip():
            self._send_json(
                {"status": "error", "message": "Missing 'code' field"},
                400,
            )
            return

        # Req 3.2 — optional timeout_ms
        timeout_ms = body.get("timeout_ms", 60_000)

        # Req 3.10 — engine not running → 503
        try:
            client = self._get_pipe_client(lang)
        except KeyError:
            self._send_json(
                {"status": "error", "message": f"{lang} engine not available"},
                503,
            )
            return

        # Req 3.4 — send code to PipeClient; Req 8.4 — one reconnect on broken pipe
        lines = code.splitlines()
        try:
            try:
                var = client.send_code(lines, wait=True)
            except (OSError, _PipeClientError) as exc:
                # Req 8.4: detect broken pipe — attempt one reconnect
                msg = str(exc)
                if _is_broken_pipe(exc, msg):
                    try:
                        client.close()
                        client.connect()
                        var = client.send_code(lines, wait=True)
                    except Exception:
                        self._send_json(
                            {"status": "error", "message": f"{lang} engine not available"},
                            503,
                        )
                        return
                else:
                    raise
        except _PipeTimeoutError:
            # Req 3.9 — timeout → 408
            self._send_json(
                {"status": "error", "message": "Script execution timed out"},
                408,
            )
            return
        except _PipeClientError as exc:
            # Req 3.8 — PipeClientError → 200 with status: error
            self._send_json(
                {"status": "error", "message": str(exc)},
                200,
            )
            return

        # Convert Variable → JSON response (via variable_to_python)
        self._send_script_result(_variable_to_python(var))

    def _send_script_result(self, result):
        """Dispatch a variable_to_python result to the appropriate JSON response shape.

        Req 3.5 — scalar: {status, type, result, console}
        Req 3.6 — html:   {status, type, html, title, console}
        Req 3.7 — array:  {status, type, columns, rows, console}
        """
        console = ""  # Variable doesn't carry console separately (task spec note)

        if result is None:
            self._send_json({
                "status": "ok",
                "type": "nil",
                "result": None,
                "console": console,
            })
        elif isinstance(result, bool):
            self._send_json({
                "status": "ok",
                "type": "boolean",
                "result": result,
                "console": console,
            })
        elif isinstance(result, int):
            self._send_json({
                "status": "ok",
                "type": "integer",
                "result": result,
                "console": console,
            })
        elif isinstance(result, float):
            self._send_json({
                "status": "ok",
                "type": "real",
                "result": result,
                "console": console,
            })
        elif isinstance(result, str):
            self._send_json({
                "status": "ok",
                "type": "string",
                "result": result,
                "console": console,
            })
        elif isinstance(result, dict) and "html" in result:
            # Req 3.6 — html_content Variable
            self._send_json({
                "status": "ok",
                "type": "html",
                "html": result.get("html", ""),
                "title": result.get("title", ""),
                "console": console,
            })
        elif isinstance(result, dict) and "columns" in result:
            # Req 3.7 — arr Variable
            self._send_json({
                "status": "ok",
                "type": "array",
                "columns": result.get("columns", []),
                "rows": result.get("rows", []),
                "console": console,
            })
        else:
            # Fallback: treat as string
            self._send_json({
                "status": "ok",
                "type": "string",
                "result": str(result),
                "console": console,
            })

    def _handle_rpivot(self, body: dict):
        """POST /api/rpivot — generate RPivot HTML via R.

        1. Parse optional ``max_rows`` (default 10,000).
        2. Probe R engine via ``_probe_pipe``; return 503 if unavailable.
        3. ``SELECT * FROM dataset LIMIT <max_rows>`` via DuckDB; return 400
           if the ``dataset`` table is missing.
        4. Convert rows to a JSON string; build the R code that loads the
           data, creates an rpivotTable widget, saves it as self-contained
           HTML, and returns the HTML string.
        5. Send via ``PipeClient("neven_r").send_code(lines)``; extract the
           HTML from the returned ``Variable`` via ``variable_to_python``.
        6. Return ``{"status": "ok", "type": "html", "html": "..."}``.

        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
        """
        # ── 1. Parse max_rows ────────────────────────────────────────────────
        max_rows = int(body.get("max_rows", 10_000))

        # ── 2. Probe R engine ────────────────────────────────────────────────
        r_pipe = r"\\.\pipe\neven_r"
        if not _probe_pipe(r_pipe):
            self._send_json(
                {"status": "error", "message": "R engine not available for RPivot"},
                503,
            )
            return

        # ── 3. Query DuckDB ──────────────────────────────────────────────────
        try:
            db = _get_db()
            with _db_lock:
                # Verify the table exists first (raises if missing)
                db.execute("SELECT COUNT(*) FROM dataset")
                result = db.execute(
                    f"SELECT * FROM dataset LIMIT {max_rows}"
                )
                col_names = [desc[0] for desc in result.description]
                raw_rows = result.fetchall()
        except Exception as exc:
            err_msg = str(exc)
            # DuckDB raises an error whose message mentions "dataset" when
            # the table is absent.
            if "dataset" in err_msg.lower() or "table" in err_msg.lower():
                self._send_json(
                    {"status": "error", "message": "No dataset loaded — load data first"},
                    400,
                )
                return
            self._send_json({"status": "error", "message": f"DuckDB error: {err_msg}"})
            return

        # ── 4. Build R code ──────────────────────────────────────────────────
        # Convert rows to a list-of-dicts and serialise as JSON.
        rows_as_dicts = [
            {col: (row[i] if row[i] is not None else None)
             for i, col in enumerate(col_names)}
            for row in raw_rows
        ]
        json_str = json.dumps(rows_as_dicts, default=str)
        # Escape single backslashes and single quotes for embedding in R code.
        json_escaped = json_str.replace("\\", "\\\\").replace("'", "\\'")

        r_lines = [
            "if (!requireNamespace('rpivotTable', quietly=TRUE)) stop('rpivotTable required')",
            "if (!requireNamespace('htmlwidgets', quietly=TRUE)) stop('htmlwidgets required')",
            "library(rpivotTable); library(htmlwidgets)",
            f"data <- jsonlite::fromJSON('{json_escaped}')",
            "widget <- rpivotTable(data)",
            "tmp <- tempfile(fileext='.html')",
            "htmlwidgets::saveWidget(widget, tmp, selfcontained=TRUE)",
            "readLines(tmp) |> paste(collapse='\\n')",
        ]

        # ── 5. Send to R engine ──────────────────────────────────────────────
        try:
            client = self._get_pipe_client("r")
        except KeyError:
            self._send_json(
                {"status": "error", "message": "R engine not available for RPivot"},
                503,
            )
            return

        try:
            # Lazily connect if the client supports it
            if hasattr(client, "connect") and getattr(client, "_handle", None) is None:
                client.connect()
            var = client.send_code(r_lines)
        except Exception as exc:
            from pipe_client import PipeClientError, PipeTimeoutError  # noqa: PLC0415
            if isinstance(exc, PipeTimeoutError):
                self._send_json(
                    {"status": "error", "message": "Script execution timed out"},
                    408,
                )
                return
            if isinstance(exc, PipeClientError):
                err_text = str(exc)
                if "rpivotTable required" in err_text or "htmlwidgets required" in err_text:
                    self._send_json(
                        {"status": "error",
                         "message": "R packages rpivotTable and htmlwidgets are required"},
                    )
                    return
                self._send_json({"status": "error", "message": err_text})
                return
            self._send_json({"status": "error", "message": str(exc)})
            return

        # ── 6. Extract HTML and return ───────────────────────────────────────
        try:
            # Import here to avoid circular issues at module load time.
            from pipe_client import variable_to_python, PipeClientError  # noqa: PLC0415
            result_val = variable_to_python(var)
        except Exception as exc:
            self._send_json({"status": "error", "message": str(exc)})
            return

        # variable_to_python returns dict(html=..., title=...) for html_content
        # and a plain str when R returns a character string directly.
        if isinstance(result_val, dict) and "html" in result_val:
            html_content = result_val["html"]
        elif isinstance(result_val, str):
            html_content = result_val
        else:
            self._send_json(
                {"status": "error", "message": "Unexpected result type from R engine"}
            )
            return

        self._send_json({"status": "ok", "type": "html", "html": html_content})

    def _handle_engines(self):
        """GET /api/engines — pipe-probe each language engine.

        Probes each language's Named Pipe using :func:`_probe_pipe` and returns
        a JSON object reflecting real-time availability.

        Returns:
            JSON ``{"r": bool, "python": bool, "julia": bool}`` where each value
            is ``True`` iff a CreateFile probe on ``\\\\.\\pipe\\neven_{lang}``
            succeeded (Requirements 8.1, 8.2).
        """
        self._send_json({
            "r":      _probe_pipe(r"\\.\pipe\neven_r"),
            "python": _probe_pipe(r"\\.\pipe\neven_python"),
            "julia":  _probe_pipe(r"\\.\pipe\neven_julia"),
        })

    def _handle_functions(self):
        """GET /api/functions — list registered functions per language.

        For each language in {r, python, julia}:
          - If a PipeClient factory is registered, call
            ``send_function_call("list-functions", [], target=system)`` on a
            fresh client, convert the returned Variable via
            ``variable_to_python``, and build a list of
            ``{name, description, arguments}`` dicts from the arr result.
          - If the language has no factory (KeyError) or a
            ``PipeClientError`` is raised, return ``[]`` for that language.

        Returns
        -------
        JSON: ``{"status": "ok", "languages": {"r": [...], "python": [...],
                 "julia": [...]}}``

        Requirements: 7.3, 7.4
        """
        # Import variable_to_python and the target enum at call time so that
        # the module is importable even when variable_pb2 is not on PYTHONPATH.
        try:
            from pipe_client import variable_to_python, PipeClientError  # type: ignore[import]
            import variable_pb2  # type: ignore[import]
            _system_target = variable_pb2.CallTarget.Value("system")
        except ImportError:
            # If pipe_client / variable_pb2 are not available, return all empty.
            self._send_json(
                {"status": "ok", "languages": {"r": [], "python": [], "julia": []}}
            )
            return

        languages = {}
        for lang in ("r", "python", "julia"):
            try:
                client = self._get_pipe_client(lang)
                var = client.send_function_call(
                    "list-functions",
                    [],
                    target=_system_target,
                )
                result = variable_to_python(var)
            except (KeyError, PipeClientError):
                languages[lang] = []
                continue
            except Exception:
                languages[lang] = []
                continue

            # Build list of {name, description, arguments} from the arr result.
            # variable_to_python returns {"columns": [...], "rows": [[...],...]}
            # for arr variables.
            func_list = []
            if isinstance(result, dict) and "columns" in result and "rows" in result:
                cols = result["columns"]
                # Locate column indices (case-insensitive, with fallback)
                col_lower = [c.lower() for c in cols]
                try:
                    idx_name = col_lower.index("name")
                except ValueError:
                    idx_name = 0
                try:
                    idx_desc = col_lower.index("description")
                except ValueError:
                    idx_desc = 1 if len(cols) > 1 else 0
                try:
                    idx_args = col_lower.index("arguments")
                except ValueError:
                    idx_args = 2 if len(cols) > 2 else None

                for row in result["rows"]:
                    entry = {
                        "name": row[idx_name] if idx_name < len(row) else "",
                        "description": row[idx_desc] if idx_desc < len(row) else "",
                        "arguments": row[idx_args] if (idx_args is not None and idx_args < len(row)) else [],
                    }
                    func_list.append(entry)

            languages[lang] = func_list

        self._send_json({"status": "ok", "languages": languages})


# ─── Bridge Buffer ────────────────────────────────────────────────────────────

_bridge_buffer = {}


# ─── Server Startup ───────────────────────────────────────────────────────────

def start_server(config=None):
    """Start the HTTP server on a daemon thread. Returns (thread, port) or None.

    Args:
        config: Optional dict that overrides DEFAULT_CONFIG values.  May include
                ``pipe_client_factory``: a ``dict[str, Callable[[], PipeClient]]``
                that maps language names ("r", "python", "julia") to zero-argument
                callables returning a connected PipeClient.  When provided,
                NEVENHandler._get_pipe_client() uses these factories instead of
                raising KeyError, enabling unit tests and start_studio.py to inject
                real or mock clients without modifying handler code (Req 9.5).
    """
    global _server_instance, _server_port, _config

    if config:
        _config = config
    else:
        _config = DEFAULT_CONFIG.copy()

    if not _config.get("enabled", True):
        print("[NEVEN HTTP] TaskPane disabled in config — server not started", file=sys.stderr)
        return None

    ports = [_config.get("port", 5555), _config.get("fallbackPort", 5556)]

    server = None
    for port in ports:
        try:
            server = HTTPServer(('127.0.0.1', port), NEVENHandler)
            _server_port = port
            print(f"[NEVEN HTTP] Bound to localhost:{port}", file=sys.stderr)
            break
        except OSError as e:
            print(f"[NEVEN HTTP] Port {port} unavailable: {e}", file=sys.stderr)

    if server is None:
        print("[NEVEN HTTP] FATAL: Cannot bind HTTP server on any port", file=sys.stderr)
        return None

    # HTTPS setup (if cert available)
    cert_path = _config.get("certPath", "")
    key_path = _config.get("keyPath", "")
    if cert_path and key_path and os.path.isfile(cert_path) and os.path.isfile(key_path):
        try:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
            print(f"[NEVEN HTTP] HTTPS enabled (cert: {cert_path})", file=sys.stderr)
        except Exception as e:
            print(f"[NEVEN HTTP] HTTPS setup failed: {e} — running HTTP only", file=sys.stderr)
    else:
        print("[NEVEN HTTP] No cert configured — running HTTP (Task Pane may require HTTPS)", file=sys.stderr)

    _server_instance = server

    # Inicializar Package Manager Service
    global _pkg_service, _PKG_SERVICE_AVAILABLE
    if _PKG_IMPORT_OK:
        try:
            factory = _config.get("pipe_client_factory", {})
            def _get_pipe_for_pkg(lang: str):
                if lang in factory:
                    return factory[lang]()
                raise KeyError(f"No factory for {lang}")
            _pkg_service = _init_pkg_service(_get_pipe_for_pkg)
            _PKG_SERVICE_AVAILABLE = True
            print("[NEVEN HTTP] Package Manager Service iniciado", file=sys.stderr)
        except Exception as e:
            print(f"[NEVEN HTTP] Package Manager Service no disponible: {e}", file=sys.stderr)

    # Start on daemon thread
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[NEVEN HTTP] Server running on thread (port {_server_port})", file=sys.stderr)

    return thread, _server_port


def stop_server():
    """Stop the HTTP server gracefully."""
    global _server_instance
    if _server_instance:
        _server_instance.shutdown()
        _server_instance = None
        print("[NEVEN HTTP] Server stopped", file=sys.stderr)
