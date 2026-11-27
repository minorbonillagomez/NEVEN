"""Configuracion comun de pytest para los tests de Python de NEVEN (B-02).

ControlPython carga las funciones con ``register_function``, que el host
inyecta como builtin. Fuera del host no existe, asi que se define aqui un
registro vacio para poder importar los modulos. Solo afecta a pytest.
"""
import atexit
import builtins
import os
import shutil
import sys
import tempfile

_SRC = os.path.dirname(os.path.abspath(__file__))
for _p in (
    os.path.join(_SRC, "ControlPython", "startup"),
    os.path.join(_SRC, "libreria", "PYTHON"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

if not hasattr(builtins, "register_function"):
    def _register_function(*args, **kwargs):
        return None
    builtins.register_function = _register_function

# A-03: los logs de la suite van a un directorio temporal, nunca a C:\NEVEN.
# El logger "NEVEN.HTTP" es global del proceso y neven_http_server.py le engancha su
# RotatingFileHandler en el primer import (con NEVEN_LOG_DIR por defecto C:\NEVEN).
# Varios tests de TaskPane\tests lo importan al recolectar sin fijar la variable, y
# ese handler lo heredan despues todos los servidores de prueba. Se fija aqui,
# incondicionalmente, antes de recolectar nada. Los subprocesos la heredan.
_TEST_LOG_DIR = tempfile.mkdtemp(prefix="neven_test_log_")
os.environ["NEVEN_LOG_DIR"] = _TEST_LOG_DIR
atexit.register(shutil.rmtree, _TEST_LOG_DIR, ignore_errors=True)
