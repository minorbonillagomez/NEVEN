# Contexto Completo del Proyecto NEVEN v2.0

**Documento de referencia para modelos de IA y desarrolladores**
**Fecha**: 3 de mayo de 2026 | **Versión**: 1.0

---

## 1. IDENTIDAD DEL PROYECTO

**NEVEN** es un add-in XLL de alto rendimiento para Microsoft Excel que integra los lenguajes **R 4.4.1** y **Julia 1.12.6** como motores de scripting embebidos. Permite ejecutar funciones estadísticas, modelos de machine learning y visualizaciones interactivas directamente desde celdas de Excel.

- **Nombre anterior**: R4XCL / RJ2XCL / BERT Toolkit
- **Nombre actual**: NEVEN (palíndromo; del esperanto "invicto"; en eslavo, la caléndula "flor que no se marchita")
- **Autor**: Minor Bonilla Gómez
- **Contexto académico**: Tesis de Maestría en Matemática Aplicada, Universidad de Costa Rica
- **Licencia**: GNU General Public License v3.0
- **Origen**: Fork modernizado de BERT (Basic Excel R Toolkit) por Structured Data, LLC
- **Lenguaje principal**: C++17 (MSVC, Visual Studio 2022)
- **Build system**: CMake 3.15+
- **Plataforma**: Windows 10+ (64-bit), Excel 2013/2016/2019/365

---

## 2. QUÉ HACE NEVEN (Resumen Funcional)

El usuario escribe fórmulas en celdas de Excel y obtiene resultados de R o Julia:

```
=NEVEN.r("1+1")                    → 2
=NEVEN.j("sqrt(144)")              → 12
=R.MR_Lineal(Y, X, 1)             → Modelo de regresión lineal
=J.Algebra(A1:B2, 0, 6)           → Determinante de matriz
=NEVEN.v(R.Pivot(A1:E11, 1))      → Tabla pivote interactiva en WebView2
=NEVEN.q("reporte.qmd")           → Reporte Quarto renderizado en WebView2
=NEVEN.pluto.start()              → Inicia servidor Pluto.jl
=NEVEN.r("system('dir')")         → BLOCKED (sandbox de seguridad)
```

### Capacidades principales
- **~90 funciones R** (regresión, ACP, SVM, series de tiempo, panel data, mapas)
- **~70 funciones Julia** (álgebra lineal, cálculo, EDO, KNN, clustering, optimización)
- **Visualización interactiva**: Plotly, D3.js (Treemap, Sankey, Sunburst, Force), Leaflet (mapas), rpivotTable
- **WebView2**: Visor HTML embebido con Edge Chromium para gráficos interactivos
- **Pluto.jl**: Notebooks reactivos con pipeline de datos Excel→Julia→Pluto
- **Quarto**: Renderizado de documentos .qmd → HTML → WebView2
- **Ribbon COM**: Pestaña nativa "NEVEN" en Excel con 13 botones y 5 grupos
- **Sandbox**: 30+ patrones bloqueados por lenguaje (shell, archivos, red, código nativo, bypass)
- **228 tests automatizados** (GTest, 100% pass rate)
- **Hot-reload**: FileWatchService detecta cambios en .R y .jl automáticamente
- **Errores descriptivos**: Mensajes reales de R/Julia en celdas (no `#VALOR!`)

---

## 3. ARQUITECTURA (4 Capas)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA 1: Interface Excel (XLL)                    │
│  RJ2XCL_Engine · basic_functions · MenuService · function_descriptor│
├─────────────────────────────────────────────────────────────────────┤
│                 CAPA 2: Servicios del Núcleo                        │
│  ConfigService · LanguageManager · LanguageService · SecurityService│
│  SandboxVerifier · DiscoveryService · LogService                    │
├─────────────────────────────────────────────────────────────────────┤
│              CAPA 3: Subsistemas Especializados                     │
│  ViewerManager · ViewerWindow · PlutoManager · ContentPipeline      │
│  PostMessageBridge · NotebookLibrary · NotebookExporter             │
│  PresentationBuilder                                                │
├─────────────────────────────────────────────────────────────────────┤
│              CAPA 4: Herramientas Comunes                           │
│  Pipe · WindowManager · EnvService · child_process_log              │
│  string_utilities · type_conversions · module_functions · json11    │
└─────────────────────────────────────────────────────────────────────┘
```

### Diagrama de componentes en runtime

```
┌───────────────────────────────────────────────────────┐
│                   Microsoft Excel                      │
│  ┌─────────────────────────────────────────────────┐  │
│  │              NEVEN64.xll (= NEVEN.dll)          │  │
│  │  • Registra ~125 funciones via xlfRegister      │  │
│  │  • Sandbox valida código arbitrario             │  │
│  │  • Convierte XLOPER12 ↔ Protobuf               │  │
│  │  • WebView2 en STA thread dedicado              │  │
│  └──────────┬──────────────────┬───────────────────┘  │
└─────────────┼──────────────────┼──────────────────────┘
              │ Named Pipes      │ COM automation
              │ + Protobuf       │
    ┌─────────┴─────────┐       ▼
    │                   │   WebView2 (Edge Chromium)
┌───┴────┐        ┌────┴─────┐
│ControlR│        │ControlJ  │
│  .exe  │        │ ulia.exe │
│ R 4.4.1│        │Julia 1.12│
└────────┘        └──────────┘
```

### Principios de diseño
- **Aislamiento de procesos**: R/Julia corren en procesos separados; un crash no mata Excel
- **Protocolo agnóstico**: Protocol Buffers para IPC; agregar un lenguaje = crear ControlX.exe
- **RAII**: `RaiiXlOper` para manejo determinístico de memoria Excel; `Result<T,E>` sin excepciones
- **Mock headers**: Compilación sin R, Julia ni Excel SDK instalados (headers en `include/`)
- **Carga dinámica**: R.dll y libjulia se cargan en runtime via `LoadLibrary`/`GetProcAddress`

---

## 4. MÓDULOS DEL CÓDIGO FUENTE

| Módulo | Output | Descripción |
|:---|:---|:---|
| `Core/` (NEVEN_Core) | `NEVEN.dll` | Corazón: singleton Engine, funciones XLL, COM, type conversions, WebView2, Pluto, Quarto |
| `ControlR/` | `ControlR.exe` | Proceso hijo que embebe R: eval, parse, GDI+ graphics, conversiones SEXP |
| `ControlJulia/` | `ControlJulia.exe` | Proceso hijo que embebe Julia: eval, arrays, tipos, conversiones |
| `Common/` | `Common.lib` | Código compartido: pipes, config, security, logging, sandbox, viewers |
| `PB/` | `PB.lib` | Protocol Buffers: `variable.proto` con 20+ mensajes |
| `Ribbon/` | `NEVENRibbon.dll` | COM Add-in: pestaña nativa en Excel con IRibbonExtensibility |
| `Addin/` | `NEVEN64.xll` | Target de empaquetado: copia DLL → XLL + binarios al directorio Dist |
| `OfficeTypes/` | (headers) | Type libraries COM pre-generadas de Excel/Office (.tlh/.tli) |
| `Console/` | Electron app | Consola REPL (TypeScript/React) — pendiente de reconexión |
| `tests/` | `neven_tests.exe` | 228 tests con GTest v1.14.0 |
| `Include/` | (headers) | Mock headers de R, Julia y Excel SDK para compilación sin SDKs |
| `libreria/R/` | 32 archivos .R | Funciones R de la librería R4XCL (~90 procedimientos) |
| `libreria/JULIA/` | 5 archivos .jl | Funciones Julia: functions.jl (9 módulos) + 4 módulos J4XCL |
| `Ejemplos/` | (por lenguaje) | Ejemplos organizados en subcarpetas: R, Julia, Python, Quarto, Java |

### Archivos clave del XLL (NEVEN.dll)

| Archivo | Función |
|:---|:---|
| `NEVEN.cc` | Singleton `RJ2XCL_Engine`: Init/Close, gestión de procesos, callbacks |
| `basic_functions.cc` | ~125 funciones exportadas: `RJ_FunctionCall`, `RJ_Exec_Generic`, VIEW, PLUTO, QUARTO |
| `excel_api_functions.cc` | Registro de funciones R/Julia en Excel via `xlfRegister` |
| `type_conversions.h` | Conversiones `XLOPER12` ↔ Protobuf ↔ COM VARIANT |
| `language_service.cc` | Comunicación con ControlR/Julia vía Named Pipes |
| `xlcall_stubs.cc` | Stubs de `Excel12`/`Excel12v` con binding en runtime |
| `NEVEN.def` | Tabla de exports del DLL |

---

## 5. FLUJO DE DATOS

```
Excel XLOPER12 ←→ type_conversions ←→ Protobuf Variable ←→ Named Pipe ←→ R SEXP / Julia jl_value_t
   (Celdas)         (NEVEN.dll)          (PB.lib)         (Windows)      (ControlR/Julia)
```

### Flujo de inicialización (xlAutoOpen)
1. `LogService::Initialize()`
2. `ConfigService::Initialize()` ← `neven-config.json`
3. `SecurityService::Initialize()`
4. `LanguageManager::ConfigureLanguages()` ← `neven-languages.json`
   - `LanguageService[R]::Connect()` → lanza ControlR.exe, conecta Named Pipe
   - `LanguageService[Julia]::Connect()` → lanza ControlJulia.exe, conecta Named Pipe
5. `ViewerManager::Initialize()` ← WebView2 runtime detection + STA thread
6. `PlutoManager::Initialize()` ← Julia path resolution
7. `RJ2XCL_Engine::MapFunctions()` ← xlfRegister ~125 funciones
8. Timer (5s) → `UpdateFunctions()` + `MenuService::CreateMenu()`

---

## 6. COMUNICACIÓN INTER-PROCESOS

- **Named Pipes** bidireccionales por lenguaje, serializados con Protocol Buffers
- **Health monitoring**: `HealthStatus` enum (Healthy/Unavailable/Unknown)
- **Timeouts**: per-language configurable (default 30s R, 900s Julia primera llamada)
- **Reconnect**: máximo 2 reintentos con logging estructurado
- **COM automation**: WebView2 en STA thread, Excel _Application/Range via COM

---

## 7. CATÁLOGO DE FUNCIONES

### Funciones del sistema
| Función | Descripción |
|:---|:---|
| `=NEVEN.r("código")` | Ejecutar código R arbitrario (con sandbox) |
| `=NEVEN.j("código")` | Ejecutar código Julia arbitrario (con sandbox) |
| `=NEVEN.v(html_o_ruta)` | Abrir contenido en WebView2 |
| `=NEVEN.q("archivo.qmd")` | Renderizar documento Quarto |
| `=NEVEN.pluto.start/STOP/STATUS()` | Control del servidor Pluto.jl |
| `=NEVEN.pluto.data(rango,"nombre")` | Enviar datos de Excel a Julia/Pluto |
| `=NEVEN.notebook.open/LIST()` | Gestionar notebooks Pluto |
| `=NEVEN.editor()` | Editor de presentaciones Impress.js |

### Julia (nombres cortos con rangos)
| Función | Procedimientos |
|:---|:---|
| `=J.Algebra(rango,vector,tipo)` | 12: LU, QR, SVD, eigenvalores, det, normas, pseudoinversa |
| `=J.Calculo(X,Y,param,tipo)` | 7: derivada, integrales, bisección, interpolación, Taylor |
| `=J.EDO(intervalo,CI,h,tipo)` | 4: Euler, RK4, oscilador, 2do orden |
| `=J.Estadistica(datos,Y,tipo)` | 8: descriptiva, correlación, t-test, normalizar, outliers |
| `=J.KNN(X,Y,K,tipo)` | 5: clasificación, precision/recall/F1, confusión |
| `=J.Regresion(X,Y,param,tipo)` | 5: coeficientes, predicción, residuos, resumen |
| `=J.Clustering(datos,K,seed,tipo)` | 6: asignación, centros, WCSS, codo |
| `=J.Optimizar(A,b,lr,iter,tipo)` | 7: gradiente, Newton, simplex, NNLS, QP |
| `=J.Transformar(datos,col,val,tipo)` | 6: transponer, ordenar, filtrar, únicos |
| `=J.Utilidades(p1,p2,p3,tipo)` | 5: fecha, secuencias, aleatorios, redondeo |

### R — Estadística
| Módulo | Funciones |
|:---|:---|
| Regresión | MR_Lineal, MR_Binario, MR_Poisson, MR_Tobit, MR_PanelData, MR_SVM |
| Análisis de Datos | AD_ACP, AD_KMedias, AD_Descriptiva, AD_Psicometria |
| Series de Tiempo | ST_SeriesTemporales, ST_Autoregresivos, ST_Filtro |
| Gráficos | GR_PlotlyView, GR_QuickPlot (9 tipos: barras, líneas, scatter, histograma, box, pie + ggplot2/Plotly) |
| Mixtos | RG_Mixtos, RG_Supervivencia, RG_Bayesiana |

### R — Visualización interactiva
| Función | Librería | Tipos |
|:---|:---|:---|
| `=R.Pivot(rango, tipo)` | rpivotTable | Pivot libre, Heatmap, Barras |
| `=R.Esquisse(rango, tipo)` | Plotly.js | Scatter, Barras, Líneas, Box, Histograma, Heatmap |
| `=R.D3(rango, tipo)` | D3.js v7 | Treemap, Sankey, Sunburst, Force Graph |
| `=R.Dashboard(rango, tipo)` | Combinado | 6 tabs todo-en-uno |
| `=R.Map(rango, tipo)` | Leaflet.js | Marcadores, Mapa de calor, Círculos proporcionales |

---

## 8. SEGURIDAD (Sandbox)

### Patrones bloqueados en `=NEVEN.r()` y `=NEVEN.j()`
- **Shell**: `system()`, `shell()`, `run()`, backtick literals
- **Archivos**: `file.remove()`, `unlink()`, `rm()`, `mv()`
- **Red**: `download.file()`, `url()`, `socketConnection()`
- **Código nativo**: `.Call()`, `ccall()`, `dyn.load()`, `cglobal()`
- **Bypass dinámico**: `eval(parse())`, `paste()` concatenación, `do.call()`, `get()`
- **Config**: Path traversal (`..`) y command injection (`|`, `&`, `;`) bloqueados

### Protección contra bypass
- Whitespace stripping: `sys tem()` → detectado
- String concatenation: `paste0("sys","tem()")` → detectado
- Case insensitive: `SYSTEM()` → bloqueado

### Funciones registradas NO pasan por sandbox
`=R.MR_Lineal(...)` ejecuta código pre-cargado y confiable via `RJ_FunctionCall`.

---

## 9. TESTING

| Categoría | Tests |
|:---|:---:|
| Sandbox (R + Julia + Python) | 109 |
| Property-based (reliability + WebView2) | 8 |
| Property-based (Python sandbox) | 3 |
| Config, Security, Discovery | 16 |
| Type conversions, RAII, callbacks | 34 |
| Basic functions, COM | 35 |
| E2E tests | 8 |
| NewFunctionsSandboxTest | 16 |
| **Total** | **228** |

Framework: Google Test v1.14.0. Todos los tests corren **sin Excel, R ni Julia** gracias a `MockExcelBridge` y mock headers.

---

## 10. BUILD Y COMPILACIÓN

### Requisitos
- Visual Studio 2022 (C++ Desktop Development)
- CMake 3.15+
- R 4.4.1+ (solo para ControlR.exe; no requerido para tests)
- Julia 1.12.6+ (solo para ControlJulia.exe; no requerido para tests)

### Comandos
```cmd
cd Build
cmake .. -A x64 -DR_HOME="C:\Program Files\R\R-4.4.1"
cmake --build . --config Release
```

### CI-Only (sin R/Julia)
```cmd
cmake .. -A x64 -DSKIP_LANGUAGE_TARGETS=ON
cmake --build . --config Release --target neven_tests
```

### Outputs
| Target | Output |
|:---|:---|
| NEVEN_Core | `NEVEN/Release/NEVEN.dll` |
| ControlR | `ControlR/Release/ControlR.exe` |
| ControlJulia | `ControlJulia/Release/ControlJulia.exe` |
| NEVENRibbon | `Ribbon/Release/NEVENRibbon.dll` |
| Addin | `Dist/NEVEN64.xll` + binarios |
| neven_tests | `tests/Release/neven_tests.exe` |

### Dependencias auto-descargadas (FetchContent)
- Protocol Buffers v21.12
- Google Test v1.14.0
- WebView2 SDK v1.0.2903.40

---

## 11. ESTRUCTURA DE PRODUCCIÓN

```
C:\NEVEN\
├── NEVEN64.xll              # Add-in Excel
├── NEVENRibbon.dll           # COM Add-in (Ribbon)
├── ControlR.exe              # Proceso hijo R
├── ControlJulia.exe          # Proceso hijo Julia
├── neven_julia.dll           # Sysimage Julia (~415 MB, arranque en 1-2s)
├── neven-config.json         # Configuración global
├── neven-languages.json      # Definición de lenguajes
├── startup/
│   ├── startup.r             # Script inicio R
│   └── startup.jl            # Módulo NEVEN Julia + data exchange
├── notebooks/                # 15 notebooks Pluto precargados
├── data/                     # Datasets compartidos Excel↔Pluto (TSV)
├── quarto/                   # Documentos Quarto (.qmd)
├── webview2-data/            # HTML temporales
├── CreadorPresentaciones/    # Editor Impress.js
└── neven.log                 # Log del add-in
```

### Directorios del usuario
```
%USERPROFILE%\Documents\NEVEN\
├── functions/                # Archivos .R y .jl del usuario
└── graphics/                 # PNGs y HTMLs generados
```

---

## 12. CONFIGURACIÓN

### neven-config.json
```json
{
  "NEVEN": {
    "functionsDirectory": "%USERPROFILE%\\Documents\\NEVEN\\functions",
    "graphicsDirectory": "%USERPROFILE%\\Documents\\NEVEN\\graphics",
    "logFile": "%NEVEN_HOME%\\neven.log",
    "openConsole": false,
    "useJobObject": true,
    "callTimeoutMs": 600000,
    "maxRetries": 2,
    "sandboxEnabled": true,
    "R": { "home": "" },
    "Julia": { "home": "" }
  },
  "WebView2": { "enabled": true, "maxViewers": 8, "maxMemoryMB": 512 },
  "Pluto": { "port": 1234 }
}
```

### neven-languages.json
```json
[
  { "name": "R", "executable": "ControlR.exe", "prefix": "R", "extensions": ["r","R"] },
  { "name": "Julia", "executable": "ControlJulia.exe", "prefix": "J", "extensions": ["jl"] }
]
```

---

## 13. ESTÁNDARES DE CÓDIGO

| Elemento | Convención | Ejemplo |
|:---|:---|:---|
| Clases | `PascalCase` | `class LanguageManager` |
| Funciones | `snake_case` | `void register_functions()` |
| Variables locales | `snake_case` | `std::string file_path` |
| Miembros de clase | `snake_case_` | `int next_id_` |
| Constantes/Macros | `SCREAMING_SNAKE_CASE` | `MAX_BUFFER_SIZE` |
| Archivos | `.cc` (implementación), `.h` (headers) | `message_utilities.cc` |
| Comentarios | Doxygen en headers, "por qué" en implementación | `@brief`, `@param`, `@return` |

---

## 14. DEPENDENCIAS EXTERNAS EN RUNTIME

| Componente | Versión | Propósito |
|:---|:---|:---|
| R | 4.4.1+ | Motor estadístico |
| Julia | 1.12.6+ | Motor matemático/ML |
| Quarto | 1.9.18+ | Reportes (requiere junction `C:\Quarto`) |
| Pandoc | 3.6+ | Conversión de documentos (incluido con Quarto) |
| WebView2 Runtime | Edge | Visualización (preinstalado en Windows 10/11) |
| Pluto.jl | 0.20+ | Notebooks reactivos |

### Paquetes R requeridos
`stargazer`, `plm`, `sandwich`, `margins`, `plotly`, `htmlwidgets`, `ggplot2`, `rpivotTable`, `jsonlite`, `corrplot`, `lme4`, `survival`, `psych`, `forecast`, `car`, `maps`

### Paquetes Julia requeridos
`Pluto`, `RCall` (opcional), `JuMP`, `HiGHS`, `DifferentialEquations` (opcionales para notebooks)

---

## 15. FIXES CRÍTICOS (No revertir)

Estos cambios son esenciales para el funcionamiento. Revertir cualquiera rompe el sistema:

1. **Firma de MdCallBack12** (`xlcall_stubs.cc`): Orden `(xlfn, count, opers[], operRes)`
2. **Constantes Excel SDK** (`XLCALL.h`): `xlGetName=0x4019`, `xlCoerce=0x4002`, `xlFree=0x4000`
3. **Complex.h para MSVC** (`ControlR/include/R_ext/Complex.h`): `Rcomplex` como struct simple
4. **ReadConsole firma**: R 4.4.1 cambió `char*` → `unsigned char*`
5. **CharacterMode = LinkDLL**: Necesario para ejecutar sin consola
6. **Startup con wait=true**: Mantiene pipe sincronizado
7. **Export name RJ_FunctionCall**: Debe coincidir con el `.def`
8. **Fallback xlGetName**: Usa `GetModuleFileNameW` con corrección `.dll` → `.xll`
9. **thread_local XLOPER12**: Reemplaza `static` para thread safety en UDFs
10. **Julia julia_compat.h**: 10+ macros de traducción API Julia 0.6→1.12

---

## 16. DECISIONES ARQUITECTÓNICAS CLAVE

| Decisión | Justificación |
|:---|:---|
| Procesos hijo separados (ControlR/Julia) | Crash de R no mata Excel. Aislamiento de memoria |
| Protocol Buffers para IPC | Versionable, eficiente, independiente del lenguaje |
| WebView2 en STA thread dedicado | COM apartment threading requerido por WebView2 |
| Archivo TSV para Excel↔Pluto | Pluto corre en proceso Julia separado, no comparte memoria |
| Quarto como CreateProcess externo | Evita bloquear el pipe. Timeout de 60s |
| Junction C:\Quarto | Workaround para bug de Sass con espacios en ruta |
| CommandBar + Ribbon COM separado | XLL puro no puede registrar Ribbon sin COM Add-in |
| Python deprecado (OFF por defecto) | Causaba hangs. R+Julia cubren todos los casos de uso |
| Julia sysimage precompilada | PackageCompiler.jl genera neven_julia.dll (~415MB), cold start eliminado |

---

## 17. EVOLUCIÓN Y CALIDAD

| Fecha | Nota | Hito |
|:---|:---:|:---|
| 14 abril 2026 | 4.3 | Estado original — prototipo con deuda técnica |
| 15 abril | 6.8 | Seguridad, RAII, mutex, retry limits |
| 16 abril | 8.1 | Python (deprecado), mantenibilidad, confiabilidad |
| 19 abril | 8.9 | WebView2, Plotly interactivo |
| 22 abril | 9.0 | Pluto.jl, PLUTO.DATA, toolbar |
| 23 abril | 9.1 | Quarto, notebook genérico |
| 27 abril | 9.2 | Ribbon COM, callback thread, depuración, KNN/Regresión |
| **2 mayo** | **9.6** | **Rename NEVEN, 5 nuevas visualizaciones, 228 tests, Doxygen completo** |

### Dimensiones actuales (mayo 2026)
| Dimensión | Nota |
|:---|:---:|
| Funcionalidad | 10 |
| Calidad de Código | 9.5 |
| Seguridad | 9.5 |
| Mantenibilidad | 9.5 |
| Confiabilidad | 9.5 |
| Testing | 10 |
| Documentación | 10 |

---

## 18. PENDIENTES

| Tema | Prioridad |
|:---|:---|
| Instalador MSI/NSIS | Alta |
| PLUTO.READ (Pluto → Excel) | Media |
| CrashHandler (telemetría local) | Media |
| Consola REPL Electron | Media |
| Viewer título NEVEN (wstring resize bug) | Media |
| Idioma toggle (ES/EN) en Ribbon | Baja |
| Corrección EDO TipoOutput 2-4 (scope Julia 1.12) | Baja |
| R.Network (grafos con vis.js) | Baja |

---

## 19. TROUBLESHOOTING RÁPIDO

| Problema | Solución |
|:---|:---|
| Excel se congela al abrir | Matar procesos zombie: `Stop-Process -Name "EXCEL","ControlR","ControlJulia" -Force` |
| Ribbon no aparece | Limpiar `HKCU:\...\Resiliency\DisabledItems`, re-registrar `regsvr32 NEVENRibbon.dll` |
| `#NOMBRE?` en funciones | Verificar XLL cargado en Archivo→Opciones→Complementos |
| Julia "read error" | Esperar 15s (timer de recarga diferida) o verificar sysimage |
| Paquetes R faltantes | `=NEVEN.r("install.packages('paquete', repos='https://cran.r-project.org')")` |
| WebView2 no disponible | Verificar Edge WebView2 Runtime instalado |
| `R.Pivot` no abre viewer | Envolver: `=NEVEN.v(R.Pivot(rango, tipo))` |

---

## 20. MAPA DE DOCUMENTACIÓN Y CARPETAS CLAVE

| Carpeta/Documento | Contenido |
|:---|:---|
| `libreria/R/` | 32 archivos .R con ~90 procedimientos estadísticos (R4XCL) |
| `libreria/JULIA/` | 5 archivos .jl con ~70 procedimientos (functions.jl + J4XCL) |
| `Ejemplos/R/` | Ejemplos de funciones R y scripting |
| `Ejemplos/Julia/` | Ejemplos de funciones Julia |
| `Ejemplos/Quarto/` | Documentos .qmd de ejemplo + XLSX |
| `Ejemplos/Python/` | Funciones Python de ejemplo |
| `Ejemplos/Java/` | Ejemplo D3.js |
| `docs/arquitectura.md` | Arquitectura 4 capas, flujos, decisiones |
| `docs/ESTADO_DE_LAS_COSAS.md` | Historia completa, problemas resueltos, hitos |
| `docs/ESTADO_DEL_ARTE.md` | Catálogo de funciones, comparación con alternativas |
| `docs/EVALUACION_OBJETIVA.md` | Auditoría de calidad: de 4.3 a 9.6/10 |
| `docs/MANUAL_MANTENIMIENTO.md` | Build, deploy, troubleshoot, fixes críticos |
| `docs/TROUBLESHOOTING.md` | Guía de solución de problemas |
| `docs/DEPENDENCIAS_INSTALACION.md` | Todas las dependencias y checklist de verificación |
| `docs/coding-standards.md` | Convenciones de nomenclatura y estilo |
| `docs/EXPLICACION_NEVEN.md` | Identidad de marca, significado del nombre |
| `docs/descripcion.md` | Descripción técnica detallada de módulos |
| `docs/sops/architecture-overview.md` | Referencia arquitectónica en inglés |
| `docs/sops/testing-guide.md` | Cómo escribir y ejecutar tests |
| `docs/docusaurus/` | 10 capítulos para documentación web |
| `CHANGELOG.md` | Historial de cambios por versión |
| `CONTRIBUTING.md` | Guía para contribuidores |

---

*NEVEN v2.0 — Universidad de Costa Rica — Team Vikingos — SKÅL!*
*Documento generado: 3 de mayo de 2026*
