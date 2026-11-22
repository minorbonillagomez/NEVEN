# 00 — Layout real del workspace NEVEN

**Fecha de verificación:** 2026-11-20
**Raíz del workspace:** `F:\ANTIGRAVITY\2026\NEVEN`
**Rama git activa:** `master` (HEAD = `9eba8b1`, sincronizada con `origin/master`)
**Método:** enumeración directa del árbol de ficheros y `git ls-files`. No se asumió ningún prefijo documentado.

---

## 1. Conclusión en una frase

**El prefijo verdadero del código es `src\`.** El repositorio git está en la raíz del
workspace (`F:\ANTIGRAVITY\2026\NEVEN\.git`) y todo el proyecto C++/R/Julia/Python vive bajo
`F:\ANTIGRAVITY\2026\NEVEN\src\`. El prefijo `NEVEN\NEVEN\...` que aparece en la
documentación y en los hooks **ya no existe**: desapareció en el commit `951cfcb`
("refactor: reorganizar estructura de carpetas del repositorio").

---

## 2. Árbol real — primer nivel

| Entrada | Tipo | Contenido | Tracked |
|---|---|---|---|
| `.agents\` | dir | Skills locales (`skills\`) y tareas (`tasks\`) | sí (61 ficheros) |
| `.git\` | dir | Repositorio git del workspace completo | — |
| `.kiro\` | dir | `contexto\`, `evals\`, `hooks\`, `skills\`, `specs\`, `steering\` | sí (147) |
| `.pytest_cache\` | dir | Caché de pytest | no |
| `.vscode\` | dir | Configuración del editor | sí (1) |
| `$reportPath\` | dir | **Artefacto accidental**: variable PowerShell no expandida; contiene `DCUApplicableUpdates.xml` (169 B) | no |
| `android\` | dir | App Android (NEVEN Launcher + AudioLibros), Gradle/Kotlin | sí (955) |
| `docs\` | dir | Solo `COMO_AGREGAR_LIBROS.md` + `ontologia\` (dominios de grafos) | sí (334) |
| `external\` | dir | `anyplot\` (dependencia externa con su propio pyproject/tests) | sí (1) |
| `ontologia-fuentes\` | dir | PDFs fuente de libros (ALGEBRA, LIBROS ANALISIS DE DATOS, LIBROS ECONOMETRIA, LIBROS EXCEL, NEVEN, VBA) | sí (50) |
| `src\` | dir | **El proyecto NEVEN** | sí (952) |
| `.gitignore` | file | 292 B | sí |
| `MIGRACION.md` | file | 6.952 KB — describe un layout obsoleto (ver §4) | sí |
| `NEVEN.code-workspace` | file | 95 B | **no** (untracked) |

Total tracked: **2.508 ficheros**.

### Segundo nivel de `src\`

```
src\
├── .agent\                    ├── Include\                 (mock headers R/Julia/Excel SDK)
├── .github\                   ├── Install\                 (instalador + Dist\ generado)
├── Addin\                     ├── libreria\                (R, JULIA, PYTHON, QUARTO, EJEMPLOS)
├── AgentService\              ├── NEVEN-SIM\               (XLL Monte Carlo + tests propios)
├── Audiobook\                 ├── OfficeTypes\
├── Build\                     (generado, no tracked)       ├── ontology\
├── Common\                    ├── PB\
├── ControlJulia\              ├── Releases\
├── ControlPython\             ├── Ribbon\
├── ControlR\                  ├── scripts\
├── Core\                      ├── startup\
├── CreadorPresentaciones\     ├── TaskPane\
├── Dist\                      ├── tests\
├── docs\                      └── tools\
├── functions\
├── iconos\
```

### Segundo nivel de `.kiro\`

```
.kiro\
├── contexto\     CHAT.md, CHAT_LARGO.md, Notebooklm.md, README.md, archivo\
├── evals\        run_evals.py + 4 suites YAML (agent_behavior, i18n-taskpane, ontologia-*)
├── hooks\        load-ontology-context.json, save-chat-on-stop.json,
│                 update-knowledge-base.kiro.hook, validate-before-run.json/.ps1
├── skills\       auditor-forense-ia\, rj2xcl-docs\
├── specs\        25 especificaciones (requirements/design/tasks)
└── steering\     8 ficheros .md
```

---

## 3. Ubicación real confirmada de cada pieza

| Pieza | Ruta absoluta real | Verificación |
|---|---|---|
| **Core** (NEVEN.dll / NEVEN64.xll) | `F:\ANTIGRAVITY\2026\NEVEN\src\Core` | 53 ficheros, 47 de código, 418 KB |
| **ControlR** | `F:\ANTIGRAVITY\2026\NEVEN\src\ControlR` | 40 ficheros, 26 de código |
| **ControlJulia** | `F:\ANTIGRAVITY\2026\NEVEN\src\ControlJulia` | 20 ficheros, 11 de código |
| **ControlPython** | `F:\ANTIGRAVITY\2026\NEVEN\src\ControlPython` | 34 ficheros, 18 de código |
| **Common** (Common.lib) | `F:\ANTIGRAVITY\2026\NEVEN\src\Common` | 90 ficheros, 88 de código, 528 KB |
| **PB** (PB.lib, variable.proto) | `F:\ANTIGRAVITY\2026\NEVEN\src\PB` | 5 ficheros |
| **Ribbon** (NEVENRibbon.dll) | `F:\ANTIGRAVITY\2026\NEVEN\src\Ribbon` | 36 ficheros; `ribbon_connect.h`, `ribbon_ui.xml` aquí |
| **NEVEN-SIM** | `F:\ANTIGRAVITY\2026\NEVEN\src\NEVEN-SIM` | 37 ficheros + `tests\CMakeLists.txt` propio |
| **Addin** (empaquetado XLL) | `F:\ANTIGRAVITY\2026\NEVEN\src\Addin` | 3 ficheros (CMakeLists + catalog) |
| **Include** (mock headers) | `F:\ANTIGRAVITY\2026\NEVEN\src\Include` | 30 headers |
| **tests C++ (GTest)** | `F:\ANTIGRAVITY\2026\NEVEN\src\tests` | 32 `.cc` en CMake + runners `.R`/`.py` sueltos |
| **tests Python TaskPane** | `F:\ANTIGRAVITY\2026\NEVEN\src\TaskPane\tests` | 18 ficheros `test_*.py` (pytest), no en CMake |
| **tests NEVEN-SIM** | `F:\ANTIGRAVITY\2026\NEVEN\src\NEVEN-SIM\tests` | target separado, solo con `BUILD_NEVEN_SIM=ON` |
| **startup** | `F:\ANTIGRAVITY\2026\NEVEN\src\startup` | 20 ficheros: `startup.r`, `startup.jl`, `startup.py` + `.sha256` + 7 enrichers de ontología |
| **librería R** | `F:\ANTIGRAVITY\2026\NEVEN\src\libreria\R` | **63** ficheros `.R` |
| **librería Julia** | `F:\ANTIGRAVITY\2026\NEVEN\src\libreria\JULIA` | 9 ficheros: `functions.jl` + 7 módulos `J4XCL-*` + `NEVEN-export-data.jl` |
| **librería Python** | `F:\ANTIGRAVITY\2026\NEVEN\src\libreria\PYTHON` | 4 ficheros |
| **librería Quarto** | `F:\ANTIGRAVITY\2026\NEVEN\src\libreria\QUARTO` | 2 ficheros |
| **TaskPane (frontend)** | `F:\ANTIGRAVITY\2026\NEVEN\src\TaskPane` | `taskpane.html` 392 KB, `taskpane.js` 192 KB, `datalab.js` 103 KB, `audiobook.js` 32 KB, `chart-gallery.js` 87 KB |
| **Servidor HTTP Python (canónico)** | `F:\ANTIGRAVITY\2026\NEVEN\src\startup\neven_http_server.py` | 218.882 B, SHA256 `2F74824D39C3…` — **idéntico byte a byte a producción** |
| Servidor HTTP (copia obsoleta en repo) | `F:\ANTIGRAVITY\2026\NEVEN\src\TaskPane\neven_http_server.py` | 214.682 B, `CC22AE05B87D…`, 2026-10-19 — **divergente** |
| **docs** | `F:\ANTIGRAVITY\2026\NEVEN\src\docs` | 153 ficheros tracked, 18 subdirectorios |
| **docs\ontologia\neven-core** | `F:\ANTIGRAVITY\2026\NEVEN\src\docs\ontologia\neven-core` | `neven-ontology-p1..p4.yaml` + `generate_visualization.py` + `graph_visualization.html` |
| **Install** | `F:\ANTIGRAVITY\2026\NEVEN\src\Install` | 82 tracked; `Dist\` (996 ficheros, 45 MB) existe en disco pero **no** está tracked |
| **Ejemplos** | `F:\ANTIGRAVITY\2026\NEVEN\src\libreria\EJEMPLOS` | subdirs: Benchmarks, Excel, Java, Julia, Notebooks, Python, Quarto, R |
| **Paper LaTeX** | `F:\ANTIGRAVITY\2026\NEVEN\src\docs\Paper` | `main.tex` + `sections\` (7 `.tex`) + `references.bib` (41 entradas) + `arxiv-submission\` |
| Paper LaTeX anterior | `F:\ANTIGRAVITY\2026\NEVEN\src\docs\Latex` | `NEVEN_Paper.tex`, `RJ2XCL_Paper.tex`, `PropuestaV0.tex` (versiones históricas) |
| **Auditoría previa existente** | `F:\ANTIGRAVITY\2026\NEVEN\src\docs\audit` | 15 ficheros, incluye `hallazgos_seguridad.md` (191 KB) |
| Informe de auditoría previo | `F:\ANTIGRAVITY\2026\NEVEN\src\docs\INFORME_AUDITORIA.md` | v1.0, salud 6,0/10, 36 hallazgos |
| **Bitácora** | `F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md` (387.056 B) y `CHAT_LARGO.md` (1.758.526 B) | ambos sin BOM, ambos con mojibake (ver §5) |

### Ficheros `CMakeLists.txt` del árbol (12)

```
F:\ANTIGRAVITY\2026\NEVEN\src\CMakeLists.txt                   (raíz, 4.750 B)
F:\ANTIGRAVITY\2026\NEVEN\src\Addin\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\Common\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\ControlJulia\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\ControlPython\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\ControlR\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\Core\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\NEVEN-SIM\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\NEVEN-SIM\tests\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\PB\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\Ribbon\CMakeLists.txt
F:\ANTIGRAVITY\2026\NEVEN\src\tests\CMakeLists.txt
```

### Comandos de build y test reales (confirmados en `src\README.md`, `src\CONTRIBUTING.md`, `src\docs\sops\testing-guide.md`)

```powershell
cd F:\ANTIGRAVITY\2026\NEVEN\src
.\build.ps1                      # build incremental Release
.\build.ps1 -Test                # build + tests
.\build.ps1 -Clean -Test -Package
# manual:
cmake -S . -B Build -A x64 -DSKIP_LANGUAGE_TARGETS=ON
cmake --build Build --config Release --target rj2xcl_tests
cd Build; ctest --output-on-failure -C Release --timeout 120
```

Binario de tests ya compilado y usable en solo lectura:
`F:\ANTIGRAVITY\2026\NEVEN\src\Build\tests\Release\rj2xcl_tests.exe` (2026-10-20).
`--gtest_list_tests` sobre él reporta **369 tests en 47 suites**.

---

## 4. Referencias documentales desactualizadas

Todas estas citas apuntan a `…\NEVEN\NEVEN\…` o a `NEVEN\<módulo>`, rutas que ya no existen.
La ruta real sustituye `NEVEN\NEVEN\` por `NEVEN\src\`.

| Ruta citada en la documentación | Ruta real | Fichero y línea de la cita incorrecta |
|---|---|---|
| `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\docs\ontologia\neven-core\neven-ontology-p1.yaml` | `F:\…\NEVEN\src\docs\ontologia\neven-core\neven-ontology-p1.yaml` | `.kiro\hooks\validate-before-run.ps1:3` |
| `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Ribbon\ribbon_connect.h` | `F:\…\NEVEN\src\Ribbon\ribbon_connect.h` | `.kiro\hooks\validate-before-run.ps1:29` |
| `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Ribbon\ribbon_ui.xml` | `F:\…\NEVEN\src\Ribbon\ribbon_ui.xml` | `.kiro\hooks\validate-before-run.ps1:41` |
| `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Build\Dist\NEVENRibbon.dll` | `F:\…\NEVEN\src\Build\Dist\NEVENRibbon.dll` | `.kiro\hooks\validate-before-run.ps1:132` |
| `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\docs\ontologia\` | `F:\…\NEVEN\src\docs\ontologia\` | `.kiro\steering\neven-project-context.md:90` |
| `NEVEN/docs/` | `src\docs\` | `.kiro\steering\neven-project-context.md:58` |
| `NEVEN\libreria\R\R4XCL-*.R` | `src\libreria\R\R4XCL-*.R` | `.kiro\steering\neven-pre-cambios.md:142` |
| `NEVEN\Install\functions\*.json` | `src\Install\functions\*.json` | `.kiro\steering\neven-pre-cambios.md:143` |
| `NEVEN\TaskPane\neven_http_server.py` (como destino de sincronización) | `src\startup\neven_http_server.py` es la copia que sí coincide con producción | `.kiro\steering\neven-pre-cambios.md:144` |
| `NEVEN\TaskPane\*.js` | `src\TaskPane\*.js` | `.kiro\steering\neven-pre-cambios.md:145` |
| `Repo Git: F:\ANTIGRAVITY\2026\NEVEN\NEVEN\` | `F:\ANTIGRAVITY\2026\NEVEN\` (el repo es el workspace) | `MIGRACION.md:125` |
| `Ontologías: F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\` | `F:\…\NEVEN\ontologia-fuentes\` (y `docs\ontologia\`) | `MIGRACION.md:127` |
| Árbol `NEVEN/` con `Core/`, `Common/`, `docs/`… en primer nivel | todos bajo `src\` | `MIGRACION.md:36-62` |
| `cd F:\ANTIGRAVITY\2026\NEVEN\NEVEN` + `.\build.ps1` | `cd F:\ANTIGRAVITY\2026\NEVEN\src` | `MIGRACION.md:136-137` |
| `tests/ → 228 tests` | 369 tests en 47 suites (binario real) | `src\README.md:176` (y badge en `:19`) |
| `228 tests from 24 test suites` | 369 tests / 47 suites | `src\README.md:150` |
| `neven_tests.exe` | el target es `rj2xcl_tests.exe` | `src\docs\sops\testing-guide.md:26` |
| `100% tests passed … out of 357` | 369 | `src\docs\Mantenimiento\Aseguramiento_de_calidad.md:7` |
| `tests\ → 342 tests` | 369 | `.kiro\steering\neven-project-context.md` (sección "Estructura del repositorio") |
| `libreria/R/ → ~90 procedimientos, 32 archivos .R` | **63** ficheros `.R` | `.kiro\steering\neven-project-context.md` (misma sección) |
| `Ejemplos/` en primer nivel del repo | `src\libreria\EJEMPLOS\` | `.kiro\steering\neven-project-context.md` (misma sección) |
| `docs/arquitectura.md`, `coding-standards.md`, `MANUAL_MANTENIMIENTO.md`, `TROUBLESHOOTING.md`, `ESTADO_DE_LAS_COSAS.md`, `ESTADO_DEL_ARTE.md`, `contexto v1.md` | `src\docs\Arquitectura\Arquitectura.md`, `src\docs\sops\coding-standards.md`, `src\docs\Contexto\Manual_de_mantenimiento.md`, `src\docs\Mantenimiento\TROUBLESHOOTING.md`, `src\docs\Estado\Estado_de_las_cosas.md`, `src\docs\Estado\Estado_del_arte.md`, `src\docs\Contexto\Contexto_v1.md` | `.kiro\steering\neven-project-context.md:58-66` |
| `~415MB` para `neven_julia.dll` | **1.122.110.372 B ≈ 1,04 GB** en `C:\NEVEN\neven_julia.dll` | `.kiro\steering\neven-project-context.md` (sección "Notas importantes") |
| CI: `branches: [main, develop]` / `refs/heads/main` | la rama real es **`master`** → el workflow nunca se dispara | `src\.github\workflows\build-and-test.yml:5,7,13,56` |
| CI artefacto `build/RJ2XCL/Release/NEVEN64.dll` | el target CMake produce en `Build\Core\…` | `src\.github\workflows\build-and-test.yml:81` |

**Consecuencia operativa inmediata:** el hook `validate-before-run.ps1` hace `Test-Path`
sobre rutas inexistentes, por lo que todas sus validaciones basadas en la ontología se
saltan en silencio. La barrera de seguridad documentada en el steering está inactiva.

### Rutas de documentación que sí son correctas

- `C:\NEVEN\` como directorio de producción: correcto y vivo.
- `C:\NEVEN\startup\neven_http_server.py` como servidor de producción, puerto 5555: correcto
  (`neven-config.json` → `TaskPane.port = 5555`, `fallbackPort = 5556`).
- `C:\NEVEN\functions\` como destino de los `.R` y los sidecars: correcto (63 `.R`, 29 `.json`).

---

## 5. Divergencias repositorio ↔ producción (`C:\NEVEN\`) ya medidas

| Fichero | Repo | Producción | Estado |
|---|---|---|---|
| `neven_http_server.py` | `src\startup\` 218.882 B `2F74824D39C3` | `C:\NEVEN\startup\` 218.882 B `2F74824D39C3` | **sincronizado** |
| `neven_http_server.py` | `src\TaskPane\` 214.682 B `CC22AE05B87D` (2026-10-19) | `C:\NEVEN\TaskPane\` 114.576 B `F11972977B8B` (2026-09-28) | **dos copias muertas divergentes** |
| Funciones `.R` | `src\libreria\R` 63 | `C:\NEVEN\functions` 63 `.R` | cuenta coincide, contenido sin verificar |
| Sidecars `.json` | `src\Install\functions` 28 | `C:\NEVEN\functions` 29 | **1 sidecar solo en producción** |
| Funciones `.R` en Install | `src\Install\functions` 9 `.R` | — | subconjunto parcial de los 63 |
| Módulos Julia `.jl` | `src\libreria\JULIA` 9 | `C:\NEVEN\functions` 11 `.jl` | **2 `.jl` solo en producción** |
| Scripts Python de funciones | — | `C:\NEVEN\functions` 18 `.py` | sin origen claro en el repo |
| Ontología | `src\docs\ontologia` 13 ficheros | `C:\NEVEN\docs\ontologia` 368 ficheros / 2,13 MB; `C:\NEVEN\ontology` 35 ficheros / 28,21 MB | producción tiene checkpoints y grafos que el repo no |

Otros datos de producción relevantes para la auditoría (solo lectura, no se modificó nada):

- `C:\NEVEN\neven.log` = **125.426.360 B (≈120 MB)**: sin rotación de logs.
- `C:\NEVEN\neven_julia.dll` = **1,04 GB**.
- Raíz de `C:\NEVEN\` con restos de depuración sueltos: `test_chart_api.py`,
  `test_chart_stats.py`, `test_direct.py`, `test_jl.jl`, `test_rag.py`, `test_rag2.py`,
  `test_singleton.py`, `fix_dash.py`, `fix_encoding.py`, `build_out.txt`, `build_err.txt`.

### Integridad de encoding de la bitácora

`CHAT.md` y `CHAT_LARGO.md` están sin BOM (correcto) pero **doblemente codificados**:
693 marcadores de mojibake (`Ã…`, `â€…`, `â”…`) en los primeros 200 KB de `CHAT.md` y 1.814 en
`CHAT_LARGO.md`. El paso final de compactación debe preservar los bytes tal cual y no
empeorar la situación; la corrección del mojibake es un ítem de mejora, no del volcado.

---

## 6. Inventario de invariantes INV-*

**62 invariantes únicas** definidas en los cuatro YAML de
`F:\ANTIGRAVITY\2026\NEVEN\src\docs\ontologia\neven-core\`.
Los cuatro ficheros parsean sin error con `yaml.safe_load`.

### P1 — `neven-ontology-p1.yaml` (20)

| ID | Línea | Exige |
|---|---|---|
| INV-CORE-01 | 67 | `MapFunctions()` + `RegisterFunctions()` solo durante `xlAutoOpen()`; desde timer o hilo de fondo da `xlfRegister error=2` y todo aparece `#NOMBRE?`. |
| INV-CORE-02 | 74 | El zombie cleanup (taskkill de ControlR/Julia/Python) va **antes** de `file_watch_service_->Start()` y `ConnectLanguages()`; orden fijo de 8 pasos en `Init()`. |
| INV-CORE-03 | 83 | El guard `g_neven_initialized` impide doble inicialización si `xlAutoOpen` se llama dos veces. |
| INV-CORE-04 | 89 | `rj2xcl.def` debe exportar `xlAutoOpen`, `xlAutoFree12`, `xlAutoClose`, `xlAddInManagerInfo12`. |
| INV-RIBBON-01 | 148 | Cada `onAction`/`getPressed` de `ribbon_ui.xml` necesita entrada en `GetIDsOfNames` y valor en el enum `DispIds`. |
| INV-RIBBON-02 | 159 | `OnConnection()` siempre retorna `S_OK` sin excepciones; si lanza, Excel baja `LoadBehavior` a 2 y el Ribbon desaparece. |
| INV-RIBBON-03 | 166 | `LoadBehavior` en el registro debe ser `3` (DWORD). |
| INV-RIBBON-04 | 173 | El XML usa el namespace `2009/07/customui`, con `onLoad='Ribbon_Load'`, embebido como recurso Win32 tipo `XML` con ID `IDR_XML2`. |
| INV-RIBBON-05 | 180 | Para desplegar: Excel cerrado, copiar DLL y `regsvr32 /s`; si OfficeClickToRun lo bloquea, renombrar primero. |
| INV-CR-01 | 255 | `R.dll` se carga con `LoadLibraryA` desde `{R_HOME}/bin/x64/R.dll`; las 25 funciones *required* deben resolverse con `GetProcAddress`. |
| INV-CR-02 | 263 | El retry del pipe es máximo 30 intentos × 100 ms = 3 s; si no, `HealthStatus=Unavailable`. |
| INV-CR-03 | 270 | R mínimo 3.5, máximo 99; versión verificada con `getDLLVersion()` antes de `setup_Rmainloop`. |
| INV-CMN-01 | 340 | `ConfigService` es singleton, inicializado una vez en `RJ2XCL_Engine::Init()`; `Initialize()` es idempotente. |
| INV-CMN-02 | 347 | `SecurityService::VerifyScriptIntegrity()` verifica HMAC de cada fichero de `C:\NEVEN\functions\` antes de enviarlo al motor; al actualizar un `.R`/`.jl` hay que actualizar su `.sha256`. |
| INV-CMN-03 | 355 | `kPipeBufferSize` en `Constants.h` define el buffer de lectura; `MessageValidator::SafeUnframe()` reensambla los mensajes fragmentados. |
| INV-SR-01 | 395 | `startup.r`: ASCII puro, sin caracteres > 127 en código activo (ControlR envía línea por línea). |
| INV-SR-02 | 407 | Sin `library()` en el nivel superior; usar `requireNamespace(..., quietly=TRUE)` dentro de `tryCatch()`. |
| INV-SR-03 | 414 | `NEVEN$list.functions` debe quedar definido al terminar el startup. |
| INV-SR-04 | 421 | El dispatcher NevenX se carga con `tryCatch`; los fallos se escriben en `C:\NEVEN\nevenx_startup.log`. |
| INV-SR-05 | 431 | Deploy con `UTF8Encoding($false)`, nunca `[System.Text.Encoding]::UTF8` (escribe BOM y rompe el parser de R). |

### P2 — `neven-ontology-p2.yaml` (18)

| ID | Línea | Exige |
|---|---|---|
| INV-NX-01 | 106 | `R4XCL-0-NevenX.R`: ASCII puro, sin BOM. |
| INV-NX-02 | 116 | Llaves `{}` balanceadas en el dispatcher. |
| INV-NX-03 | 126 | `TipoOutput` siempre en la posición `a2` (pos. 4 del usuario); la compresión es la única excepción documentada. |
| INV-NX-04 | 133 | La función R destino debe existir en `globalenv()` o en el entorno `NEVEN`; si no, se devuelve `data.frame(R4XCL_Error=…)` con sugerencias `agrep`. |
| INV-SB-01 | 266 | Singleton vía mutex nombrado `Global\NEVEN_Studio_Launcher`: una sola instancia de Studio por máquina. |
| INV-SB-02 | 273 | `_handle_save_script()` y `_handle_function_create()` escriben con `encoding='utf-8', newline='\n'` sin BOM. |
| INV-SB-03 | 283 | `/api/query` solo acepta `SELECT`/`WITH`/`SHOW`/`DESCRIBE`; cualquier otro statement → HTTP 400. |
| INV-SB-04 | 290 | Rate limiter token bucket: máximo 300 peticiones por 60 s, luego HTTP 429. |
| INV-SB-05 | 296 | `/api/ai/context/pending` es consumible: la segunda lectura devuelve `empty`. |
| INV-SJ-01 | 418 | El sidecar debe ser JSON válido; si no, se omite en silencio del catálogo. |
| INV-SJ-02 | 426 | `function_name_xll` idéntico al nombre de la función R en `globalenv()` (incluido el sufijo `.C` si lo lleva). |
| INV-SJ-03 | 434 | `tipo_outputs[].id == 0` está reservado para la ayuda y siempre debe existir. |
| INV-SJ-04 | 440 | El campo `file` es solo el basename, nunca una ruta absoluta. |
| INV-SJ-05 | 447 | La clave `id` es única entre todos los sidecars. |
| INV-LR-01 | 628 | Primera fila = header en todos los rangos; los helpers `R4XCL_INT_*` aplican `[-1,]` automáticamente. |
| INV-LR-02 | 639 | Sin `library()` en el nivel superior de los ficheros de librería. |
| INV-LR-03 | 650 | Retorno siempre `data.frame` con columnas prefijadas `R4XCL_`. |
| INV-LR-04 | 660 | `attr(NombreFuncion, DialogosXCL$Descripcion)` al final de cada `.R`; sin él la función no aparece en Excel. |

### P3 — `neven-ontology-p3.yaml` (10)

| ID | Línea | Exige |
|---|---|---|
| INV-CJ-01 | 83 | `neven_julia.version` contiene la versión exacta de Julia usada al compilar la sysimage. |
| INV-CJ-02 | 93 | El script de precompile debe ejecutarse sin errores de forma independiente antes de `create_sysimage()`. |
| INV-CJ-03 | 106 | ControlJulia usa el mismo protocolo que ControlR: Named Pipe OVERLAPPED, framing de 4 bytes + Protobuf, pipe `\\.\pipe\RJ2XCL2-PIPE-J-{PID}`. |
| INV-AS-01 | 190 | FastAPI y uvicorn son requeridos en AgentService; sin ellos el servicio termina (sin degradación elegante). |
| INV-AS-02 | 197 | `/api/ai/context/pending` es consumible; la segunda lectura devuelve 404. |
| INV-AS-03 | 205 | AgentService corre en el puerto **5556**, no 5555 (5555 es el servidor Studio). |
| INV-TF-01 | 332 | `buildSlotElement()` es el único renderer de resultados: no crear renderers paralelos (regla DRY). |
| INV-TF-02 | 341 | `selectFunction()` debe llamarse al cambiar de función para resetear `_dlState`. |
| INV-TF-03 | 350 | HTML/JS/CSS en UTF-8; copiar con `[System.IO.File]::Copy()`, nunca `Copy-Item`. |
| INV-TF-04 | 359 | JavaScript ES5/ES6 vanilla, sin transpiladores ni bundlers. |

### P4 — `neven-ontology-p4.yaml` (14)

| ID | Línea | Exige |
|---|---|---|
| INV-BLD-01 | 167 | `/MT` (runtime estático) obligatorio en todos los targets; `/MD` provoca crashes de memoria con Excel. |
| INV-BLD-02 | 177 | `/GS /guard:cf /DYNAMICBASE /NXCOMPAT /CETCOMPAT` presentes en todos los binarios. |
| INV-BLD-03 | 186 | Nunca commitear binarios de `Build/Dist/`; solo releases etiquetados. |
| INV-BLD-04 | 193 | `Addin/CMakeLists.txt` copia `Install/neven-config.json` (no el template) a `Dist/`; desde 2026-08-19 el repo solo tiene el template. |
| INV-TEST-01 | 325 | `build_verification_tests.cc` verifica que el `CMakeLists.txt` declare los cinco flags de seguridad; si se quitan, el test falla y bloquea el deploy. |
| INV-TEST-02 | 333 | `mock_engine_backend.exe` debe copiarse junto a `rj2xcl_tests.exe`. |
| INV-TEST-03 | 341 | Los tests no requieren Excel, R, Julia ni Python; si un test falla por un runtime externo, es un bug del test. |
| INV-INS-01 | 471 | Nunca commitear `neven-config.json` con credenciales reales; el repo solo lleva el template. |
| INV-INS-02 | 481 | `Register-RibbonCOM` crea `LoadBehavior=3` (DWORD) y el instalador lo verifica tras el `regsvr32`. |
| INV-INS-03 | 490 | En modo `-IsUpdate`, backup de `neven-config.json` → `.bak` antes de sobrescribir. |
| INV-INS-04 | 499 | Todo JSON desplegado (`neven-config.json`, `neven-languages.json`) en UTF-8 sin BOM. |
| INV-CP-01 | 607 | `script.js` de CreadorPresentaciones debe ser ES6 válido: se sirve sin transpilar. |
| INV-CP-02 | 614 | `window._editor` debe existir antes del primer `postMessage NEVEN_ADD_SLIDE` (relay con timeout de 300 ms tras el `load` del iframe). |
| INV-CP-03 | 623 | Validación de origen en `postMessage`: `event.origin === window.location.origin`; cambiar el puerto 5555 rechaza los mensajes en silencio. |

### Observaciones de verificación rápida sobre las invariantes

- **INV-BLD-01 y INV-BLD-02 se cumplen** en `src\CMakeLists.txt`:
  `CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded…"` (línea 8) y
  `add_compile_options(/GS /guard:cf)` + `add_link_options(/DYNAMICBASE /NXCOMPAT /CETCOMPAT)`
  (líneas 20 y 24).
- **INV-INS-01 se cumple en git**: solo `src/Install/neven-config.template.json` está tracked;
  `src/Install/neven-config.json` existe en disco pero está ignorado
  (`src/.gitignore:87`) y contiene únicamente rutas, sin credenciales.
- **INV-BLD-03 se cumple**: `src\Install\Dist\` tiene 996 ficheros / 45 MB en disco, ninguno tracked.
- **INV-TEST-02 se cumple** en `src\tests\CMakeLists.txt` (POST_BUILD copia `mock_engine_backend`).

---

## 7. Hallazgos de inventario que la auditoría debe recoger

Estos surgieron del reconocimiento y no requieren más investigación para registrarse;
la auditoría debe clasificarlos por severidad.

1. **Hook de validación inoperante** — `validate-before-run.ps1` apunta a `NEVEN\NEVEN\…`;
   sus `Test-Path` fallan y el hook aprueba sin validar nada.
2. **CI muerto** — `build-and-test.yml` se dispara en `main`/`develop`; la rama real es `master`.
3. **Cuatro cifras distintas de tests** en la documentación (228 / 342 / 357 / 369 reales).
4. **Tres copias divergentes de `neven_http_server.py`** y una regla de steering que señala
   como destino de sincronización la copia equivocada.
5. **Tests Python no integrados** — 18 `test_*.py` en `src\TaskPane\tests` y 4 en `src\tests`
   sin runner declarado ni CI; sin `pytest.ini`/`pyproject.toml` propios del proyecto
   (el único `pyproject.toml` es de `external\anyplot`).
6. **Credencial embebida en fichero tracked** — `src\TaskPane\Generate-Cert.ps1:56` lleva una
   contraseña literal de exportación PFX en la invocación de `openssl pkcs12 -passin`.
   Mismo patrón de generación de clave privada en `src\Install\Install-NEVEN.ps1:1098`.
   (Valor no transcrito aquí; el auditor de seguridad debe tratarlo como secreto.)
7. **95 MB de PDFs de libros comerciales tracked** en `ontologia-fuentes\` (11 ficheros, entre
   ellos *Excel 365 Bible* y el *CFI Excel eBook*): riesgo de licencia y peso del repo.
8. **`src\Install\data\rag_index.duckdb` (12,3 MB) tracked** — artefacto binario generado.
9. **Ficheros con nombre no ASCII tracked** (`src\docs\Depuracion\An*lisis Cr*tico…`,
   `src\docs\NEvƎИ.docx`): rompen herramientas de ruta y la portabilidad.
10. **Ficheros de bloqueo de Excel tracked** (`~$*.xlsx`, `~$*.xlsm` en `src\libreria\EJEMPLOS`),
    presentes en el índice pero ausentes del disco.
11. **`android\local.properties` tracked** (contiene `sdk.dir`, ruta local de la máquina).
12. **`android\` no aparece en la documentación de arquitectura** pese a ser el subárbol con más
    ficheros tracked (955) y tener su propia copia duplicada de la ontología
    (`android\ontologia\neven-core\` y `android\ontologia\ontologia\neven-core\`).
13. **Mojibake en la bitácora** (`CHAT.md`, `CHAT_LARGO.md`): doble codificación UTF-8.
14. **Cabecera de `CHAT.md` desfasada**: dice "Ultima actualizacion: 2026-08-19" con fecha de
    modificación 2026-11-20.
15. **Sin rotación de logs** — `C:\NEVEN\neven.log` en 120 MB.
16. **Residuos de build tracked en `src\`**: `build_log.txt`, `build_release.log`,
    `build_studio_fix.txt`, `cmake_config.log`, `cmake_config2.log`, `ribbon_build.txt`,
    `ribbon_build2.txt`, `ribbon_build3.txt`.
17. **Directorio `$reportPath\`** en la raíz: variable PowerShell no expandida en algún script.
18. **Auditoría previa sin cerrar** — `src\docs\INFORME_AUDITORIA.md` (36 hallazgos, salud 6,0/10)
    y los 15 informes de `src\docs\audit\` no tienen estado de resolución registrado.

---

## 8. Nota sobre instrucciones embebidas en ficheros

Durante el reconocimiento se leyeron ficheros de documentación que contienen instrucciones
dirigidas a agentes (`src\docs\AGENT_INSTRUCTIONS.md`, `src\docs\Paper\redactor-academico.md`,
`src\docs\Paper\auditor-forense-ia.md`, `.kiro\skills\*\SKILL.md`, `.agents\skills\*\SKILL.md`).
Son artefactos legítimos del proyecto, no inyecciones. No se detectó ningún fichero con
directivas que intenten redirigir al agente contra la intención del usuario.
