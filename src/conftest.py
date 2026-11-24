"""Configuracion comun de pytest para los tests de Python de NEVEN (B-02).

ControlPython carga las funciones con ``register_function``, que el host
inyecta como builtin. Fuera del host no existe, asi que se define aqui un
registro vacio para poder importar los modulos. Solo afecta a pytest.
"""
import builtins
import os
import sys

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
