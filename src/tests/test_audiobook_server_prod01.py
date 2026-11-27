# NEVEN - PROD-01 / A-02 / SEC-16: servidor de audiolibros con puerto propio, bind a
# 127.0.0.1, fallo de bind visible y autenticacion local. Arranca servidores REALES
# (neven_audiobook_server.py como subproceso y startup/neven_http_server.py en este
# proceso) en puertos libres; nada se escribe fuera de directorios temporales.
import http.client
import importlib.util
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

pytest.importorskip("flask")

_SRC = pathlib.Path(__file__).resolve().parent.parent
_AUDIOBOOK_SRC = _SRC / "Audiobook"
_STARTUP_SERVER = _SRC / "startup" / "neven_http_server.py"
os.environ.setdefault("NEVEN_LOG_DIR", tempfile.mkdtemp(prefix="neven_test_log_"))

SENTINEL_KEY = "SENTINEL-DEEPL-KEY-0123456789"


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _request(port, method, path, body=None, headers=None, host=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    conn.putrequest(method, path, skip_host=host is not None)
    if host is not None:
        conn.putheader("Host", host)
    data = None
    h = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
        h["Content-Length"] = str(len(data))
    for k, v in h.items():
        conn.putheader(k, v)
    conn.endheaders(data)
    resp = conn.getresponse()
    raw = resp.read()
    hdrs = {k.lower(): v for k, v in resp.getheaders()}
    conn.close()
    return resp.status, hdrs, raw


def _json(raw):
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        return {}


_START_TIMEOUT = float(os.environ.get("NEVEN_TEST_START_TIMEOUT", "180"))


def _wait_for(predicate, timeout=_START_TIMEOUT, interval=0.3):
    end = time.time() + timeout
    while time.time() < end:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    return None


def _health(port):
    try:
        status, _, raw = _request(port, "GET", "/api/health")
        return _json(raw) if status == 200 else None
    except OSError:
        return None


def _kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def _listeners(pid, port):
    """Direcciones locales en LISTENING del proceso pid en el puerto dado."""
    out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True).stdout
    found = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0] == "TCP" and parts[3] == "LISTENING" and parts[4] == str(pid):
            if parts[1].rsplit(":", 1)[-1] == str(port):
                found.append(parts[1])
    return found


class AudiobookProc:
    """Servidor de audiolibros real en un subproceso, con registro en un fichero."""

    def __init__(self, root, port, token_file, studio_port, config=None, cli_port=True):
        self.root = pathlib.Path(root)
        self.port = port
        self.log = self.root / "audiobook-test.log"
        self.config_path = self.root / "neven-config.json"
        if config is not None:
            self.config_path.write_text(json.dumps(config), encoding="utf-8")
        env = dict(os.environ)
        env["NEVEN_TOKEN_FILE"] = str(token_file)
        env["NEVEN_STUDIO_PORT"] = str(studio_port)
        env["PYTHONUTF8"] = "1"
        cmd = [sys.executable, str(self.root / "Audiobook" / "neven_audiobook_server.py")]
        if config is not None:
            cmd += ["--config", str(self.config_path)]
        if cli_port:
            cmd += ["--port", str(port)]
        with open(self.log, "wb") as fh:
            self.proc = subprocess.Popen(cmd, cwd=str(self.root / "Audiobook"), env=env,
                                         stdout=fh, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL)
        self.pid = None

    def wait_ready(self):
        health = _wait_for(lambda: _health(self.port) if self.proc.poll() is None else {})
        assert health, f"el servidor no arranco:\n{self.log_text()}"
        self.pid = health["pid"]
        return health

    def wait_exit(self, timeout=40):
        try:
            return self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.stop()
            pytest.fail(f"el servidor no salio:\n{self.log_text()}")

    def log_text(self):
        try:
            return self.log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def stop(self):
        if self.pid:
            _kill_tree(self.pid)
        _kill_tree(self.proc.pid)
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    """Arbol temporal tipo C:\\NEVEN con una copia de src/Audiobook (sin cache)."""
    root = tmp_path_factory.mktemp("prod01")
    shutil.copytree(_AUDIOBOOK_SRC, root / "Audiobook",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (root / "taskpane").mkdir()
    return root


@pytest.fixture(scope="module")
def token_file(work):
    path = work / "session.token"
    path.write_text("secret-A-" + "a" * 34, encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def studio_port():
    return _free_port()


@pytest.fixture(scope="module")
def ab(work, token_file, studio_port):
    """Servidor de audiolibros con la configuracion por defecto (solo 127.0.0.1)."""
    proc = AudiobookProc(work, _free_port(), token_file, studio_port)
    proc.wait_ready()
    yield proc
    proc.stop()


def _auth(token_file):
    return {"X-NEVEN-Token": token_file.read_text(encoding="utf-8").strip()}


def _studio_origin(studio_port):
    return {"Origin": f"https://localhost:{studio_port}"}


# ── 10. Identidad de /api/health ──────────────────────────────────────────────
def test_health_identifies_the_audiobook_service(ab, studio_port):
    status, _, raw = _request(ab.port, "GET", "/api/health")
    data = _json(raw)
    assert status == 200
    assert data["service"] == "neven-audiobook"
    assert data["port"] == ab.port
    assert data["studio_port"] == studio_port
    assert data["lan"] is False
    assert isinstance(data["pid"], int)


# ── 2. Solo 127.0.0.1 por defecto ─────────────────────────────────────────────
def test_default_server_listens_only_on_loopback(ab):
    addrs = _listeners(ab.pid, ab.port)
    assert addrs == [f"127.0.0.1:{ab.port}"], addrs


def test_qr_is_refused_with_a_reason_when_not_on_lan(ab, token_file):
    status, _, raw = _request(ab.port, "GET", "/api/qr", headers=_auth(token_file))
    assert status == 409
    assert _json(raw)["code"] == "lan_disabled"
    assert "127.0.0.1" in _json(raw)["message"]


def test_lan_mode_is_explicit_warns_and_still_requires_the_secret(work, token_file, studio_port):
    port = _free_port()
    sub = work / "lan"
    sub.mkdir()
    shutil.copytree(work / "Audiobook", sub / "Audiobook", dirs_exist_ok=True)
    proc = AudiobookProc(sub, port, token_file, studio_port,
                         config={"Audiobook": {"port": port, "lan": True}})
    try:
        health = proc.wait_ready()
        assert health["lan"] is True
        addrs = _listeners(proc.pid, port)
        assert f"0.0.0.0:{port}" in addrs
        assert "WARNING" in proc.log_text() and "red local" in proc.log_text()
        for path in ("/api/upload", "/api/generate", "/api/translate/deepl/configure"):
            status, _, _ = _request(port, "POST", path, {})
            assert status == 401, path
        status, _, _ = _request(port, "POST", "/api/upload", {},
                                headers={**_auth(token_file), "Origin": "https://evil.example"})
        assert status == 403
    finally:
        proc.stop()


def test_non_boolean_lan_is_a_configuration_error(work, token_file, studio_port):
    sub = work / "badlan"
    sub.mkdir()
    shutil.copytree(work / "Audiobook", sub / "Audiobook", dirs_exist_ok=True)
    proc = AudiobookProc(sub, _free_port(), token_file, studio_port,
                         config={"Audiobook": {"lan": "yes"}})
    assert proc.wait_exit() == 2
    assert "Audiobook.lan" in proc.log_text()


# ── 3a. Puerto ocupado: error visible en el servidor de audiolibros ──────────
def test_busy_port_makes_the_server_exit_with_a_visible_error(work, token_file, studio_port):
    sub = work / "busy"
    sub.mkdir()
    shutil.copytree(work / "Audiobook", sub / "Audiobook", dirs_exist_ok=True)
    occupant = socket.socket()
    occupant.bind(("127.0.0.1", 0))
    occupant.listen(1)
    port = occupant.getsockname()[1]
    try:
        proc = AudiobookProc(sub, port, token_file, studio_port)
        assert proc.wait_exit() == 3
        text = proc.log_text()
        assert "ERROR" in text and f"puerto {port} esta ocupado" in text
    finally:
        occupant.close()


# ── 1. No comparten puerto ────────────────────────────────────────────────────
def test_reserved_ports_are_rejected_with_the_key_named(work, token_file, studio_port):
    sub = work / "reserved"
    sub.mkdir()
    shutil.copytree(work / "Audiobook", sub / "Audiobook", dirs_exist_ok=True)
    fallback = _free_port()
    proc = AudiobookProc(sub, fallback, token_file, studio_port,
                         config={"TaskPane": {"port": _free_port(), "fallbackPort": fallback},
                                 "Audiobook": {"port": fallback}},
                         cli_port=False)
    assert proc.wait_exit() == 2
    text = proc.log_text()
    assert "Audiobook.port" in text and str(fallback) in text and "reservado" in text


def test_default_port_is_distinct_from_every_other_neven_service():
    src = (_AUDIOBOOK_SRC / "neven_audiobook_server.py").read_text(encoding="utf-8")
    assert re.search(r"^DEFAULT_PORT = 5557$", src, re.M)
    template = json.loads((_SRC / "Install" / "neven-config.template.json").read_text(encoding="utf-8"))
    taskpane = template["TaskPane"]
    assert template["Audiobook"]["port"] == 5557
    assert template["Audiobook"]["port"] not in {taskpane["port"], taskpane["fallbackPort"], 5556}
    agent = (_SRC / "AgentService" / "neven_ai_service.py").read_text(encoding="utf-8")
    assert re.search(r'"--port",\s*type=int,\s*default=5556', agent)


def _load_main_server(name):
    spec = importlib.util.spec_from_file_location(name, _STARTUP_SERVER)
    srv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(srv)
    return srv


@pytest.fixture
def studio(work, tmp_path):
    """Servidor principal REAL (startup) con Audiobook en una copia temporal."""
    root = tmp_path / "NEVEN"
    root.mkdir()
    shutil.copytree(_AUDIOBOOK_SRC, root / "Audiobook",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    static_dir = root / "taskpane"
    static_dir.mkdir()
    (static_dir / "taskpane.html").write_text("<html><head></head><body>x</body></html>", encoding="utf-8")
    token = root / "session.token"
    srv = _load_main_server("srv_prod01_" + tmp_path.name)
    port, fallback = _free_port(), _free_port()
    cfg = srv.DEFAULT_CONFIG.copy()
    cfg.update({"port": port, "fallbackPort": fallback, "staticDir": str(static_dir),
                "functionsDir": str(root / "functions"), "tokenFile": str(token),
                "audiobookDir": str(root / "Audiobook"), "pipe_client_factory": {}})
    assert srv.start_server(cfg) is not None
    ctx = {"srv": srv, "port": port, "fallback": fallback, "root": root,
           "token": token.read_text(encoding="utf-8"), "token_file": token}

    def write_config(audiobook_port, **extra):
        data = {"TaskPane": {"port": port, "fallbackPort": fallback},
                "Audiobook": {"port": audiobook_port, **extra}}
        (root / "neven-config.json").write_text(json.dumps(data), encoding="utf-8")

    ctx["write_config"] = write_config
    yield ctx
    proc = srv._audiobook_proc
    if proc is not None:
        _kill_tree(proc.pid)
    srv.stop_server()


def _studio(ctx, method, path, body=None):
    return _request(ctx["port"], method, path, body, headers={"X-NEVEN-Token": ctx["token"]})


def test_studio_and_audiobook_servers_run_together_on_different_ports(studio, ab):
    status, _, raw = _request(studio["port"], "GET", "/health")
    assert status == 200 and _json(raw)["port"] == studio["port"]
    assert _health(ab.port)["service"] == "neven-audiobook"
    assert studio["port"] != ab.port
    assert ab.port not in (studio["port"], studio["fallback"], 5555, 5556)


# ── 3b/3c/3d. Arranque desde el servidor principal ───────────────────────────
class _Impostor(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"status": "ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def test_start_refuses_a_port_held_by_another_http_service(studio):
    impostor = HTTPServer(("127.0.0.1", 0), _Impostor)
    port = impostor.server_address[1]
    threading.Thread(target=impostor.serve_forever, daemon=True).start()
    try:
        studio["write_config"](port)
        status, _, raw = _studio(studio, "POST", "/api/audiobook/start", {})
        data = _json(raw)
        assert status == 409 and data["code"] == "port_in_use"
        assert str(port) in data["message"] and "Audiobook.port" in data["message"]
        assert studio["srv"]._audiobook_proc is None
        status, _, raw = _studio(studio, "GET", "/api/audiobook/status")
        assert _json(raw)["state"] == "port_in_use"
    finally:
        impostor.shutdown()
        impostor.server_close()


def test_start_does_not_trust_a_socket_that_accepts_but_never_answers(studio):
    silent = socket.socket()
    silent.bind(("127.0.0.1", 0))
    silent.listen(5)
    port = silent.getsockname()[1]
    try:
        studio["write_config"](port)
        status, _, raw = _studio(studio, "POST", "/api/audiobook/start", {})
        assert status == 409 and _json(raw)["code"] == "port_in_use"
        assert studio["srv"]._audiobook_proc is None
    finally:
        silent.close()


def test_start_launches_the_real_server_and_reports_running(studio):
    port = _free_port()
    studio["write_config"](port)
    status, _, raw = _studio(studio, "GET", "/api/audiobook/status")
    assert _json(raw)["state"] == "not_running"
    status, _, raw = _studio(studio, "POST", "/api/audiobook/start", {})
    assert status == 200 and _json(raw)["state"] == "starting"

    def running():
        _, _, r = _studio(studio, "GET", "/api/audiobook/status")
        data = _json(r)
        assert data["state"] in ("starting", "running"), data
        return data if data["state"] == "running" else None

    data = _wait_for(running, timeout=max(60, _START_TIMEOUT))
    assert data and data["port"] == port
    health = _health(port)
    assert health["studio_port"] == studio["port"]
    assert _listeners(health["pid"], port) == [f"127.0.0.1:{port}"]
    status, _, raw = _studio(studio, "POST", "/api/audiobook/start", {})
    assert status == 200 and _json(raw)["state"] == "already_running"
    # el hijo leyo el mismo fichero de secreto que publica el servidor principal
    token = studio["token_file"].read_text(encoding="utf-8")
    status, _, _ = _request(port, "GET", "/api/system", headers={"X-NEVEN-Token": token})
    assert status == 200
    _kill_tree(health["pid"])


def test_start_reports_a_failed_launch_with_reason_and_exit_code(studio):
    port = studio["fallback"]  # reservado: el hijo debe negarse a arrancar
    studio["write_config"](port)
    status, _, raw = _studio(studio, "POST", "/api/audiobook/start", {})
    assert status == 200

    def failed():
        _, _, r = _studio(studio, "GET", "/api/audiobook/status")
        data = _json(r)
        return data if data["state"] == "failed" else None

    data = _wait_for(failed, timeout=40)
    assert data, "el estado nunca paso a failed"
    assert "codigo 2" in data["detail"]
    assert "reservado" in data["detail"]


def test_start_without_the_audiobook_script_is_a_visible_404(studio):
    studio["srv"]._config["audiobookDir"] = str(studio["root"] / "no-existe")
    status, _, raw = _studio(studio, "POST", "/api/audiobook/start", {})
    assert status == 404 and "no encontrado" in _json(raw)["message"]


# ── 4. Autenticacion con servidor real ────────────────────────────────────────
def _jobs_empty(ab, token_file):
    status, _, raw = _request(ab.port, "GET", "/api/jobs", headers=_auth(token_file))
    assert status == 200
    data = _json(raw)
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    return not jobs


PROTECTED = [
    ("POST", "/api/upload"),
    ("POST", "/api/generate"),
    ("POST", "/api/extract"),
    ("POST", "/api/generate-from-markdown"),
    ("POST", "/api/markdown/upload"),
    ("PUT", "/api/markdown/x"),
    ("POST", "/api/translate/deepl/configure"),
    ("POST", "/api/serve"),
    ("POST", "/api/preview-voice"),
    ("GET", "/api/system"),
    ("GET", "/api/jobs"),
    ("GET", "/api/voices"),
    ("GET", "/api/qr"),
]


@pytest.mark.parametrize("method,path", PROTECTED)
def test_protected_endpoints_reject_requests_without_the_secret(ab, token_file, method, path):
    body = {"api_key": SENTINEL_KEY} if "deepl" in path else {}
    status, _, raw = _request(ab.port, method, path, body if method != "GET" else None)
    assert status == 401
    assert _json(raw)["code"] == "auth_required"
    status, _, _ = _request(ab.port, method, path, body if method != "GET" else None,
                            headers={"X-NEVEN-Token": "x" * 43})
    assert status == 401


def test_rejected_requests_execute_nothing(ab, token_file):
    uploads = ab.root / "uploads"
    before = sorted(p.name for p in uploads.glob("*")) if uploads.exists() else []
    for method, path in PROTECTED:
        _request(ab.port, method, path, {"api_key": SENTINEL_KEY} if method != "GET" else None)
    after = sorted(p.name for p in uploads.glob("*")) if uploads.exists() else []
    assert before == after
    assert _jobs_empty(ab, token_file)
    assert SENTINEL_KEY not in ab.log_text()


def test_correct_secret_reaches_the_handler(ab, token_file):
    for method, path in (("POST", "/api/upload"), ("POST", "/api/extract"),
                         ("POST", "/api/generate-from-markdown"), ("POST", "/api/serve")):
        status, _, _ = _request(ab.port, method, path, {}, headers=_auth(token_file))
        assert status not in (401, 403) and status < 500, (path, status)
    status, _, _ = _request(ab.port, "GET", "/api/system", headers=_auth(token_file))
    assert status == 200
    status, _, raw = _request(ab.port, "POST", "/api/upload", {}, headers=_auth(token_file))
    assert status == 400


# ── 9. La clave de terceros no llega al registro ─────────────────────────────
def test_third_party_key_is_never_logged(ab, token_file):
    _request(ab.port, "POST", "/api/translate/deepl/configure", {"api_key": SENTINEL_KEY})
    _request(ab.port, "POST", "/api/translate/deepl/configure", {"api_key": SENTINEL_KEY},
             headers={**_auth(token_file), "Origin": "https://evil.example"})
    _request(ab.port, "POST", "/api/translate/deepl/configure", {"api_key": SENTINEL_KEY},
             headers=_auth(token_file))
    assert SENTINEL_KEY not in ab.log_text()
    assert token_file.read_text(encoding="utf-8").strip() not in ab.log_text()


# ── 6. Origin y Host ──────────────────────────────────────────────────────────
def test_foreign_origin_is_rejected_even_with_a_valid_secret(ab, token_file, studio_port):
    h = _auth(token_file)
    for origin in ("https://evil.example", f"http://localhost:{studio_port + 1}",
                   f"http://evil.example:{studio_port}"):
        status, hdrs, raw = _request(ab.port, "POST", "/api/upload", {}, headers={**h, "Origin": origin})
        assert status == 403, origin
        assert _json(raw)["code"] == "forbidden_origin"
        assert "access-control-allow-origin" not in hdrs


def test_foreign_host_is_rejected(ab, token_file):
    for host in (f"evil.example:{ab.port}", "localhost", f"localhost:{ab.port + 1}"):
        status, _, _ = _request(ab.port, "GET", "/api/health", host=host)
        assert status == 403, host
        status, _, _ = _request(ab.port, "GET", "/api/system", headers=_auth(token_file), host=host)
        assert status == 403, host
    status, _, _ = _request(ab.port, "GET", "/api/health", host=f"localhost:{ab.port}")
    assert status == 200


def test_studio_origin_is_echoed_and_never_a_wildcard(ab, token_file, studio_port):
    origin = f"https://localhost:{studio_port}"
    status, hdrs, _ = _request(ab.port, "GET", "/api/system",
                               headers={**_auth(token_file), "Origin": origin})
    assert status == 200
    assert hdrs["access-control-allow-origin"] == origin
    assert "x-neven-token" in hdrs["access-control-allow-headers"].lower()
    status, hdrs, _ = _request(ab.port, "GET", "/api/health")
    assert "access-control-allow-origin" not in hdrs


def test_preflight_from_a_foreign_origin_gets_no_cors_headers(ab, studio_port):
    status, hdrs, _ = _request(ab.port, "OPTIONS", "/api/upload", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert status == 403
    assert "access-control-allow-origin" not in hdrs
    status, hdrs, _ = _request(ab.port, "OPTIONS", "/api/upload", headers={
        **_studio_origin(studio_port), "Access-Control-Request-Method": "POST"})
    assert status == 204
    assert hdrs["access-control-allow-origin"] == f"https://localhost:{studio_port}"


# ── 7. Rotacion del secreto ───────────────────────────────────────────────────
def test_secret_rotation_is_accepted_without_restart(ab, token_file):
    original = token_file.read_text(encoding="utf-8")
    old = {"X-NEVEN-Token": original.strip()}
    try:
        assert _request(ab.port, "GET", "/api/system", headers=old)[0] == 200
        token_file.write_text("secret-B-rotated-" + "b" * 30, encoding="utf-8")
        assert _request(ab.port, "GET", "/api/system", headers=old)[0] == 401
        new = {"X-NEVEN-Token": token_file.read_text(encoding="utf-8").strip()}
        assert _request(ab.port, "GET", "/api/system", headers=new)[0] == 200
        token_file.unlink()
        status, _, raw = _request(ab.port, "GET", "/api/system", headers=new)
        assert status == 401 and _json(raw)["code"] == "token_unavailable"
        token_file.write_text("", encoding="utf-8")
        status, _, raw = _request(ab.port, "GET", "/api/system", headers=new)
        assert status == 401 and _json(raw)["code"] == "token_unavailable"
    finally:
        token_file.write_text(original, encoding="utf-8")
    assert _request(ab.port, "GET", "/api/system", headers=old)[0] == 200


# ── 5. Cobertura por construccion ─────────────────────────────────────────────
_COVERAGE_SCRIPT = r"""
import json, os, re, sys, tempfile
sys.path.insert(0, sys.argv[1])
import neven_audiobook_server as m
d = tempfile.mkdtemp()
app = m.create_app(d + '/u', d + '/o', port=5557, studio_ports={5555}, token_file=d + '/none.token')
client = app.test_client()
exempt = {('GET', '/api/health'), ('GET', '/api/download/x'), ('GET', '/download'), ('GET', '/')}
out = []
for rule in app.url_map.iter_rules():
    if not rule.rule.startswith('/api/'):
        continue
    path = re.sub(r'<[^>]+>', 'x', rule.rule)
    for method in sorted(rule.methods - {'HEAD', 'OPTIONS'}):
        status = client.open(path, method=method, base_url='http://127.0.0.1:5557').status_code
        out.append([method, path, status, (method, path) in exempt])
print('RESULT' + json.dumps(out))
"""


def test_every_api_route_is_protected_unless_explicitly_exempt(tmp_path):
    result = subprocess.run([sys.executable, "-c", _COVERAGE_SCRIPT, str(_AUDIOBOOK_SRC)],
                            capture_output=True, text=True, timeout=120,
                            env={**os.environ, "PYTHONUTF8": "1"})
    line = next((ln for ln in result.stdout.splitlines() if ln.startswith("RESULT")), None)
    assert line, result.stdout + result.stderr
    rows = json.loads(line[len("RESULT"):])
    assert len(rows) >= 25
    for method, path, status, exempt in rows:
        if exempt:
            assert status != 401, (method, path)
        else:
            assert status == 401, (method, path, status)


# ── 8. Paridad con SEC-01 ─────────────────────────────────────────────────────
def test_auth_rules_match_the_main_server():
    spec = importlib.util.spec_from_file_location("ab_local_auth", _AUDIOBOOK_SRC / "neven_local_auth.py")
    auth = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auth)
    srv = _load_main_server("srv_prod01_parity")
    srv._server_port = 5555
    srv._session_token = "s" * 43
    hosts = ["localhost:5555", "127.0.0.1:5555", "[::1]:5555", "LOCALHOST:5555", "localhost:5556",
             "localhost", "", None, "evil.example:5555", "localhost:55555", "localhost:abc",
             "localhost:5555x", " localhost:5555 ", "[::1]", "[::1]:5556"]
    for h in hosts:
        assert auth.host_is_local(h, 5555) == srv._host_is_local(h), h
    origins = ["https://localhost:5555", "http://127.0.0.1:5555", "http://localhost:5556",
               "https://evil.example:5555", "null", "", "ftp://localhost:5555", "http://localhost",
               "http://[::1]:5555", "http://localhost:99999", "https://localhost:5555.evil.example"]
    for o in origins:
        assert auth.origin_is_local(o, {5555}) == srv._origin_is_local(o), o
    for t in ["s" * 43, "s" * 42, "", None, "S" * 43, "é" * 10]:
        assert auth.token_matches(t, "s" * 43) == srv._token_matches(t), t
