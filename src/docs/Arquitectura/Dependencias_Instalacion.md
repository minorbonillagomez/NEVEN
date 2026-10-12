# Dependencias de Instalación — NEVEN v2.0

## Guía Completa de Componentes Requeridos

**Fecha**: Junio 2026
**Versión**: 2.0 (WebView2 + Pluto.jl)

Este documento lista TODOS los componentes que deben instalarse para que NEVEN funcione correctamente en la primera ejecución del usuario.

------------------------------------------------------------------------

## 1. Componentes del Sistema (incluidos en el instalador)

| Componente | Versión | Tipo | Tamaño | Notas |
|:---|:---|:---|:---|:---|
| NEVEN64.xll | 2.0 | Add-in Excel | ~2 MB | Compilado MSVC 2022, x64 |
| ControlR.exe | 2.0 | Proceso hijo R | ~1 MB | Embedding R via C API |
| ControlJulia.exe | 2.0 | Proceso hijo Julia | ~1 MB | Embedding Julia via C API |
| ControlPython.exe | 2.0 | Proceso hijo Python | ~1 MB | Embedding Python via stable ABI |
| neven-config.json | — | Configuración | ~1 KB | Timeouts, puertos, paths |
| neven-languages.json | — | Config lenguajes | ~1 KB | R + Julia + Python |
| startup.r | — | Script inicio R | ~5 KB | Funciones internas R |
| startup.jl | — | Script inicio Julia | ~8 KB | Módulo NEVEN + RCall bridge |
| 13 notebooks Pluto | — | Templates .jl | ~50 KB | En `notebooks/` directory |

## 2. Runtimes de Lenguaje (instalación separada)

### R 4.4.1+

| Detalle | Valor |
|:---|:---|
| **Descarga** | https://cran.r-project.org/bin/windows/base/ |
| **Instalador** | `R-4.4.1-win.exe` (~80 MB) |
| **Ruta típica** | `C:\Program Files\R\R-4.4.1\` |
| **Requerido por** | ControlR.exe, funciones `=R.func()` |
| **Verificación** | `=NEVEN.r("R.version.string")` |

### Julia 1.12.6+

| Detalle | Valor |
|:---|:---|
| **Descarga** | https://julialang.org/downloads/ |
| **Instalador** | `julia-1.12.6-win64.exe` (~100 MB) |
| **Ruta típica** | `C:\Users\[user]\AppData\Local\Programs\Julia-1.12.6\` |
| **Requerido por** | ControlJulia.exe, funciones `=J.func()`, Pluto.jl |
| **Verificación** | `=NEVEN.j("VERSION")` |

### Python 3.13+

| Detalle | Valor |
|:---|:---|
| **Descarga** | https://www.python.org/downloads/ |
| **Instalador** | `python-3.13.x-amd64.exe` (~30 MB) |
| **Ruta típica** | `C:\Users\[user]\AppData\Local\Programs\Python\Python313\` |
| **Requerido por** | ControlPython.exe, funciones AI (`=P.ai_call()`), funciones `=P.func()` |
| **Opcional** | Sí — NEVEN funciona sin Python (solo R + Julia) |
| **Verificación** | `=NEVEN.p("1+1")` |

## 3. Paquetes R (instalación automática recomendada)

### Paquetes base (requeridos para funciones estadísticas)

```r
install.packages(c(
    "stargazer", "svDialogs", "lmtest", "sandwich",
    "margins", "usdm", "plm", "rpart", "rpart.plot",
    "PerformanceAnalytics", "tseries", "mFilter",
    "e1071", "dummies", "wooldridge",
    "lme4", "survival", "psych", "rstanarm",
    "car", "Hmisc", "forecast"
), repos = "https://cran.r-project.org")
```

### Paquetes para visualización interactiva (requeridos para Plotly en WebView2)

```r
install.packages(c(
    "plotly", "htmlwidgets", "ggplot2",
    "corrplot", "rpivotTable"
), repos = "https://cran.r-project.org")
```

### Paquetes para mapas y gráficos avanzados

```r
install.packages(c(
    "maps", "rworldmap", "mapdeck"
), repos = "https://cran.r-project.org")
```

## 4. Paquetes Julia (instalación desde Julia REPL)

### Paquete requerido: Pluto.jl

```julia
import Pkg
Pkg.add("Pluto")
```

| Detalle | Valor |
|:---|:---|
| **Requerido por** | `=NEVEN.pluto.start()`, notebooks, modo avanzado |
| **Tamaño** | ~50 MB (con dependencias) |
| **Verificación** | `=NEVEN.pluto.status()` retorna "stopped" |

### Paquete opcional: RCall.jl (para pipelines mixtos Julia+R)

```julia
import Pkg
Pkg.add("RCall")
```

| Detalle | Valor |
|:---|:---|
| **Requerido por** | `=J.rcall_status()`, notebooks R via RCall, `multilang_pipeline.jl` |
| **Requiere** | R instalado y `R_HOME` configurado |
| **Verificación** | `=NEVEN.j("rcall_status()")` retorna "available" |

### Paquetes opcionales para notebooks avanzados

```julia
import Pkg
Pkg.add(["JuMP", "HiGHS", "DifferentialEquations", "Turing",
         "Distributions", "Plots", "DataFrames", "CSV"])
```

## 5. Herramientas del Sistema

### Pandoc (REQUERIDO para htmlwidgets selfcontained)

| Detalle | Valor |
|:---|:---|
| **Descarga** | https://github.com/jgm/pandoc/releases/ |
| **Instalador** | `pandoc-3.6.4-windows-x86_64.msi` (~30 MB) |
| **Ruta típica** | `C:\Program Files\Pandoc\` (se agrega al PATH automáticamente) |
| **Requerido por** | `htmlwidgets::saveWidget(selfcontained=TRUE)`, Plotly en WebView2 |
| **Incluir en instalador** | ✅ SÍ — ejecutar MSI silenciosamente durante instalación |
| **Comando silencioso** | `msiexec /i pandoc-3.6.4-windows-x86_64.msi /quiet /norestart` |
| **Verificación** | `=NEVEN.r("Sys.which('pandoc')")` retorna ruta |

### Microsoft Edge WebView2 Runtime

| Detalle | Valor |
|:---|:---|
| **Descarga** | https://developer.microsoft.com/en-us/microsoft-edge/webview2/ |
| **Instalador** | `MicrosoftEdgeWebView2RuntimeInstallerX64.exe` (~1.5 MB bootstrapper) |
| **Preinstalado** | ✅ Windows 10 21H2+ y Windows 11 ya lo incluyen |
| **Requerido por** | `=NEVEN.v()`, visor HTML embebido, Pluto en WebView2 |
| **Incluir en instalador** | ✅ SÍ — verificar presencia, instalar si ausente |
| **Comando silencioso** | `MicrosoftEdgeWebView2RuntimeInstallerX64.exe /silent /install` |
| **Verificación** | `=NEVEN.v.list()` no retorna error de WebView2 |

### Quarto CLI (REQUERIDO para reportes Quarto)

| Detalle | Valor |
|:---|:---|
| **Descarga** | https://quarto.org/docs/download/ |
| **Instalador** | `quarto-1.9.18-win.msi` (~200 MB) |
| **Ruta típica** | `C:\Program Files\Quarto\` |
| **Requerido por** | `=NEVEN.q()`, renderizado de documentos `.qmd` |
| **Incluir en instalador** | ✅ SÍ — instalar MSI + crear junction |
| **Comando silencioso** | `msiexec /i quarto-1.9.18-win.msi /quiet /norestart` |
| **Junction requerido** | `mklink /J C:\Quarto "C:\Program Files\Quarto"` (bug de Sass con espacios en ruta) |
| **Verificación** | `=NEVEN.q("C:/NEVEN/quarto/test_report.qmd")` abre reporte en WebView2 |

**Nota importante:** Quarto 1.9.18 tiene un bug en el compilador Dart/Sass que falla cuando la ruta de instalación contiene espacios (`C:\Program Files\`). La solución es crear un junction link `C:\Quarto` que apunta a la instalación real. El instalador de NEVEN debe crear este junction automáticamente.

## 6. Configuración Post-Instalación

### neven-config.json

```json
{
    "NEVEN": {
        "homeDirectory": "C:\\NEVEN\\",
        "functionsDirectory": "%USERPROFILE%\\Documents\\NEVEN\\functions",
        "R": { "home": "" },
        "Julia": { "home": "" }
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

### neven-languages.json

```json
[
    { "name": "R", "executable": "ControlR.exe", "prefix": "R", "extensions": ["r","R"] },
    { "name": "Julia", "executable": "ControlJulia.exe", "prefix": "J", "extensions": ["jl"] },
    { "name": "Python", "executable": "ControlPython.exe", "prefix": "P", "extensions": ["py"] }
]
```

### Directorios creados automáticamente

| Directorio | Propósito |
|:---|:---|
| `C:\NEVEN\` | Home del add-in |
| `C:\NEVEN\startup\` | Scripts de inicio R y Julia |
| `C:\NEVEN\notebooks\` | 15 notebooks Pluto precargados |
| `C:\NEVEN\notebooks\custom\` | Notebooks modificados por el usuario |
| `C:\NEVEN\notebooks\exports\` | Análisis exportados como notebooks |
| `C:\NEVEN\data\` | Datasets compartidos Excel<-->Pluto (TSV) |
| `C:\NEVEN\quarto\` | Documentos Quarto (.qmd) y salidas HTML |
| `C:\NEVEN\webview2-data\` | Datos WebView2 + archivos HTML temporales |
| `C:\NEVEN\CreadorPresentaciones\` | Editor de presentaciones Impress.js |
| `C:\Quarto` | Junction a `C:\Program Files\Quarto\` (bug Sass) |
| `%USERPROFILE%\Documents\NEVEN\functions\` | Funciones R, Julia y Python del usuario |
| `%USERPROFILE%\Documents\NEVEN\notebooks\` | Notebooks .jl, .R, .py (descubiertos dinámicamente) |
| `%USERPROFILE%\Documents\NEVEN\prompts\` | Templates AI editables (.txt) |
| `%USERPROFILE%\Documents\NEVEN\graphics\` | Gráficos generados |

## 7. Checklist de Verificación Post-Instalación

| # | Verificación | Comando Excel | Resultado Esperado |
|:---|:---|:---|:---|
| 1 | R operativo | `=NEVEN.r("1+1")` | 2 |
| 2 | Julia operativa | `=NEVEN.j("1+1")` | 2 |
| 3 | Funciones R registradas | `=R.MR_Lineal(...)` | Resultado estadístico |
| 4 | Funciones Julia registradas | `=J.JM_Algebra(...)` | Resultado matemático |
| 5 | WebView2 disponible | `=NEVEN.v("<html><body>Test</body></html>")` | Ventana con "Test" |
| 6 | Pluto.jl instalado | `=NEVEN.pluto.status()` | "stopped" |
| 7 | Notebooks disponibles | `=NEVEN.notebook.list()` | 15 nombres |
| 8 | Plotly funcional | `=NEVEN.r("library(plotly); 'OK'")` | "OK" |
| 9 | Pandoc disponible | `=NEVEN.r("Sys.which('pandoc')")` | Ruta a pandoc.exe |
| 10 | Presentaciones | `=NEVEN.presentation.new("Test")` | "presentation-1" |
| 11 | Quarto funcional | `=NEVEN.q("C:/NEVEN/quarto/test_report.qmd")` | Reporte en WebView2 |
| 12 | Excel-->Julia data | `=NEVEN.pluto.data(A1:C4, "test")` | "OK: test (4x3, v1)" |
| 13 | Toolbar visible | Pestaña Complementos | 6 botones NEVEN |
| 14 | Ribbon COM | Pestaña NEVEN en cinta | 13 botones con iconos R/Julia/Quarto |
| 15 | Python operativo | =NEVEN.p("1+1") | 2 |

## 8. Script de Instalación Automatizada (propuesta)

```powershell
# install_rj2xcl.ps1 — Instalador automatizado NEVEN v2.0

# 1. Verificar R
$r_home = "C:\Program Files\R\R-4.4.1"
if (!(Test-Path "$r_home\bin\R.exe")) {
    Write-Host "ERROR: R 4.4.1 no encontrado. Instale desde https://cran.r-project.org"
    exit 1
}

# 2. Verificar Julia
$julia_home = Get-ChildItem "$env:LOCALAPPDATA\Programs\Julia-*" -Directory | Select-Object -Last 1
if (!$julia_home) {
    Write-Host "ERROR: Julia no encontrada. Instale desde https://julialang.org"
    exit 1
}

# 3. Instalar Pandoc (silencioso)
if (!(Get-Command pandoc -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando Pandoc..."
    msiexec /i pandoc-3.6.4-windows-x86_64.msi /quiet /norestart
}

# 4. Instalar WebView2 Runtime (si no está presente)
$wv2 = Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" -ErrorAction SilentlyContinue
if (!$wv2) {
    Write-Host "Instalando WebView2 Runtime..."
    Start-Process MicrosoftEdgeWebView2RuntimeInstallerX64.exe -ArgumentList "/silent /install" -Wait
}

# 5. Instalar Quarto (silencioso) + crear junction
if (!(Test-Path "C:\Program Files\Quarto\bin\quarto.exe")) {
    Write-Host "Instalando Quarto..."
    msiexec /i quarto-1.9.18-win.msi /quiet /norestart
}
if (!(Test-Path "C:\Quarto")) {
    Write-Host "Creando junction C:\Quarto..."
    cmd /c 'mklink /J C:\Quarto "C:\Program Files\Quarto"'
}

# 6. Copiar archivos NEVEN
Copy-Item "Dist\*" "C:\NEVEN\" -Recurse -Force

# 6b. Registrar Ribbon COM Add-in
Copy-Item "Dist\NEVENRibbon.dll" "C:\NEVEN\NEVENRibbon.dll" -Force
Start-Process regsvr32 -ArgumentList "/s `"C:\NEVEN\NEVENRibbon.dll`"" -Wait
$addinPath = "HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect"
New-Item -Path $addinPath -Force | Out-Null
Set-ItemProperty -Path $addinPath -Name "FriendlyName" -Value "NEVEN" -Type String
Set-ItemProperty -Path $addinPath -Name "Description" -Value "NEVEN Ribbon Menu" -Type String
Set-ItemProperty -Path $addinPath -Name "LoadBehavior" -Value 3 -Type DWord

# 7. Crear directorios adicionales
New-Item -ItemType Directory -Path "C:\NEVEN\data" -Force | Out-Null
New-Item -ItemType Directory -Path "C:\NEVEN\quarto" -Force | Out-Null

# 8. Instalar paquetes R
& "$r_home\bin\Rscript.exe" -e "install.packages(c('plotly','htmlwidgets','lme4','survival','psych','forecast','car','Hmisc','rstanarm','plm'), repos='https://cran.r-project.org', quiet=TRUE)"

# 9. Instalar paquetes Julia
& "$($julia_home.FullName)\bin\julia.exe" -e 'import Pkg; Pkg.add("Pluto")'

Write-Host "NEVEN v2.0 instalado correctamente!"
```

------------------------------------------------------------------------

*Documento generado en junio 2026. Versión 2.0.*
*Incluye todas las dependencias descubiertas durante el desarrollo y testing.*
