# NEVEN v2.0 -- Metricas del Proyecto

**Fecha de generacion:** 3 de mayo de 2026
**Universidad de Costa Rica -- Tesis de Maestria**

------------------------------------------------------------------------

## 1. Lineas de Codigo

| Lenguaje | Archivos | Lineas | Porcentaje |
|:---|---:|---:|---:|
| C++ source (.cc/.cpp) | 561 | 368,078 | 56.3% |
| C++ headers (.h) | 448 | 215,114 | 32.9% |
| JavaScript / TypeScript | 319 | 23,865 | 3.7% |
| R (.R/.r) | 55 | 10,800 | 1.7% |
| Julia (.jl) | 33 | 4,202 | 0.6% |
| **Codigo total** | **1,416** | **622,059** | **95.1%** |
| Documentacion (.md) | 120 | 33,500 | 4.9% |
| **Gran total** | **1,536** | **655,559** | **100%** |

------------------------------------------------------------------------

## 2. Componentes del Sistema

| Componente | Tipo | Descripcion |
|:---|:---|:---|
| NEVEN64.xll | DLL (XLL) | Add-in principal de Excel |
| NEVENRibbon.dll | DLL (COM) | Cinta de opciones con 17 botones + logo NEVEN |
| ControlR.exe | Ejecutable | Proceso hijo R 4.4.1 |
| ControlJulia.exe | Ejecutable | Proceso hijo Julia 1.12.6 |
| ControlPython.exe | Ejecutable | Proceso hijo Python 3.13 |
| neven_julia.dll | Sysimage | Julia precompilada (~415 MB) |
| Common (lib) | Biblioteca estatica | 25+ servicios compartidos |
| PB (lib) | Biblioteca estatica | Protocol Buffers v21.12 |

------------------------------------------------------------------------

## 3. Funciones Disponibles en Excel

| Categoria | Prefijo | Cantidad | Ejemplos |
|:---|:---|---:|:---|
| Ejecucion directa | NEVEN.R, NEVEN.J, NEVEN.P | 3 | `=NEVEN.R("1+1")`, `=NEVEN.J("sqrt(144)")`, `=NEVEN.P("1+1")` |
| Funciones R registradas | R. | ~95 | `=R.Pivot(...)`, `=R.D3(...)`, `=R.Dashboard(...)` |
| Funciones Julia registradas | J. | ~75 | `=J.Algebra(...)`, `=J.Calculo(...)` |
| Funciones Python registradas | P. | variable | `=P.MiFuncion(...)` (funciones de usuario) |
| WebView2 Viewer | NEVEN.v | 4 | `=NEVEN.v(html)`, `=NEVEN.v.list()` |
| Pluto.jl | NEVEN.pluto | 4 | `=NEVEN.pluto.start()`, `=NEVEN.pluto.data(...)` |
| Notebooks | NEVEN.notebook | 3 | `=NEVEN.notebook.open(...)` |
| Quarto | NEVEN.q | 1 | `=NEVEN.q("file.qmd")` |
| Presentaciones | NEVEN.presentation | 3 | `=NEVEN.presentation.new(...)` |
| Informacion | NEVEN | 4 | `=NEVEN.about()`, `=NEVEN.help()` |
| **Total aproximado** | | **~200+** | |

------------------------------------------------------------------------

## 4. Visualizaciones Interactivas

| Funcion | Libreria | Tipos de grafico |
|:---|:---|:---|
| R.Pivot | rpivotTable | Tabla pivote drag-and-drop, Heatmap, Barras |
| R.Esquisse | Plotly.js | Scatter, Barras, Lineas, Box Plot, Histograma, Heatmap |
| R.D3 | D3.js v7 | Treemap, Sankey, Sunburst, Force Graph |
| R.Dashboard | rpivotTable + Plotly + D3 | 6 tabs: Pivot, Explorador, Treemap, Sankey, Sunburst, Force |
| R.Map | Leaflet.js | Marcadores, Mapa de calor, Circulos proporcionales |
| R.GR_PlotlyView | Plotly (R) | Lineas, Barras, Scatter, Area, Combinado |
| R.GR_QuickPlot | R base + ggplot2 | 9 tipos (6 base + 3 ggplot2/Plotly) |

------------------------------------------------------------------------

## 5. Testing

| Suite | Tests | Cobertura |
|:---|---:|:---|
| SandboxTest (R + Julia + Python) | 109 | Patrones bloqueados, bypass prevention |
| NewFunctionsSandboxTest | 16 | Pivot, D3, Esquisse, Map sandbox validation |
| E2ETest | 8 | Rename verification, config keys, version |
| Property-Based Testing | 8 | Sandbox, reliability, WebView2 |
| Config, Security, RAII | 35 | Getters, SHA-256, memory management |
| Reliability (unit + PBT) | 35 | Timeout, health status, error messages |
| Integration, COM, Discovery | 17 | Pipe lifecycle, COM objects, auto-discovery |
| Python Reactivation (exploration) | 7 | Bug condition verification, fix validation |
| Python Reactivation (preservation) | 9 | R/Julia behavior unchanged, config parsing |
| Python Sandbox PBT | 3 | Property-based sandbox testing (450 iteraciones) |
| **Total** | **247** | **245 pass, 2 root-cause demos** |

Archivos de test: 22 (.cc)

------------------------------------------------------------------------

## 6. Seguridad

| Mecanismo | Patrones | Lenguajes |
|:---|---:|:---|
| SandboxVerifier | 30+ por lenguaje | R, Julia, Python |
| Bypass detection | Whitespace strip, paste(), getattr() | R, Julia, Python |
| Config validation | Path traversal, injection | JSON |
| SecurityService | SHA-256 integridad | Scripts criticos |
| SHA-256 startup verification | startup.r, startup.jl, startup.py | R, Julia, Python |
| WebView2 navigation filter | CDN whitelist | HTML/JS |

------------------------------------------------------------------------

## 7. Documentacion

| Documento | Lineas | Descripcion |
|:---|---:|:---|
| Docusaurus (11 capitulos) | ~8,000 | Documentacion completa con LaTeX |
| EJEMPLOS_USUARIO.md | ~650 | 90+ ejemplos con datos (Pivot, D3, Map, Dashboard) |
| EVALUACION_OBJETIVA.md | ~1,500 | Auditoria de calidad |
| METRICAS_PROYECTO.md | ~200 | Este documento |
| arquitectura.md | ~400 | Arquitectura de 4 capas |
| explicacion.md | ~300 | Guia tecnica |
| Otros docs | ~22,400 | Manuales, estado del arte, etc. |
| **Total documentacion** | **~33,500** | **120 archivos .md** |

------------------------------------------------------------------------

## 8. Infraestructura

| Elemento | Detalle |
|:---|:---|
| Build system | CMake 3.15+ |
| CI/CD | GitHub Actions (build + test en cada push) |
| Compilador | MSVC 2022 (C++17) |
| IPC | Protocol Buffers v21.12 sobre Named Pipes |
| Viewer | WebView2 (Edge Chromium) con tema dark (#2D2D2D) |
| Ribbon | COM Add-in con iconos PNG (R, Julia, Quarto, NEVEN) |
| Sysimage | PackageCompiler.jl (~415 MB, arranque en 1-2s) |
| Deploy | C:\NEVEN\ |
| Log | neven.log (structured logging, CHILD_LOG en procesos hijo) |
| Doxygen | 100% clases publicas + funciones exportadas documentadas |

------------------------------------------------------------------------

## 9. Calificacion de Calidad

| Dimension | Nota |
|:---|---:|
| Funcionalidad | 10/10 |
| Calidad de Codigo | 9.5/10 |
| Seguridad | 9.5/10 |
| Mantenibilidad | 9.7/10 |
| Confiabilidad | 9.5/10 |
| Testing | 10/10 |
| Documentacion | 10/10 |
| **Promedio** | **9.6/10** |

------------------------------------------------------------------------

## 10. Evolucion del Proyecto

| Version | Fecha | Hito |
|:---|:---|:---|
| R4XCL | 2023 | R en Excel via BERT (tesis original) |
| RJ2XCL v1.0 | Enero 2026 | Fork de BERT, R 4.4.1 + Julia 1.12.6 |
| RJ2XCL v2.0 | Abril 2026 | WebView2, Pluto.jl, Quarto, Ribbon COM |
| **NEVEN v2.0** | **Mayo 2026** | **Rename, R.Pivot, R.Esquisse, R.D3, R.Dashboard, R.Map** |
| **NEVEN v2.0** | **Mayo 2026** | **Python reactivado, repositorio reorganizado (Core/, Build/, libreria/)** |

### Logros de la sesion NEVEN (Mayo 2026)

- Rename completo RJ2XCL --> NEVEN (70+ archivos)
- 5 nuevas funciones de visualizacion (Pivot, Esquisse, D3, Dashboard, Map)
- **Python reactivado como tercer lenguaje** (7 bugs corregidos: startup retry, stack guard, single-block startup, health check, NEVEN_HOME, config paths, prefix)
- **Repositorio reorganizado**: RJ2XCL/ → Core/, build_new/ → Build/, docs/LIBRERIA/ → libreria/R/ + libreria/JULIA/, Examples/ → Ejemplos/
- **neven-config.json limpiado**: Python y WebView2/Pluto sections agregadas, Quarto (abortado) removido
- **Julia y Python opcionales**: campo `"enabled": true/false` en config
- WebView2 dark mode (grafito #2D2D2D)
- Logo NEVEN en Ribbon
- Julia sysimage con delayed reload (15s timer)
- SHA-256 integrity para startup scripts
- Doxygen completo en funciones exportadas
- std::cout eliminados de ControlR y ControlJulia
- CI/CD actualizado para NEVEN
- 247 tests (245 pass + 2 root-cause demos)
- De 228 a 247 tests (+19 nuevos: Python reactivation exploration + preservation)

------------------------------------------------------------------------

*NEVEN v2.0 -- Universidad de Costa Rica -- Tesis de Maestria*
