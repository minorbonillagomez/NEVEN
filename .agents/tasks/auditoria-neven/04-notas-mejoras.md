# 04 — Eje 4: mejoras recomendadas

**Fecha:** 2026-11-21 · **HEAD:** `9eba8b1` (master) · **Prefijo real del código:** `src\`
**Entregable del eje 4 del plan** (`plan-auditoria.md` §4). Nombre de fichero alineado con
`01-`, `02-` y `03-` por indicación de la tarea, en lugar del `40-mejoras.md` del plan.
**Modo:** solo lectura. No se modificó ningún fichero de NEVEN, nada en `C:\NEVEN\`, no se
commiteó ni se hizo push. Este fichero es la única escritura.

---

## 0. Alcance, método y cómo leer este documento

### 0.1 Qué consume este eje

| Entrada | Qué aportó |
|---|---|
| `00-layout-real.md` | layout real (prefijo `src\`), 22 referencias documentales obsoletas, inventario de las 62 invariantes `INV-*`, 18 hallazgos de inventario |
| `01-notas-producto.md` | 29 hallazgos `PROD-*` + 35 candidatos (13 D, 14 M, 8 N) |
| `02-notas-codigo.md` | 56 hallazgos `COD-*` + 56 candidatos (24 PEN, 20 MEJ, 12 IDEA) |
| `03-notas-seguridad.md` | 24 hallazgos `SEC-*` + 35 candidatos (17 PEN-S, 10 MEJ-S, 8 IDEA-S) |
| `.kiro\contexto\CHAT.md` (52 KB) y `CHAT_LARGO.md` (2,16 MB) | decisiones ya tomadas, causas raíz, intentos fallidos. Leídos por secciones; §0.6 detalla qué se buscó |
| `.kiro\specs\` (27 especificaciones) | 461 casillas sin marcar = pendientes ya acordados con el usuario. §5 declara el estado de cada una |
| `src\docs\Paper\`, `src\docs\Plan_trabajo\`, `src\docs\Evaluaciones\` | el paper como entregable de tesis y los planes de mejora previos |

Los tres ejes anteriores produjeron **126 candidatos** con solape entre sí. Este eje **no los
repite**: los consolida en **55 mejoras** con trazabilidad al identificador de origen, les añade
coste, riesgo, secuencia y comprobación contra la bitácora, e incorpora **7 hallazgos nuevos**
que surgieron al hacerlo (§10). Ningún candidato de los ejes 1-3 se pierde: todos aparecen
citados en el campo *Origen* de alguna mejora.

### 0.2 Criterio de las tres familias

El criterio es el **tipo de problema**, no la gravedad:

- **Familia A — cierra un hallazgo de los ejes 1-3.** Defecto concreto del producto, del código
  o de la seguridad, con ruta y línea. 23 mejoras.
- **Familia B — ingeniería del proyecto.** Cómo se verifica, se construye, se empaqueta, se
  observa y se documenta NEVEN. No arregla un defecto de usuario: arregla la razón por la que los
  defectos de la familia A llevaban meses sin detectarse. 21 mejoras.
- **Familia C — capacidad nueva.** Funcionalidad que hoy no existe y que encaja con la
  arquitectura real: XLL + tres `Control*` por pipes + servidor HTTP local + TaskPane sin
  bundler + WebView2 + sysimage de Julia. 11 mejoras.

Cuando un ítem podía ir en dos familias, manda el criterio de la tarea: la cobertura de tests, el
CI, la reproducibilidad del build, el empaquetado, la observabilidad, la higiene documental, la
bitácora, el espacio de ontologías y el paper van a la familia B aunque el hallazgo de origen
esté en el eje 2 o 3. Se dice en el campo *Origen*.

### 0.3 Campos de cada mejora

```
**Origen:** hallazgo(s) e identificador(es) de los ejes 1-3, o "nuevo de este eje"
**Problema:** qué se rompe hoy, con ruta y línea
**Propuesta:** la acción concreta
**Ficheros y subsistemas:** rutas absolutas o relativas a src\
**Clasificación · Prioridad · Coste · Riesgo · Fundamento**
**Invariantes:** las INV-* que toca, o "ninguna"
**Bitácora:** si ya se intentó, con qué resultado
```

### 0.4 Escalas

**Clasificación** (la que pidió el usuario):

- **PENDIENTE** — está roto, o prometido y no cumplido.
- **POR MEJORAR** — funciona, pero su diseño, su estructura o su coherencia cuesta mantenerla.
- **NUEVA IDEA** — no existe hoy.

**Prioridad:** **P0** antes de volver a exponer el TaskPane a un usuario · **P1** antes de la
siguiente release o entrega de tesis · **P2** siguiente ciclo · **P3** cuando haya hueco.

**Coste:** jornadas de trabajo de una persona que ya conoce el proyecto. `S` < 1 día ·
`M` 1-3 días · `L` 4-10 días · `XL` > 10 días. Se da el rango en días además de la letra.

**Riesgo de ejecución:** probabilidad de romper algo que hoy funciona al aplicar la mejora, no
gravedad del problema que resuelve.

**Fundamento:** **VERIFICADO** (medido sobre el código, el binario, el disco o la bitácora) ·
**HIPÓTESIS** (razonado, con el método de comprobación escrito).

### 0.5 Restricción dura: la ontología manda

Ninguna de las 55 mejoras viola una invariante `INV-*`. Cada una declara las que toca o declara
explícitamente que no toca ninguna. **Cuatro** exigen reformular el texto de una invariante
**antes** de implementarse, y están recogidas en §6 con la justificación; **cuatro** proponen
**añadir** invariantes nuevas para huecos que la ontología no cubre, y añadir no contradice. Lo
que colisiona con una decisión previa del usuario —no con una invariante— está en §8, sin
implementarlo por silencio.

### 0.6 Qué se comprobó contra la bitácora

Se buscó en `CHAT.md` y `CHAT_LARGO.md`, por tema: intentos fallidos y rollbacks, CSP, ACL de
pipes, rate limiting, CI/CD, pytest, rotación de logs, runtime de WebView2, autenticación del
servidor HTTP, `.sha256` e integridad, `icacls`/ACL de producción, `/guard:cf`, refactor de
`neven_http_server.py`, `module` en Julia y sysimage, `requireNamespace`,
`attr(..., "description")`, firma de binarios, extracción del JS de `taskpane.html`, mojibake,
offline y CDN, instalación en máquina limpia, y el módulo de audiolibros.

Resultado resumido, porque cambia el tono de varias propuestas:

| Tema | Estado en la bitácora |
|---|---|
| **CSP en WebView2** | **DESCARTADO por el usuario** (2026-08-19) con razón escrita: R genera `<script>` inline, haría falta `unsafe-inline`, beneficio ~10 %, riesgo de romper Plotly/D3/Leaflet |
| **ACL restrictiva en named pipes** | **DESCARTADO** (2026-08-19): riesgo ALTO, "si falla, el XLL no conecta y Excel se congela" |
| Rate limiting del servidor HTTP | **HECHO** (ya existía, 300 req/60 s; se corrigió el mensaje) |
| `SECURITY.md` | **HECHO** (2026-08-19) y hoy desfasado (SEC-22) |
| **API HTTP sin autenticación** | evaluada en 2026-08-19 y clasificada **Baja** con el motivo "solo localhost"; nunca se actuó |
| Refactor de `neven_http_server.py` (Bloque 4) | **INTENTADO y REVERTIDO** (2026-09-24): incidente crítico, TaskPane caído. Causa: despliegue incompleto (no se copió el módulo del que dependía) + corrupción de encoding al revertir con PowerShell. Conclusión escrita: "se puede re-aplicar con mejor proceso de deploy" |
| Tercera instancia del pipe en `controlr.cc` | modificada en el repo, **nunca compilada**, diferida por riesgo |
| "Probar instalador en máquina limpia" | pendiente **ALTA recurrente** desde ~abril 2026, nunca ejecutado |
| Corrección de mojibake | **intentada y fallida** con `-replace` de PowerShell; lo que funcionó fue reemplazo de línea completa |
| Firma digital de los `.exe` | pendiente BAJA, nunca hecho |
| Filosofía offline | **decisión explícita del proyecto** ("instalar solo lo que funciona 100 % offline"); se decidió incluir los ~76 MB de `external\anyplot\plots\` en el instalador por esa razón |
| CI, pytest, rotación de logs, WebView2 en el instalador, `.sha256` desplegados, ACL de `C:\NEVEN\`, `/guard:cf` | **ninguna mención**: son territorio nuevo, no asuntos reabiertos |
| `roughViz`/Sketch y Mermaid.js | múltiples intentos fallidos, no repetir |
| Repositorio ECC | evaluado y **descartado** (coste > beneficio) |

---

## 1. Resumen

### 1.1 Recuento por familia y clasificación

| Familia | PENDIENTES | POR MEJORAR | NUEVAS IDEAS | Total |
|---|---:|---:|---:|---:|
| **A — cierra hallazgos de los ejes 1-3** | 12 | 11 | 0 | **23** |
| **B — ingeniería del proyecto** | 7 | 9 | 5 | **21** |
| **C — capacidades nuevas** | 2 | 0 | 9 | **11** |
| **Total** | **21** | **20** | **14** | **55** |

Por prioridad: **5 en P0** (A-01, A-02, A-03, B-01, B-02), **22 en P1**, **19 en P2**, **9 en P3**.
Coste agregado: **≈ 125-195 jornadas** si se hiciera todo. §9 lo reparte en cinco fases; las
fases 0 a 2, que son las que cambian el riesgo real del proyecto, suman **26-39 jornadas**.

### 1.2 Las cinco de mayor prioridad

| # | Mejora | Por qué está arriba |
|---|---|---|
| 1 | **A-01** — autenticar la API local del puerto 5555 y cerrar el CORS comodín | Hoy ejecutar código R/Julia/Python en la sesión del usuario solo exige llegar al puerto: ni token, ni validación de `Origin`, y `/api/save_script` escribe en cualquier ruta que luego el hot-reload ejecuta |
| 2 | **B-01** — mover `src\.github\` a la raíz del repositorio y arreglar el workflow | El CI **no existe para GitHub**: el fichero está en `src\.github\workflows\`, que GitHub no lee. Corregir solo la rama no habría cambiado nada. Media jornada y es el prerrequisito de que cualquier otra mejora quede protegida |
| 3 | **A-02** — puerto propio y bind local para el servidor de audiolibros | Tres servicios pelean por el 5556; el de audiolibros pierde y además escucha en `0.0.0.0` sin autenticación. Es la causa de que la descarga de audiolibros nunca se pudiera probar |
| 4 | **A-03** — arreglar el endpoint de descarga y el esquema de URLs, y ejecutar la verificación | Es el pendiente que el usuario arrastra desde el commit `9eba8b1`: el arreglo está en producción byte a byte y nunca se ejecutó. Incluye quitar el *fallback* por prefijo, que entrega un fichero distinto del pedido |
| 5 | **A-13** — librería R: `requireNamespace` + `tryCatch` + HC3 + `attr(description/category)` | Es el producto. 30 de 63 ficheros pierden **todas** sus funciones si falta un paquete, 34 no tienen `tryCatch`, los errores estándar robustos son HC0 (anticonservadores con 30-200 filas) y 62 de 63 funciones aparecen en Excel como "Exported Function" |

Las dos siguientes, por si la ventana de trabajo da para siete: **A-04** (integridad de scripts
real: 0 ficheros `.sha256` para 92 scripts desplegados) y **A-05** (ACL de `C:\NEVEN\`, hoy
escribible por cualquier cuenta autenticada de la máquina).

### 1.3 Mejoras que chocan con una invariante o con una decisión previa

Ninguna la **viola**. Cuatro exigen **reformular** el texto de una invariante antes de
implementarse, y una choca con una decisión del usuario, no con la ontología:

| Mejora | Invariante | Naturaleza del choque |
|---|---|---|
| **A-13** | `INV-LR-04` (P2:660) | La invariante exige `attr(NombreFuncion, DialogosXCL$Descripcion)` y afirma que sin ello la función no aparece en Excel. Las dos partes son falsas (el atributo real es `"description"`; la visibilidad no depende de él). **Reformular primero** (§6.1) |
| **A-11** | `INV-AS-03` (P3:205) | Fija el 5556 para AgentService como literal, sin declarar quién más puede usarlo; tres servicios lo reclaman. Si se adopta el registro de puertos en configuración, pasa a "valor por defecto" (§6.2) |
| **A-01** (parte de la barrera SQL) | `INV-SB-03` (P2:283) | La invariante se cumple y es insuficiente: un `SELECT` de DuckDB alcanza el sistema de ficheros. **Ampliar el texto** antes de implementar la lista blanca de funciones de tabla (§6.3) |
| **A-04** | `INV-CMN-02` (P1:347) | Dice HMAC donde el código hace SHA-256 sin clave, y da por hecho un control que en producción no opera (0 `.sha256` para 92 scripts). **Corregir el texto y la política de ausencia** (§6.4) |
| **A-19** | — (ninguna) | Choca con una **decisión del usuario** de 2026-08-19 que descartó la ACL en named pipes por riesgo/beneficio. Se re-propone en forma reducida y en P3, porque la premisa de aquel análisis ("requiere privilegios elevados") resultó falsa. La decisión sigue siendo del usuario (§8.3) |

Condicionadas, sin cambio de ontología: **B-19** (toca `INV-SB-01..05` y `INV-TF-01/03/04`;
exige tests previos y despliegue atómico), **A-23** (el `module` de Julia obliga a reconstruir
`neven_julia.dll`, 1,04 GB, y revalidar `INV-CJ-01/02`), **C-03** (requiere actualizar
`tipo_outputs[]` del sidecar: `INV-SJ-02/03`).

Adiciones propuestas a la ontología, que no contradicen nada: ACL del directorio de producción,
autenticación de la API local, alcance declarado del sandbox y fuente única de cada artefacto
desplegado (§6.5).

---

## 2. Familia A — Mejoras que cierran hallazgos de los ejes 1-3

23 mejoras. Cada una consolida varios candidatos de los ejes anteriores; el campo *Origen* da la
trazabilidad completa.

### A-01 · Autenticar la API local y cerrar su superficie de escritura y lectura

**Origen:** `SEC-01` (Crítica), `SEC-03` (Crítica), `SEC-04` (Alta), `SEC-05`, `SEC-06`
(= `PEN-S01`, `PEN-S02`, `PEN-S03`, `PEN-S09`, `MEJ-S03`).

**Problema.** Con NEVEN Studio en marcha, `POST /api/{r,python,julia}`
(`src\startup\neven_http_server.py:1110-1112` → `:4367 client.send_code(lines)`) ejecuta código
arbitrario en los motores de la sesión del usuario. No hay token, ni validación de `Origin`,
`Host` o `Referer`; el cuerpo se parsea como JSON sin mirar `Content-Type` (`:1091`), así que una
petición simple no necesita *preflight*; y todas las respuestas llevan
`Access-Control-Allow-Origin: *` (`:633-637`). Dos agravantes en el mismo fichero:
`_handle_save_script` (`:2783-2814`) escribe en **cualquier ruta absoluta** —solo filtra la
extensión y hace `makedirs`— y el fichero escrito lo ejecuta el *hot-reload*
(`src\Core\src\FileWatchService.cc:68-77`); y cuatro ramas de servido estático (`:933-936`,
`:963-968`, `:978-983`, `:1038-1043`) concatenan una ruta ya decodificada (`:652`) sin
contención. El bind a `127.0.0.1` excluye la red, no a los demás usuarios de la máquina ni a una
página abierta en el navegador del usuario.

**Propuesta.** Cinco cambios en el mismo fichero, en este orden:

1. Token aleatorio por sesión en `%LOCALAPPDATA%\NEVEN\session.token` con ACL del usuario,
   exigido en cabecera en **todas** las rutas `/api/*`; el TaskPane lo adjunta.
2. `Access-Control-Allow-Origin` con el origen propio en lugar de `*`, y rechazo de cualquier
   `Origin` ajeno en `do_OPTIONS` y en el despachador.
3. Rechazar cuerpos cuyo `Content-Type` no sea `application/json`.
4. `_handle_save_script` reducido al patrón que ya usa `_handle_function_create` (`:2669-2676`):
   solo nombre base con `^[A-Za-z0-9_\-\.]+$`, resuelto contra el directorio configurado, con
   `os.path.commonpath`; sin `makedirs`.
5. Contención real del servido estático: normalizar **después** de `unquote`, `os.path.realpath`
   y `commonpath` contra el directorio base en las cuatro ramas, copiando el patrón que la rama
   `/file?path=` (`:988-1016`) ya aplica bien.

Además, en el mismo paquete porque es la misma superficie: validar los nombres de columna de
`/api/groupby` contra `DESCRIBE dataset` y parametrizar la ruta de `read_csv_auto`
(`:500-514`, `:2965-2983`, `:4262-4274`).

**Ficheros y subsistemas.** `src\startup\neven_http_server.py` (líneas citadas);
clientes que deben adjuntar el token: `src\TaskPane\taskpane.html`, `taskpane.js`, `datalab.js`,
`audiobook.js`, `chart-gallery.js`, `ayuda.js`; `src\TaskPane\start_studio.py` (generación del
token).

**Clasificación:** PENDIENTE · **Prioridad:** P0 · **Coste:** L, 4-6 días (2-3 el servidor, 2-3
los seis clientes y la prueba manual de los 9 tabs) · **Riesgo:** Alto — si un cliente olvida el
token, su tab deja de funcionar y el síntoma es un 401 silencioso; mitigación: B-03 (suite de
tests de la API) a la vez, y una fase de rodaje con el token exigido pero registrando en lugar
de rechazar · **Fundamento:** VERIFICADO.

**Invariantes.** `INV-SB-01..05` se preservan: el mutex, el encoding de escritura, el límite de
`/api/query`, el rate limiter y el contexto consumible no cambian. Atención a `INV-CP-03`: si en
el proceso se cambia el puerto, los `postMessage` dejan de validar. **La parte de lista blanca de
funciones de tabla de DuckDB exige ampliar primero `INV-SB-03`** (§6.3) y por eso va separada:
los puntos 1-5 no requieren tocar la ontología.

**Bitácora.** La sesión de 2026-08-19 evaluó "HTTP server sin auth" y lo clasificó **Baja** con
el motivo "solo localhost, pero sin autenticacion"; de aquella sesión salió el rate limiting, no
la autenticación. No es una decisión descartada, es una severidad mal calibrada: el eje 3
documenta que el bind local no excluye a otros usuarios de la máquina ni a páginas del navegador,
y que en el intervalo aparecieron `/api/save_script` y el servido estático. Conviene decírselo
así al usuario, porque está revisando su propio juicio anterior con información nueva.

---

### A-02 · Puerto propio y bind local para el servidor de audiolibros

**Origen:** `PROD-01` (Crítica), `SEC-16` (Alta), `PROD-20` (= `D-01`, `PEN-S07`, `N-05`,
`IDEA-S05` parcial).

**Problema.** Tres servicios reclaman el 5556: AgentService (`src\AgentService\neven_ai_service.py:1207`,
que es a quien `INV-AS-03` se lo reserva), el servidor de audiolibros
(`src\Audiobook\neven_audiobook_server.py:29`) y el `fallbackPort` de Studio
(`src\Install\neven-config.template.json:56`). Y `_handle_audiobook_start`
(`src\startup\neven_http_server.py:2332-2341`) decide que el servidor ya está vivo con un
`connect_ex` a ciegas: si **cualquier** proceso escucha en 5556, responde
`{"status":"ok","message":"Server already running"}`. El error de bind del servidor real se
pierde porque se lanza con `stdout=DEVNULL, stderr=DEVNULL` (`:2350-2357`). Encima, cuando sí
arranca, lo hace en `host='0.0.0.0'` con `CORS(origins=["*"])` y sin autenticación
(`neven_audiobook_server.py:38-45, 376-382`), con endpoints de subida, de generación y de
configuración de clave de DeepL.

**Propuesta.** Puerto propio (5557) leído de configuración; bind por defecto a `127.0.0.1`;
exposición a la red local como *opt-in* explícito con aviso en la interfaz y **token de descarga
de un solo uso embebido en el QR**, que es lo que preserva la transferencia al móvil sin abrir
`/api/*` a la red; y `_handle_audiobook_start` validando `GET /api/health` en lugar de
`connect_ex`, con el `stderr` del hijo a un fichero de log en lugar de `DEVNULL`.

**Ficheros.** `src\Audiobook\neven_audiobook_server.py:29, 38-45, 376-382`;
`src\Audiobook\api\routes.py` (verificación del token en el *blueprint*);
`src\TaskPane\audiobook.js:20`; `src\Audiobook\start_audiobook_server.bat:38`;
`src\startup\neven_http_server.py:2314-2365`; `src\Install\neven-config.template.json`.

**Clasificación:** PENDIENTE · **Prioridad:** P0 · **Coste:** M, 2-3 días · **Riesgo:** Medio —
el QR y la app Android dependen de la URL publicada; si el token se implementa mal, la
transferencia al móvil deja de funcionar y es justo la razón de ser del módulo ·
**Fundamento:** VERIFICADO.

**Invariantes.** **Respeta `INV-AS-03` en lugar de contradecirla**: deja el 5556 para
AgentService. No toca `INV-SB-01` ni `INV-CP-03` (el 5555 no cambia). Si se adopta el registro
de puertos de A-11, ahí sí hay reformulación (§6.2).

**Bitácora.** El módulo se integró el 2026-08-19 ("Fase 2 — TAB Audiobook"); no hay ningún
intento previo de reasignar el puerto ni de cerrar el bind. Territorio nuevo.

---

### A-03 · Endpoint de descarga, esquema de las URLs del TaskPane y verificación del arreglo `9eba8b1`

**Origen:** `PROD-02` (Alta), `PROD-03` (Alta), `SEC-17`, `MEJ-S09` (= `D-02`, `D-03`,
`PEN-S15`).

**Problema.** El arreglo del commit `9eba8b1` está en producción byte a byte y **nunca se
ejecutó**. Sobre el código resultante (`src\Audiobook\neven_audiobook_server.py:91-124`): la
travesía de rutas queda bloqueada, pero quedan tres defectos. (a) Doble decodificación: Flask ya
decodifica el segmento y `unquote()` lo vuelve a decodificar. (b) `startswith` sin separador, que
acepta directorios hermanos con el mismo prefijo. (c) **El *fallback* por prefijo es la regresión
real**: si el nombre exacto no existe, lista el directorio y sirve el **primer** fichero que
empiece por lo pedido, con `mimetype='audio/mp4'` aunque sea un `*_draft.md`. Y por encima de
todo eso, el pipeline escribe `.m4a` (`muxer\ffmpeg_muxer.py:27`, `pipeline.py:317,324`) mientras
el listado, la página del QR y el cliente buscan `.m4b` (`api\routes.py:1014,1112`,
`neven_audiobook_server.py:170`). La hipótesis de por qué el botón no arranca nada:
`audiobook.js:118` llama a `http://localhost:5555/...` cuando en producción el 5555 sirve
**https** (hay `certPath`/`keyPath` en `C:\NEVEN\neven-config.json` y los ficheros existen), lo
que el navegador bloquea como contenido mixto.

**Propuesta.** Paso 0: comprobar el esquema del 5555 y pasar las URLs del TaskPane a **rutas
relativas** (3 `http` + 2 `https` en `taskpane.html`, 1 en `taskpane.js`, 1 en `audiobook.js`).
Después: quitar el `unquote` redundante, `commonpath` en lugar de `startswith`, **eliminar el
fallback por prefijo** (404 si no existe el nombre exacto), codificar como URL el `href` de
`/download` (`:273`), y unificar la extensión de salida en muxer, pipeline, listados y
`mimetype`. Por último, ejecutar el procedimiento de verificación manual de
`03-notas-seguridad.md` §5 (6 pasos, con `Miguel de Cervantes - Don Quijote de la Mancha á é í.m4b`
como caso de prueba) y **registrar el resultado en `CHAT.md`**, que es lo que impide que esto
vuelva a aparecer como "aplicado y no comprobado".

**Ficheros.** `src\Audiobook\neven_audiobook_server.py:91-124, 273`;
`src\Audiobook\muxer\ffmpeg_muxer.py:27`; `src\Audiobook\pipeline.py:317,324`;
`src\Audiobook\api\routes.py:1014,1112`; `src\TaskPane\audiobook.js:118,357,392,604`;
`src\TaskPane\taskpane.html`, `taskpane.js`.

**Clasificación:** PENDIENTE · **Prioridad:** P0 · **Coste:** M, 1-2 días de código + media
jornada de verificación manual (requiere Excel, ffmpeg y un motor TTS) · **Riesgo:** Bajo para el
endpoint; Medio para el cambio a rutas relativas, que toca llamadas de todos los tabs ·
**Fundamento:** VERIFICADO el código y los hashes repo↔producción; **HIPÓTESIS** el contenido
mixto como causa del fallo del botón (comprobable en un minuto con `document.location.protocol`).

**Invariantes.** Ninguna. El cambio a rutas relativas **ayuda** a `INV-CP-03`, porque deja un
solo origen.

**Bitácora.** El commit `9eba8b1` es el HEAD actual y su propio mensaje dice qué intentaba
arreglar; la bitácora no registra ninguna verificación posterior. No hay intento previo sobre la
extensión `.m4a`/`.m4b` ni sobre el esquema de las URLs.

---

### A-04 · Hacer real la integridad de los scripts desplegados

**Origen:** `SEC-08` (Alta) (= `PEN-S04`).

**Problema.** `SecurityService::VerifyScriptIntegrity` devuelve `true` cuando falta el fichero
`.sha256` (`src\Common\Security\SecurityService.cc:34-40`, *fail-open*), y en producción hay
**0** ficheros `.sha256` para los 92 scripts de `C:\NEVEN\functions` (63 `.R` + 11 `.jl` + 18
`.py`) y **0** para los 3 de `C:\NEVEN\startup`. El repositorio **sí** tiene
`src\startup\startup.r.sha256` y `startup.jl.sha256`: el control existe y el instalador no lo
despliega. Además es SHA-256 sin clave, no HMAC como dicen `INV-CMN-02` y `SECURITY.md`.

**Propuesta,** en este orden y sin invertirlo:

1. El instalador genera y despliega un `.sha256` por cada `.R`/`.jl`/`.py` de
   `C:\NEVEN\functions` y `C:\NEVEN\startup`.
2. `Sync-Dist.ps1` los regenera en cada sincronización.
3. **Solo entonces**, pasar la verificación de *fail-open* a *fail-closed* con registro explícito
   del fichero rechazado.
4. Corregir el texto de `INV-CMN-02` y de `SECURITY.md` (§6.4).

**Ficheros.** `src\Common\Security\SecurityService.cc:34-40`; `src\Install\Install-NEVEN.ps1`;
`src\Install\Sync-Dist.ps1`; `src\docs\ontologia\neven-core\neven-ontology-p1.yaml:347`;
`src\SECURITY.md`.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** M, 2-3 días · **Riesgo:** Alto si
se invierte el orden — pasar a *fail-closed* antes de desplegar los hashes deja NEVEN sin
funciones; y cada actualización manual de un `.R` en producción que no regenere su hash provoca
el mismo efecto, así que el paso 3 necesita que B-08 (fuente única y script de paridad) esté
hecho · **Fundamento:** VERIFICADO (conteo en disco, solo lectura).

**Invariantes.** **Cierra `INV-CMN-02`**, hoy violada en producción. Requiere reformular su texto
(§6.4): o se implementa HMAC de verdad, o la invariante dice SHA-256. La recomendación es lo
segundo, con el motivo escrito en §6.4.

**Bitácora.** Sin menciones. El control se introdujo en la remediación de seguridad de mayo
(`security-remediation`, 72/72 tareas marcadas) y nadie verificó que operase sobre lo desplegado.

---

### A-05 · Endurecer las ACL del directorio de producción

**Origen:** `SEC-09` (Alta), `SEC-10`, `PROD-19` (= `PEN-S05`, parte de `PEN-S14`).

**Problema.** `C:\NEVEN`, `C:\NEVEN\functions` y `C:\NEVEN\certs` tienen
`NT AUTHORITY\Authenticated Users : Modify` heredado de la raíz `C:\`, y el instalador no llama a
`icacls` ni a `Set-Acl` en ningún punto. Cualquier cuenta local puede reescribir los 92 scripts
que se ejecutan por *hot-reload*, `neven-config.json` (incluido `sandboxEnabled`), los binarios
que Excel carga, la clave privada PEM sin cifrar del certificado instalado en la raíz de
confianza del usuario, y el `neven.log` de 119,6 MB que contiene líneas de código de arranque,
8 448 líneas de comandos y valores de celda —y que, siendo modificable, invalida el rastro de
auditoría que invoca `SECURITY.md`.

**Propuesta.** Bloque de endurecimiento en el instalador: quitar la herencia y conceder escritura
solo a Administradores, SYSTEM y al usuario instalador; lectura al resto. **Antes** hay que
enumerar lo que el runtime necesita escribir (`data\`, `workspace\`, `graphics\`, `output\`,
`logs\`, `neven.log`, `functions\` si se mantiene el flujo de creación de funciones desde el
TaskPane) y decidir, para cada uno, ACL propia o traslado a `%LOCALAPPDATA%`. El desinstalador
debe revertirlo.

**Ficheros.** `src\Install\Install-NEVEN.ps1` (bloque nuevo), `src\Install\Uninstall-NEVEN.ps1`.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** M-L, 3-4 días (la mayor parte es
inventariar y probar las escrituras del runtime, no escribir el `icacls`) · **Riesgo:** Alto —
una ACL de más deja a NEVEN sin poder escribir sus propios ficheros de trabajo, y el síntoma
aparece lejos del cambio. Mitigación: aplicar primero en una instalación de prueba (B-11,
máquina limpia) y no en la instalación viva del usuario · **Fundamento:** VERIFICADO
(`Get-Acl`, solo lectura).

**Invariantes.** Ninguna de las 62 cubre las ACL del directorio de producción: es un **hueco**,
no una violación. Se propone **añadir** una invariante (§6.5a). **No se propone mover
`C:\NEVEN\`**: lo asumen `INV-SR-01..05`, `INV-CMN-02`, `INV-SB-01..05` y rutas absolutas del
código y de los scripts; mover el directorio es un proyecto, no un arreglo.

**Bitácora.** Sin menciones de `icacls` ni de permisos de producción. Territorio nuevo.

---

### A-06 · `/guard:cf` en el enlazado del XLL principal

**Origen:** `SEC-11` (= `PEN-S06`).

**Problema.** `NEVEN64.xll` se distribuye con `DllCharacteristics = 0x0160`, es decir **sin
Control Flow Guard**, en `src\Build\Dist`, `src\Install\Dist` y `C:\NEVEN`. Todos los demás
binarios de NEVEN sí lo llevan (`NEVENRibbon.dll` y `NEVEN-SIM.xll` `0x4160`; los tres
`Control*.exe` `0xC160`). El único que falta es el que Excel carga en su propio proceso. Causa
probable: `/guard:cf` está en `add_compile_options` (`src\CMakeLists.txt:20`) y **no** en
`add_link_options` (`:24`), y `NEVEN_Core` es el único objetivo construido a través de una
*object library* (`src\Core\CMakeLists.txt:5-7`).

**Propuesta.** Añadir `/guard:cf` a `add_link_options`, reconstruir y volver a leer los 2 bytes
de `DllCharacteristics` (debe pasar a `0x4160`). Verificar también `CETCOMPAT`, que vive en el
*load config* extendido y no se pudo medir con el método del eje 3. La comprobación automática
sobre el PE va en B-01/B-07 (job de CI).

**Ficheros.** `src\CMakeLists.txt:24`; comprobar `src\Core\CMakeLists.txt:5-7`.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** S, 2-4 horas de cambio + el tiempo
de reconstruir y redesplegar · **Riesgo:** Bajo técnicamente, Medio operativamente: obliga a
regenerar y redesplegar el XLL con Excel cerrado (`INV-RIBBON-05` describe el procedimiento para
el Ribbon; el XLL tiene el mismo problema de fichero en uso) · **Fundamento:** VERIFICADO el
estado del binario (parser PE propio validado contra `kernel32.dll` y `notepad.exe`);
**HIPÓTESIS** la causa.

**Invariantes.** **Cierra `INV-BLD-02`** en el artefacto, que es donde está incumplida. No se
quita ningún flag, así que `INV-TEST-01` (`build_verification_tests.cc` comprueba presencia en el
`CMakeLists`) sigue pasando. `INV-BLD-01` (`/MT`) intacta.

**Bitácora.** Sin menciones de `/guard:cf`. Nadie lo vio porque el test que debería protegerlo
lee el `CMakeLists.txt`, no el binario.

---

### A-07 · Guarda de excepciones en los cuatro exports del XLL

**Origen:** `COD-01` (Alta) (= `PEN-01`).

**Problema.** `xlAutoOpen` (`src\Core\src\rj2xcl.cc:619-651`) ejecuta `Init()` completo —
configuración, `json11` (que lanza con JSON malformado), creación de directorios, `taskkill`,
`ConnectLanguages()`, `MapFunctions()`, `RegisterFunctions()` — sin ningún `try`/`catch`. Lo
mismo `xlAutoClose` (`:653-668`), que llama a `PlutoManager::Shutdown()` y
`ViewerManager::Shutdown()`. Una excepción C++ que cruce un `extern "C" __stdcall` invocado por
Excel es comportamiento indefinido: en la práctica Excel termina sin mensaje y sin entrada en
`neven.log`.

**Propuesta.** Envolver el cuerpo de los cuatro exports en
`try { ... } catch (const std::exception& e) { log } catch (...) { log }` y devolver `1`, como ya
hace `OnConnection` del Ribbon por exigencia de `INV-RIBBON-02`. Añadir el null-check de
`xlAutoFree12` (`:670`) en el mismo paso.

**Ficheros.** `src\Core\src\rj2xcl.cc:619-651, 653-668, 670-686, 690-707`.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** S, 2-4 horas · **Riesgo:** Bajo ·
**Fundamento:** VERIFICADO.

**Invariantes.** Ninguna. La envoltura no cambia el orden ni el contexto, así que
`INV-CORE-01` (registro solo en `xlAutoOpen`), `INV-CORE-02` (orden de los 8 pasos),
`INV-CORE-03` (guard de doble inicialización) e `INV-CORE-04` (exports presentes) se preservan.

**Bitácora.** Sin menciones.

---

### A-08 · Política única de `srcdoc` en el TaskPane

**Origen:** `SEC-07` (Alta) (= `PEN-S08`).

**Problema.** Tres rutas renderizan HTML producido por los motores con tres políticas distintas:
`src\TaskPane\datalab.js:1593-1599` usa `sandbox="allow-scripts allow-same-origin"`, que es la
combinación que **anula** el aislamiento (el documento hereda el origen del contenedor y alcanza
`window.parent`); `src\TaskPane\chart-gallery.js:1770` y `src\TaskPane\taskpane.js:1235` no ponen
`sandbox` en absoluto. Si en ese HTML entra texto que el usuario no escribió —el nombre de una
columna de un CSV, una celda de un libro recibido por correo, un fragmento del RAG— se ejecuta
como JavaScript con el origen del TaskPane, desde donde se alcanza `Office` y la API local.

**Propuesta.** Una sola política: `sandbox="allow-scripts"` **sin** `allow-same-origin` en los
tres puntos, y escape del contenido en los sumideros que no necesitan HTML.

**Ficheros.** `src\TaskPane\datalab.js:1593-1599`, `chart-gallery.js:1770`, `taskpane.js:1235`.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** S, 4-8 horas + prueba de las
visualizaciones · **Riesgo:** Medio — hay que comprobar que ningún contenido de `srcdoc`
dependa de alcanzar el documento padre; los botones "Enviar a Slide" y de descarga viven **fuera**
del iframe (`_addSendToSlideBtn` en `taskpane.html:4371`), así que la expectativa es que no se
rompa nada, pero hay que verificarlo con Plotly, D3, Leaflet y KaTeX · **Fundamento:** VERIFICADO.

**Invariantes.** Avanza `INV-TF-01` (una sola política de renderizado). `INV-TF-04` intacta:
cambiar un atributo no requiere empaquetador.

**Bitácora. Importante: esto no es el CSP que el usuario descartó.** La decisión de 2026-08-19
descartó inyectar una **CSP en el visor WebView2**, porque el HTML de R lleva `<script>` inline y
haría falta `unsafe-inline`. Aquí se trata del atributo `sandbox` de los `<iframe srcdoc>` del
**TaskPane**, que no prohíbe scripts inline y por tanto no rompe Plotly. Se dice explícitamente
para que no parezca que se reabre un asunto cerrado.

---

### A-09 · Unificar los renderizadores de resultados en `buildSlotElement`

**Origen:** `COD-41`, `PROD-13`, `PROD-14`, `COD-42` (= `MEJ-06`, `PEN-16`, `M-03`, `M-04`).

**Problema.** `INV-TF-01` declara `buildSlotElement()` el único renderizador y el veredicto del
eje 2 es **PARCIAL**: la función está definida una sola vez (`datalab.js:1528`), pero hay cuatro
renderizadores paralelos — `renderScriptResult` (`taskpane.js:1219`), el *fallback* literal de
`taskpane.html:7243`, `_renderBackendResult` (`chart-gallery.js:1646`) y `renderScriptResultRS`
(`taskpane.html:5327`) — más el par duplicado `renderSQLResultRS`/`renderSQLResults` y
`_excelRenderSlots` (`taskpane.html:7244-7301`) en el tab comentado. Y `showToast` está definida
tres veces con tres firmas. El acoplamiento es frágil: `taskpane.html` invoca
`buildSlotElement` solo tras `typeof ... === 'function'`, así que depende del orden de 23
etiquetas `<script>` y degrada en silencio al *fallback* si `datalab.js` no cargó.

**Propuesta.** Convertir los renderizadores paralelos en adaptadores que produzcan slots
`{name,label,type,value,tier}` y deleguen en `buildSlotElement`; eliminar `_excelRenderSlots` y el
panel comentado `excel-analysis` (`taskpane.html:861`), el panel huérfano `id="sql"` (`:384`) y
los `typeof` defensivos; dejar una sola `showToast` con `duration` opcional.

**Ficheros.** `src\TaskPane\datalab.js:1528`; `taskpane.js:476,1219`;
`taskpane.html:384,861,2336,2657,5211,5327,7243-7301`; `chart-gallery.js:1646`;
`audiobook.js:43`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** L, 4-6 días · **Riesgo:** Medio —
es el camino por el que se ve todo resultado; sin tests de frontend (B-20) la única red es la
prueba manual de los 9 tabs · **Fundamento:** VERIFICADO.

**Invariantes.** **Cierra `INV-TF-01`**. `INV-TF-03` (copiar con `[System.IO.File]::Copy()`) y
`INV-TF-04` (sin bundler) se respetan.

**Bitácora.** Sin intentos previos de unificación. Sí hay una lección aplicable registrada:
"cuando un cambio en `.html` no funciona, buscar si `.js` tiene la misma función" — que es
exactamente el síntoma de esta duplicación.

---

### A-10 · Sandbox consciente del lenguaje, y alcance declarado por escrito

**Origen:** `SEC-02` (Alta), `SEC-23` (= `MEJ-S01`, `MEJ-S02`).

**Problema.** `SandboxVerifier` evalúa **las tres listas de lenguaje sobre cualquier entrada**
(`src\Common\Security\SandboxVerifier.cc:269-323`): código R legítimo que contenga `eval(`, un
acento grave, `open(` o el token `ENV` se rechaza por reglas de Julia. Ese coste en falsos
positivos es la causa de fondo de que la vía HTTP→pipe se construyera **sin ningún control**:
`git grep` de sandbox sobre `neven_http_server.py`, `datalab_handler.py` y `pipe_client.py`
devuelve cero. Y las excepciones de contexto son decorativas: un comentario `# neven` en
cualquier parte del fragmento habilita `library()` arbitraria (`:240-262`), y mencionar una ruta
de NEVEN habilita `source()` de cualquier fichero (`:214-233`), porque no se extrae el argumento
real. Además, el único camino que valida contenido (`AutoLoader`) **no tiene invocadores**: la
carga real pasa por `FileWatchService`, que verifica integridad pero no contenido.

**Propuesta.** Dos partes, en este orden. (1) Pasar el lenguaje a `ValidateCodeForExecution` y
evaluar solo su lista; reetiquetar por lenguaje los 133 tests de `sandbox_tests.cc`. (2) Decidir
y escribir el alcance: o se aplica el verificador también en la ruta HTTP→pipe, o se declara en
`SECURITY.md` que el TaskPane es zona de confianza del usuario y que el sandbox solo cubre las
celdas. Las dos opciones son defendibles; lo que no lo es es prometer un control que esa ruta no
tiene. En el mismo paquete: reparar o retirar `AutoLoader` y dejar escrito cuál es el camino
canónico de carga.

**Ficheros.** `src\Common\Security\SandboxVerifier.cc:62-330`; `src\Include\SandboxVerifier.h:58`;
`src\tests\sandbox_tests.cc` (133 tests); `src\Common\AutoLoader.cc:43-110`;
`src\Core\src\FileWatchService.cc:68-77`; `src\startup\neven_http_server.py:1110-1112, 4332-4400`;
`src\SECURITY.md`.

**Clasificación:** POR MEJORAR · **Prioridad:** P1 · **Coste:** L, 4-6 días (la mayor parte es
reetiquetar y revisar los 133 tests) · **Riesgo:** Medio — tocar el verificador puede rechazar
código que hoy pasa, o al contrario; los 158 tests de sandbox son la red, y hay que extenderlos
antes de cambiar la lógica · **Fundamento:** VERIFICADO.

**Invariantes.** **Ninguna de las 62 describe el sandbox**, que es el control que `SECURITY.md`
presenta como principal: otro **hueco** de la ontología. Se propone añadir una invariante de
alcance (§6.5c). `INV-TEST-03` se mantiene (los tests no necesitan motores).

**Bitácora.** Sin intentos previos. La bitácora sí confirma el efecto: en el flujo de Run Script
se documentó que "el enfoque de guardar script y hacer `source(path)` vía Office.js **no funciona
debido al sandbox**", que es el falso positivo de esta misma lógica visto desde el producto.

---

### A-11 · Un solo contrato de configuración y un solo inventario de puertos

**Origen:** `PROD-06` (Alta), `PROD-01`, `SEC-16` (= `D-05`, `N-03`, `IDEA-S05`).

**Problema.** `src\Install\neven-config.template.json` y el `neven-config.json` de producción
tienen esquemas incompatibles. Solo en el template: `AI.*`, `auto_load_xll`. Solo en producción:
`version`, `active_ai_profile`, `ai_profiles`, `db_connections`, `prompts`, `preferences`. Y los
dos consumidores leen esquemas distintos: NEVEN Studio lee `ai_profiles` y `db_connections`
(6 referencias en `src\startup\neven_http_server.py`), AgentService lee `AI`
(`src\AgentService\neven_ai_service.py:733`, que emite "AI.enabled=false" con el config de
producción). Una instalación limpia parte del template y produce un fichero que el servidor de
Studio no entiende. En paralelo, ningún sitio declara la asignación de puertos y tres servicios
reclaman el 5556.

**Propuesta.** Un esquema único con `version` y migración desde el antiguo; AgentService
adaptado a `ai_profiles`; sección `ports` explícita (`ports.studio`, `ports.agent`,
`ports.audiobook`) leída por los tres servicios, con comprobación al arrancar y mensaje claro si
el puerto está ocupado por otro servicio de NEVEN.

**Ficheros.** `src\Install\neven-config.template.json`; `src\AgentService\neven_ai_service.py:733,1207`;
`src\startup\neven_http_server.py`; `src\Audiobook\neven_audiobook_server.py:29`;
`src\TaskPane\audiobook.js:20`; `src\Install\Install-NEVEN.ps1` (migración).

**Clasificación:** POR MEJORAR · **Prioridad:** P1 · **Coste:** M-L, 3-4 días · **Riesgo:**
Medio — el fichero de configuración es el que hace arrancar todo; la migración debe hacer backup
`.bak` antes de sobrescribir · **Fundamento:** VERIFICADO.

**Invariantes.** `INV-INS-03` (backup `.bak` en modo `-IsUpdate`) e `INV-INS-04` (UTF-8 sin BOM)
deben seguir cumpliéndose en la migración. **`INV-AS-03` pasa de literal a valor por defecto
configurado: requiere reformulación previa** (§6.2). `INV-INS-01` intacta: ni el template ni
producción contienen hoy una clave de API no vacía (verificado sin transcribir valores).

**Bitácora.** La divergencia de esquemas no aparece registrada; el tab IA y los `ai_profiles` se
construyeron en septiembre sobre el servidor de Studio, y AgentService quedó con el esquema de la
especificación `ai-integration` de mayo (§5). No hay decisión previa que respetar.

---

### A-12 · WebView2 en el preflight del instalador

**Origen:** `PROD-05` (Alta) (= `D-04`).

**Problema.** `src\Install\Install-NEVEN.ps1` (104 KB) tiene **cero** ocurrencias de `WebView2`,
y de ese runtime cuelga toda la interfaz: TaskPane, visor, editor, Pluto y Quarto. El instalador
sí hace un preflight serio para los motores (`Find-R`, `Find-Julia`, `Find-Python`, con detección
por PATH y registro, exclusión del stub de WindowsApps, versión mínima, enlace de descarga y
pausa interactiva). El código ya tiene los mensajes de fallo preparados ("WebView2 not available
— install Edge WebView2 Runtime" en seis puntos de `basic_functions.cc`), así que el usuario de
una máquina sin runtime recibe un texto de error en la celda y ninguna advertencia en la
instalación.

**Propuesta.** Detectar el runtime (clave de registro del Evergreen Runtime), y en su ausencia
ofrecer la descarga del *bootstrapper* o, si se quiere instalación desatendida, incluirlo como
prerrequisito del NSIS. Añadirlo al `Show-PreflightSummary` (L383-446) con el mismo formato que
los motores.

**Ficheros.** `src\Install\Install-NEVEN.ps1` (`Show-PreflightSummary`, L383-446);
`src\Install\NEVEN-Setup.nsi`; `src\docs\Arquitectura\Dependencias_Instalacion.md`.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** M, 1-2 días · **Riesgo:** Bajo ·
**Fundamento:** VERIFICADO.

**Invariantes.** Ninguna.

**Bitácora.** Sin menciones del runtime de WebView2 en el instalador. Sí está el pendiente
recurrente "probar instalador en máquina limpia" (B-11), que es justo donde esto se habría visto.

---

### A-13 · Librería R: `requireNamespace`, `tryCatch`, HC3 y atributos de ayuda

**Origen:** `PROD-08` (Alta), `PROD-17`, `COD-27`, `COD-28`, `COD-29`, `COD-30`, `COD-31`
(= `PEN-06`, `PEN-07`, `PEN-08`, `PEN-15`, `D-08`, `M-02`).

**Problema.** Cuatro defectos sobre los mismos 63 ficheros de `src\libreria\R`:

1. **30 ficheros tienen `library()` en el nivel superior**, contra `INV-LR-02`. Si el paquete no
   está instalado, el `source()` del fichero **completo** falla y el usuario pierde todas sus
   funciones, no solo la que necesitaba el paquete. Es la causa documentada de los `#¿NOMBRE?` en
   bloque. La migración a `requireNamespace` está empezada (11 ficheros ya lo usan) y sin acabar.
2. **34 de 63 ficheros no tienen un solo `tryCatch`**: un error analítico (matriz singular, NA en
   el `lm`) propaga la condición de R y la celda recibe algo que no es el contrato `R4XCL_`.
3. **`vcovHC(type = "HC")` es HC0** (`R4XCL-RG-Lineal.R:124`), que subestima la varianza en
   muestras pequeñas y produce p-valores anticonservadores — justo el régimen de una hoja con
   30-200 filas. HC3 es la corrección recomendada y es una cadena.
4. **Una sola asignación de `attr(..., "description")` en los 63 ficheros**, de modo que el
   asistente de funciones de Excel muestra "Exported Function" y "Argument" para casi todo el
   catálogo (el mecanismo real está en `src\startup\startup.r:69-71` y
   `excel_api_functions.cc:272,292,296`).

**Propuesta.** Un barrido por los 63 ficheros: `library()` → `requireNamespace(..., quietly=TRUE)`
dentro de `tryCatch`; envolver el cuerpo analítico con
`error = function(e) data.frame(R4XCL_Error = conditionMessage(e))`; `type = "HC3"` (o parámetro
con HC3 por defecto); y `attr(fn,"description")` + `attr(fn,"category")` en cada función
exportada. Desplegar con `UTF8Encoding($false)`.

**Ficheros.** los 30 con `library()` (lista en `COD-27`), los 34 sin `tryCatch` (`COD-29`),
`src\libreria\R\R4XCL-RG-Lineal.R:124`, y los 5 sin ningún `attr(`
(`R4XCL-AD-NonParRolCor.R`, `R4XCL-BD-ObtieneDatos.R`, `R4XCL-DS-Wooldridge.R`,
`R4XCL-GR-Mapa.R`, `R4XCL-NEVEN-pluto-read.R`) más el resto del catálogo.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** L, 5-7 días · **Riesgo:** Medio —
63 ficheros de código del usuario final; sin los runners `.R` de `src\tests` convertidos en suite
(B-02/C-04) la verificación es manual. Hacerlo por familias (`RG`, `AD`, `GR`, `ST`) y no de
golpe · **Fundamento:** VERIFICADO los cuatro conteos.

**Invariantes.** **Cierra `INV-LR-02`** (hoy violada en 30 ficheros) y **refuerza `INV-LR-03` e
`INV-NX-04`**. Los atributos de ayuda **exigen reformular `INV-LR-04` antes** (§6.1), porque la
invariante actual nombra un mecanismo que el código no implementa. `INV-SR-05` manda el método de
despliegue (`UTF8Encoding($false)`, nunca `[System.Text.Encoding]::UTF8`).

**Bitácora.** No hay intento previo de migrar los `library()` ni de añadir los atributos. Sí hay
precedente documentado del mecanismo correcto: en una sesión de documentación se escribió
`attr(MiModelo, "description") <- ...` como la forma de registrar ayuda, y el paper lo documenta
igual (`03_viewer_extensibility.tex:95-96`). Es decir, el proyecto ya sabe cuál es la forma
correcta; falta aplicarla y corregir la ontología, que dice otra cosa.

---

### A-14 · `ViewerManager`: estado compartido atómico y cierre sin `TerminateThread`

**Origen:** `COD-06`, `COD-07` (= `PEN-11`, `PEN-12`).

**Problema.** `available_` es un `bool` no atómico (`src\Common\ViewerManager.h:188`) escrito
desde el hilo de Excel (`:99,123,139,146`) y desde el hilo STA, como documenta el propio
comentario del código (`ViewerManager.cc:144`); `viewers_` sí está protegido por mutex, pero
`available_`, `max_viewers_`, `max_memory_mb_`, `sta_thread_id_` y `sta_thread_handle_` quedan
fuera. Y el cierre hace `TerminateThread` sobre el hilo STA si no responde a `WM_QUIT` en 5 s
(`ViewerManager.cc:155-166`), lo que no desenrolla la pila ni libera locks: sobre un hilo con
objetos COM de WebView2 vivos puede dejar el heap **de Excel** inconsistente justo al salir. Es
la causa clásica de "Excel se cerró al salir".

**Propuesta.** `std::atomic<bool> available_`; fijar `max_viewers_`/`max_memory_mb_` antes de
lanzar el hilo; y sustituir `TerminateThread` por registrar el fallo y abandonar el hilo — el
proceso va a terminar de todos modos.

**Ficheros.** `src\Common\ViewerManager.h:188, 211-212`; `src\Common\ViewerManager.cc:99, 123,
139, 146, 155-166`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** S-M, 1 día · **Riesgo:** Medio —
es la parte más concurrente del proyecto y tiene **cero** tests (`COD-23`); conviene emparejarlo
con el test de ciclo de vida del hilo STA de B-05 · **Fundamento:** VERIFICADO.

**Invariantes.** Ninguna.

**Bitácora.** Sin menciones.

---

### A-15 · Acotar el *zombie cleanup* a procesos huérfanos

**Origen:** `COD-02` (= `PEN-10`).

**Problema.** `src\Core\src\rj2xcl.cc:457-476` ejecuta
`taskkill /F /IM ControlR.exe /T` (y Julia y Python) al arrancar. `taskkill /IM` mata **todos**
los procesos con ese nombre en la sesión, no solo los huérfanos: si el usuario abre un segundo
Excel con NEVEN, el `xlAutoOpen` del segundo deja sin motores al primero, que seguirá mostrando
funciones registradas que devuelven error de pipe.

**Propuesta.** Registro de PIDs en `%LOCALAPPDATA%` o enumeración por proceso padre, y matar solo
lo que no tenga un Excel vivo detrás. El JobObject que `Init()` ya crea es el mecanismo natural
para acotarlo.

**Ficheros.** `src\Core\src\rj2xcl.cc:457-476`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** M, 1-2 días · **Riesgo:** Medio —
si la detección de huérfanos falla al revés, quedan procesos zombi que bloquean los pipes, que es
el problema que el `taskkill` vino a resolver · **Fundamento:** VERIFICADO el código;
**HIPÓTESIS** el efecto con dos instancias de Excel (no se probó).

**Invariantes.** **`INV-CORE-02` se preserva**: fija el **orden** (limpieza antes de
`file_watch_service_->Start()` y `ConnectLanguages()`, hoy en `:480` y `:487`), no el
**mecanismo**.

**Bitácora.** Sin intentos previos. Relacionado con un problema real documentado: el error 231
("All pipe instances are busy") llevó a matar ControlR a mano para limpiar pipes, lo que indica
que el ciclo de vida de los motores ya ha dado guerra.

---

### A-16 · Validar los mensajes del puente del visor

**Origen:** `SEC-15` (= `PEN-S12`).

**Problema.** `src\Common\PostMessageBridge.cc:119-130` construye el JSON de `writeCell`
**concatenando** `sheet`, `cell` y `value` sin escapar, y lo escribe en
`C:\NEVEN\data\bridge_queue.json`; `:73-82` escribe el mensaje de `sim-command` **tal cual**, sin
validar nada, en `C:\NEVEN\data\sim_command.json`. Los consumidores son
`src\NEVEN-SIM\src\bridge_poller.cc:30` y `sim_main.cc:619`. El emisor es el HTML renderizado en
el visor, que genera R/Julia y puede incorporar datos ajenos.

**Propuesta.** Serializar con `json11` en lugar de concatenar, y validar `sim-command` contra un
esquema antes de escribir la cola.

**Ficheros.** `src\Common\PostMessageBridge.cc:73-82, 119-130`;
`src\NEVEN-SIM\src\bridge_poller.cc:30`, `sim_main.cc:619`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** S-M, 1 día · **Riesgo:** Bajo ·
**Fundamento:** VERIFICADO.

**Invariantes.** Ninguna. `INV-CP-03` **no cubre** este puente, porque el canal es
`window.chrome.webview.postMessage` y no tiene origen que comparar: la defensa tiene que ser la
validación del mensaje en C++.

**Bitácora.** Sin menciones.

---

### A-17 · `NEVEN.Notebook.Export` nunca puede funcionar: cablear `CaptureAnalysis`

**Origen:** **nuevo de este eje** (`MEJ4-02`, §10).

**Problema.** `=NEVEN.Notebook.Export(Title)` está registrada en el XLL y documentada como
"Export last analysis as Pluto notebook" (`src\Core\include\basic_functions.h:62`), y llega a
`NotebookExporter::ExportNotebook` (`src\Core\src\basic_functions.cc:914`). Pero
`NotebookExporter::CaptureAnalysis` **no tiene ningún invocador** en todo el árbol
(`git grep CaptureAnalysis -- src` devuelve solo la declaración y la definición), de modo que
`has_analysis_` es siempre `false` y la función devuelve invariablemente
`"No analysis to export — execute an analysis first"`, haga el usuario lo que haga. Dos defectos
adicionales en el mismo camino: el notebook generado cierra con `# ╔═╡ Cell order:` **sin listar
ningún UUID** (`NotebookExporter.cc:180`), que es un `.jl` probablemente inválido para Pluto; y
el Doxygen dice "exports to a standalone HTML file" mientras el código escribe `.jl`, con la
cabecera "Exported from RJ2XCL" (nombre heredado, `PROD-23`).

**Propuesta.** Llamar a `CaptureAnalysis` donde se completa una ejecución con éxito
(`LanguageService`, o `basic_functions.cc` en el retorno de `NEVEN.r/.j/.p` y de las funciones de
librería), completar la lista de orden de celdas, y corregir el Doxygen y la cabecera. Si se
decide que la captura no interesa, retirar la función del registro: lo que no debe quedar es una
función anunciada en el asistente de Excel que siempre falla.

**Ficheros.** `src\Common\NotebookExporter.cc:29, 43, 180`, `NotebookExporter.h:33`;
`src\Core\src\basic_functions.cc:914`; `src\Core\include\basic_functions.h:62`;
`src\Core\src\language_service.cc` (punto de captura).

**Clasificación:** PENDIENTE · **Prioridad:** P2 · **Coste:** M, 1-2 días (más C-05 si se quiere
la capacidad completa) · **Riesgo:** Bajo · **Fundamento:** VERIFICADO el invocador ausente;
**HIPÓTESIS** que el `.jl` sin orden de celdas sea inválido para Pluto (comprobable abriéndolo).

**Invariantes.** Ninguna. La función ya está en `funcTemplates`, así que se registra durante
`xlAutoOpen` y `INV-CORE-01` se respeta sin cambios.

**Bitácora.** Sin menciones. El exportador se construyó con el trabajo de Pluto/sysimage y nadie
volvió a mirarlo.

---

### A-18 · Endurecimientos menores del C++ con control que aparenta existir

**Origen:** `SEC-13`, `SEC-14`, `SEC-20` (residual c), `COD-09`, `MEJ-S07`, `MEJ-S10`
(= `PEN-S10`, `PEN-S13`, `MEJ-19`).

**Problema.** Cuatro controles que existen y no actúan. (a)
`ConfigService::ValidateConfig()` detecta `..` y caracteres peligrosos y **descarta el valor de
retorno** en sus seis llamadas (`src\Common\ConfigService.cc:78-105`); además la lista no incluye
la comilla doble, que es la que importaría para la línea de comandos de Quarto. (b)
`RequestSandboxDisable()` (`:111-155`) implementa el diálogo de confirmación y el registro en los
que `Evaluacion_OWASP.md:16` apoya un 9/10 en A01, y **no tiene invocadores** ni persiste el
cambio. (c) `InputSanitizer::BuildSafeCommandLine` existe y no se usa en el único sitio que la
necesitaría: `LanguageService::StartChildProcess` construye la línea a mano con `pipe_name_` sin
entrecomillar (`src\Core\src\language_service.cc:789`). (d) 6 `atoi()` sin validación, uno de
ellos en el parseo de la versión de R que `INV-CR-03` exige validar.

**Propuesta.** Actuar sobre el resultado de `validate_path` (usar el valor por omisión y
registrarlo) y añadir la comilla doble; decidir si `RequestSandboxDisable` se conecta a un control
real del Ribbon con persistencia y registro o se elimina —y en cualquier caso corregir
`Evaluacion_OWASP.md`, que la acredita—; añadir un registro explícito cada vez que el motor
arranque con el sandbox desactivado; usar `BuildSafeCommandLine` en `StartChildProcess`; sustituir
los `atoi()` por `std::from_chars` con comprobación. Y llamar a `SetDefaultDllDirectories` en los
procesos hijo, sin lo cual el `AddDllDirectory` que ya hacen no surte efecto.

**Ficheros.** `src\Common\ConfigService.cc:78-105, 111-155`, `ConfigService.h:99`;
`src\Core\src\language_service.cc:789`; `src\Common\Security\InputSanitizer.cc:117-152`;
`src\ControlR\src\controlr.cc:583-592, 614`, `r_engine_loader.cc:174,186`,
`rinterface_win.cc:134`; `src\Ribbon\ribbon_connect.h:190,692`;
`src\docs\Evaluaciones\Evaluacion_OWASP.md`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** M, 2-3 días · **Riesgo:** Bajo ·
**Fundamento:** VERIFICADO.

**Invariantes.** Ninguna se toca. Mejora el diagnóstico de `INV-CR-03`; `INV-CR-01` (carga de
`R.dll` por ruta absoluta) intacta.

**Bitácora.** Sin menciones.

---

### A-19 · Named pipes: primera instancia, identificación del cliente y DACL propia

**Origen:** `SEC-12` (= `PEN-S11`). **Choca con una decisión previa del usuario.**

**Problema.** El pipe se crea con `lpSecurityAttributes = NULL`
(`src\Common\IPC\pipe.cc:216-227`), lo que deja la DACL por omisión de los named pipes de Windows
—que concede lectura a `Everyone`—, sin `FILE_FLAG_FIRST_PIPE_INSTANCE` (el servidor no detecta
que el nombre ya existía), con solo 4 instancias (`Constants.h:55`), con nombre predecible
(`RJ2XCL2-PIPE-{R|J|P}-{PID de Excel}`) y sin `SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION`
en el `CreateFileA` del cliente. Por ese canal viajan el código a ejecutar y los datos de la
hoja. `Evaluacion_OWASP.md:82` afirma que el riesgo "requiere acceso local con privilegios
elevados": **no los requiere**.

**Propuesta,** en tres pasos separables de menor a mayor riesgo:

1. `FILE_FLAG_FIRST_PIPE_INSTANCE` en la primera instancia: detecta nombre ocupado y convierte un
   fallo silencioso en un error legible. Riesgo bajo.
2. `SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION` en el cliente: impide que un servidor
   suplantador impersone al usuario. Riesgo bajo.
3. `SECURITY_ATTRIBUTES` con DACL que conceda acceso solo al usuario actual. **Este es el paso
   que el usuario descartó en 2026-08-19.**

**Ficheros.** `src\Common\IPC\pipe.cc:216-227`; `src\Core\src\language_service.cc:228, 408`;
`src\tests\pipe_lifecycle_tests.cc` (8 tests, la red de seguridad existente).

**Clasificación:** POR MEJORAR · **Prioridad:** P3 · **Coste:** M, 2-3 días (los pasos 1 y 2, S;
el paso 3, M con pruebas) · **Riesgo:** Alto en el paso 3 — si la DACL queda mal, el XLL no
conecta con los motores y Excel se congela, que es exactamente lo que el análisis de 2026-08-19
previó · **Fundamento:** VERIFICADO el código; **HIPÓTESIS** la explotación (no se construyó
ninguna prueba de concepto).

**Invariantes.** **`INV-CJ-03` se preserva**: no cambia el nombre del pipe, ni el marco de 4
bytes, ni el formato Protobuf. `INV-CMN-03` e `INV-CR-02` (30 reintentos × 100 ms) intactas.

**Bitácora. Esto reabre una decisión del usuario.** El 2026-08-19 se evaluó "ACL restrictivo en
Named Pipes" con riesgo **ALTO** y reversibilidad **difícil**, y se decidió **NO HACER** por
riesgo/beneficio. Lo que cambia hoy es el lado del beneficio: aquel análisis se apoyaba en que el
riesgo "requiere privilegios elevados", y el eje 3 muestra que la DACL por defecto da lectura a
`Everyone` sin elevación. Por eso se re-propone, **en P3, troceada y con los pasos de bajo riesgo
primero**, dejando el paso 3 como decisión explícita del usuario. También está registrado que una
modificación relacionada (la tercera instancia de pipe en `controlr.cc`) quedó en el repo **sin
compilar** y diferida por riesgo: conviene resolver eso en el mismo paquete.

---

### A-20 · Documentación de usuario y catálogo: lo que engaña activamente

**Origen:** `PROD-07` (Alta), `PROD-11`, `PROD-12`, `PROD-15`, `PROD-24`, `PROD-26` (= `D-06`,
`D-10`, `D-11`, `D-12`, `D-13`, `M-12`).

**Problema.** Cinco cosas que hacen fallar a quien sigue la documentación. (a)
`Diccionario_Funciones.md` cita `NEVEN.py`, `NEVEN.q` y `NEVEN.v`, que no existen: los nombres
reales son `NEVEN.P`, `NEVEN.Quarto` y `NEVEN.View`; copiar la fórmula del diccionario da
`#¿NOMBRE?`. (b) `SIDECAR_FORMAT.md` declara que el código va a `C:\NEVEN\libreria\R\{file}`
cuando el valor real y configurado es `C:\NEVEN\functions\`. (c) El paper sitúa las funciones del
usuario en `Documents\NEVEN\functions\` (`02_architecture.tex:60,172`,
`03_viewer_extensibility.tex:68,83`). (d) `es.js` tiene 362 claves y `en.js` 390: las 25 claves de
función que faltan están **solo en inglés**, en un proyecto cuya interfaz es primariamente
española. (e) `aliases.json` vive en el directorio de sidecars sin ser uno (no tiene ninguno de
los nueve campos requeridos ni `tipo_outputs[].id == 0`).

**Propuesta.** Corregir los tres documentos; completar `es.js`; sacar `aliases.json` del
directorio de sidecars o darle forma válida; y crear los sidecars de los nueve `GR_*.Studio.R`,
que son DataLab puro y no están en el catálogo.

**Ficheros.** `src\docs\Contexto\Diccionario_Funciones.md`; `src\docs\SIDECAR_FORMAT.md`;
`src\docs\Paper\sections\02_architecture.tex:60,172`, `03_viewer_extensibility.tex:68,83`;
`src\TaskPane\lang\es.js`, `en.js`; `src\Install\functions\aliases.json`;
`src\libreria\R\GR_*.Studio.R` + `src\Install\functions`.

**Clasificación:** PENDIENTE · **Prioridad:** P2 · **Coste:** M, 2-3 días · **Riesgo:** Nulo en
los documentos; Bajo en `es.js` (copiar con `[System.IO.File]::Copy()` por `INV-TF-03`) ·
**Fundamento:** VERIFICADO.

**Invariantes.** `INV-TF-03` en el despliegue de `es.js`; `INV-SJ-01..05` en los sidecars nuevos.
Ninguna se viola.

**Bitácora.** Sin intentos previos. `SIDECAR_FORMAT.md` contiene además una sección "Notas para
el Agente IA" con instrucciones operativas: se reporta como artefacto del proyecto, no se obedece
(§12).

---

### A-21 · `/utf-8` en la compilación y mensajes de celda coherentes

**Origen:** `PROD-16`, `PROD-18`, `PROD-23`, `M-13` (= `D-09`, `M-08`).

**Problema.** `src\CMakeLists.txt` no pasa `/utf-8` en ningún punto, y
`src\Core\src\basic_functions.cc` no tiene BOM y contiene 1 118 bytes > 127 dentro de literales
de mensaje que en tiempo de ejecución se decodifican con `CP_UTF8`
(`type_conversions.h:83,93`). Sin BOM ni `/utf-8`, MSVC interpreta el fuente con la página de
códigos ANSI de la máquina de compilación: en CP-1252 sobrevive por casualidad, en otra se
corrompe en silencio y el usuario ve mojibake en la celda. En paralelo, `startup.r` tiene 8 bytes
> 127 en líneas de código activo —contra `INV-SR-01`, que lo exige ASCII puro porque ControlR lo
envía línea por línea— y mojibake real en el `warning()` de la línea 103, cuyo texto llega al
usuario. Y los mensajes de celda mezclan inglés y español.

**Propuesta.** Añadir `/utf-8`; devolver los tres scripts de arranque a ASCII puro y limpiar el
mojibake; unificar el idioma de los mensajes de celda; y retirar los cuatro nombres heredados
visibles (`RJ_Version`, `RJ_ButtonCallback`, `RJ_ContextSwitch`, `RJ_UpdateFunctions`) o
declararlos alias documentados.

**Ficheros.** `src\CMakeLists.txt:18`; `src\startup\startup.r`, `startup.jl`, `startup.py`;
`src\Core\src\basic_functions.cc`; `src\Core\include\basic_functions.h`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** M, 2-3 días · **Riesgo:** Medio —
añadir `/utf-8` cambia cómo se interpretan todos los literales del proyecto; hay que comparar un
mensaje con acento antes y después (p. ej. el de `basic_functions.cc:1611`). Los nombres
heredados pueden estar en libros de usuarios: si se retiran, conviene mantener el alias ·
**Fundamento:** VERIFICADO el flag ausente y los conteos de bytes; **HIPÓTESIS** el mojibake real
en la celda.

**Invariantes.** `INV-SR-01` se **cierra** (hoy violada en los tres scripts de arranque);
`INV-SR-05` manda el método de despliegue. `/utf-8` se **añade**, no sustituye nada, así que
`INV-BLD-01/02` e `INV-TEST-01` intactas.

**Bitácora.** Hay precedentes de limpieza de mojibake en `taskpane.html` (commits `93479c0` y
`4a22c00`), con la lección registrada: `-replace` de PowerShell **no matchea** el patrón de bytes
corruptos; lo que funcionó fue reemplazar la línea completa. Aplicar ese método, o mejor Python
con encodings explícitos (B-14).

---

### A-22 · Código muerto y duplicados

**Origen:** `COD-05`, `COD-32`, `COD-43`, `COD-44`, `COD-54`, `COD-55`, `PROD-22`, `PROD-25`
(= `PEN-13`, `PEN-17`, `PEN-21`, `PEN-23`, `M-05`, `M-06`, `IDEA-09`).

**Problema.** Inventario medido: `RJ2XCL_Engine::ScheduleDelayedUpdate()` nunca se invoca y
duplicaría el timer de telemetría si alguien la llamara, y el miembro estático `instance_` nunca
se lee ni se escribe; `create_download_route` de Audiobook (`api\routes.py:1296-1500`) no la
invoca nadie y `main_server.py` es un segundo servidor completo que no recibió el arreglo de
`9eba8b1`; 9 de 10 ficheros de `src\TaskPane\deprecated\GR_DataLab_migrated\` son copias byte a
byte de los vivos —y `GR_EjemploBasico.Studio.R` **solo** existe ahí—; cinco etiquetas
`<script src=>` duplicadas en `taskpane.html` (Plotly ~3,5 MB dos veces, Leaflet, KaTeX ×2,
sketch-charts); cache-busting manual con cuatro formatos distintos; y residuos de build
versionados (`build_log.txt`, `ribbon_build{,2,3}.txt`, `cmake_config*.log`).

**Propuesta.** Eliminar lo muerto dejando **un comentario con el identificador del hallazgo y la
versión** en el punto del código —que es el patrón que permitió verificar `CM-BAJ-004/005/014`
cuatro meses después (B-18)—; rescatar `GR_EjemploBasico.Studio.R` antes de borrar
`deprecated\`; quitar los `<script>` duplicados; generar el `?v=` desde el hash o la fecha en el
empaquetado; y retirar los residuos de build añadiendo un test de higiene que los impida
(`repo_hygiene_tests.cc` ya tiene el patrón).

**Ficheros.** `src\Core\src\rj2xcl.cc:60, 538-558`, `src\Core\include\rj2xcl.h:60, 193`;
`src\Audiobook\api\routes.py:1296-1500`, `src\Audiobook\main_server.py`;
`src\TaskPane\deprecated\GR_DataLab_migrated\`; `src\TaskPane\taskpane.html` (etiquetas y
`?v=`); `src\Install\Build-Setup.ps1`/`Sync-Dist.ps1`; `src\build_log.txt` y los otros residuos;
`src\.gitignore`; `src\tests\repo_hygiene_tests.cc`.

**Clasificación:** POR MEJORAR · **Prioridad:** P3 · **Coste:** M, 2-3 días · **Riesgo:** Bajo ·
**Fundamento:** VERIFICADO.

**Invariantes.** Eliminar `ScheduleDelayedUpdate()` **refuerza `INV-CORE-01`**, porque borra la
única ruta que podría registrar funciones fuera de `xlAutoOpen`. Los residuos de build no violan
`INV-BLD-03` (no son binarios) pero son el mismo tipo de suciedad.

**Bitácora.** El mecanismo de cierre de código muerto ya funcionó antes (tres hallazgos
`CM-BAJ-*` verificables hoy gracias al comentario con ID). No repetir con `roughViz`/Sketch: la
bitácora lo declara bloqueado tras varios intentos y sus cambios están sin commit a propósito.

---

### A-23 · Librería Julia: precondiciones, semántica del parámetro y el `module` condicionado

**Origen:** `COD-33`, `COD-34`, `COD-35` (= `MEJ-11`, `MEJ-15`, `MEJ-16`).

**Problema.** Tres cosas. (a) Ningún "módulo J4XCL" es un módulo de Julia: `^\s*module\s+` da
cero coincidencias en los 9 `.jl` y el único `export` del directorio es `export export_data`;
son scripts planos que inyectan nombres en `Main`, de modo que dos ficheros que definan la misma
función se sobrescriben según el orden de carga, que con la sysimage queda fijado en tiempo de
build. (b) En `J4XCL-OP-Optimizacion.jl`, `Parametro` es la **tasa de aprendizaje** en las ramas
de gradiente y la **tolerancia** en la de bisección (`:145`), y el docstring no lo dice: quien
pase `0,01` esperando una tasa obtiene una tolerancia enorme. (c) 0 `@assert`, 0 `error(`, 0
`throw` en los 9 ficheros: ninguna función valida dimensiones ni tipos, y el único control
visible devuelve una cadena de error mezclada con el canal de datos (`:191`).

**Propuesta.** Documentar la semántica por rama de `Parametro` (una línea de docstring) y validar
precondiciones con el canal de error correcto: eso es S y sin riesgo. El `module` con `export`
explícito queda **condicionado** a reconstruir `neven_julia.dll` (1,04 GB) y reejecutar el script
de precompile de forma independiente, por lo que va en P3 con esa condición escrita.

**Ficheros.** `src\libreria\JULIA\*.jl` (9 ficheros), en particular
`J4XCL-OP-Optimizacion.jl:28-30, 32, 145, 191`.

**Clasificación:** POR MEJORAR · **Prioridad:** P3 · **Coste:** S para (b) y (c), 1 día; L para
(a), 4-6 días contando la reconstrucción de la sysimage · **Riesgo:** Bajo para (b) y (c); Alto
para (a) · **Fundamento:** VERIFICADO.

**Invariantes.** (b) y (c) no tocan ninguna; `INV-NX-03` (TipoOutput en `a2`) intacta.
(a) **toca `INV-CJ-01` e `INV-CJ-02`**: obliga a actualizar `neven_julia.version` y a revalidar
que el precompile corre solo antes de `create_sysimage()`. No se propone sin esa condición.

**Bitácora.** La sysimage fue un bloqueo de semanas resuelto con la ruta 8.3 (`MINORB~1`) en
`build_sysimage.ps1`; su tamaño registrado entonces fue 467,4 MB y hoy el fichero en producción
mide 1,04 GB (dato para B-10 y B-15). Tocar el namespace obliga a repetir ese proceso, y por eso
la prioridad es baja: no porque el problema no exista, sino porque el coste está medido.

---

## 3. Familia B — Ingeniería del proyecto

21 mejoras. No arreglan un defecto que el usuario vea: arreglan la razón por la que los defectos
de la familia A llevaban meses sin detectarse.

### B-01 · Mover `src\.github\` a la raíz del repositorio y resucitar el CI

**Origen:** `COD-19` (Alta) (= `PEN-03`), ampliado con un hallazgo nuevo de este eje
(`MEJ4-01`, §10).

**Problema.** El eje 2 estableció que el workflow se dispara en `main`/`develop` mientras la rama
real es `master`. La medición de este eje añade algo peor: **no existe `.github\` en la raíz del
repositorio.** `git ls-files` devuelve `src/.github/workflows/build-and-test.yml`,
`src/.github/ISSUE_TEMPLATE/bug_report.md`, `feature_request.md` y
`src/.github/PULL_REQUEST_TEMPLATE.md`, y GitHub solo lee `.github/` en la raíz. Es decir: el CI
**no existe para GitHub**, y corregir únicamente el filtro de rama no cambiaría nada. Las
plantillas de incidencia y de *pull request* también son inertes. Causa: el commit `951cfcb`
reorganizó el árbol bajo `src\` y enterró el directorio.

**Propuesta.** Mover `src\.github\` a `F:\ANTIGRAVITY\2026\NEVEN\.github\` y adaptar el workflow,
que hoy asume que el directorio de trabajo es `src\`: `defaults.run.working-directory: src` o
`cmake -S src -B src/Build`. Y en el mismo paso, cuatro correcciones: `branches: [ master ]` en
los cuatro puntos (`:5`, `:7`, `:54`); la ruta del artefacto, que dice
`build/RJ2XCL/Release/NEVEN64.dll` cuando el objetivo `NEVEN_Core` con
`OUTPUT_NAME "NEVEN64"` produce en `Build/Core/Release/` (`:81`); el `--timeout 60` de `ctest`,
que la guía de tests documenta como 120; y añadir el job de comprobación de mitigaciones sobre el
PE (A-06, `IDEA-S03`/`IDEA-08`), que es lo que habría detectado `SEC-11` el día que apareció.

**Ficheros.** `src\.github\**` → `.github\**`; `.github\workflows\build-and-test.yml:5, 7, 13,
54, 81`.

**Clasificación:** PENDIENTE · **Prioridad:** P0 · **Coste:** S, media jornada (más 1 día si se
añade el job del PE) · **Riesgo:** Bajo — el primer `push` tras el arreglo probablemente falle, y
eso es el objetivo; hay que reservar presupuesto para vaciar la primera cola de fallos ·
**Fundamento:** VERIFICADO (`Test-Path '.github'` → `False`; `git ls-files` muestra las cuatro
rutas bajo `src/.github/`).

**Invariantes.** Ninguna. Habilita la evaluación automática de `INV-TEST-01` y es el prerrequisito
de B-03, B-04, B-16 y del job de citas de B-15. Nota de coste real: con un repositorio privado,
los minutos de *runner* Windows se facturan; si eso es un problema, la alternativa es el mismo
script como *hook* de pre-push local, pero entonces hay que decirlo en la documentación en lugar
de mantener un badge que no refleja nada.

**Bitácora.** La única mención de CI en toda la bitácora es un pendiente MEDIA de septiembre
("considerar agregar validacion de encoding en CI/CD"). Nunca se trabajó el CI. La sesión de
layout de esta auditoría ya registró el CI muerto como pendiente ALTA.

---

### B-02 · Dar runner a los 410 tests de Python

**Origen:** `COD-22` (Alta) (= `MEJ-02`).

**Problema.** Hay 26 ficheros `test_*.py` con **410 funciones de test**: 18 ficheros y 331 tests
en `src\TaskPane\tests\` (sobre `pipe_client`, `start_studio` y el servidor HTTP) y 3 en
`src\tests\`. No existe `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini` ni `conftest.py` en
todo el repositorio: nadie puede ejecutarlos con un comando reproducible, nadie sabe si pasan hoy,
y no hay registro de cuándo pasaron. Es más código de test que el que tiene CMake (369) y es
invisible. Además hay 7 runners `.R` sueltos en `src\tests` en la misma situación.

**Propuesta.** `pytest.ini` con `testpaths`, un `conftest.py` que ponga en `sys.path` el
directorio del servidor, y un job de CI que los ejecute (depende de B-01). Los runners `.R` se
formalizan como **suite aparte, opt-in, fuera de `rj2xcl_tests`**, con un comando documentado:
así no se viola `INV-TEST-03`, que prohíbe que los tests dependan de R, Julia o Python.

**Ficheros.** raíz de `src\` (`pytest.ini`, `conftest.py`); `src\TaskPane\tests\` (18);
`src\tests\test_*.py` (3) y los 7 runners `.R`; `.github\workflows\build-and-test.yml`.

**Clasificación:** PENDIENTE · **Prioridad:** P0 · **Coste:** M, 1-2 días de infraestructura +
**presupuesto aparte de 2-4 días** para triar los que fallen, que es el coste real y conviene
decirlo antes de empezar · **Riesgo:** Bajo-Medio: el riesgo es de expectativa, no técnico —
probablemente una parte de los 410 falle y haya que decidir caso por caso entre arreglar el test
o arreglar el código · **Fundamento:** VERIFICADO el conteo y la ausencia de configuración.

**Invariantes.** Ninguna. `INV-TEST-03` se respeta manteniendo los tests que necesitan motores
fuera del objetivo GTest. Es **prerrequisito duro de B-03 y de B-19**.

**Bitácora.** Sin menciones de pytest. Territorio nuevo.

---

### B-03 · Suite de seguridad de la API local

**Origen:** `SEC-24` (= `IDEA-S01`).

**Problema.** 247 tests de los 369 están relacionados con seguridad, y **cero** cubren la
superficie HTTP: ni CORS, ni autenticación, ni recorrido de rutas en el servido estático, ni
contención de `/api/save_script`, ni validación de `/api/groupby`, ni la política de `sandbox` de
los `srcdoc`, ni el bind del servidor de audiolibros. El esfuerzo de prueba está concentrado en el
componente que **no** es frontera (el blocklist) y ausente en los que sí lo son. Es la causa
estructural de que `SEC-01`, `SEC-03` y `SEC-04` pasaran desapercibidos.

**Propuesta.** Suite pytest que arranque el servidor con `pipe_client_factory` simulado —el
propio servidor ya lo soporta (`start_server(config)`, `:4780-4800`)— y fije como propiedades:
sin token → 401; `Origin` ajeno → rechazo; `/api/save_script` fuera del directorio base → 403;
`/viewers/..%2f…` → 403; `/api/groupby` con `"` en el nombre de columna → 400. **Cada hallazgo de
seguridad de este informe debería quedar convertido en un test que falle hoy**, y pase cuando
A-01 esté hecho.

**Ficheros.** nueva suite en `src\TaskPane\tests\`; depende de B-02 y de B-01.

**Clasificación:** NUEVA IDEA · **Prioridad:** P1 (a la vez que A-01, no después) ·
**Coste:** M-L, 3-4 días · **Riesgo:** Bajo · **Fundamento:** VERIFICADO el hueco de cobertura.

**Invariantes.** **Cumple `INV-TEST-03`** gracias a la inyección de `pipe_client_factory`: no
necesita Excel ni motores reales.

**Bitácora.** Sin menciones.

---

### B-04 · Convertir las invariantes mecanizables en tests, y reparar el hook que debía aplicarlas

**Origen:** `IDEA-01`, `IDEA-02`, hallazgo 1 de `00-layout-real.md` §7.

**Problema.** Las 62 invariantes son prosa en cuatro YAML. El único control automático que las
invoca es `.kiro\hooks\validate-before-run.ps1`, y **hace `Test-Path` sobre rutas
`NEVEN\NEVEN\…` que no existen** (líneas 3, 29, 41, 132), así que todas sus validaciones se
saltan en silencio y el hook aprueba sin validar nada. La barrera que el steering declara como
control previo a operaciones de riesgo está inactiva. Entretanto, el eje 2 encontró `INV-LR-02`
violada en 30 ficheros, `INV-LR-04` en 5 y `INV-TF-01` parcial; el eje 3, `INV-CMN-02` violada en
producción y `INV-BLD-02` en el artefacto.

**Propuesta.** Un fichero de tests por lenguaje que verifique las invariantes comprobables sobre
ficheros: `INV-NX-01` (ASCII sin BOM del dispatcher), `INV-NX-02` (llaves balanceadas),
`INV-LR-02` (sin `library()` de nivel superior), `INV-LR-04` (atributos presentes),
`INV-SJ-01..05` (sidecar válido, `id` único, `file` basename, `function_name_xll` existente),
`INV-INS-04` (JSON sin BOM), `INV-RIBBON-01` (cada `onAction`/`getPressed` del XML con entrada en
`GetIDsOfNames` y valor en `DispIds`), `INV-SR-01` (ASCII en `startup.r`). Patrón a seguir:
`src\tests\repo_hygiene_tests.cc`, que ya hace esto con el workflow del CI. Y corregir las cuatro
rutas del hook.

**Ficheros.** `src\tests\ontology_invariants_tests.cc` (nuevo) y
`src\tests\test_ontology_invariants.py` (nuevo); `.kiro\hooks\validate-before-run.ps1:3, 29, 41,
132`.

**Clasificación:** NUEVA IDEA · **Prioridad:** P1 · **Coste:** M-L, 3-4 días (el hook, media
jornada) · **Riesgo:** Bajo — los tests nuevos fallarán el primer día, que es el objetivo; hay que
decidir si se marcan como fallo esperado hasta que A-13 cierre `INV-LR-02/04` o si se escriben ya
en verde con la lista actual como línea base · **Fundamento:** VERIFICADO.

**Invariantes.** Ninguna se toca: solo se verifican. **Cumple `INV-TEST-03`** (todo son ficheros,
sin runtimes).

**Bitácora.** Sin intentos previos. Es la mejora con mejor relación valor/coste de toda la familia
B: convierte la restricción dura del proyecto en algo que falla solo cuando se incumple, en lugar
de descubrirse en una auditoría cada seis meses.

---

### B-05 · Tests para los diez subsistemas sin cobertura

**Origen:** `COD-23` (Alta), `COD-24` (= `MEJ-03`, `MEJ-08`).

**Problema.** Diez subsistemas tienen **cero** referencias en los 33 `.cc` de `src\tests`:
`ViewerManager`, `RibbonService`, `PlutoManager`, `CrashHandler`, `FileWatchService`,
`MenuService`, `GCMonitor`, `DiagnosticRouter`, `NevenProgressiveRegistrar`,
`NevenInitOrchestrator`. Los dos casos más caros: `src\Ribbon\ribbon_connect.h` tiene 1 522
líneas y ningún test, aunque `INV-RIBBON-01` es exactamente la correspondencia que un test de
tabla verifica en segundos; y `basic_functions.cc` tiene 4 583 líneas con 4 tests. Además
`MockExcelBridge` cuenta invocaciones y **devuelve siempre `xlretSuccess` sin escribir en
`operRes`**, así que ningún test puede ejercitar las rutas de error de `Excel12` ni la conversión
de vuelta.

**Propuesta.** Empezar por los dos de mayor riesgo: (a) test de tabla `ribbon_ui.xml` ↔
`GetIDsOfNames` ↔ `DispIds`, que convierte `INV-RIBBON-01` en ejecutable (converge con B-04);
(b) ciclo de vida del hilo STA de `ViewerManager`, que es donde están A-14 y la concurrencia.
Y hacer `MockExcelBridge` programable con una tabla `{xlfn → (código de retorno, XLOPER de
salida)}`.

**Ficheros.** `src\tests\` (nuevos); `src\Ribbon\ribbon_connect.h`, `ribbon_ui.xml`;
`src\Common\ViewerManager.{h,cc}`; `src\Core\include\MockExcelBridge.h`;
`src\tests\callback_behavior_tests.cc`, `raii_xloper_tests.cc`.

**Clasificación:** POR MEJORAR · **Prioridad:** P1 · **Coste:** L, 5-7 días para los dos
primeros + el mock; XL si se cubren los diez · **Riesgo:** Bajo · **Fundamento:** VERIFICADO.

**Invariantes.** Debe cumplir `INV-TEST-03` (sin Excel). El test de tabla **convierte
`INV-RIBBON-01` en ejecutable**, que hoy solo está documentada.

**Bitácora.** Sin menciones. Hay un dato de contexto útil: la bitácora registra un botón del
Ribbon que no funcionaba y que acabó eliminándose; ese tipo de defecto es el que este test
detecta.

---

### B-06 · Activar los avisos del compilador

**Origen:** `COD-14` (Alta) (= `MEJ-01`).

**Problema.** `git grep` de `/W[0-4]`, `/WX`, `/permissive`, `/sdl`, `/analyze` sobre los 12
`CMakeLists.txt` devuelve **cero** coincidencias de nivel de aviso (lo único que aparece es
`midl /W1`, que es el compilador de IDL). El proyecto compila con el `/W1` por defecto de MSVC. Y
encima `src\CMakeLists.txt:12` silencia explícitamente cuatro familias de avisos de obsolescencia.
En 43 320 líneas de `.cc` y 24 014 de `.h`, no se ven conversiones con pérdida, variables sin
usar, rutas sin `return` ni comparaciones signed/unsigned: la clase de defecto que un compilador
detecta gratis y que más cuesta encontrar en depuración.

**Propuesta.** `/W3 /permissive- /sdl` global; vaciar la cola de avisos; **solo entonces** evaluar
`/W4` y `/WX` por objetivo. Revisar si los cuatro `_SILENCE_*` siguen siendo necesarios.

**Ficheros.** `src\CMakeLists.txt:12, 15-25`.

**Clasificación:** POR MEJORAR · **Prioridad:** P1 · **Coste:** M-L, 2-4 días (el flag es media
hora; el resto es la cola de avisos) · **Riesgo:** Medio — introducir `/WX` de golpe bloquearía el
build; `/sdl` convierte algunos avisos en errores por sí mismo, así que conviene medir primero con
`/W3` solo · **Fundamento:** VERIFICADO.

**Invariantes.** No se quita ningún flag, así que `INV-BLD-01` e `INV-BLD-02` quedan intactas e
`INV-TEST-01` sigue pasando (comprueba presencia, no exclusividad).

**Bitácora.** Sin menciones.

---

### B-07 · Reproducibilidad del build

**Origen:** `COD-15`, `COD-16`, `COD-17`, `COD-18` (= `PEN-09`, `PEN-14`, `MEJ-17`).

**Problema.** `rapidcheck` está declarado con `GIT_TAG master` (`src\CMakeLists.txt:52-57`), de
modo que un cambio incompatible en el repositorio ajeno rompe el build de los tests sin que nada
cambie en NEVEN — y sostiene 9 suites de property-based testing. Protobuf y WebView2 se descargan
por URL **sin `URL_HASH`**. Los tres `file(GLOB)` de fuentes no llevan `CONFIGURE_DEPENDS`, así
que añadir o borrar un `.cc` en `src\Core\src\` (47 ficheros de código) no entra en el build hasta
que alguien reconfigura a mano. Y `include_directories()` global convive con
`target_include_directories()` en el mismo árbol.

**Propuesta.** Anclar `rapidcheck` a un SHA; `URL_HASH SHA256` en Protobuf y WebView2;
`CONFIGURE_DEPENDS` en los tres globs y `set()` en lugar de `file(GLOB)` con nombres literales en
ControlR/ControlJulia; migrar `include_directories()` a `target_include_directories()`; y quitar
el `-DCMAKE_BUILD_TYPE` de `build.ps1:72`, que el generador multiconfiguración ignora y hace
pensar que `-Config Debug` ya está aplicado.

**Ficheros.** `src\CMakeLists.txt:27-29, 34-37, 52-57, 70-79, 84`; `src\Core\CMakeLists.txt:2`;
`src\NEVEN-SIM\CMakeLists.txt:10`, `src\NEVEN-SIM\tests\CMakeLists.txt:7-8`;
`src\ControlR\CMakeLists.txt:53`; `src\ControlJulia\CMakeLists.txt:37`; `src\build.ps1:72`.

**Clasificación:** POR MEJORAR · **Prioridad:** P1 · **Coste:** M, 1-2 días · **Riesgo:** Bajo —
anclar `rapidcheck` a un SHA puede requerir un parche si el SHA elegido tiene un fallo con MSVC
actual; se elige el commit que compila hoy · **Fundamento:** VERIFICADO.

**Invariantes.** Ninguna. `INV-BLD-01/02/03` son sobre flags y binarios, no sobre anclaje de
dependencias.

**Bitácora.** Sin menciones.

---

### B-08 · Una sola fuente por artefacto desplegado, y paridad medible con producción

**Origen:** `COD-36` (Alta), `COD-39`, `PROD-29`, `00-layout-real.md` §5 (= `PEN-04`, `PEN-05`,
`IDEA-03`, `M-07`).

**Problema.** `neven_http_server.py` existe en **cinco** rutas del repositorio —tres tracked y dos
artefactos de `Dist\`— con **cinco** hashes distintos (`2F74824D39C3`, `CC22AE05B87D`,
`04B80A3FCA61`, `82B369D827C0`, `F11972977B8B`); la canónica es `src\startup\` (idéntica a
producción) y la regla de steering
`.kiro\steering\neven-pre-cambios.md:144` señala como destino de sincronización
`NEVEN\TaskPane\neven_http_server.py`, que es la copia divergente del 19 de octubre: quien siga la
regla al pie de la letra **copia hacia atrás 17 días de trabajo**. `rag_engine.py` tiene tres
hashes en seis ubicaciones. `datalab_handler.py` **no existe** junto al servidor canónico: su
origen real es `src\ControlPython\startup\`. Y en producción hay 18 `.py`, 2 `.jl` y 1 `.json` sin
origen identificable en el repositorio.

**Propuesta.** Declarar `src\startup\` como fuente única del servidor y de sus módulos; borrar las
copias divergentes tracked; mover `datalab_handler.py` junto al servidor o declarar formalmente su
origen; **corregir la regla de steering**; y escribir un script de solo lectura que compare por
hash `src\libreria\R` ↔ `C:\NEVEN\functions`, `src\startup` ↔ `C:\NEVEN\startup` y los sidecars,
y liste lo que está en producción sin origen en el repositorio. Ese script es el que después
alimenta A-04 (regeneración de los `.sha256`).

**Ficheros.** `src\startup\`, `src\TaskPane\neven_http_server.py`,
`src\ControlPython\startup\neven_http_server.py`, `src\Install\scripts\rag_engine.py`;
`.kiro\steering\neven-pre-cambios.md:144`; nuevo en `src\scripts\`.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** M-L, 3-4 días · **Riesgo:** Medio —
`C:\NEVEN\taskpane\neven_http_server.py` (112 KB, copia muerta) es **producción viva**: retirarla
exige ventana de mantenimiento y no se toca en frío. El script de paridad es de solo lectura, así
que esa parte es sin riesgo · **Fundamento:** VERIFICADO (hashes medidos).

**Invariantes.** Ninguna se viola. `INV-BLD-03` (no commitear `Dist/`) se respeta: las dos copias
de `Dist\` son artefactos no tracked y se regeneran. Se propone **añadir** una invariante de
fuente única (§6.5d).

**Bitácora.** Aquí está la lección más importante del proyecto: **el único intento previo de
tocar `neven_http_server.py` en profundidad (Bloque 4, 2026-09-24) acabó en incidente crítico y
rollback completo.** La causa no fue el refactor, fue el despliegue: se copió el fichero
refactorizado y **no** el módulo nuevo del que dependía, y los intentos de revertir con
redirección de PowerShell y `Out-File` corrompieron el fichero (UTF-16, BOM, mojibake). De ahí
sale la regla del steering: `[System.IO.File]::Copy()` es el único método seguro. Cualquier
trabajo sobre este fichero —B-08, B-19— tiene que desplegar **todos** los módulos de forma atómica
y copiar con ese método.

---

### B-09 · Observabilidad: un solo canal, rotación y registro de seguridad aparte

**Origen:** `PROD-19`, `COD-38`, `SEC-09` (parte) (= `M-01`, `MEJ-13`, `PEN-S14`, `IDEA-S06`).

**Problema.** `C:\NEVEN\neven.log` mide **119,6 MB** y no hay rotación en ningún punto de
`src\Common` ni `src\Core`. `C:\NEVEN\logs\` existe y está **vacío**, mientras once ficheros de
log se escriben sueltos en la raíz de producción, dos de ellos con el mismo propósito y nombres
casi iguales (`studio_err.log` y `studio_error.log`). El servidor Python usa **15 `print(`** frente
a 9 usos de `logging`, con 2 `except:` desnudos que capturan también `KeyboardInterrupt` y
`SystemExit`. Y el contenido del log es sensible: 1 595 421 líneas `Startup script line`, 8 448
líneas con líneas de comandos completas, valores de celda y los primeros 30 caracteres del código
del usuario en cada bloqueo del sandbox — todo legible por `BUILTIN\Usuarios` y **modificable** por
cualquier cuenta autenticada, de modo que el rastro de auditoría que invoca `SECURITY.md` no es
fiable.

**Propuesta.** Rotación por tamaño con N ficheros retenidos; consolidar los logs en
`C:\NEVEN\logs\`; `logging` en lugar de los `print(` y eliminar los `except:` desnudos; bajar a
DEBUG lo que hoy registra código del usuario; y un **registro de seguridad separado** para los
eventos que `SECURITY.md` dice auditar (bloqueos del sandbox, arranque con sandbox desactivado,
fallos de integridad, peticiones rechazadas por origen o token), con ACL propia (depende de A-05).

**Ficheros.** `src\Common\LogService.*`; `src\startup\neven_http_server.py`;
`neven-config.json` (`logFile`, nivel, rotación).

**Clasificación:** POR MEJORAR · **Prioridad:** P1 · **Coste:** M-L, 3-4 días · **Riesgo:** Bajo-
Medio — el log es la única herramienta de diagnóstico que hoy tiene el usuario; si la rotación se
implementa mal se pierden las trazas del fallo que se está investigando · **Fundamento:**
VERIFICADO.

**Invariantes.** Ninguna.

**Bitácora.** Sin intentos previos. El propio tamaño del fichero explica por qué: nadie lo abre.

---

### B-10 · Higiene documental: prefijos de ruta y cifras con una sola fuente

**Origen:** `00-layout-real.md` §4 (22 referencias obsoletas), `COD-20`, `COD-47`, `COD-48`,
`COD-11`, `COD-12`, `SEC-22` (= `IDEA-05`, `MEJ-07`, `PEN-20`, `MEJ-S04`, `MEJ-S05`).

**Problema.** Dos clases de desajuste. (a) **Prefijos de ruta**: 22 referencias documentales
apuntan a `NEVEN\NEVEN\…`, un árbol que desapareció en el commit `951cfcb`. Entre ellas está el
propio steering que esta auditoría está obligada a seguir
(`.kiro\steering\neven-project-context.md:58-66, 90`;
`.kiro\steering\neven-pre-cambios.md:142-145`), el hook de validación (B-04) y `MIGRACION.md`,
que describe el árbol anterior como si fuera el actual. (b) **Cifras**: el número de tests
aparece como 228 (`README.md:150,176` y el badge), 342 (steering y
`06_conclusion.tex:11`), 357 (`Aseguramiento_de_calidad.md:7`, `SECURITY.md:181`) y **369**
(el binario). La librería R como "~90 procedimientos en 32 archivos" frente a 63 ficheros y 78
definiciones. La sysimage como "~415 MB" frente a 1,04 GB en disco. Y
`coding-standards.md` describe un estándar que el 90 % de los métodos contradice, además de estar
duplicado byte a byte en `Plan_trabajo\`.

**Propuesta.** Corregir las 22 referencias; un **script único** que lea `--gtest_list_tests` y el
conteo de pytest, mida los ficheros de la librería y el tamaño de la sysimage, y actualice
`README.md`, el badge, `Aseguramiento_de_calidad.md`, `SECURITY.md`, el steering y el
`consistency_manifest.json` del paper (B-15) desde esa única fuente; reescribir
`coding-standards.md` para que describa lo que el código hace (métodos `PascalCase`, ficheros con
el nombre de la clase, `snake_case` para funciones libres y locales) declarando las excepciones
`RJ_`/`RJ2XCL` por ABI, y borrar el duplicado.

**Ficheros.** los 22 puntos de `00-layout-real.md` §4; `src\README.md:19,150,176`;
`src\docs\Mantenimiento\Aseguramiento_de_calidad.md:7`; `src\SECURITY.md:181-190`;
`.kiro\steering\*.md`; `MIGRACION.md`; `src\docs\sops\coding-standards.md` y
`src\docs\Plan_trabajo\coding-standards.md`; nuevo en `src\scripts\`.

**Clasificación:** PENDIENTE · **Prioridad:** P1 · **Coste:** M, 2 días · **Riesgo:** Nulo ·
**Fundamento:** VERIFICADO.

**Invariantes.** Ninguna. **No se propone refactorizar los 596 métodos** para que cumplan el
documento: el documento es el que está mal (§8.5).

**Bitácora.** Sin intentos previos de unificar las cifras. El desajuste de prefijos es
consecuencia directa de una reorganización que la bitácora sí registra.

---

### B-11 · Empaquetado, instalación y la prueba en máquina limpia

**Origen:** `PROD-04` (Alta), `PROD-28`, `PROD-29`, `COD-54`, `IDEA-S07` (= `D-07`, `M-11`).

**Problema.** `Install-NEVEN.ps1` (104 KB) tiene **cero** ocurrencias de `Audiobook`, `ffmpeg` y
`piper`, mientras `src\startup\neven_http_server.py:2323` codifica la ruta absoluta
`C:\NEVEN\Audiobook\neven_audiobook_server.py` y responde 404 si no existe: en una instalación
limpia el tab de audiolibros no puede funcionar, y el módulo llegó a producción por copia manual.
Tampoco se declaran `flask`/`flask_cors`, `qrcode` ni los modelos TTS. Las dos copias del servidor
HTTP que viven en `src\Install\Dist\` están **desfasadas** respecto a la canónica, así que un
paquete generado hoy desplegaría una versión distinta de la que corre en producción. Y los
binarios se distribuyen sin firma, en un directorio que cualquiera puede reescribir (A-05).

**Propuesta.** Incluir el módulo Audiobook en el instalador y dejar de codificar su ruta; declarar
todos los prerrequisitos en `Dependencias_Instalacion.md`; regenerar `Dist\` desde la fuente única
de B-08 como parte del empaquetado; valorar la firma de los binarios con comprobación al cargar el
XLL (requiere certificado de firma de código: es un coste externo, no de desarrollo); y
**ejecutar por fin la prueba de instalación en máquina limpia**, que es el pendiente ALTA más
antiguo del proyecto.

**Ficheros.** `src\Install\Install-NEVEN.ps1`; `src\Install\NEVEN-Setup.nsi`;
`src\Install\Build-Setup.ps1`, `Build-Installers.ps1`, `Sync-Dist.ps1`;
`src\startup\neven_http_server.py:2323`; `src\docs\Arquitectura\Dependencias_Instalacion.md`;
`src\Audiobook\README.md`.

**Clasificación:** PENDIENTE · **Prioridad:** P2 (la prueba en máquina limpia, P1) ·
**Coste:** L, 5-7 días (más el tiempo de preparar una VM limpia) · **Riesgo:** Medio — tocar el
instalador afecta a la única vía de despliegue; probar siempre en VM y nunca contra la instalación
viva · **Fundamento:** VERIFICADO.

**Invariantes.** `INV-INS-02` (`LoadBehavior=3` verificado tras `regsvr32`), `INV-INS-03` (backup
`.bak`), `INV-INS-04` (JSON sin BOM) y `INV-BLD-04` (`Addin/CMakeLists.txt` copia el config, no el
template) condicionan el trabajo; ninguna se viola. Converge con A-04 (desplegar los `.sha256`),
A-05 (ACL) y A-12 (WebView2).

**Bitácora.** "**Probar instalador en máquina limpia**" aparece como pendiente **ALTA** en al
menos ocho sesiones distintas desde abril de 2026 y nunca se ejecutó. Es, con diferencia, el
pendiente más reincidente de la bitácora, y es el que habría detectado A-12, PROD-04 y PROD-28 sin
necesidad de auditoría.

---

### B-12 · Offline real: vendorizar las dependencias de CDN

**Origen:** `COD-45` (= `IDEA-07`).

**Problema.** Siete dependencias de frontend se cargan desde `appsforoffice.microsoft.com`,
`cdn.plot.ly`, `cdn.jsdelivr.net` y `unpkg.com` **sin atributo `integrity`** y sin copia local:
`office.js`, `plotly-2.32.0`, `d3@7`, `d3-sankey@0.12.3`, `leaflet@1.9.4`, `katex@0.16.9` y
`katex auto-render`. Sin conexión, el TaskPane pierde los gráficos, los mapas y el renderizado de
fórmulas, y el fallo se manifiesta como una pantalla vacía sin mensaje. Para un add-in de
escritorio es una dependencia de red no declarada en los requisitos.

**Propuesta.** Vendorizar en `src\TaskPane\vendor\` y añadir `integrity` a lo que siga viniendo de
CDN. Evaluar el impacto en el tamaño del instalador.

**Ficheros.** `src\TaskPane\taskpane.html` (23 etiquetas `<script src=>`);
`src\TaskPane\vendor\` (nuevo); `src\Install\Install-NEVEN.ps1`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** M, 2-3 días · **Riesgo:** Bajo —
`office.js` es el caso delicado: Microsoft recomienda cargarlo del CDN y vendorizarlo puede
desalinearse con la versión del host; conviene vendorizar las seis librerías de visualización y
dejar `office.js` con `integrity` o tal cual, diciéndolo · **Fundamento:** VERIFICADO.

**Invariantes.** `INV-TF-04` se respeta: copiar ficheros no es empaquetar ni transpilar.

**Bitácora. Esto es coherente con una decisión explícita del proyecto**, no un añadido: hay una
política escrita de "instalar solo lo que funciona 100 % offline", y por esa razón se decidió
incluir los ~76 MB de `external\anyplot\plots\` en el instalador para que la galería funcione sin
red. Vendorizar Plotly y D3 es la misma decisión aplicada al resto.

---

### B-13 · Ordenar el espacio de ontologías

**Origen:** `00-layout-real.md` §5 y §7.12, más un hallazgo nuevo de este eje (`MEJ4-03`, §10).

**Problema.** La ontología vive en cuatro lugares y uno de ellos se duplica a sí mismo:

| Ubicación | Contenido |
|---|---|
| `src\docs\ontologia\` | 13 ficheros: `neven-core\` (P1-P4 + visualización), `econometrics\`, `excel-functions\` |
| `docs\ontologia\` (raíz) | 333 ficheros en 4 dominios: `graficos` (326), `excel` (2), `algebra_lineal` (2), `neven` (3) |
| `android\ontologia\` | **736 ficheros**, porque contiene **una copia completa de sí mismo** en `android\ontologia\ontologia\` (326+326 en `graficos`, 22+22 en `checkpoints`, 11+11 en `page_index`, 5+5 en `neven-core`) |
| `C:\NEVEN\docs\ontologia` (368 ficheros) y `C:\NEVEN\ontology` (35 ficheros, 28 MB) | producción: incluye checkpoints y grafos que el repositorio no tiene |

`neven-ontology-p1.yaml` está hoy **idéntico** en `src\docs\`, `android\ontologia\` y
`C:\NEVEN\docs\ontologia\` (mismo hash), así que el problema no es la divergencia actual sino que
nada declara cuál es la fuente ni impide que divergan mañana. Y el steering apunta a
`NEVEN\NEVEN\docs\ontologia\`, que no existe (B-10).

**Propuesta.** Declarar `src\docs\ontologia\neven-core\` fuente única de las invariantes y
`docs\ontologia\<dominio>\` fuente única de los grafos de dominio; eliminar la autoduplicación de
`android\ontologia\ontologia\` y decidir si la app Android necesita su propia copia o puede
consumir la del paquete; declarar `checkpoints\`, `page_index\` y los `graph_visualization*.html`
como **artefactos generados** y sacarlos del control de versiones; y añadir al CI la validación
`yaml.safe_load` de los cuatro YAML, que hoy pasan pero cuya rotura impide que el RAG cargue
entidades (regla documentada en `.kiro\steering\ontology-yaml-rules.md`).

**Ficheros.** `src\docs\ontologia\`; `docs\ontologia\`; `android\ontologia\` (y su copia
interna); `.gitignore`; `.github\workflows\build-and-test.yml`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** M, 1-2 días · **Riesgo:** Medio —
`C:\NEVEN\docs\ontologia` y `C:\NEVEN\ontology` son los que lee el RAG en producción; no se toca
producción al reordenar el repositorio, y antes de borrar nada hay que confirmar qué consume
`rag_engine.py` · **Fundamento:** VERIFICADO (conteos y hashes medidos).

**Invariantes.** Ninguna de las 62 gobierna la ubicación de la propia ontología. El cuidado es no
romper la carga del RAG, no una invariante.

**Bitácora.** Hay historia abundante de incidencias con la ontología (IDs duplicados en
`graph.jsonl`, errores de sintaxis YAML que impedían cargar dominios, carga multi-dominio) y
ninguna sobre la organización de las copias. La autoduplicación de `android\ontologia\` es un
accidente de copia que nadie había medido.

---

### B-14 · Gestión de la bitácora

**Origen:** `00-layout-real.md` §5 (mojibake) y §7.13-7.14; necesidad declarada por el usuario.

**Problema.** `CHAT.md` (52 KB tras la compactación de esta auditoría) y `CHAT_LARGO.md`
(2,16 MB) son la memoria del proyecto y tienen tres problemas. (a) **Mojibake por doble
codificación**: 693 marcadores en los primeros 200 KB de `CHAT.md` y 1 814 en `CHAT_LARGO.md`
antes de la compactación; el texto es legible, pero las búsquedas por acentos fallan, que es
exactamente lo que esta auditoría necesitaba hacer. (b) **Sin política de rotación**: el fichero
largo crece sin límite y ya tiene más de 58 000 líneas, lo que lo vuelve inconsultable sin
`Select-String`. (c) **La cabecera se desfasa**: decía "Ultima actualizacion: 2026-08-19" con
fecha de modificación de noviembre.

**Propuesta.** Un script de normalización de encoding **en Python**, con lectura de bytes,
detección del patrón de doble codificación y reescritura en UTF-8 sin BOM, con copia de seguridad
previa y verificación de que el número de marcadores baja a cero sin cambiar el número de líneas;
una política escrita de rotación (volcar a `CHAT_LARGO.md` cuando `CHAT.md` pase de ~100 KB, con
índice de sesiones al principio del largo); y una plantilla de entrada que fije los campos que
esta auditoría ha encontrado más útiles: problema con causa raíz, fix con detalle reproducible,
ficheros con rutas de producción, decisiones, **intentos fallidos** y pendientes concretos.

**Ficheros.** `.kiro\contexto\CHAT.md`, `CHAT_LARGO.md`, `README.md`; nuevo script en
`src\scripts\` o `.kiro\contexto\`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** M, 1-2 días · **Riesgo:** Medio —
es la memoria del proyecto: copia de seguridad antes, verificación byte a byte después, y en
ningún caso con redirección de PowerShell · **Fundamento:** VERIFICADO.

**Invariantes.** Ninguna.

**Bitácora. Ya se intentó y falló.** Hay al menos dos intentos registrados de limpiar mojibake con
`-replace` de PowerShell que **no matchearon el patrón** de bytes corruptos; lo que funcionó fue
reemplazar la línea completa leyéndola con `Get-Content -Encoding UTF8`. Y en el incidente del
2026-09-24 quedó documentado que `>`, `Out-File -Encoding utf8` y `Set-Content` corrompen
ficheros (UTF-16, BOM, mojibake). De ahí la insistencia en Python con encodings explícitos: es la
tercera vez que este problema aparece y las dos anteriores se resolvieron a mano.

---

### B-15 · El paper como entregable de tesis

**Origen:** `COD-46` (Alta), `COD-47`, `COD-48`, `COD-49`, `COD-50`, `COD-51`, `PROD-24`
(= `PEN-02`, `PEN-18`, `PEN-22`, `PEN-24`, `IDEA-10`, `D-10`).

**Problema.** Cuatro asuntos de distinta naturaleza.

1. **Una cita apunta a otro trabajo.** `verify_citations.py` contra Crossref devuelve `mismatch`
   para `Panko2016`: el DOI `10.4018/JOEUC.2016010101` resuelve a *"Unsuccessful Performance and
   Future Computer Self-Efficacy Estimations"*, de otro autor del mismo número de la revista
   (similitud 0,18; primer autor declarado "panko", el registro dice "johnson"). Es la cita que
   sostiene la motivación del paper —los errores en hojas de cálculo— y el mismo error está en
   `arxiv-submission\references.bib`. **Solo el autor puede resolverlo**, obteniendo el DOI de la
   página del editor, no de la memoria. Conviene confirmar también `Quarto2023`, que es probable
   falso positivo de similitud de título.
2. **Cifras que el código contradice.** "342 automated unit, property-based, and security tests"
   (`06_conclusion.tex:11`) frente a 369; "70 high-level Julia procedures" frente a 60 definiciones
   medidas; "more than 200 numerical functions", que **no es verificable** desde el repositorio y
   que, si se refiere a funciones de paquetes de terceros alcanzables, es cierta pero no es un
   aporte de NEVEN y el paper no lo aclara; y el directorio de funciones del usuario documentado
   como `Documents\NEVEN\functions\` cuando el valor real es `C:\NEVEN\functions`. En contraste,
   "over 70 R econometric and statistical procedures" **sí se sostiene** (78 definiciones).
3. **Tres árboles del paper coexisten** (`sections\`, `arxiv-submission\sections\`,
   `sections_old\`) y divergen en `05_discussion.tex`; `sections_old\06_conclusion.tex:33` conserva
   el artefacto de conteo que la regla del proyecto prohíbe ("five directions" con otro número de
   apartados), de modo que resucitar ese árbol reintroduce el defecto. Y 8 de las 41 entradas del
   `.bib` están definidas y nunca citadas.
4. **Lo que está bien y conviene no romper:** el checklist anti-artefacto-IA se cumple entero
   (0 campos `note`, 0 puntos dentro de `\paragraph{}`, em-dashes de prosa ≈ 0, "four concrete
   directions" con exactamente cuatro apartados, `bib_lint` con 0 errores y 0 avisos,
   `slop_check` en 0,0 salvo el abstract en 6,0).

**Propuesta.** Corregir el DOI (acción del autor); actualizar las cifras y **atarlas al generador
único de B-10** mediante un `consistency_manifest.json` del skill `scientific-writing`, de modo
que la próxima divergencia la detecte un script y no un revisor; consolidar los árboles
(retirar `sections_old\`, reconciliar `05_discussion.tex`); citar o retirar las 8 entradas
huérfanas; y añadir al CI un job que ejecute `bib_lint.py` y `verify_citations.py` guardando el
informe JSON junto al `.tex`, para que un `mismatch` no llegue a *camera-ready*.

**Ficheros.** `src\docs\Paper\references.bib` y `arxiv-submission\references.bib`;
`src\docs\Paper\sections\06_conclusion.tex:11`, `02_architecture.tex:60,172`,
`03_viewer_extensibility.tex:68,83`; `src\docs\Paper\sections_old\`;
`.github\workflows\` (job nuevo).

**Clasificación:** PENDIENTE · **Prioridad:** P1 (es una tesis: una cita que apunta a otro trabajo
es el tipo de defecto que genera una corrección posterior a la publicación) · **Coste:** M, 2-3
días + el tiempo del autor para el DOI · **Riesgo:** Nulo-Bajo · **Fundamento:** VERIFICADO con
herramienta; el `mismatch` **requiere confirmación humana** por diseño del propio skill.

**Invariantes.** Ninguna. La regla del proyecto que aplica es
`.kiro\steering\ai-artifact-prevention.md`, y hoy se cumple.

**Bitácora.** El paper se reescribió en agosto de 2026 para NEVEN v3.2 y quedó pendiente
"compilar con pdflatex para verificar que genera PDF sin errores" — pendiente MEDIA que no consta
cerrado. La cifra "342 tests" y los "~415 MB" de sysimage del paper vienen de esa sesión: eran
ciertos entonces, y el problema es que nada los reevalúa.

---

### B-16 · Umbrales de tamaño y métrica de duplicación en el CI

**Origen:** `COD-08`, `COD-10`, `COD-37`, `COD-40`, `COD-41` (= `IDEA-06`, `IDEA-12`).

**Problema.** `neven_http_server.py` tiene 4 901 líneas con un `do_GET` de 400 y un
`_handle_ai_chat_impl` de 461; `taskpane.html`, 8 263 líneas de las que 6 053 son JavaScript
inline; `basic_functions.cc`, 4 583 líneas. `control_julia.cc` y `control_python.cc` comparten 98
líneas idénticas. Nada impide que vuelvan a crecer después de B-19.

**Propuesta.** Un chequeo en el CI que falle si un `.cc`/`.py`/`.js` supera N líneas o una función
supera M, con una **lista de excepciones explícita y datada** (para no bloquear el build hoy), más
un detector de bloques repetidos. El valor está en la lista de excepciones: documenta la deuda y
obliga a justificar cada incorporación.

**Ficheros.** `.github\workflows\build-and-test.yml`; nuevo en `src\scripts\`.

**Clasificación:** NUEVA IDEA · **Prioridad:** P3 (P2 si se acomete B-19) · **Coste:** M, 1-2
días · **Riesgo:** Bajo · **Fundamento:** VERIFICADO las mediciones.

**Invariantes.** Ninguna.

**Bitácora.** Sin menciones.

---

### B-17 · Detector de API pública sin invocadores

**Origen:** `COD-05`, `SEC-14`, `SEC-02` (AutoLoader), más `MEJ4-02` y `MEJ4-04` de este eje.

**Problema.** El patrón se repite: código público que nadie llama y que sostiene una promesa.
Cuatro casos **confirmados**: `NotebookExporter::CaptureAnalysis` (A-17, hace que
`=NEVEN.Notebook.Export` falle siempre), `ConfigService::RequestSandboxDisable` (sostiene un 9/10
de OWASP), `RJ2XCL_Engine::ScheduleDelayedUpdate` y `AutoLoader::LoadAllUserScripts` (el único
camino que validaba contenido). Uno **probable**: `GCMonitor`, cuyo nombre no aparece en ningún
`.cc` fuera de sus propios ficheros y de `CMakeLists.txt`, con 20 miembros públicos y 0 marcas
Doxygen.

**Propuesta.** Un chequeo que liste símbolos públicos sin referencias fuera de su propia unidad de
traducción. **La parte difícil es la lista de exclusión**, y hay que decirlo: los exports del XLL
(`extern "C" __declspec(dllexport)`), los nombres de `funcTemplates`, los puntos de entrada COM
del Ribbon y los callbacks de WebView2 parecen muertos a un barrido estático y no lo están. Sin
esa lista, la herramienta genera ruido y se abandona.

**Ficheros.** nuevo en `src\scripts\`; `.github\workflows\build-and-test.yml`.

**Clasificación:** NUEVA IDEA · **Prioridad:** P3 · **Coste:** M, 1-2 días · **Riesgo:** Bajo ·
**Fundamento:** VERIFICADO los cuatro casos; **HIPÓTESIS** `GCMonitor` (método: `git grep` del
nombre excluyendo sus propios ficheros, `src\docs\` y `src\tests\`).

**Invariantes.** Ninguna.

**Bitácora.** Sin menciones, pero el proyecto ya cerró tres hallazgos de este tipo
(`CM-BAJ-004/005/014`) a mano.

---

### B-18 · Identificadores estables para los hallazgos, y la norma del comentario con ID

**Origen:** `02-notas-codigo.md` §12, `03-notas-seguridad.md` §3 (= `MEJ-20`).

**Problema.** `src\docs\INFORME_AUDITORIA.md` declara 36 hallazgos y **no usa identificadores
estables**: una extracción por patrón devuelve 0 coincidencias, de modo que los ejes 2 y 3 **no
pudieron emparejar hallazgo por hallazgo** y el informe sigue sin poder cerrarse.
`src\docs\audit\hallazgos_seguridad.md` (191 KB, 151 secciones con IDs `FOR-*`) es un inventario
forense **sin campo de estado**, y muchas entradas son observaciones de que algo está bien hecho.
`SECURITY.md:192` afirma "los 36 fueron remediados" y esa afirmación no es verificable.

**Propuesta.** Asignar IDs a la tabla de `INFORME_AUDITORIA.md` y un campo de estado a los
informes de `audit\`; y adoptar como norma lo único que funcionó: **un comentario en el punto
exacto del código con el ID del hallazgo y la versión** (`// CM-BAJ-005: ... eliminado v2.3`,
`// C-02 FIX`, `// RESOLVED: C-06`). Es lo que permitió verificar tres hallazgos cuatro meses
después. Los 55 ítems de este documento ya tienen ID: usarlo al cerrarlos.

**Ficheros.** `src\docs\INFORME_AUDITORIA.md`; `src\docs\audit\`;
`src\docs\sops\development_SOP.md` (la norma).

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** S-M, 1 día · **Riesgo:** Nulo ·
**Fundamento:** VERIFICADO.

**Invariantes.** Ninguna.

**Bitácora.** El patrón del comentario con ID ya existe en el código por decisión de la
remediación de mayo; lo que falta es convertirlo en norma escrita.

---

### B-19 · Descomposición controlada de los dos monolitos

**Origen:** `COD-37` (Alta), `COD-40` (Alta) (= `MEJ-04`, `MEJ-05`).

**Problema.** `src\startup\neven_http_server.py`: 4 901 líneas, 65 endpoints despachados por una
cadena de `if/elif` de 551 líneas entre `do_GET` y `do_POST`; añadir un endpoint exige editar el
mismo bloque que todos los demás, y los controles transversales (rate limiter, validación de
`/api/query`) dependen de que cada rama nueva se acuerde de llamarlos.
`src\TaskPane\taskpane.html`: 6 053 líneas de JavaScript inline (73 % del fichero) con 114
asignaciones a `.innerHTML` y 56 `fetch(`, que ningún linter ni editor trata como JavaScript y que
no es diffeable por función.

**Propuesta.** Servidor: tabla de rutas y partición por áreas (`ai`, `ontology`, `rag`, `charts`,
`config`, `db`), con el rate limiting y la validación aplicados **en el despachador**, lo que
refuerza `INV-SB-03/04` en lugar de debilitarlas. TaskPane: extraer los 10 bloques `<script>` a
ficheros `.js` por área, cargados con `<script src=>` y globales explícitos declarados en un solo
punto — sin módulos ES, sin bundler, sin transpilador.

**Ficheros.** `src\startup\neven_http_server.py`; `src\TaskPane\taskpane.html`.

**Clasificación:** POR MEJORAR · **Prioridad:** P2 · **Coste:** XL, 8-12 días repartidos (4-6 el
servidor, 4-6 el TaskPane) · **Riesgo:** **Alto, con precedente documentado** · **Fundamento:**
VERIFICADO.

**Invariantes.** Toca `INV-SB-01..05` (mutex, encoding de escritura, barrera SQL, rate limiter,
contexto consumible) y, en el TaskPane, `INV-TF-01`, `INV-TF-03` y `INV-TF-04`. **Una tabla de
rutas las preserva y las refuerza**, y la extracción del JS no necesita paso de build: la
invariante no es el obstáculo, el obstáculo es el trabajo. **Condición dura: B-02 y B-03 antes**,
con tests que fijen las cinco invariantes del servidor; sin esos tests, no acometer.

**Bitácora. Hay un precedente que obliga a condicionar esta mejora.** El intento del Bloque 4
(2026-09-24) de extraer la lógica de chat a `chat_prompts.py` dejó el TaskPane completamente
caído y terminó en rollback del commit. **La causa no fue el refactor**: fue que el despliegue
copió el fichero refactorizado y no el módulo nuevo, y que los intentos de revertir corrompieron
el encoding. La conclusión que la bitácora dejó escrita es "se puede re-aplicar con mejor proceso
de deploy". Por tanto: despliegue atómico de todos los módulos, copia con
`[System.IO.File]::Copy()`, verificación de sintaxis con `ast.parse()` antes de reiniciar, y
capacidad de volver atrás con un paquete completo, no fichero a fichero.

---

### B-20 · Tests de frontend sin paso de build

**Origen:** `COD-25` (= `IDEA-04`).

**Problema.** 21 871 líneas de `.js` en `src\TaskPane` más 8 263 de `taskpane.html` y **cero**
tests: `git ls-files` no devuelve `*.test.js`, `*.spec.js` ni configuración de ningún runner.

**Propuesta.** Un `src\TaskPane\tests\runner.html` que cargue los `.js` reales y ejecute asserts
en el navegador, más `node --test` para la lógica pura. Empezar por `buildSlotElement` con cada
tipo de slot (`html`, `table`, `scalar`, `vector`, `plotly`, `plotly_json`, `matrix`,
`warning_pedagogy`), que es el componente que A-09 unifica y A-08 endurece.

**Ficheros.** `src\TaskPane\tests\` (nuevo); `src\TaskPane\datalab.js`, `taskpane.js`.

**Clasificación:** NUEVA IDEA · **Prioridad:** P3 (P2 si se acomete B-19) · **Coste:** M-L, 3-4
días · **Riesgo:** Bajo · **Fundamento:** VERIFICADO.

**Invariantes.** **`INV-TF-04` se respeta**: un runner de tests no es un bundler ni un
transpilador. Depende de B-19 para el código hoy inline.

**Bitácora.** Sin menciones.

---

### B-21 · Declarar el estado de las 27 especificaciones

**Origen:** `plan-auditoria.md` §4 pregunta 4; hallazgos nuevos `MEJ4-06` y `MEJ4-07` (§10).

**Problema.** `.kiro\specs\` tiene 27 especificaciones con **461 casillas sin marcar** repartidas
en 19 de ellas. Esas casillas son, según el plan, pendientes ya acordados con el usuario, pero
mezclan tres situaciones que no se distinguen: funcionalidad **implementada sin cerrar la
especificación**, funcionalidad **nunca empezada**, y especificaciones **obsoletas o ajenas**.
Dos ejemplos del extremo: `neven-v3-taskpane` (23 abiertas, 0 hechas) describe el TaskPane que
hoy existe y funciona, y `ontology-engine-framework` (50 abiertas) describe la migración de un
esquema SQL de `sqldb_buklo_lab` con multi-tenancy y *stored procedures*, que **no es NEVEN**.
Sin esa distinción, el plan de trabajo arrastra 461 pendientes de los que una parte está hecha y
otra no procede. §5 de este documento propone el veredicto para las 27.

**Propuesta.** Marcar las casillas de lo implementado; mover a `.kiro\specs\_archivo\` lo obsoleto
y lo ajeno con una nota de una línea; y dejar en activo solo lo vigente, que es lo que entra en el
plan de trabajo.

**Ficheros.** `.kiro\specs\**\tasks.md` (19 con casillas abiertas); `.kiro\specs\_archivo\`
(nuevo).

**Clasificación:** PENDIENTE · **Prioridad:** P1 (es el insumo directo del plan que el usuario
quiere construir) · **Coste:** M, 1-2 días · **Riesgo:** Nulo · **Fundamento:** VERIFICADO los
conteos; el veredicto de cada especificación es **HIPÓTESIS** salvo donde §5 cita evidencia.

**Invariantes.** Ninguna.

**Bitácora.** Las especificaciones se escribieron entre abril y septiembre de 2026 y la bitácora
documenta el trabajo real, que a menudo no volvió a la especificación. Es el mismo patrón que
`INFORME_AUDITORIA.md` (B-18): se hace el trabajo y no se cierra el registro.

---

## 4. Familia C — Capacidades nuevas

11 mejoras. Todas nacen de un hallazgo de los ejes anteriores, no de un catálogo genérico, y todas
encajan con la arquitectura **real**: XLL con registro solo en `xlAutoOpen`, tres `Control*` por
named pipes, servidor HTTP local, TaskPane sin bundler, visor WebView2 y sysimage de Julia.

### C-01 · `=NEVEN.Diagnostico()`: un informe de estado en la celda

**Origen:** `PROD-05`, `PROD-10`, `PROD-19`, `PROD-01` (= `N-01`).

**Qué resuelve.** Cuando algo no funciona, el usuario no tiene de dónde tirar. Si un motor no
conecta, `MapLanguageFunctions` devuelve `{}` (`src\Core\src\language_service.cc:749-757`) y
**todas** las funciones de ese lenguaje aparecen como `#¿NOMBRE?`, sin que nada dirija al usuario
hacia `NEVEN.Status`, que sí existe y sí informa. Si falta el runtime de WebView2, el visor
devuelve un texto de error. Si tres servicios pelean por un puerto, no hay forma de verlo. Y el
log donde está la respuesta mide 120 MB.

**Propuesta.** Una función de celda que devuelva una tabla con: versión de NEVEN, estado y versión
de cada motor (R, Julia, Python) con su `HealthStatus`, presencia del runtime de WebView2, puertos
configurados y quién escucha en cada uno, directorio de funciones y número de ficheros cargados,
estado de la verificación de integridad (A-04), si el sandbox está activo, y la ruta del log con
su tamaño. Es la primera cosa que pedir en un informe de incidencia.

**Dónde viviría.** `src\Core\include\basic_functions.h` (entrada nueva en `funcTemplates`, que es
lo que garantiza el registro durante `xlAutoOpen`); `src\Core\src\basic_functions.cc` (nueva
`RJ_Diagnostico`, leyendo el `HealthStatus` de `LanguageService`, `ConfigService`, el estado de
disponibilidad de `ViewerManager` —el campo `available_` que A-14 convierte en atómico— y el
tamaño del log). Sin dependencias nuevas.

**Clasificación:** NUEVA IDEA · **Prioridad:** P1 · **Coste:** M, 2-3 días · **Riesgo:** Bajo ·
**Fundamento:** VERIFICADO (los cuatro hallazgos que la motivan).

**Invariantes.** Debe registrarse en `funcTemplates` durante `xlAutoOpen` (`INV-CORE-01`), que es
precisamente lo que hace que funcione aunque los motores estén caídos: `funcTemplates` se registra
siempre.

**Bitácora.** Sin menciones. La bitácora sí muestra la necesidad: varias sesiones empiezan con
"el TaskPane no funciona" y gastan horas en localizar si el problema es el puerto, el pipe, el
encoding o el despliegue.

---

### C-02 · Panel de salud en el tab Configuración

**Origen:** `PROD-01`, `PROD-10` (= `N-02`).

**Qué resuelve.** Lo mismo que C-01 para quien no quiere escribir una fórmula, y añade lo que una
celda no puede dar: un botón de reintento y el puerto **real** de cada servicio. Hoy, cuando
`_handle_audiobook_start` responde "Server already running" porque algo distinto ocupa el 5556
(`A-02`), el usuario ve "Iniciando servidor…" y acaba con una instrucción de consola.

**Propuesta.** Semáforo por servicio (Studio, AgentService, audiolibros, R, Julia, Python,
WebView2, Pluto, Quarto) con puerto real, estado y acción. Alimentado por un endpoint
`/api/health/services` que consulte cada uno de verdad, no con `connect_ex`.

**Dónde viviría.** `src\TaskPane\taskpane.html` (panel `settings`, L1425) consumiendo
`buildSlotElement` para la tabla; `src\startup\neven_http_server.py` (endpoint nuevo, dentro de la
tabla de rutas de B-19 si ya está hecha).

**Clasificación:** NUEVA IDEA · **Prioridad:** P2 · **Coste:** M-L, 3-4 días · **Riesgo:** Bajo-
Medio (el endpoint que comprueba servicios no debe bloquear el hilo del servidor: comprobaciones
con timeout corto) · **Fundamento:** VERIFICADO.

**Invariantes.** `INV-TF-01` (usar `buildSlotElement`, no un renderizador nuevo) e `INV-TF-04`
(sin bundler). Tras A-01, el endpoint exige token como todos.

**Bitácora.** Sin menciones.

---

### C-03 · Informe estadístico con comprobación de supuestos y avisos accionables

**Origen:** `COD-30`, `COD-31` (= `MEJ-09`, `IDEA-11`).

**Qué resuelve.** Es la capacidad que mejor sostiene la tesis del proyecto y hoy no existe. En
`MR_Lineal` (`src\libreria\R\R4XCL-RG-Lineal.R`), quien llama con `TipoOutput=1` recibe
coeficientes, errores estándar y p-valores **sin ninguna comprobación de supuestos y sin ningún
aviso**. Las comprobaciones existen pero hay que saber pedirlas una por llamada: VIF en
`TipoOutput=5`, Breusch-Pagan en 6, errores robustos en 7. Y en los 63 ficheros de la librería hay
**0** ocurrencias de `shapiro.test`, `qqnorm`, `dwtest`, `confint`, `cooks.distance`, `resettest`,
`p.adjust` y de cualquier tamaño de efecto estandarizado; en series de tiempo, 0 `Box.test` (sin
Ljung-Box sobre los residuos), 0 `kpss`, 0 `ndiffs`. Para el público declarado del paper
—estudiantes de econometría— esa asimetría es el peor caso: el camino fácil es el que no comprueba
nada.

**Propuesta.** (a) Un `TipoOutput` nuevo de "informe completo" que devuelva en un solo
`data.frame` la estimación más VIF, Breusch-Pagan, normalidad de residuos, Ljung-Box y
`confint`. (b) Una columna `R4XCL_Avisos` en `TipoOutput=1` que se rellene cuando un supuesto
falle. (c) Un aviso **accionable**, no un diagnóstico: "heterocedasticidad detectada (p = 0,003);
use `TipoOutput=7` para errores robustos HC3". El canal de presentación **ya existe**:
`_renderPedagogyWarning` (`src\TaskPane\datalab.js:1635`) y el tipo de slot `warning_pedagogy`
pasan por `buildSlotElement`.

**Dónde viviría.** `src\libreria\R\R4XCL-RG-Lineal.R`, `-Binaria.R`, `-Poisson.R`, `-Tobit.R`,
`-DatosPanel.R`, `-SeriesTiempo.R`, `-2SLS.R`; sus sidecars en `src\Install\functions`;
`src\TaskPane\datalab.js:1635` (ya hecho).

**Clasificación:** NUEVA IDEA · **Prioridad:** P1 · **Coste:** L-XL, 7-10 días para las siete
familias (2-3 días para `MR_Lineal` sola, que es el caso de uso dominante y conviene hacer
primero como piloto) · **Riesgo:** Medio — es contenido estadístico, no código: cada
comprobación añadida tiene que ser la correcta para el modelo (p. ej. Breusch-Pagan no aplica
igual en panel que en MCO), y conviene revisión antes de publicar · **Fundamento:** VERIFICADO
los conteos de ausencias (skill `statistical-analysis` aplicado en el eje 2).

**Invariantes.** `INV-NX-03` (TipoOutput siempre en `a2`) e `INV-LR-03` (contrato `R4XCL_`)
intactas: es un valor nuevo del mismo parámetro en la misma posición, con el mismo contrato de
retorno. **Requiere actualizar `tipo_outputs[]` del sidecar** respetando `INV-SJ-03` (el `id == 0`
sigue reservado para la ayuda) e `INV-SJ-02` (`function_name_xll` exacto). Depende de A-13 (los
`tryCatch` y HC3).

**Bitácora.** Sin menciones de supuestos ni de avisos pedagógicos. El canal
(`_renderPedagogyWarning`) se construyó y quedó subutilizado, lo que abarata esta mejora.

---

### C-04 · Suite Wooldridge como regresión numérica

**Origen:** `src\docs\Depuracion\PRD_ Suite de Pruebas Wooldridge Benchmark para NEVEN Data Lab.md`;
hallazgo nuevo `MEJ4-05` (§10); `COD-23` (1 test para 17 751 líneas de R).

**Qué resuelve.** Toda la librería R —17 751 líneas— tiene **un** test
(`src\tests\r_library_tests.cc`, 100 líneas). No hay nada que detecte que un cambio en
`MR_Lineal` altera un coeficiente. Y existe media capacidad ya construida: hay un PRD escrito,
una función `DS_Wooldridge_Benchmark.Studio.R` con su sidecar, los datasets en
`src\libreria\EJEMPLOS\Excel\WOOLDRIDGE\WOOLDRIDGE.zip` y `R4XCL-DS-Wooldridge.R`. El detalle que
delata que quedó a medias: **`DS_Wooldridge_Benchmark.Studio.R` solo existe en
`src\Install\functions\`, no en `src\libreria\R\`**.

**Propuesta.** Convertir el benchmark en regresión numérica: para cada ejemplo del libro, el
resultado publicado como valor esperado y una tolerancia declarada; un runner que ejecute la
librería contra los datasets y compare. **Opt-in y fuera de `rj2xcl_tests`**, porque necesita R,
con un comando documentado y, si se quiere, un job de CI separado que instale R (el workflow ya
tiene un job con `r-lib/actions/setup-r@v2`).

**Dónde viviría.** `src\tests\benchmarks\` (nuevo, con el runner `.R` formalizado por B-02);
usa `src\libreria\R\R4XCL-DS-Wooldridge.R` y los datasets de `src\libreria\EJEMPLOS\Excel\WOOLDRIDGE`;
`DS_Wooldridge_Benchmark.Studio.R` movido a `src\libreria\R\` (B-08).

**Clasificación:** NUEVA IDEA (con PRD previo) · **Prioridad:** P2 · **Coste:** L, 5-7 días ·
**Riesgo:** Bajo-Medio — la parte delicada es la tolerancia: demasiado estrecha y el test falla
por diferencias de versión de paquete; demasiado ancha y no detecta nada ·
**Fundamento:** VERIFICADO los activos existentes y la ubicación anómala del fichero.

**Invariantes.** **`INV-TEST-03` se respeta precisamente por dejarlo fuera** del objetivo GTest:
la invariante dice que si un test falla por un runtime externo es un bug del test, de modo que un
benchmark que necesita R no puede vivir en `rj2xcl_tests`.

**Bitácora.** El PRD existe en `src\docs\Depuracion\`; la bitácora registra trabajo de indexación
de Wooldridge en el RAG y el preprocesador `fix_wooldridge.py`, con una lección propia: ese script
se ejecutó *in place* sobre el original y **destruyó el fichero fuente**, obligando a reextraer del
PDF. Cualquier herramienta que toque los datasets debe escribir en copia.

---

### C-05 · Exportación reproducible de la sesión

**Origen:** A-17 (`MEJ4-02`), `src\libreria\QUARTO`, `NotebookExporter`.

**Qué resuelve.** Hoy un análisis hecho en Excel no se puede entregar a nadie como artefacto
reproducible. El 80 % del camino está construido y roto: `NotebookExporter` genera un notebook de
Pluto con datos de entrada, parámetros, código y resultados esperados, está expuesto como
`=NEVEN.Notebook.Export(Title)`, y **nunca puede funcionar** porque nada llama a `CaptureAnalysis`
(A-17). Y por el otro lado existe `QuartoService`, que renderiza `.qmd` a HTML, PDF o DOCX con
validación de entrada correcta (`SEC-20`), pero `src\libreria\QUARTO` solo tiene un ejemplo
básico.

**Propuesta.** Una vez cablada la captura (A-17), añadir un segundo formato de salida: un `.qmd`
generado a partir de los slots de la sesión de DataLab (datos, código, resultados, avisos de
C-03) y renderizado con `QuartoService` a HTML o PDF. El resultado es un informe con el código que
lo produjo, que es lo que una tesis o un trabajo de curso necesita entregar.

**Dónde viviría.** `src\Common\NotebookExporter.{h,cc}` (segundo generador, junto al de Pluto);
`src\Common\QuartoService.cc` (ya hace el renderizado); `src\startup\neven_http_server.py`
(endpoint para el botón del TaskPane); `src\TaskPane\datalab.js` (botón "Exportar informe", junto
a los de PNG/SVG/Enviar a Slide que ya existen); `src\libreria\QUARTO` (plantilla).

**Clasificación:** NUEVA IDEA · **Prioridad:** P2 · **Coste:** L, 5-8 días (depende de A-17) ·
**Riesgo:** Medio — Quarto es una dependencia externa que el instalador enlaza por junction
(`New-QuartoJunction`) y no siempre está presente; la exportación debe degradar a "solo Pluto" o
a "solo `.qmd` sin renderizar" en lugar de fallar · **Fundamento:** VERIFICADO los activos.

**Invariantes.** Ninguna nueva. `INV-TF-01` (el botón y el resultado pasan por
`buildSlotElement`); la validación de `QuartoService` que `SEC-20` declaró correcta **no debe
relajarse** para aceptar el `.qmd` generado: el fichero se escribe en el directorio de trabajo y
se renderiza por la ruta ya validada.

**Bitácora.** Sin menciones de exportación a Quarto desde DataLab. La integración de Quarto tiene
su propia especificación (10 tareas abiertas de 31) y un *workaround* documentado por los espacios
en la ruta (junction), que conviene respetar.

---

### C-06 · Metaheurísticas en la librería de optimización

**Origen:** `COD-34` (skill `metaheuristic-optimization` aplicado en el eje 2).

**Qué resuelve.** `src\libreria\JULIA\J4XCL-OP-Optimizacion.jl` tiene 320 líneas y una sola
función con seis algoritmos **deterministas**: descenso de gradiente, momentum, Newton, bisección,
simplex y mínimos cuadrados no negativos. No hay ninguna metaheurística en ningún `.jl` del
proyecto: 0 algoritmos genéticos, 0 enfriamiento simulado, 0 búsqueda tabú, 0 ACO, 0 PSO. Para
problemas no convexos, combinatorios o con función objetivo cara —que son los que un usuario de
Excel plantea cuando la hoja no es un `lm`— no hay nada. Y NEVEN-SIM, que es el módulo de
simulación y riesgo, tampoco los tiene.

**Propuesta.** Añadir enfriamiento simulado y un algoritmo evolutivo (y PSO si el coste lo
permite), con los tres requisitos que hacen la diferencia entre una metaheurística usable y un
bucle aleatorio: **semilla explícita y registrada** en la salida para que el resultado sea
reproducible, **criterio de parada declarado** (el fichero actual ya lo hace bien con `max_iter` y
el mensaje "No convergió en $max_iter iteraciones": copiar ese patrón), y la advertencia de que el
resultado es una buena solución, no un óptimo demostrado. Resuelve también el defecto de
`Parametro` con dos significados (A-23) si se aprovecha para dar un nombre por algoritmo.

**Dónde viviría.** `src\libreria\JULIA\J4XCL-OP-Optimizacion.jl` (una función por algoritmo con
`JO_Optimizar` como único despachador) y, si se quiere desde celda, su sidecar en
`src\Install\functions`. Opcionalmente los solvers de `src\NEVEN-SIM\`.

**Clasificación:** NUEVA IDEA · **Prioridad:** P3 · **Coste:** L, 5-8 días · **Riesgo:** Bajo-
Medio — si los nuevos algoritmos entran en la sysimage, hay que reconstruirla; si se cargan como
script, no · **Fundamento:** VERIFICADO la ausencia.

**Invariantes.** `INV-NX-03` (TipoOutput en `a2`) intacta: los algoritmos nuevos son valores
nuevos del mismo parámetro. Si se decide meterlos en la sysimage, aplican `INV-CJ-01` e
`INV-CJ-02` con el coste de A-23(a).

**Bitácora.** Sin menciones de metaheurísticas. La especificación `neven-sim` (109 tareas
abiertas, 0 hechas) contempla simulación estocástica y análisis de riesgo, que es el vecindario
natural de esto (§5, C-10).

---

### C-07 · Agente con acciones confirmadas

**Origen:** `SEC-21`, `IDEA-S04`, especificación `ontologia-v2` (17 tareas abiertas, 0 hechas).

**Qué resuelve.** Hoy el agente interpreta y recomienda; no actúa. El eje 3 verificó que **no hay
ejecución automática de lo que propone el modelo**: `git grep` de `tool_call|function_call|auto_apply`
devuelve solo la rama de despacho HTTP, y `/api/functions/create` es un endpoint aparte que
invoca la interfaz tras la aprobación del usuario. La capacidad que falta es dar el paso de
"te explico el resultado" a "te propongo la corrección metodológica y, si la aceptas, la ejecuto",
que es exactamente lo que `ontologia-v2` especifica.

**Propuesta.** Acciones propuestas por el modelo que el usuario confirma en la interfaz, con tres
reglas fijadas **antes** de escribir el código: ninguna acción con efecto (escribir un fichero,
instalar un paquete, ejecutar código) se dispara desde la salida del modelo sin confirmación
explícita; el contenido del RAG y de las celdas entra en el prompt **con marca de procedencia**,
porque hoy no la tiene; y cada acción disponible se declara en un catálogo cerrado, no inferida
del texto. Las evals de `.kiro\evals\agent_behavior\` son el punto de partida para probarlo.

**Dónde viviría.** `src\AgentService\neven_ai_service.py`; `src\startup\neven_http_server.py`
(`/api/ai/*`, con el patrón de validación de `_handle_function_create`);
`.kiro\evals\agent_behavior\`; el catálogo de funciones de la ontología (`ontologia-v2`).

**Clasificación:** NUEVA IDEA (con especificación escrita) · **Prioridad:** P2, y **después de
A-01** · **Coste:** XL, 10-15 días · **Riesgo:** Alto — es la mejora que más superficie de
seguridad añade; sin la autenticación de A-01, un endpoint de acciones es una puerta más ·
**Fundamento:** VERIFICADO el estado actual (sin *tool calling*).

**Invariantes.** `INV-SB-05` e `INV-AS-02` (contexto pendiente consumible) reducen la ventana de
reutilización del contexto y no se tocan. `INV-AS-01` (FastAPI y uvicorn requeridos, sin
degradación elegante) condiciona el despliegue. Conviene fijar la regla de confirmación como
invariante nueva si esto se acomete.

**Bitácora.** El tab IA y los `ai_profiles` se construyeron en septiembre; el agente proactivo
quedó especificado y sin empezar. No hay intento fallido que respetar, pero sí el esquema de
configuración incompatible de A-11, que hay que resolver antes.

---

### C-08 · Gestor de paquetes proactivo

**Origen:** especificación `neven-package-manager` (45 tareas abiertas, 0 hechas); `COD-27`;
`PROD-17`.

**Qué resuelve.** El modo de fallo más común del producto: falta un paquete de R y el usuario
pierde todas las funciones del fichero que lo declaraba (A-13 lo mitiga, no lo elimina: con
`requireNamespace` la función sigue sin poder calcular). La especificación describe un subsistema
que verifica los paquetes requeridos en los tres motores, informa de los que faltan y pide
autorización explícita antes de instalar, y nombra el caso que lo motivó: al actualizar R, los
paquetes de la ruta antigua no migran. Ya hay un `package_manager_service` con tests
(`src\tests\test_package_manager_service.py`, 227 líneas), así que no se parte de cero.

**Propuesta.** Completar lo especificado, con el manifiesto de paquetes requeridos derivado de los
`requireNamespace` de la librería (A-13 lo hace enumerable) y el flujo de autorización en el tab
Configuración.

**Dónde viviría.** `src\startup\` (servicio) y `src\TaskPane\taskpane.html` (panel `settings`);
`src\libreria\R\R4XCL-0-UT-InstalaPaqueterias.R` (ya existe y usa `requireNamespace`);
`src\tests\test_package_manager_service.py`.

**Clasificación:** PENDIENTE (especificación acordada, no empezada) · **Prioridad:** P2 ·
**Coste:** L-XL, 8-12 días · **Riesgo:** Medio — instalar paquetes es una acción con efecto en la
máquina del usuario: la autorización explícita y el registro no son opcionales ·
**Fundamento:** VERIFICADO la especificación y los activos.

**Invariantes.** Ninguna de las 62 la cubre. Si el servicio escribe en el directorio de la
librería de R, hay que revisar que no choque con A-05 (ACL) ni con A-04 (integridad).

**Bitácora.** El problema está documentado de primera mano (sesiones con funciones que
desaparecen por paquetes ausentes) y la solución especificada en agosto no se empezó.

---

### C-09 · Ayuda contextual real en el asistente de funciones de Excel

**Origen:** `PROD-08`, `PROD-09` (= `N-08`).

**Qué resuelve.** El asistente de funciones de Excel es el principal punto de descubrimiento para
quien no lee el código, y hoy muestra "Exported Function", "Exported R Functions" y "Argument"
para casi todo el catálogo (`excel_api_functions.cc:272,292,296`). A-13 arregla la mitad (los
atributos de la librería); la otra mitad es que el trabajo de documentación **ya existe** en 28
sidecars y en un diccionario de 37 KB y no llega al sitio donde el usuario lo necesita. Además
todas las funciones dinámicas se registran con la misma firma de 16 argumentos
(`"UQQQQQQQQQQQQQQQQ"`, `:253`), con independencia de su aridad real.

**Propuesta.** Generar la descripción, la categoría y los textos de argumento desde los sidecars
en el momento del registro, y acotar la firma a la aridad real de cada función.

**Dónde viviría.** `src\Core\src\excel_api_functions.cc:194, 235, 253, 268, 287-296`;
`src\Install\functions\*.json`.

**Clasificación:** NUEVA IDEA · **Prioridad:** P3 · **Coste:** L, 5-8 días · **Riesgo:** Medio —
`xlfRegister` tiene límites de longitud por argumento y de número de argumentos, y el registro
ocurre en el camino crítico de `xlAutoOpen`: un error ahí deja todo en `#¿NOMBRE?`. Medir primero
la aridad máxima real de las funciones exportadas, que el eje 1 dejó como comprobación pendiente
(hay arrays de 32 con descripciones escritas en `xlParmPtrs[10 + i]`) ·
**Fundamento:** VERIFICADO la firma única y los textos genéricos; **HIPÓTESIS** el riesgo de
desbordamiento con aridades > 22.

**Invariantes.** `INV-CORE-01` (el registro sigue ocurriendo solo en `xlAutoOpen`) e `INV-SJ-02`
(`function_name_xll` debe seguir coincidiendo exactamente con el nombre en `globalenv()`).

**Bitácora.** Sin menciones.

---

### C-10 · Decidir el alcance de NEVEN-SIM

**Origen:** especificación `neven-sim` (**109 tareas abiertas, 0 marcadas**); `src\NEVEN-SIM\`
(37 ficheros, `BUILD_NEVEN_SIM=OFF` por defecto); `SEC-15`; `COD-08`.

**Qué resuelve.** Una ambigüedad que contamina el plan de trabajo. NEVEN-SIM existe como XLL
separado con 37 ficheros, tiene su propio `CMakeLists.txt` y sus propios tests, su
`SIM_QuickSim` de 250 líneas está exportado, consume las colas de
`PostMessageBridge` (A-16) y está **desactivado por defecto** en el build. Su especificación es la
más grande del proyecto y tiene cero tareas marcadas. Nadie sabe, leyendo el repositorio, si es un
módulo del producto o un prototipo.

**Propuesta.** Una decisión, no código: o se define un corte vertical mínimo (una simulación Monte
Carlo de extremo a extremo, con su sidecar, su documentación y su activación en el instalador) y
se cierra el resto de la especificación como futuro, o se declara experimental y se saca de la
narrativa del producto y del paper. Lo que no conviene es dejar 109 tareas abiertas en el plan de
trabajo como si fueran deuda inmediata.

**Dónde viviría.** `.kiro\specs\neven-sim\tasks.md` (la decisión); `src\CMakeLists.txt:96-97`
(zona de las opciones de build); `src\docs\Arquitectura\Arquitectura.md`;
`src\docs\Paper\sections\` si se menciona.

**Clasificación:** PENDIENTE (decisión) · **Prioridad:** P1 la decisión (S, media jornada); el
corte vertical, XL si se elige hacerlo · **Riesgo:** Nulo la decisión · **Fundamento:**
VERIFICADO.

**Invariantes.** Ninguna. `INV-BLD-01/02` aplican a NEVEN-SIM como a todos los binarios; su
`NEVEN-SIM.xll` en producción **sí** lleva CFG (`0x4160`), al contrario que el XLL principal
(A-06).

**Bitácora.** Sin decisión registrada sobre el alcance.

---

### C-11 · NEVEN Enterprise: declarar explícitamente fuera del alcance de la tesis

**Origen:** especificación `neven-enterprise` (24 tareas abiertas, 0 hechas).

**Qué resuelve.** La especificación propone llevar NEVEN a multiplataforma con una capa cloud,
macOS, Excel Web y despliegue corporativo. Es una dirección legítima y es de otro orden de
magnitud: su primer requisito contradice el supuesto que sostiene toda la arquitectura actual
(XLL de Windows con procesos hijo locales y rutas absolutas en `C:\NEVEN\`). Mientras esté en
`.kiro\specs\` como especificación activa, sus 24 tareas aparecen en cualquier recuento de
pendientes y compiten por atención con el arreglo de la descarga de audiolibros.

**Propuesta.** Marcarla como dirección estratégica fuera del alcance de la entrega de tesis, con
una nota de una línea, y mantenerla fuera del plan de trabajo hasta que la tesis esté entregada.
Si se quiere avanzar algo en esa dirección con coste casi nulo, lo que de verdad la habilita es
B-12 (offline y dependencias vendorizadas) y A-11 (configuración única): ambas reducen el acoplamiento
con la máquina.

**Dónde viviría.** `.kiro\specs\neven-enterprise\` (nota de alcance) y el archivo de
especificaciones de B-21.

**Clasificación:** NUEVA IDEA (decisión de alcance) · **Prioridad:** P3 · **Coste:** S, media
jornada · **Riesgo:** Nulo · **Fundamento:** VERIFICADO.

**Invariantes.** Ninguna hoy. Si algún día se acomete, chocaría con buena parte de P1 y P3
(rutas absolutas, pipes locales, `C:\NEVEN\`): entonces la ontología tendría que revisarse en
bloque, y conviene saberlo antes de empezar, no después.

**Bitácora.** Sin menciones. Es la especificación más reciente (septiembre) y la menos conectada
con el trabajo real registrado.

---

## 5. Estado de las 27 especificaciones de `.kiro\specs\`

461 casillas abiertas en 19 especificaciones. El plan de auditoría pide declarar el estado, porque
una casilla abierta en una especificación obsoleta no es un pendiente. Veredicto propuesto
(**HIPÓTESIS** salvo donde se cita evidencia; B-21 ejecuta la limpieza):

| Especificación | Abiertas / hechas | Veredicto propuesto |
|---|---:|---|
| `code-audit` | 0 / 74 | **CERRADA** |
| `function-dictionary` | 0 / 41 | **CERRADA** |
| `neven-studio-standalone` | 0 / 45 | **CERRADA** |
| `python-integration` | 0 / 51 | **CERRADA** |
| `python-reactivation` | 0 / 23 | **CERRADA** — el plan preguntaba por ella: Python está integrado y `ON` por defecto; hay 4 suites `PythonReactivation*PBT` en el binario |
| `rj2xcl-to-ponto-rename` | 0 / 32 | **CERRADA con residuo** — quedan 4 nombres `RJ_*` visibles al usuario y 29 menciones de `RJ2XCL` en la documentación (`PROD-23`, A-21) |
| `security-remediation` | 0 / 72 | **CERRADA formalmente, no verificable** — `SECURITY.md:192` afirma 36/36 remediados y sin IDs estables no se puede comprobar (B-18). Y dos controles que introdujo están inertes: integridad (A-04) y confirmación de desactivación del sandbox (A-18) |
| `neven-data-lab` | 7 / 123 | **VIGENTE, casi cerrada** |
| `viewer-professional` | 5 / 36 | **VIGENTE** — hay 34 tests `viewer_professional_tests.cc` |
| `reliability-improvements` | 7 / 29 | **VIGENTE** — converge con A-07, A-14, A-15 |
| `maintainability-improvements` | 11 / 18 | **VIGENTE** — converge con B-06, B-07, B-19 |
| `quarto-integration` | 10 / 21 | **VIGENTE** — converge con C-05 |
| `webview2-repl-console` | 8 / 23 | **VIGENTE con reserva** — la consola Electron se eliminó (`CMakeLists.txt:124-126`) y el sustituto es `REPLManager`/`REPLBridge`: revisar qué tareas siguen aplicando |
| `console-diagnostic-stream` | 15 / 30 | **VIGENTE** — converge con B-09 y C-01 |
| `startup-optimization` | 27 / 30 | **VIGENTE** — la sysimage resolvió el arranque de Julia; revisar qué queda |
| `webview2-viewer` | 30 / 78 | **VIGENTE** — converge con A-14 y con la parte del visor de `SEC-19` |
| `neven-datalab-gr-family` | 18 / 12 | **VIGENTE** — converge con A-20 (sidecars de los nueve `GR_*.Studio.R`) |
| `neven-installer` | 7 / 27 | **VIGENTE** — converge con A-12, B-11 |
| `nevenx-dispatcher` | 20 / 0 | **IMPLEMENTADA SIN CERRAR** — `R4XCL-0-NevenX.R` existe, cumple `INV-NX-01..04` y tiene 55 alias (`COD-26`). Marcar lo hecho |
| `neven-v3-taskpane` | 23 / 0 | **IMPLEMENTADA SIN CERRAR** — el TaskPane con 9 tabs, DuckDB y el servidor 5555 existen y funcionan. Marcar lo hecho |
| `ai-integration` | 28 / 1 | **SUPERADA POR LA IMPLEMENTACIÓN** — especifica la sección `AI.*` y prompts en `Documents\NEVEN\prompts\`; producción usa `ai_profiles` y el servidor de Studio. Es el origen documental de `PROD-06`: reescribir o archivar, no ejecutar (A-11) |
| `ontologia-v2` | 17 / 0 | **VIGENTE, no empezada** — es la base de C-07 |
| `neven-package-manager` | 45 / 0 | **VIGENTE, no empezada** — es C-08; hay `package_manager_service` con tests |
| `neven-sim` | 109 / 0 | **AMBIGUA** — decidir alcance (C-10) antes de contarla como deuda |
| `neven-enterprise` | 24 / 0 | **FUERA DE ALCANCE de la tesis** (C-11) |
| `ontology-engine-framework` | 50 / 7 | **AJENA A NEVEN** — describe la migración del esquema `[IA]` de `sqldb_buklo_lab` (PKs `BIGINT IDENTITY`, `id_cat_company`, *stored procedures* `pa_con`/`pa_man`, capas Gateway y Angular). No es el add-in de Excel: archivar (`MEJ4-07`) |
| `ai-interpreter` | sin `tasks.md` | **INCOMPLETA** — decidir si se completa o se archiva |

**Efecto en el plan de trabajo.** De las 461 casillas abiertas:

| Situación | Casillas | Especificaciones |
|---|---:|---|
| Decisión de alcance pendiente, no deuda inmediata | **133** | `neven-sim` (109), `neven-enterprise` (24) |
| Ajena a NEVEN | **50** | `ontology-engine-framework` |
| Implementada sin cerrar: hay que marcar, no ejecutar | **43** | `nevenx-dispatcher` (20), `neven-v3-taskpane` (23) |
| Superada por la implementación: reescribir o archivar | **28** | `ai-integration` |
| **Deuda real** | **207** | las 14 vigentes; de ellas 62 son C-07 y C-08 (especificadas y no empezadas) y el resto converge en buena parte con las mejoras de este documento |

Depurar esto es B-21, y es lo que evita construir el plan de trabajo sobre un recuento que
multiplica por más de dos la deuda real.

---

## 6. Cambios que requieren modificar la ontología

Cuatro reformulaciones y cuatro adiciones. En todos los casos **primero se actualiza el YAML y se
justifica el cambio; después se implementa**. Ninguna propuesta de este documento contradice una
invariante en silencio.

### 6.1 `INV-LR-04` — reformular (bloquea A-13 y C-09)

**Dónde:** `src\docs\ontologia\neven-core\neven-ontology-p2.yaml:660`.
**Texto actual:** exige `attr(NombreFuncion, DialogosXCL$Descripcion)` al final de cada `.R` y
afirma que sin él "la función no aparece en Excel".
**Por qué hay que cambiarlo:** las dos partes son falsas, y se verificó en el eje 1.
`DialogosXCL` no es un nombre de atributo: es la lista de textos de ayuda que devuelve
`R4XCL_INT_DIALOGOS()` (`src\libreria\R\R4XCL-0-Interno-2.R:241-280`), que las funciones usan para
rellenar sus diálogos. El atributo que el runtime lee es literalmente `"description"`
(`src\startup\startup.r:69-71`). Y la visibilidad no depende de él: `NEVEN$list.functions()`
enumera toda función de `globalenv()`, de modo que las 62 funciones sin atributo **sí** aparecen
en Excel, solo que con la descripción genérica "Exported Function". El propio paper lo documenta
correctamente (`03_viewer_extensibility.tex:95-96`).
**Redacción propuesta:** "cada función exportada asigna `attr(fn, "description")` y
`attr(fn, "category")`; sin ellos la función aparece en Excel pero el asistente de funciones
muestra la descripción genérica y los argumentos sin nombre útil".
**Consecuencia:** una invariante que describe un mecanismo inexistente no sirve ni como control ni
como guía, y además hace fracasar cualquier test que intente mecanizarla (B-04).

### 6.2 `INV-AS-03` — reformular (solo si se adopta A-11)

**Dónde:** `neven-ontology-p3.yaml:205`. **Texto actual:** "AgentService corre en el puerto 5556,
no 5555".
**Por qué:** la invariante fija un número sin declarar quién más puede usarlo, y hoy tres
servicios reclaman el 5556 (AgentService, el servidor de audiolibros y el `fallbackPort` de
Studio). Al no decir nada sobre exclusividad, no impidió la colisión que rompe el módulo de
audiolibros.
**Redacción propuesta:** "cada servicio toma su puerto de `neven-config.json`, los rangos no se
solapan y el arranque falla con mensaje explícito si el puerto está ocupado por otro servicio de
NEVEN; 5556 es el valor por defecto de AgentService".
**Importante:** **A-02 no requiere este cambio.** Mover el servidor de audiolibros a un puerto
propio respeta la invariante tal como está, y es la corrección inmediata. El cambio solo hace
falta si se adopta el registro de puertos en configuración (A-11).

### 6.3 `INV-SB-03` — ampliar (bloquea la parte SQL de A-01)

**Dónde:** `neven-ontology-p2.yaml:283`. **Texto actual:** `/api/query` solo acepta
`SELECT`/`WITH`/`SHOW`/`DESCRIBE`; cualquier otro statement → HTTP 400.
**Por qué:** la invariante **se cumple literalmente** (`neven_http_server.py:523-533`) **y es
insuficiente**: en DuckDB, las funciones de tabla que leen ficheros del disco se invocan desde un
`SELECT`, de modo que "solo SELECT" no impide la lectura de ficheros arbitrarios a través de la
base de datos; y `/api/groupby` interpola nombres de columna en la consulta sin escapar. El
proyecto presenta esta invariante como el control del endpoint.
**Redacción propuesta:** mantener la restricción de sentencia y **añadir** que los identificadores
nunca se interpolan sin validarse contra `DESCRIBE dataset`, que las funciones de tabla permitidas
son una lista blanca explícita, y que la conexión del endpoint es de solo lectura sobre el dataset
cargado.
**Nota:** no se propone eliminar la invariante ni relajarla. La parte de A-01 que solo valida
identificadores y parametriza rutas (`PEN-S09`) **no** necesita este cambio y puede hacerse ya.

### 6.4 `INV-CMN-02` — corregir el mecanismo declarado y la política de ausencia (bloquea A-04)

**Dónde:** `neven-ontology-p1.yaml:347`. **Texto actual:** `SecurityService::VerifyScriptIntegrity()`
verifica **HMAC** de cada fichero de `C:\NEVEN\functions\` antes de enviarlo al motor.
**Por qué:** tres desajustes verificados. (a) No es HMAC: es SHA-256 sin clave
(`SecurityService.cc:56-93`), de modo que quien puede reescribir el `.R` puede reescribir el
`.sha256`. (b) La verificación es *fail-open*: devuelve `true` cuando falta el fichero de hash
(`:34-40`). (c) En producción hay **0** ficheros `.sha256` para 92 scripts, así que la invariante
está violada en los datos aunque se cumpla en la lógica.
**Redacción propuesta:** decir SHA-256 (no HMAC), declarar la política ante ausencia de hash
(rechazar y registrar, tras el despliegue de los hashes), y declarar que el instalador y
`Sync-Dist.ps1` son responsables de generarlos.
**Por qué SHA-256 y no implementar HMAC de verdad:** la clave tendría que vivir en la misma
máquina donde el atacante del modelo de amenazas es un usuario local (`SEC-09`); embebida en el
XLL es ofuscación, no secreto. El control que de verdad protege estos ficheros es la ACL (A-05).
Declararlo así es más honesto que prometer un HMAC que no añade fuerza.

### 6.5 Cuatro invariantes nuevas (adiciones, no contradicen nada)

| Propuesta | Dónde | Motivo | Mejora que la necesita |
|---|---|---|---|
| **a. ACL del directorio de producción** — `C:\NEVEN\` y sus subdirectorios no deben ser escribibles por `Authenticated Users`; los directorios que el runtime necesita escribir se enumeran explícitamente | `p1.yaml` | Ninguna de las 62 cubre los permisos del árbol de producción, que es la vía por la que una cuenta local cualquiera ejecuta código en la sesión de otra | A-05 |
| **b. Autenticación de la API local** — ninguna ruta `/api/*` responde sin token y sin validación de origen; el CORS no es comodín | `p2.yaml` | Es el hallazgo crítico del eje 3 y no hay invariante que lo gobierne | A-01 |
| **c. Alcance del sandbox** — qué cubre, qué no cubre, en qué puntos se aplica y qué no promete | `p1.yaml` | Ninguna de las 62 describe el sandbox, que es el control que `SECURITY.md` presenta como principal y que no se aplica en la vía por la que hoy entra la mayor parte del código | A-10 |
| **d. Fuente única de artefacto desplegado** — cada fichero desplegado en `C:\NEVEN\` tiene exactamente un origen declarado en el repositorio, y la paridad se puede comprobar por hash | `p4.yaml` | Cinco copias del servidor HTTP con cuatro hashes, una regla de steering que apunta a la copia equivocada, y 21 ficheros en producción sin origen | B-08 |

---

## 7. Skills del catálogo que conviene incorporar al flujo de trabajo del proyecto

La tarea pide valorar si algún skill del catálogo puede incorporarse al flujo de NEVEN, no solo
usarse en esta auditoría. Seis encajan y uno conviene retirar.

| Skill | Dónde encaja | Propuesta concreta | Mejora |
|---|---|---|---|
| `bibtex-hygiene` | el `.bib` del paper | `bib_lint.py` como paso del CI del documento. Hoy da `41 entries: 0 errors, 0 warnings`: el valor es que siga así cuando se añadan referencias | B-15 |
| `citation-verification` | el `.bib` del paper | `verify_citations.py` en el mismo job. **Es el skill que detectó `COD-46`** (`Panko2016` apuntando a otro trabajo), que es el defecto de mayor consecuencia académica de todo el informe. Guardar el JSON junto al `.tex` para que el estado de cada referencia sea consultable | B-15 |
| `unslop-academic-writing` | documentación de usuario y el propio informe | `slop_check.py` sobre los documentos que lee un usuario nuevo. Línea base medida: `Guia_usuario.md` 0,0 y `Guia_inicio_rapido.md` 0,0 (limpias), `TROUBLESHOOTING.md` 6,8, `README.md` **10,0** con frases de 39,5 palabras de media, y `00_abstract.tex` 6,0. Umbral propuesto: < 5 para el abstract y el README, < 10 para el resto | B-10, B-15 |
| `scientific-writing` | coherencia numérica del paper | `check_consistency.py` con un `consistency_manifest.json` que registre los números repetidos (tests, procedimientos R y Julia, tamaño de la sysimage) y los **ate al generador único de B-10**. Es la herramienta que convierte "342 vs 369" en un fallo de script en lugar de un hallazgo de auditoría. `check_references.py` y `audit_claims.py` para la trazabilidad de afirmaciones | B-15, B-10 |
| `statistical-analysis` | la librería R y el paper | Referencia para la batería de supuestos de C-03 (`assumption_checks.py`) y para revisar nuevas funciones econométricas antes de publicarlas. Es el skill que fundamentó `COD-30` (0 `shapiro.test`, 0 `Box.test`, 0 tamaños de efecto) y `COD-31` (HC0 en lugar de HC3) | C-03, A-13 |
| `metaheuristic-optimization` | `J4XCL-OP-Optimizacion.jl` y NEVEN-SIM | Referencia de diseño para C-06: control de semilla, criterios de parada y reproducibilidad. **Dicho con precisión: hoy no aplica al código existente**, porque el fichero implementa métodos deterministas; aplicaría a lo que se añada | C-06 |
| `ontology-book-processor` | el pipeline de ingesta de libros | **Ya existe un pipeline propio que hace esto**: `docs\COMO_AGREGAR_LIBROS.md` (13 KB), los 7 `ontology_*_enricher.py` de `src\startup\` y `rag_engine.py`. La propuesta no es adoptar el skill, es **alinearlo o retirarlo**: mantener dos descripciones del mismo procedimiento garantiza que divergan | B-13 |

**Un problema de los skills locales, no de los del catálogo.** `.agents\skills\research-agent\`
contiene copias de cinco skills del catálogo (`scientific-writing`, `unslop-academic-writing`,
`bibtex-hygiene`, `citation-verification`, `statistical-analysis`) y `.agents\skills\` otras dos
(`metaheuristic-optimization`, `ontology-book-processor`). Son copias que ya pueden haber
divergido de las instaladas en `C:\Users\…\.kiro\skills\`, y nada declara cuál manda: es el mismo
patrón de B-08 aplicado a los skills. Propuesta: usar los del catálogo y dejar en el repositorio
solo los que son **objeto** del producto, que son otra cosa — `.agents\skills\econometria`,
`excel-consultant`, `statistical-analysis`, `unslop-academic`, `citation-verification` son los
skills de *runtime* que el agente de NEVEN carga para atender al usuario final
(`restricted_to_rag: true`, `always_active: true`). Sobre esos, el eje 3 dejó un veredicto que
conviene no olvidar al diseñar C-07: **`restricted_to_rag` no es una defensa técnica contra
inyección de prompt**, es una restricción de las fuentes que el agente debe citar, aplicada en el
prompt.

**Y el skill local `.kiro\skills\rj2xcl-docs\SKILL.md`** describe el proyecto con su nombre
antiguo y cita `docs/ESTADO_DE_LAS_COSAS.md`, ruta que no existe: entra en B-10.

**Lo que el catálogo no tiene** y esta auditoría habría necesitado, para que no se dé por
cubierto: revisión de código y análisis estático de C++, AppSec y modelado de amenazas,
dependencias y SBOM, Windows/COM/Excel SDK, usabilidad, y validación de ontologías contra código.
Los dos ejes técnicos —código y seguridad, que son el núcleo de lo que pidió el usuario— se
ejecutaron **sin apoyo instrumental**. Es un argumento a favor de B-04: si no hay skill que
valide la ontología contra el código, hay que convertirla en tests.

---

## 8. Lo que NO se propone, y por qué

Nueve cosas que parecen mejoras obvias y no entran en el plan. Se enumeran para que no se
reintroduzcan por inercia en la siguiente iteración.

### 8.1 Modo degradado que registre funciones de sustitución tras conectar los motores

Sería la respuesta natural a `PROD-10` (si R no arranca, todas las fórmulas `R.*` dan `#¿NOMBRE?`
y la única salida es cerrar Excel). **Choca de frente con `INV-CORE-01`**: `MapFunctions()` y
`RegisterFunctions()` solo pueden ejecutarse durante `xlAutoOpen`; desde un temporizador o un hilo
de fondo, `xlfRegister` devuelve error 2 y **todo** aparece como `#¿NOMBRE?`. Y el comentario de
`src\Core\src\rj2xcl.cc:544-550` documenta que esa vía ya se probó y causó cuelgues. La
alternativa viable es C-01 (diagnóstico en celda) y C-02 (panel de salud): no arreglan la
degradación, pero el usuario sabe qué pasa y por qué.

### 8.2 CSP en el visor WebView2

**Descartado por el usuario el 2026-08-19** con razón escrita: el HTML que genera R lleva
`<script>` inline (`Plotly.newPlot(...)`), de modo que la CSP necesitaría `unsafe-inline` y
perdería la mayor parte de su protección; el beneficio estimado era ~10 % y el riesgo de romper
Plotly, D3, Leaflet, KaTeX y las fuentes era medio-alto, con 2-3 horas de pruebas por sesión. **No
se reabre.** De `SEC-19` se propone solo lo que no requiere CSP y no estaba en aquella decisión:
acotar `file:///` a los directorios de trabajo de NEVEN y añadir `add_FrameNavigationStarting`
para que los iframes hereden el filtro de navegación que ya existe y está bien diseñado. Eso cabe
en A-18 como trabajo menor; si se quiere como ítem propio, es S y P3.

### 8.3 DACL restrictiva en los named pipes como primer paso

**Descartada por el usuario el 2026-08-19** (riesgo ALTO, "si falla, el XLL no conecta y Excel se
congela"). A-19 la re-propone **troceada y en P3**, con los dos pasos de bajo riesgo primero, y
deja el paso de la DACL como decisión explícita del usuario, con el único dato nuevo que justifica
volver a plantearla: la premisa de aquel análisis —que el riesgo "requiere privilegios
elevados"— es falsa.

### 8.4 Mover `C:\NEVEN\` a `%ProgramFiles%`

Resolvería `SEC-09` de raíz (las ACL heredadas de `C:\`), y **no se propone**: la ruta está
asumida por `INV-SR-01..05`, `INV-CMN-02`, `INV-SB-01..05` y por rutas absolutas repartidas en el
código C++, en los scripts de arranque, en el servidor Python y en el instalador. Es un proyecto,
no un arreglo. A-05 endurece las ACL, que es el arreglo acotado.

### 8.5 Refactorizar 596 métodos a `snake_case`

`src\docs\sops\coding-standards.md` pide funciones `snake_case` y **596 de 663 métodos son
`PascalCase`**. El código es internamente coherente (estilo Google para clases y métodos) y el
documento es el que está mal. Cambiar 596 firmas es un cambio masivo, sin beneficio y con riesgo
de ABI. Se propone corregir el documento (B-10) y declarar expresamente las excepciones
`RJ_`/`RJ2XCL`, que el usuario mantiene a propósito por compatibilidad.

### 8.6 Reescribir el historial de git por el endpoint de Azure

`SEC-18`: el historial conserva el identificador de un recurso Azure OpenAI retirado en `de8d44b`;
lo que había en `apiKey` era un marcador, no una clave. Reescribir el historial de un repositorio
con remoto es caro y rompe clones; el beneficio es bajo. Se propone rotar la clave de ese recurso
si sigue vivo y **dejar la decisión escrita** (A-18 lo recoge como nota de decisión, no como
reescritura).

### 8.7 `/WX` desde el primer día

B-06 sube a `/W3`; añadir `/WX` antes de vaciar la cola de avisos bloquearía el build y haría
abandonar la mejora. Primero `/W3`, luego la cola, y después `/WX` por objetivo.

### 8.8 `module` en la librería Julia como tarea inmediata

`COD-33` es real (ningún "módulo J4XCL" es un módulo de Julia, no hay frontera de namespace), y el
coste está medido: obliga a reconstruir `neven_julia.dll` (1,04 GB) y a revalidar `INV-CJ-01` e
`INV-CJ-02`. Va en A-23 en P3 con esa condición escrita, no como tarea suelta.

### 8.9 Bundlers, transpiladores o módulos ES en el TaskPane

`INV-TF-04` lo prohíbe y la invariante **no es el obstáculo** para nada de lo que se propone:
B-19 extrae el JS a ficheros servidos con `<script src=>` y globales explícitos, y B-20 usa un
runner en el navegador y `node --test`. No se propone tocar esa invariante. Tampoco se retoman
`roughViz`/Sketch ni Mermaid.js, que la bitácora declara bloqueados tras varios intentos.

---

## 9. Secuencia por dependencia y coste agregado

El orden no es por severidad: es por dependencia. Hacer A-01 sin B-03 deja los arreglos sin fijar;
hacer B-19 sin B-02 repite el incidente de septiembre; pasar la integridad a *fail-closed* sin
desplegar los hashes deja NEVEN sin funciones.

### Fase 0 — Verificación antes que arreglos (3-6 jornadas)

| Mejora | Coste | Por qué primero |
|---|---|---|
| **B-01** mover `.github\` y arreglar el workflow | 0,5-1,5 d | Sin esto nada queda protegido |
| **B-02** runner de pytest | 1-2 d (+2-4 de triaje) | Prerrequisito de B-03 y B-19 |
| **B-21** declarar el estado de las 27 especificaciones | 1-2 d | El plan de trabajo necesita un recuento verdadero |
| **C-10** decidir el alcance de NEVEN-SIM | 0,5 d | 109 casillas dependen de esta decisión |

### Fase 1 — Cerrar lo que está abierto al exterior (11-17 jornadas)

| Mejora | Coste | Nota |
|---|---|---|
| **A-01** autenticar la API local | 4-6 d | con **B-03** (3-4 d) en paralelo, no después |
| **A-02** puerto y bind del servidor de audiolibros | 2-3 d | |
| **A-03** endpoint de descarga + esquema de URLs + verificación | 1,5-2,5 d | cierra el pendiente arrastrado |
| **A-08** política única de `srcdoc` | 0,5-1 d | |

### Fase 2 — Integridad del despliegue y del artefacto (12-16 jornadas)

| Mejora | Coste | Nota |
|---|---|---|
| **B-08** fuente única + script de paridad | 3-4 d | prerrequisito de A-04 |
| **A-04** integridad real de scripts | 2-3 d | orden interno obligatorio |
| **A-05** ACL de producción | 3-4 d | probar en VM, nunca en la instalación viva |
| **A-06** `/guard:cf` en el enlazado | 0,5 d | + el job del PE en B-01 |
| **B-09** observabilidad y rotación de logs | 3-4 d | |
| **A-07** guarda de excepciones en los exports | 0,5 d | independiente, se puede colar en cualquier hueco |

### Fase 3 — Calidad del producto y de la verificación (30-44 jornadas)

**A-13** librería R (5-7 d, con §6.1 hecho antes) · **B-04** invariantes ejecutables y hook
(3-4 d) · **B-05** tests de los subsistemas sin cobertura (5-7 d) · **B-06** avisos del compilador
(2-4 d) · **B-07** reproducibilidad del build (1-2 d) · **B-10** higiene documental y cifras
(2 d) · **B-15** el paper (2-3 d) · **A-11** configuración y puertos (3-4 d, con §6.2) ·
**A-12** WebView2 en el instalador (1-2 d) · **A-10** sandbox por lenguaje (4-6 d) ·
**C-01** `=NEVEN.Diagnostico()` (2-3 d).

### Fase 4 — Estructura, capacidades y lo que puede esperar (aprox. 70-110 jornadas)

**B-19** monolitos (8-12 d, condicionado) · **B-11** empaquetado y máquina limpia (5-7 d) ·
**C-03** informe estadístico (7-10 d) · **C-05** exportación reproducible (5-8 d) ·
**C-08** gestor de paquetes (8-12 d) · **C-07** agente con acciones confirmadas (10-15 d, después
de A-01) · **A-09** unificar renderizadores (4-6 d) · **C-04** benchmark Wooldridge (5-7 d) ·
**A-14** a **A-23**, **B-12** a **B-14**, **B-16** a **B-18**, **B-20**, **C-02**, **C-06**,
**C-09**, **C-11** (el resto, en P2-P3).

### Lectura del coste

Las fases 0 a 2 suman **26-39 jornadas** y son las que cambian el riesgo real del proyecto: dejan
el CI funcionando, los tests ejecutables, la API cerrada, el pendiente de audiolibros resuelto y
verificado, el despliegue con una sola fuente y con integridad, y el XLL con las mitigaciones que
la ontología ya exigía. La fase 3 (**30-44 jornadas**) es lo que un lector de la tesis y un
usuario nuevo notan. La fase 4 es trabajo de varios meses y conviene decidirlo con la entrega de
la tesis delante, no antes.

---

## 10. Hallazgos nuevos de este eje

Siete cosas que no venían de los ejes 1-3 y que salieron al consolidar. Se registran con el mismo
formato que los demás hallazgos para que puedan cerrarse con identificador (B-18).

### MEJ4-01 · `src\.github\` no está en la raíz del repositorio: el CI, las plantillas de incidencia y la de *pull request* son inertes · **ALTA** · VERIFICADO

`Test-Path '.github'` en `F:\ANTIGRAVITY\2026\NEVEN` devuelve **False**, y `git ls-files` sitúa
`build-and-test.yml`, los dos `ISSUE_TEMPLATE` y `PULL_REQUEST_TEMPLATE.md` bajo `src/.github/`.
GitHub solo lee `.github/` en la raíz del repositorio. El eje 2 (`COD-19`) estableció que el
*trigger* apunta a `main`/`develop` siendo `master` la rama real; esto es anterior y más grave:
**corregir la rama no habría cambiado nada**. Causa probable: el commit `951cfcb` movió el
proyecto bajo `src\`. Mejora: **B-01**.

### MEJ4-02 · `=NEVEN.Notebook.Export` no puede funcionar nunca · **MEDIA** · VERIFICADO

`NotebookExporter::CaptureAnalysis` no tiene invocadores
(`git grep CaptureAnalysis -- src` devuelve solo la declaración en `NotebookExporter.h:33` y la
definición en `NotebookExporter.cc:29`), de modo que `has_analysis_` es siempre `false` y
`ExportNotebook` (`:43-48`) devuelve invariablemente *"No analysis to export"*. La función está
registrada y anunciada al usuario en el asistente de Excel
(`src\Core\include\basic_functions.h:62`, "Export last analysis as Pluto notebook") y llamada
desde `src\Core\src\basic_functions.cc:914`. Dos defectos secundarios en el mismo camino: el
notebook generado cierra con `# ╔═╡ Cell order:` **sin listar ningún UUID** (`:180`), lo que
probablemente lo invalide para Pluto (**HIPÓTESIS**, comprobable abriéndolo); y el Doxygen anuncia
"a standalone HTML file" mientras el código escribe `.jl` con la cabecera "Exported from RJ2XCL".
Mejoras: **A-17** (arreglo) y **C-05** (capacidad).

### MEJ4-03 · `android\ontologia\` contiene una copia completa de sí mismo · **BAJA** · VERIFICADO

736 ficheros, de los que la mitad son una duplicación exacta en
`android\ontologia\ontologia\`: 326+326 en `graficos`, 22+22 en `checkpoints`, 11+11 en
`page_index`, 5+5 en `neven-core`, 2+2 en `_archived_econometrics`. Y el dominio `graficos` (326
ficheros) existe además en `docs\ontologia\graficos`, de modo que hay **tres copias** del mismo
dominio en el repositorio. `neven-ontology-p1.yaml` es hoy idéntico (mismo hash) en `src\docs\`,
`android\ontologia\` y `C:\NEVEN\docs\ontologia\`: el problema no es la divergencia actual, es que
nada declara la fuente. Mejora: **B-13**.

### MEJ4-04 · El patrón de API pública sin invocadores afecta al menos a cinco componentes · **BAJA** · VERIFICADO (4) / HIPÓTESIS (1)

Confirmados: `NotebookExporter::CaptureAnalysis` (MEJ4-02),
`ConfigService::RequestSandboxDisable` (`SEC-14`, sostiene un 9/10 de OWASP publicado),
`RJ2XCL_Engine::ScheduleDelayedUpdate` (`COD-05`) y `AutoLoader::LoadAllUserScripts` (`SEC-02`,
el único camino que validaba contenido). Probable: **`GCMonitor`**, cuyo nombre no aparece en
ningún `.cc` fuera de sus propios ficheros y de `CMakeLists.txt`, con 20 miembros públicos y 0
marcas Doxygen (`COD-13`). Mejora: **B-17**.

### MEJ4-05 · `DS_Wooldridge_Benchmark.Studio.R` solo existe en `src\Install\functions\` · **BAJA** · VERIFICADO

La función y su sidecar viven en el directorio del instalador y **no** en `src\libreria\R\`, donde
están las otras 63. Es un caso concreto del problema de origen de verdad de `COD-36`/`PROD-29`, y
señala que el PRD de la suite Wooldridge quedó a medio camino: hay función de usuario y no hay
regresión numérica. Mejoras: **B-08** (ubicación) y **C-04** (capacidad).

### MEJ4-06 · 461 casillas abiertas mezclan deuda real, trabajo ya hecho y asuntos ajenos · **MEDIA** · VERIFICADO

Medido spec por spec (§5): 133 casillas son decisiones de alcance, 50 son ajenas al proyecto, 43
corresponden a funcionalidad que existe y funciona (`nevenx-dispatcher`, `neven-v3-taskpane`) y 28
a una especificación superada por la implementación (`ai-integration`). La deuda real son ~207, no
461. Mejora: **B-21**.

### MEJ4-07 · `ontology-engine-framework` describe un proyecto que no es NEVEN · **BAJA** · VERIFICADO

Sus 50 tareas abiertas detallan la migración del esquema `[IA]` de `sqldb_buklo_lab`: PKs
`BIGINT IDENTITY(1,1)`, multi-tenancy `id_cat_company`, *stored procedures* `pa_con`/`pa_man`, y
capas de Gateway y Angular. No tiene relación con el add-in de Excel ni con sus motores. Mejora:
**B-21** (archivar).

---

## 11. Límites de este eje

| Límite | Motivo |
|---|---|
| No se ejecutó ningún test, build ni servicio | La ejecución es de auditoría y planificación; recompilar escribe en `src\Build\`, dentro del árbol de fuentes |
| Los costes son estimaciones | Calibradas con el tamaño medido de cada fichero y con la duración de sesiones comparables registradas en la bitácora. El triaje de los 410 tests de Python (B-02) es el que tiene mayor incertidumbre y va declarado como presupuesto aparte |
| El veredicto de cada especificación (§5) es **HIPÓTESIS** salvo donde se cita evidencia | Cerrar cada una exige revisar sus tareas una por una, que es el trabajo de B-21 |
| No se verificó el pendiente de audiolibros | Exige Excel, un motor TTS y ffmpeg, es decir ejecutar servicios y escribir en producción. El procedimiento está en `03-notas-seguridad.md` §5 y A-03 lo recoge |
| No se reauditó nada de los ejes 1-3 | Sus hallazgos se tomaron como establecidos, con su marca original de VERIFICADO o HIPÓTESIS. Donde este eje midió algo nuevo, está en §10 |
| La cobertura instrumental es asimétrica | El catálogo tiene skills para el paper y la documentación, y ninguno para revisión de código, AppSec, dependencias, Windows/COM/Excel SDK, usabilidad ni validación de ontologías (§7) |

---

## 12. Nota sobre secretos y sobre instrucciones embebidas en ficheros

**Secretos.** No se transcribió ningún valor. Los dos casos conocidos siguen siendo los que
reportaron los ejes anteriores, y se repiten aquí solo por ubicación y naturaleza: una contraseña
literal de exportación de PFX en `src\TaskPane\Generate-Cert.ps1` (líneas 43, 55 y 56) y el bloque
equivalente de `src\Install\Install-NEVEN.ps1` (~1090-1100); y, en el historial de git, el
identificador de un recurso Azure OpenAI retirado en `de8d44b` —no una clave—. `INV-INS-01` se
cumple en HEAD. Este eje no encontró ningún secreto nuevo.

**Instrucciones embebidas.** Se leyeron ficheros que contienen directivas dirigidas a agentes:
`src\docs\SIDECAR_FORMAT.md` (sección "Notas para el Agente IA"), `src\docs\AGENT_INSTRUCTIONS.md`,
`src\docs\Paper\redactor-academico.md`, `src\docs\Paper\auditor-forense-ia.md`,
`.kiro\skills\*\SKILL.md`, `.agents\skills\*\SKILL.md`, y el comentario imperativo de
`src\CMakeLists.txt:96-97` ("Default ON is correct — do NOT set to OFF" sobre
`NEVEN_ENABLE_PYTHON`). Todos son artefactos legítimos del proyecto. **Ninguno fue obedecido**: se
trataron como dato, y donde su contenido afecta al plan se recoge como hallazgo —`SIDECAR_FORMAT.md`
documenta una ruta de despliegue falsa (A-20) y el skill `rj2xcl-docs` cita rutas inexistentes
(B-10)—. No se detectó ninguna directiva que intente redirigir al agente contra la intención del
usuario.




