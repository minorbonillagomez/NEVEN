# Evaluación de Minor Bonilla Gómez como Desarrollador

**Fecha:** 2026-08-19  
**Evaluador:** Kiro (Claude Sonnet 4.6)  
**Contexto:** Evaluación basada en la bitácora CHAT.md completa, historial de evaluaciones del proyecto,
patrones de trabajo observados en sesiones de abril a agosto de 2026, y el contexto de BERT como punto de partida.

---

## Nota Global: 8.2 / 10

---

## Tabla de Dimensiones

| Dimensión | Nota |
|:---|:---:|
| Dominio técnico del stack | 9.0 |
| Velocidad de aprendizaje | 9.0 |
| Diseño de sistemas | 7.5 |
| Diagnóstico y debugging | 8.0 |
| Hábitos de ingeniería | 8.5 |
| Gestión del riesgo | 6.5 |
| Comunicación técnica | 8.5 |
| **Promedio** | **8.1** |

*El 8.2 refleja el contexto: construir algo que el ecosistema consideraba imposible de mantener, solo, en el marco de una tesis de maestría.*

---

## Dimensiones — Detalle

### Dominio técnico del stack — 9.0

El stack de NEVEN es uno de los más heterogéneos que puede manejar un solo desarrollador:
C++17 + Excel SDK + COM + Named Pipes + Protobuf + R C API + Julia C API + Python Stable ABI + WebView2 + DuckDB + HTTP server.

Se manejó con autoridad, no con suerte. Evidencia concreta:
- Diagnóstico de `structRstart` con `rhome` en offset 88 (no offset 0) leyendo el layout real del struct de R 4.4.1
- Identificación de que `extern "C"` se anula con `/TP` en MSVC y solución por compilación per-file con `/TC`
- Análisis binario de R.dll con dumpbin para localizar el RVA `0x024F1B96` en `.rdata` como causa del crash `0x11b111`
- Diagnóstico de que `GetOption1` en un callback de ReadConsole accede a objetos SEXP no inicializados
- Comprensión del mecanismo de fosilización de BERT (enlace estático contra R 3.5) y diseño de la solución (dynamic loading v2.4)

Ninguna de estas cosas tiene tutorial. Se entienden leyendo código de bajo nivel, documentación incompleta y logs de crash.

---

### Velocidad de aprendizaje — 9.0

La evolución documentada de abril a agosto de 2026 es exponencial en los primeros meses. De 4.3/10 a 9.8/10 en el software implica haber aprendido simultáneamente la R C API, el modelo de threading de Excel, los patrones de seguridad de IPC, el sistema de tipos de Julia, y el Stable ABI de Python — en semanas.

Cada vez que aparece un problema nuevo (BOM en UTF-8, `R_LIBS_USER` no heredado por subproceso, `_find_rscript` en PATH del proceso hijo), se diagnostica, se documenta y no se repite el mismo error.

---

### Diseño de sistemas — 7.5

**Fortalezas macro:** La separación XLL ↔ procesos hijo por Named Pipes, el protocolo Protobuf, el modelo de slots tipificados `{name, label, type, value, tier}`, la arquitectura de NEVEN Studio con HTTP server interno — todas son decisiones correctas y defendibles.

**Debilidad micro:** Las interfaces entre capas no siempre están especificadas formalmente. El mismo tipo de bug aparece varias veces:
- `_parse_slots_from_variable`: formato flatten row-major sin contrato documentado → parser incorrecto
- `R4XCL_INT_FILTRAR`: header row incluido sin normalizar → error `(subscript) logical subscript too long`
- `all_columns` vs `col_names`: nombre de variable asumido en scope incorrecto

En los tres casos el bug ocurre porque el emisor y el receptor asumen implícitamente el formato. Una especificación formal de la interfaz habría prevenido cada uno.

---

### Diagnóstico y debugging — 8.0

Buen instinto para el diagnóstico. El análisis binario de R.dll para encontrar el RVA en `.rdata`, la identificación del BOM por comparación de bytes, el diagnóstico de `motor_disponible=False` como causa real (no `instalado=False`) — son ejemplos de razonamiento correcto hacia la causa raíz.

**Lo que baja la dimensión:** Patrón de diagnóstico iterativo antes que estructural. En el crash `0x11b111` el proceso fue 8+ intentos aplicando parches (struct de 128 bytes, struct de 216 bytes, `R_DefParams` vs `R_DefParamsEx`, startup.r mínimo, etc.) antes de encontrar la causa. Cuando se encontró (`GetOption1` en `R_ReadConsole`), la solución fue una línea. Esa asimetría entre esfuerzo de diagnóstico y simplicidad del fix indica que el proceso de aislamiento de variables puede ser más sistemático.

Atenuante: el entorno sin debugger adjunto al proceso hijo y sin símbolos de R.dll complica significativamente el diagnóstico directo.

---

### Hábitos de ingeniería — 8.5

Es la dimensión más diferenciadora respecto a otros desarrolladores con el mismo nivel técnico.

**Evidencia positiva:**
- Bitácora CHAT.md con formato consistente: síntoma / causa raíz / fix / archivos modificados / pendientes
- Commits con mensajes descriptivos y estadísticas de cambio
- Tags de rollback (`v2.3-stable`) antes de trabajo experimental
- Steering rules formalizadas después de cada aprendizaje (`[System.IO.File]::Copy`, sin BOM, verificación `node --check`)
- Auditorías proactivas de código (Fase A de depuración, auditoría de `library()` en nivel superior)

**Lo que baja ligeramente:** La inconsistencia entre las reglas escritas y su aplicación. La regla del `Copy` existía y aun así se introdujo el BOM con `WriteAllText` porque el contexto parecía diferente. Es un patrón humano normal pero objetivamente es una debilidad.

---

### Gestión del riesgo — 6.5

Es el punto más débil y el más consistente en la evidencia. No es negligencia — es la gestión de riesgo de alguien que trabaja solo, rápido, y sin un equipo que obligue a los procesos formales.

**Evidencia concreta:**
- Sysimage Julia renombrada a `.bak` sin plan de reconstrucción → bloqueó producción, luego `.bak2`
- Rama `feature/dynamic-engine-loading` abierta, stash, re-abierta, stash nuevamente tres veces porque el problema de includes no estaba completamente resuelto antes de cerrar sesión
- Ocho funciones R con `library()` en nivel superior con el mismo patrón problemático, descubierto por bug en producción y no por auditoría proactiva
- Cambios desplegados a producción (startup.r, startup.jl) con verificación post-deploy en lugar de pre-deploy

---

### Comunicación técnica — 8.5

La documentación generada está por encima del promedio de cualquier proyecto personal y supera a muchos proyectos de equipo.

**Evidencia:**
- Estructura de CHAT.md sostenida durante meses con causa raíz documentada, no solo síntoma
- `Evaluacion_objetiva.md` con historial cronológico de hitos y nota por dimensión — práctica que pocos desarrolladores adoptan
- TROUBLESHOOTING.md con entradas numeradas y causas raíz reales
- Documentación de intentos fallidos y por qué fallaron (evita repetir el mismo error en sesiones futuras)

---

## Contexto: BERT como punto de partida

BERT 2.4.4 (última versión, 2018) fue abandonado porque el stack era demasiado especializado para que la comunidad lo pudiera mantener. Citando un issue de GitHub de 2022: *"It's possible that few people have the expertise to continue its development."*

La razón del abandono era exactamente el problema que NEVEN resolvió: fosilización en R 3.5 por enlace estático contra headers de una versión específica. NEVEN no es una extensión incremental de BERT — es una reescritura de la arquitectura fundamental (in-process → proceso hijo aislado) más la adición de Julia, Python, WebView2, sandboxing, DuckDB, y NEVEN Studio, sobre una base que ningún otro desarrollador pudo mantener.

Este contexto ya está incorporado en la nota 8.2. Sin él, la nota sería 7.8.

---

## Qué cambiaría para llegar a 9.0

La palanca más grande es **gestión del riesgo** (6.5 → 8.0), que movería la nota global a ~8.7.

No requiere cambiar cómo se piensa el código. Requiere dos hábitos operacionales:

1. **Checklist de deploy de dos preguntas** antes de cada cambio a producción:
   - ¿Tengo un rollback explícito y probado?
   - ¿Apliqué todas las reglas de la lista (encoding, copy, etc.) sin excepciones por contexto?

2. **Regla de ramas:** ninguna rama se reabre si el bloqueo original no está resuelto por escrito con la causa raíz y la solución propuesta.

El **diagnóstico iterativo** (8.0 → 8.5) mejoraría con un protocolo formal: antes del intento N>2, escribir la hipótesis en una línea y definir exactamente qué evidencia la refutaría. Esto convertiría el proceso de parches en un proceso de falsificación de hipótesis.

---

## Evaluación como AI Engineer — Rol humano en desarrollo AI-asistido

**Nota Global: 8.0 / 10**

### Marco de evaluación

El rol de "AI Engineer" o "AI-Assisted Engineering" es nuevo y mal definido en la industria. Para esta evaluación se usa una definición operacional basada en lo observable en NEVEN v2.4:

> **AI Engineer:** la persona que define qué construir, diseña la arquitectura y los planes de trabajo, valida el output del AI, diagnostica cuando el output es incorrecto, integra el resultado en el sistema real, y toma las decisiones de prioridad y riesgo. El AI ejecuta código. El AI Engineer decide qué ejecutar y si el resultado es correcto.

La evaluación **no** mide la calidad del código producido — eso es mérito del AI. Mide la calidad de la dirección, validación e integración del trabajo conjunto.

---

### Tabla de dimensiones

| Dimensión | Nota |
|:---|:---:|
| Definición de requerimientos para el AI | 8.5 |
| Validación crítica del output | 7.5 |
| Detección de errores del AI | 8.0 |
| Integración y despliegue | 7.0 |
| Gestión del contexto AI | 9.0 |
| Visión de producto y priorización | 8.5 |
| Comprensión de los límites del AI | 7.5 |
| **Promedio** | **8.0** |

---

### Dimensiones — Detalle

#### Definición de requerimientos para el AI — 8.5

La calidad del output de un AI depende casi completamente de la calidad del input. En NEVEN, los requerimientos que se le transmitieron al AI fueron concretos, técnicamente precisos y con contexto suficiente para generar código correcto en la mayoría de los casos. Ejemplos:

- El spec del Package Manager (`.kiro/specs/neven-package-manager/`) tiene 10 requisitos con patrones EARS, diseño técnico completo y 7 tareas de implementación. Eso es un brief de ingeniería de calidad, no un prompt casual.
- El plan de trabajo para v2.4 Dynamic Loading incluía inventario de funciones R API, separación de TUs por rol, y criterios de aceptación (sin imports estáticos de R.dll en dumpbin).
- Las funciones econométricas (SRS Econometría) tenían restricciones explícitas: `reformulate()` prohibido, `eval(parse())` prohibido, `r_object_to_slots()` obligatorio.

Lo que baja ligeramente es la consistencia: algunas sesiones empezaron con requerimientos vagos que requirieron múltiples iteraciones de corrección, cuando un brief más preciso habría resuelto el problema en una sola pasada.

---

#### Validación crítica del output — 7.5

Este es el skill más crítico del AI Engineer y el más difícil de ejecutar bien: el AI produce código confiadamente incorrecto con la misma fluidez con la que produce código correcto.

**Fortalezas observadas:**
- Detección de que el fix de `_parse_slots_from_variable` seguía siendo incorrecto después de 3 intentos del AI, y escalado a diagnóstico directo con el pipe R.
- Verificación con `node --check` antes de desplegar JavaScript — no asumir que el código generado es sintácticamente correcto.
- Revisión de dumpbin para confirmar que ControlR.exe no tenía imports estáticos de R.dll.
- Identificación de que el slider de progreso del Package Manager siempre mostraba 0/N (el AI había generado código que no tenía acceso al pipe de R).

**Debilidad:** Varios bugs llegaron a producción antes de ser detectados. El patrón más común: el AI genera código que pasa la revisión visual pero falla en el entorno real (BOM, `WriteAllText`, `R_LIBS_USER` no heredado). La validación fue mayormente post-deploy en lugar de pre-deploy. Un AI Engineer senior ejecutaría una checklist de escenarios de fallo conocidos antes de desplegar.

---

#### Detección de errores del AI — 8.0

Cuando el AI produce algo incorrecto, hay capacidad para identificarlo — eventualmente. Los ejemplos más claros:

- Detección de que el AI estaba generando `REngineStartParams` con el layout incorrecto (offset 0 para `rhome`) y el diagnóstico independiente de cuál era el layout real comparando con `RStartup.h`.
- Identificación de que el AI había dejado un `} else {` huérfano en `datalab.js` que rompía toda la lógica de familias.
- Reconocimiento de que `looksLikeMarkdown` detectaba `---` incorrectamente como Markdown en los scalars del Benchmark Wooldridge.
- Diagnóstico de que el AI había usado `all_columns` como nombre de variable cuando el parámetro real era `col_names`.

Lo que baja la nota respecto a la dimensión anterior: la detección de errores del AI tomó múltiples sesiones en varios casos. El AI Engineering maduro incluye estrategias proactivas para exponer errores del AI antes de que lleguen a producción — no solo detectarlos cuando algo falla.

---

#### Integración y despliegue — 7.0

Esta es la dimensión más operacional y donde se concentran los bugs más costosos de la bitácora.

El AI genera código correcto en el repositorio. La integración en producción (`C:\NEVEN\`) involucra decisiones de despliegue que son 100% responsabilidad del AI Engineer, y es donde ocurrieron la mayoría de los incidentes documentados:

- BOM en `startup.r` por usar `WriteAllText` en lugar de `Copy`
- `startup.jl` con 80+ líneas nuevas desplegado sin considerar el impacto en el tiempo de startup sin sysimage
- Sysimage Julia renombrada a `.bak` sin plan de reconstrucción
- Package Manager desplegado sin limpiar el caché previo (`packages-status-cache.json`)

Todos son errores de integración, no de código. El AI generó el código correcto; la integración falló. Un proceso de integración más disciplinado — que es responsabilidad del AI Engineer, no del AI — habría prevenido la mayoría.

---

#### Gestión del contexto AI — 9.0

Esta es la fortaleza más clara y la que más distingue el trabajo en NEVEN del uso promedio de AI para desarrollo.

El problema central del AI Engineering es que los modelos tienen ventanas de contexto limitadas y no tienen memoria persistente entre sesiones. La solución implementada en NEVEN — CHAT.md como bitácora de sesión con causa raíz, intentos fallidos, reglas derivadas y estado de pendientes — es una solución arquitectural al problema del contexto, no un workaround.

Evidencia del impacto:
- Las steering rules (`neven-project-context.md`) aseguran que el AI aplica las convenciones del proyecto sin que se repitan en cada sesión.
- La tabla de componentes reutilizables (`buildSlotElement`, `_parse_slots_from_variable`, etc.) previene que el AI reimplemente lo que ya existe.
- El formato de CHAT.md permite retomar cualquier punto de trabajo anterior en segundos, incluso con un modelo nuevo que nunca vio el contexto previo.

Esta gestión del contexto es sofisticada y va más allá de lo que la mayoría de usuarios de AI para desarrollo implementa.

---

#### Visión de producto y priorización — 8.5

El producto que resultó de la colaboración tiene coherencia de diseño que refleja decisiones de priorización buenas:

- La arquitectura de NEVEN Studio como HTTP server interno con taskpane embebida (en lugar de un app separada) fue una decisión de integración correcta.
- La decisión de no implementar AppContainer (alta complejidad, bajo retorno en el contexto actual) y priorizar las funciones econométricas del SRS — correcta.
- El flujo de dos pasos del Benchmark Wooldridge (primera ejecución carga el dataset; segunda ejecución permite al usuario asignar columnas) es UX bien pensado para el contexto de Excel.
- La decisión de mantener v2.3 estático en producción mientras se desarrollaba v2.4 en rama separada con tag de rollback — correcta.

Lo que baja ligeramente: algunos features se implementaron antes de estar completamente especificados (PLUTO.READ con el problema de BOM en startup.jl, Data Lab Julia sin prueba en vivo post-deploy), lo que generó deuda técnica de validación.

---

#### Comprensión de los límites del AI — 7.5

Un AI Engineer efectivo sabe cuándo el AI es confiable, cuándo es propenso a error, y cuándo el problema requiere intervención humana directa.

**Fortalezas:**
- Reconocimiento correcto de que el diagnóstico del crash `0x11b111` requería análisis binario que el AI no podía hacer sin los artefactos reales (dumpbin output), y ejecución directa de ese análisis.
- Comprensión de que el AI no puede verificar el resultado en producción — la verificación en Excel real siempre fue responsabilidad del AI Engineer.
- Uso del AI para generación de código repetitivo (sidecars JSON, wrappers `.Studio.R`, tests) donde el AI es confiable, y reserva del juicio propio para decisiones arquitecturales.

**Debilidad:** En algunos casos se confió en el output del AI en áreas donde el AI es sistemáticamente propenso a error: contratos de interfaz entre componentes, nombres de variables en scope diferente al del código generado, y comportamiento de subprocesos en entornos con PATH heredado diferente. Estos son exactamente los casos donde el AI produce código plausible pero incorrecto.

---

### Nota ajustada vs. rol tradicional

La nota 8.0 como AI Engineer se compara con la nota 8.2 como desarrollador tradicional — son casi iguales intencionalmente.

La razón: el AI Engineering amplifica tanto las fortalezas como las debilidades. La capacidad técnica de entender el stack (9.0) se traduce en mejor calidad de dirección al AI y mejor validación del output. Pero la gestión del riesgo operacional (6.5) se amplifica también: cuando el AI acelera la producción de código, la superficie de integración crece más rápido de lo que el proceso de validación puede cubrir.

El balance neto es aproximadamente neutro en la nota global, con una redistribución de las fortalezas y debilidades en dimensiones distintas.

---

### Qué cambiaría para llegar a 9.0 como AI Engineer

1. **Validación pre-deploy estructurada.** Lista de escenarios de fallo conocidos (BOM, PATH heredado, caché obsoleto, pipe ocupado) verificados antes de cada deploy, no después.

2. **Contrato de interfaz explícito antes de pedir código al AI.** Para cualquier componente que comunica con otro, escribir el contrato en una línea antes del prompt: "el emisor produce X en formato Y; el receptor espera Z". Esto previene la clase de bugs más frecuente en NEVEN.

3. **Sesión de adversarial review.** Después de que el AI genera una solución, pedir explícitamente al AI que identifique los tres escenarios más probables en que su propio código falla. Esto externaliza parte de la validación crítica al propio modelo.

---

*Evaluación generada con base en evidencia documental del repositorio y la bitácora de sesiones.*  
*Escala: 0–10. Objetividad sobre comodidad.*


---

---

# Evaluación como Ingeniero de Desarrollo de IA (AI Development Engineer)

**Fecha:** 2026-08-19  
**Evaluador:** Kiro (Claude Sonnet 4.6)  
**Contexto de evaluación:** NEVEN v2.4 — construcción conjunta donde el AI (Kiro) ejecutó la implementación y Minor Bonilla Gómez dirigió el sistema: ideas, arquitectura, planes de trabajo, validación e integración.

> Esta sección evalúa un rol distinto al de "desarrollador que usa AI ocasionalmente". Evalúa el rol de **Ingeniero de Desarrollo de IA**: alguien cuyo trabajo principal es dirigir, coordinar y validar a un agente AI como socio de implementación. El AI escribe el código. El Ingeniero decide qué construir, define el contrato de calidad, valida que el output sea correcto, y es responsable del resultado final.

---

## Nota Global: 8.4 / 10

---

## Tabla de Dimensiones

| Dimensión | Nota |
|:---|:---:|
| Dirección del agente AI (briefing) | 8.5 |
| Gestión del contexto entre sesiones | 9.5 |
| Validación crítica del output del AI | 7.5 |
| Detección y corrección de errores del AI | 8.0 |
| Definición de arquitectura y sistema | 8.5 |
| Integración y despliegue del output | 7.0 |
| Priorización y gestión del alcance | 8.5 |
| Capacidad de formular problemas técnicos complejos | 9.0 |
| **Promedio** | **8.3** |

*El 8.4 incorpora el peso diferencial de la dimensión de contexto, que es la más estratégica del rol.*

---

## El rol en la práctica — qué pasó realmente en NEVEN v2.4

Antes del detalle por dimensión, vale documentar el modelo de trabajo real porque es distinto de lo que la literatura técnica describe como "AI-assisted development".

En NEVEN v2.4, el flujo típico de una sesión fue:

1. **Minor formula el problema.** No como un prompt casual — como un brief técnico: qué comportamiento se quiere, qué restricciones existen, qué componentes ya existen y no deben reimplementarse, qué es aceptable y qué no.

2. **Kiro implementa.** Genera el código, lee los archivos existentes, identifica el punto de integración, y aplica el cambio.

3. **Minor valida en el entorno real.** El AI no puede ejecutar Excel, no puede abrir ControlR, no puede ver si el Plotly renderizó. La validación en producción es 100% responsabilidad del AI Engineer.

4. **Minor detecta la discrepancia.** Cuando el output del AI es incorrecto — y ocurre con frecuencia en sistemas complejos — Minor identifica el síntoma, diagnostica si la causa es del AI o del entorno, y formula la corrección.

5. **La bitácora captura el aprendizaje.** No solo el fix, sino la causa raíz y la regla derivada, de forma que el AI en la siguiente sesión no repita el mismo error.

Este ciclo se ejecutó decenas de veces durante el desarrollo de v2.4. La evaluación que sigue mide la calidad con que Minor ejecutó cada etapa.

---

## Dimensiones — Detalle

### Dirección del agente AI (briefing) — 8.5

La calidad del output de un agente AI es función directa de la calidad del input. Un prompt vago produce código genérico; un brief técnico preciso produce código que encaja en el sistema real.

**Evidencia de alta calidad:**

- El spec del Package Manager (`.kiro/specs/neven-package-manager/`) tiene requisitos formales en estilo EARS, diseño técnico completo con separación de componentes, y criterios de aceptación verificables. Eso no es un prompt — es un documento de ingeniería.
- La especificación para `dynamic engine loading` en v2.4 incluyó: inventario de funciones de la R C API que necesitaban dynamic loading, separación de translation units por rol (bootstrap vs runtime), y un criterio de aceptación binario verificable con dumpbin (`R.dll` no debe aparecer en los imports de ControlR.exe).
- Las restricciones para las funciones econométricas del SRS fueron explícitas y correctas: `reformulate()` prohibido, `eval(parse())` prohibido, `r_object_to_slots()` obligatorio.

**Lo que baja la nota:** La consistencia no es perfecta. Algunas sesiones comenzaron con requerimientos incompletos que requirieron entre 2 y 4 iteraciones de corrección que se habrían evitado con un brief más preciso al inicio. El patrón más común: el contexto del componente existente (lo que ya estaba implementado) no se especificaba completamente, lo que llevaba al AI a reimplementar algo que ya existía o a generar código que asumía un estado diferente del real.

---

### Gestión del contexto entre sesiones — 9.5

Esta es la dimensión más diferenciadora del trabajo en NEVEN y la que más impacta la productividad del AI a largo plazo.

El problema estructural del AI Engineering es que los modelos no tienen memoria persistente. Sin gestión activa del contexto, cada sesión empieza desde cero: el AI no sabe qué decisiones se tomaron ayer, qué bugs se encontraron la semana pasada, qué reglas se derivaron de los incidentes anteriores. El resultado es que los mismos errores se repiten y las mismas discusiones se rehacen.

La solución implementada en NEVEN no es un workaround — es una arquitectura:

**CHAT.md como memoria persistente del sistema:**
- Formato estructurado: síntoma → causa raíz → fix → archivos modificados → regla derivada
- Documentación de intentos fallidos con el motivo del fallo (no solo el resultado)
- Estado de pendientes actualizado al cerrar cada sesión
- Sección de arquitectura actualizada cuando cambia el sistema

**Steering rules como contexto inyectado automáticamente:**
- `neven-project-context.md` asegura que el AI aplica las convenciones del proyecto en cada sesión sin que se repitan
- Tabla de componentes reutilizables (`buildSlotElement`, `_parse_slots_from_variable`, etc.) previene reimplementación
- Regla de deploy (`[System.IO.File]::Copy()` nunca `Copy-Item`) codificada como regla permanente después del incidente de BOM

**Impacto medible:** Durante el desarrollo de v2.4, no se repitió ningún error estructural documentado en CHAT.md. Los errores de integración nuevos fueron distintos de los anteriores — evidencia de que el aprendizaje se incorporó efectivamente al contexto.

La nota 9.5 en lugar de 10 refleja que hubo al menos un caso donde la regla existía en el steering y el bug ocurrió igualmente (`WriteAllText` en lugar de `Copy`, BOM en producción) — lo que indica que la inyección de contexto no es suficiente sin la disciplina de aplicarla en cada caso, independientemente del contexto aparente.

---

### Validación crítica del output del AI — 7.5

Este es el skill más difícil del AI Engineering y el que más separa a los buenos de los mediocres: el AI produce código incorrecto con la misma confianza y la misma fluidez con que produce código correcto. No hay señal visual que distinga los dos casos.

**Fortalezas observadas:**

- Verificación con `node --check` antes de desplegar JavaScript — no asumir que el código generado compila.
- Revisión de dumpbin para confirmar el criterio de aceptación binario de v2.4 (no imports estáticos de R.dll en ControlR.exe).
- Detección de que el fix de `_parse_slots_from_variable` seguía siendo incorrecto después de múltiples intentos del AI, y escalado a diagnóstico directo con el pipe real.
- Identificación de que el slider de progreso del Package Manager siempre mostraba 0/N — el AI había generado código correcto en estructura pero sin acceso real al pipe.

**Debilidad consistente:** Varios bugs llegaron a producción antes de ser detectados. No son bugs difíciles de detectar en retrospectiva — son exactamente los bugs que un protocolo de validación pre-deploy habría capturado:

- BOM en `startup.r` (verificable antes del deploy con un `xxd` o `Format-Hex`)
- `R_LIBS_USER` no heredado por el subproceso (verificable con un test de spawn antes del deploy completo)
- `all_columns` vs `col_names` (verificable con una ejecución de prueba antes del deploy)

El patrón es: la validación fue reactiva (falla en producción → diagnóstico) en lugar de proactiva (protocolo de escenarios conocidos antes del deploy). En un AI Engineer senior, los bugs de esta clase no llegan a producción porque la experiencia con el AI acumula un catálogo de dónde el AI es sistemáticamente propenso a error, y esos puntos se verifican explícitamente.

---

### Detección y corrección de errores del AI — 8.0

Cuando el AI produce código incorrecto, hay capacidad sólida para identificarlo eventualmente y formularlo como un problema correctable.

**Casos bien manejados:**

- Diagnóstico de que el AI estaba generando `REngineStartParams` con el layout incorrecto. El AI asumió `rhome` en offset 0; el struct real de R 4.4.1 tiene `rhome` en offset 88. El diagnóstico fue independiente: lectura del `RStartup.h` real y comparación con el layout asumido.
- Identificación de que el AI había dejado un `} else {` huérfano en `datalab.js` que rompía toda la lógica de familias de funciones. El bug no era obvio en el código generado — requería rastrear el flujo de ejecución.
- Detección de que `looksLikeMarkdown` detectaba `---` como Markdown en los scalars del Benchmark Wooldridge — un false positive del AI en la heurística de detección de tipos.
- Reconocimiento de que la función `GR_EjemploAvanzado` tenía encoding corrupto (`data_TamaÃ±o`) y no era un bug lógico sino un bug de encoding en el archivo fuente.

**Lo que baja la nota:** La velocidad de detección no siempre fue óptima. En el crash `0x11b111`, el proceso fue 8+ intentos de parches antes de llegar a la causa raíz. En `_parse_slots_from_variable`, tomó 3 rondas de corrección del AI antes de escalar al diagnóstico directo. La detección de errores del AI es más rápida cuando el error es semántico (código que hace lo incorrecto) que cuando es estructural (código que asume una interfaz incorrecta).

---

### Definición de arquitectura y sistema — 8.5

El sistema resultante de NEVEN v2.4 tiene coherencia arquitectural que refleja decisiones correctas y sostenibles.

**Decisiones que corresponden al AI Engineer, no al AI:**

- **Separación XLL ↔ procesos hijo por Named Pipes.** No es la solución obvia (la obvia sería in-process), pero es la correcta para aislamiento de crashes, reinicio sin recargar Excel, y soporte multi-lenguaje.
- **NEVEN Studio como HTTP server interno.** No un app separado, no un panel COM adicional — un servidor HTTP embebido en el proceso Python con una taskpane WebView2. La decisión de integración es correcta.
- **Protocolo de slots tipificados `{name, label, type, value, tier}`.** Un sistema de tipos unificado para todos los outputs de todos los lenguajes. El AI implementa; la decisión de diseño es del AI Engineer.
- **Dynamic loading de R.dll en v2.4.** La solución al problema de fosilización (el mismo que mató a BERT) no era la obvia (re-enlazar dinámicamente en tiempo de compilación) — era dynamic loading en runtime con gestión explícita de handles. Decisión correcta.
- **Sysimage Julia (`neven_julia.dll`, ~415MB).** Eliminar el cold start de minutos es una decisión de producto con impacto UX significativo. La decisión de construirla y gestionarla como artefacto de producción fue del AI Engineer.

**Lo que baja ligeramente:** Algunas interfaces entre componentes no quedaron formalmente especificadas, lo que generó bugs recurrentes de contrato implícito. El emisor y el receptor asumen el formato — no hay contrato escrito. Esto no es un problema del AI (que no puede conocer lo que no se le especificó) — es un gap de diseño.

---

### Integración y despliegue del output — 7.0

Esta es la dimensión más operacional y donde se concentra la mayor cantidad de incidentes documentados en CHAT.md.

El AI genera código correcto en el repositorio (`F:\ANTIGRAVITY\2026\NEVEN\`). La integración en producción (`C:\NEVEN\`) es responsabilidad exclusiva del AI Engineer, y es donde ocurrieron los incidentes de mayor impacto:

| Incidente | Causa | Detectado |
|-----------|-------|-----------|
| BOM en `startup.r` | `WriteAllText` en lugar de `Copy` | Post-deploy, por síntomas en R |
| `startup.jl` con 80+ líneas nuevas sin sysimage | Deploy sin considerar impacto en cold start | Post-deploy, al medir tiempo |
| Sysimage Julia renombrada a `.bak` sin plan de reconstrucción | Decisión de deploy no reversible | Al intentar revertir |
| Package Manager con caché obsoleto (`packages-status-cache.json`) | Deploy sin limpiar caché previo | Post-deploy, por comportamiento incorrecto |
| `R_LIBS_USER` no heredado | Proceso hijo con entorno diferente | Post-deploy, por error en R |

Todos son errores de integración, no de código. El AI generó el código correcto. La integración falló en la capa que es 100% responsabilidad del AI Engineer.

La nota 7.0 es la más honesta del conjunto — no porque la integración sea mala en términos absolutos, sino porque es la dimensión que más directamente causa incidentes en producción y donde la mejora tiene el mayor retorno.

---

### Priorización y gestión del alcance — 8.5

El producto resultante tiene coherencia de producto que refleja buenas decisiones de alcance:

- **No implementar AppContainer** (alta complejidad, bajo retorno en el contexto actual) y priorizar las funciones econométricas del SRS — correcto dado el contexto de tesis.
- **Mantener v2.3 estable en producción** mientras v2.4 se desarrollaba en rama separada con tag de rollback — correcto.
- **Creador de Presentaciones como feature de valor alto** para el contexto universitario — correcto para la audiencia objetivo.
- **Package Manager como feature que reduce la fricción de instalación** — correcto para el ciclo de vida del proyecto post-tesis.
- **DataLab antes que el tab IA** — correcto porque el DataLab tiene más superficie de valor inmediato para el caso de uso de tesis.

Lo que baja ligeramente: algunos features se implementaron antes de estar completamente validados en el entorno real (PLUTO.READ con el problema de BOM en `startup.jl`, DataLab Julia sin prueba completa post-deploy), lo que generó deuda técnica de validación que tomó sesiones adicionales para resolver.

---

### Capacidad de formular problemas técnicos complejos — 9.0

Esta es una fortaleza clara y consistente a lo largo de todo el proyecto, y es quizás la habilidad más subvalorada del AI Engineering.

El AI puede resolver problemas bien formulados. Lo que el AI no puede hacer es tomar un síntoma vago ("no funciona") y convertirlo en un problema técnico preciso que tenga solución. Eso requiere comprensión del sistema, experiencia con los puntos de fallo, y capacidad de articulación técnica.

**Ejemplos concretos:**

- El diagnóstico del crash `0x11b111` se articuló como: "el crash ocurre en `R_ReadConsole`, específicamente en `GetOption1`, que accede a objetos SEXP antes de que el runtime de R esté completamente inicializado". Esa formulación convirtió un crash sin símbolo en una hipótesis verificable.
- El problema de `structRstart` con `rhome` en offset incorrecto se articuló como: "el layout del struct que usamos difiere del layout del struct en la versión de R que tenemos instalada — necesito leer el offset real". Eso convirtió un problema de ABI en un problema de diagnóstico binario.
- El problema de `_parse_slots_from_variable` se articuló eventualmente como: "hay dos formatos de respuesta de ControlR (directo y transpuesto) y el parser solo maneja uno". Esa formulación llevó directamente a la solución.

La nota 9.0 en lugar de 10 refleja que en algunos casos la formulación inicial del problema no era suficientemente precisa, lo que llevó al AI a generar soluciones para el problema equivocado antes de que se refinara la formulación.

---

## Comparación con el rol de Desarrollador Tradicional

| Dimensión | Desarrollador Tradicional | AI Development Engineer |
|:---|:---:|:---:|
| Dominio técnico del stack | 9.0 | 9.0* |
| Gestión del contexto del trabajo | 8.5 | 9.5 |
| Validación del output | 8.0 | 7.5 |
| Diagnóstico de errores | 8.0 | 8.0 |
| Diseño/Arquitectura | 7.5 | 8.5 |
| Integración y despliegue | — | 7.0 |
| Priorización de producto | 8.5 | 8.5 |
| Formulación de problemas | — | 9.0 |
| **Nota global** | **8.2** | **8.4** |

\* El dominio técnico no cambia de rol — es una propiedad de la persona, no del modelo de trabajo.

La diferencia neta de 0.2 puntos no cuenta la historia completa. Lo que cambió fue la distribución:

- **Diseño de sistemas subió** (7.5 → 8.5): cuando el AI ejecuta, el AI Engineer puede dedicar más ciclos cognitivos a pensar la arquitectura que a escribir el código.
- **Gestión del contexto subió** (8.5 → 9.5): el modelo de trabajo AI-asistido forzó una disciplina de documentación que como desarrollador solitario no había existido antes.
- **Validación bajó** (8.0 → 7.5): el AI acelera la producción de código más rápido de lo que el proceso de validación puede cubrir, lo que aumenta la superficie de error en integración.
- **Integración y despliegue es nueva como dimensión** (7.0): en el desarrollo tradicional, este paso existe pero es más simple. En el AI Engineering, el código se genera en el repositorio y la integración es un paso explícito y costoso.

---

## Nota contextual: lo que este modelo de trabajo logró

Antes de la nota final, vale nombrar explícitamente qué se construyó con este modelo de trabajo, porque el contexto es relevante para interpretar la evaluación:

**NEVEN v2.4** (del 1 de abril al 19 de agosto de 2026, ~4.5 meses):
- Migración de enlace estático a dynamic loading de R.dll (resolviendo el problema que hizo obsoleto a BERT en 2018)
- DataLab con 10 funciones gráficas y soporte para 20+ análisis estadísticos
- NEVEN Studio con HTTP server interno, taskpane embebida, y 5 tabs funcionales
- Package Manager con búsqueda, instalación, y gestión de paquetes R/Python/Julia desde Excel
- Creador de Presentaciones integrado con pipeline DataLab → Slide
- Funciones econométricas del SRS con 10 modelos de regresión
- 228 tests con GTest, cobertura de los componentes críticos de C++

Esto no lo construyó un equipo de 5 personas — lo construyó una persona dirigiendo un AI. La nota 8.4 es en ese contexto.

---

## Qué cambiaría para llegar a 9.5

La distancia entre 8.4 y 9.5 no es técnica — es de proceso operacional. Tres cambios concretos:

**1. Protocolo de integración como artefacto de primera clase**

Antes de cada deploy, ejecutar una checklist de escenarios de fallo conocidos derivados de la bitácora:
- ¿Encoding UTF-8 verificado? (`Format-Hex` en los primeros bytes del archivo)
- ¿Variables de entorno que necesita el proceso hijo definidas explícitamente?
- ¿Caché relevante invalidado antes del deploy?
- ¿El rollback está definido y probado antes del deploy, no después?

Esto no es trabajo adicional significativo — es sistematizar lo que ya se hace de forma ad hoc.

**2. Contrato de interfaz explícito antes de cada prompt al AI**

Para cualquier componente que comunica con otro, una línea antes del prompt: "el emisor produce X en formato Y; el receptor espera Z en formato W". Esto previene la clase de bugs más frecuente en NEVEN (contratos implícitos entre componentes) y acorta los ciclos de corrección de 3-4 iteraciones a 1.

**3. Validación adversarial del output del AI**

Después de que el AI genera una solución, añadir al prompt: "identifica los tres escenarios más probables en que este código falla en el entorno de producción de NEVEN (Windows, proceso hijo con PATH heredado diferente, encoding UTF-8 sin BOM)". Esto externaliza parte de la validación crítica al propio modelo y convierte el AI en revisor de su propio output antes del deploy.

Estos tres cambios moverían la nota global de 8.4 a ~9.2. El 9.5 requiere además consistencia temporal — que los procesos se apliquen incluso bajo presión de velocidad, que es donde todos los buenos procesos tienden a romperse.

---

*Evaluación generada con base en evidencia documental de CHAT.md, bitácora de sesiones de trabajo, y patrones observados durante el desarrollo conjunto de NEVEN v2.4 (abril–agosto 2026).*  
*Escala: 0–10. Objetividad sobre comodidad.*
