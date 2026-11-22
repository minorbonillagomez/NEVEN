# NEVEN -- Bitacora de Sesion de Trabajo con Kiro

> **Proposito:** indice vivo del proyecto. Estado actual, pendientes abiertos, decisiones de
> diseno vigentes y las entradas de las sesiones mas recientes. **No es el historial completo:**
> todo lo anterior esta en `CHAT_LARGO.md`, en este mismo directorio (ver seccion 4).
> **Ultima actualizacion:** 2026-11-21 ~22:15 (cierre de la auditoria exhaustiva de NEVEN y
> reduccion de esta bitacora).

---

## 0. Regla de la bitacora (obligatoria)

`CHAT.md` es la **memoria persistente** del proyecto. NEVEN tiene muchas capas (C++, Python, R,
Julia, JavaScript); sin bitacora cada sesion empieza de cero.

**Cuando escribir:** al completar un hito (fix, feature, decision de arquitectura), antes de
cerrar sesion, y al abrir sesion hay que **leerla antes de empezar**.

**Que documentar:** el problema y su **causa raiz**, no el sintoma; el arreglo con detalle
suficiente para reproducirlo; los ficheros tocados y sus rutas en produccion; las decisiones de
diseno y su motivo; los **intentos fallidos** y por que fallaron; y los pendientes concretos.

**Reglas de forma, aprendidas a golpes (ver [15] y [16] en `CHAT_LARGO.md`):**

- **Copia de seguridad antes de tocar este fichero, siempre.** Es lo unico que salvo la sesion
  [15], que dejo `CHAT.md` en 2 bytes al intentar trocear bytes con `$b[0..$n]` (en PowerShell el
  *slicing* de un `byte[]` devuelve `Object[]`, y el script siguio sin `$ErrorActionPreference`).
- Anadir en modo `Append`, **sin reescribir el fichero**, y UTF-8 **sin BOM**.
- Mantener el **salto de linea final**: no tenerlo rompio un append y volvera a romperlo.
- Rotacion acotada (hook `save-chat-on-stop.json`): `CHAT.md` > 1.500 lineas baja a ~800 moviendo
  lo antiguo a `CHAT_LARGO.md`; `CHAT_LARGO.md` > 1 MB mueve lo antiguo a `CHAT_ARCHIVO_<AAAA>.md`.
  **Nunca borrar, solo mover**, cortando por entradas completas (`###`).
- Solo la sesion principal escribe aqui (Regla 0 del hook). **Matiz pendiente:** un paso de
  workflow cuyo mandato explicito sea la bitacora si debe escribir; la Regla 0 apunta a las
  escrituras incidentales del hook.

---

## 1. Estado actual del proyecto

| Dato | Valor |
|---|---|
| Rama / HEAD | `master` / `8ec60ae`, sincronizado con `origin/master` |
| Remoto | `https://github.com/minorbonillagomez/NEVEN.git` |
| Prefijo real del codigo | **`src\`**. El arbol `NEVEN\NEVEN\...` **no existe**: desaparecio en `951cfcb` |
| Auditoria exhaustiva | **Cerrada** (3 pasadas de revision). 116 hallazgos + 18 de inventario |
| Veredicto del revisor | `CHANGES_REQUESTED` con 0 HIGH / 2 MEDIUM / 1 NIT. **No se reescribio** |
| Plan de trabajo | 55 items: PENDIENTES 21 / POR MEJORAR 20 / NUEVAS IDEAS 14 |
| Ultimos commits | `8ec60ae` rotacion de bitacora · `2255c57` hooks · `9eba8b1` fix de descarga de audiolibros |

**Hooks:** `load-ontology-context.json` operativo · `save-chat-on-stop.json` corregido (5 reglas,
rotacion acotada) · `validate-before-run.json` + `.ps1` **ROTO** (`IDEA-02`): cita rutas
`NEVEN\NEVEN\` inexistentes, de modo que **aprueba sin validar**. La red de seguridad previa a
operaciones de riesgo no existe hoy.

**Sin commitear (`git status`):** `$reportPath/` (artefacto de una variable de PowerShell no
expandida, `LAY-17`), `.agents/tasks/` (los entregables de la auditoria, ~900 KB),
`NEVEN.code-workspace` y cuatro `.bak-*` de este directorio.

**Bases de conteo de la libreria R** (las tres son legitimas; hay que decir siempre cual se usa):
**93** definiciones en 63 ficheros `.R` (bruta) · **67** en los 37 no-`.Studio.R` · **42** en los
30 no-Studio y no-internos (funciones de usuario). El cargador **no distingue** `.Studio.R`, asi
que "67 llamables desde celda" es falso.

---

## 2. Pendientes vivos

### ALTA

| # | Tarea |
|---|---|
| 1 | **Verificar funcionalmente la descarga de audiolibros en el TaskPane.** El arreglo de `9eba8b1` esta desplegado byte a byte y es correcto en su mecanismo, pero **nunca se ha ejecutado**. Detalle en la seccion 3 |
| 2 | **`A-01` / `SEC-01` + `SEC-03`:** la API local del 5555 ejecuta R/Julia/Python y escribe ficheros **sin autenticacion**, con `Access-Control-Allow-Origin: *`. Los dos unicos criticos con consecuencia directa |
| 3 | **`B-01` / `MEJ4-01`: mover `src\.github\` a la raiz.** GitHub no lee esa ruta: el CI **no existe**. Media jornada y habilita toda la verificacion automatica |
| 4 | **Arreglar `validate-before-run.ps1` (`IDEA-02`).** Hoy da luz verde a todo |
| 5 | **`A-02` / `PROD-01`: colision del puerto 5556.** Tres servicios lo reclaman y el de audiolibros pierde |
| 6 | **Completar los dos puntos que el revisor dejo abiertos:** (a) la lista de rutas de `A-13` cubre 10 de las 12 funciones que el item se obliga a cerrar; faltan `DB_Unicos` y `DB_Union` de `src\libreria\R\R4XCL-UT-Pivote.R`; (b) la tabla de estado del arbol de `informe §13` / `plan §9` esta incompleta y ya desfasada por los commits posteriores |

### MEDIA

| # | Tarea |
|---|---|
| 7 | **Reformular `INV-LR-04`** (`src\docs\ontologia\neven-core\neven-ontology-p2.yaml:660-667`, redaccion en `plan §5.1`) **antes** de ejecutar `A-13` y `C-09`. Primero el YAML, despues el codigo |
| 8 | **Decidir si los 26 `.Studio.R` se siguen desplegando a `C:\NEVEN\functions`.** Estan desplegados, se registran y aparecen en el asistente de funciones de Excel con el texto de respaldo. Decision de producto delegada a `B-08`; comprobable en un minuto con Excel abierto |
| 9 | **`COD-46`: el DOI de `Panko2016` resuelve a otro articulo de otro autor.** Es una tesis: riesgo de publicacion |
| 10 | **Matizar la Regla 0 del hook** para excluir a los pasos de workflow con mandato explicito sobre `CHAT.md` |
| 11 | **Anadir `.gitattributes`.** Sin el, git reescribe finales de linea (`LF will be replaced by CRLF`) e infla diffs sin cambio real de contenido |
| 12 | **Borrar los `.bak-*` de `.kiro\contexto\`** (~2,4 MB) una vez comprobada esta reduccion |
| 13 | Eliminar `G:\JIC` (5,42 GB) tras dias de sistema estable; **disco externo USB** para backup de `M:` y `E:` (el iPhone **no sirve**) |

### BAJA

| # | Tarea |
|---|---|
| 14 | **Mojibake de `CHAT.md` y `CHAT_LARGO.md`** (`LAY-13`): doble codificacion UTF-8. Es una pasada de reencodificado con copia previa, no algo que hacer a la vez que se escribe |
| 15 | dupeGuru excluyendo `C:\Windows`; limpieza Dism; cache de Windows Update |

---

## 3. El pendiente de audiolibros, con su causa raiz

No era un fallo: eran **tres causas independientes** que mantenian inerte un arreglo correcto.

1. **`PROD-01`** -- algo escucha en el 5556; el servidor responde "Server already running" sin
   comprobar que sea el servidor correcto, y el error de bind real se pierde en `DEVNULL`
   (`src\startup\neven_http_server.py:2332-2341`, `:2350-2357`).
2. **`SEC-17`** (hipotesis, comprobable en un minuto) -- `src\TaskPane\audiobook.js:118` llama a
   `http://localhost:5555` mientras produccion sirve **https** (hay `certPath`/`keyPath` en
   `C:\NEVEN\neven-config.json`). El navegador bloquea por contenido mixto.
3. **`PROD-03`** -- el pipeline escribe `.m4a`; el listado, el QR y el cliente buscan `.m4b`.

**Regresion que introdujo `9eba8b1`:** si el nombre exacto no existe, el endpoint lista el
directorio y sirve `matches[0]` como `audio/mp4` aunque sea un `.md`, en orden arbitrario de
`os.listdir` (`src\Audiobook\api\routes.py:109-113`).

**Path traversal: DESCARTADO con evidencia.** `normpath` mas comprobacion de prefijo rechazan con
403, incluso con `..` doblemente codificados.

**Como verificar:** los seis pasos de `informe §7.3`. **El paso 4 es el que vale**: pedir
`/api/download/Miguel` (caso negativo) delata si el paso 3 paso por el *fallback*. Sin ese paso la
verificacion no significa nada.

---

## 4. Decisiones de diseno vigentes

**Sobre el repositorio y la bitacora**

1. **`CHAT*` se mantiene trackeado en git.** El usuario descarto el `git rm --cached` y el ignore
   selectivo para evitar riesgos: dejar de trackear rompe la sincronizacion entre maquinas y **no**
   reduce el peso del repositorio (los 93 commits siguen en los objetos de git).
2. **Un ignore de este directorio tendria que ser por fichero (`CHAT*`), nunca por carpeta,**
   porque `Notebooklm.md` y `README.md` viven aqui y si son del repositorio.
3. **`git rm` en lugar de `Remove-Item`** para borrar ficheros trackeados, para que el borrado
   quede declarado en el indice (leccion de `Notebooklm.md`, que desaparecio del arbol sin que
   nadie lo reclamara; se restauro).
4. **Se descarto heredar hooks ajenos.** `update-knowledge-base.kiro.hook` apuntaba a un proyecto
   distinto y ordenaba *commit and push* automatico. Recuperable con
   `git checkout c27eac3 -- .kiro/hooks/update-knowledge-base.kiro.hook`.

**Sobre el metodo de trabajo**

5. **La ontologia manda.** Las 62 invariantes de `src\docs\ontologia\neven-core\*.yaml` son
   restricciones de arquitectura: ningun item del plan viola una. Si una invariante debe cambiar,
   **primero se reformula el YAML y despues se toca el codigo**.
6. **Un test que verifica la intencion declarada no verifica el resultado entregado.** `SEC-11`:
   el XLL se distribuye sin Control Flow Guard y el test que protege `INV-BLD-02` **pasa**, porque
   lee el `CMakeLists.txt` y no el binario. Las invariantes mecanizadas deben medir el **artefacto**.
7. **Publicar siempre el patron y la poblacion junto al numero.** Las tres clases de error de la
   auditoria fueron: un patron unico sobre un lenguaje con dos sintaxis; restar conteos en lugar de
   comparar conjuntos; y usar dos poblaciones distintas como si fueran la misma (93 / 67 / 42).
8. **Cualquier regex sobre texto de este repositorio tiene que contemplar las dos formas, con y
   sin acento.** La documentacion mezcla ambas; ya ha causado tres mediciones falsas.
9. **Copiar ficheros con `[System.IO.File]::Copy()`, nunca `Copy-Item`** (corrompe UTF-8). Los `.R`
   se despliegan con `UTF8Encoding($false)` por `INV-SR-05`.
10. **Reutilizar antes de escribir.** `buildSlotElement` es el unico renderer de resultados y
    `_parse_slots_from_variable` el unico parser de ControlR; no se reimplementan.

---

## 5. Donde esta el historial completo

| Fichero | Contenido |
|---|---|
| **`CHAT_LARGO.md`** | **Archivo historico completo**, por orden cronologico. Incluye las entradas **[1] a [17]** de la auditoria (las [9]-[17] se archivaron el 2026-11-21 ~22:15; la cabecera del archivado explica el rango y la continuidad) |
| `CHAT_ARCHIVO_2026.md` | Historico de 2026 anterior, separado por la rotacion del 2026-11-21 ~09:37 |
| `CHAT.md.bak-20261121-2211` | **Copia de seguridad del `CHAT.md` completo previo a esta reduccion** (47.671 B, 825 lineas, hash verificado) |
| `CHAT.md.bak-pre15`, `CHAT.md.bak-rot20261121-093709`, `CHAT_LARGO.md.bak-rot20261121-093709` | Copias de rotaciones anteriores del mismo dia. Borrables (pendiente 12) |

---

## 6. Entradas de sesion

### [18] 2026-11-21 (~20:50-22:15) -- Auditoria exhaustiva de NEVEN: cerrada, con entregables

**Entregables, en `F:\ANTIGRAVITY\2026\NEVEN\.agents\tasks\auditoria-neven\`:**

- [`informe-auditoria.md`](../../.agents/tasks/auditoria-neven/informe-auditoria.md) --
  107.035 B, 1.065 lineas. Los cuatro ejes que pidio el usuario (producto, codigo, seguridad,
  mejoras), 116 hallazgos con ruta y linea, cada uno citable por su identificador.
- [`plan-de-trabajo.md`](../../.agents/tasks/auditoria-neven/plan-de-trabajo.md) --
  126.723 B, 1.956 lineas. 55 items en los tres grupos pedidos: **PENDIENTES 21**,
  **POR MEJORAR 20**, **NUEVAS IDEAS 14**.
- Material de respaldo en el mismo directorio: `00-layout-real.md`, `plan-auditoria.md`,
  `01-notas-producto.md` (29 `PROD-*`), `02-notas-codigo.md` (56 `COD-*`),
  `03-notas-seguridad.md` (24 `SEC-*`), `04-notas-mejoras.md` (7 `MEJ4-*`), `review.md`,
  `review.json`.

**Modo de ejecucion:** solo lectura sobre NEVEN. Ningun fichero de codigo modificado, nada escrito
en `C:\NEVEN\`, sin compilar, sin ejecutar servicios.

**La tesis de la auditoria: los problemas no estan donde el proyecto los vigila.** El codigo C++
tiene mejor higiene de la esperada (cero funciones inseguras de la CRT, RAII real, IPC
centralizado, 369 tests, **cero hallazgos criticos en codigo**). Los tres focos reales son la
superficie HTTP local sin control de acceso, la ausencia de verificacion automatica, y una
documentacion que describe un proyecto que ya no es este.

**Recuento:** 3 criticas, 24 altas, 53 medias, 2 media-baja, 26 bajas, 8 informativas = **116**,
mas 18 hallazgos de inventario (`LAY-01..LAY-18`).

**Hallazgos de mayor prioridad** (los que cambian una decision, `informe §1`):

| ID | Que | Por que importa |
|---|---|---|
| `SEC-01` | API del 5555 sin autenticacion, CORS comodin, endpoints de ejecucion | Convierte "visitar una pagina" en ejecucion de codigo en la sesion de Excel del usuario |
| `SEC-03` | `/api/save_script` escribe en cualquier ruta y el hot-reload lo ejecuta | Misma superficie, escritura en lugar de lectura |
| `MEJ4-01` | `src\.github\` no esta en la raiz: el CI no existe para GitHub | Arreglar solo el filtro de rama (`COD-19`, main/develop frente a master) no habria cambiado nada |
| `PROD-01` | Tres servicios reclaman el 5556; el de audiolibros pierde | Es la causa de que el pendiente arrastrado nunca se pudiera probar |
| `SEC-08` | Integridad de scripts *fail-open* y **0** ficheros `.sha256` para 92 scripts desplegados | `INV-CMN-02` se cumple en la logica y esta violada en los datos |
| `SEC-11` | `NEVEN64.xll` distribuido sin Control Flow Guard | `INV-BLD-02` incumplida en el artefacto mientras su test pasa |
| `COD-46` | El DOI de `Panko2016` apunta a otro trabajo | Es una tesis: la cita que sostiene la motivacion envia al lector a otro articulo |
| `PROD-08` | 12 de las 42 funciones de usuario de la libreria R no tienen ayuda efectiva | El asistente de funciones de Excel muestra "Exported Function" para esas 12 |

**Primeros items del plan.** El orden es **por dependencia, no por severidad**. Coste total si se
hiciera todo: 126-196 jornadas; las fases 0 a 2 suman **26-39** y son las que cambian el riesgo
real del proyecto.

| Fase | Items | Coste |
|---|---|---|
| **0 -- Verificar antes de arreglar** | `B-01` mover `.github\` y arreglar el workflow · `B-02` runner de pytest · `B-21` declarar el estado de las 27 especificaciones · `C-10` decidir el alcance de NEVEN-SIM | 3-6 j |
| **1 -- Cerrar lo abierto al exterior** | `A-01` autenticar la API local (con `B-03` **en paralelo**) · `A-02` puerto y bind del servidor de audiolibros · `A-03` endpoint de descarga y verificacion (cierra el pendiente arrastrado) · `A-08` politica unica de `srcdoc` | 11-17 j |
| **2 -- Integridad del despliegue** | `B-08` fuente unica y paridad (antes de `A-04`) · `A-04` integridad real de scripts · `A-05` ACL de produccion · `A-06` `/guard:cf` · `B-09` logs · `A-07` guarda de excepciones | 12-16 j |

**Cierre del bucle de revision.** Tres pasadas: **2H+4M+5N -> 0H+3M+4N -> 0H+2M+1N**. La tercera
se concedio por un motivo concreto y lo cumplio: **MEDIUM-1 resuelto**, las tres bases de conteo
publicadas con su patron, 113 de 116 identificadores presentes en los bloques "Motivado por".
**`COD-48` ya es fiable y puede usarse para corregir la tesis.** El usuario aprobo cerrar
(`update_workflow`, `update_status`, nodo `entrega_loop`), lo que **no reescribe el veredicto**:
queda `CHANGES_REQUESTED` con los dos puntos del pendiente 6.

**Esta sesion, ademas:** se reviso el repositorio `affaan-m/ECC` y **se descarto** por no aportar a
NEVEN; se corrigio el hook `save-chat-on-stop.json` (5 reglas, rotacion acotada) y se elimino
`update-knowledge-base.kiro.hook`, que apuntaba a otro proyecto y ordenaba push automatico; y se
archivo el historial [9]-[17] en `CHAT_LARGO.md` dejando este fichero como indice.

**Commits:** `2255c57` (hooks) y `8ec60ae` (rotacion de bitacora), ambos pusheados a
`origin/master` previa comprobacion de fast-forward puro. Los entregables de `.agents/tasks/`
siguen sin commitear.

**Addenda a [18] (~21:31).** El run `wf_2c457a59650e274f` **termino**: nueve pasos completados
(setup, recon, los cuatro ejes, `entrega_loop` con 3 pasadas, `bitacora`). **Incumplimiento de la
Regla 3(b) detectado y corregido en este mismo cierre:** el paso `bitacora` anadio 48.554 B a
`CHAT_LARGO.md` y lo dejo en 1.096.308 B, por encima del cap de 1 MB que yo mismo fije hoy; no lo
conocia. Archivado aplicado (ver abajo). **Nota de formato:** la entrada [18] usa `### ALTA/MEDIA/BAJA`
como subsecciones, lo que falsea cualquier recuento por `^###`; al rotar hay que cortar solo en
`^###\s+\[` o `^###\s+Sesion`, nunca en cualquier `###`.

**Addenda 2 a [18] (~21:34) — arranque de la ejecucion.** Consultado el plan a peticion del usuario:
el detalle vive en `plan-de-trabajo.md` **§7 (secuencia por fases)** y **§8 (dependencias duras)**;
no se duplica aqui. **Tecnicamente nada bloquea empezar**; la Fase 0 ("verificacion antes que
arreglos", 3-6 jornadas) **es** el arranque: `B-01` mover `.github\` + arreglar el workflow,
`B-02` runner de pytest, `B-21` estado real de las 27 especificaciones (207 de deuda real, no 461),
`C-10` alcance de NEVEN-SIM. Ninguno arregla un bug: sirven para que lo arreglado despues quede sujeto.
**Lo que depende del usuario, no de codigo:** (a) `C-10`, media jornada pero **109 casillas** cuelgan de
ella; (b) **aprobar las 4 reformulaciones de ontologia** (§5.1-§5.4), prerrequisitos duros -- la mas
urgente §5.1, porque `INV-LR-04` afirma una consecuencia falsa y bloquea `A-13` y `C-09`;
(c) commitear `.agents/tasks/` (~900 KB), hoy sin control de versiones.
**Dos trampas de orden que el plan marca como errores:** `A-01` va **en paralelo** con `B-03`, no
despues, o los arreglos quedan sin fijar; y `B-19` sin `B-02` **repite el incidente de septiembre de
2026** (refactor del servidor HTTP revertido, TaskPane caido), precedente que esta en esta bitacora.
**Coste:** fases 0-2 = 26-39 jornadas (es lo que cambia el riesgo real); fase 3 = 30-45; fase 4 = 70-110;
todo = 126-196. **Propuesta hecha al usuario, SIN respuesta aun:** commitear entregables, el resuelve
`C-10` y §5.1, y se lanza `B-01` por workflow.

**Addenda 3 a [18] (~21:38) — evidencia para cerrar `C-10` (alcance de NEVEN-SIM).**
**Hallazgo decisivo, VERIFICADO:** **el paper de la tesis NO menciona NEVEN-SIM.** Lo unico que
aparece al buscar en `src\docs\Paper\sections\*.tex` y `main.tex` es un ejemplo de funcion Julia
**definida por el usuario** (`=J.MonteCarlo()`, `03_viewer_extensibility.tex:101-116`) que ilustra
la extensibilidad del registro de funciones. **Es otra cosa**, no el modulo XLL. Consecuencia:
declarar NEVEN-SIM experimental **no exige cambiar ni una linea de LaTeX**, lo que abarata mucho esa
rama de la decision.
**Contradiccion documental confirmada:** `src\docs\Arquitectura\Arquitectura.md:267` **si** lo
presenta como modulo del producto, con seccion propia y diagrama, fechado julio 2026; la spec
`.kiro\specs\neven-sim\tasks.md` tiene **109 abiertas / 0 marcadas** (recontado); y el build lo trae
desactivado. Arquitectura dice "modulo", la spec dice "sin empezar", la tesis no lo menciona.
**No verificado (fallo propio):** el estado real del flag en `src\CMakeLists.txt`; use un offset de
lineas equivocado y lei otro bloque. Queda por comprobar.
**Cinco preguntas planteadas al usuario, SIN respuesta aun:** (1) ¿se ha ejecutado `SIM_QuickSim`
de extremo a extremo alguna vez? -- separa "modulo que funciona sin documentar" de "prototipo que
nunca corrio", y es la que mas pesa; (2) ¿entra en la defensa, y la ausencia en el paper fue
deliberada?; (3) ¿hay un caso de simulacion concreto que sirva como corte vertical minimo?;
(4) ¿plazo hasta la entrega? (corte vertical = XL frente a media jornada de declararlo experimental);
(5) ¿`BUILD_NEVEN_SIM=OFF` fue deliberado? Si lo fue, la decision ya estaba tomada y solo falta
escribirla. **Con las respuestas 1 y 2 probablemente baste.**

**Addenda 4 a [18] (~21:52) — `C-10` CERRADO: NEVEN-SIM congelado temporalmente.**
**Decision del usuario:** congelar (opcion **A**) **para recuperar enfoque**, y retomar por la opcion
**C** una vez cerrados los pendientes. Congelacion **temporal y con salida nombrada**, no
"experimental" a secas. **Motivo de fondo:** NEVEN-SIM se concibio como **alternativa a Oracle Crystal
Ball**; eso es una linea de producto (distribuciones, entradas correlacionadas, tornado, sensibilidad,
optimizacion), no un modulo, y sus 109 tareas competian con los P0.
**HALLAZGO QUE CORRIGE MI PROPIO ANALISIS:** dije que la opcion C "pierde el rendimiento nativo de
C++" y **era falso**. La spec de NEVEN-SIM **ya delegaba el calculo en R y Julia**: Task 2 define
`SimBridge` como *relay* que invoca `NEVEN.r()` / `NEVEN.j()` via `Excel12(xlUDF, ...)`, y el
diagrama de `Arquitectura.md` lo dice literalmente ("SimBridge (relay a R/Julia)",
"FitService (->R fitdistrplus)", "MonteCarloService (->Julia)"). **No hay calculo nativo que perder:**
el XLL separado siempre fue una capa de relay sobre capacidades que NEVEN ya expone. Eso **abarata
mucho la opcion C** y la convierte en la via razonable al retomar.
**Flag verificado** (cierra el "no verificado" de la addenda 3): `src\CMakeLists.txt:117`
`option(BUILD_NEVEN_SIM ... OFF)`, `if(...)` en :119, `add_subdirectory` en :120. Ya estaba
congelado de facto en el build; faltaba declararlo.
**Ficheros modificados:** `.kiro\specs\neven-sim\tasks.md` (cabecera de estado con motivo, condicion
de salida = fases 0-2 del plan §7, y el aviso de no reabrir las 109 sin responder antes "¿hace falta
un XLL separado?") y `src\docs\Arquitectura\Arquitectura.md:267` (nota de estado; aclara que lo que
sigue es diseno previsto, no funcionalidad disponible). **Sin tocar** `CMakeLists.txt` (ya OFF) ni el
paper (no lo menciona). Las 109 tareas **no se borraron**, solo salen del computo de deuda.
**Desbloquea:** `B-21` ya puede publicar la deuda real (**207, no 461**).
**Abierto (narrativa de la tesis, decision del usuario):** si se anade "Monte Carlo como alternativa a
Crystal Ball" al *future work* del paper. Sin commitear aun.
