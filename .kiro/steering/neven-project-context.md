# NEVEN — Contexto del Proyecto para Kiro

## Qué es NEVEN

NEVEN es un add-in XLL de C++17 para Microsoft Excel que integra R 4.4.1 y Julia 1.12.6 como motores de scripting embebidos. Permite ejecutar funciones estadísticas, modelos de ML y visualizaciones interactivas desde celdas de Excel. Es una tesis de maestría de Minor Bonilla Gómez en la Universidad de Costa Rica.

## Arquitectura

- **NEVEN64.xll** (= NEVEN.dll): Add-in principal cargado por Excel. Singleton `RJ2XCL_Engine`.
- **ControlR.exe**: Proceso hijo que embebe R via C API. Comunicación por Named Pipes + Protobuf.
- **ControlJulia.exe**: Proceso hijo que embebe Julia. Misma arquitectura de pipes.
- **NEVENRibbon.dll**: COM Add-in separado para la pestaña nativa en Excel.
- **WebView2**: Visor HTML embebido (Edge Chromium) en STA thread dedicado.
- **Pluto.jl**: Notebooks reactivos con pipeline de datos Excel→Julia→Pluto via TSV.
- **Quarto**: Renderizado de .qmd via CreateProcess externo.

## Estructura del repositorio

- `Core/` → NEVEN_Core (NEVEN.dll) — corazón del proyecto
- `ControlR/` → ControlR.exe — integración con R
- `ControlJulia/` → ControlJulia.exe — integración con Julia
- `ControlPython/` → ControlPython.exe — integración con Python (Stable ABI)
- `Common/` → Common.lib — utilidades compartidas (pipes, config, security, viewers, PostMessageBridge)
- `PB/` → PB.lib — Protocol Buffers (variable.proto)
- `NEVEN-SIM/` → NEVEN-SIM.xll — Módulo de Simulación Monte Carlo (XLL separado)
- `Ribbon/` → NEVENRibbon.dll — COM Ribbon
- `Addin/` → empaquetado XLL
- `OfficeTypes/` → type libraries COM pre-generadas
- `Include/` → mock headers de R, Julia, Excel SDK
- `tests/` → 342 tests con GTest v1.14.0
- `startup/` → scripts de inicio R, Julia y Python
- `libreria/R/` → funciones R de la librería R4XCL (~90 procedimientos, 32 archivos .R)
- `libreria/JULIA/` → funciones Julia (functions.jl + 4 módulos J4XCL)
- `Ejemplos/` → ejemplos organizados por lenguaje (R, Julia, Python, Quarto, Java)
- `docs/` → documentación completa del proyecto

## Tecnologías clave

- C++17, MSVC, Visual Studio 2022, CMake 3.15+
- Protocol Buffers v21.12 (FetchContent)
- Google Test v1.14.0
- WebView2 SDK
- Named Pipes de Windows para IPC
- COM automation para Excel
- R 4.4.1, Julia 1.12.6, Quarto 1.9.18

## Convenciones de código

- Clases: `PascalCase` (ej: `LanguageManager`)
- Funciones: `snake_case` (ej: `register_functions()`)
- Miembros: `snake_case_` (ej: `next_id_`)
- Constantes: `SCREAMING_SNAKE_CASE`
- Archivos: `.cc` para implementación, `.h` para headers
- Comentarios: Doxygen en headers

## Documentación de referencia

La documentación completa está en `NEVEN/docs/`:
- `contexto v1.md` — contexto consolidado del proyecto entero
- `arquitectura.md` — arquitectura 4 capas
- `ESTADO_DE_LAS_COSAS.md` — historia y hitos
- `ESTADO_DEL_ARTE.md` — catálogo de funciones
- `MANUAL_MANTENIMIENTO.md` — build, deploy, troubleshoot
- `TROUBLESHOOTING.md` — solución de problemas
- `coding-standards.md` — convenciones

## Notas importantes

- Los prefijos internos C++ siguen siendo `RJ_` y `RJ2XCL` por compatibilidad ABI
- Los nombres visibles al usuario usan `NEVEN` (ej: `=NEVEN.r()`, `neven-config.json`)
- Python está completamente integrado (ON por defecto) — usa Stable ABI (python3.dll)
- **NEVEN-SIM** es un XLL separado para simulación Monte Carlo (BUILD_NEVEN_SIM=ON)
- La sysimage de Julia (`neven_julia.dll`, ~415MB) elimina el cold start de minutos
- El directorio de producción es `C:\NEVEN\`
- Los tests corren sin Excel, R ni Julia gracias a mock headers y MockExcelBridge

## Regla de trabajo — Ontología del proyecto (OBLIGATORIA antes de proponer cambios)

**Antes de proponer o implementar cualquier cambio, consultar la ontología del proyecto.**

La ontología es la base conceptual del proyecto. Documenta para cada componente:
- Invariantes técnicas que NUNCA deben violarse
- Dependencias entre componentes
- Cómo se despliega correctamente
- Señales de error conocidas y sus causas

### Ubicación — Espacio de Ontologías

```
F:\ANTIGRAVITY\2026\NEVEN\NEVEN\docs\ontologia\
├── README.md                      — Índice de ontologías
├── neven-core/                    — Ontología de arquitectura del proyecto
│   ├── neven-ontology-p1.yaml       (Core, Ribbon, ControlR, Common, startup.r)
│   ├── neven-ontology-p2.yaml       (NevenX dispatcher, Studio backend, sidecars, libreria R)
│   ├── neven-ontology-p3.yaml       (ControlJulia, AgentService, TaskPane frontend)
│   └── neven-ontology-p4.yaml       (Build/CMake, tests, instalador, CreadorPresentaciones)
│
├── econometrics/                  — Ontología econométrica (grafo de conocimiento)
│   ├── schema.yaml                  (tipos y relaciones)
│   ├── graph.jsonl                  (598 nodos — Wooldridge, inferencia causal)
│   ├── graph_aer_update.jsonl       (extensión AER)
│   ├── graph_ts_update.jsonl        (extensión series de tiempo)
│   └── graph_visualization*.html    (visualizaciones interactivas)
│
└── excel-functions/               — Ontología de funciones de Microsoft Excel
    └── excel-functions-ontology.yaml   (523 funciones, 14 categorías)
```

**Fuente original econometrics:** `F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS\memory\ontology\`

### Cuándo consultar la ontología

| Tipo de cambio | Consultar |
|----------------|-----------|
| Modificar ribbon_connect.h o ribbon_ui.xml | P1 (ribbon_dll) — INV-RIBBON-01/02/03 |
| Desplegar archivos .R a C:\NEVEN\ | P1 (startup_r) — INV-SR-01/02/05 |
| Modificar R4XCL-0-NevenX.R | P2 (dispatcher_nevenx) — INV-NX-01/02 |
| Modificar neven_http_server.py | P2 (studio_backend) — INV-SB-01..05 |
| Crear o modificar sidecar JSON | P2 (sidecars_json) — INV-SJ-01..05 |
| Agregar o modificar funcion .R en libreria | P2 (libreria_r) — INV-LR-01..04 |
| Construir sysimage Julia | P3 (controljulia_exe) — INV-CJ-01/02 |
| Modificar datalab.js o taskpane.html | P3 (taskpane_frontend) — INV-TF-01..04 |
| Modificar CMakeLists.txt | P4 (build_cmake) — INV-BLD-01..04 |
| Commitear archivos en Install/ | P4 (install_scripts) — INV-INS-01 (NO credenciales) |

### Regla de validación antes de ejecutar

El hook `.kiro/hooks/validate-before-run.ps1` ejecuta verificaciones automáticas
basadas en la ontología antes de operaciones de alto riesgo. Si el hook pide
confirmación, revisar el análisis técnico antes de aprobar.

### Principio general

Un cambio que viola una invariante de la ontología NO debe implementarse
aunque sea técnicamente posible. La ontología refleja decisiones de arquitectura
tomadas con razón — si una invariante debe cambiarse, primero actualizar
la ontología y justificar el cambio.

## Regla de trabajo — Reutilización de componentes (PRIORITARIA)

**Antes de escribir código nuevo, SIEMPRE buscar si el componente ya existe en el proyecto.**

Esta regla aplica a todo: funciones JS, endpoints Python, parsers, renderers, estilos CSS.

### Componentes reutilizables de NEVEN Studio (taskpane)

| Componente | Ubicación | Reutilizar cuando... |
|-----------|-----------|----------------------|
| `buildSlotElement(slot)` | `datalab.js` | Renderizar cualquier resultado tipificado (html, table, scalar, vector, plotly) |
| `renderSlotTable(rows, name)` | `datalab.js` | Mostrar tablas de datos con paginación y descarga CSV |
| `_renderPlotlyJSON(jsonStr, name)` | `datalab.js` | Renderizar gráficos Plotly con botones PNG/SVG/Enviar a Slide |
| `_parse_slots_from_variable(raw)` | `datalab_handler.py` | Deserializar respuestas de ControlR (flatten row-major) |
| `_build_r_script(...)` | `datalab_handler.py` | Construir scripts R con source(), rm(), assign() al env NEVEN |
| `load_data(cols, types, rows)` | `neven_http_server.py` | Cargar datos en DuckDB |
| `_loadFromContent(name, content)` | `taskpane.html` | Cargar CSV/TSV/JSON del browser en DuckDB |
| `_addSendToSlideBtn(el, title, fn)` | `taskpane.html` | Agregar botón "Enviar a Slide" a cualquier resultado |
| `showToast(text)` | `taskpane.html` | Mostrar notificación temporal sin cambiar de tab |
| `_renderRecentFiles()` | `taskpane.html` | Mostrar lista de archivos recientes |

### Principio DRY aplicado a NEVEN

1. **Un solo renderer de resultados** — `buildSlotElement` es la fuente de verdad para mostrar cualquier output de R/Python/Julia. Run Script, DataLab, y cualquier futuro módulo lo usan.
2. **Un solo parser de ControlR** — `_parse_slots_from_variable` en `datalab_handler.py`. No reimplementar en otro lado.
3. **Un solo sistema de tipos** — `{name, label, type, value, tier}`. Todo output se convierte a este formato.
4. **Copiar archivos siempre con** `[System.IO.File]::Copy()` — nunca `Copy-Item` (corrompe UTF-8).

## Regla de trabajo — Bitácora de sesión (OBLIGATORIA)

**El archivo `.kiro/contexto/CHAT.md` es la memoria persistente del proyecto.**

### Cuándo actualizar CHAT.md

- **Cada hora** durante sesiones de trabajo activas
- **Al completar cualquier hito** — fix, feature, decisión arquitectural
- **Antes de cerrar sesión** — resumen del día + pendientes
- **Al inicio de sesión** — revisar CHAT.md antes de empezar para retomar el contexto

### Qué documentar en CHAT.md

- El problema diagnosticado y su causa raíz (no solo el síntoma)
- El fix aplicado con suficiente detalle para reproducirlo
- Los archivos modificados y sus rutas en producción
- Decisiones de diseño y por qué se tomaron
- Intentos fallidos y por qué fallaron (evita repetir el mismo error)
- Pendientes concretos para la próxima sesión

### Por qué es crítico

NEVEN es un proyecto complejo con muchas capas (C++, Python, R, Julia, JavaScript). Sin la bitácora, cada sesión empieza desde cero. Con ella, cualquier punto anterior es recuperable en segundos sin depender del historial del chat activo, que tiene límites de contexto.

**Ubicación:** `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md`
