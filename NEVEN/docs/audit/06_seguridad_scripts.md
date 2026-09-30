# Auditoría de Seguridad — Scripts (R, Julia, Python)

**Proyecto:** NEVEN  
**Fecha:** 2025-01-XX  
**Alcance:** `libreria/R/*.R`, `libreria/JULIA/*.jl`, `startup/startup.r`, `startup/startup.jl`, `startup/startup.py`  
**Auditor:** Kiro (Análisis Automatizado)

---

## Resumen Ejecutivo

| Severidad | Cantidad | Descripción |
|-----------|----------|-------------|
| Crítica   | 2        | Ejecución de comandos OS con entrada no sanitizada |
| Alta      | 3        | Ejecución de código arbitrario, exposición de credenciales |
| Media     | 4        | Dependencias sin versión, acceso a filesystem sin restricción |
| Baja      | 2        | Exposición de información del usuario, rutas hardcodeadas |
| **Total** | **11**   | |

---

## Hallazgos

### [SEC-SEV-001] Ejecución de comandos OS via os.system() en Python
- **Archivo:** startup/startup.py:270
- **Severidad:** Crítica
- **Descripción:** La función `quarto_render()` construye un comando shell concatenando directamente el parámetro `file_path` proporcionado por el usuario (desde una celda de Excel) sin sanitización. Un atacante podría inyectar comandos arbitrarios del sistema operativo mediante caracteres especiales en el nombre del archivo (ej: `file.qmd" & del /f /q C:\* & echo "`).
- **Código:**
```python
def quarto_render(file_path, format="html"):
    fp = str(file_path).strip()
    # ...
    cmd = "set " + env_str + " && quarto render " + '"' + fp + '"' + " --to " + fmt
    work_dir = os.path.dirname(fp) or "."
    full_cmd = 'start /B /D "' + work_dir + '" cmd /C "' + cmd + '"'
    os.system(full_cmd)
```
- **Recomendación:** Reemplazar `os.system()` con `subprocess.Popen()` usando una lista de argumentos (sin shell=True). Validar que `file_path` no contenga caracteres de inyección (`&`, `|`, `;`, `>`, `<`, `` ` ``). Usar `shlex.quote()` o validar contra una expresión regular de rutas seguras:
```python
import subprocess
import re

def quarto_render(file_path, format="html"):
    fp = str(file_path).strip()
    if not re.match(r'^[a-zA-Z]:\\[\w\\\.\-\s]+\.qmd$', fp):
        return "ERROR: Ruta de archivo no válida"
    subprocess.Popen(
        ["quarto", "render", fp, "--to", fmt],
        cwd=os.path.dirname(fp),
        env={**os.environ, "QUARTO_PYTHON": sys.executable}
    )
```

---

### [SEC-SEV-002] Ejecución de código arbitrario via exec() en Python
- **Archivo:** startup/startup.py:175
- **Severidad:** Crítica
- **Descripción:** La función `read_script_file()` ejecuta archivos Python arbitrarios en el namespace de `__main__` usando `exec(compile(source, path, "exec"), __main__.__dict__)`. El parámetro `path` proviene del motor C++ (XLL) que lo recibe como ruta de archivo del usuario. Si un atacante logra que el usuario cargue un archivo .py malicioso, se ejecutará con los privilegios completos del proceso.
- **Código:**
```python
def read_script_file(path, notify=False):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    exec(compile(source, path, "exec"), __main__.__dict__)
```
- **Recomendación:** Este es un comportamiento intencional del diseño (cargar scripts del usuario), pero se debe mitigar:
  1. Restringir las rutas permitidas a un directorio de confianza (ej: `C:\NEVEN\scripts\` o `%USERPROFILE%\Documents\NEVEN\`).
  2. Validar que la ruta no contenga traversal (`..`).
  3. Verificar la extensión del archivo (solo `.py`).
  4. Considerar un sandbox con `RestrictedPython` para scripts de terceros.

---

### [SEC-SEV-003] Inclusión dinámica de archivos en Julia sin restricción de ruta
- **Archivo:** startup/startup.jl:18-25
- **Severidad:** Alta
- **Descripción:** La función `ReadScriptFile(path)` ejecuta `Base.include(Main, path)` con una ruta proporcionada externamente sin validación. Esto permite cargar y ejecutar código Julia arbitrario desde cualquier ubicación del filesystem.
- **Código:**
```julia
function ReadScriptFile(path::String, notify::Bool=false)
    try
        Base.include(Main, path)
        return true
    catch e
        @error "Error loading $path" exception=(e, catch_backtrace())
        return false
    end
end
```
- **Recomendación:** Validar que la ruta esté dentro de directorios permitidos antes de ejecutar `include()`:
```julia
function ReadScriptFile(path::String, notify::Bool=false)
    allowed_dirs = [get(ENV, "NEVEN_HOME", "C:\\NEVEN"), 
                    joinpath(homedir(), "Documents", "NEVEN")]
    abs_path = abspath(path)
    if !any(startswith(abs_path, d) for d in allowed_dirs)
        @error "Ruta no permitida: $path"
        return false
    end
    Base.include(Main, abs_path)
end
```

---

### [SEC-SEV-004] API Key almacenada en archivo JSON sin cifrado
- **Archivo:** startup/startup.py:583-600
- **Severidad:** Alta
- **Descripción:** La función `_read_ai_config()` lee la API key de OpenAI/Azure directamente desde `neven-config.json` en texto plano. Si el archivo es accesible por otros usuarios del sistema o se incluye accidentalmente en un repositorio, las credenciales quedan expuestas. Además, la key se transmite en headers HTTP.
- **Código:**
```python
neven_home = os.environ.get("NEVEN_HOME", os.environ.get("RJ2XCL_HOME", "C:\\NEVEN\\"))
config_path = os.path.join(neven_home, "neven-config.json")
# ...
api_key = ai_config.get("apiKey", "")
headers["Authorization"] = f"Bearer {config['apiKey']}"
```
- **Recomendación:** 
  1. Usar Windows Credential Manager (via `keyring` package) para almacenar API keys.
  2. Verificar permisos del archivo de configuración (solo lectura para el usuario actual).
  3. Agregar `neven-config.json` al `.gitignore` (ya debería estar).
  4. Considerar variables de entorno como alternativa: `NEVEN_AI_KEY`.

---

### [SEC-SEV-005] Exposición de variable USERNAME en resultados de R
- **Archivo:** libreria/R/R4XCL-0-Interno-1.R:611
- **Severidad:** Alta
- **Descripción:** La función `R4XCL_INT_INFO_EJECUCION()` incluye `Sys.getenv("USERNAME")` en los resultados que se devuelven a Excel. Si estos resultados se comparten (archivos Excel, reportes), el nombre de usuario del sistema queda expuesto a terceros.
- **Código:**
```r
InfoEjecucion <- rbind(
    paste0("Especificación: ", FX),
    paste0("N = ", nrow(DT)),
    paste0("Ejecutado por: ", Sys.getenv("USERNAME")),
    paste0("Fecha Ejecución: ", Sys.time())
)
```
- **Recomendación:** Reemplazar con un identificador genérico o hacer la inclusión del username opcional:
```r
usuario <- ifelse(getOption("neven.show.username", FALSE), 
                  Sys.getenv("USERNAME"), "usuario")
```

---

### [SEC-SEV-006] eval(parse()) con entrada derivada de datos de Excel en R
- **Archivo:** Múltiples archivos (10+ ocurrencias)
  - libreria/R/R4XCL-RG-Lineal.R:44
  - libreria/R/R4XCL-RG-Binaria.R:39
  - libreria/R/R4XCL-RG-DatosPanel.R:36, 96
  - libreria/R/R4XCL-RG-Tobit.R:35
  - libreria/R/R4XCL-RG-Poisson.R:24
  - libreria/R/R4XCL-RG-SVM.R:43
  - libreria/R/R4XCL-RG-ArbolDecision.R:58
  - libreria/R/R4XCL-GR-Graficacion.R:49
  - libreria/R/R4XCL-UT-Pivote.R:162
  - libreria/R/R4XCL-0-Interno-1.R:46
- **Severidad:** Media
- **Descripción:** Se usa `eval(parse(text=FX))` donde `FX` es una fórmula construida a partir de nombres de columnas provenientes de celdas de Excel (primera fila de los rangos). Aunque el vector `FX` se construye internamente por `R4XCL_INT_FUNCION()` concatenando nombres de variables, un usuario malicioso podría nombrar una columna con código R inyectable (ej: una columna llamada `); system("cmd /c calc.exe"); #`).
- **Código:**
```r
FX <- R4XCL_INT_FUNCION(SetDatosX, SetDatosY)
especificacion <- eval(parse(text=FX))
```
- **Recomendación:** Validar que los nombres de columnas solo contengan caracteres alfanuméricos, puntos y guiones bajos antes de construir la fórmula:
```r
R4XCL_INT_FUNCION <- function(SetDatosX, SetDatosY = NULL) {
  nombresX <- paste0(SetDatosX[1, 1:ncol(SetDatosX)])
  nombresY <- paste0(SetDatosY[1, 1])
  # Validar nombres seguros
  patron_seguro <- "^[a-zA-Z][a-zA-Z0-9._]*$"
  if (!all(grepl(patron_seguro, c(nombresX, nombresY)))) {
    stop("Error: nombres de variables contienen caracteres no permitidos")
  }
  # ... construir fórmula ...
}
```
Alternativamente, usar `as.formula()` en lugar de `eval(parse())`:
```r
especificacion <- as.formula(FX)
```

---

### [SEC-SEV-007] Carga de paquetes R sin versión específica
- **Archivo:** Múltiples archivos en libreria/R/ (30+ ocurrencias)
- **Severidad:** Media
- **Descripción:** Todos los archivos de la librería R cargan paquetes con `library()` o `require()` sin especificar versión mínima ni máxima. Esto expone al sistema a ataques de supply chain si un paquete es comprometido en CRAN, o a incompatibilidades silenciosas si se actualiza un paquete con breaking changes.
- **Código:**
```r
library(stargazer)
library(margins)
library(plm)
library(e1071)
library(plotly)
library(htmlwidgets)
# ... ~25 paquetes diferentes sin versión
```
- **Recomendación:** 
  1. Usar `renv` para crear un lockfile con versiones exactas.
  2. Documentar versiones mínimas requeridas.
  3. Agregar verificación de versión en el startup:
```r
if (packageVersion("plotly") < "4.10.0") {
  warning("NEVEN requiere plotly >= 4.10.0")
}
```

---

### [SEC-SEV-008] Instalación automática de paquetes desde CRAN sin verificación de integridad
- **Archivo:** libreria/R/R4XCL-0-UT-InstalaPaqueterias.R:387, libreria/R/R4XCL-AD-Pivot.R:27, libreria/R/R4XCL-DS-Wooldridge.R:26
- **Severidad:** Media
- **Descripción:** Varias funciones instalan paquetes automáticamente desde CRAN sin verificar checksums ni firmas. `UT_INSTALACION_WEB()` usa un snapshot de 2018 (`https://packagemanager.rstudio.com/cran/2018-03-15`) que podría contener versiones con vulnerabilidades conocidas. `R4XCL-AD-Pivot.R` instala `rpivotTable` directamente desde CRAN sin confirmación del usuario.
- **Código:**
```r
# R4XCL-AD-Pivot.R - instalación silenciosa
if (!requireNamespace("rpivotTable", quietly = TRUE)) {
    install.packages("rpivotTable", repos = "https://cran.r-project.org", quiet = TRUE)
}

# R4XCL-0-UT-InstalaPaqueterias.R - snapshot antiguo
repositorio_cran <- "https://packagemanager.rstudio.com/cran/2018-03-15"
install.packages(paquete, dependencies = TRUE)
```
- **Recomendación:**
  1. Actualizar el snapshot a una fecha reciente y documentada.
  2. Requerir confirmación explícita del usuario antes de instalar.
  3. Usar `renv` con un lockfile versionado en el repositorio.
  4. Verificar checksums de paquetes instalados localmente.

---

### [SEC-SEV-009] Acceso a filesystem sin restricción en Julia (JC_Archivos)
- **Archivo:** libreria/JULIA/J4XCL-CN-Conectividad.jl:55-125
- **Severidad:** Media
- **Descripción:** La función `JC_Archivos()` permite leer, escribir y listar archivos en cualquier ruta del sistema sin restricción. Un usuario podría leer archivos sensibles (`C:\Windows\System32\config\SAM`) o escribir en ubicaciones del sistema.
- **Código:**
```julia
function JC_Archivos(Ruta="", Datos=nothing, Delimitador=",", TipoOutput=0)
    ruta = string(Ruta)
    if TipoOutput == 1  # Leer CSV
        data = readdlm(ruta, ',')  # Sin validación de ruta
    elseif TipoOutput == 2  # Escribir CSV
        writedlm(ruta, Datos, ',')  # Escritura sin restricción
    elseif TipoOutput == 5  # Listar directorio
        archivos = readdir(ruta)  # Enumeración sin restricción
    end
end
```
- **Recomendación:** Implementar una whitelist de directorios permitidos:
```julia
const ALLOWED_DIRS = [
    get(ENV, "NEVEN_HOME", "C:\\NEVEN"),
    joinpath(homedir(), "Documents"),
    tempdir()
]

function _validate_path(ruta::String)
    abs_ruta = abspath(ruta)
    if !any(startswith(abs_ruta, d) for d in ALLOWED_DIRS)
        return false, "Acceso denegado: ruta fuera de directorios permitidos"
    end
    return true, ""
end
```

---

### [SEC-SEV-010] Dependencias Julia cargadas sin versión en functions.jl
- **Archivo:** libreria/JULIA/functions.jl:7-11
- **Severidad:** Baja
- **Descripción:** El archivo principal de funciones Julia carga módulos de la stdlib sin especificar versiones. Aunque estos son parte de la stdlib y tienen menor riesgo que paquetes externos, no hay mecanismo para detectar incompatibilidades entre versiones de Julia.
- **Código:**
```julia
using LinearAlgebra
using Statistics
using DelimitedFiles
using Dates
using Random
```
- **Recomendación:** Dado que son módulos stdlib, el riesgo es bajo. Documentar la versión mínima de Julia requerida (1.12.6) y agregar un check en el startup:
```julia
if VERSION < v"1.12.0"
    @warn "NEVEN requiere Julia >= 1.12.0"
end
```

---

### [SEC-SEV-011] Rutas hardcodeadas y fallback a C:\NEVEN sin validación
- **Archivo:** startup/startup.jl:155, startup/startup.py:583, libreria/R/R4XCL-GR-QuickPlot.R:7
- **Severidad:** Baja
- **Descripción:** Múltiples scripts usan `C:\NEVEN` como ruta por defecto cuando la variable de entorno `NEVEN_HOME` no está definida. Si un atacante puede crear o modificar archivos en `C:\NEVEN\` (directorio con permisos potencialmente laxos en la raíz de C:), podría inyectar configuraciones o scripts maliciosos.
- **Código:**
```python
# Python
neven_home = os.environ.get("NEVEN_HOME", "C:\\NEVEN\\")

# Julia  
dir = get(ENV, "NEVEN_HOME", "C:\\NEVEN")

# R
home <- Sys.getenv("NEVEN_HOME", "C:/NEVEN")
```
- **Recomendación:** 
  1. Verificar que `C:\NEVEN` tenga permisos restrictivos (solo el usuario actual y administradores).
  2. Documentar que el directorio de instalación debe tener ACLs apropiadas.
  3. Considerar usar `%LOCALAPPDATA%\NEVEN` como alternativa más segura.

---

## Hallazgos Positivos

| # | Aspecto | Detalle |
|---|---------|---------|
| ✅ 1 | **Validación HTTPS en AI** | `startup.py` verifica que endpoints no-localhost usen HTTPS antes de enviar API keys (línea ~800). |
| ✅ 2 | **Enmascaramiento de API key** | La función `_mask_api_key()` oculta la key en logs mostrando solo los primeros 4 caracteres. |
| ✅ 3 | **Rate limiting** | Las llamadas AI usan `_rate_limited_post()` con mutex y delay mínimo de 1 segundo. |
| ✅ 4 | **Buffer limitado en stdout** | `_DiagnosticCapture` tiene un límite de 64KB para prevenir consumo de memoria descontrolado. |
| ✅ 5 | **Validación de parámetros en R** | Las funciones internas R (`R4XCL_INT_*`) validan tipos y existencia de parámetros con `stop()`. |
| ✅ 6 | **tryCatch/try-catch consistente** | Todas las operaciones de I/O en los tres lenguajes usan manejo de errores apropiado. |
| ✅ 7 | **Matplotlib backend no-interactivo** | Python configura `matplotlib.use("Agg")` para evitar ventanas GUI desde el proceso hijo. |
| ✅ 8 | **SHA256 checksums para startup scripts** | Existen archivos `.sha256` junto a `startup.r` y `startup.jl` para verificar integridad. |
| ✅ 9 | **Validación de formato Quarto** | `quarto_render()` valida que el formato sea uno de `html|pdf|docx` y que el archivo tenga extensión `.qmd`. |
| ✅ 10 | **Julia stdlib únicamente** | Las funciones Julia solo usan módulos de la biblioteca estándar (LinearAlgebra, Statistics, etc.), eliminando riesgo de supply chain en paquetes externos. |

---

## Matriz de Riesgo por Lenguaje

| Lenguaje | Crítica | Alta | Media | Baja | Riesgo Global |
|----------|---------|------|-------|------|---------------|
| Python   | 2       | 1    | 0     | 1    | **Alto** |
| R        | 0       | 1    | 3     | 0    | **Medio** |
| Julia    | 0       | 1    | 1     | 1    | **Medio-Bajo** |

---

## Recomendaciones Prioritarias

1. **[URGENTE]** Reemplazar `os.system()` en `quarto_render()` con `subprocess.Popen()` sin shell.
2. **[URGENTE]** Agregar validación de ruta (whitelist + anti-traversal) en `read_script_file()` (Python) y `ReadScriptFile()` (Julia).
3. **[ALTA]** Sanitizar nombres de columnas antes de `eval(parse())` en funciones R, o migrar a `as.formula()`.
4. **[ALTA]** Migrar almacenamiento de API keys a Windows Credential Manager.
5. **[MEDIA]** Implementar `renv` para gestión de dependencias R con versiones fijas.
6. **[MEDIA]** Agregar validación de rutas en `JC_Archivos()` de Julia.
7. **[BAJA]** Asegurar permisos restrictivos en `C:\NEVEN\` durante la instalación.
