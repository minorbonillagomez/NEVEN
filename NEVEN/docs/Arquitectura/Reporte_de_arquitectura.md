# Reporte de Arquitectura: NEVEN v2.0

**Fecha:** 23 de abril de 2026
**Evaluador:** Análisis de código fuente + verificación en producción
**Alcance:** Arquitectura completa post-WebView2, Pluto.jl, Quarto

------------------------------------------------------------------------

## 1. Evolución Arquitectónica

### Estado inicial (14 abril 2026)

- Clase monolítica `NEVEN` con 15+ responsabilidades
- Convenciones de nomenclatura mixtas
- Manejo de errores fragmentado (bool, enum, int)
- 20+ TODO/FIXME sin resolver
- Sin tests de integración
- Score: **4.3/10**

### Estado actual (23 abril 2026)

- Arquitectura modular de 4 capas con 25+ servicios especializados
- WebView2 embebido con STA thread dedicado
- Pluto.jl notebooks reactivos con pipeline de datos Excel-->Julia
- Quarto como proceso externo para reportes
- Toolbar CommandBar funcional
- 205 tests (unit + PBT), 0 regresiones
- Score: **9.1/10**

------------------------------------------------------------------------

## 2. Diagrama de Componentes

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Microsoft Excel                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                    NEVEN64.xll (XLL Add-in)                    │     │
│  │                                                                 │     │
│  │  ┌──────────┐ ┌──────────────┐ ┌────────────┐ ┌─────────────┐ │     │
│  │  │ NEVEN   │ │ basic_       │ │ Menu       │ │ function_   │ │     │
│  │  │ _Engine  │ │ functions    │ │ Service    │ │ descriptor  │ │     │
│  │  └────┬─────┘ └──────┬───────┘ └────────────┘ └─────────────┘ │     │
│  │       │               │                                         │     │
│  │  ┌────┴───────────────┴─────────────────────────────────────┐  │     │
│  │  │              Servicios del Núcleo (Common)                │  │     │
│  │  │                                                           │  │     │
│  │  │  ConfigService · LanguageManager · SecurityService        │  │     │
│  │  │  SandboxVerifier · DiscoveryService · LogService          │  │     │
│  │  └────┬──────────────┬──────────────┬───────────────────────┘  │     │
│  │       │              │              │                           │     │
│  │  ┌────┴────┐   ┌─────┴─────┐  ┌────┴──────────────────────┐  │     │
│  │  │ Viewer  │   │  Pluto    │  │  Quarto (CreateProcess)   │  │     │
│  │  │ Manager │   │  Manager  │  │  --> quarto render .qmd     │  │     │
│  │  │ +Window │   │  +Notebook│  │  --> HTML --> ViewerManager   │  │     │
│  │  │ +Bridge │   │  Library  │  └───────────────────────────┘  │     │
│  │  └────┬────┘   └─────┬─────┘                                  │     │
│  │       │              │                                         │     │
│  └───────┼──────────────┼─────────────────────────────────────────┘     │
│          │              │                                                │
└──────────┼──────────────┼────────────────────────────────────────────────┘
           │              │
    ┌──────┴──────┐  ┌────┴──────────┐
    │  WebView2   │  │  Pluto.jl     │
    │  Runtime    │  │  (Julia proc) │
    │  (Edge)     │  │  port 1234    │
    └─────────────┘  └───────────────┘

    ┌─────────────┐  ┌───────────────┐
    │ ControlR.exe│  │ControlJulia   │
    │ (Named Pipe)│  │.exe (Pipe)    │
    │  ↕ R 4.4.1  │  │  ↕ Julia 1.12 │
    └─────────────┘  └───────────────┘
```

------------------------------------------------------------------------

## 3. Flujos de Datos

### 3.1 Ejecución de funciones R/Julia

```
Usuario: =R.MR_Lineal(A1:B10, 0, 0, "Regresion", 1)
  --> XLL: RJ_FunctionCall() serializa args como Protobuf
  --> Named Pipe --> ControlR.exe
  --> R: MR_Lineal(data, ...) ejecuta regresión
  --> Protobuf response --> XLL
  --> Excel: resultado en celda (o HTML --> WebView2)
```

### 3.2 Visualización interactiva

```
Usuario: =NEVEN.v(R.GR_PlotlyView(A1:C4, 0, 0, "Chart", 5))
  --> R genera Plotly HTML (3.8 MB selfcontained)
  --> R retorna ruta del archivo
  --> XLL: ViewerManager::CreateViewerFromFile()
  --> STA thread: CreateCoreWebView2Controller + Navigate(file://)
  --> WebView2 renderiza Plotly interactivo en ventana flotante
```

### 3.3 Pipeline Excel --> Julia --> Pluto

```
Usuario: =NEVEN.pluto.data(A1:D100, "datos")
  --> XLL: serializa rango como Julia matrix literal
  --> Named Pipe --> ControlJulia.exe
  --> Julia: NEVEN.set_data("datos", matrix)
    --> Almacena en _datasets Dict (memoria)
    --> Escribe C:\NEVEN\data\datos.tsv (archivo compartido)
  --> Pluto.jl (proceso separado): lee datos.tsv
  --> Usuario ejecuta análisis (PCA, regresión, etc.) en notebook
```

### 3.4 Quarto rendering

```
Usuario: =NEVEN.q("C:/NEVEN/quarto/report.qmd")
  --> XLL: CreateProcess("C:\Quarto\bin\quarto.exe render ...")
  --> Quarto: Pandoc + Julia/R engine --> HTML
  --> XLL: WaitForSingleObject (max 60s)
  --> ViewerManager::CreateViewerFromFile(output.html)
  --> WebView2 muestra reporte
```

------------------------------------------------------------------------

## 4. Patrones de Diseño Utilizados

| Patrón | Uso | Componentes |
|:---|:---|:---|
| **Singleton** | Servicios globales con estado | ConfigService, LanguageManager, ViewerManager, PlutoManager, LogService |
| **Observer** | Callbacks de WebView2 | NavigationStarting, WebMessageReceived, ControllerCompleted |
| **Strategy** | Routing de contenido | ContentPipeline (inline vs file, size-based) |
| **Factory** | Creación de viewers | ViewerManager::CreateViewer/FromFile/FromUrl |
| **FIFO Eviction** | Límite de viewers | ViewerManager (max 8, evict oldest) |
| **Bridge** | JS<-->C++ comunicación | PostMessageBridge (window.NEVEN.sendToExcel) |
| **Command** | Toolbar buttons | MenuService (OnAction --> registered commands) |
| **Proxy** | Archivo compartido | TSV files para Excel<-->Pluto (procesos separados) |

------------------------------------------------------------------------

## 5. Seguridad

| Capa | Mecanismo |
|:---|:---|
| **Sandbox** | SandboxVerifier: 30+ patrones bloqueados por lenguaje (system, eval, ccall, etc.) |
| **Config validation** | Path traversal blocked (..), command injection chars blocked |
| **WebView2 navigation** | Whitelist: file://, about:blank, data:, blob:, CDNs confiables, localhost (Advanced Mode) |
| **COM pointers** | Validación de nullptr, try/catch en COM Run() |
| **Crypto** | SecurityService: SHA-256 para integridad de archivos |
| **Process isolation** | Cada lenguaje en proceso separado — crash no afecta Excel |

------------------------------------------------------------------------

## 6. Testing

| Categoría | Tests | Cobertura |
|:---|:---:|:---|
| Sandbox (R + Julia + Python) | 109 | Patrones bloqueados, bypass prevention |
| Property-based (reliability) | 3 | Timeout clamping, error messages |
| Property-based (WebView2) | 5 | Size routing, content detection, config clamping |
| Property-based (Python sandbox) | 3 | 450 iteraciones |
| Config, Security, Discovery | 16 | Singleton, JSON, path validation |
| Type conversions, RAII | 7 | Thread safety, move semantics |
| Reliability (unit) | 35 | Health status, error formats, timeouts |
| Basic functions, COM, callbacks | 27 | Version, bounds, input validation |
| **Total** | **205** | **100% pass rate** |

------------------------------------------------------------------------

## 7. Métricas del Proyecto

| Métrica | Valor |
|:---|:---|
| Archivos C++ (source) | ~60 (.cc/.cpp) |
| Archivos C++ (headers) | ~40 (.h/.hpp) |
| Funciones Excel registradas | ~125 |
| Tests automatizados | 205 |
| Notebooks Pluto precargados | 15 |
| Funciones R (libreria/R/) | ~90 procedimientos en 9 módulos |
| Funciones Julia (libreria/JULIA/) | 61 procedimientos en 9 funciones |
| Líneas de código estimadas | ~25,000 (C++ core) |

------------------------------------------------------------------------

## 8. Pendientes y Trabajo Futuro

| Pendiente | Prioridad | Complejidad |
|:---|:---|:---|
| Viewer reuse (actualizar contenido sin crear nuevo) | Media | Media — Navigate + cache invalidation |
| PLUTO.READ (Pluto --> Excel via TSV) | Media | Baja — patrón inverso de PLUTO.DATA |
| CI/CD pipeline | Baja | Media — GitHub Actions + CMake |
| Ribbon COM Add-in (reemplazar CommandBar) | Baja | Alta — requiere VSTO o COM registration |
| Idioma toggle (ES/EN) en toolbar | Baja | Baja — RemoveMenu + CreateMenu |
| ControlBase refactoring | Baja | Alta — riesgo de romper 3 procesos hijo |
| Instalador MSI/NSIS | Media | Media — script PowerShell existe como base |

------------------------------------------------------------------------

## 9. Conclusión

NEVEN v2.0 ha evolucionado de un prototipo monolítico (4.3/10) a un sistema modular de producción (9.1/10). La arquitectura de 4 capas permite:

- **Extensibilidad:** agregar nuevos lenguajes o subsistemas sin modificar el core
- **Estabilidad:** procesos aislados, health monitoring, retry con límites
- **Interactividad:** WebView2 para Plotly, Pluto notebooks, Quarto reportes, editor de presentaciones
- **Usabilidad:** toolbar con botones, funciones de celda intuitivas, pipeline de datos directo

El ecosistema R + Julia + Quarto + Pluto + WebView2 dentro de Excel es una contribución original que supera las capacidades de BERT (el proyecto base) en todas las dimensiones evaluadas.

------------------------------------------------------------------------

*Reporte actualizado el 23 de abril de 2026.*
*NEVEN — Universidad de Costa Rica, Tesis de Maestría.*
