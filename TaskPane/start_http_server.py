"""NEVEN HTTP Server — Standalone launcher.
Run: python start_http_server.py
Serves Task Pane and API on localhost:5555.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\NEVEN\startup")
from neven_http_server import start_server
import time

def main():
    config_path = r"C:\NEVEN\neven-config.json"
    config = {}
    if os.path.isfile(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            full_config = json.load(f)
        config = full_config.get("TaskPane", {})

    config.setdefault("enabled", True)
    config.setdefault("port", 5555)
    config.setdefault("fallbackPort", 5556)
    config.setdefault("staticDir", "C:/NEVEN/taskpane")
    config.setdefault("viewersDir", "C:/NEVEN/workspace")
    config.setdefault("queryTimeoutSec", 30)
    config.setdefault("maxPayloadMB", 50)

    # Run server on MAIN thread (not daemon)
    from neven_http_server import _config, NEVENHandler, _rate_limiter
    from http.server import HTTPServer
    import ssl as ssl_mod

    global _server_port
    _config.update(config)

    ports = [config.get("port", 5555), config.get("fallbackPort", 5556)]
    server = None
    for port in ports:
        try:
            server = HTTPServer(('127.0.0.1', port), NEVENHandler)
            print(f"[NEVEN HTTP] Bound to 127.0.0.1:{port}")
            break
        except OSError as e:
            print(f"[NEVEN HTTP] Port {port} unavailable: {e}")

    if server is None:
        print("FATAL: Cannot bind")
        sys.exit(1)

    # HTTPS if certs available
    cert_path = config.get("certPath", "")
    key_path = config.get("keyPath", "")
    if cert_path and key_path and os.path.isfile(cert_path) and os.path.isfile(key_path):
        try:
            ctx = ssl_mod.SSLContext(ssl_mod.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
            server.socket = ctx.wrap_socket(server.socket, server_side=True)
            print(f"[NEVEN HTTP] HTTPS enabled")
        except Exception as e:
            print(f"[NEVEN HTTP] HTTPS failed: {e} — HTTP only")
    else:
        print("[NEVEN HTTP] Running HTTP (no cert)")

    print(f"NEVEN HTTP Server on port {port}")
    print(f"Open: http://localhost:{port}/taskpane.html")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
        server.shutdown()

if __name__ == "__main__":
    main()
