---
id: metricas-proyecto
title: Métricas del Proyecto
sidebar_label: Métricas
sidebar_position: 20
---

# NEVEN v3.2 — Métricas del Proyecto

**Fecha de actualización:** Agosto 2026

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
| NEVENRibbon.dll | DLL (COM) | Cinta de opciones con 17 botones |
| ControlR.exe | Ejecutable | Proceso hijo R 4.4.1 |
| ControlJulia.exe | Ejecutable | Proceso hijo Julia 1.12.6 |
| ControlPython.exe | Ejecutable | Proceso hijo Python 3.13 |
| neven_julia.dll | Sysimage | Julia precompilada (~415 MB) |
| neven_http_server.py | Servidor | HTTP server para NEVEN Studio |
| rag_engine.py | Módulo | RAG Engine con DuckDB + FastEmbed |
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
| Ejecución directa | NEVEN.R, NEVEN.J, NEVEN.P | 3 | `=NEVEN.R("1+1")` |
| Funciones R | R. | ~120 | `=R.Pivot(...)`, `=R.Dashboard(...)` |
| Funciones Julia | J. | ~75 | `=J.Algebra(...)`, `=J.Optimizar(...)` |
| Funciones Python | P. | variable | `=P.MiFuncion(...)` |
| WebView2 Viewer | NEVEN.v | 4 | `=NEVEN.v(html)` |
| Pluto.jl | NEVEN.pluto | 4 | `=NEVEN.pluto.start()` |
| Quarto | NEVEN.q | 1 | `=NEVEN.q("file.qmd")` |
| **Total** | | **200+** | |

---

## 5. RAG Engine

| Métrica | Valor |
|:---|:---|
| Entidades de ontología | 300+ |
| Documentos indexados | 9 libros base |
| Chunks en índice | 3,690+ |
| Formatos soportados | 12 |
| Modelo de embeddings | bge-small-en-v1.5 |
| Traducción multilingüe | EN, ES, PT, FR |

---

## 6. Testing

| Suite | Tests | Cobertura |
|:---|---:|:---|
| Core Tests | 228 | Sandbox, Config, RAII, COM |
| NEVEN-SIM Tests | 114 | Simulación Monte Carlo |
| Property-Based Testing | 15+ | Sandbox, reliability |
| **Total** | **342** | **342 pass** |

---

## 7. Calificación de Calidad

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

## 8. Evolución del Proyecto

| Versión | Fecha | Hito |
|:---|:---|:---|
| R4XCL | 2023 | R en Excel via BERT |
| RJ2XCL v1.0 | Enero 2026 | Fork de BERT |
| NEVEN v2.0 | Mayo 2026 | WebView2, Pluto, Quarto |
| NEVEN v3.0 | Julio 2026 | NEVEN Studio, DuckDB |
| NEVEN v3.1 | Julio 2026 | RAG Engine, Chat IA |
| **NEVEN v3.2** | **Agosto 2026** | **342 tests, instalador automatizado** |

---

*NEVEN v3.2 — BukloLAB*
