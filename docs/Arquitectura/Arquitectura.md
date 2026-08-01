# Arquitectura del Proyecto NEVEN v2.0

**Fecha de actualización:** Junio 2026

Este documento describe la arquitectura modular del sistema NEVEN tras la implementación completa de WebView2, Pluto.jl, Quarto y el pipeline de datos Excel<-->Julia.

------------------------------------------------------------------------

## Resumen de la Arquitectura

NEVEN es un add-in XLL para Microsoft Excel que integra R, Julia, WebView2, Pluto.jl y Quarto en un ecosistema unificado. La arquitectura se organiza en 4 capas.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA 1: Interface Excel (XLL)                    │
│  RJ2XCL_Engine · basic_functions · MenuService · function_descriptor│
├─────────────────────────────────────────────────────────────────────┤
│                 CAPA 2: Servicios del Núcleo                        │
│  ConfigService · LanguageManager · LanguageService · SecurityService│
│  SandboxVerifier · DiscoveryService · LogService                    │
├─────────────────────────────────────────────────────────────────────┤
│              CAPA 3: Subsistemas Especializados                     │
│  ViewerManager · ViewerWindow · PlutoManager · ContentPipeline      │
│  PostMessageBridge · NotebookLibrary · NotebookExporter             │
│  PresentationBuilder · MenuService                                  │
├─────────────────────────────────────────────────────────────────────┤
│              CAPA 4: Herramientas Comunes                           │
│  Pipe · WindowManager · EnvService · child_process_log              │
│  string_utilities · type_conversions · module_functions · json11    │
└─────────────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

## Capa 1: Interface Excel (XLL)

Encargada de la interacción con Excel: registro de funciones, despacho de llamadas, toolbar y ciclo de vida del add-in.

| Componente | Archivo | Responsabilidad |
|:---|:---|:---|
| **RJ2XCL_Engine** | `NEVEN.cc/h` | Singleton principal. Init/Close, registro de funciones, callbacks |
| **basic_functions** | `basic_functions.cc/h` | ~125 funciones Excel exportadas (R, Julia, VIEW, PLUTO, QUARTO, etc.) |
| **MenuService** | `MenuService.cc/h` | Toolbar CommandBar con 6 botones en pestaña Complementos |
| **function_descriptor** | `function_descriptor.h` | Descriptores de funciones para xlfRegister |

### Funciones Excel registradas

| Categoría | Prefijo | Ejemplos | Tipo |
|:---|:---|:---|:---|
| Ejecución directa | `NEVEN.r()`, `NEVEN.j()` | Código R/Julia arbitrario | Worksheet (1) |
| Funciones R | `R.` | `R.MR_Lineal()`, `R.GR_PlotlyView()` | Worksheet (1) |
| Funciones Julia | `J.` | `J.JM_Algebra()`, `J.JM_Optimizacion()` | Worksheet (1) |
| WebView2 | `NEVEN.v()` | HTML, archivos, URLs | Worksheet (1) |
| Pluto.jl | `NEVEN.PLUTO.*` | START, STOP, STATUS, DATA | Worksheet (1) |
| Quarto | `NEVEN.q()` | Renderiza .qmd --> HTML --> WebView2 | Worksheet (1) |
| Notebooks | `NEVEN.NOTEBOOK.*` | OPEN, LIST, EXPORT | Worksheet (1) |
| Toolbar commands | `NEVEN.cmd.*` | EDITOR, PLUTO.START/STOP | Command (2) |
| Diálogos | `NEVEN.*.DIALOG` | VIEW.DIALOG, ABOUT.DIALOG | Command (2) |

------------------------------------------------------------------------

## Capa 2: Servicios del Núcleo

Servicios singleton que encapsulan la lógica de negocio.

| Servicio | Responsabilidad |
|:---|:---|
| **ConfigService** | Carga `neven-config.json`, valida paths, getters tipados con clamping |
| **LanguageManager** | Orquesta servicios de lenguaje (R, Julia). Carga `neven-languages.json` |
| **LanguageService** | Gestiona un proceso hijo (ControlR/ControlJulia): pipe, health, reconnect |
| **SecurityService** | Verificación de integridad SHA-256 de archivos críticos |
| **SandboxVerifier** | Valida código antes de ejecución: 30+ patrones bloqueados por lenguaje |
| **DiscoveryService** | Detecta instalaciones de R, Julia en el sistema (registry, env, filesystem) |
| **REPLManager** | Consola REPL interactiva en WebView2 (reemplaza Console/Electron) |
| **REPLBridge** | Dispatch de código REPL con sandbox enforcement |
| **InputSanitizer** | Allowlist validation para paths de CreateProcess |
| **MessageValidator** | Validación de frames Protobuf antes de deserialización |
| **SafePipeHandle** | RAII wrapper con CRITICAL_SECTION para operaciones atómicas |
| **LogService** | Logging estructurado a archivo con niveles INFO/WARN/ERROR |

### Comunicación con procesos hijo

```
Excel (XLL)  <--──Named Pipe (Protobuf)──-->  ControlR.exe      <---->  R 4.4.1
                                           ControlJulia.exe   <---->  Julia 1.12.6
                                           ControlPython.exe  <---->  Python 3.13
```

- Protocolo: Protocol Buffers (`variable.proto`)
- Pipe: Named Pipe bidireccional por lenguaje
- Health monitoring: `HealthStatus` enum (Healthy/Unavailable/Unknown)
- Timeouts: per-language configurable (default 30s R, 900s Julia first call)
- Reconnect: máximo 2 reintentos con logging estructurado

------------------------------------------------------------------------

## Capa 3: Subsistemas Especializados

### WebView2 Viewer

Renderiza contenido HTML interactivo (Plotly, D3.js, htmlwidgets) en ventanas flotantes asociadas a Excel.

| Componente | Responsabilidad |
|:---|:---|
| **ViewerManager** | Singleton. STA thread, environment, registro de viewers, FIFO eviction |
| **ViewerWindow** | Ventana Win32 + ICoreWebView2Controller. Navegación, resize, seguridad |
| **ContentPipeline** | Routing: inline HTML vs archivo, size-based (< 2MB string, ≥ 2MB file) |
| **PostMessageBridge** | Comunicación bidireccional JS<-->C++ via PostWebMessage |

**Filtro de navegación:**
- `about:blank`, `data:`, `blob:` — siempre permitidos
- `file://` — contenido local
- CDNs confiables: jsdelivr, cloudflare, Google Fonts, unpkg
- `localhost:port` — solo en Advanced Mode (Pluto)

### Pluto.jl Advanced Mode

| Componente | Responsabilidad |
|:---|:---|
| **PlutoManager** | Lifecycle del servidor Pluto: start/stop, port probe, process management |
| **NotebookLibrary** | Registro de 15 notebooks precargados + directorio custom |
| **NotebookExporter** | Captura análisis y exporta como notebook Pluto reproducible |

**Pipeline de datos Excel --> Pluto:**
```
Excel                    ControlJulia              Pluto (proceso separado)
  │                         │                         │
  │ PLUTO.DATA(range,name)  │                         │
  │────────────────────────-->│                         │
  │                         │ NEVEN.set_data()       │
  │                         │ --> _datasets[name]       │
  │                         │ --> C:\NEVEN\data\*.tsv  │
  │                         │                         │
  │                         │                    read TSV
  │                         │                    <--────│
  │                         │                         │ Análisis
  │                         │                         │ (PCA, etc.)
```

### Quarto Integration

Renderiza documentos `.qmd` como proceso externo y muestra el resultado en WebView2.

```
Excel --> CreateProcess("C:\Quarto\bin\quarto.exe render file.qmd --to html")
      --> WaitForSingleObject (max 60s)
      --> ViewerManager::CreateViewerFromFile(output.html)
```

**Nota:** Requiere junction `C:\Quarto` --> `C:\Program Files\Quarto\` por bug de Sass con espacios en ruta.

### Presentaciones

| Componente | Responsabilidad |
|:---|:---|
| **PresentationBuilder** | Composición de presentaciones reveal.js desde Excel |
| **CreadorPresentaciones** | Editor Impress.js drag-and-drop en WebView2 |

### Toolbar (MenuService)

Barra de herramientas CommandBar creada via COM automation (`AccessibleObjectFromWindow` --> `CommandBars.Add`). 6 botones funcionales en pestaña Complementos.

------------------------------------------------------------------------

## Capa 4: Herramientas Comunes

| Componente | Responsabilidad |
|:---|:---|
| **Pipe** | Named Pipe wrapper: connect, read, write, reconnect |
| **WindowManager** | Gestión de ventanas Win32 (consola, callbacks) |
| **EnvService** | Variables de entorno y paths del sistema |
| **child_process_log** | Logging unificado para procesos hijo (ControlR/Julia) |
| **type_conversions** | XLOPER12 <--> Protobuf Variable conversión |
| **string_utilities** | Split, trim, conversión de strings |
| **json11** | Parser JSON ligero (third-party) |

------------------------------------------------------------------------

## Flujo de Inicialización

```
xlAutoOpen()
  │
  ├─ LogService::Initialize()
  ├─ ConfigService::Initialize()          <-- neven-config.json
  ├─ SecurityService::Initialize()
  ├─ LanguageManager::ConfigureLanguages() <-- neven-languages.json
  │    ├─ LanguageService[R]::Connect()    --> ControlR.exe (Named Pipe)
  │    └─ LanguageService[Julia]::Connect() --> ControlJulia.exe (Named Pipe)
  ├─ ViewerManager::Initialize()           <-- WebView2 runtime detection + STA thread
  ├─ PlutoManager::Initialize()            <-- Julia path resolution
  ├─ RJ2XCL_Engine::MapFunctions()         <-- xlfRegister ~125 funciones
  │
  └─ Timer (5s) --> UpdateFunctions() + MenuService::CreateMenu()
```

## Flujo de Cierre

```
xlAutoClose()
  │
  ├─ MenuService::RemoveMenu()
  ├─ PlutoManager::Shutdown()     <-- TerminateProcess si started_by_this_session
  ├─ ViewerManager::Shutdown()    <-- CloseAllViewers + STA thread WM_QUIT
  └─ RJ2XCL_Engine::Close()      <-- Disconnect pipes, close handles
```

------------------------------------------------------------------------

## Estructura de Directorios en Producción

```
C:\NEVEN\
├── NEVEN64.xll              # Add-in Excel
├── ControlR.exe               # Proceso hijo R
├── ControlJulia.exe           # Proceso hijo Julia
├── ControlPython.exe          # Proceso hijo Python
├── neven-config.json         # Configuración global
├── neven-languages.json      # R + Julia + Python
├── startup\
│   ├── startup.r              # Script inicio R
│   └── startup.jl             # Módulo NEVEN Julia + data exchange
├── notebooks\                 # 15 notebooks Pluto precargados
│   ├── excel_data.jl          # Notebook genérico NxP
│   ├── linalg_decomposition.jl
│   └── ...
├── data\                      # Datasets compartidos Excel<-->Pluto (TSV)
├── quarto\                    # Documentos Quarto (.qmd)
├── webview2-data\             # Archivos HTML temporales
├── CreadorPresentaciones\     # Editor Impress.js
│   ├── index.html
│   ├── script.js
│   └── styles.css
└── neven.log                 # Log del add-in

%USERPROFILE%\Documents\NEVEN\
├── functions\             # Funciones R/Julia/Python del usuario
├── notebooks\             # Notebooks .jl, .R, .py (descubiertos dinámicamente)
├── prompts\               # Templates AI editables (.txt)
└── graphics\              # Gráficos generados
```

------------------------------------------------------------------------

## Decisiones Arquitectónicas Clave

| Decisión | Justificación |
|:---|:---|
| Procesos hijo separados (ControlR/Julia) | Crash de R no mata Excel. Aislamiento de memoria |
| Protocol Buffers para IPC | Versionable, eficiente, independiente del lenguaje |
| WebView2 en STA thread dedicado | COM apartment threading requerido por WebView2 |
| Archivo TSV para Excel<-->Pluto | Pluto corre en proceso Julia separado, no comparte memoria |
| Quarto como CreateProcess externo | Evita bloquear el pipe. Timeout de 60s |
| Junction C:\Quarto | Workaround para bug de Sass con espacios en ruta |
| CommandBar (no Ribbon) | XLL puro no puede registrar Ribbon sin COM Add-in |
| `require_secret_for_access=false` | Pluto v1.0.1 requiere token; localhost es seguro |
| Python reactivado | 4 bugs de estabilidad resueltos (retry startup, SEH guard, single-block, health check). R+Julia+Python activos |

------------------------------------------------------------------------

*Documento actualizado en junio 2026. Versión 2.0 — Post remediación de seguridad.*
*NEVEN — Universidad de Costa Rica, Tesis de Maestría.*


------------------------------------------------------------------------

## Módulo NEVEN-SIM: Simulación Monte Carlo (Julio 2026)

NEVEN-SIM es un **XLL separado** (`NEVEN-SIM.xll`) que carga junto a NEVEN64.xll y proporciona simulación estocástica, análisis de riesgo y exploración reactiva de escenarios.

### Arquitectura NEVEN-SIM

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Microsoft Excel                              │
│  ┌─────────────────────┐        ┌──────────────────────────────────┐ │
│  │   NEVEN64.xll       │        │     NEVEN-SIM.xll                │ │
│  │   (Base)            │◄──────►│     (Simulación)                 │ │
│  │ • LanguageManager   │ xlUDF  │ • SimBridge (relay a R/Julia)    │ │
│  │ • ViewerManager     │        │ • SimEngine (orquestador)        │ │
│  │ • PostMessageBridge │        │ • FitService (→R fitdistrplus)   │ │
│  └────────┬────────────┘        │ • MonteCarloService (→Julia)     │ │
│           │                      │ • SensitivityService (Spearman)  │ │
│           │ Named Pipes          │ • SimViewerManager (WebView2)    │ │
│           ▼                      │ • BridgePoller (JS↔Excel)        │ │
│    ControlR / ControlJulia       └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Principios de Diseño

| Principio | Implementación |
|:---|:---|
| **Modularidad** | XLL separado, no modifica NEVEN64.xll |
| **Orquestación C++** | El XLL coordina R→Julia pipeline |
| **Sin recalculation loop** | Julia ejecuta N iteraciones internamente |
| **Reactividad JS** | Explorador de escenarios 100% en JavaScript |
| **Lazy detection** | SimBridge detecta NEVEN base en primer uso, no en xlAutoOpen |

### Comunicación Inter-XLL

NEVEN-SIM consume servicios de NEVEN base via `xlUDF`:
- `SimBridge::CallR(code)` → `xlUDF("NEVEN.r", code)` → ControlR.exe
- `SimBridge::CallJulia(code)` → `xlUDF("NEVEN.j", code)` → ControlJulia.exe
- `SimBridge::CallUDF_Public("NEVEN.v", path)` → abre WebView2 viewer

### Funciones Excel (NEVEN-SIM)

| Función | Descripción |
|:---|:---|
| `=SIM.Status()` | Estado del módulo y conexión a base |
| `=SIM.Fit(rango, [dist])` | Ajusta distribución a datos vía R |
| `=SIM.QuickRun(rango, modelo, N, [reporte])` | Pipeline completo: Fit→MC→Resultados |
| `=SIM.Datos(N)` | Primeras N muestras simuladas |
| `=SIM.Exportar()` | Exporta resultados completos a CSV |
| `=SIM.Workspace()` | Abre explorador interactivo |
| `=SIM.Percentile(p)` | Percentil de última simulación |
| `=SIM.Sensitivity()` | Análisis de sensibilidad (Tornado) |

### Explorador Reactivo (WebView2)

El viewer HTML genera simulaciones Monte Carlo **en JavaScript puro** usando:
- Box-Muller (Normal), transformaciones para Gamma/Weibull/Beta/LogNormal
- Plotly.js para histogramas interactivos
- Sliders que recalculan 200,000 muestras en <100ms
- Comparación de escenarios con histogramas superpuestos
- Escenarios guardados con parámetros visibles para copiar

### Dependencias

| Componente | Versión | Uso |
|:---|:---|:---|
| fitdistrplus (R) | >= 1.1 | Ajuste de distribuciones MLE |
| Distributions.jl | >= 0.25 | Generación de muestras en Julia |
| Plotly.js | 2.32.0 | Visualización interactiva |
| json11 | vendored | Parsing JSON en C++ |

### Build

```bash
cmake -DBUILD_NEVEN_SIM=ON ...
cmake --build . --target NEVEN_SIM
```

Produce: `NEVEN-SIM.xll` (~400KB)
Tests: `cmake --build . --target NEVEN_SIM_Tests` (69 tests)

---

## NEVEN Studio Standalone (Julio 2026)

NEVEN Studio Standalone es el modo de operación de NEVEN **sin Microsoft Excel**. Reutiliza exactamente los mismos procesos hijo C++ (`ControlR.exe`, `ControlPython.exe`, `ControlJulia.exe`) pero los arranca desde un script Python en lugar del XLL.

### Arquitectura Studio Standalone

```
┌──────────────────────────────────────────────────────────────────────┐
│                    NEVEN Studio Standalone                            │
│                                                                       │
│  NEVEN Studio.vbs                                                    │
│       │                                                               │
│       ▼                                                               │
│  start_studio.py ──────────────────────> ControlPython.exe          │
│       │                                        │                     │
│       │                                  neven_http_server.py        │
│       │                                  (puerto 5555)               │
│       │                                        │                     │
│       │                            ┌───────────┴────────────┐       │
│       │                            │   Named Pipes (IPC)    │       │
│       │                            │                        │       │
│       │                      ControlR.exe    ControlJulia.exe        │
│       │                          │                │                  │
│       │                       R 4.4.1       Julia 1.12.6             │
│       │                                                               │
│       ▼                                                               │
│  Navegador del sistema                                               │
│  (Chrome/Edge → http://localhost:5555)                               │
│  taskpane.html + datalab.js + taskpane.js                            │
└──────────────────────────────────────────────────────────────────────┘
```

### Diferencia con modo Excel

| Aspecto | Modo Excel | Modo Studio |
|:---|:---|:---|
| Requiere Excel | ✅ Obligatorio | ❌ No necesario |
| Inicia ControlPython | NEVEN64.xll (C++) | start_studio.py (Python) |
| UI | Panel lateral Excel | Navegador web |
| Datos entran via | Celdas de Excel | CSV/Parquet/JSON o Excel Bridge |
| Resultados van a | Celdas de Excel | Visualización en browser |
| Binarios C++ | Sin cambios | Sin cambios |

### Componentes nuevos (Python + HTML)

| Archivo | Responsabilidad |
|:---|:---|
| `start_studio.py` | Lanza ControlPython.exe, configura puertos |
| `neven_http_server.py` | Servidor HTTP BaseHTTPRequestHandler, rutas API |
| `taskpane.html` | UI principal: tabs (Data Studio, Data Lab, Run Script, etc.) |
| `taskpane.js` | Lógica UI: carga de archivos, ejecución de scripts, bridge Excel |
| `datalab.js` | Módulo Data Lab: catálogo, asignación de columnas, resultados |
| `pipe_client.py` | Cliente Named Pipes Python — mismos pipes que usa el XLL |
| `NEVEN Studio.vbs` | Lanzador: `wscript.exe` → `pythonw.exe start_studio.py` |

### Rutas HTTP

| Método | Ruta | Función |
|:---|:---|:---|
| GET | `/` | Sirve `taskpane.html` |
| POST | `/api/r` | Ejecuta código R en ControlR |
| POST | `/api/python` | Ejecuta código Python en ControlPython |
| POST | `/api/julia` | Ejecuta código Julia en ControlJulia |
| POST | `/api/load_file` | Carga CSV/Parquet/JSON en DuckDB |
| POST | `/api/query` | Consulta SQL en DuckDB |
| GET | `/api/datalab/catalog` | Catálogo de funciones Data Lab |
| POST | `/api/datalab/run` | Ejecuta función Data Lab |

---

## Data Lab (Julio 2026)

El Data Lab es la pestaña de NEVEN Studio que expone funciones analíticas de R y Python mediante una interfaz guiada de punto y clic, sin escribir código.

### Componentes Data Lab

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Lab UI                                │
│              (datalab.js + taskpane.html)                       │
│                                                                 │
│  Familia ▼  │  Función  │  Columnas → Roles  │  Parámetros     │
│                                                                 │
│             GET /api/datalab/catalog                            │
│                    ▼                                            │
│             DataLabHandler.handle_catalog()                     │
│             (C:\NEVEN\functions\*.json)                         │
│                                                                 │
│             POST /api/datalab/run                               │
│                    ▼                                            │
│             DataLabHandler.handle_run()                         │
│             DuckDB → columnas → R script → ControlR.exe        │
│                    ▼                                            │
│             r_object_to_slots() → Slots tipificados             │
│                    ▼                                            │
│             Results Panel (table, html, scalar, vector)         │
└─────────────────────────────────────────────────────────────────┘
```

### Sidecar JSON Convention

Cada función del catálogo tiene un par de archivos en `C:\NEVEN\functions\`:

```
AD_KMedias.Studio.R      ← implementación R
AD_KMedias.json          ← metadatos UI (sidecar)
```

El sidecar define:
- `id`, `family`, `family_label`, `name`, `description`
- `variable_roles` — roles de columnas con tipos y multiplicidad
- `parameters` — parámetros con tipo, default y tier (1=visible, 2=avanzado)
- `languages` — lenguajes disponibles (`["r"]`, `["python"]`, etc.)

### Serializer r_object_to_slots

Función R cargada en startup de ControlR que convierte cualquier objeto S3 en slots tipificados:

```
obj R → r_object_to_slots() → data.frame → ControlR → Variable(arr) → Python → JSON
```

Tipos de slots: `table`, `scalar`, `vector`, `html`, `unknown`
Tiers: `1` = expandido por defecto, `2` = en sección "Detalles técnicos"

### Estructura de directorios nuevos en producción

```
C:\NEVEN\
├── taskpane\              # NEVEN Studio Standalone
│   ├── taskpane.html
│   ├── taskpane.js
│   ├── taskpane.css
│   ├── datalab.js
│   ├── pipe_client.py
│   ├── neven_http_server.py (+ datalab_handler.py en startup/)
│   ├── start_studio.py
│   └── NEVEN Studio.vbs
└── functions\             # Catálogo Data Lab
    ├── R4XCL-AD-KMediass.Studio.R
    ├── R4XCL-AD-KMediass.json
    ├── TM_TextAnalysis.Studio.py
    ├── TM_TextAnalysis.json
    ├── UC_EjemploBasico.Studio.R
    ├── UC_EjemploBasico.json
    └── ... (18 funciones total)
```

*Documento actualizado: 30 de julio de 2026 — Post NEVEN Studio Standalone y Data Lab V1.*
