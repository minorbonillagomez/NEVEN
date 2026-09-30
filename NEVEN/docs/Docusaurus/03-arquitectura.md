---
id: arquitectura
title: Capitulo 3 -- Arquitectura
sidebar_label: 3. Arquitectura
sidebar_position: 3
---

# Capitulo 3: Arquitectura del Sistema

## 3.1 Vision general

NEVEN se organiza en 4 capas, cada una con responsabilidades claras:

$
\underbrace{\text{Interface Excel}}_{\text{Capa 1}} \rightarrow \underbrace{\text{Servicios Nucleo}}_{\text{Capa 2}} \rightarrow \underbrace{\text{Subsistemas}}_{\text{Capa 3}} \rightarrow \underbrace{\text{Herramientas}}_{\text{Capa 4}}
$

### Capa 1: Interface Excel (XLL)

El punto de entrada. Registra ~200 funciones en Excel, gestiona el ciclo de vida del add-in, y crea la toolbar.

| Componente | Responsabilidad |
|:---|:---|
| `RJ2XCL_Engine` | Singleton principal: Init, Close, callbacks |
| `basic_functions` | ~200 funciones exportadas a Excel |
| `MenuService` | Toolbar CommandBar (legacy, deshabilitado) |
| `NEVENRibbon.dll` | Ribbon COM nativo con iconos |

### Capa 2: Servicios del Nucleo

La logica de negocio: configuracion, lenguajes, seguridad, logging.

| Servicio | Responsabilidad |
|:---|:---|
| `ConfigService` | Lee `neven-config.json`, valida paths, getters tipados |
| `LanguageManager` | Orquesta R y Julia: conexion, health, dispatch |
| `LanguageService` | Un proceso hijo: pipe, timeout, reconnect |
| `SandboxVerifier` | Valida codigo antes de ejecucion |
| `SecurityService` | SHA-256 para integridad de archivos |
| `DiscoveryService` | Detecta R y Julia en el sistema |
| `LogService` | Logging estructurado a archivo |

### Capa 3: Subsistemas Especializados

Los componentes que hacen a NEVEN unico:

| Subsistema | Componentes |
|:---|:---|
| **WebView2** | ViewerManager, ViewerWindow, ContentPipeline, PostMessageBridge |
| **Pluto.jl** | PlutoManager, NotebookLibrary, NotebookExporter |
| **Quarto** | Integrado en `basic_functions.cc` (CreateProcess) |
| **Presentaciones** | PresentationBuilder, CreadorPresentaciones (Impress.js) |

### Capa 4: Herramientas Comunes

Utilidades compartidas por todas las capas:

| Herramienta | Uso |
|:---|:---|
| `Pipe` | Named Pipe wrapper (connect, read, write) |
| `type_conversions` | XLOPER12 <--> Protobuf Variable |
| `json11` | Parser JSON ligero |
| `child_process_log` | Logging para procesos hijo |

## 3.2 Comunicacion entre componentes

$
\text{Excel} \xrightleftharpoons[\text{Protobuf}]{\text{Named Pipe}} \text{ControlR/Julia} \xrightarrow{\text{TSV}} \text{Pluto.jl}
$

El protocolo de comunicacion usa **Protocol Buffers** sobre **Named Pipes**:

1. Excel serializa argumentos como `Variable` (Protobuf)
2. Envia por pipe a ControlR.exe o ControlJulia.exe
3. El proceso hijo ejecuta la funcion R/Julia
4. Serializa el resultado como `Variable`
5. Retorna por pipe al XLL
6. El XLL convierte a `XLOPER12` para Excel

## 3.3 Flujo de inicializacion

```
xlAutoOpen()
  +-- LogService::Initialize()
  +-- ConfigService::Initialize()           <-- neven-config.json
  +-- SecurityService::Initialize()
  +-- LanguageManager::ConfigureLanguages() <-- neven-languages.json
  |    +-- LanguageService[R]::Connect()    --> ControlR.exe
  |    +-- LanguageService[Julia]::Connect() --> ControlJulia.exe
  +-- ViewerManager::Initialize()           <-- WebView2 STA thread
  +-- PlutoManager::Initialize()
  +-- MapFunctions() + xlfRegister          <-- ~200 funciones
  +-- Timer(5s) --> UpdateFunctions()
```

## 3.4 Decisiones arquitectonicas clave

| Decision | Justificacion |
|:---|:---|
| Procesos hijo separados | Crash de R no mata Excel |
| Protobuf para IPC | Versionable, eficiente, agnostico |
| WebView2 en STA thread | COM apartment threading requerido |
| TSV para Excel<-->Pluto | Procesos separados, no comparten memoria |
| Quarto como CreateProcess | No bloquea el pipe, timeout 60s |
| `require_secret_for_access=false` | Pluto 0.20 requiere token; localhost es seguro |
| Junction `C:\Quarto` | Workaround para bug de Sass |


## 3.6 NEVEN-SIM: Modulo de Simulacion (XLL separado)

NEVEN-SIM es un add-in XLL independiente que carga junto a NEVEN64.xll. Proporciona simulacion Monte Carlo, fitting de distribuciones y analisis de sensibilidad.

### Comunicacion Inter-XLL

```
NEVEN-SIM.xll --[xlUDF]--> NEVEN64.xll --[Named Pipe]--> ControlR/Julia
```

NEVEN-SIM usa `xlUDF` para llamar funciones registradas por NEVEN base (`NEVEN.r`, `NEVEN.j`, `NEVEN.v`). No tiene sus propios procesos hijo.

### Componentes

| Componente | Responsabilidad |
|:---|:---|
| `SimBridge` | Relay a R/Julia via xlUDF (lazy detection) |
| `SimEngine` | Orquestador: Fit → Simulate → Analyze |
| `FitService` | Genera codigo R (fitdistrplus) |
| `MonteCarloService` | Genera codigo Julia (Distributions.jl) |
| `SensitivityService` | Spearman rank correlation |
| `SimViewerManager` | Genera HTML y abre viewer |

### Explorador Reactivo

El viewer de NEVEN-SIM incluye un simulador Monte Carlo 100% JavaScript que permite explorar escenarios en tiempo real (<100ms para 200K muestras). Soporta 7 distribuciones, comparacion de escenarios y sliders interactivos.

Referencia completa: **Capitulo 12 - Simulacion Monte Carlo**

## 3.7 NEVEN Studio Standalone (Julio 2026)

NEVEN Studio es el modo de operación **sin Excel**. Reutiliza los mismos procesos hijo C++ pero los arranca desde Python en lugar del XLL.

### Flujo de arranque

```
NEVEN Studio.vbs
  → pythonw.exe start_studio.py
    → ControlPython.exe (con neven_http_server.py en puerto 5555)
      → ControlR.exe (Named Pipe)
      → ControlJulia.exe (Named Pipe)
  → Navegador → http://localhost:5555 → taskpane.html
```

### Componentes Studio

| Componente | Tecnología | Rol |
|:---|:---|:---|
| `start_studio.py` | Python | Lanza ControlPython, configura config |
| `neven_http_server.py` | Python BaseHTTPRequestHandler | Servidor HTTP rutas API |
| `taskpane.html` | HTML5 | UI con tabs: Data Lab, Run Script, Data Studio |
| `taskpane.js` | JavaScript | Lógica UI, bridge Excel |
| `datalab.js` | JavaScript | Módulo Data Lab completo |
| `pipe_client.py` | Python | Cliente Named Pipes (mismos que XLL) |
| `NEVEN Studio.vbs` | VBScript | Lanzador sin consola visible |

### Rutas API

| Ruta | Descripción |
|:---|:---|
| `GET /api/datalab/catalog` | Catálogo Data Lab (sidecar JSONs) |
| `POST /api/datalab/run` | Ejecuta Studio wrapper via ControlR |
| `POST /api/r` | Ejecuta código R arbitrario |
| `POST /api/python` | Ejecuta código Python |
| `POST /api/load_file` | Carga CSV/Parquet/JSON en DuckDB |
| `POST /api/query` | Consulta SQL en DuckDB |

---

## 3.8 Data Lab (Julio 2026)

El Data Lab es la pestaña de NEVEN Studio para análisis estadístico sin código.

### Arquitectura

```
UI (datalab.js)
  │
  ├─ GET /api/datalab/catalog ──> DataLabHandler.handle_catalog()
  │                                    └─> escanea C:\NEVEN\functions\*.json
  │
  └─ POST /api/datalab/run ────> DataLabHandler.handle_run()
                                      ├─> DuckDB: SELECT columnas FROM dataset
                                      ├─> build R script
                                      ├─> Named Pipe → ControlR.exe
                                      │     └─> wrapper.Studio(data_X, params...)
                                      │           └─> r_object_to_slots()
                                      └─> slots → JSON response → UI
```

### Sidecar JSON Convention

```
C:\NEVEN\functions\
├── AD_KMedias.Studio.R       ← implementación R
├── AD_KMedias.json           ← metadatos (sidecar)
├── TM_TextAnalysis.Studio.py ← implementación Python
└── TM_TextAnalysis.json      ← metadatos
```

### r_object_to_slots Serializer

```
Objeto R S3 → r_object_to_slots(obj, tier_map) → data.frame
           ↓
  Columnas: name | label | type | value | tier
           ↓
  Variable(arr) via ControlR → Python → JSON → UI
```

Tipos de slot: `table` · `scalar` · `vector` · `html` · `unknown`

Tiers: `1` = visible por defecto | `2` = en "Detalles técnicos" (colapsado)

### Catálogo de funciones (18 Studio wrappers)

| Familia | Funciones |
|:---|:---|
| **AD** — Análisis de Datos | K-Medias, Componentes Principales, Clustering Jerárquico |
| **RG** — Regresión | Lineal, Logística, Árbol de Decisión, Datos Panel, Poisson, Series de Tiempo, SVM, Tobit |
| **DS** — Conjuntos de Datos | Wooldridge (115 datasets de econometría) |
| **TM** — Text Mining | Análisis PDF/DOCX/TXT con resumen LLM y WordCloud |
| **UC** — Mis Funciones | 3 plantillas para funciones personalizadas |

### AI Integration

`TM_TextAnalysis.Studio.py` llama a LMStudio via HTTP para generar un resumen contextual del documento analizado. Configurado en `neven-config.json` bajo la clave `"AI"`.
