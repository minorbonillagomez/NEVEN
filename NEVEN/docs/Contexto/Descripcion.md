# Descripción del Proyecto: NEVEN 2.0

## Resumen Ejecutivo

**NEVEN** (*R and Julia to Excel*), anteriormente conocido como el toolkit **NEVEN**, es un **add-in de Excel** que permite ejecutar código **R** y **Julia** directamente desde celdas de Excel. El proyecto fue creado originalmente por Structured Data, LLC y se modernizó para soportar versiones modernas de R (> 3.5), integrar Julia como segundo motor de scripting, y migrar el sistema de build a CMake.

### ¿Qué hace NEVEN?

- Permite llamar funciones de R y Julia desde fórmulas de Excel (e.g., `=R.MiFuncion(A1:A10)`)
- Convierte datos automáticamente entre tipos de Excel (`XLOPER12`), Protobuf (`Variable`), R (`SEXP`) y Julia (`jl_value_t`)
- Ofrece una consola REPL integrada en Excel para R y Julia
- Genera gráficos de R directamente como shapes en hojas de cálculo
- Vigila cambios en archivos de scripts para recarga automática (hot-reload)
- Registra hasta 512 funciones dinámicamente en Excel mediante el framework XLL

---

## Estado Actual del Proyecto (Marzo 2026)

### ✅ Completado

| Área | Detalle |
|------|---------|
| **Build System** | Migrado a CMake 3.15+ con C++17. Build exitoso con MSVC (Visual Studio 2019+) |
| **Protobuf** | Actualizado de v3.5.0 a v21.12 (descarga automática via FetchContent) |
| **Headers Mock** | R (Rinternals.h + 15 extensiones), Julia (julia.h), Excel SDK (XLCALL.h) |
| **Office Type Libraries** | Integradas `.tlh`/`.tli` pre-generadas con rutas corregidas |
| **Módulo ControlR** | Compila como static lib (.lib). Todos los fuentes compilados |
| **Módulo ControlJulia** | Compila como static lib (.lib). Todos los fuentes compilados |
| **Módulo Common** | Compila como static lib (.lib). Incluye utilidades compartidas |
| **Módulo PB** | Compila como static lib (.lib). Protobuf serialization |
| **NEVEN.dll** | **Enlazado exitosamente**. DLL principal generado en `Build/NEVEN/NEVEN/Release/NEVEN.dll` |
| **Stubs XLL** | Excel12/Excel12v resueltos con binding en runtime |

### 🔲 Pendiente para Operatividad Completa

| Área | Detalle |
|------|---------|
| **Pruebas en Runtime** | Cargar NEVEN.dll dentro de Excel con R.dll y libjulia reales |
| **Addin (XLL)** | El cargador XLL (`Addin/`) no está integrado al build CMake aún |
| **Console (Electron)** | La consola REPL de Electron no ha sido actualizada al nuevo build |
| **Instalador** | El empaquetado (.EXE/.MSI) requiere el binario final validado |
| **Pruebas UTF-8** | Validación de conversiones de texto con caracteres especiales |
| **Memory Leak Tests** | Pruebas de estrés de memoria entre COM, R y Julia GCs |

---

## Arquitectura del Sistema

### Diagrama de Componentes

```
┌───────────────────────────────────────────────────────┐
│                   Microsoft Excel                      │
│                                                       │
│   ┌──────────────┐     XLL API      ┌──────────────┐ │
│   │  NEVEN.xll  │◄────────────────►│  Excel C API │ │
│   │  (Addin)     │   Excel12/12v    │  (xloper12)  │ │
│   └──────┬───────┘                  └──────────────┘ │
└──────────┼────────────────────────────────────────────┘
           │ LoadLibrary
           ▼
┌───────────────────────────────────────────────────────┐
│                    NEVEN.dll                          │
│               (NEVEN_Core Module)                    │
│                                                       │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │ Excel API   │ │ COM Object   │ │ Language      │  │
│  │ Functions   │ │ Map          │ │ Service       │  │
│  └─────────────┘ └──────────────┘ └───────┬───────┘  │
│                                           │           │
│  ┌─────────────┐ ┌──────────────┐         │           │
│  │  Type       │ │  Graphics    │         │           │
│  │  Conversions│ │  (R-->Excel)   │         │           │
│  └─────────────┘ └──────────────┘         │           │
└───────────────────────────────────┬───────┼───────────┘
                                    │       │
          ┌─────────────────────────┘       └──────────────┐
          ▼                                                ▼
┌──────────────────┐                          ┌──────────────────┐
│  ControlR.lib    │                          │ ControlJulia.lib │
│                  │                          │                  │
│ • R Environment  │                          │ • Julia Env      │
│ • R Interface    │                          │ • Julia Interface │
│ • GDI+ Graphics  │                          │ • Julia Convert  │
│ • Conversions    │                          │                  │
└────────┬─────────┘                          └────────┬─────────┘
         │ LoadLibrary                                 │ LoadLibrary
         ▼                                             ▼
    ┌──────────┐                                 ┌───────────┐
    │  R.dll   │                                 │ libjulia  │
    │  (real)  │                                 │   (real)  │
    └──────────┘                                 └───────────┘
```

### Flujo de Datos

```
Excel XLOPER12  ◄─── type_conversions.h ───►  RJ2XCLBuffers::Variable  ◄─── ControlR/Julia ───►  R SEXP / Julia jl_value_t
    (Celdas)           (NEVEN.dll)                (Protobuf)                (Named Pipes)         (Runtime real)
```

---

## Módulos del Proyecto

### 1. NEVEN_Core (`NEVEN/NEVEN/`) --> `NEVEN.dll`

**Es el corazón del proyecto**. Se compila como un DLL compartido (Dynamic Link Library) que se carga dentro de Excel a través del add-in XLL.

| Archivo | Función | Tamaño |
|---------|---------|--------|
| `NEVEN.cc` | Clase principal singleton NEVEN. Gestión de procesos R/Julia, callbacks, pipes | 34 KB |
| `basic_functions.cc` | Funciones XLL exportadas (`RJ2XCLFunctionCall0..511`, `xlAutoOpen`, etc.) | 31 KB |
| `excel_api_functions.cc` | Registro de funciones R/Julia en Excel via `xlfRegister` | ~8 KB |
| `type_conversions.h` | Conversiones `XLOPER12` <--> `Protobuf` <--> `COM VARIANT` | 18 KB |
| `com_object_map.cc` | Mapa de objetos COM para Excel Automation | ~5 KB |
| `rj2xcl_graphics.cc` | Renderizado de gráficos R en Excel shapes | ~3 KB |
| `language_service.cc` | Servicio de lenguajes (despacha a ControlR/ControlJulia) | ~7 KB |
| `xlcall_stubs.cc` | Stubs de `Excel12`/`Excel12v` con binding en runtime | 1.2 KB |
| `NEVEN.def` | Tabla de exports del DLL (512 funciones + callbacks) | 46 KB |

### 2. ControlR (`ControlR/`) --> `ControlR.lib`

Módulo de integración con el lenguaje R. Se compila como biblioteca estática.

| Archivo | Función | Tamaño |
|---------|---------|--------|
| `rinterface_common.cc` | Interface principal con R: pars, eval, conversiones SEXP | 39 KB |
| `controlr.cc` | Lógica de control del proceso R | 37 KB |
| `gdi_graphics_device.cc` | Dispositivo GDI+ para renderizar gráficos de R | 20 KB |
| `console_graphics_device.cc` | Gráficos en consola | 12 KB |
| `spreadsheet_graphics_device.cc` | Gráficos directos en hojas de cálculo | 9 KB |
| `rinterface_win.cc` | Interface R específica para Windows | 5 KB |
| `convert.cc` | Conversiones de encoding (UTF-8 <--> UTF-16) | 4 KB |
| `R_Environment.cpp` | Entorno de ejecución de R (LoadLibrary, GetProcAddress) | 2.4 KB |

### 3. ControlJulia (`ControlJulia/`) --> `ControlJulia.lib`

Módulo de integración con Julia. Compilado como biblioteca estática.

| Archivo | Función | Tamaño |
|---------|---------|--------|
| `julia_interface.cc` | Interface completa con Julia (eval, arrays, tipos) | 40 KB |
| `control_julia.cc` | Lógica de control del proceso Julia | 20 KB |
| `Julia_Environment.cpp` | Entorno de ejecución de Julia (carga dinámica) | 2.6 KB |
| `JuliaConversion.cpp` | Conversiones Julia <--> Protobuf | 1.6 KB |

### 4. Common (`Common/`) --> `Common.lib`

Código compartido entre todos los módulos.

| Archivo | Función |
|---------|---------|
| `pipe.cc/h` | Comunicación por Named Pipes de Windows |
| `message_utilities.cc/h` | Serialización/deserialización de mensajes Protobuf |
| `windows_api_functions.cc/h` | Wrappers de Win32 API (procesos, memoria) |
| `module_functions.cc/h` | Funciones de gestión de módulos |
| `string_utilities.h` | Conversiones UTF-8 <--> UTF-16 |
| `RJ2XCL_Main.cpp` | Punto de entrada principal del framework |
| `AutoLoader.cpp` | Carga automática de scripts desde `Documentos/NEVEN/scripts/` |
| `RuntimeLoader.cpp` | Carga perezosa (Lazy Loading) de R.dll/libjulia |
| `GCMonitor.cpp` | Monitor coordinado de Garbage Collection |
| `SandboxVerifier.cpp` | Validación de seguridad de scripts |
| `json11/` | Parser JSON ligero (third-party) |

### 5. PB (`PB/`) --> `PB.lib`

Capa de serialización usando Protocol Buffers.

| Archivo | Función |
|---------|---------|
| `variable.proto` | Schema con 20+ mensajes: `Variable`, `Array`, `CallResponse`, `FunctionDescriptor`, `GraphicsCommand`, `Console`, etc. |
| `variable.pb.h/cc` | Código C++ generado por `protoc` (~600 KB total) |

### 6. OfficeTypes (`OfficeTypes/`)

Type libraries COM pre-generadas de Microsoft Office.

| Archivo | Descripción | Tamaño |
|---------|-------------|--------|
| `excel.tlh` | Interfaces COM de Excel (_Application, Range, etc.) | ~119K líneas |
| `excel.tli` | Implementaciones inline de métodos COM | ~5.2 MB |
| `mso.tlh` | Interfaces COM de Microsoft Office | ~30K líneas |
| `mso.tli` | Implementaciones inline de MSO | variable |

---

## Dependencias Externas

| Dependencia | Versión | Cómo se obtiene | Propósito |
|-------------|---------|-----------------|-----------|
| **Protocol Buffers** | 21.12 (3.21.12) | CMake FetchContent (automático) | Serialización de datos entre módulos |
| **Visual Studio** | 2019+ | Instalación manual | Compilador MSVC para C++17 |
| **CMake** | 3.15+ | Instalación manual | Sistema de build |
| **Windows SDK** | 10.0+ | Viene con Visual Studio | APIs de Windows |
| **json11** | Incluido en `Common/json11/` | Embebido en el repo | Parsing JSON ligero |
| **R** | 4.x+ | Solo en runtime | Motor de scripting (no requerido para compilar) |
| **Julia** | 1.x+ | Solo en runtime | Motor de scripting (no requerido para compilar) |
| **Excel** | 2016+ (64-bit) | Solo en runtime | Host del add-in |

> **Nota**: R, Julia y Excel **NO son necesarios** para compilar. Se usan headers mock que declaran las interfaces sin implementarlas. Las funciones reales se cargan dinámicamente en runtime vía `LoadLibrary`/`GetProcAddress`.

---

## Headers Mock (Compilación sin SDKs)

Para compilar sin instalar R, Julia ni el Excel SDK, el directorio `include/` contiene headers mock:

### Mock de R (`include/Rinternals.h` + `include/R_ext/`)
- **170 líneas** que definen `SEXP`, ~50 funciones de R, macros `PROTECT`/`UNPROTECT`, constantes de tipos (`INTSXP`, `REALSXP`, etc.)
- **15 sub-headers** en `R_ext/`: `Parse.h`, `Boolean.h`, `GraphicsEngine.h`, `GraphicsDevice.h`, `RStartup.h`, etc.
- Guard `SEXP_DEFINED` previene redefiniciones circulares

### Mock de Julia (`include/julia.h`)
- **190 líneas** que definen `jl_value_t`, `jl_array_t`, `jl_ptls_t`, funciones de boxing/unboxing, macros de GC (`JL_GC_PUSH1/2/3`)
- Funciones de inicialización (`jl_init`), evaluación (`jl_eval_string`), tipos (`jl_typeof_str`)

### Mock de Excel SDK (`include/XLCALL.h`)
- **100 líneas** que definen `XLOPER12` (estructura principal de datos de Excel), `XLREF12`, constantes de tipos, errores, y funciones `Excel12`/`Excel12v`
- Stubs de `Excel12`/`Excel12v` en `NEVEN/NEVEN/src/xlcall_stubs.cc` con binding de punteros en runtime

---

## Cómo Compilar

### Requisitos
1. **CMake** 3.15 o superior
2. **Visual Studio** 2019 o superior (con componente "Desarrollo de escritorio con C++")
3. **Conexión a internet** (para descargar Protobuf automáticamente)

### Comandos

```powershell
# 1. Asegurar CMake en PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 2. Desde la raíz del repositorio
cd C:\Users\mboni\Documents\Antigravity\NEVEN\RJ2XCL_repo
mkdir Build
cd Build

# 3. Configurar (x64)
cmake .. -A x64

# 4. Compilar en Release
cmake --build . --config Release

# 5. Paso manual: copiar .tli al build
Copy-Item "..\OfficeTypes\mso.tli" "NEVEN\NEVEN\mso.tli"
Copy-Item "..\OfficeTypes\excel.tli" "NEVEN\NEVEN\excel.tli"

# 6. Recompilar NEVEN_Core (si falta el paso 5)
cmake --build . --config Release --target NEVEN_Core
```

### Outputs del Build

| Target | Output |
|--------|--------|
| `libprotobuf` | `_deps/protobuf-build/Release/libprotobuf.lib` |
| `PB` | `PB/Release/PB.lib` |
| `Common` | `Common/Release/Common.lib` |
| `ControlR` | `ControlR/Release/ControlR.lib` |
| `ControlJulia` | `ControlJulia/Release/ControlJulia.lib` |
| **NEVEN_Core** | **`NEVEN/NEVEN/Release/NEVEN.dll`** |

---

## Comunicación Inter-procesos

### Named Pipes
Los datos entre NEVEN.dll y los procesos R/Julia se transmiten por **Named Pipes** de Windows, serializados con Protobuf:

```
Excel celdas --> XLOPER12 --> Protobuf (Variable) --> Named Pipe --> R (SEXP) / Julia (jl_value_t)
                                                      ↑
                                                  Respuesta
```

### COM (Component Object Model)
NEVEN interactúa con Excel via COM para:
- Lectura/escritura de celdas desde threads de background
- Creación de shapes (gráficos de R)
- Automatización de Excel (_Application, _Workbook, Range)

Las type libraries de COM están pre-generadas en `OfficeTypes/`.

---

## Seguridad

### SandboxVerifier
Detecta patrones maliciosos en scripts antes de ejecutarlos:
- `os.execute`, `system()`, `shell()` y variantes
- Protege contra archivos Excel compartidos con macros de auto-arranque maliciosas

### Validación de Scripts
La carga automática de scripts (`AutoLoader`) solo lee archivos de un directorio controlado por el usuario (`Documentos/NEVEN/scripts/`), evitando ejecución de código no autorizado.

---

## Historial de Cambios Significativos

| Fecha | Cambio |
|-------|--------|
| **2017-2018** | NEVEN v1 original (como NEVEN, solo R, build con MSBuild/VS) |
| **2026-03** | Migración a CMake, C++17, Protobuf v21.12 |
| **2026-03** | Creación de headers mock para R, Julia, Excel SDK |
| **2026-03** | Integración de OfficeTypes (type libraries COM pre-generadas) |
| **2026-03** | Creación de targets static lib: `Common`, `PB` |
| **2026-03** | Stubs de `Excel12`/`Excel12v` con runtime binding |
| **2026-03** | **Build exitoso**: `NEVEN.dll` generado correctamente |

---

## Licencia

GNU General Public License v3.0 (GPLv3). Copyright (c) 2017-2018 Structured Data, LLC. Modernización 2026 por el equipo NEVEN.
