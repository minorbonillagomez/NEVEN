# NEVEN-BOOK — Manual Técnico Completo del Proyecto

> **Propósito:** Documento de referencia exhaustivo para que un desarrollador que llega por primera vez al proyecto pueda entenderlo, reproducirlo, depurarlo y extenderlo sin depender de ninguna otra fuente.
>
> **Versión:** NEVEN v2.2 — Agosto 2026
> **Autor del sistema:** Minor Bonilla Gómez, Universidad de Costa Rica
> **Repositorio:** https://github.com/minorbonillagomez/NEVEN.git

---

## Tabla de Contenidos

1. [¿Qué es NEVEN?](#1-qué-es-neven)
2. [Visión de alto nivel — dos modos de uso](#2-visión-de-alto-nivel)
3. [Estructura del repositorio](#3-estructura-del-repositorio)
4. [Arquitectura del sistema](#4-arquitectura-del-sistema)
5. [Protocolo IPC — Protocol Buffers + Named Pipes](#5-protocolo-ipc)
6. [NEVEN64.xll — el Add-in de Excel](#6-neven64xll)
7. [ControlR.exe — motor R](#7-controlrexe)
8. [ControlJulia.exe — motor Julia](#8-controljuliaexe)
9. [ControlPython.exe — motor Python](#9-controlpythonexe)
10. [NEVENRibbon.dll — pestaña COM](#10-nevenribbondll)
11. [NEVEN Studio — servidor standalone](#11-neven-studio)
12. [Data Lab — análisis punto-y-clic](#12-data-lab)
13. [Data Studio — exploración de datos](#13-data-studio)
14. [Run Script — editor de scripts](#14-run-script)
15. [Creador de Presentaciones](#15-creador-de-presentaciones)
16. [Librería R (R4XCL)](#16-librería-r-r4xcl)
17. [Librería Julia (J4XCL)](#17-librería-julia-j4xcl)
18. [Seguridad](#18-seguridad)
19. [Sistema de configuración](#19-sistema-de-configuración)
20. [Build system](#20-build-system)
21. [Testing](#21-testing)
22. [Instalación y despliegue](#22-instalación-y-despliegue)
23. [Guía de resolución de problemas](#23-guía-de-resolución-de-problemas)
24. [Convenciones de código](#24-convenciones-de-código)
25. [Glosario](#25-glosario)

---

## 1. ¿Qué es NEVEN?

NEVEN es una plataforma multilenguaje para análisis de datos que integra R 4.4.1, Julia 1.12.6 y Python 3.13 en dos contextos:

1. **Add-in XLL de Microsoft Excel**: el usuario escribe `=R.MR_Lineal(Y, X, 1)` en una celda y obtiene un modelo de regresión. Las funciones de R/Julia/Python se exponen como fórmulas nativas de Excel.

2. **NEVEN Studio Standalone**: una interfaz web accesible en `http://localhost:5555` que expone Data Lab (análisis punto-y-clic), Run Script (editor de scripts), Data Studio (explorador de datos con SQL) y el Creador de Presentaciones. No requiere Excel instalado.

NEVEN es la evolución de BERT (Basic Excel R Toolkit, Structured Data LLC, 2017-2018), modernizado para R 4.4.1 y Julia 1.12.6, con seguridad, testing y visualización interactiva vía WebView2.

### Problema que resuelve

Excel es universal pero estadísticamente limitado. R y Julia son potentes pero requieren programación. NEVEN cierra esta brecha: el analista que sabe Excel puede usar modelos estadísticos avanzados sin escribir código.

### Lo que NEVEN NO es

- No es una aplicación web en la nube (todo corre localmente en Windows)
- No es un wrapper simple de R — es un sistema multi-proceso con IPC, sandboxing, RAII y 357 tests
- No funciona en macOS/Linux (usa Named Pipes de Windows, COM, WebView2)

---

## 2. Visión de Alto Nivel

### Modo 1: Add-in Excel

```
Usuario escribe =R.MR_Lineal(Y, X, 1) en celda
    ↓
Excel invoca RJ_FunctionCall1000 en NEVEN64.xll
    ↓
NEVEN64.xll valida input, serializa a Protobuf CallResponse
    ↓
Named Pipe \\.\pipe\neven_r → ControlR.exe
    ↓
ControlR.exe ejecuta código R via C API de R
    ↓
Resultado R → Protobuf Variable → Named Pipe → XLL
    ↓
XLL deserializa y retorna XLOPER12 a Excel
    ↓
Celda muestra resultado (tabla, escalar, HTML)
```

### Modo 2: NEVEN Studio

```
Usuario abre navegador en http://localhost:5555
    ↓
taskpane.html (HTML/JS) hace fetch a neven_http_server.py
    ↓
neven_http_server.py usa PipeClient para conectar a Control*.exe
    ↓
Control*.exe ejecuta código y retorna Variable Protobuf
    ↓
neven_http_server.py convierte Variable → JSON → respuesta HTTP
    ↓
taskpane.html renderiza resultado (tabla, Plotly, scalar)
```

---

## 3. Estructura del Repositorio

```
NEVEN/                          ← raíz del repositorio
├── Core/                       ← NEVEN.dll (add-in XLL)
│   ├── src/                    ← archivos .cc de implementación
│   │   ├── NEVEN.cc            ← punto de entrada xlAutoOpen, Init()
│   │   ├── basic_functions.cc  ← RJ_FunctionCall*, RJ_Exec_Generic
│   │   ├── excel_api_functions.cc ← registro de funciones en Excel
│   │   ├── language_manager.cc ← gestión de motores R/Julia/Python
│   │   ├── language_service.cc ← comunicación por Named Pipe
│   │   └── ...
│   └── include/                ← headers del core
├── Common/                     ← Common.lib (compartida por Core y Control*)
│   ├── ConfigService.cc/.h     ← lectura de neven-config.json
│   ├── DiscoveryService.cc/.h  ← detección de R/Julia/Python instalados
│   ├── SandboxVerifier (en Security/)
│   ├── InputSanitizer  (en Security/)
│   ├── MessageValidator (en IPC/)
│   ├── SafePipeHandle   (en IPC/)
│   ├── ViewerManager.cc/.h     ← gestión de ventanas WebView2
│   ├── REPLManager.cc/.h       ← consola REPL interactiva
│   └── ...
├── ControlR/                   ← ControlR.exe (proceso hijo R)
│   └── src/
│       ├── controlr.cc         ← main(), inicialización de R
│       └── rinterface_win.cc   ← R_ReadConsole, R_WriteConsole, RLoop()
├── ControlJulia/               ← ControlJulia.exe (proceso hijo Julia)
│   └── src/
│       ├── control_julia.cc    ← main(), pipe loop
│       └── julia_interface.cc  ← jl_eval_string, type conversion
├── ControlPython/              ← ControlPython.exe (proceso hijo Python)
│   ├── src/
│   │   ├── control_python.cc  ← main(), pipe loop
│   │   └── python_interface.cc ← Py_Initialize, PythonExec
│   └── startup/               ← scripts Python del servidor Studio
│       ├── neven_http_server.py ← servidor HTTP de NEVEN Studio
│       └── datalab_handler.py  ← handler del Data Lab
├── PB/                         ← Protocol Buffers
│   ├── variable.proto          ← definición del protocolo IPC
│   ├── variable.pb.cc          ← generado por protoc
│   └── variable.pb.h
├── Ribbon/                     ← NEVENRibbon.dll (pestaña COM de Excel)
│   ├── ribbon_connect.cc       ← OnConnection, SetPointers
│   └── ribbon_ui.xml           ← definición de botones y grupos
├── TaskPane/                   ← NEVEN Studio (frontend + servidor)
│   ├── taskpane.html           ← UI principal (Data Studio, Run Script, SQL)
│   ├── datalab.js              ← módulo Data Lab
│   ├── taskpane.css            ← estilos
│   ├── start_studio.py         ← launcher del servidor
│   ├── pipe_client.py          ← cliente de Named Pipes en Python
│   └── neven_studio_server.py  ← servidor alternativo (legacy)
├── CreadorPresentaciones/      ← Editor de presentaciones Impress.js
│   ├── index.html              ← UI del editor
│   ├── script.js               ← lógica completa (PresentationEditor)
│   └── styles.css              ← estilos
├── startup/                    ← scripts de inicialización
│   ├── startup.r               ← startup de R (NEVEN env, Extraer_outputs)
│   ├── startup.jl              ← startup de Julia (módulos J4XCL)
│   ├── startup.py              ← startup de Python (funciones AI)
│   └── r_object_to_slots.R     ← serializador de objetos R → slots Data Lab
├── libreria/
│   ├── R/                      ← ~90 funciones R4XCL (32 archivos .R)
│   ├── JULIA/                  ← ~70 procedimientos J4XCL (5 archivos .jl)
│   ├── PYTHON/                 ← funciones AI Python
│   └── EJEMPLOS/               ← ejemplos por lenguaje
├── Install/
│   ├── neven-config.json       ← configuración canónica
│   ├── neven-languages.json    ← configuración de motores de lenguaje
│   ├── functions/              ← sidecar JSON del catálogo Data Lab
│   └── Install-NEVEN.ps1       ← script de instalación
├── tests/                      ← 357 tests (GTest + rapidcheck PBT)
├── docs/                       ← documentación completa
├── CMakeLists.txt              ← build system raíz
└── Include/                    ← headers mock (R, Julia, Excel SDK)
```

---

## 4. Arquitectura del Sistema

### 4.1 Procesos y comunicación

NEVEN usa una arquitectura multi-proceso. El principio fundamental es que un crash de R o Julia no mata Excel ni Studio.

```
┌─────────────────────────────────────────────────────┐
│  Microsoft Excel (host)                              │
│  ┌─────────────────────────────────────────────┐    │
│  │  NEVEN64.xll                                 │    │
│  │  ┌──────────────┐  ┌─────────────────────┐  │    │
│  │  │LanguageManager│  │ WebView2 (STA thread)│  │    │
│  │  └──────┬───────┘  └─────────────────────┘  │    │
│  └─────────┼───────────────────────────────────┘    │
└────────────┼────────────────────────────────────────┘
             │ Named Pipes + Protocol Buffers
    ┌────────┼──────────────────────┐
    │        │                      │
┌───▼──┐ ┌──▼──────┐ ┌─────────────▼──┐
│CtrlR │ │CtrlJulia│ │  CtrlPython     │
│.exe  │ │.exe     │ │  .exe           │
│R 4.4 │ │Julia1.12│ │  Python 3.13    │
└──────┘ └─────────┘ └────────────────┘
```

Cada `Control*.exe` expone exactamente **tres Named Pipes**:
- `\\.\pipe\neven_{lang}` — pipe principal (llamadas/respuestas)
- `\\.\pipe\neven_{lang}_callback` — callbacks desde el lenguaje hacia Excel
- `\\.\pipe\neven_{lang}_extra` — pipe auxiliar (no crítico)

### 4.2 Ciclo de vida del Add-in

1. Excel carga `NEVEN64.xll` → `xlAutoOpen()` es llamado
2. `RJ2XCL_Engine::Init()` arranca:
   - Mata procesos huérfanos de sesiones anteriores (Zombie Process Killer)
   - Lee `neven-config.json` y `neven-languages.json`
   - `DiscoveryService` detecta dónde están R, Julia, Python
   - Lanza `ControlR.exe`, `ControlJulia.exe`, `ControlPython.exe` con `CreateProcess`
   - Espera conexión de cada pipe (timeout 10s por motor)
   - Envía script de startup al motor (`startup.r`, `startup.jl`, `startup.py`)
   - Motor responde con lista de funciones disponibles
   - `RegisterFunctions()` registra cada función en Excel con `xlfRegister`
3. Excel muestra las funciones `R.`, `J.`, `P.` en el asistente de funciones (Shift+F3)

### 4.3 Flujo de una llamada UDF

```
Celda: =R.MR_Lineal(A1:A100, B1:C100, 1)
        ↓
Excel invoca RJ_FunctionCall1042 (índice asignado al registrar)
        ↓
basic_functions.cc :: RJ_Exec_Generic()
  1. Convierte XLOPER12 → Variable (Protobuf)
  2. Construye CallResponse con Code{line=["MR_Lineal(Y,X,1)"]}
  3. SandboxVerifier verifica el código (si sandboxEnabled=true)
  4. Escribe frame en Named Pipe (4 bytes de longitud + payload Protobuf)
        ↓
ControlR.exe recibe el CallResponse
  1. Deserializa el Protobuf
  2. Ejecuta R_tryEval(parse(text=code))
  3. Serializa resultado como Variable Protobuf
  4. Escribe respuesta en el pipe
        ↓
XLL lee respuesta
  1. Deserializa Variable
  2. Convierte a XLOPER12
  3. Retorna a Excel
        ↓
Celda muestra resultado
```

### 4.4 WebView2

Para gráficos interactivos, el XLL usa WebView2 (Edge Chromium embebido) en un STA thread dedicado (Single-Threaded Apartment, requerido por COM). El patrón:

1. R genera HTML con Plotly/D3 y lo retorna como `HtmlContent` en el Protobuf
2. XLL recibe `html_content` → `ViewerManager` abre una ventana WebView2
3. `ContentPipeline` decide si enviar el HTML inline o vía archivo temporal (`file://`)
4. `PostMessageBridge` permite comunicación bidireccional JS ↔ C++

### 4.5 Arquitectura NEVEN Studio (standalone)

```
NEVEN Studio.vbs
    ↓
start_studio.py --no-browser
    ↓
launch_control("r", "python", "julia")
  → ControlR.exe -p neven_r
  → ControlPython.exe -p neven_python
  → ControlJulia.exe -p neven_julia
    ↓
PipeClient conecta a cada Control*.exe
    ↓
neven_http_server.py (puerto 5555) sirve:
  GET /              → taskpane.html
  GET /static/*      → assets, CSS, JS
  POST /api/run      → ejecutar código R/Julia/Python
  POST /api/datalab/run → Data Lab
  POST /api/load     → cargar CSV/JSON en DuckDB
  POST /api/query    → SQL sobre DuckDB
  POST /api/db_connect → conectar BD externa
  POST /api/save_script → guardar script
  GET /api/engines   → estado de motores
    ↓
Navegador del usuario: http://localhost:5555
```

---

## 5. Protocolo IPC — Protocol Buffers + Named Pipes

### 5.1 Framing

Cada mensaje en el pipe está prefijado con un entero de 4 bytes (signed int32, little-endian) que indica el tamaño del payload Protobuf que sigue. La función C++ es `MessageUtilities::Frame` / `MessageUtilities::Unframe`. En Python es `_frame()` / `_unframe()` en `pipe_client.py`.

```
[4 bytes: longitud] [N bytes: CallResponse serializado]
```

El límite es 256 KB (`kMaxDynamicBufferSize`). Mensajes más grandes se rechazan con `PipeProtocolError`.

### 5.2 El mensaje raíz: `CallResponse`

```protobuf
message CallResponse {
  uint32 id = 1;
  bool wait = 2;      // true = esperar respuesta sincrónicamente
  oneof operation {
    string err = 3;             // error de ejecución
    Variable result = 4;        // resultado
    Console console = 5;        // output de consola (cat/print)
    Code code = 6;              // código a ejecutar
    string shell_command = 7;   // comando de consola
    CompositeFunctionCall function_call = 8;  // llamada a función
    FunctionList function_list = 9;   // lista de funciones del motor
    uint32 user_command = 10;   // comandos del sistema
  }
  string console_output = 11;   // stdout capturado (Python)
  string console_error_output = 12; // stderr capturado (Python)
}
```

**Para ejecutar código:** se envía `CallResponse{wait=true, code=Code{line=["R_code_here"]}}`.

**Para listar funciones:** se envía `CallResponse{function_call=CompositeFunctionCall{function="list-functions", target=system}}`.

### 5.3 El tipo `Variable`

```protobuf
message Variable {
  oneof value {
    bool nil = 1;
    bool missing = 2;
    Error err = 3;
    int32 integer = 5;
    double real = 6;
    string str = 7;
    bool boolean = 8;
    Complex cpx = 9;
    Array arr = 10;      // tablas, matrices, data.frames
    SheetReference ref = 11;
    ExternalPointer com_pointer = 12;
    GraphicsUpdate graphics = 13;
    uint32 cache_reference = 14;
    HtmlContent html_content = 16;  // para WebView2
  }
  string name = 15;
}
```

**Tipo `Array`** (el más importante):
```protobuf
message Array {
  int32 rows = 1;
  int32 cols = 2;
  repeated Variable data = 3;  // flat, row-major: data[r*cols + c]
  repeated string rownames = 4;
  repeated string colnames = 5;
}
```

Un data.frame de R con N filas y 5 columnas se serializa como `Array{rows=N, cols=5, data=[N*5 Variables], colnames=["col1","col2",...]}`.

### 5.4 Pipe names

| Motor | Pipe principal | Callback pipe |
|:---|:---|:---|
| R | `\\.\pipe\neven_r` | `\\.\pipe\neven_r_callback` |
| Julia | `\\.\pipe\neven_julia` | `\\.\pipe\neven_julia_callback` |
| Python | `\\.\pipe\neven_python` | `\\.\pipe\neven_python_callback` |

En NEVEN Studio, los pipes se manejan desde Python con `PipeClient` en `pipe_client.py`. En el XLL, los pipes los maneja `LanguageService` en C++.

---

## 6. NEVEN64.xll

El XLL es el componente central del modo Excel. Es una DLL renombrada con extensión `.xll`.

### 6.1 Punto de entrada

```cpp
// Core/src/NEVEN.cc
int xlAutoOpen() {
    // 1. Guard contra doble inicialización
    static bool already_initialized = false;
    if (already_initialized) return 1;
    already_initialized = true;

    // 2. Inicializar el engine singleton
    RJ2XCL_Engine::GetInstance().Init();
    return 1;
}
```

### 6.2 Clase principal: `RJ2XCL_Engine`

```cpp
class RJ2XCL_Engine {
public:
    static RJ2XCL_Engine& GetInstance();  // singleton
    void Init();            // arranca todo
    void SetPointers(IDispatch* app, IDispatch* book); // invocado por Ribbon
    LanguageManager& GetLanguageManager();
    ViewerManager& GetViewerManager();
    // ...
};
```

`Init()` hace (en este orden):
1. Zombie Process Killer: `CreateProcess("taskkill /F /IM ControlR.exe", CREATE_NO_WINDOW)`
2. Cargar `neven-config.json` vía `ConfigService`
3. Cargar `neven-languages.json` vía `DiscoveryService`
4. Crear directorios de usuario si no existen (`CreateDirectoryA` recursivo)
5. `LanguageManager::ConnectLanguages()` — lanza y conecta los motores
6. Enviar startup scripts (espera respuesta sincrónicamente con `set_wait(true)`)
7. `MapFunctions()` — obtiene lista de funciones de cada motor
8. `RegisterFunctions()` — registra en Excel vía `xlfRegister`

> **Bug histórico importante:** `xlfRegister` solo funciona durante `xlAutoOpen`. No se puede llamar desde un timer (`WM_TIMER`) ni desde un hilo de background. Intentarlo causa que Excel cuelgue.

### 6.3 Funciones UDF: slots estáticos

El archivo `.def` exporta funciones con nombres predefinidos:
```
RJ_FunctionCall1000
RJ_FunctionCall1001
...
RJ_FunctionCall2860
```

Cada función registrada en Excel se asigna a uno de estos slots en tiempo de inicio. Cuando Excel invoca `RJ_FunctionCall1042`, el XLL sabe qué función de qué motor corresponde a ese índice.

### 6.4 `basic_functions.cc`

Implementa la lógica central de las UDFs:

```cpp
// Ejemplo simplificado
LPXLOPER12 RJ_Exec_Generic(int idx, LPXLOPER12 args[], int nargs) {
    // 1. Obtener la función registrada en el slot idx
    auto& func = language_manager.GetFunctionAtIndex(idx);

    // 2. Convertir XLOPER12[] → vector<Variable>
    auto vars = ConvertArguments(args, nargs);

    // 3. Validar con SandboxVerifier si es código arbitrario
    if (func.IsArbitrary()) {
        if (!SandboxVerifier::Validate(code)) {
            return MakeErrorString("Code blocked by sandbox");
        }
    }

    // 4. Enviar al motor correspondiente
    auto result = language_manager.Call(func.language, code, vars);

    // 5. Convertir Variable → XLOPER12 y retornar
    thread_local XLOPER12 result_oper;  // thread_local evita race conditions
    result_oper = ConvertToXloper(result);
    return &result_oper;
}
```

> **Importante:** Las variables de resultado son `thread_local` (no `static`). Con `static`, llamadas paralelas de Excel corromperían los resultados. El `thread_local` fue un fix crítico de seguridad.

### 6.5 Type conversion: `XLOPER12` ↔ `Variable`

| XLOPER12 type | Variable Protobuf |
|:---|:---|
| `xltypeNum` | `real` (double) |
| `xltypeInt` | **`real`** (no `integer`) — R no soporta int64 de Excel |
| `xltypeStr` | `str` |
| `xltypeBool` | `boolean` |
| `xltypeNil` | `nil` |
| `xltypeMulti` (range) | `arr` (Array row-major) |
| `xltypeErr` | `err` |

### 6.6 `RaiiXlOper` — RAII para memoria Excel

```cpp
class RaiiXlOper {
public:
    explicit RaiiXlOper(XLOPER12* p) : ptr_(p) {}
    ~RaiiXlOper() { if (ptr_) Excel12(xlFree, nullptr, 1, ptr_); }
    RaiiXlOper(const RaiiXlOper&) = delete;
    RaiiXlOper(RaiiXlOper&&) noexcept;
    XLOPER12* get() { return ptr_; }
private:
    XLOPER12* ptr_ = nullptr;
};
```

Siempre que el XLL recibe un `XLOPER12` de Excel (p.ej. resultado de `xlfCoerce`), lo envuelve en `RaiiXlOper` para garantizar que `xlFree` sea llamado incluso si hay excepciones.

---

## 7. ControlR.exe

### 7.1 Arquitectura interna

```
main()
  ├── Parsear argumentos: -p pipe_name -r r_home
  ├── Crear pipe de management (non-blocking)
  ├── Conectar pipe principal (blocking — espera al XLL)
  ├── Enviar confirmación de conexión
  └── RLoop(r_home)
        ├── R_DefParams() + R_SetParams()   # configura R
        ├── setup_Rmainloop()               # inicializa R internamente
        ├── RegisterCallbacks()              # NEVEN.Callback en R
        └── run_Rmainloop()                 # REPL loop de R
              └── pipe_loop()               # lee CallResponse del pipe
                    ├── Code → R_tryEvalSilent()
                    ├── function_call → dispatch
                    └── Serializar Variable → respuesta
```

### 7.2 Compatibilidad con R 4.4.1

R 4.4.1 introdujo cambios de API incompatibles con BERT/versiones anteriores:

- **`double _Complex`**: R 4.2+ usa `double _Complex` en `Rcomplex` (C99, no soportado por MSVC en C++). Fix: header `ControlR/include/R_ext/Complex.h` que define `Rcomplex` como `struct {double r; double i;}` interceptando el include original.
- **`R_ReadConsole`**: la firma cambió de `char*` a `unsigned char*` en R 4.4.1. Actualizado en `rinterface_win.cc`.
- **`structRstart`**: tiene campos adicionales en R 4.4.1 (`vsize`, `nsize`, `EmitEmbeddedUTF8`, etc.). Si se usa el struct viejo, `R_DefParams()` escribe fuera de límites y crashea. Fix: usar los headers reales de R 4.4.1 con `target_include_directories(BEFORE)`.
- **`CharacterMode`**: cambiado de `RTerm` a `LinkDLL` para que R no intente inicializar GUI sin consola.

### 7.3 Localización de R

1. `neven-config.json → NEVEN.R.home` (si está configurado)
2. Registro de Windows: `HKLM\SOFTWARE\R-core\R\InstallPath`
3. Default: `C:\Program Files\R\R-4.4.1`

La ruta se convierte a formato 8.3 (`GetShortPathNameW`) para evitar espacios en los argumentos de línea de comandos.

### 7.4 Startup de R

Al conectar, el XLL envía el contenido de `startup.r` como `Code{startup=true}`. El motor lo ejecuta y responde. El `set_wait(true)` es crítico — sin él, el pipe queda en estado inconsistente porque el motor enviaría una respuesta que nadie leería.

`startup.r` define:
- El entorno `NEVEN` (namespace interno)
- `NEVEN$install.application.pointer(p)` — para callbacks COM
- `BERT.graphics.device()` — capa de compatibilidad con BERT
- `NEVEN$list.functions()` — introspección de funciones de usuario
- `Extraer_outputs(modelo)` — extractor universal de outputs de modelos
- Fuente de `r_object_to_slots.R` — serializador para Data Lab

---

## 8. ControlJulia.exe

### 8.1 Compatibilidad con Julia 1.12.6

Julia 1.12.6 cambió ~50 funciones de API respecto a Julia 0.6 (la versión que usaba BERT). El header `ControlJulia/include/julia_compat.h` contiene 10+ macros de traducción:

```cpp
// Ejemplos de cambios de API:
// Julia 0.6           → Julia 1.12
// jl_arrayset()       → eliminado (usar jl_array_ptr_set)
// jl_options.handle_signals → campo eliminado
// JL_STDOUT/STDERR    → cambió de tipo
// jl_array_data()     → ahora retorna void* en vez de T*
// jl_current_exception() → nueva firma
```

### 8.2 Sysimage precompilada

Para eliminar el cold start de Julia (JIT compilation tarda 1-5 minutos), NEVEN genera una sysimage precompilada:

```bash
julia scripts/build-julia-sysimage.jl
# Genera: C:\NEVEN\neven_julia.dll (~415 MB)
```

`ControlJulia.exe` detecta si existe `neven_julia.dll` en su directorio:
- Si existe: `jl_init_with_image("C:/NEVEN", "neven_julia.dll")` → Julia arranca en ~1-2 segundos
- Si no existe: `jl_init()` estándar → Julia arranca en ~1-5 minutos

### 8.3 Librería J4XCL

Los módulos Julia exponen 9 namespaces a Excel con el prefijo `J.`:

| Función Excel | Módulo | Procedimientos |
|:---|:---|:---|
| `=J.Algebra(rango, vector, tipo)` | Álgebra lineal | 12: LU, QR, SVD, eigenvalores, det, etc. |
| `=J.Estadistica(datos, Y, tipo)` | Estadística | 8: descriptiva, correlación, t-test |
| `=J.Regresion(X, Y, param, tipo)` | Regresión | 5: coeficientes, predicción, residuos |
| `=J.KNN(X, Y, K, tipo)` | Clasificación KNN | 5: clasificación, F1, confusion matrix |
| `=J.Clustering(datos, K, seed, tipo)` | K-Medias | 6: asignación, centros, codo |
| `=J.Calculo(X, Y, param, tipo)` | Cálculo numérico | 7: derivadas, integrales |
| `=J.EDO(intervalo, CI, h, tipo)` | EDOs | 4: Euler, RK4, oscilador |
| `=J.Optimizar(A, b, lr, iter, tipo)` | Optimización | 7: gradiente, Newton, simplex |
| `=J.Transformar(datos, col, val, tipo)` | Transformaciones | 6: filtrar, ordenar, transponer |

---

## 9. ControlPython.exe

### 9.1 Stable ABI

Python se compila usando la Stable ABI (`python3.dll` en lugar de `python3XX.dll`) para que el binario funcione con cualquier versión de Python 3.x sin recompilar.

### 9.2 Funciones AI

Las funciones `P.ai_*` permiten enviar datos a un LLM:

```python
# En startup/startup.py
def ai_call(data_str, prompt_name="interpretar_regresion"):
    """Envía datos al LLM configurado y retorna interpretación textual."""
    # Lee el prompt template de C:\NEVEN\prompts\{prompt_name}.txt
    # Construye el mensaje y hace HTTP POST al endpoint configurado
    # Soporta: OpenAI, Ollama (local), LM Studio (local)
```

Configuración en `neven-config.json`:
```json
"AI": {
    "provider": "lmstudio",
    "endpoint": "http://localhost:1234/v1/chat/completions",
    "model": "nvidia/nemotron-3-nano-4b",
    "promptsDirectory": "C:\\NEVEN\\prompts"
}
```

### 9.3 Estabilización de ControlPython

ControlPython fue congelado temporalmente y requirió 4 fixes críticos para estabilizarse:
1. **Startup retry**: `PythonInit()` reintenta si `Py_Initialize()` falla en el primer intento
2. **SEH stack guard**: `__try/__except` alrededor del main pipe loop para capturar excepciones de Windows (ACCESS_VIOLATION, STACK_OVERFLOW)
3. **Single-block sending**: el frame entero se envía en una sola `WriteFile` — enviar header y payload en llamadas separadas causaba corrupción del protocolo
4. **Health check**: `GetExitCodeProcess` verifica que el proceso siga vivo antes de cada I/O

---

## 10. NEVENRibbon.dll

COM Add-in separado del XLL. Expone la pestaña "NEVEN" en la cinta de Excel con 13 botones en 5 grupos.

### 10.1 Grupos y botones

| Grupo | Botones |
|:---|:---|
| Motores | Consola R, Consola Julia, Actualizar, Instalar Paquete R/Julia |
| Visualización | Abrir HTML, Presentaciones, Cerrar Visores |
| Pluto.jl | Iniciar Pluto, Notebooks, Detener Pluto |
| Quarto | Renderizar QMD |
| Configuración | Carpeta Scripts, Config JSON, Acerca de |

### 10.2 Comunicación con el XLL

El Ribbon llama `RJ_SetPointers(IDispatch* app, IDispatch* book)` exportada por el XLL para obtener los punteros COM de la aplicación Excel. Esta función puede ser invocada antes de que todos los motores conecten — por eso verifica el estado antes de llamar `SetApplicationPointer()` en cada servicio.

```cpp
// Core/src/NEVEN.cc
void RJ2XCL_Engine::SetPointers(IDispatch* app, IDispatch* book) {
    for (auto& service : language_services_) {
        if (service.IsConnected()) {  // ← verificación crítica
            service.SetApplicationPointer(app, book);
        }
        // Si no está conectado, se omite sin error
    }
}
```

Sin esta verificación, el Ribbon podría llamar `SetPointers` antes de que ControlR esté listo y causar un hang.

---

## 11. NEVEN Studio — Servidor Standalone

### 11.1 Arranque

El usuario lanza `NEVEN Studio.vbs` (doble clic), que:
1. Mata `ControlR.exe`, `ControlJulia.exe`, `ControlPython.exe` (procesos huérfanos)
2. Pausa 2 segundos (libera el mutex de instancia)
3. Ejecuta: `python start_studio.py --no-browser` desde `C:\NEVEN\taskpane\`
4. Espera hasta 45 segundos a que el servidor escuche en el puerto 5555
5. Abre `http://localhost:5555` en el navegador por defecto

### 11.2 `start_studio.py`

Responsabilidades:
- **Mutex de instancia única**: `CreateMutex("Global\\NEVEN_Studio_Launcher")` — previene dos instancias simultáneas. Si el mutex está ocupado, el proceso termina con error descriptivo.
- **Carga de config**: `load_config(path)` lee `neven-config.json`. Si no existe, usa defaults.
- **Resolución de lenguajes**: `resolve_languages(config, arg)` decide qué motores iniciar.
- **Descubrimiento de ejecutables**: `find_exe(config, lang)` busca `ControlR.exe`, etc.
- **Lanzamiento de motores**: `launch_control(exe, lang, config)` con `subprocess.Popen`.
  - Para R: prepend `R\bin\x64` al PATH, argumento `-r <R_HOME>`
  - Para Julia: setea `JULIA_BINDIR`, prepend bin al PATH
  - Paths con espacios se convierten a 8.3 con `GetShortPathNameW`
- **Espera de pipes**: `wait_for_pipes(processes, timeout=10.0)` hace `CreateFile` cada 100ms hasta que el pipe esté disponible.
- **Archivo PID**: `write_pid_file(config, processes, os.getpid())` — JSON con PIDs de todos los procesos.
- **Servidor HTTP**: `start_server(config, pipe_clients)` inicia `neven_http_server.py` en un hilo daemon.

### 11.3 `neven_http_server.py`

Servidor HTTP construido sobre `http.server.BaseHTTPRequestHandler`. Maneja:

| Endpoint | Método | Descripción |
|:---|:---|:---|
| `/` | GET | Sirve `taskpane.html` |
| `/static/*` | GET | Archivos estáticos (CSS, JS, imágenes) |
| `/api/run` | POST | Ejecuta código R/Julia/Python |
| `/api/datalab/run` | POST | Ejecuta función del Data Lab |
| `/api/datalab/functions` | GET | Lista funciones del catálogo |
| `/api/load` | POST | Carga datos en DuckDB (CSV/JSON/array) |
| `/api/query` | POST | Ejecuta SQL en DuckDB |
| `/api/stats` | GET | Estadísticas descriptivas del dataset |
| `/api/groupby` | POST | GROUP BY del dataset |
| `/api/db_connect` | POST | Conecta BD externa (PG/MySQL/SQLite/MSSQL) |
| `/api/save_script` | POST | Guarda script al filesystem |
| `/api/engines` | GET | Estado de motores (conectados/desconectados) |
| `/api/read_excel` | POST | Lee Excel via openpyxl |
| `/api/ai/call` | POST | Llama al LLM con datos + prompt |
| `/presentaciones/*` | GET | Sirve el Creador de Presentaciones |

### 11.4 `pipe_client.py` — el puente

`PipeClient` implementa el protocolo framing C++ en Python:

```python
class PipeClient:
    def connect(self):
        """Abre CreateFile al Named Pipe."""
        # Usa pywin32 si está disponible, sino ctypes
    
    def send_code(self, lines: list, wait=True) -> Variable:
        """Envía código y retorna el resultado."""
        msg = CallResponse(wait=wait, code=Code(line=lines))
        self._write_all(_frame(msg))  # 4 bytes + payload
        return self._read_response()
    
    def _read_response(self) -> Variable:
        """Lee 4 bytes de longitud + payload Protobuf."""
        header = self._read_exact(4)
        length = struct.unpack("<i", header)[0]
        payload = self._read_exact(length)
        response = CallResponse()
        response.ParseFromString(payload)
        if response.HasField("err"):
            raise PipeClientError(response.err)
        return response.result
```

`variable_to_python(var)` convierte el resultado a Python nativo:
- `integer/real` → `int/float`
- `str` → `str`
- `arr` → `{"columns": [...], "rows": [[...], ...]}` (formato row-major)
- `html_content` → `{"html": "...", "title": "..."}`

---

## 12. Data Lab — Análisis Punto-y-Clic

### 12.1 Arquitectura

```
datalab.js (browser)
  selectFunction(id)    → carga sidecar JSON, renderiza formulario
  runAnalysis()         → POST /api/datalab/run
                          { function_id, column_roles, parameters, dataset_cols }
        ↓
datalab_handler.py
  handle_run()
    _build_r_script()   → construye código R con source() + llamada .Studio()
    ControlR ejecuta    → retorna Variable (Array con slots)
    _parse_slots_from_variable() → convierte Array → lista de slots
        ↓
datalab.js
  renderResults(slots)  → buildSlotElement(slot) por cada slot
```

### 12.2 Sidecar JSON Convention

Cada función del catálogo tiene un archivo `.json` co-ubicado con el `.Studio.R`:

```
C:\NEVEN\functions\
  AD_KMedias.Studio.R      ← implementación R
  AD_KMedias.json          ← sidecar (descripción de la interfaz)
```

Estructura del sidecar JSON:
```json
{
  "id": "AD_KMedias",
  "label": "K-Medias",
  "family": "AD",
  "description": "Clustering K-Means",
  "roles": [
    {
      "id": "Variables",
      "label": "Variables a clusterizar",
      "type": "columns",
      "multiple": true,
      "required": true
    }
  ],
  "parameters": [
    {
      "id": "K",
      "label": "Número de clusters",
      "type": "number",
      "default": 3,
      "min": 2,
      "max": 20,
      "tier": 1
    },
    {
      "id": "PaletaColores",
      "label": "Paleta de colores",
      "type": "palette",
      "default": "1",
      "tier": 1
    }
  ]
}
```

Tipos de `parameter.type` disponibles:
- `number`, `text`, `boolean`, `select`, `palette`

El tipo `palette` renderiza botones con 6 swatches de color usando la paleta NEVEN (dorado).

### 12.3 `_build_r_script()` en `datalab_handler.py`

```python
def _build_r_script(function_id, column_roles, parameters, sidecar):
    """Construye el script R que ejecuta la función Studio."""
    lines = []
    
    # Forzar recarga de la función (evita caché en env NEVEN)
    lines.append(f"if(exists('FN.Studio',envir=globalenv())) rm(list='FN.Studio',envir=globalenv())")
    lines.append(f"source('C:/NEVEN/functions/{function_id}.Studio.R', local=FALSE)")
    lines.append(f"if(exists('NEVEN',envir=globalenv()) && is.environment(get('NEVEN',envir=globalenv())))")
    lines.append(f"  assign('FN.Studio', get('FN.Studio',envir=globalenv()), envir=get('NEVEN',envir=globalenv()))")
    
    # Asignar datos de columnas
    for role_id, cols in column_roles.items():
        lines.append(f"data_{role_id} <- dataset[, c({','.join(repr(c) for c in cols)})]")
    
    # Fallback para roles opcionales no asignados
    for role in sidecar.get("roles", []):
        if not role.get("required") and role["id"] not in column_roles:
            lines.append(f"data_{role['id']} <- data.frame(.idx = seq_len(nrow(dataset)))")
    
    # Filtrar parámetros contra el sidecar (evita contaminación entre funciones)
    valid_param_ids = {p["id"] for p in sidecar.get("parameters", [])}
    params_r = {k: v for k, v in parameters.items() if k in valid_param_ids}
    
    # Construir llamada .Studio()
    params_str = ", ".join(f"{k}={repr(v)}" for k, v in params_r.items())
    lines.append(f"FN.Studio(data_Variables, ..., {params_str})")
    
    return "\n".join(lines)
```

> **Bug crítico resuelto:** ControlR cachea funciones en el env `NEVEN`, no en `globalenv()`. El `source()` solo actualiza `globalenv()`. La solución es el triple bloque `rm() + source() + assign()`.

### 12.4 `_parse_slots_from_variable()` — el parser crítico

ControlR serializa un `data.frame` de N filas × 5 columnas como un `Array` flatten row-major:

```
Array{rows=N, cols=5, colnames=["name","label","type","value","tier"],
      data=[N*5 Variables]}

flat[i + j*N] = campo j del slot i
```

```python
def _parse_slots_from_variable(raw):
    """Convierte la Variable Protobuf de ControlR en lista de slots."""
    result = variable_to_python(raw)
    
    if result is None:
        return []
    
    columns = result.get("columns", [])
    rows = result.get("rows", [])
    
    # Detectar formato DIRECTO (GR_*, BoxPlot): 1 row, fields en columns
    if len(rows) == 1:
        row = rows[0]
        ti = columns.index("type") if "type" in columns else -1
        KNOWN_TYPES = {"html", "table", "scalar", "vector", "plotly"}
        if ti >= 0 and isinstance(row[ti], str) and row[ti].lower() in KNOWN_TYPES:
            # Formato directo: una sola fila = un slot
            slot = {col: row[i] for i, col in enumerate(columns)}
            return [slot]
    
    # Formato FLATTEN (PCA, regresión, etc.): N filas en formato flatten
    flat = [elem for row in rows for elem in (row if isinstance(row, list) else [row])]
    n_slots = len(flat) // 5  # siempre 5 campos: name,label,type,value,tier
    slots = []
    for i in range(n_slots):
        slot = {columns[j]: flat[i + j * n_slots] for j in range(5)}
        slots.append(slot)
    return slots
```

> **Crítico:** El índice es `flat[i + j*n_slots]`, NO `flat[i*5 + j]`. Es column-major aunque el data.frame en R sea row-major. Este fue el bug más difícil de diagnosticar del proyecto.

### 12.5 `buildSlotElement()` en `datalab.js`

La función central de renderizado — **nunca reimplementar**:

```javascript
function buildSlotElement(slot) {
    // slot = { name, label, type, value, tier }
    const el = document.createElement('div');
    
    if (slot.type === 'html') {
        // Detectar <neven-plotly> → renderizar gráfico Plotly
        if (slot.value.includes('<neven-plotly>')) {
            return _renderPlotlyJSON(extractBase64(slot.value), slot.label);
        }
        el.innerHTML = slot.value;
    } else if (slot.type === 'table') {
        return renderSlotTable(slot.value, slot.label);
    } else {  // scalar, vector
        el.textContent = slot.value;
    }
    return el;
}
```

### 12.6 `r_object_to_slots.R` — el serializador

Convierte cualquier objeto R S3 en un data.frame de slots:

```r
r_object_to_slots(obj, tier_map = NULL)
```

Detección de tipo (en orden de prioridad):
1. `data.frame` o `matrix` → `"table"`
2. `string` con `"<html"` → `"html"`
3. Vector atómico longitud > 1 → `"vector"`
4. Vector atómico longitud == 1 → `"scalar"`
5. Cualquier otro → `"unknown"`

Serialización JSON:
- `"table"` → `jsonlite::toJSON(df, dataframe="rows")`
- `"html"` → string tal cual
- `"vector"` → `jsonlite::toJSON(as.list(val))`
- `"scalar"` → `jsonlite::toJSON(val, auto_unbox=TRUE)`

---

## 13. Data Studio — Exploración de Datos

### 13.1 Funcionalidades

- **Cargar archivo**: botón "Abrir archivo" → `<input type="file">` oculto → `FileReader` → `POST /api/load` → DuckDB en memoria
- **Leer Excel**: botón con SVG → carga `.xlsx` vía `openpyxl` en el servidor
- **Conectar BD**: modal → motor + credenciales → `POST /api/db_connect` → DuckDB
- **Archivos recientes**: persistidos en `localStorage` (últimos 8, con nombre y dimensiones)
- **SQL**: editor de texto + `POST /api/query` + botón "Cargar ejemplo..." con 3 ejemplos
- **Estadísticas descriptivas**: `POST /api/stats` → tabla de describe()
- **GROUP BY**: selector de columna → `POST /api/groupby`
- **"Enviar a Slide"**: botón en cada resultado → `postMessage` al iframe de Presentaciones

### 13.2 DuckDB como motor SQL

```python
# En neven_http_server.py
import duckdb
_duckdb_conn = duckdb.connect()  # in-memory

def load_data(cols, types, rows):
    """Carga un array de objetos JSON en DuckDB como tabla 'dataset'."""
    df = pd.DataFrame(rows, columns=cols)
    _duckdb_conn.execute("DROP TABLE IF EXISTS dataset")
    _duckdb_conn.register('df_temp', df)
    _duckdb_conn.execute("CREATE TABLE dataset AS SELECT * FROM df_temp")

def execute_query(sql):
    """Ejecuta SQL y retorna resultado como JSON."""
    # Filtrar comentarios -- antes de validar el tipo de sentencia
    sql_clean = '\n'.join(
        line for line in sql.splitlines() 
        if not line.strip().startswith('--')
    ).strip()
    
    if not sql_clean.upper().startswith(('SELECT', 'WITH', 'SHOW', 'DESCRIBE')):
        raise ValueError("Only SELECT/WITH/SHOW/DESCRIBE statements are allowed")
    
    result = _duckdb_conn.execute(sql_clean).fetchdf()
    return result.to_json(orient='records')
```

### 13.3 Enviar a Slide

El flujo de datos DataStudio → Presentaciones usa `postMessage` cruzado entre iframes:

```javascript
// En taskpane.html
function sendTableToSlide(html, title) {
    const msg = {
        type: 'NEVEN_ADD_SLIDE',
        slideHtml: html,
        slideTitle: title
    };
    // Si el iframe de presentaciones está cargado
    const frame = document.getElementById('presentaciones-frame');
    if (frame.src) {
        frame.contentWindow.postMessage(msg, '*');
    } else {
        // Cargar el iframe primero
        frame.src = '/presentaciones/index.html';
        frame.onload = () => frame.contentWindow.postMessage(msg, '*');
    }
    showToast('✓ Slide agregado a Presentaciones');
}
```

---

## 14. Run Script — Editor de Scripts

### 14.1 Funcionalidades

- Selector de lenguaje (R / Julia / Python) con dot de estado (verde=OK, naranja=cambios)
- Botones: Abrir (`<input type="file">`), Guardar (`/api/save_script`), Guardar como (`showSaveFilePicker`), Nuevo
- Dropdown "Ejemplos..." con 9 ejemplos (3 por lenguaje)
- `Ctrl+S` → guardar, `Ctrl+Enter` → ejecutar
- Timeout de 120 segundos con `AbortController`
- Output renderizado vía `buildSlotElement` (mismo componente que Data Lab)

### 14.2 `renderScriptResultRS()` — reutiliza buildSlotElement

El servidor retorna el resultado del script como JSON. `renderScriptResultRS` normaliza el tipo y delega a `buildSlotElement`:

```javascript
function renderScriptResultRS(res) {
    let slot = { name: 'resultado', label: 'Resultado', tier: 1 };
    
    if (res.type === 'array' && res.columns && res.rows) {
        // Convertir row-major a array-of-objects
        slot.type = 'table';
        slot.value = res.rows.map(row => {
            const obj = {};
            res.columns.forEach((c, i) => { obj[c] = Array.isArray(row) ? row[i] : row[c]; });
            return obj;
        });
    } else if (res.type === 'html' || (res.html && res.html.includes('<neven-plotly>'))) {
        slot.type = 'html';
        slot.value = res.html || res.result;
    } else if (res.type === 'nil') {
        slot.type = 'scalar';
        slot.value = '(sin valor de retorno)';
    } else {
        slot.type = 'scalar';
        slot.value = String(res.result ?? res.value ?? '');
    }
    
    return buildSlotElement(slot);  // ← SIEMPRE delegar a buildSlotElement
}
```

### 14.3 `/api/save_script`

```python
def _handle_save_script(self, body):
    """Escribe el contenido del script al filesystem."""
    path = body.get('path', '').strip()
    content = body.get('content', '')
    
    # Validar extensión
    ext = os.path.splitext(path)[1].lower()
    if ext not in ('.r', '.py', '.jl'):
        return {'error': 'Solo se permiten extensiones .r, .py, .jl'}
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return {'status': 'ok', 'path': path}
```

---

## 15. Creador de Presentaciones

### 15.1 Arquitectura

El Creador de Presentaciones es una aplicación HTML/CSS/JS autocontenida en `CreadorPresentaciones/`. Se embebe en NEVEN Studio como un iframe lazy-loaded en el tab "Presentaciones". También puede usarse de forma independiente abriendo `index.html` directamente.

Cuando se carga dentro de NEVEN Studio (dentro de un iframe), detecta el contexto y oculta el header duplicado:
```html
<script>
if (window.self !== window.top) {
    document.documentElement.classList.add('embedded');
}
</script>
```

### 15.2 La clase `PresentationEditor`

Todo el estado y la lógica residen en la clase `PresentationEditor`:

```javascript
class PresentationEditor {
    constructor() {
        this.slides = [];         // array de objetos slide
        this.currentSlide = null; // slide seleccionado
        this.slideCounter = 0;    // contador para IDs únicos
        this.history = [];        // stack de undo/redo (estados JSON)
        this.historyIndex = -1;
        this.title = 'Mi Presentación';
        this._zoom = 1.0;         // zoom del canvas
        this._dragAbort = null;   // AbortController para drag listeners
        this._init();
    }
}
```

### 15.3 Modelo del slide

Cada slide es un objeto plain JS con estas propiedades:

```javascript
{
    id: 'slide-N',           // string único
    text: 'Contenido',       // texto principal
    type: 'slide',           // 'slide'|'title'|'image'|'iframe'|'chart'|'blackboard'|'overview'|'plotly'
    
    // Posición en el espacio Impress.js (navegación entre slides)
    x: 0, y: 0, z: 0,       // coordenadas en el espacio 3D
    rotate: 0,               // rotación en grados
    scale: 1.0,              // escala del slide en Impress
    
    // Estilo del texto
    fontFamily: "'Segoe UI', sans-serif",
    fontSize: 48,
    textColor: '#e0e0e0',
    
    // Contenido embebido
    imageUrl: '',            // para type='image'
    iframeUrl: '',           // para type='iframe' (URL web)
    charts: [],              // para type='chart' (gráficos Chart.js)
    blackboardData: null,    // dataURL del canvas de pizarra
    
    // Datos enviados desde NEVEN Studio
    _srcdoc: '',             // HTML de tabla/resultado (type='iframe' desde DataStudio)
    _plotlyData: null,       // datos JSON de gráfico Plotly (type='plotly')
    
    // Posición y tamaño del CONTENIDO dentro del slide
    contentZoom: 1.0,        // transform:scale — escala el contenido uniformemente
    contentOffsetX: 50,      // posición horizontal (%) desde centro: 50=centrado
    contentOffsetY: 50,      // posición vertical (%) desde centro: 50=centrado
}
```

> **Diferencia crítica:** `x/y/z/rotate/scale` controlan la posición del **slide en el espacio Impress.js** (la navegación entre slides). `contentZoom/contentOffsetX/contentOffsetY` controlan la posición del **contenido dentro del slide** (la tabla, gráfico o iframe).

### 15.4 El patrón `propMap` — propiedades independientes por slide

El panel de propiedades usa un `propMap` donde cada campo del DOM tiene su propia función de escritura que modifica **únicamente** su propiedad en el slide activo:

```javascript
_bindProperties() {
    const propMap = [
        [this.el.x,           s => { s.x = parseInt(this.el.x.value) || 0; }],
        [this.el.rotate,      s => { s.rotate = parseInt(this.el.rotate.value) || 0; }],
        [this.el.contentZoom, s => { s.contentZoom = parseFloat(this.el.contentZoom.value) || 1.0; }],
        // ... un entry por cada campo
    ];
    
    propMap.forEach(([el, writeFn]) => {
        if (!el) return;
        const handler = () => {
            if (!this.currentSlide) return;
            writeFn(this.currentSlide);  // ← escribe SOLO esta propiedad
            this._renderCanvas();
            this._updateCurrentSlideLabel();  // ← NO _renderList()
            this._saveState();
        };
        el.addEventListener('input', handler);
        el.addEventListener('change', handler);
    });
}
```

> **Antipatrón eliminado:** La función `_updateFromPanel()` monolítica que leía todos los campos del DOM y los aplicaba al slide activo. Si el DOM tenía valores residuales de otro slide, los sobreescribía en el slide activo (bug de contaminación). Ahora cada campo escribe solo su propiedad.

> **Regla:** Nunca llamar `_renderList()` desde un handler de propiedad. `_renderList()` reconstruye todo el DOM de la lista con `innerHTML = ''`, destruye la selección visual y parece "resetear" al Slide 1. Usar `_updateCurrentSlideLabel()` que actualiza solo el label del card activo.

### 15.5 Renderizado del HTML de presentación

`_buildPresentationHTML(forExport)` genera el HTML completo para Preview o Exportar.

**Para tablas HTML embebidas (`type='iframe'` con `_srcdoc`)**:
```javascript
const zoom = s.contentZoom || 1.0;
const tx = ((s.contentOffsetX ?? 50) - 50);  // desplazamiento desde centro en vw
const ty = ((s.contentOffsetY ?? 50) - 50);  // desplazamiento desde centro en vh

// El contenedor llena la pantalla completa
// El elemento interno usa transform para posición + escala
`<div class="step" ...style="display:flex;align-items:center;justify-content:center;width:100vw;height:100vh">
  <div style="display:inline-block;transform:translate(${tx}vw,${ty}vh) scale(${zoom});transform-origin:center center">
    ${innerStyle}${innerHtml}
  </div>
</div>`
```

**Por qué `translate + scale` en lugar de `width/height`:**
- `width/height` en un contenedor no escala el contenido — solo agrandea el espacio vacío
- `transform:scale(N)` escala todo el contenido (fuentes, celdas, bordes) uniformemente
- `transform` no afecta el layout del DOM — el contenedor padre no se recorta si no tiene `overflow:hidden`
- El desplazamiento `(offsetX - 50) vw` funciona porque `50/50` = centrado, `60/50` = 10vw a la derecha

**Por qué `%` no funciona para `height` en Impress.js:**
Los elementos `.step` de Impress.js son bloques sin altura definida. `height: 80%` resuelve a 0 porque no hay referencia de altura en el padre. La solución es usar `vh` (unidades de viewport). El método `_normalizeUnit(val, axis)` convierte `%` → `vw/vh` automáticamente.

### 15.6 Preview con overlay flotante de propiedades

Cuando el usuario hace clic en "Preview":
1. `_buildPresentationHTML(false)` genera el HTML y lo asigna a `previewFrame.srcdoc`
2. `_attachPropsToPreview()` crea (o reutiliza) el overlay `#preview-props-overlay`
3. El overlay usa `position:fixed` (z-index 9999) para escapar de `overflow:hidden` del modal
4. Los campos del overlay tienen `_pvBound = true` para no registrar listeners duplicados
5. Al cambiar cualquier campo, el handler actualiza `this.currentSlide.propiedad` directamente
6. El preview se regenera: `this.el.previewFrame.srcdoc = this._buildPresentationHTML(false)`

El overlay es arrastrable (drag con `getBoundingClientRect` para coordenadas `position:fixed`) y minimizable con el botón `−/+`.

### 15.7 Flujo DataLab/DataStudio → Slide

```javascript
// 1. En datalab.js o taskpane.html:
window.parent.postMessage({
    type: 'NEVEN_ADD_SLIDE',
    plotlyData: JSON.stringify(plotlyFig),  // para gráficos Plotly
    // O:
    slideHtml: tableHtml,                   // para tablas HTML
    slideTitle: 'Mi Gráfico'
}, '*');

// 2. En taskpane.html (relay):
window.addEventListener('message', e => {
    if (e.data.type !== 'NEVEN_ADD_SLIDE') return;
    const frame = document.getElementById('presentaciones-frame');
    const forwardMsg = () => frame.contentWindow.postMessage(e.data, '*');
    if (!frame.src) {
        frame.src = '/presentaciones/index.html';
        frame.onload = forwardMsg;
    } else {
        forwardMsg();
    }
    showToast('✓ Slide agregado a Presentaciones');
});

// 3. En script.js (receptor):
window.addEventListener('message', e => {
    if (e.data.type !== 'NEVEN_ADD_SLIDE') return;
    if (e.data.plotlyData) {
        editor._newSlide({ type: 'plotly', _plotlyData: e.data.plotlyData,
                           text: e.data.slideTitle || 'Gráfico' });
    } else if (e.data.slideHtml) {
        editor._newSlide({ type: 'iframe', _srcdoc: e.data.slideHtml,
                           text: e.data.slideTitle || 'Tabla' });
    }
});
```

---

## 16. Librería R (R4XCL)

### 16.1 Estructura

Cada módulo estadístico tiene:
- `libreria/R/MR_Lineal.Studio.R` — implementación completa
- `Install/functions/MR_Lineal.json` — sidecar Data Lab

Las funciones se registran en Excel con prefijo `R.`: `=R.MR_Lineal(Y, X, TipoOutput)`.

### 16.2 Patrón TipoOutput

Todas las funciones R4XCL siguen el patrón `TipoOutput`:

```r
MR_Lineal <- function(Y, X, TipoOutput = 1) {
    modelo <- lm(Y ~ ., data = data.frame(Y=Y, X))
    
    if (TipoOutput == 0) return("0=Coeficientes, 1=Resumen, 2=ANOVA, ...")
    if (TipoOutput == 1) return(coef(modelo))          # coeficientes
    if (TipoOutput == 2) return(summary(modelo)$r.squared) # R²
    if (TipoOutput == 3) return(as.data.frame(anova(modelo))) # tabla ANOVA
    # ...
    if (TipoOutput == 13) return(Extraer_outputs(modelo))  # TODOS los outputs
}
```

`TipoOutput=0` retorna la lista de procedimientos disponibles — útil para descubrimiento.

### 16.3 Módulos disponibles

| Prefijo | Módulo | Funciones |
|:---|:---|:---|
| MR_ | Regresión | MR_Lineal, MR_Binario, MR_Poisson, MR_Tobit, MR_PanelData, MR_SVM |
| AD_ | Análisis de Datos | AD_ACP, AD_KMedias, AD_Descriptiva, AD_Psicometria |
| ST_ | Series de Tiempo | ST_SeriesTemporales, ST_Autoregresivos, ST_Filtro |
| GR_ | Gráficos | GR_PlotlyView, GR_QuickPlot |
| RG_ | Modelos avanzados | RG_Mixtos, RG_Supervivencia, RG_Bayesiana |
| R. | Visualización interactiva | R.Pivot, R.Esquisse, R.D3, R.Dashboard, R.Map |

### 16.4 Funciones Data Lab (`.Studio.R`)

Las funciones del Data Lab tienen la convención `.Studio()`:

```r
AD_KMedias.Studio <- function(data_Variables, K=3, PaletaColores="1", ...) {
    # Ejecuta el análisis
    resultado <- kmeans(data_Variables, centers=K)
    
    # Retorna como data.frame de slots via r_object_to_slots()
    return(r_object_to_slots(resultado))
}
```

El resultado de `r_object_to_slots(resultado)` es el data.frame que `_parse_slots_from_variable()` convierte en lista de slots para renderizar.

### 16.5 `Extraer_outputs(modelo)` — extractor universal

```r
Extraer_outputs(objeto, nombre_modelo = NULL)
```

Extrae TODOS los outputs de cualquier modelo R como un data.frame estructurado:

```
[Modelo] [Seccion] [Parametro] [Metrica] [Valor]
lm_reg   Coefficients  (Intercept)  Estimate  2.345
lm_reg   Coefficients  X1           Estimate  0.876
lm_reg   R_Squared     Multiple_R2  Value     0.891
lm_reg   F_Statistic   F_Value      Stat      45.23
...
```

Disponible como `TipoOutput=N_MAX` en 11 funciones. Permite al usuario obtener todos los outputs con una sola llamada.

---

## 17. Librería Julia (J4XCL)

### 17.1 Estructura

Archivo principal: `libreria/JULIA/functions.jl` carga los 9 módulos.

Cada módulo es un módulo Julia (namespace):
```julia
module JM_Algebra
    using LinearAlgebra

    function main(matriz, vector, tipo)
        # tipo 1 = descomposición LU
        # tipo 2 = QR
        # ...
    end
end
```

### 17.2 Aliases de nombres cortos

El módulo de startup de Julia define aliases para que el usuario pueda escribir `J.Algebra` en lugar de `J.JM_Algebra`:

```julia
# En startup/startup.jl
J_Algebra    = JM_Algebra.main
J_Estadistica = JM_Estadistica.main
# ...
```

Los nombres originales siguen funcionando — los aliases son adicionales.

### 17.3 Gestión de memoria Julia 1.12

Julia usa un GC que puede interferir con los Named Pipes en ventanas de tiempo largas. El `GCMonitor` en C++ detecta presión de memoria y puede forzar un `GC.gc()` cuando es seguro hacerlo.

---

## 18. Seguridad

### 18.1 SandboxVerifier — 5 mecanismos anti-bypass

Protege contra código malicioso en `=NEVEN.r()`, `=NEVEN.j()`, `=NEVEN.p()` y la consola REPL.

**Mecanismo 1 — Whitespace stripping:**
`sys tem()` → strip → `system()` → bloqueado

**Mecanismo 2 — Concatenation detection:**
`paste0("sys","tem()")` → detectado como intento de bypass

**Mecanismo 3 — Case insensitivity:**
`SYSTEM()`, `System()`, `sYsTeM()` → todos bloqueados

**Mecanismo 4 — Context-aware detection:**
Un `file.remove` dentro de un string literal no se bloquea, pero fuera de comillas sí.

**Mecanismo 5 — Unified enforcement:**
El mismo mecanismo aplica en REPL, AutoLoader y llamadas arbitrarias.

Patrones bloqueados por lenguaje:

| R | Julia | Python |
|:---|:---|:---|
| `system()`, `system2()` | `run()`, `pipeline()` | `os.system()`, `subprocess.*` |
| `shell()`, `shell.exec()` | `@ccall`, `ccall()` | `eval()`, `exec()` |
| `file.remove()`, `unlink()` | `unsafe_*` | `open()` con modo `w` |
| `download.file()`, `url()` | backtick literals | `importlib.*` |
| `eval(parse())`, `do.call()` | `include()` | `__import__()` |
| `.Call()`, `dyn.load()` | `Base.eval()` | `ctypes.*` |
| `Sys.setenv()`, `setwd()` | `Pkg.*` | `sys.path` modification |

### 18.2 InputSanitizer

Allowlist validation para paths de `CreateProcess`. Solo permite ejecutar:
- `ControlR.exe`, `ControlJulia.exe`, `ControlPython.exe`
- `julia.exe`, `Rgui.exe` (consolas interactivas)
- `quarto.exe` (renderizado de documentos)

Cualquier otro path es rechazado.

### 18.3 MessageValidator

Valida frames Protobuf antes de deserializar:
- Longitud del frame ≥ 4 bytes
- Longitud declarada ≤ 256 KB (`kMaxDynamicBufferSize`)
- El payload puede ser deserializado como `CallResponse`

### 18.4 SafePipeHandle

RAII wrapper para handles de Named Pipes con `CRITICAL_SECTION` para operaciones atómicas. Previene uso del handle después de que el proceso hijo muere.

### 18.5 Integridad de startup scripts

`SecurityService` verifica los hashes SHA-256 de `startup.r` y `startup.jl` contra archivos `.sha256` sidecar antes de enviarlos al motor. Si el hash no coincide, el motor no arranca.

### 18.6 MSVC hardening flags

```
/GS           — buffer overrun detection
/guard:cf     — Control Flow Guard
/sdl          — Additional Security Checks
/DYNAMICBASE  — ASLR (Address Space Layout Randomization)
/NXCOMPAT     — Data Execution Prevention
/CETCOMPAT    — Control-flow Enforcement Technology
```

---

## 19. Sistema de Configuración

### 19.1 `neven-config.json`

Ubicación en producción: `C:\NEVEN\neven-config.json`

```json
{
  "NEVEN": {
    "functionsDirectory": "C:\\NEVEN\\functions",
    "graphicsDirectory": "C:\\NEVEN\\graphics",
    "logFile": "C:\\NEVEN\\neven.log",
    "openConsole": false,
    "useJobObject": true,          // procesos hijo mueren con Excel
    "callTimeoutMs": 600000,       // 10 minutos por llamada
    "maxRetries": 2,               // máximo de reintentos de reconexión
    "sandboxEnabled": true,
    "R": { "home": "", "minMajor": 3, "minMinor": 5, "maxMajor": 99 },
    "Julia": { "home": "", "enabled": true, "minMajor": 1, "minMinor": 6 },
    "Python": { "home": "", "enabled": true, "minMajor": 3, "minMinor": 10 }
  },
  "WebView2": { "enabled": true, "maxViewers": 8, "maxMemoryMB": 512 },
  "Pluto": { "port": 1234 },
  "AI": {
    "enabled": true,
    "provider": "lmstudio",
    "endpoint": "http://localhost:1234/v1/chat/completions",
    "model": "nvidia/nemotron-3-nano-4b",
    "promptsDirectory": "C:\\NEVEN\\prompts"
  }
}
```

> **Nota de seguridad:** `neven-config.json` está en `.gitignore` para no incluir configuraciones locales en el repositorio.

### 19.2 `neven-languages.json`

Define los motores de lenguaje. El XLL lee este archivo para saber cómo lanzar cada motor:

```json
[
  {
    "name": "R",
    "executable": "ControlR.exe",
    "prefix": "R",               // prefijo en Excel: =R.func()
    "extensions": ["r", "R"],    // extensiones de archivos monitoreados
    "command_arguments": "-r \"$HOME\"",  // $HOME se reemplaza con R_HOME
    "prepend_path": "$HOME\\bin\\x64",    // DLLs de R
    "priority": 10,
    "startup_resource": "startup.r"
  }
]
```

### 19.3 `ConfigService` en C++

Singleton que expone getters tipados:

```cpp
int GetCallTimeoutMs() const;
int GetCallTimeoutMs(const std::string& lang) const;  // por lenguaje
bool IsSandboxEnabled() const;
std::string GetFunctionsDirectory() const;
int GetMaxRetries() const;
HealthStatus GetLanguageHealth(const std::string& lang) const;
```

Paths con variables de entorno se expanden automáticamente (`%USERPROFILE%`, `%NEVEN_HOME%`).

---

## 20. Build System

### 20.1 CMake — estructura

```
CMakeLists.txt (raíz)
  ├── FetchContent: Protobuf v21.12, GTest v1.14.0, rapidcheck, WebView2 SDK
  ├── add_subdirectory(PB)        → PB.lib
  ├── add_subdirectory(Common)    → Common.lib
  ├── add_subdirectory(Core)      → NEVEN.dll / NEVEN64.xll
  ├── add_subdirectory(ControlR)  → ControlR.exe
  ├── add_subdirectory(ControlJulia) → ControlJulia.exe
  ├── add_subdirectory(ControlPython) → ControlPython.exe
  ├── add_subdirectory(Ribbon)    → NEVENRibbon.dll
  ├── add_subdirectory(Addin)     → copia XLL al directorio Dist/
  ├── add_subdirectory(tests)     → test runner
  └── add_subdirectory(NEVEN-SIM) → NEVEN-SIM.xll (opcional: BUILD_NEVEN_SIM=ON)
```

### 20.2 Comandos de build

```powershell
# Desde la raíz del repositorio
cmake -S . -B Build -G "Visual Studio 17 2022" -A x64
cmake --build Build --config Release --target INSTALL
```

El target `INSTALL` copia todos los binarios a `Build/Dist/`:
```
Build/Dist/
  NEVEN64.xll
  NEVENRibbon.dll
  ControlR.exe
  ControlJulia.exe
  ControlPython.exe
  neven-config.json
  neven-languages.json
  startup/
  functions/
```

### 20.3 Build del Ribbon (separado)

```powershell
scripts/build-ribbon.ps1
```

El Ribbon se compila con MSBuild (no CMake) porque usa ATL/COM que tiene mejor soporte con el sistema de proyectos de Visual Studio.

### 20.4 Variables de build importantes

```cmake
NEVEN_ENABLE_PYTHON=ON      # incluir ControlPython.exe (default: ON)
BUILD_NEVEN_SIM=ON          # incluir NEVEN-SIM.xll (default: OFF)
CMAKE_BUILD_TYPE=Release    # Release / Debug
```

### 20.5 R libs

ControlR necesita `R64.lib` y `RGraphApp64.lib`. Estas se generan desde la instalación de R:

```powershell
scripts/rebuild-r-libs.ps1
```

Usa `dumpbin` + `lib` para generar las librerías de importación desde las DLLs de R 4.4.1.

### 20.6 Julia sysimage

```bash
julia scripts/build-julia-sysimage.jl
# Genera C:\NEVEN\neven_julia.dll (~415 MB)
# Tarda 5-10 minutos
```

### 20.7 Registro del Ribbon

El Ribbon es un COM DLL y necesita registrarse en Windows:

```cmd
regsvr32 C:\NEVEN\NEVENRibbon.dll
```

El instalador hace esto automáticamente con elevación de permisos.

---

## 21. Testing

### 21.1 Suite completa: 357 tests

| Suite | Tests | Tecnología | Qué cubre |
|:---|:---:|:---|:---|
| SandboxTest | 154 | GTest | Todos los patrones de sandbox R/Julia/Python + bypass |
| InputSanitizer | 21 | GTest | Allowlist validation para CreateProcess |
| ReliabilityPBT | 24 | rapidcheck | Property-based: timeouts, mensajes de error, health |
| ProtobufIPC | 6 | GTest | Framing, serialización, límites de tamaño |
| PipeLifecycle | 8 | GTest | RAII handles, SafePipeHandle |
| ConfigService | 12 | GTest | JSON parsing, getters, validación de paths |
| TypeConversions | 4 | GTest | XLOPER12 ↔ Variable, thread safety |
| BasicFunctions | 35 | GTest | RJ_FunctionCall, bounds checking |
| E2ETest | 8 | GTest | Pipeline completo via MockExcelBridge |
| RepoHygiene | 14 | GTest | Convenciones de código, no std::cout |
| BuildVerification | 4 | GTest | Verificación de que los binarios se generan |
| RLibrary | 1 | GTest | r_object_to_slots.R funciona correctamente |
| EnvLookup | 4 | GTest | DiscoveryService, detección de R/Julia/Python |
| Otros | ~12 | GTest | COM, callbacks, tipos |

### 21.2 Tests de Python

```python
# tests/test_datalab_handler.py
# tests/test_r_object_to_slots.R
```

### 21.3 Ejecutar los tests

```powershell
cmake --build Build --config Release
cd Build
ctest -C Release --output-on-failure
```

### 21.4 MockExcelBridge

Los tests corren sin Excel, R ni Julia gracias a `MockExcelBridge`:

```cpp
// tests/mocks/mock_engine_backend.cc
class MockEngineBackend : public IEngineBackend {
    Variable Execute(const Code& code) override {
        // Retorna respuestas predefinidas según el código enviado
        if (code.line(0) == "1+1") {
            Variable v;
            v.set_integer(2);
            return v;
        }
        // ...
    }
};
```

---

## 22. Instalación y Despliegue

### 22.1 Prerrequisitos

| Componente | Versión mínima | Descarga |
|:---|:---|:---|
| R | 4.4.1+ | cran.r-project.org |
| Julia | 1.12.6+ | julialang.org |
| Python | 3.10+ | python.org |
| WebView2 Runtime | Cualquiera | Preinstalado en Windows 10/11 |
| Windows | 10+ (64-bit) | — |
| Excel | 2013+ | — |

### 22.2 Instalación automática

```cmd
Install-NEVEN.exe
```

El instalador hace:
1. Detecta R, Julia, Python y Excel automáticamente
2. Pregunta directorio de instalación (default: `C:\NEVEN\`)
3. Copia binarios y configs
4. Registra XLL en Excel: `%APPDATA%\Microsoft\AddIns\NEVEN64.xll`
5. Registra Ribbon COM: `regsvr32 NEVENRibbon.dll`
6. Crea `%USERPROFILE%\Documents\NEVEN\functions\` con ejemplos
7. Instala paquetes R necesarios: `install.packages(c("jsonlite","plotly","ggplot2","stargazer",...))`
8. Verifica: `=NEVEN.r("1+1")` → 2

### 22.3 Despliegue manual de archivos editados

**Regla crítica:** NUNCA usar `Copy-Item` de PowerShell para archivos con caracteres UTF-8 (JS, Python). Corrompe el encoding.

```powershell
# CORRECTO — preserva UTF-8
[System.IO.File]::Copy("repo\archivo.js", "C:\NEVEN\taskpane\archivo.js", $true)

# INCORRECTO — corrompe UTF-8
Copy-Item "repo\archivo.js" "C:\NEVEN\taskpane\archivo.js" -Force
```

Rutas de producción:

| Archivo del repositorio | Ruta en producción |
|:---|:---|
| `TaskPane/taskpane.html` | `C:\NEVEN\taskpane\taskpane.html` |
| `TaskPane/datalab.js` | `C:\NEVEN\taskpane\datalab.js` |
| `ControlPython/startup/datalab_handler.py` | `C:\NEVEN\startup\datalab_handler.py` |
| `ControlPython/startup/neven_http_server.py` | `C:\NEVEN\startup\neven_http_server.py` |
| `CreadorPresentaciones/script.js` | `C:\NEVEN\taskpane\presentaciones\script.js` |
| `CreadorPresentaciones/index.html` | `C:\NEVEN\taskpane\presentaciones\index.html` |
| `libreria/R/MR_*.R` | `C:\NEVEN\functions\MR_*.Studio.R` |
| `Install/functions/*.json` | `C:\NEVEN\functions\*.json` |
| `startup/startup.r` | `C:\NEVEN\startup\startup.r` |

### 22.4 Reiniciar el servidor

```powershell
# Matar el servidor actual
netstat -ano | findstr :5555 | findstr LISTENING
taskkill /PID <PID> /F

# Limpiar pycache
Remove-Item "C:\NEVEN\startup\__pycache__\*" -Force -ErrorAction SilentlyContinue

# Reiniciar con el .vbs
# O manualmente:
cd C:\NEVEN\taskpane
python start_studio.py --no-browser
```

### 22.5 Verificar sintaxis JS antes de desplegar

```powershell
node --check "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\CreadorPresentaciones\script.js"
# Exit code 0 = OK
```

---

## 23. Guía de Resolución de Problemas

### 23.1 Excel no muestra las funciones R./J.

**Diagnóstico:**
```excel
=NEVEN.r("1+1")
```
Si retorna `#VALOR!` en lugar de `2`, el motor R no está conectado.

**Verificar:**
1. Abrir Task Manager → verificar que `ControlR.exe` esté corriendo
2. Revisar `C:\NEVEN\neven.log` (últimas 50 líneas)
3. Esperar 15-30 segundos — los motores conectan en background

**Si ControlR.exe no corre:**
- Cerrar Excel completamente
- Ejecutar `NEVEN Studio.vbs` (mata procesos huérfanos y los reinicia)

### 23.2 NEVEN Studio no arranca

**Síntoma:** El .vbs abre pero el browser no responde en localhost:5555.

**Pasos:**
```powershell
# Verificar si hay proceso en el puerto
netstat -ano | findstr :5555

# Verificar logs del launcher
Get-Content C:\NEVEN\studio.pid  # PID file si existe

# Iniciar manualmente y ver error:
cd C:\NEVEN\taskpane
python start_studio.py
```

**Causa común:** mutex `Global\NEVEN_Studio_Launcher` de instancia anterior que no se limpió. El `.vbs` mata los procesos antes de lanzar, pero si el proceso Python padre no murió, el mutex sigue activo.

### 23.3 DataLab retorna datos corridos

**Síntoma:** Los campos de los slots aparecen en las posiciones incorrectas (el `type` aparece como `name`, el `value` como `type`, etc.).

**Causa:** El parser `_parse_slots_from_variable` detectó incorrectamente el formato del Array.

**Diagnóstico:**
```python
# En Python, conectar directamente al pipe y ver el raw:
from pipe_client import PipeClient, variable_to_python

with PipeClient(r"\\.\pipe\neven_r") as client:
    result = client.send_code(["AD_ACP.Studio(iris[,1:4])"])
    raw = variable_to_python(result)
    print(f"columns: {raw['columns']}")
    print(f"rows[0]: {raw['rows'][0]}")
    print(f"total cells: {len(raw['rows']) * len(raw['columns'])}")
```

Si `columns = ["name","label","type","value","tier"]` y `rows[0]` tiene 5 elementos con el nombre del slot en la primera posición, el formato es FLATTEN. Si `rows[0][2]` es un tipo conocido (`html`, `table`, etc.), es DIRECTO.

### 23.4 Gráfico Plotly retorna HTML crudo

**Síntoma:** El resultado muestra `<html><body><neven-plotly>eyJ...` en lugar del gráfico.

**Causa:** El gráfico se retorna como `type='html'` con el tag `<neven-plotly>` que contiene el JSON del gráfico en base64.

**Fix en `datalab.js`:**
```javascript
function _renderPlotlyJSON(jsonStr, name) {
    // Extraer base64 del tag <neven-plotly>
    const match = jsonStr.match(/<neven-plotly>(.*?)<\/neven-plotly>/s);
    if (!match) return null;
    const decoded = atob(match[1].trim());
    const fig = JSON.parse(decoded);
    const div = document.createElement('div');
    div.style = 'width:100%;height:400px';
    Plotly.newPlot(div, fig.data, fig.layout, {responsive:true});
    return div;
}
```

### 23.5 Encoding corrupto en producción

**Síntoma:** Caracteres como `é` se muestran como `Ã©`, `→` como `â†'`.

**Causa:** `Copy-Item` de PowerShell recodifica el archivo de UTF-8 a latin-1.

**Fix:**
```powershell
[System.IO.File]::Copy("origen.js", "destino.js", $true)
```

**Verificar:**
```powershell
# Verificar encoding del archivo en producción
$bytes = [System.IO.File]::ReadAllBytes("C:\NEVEN\taskpane\datalab.js")
$bytes[0..3]  # Debe ser 239 187 191 (BOM UTF-8) o simplemente texto UTF-8
```

### 23.6 ControlR no arranca después de reinstalar R

**Síntoma:** ControlR.exe arranca pero muere inmediatamente.

**Causa:** `R64.lib` y `RGraphApp64.lib` fueron generadas para una versión anterior de R. Si actualizaste R, necesitas regenerar las librerías.

```powershell
scripts/rebuild-r-libs.ps1
cmake --build Build --config Release --target ControlR
```

### 23.7 Presentaciones — contenido embebido no escala

**Síntoma:** Al cambiar el Zoom del contenido, el tamaño del div cambia pero las fuentes y celdas de la tabla quedan igual.

**Causa:** El contenido usa `width/height` en lugar de `transform:scale`.

**Verificar:** Abrir DevTools en el iframe de Presentaciones → inspeccionar el elemento interno del slide → debe tener `transform: translate(Xvw, Yvh) scale(N)`.

### 23.8 Propiedades contaminan todos los slides

**Síntoma:** Al cambiar el zoom de un slide, todos los demás slides también cambian.

**Causa:** Versión antigua de `script.js` con `_updateFromPanel()` monolítica.

**Verificar:**
```powershell
# Verificar fecha del archivo en producción
(Get-Item "C:\NEVEN\taskpane\presentaciones\script.js").LastWriteTime
# Debe ser >= 2026-08-02
```

---

## 24. Convenciones de Código

### 24.1 C++

```
Clases:    PascalCase           → LanguageManager, SandboxVerifier
Funciones: snake_case           → register_functions(), connect_pipe()
Miembros:  snake_case_ (trailing underscore) → pipe_handle_, next_id_
Constantes: SCREAMING_SNAKE_CASE → MAX_RETRIES, PIPE_TIMEOUT_MS
Archivos:  .cc para implementación, .h para headers
Macros de logging: RJ2XCL_LOG_INFO("mensaje"), RJ2XCL_LOG_ERROR("error")
```

**Nunca usar en código de producción:**
- `std::cout` o `std::cerr` → usar `RJ2XCL_LOG_*`
- `MessageBoxA()` / `MessageBoxW()` → debugging únicamente
- `system()` → usar `CreateProcess` con `CREATE_NO_WINDOW`
- Variables estáticas en funciones UDF → usar `thread_local`

### 24.2 JavaScript (NEVEN Studio)

```
Funciones privadas: _camelCase    → _renderCanvas(), _buildPresentationHTML()
Funciones públicas: camelCase     → addSlide(), showPreview()
Clases: PascalCase                → PresentationEditor
Variables DOM: el.nombreCampo     → this.el.slidesList, this.el.canvas
```

**Reglas de reutilización (CRÍTICO):**

| Componente | Ubicación | Cuándo usar |
|:---|:---|:---|
| `buildSlotElement(slot)` | `datalab.js` | Renderizar cualquier resultado de R/Julia/Python |
| `renderSlotTable(rows, name)` | `datalab.js` | Mostrar tablas con paginación |
| `_renderPlotlyJSON(json, name)` | `datalab.js` | Renderizar gráficos Plotly |
| `_parse_slots_from_variable(raw)` | `datalab_handler.py` | Deserializar respuestas de ControlR |
| `_build_r_script(...)` | `datalab_handler.py` | Construir scripts R para Data Lab |

**Nunca reimplementar estos componentes.** Si Run Script necesita renderizar una tabla, usa `buildSlotElement`. Si un nuevo módulo necesita ejecutar R, usa `_build_r_script`.

### 24.3 Python

```python
# Funciones: snake_case
def load_data(cols, types, rows):
    pass

# Clases: PascalCase
class PipeClient:
    pass

# Constantes: SCREAMING_SNAKE_CASE
MAX_RESPONSE_BYTES = 256 * 1024
```

### 24.4 R (funciones de usuario)

```r
# Funciones de la librería R4XCL: PascalCase con guiones bajos
MR_Lineal <- function(Y, X, TipoOutput = 1) { ... }
AD_ACP <- function(Datos, TipoOutput = 1) { ... }

# Funciones internas NEVEN: .neven_prefijo
.neven_procesar_valor <- function(valor) { ... }
.neven_dl_detect_type <- function(val) { ... }
```

---

## 25. Glosario

| Término | Definición |
|:---|:---|
| **XLL** | DLL renombrada con extensión `.xll`. Add-in nativo de Excel que puede registrar funciones de hoja de cálculo (UDFs). |
| **UDF** | User-Defined Function. Función personalizada registrada en Excel que el usuario puede llamar desde una celda como `=MI_FUNCION()`. |
| **Named Pipe** | Mecanismo IPC de Windows. Un canal de comunicación bidireccional con nombre (`\\.\pipe\nombre`) entre dos procesos. |
| **Protobuf** | Protocol Buffers. Formato de serialización binario de Google usado para serializar mensajes entre el XLL y los motores de lenguaje. |
| **Frame** | El protocolo de NEVEN: 4 bytes de longitud (signed int32 LE) seguidos del payload Protobuf serializado. |
| **Slot** | Unidad de resultado del Data Lab: `{name, label, type, value, tier}`. Una función puede retornar múltiples slots (tabla, gráfico, escalar). |
| **Sidecar JSON** | Archivo `.json` co-ubicado con una función `.Studio.R` que describe su interfaz para el Data Lab (roles, parámetros, tipos). |
| **Control*.exe** | Proceso hijo que embebe un motor de lenguaje (R, Julia, Python). Corre de forma aislada — si crashea, no afecta a Excel. |
| **SandboxVerifier** | Componente que valida código enviado por el usuario antes de ejecutarlo, bloqueando patrones peligrosos. |
| **WebView2** | Edge Chromium embebido en una aplicación Win32. Usado para renderizar Plotly, D3.js, Leaflet dentro de Excel. |
| **STA thread** | Single-Threaded Apartment. Requerido por COM (y por WebView2). El XLL crea un thread dedicado para WebView2. |
| **TipoOutput** | Parámetro de las funciones R4XCL que selecciona qué resultado retornar (coeficientes, gráfico, tabla ANOVA, todos los outputs, etc.). |
| **Impress.js** | Biblioteca JavaScript para presentaciones 3D. Los slides tienen coordenadas X/Y/Z/rotate/scale en un espacio 3D. |
| **contentZoom** | Propiedad del slide en el Creador de Presentaciones. Aplica `transform:scale(N)` al contenido embebido (escala fuentes, celdas, todo). |
| **contentOffset** | Propiedades X/Y del contenido dentro del slide. Desplazan el elemento desde el centro: `tx = (offsetX - 50) vw`. |
| **propMap** | Patrón de binding de propiedades: cada campo del DOM tiene su propia función que escribe únicamente su propiedad en el modelo. |
| **RAII** | Resource Acquisition Is Initialization. Patrón C++ donde los recursos se liberan automáticamente al destruirse el objeto. |
| **r_object_to_slots** | Función R que serializa cualquier objeto S3 en un data.frame de slots tipificados (`table`, `scalar`, `html`, etc.). |
| **Extraer_outputs** | Función R que extrae TODOS los outputs de cualquier modelo (lm, glm, kmeans, etc.) en una tabla estructurada. |
| **DuckDB** | Base de datos analítica in-memory usada en Data Studio para ejecutar SQL sobre los datos cargados. |
| **neven-config.json** | Archivo de configuración central. Define directorios, timeouts, sandbox, AI, WebView2. |
| **Zombie Process Killer** | Código en `Init()` que mata procesos huérfanos de sesiones anteriores usando `taskkill /F /IM`. |

---

## Apéndice A: Diagrama de componentes completo

```
┌─────────────────────────────────────────────────────────────────────┐
│  NEVEN v2.2                                                          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ Hosts                                                     │       │
│  │  ┌────────────────┐    ┌─────────────────────────────┐   │       │
│  │  │  Excel + XLL   │    │   NEVEN Studio (browser)    │   │       │
│  │  │  NEVEN64.xll   │    │   localhost:5555            │   │       │
│  │  │                │    │                             │   │       │
│  │  │ LanguageManager│    │  taskpane.html              │   │       │
│  │  │ SandboxVerifier│    │  datalab.js                 │   │       │
│  │  │ WebView2       │    │  neven_http_server.py       │   │       │
│  │  │ NEVENRibbon    │    │  pipe_client.py             │   │       │
│  │  └───────┬────────┘    └──────────┬──────────────────┘   │       │
│  └──────────┼───────────────────────┼──────────────────────┘       │
│             │ Named Pipes + Protobuf │                              │
│  ┌──────────▼───────────────────────▼──────────────────────┐       │
│  │  Motores de Lenguaje                                      │       │
│  │  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐  │       │
│  │  │ ControlR.exe │  │ControlJulia   │  │ControlPython  │  │       │
│  │  │ R 4.4.1      │  │ Julia 1.12.6  │  │ Python 3.13   │  │       │
│  │  │              │  │ neven_julia.dll│  │ AI/LLM funcs  │  │       │
│  │  │ startup.r    │  │ startup.jl    │  │ startup.py    │  │       │
│  │  │ R4XCL lib    │  │ J4XCL lib     │  │               │  │       │
│  │  └──────────────┘  └───────────────┘  └───────────────┘  │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  Módulos de UI                                            │       │
│  │  ┌──────────────────────────────────────────────────┐    │       │
│  │  │ Creador de Presentaciones                        │    │       │
│  │  │ PresentationEditor (Impress.js)                  │    │       │
│  │  │ propMap · contentZoom · contentOffset            │    │       │
│  │  │ Overlay glassmorphism · Preview en tiempo real   │    │       │
│  │  └──────────────────────────────────────────────────┘    │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Apéndice B: Checklist para un nuevo desarrollador

Antes de tocar código, verificar que puedas hacer:

- [ ] `=NEVEN.r("1+1")` → 2 en Excel
- [ ] `=NEVEN.j("sqrt(144)")` → 12 en Excel
- [ ] Abrir `http://localhost:5555` en el browser
- [ ] Cargar un CSV en Data Studio y ejecutar `SELECT * FROM dataset LIMIT 5`
- [ ] Ejecutar un script R en Run Script y ver el resultado
- [ ] Ejecutar AD_KMedias en Data Lab con datos del dataset
- [ ] Enviar un gráfico desde Data Lab a una presentación y ver el preview
- [ ] `cmake --build Build --config Release && ctest -C Release` → todos pasan

Si alguno falla, revisar TROUBLESHOOTING.md antes de tocar código.

---

*NEVEN-BOOK — Versión 2.2 — Agosto 2026*
*Universidad de Costa Rica — Minor Bonilla Gómez*
*Team Vikingos ⚔️ — SKÅL!*
