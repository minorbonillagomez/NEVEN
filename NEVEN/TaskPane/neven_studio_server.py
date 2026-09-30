"""NEVEN Studio — Servidor HTTP standalone para pruebas.

Corre el servidor en el thread PRINCIPAL (no daemon) para que sea
estable desde Kiro y desde terminales.

Uso:
    python neven_studio_server.py
    python neven_studio_server.py --port 5555
"""
import sys
import os

# Agregar startup al path
sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "ControlPython", "startup"
)))

from http.server import HTTPServer
from neven_http_server import NEVENHandler, _config, DEFAULT_CONFIG
import json

def main():
    port = 5555
    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg == "--port" and sys.argv.index(arg) + 1 < len(sys.argv):
            port = int(sys.argv[sys.argv.index(arg) + 1])

    # Config sin certs (HTTP puro)
    config = {
        **DEFAULT_CONFIG,
        "port": port,
        "certPath": "",
        "keyPath":  "",
        "staticDir":  r"C:\NEVEN\taskpane",
        "viewersDir": r"C:\NEVEN\workspace",
        "pipe_client_factory": {},
    }
    _config.update(config)

    # Importar _server_port y setearlo
    import neven_http_server as srv
    srv._server_port = port

    server = HTTPServer(("127.0.0.1", port), NEVENHandler)
    print(f"[NEVEN Studio] HTTP server en http://localhost:{port}/taskpane.html")
    print("[NEVEN Studio] Ctrl+C para detener")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[NEVEN Studio] Detenido")
        server.server_close()

if __name__ == "__main__":
    main()
