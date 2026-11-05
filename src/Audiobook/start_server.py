#!/usr/bin/env python
"""
NEVEM Studio - Server Launcher
"""
import os
import sys

# Asegurar que src está en el path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from server.http_server import NevemServer

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = NevemServer(port)
    server.start()
