# Motores opcionales: R, Julia y Python

NEVEN entrega las conexiones a R, Julia y Python. No entrega los motores.
Instalarlos es responsabilidad del usuario y NEVEN nunca ejecuta un instalador de
terceros: solo informa de lo que falta y enlaza al sitio oficial.

Con los tres motores instalados y habilitados se usa el 100% de la herramienta. Con
uno o dos se usa la parte correspondiente: los subsistemas que no dependen de un
motor ausente siguen funcionando, y los que dependen de el devuelven el motivo y el
enlace en lugar de fallar en silencio.

Sitios oficiales (las mismas tres URL en `Common/engine_availability.h`,
`Install-NEVEN.ps1::Get-EngineStatus` y `_ENGINE_DOWNLOAD_URLS` del servidor HTTP):

| Motor | Descarga oficial |
|---|---|
| R | https://cran.r-project.org/bin/windows/base/ |
| Julia | https://julialang.org/downloads/ |
| Python | https://www.python.org/downloads/ |

## Que escribe y lee cada capa

| Fichero | Papel | Quien escribe | Quien lee |
|---|---|---|---|
| `neven-languages.json` | Catalogo de conexiones que NEVEN sabe hablar (nombre, prefijo, ejecutable del puente). No lleva `enabled`: no es una decision, es la oferta. | Nadie en caliente; se despliega con el producto | `LanguageManager::ConfigureLanguages`, el instalador |
| `neven-config.json`, `NEVEN.<Lang>.enabled` | Decision del usuario sobre cada motor | El servidor HTTP (unico escritor en caliente) y el instalador (`Install-NEVEN.ps1`, tambien con `-ConfigureOnly`) | `LanguageService` (C++), el servidor HTTP, `start_studio.py` |
| `neven-config.json`, `NEVEN.<Lang>.home` | Instalacion concreta a usar; si el directorio no existe, se ignora y se vuelve a la deteccion automatica | El instalador: lo escribe para los motores que detecta con version suficiente; conserva un valor escrito a mano mientras su directorio exista; lo vacia cuando el directorio ya no existe o cuando apunta a la version que la deteccion acaba de rechazar por ser inferior al minimo | `DiscoveryService::GetBestVersion` |
| `neven-config.json`, `preferences.auto_start_engines` | Recorte de los motores habilitados que arranca NEVEN Studio. No puede habilitar un motor con `enabled: false` | El servidor HTTP y el instalador, los dos desde el `enabled` persistido | `start_studio.languages_from_engine_config` |
| `neven-config.json`, `Standalone.languages` | Lista de motores que arranca NEVEN Studio en modo standalone. Tiene prioridad sobre `enabled`, asi que una lista heredada o editada a mano puede arrancar un motor que el XLL considera desactivado. El `neven-config.template.json` no la trae | Nadie en caliente; solo edicion manual | `start_studio.resolve_languages` |
| `neven-config.template.json` | Plantilla publica en el repo (`R` habilitado, `Julia` y `Python` no). El build la copia a `Dist/neven-config.json`; el instalador la sobrescribe con la deteccion | El build (`Addin/CMakeLists.txt`) | El instalador |

Semantica de `enabled`, igual en C++, en el servidor HTTP y en `start_studio.py`:

- seccion `NEVEN.<Lang>` ausente: no declarado (`LanguageConfigState::NotInConfig`);
- seccion presente sin la clave `enabled`: habilitado;
- `"enabled": false`: desactivado en el config (`LanguageConfigState::DisabledInConfig`).

Ese `false` no se atribuye al usuario en ningun texto: lo puede haber escrito el,
`neven-config.template.json` (que trae `Julia` y `Python` en `false`) o una deteccion
del instalador que no encontro el motor. Los mensajes dicen donde esta escrito el
valor y como cambiarlo.

`start_studio.py` resuelve los motores a arrancar en este orden: el argumento
`--languages`, `Standalone.languages` y, por ultimo, `enabled` recortado por
`preferences.auto_start_engines`. Las dos primeras capas ganan sobre `enabled`, de modo
que un `Standalone.languages` heredado puede dejar un motor corriendo en Studio que el
XLL reporta como desactivado. Para que las dos vistas coincidan, basta no declarar
`Standalone.languages` y dejar la decision en `enabled`.

`preferences.auto_start_engines` no es una cuarta decision: solo puede recortar la lista
de motores habilitados, nunca ampliarla. Un motor con `enabled: false` no arranca aunque
siga nombrado en una lista guardada antes en Studio, y un motor que el instalador acaba
de habilitar no se queda fuera por una lista vieja, porque `Update-NEVENConfig` reescribe
`auto_start_engines` desde el `enabled` ya persistido en la misma pasada. Las dos vias que
escriben `enabled` (el servidor HTTP y el instalador) escriben tambien esa lista.

Cambiar motores no obliga a reinstalar. Hay dos caminos:

1. NEVEN Studio > Settings > Motores (escribe `enabled` via el servidor HTTP);
2. `Install-NEVEN.ps1 -ConfigureOnly` sobre un `neven-config.json` existente, que
   redetecta los tres motores y reescribe `enabled` y `home`. Pisa un
   `enabled: false` previo a proposito: el usuario pidio reconfigurar.

El primer camino necesita Python en el equipo, porque NEVEN Studio arranca con
`python start_studio.py` y Python es tambien un motor opcional. Por eso el consejo que
cierra cada mensaje de motor ausente (`kEngineSettingsHint`) nombra los dos caminos: sin
Python, `-ConfigureOnly` es el que queda.

En ambos casos el cambio surte efecto al reiniciar Excel (`INV-CMN-01`). El Ribbon no
escribe `enabled`; su boton **Motores** solo muestra la salida de `NEVEN.Status`, y
cuando no puede leerla (complemento sin activar) dice eso y da los tres sitios
oficiales en lugar de no hacer nada.

El instalador NSIS corre esa deteccion con `-ConfigureOnly` desde `$PLUGINSDIR`, con la
ruta absoluta de `powershell.exe`, y comprueba el codigo de salida: si la deteccion no
se completa, avisa de forma visible que `neven-config.json` conserva los valores de la
plantilla y como redetectar.

## Las 8 combinaciones

La suite `src/tests/engine_matrix_tests.cc` parametriza el subconjunto como mascara de
bits: bit0 = R, bit1 = Julia, bit2 = Python. El indice de la mascara es el sufijo `/N`
de los tests `EngineMatrix/EngineSubsetTest.*`.

| # | R | Julia | Python | Formulas de Excel | `NEVEN.Status` | Ribbon | TaskPane | Instalador |
|---|---|---|---|---|---|---|---|---|
| 0 | no | no | no | Las formulas estaticas devuelven el texto del motor que les toca, con motivo y enlace; las familias por prefijo dan `#¿NOMBRE?` (nota 1). `NEVEN.Status` y las funciones sin motor siguen registradas | `0/3 motores conectados`, nombra los tres con su sitio oficial | **Motores** lista los tres como ausentes; **Pluto** responde nombrando Julia y su enlace | Los tres puntos en rojo o gris con su motivo; el selector de lenguaje conserva las tres opciones anotadas `(no instalado)` o `(desactivado)` | `Engines enabled: none` + una linea por motor con su enlace |
| 1 | si | no | no | R responde; Julia y Python devuelven su propio motivo y enlace en las estaticas (nota 1) | `[R] OK`; Julia y Python ausentes con su URL | **Motores** muestra R conectado; **Pluto** nombra Julia | R conectado; Julia y Python con su estado y enlace | `Engines enabled: R` |
| 2 | no | si | no | Julia responde; R y Python devuelven su propio motivo en las estaticas (nota 1) | `[J] OK`; R y Python ausentes con su URL | **Motores** muestra Julia conectado; **Pluto** arranca | Julia conectado; R y Python con su estado | `Engines enabled: Julia` |
| 3 | si | si | no | R y Julia responden; Python devuelve su motivo en las estaticas (nota 1) | `[R] OK`, `[J] OK`; Python ausente con su URL | **Motores** muestra R y Julia; **Pluto** arranca | R y Julia conectados; Python con su estado | `Engines enabled: R, Julia` |
| 4 | no | no | si | Python responde; R y Julia devuelven su motivo en las estaticas (nota 1) | `[P] OK`; R y Julia ausentes con su URL | **Motores** muestra Python; **Pluto** nombra Julia | Python conectado; R y Julia con su estado | `Engines enabled: Python` |
| 5 | si | no | si | R y Python responden; Julia devuelve su motivo en las estaticas (nota 1) | `[R] OK`, `[P] OK`; Julia ausente con su URL | **Motores** muestra R y Python; **Pluto** nombra Julia | R y Python conectados; Julia con su estado | `Engines enabled: R, Python` |
| 6 | no | si | si | Julia y Python responden; R devuelve su motivo en las estaticas (nota 1) | `[J] OK`, `[P] OK`; R ausente con su URL | **Motores** muestra Julia y Python; **Pluto** arranca | Julia y Python conectados; R con su estado | `Engines enabled: Julia, Python` |
| 7 | si | si | si | Las tres familias responden: 100% de la herramienta | `3/3 motores conectados` | Todos los botones operativos | Los tres puntos en verde, sin anotaciones | `Engines enabled: R, Julia, Python` |

### Nota 1: que familias de funciones llevan el motivo y cual no

No todas las funciones de Excel que dependen de un motor pueden devolver texto cuando
el motor falta, porque no todas estan registradas en ese caso.

| Familia | Sin el motor | Por que |
|---|---|---|
| `NevenX.R`, `NevenX.J`, `NevenX.P`, `NEVEN.Chart.R`, `NEVEN.Chart.J`, `NEVEN.Chart.P`, `NEVEN.Pluto.Data`, `NEVEN.Status`, `NEVEN.Pluto.Start` | Devuelven el motivo del motor que les toca y su enlace oficial | Se registran siempre en `xlAutoOpen` y resuelven el motor por nombre con `CallLanguageByName`, que ante un servicio ausente escribe `EngineUnavailableMessage` en `err` |
| `NEVEN.R`, `NEVEN.J`, `NEVEN.P` y las derivadas por prefijo (`NEVEN.<prefix>.Call`, `.Exec`) | Excel devuelve `#¿NOMBRE?`, sin motivo | La fase 2 de `RegisterBasicFunctions` itera `LanguageManager::GetServices()`, que solo contiene motores configurados, asi que esos nombres no existen en el libro (`excel_api_functions.cc` L126-182) |

Es la linea base del producto, no una regresion de los motores opcionales: la decision
esta en `plan.md` L11-15 y catalogada como `PROD-10` en `investigacion.md` §3.2. Rellenar
huecos en el vector de `GetServices()` desplazaria las claves numericas de `BCALL`/`BEXEC`,
que son posiciones de ese vector, y `INV-CORE-01` prohibe registrar funciones fuera de
`xlAutoOpen`, asi que no se puede registrar el nombre mas tarde, cuando ya se sabe que
hace falta.

Consecuencia practica para el usuario: un libro escrito con `=NEVEN.J("...")` abierto en
un equipo sin Julia muestra `#¿NOMBRE?` en esas celdas. Para ver el motivo hay que usar
`NEVEN.Status`, el boton **Motores** del Ribbon, o la forma estatica equivalente
(`=NevenX.J("...")`), que si lo dice.

La columna TaskPane describe lo que se ve cuando NEVEN Studio esta corriendo, y Studio
necesita Python. En las filas 0 a 3 (sin Python) el estado de los motores se consulta
con `NEVEN.Status` o con el boton **Motores** del Ribbon, y la configuracion se cambia
con `Install-NEVEN.ps1 -ConfigureOnly`.

Un motor declarado y habilitado pero sin conexion viva no se confunde con un motor
ausente: la celda dice `not connected`, `NEVEN.Status` dice `activado, sin conectar` y
el TaskPane dice `Habilitado, sin conectar`. Los otros dos estados tienen su propio
texto: `DESACTIVADO en neven-config.json` / `Desactivado` y `NO INSTALADO` /
`No instalado`. El selector de lenguaje de Run Script anota las dos situaciones que
hacen que el motor no responda, `(no instalado)` y `(desactivado)`, sin quitar la opcion.

Un quinto caso no es un estado de motor: que el servidor de NEVEN Studio no responda.
Entonces `/api/engines/config` no se puede leer y no se sabe nada de ningun motor, asi
que el TaskPane dice `Servidor no disponible` y el aviso de Run Script nombra el servidor
en vez de culpar al motor y en vez de remitir a Settings > Motores, que tampoco cargaria.

## Como se comprobo cada fila

`N` es el indice de la fila en la tabla de arriba.

| Fila | GTest (`ctest -C Release -R EngineMatrix`) | pytest (`python -m pytest src/tests/test_engine_availability.py -q`) | Instalador |
|---|---|---|---|
| 0..7 | `EngineMatrix/EngineSubsetTest.ServicesContainExactlyTheSubset/N` (el subconjunto configurado es exactamente el esperado) | `test_detect_reports_the_documented_keys_for_every_engine` | `Install-NEVEN.ps1 -ConfigureOnly -Silent -InstallDir <dir>` sobre un `neven-config.json` de prueba: reescribe `enabled` y `home` desde la deteccion y sale 0 |
| 0..7 | `EngineMatrix/EngineSubsetTest.AbsentEngineReportsItselfAndNeverAnotherEngine/N` (el motivo es del motor pedido, nunca de otro) | `test_disabled_engine_is_reported_as_not_enabled`, `test_engine_without_section_is_not_declared_and_does_not_crash` | idem |
| 0..7 | `EngineMatrix/EngineSubsetTest.NevenXFunctionsReportTheirOwnAbsentEngine/N` (`NevenX.R` / `NevenX.J` / `NevenX.P`) | `test_engines_endpoint_keeps_its_boolean_shape`, `test_get_router_serves_the_engines_config_endpoint` | idem |
| 0..7 | `EngineMatrix/EngineSubsetTest.ChartAndPlutoWrappersReportTheirOwnAbsentEngine/N` (`NEVEN.Chart.R` / `.J` / `.P` y `NEVEN.Pluto.Data`) | `test_both_config_readers_tolerate_a_bom` | idem |
| 0..7 | `EngineMatrix/EngineSubsetTest.PresentButUnconnectedEngineReportsNotConnected/N` | `test_enabled_engine_with_empty_home_is_not_installed`, `test_home_with_the_expected_file_is_installed[r\|julia\|python]` | idem |
| 0..7 | `EngineMatrix/EngineSubsetTest.StatusNamesTheThreeEnginesWithTheirUrls/N` | `test_download_urls_are_the_official_https_pages` | `Show-EngineSummary` imprime el enlace oficial de cada motor ausente |
| 0 | `EngineMatrixTest.StatusWithoutAnyEngineNamesAllThreeAndTheirUrls` | `test_resolve_languages_without_any_enabled_engine_is_empty`, `test_resolve_languages_without_neven_section_is_empty` | `Engines enabled: none`, el instalador no aborta |
| 0..6 | `EngineMatrixTest.ConfigStatesDistinguishDisabledFromMissing`, `EngineMatrixTest.UndiscoverableEngineIsReportedAsNotFound` | `test_missing_config_file_is_not_an_error`, `test_malformed_config_file_is_not_an_error` | el modo actualizacion conserva un `enabled: false` del usuario |
| 0, 1, 4, 5 (sin Julia) | `EngineMatrixTest.PlutoStartWithoutJuliaNamesJuliaAndItsUrl` | `test_resolve_languages_uses_the_enabled_engines`, `test_resolve_languages_prefers_auto_start_engines` | `Show-EngineSummary` nombra Julia con su enlace |
| 7 | `EngineMatrixTest.NumericKeysOutOfRangeStillFail` (con los tres motores, una clave fuera de rango sigue fallando) | `test_resolve_languages_cli_wins_over_the_config`, `test_resolve_languages_standalone_wins_over_enabled`, `test_resolve_languages_drops_unknown_names` | `Engines enabled: R, Julia, Python` |

Las tres copias versionadas del servidor HTTP (`src/TaskPane`, `src/startup`,
`src/ControlPython/startup`) exponen el mismo contrato de motores y
`test_the_three_copies_expose_the_same_engine_contract` lo verifica (`G-TP-05`).

El modo `-ConfigureOnly` ya no se comprueba solo a mano:
`python -m pytest src/tests/test_configure_only.py -q` lo ejecuta sobre una copia de la
plantilla en un directorio temporal y afirma lo que no depende de los motores que haya en
el equipo (`INV-TEST-03`): los tres `enabled` son booleanos, ningun `home` apunta a un
directorio inexistente, un `home` escrito a mano no se pierde, y
`preferences.auto_start_engines` sale del `enabled` persistido.

El `.nsi` tambien se puede comprobar entero: `powershell -File src\Install\Check-NSISSyntax.ps1`
copia `NEVEN-Setup.nsi` a un temporal con un `Dist/` de relleno (un icono y dos BMP
validos) y lo compila con `makensis`. Sin eso, `makensis` aborta en la linea 62 por
`Dist\NEVEN_studio.ico` y nunca llega a las secciones del final.

Del Ribbon se comprueba su cableado, que es lo que falla en silencio:
`RepoHygieneTests.RibbonCallbacksAreWiredInTheThreePlaces` extrae cada
`onAction`/`getPressed` de `ribbon_ui.xml` y exige las tres patas de `INV-RIBBON-01`
(valor en `DispIds`, entrada en `GetIDsOfNames`, `case` en `Invoke`). Un boton nuevo sin
cablear ya no pasa la suite.

Resultados de la ultima ejecucion: `ctest --output-on-failure -C Release --timeout 120`
425/425 passed; `python -m pytest src/tests/test_engine_availability.py -q` 50 passed;
`python -m pytest src/tests/test_configure_only.py -q` 6 passed;
`node --check src/TaskPane/taskpane.js` sin errores; `Install-NEVEN.ps1` parsea sin
errores; `Check-NSISSyntax.ps1` exit 0.

## Cierre de los hallazgos no bloqueantes de la revision

La revision semantica de `8e34a27` aprobo la rama y dejo ocho hallazgos no bloqueantes.
Esta es la decision tomada para cada uno, con donde quedo el cambio.

| # | Hallazgo | Estado |
|---|---|---|
| 1 | `preferences.auto_start_engines` ganaba sobre `enabled` y ningun camino del instalador la refrescaba | **Resuelto.** `languages_from_engine_config` la usa solo para recortar los motores habilitados, y `Update-NEVENConfig` la reescribe desde el `enabled` persistido. Tests: `test_auto_start_engines_cannot_enable_a_disabled_engine`, `test_auto_start_engines_ignores_an_engine_without_section`, `test_auto_start_engines_that_names_nothing_enabled_is_empty`, `test_auto_start_engines_is_derived_from_enabled` |
| 2 | El instalador borraba un `home` escrito a mano | **Resuelto.** Se conserva mientras su directorio exista; se vacia solo cuando ya no existe. Test: `test_a_manual_home_is_not_silently_lost`, `test_home_is_either_empty_or_an_existing_directory` |
| 3 | `home` de una version inadecuada sin validar | **Resuelto.** `Get-EngineStatus` publica `Path` solo cuando el motor es `Available` (version suficiente), y `Update-NEVENConfig` vacia un `home` que apunte a la instalacion que la deteccion acaba de rechazar por version |
| 4 | El aviso de `runScript` culpaba al motor con el servidor caido | **Resuelto.** `ENGINE_INFO_UNREACHABLE` separa "no se pudo leer el estado" de "el motor no esta": el aviso nombra el servidor de Studio y no remite a Settings > Motores |
| 5 | El selector de lenguaje solo anotaba "no instalado" | **Resuelto.** `annotateScriptLangOptions` anota tambien `(desactivado)` |
| 6 | La copia de `Install-NEVEN.ps1` en `$INSTDIR` y el consejo de ejecutarla | **Resuelto, con el problema reformulado.** La ACL efectiva medida en una instalacion real (`icacls C:\NEVEN`) muestra `NT AUTHORITY\Authenticated Users:(I)(OI)(CI)(IO)(M)` heredado de `C:\`: los ficheros de `$INSTDIR` son modificables por cualquier usuario autenticado, asi que `-ConfigureOnly` **no** necesita elevacion para reescribir el config (lo que el hallazgo temia), pero el script desplegado era manipulable por cualquier usuario y el instalador invita a ejecutarlo. El `.nsi` le quitaba la herencia solo a ese fichero; el endurecimiento se extendio despues a todo `$INSTDIR` con `Set-InstallPermissions.ps1`, que comprueba el resultado de cada operacion y lo deja auditable con `-AuditOnly`. El aviso menciona la elevacion solo para el caso de una carpeta protegida. Detalle en P4 `install_scripts.permisos_instalacion` e `INV-INS-05` |
| 7 | La tabla de las 8 combinaciones prometia mas de lo que hay | **Resuelto en la documentacion.** Nota 1: las familias por prefijo (`NEVEN.R`, `NEVEN.J`, `NEVEN.P`, `.Call`, `.Exec`) dan `#¿NOMBRE?` sin motivo, con la razon y lo que el usuario puede hacer en su lugar. No se registran stubs: desplazaria las claves de `BCALL`/`BEXEC` e `INV-CORE-01` prohibe registrar fuera de `xlAutoOpen` |
| 8 | Sin cobertura automatica del Ribbon, de `-ConfigureOnly` ni del bloque NSIS | **Resuelto.** `src/tests/test_configure_only.py` ejecuta `-ConfigureOnly`; `src/Install/Check-NSISSyntax.ps1` compila el `.nsi` completo con un `Dist/` de relleno, asi que `makensis` ya pasa de la linea 62; y `RepoHygieneTests.RibbonCallbacksAreWiredInTheThreePlaces` comprueba las tres patas de `INV-RIBBON-01` para cada `onAction`/`getPressed` de `ribbon_ui.xml`. Lo que sigue sin automatizar es el comportamiento del Ribbon en ejecucion: `NEVENRibbon.dll` solo recibe sus callbacks desde Excel via `IDTExtensibility2` e `INV-TEST-03` exige que la suite corra sin Excel, asi que ahi la comprobacion es manual |

## Invariantes relacionadas

- `INV-CMN-01`: un cambio de `enabled` surte efecto al reiniciar Excel.
- `INV-CORE-01`: las funciones no se re-registran fuera de `xlAutoOpen`, por eso el
  motivo de un motor ausente llega como texto de la funcion ya registrada.
- `INV-BLD-04`: `Addin/CMakeLists.txt` copia `Install/neven-config.template.json` a
  `Dist/neven-config.json`; el `neven-config.json` real nunca va al repo
  (`INV-INS-01`).
- `INV-TEST-03`: esta matriz se verifica sin R, Julia ni Python instalados.
