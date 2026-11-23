"""Contrato de ``Install-NEVEN.ps1 -ConfigureOnly`` sobre neven-config.json.

El modo ``-ConfigureOnly`` es la via para cambiar los motores sin reinstalar
(docs/MOTORES_OPCIONALES.md) y hasta ahora solo se comprobaba a mano. Lo que se
afirma aqui no depende de que R, Julia o Python esten en el equipo
(``INV-TEST-03``): son invariantes del fichero que el instalador deja escrito,
y valen igual con los tres motores, con alguno o con ninguno.

El test se salta si no hay ``powershell.exe`` en el PATH.
"""

import json
import os
import shutil
import subprocess

import pytest

_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_INSTALLER = os.path.join(_SRC, "Install", "Install-NEVEN.ps1")
_TEMPLATE = os.path.join(_SRC, "Install", "neven-config.template.json")
_POWERSHELL = shutil.which("powershell.exe")

# Nombre de la seccion en neven-config.json y su identificador en
# preferences.auto_start_engines.
_ENGINES = (("R", "r"), ("Julia", "julia"), ("Python", "python"))


@pytest.fixture(scope="module")
def configured(tmp_path_factory):
    """Corre -ConfigureOnly sobre una copia de la plantilla y devuelve el resultado."""
    if _POWERSHELL is None:
        pytest.skip("powershell.exe no esta disponible")

    work = tmp_path_factory.mktemp("configure_only")
    config_path = work / "neven-config.json"
    manual_home = work / "manual-engine-home"
    manual_home.mkdir()
    gone_home = work / "directorio-borrado"

    with open(_TEMPLATE, encoding="utf-8") as handle:
        config = json.load(handle)
    # Julia: home escrito a mano que existe. Python: home cuyo directorio ya no
    # existe. preferences: una lista vieja que el instalador tiene que refrescar.
    config["NEVEN"]["Julia"]["home"] = str(manual_home)
    config["NEVEN"]["Python"]["home"] = str(gone_home)
    config["preferences"] = {"auto_start_engines": ["julia"]}
    config_path.write_text(json.dumps(config, indent=4), encoding="utf-8")

    proc = subprocess.run(
        [
            _POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", _INSTALLER,
            "-ConfigureOnly", "-Silent", "-InstallDir", str(work),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    raw = config_path.read_bytes()
    return {
        "raw": raw,
        "config": json.loads(raw.decode("utf-8")),
        "manual_home": str(manual_home),
        "gone_home": str(gone_home),
    }


def test_the_config_stays_utf8_without_bom(configured):
    # INV-INS-04: json11 (C++) no tolera el BOM.
    assert not configured["raw"].startswith(b"\xef\xbb\xbf")


def test_every_engine_declares_a_boolean_enabled(configured):
    neven = configured["config"]["NEVEN"]
    for section, _ in _ENGINES:
        assert isinstance(neven[section]["enabled"], bool), section


def test_home_is_either_empty_or_an_existing_directory(configured):
    # Un home que no existe se ignora en DiscoveryService, pero deja al usuario
    # creyendo que apunta a algo: el instalador no debe dejar ninguno asi.
    neven = configured["config"]["NEVEN"]
    for section, _ in _ENGINES:
        home = neven[section].get("home", "")
        assert home == "" or os.path.isdir(home), f"{section}: {home!r}"


def test_a_home_whose_directory_disappeared_is_not_kept(configured):
    home = configured["config"]["NEVEN"]["Python"].get("home", "")
    assert home != configured["gone_home"]


def test_a_manual_home_is_not_silently_lost(configured):
    # Si la deteccion encuentra Julia, home pasa a ser esa instalacion; si no,
    # se conserva el valor escrito a mano. Lo que no puede pasar es quedarse
    # vacio teniendo un directorio valido.
    home = configured["config"]["NEVEN"]["Julia"].get("home", "")
    assert home != "" and os.path.isdir(home)


def test_auto_start_engines_is_derived_from_enabled(configured):
    # El instalador refresca la lista que usa start_studio.resolve_languages,
    # asi que no puede quedar la que habia antes (["julia"]).
    config = configured["config"]
    neven = config["NEVEN"]
    expected = {
        lang for section, lang in _ENGINES if neven[section].get("enabled", True) is not False
    }
    auto_start = config["preferences"]["auto_start_engines"]
    assert isinstance(auto_start, list)
    assert set(auto_start) == expected
