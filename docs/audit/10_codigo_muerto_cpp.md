# Auditoría de Código Muerto C++ — NEVEN

**Fecha:** 2025-01-XX  
**Módulos auditados:** Core/, Common/, ControlR/, ControlJulia/, ControlPython/  
**Metodología:** Análisis estático de definiciones vs. invocaciones, revisión de CMakeLists.txt, inspección de directivas de preprocesador y tabla de exportaciones.

---

## Resumen Ejecutivo

| Categoría | Hallazgos | Severidad |
|-----------|-----------|-----------|
| 7.1 Funciones no invocadas | 5 | Baja-Media |
| 7.2 Bloques comentados | 3 | Baja |
| 7.3 Directivas preprocesador | 2 | Baja |
| 7.4 Archivos no referenciados | 2 | Baja |
| 7.5 Exportaciones XLL no registradas | 1 | Media |
| 7.6 Variables miembro sin lectura | 1 | Baja |
| 7.7 Código residual Python | 3 | Baja |
| **Total** | **17** | |

---

## 7.1 Funciones C++ No Invocadas

### [CM-MED-001] GCMonitor — Clase completa sin invocaciones externas
- **Archivo(s):** Common/GCMonitor.cc:17-45
- **Severidad:** Media
- **Descripción:** La clase `GCMonitor` (métodos `GetInstance()`, `RegisterEngine()`, `NotifyExcelCOMRelease()`, `ForceGlobalSweep()`) está compilada en Common.lib pero ningún otro módulo la invoca. Ni Core ni los procesos hijos llaman a `GCMonitor::GetInstance()`.
- **Evidencia:** Búsqueda de `GCMonitor|NotifyExcelCOMRelease|ForceGlobalSweep` en `Core/**/*.cc` y `Common/**/*.cc` (excluyendo GCMonitor.cc) no produce resultados. La clase depende de `IScriptEngine*` que solo existe en el patrón legacy (RuntimeLoader).
- **Recomendación:** Eliminar `GCMonitor.cc` de `Common/CMakeLists.txt` y del repositorio. Si se necesita GC coordinado en el futuro, reimplementar con la arquitectura actual de procesos hijos.

### [CM-MED-002] RuntimeLoader — Clase completa sin invocaciones desde Core
- **Archivo(s):** Common/RuntimeLoader.cc:20-51
- **Severidad:** Media
- **Descripción:** `RuntimeLoader::GetInstance()` y `RuntimeLoader::GetEngine()` solo son invocados desde `AutoLoader.cc`, que a su vez tampoco es invocado desde Core. Toda la cadena RuntimeLoader→AutoLoader→R_Environment/Julia_Environment es código muerto funcional.
- **Evidencia:** Búsqueda de `AutoLoader` en `Core/**/*.cc` no produce resultados. `RuntimeLoader` solo aparece en `AutoLoader.cc` y en su propia implementación. El patrón actual usa `LanguageManager` + procesos hijos (ControlR.exe, ControlJulia.exe) en lugar de embedding directo.
- **Recomendación:** Eliminar `RuntimeLoader.cc` y `AutoLoader.cc` de `Common/CMakeLists.txt`. Estos archivos pertenecen a una arquitectura anterior (embedding directo de R/Julia en el proceso XLL).

### [CM-MED-003] AutoLoader — Clase completa sin invocaciones desde Core
- **Archivo(s):** Common/AutoLoader.cc:23-87
- **Severidad:** Media
- **Descripción:** `AutoLoader::GetInstance()`, `SetUserScriptDirectory()`, `LoadAllUserScripts()`, `SourcingRFiles()`, `SourcingJuliaFiles()` nunca son invocados desde el módulo Core. Solo `RuntimeLoader.cc` los llama, y RuntimeLoader tampoco es invocado.
- **Evidencia:** Búsqueda de `AutoLoader` en `Core/**/*.cc` = 0 resultados. La funcionalidad de carga de scripts de usuario fue reemplazada por el sistema de `file_watch_service_` + `MapFunctions()` en `rj2xcl.cc`.
- **Recomendación:** Eliminar junto con RuntimeLoader.cc.

### [CM-BAJ-004] SandboxVerifier::EvaluateScript() y AddTrustedSignature()
- **Archivo(s):** Common/SandboxVerifier.cc:40-50
- **Severidad:** Baja
- **Descripción:** Los métodos `EvaluateScript()` y `AddTrustedSignature()` están definidos pero nunca son invocados. Solo `ValidateCodeForExecution()` (llamado desde `basic_functions.cc`) y `ContainsRestrictedCommands()` (interno) son utilizados.
- **Evidencia:** Búsqueda de `EvaluateScript|AddTrustedSignature` en todos los `.cc/.cpp` solo muestra la definición en `SandboxVerifier.cc`, no invocaciones.
- **Recomendación:** Eliminar ambos métodos y el miembro `m_trusted_signatures`. Si se necesita un sistema de firmas confiables en el futuro, diseñar con la API actual.

### [CM-BAJ-005] RJ2XCL_Engine::RemoveUserButton() — Función con cuerpo vacío
- **Archivo(s):** Core/src/rj2xcl.cc:288-289, Core/include/rj2xcl.h:205
- **Severidad:** Baja
- **Descripción:** `RemoveUserButton()` tiene un cuerpo completamente vacío (`{}`). Está declarada en el header y definida en el .cc pero no realiza ninguna operación. No se encontraron invocaciones externas.
- **Evidencia:** La búsqueda de `RemoveUserButton` solo muestra la definición (rj2xcl.cc) y la declaración (rj2xcl.h). El cuerpo es `{}`.
- **Recomendación:** Implementar la funcionalidad o eliminar la declaración y definición si no se planea usar.

---

## 7.2 Bloques de Código Comentado

### [CM-BAJ-006] Comentario residual "ReadConfigFile removed"
- **Archivo(s):** Core/src/rj2xcl.cc:84
- **Severidad:** Baja
- **Descripción:** Línea `// ReadConfigFile removed, use ConfigService::Instance().ReadJsonFile` es un comentario residual que indica código eliminado previamente. No hay código comentado asociado, pero el comentario en sí es ruido.
- **Evidencia:** Inspección directa del archivo. El comentario no aporta valor documental — la función ya no existe.
- **Recomendación:** Eliminar el comentario. El historial de git preserva la información.

### [CM-BAJ-007] Comentario residual "Redundant UpdateGraphics removed"
- **Archivo(s):** Core/src/rj2xcl.cc:286
- **Severidad:** Baja
- **Descripción:** Línea `// Redundant UpdateGraphics removed, replaced by GraphicsHandler` es un comentario residual sobre código eliminado.
- **Evidencia:** Inspección directa. No hay código comentado, solo el comentario informativo.
- **Recomendación:** Eliminar el comentario. El refactoring ya está completo.

### [CM-BAJ-008] Código condicional INCLUDE_DUMP_JSON comentado por defecto
- **Archivo(s):** Common/message_utilities.h:28, Common/message_utilities.cc:74-90
- **Severidad:** Baja
- **Descripción:** La macro `INCLUDE_DUMP_JSON` está comentada (`// #define INCLUDE_DUMP_JSON`) y el bloque `#ifdef INCLUDE_DUMP_JSON` contiene la función `DumpJSON()` que nunca se compila. Son ~16 líneas de código de depuración que nunca se activan.
- **Evidencia:** La macro no está definida en ningún CMakeLists.txt ni en ningún otro archivo del proyecto. El `#define` está comentado en el header.
- **Recomendación:** Mantener como utilidad de depuración documentada, o mover a un archivo de utilidades de debug separado. Severidad baja porque es un patrón intencional de debug.

---

## 7.3 Directivas de Preprocesador con Código No Compilado

### [CM-BAJ-009] #ifdef INCLUDE_DUMP_JSON — Macro nunca definida
- **Archivo(s):** Common/message_utilities.h:29-32, Common/message_utilities.cc:74-90
- **Severidad:** Baja
- **Descripción:** El bloque `#ifdef INCLUDE_DUMP_JSON` protege la función `DumpJSON()` y su include de `<google/protobuf/util/json_util.h>`. La macro nunca se define en CMakeLists.txt ni en ninguna configuración activa del proyecto.
- **Evidencia:** Búsqueda de `INCLUDE_DUMP_JSON` en `**/*.txt` y `**/*.cmake` = 0 resultados. El `#define` está comentado en el propio header.
- **Recomendación:** Aceptable como utilidad de depuración manual. Documentar en el header que se activa descomentando la línea 28.

### [CM-BAJ-010] #ifdef _DEBUG en dllmain.cpp — Solo activo en configuración Debug
- **Archivo(s):** Core/src/dllmain.cpp:35-37
- **Severidad:** Baja (informativo)
- **Descripción:** El bloque `#ifdef _DEBUG` redirige streams de stdio para la consola de Visual Studio. Solo se compila en configuración Debug, lo cual es el comportamiento esperado.
- **Evidencia:** `_DEBUG` es definido automáticamente por MSVC en configuración Debug. No es código muerto sino código condicional legítimo.
- **Recomendación:** Sin acción requerida. Patrón estándar de depuración MSVC.

---

## 7.4 Archivos C++ No Referenciados por CMakeLists.txt

### [CM-BAJ-011] ControlR/src/R_Environment.cpp — Excluido explícitamente del build
- **Archivo(s):** ControlR/src/R_Environment.cpp
- **Severidad:** Baja
- **Descripción:** El archivo `R_Environment.cpp` existe en el directorio de fuentes de ControlR pero está explícitamente excluido del CMakeLists.txt (el comentario dice "exclude R_Environment.cpp which uses xloper12 from Excel SDK"). El CMakeLists.txt lista archivos individuales en lugar de usar glob, y este archivo no está incluido.
- **Evidencia:** `ControlR/CMakeLists.txt` lista explícitamente: `controlr.cc`, `rinterface_common.cc`, `rinterface_win.cc`, `convert.cc`, `console_graphics_device.cc`, `gdi_graphics_device.cc`, `spreadsheet_graphics_device.cc`. `R_Environment.cpp` no aparece. Pertenece al patrón legacy de embedding directo.
- **Recomendación:** Mover a un directorio `legacy/` o eliminar. El archivo implementa `IScriptEngine` para embedding directo de R, un patrón reemplazado por la arquitectura de procesos hijos.

### [CM-BAJ-012] ControlJulia/src/Julia_Environment.cpp — Excluido explícitamente del build
- **Archivo(s):** ControlJulia/src/Julia_Environment.cpp
- **Severidad:** Baja
- **Descripción:** Mismo caso que R_Environment.cpp. El archivo implementa `IScriptEngine` para Julia pero está excluido del build de ControlJulia.exe.
- **Evidencia:** `ControlJulia/CMakeLists.txt` lista: `control_julia.cc`, `julia_interface.cc`, `JuliaConversion.cpp`. `Julia_Environment.cpp` no aparece.
- **Recomendación:** Mover a `legacy/` o eliminar. Mismo patrón obsoleto de embedding directo.

---

## 7.5 Exportaciones XLL No Registradas en Tabla de Funciones Excel

### [CM-MED-013] RJ_Q — Registrada en funcTemplates pero ausente del .def file
- **Archivo(s):** Core/src/basic_functions.cc:348, Core/src/rj2xcl.def
- **Severidad:** Media
- **Descripción:** La función `RJ_Q` (renderizado de Quarto) está definida con `__declspec(dllexport)` y registrada en `funcTemplates[]` como `NEVEN.q`, pero NO aparece en el archivo `rj2xcl.def`. Con MSVC y la opción `/DEF:`, `__declspec(dllexport)` es aditivo al .def file, por lo que la función SÍ se exporta. Sin embargo, la inconsistencia entre .def y funcTemplates es un riesgo de mantenimiento.
- **Evidencia:** `Select-String -Pattern "^RJ_Q$"` en rj2xcl.def = 0 resultados. La función SÍ aparece en `funcTemplates[]` en basic_functions.h línea ~82 como `{ L"RJ_Q", L"UQ", L"NEVEN.q", ... }`.
- **Recomendación:** Agregar `RJ_Q` al archivo .def para mantener consistencia con las demás exportaciones. Aunque funciona por `__declspec(dllexport)`, la práctica del proyecto es listar todas las exportaciones en el .def.

---

## 7.6 Variables Miembro Asignadas pero Nunca Leídas

### [CM-BAJ-014] SandboxVerifier::m_trusted_signatures — Asignada pero nunca consultada
- **Archivo(s):** Include/SandboxVerifier.h (declaración), Common/SandboxVerifier.cc:41-44
- **Severidad:** Baja
- **Descripción:** El vector `m_trusted_signatures` es modificado por `AddTrustedSignature()` pero nunca es leído por ningún método. `ValidateCodeForExecution()` (el método activo) no consulta esta colección para determinar si un script es confiable.
- **Evidencia:** `AddTrustedSignature()` hace `push_back` al vector, pero ningún otro método accede a `m_trusted_signatures`. La validación actual es puramente basada en patrones de texto.
- **Recomendación:** Eliminar `m_trusted_signatures` junto con `AddTrustedSignature()` y `EvaluateScript()` (ver CM-BAJ-004).

---

## 7.7 Código Residual Python (Deprecado)

### [CM-BAJ-015] ControlPython/ — Módulo completo ON por defecto pero documentado como deprecado
- **Archivo(s):** ControlPython/src/control_python.cc, ControlPython/src/python_interface.cc, ControlPython/CMakeLists.txt
- **Severidad:** Baja
- **Descripción:** El módulo ControlPython está habilitado por defecto (`option(NEVEN_ENABLE_PYTHON ... ON)`) en el CMakeLists.txt raíz, a pesar de que la documentación del proyecto indica que Python "fue integrado pero está deprecado (OFF por defecto) — causaba hangs". Hay una contradicción entre la documentación y la configuración real.
- **Evidencia:** `CMakeLists.txt` línea 67: `option(NEVEN_ENABLE_PYTHON "Build ControlPython.exe (optional, requires Python >= 3.10)" ON)`. La guía del proyecto dice "OFF por defecto". El código en `language_service.cc` tiene workarounds específicos para Python (skip callback pipe, piggybacked diagnostics).
- **Recomendación:** Cambiar el default a `OFF` para alinear con la documentación. Mantener el código para compilación opcional pero documentar claramente su estado experimental.

### [CM-BAJ-016] Código Python-específico en Core/src/language_service.cc
- **Archivo(s):** Core/src/language_service.cc:144-145, 180-183, 667-674
- **Severidad:** Baja
- **Descripción:** El módulo Core contiene lógica condicional específica para Python:
  - Línea 144: `bool skip_callback = (language_descriptor_.name_ == "Python");` — desactiva callback pipe
  - Línea 180: `bool is_python = (language_descriptor_.name_ == "Python");` — envío de código en bloque
  - Línea 669: `if (language_descriptor_.name_ == "Python")` — routing de diagnósticos piggybacked
  
  Este código se ejecuta incluso cuando Python no está conectado, añadiendo complejidad al path crítico de R/Julia.
- **Evidencia:** Inspección directa de `language_service.cc`. Los checks de string comparison se ejecutan en cada llamada.
- **Recomendación:** Si Python se mantiene OFF por defecto, considerar proteger estos bloques con `#ifdef NEVEN_ENABLE_PYTHON` o un flag de compilación para eliminar el overhead en builds de producción.

### [CM-BAJ-017] DiagnosticRouter::RoutePythonDiagnostics() — Solo útil con Python activo
- **Archivo(s):** Common/DiagnosticRouter.cc:71-104, Common/DiagnosticRouter.h:68-70
- **Severidad:** Baja
- **Descripción:** El método `RoutePythonDiagnostics()` es específico para el workaround de Python (diagnósticos piggybacked en la respuesta porque el callback pipe no funciona con Python). Si Python está deshabilitado, este método nunca se invoca.
- **Evidencia:** Solo es llamado desde `language_service.cc:671` dentro del bloque `if (language_descriptor_.name_ == "Python")`. Sin Python conectado, el código es inalcanzable.
- **Recomendación:** Documentar como parte del soporte Python experimental. No eliminar mientras el módulo ControlPython exista.

---

## Hallazgos Positivos

| Aspecto | Observación |
|---------|-------------|
| Arquitectura limpia | La separación Core/Common/ControlR/ControlJulia es clara y bien definida |
| Exportaciones consistentes | 99% de las funciones en funcTemplates tienen su correspondiente entrada en .def |
| Sin `#if 0` en código propio | No se encontraron bloques `#if 0` en los módulos auditados (solo en dependencias externas) |
| Código condicional legítimo | Los `#ifdef _DEBUG` y `#ifdef _WIN64` son patrones estándar y correctos |
| Funciones placeholder documentadas | Los 2048 `RJ_FunctionCall1000-3047` en .def son slots pre-reservados para registro dinámico de funciones R/Julia — patrón intencional del XLL |
| Módulos bien acotados | ControlR y ControlJulia no tienen código muerto significativo — sus archivos .cc están todos referenciados |
| Doxygen bien separado | Los bloques `/** ... */` son documentación Doxygen legítima, no código comentado |

---

## Resumen de Acciones Recomendadas

| Prioridad | Acción | Archivos afectados |
|-----------|--------|-------------------|
| 1 (Media) | Eliminar cadena RuntimeLoader→AutoLoader→GCMonitor | Common/RuntimeLoader.cc, Common/AutoLoader.cc, Common/GCMonitor.cc + CMakeLists.txt |
| 2 (Media) | Agregar `RJ_Q` al archivo .def | Core/src/rj2xcl.def |
| 3 (Baja) | Cambiar `NEVEN_ENABLE_PYTHON` default a OFF | CMakeLists.txt raíz |
| 4 (Baja) | Eliminar métodos muertos de SandboxVerifier | Common/SandboxVerifier.cc |
| 5 (Baja) | Mover R_Environment.cpp y Julia_Environment.cpp a legacy/ | ControlR/src/, ControlJulia/src/ |
| 6 (Baja) | Eliminar comentarios residuales | Core/src/rj2xcl.cc |
| 7 (Baja) | Implementar o eliminar RemoveUserButton() | Core/src/rj2xcl.cc, Core/include/rj2xcl.h |

---

## Notas Metodológicas

- **Exclusiones:** Se excluyeron del análisis los directorios `Build/`, `Include/` (mock headers para tests), y dependencias externas (protobuf, googletest, webview2).
- **Funciones placeholder:** Los ~2048 exports `RJ_FunctionCall1000`–`RJ_FunctionCall3047` son slots pre-reservados para el registro dinámico de funciones de usuario (R/Julia). No son código muerto — son el mecanismo por el cual Excel puede llamar funciones descubiertas en runtime.
- **Entry points excluidos:** `DllMain`, `xlAutoOpen`, `xlAutoFree12`, `xlAutoClose`, `xlAddInManagerInfo12`, y todas las funciones en `funcTemplates[]` fueron excluidas del análisis de "funciones no invocadas" por ser entry points del framework XLL.
- **Limitación:** El análisis es estático. Funciones invocadas dinámicamente (via punteros a función, COM dispatch, o reflection) podrían no detectarse como "usadas".
