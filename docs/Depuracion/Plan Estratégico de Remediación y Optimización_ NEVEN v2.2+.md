# Plan Estratégico de Remediación y Optimización: NEVEN v2.2+

> **Última actualización:** 2026-08-07
> **Estado general:** En progreso — v2.3.2 estable en producción
> **Versiones activas:** R 4.6.1 · Julia 1.12.6 · Python 3.13.5

Este documento constituye la directriz técnica de cumplimiento obligatorio para la estabilización y blindaje de NEVEN. El objetivo central es la transición de un prototipo avanzado hacia un sistema de grado de producción, eliminando vulnerabilidades de diseño y saneando el núcleo mediante la remoción exhaustiva de deuda técnica identificada en las auditorías de mayo de 2026.

---

## 1. Fortalecimiento de la Seguridad Crítica (Aislamiento de Nivel OS)

**Estado: ⏳ Pendiente (prioridad diferida)**

La arquitectura actual depende de **SandboxVerifier**, el cual opera mediante filtrado de patrones de texto. Si bien cuenta con una cobertura de 154 tests, el análisis de riesgo admite una limitación estructural: la validación basada en patrones es susceptible de bypass ante atacantes motivados que empleen técnicas de ofuscación complejas. Se propone la transición hacia AppContainer (Win32) para aislamiento a nivel de Kernel.

| Característica | Situación Actual | Mejora Propuesta |
|:---|:---|:---|
| Mecanismo primario | Análisis de strings en SandboxVerifier | Restricción de privilegios via AppContainer (Win32) |
| Punto de control | Espacio de usuario (User-space) | Nivel de Kernel/Sistema Operativo |
| Riesgo identificado | Bypass mediante ofuscación (Doc 2.2) | Denegación por política de hardware/red |
| Mantenimiento | Actualización reactiva de blocklists | Definición estática de capabilities de proceso |

**Decisión:** Diferido hasta completar v2.4 Dynamic Loading. La superficie de ataque actual es aceptable para el contexto académico de la tesis.

---

## 2. Depuración Arquitectónica y Saneamiento de Deuda Técnica

### 2.1 Eliminación de Componentes Obsoletos

| Ítem | Componente | Estado |
|:---|:---|:---:|
| CM-MED-001/002/003 | RuntimeLoader.cc, AutoLoader.cc, GCMonitor.cc | ✅ Eliminados (sesión ago-2026) |
| CM-BAJ-004 | SandboxVerifier: EvaluateScript, AddTrustedSignature | ✅ Limpiado |
| CM-BAJ-011/012 | R_Environment.cpp, Julia_Environment.cpp | ✅ Movidos a legacy/ |

### 2.2 Consistencia en Exportaciones XLL

| Ítem | Fix | Estado |
|:---|:---|:---:|
| CM-MED-013 | Incluir RJ_Q en rj2xcl.def | ✅ Aplicado |
| — | Agregar RJ_JuliaSysimageCmd a rj2xcl.def | ✅ Aplicado (ago-2026) |

---

## 3. Estabilidad de Motores y Resolución Funcional

### 3.1 Correcciones aplicadas en esta etapa

| Fix | Descripción | Commit | Estado |
|:---|:---|:---|:---:|
| R_ReadConsole crash | `GetOption1` en ReadConsole callback causaba crash c0000005 en R.dll 0x11b111. Removido `is_continuation = false`. | `7179d4f` | ✅ |
| Sysimage Julia versión | `jl_init_with_image` crashea con sysimage de versión distinta. Ahora verifica `neven_julia.version` antes de cargar. | `d0a80ad` | ✅ |
| UTF-8 BOM en .r | `WriteAllText(Encoding.UTF8)` agrega BOM → R no parsea → crash RLoop. Regla: usar `UTF8NoBOM`. | `073241f` | ✅ |
| startup.jl bloqueaba Core | `export_data` (80+ líneas) en startup principal bloqueaba el Core durante el envío. Movido a archivo separado. | `073241f` | ✅ |

### 3.2 Compatibilidad de versiones verificada (2026-08-07)

| Motor | Versión | Actualización | Resultado |
|:---|:---|:---|:---:|
| R | 4.6.1 | winget upgrade | ✅ Funciona sin recompilar ControlR |
| Julia | 1.12.6 | juliaup update | ✅ Init estándar auto (sin sysimage) |
| Python | 3.13.5 | winget upgrade | ✅ Sin cambios requeridos |

**Nota importante:** R 4.6.1 funciona con ControlR.exe compilado para R 4.4.1. Windows resuelve `R.dll` dinámicamente por PATH — confirma que v2.4 dynamic loading probablemente ya funciona con el fix de R_ReadConsole.

### 3.3 Pendientes de esta sección

| Ítem | Descripción | Prioridad |
|:---|:---|:---:|
| Bug EDO Julia 1.12 | TipoOutput 2-4 de J.EDO tienen bug de scope | Media |
| Viewer Professional | Estabilizar botón guardado + hash de contenido | Baja |
| CrashHandler | Integrar telemetría local estable | Media |

---

## 4. Nuevas funcionalidades implementadas (NEVEN v2.3.x)

Trabajo realizado en agosto de 2026 que no estaba en el plan original:

### NEVEN Studio — Bloques completados

| Bloque | Descripción | Commit | Estado |
|:---|:---|:---|:---:|
| B1 — Tests Studio | Suite de tests wrappers .Studio(): 110 pass, 0 fail, 21 skip. 33 funciones cubiertas. | `4ed4e53` | ✅ |
| B2 — Data Lab Julia | Soporte `language:"julia"` en DataLab. Funciones `J_AD_Descriptiva` y `J_RG_Lineal` en Julia puro. | `e93932d` | ✅ |
| B3 — Tab IA | Endpoint `/api/ai/chat` + tab "IA" con chat LLM, contexto dataset DuckDB, prompts guía. | `246100e` | ✅ |
| B4 — PLUTO.READ | `NEVEN.export_data()` en Julia + `NEVEN.pluto_read()` en R para pipeline Julia→Excel. | `3ce88a7` | ✅ |

### Mejoras de infraestructura

| Mejora | Descripción | Estado |
|:---|:---|:---:|
| Botón Ribbon "Sysimage" | Compila `neven_julia.dll` desde el Ribbon sin abrir terminal | ✅ v2.3.2 |
| Verificación versión sysimage | ControlJulia no carga sysimage incompatible → degradación graceful | ✅ v2.3.1 |
| build_controlr.ps1 | Script de build incremental para ControlR sin cmake directo | ✅ |

---

## 5. Hoja de ruta: v2.4 Dynamic Engine Loading

### Estado actual

| Task | Descripción | Estado |
|:---|:---|:---:|
| TASK-R-01..05 | REngineLoader, shims, compat, CMake sin R64.lib | ✅ En stash |
| TASK-R-06 | Test R 4.4.1 paridad funcional | ⚠️ Bloqueado por crash (resuelto en v2.3?) |
| TASK-R-07 | Test R 4.6.1 sin recompilar | ⏳ R 4.6.1 ya funciona con v2.3 — a confirmar con dynamic loading |
| TASK-J-01..07 | Julia Engine Loader | ⏳ |
| TASK-INT-01..04 | Integración y release | ⏳ |

### Próximos pasos para v2.4

1. `git stash pop` — recuperar trabajo de dynamic loading
2. Compilar con `.\build_controlr.ps1 -CleanFirst`
3. Probar — el fix de `R_ReadConsole` probablemente resuelve el crash `0x11b111`
4. Si pasa → TASK-R-06 completada → continuar con TASK-J

**Bloqueante original resuelto:** El crash `c0000005 R.dll 0x11b111` era `GetOption1(install("continue"))` en `R_ReadConsole`. Ya removido en v2.3.1 (`7179d4f`). El dynamic loading debería funcionar ahora.

---

## 6. Validación Externa y Viabilidad del Proyecto

| Ítem | Estado |
|:---|:---:|
| Benchmark Named Pipes+Protobuf vs VBA vs xlwings | ⏳ Pendiente |
| Estudio de Usabilidad UCR | ⏳ Pendiente |
| Comparativa vs PyXLL y RExcel | ⏳ Pendiente |
| Documentar limitación Windows-only | ⏳ Pendiente |

---

## 7. Lista Maestra de Tareas — Estado Actualizado

| Prioridad | Tarea | Estado |
|:---|:---|:---:|
| 🔴 Crítica | Implementar aislamiento OS-Level (AppContainer) | ⏳ Diferido |
| 🔴 Crítica | Fix crash R.dll 0x11b111 en R_ReadConsole | ✅ `7179d4f` |
| 🟠 Alta | Remover RuntimeLoader → AutoLoader → GCMonitor | ✅ Agosto 2026 |
| 🟠 Alta | Sincronizar rj2xcl.def con RJ_Q | ✅ |
| 🟠 Alta | Tests Studio wrappers (Tarea 15) | ✅ 110 pass |
| 🟠 Alta | Data Lab Julia | ✅ Bloque 2 |
| 🟠 Alta | Tab IA NEVEN Studio | ✅ Bloque 3 |
| 🟠 Alta | PLUTO.READ pipeline | ✅ Bloque 4 |
| 🟠 Alta | Sysimage Julia versión-safe | ✅ `d0a80ad` |
| 🟠 Alta | Botón Ribbon "Sysimage Julia" | ✅ `b4f0b53` |
| 🟡 Media | v2.4 Dynamic Loading ControlR | ⏳ Próxima etapa |
| 🟡 Media | Corregir bug EDO Julia 1.12 TipoOutput 2-4 | ⏳ |
| 🟡 Media | Integración estable CrashHandler | ⏳ |
| 🟡 Media | Probar Studio en vivo (todos los bloques) | ⏳ Próxima sesión |
| 🟢 Baja | Sanear SandboxVerifier métodos huérfanos | ✅ |
| 🟢 Baja | Remover R_Environment.cpp / Julia_Environment.cpp | ✅ |
| 🟢 Baja | Finalizar Viewer Professional (hash + guardado) | ⏳ |
| 🟢 Baja | Benchmark rendimiento vs VBA/xlwings | ⏳ |
| 🟢 Baja | Documentar limitación Windows-only | ⏳ |
| 🟢 Baja | Estudio usabilidad UCR | ⏳ |

---

*Actualizado: 2026-08-07 — NEVEN v2.3.2 en producción · R 4.6.1 · Julia 1.12.6 · Python 3.13.5*
