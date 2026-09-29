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
| Python | 3.12+ | [python.org](https://python.org) |
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
\texttt{=NEVEN.r("1+1")} \rightarrow 2 \qquad \texttt{=NEVEN.j("sqrt(144)")} \rightarrow 12 \qquad \texttt{=NEVEN.py("1+1")} \rightarrow 2
$

## 2.4 Checklist completo

| # | Verificacion | Formula | Resultado esperado |
|:---|:---|:---|:---|
| 1 | R operativo | `=NEVEN.r("1+1")` | $2$ |
| 2 | Julia operativa | `=NEVEN.j("1+1")` | $2$ |
| 3 | Python operativo | `=NEVEN.py("1+1")` | $2$ |
| 4 | WebView2 | `=NEVEN.v("<html><body>OK</body></html>")` | Ventana |
| 5 | Pluto.jl | `=NEVEN.pluto.status()` | "stopped" |
| 6 | Quarto | `=NEVEN.q("C:/NEVEN/quarto/test_report.qmd")` | Reporte |
| 7 | Ribbon | Pestana NEVEN en cinta | 6 grupos, ~15 botones |

## 2.5 NEVEN Studio Standalone

NEVEN Studio Standalone funciona con la misma instalación. No requiere pasos adicionales.

### Abrir el Studio

```
C:\NEVEN\taskpane\NEVEN Studio.vbs  →  Doble clic
```

Se abre el navegador del sistema en `http://localhost:5555`.

### Verificación del Studio

| # | Verificación | Acción | Resultado esperado |
|:---|:---|:---|:---|
| 1 | Studio abre | Doble clic en VBS | Navegador muestra NEVEN Studio |
| 2 | Data Lab | Pestaña "Data Lab" | Dropdown de familias activo |
| 3 | Cargar datos | Data Studio → Cargar CSV | Tabla visible |
| 4 | Run Script R | Run Script → escribir `1+1` → Ejecutar | `[1] 2` |
| 5 | Data Lab K-Medias | AD → K-Medias → asignar columnas → Ejecutar | Tabla de centroides |

### Paquetes Python recomendados para Studio

```bash
pip install duckdb pandas pyarrow pypdf python-docx
```

### Troubleshooting del servidor

Si el TaskPane muestra "ERROR DEL COMPLEMENTO" o no puede conectarse:

1. En la pestana NEVEN → grupo **Studio** → clic en **"Iniciar Servidor"**
2. Esperar mensaje de confirmacion (hasta 15 segundos)
3. Recargar el TaskPane

El boton "Iniciar Servidor" inicia el servidor HTTP en el puerto 5555 si no esta corriendo.

## 2.6 Estructura de directorios

```
C:\NEVEN\
+-- NEVEN64.xll              # Add-in Excel
+-- NEVENRibbon.dll           # Ribbon COM
+-- ControlR.exe               # Motor R
+-- ControlJulia.exe           # Motor Julia
+-- ControlPython.exe          # Motor Python
+-- neven-config.json         # Configuracion
+-- neven-languages.json      # R + Julia + Python
+-- startup\                   # Scripts de inicio
+-- notebooks\                 # 15 notebooks Pluto
+-- data\                      # Datasets Excel<-->Pluto
+-- quarto\                    # Documentos .qmd
+-- CreadorPresentaciones\     # Editor Impress.js
+-- crashes\                   # Telemetria local
+-- taskpane\                  # NEVEN Studio Standalone
|   +-- taskpane.html          # UI web del Studio
|   +-- taskpane.js            # Logica UI
|   +-- datalab.js             # Modulo Data Lab
|   +-- pipe_client.py         # Cliente Named Pipes
|   +-- start_studio.py        # Arranque del Studio
|   \-- NEVEN Studio.vbs       # Lanzador de doble clic
+-- functions\                 # Catalogo Data Lab (40+ funciones)
+-- docs\                      # Documentacion y ontologias
+-- webview2-data\             # HTML temporales
```

## 2.7 Paquetes R recomendados

```r
install.packages(c(
    "plotly", "htmlwidgets", "ggplot2",
    "lme4", "survival", "psych", "forecast",
    "car", "Hmisc", "rstanarm", "plm",
    "stargazer", "sandwich", "lmtest"
), repos = "https://cran.r-project.org")
```

## 2.8 Paquetes Julia recomendados

```julia
import Pkg
Pkg.add(["Pluto", "Plots", "DataFrames", "CSV",
         "MultivariateStats", "JuMP", "HiGHS"])
```
