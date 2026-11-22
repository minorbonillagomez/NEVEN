# 03 — Eje 3: Seguridad

**Fecha:** 2026-11-20 · **HEAD:** `9eba8b1` (master) · **Prefijo real del código:** `src\`
**Entregable del eje 3 del plan** (`plan-auditoria.md` §3). Nombre de fichero alineado con
`02-notas-codigo.md` por indicación de la tarea, en lugar del `30-seguridad.md` del plan.

---

## 0. Alcance, método y límites

### 0.1 Qué se hizo

Lectura de código y de configuración, más inspección en **solo lectura** de la instalación viva
(`C:\NEVEN\`): ACLs, conteo de ficheros de integridad, certificados, cabeceras PE de los binarios
y contenido del log. No se ejecutó ninguna petición HTTP contra los servidores de NEVEN, no se
construyó ninguna prueba de concepto y no se modificó nada en producción ni en el repositorio
(este fichero es la única escritura).

### 0.2 Marco de severidad usado

NEVEN ejecuta R, Julia y Python en la máquina del usuario **por diseño**
(`src\SECURITY.md:16`). Por tanto:

- Un hallazgo que solo es explotable por alguien que **ya ejecuta código como el usuario
  víctima** no añade riesgo: se clasifica Baja o Informativa, por mucho que suene grave.
- Un hallazgo que **elimina ese requisito** —que permite llegar a la ejecución de código sin
  tener antes ejecución de código como esa persona— sí añade superficie y se clasifica Alta o
  Crítica. Los dos casos que cumplen esto son: (a) la API HTTP local sin autenticación y (b) los
  permisos de escritura de `C:\NEVEN\` para cualquier usuario autenticado de la máquina.
- Los controles que el proyecto presenta como frontera de seguridad y que no lo son se reportan
  como desalineación entre documentación y código, con su severidad propia.

### 0.3 Límites declarados

| Límite | Motivo |
|---|---|
| No se verificó explotación en caliente de ningún endpoint | Requiere lanzar peticiones contra producción; la tarea es analizar y documentar |
| `CETCOMPAT` no verificado sobre el binario | No está en `DllCharacteristics`; vive en el *load config* extendido, cuyo parseo no se abordó |
| Comportamiento real de DuckDB ante sentencias múltiples | No se ejecutó DuckDB; el alcance de `read_csv_auto`/funciones de tabla se razona desde su documentación, no desde una prueba |
| Versión de `werkzeug`/`flask` instalada | No se inventarió el entorno Python de producción; afecta a si la cabecera `Content-Disposition` del endpoint de descarga está protegida por el framework |
| Hallazgos previos sin identificador estable | `src\docs\audit\hallazgos_seguridad.md` (151 secciones, IDs `FOR-*`) es un inventario forense sin campo de estado; el emparejamiento uno a uno no es posible (mismo problema que detectó el eje 2) |

### 0.4 Skills

El plan (`plan-auditoria.md` §3 "Skills a cargar" y §6.4) declara que **no existe ningún skill de
seguridad en el catálogo** —ni AppSec, ni modelado de amenazas, ni OWASP, ni análisis estático de
seguridad, ni criptografía, ni SBOM— y que este eje se audita contra `src\SECURITY.md`, las
invariantes `INV-*`, los informes de `src\docs\audit\` y el código. Se confirma: no se cargó
ningún skill porque ninguno aplica. Sí se cargó la herramienta MCP `tool::rea::binary_overview`
para la parte binaria, y se descartó su uso porque exige abrir y analizar el binario completo
para una pregunta que se responde leyendo 2 bytes de la cabecera PE; se verificó con un parser
propio validado contra `kernel32.dll` (ver SEC-11).

### 0.5 Instrucciones embebidas en ficheros

En los ficheros leídos para este eje no se encontró ninguna directiva dirigida a un agente.
Los ficheros con prompts de agente del proyecto (`src\docs\AGENT_INSTRUCTIONS.md`,
`.agents\skills\*\SKILL.md`, …) ya están inventariados en `00-layout-real.md` §8 y son artefactos
legítimos. Todo el contenido leído se trató como dato.

---

## 1. Veredicto por superficie

Una línea por superficie de la lista de la tarea.

| # | Superficie | Veredicto | Motivo |
|---|---|---|---|
| 1 | **IPC por Named Pipes** (nombres, ACLs, autenticación del extremo, suplantación, validación Protobuf) | **CONFIRMADA (parcial)** | DACL por defecto (`lpSecurityAttributes = NULL`), sin `FILE_FLAG_FIRST_PIPE_INSTANCE`, sin autenticación del extremo y nombre predecible → SEC-12. La validación de los mensajes Protobuf, en cambio, es correcta y acota la longitud antes de deserializar → **descartada** como problema |
| 2 | **El sandbox de los 133 tests** | **CONFIRMADA como no-frontera** | `SandboxTest` tiene 133 tests reales, pero el control es una lista de subcadenas aplicada solo en tres puntos (celda, REPL, AutoLoader sin invocadores), con excepciones de contexto triviales de satisfacer y sin cobertura de la vía HTTP → SEC-02, SEC-23 |
| 3 | **Servidor HTTP 5555: bind, autenticación, CORS, recorrido de rutas** | **CONFIRMADA (crítica)** | Bind correcto a `127.0.0.1`; pero `Access-Control-Allow-Origin: *`, cero autenticación, endpoints de ejecución de código y de escritura de ficheros, y recorrido de rutas en cuatro ramas de servido estático → SEC-01, SEC-03, SEC-04 |
| 4 | **Arreglo 9eba8b1 del endpoint de descarga de audiolibros** | **Travesía DESCARTADA; debilidades nuevas CONFIRMADAS** | `normpath` + comprobación de prefijo bloquea `../`; pero quedan doble decodificación, prefijo sin separador y un *fallback* que entrega cualquier fichero del directorio por coincidencia de prefijo → SEC-17. Funcionalmente **NO VERIFICABLE** sin Excel y servidor TTS: se deja procedimiento (§6) |
| 5 | **TaskPane: XSS al renderizar `html` en `buildSlotElement()`** | **CONFIRMADA** | `srcdoc` con `sandbox="allow-scripts allow-same-origin"` (combinación que anula el aislamiento) y dos `srcdoc` sin atributo `sandbox` → SEC-07 |
| 6 | **Ejecución de código arbitrario desde celdas: controles alrededor y lugar del límite de confianza** | **CONFIRMADA como mal ubicado** | El límite está en la celda de Excel, pero existe una segunda puerta (HTTP→pipe) sin ningún control equivalente, y el sandbox se puede desactivar editando un JSON escribible por cualquier usuario autenticado, sin registro → SEC-02, SEC-09, SEC-14 |
| 7a | **Visor WebView2** (navegación, host objects, contenido remoto) | **CONFIRMADA (menor)** | Filtro de navegación de lista blanca correcto y **cero** `AddHostObjectToScript`; pero `file:///` sin acotar directorio, cinco CDN permitidas, sin CSP y sin filtro de subrecursos (el filtro no cubre `fetch`/XHR) → SEC-19 |
| 7b | **Quarto por `CreateProcess`** (línea de comandos, inyección de argumentos, rutas con espacios) | **DESCARTADA** | Validación de entrada, allowlist de extensión y de formato, rutas entrecomilladas y `CreateProcessA` sin shell → SEC-20. Residual bajo: `quarto_path_` viene de la config (SEC-13) |
| 8 | **Secretos en el árbol y en el historial de git** (`INV-INS-01`) | **CONFIRMADA (baja)** | `INV-INS-01` **se cumple en HEAD**; el historial conserva un endpoint de recurso Azure concreto retirado en `de8d44b`, y hay una contraseña literal de exportación PFX en un fichero versionado → SEC-18, SEC-10 |
| 9a | **Permisos del directorio de producción `C:\NEVEN\`** | **CONFIRMADA (alta)** | `NT AUTHORITY\Authenticated Users : Modify` sobre `C:\NEVEN`, `C:\NEVEN\functions` y `C:\NEVEN\certs` → SEC-09 |
| 9b | **Integridad de scripts (`INV-CMN-02`)** | **CONFIRMADA (alta)** | Verificación *fail-open* y **0** ficheros `.sha256` para 92 scripts desplegados → SEC-08 |
| 9c | **Deserialización** | **DESCARTADA** | Protobuf con validación de marco previa; cero `pickle.load`, cero `yaml.load(`, cero `eval(` en el servidor; el único `exec(compile(...))` es el cargador de ficheros `.py` de NEVEN (riesgo = SEC-08/SEC-09, no deserialización) |
| 9d | **DLL hijacking en el arranque del XLL y de los procesos hijo** | **DESCARTADA (con reserva menor)** | `LoadLibraryA` siempre con ruta absoluta derivada de `R_HOME`/`JULIA_HOME` descubiertos en `HKEY_LOCAL_MACHINE`; `AddDllDirectory` acota las dependencias de R. Reserva: `AddDllDirectory` solo surte efecto con `SetDefaultDllDirectories`, que no se llama en ningún punto |
| 9e | **Prompt injection en el RAG y el agente** | **DESCARTADA parcialmente** | No se encontró ejecución automática de acciones propuestas por el modelo: `/api/functions/create` es un endpoint aparte que invoca la interfaz. El eslabón débil no es el modelo, es que ese endpoint no exige autenticación (SEC-01). Sin marcado de procedencia del contenido RAG → SEC-21 |
| 9f | **Superficie HTTP del servidor de audiolibros** (no estaba en la lista; hallada) | **CONFIRMADA (alta)** | `host='0.0.0.0'` + CORS `*` + sin autenticación, con endpoints de subida y de generación → SEC-16 |
| 9g | **Puente `postMessage` del visor hacia ficheros de cola** (no estaba en la lista; hallado) | **CONFIRMADA (media)** | Inyección JSON por concatenación y volcado íntegro del mensaje a un fichero que consume NEVEN-SIM → SEC-15 |
| 9h | **Barrera SQL `INV-SB-03`** | **CONFIRMADA** | La validación es por prefijo de sentencia; y `/api/groupby` interpola nombres de columna en la consulta sin escapar → SEC-05, SEC-06 |

---

## 2. Hallazgos

Formato: título · superficie · severidad · marca de verificación. Cada uno con evidencia
(ruta y línea), vector y precondiciones, severidad razonada e invariante relacionada.

### SEC-01 · La API HTTP local no tiene autenticación, responde con CORS comodín y expone ejecución de código arbitrario · **CRÍTICA** · VERIFICADO

**Superficie:** servidor HTTP del TaskPane (puerto 5555).

**Evidencia:**

| Qué | Ruta y línea |
|---|---|
| `Access-Control-Allow-Origin: *` en **todas** las respuestas | `src\startup\neven_http_server.py:633-637` (`_add_cors_headers`, invocada por `_send_json`, `_send_error_json` y `_serve_file`) |
| Preflight concedido sin comprobar origen | `:639-643` (`do_OPTIONS` → 204 + mismas cabeceras) |
| Cuerpo interpretado como JSON **sin comprobar `Content-Type`** | `:1091` (`json.loads(self.rfile.read(content_length))`) |
| Endpoints de ejecución de código | `:1110-1112` → `elif path in ('api/r', 'api/python', 'api/julia'): self._handle_script(...)` |
| El código se envía tal cual al motor | `:4332` `_handle_script`, `:4367` `var = client.send_code(lines, wait=True)` |
| Cero comprobación de `Origin`, `Host`, `Referer`, token o sesión | `git grep` sobre el fichero: ninguna aparición |
| Único control de abuso: *rate limiter* | `:646-649` y `:1076-1079` (300 req/60 s → 429) — `INV-SB-04` |

**Vector y precondiciones.** Con NEVEN Studio en marcha (el servidor vive en un hilo demonio de
`ControlPython.exe` o lo arranca `start_studio.py`), un `POST` a `/api/r` con
`{"code": "..."}` ejecuta ese código en el intérprete de R de la sesión del usuario. No hace
falta privilegio alguno: basta alcanzar el puerto. Dos caminos:

1. **Cualquier proceso local, de cualquier usuario de la máquina.** El bind a `127.0.0.1` solo
   excluye la red; no excluye a otros usuarios locales. Un proceso sin acceso al token de la
   víctima consigue ejecución de código *en su sesión*. Esto es exactamente lo que el marco de
   severidad llama "eliminar el requisito previo".
2. **Una página web abierta en cualquier navegador de la máquina.** `ACAO: *` permite leer la
   respuesta y, como el cuerpo se parsea sin mirar `Content-Type`, una petición simple
   (`text/plain`) no necesita *preflight*. Aquí hay un mitigante que **no es de NEVEN**: las
   reglas de acceso a red privada que los navegadores vienen desplegando (preflight especial y
   permiso del usuario para peticiones de contexto público a `localhost`). Depender de eso es
   depender de la versión del navegador del usuario.

En producción el puerto 5555 sirve **HTTPS** (hay `certPath`/`keyPath` en
`C:\NEVEN\neven-config.json` y los ficheros existen; `:4821-4832`), con un certificado
`CN=localhost` **instalado en la raíz de confianza del usuario** (SEC-10). Eso no reduce el
problema: lo hace alcanzable también desde páginas `https://`.

**Severidad razonada: Crítica.** Es el único hallazgo del eje que convierte "visitar una página"
o "tener una cuenta local cualquiera" en "ejecutar código en la sesión de Excel del usuario".
Todo lo demás del informe es, como mucho, una agravante de este.

**Invariantes.** Toca `INV-SB-03` y `INV-SB-04`, que existen y se cumplen, pero que no son
controles de acceso. **Ninguna invariante impide añadir autenticación**: un token local
(fichero en `%LOCALAPPDATA%` con ACL del usuario, enviado en cabecera) más validación estricta
de `Origin` es compatible con `INV-SB-01..05` y con `INV-CP-03`. Si se cambia el puerto, hay que
recordar `INV-CP-03` (la validación de origen de `postMessage` compara contra el origen propio).

### SEC-02 · El sandbox no cubre la vía HTTP→pipe: hay una segunda puerta sin ningún control equivalente · **ALTA** · VERIFICADO

**Superficie:** ejecución de código arbitrario; sandbox.

**Evidencia.** `SandboxVerifier` se invoca en exactamente tres sitios:

| Punto de entrada | Llamada | Observación |
|---|---|---|
| `=NEVEN.r()/.j()/.p()` desde celda | `src\Core\src\basic_functions.cc:157-166` | condicionado a `ConfigService::IsSandboxEnabled()` |
| REPL | `src\Common\IPC\REPLBridge.cc:77` | siempre |
| AutoLoader | `src\Common\AutoLoader.cc:72` y `:98` | siempre, **pero `AutoLoader::LoadAllUserScripts()` no tiene ningún invocador** en el árbol |

Y **no hay ninguna validación en la ruta Python**: `git grep -i "sandbox|blocklist|blacklist|forbidden"`
sobre `src\startup\neven_http_server.py`, `src\ControlPython\startup\datalab_handler.py` y
`src\TaskPane\pipe_client.py` devuelve **cero** coincidencias. El código de `/api/r` viaja a
`PipeClient.send_code()` sin pasar por el verificador de C++.

Además, la ruta real de carga de los scripts desplegados **tampoco** pasa por el sandbox:
`src\Core\src\FileWatchService.cc:68-77` (`LoadLanguageFile`) llama a
`LanguageService::ReadSourceFile` (`src\Core\src\language_service.cc:443-462`), que verifica
integridad (SEC-08) pero **no** valida contenido. El único camino que sí valida contenido
(`AutoLoader`) está muerto.

**Vector y precondiciones.** Las mismas que SEC-01. El efecto es que el blocklist, que el
proyecto presenta como mitigación de "Inyección de comandos OS"
(`src\SECURITY.md:28`), no está presente en el camino por el que hoy entra la mayor parte del
código que NEVEN ejecuta (TaskPane, DataLab, hot-reload de `C:\NEVEN\functions`).

**Severidad razonada: Alta.** No es que el sandbox sea evitable (eso ya lo admite
`SECURITY.md:54`); es que en la vía principal **no se aplica**, de modo que la protección
declarada no existe donde más tráfico hay.

**Invariantes.** Ninguna. Aplicar el verificador también en la ruta Python no contradice
`INV-SB-*`; sí exige decidir qué hacer con los falsos positivos de SEC-23 antes de activarlo, o
el TaskPane dejará de funcionar para código legítimo.

### SEC-03 · `/api/save_script` escribe en cualquier ruta absoluta del disco; el fichero escrito se ejecuta solo · **CRÍTICA** (en combinación con SEC-01) · VERIFICADO

**Superficie:** servidor HTTP 5555; ejecución de código.

**Evidencia.** `src\startup\neven_http_server.py:2783-2814`:

- `path = body.get("path", "").strip()` — ruta tal cual, sin normalizar ni acotar a ningún
  directorio base (`:2789`).
- Único control: la extensión debe estar en `(".r", ".py", ".jl", ".R", ".python")` (`:2795-2798`).
- `os.makedirs(dirpath, exist_ok=True)` — **crea los directorios que falten** (`:2802-2804`).
- `open(path, "w", encoding="utf-8", newline="\n")` (`:2805`) — cumple `INV-SB-02` en encoding,
  que es precisamente lo que hace que el fichero escrito sea válido para el motor.

Y lo escrito se ejecuta sin intervención del usuario: `FileChangeWatcher` vigila el directorio de
funciones y `FileWatchService::OnFilesChanged` → `LoadLanguageFile` → `ReadSourceFile`
(`src\Core\src\FileWatchService.cc:53-77`), que en el lado de R hace `source()` y en Python
`exec(compile(code, path, "exec"), globals())` (`src\startup\startup.py:72`).

**Contraste.** El endpoint hermano `/api/functions/create` **sí** lo hace bien:
`src\startup\neven_http_server.py:2669-2676` exige `^[A-Za-z0-9_\-\.]+$` (solo nombre base),
valida la extensión contra el lenguaje y resuelve contra `functionsDir`. Es el patrón correcto y
está en el mismo fichero; `_handle_save_script` debería reducirse a eso.

**Vector y precondiciones.** Un `POST` sin autenticación (SEC-01) con una ruta dentro de
`C:\NEVEN\functions\` deja un `.R` que el *hot-reload* ejecuta en segundos. También permite
sobrescribir los scripts de arranque de `C:\NEVEN\startup\` (SEC-08: no hay integridad que lo
impida) y plantar `.py` en cualquier directorio donde la extensión importe.

**Severidad razonada: Crítica junto a SEC-01.** Por sí solo (si el API estuviera autenticada)
sería Media: un usuario legítimo del TaskPane ya puede ejecutar código, así que escribir un `.R`
no le añade poder. Lo que lo vuelve crítico es la combinación con la falta de autenticación y con
la ejecución automática del fichero.

**Invariantes.** `INV-SB-02` se cumple y debe seguir cumpliéndose tras el arreglo (UTF-8 sin BOM,
`newline='\n'`). Acotar la escritura a un directorio base no toca ninguna invariante.

### SEC-04 · Recorrido de rutas en cuatro ramas de servido estático del servidor Studio · **ALTA** · VERIFICADO (el código) / HIPÓTESIS (la explotación concreta)

**Superficie:** servidor HTTP 5555.

**Evidencia.** `src\startup\neven_http_server.py:652`:

```
path = unquote(parsed.path).lstrip('/')
```

Se decodifica **antes** de cualquier normalización y después se concatena sin contención:

| Rama | Línea | Construcción |
|---|---|---|
| `/viewers/*` | `:933-936` | `os.path.join(viewers_dir, path[8:])` → `_serve_file` |
| `/catalog/*` | `:963-968` | `os.path.join(catalog_dir, path[8:])` (con `isfile` previo) |
| `/docs/*` | `:978-983` | `os.path.join(docs_dir, path[5:])` → `_serve_file` |
| estático final | `:1038-1043` | `os.path.join(static_dir, path)` → `_serve_file` |

`_serve_file` (`:1045-1073`) solo comprueba `os.path.isfile` y abre. No hay `os.path.realpath`,
ni `os.path.commonpath`, ni lista blanca. Dos clases de abuso derivan de la decodificación previa:
segmentos `..` codificados (que el navegador no normaliza porque los ve codificados) y rutas
absolutas con letra de unidad, que `os.path.join` adopta descartando la base.

**Contraste.** La rama `/file?path=` (`:988-1016`) **sí** valida: `os.path.normpath` y
`startswith` contra tres directorios permitidos, con 403 y registro en caso contrario. Es el
patrón correcto, en el mismo fichero y a 20 líneas de las ramas que no lo aplican. (Su
comprobación tiene la misma debilidad de prefijo sin separador que SEC-17, pero en sentido
conservador: deniega más de lo que debería, no menos.)

**Vector y precondiciones.** Lectura de cualquier fichero legible por el proceso del servidor
(que corre como el usuario). Con `ACAO: *` (SEC-01) la respuesta es legible desde otro origen, lo
que convierte una lectura local en exfiltración. Marco la **explotación** como HIPÓTESIS porque
no se emitió ninguna petición: lo verificado es la ausencia de contención en el código.

**Severidad razonada: Alta.** Lectura arbitraria de ficheros sin autenticación previa. No es
crítica solo porque SEC-01 y SEC-03 ya dan algo peor (escritura y ejecución).

**Invariantes.** Ninguna. Añadir `commonpath` y servir solo bajo los directorios configurados no
toca `INV-SB-*`.

### SEC-05 · `INV-SB-03` es una barrera de prefijo: un `SELECT` de DuckDB puede leer el disco · **MEDIA** · VERIFICADO (el código) / HIPÓTESIS (alcance en DuckDB)

**Superficie:** `/api/query`, barrera SQL.

**Evidencia.** `src\startup\neven_http_server.py:523-533` (`execute_query`): se eliminan las
líneas que **empiezan** por `--`, se pasa a mayúsculas y se exige que la cadena **empiece** por
`SELECT`, `WITH`, `SHOW` o `DESCRIBE`. Eso es todo. No hay análisis sintáctico, ni lista blanca
de funciones, ni restricción del motor.

Consecuencias que se derivan del diseño de DuckDB (documentadas, no probadas aquí): las funciones
de tabla que leen ficheros del disco se invocan **desde un `SELECT`**, de modo que la restricción
"solo SELECT" no impide leer ficheros arbitrarios a través de la base de datos. Lo mismo aplica a
`_handle_load_file` (SEC-06), que carga cualquier fichero del disco en la tabla `dataset` y luego
es consultable por este endpoint.

**Severidad razonada: Media.** La invariante protege de lo que dice proteger (escrituras y DDL por
prefijo de sentencia) pero no de la lectura de ficheros, y el proyecto la presenta como el control
de este endpoint. Sumada a SEC-01 es una segunda vía de lectura arbitraria; por sí sola, para un
usuario legítimo del TaskPane, no añade poder.

**Invariantes.** `INV-SB-03` **se cumple literalmente** y es **insuficiente**. No propongo
eliminarla: propongo complementarla (ver POR MEJORAR MEJ-S03). Si en el futuro se decide
reformular el texto de la invariante para exigir también una lista blanca de funciones de tabla,
eso es un cambio de ontología que hay que escribir primero en
`src\docs\ontologia\neven-core\neven-ontology-p2.yaml:283`.

### SEC-06 · Inyección SQL en `/api/groupby` y en `/api/load` por interpolación de cadenas · **MEDIA** · VERIFICADO

**Superficie:** barrera SQL, DuckDB.

**Evidencia.**

- `src\startup\neven_http_server.py:4262-4274` (`_handle_groupby`): `group_column` y
  `value_column` se toman del cuerpo sin validar y se pasan a `execute_groupby`.
- `:500-514` (`execute_groupby`): la métrica **sí** se valida contra `VALID_METRICS` (`:487`),
  pero los nombres de columna se interpolan en una f-string dentro de comillas dobles
  (`f'SELECT "{group_column}" as grp, {agg_expr} ... GROUP BY "{group_column}" ...'`) sin escapar
  las comillas dobles. Un nombre de columna que contenga `"` cierra el identificador y continúa la
  consulta.
- `:2965-2983` (`_handle_load_file`): `path` se interpola dentro de comillas simples en
  `read_parquet('{path}')` / `read_csv_auto('{path}')` sin escapar. Aquí el requisito previo
  `os.path.isfile(path)` limita mucho la explotación, pero el patrón es el mismo.
- Para contraste, `:440-480` (estadísticas por columna) también interpola, pero los nombres vienen
  de `DESCRIBE dataset`, es decir del propio motor: ahí no hay entrada externa.

**Vector y precondiciones.** Las de SEC-01. El resultado es SQL arbitrario en DuckDB, que es la
vía por la que se esquiva `INV-SB-03` sin siquiera discutir prefijos.

**Severidad razonada: Media**, por el mismo motivo que SEC-05: añade capacidad al atacante remoto
de SEC-01, no al usuario legítimo.

**Invariantes.** Ninguna. Parametrizar o validar los identificadores con una lista blanca tomada
de `DESCRIBE dataset` **refuerza** `INV-SB-03`.

### SEC-07 · XSS en el renderizador de resultados: `srcdoc` con `allow-scripts allow-same-origin`, y dos `srcdoc` sin `sandbox` · **ALTA** · VERIFICADO

**Superficie:** TaskPane, `buildSlotElement()`.

**Evidencia.**

| Ruta y línea | Qué hace |
|---|---|
| `src\TaskPane\datalab.js:1593-1599` | `case 'html':` → `iframe.setAttribute('srcdoc', slot.value)` con `sandbox="allow-scripts allow-same-origin"` |
| `src\TaskPane\chart-gallery.js:1770` | `iframe.setAttribute('srcdoc', html)` — **sin atributo `sandbox`** |
| `src\TaskPane\taskpane.js:1235` | `iframe.srcdoc = res.html` — **sin atributo `sandbox`** |
| `src\TaskPane\datalab.js:1606-1620` | para `scalar`/`text` usa `textContent`: correcto, sin riesgo |

`allow-scripts` junto a `allow-same-origin` es la combinación que anula el aislamiento: el
documento de `srcdoc` hereda el origen del documento que lo contiene y, con scripts permitidos,
puede alcanzar `window.parent`. Los dos `srcdoc` sin `sandbox` no tienen ni aislamiento nominal.

Densidad de sumideros adicionales (medida, como contexto, no como hallazgo individual):
`taskpane.html` 114 asignaciones a `.innerHTML`, 22 de ellas con concatenación;
`taskpane.js` 81/4; `datalab.js` 28/2; `ayuda.js` 9/4.

**Vector y precondiciones.** El `slot` de tipo `html` lo produce R/Julia/Python. Si en ese HTML
entra texto que el usuario no escribió —el nombre de una columna de un CSV descargado, el
contenido de una celda de un libro recibido por correo, un fragmento de documento del RAG— ese
texto se ejecuta como JavaScript con el origen del TaskPane. Desde ahí: `window.parent.Office`
para leer y escribir el libro, y el API local del mismo origen (SEC-01, SEC-03) para ejecutar
código.

**Severidad razonada: Alta.** No requiere que el atacante ejecute nada: requiere que un dato
llegue a un informe. Es el camino más plausible por el que un libro de Excel compartido se
convierte en ejecución de código, y `SECURITY.md:118` lo declara riesgo aceptado para las
fórmulas, no para el renderizador del TaskPane.

**Invariantes.** `INV-TF-01` manda que `buildSlotElement()` sea el único renderizador; el eje 2
lo dictaminó **PARCIAL** (COD-41) y aquí se ve el coste en seguridad: tres renderizadores
distintos con tres políticas distintas de `srcdoc`. Arreglar esto **cierra** `INV-TF-01` y
`INV-TF-04` no estorba (escapar y fijar `sandbox` no necesita empaquetador).

### SEC-08 · La verificación de integridad de scripts es *fail-open* y en producción no hay ni un `.sha256`: `INV-CMN-02` incumplida · **ALTA** · VERIFICADO

**Superficie:** integridad de scripts; directorio de producción.

**Evidencia.**

- `src\Common\Security\SecurityService.cc:34-40`: si el fichero `<script>.sha256` no existe,
  **devuelve `true`** ("No hash file — allow execution but log for audit trail"; el comentario
  menciona un registro que no se emite en esa rama).
- Es un SHA-256 sin clave (`:56-93`), no un HMAC: quien puede reescribir el `.R` puede reescribir
  el `.sha256`. `INV-CMN-02`
  (`src\docs\ontologia\neven-core\neven-ontology-p1.yaml:347`) y `src\SECURITY.md` lo describen
  como HMAC. No lo es.
- Conteo en producción (solo lectura):

| Directorio | Scripts | `.sha256` |
|---|---:|---:|
| `C:\NEVEN\functions` | 63 `.R` + 11 `.jl` + 18 `.py` = **92** | **0** |
| `C:\NEVEN\startup` | 3 (`startup.r`, `startup.jl`, `startup.py`) | **0** |

- El repositorio **sí** tiene `src\startup\startup.r.sha256` y `src\startup\startup.jl.sha256`
  (64 bytes cada uno): el instalador no los despliega. El control existe en el repo y se pierde
  en el despliegue.

**Vector y precondiciones.** Cualquiera que pueda escribir en `C:\NEVEN\functions` (SEC-09: todo
usuario autenticado; SEC-03: cualquier petición HTTP) planta código que se ejecuta sin que la
verificación lo note, porque no hay con qué comparar.

**Severidad razonada: Alta.** No es que el control esté mal implementado: es que **no está
operando** sobre nada de lo desplegado, y la ontología lo da por hecho.

**Invariantes.** `INV-CMN-02`: **VIOLADA en producción** (cumple en la lógica, vacía en los
datos). Arreglarla es desplegar los `.sha256` y decidir la política de ausencia. **Importante:**
cambiar *fail-open* por *fail-closed* sin desplegar antes los hashes deja a NEVEN sin funciones;
el orden importa y va escrito en el plan (PEN-S04).

### SEC-09 · `C:\NEVEN\` es escribible por cualquier usuario autenticado de la máquina · **ALTA** · VERIFICADO

**Superficie:** permisos del directorio de producción.

**Evidencia** (`Get-Acl`, solo lectura):

```
C:\NEVEN            BUILTIN\Administradores  FullControl   (heredada)
                    NT AUTHORITY\SYSTEM      FullControl   (heredada)
                    BUILTIN\Usuarios         ReadAndExecute
                    NT AUTHORITY\Authenticated Users  Modify   (heredada)
C:\NEVEN\functions  … mismas entradas, Authenticated Users : Modify
C:\NEVEN\certs      … mismas entradas, Authenticated Users : Modify
```

Son las ACL heredadas de la raíz `C:\`: instalar en `C:\NEVEN` en lugar de bajo
`%ProgramFiles%` (que sí restringe la escritura a administradores) deja todo el árbol modificable
por cualquier cuenta autenticada, y el instalador no endurece las ACL
(`src\Install\Install-NEVEN.ps1`: ninguna llamada a `Set-Acl`/`icacls`).

**Qué hay en ese árbol que importe:**

| Fichero | Consecuencia de poder escribirlo |
|---|---|
| `C:\NEVEN\functions\*.R/.jl/.py` (92) | ejecución de código en la sesión de Excel de otro usuario (hot-reload, SEC-02/SEC-08) |
| `C:\NEVEN\startup\startup.*` | ejecución en cada arranque del motor |
| `C:\NEVEN\neven-config.json` | `NEVEN.sandboxEnabled`, rutas de R/Julia/Quarto, `certPath`/`keyPath` (SEC-13, SEC-14) |
| `C:\NEVEN\certs\localhost.key` | clave privada de un certificado de confianza (SEC-10) |
| `C:\NEVEN\NEVEN64.xll`, `*.dll`, `Control*.exe` | sustitución del binario que Excel carga |
| `C:\NEVEN\data\bridge_queue.json`, `sim_command.json` | colas que consumen NEVEN-SIM y Excel (SEC-15) |
| `C:\NEVEN\neven.log` | 119,6 MB legible por `BUILTIN\Usuarios` y **modificable** por cualquiera: con 1 595 421 líneas `Startup script line`, 8 448 líneas `StartChildProcess:` (líneas de comandos completas), 38 `write-cell` (valores de celda) y 143 `Sandbox BLOCKED` (primeros 30 caracteres del código del usuario). Divulgación de información y, peor, **el rastro de auditoría que `SECURITY.md` invoca es borrable por el atacante** |

**Vector y precondiciones.** Requiere una cuenta local (cualquiera, sin privilegios) o un proceso
corriendo como el propio usuario. Es el otro hallazgo que elimina el requisito previo de "ya
ejecuto código como la víctima": en una máquina con varias cuentas, la cuenta A consigue
ejecución en la sesión de la cuenta B.

**Severidad razonada: Alta** en multiusuario; **Media** en un portátil de un solo usuario, donde
el efecto real se reduce a persistencia cómoda para malware que ya corre como ese usuario. Lo digo
explícitamente porque el caso de NEVEN hoy (tesis, una máquina) es el segundo.

**Invariantes.** Ninguna de las 62 fija ACL del directorio de producción: es un **hueco de la
ontología**, no una violación. Propongo añadir invariante (ver NUEVAS IDEAS IDEA-S02); no se
propone cambiar `C:\NEVEN\` de sitio, porque `INV-SR-01..05`, `INV-CMN-02`, `INV-SB-01..05` y
media docena de rutas absolutas del código y de los scripts asumen esa ruta, y moverla es un
proyecto, no un arreglo.

### SEC-10 · Clave privada en claro de un certificado instalado en la raíz de confianza, en un directorio escribible por cualquier usuario · **MEDIA** · VERIFICADO

**Superficie:** secretos y despliegue.

**Evidencia.**

- `src\Install\Install-NEVEN.ps1:1082-1111` y `src\TaskPane\Generate-Cert.ps1:33-74`: se crea un
  certificado autofirmado y se **añade a `Cert:\CurrentUser\Root`** (raíz de confianza del
  usuario).
- `Generate-Cert.ps1:55`: la clave se exporta a PEM con `openssl pkcs12 -nocerts -nodes`, es
  decir **sin cifrar**, y la contraseña de exportación del PFX está **literal en el fichero
  versionado** (`:43`, `:55`, `:56`; no se transcribe el valor). Mismo patrón en
  `Install-NEVEN.ps1` (zona de las líneas 1090-1100).
- Estado real (solo lectura): `C:\NEVEN\certs\` contiene `localhost.cer`, `.crt`, `.key` (1 911 B,
  PEM sin cifrar) y `.pfx`, con ACL `Authenticated Users : Modify`. El certificado
  `CN=localhost`, SAN `DNS=localhost`, EKU servidor+cliente, **válido hasta 2036-07-24** (10 años),
  está presente en `Cert:\CurrentUser\Root`.

**Vector y precondiciones.** Cualquier usuario local lee la clave privada y puede presentar ese
certificado como `https://localhost` ante el navegador de la víctima (que lo trata como válido
por estar en su raíz). No es una CA —no hay `basicConstraints: CA`, y el SAN es solo
`localhost`—, de modo que **no** permite emitir certificados para otros dominios: el abuso se
limita a suplantar el propio servicio local. Añadido: la clave está en el repositorio del
instalador como procedimiento, no como fichero (no hay `.key`/`.pfx` versionados; se verificó el
historial).

**Severidad razonada: Media.** Vigencia de 10 años, clave sin cifrar, directorio abierto y
contraseña literal en el repo son cuatro malas prácticas sumadas; el techo del daño, en cambio,
es suplantar `localhost` ante el usuario, que ya está expuesto por SEC-01.

**Invariantes.** `INV-INS-01` habla de credenciales en `neven-config.json`, no de este fichero:
no se viola, pero el espíritu es el mismo. Propongo extender su alcance (ver IDEA-S02).

### SEC-11 · `NEVEN64.xll` se distribuye **sin Control Flow Guard**: `INV-BLD-02` incumplida en el artefacto · **MEDIA** · VERIFICADO

**Superficie:** mitigaciones del binario.

**Método.** Lectura del campo `DllCharacteristics` del *optional header* PE (desplazamiento
`+0x46`, PE32+ `magic = 0x20B`) con un parser propio **validado contra binarios de referencia**:
`kernel32.dll` → `0x4160` (CFG presente), `notepad.exe` → `0xC160`. Sin esa validación el dato no
sería defendible.

**Evidencia.**

| Binario | `DllCharacteristics` | DYNAMICBASE | NXCOMPAT | **GUARD_CF** |
|---|---|:---:|:---:|:---:|
| `src\Build\Dist\NEVEN64.xll` | `0x0160` | sí | sí | **NO** |
| `src\Install\Dist\NEVEN64.xll` | `0x0160` | sí | sí | **NO** |
| `C:\NEVEN\NEVEN64.xll` (producción) | `0x0160` | sí | sí | **NO** |
| `NEVENRibbon.dll` (repo y producción) | `0x4160` | sí | sí | sí |
| `ControlR.exe` / `ControlJulia.exe` / `ControlPython.exe` | `0xC160` | sí | sí | sí |
| `C:\NEVEN\NEVEN-SIM.xll` | `0x4160` | sí | sí | sí |

Es decir: **todos** los binarios de NEVEN llevan CFG **excepto el principal**, el que Excel carga
en su propio proceso.

**Causa — HIPÓTESIS.** `src\CMakeLists.txt:20` pone `/guard:cf` en `add_compile_options` y
`:24` pone `/DYNAMICBASE /NXCOMPAT /CETCOMPAT` en `add_link_options`, **sin `/guard:cf` en el
enlazado**. `NEVEN_Core` es el único objetivo construido en dos pasos a través de una
*object library* (`src\Core\CMakeLists.txt:5-7`: `add_library(NEVEN_Core_Objects OBJECT ...)` +
`add_library(NEVEN_Core SHARED $<TARGET_OBJECTS:...>)`), de modo que las directivas que el
compilador deja en los `.obj` no llegan al enlazado de la misma forma que en los objetivos
normales. No lo he comprobado reconstruyendo: lo marco como hipótesis y la prueba es trivial
(añadir `/guard:cf` a `add_link_options` y volver a leer los 2 bytes).

**Por qué `build_verification_tests.cc` no lo detecta.** Porque lee el `CMakeLists.txt` y
comprueba que los cinco flags están **escritos**, no que estén **en el binario**
(`INV-TEST-01`). El test pasa y la invariante está incumplida: es el caso de libro de un control
que verifica la intención en vez del resultado.

**Severidad razonada: Media.** CFG es defensa en profundidad frente a corrupción de memoria; su
ausencia no es una vulnerabilidad explotable por sí misma, y NEVEN no parsea formatos hostiles
complejos en el XLL. Lo que sí es grave es el fallo de aseguramiento: una invariante declarada
cumplida y verificada por un test, incumplida en el producto desde hace al menos un mes
(binarios del 20-21 de octubre). `CETCOMPAT`: **NO VERIFICADO** por este método.

**Invariantes.** `INV-BLD-02`: **VIOLADA en el artefacto** (cumple en el `CMakeLists`).
`INV-TEST-01` se cumple y es insuficiente. No propongo cambiar ninguna de las dos: propongo
añadir la comprobación sobre el PE (coincide con IDEA-08 del eje 2).

### SEC-12 · Named pipes con DACL por defecto, sin autenticación del extremo y con nombre predecible · **MEDIA** · VERIFICADO (el código) / HIPÓTESIS (la explotación)

**Superficie:** IPC.

**Evidencia.**

- **Quién crea y quién conecta.** El servidor es el proceso hijo: `Pipe::Start` en
  `src\Common\IPC\pipe.cc:216-227` llama a `CreateNamedPipeA(..., lpSecurityAttributes = NULL)`.
  El XLL es el cliente: `src\Core\src\language_service.cc:408` (`CreateFileA` del pipe de datos) y
  `:228` (pipe de callback `-CB`).
- **DACL por defecto.** `lpSecurityAttributes = NULL` deja el descriptor por omisión de los named
  pipes de Windows: control total para el creador, SYSTEM y administradores, y **acceso de lectura
  para `Everyone` y la cuenta anónima**. Por ese pipe viaja el código a ejecutar y los datos de
  la hoja.
- **Sin `FILE_FLAG_FIRST_PIPE_INSTANCE`.** El servidor no puede detectar que el nombre ya existía.
- **Instancias limitadas.** `kMaxPipeCount = 4` (`src\Common\Constants.h:55`).
- **Nombre predecible.** `src\Core\src\language_service.cc:127-130`:
  `RJ2XCL2-PIPE-{R|J|P}-{PID de Excel}`; el descubrimiento desde Python confirma el patrón
  (`src\startup\neven_http_server.py` §`_discover_pipe`). `INV-CJ-03` lo fija como parte del
  protocolo.
- **Sin identificación del cliente ni del servidor.** No hay `GetNamedPipeClientProcessId` en el
  árbol, y el cliente abre con `CreateFileA` **sin** `SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION`,
  de modo que un servidor de pipe suplantador podría impersonar al usuario que conecta.
- **Validación del marco: correcta.** `src\Common\IPC\MessageValidator.cc:30-56` comprueba puntero
  nulo, mínimo de 4 bytes, que la longitud declarada no exceda el máximo
  (`kDefaultMaxMessageSize = 64 MiB`, `MessageValidator.h:37`) y que el búfer contenga esa
  longitud, **antes** de `ParseFromArray`. `INV-CMN-03` se cumple. `protobuf_ipc_pbt.cc` (6 tests)
  cubre la propiedad correcta.

**Vector y precondiciones.** Otro usuario local puede (a) abrir el pipe en lectura y leer los
mensajes, (b) ocupar instancias hasta agotar las 4 y provocar denegación de servicio, (c)
adelantarse creando el nombre —calculable a partir del PID de Excel— para que el XLL conecte con
él. Todo requiere ejecución local previa como otro usuario, y el canal no transporta credenciales.

**Severidad razonada: Media.** El contenido del canal (código y datos de la hoja) es sensible y
hoy es legible por cualquiera en la máquina, lo que es más de lo que
`Evaluacion_OWASP.md:82` concede ("el riesgo es bajo porque requiere acceso local con privilegios
elevados": **no** requiere privilegios elevados). Pero no es una vía de ejecución por sí misma.

**Invariantes.** `INV-CJ-03` fija nombre y protocolo: pasar un `SECURITY_ATTRIBUTES` con DACL
propia (solo el usuario actual) y `FILE_FLAG_FIRST_PIPE_INSTANCE` **no toca el nombre ni el
formato de los mensajes**, así que no la viola. `INV-CMN-03` se preserva. `INV-CR-02` (30 reintentos
× 100 ms) tampoco cambia.

### SEC-13 · `ValidateConfig()` valida las rutas y tira el resultado · **BAJA** · VERIFICADO

**Superficie:** configuración.

**Evidencia.** `src\Common\ConfigService.cc:78-105`: la lambda `validate_path` detecta `..` y los
caracteres `| & ; ` $ > <` y devuelve `false`; las seis llamadas (`:100-105`) **descartan el valor
de retorno**. El efecto es un `RJ2XCL_LOG_WARN` y seguir usando la ruta. Además la lista no
incluye la comilla doble, que es el carácter que importaría para la línea de comandos de Quarto
(`src\Common\QuartoService.cc:331`), donde la ruta del ejecutable se entrecomilla.

**Severidad razonada: Baja.** Para abusar de esto hay que poder escribir
`C:\NEVEN\neven-config.json`, y quien puede hacerlo ya tiene SEC-09 y SEC-08 a su disposición,
que son caminos más directos. Lo registro porque es un control que aparenta existir y no existe:
`SECURITY.md:30` lo acredita como mitigación de *path traversal*.

**Invariantes.** Ninguna.

### SEC-14 · `RequestSandboxDisable()` no tiene invocadores: la confirmación y el registro que acredita la evaluación OWASP no se ejecutan nunca · **BAJA** · VERIFICADO

**Superficie:** sandbox; configuración.

**Evidencia.** `src\Common\ConfigService.cc:111-155` implementa el diálogo de confirmación, el
cambio del flag en memoria y el registro con usuario de Windows y marca de tiempo.
`git grep RequestSandboxDisable -- src` devuelve **solo** la definición (`ConfigService.cc:111`) y
la declaración (`ConfigService.h:99`). Ningún llamador. Además el método **no persiste** el
cambio (no llama a ningún `Save`), así que incluso invocado solo afectaría a la sesión.

La vía real para desactivar el sandbox es editar `sandboxEnabled` en
`C:\NEVEN\neven-config.json` (escribible por cualquier usuario autenticado, SEC-09): sin diálogo,
sin registro y sin rastro, leído en `ConfigService.h:84-88` (por defecto `true`, lo cual es
correcto).

Y `src\docs\Evaluaciones\Evaluacion_OWASP.md:16` puntúa **A01 Broken Access Control con 9/10**
apoyándose, textualmente, en "confirmacion interactiva para deshabilitar".

**Severidad razonada: Baja** como defecto técnico (código muerto), **relevante** como defecto de
aseguramiento: una puntuación de seguridad publicada se sostiene sobre una función que no se
ejecuta.

**Invariantes.** Ninguna.

### SEC-15 · El puente `postMessage` del visor inyecta JSON por concatenación y vuelca el mensaje íntegro a una cola que consume NEVEN-SIM · **MEDIA** · VERIFICADO

**Superficie:** WebView2, puente JS↔C++.

**Evidencia.** `src\Common\PostMessageBridge.cc`:

- `:88-104` (`GetBridgeScript`) inyecta `window.neven` en **todo** documento cargado en el visor
  (`ViewerWindow.cc:218-225`, `AddScriptToExecuteOnDocumentCreated`), con los métodos
  `writeCell`, `notify` y `simCommand`.
- `:119-130` (`HandleWriteCell`): construye el JSON **concatenando** `sheet`, `cell` y `value`
  sin escapar, y lo escribe en `C:\NEVEN\data\bridge_queue.json`. Un `"` en cualquiera de los tres
  rompe la estructura y permite inyectar claves arbitrarias en el documento.
- `:73-82` (`sim-command`): escribe `json_message` **tal cual**, sin validar nada, en
  `C:\NEVEN\data\sim_command.json`.
- Consumidores: `src\NEVEN-SIM\src\bridge_poller.cc:30` y `src\NEVEN-SIM\src\sim_main.cc:619`.
- `:140-212` (`HandleSaveRequest`): la ruta de guardado viene de `GetSaveFileNameA`, es decir del
  usuario. Correcto.
- No hay `AddHostObjectToScript` en ningún punto del árbol: el puente es solo este canal de
  mensajes, lo que limita bien la superficie.

**Vector y precondiciones.** El emisor de los mensajes es el HTML renderizado en el visor, que lo
genera R/Julia y puede incorporar datos ajenos (igual que SEC-07). La consecuencia inmediata es
influir en lo que NEVEN-SIM y Excel leen de esas colas; el alcance exacto depende de cómo
`bridge_poller` interpreta el JSON, que no se auditó en este eje.

**Severidad razonada: Media.** Dos ficheros de ruta fija, sin travesía, en un directorio ya
abierto por SEC-09; lo que añade es un canal desde contenido renderizado hacia el estado de la
aplicación sin validación.

**Invariantes.** Ninguna. `INV-CP-03` (validación de origen en `postMessage`) **no cubre** este
puente porque aquí el canal es `window.chrome.webview.postMessage`, que no tiene origen que
comparar: la defensa tiene que ser validación del mensaje en C++.

### SEC-16 · El servidor de audiolibros escucha en toda la red local, sin autenticación, con endpoints de subida y de generación · **ALTA** · VERIFICADO

**Superficie:** servidor HTTP del módulo Audiobook (puerto 5556).

**Evidencia.** `src\Audiobook\neven_audiobook_server.py`:

- `:376-382`: `app.run(host='0.0.0.0', port=args.port, debug=args.debug, threaded=True, ...)`.
  Bind a **todas** las interfaces, no a `127.0.0.1`.
- `:38-45`: `CORS(app, resources={r"/api/*": {"origins": ["*"], ...}})`.
- Cero autenticación en todo el fichero y en `src\Audiobook\api\routes.py` (60 KB, ~60 rutas):
  `/api/upload` (`:243`), `/api/generate` (`:288`), `/api/extract` (`:412`),
  `/api/markdown/<filename>` GET y PUT (`:486`, `:504`), `/api/markdown/upload` (`:524`),
  `/api/books/<filename>/download` (`:1123`), `/api/serve` (`:1273`),
  `/api/translate/*`, `/api/translate/deepl/configure` (`:1221`).
- La exposición es **deliberada**: `/api/qr` (`:131`) y `/download` (`:164`) existen para que la
  app Android descargue el audiolibro por la red local, y `get_local_ip()` (`:296`) se conecta a
  `8.8.8.8` para averiguar la IP a publicar en el QR.

**Lo que está bien hecho** (y conviene no romper al arreglar lo anterior): los nombres de fichero
derivados del contenido del libro se filtran con lista blanca de caracteres
(`routes.py:455-458` y `:1012-1014`: `"".join(c for c in base_name if c.isalnum() or c in ' -_')`),
los *endpoints* de markdown usan `secure_filename` (`:489`, `:512`, `:540`, `:1128`), y **ninguna
invocación de ffmpeg o de TTS usa shell**: siempre lista de argumentos
(`src\Audiobook\muxer\ffmpeg_muxer.py:185-239`, `src\Audiobook\tts\windows_tts.py:236-245`), con
escape de comillas en el fichero de lista de concatenación (`windows_tts.py:230-232`). La página
`/download` usa parámetros Jinja2 (`{{ filename }}`), no interpolación de la plantilla: **no hay
SSTI ni XSS** por ahí.

**Vector y precondiciones.** Cualquier dispositivo de la misma red (wifi de cafetería, red de
universidad) puede listar y descargar los audiolibros, subir PDFs, lanzar conversiones que
consumen CPU durante horas, escribir markdown en `output_folder` y configurar la clave de DeepL.
Requisito: que el servidor esté arrancado (se arranca a demanda desde el TaskPane,
`/api/audiobook/start`, `src\startup\neven_http_server.py:2314`).

**Severidad razonada: Alta** por alcance (red local, sin autenticación, con escritura) y
**no crítica** porque no se encontró una vía directa a ejecución de código: sin shell en ffmpeg y
con los nombres filtrados, lo que queda es lectura, escritura acotada al directorio de salida y
consumo de recursos. El agravante es que la exposición de red **no está documentada en
`SECURITY.md`**, que ni menciona este servidor.

**Invariantes.** Ninguna de las 62 cubre el módulo Audiobook, ni su puerto, ni su bind. Nota
colateral: **`INV-AS-03` reserva el 5556 para AgentService** y este servidor usa el mismo 5556
(`:29` `DEFAULT_PORT = 5556`), igual que el `fallbackPort` del servidor Studio. Tres servicios
distintos pelean por un puerto; es un conflicto de diseño documentado aquí porque determina
quién acaba escuchando.

### SEC-17 · El arreglo del commit `9eba8b1`: la travesía queda bloqueada, pero introduce doble decodificación, prefijo sin separador y un *fallback* que entrega cualquier fichero del directorio · **MEDIA** · VERIFICADO (el código) / **NO VERIFICADO** funcionalmente

**Superficie:** endpoint de descarga de audiolibros (asignación explícita de la tarea).

**Estado del despliegue (medido).** El arreglo **está en producción**, byte a byte:

| Fichero | Repo (SHA-256, 12) | Producción | Veredicto |
|---|---|---|---|
| `neven_audiobook_server.py` | `2209DC188A3B` | `C:\NEVEN\Audiobook\` igual | sincronizado |
| `audiobook.js` | `39382D4C75C5` | `C:\NEVEN\taskpane\` igual | sincronizado |
| `api\routes.py` | `25BDFE4EF97A` | `C:\NEVEN\Audiobook\` igual | sincronizado |

**Evidencia del código resultante** (`src\Audiobook\neven_audiobook_server.py:91-124`):

```
decoded_filename = unquote(filename)
file_path = os.path.normpath(os.path.join(output_folder, decoded_filename))
if not file_path.startswith(os.path.normpath(output_folder)):
    return jsonify({'error': 'Acceso no permitido'}), 403
if not os.path.exists(file_path):
    base_name = os.path.splitext(decoded_filename)[0]
    matches = [f for f in os.listdir(output_folder) if f.startswith(base_name)]
    ...
```

**Veredicto por vector:**

| Vector | Veredicto | Razón |
|---|---|---|
| **Path traversal** | **DESCARTADO** | `normpath` resuelve los `..` y la comprobación de prefijo rechaza con 403 antes de abrir. Aguanta también los `..` doblemente codificados, porque la comprobación es posterior a `unquote` |
| **Doble decodificación** | **CONFIRMADO como defecto latente** | Flask ya decodifica el segmento de ruta; `unquote()` lo decodifica otra vez. Hoy no es explotable porque los nombres que el *pipeline* genera no pueden contener `%` (la lista blanca de `routes.py:457` lo excluye), pero cualquier fichero colocado en `output_folder` por otra vía con un `%` en el nombre cambia eso |
| **Prefijo sin separador** | **CONFIRMADO (bajo)** | `startswith(output_folder)` sin exigir separador: un directorio hermano cuyo nombre empiece por el mismo prefijo (`...\output_algo\`) pasa la comprobación. Se arregla con `os.path.commonpath` |
| **Comparación sensible a mayúsculas** | **sin impacto** | En Windows las rutas no distinguen mayúsculas pero `startswith` sí: el efecto es denegar de más, nunca de menos |
| **Fallback por coincidencia de prefijo** | **CONFIRMADO (es la regresión real)** | Si el nombre exacto no existe, lista el directorio y sirve `matches[0]`, el **primer** fichero cuyo nombre empiece por el prefijo pedido. Con un prefijo de un carácter se obtiene un fichero cualquiera del directorio, sin conocer su nombre; se sirve con `mimetype='audio/mp4'` aunque sea un `*_draft.md`. Convierte el endpoint en enumerable y no determinista. Y al venir de `os.listdir`, elude la propia comprobación de contención (no la rompe: el fichero está dentro, pero no es el pedido) |
| **Inyección de cabecera por `download_name`** | **DESCARTADO con reserva** | `send_file(download_name=decoded_filename)` pasa por `Response.headers`, que en werkzeug rechaza valores con salto de línea. No se inventarió la versión instalada de werkzeug: reserva declarada |
| **`href` sin codificar en `/download`** | **CONFIRMADO (funcional, no seguridad)** | `:273` genera `<a href="/api/download/{{ filename }}">`: el valor se escapa como HTML pero **no** se codifica como URL. Para espacios el navegador lo arregla; para `#` no. Es el mismo problema que el commit intentaba resolver, en el otro extremo |

**Lo que probablemente siga roto (HIPÓTESIS, verificable en 1 minuto).**
`src\TaskPane\audiobook.js:118` llama a `fetch('http://localhost:5555/api/audiobook/start')`, en
**http**; en producción el 5555 sirve **https** (hay `certPath`/`keyPath` en
`C:\NEVEN\neven-config.json` y los dos ficheros existen). Recuento de esquemas en el TaskPane:
`taskpane.html` 3 URLs `http://localhost:5555` y 2 `https://localhost:5555`; `taskpane.js` 1
`http`; `audiobook.js` 1 `http`. Si la página se sirve por https, esas peticiones son contenido
mixto y el navegador las bloquea. Encaja exactamente con el síntoma que el commit intentó
diagnosticar añadiendo `console.warn`/`console.error`. **Esto hay que comprobarlo antes de tocar
nada más del módulo.**

**Severidad razonada: Media.** El endpoint vive en el servidor expuesto a la red local (SEC-16),
así que la entrega indiscriminada de ficheros del directorio de salida la puede pedir cualquiera
en la red. Sin SEC-16 sería Baja.

**Invariantes.** Ninguna.

### SEC-18 · El historial de git conserva el endpoint del recurso Azure retirado; `INV-INS-01` se cumple en HEAD · **BAJA** · VERIFICADO

**Superficie:** secretos en el repositorio.

**Evidencia** (sin transcribir ningún valor):

- `git log --all --diff-filter=A` sobre patrones de credencial devuelve **un** fichero:
  `Install/neven-config.json` (ruta del layout anterior).
- Commits implicados: `1cd442e` y `d66cda5` lo añaden/modifican; **`de8d44b` — "security: remover
  credenciales Azure del repo"** (2026-09-06) lo renombra a `neven-config.template.json`,
  sustituye el endpoint y retira la excepción del `.gitignore`.
- Inspección medida de los blobs históricos: el campo `apiKey` contenía un **marcador de 28
  caracteres** (clasificado PLACEHOLDER), **no** una clave real. El campo `endpoint` contenía un
  valor de 55 caracteres clasificado como real, es decir el nombre del recurso Azure OpenAI
  concreto, que **sigue siendo recuperable del historial**.
- El fichero histórico tenía BOM (`\xEF\xBB\xBF`), lo que en su día contravenía `INV-INS-04`; hoy
  el template no lo tiene.
- En HEAD solo está versionado `src\Install\neven-config.template.json`; `src\Install\neven-config.json`
  existe en disco e **está ignorado** (`src\.gitignore:87`). No hay `.pfx`, `.key`, `.pem`,
  `.jks` ni `keystore` versionados, ni en HEAD ni añadidos en el historial.
- Barridos de patrones de clave (`sk-…`, `AIza…`, `ghp_…`, `xox…`, `PRIVATE KEY`) sobre ficheros
  versionados: **sin coincidencias reales**; las apariciones de `apiKey` son documentación,
  especificaciones y ontología.
- El repositorio tiene remoto en `github.com` (nombre no transcrito).

**Lo que sí es un secreto hoy en el árbol:** la contraseña literal de exportación del PFX en
`src\TaskPane\Generate-Cert.ps1` (líneas 43, 55 y 56) y el bloque equivalente de
`src\Install\Install-NEVEN.ps1` (~1090-1100). Ver SEC-10. Ubicación y naturaleza reportadas; valor
no transcrito.

**Severidad razonada: Baja.** No hay clave filtrada; lo filtrado es el identificador de un recurso
de la organización, útil solo para dirigir un ataque contra ese recurso. Acción: si ese recurso
Azure sigue vivo, conviene rotar la clave asociada por precaución y decidir si el historial se
reescribe (coste alto, beneficio bajo) o se acepta documentándolo.

**Invariantes.** `INV-INS-01`: **CUMPLE** en HEAD. La invariante dice "nunca commitear
`neven-config.json` con credenciales reales" y así es hoy; el historial es anterior a ella.

### SEC-19 · WebView2: lista blanca de navegación correcta, sin host objects, pero sin CSP, sin filtro de subrecursos y con `file:///` sin acotar · **MEDIA-BAJA** · VERIFICADO

**Superficie:** visor WebView2.

**Evidencia.** `src\Common\ViewerWindow.cc`:

- `:552-570` (`ApplySecurityPolicy`): `AreDevToolsEnabled` configurable,
  `AreDefaultContextMenusEnabled(FALSE)`, `IsStatusBarEnabled(FALSE)`,
  **`IsScriptEnabled(TRUE)`** (necesario para Plotly/D3), `IsBuiltInErrorPageEnabled(FALSE)`.
- `:572-626` (`SetupNavigationFilter`): lista blanca en `add_NavigationStarting` —
  `about:blank`, `data:`, `blob:`, **cualquier** `file:///`, cinco CDN
  (`cdn.jsdelivr.net`, `cdnjs.cloudflare.com`, `fonts.googleapis.com`, `fonts.gstatic.com`,
  `unpkg.com`) y `localhost:{pluto_port}` solo en modo avanzado; todo lo demás `put_Cancel(TRUE)`
  con registro. **El diseño del filtro está bien**.
- Cero `AddHostObjectToScript` en todo el árbol: no se exponen objetos nativos al JS.
- `:261-275` `NavigateToString` del HTML que produce R/Julia; `:277-295` `NavigateToFile`.

**Lo que falta:**

1. `add_NavigationStarting` gobierna **navegaciones**, no subrecursos: `fetch`, `XHR`, `<img>` y
   `<script>` no pasan por ese filtro. No hay `add_WebResourceRequested` ni CSP inyectada, así que
   el HTML renderizado puede enviar datos a cualquier destino de internet.
2. `file:///` se permite sin acotar a `C:\NEVEN\workspace` o al directorio de gráficos.
3. No se usa `add_FrameNavigationStarting`, de modo que un `<iframe>` dentro del contenido no
   hereda la comprobación.

**Severidad razonada: Media-Baja.** Quien controla el HTML del visor normalmente es el código R
del propio usuario, que ya puede hacer red por su cuenta. Sube a Media cuando el HTML incorpora
datos ajenos (mismo supuesto que SEC-07) y por su conexión con el puente de SEC-15.

**Invariantes.** Ninguna. Inyectar una CSP por `AddScriptToExecuteOnDocumentCreated` o por
`add_WebResourceRequested` no toca ninguna de las 62.

### SEC-20 · Quarto: la construcción de la línea de comandos es correcta · **control efectivo, DESCARTADO como problema** · VERIFICADO

**Superficie:** Quarto por `CreateProcess`.

**Evidencia.** `src\Common\QuartoService.cc`:

- `:476-517` (`Render`) valida **antes** de cualquier otra cosa: `ValidateInputSecurity(file_path)`
  (`:486`), `ValidateInputSecurity(format)` (`:494`), `ValidateExtension(resolved)` → debe ser
  `.qmd` (`:510`), `ValidateFormat` → lista blanca `html|pdf|docx` (`:517`).
- `:36-63` (`ValidateInputSecurity`): rechaza `..` y los caracteres
  `| & ; ` < > " \n \r %`, y además delega en `InputSanitizer::ValidateArgument`, que es una
  **lista blanca** de caracteres (`src\Common\Security\InputSanitizer.cc:31-42`).
- `:331`: `cmd = "\"" + quarto_path_ + "\" render \"" + resolved_path + "\" --to " + format;`
  — ejecutable y ruta entrecomillados; `format` ya viene de una lista blanca de tres valores.
- `:402-413`: `CreateProcessA(NULL, cmd_buf.data(), ..., CREATE_NO_WINDOW, NULL, working_dir, ...)`.
  Sin shell, con `working_dir` derivado de la propia ruta.
- Las variables de entorno que se pasan al hijo se limpian después (`:415-419`).

**Residuales declarados:** (a) el `.qmd` ejecuta R/Python por diseño —es el propósito—;
(b) `quarto_path_` puede venir de la configuración, cuya validación se descarta (SEC-13), y la
lista de caracteres bloqueados de `ConfigService` **no** incluye la comilla doble, que es la que
rompería el entrecomillado; (c) `InputSanitizer::BuildSafeCommandLine` existe
(`InputSanitizer.cc:117-152`) y **no se usa** en el único sitio que la necesitaría:
`LanguageService::StartChildProcess` construye la línea a mano con `pipe_name_` **sin
entrecomillar** (`src\Core\src\language_service.cc:789`). Hoy `pipe_name_` es
`RJ2XCL2-PIPE-X-{PID}` y es inofensivo; es sustituible por un valor del registro solo con
`dev_flags_` activo (`:121-124`, `HKEY_CURRENT_USER` por `DEFAULT_BASE_KEY` de
`windows_api_functions.h:28`). Riesgo real: muy bajo; higiene: mala.

**Severidad razonada: Informativa.** Lo dejo escrito como control que **sí** funciona, para que no
se "arregle" por inercia y para que el patrón se copie en los sitios que no lo aplican.

### SEC-21 · Prompt injection: no hay ejecución automática de lo que propone el modelo, pero tampoco marcado de procedencia · **MEDIA-BAJA** · VERIFICADO (lo buscado) / NO VERIFICABLE (el comportamiento del modelo)

**Superficie:** RAG y agente IA.

**Qué se buscó y qué se encontró.** En `src\startup\neven_http_server.py` no existe ningún
mecanismo de *tool calling* que ejecute acciones decididas por el modelo: `git grep` de
`tool_call|function_call|auto_apply|apply_action` devuelve solo la rama de despacho HTTP
(`:1141 self._handle_function_create(body)`) y texto de documentación. `/api/functions/create`
es un endpoint independiente que invoca la interfaz tras la aprobación del usuario, y además está
bien validado (`:2669-2676`, ver SEC-03). El agente **no** escribe ficheros por su cuenta.

**Dónde queda el riesgo.** (a) El contenido del RAG —PDFs de libros, hojas del libro de
Excel— entra en el prompt sin marca de procedencia ni delimitador, de modo que un documento
hostil puede influir en lo que el agente recomienda al usuario; el daño se materializa si el
usuario acepta la recomendación. (b) El eslabón débil **no es el modelo**: es que
`/api/functions/create` y `/api/save_script` no exigen autenticación (SEC-01, SEC-03), así que no
hace falta convencer al agente de nada.

**Severidad razonada: Media-Baja.** Sin ejecución automática, la inyección de prompt degrada la
calidad del consejo, no la integridad del sistema. Subiría a Alta el día que se añada
*tool calling* real; conviene fijar ahora la regla (ver IDEA-S04).

**Invariantes.** `INV-SB-05` e `INV-AS-02` (contexto pendiente consumible) reducen la ventana de
reutilización del contexto; no se tocan. Nota sobre los skills de *runtime*
(`.agents\skills\*` con `restricted_to_rag: true`): el plan preguntaba si ese flag es una defensa
real contra prompt injection. **No lo es**: es una restricción de las fuentes que el agente debe
citar, aplicada en el prompt, no un control técnico que impida al modelo razonar sobre contenido
inyectado. Declararlo como defensa sería un error de modelo de amenazas.

### SEC-22 · La documentación de seguridad describe un sistema que no es el que hay · **MEDIA** (informativa, de aseguramiento) · VERIFICADO

**Superficie:** `SECURITY.md`, evaluación OWASP.

**Evidencia.**

| Afirmación | Dónde | Realidad medida |
|---|---|---|
| "357 tests automatizados"; "Sandbox (R + Julia + Python) 154" | `src\SECURITY.md:181-190` | 369 tests / 47 suites en el binario; `SandboxTest` = **133**, y sumando `NewFunctionsSandboxTest` (16), `SandboxBlocklistPBT` (4), `SandboxPathPBT` (2) y `PythonSandboxPBT` (3) = 158. Ninguna de las dos cifras publicadas coincide |
| "La auditoria de mayo 2026 identifico 36 hallazgos de seguridad. **Todos fueron remediados**" | `src\SECURITY.md:192` | `.kiro\specs\security-remediation\tasks.md`: 72/72 tareas marcadas, 0 pendientes. Pero el informe previo no tiene IDs estables, así que la afirmación no es verificable hallazgo a hallazgo (igual que concluyó el eje 2) |
| A01 Broken Access Control **9/10**, por "confirmacion interactiva para deshabilitar" | `src\docs\Evaluaciones\Evaluacion_OWASP.md:16` | La función de confirmación **no tiene invocadores** (SEC-14) y no hay control de acceso en el API local (SEC-01) |
| A07 "NEVEN no tiene sistema de autenticacion propio" tratado como **8/10** | `Evaluacion_OWASP.md:214-224` | Hay tres servidores HTTP (5555, 5556 AgentService, 5556 Audiobook), uno de ellos en `0.0.0.0`, todos sin autenticación. La evaluación no los menciona |
| "Para Named Pipes: el riesgo es bajo porque requiere acceso local **con privilegios elevados**" | `Evaluacion_OWASP.md:82` | La DACL por defecto da lectura a `Everyone`: no requiere elevación (SEC-12) |
| "`/GS /guard:cf /sdl /DYNAMICBASE /NXCOMPAT /CETCOMPAT`" como flags del código C++ | `src\SECURITY.md:160-168` | `/sdl` no está en `src\CMakeLists.txt`; `/guard:cf` no llegó al binario principal (SEC-11) |
| `SECURITY.md` no menciona ni una vez los puertos 5555/5556, el TaskPane, el servidor de audiolibros ni el visor WebView2 | — | Son hoy la mayor superficie de ataque del proyecto |

**Severidad razonada: Media.** No es una vulnerabilidad; es la razón por la que las
vulnerabilidades de este informe llevaban meses en pie. El modelo de amenazas documentado se
quedó en la versión en la que NEVEN era un XLL con dos procesos hijo, y no se actualizó cuando
aparecieron tres servidores HTTP y un TaskPane de 30 000 líneas de JavaScript.

**Invariantes.** Ninguna.

### SEC-23 · El sandbox aplica las tres listas a todo el código, con excepciones de contexto triviales: es un guardarraíl, no una frontera · **MEDIA** · VERIFICADO

**Superficie:** sandbox (`SandboxVerifier`).

**Evidencia.** `src\Common\Security\SandboxVerifier.cc`:

- **Las tres listas se evalúan sobre cualquier entrada**, sin saber el lenguaje: R (`:269-277`),
  Julia (`:306-313`) y Python (`:316-323`) se comprueban en secuencia para el mismo `code`. El
  parámetro de lenguaje no existe; `ExecutionSource` solo se usa para el registro (`:445-459`).
  Consecuencia directa: código **R** legítimo que contenga `eval(`, un acento grave, `open(` o
  el token `ENV` se rechaza por reglas de Julia; código Python con `open(` se rechaza aunque
  `open()` sea la forma normal de leer un fichero. Es un generador de falsos positivos, y explica
  por qué la ruta del TaskPane se construyó sin sandbox (SEC-02).
- **La coincidencia es por subcadena literal** (`lower_code.find("system(")`), sobre el texto y
  sobre una copia sin espacios (`StripWhitespace`, `:49-59`). Bloquea bien la forma directa y los
  trucos de espaciado; no puede cubrir la búsqueda indirecta de símbolos a través de funciones que
  no estén en la lista, porque la cadena prohibida nunca aparece. No doy carga útil: el mecanismo
  es que la lista enumera nombres y el lenguaje permite obtener funciones por nombre con APIs que
  la lista no agota. `src\SECURITY.md:54` y el encabezado del propio fichero (`:19-23`,
  "pattern-based blocking can be bypassed... is NOT a full sandbox") ya lo admiten.
- **Las excepciones de contexto son satisfacibles con un comentario.** `source()` se permite si
  **en cualquier parte** del fragmento aparece una subcadena tipo `/neven/`, `c:\neven\`,
  `appdata` + `neven`, etc. (`:214-233`) — no se extrae ni se valida el argumento real de
  `source()`. `library()` se permite si en cualquier parte aparece `.neven`, `neven_`, `# neven`,
  `r4xcl`, `nevenx`, `.graphics_dir` o `chart gallery` (`:240-262`). Es decir, un comentario
  `# neven` habilita `library()` arbitraria, y mencionar una ruta de NEVEN habilita `source()` de
  cualquier fichero.
- **Heurísticas de amplio espectro** que refuerzan lo anterior como guardarraíl pero elevan los
  falsos positivos: `paste` + (`sys`|`shell`|`unlink`) (`:378-385`), `assign(` + `envir`
  (`:388-392`), `getattr(` + (`os`|`subprocess`|`shutil`) (`:420-426`).

**Severidad razonada: Media.** Como protección frente a libros de Excel maliciosos **de serie** y
frente a accidentes, funciona y tiene 158 tests detrás. Como frontera de seguridad no lo es, y el
problema no es que sea evitable —eso está documentado— sino que (a) la excepción de contexto es
decorativa y (b) su coste en falsos positivos empujó a construir la segunda puerta sin control
(SEC-02).

**Invariantes.** Ninguna de las 62 describe el sandbox: **otro hueco de la ontología** para un
componente que `SECURITY.md` presenta como el control principal.

### SEC-24 · 247 tests de seguridad en C++ y cero sobre la superficie HTTP · **MEDIA** · VERIFICADO

**Superficie:** aseguramiento.

**Evidencia.** Recuento con `--gtest_list_tests` sobre
`src\Build\tests\Release\rj2xcl_tests.exe` (sin recompilar):

| Suite | Tests |
|---|---:|
| `SandboxTest` | 133 |
| `ErrorMessageTest` | 16 |
| `InputSanitizerTests` | 16 |
| `NewFunctionsSandboxTest` | 16 |
| `RepoHygieneTests` | 14 |
| `PipeLifecycleTests` | 8 |
| `ProtobufIpcPBT` | 6 |
| `InputSanitizerPBT` | 5 |
| `BuildVerificationTests`, `ConfigPathValidation`, `SandboxBlocklistPBT`, `SecurityServiceTest` | 4 cada una |
| `PythonSandboxPBT` | 3 |
| `SandboxPathPBT`, y 4 suites `PythonReactivation*` | 2-4 |
| **Total relacionado con seguridad** | **247** |

Y **cero** tests —ni C++ ni pytest— sobre: CORS/autenticación del servidor 5555, recorrido de
rutas en el servido estático, contención de `/api/save_script`, validación de `/api/groupby`,
política de `sandbox` de los `srcdoc`, o bind del servidor de audiolibros. Los 18 ficheros
`test_*.py` de `src\TaskPane\tests` no están en CI (eje 2, COD-22) y no cubren seguridad.

El esfuerzo de prueba está concentrado en el componente que **no** es frontera (el blocklist) y
ausente en los que sí lo son.

**Severidad razonada: Media.** Es la causa estructural de que SEC-01, SEC-03 y SEC-04 pasaran
desapercibidos.

**Invariantes.** `INV-TEST-03` (los tests no requieren Excel, R, Julia ni Python) condiciona la
forma: los tests del servidor HTTP deben arrancarlo con un `pipe_client_factory` simulado —el
propio servidor ya lo soporta (`start_server(config)` con `pipe_client_factory`,
`src\startup\neven_http_server.py:4780-4800`)—, no con motores reales. La invariante se respeta.

---

## 3. Estado de la auditoría de seguridad previa

**Limitación declarada, igual que en el eje 2:** `src\docs\audit\hallazgos_seguridad.md` (191 KB,
151 secciones, IDs `FOR-CMD-*`, `FOR-CRE-*`, `FOR-MEM-*`, `FOR-PB-*`, `FOR-PIPE-*`, `FOR-SBX-*`,
`FOR-PY-*`, `FOR-JUL-*`, `FOR-SCR-*`, `FOR-STR-*`, `FOR-DEP-*`, `FOR-ENV-*`) es un **inventario
forense sin campo de estado**: muchas entradas son observaciones de que algo está bien hecho, no
defectos. No existe un listado canónico de "los 36 hallazgos" con identificador, de modo que el
emparejamiento uno a uno es imposible sin reconstruirlo. Lo que sí se puede dictaminar:

| Asunto previo | Estado hoy | Evidencia |
|---|---|---|
| Spec `security-remediation` | **CERRADA formalmente** | `.kiro\specs\security-remediation\tasks.md`: 72 tareas marcadas, 0 pendientes |
| `CM-BAJ-004` / `CM-BAJ-014` — `AddTrustedSignature`, `EvaluateScript`, `m_trusted_signatures` sin uso | **RESUELTO** | eliminados con nota en `src\Common\Security\SandboxVerifier.cc:40,43` y `src\Include\SandboxVerifier.h:48,78,90` |
| `FOR-PIPE-001/005` — validación del handle tras `CreateNamedPipeA` | **RESUELTO** | `src\Common\IPC\pipe.cc:229-232` comprueba `NULL` e `INVALID_HANDLE_VALUE`; `SafePipeHandle` da RAII |
| `FOR-PB-*` — desbordamiento por mensajes Protobuf malformados | **RESUELTO** | `MessageValidator::ValidateFrame/SafeUnframe` + 6 tests `ProtobufIpcPBT` |
| `C-02` — código de celda sin validar | **RESUELTO** | `src\Core\src\basic_functions.cc:157-166` (marcado como "C-02 FIX" en el propio código) |
| `C-06` — `parse_error` de JSON ignorado | **RESUELTO** | `src\Common\ConfigService.cc:57-62` (marcado "RESOLVED: C-06") |
| `S-06` — fugas de handles BCrypt | **RESUELTO** | `src\Common\Security\SecurityService.cc:21-27` con deleters RAII |
| `H-04` — corrupción por recálculo paralelo | **RESUELTO** | `thread_local XLOPER12 rslt` en `basic_functions.cc:135` y `:193` |
| Integridad de scripts (el control que la remediación introdujo) | **ABIERTO en producción** | SEC-08: 0 ficheros `.sha256` desplegados, verificación *fail-open* |
| Deshabilitación del sandbox con confirmación y registro | **ABIERTO** | SEC-14: la función existe y nadie la llama |
| Superficie HTTP local (5555/5556/audiobook) | **NUNCA AUDITADA** | No aparece en `hallazgos_seguridad.md` ni en `Evaluacion_OWASP.md`: es territorio nuevo y es donde están los hallazgos críticos de este informe |

**Patrón digno de imitación** (el eje 2 llegó a la misma conclusión): los hallazgos que hoy se
pueden declarar resueltos son exactamente los que dejaron **un comentario con el ID en el punto
del código** (`// C-02 FIX`, `// RESOLVED: C-06`, `// CM-BAJ-004 ... v2.3`). Los demás no son
verificables. Debería ser norma.

---

## 4. Veredicto sobre las invariantes `INV-*` que toca este eje

Solo las que caen en seguridad y se pudieron verificar con evidencia. Las demás quedan
explícitamente sin veredicto en lugar de inventarlo (el eje 2 dictaminó las de código).

| Invariante | Veredicto | Evidencia |
|---|---|---|
| `INV-CMN-02` (integridad de scripts) | **VIOLADA en producción** | SEC-08: 0 `.sha256` para 92 scripts; verificación *fail-open* (`SecurityService.cc:34-40`); es SHA-256, no HMAC |
| `INV-CMN-03` (buffer de pipe y reensamblado) | **CUMPLE** | `kPipeBufferSize = 8 KiB` (`Constants.h:48`); `SafeUnframe` acota la longitud declarada antes de deserializar |
| `INV-CJ-03` (pipe OVERLAPPED, marco de 4 bytes + Protobuf, nombre `RJ2XCL2-PIPE-J-{PID}`) | **CUMPLE** | `pipe.cc:216-227`, `language_service.cc:127-130`. Nota: el cumplimiento del nombre es también lo que lo hace predecible (SEC-12) |
| `INV-SB-01` (mutex `Global\NEVEN_Studio_Launcher`) | **NO VERIFICADO** | No se auditó `start_studio.py` en este eje más allá de la construcción de `server_config` |
| `INV-SB-02` (escritura UTF-8 sin BOM, `newline='\n'`) | **CUMPLE** | `_handle_save_script` (`:2805`) y `_handle_function_create` (`:2691`). Ironía: es lo que hace ejecutable el fichero que SEC-03 permite escribir |
| `INV-SB-03` (`/api/query` solo SELECT/WITH/SHOW/DESCRIBE) | **CUMPLE y es insuficiente** | `execute_query` (`:523-533`) valida por prefijo; SEC-05 y SEC-06 la esquivan por otras vías |
| `INV-SB-04` (token bucket 300/60 s → 429) | **CUMPLE** | `:646-649` (GET) y `:1076-1079` (POST). Es el **único** control de abuso del servidor |
| `INV-SB-05` (`/api/ai/context/pending` consumible) | **CUMPLE** | `:863-874` borra la señal al leerla |
| `INV-AS-02` (contexto pendiente consumible en AgentService) | **NO VERIFICADO** | No se auditó el ciclo de vida del contexto |
| `INV-AS-03` (AgentService en 5556) | **CUMPLE con conflicto** | `src\AgentService\neven_ai_service.py:1207-1209`: `--port` por defecto 5556, `--host` por defecto `127.0.0.1` (bien). Pero el servidor de audiolibros usa **también** 5556 (`neven_audiobook_server.py:29`) y el Studio lo usa como `fallbackPort` → SEC-16 |
| `INV-CP-03` (validación de origen en `postMessage`) | **CUMPLE donde aplica** | `src\CreadorPresentaciones\script.js:1471` y `src\TaskPane\taskpane.html:2648` comparan con `window.location.origin`; los envíos usan `window.location.origin` como destino (`taskpane.html:2680,2685,4367`, `datalab.js:2001`). **No cubre** el puente del visor, que no es `window.postMessage` (SEC-15) |
| `INV-BLD-01` (`/MT`) | **CUMPLE** | `src\CMakeLists.txt:8` (ya verificado en el eje 2) |
| `INV-BLD-02` (`/GS /guard:cf /DYNAMICBASE /NXCOMPAT /CETCOMPAT` en **todos** los binarios) | **VIOLADA en el artefacto** | SEC-11: `NEVEN64.xll` sin `GUARD_CF` en repo y en producción; el resto de binarios sí. `CETCOMPAT` no verificado por este método |
| `INV-TEST-01` (el test comprueba los cinco flags del CMakeLists) | **CUMPLE y es insuficiente** | Lee el `CMakeLists.txt`, no el PE: pasa mientras `INV-BLD-02` está incumplida |
| `INV-TEST-03` (tests sin Excel/R/Julia/Python) | **CUMPLE** y condiciona los tests nuevos | El servidor acepta `pipe_client_factory` inyectable, así que los tests de API pueden cumplirla |
| `INV-INS-01` (nunca commitear `neven-config.json` con credenciales) | **CUMPLE** en HEAD | SEC-18: solo el template está versionado; el historial conserva un endpoint, no una clave |
| `INV-INS-04` (JSON desplegado en UTF-8 sin BOM) | **CUMPLE** (muestra) | `C:\NEVEN\neven-config.json` sin BOM; el blob histórico sí lo tenía |
| `INV-TF-01` (un solo renderizador) | **PARCIAL → con coste de seguridad** | SEC-07: tres rutas de `srcdoc` con tres políticas distintas |

### ¿Alguna invariante debería cambiar?

**No propongo violar ninguna.** Tres observaciones explícitas:

1. **`INV-SB-03` debería ampliarse, no sustituirse.** Hoy dice "solo SELECT/WITH/SHOW/DESCRIBE".
   Es verdad y es insuficiente: SEC-05 muestra que un `SELECT` de DuckDB alcanza el sistema de
   ficheros. **Propuesta de cambio de ontología:** añadir al texto de
   `neven-ontology-p2.yaml:283` la exigencia de una lista blanca de funciones de tabla y la
   prohibición de interpolar identificadores sin validar. Primero la ontología, después el código.
2. **`INV-BLD-02` no hay que tocarla: hay que hacerla cierta.** La invariante es correcta; el
   producto no la cumple. Y **`INV-TEST-01` debería verificarse sobre el PE**, no sobre el
   `CMakeLists.txt`; eso es un refuerzo del texto actual, no una contradicción.
3. **Dos huecos, no dos violaciones.** Ninguna invariante cubre (a) las ACL del directorio de
   producción ni (b) el sandbox, que es el control que `SECURITY.md` presenta como principal.
   Proponer nuevas invariantes es añadir, no contradecir; va en IDEA-S02.

---

## 5. Procedimiento de verificación del arreglo `9eba8b1`

Pendiente **A** del plan (`plan-auditoria.md` §4): el arreglo está en el código y en producción
(hashes idénticos, SEC-17) y **nunca se ejecutó**. No es verificable en este entorno (hace falta
Excel, el servidor TTS y un libro convertido). Procedimiento reproducible para que lo ejecute el
usuario, en este orden:

**Paso 0 — Determinar el esquema del 5555 (es lo que probablemente falla).**
En el navegador del TaskPane, abrir la consola y mirar de qué URL se sirvió `taskpane.html`
(`document.location.protocol`). Si es `https:`, las llamadas `http://localhost:5555` de
`audiobook.js:118` y de `taskpane.html` están bloqueadas por contenido mixto y **el botón de
iniciar el servidor no puede funcionar** (SEC-17, hipótesis). Síntoma esperado en consola:
`[Audiobook] No se pudo iniciar via servidor principal`. Si se confirma, arreglar los esquemas
(o pasar a URLs relativas) **antes** de seguir.

**Paso 1 — Arrancar el servidor de audiolibros a mano**, sin depender del botón:
`python C:\NEVEN\Audiobook\neven_audiobook_server.py` y comprobar
`http://localhost:5556/api/health` → `{"status":"ok"}`.

**Paso 2 — Fichero de prueba con el peor nombre legal.** Generar (o copiar a
`C:\NEVEN\Audiobook\output\`) un `.m4a`/`.m4b` llamado exactamente:
`Miguel de Cervantes - Don Quijote de la Mancha á é í.m4b`
Espacios, guión y acentos: es lo que el *pipeline* puede producir, porque su lista blanca
(`routes.py:457`) acepta alfanuméricos Unicode, espacio, `-` y `_`.

**Paso 3 — Descarga por el TaskPane.** Pestaña de audiolibros → descargar ese fichero.
**Resultado esperado:** descarga con el nombre completo intacto, sin 404 y sin 403.
Si da 404, comparar lo que el cliente codifica (`encodeURIComponent` en `audiobook.js:357`, `:392`,
`:604`) con lo que el servidor decodifica dos veces (`neven_audiobook_server.py:101`).

**Paso 4 — Comprobar que el *fallback* no está enmascarando el fallo.** Pedir
`/api/download/Miguel` (prefijo corto, fichero inexistente). **Comportamiento actual esperado:**
devuelve el audiolibro completo por coincidencia de prefijo. **Comportamiento deseado tras el
arreglo de SEC-17:** 404. Si el paso 3 "funciona" y el paso 4 también devuelve fichero, el paso 3
puede estar pasando por el *fallback* y no por la ruta exacta: el arreglo no estaría verificado.

**Paso 5 — Página móvil y QR.** Abrir `http://<ip-local>:5556/download` desde el teléfono y
descargar. Verificar que el enlace generado (`:273`) funciona con el nombre acentuado; si falla,
es la codificación de URL del `href`, no el endpoint.

**Paso 6 — Registrar el resultado en `CHAT.md`** con el nombre exacto del fichero de prueba y el
código HTTP de cada paso. Sin eso, el arreglo seguirá siendo "aplicado y no comprobado" en la
próxima auditoría.

---

## 6. Candidatos para el plan de trabajo

Prefijo `*-S*` para no colisionar con los IDs del eje 2.
**PENDIENTES** = roto o prometido y no cumplido. **POR MEJORAR** = funciona pero su diseño deja
riesgo. **NUEVAS IDEAS** = no existe hoy.
Prioridad: **P0** (antes de volver a exponer el TaskPane), **P1** (antes de la siguiente release),
**P2** (siguiente ciclo), **P3** (cuando haya hueco).

### 6.1 PENDIENTES

| ID | Prio | Qué | Rutas afectadas | Invariantes |
|---|---|---|---|---|
| **PEN-S01** | **P0** | **Autenticar la API local.** Token aleatorio por sesión escrito en un fichero con ACL del usuario (`%LOCALAPPDATA%\NEVEN\session.token`), exigido en cabecera en **todas** las rutas `/api/*`; sustituir `Access-Control-Allow-Origin: *` por el origen propio y validar `Origin`/`Host` (rechazar cualquier `Origin` que no sea el del TaskPane). Rechazar cuerpos cuyo `Content-Type` no sea `application/json`. SEC-01 | `src\startup\neven_http_server.py:633-643, 646-649, 1076-1091`; el TaskPane debe adjuntar el token: `src\TaskPane\taskpane.html`, `taskpane.js`, `datalab.js`, `audiobook.js`, `chart-gallery.js`, `ayuda.js` | **No viola ninguna.** Preserva `INV-SB-01..05`. Ojo con `INV-CP-03`: si se toca el puerto, los `postMessage` dejan de validar |
| **PEN-S02** | **P0** | **Acotar `/api/save_script`** al directorio de funciones/scripts: aceptar solo nombre base (patrón de `_handle_function_create`), resolver contra el directorio configurado y comprobar `os.path.commonpath`. Quitar el `makedirs`. SEC-03 | `src\startup\neven_http_server.py:2783-2814` (patrón a copiar: `:2669-2676`) | **Ninguna.** `INV-SB-02` se mantiene (UTF-8 sin BOM, `newline='\n'`) |
| **PEN-S03** | **P0** | **Contener el servido de ficheros estáticos:** normalizar **después** de `unquote`, resolver con `os.path.realpath` y exigir `commonpath` con el directorio base en las cuatro ramas; `_serve_file` debe recibir la ruta ya validada y rechazar lo demás con 403. SEC-04 | `src\startup\neven_http_server.py:652, 933-936, 963-968, 978-983, 1038-1073` (patrón a copiar: `:988-1016`) | **Ninguna** |
| **PEN-S04** | **P1** | **Hacer real la integridad de scripts:** (1) el instalador genera y despliega un `.sha256` por cada `.R`/`.jl`/`.py` de `C:\NEVEN\functions` y `C:\NEVEN\startup`; (2) `Sync-Dist.ps1` los regenera; (3) **solo después**, pasar `VerifyScriptIntegrity` de *fail-open* a *fail-closed* con registro explícito; (4) corregir la ontología y `SECURITY.md`, que dicen HMAC donde hay SHA-256. SEC-08 | `src\Common\Security\SecurityService.cc:34-40`; `src\Install\Install-NEVEN.ps1`; `src\Install\Sync-Dist.ps1`; `src\docs\ontologia\neven-core\neven-ontology-p1.yaml:347`; `src\SECURITY.md` | **Cierra `INV-CMN-02`** (hoy violada). **Orden obligatorio:** invertir (3) y (1) deja NEVEN sin funciones |
| **PEN-S05** | **P1** | **Endurecer las ACL de `C:\NEVEN\`** en el instalador: quitar la herencia y conceder escritura solo a Administradores, SYSTEM y al usuario instalador; lectura al resto. Atención a los directorios que el runtime **necesita** escribir (`data\`, `workspace\`, `graphics\`, `neven.log`): o se les da ACL propia o se mueven a `%LOCALAPPDATA%`. SEC-09 | `src\Install\Install-NEVEN.ps1` (nuevo bloque `icacls`/`Set-Acl`), `src\Install\Uninstall-NEVEN.ps1` | **Ninguna.** No se propone mover `C:\NEVEN\` (lo asumen `INV-SR-*`, `INV-CMN-02`, `INV-SB-*` y rutas absolutas del código) |
| **PEN-S06** | **P1** | **Añadir `/guard:cf` a `add_link_options`** y volver a medir `DllCharacteristics` de `NEVEN64.xll` (debe pasar de `0x0160` a `0x4160`). Verificar también `CETCOMPAT` en el *load config*. SEC-11 | `src\CMakeLists.txt:24`; comprobar `src\Core\CMakeLists.txt:5-7` | **Cierra `INV-BLD-02`** en el artefacto; **refuerza `INV-TEST-01`** |
| **PEN-S07** | **P1** | **Fijar el bind del servidor de audiolibros:** por defecto `127.0.0.1`; la exposición a la red local pasa a ser un *opt-in* explícito en `neven-config.json` con aviso en la interfaz, token de descarga de un solo uso embebido en el QR y CORS restringido al origen del TaskPane. SEC-16 | `src\Audiobook\neven_audiobook_server.py:38-45, 376-382`; `src\Audiobook\api\routes.py`; `src\TaskPane\audiobook.js` | **Ninguna.** Resuelve además el choque de puerto con `INV-AS-03` si se le asigna un puerto propio |
| **PEN-S08** | **P1** | **Escapar la salida en el renderizador:** `srcdoc` siempre con `sandbox="allow-scripts"` **sin** `allow-same-origin`; añadir `sandbox` a los dos `srcdoc` que no lo tienen; CSP en el documento inyectado. SEC-07 | `src\TaskPane\datalab.js:1593-1599`; `src\TaskPane\chart-gallery.js:1770`; `src\TaskPane\taskpane.js:1235` | **Avanza `INV-TF-01`** (una sola política). `INV-TF-04` intacta |
| **PEN-S09** | **P2** | **Corregir `/api/groupby` y `/api/load`:** validar los nombres de columna contra `DESCRIBE dataset` (lista blanca) y escapar los identificadores; parametrizar la ruta de `read_csv_auto`. SEC-06 | `src\startup\neven_http_server.py:500-514, 2965-2983, 4262-4274` | **Refuerza `INV-SB-03`** |
| **PEN-S10** | **P2** | **Resolver `RequestSandboxDisable()`:** o se conecta a un control real del Ribbon (con persistencia y registro) o se elimina, y en cualquier caso **se corrige `Evaluacion_OWASP.md:16`**, que la acredita como mitigación. Añadir un registro explícito cada vez que el motor arranque con el sandbox desactivado. SEC-14 | `src\Common\ConfigService.cc:111-155`, `ConfigService.h:99`; `src\Ribbon\ribbon_ui.xml`; `src\docs\Evaluaciones\Evaluacion_OWASP.md` | **Ninguna** |
| **PEN-S11** | **P2** | **DACL propia en los named pipes:** `SECURITY_ATTRIBUTES` que conceda acceso solo al usuario actual, más `FILE_FLAG_FIRST_PIPE_INSTANCE` para detectar nombre ocupado, y `SECURITY_SQOS_PRESENT \| SECURITY_IDENTIFICATION` en el `CreateFileA` del cliente. SEC-12 | `src\Common\IPC\pipe.cc:216-227`; `src\Core\src\language_service.cc:228, 408` | **`INV-CJ-03` se preserva** (no cambia el nombre ni el marco de los mensajes); `INV-CMN-03` intacta; `INV-CR-02` (3 s de reintentos) intacta |
| **PEN-S12** | **P2** | **Validar los mensajes del puente del visor:** serializar el JSON con la librería (`json11`) en lugar de concatenar, y validar `sim-command` contra un esquema antes de escribir la cola. SEC-15 | `src\Common\PostMessageBridge.cc:73-82, 119-130`; consumidores `src\NEVEN-SIM\src\bridge_poller.cc:30`, `sim_main.cc:619` | **Ninguna** |
| **PEN-S13** | **P2** | **Actuar sobre el resultado de `validate_path`**: si una ruta de la configuración no valida, usar el valor por omisión y registrarlo; añadir la comilla doble a la lista de caracteres bloqueados. SEC-13 | `src\Common\ConfigService.cc:78-105` | **Ninguna** |
| **PEN-S14** | **P2** | **Rotación y protección del log.** `neven.log` está en 119,6 MB, contiene 1,6 M de líneas con código de arranque, 8 448 líneas de comandos y valores de celda, es legible por `BUILTIN\Usuarios` y **modificable** por cualquier usuario autenticado. Rotar por tamaño, bajar a DEBUG lo que hoy registra código, y dejarlo fuera del alcance de escritura general. SEC-09 | `src\Common\LogService.*`; `C:\NEVEN\neven.log` (producción); PEN-S05 | **Ninguna** |
| **PEN-S15** | **P2** | **Arreglo del endpoint de descarga (SEC-17):** eliminar el `unquote` redundante, sustituir `startswith` por `commonpath`, **quitar el *fallback* por prefijo** (404 si no existe el nombre exacto) y codificar el `href` de `/download` como URL. Después, ejecutar el procedimiento de §5. | `src\Audiobook\neven_audiobook_server.py:91-124, 273` | **Ninguna** |
| **PEN-S16** | **P3** | **Rotar y endurecer el certificado local:** vigencia de 1 año en lugar de 10, clave privada cifrada o solo en el almacén de Windows (sin `.key` PEM en disco), sacar la contraseña literal del PFX de los scripts versionados a un parámetro, y añadir `127.0.0.1` al SAN si se sigue usando esa URL. SEC-10 | `src\TaskPane\Generate-Cert.ps1:33-74`; `src\Install\Install-NEVEN.ps1:1082-1111`; `C:\NEVEN\certs\` | **Ninguna.** Alinea con el espíritu de `INV-INS-01` |
| **PEN-S17** | **P3** | **Rotar la clave del recurso Azure** del endpoint que quedó en el historial, si ese recurso sigue activo, y decidir por escrito si el historial se reescribe o se acepta. SEC-18 | `src\docs\` (nota de decisión), historial de git (`de8d44b`) | **`INV-INS-01` ya cumple**; esto cierra el residual |

### 6.2 POR MEJORAR

| ID | Prio | Qué | Rutas afectadas | Invariantes |
|---|---|---|---|---|
| **MEJ-S01** | **P1** | **Aplicar el verificador de sandbox también a la ruta HTTP→pipe**, o declarar por escrito en `SECURITY.md` que el TaskPane es una zona de confianza del usuario y que el sandbox solo cubre las celdas. Las dos opciones son defendibles; lo que no lo es es la situación actual, donde el documento promete un control que esa ruta no tiene. SEC-02 | `src\startup\neven_http_server.py:1110-1112, 4332-4400`; `src\ControlPython\startup\datalab_handler.py`; `src\SECURITY.md` | **Ninguna.** Depende de MEJ-S02 (los falsos positivos de SEC-23 harían inusable el TaskPane) |
| **MEJ-S02** | **P1** | **Hacer el sandbox consciente del lenguaje**: pasar el lenguaje a `ValidateCodeForExecution` y evaluar solo su lista. Hoy las reglas de Julia (acento grave, `eval(`, `ENV`, `open(`) se aplican a R y a Python, lo que genera falsos positivos y es la razón de que la segunda puerta se construyera sin control. SEC-23 | `src\Common\Security\SandboxVerifier.cc:62-330`; `src\Include\SandboxVerifier.h:58`; `src\tests\sandbox_tests.cc` (133 tests que habrá que reetiquetar por lenguaje) | **Ninguna invariante describe el sandbox** (hueco, ver IDEA-S02). `INV-TEST-03` se mantiene |
| **MEJ-S03** | **P1** | **Convertir `/api/query` en una barrera real:** lista blanca de funciones de tabla, rechazo de sentencias múltiples y conexión DuckDB de solo lectura sobre el dataset cargado. **Requiere actualizar antes el texto de `INV-SB-03`.** SEC-05 | `src\startup\neven_http_server.py:523-560`; `src\docs\ontologia\neven-core\neven-ontology-p2.yaml:283` | **Amplía `INV-SB-03`**: cambio de ontología explícito, justificado en §4 |
| **MEJ-S04** | **P1** | **Reescribir `SECURITY.md` para el sistema real:** incluir los tres servidores HTTP y sus puertos, el TaskPane, el visor WebView2 y el módulo Audiobook; corregir el recuento de tests (369 totales, 133 `SandboxTest`, 247 relacionados con seguridad); retirar `/sdl` de la lista de flags o añadirlo al build; retirar "36/36 remediados" o sustituirlo por una tabla con IDs verificables. SEC-22 | `src\SECURITY.md`; `src\docs\Evaluaciones\Evaluacion_OWASP.md` | **Ninguna** |
| **MEJ-S05** | **P2** | **Reevaluar OWASP con la superficie completa.** A01 y A07 están puntuados sin considerar la API local; A02 afirma que el riesgo de los pipes requiere privilegios elevados, lo que es falso. Rehacer la tabla tras PEN-S01..S03 y fechar la evaluación. SEC-22, SEC-12 | `src\docs\Evaluaciones\Evaluacion_OWASP.md:14-24, 82, 214-224` | **Ninguna** |
| **MEJ-S06** | **P2** | **Política de contenido en el visor:** inyectar CSP, acotar `file:///` a los directorios de trabajo de NEVEN, y añadir `add_FrameNavigationStarting` para que los iframes hereden el filtro. Valorar `add_WebResourceRequested` para los subrecursos. SEC-19 | `src\Common\ViewerWindow.cc:552-626` | **Ninguna** |
| **MEJ-S07** | **P2** | **Usar `InputSanitizer::BuildSafeCommandLine`** en `StartChildProcess` en lugar de construir la línea a mano, y entrecomillar `pipe_name_`. SEC-20 (residual c) | `src\Core\src\language_service.cc:789`; `src\Common\Security\InputSanitizer.cc:117-152` | **Ninguna**; `INV-CJ-03` intacta |
| **MEJ-S08** | **P2** | **Reparar o retirar `AutoLoader`.** Es el único camino que valida el contenido de los scripts y no tiene invocadores; hoy la carga real pasa por `FileWatchService`, que no valida. Decidir cuál es el camino canónico y dejarlo escrito. SEC-02 | `src\Common\AutoLoader.cc:43-110`; `src\Core\src\FileWatchService.cc:68-77` | **Ninguna.** Si se unifica, `INV-CMN-02` debe seguir aplicándose en el camino que quede |
| **MEJ-S09** | **P3** | **Unificar el esquema de las URLs del TaskPane** (http/https/relativas): usar rutas relativas para que funcione con cualquier esquema y puerto. Es, probablemente, la causa de que el módulo de audiolibros no arranque. SEC-17 | `src\TaskPane\taskpane.html` (3 `http` + 2 `https`), `taskpane.js` (1), `audiobook.js:118` | **Ninguna**; ayuda a `INV-CP-03` (un solo origen) |
| **MEJ-S10** | **P3** | **Llamar a `SetDefaultDllDirectories`** al arrancar los procesos hijo para que `AddDllDirectory` surta efecto y para acotar el orden de búsqueda de DLL. Reserva del veredicto 9d | `src\ControlR\src\controlr.cc:583-592`; equivalentes en `ControlJulia`, `ControlPython` | **Ninguna**; `INV-CR-01` (carga de `R.dll` por ruta absoluta) intacta |

### 6.3 NUEVAS IDEAS

| ID | Prio | Qué | Rutas afectadas | Invariantes |
|---|---|---|---|---|
| **IDEA-S01** | **P0** | **Tests de seguridad de la API HTTP.** Suite pytest que arranque el servidor con `pipe_client_factory` simulado y fije, como propiedades: sin token → 401; `Origin` ajeno → rechazo; `/api/save_script` fuera del directorio base → 403; `/viewers/..%2f…` → 403; `/api/groupby` con `"` en el nombre de columna → 400; `srcdoc` sin `allow-same-origin`. Cada hallazgo de este informe debería quedar convertido en un test que falle hoy. SEC-24 | nueva suite en `src\TaskPane\tests\`; prerrequisito: el runner de pytest de **MEJ-02 del eje 2** | **Cumple `INV-TEST-03`** (sin Excel ni motores reales, gracias a la inyección de `pipe_client_factory`) |
| **IDEA-S02** | **P1** | **Tres invariantes nuevas en la ontología**, para los huecos detectados: (a) **ACL del directorio de producción** — `C:\NEVEN\` no debe ser escribible por `Authenticated Users`; (b) **autenticación de la API local** — ninguna ruta `/api/*` responde sin token y sin validación de origen; (c) **alcance del sandbox** — qué cubre, qué no cubre y en qué puntos se aplica. Son adiciones, no contradicen ninguna de las 62. SEC-09, SEC-01, SEC-23 | `src\docs\ontologia\neven-core\neven-ontology-p1.yaml` (ACL, sandbox), `-p2.yaml` (API) | **Añade**; ninguna violación |
| **IDEA-S03** | **P1** | **Comprobación de mitigaciones sobre el PE en el CI** (converge con IDEA-08 del eje 2): leer `DllCharacteristics` de cada binario producido y fallar el build si falta `DYNAMICBASE`, `NXCOMPAT` o `GUARD_CF`; ampliar al *load config* para `CETCOMPAT`. Habría detectado SEC-11 el día que apareció. | `src\tests\build_verification_tests.cc`; `src\.github\workflows\build-and-test.yml`; nuevo script en `src\scripts\` | **Refuerza `INV-BLD-02` e `INV-TEST-01`** sin cambiarlas |
| **IDEA-S04** | **P2** | **Regla escrita para el agente IA: ninguna acción con efecto (escribir un fichero, instalar un paquete, ejecutar código) se dispara desde la salida del modelo sin confirmación explícita del usuario en la interfaz.** Hoy se cumple de hecho (SEC-21); conviene fijarlo antes de añadir *tool calling*, y marcar la procedencia del contenido RAG en el prompt. | `src\AgentService\neven_ai_service.py`; `src\startup\neven_http_server.py` (`/api/ai/*`); `.kiro\evals\agent_behavior\` | **Ninguna**; complementa `INV-SB-05` e `INV-AS-02` |
| **IDEA-S05** | **P2** | **Un solo inventario de puertos.** Hoy el 5556 lo reclaman AgentService (`INV-AS-03`), el servidor de audiolibros y el `fallbackPort` del Studio. Documentar la asignación en un único sitio y comprobarla al arrancar (fallo claro si el puerto está ocupado por otro servicio de NEVEN). SEC-16 | `src\Install\neven-config.template.json`; `src\AgentService\neven_ai_service.py:1207`; `src\Audiobook\neven_audiobook_server.py:29`; `src\docs\ontologia\neven-core\neven-ontology-p3.yaml:205` | **Aclara `INV-AS-03`** sin cambiarla |
| **IDEA-S06** | **P3** | **Registro de seguridad separado y a prueba de borrado** para los eventos que `SECURITY.md` dice auditar: bloqueos del sandbox, arranque con sandbox desactivado, fallos de integridad, peticiones rechazadas por origen o token. Hoy todo va al `neven.log` de 119 MB que cualquier usuario puede reescribir. SEC-09, SEC-14 | `src\Common\LogService.*`; PEN-S05, PEN-S14 | **Ninguna** |
| **IDEA-S07** | **P3** | **Firmar los binarios distribuidos.** `Evaluacion_OWASP.md:23` ya reconoce "binarios sin firma" en A08. Con `C:\NEVEN\` escribible (SEC-09), una firma más una comprobación al cargar el XLL detectaría la sustitución. Coste: certificado de firma de código. | `src\Install\Build-Installers.ps1`; `src\Install\Install-NEVEN.ps1` | **Ninguna**; refuerza el espíritu de `INV-CMN-02` |
| **IDEA-S08** | **P3** | **Aislamiento a nivel de sistema operativo** para los procesos hijo (token restringido o AppContainer), que es lo que el propio encabezado de `SandboxVerifier.cc:21-23` recomienda como endurecimiento. Alto coste: R y Julia necesitan leer y escribir ficheros del usuario; probablemente solo viable para el motor Python. Se registra como dirección, no como tarea. | `src\Core\src\language_service.cc` (`LaunchProcess`), `src\ControlPython\` | **Ninguna**; `INV-CR-01`, `INV-CJ-03` y `INV-CORE-02` condicionan el diseño |

### 6.4 Nota de secuencia

El orden no es por severidad, es por dependencia:

1. **PEN-S01** (autenticación y CORS) primero: sin eso, PEN-S02, PEN-S03 y PEN-S09 arreglan
   puertas de una casa abierta.
2. **IDEA-S01** (tests de la API) a la vez que PEN-S01..S03, para que cada arreglo quede fijado.
   Depende de MEJ-02 del eje 2 (runner de pytest) y de PEN-03 del eje 2 (CI que se dispara en
   `master`), que son prerrequisitos de infraestructura.
3. **PEN-S04** (integridad) y **PEN-S05** (ACL) después, en ese orden y con el orden interno de
   PEN-S04 respetado.
4. **MEJ-S02** (sandbox por lenguaje) antes de **MEJ-S01** (aplicar el sandbox en la ruta HTTP).
5. **MEJ-S03** exige **actualizar primero la ontología** (`INV-SB-03`).
6. **MEJ-S04** y **MEJ-S05** (documentación) al final, cuando haya algo verdadero que escribir.

---

## 7. Resumen de severidades

| Severidad | Nº | IDs |
|---|---:|---|
| **Crítica** | 2 | SEC-01, SEC-03 (la segunda es crítica por su combinación con la primera) |
| **Alta** | 6 | SEC-02, SEC-04, SEC-07, SEC-08, SEC-09, SEC-16 |
| **Media** | 10 | SEC-05, SEC-06, SEC-10, SEC-11, SEC-12, SEC-15, SEC-17, SEC-22, SEC-23, SEC-24 |
| **Media-Baja** | 2 | SEC-19, SEC-21 |
| **Baja** | 3 | SEC-13, SEC-14, SEC-18 |
| **Informativa / control que funciona** | 1 | SEC-20 |
| **Total** | **24** | SEC-01 … SEC-24 |

Candidatos: **17 PENDIENTES** (3 en P0), **10 POR MEJORAR** (4 en P1), **8 NUEVAS IDEAS** (1 en
P0). **35 ítems**, todos con rutas concretas y con su relación con las invariantes declarada.

**Ningún ítem propuesto viola una invariante `INV-*`.** Dos llevan condición escrita:
**MEJ-S03** requiere ampliar el texto de `INV-SB-03` **antes** de implementarse (cambio de
ontología justificado en §4), y **PEN-S04** debe ejecutar sus cuatro pasos en el orden indicado o
deja NEVEN sin funciones. **IDEA-S02** propone **añadir** tres invariantes para huecos que la
ontología no cubre (ACL de producción, autenticación de la API local, alcance del sandbox); añadir
no contradice.

### Lo que un lector con prisa necesita saber

Con NEVEN Studio en marcha, el puerto 5555 ofrece ejecución de código y escritura de ficheros a
quien llegue a él, sin pedir nada, y con `Access-Control-Allow-Origin: *`. El sandbox de 133 tests
no cubre ese camino, la verificación de integridad no tiene con qué comparar, y
`C:\NEVEN\` es escribible por cualquier cuenta de la máquina. Los tres hallazgos se agravan entre
sí y ninguno aparece en el modelo de amenazas documentado, que sigue describiendo el NEVEN de dos
procesos hijo y una celda de Excel.








