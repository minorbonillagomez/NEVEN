# Explicacion Completa del Proyecto NEVEN v2.0

## Guia Tecnica para Desarrolladores

**Fecha**: 27 de abril de 2026

------------------------------------------------------------------------

## 1. Que es NEVEN

NEVEN es un **add-in XLL de Excel** que integra R, Julia, WebView2, Pluto.jl y Quarto en un ecosistema unificado. Permite al usuario:

- Llamar funciones de R y Julia desde formulas de Excel (`=R.func()`, `=J.func()`)
- Visualizar graficos interactivos (Plotly, ggplot2, D3.js) en WebView2
- Trabajar con notebooks reactivos de Pluto.jl
- Generar reportes profesionales con Quarto
- Todo controlado desde un Ribbon COM nativo

------------------------------------------------------------------------

## 2. Arquitectura

```
Excel (Host)
  |
  +-- NEVEN64.xll (XLL Add-in)
  |     |
  |     +-- RJ2XCL_Engine (singleton principal)
  |     +-- basic_functions (~200 funciones exportadas)
  |     +-- ConfigService, LanguageManager, SecurityService
  |     +-- ViewerManager (WebView2, STA thread)
  |     +-- PlutoManager (Pluto.jl lifecycle)
  |     +-- ContentPipeline, PostMessageBridge
  |     +-- CrashHandler (telemetria local)
  |
  +-- NEVENRibbon.dll (COM Add-in)
  |     +-- IRibbonExtensibility + IDTExtensibility2
  |     +-- 13 botones, iconos PNG de R/Julia/Quarto
  |
  +-- Named Pipes (Protobuf)
  |     +-- ControlR.exe --> R 4.4.1
  |     +-- ControlJulia.exe --> Julia 1.12.6
  |
  +-- WebView2 (Edge Chromium, STA thread)
  +-- Pluto.jl (proceso Julia separado, puerto 1234)
  +-- Quarto CLI (CreateProcess externo)
```

### Flujo de datos

```
Excel XLOPER12 <--> Convert <--> Protobuf Variable <--> R SEXP / Julia jl_value_t
```

------------------------------------------------------------------------

## 3. Estructura de Directorios del Codigo Fuente

```
NEVEN/
|-- CMakeLists.txt              # Build principal
|-- Common/                     # Servicios compartidos (25+ archivos)
|   |-- ConfigService.cc/h      # Configuracion centralizada
|   |-- LanguageManager.cc/h    # Orquestacion de lenguajes
|   |-- ViewerManager.cc/h      # WebView2 lifecycle
|   |-- ViewerWindow.cc/h       # Ventana Win32 + WebView2
|   |-- PlutoManager.cc/h       # Pluto.jl lifecycle
|   |-- ContentPipeline.cc/h    # Routing HTML
|   |-- PostMessageBridge.cc/h  # JS <-> C++
|   |-- NotebookLibrary.cc/h    # 15 notebooks Pluto
|   |-- MenuService.cc/h        # CommandBar (legacy)
|   |-- SandboxVerifier.cc/h    # Seguridad
|   |-- SecurityService.cc/h    # SHA-256
|   |-- LogService.cc/h         # Logging estructurado
|   |-- pipe.cc/h               # Named Pipes
|   |-- json11/                 # Parser JSON
|   +-- ...
|-- NEVEN/                     # Modulo XLL principal
|   |-- src/
|   |   |-- NEVEN.cc           # Singleton, Init, xlAutoOpen
|   |   |-- basic_functions.cc  # ~200 funciones exportadas
|   |   |-- excel_api_functions.cc # Registro en Excel
|   |   |-- language_service.cc # Comunicacion con procesos hijo
|   |   |-- rj2xcl_graphics.cc  # Graficos PNG en Shapes
|   |   |-- com_object_map.cc   # Objetos COM
|   |   +-- ...
|   +-- include/
|       |-- NEVEN.h            # RJ2XCL_Engine singleton
|       |-- basic_functions.h   # Descriptores de funciones
|       +-- ...
|-- ControlR/                   # Proceso hijo R
|   |-- src/controlr.cc         # main(), pipe loop
|   |-- src/rinterface_win.cc   # R embedding (R 4.4.1)
|   +-- include/R_ext/Complex.h # Fix MSVC (double _Complex)
|-- ControlJulia/               # Proceso hijo Julia
|   |-- src/control_julia.cc    # main(), pipe loop
|   +-- src/julia_interface.cc  # Julia embedding (1.12.6)
|-- Ribbon/                     # COM Add-in
|   |-- ribbon_connect.h        # IRibbonExtensibility
|   |-- ribbon_ui.xml           # Layout XML (5 grupos)
|   |-- NEVENRibbon_utf8.rc   # Recursos PNG
|   +-- CMakeLists.txt
|-- PB/                         # Protocol Buffers
|   +-- variable.proto          # Schema de comunicacion
|-- startup/                    # Scripts de inicio
|   |-- startup.r               # Funciones internas R
|   +-- startup.jl              # Modulo NEVEN Julia + data exchange
|-- notebooks/                  # 15 notebooks Pluto
|-- docs/                       # Documentacion (10+ documentos)
|-- Examples/                   # Ejemplos de usuario
|-- tests/                      # 205 tests (GTest)
+-- libreria/R/                  # Funciones R (~90 procedimientos)
+-- libreria/JULIA/              # Funciones Julia (~70 procedimientos)
```

------------------------------------------------------------------------

## 4. Sistema de Build (CMake)

### Requisitos
- Visual Studio 2022 (C++ desktop)
- CMake 3.15+
- R 4.4.1+ y Julia 1.12.6+ instalados

### Targets de build

| Target | Tipo | Output |
|:---|:---|:---|
| `libprotobuf` | Static | Descargado via FetchContent (v21.12) |
| `PB` | Static | variable.pb.cc |
| `Common` | Static | 25+ servicios |
| `ControlR` | Executable | ControlR.exe |
| `ControlJulia` | Executable | ControlJulia.exe |
| `NEVEN_Core` | Shared (DLL) | NEVEN.dll -> NEVEN64.xll |
| `NEVENRibbon` | Shared (DLL) | NEVENRibbon.dll (COM) |
| `neven_tests` | Executable | 205 tests GTest |

### Comandos

```powershell
# Compilar todo
cmake --build Build --config Release --parallel

# Solo Ribbon
cmake --build Build --config Release --target NEVENRibbon

# Solo tests
cmake --build Build --config Release --target neven_tests
.\Build\tests\Release\neven_tests.exe
```

------------------------------------------------------------------------

## 5. Comunicacion Inter-procesos

### Named Pipes + Protobuf

Cada lenguaje tiene su propio pipe bidireccional:
- Main pipe: Excel <-> ControlR/Julia (llamadas sincronas)
- Callback pipe: ControlR/Julia -> Excel (graficos, COM)

Los mensajes se serializan con Protocol Buffers (`variable.proto`):

| Mensaje | Proposito |
|:---|:---|
| `Variable` | Tipo universal: nil, int, real, string, bool, array, error |
| `CallResponse` | Peticion/respuesta: codigo, funcion, resultado |
| `CompositeFunctionCall` | Llamada a funcion con argumentos |
| `GraphicsUpdate` | Actualizacion de graficos (nombre, path, dimensiones) |

### WebView2 (STA Thread)

WebView2 requiere COM apartment threading. Se ejecuta en un thread dedicado:
- `WM_APP_CREATE_VIEWER` -> crea ventana + controller
- `WM_APP_SEND_MESSAGE` -> PostWebMessageAsJson
- `WM_APP_CLOSE_VIEWER` -> destruye ventana

### Pluto.jl (Archivo TSV)

Pluto corre en un proceso Julia separado. La comunicacion es via archivo:
- Excel -> Julia (pipe): `NEVEN.set_data("nombre", matrix)`
- Julia -> TSV: `C:\NEVEN\data\nombre.tsv`
- Pluto -> TSV: lee el archivo directamente

------------------------------------------------------------------------

## 6. Registro de Funciones en Excel

### Mecanismo XLL

```cpp
Excel12v(xlfRegister, &register_id, 16, &arguments[0]);
```

Cada funcion tiene:
- Nombre en Excel (ej: `R.MR_Lineal`, `J.Algebra`)
- Tipo de argumentos (`UQ` = 1 arg, `UQQQ` = 3 args)
- Tipo 1 (worksheet function) o Tipo 2 (command)
- Categoria y descripcion para el Asistente de Funciones

### Archivo .def

`NEVEN.def` exporta ~2000 simbolos: funciones basicas, placeholders BFC(1000-2023), y funciones del sistema.

------------------------------------------------------------------------

## 7. Seguridad

### Sandbox (SandboxVerifier)
- 30+ patrones bloqueados por lenguaje
- Whitespace stripping contra bypass
- String concatenation detection
- Solo aplica a `=NEVEN.r("...")` y `=NEVEN.j("...")`

### Config Validation
- Path traversal bloqueado (..)
- Command injection chars bloqueados (|, &, ;, `)
- Rangos validados con clamping

### WebView2 Navigation Filter
- Whitelist: file://, about:blank, data:, blob:, CDNs confiables
- localhost solo en Advanced Mode (Pluto)

------------------------------------------------------------------------

## 8. Fixes Criticos (No Revertir)

| Fix | Archivo | Impacto si se revierte |
|:---|:---|:---|
| Firma MdCallBack12 | xlcall_stubs.cc | Todas las llamadas Excel API fallan |
| Complex.h para MSVC | ControlR/include/R_ext/Complex.h | ControlR crashea |
| thread_local XLOPER12 | basic_functions.cc | Corrupcion en recalculo paralelo |
| Startup wait=true | language_service.cc | Pipe se desincroniza |
| CharacterMode=LinkDLL | rinterface_win.cc | ControlR crashea sin consola |
| Export RJ_FunctionCall | excel_api_functions.cc | Funciones no se registran |

------------------------------------------------------------------------

## 9. Metricas del Proyecto

| Metrica | Valor |
|:---|:---|
| Archivos C++ (source) | ~60 |
| Archivos C++ (headers) | ~40 |
| Funciones Excel registradas | ~200 |
| Tests automatizados | 205 |
| Notebooks Pluto | 15 |
| Funciones R (libreria/R/) | ~90 procedimientos |
| Funciones Julia | ~75 procedimientos + aliases |
| Score de calidad | 9.2/10 |

------------------------------------------------------------------------

*NEVEN v2.0 -- Universidad de Costa Rica -- Tesis de Maestria*
