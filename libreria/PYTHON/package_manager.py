# ─── NEVEN: Gestor de Paquetes Python ─────────────────────────────────────────
# Permite instalar, verificar y listar paquetes Python desde Excel.
#
# Uso en Excel:
#   =P.instalar("scikit-learn")           → Instala el paquete
#   =P.instalar("numpy pandas matplotlib") → Instala varios (separados por espacio)
#   =P.paquetes()                         → Lista paquetes instalados
#   =P.verificar("scikit-learn")          → Verifica si esta instalado

import subprocess
import sys
import os


def _get_python_exe():
    """Obtiene la ruta del ejecutable python.exe."""
    # Method 1: Find python.exe next to python3.dll (which is always loaded)
    import ctypes.util
    import ctypes
    try:
        # python3.dll is loaded - find its directory
        h = ctypes.windll.kernel32.GetModuleHandleA(b"python3.dll")
        if h:
            buf = ctypes.create_string_buffer(260)
            ctypes.windll.kernel32.GetModuleFileNameA(h, buf, 260)
            dll_path = buf.value.decode()
            python_dir = os.path.dirname(dll_path)
            candidate = os.path.join(python_dir, "python.exe")
            if os.path.isfile(candidate):
                return candidate
    except Exception:
        pass

    # Method 2: Search PATH (skip WindowsApps)
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path_dir, "python.exe")
        if os.path.isfile(candidate) and "WindowsApps" not in candidate:
            return candidate

    return "python.exe"  # fallback


def _ensure_pip():
    """Ensures pip is available. Installs it via ensurepip if missing."""
    python_exe = _get_python_exe()
    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            # pip not found — install it
            subprocess.run(
                [python_exe, "-m", "ensurepip", "--upgrade"],
                capture_output=True, timeout=60
            )
    except Exception:
        pass


# Auto-install pip on first load if missing
_ensure_pip()


def instalar(paquetes):
    """Instala uno o mas paquetes Python usando pip.
    
    Puede recibir un solo nombre o varios separados por espacios.
    Ejemplo: instalar("scikit-learn numpy pandas")
    """
    lista = paquetes.strip().split()
    resultados = []
    python_exe = _get_python_exe()

    for paquete in lista:
        try:
            result = subprocess.run(
                [python_exe, "-m", "pip", "install", paquete, "--quiet"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                resultados.append(f"[OK] {paquete} instalado correctamente")
            else:
                error_msg = result.stderr.strip().split('\n')[-1] if result.stderr else "Error desconocido"
                resultados.append(f"[ERROR] {paquete}: {error_msg}")
        except subprocess.TimeoutExpired:
            resultados.append(f"[ERROR] {paquete}: timeout (>120s)")
        except Exception as e:
            resultados.append(f"[ERROR] {paquete}: {str(e)}")

    if len(resultados) == 1:
        return resultados[0]
    return resultados


def verificar(paquete):
    """Verifica si un paquete Python esta instalado y retorna su version."""
    python_exe = _get_python_exe()
    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "show", paquete],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    return f"{paquete} v{version} [instalado]"
            return f"{paquete} [instalado]"
        return f"{paquete} [NO instalado]"
    except Exception as e:
        return f"Error verificando {paquete}: {str(e)}"


def paquetes():
    """Lista todos los paquetes Python instalados con sus versiones."""
    python_exe = _get_python_exe()
    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "list", "--format=columns"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Retornar como vector de strings (compatible con Excel)
            output = ["Paquete | Version"]
            for line in lines[2:]:  # Skip header lines (Package/-------)
                parts = line.split()
                if len(parts) >= 2:
                    output.append(f"{parts[0]} | {parts[1]}")
            return output
        if "No module named pip" in result.stderr:
            return "pip no esta instalado. Ejecute en CMD: python -m ensurepip --upgrade"
        return f"Error: {result.stderr.strip().split(chr(10))[-1]}"
    except Exception as e:
        return f"Error: {str(e)}"


# ─── Registro ─────────────────────────────────────────────────────────────────

register_function("instalar",
    "Instala paquetes Python (pip install). Varios separados por espacio.",
    "Utilidades",
    [{"name": "paquetes", "description": "Nombre(s) del paquete a instalar (ej: 'scikit-learn numpy')"}])

register_function("verificar",
    "Verifica si un paquete Python esta instalado y su version.",
    "Utilidades",
    [{"name": "paquete", "description": "Nombre del paquete a verificar"}])

register_function("paquetes",
    "Lista todos los paquetes Python instalados con sus versiones.",
    "Utilidades",
    [])
