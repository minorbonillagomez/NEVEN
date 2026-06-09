# Guia de Evaluacion Doctoral — Proyecto NEVEN

**Fecha:** 9 de mayo de 2026
**Proposito:** Documento interno de orientacion para el autor. No es una evaluacion formal.
**Proyecto:** NEVEN v2.0 — Sistema Multilenguaje para Excel (R + Julia + Python)
**Autor:** Minor Bonilla Gomez
**Programa:** Maestria en Matematica Aplicada, Universidad de Costa Rica

---

## 1. Resumen del Proyecto

NEVEN es un add-in XLL de C++17 para Microsoft Excel que integra R 4.4.1, Julia 1.12.6 y Python 3.13 como motores de scripting embebidos. Permite ejecutar funciones estadisticas, modelos de machine learning y visualizaciones interactivas directamente desde celdas de Excel.

El proyecto evoluciona de BERT (Basic Excel R Toolkit, Structured Data LLC, 2017-2018), modernizandolo para versiones actuales de R, Julia y Python, agregando seguridad, testing, visualizacion interactiva via WebView2, notebooks reactivos via Pluto.jl, y reportes via Quarto.

### Que problema resuelve

Excel es la herramienta de analisis de datos mas usada del mundo, pero sus capacidades estadisticas nativas son limitadas. R y Julia son potentes pero requieren programacion. NEVEN cierra esta brecha: el usuario escribe `=R.MR_Lineal(Y, X, 1)` en una celda y obtiene un modelo de regresion lineal sin escribir codigo R.

### Alcance actual

- ~90 funciones R (regresion, ACP, SVM, series de tiempo, panel data, mapas)
- ~70 funciones Julia (algebra lineal, calculo, EDO, KNN, clustering, optimizacion)
- Python 3.13 como tercer lenguaje (ejecucion arbitraria, funciones de usuario, type conversion con numpy/pandas)
- AI/LLM Integration: Interpretacion automatica de resultados estadisticos via OpenAI, Ollama o LM Studio
- Visualizacion interactiva: Plotly, D3.js, Leaflet, rpivotTable en WebView2
- Notebooks reactivos: Pluto.jl con pipeline de datos Excel→Julia
- Reportes: Quarto (.qmd → HTML)
- Ribbon COM nativo con 13 botones
- 357 tests automatizados (GTest + rapidcheck PBT, 100% pass rate)
- Sandbox de seguridad: 5 mecanismos anti-bypass, InputSanitizer, MessageValidator

---

## 2. Contribuciones Tecnicas Reales

Estas son las contribuciones que un comite puede verificar objetivamente:

### 2.1 Arquitectura de aislamiento de procesos

R, Julia y Python corren en procesos separados (`ControlR.exe`, `ControlJulia.exe`, `ControlPython.exe`), comunicandose con el XLL via Named Pipes + Protocol Buffers. Un crash de cualquier lenguaje no mata Excel. Esta arquitectura es heredada de BERT pero fue modernizada significativamente:
- Protobuf actualizado de v3.5.0 a v21.12
- R actualizado de 3.4.x a 4.4.1 (requirio resolver incompatibilidades de API)
- Julia actualizada de 0.6.x a 1.12.6 (requirio reescribir 50+ llamadas de API)
- Sysimage precompilada elimina el cold start de Julia (de minutos a segundos)

### 2.2 Sandbox de seguridad

BERT no tenia sandboxing. NEVEN implementa `SandboxVerifier` con 5 mecanismos anti-bypass (whitespace stripping, concatenacion de strings, case insensitivity, context-aware detection, unified enforcement) para R, Julia y Python. Complementado por `InputSanitizer` (allowlist validation para CreateProcess paths), `MessageValidator` (validacion de frames Protobuf antes de deserializacion) y `SafePipeHandle` (RAII con operaciones atomicas para handles de Named Pipes). 154 tests cubren el sandbox y la seguridad.

**Limitacion honesta:** Es pattern-based, no un sandbox de OS (AppContainer/seccomp). Un atacante suficientemente motivado podria bypassearlo. Para la tesis, esto debe mencionarse como trabajo futuro.

### 2.3 RAII para memoria de Excel

`RaiiXlOper` encapsula `XLOPER12` con semantica RAII de C++. Esto resuelve un problema real: el SDK de Excel en C requiere llamadas manuales a `xlFree` que son faciles de olvidar. La clase es move-only, con destructor automatico. 4 tests cubren RAII, move semantics y xlFree.

### 2.4 Visualizacion interactiva embebida

BERT solo soportaba graficos PNG estaticos. NEVEN integra WebView2 (Edge Chromium) como visor embebido, permitiendo Plotly, D3.js, Leaflet y rpivotTable interactivos dentro de Excel. Esto es una innovacion genuina sobre el proyecto base.

### 2.5 Notebooks reactivos desde Excel

El pipeline `NEVEN.pluto.data(rango, "nombre")` envia datos de Excel a Julia via archivo TSV, que Pluto.jl lee para analisis reactivo. 15 notebooks precargados cubren PCA, algebra lineal, optimizacion, etc.

### 2.6 Mensajes de error descriptivos

BERT retornaba `#VALOR!` ante errores. NEVEN captura el mensaje real de R/Julia y lo muestra en la celda. Ejemplo: `R: Error in library(xyz) : no hay paquete llamado 'xyz'`. Mejora significativa de UX.

### 2.7 Integracion con IA (LLM-Powered Interpretation)

NEVEN integra funciones de IA via ControlPython.exe (Python 3.13 embebido) para ejecutar llamadas HTTP a proveedores de LLM. Las funciones AI (`P.ai_call`, `P.ai_setup`, `P.ai_list_prompts`) permiten interpretacion automatica de resultados estadisticos.

Caracteristicas:
- Soporta OpenAI, Azure OpenAI, Ollama (local/gratis) y LM Studio (local)
- 7 prompts predefinidos editables por el usuario
- Rate limiting thread-safe, HTTPS obligatorio, API key protegida

### 2.8 Investigación de optimización de startup y limitaciones de xlfRegister

Se diseñó e implementó una arquitectura de inicialización paralela (`InitOrchestrator`) para reducir el tiempo de arranque conectando los motores de lenguaje concurrentemente. Sin embargo, la investigación reveló una limitación fundamental del Excel SDK:

- **Hallazgo clave:** `xlfRegister` no puede ser invocado desde callbacks `WM_TIMER` fuera del contexto de `xlAutoOpen`. Retorna error 2 (función no disponible). Esto es una restricción no documentada del SDK de Excel.
- **Conflicto con Ribbon COM:** La inicialización paralela causaba race conditions con el COM Add-in del Ribbon, que invoca `SetPointers` antes de que todos los motores estén conectados.
- **Decisión arquitectónica:** Se revirtió al flujo secuencial probado: `ConnectLanguages()` → `InitializeConnectedLanguages()` → carga de archivos → `MapFunctions()` → `RegisterFunctions()`. La infraestructura `InitOrchestrator` permanece en el código para uso futuro.
- **Contribución:** Este trabajo documenta una limitación del SDK de Excel que no aparece en la documentación oficial de Microsoft, y demuestra por qué la inicialización de add-ins XLL debe ser estrictamente secuencial durante `xlAutoOpen`.

### 2.9 Corrección de race condition en SetPointers

`RJ2XCL_Engine::SetPointers()` presentaba un hang cuando el Ribbon COM Add-in lo invocaba antes de que todos los motores de lenguaje hubieran conectado. La corrección:

- `SetPointers()` ahora verifica el estado de conexión de cada servicio antes de llamar `SetApplicationPointer()`
- Si un servicio no está conectado, se omite sin error (en lugar de bloquear esperando el pipe)
- Esto permite que el Ribbon COM se cargue en cualquier orden relativo a los motores de lenguaje

Este fix demuestra la complejidad de coordinar múltiples componentes COM en un entorno multi-proceso donde el orden de inicialización no está garantizado.

### 2.10 Compatibilidad con versiones modernas

Lograr compatibilidad con R 4.4.1 y Julia 1.12.6 fue un esfuerzo tecnico significativo:
- R 4.4.1: `double _Complex` incompatible con MSVC, firma de `R_ReadConsole` cambiada, `structRstart` con campos adicionales
- Julia 1.12.6: 50+ funciones de API cambiadas (`jl_arrayset`, `ptls`, `jl_options`, etc.)
- Header de compatibilidad `julia_compat.h` con 10+ macros de traduccion

### 2.11 Extraccion universal de outputs de modelos (Extraer_outputs)

Nueva funcion R `Extraer_outputs(modelo)` en `startup.r` que extrae TODOS los outputs de cualquier objeto modelo de R (lm, glm, summary, etc.) y los retorna como un data.frame estructurado con columnas [Modelo, Seccion, Parametro, Metrica, Valor].

Caracteristicas:
- Funciona con cualquier modelo R (lm, glm, plm, arima, svm, etc.) sin conocer su estructura interna
- Omite campos no informativos (model, effects, qr, x, y, fitted.values) pero retiene residuals y todas las estadisticas
- Integrado como el TipoOutput mas alto en 11 funciones R4XCL: MR_Lineal(13), MR_Binario(9), MR_Poisson(8), MR_PanelData(16), ST_SeriesTemporales(8), MR_SVM(2), MR_Tobit(7), AD_ArbolDeDecision(9), AD_ACP(13), AD_KMedias(10)
- El usuario ejecuta una sola llamada (ej: `=R.MR_Lineal(Y, X, 13)`) y obtiene una tabla completa con todos los outputs del modelo

**Contribucion:** Resuelve el problema de "no se que outputs tiene este modelo" — el usuario no necesita conocer la estructura interna de los objetos R. Es una abstraccion universal sobre la heterogeneidad de outputs de modelos estadisticos.

### 2.12 Zombie Process Killer (fiabilidad de arranque)

Al inicio del XLL (`Init()`), NEVEN mata automaticamente procesos huerfanos de sesiones anteriores (ControlR.exe, ControlJulia.exe, ControlPython.exe) usando `taskkill /F /IM`. Implementado con `CreateProcess` y flag `CREATE_NO_WINDOW` para ejecucion no-bloqueante.

**Problema resuelto:** Cuando Excel era cerrado forzosamente (crash, Task Manager, Windows Update), los procesos hijo quedaban huerfanos ocupando los Named Pipes. Al reabrir Excel, NEVEN no podia conectar porque los pipes ya estaban en uso por los procesos zombi. El usuario debia abrir Task Manager manualmente.

**Contribucion:** Mejora la fiabilidad del sistema en escenarios reales de uso (crashes, cierres forzosos). Es un patron comun en sistemas multi-proceso pero su implementacion correcta en el contexto de un add-in XLL (donde no se puede bloquear `xlAutoOpen`) requiere ejecucion asincrona via `CreateProcess` sin ventana.

---

## 3. Evaluacion por Dimensiones

Basada en la auditoria interna documentada en `EVALUACION_OBJETIVA.md`, que registro la evolucion desde el estado original hasta el estado actual.

| Dimension | Estado original (14 abr) | Estado actual (3 may) | Evidencia |
|:---|:---:|:---:|:---|
| Funcionalidad | 7/10 | 10/10 | R + Julia + Python + WebView2 + Pluto + Quarto + Ribbon operativos |
| Calidad de codigo | 4/10 | 9.5/10 | 0 std::cout en produccion, Doxygen completo, RAII, thread_local |
| Seguridad | 2/10 | 9.5/10 | 36/36 hallazgos remediados, InputSanitizer, MessageValidator, SafePipeHandle, MSVC flags (/GS, /guard:cf, /sdl, /DYNAMICBASE, /NXCOMPAT, /CETCOMPAT) |
| Mantenibilidad | 3/10 | 9.7/10 | Repositorio reorganizado, TROUBLESHOOTING, paths centralizados |
| Confiabilidad | 4/10 | 9.5/10 | Health monitoring, reconnect con limites, CI/CD |
| Testing | 2/10 | 10/10 | 357 tests, property-based (rapidcheck), E2E, 0 regresiones |
| Documentacion | 8/10 | 10/10 | 15+ documentos, Docusaurus, Doxygen, manuales |

**Nota global: 9.6/10** — Promedio ponderado de las 7 dimensiones.

### Contexto de las calificaciones

Estas notas son internas y relativas al propio proyecto. No son comparables con otros proyectos doctorales. El 4.3 original refleja el estado del fork de BERT antes de las correcciones; el 9.6 refleja el estado despues de ~3 semanas de trabajo intensivo. Un comite evaluara el proyecto en su totalidad, no estas metricas internas.

---

## 4. Limitaciones y Trabajo Futuro

**Esta seccion es critica para la defensa.** Un comite doctoral espera autocritica honesta.

### 4.1 Limitaciones tecnicas

| Limitacion | Impacto | Mitigacion |
|:---|:---|:---|
| Sandbox pattern-based, no OS-level | Un atacante motivado podria bypassearlo | Documentar como trabajo futuro; recomendar AppContainer |
| Solo Windows | No funciona en macOS/Linux | Inherente a la arquitectura XLL de Excel; documentar como limitacion de plataforma |
| Tests corren con mocks, no con Excel real | No hay tests de integracion end-to-end en runtime | MockExcelBridge cubre la API; tests manuales en Excel documentados en UAT_Report |
| Python fue congelado y reactivado | Requirio 7 fixes para estabilizar (startup retry, stack guard, single-block startup, health check, NEVEN_HOME, config paths, prefix) | Documentar el proceso de debugging como caso de estudio de ingenieria |
| Consola REPL pendiente | BERT tenia consola Electron; NEVEN la reemplazó con REPL WebView2 | Consola REPL completada — WebView2 REPL implementado (REPLManager + REPLBridge) y Console/Electron eliminado del repositorio. Cero dependencias externas (no Electron, no Node.js, no npm) |
| Relacion con BERT | NEVEN toma la idea de comunicar Excel con R via procesos aislados | BERT era un prototipo con R 3.4 y Julia 0.6 (nunca funcional). NEVEN reimplementa el concepto correctamente: R 4.4.1, Julia 1.12.6, Python 3.13, seguridad, testing, visualizacion interactiva. Es la evolucion de una buena idea, ahora correctamente implementada |

### 4.2 Limitaciones academicas

| Limitacion | Recomendacion |
|:---|:---|
| No hay estudio de usuarios | Disenar un estudio piloto con estudiantes de la UCR |
| No hay benchmarks de rendimiento | Medir latencia de llamadas R/Julia vs VBA nativo |
| No hay comparacion formal con alternativas | Tabla comparativa con xlwings, PyXLL, RExcel (existe parcialmente en ESTADO_DEL_ARTE) |
| Validacion estadistica limitada a Wooldridge | Expandir a otros textos de referencia |

### 4.3 Trabajo futuro concreto

| Tema | Complejidad | Valor academico |
|:---|:---|:---|
| Sandbox OS-level (AppContainer) | Alta | Alto — publicable como paper de seguridad |
| Estudio de usabilidad con usuarios reales | Media | Alto — esencial para la tesis de "democratizacion" |
| Benchmarks de rendimiento | Baja | Medio — datos cuantitativos para la defensa |
| Instalador MSI/NSIS | Media | Bajo — operativo, no academico |
| Soporte macOS via Office.js | Alta | Medio — ampliar alcance |

---

## 5. Comparacion con BERT (Proyecto Base)

Esta tabla es util para la defensa porque demuestra el valor agregado:

| Capacidad | BERT (2017-2018) | NEVEN (2026) | Innovacion |
|:---|:---|:---|:---|
| R en Excel | R 3.4.x | R 4.4.1 | Actualizacion con fixes de API |
| Julia en Excel | Julia 0.6.x | Julia 1.12.6 | Reescritura completa de interfaz |
| Python en Excel | No | Python 3.13 (CPython embedding) | **Innovacion** |
| AI/LLM Integration | No | Interpretacion de resultados via OpenAI/Ollama/LM Studio | **Innovacion** |
| Consola REPL | No (abandonado) | WebView2 REPL autocontenido (0 MB extra, REPLManager + REPLBridge) | **Innovacion** |
| Graficos | PNG estatico | Plotly + D3 + Leaflet interactivos | **Innovacion** |
| Notebooks | No | Pluto.jl reactivos | **Innovacion** |
| Reportes | No | Quarto (.qmd → HTML/PDF) | **Innovacion** |
| Seguridad | Ninguna | Sandbox 5 mecanismos + InputSanitizer + MessageValidator + MSVC hardening + 36/36 audit findings resolved | **Innovacion** |
| Testing | 0 tests | 357 tests (GTest + rapidcheck PBT) | **Innovacion** |
| Errores | `#VALOR!` | Mensaje real de R/Julia/Python en celda | **Innovacion** |
| Config | Hardcoded | JSON centralizado con validacion | **Innovacion** |
| Ribbon | No | COM Add-in nativo | **Innovacion** |
| Documentacion | Sitio web basico | 15+ documentos + Docusaurus + Doxygen | **Innovacion** |
| CI/CD | No | GitHub Actions | **Innovacion** |

**Resumen:** De 15 capacidades comparadas, 13 son innovaciones sobre BERT.

---

## 6. Arquitectura del Sistema

### Diagrama de componentes

```
+-------------------------------------------+
|           Microsoft Excel                  |
|  +-------------------------------------+  |
|  |          NEVEN64.xll                 |  |
|  |  - Registra ~125 funciones           |  |
|  |  - Sandbox valida codigo             |  |
|  |  - Convierte Excel <-> Protobuf      |  |
|  |  - WebView2 en STA thread            |  |
|  +----------------+--------------------+  |
+-------------------|-----------------------+
                    | Named Pipes + Protobuf
          +---------+---------+---------+
     +----+----+ +---+------+ +----+-------+
     |ControlR | |ControlJ  | |ControlPy   |
     |  .exe   | |ulia.exe  | |thon.exe    |
     | R 4.4.1 | |Julia 1.12| |Python 3.13 |
     +---------+ +----------+ +------------+
```

### Estructura del repositorio

```
NEVEN/
+-- Core/              # NEVEN_Core (NEVEN.dll) — corazon del proyecto
+-- Common/            # Utilidades compartidas (Security/, IPC/, config, viewers)
+-- ControlR/          # Proceso hijo R
+-- ControlJulia/      # Proceso hijo Julia
+-- ControlPython/     # Proceso hijo Python
+-- PB/                # Protocol Buffers
+-- Ribbon/            # COM Ribbon
+-- libreria/R/        # 32 archivos .R (~90 procedimientos)
+-- libreria/JULIA/    # 5 archivos .jl (~70 procedimientos)
+-- Ejemplos/          # Organizados por lenguaje (R, Julia, Quarto)
+-- tests/             # 357 tests (GTest v1.14.0 + rapidcheck PBT)
+-- Build/             # Directorio de build CMake
+-- docs/              # Documentacion completa
```

---

## 7. Metricas Cuantitativas

| Metrica | Valor |
|:---|:---|
| Lenguaje principal | C++17 (MSVC 2022) |
| Funciones R expuestas a Excel | ~90 procedimientos en 32 archivos |
| Funciones Julia expuestas a Excel | ~70 procedimientos en 5 archivos |
| Tests automatizados | 357 (GTest + rapidcheck PBT, 100% pass rate) |
| Patrones de sandbox | 5 mecanismos anti-bypass + InputSanitizer + MessageValidator (R, Julia, Python) |
| Notebooks Pluto precargados | 15 |
| Dependencias auto-descargadas | Protobuf v21.12, GTest v1.14.0, rapidcheck, WebView2 SDK |
| Plataforma | Windows 10+ (64-bit), Excel 2013+ |

---

## 8. Preguntas Probables del Comite

Preparacion para la defensa — preguntas dificiles y como responderlas:

### "¿Cual es la contribucion original si BERT ya existia?"

BERT era un prototipo funcional para R 3.4 y Julia 0.6, sin seguridad, sin tests, sin visualizacion interactiva. NEVEN lo moderniza para versiones actuales, agrega 10 innovaciones (sandbox, WebView2, Pluto, Quarto, testing, etc.) y lo lleva de calidad 4.3 a 9.6. La contribucion es la transformacion de un prototipo en un sistema de calidad profesional.

### "¿Por que no Python si la tesis habla de sistema multilenguaje?"

Python fue integrado como tercer lenguaje en abril 2026 (ControlPython.exe con CPython 3.13 embebido). Fue congelado temporalmente el 18 de abril debido a 4 bugs de estabilidad (startup retry, SEH stack guard, single-block sending, health check). Estos 4 bugs fueron resueltos exitosamente en mayo 2026 via el spec `python-reactivation`, y Python esta activo con `NEVEN_ENABLE_PYTHON=ON` en CMakeLists.txt. El sistema soporta los tres lenguajes: R + Julia + Python.

### "¿Como validan que los resultados estadisticos son correctos?"

Las funciones R4XCL fueron validadas contra el texto de Wooldridge (2016) — un estandar en econometria. Los resultados de regresion lineal, ACP, panel data, etc. coinciden con los del libro. Esto esta documentado en los archivos de ejemplo en `Ejemplos/R/`.

### "¿El sandbox es realmente seguro?"

Es pattern-based con 5 mecanismos anti-bypass y 154 tests de cobertura. Complementado por InputSanitizer (allowlist validation para CreateProcess), MessageValidator (validacion de frames Protobuf), SafePipeHandle (RAII con atomic ops) y MSVC hardening flags. Bloquea los vectores de ataque mas comunes (shell, archivos, red, codigo nativo, bypass). No es un sandbox de OS (AppContainer). Para un entorno academico/corporativo tipico es suficiente. Para entornos hostiles, se recomienda complementar con sandboxing a nivel de sistema operativo. Esto esta documentado como limitacion y trabajo futuro.

### "¿Que pasa si R o Julia crashean?"

Nada. Corren en procesos separados. El XLL detecta el crash via `GetExitCodeProcess`, marca el servicio como `Unavailable`, y muestra un mensaje descriptivo al usuario. Excel sigue funcionando. Hay reconexion automatica con maximo 2 reintentos.

### "¿Los tests son suficientes?"

357 tests cubren sandbox (154), InputSanitizer (21), IPC/Protobuf (6), pipe lifecycle (8), config/security/discovery (16), type conversions/RAII/callbacks (34), basic functions/COM (35), E2E (8), property-based con rapidcheck (24), build verification (4), repo hygiene (14), R library (1), env lookup (4), y mas. Todos corren sin Excel, R ni Julia gracias a MockExcelBridge. La limitacion es que no hay tests de integracion end-to-end con Excel real — eso requiere un entorno de CI con Office instalado.

### "¿Cual es el impacto practico?"

Un profesor de econometria puede usar `=R.MR_Lineal(Y, X, 1)` en Excel sin saber R. Un estudiante puede explorar datos con `=NEVEN.v(R.Dashboard(datos, 1))` y obtener un dashboard interactivo con Plotly, D3 y rpivotTable. Un investigador puede generar un reporte Quarto reproducible con `=NEVEN.q("reporte.qmd")`. Todo sin salir de Excel.

### "¿La integracion AI no es solo un wrapper de una API?"

La implementacion resuelve problemas reales de ingenieria: resolucion IPv6/IPv4, rate limiting thread-safe, templates editables, soporte para modelos locales (Ollama, LM Studio). No es un simple wrapper — es una integracion robusta que maneja errores de red, timeouts, y permite al usuario elegir entre proveedores cloud (OpenAI) y locales (Ollama, LM Studio) sin cambiar codigo. Los prompts son archivos `.txt` editables que el usuario puede personalizar sin programacion.

---

## 9. Documentacion de Referencia

| Documento | Contenido | Relevancia para defensa |
|:---|:---|:---|
| `ESTADO_DE_LAS_COSAS.md` | Historia completa, problemas resueltos, hitos | Demuestra el proceso de ingenieria |
| `ESTADO_DEL_ARTE.md` | Catalogo de funciones, comparacion con alternativas | Contexto academico |
| `EVALUACION_OBJETIVA.md` | Auditoria de calidad: de 4.3 a 9.6 | Evidencia de mejora continua |
| `arquitectura.md` | Arquitectura 4 capas, flujos, decisiones | Referencia tecnica |
| `MANUAL_MANTENIMIENTO.md` | Build, deploy, troubleshoot | Reproducibilidad |
| `DEPENDENCIAS_INSTALACION.md` | Todas las dependencias | Reproducibilidad |
| `TROUBLESHOOTING.md` | Solucion de problemas | Operatividad |
| `contexto v1.md` | Contexto consolidado del proyecto entero | Vision general |
| `docs/LATEX/RJ2XCL_Paper.tex` | Paper academico en LaTeX | Documento formal de la tesis |

---

## 10. Hoja de Ruta Completada

| Fase | Estado | Descripcion |
|:---|:---|:---|
| Seguridad y testing | ✅ | Sandbox 5 mecanismos, InputSanitizer, MessageValidator, SafePipeHandle, SHA-256, 357 tests |
| Julia funcional | ✅ | 70 procedimientos, sysimage, aliases |
| Python reactivado | ✅ | ControlPython reactivado tras resolver 4 bugs de estabilidad (retry startup, SEH guard, single-block sending, health check) |
| WebView2 y Pluto.jl | ✅ | Visor embebido, notebooks reactivos |
| Quarto | ✅ | Reportes reproducibles |
| Ribbon COM | ✅ | Pestana nativa con 13 botones |
| CI/CD | ✅ | GitHub Actions |
| Callback thread | ✅ | COM bidireccional estable |
| Documentacion | ✅ | 15+ documentos, Docusaurus, Doxygen |
| Reorganizacion | ✅ | Core/, libreria/, Ejemplos/, Build/ |
| Instalador MSI | ✅ | PowerShell script + .exe (Install-NEVEN.exe, 78 KB). Detecta R/Julia/Python, registra XLL y Ribbon COM, instala paquetes R, crea shortcut |
| AI Integration | ✅ | Interpretacion de resultados via OpenAI/Ollama/LM Studio. Funciones P.ai_call/P.ai_setup/P.ai_list_prompts operativas |
| Consola REPL WebView2 | ✅ | `=NEVEN.Console()` — REPL interactivo R/Julia en WebView2 (REPLManager + REPLBridge). Dark theme, tabs con indicador de conexión, historial 500 comandos, multi-línea (Shift+Enter). Console/Electron eliminado del repositorio. Cero dependencias externas |
| Diagnostic Stream (R/Julia) | ⏳ Pendiente | Requiere enfoque alternativo: `PushWrite` en ControlR es asíncrono y no se flushea durante `R_WriteConsoleEx`. Solución propuesta: capturar output en el XLL post-`Call()` via campo protobuf (mismo patrón que Python) |
| Startup Optimization (investigación) | ✅ Revertido | Spec implementada pero causó conflictos con Ribbon COM y limitaciones de `xlfRegister` (solo funciona durante `xlAutoOpen`). Arquitectura revertida al flujo secuencial probado. Infraestructura `InitOrchestrator` permanece para uso futuro |
| SetPointers Race Condition Fix | ✅ | `SetPointers()` ahora omite `SetApplicationPointer()` para servicios no conectados, previniendo hangs cuando el Ribbon COM llama antes de que todos los motores conecten |
| Viewer Snap Layout | ✅ | `=NEVEN.v()` ajusta Excel a la mitad izquierda y el visor a la mitad derecha automáticamente. `SetWindowPos()` + `SPI_GETWORKAREA` |
| `=NEVEN.status()` | ✅ | Función diagnóstica: muestra estado de conexión, salud, prefijo y conteo de funciones de todos los motores |
| Zombie Process Killer | Completado | `Init()` mata ControlR/Julia huérfanos con `taskkill /F /IM` via `CreateProcess(CREATE_NO_WINDOW)`. Previene conflictos de Named Pipes |
| Extraer_outputs (TipoOutput universal) | ✅ | `Extraer_outputs(modelo)` en startup.r — extrae TODOS los outputs de cualquier modelo R como data.frame [Modelo, Seccion, Parametro, Metrica, Valor]. Integrado en 11 funciones R4XCL como TipoOutput más alto |
| Viewer Professional (parcial) | ⏳ En progreso | Botón guardar (💾) inyectado, detección de tipo (PDF/TXT/DOCX), hash de contenido para evitar recargas. Auto-refresh revertido (deadlock STA) |
| Diccionario de Funciones | ✅ | 95 funciones documentadas con ejemplos ejecutables. Accesible desde Ribbon ("Diccionario") y documentación embebida (capítulo 11). Incluye R (~32 funciones), Julia (~52 procedimientos), Python (4 funciones AI) y Sistema (13 funciones) |
| Documentación usuario (Docusaurus) | ✅ | 12 capítulos con tabla de contenidos, accesible desde el Ribbon. Incluye instalación, arquitectura, funciones por lenguaje, ejemplos y diccionario completo |
| Estudio de usuarios | ⏳ Pendiente | Recomendado para la defensa |
| Benchmarks | ⏳ Pendiente | Datos cuantitativos de rendimiento |

---

*Documento interno de orientacion — no para presentar al comite.*
*NEVEN v2.0 — Universidad de Costa Rica*
*Ultima actualizacion: 9 de mayo de 2026*
