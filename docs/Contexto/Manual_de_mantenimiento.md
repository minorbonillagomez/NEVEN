# Manual de Mantenimiento — NEVEN 2.0

## Para desarrolladores y administradores del sistema

---

## 1. Arquitectura del Sistema

### Componentes principales

```
┌──────────────────────────────────────────────────┐
│                Microsoft Excel                    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │            NEVEN64.xll                  │    │
│  │  (Add-in XLL cargado por Excel)          │    │
│  │                                          │    │
│  │  • Registra funciones R., J. y P.        │    │
│  │  • Convierte datos Excel <--> Protobuf   │    │
│  │  • Gestiona procesos hijo                │    │
│  └──────────┬───────────────────────────────┘    │
└─────────────┼────────────────────────────────────┘
              │ Named Pipes + Protobuf
              │
    ┌─────────┼──────────────┐
    │         │              │
┌───┴───┐ ┌──┴─────┐ ┌──────┴──────┐
│ControlR│ │Control │ │ControlPython│
│  .exe  │ │Julia   │ │    .exe     │
│        │ │ .exe   │ │             │
│ R 4.4.1│ │Julia   │ │ Python 3.13 │
│        │ │ 1.12.6 │ │             │
└────────┘ └────────┘ └─────────────┘
```

### Archivos y ubicaciones

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `NEVEN64.xll` | `C:\NEVEN\` | Add-in principal de Excel |
| `ControlR.exe` | `C:\NEVEN\` | Proceso hijo que embebe R |
| `ControlJulia.exe` | `C:\NEVEN\` | Proceso hijo que embebe Julia |
| `ControlPython.exe` | `C:\NEVEN\` | Proceso hijo que embebe Python |
| `neven-config.json` | `C:\NEVEN\` | Configuración principal |
| `neven-languages.json` | `C:\NEVEN\` | Definición de lenguajes |
| `startup\startup.r` | `C:\NEVEN\startup\` | Script de inicialización de R |
| `startup\startup.jl` | `C:\NEVEN\startup\` | Script de inicialización de Julia |
| `startup\startup.py` | `C:\NEVEN\startup\` | Script de inicialización de Python |
| Funciones de usuario | `%USERPROFILE%\Documents\NEVEN\functions\` | Archivos .R, .jl y .py del usuario |
| Gráficos generados | `%USERPROFILE%\Documents\NEVEN\graphics\` | PNGs generados por R |
| Log del XLL | `C:\NEVEN\neven.log` | Log de diagnóstico del add-in |
| Log de ControlR | `C:\NEVEN\controlr.log` | Log de diagnóstico de ControlR |

---

## 2. Compilación del Proyecto

### Requisitos
- Visual Studio 2022 (con "Desarrollo de escritorio con C++")
- CMake 3.15+ (incluido con VS 2022)
- R 4.4.1+ instalado en `C:\Program Files\R\R-4.4.1`
- Conexión a internet (primera compilación descarga Protobuf y GoogleTest)

### Pasos de compilación

Abrir **Developer Command Prompt for VS 2022** y ejecutar:

```cmd
F:
cd \ANTIGRAVITY\2026\NEVEN\NEVEN

:: Build completo limpio (recomendado)
powershell -ExecutionPolicy Bypass -File build.ps1 -Clean -Config Release

:: O usando CMake directamente:
cd Build
cmake .. -A x64 -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build . --config Release
```

### Compilación individual de componentes

```cmd
:: Solo el XLL
cmake --build Build --config Release --target NEVEN_Core

:: Solo ControlJulia
cmake --build Build --config Release --target ControlJulia

:: Solo ControlR
cmake --build Build --config Release --target ControlR

:: Solo ControlPython
cmake --build Build --config Release --target ControlPython
```

### Regenerar libjulia.lib (si Julia se actualiza)

Si se actualiza Julia, es necesario regenerar el import library:

```powershell
cd NEVEN\ControlJulia\lib
# Ejecutar el script original:
.\rebuild-julia-lib.ps1
# Luego ejecutar manualmente:
lib /machine:X64 /def:libjulia.def /out:libjulia.lib
```

> **IMPORTANTE:** Usar el método exacto del script `rebuild-julia-lib.ps1`. Otros métodos de parsing del output de dumpbin producen un `.lib` que compila pero crashea en runtime.

### Julia: Carga bajo demanda (lazyLoad)

Julia se configura con `"lazyLoad": true` en `neven-config.json`. Esto significa:
- Julia NO se conecta al abrir Excel (inicio rápido)
- El usuario activa Julia haciendo clic en "Actualizar" del Ribbon
- El startup.jl (8KB) se evalúa en ese momento (~30-60s de JIT)
- Las funciones J.* se registran después de la activación

### Zombie Killer (limpieza de procesos huérfanos)

El XLL incluye un mecanismo que mata procesos huérfanos de sesiones anteriores al iniciar. El orden de ejecución es crítico:

```
1. file_watch_service_->WatchDirectory()  ← registra directorio
2. Zombie Killer (taskkill ControlR/Julia/Python)  ← mata huérfanos
3. file_watch_service_->Start()  ← inicia monitoreo
4. ConnectLanguages()  ← conecta R y Python (Julia en lazyLoad no)
```

> **CRÍTICO:** El zombie killer DEBE ejecutar ANTES de `file_watch_service_->Start()`. Si se invierte el orden, el file watcher dispara la conexión de Julia y el zombie killer la mata inmediatamente.

### Office WebView2 PreWarm (Windows Update 13/05/2026)

A partir del Windows Update KB5087051 (13/05/2026), Office 365 lanza procesos `msedgewebview2.exe` en background ("PreWarm Empty Addin", "Storage Service", "Network Service"). Estos procesos consumen CPU y pueden interferir con la inicialización de NEVEN.

**Solución aplicada:**
```
HKCU\Software\Microsoft\Office\16.0\Common → StartupBoost = 0 (DWORD)
HKCU\Software\Microsoft\Office\16.0\Wef → EnablePreWarm = 0 (DWORD)
```

### Despliegue

**Opcion 1: Usar el instalador (recomendado)**

```powershell
# Desde la carpeta Install/
.\Install-NEVEN.ps1 -DistDir ..\Build\Dist -Silent

# O doble clic en Install-NEVEN.exe (requiere Dist/ en la misma carpeta)
```

**Opcion 2: Despliegue manual (desarrollo)**

```cmd
:: Cerrar Excel y procesos hijo primero
taskkill /f /im excel.exe 2>nul
taskkill /f /im ControlR.exe 2>nul
taskkill /f /im ControlPython.exe 2>nul

:: Copiar XLL
copy /Y NEVEN\Release\NEVEN.dll C:\NEVEN\NEVEN64.xll

:: Copiar ControlR (solo si cambió)
copy /Y ControlR\Release\ControlR.exe C:\NEVEN\ControlR.exe

:: Copiar ControlPython (solo si cambió)
copy /Y ControlPython\Release\ControlPython.exe C:\NEVEN\ControlPython.exe

:: Copiar startup (solo si cambió)
copy /Y "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\startup\startup.r" "C:\NEVEN\startup\startup.r"
```

### Regenerar libs de R (si se actualiza R)

```cmd
powershell -ExecutionPolicy Bypass -File .\scripts\rebuild-r-libs.ps1 -RHome "C:\Program Files\R\R-4.4.1"
```

---

## 3. Flujo de Inicialización

Cuando Excel carga el XLL, ocurre lo siguiente:

1. Excel llama `xlAutoOpen()` en el XLL
2. El XLL busca `MdCallBack12` en Excel.exe para enganchar la API
3. `RJ2XCL_Engine::Init()` se ejecuta:
   a. **Zombie Process Killer**: mata procesos huérfanos (ControlR/Julia/Python) de sesiones anteriores
   b. `ConfigService` lee `neven-config.json`
   c. `DiscoveryService` busca R, Julia y Python en el registro y paths comunes
   d. `LanguageManager` configura los servicios de lenguaje
   e. Se lanza `ControlR.exe` con `CreateProcessA`
   f. Se conecta al pipe `\\.\pipe\RJ2XCL2-PIPE-R-{PID}`
   g. Se envía `startup.r` a R (con `wait=true`)
   h. Se cargan los archivos `.R` del directorio de funciones
   i. Si Julia está habilitada, se lanza `ControlJulia.exe` y se conecta al pipe Julia
   j. Si Python está habilitado (`"enabled": true` en config), se lanza `ControlPython.exe`
   k. Se conecta al pipe `\\.\pipe\RJ2XCL2-PIPE-P-{PID}` y se envía `startup.py`
   l. Se llama `UpdateFunctions()` que pide a cada motor la lista de funciones
   m. Se registran las funciones en Excel con `xlfRegister`

> **Nota:** Si Python no está instalado en el sistema, el `DiscoveryService` no lo encuentra y NEVEN continúa con R y Julia sin errores.

> **IMPORTANTE (hallazgo mayo 2026):** `xlfRegister` solo funciona dentro del contexto de `xlAutoOpen`. No puede ser invocado desde timers, threads secundarios ni UDFs. Todo el registro de funciones debe completarse sincrónicamente en el paso (l). Ver sección 17 para detalles.

---

## 4. Solución de Problemas Comunes

### Problema: Las funciones no aparecen en Excel (error #NOMBRE?)

**Causa probable**: El XLL no se cargó correctamente.

**Solución**:
1. Ir a Archivo --> Opciones --> Complementos
2. En "Administrar", seleccionar "Complementos de Excel" --> Ir
3. Verificar que `NEVEN64.xll` está marcado
4. Si no aparece, hacer clic en Examinar y seleccionar `C:\NEVEN\NEVEN64.xll`

### Problema: Las funciones NEVEN.r y NEVEN.j aparecen pero las funciones R.* no

**Causa probable**: Los archivos .R no se cargaron en R, o `NEVEN$list.functions()` falló.

**Diagnóstico**:
1. Revisar `C:\NEVEN\neven.log`
2. Buscar líneas `Loading startup file:` — deben aparecer todos los archivos .R
3. Buscar `Updating function registry` — debe aparecer después de cargar los archivos
4. Probar `=NEVEN.R("ls()")` para ver si las funciones están en R

**Solución**:
- Verificar que los archivos .R están en `%USERPROFILE%\Documents\NEVEN\functions\`
- Verificar que `startup.r` tiene la función `NEVEN$list.functions()`

### Problema: =NEVEN.r("1+1") retorna #VALOR!

**Causa probable**: El pipe con ControlR.exe se rompió.

**Diagnóstico**:
1. Revisar `neven.log` — buscar `Pipe broken on write`
2. Verificar si ControlR.exe está corriendo: `tasklist | findstr ControlR`

**Solución**:
- Cerrar Excel y ControlR, reabrir Excel
- Si persiste, verificar que R está en el PATH: `set PATH=C:\Program Files\R\R-4.4.1\bin\x64;%PATH%`

### Problema: ControlR.exe crashea al iniciar

**Causa probable**: Incompatibilidad de headers de R o R.dll no encontrada.

**Diagnóstico**:
1. Revisar `C:\NEVEN\controlr.log`
2. Si termina en `Starting RLoop` sin más líneas, el crash es en la inicialización de R

**Solución**:
- Verificar que `R64.lib` y `RGraphApp64.lib` fueron generados para la versión correcta de R
- Regenerar con `scripts\rebuild-r-libs.ps1`
- Verificar que `ControlR/include/R_ext/Complex.h` existe (fix para MSVC)

### Problema: Los gráficos retornan #VALOR! en lugar de la ruta del PNG

**Causa probable**: `BERT.graphics.device()` no está definida.

**Solución**:
- Verificar que `C:\NEVEN\startup\startup.r` contiene la definición de `BERT.graphics.device`
- Verificar que los archivos .R en `functions\` usan `NEVEN.last.plot()` en lugar de texto fijo

### Problema: Excel se congela al cargar el XLL

**Causa probable**: El callback thread o el startup causan un deadlock.

**Solución**:
1. Matar Excel: `taskkill /f /im excel.exe`
2. Matar ControlR: `taskkill /f /im ControlR.exe`
3. Matar ControlPython: `taskkill /f /im ControlPython.exe`
4. Verificar que el callback thread está deshabilitado en `language_service.cc`
5. Verificar que el startup usa `call.set_wait(true)`

### Problema: =NEVEN.P("1+1") retorna #VALOR! o Python no responde

**Causa probable**: Python no está instalado, o el pipe con ControlPython.exe se rompió.

**Diagnóstico**:
1. Verificar que Python 3.13+ está instalado: `python --version`
2. Revisar `neven.log` — buscar `Language 'Python' connected successfully`
3. Verificar que `neven-config.json` tiene `"Python": { "enabled": true }`
4. Verificar si ControlPython.exe está corriendo: `tasklist | findstr ControlPython`

**Solución**:
- Si Python no está instalado, NEVEN arranca sin él. Instalar Python 3.13+ y reiniciar Excel.
- Si el pipe se rompió, cerrar Excel y ControlPython, reabrir Excel.
- Para deshabilitar Python, cambiar `"enabled": false` en la sección Python de `neven-config.json`.

### Problema: Paquetes de R faltantes

**Síntoma**: Las funciones de R4XCL retornan errores como "there is no package called 'stargazer'"

**Solución**: Ejecutar en Excel:
```
=NEVEN.r("install.packages(c('stargazer','plm','sandwich','margins','ResourceSelection','VGAM','mFilter'), repos='https://cloud.r-project.org')")
```

---

## 5. Agregar Nuevas Funciones de R

### Paso 1: Crear el archivo .R
Crear un archivo en `%USERPROFILE%\Documents\NEVEN\functions\` con la función:

```r
MiFuncion <- function(datos, parametro1 = 0) {
  # Tu código aquí
  resultado <- sum(datos) * parametro1
  return(resultado)
}

# Atributos para Excel
attr(MiFuncion, "description") <- list(
  "Descripción de mi función",
  datos = "Rango de datos de entrada",
  parametro1 = "Un parámetro numérico (default: 0)"
)
attr(MiFuncion, "category") <- "Mis Funciones"
```

### Paso 2: Recargar
Reiniciar Excel o guardar el archivo .R (el FileWatchService detectará el cambio).

### Paso 3: Usar en Excel
La función aparecerá como `=R.MiFuncion(A1:A10, 5)` en Excel.

### Agregar funciones Python

Crear un archivo `.py` en `%USERPROFILE%\Documents\NEVEN\functions\`:

```python
def MiCalculoPy(datos, factor=1.0):
    """Multiplica la suma de los datos por un factor.

    Args:
        datos: Rango de datos de entrada
        factor: Factor multiplicador (default: 1.0)
    """
    return sum(datos) * factor
```

Usar en Excel: `=P.MiCalculoPy(A1:A10, 2.5)`

> **Nota:** El prefijo para funciones Python es `P` (mayúscula), consistente con `R.` y `J.` para funciones de usuario.

---

## 6. Archivos Clave del Código Fuente

### XLL (NEVEN.dll)

| Archivo | Función |
|---------|---------|
| `NEVEN/src/NEVEN.cc` | Singleton principal, `Init()`, `xlAutoOpen()` |
| `NEVEN/src/basic_functions.cc` | Funciones exportadas (`RJ_FunctionCall`, `RJ_Exec_Generic`) |
| `NEVEN/src/excel_api_functions.cc` | Registro de funciones en Excel (`RegisterFunctions`) |
| `NEVEN/src/language_service.cc` | Comunicación con ControlR/Julia vía pipes |
| `NEVEN/src/xlcall_stubs.cc` | Stubs de `Excel12`/`Excel12v` con firma corregida de `MdCallBack12` |
| `Include/XLCALL.h` | Constantes del Excel SDK (corregidas) |

### ControlR (ControlR.exe)

| Archivo | Función |
|---------|---------|
| `ControlR/src/controlr.cc` | `main()`, loop de pipes, `InputStreamRead` |
| `ControlR/src/rinterface_win.cc` | `RLoop()`, inicialización de R embebido |
| `ControlR/src/rinterface_common.cc` | `RExec`, `RCall`, `ListScriptFunctions`, `RCallback` |
| `ControlR/include/R_ext/Complex.h` | Fix de `Rcomplex` para MSVC (sin `double _Complex`) |

### ControlPython (ControlPython.exe)

| Archivo | Función |
|---------|---------|
| `ControlPython/src/control_python.cc` | `main()`, loop de pipes, inicialización de Python embebido |
| `ControlPython/src/python_interface.cc` | Ejecución de código Python, conversión de tipos |
| `ControlPython/include/python_interface.h` | Interfaz pública de Python |

### Configuración

| Archivo | Función |
|---------|---------|
| `startup/startup.r` | Inicialización de R: `list.functions()`, `BERT.graphics.device()` |
| `Install/neven-config.json` | Configuración principal |
| `Install/neven-languages.json` | Definición de lenguajes (ejecutables, argumentos, paths) |

---

## 7. Fixes Críticos Aplicados (Referencia)

Estos son los cambios más importantes que se hicieron para que el sistema funcione. Si se revierte alguno, el sistema dejará de funcionar:

1. **Firma de MdCallBack12** (`xlcall_stubs.cc`): El orden de parámetros es `(xlfn, count, opers[], operRes)`, NO `(xlfn, operRes, count, opers[])`

2. **Constantes del Excel SDK** (`XLCALL.h`): `xlGetName = 0x4019`, `xlCoerce = 0x4002`, `xlFree = 0x4000`

3. **Complex.h para MSVC** (`ControlR/include/R_ext/Complex.h`): R 4.4.1 usa `double _Complex` que MSVC no soporta. El fix define `Rcomplex` como struct simple

4. **ReadConsole firma** (`rinterface_win.cc`, `controlr.cc`, `controlr.h`): R 4.4.1 cambió `char*` a `unsigned char*`

5. **CharacterMode = LinkDLL** (`rinterface_win.cc`): Necesario para ejecutar sin consola

6. **Startup con wait=true** (`language_service.cc`): El startup debe esperar respuesta para mantener el pipe sincronizado

7. **Export name RJ_FunctionCall** (`excel_api_functions.cc`): Debe coincidir con el `.def` (`RJ_FunctionCall1000`, no `RJ2XCLFunctionCall1000`)

8. **Fallback de xlGetName** (`excel_api_functions.cc`): Usa `GetModuleFileNameW` con corrección de extensión `.dll` --> `.xll`

---

## 8. Logs y Diagnóstico

### Ubicación de logs
- `C:\NEVEN\neven.log` — Log del XLL (dentro de Excel)
- `C:\NEVEN\controlr.log` — Log de ControlR.exe
- `C:\NEVEN\controlpython.log` — Log de ControlPython.exe

### Cómo leer el log del XLL

```
[INFO] xlAutoOpen called                    <-- Excel cargó el XLL
[INFO] Discovered R version 4.4.1          <-- R encontrado
[INFO] Pipe connected OK!                  <-- Conexión con ControlR exitosa
[INFO] Language 'R' connected successfully  <-- R listo para usar
[INFO] Loading startup file: ...           <-- Archivos .R cargándose
[INFO] Updating function registry          <-- Funciones registrándose en Excel
[ERROR] ERR getting dll name               <-- Normal (usa fallback)
[ERROR] ERR register function: 0           <-- Problema de registro (ver sección 4)
[WARN] Pipe broken on write               <-- Pipe roto (reiniciar Excel)
```

### Borrar logs para diagnóstico limpio
```cmd
taskkill /f /im excel.exe 2>nul
taskkill /f /im ControlR.exe 2>nul
taskkill /f /im ControlPython.exe 2>nul
del C:\NEVEN\neven.log
del C:\NEVEN\controlr.log
del C:\NEVEN\controlpython.log
```

---

*Manual generado por Team Vikingos ⚔️ — Abril 2026*


---

## 9. Configuración Centralizada (neven-config.json)

Todos los parámetros operativos se leen de `neven-config.json`:

```json
{
  "NEVEN": {
    "functionsDirectory": "%USERPROFILE%\\Documents\\NEVEN\\functions",
    "graphicsDirectory": "%USERPROFILE%\\Documents\\NEVEN\\graphics",
    "logFile": "%NEVEN_HOME%\\neven.log",
    "openConsole": false,
    "useJobObject": true,
    "callTimeoutMs": 600000,
    "maxRetries": 2,
    "sandboxEnabled": true,
    "R": { "home": "", "minMajor": 3, "minMinor": 5, "maxMajor": 99 },
    "Julia": { "home": "", "enabled": true, "minMajor": 1, "minMinor": 6, "maxMajor": 99 },
    "Python": { "home": "", "enabled": true, "minMajor": 3, "minMinor": 10, "maxMajor": 99 }
  },
  "WebView2": {
    "enabled": true,
    "maxViewers": 8,
    "maxMemoryMB": 512
  },
  "Pluto": {
    "port": 1234
  }
}
```

| Parámetro | Tipo | Default | Descripción |
|:---|:---|:---|:---|
| `functionsDirectory` | string | `%USERPROFILE%\Documents\NEVEN\functions` | Directorio de funciones de usuario (.R, .jl, .py) |
| `graphicsDirectory` | string | `%USERPROFILE%\Documents\NEVEN\graphics` | Directorio de gráficos generados (PNG, HTML) |
| `logFile` | string | `%NEVEN_HOME%\neven.log` | Ruta del archivo de log |
| `callTimeoutMs` | int | 600000 (10 min) | Timeout para llamadas a R/Julia/Python. Julia necesita más por JIT |
| `maxRetries` | int | 2 | Máximo de reintentos al reconectar pipe roto |
| `sandboxEnabled` | bool | true | Bloquea system(), shell(), file.remove() en código arbitrario |
| `openConsole` | bool | false | Abrir consola REPL al inicio |
| `useJobObject` | bool | true | Matar procesos hijo al cerrar Excel |
| `R.home` | string | "" (auto-detect) | Ruta de R. Vacío = auto-detectar desde registro |
| `Julia.home` | string | "" (auto-detect) | Ruta de Julia. Vacío = auto-detectar desde LocalAppData |
| `Julia.enabled` | bool | true | Habilitar/deshabilitar Julia. Si es false, NEVEN arranca solo con R |
| `Python.home` | string | "" (auto-detect) | Ruta de Python. Vacío = auto-detectar desde PATH/registro |
| `Python.enabled` | bool | true | Habilitar/deshabilitar Python. Si es false, NEVEN arranca sin Python |
| `WebView2.enabled` | bool | true | Habilitar/deshabilitar el visor WebView2 |
| `WebView2.maxViewers` | int | 8 | Máximo de ventanas WebView2 simultáneas (1-16) |
| `WebView2.maxMemoryMB` | int | 512 | Límite de memoria para WebView2 (128-2048 MB) |
| `Pluto.port` | int | 1234 | Puerto del servidor Pluto.jl (1024-65535) |

---

## 10. Sistema de Seguridad (Sandbox)

### Comandos Bloqueados — R
Cuando `sandboxEnabled: true`, los siguientes patrones se bloquean en `=NEVEN.R()`:

| Categoría | Patrones Bloqueados |
|:---|:---|
| **Shell** | `system()`, `system2()`, `shell()`, `shell.exec()`, `pipe()` |
| **Archivos** | `file.remove()`, `unlink()`, `file.rename()`, `file.copy()`, `file.create()` |
| **Red** | `download.file()`, `url()`, `socketConnection()` |
| **Código dinámico** | `eval(parse())`, `do.call()`, `match.fun()`, `get()` |
| **Código nativo** | `dyn.load()`, `.C()`, `.Call()`, `.Fortran()`, `.External()` |
| **Entorno** | `Sys.setenv()`, `setwd()` |
| **Bypass** | `paste()` + fragmentos sospechosos, `assign()` + `envir` |

### Comandos Bloqueados — Julia
| Categoría | Patrones Bloqueados |
|:---|:---|
| **Shell** | `run()`, `pipeline()`, backtick literals (`` ` ``) |
| **Archivos** | `rm()`, `mv()`, `cp()`, `mkpath()` |
| **Red** | `download()` |
| **Código nativo** | `ccall()`, `@ccall`, `cglobal()` |
| **Código dinámico** | `eval()`, `Meta.parse()`, `include()` |
| **Memoria** | `unsafe_load()`, `unsafe_store!`, `unsafe_pointer` |
| **Bypass** | `$()` interpolación + comandos sospechosos |

### Comandos Bloqueados — Python
| Categoría | Patrones Bloqueados |
|:---|:---|
| **Shell** | `os.system()`, `os.popen()`, `subprocess.*`, `os.exec*()` |
| **Archivos** | `os.remove()`, `os.unlink()`, `shutil.rmtree()`, `os.rename()` |
| **Red** | `urllib.*`, `requests.*`, `socket.*`, `http.client.*` |
| **Código dinámico** | `exec()`, `eval()`, `compile()`, `__import__()` |
| **Código nativo** | `ctypes.*`, `cffi.*` |
| **Entorno** | `os.environ`, `os.putenv()`, `os.chdir()` |
| **Bypass** | `getattr()` + módulos sospechosos, `importlib.*` |

### Protección contra bypass
- Whitespace stripping: `sys tem()` se detecta igual que `system()`
- String concatenation: `paste0("sys","tem()")` se detecta como bypass
- Case insensitive: `SYSTEM()`, `System()` se bloquean igual

### Funciones NO afectadas
Las funciones registradas (`=R.MR_Lineal(...)`, `=R.AD_ACP.C(...)`, etc.) NO pasan por el sandbox porque se ejecutan vía `RJ_FunctionCall`, no vía `RJ_Exec_Generic`.

### Deshabilitar sandbox (solo desarrollo)
En `neven-config.json`, cambiar `"sandboxEnabled": false`. **No recomendado en producción.**

### Validación de configuración
`ConfigService::ValidateConfig()` verifica al cargar `neven-config.json`:
- Paths no contienen `..` (path traversal)
- Paths no contienen `|`, `&`, `;`, `` ` ``, `$`, `>`, `<` (command injection)
- `callTimeoutMs` en rango 0-1800000 (max 30 min)
- `maxRetries` en rango 0-10

---

## 11. Correcciones de Seguridad Aplicadas

| Fecha | Hallazgo | Corrección |
|:---|:---|:---|
| 14-abr-2026 | C-01: Inyección de comandos `system()` | `CreateDirectoryA()` recursivo |
| 15-abr-2026 | C-02: Ejecución sin sandboxing | `SandboxVerifier` con patrones bloqueados |
| 15-abr-2026 | C-03: COM pointers sin validar | Validación nullptr, try/catch, no Release() si unmarshal falla |
| 14-abr-2026 | H-01: Memory leak en Pipe | Destructor cierra handles |
| 15-abr-2026 | H-02: Race condition callbacks | Mutex en CallbackInfo |
| 15-abr-2026 | H-03: goto retry infinito | Contador MAX_RETRIES desde config |
| 14-abr-2026 | H-04: Variables estáticas UDF | `thread_local XLOPER12` |
| 14-abr-2026 | H-05: Timeout global | Per-instance `first_call_timeout_` |
| 15-abr-2026 | S-01: Sandbox bypass whitespace | StripWhitespace() normaliza antes de comparar |
| 15-abr-2026 | S-02: Julia ccall/native code | ccall, @ccall, cglobal, unsafe_* bloqueados |
| 15-abr-2026 | S-03: R eval(parse()) bypass | eval(parse()), do.call(), get(), .Call(), .C() bloqueados |
| 15-abr-2026 | S-04: Julia backtick/pipeline | Backtick literals, pipeline(), include() bloqueados |
| 15-abr-2026 | S-05: Config path traversal | ValidateConfig() bloquea "..", "|", "&", ";", "$" |
| 15-abr-2026 | S-06: SecurityService goto cleanup | RAII con unique_ptr + vector, eliminado HeapAlloc/goto |
| 15-abr-2026 | S-07: R network/env manipulation | url(), socketConnection(), Sys.setenv(), setwd() bloqueados |
| 15-abr-2026 | P-01: Doble xlAutoOpen | Guard `static bool already_initialized` en xlAutoOpen |
| 15-abr-2026 | P-02: Excel congelado al abrir | Timeout 30s para carga de archivos .R durante Init |
| 15-abr-2026 | PERF: Julia sysimage | PackageCompiler.jl genera neven_julia.dll, cold start eliminado |

---

*Manual actualizado: 15 de abril de 2026 — Team Vikingos ⚔️*

------------------------------------------------------------------------

## 13. Componentes Nuevos (Abril 2026)

### WebView2 Viewer

| Archivo | Funcion |
|:---|:---|
| `Common/ViewerManager.cc/h` | Singleton, STA thread, registro de viewers, FIFO eviction |
| `Common/ViewerWindow.cc/h` | Ventana Win32 + ICoreWebView2Controller |
| `Common/ContentPipeline.cc/h` | Routing: inline HTML vs archivo, size-based |
| `Common/PostMessageBridge.cc/h` | Comunicacion JS<-->C++ via PostWebMessage |

### Pluto.jl

| Archivo | Funcion |
|:---|:---|
| `Common/PlutoManager.cc/h` | Lifecycle del servidor Pluto: start/stop, port probe |
| `Common/NotebookLibrary.cc/h` | Registro de 15 notebooks precargados |
| `Common/NotebookExporter.cc/h` | Exportar analisis como notebook Pluto |
| `startup/startup.jl` | Modulo NEVEN con set_data/get_data para pipeline datos |

### Ribbon COM

| Archivo | Funcion |
|:---|:---|
| `Ribbon/ribbon_connect.h` | IRibbonExtensibility + IDTExtensibility2 |
| `Ribbon/ribbon_ui.xml` | Layout XML del Ribbon (5 grupos, 13 botones) |
| `Ribbon/NEVENRibbon_utf8.rc` | Recursos PNG (logos R, Julia, Quarto) |
| `Ribbon/CMakeLists.txt` | Build del DLL COM |

### Quarto

Implementado directamente en `basic_functions.cc` como `RJ_Q`:
- `CreateProcess("C:\Quarto\bin\quarto.exe render ...")` 
- `WaitForSingleObject` (max 60s)
- `ViewerManager::CreateViewerFromFile(output.html)`

### MenuService (deshabilitado — reemplazado por Ribbon COM)

| Archivo | Funcion |
|:---|:---|
| `Common/MenuService.cc/h` | CommandBar toolbar via COM automation (legacy) |

### Funciones Julia

| Archivo | Funcion |
|:---|:---|
| `libreria/JULIA/functions.jl` | 9 modulos + aliases cortos + KNN + Regresion |

### ControlPython

| Archivo | Funcion |
|:---|:---|
| `ControlPython/src/control_python.cc` | `main()`, loop de pipes, Python embebido |
| `ControlPython/src/python_interface.cc` | Ejecución de código, conversión de tipos Python<-->Protobuf |
| `ControlPython/include/python_interface.h` | Interfaz pública |
| `ControlPython/CMakeLists.txt` | Build de ControlPython.exe (`NEVEN_ENABLE_PYTHON=ON` por defecto) |
| `startup/startup.py` | Script de inicialización de Python |

> ControlPython.exe se compila por defecto. Si Python 3.13+ no está instalado en la máquina destino, NEVEN arranca limpiamente solo con R y Julia.

### Despliegue completo (27 abril 2026)

```powershell
Stop-Process -Name "EXCEL","ControlR","ControlJulia","ControlPython","julia" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# XLL + procesos hijo
Copy-Item "Build\Dist\NEVEN64.xll" "C:\NEVEN\NEVEN64.xll" -Force
Copy-Item "Build\Dist\ControlR.exe" "C:\NEVEN\ControlR.exe" -Force
Copy-Item "Build\Dist\ControlJulia.exe" "C:\NEVEN\ControlJulia.exe" -Force
Copy-Item "Build\Dist\ControlPython.exe" "C:\NEVEN\ControlPython.exe" -Force

# Ribbon COM
Copy-Item "Build\Ribbon\Release\NEVENRibbon.dll" "C:\NEVEN\NEVENRibbon.dll" -Force
regsvr32 /s "C:\NEVEN\NEVENRibbon.dll"

# Startup scripts
Copy-Item "startup\startup.jl" "C:\NEVEN\startup\startup.jl" -Force
Copy-Item "startup\startup.py" "C:\NEVEN\startup\startup.py" -Force

# Funciones Julia
Copy-Item "libreria\JULIA\functions.jl" "$env:USERPROFILE\Documents\NEVEN\functions\functions.jl" -Force

# Config (si cambió)
Copy-Item "Install\neven-config.json" "C:\NEVEN\neven-config.json" -Force
Copy-Item "Install\neven-languages.json" "C:\NEVEN\neven-languages.json" -Force

# Si Excel deshabilito el Ribbon:
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\DisabledItems" -Force -ErrorAction SilentlyContinue
```

### Compilacion del Ribbon

```powershell
cmake --build Build --config Release --target NEVENRibbon --parallel
```

### Registro del Ribbon (si no se registro automaticamente)

```powershell
$addinPath = "HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect"
New-Item -Path $addinPath -Force
Set-ItemProperty -Path $addinPath -Name "FriendlyName" -Value "NEVEN" -Type String
Set-ItemProperty -Path $addinPath -Name "Description" -Value "NEVEN Ribbon Menu" -Type String
Set-ItemProperty -Path $addinPath -Name "LoadBehavior" -Value 3 -Type DWord
```

------------------------------------------------------------------------

*Manual actualizado: 27 de abril de 2026 — Team Vikingos ⚔️*

------------------------------------------------------------------------

## 14. Instalador (Mayo 2026)

### Archivos del instalador

| Archivo | Tamaño | Descripcion |
|:---|:---|:---|
| `Install/Install-NEVEN.exe` | 78 KB | Instalador ejecutable (doble clic) |
| `Install/Install-NEVEN.ps1` | ~500 lineas | Script fuente (editable, modo silencioso) |
| `Install/Uninstall-NEVEN.exe` | 32 KB | Desinstalador ejecutable |
| `Install/Uninstall-NEVEN.ps1` | ~170 lineas | Script fuente del desinstalador |
| `Install/Build-Installers.ps1` | ~50 lineas | Regenera los .exe desde los .ps1 |

### Que hace el instalador (6 fases)

1. **Pre-flight**: Verifica Windows 10+, PS 5.1+, detecta R/Julia/Python/Excel
2. **User Choices**: Directorio, paquetes R, shortcut (o modo `-Silent`)
3. **File Deployment**: Copia binarios, configs, startup scripts, ejemplos
4. **Registration**: XLL en registro de Excel, Ribbon COM, junction Quarto
5. **User Setup**: Directorios del usuario, ejemplos, paquetes R, shortcut
6. **Verification**: 5 checks, mensaje de exito, genera desinstalador

### Uso

```powershell
# Instalacion interactiva
.\Install-NEVEN.ps1

# Instalacion silenciosa (usa defaults)
.\Install-NEVEN.ps1 -Silent

# Instalacion con directorio personalizado
.\Install-NEVEN.ps1 -InstallDir D:\NEVEN

# Especificar carpeta Dist
.\Install-NEVEN.ps1 -DistDir F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Build\Dist
```

### Regenerar los .exe

Despues de modificar `Install-NEVEN.ps1` o `Uninstall-NEVEN.ps1`:

```powershell
cd Install
.\Build-Installers.ps1
```

Requiere el modulo `ps2exe` (se instala automaticamente si no existe).

### Desinstalacion

```powershell
# Desde C:\NEVEN\
.\Uninstall-NEVEN.ps1

# O doble clic en Uninstall-NEVEN.exe
```

El desinstalador:
- Pide confirmacion
- Verifica que Excel este cerrado
- Desregistra COM y XLL
- Pregunta si eliminar scripts del usuario
- Elimina el directorio NEVEN
- Muestra resumen de lo removido

------------------------------------------------------------------------

*Manual actualizado: 4 de mayo de 2026 — Team Vikingos ⚔️*

------------------------------------------------------------------------

## 15. Integracion con IA (Mayo 2026)

### Funciones disponibles

| Funcion Excel | Descripcion |
|:---|:---|
| `=P.ai_call(datos, "prompt", "contexto")` | Envia datos a un LLM y retorna interpretacion |
| `=P.ai_list_prompts()` | Lista prompts disponibles |
| `=P.ai_setup()` | Formulario de configuracion en WebView2 |

### Configuracion (neven-config.json)

```json
"AI": {
    "enabled": true,
    "provider": "lmstudio",
    "apiKey": "",
    "model": "nvidia/nemotron-3-nano-4b",
    "endpoint": "http://localhost:1234/v1/chat/completions",
    "maxTokens": 1000,
    "temperature": 0.3,
    "timeout": 120,
    "promptsDirectory": "%USERPROFILE%\\Documents\\NEVEN\\prompts"
}
```

### Proveedores soportados

| Proveedor | API Key | Endpoint por defecto |
|:---|:---|:---|
| OpenAI | Requerida | `https://api.openai.com/v1/chat/completions` |
| Azure OpenAI | Requerida | (configurar manualmente) |
| Ollama (local) | No requerida | `http://localhost:11434/v1/chat/completions` |
| LM Studio (local) | No requerida | `http://localhost:1234/v1/chat/completions` |
| Custom | Segun endpoint | (configurar manualmente) |

### Prompts editables

Los prompts son archivos `.txt` en `Documents\NEVEN\prompts\`:

```
prompts/
├── interpretar_regresion.txt
├── detectar_outliers.txt
├── explicar_acp.txt
├── resumir_descriptiva.txt
├── interpretar_series.txt
├── evaluar_modelo.txt
└── comparar_modelos.txt
```

Cada archivo usa placeholders: `{{resultado}}`, `{{datos}}`, `{{contexto}}`

### Ejemplo de uso

```
=P.ai_call(A1:D5, "interpretar_regresion", "datos de ventas 2025")
→ "El modelo explica el 87% de la variabilidad (R²=0.87)..."
```

Para respuestas largas en WebView2:
```
=NEVEN.V(P.ai_call(A1:D5, "interpretar_regresion"))
```

### Seguridad

- API key solo en neven-config.json, nunca en logs ni mensajes de error
- HTTPS obligatorio para endpoints no-localhost
- Key nunca enviada a R ni Julia, solo usada por ControlPython
- Rate limiting: 1 segundo minimo entre solicitudes

### Troubleshooting AI

| Problema | Solucion |
|:---|:---|
| "AI no configurado" | Agregar seccion AI a neven-config.json con enabled:true |
| "API key invalida" | Verificar la key en neven-config.json |
| "Limite de solicitudes" | Esperar unos segundos e intentar de nuevo |
| "Tiempo de espera agotado" | Modelo local lento — aumentar `"timeout": 180` en seccion AI. Modelos de 4B en CPU tardan ~90s |
| "Sin conexion" | Verificar internet. Para uso local: Ollama o LM Studio |
| "Prompt no encontrado" | Verificar que el .txt existe en Documents\NEVEN\prompts\ |
| `P.ai_call` da #NOMBRE? | Verificar que la descripcion de la funcion no excede 255 chars (limite de xlfRegister) |

### Notas tecnicas de la integracion AI

1. **IPv6/IPv4**: Python resuelve `localhost` a `::1` (IPv6) primero. Si el servidor LLM solo escucha en IPv4, hay timeout. El codigo reemplaza automaticamente `localhost` → `127.0.0.1`.

2. **Proxy bypass**: `urllib.request.ProxyHandler({})` evita que proxies corporativos intercepten trafico a endpoints locales.

3. **Timeout configurable**: Default 120s. Modelos locales (4B-7B en CPU) tardan 30-120s. Modelos cloud (GPT-4o-mini) responden en 2-5s. Configurable via `"timeout": 180` en la seccion AI.

4. **Limite de descripcion**: Excel's `xlfRegister` falla silenciosamente si la descripcion de una funcion excede 255 caracteres. El XLL trunca automaticamente a 250 + "...".

5. **Sin delayed UpdateFunctions**: El registro de funciones se hace exclusivamente durante `xlAutoOpen`. Los timers de re-registro fueron eliminados porque `xlfRegister` falla fuera de ese contexto (error 2).

### Notas tecnicas del Diagnostic Stream

1. **Python funciona**: `_DiagnosticCapture` en `startup.py` redirige `sys.stdout`/`sys.stderr`. Los mensajes se entregan via campos `console_output`/`console_error_output` en el protobuf de respuesta. Funciona correctamente.

2. **R pendiente**: `R_WriteConsoleEx` → `ConsoleMessage()` → `PushWrite()` al callback pipe. Pero `PushWrite` es asíncrono y requiere que `NextWrite()` se llame en el loop de `InputStreamRead`. Durante la ejecución de R, el loop está bloqueado esperando que R termine — los mensajes no se flushean hasta después. Solución propuesta: agregar campos `console_output`/`console_error_output` al protobuf de respuesta de R (mismo patrón que Python), acumulando en un buffer dentro de `ConsoleMessage()` y entregando con la respuesta.

3. **Julia pendiente**: Mismo problema arquitectónico que R. Solución idéntica propuesta.

4. **Timer eliminado**: El timer de 50ms/500ms en el STA thread causaba hangs durante la inicialización de WebView2. Se eliminó completamente. Los mensajes se entregan directamente via `SendToViewer()` (que usa `PostThreadMessage` internamente) o via flush cuando la consola se abre.

------------------------------------------------------------------------

## 16. Consola REPL WebView2 (Mayo 2026)

### Uso

```
=NEVEN.Console()
```

Abre una ventana WebView2 con una consola REPL interactiva para R, Julia y Python.

### Características

| Feature | Descripción |
|:---|:---|
| Tabs | R, Julia, Python con indicador de conexión (punto verde/rojo) |
| Dark theme | Fondo oscuro profesional, prompts coloreados |
| Historial | 500 comandos por lenguaje, navegación con flechas ↑↓ |
| Multi-línea | Shift+Enter o Ctrl+Enter para nuevas líneas |
| Gráficos inline | HTML en iframe sandboxed, imágenes PNG/SVG inline |
| Buffer acotado | Máximo 1000 líneas de output por tab |
| Singleton | Solo una consola abierta a la vez |
| Cero dependencias | HTML autocontenido, sin Node.js, sin npm, sin Electron |

### Archivos

| Archivo | Función |
|:---|:---|
| `Common/REPLManager.h/.cc` | Singleton: lifecycle de la consola + historial de comandos |
| `Common/REPLBridge.h/.cc` | Bridge PostMessage: repl-exec, repl-result, repl-interrupt, repl-status |
| `Common/REPLLanguageAccessor.h/.cc` | Interfaz abstracta (desacopla Common de Core) |
| `Core/src/REPLLanguageAccessorImpl.cc` | Implementación concreta con LanguageManager |
| `console/repl.html` | UI autocontenida (HTML + CSS + JS inline) |

### Arquitectura

```
=NEVEN.Console() → WindowManager → REPLManager → ViewerManager → WebView2
    ↕ PostMessage (JSON)
REPLBridge → Worker Thread → LanguageService::Call() → Named Pipe → ControlR/Julia/Python
```

### Protocolo de mensajes (JS ↔ C++)

| Dirección | Action | Campos |
|:---|:---|:---|
| JS → C++ | `repl-exec` | language, code, id |
| JS → C++ | `repl-interrupt` | language |
| C++ → JS | `repl-result` | id, status, output, language, contentType |
| C++ → JS | `repl-status` | language, connected |

### Troubleshooting

| Problema | Solución |
|:---|:---|
| `=NEVEN.Console()` da #NOMBRE? | Verificar que el XLL está cargado. La función se registra como tipo 1 (worksheet) |
| Consola no responde a código | Verificar `neven.log` — buscar "REPLBridge" o "invalid JSON" |
| JSON inválido en log | Bug del null terminator en WideCharToMultiByte — corregido con `len - 1` |
| Tabs deshabilitados | El lenguaje no está conectado. Verificar que el motor está instalado |

### Nota sobre WindowManager

El `WindowManager` fue simplificado: ya no lanza procesos Electron. Los métodos `ShowConsole()`, `HideConsole()`, `ShutdownConsole()` delegan directamente a `REPLManager`. El código de pipes de la consola Electron fue eliminado.

------------------------------------------------------------------------

*Manual actualizado: 6 de mayo de 2026 — Team Vikingos ⚔️*

------------------------------------------------------------------------

## 17. Flujo de Startup — Hallazgos y Restricciones (Mayo 2026)

### Flujo secuencial obligatorio

El flujo de inicialización de NEVEN **debe** ser estrictamente secuencial durante `xlAutoOpen`:

```
xlAutoOpen()
  → ConnectLanguages()           // Conecta pipes a ControlR, ControlJulia, ControlPython
  → InitializeConnectedLanguages() // Envía startup scripts
  → Carga de archivos .R/.jl/.py
  → MapFunctions()               // Pide lista de funciones a cada motor
  → RegisterFunctions()          // Registra en Excel con xlfRegister
```

### Limitación de xlfRegister (hallazgo clave)

`xlfRegister` **solo funciona durante el contexto de `xlAutoOpen`**. Intentar llamarlo desde:
- Callbacks `WM_TIMER`
- Threads secundarios
- Funciones de celda (UDF)
- Cualquier momento posterior a `xlAutoOpen`

...retorna error 2 (función no disponible). Esta es una restricción no documentada del SDK de Excel.

**Implicación:** No es posible registrar funciones de forma diferida o paralela. Todo el registro debe completarse sincrónicamente dentro de `xlAutoOpen`.

### InitOrchestrator (infraestructura inactiva)

Se implementó un `InitOrchestrator` para inicialización paralela de motores, pero fue desactivado porque:
1. `xlfRegister` no funciona fuera de `xlAutoOpen`
2. Causaba race conditions con el Ribbon COM Add-in
3. El Ribbon invoca `SetPointers` antes de que todos los motores conecten

La infraestructura permanece en el código (`Common/InitOrchestrator.h/.cc`) para potencial uso futuro si Microsoft relaja las restricciones de `xlfRegister`.

### SetPointers Race Condition Fix

**Problema:** El Ribbon COM Add-in llama `RJ2XCL_Engine::SetPointers()` durante su inicialización, que puede ocurrir antes de que todos los motores de lenguaje hayan conectado sus pipes. `SetApplicationPointer()` bloqueaba indefinidamente esperando un pipe no conectado.

**Solución:** `SetPointers()` ahora verifica `IsConnected()` de cada servicio antes de llamar `SetApplicationPointer()`:

```cpp
void RJ2XCL_Engine::SetPointers() {
    for (auto& service : language_services_) {
        if (service && service->IsConnected()) {
            service->SetApplicationPointer(application_);
        }
        // Si no está conectado, se omite silenciosamente
    }
}
```

**Diagnóstico:** Si Excel se congela al abrir con el Ribbon habilitado, verificar en `neven.log`:
- `SetPointers called` — indica que el Ribbon invocó SetPointers
- `Service not connected, skipping SetApplicationPointer` — comportamiento correcto (skip)
- Si no aparece el skip y hay hang, el fix no está aplicado

### Troubleshooting del startup

| Problema | Causa | Solución |
|:---|:---|:---|
| Excel se congela al abrir | SetPointers bloquea en pipe no conectado | Verificar que el fix de SetPointers está aplicado |
| Funciones no se registran | xlfRegister llamado fuera de xlAutoOpen | Verificar que RegisterFunctions() se llama dentro de xlAutoOpen |
| Ribbon no aparece pero funciones sí | Ribbon COM se cargó antes que el XLL | Normal — el Ribbon reintenta al detectar el XLL |
| Funciones aparecen parcialmente | Un motor no conectó a tiempo | Verificar logs de conexión de cada motor |

------------------------------------------------------------------------

## 18. Función de Diagnóstico =NEVEN.status() (Mayo 2026)

### Uso

```
=NEVEN.status()
```

Retorna una tabla con el estado de todos los motores de lenguaje conectados.

### Información mostrada

| Columna | Descripción |
|:---|:---|
| Motor | Nombre del lenguaje (R, Julia, Python) |
| Conectado | Sí/No — si el pipe está activo |
| Salud | Healthy/Unhealthy/Unknown |
| Prefijo | Prefijo de funciones (R., J., P.) |
| Funciones | Conteo total de funciones registradas para ese motor |

### Ejemplo de output

```
Motor     | Conectado | Salud   | Prefijo | Funciones
R         | Sí        | Healthy | R.      | 90
Julia     | Sí        | Healthy | J.      | 70
Python    | No        | Unknown | P.      | 0
```

### Cuándo usar

- **Soporte técnico:** Verificar rápidamente qué motores están activos sin revisar logs
- **Después de instalar:** Confirmar que todos los motores conectaron correctamente
- **Debugging:** Si funciones no aparecen, verificar si el motor correspondiente está conectado
- **Monitoreo:** Verificar salud después de un crash/reconexión de un motor

### Nombre de exportación

La función se exporta como `NEVEN_Status` (nueva convención de nombres para exports del sistema). Se registra como función de tipo 1 (worksheet function).

### Troubleshooting

| Problema | Solución |
|:---|:---|
| `=NEVEN.status()` da #NOMBRE? | El XLL no está cargado. Verificar complementos de Excel |
| Muestra "No" en un motor que debería estar activo | El motor no conectó. Revisar `neven.log` para errores de pipe |
| Muestra "Unhealthy" | El motor conectó pero no responde a health checks. Reiniciar Excel |

------------------------------------------------------------------------

## 19. Viewer Snap Layout (Mayo 2026)

### Comportamiento

Cuando `=NEVEN.v()` abre un visor WebView2, el sistema automáticamente:
1. Busca la ventana de Excel via `FindWindowW(L"XLMAIN", nullptr)`
2. Obtiene el área de trabajo disponible con `SystemParametersInfo(SPI_GETWORKAREA)` (respeta la barra de tareas)
3. Ajusta Excel a la mitad izquierda con `SetWindowPos()`
4. Abre el visor WebView2 en la mitad derecha

### Resultado

El usuario obtiene un layout lado a lado óptimo sin necesidad de organizar ventanas manualmente:

```
┌─────────────────────┬─────────────────────┐
│                     │                     │
│      Excel          │    WebView2 Viewer  │
│   (datos/fórmulas)  │  (visualización)    │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

### Implementación técnica

- `FindWindowW(L"XLMAIN", nullptr)` — localiza la ventana principal de Excel
- `SystemParametersInfo(SPI_GETWORKAREA, ...)` — obtiene el rectángulo de trabajo (excluye taskbar)
- `SetWindowPos(hExcel, ..., 0, 0, width/2, height, ...)` — Excel a la izquierda
- `SetWindowPos(hViewer, ..., width/2, 0, width/2, height, ...)` — Viewer a la derecha

### Troubleshooting

| Problema | Solución |
|:---|:---|
| Excel no se mueve | `FindWindowW` no encontró la ventana. Verificar que Excel está en primer plano |
| Viewer se abre pero no se ajusta | Error en `SetWindowPos`. Verificar permisos de ventana |
| Layout no respeta la taskbar | `SPI_GETWORKAREA` debería manejar esto. Verificar configuración de múltiples monitores |
| Funciona solo en monitor principal | Comportamiento esperado — usa el work area del monitor primario |

------------------------------------------------------------------------

## 20. Zombie Process Killer (Mayo 2026)

### Qué es

Al inicio del XLL (`RJ2XCL_Engine::Init()`), NEVEN mata automáticamente procesos huérfanos de sesiones anteriores que podrían bloquear los Named Pipes. Esto ocurre **antes** de lanzar los nuevos procesos hijo.

### Procesos que mata

| Proceso | Pipe que bloquea |
|:---|:---|
| `ControlR.exe` | `\\.\pipe\RJ2XCL2-PIPE-R-{PID}` |
| `ControlJulia.exe` | `\\.\pipe\RJ2XCL2-PIPE-J-{PID}` |
| `ControlPython.exe` | `\\.\pipe\RJ2XCL2-PIPE-P-{PID}` |

### Por qué es necesario

Cuando Excel es cerrado forzosamente (crash, `taskkill /f /im excel.exe`, Windows Update, BSOD), los procesos hijo quedan huérfanos:
- Siguen corriendo en background
- Mantienen los Named Pipes abiertos
- Al reabrir Excel, NEVEN intenta crear pipes con el mismo nombre → conflicto
- Resultado: hang en la conexión o error de pipe

Antes de este fix, el usuario debía abrir Task Manager manualmente y matar los procesos.

### Implementación

```cpp
// En Init(), antes de lanzar nuevos procesos:
void KillOrphanedProcesses() {
    const char* processes[] = {"ControlR.exe", "ControlJulia.exe", "ControlPython.exe"};
    for (const auto& proc : processes) {
        std::string cmd = "taskkill /F /IM " + std::string(proc);
        STARTUPINFOA si = {sizeof(si)};
        PROCESS_INFORMATION pi = {};
        CreateProcessA(NULL, cmd.data(), NULL, NULL, FALSE,
                       CREATE_NO_WINDOW, NULL, NULL, &si, &pi);
        if (pi.hProcess) CloseHandle(pi.hProcess);
        if (pi.hThread) CloseHandle(pi.hThread);
    }
}
```

### Detalles técnicos

- **`CREATE_NO_WINDOW`**: No muestra ventana de consola al usuario. La ejecución es invisible.
- **No-bloqueante**: `CreateProcess` retorna inmediatamente. No se espera a que `taskkill` termine (no hay `WaitForSingleObject`). Esto es intencional — no queremos bloquear `xlAutoOpen`.
- **Silencioso**: Si no hay procesos huérfanos, `taskkill` retorna error silenciosamente. No afecta el flujo normal.
- **Orden**: Se ejecuta antes de `ConnectLanguages()`, garantizando que los pipes estén libres.

### Troubleshooting

| Problema | Solución |
|:---|:---|
| Procesos huérfanos persisten después de reabrir Excel | Verificar que `KillOrphanedProcesses()` se llama en `Init()`. Revisar `neven.log` |
| `taskkill` no tiene permisos | Los procesos hijo corren con el mismo usuario que Excel — no requiere elevación |
| Mata procesos de otra instancia de Excel | Comportamiento esperado — NEVEN asume una sola instancia. Si se necesitan múltiples instancias, usar PIDs específicos |

------------------------------------------------------------------------

## 21. Extraer_outputs — Tabla Completa de Outputs (Mayo 2026)

### Qué es

`Extraer_outputs(modelo)` es una función R en `startup.r` que extrae TODOS los outputs de cualquier objeto modelo de R y los retorna como un data.frame estructurado.

### Uso desde Excel

```
=R.MR_Lineal(Y, X, 13)     ← TipoOutput 13 = Tabla completa de outputs
=R.MR_Binario(Y, X, 9)     ← TipoOutput 9 = Tabla completa
=R.AD_ACP(datos, 13)       ← TipoOutput 13 = Tabla completa
```

### Estructura del output

| Columna | Descripción |
|:---|:---|
| Modelo | Clase del modelo (ej: "lm", "glm", "summary.lm") |
| Seccion | Componente del modelo (ej: "coefficients", "residuals") |
| Parametro | Nombre del parámetro (ej: "Intercept", "x1") |
| Metrica | Nombre de la métrica (ej: "Estimate", "Std. Error") |
| Valor | Valor numérico o texto |

### Funciones que lo soportan (TipoOutput)

| Función | TipoOutput para tabla completa |
|:---|:---|
| `MR_Lineal` | 13 |
| `MR_Binario` | 9 |
| `MR_Poisson` | 8 |
| `MR_PanelData` | 16 |
| `ST_SeriesTemporales` | 8 |
| `MR_SVM` | 2 |
| `MR_Tobit` | 7 |
| `AD_ArbolDeDecision` | 9 |
| `AD_ACP` | 13 |
| `AD_KMedias` | 10 |

### Campos omitidos

Los siguientes campos se omiten por ser demasiado grandes o no informativos en formato tabla:
- `model` (la matriz de diseño completa)
- `effects` (vector de efectos)
- `qr` (descomposición QR)
- `x`, `y` (datos originales)
- `fitted.values` (valores ajustados — usar `residuals` en su lugar)

Se **retienen**: `residuals`, `coefficients`, todas las estadísticas de resumen, R², F-statistic, AIC, BIC, etc.

### Cómo funciona internamente

```r
Extraer_outputs <- function(modelo) {
  # 1. Obtiene names() del objeto modelo
  # 2. Para cada componente, extrae su contenido
  # 3. Convierte matrices/vectores/escalares a filas del data.frame
  # 4. Omite campos en la lista de exclusión
  # 5. Retorna data.frame con 5 columnas [Modelo, Seccion, Parametro, Metrica, Valor]
}
```

### Troubleshooting

| Problema | Solución |
|:---|:---|
| Retorna tabla vacía | El modelo no tiene componentes extraíbles. Verificar que el objeto es un modelo válido |
| Falta un campo esperado | Verificar si está en la lista de exclusión. Si no debería estar excluido, editar `Extraer_outputs` en `startup.r` |
| Error "object is not a model" | El TipoOutput más alto solo funciona con funciones que generan modelos R |
| Tabla muy grande | Normal para modelos complejos (panel data, SVM). Usar filtros de Excel para navegar |

------------------------------------------------------------------------

*Manual actualizado: 9 de mayo de 2026 — Team Vikingos ⚔️*
