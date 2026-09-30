# Diseño — NEVEN Package Manager

## Overview

El NEVEN Package Manager es un subsistema de verificación e instalación de paquetes que actúa
de forma proactiva sobre los tres motores de scripting de NEVEN: R (ControlR.exe), Julia
(ControlJulia.exe) y Python (ControlPython.exe).

El problema central es la *rotura silenciosa por actualización de motor*: cuando el usuario
instala R 4.6.x sobre R 4.4.1, los paquetes de la biblioteca anterior no migran automáticamente.
El motor arranca sin errores pero las funciones del catálogo DataLab fallan con mensajes del
tipo `"no hay paquete llamado 'plm'"`. El Package Manager detecta ese estado antes de que el
usuario intente ejecutar una función.

### Principios de diseño

1. **No bloquear, advertir.** Ninguna verificación retrasa la carga del add-in ni la UI.
2. **No instalar sin permiso.** La instalación requiere autorización explícita del usuario.
3. **Reutilizar, no duplicar.** Se extiende `package_manager.py` existente; no se reimplementa
   la lógica de detección del ejecutable Python. Los pipes de ControlR y ControlJulia se
   reutilizan para verificar e instalar en el proceso correcto.
4. **Una sola fuente de verdad.** El manifiesto `packages-manifest.json` es el origen canónico
   de qué se necesita. El caché `packages-status-cache.json` es el origen canónico del estado.
5. **Degradación elegante.** Si un motor no está disponible, el endpoint retorna
   `motor_disponible: false` en lugar de un HTTP 5xx.

---

## Architecture

### Diagrama de componentes

```
NEVEN Studio (puerto 5555) — neven_http_server.py
  ├── GET  /api/packages/status            ──┐
  ├── GET  /api/packages/status/{motor}    ──┤
  ├── POST /api/packages/install           ──┤── PackageManagerService
  ├── GET  /api/packages/progress          ──┤     (package_manager_service.py)
  └── GET  /api/packages/function/{id}     ──┘
                                                ├── Python: package_manager.py
                                                │   (_get_python_exe, pip show/install)
                                                ├── R: send_code(pipe_client("r"))
                                                │   requireNamespace / install.packages
                                                └── Julia: send_code(pipe_client("julia"))
                                                    Base.find_package / Pkg.add
```

### Flujo de inicio

```
NEVEN arranca → start_studio.py conecta pipes → neven_http_server.start_server()
    └── PackageManagerService.start()
            ├── Carga o genera packages-manifest.json
            └── Thread daemon: verificar_todos()
                    ├── R:      send_code("requireNamespace('X')")
                    ├── Julia:  send_code("Base.find_package('X')")
                    ├── Python: pip show X (via _get_python_exe())
                    └── Escribe packages-status-cache.json
                        Si faltantes → notificación en UI
```

### Flujo de instalación

```
Usuario hace clic "Instalar" → POST /api/packages/install
    └── PackageManagerService.encolar_instalacion(lista)
            └── Thread de instalación (uno por vez)
                    ├── R:      send_code("install.packages('X', dependencies=TRUE)")
                    ├── Julia:  send_code("import Pkg; Pkg.add('X')")
                    ├── Python: subprocess pip install X (via _get_python_exe())
                    └── Actualiza manifest.json + status-cache.json

UI → GET /api/packages/progress (polling cada 2s) ← resultado de la cola
```

---

## Components and Interfaces

### `package_manager_service.py` (nuevo)

**Ubicación:** `ControlPython/startup/package_manager_service.py`

Este módulo **no reemplaza** `libreria/PYTHON/package_manager.py`. Lo importa para la lógica
de detección del ejecutable Python (`_get_python_exe`) y delega en él las operaciones pip.

```python
class PackageManagerService:
    """Subsistema central de verificación e instalación de paquetes."""

    MANIFEST_PATH      = r"C:\NEVEN\packages-manifest.json"
    CACHE_PATH         = r"C:\NEVEN\packages-status-cache.json"
    LOG_PATH           = r"C:\NEVEN\neven.log"
    TIMEOUT_STARTUP_S  = 30   # Req 2.5
    TIMEOUT_FUNCTION_S = 5    # Req 3.4
    POLL_INTERVAL_S    = 2    # Req 9.6

    def __init__(self, get_pipe_client: Callable[[str], Any]): ...
    def start(self) -> None: ...         # Carga manifiesto + lanza thread de verificación
    def stop(self) -> None: ...          # Señaliza al hilo de instalación que termine

    # Manifiesto
    def load_manifest(self) -> dict: ...
    def generate_manifest(self) -> dict: ...
    def save_manifest(self, manifest: dict) -> None: ...
    def merge_sidecar_deps(self, sidecar: dict) -> None: ...

    # Verificación
    def verificar_todos(self, timeout_s: float = ...) -> dict: ...
    def verificar_funcion(self, function_id: str) -> list[dict]: ...
    def verificar_motor(self, motor: str) -> list[dict]: ...
    def _verificar_r(self, paquete: str) -> dict: ...      # requireNamespace() via pipe
    def _verificar_julia(self, paquete: str) -> dict: ...  # Base.find_package() via pipe
    def _verificar_python(self, paquete: str) -> dict: ... # pip show via _get_python_exe()

    # Instalación
    def encolar_instalacion(self, items: list[dict]) -> None: ...
    def get_progress(self) -> dict: ...
    def _instalar_r(self, paquete: str, repo: str) -> dict: ...
    def _instalar_julia(self, paquete: str) -> dict: ...
    def _instalar_python(self, paquete: str) -> dict: ...

    # Persistencia y logging
    def save_cache(self, status: dict) -> None: ...
    def load_cache(self) -> dict: ...
    def _log(self, level: str, message: str) -> None: ...
```

### Extensiones a `neven_http_server.py`

Se agregan cinco rutas al bloque `do_GET` y una al bloque `do_POST`. El servicio se instancia
como variable global `_pkg_service` con el mismo `get_pipe_client` de `_datalab_handler`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/packages/status` | Estado de todos los paquetes (lee caché) |
| GET | `/api/packages/status/{motor}` | Estado de un motor específico |
| POST | `/api/packages/install` | Inicia Cola_de_Instalación |
| GET | `/api/packages/progress` | Estado actual de la cola (polling) |
| GET | `/api/packages/function/{id}` | Estado de paquetes de una función |

### Hook en `datalab_handler.py`

Se inserta en `handle_run()` **después** de resolver `function_id` y **antes** de ejecutar:

```python
if _PKG_SERVICE_AVAILABLE:
    pkg_check = _pkg_service.verificar_funcion(function_id)
    faltantes = [p for p in pkg_check if not p["instalado"]]
    if faltantes:
        advertencia_slot = {
            "name":  "advertencia_paquetes",
            "label": "⚠️ Paquetes faltantes",
            "type":  "scalar",
            "value": "Faltan: " + ", ".join(p["nombre"] for p in faltantes),
            "tier":  1,
        }
        # Se inyecta al inicio de la lista de slots — la ejecución NO se bloquea
```

**Decisión de diseño:** el hook nunca bloquea. Retorna el slot de advertencia y deja que la
función R/Julia/Python se ejecute normalmente. El usuario puede instalar los paquetes faltantes
sin reiniciar el flujo.

### Cambios en `taskpane.html`

**Advertencia de paquetes** (entre `#dl-selector-card` y `#dl-column-panel`):

```html
<div id="dl-pkg-warning" class="msg-warn" style="display:none">
  <span id="dl-pkg-warning-msg"></span>
  <button class="btn btn-secondary" id="dl-pkg-install-btn" style="margin-left:8px">
    Instalar paquetes faltantes
  </button>
</div>
```

**Botón de verificación manual** (al final de `#dl-selector-card`):

```html
<div style="margin-top:8px;display:flex;justify-content:flex-end">
  <button class="btn btn-secondary" id="dl-pkg-check-btn">🔍 Verificar paquetes</button>
</div>
```

El botón llama a `GET /api/packages/status` y muestra el reporte reutilizando
`renderSlotTable` de `datalab.js`.

---

## Data Models

### `packages-manifest.json`

```json
{
  "version": "1.0",
  "generated_at": "2026-08-01T10:00:00",
  "packages": [
    {
      "nombre": "plm",
      "motor": "R",
      "version_minima": "2.6.0",
      "funciones": ["RG_Efectos_Fijos"],
      "repo": "https://cloud.r-project.org"
    },
    {
      "nombre": "DataFrames",
      "motor": "Julia",
      "version_minima": "1.5.0",
      "funciones": ["J_AD_Descriptiva"],
      "repo": null
    },
    {
      "nombre": "scikit-learn",
      "motor": "Python",
      "version_minima": "1.0.0",
      "funciones": ["PY_Clustering"],
      "repo": null
    }
  ]
}
```

**Campos del objeto paquete:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre` | string | Nombre canónico del paquete en el gestor nativo |
| `motor` | `"R"` \| `"Julia"` \| `"Python"` | Motor al que pertenece |
| `version_minima` | string | Versión mínima aceptable (semver) |
| `funciones` | string[] | IDs de funciones DataLab que dependen del paquete |
| `repo` | string \| null | Repositorio CRAN para R; null usa el default del motor |

### `packages-status-cache.json`

```json
{
  "ultima_verificacion": {
    "R":      "2026-08-01T10:05:30",
    "Julia":  "2026-08-01T10:05:45",
    "Python": "2026-08-01T10:05:15"
  },
  "estado": [
    {
      "motor": "R",
      "motor_disponible": true,
      "paquete": "plm",
      "instalado": false,
      "version_instalada": null,
      "version_requerida": "2.6.0",
      "funciones_afectadas": ["RG_Efectos_Fijos"]
    }
  ]
}
```

### Extensión a sidecars JSON del catálogo DataLab

Se agrega el campo opcional `dependencies` a cada sidecar. Si no existe, el sidecar es
compatible hacia atrás:

```json
{
  "id": "RG_Efectos_Fijos",
  "family": "REGRESION",
  "name": "Efectos fijos",
  "dependencies": {
    "R": ["plm", "lmtest"],
    "Python": [],
    "Julia": []
  }
}
```

### Respuesta de `GET /api/packages/status`

```json
{
  "status": "ok",
  "fuente": "cache",
  "timestamp_cache": "2026-08-01T10:05:30",
  "paquetes": [
    {
      "motor": "R",
      "motor_disponible": true,
      "paquete": "plm",
      "instalado": false,
      "version_instalada": null,
      "version_requerida": "2.6.0",
      "funciones_afectadas": ["RG_Efectos_Fijos"]
    }
  ]
}
```

### Respuesta de `POST /api/packages/install`

Request: `{"paquetes": [{"motor":"R","nombre":"plm"}, {"motor":"Python","nombre":"sklearn"}]}`

Response: `{"status":"ok","encolados":2,"cola_id":"install-2026-08-01T10:10:00"}`

### Respuesta de `GET /api/packages/progress`

```json
{
  "status": "en_progreso",
  "cola_id": "install-2026-08-01T10:10:00",
  "total": 2,
  "completados": 1,
  "en_curso": "scikit-learn (Python)",
  "errores": [],
  "historial": [{"paquete":"plm","motor":"R","resultado":"ok","version":"2.6.4"}]
}
```

### Manifiesto predeterminado

**R** (Req 6.5): `jsonlite`, `plm`, `stargazer`, `e1071`, `rpart`, `VGAM`, `tseries`,
`FactoMineR`, `wooldridge`, `cluster`, `PerformanceAnalytics`, `plotly`, `htmlwidgets`,
`fitdistrplus`

**Python** (Req 8.4): `nltk`, `scikit-learn`, `pandas`, `numpy`

**Julia**: `DataFrames`, `Statistics`, `JSON`, `Distributions`

---

## Error Handling

| Escenario | Comportamiento |
|-----------|----------------|
| Motor no disponible al verificar | `motor_disponible: false`, sin HTTP 5xx (Req 9.5) |
| Manifiesto con entrada inválida | Omitir entrada, log WARNING, continuar (Req 1.5) |
| Timeout verificación inicio (>30s) | Resultado parcial, no bloquea (Req 2.5) |
| Timeout verificación función (>5s) | `instalado: unknown`, no advierte (Req 3.4) |
| Instalación de paquete falla | Log ERROR, notifica usuario, continúa cola (Req 5.5) |
| Motor Julia no disponible al instalar | Diferir, notificar "pendiente" (Req 7.3) |
| `packages-status-cache.json` corrupto | Regenerar desde verificación en vivo |
| `packages-manifest.json` no existe | Generar desde valores predeterminados (Req 1.3) |

### Formato de log

```
[2026-08-01T10:05:30] [INFO]  [PKG] Motor=R verificados=14 faltantes=1 duracion=2340ms
[2026-08-01T10:10:15] [INFO]  [PKG] Motor=R instalar=plm version=2.6.4 resultado=ok
[2026-08-01T10:10:45] [ERROR] [PKG] Motor=Julia instalar=Optim error="PkgServer unreachable"
```

---

## Testing Strategy

### Enfoque dual

**Pruebas unitarias (ejemplos concretos):** cubren comportamientos de inicialización, timeouts,
threading, efectos secundarios (logging, escritura en disco) y casos de error específicos.

**Pruebas basadas en propiedades (PBT):** verifican invariantes universales sobre la lógica
de transformación: generación del manifiesto, filtrado de dependencias, scripts R/Julia/Python,
y estructura de respuestas HTTP.

**Librería PBT:** `hypothesis` (ya presente en el proyecto — `.hypothesis/` en la raíz).
Configuración mínima: `@settings(max_examples=100)`.

**Tag de cada prueba de propiedad:**
`# Feature: neven-package-manager, Property N: <texto>`

### Pruebas unitarias (ejemplos concretos)

- `test_load_manifest_creates_default_when_missing` — Req 1.3
- `test_start_launches_background_thread` — Req 2.1, 2.2
- `test_verificar_todos_timeout_returns_partial` — Req 2.5
- `test_verificar_funcion_timeout_returns_unknown` — Req 3.4
- `test_concurrent_run_skips_second_check` — Req 3.5
- `test_install_r_via_pipe_client` — Req 6.1, con mock de PipeClient
- `test_install_julia_deferred_when_engine_unavailable` — Req 7.3
- `test_install_success_updates_manifest` — Req 5.4
- `test_install_failure_continues_queue` — Req 5.5
- `test_endpoint_motor_unavailable_returns_flag` — Req 9.5
- `test_log_written_on_verification_complete` — Req 10.1

### Pruebas de propiedad (hypothesis, 100+ iteraciones)

Cada prueba implementa exactamente una propiedad de la sección Correctness Properties.

```python
# Feature: neven-package-manager, Property 1: integridad del manifiesto generado
@given(packages=st.lists(valid_package_entry_strategy(), min_size=0, max_size=50))
@settings(max_examples=100)
def test_manifest_integrity(packages): ...

# Feature: neven-package-manager, Property 4: filtrado exacto de paquetes por función
@given(manifest=manifest_strategy(), function_id=st.text(min_size=1))
@settings(max_examples=100)
def test_filter_by_function_exact(manifest, function_id): ...
```

### Pruebas de integración

- Verificar que `GET /api/packages/status` está registrado en el servidor HTTP
- Verificar que `_pkg_service` se inicializa al arrancar el servidor
- Verificar que el hook en `handle_run()` inyecta el slot de advertencia cuando hay faltantes

---

## Correctness Properties

*Una propiedad es una característica del comportamiento que debe mantenerse verdadera en todas
las ejecuciones válidas del sistema — en esencia, una declaración formal de qué debe hacer el
software. Las propiedades sirven como puente entre las especificaciones legibles por humanos y
las garantías de corrección verificables automáticamente.*

### Property 1: Integridad del manifiesto generado

*Para cualquier* conjunto de entradas de paquetes (nombre, motor, versión mínima, funciones),
el manifiesto generado por `generate_manifest()` debe contener exactamente esas entradas con
todos los campos requeridos (`nombre`, `motor`, `version_minima`, `funciones`) presentes y no
nulos.

**Validates: Requirements 1.2**

---

### Property 2: Absorción de dependencias de sidecars sin duplicados

*Para cualquier* sidecar JSON con un campo `dependencies` que declare paquetes en uno o más
motores, después de llamar `merge_sidecar_deps(sidecar)`, el manifiesto debe contener todos
esos paquetes; y si alguno ya existía, la entrada original no debe duplicarse — el total de
entradas para ese paquete y motor debe ser exactamente uno.

**Validates: Requirements 1.4**

---

### Property 3: Tolerancia a entradas inválidas en el manifiesto

*Para cualquier* archivo de manifiesto que contenga una mezcla de entradas válidas (con todos
los campos requeridos: `nombre`, `motor`, `version_minima`, `funciones`) e inválidas (con
campos ausentes o tipo incorrecto), `load_manifest()` debe retornar únicamente las entradas
válidas, sin lanzar excepción y sin incluir ninguna entrada inválida en el resultado.

**Validates: Requirements 1.5**

---

### Property 4: Filtrado exacto de paquetes por función

*Para cualquier* manifiesto con N paquetes distribuidos en M funciones distintas, y para
cualquier `function_id` válido, `verificar_funcion(function_id)` debe retornar exactamente
los paquetes cuyo campo `funciones` incluye ese `function_id`, ni más ni menos.

**Validates: Requirements 3.1**

---

### Property 5: Autorización explícita como precondición de instalación

*Para cualquier* secuencia de llamadas a la API pública de `PackageManagerService` que no
incluya ninguna llamada a `encolar_instalacion()`, el estado interno de la cola de instalación
debe permanecer vacío y ningún paquete debe ser instalado.

**Validates: Requirements 5.1**

---

### Property 6: Orden FIFO de la cola de instalación

*Para cualquier* lista de N paquetes encolados mediante `encolar_instalacion()`, el historial
de `get_progress()` debe reflejar que las instalaciones se completaron en el mismo orden en
que fueron encoladas — el índice de aparición en el historial es idéntico al índice de entrada
en la cola.

**Validates: Requirements 5.2**

---

### Property 7: Corrección del script R de instalación

*Para cualquier* nombre de paquete R válido y cualquier URL de repositorio CRAN, el código
generado y enviado a ControlR por `_instalar_r()` debe contener una llamada a
`install.packages()` con el nombre del paquete, `dependencies = TRUE`, y el repositorio
especificado en el argumento `repos`.

**Validates: Requirements 6.1, 6.3**

---

### Property 8: Corrección del script Julia de verificación e instalación

*Para cualquier* nombre de paquete Julia válido, el código generado por `_verificar_julia()`
debe contener `Base.find_package` o `Pkg.status`, y el código de `_instalar_julia()` debe
contener `Pkg.add` con el nombre del paquete como argumento.

**Validates: Requirements 7.1, 7.2**

---

### Property 9: Reutilización del ejecutable Python correcto

*Para cualquier* nombre de paquete Python, tanto `_verificar_python()` como
`_instalar_python()` deben invocar un subproceso cuyo primer elemento es exactamente el
ejecutable retornado por `_get_python_exe()` de `package_manager.py`, nunca un ejecutable
diferente ni hardcodeado.

**Validates: Requirements 8.1, 8.2, 8.3**

---

### Property 10: Completitud del esquema de respuesta HTTP

*Para cualquier* lista de estados de paquetes (con cualquier combinación de motores, paquetes
instalados y ausentes), la respuesta serializada de `GET /api/packages/status` debe contener
para cada elemento los seis campos obligatorios: `motor`, `paquete`, `instalado`,
`version_instalada`, `version_requerida`, `funciones_afectadas`. Ningún campo puede estar
ausente del objeto JSON.

**Validates: Requirements 9.4**

---

### Property 11: Timestamp ISO 8601 en el caché de estado

*Para cualquier* resultado de verificación con cualquier combinación de motores y estados,
`save_cache()` debe escribir un archivo JSON que contenga, para cada motor verificado, un
campo de timestamp con formato ISO 8601 válido (`YYYY-MM-DDTHH:MM:SS`), parseable sin error
por `datetime.fromisoformat()`.

**Validates: Requirements 10.4, 10.5**
