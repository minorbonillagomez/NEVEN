# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Package Manager Service
# Verifica e instala paquetes para los motores R, Julia y Python.
#
# Principios:
#   - No bloquear: verificación en hilo de fondo
#   - No instalar sin permiso: Cola_de_Instalación requiere autorización
#   - Reutilizar: importa _get_python_exe de package_manager.py existente
#   - Una sola fuente de verdad: packages-manifest.json + packages-status-cache.json
# ═══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import json
import os
import sys
import threading
import time
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

# Reutilizar _get_python_exe del package_manager.py existente
_HERE = os.path.dirname(os.path.abspath(__file__))
_LIBRERIA_PYTHON = os.path.normpath(os.path.join(_HERE, "..", "..", "libreria", "PYTHON"))
if _LIBRERIA_PYTHON not in sys.path and os.path.isdir(_LIBRERIA_PYTHON):
    sys.path.insert(0, _LIBRERIA_PYTHON)

try:
    from package_manager import _get_python_exe  # type: ignore[import]
    _PYTHON_EXE_AVAILABLE = True
except ImportError:
    _PYTHON_EXE_AVAILABLE = False
    def _get_python_exe() -> str:  # type: ignore[misc]
        return "python.exe"

# Paquetes R predeterminados (generados desde análisis de wrappers .Studio.R)
_DEFAULT_R_PACKAGES = [
    "jsonlite", "plm", "stargazer", "e1071", "rpart", "VGAM",
    "tseries", "AER", "lmtest", "sandwich", "sampleSelection",
    "vars", "urca", "wooldridge", "FactoMineR", "forecast",
]
_DEFAULT_JULIA_PACKAGES = ["Statistics", "LinearAlgebra"]
_DEFAULT_PYTHON_PACKAGES = ["nltk", "PyPDF2", "python-docx"]

NEVEN_HOME = os.environ.get("NEVEN_HOME", os.environ.get("RJ2XCL_HOME", r"C:\NEVEN\\"))


class PackageManagerService:
    """Subsistema central de verificación e instalación de paquetes NEVEN."""

    MANIFEST_PATH      = os.path.join(NEVEN_HOME, "packages-manifest.json")
    CACHE_PATH         = os.path.join(NEVEN_HOME, "packages-status-cache.json")
    LOG_PATH           = os.path.join(NEVEN_HOME, "neven.log")
    TIMEOUT_STARTUP_S  = 30
    TIMEOUT_FUNCTION_S = 5
    CRAN_REPO          = "https://cloud.r-project.org"

    def __init__(self, get_pipe_client: Optional[Callable[[str], Any]] = None):
        self._get_pipe_client = get_pipe_client
        self._manifest: Dict = {}
        self._cache: Dict = {}
        self._install_queue: List[Dict] = []
        self._install_lock = threading.Lock()
        self._install_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._progress: Dict = {"status": "idle", "total": 0, "completados": 0,
                                "en_curso": None, "errores": [], "historial": []}
        self._progress_lock = threading.Lock()

    # ─── Ciclo de vida ───────────────────────────────────────────────────────

    def start(self) -> None:
        """Carga el manifiesto y lanza verificación en hilo de fondo."""
        self._manifest = self.load_manifest()
        t = threading.Thread(target=self._verificar_todos_bg,
                             daemon=True, name="pkg-mgr-verify")
        t.start()

    def stop(self) -> None:
        """Señaliza al hilo de instalación que termine."""
        self._stop_event.set()

    # ─── Manifiesto ──────────────────────────────────────────────────────────

    def load_manifest(self) -> Dict:
        """Carga packages-manifest.json o genera uno predeterminado."""
        if os.path.isfile(self.MANIFEST_PATH):
            try:
                with open(self.MANIFEST_PATH, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                valid = [p for p in raw.get("packages", [])
                         if all(k in p for k in ("nombre", "motor", "version_minima", "funciones"))]
                skipped = len(raw.get("packages", [])) - len(valid)
                if skipped:
                    self._log("WARNING", f"Manifiesto: {skipped} entradas invalidas omitidas")
                return {"packages": valid}
            except Exception as e:
                self._log("WARNING", f"No se pudo leer manifiesto: {e} — usando predeterminado")
        return self.generate_manifest()

    def generate_manifest(self) -> Dict:
        """Genera el manifiesto predeterminado desde los valores conocidos."""
        pkgs = []
        for nombre in _DEFAULT_R_PACKAGES:
            pkgs.append({"nombre": nombre, "motor": "R",
                         "version_minima": "0.0.0", "funciones": [],
                         "repo": self.CRAN_REPO})
        for nombre in _DEFAULT_JULIA_PACKAGES:
            pkgs.append({"nombre": nombre, "motor": "Julia",
                         "version_minima": "0.0.0", "funciones": [], "repo": None})
        for nombre in _DEFAULT_PYTHON_PACKAGES:
            pkgs.append({"nombre": nombre, "motor": "Python",
                         "version_minima": "0.0.0", "funciones": [], "repo": None})
        manifest = {"version": "1.0", "packages": pkgs,
                    "generated_at": datetime.now(timezone.utc).isoformat()}
        self.save_manifest(manifest)
        return manifest

    def save_manifest(self, manifest: Dict) -> None:
        try:
            with open(self.MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log("WARNING", f"No se pudo guardar manifiesto: {e}")

    def merge_sidecar_deps(self, sidecar: Dict) -> None:
        """Agrega al manifiesto las dependencias de un sidecar si no existen."""
        deps = sidecar.get("dependencies", {})
        fn_id = sidecar.get("id", "")
        changed = False
        for motor, paquetes in deps.items():
            for pkg in paquetes:
                existing = [p for p in self._manifest.get("packages", [])
                            if p["nombre"] == pkg and p["motor"] == motor]
                if not existing:
                    self._manifest.setdefault("packages", []).append(
                        {"nombre": pkg, "motor": motor, "version_minima": "0.0.0",
                         "funciones": [fn_id], "repo": self.CRAN_REPO if motor == "R" else None})
                    changed = True
                else:
                    if fn_id and fn_id not in existing[0].get("funciones", []):
                        existing[0].setdefault("funciones", []).append(fn_id)
                        changed = True
        if changed:
            self.save_manifest(self._manifest)

    # ─── Caché ───────────────────────────────────────────────────────────────

    def save_cache(self, status: List[Dict]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        motores = {}
        for item in status:
            if item.get("motor_disponible", False):
                motores[item["motor"]] = now
        cache = {"ultima_verificacion": motores, "estado": status}
        try:
            with open(self.CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            self._cache = cache
        except Exception as e:
            self._log("WARNING", f"No se pudo guardar cache: {e}")

    def load_cache(self) -> Dict:
        if os.path.isfile(self.CACHE_PATH):
            try:
                with open(self.CACHE_PATH, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                return self._cache
            except Exception:
                pass
        return {}

    # ─── Verificación ────────────────────────────────────────────────────────

    def _send_r(self, code: str, timeout_s: float = 10) -> str:
        """Envía código R por pipe y retorna el resultado como string."""
        if not self._get_pipe_client:
            return ""
        try:
            client = self._get_pipe_client("r")
            from pipe_client import variable_to_python  # type: ignore
            var = client.send_code([code], wait=True)
            result = variable_to_python(var)
            return str(result) if result is not None else ""
        except Exception:
            return ""

    def _send_julia(self, code: str, timeout_s: float = 10) -> str:
        """Envía código Julia por pipe y retorna resultado."""
        if not self._get_pipe_client:
            return ""
        try:
            client = self._get_pipe_client("julia")
            from pipe_client import variable_to_python  # type: ignore
            var = client.send_code([code], wait=True)
            result = variable_to_python(var)
            return str(result) if result is not None else ""
        except Exception:
            return ""

    def _verificar_r(self, paquete: str) -> Dict:
        """Verifica paquete R via subprocess Rscript (no usa pipe — compatible con Excel activo)."""
        import subprocess, shutil
        result = {"motor": "R", "motor_disponible": False, "paquete": paquete,
                  "instalado": False, "version_instalada": None,
                  "version_requerida": "0.0.0", "funciones_afectadas": []}
        try:
            rscript = shutil.which("Rscript") or "Rscript"
            code = (f"tryCatch({{cat('OK:', as.character(packageVersion('{paquete}')))}}, "
                    f"error=function(e) cat('MISSING'))")
            # NO usar --vanilla: deshabilita R_LIBS_USER y no encuentra paquetes de usuario
            proc = subprocess.run(
                [rscript, "--no-save", "--no-restore", "-e", code],
                capture_output=True, text=True, timeout=15,
                env={**os.environ}
            )
            result["motor_disponible"] = True
            out = (proc.stdout + proc.stderr).strip()
            if out.startswith("OK:"):
                result["instalado"] = True
                result["version_instalada"] = out.replace("OK:", "").strip().split()[0]
            else:
                result["instalado"] = False
        except Exception:
            pass
        return result

    def _verificar_julia(self, paquete: str) -> Dict:
        result = {"motor": "Julia", "motor_disponible": False, "paquete": paquete,
                  "instalado": False, "version_instalada": None,
                  "version_requerida": "0.0.0", "funciones_afectadas": []}
        try:
            code = f'Base.find_package("{paquete}") !== nothing ? "OK" : "MISSING"'
            out = self._send_julia(code, timeout_s=8)
            result["motor_disponible"] = True
            result["instalado"] = out.strip() == "OK"
        except Exception:
            pass
        return result

    def _verificar_python(self, paquete: str) -> Dict:
        result = {"motor": "Python", "motor_disponible": True, "paquete": paquete,
                  "instalado": False, "version_instalada": None,
                  "version_requerida": "0.0.0", "funciones_afectadas": []}
        try:
            exe = _get_python_exe()
            proc = subprocess.run([exe, "-m", "pip", "show", paquete],
                                  capture_output=True, text=True, timeout=15)
            if proc.returncode == 0:
                result["instalado"] = True
                for line in proc.stdout.splitlines():
                    if line.startswith("Version:"):
                        result["version_instalada"] = line.split(":", 1)[1].strip()
        except Exception:
            pass
        return result

    def _verificar_paquete(self, entry: Dict) -> Dict:
        motor = entry.get("motor", "")
        pkg   = entry.get("nombre", "")
        if motor == "R":
            r = self._verificar_r(pkg)
        elif motor == "Julia":
            r = self._verificar_julia(pkg)
        elif motor == "Python":
            r = self._verificar_python(pkg)
        else:
            return {}
        r["version_requerida"] = entry.get("version_minima", "0.0.0")
        r["funciones_afectadas"] = entry.get("funciones", [])
        return r

    def verificar_motor(self, motor: str) -> List[Dict]:
        """Verifica todos los paquetes de un motor específico."""
        pkgs = [p for p in self._manifest.get("packages", [])
                if p.get("motor", "").lower() == motor.lower()]
        results = []
        for p in pkgs:
            results.append(self._verificar_paquete(p))
        return results

    def verificar_todos(self, timeout_s: float = None) -> List[Dict]:
        """Verifica todos los paquetes de todos los motores."""
        timeout_s = timeout_s or self.TIMEOUT_STARTUP_S
        results = []
        start = time.monotonic()
        for p in self._manifest.get("packages", []):
            if time.monotonic() - start > timeout_s:
                self._log("WARNING", f"Verificacion de inicio interrumpida por timeout ({timeout_s}s)")
                break
            results.append(self._verificar_paquete(p))
        return results

    def verificar_funcion(self, function_id: str) -> List[Dict]:
        """Verifica solo los paquetes requeridos por una función específica."""
        pkgs = [p for p in self._manifest.get("packages", [])
                if function_id in p.get("funciones", []) or "ALL" in p.get("funciones", [])]
        results = []
        start = time.monotonic()
        for p in pkgs:
            if time.monotonic() - start > self.TIMEOUT_FUNCTION_S:
                break
            results.append(self._verificar_paquete(p))
        return results

    def _verificar_todos_bg(self) -> None:
        """Hilo de fondo: verifica al inicio y escribe caché."""
        try:
            results = self.verificar_todos(timeout_s=self.TIMEOUT_STARTUP_S)
            self.save_cache(results)
            faltantes = [r for r in results if not r.get("instalado")]
            n_ok = len(results) - len(faltantes)
            self._log("INFO", f"Verificacion inicio: {n_ok} OK, {len(faltantes)} faltantes")
        except Exception as e:
            self._log("WARNING", f"Error en verificacion de inicio: {e}")

    # ─── Instalación ─────────────────────────────────────────────────────────

    def encolar_instalacion(self, items: List[Dict]) -> None:
        """Encola paquetes para instalar. Nunca instala sin llamar este método."""
        with self._install_lock:
            self._install_queue.extend(items)
            total = len(self._install_queue)
        with self._progress_lock:
            self._progress = {"status": "pendiente", "total": total, "completados": 0,
                              "en_curso": None, "errores": [], "historial": []}
        if (self._install_thread is None or not self._install_thread.is_alive()):
            self._install_thread = threading.Thread(
                target=self._run_install_queue, daemon=True, name="pkg-install")
            self._install_thread.start()

    def _run_install_queue(self) -> None:
        """Thread: procesa la cola de instalación secuencialmente."""
        while not self._stop_event.is_set():
            with self._install_lock:
                if not self._install_queue:
                    break
                item = self._install_queue.pop(0)
            motor  = item.get("motor", "")
            nombre = item.get("nombre", "")
            with self._progress_lock:
                self._progress["status"] = "en_progreso"
                self._progress["en_curso"] = f"{nombre} ({motor})"
            self._log("INFO", f"Instalando {nombre} ({motor})")
            if motor == "R":
                res = self._instalar_r(nombre, item.get("repo", self.CRAN_REPO))
            elif motor == "Julia":
                res = self._instalar_julia(nombre)
            elif motor == "Python":
                res = self._instalar_python(nombre)
            else:
                res = {"ok": False, "error": f"Motor desconocido: {motor}"}
            with self._progress_lock:
                self._progress["completados"] += 1
                entry = {"paquete": nombre, "motor": motor,
                         "resultado": "ok" if res.get("ok") else "error",
                         "version": res.get("version", ""),
                         "error": res.get("error", "")}
                self._progress["historial"].append(entry)
                if not res.get("ok"):
                    self._progress["errores"].append(entry)
                    self._log("ERROR", f"Error instalando {nombre} ({motor}): {res.get('error')}")
                else:
                    self._log("INFO", f"Instalado {nombre} ({motor}) v{res.get('version','?')}")
        with self._progress_lock:
            self._progress["status"] = "completado"
            self._progress["en_curso"] = None

    def get_progress(self) -> Dict:
        with self._progress_lock:
            return dict(self._progress)

    def _instalar_r(self, paquete: str, repo: str) -> Dict:
        """Instala paquete R via subprocess Rscript — NO usa el pipe (que está ocupado por Excel)."""
        import subprocess, shutil
        # Buscar Rscript en rutas conocidas
        rscript_candidates = [
            r"C:\Program Files\R\R-4.6.1\bin\Rscript.exe",
            r"C:\Program Files\R\R-4.6.1\bin\x64\Rscript.exe",
            r"C:\Program Files\R\R-4.5.0\bin\Rscript.exe",
            r"C:\Program Files\R\R-4.5.0\bin\x64\Rscript.exe",
        ]
        # También buscar en el registro de Windows la versión activa
        try:
            import winreg
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for sub in (r"SOFTWARE\R-core\R", r"SOFTWARE\WOW6432Node\R-core\R"):
                    try:
                        with winreg.OpenKey(hive, sub) as k:
                            val, _ = winreg.QueryValueEx(k, "InstallPath")
                            if val:
                                rscript_candidates.insert(0, os.path.join(str(val), "bin", "Rscript.exe"))
                    except OSError:
                        pass
        except ImportError:
            pass

        rscript = next((p for p in rscript_candidates if os.path.isfile(p)), None)
        if not rscript:
            rscript = shutil.which("Rscript") or "Rscript"

        r_code = (
            f"lib_path <- Sys.getenv('R_LIBS_USER', unset=file.path(Sys.getenv('USERPROFILE','~'), 'R', 'win-library', R.version$major));"
            f"if (!dir.exists(lib_path)) dir.create(lib_path, recursive=TRUE);"
            f"install.packages('{paquete}', repos='{repo}', dependencies=TRUE, quiet=FALSE, lib=lib_path);"
            f"cat('VERSION:', as.character(tryCatch(packageVersion('{paquete}'), error=function(e)'?')))"
        )
        try:
            proc = subprocess.run(
                [rscript, "--no-save", "--no-restore", "-e", r_code],
                capture_output=True, text=True, timeout=300,
                env={**os.environ}
            )
            output = (proc.stdout + proc.stderr).strip()
            if proc.returncode == 0 and "error" not in output.lower()[:100]:
                version = ""
                for line in output.splitlines():
                    if line.startswith("VERSION:"):
                        version = line.replace("VERSION:", "").strip()
                return {"ok": True, "version": version}
            # Buscar mensaje de error real
            err_lines = [l for l in output.splitlines() if "error" in l.lower() or "Error" in l]
            err = err_lines[-1] if err_lines else output[-300:]
            return {"ok": False, "error": err}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Timeout durante instalacion (>5 min)"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _instalar_julia(self, paquete: str) -> Dict:
        code = f'import Pkg; Pkg.add("{paquete}"); println("OK:", string(pkgversion(Base.PkgId("{paquete}"))))'
        out = self._send_julia(code, timeout_s=300)
        if "OK:" in out:
            return {"ok": True, "version": out.split("OK:", 1)[-1].strip()}
        return {"ok": False, "error": out}

    def _instalar_python(self, paquete: str) -> Dict:
        exe = _get_python_exe()
        try:
            proc = subprocess.run([exe, "-m", "pip", "install", paquete, "--quiet"],
                                  capture_output=True, text=True, timeout=300)
            if proc.returncode == 0:
                ver_proc = subprocess.run([exe, "-m", "pip", "show", paquete],
                                          capture_output=True, text=True, timeout=15)
                version = ""
                for line in ver_proc.stdout.splitlines():
                    if line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
                return {"ok": True, "version": version}
            return {"ok": False, "error": proc.stderr.strip()[-300:]}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Timeout durante instalación"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ─── Logging ─────────────────────────────────────────────────────────────

    def _log(self, level: str, message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        line = f"[{ts}] [{level}]  [PKG] {message}\n"
        try:
            with open(self.LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass


# Instancia global (inicializada por neven_http_server.py)
_pkg_service: Optional[PackageManagerService] = None
_PKG_SERVICE_AVAILABLE = False


def init_pkg_service(get_pipe_client: Callable[[str], Any]) -> PackageManagerService:
    """Inicializa el servicio global. Llamar desde neven_http_server.start_server()."""
    global _pkg_service, _PKG_SERVICE_AVAILABLE
    _pkg_service = PackageManagerService(get_pipe_client=get_pipe_client)
    _pkg_service.start()
    _PKG_SERVICE_AVAILABLE = True
    return _pkg_service
