# Auditoría de Documentación — NEVEN

**Fecha:** 2026-05-30  
**Auditor:** Kiro (Asistente IA)  
**Alcance:** docs/, headers públicos (.h), librería R/Julia, build scripts  
**Severidades:** Media | Baja

---

## Resumen Ejecutivo

| Métrica | Valor |
|:---|:---|
| Módulos con documentación (README) | 4/7 (Core, ControlR, ControlJulia, Ribbon) |
| Funciones XLL documentadas | ~95/95 (Diccionario completo) |
| Headers con Doxygen adecuado | ~80% |
| Documentos Docusaurus | 12 capítulos completos |
| Hallazgos negativos | 11 |
| Hallazgos positivos | 8 |

---

## Hallazgos Negativos

### [DOC-BAJA-001] Módulos sin README dedicado: Common, ControlPython, Console

- **Archivo(s):** `Common/`, `ControlPython/`, `Console/`
- **Severidad:** Baja
- **Descripción:** Los módulos Core, ControlR, ControlJulia y Ribbon tienen README.md con descripción de arquitectura, responsabilidades y dependencias. Sin embargo, Common (82 archivos), ControlPython y Console carecen de README.
- **Evidencia:**
  - `Common/` contiene 42 headers y 38 .cc sin README.md
  - `ControlPython/` solo tiene CMakeLists.txt y un header, sin README.md
  - `Console/` (aplicación Electron) no tiene README.md
- **Recomendación:** Crear README.md para cada módulo con: propósito, archivos clave, dependencias y notas de uso. Para ControlPython indicar su estado deprecado.

---

### [DOC-BAJA-002] Funciones XLL exportadas sin documentación Doxygen individual

- **Archivo(s):** `Core/include/basic_functions.h`
- **Severidad:** Baja
- **Descripción:** Las ~35 funciones exportadas con `extern "C" __declspec(dllexport)` en basic_functions.h carecen de comentarios Doxygen individuales. Solo tienen el comentario genérico `/** exported function */` o ninguno.
- **Evidencia:**
  ```cpp
  /** exported function */
  extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_SetPointers(...);
  extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Console();  // sin doc
  extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_View(LPXLOPER12 content_or_path);  // sin doc
  ```
- **Recomendación:** Agregar `@brief`, `@param` y `@return` a cada función exportada. La información ya existe en `funcTemplates[]` (descripción y parámetros) pero no está en formato Doxygen.

---

### [DOC-BAJA-003] Headers legacy sin Doxygen en funciones públicas

- **Archivo(s):** `Common/debug_functions.h`, `Common/module_functions.h`, `Common/message_utilities.h`
- **Severidad:** Baja
- **Descripción:** Algunos headers del módulo Common usan comentarios simples (`/** ... */` de una línea) en lugar de Doxygen completo con `@brief`, `@param`, `@return`.
- **Evidencia:**
  ```cpp
  // module_functions.h
  /** reads resource in this dll */
  std::string ReadResource(LPTSTR resource_id);
  
  // message_utilities.h  
  /** unframe and return message */
  bool Unframe(google::protobuf::Message &message, const char *data, uint32_t len);
  ```
  Contraste con headers modernos (ConfigService.h, LogService.h) que usan `@brief`, `@param`, `@return` completos.
- **Recomendación:** Migrar gradualmente los comentarios legacy al formato Doxygen estándar del proyecto. Priorizar headers de la API pública (Pipe, MessageUtilities, ModuleFunctions).

---

### [DOC-MEDIA-004] Discrepancia entre build.ps1 y documentación de despliegue

- **Archivo(s):** `build.ps1`, `docs/Mantenimiento/TROUBLESHOOTING.md` §10, `docs/Docusaurus/09-mantenimiento.md` §9.1
- **Severidad:** Media
- **Descripción:** Existen discrepancias entre el script de build real y la documentación de despliegue:
  1. `build.ps1` genera `RJ2XCL64.xll` en el paquete (línea del Package), pero TROUBLESHOOTING.md §10 copia `NEVEN64.xll`
  2. La documentación de Docusaurus §9.1 indica copiar desde `Build\Core\Release\NEVEN64.dll` renombrándolo a `.xll`, mientras build.ps1 busca `RJ2XCL64.xll` en `Dist/`
  3. TROUBLESHOOTING.md §10 no menciona ControlPython.exe, pero Docusaurus §9.1 sí lo incluye
- **Evidencia:**
  ```powershell
  # build.ps1 (Package section):
  $xllPath = Join-Path $distDir "RJ2XCL64.xll"
  
  # TROUBLESHOOTING.md §10:
  Copy-Item "Build\Dist\NEVEN64.xll" "C:\NEVEN\NEVEN64.xll" -Force
  
  # Docusaurus 09-mantenimiento.md:
  Copy-Item "Build\Core\Release\NEVEN64.dll" "C:\NEVEN\NEVEN64.xll" -Force
  ```
- **Recomendación:** Unificar la documentación de despliegue con el nombre real del artefacto generado por CMake/build.ps1. Verificar cuál es el nombre correcto post-rename y actualizar todos los documentos.

---

### [DOC-MEDIA-005] Inconsistencia terminológica: RJ2XCL vs NEVEN en documentación

- **Archivo(s):** Múltiples archivos en `docs/`
- **Severidad:** Media
- **Descripción:** A pesar del rename del proyecto a NEVEN, persisten ~50+ referencias a "RJ2XCL" en la documentación activa. Esto genera confusión sobre qué nombre es el correcto.
- **Evidencia:**
  - `docs/sops/architecture-overview.md`: diagrama muestra "RJ2XCL_Engine"
  - `docs/sops/error-handling.md`: usa `RJ2XCL_LOG_WARN`, `RJ2XCL_LOG_ERROR`
  - `docs/sops/coding-standards.md`: ejemplo negativo `RJ2XCL_Main.cpp`
  - `docs/Plan_trabajo/`: múltiples referencias a "RJ2XCL"
  - `docs/Latex/RJ2XCL_Paper.tex`: nombre del paper
  - `build.ps1`: header dice "RJ2XCL Build Automation", genera "RJ2XCL64.xll"
  - `Common/module_functions.h`: `DEFAULT_REGISTRY_KEY "Software\\RJ2XCL"`
- **Recomendación:** Distinguir claramente en la documentación:
  - **NEVEN**: nombre del producto visible al usuario
  - **RJ2XCL**: prefijo interno C++ mantenido por compatibilidad ABI
  
  Agregar una nota al inicio de docs/sops/ explicando esta dualidad. Actualizar build.ps1 header y los documentos de plan de trabajo que ya no son activos.

---

### [DOC-BAJA-006] Documentación de funciones R en código fuente sin formato estándar

- **Archivo(s):** `libreria/R/*.R`
- **Severidad:** Baja
- **Descripción:** Los archivos .R de la librería usan comentarios de sección (`#++++`, `#--->>>`) pero no siguen un formato de documentación estándar como roxygen2 (`#' @param`, `#' @return`, `#' @examples`).
- **Evidencia:**
  ```r
  # R4XCL-RG-Lineal.R
  #+++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # MODELO LINEAL
  #+++++++++++++++++++++++++++++++++++++++++++++++++++++++
  MR_Lineal <- function(SetDatosY, SetDatosX, Categorica=0, ...)
  ```
  No hay `#' @description`, `#' @param`, `#' @return`, `#' @examples`.
- **Recomendación:** Agregar documentación roxygen2 a las funciones exportadas. La información ya existe en el Diccionario de Funciones (cap. 11) y podría generarse semi-automáticamente.

---

### [DOC-BAJA-007] Funciones Julia sin docstrings estándar

- **Archivo(s):** `libreria/JULIA/functions.jl`, `libreria/JULIA/J4XCL-*.jl`
- **Severidad:** Baja
- **Descripción:** Las funciones Julia exportadas carecen de docstrings Julia estándar (`\"\"\"...\"\"\"`). Solo tienen comentarios de sección.
- **Evidencia:**
  ```julia
  function JM_Algebra(Matriz, VectorB=nothing, TipoOutput=0)
      # Sin docstring
      TipoOutput = Int(TipoOutput)
      ...
  end
  ```
- **Recomendación:** Agregar docstrings Julia a cada función exportada. Esto además habilitaría que `NEVEN.ListFunctions()` extraiga descripciones automáticamente via `Base.Docs.doc()`.

---

### [DOC-BAJA-008] Fecha de actualización desactualizada en Diccionario de Funciones

- **Archivo(s):** `docs/Docusaurus/11-diccionario-funciones.md`
- **Severidad:** Baja
- **Descripción:** El diccionario indica "Última actualización: 2025-01-15" pero el proyecto ha tenido cambios significativos en 2026 (rename, nuevas funciones, Julia on-demand).
- **Evidencia:** Header del documento: `**Última actualización:** 2025-01-15`
- **Recomendación:** Actualizar la fecha y verificar que las 95 funciones documentadas corresponden al estado actual del código.

---

### [DOC-BAJA-009] Documentación Doxygen generada (docs/api/html/) sin verificación de actualidad

- **Archivo(s):** `docs/api/html/`
- **Severidad:** Baja
- **Descripción:** Existe un directorio `docs/api/html/` que sugiere generación Doxygen previa, pero no hay un `Doxyfile` visible en el repositorio ni instrucciones para regenerar la documentación API.
- **Evidencia:** Directorio `docs/api/html/` existe pero no se encontró `Doxyfile` en la raíz del proyecto.
- **Recomendación:** Agregar un `Doxyfile` al repositorio y documentar el comando de regeneración en `docs/Docusaurus/09-mantenimiento.md`. Considerar integrar la generación en el CI.

---

### [DOC-MEDIA-010] Requerimiento v2 con estado "Pendiente de asignación" sin resolución

- **Archivo(s):** `docs/Requerimientos/Requerimiento_estadistica_excel_v2.md`
- **Severidad:** Media
- **Descripción:** El documento de requerimientos v2 (rediseño con Pluto.jl como orquestador) tiene estado "Pendiente de asignación" y describe una arquitectura diferente a la implementada actualmente (Named Pipes directos). No está claro si fue descartado o está pendiente.
- **Evidencia:** 
  ```
  **Estado:** Pendiente de asignación
  **Versión:** 4.0 (rediseño completo)
  ```
  El documento propone "Pluto como único punto de entrada" y "R como librería via RCall.jl", lo cual contradice la arquitectura actual de procesos separados.
- **Recomendación:** Marcar explícitamente como "Descartado" o "Futuro" con una nota explicando que la arquitectura actual (Named Pipes + procesos hijo) es la implementación vigente. Esto evita confusión para nuevos contribuidores.

---

### [DOC-BAJA-011] Marcadores TODO/PENDIENTE en documentación

- **Archivo(s):** `docs/Requerimientos/Requerimiento_estadistica_excel_v2.md`
- **Severidad:** Baja
- **Descripción:** Se encontraron secciones con contenido pendiente o incompleto en la documentación de requerimientos.
- **Evidencia:** El documento v2 tiene 7 entregables listados al final sin estado de completitud, y múltiples tablas duplicadas (filas repetidas).
- **Recomendación:** Revisar y limpiar el documento, eliminando duplicados y marcando claramente el estado de cada entregable.

---

## Hallazgos Positivos

### [DOC-POS-001] Documentación Docusaurus completa y bien estructurada

- **Archivo(s):** `docs/Docusaurus/` (12 capítulos)
- **Descripción:** La documentación principal del proyecto está organizada en 12 capítulos Docusaurus con estructura consistente, sidebar navigation, y cobertura completa: introducción, instalación, arquitectura, funciones Julia, funciones R, Pluto/Quarto, WebView2/Ribbon, seguridad/testing, mantenimiento, ejemplos, y diccionario de funciones.
- **Fortaleza:** Cada capítulo sigue un formato uniforme con frontmatter, tabla de contenidos implícita, y progresión lógica.

---

### [DOC-POS-002] Diccionario de Funciones exhaustivo con 95 funciones documentadas

- **Archivo(s):** `docs/Docusaurus/11-diccionario-funciones.md`
- **Descripción:** Documento de ~2000 líneas que cataloga las 95 funciones del sistema con: nombre Excel, descripción, tabla de parámetros (tipo, default, descripción), tabla de TipoOutput, ejemplo de uso, resultado esperado, y paquetes requeridos.
- **Fortaleza:** Nivel de detalle excepcional. Cada función tiene información suficiente para que un usuario la utilice sin ayuda adicional.

---

### [DOC-POS-003] READMEs de módulos con diagramas de arquitectura y tablas de diseño

- **Archivo(s):** `Core/README.md`, `ControlR/README.md`, `ControlJulia/README.md`, `Ribbon/README.md`
- **Descripción:** Los READMEs existentes incluyen diagramas ASCII de arquitectura, tablas de archivos clave, descripción de patrones de diseño (Buffer Design, RControllerState, Pipe Indices), y grafos de dependencias.
- **Fortaleza:** Permiten a un desarrollador nuevo entender rápidamente la responsabilidad y diseño interno de cada módulo.

---

### [DOC-POS-004] Headers modernos con Doxygen completo (ConfigService, LanguageManager, LogService)

- **Archivo(s):** `Common/ConfigService.h`, `Core/include/LanguageManager.h`, `Common/LogService.h`
- **Descripción:** Los headers de servicios principales tienen documentación Doxygen ejemplar con `@brief`, `@param`, `@return`, `@note`, y descripciones de comportamiento (defaults, clamping, fallbacks).
- **Fortaleza:** ConfigService.h documenta ~25 métodos con valores por defecto, rangos válidos y comportamiento de fallback. LanguageManager.h documenta el patrón de diseño y las 3 fases de inicialización.

---

### [DOC-POS-005] Guía de Troubleshooting práctica y actualizada

- **Archivo(s):** `docs/Mantenimiento/TROUBLESHOOTING.md`
- **Descripción:** 16 problemas documentados con formato consistente: Síntoma → Causa → Solución (con comandos PowerShell copiables). Incluye sección "NUEVOS (Mayo 2026)" con problemas recientes.
- **Fortaleza:** Orientada a la acción, con comandos exactos que el usuario puede ejecutar. Cubre desde problemas de instalación hasta edge cases como el KB5087051 de Windows Update.

---

### [DOC-POS-006] SOPs de desarrollo bien definidos

- **Archivo(s):** `docs/sops/` (5 documentos)
- **Descripción:** Procedimientos operativos estándar para: arquitectura, coding standards, desarrollo, manejo de errores, y testing. Proporcionan guías claras para contribuidores.
- **Fortaleza:** El SOP de error-handling define el patrón `Result<T,E>` con reglas claras. El testing-guide explica cómo correr tests sin Excel/R/Julia.

---

### [DOC-POS-007] Documentación de funciones Julia con notación matemática LaTeX

- **Archivo(s):** `docs/Docusaurus/04-funciones-julia.md`
- **Descripción:** La documentación de funciones Julia incluye notación matemática LaTeX para fórmulas, matrices y distribuciones, haciendo la documentación apropiada para un contexto académico.
- **Fortaleza:** Combina la referencia técnica (firma, parámetros) con la fundamentación matemática, ideal para una tesis de maestría.

---

### [DOC-POS-008] Múltiples niveles de documentación para diferentes audiencias

- **Archivo(s):** `docs/` (estructura completa)
- **Descripción:** La documentación está organizada para diferentes audiencias:
  - **Usuario final:** Docusaurus caps 1-6, 10-11 (funciones, ejemplos)
  - **Desarrollador:** SOPs, READMEs de módulo, coding standards
  - **Mantenedor:** Troubleshooting, mantenimiento, build procedures
  - **Académico:** Paper LaTeX, evaluaciones, contexto, requerimientos
- **Fortaleza:** Separación clara de concerns documentales. Un usuario no necesita leer sobre arquitectura interna, y un desarrollador tiene sus guías separadas.

---

## Resumen de Severidades

| Severidad | Cantidad | IDs |
|:---|:---:|:---|
| Media | 3 | DOC-MEDIA-004, DOC-MEDIA-005, DOC-MEDIA-010 |
| Baja | 8 | DOC-BAJA-001 a 003, DOC-BAJA-006 a 009, DOC-BAJA-011 |
| **Total** | **11** | |

## Conclusión

La documentación del proyecto NEVEN es **notablemente completa** para un proyecto de tesis. Los 12 capítulos Docusaurus, el diccionario de 95 funciones, y los SOPs de desarrollo representan un esfuerzo significativo y bien organizado. Los hallazgos negativos son principalmente de severidad Baja y se concentran en:

1. **Consistencia terminológica** (RJ2XCL vs NEVEN) — consecuencia natural del rename reciente
2. **Cobertura de módulos secundarios** (Common, ControlPython, Console sin README)
3. **Formato de documentación en código fuente** (R sin roxygen2, Julia sin docstrings)

Las discrepancias de severidad Media (build paths, terminología, requerimiento obsoleto) merecen atención prioritaria para evitar confusión en mantenimiento futuro.
