# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN — Motores opcionales: disponibilidad de motores
# Cubre _detect_engine_installations en las TRES copias versionadas del servidor
# HTTP y la resolucion de motores de start_studio.resolve_languages.
# NEVEN no instala motores: aqui solo se comprueba que informa y enlaza.
# ═══════════════════════════════════════════════════════════════════════════════
import importlib.util
import inspect
import json
import os
import sys
import tempfile

import pytest

_SRC = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

# El servidor abre su fichero de log al importarse: se desvia a un temporal
# para no escribir en C:\NEVEN durante los tests.
os.environ["NEVEN_LOG_DIR"] = tempfile.mkdtemp(prefix="neven_test_log_")

#: Las tres copias versionadas del servidor (git ls-files '*neven_http_server.py')
SERVER_COPIES = {
    "taskpane":      os.path.join(_SRC, "TaskPane", "neven_http_server.py"),
    "startup":       os.path.join(_SRC, "startup", "neven_http_server.py"),
    "controlpython": os.path.join(_SRC, "ControlPython", "startup", "neven_http_server.py"),
}

_COPY_IDS = sorted(SERVER_COPIES)

#: URLs oficiales esperadas, las mismas de Common/engine_availability.h
OFFICIAL_URLS = {
    "r":      "https://cran.r-project.org/bin/windows/base/",
    "julia":  "https://julialang.org/downloads/",
    "python": "https://www.python.org/downloads/",
}

#: Dominio oficial de cada motor
OFFICIAL_HOSTS = {
    "r":      "https://cran.r-project.org/",
    "julia":  "https://julialang.org/",
    "python": "https://www.python.org/",
}

#: Claves que devuelve _detect_engine_installations por motor
ENGINE_KEYS = {"enabled", "installed", "home", "running", "url"}

#: Fichero relativo a <home> que convierte un directorio en una instalacion
HOME_MARKERS = {
    "r":      ("bin", "x64", "R.dll"),
    "julia":  ("bin", "julia.exe"),
    "python": ("python.exe",),
}

_loaded_servers = {}


def _load_server(name):
    """Import one copy of the server under its own module name."""
    if name not in _loaded_servers:
        spec = importlib.util.spec_from_file_location(
            "neven_http_server_" + name, SERVER_COPIES[name]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _loaded_servers[name] = module
    return _loaded_servers[name]


@pytest.fixture(params=_COPY_IDS, ids=_COPY_IDS)
def server(request):
    return _load_server(request.param)


def _write_config(tmp_path, neven_section, extra=None):
    """Write a temporary neven-config.json and return its path."""
    config = {"NEVEN": neven_section}
    if extra:
        config.update(extra)
    path = tmp_path / "neven-config.json"
    path.write_text(json.dumps(config, indent=4), encoding="utf-8")
    return str(path)


def _make_home(tmp_path, lang, name):
    """Create a directory that looks like a real installation of *lang*."""
    home = tmp_path / name
    marker = home.joinpath(*HOME_MARKERS[lang])
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("", encoding="ascii")
    return home


# ─────────────────────────────────────────────────────────────────────────────
# URLs oficiales — NEVEN informa y enlaza, nunca descarga ni instala
# ─────────────────────────────────────────────────────────────────────────────

def test_download_urls_are_the_official_https_pages(server):
    urls = server._ENGINE_DOWNLOAD_URLS
    assert set(urls) == {"r", "julia", "python"}
    for lang, url in urls.items():
        assert url == OFFICIAL_URLS[lang]
        assert url.startswith("https://")
        assert url.startswith(OFFICIAL_HOSTS[lang])


# ─────────────────────────────────────────────────────────────────────────────
# _detect_engine_installations
# ─────────────────────────────────────────────────────────────────────────────

def test_detect_reports_the_documented_keys_for_every_engine(server, tmp_path):
    result = server._detect_engine_installations(_write_config(tmp_path, {}))
    assert set(result) == {"r", "julia", "python"}
    for lang, info in result.items():
        assert set(info) == ENGINE_KEYS
        assert isinstance(info["enabled"], bool)
        assert isinstance(info["installed"], bool)
        assert isinstance(info["running"], bool)
        assert isinstance(info["home"], str)
        assert info["url"] == OFFICIAL_URLS[lang]


def test_disabled_engine_is_reported_as_not_enabled(server, tmp_path):
    home = _make_home(tmp_path, "r", "R-ok")
    config_path = _write_config(tmp_path, {
        "R": {"enabled": False, "home": str(home)},
    })
    result = server._detect_engine_installations(config_path)
    assert result["r"]["enabled"] is False
    # Desactivado no es lo mismo que ausente: la instalacion sigue ahi.
    assert result["r"]["installed"] is True


def test_enabled_engine_with_empty_home_is_not_installed(server, tmp_path):
    empty = tmp_path / "R-empty"
    empty.mkdir()
    config_path = _write_config(tmp_path, {
        "R": {"enabled": True, "home": str(empty)},
    })
    result = server._detect_engine_installations(config_path)
    assert result["r"]["enabled"] is True
    assert result["r"]["installed"] is False


@pytest.mark.parametrize("lang,section", [("r", "R"), ("julia", "Julia"), ("python", "Python")])
def test_home_with_the_expected_file_is_installed(server, tmp_path, lang, section):
    home = _make_home(tmp_path, lang, section + "-home")
    config_path = _write_config(tmp_path, {section: {"enabled": True, "home": str(home)}})
    result = server._detect_engine_installations(config_path)
    assert result[lang]["enabled"] is True
    assert result[lang]["installed"] is True
    assert result[lang]["home"] == str(home)


def test_engine_without_section_is_not_declared_and_does_not_crash(server, tmp_path):
    home = _make_home(tmp_path, "r", "R-only")
    config_path = _write_config(tmp_path, {"R": {"enabled": True, "home": str(home)}})
    result = server._detect_engine_installations(config_path)
    assert set(result) == {"r", "julia", "python"}
    # Un motor que no esta declarado en el config no esta habilitado.
    assert result["julia"]["enabled"] is False
    assert result["python"]["enabled"] is False
    # Y se sigue informando su enlace oficial.
    assert result["julia"]["url"] == OFFICIAL_URLS["julia"]


def test_missing_config_file_is_not_an_error(server, tmp_path):
    result = server._detect_engine_installations(str(tmp_path / "no-such-config.json"))
    assert set(result) == {"r", "julia", "python"}
    assert all(info["enabled"] is False for info in result.values())


def test_both_config_readers_tolerate_a_bom(server, tmp_path):
    # Los dos lectores del config leen con utf-8-sig: un BOM no puede dejar
    # el estado visible y el guardado fallando con 500.
    path = tmp_path / "neven-config.json"
    path.write_text(json.dumps({"NEVEN": {"R": {"enabled": True}}}, indent=4),
                    encoding="utf-8-sig")
    result = server._detect_engine_installations(str(path))
    assert result["r"]["enabled"] is True

    source = inspect.getsource(server.NEVENHandler._handle_engines_config)
    assert "utf-8-sig" in source


def test_malformed_config_file_is_not_an_error(server, tmp_path):
    broken = tmp_path / "neven-config.json"
    broken.write_text("{ esto no es JSON }", encoding="utf-8")
    result = server._detect_engine_installations(str(broken))
    assert all(info["enabled"] is False for info in result.values())


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints: /api/engines mantiene su forma booleana, /api/engines/config no
# ─────────────────────────────────────────────────────────────────────────────

def test_engines_endpoint_keeps_its_boolean_shape(server):
    status = server._get_engine_status()
    assert set(status) == {"r", "python", "julia"}
    assert all(isinstance(value, bool) for value in status.values())


def test_get_router_serves_the_engines_config_endpoint(server):
    assert hasattr(server.NEVENHandler, "_handle_engines_config_get")
    source = inspect.getsource(server.NEVENHandler.do_GET)
    assert "api/engines/config" in source
    assert "api/engines'" in source


# ─────────────────────────────────────────────────────────────────────────────
# Las tres copias no vuelven a divergir (G-TP-05)
# ─────────────────────────────────────────────────────────────────────────────

def test_the_three_copies_expose_the_same_engine_contract(tmp_path):
    modules = [_load_server(name) for name in _COPY_IDS]
    reference = modules[0]
    for module in modules[1:]:
        assert module._ENGINE_DOWNLOAD_URLS == reference._ENGINE_DOWNLOAD_URLS
        assert module._ENGINE_CONFIG_SECTIONS == reference._ENGINE_CONFIG_SECTIONS
        assert module._ENGINE_HOME_MARKERS == reference._ENGINE_HOME_MARKERS
        assert module._ENGINE_PATH_EXECUTABLES == reference._ENGINE_PATH_EXECUTABLES
        assert module._CONFIG_JSON_PATH == reference._CONFIG_JSON_PATH

    config_path = _write_config(tmp_path, {
        "R": {"enabled": True, "home": str(_make_home(tmp_path, "r", "R-shared"))},
        "Julia": {"enabled": False, "home": ""},
    })
    results = [module._detect_engine_installations(config_path) for module in modules]
    for result in results[1:]:
        assert set(result) == set(results[0])
        for lang in results[0]:
            assert set(result[lang]) == set(results[0][lang])
            assert result[lang]["url"] == results[0][lang]["url"]
            assert result[lang]["enabled"] == results[0][lang]["enabled"]
            assert result[lang]["installed"] == results[0][lang]["installed"]


# ─────────────────────────────────────────────────────────────────────────────
# start_studio.resolve_languages — arrancar solo lo que el usuario habilito
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def studio():
    spec = importlib.util.spec_from_file_location(
        "neven_start_studio", os.path.join(_SRC, "TaskPane", "start_studio.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_resolve_languages_cli_wins_over_the_config(studio):
    config = {
        "Standalone": {"languages": ["julia"]},
        "NEVEN": {"R": {"enabled": True}, "Julia": {"enabled": True}},
    }
    assert studio.resolve_languages(config, "r,python") == {"r", "python"}


def test_resolve_languages_standalone_wins_over_enabled(studio):
    config = {
        "Standalone": {"languages": ["julia"]},
        "NEVEN": {"R": {"enabled": True}, "Python": {"enabled": True}},
    }
    assert studio.resolve_languages(config, None) == {"julia"}


def test_resolve_languages_uses_the_enabled_engines(studio):
    config = {
        "NEVEN": {
            "R": {"enabled": True},
            "Julia": {"enabled": False},
            "Python": {},
        }
    }
    # Python declarado sin la clave enabled cuenta como habilitado,
    # igual que en language_service.cc.
    assert studio.resolve_languages(config, None) == {"r", "python"}


def test_resolve_languages_prefers_auto_start_engines(studio):
    config = {
        "preferences": {"auto_start_engines": ["julia"]},
        "NEVEN": {"R": {"enabled": True}, "Julia": {"enabled": True}},
    }
    assert studio.resolve_languages(config, None) == {"julia"}


def test_resolve_languages_without_any_enabled_engine_is_empty(studio):
    config = {
        "NEVEN": {
            "R": {"enabled": False},
            "Julia": {"enabled": False},
            "Python": {"enabled": False},
        }
    }
    assert studio.resolve_languages(config, None) == set()


def test_resolve_languages_without_neven_section_is_empty(studio):
    assert studio.resolve_languages({"Standalone": {"port": 5555}}, None) == set()


def test_resolve_languages_drops_unknown_names(studio):
    config = {"NEVEN": {"R": {"enabled": True}}}
    assert studio.resolve_languages(config, "r,cobol") == {"r"}
    assert studio.resolve_languages(config, "cobol") == set()
