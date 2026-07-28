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

import os
import sys
import json
import ssl
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

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
    "maxPayloadMB": 50
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
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col_name}")
                    FROM dataset WHERE "{col_name}" IS NOT NULL''').fetchone()
            stat.update({
                "count": int(r[0] or 0), "min": float(r[1] or 0), "max": float(r[2] or 0),
                "mean": float(r[3] or 0), "median": float(r[4] or 0), "std": float(r[5] or 0),
                "q25": float(r[6] or 0), "q75": float(r[7] or 0)
            })
        else:
            with _db_lock:
                r = db.execute(f'SELECT COUNT(DISTINCT "{col_name}"), MODE("{col_name}") FROM dataset WHERE "{col_name}" IS NOT NULL').fetchone()
            stat.update({"unique": int(r[0] or 0), "mode": str(r[1] or "")})

        statistics.append(stat)

    return {"status": "ok", "statistics": statistics, "row_count": row_count, "col_count": len(cols_info)}


VALID_METRICS = {'SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'MEDIAN'}


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
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT") and not sql_stripped.startswith("WITH"):
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
        else:
            self._send_error_json(f"Unknown endpoint: /{path}", 404)

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


# ─── Bridge Buffer ────────────────────────────────────────────────────────────

_bridge_buffer = {}


# ─── Server Startup ───────────────────────────────────────────────────────────

def start_server(config=None):
    """Start the HTTP server on a daemon thread. Returns (thread, port) or None."""
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
