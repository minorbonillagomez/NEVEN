# Descripción del Proyecto: NEVEN v3.2

## Resumen Ejecutivo

**NEVEN** es un **add-in XLL de C++17 para Microsoft Excel** que integra **R 4.4.1**, **Julia 1.12.6** y **Python 3.13** como motores de scripting embebidos. Permite ejecutar funciones estadísticas, modelos de ML y visualizaciones interactivas desde celdas de Excel. Es una tesis de maestría de Minor Bonilla-Gómez en la Universidad de Costa Rica.

### ¿Qué hace NEVEN?

- Ejecuta código R, Julia y Python desde fórmulas de Excel (`=NEVEN.R()`, `=NEVEN.J()`, `=NEVEN.P()`)
- Registra 200+ funciones como UDFs de Excel (`=R.Pivot()`, `=J.Algebra()`, `=P.MiFuncion()`)
- Genera gráficos interactivos con Plotly, D3.js y Leaflet en WebView2
- Ofrece NEVEN Studio (TaskPane) con 7 tabs: SQL, Data Studio, Run Script, Data Lab, Presentaciones, IA, Ayuda
- Integra DuckDB para consultas SQL sobre datos de Excel
- Incluye Chat IA con RAG (300+ entidades de conocimiento)
- Soporta Pluto.jl para notebooks reactivos y Quarto para reportes
- Vigila cambios en scripts para hot-reload automático

---

## Estado Actual (Agosto 2026)

### Métricas Clave

| Métrica | Valor |
|---------|-------|
| Versión | 3.2 |
| Tests | 342 (228 Core + 114 NEVEN-SIM) |
| UDFs | 200+ |
| Score de calidad | 9.71/10 |
| Entidades RAG | 300+ |
| Formatos soportados | 12 |

### Componentes

| Componente | Tipo | Descripción |
|:---|:---|:---|
| NEVEN64.xll | DLL (XLL) | Add-in principal de Excel |
| NEVENRibbon.dll | DLL (COM) | Cinta de opciones con 17 botones |
| ControlR.exe | Ejecutable | Proceso hijo R 4.4.1 |
| ControlJulia.exe | Ejecutable | Proceso hijo Julia 1.12.6 |
| ControlPython.exe | Ejecutable | Proceso hijo Python 3.13 (Stable ABI) |
| neven_julia.dll | Sysimage | Julia precompilada (~415 MB) |
| neven_http_server.py | Servidor | HTTP server para NEVEN Studio (puerto 5555) |
| rag_engine.py | Módulo | RAG Engine con DuckDB + FastEmbed |
| NEVEN-SIM.xll | DLL (XLL) | Módulo de Simulación Monte Carlo |

---

## Arquitectura del Sistema

### Diagrama de Componentes v3.2

```
┌───────────────────────────────────────────────────────────────────┐
│                        Microsoft Excel                             │
│                                                                   │
│   ┌──────────────┐     XLL API      ┌──────────────┐              │
│   │ NEVEN64.xll │◄────────────────►│  Excel C API │              │
│   │   (Addin)    │   Excel12/12v    │  (xloper12)  │              │
│   └──────┬───────┘                  └──────────────┘              │
└──────────┼────────────────────────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────────┐
│                         NEVEN_Core                                 │
│                                                                   │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐               │
│  │ Excel API   │ │ COM Object   │ │ Language      │               │
│  │ Functions   │ │ Map          │ │ Manager       │               │
│  └─────────────┘ └──────────────┘ └───────┬───────┘               │
│                                           │                        │
│  ┌─────────────┐ ┌──────────────┐ ┌───────┴───────┐               │
│  │  Type       │ │  WebView2    │ │  Config       │               │
│  │  Conversions│ │  Manager     │ │  Service      │               │
│  └─────────────┘ └──────────────┘ └───────────────┘               │
└───────────────────────────────┬───────────────────────────────────┘
                                │
      ┌─────────────────────────┼─────────────────────────┐
      │                         │                         │
      ▼                         ▼                         ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ ControlR.exe │       │ControlJulia  │       │ControlPython │
│   (R 4.4.1)  │       │ (Julia 1.12) │       │ (Python 3.13)│
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │ Named Pipes          │ Named Pipes          │ Named Pipes
       │ + Protobuf           │ + Protobuf           │ + Protobuf
       ▼                      ▼                      ▼
   ┌───────┐              ┌───────┐              ┌───────┐
   │ R.dll │              │libjulia│             │python3│
   └───────┘              └───────┘              └───────┘

                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                    HTTP Server (Python 5555)                       │
│                                                                   │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐               │
│  │   DuckDB    │ │  RAG Engine  │ │  AI Chat      │               │
│  │   (SQL)     │ │  (FastEmbed) │ │  (Bedrock)    │               │
│  └─────────────┘ └──────────────┘ └───────────────┘               │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                      NEVEN Studio (TaskPane)                       │
│                                                                   │
│  ┌─────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌─────┐ ┌────┐ ┌─────┐│
│  │ SQL │ │Data      │ │Run     │ │Data    │ │Pres.│ │ IA │ │Ayuda││
│  │     │ │Studio    │ │Script  │ │Lab     │ │     │ │    │ │     ││
│  └─────┘ └──────────┘ └────────┘ └────────┘ └─────┘ └────┘ └─────┘│
└───────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
Excel XLOPER12 ◄── type_conversions ──► Protobuf Variable ◄── Named Pipes ──► R SEXP / Julia jl_value_t / Python PyObject
    (Celdas)         (NEVEN_Core)          (PB.lib)            (ControlX.exe)        (Runtime)
```

---

## Módulos del Proyecto

### 1. Core (`Core/`) → NEVEN64.xll

**Corazón del proyecto**. Add-in XLL que se carga en Excel.

| Archivo | Función |
|---------|---------|
| `RJ2XCL_Engine.cc` | Singleton principal, gestión de procesos |
| `basic_functions.cc` | Funciones XLL exportadas (512 slots) |
| `language_manager.cc` | Orquesta R, Julia, Python |
| `config_service.cc` | Configuración centralizada |
| `viewer_manager.cc` | Gestión de WebView2 |
| `security_service.cc` | SHA-256 integridad de scripts |
| `type_conversions.h` | Conversiones XLOPER12 ↔ Protobuf ↔ COM |

### 2. ControlR (`ControlR/`) → ControlR.exe

Proceso hijo que embebe R via C API.

| Archivo | Función |
|---------|---------|
| `controlr.cc` | Lógica principal del proceso |
| `rinterface_common.cc` | Interface con R |
| `gdi_graphics_device.cc` | Renderizado de gráficos |

### 3. ControlJulia (`ControlJulia/`) → ControlJulia.exe

Proceso hijo que embebe Julia.

| Archivo | Función |
|---------|---------|
| `control_julia.cc` | Lógica principal |
| `julia_interface.cc` | Interface con Julia |

### 4. ControlPython (`ControlPython/`) → ControlPython.exe

Proceso hijo que embebe Python (Stable ABI).

| Archivo | Función |
|---------|---------|
| `control_python.cc` | Lógica principal |
| `python_interface.cc` | Interface via python3.dll |

### 5. Common (`Common/`) → Common.lib

Código compartido entre módulos.

| Archivo | Función |
|---------|---------|
| `pipe.cc` | Named Pipes de Windows |
| `config_service.cc` | Lectura de neven-config.json |
| `sandbox_verifier.cc` | Validación de seguridad |
| `post_message_bridge.cc` | Comunicación entre threads |

### 6. PB (`PB/`) → PB.lib

Protocol Buffers v21.12.

| Archivo | Función |
|---------|---------|
| `variable.proto` | Schema de mensajes |
| `variable.pb.cc` | Código generado |

### 7. NEVEN-SIM (`NEVEN-SIM/`) → NEVEN-SIM.xll

Módulo de Simulación Monte Carlo (XLL separado).

### 8. Ribbon (`Ribbon/`) → NEVENRibbon.dll

COM Add-in para la pestaña nativa en Excel.

### 9. TaskPane (`TaskPane/`)

Archivos del servidor HTTP y frontend de NEVEN Studio.

| Archivo | Función |
|---------|---------|
| `neven_http_server.py` | Servidor HTTP puerto 5555 |
| `rag_engine.py` | RAG con DuckDB + FastEmbed |
| `taskpane.html` | Frontend de NEVEN Studio |

---

## Dependencias

| Dependencia | Versión | Propósito |
|-------------|---------|-----------|
| Protocol Buffers | 21.12 | Serialización IPC |
| Google Test | 1.14.0 | Testing |
| WebView2 SDK | Latest | Visor HTML embebido |
| DuckDB | 1.0+ | SQL en Python |
| FastEmbed | Latest | Embeddings para RAG |
| MarkItDown | Latest | Extracción de texto |

### Runtime (no requeridos para compilar)

| Componente | Versión |
|------------|---------|
| R | 4.4.1+ |
| Julia | 1.12.6+ |
| Python | 3.10+ |
| Excel | 2016+ (64-bit) |

---

## Cómo Compilar

### Requisitos

1. CMake 3.15+
2. Visual Studio 2022 (C++17)
3. Conexión a internet (FetchContent descarga Protobuf y GTest)

### Comandos

```powershell
# Desde la raíz del repositorio
mkdir build
cd build
cmake .. -A x64
cmake --build . --config Release

# Tests
ctest -C Release --output-on-failure
```

### Outputs

| Target | Output |
|--------|--------|
| NEVEN_Core | `NEVEN64.xll` (= NEVEN.dll) |
| ControlR | `ControlR.exe` |
| ControlJulia | `ControlJulia.exe` |
| ControlPython | `ControlPython.exe` |
| NEVEN_SIM | `NEVEN-SIM.xll` |
| NEVENRibbon | `NEVENRibbon.dll` |

---

## Comunicación Inter-procesos

### Named Pipes + Protobuf

```
Excel celdas → XLOPER12 → Protobuf → Named Pipe → R/Julia/Python
                                         ↑
                                    Respuesta
```

### HTTP Server (NEVEN Studio)

```
TaskPane (HTML/JS) ←→ HTTP :5555 ←→ DuckDB / RAG / AI
```

---

## Seguridad

| Mecanismo | Descripción |
|-----------|-------------|
| SandboxVerifier | 30+ patrones bloqueados por lenguaje |
| SHA-256 | Integridad de scripts de startup |
| WebView2 filter | Whitelist de CDNs permitidos |
| Config validation | Prevención de path traversal |

---

## Estructura del Repositorio

```
NEVEN/
├── Core/           → NEVEN_Core (NEVEN64.xll)
├── ControlR/       → ControlR.exe
├── ControlJulia/   → ControlJulia.exe
├── ControlPython/  → ControlPython.exe
├── Common/         → Common.lib
├── PB/             → PB.lib (Protobuf)
├── NEVEN-SIM/      → NEVEN-SIM.xll
├── Ribbon/         → NEVENRibbon.dll
├── TaskPane/       → Servidor HTTP + frontend
├── Include/        → Mock headers (R, Julia, Excel SDK)
├── tests/          → 342 tests con GTest
├── startup/        → Scripts de inicio R, Julia, Python
├── libreria/       → Funciones R, Julia, Python
├── Ejemplos/       → 80+ ejemplos organizados por lenguaje
├── docs/           → Documentación completa
└── Install/        → Instalador y distribución
```

---

## Evolución del Proyecto

| Versión | Fecha | Hito |
|---------|-------|------|
| BERT | 2017 | Toolkit original (solo R) |
| R4XCL | 2023 | Fork con R moderno |
| RJ2XCL v1.0 | Ene 2026 | +Julia 1.12.6 |
| RJ2XCL v2.0 | Abr 2026 | +WebView2, Pluto, Quarto |
| NEVEN v2.0 | May 2026 | Rename, +Pivot, D3, Dashboard |
| NEVEN v2.5 | Jun 2026 | +Python reactivado |
| NEVEN v3.0 | Jul 2026 | +NEVEN Studio, DuckDB |
| NEVEN v3.1 | Jul 2026 | +RAG Engine, Chat IA |
| **NEVEN v3.2** | **Ago 2026** | **+NEVEN-SIM, 342 tests, instalador** |

---

## Licencia

GNU General Public License v3.0 (GPLv3)

---

*NEVEN v3.2 — BukloLAB — Tesis de Maestría, Universidad de Costa Rica*
