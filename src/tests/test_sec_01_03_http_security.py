# NEVEN - SEC-01 / SEC-03: autenticacion por secreto de sesion, CORS sin comodin
# y /api/save_script restringido. Arranca el servidor REAL en un puerto libre y
# se ejecuta contra las TRES copias versionadas del servidor.
import http.client
import importlib.util
import json
import os
import socket
import tempfile

import pytest

_SRC = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
os.environ["NEVEN_LOG_DIR"] = tempfile.mkdtemp(prefix="neven_test_log_")

SERVER_COPIES = {
    "taskpane":      os.path.join(_SRC, "TaskPane", "neven_http_server.py"),
    "startup":       os.path.join(_SRC, "startup", "neven_http_server.py"),
    "controlpython": os.path.join(_SRC, "ControlPython", "startup", "neven_http_server.py"),
}


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _FakePipe:
    calls = []

    def send_code(self, lines, wait=True):
        _FakePipe.calls.append(list(lines))
        raise _FakePipe.error("fake engine")

    def close(self):
        pass


@pytest.fixture(params=sorted(SERVER_COPIES), scope="module")
def live(request, tmp_path_factory):
    path = SERVER_COPIES[request.param]
    spec = importlib.util.spec_from_file_location("srv_sec_" + request.param, path)
    srv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(srv)
    _FakePipe.error = srv._PipeClientError
    _FakePipe.calls = []

    root = tmp_path_factory.mktemp("sec")
    functions_dir = root / "functions"
    functions_dir.mkdir()
    static_dir = root / "static"
    static_dir.mkdir()
    (static_dir / "taskpane.html").write_text("<html><head></head><body>x</body></html>", encoding="utf-8")
    outside = root / "outside"
    outside.mkdir()
    token_file = root / "session.token"
    port = _free_port()
    cfg = srv.DEFAULT_CONFIG.copy()
    cfg.update({"port": port, "fallbackPort": _free_port(), "staticDir": str(static_dir),
                "functionsDir": str(functions_dir), "tokenFile": str(token_file),
                "pipe_client_factory": {"python": _FakePipe}})
    result = srv.start_server(cfg)
    assert result is not None
    _, bound = result
    yield {"srv": srv, "port": bound, "functions": functions_dir, "outside": outside,
           "token": token_file.read_text(encoding="utf-8"), "token_file": token_file}
    srv.stop_server()


def _req(live, method, path, body=None, headers=None, token=True, host=None):
    h = dict(headers or {})
    if token:
        h["X-NEVEN-Token"] = live["token"]
    conn = http.client.HTTPConnection("127.0.0.1", live["port"], timeout=10)
    conn.putrequest(method, path, skip_host=host is not None)
    if host is not None:
        conn.putheader("Host", host)
    data = None
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


# ── Secreto de sesion ─────────────────────────────────────────────────────────

def test_token_is_generated_at_startup_and_not_constant(live):
    assert len(live["token"]) >= 32
    first = live["token"]
    assert live["srv"]._init_session_token() != first
    live["token"] = live["token_file"].read_text(encoding="utf-8")  # el servidor rota el secreto


def test_exec_endpoint_without_token_is_rejected_and_does_not_execute(live):
    _FakePipe.calls.clear()
    for lang in ("r", "python", "julia"):
        status, _, raw = _req(live, "POST", "/api/" + lang, {"code": "1+1"}, token=False)
        assert status == 401
        assert json.loads(raw)["code"] == "auth_required"
    assert _FakePipe.calls == []


def test_exec_endpoint_with_wrong_token_is_rejected(live):
    status, _, _ = _req(live, "POST", "/api/python", {"code": "1+1"},
                        headers={"X-NEVEN-Token": "x" * 43}, token=False)
    assert status == 401
    assert _FakePipe.calls == []


def test_exec_endpoint_with_token_reaches_the_engine(live):
    _FakePipe.calls.clear()
    status, _, _ = _req(live, "POST", "/api/python", {"code": "1+1"})
    assert status == 200
    assert _FakePipe.calls == [["1+1"]]


@pytest.mark.parametrize("path", ["api/datalab/run", "api/rpivot", "api/functions/create",
                                  "api/packages/install", "api/db_connect", "api/bridge/write",
                                  "api/engines/config", "api/shutdown", "api/audiobook/start"])
def test_every_post_requires_token(live, path):
    status, _, _ = _req(live, "POST", "/" + path, {}, token=False)
    assert status == 401


def test_save_script_without_token_writes_nothing(live):
    target = live["functions"] / "nope.R"
    status, _, _ = _req(live, "POST", "/api/save_script",
                        {"path": str(target), "content": "x"}, token=False)
    assert status == 401
    assert not target.exists()


# ── CORS / Origin / Host ──────────────────────────────────────────────────────

def test_no_wildcard_cors(live):
    status, hdrs, _ = _req(live, "GET", "/health", token=False)
    assert status == 200
    assert hdrs.get("access-control-allow-origin") != "*"
    status, hdrs, _ = _req(live, "GET", "/health", headers={"Origin": "http://localhost:5555"}, token=False)
    assert hdrs.get("access-control-allow-origin") == "http://localhost:5555"


def test_foreign_origin_is_rejected(live):
    for method, path in (("GET", "/health"), ("OPTIONS", "/api/python")):
        status, hdrs, _ = _req(live, method, path, headers={"Origin": "https://evil.example"}, token=False)
        assert status == 403
        assert "access-control-allow-origin" not in hdrs
    _FakePipe.calls.clear()
    status, _, _ = _req(live, "POST", "/api/python", {"code": "1"}, headers={"Origin": "https://evil.example"})
    assert status == 403
    assert _FakePipe.calls == []


def test_foreign_host_is_rejected(live):
    status, _, _ = _req(live, "GET", "/health", token=False, host="evil.example:5555")
    assert status == 403


# ── Entrega del secreto al TaskPane ───────────────────────────────────────────

def test_taskpane_html_receives_token_meta(live):
    status, hdrs, raw = _req(live, "GET", "/taskpane.html", token=False)
    assert status == 200
    assert ('<meta name="neven-token" content="%s">' % live["token"]).encode() in raw
    assert hdrs.get("cache-control") == "no-store"
    status, _, raw = _req(live, "GET", "/taskpane.html", headers={"Origin": "https://evil.example"}, token=False)
    assert status == 403 and live["token"].encode() not in raw


# ── /api/save_script (SEC-03) ─────────────────────────────────────────────────

def test_save_script_accepts_valid_paths(live):
    target = live["functions"] / "ok.R"
    status, _, _ = _req(live, "POST", "/api/save_script", {"path": str(target), "content": "x <- 1"})
    assert status == 200 and target.read_text(encoding="utf-8") == "x <- 1"
    status, _, _ = _req(live, "POST", "/api/save_script", {"path": "rel.py", "content": "y = 2"})
    assert status == 200 and (live["functions"] / "rel.py").exists()


def test_save_script_rejects_absolute_path_outside_allowed_dirs(live):
    target = live["outside"] / "evil.py"
    status, _, _ = _req(live, "POST", "/api/save_script", {"path": str(target), "content": "x"})
    assert status == 403
    assert not target.exists()


def test_save_script_rejects_traversal(live):
    for p in (os.path.join(str(live["functions"]), "..", "outside", "evil.py"),
              "..\\outside\\evil2.py", "../outside/evil3.py"):
        status, _, _ = _req(live, "POST", "/api/save_script", {"path": p, "content": "x"})
        assert status == 403
    assert os.listdir(live["outside"]) == []
