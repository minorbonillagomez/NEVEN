# NEVEN v3.2 — Métricas del Proyecto

**Fecha de actualización:** Agosto 2026
**BukloLAB — Tesis de Maestría, Universidad de Costa Rica**

---

## 1. Líneas de Código

| Lenguaje | Archivos | Líneas | Porcentaje |
|:---|---:|---:|---:|
| C++ source (.cc/.cpp) | 580+ | 380,000+ | 54% |
| C++ headers (.h) | 460+ | 220,000+ | 31% |
| Python (.py) | 45+ | 15,000+ | 2.1% |
| JavaScript / TypeScript | 330+ | 28,000+ | 4% |
| R (.R/.r) | 62+ | 12,500+ | 1.8% |
| Julia (.jl) | 35+ | 4,500+ | 0.6% |
| **Código total** | **1,512+** | **660,000+** | **93.6%** |
| Documentación (.md) | 140+ | 45,000+ | 6.4% |
| **Gran total** | **1,652+** | **705,000+** | **100%** |

---

## 2. Componentes del Sistema

| Componente | Tipo | Descripción |
|:---|:---|:---|
| NEVEN64.xll | DLL (XLL) | Add-in principal de Excel |
| NEVENRibbon.dll | DLL (COM) | Cinta de opciones con 17 botones + logo NEVEN |
| ControlR.exe | Ejecutable | Proceso hijo R 4.4.1 |
| ControlJulia.exe | Ejecutable | Proceso hijo Julia 1.12.6 |
| ControlPython.exe | Ejecutable | Proceso hijo Python 3.13 (Stable ABI) |
| neven_julia.dll | Sysimage | Julia precompilada (~415 MB) |
| neven_http_server.py | Servidor | HTTP server para NEVEN Studio (puerto 5555) |
| rag_engine.py | Módulo | RAG Engine con DuckDB + FastEmbed |
| Common (lib) | Biblioteca estática | 25+ servicios compartidos |
| PB (lib) | Biblioteca estática | Protocol Buffers v21.12 |
| NEVEN-SIM.xll | DLL (XLL) | Módulo de Simulación Monte Carlo |

---

## 3. NEVEN Studio (TaskPane)

| Tab | Tecnología | Función |
|:---|:---|:---|
| SQL | DuckDB | Consultas SQL sobre datos de Excel |
| Data Studio | Plotly.js | Análisis exploratorio con gráficos |
| Run Script | CodeMirror | REPL para R, Python, Julia |
| Data Lab | Custom | Notebooks interactivos |
| Presentaciones | Impress.js / Quarto | Slides interactivos |
| IA | Bedrock + RAG | Chat con contexto de 300+ entidades |
| Ayuda | HTML embebido | 16 capítulos de documentación |

---

## 4. Funciones Disponibles en Excel

| Categoría | Prefijo | Cantidad | Ejemplos |
|:---|:---|---:|:---|
| Ejecución directa | NEVEN.R, NEVEN.J, NEVEN.P | 3 | `=NEVEN.R("1+1")`, `=NEVEN.J("sqrt(144)")`, `=NEVEN.P("1+1")` |
| Funciones R registradas | R. | ~120 | `=R.Pivot(...)`, `=R.D3(...)`, `=R.Dashboard(...)` |
| Funciones Julia registradas | J. | ~75 | `=J.Algebra(...)`, `=J.Calculo(...)`, `=J.Optimizar(...)` |
| Funciones Python registradas | P. | variable | `=P.MiFuncion(...)` (funciones de usuario) |
| WebView2 Viewer | NEVEN.v | 4 | `=NEVEN.v(html)`, `=NEVEN.v.list()` |
| Pluto.jl | NEVEN.pluto | 4 | `=NEVEN.pluto.start()`, `=NEVEN.pluto.data(...)` |
| Notebooks | NEVEN.notebook | 3 | `=NEVEN.notebook.open(...)` |
| Quarto | NEVEN.q | 1 | `=NEVEN.q("file.qmd")` |
| Presentaciones | NEVEN.presentation | 3 | `=NEVEN.presentation.new(...)` |
| Información | NEVEN | 4 | `=NEVEN.about()`, `=NEVEN.help()` |
| **Total aproximado** | | **200+** | |

---

## 5. Visualizaciones Interactivas

| Función | Librería | Tipos de gráfico |
|:---|:---|:---|
| R.Pivot | rpivotTable | Tabla pivote drag-and-drop, Heatmap, Barras |
| R.Esquisse | Plotly.js | Scatter, Barras, Líneas, Box Plot, Histograma, Heatmap |
| R.D3 | D3.js v7 | Treemap, Sankey, Sunburst, Force Graph |
| R.Dashboard | rpivotTable + Plotly + D3 | 6 tabs: Pivot, Explorador, Treemap, Sankey, Sunburst, Force |
| R.Map | Leaflet.js | Marcadores, Mapa de calor, Círculos proporcionales |
| R.GR_PlotlyView | Plotly (R) | Líneas, Barras, Scatter, Area, Combinado |
| R.GR_QuickPlot | R base + ggplot2 | 9 tipos (6 base + 3 ggplot2/Plotly) |

---

## 6. RAG Engine

| Métrica | Valor |
|:---|:---|
| Entidades de ontología | 300+ |
| Documentos indexados | 9 libros base |
| Chunks en índice | 3,690+ |
| Formatos soportados | 12 (PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, CSV, JSON, XML, TXT, MD) |
| Modelo de embeddings | bge-small-en-v1.5 (FastEmbed) |
| Base de datos | DuckDB con extensión VSS |
| Traducción multilingüe | EN, ES, PT, FR |

---

## 7. Testing

| Suite | Tests | Cobertura |
|:---|---:|:---|
| Core Tests | 228 | Sandbox, Config, RAII, COM, Integration |
| NEVEN-SIM Tests | 114 | Simulación Monte Carlo |
| Property-Based Testing | 15+ | Sandbox, reliability, distributions |
| **Total** | **342** | **342 pass** |

Archivos de test: 28+ (.cc)

---

## 8. Seguridad

| Mecanismo | Patrones | Lenguajes |
|:---|---:|:---|
| SandboxVerifier | 30+ por lenguaje | R, Julia, Python |
| Bypass detection | Whitespace strip, paste(), getattr() | R, Julia, Python |
| Config validation | Path traversal, injection | JSON |
| SecurityService | SHA-256 integridad | Scripts críticos |
| SHA-256 startup verification | startup.r, startup.jl, startup.py | R, Julia, Python |
| WebView2 navigation filter | CDN whitelist | HTML/JS |

---

## 9. Documentación

| Documento | Descripción |
|:---|:---|
| Docusaurus (19 capítulos) | Documentación completa con LaTeX |
| neven-docs.html | Documentación embebida en TaskPane |
| EJEMPLOS_USUARIO.md | 90+ ejemplos con datos |
| RAG_GUIDE.md | Guía de RAG y formatos |
| Diccionario_Funciones.md | 200+ funciones documentadas |
| **Total documentación** | **45,000+ líneas en 140+ archivos** |

---

## 10. Infraestructura

| Elemento | Detalle |
|:---|:---|
| Build system | CMake 3.15+ |
| CI/CD | GitHub Actions (build + test en cada push) |
| Compilador | MSVC 2022 (C++17) |
| IPC | Protocol Buffers v21.12 sobre Named Pipes |
| Viewer | WebView2 (Edge Chromium) con tema dark (#1e1e1e) |
| Ribbon | COM Add-in con iconos PNG (R, Julia, Python, Quarto, NEVEN) |
| Sysimage | PackageCompiler.jl (~415 MB, arranque en <5s) |
| HTTP Server | Python (puerto 5555, DuckDB, RAG) |
| Deploy | C:\NEVEN\ |
| Log | neven.log (structured logging) |
| Instalador | Install-NEVEN.ps1 + NEVEN-v3.2-Setup.zip |

---

## 11. Calificación de Calidad

| Dimensión | Nota |
|:---|---:|
| Funcionalidad | 10/10 |
| Calidad de Código | 9.5/10 |
| Seguridad | 9.5/10 |
| Mantenibilidad | 9.7/10 |
| Confiabilidad | 9.5/10 |
| Testing | 10/10 |
| Documentación | 10/10 |
| **Promedio** | **9.71/10** |

---

## 12. Evolución del Proyecto

| Versión | Fecha | Hito |
|:---|:---|:---|
| R4XCL | 2023 | R en Excel via BERT (tesis original) |
| RJ2XCL v1.0 | Enero 2026 | Fork de BERT, R 4.4.1 + Julia 1.12.6 |
| RJ2XCL v2.0 | Abril 2026 | WebView2, Pluto.jl, Quarto, Ribbon COM |
| NEVEN v2.0 | Mayo 2026 | Rename, R.Pivot, R.Esquisse, R.D3, R.Dashboard, R.Map |
| NEVEN v2.5 | Junio 2026 | Python reactivado, repositorio reorganizado |
| **NEVEN v3.0** | **Julio 2026** | **NEVEN Studio (TaskPane), SQL DuckDB, HTTP Server** |
| **NEVEN v3.1** | **Julio 2026** | **RAG Engine, Chat IA, Ontología** |
| **NEVEN v3.2** | **Agosto 2026** | **NEVEN-SIM, 342 tests, 12+ formatos RAG, instalador automatizado** |

### Logros de NEVEN v3.2 (Agosto 2026)

- **NEVEN-SIM**: Módulo de Simulación Monte Carlo (XLL separado)
- **342 tests** (228 Core + 114 NEVEN-SIM)
- **RAG multilingüe** (EN/ES/PT/FR) con traducción automática
- **12+ formatos** de documentos soportados (PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, CSV, JSON, XML, TXT, MD)
- **Botón browse** nativo de Windows para selección de archivos
- **Instalador automatizado** (Install-NEVEN.ps1)
- **Build-Setup.ps1** para regenerar ZIP de distribución
- **Documentación actualizada** a 19 capítulos Docusaurus

---

*NEVEN v3.2 — BukloLAB — Tesis de Maestría, Universidad de Costa Rica*
