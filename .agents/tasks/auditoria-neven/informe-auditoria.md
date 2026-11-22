# Informe de auditoría de NEVEN

**Fecha:** 2026-11-21 · **Rama:** `master` · **HEAD:** `9eba8b1`
**Raíz del workspace:** `F:\ANTIGRAVITY\2026\NEVEN` · **Prefijo real del código:** `src\`
**Alcance:** los cuatro ejes que pidió el usuario — calidad de la herramienta como producto,
calidad del código, seguridad y mejoras recomendadas.
**Modo:** solo lectura. No se modificó ningún fichero de NEVEN, nada en `C:\NEVEN\` (producción
viva), no se compiló, no se ejecutó ningún servicio, no se commiteó y no se hizo push.
**Entregable complementario:** `plan-de-trabajo.md`, en el mismo directorio, con los tres grupos
PENDIENTES, POR MEJORAR y NUEVAS IDEAS.

Documentos de trabajo que sostienen este informe, en el mismo directorio: `00-layout-real.md`
(layout e inventario de invariantes), `plan-auditoria.md` (plan de los cuatro ejes),
`01-notas-producto.md`, `02-notas-codigo.md`, `03-notas-seguridad.md`, `04-notas-mejoras.md`.
Cada hallazgo de este informe mantiene el identificador con el que aparece en esas notas, de modo
que puede cerrarse citándolo.

---

> ## Fe de errata — 2026-11-22
>
> **Este informe afirmaba que «el CI no existe». Era falso.** El CI sí existía: corría en la rama
> `main` y llevaba un mes fallando en todas las ejecuciones. Evidencia: run
> [36640534455](https://github.com/minorbonillagomez/NEVEN/actions/runs/36640534455), rama `main`,
> `FAILURE` en «Run Unit Tests» con `rj2xcl_tests_NOT_BUILT (Not Run)`.
>
> **Causa del error:** la auditoría se hizo sobre `master` y no detectó que el repositorio tenía
> **dos historias sin antepasado común**. `main` era entonces la rama por defecto en GitHub, tenía
> `.github/` en la raíz y por tanto CI activo; `master` tenía el workflow bajo `src/` y ningún CI.
> El enunciado correcto es: **`master` no tenía CI**.
>
> Esto no invalida el ítem `B-01` del plan, pero sí redefine su alcance: era «dar CI a `master`»,
> no «resucitar un CI muerto». `B-01` se ejecutó y `master` tiene ahora CI operativo (run
> [44984615668](https://github.com/minorbonillagomez/NEVEN/actions/runs/44984615668): 368 de 369
> tests en verde). `main` quedó archivada como `archive/pre-reorg-2026-09-29`.
>
> Los párrafos afectados (§1 foco 2, la tabla de §1 en la fila `MEJ4-01`, y §4.2 punto 2) se
> corrigieron en el cuerpo del documento.

## 1. Resumen

NEVEN funciona y hace cosas que ningún add-in comparable hace: ejecuta R, Julia y Python desde
celdas de Excel, con un IPC propio por named pipes, un visor WebView2, una librería de 93
definiciones de nivel superior en R (42 de ellas funciones de usuario, §2.2), y un TaskPane con
nueve pestañas. El código C++ tiene mejor higiene de la esperada: cero funciones inseguras de la
CRT, RAII real, IPC centralizado y 369 tests automatizados.

Los problemas no están donde el proyecto los vigila. Están en tres sitios:

1. **La superficie HTTP local no tiene control de acceso.** Con NEVEN Studio en marcha, el puerto
   5555 ofrece ejecución de código R/Julia/Python y escritura de ficheros a quien llegue a él,
   sin token y con `Access-Control-Allow-Origin: *`. El sandbox de 133 tests no cubre ese camino.
2. **Nada verifica el proyecto de forma automática.** El workflow de CI vive en `src\.github\`,
   que GitHub no lee, de modo que `master` no tiene CI (en `main` sí lo había, fallando desde hace
   un mes: ver la fe de errata al inicio); 410 funciones de test en Python no tienen
   runner declarado; diez subsistemas C++ no tienen ningún test; el build compila con `/W1`.
3. **La documentación describe un proyecto que ya no es este.** El layout real cambió en el
   commit `951cfcb` y 22 referencias documentales siguen apuntando al árbol anterior, entre ellas
   el hook que debía validar los cambios y el propio steering que esta auditoría está obligada a
   seguir.

### Recuento de hallazgos

| Eje | Prefijo | Crítica | Alta | Media | Media-Baja | Baja | Informativa | Total |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 — Producto | `PROD-*` | 1 | 8 | 14 | — | 5 | 1 | **29** |
| 2 — Código | `COD-*` | 0 | 9 | 26 | — | 15 | 6 | **56** |
| 3 — Seguridad | `SEC-*` | 2 | 6 | 10 | 2 | 3 | 1 | **24** |
| 4 — Mejoras (hallazgos nuevos del eje) | `MEJ4-*` | 0 | 1 | 3 | — | 3 | 0 | **7** |
| **Total** | | **3** | **24** | **53** | **2** | **26** | **8** | **116** |

`MEJ4-05` pasó de Baja a Media al remedirlo por nombre y hash en lugar de por conteo (§6.5). Es el
único cambio de severidad respecto a los documentos de trabajo.

A esos 116 se suman los **18 hallazgos de inventario** (`LAY-01..LAY-18`, §2.4), que son
mediciones del reconocimiento inicial; cuatro de ellos coinciden con hallazgos de los ejes y se
señala el solape.

### Los hallazgos que cambian una decisión

| ID | Qué | Por qué importa |
|---|---|---|
| `SEC-01` | API local del 5555 sin autenticación, CORS comodín, endpoints de ejecución | Convierte "visitar una página" o "tener una cuenta local" en ejecución de código en la sesión de Excel del usuario |
| `MEJ4-01` | `src\.github\` no está en la raíz: `master` no tiene CI (`main` sí lo tenía, y fallaba) | Corregir solo el filtro de rama (`COD-19`) no habría cambiado nada. Media jornada de arreglo y habilita todo lo demás |
| `PROD-01` | Tres servicios reclaman el puerto 5556; el de audiolibros pierde | Es la causa de que el pendiente arrastrado de la descarga de audiolibros nunca se pudiera probar |
| `SEC-08` | Integridad de scripts *fail-open* y **0** ficheros `.sha256` para 92 scripts desplegados | `INV-CMN-02` está violada en los datos aunque se cumpla en la lógica |
| `SEC-11` | `NEVEN64.xll` se distribuye sin Control Flow Guard | `INV-BLD-02` incumplida en el artefacto mientras el test que la protege pasa, porque lee el `CMakeLists.txt` y no el binario |
| `COD-46` | El DOI de `Panko2016` apunta a otro trabajo | Es una tesis; la cita que sostiene la motivación del paper envía al lector a otro artículo |
| `PROD-08` | 12 de las 42 funciones de usuario de la librería R no tienen ayuda efectiva, una de ellas porque usa la forma de cadena, que es inerte | El asistente de funciones de Excel muestra "Exported Function" para esas 12. En cifra bruta son 63 de 93 definiciones, pero 26 son `.Studio.R` y 25 internas, que no necesitan ayuda (§2.2, §3.4) |

---

## 2. Layout real del repositorio frente a la documentación

El usuario señaló el síntoma con precisión: la documentación cita unas veces
`NEVEN\libreria\R\...` y `NEVEN\docs\ontologia\...`, y otras veces `src\docs\Paper\...` y
`src\TaskPane\audiobook.js`. Las dos familias no pueden ser ciertas a la vez. **El desajuste es
en sí mismo un hallazgo de calidad documental**, y es el que explica por qué el control previo
que el proyecto cree tener está inactivo.

### 2.1 Cuál es el layout verdadero · VERIFICADO

**El prefijo verdadero del código es `src\`.** El repositorio git está en la raíz del workspace
(`F:\ANTIGRAVITY\2026\NEVEN\.git`) y todo el proyecto C++/R/Julia/Python vive bajo
`F:\ANTIGRAVITY\2026\NEVEN\src\`. El árbol intermedio `NEVEN\NEVEN\...` **no existe**:
desapareció en el commit `951cfcb` ("refactor: reorganizar estructura de carpetas del
repositorio"). Método: enumeración directa del árbol y `git ls-files` (2.508 ficheros tracked),
sin asumir ningún prefijo documentado.

Es decir: `src\TaskPane\audiobook.js` y `src\docs\Paper\main.tex` son **rutas reales**, y
`NEVEN\libreria\R\...` y `NEVEN\docs\ontologia\...` son **rutas obsoletas**. Sus equivalentes
vivos son `src\libreria\R\` (63 ficheros `.R`) y `src\docs\ontologia\neven-core\` (los cuatro
YAML de invariantes).

Primer nivel real del workspace: `.agents\`, `.kiro\`, `.vscode\`, `android\`, `docs\`,
`external\`, `ontologia-fuentes\`, `src\`, más `.gitignore`, `MIGRACION.md` y
`NEVEN.code-workspace` (este último no tracked). Hay además un directorio `$reportPath\` en la
raíz, artefacto de una variable de PowerShell no expandida en algún script (`LAY-17`).

### 2.2 Referencias documentales desactualizadas · VERIFICADO

22 referencias apuntan a rutas que no existen. **Regla de recuento**, porque la tabla que las
respalda no tiene 22 filas: `00-layout-real.md` §4 tiene **25 filas**, 18 de ruta y 7 de cifra o de
nombre. De las 18 de ruta se excluyen las 2 del workflow de CI (van con `COD-19`/`MEJ4-01`, no con
la higiene documental) y la fila de `.kiro\steering\neven-project-context.md:58-66` cuenta como los
**siete** documentos que enumera: 18 − 2 − 1 + 7 = **22**. Las 7 filas de cifra se reducen a **6**
porque las dos del `README` son la misma afirmación. Quien implemente `B-10` necesita esta regla
para no encontrarse 25 filas y no saber cuáles quedan fuera.

Las que engañan activamente a un mantenedor:

| Ruta citada | Ruta real | Fichero y línea de la cita |
|---|---|---|
| `…\NEVEN\NEVEN\docs\ontologia\neven-core\neven-ontology-p1.yaml` | `src\docs\ontologia\neven-core\neven-ontology-p1.yaml` | `.kiro\hooks\validate-before-run.ps1:3` |
| `…\NEVEN\NEVEN\Ribbon\ribbon_connect.h` | `src\Ribbon\ribbon_connect.h` | `.kiro\hooks\validate-before-run.ps1:29` |
| `…\NEVEN\NEVEN\Ribbon\ribbon_ui.xml` | `src\Ribbon\ribbon_ui.xml` | `.kiro\hooks\validate-before-run.ps1:41` |
| `…\NEVEN\NEVEN\Build\Dist\NEVENRibbon.dll` | `src\Build\Dist\NEVENRibbon.dll` | `.kiro\hooks\validate-before-run.ps1:132` |
| `…\NEVEN\NEVEN\docs\ontologia\` | `src\docs\ontologia\` | `.kiro\steering\neven-project-context.md:90` |
| `NEVEN/docs/` y los siete documentos que enumera | `src\docs\Arquitectura\Arquitectura.md`, `src\docs\sops\coding-standards.md`, `src\docs\Contexto\Manual_de_mantenimiento.md`, `src\docs\Mantenimiento\TROUBLESHOOTING.md`, `src\docs\Estado\Estado_de_las_cosas.md`, `src\docs\Estado\Estado_del_arte.md`, `src\docs\Contexto\Contexto_v1.md` | `.kiro\steering\neven-project-context.md:58-66` |
| `NEVEN\libreria\R\R4XCL-*.R` | `src\libreria\R\R4XCL-*.R` | `.kiro\steering\neven-pre-cambios.md:142` |
| `NEVEN\Install\functions\*.json` | `src\Install\functions\*.json` | `.kiro\steering\neven-pre-cambios.md:143` |
| `NEVEN\TaskPane\neven_http_server.py` como destino de sincronización | la copia que coincide con producción es `src\startup\neven_http_server.py` | `.kiro\steering\neven-pre-cambios.md:144` |
| `NEVEN\TaskPane\*.js` | `src\TaskPane\*.js` | `.kiro\steering\neven-pre-cambios.md:145` |
| `Repo Git: …\NEVEN\NEVEN\` | el repo es el workspace, `F:\ANTIGRAVITY\2026\NEVEN\` | `MIGRACION.md:125` |
| `Ontologías: …\NEVEN\ONTOLOGIA\` | `ontologia-fuentes\` y `docs\ontologia\` | `MIGRACION.md:127` |
| árbol con `Core/`, `Common/`, `docs/` en primer nivel | todos bajo `src\` | `MIGRACION.md:36-62` |
| `cd …\NEVEN\NEVEN` + `.\build.ps1` | `cd …\NEVEN\src` | `MIGRACION.md:136-137` |

Y seis cifras que la documentación afirma y el repositorio contradice:

| Afirmación | Dónde | Medición real |
|---|---|---|
| 228 tests | `src\README.md:150, 176` y badge `:19` | **369 tests en 47 suites** (`rj2xcl_tests.exe --gtest_list_tests`) |
| 342 tests | `.kiro\steering\neven-project-context.md`, `src\docs\Paper\sections\06_conclusion.tex:11` | 369 |
| 357 tests | `src\docs\Mantenimiento\Aseguramiento_de_calidad.md:7`, `src\SECURITY.md:181` | 369 |
| `libreria/R/` con ~90 procedimientos en 32 ficheros | `.kiro\steering\neven-project-context.md` | **63 ficheros**, **93 definiciones de nivel superior**; de ellas 67 en los 37 no-`.Studio.R` y **42 funciones de usuario** en 30 ficheros (las tres bases, abajo) |
| sysimage de Julia de ~415 MB | `.kiro\steering\neven-project-context.md`; `src\docs\ontologia\neven-core\neven-ontology-p4.yaml:164` dice `"~414MB"` | `C:\NEVEN\neven_julia.dll` = 1.122.110.372 B (**1,04 GB**) |
| `neven_tests.exe` como nombre del binario | `src\docs\sops\testing-guide.md:26` | el objetivo es `rj2xcl_tests.exe` |

**Método de las cifras de la librería R, porque el patrón de medida cambia el resultado.** Las
definiciones se cuentan con `^[A-Za-z_.][A-Za-z0-9_.]*\s*(<-|=)\s*function`, anclado en columna 0 y
**aceptando las dos formas de asignación de R**. Un patrón que solo acepte `<-` devuelve 83 y 57, y
un patrón que acepte indentación cualquiera devuelve 121, contando funciones anidadas.

**Las tres bases de conteo de la librería R, porque este informe usa las tres y no son
intercambiables.** Toda afirmación del informe sobre la librería declara cuál usa.

| Base | Definiciones | Ficheros | Qué es | Cuándo se usa |
|---|---:|---:|---|---|
| **Bruta** | **93** | 63 | todo lo que define el directorio | Volumen de la librería; cifra del paper (`COD-48`) |
| **No-Studio** | **67** | 37 | excluye los 26 `.Studio.R`, que alimentan DataLab | Comparación con la documentación |
| **Usuario** | **42** | 30 | además de los `.Studio.R`, excluye las 25 definiciones de los siete ficheros internos `R4XCL-0-*` | **Impacto de producto**: es la población de `A-13` y de `PROD-08` |

Reparto de los internos: `R4XCL-0-Interno-1` 13, `Interno-2` 3, `Interno-3` 0, `NevenX` 5,
`Shared-WebView` 1, `UT-Ayuda` 1, `UT-InstalaPaqueterias` 2 = 25. Ninguno de los siete tiene una
sola asignación de descripción, y ningún usuario los busca en el asistente de funciones.

**Lo que ninguna de las tres bases es: el número de funciones que Excel registra.** El cargador
registra todo lo que encuentra en el directorio de funciones sin distinguir `.Studio.R`:
`src\Core\src\rj2xcl.cc:479-497` enumera `functions_directory\*.*`, llama a `ReadSourceFile` por
cada fichero que pase `ValidFile` (`src\Core\src\language_service.cc:492-510`, que compara solo la
extensión) y acto seguido hace `MapFunctions()` + `RegisterFunctions()` (`:502-503`). Lo que se
registra es lo que hay en `globalenv()` tras cargar el directorio de **producción**, que incluye 21
artefactos sin origen en el repositorio (§8.1); medirlo exige una sesión real de R (§9).

El proyecto tiene el mismo sesgo de patrón escrito en su propia ontología: el campo
`como_verificar` de `INV-LR-04`
(`src\docs\ontologia\neven-core\neven-ontology-p2.yaml:666`) busca solo `attr\(.*DialogosXCL` y por
tanto no ve las 21 asignaciones del mismo atributo escritas con el literal `"description"` (§3.4).
Cualquier cifra de este informe sobre la librería R va con su patrón declarado por esta razón.

### 2.3 Consecuencia operativa: el control previo está inactivo · VERIFICADO

`.kiro\hooks\validate-before-run.ps1` es la barrera que el steering declara como validación
previa a operaciones de riesgo. Sus `Test-Path` apuntan a `NEVEN\NEVEN\...`, rutas inexistentes,
así que **todas sus comprobaciones se saltan en silencio y el hook aprueba sin validar nada**.
Las invariantes que decía aplicar (`INV-RIBBON-01/02/03`, `INV-SR-01/02/05`) no tienen hoy
ninguna aplicación automática.

El segundo efecto es peor y es nuevo de esta auditoría (`MEJ4-01`): `Test-Path '.github'` en la
raíz devuelve **False**, y `git ls-files` sitúa `build-and-test.yml`, los dos `ISSUE_TEMPLATE` y
`PULL_REQUEST_TEMPLATE.md` bajo `src/.github/`. GitHub solo lee `.github/` en la raíz del
repositorio. El eje 2 había establecido que el workflow se dispara en `main`/`develop` siendo
`master` la rama real (`COD-19`); esta medición es anterior en la cadena causal: **corregir la
rama no habría cambiado nada, porque el fichero no se lee**.

### 2.4 Hallazgos de inventario

Son mediciones del reconocimiento, todas VERIFICADO, numeradas como en `00-layout-real.md` §7.

| ID | Hallazgo | Evidencia | Solape |
|---|---|---|---|
| `LAY-01` | Hook de validación inoperante | `.kiro\hooks\validate-before-run.ps1:3,29,41,132` | §2.3 |
| `LAY-02` | CI que no se dispara en la rama real | `src\.github\workflows\build-and-test.yml:5,7,13,54` | `COD-19`, `MEJ4-01` |
| `LAY-03` | Cuatro cifras distintas de tests en la documentación | §2.2 | `COD-20` |
| `LAY-04` | Copias divergentes de `neven_http_server.py` y regla de steering que señala la equivocada | `.kiro\steering\neven-pre-cambios.md:144` | `COD-36`, `PROD-29` |
| `LAY-05` | Tests Python sin runner declarado ni CI | `src\TaskPane\tests\` (18 ficheros), `src\tests\test_*.py` | `COD-22` |
| `LAY-06` | Contraseña literal de exportación PFX en fichero versionado | `src\TaskPane\Generate-Cert.ps1:42` (el literal, en la línea que lo convierte a `SecureString`), `:55, 56`; bloque equivalente en `src\Install\Install-NEVEN.ps1` (~1090-1100) | `SEC-10`, `SEC-18` |
| `LAY-07` | 95 MB de PDFs de libros comerciales tracked | `ontologia-fuentes\` (11 ficheros) | riesgo de licencia |
| `LAY-08` | Artefacto binario generado tracked | `src\Install\data\rag_index.duckdb` (12,3 MB) | — |
| `LAY-09` | Ficheros con nombre no ASCII tracked | `src\docs\Depuracion\An*lisis Cr*tico…`, `src\docs\NEvƎИ.docx` | — |
| `LAY-10` | Ficheros de bloqueo de Excel en el índice | `~$*.xlsx`, `~$*.xlsm` en `src\libreria\EJEMPLOS` | — |
| `LAY-11` | `android\local.properties` tracked (ruta local de la máquina) | `android\local.properties` | — |
| `LAY-12` | `android\` no aparece en la documentación de arquitectura pese a ser el subárbol con más ficheros tracked (955) | `src\docs\Arquitectura\` | `MEJ4-03` |
| `LAY-13` | Mojibake por doble codificación en la bitácora | `.kiro\contexto\CHAT.md`, `CHAT_LARGO.md` | — |
| `LAY-14` | Cabecera de `CHAT.md` desfasada | `.kiro\contexto\CHAT.md` (cabecera) | — |
| `LAY-15` | Sin rotación de logs: `C:\NEVEN\neven.log` en 119,6 MB | producción | `PROD-19`, `COD-38` |
| `LAY-16` | Residuos de build versionados | `src\build_log.txt`, `build_release.log`, `build_studio_fix.txt`, `cmake_config.log`, `cmake_config2.log`, `ribbon_build{,2,3}.txt` | `COD-54` |
| `LAY-17` | Directorio `$reportPath\` en la raíz: variable PowerShell no expandida | `F:\ANTIGRAVITY\2026\NEVEN\$reportPath\` | — |
| `LAY-18` | Auditoría previa sin estado de resolución registrado | `src\docs\INFORME_AUDITORIA.md` (36 hallazgos), `src\docs\audit\` (15 informes) | `COD-56`/§4.5, §5.5 |

### 2.5 Lo que la documentación sí dice bien · VERIFICADO

`C:\NEVEN\` como directorio de producción; `C:\NEVEN\startup\neven_http_server.py` como servidor
de producción en el puerto 5555 (`neven-config.json` → `TaskPane.port = 5555`,
`fallbackPort = 5556`); `C:\NEVEN\functions\` como destino de los `.R` y de los sidecars (63
`.R`, 29 `.json`). Y la ontología parsea sin error: los cuatro YAML de
`src\docs\ontologia\neven-core\` cargan con `yaml.safe_load`, con **62 invariantes únicas**.

---

## 3. Eje 1 — Calidad de la herramienta como producto

**Pregunta de fondo:** ¿un usuario de Excel puede instalar NEVEN, usarlo y recuperarlo cuando
falla, sin leer el código?

**Respuesta corta:** usarlo sí, cuando todo está en su sitio. Instalarlo desde cero y recuperarlo
cuando falla, no. El instalador cuida los tres motores con un preflight serio y deja fuera la
dependencia de la que cuelga toda la interfaz; y cuando un motor no conecta, el usuario recibe
`#¿NOMBRE?` en todas sus fórmulas sin ninguna indicación de qué pasó.

### 3.1 Los cuatro más graves

1. **`PROD-01` (Crítica)** — tres servicios reclaman el puerto 5556 y el de audiolibros es el que
   pierde. Es la causa de que la descarga de audiolibros nunca se pudiera comprobar (§7).
2. **`PROD-05` (Alta)** — el instalador nunca verifica ni instala el runtime de WebView2, del que
   dependen TaskPane, visor, editor, Pluto y Quarto.
3. **`PROD-06` (Alta)** — el template de configuración y el `neven-config.json` de producción
   tienen esquemas incompatibles, y los dos consumidores leen claves distintas.
4. **`PROD-08` (Alta)** — de las 42 funciones de usuario de la librería R, 30 tienen ayuda efectiva
   y **12 no**, así que el asistente de funciones de Excel les muestra "Exported Function" y
   "Argument". Medido sobre la base bruta son 63 de 93 definiciones, pero esa cifra incluye 26
   `.Studio.R` y 25 internas que no necesitan ayuda (§2.2, §3.4).

### 3.2 Hallazgos del eje 1

| ID | Sev. | Hallazgo | Evidencia | Fundamento |
|---|---|---|---|---|
| `PROD-01` | Crítica | Tres servicios reclaman el puerto 5556; `_handle_audiobook_start` da por vivo el servidor con un `connect_ex` a ciegas y el error de bind se pierde en `DEVNULL` | `src\AgentService\neven_ai_service.py:1207`; `src\Audiobook\neven_audiobook_server.py:29,376-387`; `src\Install\neven-config.template.json:56`; `src\startup\neven_http_server.py:2332-2357`; `src\TaskPane\audiobook.js:20,119,130-144` | VERIFICADO |
| `PROD-02` | Alta | El arreglo de nombres con espacios es correcto en lo esencial y deja tres defectos: doble decodificación, prefijo sin separador y *fallback* por nombre parcial | `src\Audiobook\neven_audiobook_server.py:91-125`; `src\TaskPane\audiobook.js:602-604` | VERIFICADO |
| `PROD-03` | Alta | El pipeline genera `.m4a` y el listado, la página del QR y el cliente buscan `.m4b` | `muxer\ffmpeg_muxer.py:27`; `pipeline.py:317,324`; `api\routes.py:1014,1112`; `neven_audiobook_server.py:122,170` | VERIFICADO |
| `PROD-04` | Alta | El módulo de audiolibros no forma parte del instalador, pero el servidor codifica su ruta absoluta y responde 404 si falta | `src\Install\Install-NEVEN.ps1` (0 ocurrencias de `Audiobook`/`ffmpeg`/`piper`); `src\startup\neven_http_server.py:2323` | VERIFICADO |
| `PROD-05` | Alta | WebView2 no se verifica ni se instala, mientras el código ya tiene los mensajes de fallo preparados | `src\Install\Install-NEVEN.ps1` (0 ocurrencias de `WebView2`); `src\Core\src\basic_functions.cc:497,1187,1341,1471,1502,1611` | VERIFICADO |
| `PROD-06` | Alta | Esquemas de configuración incompatibles: Studio lee `ai_profiles`, AgentService lee `AI.*`, que ya no existe en producción | `src\Install\neven-config.template.json`; `src\AgentService\neven_ai_service.py:733,737`; `src\startup\neven_http_server.py` | VERIFICADO |
| `PROD-07` | Alta | El diccionario documenta `NEVEN.py`, `NEVEN.q` y `NEVEN.v`, que no existen: los nombres reales son `NEVEN.P`, `NEVEN.Quarto`, `NEVEN.View` | `src\docs\Contexto\Diccionario_Funciones.md`; `src\Core\include\basic_functions.h:48,88`; `src\Install\neven-languages.json` | VERIFICADO |
| `PROD-08` | Alta | 31 definiciones declaran descripción y **30** lo hacen en la forma que el runtime consume. Sobre la base de usuario (42 definiciones, §2.2): **30 con ayuda efectiva, 12 sin ella** — 11 que nunca la declaran más una inerte. Sobre la base bruta son 63 de 93, cifra que incluye 26 `.Studio.R` y 25 internas. Detalle en §3.4 | 32 asignaciones en 25 ficheros (`src\libreria\R`); `src\startup\startup.r:51-77` (lectura); `src\ControlR\src\rinterface_common.cc:813-818, 834, 843-846` (consumo); `src\Core\src\excel_api_functions.cc:284-296` (registro y texto de respaldo) | VERIFICADO |
| `PROD-10` | Alta | Si un motor no conecta, sus funciones no se registran y no hay recuperación en sesión salvo reiniciar Excel | `src\Core\src\language_service.cc:749-757`; `src\Core\src\rj2xcl.cc:544-550,565-571`; mitigación parcial: `NEVEN.Status` (`basic_functions.cc:1152,1164`) | VERIFICADO |
| `PROD-09` | Media | Todas las funciones dinámicas se registran con la misma firma de 16 argumentos, sin validar la aridad real | `src\Core\src\excel_api_functions.cc:194,253,268,295-296` | VERIFICADO (firma) / HIPÓTESIS (desbordamiento con aridad > 22) |
| `PROD-11` | Media | El catálogo del TaskPane cubre 17 de los 63 ficheros `.R`; los nueve `GR_*.Studio.R` no tienen sidecar **y tampoco están desplegados en `C:\NEVEN\functions`** (§8), de modo que hoy no son DataLab vivo sino código del repositorio sin uso | `src\libreria\R` (63), `src\Install\functions` (28 sidecars, 17 ficheros referenciados); `src\docs\SIDECAR_FORMAT.md`; comparación nombre a nombre con producción | VERIFICADO |
| `PROD-12` | Media | `aliases.json` ocupa el directorio de sidecars sin ser uno: no tiene ninguno de los nueve campos requeridos | `src\Install\functions\aliases.json`; `C:\NEVEN\functions\aliases.json`; `src\docs\SIDECAR_FORMAT.md` | VERIFICADO (contenido) / HIPÓTESIS (efecto en el catálogo: no se localizó el cargador) |
| `PROD-13` | Media | Segundo renderizador de slots, completo y paralelo, con su propia construcción de tabla y un `innerHTML` sobre contenido del motor | `src\TaskPane\taskpane.html:7244-7301` (`_excelRenderSlots`), `:7291`, orden de preferencia en `:7204-7225` | VERIFICADO |
| `PROD-15` | Media | 25 claves de función existen solo en inglés; la versión española del catálogo es la incompleta | `src\TaskPane\lang\es.js` (362 claves) vs `en.js` (390) | VERIFICADO; cobertura real de i18n en la interfaz: HIPÓTESIS |
| `PROD-16` | Media | `INV-SR-01` violada: bytes > 127 en código activo de los tres scripts de arranque, y mojibake en un `warning()` que llega al usuario | `src\startup\startup.r` (8 bytes > 127 fuera de comentarios, mojibake en `:85` y `:103`), `startup.jl` (10), `startup.py` (3) | VERIFICADO |
| `PROD-17` | Media | `INV-LR-02` violada: `library()` de nivel superior en 30 ficheros de librería, 58 ocurrencias | `src\libreria\R\R4XCL-AD-TextMining.R`, `R4XCL-GR-Interactivos.R`, `R4XCL-RG-Lineal.R` y 27 más | VERIFICADO |
| `PROD-18` | Media | Sin `/utf-8` en la compilación y 1.118 bytes > 127 en literales de mensaje que se decodifican con `CP_UTF8` | `src\CMakeLists.txt:18`; `src\Core\src\basic_functions.cc`; `src\Core\include\type_conversions.h:83,93` | VERIFICADO (flag) / HIPÓTESIS (mojibake real en celda) |
| `PROD-19` | Media | Sin rotación de logs: `neven.log` en 119,6 MB, `C:\NEVEN\logs\` vacío y once ficheros de log sueltos en la raíz de producción | búsqueda sin coincidencias en `src\Common`, `src\Core`; medición en `C:\NEVEN\` | VERIFICADO |
| `PROD-20` | Media | El servidor de audiolibros se publica en toda la red local sin autenticación | `src\Audiobook\neven_audiobook_server.py:41,376-377`; `src\Audiobook\api\routes.py:243,288,1202` | VERIFICADO |
| `PROD-21` | Media | Las carpetas de trabajo del módulo no son las que sugiere su nombre (`C:\NEVEN\output`, no `C:\NEVEN\Audiobook\output`), y nada lo documenta | `src\Audiobook\neven_audiobook_server.py:48-52,116`; comprobado en disco | VERIFICADO |
| `PROD-24` | Media | El paper sitúa las funciones del usuario en `Documents\NEVEN\functions\`; el valor real y configurado es `C:\NEVEN\functions` | `src\docs\Paper\sections\02_architecture.tex:60,172`; `03_viewer_extensibility.tex:68,83` | VERIFICADO |
| `PROD-28` | Media | Prerrequisitos no declarados del módulo de audiolibros: `ffmpeg`, `flask`/`flask_cors`, `qrcode`, modelos TTS | `src\Audiobook\muxer\ffmpeg_muxer.py`; `neven_audiobook_server.py:25-26,131`; `download_model.bat` | VERIFICADO |
| `PROD-29` | Media | Cinco copias de `neven_http_server.py` en el repositorio, con cinco hashes distintos; las dos de `Dist\` desfasadas respecto a la canónica | `src\startup\`, `src\TaskPane\`, `src\ControlPython\startup\`, `src\Install\Dist\startup\`, `src\Install\Dist\TaskPane\` | VERIFICADO (hashes medidos) |
| `PROD-14` | Baja | `showToast` definida dos veces dentro del mismo fichero | `src\TaskPane\taskpane.html:2336,2657` | VERIFICADO |
| `PROD-22` | Baja | Código muerto y duplicado en el módulo de audiolibros: `create_download_route` sin invocadores y un segundo servidor completo que no recibió el arreglo | `src\Audiobook\api\routes.py:1296,1303,1449`; `src\Audiobook\main_server.py:13,236,282` | VERIFICADO |
| `PROD-23` | Baja | Nombres heredados visibles al usuario y en la interfaz | `src\Core\include\basic_functions.h` (`RJ_Version`, `RJ_ButtonCallback`, `RJ_ContextSwitch`, `RJ_UpdateFunctions`); 3 menciones en `taskpane.html`, 1 en `ribbon_ui.xml`; `excel_api_functions.cc:236` | VERIFICADO; hallazgo previo `DOC-BAJ-001` sigue **ABIERTO** |
| `PROD-25` | Baja | Dos paneles huérfanos en el HTML: `id="sql"` sin botón y `excel-analysis` comentado con su panel y su JavaScript vivos | `src\TaskPane\taskpane.html:384,373,861` | VERIFICADO |
| `PROD-27` | Baja | Prosa del README: índice de relleno 10,0, frases de 39,5 palabras de media. Las dos guías de usuario, en cambio, puntúan 0,0 | `src\README.md:7`; `src\docs\Mantenimiento\TROUBLESHOOTING.md` (6,8) | VERIFICADO (`slop_check.py`) |
| `PROD-26` | Informativa | `SIDECAR_FORMAT.md` contiene directivas para un agente y declara una ruta de despliegue falsa (`C:\NEVEN\libreria\R\`) | `src\docs\SIDECAR_FORMAT.md` (secciones "Ubicacion de Archivos" y "Notas para el Agente IA") | VERIFICADO; reportado, no obedecido |

### 3.3 Lo que funciona bien, verificado

Conviene no romperlo al arreglar lo anterior.

- **Preflight de motores del instalador:** `Find-R` (L136), `Find-Julia` (L200), `Find-Python`
  (L274) con detección por PATH y registro, exclusión del stub de WindowsApps, comprobación de
  versión mínima, enlace de descarga y pausa interactiva (`Show-PreflightSummary`, L383-446), más
  la junction de Quarto (`New-QuartoJunction`, L938-962).
- **`INV-RIBBON-01` se cumple:** los 7 callbacks de `src\Ribbon\ribbon_ui.xml` tienen entrada en
  `src\Ribbon\ribbon_connect.h`. No hay botón de la cinta sin conectar.
- **Sidecars sanos:** los 28 parsean, no hay `id` duplicado, ningún campo `file` lleva ruta y
  todos resuelven a un fichero existente (`INV-SJ-01`, `02`, `04`, `05`).
- **Dispatcher limpio:** `src\libreria\R\R4XCL-0-NevenX.R` cumple `INV-NX-01` (0 bytes > 127, sin
  BOM) y `INV-NX-02` (llaves balanceadas).
- **Vigilancia de arranque:** limpieza de zombies antes de conectar, guard de doble
  inicialización (`rj2xcl.cc:617-625`), `WatchdogTimer` por motor
  (`src\Common\NevenBackgroundConnector.cc:94-378`) y `NEVEN.Status` para consultar la salud.
- **Guías de usuario:** `Guia_usuario.md` y `Guia_inicio_rapido.md` con índice de relleno 0,0.

### 3.4 `PROD-08` en detalle: la convención real de la ayuda de funciones · VERIFICADO

`PROD-08` es el hallazgo de producto con más impacto visible, y una primera medición de esta
auditoría lo cuantificó mal por usar un patrón que solo aceptaba una de las dos sintaxis de R y uno
de los dos nombres con que el proyecto escribe el atributo. La medición corregida, y lo que apareció
al corregirla, es lo siguiente.

**Cuántas funciones declaran descripción.** 32 asignaciones de nivel superior en 25 de los 63
ficheros, que cubren 31 de las 93 definiciones:

| Forma escrita | Asignaciones | Ficheros |
|---|---:|---:|
| `attr(fn, "description") = …` | 21 | 15 |
| `attr(fn, DialogosXCL$Descripcion) = …` | 11 | 11 |
| **Total** | **32** | **25** |

Las dos formas son **la misma**: `DialogosXCL$Descripcion` vale literalmente `"description"`
(`src\libreria\R\R4XCL-0-Interno-2.R:242`). Hay además 6 asignaciones de `attr(fn, "category")`.
Las 32 asignaciones cubren 31 nombres distintos porque `R4XCL-FX-Aleatorios.R:229` repite
`FX_AleatorioUniforme` donde el fichero define `FX_AleatorioNormal` en `:167`: esa función se queda
sin descripción y la del uniforme se asigna dos veces. Los 25 ficheros que declaran son **todos** de
función de usuario: cero asignaciones en los 26 `.Studio.R` y cero en los siete internos, de modo
que los 31 nombres con descripción están todos dentro de la base de usuario de §2.2.

**El valor tiene que ser una `list()`, y una de las 32 no lo es.** El puente de R solo lee el
atributo si llega como array (`src\ControlR\src\rinterface_common.cc:813-818`, que exige
`ValueCase::kArr`). El primer elemento se convierte en la descripción de la función (`:834`) y los
siguientes se asignan a los argumentos **por posición**, no por nombre (`:843-846, 854`), de modo
que los nombres del `list()` son documentación para quien lee el `.R` y el orden es lo que importa.
Consecuencia: `R4XCL-UT-Pivote.R:336`, la única que asigna una cadena simple, **no surte efecto** y
`DB_Recodificar` muestra el texto genérico igual que si no tuviera atributo. Descripciones
efectivas: **30 nombres**.

**La función se registra igual, con o sin atributo.** `src\Core\src\excel_api_functions.cc:284-292`
pone `"Exported Function"` cuando la descripción está vacía y `:294-296` pone `"Argument"` por cada
argumento sin texto. El registro no depende del atributo.

**Universo relevante, sobre la base de usuario de §2.2.** De los 37 ficheros no-`.Studio.R`, 25
declaran descripción y 12 no; de esos 12, siete son internos (`R4XCL-0-Interno-1/2/3`,
`R4XCL-0-NevenX`, `R4XCL-0-Shared-WebView`, `R4XCL-0-UT-Ayuda`, `R4XCL-0-UT-InstalaPaqueterias`) y
cinco exponen funciones de usuario sin ninguna ayuda: `R4XCL-AD-NonParRolCor.R`,
`R4XCL-BD-ObtieneDatos.R`, `R4XCL-DS-Wooldridge.R`, `R4XCL-GR-Mapa.R`,
`R4XCL-NEVEN-pluto-read.R`. El impacto, medido donde importa:

| Base | Definiciones | Con ayuda efectiva | Sin ayuda | Lectura |
|---|---:|---:|---:|---|
| **Usuario** (30 ficheros) | 42 | **30** | **12** | 11 que nunca declaran el atributo más la inerte de `R4XCL-UT-Pivote.R:336`. **Es el alcance de `A-13`(d)** |
| No-Studio (37 ficheros) | 67 | 30 | 37 | las 12 anteriores más las 25 internas, que no se buscan en el asistente |
| Bruta (63 ficheros) | 93 | 30 | 63 | añade los 26 `.Studio.R` |

El hallazgo es real en las tres bases; su magnitud, medida sobre la población en la que el plan
trabaja, es **12**, no 63. Las cifras brutas se mantienen porque son las comparables con la
documentación y con el paper, siempre con esta nota al lado.

**Los `.Studio.R` sí aparecen en el asistente de funciones, y eso es una decisión pendiente, no un
"fuera de alcance".** Decir que no se documentan porque alimentan DataLab describe la intención, no
el comportamiento: están desplegados en `C:\NEVEN\functions` (§8.1, salvo los nueve `GR_*`), el
cargador no distingue su extensión (§2.2) y por tanto sus 26 definiciones se registran y se listan
en el asistente con el texto de respaldo, igual que las demás. Hay dos salidas coherentes y hay que
elegir una por escrito: **documentarlos** como funciones de celda, o **dejar de desplegarlos** al
directorio de funciones y servirlos solo a DataLab. La segunda es la que encaja con su propósito
declarado, y es un cambio de empaquetado que pertenece a `B-08`, no a `A-13`. Mientras no se decida,
26 funciones que nadie documenta están visibles en la interfaz de descubrimiento del producto.

**Lo que esto cambia en el plan.** `A-13`(d) no puede mandar "añadir `attr(fn,"description")`" sin
más: tiene que extender la convención `list()` que 30 funciones ya usan, o introduciría una segunda
convención incompatible y un test de `B-04` escrito con el patrón equivocado marcaría esas 30 como
incumplidoras. La redacción propuesta para `INV-LR-04` (plan §5.1) recoge la convención real.

---

## 4. Eje 2 — Calidad del código

**Pregunta de fondo:** ¿este código se puede mantener, probar y extender sin romperlo?

**Respuesta corta:** mantener y extender, sí, con esfuerzo. Probarlo, no: lo que hay de red de
seguridad no se ejecuta automáticamente y está concentrado donde menos hace falta.

### 4.1 Volumen medido

| Lenguaje | Ficheros | Líneas |
|---|---:|---:|
| `.html` | 323 | 71.184 |
| `.py` | 115 | 58.306 |
| `.cc` | 127 | 43.320 |
| `.h` | 140 | 24.014 |
| `.js` | 288 | 21.871 |
| `.R` | 98 | 17.751 |
| `.jl` | 37 | 5.662 |
| `.ps1` | 19 | 4.400 |

Excluye `Build\`, `Dist\`, `_deps\`, `Releases\`, `__pycache__\`. Incluye código generado de
Protobuf (`variable.pb.h` 10.240 líneas, `variable.pb.cc` 8.794).

Tests reales: **369 en 47 suites**, de los que **133 (36 %) están en `sandbox_tests.cc`**.
`basic_functions.cc` tiene 4.583 líneas y 4 tests; los 17.751 de R tienen 1.

### 4.2 Los cuatro más graves

1. **`COD-01`** — `xlAutoOpen` ejecuta todo el arranque sin guarda de excepciones en la frontera C
   del XLL. Una excepción al leer la configuración mata Excel sin diagnóstico.
2. **`COD-19` + `COD-22` + `COD-23`** — nada protege el código de `master` automáticamente: su CI no
   se dispara porque el workflow no se lee desde ahí (`MEJ4-01`; en `main` sí se leía y fallaba),
   410 funciones de test Python no tienen runner, y diez
   subsistemas C++ no tienen un solo test.
3. **`COD-36` + `COD-37`** — cuatro copias divergentes del servidor HTTP en el repositorio, y la
   canónica es un monolito de 4.901 líneas con un `do_GET` de 400 y 65 endpoints despachados por
   cadena de `if/elif`.
4. **`COD-40`** — `taskpane.html` tiene 6.053 líneas de JavaScript inline (73 % del fichero) con
   114 asignaciones a `.innerHTML` y 56 `fetch(`.

### 4.3 Hallazgos del eje 2

**Altos**

| ID | Hallazgo | Evidencia | Fundamento |
|---|---|---|---|
| `COD-01` | Los cuatro exports del XLL no tienen `try`/`catch`; una excepción que cruce `extern "C" __stdcall` es comportamiento indefinido | `src\Core\src\rj2xcl.cc:619-651, 653-668, 670-686, 690-707` | VERIFICADO |
| `COD-14` | Cero flags de nivel de aviso en los 12 `CMakeLists.txt`; se compila con `/W1` y además se silencian cuatro familias de avisos | `src\CMakeLists.txt:12`; `src\Ribbon\CMakeLists.txt:13` (`midl /W1`, no es C++) | VERIFICADO |
| `COD-19` | El CI nunca se dispara en la rama real | `src\.github\workflows\build-and-test.yml:5,7,54`; `git rev-parse --abbrev-ref HEAD` → `master` | VERIFICADO |
| `COD-22` | 410 funciones de test Python sin runner declarado, fuera de CMake y del CI; no hay `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini` ni `conftest.py` | `src\TaskPane\tests\` (18 ficheros, 331 tests), `src\tests\test_*.py` (3), más 7 runners `.R` | VERIFICADO |
| `COD-23` | Diez subsistemas sin ningún test, incluidos `ViewerManager`, `RibbonService`, `CrashHandler` y las 1.522 líneas de `ribbon_connect.h` | búsqueda de nombre de clase en los 33 `.cc` de `src\tests` | VERIFICADO |
| `COD-36` | Cuatro copias divergentes de `neven_http_server.py` tracked y tres de `rag_engine.py`; la regla de steering apunta a la copia equivocada | `src\startup\`, `src\TaskPane\`, `src\ControlPython\startup\`, `src\Install\scripts\`; `.kiro\steering\neven-pre-cambios.md:144` | VERIFICADO (hashes) |
| `COD-37` | El servidor canónico es un monolito: 4.901 líneas, 65 endpoints, `do_GET` de 400 líneas, `_handle_ai_chat_impl` de 461 | `src\startup\neven_http_server.py:645,1075,1816` | VERIFICADO |
| `COD-40` | 6.053 líneas de JS inline en `taskpane.html` (73 %), 114 `.innerHTML`, 56 `fetch(`, 25 `onclick=` | `src\TaskPane\taskpane.html` (8.263 líneas, 10 bloques `<script>`) | VERIFICADO |
| `COD-46` | El DOI de `Panko2016` apunta a otro trabajo de la misma revista | `src\docs\Paper\references.bib` y `arxiv-submission\references.bib` | VERIFICADO con herramienta; **requiere confirmación del autor** |

**Medios**

| ID | Hallazgo | Evidencia | Fundamento |
|---|---|---|---|
| `COD-02` | El zombie cleanup usa `taskkill /IM`, que mata los motores de otras instancias de Excel | `src\Core\src\rj2xcl.cc:457-476` | VERIFICADO (código) / HIPÓTESIS (efecto con dos instancias) |
| `COD-05` | `ScheduleDelayedUpdate()` nunca se invoca y duplicaría el timer de telemetría; el miembro estático `instance_` nunca se lee ni se escribe | `src\Core\src\rj2xcl.cc:60,538-558`; `src\Core\include\rj2xcl.h:60,193` | VERIFICADO |
| `COD-06` | Carrera de datos en `ViewerManager`: `available_` cruza hilos sin protección, igual que `max_viewers_` y `max_memory_mb_` | `src\Common\ViewerManager.h:188,211-212`; `ViewerManager.cc:99,123,139,144,146` | VERIFICADO |
| `COD-07` | `TerminateThread` sobre el hilo STA de WebView2 en el cierre | `src\Common\ViewerManager.cc:155-166` | VERIFICADO |
| `COD-08` | Cinco funciones de más de 180 líneas, entre ellas `RJ2XCL_Engine::Init` (187) y `RJ_IA_Contexto` (371) | `src\Core\src\rj2xcl.cc:350`; `basic_functions.cc:1601`; `convert.cc:60`; `julia_interface.cc:34,266`; `sim_main.cc:280` | VERIFICADO |
| `COD-10` | `control_julia.cc` y `control_python.cc` comparten 98 líneas idénticas de bucle de mensajes y despacho | `src\ControlJulia\src\control_julia.cc`, `src\ControlPython\src\control_python.cc`, `src\ControlR\src\controlr.cc` | VERIFICADO |
| `COD-11` | El estándar de código no describe el código: 596 de 663 métodos son `PascalCase` donde el documento pide `snake_case`; 123 de 267 ficheros no siguen la convención de nombre | `src\docs\sops\coding-standards.md` | VERIFICADO |
| `COD-15` | `rapidcheck` anclado a `GIT_TAG master`; Protobuf y WebView2 se descargan por URL sin `URL_HASH` | `src\CMakeLists.txt:34-37,52-57,70-79` | VERIFICADO |
| `COD-16` | `file(GLOB)` sin `CONFIGURE_DEPENDS` en el objetivo más grande | `src\Core\CMakeLists.txt:2`; `src\NEVEN-SIM\CMakeLists.txt:10`; `src\NEVEN-SIM\tests\CMakeLists.txt:7` | VERIFICADO |
| `COD-24` | `MockExcelBridge` devuelve siempre `xlretSuccess` y no escribe en `operRes`: no puede probar rutas de error ni conversión de vuelta | `src\Core\include\MockExcelBridge.h` | VERIFICADO |
| `COD-25` | Cero tests de frontend para unas 30.000 líneas de JS/HTML | `git ls-files` sin `*.test.js`, `*.spec.js` ni configuración de runner | VERIFICADO |
| `COD-27` | `INV-LR-02` violada en 30 de 63 ficheros; un `library()` fallido tumba el `source()` completo del fichero | lista en `02-notas-codigo.md` §5 | VERIFICADO |
| `COD-28` | `INV-LR-04`: 12 de los 37 ficheros no-Studio no asignan descripción en ninguna de sus dos formas, y los cinco que exponen funciones de usuario no tienen ningún `attr(`. Los 26 `.Studio.R` no la necesitan (§3.4) | `R4XCL-AD-NonParRolCor.R`, `R4XCL-BD-ObtieneDatos.R`, `R4XCL-DS-Wooldridge.R`, `R4XCL-GR-Mapa.R`, `R4XCL-NEVEN-pluto-read.R`, más siete internos `R4XCL-0-*` | VERIFICADO (conteo y mecanismo) / HIPÓTESIS (qué ve el usuario en el asistente, §9) |
| `COD-29` | 34 de 63 ficheros `.R` sin ningún `tryCatch`: un error rompe el contrato de retorno `R4XCL_` | `src\libreria\R` | VERIFICADO |
| `COD-30` | Los diagnósticos estadísticos son ramas opcionales de `TipoOutput`, no parte del informe; 0 ocurrencias de `shapiro.test`, `dwtest`, `confint`, `cooks.distance`, `resettest`, `p.adjust`, `Box.test`, `kpss` y de cualquier tamaño de efecto estandarizado | `src\libreria\R\R4XCL-RG-Lineal.R:69-156`; conteo sobre los 63 `.R` | VERIFICADO (skill `statistical-analysis`) |
| `COD-31` | `vcovHC(type = "HC")` es HC0; para 30-200 filas la recomendación es HC3 | `src\libreria\R\R4XCL-RG-Lineal.R:124` | VERIFICADO |
| `COD-33` | Ningún "módulo J4XCL" es un módulo de Julia: cero `module`, un solo `export` en el directorio | `src\libreria\JULIA\*.jl` (9 ficheros) | VERIFICADO |
| `COD-34` | `J4XCL-OP-Optimizacion.jl`: 320 líneas, una función, y `Parametro` significa tasa de aprendizaje o tolerancia según la rama, sin documentarlo | `src\libreria\JULIA\J4XCL-OP-Optimizacion.jl:28-30,32,145` | VERIFICADO (skill `metaheuristic-optimization`, que **no aplica**: los métodos son deterministas) |
| `COD-38` | Observabilidad incoherente: 15 `print(` frente a 9 usos de `logging`, y dos `except:` desnudos | `src\startup\neven_http_server.py` | VERIFICADO |
| `COD-39` | `datalab_handler.py` no existe junto al servidor canónico; su origen real es `src\ControlPython\startup\` | `src\startup\` (ausente), `src\ControlPython\startup\datalab_handler.py`, `C:\NEVEN\startup\datalab_handler.py` | VERIFICADO |
| `COD-41` | `INV-TF-01` **PARCIAL**: la función única existe, pero hay cuatro renderizadores paralelos y un par duplicado para SQL | `taskpane.js:476,1219`; `taskpane.html:5211,5327,7243`; `chart-gallery.js:1646`; `datalab.js:1528` | VERIFICADO |
| `COD-42` | `showToast` definida tres veces, con tres firmas | `audiobook.js:43`; `taskpane.html:2336,2657` | VERIFICADO |
| `COD-43` | Cuatro librerías de CDN se cargan dos veces, entre ellas Plotly (~3,5 MB) | `src\TaskPane\taskpane.html` (23 etiquetas para 18 recursos) | VERIFICADO |
| `COD-45` | Siete dependencias de CDN sin `integrity` y sin copia local: sin red, el TaskPane pierde gráficos, mapas y fórmulas | `src\TaskPane\taskpane.html` | VERIFICADO |
| `COD-47` | El paper afirma 342 tests; el binario reporta 369 | `src\docs\Paper\sections\06_conclusion.tex:11` | VERIFICADO |
| `COD-48` | "70 procedimientos Julia" frente a 60 definiciones medidas; "más de 200 funciones numéricas" no es verificable desde el repositorio. La afirmación paralela sobre R (más de 70) **depende de la base de conteo** (§2.2): se sostiene con la base bruta (93 definiciones en los 63 `.R`) y con la no-Studio (67), y **no** con la base de usuario (42). El paper debe declarar cuál cuenta; lo defendible es la bruta, diciéndolo | `src\docs\Paper\sections\06_conclusion.tex:11`; `src\libreria\JULIA`, `src\libreria\R` | VERIFICADO lo medible / NO VERIFICABLE las 200 |

**Bajos e informativos**

Fundamento de los 21: **todos VERIFICADO**, salvo `COD-21`, que está declarado NO VERIFICADO con su
motivo en §9.

| ID | Sev. | Hallazgo | Evidencia |
|---|---|---|---|
| `COD-03` | Baja | `xlAutoFree12` desreferencia su argumento sin comprobar nulo | `src\Core\src\rj2xcl.cc:670-671` |
| `COD-04` | Baja | `xlAddInManagerInfo12` usa estáticos mutables compartidos | `src\Core\src\rj2xcl.cc:691` |
| `COD-09` | Baja | Seis `atoi()` sin validación, dos de ellos en el parseo de versión de R | `controlr.cc:614`; `r_engine_loader.cc:174,186`; `rinterface_win.cc:134`; `ribbon_connect.h:190,692` |
| `COD-12` | Baja | `coding-standards.md` duplicado byte a byte | `src\docs\sops\` y `src\docs\Plan_trabajo\` |
| `COD-13` | Baja | Cobertura Doxygen desigual: `rj2xcl.h` documenta 1 de 28 miembros; `ribbon_connect.h`, `RuntimeLoader.h` y `GCMonitor.h`, ninguno | `src\Core\include\rj2xcl.h`; `src\Ribbon\ribbon_connect.h`; `src\Common\RuntimeLoader.h`, `GCMonitor.h` |
| `COD-17` | Baja | `include_directories()` global en lugar de por objetivo, con estilo mixto en el mismo build | `src\CMakeLists.txt:27-29,84` vs `src\Core\CMakeLists.txt:5` |
| `COD-18` | Baja | `build.ps1` pasa `CMAKE_BUILD_TYPE` a un generador multiconfiguración, que lo ignora | `src\build.ps1:72,77` |
| `COD-32` | Baja | 9 de 10 `GR_*.Studio.R` de `deprecated\` son copias byte a byte de los vivos, y `GR_EjemploBasico.Studio.R` **solo** existe allí | `src\TaskPane\deprecated\GR_DataLab_migrated\` |
| `COD-35` | Baja | Cero `@assert`, `error(` o `throw` en los 9 `.jl`: ninguna función valida dimensiones ni tipos | `src\libreria\JULIA`; `J4XCL-OP-Optimizacion.jl:191` mezcla error y datos |
| `COD-44` | Baja | Cache-busting manual con cuatro formatos distintos de sello, y un fichero sin ninguno | `src\TaskPane\taskpane.html` |
| `COD-49` | Baja | 8 entradas del `.bib` definidas y nunca citadas; ninguna clave citada sin definir | `src\docs\Paper\references.bib` |
| `COD-50` | Baja | Tres árboles del paper coexisten y `05_discussion.tex` divergió entre dos de ellos | `src\docs\Paper\sections\`, `arxiv-submission\sections\`, `sections_old\` |
| `COD-53` | Baja | Deuda declarada muy baja (28 marcadores `TODO`/`FIXME` en todo `src`), pero la deuda real de este informe no está marcada en ningún sitio | `git grep` sobre `src` |
| `COD-54` | Baja | Residuos de build versionados | `src\build_log.txt`, `build_studio_fix.txt`, `ribbon_build{,2,3}.txt` |
| `COD-55` | Baja | Directorios muertos versionados; los dos `legacy\*.cpp`, en cambio, están excluidos del build a propósito y documentado | `src\TaskPane\deprecated\`, `src\docs\_legacy\RJ2XCLModule_2018\` |
| `COD-20` | Inf. | Recuento real de tests (369/47) frente a cuatro cifras documentadas, y distribución muy desigual | `rj2xcl_tests.exe --gtest_list_tests` |
| `COD-21` | Inf. | **No se comprobó que los tests pasen**, con motivo declarado (§9) | binario del 2026-10-20 con 5 fuentes posteriores |
| `COD-26` | Inf. | `INV-NX-01` e `INV-NX-02` se cumplen en el dispatcher; los 54 ficheros de librería con bytes > 127 **no** violan ninguna invariante | `src\libreria\R\R4XCL-0-NevenX.R` |
| `COD-51` | Inf. | Los controles anti-artefacto-IA del proyecto **se cumplen**: 0 campos `note`, 0 puntos dentro de `\paragraph{}`, em-dashes de prosa ≈ 0, números de lista coherentes, `bib_lint` sin errores | `src\docs\Paper\**` |
| `COD-52` | Inf. | Instrucciones dirigidas a agentes embebidas en ficheros del repositorio, todas legítimas | §11 |
| `COD-56` | Inf. | Encoding de la documentación correcto (4 de 129 `.md` con algún marcador de mojibake); única incoherencia: `testing-guide.md` tiene BOM y sus dos vecinos no | `src\docs\sops\` |

### 4.4 Veredicto sobre las 62 invariantes

De las 62 invariantes de `src\docs\ontologia\neven-core\neven-ontology-p1..p4.yaml`, esta
auditoría emitió veredicto con evidencia sobre **38**: 28 cumplen, 5 están violadas y 5 se
cumplen pero son insuficientes o parciales. Las 24 restantes quedan **sin veredicto**, declarado
como tal en lugar de inventado.

**Violadas**

| Invariante | Dónde está definida | Estado | Evidencia |
|---|---|---|---|
| `INV-LR-02` | `p2.yaml:639` | **VIOLADA** | `library()` de nivel superior en 30 de 63 ficheros (`COD-27`, `PROD-17`) |
| `INV-LR-04` | `p2.yaml:660` | **VIOLADA, y mal redactada** | Violada: 12 de los 37 ficheros no-Studio no asignan el atributo, y la que lo asigna como cadena es inerte (`COD-28`, `PROD-08`, §3.4). Mal redactada por dos cosas distintas del mecanismo, que **sí existe**: afirma que "sin el attr la función no aparece en Excel", y el registro es independiente del atributo (`excel_api_functions.cc:284-292`); y su `como_verificar` (`p2.yaml:666`) busca solo `attr\(.*DialogosXCL`, con lo que no ve las 21 asignaciones escritas con el literal `"description"` |
| `INV-SR-01` | `p1.yaml:395` | **VIOLADA** | bytes > 127 en código activo de `startup.r`, `startup.jl`, `startup.py` (`PROD-16`) |
| `INV-CMN-02` | `p1.yaml:347` | **VIOLADA en producción** | 0 ficheros `.sha256` para 92 scripts desplegados; verificación *fail-open*; es SHA-256, no HMAC (`SEC-08`) |
| `INV-BLD-02` | `p4.yaml:177` | **VIOLADA en el artefacto** | `NEVEN64.xll` con `DllCharacteristics = 0x0160`, sin CFG, en repo y en producción (`SEC-11`) |

**Cumplen pero no bastan, o se cumplen a medias**

| Invariante | Estado | Evidencia |
|---|---|---|
| `INV-TF-01` | **PARCIAL** | `buildSlotElement` está definida una vez; la exclusividad declarada no existe (`COD-41`, `PROD-13`, `SEC-07`) |
| `INV-LR-03` | **PARCIAL** | el contrato `R4XCL_` se respeta en la ruta feliz; 34 ficheros no tienen `tryCatch` que lo garantice ante error (`COD-29`) |
| `INV-CR-03` | **PARCIAL** | la validación de versión de R existe, pero el parseo con `atoi` no distingue fallo de `0` (`COD-09`) |
| `INV-SB-03` | **CUMPLE y es insuficiente** | la validación es por prefijo de sentencia; un `SELECT` de DuckDB alcanza el sistema de ficheros (`SEC-05`, `SEC-06`) |
| `INV-TEST-01` | **CUMPLE y es insuficiente** | comprueba que los flags estén escritos en el `CMakeLists.txt`, no que estén en el binario: pasa mientras `INV-BLD-02` está incumplida (`SEC-11`) |

**Cumplen, con evidencia**

`INV-CORE-01`, `INV-CORE-02`, `INV-CORE-03` (`rj2xcl.cc:457-502, 617-662`); `INV-RIBBON-01`;
`INV-NX-01`, `INV-NX-02`, `INV-NX-03`, `INV-NX-04`; `INV-SJ-01` a `INV-SJ-05`; `INV-CMN-03`
(`MessageValidator.cc:30-56` acota la longitud declarada antes de deserializar); `INV-CJ-03`;
`INV-SB-02`, `INV-SB-04`, `INV-SB-05`; `INV-AS-03` (cumple, con el conflicto de puerto de
`PROD-01`); `INV-CP-03` (cumple donde aplica; no cubre el puente del visor, `SEC-15`);
`INV-BLD-01`, `INV-BLD-03`; `INV-TEST-02`; `INV-INS-01` (en HEAD), `INV-INS-04`; `INV-SR-05`;
`INV-TF-03` (parcial: los ficheros están en UTF-8, no se auditaron los scripts de copia);
`INV-TF-04`.

**Dos huecos de la ontología, que no son violaciones**

Ninguna de las 62 invariantes cubre (a) las ACL del directorio de producción `C:\NEVEN\`, que es
la vía por la que una cuenta local cualquiera puede ejecutar código en la sesión de otra
(`SEC-09`), ni (b) el **sandbox**, que es el control que `src\SECURITY.md` presenta como
principal (`SEC-23`). El plan de trabajo propone añadir invariantes para ambos, además de para
la autenticación de la API local y para la fuente única de cada artefacto desplegado.

### 4.5 Estado de los hallazgos de código de la auditoría previa

`src\docs\INFORME_AUDITORIA.md` (v1.0, salud 6,0/10, 36 hallazgos) **no usa identificadores
estables**: una extracción por patrón devuelve 0 coincidencias, de modo que el emparejamiento uno
a uno no es posible. Lo que sí se pudo verificar:

| Hallazgo previo | Estado | Evidencia |
|---|---|---|
| `CM-BAJ-004` — `AddTrustedSignature`/`EvaluateScript` sin invocaciones | **RESUELTO** | `src\Common\Security\SandboxVerifier.cc:40,43`; `src\Include\SandboxVerifier.h:48,78` |
| `CM-BAJ-014` — `m_trusted_signatures` nunca consultado | **RESUELTO** | `src\Include\SandboxVerifier.h:90` |
| `CM-BAJ-005` — `RemoveUserButton` con cuerpo vacío | **RESUELTO** | `src\Core\include\rj2xcl.h:203`; `rj2xcl.cc:281` |
| Consola Electron (código muerto) | **RESUELTO** | `src\CMakeLists.txt:124-126`; sin fuentes de Electron en el árbol |
| Informes `10..12_codigo_muerto_*.md` | **PARCIAL** | quedan `deprecated\`, `_legacy\` y los residuos de build; y aparecen muertos nuevos (`COD-05`) |
| `DOC-BAJ-001` nomenclatura RJ2XCL/NEVEN/BERT | **ABIERTO** | `PROD-23` |
| `DOC-BAJ-002` cobertura desigual de documentación de módulos | **ABIERTO** | `android\` y `src\Audiobook\` no aparecen en `src\docs\Arquitectura\` |
| `DOC-MED-001` Doxygen ausente en headers públicos | **PARCIAL** | `src\Core\include\*.h` sí lo tiene; `src\Audiobook\**` y `src\TaskPane\*.js` no |
| `SEC-ALT-007` flags de seguridad MSVC ausentes | **RESUELTO en el `CMakeLists`** | `src\CMakeLists.txt:18,23`; pero ver `SEC-11` para el artefacto |
| Resto de hallazgos de código | **NO VERIFICADO** | sin identificadores estables no hay emparejamiento posible |

El patrón que permitió verificar los cuatro primeros, cuatro meses después, es el mismo en los
cuatro: **un comentario en el punto exacto del código con el identificador del hallazgo y la
versión** (`// CM-BAJ-005: ... eliminado v2.3`, `// C-02 FIX`, `// RESOLVED: C-06`). Es lo único
que funcionó y debería ser la norma.

---

## 5. Eje 3 — Seguridad

### 5.1 Marco de severidad usado

NEVEN ejecuta R, Julia y Python en la máquina del usuario **por diseño**, y así lo declara
`src\SECURITY.md:16`. Con ese punto de partida:

- Un hallazgo explotable solo por quien **ya ejecuta código como el usuario víctima** no añade
  riesgo: se clasifica Baja o Informativa, por grave que suene.
- Un hallazgo que **elimina ese requisito previo** sí añade superficie y se clasifica Alta o
  Crítica. Dos lo cumplen: la API HTTP local sin autenticación (`SEC-01`) y los permisos de
  escritura de `C:\NEVEN\` para cualquier usuario autenticado (`SEC-09`).
- Los controles que el proyecto presenta como frontera de seguridad y no lo son se reportan como
  desalineación entre documentación y código, con su propia severidad (`SEC-22`, `SEC-23`).

Método: lectura de código y de configuración, más inspección en solo lectura de la instalación
viva (ACL con `Get-Acl`, conteo de ficheros de integridad, certificados, cabeceras PE y contenido
del log). **No se emitió ninguna petición HTTP contra los servidores de NEVEN y no se construyó
ninguna prueba de concepto.**

### 5.2 Veredicto por superficie examinada

| # | Superficie | Veredicto | Motivo |
|---|---|---|---|
| 1 | IPC por named pipes (nombres, ACL, autenticación del extremo, validación Protobuf) | **CONFIRMADA (parcial)** | DACL por defecto (`lpSecurityAttributes = NULL`), sin `FILE_FLAG_FIRST_PIPE_INSTANCE`, sin identificación del extremo y nombre predecible → `SEC-12`. La validación del marco Protobuf, en cambio, acota la longitud antes de deserializar: **descartada** como problema |
| 2 | El sandbox de los 133 tests | **CONFIRMADA como no-frontera** | Lista de subcadenas aplicada en tres puntos, con excepciones de contexto satisfacibles con un comentario y sin cobertura de la vía HTTP → `SEC-02`, `SEC-23` |
| 3 | Servidor HTTP 5555: bind, autenticación, CORS, recorrido de rutas | **CONFIRMADA (crítica)** | Bind correcto a `127.0.0.1`; pero CORS comodín, cero autenticación, endpoints de ejecución y de escritura, y recorrido de rutas en cuatro ramas de servido estático → `SEC-01`, `SEC-03`, `SEC-04` |
| 4 | Endpoint de descarga de audiolibros (arreglo `9eba8b1`) | **Travesía DESCARTADA; debilidades nuevas CONFIRMADAS; funcionalmente NO VERIFICABLE** | `normpath` + comprobación de prefijo bloquea `../`; quedan doble decodificación, prefijo sin separador y un *fallback* que entrega cualquier fichero del directorio → `SEC-17`. Verificación funcional imposible sin Excel y servidor TTS: procedimiento en §7 |
| 5 | TaskPane: XSS al renderizar `html` | **CONFIRMADA** | `srcdoc` con `sandbox="allow-scripts allow-same-origin"`, combinación que anula el aislamiento, y dos `srcdoc` sin `sandbox` → `SEC-07` |
| 6 | Ejecución de código desde celdas y ubicación del límite de confianza | **CONFIRMADA como mal ubicado** | El límite está en la celda, pero hay una segunda puerta (HTTP→pipe) sin control equivalente, y el sandbox se desactiva editando un JSON escribible por cualquier usuario → `SEC-02`, `SEC-09`, `SEC-14` |
| 7a | Visor WebView2 (navegación, host objects, contenido remoto) | **CONFIRMADA (menor)** | Filtro de navegación de lista blanca correcto y **cero** `AddHostObjectToScript`; pero `file:///` sin acotar, cinco CDN permitidas, sin filtro de subrecursos → `SEC-19` |
| 7b | Quarto por `CreateProcess` (línea de comandos, inyección de argumentos) | **DESCARTADA** | Validación de entrada, allowlist de extensión y formato, rutas entrecomilladas y `CreateProcessA` sin shell → `SEC-20`. Residual bajo: `quarto_path_` viene de la configuración (`SEC-13`) |
| 8 | Secretos en el árbol y en el historial de git (`INV-INS-01`) | **CONFIRMADA (baja)** | `INV-INS-01` **se cumple en HEAD**; el historial conserva el identificador de un recurso Azure retirado en `de8d44b`, y hay una contraseña literal de exportación PFX en un fichero versionado → `SEC-18`, `SEC-10` |
| 9a | Permisos del directorio de producción `C:\NEVEN\` | **CONFIRMADA (alta)** | `NT AUTHORITY\Authenticated Users : Modify` sobre `C:\NEVEN`, `C:\NEVEN\functions` y `C:\NEVEN\certs` → `SEC-09` |
| 9b | Integridad de scripts (`INV-CMN-02`) | **CONFIRMADA (alta)** | Verificación *fail-open* y **0** ficheros `.sha256` para 92 scripts desplegados → `SEC-08` |
| 9c | Deserialización | **DESCARTADA** | Protobuf con validación de marco previa; cero `pickle.load`, cero `yaml.load(`, cero `eval(` en el servidor. El único `exec(compile(...))` es el cargador de ficheros `.py` de NEVEN, cuyo riesgo es `SEC-08`/`SEC-09`, no deserialización |
| 9d | DLL hijacking en el arranque del XLL y de los procesos hijo | **DESCARTADA (con reserva menor)** | `LoadLibraryA` siempre con ruta absoluta derivada de `R_HOME`/`JULIA_HOME` descubiertos en `HKEY_LOCAL_MACHINE`; `AddDllDirectory` acota las dependencias. Reserva: `AddDllDirectory` solo surte efecto con `SetDefaultDllDirectories`, que no se llama en ningún punto |
| 9e | Prompt injection en el RAG y el agente | **DESCARTADA parcialmente** | No hay ejecución automática de acciones propuestas por el modelo; el eslabón débil no es el modelo, es que `/api/functions/create` no exige autenticación (`SEC-01`). Sin marcado de procedencia del contenido RAG → `SEC-21`. El comportamiento del modelo ante contenido hostil: **NO VERIFICABLE** sin ejecutar el agente |
| 9f | Servidor HTTP del módulo Audiobook (no estaba en la lista; hallada) | **CONFIRMADA (alta)** | `host='0.0.0.0'` + CORS `*` + sin autenticación, con endpoints de subida y generación → `SEC-16` |
| 9g | Puente `postMessage` del visor hacia ficheros de cola (no estaba en la lista; hallado) | **CONFIRMADA (media)** | Inyección JSON por concatenación y volcado íntegro del mensaje a un fichero que consume NEVEN-SIM → `SEC-15` |
| 9h | Barrera SQL `INV-SB-03` | **CONFIRMADA** | La validación es por prefijo de sentencia, y `/api/groupby` interpola nombres de columna sin escapar → `SEC-05`, `SEC-06` |
| 10 | Mitigaciones en el binario (`INV-BLD-02`) | **CONFIRMADA (media)** | `NEVEN64.xll` sin CFG en repo y en producción; el resto de binarios sí lo lleva → `SEC-11`. `CETCOMPAT`: **NO VERIFICABLE** con el método usado (vive en el *load config* extendido) |

### 5.3 Hallazgos del eje 3

| ID | Sev. | Hallazgo | Evidencia | Fundamento |
|---|---|---|---|---|
| `SEC-01` | **Crítica** | La API local no tiene autenticación, responde con `Access-Control-Allow-Origin: *`, parsea el cuerpo sin mirar `Content-Type` y expone `POST /api/{r,python,julia}`, que ejecuta código en los motores de la sesión | `src\startup\neven_http_server.py:633-643, 1091, 1110-1112, 4332, 4367`; único control de abuso: rate limiter `:646-649, 1076-1079` | VERIFICADO |
| `SEC-03` | **Crítica** en combinación con `SEC-01` | `/api/save_script` escribe en cualquier ruta absoluta (solo filtra la extensión y hace `makedirs`), y el fichero escrito lo ejecuta el hot-reload | `src\startup\neven_http_server.py:2783-2814`; `src\Core\src\FileWatchService.cc:53-77`; `src\startup\startup.py:72`. Patrón correcto en el mismo fichero: `:2669-2676` | VERIFICADO |
| `SEC-02` | Alta | El sandbox no cubre la vía HTTP→pipe: cero coincidencias de validación en el servidor, en `datalab_handler.py` y en `pipe_client.py`; y el único camino que valida contenido (`AutoLoader`) no tiene invocadores | `src\Core\src\basic_functions.cc:157-166`; `src\Common\IPC\REPLBridge.cc:77`; `src\Common\AutoLoader.cc:72,98`; `src\Core\src\language_service.cc:443-462` | VERIFICADO |
| `SEC-04` | Alta | Recorrido de rutas en cuatro ramas de servido estático: se decodifica antes de normalizar y se concatena sin contención | `src\startup\neven_http_server.py:652, 933-936, 963-968, 978-983, 1038-1073`. Patrón correcto a 20 líneas: `:988-1016` | VERIFICADO (código) / HIPÓTESIS (explotación concreta: no se emitió ninguna petición) |
| `SEC-07` | Alta | Tres políticas distintas de `srcdoc` para HTML producido por los motores; una de ellas anula el aislamiento y dos no tienen `sandbox` | `src\TaskPane\datalab.js:1593-1599`; `chart-gallery.js:1770`; `taskpane.js:1235` | VERIFICADO |
| `SEC-08` | Alta | Verificación de integridad *fail-open*, SHA-256 sin clave en lugar del HMAC que declara la ontología, y **0** ficheros `.sha256` para 92 scripts desplegados | `src\Common\Security\SecurityService.cc:34-40, 56-93`; conteo en `C:\NEVEN\functions` y `C:\NEVEN\startup`; el repo sí tiene `src\startup\startup.r.sha256` | VERIFICADO |
| `SEC-09` | Alta en multiusuario, Media en máquina de un solo usuario | `C:\NEVEN`, `C:\NEVEN\functions` y `C:\NEVEN\certs` con `Authenticated Users : Modify` heredado de `C:\`; el instalador no llama a `icacls` ni `Set-Acl` | `Get-Acl` (solo lectura); `src\Install\Install-NEVEN.ps1` | VERIFICADO |
| `SEC-16` | Alta | El servidor de audiolibros escucha en `0.0.0.0` con CORS `*` y sin autenticación, con endpoints de subida, generación y configuración de clave de terceros | `src\Audiobook\neven_audiobook_server.py:38-45, 376-382`; `src\Audiobook\api\routes.py:243,288,412,486,504,524,1123,1221,1273` | VERIFICADO |
| `SEC-05` | Media | `INV-SB-03` es una barrera de prefijo: en DuckDB las funciones de tabla que leen ficheros se invocan desde un `SELECT` | `src\startup\neven_http_server.py:523-533` | VERIFICADO (código) / HIPÓTESIS (alcance en DuckDB: no se ejecutó el motor) |
| `SEC-06` | Media | Inyección SQL por interpolación de identificadores en `/api/groupby` y de la ruta en `/api/load` | `src\startup\neven_http_server.py:500-514, 2965-2983, 4262-4274`. La métrica sí se valida (`:487`) | VERIFICADO |
| `SEC-10` | Media | Clave privada PEM sin cifrar de un certificado instalado en la raíz de confianza del usuario, con vigencia de 10 años, en un directorio escribible por cualquier usuario; contraseña de exportación del PFX literal en un fichero versionado | `src\TaskPane\Generate-Cert.ps1:33-74`; `src\Install\Install-NEVEN.ps1:1082-1111`; `C:\NEVEN\certs\` | VERIFICADO (valor no transcrito) |
| `SEC-11` | Media | `NEVEN64.xll` sin Control Flow Guard (`0x0160`) en repo y en producción; `NEVENRibbon.dll`, `NEVEN-SIM.xll` y los tres `Control*.exe` sí lo llevan | lectura de `DllCharacteristics` con parser propio validado contra `kernel32.dll` (`0x4160`) y `notepad.exe` (`0xC160`) | VERIFICADO el estado / HIPÓTESIS la causa (`/guard:cf` en `add_compile_options` y no en `add_link_options`, `src\CMakeLists.txt:20,24`, con `NEVEN_Core` construido vía *object library*, `src\Core\CMakeLists.txt:5-7`) |
| `SEC-12` | Media | Named pipes con DACL por defecto (lectura para `Everyone`), sin `FILE_FLAG_FIRST_PIPE_INSTANCE`, 4 instancias, nombre predecible y cliente sin `SECURITY_IDENTIFICATION` | `src\Common\IPC\pipe.cc:216-227`; `src\Core\src\language_service.cc:127-130, 228, 408`; `src\Common\Constants.h:55` | VERIFICADO (código) / HIPÓTESIS (explotación) |
| `SEC-15` | Media | El puente del visor construye el JSON de `writeCell` concatenando sin escapar y vuelca `sim-command` tal cual a una cola que consume NEVEN-SIM | `src\Common\PostMessageBridge.cc:73-82, 119-130`; `src\NEVEN-SIM\src\bridge_poller.cc:30`, `sim_main.cc:619` | VERIFICADO |
| `SEC-17` | Media | El arreglo `9eba8b1`: travesía bloqueada, pero doble decodificación, prefijo sin separador y *fallback* por prefijo que entrega el primer fichero coincidente con `mimetype` de audio | `src\Audiobook\neven_audiobook_server.py:91-124, 273` | VERIFICADO el código y los hashes repo↔producción / **NO VERIFICADO** funcionalmente (§7) |
| `SEC-22` | Media (aseguramiento) | La documentación de seguridad describe un sistema que ya no es este: cifras de tests que no coinciden, "36/36 remediados" no verificable, A01 puntuado 9/10 apoyándose en una función sin invocadores, y ni una mención de los puertos 5555/5556, del TaskPane, del servidor de audiolibros ni del visor | `src\SECURITY.md:160-168, 181-192`; `src\docs\Evaluaciones\Evaluacion_OWASP.md:16, 82, 214-224` | VERIFICADO |
| `SEC-23` | Media | El sandbox aplica las tres listas de lenguaje a todo el código (genera falsos positivos), coincide por subcadena, y sus excepciones de contexto se satisfacen con un comentario | `src\Common\Security\SandboxVerifier.cc:49-59, 214-262, 269-323, 378-426` | VERIFICADO |
| `SEC-24` | Media | 247 de los 369 tests están relacionados con seguridad y **cero** cubren la superficie HTTP | recuento con `--gtest_list_tests` | VERIFICADO |
| `SEC-19` | Media-Baja | Visor WebView2: lista blanca de navegación correcta y sin host objects, pero sin CSP, sin filtro de subrecursos, `file:///` sin acotar y sin `add_FrameNavigationStarting` | `src\Common\ViewerWindow.cc:261-295, 552-626` | VERIFICADO |
| `SEC-21` | Media-Baja | Sin *tool calling*: el agente no escribe ficheros por su cuenta. Lo que falta es marcado de procedencia del contenido del RAG en el prompt | `src\startup\neven_http_server.py:1141, 2669-2676`; `.agents\skills\*` (`restricted_to_rag` **no es** una defensa técnica) | VERIFICADO lo buscado / NO VERIFICABLE el comportamiento del modelo |
| `SEC-13` | Baja | `ValidateConfig()` valida las rutas y descarta el valor de retorno en sus seis llamadas; la lista de caracteres no incluye la comilla doble | `src\Common\ConfigService.cc:78-105` | VERIFICADO |
| `SEC-14` | Baja como defecto, relevante como aseguramiento | `RequestSandboxDisable()` implementa el diálogo y el registro en los que la evaluación OWASP apoya un 9/10, y **no tiene invocadores** ni persiste el cambio | `src\Common\ConfigService.cc:111-155`, `ConfigService.h:99`; `src\docs\Evaluaciones\Evaluacion_OWASP.md:16` | VERIFICADO |
| `SEC-18` | Baja | El historial de git conserva el identificador de un recurso Azure OpenAI retirado en `de8d44b`; lo que había en `apiKey` era un marcador, no una clave | `git log --all --diff-filter=A`; commits `1cd442e`, `d66cda5`, `de8d44b` | VERIFICADO (valores no transcritos) |
| `SEC-20` | Informativa (control que funciona) | La construcción de la línea de comandos de Quarto es correcta: validación de entrada, allowlist, entrecomillado y `CreateProcessA` sin shell | `src\Common\QuartoService.cc:36-63, 331, 402-419, 476-517`; `src\Common\Security\InputSanitizer.cc:31-42` | VERIFICADO |

### 5.4 Estado de la auditoría de seguridad previa

`src\docs\audit\hallazgos_seguridad.md` (191 KB, 151 secciones con IDs `FOR-*`) es un inventario
forense **sin campo de estado**, y muchas entradas son observaciones de que algo está bien hecho.
No existe un listado canónico de "los 36 hallazgos" con identificador, así que el emparejamiento
uno a uno es imposible sin reconstruirlo. Lo que sí se puede dictaminar:

| Asunto previo | Estado | Evidencia |
|---|---|---|
| Spec `security-remediation` | **CERRADA formalmente** | `.kiro\specs\security-remediation\tasks.md`: 72/72 tareas marcadas |
| `FOR-PIPE-001/005` validación del handle tras `CreateNamedPipeA` | **RESUELTO** | `src\Common\IPC\pipe.cc:229-232` + `SafePipeHandle` |
| `FOR-PB-*` desbordamiento por Protobuf malformado | **RESUELTO** | `MessageValidator::ValidateFrame/SafeUnframe` + 6 tests `ProtobufIpcPBT` |
| `C-02` código de celda sin validar | **RESUELTO** | `src\Core\src\basic_functions.cc:157-166` (marcado "C-02 FIX") |
| `C-06` `parse_error` de JSON ignorado | **RESUELTO** | `src\Common\ConfigService.cc:57-62` (marcado "RESOLVED: C-06") |
| `S-06` fugas de handles BCrypt | **RESUELTO** | `src\Common\Security\SecurityService.cc:21-27` |
| `H-04` corrupción por recálculo paralelo | **RESUELTO** | `thread_local XLOPER12` en `basic_functions.cc:135,193` |
| Integridad de scripts (control introducido por la remediación) | **ABIERTO en producción** | `SEC-08` |
| Desactivación del sandbox con confirmación y registro | **ABIERTO** | `SEC-14` |
| Superficie HTTP local (5555, 5556, audiolibros) | **NUNCA AUDITADA** | no aparece en `hallazgos_seguridad.md` ni en `Evaluacion_OWASP.md`: es donde están los hallazgos críticos de este informe |

### 5.5 Secretos: ubicación y naturaleza, sin valores

No se transcribió ningún valor y no se encontró ninguna clave de proveedor filtrada.

| Qué | Dónde | Naturaleza |
|---|---|---|
| Contraseña literal de exportación de PFX | `src\TaskPane\Generate-Cert.ps1:42, 55, 56` y bloque equivalente en `src\Install\Install-NEVEN.ps1` (~1090-1100) | Credencial de exportación en fichero versionado. El literal está en `:42`, la línea que lo convierte a `SecureString` en claro; `:43` es el `Export-PfxCertificate` que lo consume. La clave resultante se escribe en PEM sin cifrar |
| Identificador de un recurso Azure OpenAI | historial de git, retirado en `de8d44b` (2026-09-06); introducido en `1cd442e`/`d66cda5` | Endpoint, **no** una clave: el campo `apiKey` del blob histórico contenía un marcador. Recuperable del historial |
| `TaskPane.keyPath` | `C:\NEVEN\neven-config.json`, `src\Install\neven-config.template.json` | Ruta a un fichero de clave, no la clave |
| Clave privada del certificado local | `C:\NEVEN\certs\localhost.key` (1.911 B, PEM sin cifrar), ACL `Authenticated Users : Modify` | Clave privada de un certificado presente en `Cert:\CurrentUser\Root`, válido hasta 2036 |

`INV-INS-01` **se cumple en HEAD**: solo `src\Install\neven-config.template.json` está
versionado; `src\Install\neven-config.json` existe en disco y está ignorado
(`src\.gitignore:87`). Ni el template, ni esa copia local, ni `C:\NEVEN\neven-config.json`
contienen una clave de API no vacía. No hay `.pfx`, `.key`, `.pem`, `.jks` ni `keystore`
versionados, ni en HEAD ni añadidos en el historial.

---

## 6. Eje 4 — Mejoras recomendadas

Los tres ejes anteriores produjeron **126 candidatos** con solape entre sí (35 del eje 1, 56 del
eje 2, 35 del eje 3). El eje 4 los consolidó en **55 mejoras** con trazabilidad al identificador
de origen, coste, riesgo, secuencia y comprobación contra la bitácora del proyecto. **113 de los
116 identificadores** aparecen citados en el campo "Motivado por" de algún ítem del plan. Los tres
que no son informativos y se cierran sin ítem, declarados expresamente en el §2 del plan: `COD-21`
(no se comprobó que los tests pasen, §9), `COD-26` (dos invariantes que se cumplen) y `COD-52`
(instrucciones a agentes, reportadas y no obedecidas, §11). El detalle está en
`plan-de-trabajo.md`; aquí va lo que un lector del informe necesita saber.

### 6.1 Recuento

| Familia | PENDIENTES | POR MEJORAR | NUEVAS IDEAS | Total |
|---|---:|---:|---:|---:|
| A — cierra un hallazgo de los ejes 1-3 | 12 | 11 | 0 | **23** |
| B — ingeniería del proyecto (verificación, build, empaquetado, documentación) | 7 | 9 | 5 | **21** |
| C — capacidad nueva | 2 | 0 | 9 | **11** |
| **Total** | **21** | **20** | **14** | **55** |

Por prioridad: 5 en P0, 22 en P1, 19 en P2, 9 en P3. Coste agregado si se hiciera todo:
**126-196 jornadas**. Las fases 0 a 2, que son las que cambian el riesgo real del proyecto, suman
**26-39 jornadas**.

### 6.2 Las siete primeras, y por qué

| # | Mejora | Razón |
|---|---|---|
| 1 | `A-01` autenticar la API local y cerrar su superficie de escritura y lectura | Es el único hallazgo que convierte "visitar una página" o "tener una cuenta local" en ejecución de código en la sesión de Excel |
| 2 | `B-01` mover `src\.github\` a la raíz y arreglar el workflow | Media jornada; sin esto ninguna otra mejora queda protegida |
| 3 | `A-02` puerto propio y bind local para el servidor de audiolibros | Causa raíz de que la descarga de audiolibros nunca se pudiera probar |
| 4 | `A-03` endpoint de descarga, esquema de URLs y verificación del arreglo `9eba8b1` | Es el pendiente que el usuario arrastra; incluye quitar el *fallback* que entrega un fichero distinto del pedido |
| 5 | `A-13` librería R: `requireNamespace`, `tryCatch`, HC3 y atributos de ayuda | Es el producto: 30 ficheros pierden todas sus funciones si falta un paquete, 34 no tienen `tryCatch`, los errores robustos son HC0 y 12 de las 42 funciones de usuario aparecen como "Exported Function" (63 de 93 en cifra bruta, §2.2) |
| 6 | `A-04` integridad real de los scripts desplegados | 0 ficheros `.sha256` para 92 scripts, con verificación *fail-open* |
| 7 | `A-05` ACL del directorio de producción | Hoy `C:\NEVEN\` es escribible por cualquier cuenta autenticada de la máquina |

### 6.3 Cambios que exigen tocar la ontología

Restricción dura del proyecto: una propuesta que viola una invariante no se implementa aunque sea
técnicamente posible. **Ninguna de las 55 mejoras viola una invariante.** Cuatro exigen
**reformular** el texto de una invariante antes de implementarse, y cuatro proponen **añadir**
invariantes nuevas para huecos que la ontología no cubre. En todos los casos se actualiza primero
el YAML y se justifica el cambio; después se implementa.

| Invariante | Acción | Motivo verificado | Mejora que la necesita |
|---|---|---|---|
| `INV-LR-04` (`p2.yaml:660`) | **Reformular** | El mecanismo que nombra sí existe (`DialogosXCL$Descripcion` vale `"description"`, `R4XCL-0-Interno-2.R:242`), pero afirma una consecuencia falsa (las funciones sin atributo **sí** aparecen en Excel, con el texto de respaldo de `excel_api_functions.cc:292`), no dice que el valor debe ser una `list()` cuyos elementos 2..n se asignan a los argumentos por posición (`rinterface_common.cc:843-846`), y su `como_verificar` solo detecta una de las dos formas en uso. El paper lo documenta mejor que la ontología (`03_viewer_extensibility.tex:95-96`) | `A-13`, `C-09` |
| `INV-AS-03` (`p3.yaml:205`) | **Reformular**, solo si se adopta `A-11` | Fija el 5556 como literal sin declarar exclusividad, y tres servicios lo reclaman. `A-02` **no** requiere este cambio: mover el servidor de audiolibros a un puerto propio respeta la invariante tal como está | `A-11` |
| `INV-SB-03` (`p2.yaml:283`) | **Ampliar** | Se cumple literalmente y es insuficiente: en DuckDB las funciones de tabla que leen ficheros se invocan desde un `SELECT`. La parte de `A-01` que valida identificadores y parametriza rutas **no** necesita el cambio | `A-01` (parte SQL) |
| `INV-CMN-02` (`p1.yaml:347`) | **Corregir mecanismo y política de ausencia** | Dice HMAC donde el código hace SHA-256 sin clave, y da por hecho un control que en producción no opera. Recomendación: decir SHA-256, porque una clave en la misma máquina donde el atacante es un usuario local es ofuscación, no secreto; lo que protege esos ficheros es la ACL (`A-05`) | `A-04` |

Adiciones propuestas, que no contradicen nada: (a) ACL del directorio de producción; (b)
autenticación de la API local; (c) alcance declarado del sandbox; (d) fuente única de cada
artefacto desplegado.

Tres mejoras llevan condición escrita sin cambio de ontología: `B-19` (toca `INV-SB-01..05` y
`INV-TF-01/03/04`; exige los tests de `B-02`/`B-03` antes), `A-23` (el `module` de Julia obliga a
reconstruir `neven_julia.dll`, 1,04 GB, y revalidar `INV-CJ-01/02`) y `C-03` (requiere actualizar
`tipo_outputs[]` del sidecar respetando `INV-SJ-02/03`).

### 6.4 Lo que no se propone, y por qué

Nueve cosas que parecen mejoras obvias y quedan fuera, para que no se reintroduzcan por inercia:

1. **Modo degradado que registre funciones de sustitución tras conectar los motores.** Choca de
   frente con `INV-CORE-01`, y `src\Core\src\rj2xcl.cc:544-550` documenta que esa vía ya se probó
   y causó cuelgues. La alternativa viable son `C-01` y `C-02`.
2. **CSP en el visor WebView2.** Descartada por el usuario el 2026-08-19 con razón escrita: el
   HTML que genera R lleva `<script>` inline, haría falta `unsafe-inline`. No se reabre. Lo que de
   `SEC-19` no requiere CSP —acotar `file:///` a los directorios de trabajo y añadir
   `add_FrameNavigationStarting`— sí está en el plan, en `A-18`(e).
3. **DACL restrictiva en los named pipes como primer paso.** Descartada por el usuario el
   2026-08-19 por riesgo. `A-19` la re-propone troceada y en P3, con el único dato nuevo que la
   justifica: la premisa de aquel análisis ("requiere privilegios elevados") es falsa.
4. **Mover `C:\NEVEN\` a `%ProgramFiles%`.** Lo asumen `INV-SR-01..05`, `INV-CMN-02`,
   `INV-SB-01..05` y rutas absolutas repartidas por el código. Es un proyecto, no un arreglo.
5. **Refactorizar 596 métodos a `snake_case`.** El código es internamente coherente; el documento
   es el que está mal (`B-10`).
6. **Reescribir el historial de git por el endpoint de Azure.** Caro, rompe clones, beneficio
   bajo; lo que se propone es rotar la clave de ese recurso si sigue vivo.
7. **`/WX` desde el primer día.** Bloquearía el build y haría abandonar la mejora.
8. **`module` en la librería Julia como tarea inmediata.** Va en `A-23`, P3, con su condición.
9. **Bundlers, transpiladores o módulos ES en el TaskPane.** `INV-TF-04` lo prohíbe y la
   invariante no es el obstáculo para nada de lo propuesto.

### 6.5 Hallazgos nuevos del eje 4

| ID | Sev. | Hallazgo | Evidencia | Fundamento |
|---|---|---|---|---|
| `MEJ4-01` | Alta | `src\.github\` no está en la raíz: el CI, las plantillas de incidencia y la de *pull request* son inertes | `Test-Path '.github'` → False; `git ls-files` sitúa las cuatro rutas bajo `src/.github/` | VERIFICADO |
| `MEJ4-02` | Media | `=NEVEN.Notebook.Export` no puede funcionar nunca: `CaptureAnalysis` no tiene invocadores, así que `has_analysis_` es siempre falso | `src\Common\NotebookExporter.cc:29,43,180`, `NotebookExporter.h:33`; `src\Core\src\basic_functions.cc:914`; `src\Core\include\basic_functions.h:62` | VERIFICADO el invocador ausente / HIPÓTESIS que el `.jl` sin orden de celdas sea inválido para Pluto |
| `MEJ4-06` | Media | Las 461 casillas abiertas de las especificaciones mezclan deuda real (207), decisiones de alcance (133), trabajo ya hecho (43), una especificación superada (28) y una ajena (50) | `.kiro\specs\**\tasks.md`, medido spec por spec | VERIFICADO los conteos; el veredicto por spec es HIPÓTESIS |
| `MEJ4-03` | Baja | `android\ontologia\` contiene una copia completa de sí mismo (736 ficheros, la mitad duplicados), y el dominio `graficos` existe en tres lugares | `android\ontologia\ontologia\`; `docs\ontologia\graficos` | VERIFICADO |
| `MEJ4-04` | Baja | El patrón de API pública sin invocadores afecta al menos a cinco componentes | `NotebookExporter::CaptureAnalysis`, `ConfigService::RequestSandboxDisable`, `RJ2XCL_Engine::ScheduleDelayedUpdate`, `AutoLoader::LoadAllUserScripts`; probable `GCMonitor` | VERIFICADO (4) / HIPÓTESIS (1) |
| `MEJ4-05` | Media (se eleva desde Baja al medirlo por nombre y hash) | `src\Install\functions\` es un segundo directorio de librería no declarado: **ocho** ficheros de función tienen ahí su única copia del repositorio, y **dos** existen en los dos directorios con contenido distinto | Única copia: `DS_Wooldridge_Benchmark.Studio.R`, `RG_Davidson_MacKinnon.Studio.R`, `RG_FGLS.Studio.R`, `RG_Newey_West.Studio.R`, `RG_RESET.Studio.R`, `ST_ECM.Studio.R`, `ST_VAR.Studio.R`, `TM_TextAnalysis.Studio.py`. Divergentes: `RG_2SLS.Studio.R` (`Install\ E6DF7AAFDE9F` ≠ `libreria\R\ D7D9247EA5D4`) y `RG_HECKIT.Studio.R` (`039DE184C4AA` ≠ `D26193CB28EA`); **producción sigue a la copia de `src\libreria\R\`** en los dos casos | VERIFICADO (hashes SHA-256 medidos) |
| `MEJ4-07` | Baja | `ontology-engine-framework` describe un proyecto que no es NEVEN: migración del esquema `[IA]` de `sqldb_buklo_lab`, con capas Gateway y Angular | `.kiro\specs\ontology-engine-framework\tasks.md` (50 tareas abiertas) | VERIFICADO |

### 6.6 Estado de las 27 especificaciones

De las 461 casillas sin marcar, **la deuda real son unas 207**. El resto: 133 son decisiones de
alcance (`neven-sim` 109, `neven-enterprise` 24), 50 son ajenas al proyecto
(`ontology-engine-framework`), 43 corresponden a funcionalidad que existe y funciona
(`nevenx-dispatcher` 20, `neven-v3-taskpane` 23) y 28 a una especificación superada por la
implementación (`ai-integration`, que es el origen documental de `PROD-06`). Ocho
especificaciones están cerradas (0 abiertas): `code-audit`, `function-dictionary`,
`neven-studio-standalone`, `python-integration`, `python-reactivation`,
`rj2xcl-to-ponto-rename` (con residuo), `security-remediation` (formalmente, no verificable).
El detalle por especificación está en `04-notas-mejoras.md` §5, y depurarlo es el ítem `B-21`.

---

## 7. El pendiente arrastrado: descarga de audiolibros del TaskPane

**Estado: el arreglo del commit `9eba8b1` está aplicado y desplegado byte a byte, y nunca se ha
ejecutado. Sigue sin comprobar funcionalmente.**

### 7.1 Qué está desplegado · VERIFICADO

Hashes medidos entre repositorio y producción (solo lectura):

| Fichero | Repo (SHA-256, 12) | Producción | Veredicto |
|---|---|---|---|
| `src\Audiobook\neven_audiobook_server.py` | `2209DC188A3B` | `C:\NEVEN\Audiobook\` idéntico | sincronizado |
| `src\TaskPane\audiobook.js` | `39382D4C75C5` | `C:\NEVEN\taskpane\` idéntico | sincronizado |
| `src\Audiobook\api\routes.py` | `25BDFE4EF97A` | `C:\NEVEN\Audiobook\` idéntico | sincronizado |

El commit toca `neven_audiobook_server.py` (35 líneas) y `audiobook.js` (20 líneas), y el cliente
usa `encodeURIComponent()` en `audiobook.js:357, 392, 604`.

### 7.2 Qué arregla y qué introduce · VERIFICADO (código)

| Vector | Veredicto | Razón |
|---|---|---|
| Nombres con espacios y acentos (lo que el commit dice arreglar) | **correcto en el mecanismo** | El cliente codifica el basename y el servidor lo resuelve contra la carpeta de salida; el supuesto del commit es válido, porque `routes.py:1013` acepta alfanuméricos Unicode, espacio, `-` y `_` |
| Recorrido de rutas | **DESCARTADO** | `normpath` resuelve los `..` y la comprobación de prefijo rechaza con 403 antes de abrir, también con `..` doblemente codificados |
| Doble decodificación | **defecto latente** | Flask ya decodifica el segmento de ruta y `unquote()` (`:101`) lo decodifica otra vez. Hoy inalcanzable por la ruta normal, porque la lista blanca de nombres excluye `%` |
| Prefijo sin separador | **defecto (bajo)** | `startswith(output_folder)` acepta un directorio hermano cuyo nombre empiece igual; se arregla con `os.path.commonpath` |
| *Fallback* por coincidencia de prefijo | **la regresión real** | Si el nombre exacto no existe, lista el directorio y sirve `matches[0]` con `mimetype='audio/mp4'` aunque sea un `.md`. Con un prefijo de un carácter se obtiene un fichero cualquiera, y el orden de `os.listdir` es arbitrario (`:109-113`) |
| `href` sin codificar en `/download` | **defecto funcional** | `:273` genera el enlace escapado como HTML pero no codificado como URL: es el mismo problema del commit, en el otro extremo |
| Inyección de cabecera por `download_name` | **DESCARTADO con reserva** | `send_file` pasa por `Response.headers`, que en werkzeug rechaza saltos de línea. No se inventarió la versión instalada: reserva declarada |

Además, dos cosas lo mantienen inerte aunque el endpoint fuese perfecto:

- **`PROD-01`:** si cualquier proceso escucha en el 5556, `_handle_audiobook_start` responde
  "Server already running" sin comprobar que sea el servidor de audiolibros
  (`src\startup\neven_http_server.py:2332-2341`), y el error de bind del servidor real se pierde
  en `DEVNULL` (`:2350-2357`).
- **`SEC-17`, HIPÓTESIS comprobable en un minuto:** `audiobook.js:118` llama a
  `http://localhost:5555/...` mientras en producción el 5555 sirve **https** (hay
  `certPath`/`keyPath` en `C:\NEVEN\neven-config.json` y los ficheros existen). Si la página se
  sirve por https, el navegador bloquea esas peticiones como contenido mixto. Encaja con el
  síntoma que el commit intentó diagnosticar añadiendo trazas de consola.

Y un tercer desajuste que hace invisibles los audiolibros generados por una de las dos rutas
(`PROD-03`): el pipeline escribe `.m4a` y el listado, la página del QR y el cliente buscan `.m4b`.

### 7.3 Por qué no se pudo verificar, y cómo verificarlo

**Motivo:** comprobarlo exige arrancar Flask, un motor TTS y ffmpeg, es decir ejecutar servicios
y escribir en `C:\NEVEN\output`. Esta ejecución es de auditoría y lo prohíbe expresamente.

El procedimiento reproducible completo está en `03-notas-seguridad.md` §5 (seis pasos) y en
`01-notas-producto.md` §1.5. Resumen del orden correcto:

1. Comprobar `document.location.protocol` del TaskPane. Si es `https:`, arreglar primero el
   esquema de las URLs (o pasarlas a rutas relativas) antes de tocar nada más.
2. Arrancar el servidor a mano y en primer plano
   (`python C:\NEVEN\Audiobook\neven_audiobook_server.py`) para ver un `WinError 10048` si el
   puerto está tomado, y confirmar `/api/health` y `/api/system` (que devuelve la carpeta de
   salida real, que **no** es `C:\NEVEN\Audiobook\output` sino `C:\NEVEN\output`, `PROD-21`).
3. Probar con el peor nombre legal:
   `Miguel de Cervantes - Don Quijote de la Mancha á é í.m4b`. Esperado: HTTP 200 y tamaño igual
   al del fichero original.
4. **Probar el caso negativo**, que es el que delata si el paso 3 pasó por el *fallback*: pedir
   `/api/download/Miguel`. Comportamiento actual esperado: devuelve un fichero. Comportamiento
   correcto tras el arreglo: 404. Si el paso 3 funciona y el paso 4 también devuelve fichero, el
   arreglo no queda verificado.
5. Probar la página móvil del QR desde el teléfono con el nombre acentuado.
6. **Registrar el resultado en `.kiro\contexto\CHAT.md`** con el nombre exacto del fichero de
   prueba y el código HTTP de cada paso. Sin eso, en la próxima auditoría volverá a aparecer como
   "aplicado y no comprobado".

La mejora que recoge todo esto es `A-03`, en P0 del plan de trabajo.

---

## 8. Repositorio frente a la instalación de producción `C:\NEVEN\`

Medido en solo lectura. Nada se modificó en producción.

**Método, y por qué importa.** Esta comparación es **nombre a nombre y hash a hash** (SHA-256) de
los 125 ficheros de `C:\NEVEN\functions` contra el conjunto `src\libreria\R` + `src\libreria\JULIA`
+ `src\libreria\PYTHON` + `src\Install\functions`, que son los cuatro directorios del repositorio
que alimentan ese destino. Hacerlo por diferencia de conteos por directorio, que es lo barato,
produce cifras falsas en las dos direcciones: oculta los ficheros que divergen con el mismo nombre,
cuenta como huérfano lo que tiene origen en un directorio que no se miró (`src\libreria\PYTHON\`
contiene el origen de tres de los `.py`) y hace pasar por sincronizado un 63 ↔ 63 que esconde diez
nombres distintos en cada lado.

### 8.1 `C:\NEVEN\functions` frente a sus cuatro orígenes

| Resultado | Ficheros | Detalle |
|---|---:|---|
| **Idénticos** (mismo nombre, mismo hash) | 81 | incluye los 8 `.Studio.R`/`.py` cuyo único origen es `src\Install\functions\` (`MEJ4-05`) |
| **Divergentes** (mismo nombre, hash distinto) | 20 | 14 sidecars `.json`, 4 `.R`, `functions.jl` y `COMO_AGREGAR_FUNCIONES.md` |
| **Sin origen** en los cuatro directorios | 24 | 14 `.py`, 3 `.jl`, 3 `.R`, 1 `.json`, más `.Rhistory`, `AGENT_INSTRUCTIONS.md` y `SIDECAR_FORMAT.md` |

**Sin origen, por tipo.** `.py` (14): `bridge_excel_reader`, `bridge_functions`, `bridge_send`,
`bridge_viewer`, `dashboard_builder`, `data_studio`, `Ejemplo_P`, `geo_visualization`,
`ml_classification`, `ml_regression`, `network_graph`, `text_analysis`, `timeline_viewer`,
`z_geo_live`. `.jl` (3): `Ejemplo_J.jl`, `J4XCL-ML-Avanzado.jl`, `R4XCL-0-NevenX.jl`. `.R` (3):
`Ejemplo_R.r`, `R4XCL-RG-ML-Avanzado.R`, `R4XCL-UT-Paquetes.R`. `.json` (1): `NEVEN_Chart.json`.
Total de artefactos ejecutables o de catálogo sin origen: **21**. Los cuatro `.py` que **sí** tienen
origen están byte a byte: `ai_functions.py`, `package_manager.py` y `quarto_functions.py` en
`src\libreria\PYTHON\`, y `TM_TextAnalysis.Studio.py` en `src\Install\functions\`.

**Divergentes de código, con fecha y tamaño.** Aquí es donde una sincronización ciega en cualquiera
de las dos direcciones pierde trabajo:

| Fichero | Repositorio | Producción |
|---|---|---|
| `functions.jl` (`src\libreria\JULIA`) | 2026-10-08, 55.721 B | 2026-05-01, 55.499 B |
| `R4XCL-RG-Binaria.R` | 2026-08-03, 5.128 B | 2026-05-21, 5.095 B |
| `R4XCL-FX-Aleatorios.R` | 2026-08-03, 9.908 B | 2025-02-17, 9.932 B |
| `R4XCL-0-UT-InstalaPaqueterias.R` | 2026-08-03, 7.729 B | 2025-10-08, **12.853 B** |
| `R4XCL-AD-ACP.R` | 2026-09-28, 10.237 B | 2026-09-28, **10.663 B** |

Los dos últimos tienen más contenido en producción que en el repositorio: hay trabajo que solo
existe en `C:\NEVEN\` y que un redespliegue desde el repositorio borraría. A eso se suman 14 de los
28 sidecars con hash distinto.

**Solo en el repositorio, nunca desplegados.** Los nueve `GR_*.Studio.R` (`GR_Barras`, `GR_BoxPlot`,
`GR_Correlaciones`, `GR_EjemploAvanzado`, `GR_Histograma`, `GR_Lineas`, `GR_Mapa`, `GR_Scatter`,
`GR_SeriesTiempo`), `R4XCL-NEVEN-pluto-read.R` y `NEVEN-export-data.jl`. El dato operativo que la
comparación por conteo ocultaba: **la igualdad 63 ↔ 63 de los `.R` era casualidad**, con diez
nombres distintos en cada lado. Obliga a releer `PROD-11` y el punto (e) de `A-20`, que tratan los
`GR_*.Studio.R` como DataLab vivo.

### 8.2 El resto de la instalación

| Artefacto | Repositorio | Producción | Estado |
|---|---|---|---|
| `neven_http_server.py` | `src\startup\` 218.882 B `2F74824D39C3` | `C:\NEVEN\startup\` idéntico | **sincronizado** (es la copia canónica) |
| `neven_http_server.py` (copias muertas) | `src\TaskPane\` `CC22AE05B87D`, `src\ControlPython\startup\` `04B80A3FCA61`, dos en `src\Install\Dist\` | `C:\NEVEN\taskpane\` 114.576 B `F11972977B8B` (2026-09-28) | **cinco copias, cinco hashes**; la del `taskpane\` de producción está muerta y retirarla exige ventana de mantenimiento |
| `datalab_handler.py` | **no existe** en `src\startup\`; sí en `src\ControlPython\startup\` (48.454 B) | `C:\NEVEN\startup\` 48.454 B | el handler no vive junto al servidor que lo importa |
| `test_rag_queries.py` | `src\startup\` y `src\Install\scripts\`, byte a byte idénticos (`CE99746F2D9F`) | — | duplicado dentro del repositorio; es caso de `B-08` además de `B-02` |
| `.sha256` de integridad | `src\startup\startup.r.sha256`, `startup.jl.sha256` | **0** en `C:\NEVEN\functions` y **0** en `C:\NEVEN\startup` | el control existe en el repo y el instalador no lo despliega (`SEC-08`) |
| Ontología | `src\docs\ontologia` 13 ficheros | `C:\NEVEN\docs\ontologia` 368 ficheros / 2,13 MB; `C:\NEVEN\ontology` 35 / 28,21 MB | producción tiene checkpoints y grafos que el repo no; nada declara qué es fuente y qué es artefacto generado |
| `NEVEN64.xll` | `src\Build\Dist`, `src\Install\Dist`: `DllCharacteristics 0x0160` | `C:\NEVEN\NEVEN64.xll`: `0x0160` | **sin CFG en los tres** (`SEC-11`) |
| `neven.log` | — | `C:\NEVEN\neven.log` 119,6 MB, 1.595.421 líneas `Startup script line`, 8.448 `StartChildProcess:`, 38 `write-cell`, 143 `Sandbox BLOCKED` | sin rotación; legible por `BUILTIN\Usuarios` y **modificable** por cualquier usuario autenticado |
| Permisos | — | `C:\NEVEN`, `C:\NEVEN\functions`, `C:\NEVEN\certs` con `Authenticated Users : Modify` | `SEC-09` |
| Residuos de depuración | — | `C:\NEVEN\test_chart_api.py`, `test_chart_stats.py`, `test_direct.py`, `test_jl.jl`, `test_rag.py`, `test_rag2.py`, `test_singleton.py`, `fix_dash.py`, `fix_encoding.py`, `build_out.txt`, `build_err.txt` | ficheros sueltos en la raíz de producción |

**Lectura.** La regla de sincronización del steering (`.kiro\steering\neven-pre-cambios.md:144`)
señala como destino `NEVEN\TaskPane\neven_http_server.py`, que es la copia divergente del 19 de
octubre: quien siga la regla al pie de la letra copia hacia atrás 17 días de trabajo. Y la
instalación viva no es reproducible desde el repositorio en ninguna de las dos direcciones: 21
artefactos ejecutables solo existen en producción, 20 ficheros con el mismo nombre tienen contenido
distinto en los dos lados (dos de ellos con **más** contenido en producción), y 11 ficheros del
repositorio nunca se desplegaron. Las mejoras que lo atacan son `B-08` (fuente única y script de
paridad por hash, de solo lectura, que es el que debe producir este mismo inventario de forma
repetible) y `B-11` (empaquetado y prueba en máquina limpia, el pendiente más antiguo del
proyecto). Nada de esto puede resolverse por conteo: exige la comparación por nombre y hash.

---

## 9. Lo que no se pudo verificar, y por qué

Se declara en lugar de rellenarse con suposiciones.

| Asunto | Motivo |
|---|---|
| **Que los 369 tests pasen** | No se ejecutaron. El binario `src\Build\tests\Release\rj2xcl_tests.exe` es del 2026-10-20 y hay 5 fuentes modificadas después (`ribbon_connect.cc`, `basic_functions.cc`, `ribbon_connect.h`, `basic_functions.h`, `julia_interface.cc`), así que un verde de ese binario no probaría nada; recompilar escribe en `src\Build\`, dentro del árbol de fuentes; y varias suites escriben ficheros, de modo que ejecutarlas no es solo lectura. **No se afirma ni se niega que pasen** (`COD-21`) |
| **`INV-TEST-03`** (los tests no requieren Excel, R, Julia ni Python) | No verificada, precisamente por no haberlos ejecutado. Indicio favorable: los 30 mock headers de `src\Include` |
| **La descarga de audiolibros de extremo a extremo** | Exige Flask, un motor TTS y ffmpeg, es decir ejecutar servicios y escribir en producción. Procedimiento en §7.3 |
| **La explotación de `SEC-04`, `SEC-05`, `SEC-06`, `SEC-12`** | No se emitió ninguna petición HTTP contra los servidores ni se construyó ninguna prueba de concepto. Lo verificado es la ausencia de contención en el código |
| **`CETCOMPAT` en los binarios** | No está en `DllCharacteristics`: vive en el *load config* extendido, cuyo parseo no se abordó |
| **El alcance real de las funciones de tabla de DuckDB** | No se ejecutó DuckDB; se razona desde su documentación, no desde una prueba |
| **La versión instalada de `werkzeug`/`flask`** | No se inventarió el entorno Python de producción; afecta a si la cabecera `Content-Disposition` del endpoint de descarga está protegida por el framework |
| **El mojibake real en los mensajes de celda** (`PROD-18`) | Exige compilar con y sin `/utf-8` y comparar en Excel |
| **El efecto del zombie cleanup con dos instancias de Excel** (`COD-02`) | No se abrieron dos instancias |
| **La aridad máxima de las funciones exportadas** (`PROD-09`) | Exige un arranque real de R y consultar `formals()` sobre `globalenv()` |
| **Qué hace el cargador de sidecars con `aliases.json`** (`PROD-12`) | No se localizó el punto de carga |
| **La cobertura real de i18n en la interfaz** (`PROD-15`) | Exige instrumentar `i18n.js` en una sesión real del TaskPane |
| **Qué ve el usuario en el asistente de funciones** (`PROD-08`, `COD-28`) | El mecanismo sí se verificó leyendo el código de los tres tramos (R → `rinterface_common.cc` → `xlfRegister`, §3.4), y de ahí sale el recuento de 30 descripciones efectivas. Lo que no se verificó es el resultado en pantalla: exige Excel abierto. Dos cosas concretas quedan abiertas: que la asignación posicional de los textos de argumento case con el orden de `formals()` en cada una de las 30 funciones, que no se comprobó una por una; y **qué población aparece realmente en la lista**, porque el cargador no filtra por extensión (§2.2) y la evidencia de código dice que los 26 `.Studio.R` desplegados también se registran. Lo segundo se comprueba en un minuto con Excel abierto y decide el asunto de §3.4 |
| **El número de funciones que `ls(globalenv())` devuelve en ejecución** | Las 93 definiciones son una medición estática de los 63 `.R`. Lo que se registra en Excel es lo que hay en `globalenv()` tras cargar también `startup.r`, el dispatcher y los ficheros de producción sin origen en el repositorio (§8.1), y eso exige una sesión real de R |
| **El comportamiento del modelo ante contenido hostil del RAG** (`SEC-21`) | Exige ejecutar el agente con un proveedor de LLM. Lo verificado es que no hay ejecución automática de acciones |
| **El emparejamiento uno a uno con la auditoría previa** | `src\docs\INFORME_AUDITORIA.md` no usa identificadores estables y `hallazgos_seguridad.md` no tiene campo de estado |
| **"26 capítulos" de documentación, "11 formatos del visor", "nueve módulos de Studio", "cinco capas del SandboxVerifier"** (afirmaciones del paper) | No hay en el código una definición que permita contarlos; se declaran no verificadas en lugar de darlas por buenas |
| **Qué copia es la correcta en los 20 ficheros divergentes repo↔producción** (§8.1) | Se midieron nombre, hash, fecha y tamaño, que es lo que permite afirmar que divergen y en qué dirección hay más contenido. Decidir cuál es la fuente de verdad exige leer los diffs uno por uno con el autor delante, y es trabajo de `B-08`, no de esta auditoría |
| **El veredicto de cada una de las 27 especificaciones** | Es HIPÓTESIS salvo donde se cita evidencia; cerrarlas exige revisar sus tareas una por una (`B-21`) |
| **La causa de `SEC-11`** (`/guard:cf` ausente en el enlazado) | HIPÓTESIS; la prueba es trivial: añadir el flag, reconstruir y volver a leer los 2 bytes |

---

## 10. Skills del catálogo usados en la auditoría

Seis skills del catálogo se cargaron y se aplicaron; uno se evaluó y se descartó por no aplicar.

| Skill | Eje | Para qué, y qué produjo |
|---|---|---|
| `citation-verification` | 2 | `verify_citations.py` contra Crossref, OpenAlex y arXiv sobre las 41 entradas de `src\docs\Paper\references.bib`. **Es el skill que detectó `COD-46`**: el DOI de `Panko2016` apunta a un artículo de otro autor del mismo número de la revista. También permitió clasificar como falsos positivos legítimos las 16 entradas de software y literatura gris, y confirmar que `BERT2018` es "Basic Excel R Toolkit", no el BERT de PLN, es decir que no es una referencia fabricada |
| `bibtex-hygiene` | 2 | `bib_lint.py` sobre `references.bib`: `41 entries: 0 errors, 0 warnings, 0 info`. Línea base limpia que conviene mantener al añadir referencias |
| `unslop-academic-writing` | 1, 2 | `slop_check.py` sobre las nueve secciones del paper y sobre la documentación de usuario. Resultado: `00_abstract.tex` 6,0, `05_discussion.tex` 1,6, el resto 0,0; `Guia_usuario.md` y `Guia_inicio_rapido.md` 0,0; `TROUBLESHOOTING.md` 6,8; `src\README.md` **10,0** con frases de 39,5 palabras de media (`PROD-27`). Da número de línea, no impresiones |
| `scientific-writing` | 2, 4 | Criterio de consistencia numérica entre las afirmaciones del paper y el código medido. Sostiene `COD-47` (342 tests publicados frente a 369 reales) y `COD-48` (70 procedimientos Julia frente a 60 definiciones; "más de 200 funciones numéricas" no verificable). La afirmación paralela sobre R sí se sostiene |
| `statistical-analysis` | 2 | Revisión de la corrección estadística de la librería R. Fundamenta `COD-30` (0 ocurrencias de `shapiro.test`, `dwtest`, `confint`, `cooks.distance`, `resettest`, `p.adjust`, `Box.test`, `kpss` y de cualquier tamaño de efecto estandarizado en los 63 ficheros) y `COD-31` (`vcovHC(type="HC")` es HC0; para 30-200 filas la recomendación es HC3) |
| `metaheuristic-optimization` | 2 | Se cargó para revisar `src\libreria\JULIA\J4XCL-OP-Optimizacion.jl` y **se concluyó que no aplica**: el fichero implementa métodos deterministas (gradiente, momentum, Newton, bisección, simplex, NNLS), y no hay metaheurísticas en ningún `.jl` del proyecto. Se dice explícitamente en lugar de forzarlo. Sus criterios transversales sí sirvieron: los criterios de parada del fichero son correctos, y el defecto real es la semántica sobrecargada de `Parametro` (`COD-34`) |
| `ontology-book-processor` | — | **No se cargó.** Sirve para ingerir PDFs al grafo de conocimiento, no para validar la ontología ni sus invariantes. Además el proyecto ya tiene su propio pipeline (`docs\COMO_AGREGAR_LIBROS.md`, los siete `ontology_*_enricher.py` y `rag_engine.py`), lo que convierte al skill en una segunda descripción del mismo procedimiento |

**El eje 3 se ejecutó sin ningún skill**, porque el catálogo no tiene ninguno de seguridad. Sí se
cargó la herramienta MCP `rea` para la parte binaria y se descartó su uso: la pregunta de
`SEC-11` se responde leyendo dos bytes de la cabecera PE, y se resolvió con un parser propio
**validado contra binarios de referencia** (`kernel32.dll` → `0x4160`, `notepad.exe` → `0xC160`).
Sin esa validación el dato no sería defendible.

**Lo que el catálogo no tiene**, para que no se dé por cubierto: revisión de código y análisis
estático de C++, AppSec y modelado de amenazas, dependencias y SBOM, Windows/COM/Excel SDK,
usabilidad o diseño de producto, y validación de ontologías contra código. Los dos ejes técnicos,
que son el núcleo de lo que pidió el usuario, se auditaron **sin apoyo instrumental**, contra las
62 invariantes, los informes previos de `src\docs\audit\`, `src\SECURITY.md`, `src\docs\sops\*` y
el código. La cobertura instrumental de esta auditoría es asimétrica, y conviene saberlo al leer
sus conclusiones. Es también el argumento más fuerte a favor del ítem `B-04`: si no hay skill que
valide la ontología contra el código, hay que convertir las invariantes en tests.

**Skills del repositorio**, que son otra cosa: `.agents\skills\research-agent\` contiene copias de
cinco skills del catálogo y `.agents\skills\` otras dos, sin que nada declare cuál manda (es el
mismo patrón de `B-08` aplicado a los skills). Y `.agents\skills\{econometria, excel-consultant,
statistical-analysis, unslop-academic, citation-verification}` no son herramientas del auditor:
son los skills de *runtime* que el agente de NEVEN carga para atender al usuario final. Sobre
esos, el eje 3 dejó un veredicto que conviene no olvidar: **`restricted_to_rag` no es una defensa
técnica contra inyección de prompt**, es una restricción de las fuentes que el agente debe citar,
aplicada en el prompt. El skill local `.kiro\skills\rj2xcl-docs\SKILL.md` describe el proyecto con
su nombre antiguo y cita `docs/ESTADO_DE_LAS_COSAS.md`, ruta que no existe: entra en `B-10`.

---

## 11. Nota sobre instrucciones embebidas en ficheros

Varios ficheros del proyecto contienen directivas dirigidas a agentes:
`src\docs\SIDECAR_FORMAT.md` (sección "Notas para el Agente IA"),
`src\docs\AGENT_INSTRUCTIONS.md`, `src\docs\Paper\redactor-academico.md`,
`src\docs\Paper\auditor-forense-ia.md`, `.kiro\skills\*\SKILL.md`, `.agents\skills\*\SKILL.md`, y
el comentario imperativo de `src\CMakeLists.txt:96-97` ("Default ON is correct — do NOT set to
OFF" sobre `NEVEN_ENABLE_PYTHON`).

Todos son artefactos legítimos del proyecto. **Ninguno fue obedecido**: se trataron como dato, y
donde su contenido afecta al resultado se recoge como hallazgo (`SIDECAR_FORMAT.md` documenta una
ruta de despliegue falsa, `PROD-26`; el skill `rj2xcl-docs` cita rutas inexistentes). **No se
detectó ninguna directiva que intente redirigir al auditor contra la intención del usuario.**

---

## 12. Trazabilidad

| Documento | Contenido |
|---|---|
| `00-layout-real.md` | Layout real verificado, 22 referencias documentales obsoletas, inventario de las 62 invariantes, 18 hallazgos de inventario |
| `plan-auditoria.md` | Plan de los cuatro ejes, reglas de ejecución, skills evaluados |
| `01-notas-producto.md` | 29 hallazgos `PROD-*` con evidencia y el procedimiento de verificación manual de la descarga de audiolibros |
| `02-notas-codigo.md` | 56 hallazgos `COD-*`, tabla de veredictos de invariantes, auditoría del paper |
| `03-notas-seguridad.md` | 24 hallazgos `SEC-*`, veredicto por superficie, procedimiento de verificación del arreglo `9eba8b1` |
| `04-notas-mejoras.md` | Consolidación de los 126 candidatos en 55 mejoras, estado de las 27 especificaciones, cambios de ontología, lo descartado y por qué |
| `informe-auditoria.md` | Este documento |
| `plan-de-trabajo.md` | PENDIENTES, POR MEJORAR y NUEVAS IDEAS, con prioridad, rutas, invariantes, hallazgo de origen y coste |

---

## 13. Estado del árbol de trabajo al cerrar la auditoría · VERIFICADO

Esta auditoría es de solo lectura y conviene dejar constancia medible de ello, porque un árbol con
cambios sin explicar hace que el siguiente commit arrastre lo que nadie reclama.

`git status --porcelain` en `F:\ANTIGRAVITY\2026\NEVEN`, al cierre:

| Entrada | Qué es | Veredicto |
|---|---|---|
| ` M .kiro/contexto/CHAT.md` | Consolidación de la bitácora, que el usuario pidió expresamente al aprobar el plan, más las entradas de sesión que exige la regla de bitácora | justificado |
| ` M .kiro/contexto/CHAT_LARGO.md` | Destino del volcado de esa consolidación | justificado |
| `?? .agents/tasks/` | Los documentos de trabajo y los dos entregables | justificado |
| `?? $reportPath/` | Artefacto del 07/11, anterior a la auditoría. Es el hallazgo `LAY-17` | preexistente |
| `?? NEVEN.code-workspace` | Fichero del editor del 15/11, anterior a la auditoría | preexistente |

**Ningún fichero de código del repositorio está modificado. Nada se escribió en `C:\NEVEN\`:** cero
ficheros de producción con fecha de escritura posterior al inicio de la auditoría, comprobado en la
raíz y en `functions`, `startup`, `taskpane`, `Audiobook`, `certs`, `docs` y `data`.

**Una anomalía detectada durante la auditoría, ya resuelta.** `.kiro\contexto\Notebooklm.md`, un
fichero versionado con notas de integración con NotebookLM, apareció borrado del árbol de trabajo a
mitad de la auditoría sin que ninguna sesión lo reclamara, y `CHAT.md:1530` lo registró como
pendiente 9. Al cierre está **restaurado e idéntico a `HEAD`** (`git diff HEAD` sin salida) y ya no
aparece en `git status`. Queda una tarea de bitácora, no de código: cerrar ese pendiente 9 de
`CHAT.md`. No se abre ítem de plan por ello, porque no hay cambio de código que planificar; se
registra aquí para que no vuelva a aparecer como anomalía sin origen.

El borrado no fue obra de esta auditoría —que no escribe fuera de
`.agents\tasks\auditoria-neven\`— y su causa no se determinó: es la única afirmación de esta
sección que queda como **NO VERIFICADA**, por falta de registro de qué proceso lo borró.



