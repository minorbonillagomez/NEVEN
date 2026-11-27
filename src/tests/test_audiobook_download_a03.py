# NEVEN - A-03: endpoint de descarga de audiolibros, pagina /download y extension .m4b.
# Arranca el servidor REAL (neven_audiobook_server.py como subproceso) sobre una copia
# temporal de src/Audiobook, en un puerto libre y con una carpeta de salida temporal.
# Nada se escribe fuera de directorios temporales.
import http.client
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse

import pytest

pytest.importorskip("flask")

_SRC = pathlib.Path(__file__).resolve().parent.parent
_AUDIOBOOK_SRC = _SRC / "Audiobook"
_JS_CHECK = _SRC / "tests" / "js" / "audiobook_download_check.js"

WORST_NAME = "Miguel de Cervantes - Don Quijote de la Mancha \u00e1 \u00e9 \u00ed.m4b"
WORST_BYTES = b"WORST-CASE-AUDIO-" + bytes(range(256)) * 8
TOKEN = "secret-A-" + "a" * 34


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _request(port, method, path, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    conn.request(method, path, headers=dict(headers or {}))
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


def _q(name):
    return urllib.parse.quote(name, safe="")


_START_TIMEOUT = float(os.environ.get("NEVEN_TEST_START_TIMEOUT", "180"))


def _wait_health(proc, port, log, timeout=_START_TIMEOUT):
    end = time.time() + timeout
    while time.time() < end:
        if proc.poll() is not None:
            break
        try:
            status, _, raw = _request(port, "GET", "/api/health")
            if status == 200:
                return _json(raw)
        except OSError:
            pass
        time.sleep(0.3)
    pytest.fail("el servidor no arranco:\n" + pathlib.Path(log).read_text(encoding="utf-8", errors="replace"))


class Server:
    def __init__(self, root, output):
        self.root = pathlib.Path(root)
        self.output = pathlib.Path(output)
        self.port = _free_port()
        self.studio_port = _free_port()
        self.token_file = self.root / "session.token"
        self.token_file.write_text(TOKEN, encoding="utf-8")
        self.log = self.root / "audiobook-test.log"
        env = dict(os.environ)
        env["NEVEN_TOKEN_FILE"] = str(self.token_file)
        env["NEVEN_STUDIO_PORT"] = str(self.studio_port)
        env["PYTHONUTF8"] = "1"
        cmd = [sys.executable, str(self.root / "Audiobook" / "neven_audiobook_server.py"),
               "--port", str(self.port), "--output-folder", str(self.output)]
        with open(self.log, "wb") as fh:
            self.proc = subprocess.Popen(cmd, cwd=str(self.root / "Audiobook"), env=env,
                                         stdout=fh, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL)
        self.health = _wait_health(self.proc, self.port, self.log)

    def get(self, path, headers=None):
        return _request(self.port, "GET", path, headers)

    def stop(self):
        pid = self.health.get("pid") if self.health else None
        for p in (pid, self.proc.pid):
            if p:
                subprocess.run(["taskkill", "/PID", str(p), "/T", "/F"], capture_output=True)
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    root = tmp_path_factory.mktemp("a03")
    shutil.copytree(_AUDIOBOOK_SRC, root / "Audiobook",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (root / "taskpane").mkdir()
    return root


@pytest.fixture(scope="module")
def srv(work):
    output = work / "out"
    output.mkdir()
    (output / WORST_NAME).write_bytes(WORST_BYTES)
    (output / "a b.m4b").write_bytes(b"SPACE-FILE")
    (output / "legacy.m4a").write_bytes(b"LEGACY-M4A")
    # secreto fuera de la carpeta de salida y hermano con el mismo prefijo
    (work / "secret.txt").write_bytes(b"TOP-SECRET")
    sibling = work / "out_x"
    sibling.mkdir()
    (sibling / "evil.m4b").write_bytes(b"EVIL-SIBLING")
    server = Server(work, output)
    yield server
    server.stop()


def _auth():
    return {"X-NEVEN-Token": TOKEN}


# 1. Nombre legal del peor caso, por URL codificada
def test_worst_case_name_downloads_exact_bytes(srv):
    status, hdrs, raw = srv.get("/api/download/" + _q(WORST_NAME))
    assert status == 200
    assert raw == WORST_BYTES
    assert hdrs["content-type"].startswith("audio/mp4")
    disp = hdrs["content-disposition"]
    assert "attachment" in disp
    assert urllib.parse.quote(WORST_NAME, safe="") in disp or "filename*=" in disp


# 2. El fallback por prefijo ya no existe
@pytest.mark.parametrize("name", ["Miguel", "Miguel%20de", "a", "legacy"])
def test_prefix_does_not_resolve_to_another_file(srv, name):
    status, _, raw = srv.get("/api/download/" + name)
    assert status == 404
    assert "requested" in _json(raw)
    assert b"WORST-CASE" not in raw and b"SPACE-FILE" not in raw and b"LEGACY" not in raw


# 3. Sin doble decodificacion
def test_percent_encoded_percent_is_not_decoded_twice(srv):
    status, _, raw = srv.get("/api/download/a%2520b.m4b")
    assert status == 404
    assert b"SPACE-FILE" not in raw
    status, _, raw = srv.get("/api/download/a%20b.m4b")
    assert status == 200 and raw == b"SPACE-FILE"


# 4. Travesia y directorio hermano con el mismo prefijo
@pytest.mark.parametrize("path", [
    "..%2f..%2fsecret.txt",
    "%2e%2e/secret.txt",
    "..%2fsecret.txt",
    "..%5csecret.txt",
    "..%5cout_x%5cevil.m4b",
    "..%2fout_x%2fevil.m4b",
    "%2e%2e%2fout_x%2fevil.m4b",
    "C%3A%5CWindows%5Cwin.ini",
    "%2FWindows%2Fwin.ini",
])
def test_traversal_and_sibling_never_served(srv, path):
    status, _, raw = srv.get("/api/download/" + path)
    # 308: Flask normaliza '//' por redireccion; no es contenido servido\n    assert status in (403, 404, 308), (path, status)
    assert b"TOP-SECRET" not in raw and b"EVIL-SIBLING" not in raw


# 5. Inexistente y guardia de autenticacion intacta
def test_missing_file_is_404_with_reason(srv):
    status, _, raw = srv.get("/api/download/no-existe.m4b")
    assert status == 404
    assert _json(raw)["requested"] == "no-existe.m4b"


def test_download_guard_unchanged(srv):
    status, _, _ = srv.get("/api/download/" + _q(WORST_NAME), headers=dict(_auth(), Origin="https://evil.example"))
    assert status == 403
    status, _, _ = srv.get("/api/download/" + _q(WORST_NAME))  # sin token: exento (QR/movil)
    assert status == 200
    conn = http.client.HTTPConnection("127.0.0.1", srv.port, timeout=15)
    conn.request("POST", "/api/upload", body=b"x", headers={"Content-Type": "application/octet-stream"})
    resp = conn.getresponse()
    resp.read()
    conn.close()
    assert resp.status == 401


# 6. Pagina /download
def test_download_page_href_is_encoded_and_followable(srv, work):
    out = srv.output
    older = out / "viejo.m4a"
    older.write_bytes(b"OLDER")
    now = time.time()
    os.utime(older, (now - 500, now - 500))
    for f in out.iterdir():
        if f != older:
            os.utime(f, (now - 100, now - 100))
    os.utime(out / WORST_NAME, (now, now))
    status, _, raw = srv.get("/download")
    assert status == 200
    html = raw.decode("utf-8")
    href = re.search(r'<a href="([^"]+)" class="download-btn"', html).group(1)
    assert href == "/api/download/" + _q(WORST_NAME)
    assert "%C3%A1" in href and "%20" in href
    status, _, body = srv.get(href)
    assert status == 200 and body == WORST_BYTES


def test_download_page_lists_legacy_m4a_and_empty_is_404(work):
    out = work / "out_only_m4a"
    out.mkdir()
    (out / "solo.m4a").write_bytes(b"ONLY-M4A")
    root = work / "p2"
    root.mkdir()
    shutil.copytree(work / "Audiobook", root / "Audiobook", dirs_exist_ok=True)
    server = Server(root, out)
    try:
        status, _, raw = server.get("/download")
        assert status == 200 and b"/api/download/solo.m4a" in raw
        (out / "solo.m4a").unlink()
        status, _, raw = server.get("/download")
        assert status == 404 and b"No hay archivos disponibles" in raw
    finally:
        server.stop()


# 7. Extension .m4b coherente
def test_constants_and_listings(srv):
    sys.path.insert(0, str(_AUDIOBOOK_SRC))
    try:
        from muxer.ffmpeg_muxer import DEFAULT_AUDIOBOOK_EXTENSION, AUDIOBOOK_EXTENSIONS
    finally:
        sys.path.remove(str(_AUDIOBOOK_SRC))
    assert DEFAULT_AUDIOBOOK_EXTENSION == ".m4b"
    assert AUDIOBOOK_EXTENSIONS == (".m4b", ".m4a")
    status, _, raw = srv.get("/api/books", headers=_auth())
    assert status == 200
    names = {b["filename"] for b in _json(raw)}
    assert WORST_NAME in names and "legacy.m4a" in names
    titles = {b["title"] for b in _json(raw)}
    assert "legacy" in titles and "a b" in titles


def test_pipeline_writes_m4b():
    text = (_AUDIOBOOK_SRC / "pipeline.py").read_text(encoding="utf-8")
    muxer = (_AUDIOBOOK_SRC / "muxer" / "ffmpeg_muxer.py").read_text(encoding="utf-8")
    assert re.search(r'^DEFAULT_AUDIOBOOK_EXTENSION = "\.m4b"', muxer, re.M)
    assert "DEFAULT_AUDIOBOOK_EXTENSION" in text and '".m4a"' not in text


# 8. Muxer real con ffmpeg
@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")),
                    reason="ffmpeg/ffprobe no estan en el PATH")
def test_real_muxer_output_is_m4b_and_downloads_identically(srv, tmp_path):
    wav = tmp_path / "ch1.wav"
    r = subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                        "-ar", "24000", "-ac", "1", str(wav)], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")[-500:]
    sys.path.insert(0, str(_AUDIOBOOK_SRC))
    try:
        from muxer.ffmpeg_muxer import FFmpegMuxer, ChapterMarker, DEFAULT_AUDIOBOOK_EXTENSION
        muxer = FFmpegMuxer()
        out = srv.output / ("muxer-real" + DEFAULT_AUDIOBOOK_EXTENSION)
        ok = muxer.create_from_chapter_audio([(str(wav), "Capitulo 1", 2000)], str(out), "Prueba", "Autor")
    finally:
        sys.path.remove(str(_AUDIOBOOK_SRC))
    assert ok and out.is_file() and out.suffix == ".m4b"
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                            "-show_chapters", "-of", "json", str(out)], capture_output=True)
    info = json.loads(probe.stdout.decode("utf-8"))
    assert "mp4" in info["format"]["format_name"]
    assert any(s["codec_name"] == "aac" for s in info["streams"] if s["codec_type"] == "audio")
    status, _, raw = srv.get("/api/download/" + _q(out.name))
    assert status == 200 and raw == out.read_bytes()


# 9. Cliente JS con DOM simulado
@pytest.mark.skipif(not shutil.which("node"), reason="node no esta en el PATH")
def test_taskpane_download_does_not_navigate():
    r = subprocess.run(["node", str(_JS_CHECK)], capture_output=True, timeout=60)
    out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    assert r.returncode == 0, out
    assert "todos los casos pasaron" in out
