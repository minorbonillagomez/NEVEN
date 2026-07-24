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

    result = start_server(config)
    if result is None:
        print("FATAL: Server failed to start")
        sys.exit(1)

    print(f"NEVEN HTTP Server running on port {result[1]}")
    print("Open: http://localhost:{}/taskpane.html".format(result[1]))
    print("Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()
