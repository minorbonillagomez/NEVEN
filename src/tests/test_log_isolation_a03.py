# NEVEN - A-03: la suite no debe escribir en el log de produccion (C:\NEVEN).
# El logger "NEVEN.HTTP" es global del proceso y el servidor solo le anade su
# RotatingFileHandler la primera vez que se importa; si el primer importador no
# fijo NEVEN_LOG_DIR, todos los servidores de prueba escriben en C:\NEVEN.
import importlib.util
import logging
import os
import pathlib

_SRC = pathlib.Path(__file__).resolve().parent.parent
_COPIES = (
    _SRC / "startup" / "neven_http_server.py",
    _SRC / "TaskPane" / "neven_http_server.py",
    _SRC / "ControlPython" / "startup" / "neven_http_server.py",
)
_PROD = os.path.normcase(os.path.normpath(r"C:\NEVEN"))


def _inside_prod(path):
    p = os.path.normcase(os.path.realpath(path))
    return p == _PROD or p.startswith(_PROD + os.sep)


def test_log_dir_is_not_production():
    log_dir = os.environ.get("NEVEN_LOG_DIR")
    assert log_dir, "NEVEN_LOG_DIR no esta fijado para la suite"
    assert not _inside_prod(log_dir), log_dir


def test_http_server_handlers_never_point_at_production():
    for i, path in enumerate(_COPIES):
        spec = importlib.util.spec_from_file_location(f"_neven_http_a03_{i}", str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    handlers = [h for h in logging.getLogger("NEVEN.HTTP").handlers
                if hasattr(h, "baseFilename")]
    for h in handlers:
        assert not _inside_prod(h.baseFilename), h.baseFilename
    log_dir = os.path.normcase(os.path.realpath(os.environ["NEVEN_LOG_DIR"]))
    for h in handlers:
        assert os.path.normcase(os.path.realpath(os.path.dirname(h.baseFilename))) == log_dir, h.baseFilename
