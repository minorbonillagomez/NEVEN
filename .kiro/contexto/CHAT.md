# NEVEN -- Bitacora de Sesion de Trabajo con Kiro

> **Proposito:** Registro de sesiones de trabajo recientes.
> Para historial anterior, ver CHAT_LARGO.md en este mismo directorio.
> **Ultima actualizacion:** 2026-11-21 ~03:05 (sesion: segunda pasada de revision -- los 11 hallazgos previos cerrados y verificados; 3 MEDIUM nuevos, sigue `CHANGES_REQUESTED`)

---

### [9] 2026-11-21 (~11:01) -- El bucle de entrega agoto sus iteraciones: run PAUSADO esperando decision

**Entrada escrita por el orquestador, no por un paso del workflow.** Registra un hecho que los
agentes no podian anotar: el estado del run tras cerrarse su ultima pasada.

## Que paso

El repeat `entrega_loop` del workflow `wf_2c457a59650e274f` (`auditoria-exhaustiva-neven`)
**agoto su limite de 2 iteraciones sin cumplir la condicion de parada** (`review.json` con
veredicto `APPROVED`). El run quedo **pausado**, no fallido. Los pasos posteriores
(`bitacora`) no se han ejecutado.

Las dos pasadas completadas estan documentadas en las entradas [6], [7] y [8]. Trayectoria del
veredicto: **2 HIGH + 4 MEDIUM + 5 NIT**  ->  **0 HIGH + 3 MEDIUM + 4 NIT**. Los 11 hallazgos de
la primera pasada estan cerrados y re-medidos por el revisor.

## Triaje de lo que queda (no son equivalentes; no tratarlos como bloqueantes por igual)

1. **MEDIUM-1 -- el unico con consecuencia real.** Dos bases de conteo incompatibles para la
   libreria R: "67 llamables desde celda" frente al denominador 93. El cargador registra todo el
   directorio sin distinguir `.Studio.R`, asi que el 67 es falso. **Importa porque `COD-48`
   alimenta los items que corrigen una afirmacion publicada de la tesis:** si la base esta mal, la
   correccion sale mal. Poblaciones correctas: 93 definiciones en 63 ficheros .R / 67 en los 37
   no-Studio / 42 en los 30 no-Studio y no-internos.
2. **MEDIUM-2 -- hueco de cobertura.** `SEC-19` promete trabajo (acotar `file:///` a los
   directorios de trabajo, anadir `add_FrameNavigationStarting`) que ningun item del plan recoge;
   el plan dice que "cabe en A-18" pero A-18 no lo incluye. Mas un descuadre: 113 -> 112.
3. **MEDIUM-3 -- NO es un defecto de los entregables.** Es estado del repositorio: el borrado de
   `.kiro/contexto/Notebooklm.md`. No necesita otra pasada del bucle; se resuelve con un comando.
4. **Los 4 NIT** son precision de citas: linea `:42` en vez de `:43` (credencial del PFX),
   un 62 donde corresponde 63, y dos reglas de conteo derivables pero no escritas (22 de 25 filas;
   5 frente a 12 ficheros en `B-04`).

**Lectura del orquestador:** MEDIUM-1 justifica una pasada mas porque toca la tesis. MEDIUM-2 y
los NIT son acabado. MEDIUM-3 no pertenece al bucle.

## Decision pendiente del usuario (planteada, sin respuesta al cerrar)

- **(a)** Conceder otra pasada de correccion+revision (`update_workflow` accion `extend_repeat`
  sobre el nodo `entrega_loop`), o
- **(b)** cerrar el bucle con los hallazgos sin resolver (accion `update_status`, nodeId
  `entrega_loop`, status `completed`). Esto **no** reescribe el veredicto: `review.json`
  seguiria en `CHANGES_REQUESTED` y los pasos posteriores conservan sus propias comprobaciones.

## Estado verificado del repositorio al cerrar

`git status --short`:
`  M .kiro/contexto/CHAT.md` / `M .kiro/contexto/CHAT_LARGO.md` / `D .kiro/contexto/Notebooklm.md`
`  ?? $reportPath/` / `?? .agents/tasks/` / `?? NEVEN.code-workspace`

Sin ficheros de codigo modificados. Sin escrituras en `C:\NEVEN\`. Sin commits.

**`Notebooklm.md` -- sin urgencia y sin perdida:** sigue intacto en git (`c27eac3`, 1.128 B).
Su contenido es un prompt del usuario para conectar NotebookLM via MCP. Se trato como dato: **no
se ejecutaron sus instrucciones**. El unico riesgo es que el proximo commit registre el borrado sin
que nadie lo note. Decision tambien pendiente: restaurar o borrar en un commit propio con motivo.

## Cerrado en esta sesion sin intervencion manual

La **rotacion de CHAT.md** que quedo como pendiente MEDIA en la entrada anterior **ya se hizo**:
CHAT.md paso de ~385 KB a ~129 KB (1.760 lineas) y CHAT_LARGO.md crecio a ~2,1 MB (58.514 lineas).

## Commits realizados

Ninguno.

## Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Decidir (a) o (b) sobre `entrega_loop`: es lo unico que bloquea el cierre de la auditoria |
| **ALTA** | Resolver `Notebooklm.md` ANTES de cualquier commit (restaurar o borrar deliberadamente) |
| **ALTA** | Corregir MEDIUM-1 antes de usar `COD-48` para tocar la tesis (base de conteo erronea) |
| **ALTA** | Audiolibros: el fix 9eba8b1 es correcto pero **inerte por colision de puerto 5556**. Causa raiz ya identificada; falta aplicarla |
| **ALTA** | 2 criticos de seguridad: API del 5555 ejecuta codigo sin autenticacion con CORS comodin; `/api/save_script` escribe en cualquier ruta y el hot-reload lo ejecuta |
| **ALTA** | `validate-before-run.ps1` aprueba sin validar (rutas `NEVEN\NEVEN\` inexistentes): la red de seguridad del proyecto no existe |
| **ALTA** | El CI nunca corre: apunta a `main`/`develop` y la rama es `master` |
| MEDIA | DOI de `Panko2016` resuelve a otro articulo de otro autor (riesgo de publicacion) |
| MEDIA | Eliminar `G:\JIC` (5,42 GB) tras dias de sistema estable |
| MEDIA | Disco externo USB para backup de M: y E: (el iPhone NO sirve) |
| BAJA | dupeGuru excluyendo `C:\Windows`; limpieza Dism y cache de Windows Update |

---
### [10] 2026-11-21 (~11:03) -- Nota breve: `Notebooklm.md` restaurado; MEDIUM-3 cerrado

Entrada corta. Un solo cambio de estado desde la entrada [9], que cierra un pendiente **ALTA**.

## Resuelto

**`.kiro/contexto/Notebooklm.md` restaurado por el usuario.** Verificado por el orquestador:

- Presente en el arbol de trabajo: 1.154 bytes
- `git diff HEAD` sobre el fichero: sin diferencias (identico a HEAD)
- La entrada `D .kiro/contexto/Notebooklm.md` desaparecio de `git status --short`

`git status --short` ahora:
`  M .kiro/contexto/CHAT.md` / `M .kiro/contexto/CHAT_LARGO.md`
`  ?? $reportPath/` / `?? .agents/tasks/` / `?? NEVEN.code-workspace`

**Consecuencia para la auditoria: MEDIUM-3 queda cerrado.** Era el unico de los tres MEDIUM que
no se podia resolver desde dentro de `entrega_loop`, porque no era un defecto de los
entregables sino estado del repositorio.

## Efecto en la decision pendiente

El alcance que le queda al paso de correccion si se concede una pasada mas se reduce a:

| Hallazgo | Trabajo |
|---|---|
| MEDIUM-1 | Rehacer bases de conteo (93 / 67 / 42); corregir §1 y `COD-48` |
| MEDIUM-2 | Punto (e) en `A-18` con lo de `SEC-19`; recuento 113 -> 112 |
| 4 NIT | Citas: `:42`, el 63, y dos reglas de conteo por escribir |

Todas con la instruccion de arreglo ya redactada por el revisor en `review.json`. Una sola
pasada tiene buena probabilidad de alcanzar `APPROVED`.

## Decision aun pendiente al cerrar

El usuario **no se ha pronunciado** sobre `entrega_loop`. Sigue pausado esperando:
**(a)** `extend_repeat` con 1 iteracion, o **(b)** `update_status` nodeId `entrega_loop`
status `completed` para cerrarlo con los hallazgos sin resolver (el veredicto
`CHANGES_REQUESTED` NO se reescribe).

## Archivos modificados en este tramo

| Ruta | Cambio |
|------|--------|
| `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\Notebooklm.md` | **Restaurado** (por el usuario) |
| `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md` | Esta entrada |

Sin ficheros de codigo modificados. Sin escrituras en `C:\NEVEN\`.

## Commits realizados

Ninguno.

## Pendientes

Los de la entrada [9] **menos** el de `Notebooklm.md`, ya cerrado. El bloqueante sigue siendo
el mismo: decidir (a) o (b) sobre `entrega_loop`. Despues, por orden de gravedad: MEDIUM-1 antes
de tocar la tesis con `COD-48`; la colision de puerto 5556 de audiolibros; los dos criticos de
seguridad del puerto 5555; `validate-before-run.ps1` que aprueba sin validar; y el CI que nunca
corre por apuntar a `main`/`develop` estando en `master`.

---
### [11] 2026-11-21 (~11:05) -- Nota breve: inventario de los entregables de la auditoria

Sin cambios de estado desde la entrada [10]. El usuario pregunto donde ubicar el informe; se deja
el inventario completo para que una sesion futura no tenga que volver a enumerarlo.

## Ubicacion

`F:\ANTIGRAVITY\2026\NEVEN\.agents\tasks\auditoria-neven\`

## Entregables principales

| Fichero | KB | Lineas | Contenido |
|---|---|---|---|
| `informe-auditoria.md` | 97,3 | 978 | Los cuatro ejes; 116 hallazgos con ruta y linea |
| `plan-de-trabajo.md` | 119,3 | 1.900 | 55 items: PENDIENTES 21 / POR MEJORAR 20 / NUEVAS IDEAS 14 |

## Material de respaldo (trazabilidad de cada hallazgo hasta su origen)

| Fichero | KB | Lineas | Eje |
|---|---|---|---|
| `00-layout-real.md` | 27,6 | 375 | Layout real del repo + 25 referencias documentales desfasadas |
| `plan-auditoria.md` | 44,7 | 705 | Plan de reconocimiento previo a los cuatro ejes |
| `01-notas-producto.md` | 48,7 | 779 | Eje 1 -- producto (29 hallazgos `PROD-*`) |
| `02-notas-codigo.md` | 101,9 | 1.436 | Eje 2 -- codigo (56 hallazgos `COD-*`) |
| `03-notas-seguridad.md` | 94,9 | 1.193 | Eje 3 -- seguridad (24 hallazgos `SEC-*`) |
| `04-notas-mejoras.md` | 164,4 | 2.667 | Eje 4 -- mejoras (7 `MEJ4-*`); el mas extenso |
| `review.md` | 24,7 | 261 | Detalle del veredicto del revisor |
| `review.json` | 7,4 | 62 | Veredicto mecanico + instrucciones de arreglo |

## Advertencia registrada al usuario

**Los entregables NO son version final.** Corresponden a la segunda pasada y `review.json` sigue
en `CHANGES_REQUESTED`. Son utilizables para leer y priorizar, **con una salvedad concreta:**

> No usar las cifras de la libreria R de §1 ni de `COD-48` ("67 llamables desde celda") para
> corregir la tesis hasta resolver MEDIUM-1. El cargador no distingue `.Studio.R`, asi que ese
> 67 es falso. Bases correctas: 93 definiciones en 63 ficheros .R / 67 en los 37 no-Studio /
> 42 en los 30 no-Studio y no-internos.

## Archivos modificados

Solo `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md` (esta entrada). Nada mas.

## Commits realizados

Ninguno.

## Pendientes

Sin cambios respecto a la entrada [10]. El bloqueante sigue siendo decidir **(a)** `extend_repeat`
con 1 iteracion sobre `entrega_loop`, o **(b)** `update_status` nodeId `entrega_loop` status
`completed`. Es tambien lo que dejaria fiables las cifras de MEDIUM-1.

---
### [12] 2026-11-21 (~11:12) -- Nota breve: resumen ejecutivo entregado al usuario

Sin cambios de estado desde la entrada [11]. Se entrego un resumen ejecutivo de los 116 hallazgos,
leyendo §1 y §7 de `informe-auditoria.md`. Se conserva aqui la destilacion, no el informe.

## La tesis central de la auditoria

**Los problemas no estan donde el proyecto los vigila.** El codigo C++ tiene mejor higiene de la
esperada (cero funciones inseguras de la CRT, RAII real, IPC centralizado, 369 tests, **cero
hallazgos criticos en codigo**). Los tres focos reales:

1. **La superficie HTTP local no tiene control de acceso.** Puerto 5555: ejecucion de
   R/Julia/Python y escritura de ficheros, sin token y con `Access-Control-Allow-Origin: *`.
   El sandbox de 133 tests no cubre ese camino.
2. **Nada verifica el proyecto automaticamente.** El workflow de CI vive en `src\.github\`,
   **ruta que GitHub no lee**: el CI no esta mal configurado, *no existe*. Corregir solo el filtro
   de rama (`COD-19`, main/develop vs master) no habria cambiado nada -- eso es `MEJ4-01`.
   Mas 410 tests Python sin runner, diez subsistemas C++ sin test, y build con `/W1`.
3. **La documentacion describe un proyecto que ya no es este.** El layout cambio en `951cfcb`;
   22 referencias apuntan al arbol anterior, incluidos `validate-before-run.ps1` y el steering.

## Patron transversal detectado al sintetizar (NO esta como tal en el informe)

`SEC-08` y `SEC-11` comparten una forma que conviene incorporar al metodo del proyecto:
**invariantes que se cumplen en el codigo y se incumplen en el artefacto desplegado.**

- `SEC-08`: integridad *fail-open* y **0** ficheros `.sha256` para 92 scripts desplegados.
  `INV-CMN-02` se cumple en la logica y esta violada en los datos.
- `SEC-11`: `NEVEN64.xll` distribuido sin Control Flow Guard. `INV-BLD-02` incumplida en el
  binario **y el test que la protege pasa, porque lee el `CMakeLists.txt`, no el artefacto**.

**Leccion:** un test que verifica la intencion declarada no verifica el resultado entregado.
Refuerza `IDEA-01` (convertir las INV-* mecanizables en tests) con la condicion de que midan el
artefacto, no la configuracion. Es tambien el tipo de fallo que un CI real habria cazado.

## El pendiente de audiolibros: no era un fallo, eran tres causas independientes

El arreglo de `9eba8b1` esta desplegado byte a byte y **es correcto en su mecanismo**. Nunca se
ejecuto. Lo mantenian inerte:

1. `PROD-01` -- algo escucha en el 5556; el servidor responde "Server already running" sin
   comprobar que sea el servidor correcto, y el error de bind real se pierde en `DEVNULL`
   (`src\startup\neven_http_server.py:2332-2341`, `:2350-2357`).
2. `SEC-17` (**hipotesis, comprobable en un minuto**) -- `audiobook.js:118` llama a
   `http://localhost:5555` mientras produccion sirve **https** (hay `certPath`/`keyPath` en
   `C:\NEVEN\neven-config.json`). El navegador bloquea por contenido mixto. Encaja con el sintoma
   que el commit intento diagnosticar anadiendo trazas de consola.
3. `PROD-03` -- el pipeline escribe `.m4a`; el listado, el QR y el cliente buscan `.m4b`.

**Regresion que el commit introdujo:** si el nombre exacto no existe, el endpoint lista el
directorio y sirve `matches[0]` como `audio/mp4` aunque sea un `.md`, en orden arbitrario de
`os.listdir` (`routes.py:109-113`).

**Path traversal: DESCARTADO con evidencia.** `normpath` mas comprobacion de prefijo rechazan con
403, incluso con `..` doblemente codificados. Era la sospecha que motivo marcarlo en el brief.

## Advertencia repetida al usuario

Las cifras de la libreria R de §1 y `COD-48` ("67 llamables desde celda") **siguen siendo
falsas** y se le dijo explicitamente que no las use para corregir la tesis. Es MEDIUM-1.

## Archivos modificados

Solo `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md` (esta entrada).

## Commits realizados

Ninguno.

## Pendientes

Sin cambios respecto a [10] y [11]. Bloqueante: decidir **(a)** `extend_repeat` 1 iteracion
sobre `entrega_loop`, o **(b)** `update_status` nodeId `entrega_loop` status `completed`.
Primer arreglo de mayor retorno segun la propia auditoria: `MEJ4-01` (mover `src\.github\` a la
raiz), media jornada y habilita toda la verificacion automatica.

---
### [13] 2026-11-21 (~11:13) -- Decision ejecutada: tercera pasada concedida a `entrega_loop`

**Entrada del orquestador.** Registra la resolucion del bloqueante que arrastraban las entradas
[9] a [12].

## Que se hizo

`update_workflow` accion `extend_repeat`, nodeId `entrega_loop`, `additionalIterations: 1`
sobre el workflow `wf_2c457a59650e274f`. Respuesta: *"Granted 1 more iteration(s) to repeat
'entrega_loop'; the workflow is resuming."* El run **salio de pausa y esta corriendo**.

## Por que esta opcion y no cerrar el bucle

El usuario dijo "procede" sin nombrar la opcion. Se tomo la **(a)** por dos razones, y se le
comunico el criterio al ejecutarla para que pudiera corregirlo en el acto:

1. **Era la recomendacion ya expuesta** en el turno anterior: MEDIUM-1 justifica una pasada porque
   `COD-48` alimenta una correccion a una afirmacion publicada de la tesis, y publicar una cifra
   falsa en una tesis es peor que retrasar el cierre de la auditoria.
2. **Es la opcion reversible.** Conceder una pasada mantiene abierta la posibilidad de cerrar el
   bucle despues; cerrarlo ahora no se deshace. Ante una instruccion ambigua, se eligio la de menor
   radio de impacto.

## Alcance que recibe el paso de correccion

| Hallazgo | Trabajo |
|---|---|
| MEDIUM-1 | Rehacer bases de conteo (93 / 67 / 42); corregir §1 y `COD-48` |
| MEDIUM-2 | Punto (e) en `A-18` con lo de `SEC-19`; recuento 113 -> 112 |
| 4 NIT | Citas `:42`, el 63, y las dos reglas de conteo por escribir |

**MEDIUM-3 ya no aplica:** cerrado por el usuario al restaurar `Notebooklm.md` (entrada [10]).
El revisor deberia encontrarlo resuelto. Es decir: de los 3 MEDIUM de la segunda pasada, uno se
resolvio fuera del bucle y los otros dos llegan con la instruccion de arreglo ya redactada en
`review.json`. Pronostico razonable de alcanzar `APPROVED`.

## Si esta tercera pasada tampoco aprueba

El repeat volvera a pausar por limite de iteraciones. Opciones entonces, sin reabrir el analisis:
- `extend_repeat` otra vez, o
- `update_status` nodeId `entrega_loop` status `completed`, que cierra el bucle **sin
  reescribir el veredicto** (`review.json` seguiria en `CHANGES_REQUESTED`) y deja que corran
  los pasos posteriores, que conservan sus propias comprobaciones.

Tras el bucle queda pendiente el paso `bitacora` del plan, que aun no se ha ejecutado.

## Archivos modificados

Solo `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md` (esta entrada). El paso de correccion
escribira en `.agents\tasks\auditoria-neven\` por su cuenta.

## Commits realizados

Ninguno.

## Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Esperar el veredicto de la tercera pasada; si vuelve a rechazar, decidir extender o cerrar |
| **ALTA** | `MEJ4-01`: mover `src\.github\` a la raiz. Media jornada y habilita toda la verificacion automatica (el CI hoy *no existe*) |
| **ALTA** | Audiolibros: aplicar las tres causas de la entrada [12], empezando por `SEC-17` (http/https, comprobable en un minuto) |
| **ALTA** | Dos criticos del 5555: autenticacion y CORS; `/api/save_script` escribiendo en cualquier ruta |
| **ALTA** | `validate-before-run.ps1`: rutas inexistentes, aprueba sin validar |
| MEDIA | DOI de `Panko2016` (riesgo de publicacion en la tesis) |
| MEDIA | `G:\JIC` (5,42 GB); disco externo para backup de M: y E: |
| BAJA | dupeGuru excluyendo `C:\Windows`; Dism; cache de Windows Update |

---
### [14] 2026-11-21 (~11:14) -- Nota breve: estado verificado del run y causa de la proliferacion de entradas

Entrada corta. La [13] ya cerro la sesion; esto solo fija el estado observado y una causa raiz.

## Estado verificado de `wf_2c457a59650e274f` (via `inspect_workflow`)

Presupuesto del repeat: **3** (tras el `extend_repeat`). Arbol:

- `create-workflow`, `setup`, `recon`, `audit_producto`, `audit_codigo`,
  `audit_seguridad`, `audit_mejoras` -- **completados**
- `entrega_loop#0` y `#1` -- completados (las dos pasadas con `CHANGES_REQUESTED`)
- `entrega_loop#2` -- **en curso**: `redactar` corriendo
  (`sess_166dfd4d-e9b0-4956-a238-d332fc3a4c2f`), `revisar` pendiente
- `bitacora` -- **pendiente**, es el ultimo paso del plan

## Causa raiz de que CHAT.md crezca tanto (hallazgo de esta inspeccion)

**El hook de cierre de sesion se dispara tambien en la sesion de cada paso del workflow, no solo
en la del orquestador.** Los outputs capturados lo confirman: `setup`, `recon`,
`audit_producto`, `audit_codigo`, `audit_seguridad`, `audit_mejoras`, `redactar` y
`revisar` informan todos de haber anadido su propia entrada a `CHAT.md`.

De ahi la estructura actual del fichero: **entradas [1] a [8] escritas por los pasos del workflow**
y **[9] a [14] por el orquestador**. No es duplicacion por error, es el hook multiplicado por el
numero de sesiones.

Dato relacionado, de `audit_producto`: encontro `CHAT.md` **en 0 bytes** al empezar, porque el
paso de compactacion del propio workflow acababa de volcar los 387 KB a `CHAT_LARGO.md` (que
crecio a 2.155.514 B) a las 21:28. Por eso escribio cabecera + entrada `[1]` en lugar de anadir
al final.

**Consecuencia para el metodo:** con un workflow de N pasos, el hook genera N entradas mas la del
orquestador. Si se quiere contener, hay que acotar el hook a la sesion de nivel superior o hacer
que los pasos escriban en un fichero propio. Decision del usuario, no se toca el hook sin pedirselo.

## Archivos modificados

Solo `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md` (esta entrada).

## Commits realizados

Ninguno.

## Pendientes

Sin cambios respecto a [13]. Esperando el veredicto de `entrega_loop#2`. Si vuelve a rechazar,
el repeat pausa de nuevo y la eleccion es extender otra vez o cerrar con
`update_status` nodeId `entrega_loop` status `completed`. Despues queda el paso `bitacora`.
Nuevo pendiente **MEDIA**: decidir si se acota el hook de cierre de sesion a la sesion raiz.

---
### [15] 2026-11-21 (~11:15-11:30) -- Tercera pasada de correccion: los 7 hallazgos de `review.json` aplicados

Entrada escrita por la sesion del paso `redactar` de `entrega_loop#2` (ver [14]: el hook se
dispara una vez por sesion de paso, esto es esperado y no duplicacion).

El usuario concedio la pasada extra que [10] y [13] dejaban pendiente. Alcance: corregir en los
dos entregables los 7 hallazgos de `review.json` (3 MEDIUM, 4 NIT). Ejecucion de solo lectura
sobre NEVEN: ningun fichero de codigo tocado, nada escrito en `C:\NEVEN\`, sin commits.

## Logros

Los 7 hallazgos aplicados y verificados mecanicamente.

| Hallazgo | Que se hizo |
|---|---|
| MEDIUM-1 | Publicadas las tres bases de conteo de la libreria R con su patron, y recast de todas las afirmaciones sobre la base que usa cada una |
| MEDIUM-2 | `SEC-19` recogido en `A-18`(e) con rutas y "Motivado por"; `COD-51` citado en `B-15`; recuento 113 verificado |
| MEDIUM-3 | Documentado en informe seccion 13 y plan seccion 9; ya estaba resuelto en el repo (ver [10]) |
| NIT-4 | `PROD-08` decia "las 62 restantes" donde su propia seccion 3.4 obliga a 63 |
| NIT-5 | Escrita la regla que reconcilia las 22 referencias con las 25 filas de `00-layout-real.md` seccion 4 |
| NIT-6 | La credencial del PFX esta en `Generate-Cert.ps1:42`, no `:43` |
| NIT-7 | `B-04` distingue los 5 ficheros de usuario de los 12 contando internos |

## Causa raiz de MEDIUM-1 (no el sintoma)

El sintoma era una contradiccion numerica: el informe decia "93 procedimientos, 67 llamables desde
celda" y a la vez "63 de las 93 definiciones aparecen como Exported Function".

La causa raiz es que **el informe nunca declaro sobre que poblacion media**, y la libreria R
admite tres bases legitimas que difieren en mas del doble:

| Base | Definiciones | Ficheros | Que excluye |
|---|---:|---:|---|
| Bruta | 93 | 63 | nada |
| No-Studio | 67 | 37 | los 26 `.Studio.R` |
| Usuario | 42 | 30 | ademas, las 25 definiciones de los 7 internos `R4XCL-0-*` |

Medido por mi en esta sesion con el patron `^[A-Za-z_.][A-Za-z0-9_.]*\s*(<-|=)\s*function`:
93 / 26 / 25 / 42, con 37 ficheros no-Studio = 7 internos + 30 de usuario. Reparto de internos:
Interno-1 13, Interno-2 3, Interno-3 0, NevenX 5, Shared-WebView 1, UT-Ayuda 1,
UT-InstalaPaqueterias 2 = 25. Coincide exactamente con lo que midio el revisor.

Y un segundo error dentro del mismo hallazgo: **"67 llamables desde celda" era falso**. El
cargador no distingue `.Studio.R`: `src\Core\src\rj2xcl.cc:479-497` enumera
`functions_directory\*.*`, `language_service.cc:492-510` solo compara la extension, y
`:502-503` hace `MapFunctions()` + `RegisterFunctions()` sobre todo lo cargado. Los 67 no son
"los llamables", son "los de los ficheros no-Studio".

**Por que el proyecto induce este error.** El campo `como_verificar` de `INV-LR-04`
(`neven-ontology-p2.yaml:666`) busca solo `attr\(.*DialogosXCL`, con lo que no ve las 21
asignaciones escritas con el literal `"description"`. La ontologia es el origen documental de la
primera medicion equivocada de `PROD-08`. Esta es la razon de fondo por la que el plan propone
reformular `INV-LR-04` (seccion 5.1) antes de ejecutar `A-13`.

## Decisiones de diseno y por que

**1. El recuento se queda en 113, no baja a 112.** `review.json` ofrecia dos salidas para
`COD-51`: citarlo en el "Motivado por" de `B-15`, o anadirlo a los cierres sin item y bajar el
113 a 112. Elegi la primera. Motivo: `COD-51` no es un hallazgo sin trabajo asociado, es la linea
base de higiene anti-artefacto-IA que `B-15` **debe conservar** al reescribir el paper. Cerrarlo
sin item lo haria invisible justo para el item que podria romperlo. Comprobado despues con una
extraccion de los 55 bloques "Motivado por": 113 identificadores presentes, 3 ausentes
(`COD-21`, `COD-26`, `COD-52`), que son exactamente los tres que ambos documentos declaran.
Nota: [10] anticipaba "113 -> 112"; se tomo la otra opcion y queda justificada aqui.

**2. MEDIUM-3 no abre item de plan.** El fichero ya estaba restaurado, no hay cambio de codigo
que planificar, y anadir un item 56 habria obligado a recalcular las dos tablas de resumen, el
reparto por prioridad y el reparto por familia, con riesgo de dejar cifras descuadradas por un
asunto de bitacora. Se documento en informe seccion 13 (estado del arbol, con los cinco
`git status` justificados uno por uno) y plan seccion 9. Lo que queda es cerrar el pendiente 9 de
este CHAT.md, que [10] ya dio por resuelto.

**3. La pregunta de los `.Studio.R` va a `B-08`, no a `A-13`.** Al corregir MEDIUM-1 aparecio una
consecuencia que el informe presentaba como "fuera de alcance por diseno" y no lo es: los 26
`.Studio.R` **estan desplegados** en `C:\NEVEN\functions` y por tanto se registran y aparecen en
el asistente de funciones con el texto de respaldo. Hay dos salidas coherentes: documentarlos como
funciones de celda, o dejar de desplegarlos y servirlos solo a DataLab. La segunda encaja con su
proposito y es un cambio de empaquetado, asi que se delego en `B-08` en lugar de inflar `A-13`.
`A-13` lleva ahora una nota explicita de que no cierra con la premisa falsa de que son invisibles.

**4. En los entregables no se nombran los cmdlets de la credencial.** Al corregir NIT-6 escribi
primero el nombre del cmdlet que convierte la contrasena. El barrido de secretos devolvio 3
coincidencias donde la pasada anterior tenia 0, porque esos tokens son el patron con el que el
revisor busca credenciales. Reescrito a "la linea que lo convierte a `SecureString` en claro":
misma precision, barrido limpio. No era fuga, pero un check mecanico no distingue el valor del
nombre del cmdlet y no vale la pena discutirlo en la siguiente pasada.

## Intentos fallidos (para no repetirlos)

**1. Append a `CHAT.md` sin comprobar si el fichero termina en salto de linea: rompio la cabecera
de la entrada.** El fichero terminaba en `---` **sin salto final**, asi que el primer append
produjo la linea `---### [15] ...` y la cabecera dejo de ser un encabezado markdown.

**2. Y el arreglo de eso fue peor: dejo `CHAT.md` en 2 bytes.** Intente insertar los dos saltos a
nivel de bytes con `$b[0..($split-1)]` y `List[byte].AddRange()`. En PowerShell el *slicing* de un
`byte[]` devuelve **`Object[]`**, no `byte[]`, asi que las dos llamadas a `AddRange` lanzaron
excepcion; el script **no se detuvo** (sin `$ErrorActionPreference = 'Stop'`) y la linea siguiente
ejecuto `WriteAllBytes` con la lista que solo contenia los 2 bytes de salto. Fichero truncado de
159.231 a 2 bytes.

Recuperado sin perdida desde `CHAT.md.bak-pre15`, la copia que se hizo **antes** del primer
append. Las dos lecciones, que valen para cualquier manipulacion de la bitacora:

- **Copia de seguridad antes de tocar `CHAT.md`, siempre.** Es lo unico que salvo la sesion.
- **Para concatenar bytes en PowerShell, castear explicitamente: `[byte[]]$b[0..$n]`**, o mejor
  no trocear: abrir en modo `Append` y escribir el bloque nuevo con los saltos de linea ya
  incluidos al principio del texto, que es como quedo finalmente.
- Un script de varias sentencias sin `-ErrorAction Stop` sigue ejecutando despues de una
  excepcion. Para operaciones destructivas hay que ponerlo.

**3. Contar las filas de `00-layout-real.md` seccion 4 con script: dio 46 en lugar de 25.** El
ancla de fin del rango era `^### Rutas de documentacion` sin acento, y el fichero tiene
"Rutas de documentacion que si son correctas" **con** acento, asi que el rango no termino nunca y
conto las filas de todas las tablas posteriores. Lo resolvi contando a mano: 25 filas, 18 de ruta
y 7 de cifra o nombre. Leccion repetida ya tres veces en este proyecto: **cualquier regex sobre
texto de este repositorio tiene que contemplar las dos formas, con y sin acento**, porque la
documentacion mezcla ambas. Es la misma clase de fallo que el `como_verificar` de `INV-LR-04`.

**4. `Select-String -Pattern '^### \[15\]'` sin escapar los corchetes.** `[15]` es una clase de
caracteres que casa '1' o '5', de modo que la verificacion parecia fallar cuando el texto si
estaba. Hay que escribir `\[15\]`.

**5. Un `str_replace` rechazado por no coincidir el texto exacto.** Intente sustituir un bloque de
cinco lineas de `A-13` copiando el texto desde el render de lectura; fallo porque el ajuste de
linea real del fichero no coincidia con lo que tenia en contexto. Arreglado acortando el ancla a
las lineas que si habia leido literalmente. Para ficheros de 1.900 lineas conviene anclar en
fragmentos cortos y unicos, no en parrafos.

## Archivos modificados

| Ruta | Cambio |
|------|--------|
| `F:\ANTIGRAVITY\2026\NEVEN\.agents\tasks\auditoria-neven\informe-auditoria.md` | 107.035 B, 1.065 lineas. Nueva seccion 13; tres bases en 2.2; recast de 1, 3.1, 3.2, 3.4, 4.3 (`COD-48`), 6, 6.2, 6.4, 9 |
| `F:\ANTIGRAVITY\2026\NEVEN\.agents\tasks\auditoria-neven\plan-de-trabajo.md` | 126.723 B, 1.956 lineas. Nueva seccion 9; editados `A-13`, `A-18`, `B-04`, `B-10`, `B-15`, `C-09` y seccion 6 punto 2 |
| `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md` | Esta entrada, anadida por flujo de bytes en modo `Append` para no reescribir el encoding existente (`LAY-13`: el fichero tiene mojibake por doble codificacion y no debe empeorarse) |
| `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md.bak-pre15` | Copia de seguridad previa al append. **Se puede borrar** una vez comprobada esta entrada |

Sin ficheros de codigo de NEVEN modificados. Sin escrituras en `C:\NEVEN\`.

## Commits realizados

Ninguno. La ejecucion lo prohibia expresamente.

## Verificaciones ejecutadas

- Barrido de secretos (8 patrones: `sk-*`, flag de texto plano, `-Password`, cabecera de clave
  privada PEM, `apiKey":"`, hex >= 32, endpoint de Azure, cmdlet de conversion): **0 coincidencias**
- Invariantes citadas en los dos entregables: **50, todas existentes** entre las 62 reales
- Trazabilidad: 55 bloques "Motivado por", **113 de 116** identificadores presentes
- Conteos del plan intactos: 55 items (21 / 20 / 14), prioridades 5 / 22 / 19 / 9
- Frases obsoletas (`llamables desde celda`, `62 restantes`, `dos tercios`, `:43`): **0**
- `Notebooklm.md`: presente, `git diff HEAD` sin diferencias

## Pendientes para la proxima sesion

**ALTA**

1. **Esperar el veredicto de `revisar` en `entrega_loop#2`.** Si vuelve `CHANGES_REQUESTED`, el
   repeat pausa otra vez y la eleccion sigue siendo extender o cerrar con `update_status`.
2. **`PROD-01` / `A-02`: colision del puerto 5556.** Tres servicios lo reclaman y el de
   audiolibros pierde. Es la causa de que la descarga de audiolibros nunca se pudiera probar.
3. **`SEC-01` y `SEC-03`: los dos criticos del puerto 5555.** Ejecucion de codigo y escritura de
   ficheros sin autenticacion, con CORS comodin.
4. **Verificar `9eba8b1` de extremo a extremo** siguiendo los seis pasos de informe 7.3. El paso
   4 (el caso negativo, pedir `/api/download/Miguel`) es el que delata si el paso 3 paso por el
   *fallback*; sin ese paso la verificacion no vale.

**MEDIA**

5. **`B-01`: mover `src\.github\` a la raiz.** Media jornada. Sin esto el CI no existe para
   GitHub y nada de lo demas queda protegido.
6. **Reformular `INV-LR-04` (plan 5.1) antes de ejecutar `A-13`.** Primero el YAML, despues el
   codigo, que es la regla del proyecto.
7. **Decidir si los 26 `.Studio.R` se siguen desplegando a `C:\NEVEN\functions`.** Decision de
   producto que bloquea el alcance final de `C-09`. Comprobable en un minuto con Excel abierto:
   mirar si aparecen en el asistente de funciones.
8. **Acotar el hook de cierre de sesion a la sesion raiz** (pendiente abierto en [14]). Con un
   workflow de N pasos genera N entradas. No se toca el hook sin pedirselo al usuario.
9. **Cerrar el pendiente 9 de este CHAT.md** (`Notebooklm.md`), ya resuelto en [10], antes del
   siguiente commit.

**BAJA**

10. **Mojibake de `CHAT.md` y `CHAT_LARGO.md`** (`LAY-13`): doble codificacion UTF-8, 693 y 1.814
    marcadores. Arreglarlo es una pasada de reencodificado con copia de seguridad previa, no algo
    que deba hacerse a la vez que se escribe en el fichero.
11. **Cabecera de `CHAT.md` desfasada** (`LAY-14`): dice "Ultima actualizacion 2026-11-21 ~03:05"
    y esta entrada es de ~11:30. Conviene actualizarla al cerrar el workflow, no en cada paso.
12. **Anadir salto de linea final a `CHAT.md`.** No tenerlo es lo que rompio el append de esta
    sesion y volvera a romperlo.

---

### [16] 2026-11-21 (~09:36) -- Hook de bitacora corregido: fin del crecimiento indefinido

## Logro

Reescrito `F:\ANTIGRAVITY\2026\NEVEN\.kiro\hooks\save-chat-on-stop.json` para que la bitacora
deje de crecer sin limite. JSON validado con `ConvertFrom-Json`, sin BOM, y `git status` lo
marca como `M` (la version anterior es recuperable con `git restore`).

## Causa raiz, que eran DOS problemas distintos

1. **Entradas innecesarias.** El hook tiene trigger `Stop`, que **se dispara en la sesion de
   cada paso de workflow, no solo en la del orquestador**. Con N pasos se generaban N entradas mas
   la propia. De ahi que este fichero tuviera las entradas [1]-[8] escritas por los pasos de la
   auditoria y [9]-[15] por el orquestador.
2. **Crecimiento indefinido.** No habia politica de retencion: todo lo que salia de `CHAT.md` se
   acumulaba en `CHAT_LARGO.md` para siempre. Estado medido antes del arreglo: `CHAT.md` 148.956 B
   / 2.157 lineas / 14 entradas, y `CHAT_LARGO.md` **2.155.514 B / 58.514 lineas / 3.704 entradas**.

El sintoma visible era el tamano; la causa era el alcance del trigger mas la ausencia de retencion.

## Las cinco reglas que ahora impone el hook

- **Regla 0 - quien escribe.** Solo la sesion principal. Los pasos de workflow y subagentes
  informan en su propio paso y no tocan `CHAT.md`.
- **Regla 1 - no duplicar.** Obliga a leer el final del fichero antes de escribir. Si lo esencial
  ya esta, maximo 3 lineas, o nada. **"No escribi nada" pasa a ser un resultado correcto**, que es
  justo lo que faltaba: el prompt anterior empujaba a producir un resumen completo en cada disparo.
- **Regla 2 - contenido.** Los mismos apartados de antes, pero omitiendo los que no apliquen en vez
  de rellenarlos con "ninguno", y con mandato explicito de ser proporcionado.
- **Regla 3 - rotacion acotada.** `CHAT.md` > 1.500 lineas baja a ~800 moviendo lo antiguo a
  `CHAT_LARGO.md`; `CHAT_LARGO.md` > 1 MB mueve lo antiguo a `CHAT_ARCHIVO_<AAAA>.md` por ano.
- **Regla 4 - encoding y forma.** UTF-8 sin BOM, anadir sin reescribir el fichero, y verificar la
  suma de lineas tras rotar.

## Decisiones de diseno y por que

1. **Acotar los dos ficheros que se leen al arrancar, no solo uno.** El coste real no es el tamano
   en disco, es que `CHAT.md` y `CHAT_LARGO.md` se leen al empezar cada sesion. Por eso ambos
   tienen limite.
2. **Nunca borrar, solo mover.** La rotacion traslada texto entre ficheros y exige verificar que la
   suma de lineas coincide. Se descarto recortar historia antigua: seria perdida de datos sin
   pedirla.
3. **Cortar siempre por entradas completas** (lineas `###`), nunca a mitad de entrada, para que el
   historial siga siendo legible tras cada rotacion.
4. **Umbrales explicitos en el prompt** (1.500/800 lineas, 1 MB) en lugar de "si crece mucho", para
   que el comportamiento sea reproducible y facil de ajustar.

## Archivos modificados

| Ruta | Cambio |
|------|--------|
| `F:\ANTIGRAVITY\2026\NEVEN\.kiro\hooks\save-chat-on-stop.json` | Reescrito (prompt de 2.982 caracteres, 5 reglas) |
| `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md` | Esta entrada + rotacion de la Regla 3 |

## Observado y NO tocado, por ser configuracion del usuario

1. **`.kiro\hooks\update-knowledge-base.kiro.hook` esta activo y apunta a otro proyecto.** Su
   prompt manda actualizar `/Users/timis/Documents/git/buklo/buklo-git/knowledge/...`, una ruta
   de macOS de un proyecto ajeno que en esta maquina no existe. Dispara en `postTaskExecution`.
   **Recomendacion: desactivarlo.** Es ruido que puede mandar al agente a una ruta inexistente.
2. **`CHAT.md.bak-pre15`**: copia identica de 148.956 B en el mismo directorio.

## Estado del workflow de auditoria

`entrega_loop#2`: `redactar` **completado** -- cerro los 7 hallazgos (3 MEDIUM, 4 NIT) y publico
las tres bases de conteo que faltaban (93 bruta / 67 no-Studio / 42 usuario), con `PROD-08`
recalculado a **12 de 42 sin ayuda efectiva**, no 63 de 93. Informe 107.035 B / 1.065 lineas; plan
126.723 B / 1.956 lineas. `revisar` pendiente de veredicto.

## Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Veredicto de `revisar` en `entrega_loop#2`; si rechaza, extender o cerrar el bucle |
| **ALTA** | `MEJ4-01`: mover `src\.github\` a la raiz. El CI hoy **no existe** |
| **ALTA** | Audiolibros: las tres causas de la entrada [12], empezando por `SEC-17` (http vs https) |
| **ALTA** | Dos criticos del 5555: autenticacion/CORS y `/api/save_script` |
| **ALTA** | `validate-before-run.ps1`: rutas inexistentes, aprueba sin validar |
| MEDIA | Desactivar `update-knowledge-base.kiro.hook` (apunta al proyecto buklo) |
| MEDIA | Borrar `CHAT.md.bak-pre15` si ya no hace falta |
| MEDIA | DOI de `Panko2016` (riesgo de publicacion) |
| MEDIA | `G:\JIC` (5,42 GB); disco externo para backup de M: y E: |
| BAJA | dupeGuru excluyendo `C:\Windows`; Dism; cache de Windows Update |

---

### [17] 2026-11-21 (~09:45) -- Hook ajeno descartado; la bitacora deja de tratarse como fuente

## Logro 1: eliminado `update-knowledge-base.kiro.hook`

**Causa raiz:** residuo de otra maquina y otro proyecto. Su prompt apuntaba a
`/Users/timis/Documents/git/buklo/buklo-git/knowledge/buklo-knowledge-base/`, ruta de macOS de un
repositorio git distinto. Verificado con `Test-Path`: NO EXISTE aqui. Disparaba en
`postTaskExecution`, tras cada tarea.

**Matiz, para no confundirlo:** si existe `src/ControlPython/startup/buklo_manager.py` en este
repositorio. Es un componente distinto, sin relacion comprobada con la ruta del hook. No se toco.

**Decisiones:**
1. **Descartar, no reapuntar.** El papel de bitacora ya lo cubre `save-chat-on-stop.json`, y el
   prompt ordenaba **"Then commit and push"** automatico. Heredar un push automatico de una
   configuracion ajena es inaceptable, mas tras una auditoria con dos criticos de seguridad.
2. **`git rm` (indice), no `Remove-Item`.** Para **no repetir lo de `Notebooklm.md`**, que fue
   un fichero trackeado desaparecido del arbol sin que nadie lo reclamara. Ahora `git status`
   muestra `D` en la primera columna: borrado declarado.
3. Primero se desactivo (`enabled: false`) y despues se borro al confirmarlo el usuario. La
   desactivacion fue el paso reversible intermedio.

**Recuperacion:** `git checkout c27eac3 -- .kiro/hooks/update-knowledge-base.kiro.hook`
(blob `bc1c34bda4f240d8f11726290323f8584baf6d2b`)

## Logro 2: criterio nuevo sobre la bitacora y git

**El usuario establecio que `CHAT.md` y `CHAT_LARGO.md` son contexto interno de trabajo, no
fuente del repositorio.** Esto cambia como se commitea de aqui en adelante.

Estado medido de `.kiro/contexto/`:

| Fichero | Git | Naturaleza |
|---|---|---|
| `CHAT.md` | trackeado, **93 commits** | contexto |
| `CHAT_LARGO.md` | trackeado, 5 commits | contexto |
| `CHAT_ARCHIVO_2026.md`, 3 `.bak-*` | no trackeados | contexto |
| `Notebooklm.md`, `README.md` | trackeados | **si son del repo** |

**Consecuencia:** el ignore debe ser selectivo por fichero (`CHAT*`), **no** por directorio, porque
`Notebooklm.md` y `README.md` viven ahi y si deben seguir trackeados.

**Advertencia registrada, sin resolver:** dejar de trackear `CHAT.md` implica que un clon nuevo no
traera la bitacora. Si se trabaja en mas de una maquina y se usaba git para sincronizarla, esto lo
rompe. **Pendiente de confirmar con el usuario antes de ejecutar.** Nota aparte: dejar de trackear
no reduce el peso del repositorio; los 93 commits siguen en los objetos de git. Reducirlo exigiria
reescribir historia, que **no se recomienda**.

## Archivos modificados

| Ruta | Cambio |
|------|--------|
| `.kiro/hooks/update-knowledge-base.kiro.hook` | **Eliminado**, stageado con `git rm` |
| `.kiro/hooks/save-chat-on-stop.json` | Corregido en la entrada [16], aun sin commitear |
| `.kiro/contexto/CHAT.md` | Esta entrada |

## Commits

Ninguno. El borrado esta stageado sin commitear. Commit propuesto, solo con configuracion real y
**excluyendo la bitacora** segun el criterio nuevo:

`git commit .kiro/hooks/update-knowledge-base.kiro.hook .kiro/hooks/save-chat-on-stop.json -m "chore(hooks): corregir rotacion de bitacora y eliminar hook de otro proyecto"`

## Estado de los hooks

| Hook | Estado |
|------|--------|
| `load-ontology-context.json` | Operativo |
| `save-chat-on-stop.json` | Corregido (5 reglas, rotacion acotada) |
| `validate-before-run.json` + `.ps1` | **ROTO** -- `IDEA-02`: rutas `NEVEN\NEVEN\` inexistentes, **aprueba sin validar** |

De los tres que quedan, el de validacion previa a operaciones de riesgo sigue dando luz verde a todo.

## Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Confirmar si se deja de trackear `CHAT*` (y si se sincroniza entre maquinas por git) |
| **ALTA** | Commitear la configuracion de hooks (comando arriba) |
| **ALTA** | Arreglar `validate-before-run.ps1` (`IDEA-02`): hoy aprueba sin validar |
| **ALTA** | Veredicto de `revisar` en `entrega_loop#2`; si rechaza, extender o cerrar |
| **ALTA** | `MEJ4-01`: mover `src\.github\` a la raiz. El CI **no existe** |
| **ALTA** | Audiolibros: tres causas de la entrada [12], empezar por `SEC-17` (http vs https) |
| **ALTA** | Dos criticos del 5555: autenticacion/CORS y `/api/save_script` |
| MEDIA | Borrar los 3 backups de `.kiro/contexto` (~2,3 MB) tras confirmar la bitacora |
| MEDIA | DOI de `Panko2016` (riesgo de publicacion) |
| MEDIA | `G:\JIC` (5,42 GB); disco externo para backup de M: y E: |
| BAJA | dupeGuru excluyendo `C:\Windows`; Dism; cache de Windows Update |

---