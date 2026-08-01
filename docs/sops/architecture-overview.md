# Architecture Overview — NEVEN 2.0

> This document consolidates the architectural design of NEVEN. It serves as the definitive reference for contributors and academic reviewers.

## 1. System Purpose

NEVEN is a C++17 Excel add-in that enables users to call R, Julia, and Python functions directly from Excel cell formulas (e.g., `=NEVEN.r.myFunc(A1)`), and also operates as **NEVEN Studio Standalone** — a browser-based interface that runs without Microsoft Excel.

The system operates as a **bridge**: it converts data between Excel's native `XLOPER12` structures, Protocol Buffers for IPC, and the native types of each scripting language (`SEXP` for R, `jl_value_t` for Julia).

---

## 2. Three-Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: Standards & Governance                         │
│  docs/sops/  —  coding-standards, error-handling, etc.   │
├──────────────────────────────────────────────────────────┤
│  Layer 2: Control & Orchestration                        │
│  LanguageManager, CallbackDispatcher, RibbonService,     │
│  FileWatchService, ConfigService, DiscoveryService       │
├──────────────────────────────────────────────────────────┤
│  Layer 3: Core Infrastructure                            │
│  RaiiXlOper, TypeConversions, Named Pipes, Protobuf,     │
│  SecurityService, LogService, COM type-libraries         │
└──────────────────────────────────────────────────────────┘
```

### Layer 1 — Standards and Governance
Defines code conventions, error handling patterns, and operational procedures. All SOPs are stored in `docs/sops/`.

### Layer 2 — Orchestration
Controls the lifecycle of R and Julia engines, routes callbacks between them and Excel, manages the Ribbon UI, and watches for file changes. Key classes:

| Class | Responsibility |
|-------|---------------|
| `LanguageManager` | Dynamic registry for scripting engine services |
| `CallbackDispatcher` | Routes callbacks from R/Julia to Excel (Command Dispatcher pattern) |
| `RibbonService` | Manages the COM-based Excel Ribbon UI |
| `FileWatchService` | Monitors user script directories for hot-reloading |
| `ConfigService` | Reads/writes JSON configuration with graceful fallback |
| `DiscoveryService` | Auto-detects R/Julia installations via Windows Registry |

### Layer 3 — Core
Handles memory management, type conversion, IPC, and security. Key components:

| Component | Purpose |
|-----------|---------|
| `RaiiXlOper` | RAII wrapper for `XLOPER12` — deterministic cleanup via `xlFree` |
| `Result<T,E>` | Error handling without exceptions — explicit success/failure |
| `Named Pipes` + Protobuf | IPC between the in-process DLL and out-of-process R/Julia |
| `SecurityService` | SHA-256 verification of user scripts |
| `LogService` | Structured logging with severity levels |

---

## 3. Component Diagram

```
┌───────────────────────────────────────────────────────────┐
│                    Microsoft Excel                         │
│                                                           │
│   ┌────────────────┐  XLL API   ┌────────────────┐       │
│   │ NEVEN64.xll   │◄─────────►│ Excel C API    │       │
│   │ (= NEVEN.dll) │ Excel12v  │ (XLOPER12)     │       │
│   └───────┬────────┘           └────────────────┘       │
└───────────┼─────────────────────────────────────────────┘
            │ in-process
            ▼
┌───────────────────────────────────────────────────────────┐
│                     NEVEN.dll                             │
│                                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │ RJ2XCL_Engine│ │ Language     │ │ Callback        │   │
│  │ (Singleton)  │ │ Manager      │ │ Dispatcher      │   │
│  └──────────────┘ └──────┬───────┘ └─────────────────┘   │
│                          │                                 │
│  ┌──────────────┐ ┌──────┴───────┐ ┌─────────────────┐   │
│  │ RaiiXlOper   │ │ Language     │ │ COM Object Map  │   │
│  │ (RAII guard) │ │ Service(s)   │ │ (Excel COM)     │   │
│  └──────────────┘ └──────────────┘ └─────────────────┘   │
│                                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │ Type         │ │ Ribbon       │ │ FileWatch       │   │
│  │ Conversions  │ │ Service      │ │ Service         │   │
│  └──────────────┘ └──────────────┘ └─────────────────┘   │
└───────────────────────────┬───────────────────────────────┘
                            │ Named Pipes (Protobuf)
              ┌─────────────┴─────────────┐
              ▼                           ▼
   ┌──────────────────┐       ┌──────────────────┐
   │   ControlR.lib   │       │ ControlJulia.lib │
   │                  │       │                  │
   │ • R Interface    │       │ • Julia Interface│
   │ • GDI+ Graphics  │       │ • Julia Convert  │
   │ • SEXP Convert   │       │ • MIME Pipeline   │
   └────────┬─────────┘       └────────┬─────────┘
            │ LoadLibrary              │ LoadLibrary
            ▼                          ▼
       ┌──────────┐              ┌───────────┐
       │  R.dll   │              │ libjulia  │
       │ (4.x+)   │              │ (1.x+)    │
       └──────────┘              └───────────┘
```

---

## 9. NEVEN Studio Standalone (July 2026)

NEVEN Studio is a **second host mode** that replaces the Excel XLL with a Python HTTP server. All three language engines (ControlR.exe, ControlJulia.exe, ControlPython.exe) are reused unchanged.

### Startup Comparison

| | Excel Mode | Studio Mode |
|---|---|---|
| Host initiates engines | `NEVEN64.xll` (C++) | `start_studio.py` (Python) |
| UI | Excel Task Pane | Browser at `http://localhost:5555` |
| API | Excel C API (XLOPER12) | HTTP REST (JSON) |
| Data input | Excel cell ranges | CSV/Parquet/JSON via DuckDB |
| Requires Excel | Yes | No |

### Studio Component Diagram

```
NEVEN Studio.vbs
  → pythonw.exe start_studio.py
    → ControlPython.exe
      → neven_http_server.py (port 5555)
        → datalab_handler.py      (Data Lab endpoints)
        → pipe_client.py          (Named Pipe client)
          → ControlR.exe   (Named Pipe: neven_r)
          → ControlJulia.exe (Named Pipe: neven_j)
    → Browser opens http://localhost:5555
      → taskpane.html + datalab.js + taskpane.js
```

### HTTP API Routes

| Method | Route | Handler |
|--------|-------|---------|
| GET | `/` | Serve `taskpane.html` |
| POST | `/api/r` | Execute R code via ControlR |
| POST | `/api/python` | Execute Python code via ControlPython |
| POST | `/api/julia` | Execute Julia code via ControlJulia |
| POST | `/api/load_file` | Load CSV/Parquet/JSON into DuckDB |
| POST | `/api/query` | SQL query on DuckDB `dataset` table |
| GET | `/api/datalab/catalog` | Scan `C:\NEVEN\functions\*.json` for catalog |
| POST | `/api/datalab/run` | Run Studio wrapper via ControlR + r_object_to_slots |

### Data Lab Architecture

The Data Lab tab implements a guided analytics interface:

```
Browser (datalab.js)
  ├── GET /api/datalab/catalog → scan *.json sidecars → FunctionCard[]
  └── POST /api/datalab/run
        → DataLabHandler.handle_run()
        → DuckDB: SELECT assigned columns FROM dataset WHERE filter
        → build R script: data_X <- ...; result <- FunctionId.Studio(data_X, params)
        → pipe_client.send_code(r_lines) → ControlR.exe
        → r_object_to_slots(result, tier_map) → Variable(arr)
        → parse slots → JSON response → UI renders table/html/scalar
```

**Key abstraction — `r_object_to_slots`:** A startup R function that converts any S3 object into a list of typed slots, enabling a uniform UI representation regardless of the function's native return type.

**Sidecar JSON Convention:** Each analytics function has a companion `.json` metadata file defining variable roles, parameters, and UI behavior. New functions are discovered automatically by scanning `C:\NEVEN\functions\*.json`.

---

## 4. Data Flow

```
Excel Cell ──► XLOPER12 ──► TypeConversions ──► Protobuf Variable
                                                       │
                                                 Named Pipe
                                                       │
                                                       ▼
                                          R: SEXP  /  Julia: jl_value_t
                                                       │
                                                  (execute)
                                                       │
                                                       ▼
                                               Protobuf Response
                                                       │
                                                 Named Pipe
                                                       │
                                                       ▼
Excel Cell ◄── XLOPER12 ◄── TypeConversions ◄── Protobuf Variable
```

---

## 5. Module Structure

| Module | Output | Description |
|--------|--------|-------------|
| `NEVEN/` | `NEVEN.dll` | Core engine — Excel API, COM, orchestration |
| `ControlR/` | `ControlR.lib` | R language integration (parse, eval, GDI+) |
| `ControlJulia/` | `ControlJulia.lib` | Julia language integration (eval, MIME) |
| `Common/` | `Common.lib` | Shared utilities (pipes, config, security, logging) |
| `PB/` | `PB.lib` | Protocol Buffers serialization layer |
| `Ribbon/` | `NEVENRibbon2x64.dll` | COM ATL Ribbon (built via MSBuild) |
| `Addin/` | `NEVEN64.xll` | XLL packaging target (copy of DLL) |
| `OfficeTypes/` | (headers) | Pre-generated COM type libraries for Excel |

---

## 6. Key Design Decisions

### 6.1 RAII for XLOPER12
**Problem:** The Excel C API requires manual `xlFree` calls for every allocated `XLOPER12`. Missing a call produces memory leaks; double-frees produce access violations.

**Solution:** `RaiiXlOper` wraps `XLOPER12` with C++ RAII semantics. Move-only (no copy). Destructor calls `xlFree` automatically when the wrapper leaves scope.

### 6.2 Result\<T,E\> instead of Exceptions
**Problem:** Exceptions in XLL callbacks can crash Excel silently.

**Solution:** `Result<T,E>` forces callers to check success before accessing data. Includes `void` specialization.

### 6.3 Mock Headers for Compilation
**Problem:** Compiling the C++ bridge requires R, Julia, and Excel SDK headers, but developers shouldn't need all three installed.

**Solution:** `include/` contains mock headers that declare all necessary types and function signatures without implementation. Real libraries are loaded at runtime via `LoadLibrary`/`GetProcAddress`.

### 6.4 Protobuf for IPC
**Problem:** Efficient, typed serialization between in-process C++ and out-of-process R/Julia.

**Solution:** Protocol Buffers provide backward-compatible, schema-defined message formats. The `variable.proto` schema defines 20+ message types.

### 6.5 Language-Agnostic Engine Registry
**Problem:** Adding a new language should not require modifying the core Excel bridge.

**Solution:** `LanguageManager` acts as a dynamic registry. To add Python, implement `LanguageService` for Python — no changes to orchestration or the Excel bridge.

---

## 7. Security Model

- **SandboxVerifier**: Scans scripts for dangerous patterns (`system()`, `os.execute`, etc.) before execution
- **SecurityService**: Computes SHA-256 hashes and verifies against `.sha256` sidecar files
- **AutoLoader**: Only loads scripts from the controlled user directory (`Documents/NEVEN/functions/`)

---

## 8. Build System

The project uses **CMake 3.15+** with C++17. Dependencies are auto-fetched:

- Protocol Buffers v21.12 via `FetchContent`
- Google Test v1.14.0 via `FetchContent`

The Ribbon COM DLL is compiled separately via MSBuild (`scripts/build-ribbon.ps1`).

Full build command:
```powershell
.\build.ps1 -Clean -Test -Package
```

---

*Version: 1.1.0 | Status: Active | Language: English*
*Updated: July 2026 — Added Studio Standalone and Data Lab (sections 9)*
*Consolidated from architectural reports v1–v4*
