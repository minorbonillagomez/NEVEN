# Revisión de los entregables de la auditoría de NEVEN (tercera pasada)

**Objeto:** `informe-auditoria.md` (107.035 B, 1.065 líneas) y `plan-de-trabajo.md` (126.723 B,
1.956 líneas) en `f:\ANTIGRAVITY\2026\NEVEN\.agents\tasks\auditoria-neven\`.
**Esta es una revisión, no una primera lectura.** El directorio contiene el `review.md` y el
`review.json` de la pasada anterior (21/11 00:49-00:50) y los dos entregables se reescribieron
después (09:22-09:23), así que el método ha sido: re-comprobar los siete hallazgos previos uno por
uno y marcarlos **Cerrado** o **Sin cambio**, y después revisar lo que cambió midiéndolo yo.
**Modo:** solo lectura. No se repitió la auditoría, no se ejecutó ninguna suite, no se escribió nada
fuera de `review.md` y `review.json`.
**Veredicto:** **CHANGES_REQUESTED** (0 HIGH, 2 MEDIUM, 1 NIT).

Los siete hallazgos de la pasada anterior están **cerrados**, y lo están con datos que he vuelto a
medir: las tres bases de conteo de la librería R que publica la nueva §2.2 (93 / 67 / 42) son
exactas fichero a fichero, el reparto de los siete internos (13, 3, 0, 5, 1, 1, 2 = 25) también, y
los 116 identificadores contra los 55 campos "Motivado por" dan exactamente los tres cierres sin
ítem que los dos documentos declaran. Lo que queda son dos cosas: la corrección del conteo llegó a
las cifras pero **no a la lista de rutas de `A-13`**, que cubre 10 de las 12 funciones que el ítem
se obliga a cerrar, y la tabla de **estado del árbol** que los dos documentos publican como
inventario medido ya estaba incompleta cuando se escribió, y lo está más ahora: el árbol se movió
durante esta revisión, con dos commits de bitácora que no tocan nada bajo `src\`.

---

## 1. Verificación del check, punto por punto

| # | Check | Resultado |
|---|---|---|
| 1 | Existen los dos entregables en las rutas indicadas | **PASS**. Presentes, con los seis documentos de respaldo y el `review.*` de la pasada anterior |
| 2 | El informe cubre los cuatro ejes | **PASS**. §3 producto (29 `PROD-*`), §4 código (56 `COD-*`), §5 seguridad (24 `SEC-*`), §6 mejoras (7 `MEJ4-*` más la consolidación en 55 ítems). Recontado el recuadro de §1 eje por eje y severidad por severidad: COD da 9 altos + 26 medios + 15 bajas + 6 informativas = 56 contando filas de tabla, y PROD + SEC + MEJ4 dan 3 críticas, 15 altas, 27 medias, 2 medias-bajas, 11 bajas y 2 informativas = 60. Total 116, y 29 + 56 + 24 + 7 = 116 |
| 3 | Layout real confirmado frente a las referencias contradictorias | **PASS**. Comprobado por mí: `.github` en la raíz = **False**, `src\.github` = True, y `git ls-files` sitúa el workflow y las tres plantillas bajo `src/.github/`; `src\.github\workflows\build-and-test.yml:5` dice `branches: [ main, develop ]`, `:7` `[ main ]` y `:54` el `refs/heads/main`, que son las líneas que el informe cita (la nota de trabajo decía `:56`; el entregable la corrigió); 62 invariantes únicas en los cuatro YAML; 63 `.R` en `src\libreria\R` |
| 4 | Cada hallazgo cita ruta concreta y distingue VERIFICADO de HIPÓTESIS | **PASS**. Los 116 tienen fila propia con columna de evidencia; la tabla de bajos e informativos de §4.3, que no lleva columna de fundamento, declara antes "todos VERIFICADO salvo `COD-21`". Donde el hallazgo es una ausencia o una afirmación sobre el historial, la evidencia es el comando o el commit (`COD-25`, `COD-20`, `SEC-24`, `SEC-18`), que es la cita correcta para eso. Los basenames sin prefijo (`taskpane.html`, `controlr.cc`, `audiobook.js`) resuelven sin ambigüedad: comprobado que cada uno tiene **una sola** copia tracked |
| 5 | Cada ítem declara prioridad, rutas e invariantes | **PASS con un defecto de forma** (finding NIT-3). 55 ítems, 55 con `Prioridad`, `Coste`, `Riesgo`, `Invariantes` y `Motivado por`; 54 con la etiqueta `**Rutas:**` y uno, `B-08`, que la escribe `**Rutas.**` aunque sí declara las rutas. Prioridades 5/22/19/9. Las 50 invariantes citadas en los dos documentos existen todas en los YAML; **cero citadas inexistentes** |
| 6 | Los tres grupos poblados | **PASS**. PENDIENTES 21, POR MEJORAR 20, NUEVAS IDEAS 14 = 55, contado por encabezado. Por familia y grupo: A 12/11/0 = 23, B 7/9/5 = 21, C 2/0/9 = 11, que es exactamente la tabla de §6.1 del informe |
| 7 | Ninguna propuesta viola una invariante en silencio | **PASS**. Extraído el campo `Invariantes` de los 55: ninguno queda vacío y los que no tocan nada lo dicen. §5 nombra las cuatro reformulaciones (`INV-LR-04` `p2:660`, `INV-AS-03` `p3:205`, `INV-SB-03` `p2:283`, `INV-CMN-02` `p1:347`) con dónde, por qué y redacción propuesta; las cuatro adiciones para huecos declarados; y §5.6 los cuatro ítems condicionados. Los que podrían chocar declaran lo contrario con argumento: `A-02` respeta `INV-AS-03`, `A-05` declara que las ACL son un hueco y no una violación, `B-20` respeta `INV-TF-04` con el cargador elegido |
| 8 | Sin credenciales, secretos ni tokens | **PASS**. Barrido de `sk-*`, `AsPlainText`, `-Password`, `BEGIN PRIVATE KEY`, `apiKey":"…`, cadenas hex ≥ 40, endpoints de Azure, `AKIA*`, `ghp_*` y `xox*` sobre los dos entregables: **0 coincidencias**. Extraído el literal de la contraseña de exportación del PFX del propio script y buscado como cadena exacta en los dos entregables: **0 coincidencias**. `SEC-10`, `SEC-18`, `LAY-06` y §5.5 describen naturaleza y ubicación sin valores |
| 9 | Nada modificado fuera de `.agents\tasks\auditoria-neven\`; nada en `C:\NEVEN\` | **PASS en lo sustantivo, FAIL en lo que los entregables publican** → finding MEDIUM-2. `C:\NEVEN\`: **0** ficheros con escritura posterior al 2026-11-20 en todo el árbol recursivo. `git status --porcelain -- src` devuelve **0** entradas: ningún fichero de código tocado, ni en el árbol ni en los dos commits de bitácora que aterrizaron durante esta revisión (`git diff --name-only 9eba8b1..HEAD` filtrado por `src/` da 0). Lo que falla es la tabla: al escribirse publicaba cinco entradas y el árbol tenía siete, una de ellas creada ocho minutos antes |

---

## 2. Estado de los siete hallazgos de la pasada anterior

| Previo | Asunto | Estado |
|---|---|---|
| MEDIUM-1 | Dos bases de conteo incompatibles: "67 llamables desde celda" frente al denominador 93 | **Cerrado, y bien cerrado.** La nueva §2.2 publica las tres bases con su patrón y declara que ninguna es el número que Excel registra, citando el mecanismo (`rj2xcl.cc:479-497`, `language_service.cc:492-510`, `:502-503`). Re-medido por mí con el patrón declarado: **93** definiciones en 63 ficheros, **67** en los 37 no-`.Studio.R`, **42** en los 30 no-Studio y no-internos, 26 ficheros `.Studio.R`, y el reparto de los siete internos 13/3/0/5/1/1/2 = **25**. Las cuatro cifras y los siete sumandos caen exactos. §1, `PROD-08`, §3.1 punto 4, §3.4, §6.2 nº 5, `COD-48`, `A-13`(d), `B-10`, `B-15` y `C-09` usan ahora la base que les corresponde y la nombran |
| MEDIUM-2 | `SEC-19` y `COD-51` fuera de todo "Motivado por", y el trabajo de `SEC-19` sin ítem | **Cerrado.** Extraídos los 55 bloques "Motivado por" y buscados los 116 identificadores: faltan exactamente **tres**, `COD-21`, `COD-26` y `COD-52`, que es lo que los dos documentos declaran. `A-18` tiene ahora punto (e) con las dos acciones de `SEC-19`, `src\Common\ViewerWindow.cc:261-295, 552-626` en sus rutas y `SEC-19` en su "Motivado por"; §6 punto 2 apunta a `A-18`(e) y acota que lo único que no entra es la CSP. `COD-51` está en el "Motivado por" de `B-15`, con la nota de que es línea base a conservar |
| MEDIUM-3 | El árbol no estaba confinado: faltaba `Notebooklm.md`, tracked | **Cerrado en el fichero, reabierto en la tabla.** `git diff HEAD -- .kiro/contexto/Notebooklm.md` no devuelve salida y el fichero ya no aparece en `git status`: está restaurado e idéntico a `HEAD`, como dice §13. La anomalía queda registrada con su causa declarada como no determinada, que es lo correcto. Lo que no cierra es la completitud de la tabla: hoy hay dos entradas más → finding MEDIUM-2 de esta pasada |
| NIT-4 | `PROD-08` decía "las 62 restantes" donde §3.4 obliga a 63 | **Cerrado.** La fila de `PROD-08` ya no usa ese reparto: dice "30 con ayuda efectiva, 12 sin ella" sobre la base de usuario y deja el 63 de 93 como cifra bruta con su nota. La tabla de §3.4 publica 12 / 37 / 63 según la base, y las tres restas cuadran (42−30, 67−30, 93−30) |
| NIT-5 | "22 referencias" sin regla de recuento frente a 25 filas | **Cerrado.** §2.2 publica la regla (18 filas de ruta − 2 del workflow de CI − 1 + 7 documentos = 22; 7 filas de cifra − 1 por la duplicación del `README` = 6) y `B-10` la repite en su campo de rutas. Contadas por mí las filas de `00-layout-real.md` §4: **25**, de ellas **18** de ruta y **7** de cifra o nombre. La aritmética es reproducible |
| NIT-6 | Línea de la credencial del PFX desplazada (`:43` por `:42`) | **Cerrado.** `LAY-06` y §5.5 citan `:42` como la línea del literal y explican que `:43` es el `Export-PfxCertificate` que lo consume |
| NIT-7 | `B-04` decía `INV-LR-04` violada "en cinco" y §4.4 decía 12 | **Cerrado.** `B-04` dice "`INV-LR-04` en **cinco ficheros de función de usuario** —12 contando los siete internos, que la redacción propuesta en §5.1 deja fuera de alcance—" |

---

## 3. Hallazgos

### MEDIUM-1 · La lista de rutas de `A-13` alcanza 10 de las 12 funciones que el propio ítem se obliga a cerrar: faltan `DB_Unicos` y `DB_Union`

**Dónde.** `plan-de-trabajo.md`, `A-13`, campo **Rutas**: "…y los cinco ficheros de función de
usuario sin ningún `attr(`: `R4XCL-AD-NonParRolCor.R`, `R4XCL-BD-ObtieneDatos.R`,
`R4XCL-DS-Wooldridge.R`, `R4XCL-GR-Mapa.R`, `R4XCL-NEVEN-pluto-read.R`", más
`R4XCL-UT-Pivote.R:336` y `R4XCL-FX-Aleatorios.R:229`. Y `informe-auditoria.md` §3.4, que publica el
recuento de 12 sin decir en qué ficheros viven.

**El problema.** El ítem fija su propio criterio de cierre: "De las 42 funciones de usuario de la
librería, 30 tienen ayuda efectiva y 12 no… **Esa es la base sobre la que trabaja este ítem y la que
hay que usar para medir si está cerrado**". Extraídas las 42 definiciones de usuario y cruzadas con
los 31 nombres que reciben el atributo, las que se quedan sin él son once, y están en **siete**
ficheros, no en cinco:

| Fichero | Funciones sin atributo |
|---|---|
| `R4XCL-AD-NonParRolCor.R` | `AD_NonParRolCor`, `AD_plot_rolcor_estim_heatmap`, `AD_prueba` |
| `R4XCL-BD-ObtieneDatos.R` | `DS_ObtenerDatos` |
| `R4XCL-DS-Wooldridge.R` | `DS_Wooldridge` |
| `R4XCL-GR-Mapa.R` | `MP_MapaISO03` |
| `R4XCL-NEVEN-pluto-read.R` | `NEVEN.pluto_list`, `NEVEN.pluto_read` |
| `R4XCL-FX-Aleatorios.R` | `FX_AleatorioNormal` (`:167`) |
| **`R4XCL-UT-Pivote.R`** | **`DB_Unicos` (`:1`), `DB_Union` (`:18`)** |

Las cinco rutas enumeradas cubren 8 funciones; `FX-Aleatorios.R:229` cubre la novena; `UT-Pivote.R:336`
cubre la inerte `DB_Recodificar`, que es la duodécima. **`DB_Unicos` y `DB_Union` no están en
ninguna ruta de ningún ítem.** `R4XCL-UT-Pivote.R` define cuatro funciones de usuario
(`DB_Unicos:1`, `DB_Union:18`, `DB_Pivote:112`, `DB_Recodificar:312`) y solo una tiene descripción
efectiva (`attr(DB_Pivote, DialogosXCL$Descripcion)` en `:298`); el fichero aparece en el plan solo
por la cadena inerte de `:336`, de modo que un implementador que trabaje el campo Rutas arregla esa
línea y no se entera de las otras dos.

Consecuencia: `A-13`(d) se cierra con 40 de 42 funciones con ayuda y el ítem queda marcado como
hecho mientras `PROD-08` sigue abierto en dos funciones. No es un error de conteo —el 11 y el 12 son
correctos y los he medido— sino un error de alcance: la corrección de la base de conteo llegó a las
cifras y no a la lista de trabajo.

**Arreglo concreto.**

1. En el campo Rutas de `A-13`, sustituir "y los cinco ficheros de función de usuario sin ningún
   `attr(`" por la lista de las **doce funciones** con fichero y línea, que es la unidad en la que
   el ítem se mide. Añadir explícitamente `R4XCL-UT-Pivote.R:1` (`DB_Unicos`) y `:18` (`DB_Union`),
   y dejar la nota de que ese fichero necesita tres cosas, no una: dos atributos nuevos y la
   conversión de la cadena de `:336` a `list()`.
2. En `informe-auditoria.md` §3.4, publicar la tabla de las 12 funciones por fichero. Son doce
   nombres y cierran el salto entre el recuento por fichero (12 de 37 ficheros no asignan el
   atributo) y el recuento por función (12 de 42 funciones no tienen ayuda efectiva), que hoy el
   lector tiene que reconstruir y que es justo donde se perdieron estas dos.
3. Comprobación de cierre, para que no vuelva a pasar: el barrido de `B-04` que derive de la nueva
   `como_verificar` de §5.1 debe contar **por función exportada**, no por fichero, y ese es el
   número que cierra `A-13`(d).

### MEDIUM-2 · El inventario del árbol de trabajo que los dos entregables publican como medido estaba incompleto al escribirse y hoy lo está más

**Dónde.** `informe-auditoria.md` §13, titulada "Estado del árbol de trabajo al cerrar la auditoría ·
**VERIFICADO**", con una tabla de cinco filas; y `plan-de-trabajo.md` §9, que la resume con las
mismas cinco.

**El problema, medido en dos momentos.** Al empezar esta revisión, `git status --porcelain` devolvía
**siete** entradas: las cinco de la tabla más ` M .kiro/hooks/save-chat-on-stop.json` y
`?? .kiro/contexto/CHAT.md.bak-pre15`. Las cinco declaradas estaban ahí y sus veredictos son
correctos: comprobado que `$reportPath\` contiene un `DCUApplicableUpdates.xml` del 07/11 y
`NEVEN.code-workspace` es del 15/11, los dos anteriores a la auditoría.

La que delata el defecto es **`CHAT.md.bak-pre15`**, 148.956 B, creado el 21/11 a las **09:14**, es
decir **ocho minutos antes** de que se escribiera `plan-de-trabajo.md` (09:22) y nueve antes del
informe (09:23). Existía cuando se redactó la sección y la sección no lo recoge, de modo que la
tabla no era completa ya en el momento de publicarla. La otra, el hook, se modificó a las 09:34, once
minutos después del informe: 3 líneas por 3 para añadir las reglas de rotación acotada de
`CHAT.md`/`CHAT_LARGO.md`, trabajo sancionado por la corrección que el usuario escribió al aprobar
el plan.

**Durante esta revisión el árbol volvió a moverse**, lo que confirma que el problema es el método y
no una entrada concreta. Aterrizaron dos commits, `2255c57` ("chore(hooks): acotar rotacion de
bitacora…") y `8ec60ae` ("docs(bitacora): rotar CHAT.md y archivar historico 2026"), de modo que
HEAD ya no es el `9eba8b1` de la cabecera del informe. Los dos juntos tocan cinco ficheros
—`CHAT.md`, `CHAT_LARGO.md`, `CHAT_ARCHIVO_2026.md`, `save-chat-on-stop.json` y
`update-knowledge-base.kiro.hook`— y **cero bajo `src\`** (`git diff --name-only 9eba8b1..HEAD`
filtrado por `src/` da 0), lo que respalda la disciplina de solo lectura de la auditoría. Al cerrar
esta revisión el árbol tiene siete entradas, **tres de ellas respaldos de bitácora sin seguimiento**
que ningún documento reclama: `CHAT.md.bak-pre15` (148.956 B),
`CHAT.md.bak-rot20261121-093709` (166.264 B) y `CHAT_LARGO.md.bak-rot20261121-093709` (2.155.514 B),
unos 2,5 MB en total, más `CHAT.md` otra vez modificado por el hook de bitácora. Que la cuenta haya
cambiado tres veces en una tarde es el argumento para fechar la tabla en lugar de ampliarla fila a
fila.

Lo sustantivo del check se cumple y lo he verificado en los dos momentos: **0** ficheros escritos en
`C:\NEVEN\` después del 2026-11-20 en todo el árbol recursivo, y **0** entradas de `git status` bajo
`src\`. El defecto es la completitud de una afirmación marcada VERIFICADO, y el riesgo es
exactamente el que §13 dice querer evitar: 2,5 MB de respaldos sin dueño declarado que el siguiente
`git add` amplio se lleva.

**Arreglo concreto.**

1. En §13 y §9, **fechar la medición** ("`git status` a las HH:MM del 2026-11-21") en lugar de
   presentarla como el estado del árbol sin más. Una tabla de estado sin instante no es verificable
   por el siguiente lector, que es el mismo criterio que el informe exige para las cifras de la
   librería R en §2.2.
2. Añadir una fila para la familia que falta, no solo para los ficheros que hoy existen:

| Entrada | Qué es | Veredicto |
|---|---|---|
| `?? .kiro/contexto/*.bak-*` | Respaldos de la bitácora creados por la consolidación y por la rotación del hook (hoy tres, ~2,5 MB) | temporal: borrar o añadir a `.gitignore` antes del siguiente commit |
| ` M .kiro/hooks/save-chat-on-stop.json` | Reglas de rotación de la bitácora, parte de la consolidación que el usuario pidió al aprobar el plan | justificado; **ya commiteado** en `2255c57` |

3. Cerrar los respaldos: si la consolidación y la rotación ya están verificadas, los tres `.bak-*`
   no tienen función. Lo barato y definitivo es una línea en `.gitignore` para
   `.kiro/contexto/*.bak-*`, que es trabajo de bitácora y no de código, y que evita que la próxima
   rotación vuelva a dejar el árbol con entradas que nadie reclama.

### NIT-3 · `B-08` escribe `**Rutas.**` donde los otros 54 ítems escriben `**Rutas:**`

`plan-de-trabajo.md`, `B-08`. El campo existe y declara las rutas con detalle; lo que rompe es la
etiqueta. Una extracción mecánica de los seis campos obligatorios sobre los 55 ítems da 55/55 en
`Prioridad`, `Coste`, `Riesgo`, `Invariantes` y `Motivado por`, y **54/55** en `Rutas`. El plan
declara en su cabecera que cada ítem lleva esos campos, y es el documento que se va a recorrer con
un script para seguir el avance. **Arreglo:** `**Rutas:**`.

---

## 4. Afirmaciones verificadas

Comprobadas por mí en esta pasada, de solo lectura, y correctas tal como están escritas:

| Afirmación del entregable | Comprobación |
|---|---|
| Las tres bases de la librería R: 93 definiciones en 63 `.R`, 67 en los 37 no-`.Studio.R`, 42 en los 30 no-Studio y no-internos | 63 / 93 / 67 / 42 con el patrón declarado, y 26 ficheros `.Studio.R` |
| Reparto de los siete internos `R4XCL-0-*`: 13, 3, 0, 5, 1, 1, 2 = 25, y ninguno con asignación de descripción | Exacto, fichero a fichero, y 0 atributos en los siete |
| 32 asignaciones de descripción en 25 ficheros (21 con el literal `"description"` en 15 ficheros + 11 con `DialogosXCL$Descripcion` en 11), 31 nombres distintos, 6 de `category` | Exacto, incluidos los 25 ficheros únicos y los 15 + 11 |
| Cero asignaciones en los 26 `.Studio.R` y cero en los siete internos: los 31 nombres con descripción están todos en la base de usuario | Confirmado |
| 12 de los 37 ficheros no-Studio no asignan el atributo, siete internos y cinco de función de usuario, con los cinco nombres que lista §3.4 | Los 12 ficheros son exactamente los que enumera |
| `R4XCL-UT-Pivote.R:336` asigna una cadena simple; `R4XCL-FX-Aleatorios.R:229` repite `FX_AleatorioUniforme` y `FX_AleatorioNormal` (`:167`) queda sin ayuda | Las dos, en esas líneas |
| El puente exige array y asigna los argumentos por posición | `rinterface_common.cc:813` (`"description"`), `:814` (`kArr`), `:834` (`descriptions[0]`), `:843-846` y `:854` (índice) |
| El registro no depende del atributo: `"Exported Function"` en `:292` y `"Argument"` en `:296` | `excel_api_functions.cc:284-292` y `:294-296`, literalmente |
| `.github` no existe en la raíz y el workflow vive bajo `src/.github/` (`MEJ4-01`) | `Test-Path '.github'` → False; `git ls-files` da las cuatro rutas bajo `src/.github/` |
| Las líneas del workflow: `:5` `[ main, develop ]`, `:7` `[ main ]`, `:54` `refs/heads/main`, `:81` la ruta del artefacto | Las cuatro, exactas |
| §8.1: 125 ficheros en producción, 81 idénticos, 20 divergentes, 24 sin origen | Comparación propia por nombre y hash SHA-256 contra los cuatro directorios de origen: 125 / 81 / 20 / 24 |
| `C:\NEVEN\functions`: 63 `.R`, 29 `.json`, 92 scripts ejecutables, **0** `.sha256`; `C:\NEVEN\startup` 0 `.sha256` (`SEC-08`, `A-04`) | 63 / 29 / 92 / 0 / 0 |
| `B-02`: 26 ficheros `test_*.py` con 410 funciones de test, repartidos en seis directorios, 18 ficheros y 331 tests en `src\TaskPane\tests\` | 26 / 410 / seis directorios / 18 y 331 |
| `A-10`: 133 tests en `sandbox_tests.cc` y una red de 158 contando las cuatro suites que desglosa | La distinción está escrita y es coherente con el desglose 133 + 16 + 4 + 2 + 3 |
| 62 invariantes únicas en los cuatro YAML; 50 citadas en los dos entregables; cero inexistentes | Extracción de IDs sobre los cuatro ficheros: 62 y 0 citadas falsas |
| Recuentos internos: 116 hallazgos por eje y severidad; 55 ítems con sus campos; 21/20/14; 5/22/19/9; A 23, B 21, C 11; 113 identificadores en "Motivado por" y tres cierres sin ítem | Recontados uno a uno: cuadran todos, incluido el 113 |
| `00-layout-real.md` §4 tiene 25 filas, 18 de ruta y 7 de cifra o nombre, y la regla que las reduce a 22 y a 6 | Contadas: 25, 18 y 7; la aritmética de §2.2 y de `B-10` se reproduce |
| `Notebooklm.md` restaurado e idéntico a `HEAD` | `git diff HEAD` sin salida; ya no aparece en `git status` |
| Nada escrito en `C:\NEVEN\`; ningún fichero de código modificado; la auditoría se hizo sobre `9eba8b1` en `master`; sin secretos transcritos | 0 ficheros de producción posteriores al 2026-11-20; `git status -- src` vacío; `9eba8b1` era HEAD al empezar esta revisión y los dos commits posteriores (`2255c57`, `8ec60ae`) tocan cinco ficheros de bitácora y hooks y ninguno bajo `src\`; 0 coincidencias de los diez patrones de secreto y 0 del literal del PFX |

---

## 5. Afirmaciones no verificadas o incorrectas

**Incorrectas o incompletas** (desarrolladas arriba): la lista de rutas de `A-13`, que alcanza 10 de
las 12 funciones que el ítem se obliga a cerrar (MEDIUM-1); y la tabla de estado del árbol de §13 y
§9, que publicaba cinco entradas cuando el árbol tenía siete, con una de las omitidas creada ocho
minutos antes de escribirla (MEDIUM-2). La cabecera del informe declara HEAD `9eba8b1`, que era
correcto al cierre de la auditoría y ya no lo es: no es un defecto del documento, pero conviene
saberlo al releerlo.

**No verificadas, y correctamente declaradas como tales.** §9 del informe enumera 19 asuntos con su
motivo, y los marcadores HIPÓTESIS están donde corresponde: explotación de
`SEC-04`/`SEC-05`/`SEC-06`/`SEC-12`, causa de `SEC-11`, efecto del zombie cleanup con dos
instancias, mojibake real en celda, aridad máxima, cargador de `aliases.json`, comportamiento del
modelo ante contenido hostil, veredicto por especificación, qué copia es la correcta en los 20
divergentes, y la entrada sobre el asistente de funciones, que ahora recoge además la pregunta de
población que la pasada anterior había dejado abierta ("qué población aparece realmente en la
lista"). La práctica es correcta y no la repito. La causa del borrado de `Notebooklm.md` se declara
expresamente como no determinada.

**No verificadas por mí, y que esta revisión no comprobó** porque exigen ejecución o un barrido que
no hice: que los 369 tests pasen y el recuento 369/47; el 247 de 369 relacionados con seguridad
(`SEC-24`); los conteos de líneas por lenguaje de §4.1; los índices de `slop_check.py`; el resultado
de `verify_citations.py` sobre `Panko2016`; los 1.118 bytes > 127 de `basic_functions.cc`; las ACL
de `C:\NEVEN` y el tamaño de `neven.log`; las cabeceras PE de `SEC-11` y de `C-10`; el estado de las
27 especificaciones y las 461 casillas; los 30 ficheros con `library()` y los 34 sin `tryCatch` de
`A-13`(a) y (b). Quedan como afirmaciones del informe, no como afirmaciones respaldadas por esta
revisión. Las que sí recomprobé de la pasada anterior se listan en §4.
