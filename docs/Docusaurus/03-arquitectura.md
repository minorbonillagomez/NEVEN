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
