# A-03: verificacion

Rama `a03-descarga` (base 12aa43d). Logs en este directorio: `ctest.log`, `python-tests.log`, `python-tests-2.log`, `log-before.txt`, `log-after.txt`.

## Hallazgos

| # | Hallazgo | Cambio | Comprobacion |
|---|----------|--------|--------------|
| 1 | Parpadeo/recarga del TaskPane al pulsar DESCARGAR | `audiobook.js` `downloadM4B`: `abFetch` (con `X-NEVEN-Token`) -> `Blob` -> `<a download>` con URL `blob:`. No navega al origen `http://localhost:5557`. Los errores llegan al usuario por toast con motivo y codigo HTTP | `node src/tests/js/audiobook_download_check.js`: 4 casos ok (descarga, 404 con motivo, error de red, sin resultado), sin escritura en `location`. Sin probar en Excel real: pendiente del usuario |
| 2 | `.m4a`/`.m4b` (PROD-03) | `DEFAULT_AUDIOBOOK_EXTENSION = ".m4b"`; `AUDIOBOOK_EXTENSIONS = (".m4b", ".m4a")` para `/api/books`, `/api/serve`, `/api/download/file`, `/download`; textos M4B en pipeline | tests 7 y 8: muxer real con ffmpeg produce `.m4b` (contenedor mp4, AAC) y se descarga byte a byte; un `.m4a` existente se sigue listando |
| 3 | La suite escribia en `C:\NEVEN\neven_http.log` | `src/conftest.py` fija `NEVEN_LOG_DIR` a un temporal antes de recolectar. Causa: el primer import del servidor (TaskPane/tests sin la variable) enganchaba el handler global de `NEVEN.HTTP` a `C:\NEVEN` | `test_log_isolation_a03.py` falla sin el arreglo (handler en `C:\NEVEN\neven_http.log`) y pasa con el arreglo. Log de produccion antes/despues de ctest y de dos pasadas completas de la suite: 447.932 bytes, `LastWriteTime` 11:41:56, ultima linea igual |
| 4 | Endpoint `/api/download` | Sin `unquote`; contencion con `commonpath` sobre `realpath` (403 fuera); 404 exacto con `requested`, sin fallback por prefijo; `download_name=basename`; href de `/download` con `quote(..., safe='')` | `test_audiobook_download_a03.py`: 23 pasados contra el servidor real. Contra el servidor de 12aa43d fallan 9 (fallback `Miguel`, `Miguel%20de`, `a`, `legacy`; `%2520`; hermano `out_x` x3; href sin codificar) |
| 5 | Token de un solo uso para el QR con `lan=true` | No se hace (A-03 no lo incluye). Declarado en `src/SECURITY.md` como pendiente propio | - |

URLs: `audiobook.js` ya usa ruta relativa para el servidor principal; el unico `http://` es `http://localhost:5557` (servidor de audiolibros, sin TLS por diseno). Los `localhost:5555` de `taskpane.html`, `taskpane.js`, `chart-gallery.js` y `ontology-graph.html` no se tocaron.

## Seis pasos de verificacion (automatizados)

1. Protocolo: la pagina https llama al 5557 por `fetch` (caso JS); no hay navegacion.
2. Servidor en primer plano: subproceso real en puerto libre.
3. Peor nombre legal (`Miguel de Cervantes - Don Quijote de la Mancha á é í.m4b`): 200, bytes iguales, `audio/mp4`, `attachment`.
4. Negativo `/api/download/Miguel`: 404 con `requested`, sin bytes del fichero.
5. Pagina `/download` (sin movil): href `%20`/`%C3%A1`; seguirlo da 200 y los bytes del mas reciente.
6. Guardia intacta: `Origin: https://evil.example` -> 403; sin token -> 200 (exencion del QR); `POST /api/upload` sin token -> 401.

El registro de este procedimiento en `CHAT.md` no se hizo (restriccion del encargo).

## Suites

- ctest (`ctest -C Release`, VS2022 CMake): **100% tests passed, 0 failed out of 438**. El `cmake --build` completo falla al enlazar ControlJulia (`src/ControlJulia/lib/libjulia.lib` no existe en el worktree, fichero sin versionar); se construyo solo `rj2xcl_tests` (no hay cambios en C++).
- `python src/scripts/run_python_tests.py`, dos pasadas con Excel y el servidor de produccion en marcha (no se pararon desde el workflow): 627 recogidos, 606 pasados, 14 esperado-fallo, 7 marcados nuevos en cada pasada:
  - `test_start_studio_4_4` (4-5 tests): `SystemExit: 1` por el mutex de instancia unica del Studio de produccion. Mismo efecto descrito en 12aa43d.
  - `test_datalab_handler::test_property_*` (2-3, varian entre pasadas): `hypothesis DeadlineExceeded`. Con el `conftest.py` de 12aa43d, `test_property_1_catalog_filtering` tambien falla por deadline en este equipo; con el de A-03, aislado, pasa. Es tiempo, no este cambio.
  - `test_http_server_7_4::test_probe_pipe_called_for_each_language` fallo en la primera pasada y paso en la segunda y aislado.
  - Los tests nuevos de A-03 (`test_log_isolation_a03`, `test_audiobook_download_a03`) pasan en ambas pasadas.
  - Para dejar 0 nuevos hay que repetir la suite con el Studio de produccion parado.

## Despliegue (preparado, no ejecutado)

`deploy/manifest.json` (6 ficheros: `neven_audiobook_server.py`, `api/routes.py`, `pipeline.py`, `muxer/ffmpeg_muxer.py`, `taskpane/audiobook.js`, `neven-ontology-p3.yaml`). `Deploy-NEVEN.ps1 -DryRun` y `Rollback-NEVEN.ps1 -DryRun` terminan sin errores y listan los mismos ficheros (`deploy/dryrun-*.txt`). En 3 destinos el hash no coincide con 12aa43d (`neven_audiobook_server.py`, `audiobook.js`, P3): el contenido es identico salvo fin de linea (CRLF de git frente a LF desplegado), sin cambios manuales en produccion. No se copia `neven-config.json`, el manifiesto del complemento, `startup/neven_http_server.py` ni sus copias. El despliegue real exige cerrar Excel y la aprobacion del usuario.