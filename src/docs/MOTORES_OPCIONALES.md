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
| `neven-config.json`, `NEVEN.<Lang>.home` | Instalacion concreta a usar; si el directorio no existe, se ignora y se vuelve a la deteccion automatica | El instalador, solo para los motores detectados | `DiscoveryService::GetBestVersion` |
| `neven-config.template.json` | Plantilla publica en el repo (`R` habilitado, `Julia` y `Python` no). El build la copia a `Dist/neven-config.json`; el instalador la sobrescribe con la deteccion | El build (`Addin/CMakeLists.txt`) | El instalador |

Semantica de `enabled`, igual en C++, en el servidor HTTP y en `start_studio.py`:

- seccion `NEVEN.<Lang>` ausente: no declarado (`LanguageConfigState::NotInConfig`);
- seccion presente sin la clave `enabled`: habilitado;
- `"enabled": false`: desactivado por el usuario.

Cambiar motores no obliga a reinstalar. Hay dos caminos:

1. NEVEN Studio > Settings > Motores (escribe `enabled` via el servidor HTTP);
2. `Install-NEVEN.ps1 -ConfigureOnly` sobre un `neven-config.json` existente, que
   redetecta los tres motores y reescribe `enabled` y `home`. Pisa un
   `enabled: false` previo a proposito: el usuario pidio reconfigurar.

En ambos casos el cambio surte efecto al reiniciar Excel (`INV-CMN-01`). El Ribbon no
escribe `enabled`; su boton **Motores** solo muestra la salida de `NEVEN.Status`.

## Las 8 combinaciones

La suite `src/tests/engine_matrix_tests.cc` parametriza el subconjunto como mascara de
bits: bit0 = R, bit1 = Julia, bit2 = Python. El indice de la mascara es el sufijo `/N`
de los tests `EngineMatrix/EngineSubsetTest.*`.

| # | R | Julia | Python | Formulas de Excel | `NEVEN.Status` | Ribbon | TaskPane | Instalador |
|---|---|---|---|---|---|---|---|---|
| 0 | no | no | no | Toda formula de motor devuelve el texto del motor que le toca, con motivo y enlace. `NEVEN.Status` y las funciones sin motor siguen registradas | `0/3 motores conectados`, nombra los tres con su sitio oficial | **Motores** lista los tres como ausentes; **Pluto** responde nombrando Julia y su enlace | Los tres puntos en rojo o gris con su motivo; el selector de lenguaje conserva las tres opciones anotadas `(no instalado)` | `Engines enabled: none` + una linea por motor con su enlace |
| 1 | si | no | no | R responde; Julia y Python devuelven su propio motivo y enlace | `[R] OK`; Julia y Python ausentes con su URL | **Motores** muestra R conectado; **Pluto** nombra Julia | R conectado; Julia y Python con su estado y enlace | `Engines enabled: R` |
| 2 | no | si | no | Julia responde; R y Python devuelven su propio motivo | `[J] OK`; R y Python ausentes con su URL | **Motores** muestra Julia conectado; **Pluto** arranca | Julia conectado; R y Python con su estado | `Engines enabled: Julia` |
| 3 | si | si | no | R y Julia responden; Python devuelve su motivo | `[R] OK`, `[J] OK`; Python ausente con su URL | **Motores** muestra R y Julia; **Pluto** arranca | R y Julia conectados; Python con su estado | `Engines enabled: R, Julia` |
| 4 | no | no | si | Python responde; R y Julia devuelven su motivo | `[P] OK`; R y Julia ausentes con su URL | **Motores** muestra Python; **Pluto** nombra Julia | Python conectado; R y Julia con su estado | `Engines enabled: Python` |
| 5 | si | no | si | R y Python responden; Julia devuelve su motivo | `[R] OK`, `[P] OK`; Julia ausente con su URL | **Motores** muestra R y Python; **Pluto** nombra Julia | R y Python conectados; Julia con su estado | `Engines enabled: R, Python` |
| 6 | no | si | si | Julia y Python responden; R devuelve su motivo | `[J] OK`, `[P] OK`; R ausente con su URL | **Motores** muestra Julia y Python; **Pluto** arranca | Julia y Python conectados; R con su estado | `Engines enabled: Julia, Python` |
| 7 | si | si | si | Las tres familias responden: 100% de la herramienta | `3/3 motores conectados` | Todos los botones operativos | Los tres puntos en verde, sin anotaciones | `Engines enabled: R, Julia, Python` |

Un motor declarado y habilitado pero sin conexion viva no se confunde con un motor
ausente: la celda dice `not connected`, `NEVEN.Status` dice `activado, sin conectar` y
el TaskPane dice `Habilitado, sin conectar`. Los otros dos estados tienen su propio
texto: `DESACTIVADO por el usuario` / `Desactivado` y `NO INSTALADO` / `No instalado`.

## Como se comprobo cada fila

`N` es el indice de la fila en la tabla de arriba.

| Fila | GTest (`ctest -C Release -R EngineMatrix`) | pytest (`python -m pytest src/tests/test_engine_availability.py -q`) | Instalador |
|---|---|---|---|
| 0..7 | `EngineMatrix/EngineSubsetTest.ServicesContainExactlyTheSubset/N` (el subconjunto configurado es exactamente el esperado) | `test_detect_reports_the_documented_keys_for_every_engine` | `Install-NEVEN.ps1 -ConfigureOnly -Silent -InstallDir <dir>` sobre un `neven-config.json` de prueba: reescribe `enabled` y `home` desde la deteccion y sale 0 |
| 0..7 | `EngineMatrix/EngineSubsetTest.AbsentEngineReportsItselfAndNeverAnotherEngine/N` (el motivo es del motor pedido, nunca de otro) | `test_disabled_engine_is_reported_as_not_enabled`, `test_engine_without_section_is_not_declared_and_does_not_crash` | idem |
| 0..7 | `EngineMatrix/EngineSubsetTest.NevenXFunctionsReportTheirOwnAbsentEngine/N` (`NevenX.R` / `NevenX.J` / `NevenX.P`) | `test_engines_endpoint_keeps_its_boolean_shape`, `test_get_router_serves_the_engines_config_endpoint` | idem |
| 0..7 | `EngineMatrix/EngineSubsetTest.PresentButUnconnectedEngineReportsNotConnected/N` | `test_enabled_engine_with_empty_home_is_not_installed`, `test_home_with_the_expected_file_is_installed[r\|julia\|python]` | idem |
| 0..7 | `EngineMatrix/EngineSubsetTest.StatusNamesTheThreeEnginesWithTheirUrls/N` | `test_download_urls_are_the_official_https_pages` | `Show-EngineSummary` imprime el enlace oficial de cada motor ausente |
| 0 | `EngineMatrixTest.StatusWithoutAnyEngineNamesAllThreeAndTheirUrls` | `test_resolve_languages_without_any_enabled_engine_is_empty`, `test_resolve_languages_without_neven_section_is_empty` | `Engines enabled: none`, el instalador no aborta |
| 0..6 | `EngineMatrixTest.ConfigStatesDistinguishDisabledFromMissing`, `EngineMatrixTest.UndiscoverableEngineIsReportedAsNotFound` | `test_missing_config_file_is_not_an_error`, `test_malformed_config_file_is_not_an_error` | el modo actualizacion conserva un `enabled: false` del usuario |
| 0, 1, 4, 5 (sin Julia) | `EngineMatrixTest.PlutoStartWithoutJuliaNamesJuliaAndItsUrl` | `test_resolve_languages_uses_the_enabled_engines`, `test_resolve_languages_prefers_auto_start_engines` | `Show-EngineSummary` nombra Julia con su enlace |
| 7 | `EngineMatrixTest.NumericKeysOutOfRangeStillFail` (con los tres motores, una clave fuera de rango sigue fallando) | `test_resolve_languages_cli_wins_over_the_config`, `test_resolve_languages_standalone_wins_over_enabled`, `test_resolve_languages_drops_unknown_names` | `Engines enabled: R, Julia, Python` |

Las tres copias versionadas del servidor HTTP (`src/TaskPane`, `src/startup`,
`src/ControlPython/startup`) exponen el mismo contrato de motores y
`test_the_three_copies_expose_the_same_engine_contract` lo verifica (`G-TP-05`).

Resultados de la ultima ejecucion: `ctest -C Release -R EngineMatrix` 45/45 passed;
`python -m pytest src/tests/test_engine_availability.py -q` 44 passed.

## Invariantes relacionadas

- `INV-CMN-01`: un cambio de `enabled` surte efecto al reiniciar Excel.
- `INV-CORE-01`: las funciones no se re-registran fuera de `xlAutoOpen`, por eso el
  motivo de un motor ausente llega como texto de la funcion ya registrada.
- `INV-BLD-04`: `Addin/CMakeLists.txt` copia `Install/neven-config.template.json` a
  `Dist/neven-config.json`; el `neven-config.json` real nunca va al repo
  (`INV-INS-01`).
- `INV-TEST-03`: esta matriz se verifica sin R, Julia ni Python instalados.
