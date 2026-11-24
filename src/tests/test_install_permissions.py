"""Contrato de ``Set-InstallPermissions.ps1`` sobre una instalacion medida.

El directorio de instalacion hereda de la raiz del disco el ACE
``Authenticated Users:(OI)(CI)(IO)(M)``, de modo que cualquier usuario autenticado
de la maquina puede sustituir un fichero que NEVEN ejecuta por su cuenta
(``startup\\*.py``, ``functions\\*.R``, ``TaskPane\\*``, los ejecutables de los
motores). Lo que se comprueba aqui no es el texto del script, sino la DACL real
que queda en el disco: se construye un arbol con la forma de una instalacion, se
le concede la misma herencia permisiva y se mide antes y despues de endurecer
(``INV-INS-05``).

Tres direcciones, que son las que exige la verificacion de la tarea:

1. El auditor falla y nombra lo que NEVEN ejecuta cuando esta escribible.
2. Tras endurecer no queda nada escribible por usuarios sin privilegios, y los
   directorios de datos siguen escribiendose sin elevar.
3. Una operacion de permisos que falla se reporta con su codigo, en vez de pasar
   inadvertida.
4. En un destino protegido, donde los usuarios no podian escribir antes de
   instalar, la clase datos no les concede nada: el script solo restringe.

No hace falta elevacion: el usuario es dueno del arbol que crea en TEMP, asi que
puede cambiar su DACL. Tampoco hace falta R, Julia ni Python (``INV-TEST-03``).
El test se salta si no hay ``powershell.exe`` en el PATH.
"""

import json
import os
import shutil
import subprocess

import pytest

_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPT = os.path.join(_SRC, "Install", "Set-InstallPermissions.ps1")
_POWERSHELL = shutil.which("powershell.exe")

# Ficheros de la clase codigo: NEVEN los ejecuta o los carga sin que el usuario
# los invoque.
_CODE_FILES = (
    "NEVEN64.xll",
    os.path.join("startup", "neven_http_server.py"),
    os.path.join("TaskPane", "datalab.js"),
    os.path.join("ControlR.exe"),
)

# Clase datos: NEVEN las escribe desde la sesion del usuario, sin elevar.
_DATA_DIRS = ("functions", "logs", "webview2-data")


def _run(*arguments):
    """Corre el script y devuelve (returncode, stdout + stderr)."""
    proc = subprocess.run(
        [_POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", _SCRIPT] + list(arguments),
        capture_output=True,
        text=True,
        timeout=600,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _audit(install_dir):
    """Audita y devuelve (returncode, informe deserializado)."""
    code, output = _run("-InstallDir", install_dir, "-AuditOnly", "-Json")
    return code, json.loads(output)


def _findings(report, finding_class):
    return [f for f in report["Findings"] if f["Class"] == finding_class]


def _is_writable_by_authenticated_users(path):
    """Mide con Get-Acl si S-1-5-11 tiene Modify sobre una ruta."""
    command = (
        "$acl = Get-Acl -LiteralPath '{0}'; "
        "$m = [System.Security.AccessControl.FileSystemRights]::Modify; "
        "$hit = $acl.Access | Where-Object {{ "
        "$_.AccessControlType -eq 'Allow' -and "
        "$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value -eq 'S-1-5-11' -and "
        "([int]$_.FileSystemRights -band [int]$m) -eq [int]$m }}; "
        "if ($hit) {{ 'yes' }} else {{ 'no' }}"
    ).format(path.replace("'", "''"))
    proc = subprocess.run(
        [_POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.stdout.strip() == "yes"


def _icacls(*arguments):
    subprocess.run(
        ["icacls.exe"] + list(arguments),
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )


def _current_user_sid():
    proc = subprocess.run(
        [
            _POWERSHELL, "-NoProfile", "-Command",
            "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.stdout.strip()


def _make_tree(root, grant_authenticated_users=True):
    """Construye un arbol con la forma de una instalacion y la herencia de C:\\."""
    for relative in ("startup", "TaskPane", "functions", "certs", "libreria"):
        os.makedirs(os.path.join(root, relative), exist_ok=True)
    for relative in _CODE_FILES:
        with open(os.path.join(root, relative), "w", encoding="utf-8") as handle:
            handle.write("placeholder\n")
    with open(os.path.join(root, "neven-config.json"), "w", encoding="utf-8") as handle:
        handle.write("{}")
    if grant_authenticated_users:
        # La misma concesion que un directorio bajo C:\ recibe por herencia.
        _icacls(root, "/grant", "*S-1-5-11:(OI)(CI)(M)")


@pytest.fixture(scope="module")
def hardened(tmp_path_factory):
    """Mide el arbol antes y despues de aplicar el endurecimiento."""
    if _POWERSHELL is None:
        pytest.skip("powershell.exe no esta disponible")

    root = str(tmp_path_factory.mktemp("install_permissions"))
    _make_tree(root)

    before_code, before = _audit(root)
    apply_code, apply_output = _run("-InstallDir", root)
    after_code, after = _audit(root)

    return {
        "root": root,
        "before": before,
        "before_code": before_code,
        "apply_code": apply_code,
        "apply_output": apply_output,
        "after": after,
        "after_code": after_code,
    }


def test_the_audit_fails_while_neven_code_is_writable(hardened):
    # Codigo 1: hay hallazgos de ACL y ninguna operacion fallo.
    assert hardened["before_code"] == 1, hardened["before"]
    writable = _findings(hardened["before"], "WritableByNonPrivileged")
    assert writable, hardened["before"]


def test_the_audit_names_the_files_neven_executes(hardened):
    paths = {f["Path"].lower() for f in _findings(hardened["before"], "WritableByNonPrivileged")}
    for relative in ("startup\\neven_http_server.py", "neven64.xll", "taskpane\\datalab.js"):
        assert any(path.endswith(relative) for path in paths), (relative, sorted(paths))


def test_nothing_neven_executes_stays_writable_after_hardening(hardened):
    assert _findings(hardened["after"], "WritableByNonPrivileged") == [], hardened["after"]
    for relative in _CODE_FILES:
        path = os.path.join(hardened["root"], relative)
        assert not _is_writable_by_authenticated_users(path), relative


def test_the_data_directories_stay_writable_without_elevation(hardened):
    # El servidor HTTP, el FileWatchService y los logs escriben aqui sin elevar:
    # endurecer no puede quitarles la escritura.
    for relative in _DATA_DIRS:
        path = os.path.join(hardened["root"], relative)
        assert os.path.isdir(path), relative
        assert _is_writable_by_authenticated_users(path), relative


def test_a_failed_permission_operation_is_reported_with_its_exit_code(tmp_path):
    if _POWERSHELL is None:
        pytest.skip("powershell.exe no esta disponible")

    # Un destino que no existe: icacls falla y el script lo tiene que decir.
    missing = str(tmp_path / "no-existe" / "nada")
    code, output = _run("-InstallDir", missing, "-Json")
    report = json.loads(output)

    assert code == 2, report
    failures = _findings(report, "OperationFailed")
    assert failures, report
    assert any("icacls" in f["Detail"] for f in failures), failures
    # El codigo de salida de la operacion queda registrado, no solo el hallazgo.
    assert [op for op in report["Operations"] if not op["Ok"] and op["ExitCode"] != 0], report


def test_the_probe_measures_without_leaving_anything_behind(tmp_path):
    if _POWERSHELL is None:
        pytest.skip("powershell.exe no esta disponible")

    root = str(tmp_path / "probe-target")
    os.makedirs(root)
    _make_tree(root)

    code, output = _run("-InstallDir", root, "-Probe", "-Json")
    report = json.loads(output)

    assert code == 0, report
    assert not os.path.exists(os.path.join(root, ".neven-acl-probe")), report
    # El sondeo no toca el resto del arbol: mide y se retira.
    assert os.path.isfile(os.path.join(root, "NEVEN64.xll"))


@pytest.fixture(scope="module")
def protected(tmp_path_factory):
    """Instala en un destino que no concedia escritura a los usuarios.

    Es la forma de ``C:\\Program Files``, donde la herencia solo da lectura y
    ejecucion a los usuarios: ahi la clase datos no puede conceder escritura sin
    crear el mismo vector de escalada que el script cierra.
    """
    if _POWERSHELL is None:
        pytest.skip("powershell.exe no esta disponible")

    parent = str(tmp_path_factory.mktemp("protected_parent"))
    # Se corta la herencia del padre y se deja solo a los administradores y al
    # usuario que corre el test, que es el dueno y puede cambiar la DACL sin elevar.
    _icacls(
        parent, "/inheritance:r",
        "/grant", "*S-1-5-32-544:(OI)(CI)(F)",
        "/grant", "*{0}:(OI)(CI)(F)".format(_current_user_sid()),
    )

    root = os.path.join(parent, "NEVEN")
    os.makedirs(root)
    _make_tree(root, grant_authenticated_users=False)

    code, output = _run("-InstallDir", root, "-Json")
    return {"root": root, "code": code, "report": json.loads(output)}


def test_a_protected_destination_gets_no_new_write_grant(protected):
    # Ninguna concesion de la clase datos: el destino no la tenia.
    granted = [entry for entry in protected["report"]["DataClass"] if entry["Granted"]]
    assert granted == [], granted
    # Lo unico que se concede a los usuarios es leer y ejecutar. Ni (M), ni
    # (RX,W), ni el (AD) que deja crear subdirectorios en la raiz.
    write_grants = ("S-1-5-11:(OI)(CI)(M)", "S-1-5-11:(OI)(CI)(RX,W)", "S-1-5-11:(RX,W)", "S-1-5-11:(AD)")
    assert not [
        op for op in protected["report"]["Operations"]
        if any(grant in op["Args"] for grant in write_grants)
    ], protected["report"]["Operations"]


def test_a_protected_destination_keeps_the_data_paths_read_only(protected):
    for relative in _DATA_DIRS:
        path = os.path.join(protected["root"], relative)
        assert os.path.isdir(path), relative
        assert not _is_writable_by_authenticated_users(path), relative
    config = os.path.join(protected["root"], "neven-config.json")
    assert not _is_writable_by_authenticated_users(config)


def test_a_protected_destination_says_what_quedar_en_solo_lectura_implies(protected):
    # La politica del producto: lo que no se pudo dejar escribible se dice con su
    # motivo y su consecuencia, no se oculta.
    residual = " ".join(protected["report"]["Residual"]).lower()
    assert "solo lectura" in residual, residual
    assert "elevada" in residual, residual
    assert "functions" in residual, residual


def test_the_report_is_parseable_json_and_names_the_residual_exposure(hardened):
    report = hardened["after"]
    assert report["Mode"] == "auditoria"
    assert report["Checked"] > 0
    # La politica del producto: lo que sigue expuesto se dice, no se oculta.
    residual = " ".join(report["Residual"]).lower()
    assert "functions" in residual
    assert "neven-config.json" in residual
