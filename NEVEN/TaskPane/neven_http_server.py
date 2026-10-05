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
#   POST /api/sheet/analyze→ Extract formula metadata for AI (hybrid JS+Python)
#   POST /api/workbook/analyze → Analyze entire workbook with cross-sheet refs
#   GET  /api/ontology/domains → List available ontology domains
#   GET  /api/ontology/domain/{id}/stats → Get domain statistics
#   GET  /api/ontology/search?q=term&domain=excel → Search knowledge graph
#   GET  /api/ayuda/funciones → Diccionario dinámico de funciones NevenX

import os
import sys
import json
import ssl
import time
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

# ═══════════════════════════════════════════════════════════════════════════════
# Logging Configuration
# ═══════════════════════════════════════════════════════════════════════════════
_log = logging.getLogger("NEVEN.HTTP")
_log.setLevel(logging.DEBUG)

# Console handler with format
if not _log.handlers:
    _console = logging.StreamHandler(sys.stderr)
    _console.setLevel(logging.INFO)
    _console.setFormatter(logging.Formatter(
        "[%(name)s] %(levelname)s: %(message)s"
    ))
    _log.addHandler(_console)

    # File handler (optional, rotates at 5MB)
    _log_dir = os.environ.get("NEVEN_LOG_DIR", r"C:\NEVEN")
    _log_file = os.path.join(_log_dir, "neven_http.log")
    try:
        from logging.handlers import RotatingFileHandler
        _file_handler = RotatingFileHandler(
            _log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
        )
        _file_handler.setLevel(logging.DEBUG)
        _file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))
        _log.addHandler(_file_handler)
    except Exception:
        pass  # File logging optional

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

# Sheet Analyzer — extrae metadatos de fórmulas Excel para el agente IA
try:
    from sheet_analyzer import analyze_sheet as _analyze_sheet  # type: ignore
    from sheet_analyzer import analyze_workbook as _analyze_workbook  # type: ignore
    _SHEET_ANALYZER_AVAILABLE = True
except ImportError:
    _SHEET_ANALYZER_AVAILABLE = False

    def _analyze_sheet(body):  # type: ignore[misc]
        return {"status": "error", "message": "Sheet analyzer not available"}

    def _analyze_workbook(body):  # type: ignore[misc]
        return {"status": "error", "message": "Workbook analyzer not available"}

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

# Config Manager — perfiles AI/DB con credenciales seguras (v2.0)
try:
    from config_manager import (  # type: ignore
        get_config_manager as _get_config_manager,
        reload_config as _reload_config,
        ConfigManager as _ConfigManager,
        AI_PROVIDERS, AI_MODELS, DB_TYPES, DB_DEFAULT_PORTS,
    )
    _CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    _CONFIG_MANAGER_AVAILABLE = False
    _get_config_manager = None
    _reload_config = None
    AI_PROVIDERS = []
    AI_MODELS = {}
    DB_TYPES = []
    DB_DEFAULT_PORTS = {}


# RAG Engine — Ontology-Guided Retrieval Augmented Generation
try:
    from rag_engine import (  # type: ignore
        get_rag_engine as _get_rag_engine,
        RAGEngine as _RAGEngine,
    )
    _RAG_AVAILABLE = True
except ImportError:
    _RAG_AVAILABLE = False
    _get_rag_engine = None
    _RAGEngine = None


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
    """Return True if the named pipe exists, False otherwise.

    On non-Windows (or when pywin32 is unavailable) always returns False.

    Args:
        pipe_name: Full pipe path, e.g. ``\\\\.\\pipe\\neven_r``.

    Returns:
        True if the pipe exists in the filesystem; False otherwise.
    """
    if not _WIN32_AVAILABLE:
        return False
    try:
        # Try to open with FILE_FLAG_OVERLAPPED and no exclusive access
        # This allows probing even if another client is connected
        handle = win32file.CreateFile(
            pipe_name,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0,           # no sharing
            None,        # default security
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_OVERLAPPED,  # non-blocking
            None,        # no template
        )
        win32file.CloseHandle(handle)
        return True
    except pywintypes.error as e:
        # Error 231 = All pipe instances are busy (pipe exists but all instances in use)
        # This means the pipe EXISTS, just busy — return True
        if e.winerror == 231:
            return True
        # Other errors (file not found, access denied, etc.) — pipe doesn't exist or inaccessible
        return False
    except Exception:
        return False


# ─── Dynamic pipe discovery ───────────────────────────────────────────────────

# Cache for discovered pipe names: {"r": "\\.\pipe\RJ2XCL2-PIPE-R-12345", ...}
_discovered_pipes: dict = {}
_discovered_pipes_lock = threading.Lock()


def _discover_pipe(lang: str) -> str | None:
    """Discover the Named Pipe for a language engine dynamically.

    Searches for pipes in two patterns:
    1. Fixed names from start_studio.py: ``neven_r``, ``neven_python``, ``neven_julia``
    2. Dynamic names from XLL: ``RJ2XCL2-PIPE-{LANG}-{PID}`` (e.g., ``RJ2XCL2-PIPE-R-214888``)

    Args:
        lang: Language identifier ("r", "python", "julia").

    Returns:
        Full pipe path if found, or ``None`` if no matching pipe exists.
    """
    lang_upper = lang.upper()
    lang_lower = lang.lower()
    
    # Check cache first
    with _discovered_pipes_lock:
        if lang in _discovered_pipes:
            cached = _discovered_pipes[lang]
            # Verify cached pipe still exists
            if _probe_pipe(cached):
                return cached
            # Cache invalid, clear it
            del _discovered_pipes[lang]
    
    pipe_dir = r"\\.\pipe"
    
    # Strategy 1: Check fixed pipe name (start_studio.py style)
    fixed_name = f"neven_{lang_lower}"
    fixed_path = f"{pipe_dir}\\{fixed_name}"
    if _probe_pipe(fixed_path):
        with _discovered_pipes_lock:
            _discovered_pipes[lang] = fixed_path
        return fixed_path
    
    # Strategy 2: Enumerate dynamic pipes (XLL style)
    pattern_prefix = f"RJ2XCL2-PIPE-{lang_upper}-"
    
    try:
        import os
        for name in os.listdir(pipe_dir):
            # Match pattern: RJ2XCL2-PIPE-R-{PID} (without -CB or -M suffix)
            if name.startswith(pattern_prefix) and not name.endswith(("-CB", "-M", "-STDOUT", "-STDERR")):
                full_path = f"{pipe_dir}\\{name}"
                if _probe_pipe(full_path):
                    # Cache and return
                    with _discovered_pipes_lock:
                        _discovered_pipes[lang] = full_path
                    return full_path
    except OSError:
        # Pipe directory enumeration failed
        pass
    
    return None


def _get_engine_status() -> dict:
    """Get availability status of all language engines.

    ALWAYS uses dynamic pipe discovery to verify engines are actually running.
    Does not trust factory registration alone - the pipe must exist and respond.

    Returns:
        Dict with keys "r", "python", "julia" and boolean values indicating
        whether each engine is available (pipe exists and is responsive).
    """
    result = {}
    for lang in ("r", "python", "julia"):
        # Always verify via dynamic discovery - don't trust factory alone
        # This handles Excel restarts, PID changes, and stale pipes
        pipe_path = _discover_pipe(lang)
        result[lang] = pipe_path is not None
    return result


# ─── Configuration ────────────────────────────────────────────────────────────

_server_instance = None
_server_port = None
_config = {}

# ── Estado global del contexto Excel → Tab IA ─────────────────────────────
# Almacena el último contexto publicado por =NEVEN.IA.Contexto()
# Se consume al ser leído por GET /api/ai/context/pending
_excel_context_lock    = threading.Lock()
_excel_context_pending = None   # {text, timestamp, source, columns, n_rows}

# ── Señal de show-taskpane (desde Ribbon) ─────────────────────────────────
# Se activa via POST /api/show-taskpane y se consume via GET /api/show-taskpane/poll
_show_taskpane_lock    = threading.Lock()
_show_taskpane_signal  = False   # True cuando el Ribbon solicita mostrar el TaskPane

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

        If no factory is registered, attempts to discover the pipe dynamically
        by searching for pipes matching the pattern ``RJ2XCL2-PIPE-{LANG}-{PID}``.

        Args:
            lang: Language key — "r", "python", or "julia".

        Returns:
            A PipeClient instance produced by the registered factory callable,
            or a dynamically created PipeClient using the discovered pipe.

        Raises:
            KeyError: If *lang* has no factory registered and no pipe could be
                      discovered. Callers should map this to an HTTP 503 response.
        """
        factory = _config.get("pipe_client_factory", {})
        if lang in factory:
            return factory[lang]()
        
        # No factory registered — try dynamic discovery
        pipe_path = _discover_pipe(lang)
        if pipe_path is None:
            raise KeyError(f"No pipe_client_factory registered and no pipe discovered for language: {lang!r}")
        
        # Import PipeClient and create instance with discovered pipe
        if not _PIPE_CLIENT_AVAILABLE:
            raise KeyError(f"pipe_client module not available for language: {lang!r}")
        
        # Import at call time to avoid circular imports
        try:
            from pipe_client import PipeClient  # type: ignore[import]
            client = PipeClient(pipe_path)
            client.connect()
            return client
        except Exception as exc:
            raise KeyError(f"Failed to connect to discovered pipe for {lang!r}: {exc}") from exc

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
            self._send_error_json("Rate limit exceeded (300 req/min)", 429)
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
            static_dir = _config.get("staticDir", "C:\\NEVEN\\taskpane").rstrip('/\\')
            bridge_dir = os.path.join(os.path.dirname(static_dir), "bridge")
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
            static_dir = _config.get("staticDir", "C:\\NEVEN\\taskpane").rstrip('/\\')
            bridge_dir = os.path.join(os.path.dirname(static_dir), "bridge")
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

        # ══════════════════════════════════════════════════════════════════════
        # Config Manager v2.0 — Perfiles AI/DB con credenciales seguras
        # ══════════════════════════════════════════════════════════════════════
        
        # GET /api/config/ai-profiles — Lista todos los perfiles de IA
        if path == 'api/config/ai-profiles':
            self._handle_config_ai_list()
            return
        
        # GET /api/config/ai-profiles/{id} — Obtener perfil específico
        if path.startswith('api/config/ai-profiles/') and '/test' not in path:
            profile_id = path.split('api/config/ai-profiles/', 1)[1]
            self._handle_config_ai_get(profile_id)
            return
        
        # GET /api/config/db-connections — Lista todas las conexiones DB
        if path == 'api/config/db-connections':
            self._handle_config_db_list()
            return
        
        # GET /api/config/db-connections/{id} — Obtener conexión específica
        if path.startswith('api/config/db-connections/') and '/test' not in path:
            conn_id = path.split('api/config/db-connections/', 1)[1]
            self._handle_config_db_get(conn_id)
            return
        
        # GET /api/config/providers — Lista proveedores AI disponibles
        if path == 'api/config/providers':
            self._handle_config_providers()
            return
        
        # GET /api/config/db-types — Lista tipos de DB disponibles
        if path == 'api/config/db-types':
            self._handle_config_db_types()
            return
        
        # GET /api/config/prompts — Lista prompts disponibles
        if path == 'api/config/prompts':
            self._handle_config_prompts_list()
            return
        
        # GET /api/config/prompts/{id} — Obtener contenido de prompt
        if path.startswith('api/config/prompts/'):
            prompt_id = path.split('api/config/prompts/', 1)[1]
            self._handle_config_prompt_get(prompt_id)
            return

        # ══════════════════════════════════════════════════════════════════════

        # ── AI config ─────────────────────────────────────────────────────────
        if path == 'api/ai/config':
            # Usar config_manager para obtener perfil activo
            if _CONFIG_MANAGER_AVAILABLE:
                try:
                    mgr = _get_config_manager()
                    active_profile = mgr.get_active_ai_profile()
                    prompts_dir = mgr.prompts.prompts_directory
                    prompt_ids = []
                    if os.path.isdir(prompts_dir):
                        prompt_ids = [
                            os.path.splitext(f)[0]
                            for f in sorted(os.listdir(prompts_dir))
                            if f.endswith(".txt")
                        ]
                    
                    if active_profile:
                        self._send_json({
                            "status":    "ok",
                            "enabled":   True,
                            "provider":  active_profile.get("provider", ""),
                            "model":     active_profile.get("model", ""),
                            "endpoint":  active_profile.get("endpoint", ""),
                            "prompts":   prompt_ids,
                        })
                    else:
                        self._send_json({
                            "status":    "ok",
                            "enabled":   False,
                            "provider":  "",
                            "model":     "",
                            "endpoint":  "",
                            "prompts":   prompt_ids,
                        })
                    return
                except Exception as exc:
                    _log.warning(f"Error con config_manager: {exc}")
            
            # Fallback a config legacy
            static_dir = _config.get("staticDir", r"C:\NEVEN\taskpane").rstrip('/\\')
            config_path = os.path.join(
                os.path.dirname(static_dir), "..",
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

        # ── Ontology endpoints — Multi-domain knowledge graph ─────────────────
        if path == 'api/ontology/domains':
            self._handle_ontology_domains()
            return
        
        if path.startswith('api/ontology/domain/'):
            # GET /api/ontology/domain/{domain_id}/stats
            parts = path.split('/')
            if len(parts) >= 5 and parts[4] == 'stats':
                domain_id = parts[3]
                self._handle_ontology_stats(domain_id)
                return

        if path.startswith('api/ontology/search'):
            # GET /api/ontology/search?q=VLOOKUP&domain=excel
            self._handle_ontology_search()
            return

        # ── Ayuda / Diccionario de Funciones NevenX ───────────────────────────
        if path == 'api/ayuda/funciones':
            self._handle_ayuda_funciones()
            return

        # ── Show TaskPane polling — GET consume la señal del Ribbon ───────────
        if path == 'api/show-taskpane/poll':
            global _show_taskpane_signal
            with _show_taskpane_lock:
                should_show = _show_taskpane_signal
                _show_taskpane_signal = False   # consumible — se borra al leerse
            self._send_json({"shouldShow": should_show})
            return

        # Serve viewers
        if path.startswith('viewers/'):
            viewers_dir = _config.get("viewersDir", "C:\\NEVEN\\workspace")
            file_path = os.path.join(viewers_dir, path[8:])
            self._serve_file(file_path)
            return

        # ── Office Add-in Catalog ─────────────────────────────────────────────
        # Serve manifest.xml for Office Add-in registration
        # Users can add http://localhost:5555/catalog/ as trusted catalog in Excel
        if path == 'catalog/' or path == 'catalog':
            # Return catalog listing (for Office to discover add-ins)
            catalog_dir = _config.get("catalogDir", r"C:\NEVEN\catalog")
            manifests = []
            if os.path.isdir(catalog_dir):
                for f in os.listdir(catalog_dir):
                    if f.endswith('.xml'):
                        manifests.append(f)
            # Return simple HTML listing
            html = '<!DOCTYPE html><html><head><title>NEVEN Add-in Catalog</title></head><body>'
            html += '<h1>NEVEN Office Add-in Catalog</h1><ul>'
            for m in manifests:
                html += f'<li><a href="/catalog/{m}">{m}</a></li>'
            html += '</ul></body></html>'
            self.send_response(200)
            self._add_cors_headers()
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(html)))
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        if path.startswith('catalog/'):
            catalog_dir = _config.get("catalogDir", r"C:\NEVEN\catalog")
            manifest_name = path[8:]  # Remove 'catalog/' prefix
            file_path = os.path.join(catalog_dir, manifest_name)
            if os.path.isfile(file_path):
                self._serve_file(file_path, content_type='application/xml')
            else:
                self.send_response(404)
                self._add_cors_headers()
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Manifest not found')
            return

        # ── Serve /docs/* for NEVEN documentation ─────────────────────────────
        if path.startswith('docs/'):
            docs_dir = _config.get("docsDir", r"C:\NEVEN\docs")
            doc_file = path[5:]  # Remove 'docs/' prefix
            file_path = os.path.join(docs_dir, doc_file)
            self._serve_file(file_path)
            return

        # ══════════════════════════════════════════════════════════════════════
        # RAG Engine — GET endpoints
        # ══════════════════════════════════════════════════════════════════════
        if path == 'api/rag/documents':
            self._handle_rag_documents()
            return
        
        if path == 'api/rag/stats':
            self._handle_rag_stats()
            return

        # Serve static files (taskpane, assets)
        static_dir = _config.get("staticDir", "C:\\NEVEN\\taskpane")
        if path == '' or path == 'taskpane.html':
            path = 'taskpane.html'
        file_path = os.path.join(static_dir, path)
        self._serve_file(file_path)

    def _serve_file(self, file_path, content_type=None):
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
            '.ico': 'image/x-icon', '.xml': 'application/xml'
        }
        ctype = content_type or content_types.get(ext, 'application/octet-stream')

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
            self._send_error_json("Rate limit exceeded (300 req/min)", 429)
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
        elif path == 'api/sheet/analyze':
            self._handle_sheet_analyze(body)
        elif path == 'api/workbook/analyze':
            self._handle_workbook_analyze(body)
        elif path == 'api/ai/chat':
            self._handle_ai_chat(body)
        elif path == 'api/ai/context':
            self._handle_ai_context(body)
        elif path == 'api/ai/chart':
            self._handle_ai_chart(body)
        elif path == 'api/functions/create':
            self._handle_function_create(body)
        elif path == 'api/packages/install':
            self._handle_pkg_install(body)
        elif path == 'api/show-taskpane':
            # Signal from Ribbon to show TaskPane (client polls this via GET)
            self._handle_show_taskpane()
        elif path == 'api/shutdown':
            # Graceful shutdown requested from Ribbon "Detener Servidor" button
            self._handle_shutdown()
        # ══════════════════════════════════════════════════════════════════════
        # Config Manager v2.0 — POST endpoints
        # ══════════════════════════════════════════════════════════════════════
        elif path == 'api/config/ai-profiles':
            self._handle_config_ai_create(body)
        elif path.startswith('api/config/ai-profiles/') and path.endswith('/test'):
            profile_id = path.replace('api/config/ai-profiles/', '').replace('/test', '')
            self._handle_config_ai_test(profile_id)
        elif path.startswith('api/config/ai-profiles/') and path.endswith('/activate'):
            profile_id = path.replace('api/config/ai-profiles/', '').replace('/activate', '')
            self._handle_config_ai_activate(profile_id)
        elif path.startswith('api/config/ai-profiles/') and path.endswith('/delete'):
            profile_id = path.replace('api/config/ai-profiles/', '').replace('/delete', '')
            self._handle_config_ai_delete(profile_id)
        elif path.startswith('api/config/ai-profiles/'):
            profile_id = path.split('api/config/ai-profiles/', 1)[1]
            self._handle_config_ai_update(profile_id, body)
        elif path == 'api/config/db-connections':
            self._handle_config_db_create(body)
        elif path.startswith('api/config/db-connections/') and path.endswith('/test'):
            conn_id = path.replace('api/config/db-connections/', '').replace('/test', '')
            self._handle_config_db_test(conn_id)
        elif path.startswith('api/config/db-connections/') and path.endswith('/activate'):
            conn_id = path.replace('api/config/db-connections/', '').replace('/activate', '')
            self._handle_config_db_activate(conn_id)
        elif path.startswith('api/config/db-connections/') and path.endswith('/delete'):
            conn_id = path.replace('api/config/db-connections/', '').replace('/delete', '')
            self._handle_config_db_delete(conn_id)
        elif path.startswith('api/config/db-connections/'):
            conn_id = path.split('api/config/db-connections/', 1)[1]
            self._handle_config_db_update(conn_id, body)
        elif path == 'api/config/prompts':
            self._handle_config_prompt_save(body)
        elif path == 'api/config/reload':
            self._handle_config_reload()
        # ══════════════════════════════════════════════════════════════════════
        # RAG Engine — Ontology-Guided Retrieval Augmented Generation
        # ══════════════════════════════════════════════════════════════════════
        elif path == 'api/rag/upload':
            self._handle_rag_upload(body)
        elif path == 'api/rag/upload-text':
            self._handle_rag_upload_text(body)
        elif path == 'api/rag/query':
            self._handle_rag_query(body)
        elif path == 'api/rag/delete':
            self._handle_rag_delete(body)
        # ══════════════════════════════════════════════════════════════════════
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

    # ══════════════════════════════════════════════════════════════════════════
    # Config Manager v2.0 — Handlers para perfiles AI/DB
    # ══════════════════════════════════════════════════════════════════════════

    def _handle_config_ai_list(self):
        """GET /api/config/ai-profiles — Lista todos los perfiles de IA."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            profiles = mgr.list_ai_profiles()
            self._send_json({
                "status": "ok",
                "profiles": profiles,
                "active_id": mgr.active_ai_profile,
            })
        except Exception as e:
            self._send_error_json(f"Error listando perfiles AI: {e}", 500)

    def _handle_config_ai_get(self, profile_id: str):
        """GET /api/config/ai-profiles/{id} — Obtener perfil específico."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            profile = mgr.get_ai_profile(profile_id)
            if profile:
                self._send_json({"status": "ok", "profile": profile})
            else:
                self._send_error_json(f"Perfil no encontrado: {profile_id}", 404)
        except Exception as e:
            self._send_error_json(f"Error obteniendo perfil AI: {e}", 500)

    def _handle_config_ai_create(self, body: dict):
        """POST /api/config/ai-profiles — Crear nuevo perfil de IA."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            profile_id = mgr.add_ai_profile(
                name=body.get("name", "Nuevo Perfil"),
                provider=body.get("provider", "openai"),
                model=body.get("model", "gpt-4o"),
                api_key=body.get("api_key"),
                endpoint=body.get("endpoint"),
                api_version=body.get("api_version"),
                temperature=body.get("temperature", 0.7),
                max_tokens=body.get("max_tokens", 4096),
                timeout=body.get("timeout", 120),
                set_active=body.get("set_active", False),
            )
            mgr.save()
            self._send_json({
                "status": "ok",
                "message": "Perfil creado",
                "profile_id": profile_id,
            })
        except Exception as e:
            self._send_error_json(f"Error creando perfil AI: {e}", 500)

    def _handle_config_ai_update(self, profile_id: str, body: dict):
        """POST /api/config/ai-profiles/{id} — Actualizar perfil existente."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            success = mgr.update_ai_profile(
                profile_id=profile_id,
                name=body.get("name"),
                provider=body.get("provider"),
                model=body.get("model"),
                api_key=body.get("api_key"),
                endpoint=body.get("endpoint"),
                api_version=body.get("api_version"),
                temperature=body.get("temperature"),
                max_tokens=body.get("max_tokens"),
                timeout=body.get("timeout"),
            )
            if success:
                mgr.save()
                self._send_json({"status": "ok", "message": "Perfil actualizado"})
            else:
                self._send_error_json(f"Perfil no encontrado: {profile_id}", 404)
        except Exception as e:
            self._send_error_json(f"Error actualizando perfil AI: {e}", 500)

    def _handle_config_ai_delete(self, profile_id: str):
        """POST /api/config/ai-profiles/{id}/delete — Eliminar perfil."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            success = mgr.delete_ai_profile(profile_id)
            if success:
                mgr.save()
                self._send_json({"status": "ok", "message": "Perfil eliminado"})
            else:
                self._send_error_json(f"Perfil no encontrado: {profile_id}", 404)
        except Exception as e:
            self._send_error_json(f"Error eliminando perfil AI: {e}", 500)

    def _handle_config_ai_activate(self, profile_id: str):
        """POST /api/config/ai-profiles/{id}/activate — Activar perfil."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            success = mgr.set_active_ai_profile(profile_id)
            if success:
                mgr.save()
                self._send_json({"status": "ok", "message": "Perfil activado"})
            else:
                self._send_error_json(f"Perfil no encontrado: {profile_id}", 404)
        except Exception as e:
            self._send_error_json(f"Error activando perfil AI: {e}", 500)

    def _handle_config_ai_test(self, profile_id: str):
        """POST /api/config/ai-profiles/{id}/test — Probar conexión."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            result = mgr.test_ai_connection(profile_id)
            self._send_json(result)
        except Exception as e:
            self._send_error_json(f"Error probando conexión AI: {e}", 500)

    # ── DB Connection handlers ────────────────────────────────────────────────

    def _handle_config_db_list(self):
        """GET /api/config/db-connections — Lista todas las conexiones DB."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            connections = mgr.list_db_connections()
            self._send_json({
                "status": "ok",
                "connections": connections,
                "active_id": mgr.active_db_connection,
            })
        except Exception as e:
            self._send_error_json(f"Error listando conexiones DB: {e}", 500)

    def _handle_config_db_get(self, conn_id: str):
        """GET /api/config/db-connections/{id} — Obtener conexión específica."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            conn = mgr.get_db_connection(conn_id)
            if conn:
                self._send_json({"status": "ok", "connection": conn})
            else:
                self._send_error_json(f"Conexión no encontrada: {conn_id}", 404)
        except Exception as e:
            self._send_error_json(f"Error obteniendo conexión DB: {e}", 500)

    def _handle_config_db_create(self, body: dict):
        """POST /api/config/db-connections — Crear nueva conexión DB."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            conn_id = mgr.add_db_connection(
                name=body.get("name", "Nueva Conexión"),
                db_type=body.get("db_type", "postgresql"),
                database=body.get("database", ""),
                host=body.get("host"),
                port=body.get("port"),
                username=body.get("username"),
                password=body.get("password"),
                use_windows_auth=body.get("use_windows_auth", False),
                extra_params=body.get("extra_params"),
                set_active=body.get("set_active", False),
            )
            mgr.save()
            self._send_json({
                "status": "ok",
                "message": "Conexión creada",
                "connection_id": conn_id,
            })
        except Exception as e:
            self._send_error_json(f"Error creando conexión DB: {e}", 500)

    def _handle_config_db_update(self, conn_id: str, body: dict):
        """POST /api/config/db-connections/{id} — Actualizar conexión existente."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            success = mgr.update_db_connection(
                conn_id=conn_id,
                name=body.get("name"),
                db_type=body.get("db_type"),
                host=body.get("host"),
                port=body.get("port"),
                database=body.get("database"),
                username=body.get("username"),
                password=body.get("password"),
                use_windows_auth=body.get("use_windows_auth"),
                extra_params=body.get("extra_params"),
            )
            if success:
                mgr.save()
                self._send_json({"status": "ok", "message": "Conexión actualizada"})
            else:
                self._send_error_json(f"Conexión no encontrada: {conn_id}", 404)
        except Exception as e:
            self._send_error_json(f"Error actualizando conexión DB: {e}", 500)

    def _handle_config_db_delete(self, conn_id: str):
        """POST /api/config/db-connections/{id}/delete — Eliminar conexión."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            success = mgr.delete_db_connection(conn_id)
            if success:
                mgr.save()
                self._send_json({"status": "ok", "message": "Conexión eliminada"})
            else:
                self._send_error_json(f"Conexión no encontrada: {conn_id}", 404)
        except Exception as e:
            self._send_error_json(f"Error eliminando conexión DB: {e}", 500)

    def _handle_config_db_activate(self, conn_id: str):
        """POST /api/config/db-connections/{id}/activate — Activar conexión."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            success = mgr.set_active_db_connection(conn_id)
            if success:
                mgr.save()
                self._send_json({"status": "ok", "message": "Conexión activada"})
            else:
                self._send_error_json(f"Conexión no encontrada: {conn_id}", 404)
        except Exception as e:
            self._send_error_json(f"Error activando conexión DB: {e}", 500)

    def _handle_config_db_test(self, conn_id: str):
        """POST /api/config/db-connections/{id}/test — Probar conexión."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            result = mgr.test_db_connection(conn_id)
            self._send_json(result)
        except Exception as e:
            self._send_error_json(f"Error probando conexión DB: {e}", 500)

    # ── Providers / Types helpers ─────────────────────────────────────────────

    def _handle_config_providers(self):
        """GET /api/config/providers — Lista proveedores AI y sus modelos."""
        self._send_json({
            "status": "ok",
            "providers": AI_PROVIDERS,
            "models": AI_MODELS,
        })

    def _handle_config_db_types(self):
        """GET /api/config/db-types — Lista tipos de BD y puertos default."""
        self._send_json({
            "status": "ok",
            "db_types": DB_TYPES,
            "default_ports": DB_DEFAULT_PORTS,
        })

    # ── Prompts handlers ──────────────────────────────────────────────────────

    def _handle_config_prompts_list(self):
        """GET /api/config/prompts — Lista prompts disponibles organizados por categoría."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            prompts_dir = mgr.prompts.prompts_directory
            
            # Cargar configuración de categorías
            config_path = os.path.join(prompts_dir, "prompts_config.json")
            categories_config = {}
            if os.path.isfile(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    categories_config = json.load(f)
            
            categories = categories_config.get("categories", {})
            default_category = categories_config.get("default_category", "custom")
            
            # Recopilar todos los prompts
            all_prompts = {}  # id -> prompt info
            
            # System prompts
            if os.path.isdir(prompts_dir):
                for f in sorted(os.listdir(prompts_dir)):
                    if f.endswith(".txt"):
                        pid = os.path.splitext(f)[0]
                        all_prompts[pid] = {
                            "id": pid,
                            "name": pid.replace("_", " ").replace("-", " ").title(),
                            "type": "system",
                        }
            
            # Custom prompts
            custom_dir = os.path.join(prompts_dir, "custom")
            if os.path.isdir(custom_dir):
                for f in sorted(os.listdir(custom_dir)):
                    if f.endswith(".txt"):
                        pid = os.path.splitext(f)[0]
                        all_prompts[pid] = {
                            "id": pid,
                            "name": pid.replace("_", " ").replace("-", " ").title(),
                            "type": "custom",
                        }
            
            # Organizar por categorías
            categorized = {}
            assigned_prompts = set()
            
            for cat_id, cat_info in categories.items():
                cat_prompts = []
                for pid in cat_info.get("prompts", []):
                    if pid in all_prompts:
                        cat_prompts.append(all_prompts[pid])
                        assigned_prompts.add(pid)
                
                # Agregar prompts custom a categoría "custom"
                if cat_id == "custom":
                    for pid, pinfo in all_prompts.items():
                        if pinfo["type"] == "custom" and pid not in assigned_prompts:
                            cat_prompts.append(pinfo)
                            assigned_prompts.add(pid)
                
                if cat_prompts or cat_id == "custom":  # Siempre mostrar custom aunque esté vacía
                    categorized[cat_id] = {
                        "label": cat_info.get("label", cat_id.title()),
                        "icon": cat_info.get("icon", "📄"),
                        "prompts": cat_prompts,
                    }
            
            # Prompts no asignados van a default_category
            unassigned = [p for pid, p in all_prompts.items() if pid not in assigned_prompts]
            if unassigned:
                if default_category not in categorized:
                    categorized[default_category] = {
                        "label": "Otros",
                        "icon": "📄",
                        "prompts": [],
                    }
                categorized[default_category]["prompts"].extend(unassigned)
            
            self._send_json({
                "status": "ok",
                "active": mgr.prompts.active_system,
                "categories": categorized,
            })
        except Exception as e:
            self._send_error_json(f"Error listando prompts: {e}", 500)

    def _handle_config_prompt_get(self, prompt_id: str):
        """GET /api/config/prompts/{id} — Obtener contenido de un prompt."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _get_config_manager()
            prompts_dir = mgr.prompts.prompts_directory
            
            # Try system prompt first
            path = os.path.join(prompts_dir, f"{prompt_id}.txt")
            prompt_type = "system"
            
            if not os.path.isfile(path):
                # Try custom
                path = os.path.join(prompts_dir, "custom", f"{prompt_id}.txt")
                prompt_type = "custom"
            
            if not os.path.isfile(path):
                self._send_error_json(f"Prompt no encontrado: {prompt_id}", 404)
                return
            
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self._send_json({
                "status": "ok",
                "id": prompt_id,
                "type": prompt_type,
                "content": content,
                "editable": prompt_type == "custom",
            })
        except Exception as e:
            self._send_error_json(f"Error leyendo prompt: {e}", 500)

    def _handle_config_prompt_save(self, body: dict):
        """POST /api/config/prompts — Guardar prompt (con backup automático)."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            prompt_id = body.get("id", "").strip()
            content = body.get("content", "")
            set_active = body.get("set_active", False)
            
            if not prompt_id:
                self._send_error_json("ID de prompt requerido", 400)
                return
            
            # Sanitize ID
            prompt_id = "".join(c for c in prompt_id if c.isalnum() or c in "-_")
            
            mgr = _get_config_manager()
            prompts_dir = mgr.prompts.prompts_directory
            
            # Determinar si es prompt de sistema o custom existente
            system_path = os.path.join(prompts_dir, f"{prompt_id}.txt")
            custom_path = os.path.join(prompts_dir, "custom", f"{prompt_id}.txt")
            
            if os.path.isfile(system_path):
                # Es prompt de sistema - hacer backup antes de sobrescribir
                backup_dir = os.path.join(prompts_dir, "backup")
                os.makedirs(backup_dir, exist_ok=True)
                
                # Backup con timestamp
                import datetime
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"{prompt_id}_{ts}.txt")
                
                # Solo hacer backup si no existe uno idéntico reciente
                with open(system_path, "r", encoding="utf-8") as f:
                    original_content = f.read()
                
                if original_content != content:  # Solo backup si hay cambios
                    with open(backup_path, "w", encoding="utf-8") as f:
                        f.write(original_content)
                    _log.info(f"Backup creado: {backup_path}")
                
                # Guardar directamente en el archivo de sistema
                target_path = system_path
            elif os.path.isfile(custom_path):
                # Es prompt custom existente - sobrescribir
                target_path = custom_path
            else:
                # Es nuevo prompt custom
                custom_dir = os.path.join(prompts_dir, "custom")
                os.makedirs(custom_dir, exist_ok=True)
                target_path = os.path.join(custom_dir, f"{prompt_id}.txt")
            
            # Guardar
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            if set_active:
                mgr.prompts.active_system = prompt_id
                mgr.save()
            
            self._send_json({
                "status": "ok",
                "message": "Prompt guardado",
                "id": prompt_id,
                "path": target_path,
            })
        except Exception as e:
            self._send_error_json(f"Error guardando prompt: {e}", 500)

    def _handle_config_reload(self):
        """POST /api/config/reload — Recargar configuración desde archivo."""
        if not _CONFIG_MANAGER_AVAILABLE:
            self._send_error_json("Config Manager no disponible", 503)
            return
        try:
            mgr = _reload_config()
            self._send_json({
                "status": "ok",
                "message": "Configuración recargada",
                "version": mgr.version,
            })
        except Exception as e:
            self._send_error_json(f"Error recargando config: {e}", 500)

    # ══════════════════════════════════════════════════════════════════════════

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
        import traceback

        try:
            return self._handle_ai_chat_impl(body, _url_req)
        except Exception as e:
            tb = traceback.format_exc()
            _log.error(f"CRITICAL ERROR in AI Chat:\n{tb}")
            self._send_error_json(f"Error interno en AI Chat: {e}", 500)
            return

    def _handle_ai_chat_impl(self, body: dict, _url_req):
        """Implementación interna del chat con AI."""

        # ── Load AI config from neven-config.json ────────────────────────────
        static_dir = _config.get("staticDir", r"C:\NEVEN\taskpane").rstrip('/\\')
        config_path = os.path.join(
            os.path.dirname(static_dir), "..",
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

        # ═══ Obtener configuración AI del perfil activo (v2) o sección legacy ═══
        endpoint    = ""
        model       = ""
        max_tokens  = 2000
        temperature = 0.3
        timeout_sec = 60
        api_key     = ""
        provider    = "lmstudio"
        prompts_dir = r"C:\NEVEN\prompts"
        api_version = ""
        
        if _CONFIG_MANAGER_AVAILABLE:
            # Usar sistema nuevo de perfiles con credenciales en keyring
            try:
                mgr = _get_config_manager()
                active_profile = mgr.get_active_ai_profile()
                if active_profile:
                    endpoint    = active_profile.get("endpoint", "")
                    model       = active_profile.get("model", "gpt-4")
                    max_tokens  = int(active_profile.get("max_tokens", 2000))
                    temperature = float(active_profile.get("temperature", 0.3))
                    timeout_sec = int(active_profile.get("timeout", 60))
                    provider    = active_profile.get("provider", "azure")
                    api_version = active_profile.get("api_version", "")
                    # API key viene de keyring via config_manager
                    api_key     = active_profile.get("api_key", "")
                    _log.info(f"Usando perfil activo: {active_profile.get('name')} ({provider}/{model})")
            except Exception as e:
                _log.warning(f"Error obteniendo perfil activo: {e}")
        
        # Fallback a sección AI legacy si no hay perfil activo
        if not api_key:
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
            api_version = ai.get("api_version", "")
        
        prompts_cfg = full_cfg.get("prompts", {})
        prompts_dir = prompts_cfg.get("prompts_directory", r"C:\NEVEN\prompts")

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
        # Carga el catálogo de funciones para que el agente pueda sugerir análisis concretos
        try:
            from catalog_loader import build_catalog_prompt_section
            catalog_section = build_catalog_prompt_section()
        except Exception:
            catalog_section = ""

        # ═══════════════════════════════════════════════════════════════════════
        # RAG: Ontology-Guided Retrieval — Enriquece el contexto con libros indexados
        # ═══════════════════════════════════════════════════════════════════════
        rag_context = ""
        rag_domains = []
        rag_sources = []  # Inicializar fuentes RAG
        _log.info(f"[RAG] _RAG_AVAILABLE={_RAG_AVAILABLE}, _get_rag_engine={_get_rag_engine is not None}")
        if _RAG_AVAILABLE and _get_rag_engine:
            try:
                # Extraer la pregunta del último mensaje del usuario
                user_messages = [m for m in messages if m.get("role") == "user"]
                if user_messages:
                    last_question = user_messages[-1].get("content", "")[:500]  # Limitar a 500 chars
                    
                    # Obtener idiomas disponibles y expandir query con traducciones
                    engine = _get_rag_engine()
                    available_languages = engine.get_available_languages()
                    query_for_rag = engine.translate_query_for_languages(
                        last_question, 
                        available_languages if available_languages else ["en", "es"]
                    )
                    
                    _log.info(f"[RAG] Query expandida ({len(available_languages)} idiomas): {query_for_rag[:100]}...")
                    
                    # Consultar RAG con ontología
                    rag_result = engine.query_with_ontology(query_for_rag, top_k=3)
                    
                    if rag_result.get("results"):
                        rag_domains = rag_result.get("detected_domains", [])
                        chunks = rag_result["results"]
                        
                        # Leer umbral mínimo desde config (default 0.50)
                        rag_config = full_cfg.get("RAG", {})
                        MIN_RAG_SCORE = rag_config.get("minScore", 0.50)
                        
                        # Filtrar chunks con score mínimo de relevancia
                        relevant_chunks = [c for c in chunks if c.get("score", 0) >= MIN_RAG_SCORE]
                        
                        if not relevant_chunks:
                            _log.info(f"[RAG] Chunks descartados por bajo score (max: {max(c.get('score',0) for c in chunks):.2f} < {MIN_RAG_SCORE})")
                        else:
                            chunks = relevant_chunks
                            # Construir contexto RAG
                            rag_parts = []
                            for i, chunk in enumerate(chunks, 1):
                                source = chunk.get("filename", "unknown")
                                domain = chunk.get("domain", "general")
                                score = chunk.get("score", 0)
                                content = chunk.get("content", "")[:800]  # Limitar cada chunk
                                rag_parts.append(
                                    f"[Fuente {i}: {source} ({domain}, relevancia: {score:.2f})]\n{content}"
                                )
                            
                            if rag_parts:
                                rag_context = (
                                    "\n\n## CONTEXTO DE LIBROS DE REFERENCIA (RAG)\n"
                                    "Los siguientes fragmentos provienen de libros de econometría, "
                                    "estadística y Excel indexados en la base de conocimiento:\n\n"
                                    + "\n\n---\n\n".join(rag_parts)
                                    + "\n\n---\nUsa esta información para fundamentar tu respuesta. "
                                    "NO cites las fuentes en el texto, el sistema las mostrará en un popup.\n"
                                )
                                # Guardar fuentes con chunk de texto para el popup
                                rag_sources = [
                                    {
                                        "filename": c.get("filename"),
                                        "domain": c.get("domain"),
                                        "page": c.get("page"),
                                        "page_end": c.get("page_end"),
                                        "score": round(c.get("score", 0), 2),
                                        "content": c.get("content", "")[:500]  # Limitar a 500 chars
                                    }
                                    for c in chunks
                                ]
                                _log.info(f"[RAG] Contexto enriquecido: {len(chunks)} chunks, dominios: {rag_domains}")
            except Exception as e:
                _log.warning(f"[RAG] Error consultando: {e}")
                # Continuar sin RAG si falla

        has_excel_context   = "=== DATOS DE EXCEL ===" in context
        has_results_context = "=== RESULTADOS DEL ANÁLISIS ===" in context
        has_sheet_analysis  = (
            "=== SHEET ANALYSIS ===" in context or
            "=== ANÁLISIS DE HOJA EXCEL ===" in context or
            "## Estructura de columnas" in context
        )

        _fmt = (
            "Responde siempre en español a menos que el usuario escriba en otro idioma. "
            "Usa Markdown para formatear tu respuesta. "
            "Para fórmulas matemáticas usa SIEMPRE delimitadores Markdown estándar: "
            "$$...$$ para fórmulas en bloque y $...$ para fórmulas inline. "
            "NUNCA uses \\(...\\) ni \\[...\\] ni ninguna otra notación LaTeX."
        )

        _run_hint = (
            "Cuando sugieras un nuevo análisis o corrección metodológica, "
            "incluye la fórmula Excel exacta con convención NevenX v4: "
            "=NevenX.R(\"NombreFuncion\", Y, X, TipoOutput) donde TipoOutput es el número en posición 4. "
            "Usa EXACTAMENTE uno de los xll_name del catálogo — no inventes nombres. "
            "Ejemplo: =NevenX.R(\"MR_Lineal\", A1:A100, B1:D100, 1) para OLS, "
            "=NevenX.R(\"MR_Lineal\",,, 0) para ver la ayuda de parámetros. "
            "Convención de posiciones: Pos2=Y, Pos3=X, Pos4=TipoOutput, Pos5=Escala, "
            "Pos6=Filtro, Pos7=Constante, Pos8+=rangos libres (ej: instrumentos Z). "
            "\n\n"
            "Si la función que necesitas NO existe en el catálogo, puedes crearla. "
            "SOLO bajo solicitud o aprobación explícita del usuario, incluye un bloque "
            "```neven-create-function con el JSON: "
            "{\"filename\": \"R4XCL-RG-NombreFuncion.R\", "
            "\"language\": \"r\", "
            "\"description\": \"descripción breve\", "
            "\"code\": \"<código R completo siguiendo el protocolo NEVEN>\", "
            "\"excel_usage\": \"=NevenX.R(\\\"NombreFuncion\\\", Y, X, 1)\"}. "
            "El código DEBE seguir el protocolo de C:\\\\NEVEN\\\\functions\\\\: "
            "función con SetDatosY/SetDatosX como primeros parámetros, "
            "primera fila de cada rango = nombres de columnas, "
            "filas restantes = datos, retornar data.frame con prefijo R4XCL_. "
            "\n\n"
            "Si el usuario pide EXPLÍCITAMENTE instalar un paquete, genera un bloque "
            "```neven-install con el JSON: "
            "{\"package\": \"nombre\", \"language\": \"r\"|\"python\"|\"julia\", "
            "\"context_note\": \"para qué se necesita\"}. "
            "NUNCA sugiereas instalar paquetes ni crear funciones proactivamente — "
            "solo bajo solicitud o aprobación explícita del usuario."
        )

        if context or catalog_section:
            if has_sheet_analysis:
                # ═══════════════════════════════════════════════════════════════
                # Excel Forensic Analysis Mode — Usa prompt forense para auditoria
                # ═══════════════════════════════════════════════════════════════
                forense_prompt = ""
                forense_path = os.path.join(prompts_dir, "analisis_forense_libro.txt")
                if os.path.isfile(forense_path):
                    try:
                        with open(forense_path, "r", encoding="utf-8") as f:
                            forense_prompt = f.read()
                    except Exception:
                        pass
                
                if forense_prompt:
                    sys_content = (
                        forense_prompt + "\n\n"
                        f"## DATOS DEL ANALISIS ACTUAL:\n\n{context}\n\n"
                        + _fmt
                    )
                else:
                    # Fallback si no existe el archivo
                    sys_content = (
                        "Eres un **Consultor Excel experto** integrado en NEVEN.\n\n"
                        "## Tu rol\n"
                        "Actuas como auditor forense, documentador y asesor de hojas de calculo. "
                        "Tienes acceso al analisis estructural de la hoja activa del usuario.\n\n"
                        "## REGLA CRITICA: Usa el contexto para respuestas precisas\n"
                        "Cuando el usuario pregunte sobre una columna por nombre, SIEMPRE:\n"
                        "1. Busca en '## Estructura de columnas' que columna tiene ese nombre\n"
                        "2. Usa el rango exacto mostrado para tu formula\n"
                        "3. NUNCA pidas mas informacion si ya la tienes en el contexto\n\n"
                        f"## Contexto del analisis de la hoja:\n\n{context}\n\n"
                        "Responde siempre basandote en los datos reales de la hoja del usuario.\n\n"
                        + _fmt
                    )
            elif has_results_context and has_excel_context:
                sys_content = (
                    "Eres NEVEN Assistant, un econometrista experto. "
                    "Tienes acceso a los datos reales y los resultados del análisis del usuario. "
                    "Responde sobre ESTE modelo específico, no en abstracto. "
                    "Si detectas problemas metodológicos (endogeneidad, heterocedasticidad, "
                    "especificación incorrecta), cita el diagnóstico concreto y sugiere "
                    "la función NEVEN que lo corrige.\n\n"
                    + _run_hint + "\n\n"
                    + (f"Contexto del usuario:\n\n{context}\n\n" if context else "")
                    + (catalog_section + "\n\n" if catalog_section else "")
                    + _fmt
                )
            elif has_results_context:
                sys_content = (
                    "Eres NEVEN Assistant, un econometrista experto. "
                    "Tienes acceso a los resultados del análisis del usuario. "
                    "Responde sobre ESTE modelo específico.\n\n"
                    + _run_hint + "\n\n"
                    + (f"Resultados:\n\n{context}\n\n" if context else "")
                    + (catalog_section + "\n\n" if catalog_section else "")
                    + _fmt
                )
            elif has_excel_context:
                sys_content = (
                    "Eres NEVEN Assistant, un analista de datos experto. "
                    "El usuario ha enviado datos directamente desde su hoja de cálculo de Excel. "
                    "Responde sobre ESTOS datos específicos. "
                    "Cuando sugieras un análisis, menciona las columnas por su nombre real "
                    "y la función NEVEN exacta que ejecutarlo.\n\n"
                    + _run_hint + "\n\n"
                    + (f"Datos de Excel:\n\n{context}\n\n" if context else "")
                    + (catalog_section + "\n\n" if catalog_section else "")
                    + _fmt
                )
            else:
                sys_content = (
                    "Eres NEVEN Assistant, un econometrista y analista de datos experto. "
                    "El usuario trabaja con NEVEN, un add-in de Excel con R, Julia y Python.\n\n"
                    + (f"Contexto actual:\n\n{context}\n\n" if context else "")
                    + (catalog_section + "\n\n" if catalog_section else "")
                    + _fmt
                )

            # ═══ Inyectar contexto RAG si existe ═══
            if rag_context:
                sys_content = sys_content + rag_context

            sys_msg = {"role": "system", "content": sys_content}
            messages = [sys_msg] + [m for m in messages if m.get("role") != "system"]
        else:
            # Sin contexto — system message mínimo
            if not any(m.get("role") == "system" for m in messages):
                messages = [{"role": "system", "content": (
                    "Eres NEVEN Assistant, un econometrista y analista de datos experto. "
                    "Responde siempre en español. Usa Markdown. "
                    "Para fórmulas usa $$...$$ (bloque) y $...$ (inline)."
                )}] + messages

        # ── HTTP request to LLM ───────────────────────────────────────────────
        headers = {"Content-Type": "application/json"}

        if provider == "azure":
            # Azure OpenAI usa api-key en header y endpoint con deployment + api-version
            headers["api-key"] = api_key
            # api_version ya viene del perfil activo; fallback solo si está vacía
            if not api_version:
                ai = full_cfg.get("AI", {})
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

        _log.debug(f"AI Chat endpoint: {endpoint}")
        
        # Usar requests en lugar de urllib (más confiable en threading)
        import requests as _requests
        try:
            resp = _requests.post(
                endpoint,
                headers=headers,
                data=req_body,
                timeout=timeout_sec
            )
            
            if resp.status_code != 200:
                detail = resp.text[:300]
                try:
                    err_json = resp.json()
                    detail = (err_json.get("error", {}).get("message")
                              or err_json.get("message") or detail)
                except Exception:
                    pass
                self._send_error_json(
                    f"El LLM ({provider}) retornó HTTP {resp.status_code}: {detail}", 502)
                return
            
            raw_str = resp.text.strip()
            if not raw_str:
                self._send_error_json(
                    f"El LLM ({provider}) retornó respuesta vacía. "
                    f"Verifica el modelo '{model}' y la apiVersion en neven-config.json.",
                    502
                )
                return
            data = resp.json()
        except _requests.exceptions.Timeout:
            self._send_error_json(
                f"Timeout al llamar al LLM ({provider}). "
                f"El servidor no respondió en {timeout_sec} segundos.",
                504
            )
            return
        except _requests.exceptions.RequestException as exc:
            self._send_error_json(
                f"No se pudo conectar al LLM ({provider}). "
                f"Verifique que {endpoint} esté activo. Detalle: {exc}",
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
            "rag_used":    bool(rag_context),
            "rag_domains": rag_domains if rag_context else [],
            "rag_sources": rag_sources if rag_context else [],
        })

    def _handle_show_taskpane(self):
        """POST /api/show-taskpane — señal del Ribbon para mostrar el TaskPane.

        El Add-in hace polling a GET /api/show-taskpane/poll y cuando recibe
        shouldShow=true, llama a Office.addin.showAsTaskpane().
        """
        global _show_taskpane_signal
        with _show_taskpane_lock:
            _show_taskpane_signal = True
        self._send_json({"status": "ok", "message": "Signal sent"})

    def _handle_shutdown(self):
        """POST /api/shutdown — apagado limpio solicitado desde el Ribbon.

        Responde inmediatamente y luego agenda el shutdown en un thread separado
        para que la respuesta HTTP llegue al cliente antes de cerrar.
        """
        import threading

        def _shutdown_server():
            import time
            time.sleep(0.3)  # Dar tiempo a que la respuesta HTTP se envíe
            log("Shutdown solicitado desde Ribbon — cerrando servidor...")
            # Cerrar el socket directamente sin bloquear
            global _server_instance
            if _server_instance:
                try:
                    _server_instance.server_close()  # Cierra socket sin bloquear
                except:
                    pass
            time.sleep(0.1)
            import os
            os._exit(0)

        self._send_json({"status": "ok", "message": "Shutdown initiated"})
        threading.Thread(target=_shutdown_server, daemon=True).start()

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

    def _handle_ai_chart(self, body: dict):
        """POST /api/ai/chart — genera un gráfico HTML interactivo.

        Body:
            range_address : str — dirección del rango (ej: "Sheet1!A1:D50")
            headers       : [str] | null — nombres de columnas
            data          : [[...]] — datos en formato row-major
            prompt        : str — solicitud del usuario (ej: "gráfico de barras")

        Returns:
            {status, html, chart_type, library, tokens_used}
        """
        import urllib.request as _url_req

        # Cargar config de AI
        static_dir = _config.get("staticDir", r"C:\NEVEN\taskpane").rstrip('/\\')
        config_path = os.path.join(os.path.dirname(static_dir), "neven-config.json")

        ai_config = {}
        if os.path.isfile(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
                ai_config = full_config.get("AI", {})
            except Exception as e:
                self._send_error_json(f"Error leyendo config: {e}", 500)
                return

        if not ai_config.get("enabled", False):
            self._send_error_json("AI.enabled=false en neven-config.json", 503)
            return

        # Extraer campos del body
        range_address = body.get("range_address", "Desconocido")
        headers = body.get("headers")  # puede ser None o lista
        data = body.get("data", [])
        user_prompt = body.get("prompt", "").strip()

        if not data:
            self._send_error_json("El campo 'data' no puede estar vacío", 400)
            return
        if not user_prompt:
            self._send_error_json("El campo 'prompt' no puede estar vacío", 400)
            return

        # Detectar tipo de gráfico
        chart_type = self._detect_chart_type(user_prompt)

        # Construir prompt para generación de gráfico
        system_prompt = self._build_chart_system_prompt(
            range_address=range_address,
            headers=headers,
            data=data,
            chart_type=chart_type
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Llamar al LLM
        try:
            provider = ai_config.get("provider", "azure").lower()
            endpoint = ai_config.get("endpoint", "")
            api_key = ai_config.get("apiKey", "")
            model = ai_config.get("model", "gpt-4")
            max_tokens = ai_config.get("maxTokens", 4000)
            temperature = ai_config.get("temperature", 0.3)
            timeout = ai_config.get("timeout", 120)

            if provider == "azure":
                api_version = ai_config.get("apiVersion", "2024-02-15-preview")
                url = f"{endpoint}/openai/deployments/{model}/chat/completions?api-version={api_version}"
                headers_req = {
                    "Content-Type": "application/json",
                    "api-key": api_key
                }
            else:
                url = endpoint if endpoint else "https://api.openai.com/v1/chat/completions"
                headers_req = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }

            payload = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            if provider != "azure":
                payload["model"] = model

            req = _url_req.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers_req,
                method='POST'
            )

            with _url_req.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode('utf-8'))

            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            tokens_used = result.get("usage", {}).get("total_tokens", 0)

        except Exception as e:
            self._send_error_json(f"Error llamando al LLM: {e}", 502)
            return

        # Limpiar respuesta (quitar bloques de código markdown)
        html_content = reply.strip()
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        if html_content.startswith("```"):
            html_content = html_content[3:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
        html_content = html_content.strip()

        # Detectar librería usada
        library = "unknown"
        html_lower = html_content.lower()
        if "plotly" in html_lower:
            library = "Plotly"
        elif "chart.js" in html_lower or "new chart(" in html_lower:
            library = "Chart.js"
        elif "echarts" in html_lower:
            library = "ECharts"
        elif "apexcharts" in html_lower:
            library = "ApexCharts"
        elif "leaflet" in html_lower:
            library = "Leaflet"
        elif "d3" in html_lower:
            library = "D3.js"

        self._send_json({
            "status": "ok",
            "html": html_content,
            "chart_type": chart_type,
            "library": library,
            "tokens_used": tokens_used
        })

    def _detect_chart_type(self, prompt: str) -> str:
        """Detecta el tipo de gráfico solicitado en el prompt."""
        prompt_lower = prompt.lower()
        
        chart_patterns = {
            "bar": ["barra", "barras", "bar chart", "bar graph"],
            "line": ["línea", "linea", "line chart", "tendencia", "serie temporal"],
            "pie": ["pastel", "torta", "pie chart", "circular"],
            "scatter": ["dispersión", "dispersion", "scatter", "puntos"],
            "histogram": ["histograma", "histogram", "distribución"],
            "box": ["caja", "boxplot", "box plot", "bigotes"],
            "heatmap": ["calor", "heatmap", "heat map", "mapa de calor"],
            "area": ["área", "area chart", "apilado"],
            "map": ["mapa", "geográfico", "geografico", "ubicación", "lat", "lon"],
        }
        
        for chart_type, patterns in chart_patterns.items():
            for pattern in patterns:
                if pattern in prompt_lower:
                    return chart_type
        
        return "auto"

    def _build_chart_system_prompt(self, range_address: str, headers, data: list, chart_type: str) -> str:
        """Construye el prompt de sistema para generación de gráficos."""
        
        # Limitar datos para el prompt (máximo 50 filas de muestra)
        sample_data = data[:50] if len(data) > 50 else data
        total_rows = len(data)
        
        # Formatear headers
        if headers:
            header_str = ", ".join(str(h) for h in headers)
        else:
            header_str = f"Columna 1 a Columna {len(data[0]) if data else 0}"
        
        # Detectar si hay coordenadas geográficas
        has_geo = False
        if headers:
            headers_lower = [str(h).lower() for h in headers]
            has_geo = any(h in headers_lower for h in ['lat', 'lon', 'latitude', 'longitude', 'latitud', 'longitud'])
        
        prompt = f"""Eres un experto en visualización de datos. Tu tarea es generar código HTML completo y auto-contenido que muestre un gráfico interactivo.

## Datos disponibles
- **Rango:** {range_address}
- **Columnas:** {header_str}
- **Total filas:** {total_rows}
- **Muestra de datos (primeras {len(sample_data)} filas):**

{json.dumps(sample_data[:10], indent=2, ensure_ascii=False)}

## Tipo de gráfico solicitado: {chart_type}

## Instrucciones críticas:

1. **Genera HTML COMPLETO** con todo el código necesario (CSS, JavaScript, datos).
2. **Usa una de estas librerías** (en orden de preferencia):
   - **Plotly.js** (preferido para gráficos interactivos)
   - **Chart.js** (alternativa ligera)
   - **Leaflet** (si hay datos geográficos lat/lon)
   
3. **Incluye los CDN** de las librerías en el HTML.

4. **Incrusta los datos** directamente en el JavaScript (no uses fetch ni archivos externos).

5. **El gráfico debe ser interactivo**: hover, zoom, tooltips.

6. **Tamaño responsivo**: usa width: 100% y height: 400px.

7. **Tema oscuro**: fondo #1e1e1e, texto #e0e0e0, colores vibrantes para datos.

8. **NO incluyas** explicaciones, solo el código HTML completo.

{"IMPORTANTE: Los datos contienen coordenadas geográficas (lat/lon). Usa Leaflet para un mapa interactivo." if has_geo else ""}
"""
        return prompt

    def _handle_function_create(self, body: dict):
        """POST /api/functions/create — guarda una nueva función en C:\\NEVEN\\functions\\

        Llamado por el agente IA cuando el usuario aprueba crear una función nueva.
        Body:
            filename   : str — nombre del archivo, ej: "R4XCL-RG-2SLS.R"
            code       : str — código R/Python/Julia completo de la función
            language   : str — "r" | "python" | "julia"
            description: str — descripción breve para el log
        Returns:
            {status, path, message}
        """
        filename    = body.get("filename", "").strip()
        code        = body.get("code", "").strip()
        language    = body.get("language", "r").lower()
        description = body.get("description", "")

        if not filename or not code:
            self._send_error_json("'filename' y 'code' son requeridos.", 400)
            return

        # Validar extensión según lenguaje
        ext_map = {"r": ".R", "python": ".py", "julia": ".jl"}
        expected_ext = ext_map.get(language, ".R")
        if not filename.endswith(expected_ext) and not filename.endswith(expected_ext.lower()):
            self._send_error_json(
                f"El filename '{filename}' debe terminar en '{expected_ext}' para lenguaje '{language}'.",
                400
            )
            return

        # Solo permitir nombres seguros (sin rutas relativas o absolutas)
        import re as _re
        if not _re.match(r'^[A-Za-z0-9_\-\.]+$', filename):
            self._send_error_json(
                f"Nombre de archivo inválido: '{filename}'. Solo se permiten letras, números, guiones y puntos.",
                400
            )
            return

        functions_dir = _config.get("functionsDir",
                        _config.get("Standalone", {}).get("functionsDir", r"C:\NEVEN\functions"))
        dest_path = os.path.join(functions_dir, filename)

        # No sobreescribir funciones del sistema sin confirmación explícita
        is_system = filename.startswith("R4XCL-") or filename.startswith("J4XCL-")
        if os.path.exists(dest_path) and is_system:
            self._send_error_json(
                f"El archivo '{filename}' ya existe. Para sobreescribirlo, renombra el archivo nuevo.",
                409
            )
            return

        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(code)

            import logging as _log
            _log.getLogger("neven.functions").info(
                f"Función creada por el agente: {filename} ({len(code)} chars) — {description}"
            )

            self._send_json({
                "status":   "ok",
                "path":     dest_path,
                "filename": filename,
                "message":  (
                    f"Función guardada en {dest_path}. "
                    f"Reinicia NEVEN Studio para que aparezca en DataLab, "
                    f"o usa =NevenX.R(\"{filename.replace('.R','').replace('R4XCL-RG-','MR_').replace('R4XCL-','')}\", Y, X, 1) "
                    f"desde Excel directamente."
                ),
            })
        except Exception as exc:
            self._send_error_json(f"No se pudo guardar '{filename}': {exc}", 500)

    def _handle_sheet_analyze(self, body: dict):
        """POST /api/sheet/analyze — Analiza fórmulas Excel y retorna metadatos estructurados.

        Body:
            sheet_name    : str — Nombre de la hoja
            formulas      : List[{address, formula}] — Celdas con fórmulas desde Office.js
            total_cells   : int — Total de celdas en UsedRange (opcional)
            include_graph : bool — Incluir grafo Mermaid (default: True)

        Returns:
            {
                status, sheet_name, summary, functions, patterns,
                dependencies, critical_cells, complexity, mermaid_graph?
            }

        Usado por el sistema híbrido JS+Python para análisis de hojas:
        1. JavaScript (Office.js) captura range.formulas interactivamente
        2. Python (este endpoint) procesa, normaliza y construye metadatos
        3. El agente IA interpreta los metadatos con la ontología Excel
        """
        if not _SHEET_ANALYZER_AVAILABLE:
            self._send_error_json("Sheet analyzer module not available", 503)
            return

        try:
            result = _analyze_sheet(body)
            status_code = 200 if result.get("status") == "ok" else 400
            self._send_json(result, status_code)
        except Exception as exc:
            self._send_error_json(f"Error analyzing sheet: {exc}", 500)

    def _handle_workbook_analyze(self, body: dict):
        """POST /api/workbook/analyze — Analiza todo el libro de trabajo.

        Body:
            workbook_name : str — Nombre del libro
            sheets        : List[{name, formulas, cell_values, total_cells}] — Hojas capturadas
            total_sheets  : int — Total de hojas en el libro (algunas pueden no capturarse)
            include_graph : bool — Incluir grafo Mermaid de flujo de datos (default: True)

        Returns:
            {
                status, workbook_name, sheet_count, captured_sheets,
                sheets: [análisis por hoja],
                cross_sheet_dependencies: {edges, hub_sheets, orphan_sheets, ...},
                workbook_pattern: {pattern, confidence, characteristics, suggestions},
                data_flow: {nodes, critical_path, mermaid?},
                aggregated_stats: {...},
                recommendations: [...]
            }

        Extiende el análisis de hoja individual a nivel de libro completo:
        1. Analiza cada hoja individualmente (reutiliza _analyze_sheet)
        2. Detecta referencias cruzadas entre hojas (=Sheet1!A1)
        3. Clasifica el patrón arquitectural (financial_model, dashboard, etc.)
        4. Construye grafo de flujo de datos (Input → Processing → Output)
        5. Genera recomendaciones basadas en la estructura
        """
        if not _SHEET_ANALYZER_AVAILABLE:
            self._send_error_json("Workbook analyzer module not available", 503)
            return

        try:
            result = _analyze_workbook(body)
            status_code = 200 if result.get("status") == "ok" else 400
            self._send_json(result, status_code)
        except Exception as exc:
            self._send_error_json(f"Error analyzing workbook: {exc}", 500)

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

    # ── Ontology handlers ─────────────────────────────────────────────────────
    
    def _handle_ontology_domains(self):
        """GET /api/ontology/domains — List available ontology domains."""
        try:
            from ontology_manager import get_manager
            manager = get_manager()
            domains = manager.list_domains()
            self._send_json({
                "status": "ok",
                "domains": domains,
                "total": len(domains)
            })
        except ImportError:
            self._send_json({
                "status": "ok",
                "domains": [],
                "total": 0,
                "warning": "ontology_manager not available"
            })
        except Exception as e:
            self._send_error_json(f"Ontology error: {e}")
    
    def _handle_ontology_stats(self, domain_id: str):
        """GET /api/ontology/domain/{domain_id}/stats — Get domain statistics."""
        try:
            from ontology_manager import get_manager
            manager = get_manager()
            stats = manager.get_domain_stats(domain_id)
            if "error" in stats:
                self._send_error_json(stats["error"], 404)
            else:
                self._send_json({"status": "ok", **stats})
        except ImportError:
            self._send_error_json("ontology_manager not available", 503)
        except Exception as e:
            self._send_error_json(f"Ontology stats error: {e}")
    
    def _handle_ontology_search(self):
        """GET /api/ontology/search?q=term&domain=excel — Search knowledge graph."""
        from urllib.parse import urlparse, parse_qs
        query_params = parse_qs(urlparse(self.path).query)
        
        q = query_params.get("q", [""])[0]
        domain = query_params.get("domain", [None])[0]
        limit = int(query_params.get("limit", ["50"])[0])
        
        if not q:
            self._send_error_json("Missing 'q' parameter", 400)
            return
        
        try:
            from ontology_manager import search_knowledge
            results = search_knowledge(q, domain=domain)[:limit]
            self._send_json({
                "status": "ok",
                "query": q,
                "domain": domain,
                "results": results,
                "count": len(results)
            })
        except ImportError:
            self._send_json({
                "status": "ok",
                "query": q,
                "results": [],
                "count": 0,
                "warning": "ontology_manager not available"
            })
        except Exception as e:
            self._send_error_json(f"Search error: {e}")

    def _handle_ayuda_funciones(self):
        """GET /api/ayuda/funciones — Diccionario dinámico de funciones NevenX.
        
        Lee todos los archivos JSON de C:\\NEVEN\\functions\\ y filtra solo
        aquellas funciones que tienen 'function_name_xll' (usables desde Excel).
        
        Retorna estructura organizada por familia (categoría) con toda la
        información necesaria para el Diccionario de Funciones del TaskPane.
        """
        functions_dir = r"C:\NEVEN\functions"
        result = {
            "status": "ok",
            "familias": {},   # { "RG": { label, funciones: [...] } }
            "total": 0
        }
        
        # Mapeo de family → label (fallback si no está en el JSON)
        family_labels = {
            "RG": "Regresión",
            "AD": "Análisis de Datos", 
            "GR": "Gráficos",
            "ML": "Machine Learning",
            "DS": "Data Science",
            "ST": "Series de Tiempo",
            "TM": "Text Mining",
            "UC": "Casos de Uso"
        }
        
        # Cargar mapeo de aliases (function_name_xll -> [aliases])
        aliases_map = {}
        aliases_file = os.path.join(functions_dir, "aliases.json")
        if os.path.isfile(aliases_file):
            try:
                with open(aliases_file, 'r', encoding='utf-8') as f:
                    aliases_data = json.load(f)
                    aliases_map = aliases_data.get('function_to_aliases', {})
            except Exception as e:
                _log.warning(f"Error cargando aliases.json: {e}")
        
        try:
            if not os.path.isdir(functions_dir):
                self._send_json(result)
                return
            
            for filename in os.listdir(functions_dir):
                if not filename.endswith('.json') or filename == 'aliases.json':
                    continue
                
                filepath = os.path.join(functions_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        sidecar = json.load(f)
                    
                    # Solo funciones con function_name_xll (usables en Excel)
                    xll_name = sidecar.get('function_name_xll')
                    if not xll_name:
                        continue
                    
                    family = sidecar.get('family', 'UC')
                    family_label = sidecar.get('family_label', family_labels.get(family, family))
                    
                    # Crear familia si no existe
                    if family not in result['familias']:
                        result['familias'][family] = {
                            "label": family_label,
                            "funciones": []
                        }
                    
                    # Extraer información relevante para el diccionario
                    func_info = {
                        "id": sidecar.get('id', filename.replace('.json', '')),
                        "name": sidecar.get('name', xll_name),
                        "description": sidecar.get('description', ''),
                        "function_name_xll": xll_name,
                        "languages": sidecar.get('languages', []),
                        "wikipedia_url": sidecar.get('wikipedia_url'),
                        "nevenx_positions": sidecar.get('nevenx_positions', {}),
                        "tipo_outputs": sidecar.get('tipo_outputs', []),
                        "variable_roles": sidecar.get('variable_roles', {}),
                        "aliases": aliases_map.get(xll_name, [])
                    }
                    
                    result['familias'][family]['funciones'].append(func_info)
                    result['total'] += 1
                    
                except Exception as e:
                    # Log error pero continuar con otros archivos
                    _log.warning(f"Error leyendo {filename}: {e}")
                    continue
            
            # Ordenar funciones dentro de cada familia por nombre
            for fam in result['familias'].values():
                fam['funciones'].sort(key=lambda x: x['name'])
            
            self._send_json(result)
            
        except Exception as e:
            self._send_error_json(f"Error cargando funciones: {e}", 500)

    # ══════════════════════════════════════════════════════════════════════════
    # RAG Engine handlers — Ontology-Guided Retrieval Augmented Generation
    # ══════════════════════════════════════════════════════════════════════════

    def _handle_rag_documents(self):
        """GET /api/rag/documents — List all indexed documents."""
        if not _RAG_AVAILABLE:
            self._send_error_json("RAG Engine no disponible", 503)
            return
        
        try:
            engine = _get_rag_engine()
            docs = engine.list_documents()
            self._send_json({
                "status": "ok",
                "documents": docs,
                "count": len(docs)
            })
        except Exception as e:
            self._send_error_json(f"RAG documents error: {e}")

    def _handle_rag_stats(self):
        """GET /api/rag/stats — Get RAG engine statistics."""
        if not _RAG_AVAILABLE:
            self._send_error_json("RAG Engine no disponible", 503)
            return
        
        try:
            engine = _get_rag_engine()
            stats = engine.get_stats()
            self._send_json({
                "status": "ok",
                "stats": stats
            })
        except Exception as e:
            self._send_error_json(f"RAG stats error: {e}")

    def _handle_rag_upload(self, body: dict):
        """POST /api/rag/upload — Upload and index a document file."""
        if not _RAG_AVAILABLE:
            self._send_error_json("RAG Engine no disponible", 503)
            return
        
        file_path = body.get("file_path")
        domain = body.get("domain", "general")
        metadata = body.get("metadata", {})
        
        if not file_path:
            self._send_error_json("Missing 'file_path'", 400)
            return
        
        if not os.path.isfile(file_path):
            self._send_error_json(f"File not found: {file_path}", 404)
            return
        
        try:
            engine = _get_rag_engine()
            doc_id = engine.add_document(file_path, domain=domain, metadata=metadata)
            self._send_json({
                "status": "ok",
                "doc_id": doc_id,
                "message": f"Document indexed successfully"
            })
        except Exception as e:
            self._send_error_json(f"RAG upload error: {e}")

    def _handle_rag_upload_text(self, body: dict):
        """POST /api/rag/upload-text — Upload and index text directly."""
        if not _RAG_AVAILABLE:
            self._send_error_json("RAG Engine no disponible", 503)
            return
        
        text = body.get("text")
        doc_name = body.get("name", "untitled")
        domain = body.get("domain", "general")
        metadata = body.get("metadata", {})
        
        if not text:
            self._send_error_json("Missing 'text'", 400)
            return
        
        try:
            engine = _get_rag_engine()
            doc_id = engine.add_text(text, doc_name, domain=domain, metadata=metadata)
            self._send_json({
                "status": "ok",
                "doc_id": doc_id,
                "message": f"Text indexed successfully"
            })
        except Exception as e:
            self._send_error_json(f"RAG upload text error: {e}")

    def _handle_rag_query(self, body: dict):
        """POST /api/rag/query — Query the RAG index."""
        if not _RAG_AVAILABLE:
            self._send_error_json("RAG Engine no disponible", 503)
            return
        
        question = body.get("question") or body.get("query")
        domain = body.get("domain")
        top_k = int(body.get("top_k", 5))
        min_score = float(body.get("min_score", 0.0))  # 0 = sin filtro
        use_ontology = body.get("use_ontology", True)
        
        if not question:
            self._send_error_json("Missing 'question' or 'query'", 400)
            return
        
        try:
            engine = _get_rag_engine()
            
            if use_ontology:
                result = engine.query_with_ontology(question, top_k=top_k)
            else:
                results = engine.query(question, domain=domain, top_k=top_k)
                result = {
                    "question": question,
                    "detected_domains": [],
                    "ontology_guided": False,
                    "results": results
                }
            
            # Filtrar por score mínimo si se especificó
            if min_score > 0 and result.get("results"):
                filtered = [r for r in result["results"] if r.get("score", 0) >= min_score]
                result["results"] = filtered
                result["filtered_by_score"] = min_score
            
            self._send_json({
                "status": "ok",
                **result
            })
        except Exception as e:
            self._send_error_json(f"RAG query error: {e}")

    def _handle_rag_delete(self, body: dict):
        """POST /api/rag/delete — Delete a document from the index."""
        if not _RAG_AVAILABLE:
            self._send_error_json("RAG Engine no disponible", 503)
            return
        
        doc_id = body.get("doc_id")
        
        if not doc_id:
            self._send_error_json("Missing 'doc_id'", 400)
            return
        
        try:
            engine = _get_rag_engine()
            success = engine.delete_document(doc_id)
            if success:
                self._send_json({
                    "status": "ok",
                    "message": f"Document {doc_id} deleted"
                })
            else:
                self._send_error_json(f"Failed to delete document {doc_id}")
        except Exception as e:
            self._send_error_json(f"RAG delete error: {e}")

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
        static_dir = _config.get("staticDir", "C:\\NEVEN\\taskpane").rstrip('/\\')
        bridge_dir = os.path.join(os.path.dirname(static_dir), "bridge")
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
        static_dir = _config.get("staticDir", "C:\\NEVEN\\taskpane").rstrip('/\\')
        bridge_dir = os.path.join(os.path.dirname(static_dir), "bridge")
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

        Probes each language's Named Pipe using dynamic discovery and returns
        a JSON object reflecting real-time availability.

        The discovery logic searches for pipes matching the pattern
        ``RJ2XCL2-PIPE-{LANG}-{PID}`` created by the XLL, falling back to
        the legacy fixed names ``neven_{lang}`` for compatibility.

        Returns:
            JSON ``{"r": bool, "python": bool, "julia": bool}`` where each value
            is ``True`` iff a matching pipe was found and is accessible.
        """
        self._send_json(_get_engine_status())

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
        _log.warning("TaskPane disabled in config — server not started")
        return None

    ports = [_config.get("port", 5555), _config.get("fallbackPort", 5556)]

    server = None
    for port in ports:
        try:
            server = HTTPServer(('127.0.0.1', port), NEVENHandler)
            _server_port = port
            _log.info(f"Bound to localhost:{port}")
            break
        except OSError as e:
            _log.warning(f"Port {port} unavailable: {e}")

    if server is None:
        _log.error("FATAL: Cannot bind HTTP server on any port")
        return None

    # HTTPS setup (if cert available)
    cert_path = _config.get("certPath", "")
    key_path = _config.get("keyPath", "")
    if cert_path and key_path and os.path.isfile(cert_path) and os.path.isfile(key_path):
        try:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
            _log.info(f"HTTPS enabled (cert: {cert_path})")
        except Exception as e:
            _log.warning(f"HTTPS setup failed: {e} — running HTTP only")
    else:
        _log.info("No cert configured — running HTTP (Task Pane may require HTTPS)")

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
            _log.info("Package Manager Service iniciado")
        except Exception as e:
            _log.warning(f"Package Manager Service no disponible: {e}")

    # Start on daemon thread
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _log.info(f"Server running on thread (port {_server_port})")

    return thread, _server_port


def stop_server():
    """Stop the HTTP server gracefully."""
    global _server_instance
    if _server_instance:
        _server_instance.shutdown()
        _server_instance = None
        _log.info("Server stopped")


# ─── Standalone entry point ───────────────────────────────────────────────────

if __name__ == "__main__":
    """Run the HTTP server standalone (not embedded in ControlPython.exe)."""
    import signal
    
    _log.info("Starting standalone server...")
    
    # Start server
    result = start_server()
    if result is None:
        _log.error("Failed to start server")
        sys.exit(1)
    
    thread, port = result
    _log.info(f"Standalone server running on http://127.0.0.1:{port}")
    
    # Keep main thread alive until interrupted
    def signal_handler(sig, frame):
        _log.info("Shutting down...")
        stop_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Block forever (daemon thread will keep running)
    try:
        while True:
            thread.join(timeout=1.0)
            if not thread.is_alive():
                break
    except KeyboardInterrupt:
        stop_server()
