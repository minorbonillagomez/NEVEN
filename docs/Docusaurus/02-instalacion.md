---
id: instalacion
title: Capitulo 2 -- Instalacion
sidebar_label: 2. Instalacion
sidebar_position: 2
---

# Capitulo 2: Instalacion

## 2.1 Requisitos del sistema

| Componente | Version minima | Descarga |
|:---|:---|:---|
| Windows | 10/11 (64 bits) | -- |
| Microsoft Excel | 2016+ o Microsoft 365 | -- |
| R | 4.4.1 | [cran.r-project.org](https://cran.r-project.org) |
| Julia | 1.12.6 | [julialang.org](https://julialang.org) |
| Pandoc | 3.6 | [github.com/jgm/pandoc](https://github.com/jgm/pandoc/releases) |
| Quarto | 1.9.18 | [quarto.org](https://quarto.org/docs/download) |
| WebView2 Runtime | -- | Preinstalado en Windows 10/11 |

## 2.2 Pasos de instalacion

### Paso 1: Copiar archivos

Copiar el contenido de `Dist/` a `C:\NEVEN\`:

```powershell
Copy-Item "Dist\*" "C:\NEVEN\" -Recurse -Force
```

### Paso 2: Crear junction para Quarto

Quarto 1.9.18 tiene un bug con rutas que contienen espacios. La solucion es un junction:

```cmd
mklink /J C:\Quarto "C:\Program Files\Quarto"
```

### Paso 3: Registrar el Ribbon COM

```powershell
regsvr32 "C:\NEVEN\NEVENRibbon.dll"
```

### Paso 4: Cargar el XLL en Excel

1. Abrir Excel
2. Archivo --> Opciones --> Complementos
3. En "Administrar", seleccionar "Complementos de Excel" --> Ir
4. Examinar --> `C:\NEVEN\NEVEN64.xll`

## 2.3 Verificacion rapida

Despues de la instalacion, verificar en celdas de Excel:

$
\texttt{=NEVEN.r("1+1")} \rightarrow 2 \qquad \texttt{=NEVEN.j("sqrt(144)")} \rightarrow 12
$

## 2.4 Checklist completo

| # | Verificacion | Formula | Resultado esperado |
|:---|:---|:---|:---|
| 1 | R operativo | `=NEVEN.r("1+1")` | $2$ |
| 2 | Julia operativa | `=NEVEN.j("1+1")` | $2$ |
| 3 | WebView2 | `=NEVEN.v("<html><body>OK</body></html>")` | Ventana |
| 4 | Pluto.jl | `=NEVEN.pluto.status()` | "stopped" |
| 5 | Quarto | `=NEVEN.q("C:/NEVEN/quarto/test_report.qmd")` | Reporte |
| 6 | Ribbon | Pestana NEVEN en cinta | 13 botones |

## 2.5 Estructura de directorios

```
C:\NEVEN\
+-- NEVEN64.xll              # Add-in Excel
+-- NEVENRibbon.dll           # Ribbon COM
+-- ControlR.exe               # Motor R
+-- ControlJulia.exe           # Motor Julia
+-- neven-config.json         # Configuracion
+-- neven-languages.json      # R + Julia
+-- startup\                   # Scripts de inicio
+-- notebooks\                 # 15 notebooks Pluto
+-- data\                      # Datasets Excel<-->Pluto
+-- quarto\                    # Documentos .qmd
+-- CreadorPresentaciones\     # Editor Impress.js
+-- crashes\                   # Telemetria local
+-- webview2-data\             # HTML temporales
```

## 2.6 Paquetes R recomendados

```r
install.packages(c(
    "plotly", "htmlwidgets", "ggplot2",
    "lme4", "survival", "psych", "forecast",
    "car", "Hmisc", "rstanarm", "plm",
    "stargazer", "sandwich", "lmtest"
), repos = "https://cran.r-project.org")
```

## 2.7 Paquetes Julia recomendados

```julia
import Pkg
Pkg.add(["Pluto", "Plots", "DataFrames", "CSV",
         "MultivariateStats", "JuMP", "HiGHS"])
```
