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
