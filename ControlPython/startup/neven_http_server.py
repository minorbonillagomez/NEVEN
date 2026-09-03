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
#   GET  /api/kg/stats                  → Estadísticas del Knowledge Graph
#   GET  /api/kg/method/{function_id}   → Nodo Method + supuestos + funciones R
#   GET  /api/kg/profile                → Perfil automático del dataset en DuckDB
#   GET  /api/kg/diagnose/{function_id} → Plan metodológico completo
#   POST /api/buklo/save                → Guarda proyecto activo como .buklo
#   POST /api/buklo/load                → Abre un .buklo y restaura el estado
#   GET  /api/buklo/status              → Estado del proyecto actual
#   POST /api/ai/run_suggestion         → Ejecuta análisis propuesto por LLM/servicio externo
#   GET  /api/export/capabilities       → Detecta Quarto, pdflatex, xelatex disponibles
#   POST /api/export/generate           → LLM genera informe .tex o .qmd
#   POST /api/export/compile            → Compila .tex/.qmd a PDF
#   POST /api/ai/context                → Recibe contexto de Excel (datos + resultados)
#   GET  /api/ai/context/pending        → Retorna contexto pendiente de Excel para el Tab IA

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

# Ontology Engine — Knowledge Graph econométrico
try:
    from ontology_engine import get_engine as _get_ontology_engine  # type: ignore
    _ONTOLOGY_AVAILABLE = True
except ImportError:
    _ONTOLOGY_AVAILABLE = False
    def _get_ontology_engine(*args, **kwargs):  # type: ignore
        return None

# Buklo Manager — formato de proyecto persistente .buklo
try:
    from buklo_manager import (  # type: ignore
        get_buklo_manager as _get_buklo_manager,
        set_current_path  as _buklo_set_path,
        get_current_path  as _buklo_get_path,
    )
    _BUKLO_AVAILABLE = True
except ImportError:
    _BUKLO_AVAILABLE = False
    def _get_buklo_manager():      return None   # type: ignore
    def _buklo_set_path(p): pass                 # type: ignore
    def _buklo_get_path():         return None   # type: ignore

# ── Estado global del contexto Excel → Tab IA ─────────────────────────────────
# Almacena el último contexto publicado por =NEVEN.IA.Contexto()
# Se consume (y borra) cuando el Tab IA lo recoge via GET /api/ai/context/pending
import threading as _threading
_excel_context_lock    = _threading.Lock()
_excel_context_pending: dict | None = None   # {text, timestamp, source}

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
    "bukloDir":      r"C:\NEVEN\projects",   # Directorio de proyectos .buklo
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

        # ── AIService URL — para que el taskpane sepa si usar servicio externo ──
        if path == 'api/ai/service-url':
            config_path = os.path.join(
                os.path.dirname(_config.get("staticDir", r"C:\NEVEN\taskpane")), "..",
                "neven-config.json"
            )
            if not os.path.isfile(config_path):
                config_path = r"C:\NEVEN\neven-config.json"
            try:
                with open(config_path, "r", encoding="utf-8") as _f:
                    full_cfg = json.load(_f)
                svc = full_cfg.get("AIService", {})
                self._send_json({
                    "status":  "ok",
                    "enabled": svc.get("enabled", False),
                    "url":     svc.get("url", ""),
                })
            except Exception:
                self._send_json({"status": "ok", "enabled": False, "url": ""})
            return

        # ── Ontology / Knowledge Graph endpoints ──────────────────────────────
        if path.startswith('api/kg/'):
            self._handle_kg(path[7:])  # pasa la parte después de 'api/kg/'
            return

        # ── Buklo status (GET) ────────────────────────────────────────────────
        if path == 'api/buklo/status':
            if not _BUKLO_AVAILABLE:
                self._send_json({"status": "unavailable"})
                return
            mgr = _get_buklo_manager()
            self._send_json(mgr.status(_buklo_get_path()) if mgr else {"status": "unavailable"})
            return

        if path == 'api/buklo/list':
            if not _BUKLO_AVAILABLE:
                self._send_json({"status": "unavailable", "projects": []})
                return
            mgr = _get_buklo_manager()
            buklo_dir = _config.get("bukloDir", r"C:\NEVEN\projects")
            projects = mgr.list_projects(buklo_dir) if mgr else []
            self._send_json({"status": "ok", "projects": projects})
            return

        # ── Export capabilities (GET) ─────────────────────────────────────────
        if path == 'api/export/capabilities':
            self._handle_export_capabilities()
            return

        # ── Contexto Excel → Tab IA (GET — consume el contexto pendiente) ──────
        if path == 'api/ai/context/pending':
            global _excel_context_pending
            with _excel_context_lock:
                ctx = _excel_context_pending
                _excel_context_pending = None   # consumido
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
        # No cachear JS/CSS — el browser siempre pide la versión en disco
        if ext in ('.js', '.css'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
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
        elif path == 'api/packages/install':
            self._handle_pkg_install(body)
        elif path == 'api/buklo/save':
            self._handle_buklo_save(body)
        elif path == 'api/buklo/load':
            self._handle_buklo_load(body)
        elif path == 'api/ai/run_suggestion':
            self._handle_ai_run_suggestion(body)
        elif path == 'api/ai/context':
            self._handle_ai_context(body)
        elif path == 'api/export/generate':
            self._handle_export_generate(body)
        elif path == 'api/export/compile':
            self._handle_export_compile(body)
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
            # Detectar si el contexto incluye sección metodológica (del botón + Método)
            has_method_context  = "=== CONTEXTO METODOLÓGICO ===" in context
            has_dataset_context = "Dataset:" in context or "filas" in context
            has_results_context = "=== RESULTADOS DEL ANÁLISIS ===" in context
            has_history_context = "=== HISTORIAL DE MODELOS ===" in context
            has_excel_context   = "=== DATOS DE EXCEL ===" in context

            # Instrucciones de formato comunes a todas las personas
            _fmt = (
                "Responde siempre en español a menos que el usuario escriba en otro idioma. "
                "Usa Markdown para formatear tu respuesta. "
                "Para fórmulas matemáticas usa SIEMPRE delimitadores Markdown estándar: "
                "$$...$$ para fórmulas en bloque y $...$ para fórmulas inline. "
                "NUNCA uses \\(...\\) ni \\[...\\] ni ninguna otra notación LaTeX."
            )

            # Instrucción de sugerencias ejecutables (cuando hay resultados o historial)
            _run_hint = (
                "Cuando sugieras un nuevo análisis o corrección metodológica, "
                "incluye un bloque ```neven-run con el JSON de la llamada. "
                "El schema EXACTO es: "
                "{\"function_id\": string, \"language\": \"r\"|\"python\"|\"julia\", "
                "\"column_roles\": {\"Y\": [...], \"X\": [...], \"Z\": [...]}, "
                "\"parameters\": {}, \"context_note\": string}. "
                "IMPORTANTE: language SIEMPRE debe ser \"r\", \"python\" o \"julia\" en minúsculas. "
                "Los function_id disponibles para R son: RG_Lineal, RG_2SLS, RG_Logistica, "
                "RG_Poisson, RG_Tobit, RG_HECKIT, RG_DatosPanel, RG_FGLS, RG_Newey_West, "
                "RG_RESET, ST_VAR, ST_ECM. "
                "Usa EXACTAMENTE uno de estos IDs — no inventes nombres nuevos. "
                "Para RG_2SLS los roles son: Y (dependiente), Endo (endógenas), "
                "Exo (controles exógenos, opcional), Instru (instrumentos externos Z). "
                "Para RG_Lineal los roles son: Y (dependiente), X (independientes). "
                "Usa los nombres de roles EXACTAMENTE como están — no uses 'Z' en lugar de 'Instru'. "
                "El usuario podrá ejecutarlo con un clic desde el chat. "
                "Si el usuario pide EXPLÍCITAMENTE instalar un paquete, genera un bloque "
                "```neven-install con el JSON: "
                "{\"package\": \"nombre_paquete\", \"language\": \"r\"|\"python\"|\"julia\", "
                "\"context_note\": \"para qué se necesita\"}. "
                "NUNCA sugiereas instalar paquetes proactivamente — solo bajo solicitud explícita del usuario. "
            ) if (has_results_context or has_history_context) else ""

            if has_history_context:
                # Historial de múltiples modelos — persona de comparación y evolución
                sys_content = (
                    "Eres NEVEN Assistant, un econometrista experto. "
                    "Tienes acceso al historial completo de modelos estimados en esta sesión. "
                    "Tu tarea principal es comparar especificaciones, coeficientes y métricas "
                    "entre los modelos del historial y razonar sobre la evolución del análisis. "
                    "Cuando compares, cita los números reales de cada modelo: "
                    "  - Si el coeficiente cambió, di cuánto y qué implica (ej: sesgo de endogeneidad). "
                    "  - Si las métricas mejoraron/empeoraron, explica por qué. "
                    "  - Si hay advertencias metodológicas, vincúlalas con el cambio de especificación. "
                    "Basa tu razonamiento en la ontología econométrica de NEVEN "
                    "(Wooldridge, Hanck et al., MIT 14.382/14.384/14.387). "
                    "Cita el libro/capítulo cuando sea relevante. "
                    + _run_hint +
                    f"Historial de modelos estimados:\n\n{context}\n\n"
                    + _fmt
                )
            elif has_results_context and has_method_context:
                # Máximo contexto: resultados reales + método ontológico
                sys_content = (
                    "Eres NEVEN Assistant, un econometrista experto. "
                    "Tienes acceso a la estimación real del usuario: coeficientes, "
                    "p-valores, R², tests diagnósticos y advertencias metodológicas. "
                    "Responde sobre ESTE modelo específico, no en abstracto. "
                    "Tu base de conocimiento incluye la ontología econométrica de NEVEN "
                    "(Wooldridge, Hanck et al., MIT 14.382/14.384/14.387). "
                    "Si detectas problemas (instrumento débil, heterocedasticidad, "
                    "endogeneidad), cita el libro/capítulo y propone la corrección concreta. "
                    + _run_hint +
                    f"Contexto completo del usuario:\n\n{context}\n\n"
                    + _fmt
                )
            elif has_results_context and has_dataset_context:
                # Resultados + dataset (sin método ontológico)
                sys_content = (
                    "Eres NEVEN Assistant, un analista de datos experto. "
                    "Tienes acceso a los resultados reales del análisis del usuario "
                    "y a la estructura de sus datos. "
                    "Responde sobre ESTE modelo específico. "
                    + _run_hint +
                    f"Contexto del usuario:\n\n{context}\n\n"
                    + _fmt
                )
            elif has_results_context:
                # Solo resultados (sin dataset ni método)
                sys_content = (
                    "Eres NEVEN Assistant, un econometrista experto. "
                    "Tienes acceso a los resultados del análisis del usuario. "
                    "Responde sobre ESTE modelo específico. "
                    + _run_hint +
                    f"Resultados del análisis:\n\n{context}\n\n"
                    + _fmt
                )
            elif has_method_context and has_dataset_context:
                # Contexto completo: dataset + método ontológico (sin resultados)
                sys_content = (
                    "Eres NEVEN Assistant, un econometrista y analista de datos experto. "
                    "El usuario trabaja con NEVEN, un add-in de Excel que integra R, Julia y Python. "
                    "Tu base de conocimiento incluye la ontología econométrica de NEVEN, "
                    "que cubre métodos desde Wooldridge y Hanck et al. hasta los cursos MIT 14.382/14.384/14.387 "
                    "(Angrist, Chernozhukov, Mikusheva). "
                    "Cuando detectes posibles problemas metodológicos, cita el libro y capítulo relevante. "
                    f"Contexto actual del usuario:\n\n{context}\n\n"
                    "Sé preciso y pedagógico: explica el razonamiento, no solo el resultado. "
                    + _fmt
                )
            elif has_method_context:
                # Solo contexto metodológico
                sys_content = (
                    "Eres NEVEN Assistant, un econometrista experto especializado en "
                    "R, Julia y Python aplicados al análisis de datos. "
                    "Tu base de conocimiento incluye la ontología econométrica de NEVEN "
                    "(Wooldridge, Hanck et al., MIT 14.382/14.384/14.387). "
                    "Cuando cites supuestos, métodos o tests, menciona la referencia "
                    "bibliográfica específica (libro, capítulo). "
                    f"Marco metodológico activo del usuario:\n\n{context}\n\n"
                    "Orienta al usuario en el razonamiento metodológico, "
                    "no solo en la ejecución técnica. "
                    + _fmt
                )
            elif has_excel_context:
                # Datos y/o resultados directos de la hoja de cálculo Excel
                # Enviados por =NEVEN.IA.Contexto(datos_rango, resultados_rango)
                sys_content = (
                    "Eres NEVEN Assistant, un analista de datos experto. "
                    "El usuario ha enviado datos directamente desde su hoja de cálculo de Excel. "
                    "Tienes acceso a los datos reales con los que está trabajando: "
                    "variables, valores y estructura de la tabla. "
                    "Responde sobre ESTOS datos específicos, no en abstracto. "
                    "Si detectas patrones, valores atípicos o relaciones relevantes, coméntalos. "
                    "Cuando sugieras un análisis, sé concreto: menciona las columnas por su nombre real. "
                    + _run_hint +
                    f"Datos de la hoja de cálculo del usuario:\n\n{context}\n\n"
                    + _fmt
                )
            else:
                # Solo contexto de dataset (genérico)
                sys_content = (
                    "Eres NEVEN Assistant, un analista de datos experto. "
                    "El usuario está trabajando con NEVEN, "
                    "un add-in de Excel con R, Julia y Python. "
                    f"Contexto del dataset actual:\n\n{context}\n\n"
                    + _fmt
                )

            sys_msg = {"role": "system", "content": sys_content}
            messages = [sys_msg] + [m for m in messages if m.get("role") != "system"]
        else:
            # Sin contexto adjunto — system message mínimo solo para instrucciones de formato
            _fmt_instructions = (
                "Eres NEVEN Assistant, un analista de datos y econometrista experto. "
                "Responde siempre en español a menos que el usuario escriba en otro idioma. "
                "Usa Markdown para formatear tu respuesta. "
                "Para fórmulas matemáticas usa SIEMPRE delimitadores Markdown estándar: "
                "$$...$$ para fórmulas en bloque y $...$ para fórmulas inline. "
                "NUNCA uses \\(...\\) ni \\[...\\] ni ninguna otra notación LaTeX."
            )
            # Solo inyectar si no hay ya un system message del usuario
            if not any(m.get("role") == "system" for m in messages):
                messages = [{"role": "system", "content": _fmt_instructions}] + messages

        # ── HTTP request to LLM ───────────────────────────────────────────────
        headers = {"Content-Type": "application/json"}
        if api_key and provider not in ("ollama", "lmstudio"):
            headers["Authorization"] = f"Bearer {api_key}"

        # OpenRouter requiere headers adicionales para identificar la app
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://neven-studio.app"
            headers["X-Title"]      = "NEVEN Studio"

        # Azure OpenAI: usa api-key en header, construye endpoint con deployment + api-version
        if provider == "azure":
            headers.pop("Authorization", None)          # Azure no usa Bearer
            headers["api-key"] = api_key                # Header propio de Azure
            api_version = ai.get("apiVersion", "2024-02-15-preview")
            # endpoint en config debe ser la base: https://<resource>.openai.azure.com
            # El path completo incluye el deployment y la versión
            azure_base = endpoint.rstrip("/")
            endpoint = (
                f"{azure_base}/openai/deployments/{model}"
                f"/chat/completions?api-version={api_version}"
            )
            # Azure ignora el campo "model" en el body — el modelo va en la URL
            req_body = json.dumps({
                "messages":    messages,
                "max_tokens":  max_tokens,
                "temperature": temperature,
            }, ensure_ascii=False).encode("utf-8")
        else:
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
            # Log del request para diagnóstico
            import datetime as _dt_log
            _log_path = r"C:\NEVEN\ai_chat_debug.log"
            try:
                with open(_log_path, "a", encoding="utf-8") as _lf:
                    _lf.write(f"\n[{_dt_log.datetime.now()}] POST {endpoint}\n")
                    _lf.write(f"  body_size={len(req_body)} bytes  timeout={timeout_sec}s\n")
                    ctx_preview = context[:200].replace('\n', '\\n') if context else "(sin contexto)"
                    _lf.write(f"  context_preview: {ctx_preview}\n")
            except Exception:
                pass  # el log nunca debe abortar el handler

            with _url_req.urlopen(req, timeout=timeout_sec) as resp:
                raw_body = resp.read().decode("utf-8")
                data = json.loads(raw_body)

            try:
                with open(_log_path, "a", encoding="utf-8") as _lf:
                    finish = data.get('choices', [{}])[0].get('finish_reason', '?')
                    _lf.write(f"  => OK finish_reason={finish}\n")
            except Exception:
                pass
        except _url_req.HTTPError as exc:
            # Error HTTP con body — leer el mensaje de error del proveedor
            try:
                err_body = exc.read().decode("utf-8")
                try:
                    err_json = json.loads(err_body)
                    # Azure retorna {"error": {"code": ..., "message": ...}}
                    err_detail = (
                        err_json.get("error", {}).get("message")
                        or err_json.get("message")
                        or err_body[:300]
                    )
                except Exception:
                    err_detail = err_body[:300]
            except Exception:
                err_detail = str(exc)
            self._send_error_json(
                f"El proveedor LLM ({provider}) retornó HTTP {exc.code}: {err_detail}",
                502
            )
            with open(r"C:\NEVEN\ai_chat_debug.log", "a", encoding="utf-8") as _lf:
                _lf.write(f"  => HTTPError {exc.code}: {err_detail[:200]}\n")
            return
        except _url_req.URLError as exc:
            reason = str(exc.reason) if hasattr(exc, "reason") else str(exc)
            with open(r"C:\NEVEN\ai_chat_debug.log", "a", encoding="utf-8") as _lf:
                _lf.write(f"  => URLError: {reason}\n")
            self._send_error_json(
                f"No se pudo conectar al LLM ({provider}). "
                f"Verifique que {endpoint} esté activo. Detalle: {reason}",
                503
            )
            return
        except Exception as exc:
            with open(r"C:\NEVEN\ai_chat_debug.log", "a", encoding="utf-8") as _lf:
                _lf.write(f"  => Exception: {type(exc).__name__}: {exc}\n")
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

    # ── Ontology / Knowledge Graph handler ────────────────────────────────────

    def _handle_kg(self, sub_path: str):
        """
        Router interno para todos los endpoints GET /api/kg/*.

        Rutas manejadas:
          method/{function_id}   → nodo Method + supuestos + funciones R + alternativas
          stats                  → estadísticas del grafo cargado
          profile                → perfil automático del dataset activo en DuckDB
          diagnose/{function_id} → plan metodológico completo (usa perfil implícito)
        """
        engine = _get_ontology_engine() if _ONTOLOGY_AVAILABLE else None

        # ── GET /api/kg/stats ─────────────────────────────────────────────────
        if sub_path == "stats":
            if engine is None:
                self._send_json({"status": "unavailable", "loaded": False,
                                 "n_nodes": 0, "n_edges": 0})
            else:
                self._send_json({"status": "ok", **engine.stats})
            return

        # ── GET /api/kg/method/{function_id} ──────────────────────────────────
        if sub_path.startswith("method/"):
            function_id = sub_path[7:].strip("/")
            if not function_id:
                self._send_error_json("Falta el function_id", 400)
                return

            if engine is None or not engine.is_loaded:
                self._send_json({
                    "status": "ok",
                    "found": False,
                    "function_id": function_id,
                    "message": "OntologyEngine no disponible",
                })
                return

            method_node = engine.get_method_node(function_id)

            if method_node is None:
                self._send_json({
                    "status": "ok",
                    "found": False,
                    "function_id": function_id,
                })
                return

            method_id   = method_node["id"]
            assumptions = engine.get_assumptions(method_id)
            concepts    = engine.get_concepts(method_id)
            r_functions = engine.get_r_functions(method_id)
            r_packages  = engine.get_r_packages(method_id)
            datasets    = engine.get_datasets(method_id)
            alternatives = engine.get_alternatives(method_id)

            self._send_json({
                "status":      "ok",
                "found":       True,
                "function_id": function_id,
                "method":      engine.serialize_for_api(method_node),
                "assumptions": [engine.serialize_for_api(a) for a in assumptions],
                "concepts":    [engine.serialize_for_api(c) for c in concepts],
                "r_functions": [engine._serialize_r_function(f) for f in r_functions],
                "r_packages":  [engine.serialize_for_api(p) for p in r_packages],
                "datasets":    [engine.serialize_for_api(d) for d in datasets],
                "alternatives": [
                    {"id": a["id"],
                     "name": a.get("properties", {}).get("name", a["id"])}
                    for a in alternatives
                ],
            })
            return

        # ── GET /api/kg/profile ───────────────────────────────────────────────
        if sub_path == "profile":
            try:
                profile = self._build_dataset_profile()
                self._send_json({"status": "ok", "profile": profile})
            except Exception as exc:
                self._send_json({
                    "status": "ok",
                    "profile": {},
                    "message": f"No se pudo perfilar el dataset: {exc}",
                })
            return

        # ── GET /api/kg/diagnose/{function_id} ────────────────────────────────
        if sub_path.startswith("diagnose/"):
            function_id = sub_path[9:].strip("/")
            if not function_id:
                self._send_error_json("Falta el function_id", 400)
                return

            if engine is None or not engine.is_loaded:
                self._send_json({
                    "status": "unavailable",
                    "function_id": function_id,
                })
                return

            method_node = engine.get_method_node(function_id)
            if method_node is None:
                self._send_json({
                    "status": "ok",
                    "found": False,
                    "function_id": function_id,
                })
                return

            try:
                profile = self._build_dataset_profile()
            except Exception:
                profile = {}

            plan = engine.build_diagnostic_plan(method_node["id"], profile)
            self._send_json({
                "status":      "ok",
                "found":       True,
                "function_id": function_id,
                "plan":        plan,
            })
            return

        # Ruta no reconocida
        self._send_error_json(f"Endpoint /api/kg/{sub_path} no existe", 404)

    def _build_dataset_profile(self) -> dict:
        """
        Genera el perfil automático del dataset activo en DuckDB.
        Se ejecuta con una sola pasada sobre los metadatos de DuckDB.

        Returns:
            dict con dimensiones, tipos de columnas y dimensiones detectadas.
        """
        db = _get_db()
        with _db_lock:
            try:
                cols_info = db.execute("DESCRIBE dataset").fetchall()
                n_rows    = db.execute("SELECT COUNT(*) FROM dataset").fetchone()[0]
            except Exception:
                return {"n_rows": 0, "n_cols": 0, "columns": [],
                        "has_time_dimension": False,
                        "has_panel_structure": False,
                        "has_spatial_dimension": False,
                        "outcome_candidates": [],
                        "numeric_cols": [], "categorical_cols": []}

        columns = []
        numeric_cols = []
        categorical_cols = []

        # Heurísticas de detección de estructura
        col_names_lower = [row[0].lower() for row in cols_info]

        _TIME_KEYWORDS    = {"year", "year_", "anyo", "año", "date", "time",
                              "periodo", "period", "t", "fecha", "mes", "month"}
        _PANEL_ID_KW      = {"id", "cod", "code", "entity", "state", "country",
                              "pais", "estado", "region", "firm", "empresa"}
        _SPATIAL_KW       = {"lat", "lon", "lng", "latitude", "longitude",
                              "x", "y", "coord", "geometry", "shape", "geom"}

        has_time    = any(c in _TIME_KEYWORDS for c in col_names_lower)
        has_id_col  = any(c in _PANEL_ID_KW for c in col_names_lower)
        has_panel   = has_time and has_id_col
        has_spatial = any(c in _SPATIAL_KW for c in col_names_lower)

        for row in cols_info:
            col_name = row[0]
            col_type = row[1].upper() if len(row) > 1 else "VARCHAR"
            is_num   = any(t in col_type for t in
                           ("INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC",
                            "BIGINT", "REAL", "HUGEINT", "TINYINT", "SMALLINT"))
            columns.append({"name": col_name, "type": col_type,
                             "numeric": is_num})
            if is_num:
                numeric_cols.append(col_name)
            else:
                categorical_cols.append(col_name)

        return {
            "n_rows":               n_rows,
            "n_cols":               len(columns),
            "columns":              columns,
            "numeric_cols":         numeric_cols,
            "categorical_cols":     categorical_cols,
            "has_time_dimension":   has_time,
            "has_panel_structure":  has_panel,
            "has_spatial_dimension": has_spatial,
            "outcome_candidates":   numeric_cols[:3] if numeric_cols else [],
        }

    # ── AI context desde Excel ────────────────────────────────────────────────

    def _handle_ai_context(self, body: dict):
        """POST /api/ai/context — recibe contexto de Excel publicado por =NEVEN.IA.Contexto().

        Body (enviado desde RJ_IA_Contexto en el XLL):
        {
            dataset_text   (str)  — datos serializados como tabla de texto
            columns        (list) — nombres de columnas
            results_text   (str)  — resultados del modelo como texto plano
            formula        (str)  — ej: "=R.MR_Lineal(A1:A100, B1:D100)"
            n_rows         (int)  — número de observaciones
            source         (str)  — "excel" siempre
        }

        Almacena el contexto en _excel_context_pending para que el Tab IA
        lo recoja via GET /api/ai/context/pending al abrir la ventana.
        """
        global _excel_context_pending

        dataset_text  = body.get("dataset_text",  "").strip()
        results_text  = body.get("results_text",  "").strip()
        columns       = body.get("columns",       [])
        formula       = body.get("formula",       "")
        n_rows        = body.get("n_rows",        0)

        if not dataset_text and not results_text:
            self._send_error_json("Falta dataset_text o results_text.", 400)
            return

        # Construir texto de contexto estructurado con los mismos marcadores
        # que usa _aiAttachResults() en el Tab IA
        import datetime as _dt
        lines = ["=== CONTEXTO DESDE EXCEL ===", ""]

        if formula:
            lines.append(f"Fórmula activa: {formula}")
        if columns:
            lines.append(f"Variables: {', '.join(str(c) for c in columns)}")
        if n_rows:
            lines.append(f"Observaciones: {n_rows}")
        lines.append("")

        if dataset_text:
            lines.append("--- Datos (muestra) ---")
            lines.append(dataset_text[:1500])
            lines.append("")

        if results_text:
            lines.append("--- Resultados del modelo ---")
            lines.append(results_text[:2000])
            lines.append("")

        lines.append("IMPORTANTE: usa EXACTAMENTE los nombres de variables de la lista anterior.")

        context_text = "\n".join(lines).strip()

        with _excel_context_lock:
            _excel_context_pending = {
                "text":      context_text,
                "timestamp": _dt.datetime.utcnow().isoformat() + "Z",
                "source":    "excel",
                "columns":   columns,
                "formula":   formula,
                "n_rows":    n_rows,
            }

        self._send_json({
            "status":  "ok",
            "message": f"Contexto almacenado ({len(context_text)} chars). Abre el Agente IA en el ribbon.",
        })

    # ── AI run_suggestion endpoint ────────────────────────────────────────────

    def _handle_ai_run_suggestion(self, body: dict):
        """POST /api/ai/run_suggestion — ejecuta un análisis propuesto por el LLM
        o un servicio externo. Reutiliza datalab_handler.handle_run internamente.

        Body: {
            function_id   (str, required)
            language      (str, default: "r")
            column_roles  (dict, required)
            parameters    (dict, optional)
            filter_clause (str, optional)
            source        (str, optional) — "ai_suggestion" | "external_api" | "user" | "script"
            context_note  (str, optional) — justificación en texto libre
        }

        Retorna: igual que /api/datalab/run + campos source y context_note.
        Es intencionalmente idéntico a /api/datalab/run para permitir
        invocación desde cualquier servicio externo con el mismo schema.
        """
        if not _DATALAB_AVAILABLE:
            self._send_error_json("DataLab no disponible", 503)
            return

        # Normalizar language: el LLM puede enviar "es", "español", "R", etc.
        _LANG_MAP = {
            "r": "r", "R": "r", "es": "r", "español": "r",
            "python": "python", "Python": "python", "py": "python",
            "julia": "julia", "Julia": "julia", "jl": "julia",
        }
        if "language" in body:
            body["language"] = _LANG_MAP.get(
                str(body["language"]).strip(), "r"
            )

        # Normalizar column_roles: el LLM puede usar alias distintos a los del sidecar
        # Mapa: alias_del_llm → nombre_real_del_rol_en_el_sidecar
        if "column_roles" in body and isinstance(body["column_roles"], dict):
            _ROLE_ALIASES = {
                # RG_2SLS: instrumentos
                "Z":           "Instru",
                "z":           "Instru",
                "IV":          "Instru",
                "instrument":  "Instru",
                "instruments": "Instru",
                "Instrument":  "Instru",
                "Instruments": "Instru",
                # RG_2SLS: endógenas
                "Endo":        "Endo",
                "endogena":    "Endo",
                "endógena":    "Endo",
                "endog":       "Endo",
                # RG_2SLS: exógenas de control
                "Exo":         "Exo",
                "controls":    "Exo",
                "control":     "Exo",
                "exogena":     "Exo",
            }
            normalized_roles = {}
            for role_key, cols in body["column_roles"].items():
                mapped = _ROLE_ALIASES.get(role_key, role_key)
                normalized_roles[mapped] = cols
            body["column_roles"] = normalized_roles

        # Validar source
        _VALID_SOURCES = {"user", "ai_suggestion", "external_api", "script"}
        source       = body.get("source", "external_api")
        context_note = body.get("context_note", "").strip()

        if source not in _VALID_SOURCES:
            self._send_error_json(
                f"source inválido: '{source}'. "
                f"Valores permitidos: {sorted(_VALID_SOURCES)}", 400
            )
            return

        # Validar function_id mínimo
        if not body.get("function_id", "").strip():
            self._send_error_json("Falta el campo 'function_id'.", 400)
            return

        # Log de trazabilidad
        import logging as _log
        _log.getLogger("neven.api").info(
            "[run_suggestion] source=%s function_id=%s note=%s",
            source, body.get("function_id", ""), context_note[:80]
        )

        # Delegar al pipeline completo de DataLab (validación, DuckDB, ControlR, slots)
        # Con un retry automático si el pipe está cerrándose (error 232)
        result = _datalab_handler.handle_run(
            body, _config,
            _get_db(), _db_lock,
            self._get_pipe_client
        )
        if result.get("code") == "ENGINE_UNAVAILABLE" or (
            "cerrando la canalización" in result.get("message", "") or
            "232" in result.get("message", "")
        ):
            # Pipe transitoriamente no disponible — esperar y reintentar una vez
            import time as _time
            _time.sleep(2.0)
            result = _datalab_handler.handle_run(
                body, _config,
                _get_db(), _db_lock,
                self._get_pipe_client
            )

        # Inyectar metadatos de trazabilidad en la respuesta
        result["source"]       = source
        result["context_note"] = context_note

        status_code = 200 if result.get("status") == "ok" else 400
        self._send_json(result, status_code)

    # ── Buklo endpoints ───────────────────────────────────────────────────────

    def _handle_buklo_save(self, body: dict):
        """POST /api/buklo/save — guarda el proyecto activo como archivo .buklo.

        Body: {
            path         (str, required)  — ruta destino, ej: "C:/NEVEN/projects/mi_analisis"
            chat_history (str, optional)  — historial del chat como Markdown
            plan         (dict, optional) — plan metodológico del análisis
            metadata     (dict, optional) — metadatos adicionales del usuario
        }
        """
        if not _BUKLO_AVAILABLE:
            self._send_error_json("BukloManager no disponible", 503)
            return

        path = body.get("path", "").strip()
        if not path:
            self._send_error_json("Falta el campo 'path'", 400)
            return

        # Seguridad: solo permitir paths dentro de directorios razonables
        # (evitar guardar en rutas del sistema)
        path = os.path.normpath(path)

        mgr = _get_buklo_manager()
        if mgr is None:
            self._send_error_json("BukloManager no inicializado", 503)
            return

        result = mgr.save(
            path             = path,
            db               = _get_db(),
            db_lock          = _db_lock,
            chat_history     = body.get("chat_history", ""),
            plan             = body.get("plan", {}),
            metadata         = body.get("metadata", {}),
            analysis_log     = body.get("analysis_log", []),
            report_content   = body.get("report_content", ""),
            report_format    = body.get("report_format",  "tex"),
            report_pdf_bytes = (
                __import__("base64").b64decode(body["report_pdf_b64"])
                if body.get("report_pdf_b64") else None
            ),
        )

        if result.get("status") == "ok":
            _buklo_set_path(result["path"])

        status_code = 200 if result.get("status") == "ok" else 500
        self._send_json(result, status_code)

    def _handle_buklo_load(self, body: dict):
        """POST /api/buklo/load — abre un .buklo y restaura el estado del proyecto.

        Body: {
            path (str, required) — ruta del archivo .buklo a cargar
        }

        Respuesta: {
            status, metadata, chat_history, plan,
            n_rows, n_cols, columns, has_dataset
        }
        """
        if not _BUKLO_AVAILABLE:
            self._send_error_json("BukloManager no disponible", 503)
            return

        path = body.get("path", "").strip()
        if not path:
            self._send_error_json("Falta el campo 'path'", 400)
            return

        if not os.path.isfile(path):
            self._send_error_json(f"Archivo no encontrado: {path}", 404)
            return

        mgr = _get_buklo_manager()
        if mgr is None:
            self._send_error_json("BukloManager no inicializado", 503)
            return

        result = mgr.load(
            path    = path,
            db      = _get_db(),
            db_lock = _db_lock,
        )

        if result.get("status") == "ok":
            _buklo_set_path(path)

        status_code = 200 if result.get("status") == "ok" else 500
        self._send_json(result, status_code)

    # ── Export endpoints ──────────────────────────────────────────────────────

    def _handle_export_capabilities(self):
        """GET /api/export/capabilities — detecta Quarto, pdflatex, xelatex."""
        import shutil, subprocess as _sp

        quarto     = shutil.which("quarto")
        pdflatex   = shutil.which("pdflatex")
        xelatex    = shutil.which("xelatex")
        latex_bin  = xelatex or pdflatex

        quarto_version = None
        if quarto:
            try:
                r = _sp.run([quarto, "--version"],
                            capture_output=True, text=True, timeout=5)
                quarto_version = r.stdout.strip()
            except Exception:
                quarto = None

        if quarto:
            best = "quarto"
        elif latex_bin:
            best = "latex"
        else:
            best = "tex_only"

        self._send_json({
            "status":          "ok",
            "best":            best,
            "quarto":          bool(quarto),
            "quarto_version":  quarto_version,
            "latex":           bool(latex_bin),
            "latex_bin":       latex_bin,
        })

    def _handle_export_generate(self, body: dict):
        """POST /api/export/generate — usa el LLM para generar el informe .tex o .qmd.

        Body: {
            format:        "tex" | "qmd"
            analysis_log:  [...]
            chat_history:  str  (mensajes del chat como texto)
            dataset_info:  {name, n_rows, n_cols, columns}
            title:         str  (opcional)
        }
        """
        import urllib.request as _url_req

        fmt          = body.get("format", "tex")
        analysis_log = body.get("analysis_log", [])
        chat_history = body.get("chat_history", "")
        dataset_info = body.get("dataset_info", {})
        title        = body.get("title", "Informe de Análisis Econométrico")

        if not analysis_log:
            self._send_error_json("No hay modelos en el historial para generar el informe.", 400)
            return

        # Leer config del LLM
        config_path = r"C:\NEVEN\neven-config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as _f:
                full_cfg = json.load(_f)
        except Exception as exc:
            self._send_error_json(f"No se pudo leer neven-config.json: {exc}", 503)
            return

        ai = full_cfg.get("AI", {})
        if not ai.get("enabled", False):
            self._send_error_json("AI.enabled=false — habilita la integración AI primero.", 503)
            return

        endpoint    = ai.get("endpoint", "")
        model       = ai.get("model", "")
        api_key     = ai.get("apiKey", "")
        provider    = ai.get("provider", "lmstudio")
        max_tokens  = int(ai.get("maxTokens", 4000))
        temperature = float(ai.get("temperature", 0.3))
        timeout_sec = int(ai.get("timeout", 120))

        # Serializar historial para el prompt
        def _serialize_log(log):
            lines = []
            for entry in log:
                lines.append(f"Modelo {entry.get('id','?')}: {entry.get('function_id','?')}")
                if entry.get('source') == 'ai_suggestion' and entry.get('context_note'):
                    lines.append(f"  Motivación: {entry['context_note']}")
                roles = entry.get('column_roles', {})
                if roles:
                    role_str = " | ".join(
                        f"{k}: [{', '.join(v) if isinstance(v,list) else v}]"
                        for k,v in roles.items()
                    )
                    lines.append(f"  Especificación: {role_str}")
                metrics = entry.get('metrics_text', '')
                if metrics:
                    lines.append(f"  Resultados:\n{metrics[:400]}")
                lines.append("")
            return "\n".join(lines)

        ds_name = dataset_info.get("name", "dataset")
        ds_rows = dataset_info.get("n_rows", 0)
        ds_cols = dataset_info.get("n_cols", 0)

        fmt_name = "Quarto Markdown (archivo .qmd)" if fmt == "qmd" else "LaTeX (archivo .tex)"
        fmt_instructions = (
            "Usa sintaxis Quarto/R Markdown válida con YAML frontmatter al inicio."
            if fmt == "qmd" else
            "Usa LaTeX estándar con paquetes: geometry, booktabs, hyperref, "
            "inputenc (utf8), fontenc (T1). Usa verbatim para las tablas de resultados."
        )

        system_prompt = (
            f"Eres un asistente académico especializado en econometría. "
            f"Genera un informe técnico en {fmt_name} titulado '{title}' "
            f"que documente el siguiente análisis econométrico paso a paso.\n\n"
            f"El informe debe:\n"
            f"1. Introducción con la pregunta de investigación y descripción del dataset\n"
            f"2. Para cada modelo: especificación, resultados, diagnósticos, motivación del cambio\n"
            f"3. Modelo final con interpretación económica\n"
            f"4. Conclusiones\n"
            f"5. Apéndice con el historial completo\n\n"
            f"Dataset: {ds_name} ({ds_rows} observaciones × {ds_cols} variables)\n\n"
            f"Historial de modelos:\n{_serialize_log(analysis_log)}\n\n"
            f"Extracto de la discusión:\n{chat_history[:1500]}\n\n"
            f"{fmt_instructions}\n"
            f"Escribe el documento completo en español. "
            f"NO incluyas explicaciones fuera del documento — solo el contenido del archivo."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Genera el informe completo en formato {fmt}."}
        ]

        headers = {"Content-Type": "application/json"}
        if api_key and provider not in ("ollama", "lmstudio"):
            headers["Authorization"] = f"Bearer {api_key}"
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://neven-studio.app"
            headers["X-Title"]      = "NEVEN Studio"
        if provider == "azure":
            headers.pop("Authorization", None)
            headers["api-key"] = api_key
            api_version = ai.get("apiVersion", "2024-02-15-preview")
            azure_base  = endpoint.rstrip("/")
            endpoint    = (f"{azure_base}/openai/deployments/{model}"
                           f"/chat/completions?api-version={api_version}")

        req_body = json.dumps({
            "model":       model,
            "messages":    messages,
            "max_tokens":  max_tokens,
            "temperature": temperature,
        }, ensure_ascii=False).encode("utf-8")

        try:
            req = _url_req.Request(endpoint, data=req_body, headers=headers, method="POST")
            with _url_req.urlopen(req, timeout=timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            self._send_error_json(f"Error al llamar al LLM para generar informe: {exc}", 500)
            return

        self._send_json({
            "status":  "ok",
            "content": content,
            "format":  fmt,
            "title":   title,
        })

    def _handle_export_compile(self, body: dict):
        """POST /api/export/compile — compila .tex/.qmd a PDF.

        Body: {
            content:  str   (contenido del archivo)
            format:   "tex" | "qmd"
            filename: str   (sin extensión, default "report")
        }
        """
        import shutil, subprocess as _sp, tempfile, base64

        fmt      = body.get("format", "tex")
        content  = body.get("content", "")
        filename = body.get("filename", "report")

        if not content.strip():
            self._send_error_json("Falta el contenido del documento.", 400)
            return

        tmp_dir = tempfile.mkdtemp(prefix="neven_export_")
        try:
            if fmt == "qmd":
                quarto = shutil.which("quarto")
                if not quarto:
                    self._send_error_json("Quarto no está disponible.", 503)
                    return
                src_path = os.path.join(tmp_dir, filename + ".qmd")
                pdf_path = os.path.join(tmp_dir, filename + ".pdf")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(content)
                result = _sp.run(
                    [quarto, "render", src_path, "--to", "pdf"],
                    capture_output=True, text=True, timeout=180, cwd=tmp_dir
                )
            else:  # tex
                latex_bin = shutil.which("xelatex") or shutil.which("pdflatex")
                if not latex_bin:
                    self._send_error_json("No hay compilador LaTeX disponible.", 503)
                    return
                src_path = os.path.join(tmp_dir, filename + ".tex")
                pdf_path = os.path.join(tmp_dir, filename + ".pdf")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(content)
                # Dos pasadas para referencias cruzadas
                for _ in range(2):
                    result = _sp.run(
                        [latex_bin, "-interaction=nonstopmode",
                         f"-output-directory={tmp_dir}", src_path],
                        capture_output=True, text=True, timeout=120, cwd=tmp_dir
                    )

            if os.path.isfile(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
                self._send_json({
                    "status":   "ok",
                    "pdf_b64":  pdf_b64,
                    "filename": filename + ".pdf",
                    "log":      result.stdout[-1000:] if result else "",
                })
            else:
                self._send_json({
                    "status":  "error",
                    "message": "La compilación no generó PDF.",
                    "log":     (result.stderr + result.stdout)[-2000:] if result else "",
                })
        except Exception as exc:
            self._send_error_json(f"Error al compilar: {exc}", 500)
        finally:
            import shutil as _sh
            _sh.rmtree(tmp_dir, ignore_errors=True)

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

    # Inicializar Ontology Engine — Knowledge Graph econométrico
    if _ONTOLOGY_AVAILABLE:
        try:
            # Leer ruta del grafo desde neven-config.json si está configurada
            ontology_path = None
            config_path = os.path.join(
                os.path.dirname(_config.get("staticDir", r"C:\NEVEN\taskpane")),
                "..", "neven-config.json"
            )
            if not os.path.isfile(config_path):
                config_path = r"C:\NEVEN\neven-config.json"
            if os.path.isfile(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as _f:
                        _cfg_full = json.load(_f)
                    ontology_path = _cfg_full.get("OntologyPath") or None
                except Exception:
                    pass

            _kg_engine = _get_ontology_engine(graph_path=ontology_path)
            if _kg_engine and _kg_engine.is_loaded:
                st = _kg_engine.stats
                print(
                    f"[NEVEN HTTP] OntologyEngine listo — "
                    f"{st['n_nodes']} nodos, {st['n_edges']} aristas",
                    file=sys.stderr
                )
            else:
                print("[NEVEN HTTP] OntologyEngine: grafo no encontrado — funciona sin ontología", file=sys.stderr)
        except Exception as _e:
            print(f"[NEVEN HTTP] OntologyEngine error al iniciar: {_e}", file=sys.stderr)
    else:
        print("[NEVEN HTTP] OntologyEngine no disponible (ontology_engine.py no encontrado)", file=sys.stderr)

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
