---
id: evolucion-arquitectura
title: Capítulo 22 -- Evolución Arquitectónica
sidebar_label: 22. Evolución 2017-2026
sidebar_position: 22
---

# Capítulo 22: De BERT a NEVEN — Evolución Arquitectónica 2017-2026

Este capítulo documenta la transformación completa desde BERT Toolkit (2017) hasta NEVEN v3.2 (2026). No fue una evolución incremental — fue una reconstrucción sobre principios de C++ moderno, orquestación desacoplada y seguridad de memoria.

---

## 22.1 Línea de Tiempo

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

## 22.2 Fase 0: BERT Toolkit (2017) — Los Orígenes

### ¿Qué era BERT?

BERT (Basic Excel R Toolkit) fue un proyecto open-source creado por SDLLC que permitía ejecutar funciones R y Julia directamente desde celdas de Excel. Desarrollado bajo licencia GPL v3, BERT representó la primera solución seria para integrar lenguajes estadísticos con Excel sin depender de RExcel o add-ins comerciales.

:::info Fuente histórica
La documentación original de BERT Toolkit está disponible en [bert-toolkit.com](https://bert-toolkit.com/) y el código fuente en [GitHub](https://github.com/sdllc/Basic-Excel-R-Toolkit). NEVEN reconoce a BERT como la inspiración original del proyecto.
:::

### Características de BERT

| Aspecto | Implementación BERT |
|---------|---------------------|
| **Prefijo de funciones** | `R.FunctionName` (ej: `=R.Sort(A1:A10)`) |
| **Hot-reload** | BERT detectaba cambios en archivos `.R` y recargaba automáticamente |
| **Categorías** | Funciones agrupadas via `attr(func, "category")` |
| **Descripciones** | Documentación inline via `attr(func, "description")` |
| **Formulas array** | Soporte completo con Ctrl+Shift+Enter |
| **Scripting Excel** | Interface `EXCEL$Application` para manipular celdas desde R |

### Funciones de ejemplo originales de BERT

BERT incluía funciones de demostración que mostraban sus capacidades:

```r
# Sort — Ordenar vectores
attr(Sort, "description") <- "Sort a list"
attr(Sort, "category") <- "Examples"

# Shuffle — Barajar aleatoriamente
attr(Shuffle, "category") <- "Examples"

# PCA — Análisis de componentes principales
attr(PCA, "description") <- "Principal components analysis"
attr(PCA, "category") <- "Statistics"

# Correlation — Matriz de correlación
attr(Correlation, "description") <- "Correlation matrix"
attr(Correlation, "category") <- "Statistics"

# Cholesky — Descomposición Cholesky
attr(Cholesky, "category") <- "Statistics"
```

### Scripting de Excel desde R

BERT ofrecía una característica única: manipular Excel desde R usando COM automation:

```r
# Obtener la aplicación Excel
EXCEL$Application

# Leer rango de celdas
range <- EXCEL$Application$get_Range("Sheet1!A1:B10")
valores <- range$Value()

# Escribir en celdas
range$put_Value(matrix(1:20, nrow=10))

# Macros y hojas
EXCEL$Run.Macro("MiMacro")
EXCEL$Calculate.Sheet("Sheet1")
```

### Consola de BERT

BERT incluía una consola separada (basada en Electron) con:
- Shell R interactivo
- Editor de código con resaltado de sintaxis
- Visor de gráficos

### Stack tecnológico BERT

| Componente | Versión/Tecnología |
|------------|-------------------|
| R | 3.4.x |
| Julia | 0.6.2 |
| Protobuf | 3.5.0 |
| Build | MSBuild / Visual Studio |
| Licencia | GPL v3 |
| Tests | 0 |

### Arquitectura BERT

```
┌─────────────────────────────────────────┐
│            Microsoft Excel              │
└─────────────────┬───────────────────────┘
                  │ XLL API
                  ▼
┌─────────────────────────────────────────┐
│           BERT.xll (monolítico)         │
│  ┌──────────────────────────────────┐   │
│  │  Clase principal con 15+         │   │
│  │  responsabilidades mezcladas:    │   │
│  │  - Config (hardcoded)            │   │
│  │  - Conexiones                    │   │
│  │  - Callbacks                     │   │
│  │  - Logging (std::cout)           │   │
│  │  - etc.                          │   │
│  └──────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │ Named Pipes + Protobuf 3.5
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ ControlR.exe  │   │ControlJulia   │
│  (R 3.4.x)    │   │ (Julia 0.6.2) │
└───────────────┘   └───────────────┘
```

### Problemas técnicos identificados en BERT

| Problema | Impacto |
|----------|---------|
| Memory leaks en Pipe y XLOPER | Degradación gradual del rendimiento |
| Race conditions en callbacks | Crashes esporádicos |
| Debug artifacts (`std::cout`) en producción | Ruido en logs |
| 20+ TODOs/FIXMEs sin resolver | Deuda técnica acumulada |
| Sin health monitoring | Excel debía reiniciarse si R crasheaba |
| Sin reconexión automática | Pérdida de conexión = reinicio manual |
| Configuración hardcoded | Cero flexibilidad |

### Lo que BERT hizo bien

A pesar de sus limitaciones, BERT estableció patrones valiosos:

1. **Prefijo `R.` para funciones** — Claro y no invasivo
2. **Hot-reload de código** — Productividad en desarrollo
3. **Atributos para metadatos** — `category` y `description` como estándar
4. **Protobuf para IPC** — Decisión correcta que NEVEN heredó
5. **Named Pipes** — Comunicación eficiente en Windows

---

## 22.3 Fase 1: Modernización Base (Enero 2026)

### El salto a C++17 y CMake

La primera fase fue fundamentalmente técnica: actualizar todo el stack sin cambiar la arquitectura.

| Componente | BERT | v1.0 |
|------------|------|------|
| C++ | C++11 | **C++17** |
| Build | MSBuild | **CMake 3.15+** |
| Protobuf | 3.5.0 | **21.12** (FetchContent) |
| R | 3.4.x | **4.4.1** |
| Julia | 0.6.2 | **1.12.6** |
| Tests | 0 | **~100** |

### Mock headers

Para permitir tests sin Excel, R ni Julia instalados:

```cpp
// Include/mock/R.h
#define SEXP void*
#define Rf_allocVector(type, n) nullptr
// ... 50+ símbolos mockeados
```

### Arquitectura v1.0

```
Excel ←──→ XLL ←──→ ControlR.exe (R 4.4.1)
          │         ControlJulia.exe (Julia 1.12.6)
          │
          └──→ Named Pipes + Protobuf 21.12 (Variable.proto)
```

---

## 22.4 Fase 2: Desacoplamiento (Abril 2026)

### Extracción de servicios del monolito

La clase principal de BERT tenía 15+ responsabilidades. Se descompuso en servicios especializados:

| Servicio nuevo | Responsabilidad extraída |
|----------------|--------------------------|
| `ConfigService` | Configuración (antes hardcoded) |
| `LanguageManager` | Orquestación de R/Julia |
| `LanguageService` | Un proceso hijo específico |
| `ViewerManager` | Gestión de visualizadores |
| `LogService` | Logging estructurado |

### IExcelBridge

Abstracción del host Excel para testing:

```cpp
class IExcelBridge {
public:
    virtual XLOPER12* CallFunction(const std::string& name, ...) = 0;
    virtual void RegisterFunction(const std::string& name, ...) = 0;
    // ...
};

class MockExcelBridge : public IExcelBridge {
    // Implementación para tests sin Excel
};
```

### CallbackDispatcher

Patrón dispatcher para callbacks de lenguajes:

```cpp
class CallbackDispatcher {
    std::map<CallbackType, std::unique_ptr<ICallbackHandler>> handlers_;
public:
    void Register(CallbackType type, std::unique_ptr<ICallbackHandler> handler);
    void Dispatch(CallbackType type, const CallbackData& data);
};
```

### Result<T, E>

Manejo de errores determinista inspirado en Rust:

```cpp
template<typename T, typename E = std::string>
class Result {
public:
    static Result Ok(T value);
    static Result Err(E error);
    bool is_ok() const;
    T unwrap();
    // ...
};
```

### Nuevas capacidades v2.0

| Capacidad | Tecnología |
|-----------|------------|
| Gráficos interactivos | WebView2 + Plotly/D3.js |
| Notebooks reactivos | Pluto.jl |
| Reportes profesionales | Quarto |
| Ribbon COM nativo | NEVENRibbon.dll |

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

---

## 22.5 Fase 3: Robustez y Seguridad (Mayo-Junio 2026)

### RaiiXlOper — Eliminación de memory leaks

```cpp
class RaiiXlOper {
    XLOPER12 op_;
public:
    RaiiXlOper() { op_.xltype = xltypeNil; }
    ~RaiiXlOper() { xlFree(&op_); }  // Siempre libera
    XLOPER12* get() { return &op_; }
    // Move semantics, no copy
};
```

**Impacto:** 100% de XLOPER12 ahora usan RAII. Eliminada toda una clase de bugs.

### Security Remediation

| Métrica | Antes | Después |
|---------|-------|---------|
| Hallazgos de seguridad | 36 | **0** |
| Score de seguridad | 6.0/10 | **9.4/10** |

### SandboxVerifier

```cpp
class SandboxVerifier {
    std::vector<std::regex> blocked_patterns_r_;
    std::vector<std::regex> blocked_patterns_julia_;
    std::vector<std::regex> blocked_patterns_python_;
public:
    Result<void, std::string> Verify(Language lang, const std::string& code);
};
```

**30+ patrones bloqueados por lenguaje:**

| R | Julia | Python |
|---|-------|--------|
| `system()`, `shell()` | `run()`, `Base.run` | `os.system()`, `subprocess` |
| `Sys.*` | `Sys.*` | `eval()`, `exec()` |
| `file.remove()`, `unlink()` | `rm()`, `Base.Filesystem.rm` | `__import__()` |
| `download.file()` | `download()` | `open()` con rutas peligrosas |

### Python reactivado

ControlPython.exe usa **Stable ABI** (`python3.dll`) para compatibilidad entre versiones:

```cpp
// No linkea a python312.dll específico
// Usa python3.dll genérico
#define Py_LIMITED_API 0x03090000
#include <Python.h>
```

### MSVC Hardening

```cmake
add_compile_options(/GS /guard:cf /sdl)
add_link_options(/DYNAMICBASE /NXCOMPAT /CETCOMPAT)
```

### Tests post-seguridad

| Versión | Tests |
|---------|-------|
| v2.0 | ~100 |
| v2.5 | 205 |
| Post-security | 357 |

---

## 22.6 Fase 4: NEVEN Studio (Julio 2026)

### HTTP Server

```python
# neven_http_server.py (puerto 5555)
class NEVENHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/r':
            return self.execute_r()
        elif self.path == '/api/query':
            return self.execute_sql()
        elif self.path == '/api/rag/query':
            return self.rag_query()
        # ...
```

### TaskPane con 7 tabs

| Tab | Función |
|-----|---------|
| SQL | Consultas DuckDB sobre datos de Excel |
| Data Studio | Análisis exploratorio con gráficos |
| Run Script | REPL para R, Python, Julia |
| Data Lab | Notebooks sin código |
| Presentaciones | Quarto + Impress.js |
| IA | Chat con RAG |
| Ayuda | 16 capítulos integrados |

### RAG Engine

```python
class RAGEngine:
    def __init__(self):
        self.db = duckdb.connect('rag_index.duckdb')
        self.embedder = fastembed.TextEmbedding('bge-small-en-v1.5')
        self.ontology = OntologyService()
    
    def query(self, question: str, top_k: int = 3) -> List[Chunk]:
        # 1. Expandir términos con ontología
        expanded = self.ontology.expand(question)
        # 2. Generar embedding
        embedding = self.embedder.embed(expanded)
        # 3. Búsqueda vectorial
        return self.db.execute("""
            SELECT content, score, source, page
            FROM chunks
            ORDER BY array_distance(embedding, ?) 
            LIMIT ?
        """, [embedding, top_k]).fetchall()
```

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

## 22.7 Fase 5: Consolidación (Agosto 2026) — NEVEN v3.2

### NEVEN-SIM

Módulo de Simulación Monte Carlo como XLL separado:

```excel
=SIM.Fit(Datos, "lognormal")           → Ajuste de distribución
=SIM.Simulate(Params, 10000)           → 10,000 muestras
=SIM.VaR(Simulacion, 0.95)             → Value at Risk 95%
=SIM.Sensibilidad(Modelo, Variables)   → Análisis de sensibilidad
```

### 342 tests

| Suite | Tests |
|-------|-------|
| Core Tests | 228 |
| NEVEN-SIM Tests | 114 |
| **Total** | **342** |

### RAG multilingüe

Soporte para consultas en ES, EN, PT, FR con traducción automática de términos técnicos.

### 12+ formatos de documentos

| Formato | Extensiones |
|---------|-------------|
| PDF | .pdf |
| Word | .docx |
| PowerPoint | .pptx |
| Excel | .xlsx, .xls |
| EPUB | .epub |
| HTML/Texto | .html, .txt, .md, .csv, .json |

---

## 22.8 Comparación Final: BERT vs NEVEN v3.2

| Dimensión | BERT (2017) | NEVEN v3.2 (2026) |
|-----------|-------------|-------------------|
| **Lenguajes** | 2 (obsoletos) | 3 (actuales) |
| **R** | 3.4.x | 4.4.1 |
| **Julia** | 0.6.2 | 1.12.6 |
| **Python** | No | 3.13 |
| **Tests** | 0 | 342 |
| **UDFs** | ~25 | 200+ |
| **Visualización** | PNG estático | WebView2 interactivo |
| **Notebooks** | No | Pluto.jl reactivo |
| **SQL** | No | DuckDB integrado |
| **IA** | No | RAG + Bedrock |
| **Seguridad** | Ninguna | 30+ patrones bloqueados |
| **Score** | ~4/10 | **9.71/10** |

---

## 22.9 Lecciones Aprendidas

### Técnicas

1. **RAII es esencial** — `RaiiXlOper` eliminó una clase completa de bugs de memoria
2. **Protobuf para IPC** — Decisión correcta de BERT que NEVEN heredó y modernizó
3. **Sandbox temprano** — La seguridad no se puede agregar después
4. **Tests desde el inicio** — De 0 a 342 requirió disciplina constante

### Organizacionales

1. **Documentar mientras se construye** — Los 22 capítulos de Docusaurus no se escribieron al final
2. **Refactorizar continuamente** — El monolito se descompuso en 4 fases, no de golpe
3. **Mantener compatibilidad ABI** — Prefijos `RJ_` internos preservados

### Estratégicas

1. **No parchar, reconstruir** — NEVEN no es un parche de BERT
2. **Modularizar antes de escalar** — Studio solo fue posible después de desacoplar
3. **Offline primero** — RAG funciona sin conexión gracias a FastEmbed local
4. **Reconocer orígenes** — BERT estableció patrones valiosos que NEVEN respeta

---

## 22.10 Arquitectura Final v3.2

```
┌───────────────────────────────────────────────────────────────────┐
│                        Microsoft Excel 64-bit                      │
└───────────────────────────────────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────────┐
│                      NEVEN_Core (NEVEN64.xll)                      │
│                                                                   │
│  Capa 1: Interface    │  Capa 2: Servicios   │  Capa 4: Tools     │
│  ─────────────────    │  ─────────────────   │  ───────────────   │
│  RJ2XCL_Engine        │  ConfigService       │  Pipe              │
│  basic_functions      │  LanguageManager     │  type_conversions  │
│  RaiiXlOper           │  SandboxVerifier     │  Protobuf v21.12   │
│  NEVENRibbon.dll      │  SecurityService     │  json11            │
└───────────────────────────────────────────────────────────────────┘
           │
           │  Named Pipes + Protocol Buffers
           ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ControlR.exe   │  │ ControlJulia.exe│  │ControlPython.exe│
│    (R 4.4.1)    │  │  (Julia 1.12.6) │  │  (Python 3.13)  │
│                 │  │                 │  │  Stable ABI     │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                    Capa 3: Subsistemas                             │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  WebView2   │  │  Pluto.jl   │  │   Quarto    │                │
│  │(Edge/Chromium)│ │ (Notebooks) │  │  (Reportes) │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                   │
│  ┌─────────────────────────────────────────────────┐              │
│  │           HTTP Server (Python :5555)             │              │
│  │  ┌─────────┐  ┌───────────┐  ┌─────────────┐   │              │
│  │  │ DuckDB  │  │RAG Engine │  │  AI Chat    │   │              │
│  │  │  (SQL)  │  │(FastEmbed)│  │  (Bedrock)  │   │              │
│  │  └─────────┘  └───────────┘  └─────────────┘   │              │
│  └─────────────────────────────────────────────────┘              │
│                                                                   │
│  ┌─────────────────────────────────────────────────┐              │
│  │              NEVEN-SIM.xll                       │              │
│  │  Simulación Monte Carlo | Fitting | VaR         │              │
│  └─────────────────────────────────────────────────┘              │
└───────────────────────────────────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────────┐
│                      NEVEN Studio (TaskPane)                       │
│  ┌─────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌─────┐ ┌────┐ ┌─────┐│
│  │ SQL │ │Data      │ │Run     │ │Data    │ │Pres.│ │ IA │ │Ayuda││
│  │     │ │Studio    │ │Script  │ │Lab     │ │     │ │    │ │     ││
│  └─────┘ └──────────┘ └────────┘ └────────┘ └─────┘ └────┘ └─────┘│
└───────────────────────────────────────────────────────────────────┘
```

---

## 22.11 Extensibilidad

### Agregar nuevo lenguaje

1. Crear `ControlNuevoLenguaje.exe` siguiendo el protocolo Protobuf
2. Implementar `LanguageService` en C++
3. Registrar en `LanguageManager`
4. Agregar sección en `neven-config.json`

### Agregar nueva función

**Para R:**
1. Crear archivo `.R` en `C:\NEVEN\functions\`
2. Agregar atributos `description` y `category` (herencia de BERT)
3. Hot-reload automático

**Para Data Lab:**
1. Crear archivo `.Studio.R` o `.Studio.py`
2. Crear sidecar JSON con metadatos
3. Función aparece automáticamente en catálogo

### Agregar tab a NEVEN Studio

1. HTML en `taskpane.html`
2. Handlers JavaScript
3. Endpoint en `neven_http_server.py` si necesario

---

## 22.12 Reconocimientos

NEVEN reconoce a **BERT Toolkit** y a **SDLLC** como la inspiración original del proyecto. Los patrones establecidos por BERT (prefijo `R.`, atributos de metadatos, Protobuf para IPC) siguen presentes en NEVEN v3.2.

:::tip Evolución, no revolución
NEVEN no es un parche de BERT — es una reinvención completa que supera al original en +5.7 puntos (de ~4/10 a 9.71/10). Pero sin BERT, NEVEN no existiría.
:::

---

*NEVEN v3.2 — BukloLAB — Evolución arquitectónica 2017-2026*
*Tesis de Maestría, Universidad de Costa Rica*
