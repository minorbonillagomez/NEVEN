---
id: arquitectura
title: Capítulo 3 -- Arquitectura
sidebar_label: 3. Arquitectura
sidebar_position: 3
---

# Capitulo 3: Arquitectura del Sistema

## 3.1 Vision general

NEVEN se organiza en 4 capas, cada una con responsabilidades claras:

$$
\underbrace{\text{Interface Excel}}_{\text{Capa 1}} \rightarrow \underbrace{\text{Servicios Nucleo}}_{\text{Capa 2}} \rightarrow \underbrace{\text{Subsistemas}}_{\text{Capa 3}} \rightarrow \underbrace{\text{Herramientas}}_{\text{Capa 4}}
$$

### Capa 1: Interface Excel (XLL)

El punto de entrada. Registra ~200 funciones en Excel, gestiona el ciclo de vida del add-in y crea la pestaña Ribbon.

| Componente | Responsabilidad |
|:---|:---|
| `RJ2XCL_Engine` | Singleton principal: Init, Close, callbacks |
| `basic_functions` | ~200 funciones exportadas a Excel |
| `NEVENRibbon.dll` | Ribbon COM nativo con iconos |

### Capa 2: Servicios del Nucleo

La logica de negocio: configuracion, lenguajes, seguridad, logging.

| Servicio | Responsabilidad |
|:---|:---|
| `ConfigService` | Lee `neven-config.json`, valida paths, getters tipados |
| `LanguageManager` | Orquesta R, Julia y Python: conexion, health, dispatch |
| `LanguageService` | Un proceso hijo: pipe, timeout, reconnect |
| `SandboxVerifier` | Valida codigo antes de ejecucion |
| `SecurityService` | SHA-256 para integridad de archivos |
| `DiscoveryService` | Detecta R, Julia y Python en el sistema |
| `LogService` | Logging estructurado a archivo |

### Capa 3: Subsistemas Especializados

| Subsistema | Componentes |
|:---|:---|
| **WebView2** | ViewerManager, ViewerWindow, ContentPipeline, PostMessageBridge |
| **Pluto.jl** | PlutoManager, NotebookLibrary, NotebookExporter |
| **Quarto** | Integrado en `basic_functions.cc` (CreateProcess) |
| **Presentaciones** | PresentationBuilder, CreadorPresentaciones (Impress.js) |
| **RAG Engine** | rag_engine.py, ontology_service.py, DuckDB VSS |

### Capa 4: Herramientas Comunes

| Herramienta | Uso |
|:---|:---|
| `Pipe` | Named Pipe wrapper (connect, read, write) |
| `type_conversions` | XLOPER12 <--> Protobuf Variable |
| `json11` | Parser JSON ligero |
| `child_process_log` | Logging para procesos hijo |

---

## 3.2 Motores de scripting

NEVEN integra tres motores de calculo como procesos hijo independientes:

| Motor | Proceso | Mecanismo | Notas |
|:---|:---|:---|:---|
| **R 4.4.1** | `ControlR.exe` | C API embebido | Estadistica, ML, graficos |
| **Julia 1.12.6** | `ControlJulia.exe` | `libjulia` embebida | Matematica, simulacion |
| **Python 3.12** | `ControlPython.exe` | Stable ABI (`python3.dll`) | Data Science, IA, HTTP server |

### Sysimage de Julia

Julia tiene un cold-start de varios minutos la primera vez. Para eliminarlo, NEVEN precompila una sysimage personalizada:

```
neven_julia.dll  (~415 MB)
```

La sysimage incluye todas las librerias J4XCL precompiladas. El tiempo de arranque se reduce de minutos a segundos.

---

## 3.3 Comunicacion entre componentes

$$
\text{Excel} \xrightleftharpoons[\text{Protobuf}]{\text{Named Pipe}} \begin{cases} \text{ControlR.exe} \\ \text{ControlJulia.exe} \\ \text{ControlPython.exe} \end{cases}
$$

El protocolo de comunicacion usa **Protocol Buffers** sobre **Named Pipes** de Windows:

1. Excel serializa argumentos como `Variable` (Protobuf)
2. Envia por pipe al proceso hijo correspondiente
3. El proceso hijo ejecuta la funcion en R, Julia o Python
4. Serializa el resultado como `Variable`
5. Retorna por pipe al XLL
6. El XLL convierte a `XLOPER12` para Excel

Para Pluto.jl, los datos viajan como TSV (procesos separados no comparten memoria):

$$
\text{Excel} \xrightarrow{\text{Named Pipe}} \text{ControlJulia.exe} \xrightarrow{\text{TSV}} \text{Pluto.jl}
$$

---

## 3.4 Flujo de inicializacion

```
xlAutoOpen()
  +-- LogService::Initialize()
  +-- ConfigService::Initialize()             <-- neven-config.json
  +-- SecurityService::Initialize()
  +-- LanguageManager::ConfigureLanguages()   <-- neven-languages.json
  |    +-- LanguageService[R]::Connect()      --> ControlR.exe
  |    +-- LanguageService[Julia]::Connect()  --> ControlJulia.exe
  |    +-- LanguageService[Python]::Connect() --> ControlPython.exe
  +-- ViewerManager::Initialize()             <-- WebView2 STA thread
  +-- PlutoManager::Initialize()
  +-- MapFunctions() + xlfRegister            <-- ~200 funciones
  +-- Timer(5s) --> UpdateFunctions()
```

---

## 3.5 Decisiones arquitectonicas clave

| Decision | Justificacion |
|:---|:---|
| Procesos hijo separados | Crash de R no mata Excel |
| Protobuf para IPC | Versionable, eficiente, agnostico al lenguaje |
| Python Stable ABI | Compatibilidad entre versiones de Python sin recompilar |
| WebView2 en STA thread | COM apartment threading requerido |
| TSV para Excel↔Pluto | Procesos separados, no comparten memoria |
| Quarto como CreateProcess | No bloquea el pipe, timeout 60s |
| Sysimage Julia (~415 MB) | Elimina cold-start de minutos a segundos |
| DuckDB para RAG y DataLab | SQL + vectores en un solo engine local, sin servidor |

---

## 3.6 NEVEN-SIM: Modulo de Simulacion (XLL separado)

NEVEN-SIM es un add-in XLL independiente que carga junto a NEVEN64.xll. Proporciona simulacion Monte Carlo, fitting de distribuciones y analisis de sensibilidad.

### Comunicacion Inter-XLL

```
NEVEN-SIM.xll --[xlUDF]--> NEVEN64.xll --[Named Pipe]--> ControlR/Julia
```

NEVEN-SIM usa `xlUDF` para llamar funciones registradas por NEVEN base. No tiene sus propios procesos hijo.

### Componentes

| Componente | Responsabilidad |
|:---|:---|
| `SimBridge` | Relay a R/Julia via xlUDF |
| `SimEngine` | Orquestador: Fit → Simulate → Analyze |
| `FitService` | Genera codigo R (fitdistrplus) |
| `MonteCarloService` | Genera codigo Julia (Distributions.jl) |
| `SensitivityService` | Spearman rank correlation |
| `SimViewerManager` | Genera HTML y abre viewer |

El viewer incluye un simulador 100% JavaScript (<100ms para 200K muestras, 7 distribuciones).

Referencia completa: **Capitulo 12 - Simulacion Monte Carlo**

---

## 3.7 NEVEN Studio (modo standalone)

NEVEN Studio opera **sin Excel**. Reutiliza los mismos procesos hijo C++ pero los arranca desde Python en lugar del XLL.

### Flujo de arranque

```
NEVEN Studio.vbs
  --> pythonw.exe start_studio.py
        --> ControlPython.exe
              --> neven_http_server.py  (puerto 5555)
                    --> ControlR.exe     (Named Pipe)
                    --> ControlJulia.exe (Named Pipe)
  --> Navegador --> http://localhost:5555 --> taskpane.html
```

### Componentes Studio

| Componente | Tecnologia | Rol |
|:---|:---|:---|
| `start_studio.py` | Python | Lanza ControlPython, configura config |
| `neven_http_server.py` | Python BaseHTTPRequestHandler | Servidor HTTP, rutas API |
| `rag_engine.py` | Python + DuckDB + fastembed | Motor RAG con busqueda vectorial |
| `ontology_service.py` | Python + YAML | Carga y consulta ontologias |
| `taskpane.html` | HTML5 | UI con tabs: SQL, Data Studio, Run Script, Data Lab, Presentaciones, IA, Ayuda |
| `datalab.js` | JavaScript | Modulo Data Lab completo |
| `NEVEN Studio.vbs` | VBScript | Lanzador sin consola visible |

### Rutas API principales

| Ruta | Metodo | Descripcion |
|:---|:---:|:---|
| `/api/r` | POST | Ejecuta codigo R arbitrario |
| `/api/python` | POST | Ejecuta codigo Python |
| `/api/julia` | POST | Ejecuta codigo Julia |
| `/api/datalab/catalog` | GET | Catalogo de funciones Data Lab |
| `/api/datalab/run` | POST | Ejecuta wrapper Studio via ControlR |
| `/api/load_file` | POST | Carga CSV/Parquet/JSON en DuckDB |
| `/api/query` | POST | Consulta SQL en DuckDB |
| `/api/rag/upload` | POST | Indexa documento en RAG |
| `/api/rag/browse` | GET | Abre explorador de archivos nativo (tkinter) |
| `/api/rag/query` | POST | Busqueda semantica en RAG |
| `/api/rag/stats` | GET | Estadisticas del indice RAG |
| `/api/rag/documents` | GET | Lista documentos indexados |
| `/api/ontology/query` | POST | Consulta ontologia |
| `/api/packages/status` | GET | Estado paquetes R/Julia/Python |

---

## 3.8 Data Lab

El Data Lab es la pestana de NEVEN Studio para analisis estadistico sin codigo.

### Arquitectura

```
UI (datalab.js)
  |
  +-- GET /api/datalab/catalog --> escanea C:\NEVEN\functions\*.json
  |
  +-- POST /api/datalab/run
            +--> DuckDB: SELECT columnas FROM dataset
            +--> build R/Python script
            +--> Named Pipe --> ControlR.exe o ControlPython.exe
            |       --> wrapper.Studio(data, params)
            |             --> r_object_to_slots()
            +--> slots --> JSON --> UI (buildSlotElement)
```

### Sidecar JSON Convention

```
C:\NEVEN\functions\
+-- AD_KMedias.Studio.R       <- implementacion R
+-- AD_KMedias.json           <- metadatos (sidecar)
+-- TM_TextAnalysis.Studio.py <- implementacion Python
+-- TM_TextAnalysis.json      <- metadatos
```

### Tipos de slot

| Tipo | Descripcion |
|:---|:---|
| `table` | Data frame con paginacion y descarga CSV |
| `scalar` | Valor numerico o texto unico |
| `vector` | Arreglo de valores |
| `html` | Contenido HTML arbitrario (graficos, tablas enriquecidas) |
| `plotly` | Grafico interactivo Plotly |

**Tiers:** `1` = visible por defecto | `2` = colapsado en "Detalles tecnicos"

---

## 3.9 RAG Engine (Ontology-Guided RAG)

El RAG Engine permite al agente IA responder preguntas fundamentadas en literatura especializada indexada por el usuario.

### Arquitectura

```
Query del usuario
  |
  +--> OntologyService (deteccion de dominio)
  |       --> 213 entidades de 6 schemas YAML
  |       --> expande terminos ("ACP" --> "PCA", "principal components")
  |
  +--> RAGEngine.query()
          --> fastembed (bge-small-en-v1.5, 384 dims, offline)
          --> DuckDB VSS (HNSW index)
          --> filtro por dominio + minScore
          --> top-K chunks con score, fuente y pagina
```

### Formatos de documentos soportados (todos offline)

| Formato | Extensiones | Dependencia |
|:---|:---|:---|
| PDF | .pdf | markitdown[pdf], pdfplumber |
| Word | .docx | markitdown[docx] |
| PowerPoint | .pptx | markitdown[pptx] |
| Excel | .xlsx, .xls | markitdown[xlsx,xls] |
| EPUB | .epub | ebooklib |
| HTML / Texto | .html, .csv, .json, .xml, .txt, .md | (built-in) |
| ZIP | .zip | (built-in, itera contenido) |

### Indice vectorial

El indice se almacena en `C:\NEVEN\data\rag_index.duckdb`. Se crea automaticamente en el primer uso. Los embeddings se generan localmente con `fastembed` (~67 MB de modelo descargado una sola vez).

---

## 3.10 Testing

NEVEN cuenta con **342 tests** ejecutados con Google Test v1.14.0. Los tests corren **sin Excel, R ni Julia** gracias a mock headers y `MockExcelBridge`.

| Suite | Tests | Cobertura |
|:---|:---:|:---|
| Core / basic_functions | ~80 | Funciones exportadas a Excel |
| LanguageService / Pipes | ~60 | Comunicacion Named Pipes |
| ConfigService | ~40 | Parsing y validacion de config |
| SecurityService | ~30 | SHA-256, sandbox |
| NEVEN-SIM | ~50 | Monte Carlo, fitting, sensibilidad |
| Otros | ~82 | Utilidades, conversiones, logging |

```powershell
# Ejecutar todos los tests
cmake --build . --target RUN_TESTS
# O directamente:
.\Build\tests\Release\NEVEN_tests.exe
```
