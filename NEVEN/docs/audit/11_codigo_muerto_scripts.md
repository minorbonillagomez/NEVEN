# Auditoría de Código Muerto — Scripts (R, Julia, Python)

**Proyecto:** NEVEN  
**Fecha:** 2026-01-XX  
**Alcance:** `libreria/R/`, `libreria/JULIA/`, `startup/`  
**Auditor:** Kiro (automatizado)

---

## Resumen Ejecutivo

Se identificaron **14 hallazgos** de código muerto o residual en los scripts R, Julia y Python del proyecto NEVEN. La mayoría son de severidad baja y corresponden a funciones no invocadas, código comentado extenso, duplicación de funcionalidad entre archivos, y la integración Python deprecada que permanece en el repositorio.

## Tabla Resumen

| ID | Severidad | Archivo(s) | Descripción |
|----|-----------|------------|-------------|
| CM-BAJ-001 | Baja | libreria/R/R4XCL-0-Interno-1.R | `R4XCL_INT_CREAXCL` nunca invocada |
| CM-BAJ-002 | Baja | libreria/R/R4XCL-0-UT-Ayuda.R | `UT_Referencias` nunca invocada externamente |
| CM-BAJ-003 | Baja | libreria/R/R4XCL-RG-Binaria.R | Referencia a `R4XCL_INT_DESCRIPCION` inexistente |
| CM-BAJ-004 | Baja | libreria/R/R4XCL-FX-Aleatorios.R | `source()` a ruta BERT2 obsoleta |
| CM-BAJ-005 | Baja | libreria/R/R4XCL-0-Interno-1.R | Bloque comentado de 30+ líneas (R4XCL_INSTALAR_PAQUETES) |
| CM-BAJ-006 | Baja | libreria/R/R4XCL-FX-Aleatorios.R | Validaciones comentadas (6 bloques, ~40 líneas) |
| CM-BAJ-007 | Baja | libreria/JULIA/functions.jl | `TestAdd` y `EigenValues` — funciones de prueba residuales |
| CM-BAJ-008 | Baja | libreria/JULIA/functions.jl vs J4XCL-*.jl | Duplicación completa de funciones entre archivos |
| CM-BAJ-009 | Baja | startup/startup.py | Script Python completo (1058 líneas) — integración deprecada |
| CM-BAJ-010 | Baja | startup/__pycache__/ | Directorio __pycache__ con .pyc compilado |
| CM-BAJ-011 | Baja | startup/startup.r vs R4XCL-0-Interno-3.R | `Extraer_outputs` duplicada (startup.r y libreria) |
| CM-BAJ-012 | Baja | libreria/R/R4XCL-0-Interno-3.R vs startup.r | `procesar_valor`/`.neven_procesar_valor` duplicadas |
| CM-BAJ-013 | Baja | ControlPython/ | Módulo ControlPython completo — deprecado pero compilable |
| CM-BAJ-014 | Baja | libreria/R/R4XCL-0-UT-InstalaPaqueterias.R | Función `UT_INSTALACION_LOCAL` con rutas hardcoded obsoletas |

---

## Hallazgos Detallados

### [CM-BAJ-001] Función R4XCL_INT_CREAXCL nunca invocada
- **Archivo(s):** `libreria/R/R4XCL-0-Interno-1.R` (línea 679)
- **Severidad:** Baja
- **Descripción:** La función `R4XCL_INT_CREAXCL` está definida pero no es invocada en ningún archivo .R del proyecto. Solo aparece mencionada en documentación (`docs/Docusaurus/05-funciones-r.md`).
- **Evidencia:** Búsqueda exhaustiva con grep en todos los archivos .R — solo se encuentra la definición. La función hermana `R4XCL_INT_CREARDS` sí tiene múltiples invocaciones.
- **Recomendación:** Marcar como deprecada o eliminar. Si se desea mantener para uso futuro, documentar explícitamente su propósito.

---

### [CM-BAJ-002] Función UT_Referencias sin invocaciones externas
- **Archivo(s):** `libreria/R/R4XCL-0-UT-Ayuda.R`
- **Severidad:** Baja
- **Descripción:** La función `UT_Referencias` está definida pero no es invocada desde ningún otro archivo .R ni desde código C++. Depende de rutas BERT2 obsoletas (`~/BERT2/functions/R4XCL HELP/`).
- **Evidencia:** Búsqueda en todos los archivos .R y .cc — solo se encuentra la definición. Además, la ruta `~/BERT2/functions/` no existe en la arquitectura actual de NEVEN.
- **Recomendación:** Eliminar o actualizar las rutas a la estructura actual de NEVEN (`C:\NEVEN\`).

---

### [CM-BAJ-003] Referencia a función R4XCL_INT_DESCRIPCION inexistente
- **Archivo(s):** `libreria/R/R4XCL-RG-Binaria.R` (línea 135)
- **Severidad:** Baja
- **Descripción:** En el bloque `TipoOutput == 8`, se invoca `R4XCL_INT_DESCRIPCION()` pero esta función no está definida en ningún archivo del proyecto. Causaría un error en tiempo de ejecución.
- **Evidencia:** Búsqueda exhaustiva en todos los archivos .R — no existe definición de `R4XCL_INT_DESCRIPCION`. El resultado de la llamada se asigna a `A` pero nunca se usa.
- **Recomendación:** Eliminar la línea `A <- R4XCL_INT_DESCRIPCION()` ya que su resultado no se utiliza.

---

### [CM-BAJ-004] source() a ruta BERT2 obsoleta en FX_Distancias
- **Archivo(s):** `libreria/R/R4XCL-FX-Aleatorios.R` (líneas 34-37)
- **Severidad:** Baja
- **Descripción:** La función `FX_Distancias` ejecuta `source("~/BERT2/functions/INTERNO/R4XCL-INTERNO.R")`. La ruta `~/BERT2/` corresponde a la arquitectura anterior del proyecto (BERT2) y no existe en NEVEN. Esto causaría un error en tiempo de ejecución.
- **Evidencia:** La ruta `~/BERT2/functions/INTERNO/` no existe en el repositorio. El AutoLoader.cc carga archivos .R directamente sin necesidad de `source()` explícito.
- **Recomendación:** Eliminar las líneas 33-37 del `source()`. Las funciones internas ya están disponibles globalmente gracias al mecanismo de carga del AutoLoader.

---

### [CM-BAJ-005] Bloque comentado extenso — R4XCL_INSTALAR_PAQUETES
- **Archivo(s):** `libreria/R/R4XCL-0-Interno-1.R` (líneas 720-755, ~35 líneas)
- **Severidad:** Baja
- **Descripción:** Función completa `R4XCL_INSTALAR_PAQUETES` comentada con `#`. No es documentación roxygen2 sino código funcional deshabilitado. Fue reemplazada por `UT_INSTALACION_LOCAL` y `UT_INSTALACION_WEB`.
- **Evidencia:** El bloque está delimitado por `# R4XCL_INSTALAR_PAQUETES <- function(...)` y contiene lógica completa de instalación de paquetes. Las funciones activas en `R4XCL-0-UT-InstalaPaqueterias.R` cumplen la misma función.
- **Recomendación:** Eliminar el bloque comentado. La funcionalidad ya existe en `UT_INSTALACION_LOCAL`.

---

### [CM-BAJ-006] Validaciones comentadas extensas en R4XCL-FX-Aleatorios.R
- **Archivo(s):** `libreria/R/R4XCL-FX-Aleatorios.R`
- **Severidad:** Baja
- **Descripción:** Múltiples bloques de validaciones de parámetros comentados (6 bloques, ~40 líneas totales) en las funciones `FX_Distancias`, `FX_AleatorioUniforme`, `FX_AleatorioNormal` y `FX_Muestreo`. Son código funcional deshabilitado, no documentación.
- **Evidencia:** Cada función tiene un bloque `# if (!is.numeric(...)) { stop(...) }` comentado. Patrón repetido en líneas 14-22, 97-107, 155-163, 210-218.
- **Recomendación:** Descomentar las validaciones (son buenas prácticas) o eliminarlas si se decidió no validar por rendimiento.

---

### [CM-BAJ-007] Funciones de prueba residuales TestAdd y EigenValues en Julia
- **Archivo(s):** `libreria/JULIA/functions.jl` (líneas 38-44)
- **Severidad:** Baja
- **Descripción:** Las funciones `TestAdd` y `EigenValues` son funciones triviales de prueba/demo que permanecen en el archivo principal de la librería Julia. `TestAdd` solo suma argumentos y `EigenValues` es un wrapper trivial de `eigvals()`.
- **Evidencia:** No se invocan desde ningún otro archivo .jl ni desde código C++. `EigenValues` es redundante con `JM_Algebra(Matriz, nothing, 4)` que calcula valores propios con más funcionalidad. `TestAdd` es claramente una función de prueba por su nombre.
- **Recomendación:** Mover a un archivo de tests o eliminar. La funcionalidad de eigenvalues está cubierta por `JM_Algebra`.

---

### [CM-BAJ-008] Duplicación completa entre functions.jl y módulos J4XCL-*.jl
- **Archivo(s):** `libreria/JULIA/functions.jl` (648 líneas) vs `J4XCL-MT-Matematicas.jl`, `J4XCL-ML-Aprendizaje.jl`, `J4XCL-OP-Optimizacion.jl`, `J4XCL-CN-Conectividad.jl`
- **Severidad:** Baja
- **Descripción:** El archivo `functions.jl` contiene versiones compactas de las mismas funciones que están implementadas de forma expandida en los 4 módulos J4XCL. Las funciones duplicadas son:
  - `JM_Algebra` — en functions.jl y J4XCL-MT-Matematicas.jl
  - `JM_Calculo` — en functions.jl y J4XCL-MT-Matematicas.jl
  - `JM_EDO` — en functions.jl y J4XCL-MT-Matematicas.jl
  - `JML_Clasificacion` — en functions.jl y J4XCL-ML-Aprendizaje.jl
  - `JML_Clustering` — en functions.jl y J4XCL-ML-Aprendizaje.jl
  - `JML_Estadistica` — en functions.jl y J4XCL-ML-Aprendizaje.jl
  - `JO_Optimizar` — en functions.jl y J4XCL-OP-Optimizacion.jl
  - `JC_Transformar` — en functions.jl y J4XCL-CN-Conectividad.jl
- **Evidencia:** Comparación directa del código muestra las mismas firmas de función con implementaciones equivalentes. Los módulos J4XCL son versiones expandidas con mejor documentación y manejo de errores.
- **Recomendación:** Eliminar `functions.jl` y usar exclusivamente los módulos J4XCL-*.jl, o convertir `functions.jl` en un archivo de re-exportación que haga `include()` de los módulos.

---

### [CM-BAJ-009] Script startup.py completo — integración Python deprecada
- **Archivo(s):** `startup/startup.py` (1058 líneas)
- **Severidad:** Baja
- **Descripción:** El archivo `startup.py` contiene una integración Python completa (1058 líneas) incluyendo: captura de diagnósticos, gráficos matplotlib/plotly, integración Quarto, generador de documentación HTML, e integración con APIs de IA. Según la documentación del proyecto, Python está deprecado ("OFF por defecto — causaba hangs").
- **Evidencia:** El steering file indica "Python fue integrado pero está deprecado (OFF por defecto) — causaba hangs". Sin embargo, `NEVEN_ENABLE_PYTHON` sigue como `ON` en CMakeLists.txt y el archivo se copia al directorio de distribución. El stdout/stderr redirect está comentado con nota "was causing hangs".
- **Recomendación:** Si Python está deprecado, cambiar `NEVEN_ENABLE_PYTHON` a `OFF` por defecto y mover `startup.py` a un directorio `deprecated/` o archivarlo. Si se planea reactivar, documentar el estado actual.

---

### [CM-BAJ-010] Directorio __pycache__ con bytecode compilado
- **Archivo(s):** `startup/__pycache__/startup.cpython-312.pyc`
- **Severidad:** Baja
- **Descripción:** Existe un directorio `__pycache__` con bytecode Python compilado en el repositorio. Estos archivos son artefactos de ejecución que no deberían estar versionados.
- **Evidencia:** `startup/__pycache__/startup.cpython-312.pyc` presente en el directorio.
- **Recomendación:** Agregar `__pycache__/` al `.gitignore` y eliminar el directorio del repositorio.

---

### [CM-BAJ-011] Función Extraer_outputs duplicada entre startup.r y librería
- **Archivo(s):** `startup/startup.r` (líneas 67-107) y `libreria/R/R4XCL-0-Interno-3.R` (líneas 5-88)
- **Severidad:** Baja
- **Descripción:** La función `Extraer_outputs` existe en dos versiones:
  1. **startup.r**: Versión simplificada (sin verbose, sin R6, campos omitidos hardcoded)
  2. **R4XCL-0-Interno-3.R**: Versión expandida (con verbose, soporte R6, más estadísticas)
  
  Ambas se cargan en el entorno global, la segunda sobrescribe a la primera.
- **Evidencia:** Ambos archivos definen `Extraer_outputs <- function(objeto, nombre_modelo = NULL, ...)`. La versión de la librería es más completa y es la que efectivamente se usa (invocada en 10 archivos .R).
- **Recomendación:** Eliminar la versión de `startup.r` ya que es sobrescrita por la versión de la librería.

---

### [CM-BAJ-012] Funciones auxiliares duplicadas procesar_valor / .neven_procesar_valor
- **Archivo(s):** `startup/startup.r` y `libreria/R/R4XCL-0-Interno-3.R`
- **Severidad:** Baja
- **Descripción:** Las funciones de apoyo para `Extraer_outputs` están duplicadas con nombres diferentes:
  - `startup.r`: `.neven_procesar_valor` y `.neven_consolidar`
  - `R4XCL-0-Interno-3.R`: `procesar_valor` y `consolidar`
  
  La lógica es idéntica en ambos casos.
- **Evidencia:** Comparación del código muestra implementaciones equivalentes. Las versiones de la librería (sin prefijo `.neven_`) son las que se usan efectivamente.
- **Recomendación:** Eliminar `.neven_procesar_valor` y `.neven_consolidar` de `startup.r`.

---

### [CM-BAJ-013] Módulo ControlPython completo — deprecado pero compilable
- **Archivo(s):** `ControlPython/` (CMakeLists.txt, src/control_python.cc, src/python_interface.cc)
- **Severidad:** Baja
- **Descripción:** El directorio `ControlPython/` contiene un módulo completo para embeber CPython como proceso hijo. Según la documentación, Python está deprecado y causaba hangs. Sin embargo, el módulo sigue compilándose por defecto (`NEVEN_ENABLE_PYTHON ON`).
- **Evidencia:** 
  - CMakeLists.txt principal: `option(NEVEN_ENABLE_PYTHON ... ON)`
  - El binario `ControlPython.exe` se genera y copia al directorio de distribución
  - La documentación indica que Python está "OFF por defecto" pero el CMake dice lo contrario
- **Recomendación:** Alinear la documentación con el código. Si Python está deprecado, cambiar a `OFF` por defecto. Considerar mover a una rama separada o directorio `deprecated/`.

---

### [CM-BAJ-014] UT_INSTALACION_LOCAL con rutas hardcoded obsoletas
- **Archivo(s):** `libreria/R/R4XCL-0-UT-InstalaPaqueterias.R`
- **Severidad:** Baja
- **Descripción:** La función `UT_INSTALACION_LOCAL` instala paquetes desde archivos .tar.gz locales con versiones muy antiguas (2017-2018). Las versiones hardcoded son incompatibles con R 4.4.1. Además, el bloque `TipoOutput == 999` referencia variables locales (`pSVDIALOGS`, `pDEVTOOLS`, etc.) que no están definidas en ese scope, causando un error en tiempo de ejecución.
- **Evidencia:** Versiones como `dplyr_0.7.4` (2017), `devtools_1.13.5` (2018) son incompatibles con R 4.4.1. El repositorio CRAN snapshot `2018-03-15` en `UT_INSTALACION_WEB` también es obsoleto.
- **Recomendación:** Actualizar las versiones de paquetes o eliminar la función de instalación local. Usar `UT_INSTALACION_WEB` con un snapshot CRAN actualizado (2024+).

---

## Estadísticas

| Categoría | Cantidad |
|-----------|----------|
| Funciones R no invocadas | 2 |
| Funciones Julia residuales/test | 2 |
| Archivos con duplicación | 3 |
| Código comentado extenso | 2 |
| Integración Python deprecada | 3 |
| Referencias a rutas obsoletas | 2 |
| **Total hallazgos** | **14** |

## Notas Metodológicas

1. **Mecanismo de carga R:** Los archivos .R en `libreria/R/` son cargados por `AutoLoader.cc` que itera sobre el directorio y ejecuta cada archivo .R. No hay `source()` explícito en `startup.r` para estos archivos.
2. **Mecanismo de carga Julia:** `startup.jl` define el módulo NEVEN con `ReadScriptFile` que es invocado desde C++ (`ControlJulia`) para cargar archivos .jl adicionales.
3. **Python:** `startup.py` es cargado por `ControlPython.exe` que embebe CPython. La función `read_script_file()` permite cargar scripts adicionales.
4. **Criterio de "código muerto":** Se consideró muerto el código que: (a) no es invocado por ningún otro código, (b) referencia rutas/funciones inexistentes, (c) está comentado sin ser documentación, o (d) duplica funcionalidad existente sin valor agregado.
