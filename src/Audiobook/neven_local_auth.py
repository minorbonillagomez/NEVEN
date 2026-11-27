"""
Autenticacion local del servidor de audiolibros de NEVEN (SEC-16).

Aplica las mismas reglas que el servidor principal (startup/neven_http_server.py,
SEC-01): cabecera X-NEVEN-Token comparada en tiempo constante, Host local con el
puerto exacto del servidor y Origin local con el puerto de Studio. Solo usa la
libreria estandar.

El secreto no se genera aqui: lo publica el servidor principal en un fichero por
usuario (NEVEN_TOKEN_FILE, o %LOCALAPPDATA%\\NEVEN\\session.token). Se relee en
cada peticion (cache por mtime), de modo que una rotacion del secreto se acepta
sin reiniciar este servidor. Sin fichero o vacio, se rechaza (falla cerrado).
"""
import hmac
import os
import threading
from urllib.parse import urlparse

TOKEN_HEADER = "X-NEVEN-Token"
LOCAL_HOSTNAMES = ("localhost", "127.0.0.1", "::1")


def host_is_local(host_header, own_port):
    """True si la cabecera Host nombra esta maquina en el puerto exacto de este servidor."""
    h = (host_header or "").strip().lower()
    if h.startswith("["):
        h, _, rest = h[1:].partition("]")
        port_s = rest[1:] if rest.startswith(":") else ""
    else:
        h, _, port_s = h.partition(":")
    return (h in LOCAL_HOSTNAMES and port_s.isascii() and port_s.isdigit()
            and int(port_s) == own_port)


def origin_is_local(origin, allowed_ports):
    """True si Origin es http(s) en un hostname local y en uno de los puertos permitidos."""
    try:
        u = urlparse(origin)
        return (u.scheme in ("http", "https") and (u.hostname or "").lower() in LOCAL_HOSTNAMES
                and u.port is not None and u.port in allowed_ports)
    except ValueError:
        return False


def token_matches(supplied, secret):
    """Comparacion en tiempo constante contra el secreto de sesion."""
    if not secret or not supplied:
        return False
    return hmac.compare_digest(supplied.encode("utf-8"), secret.encode("utf-8"))


def resolve_token_file(config=None):
    """Ruta del fichero de secreto: NEVEN_TOKEN_FILE > TaskPane.tokenFile > por defecto."""
    env = os.environ.get("NEVEN_TOKEN_FILE")
    if env:
        return env
    custom = ((config or {}).get("TaskPane") or {}).get("tokenFile")
    if custom:
        return custom
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "NEVEN", "session.token")


class TokenReader:
    """Lee el secreto del fichero y lo cachea por (mtime, tamano)."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self._sig = None
        self._value = ""

    def get(self):
        try:
            st = os.stat(self.path)
            sig = (st.st_mtime_ns, st.st_size)
            with self._lock:
                if sig != self._sig:
                    with open(self.path, "r", encoding="utf-8") as f:
                        self._value = f.read().strip()
                    self._sig = sig
                return self._value
        except OSError:
            with self._lock:
                self._sig = None
                self._value = ""
            return ""


def is_exempt(method, path):
    """Rutas sin secreto: lista de exencion, todo lo demas queda protegido."""
    if method == "GET" and path in ("/", "/download", "/api/health"):
        return True
    return method == "GET" and path.startswith("/api/download/")


def install_guard(app, own_port, studio_ports, token_reader, lan=False, log=None):
    """Instala before_request/after_request en la app Flask.

    Orden: Host, Origin, preflight, secreto. Con lan=True el control de Host solo
    se aplica a rutas no exentas (las descargas llegan por la IP de la red local).
    """
    from flask import request, jsonify, make_response

    studio_ports = frozenset(studio_ports)

    def _reject(status, code, message):
        if log:
            log.warning("Peticion rechazada (%s %s): %s", request.method, request.path, code)
        resp = jsonify({"status": "error", "code": code, "message": message})
        resp.status_code = status
        return resp

    @app.before_request
    def _guard():
        exempt = is_exempt(request.method, request.path)
        host_ok = host_is_local(request.headers.get("Host"), own_port)
        if not host_ok and not (lan and exempt):
            return _reject(403, "forbidden_origin",
                           "Peticion rechazada: Host no es local en el puerto de este servidor.")
        origin = request.headers.get("Origin")
        if origin and not origin_is_local(origin, studio_ports):
            return _reject(403, "forbidden_origin",
                           "Peticion rechazada: Origin no es local en el puerto de NEVEN Studio.")
        if request.method == "OPTIONS":
            resp = make_response("", 204)
            if origin:
                resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                resp.headers["Access-Control-Max-Age"] = "600"
            return resp
        if request.path.startswith("/api/") and not exempt:
            secret = token_reader.get()
            if not secret:
                return _reject(401, "token_unavailable",
                               "Peticion rechazada: el secreto de sesion no esta disponible. "
                               "Inicie NEVEN Studio y vuelva a intentarlo.")
            if not token_matches(request.headers.get(TOKEN_HEADER), secret):
                return _reject(401, "auth_required",
                               "Peticion rechazada: falta o es invalido el secreto de sesion "
                               "(X-NEVEN-Token). Recargue NEVEN Studio.")
        return None

    @app.after_request
    def _cors(resp):
        origin = request.headers.get("Origin")
        if origin and origin_is_local(origin, studio_ports):
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, " + TOKEN_HEADER
            resp.headers.add("Vary", "Origin")
        return resp
