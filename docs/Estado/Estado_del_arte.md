# Estado del Arte -- NEVEN v2.0

**Fecha**: 9 de mayo de 2026
**Universidad de Costa Rica -- Tesis de Maestria**

------------------------------------------------------------------------

## 1. Contexto Academico

### La Tesis
- **Titulo**: NEVEN -- Sistema Multilenguaje para la Democratizacion del Analisis de Datos en Microsoft Excel
- **Autor**: Minor Bonilla Gomez
- **Programa**: Maestria en Matematica Aplicada, Universidad de Costa Rica

### Problema que Resuelve
Excel es universal pero estadisticamente limitado. R y Julia son potentes pero requieren programacion. NEVEN cierra esta brecha exponiendo funciones de R y Julia como formulas nativas de Excel, con visualizacion interactiva via WebView2 y notebooks reactivos via Pluto.jl.

### Evolucion del Proyecto
| Version | Periodo | Alcance |
|:---|:---|:---|
| R4XCL (tesis original) | 2023 | R en Excel via BERT, 50+ funciones estadisticas |
| NEVEN v1.0 | Ene-Mar 2026 | Fork de BERT, R 4.4.1 + Julia 1.12.6 |
| NEVEN v2.0 | Abr 2026 | WebView2, Pluto.jl, Quarto, Ribbon COM, 125+ funciones |
| **NEVEN v2.0** | **May 2026** | **Rename, R.Pivot, R.Esquisse, R.D3, R.Dashboard, R.Map, dark viewer, 228 tests** |
| **NEVEN v2.0** | **May 2026** | **Reorganizacion: Core/, libreria/, Ejemplos/, Build/, neven-config.json limpio** |
| **NEVEN v2.0** | **May 2026** | **Viewer Snap Layout, =NEVEN.status(), fix SetPointers race condition, investigacion xlfRegister** |
| **NEVEN v2.0** | **May 2026** | **Zombie Process Killer, Extraer_outputs (TipoOutput universal en 11 funciones), Viewer Professional parcial (💾, PDF/TXT/DOCX, hash)** |
| **NEVEN v2.0** | **May 2026** | **Security remediation: 36/36 hallazgos cerrados, Console/Electron eliminado, ControlPython reactivado, 357 tests, score 6.0→9.4** |

------------------------------------------------------------------------

## 2. Ecosistema Tecnologico

### Motores de Lenguaje

| Motor | Version | Rol | Funciones |
|:---|:---|:---|:---|
| **R** | 4.4.1 | Estadistica, econometria, graficos | ~90 procedimientos en 9 modulos |
| **Julia** | 1.12.6 | Matematica, ML, optimizacion | ~70 procedimientos en 9 modulos + aliases |
| **Python** | 3.13 | AI/LLM integration, Quarto | Funciones AI (ai_call, ai_setup, ai_list_prompts) |
| **Quarto** | 1.9.18 | Reportes profesionales (.qmd --> HTML) | Renderizado via CreateProcess |

### Subsistemas

| Subsistema | Tecnologia | Funcion |
|:---|:---|:---|
| **WebView2** | Edge Chromium | Visualizacion interactiva (Plotly, D3.js, HTML) |
| **Pluto.jl** | Julia notebooks | Notebooks reactivos con datos de Excel |
| **Ribbon COM** | ATL/COM DLL | Pestana nativa en Excel con iconos R/Julia/Quarto |
| **PostMessage Bridge** | JS <--> C++ | Comunicacion bidireccional WebView2-Excel |
| **Viewer Snap Layout** | Win32 API | Ajuste automatico Excel (izquierda) + Viewer (derecha) via SetWindowPos + SPI_GETWORKAREA |
| **Zombie Process Killer** | Win32 CreateProcess | Mata procesos huérfanos (ControlR/Julia/Python) al inicio con taskkill /F /IM + CREATE_NO_WINDOW |
| **InputSanitizer** | C++17 allowlist | Validacion allowlist para paths de CreateProcess — solo ejecutables conocidos permitidos |
| **MessageValidator** | C++17 + Protobuf | Validacion de frames Protobuf antes de deserializacion — previene mensajes malformados |
| **CreadorPresentaciones** | Impress.js | Editor drag-and-drop de presentaciones |
| **rpivotTable** | R/htmlwidgets | Tablas pivote interactivas drag-and-drop |
| **Plotly.js** | JavaScript | Explorador de datos con selectores de ejes |
| **D3.js v7** | JavaScript | Treemap, Sankey, Sunburst, Force Graph |
| **Leaflet.js** | JavaScript | Mapas interactivos con tiles CartoDB dark |

### Comunicacion

```
Excel (XLL) <---- Named Pipe (Protobuf) ----> ControlR.exe <----> R 4.4.1
                                           ControlJulia.exe <----> Julia 1.12.6
                                           ControlPython.exe <----> Python 3.13
Excel (XLL) <---- COM automation ----> WebView2 (STA thread)
Excel (XLL) <---- COM automation ----> WebView2 REPL (REPLManager + REPLBridge)
Excel (XLL) <---- CreateProcess ----> Quarto CLI --> HTML
Excel (XLL) <---- TSV file ----> Pluto.jl (proceso separado)
```

------------------------------------------------------------------------

## 3. Catalogo de Funciones

> **Referencia completa:** El diccionario de funciones con 95 entradas documentadas (parámetros, TipoOutput, ejemplos con datos dummy) está disponible en `docs/DICCIONARIO_FUNCIONES.md` y como capítulo 11 de la documentación embebida (accesible desde el botón "Diccionario" del Ribbon).

### Julia -- Funciones con Rangos (nombres cortos)

| Funcion | Modulo | Procedimientos |
|:---|:---|:---|
| `=J.Algebra(rango,vector,tipo)` | Algebra lineal | 12: LU, QR, SVD, eigenvalores, det, rango, normas, pseudoinversa |
| `=J.Calculo(X,Y,param,tipo)` | Calculo numerico | 7: derivada, integrales, biseccion, interpolacion, Taylor |
| `=J.EDO(intervalo,CI,h,tipo)` | Ecuaciones diferenciales | 4: Euler, RK4, oscilador, 2do orden |
| `=J.Estadistica(datos,Y,tipo)` | Estadistica descriptiva | 8: descriptiva, correlacion, covarianza, t-test, normalizar, outliers |
| `=J.KNN(X,Y,K,tipo)` | Clasificacion KNN | 5: clasificacion, precision/recall/F1, confusion, prediccion, distancias |
| `=J.Regresion(X,Y,param,tipo)` | Regresion lineal | 5: coeficientes, prediccion, residuos, resumen, intervalos confianza |
| `=J.Clustering(datos,K,seed,tipo)` | K-Medias | 6: asignacion, centros, WCSS, codo, descriptivas |
| `=J.Optimizar(A,b,lr,iter,tipo)` | Optimizacion | 7: gradiente, momentum, Newton, seccion aurea, simplex, NNLS, QP |
| `=J.Transformar(datos,col,val,tipo)` | Transformacion | 6: transponer, ordenar, filtrar, seleccionar, unicos, frecuencias |
| `=J.Utilidades(p1,p2,p3,tipo)` | Utilidades | 5: fecha, secuencias, aleatorios normal/uniforme, redondeo |

### R -- Funciones Estadisticas

| Modulo | Funciones | Descripcion |
|:---|:---|:---|
| Regresion | MR_Lineal, MR_Binario, MR_Poisson, MR_Tobit, MR_PanelData, MR_SVM | Modelos supervisados |
| Analisis de Datos | AD_ACP, AD_KMedias, AD_Descriptiva, AD_Psicometria | No supervisados |
| Series de Tiempo | ST_SeriesTemporales, ST_Autoregresivos, ST_Filtro | ARIMA, GARCH, filtros |
| Graficos | GR_PlotlyView, GR_QuickPlot | 15 tipos de graficos (R base + ggplot2 + Plotly) |
| Mixtos | RG_Mixtos, RG_Supervivencia, RG_Bayesiana | Modelos avanzados |
| Pronostico | RG_Pronostico, RG_Supuestos | Prediccion y diagnostico |
| **Universal** | **Extraer_outputs(modelo)** | **Tabla completa de outputs de cualquier modelo R** |

### R -- Analisis de Datos Interactivo

| Funcion | Libreria | Tipos |
|:---|:---|:---|
| `=R.Pivot(rango, tipo)` | rpivotTable | Pivot libre, Heatmap, Barras |
| `=R.Esquisse(rango, tipo)` | Plotly.js | Scatter, Barras, Lineas, Box, Histograma, Heatmap |
| `=R.D3(rango, tipo)` | D3.js v7 | Treemap, Sankey, Sunburst, Force Graph |
| `=R.Dashboard(rango, tipo)` | rpivotTable + Plotly + D3 | 6 tabs todo-en-uno |
| `=R.Map(rango, tipo)` | Leaflet.js | Marcadores, Mapa de calor, Circulos proporcionales |

### Funciones del Sistema

| Funcion | Descripcion |
|:---|:---|
| `=NEVEN.r("codigo")` | Ejecutar codigo R arbitrario |
| `=NEVEN.j("codigo")` | Ejecutar codigo Julia arbitrario |
| `=NEVEN.p("codigo")` | Ejecutar codigo Python arbitrario |
| `=NEVEN.v(html_o_ruta)` | Abrir contenido en WebView2 |
| `=NEVEN.q("archivo.qmd")` | Renderizar documento Quarto |
| `=NEVEN.Console()` | Consola REPL interactiva (R/Julia en tabs, WebView2) |
| `=NEVEN.pluto.start/stop/status()` | Control del servidor Pluto.jl |
| `=NEVEN.pluto.data(rango,"nombre")` | Enviar datos de Excel a Julia/Pluto |
| `=NEVEN.notebook.open/list()` | Gestionar notebooks Pluto |
| `=NEVEN.about/help()` | Informacion y ayuda |
| `=NEVEN.status()` | Diagnostico: estado de conexion, salud, prefijo y conteo de funciones de cada motor |

### Python -- Funciones AI y Quarto

| Funcion | Descripcion |
|:---|:---|
| `=P.ai_call(datos, prompt)` | Enviar datos a un LLM y obtener interpretacion en lenguaje natural |
| `=P.ai_setup(provider, model, key)` | Configurar proveedor AI (OpenAI, Ollama, LM Studio) |
| `=P.ai_list_prompts()` | Listar prompts disponibles (archivos .txt editables) |
| `=P.quarto_render(archivo)` | Renderizar documento Quarto via Python |

### Documentacion para el Usuario

| Recurso | Acceso | Contenido |
|:---|:---|:---|
| Diccionario de Funciones | Boton "Diccionario" en Ribbon | 95 funciones con parametros, TipoOutput y ejemplos ejecutables |
| Documentacion (12 capitulos) | Boton "Documentacion" en Ribbon | Instalacion, arquitectura, funciones, ejemplos, mantenimiento |
| Archivos Excel de ejemplo | `libreria/EJEMPLOS/Excel/` | Libros con datos y formulas listas para probar |
| Notebooks Pluto | `libreria/EJEMPLOS/Notebooks/` | 15 notebooks interactivos (PCA, algebra, optimizacion) |

------------------------------------------------------------------------

## 4. Calidad del Software

### Evolucion de la Calificacion

| Fecha | Nota | Hito |
|:---|:---:|:---|
| 14 abril | 4.3 | Estado original -- prototipo con deuda tecnica |
| 15 abril | 6.8 | Seguridad, RAII, mutex, retry limits |
| 16 abril | 8.1 | Python, mantenibilidad, confiabilidad |
| 19 abril | 8.9 | WebView2, Plotly interactivo |
| 22 abril | 9.0 | Pluto.jl, PLUTO.DATA, toolbar |
| 23 abril | 9.1 | Quarto, notebook generico |
| **27 abril** | **9.2** | **Ribbon COM, callback thread, depuracion, KNN/Regresion** |
| **2 mayo** | **9.6** | **Rename NEVEN, 5 nuevas visualizaciones, 228 tests, Doxygen completo** |
| **3 mayo** | **9.6** | **Reorganizacion repositorio: Core/, libreria/, Build/, config limpio** |
| **Mayo 2026** | **9.4** | **Security remediation: 36/36 hallazgos cerrados, Console/Electron eliminado, ControlPython reactivado, 357 tests** |

### Dimensiones Actuales

| Dimension | Nota | Detalle |
|:---|:---:|:---|
| Funcionalidad | 10 | R + Julia + Quarto + Pluto + WebView2 + Ribbon |
| Calidad de Codigo | 9.5 | 0 std::cout en produccion, Doxygen completo |
| Seguridad | 9.5 | 36/36 audit findings resolved, InputSanitizer, MessageValidator, SafePipeHandle, MSVC flags, SHA-256 startup integrity |
| Mantenibilidad | 9.7 | Repositorio reorganizado (Core/, libreria/, Build/), Common/ con Security/ e IPC/ subdirs, config limpio, paths centralizados |
| Confiabilidad | 9.5 | CI/CD pipeline, delayed Julia reload |
| Testing | 10 | 357 tests (GTest + rapidcheck PBT), E2E + sandbox + InputSanitizer + IPC |
| Documentacion | 10 | Arquitectura, evaluacion, ejemplos, dependencias |

### Testing

| Categoria | Tests |
|:---|:---:|
| Sandbox (R + Julia + Python) | 154 |
| Property-based (rapidcheck) | 24 |
| InputSanitizer | 21 |
| Config, Security, Discovery | 16 |
| Type conversions, RAII, callbacks | 34 |
| Basic functions, COM | 35 |
| E2ETest | 8 |
| Repo Hygiene | 14 |
| IPC/Protobuf (MessageValidator) | 6 |
| Pipe Lifecycle (SafePipeHandle) | 8 |
| Build Verification | 4 |
| NewFunctionsSandboxTest | 16 |
| R Library | 1 |
| Env Lookup | 4 |
| Otros | 12 |
| **Total** | **357** |

------------------------------------------------------------------------

## 5. Comparacion con Alternativas

| Caracteristica | BERT (original) | NEVEN v2.0 | Excel + VBA | Python xlwings |
|:---|:---|:---|:---|:---|
| Lenguajes | R 3.5 | R 4.4 + Julia 1.12 | VBA | Python |
| Funciones como formulas | Si | Si | No (macros) | Parcial |
| Graficos interactivos | No | Plotly + WebView2 | No | No |
| Notebooks reactivos | No | Pluto.jl | No | Jupyter (externo) |
| Reportes profesionales | No | Quarto | No | No |
| Ribbon nativo | No | COM Add-in | Si | No |
| Sandbox de seguridad | No | 5 mecanismos + InputSanitizer + MessageValidator | No | No |
| Tests automatizados | 0 | 357 | 0 | Variable |
| Pipeline datos Excel-->ML | No | PLUTO.DATA | No | Si |
| Presentaciones | No | Impress.js editor | No | No |
| Visualizaciones D3/Leaflet | No | Treemap, Sankey, Sunburst, Force, Map | No | No |
| Snap Layout (lado a lado) | No | Excel + Viewer automatico | No | No |

------------------------------------------------------------------------

## 6. Infraestructura

### Estructura del Repositorio

```
NEVEN/
+-- Core/                      # NEVEN_Core (NEVEN.dll) -- corazon del proyecto
+-- Common/                    # Common.lib -- utilidades compartidas
|   +-- Security/              # InputSanitizer, SandboxVerifier
|   \-- IPC/                   # MessageValidator, SafePipeHandle, REPLBridge, pipe
+-- ControlR/                  # ControlR.exe -- integracion con R
+-- ControlJulia/              # ControlJulia.exe -- integracion con Julia
+-- ControlPython/             # ControlPython.exe -- integracion con Python
+-- PB/                        # PB.lib -- Protocol Buffers (variable.proto)
+-- Ribbon/                    # NEVENRibbon.dll -- COM Ribbon
+-- Addin/                     # Empaquetado XLL
+-- Include/                   # Mock headers de R, Julia, Excel SDK
+-- OfficeTypes/               # Type libraries COM pre-generadas
+-- libreria/
|   +-- R/                     # 32 archivos .R (~90 procedimientos R4XCL)
|   \-- JULIA/                 # 5 archivos .jl (~70 procedimientos J4XCL)
+-- Ejemplos/
|   +-- R/                     # Funciones R de ejemplo
|   +-- Julia/                 # Funciones Julia de ejemplo
|   +-- Quarto/                # Documentos .qmd de ejemplo
|   \-- Java/                  # Ejemplo D3.js
+-- startup/                   # Scripts de inicio R y Julia
+-- notebooks/                 # 15 notebooks Pluto precargados
+-- tests/                     # 357 tests con GTest v1.14.0 + rapidcheck PBT
+-- scripts/                   # Scripts de build y utilidades
+-- docs/                      # Documentacion completa
+-- Build/                     # Directorio de build CMake (generado)
\-- Install/                   # Scripts de instalacion
```

### Estructura en Produccion (C:\NEVEN\)

```
C:\NEVEN\
+-- NEVEN64.xll              # Add-in Excel
+-- NEVENRibbon.dll           # COM Add-in (Ribbon)
+-- ControlR.exe / ControlJulia.exe / ControlPython.exe
+-- neven_julia.dll             # Sysimage (~415 MB)
+-- neven-config.json / neven-languages.json
+-- startup\                   # Scripts inicio R y Julia
+-- notebooks\                 # 15 notebooks Pluto
+-- data\                      # Datasets compartidos Excel<-->Pluto
+-- quarto\                    # Documentos Quarto
+-- CreadorPresentaciones\     # Editor Impress.js
+-- crashes\                   # Telemetria local
\-- webview2-data\             # HTML temporales
```

### Dependencias Externas

| Componente | Version | Proposito |
|:---|:---|:---|
| R | 4.4.1+ | Motor estadistico |
| Julia | 1.12.6+ | Motor matematico/ML |
| Quarto | 1.9.18+ | Reportes (requiere junction C:\Quarto) |
| Pandoc | 3.6+ | Conversion de documentos (incluido con Quarto) |
| WebView2 Runtime | Edge | Visualizacion (preinstalado en Windows 10/11) |
| Pluto.jl | 0.20+ | Notebooks reactivos |

------------------------------------------------------------------------

## 7. Ribbon COM -- Interfaz Nativa

Pestana "NEVEN" en la cinta de Excel con 5 grupos:

| Grupo | Botones |
|:---|:---|
| **Motores** | Consola R (logo R), Consola Julia (logo Julia), Actualizar, Instalar Paquete R, Instalar Paquete Julia, Paquetes R, Paquetes Julia |
| **Visualizacion** | Abrir HTML, Presentaciones, Cerrar Visores |
| **Pluto.jl** | Iniciar Pluto, Notebooks, Detener Pluto |
| **Quarto** | Renderizar QMD (logo Quarto) |
| **Configuracion** | Carpeta Scripts, Config JSON, Acerca de |

Iconos oficiales de R, Julia y Quarto embebidos como PNG en el recurso del DLL.

------------------------------------------------------------------------

## 8. Configuracion (neven-config.json)

Archivo canonico en `Install/neven-config.json`. Solo contiene campos que el codigo C++ lee activamente:

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
    "Julia": { "home": "", "minMajor": 1, "minMinor": 6, "maxMajor": 99 }
  },
  "WebView2": { "enabled": true, "maxViewers": 8, "maxMemoryMB": 512 },
  "Pluto": { "port": 1234 }
}
```

Secciones eliminadas en la reorganizacion de mayo 2026:
- `Python` -- deprecado, el codigo no lee esta seccion
- `Quarto` -- integracion abortada, los 5 campos no se leen en ningun .cc

------------------------------------------------------------------------

## 9. Lineas Futuras

| Tema | Prioridad | Estado |
|:---|:---|:---|
| Instalador MSI/NSIS | Completado | `Install-NEVEN.exe` (78 KB) — doble clic para instalar |
| PLUTO.READ (Pluto --> Excel) | Media | Patron TSV inverso |
| Viewer reuse (actualizar sin crear nuevo) | Completado | Navigate + cache invalidation |
| CrashHandler (telemetria local) | Media | Implementado, pendiente integracion estable |
| CI/CD pipeline | Completado | GitHub Actions |
| Idioma toggle (ES/EN) en Ribbon | Baja | Infraestructura lista |
| Correccion EDO TipoOutput 2-4 | Baja | Bug de scope en Julia 1.12 |
| Viewer titulo NEVEN | Media | Requiere debugging del wstring resize |
| Viewer Snap Layout | Completado | Excel (izquierda) + Viewer (derecha) automatico con SetWindowPos |
| `=NEVEN.status()` diagnostico | Completado | Estado de conexion, salud, prefijo y funciones de cada motor |
| R.Network (grafos de red con vis.js) | Baja | Propuesta |
| Zombie Process Killer | Completado | `Init()` mata ControlR/Julia/Python huérfanos con `taskkill /F /IM` via `CreateProcess(CREATE_NO_WINDOW)` |
| Extraer_outputs (TipoOutput universal) | Completado | `Extraer_outputs(modelo)` retorna ALL outputs como data.frame. Integrado en 11 funciones R4XCL |
| Viewer Professional (parcial) | En progreso | Botón 💾, detección PDF/TXT/DOCX, hash de contenido. Auto-refresh revertido (deadlock STA) |

------------------------------------------------------------------------

*NEVEN v2.0 -- De 4.3 a 9.4. 357 tests. R + Julia + Python + D3 + Leaflet + Plotly + Snap Layout + Extraer_outputs. Security remediation: 36/36 findings resolved.*
*Repositorio reorganizado: Core/, Common/Security/, Common/IPC/, libreria/R/, libreria/JULIA/, Ejemplos/, Build/*
*Universidad de Costa Rica -- Team Vikingos -- SKAL!*
