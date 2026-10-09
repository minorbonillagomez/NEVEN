# Estado de Arquitectura: NEVEN v3.2

**Reporte Arquitectónico Actual**
**Fecha:** Agosto 2026 | **Versión:** 3.2 | **Score:** 9.71/10

---

## Resumen Ejecutivo

NEVEN v3.2 representa el estado de madurez industrial del proyecto. La arquitectura actual permite escalabilidad (nuevos lenguajes), mantenibilidad (desacoplamiento total) y extensibilidad (NEVEN Studio con 7 tabs).

---

## Auditoría de Capas

### Capa 1: Interface Excel (XLL)

| Componente | Estado | Descripción |
|------------|--------|-------------|
| `RJ2XCL_Engine` | ✅ Óptimo | Singleton principal, Init/Close/callbacks |
| `basic_functions` | ✅ Óptimo | 200+ funciones exportadas a Excel |
| `NEVENRibbon.dll` | ✅ Óptimo | Ribbon COM con 17 botones |
| `RaiiXlOper` | ✅ Óptimo | Wrapper RAII para XLOPER12 |

### Capa 2: Servicios del Núcleo

| Servicio | Estado | Descripción |
|----------|--------|-------------|
| `ConfigService` | ✅ Óptimo | Lee `neven-config.json`, getters tipados |
| `LanguageManager` | ✅ Óptimo | Orquesta R, Julia, Python |
| `LanguageService` | ✅ Óptimo | Un proceso hijo: pipe, timeout, reconnect |
| `SandboxVerifier` | ✅ Óptimo | 30+ patrones bloqueados por lenguaje |
| `SecurityService` | ✅ Óptimo | SHA-256 integridad de scripts |
| `DiscoveryService` | ✅ Óptimo | Detecta R, Julia, Python |
| `LogService` | ✅ Óptimo | Logging estructurado |

### Capa 3: Subsistemas Especializados

| Subsistema | Estado | Componentes |
|------------|--------|-------------|
| WebView2 | ✅ Óptimo | ViewerManager, ViewerWindow, PostMessageBridge |
| Pluto.jl | ✅ Óptimo | PlutoManager, NotebookLibrary |
| Quarto | ✅ Óptimo | CreateProcess externo |
| HTTP Server | ✅ Óptimo | neven_http_server.py (puerto 5555) |
| RAG Engine | ✅ Óptimo | rag_engine.py, DuckDB VSS, FastEmbed |

### Capa 4: Herramientas Comunes

| Herramienta | Estado | Uso |
|-------------|--------|-----|
| `Pipe` | ✅ Óptimo | Named Pipe wrapper |
| `type_conversions` | ✅ Óptimo | XLOPER12 ↔ Protobuf |
| `json11` | ✅ Óptimo | Parser JSON |
| Protocol Buffers | ✅ Óptimo | v21.12 para IPC |

---

## Análisis de Robustez

| Criterio | Estado | Evidencia |
|----------|--------|-----------|
| **Código Determinista** | ✅ | Result<T,E> en servicios, TypeConversions puro |
| **Error Handling** | ✅ | Patrón Result propagado en toda la cadena |
| **Memoria Segura** | ✅ | 100% XLOPER12 con RAII |
| **Testabilidad** | ✅ | 342 tests (228 Core + 114 NEVEN-SIM) |
| **Seguridad** | ✅ | 30+ patrones sandbox, SHA-256, MSVC hardening |

---

## Métricas de Calidad

| Dimensión | Nota | Evidencia |
|-----------|------|-----------|
| Funcionalidad | 10/10 | 200+ UDFs, 7 tabs Studio, RAG |
| Calidad de Código | 9.5/10 | 0 TODOs, RAII, Result<T,E> |
| Seguridad | 9.5/10 | Sandbox, SHA-256, MSVC hardening |
| Mantenibilidad | 9.7/10 | 4 capas desacopladas |
| Confiabilidad | 9.5/10 | Health monitoring, reconnect |
| Testing | 10/10 | 342 tests, 100% pass |
| Documentación | 10/10 | 21 capítulos Docusaurus |
| **Promedio** | **9.71/10** | |

---

## Diagrama de Arquitectura

```
┌───────────────────────────────────────────────────────────────────┐
│                        Microsoft Excel 64-bit                      │
└───────────────────────────────────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────────┐
│                         NEVEN_Core (XLL)                           │
│                                                                   │
│  Capa 1: Interface    │  Capa 2: Servicios   │  Capa 4: Tools     │
│  ─────────────────    │  ─────────────────   │  ───────────────   │
│  RJ2XCL_Engine        │  ConfigService       │  Pipe              │
│  basic_functions      │  LanguageManager     │  type_conversions  │
│  RaiiXlOper           │  SandboxVerifier     │  Protobuf          │
│  NEVENRibbon          │  SecurityService     │  json11            │
└───────────────────────────────────────────────────────────────────┘
           │
           │  Named Pipes + Protobuf
           ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ControlR.exe   │  │ ControlJulia.exe│  │ControlPython.exe│
│    (R 4.4.1)    │  │  (Julia 1.12.6) │  │  (Python 3.13)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                    Capa 3: Subsistemas                             │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  WebView2   │  │  Pluto.jl   │  │   Quarto    │                │
│  │  (HTML/JS)  │  │ (Notebooks) │  │  (Reportes) │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                   │
│  ┌─────────────────────────────────────────────────┐              │
│  │           HTTP Server (Python :5555)             │              │
│  │  ┌─────────┐  ┌───────────┐  ┌─────────────┐   │              │
│  │  │ DuckDB  │  │RAG Engine │  │  AI Chat    │   │              │
│  │  │  (SQL)  │  │(FastEmbed)│  │  (Bedrock)  │   │              │
│  │  └─────────┘  └───────────┘  └─────────────┘   │              │
│  └─────────────────────────────────────────────────┘              │
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

---

## Componentes

### Binarios

| Componente | Tipo | Descripción |
|------------|------|-------------|
| NEVEN64.xll | XLL | Add-in principal (~2.5 MB) |
| NEVENRibbon.dll | COM | Ribbon nativo |
| ControlR.exe | EXE | Embebe R via C API |
| ControlJulia.exe | EXE | Embebe Julia |
| ControlPython.exe | EXE | Embebe Python (Stable ABI) |
| neven_julia.dll | Sysimage | Julia precompilada (~415 MB) |
| NEVEN-SIM.xll | XLL | Simulación Monte Carlo |

### Servidor HTTP

| Archivo | Función |
|---------|---------|
| neven_http_server.py | Servidor principal (puerto 5555) |
| rag_engine.py | RAG con DuckDB + FastEmbed |
| pipe_client.py | Cliente de Named Pipes |
| variable_pb2.py | Protobuf generado |

### Librerías de código

| Biblioteca | Archivos | Descripción |
|------------|----------|-------------|
| Common.lib | 15+ | Servicios compartidos |
| PB.lib | 2 | Protocol Buffers |
| R functions | 62+ | Funciones R registradas |
| Julia modules | 11 | Módulos J4XCL |

---

## Flujo de Datos

```
Usuario escribe fórmula
         │
         ▼
┌─────────────────────┐
│ =R.MR_Lineal(Y,X,1) │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   NEVEN64.xll       │
│   basic_functions   │
│   XLOPER12 → PB     │
└─────────────────────┘
         │ Named Pipe
         ▼
┌─────────────────────┐
│   ControlR.exe      │
│   PB → SEXP         │
│   R eval()          │
│   SEXP → PB         │
└─────────────────────┘
         │ Named Pipe
         ▼
┌─────────────────────┐
│   NEVEN64.xll       │
│   PB → XLOPER12     │
│   Return to Excel   │
└─────────────────────┘
         │
         ▼
    Resultado en celda
```

---

## Configuración

### neven-config.json

```json
{
  "R": { "enabled": true, "home": "" },
  "Julia": { "enabled": true, "home": "" },
  "Python": { "enabled": true },
  "RAG": {
    "enabled": true,
    "minScore": 0.50,
    "topK": 3,
    "indexPath": "C:\\NEVEN\\data\\rag_index.duckdb"
  },
  "WebView2": { "maxViewers": 8 },
  "Pluto": { "port": 1234 },
  "sandboxEnabled": true,
  "callTimeoutMs": 600000
}
```

---

## Seguridad

### Mecanismos implementados

| Mecanismo | Descripción |
|-----------|-------------|
| SandboxVerifier | 30+ patrones bloqueados por lenguaje |
| SHA-256 | Integridad de scripts startup |
| MSVC Hardening | /GS, /guard:cf, /sdl, /DYNAMICBASE |
| Config validation | Prevención de path traversal |
| WebView2 filter | Whitelist de CDNs |

### Patrones bloqueados (ejemplo R)

```
system(), shell(), Sys.*, file.remove(), unlink(),
download.file(), source() con URLs, eval(parse(text=...))
```

---

## Testing

### Suites

| Suite | Tests | Cobertura |
|-------|-------|-----------|
| Core Tests | 228 | Sandbox, Config, RAII, COM |
| NEVEN-SIM Tests | 114 | Simulación Monte Carlo |
| Property-Based | 15+ | Hipótesis, fuzzing |
| **Total** | **342** | **100% pass** |

### Frameworks

- Google Test v1.14.0
- rapidcheck (Property-Based Testing)

---

## Deuda Técnica Resuelta

| Problema original | Solución |
|-------------------|----------|
| Memory leaks (XLOPER12) | RaiiXlOper wrapper |
| Race conditions | Mutex en callbacks |
| Debug artifacts | Eliminados de producción |
| Hardcoded paths | ConfigService |
| Sin reconexión | Health monitoring + retry |
| Sin seguridad | SandboxVerifier + SHA-256 |

---

## Extensibilidad

### Agregar nuevo lenguaje

1. Crear `ControlNuevoLenguaje.exe`
2. Implementar `LanguageService` para el lenguaje
3. Registrar en `LanguageManager`
4. Agregar sección en `neven-config.json`

### Agregar nueva función R

1. Crear archivo `.R` en `Documentos\NEVEN\functions\`
2. Agregar atributos `description` y `category`
3. Hot-reload automático

### Agregar tab a NEVEN Studio

1. Agregar HTML en `taskpane.html`
2. Implementar handlers en JavaScript
3. Agregar endpoint en `neven_http_server.py` si necesario

---

## Estado: Aprobado para Producción

La arquitectura de NEVEN v3.2 cumple con todos los criterios de calidad industrial:

- ✅ Determinismo (Result<T,E>)
- ✅ Seguridad de memoria (RAII)
- ✅ Testabilidad (342 tests)
- ✅ Desacoplamiento (4 capas)
- ✅ Documentación (21 capítulos)
- ✅ Score 9.71/10

---

## Referencias

| Documento | Descripción |
|-----------|-------------|
| Evolucion_de_Arquitectura.md | Historia completa 2017-2026 |
| Estado_de_arquitectura_v2.md | Post-Fase 1 |
| Estado_de_arquitectura_v3.md | Post-Fase 2 |
| Estado_de_arquitectura_v4.md | Post-Fase 3 |

---

*NEVEN v3.2 — BukloLAB — Estado arquitectónico actual*
