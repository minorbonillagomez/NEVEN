# Plan de trabajo de NEVEN

**Fecha:** 2026-11-21 · **Base:** `informe-auditoria.md` (116 hallazgos en cuatro ejes)
**Origen de cada ítem:** los 126 candidatos de los ejes 1-3, consolidados en 55 ítems sin pérdida.
**Layout de referencia:** el prefijo real del código es `src\`; las rutas de este plan son
relativas a `F:\ANTIGRAVITY\2026\NEVEN\` salvo cuando empiezan por `C:\NEVEN\`, que es la
instalación de producción.

## Cómo leer este plan

Los tres grupos son los que pidió el usuario:

- **PENDIENTES** — está roto, o prometido y no cumplido. 21 ítems.
- **POR MEJORAR** — funciona, pero su diseño, su estructura o su coherencia cuesta mantenerla.
  20 ítems.
- **NUEVAS IDEAS** — no existe hoy. 14 ítems.

Cada grupo está ordenado por prioridad. Los identificadores (`A-*`, `B-*`, `C-*`) son estables y
coinciden con `04-notas-mejoras.md`, para que un ítem pueda cerrarse citándolo, que es lo que la
auditoría previa no permitía hacer.

**Prioridad.** `P0` antes de volver a exponer el TaskPane a un usuario · `P1` antes de la
siguiente release o de la entrega de tesis · `P2` siguiente ciclo · `P3` cuando haya hueco.

**Coste.** Jornadas de una persona que ya conoce el proyecto. `S` < 1 día · `M` 1-3 días ·
`L` 4-10 días · `XL` > 10 días. Se da el rango además de la letra.

**Riesgo.** Probabilidad de romper algo que hoy funciona al aplicar el ítem, no gravedad del
problema que resuelve.

### Restricción dura: la ontología manda

Las 62 invariantes de `src\docs\ontologia\neven-core\neven-ontology-p1..p4.yaml` son
restricciones de arquitectura. **Ningún ítem de este plan viola una invariante.** Cada uno declara
las que toca o declara explícitamente que no toca ninguna.

Cuatro ítems exigen **reformular** el texto de una invariante antes de implementarse, y están
recogidos en §5 con la justificación y la redacción propuesta: `A-13` (`INV-LR-04`), `A-11`
(`INV-AS-03`), la parte SQL de `A-01` (`INV-SB-03`) y `A-04` (`INV-CMN-02`). Cuatro invariantes
**nuevas** se proponen para huecos que la ontología no cubre; añadir no contradice. Y §6 recoge
lo que no entra en el plan, incluidas dos decisiones previas del usuario que no se reabren.

---

## 1. Resumen

| Grupo | P0 | P1 | P2 | P3 | Total |
|---|---:|---:|---:|---:|---:|
| PENDIENTES | 5 | 12 | 4 | 0 | **21** |
| POR MEJORAR | 0 | 6 | 11 | 3 | **20** |
| NUEVAS IDEAS | 0 | 4 | 4 | 6 | **14** |
| **Total** | **5** | **22** | **19** | **9** | **55** |

Coste agregado si se hiciera todo: **126-196 jornadas**. Las tres primeras fases de §7, que son
las que cambian el riesgo real del proyecto, suman **26-39 jornadas**.

**El orden no es por severidad, es por dependencia.** Hacer `A-01` sin `B-03` deja los arreglos
sin fijar; hacer `B-19` sin `B-02` repite el incidente de septiembre de 2026 (refactor del
servidor HTTP revertido, TaskPane caído); pasar la integridad a *fail-closed* sin desplegar antes
los hashes deja NEVEN sin funciones. Las dependencias duras están en §8.

---

## 2. PENDIENTES

**Tres hallazgos del informe se cierran sin ítem, y conviene decirlo aquí para que nadie los busque
en el plan.** `COD-21` (no se comprobó que los 369 tests pasen) es la declaración de un hueco de
verificación de esta auditoría, no una tarea: se resuelve ejecutándolos, que es lo que habilita
`B-01` y `B-02`. `COD-26` registra que `INV-NX-01` e `INV-NX-02` se cumplen y que los 54 ficheros
con bytes > 127 no violan ninguna invariante: es un veredicto favorable, no hay nada que hacer.
`COD-52` inventaría las instrucciones dirigidas a agentes que hay en ficheros del repositorio, todas
legítimas, reportadas y no obedecidas (informe §11). Los 113 identificadores restantes aparecen en
el campo "Motivado por" de algún ítem.

### 2.1 Prioridad P0

#### A-01 · Autenticar la API local y cerrar su superficie de escritura y lectura

**Prioridad:** P0 · **Coste:** L, 4-6 jornadas (2-3 el servidor, 2-3 los seis clientes y la
prueba manual de los nueve tabs) · **Riesgo:** Alto.

**Descripción.** Con NEVEN Studio en marcha, `POST /api/{r,python,julia}` ejecuta código
arbitrario en los motores de la sesión del usuario sin token, sin validar `Origin`/`Host` y con
`Access-Control-Allow-Origin: *`; el cuerpo se parsea como JSON sin mirar `Content-Type`, así que
una petición simple no necesita *preflight*. Cinco cambios, en este orden: (1) token aleatorio por
sesión en `%LOCALAPPDATA%\NEVEN\session.token` con ACL del usuario, exigido en cabecera en todas
las rutas `/api/*`; (2) CORS con el origen propio y rechazo de cualquier `Origin` ajeno; (3)
rechazar cuerpos que no sean `application/json`; (4) `_handle_save_script` reducido al patrón que
ya usa `_handle_function_create` (solo nombre base, resuelto contra el directorio configurado, con
`os.path.commonpath`, sin `makedirs`); (5) contención real del servido estático: normalizar
**después** de `unquote`, `realpath` y `commonpath` en las cuatro ramas, copiando el patrón que la
rama `/file?path=` ya aplica bien. En el mismo paquete, por ser la misma superficie: validar los
nombres de columna de `/api/groupby` contra `DESCRIBE dataset` y parametrizar la ruta de
`read_csv_auto`. Mitigación del riesgo: `B-03` en paralelo y una fase de rodaje con el token
exigido pero registrando en lugar de rechazar.

**Rutas:** `src\startup\neven_http_server.py:633-643, 646-649, 652, 933-936, 963-968, 978-983,
1038-1073, 1076-1091, 1110-1112, 2783-2814, 500-514, 2965-2983, 4262-4274`;
`src\TaskPane\start_studio.py` (generación del token); clientes que deben adjuntarlo:
`src\TaskPane\taskpane.html`, `taskpane.js`, `datalab.js`, `audiobook.js`, `chart-gallery.js`,
`ayuda.js`.

**Invariantes:** `INV-SB-01..05` se preservan (mutex, encoding de escritura, límite de
`/api/query`, rate limiter y contexto consumible no cambian). Atención a `INV-CP-03`: si en el
proceso se cambia el puerto, los `postMessage` dejan de validar. **La parte de lista blanca de
funciones de tabla de DuckDB exige ampliar primero `INV-SB-03`** (§5.3), y por eso va separada:
los cinco puntos anteriores no requieren tocar la ontología.

**Motivado por:** `SEC-01` (crítica), `SEC-03` (crítica), `SEC-04` (alta), `SEC-05`, `SEC-06` —
informe §5.3. La sesión del 2026-08-19 evaluó "HTTP server sin auth" y lo clasificó Baja por
"solo localhost"; no es una decisión descartada, es una severidad mal calibrada con información
de entonces: el bind local no excluye a otros usuarios de la máquina ni a páginas del navegador, y
en el intervalo aparecieron `/api/save_script` y el servido estático.

#### A-02 · Puerto propio y bind local para el servidor de audiolibros

**Prioridad:** P0 · **Coste:** M, 2-3 jornadas · **Riesgo:** Medio (el QR y la app Android
dependen de la URL publicada).

**Descripción.** Tres servicios reclaman el 5556 y el de audiolibros es el que pierde; además
`_handle_audiobook_start` da por vivo el servidor con un `connect_ex` a ciegas y el error de bind
se pierde en `DEVNULL`. Asignar un puerto propio (5557) leído de configuración; bind por defecto a
`127.0.0.1`; exposición a la red local como *opt-in* explícito, con aviso en la interfaz y token
de descarga de un solo uso embebido en el QR, que es lo que preserva la transferencia al móvil sin
abrir `/api/*` a la red; y `_handle_audiobook_start` validando `GET /api/health` en lugar de
`connect_ex`, con el `stderr` del hijo a un fichero de log.

**Rutas:** `src\Audiobook\neven_audiobook_server.py:29, 38-45, 376-382`;
`src\Audiobook\api\routes.py` (verificación del token en el *blueprint*);
`src\TaskPane\audiobook.js:20`; `src\Audiobook\start_audiobook_server.bat:38`;
`src\startup\neven_http_server.py:2314-2365`; `src\Install\neven-config.template.json`.

**Invariantes:** **respeta `INV-AS-03` en lugar de contradecirla**, porque deja el 5556 para
AgentService. No toca `INV-SB-01` ni `INV-CP-03`, ya que el 5555 no cambia.

**Motivado por:** `PROD-01` (crítica), `SEC-16` (alta), `PROD-20` — informe §3.2 y §5.3.

#### A-03 · Endpoint de descarga, esquema de las URLs del TaskPane y verificación del arreglo `9eba8b1`

**Prioridad:** P0 · **Coste:** M, 1-2 jornadas de código más media jornada de verificación manual
(requiere Excel, ffmpeg y un motor TTS) · **Riesgo:** Bajo en el endpoint, Medio en el cambio a
rutas relativas, que toca llamadas de todos los tabs.

**Descripción.** El arreglo del commit `9eba8b1` está en producción byte a byte y nunca se
ejecutó. Paso 0: comprobar `document.location.protocol` del TaskPane y pasar las URLs a rutas
relativas, porque si la página se sirve por https las llamadas a `http://localhost:5555` quedan
bloqueadas como contenido mixto, que es la causa probable de que el botón no arranque nada.
Después: quitar el `unquote` redundante, `commonpath` en lugar de `startswith`, **eliminar el
*fallback* por prefijo** (404 si no existe el nombre exacto), codificar como URL el `href` de
`/download`, y unificar la extensión de salida en muxer, pipeline, listados y `mimetype`, porque
hoy el pipeline escribe `.m4a` y todo lo demás busca `.m4b`. Por último, ejecutar el procedimiento
de verificación manual de seis pasos y **registrar el resultado en `.kiro\contexto\CHAT.md`**.

**Rutas:** `src\Audiobook\neven_audiobook_server.py:91-124, 273`;
`src\Audiobook\muxer\ffmpeg_muxer.py:27`; `src\Audiobook\pipeline.py:317, 324`;
`src\Audiobook\api\routes.py:1014, 1112`; `src\TaskPane\audiobook.js:118, 357, 392, 604`;
`src\TaskPane\taskpane.html`, `taskpane.js`.

**Invariantes:** ninguna. El cambio a rutas relativas **ayuda** a `INV-CP-03`, porque deja un solo
origen.

**Motivado por:** `PROD-02` (alta), `PROD-03` (alta), `SEC-17` — informe §7, que incluye el
procedimiento de verificación.

#### B-01 · Mover `src\.github\` a la raíz del repositorio y resucitar el CI

**Prioridad:** P0 · **Coste:** S, media jornada (más 1 jornada si se añade el job que comprueba
las mitigaciones del PE) · **Riesgo:** Bajo; el primer `push` tras el arreglo probablemente falle,
y eso es el objetivo. Hay que reservar presupuesto para vaciar la primera cola de fallos.

**Descripción.** `.github\` no existe en la raíz: el workflow, las dos plantillas de incidencia y
la de *pull request* viven bajo `src/.github/`, y GitHub solo lee `.github/` en la raíz. El CI no
existe, y corregir únicamente el filtro de rama no habría cambiado nada. Mover el directorio y
adaptar el workflow, que asume que el directorio de trabajo es `src\`
(`defaults.run.working-directory: src` o `cmake -S src -B src/Build`). En el mismo paso:
`branches: [ master ]` en los cuatro puntos, la ruta del artefacto (dice
`build/RJ2XCL/Release/NEVEN64.dll` cuando el objetivo produce en `Build/Core/Release/`) y el
`--timeout` de `ctest`.

**Rutas:** `src\.github\**` → `.github\**`; `.github\workflows\build-and-test.yml:5, 7, 13, 54,
81`.

**Invariantes:** ninguna. Habilita la evaluación automática de `INV-TEST-01` y es prerrequisito de
`B-03`, `B-04`, `B-16` y del job de citas de `B-15`. Nota de coste real: con repositorio privado,
los minutos de *runner* Windows se facturan; si eso es un problema, la alternativa es el mismo
script como hook de pre-push local, y entonces hay que decirlo en la documentación en lugar de
mantener un badge que no refleja nada.

**Motivado por:** `MEJ4-01` (alta) y `COD-19` (alta) — informe §2.3 y §6.5.

#### B-02 · Dar runner a los 410 tests de Python

**Prioridad:** P0 · **Coste:** M, 1-2 jornadas de infraestructura más **presupuesto aparte de 2-4
jornadas** para triar los que fallen, que es el coste real y conviene decirlo antes de empezar ·
**Riesgo:** Bajo-Medio, y es de expectativa más que técnico: probablemente una parte de los 410
falle y haya que decidir caso por caso entre arreglar el test o arreglar el código.

**Descripción.** Hay 26 ficheros `test_*.py` con 410 funciones de test sobre `pipe_client`,
`start_studio` y el servidor HTTP, y no existe `pytest.ini`, `pyproject.toml`, `setup.cfg`,
`tox.ini` ni `conftest.py` en todo el repositorio. Añadir `pytest.ini` con `testpaths`, un
`conftest.py` que ponga en `sys.path` el directorio del servidor, y un job de CI que los ejecute.
Los siete runners `.R` sueltos se formalizan como suite aparte, *opt-in* y fuera de
`rj2xcl_tests`, con un comando documentado.

**Los 26 están en seis directorios, no en dos**, y un `testpaths` escrito solo con los dos obvios
deja cinco fuera. Por eso la recomendación es `testpaths = src` con `norecursedirs` explícito
(`Build`, `Dist`, `_deps`, `Releases`, `__pycache__`, `external`) en lugar de una lista de
directorios de tests, y comprobar que `--collect-only` recoge 26 ficheros.

**Rutas:** raíz de `src\` (`pytest.ini`, `conftest.py`); `src\TaskPane\tests\` (18 ficheros, 331
tests); `src\tests\test_datalab_handler.py`, `test_skill_loader.py`,
`test_package_manager_service.py`; y los cinco que quedan fuera de esos dos directorios:
`src\ControlPython\startup\test_sheet_analyzer.py`, `src\scripts\ontology\test_forensic_enrichment.py`,
`src\scripts\ontology\test_wiley_search.py`, `src\startup\test_rag_queries.py` y
`src\Install\scripts\test_rag_queries.py` —estos dos últimos son el mismo fichero duplicado byte a
byte, así que además son un caso de `B-08`—; los 7 runners `.R` de `src\tests`;
`.github\workflows\build-and-test.yml`.

**Invariantes:** ninguna. `INV-TEST-03` se respeta manteniendo fuera del objetivo GTest los tests
que necesitan motores. Es **prerrequisito duro de `B-03` y de `B-19`**.

**Motivado por:** `COD-22` (alta) — informe §4.3.

### 2.2 Prioridad P1

#### A-04 · Hacer real la integridad de los scripts desplegados

**Prioridad:** P1 · **Coste:** M, 2-3 jornadas · **Riesgo:** Alto **si se invierte el orden**:
pasar a *fail-closed* antes de desplegar los hashes deja NEVEN sin funciones.

**Descripción.** La verificación devuelve `true` cuando falta el fichero `.sha256`, y en
producción hay **0** `.sha256` para los 92 scripts de `C:\NEVEN\functions` y los 3 de
`C:\NEVEN\startup`; el repositorio sí tiene los de `startup.r` y `startup.jl`, así que el control
existe y el instalador no lo despliega. Cuatro pasos, en este orden y sin invertirlo: (1) el
instalador genera y despliega un `.sha256` por cada `.R`/`.jl`/`.py`; (2) `Sync-Dist.ps1` los
regenera en cada sincronización; (3) **solo entonces**, pasar la verificación a *fail-closed* con
registro explícito del fichero rechazado; (4) corregir el texto de la invariante y de
`SECURITY.md`, que dicen HMAC donde el código hace SHA-256 sin clave.

**Rutas:** `src\Common\Security\SecurityService.cc:34-40`; `src\Install\Install-NEVEN.ps1`;
`src\Install\Sync-Dist.ps1`; `src\docs\ontologia\neven-core\neven-ontology-p1.yaml:347`;
`src\SECURITY.md`.

**Dependencia de insumo, no solo de orden.** El paso 1 genera hashes *desde una fuente*, y hoy esa
fuente no está decidida para 41 de los 125 ficheros de `C:\NEVEN\functions`: 20 divergen entre
repositorio y producción y 21 solo existen en producción (informe §8.1). Generar los hashes antes de
que `B-08` resuelva eso significa, para los divergentes, firmar la copia equivocada, y para los
huérfanos, firmar un fichero del que nadie responde. Por eso `B-08` no es una preferencia de orden.

**Invariantes:** **cierra `INV-CMN-02`**, hoy violada en producción, y **requiere reformular su
texto antes** (§5.4). El paso 3 necesita que `B-08` esté hecho: cada actualización manual de un
`.R` en producción que no regenere su hash provoca el mismo efecto que invertir el orden.

**Motivado por:** `SEC-08` (alta) — informe §5.3 y §8.1.

#### A-05 · Endurecer las ACL del directorio de producción

**Prioridad:** P1 · **Coste:** M-L, 3-4 jornadas (la mayor parte es inventariar y probar las
escrituras del runtime, no escribir el `icacls`) · **Riesgo:** Alto: una ACL de más deja a NEVEN
sin poder escribir sus propios ficheros de trabajo, y el síntoma aparece lejos del cambio.
Mitigación: aplicar primero en una instalación de prueba (`B-11`), nunca en la instalación viva.

**Descripción.** `C:\NEVEN`, `C:\NEVEN\functions` y `C:\NEVEN\certs` tienen
`Authenticated Users : Modify` heredado de la raíz `C:\`, y el instalador no llama a `icacls` ni a
`Set-Acl` en ningún punto. Cualquier cuenta local puede reescribir los 92 scripts que se ejecutan
por hot-reload, `neven-config.json` (incluido `sandboxEnabled`), los binarios que Excel carga, la
clave privada PEM del certificado de confianza y el `neven.log` que invoca `SECURITY.md` como
rastro de auditoría. Bloque de endurecimiento en el instalador: quitar la herencia y conceder
escritura solo a Administradores, SYSTEM y al usuario instalador; lectura al resto. **Antes** hay
que enumerar lo que el runtime necesita escribir (`data\`, `workspace\`, `graphics\`, `output\`,
`logs\`, `neven.log`, y `functions\` si se mantiene la creación de funciones desde el TaskPane) y
decidir para cada uno entre ACL propia o traslado a `%LOCALAPPDATA%`. El desinstalador debe
revertirlo.

**Rutas:** `src\Install\Install-NEVEN.ps1` (bloque nuevo), `src\Install\Uninstall-NEVEN.ps1`.

**Invariantes:** **ninguna de las 62 cubre las ACL del directorio de producción: es un hueco, no
una violación.** Se propone añadir una invariante (§5.5a). **No se propone mover `C:\NEVEN\`**: lo
asumen `INV-SR-01..05`, `INV-CMN-02`, `INV-SB-01..05` y rutas absolutas del código, de los
scripts y del instalador.

**Motivado por:** `SEC-09` (alta), `SEC-10`, `PROD-19` — informe §5.3 y §8.

#### A-06 · `/guard:cf` en el enlazado del XLL principal

**Prioridad:** P1 · **Coste:** S, 2-4 horas de cambio más el tiempo de reconstruir y redesplegar ·
**Riesgo:** Bajo técnicamente, Medio operativamente: obliga a regenerar y redesplegar el XLL con
Excel cerrado.

**Descripción.** `NEVEN64.xll` se distribuye con `DllCharacteristics = 0x0160`, sin Control Flow
Guard, en `src\Build\Dist`, `src\Install\Dist` y `C:\NEVEN`. Todos los demás binarios sí lo
llevan; el único que falta es el que Excel carga en su propio proceso. Añadir `/guard:cf` a
`add_link_options`, reconstruir y volver a leer los dos bytes de `DllCharacteristics`, que deben
pasar a `0x4160`. Verificar también `CETCOMPAT`, que vive en el *load config* extendido.

**Rutas:** `src\CMakeLists.txt:24`; comprobar `src\Core\CMakeLists.txt:5-7` (`NEVEN_Core` es el
único objetivo construido a través de una *object library*, que es la causa probable).

**Invariantes:** **cierra `INV-BLD-02`** en el artefacto, que es donde está incumplida. No se
quita ningún flag, así que `INV-TEST-01` sigue pasando e `INV-BLD-01` queda intacta.

**Motivado por:** `SEC-11` — informe §5.3.

#### A-07 · Guarda de excepciones en los cuatro exports del XLL

**Prioridad:** P1 · **Coste:** S, 2-4 horas · **Riesgo:** Bajo. Es independiente de todo lo demás
y cabe en cualquier hueco.

**Descripción.** `xlAutoOpen` ejecuta `Init()` completo sin ningún `try`/`catch`: configuración,
`json11` (que lanza con JSON malformado), creación de directorios, `taskkill`,
`ConnectLanguages()`, `MapFunctions()` y `RegisterFunctions()`. Lo mismo `xlAutoClose`. Una
excepción C++ que cruce un `extern "C" __stdcall` invocado por Excel es comportamiento indefinido:
en la práctica Excel termina sin mensaje y sin entrada en el log. Envolver el cuerpo de los cuatro
exports y registrar antes de devolver, como ya hace `OnConnection` del Ribbon por exigencia de
`INV-RIBBON-02`. Añadir en el mismo paso el null-check de `xlAutoFree12` y revisar los estáticos
mutables compartidos de `xlAddInManagerInfo12`, que es el cuarto export y el que menos atención ha
recibido.

**Rutas:** `src\Core\src\rj2xcl.cc:619-651, 653-668, 670-686, 690-707` (el estático mutable, en
`:691`).

**Invariantes:** ninguna. La envoltura no cambia el orden ni el contexto, así que `INV-CORE-01`,
`INV-CORE-02`, `INV-CORE-03` e `INV-CORE-04` se preservan.

**Motivado por:** `COD-01` (alta), `COD-03`, `COD-04` — informe §4.3.

#### A-08 · Política única de `srcdoc` en el TaskPane

**Prioridad:** P1 · **Coste:** S, 4-8 horas más la prueba de las visualizaciones · **Riesgo:**
Medio: hay que comprobar con Plotly, D3, Leaflet y KaTeX que ningún contenido de `srcdoc` dependa
de alcanzar el documento padre. Los botones "Enviar a Slide" y de descarga viven fuera del iframe,
así que la expectativa es que no se rompa nada.

**Descripción.** Tres rutas renderizan HTML producido por los motores con tres políticas
distintas: una usa `sandbox="allow-scripts allow-same-origin"`, que es la combinación que anula el
aislamiento, y las otras dos no ponen `sandbox`. Dejar una sola política,
`sandbox="allow-scripts"` sin `allow-same-origin`, y escapar el contenido en los sumideros que no
necesitan HTML.

**Rutas:** `src\TaskPane\datalab.js:1593-1599`; `src\TaskPane\chart-gallery.js:1770`;
`src\TaskPane\taskpane.js:1235`.

**Invariantes:** avanza `INV-TF-01` (una sola política de renderizado). `INV-TF-04` intacta:
cambiar un atributo no requiere empaquetador.

**Motivado por:** `SEC-07` (alta) — informe §5.3.

#### A-12 · WebView2 en el preflight del instalador

**Prioridad:** P1 · **Coste:** M, 1-2 jornadas · **Riesgo:** Bajo.

**Descripción.** El instalador tiene cero ocurrencias de `WebView2`, y de ese runtime cuelga toda
la interfaz: TaskPane, visor, editor, Pluto y Quarto. El código ya tiene los mensajes de fallo
preparados en seis puntos. Detectar el runtime por su clave de registro y, en su ausencia, ofrecer
la descarga del *bootstrapper* o incluirlo como prerrequisito del NSIS si se quiere instalación
desatendida. Añadirlo a `Show-PreflightSummary` con el mismo formato que los motores, que ya está
bien resuelto.

**Rutas:** `src\Install\Install-NEVEN.ps1` (`Show-PreflightSummary`, L383-446);
`src\Install\NEVEN-Setup.nsi`; `src\docs\Arquitectura\Dependencias_Instalacion.md`.

**Invariantes:** ninguna.

**Motivado por:** `PROD-05` (alta) — informe §3.2.

#### A-13 · Librería R: `requireNamespace`, `tryCatch`, HC3 y atributos de ayuda

**Prioridad:** P1 · **Coste:** L, 5-7 jornadas · **Riesgo:** Medio: son 63 ficheros de código que
el usuario final usa, y sin los runners `.R` convertidos en suite la verificación es manual.
Hacerlo por familias (`RG`, `AD`, `GR`, `ST`), no de golpe.

**Descripción.** Cuatro defectos sobre los mismos ficheros. (a) 30 tienen `library()` de nivel
superior, y un paquete ausente tumba el `source()` completo, de modo que el usuario pierde todas
las funciones del fichero y no solo la que lo necesitaba. (b) 34 no tienen ningún `tryCatch`, así
que un error rompe el contrato de retorno `R4XCL_`. (c) Los errores estándar robustos usan HC0
(`vcovHC(type="HC")`), cuando para 30-200 filas la recomendación es HC3: es una cadena. (d) **De las
42 funciones de usuario de la librería, 30 tienen ayuda efectiva y 12 no** (11 que nunca declaran el
atributo más una que lo declara como cadena y por eso es inerte), así que el asistente de funciones
de Excel les muestra "Exported Function" y "Argument". Esa es la base sobre la que trabaja este ítem
y la que hay que usar para medir si está cerrado; la cifra bruta equivalente es 63 de 93
definiciones, pero incluye 26 `.Studio.R` y 25 internas que este ítem **no** toca (informe §2.2
y §3.4). Barrido: `library()` → `requireNamespace(..., quietly=TRUE)` dentro de `tryCatch`;
envolver el cuerpo analítico con `error = function(e) data.frame(R4XCL_Error = conditionMessage(e))`;
`type = "HC3"` o parámetro con HC3 por defecto; y extender la convención de ayuda a las funciones
que no la tienen.

**La convención de (d) ya existe y hay que seguirla, no inventar otra** (informe §3.4). El valor del
atributo es una `list()`, nunca una cadena: el puente de R descarta el atributo si no llega como
array (`src\ControlR\src\rinterface_common.cc:813-818`). El primer elemento es la descripción de la
función y los siguientes se asignan a los argumentos **por posición**, de modo que su orden debe
coincidir con `formals()` y sus nombres son documentación para quien lee el `.R`:

```r
attr(MiFuncion, "description") = list(
  "Descripción de la función, menos de 250 caracteres",
  SetDatosX  = "Ayuda del primer argumento",
  TipoOutput = "Ayuda del segundo argumento"
)
attr(MiFuncion, "category") <- "Analisis de Datos"   # cadena, no list()
```

Las dos formas de nombrar el atributo son equivalentes y las dos se quedan: `"description"`
literal (21 asignaciones) y `DialogosXCL$Descripcion` (11), que vale exactamente `"description"`
(`src\libreria\R\R4XCL-0-Interno-2.R:242`). Cualquier barrido o test que se escriba tiene que
aceptar las dos, o marcará como incumplidoras a 11 funciones que sí cumplen.

Dos arreglos puntuales dentro de (d), ya localizados: `R4XCL-UT-Pivote.R:336` asigna una cadena a
`DB_Recodificar` y por eso no surte efecto, y `R4XCL-FX-Aleatorios.R:229` repite
`FX_AleatorioUniforme` donde debía poner `FX_AleatorioNormal` (definido en `:167`), que se queda sin
ayuda.

**Rutas:** los 30 ficheros con `library()` y los 34 sin `tryCatch` de `src\libreria\R` (listas en
`02-notas-codigo.md` §5); `src\libreria\R\R4XCL-RG-Lineal.R:124`; `R4XCL-UT-Pivote.R:336`;
`R4XCL-FX-Aleatorios.R:229`; y los cinco ficheros de función de usuario sin ningún `attr(`:
`R4XCL-AD-NonParRolCor.R`, `R4XCL-BD-ObtieneDatos.R`, `R4XCL-DS-Wooldridge.R`, `R4XCL-GR-Mapa.R`,
`R4XCL-NEVEN-pluto-read.R`. **Fuera del alcance de (d):** los 26 `.Studio.R` y los siete internos
`R4XCL-0-*`, que son 51 de las 93 definiciones.

**Precisión sobre los `.Studio.R`, para no cerrar este ítem con una premisa falsa.** No es cierto
que no aparezcan en el asistente de funciones de Excel: están desplegados en `C:\NEVEN\functions` y
el cargador no distingue su extensión (informe §2.2 y §3.4), de modo que hoy se registran y se
listan con el texto de respaldo. Quedan fuera de este ítem porque documentarlos como funciones de
celda contradice su propósito, no porque sean invisibles. La decisión coherente —dejar de
desplegarlos al directorio de funciones y servirlos solo a DataLab— es un cambio de empaquetado y
pertenece a `B-08`. Este ítem no la toma ni la bloquea.

**Invariantes:** **cierra `INV-LR-02`** (hoy violada en 30 ficheros) y **refuerza `INV-LR-03` e
`INV-NX-04`**. Los atributos de ayuda **exigen reformular `INV-LR-04` antes** (§5.1): no por el
mecanismo, que sí existe, sino porque la invariante afirma una consecuencia falsa, no fija el tipo
del valor y su `como_verificar` solo detecta una de las dos formas en uso. `INV-SR-05` manda el
método de despliegue: `UTF8Encoding($false)`, nunca `[System.Text.Encoding]::UTF8`.

**Motivado por:** `PROD-08` (alta), `PROD-17`, `COD-27`, `COD-28`, `COD-29`, `COD-30`, `COD-31` —
informe §3.2, §3.4 y §4.3.

#### B-08 · Una sola fuente por artefacto desplegado, y paridad medible con producción

**Prioridad:** P1 · **Coste:** M-L, 3-4 jornadas · **Riesgo:** Medio: la copia muerta
`C:\NEVEN\taskpane\neven_http_server.py` es producción viva y retirarla exige ventana de
mantenimiento, no se toca en frío. El script de paridad es de solo lectura, así que esa parte no
tiene riesgo.

**Descripción.** Tres problemas de la misma familia. (1) `neven_http_server.py` existe en cinco
rutas con cinco hashes distintos, y la regla de steering señala como destino de sincronización la
copia divergente del 19 de octubre: quien la siga al pie de la letra copia hacia atrás 17 días de
trabajo. `datalab_handler.py` no existe junto al servidor canónico, y `test_rag_queries.py` está
duplicado byte a byte en `src\startup\` y `src\Install\scripts\`. (2) `src\Install\functions\` es un
segundo directorio de librería no declarado: ocho ficheros de función tienen ahí su única copia del
repositorio y dos existen también en `src\libreria\R\` con contenido distinto (`MEJ4-05`). (3) La
instalación viva no es reproducible en ninguna de las dos direcciones (informe §8.1): 21 artefactos
ejecutables solo existen en producción, 20 ficheros comparten nombre con distinto contenido y 11 del
repositorio nunca se desplegaron.

Trabajo: declarar `src\startup\` fuente única del servidor y de sus módulos; borrar las copias
divergentes tracked; mover `datalab_handler.py` junto al servidor o declarar formalmente su origen;
**corregir la regla de steering**; y decidir por escrito qué directorio es la fuente de los ficheros
de función. Producción sigue hoy a `src\libreria\R\` en los dos divergentes, así que lo coherente es
mover los ocho de `src\Install\functions\` a `src\libreria\R\` y dejar ese directorio solo con
sidecars y documentación. Por último, escribir un **script de solo lectura** que reproduzca el inventario de
§8.1 por nombre y hash, con cuatro salidas: idénticos, divergentes (con fecha y tamaño de los dos
lados), solo en producción y solo en el repositorio. Ese script es el que después alimenta `A-04`.

**Aviso para quien lo ejecute:** dos divergentes tienen **más** contenido en producción que en el
repositorio (`R4XCL-0-UT-InstalaPaqueterias.R`, `R4XCL-AD-ACP.R`), así que no hay dirección segura
por defecto. Cada uno de los 20 se resuelve leyendo su diff, no sincronizando en bloque.

**Rutas.** Servidor y módulos: `src\startup\`; `src\TaskPane\neven_http_server.py`;
`src\ControlPython\startup\neven_http_server.py` y `datalab_handler.py`;
`src\Install\scripts\rag_engine.py`; `src\startup\test_rag_queries.py` y
`src\Install\scripts\test_rag_queries.py`. Librería de funciones: `src\libreria\R\`,
`src\libreria\JULIA\`, **`src\libreria\PYTHON\`** y `src\Install\functions\` (los ocho de copia
única y los divergentes `RG_2SLS.Studio.R` y `RG_HECKIT.Studio.R`). Sin origen en producción, a
resolver uno por uno: los 14 `.py` de `C:\NEVEN\functions` listados en el informe §8.1,
`Ejemplo_J.jl`, `J4XCL-ML-Avanzado.jl`, `R4XCL-0-NevenX.jl`, `Ejemplo_R.r`,
`R4XCL-RG-ML-Avanzado.R`, `R4XCL-UT-Paquetes.R` y `NEVEN_Chart.json`. Regla de steering:
`.kiro\steering\neven-pre-cambios.md:142-145`. Script nuevo en `src\scripts\`.

**Invariantes:** ninguna se viola. `INV-BLD-03` se respeta: las dos copias de `Dist\` son
artefactos no tracked y se regeneran. `INV-SJ-01..05` condicionan cualquier movimiento de sidecar.
`INV-SR-05` manda el método de copia de los `.R`. Se propone **añadir** una invariante de fuente
única (§5.5d).

**Motivado por:** `COD-36` (alta), `COD-39`, `PROD-29`, `MEJ4-05` (media) — informe §4.3, §6.5, §8.1
y §8.2.

#### B-10 · Higiene documental: prefijos de ruta y cifras con una sola fuente

**Prioridad:** P1 · **Coste:** M, 2-3 jornadas (la media jornada extra es la reescritura de la
parte desfasada de `SECURITY.md` y de la evaluación OWASP) · **Riesgo:** Nulo.

**Descripción.** Seis desajustes documentales, dos de ellos estructurales y cuatro puntuales.
(a) 22 referencias documentales apuntan a
`NEVEN\NEVEN\…`, un árbol que desapareció en el commit `951cfcb`; entre ellas el propio steering
que una sesión de trabajo está obligada a seguir, el hook de validación y `MIGRACION.md`, que
describe el árbol anterior como si fuera el actual. (b) El número de tests aparece como 228, 342 y
357 en cuatro documentos y el real es 369; la librería R se documenta como 32 ficheros con ~90
procedimientos y tiene 63 ficheros con 93 definiciones; la sysimage como 415 MB y mide 1,04 GB.
Corregir las 22 referencias y escribir un **script único**
que lea `--gtest_list_tests` y el conteo de pytest, mida los ficheros y las definiciones de la
librería y el tamaño de la sysimage, y actualice el README, el badge,
`Aseguramiento_de_calidad.md`, `SECURITY.md`, el steering, el bloque `tamanos_referencia` de
`neven-ontology-p4.yaml` y el manifiesto de consistencia del paper desde esa única fuente. El
script debe **publicar el patrón con el que mide y la base que cuenta**, no solo el número: contar
definiciones de R aceptando solo `<-` da 83 y aceptando `<-` y `=` da 93, y las tres bases
legítimas dan 93 (bruta), 67 (no-Studio) y 42 (funciones de usuario). Una cifra sin el patrón y la
base al lado no es verificable por el siguiente lector, y es el defecto que esta auditoría tuvo que
corregir en sus propias mediciones (informe §2.2). Reescribir
`coding-standards.md` para que describa lo que el código hace, y borrar su duplicado.

En el mismo paquete, por ser la misma clase de defecto: (c) `SECURITY.md` y la evaluación OWASP
describen un sistema que ya no es este: cifras de tests que no coinciden, un 9/10 apoyado en una
función sin invocadores, y ni una mención de los puertos 5555/5556, del TaskPane, del servidor de
audiolibros ni del visor. Aquí se corrige solo la parte documental; los controles que
faltan son `A-01`, `A-10` y `A-18`. (d) `src\README.md` puntúa 10,0 en índice de relleno con frases
de 39,5 palabras de media, mientras las dos guías de usuario puntúan 0,0: se reescribe el README
tomándolas como referencia. (e) La deuda de este informe no está marcada en ningún punto del código
(28 marcadores `TODO`/`FIXME` en todo `src`), lo que se resuelve con la norma del comentario con
identificador de `B-18`. (f) `testing-guide.md` tiene BOM y sus dos vecinos de `src\docs\sops\` no.

**Rutas:** los 22 puntos de `00-layout-real.md` §4. **Esa sección tiene 25 filas, no 22**: son 18 de
ruta y 7 de cifra o nombre; de las 18 se excluyen las 2 del workflow de CI, que van en `B-01`, y la
fila de `.kiro\steering\neven-project-context.md:58-66` cuenta como los siete documentos que
enumera (18 − 2 − 1 + 7 = 22). Las 7 de cifra se reducen a 6 porque las dos del `README` son la
misma afirmación (informe §2.2). Además: `src\README.md:7, 19, 150, 176`;
`src\docs\Mantenimiento\Aseguramiento_de_calidad.md:7`; `src\SECURITY.md:160-168, 181-192`;
`src\docs\Evaluaciones\Evaluacion_OWASP.md:16, 82, 214-224`;
`src\docs\ontologia\neven-core\neven-ontology-p4.yaml:164` (dice `"~414MB"` de la sysimage frente a
1,04 GB medidos: es corrección de un dato descriptivo del YAML, **no** cambio de invariante);
`.kiro\steering\neven-project-context.md:58-66, 90`; `.kiro\steering\neven-pre-cambios.md:142-145`;
`MIGRACION.md`; `src\docs\sops\coding-standards.md` y `src\docs\Plan_trabajo\coding-standards.md`;
`src\docs\sops\testing-guide.md:26`; `.kiro\skills\rj2xcl-docs\SKILL.md`; nuevo script en
`src\scripts\`.

**Invariantes:** ninguna. El cambio en `neven-ontology-p4.yaml` toca el bloque
`tamanos_referencia`, que es descriptivo, y no el texto de ninguna `INV-*`. **No se propone
refactorizar los 596 métodos** para que cumplan el documento: el documento es el que está mal
(§6.5).

**Motivado por:** informe §2.2 (22 referencias y seis cifras), `COD-20`, `COD-47`, `COD-48`,
`COD-11`, `COD-12`, `COD-53`, `COD-56`, `PROD-27`, `SEC-22` (media), `LAY-03`.

#### B-15 · El paper como entregable de tesis

**Prioridad:** P1. Es una tesis: una cita que apunta a otro trabajo es el tipo de defecto que
genera una corrección posterior a la publicación · **Coste:** M, 2-3 jornadas más el tiempo del
autor para obtener el DOI correcto · **Riesgo:** Nulo-Bajo.

**Antes de tocar las cifras de (b), fijar la base de conteo.** La afirmación publicada sobre R
("over 70 R procedures") se sostiene con la base bruta (93 definiciones en los 63 `.R`) y con la
no-Studio (67), y **no** con la base de funciones de usuario (42). Lo defendible es publicar la
bruta **diciendo qué cuenta**, en una nota al pie: "definiciones de nivel superior en el directorio
de funciones, incluidos los scripts de DataLab y los internos". Sin esa nota, un revisor que mida
por su cuenta con otro criterio obtiene otro número y la afirmación queda en entredicho. Las tres
bases y su patrón están en informe §2.2, y el generador único de `B-10` debe emitirlas con su
etiqueta.

**Descripción.** Cuatro asuntos. (a) El DOI de `Panko2016` apunta a un artículo de otro autor del
mismo número de la revista; **el autor debe obtenerlo de la página del editor, no de la memoria**,
porque solo él sabe qué artículo quiso citar. Conviene confirmar también `Quarto2023`, que es
probable falso positivo. (b) Las cifras publicadas no coinciden con el repositorio: 342 tests
frente a 369, 70 procedimientos Julia frente a 60, "más de 200 funciones numéricas" no verificable
y la ruta `Documents\NEVEN\functions\` que no se usa. (c) Tres árboles del paper coexisten y
`05_discussion.tex` divergió; el artefacto de conteo que la regla del proyecto prohíbe existe solo
en la copia muerta. (d) Ocho entradas del `.bib` nunca se citan. Corregir, atar las cifras al
generador único de `B-10` mediante un manifiesto de consistencia, consolidar los árboles, y añadir
al CI un job que ejecute `bib_lint.py` y `verify_citations.py` guardando el informe JSON junto al
`.tex`.

**Rutas:** `src\docs\Paper\references.bib` y `arxiv-submission\references.bib`;
`src\docs\Paper\sections\06_conclusion.tex:11`, `02_architecture.tex:60, 172`,
`03_viewer_extensibility.tex:68, 83`; `src\docs\Paper\sections_old\`; `.github\workflows\` (job
nuevo).

**Invariantes:** ninguna. La regla del proyecto que aplica es
`.kiro\steering\ai-artifact-prevention.md`, y hoy **se cumple** (`COD-51`): cero campos `note`,
cero puntos dentro de `\paragraph{}`, em-dashes de prosa prácticamente nulos y números de lista
coherentes con los ítems.

**Motivado por:** `COD-46` (alta), `COD-47`, `COD-48`, `COD-49`, `COD-50`, `PROD-24` y `COD-51`
(informativo favorable: es la línea base de higiene anti-artefacto que este ítem debe conservar al
reescribir) — informe §4.3.

#### B-21 · Declarar el estado de las 27 especificaciones

**Prioridad:** P1. Es el insumo directo del plan de trabajo · **Coste:** M, 1-2 jornadas ·
**Riesgo:** Nulo.

**Descripción.** Las 461 casillas sin marcar de `.kiro\specs\` mezclan tres situaciones que no se
distinguen: funcionalidad implementada sin cerrar la especificación (43 casillas en
`nevenx-dispatcher` y `neven-v3-taskpane`, que describen cosas que existen y funcionan),
funcionalidad nunca empezada, y especificaciones obsoletas o ajenas (50 casillas de
`ontology-engine-framework`, que describe la migración de un esquema de base de datos ajeno al
add-in; 28 de `ai-integration`, superada por la implementación y origen documental de `PROD-06`).
La deuda real son unas 207, no 461. Marcar lo implementado; mover a `.kiro\specs\_archivo\` lo
obsoleto y lo ajeno con una nota de una línea; dejar en activo solo lo vigente.

**Rutas:** `.kiro\specs\**\tasks.md` (19 con casillas abiertas); `.kiro\specs\_archivo\` (nuevo).

**Invariantes:** ninguna.

**Motivado por:** `MEJ4-06` (media), `MEJ4-07` — informe §6.5 y §6.6.

#### C-10 · Decidir el alcance de NEVEN-SIM

**Prioridad:** P1 la decisión · **Coste:** S, media jornada la decisión; XL el corte vertical si
se elige hacerlo · **Riesgo:** Nulo la decisión.

**Descripción.** NEVEN-SIM existe como XLL separado con 37 ficheros, tiene su propio
`CMakeLists.txt` y sus propios tests, su `SIM_QuickSim` de 250 líneas está exportado, consume las
colas de `PostMessageBridge` y está desactivado por defecto en el build. Su especificación es la
más grande del proyecto y tiene cero tareas marcadas. Nadie sabe, leyendo el repositorio, si es un
módulo del producto o un prototipo. La decisión: o se define un corte vertical mínimo (una
simulación Monte Carlo de extremo a extremo, con su sidecar, su documentación y su activación en
el instalador) y se cierra el resto de la especificación como futuro, o se declara experimental y
se saca de la narrativa del producto y del paper. Lo que no conviene es dejar 109 tareas abiertas
compitiendo por atención con los arreglos de P0.

**Rutas:** `.kiro\specs\neven-sim\tasks.md` (la decisión); `src\CMakeLists.txt:96-97`;
`src\docs\Arquitectura\Arquitectura.md`; `src\docs\Paper\sections\` si se menciona.

**Invariantes:** ninguna. `INV-BLD-01/02` aplican a NEVEN-SIM como a todos los binarios, y su
`NEVEN-SIM.xll` de producción **sí** lleva CFG (`0x4160`), al contrario que el XLL principal
(`A-06`).

**Motivado por:** `MEJ4-06` — informe §6.6; `src\NEVEN-SIM\` y `.kiro\specs\neven-sim\` (109
tareas abiertas, 0 marcadas).

### 2.3 Prioridad P2

#### A-17 · `NEVEN.Notebook.Export` nunca puede funcionar: cablear `CaptureAnalysis`

**Prioridad:** P2 · **Coste:** M, 1-2 jornadas (más `C-05` si se quiere la capacidad completa) ·
**Riesgo:** Bajo.

**Descripción.** `=NEVEN.Notebook.Export(Title)` está registrada y anunciada al usuario en el
asistente de Excel como "Export last analysis as Pluto notebook", y `CaptureAnalysis` no tiene
ningún invocador en todo el árbol, de modo que `has_analysis_` es siempre falso y la función
devuelve invariablemente "No analysis to export". Llamar a `CaptureAnalysis` donde se completa una
ejecución con éxito, completar la lista de orden de celdas del notebook generado (hoy cierra sin
listar ningún UUID, lo que probablemente lo invalide para Pluto) y corregir el Doxygen, que
anuncia un HTML autónomo mientras el código escribe un `.jl`. Si se decide que la captura no
interesa, retirar la función del registro: lo que no debe quedar es una función anunciada que
siempre falla.

**Rutas:** `src\Common\NotebookExporter.cc:29, 43, 180`, `NotebookExporter.h:33`;
`src\Core\src\basic_functions.cc:914`; `src\Core\include\basic_functions.h:62`;
`src\Core\src\language_service.cc` (punto de captura).

**Invariantes:** ninguna. La función ya está en `funcTemplates`, así que se registra durante
`xlAutoOpen` y `INV-CORE-01` se respeta sin cambios.

**Motivado por:** `MEJ4-02` (media) — informe §6.5.

#### A-20 · Documentación de usuario y catálogo: lo que engaña activamente

**Prioridad:** P2 · **Coste:** M, 2-3 jornadas · **Riesgo:** Nulo en los documentos; Bajo en
`es.js`.

**Descripción.** Seis cosas que hacen fallar a quien sigue la documentación. (a) El diccionario
cita `NEVEN.py`, `NEVEN.q` y `NEVEN.v`, que no existen: los nombres reales son `NEVEN.P`,
`NEVEN.Quarto` y `NEVEN.View`, de modo que copiar la fórmula da `#¿NOMBRE?`. (b)
`SIDECAR_FORMAT.md` declara que el código va a `C:\NEVEN\libreria\R\` cuando el valor real y
configurado es `C:\NEVEN\functions\`. (c) El paper sitúa las funciones del usuario en
`Documents\NEVEN\functions\`. (d) 25 claves de función existen solo en inglés, de modo que en un
proyecto hispanohablante la versión española del catálogo es la incompleta. (e) `aliases.json` vive
entre los sidecars sin ser uno, y los nueve `GR_*.Studio.R` no tienen sidecar; antes de escribirles
uno hay que resolver que **tampoco están desplegados** en `C:\NEVEN\functions` (informe §8.1). La
decisión previa es si son DataLab vivo sin desplegar, y entonces entran en `B-08` y se les escribe
sidecar, o código muerto del repositorio, y entonces se retiran. Escribir nueve
sidecars para ficheros que no se ejecutan es trabajo perdido. (f) Las carpetas de trabajo del
módulo de audiolibros no son las que sugiere su nombre: la salida real es `C:\NEVEN\output`, no
`C:\NEVEN\Audiobook\output`, y nada lo documenta, así que quien busque un audiolibro generado no lo
encuentra y quien lea el código supone la ruta equivocada.

**Rutas:** `src\docs\Contexto\Diccionario_Funciones.md`; `src\docs\SIDECAR_FORMAT.md`;
`src\docs\Paper\sections\02_architecture.tex:60, 172`, `03_viewer_extensibility.tex:68, 83`;
`src\TaskPane\lang\es.js`, `en.js`; `src\Install\functions\aliases.json`;
`src\libreria\R\GR_*.Studio.R` y `src\Install\functions`;
`src\Audiobook\neven_audiobook_server.py:48-52, 116` y `src\Audiobook\README.md` para (f).

**Invariantes:** `INV-TF-03` en el despliegue de `es.js` (copiar con `[System.IO.File]::Copy()`);
`INV-SJ-01..05` en los sidecars nuevos. Ninguna se viola.

**Motivado por:** `PROD-07` (alta), `PROD-11`, `PROD-12`, `PROD-15`, `PROD-21`, `PROD-24`,
`PROD-26` — informe §3.2 y §8.1.

#### B-11 · Empaquetado, instalación y la prueba en máquina limpia

**Prioridad:** P2, salvo la prueba en máquina limpia, que es P1 · **Coste:** L, 5-7 jornadas más
el tiempo de preparar una VM · **Riesgo:** Medio: tocar el instalador afecta a la única vía de
despliegue. Probar siempre en VM y nunca contra la instalación viva.

**Descripción.** El instalador tiene cero ocurrencias de `Audiobook`, `ffmpeg` y `piper`, mientras
el servidor codifica la ruta absoluta `C:\NEVEN\Audiobook\neven_audiobook_server.py` y responde
404 si no existe: en una instalación limpia el tab de audiolibros no puede funcionar, y el módulo
llegó a producción por copia manual. Tampoco se declaran `flask`/`flask_cors`, `qrcode` ni los
modelos TTS. Las dos copias del servidor HTTP que viven en `src\Install\Dist\` están desfasadas,
así que un paquete generado hoy desplegaría una versión distinta de la que corre en producción.
Incluir el módulo en el instalador y dejar de codificar su ruta; declarar todos los
prerrequisitos; regenerar `Dist\` desde la fuente única de `B-08` como parte del empaquetado;
valorar la firma de los binarios con comprobación al cargar el XLL (requiere certificado de firma
de código, que es un coste externo); y **ejecutar por fin la prueba de instalación en máquina
limpia**, que es el pendiente de prioridad alta más antiguo del proyecto, abierto desde abril de
2026.

**Rutas:** `src\Install\Install-NEVEN.ps1`; `src\Install\NEVEN-Setup.nsi`;
`src\Install\Build-Setup.ps1`, `Build-Installers.ps1`, `Sync-Dist.ps1`;
`src\startup\neven_http_server.py:2323`; `src\docs\Arquitectura\Dependencias_Instalacion.md`;
`src\Audiobook\README.md`.

**Invariantes:** `INV-INS-02` (`LoadBehavior=3` verificado tras `regsvr32`), `INV-INS-03` (backup
`.bak` en modo `-IsUpdate`), `INV-INS-04` (JSON desplegado sin BOM) e `INV-BLD-04`
(`Addin/CMakeLists.txt` copia el config, no el template) condicionan el trabajo; ninguna se viola.
Converge con `A-04`, `A-05` y `A-12`.

**Motivado por:** `PROD-04` (alta), `PROD-28`, `PROD-29`, `COD-54` — informe §3.2 y §8.

#### C-08 · Gestor de paquetes proactivo

**Prioridad:** P2 · **Coste:** L-XL, 8-12 jornadas · **Riesgo:** Medio: instalar paquetes es una
acción con efecto en la máquina del usuario, así que la autorización explícita y el registro no
son opcionales.

**Descripción.** Está especificado y acordado, y nunca se empezó (45 tareas, 0 marcadas). Ataca el
modo de fallo más común del producto: falta un paquete de R y el usuario pierde funcionalidad.
`A-13` lo mitiga pero no lo elimina, porque con `requireNamespace` la función sigue sin poder
calcular. La especificación describe un subsistema que verifica los paquetes requeridos en los
tres motores, informa de los que faltan y pide autorización explícita antes de instalar, y nombra
el caso que lo motivó: al actualizar R, los paquetes de la ruta antigua no migran. Completar lo
especificado, con el manifiesto de paquetes requeridos derivado de los `requireNamespace` de la
librería (que `A-13` hace enumerables) y el flujo de autorización en el tab Configuración.

**Rutas:** `src\startup\` (servicio) y `src\TaskPane\taskpane.html` (panel `settings`);
`src\libreria\R\R4XCL-0-UT-InstalaPaqueterias.R` (ya existe y usa `requireNamespace`);
`src\tests\test_package_manager_service.py`.

**Invariantes:** ninguna de las 62 la cubre. Si el servicio escribe en el directorio de la
librería, hay que revisar que no choque con `A-05` (ACL) ni con `A-04` (integridad).

**Motivado por:** `COD-27`, `PROD-17` (el modo de fallo) y la especificación
`.kiro\specs\neven-package-manager\` — informe §4.3.

---

## 3. POR MEJORAR

### 3.1 Prioridad P1

#### A-10 · Sandbox consciente del lenguaje, y alcance declarado por escrito

**Prioridad:** P1 · **Coste:** L, 4-6 jornadas (la mayor parte es reetiquetar y revisar los **133
tests de `sandbox_tests.cc`**) · **Riesgo:** Medio: tocar el verificador puede rechazar código que
hoy pasa, o al contrario. La red son **158 tests**: esos 133 más `NewFunctionsSandboxTest` (16),
`SandboxBlocklistPBT` (4), `SandboxPathPBT` (2) y `PythonSandboxPBT` (3), que también hay que
revisar aunque no se reetiqueten. Extenderlos **antes** de cambiar la lógica.

**Descripción.** `SandboxVerifier` evalúa las tres listas de lenguaje sobre cualquier entrada, de
modo que código R legítimo que contenga `eval(`, un acento grave, `open(` o el token `ENV` se
rechaza por reglas de Julia. Ese coste en falsos positivos es la causa de fondo de que la vía
HTTP→pipe se construyera sin ningún control. Y las excepciones de contexto son decorativas: un
comentario `# neven` habilita `library()` arbitraria, y mencionar una ruta de NEVEN habilita
`source()` de cualquier fichero, porque no se extrae ni se valida el argumento real. Dos partes,
en este orden: (1) pasar el lenguaje a `ValidateCodeForExecution` y evaluar solo su lista,
reetiquetando por lenguaje los 133 tests; (2) decidir y escribir el alcance, o se aplica el
verificador también en la ruta HTTP→pipe, o se declara en `SECURITY.md` que el TaskPane es zona de
confianza del usuario y que el sandbox solo cubre las celdas. **Las dos opciones son defendibles;
lo que no lo es es prometer un control que esa ruta no tiene.** En el mismo paquete: reparar o
retirar `AutoLoader`, que es el único camino que valida contenido y no tiene invocadores, mientras
la carga real pasa por `FileWatchService`, que no valida.

**Rutas:** `src\Common\Security\SandboxVerifier.cc:62-330`; `src\Include\SandboxVerifier.h:58`;
`src\tests\sandbox_tests.cc`; `src\Common\AutoLoader.cc:43-110`;
`src\Core\src\FileWatchService.cc:68-77`; `src\startup\neven_http_server.py:1110-1112, 4332-4400`;
`src\SECURITY.md`.

**Invariantes:** **ninguna de las 62 describe el sandbox**, que es el control que `SECURITY.md`
presenta como principal: es un hueco, no una violación. Se propone añadir una invariante de
alcance (§5.5c). `INV-TEST-03` se mantiene.

**Motivado por:** `SEC-02` (alta), `SEC-23` — informe §5.3.

#### A-11 · Un solo contrato de configuración y un solo inventario de puertos

**Prioridad:** P1 · **Coste:** M-L, 3-4 jornadas · **Riesgo:** Medio: el fichero de configuración
es el que hace arrancar todo, y la migración debe hacer copia `.bak` antes de sobrescribir.

**Descripción.** El template del instalador y el `neven-config.json` de producción tienen esquemas
incompatibles, y los dos consumidores leen claves distintas: Studio lee `ai_profiles` y
`db_connections`, AgentService lee `AI.*`, que ya no existe en producción y por eso emite
"AI.enabled=false". Una instalación limpia produce un config que Studio no entiende; con el de
producción pasa lo contrario. Un esquema único con `version` y migración desde el antiguo;
AgentService adaptado a `ai_profiles`; y una sección `ports` explícita (`ports.studio`,
`ports.agent`, `ports.audiobook`) leída por los tres servicios, con comprobación al arrancar y
mensaje claro si el puerto está ocupado por otro servicio de NEVEN.

**Rutas:** `src\Install\neven-config.template.json`; `src\AgentService\neven_ai_service.py:733,
1207`; `src\startup\neven_http_server.py`; `src\Audiobook\neven_audiobook_server.py:29`;
`src\TaskPane\audiobook.js:20`; `src\Install\Install-NEVEN.ps1` (migración).

**Invariantes:** `INV-INS-03` (backup `.bak` en modo `-IsUpdate`) e `INV-INS-04` (UTF-8 sin BOM)
deben seguir cumpliéndose en la migración. **`INV-AS-03` pasa de literal a valor por defecto
configurado: requiere reformulación previa** (§5.2). `INV-INS-01` intacta: ni el template ni
producción contienen hoy una clave de API no vacía.

**Motivado por:** `PROD-06` (alta), `PROD-01`, `SEC-16` — informe §3.2 y §5.3.

#### B-05 · Tests para los diez subsistemas sin cobertura

**Prioridad:** P1 · **Coste:** L, 5-7 jornadas para los dos primeros más el mock; XL si se cubren
los diez · **Riesgo:** Bajo.

**Descripción.** Diez subsistemas tienen cero referencias en los 33 `.cc` de tests:
`ViewerManager`, `RibbonService`, `PlutoManager`, `CrashHandler`, `FileWatchService`,
`MenuService`, `GCMonitor`, `DiagnosticRouter`, `NevenProgressiveRegistrar` y
`NevenInitOrchestrator`. Los dos casos más caros: `ribbon_connect.h` tiene 1.522 líneas y ningún
test, aunque `INV-RIBBON-01` es exactamente la correspondencia que un test de tabla verifica en
segundos; y `ViewerManager` concentra la carrera de datos y el `TerminateThread` de `A-14`, es
decir la parte más concurrente del proyecto es la que no tiene red. Empezar por esos dos y hacer
`MockExcelBridge` programable con una tabla `{xlfn → (código de retorno, XLOPER de salida)}`, para
poder probar `xlretAbort`, `xlretUncalced` y la conversión de vuelta, que hoy son invisibles
porque el mock devuelve siempre éxito y no escribe en `operRes`.

**Rutas:** `src\tests\` (nuevos); `src\Ribbon\ribbon_connect.h`, `src\Ribbon\ribbon_ui.xml`;
`src\Common\ViewerManager.{h,cc}`; `src\Core\include\MockExcelBridge.h`;
`src\tests\callback_behavior_tests.cc`, `raii_xloper_tests.cc`.

**Invariantes:** debe cumplir `INV-TEST-03` (sin Excel). El test de tabla **convierte
`INV-RIBBON-01` en ejecutable**, que hoy solo está documentada.

**Motivado por:** `COD-23` (alta), `COD-24` — informe §4.3.

#### B-06 · Activar los avisos del compilador

**Prioridad:** P1 · **Coste:** M-L, 2-4 jornadas (el flag es media hora; el resto es la cola de
avisos) · **Riesgo:** Medio: `/WX` de golpe bloquearía el build y `/sdl` convierte algunos avisos
en errores por sí mismo, así que conviene medir primero con `/W3` solo.

**Descripción.** No hay ningún flag de nivel de aviso en los 12 `CMakeLists.txt`: el proyecto
compila con el `/W1` por defecto de MSVC, y además se silencian explícitamente cuatro familias de
avisos de obsolescencia. En 43.320 líneas de `.cc` y 24.014 de `.h` eso significa no ver
conversiones con pérdida, variables sin usar, rutas sin `return` ni comparaciones con signo, que
es la clase de defecto que más cuesta encontrar en depuración y que el compilador detecta gratis.
Subir a `/W3 /permissive- /sdl`, vaciar la cola y **solo entonces** evaluar `/W4` y `/WX` por
objetivo. Revisar si los cuatro `_SILENCE_*` siguen siendo necesarios.

**Rutas:** `src\CMakeLists.txt:12, 15-25`.

**Invariantes:** no se quita ningún flag, así que `INV-BLD-01` e `INV-BLD-02` quedan intactas e
`INV-TEST-01` sigue pasando, porque comprueba presencia y no exclusividad.

**Motivado por:** `COD-14` (alta) — informe §4.3.

#### B-07 · Reproducibilidad del build

**Prioridad:** P1 · **Coste:** M, 1-2 jornadas · **Riesgo:** Bajo: anclar `rapidcheck` a un SHA
puede requerir elegir el commit que compila hoy con el MSVC actual.

**Descripción.** `rapidcheck` está declarado con `GIT_TAG master`, y sostiene nueve suites de
property-based testing: un cambio incompatible en un repositorio ajeno rompe el build de los tests
sin que nada cambie en NEVEN. Protobuf y WebView2 se descargan por URL sin `URL_HASH`. Los tres
`file(GLOB)` de fuentes no llevan `CONFIGURE_DEPENDS`, así que añadir o borrar un `.cc` en
`src\Core\src\` (47 ficheros) no entra en el build hasta que alguien reconfigura a mano. Anclar a
SHA, añadir `URL_HASH SHA256`, poner `CONFIGURE_DEPENDS` y sustituir por `set()` los "globs de
nombres literales" de ControlR y ControlJulia; migrar `include_directories()` a
`target_include_directories()` para homogeneizar con el estilo que ya usa `src\Core`; y quitar el
`-DCMAKE_BUILD_TYPE` de `build.ps1`, que el generador multiconfiguración ignora y hace pensar que
`-Config Debug` ya está aplicado.

**Rutas:** `src\CMakeLists.txt:27-29, 34-37, 52-57, 70-79, 84`; `src\Core\CMakeLists.txt:2`;
`src\NEVEN-SIM\CMakeLists.txt:10`, `src\NEVEN-SIM\tests\CMakeLists.txt:7-8`;
`src\ControlR\CMakeLists.txt:53`; `src\ControlJulia\CMakeLists.txt:37`; `src\build.ps1:72`.

**Invariantes:** ninguna. `INV-BLD-01/02/03` son sobre flags y binarios, no sobre anclaje de
dependencias.

**Motivado por:** `COD-15`, `COD-16`, `COD-17`, `COD-18` — informe §4.3.

#### B-09 · Observabilidad: un solo canal, rotación y registro de seguridad aparte

**Prioridad:** P1 · **Coste:** M-L, 3-4 jornadas · **Riesgo:** Bajo-Medio: el log es la única
herramienta de diagnóstico que hoy tiene el usuario, y una rotación mal implementada pierde justo
las trazas del fallo que se está investigando.

**Descripción.** `C:\NEVEN\neven.log` mide 119,6 MB y no hay rotación en ningún punto;
`C:\NEVEN\logs\` existe y está vacío mientras once ficheros de log se escriben sueltos en la raíz
de producción, dos de ellos con el mismo propósito y nombres casi iguales. El servidor Python usa
15 `print(` frente a 9 usos de `logging`, con dos `except:` desnudos que capturan también
`KeyboardInterrupt` y `SystemExit`. Y el contenido es sensible: 1,6 millones de líneas con código
de arranque, 8.448 líneas de comandos completas y valores de celda, en un fichero que cualquier
usuario autenticado puede reescribir. Rotación por tamaño con N ficheros retenidos; consolidar en
`C:\NEVEN\logs\`; `logging` en lugar de los `print(`; bajar a DEBUG lo que hoy registra código del
usuario; y un **registro de seguridad separado** para los eventos que `SECURITY.md` dice auditar
(bloqueos del sandbox, arranque con sandbox desactivado, fallos de integridad, peticiones
rechazadas), con ACL propia.

**Rutas:** `src\Common\LogService.*`; `src\startup\neven_http_server.py`; `neven-config.json`
(`logFile`, nivel y rotación).

**Invariantes:** ninguna. Depende de `A-05` para la ACL del registro de seguridad.

**Motivado por:** `PROD-19`, `COD-38`, `SEC-09` (parte) — informe §3.2, §4.3 y §8.

### 3.2 Prioridad P2

#### A-09 · Unificar los renderizadores de resultados en `buildSlotElement`

**Prioridad:** P2 · **Coste:** L, 4-6 jornadas · **Riesgo:** Medio: es el camino por el que se ve
todo resultado, y sin tests de frontend (`B-20`) la única red es la prueba manual de los nueve
tabs.

**Descripción.** `INV-TF-01` declara `buildSlotElement()` el único renderizador y el veredicto es
PARCIAL: la función está definida una sola vez, pero hay cuatro renderizadores paralelos
(`renderScriptResult`, el *fallback* literal de `taskpane.html`, `_renderBackendResult` y
`renderScriptResultRS`), más el par duplicado `renderSQLResultRS`/`renderSQLResults`,
`_excelRenderSlots` y tres definiciones de `showToast` con tres firmas. Y la dependencia entre
`taskpane.html` y `datalab.js` no está declarada: se comprueba con `typeof` y degrada en silencio
al renderizador de respaldo si el fichero no cargó. Convertir los paralelos en adaptadores que
produzcan slots `{name,label,type,value,tier}` y deleguen; eliminar `_excelRenderSlots`, el panel
comentado `excel-analysis` y el panel huérfano `id="sql"`; quitar los `typeof` defensivos; y dejar
una sola `showToast` con `duration` opcional.

**Rutas:** `src\TaskPane\datalab.js:1528`; `src\TaskPane\taskpane.js:476, 1219`;
`src\TaskPane\taskpane.html:384, 861, 2336, 2657, 5211, 5327, 7243-7301`;
`src\TaskPane\chart-gallery.js:1646`; `src\TaskPane\audiobook.js:43`.

**Invariantes:** **cierra `INV-TF-01`**. `INV-TF-03` (copiar con `[System.IO.File]::Copy()`) e
`INV-TF-04` (sin bundler) se respetan.

**Motivado por:** `COD-41`, `COD-42`, `PROD-13`, `PROD-14`, `PROD-25` — informe §3.2 y §4.3.
Converge con `A-08`, que fija la política de `srcdoc` en los mismos puntos.

#### A-14 · `ViewerManager`: estado compartido atómico y cierre sin `TerminateThread`

**Prioridad:** P2 · **Coste:** S-M, 1 jornada · **Riesgo:** Medio: es la parte más concurrente del
proyecto y tiene cero tests. Conviene emparejarlo con el test de ciclo de vida del hilo STA de
`B-05`.

**Descripción.** `available_` es un `bool` no atómico escrito desde el hilo de Excel y desde el
hilo STA, como documenta el propio comentario del código; `viewers_` sí está protegido por mutex,
pero `available_`, `max_viewers_`, `max_memory_mb_`, `sta_thread_id_` y `sta_thread_handle_`
quedan fuera. Y el cierre hace `TerminateThread` sobre el hilo STA si no responde a `WM_QUIT` en
5 s, lo que no desenrolla la pila ni libera los locks y puede dejar el heap del proceso de Excel
inconsistente justo al salir, que es la causa clásica de "Excel se cerró al salir". Hacer
`available_` atómico, fijar los dos límites antes de lanzar el hilo, y sustituir
`TerminateThread` por registrar el fallo y abandonar el hilo, porque el proceso va a terminar de
todos modos.

**Rutas:** `src\Common\ViewerManager.h:188, 211-212`; `src\Common\ViewerManager.cc:99, 123, 139,
146, 155-166`.

**Invariantes:** ninguna.

**Motivado por:** `COD-06`, `COD-07` — informe §4.3.

#### A-15 · Acotar el *zombie cleanup* a procesos huérfanos

**Prioridad:** P2 · **Coste:** M, 1-2 jornadas · **Riesgo:** Medio: si la detección de huérfanos
falla al revés, quedan procesos zombi que bloquean los pipes, que es el problema que el `taskkill`
vino a resolver.

**Descripción.** El arranque ejecuta `taskkill /F /IM ControlR.exe /T` (y Julia y Python), y
`taskkill /IM` mata todos los procesos con ese nombre en la sesión, no solo los huérfanos: si el
usuario abre un segundo Excel con NEVEN, el `xlAutoOpen` del segundo deja sin motores al primero,
que seguirá mostrando funciones registradas que devuelven error de pipe. Registro de PIDs en
`%LOCALAPPDATA%` o enumeración por proceso padre, y matar solo lo que no tenga un Excel vivo
detrás. El JobObject que `Init()` ya crea es el mecanismo natural para acotarlo.

**Rutas:** `src\Core\src\rj2xcl.cc:457-476`.

**Invariantes:** **`INV-CORE-02` se preserva**: fija el **orden** (limpieza antes de
`file_watch_service_->Start()` y `ConnectLanguages()`, hoy en `:480` y `:487`), no el
**mecanismo**.

**Motivado por:** `COD-02` — informe §4.3. El efecto con dos instancias es HIPÓTESIS: no se probó.

#### A-16 · Validar los mensajes del puente del visor

**Prioridad:** P2 · **Coste:** S-M, 1 jornada · **Riesgo:** Bajo.

**Descripción.** El puente construye el JSON de `writeCell` concatenando `sheet`, `cell` y `value`
sin escapar y lo escribe en `C:\NEVEN\data\bridge_queue.json`; y escribe el mensaje de
`sim-command` tal cual, sin validar nada, en `C:\NEVEN\data\sim_command.json`. Los consumidores
son NEVEN-SIM y Excel. El emisor es el HTML renderizado en el visor, que genera R o Julia y puede
incorporar datos ajenos. Serializar con `json11` en lugar de concatenar, y validar `sim-command`
contra un esquema antes de escribir la cola.

**Rutas:** `src\Common\PostMessageBridge.cc:73-82, 119-130`; consumidores
`src\NEVEN-SIM\src\bridge_poller.cc:30`, `sim_main.cc:619`.

**Invariantes:** ninguna. `INV-CP-03` **no cubre** este puente, porque el canal es
`window.chrome.webview.postMessage` y no tiene origen que comparar: la defensa tiene que ser la
validación del mensaje en C++.

**Motivado por:** `SEC-15` — informe §5.3.

#### A-18 · Endurecimientos menores del C++ con control que aparenta existir

**Prioridad:** P2 · **Coste:** M, 2-3 jornadas · **Riesgo:** Bajo.

**Descripción.** Cuatro controles que existen y no actúan, dos endurecimientos del visor y dos
higienes. (a) `ConfigService::ValidateConfig()` detecta `..` y caracteres peligrosos y **descarta el valor de
retorno** en sus seis llamadas; además la lista no incluye la comilla doble, que es la que
importaría para la línea de comandos de Quarto. (b) `RequestSandboxDisable()` implementa el
diálogo de confirmación y el registro en los que la evaluación OWASP apoya un 9/10 en A01, y no
tiene invocadores ni persiste el cambio: o se conecta a un control real del Ribbon o se elimina, y
en cualquier caso **se corrige el documento que la acredita**; conviene además registrar
explícitamente cada arranque con el sandbox desactivado. (c) `InputSanitizer::BuildSafeCommandLine`
existe y no se usa en el único sitio que la necesitaría, `StartChildProcess`, que construye la
línea a mano sin entrecomillar `pipe_name_`. (d) `AddDllDirectory` solo surte efecto con
`SetDefaultDllDirectories`, que no se llama en ningún punto. (e) **Los dos endurecimientos del
visor WebView2 que no requieren CSP:** acotar `file:///` a los directorios de trabajo, que hoy el
filtro de navegación permite sin límite, y añadir `add_FrameNavigationStarting` para que los
iframes hereden ese filtro, que ya existe y está bien diseñado. La CSP **no** entra: la descartó el
usuario el 2026-08-19 con razón escrita y no se reabre (§6 punto 2); estas dos acciones son lo que
quedaba de `SEC-19` fuera de aquella decisión. Más: sustituir los seis `atoi()` por
`std::from_chars` con comprobación, sobre todo en el parseo de versión de R; y dejar escrita la
decisión sobre el endpoint de Azure que quedó en el historial de git (rotar la clave si el recurso
sigue vivo, y aceptar el historial documentándolo).

**Rutas:** `src\Common\ConfigService.cc:78-105, 111-155`, `ConfigService.h:99`;
`src\Core\src\language_service.cc:789`; `src\Common\Security\InputSanitizer.cc:117-152`;
`src\ControlR\src\controlr.cc:583-592, 614`, `r_engine_loader.cc:174, 186`,
`rinterface_win.cc:134`; `src\Ribbon\ribbon_connect.h:190, 692`;
`src\Common\ViewerWindow.cc:261-295, 552-626` (punto e);
`src\docs\Evaluaciones\Evaluacion_OWASP.md`.

**Invariantes:** ninguna se toca. Mejora el diagnóstico de `INV-CR-03`; `INV-CR-01` (carga de
`R.dll` por ruta absoluta) e `INV-CJ-03` intactas. El punto (e) no toca `INV-CP-03`, porque el
filtro del visor es independiente de la validación de origen de `postMessage`.

**Motivado por:** `SEC-13`, `SEC-14`, `SEC-18`, `SEC-19` (media-baja, punto e), `SEC-20`
(residual), `COD-09` — informe §5.3 y §4.3.

#### A-21 · `/utf-8` en la compilación y mensajes de celda coherentes

**Prioridad:** P2 · **Coste:** M, 2-3 jornadas · **Riesgo:** Medio: añadir `/utf-8` cambia cómo se
interpretan todos los literales del proyecto, así que hay que comparar un mensaje con acento antes
y después. Los nombres heredados pueden estar en libros de usuarios: si se retiran, conviene
mantener el alias.

**Descripción.** El build no pasa `/utf-8` en ningún punto, y `basic_functions.cc` no tiene BOM y
contiene 1.118 bytes > 127 dentro de literales que en ejecución se decodifican con `CP_UTF8`: sin
BOM ni flag, MSVC interpreta el fuente con la página de códigos ANSI de la máquina de compilación,
y en CP-1252 sobrevive por casualidad. En paralelo, los tres scripts de arranque tienen bytes > 127
en código activo, con `INV-SR-01` violada, y `startup.r` tiene mojibake en un `warning()` cuyo
texto llega al usuario. Y quedan cuatro nombres heredados visibles (`RJ_Version`,
`RJ_ButtonCallback`, `RJ_ContextSwitch`, `RJ_UpdateFunctions`), más mezcla de inglés y español en
los mensajes de celda. Añadir `/utf-8`; devolver los scripts a ASCII puro y limpiar el mojibake;
unificar el idioma de los mensajes; y retirar o declarar como alias documentados los nombres
heredados.

**Rutas:** `src\CMakeLists.txt:18`; `src\startup\startup.r`, `startup.jl`, `startup.py`;
`src\Core\src\basic_functions.cc` (ver `:497` frente a `:1054`);
`src\Core\include\basic_functions.h`.

**Invariantes:** **cierra `INV-SR-01`** (hoy violada en los tres scripts de arranque);
`INV-SR-05` manda el método de despliegue. `/utf-8` se **añade**, no sustituye nada, así que
`INV-BLD-01/02` e `INV-TEST-01` quedan intactas.

**Motivado por:** `PROD-16`, `PROD-18`, `PROD-23` — informe §3.2. El mojibake real en la celda es
HIPÓTESIS: exige compilar con y sin el flag y comparar en Excel.

#### B-12 · Offline real: vendorizar las dependencias de CDN

**Prioridad:** P2 · **Coste:** M, 2-3 jornadas · **Riesgo:** Bajo. `office.js` es el caso
delicado: Microsoft recomienda cargarlo del CDN y vendorizarlo puede desalinearse con la versión
del host, así que conviene vendorizar las seis librerías de visualización y dejar `office.js` con
`integrity` o tal cual, diciéndolo.

**Descripción.** Siete dependencias de frontend se cargan desde cuatro CDN sin atributo
`integrity` y sin copia local. Sin conexión, el TaskPane pierde los gráficos, los mapas y el
renderizado de fórmulas, y el fallo se manifiesta como una pantalla vacía sin mensaje. Para un
add-in de escritorio es una dependencia de red no declarada en los requisitos, y además choca con
la filosofía offline que el propio proyecto adoptó por decisión explícita. Vendorizar en
`src\TaskPane\vendor\` y añadir `integrity` a lo que siga viniendo de CDN. Evaluar el impacto en
el tamaño del instalador.

**Rutas:** `src\TaskPane\taskpane.html` (23 etiquetas `<script src=>` para 18 recursos);
`src\TaskPane\vendor\` (nuevo); `src\Install\Install-NEVEN.ps1`.

**Invariantes:** `INV-TF-04` se respeta: copiar ficheros no es empaquetar ni transpilar.

**Motivado por:** `COD-45`, `COD-43` — informe §4.3.

#### B-13 · Ordenar el espacio de ontologías

**Prioridad:** P2 · **Coste:** M, 1-2 jornadas · **Riesgo:** Medio: `C:\NEVEN\docs\ontologia` y
`C:\NEVEN\ontology` son los que lee el RAG en producción. No se toca producción al reordenar el
repositorio, y antes de borrar nada hay que confirmar qué consume `rag_engine.py`.

**Descripción.** La ontología vive en cuatro lugares y uno se duplica a sí mismo:
`android\ontologia\` tiene 736 ficheros, de los que la mitad son una copia exacta en
`android\ontologia\ontologia\`, y el dominio `graficos` existe además en `docs\ontologia\graficos`,
de modo que hay tres copias del mismo dominio. Hoy `neven-ontology-p1.yaml` es idéntico en
`src\docs\`, `android\ontologia\` y `C:\NEVEN\docs\ontologia\`, así que el problema no es la
divergencia actual sino que nada declara la fuente. Declarar
`src\docs\ontologia\neven-core\` fuente única de las invariantes y `docs\ontologia\<dominio>\`
fuente única de los grafos; eliminar la autoduplicación; decidir si la app Android necesita su
propia copia o puede consumir la del paquete; declarar `checkpoints\`, `page_index\` y los
`graph_visualization*.html` como artefactos generados y sacarlos del control de versiones; y añadir
al CI la validación `yaml.safe_load` de los cuatro YAML, que hoy pasa pero nada comprueba.
Alinear o retirar el skill `ontology-book-processor`, que describe un procedimiento que el proyecto
ya tiene documentado en `docs\COMO_AGREGAR_LIBROS.md`.

**Rutas:** `src\docs\ontologia\`; `docs\ontologia\`; `android\ontologia\` y su copia interna;
`.gitignore`; `.github\workflows\build-and-test.yml`.

**Invariantes:** ninguna de las 62 gobierna la ubicación de la propia ontología. El cuidado es no
romper la carga del RAG, no una invariante.

**Motivado por:** `MEJ4-03`, `LAY-12` — informe §6.5 y §2.4.

#### B-14 · Gestión de la bitácora

**Prioridad:** P2 · **Coste:** M, 1-2 jornadas · **Riesgo:** Medio: es la memoria del proyecto.
Copia de seguridad antes, verificación byte a byte después, y en ningún caso con redirección de
PowerShell, que es lo que corrompió el encoding en un intento anterior.

**Descripción.** `CHAT.md` y `CHAT_LARGO.md` tienen mojibake por doble codificación (693
marcadores en los primeros 200 KB del primero y 1.814 en el segundo antes de la compactación): el
texto es legible, pero las búsquedas por acentos fallan, que es exactamente lo que esta auditoría
necesitaba hacer. No hay política de rotación escrita ni plantilla de entrada, y la cabecera de
`CHAT.md` llegó a estar tres meses desfasada. Un script de normalización de encoding **en
Python**, con lectura de bytes, detección del patrón de doble codificación y reescritura en UTF-8
sin BOM, con copia previa y verificación de que los marcadores bajan a cero sin cambiar el número
de líneas; una política escrita de rotación (volcar a `CHAT_LARGO.md` cuando `CHAT.md` pase de
~100 KB, con índice de sesiones al principio del largo); y una plantilla de entrada con los campos
que esta auditoría echó de menos: causa raíz, fix, ficheros con su ruta de producción, intentos
fallidos y pendientes.

**Rutas:** `.kiro\contexto\CHAT.md`, `CHAT_LARGO.md`, `README.md`; nuevo script en `src\scripts\` o
`.kiro\contexto\`.

**Invariantes:** ninguna.

**Motivado por:** `LAY-13`, `LAY-14` — informe §2.4. La bitácora registra un intento previo de
corrección con `-replace` de PowerShell que **falló**; lo que funcionó fue reemplazo de línea
completa.

#### B-18 · Identificadores estables para los hallazgos, y la norma del comentario con ID

**Prioridad:** P2 · **Coste:** S-M, 1 jornada · **Riesgo:** Nulo.

**Descripción.** `src\docs\INFORME_AUDITORIA.md` declara 36 hallazgos y no usa identificadores
estables, de modo que los ejes 2 y 3 no pudieron emparejar hallazgo por hallazgo y el informe
sigue sin poder cerrarse; `hallazgos_seguridad.md` (191 KB, 151 secciones) no tiene campo de
estado, y muchas entradas son observaciones de que algo está bien hecho. Entretanto `SECURITY.md`
afirma que los 36 fueron remediados y esta auditoría encontró abiertos dos controles que esa misma
remediación introdujo. Asignar IDs a la tabla y un campo de estado a los informes de `audit\`; y
adoptar como norma lo único que funcionó: **un comentario en el punto exacto del código con el ID
del hallazgo y la versión**, que es lo que permitió verificar `CM-BAJ-004/005/014`, `C-02` y
`C-06` cuatro meses después. Los 55 ítems de este plan ya tienen ID: usarlo al cerrarlos.

**Rutas:** `src\docs\INFORME_AUDITORIA.md`; `src\docs\audit\`;
`src\docs\sops\development_SOP.md` (la norma).

**Invariantes:** ninguna.

**Motivado por:** `LAY-18`, informe §4.5 y §5.4.

#### B-19 · Descomposición controlada de los dos monolitos

**Prioridad:** P2 · **Coste:** XL, 8-12 jornadas repartidas (4-6 el servidor, 4-6 el TaskPane) ·
**Riesgo:** **Alto, con precedente documentado**: el refactor del servidor se intentó el 2026-09-24
y hubo que revertirlo, con el TaskPane caído. La causa registrada no fue el diseño, fue el
despliegue incompleto (no se copió el módulo del que dependía) más corrupción de encoding al
revertir con PowerShell. La conclusión escrita entonces fue que se puede re-aplicar con mejor
proceso de despliegue.

**Descripción.** El servidor canónico tiene 4.901 líneas y 65 endpoints despachados por una cadena
de `if/elif` de 551 líneas entre `do_GET` y `do_POST`: añadir un endpoint exige editar el mismo
bloque que todos los demás, y los controles transversales dependen de que cada rama nueva se
acuerde de llamarlos. `taskpane.html` tiene 6.053 líneas de JavaScript inline (73 % del fichero)
que ningún linter ni editor trata como JavaScript, con 114 asignaciones a `.innerHTML`. Servidor:
tabla de rutas y partición por áreas (`ai`, `ontology`, `rag`, `charts`, `config`, `db`), con el
rate limiting y la validación aplicados **en el despachador**. TaskPane: extraer los 10 bloques
`<script>` a ficheros `.js` por área, cargados con `<script src=>` y globales explícitos
declarados en un solo punto, sin módulos ES, sin bundler y sin transpilador.

**Rutas:** `src\startup\neven_http_server.py`; `src\TaskPane\taskpane.html`.

**Invariantes:** toca `INV-SB-01..05` (mutex, encoding de escritura, barrera SQL, rate limiter,
contexto consumible) y, en el TaskPane, `INV-TF-01`, `INV-TF-03` e `INV-TF-04`. **Una tabla de
rutas las preserva y las refuerza**, porque hoy dependen de que cada rama se acuerde de llamarlas;
y la extracción del JS no necesita paso de build, así que `INV-TF-04` no es el obstáculo: el
obstáculo es el trabajo. **Condición dura: `B-02` y `B-03` antes**, con tests que fijen las cinco
invariantes del servidor. Sin esos tests, no acometer.

**Motivado por:** `COD-37` (alta), `COD-40` (alta) — informe §4.3.

### 3.3 Prioridad P3

#### A-19 · Named pipes: primera instancia, identificación del cliente y DACL propia

**Prioridad:** P3 · **Coste:** M, 2-3 jornadas (los pasos 1 y 2 son S; el paso 3 es M con pruebas)
· **Riesgo:** Alto en el paso 3: si la DACL queda mal, el XLL no conecta con los motores y Excel
se congela, que es exactamente lo que previó el análisis de 2026-08-19.

**Descripción.** El pipe se crea con `lpSecurityAttributes = NULL`, lo que deja la DACL por
omisión de los named pipes de Windows, que concede lectura a `Everyone`; sin
`FILE_FLAG_FIRST_PIPE_INSTANCE`, de modo que el servidor no detecta que el nombre ya existía; con
cuatro instancias como máximo; con nombre predecible a partir del PID de Excel; y con el cliente
abriendo sin `SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION`. Por ese canal viajan el código a
ejecutar y los datos de la hoja. Tres pasos separables, de menor a mayor riesgo: (1)
`FILE_FLAG_FIRST_PIPE_INSTANCE` para detectar nombre ocupado; (2) `SECURITY_IDENTIFICATION` en el
cliente e identificación del proceso en el extremo servidor; (3) `SECURITY_ATTRIBUTES` con DACL
que conceda acceso solo al usuario actual.

**Rutas:** `src\Common\IPC\pipe.cc:216-227`; `src\Core\src\language_service.cc:228, 408`;
`src\tests\pipe_lifecycle_tests.cc` (8 tests, la red existente).

**Invariantes:** **`INV-CJ-03` se preserva**: no cambia el nombre del pipe, ni el marco de 4
bytes, ni el formato Protobuf. `INV-CMN-03` e `INV-CR-02` (30 reintentos × 100 ms) intactas.

**Motivado por:** `SEC-12` — informe §5.3. **Choca con una decisión previa del usuario**, no con
una invariante: el 2026-08-19 se descartó la ACL en pipes por riesgo alto. Se re-propone troceada
y en P3 con el único dato nuevo que lo justifica: la premisa de aquel análisis, que el riesgo
"requiere acceso local con privilegios elevados", es falsa (la DACL por defecto concede lectura a
`Everyone`). **La decisión sigue siendo del usuario**, y el paso 3 no debería ejecutarse sin su
aprobación explícita.

#### A-22 · Código muerto y duplicados

**Prioridad:** P3 · **Coste:** M, 2-3 jornadas · **Riesgo:** Bajo.

**Descripción.** Inventario medido: `ScheduleDelayedUpdate()` nunca se invoca y duplicaría el
timer de telemetría si alguien la llamara, y el miembro estático `instance_` nunca se lee ni se
escribe; `create_download_route` de Audiobook no la invoca nadie y `main_server.py` es un segundo
servidor completo que no recibió el arreglo de `9eba8b1`; 9 de 10 ficheros de
`src\TaskPane\deprecated\GR_DataLab_migrated\` son copias byte a byte de los vivos, y
`GR_EjemploBasico.Studio.R` **solo existe allí**, de modo que el nombre "deprecated" engaña;
cuatro librerías de CDN se cargan dos veces, entre ellas Plotly (~3,5 MB); el cache-busting usa
cuatro formatos distintos de sello puestos a mano, y un fichero no tiene ninguno; y hay ocho
residuos de build versionados. Eliminar lo muerto dejando **un comentario con el identificador del
hallazgo y la versión** en el punto del código, que es el patrón de `B-18`; rescatar
`GR_EjemploBasico.Studio.R` antes de borrar `deprecated\`; quitar los `<script>` duplicados;
generar el `?v=` desde el hash o la fecha en el empaquetado; y retirar los residuos añadiendo un
test de higiene que los impida, porque `repo_hygiene_tests.cc` ya tiene el patrón.

**Rutas:** `src\Core\src\rj2xcl.cc:60, 538-558`, `src\Core\include\rj2xcl.h:60, 193`;
`src\Audiobook\api\routes.py:1296-1500`, `src\Audiobook\main_server.py`;
`src\TaskPane\deprecated\GR_DataLab_migrated\`; `src\TaskPane\taskpane.html` (etiquetas y `?v=`);
`src\Install\Build-Setup.ps1` y `Sync-Dist.ps1`; `src\build_log.txt` y los otros residuos;
`src\.gitignore`; `src\tests\repo_hygiene_tests.cc`.

**Invariantes:** eliminar `ScheduleDelayedUpdate()` **refuerza `INV-CORE-01`**, porque borra la
única ruta que podría registrar funciones fuera de `xlAutoOpen`. Los residuos de build no violan
`INV-BLD-03` (no son binarios) pero son el mismo tipo de suciedad.

**Motivado por:** `COD-05`, `COD-32`, `COD-43`, `COD-44`, `COD-54`, `COD-55`, `PROD-22`,
`PROD-25`, `LAY-16` — informe §4.3 y §2.4.

#### A-23 · Librería Julia: precondiciones, semántica del parámetro y el `module` condicionado

**Prioridad:** P3 · **Coste:** S para (b) y (c), 1 jornada; L para (a), 4-6 jornadas contando la
reconstrucción de la sysimage · **Riesgo:** Bajo para (b) y (c); Alto para (a).

**Descripción.** Tres cosas. (a) Ningún "módulo J4XCL" es un módulo de Julia: cero `module` en los
nueve `.jl` y un solo `export` en el directorio, así que son scripts planos que inyectan nombres
en `Main` y dos ficheros que definan la misma función se sobrescriben según el orden de carga, que
con la sysimage queda fijado en tiempo de build. (b) En `J4XCL-OP-Optimizacion.jl`, `Parametro` es
la tasa de aprendizaje en las ramas de gradiente y la tolerancia en la de bisección, y el
docstring no lo dice: quien pase `0.01` esperando una tasa obtiene una tolerancia enorme. (c) Cero
`@assert`, `error(` o `throw` en los nueve ficheros: ninguna función valida dimensiones ni tipos, y
el único control visible devuelve una cadena, mezclando el canal de error con el de datos.
Documentar la semántica por rama y validar precondiciones por el canal correcto es trabajo pequeño
y sin riesgo; el `module` con `export` explícito queda condicionado.

**Rutas:** `src\libreria\JULIA\*.jl` (9 ficheros), en particular
`J4XCL-OP-Optimizacion.jl:28-30, 32, 145, 191`.

**Invariantes:** (b) y (c) no tocan ninguna; `INV-NX-03` (TipoOutput en `a2`) intacta. (a) **toca
`INV-CJ-01` e `INV-CJ-02`**: obliga a reconstruir `neven_julia.dll` (1,04 GB), actualizar
`neven_julia.version` y revalidar que el script de precompile corre solo antes de
`create_sysimage()`. **No se propone sin esa condición escrita**, y por eso va en P3.

**Motivado por:** `COD-33`, `COD-34`, `COD-35` — informe §4.3.

---

## 4. NUEVAS IDEAS

Todas nacen de un hallazgo del informe, no de un catálogo genérico de buenas prácticas, y todas
encajan con la arquitectura real: XLL con registro solo en `xlAutoOpen`, tres `Control*` por named
pipes, servidor HTTP local, TaskPane sin bundler, visor WebView2 y sysimage de Julia.

### 4.1 Prioridad P1

#### B-03 · Suite de seguridad de la API local

**Prioridad:** P1, **a la vez que `A-01`, no después** · **Coste:** M-L, 3-4 jornadas · **Riesgo:**
Bajo.

**Descripción.** 247 de los 369 tests están relacionados con seguridad y **cero** cubren la
superficie HTTP: ni CORS, ni autenticación, ni recorrido de rutas en el servido estático, ni
contención de `/api/save_script`, ni validación de `/api/groupby`, ni la política de `sandbox` de
los `srcdoc`, ni el bind del servidor de audiolibros. El esfuerzo de prueba está concentrado en el
componente que no es frontera (el blocklist) y ausente en los que sí lo son, y eso es la causa
estructural de que los hallazgos críticos pasaran desapercibidos. Suite pytest que arranque el
servidor con `pipe_client_factory` simulado, que el propio servidor ya soporta, y fije como
propiedades: sin token → 401; `Origin` ajeno → rechazo; `/api/save_script` fuera del directorio
base → 403; `/viewers/..%2f…` → 403; `/api/groupby` con una comilla doble en el nombre de columna
→ 400. **Cada hallazgo de seguridad del informe debería quedar convertido en un test que falle hoy
y pase cuando `A-01` esté hecho.**

**Rutas:** nueva suite en `src\TaskPane\tests\`; `src\startup\neven_http_server.py:4780-4800` (el
punto de inyección ya existe).

**Invariantes:** **cumple `INV-TEST-03`** gracias a la inyección de `pipe_client_factory`: no
necesita Excel ni motores reales.

**Motivado por:** `SEC-24` — informe §5.3. Depende de `B-02` (runner) y de `B-01` (CI).

#### B-04 · Convertir las invariantes mecanizables en tests, y reparar el hook que debía aplicarlas

**Prioridad:** P1 · **Coste:** M-L, 3-4 jornadas (el hook, media jornada) · **Riesgo:** Bajo: los
tests nuevos fallarán el primer día, que es el objetivo. Hay que decidir si se marcan como fallo
esperado hasta que `A-13` cierre `INV-LR-02/04`, o si se escriben en verde con la lista actual como
línea base.

**Descripción.** Las 62 invariantes son prosa en cuatro YAML, y el único control automático que las
invoca hace `Test-Path` sobre rutas inexistentes, de modo que aprueba sin validar nada. Entretanto
esta auditoría encontró `INV-LR-02` violada en 30 ficheros, `INV-LR-04` en **cinco ficheros de
función de usuario —12 contando los siete internos, que la redacción propuesta en §5.1 deja fuera de
alcance—**, `INV-SR-01` en tres y `INV-TF-01` parcial. Un fichero de tests por lenguaje que verifique las invariantes
comprobables sobre ficheros: `INV-NX-01` (ASCII sin BOM del dispatcher), `INV-NX-02` (llaves
balanceadas), `INV-LR-02` (sin `library()` de nivel superior), `INV-LR-04` (atributos presentes),
`INV-SJ-01..05` (sidecar válido, `id` único, `file` como basename, `function_name_xll`
existente), `INV-INS-04` (JSON desplegado sin BOM), `INV-RIBBON-01` (cada `onAction`/`getPressed`
del XML con entrada en `GetIDsOfNames` y valor en `DispIds`) e `INV-SR-01`. Y corregir las rutas
del hook para que vuelva a ser la puerta que el steering dice que es. `repo_hygiene_tests.cc` es el
patrón a seguir.

**Rutas:** `src\tests\ontology_invariants_tests.cc` (nuevo) y
`src\tests\test_ontology_invariants.py` (nuevo); `.kiro\hooks\validate-before-run.ps1:3, 29, 41,
132`.

**Invariantes:** ninguna se toca: solo se verifican. **Cumple `INV-TEST-03`**, porque todo son
ficheros y no hay runtimes implicados.

**Motivado por:** informe §2.3 y §4.4; `LAY-01`. Es también la respuesta a que el catálogo de
skills no tenga ninguno que valide ontologías contra código (informe §10): si no hay herramienta,
hay que convertir la ontología en tests.

#### C-01 · `=NEVEN.Diagnostico()`: un informe de estado en la celda

**Prioridad:** P1 · **Coste:** M, 2-3 jornadas · **Riesgo:** Bajo.

**Descripción.** Cuando algo no funciona, el usuario no tiene de dónde tirar. Si un motor no
conecta, todas las funciones de ese lenguaje aparecen como `#¿NOMBRE?` y nada dirige al usuario
hacia `NEVEN.Status`, que sí existe y sí informa; si falta WebView2, el visor devuelve un texto de
error; si tres servicios pelean por un puerto, no hay forma de verlo; y el log donde está la
respuesta mide 119,6 MB. Una función de celda que devuelva una tabla con: versión de NEVEN, estado
y versión de cada motor con su `HealthStatus`, presencia del runtime de WebView2, puertos
configurados y quién escucha en cada uno, directorio de funciones y número de ficheros cargados,
estado de la verificación de integridad, si el sandbox está activo, y la ruta del log con su
tamaño. Es la primera cosa que pedir en un informe de incidencia.

**Rutas:** `src\Core\include\basic_functions.h` (entrada nueva en `funcTemplates`);
`src\Core\src\basic_functions.cc` (nueva función, leyendo `LanguageService`, `ConfigService`, el
estado de `ViewerManager` y el tamaño del log). Sin dependencias nuevas.

**Invariantes:** debe registrarse en `funcTemplates` durante `xlAutoOpen` (`INV-CORE-01`), que es
precisamente lo que hace que funcione aunque los motores estén caídos, porque `funcTemplates` se
registra siempre.

**Motivado por:** `PROD-01`, `PROD-05`, `PROD-10`, `PROD-19` — informe §3.2.

#### C-03 · Informe estadístico con comprobación de supuestos y avisos accionables

**Prioridad:** P1 · **Coste:** L-XL, 7-10 jornadas para las siete familias; 2-3 para `MR_Lineal`
sola, que es el caso dominante y conviene hacer primero como piloto · **Riesgo:** Medio, y no es
riesgo de código sino de contenido: cada comprobación añadida tiene que ser la correcta para el
modelo (Breusch-Pagan no aplica igual en panel que en MCO), y conviene revisión antes de publicar.

**Descripción.** Es la capacidad que mejor sostiene la tesis del proyecto y hoy no existe. Quien
llama a `MR_Lineal` con `TipoOutput=1` recibe coeficientes, errores estándar y p-valores sin
ninguna comprobación de supuestos y sin ningún aviso; las comprobaciones existen pero hay que
saber pedirlas una por llamada. Y en los 63 ficheros de la librería hay cero ocurrencias de
`shapiro.test`, `qqnorm`, `dwtest`, `confint`, `cooks.distance`, `resettest`, `p.adjust` y de
cualquier tamaño de efecto estandarizado; en series de tiempo, cero `Box.test`, `kpss` y `ndiffs`.
Para el público declarado del paper, estudiantes de econometría, esa asimetría es el peor caso: el
camino fácil es el que no comprueba nada. (a) Un `TipoOutput` nuevo de "informe completo" que
devuelva en un solo `data.frame` la estimación más VIF, Breusch-Pagan, normalidad de residuos,
Ljung-Box y `confint`. (b) Una columna `R4XCL_Avisos` en `TipoOutput=1` que se rellene cuando un
supuesto falle. (c) Un aviso **accionable**, no un diagnóstico: "heterocedasticidad detectada
(p = 0,003); use `TipoOutput=7` para errores robustos HC3". El canal de presentación ya existe:
`_renderPedagogyWarning` y el tipo de slot `warning_pedagogy` pasan por `buildSlotElement`.

**Rutas:** `src\libreria\R\R4XCL-RG-Lineal.R`, `-Binaria.R`, `-Poisson.R`, `-Tobit.R`,
`-DatosPanel.R`, `-SeriesTiempo.R`, `-2SLS.R`; sus sidecars en `src\Install\functions`;
`src\TaskPane\datalab.js:1635` (ya hecho).

**Invariantes:** `INV-NX-03` (TipoOutput siempre en `a2`) e `INV-LR-03` (contrato `R4XCL_`)
intactas: es un valor nuevo del mismo parámetro en la misma posición, con el mismo contrato de
retorno. **Requiere actualizar `tipo_outputs[]` del sidecar** respetando `INV-SJ-03` (el `id == 0`
sigue reservado para la ayuda) e `INV-SJ-02` (`function_name_xll` exacto). Depende de `A-13`.

**Motivado por:** `COD-30`, `COD-31` — informe §4.3, con el skill `statistical-analysis` como
fundamento de los conteos.

### 4.2 Prioridad P2

#### C-02 · Panel de salud en el tab Configuración

**Prioridad:** P2 · **Coste:** M-L, 3-4 jornadas · **Riesgo:** Bajo-Medio: el endpoint que
comprueba servicios no debe bloquear el hilo del servidor, así que las comprobaciones van con
timeout corto.

**Descripción.** Lo mismo que `C-01` para quien no quiere escribir una fórmula, y añade lo que una
celda no puede dar: un botón de reintento y el puerto **real** de cada servicio. Hoy, cuando
`_handle_audiobook_start` responde "Server already running" porque algo distinto ocupa el 5556, el
usuario ve "Iniciando servidor…" y acaba con una instrucción de consola. Semáforo por servicio
(Studio, AgentService, audiolibros, R, Julia, Python, WebView2, Pluto, Quarto) con puerto real,
estado y acción, alimentado por un endpoint `/api/health/services` que consulte cada uno de verdad
y no con un `connect_ex` a ciegas.

**Rutas:** `src\TaskPane\taskpane.html` (panel `settings`, L1425) consumiendo `buildSlotElement`
para la tabla; `src\startup\neven_http_server.py` (endpoint nuevo, dentro de la tabla de rutas de
`B-19` si ya está hecha).

**Invariantes:** `INV-TF-01` (usar `buildSlotElement`, no un renderizador nuevo) e `INV-TF-04`
(sin bundler). Tras `A-01`, el endpoint exige token como todos.

**Motivado por:** `PROD-01`, `PROD-10` — informe §3.2.

#### C-04 · Suite Wooldridge como regresión numérica

**Prioridad:** P2 · **Coste:** L, 5-7 jornadas · **Riesgo:** Bajo-Medio: la parte delicada es la
tolerancia, porque demasiado estrecha falla por diferencias de versión de paquete y demasiado
ancha no detecta nada.

**Descripción.** Toda la librería R, 17.751 líneas, tiene **un** test de 100 líneas. No hay nada
que detecte que un cambio en `MR_Lineal` altera un coeficiente. Y existe media capacidad ya
construida: un PRD escrito, una función `DS_Wooldridge_Benchmark.Studio.R` con su sidecar, los
datasets en `src\libreria\EJEMPLOS\Excel\WOOLDRIDGE\` y `R4XCL-DS-Wooldridge.R`. El detalle que
delata que quedó a medias es que esa función vive en `src\Install\functions\` y no en
`src\libreria\R\`, que es uno de los ocho ficheros en esa situación y por eso la ubicación se
resuelve en `B-08` y no aquí. Convertir el
benchmark en regresión numérica: para cada ejemplo del libro, el resultado publicado como valor
esperado y una tolerancia declarada, con un runner que ejecute la librería contra los datasets y
compare. **Opt-in y fuera de `rj2xcl_tests`**, porque necesita R, con un comando documentado y, si
se quiere, un job de CI separado que instale R (el workflow ya tiene uno con
`r-lib/actions/setup-r@v2`).

**Rutas:** `src\tests\benchmarks\` (nuevo, con el runner `.R` formalizado por `B-02`);
`src\libreria\R\R4XCL-DS-Wooldridge.R`; `src\libreria\EJEMPLOS\Excel\WOOLDRIDGE\`;
`DS_Wooldridge_Benchmark.Studio.R` y su sidecar, hoy en `src\Install\functions\` y desplegados
byte a byte en `C:\NEVEN\functions`, cuya reubicación decide `B-08`. Conviene comprobar también que
los sidecars `DS_Wooldridge_Benchmark.json` y `R4XCL-DS-Wooldridge.json` divergen entre repositorio
y producción (informe §8.1): el benchmark debe escribirse contra la versión que se declare fuente.

**Invariantes:** **`INV-TEST-03` se respeta precisamente por dejarlo fuera** del objetivo GTest: la
invariante dice que si un test falla por un runtime externo es un bug del test, de modo que un
benchmark que necesita R no puede vivir en `rj2xcl_tests`.

**Motivado por:** `COD-23` (1 test para 17.751 líneas de R), `MEJ4-05` (media), y el PRD de
`src\docs\Depuracion\` — informe §4.3 y §6.5. La bitácora deja una lección aplicable: el
preprocesador `fix_wooldridge.py` se ejecutó *in place* y destruyó el fichero fuente, así que
cualquier herramienta que toque los datasets debe escribir en copia.

#### C-05 · Exportación reproducible de la sesión

**Prioridad:** P2 · **Coste:** L, 5-8 jornadas (depende de `A-17`) · **Riesgo:** Medio: Quarto es
una dependencia externa que el instalador enlaza por junction y no siempre está presente, así que
la exportación debe degradar a "solo Pluto" o a "solo `.qmd` sin renderizar" en lugar de fallar.

**Descripción.** Hoy un análisis hecho en Excel no se puede entregar como artefacto reproducible, y
el 80 % del camino está construido y roto: `NotebookExporter` genera un notebook de Pluto con
datos, parámetros, código y resultados, está expuesto como función de celda y nunca puede funcionar
(`A-17`); y por el otro lado `QuartoService` renderiza `.qmd` a HTML, PDF o DOCX con validación de
entrada correcta, pero la librería Quarto solo tiene un ejemplo básico. Una vez cablada la captura,
añadir un segundo formato de salida: un `.qmd` generado a partir de los slots de la sesión de
DataLab (datos, código, resultados, avisos de `C-03`) y renderizado a HTML o PDF. El resultado es
un informe con el código que lo produjo, que es lo que una tesis o un trabajo de curso necesita
entregar.

**Rutas:** `src\Common\NotebookExporter.{h,cc}` (segundo generador); `src\Common\QuartoService.cc`
(ya hace el renderizado); `src\startup\neven_http_server.py` (endpoint para el botón);
`src\TaskPane\datalab.js` (botón junto a los de PNG/SVG/Enviar a Slide); `src\libreria\QUARTO`
(plantilla).

**Invariantes:** ninguna nueva. `INV-TF-01` (el botón y el resultado pasan por
`buildSlotElement`). La validación de `QuartoService`, que el eje 3 declaró correcta,
**no debe relajarse** para aceptar el `.qmd` generado: el fichero se escribe en el directorio de
trabajo y se renderiza por la ruta ya validada.

**Motivado por:** `MEJ4-02` (vía `A-17`) — informe §6.5.

#### C-07 · Agente con acciones confirmadas

**Prioridad:** P2, y **después de `A-01`** · **Coste:** XL, 10-15 jornadas · **Riesgo:** Alto: es
la mejora que más superficie de seguridad añade, y sin la autenticación de `A-01` un endpoint de
acciones es una puerta más.

**Descripción.** Hoy el agente interpreta y recomienda; no actúa. El eje 3 verificó que no hay
ejecución automática de lo que propone el modelo, y que `/api/functions/create` es un endpoint
aparte que invoca la interfaz tras la aprobación del usuario. La capacidad que falta es dar el paso
de "te explico el resultado" a "te propongo la corrección metodológica y, si la aceptas, la
ejecuto", que es lo que la especificación `ontologia-v2` describe. Tres reglas fijadas **antes** de
escribir el código: ninguna acción con efecto (escribir un fichero, instalar un paquete, ejecutar
código) se dispara desde la salida del modelo sin confirmación explícita en la interfaz; el
contenido del RAG y de las celdas entra en el prompt **con marca de procedencia**, que hoy no
tiene; y cada acción disponible se declara en un catálogo cerrado, no se infiere del texto. Las
evals de comportamiento que ya existen son el punto de partida para verificarlo.

**Rutas:** `src\AgentService\neven_ai_service.py`; `src\startup\neven_http_server.py` (`/api/ai/*`,
con el patrón de validación de `_handle_function_create`); `.kiro\evals\agent_behavior\`; el
catálogo de funciones de la ontología.

**Invariantes:** `INV-SB-05` e `INV-AS-02` (contexto pendiente consumible) reducen la ventana de
reutilización del contexto y no se tocan. `INV-AS-01` (FastAPI y uvicorn requeridos, sin
degradación elegante) condiciona el despliegue. Conviene fijar la regla de confirmación como
invariante nueva si esto se acomete.

**Motivado por:** `SEC-21` — informe §5.3, incluida la advertencia de que `restricted_to_rag` no
es una defensa técnica contra inyección de prompt.

### 4.3 Prioridad P3

#### B-16 · Umbrales de tamaño y métrica de duplicación en el CI

**Prioridad:** P3 (P2 si se acomete `B-19`) · **Coste:** M, 1-2 jornadas · **Riesgo:** Bajo.

**Descripción.** Nada impide que los monolitos vuelvan a crecer después de `B-19`: hoy el servidor
tiene 4.901 líneas con funciones de 400 y 461, `taskpane.html` 6.053 de JS inline,
`basic_functions.cc` 4.583, y `control_julia.cc` y `control_python.cc` comparten 98 líneas
idénticas. Un chequeo en el CI que falle si un `.cc`/`.py`/`.js` supera N líneas o una función
supera M, con una **lista de excepciones explícita y datada** para no bloquear el build hoy, más un
detector de bloques repetidos. El valor está en la lista de excepciones: documenta la deuda y
obliga a justificar cada incorporación.

**Rutas:** `.github\workflows\build-and-test.yml`; nuevo script en `src\scripts\`.

**Invariantes:** ninguna.

**Motivado por:** `COD-08`, `COD-10`, `COD-37`, `COD-40`, `COD-41` — informe §4.3.

#### B-17 · Detector de API pública sin invocadores

**Prioridad:** P3 · **Coste:** M, 1-2 jornadas · **Riesgo:** Bajo.

**Descripción.** El patrón se repite: código público que nadie llama y que sostiene una promesa.
Cuatro casos confirmados (`NotebookExporter::CaptureAnalysis`, que hace que
`=NEVEN.Notebook.Export` falle siempre; `ConfigService::RequestSandboxDisable`, que sostiene un
9/10 de OWASP publicado; `RJ2XCL_Engine::ScheduleDelayedUpdate`; y
`AutoLoader::LoadAllUserScripts`, el único camino que validaba contenido) y uno probable
(`GCMonitor`, cuyo nombre no aparece en ningún `.cc` fuera de sus propios ficheros y del
`CMakeLists.txt`). Un chequeo que liste símbolos públicos sin referencias fuera de su propia unidad
de traducción. **La parte difícil es la lista de exclusión, y hay que decirlo**: los exports del
XLL, los nombres de `funcTemplates`, los puntos de entrada COM del Ribbon y los callbacks de
WebView2 parecen muertos a un barrido estático y no lo están. Sin esa lista, la herramienta genera
ruido y se abandona.

**Rutas:** nuevo script en `src\scripts\`; `.github\workflows\build-and-test.yml`.

**Invariantes:** ninguna.

**Motivado por:** `MEJ4-04`, `MEJ4-02`, `COD-05`, `COD-13` (`GCMonitor` tiene 20 miembros públicos
y cero marcas Doxygen, y es el caso probable que este detector confirmaría o descartaría), `SEC-02`,
`SEC-14` — informe §4.3, §5.3 y §6.5.

#### B-20 · Tests de frontend sin paso de build

**Prioridad:** P3 (P2 si se acomete `B-19`) · **Coste:** M-L, 3-4 jornadas · **Riesgo:** Bajo.

**Descripción.** 21.871 líneas de `.js` más 8.263 de `taskpane.html` y **cero** tests: el
repositorio no tiene `*.test.js`, `*.spec.js` ni configuración de ningún runner. Un
`src\TaskPane\tests\runner.html` que cargue los `.js` reales y ejecute asserts en el navegador, más
`node --test` para la lógica pura. Empezar por `buildSlotElement` con cada tipo de slot (`html`,
`table`, `scalar`, `vector`, `plotly`, `plotly_json`, `matrix`, `warning_pedagogy`), que es el
componente que `A-09` unifica y `A-08` endurece.

**Cómo se cargan los `.js` en `node --test` sin tocar `INV-TF-04`, que hay que decidir por
escrito antes de empezar.** Los ficheros definen globales de navegador y no exportan nada, así que
`require()` no sirve. Dos vías, y se elige la primera: **`vm.runInNewContext` sobre el fichero tal
cual**, con un contexto que aporte los globales que el código espera (`document`, `window`, `fetch`)
y del que el test lea las funciones definidas. No modifica el fuente, no añade dependencias y no es
ni bundler ni transpilador. La segunda vía es un guard ES5 al final de cada fichero
(`if (typeof module !== 'undefined') { module.exports = { … } }`): más simple de escribir, pero mete
código de test en el fuente de producción, así que solo se adopta si el contexto de `vm` resulta
inmanejable para algún fichero. Para el runner del navegador no hay problema: carga los `.js` con `<script src=>`,
que es lo que `taskpane.html` ya hace.

**Rutas:** `src\TaskPane\tests\` (nuevo); `src\TaskPane\datalab.js`, `taskpane.js`.

**Invariantes:** **`INV-TF-04` se respeta** con la vía elegida: `vm.runInNewContext` ejecuta el
fichero sin transformarlo, y un runner de tests no es un bundler ni un transpilador. Depende de
`B-19` para el código hoy inline.

**Motivado por:** `COD-25` — informe §4.3.

#### C-06 · Metaheurísticas en la librería de optimización

**Prioridad:** P3 · **Coste:** L, 5-8 jornadas · **Riesgo:** Bajo-Medio: si los algoritmos nuevos
entran en la sysimage hay que reconstruirla; si se cargan como script, no.

**Descripción.** `J4XCL-OP-Optimizacion.jl` tiene 320 líneas y una sola función con seis algoritmos
**deterministas**: gradiente, momentum, Newton, bisección, simplex y mínimos cuadrados no
negativos. No hay ninguna metaheurística en ningún `.jl` del proyecto. Para problemas no convexos,
combinatorios o con función objetivo cara, que son los que un usuario de Excel plantea cuando la
hoja no es un `lm`, no hay nada. Añadir enfriamiento simulado y un algoritmo evolutivo (y PSO si el
coste lo permite), con los tres requisitos que separan una metaheurística usable de un bucle
aleatorio: **semilla explícita y registrada en la salida** para que el resultado sea reproducible,
**criterio de parada declarado** (el fichero actual ya lo hace bien y emite "No convergió en
$max_iter iteraciones": copiar ese patrón), y la advertencia de que el resultado es una buena
solución y no un óptimo demostrado.

**Rutas:** `src\libreria\JULIA\J4XCL-OP-Optimizacion.jl` (una función por algoritmo con un único
despachador) y su sidecar en `src\Install\functions` si se quiere desde celda; opcionalmente los
solvers de `src\NEVEN-SIM\`.

**Invariantes:** `INV-NX-03` (TipoOutput en `a2`) intacta: los algoritmos nuevos son valores nuevos
del mismo parámetro. Si se decide meterlos en la sysimage, aplican `INV-CJ-01` e `INV-CJ-02` con el
coste de `A-23`(a).

**Motivado por:** `COD-34` — informe §4.3, con el skill `metaheuristic-optimization` como criterio
de diseño. El skill **no aplica al código existente**, porque los métodos actuales son
deterministas; aplicaría a lo que se añada.

#### C-09 · Ayuda contextual real en el asistente de funciones de Excel

**Prioridad:** P3 · **Coste:** L, 5-8 jornadas · **Riesgo:** Medio: `xlfRegister` tiene límites de
longitud por argumento y de número de argumentos, y el registro ocurre en el camino crítico de
`xlAutoOpen`, donde un error deja todo en `#¿NOMBRE?`. Medir primero la aridad máxima real de las
funciones exportadas, que el eje 1 dejó como comprobación pendiente.

**Descripción.** El asistente de funciones de Excel es el principal punto de descubrimiento para
quien no lee el código, y hoy muestra "Exported Function", "Exported R Functions" y "Argument" para
todo lo que no traiga atributo: 12 de las 42 funciones de usuario, y también las 26 definiciones de
los `.Studio.R` y las 25 internas, que están desplegadas y por tanto se registran (informe §2.2 y
§3.4). `A-13` cubre las 12 de usuario; este ítem cubre lo demás que sí debe documentarse, y su
primer paso es la decisión de §3.4: si los `.Studio.R` dejan de desplegarse al directorio de
funciones (`B-08`), desaparecen del asistente y de este alcance. El material **ya existe** en 28
sidecars y en un diccionario de 37 KB, y no llega al sitio donde el usuario lo necesita. Además todas las funciones dinámicas se registran con
la misma firma de 16 argumentos, con independencia de su aridad real. Generar la descripción, la
categoría y los textos de argumento desde los sidecars en el momento del registro, y acotar la
firma a la aridad real de cada función.

**Precaución de diseño.** Si el sidecar pasa a ser una segunda fuente de la misma ayuda que ya
vive en `attr(fn, "description")`, hay que declarar la precedencia por escrito, o el resultado es
que la ayuda que el usuario ve depende de qué camino ganó. Lo coherente con `A-13` es que el
atributo del `.R` manda y el sidecar solo rellena lo que el atributo no trae. Y como el mapeo
argumento-texto del atributo es **posicional** (informe §3.4) mientras el sidecar lo tiene por
nombre, la fusión debe hacerse contra `formals()`, no contra el orden del sidecar.

**Rutas:** `src\Core\src\excel_api_functions.cc:194, 235, 253, 268, 284-296`;
`src\ControlR\src\rinterface_common.cc:803-859` (donde hoy se construye el descriptor);
`src\Install\functions\*.json`.

**Invariantes:** `INV-CORE-01` (el registro sigue ocurriendo solo en `xlAutoOpen`) e `INV-SJ-02`
(`function_name_xll` debe seguir coincidiendo exactamente con el nombre en `globalenv()`).
Requiere que `INV-LR-04` esté ya reformulada (§5.1).

**Motivado por:** `PROD-08` (alta), `PROD-09` — informe §3.2.

#### C-11 · NEVEN Enterprise: declarar explícitamente fuera del alcance de la tesis

**Prioridad:** P3 · **Coste:** S, media jornada · **Riesgo:** Nulo.

**Descripción.** La especificación propone llevar NEVEN a multiplataforma con capa cloud, macOS,
Excel Web y despliegue corporativo. Es una dirección legítima y de otro orden de magnitud: su
primer requisito contradice el supuesto que sostiene toda la arquitectura actual, que es un XLL de
Windows con procesos hijo locales y rutas absolutas en `C:\NEVEN\`. Mientras esté como
especificación activa, sus 24 tareas aparecen en cualquier recuento de pendientes y compiten por
atención con los arreglos de P0. Marcarla como dirección estratégica fuera del alcance de la
entrega de tesis, con una nota de una línea, y mantenerla fuera del plan hasta que la tesis esté
entregada. Si se quiere avanzar algo en esa dirección con coste casi nulo, lo que de verdad la
habilita es `B-12` (offline y dependencias vendorizadas) y `A-11` (configuración única): ambas
reducen el acoplamiento con la máquina.

**Rutas:** `.kiro\specs\neven-enterprise\` (nota de alcance) y el archivo de especificaciones de
`B-21`.

**Invariantes:** ninguna hoy. Si algún día se acomete, chocaría con buena parte de P1 y P3 (rutas
absolutas, pipes locales, `C:\NEVEN\`): entonces la ontología tendría que revisarse en bloque, y
conviene saberlo antes de empezar, no después.

**Motivado por:** `MEJ4-06` — informe §6.6.

---

## 5. Cambios que requieren modificar la ontología

Restricción del proyecto: una propuesta que viola una invariante no se implementa aunque sea
técnicamente posible; si el plan concluye que una invariante debe cambiar, se dice explícitamente,
se nombra y se justifica. **Primero se actualiza el YAML, después se implementa.** Son cuatro
reformulaciones y cuatro adiciones.

### 5.1 `INV-LR-04` — reformular. Bloquea `A-13` y `C-09`

**Dónde:** `src\docs\ontologia\neven-core\neven-ontology-p2.yaml:660`.

**Texto actual:** exige `attr(NombreFuncion, DialogosXCL$Descripcion)` al final de cada `.R`, dice
que `NEVEN$list.functions()` extrae esos atributos "para el Ribbon" y afirma que sin el atributo
"la función no aparece en Excel". Su `como_verificar` (`p2.yaml:666`) es
`Select-String -Pattern 'attr\(.*DialogosXCL'`, con el comentario "debe dar 1 resultado por función
definida".

**Por qué hay que cambiarlo.** El mecanismo que nombra **sí existe**: `DialogosXCL$Descripcion` vale
literalmente `"description"` (`src\libreria\R\R4XCL-0-Interno-2.R:242`), de modo que
`attr(fn, DialogosXCL$Descripcion)` y `attr(fn, "description")` son la misma asignación. Lo que hay
que cambiar son otras cuatro cosas, todas verificadas (informe §3.4):

1. **La consecuencia es falsa.** La visibilidad no depende del atributo:
   `NEVEN$list.functions()` enumera toda función de `globalenv()`
   (`src\startup\startup.r:51-77`, lecturas en `:70-71`) y el registro pone textos de respaldo
   cuando faltan (`src\Core\src\excel_api_functions.cc:292` → `"Exported Function"`, `:296` →
   `"Argument"`). Las funciones sin atributo aparecen en Excel; lo que pierden es la ayuda.
2. **No fija el tipo del valor, y el tipo importa.** El puente descarta el atributo si no llega
   como array (`src\ControlR\src\rinterface_common.cc:814` exige `ValueCase::kArr`), así que una
   cadena simple es silenciosamente inerte. Hay un caso real: `R4XCL-UT-Pivote.R:336`.
3. **No dice que el mapeo a los argumentos es posicional.** Los elementos 2..n de la `list()` se
   asignan a los argumentos por orden (`rinterface_common.cc:843-846, 854`); los nombres son
   documentación. Sin esto escrito, nadie sabe que el orden debe seguir a `formals()`.
4. **El `como_verificar` no detecta las dos formas en uso** y por tanto da 11 donde hay 32. Es el
   patrón que indujo la primera medición errónea de `PROD-08` en esta misma auditoría.

**Redacción propuesta.** Descripción: "cada función exportada desde celda asigna
`attr(fn, "description")`, o su equivalente `attr(fn, DialogosXCL$Descripcion)`, con valor
`list("<descripción>", <ayuda arg 1>, …, <ayuda arg n>)`, cuyos elementos 2..n se asignan a los
argumentos **por posición** en el orden de `formals()`, y `attr(fn, "category")` con valor de
cadena. Un valor que no sea `list()` se descarta en silencio. Sin estos atributos la función
**aparece** en Excel, pero el asistente de funciones muestra `"Exported Function"` y `"Argument"`.
No aplica a los `.Studio.R`, que alimentan DataLab." `como_verificar`:
`attr\(\s*[^,]+,\s*("description"|DialogosXCL\$Descripcion)\s*\)\s*(=|<-)\s*list\(`, con el
recuento esperado declarado como "una por función exportada desde celda", no por función definida.

**Consecuencia de no cambiarlo:** `A-13`(d) y `C-09` se escribirían contra una invariante que
promete lo que no ocurre y calla lo que sí importa, y el test que `B-04` derive de su
`como_verificar` marcaría como incumplidoras a las 21 funciones que usan el literal `"description"`.

### 5.2 `INV-AS-03` — reformular. Solo si se adopta `A-11`

**Dónde:** `neven-ontology-p3.yaml:205`. **Texto actual:** "AgentService corre en el puerto 5556,
no 5555".

**Por qué:** la invariante fija un número sin declarar quién más puede usarlo, y hoy tres servicios
reclaman el 5556 (AgentService, el servidor de audiolibros y el `fallbackPort` de Studio). Al no
decir nada sobre exclusividad, no impidió la colisión que rompe el módulo de audiolibros.

**Redacción propuesta:** "cada servicio toma su puerto de `neven-config.json`, los rangos no se
solapan y el arranque falla con mensaje explícito si el puerto está ocupado por otro servicio de
NEVEN; 5556 es el valor por defecto de AgentService".

**Importante:** **`A-02` no requiere este cambio.** Mover el servidor de audiolibros a un puerto
propio respeta la invariante tal como está, y es la corrección inmediata. El cambio solo hace falta
si se adopta el registro de puertos en configuración.

### 5.3 `INV-SB-03` — ampliar. Bloquea la parte SQL de `A-01`

**Dónde:** `neven-ontology-p2.yaml:283`. **Texto actual:** `/api/query` solo acepta
`SELECT`/`WITH`/`SHOW`/`DESCRIBE`; cualquier otro statement devuelve HTTP 400.

**Por qué:** la invariante **se cumple literalmente** (`neven_http_server.py:523-533`) **y es
insuficiente**: en DuckDB, las funciones de tabla que leen ficheros del disco se invocan desde un
`SELECT`, de modo que "solo SELECT" no impide la lectura de ficheros a través de la base de datos;
y `/api/groupby` interpola nombres de columna sin escapar. El proyecto presenta esta invariante
como el control del endpoint.

**Redacción propuesta:** mantener la restricción de sentencia y **añadir** que los identificadores
nunca se interpolan sin validarse contra `DESCRIBE dataset`, que las funciones de tabla permitidas
son una lista blanca explícita, y que la conexión del endpoint es de solo lectura sobre el dataset
cargado.

**Nota:** no se propone eliminar la invariante ni relajarla. La parte de `A-01` que solo valida
identificadores y parametriza rutas **no** necesita este cambio y puede hacerse ya.

### 5.4 `INV-CMN-02` — corregir el mecanismo declarado y la política de ausencia. Bloquea `A-04`

**Dónde:** `neven-ontology-p1.yaml:347`. **Texto actual:** `VerifyScriptIntegrity()` verifica
**HMAC** de cada fichero de `C:\NEVEN\functions\` antes de enviarlo al motor.

**Por qué:** tres desajustes verificados. (a) No es HMAC: es SHA-256 sin clave
(`SecurityService.cc:56-93`), de modo que quien puede reescribir el `.R` puede reescribir el
`.sha256`. (b) La verificación es *fail-open*: devuelve `true` cuando falta el fichero de hash
(`:34-40`). (c) En producción hay **0** ficheros `.sha256` para 92 scripts, así que la invariante
está violada en los datos aunque se cumpla en la lógica.

**Redacción propuesta:** decir SHA-256 y no HMAC; declarar la política ante ausencia de hash
(rechazar y registrar, **tras** el despliegue de los hashes); y declarar que el instalador y
`Sync-Dist.ps1` son responsables de generarlos.

**Por qué SHA-256 y no implementar HMAC de verdad:** la clave tendría que vivir en la misma máquina
donde el atacante del modelo de amenazas es un usuario local; embebida en el XLL es ofuscación, no
secreto. El control que de verdad protege estos ficheros es la ACL (`A-05`). Declararlo así es más
honesto que prometer un HMAC que no añade fuerza.

### 5.5 Cuatro invariantes nuevas, que no contradicen ninguna de las 62

| Propuesta | Dónde | Motivo | Ítem que la necesita |
|---|---|---|---|
| **a. ACL del directorio de producción** — `C:\NEVEN\` y sus subdirectorios no deben ser escribibles por `Authenticated Users`; los directorios que el runtime necesita escribir se enumeran explícitamente | `p1.yaml` | Ninguna de las 62 cubre los permisos del árbol de producción, que es la vía por la que una cuenta local cualquiera ejecuta código en la sesión de otra | `A-05` |
| **b. Autenticación de la API local** — ninguna ruta `/api/*` responde sin token y sin validación de origen; el CORS no es comodín | `p2.yaml` | Es el hallazgo crítico del eje de seguridad y no hay invariante que lo gobierne | `A-01` |
| **c. Alcance del sandbox** — qué cubre, qué no cubre, en qué puntos se aplica y qué no promete | `p1.yaml` | Ninguna de las 62 describe el sandbox, que es el control que `SECURITY.md` presenta como principal y que no se aplica en la vía por la que hoy entra la mayor parte del código | `A-10` |
| **d. Fuente única de artefacto desplegado** — cada fichero desplegado en `C:\NEVEN\` tiene exactamente un origen declarado en el repositorio, y la paridad se comprueba por nombre y hash, nunca por conteo | `p4.yaml` | Cinco copias del servidor HTTP con cinco hashes, una regla de steering que apunta a la copia equivocada, 21 artefactos ejecutables en producción sin origen, 20 ficheros con el mismo nombre y contenido distinto (dos de ellos con más contenido en producción que en el repositorio) y 11 ficheros del repositorio que nunca se desplegaron (informe §8.1) | `B-08` |

### 5.6 Ítems condicionados, sin cambio de ontología

| Ítem | Invariantes que toca | Condición |
|---|---|---|
| `B-19` | `INV-SB-01..05`, `INV-TF-01/03/04` | `B-02` y `B-03` antes, con tests que fijen las cinco invariantes del servidor. Precedente de incidente documentado |
| `A-23`(a) | `INV-CJ-01`, `INV-CJ-02` | Reconstruir `neven_julia.dll` (1,04 GB), actualizar `neven_julia.version` y revalidar el precompile independiente |
| `C-03` | `INV-SJ-02`, `INV-SJ-03` | Actualizar `tipo_outputs[]` del sidecar manteniendo reservado el `id == 0` para la ayuda |
| `A-04` | `INV-CMN-02` | Orden interno obligatorio de cuatro pasos; invertirlo deja NEVEN sin funciones |

---

## 6. Lo que no entra en el plan, y por qué

Nueve cosas que parecen mejoras obvias y quedan fuera. Se enumeran para que no se reintroduzcan
por inercia en la siguiente iteración.

1. **Modo degradado que registre funciones de sustitución tras conectar los motores.** Sería la
   respuesta natural a `PROD-10`, y **choca de frente con `INV-CORE-01`**: `MapFunctions()` y
   `RegisterFunctions()` solo pueden ejecutarse durante `xlAutoOpen`; desde un temporizador,
   `xlfRegister` devuelve error 2 y **todo** aparece como `#¿NOMBRE?`. El comentario de
   `src\Core\src\rj2xcl.cc:544-550` documenta que esa vía ya se probó y causó cuelgues. La
   alternativa viable es `C-01` y `C-02`: no arreglan la degradación, pero el usuario sabe qué pasa.
2. **CSP en el visor WebView2.** Descartada por el usuario el 2026-08-19 con razón escrita: el HTML
   que genera R lleva `<script>` inline, la CSP necesitaría `unsafe-inline` y perdería la mayor
   parte de su protección, con riesgo medio-alto de romper Plotly, D3, Leaflet y KaTeX. **No se
   reabre.** Lo que queda fuera de aquella decisión sí está en el plan: acotar `file:///` a los
   directorios de trabajo y añadir `add_FrameNavigationStarting` para que los iframes hereden el
   filtro de navegación, que ya existe y está bien diseñado. Es el punto **(e) de `A-18`**, con
   `src\Common\ViewerWindow.cc:261-295, 552-626` en sus rutas. Lo único que no entra de `SEC-19`
   es la CSP.
3. **DACL restrictiva en los named pipes como primer paso.** Descartada por el usuario el
   2026-08-19 (riesgo alto, "si falla, el XLL no conecta y Excel se congela"). `A-19` la re-propone
   troceada y en P3, con los pasos de bajo riesgo primero, y deja la DACL como decisión explícita
   del usuario.
4. **Mover `C:\NEVEN\` a `%ProgramFiles%`.** Resolvería `SEC-09` de raíz y no se propone: la ruta
   está asumida por `INV-SR-01..05`, `INV-CMN-02`, `INV-SB-01..05` y por rutas absolutas repartidas
   en el código C++, los scripts de arranque, el servidor Python y el instalador. Es un proyecto,
   no un arreglo. `A-05` endurece las ACL, que es el arreglo acotado.
5. **Refactorizar 596 métodos a `snake_case`.** El documento pide `snake_case` para funciones y el
   código usa `PascalCase` de forma coherente. Cambiar 596 firmas es masivo, sin beneficio y con
   riesgo de ABI. Se corrige el documento (`B-10`), declarando expresamente las excepciones `RJ_` y
   `RJ2XCL` que el usuario mantiene a propósito por compatibilidad.
6. **Reescribir el historial de git por el endpoint de Azure.** Lo filtrado es el identificador de
   un recurso retirado, no una clave. Reescribir el historial de un repositorio con remoto es caro
   y rompe clones. Se propone rotar la clave de ese recurso si sigue vivo y dejar la decisión
   escrita (`A-18`).
7. **`/WX` desde el primer día.** `B-06` sube a `/W3`; añadir `/WX` antes de vaciar la cola de
   avisos bloquearía el build y haría abandonar la mejora.
8. **`module` en la librería Julia como tarea inmediata.** `COD-33` es real, y el coste está
   medido: reconstruir una sysimage de 1,04 GB y revalidar dos invariantes. Va en `A-23`, P3, con
   la condición escrita.
9. **Bundlers, transpiladores o módulos ES en el TaskPane.** `INV-TF-04` lo prohíbe, y la
   invariante **no es el obstáculo** para nada de lo propuesto: `B-19` extrae el JS a ficheros
   servidos con `<script src=>` y globales explícitos, y `B-20` usa un runner en el navegador y
   `node --test`. Tampoco se retoman `roughViz`/Sketch ni Mermaid.js, que la bitácora declara
   bloqueados tras varios intentos.

---

## 7. Secuencia por fases y coste agregado

El orden es por dependencia, no por severidad.

### Fase 0 — Verificación antes que arreglos (3-6 jornadas)

| Ítem | Coste | Por qué primero |
|---|---|---|
| `B-01` mover `.github\` y arreglar el workflow | 0,5-1,5 j | Sin esto nada queda protegido |
| `B-02` runner de pytest | 1-2 j (+2-4 de triaje) | Prerrequisito de `B-03` y `B-19` |
| `B-21` declarar el estado de las 27 especificaciones | 1-2 j | El plan necesita un recuento verdadero: 207 de deuda real, no 461 |
| `C-10` decidir el alcance de NEVEN-SIM | 0,5 j | 109 casillas dependen de esa decisión |

### Fase 1 — Cerrar lo que está abierto al exterior (11-17 jornadas)

| Ítem | Coste | Nota |
|---|---|---|
| `A-01` autenticar la API local | 4-6 j | Con `B-03` (3-4 j) **en paralelo, no después** |
| `A-02` puerto y bind del servidor de audiolibros | 2-3 j | |
| `A-03` endpoint de descarga, URLs y verificación | 1,5-2,5 j | Cierra el pendiente arrastrado |
| `A-08` política única de `srcdoc` | 0,5-1 j | |

### Fase 2 — Integridad del despliegue y del artefacto (12-16 jornadas)

| Ítem | Coste | Nota |
|---|---|---|
| `B-08` fuente única y script de paridad | 3-4 j | Prerrequisito de `A-04` |
| `A-04` integridad real de scripts | 2-3 j | Orden interno obligatorio |
| `A-05` ACL de producción | 3-4 j | Probar en VM, nunca en la instalación viva |
| `A-06` `/guard:cf` en el enlazado | 0,5 j | Más el job del PE en `B-01` |
| `B-09` observabilidad y rotación de logs | 3-4 j | |
| `A-07` guarda de excepciones en los exports | 0,5 j | Independiente; cabe en cualquier hueco |

### Fase 3 — Calidad del producto y de la verificación (30-45 jornadas)

`A-13` librería R (5-7 j, con §5.1 hecho antes) · `B-04` invariantes ejecutables y hook (3-4 j) ·
`B-05` tests de los subsistemas sin cobertura (5-7 j) · `B-06` avisos del compilador (2-4 j) ·
`B-07` reproducibilidad del build (1-2 j) · `B-10` higiene documental y cifras (2-3 j) · `B-15` el
paper (2-3 j) · `A-11` configuración y puertos (3-4 j, con §5.2) · `A-12` WebView2 en el
instalador (1-2 j) · `A-10` sandbox por lenguaje (4-6 j) · `C-01` `=NEVEN.Diagnostico()` (2-3 j).

### Fase 4 — Estructura, capacidades y lo que puede esperar (aprox. 70-110 jornadas)

`B-19` monolitos (8-12 j, condicionado) · `B-11` empaquetado y máquina limpia (5-7 j) · `C-03`
informe estadístico (7-10 j) · `C-05` exportación reproducible (5-8 j) · `C-08` gestor de paquetes
(8-12 j) · `C-07` agente con acciones confirmadas (10-15 j, después de `A-01`) · `A-09` unificar
renderizadores (4-6 j) · `C-04` benchmark Wooldridge (5-7 j) · y el resto de P2-P3: `A-14` a
`A-23`, `B-12` a `B-14`, `B-16` a `B-18`, `B-20`, `C-02`, `C-06`, `C-09`, `C-11`.

### Lectura del coste

Las fases 0 a 2 suman **26-39 jornadas** y son las que cambian el riesgo real del proyecto: dejan
el CI funcionando, los tests ejecutables, la API cerrada, el pendiente de audiolibros resuelto y
verificado, el despliegue con una sola fuente y con integridad, y el XLL con las mitigaciones que
la ontología ya exigía. La fase 3 (**30-45 jornadas**) es lo que un lector de la tesis y un usuario
nuevo notan. La fase 4 es trabajo de varios meses y conviene decidirlo con la entrega de la tesis
delante, no antes.

---

## 8. Dependencias duras

Estas no son preferencias de orden: invertirlas rompe algo.

| Hay que hacer | Antes de | Motivo |
|---|---|---|
| `B-01` (CI que se lee) | `B-03`, `B-04`, `B-16`, `B-17`, el job de citas de `B-15` | Sin CI operativo, los chequeos nuevos no se ejecutan |
| `B-02` (runner de pytest) | `B-03`, `B-19` | Sin runner no hay forma de fijar el comportamiento antes de refactorizar |
| `B-03` (suite de seguridad) | **en paralelo con** `A-01`, no después | Si no, los arreglos quedan sin fijar y una regresión pasa inadvertida |
| `B-08` (fuente única y paridad) | `A-04` paso 3 | Cada `.R` actualizado a mano sin regenerar su hash deja NEVEN sin esa función en *fail-closed* |
| `A-04` pasos 1 y 2 (desplegar hashes) | `A-04` paso 3 (*fail-closed*) | Invertirlo deja NEVEN sin funciones |
| §5.1 (reformular `INV-LR-04`) | `A-13` (parte de atributos), `C-09` | Su texto afirma una consecuencia falsa, no fija el tipo del valor y su `como_verificar` solo detecta una de las dos formas en uso |
| §5.2 (reformular `INV-AS-03`) | `A-11` | `A-02` **no** lo necesita |
| §5.3 (ampliar `INV-SB-03`) | la parte de lista blanca de funciones de tabla de `A-01` | El resto de `A-01` no lo necesita |
| §5.4 (corregir `INV-CMN-02`) | `A-04` | Hoy declara HMAC donde hay SHA-256 |
| `A-13` (`tryCatch` y HC3) | `C-03` | El informe con supuestos se construye sobre funciones que ya no revientan |
| `A-17` (cablear la captura) | `C-05` | Sin captura no hay sesión que exportar |
| `A-01` (autenticación) | `C-07` (agente con acciones) | Un endpoint de acciones sin autenticación es una puerta más |
| `B-11` (instalación en VM limpia) | aplicar `A-05` en la máquina del usuario | Una ACL de más deja a NEVEN sin poder escribir, y el síntoma aparece lejos del cambio |
| `B-19` (extraer el JS inline) | `B-20` (tests de frontend del código hoy inline) | No se puede cargar en un runner lo que vive dentro del HTML |
| `C-10` (decisión de alcance) | contar las 109 tareas de NEVEN-SIM como deuda | Media jornada evita planificar sobre una ambigüedad |

---

## 9. Nota de cierre: estado del árbol de trabajo

El inventario completo está en informe §13. Lo que afecta a quien ejecute este plan: el árbol solo
tiene modificados `.kiro\contexto\CHAT.md` y `CHAT_LARGO.md` (la consolidación de la bitácora que el
usuario pidió) y sin seguimiento `.agents\tasks\`, `$reportPath\` y `NEVEN.code-workspace`, los dos
últimos anteriores a la auditoría. Ningún fichero de código está modificado y nada se escribió en
`C:\NEVEN\`.

`.kiro\contexto\Notebooklm.md` apareció borrado del árbol a mitad de la auditoría sin que ninguna
sesión lo reclamara; al cierre está **restaurado e idéntico a `HEAD`**. No tiene ítem en este plan
porque no hay cambio de código que planificar: lo que queda es cerrar el pendiente 9 de `CHAT.md`
antes del siguiente commit, que es trabajo de bitácora. Se deja escrito porque el riesgo era
concreto —que el siguiente commit arrastrase el borrado sin que nadie lo notara— y porque la causa
del borrado no se determinó.


