# Evolución de la Arquitectura de NEVEN

**Documento consolidado de la evolución arquitectónica del proyecto**
**Fecha:** Agosto 2026 | **Versión actual:** NEVEN v3.2

---

## Resumen Ejecutivo

Este documento traza la evolución de NEVEN desde su origen como BERT Toolkit (2017) hasta su estado actual como plataforma analítica integral (2026). La transformación no fue incremental — fue una reconstrucción completa sobre principios de C++ moderno, orquestación desacoplada y seguridad de memoria.

---

## Línea de Tiempo

```
2017        2023        Ene 2026    Abr 2026    May 2026    Jul 2026    Ago 2026
  │           │            │           │           │           │           │
BERT ──────► R4XCL ─────► v1.0 ─────► v2.0 ─────► v2.5 ─────► v3.0 ─────► v3.2
  │           │            │           │           │           │           │
Solo R    R moderno    +Julia     +WebView2   +Python    +Studio      +SIM
monolito  CMake        Protobuf   Pluto       reactivado DuckDB       342 tests
0 tests   básico       100 tests  Quarto      Sandbox    RAG          9.71/10
```

---

## Fase 0: BERT Toolkit (2017)

### Características

| Aspecto | Estado |
|---------|--------|
| Lenguajes | R 3.4.x, Julia 0.6.2 (obsoletos) |
| Arquitectura | Monolítica (clase principal con 15+ responsabilidades) |
| Visualización | PNG estático en hoja |
| Configuración | Hardcoded |
| Tests | 0 |
| Seguridad | Sin sandbox |
| Build | MSBuild/Visual Studio |

### Diagrama

```
Excel ←──→ XLL ←──→ ControlR.exe (R 3.4)
                    ControlJulia.exe (Julia 0.6)
```

### Problemas identificados

- Memory leaks conocidos (Pipe, XLOPER)
- Race conditions en callbacks
- Debug artifacts (std::cout) en producción
- TODOs/FIXMEs: 20+
- Sin health monitoring
- Sin reconexión automática

---

## Fase 1: Modernización Base (Enero 2026)

### Hitos

- **Migración a CMake 3.15+** con C++17
- **Protobuf actualizado** de v3.5.0 a v21.12 (FetchContent)
- **Headers mock** creados para R, Julia, Excel SDK
- **Julia actualizado** a 1.12.6
- **R actualizado** a 4.4.1

### Arquitectura v1.0

```
Excel ←──→ XLL ←──→ ControlR.exe (R 4.4.1)
          │         ControlJulia.exe (Julia 1.12.6)
          │
          └──→ Named Pipes + Protobuf (Variable)
```

### Logros

| Métrica | BERT | v1.0 |
|---------|------|------|
| Tests | 0 | ~100 |
| R | 3.4.x | 4.4.1 |
| Julia | 0.6.2 | 1.12.6 |
| Build | MSBuild | CMake |

---

## Fase 2: Desacoplamiento (Abril 2026)

### Hitos arquitectónicos

1. **Extracción de servicios** del monolito:
   - `ConfigService` — Configuración centralizada
   - `LanguageManager` — Orquesta R, Julia, Python
   - `WindowManager` → `ViewerManager` — Gestión de WebView2

2. **IExcelBridge** — Abstracción del host Excel para testing

3. **CallbackDispatcher** — Patrón dispatcher para callbacks:
   - `GraphicsHandler` — Gráficos
   - `COMHandler` — COM automation

4. **Result<T, E>** — Manejo de errores determinista

### Diagrama v2.0

```
Excel ←──→ XLL ←──→ ControlR.exe (R 4.4.1)
          │         ControlJulia.exe (Julia 1.12.6)
          │
          ├──→ WebView2 ──→ Plotly, D3.js, HTML
          ├──→ Pluto.jl ──→ Notebooks reactivos
          ├──→ Quarto ──→ Reportes HTML
          └──→ NEVENRibbon.dll ──→ Ribbon COM
```

### Nuevas capacidades

- Gráficos interactivos (Plotly, D3.js)
- Notebooks reactivos (Pluto.jl)
- Reportes profesionales (Quarto)
- Ribbon COM nativo

---

## Fase 3: Robustez y Seguridad (Mayo-Junio 2026)

### Hitos

1. **RAII para Excel SDK**:
   - `RaiiXlOper` — Wrapper determinista para XLOPER12
   - Eliminadas fugas de memoria históricas

2. **Security Remediation**:
   - 36/36 hallazgos resueltos
   - Score: 6.0/10 → 9.4/10

3. **SandboxVerifier**:
   - 30+ patrones bloqueados por lenguaje
   - Prevención de inyección

4. **Python reactivado**:
   - ControlPython.exe con Stable ABI
   - 4 bugs resueltos (retry startup, SEH guard, single-block, health check)

5. **MSVC Hardening**:
   - /GS, /guard:cf, /sdl
   - /DYNAMICBASE, /NXCOMPAT, /CETCOMPAT

### Tests

| Versión | Tests |
|---------|-------|
| v2.0 | ~100 |
| v2.5 | 205 |
| Post-security | 357 |

---

## Fase 4: NEVEN Studio (Julio 2026)

### Hitos

1. **HTTP Server** (Python, puerto 5555):
   - `neven_http_server.py`
   - DuckDB integrado
   - RAG Engine

2. **TaskPane con 7 tabs**:
   - SQL — Consultas DuckDB
   - Data Studio — Análisis exploratorio
   - Run Script — REPL R/Python/Julia
   - Data Lab — Notebooks
   - Presentaciones — Quarto/Impress.js
   - IA — Chat con RAG
   - Ayuda — 16 capítulos

3. **RAG Engine**:
   - FastEmbed (bge-small-en-v1.5)
   - DuckDB VSS
   - 300+ entidades de ontología

### Diagrama v3.0

```
Excel ←──→ XLL ←──→ ControlR.exe
          │         ControlJulia.exe
          │         ControlPython.exe
          │
          ├──→ WebView2 ──→ Plotly, D3, Leaflet
          ├──→ Pluto.jl
          ├──→ Quarto
          ├──→ NEVENRibbon.dll
          │
          └──→ HTTP Server (:5555)
                    │
                    ├──→ DuckDB (SQL)
                    ├──→ RAG Engine
                    └──→ AI Chat (Bedrock)
                              │
                              └──→ NEVEN Studio (TaskPane)
```

---

## Fase 5: Consolidación (Agosto 2026)

### NEVEN v3.2 — Estado actual

1. **NEVEN-SIM**: Módulo de Simulación Monte Carlo (XLL separado)

2. **342 tests** (228 Core + 114 NEVEN-SIM)

3. **RAG multilingüe** (EN/ES/PT/FR)

4. **12+ formatos** de documentos (PDF, DOCX, PPTX, XLSX, EPUB, etc.)

5. **Instalador automatizado** (`Install-NEVEN.ps1`)

6. **21 capítulos** de documentación Docusaurus

### Métricas finales

| Métrica | BERT (2017) | NEVEN v3.2 (2026) |
|---------|-------------|-------------------|
| Lenguajes | 2 (obsoletos) | 3 (actuales) |
| Tests | 0 | 342 |
| UDFs | ~25 | 200+ |
| Visualización | PNG estático | WebView2 interactivo |
| SQL | No | DuckDB |
| IA | No | RAG + Bedrock |
| Seguridad | Ninguna | 30+ patrones bloqueados |
| Score | ~4/10 | 9.71/10 |

---

## Arquitectura Final v3.2

```
┌───────────────────────────────────────────────────────────────────┐
│                        Microsoft Excel                             │
│                                                                   │
│   ┌──────────────┐                          ┌──────────────┐      │
│   │ NEVEN64.xll │◄────── XLL API ─────────►│  Excel C API │      │
│   └──────┬───────┘                          └──────────────┘      │
└──────────┼────────────────────────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────────┐
│                         NEVEN_Core                                 │
│                                                                   │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐               │
│  │ ConfigSvc   │ │ LanguageMgr  │ │ ViewerMgr     │               │
│  ├─────────────┤ ├──────────────┤ ├───────────────┤               │
│  │ SecuritySvc │ │ SandboxVerif │ │ PostMsgBridge │               │
│  └─────────────┘ └──────────────┘ └───────────────┘               │
└───────────────────────────────┬───────────────────────────────────┘
                                │
      ┌─────────────────────────┼─────────────────────────┐
      ▼                         ▼                         ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ ControlR.exe │       │ControlJulia  │       │ControlPython │
│   (R 4.4.1)  │       │ (Julia 1.12) │       │ (Python 3.13)│
└──────────────┘       └──────────────┘       └──────────────┘
       │ Protobuf            │ Protobuf            │ Protobuf
       │ Named Pipes         │ Named Pipes         │ Named Pipes
       ▼                     ▼                     ▼
   ┌───────┐             ┌───────┐             ┌───────┐
   │ R.dll │             │libjulia│            │python3│
   └───────┘             └───────┘             └───────┘

┌───────────────────────────────────────────────────────────────────┐
│                    HTTP Server (Python :5555)                      │
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
│  ┌─────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌─────┐ ┌────┐ ┌─────┐│
│  │ SQL │ │Data      │ │Run     │ │Data    │ │Pres.│ │ IA │ │Ayuda││
│  └─────┘ │Studio    │ │Script  │ │Lab     │ └─────┘ └────┘ └─────┘│
│          └──────────┘ └────────┘ └────────┘                       │
└───────────────────────────────────────────────────────────────────┘
```

---

## Lecciones Aprendidas

### Técnicas

1. **RAII es esencial** — El wrapper `RaiiXlOper` eliminó una clase completa de bugs
2. **Protobuf para IPC** — Hace el core agnóstico al lenguaje
3. **Sandbox temprano** — La seguridad no se puede agregar después
4. **Tests desde el inicio** — De 0 a 342 tests requirió disciplina constante

### Organizacionales

1. **Documentar mientras se construye** — Los 21 capítulos de Docusaurus no se escribieron al final
2. **Refactorizar continuamente** — El monolito se descompuso en 4 fases, no de golpe
3. **Mantener compatibilidad** — Prefijos `RJ_` internos preservados para ABI

### Estratégicas

1. **No parchar, reconstruir** — NEVEN no es un parche de BERT
2. **Modularizar antes de escalar** — Studio solo fue posible después de desacoplar
3. **Offline primero** — RAG funciona sin conexión gracias a FastEmbed local

---

## Referencias

| Documento | Ubicación |
|-----------|-----------|
| Estado_de_arquitectura_v2.md | `docs/Estado/` |
| Estado_de_arquitectura_v3.md | `docs/Estado/` |
| Estado_de_arquitectura_v4.md | `docs/Estado/` |
| Estado_agosto_2026.md | `docs/Estado/` |
| Bert_vs_RJ2XCL_arquitectura.md | `docs/Contexto/` |

---

*NEVEN v3.2 — BukloLAB — Evolución arquitectónica 2017-2026*
