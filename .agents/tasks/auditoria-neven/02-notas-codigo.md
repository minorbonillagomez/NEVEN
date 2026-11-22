# 02 — Eje 2: Calidad del código

**Fecha:** 2026-11-20
**Raíz:** `F:\ANTIGRAVITY\2026\NEVEN` · **Rama:** `master` · **HEAD:** `9eba8b1` (2026-11-08)
**Alcance:** C++17/CMake/GTest, R, Julia, Python, JavaScript del TaskPane y la documentación LaTeX del paper.
**Modo:** solo lectura. No se modificó ningún fichero de NEVEN ni de `C:\NEVEN\`.

**Prerrequisitos leídos:** `00-layout-real.md` (layout real, prefijo `src\`, inventario de las 62 invariantes
`INV-*`) y `plan-auditoria.md` §2 (reparto de este eje).

**Skills cargados y aplicados:**

| Skill | Dónde se aplicó |
|---|---|
| `statistical-analysis` | §5 — corrección estadística de `src\libreria\R\R4XCL-RG-*` |
| `metaheuristic-optimization` | §6 — `src\libreria\JULIA\J4XCL-OP-Optimizacion.jl`. **Conclusión: no aplica**, el fichero no implementa metaheurísticas (ver COD-34) |
| `bibtex-hygiene` | §9 — `bib_lint.py` sobre `references.bib` |
| `citation-verification` | §9 — `verify_citations.py` contra Crossref/OpenAlex/arXiv |
| `unslop-academic-writing` | §9 — `slop_check.py` sobre las 9 secciones `.tex` |
| `scientific-writing` | §9 — criterio de consistencia numérica entre afirmaciones del paper y el código |

---

## 0. Resumen ejecutivo

**56 hallazgos:** 0 críticos, **9 altos**, **26 medios**, **15 bajos**, **6 informativos** (desglose en §14).

**56 candidatos para el plan de trabajo:** 24 PENDIENTES, 20 POR MEJORAR, 12 NUEVAS IDEAS (§13).

Los cuatro más graves:

1. **COD-01** — `xlAutoOpen` ejecuta todo el arranque (`Init()`) sin ninguna guarda de excepciones en la frontera C del XLL (`src\Core\src\rj2xcl.cc:619-651`). Una excepción al leer la configuración mata Excel sin diagnóstico.
2. **COD-19 + COD-22 + COD-23** — nada protege el código automáticamente: el CI no se dispara en `master`, 410 funciones de test Python no tienen runner declarado ni entran en CMake/CI, y diez subsistemas C++ (incluidos `ViewerManager`, `RibbonService`, `CrashHandler` y las 1 522 líneas de `ribbon_connect.h`) no tienen un solo test.
3. **COD-36 + COD-37** — cuatro copias divergentes de `neven_http_server.py` en el repositorio con cuatro hashes distintos, y la copia canónica es un monolito de 4 901 líneas con un `do_GET` de 400 líneas y 65 endpoints despachados por cadena de `if/elif`.
4. **COD-40** — `taskpane.html` tiene 6 053 líneas de JavaScript inline (73 % del fichero) con 114 asignaciones a `.innerHTML` y 56 `fetch(`.

**Lo que está bien y conviene no romper:** cero funciones inseguras de la CRT (`strcpy`, `strcat`, `sprintf`,
`strncpy`, `alloca`: 0 usos en todo el árbol); RAII real en el motor (`std::unique_ptr` para los cuatro
servicios, `RaiiXlOper`, `UniqueHandle`, `SafePipeHandle`); IPC centralizado en `Common\IPC` y usado por los
tres `Control*`; `std::lock_guard` en 95 puntos; cero `eval`/`exec`/`shell=True`/`os.system` en el servidor
Python; deuda declarada mínima (28 marcadores en todo `src`); y el paper cumple **todos** los controles
anti-artefacto-IA que exige la regla del proyecto (COD-51).

### Verificación de build y tests: NO REALIZADA (con justificación)

Se **enumeraron** los tests sin recompilar (`--gtest_list_tests`) pero **no se comprobó que pasen**. Razones:

1. El binario `src\Build\tests\Release\rj2xcl_tests.exe` es del **2026-10-20 13:32** y hay **5 fuentes
   modificadas después**: `src\Ribbon\ribbon_connect.cc` (2026-10-22), `src\Core\src\basic_functions.cc`
   (2026-10-21), `src\Ribbon\ribbon_connect.h` (2026-10-21), `src\Core\include\basic_functions.h`
   (2026-10-21), `src\ControlJulia\src\julia_interface.cc` (2026-10-21). Un resultado verde de ese binario
   no probaría que el código actual pasa.
2. Reconfigurar o recompilar escribe en `src\Build\`, que está **dentro del árbol de fuentes**; esta
   ejecución lo prohíbe.
3. Varias suites escriben o leen ficheros del árbol (`ViewerProfessional_*`, `RepoHygieneTests`), de modo que
   ejecutarlas no es una operación de solo lectura.

**Recuento real de tests: 369 en 47 suites** (`src\Build\tests\Release\rj2xcl_tests.exe --gtest_list_tests`),
frente a los **342** que documenta el steering, 228 de `src\README.md:150,176` y 357 de
`src\docs\Mantenimiento\Aseguramiento_de_calidad.md:7`. De los 369, **133 (36 %) están en
`sandbox_tests.cc`** — coincide exactamente con los "133 de sandbox" documentados.

### Volumen del código medido

| Lenguaje | Ficheros | Líneas | KB |
|---|---:|---:|---:|
| `.html` | 323 | 71 184 | 5 017 |
| `.py` | 115 | 58 306 | 2 335 |
| `.cc` | 127 | 43 320 | 1 529 |
| `.h` | 140 | 24 014 | 812 |
| `.js` | 288 | 21 871 | 1 219 |
| `.R` | 98 | 17 751 | 702 |
| `.jl` | 37 | 5 662 | 222 |
| `.ps1` | 19 | 4 400 | 175 |
| `.css` | 6 | 4 085 | 97 |
| `.proto` | 1 | 404 | 10 |

(Excluye `Build\`, `Dist\`, `_deps\`, `Releases\`, `__pycache__\`. Incluye código generado: `variable.pb.h`
10 240 líneas y `variable.pb.cc` 8 794 líneas son de Protobuf.)

---

## 1. C++ — Core, Common, PB, Ribbon, los tres `Control*` y NEVEN-SIM

### COD-01 · El arranque del XLL no tiene guarda de excepciones · **ALTA** · VERIFICADO

**Evidencia:** `src\Core\src\rj2xcl.cc:619-651` (`xlAutoOpen`) y `:653-668` (`xlAutoClose`).

```
L619  __declspec(dllexport) int __stdcall xlAutoOpen(void) {
L641      RJ2XCL_Engine::Instance()->Init();
L642      NevenX_InitGlobals();
```

`Init()` (`:350-536`) llama a `ConfigService::Initialize()`, `config_service.ReadJsonFile(...)` (json11
lanza en JSON malformado), `language_manager.ConnectLanguages()`, `MapFunctions()` y `RegisterFunctions()`.
Ninguna de esas llamadas está envuelta en `try`/`catch`. Lo mismo en `xlAutoClose` → `Close()` (`:597-614`),
que a su vez llama `PlutoManager::Shutdown()`, `ViewerManager::Shutdown()` y
`file_watch_service_->Stop()` sin protección.

El patrón sí existe en el resto del fichero: hay un `catch (...)` en `HandleCallback` (`:159`) alrededor de
`application->Run()`. En todo `src` hay 15 bloques `try {` y 10 `catch (...)`, pero ninguno en los cuatro
exports del XLL.

**Impacto:** `xlAutoOpen` es un `extern "C" __stdcall` invocado por Excel. Una excepción C++ que cruce ese
límite es comportamiento indefinido: en la práctica Excel termina sin mensaje y sin entrada en `neven.log`,
y el usuario no distingue "NEVEN falló" de "Excel se cerró".

**Invariantes:** ninguna se viola al añadir el `try`/`catch`. `INV-CORE-01` (registro solo en `xlAutoOpen`),
`INV-CORE-02` (orden de los 8 pasos) e `INV-CORE-03` (guard `g_neven_initialized`) se preservan: la
envoltura no cambia el orden ni el contexto.

**Recomendación:** envolver el cuerpo de los cuatro exports en `try { ... } catch (const std::exception& e)
{ log; MessageBox } catch (...) { log }` y devolver `1` siempre, como ya hace `OnConnection` del Ribbon por
exigencia de `INV-RIBBON-02`.

---

### COD-02 · El zombie cleanup mata procesos de otras instancias de Excel · **MEDIA** · VERIFICADO (el código) / HIPÓTESIS (el efecto)

**Evidencia:** `src\Core\src\rj2xcl.cc:457-476`.

```
const char* kill_cmds[] = {
  "taskkill /F /IM ControlR.exe /T",
  "taskkill /F /IM ControlJulia.exe /T",
  "taskkill /F /IM ControlPython.exe /T", nullptr };
```

`taskkill /IM` mata **todos** los procesos con ese nombre de imagen en la sesión, no solo los huérfanos.

**Impacto (HIPÓTESIS razonada, no probada con dos instancias):** si el usuario abre un segundo Excel con
NEVEN cargado, el `xlAutoOpen` del segundo ejecuta este bloque antes de `ConnectLanguages()` y deja sin
motores al primero. El primero seguiría mostrando funciones registradas que devuelven error de pipe.

**Invariantes:** `INV-CORE-02` exige que la limpieza vaya **antes** de `file_watch_service_->Start()` y
`ConnectLanguages()` — y así está (`:480` y `:487`). La invariante fija el **orden**, no el **mecanismo**:
acotar la limpieza a PIDs huérfanos (registro de PIDs en `%LOCALAPPDATA%` o enumeración por proceso padre)
mantiene el orden y **no viola `INV-CORE-02`**.

---

### COD-03 · `xlAutoFree12` desreferencia su argumento sin comprobar nulo · **BAJA** · VERIFICADO

**Evidencia:** `src\Core\src\rj2xcl.cc:670-671` — `if (px->xltype & xlbitDLLFree)` sin `if (!px) return;`.
`INV-CORE-04` exige que el export exista, no que confíe en el puntero.

---

### COD-04 · `xlAddInManagerInfo12` usa estáticos mutables compartidos · **BAJA** · VERIFICADO

**Evidencia:** `src\Core\src\rj2xcl.cc:691` — `static XLOPER12 xInfo, xIntAction;` mutados en cada llamada
sin sincronización. Excel lo invoca desde el hilo de UI, por lo que hoy no hay carrera, pero es estado
global mutable en un export público.

---

### COD-05 · Código muerto en el motor: `ScheduleDelayedUpdate()` y el miembro `instance_` · **MEDIA** · VERIFICADO

**Evidencia:**

- `src\Core\src\rj2xcl.cc:538-558` define `RJ2XCL_Engine::ScheduleDelayedUpdate()`. `git grep
  ScheduleDelayedUpdate -- src` devuelve **solo** la declaración (`src\Core\include\rj2xcl.h:193`) y la
  definición. **Nunca se invoca.** Su cuerpo instala un `SetTimer(NULL, 0, 300000, ...)` (`:554`) idéntico
  al que ya instala `Init()` (`:531`): si alguna vez se llamara habría dos timers de telemetría de salud.
- `src\Core\include\rj2xcl.h:60` declara `static RJ2XCL_Engine *instance_;` y `rj2xcl.cc:60` lo define a `0`,
  pero `Instance()` (`:62-66`) devuelve la dirección de un `static RJ2XCL_Engine instance;` local. El
  miembro estático **nunca se lee ni se escribe**.

**Nota positiva:** el `static` local hace `Instance()` seguro frente a carreras (magic statics de C++11) y
el ciclo de vida del singleton queda atado al descarga de la DLL, que es lo correcto para un XLL.

---

### COD-06 · Carrera de datos en `ViewerManager`: `available_` cruza hilos sin protección · **MEDIA** · VERIFICADO

**Evidencia:** `src\Common\ViewerManager.h:188` declara `bool available_;` (no `std::atomic<bool>`).
`src\Common\ViewerManager.cc:144` documenta explícitamente el cruce de hilos:

```
L144  // The STA thread will set available_ = true when ready.
L146  available_ = true;  // Optimistic — will be set to false if environment fails
```

Escrituras desde el hilo de Excel en `:99`, `:123`, `:139`, `:146` y desde el hilo STA según el comentario.
`ViewerManager.h` incluye `<mutex>` (`:16`) y protege `viewers_` con `viewers_mutex_` (`:208-209`), pero
`available_` (`:188`), `max_viewers_` (`:211`), `max_memory_mb_` (`:212`), `sta_thread_id_` y
`sta_thread_handle_` quedan fuera.

**Impacto:** lectura de un `bool` no atómico escrito por otro hilo. En la práctica funciona en x64, pero es
una carrera formal que el compilador puede optimizar (cachear el valor en registro dentro de un bucle) y es
el tipo de defecto que no reproduce en depuración.

**Recomendación:** `std::atomic<bool> available_` y mover `max_viewers_`/`max_memory_mb_` a lectura única
antes de lanzar el hilo. No toca ninguna invariante.

---

### COD-07 · `TerminateThread` sobre el hilo STA de WebView2 en el cierre · **MEDIA** · VERIFICADO

**Evidencia:** `src\Common\ViewerManager.cc:155-166`.

```
L156  PostThreadMessage(sta_thread_id_, WM_QUIT, 0, 0);
L158  DWORD result = WaitForSingleObject(sta_thread_handle_, 5000);
L161      TerminateThread(sta_thread_handle_, 1);
```

**Impacto:** `TerminateThread` no desenrolla la pila ni libera los locks que el hilo tuviera tomados. Sobre
un hilo STA con objetos COM de WebView2 vivos puede dejar el heap o el lock del CRT del proceso **de Excel**
en estado inconsistente justo durante el cierre. Es la causa clásica de "Excel se cerró al salir".

Hay 6 usos más de `TerminateProcess` (`ContentPipeline.cc:421`, `PlutoManager.cc:77,178,207`,
`QuartoService.cc:439`, `language_service.cc:541`) que son aceptables: matan **procesos hijo**, no hilos del
proceso anfitrión.

**Recomendación:** si el STA no responde a `WM_QUIT` en 5 s, registrar el fallo y **dejar el hilo
colgado** (el proceso va a terminar de todos modos) en lugar de `TerminateThread`.

---

### COD-08 · Funciones excesivamente grandes · **MEDIA** · VERIFICADO

Medido con un contador de profundidad de llaves sobre los 127 `.cc` (excluyendo los generados de Protobuf);
umbral 120 líneas:

| Líneas | Ubicación | Función |
|---:|---|---|
| 371 | `src\Core\src\basic_functions.cc:1601` | `RJ_IA_Contexto` |
| 251 | `src\ControlR\src\convert.cc:60` (ámbito) | `VariableToSEXP` |
| 250 | `src\NEVEN-SIM\src\sim_main.cc:280` | `SIM_QuickSim` (export XLL) |
| 231 | `src\ControlJulia\src\julia_interface.cc:34` | `VariableToJlValue` |
| **187** | `src\Core\src\rj2xcl.cc:350` | **`RJ2XCL_Engine::Init`** |
| 174 | `src\ControlPython` / `ControlJulia` | `main` |
| 169 | `src\Common` (viewer) | `RJ_View` (export XLL) |
| 167 | `src\ControlR\src\r_engine_loader.cc:229` | `REngineLoader::Load` |
| 164 | `src\ControlJulia\src\julia_interface.cc:266` | `JlValueToVariable` |
| 164 | `src\ControlR\src\rinterface_common.cc:314` | `InputStreamRead` |

`Init()` mezcla seis niveles de abstracción en un cuerpo: configuración, creación del JobObject, creación
recursiva de directorios, `taskkill`, enumeración de ficheros con `FindFirstFileA`, registro de funciones,
lanzamiento de consola, WebView2, Pluto y un timer. Fichero más grande: `basic_functions.cc` con **4 583
líneas**.

**Recomendación:** extraer de `Init()` los pasos que ya están delimitados por los separadores de comentario
(`EnsureFunctionsDirectory()`, `CleanupOrphanEngines()`, `LoadUserFunctionFiles()`). La secuencia observable
no cambia, así que **`INV-CORE-02` se preserva**.

---

### COD-09 · 6 usos de `atoi()` sin validación · **BAJA** · VERIFICADO

`src\ControlR\src\controlr.cc:614`, `src\ControlR\src\r_engine_loader.cc:174` y `:186`,
`src\ControlR\src\rinterface_win.cc:134`, `src\Ribbon\ribbon_connect.h:190` y `:692`. `atoi` devuelve `0`
indistinguible de un `"0"` legítimo. En `r_engine_loader.cc` se usa para parsear la versión de R, que
`INV-CR-03` exige validar entre 3.5 y 99: un parseo fallido produce `0` y la comprobación lo rechaza, así que
el fallo es seguro, pero el diagnóstico es malo.

**Dato positivo verificado:** `strcpy`, `strcat`, `sprintf`, `vsprintf`, `gets`, `wcscpy`, `wcscat`,
`_snprintf`, `strncpy`, `alloca`, `scanf` → **0 usos** en todo `src` (excluidos los generados de Protobuf y
los mock headers de `src\Include`). El único uso de copia de cadena a buffer fijo es `strncpy_s`
(`rj2xcl.cc:469`), que es la variante segura.

---

### COD-10 · Duplicación entre `ControlJulia` y `ControlPython` · **MEDIA** · VERIFICADO

**Dato positivo primero:** el IPC **no** está duplicado. Los tres `Control*` incluyen `Common\IPC\pipe.cc`
(`git grep -l '#include.*IPC/'` → `controlr.cc`, `control_julia.cc`, `control_python.cc`) y las llamadas
directas a `CreateNamedPipe`/`ConnectNamedPipe`/`ReadFile`/`WriteFile`/`OVERLAPPED` son 0 en ControlR, 1 en
ControlJulia y 2 en ControlPython. Eso cumple el espíritu de `INV-CJ-03` (mismo protocolo).

**El problema:** comparando líneas no triviales (>40 caracteres, normalizadas),
`src\ControlJulia\src\control_julia.cc` y `src\ControlPython\src\control_python.cc` comparten **98 líneas
idénticas** de 166 y 148 respectivamente (59 % / 66 %). `src\ControlR\src\controlr.cc` comparte 66 con
ControlJulia y 58 con ControlPython de sus 224. El bucle de mensajes, el despacho de operaciones y el manejo
de apagado están triplicados.

**Recomendación:** extraer a `Common\` un `EngineHostLoop` plantilla al que cada `Control*` pase solo su
adaptador de lenguaje. No toca ninguna invariante.

---

## 2. Adherencia a `coding-standards.md`

El estándar vigente es `src\docs\sops\coding-standards.md` (1 112 B, v1.0, "Estado: Vigente"). Pide:
clases `PascalCase`, **funciones `snake_case`**, miembros `snake_case_`, constantes `SCREAMING_SNAKE_CASE`,
**`.cc`/`.h` evitando `.cpp`**, nombres de fichero en **`snake_case`** y Doxygen en los encabezados.

### COD-11 · El estándar no describe el código: 90 % de los métodos lo contradicen · **MEDIA** · VERIFICADO

Medición directa sobre los `.cc` (excluido Protobuf generado):

| Regla del estándar | Cumplimiento real |
|---|---|
| Funciones `snake_case` | **596 de 663 métodos son `PascalCase`**; solo 25 son `snake_case`; 42 otros |
| Nombres de fichero `snake_case` | **123 de 267** ficheros `.cc`/`.h` **no** lo son (46 %) |
| Evitar `.cpp` | **9 ficheros `.cpp`** en el árbol |
| Clases `PascalCase` | **180 de 191** cumplen |

Ficheros `.cpp` concretos: `src\Common\json11\json11.cpp` (tercero, legítimo),
`src\ControlJulia\legacy\Julia_Environment.cpp`, `src\ControlJulia\src\JuliaConversion.cpp`,
`src\ControlJulia\src\Julia_Environment.cpp`, `src\ControlR\legacy\R_Environment.cpp`,
`src\Core\src\dllmain.cpp`, `src\Include\XLCALL.cpp` (SDK de Excel, legítimo),
`src\Ribbon\dllmain.cpp`, `src\Ribbon\stdafx.cpp`.

Ficheros con nombre `PascalCase` (muestra): `ConfigService.cc/.h`, `Constants.h`, `ContentPipeline.cc/.h`,
`CrashHandler.cc/.h`, `DiagnosticRouter.cc/.h`, `DiscoveryService.cc/.h`, `EnvService.cc/.h`, `GCMonitor.cc`,
`InputSanitizer.cc/.h`, `LogService.cc/.h`, `MenuService.cc/.h`, `MessageValidator.cc/.h`,
`NevenBackgroundConnector.cc/.h`, `NevenInitOrchestrator.cc/.h`, `NevenProgressiveRegistrar.cc/.h`,
`REPLBridge.cc/.h`, `SafePipeHandle.cc/.h`, `SandboxVerifier.cc`, `SecurityService.cc/.h`, `ViewerManager.cc`.

Las 11 clases que no son `PascalCase` son, en su mayoría, ajenas o deliberadas: `_Internal` y
`TableStruct_variable_2eproto` (Protobuf generado), `_jl_value_t` (C API de Julia), `ATL_NO_VTABLE` y
`DECLSPEC_UUID` (macros de Win32/ATL), `dbg_stream_for_stdio`, `Impl_` (idioma pimpl),
`ViewerProfessional_TxtWrap` (fixture de test). Las reales son `R_Environment`, `Julia_Environment` y
**`RJ2XCL_Engine` — que el usuario declara deliberada por compatibilidad ABI y por tanto no es un defecto.**

**Conclusión:** el código es internamente coherente (Google C++ Style para clases y métodos: `PascalCase`
para ambos, `snake_case_` para miembros). **El documento es el que está mal, no el código.** Refactorizar
596 métodos sería un cambio masivo sin beneficio y con riesgo de ABI.

**Recomendación:** actualizar `coding-standards.md` a lo que el código hace realmente (métodos `PascalCase`,
ficheros con el nombre de la clase, `snake_case` solo para funciones libres y variables locales) y declarar
expresamente las excepciones `RJ_`/`RJ2XCL` por ABI. No toca ninguna invariante.

### COD-12 · `coding-standards.md` duplicado byte a byte · **BAJA** · VERIFICADO

`src\docs\sops\coding-standards.md` y `src\docs\Plan_trabajo\coding-standards.md`: ambos 1 112 B,
contenido idéntico (comparación de bytes). Dos fuentes de verdad para la misma norma.

### COD-13 · Cobertura Doxygen desigual en los encabezados · **BAJA** · VERIFICADO

De 133 `.h` propios (excluidos `variable.pb.h`, `XLCALL`, `stdafx`, `resource`): **103 tienen al menos una
marca Doxygen, 30 no**. De esos 30, 24 son mock headers del SDK de R (`src\Include\R_ext\*`, `Rinternals.h`,
`Rmath.h`…) y de Julia, donde no aplica. Los casos propios sin marca son
`src\ControlJulia\include\julia_compat.h`, `src\ControlR\src\r_api_shim.h`, `src\Ribbon\targetver.h`,
`src\tests\mocks\mock_language_service.h`, `src\tests\mocks\mock_type_info.h`.

Más relevante es la densidad en los headers grandes:

| Header | `@brief` | Miembros públicos aprox. |
|---|---:|---:|
| `src\Core\include\rj2xcl.h` | **1** | 28 |
| `src\ControlR\include\gdi_graphics_device.h` | **0** | 23 |
| `src\Common\RuntimeLoader.h` | **0** | 20 |
| `src\Common\GCMonitor.h` | **0** | 20 |
| `src\Ribbon\ribbon_connect.h` | **0** | 14 |
| `src\Common\AutoLoader.h` | 3 | 23 |

El header del singleton central del proyecto documenta 1 de 28 miembros.

---

## 3. Build — CMake, dependencias, reproducibilidad

### COD-14 · El build no tiene avisos activados y silencia los que vienen por defecto · **ALTA** · VERIFICADO

**Evidencia:** `git grep -n -E '/W[0-4]|/WX|/permissive|/sdl|/analyze|CMAKE_CXX_FLAGS'` sobre los **12
`CMakeLists.txt`** del árbol devuelve **cero coincidencias** de nivel de aviso. Lo único que aparece es
`midl /W1` en `src\Ribbon\CMakeLists.txt:13`, que es el compilador de IDL, no el de C++.

Y además `src\CMakeLists.txt:12` silencia explícitamente cuatro familias de avisos:

```
add_compile_definitions(_SILENCE_CXX17_OLD_ALLOCATOR_MEMBERS_DEPRECATION_WARNING
  _SILENCE_CXX17_HASH_IMPLEMENTATION_DEPRECATION_WARNING
  _SILENCE_STDEXT_HASH_DEPRECATION_WARNING
  _SILENCE_CXX17_CODECVT_HEADER_DEPRECATION_WARNING)
```

**Impacto:** el proyecto compila con el `/W1` por defecto de MSVC. No se ven conversiones con pérdida de
precisión, variables sin usar, rutas sin `return`, comparaciones signed/unsigned ni inicializaciones
faltantes — la clase de defecto que más cuesta encontrar en depuración y que un compilador detecta gratis.
En un proyecto de 43 320 líneas de `.cc` y 24 014 de `.h` esto es el hueco de calidad más barato de cerrar.

**Invariantes:** `INV-BLD-02` exige `/GS /guard:cf /DYNAMICBASE /NXCOMPAT /CETCOMPAT`, y **se cumplen**
(`src\CMakeLists.txt:20` y `:24`). Añadir `/W3` o `/W4` no los toca. `INV-TEST-01`
(`build_verification_tests.cc` comprueba que los cinco flags estén declarados) seguiría pasando: solo
hay que evitar **quitar** flags, no añadirlos.

**Recomendación:** subir a `/W3` con `/permissive-` y `/sdl` (que complementa `/GS`), arreglar la cola de
avisos y solo entonces evaluar `/W4 /WX` por target. Introducirlo con `/WX` de golpe bloquearía el build.

### COD-15 · `rapidcheck` sin anclar: build no reproducible · **MEDIA** · VERIFICADO

**Evidencia:** `src\CMakeLists.txt:52-57`.

```
FetchContent_Declare(rapidcheck
  GIT_REPOSITORY https://github.com/emil-e/rapidcheck.git
  GIT_TAG        master)
```

Las otras tres sí están ancladas: Protobuf por URL de release (`:34`, v21.12), GoogleTest por tag (`:47`,
`v1.14.0`), WebView2 por versión de paquete NuGet (`:76`, `1.0.2903.40`). **Pero ninguna de las dos descargas
por URL lleva `URL_HASH`**, así que un artefacto cambiado en origen no se detecta.

`rapidcheck` no es decorativo: sostiene 9 suites de property-based testing
(`PythonSandboxPBT`, `InputSanitizerPBT`, `SandboxPathPBT`, `SandboxBlocklistPBT`, `ProtobufIpcPBT`,
`ReliabilityPBT`, `WebView2PBT`, `EnvLookupPBT`, `PythonReactivation*PBT`). Un cambio incompatible en `master`
rompe el build de los tests sin que nada cambie en el repositorio.

**Recomendación:** fijar `GIT_TAG` a un commit SHA concreto y añadir `URL_HASH SHA256=...` a Protobuf y
WebView2. No toca ninguna invariante (`INV-BLD-01/02/03` son sobre flags y binarios, no sobre pinning).

### COD-16 · `file(GLOB)` sin `CONFIGURE_DEPENDS` en el target más grande · **MEDIA** · VERIFICADO

**Evidencia:**

- `src\Core\CMakeLists.txt:2` → `file(GLOB RJ2XCL_SOURCES src/*.cc src/*.cpp)`
- `src\NEVEN-SIM\CMakeLists.txt:10` → `file(GLOB SIM_SOURCES src/*.cc)`
- `src\NEVEN-SIM\tests\CMakeLists.txt:7` → `file(GLOB SIM_TEST_SOURCES *.cc)`

Sin `CONFIGURE_DEPENDS`, CMake **no** reevalúa el glob al construir: añadir o borrar un `.cc` en
`src\Core\src\` no entra en el build hasta que alguien reconfigura a mano. Core tiene 47 ficheros de código.

Caso distinto (y confuso, pero no roto): `src\ControlR\CMakeLists.txt:53` y
`src\ControlJulia\CMakeLists.txt:37` usan `file(GLOB SRC_FILES ...)` con una lista de **nombres exactos**.
Funciona, pero `file(GLOB)` con rutas literales no es un glob: debería ser `set(SRC_FILES ...)`. El comentario
de `ControlR\CMakeLists.txt:50` explica que es para **excluir** `R_Environment.cpp` — ese propósito se cumple
mejor con una lista explícita.

### COD-17 · `include_directories()` global en lugar de por target · **BAJA** · VERIFICADO

`src\CMakeLists.txt:27-29` (`include`, `Common`, `OfficeTypes`) y `:84` (`${protobuf_SOURCE_DIR}/src`)
inyectan rutas en **todos** los targets del árbol, incluidos los que no las necesitan. `src\Core` sí usa el
estilo moderno (`target_include_directories(NEVEN_Core_Objects PUBLIC ...)`, `CMakeLists.txt:5`). Estilo
mixto en el mismo build.

### COD-18 · `build.ps1` pasa `CMAKE_BUILD_TYPE` a un generador multiconfiguración · **BAJA** · VERIFICADO

`src\build.ps1:72` → `cmake -S . -B $BuildDir -A x64 "-DCMAKE_BUILD_TYPE=$Config"`. Con el generador de
Visual Studio 2022, `CMAKE_BUILD_TYPE` se ignora; la configuración real la fija `--build --config $Config`
(`:77`). Es inocuo, pero hace pensar que `-Config Debug` ya está aplicado en el paso de configuración.

### COD-19 · El CI nunca se dispara en la rama real · **ALTA** · VERIFICADO · (estado: ABIERTO, ya detectado en `00-layout-real.md` §7.2)

**Evidencia:** `src\.github\workflows\build-and-test.yml:5` → `branches: [ main, develop ]`, `:7` →
`branches: [ main ]`, `:54` → `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`.
`git rev-parse --abbrev-ref HEAD` → **`master`**.

**Impacto para este eje:** los 369 tests solo se ejecutan si alguien los lanza a mano. No hay ninguna barrera
automática contra una regresión, y `INV-TEST-01` (el test que protege los flags de seguridad del
`CMakeLists.txt`) no se evalúa nunca en un push. Es la razón de fondo por la que COD-20 (cuatro cifras
distintas de tests en la documentación) pudo divergir sin que nadie lo notase.

**Nota:** `repo_hygiene_tests.cc` ya comprueba propiedades del propio workflow
(`CIWorkflowHasPermissionsBlock:84`, `CIWorkflowHasContentsReadPermission:94`) pero no que el trigger
apunte a una rama existente.

---

## 4. Tests — recuento, cobertura y calidad de los mocks

### COD-20 · Recuento real: 369 tests / 47 suites frente a cuatro cifras documentadas · **INFORMATIVA** · VERIFICADO

**Método:** `src\Build\tests\Release\rj2xcl_tests.exe --gtest_list_tests` (solo lectura, no recompila).

| Fuente | Cifra |
|---|---:|
| **Binario (real)** | **369 tests, 47 suites** |
| `.kiro\steering\neven-project-context.md` | 342 |
| `src\README.md:150` y `:176` + badge `:19` | 228 |
| `src\docs\Mantenimiento\Aseguramiento_de_calidad.md:7` | 357 |
| `src\docs\Paper\sections\06_conclusion.tex:11` | 342 |

Los 33 `.cc` de `src\tests` están **todos** declarados en `src\tests\CMakeLists.txt` y todos los declarados
existen en disco (comparación bidireccional: 0 diferencias). Eso sí está bien gobernado.

**La distribución es muy desigual:**

| Tests | Fichero |
|---:|---|
| **133** | `sandbox_tests.cc` (36 % del total, 789 líneas) |
| 34 | `viewer_professional_tests.cc` |
| 32 | `reliability_tests.cc` |
| 16 | `common_tests.cc`, `new_functions_tests.cc`, `input_sanitizer_tests.cc` |
| 14 | `repo_hygiene_tests.cc` |
| 11 | `config_service_tests.cc` |
| 8 | `pipe_lifecycle_tests.cc`, `python_reactivation_preservation_pbt.cc`, `e2e_tests.cc` |
| 1–6 | los 20 restantes |
| **4** | `basic_functions_tests.cc` (90 líneas) — para las **4 583 líneas** de `basic_functions.cc` |
| **1** | `r_library_tests.cc` (100 líneas) — para las **17 751 líneas** de R |

La cifra "133 de sandbox" del steering coincide exactamente con el `sandbox_tests.cc` actual.

### COD-21 · No se comprobó que los tests pasen · **INFORMATIVA** · NO VERIFICADO (motivo declarado)

Ver §0. Resumen: binario del 2026-10-20 con 5 fuentes posteriores; recompilar escribe en `src\Build\`
(dentro del árbol); varias suites escriben ficheros. **No se afirma ni se niega que pasen.**

`INV-TEST-03` (los tests no requieren Excel, R, Julia ni Python) **no queda verificada** en esta auditoría
precisamente por no haberlos ejecutado. `INV-TEST-02` (copia de `mock_engine_backend.exe` junto al binario)
**sí se cumple**: `src\tests\CMakeLists.txt` lo copia en `POST_BUILD`.

### COD-22 · 410 funciones de test Python sin runner declarado, fuera de CMake y fuera del CI · **ALTA** · VERIFICADO

**Evidencia:** 26 ficheros `test_*.py` con **410 funciones `def test_`**:

- `src\TaskPane\tests\` — 18 ficheros, 331 tests. Los mayores: `test_start_studio_4_1.py` (55),
  `test_start_studio_4_2.py` (43), `test_pipe_client_2_3.py` (34), `test_pipe_client_2_1.py` y
  `test_pipe_client_2_5.py` (25 cada uno), `test_start_studio_4_7.py` y `test_pipe_client_2_2.py` (24),
  `test_http_server_6_1.py` (17), `test_http_server_6_5.py` y `test_http_server_7_6.py` (16).
- `src\tests\` — `test_datalab_handler.py` (388 líneas), `test_skill_loader.py` (358),
  `test_package_manager_service.py` (227).
- Más 7 runners `.R` sueltos en `src\tests`: `run_studio_tests.R`, `test_ad_funciones.R`,
  `test_gr_funciones.R`, `test_rg_avanzado.R`, `test_rg_basico.R`, `test_rg_econometrico.R`,
  `test_r_object_to_slots.R`.

**Lo que falta:** `git ls-files` en todo el repositorio **no** devuelve `pytest.ini`, `pyproject.toml`,
`setup.cfg`, `tox.ini` ni `conftest.py`. Los únicos ficheros de dependencias Python son
`src\Audiobook\requirements.txt` y `src\TaskPane\requirements.txt`. (El único `pyproject.toml` del workspace
pertenece a `external\anyplot`, dependencia de terceros.)

**Impacto:** son 410 tests sobre `pipe_client`, `start_studio` y el servidor HTTP — exactamente la superficie
que COD-37 identifica como la más grande y menos estructurada del proyecto. Nadie puede ejecutarlos con un
comando reproducible, nadie sabe si pasan hoy, y no hay registro de cuándo pasaron por última vez. Es más
código de test que el que tiene CMake (369) y es invisible.

### COD-23 · Diez subsistemas C++ sin ningún test · **ALTA** · VERIFICADO

Búsqueda del nombre de clase en los 33 `.cc` de `src\tests`:

| Subsistema | Referencias en tests |
|---|---:|
| `ViewerManager` | **0** |
| `RibbonService` | **0** |
| `PlutoManager` | **0** |
| `CrashHandler` | **0** |
| `FileWatchService` | **0** |
| `MenuService` | **0** |
| `GCMonitor` | **0** |
| `DiagnosticRouter` | **0** |
| `NevenProgressiveRegistrar` | **0** |
| `NevenInitOrchestrator` | **0** |
| `ContentPipeline` | 72 (bien cubierto) |
| `AutoLoader` | 3 |
| `REPLManager`, `REPLBridge`, `NotebookExporter` | 2 cada uno |

Casos especialmente caros: `src\Ribbon\ribbon_connect.h` tiene **1 522 líneas** y ningún test, aunque
`INV-RIBBON-01` (cada `onAction` del XML necesita entrada en `GetIDsOfNames` y en el enum `DispIds`) es
exactamente el tipo de correspondencia que un test de tabla verifica en segundos. Y
`src\Core\src\basic_functions.cc` tiene 4 583 líneas (incluido `RJ_IA_Contexto` de 371) con 4 tests.

`ViewerManager` concentra además COD-06 (carrera) y COD-07 (`TerminateThread`): la parte más concurrente del
proyecto es la que no tiene red de seguridad.

### COD-24 · `MockExcelBridge` no puede simular errores ni salidas · **MEDIA** · VERIFICADO

**Evidencia:** `src\Core\include\MockExcelBridge.h` (50 líneas, leído completo).

```cpp
virtual int Excel12(int xlfn, LPXLOPER12 operRes, int count, ...) override {
  call_counts_[xlfn]++;
  return xlretSuccess;
}
```

Cuenta invocaciones y **devuelve siempre `xlretSuccess` sin escribir nada en `operRes`**. No puede producir
`xlretAbort`, `xlretUncalced`, `xlretInvXlfn` ni un `XLOPER12` de salida.

**Impacto:** ningún test que use este mock puede verificar (a) la conversión de tipos de vuelta desde Excel,
(b) las rutas de error de `Excel12`/`Excel12v`, ni (c) el comportamiento cuando Excel está ocupado o en
recálculo. Solo puede afirmar "se llamó a la función X n veces".

**Uso real:** solo 2 ficheros de test lo instancian (`src\tests\callback_behavior_tests.cc`,
`src\tests\raii_xloper_tests.cc`). El resto de las menciones de `MockExcelBridge` (16) están en
documentación.

**Dato positivo sobre los otros mocks:** los mock headers de R (`src\Include\R_ext\*`, `Rinternals.h`,
`Rmath.h`, `Rembedded.h`…, 30 headers) y de Julia (`src\Include\julia.h`) sí permiten compilar el árbol sin
los SDK instalados, que es su propósito y lo cumplen. Son el motor de `INV-TEST-03`.

**Recomendación:** dar al mock una tabla programable `{xlfn → (retorno, XLOPER de salida)}`. Es un cambio
contenido en el header y habilita tests de las rutas de error del XLL. No toca ninguna invariante.

### COD-25 · Cero tests de frontend para 30 000 líneas de JS/HTML · **MEDIA** · VERIFICADO

`src\TaskPane` tiene 21 871 líneas de `.js` repartidas en el árbol y `taskpane.html` con 8 263 líneas (de
las que 6 053 son JavaScript inline, COD-40). No existe ningún fichero de test de frontend en el repositorio:
`git ls-files` no devuelve `*.test.js`, `*.spec.js`, ni configuración de Jest/Vitest/Karma.

`INV-TF-04` prohíbe transpiladores y bundlers, pero **no** prohíbe un runner de tests: un fichero HTML con
asserts cargado en el navegador, o `node --test` sobre los `.js` extraídos, son compatibles. La invariante
no es el obstáculo.

---

## 5. R — los 63 ficheros de `src\libreria\R` y el dispatcher

**Método:** verificación byte a byte fichero a fichero (BOM, bytes >127, balance de `{}`, `library()` de
nivel superior, presencia de `DialogosXCL$Descripcion`, presencia de `tryCatch`). Los 63 ficheros se
descomponen en **37 no-Studio** (funciones expuestas al XLL) y **26 `*.Studio.R`** (scripts de DataLab).

### COD-26 · `INV-NX-01` e `INV-NX-02` se CUMPLEN en el dispatcher · **INFORMATIVA** · VERIFICADO

`src\libreria\R\R4XCL-0-NevenX.R`: 468 líneas, 17 706 B, **0 bytes >127**, **sin BOM**, **llaves
balanceadas** (apertura = cierre). Contiene 5 definiciones de función, 8 `tryCatch` y una tabla
`.neven_aliases` (`:205`) con 55 entradas. `INV-NX-03` (TipoOutput siempre en `a2`) está documentada en el
propio fichero (`:8` — "Pos 4 (a2) : TipoOutput (entero, default 1) -- SIEMPRE pos 4") y la firma lo refleja
(`:191` — `a0=NULL, a1=NULL, a2=NULL, a3=NULL, a4=NULL`). `INV-NX-04` (sugerencias con `agrep` ante función
inexistente) está presente (`:283-287`).

Nota de alcance: **54 de los 63** ficheros de la librería **sí** tienen bytes >127 (hasta 2 199 en
`GR_Scatter.Studio.R`). Eso **no** viola ninguna invariante: `INV-SR-01` (ASCII puro) aplica solo a
`startup.r`, porque ControlR lo envía línea por línea; `INV-NX-01` aplica solo al dispatcher. La librería se
carga con `source()`, que es tolerante. Lo que sí importa es `INV-SR-05`: el despliegue debe hacerse con
`UTF8Encoding($false)` y nunca con `[System.Text.Encoding]::UTF8` (que añade BOM). Ningún fichero del
repositorio tiene BOM hoy, así que el despliegue se está haciendo bien.

### COD-27 · `INV-LR-02` violada en 30 de los 63 ficheros de la librería · **MEDIA** · VERIFICADO

`INV-LR-02` (`neven-ontology-p2.yaml:639`): sin `library()` en el nivel superior de los ficheros de
librería; usar `requireNamespace(..., quietly=TRUE)` dentro de `tryCatch()`.

**30 ficheros tienen al menos un `library()` al inicio de línea en nivel superior.** Los peores:

| `library()` | Fichero |
|---:|---|
| 4 | `R4XCL-AD-TextMining.R`, `R4XCL-GR-Interactivos.R` |
| 3 | `R4XCL-AD-Dashboard.R`, `R4XCL-AD-Esquisse.R`, `R4XCL-AD-NonParRolCor.R`, `R4XCL-GR-QuickPlot.R`, `R4XCL-RG-DatosPanel.R`, `R4XCL-RG-Lineal.R`, `R4XCL-RG-SeriesTiempo.R` |
| 2 | `R4XCL-0-UT-Ayuda.R`, `R4XCL-AD-ACP.R`, `R4XCL-AD-Pivot.R`, `R4XCL-FX-Calculos.R`, `R4XCL-GR-PlotlyView.R`, `R4XCL-RG-ArbolDecision.R`, `R4XCL-RG-Poisson.R`, `R4XCL-RG-Tobit.R`, `R4XCL-UT-Pivote.R` |
| 1 | 13 ficheros más |

**Impacto:** `library()` en nivel superior falla el `source()` **completo** del fichero si el paquete no está
instalado. El usuario pierde todas las funciones del fichero, no solo la que necesitaba el paquete. Es la
causa de raíz documentada de los `#NOMBRE?` en bloque.

Hay un patrón mixto: 11 ficheros ya usan `requireNamespace` (p. ej. `R4XCL-RG-2SLS.R` con 3,
`R4XCL-RG-SeriesTiempo.R` con 3, `R4XCL-0-UT-InstalaPaqueterias.R` con 3). La migración está empezada pero no
terminada.

### COD-28 · `INV-LR-04`: 26 de los 37 no-Studio sin `DialogosXCL$Descripcion` · **MEDIA** · VERIFICADO (el conteo) / HIPÓTESIS (cuántos son violación real)

`INV-LR-04` (`neven-ontology-p2.yaml:660`): `attr(NombreFuncion, DialogosXCL$Descripcion)` al final de cada
`.R`; sin él la función no aparece en Excel.

De los 37 ficheros no-Studio, **26 no contienen la cadena `DialogosXCL$Descripcion`**. Pero no todos son
violación:

- **7 no aplican** porque son internos o el propio dispatcher: `R4XCL-0-Interno-1.R`, `-2.R`, `-3.R`,
  `R4XCL-0-NevenX.R`, `R4XCL-0-Shared-WebView.R`, `R4XCL-0-UT-Ayuda.R`,
  `R4XCL-0-UT-InstalaPaqueterias.R`.
- **5 tienen `attr(` sin la cadena** (otra forma de registro): `R4XCL-AD-D3.R` (2), `R4XCL-AD-Dashboard.R`
  (2), `R4XCL-AD-Esquisse.R` (2), `R4XCL-AD-KMediass.R` (2), `R4XCL-AD-Map.R` (2), `R4XCL-AD-Pivot.R` (2),
  `R4XCL-FX-Aleatorios.R` (4), `R4XCL-RG-SeriesTiempo.R` (3) — requieren inspección individual.
- **6 no tienen ningún `attr(`**: `R4XCL-AD-NonParRolCor.R`, `R4XCL-BD-ObtieneDatos.R`,
  `R4XCL-DS-Wooldridge.R`, `R4XCL-GR-Mapa.R`, `R4XCL-NEVEN-pluto-read.R` — **estos son los candidatos
  firmes a violación de `INV-LR-04`**.

**No se verificó en Excel** qué funciones aparecen y qué funciones no, porque requiere Excel abierto. El
delta entre los 78 procedimientos contados y lo que el usuario ve es trabajo del Eje 1.

### COD-29 · 34 de 63 ficheros `.R` sin ningún `tryCatch` · **MEDIA** · VERIFICADO

`INV-LR-03` exige retorno siempre `data.frame` con columnas prefijadas `R4XCL_`; `INV-NX-04` exige
`data.frame(R4XCL_Error=...)` cuando la función no existe. Pero **34 de 63 ficheros no tienen un solo
`tryCatch`**: un error dentro del procedimiento (matriz singular, columna ausente, NA en el `lm`) propaga la
condición de R, el dispatcher la convierte en lo que pueda y la celda recibe algo que no es el contrato
`R4XCL_`.

**Recomendación:** envolver el cuerpo analítico de cada procedimiento en `tryCatch` con un
`error = function(e) data.frame(R4XCL_Error = conditionMessage(e))`. **Refuerza** `INV-LR-03` e `INV-NX-04`
en lugar de tocarlas.

### COD-30 · Los diagnósticos estadísticos son ramas opcionales, no parte del informe · **MEDIA** · VERIFICADO · (skill `statistical-analysis`)

**Evidencia:** `src\libreria\R\R4XCL-RG-Lineal.R`, función `MR_Lineal` (`:5`). El despacho por `TipoOutput`
reparte la salida así:

| `TipoOutput` | Línea | Qué devuelve |
|---:|---:|---|
| 1 | `:69`, `:72` | `summary(Modelo)` y `stargazer(..., ci=TRUE, ci.level=0.95)` |
| 2–3 | `:77`, `:83-97` | predicción dentro y fuera de muestra |
| 4 | `:105` | efectos marginales |
| 5 | `:110` | `usdm::vif(DT[,-1])` — multicolinealidad |
| 6 | `:115` | `lmtest::bptest(Modelo)` — heterocedasticidad |
| 7 | `:124` | `sandwich::vcovHC(Modelo, type = "HC")` — errores robustos |
| 8 | `:136` | observaciones de influencia |
| 12 | `:156` | residuos |

**El problema:** quien llama `TipoOutput=1` recibe coeficientes, errores estándar y p-valores **sin ninguna
comprobación de supuestos y sin ningún aviso**. Las comprobaciones existen pero exigen que el usuario sepa
pedirlas, una por llamada.

**Lo que no existe en ninguno de los 63 ficheros** (conteo por `Select-String` sobre `*.R`):

| Comprobación | Ocurrencias |
|---|---:|
| `shapiro.test` (normalidad de residuos) | **0** |
| `qqnorm` / gráfico Q-Q | **0** |
| `dwtest` / `durbinWatson` (autocorrelación) | **0** |
| `confint` (IC de coeficientes, salvo vía `stargazer`) | **0** |
| `cooks.distance` | **0** |
| `resettest` (forma funcional) | **0** |
| `p.adjust` / `holm` / `fdr` / `bonferroni` / `TukeyHSD` / `pairwise` | **0** |
| `vif` | 11 |
| `bptest` | 2 · `bgtest` 1 · `vcovHC` 2 |
| `AIC` 11 · `BIC` 9 · `anova` 4 · `r.squared` 7 · `adj.r.squared` 2 | — |

Aclaración honesta: las 192 coincidencias de `eta` son subcadenas de palabras en español
(`etiquetas`, `Paleta`, `paletas`…), **no** eta cuadrado. No hay ningún tamaño de efecto estandarizado
(`cohen` 0, `hedges` 0, pseudo-R² 0).

**En series de tiempo** (`R4XCL-RG-SeriesTiempo.R` + `.Studio.R`): `adf.test` 2, `pp.test` 1, `acf` 22,
`pacf` 5, pero `kpss` 0, `Box.test` 0 (sin prueba de Ljung-Box sobre los residuos), `ndiffs` 0,
`auto.arima` 0, `ur.df` 0.

**Impacto:** el criterio de reporte estadístico defendible exige que el informe lleve descriptivos, el
estadístico con sus grados de libertad, el p-valor exacto, el tamaño de efecto con su IC **y las
comprobaciones de supuestos realizadas**. NEVEN entrega lo primero y lo tercero; lo segundo y lo quinto son
opcionales y lo cuarto no existe. Para el público declarado del proyecto (estudiantes de econometría, según
`06_conclusion.tex:21`) esa asimetría es el peor caso: el camino fácil es el que no comprueba nada.

**Recomendación (no viola ninguna invariante):** añadir un `TipoOutput` nuevo "informe completo" que
devuelva estimación + VIF + Breusch-Pagan + normalidad de residuos + Ljung-Box en un solo `data.frame`, y
que `TipoOutput=1` incluya una columna `R4XCL_Avisos` cuando un supuesto falle. El contrato `R4XCL_` y la
posición `a2` de `TipoOutput` se mantienen → `INV-LR-03`, `INV-NX-03` y `INV-SJ-03` intactas. Requiere
actualizar el sidecar correspondiente (`tipo_outputs[]`) según `INV-SJ-03`.

### COD-31 · `vcovHC(type = "HC")` es HC0; para muestras finitas la recomendación es HC3 · **MEDIA** · VERIFICADO · (skill `statistical-analysis`)

**Evidencia:** `src\libreria\R\R4XCL-RG-Lineal.R:124` → `cov <- sandwich::vcovHC(Modelo, type = "HC")`.
En el paquete `sandwich`, `type = "HC"` es sinónimo de **HC0**, el estimador original de White sin corrección
de grados de libertad.

**Impacto:** HC0 subestima la varianza en muestras pequeñas, lo que produce errores estándar demasiado
pequeños y p-valores anticonservadores — precisamente el régimen de una hoja de Excel con 30–200 filas, que
es el caso de uso típico de NEVEN. HC3 es la corrección recomendada para ese régimen y solo cambia una
cadena.

**Recomendación:** `type = "HC3"`, o exponer el tipo como parámetro con HC3 por defecto. Cambio de una línea.
No toca ninguna invariante.

### COD-32 · 9 de 10 `GR_*.Studio.R` de `deprecated\` son copias byte a byte de los vivos · **BAJA** · VERIFICADO

`src\TaskPane\deprecated\GR_DataLab_migrated\` (19 ficheros tracked: 9 `.R` + 10 `.json`). Comparación de
hash contra `src\libreria\R\`:

| Fichero | Estado |
|---|---|
| `GR_Barras.Studio.R`, `GR_BoxPlot.Studio.R`, `GR_Correlaciones.Studio.R`, `GR_EjemploAvanzado.Studio.R`, `GR_Histograma.Studio.R`, `GR_Lineas.Studio.R`, `GR_Mapa.Studio.R`, `GR_SeriesTiempo.Studio.R` | **IDÉNTICO** al de `src\libreria\R\` |
| `GR_EjemploBasico.Studio.R` | **solo existe en `deprecated\`** |

**Impacto:** quien busque `GR_Histograma.Studio.R` con una herramienta de ruta encuentra dos resultados y no
sabe cuál editar. Y `GR_EjemploBasico.Studio.R` solo vive en el directorio marcado como obsoleto, de modo que
el nombre "deprecated" es engañoso: contiene el único ejemplar de un fichero.

---

## 6. Julia — `functions.jl` y los módulos J4XCL

Inventario real de `src\libreria\JULIA` (9 ficheros, 5 662 líneas de `.jl` en todo el árbol):

| Fichero | `function nombre` | Una línea (`f(x) = ...`) | `export` | Líneas |
|---|---:|---:|---:|---:|
| `functions.jl` | 14 | 14 | 0 | 644 |
| `J4XCL-RG-Lineal.Studio.jl` | 6 | 2 | 0 | 217 |
| `J4XCL-ML-Aprendizaje.jl` | 5 | 0 | 0 | 545 |
| `J4XCL-AD-Descriptiva.Studio.jl` | 4 | 1 | 0 | 161 |
| `J4XCL-CN-Conectividad.jl` | 3 | 0 | 0 | 375 |
| `J4XCL-MT-Matematicas.jl` | 3 | 3 | 0 | 506 |
| `J4XCL-UT-Paquetes.jl` | 3 | 0 | 0 | 63 |
| `J4XCL-OP-Optimizacion.jl` | **1** | 0 | 0 | **320** |
| `NEVEN-export-data.jl` | 1 | 0 | 1 | 87 |
| **Total** | **40** | **20** | **1** | **2 918** |

### COD-33 · Ningún "módulo J4XCL" es un módulo de Julia · **MEDIA** · VERIFICADO

**Evidencia:** `Select-String -Path src\libreria\JULIA\*.jl -Pattern '^\s*module\s+'` → **cero
coincidencias**. El único `export` del directorio es `export export_data` en `NEVEN-export-data.jl`.

Los nueve ficheros son scripts planos que, al cargarse, inyectan sus nombres en `Main`. Se los documenta como
"módulos J4XCL" en `.kiro\steering\neven-project-context.md` y en el paper, pero no hay frontera de
namespace.

**Impacto:** dos ficheros que definan la misma función se sobrescriben en silencio según el orden de carga, y
cualquier paquete que el usuario cargue en el mismo `Main` puede colisionar con un nombre de la librería. Con
la sysimage precompilada (`neven_julia.dll`), el orden de carga queda además fijado en tiempo de build, lo
que hace el conflicto difícil de diagnosticar.

**Invariantes:** `INV-CJ-01` (la sysimage declara su versión de Julia en `neven_julia.version`) y
`INV-CJ-02` (el script de precompile debe ejecutarse solo antes de `create_sysimage()`) **sí se verían
afectadas** por envolver los ficheros en `module`: habría que regenerar la sysimage y reejecutar el
precompile. **No se propone el cambio sin más**: se propone como ítem con su coste declarado (ver
`POR MEJORAR` → `MEJ-11`), condicionado a reconstruir la sysimage y revalidar `INV-CJ-02`.

### COD-34 · `J4XCL-OP-Optimizacion.jl`: 320 líneas, una función, un parámetro con dos significados · **MEDIA** · VERIFICADO · (skill `metaheuristic-optimization`)

**Primero, el alcance del skill.** El plan de auditoría pedía usar `metaheuristic-optimization` para
comprobar "si el algoritmo declarado es el implementado". **Resultado: el skill no aplica a este fichero.**
`J4XCL-OP-Optimizacion.jl` implementa métodos **deterministas**, no metaheurísticas: descenso de gradiente
(`:41`), gradiente con momentum (`:76`), método de Newton (`:112`), bisección (`:145-151`), simplex sobre
tableau (`:199-248`) y mínimos cuadrados no negativos por gradiente proyectado (`:251-276`). No hay
algoritmos genéticos, enfriamiento simulado, búsqueda tabú, ACO ni PSO en ningún `.jl` del proyecto. Lo digo
explícitamente en lugar de forzar el skill.

**Lo que sí evalúo con los criterios del skill que son transversales:**

- **Criterios de parada: correctos.** Todas las ramas usan `max_iter` (`:51`, `:87`, `:146`, `:202`, `:260`,
  `:293`) con tolerancia y emiten `"No convergió en $max_iter iteraciones"` (`:70`, `:107`, `:171`, `:248`)
  en lugar de devolver silenciosamente el último iterado. Eso es lo correcto y poco habitual.
- **Gestión de la aleatoriedad: no aplica** — no hay `rand()` ni semillas porque no hay estocasticidad.
  Correcto por construcción.
- **Defecto real: semántica sobrecargada del parámetro.** `Parametro` es la **tasa de aprendizaje** en las
  ramas de gradiente y momentum, pero la **tolerancia** en la rama de bisección (`:145`:
  `tol = Float64(Parametro) > 0 ? Float64(Parametro) : 1e-6`). La ayuda del docstring (`:28-30`) no lo dice:
  anuncia `TipoOutput=0: lista procedimientos, 1:Gradiente, 2:Momentum, 3:Newton, ...` sin mencionar que el
  significado de `Parametro` cambia con `TipoOutput`. Un usuario que pase `0.01` esperando una tasa de
  aprendizaje obtiene una tolerancia de 0.01, que es enorme.
- **Estructura:** una única `function JO_Optimizar(...)` (`:32`) de 287 líneas con 6+ algoritmos en un
  `if/elseif` sobre `TipoOutput`. `const PROC_OPTIMIZACION` (`:13`) lista los procedimientos como cadenas,
  de modo que añadir uno exige tocar la lista, el despacho y el cuerpo.

**Recomendación:** documentar la semántica de `Parametro` por rama (una línea de docstring) y, si se refactoriza,
una función por algoritmo con `JO_Optimizar` como único despachador. `INV-NX-03` (TipoOutput en `a2`) se
mantiene intacta.

### COD-35 · Validación de precondiciones inexistente en la librería Julia · **BAJA** · VERIFICADO

Sobre los 9 `.jl` de `src\libreria\JULIA`: **12 `try` / 12 `catch`**, pero **0 `@assert`, 0 `error(`,
0 `throw`**. Ninguna función valida dimensiones, rango ni tipo de sus argumentos antes de operar; se confía
en que la excepción de Julia la atrape un `catch` genérico aguas arriba. El único control de error visible
dentro de `J4XCL-OP-Optimizacion.jl` es la devolución de una cadena (`:191`: `"Error: Todos los valores del
lado derecho (b) deben ser >= 0"`), que mezcla el canal de error con el de datos.

---

## 7. Python — servidor HTTP del TaskPane, handlers, ControlPython y startup

### COD-36 · Cuatro copias divergentes de `neven_http_server.py` y seis de `rag_engine.py` · **ALTA** · VERIFICADO

**`neven_http_server.py` — hashes medidos (`Get-FileHash`):**

| Hash (12) | Tamaño | Fecha | Ruta | Estado |
|---|---:|---|---|---|
| `2F74824D39C3` | 214 KB | 2026-11-05 | `src\startup\neven_http_server.py` | **canónica** |
| `2F74824D39C3` | 214 KB | 2026-11-05 | `C:\NEVEN\startup\neven_http_server.py` | producción, **sincronizada** |
| `CC22AE05B87D` | 210 KB | 2026-10-19 | `src\TaskPane\neven_http_server.py` | divergente, tracked |
| `04B80A3FCA61` | 204 KB | 2026-10-19 | `src\ControlPython\startup\neven_http_server.py` | divergente, tracked |
| (211 KB) | 211 KB | 2026-10-20 | `src\Install\Dist\startup\neven_http_server.py` | artefacto `Dist\`, no tracked |
| `F11972977B8B` | 112 KB | 2026-09-28 | `src\Install\Dist\TaskPane\neven_http_server.py` | artefacto, no tracked |
| `F11972977B8B` | 112 KB | 2026-09-28 | `C:\NEVEN\taskpane\neven_http_server.py` | **copia muerta en producción** |

**`rag_engine.py` — tres hashes distintos en seis ubicaciones:**

| Hash | Ubicaciones |
|---|---|
| `B47326D3B443` (63 KB) | `src\startup\`, `src\TaskPane\`, `src\ControlPython\startup\`, `src\Install\Dist\startup\`, `C:\NEVEN\startup\` |
| `9EFF5D075C98` (63 KB) | `src\Install\scripts\rag_engine.py` |
| `1F6CAAE222EB` (42 KB) | `src\Install\Dist\TaskPane\`, `C:\NEVEN\taskpane\` |

**Agravante:** la regla de steering `.kiro\steering\neven-pre-cambios.md:144` indica como destino de
sincronización `NEVEN\TaskPane\neven_http_server.py`, que es **la copia divergente de 2026-10-19**, no la
canónica de `src\startup\`. Un mantenedor que siga la regla al pie de la letra copia hacia atrás 17 días de
trabajo.

**Impacto:** el servidor HTTP es el componente con mayor superficie del proyecto (65 endpoints). Que haya
cuatro versiones en el repositorio hace imposible saber qué está desplegado sin calcular hashes, e invalida
cualquier revisión de código sobre "el servidor".

### COD-37 · El servidor canónico es un monolito con despacho por `if/elif` · **ALTA** · VERIFICADO

**Evidencia:** `src\startup\neven_http_server.py` — 4 901 líneas, **2 clases** (`RateLimiter`,
`NEVENHandler(BaseHTTPRequestHandler)`), **104 `def`**, **65 endpoints `/api/*` distintos**.

Funciones de más de 80 líneas:

| Líneas | Línea | Función |
|---:|---:|---|
| **461** | 1816 | `_handle_ai_chat_impl` |
| **400** | 645 | `do_GET` |
| 212 | 3401 | `_handle_ontology_graph` |
| 151 | 1075 | `do_POST` |
| 144 | 2416 | `_handle_ai_chart` |
| 133 | 4474 | `_handle_rpivot` |
| 132 | 2816 | `_handle_db_connect` |
| 123 | 3898 | `_handle_rag_graph` |
| 103 | 3762 | `_handle_ayuda_funciones` |
| 90 | 4691 | `_handle_functions` |
| 89 | 1578 | `_handle_config_prompts_list` |
| 84 | 3108 | `_handle_user_chart_save` |

`do_GET` + `do_POST` = 551 líneas de cadena `if path == '/api/...' elif path.startswith('/api/...')`. Añadir
un endpoint exige editar el mismo bloque que todos los demás.

**Datos positivos verificados:** `eval(` 0, `exec(` 0, `shell=True` 0, `os.system` 0, `subprocess.` 6
(usos acotados), 190 docstrings, solo 7 líneas de más de 120 caracteres, 0 marcadores TODO/FIXME. La higiene
de seguridad y de formato es buena; el problema es estructural.

**Invariantes afectadas por una refactorización a tabla de rutas:** `INV-SB-01` (mutex
`Global\NEVEN_Studio_Launcher`), `INV-SB-02` (escritura UTF-8 sin BOM, `newline='\n'`), `INV-SB-03`
(`/api/query` solo SELECT/WITH/SHOW/DESCRIBE), `INV-SB-04` (token bucket 300/60 s → HTTP 429) y `INV-SB-05`
(`/api/ai/context/pending` consumible). **Una tabla de rutas las preserva todas** si el middleware de rate
limiting y la validación de `/api/query` se aplican en el despachador y no en cada rama — de hecho las
refuerza, porque hoy dependen de que cada rama nueva se acuerde de llamarlas. Se propone como ítem con la
condición explícita de añadir antes tests que fijen esas cinco invariantes.

### COD-38 · Observabilidad incoherente: `print` compite con `logging` · **MEDIA** · VERIFICADO

`src\startup\neven_http_server.py`: **15 `print(`** frente a **9 usos de `logging.`**; **2 `except:`
desnudos** y **83 `except Exception`**. Combinado con `C:\NEVEN\neven.log` en **120 MB sin rotación** (medido
en `00-layout-real.md` §5), diagnosticar un fallo de endpoint depende de ver stdout de un proceso que arranca
oculto.

Los 2 `except:` desnudos capturan también `KeyboardInterrupt` y `SystemExit`, lo que puede impedir el apagado
limpio del servidor.

### COD-39 · `datalab_handler.py` no está en la ruta canónica del servidor · **MEDIA** · VERIFICADO

**Evidencia:**

| Ruta | Tamaño | Hash (10) |
|---|---:|---|
| `src\ControlPython\startup\datalab_handler.py` | 48 454 B | `56BD1E86B7` |
| `src\Install\Dist\startup\datalab_handler.py` | 48 454 B | `56BD1E86B7` |
| `C:\NEVEN\startup\datalab_handler.py` | 48 454 B | (2026-09-01) |
| **`src\startup\datalab_handler.py`** | **NO EXISTE** | — |

El servidor canónico está en `src\startup\`, pero su handler de DataLab no. El origen de verdad del fichero
desplegado es `src\ControlPython\startup\`, que es donde también está la copia **divergente** del servidor
(COD-36). `src\docs\Mantenimiento\TROUBLESHOOTING.md:287` instruye verificar
`C:\NEVEN\startup\datalab_handler.py` "versión del 31/07/2026 o posterior" — la desplegada es del
2026-09-01, así que cumple, pero el repositorio no tiene ese fichero junto al servidor que lo importa.

**Dato positivo:** `_parse_slots_from_variable` tiene **una sola definición** en todo el árbol
(`src\ControlPython\startup\datalab_handler.py:857`, usada en `:314` y `:691`). La regla DRY del steering
se cumple para el parser de ControlR. Las otras 18 menciones son documentación y ontología.

---

## 8. JavaScript del TaskPane

### COD-40 · `taskpane.html`: 6 053 líneas de JavaScript inline (73 % del fichero) · **ALTA** · VERIFICADO

**Evidencia:** medición sobre `src\TaskPane\taskpane.html` (8 263 líneas, 392 KB):

| Métrica | Valor |
|---|---:|
| Líneas totales | 8 263 |
| **Líneas de JS inline** (10 bloques `<script>` sin `src`) | **6 053 (73 %)** |
| Líneas de CSS inline | 130 (2 %) |
| Funciones JS definidas inline | 97 |
| Asignaciones `.innerHTML =` | 114 |
| Llamadas `fetch(` | 56 |
| `onclick=` inline en el HTML | 25 |
| `try {` / `catch (` | 41 / 67 |

**Impacto:** ningún linter, ningún editor con análisis de JS y ninguna herramienta de cobertura trata este
código como JavaScript. No es navegable por símbolo, no es diffeable por función (un cambio de indentación
mueve miles de líneas) y las 114 asignaciones a `.innerHTML` no son auditables una por una. Es el fichero más
difícil de mantener del proyecto.

**Invariantes:** `INV-TF-04` prohíbe transpiladores y bundlers; `INV-TF-03` exige UTF-8 y copia con
`[System.IO.File]::Copy()`. **Extraer los 10 bloques `<script>` a ficheros `.js` servidos con
`<script src="...">` no viola ninguna de las dos**: sigue siendo ES5/ES6 vanilla cargado por el navegador sin
paso de build, exactamente como ya se hace con los 9 `.js` propios que el fichero carga. La invariante no es
el obstáculo; el obstáculo es el trabajo de dividir.

### COD-41 · `INV-TF-01` se cumple a medias: hay renderers de resultados paralelos · **MEDIA** · VERIFICADO

`INV-TF-01` (`neven-ontology-p3.yaml:332`): `buildSlotElement()` es el **único** renderer de resultados.

**Lo que cumple:** `buildSlotElement` tiene **una sola definición**, en `src\TaskPane\datalab.js:1528`.
`renderSlotTable` (`datalab.js:2430`), `_renderPlotlyJSON` (`datalab.js:1892`), `_addSendToSlideBtn`
(`taskpane.html:4371`) y `_loadFromContent` (`taskpane.html:2758`) también están definidos una sola vez.

**Lo que no cumple:**

| Ubicación | Renderer paralelo |
|---|---|
| `src\TaskPane\taskpane.js:1219` | `renderScriptResult(res)` — su propio `switch` sobre `res.type` (`'html'`, `'array'`), no llama a `buildSlotElement` en ningún punto (`git grep buildSlotElement -- src/TaskPane` no devuelve ninguna línea de `taskpane.js`) |
| `src\TaskPane\taskpane.html:7243` | comentario literal **"Fallback renderer si buildSlotElement no está disponible"** — un segundo renderer completo |
| `src\TaskPane\chart-gallery.js:1646` | `_renderBackendResult(data, container, language, library)` — despacho propio por tipo; reutiliza `renderSlotTable` pero tras un `typeof ... === 'function'` |
| `src\TaskPane\taskpane.html:5211` vs `src\TaskPane\taskpane.js:476` | `renderSQLResultRS(res)` y `renderSQLResults(result)` — par duplicado para el mismo propósito |
| `src\TaskPane\taskpane.html:5327` | `renderScriptResultRS(res)` — tercera variante del renderer de resultado de script |

Hay 37 funciones `render*`/`build*` en `src\TaskPane`, distribuidas entre `datalab.js` (12), `taskpane.js`
(18), `taskpane.html` (7) y `chart-gallery.js` (3).

**Acoplamiento frágil:** `taskpane.html:5391` y `:7213` invocan `buildSlotElement` solo tras comprobar
`typeof buildSlotElement === 'function'`. Es decir, la dependencia entre `taskpane.html` y `datalab.js` no
está declarada: depende del orden de las 23 etiquetas `<script>` y degrada en silencio al renderer de
respaldo si `datalab.js` no cargó.

**Veredicto `INV-TF-01`: PARCIAL.** La función única existe; la exclusividad declarada no.

### COD-42 · `showToast` definida tres veces · **MEDIA** · VERIFICADO

`.kiro\steering\neven-project-context.md` lo declara componente reutilizable único. Definiciones reales:

| Ubicación | Firma |
|---|---|
| `src\TaskPane\audiobook.js:43` | `function showToast(message, duration = 3000)` |
| `src\TaskPane\taskpane.html:2336` | `window.showToast = function(text)` |
| `src\TaskPane\taskpane.html:2657` | `function showToast(text)` |

Tres firmas distintas, dos de ellas en el mismo fichero. La de `:2657` sombrea a `window.showToast` dentro de
su ámbito, así que el comportamiento depende de desde dónde se llame.

### COD-43 · Cuatro librerías de CDN se cargan dos veces · **MEDIA** · VERIFICADO

`src\TaskPane\taskpane.html` tiene **23 etiquetas `<script src=>` para 18 recursos distintos**. Duplicados:

| Recurso | Veces |
|---|---:|
| `https://cdn.plot.ly/plotly-2.32.0.min.js` | 2 |
| `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js` | 2 |
| `https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js` | 2 |
| `.../katex@0.16.9/dist/contrib/auto-render.min.js` | 2 |
| `sketch-charts.js` | 2 (una con `?v=20260819`, otra sin versión) |

Plotly son ~3,5 MB: descargarlo y parsearlo dos veces retrasa visiblemente la apertura del TaskPane.

### COD-44 · Cache-busting manual e incoherente · **BAJA** · VERIFICADO

`color-palettes.js?v=20260819`, `sketch-charts.js?v=20260819`, `datalab.js?v=20260819170000`,
`taskpane.js?v=20260925113746`, `chart-classification.js?v=20260820`, `chart-gallery.js?v=20260820`,
`ayuda.js?v=20260819202000`, `audiobook.js?v=20260819`, y `sketch-charts.js` sin ninguna.

Cuatro formatos distintos de sello (fecha, fecha+hora, fecha+hora+segundos, ninguno) puestos a mano. Una
actualización de `datalab.js` sin tocar su `?v=` deja a los usuarios con la versión antigua en caché y con
el `typeof buildSlotElement` de COD-41 cayendo al renderer de respaldo sin aviso.

### COD-45 · Las 7 dependencias de CDN se cargan sin `integrity` ni copia local · **MEDIA** · VERIFICADO

`office.js`, `plotly-2.32.0`, `d3@7`, `d3-sankey@0.12.3`, `leaflet@1.9.4`, `katex@0.16.9` y
`katex auto-render` se cargan desde `appsforoffice.microsoft.com`, `cdn.plot.ly`, `cdn.jsdelivr.net` y
`unpkg.com` **sin atributo `integrity`** y sin copia en `src\TaskPane`.

Lo registro aquí como calidad, no como seguridad (eso es del Eje 3): **sin conexión a internet el TaskPane
pierde todos los gráficos, los mapas y el renderizado de fórmulas**, y el fallo se manifiesta como una
pantalla vacía sin mensaje. Para un add-in de Excel que se vende como escritorio, es una dependencia de red
no declarada en los requisitos.

---

## 9. Documentación LaTeX del paper

**Alcance:** `src\docs\Paper\` — `main.tex` (141 líneas), `sections\` (9 `.tex`), `figures\` (2),
`references.bib` (386 líneas, 41 entradas), más dos árboles paralelos: `arxiv-submission\` y `sections_old\`.

### COD-46 · `Panko2016` tiene un DOI que apunta a otro trabajo · **ALTA** · VERIFICADO (herramienta) / requiere confirmación del autor

**Evidencia:** `src\docs\Paper\references.bib`, entrada `@article{Panko2016}`:

```
author  = {Panko, Raymond R.}
title   = {What We Don't Know About Spreadsheet Errors Today: ...}
journal = {Journal of Organizational and End User Computing}
volume  = {28}, number = {1}, pages = {1--21}, year = {2016}
doi     = {10.4018/JOEUC.2016010101}
```

`verify_citations.py` contra Crossref devuelve:

```
FAIL Panko2016: mismatch
  - DOI points to a different work: 'Unsuccessful Performance and Future
    Computer Self-Efficacy Estimations' (similarity 0.18)
  - first author 'panko' but record says 'johnson'
```

El mismo error está en `src\docs\Paper\arxiv-submission\references.bib` (fichero idéntico, 12 451 B ambos).

**Impacto:** la cita que sostiene la motivación del paper (errores en hojas de cálculo) envía al lector al
artículo de otro autor del mismo número de la revista. Es el tipo de defecto que genera una corrección
posterior a la publicación. El skill de verificación es explícito: un `mismatch` **requiere confirmación
humana**, porque solo el autor sabe qué artículo quiso citar. **Acción: el autor debe obtener el DOI correcto
de la página del editor, no de la memoria.**

### COD-47 · El paper afirma 342 tests; el binario reporta 369 · **MEDIA** · VERIFICADO

**Evidencia:** `src\docs\Paper\sections\06_conclusion.tex:11` — "a suite of 342 automated unit,
property-based, and security tests provides a robust foundation for academic and enterprise adoption".
Idéntico en `arxiv-submission\sections\06_conclusion.tex:11`.

Real: 369 en 47 suites. Es una afirmación numérica verificable y publicada.

### COD-48 · "70 procedimientos Julia" y "más de 200 funciones numéricas" no se sostienen con el repositorio · **MEDIA** · VERIFICADO (lo medible) / NO VERIFICABLE (las 200)

**Evidencia:** `src\docs\Paper\sections\06_conclusion.tex:11` — "70 high-level Julia procedures backed by
more than 200 numerical functions".

Medición: `src\libreria\JULIA` tiene 9 ficheros con **60 definiciones** (40 `function nombre` + 20 de una
línea). La cifra de 70 excede en 10 lo que hay. Las "más de 200 funciones numéricas" **no son verificables
desde el repositorio**: si se refieren a funciones de paquetes de terceros alcanzables (LinearAlgebra,
Statistics, GLM…) la afirmación es cierta pero no es un aporte de NEVEN, y el paper no lo aclara.

**Contraste honesto:** la afirmación paralela sobre R **sí se sostiene**. "over 70 R econometric and
statistical procedures" frente a **78 definiciones `x <- function(`** en los 37 `.R` no-Studio de
`src\libreria\R`.

Otras afirmaciones del mismo párrafo y de la sección de disponibilidad, comprobadas:

| Afirmación | Ubicación | Verificación |
|---|---|---|
| `Ejemplos/Excel/WOOLDRIDGE/` | `06_conclusion.tex:36` | **existe** (`src\libreria\EJEMPLOS\Excel\WOOLDRIDGE`) |
| `Ejemplos/Excel/BONILLA/` | `06_conclusion.tex:36` | **existe** |
| GNU GPL v3 | `06_conclusion.tex:31` | `src\LICENSE` presente, cabecera consistente |
| "docs/ directory, 26 chapters" | `06_conclusion.tex:34` | `src\docs` tiene **129 ficheros `.md`** en 18 subdirectorios; la correspondencia con "26 capítulos" **no se pudo verificar** (no hay un índice numerado que los enumere) |
| "11-format WebView2 unified viewer" | `06_conclusion.tex:11` | **no verificada** — no se enumeró la lista de formatos de `ViewerManager`; queda para el Eje 1 |
| "nine-module NEVEN Studio IDE" | `06_conclusion.tex:11` | **no verificada** — no hay una definición de "módulo de Studio" en el código que permita contarlos |
| "five-layer static SandboxVerifier" | `06_conclusion.tex:18` | **no verificada en este eje** — corresponde al Eje 3 |

### COD-49 · 8 entradas del `.bib` definidas y nunca citadas · **BAJA** · VERIFICADO

De las 41 entradas de `references.bib`, **33 están citadas** desde `main.tex`, `sections\*.tex` o
`figures\*.tex`. Las 8 no citadas: `White1980`, `Wilson2014`, `Stodden2014`, `Tanenbaum2014`,
`ExcelSDK2023`, `GTest2023`, `Claerbout1992`, `Gentleman2007`.

No hay ninguna clave citada sin definir (0), así que el documento compila sin `??`. Las 8 entradas
simplemente no aparecerán en el PDF. Es higiene: o se citan o se retiran.

### COD-50 · Tres árboles del paper coexisten y divergen · **BAJA** · VERIFICADO

| Árbol | Contenido |
|---|---|
| `src\docs\Paper\sections\` | **versión viva** (9 `.tex`) |
| `src\docs\Paper\arxiv-submission\sections\` | copia para arXiv (10 `.tex`) |
| `src\docs\Paper\sections_old\` | versión histórica (8 `.tex`) |

`sections\05_discussion.tex` = 11 146 B frente a `arxiv-submission\sections\05_discussion.tex` = 11 190 B:
**divergen**. El resto de las secciones coincide en tamaño.

**Dato relevante para la regla anti-artefacto-IA:** el artefacto de conteo que la regla prohíbe **existe pero
solo en la copia muerta**. `sections_old\06_conclusion.tex:33` dice "We identify **five** directions for
future research and development", mientras la versión viva dice "We identify **four** concrete directions"
(`sections\06_conclusion.tex:15`) **seguida de exactamente cuatro `\paragraph{}`** (`:17`, `:20`, `:23`,
`:26`). La versión viva es correcta; la obsoleta, si alguien la resucita, arrastra el defecto.

### COD-51 · Los controles anti-artefacto-IA de la regla del proyecto se CUMPLEN · **INFORMATIVA** · VERIFICADO

Comprobación uno por uno del checklist de `.kiro\steering\ai-artifact-prevention.md` §7:

| Control exigido | Resultado medido |
|---|---|
| **Cero campos `note` en el `.bib`** | **0** en `references.bib` y en `arxiv-submission\references.bib` ✔ |
| **Sin puntos dentro de `\paragraph{}`** | **0** coincidencias de `\paragraph\{[^}]*\.\}` en todos los `.tex` ✔ |
| **≤15–20 em-dashes en el paper** | Em-dashes en prosa ≈ **0**. Los 16 `---` de `main.tex` son separadores de comentario LaTeX (`%% --- Essential Packages ... ---`, `:7`, `:20`, `:60`, `:71`, `:76`, `:86`). `U+2014` aparece **1 vez por fichero de sección**, siempre en la cabecera de comentario de la línea 1 ✔ |
| **Números de lista coherentes con los ítems** | "four concrete directions" (`06_conclusion.tex:15`) → 4 `\paragraph{}` ✔. La discrepancia solo está en `sections_old\` (COD-50) |
| **≤1 antítesis arquetípica, ≤2 tricolons** | No medido automáticamente; el índice de triadas del linter es ≤4.8 por 1 000 palabras |
| **`bib_lint`** | `41 entries: 0 errors, 0 warnings, 0 info` — exit 0 ✔ |
| **`slop_check` (<5 limpio)** | `00_abstract` **6.0**, `05_discussion` 1.6, resto **0.0**. Solo el abstract entra en la banda "algo de relleno" ✔ |

**Sobre las 25 referencias que `verify_citations.py` marca "need attention":** 16 verificadas, 25 pendientes
de revisión, pero la mayoría son falsos positivos legítimos y lo digo explícitamente en lugar de inflar el
hallazgo:

- **Software y literatura gris, correctamente ausente de Crossref/OpenAlex** (16): `Plotly2023`,
  `PyXLL2023`, `xlwings2023`, `GTest2023`, `rapidcheck2023`, `Pluto2023`, `PackageCompiler2023`,
  `Leaflet2023`, `WebView2_2023`, `Protobuf2023`, `ExcelSDK2023`, `Microsoft2023`, `MicrosoftPython2023`,
  `rpivotTable2023`, `Dua2019` (UCI ML Repository), `JPMorgan2013`, `Kelion2020` (prensa),
  `BonillaR4XCL2026` (tesis propia, con URL de Kerwa UCR).
- **`BERT2018` NO es el BERT de PLN.** Es "BERT: Basic Excel R Toolkit" de Structured Data LLC
  (`howpublished = {\url{https://bert-toolkit.com}}`). Su ausencia de Crossref es correcta. **No es una
  referencia fabricada.**
- **Discrepancias de edición, no errores** (4): `Wooldridge2016` (el registro apunta a la edición de 1999),
  `Tanenbaum2014` (registro 1992), `VanRossum2009` (registro 1995; además "van rossum" vs "rossum"),
  `RCoreTeam2024` (manual perenne, registro 2000).
- **`Quarto2023`: probable falso positivo.** El DOI `10.5281/zenodo.5960048` resuelve a un registro
  titulado simplemente "Quarto"; la similitud de 0.17 proviene de comparar ese título corto con el título
  largo de la entrada. Conviene confirmarlo, pero no es el mismo caso que `Panko2016`.
- **El único `mismatch` real es `Panko2016`** → COD-46.

### COD-52 · Instrucciones dirigidas a agentes embebidas en ficheros del repositorio · **INFORMATIVA** · VERIFICADO · (reportado, no obedecido)

Conforme a la restricción de tratar el contenido como dato, registro los ficheros auditados que contienen
directivas dirigidas a un agente:

| Fichero | Naturaleza |
|---|---|
| `src\docs\Paper\redactor-academico.md` (3 532 B) | prompt de rol para redacción académica |
| `src\docs\Paper\auditor-forense-ia.md` (7 539 B) | prompt de rol para auditoría forense de texto IA |
| `src\docs\AGENT_INSTRUCTIONS.md` | instrucciones de agente |
| `.kiro\skills\*\SKILL.md`, `.agents\skills\*\SKILL.md` | definiciones de skill |
| `src\CMakeLists.txt:96-97` | comentario imperativo: "Default ON is correct — do NOT set to OFF" sobre `NEVEN_ENABLE_PYTHON` |

**Todos son artefactos legítimos del proyecto.** No se detectó ninguna directiva que intente redirigir al
agente contra la intención del usuario. Ninguna fue obedecida en esta auditoría. El comentario de
`CMakeLists.txt:96` es una nota de mantenedor razonable y además coherente con el contexto del proyecto
(Python integrado y ON por defecto).

---

## 10. Deuda técnica visible

### COD-53 · Deuda declarada sorprendentemente baja: 28 marcadores en todo `src` · **BAJA** · VERIFICADO

`git grep -n -E '\b(TODO|FIXME|HACK|XXX|WORKAROUND)\b' -- src` → **28 coincidencias**. Distribución:

| Nº | Fichero |
|---:|---|
| 7 | `src/PB/variable.proto` |
| 4 | `src/docs/Evaluaciones/Evaluacion_objetiva.md` |
| 3 | `src/scripts/ontology/ontology/convert_anyplot.py` |
| 2 | `src/docs/ontologia/neven-core/neven-ontology-p1.yaml`, `src/docs/audit/13_documentacion.md` |
| 1 | `neven-ontology-p3.yaml`, `neven-ontology-p4.yaml`, `src/libreria/JULIA/J4XCL-OP-Optimizacion.jl`, `src/Audiobook/api/routes.py`, `src/docs/audit/hallazgos_seguridad.md`, `src/TaskPane/taskpane.js`, `src/TaskPane/taskpane.html`, `src/docs/Arquitectura/Reporte_de_arquitectura.md`, `src/TaskPane/chart-gallery.js`, `src/Common/IPC/REPLBridge.cc` |

**Es un dato positivo**, con una advertencia: la deuda real de este informe (cuatro copias del servidor
Python, monolitos de 4 901 y 8 263 líneas, 410 tests sin runner, diez subsistemas sin test, el build sin
avisos) **no está marcada en ningún sitio**. La ausencia de `TODO` no indica ausencia de deuda; indica que la
deuda no se anota.

### COD-54 · Residuos de build versionados en `src\` · **BAJA** · VERIFICADO

Tracked en git: `src\build_log.txt`, `src\build_studio_fix.txt`, `src\ribbon_build.txt`,
`src\ribbon_build2.txt`, `src\ribbon_build3.txt` (más `build_release.log`, `cmake_config.log`,
`cmake_config2.log` según `00-layout-real.md` §7.16). Son salidas de compilación de una máquina concreta.

`INV-BLD-03` prohíbe commitear binarios de `Build/Dist/` y **se cumple** (`src\Install\Dist\` tiene 996
ficheros en disco, ninguno tracked). Estos `.txt` no son binarios, así que no la violan técnicamente, pero
son el mismo tipo de residuo y `repo_hygiene_tests.cc` ya tiene el patrón de test adecuado para cerrarlos.

### COD-55 · Directorios muertos versionados · **BAJA** · VERIFICADO

| Directorio | Ficheros tracked | Observación |
|---|---:|---|
| `src\TaskPane\deprecated\GR_DataLab_migrated\` | 19 | 9 de 10 `.R` idénticos a los vivos (COD-32) + 10 sidecars `.json` |
| `src\docs\_legacy\RJ2XCLModule_2018\` | 9 | paquete R de 2018, incluye `src\RJ2XCLModule.cc` |
| `src\ControlJulia\legacy\Julia_Environment.cpp` | 1 | **excluido a propósito** del build (`ControlJulia\CMakeLists.txt:35`) |
| `src\ControlR\legacy\R_Environment.cpp` | 1 | **excluido a propósito** del build (`ControlR\CMakeLists.txt:50`) |

Los dos `legacy\*.cpp` tienen una justificación documentada en el `CMakeLists` ("exclude ... which uses
xloper12 from Excel SDK"), de modo que su presencia es deliberada. `deprecated\` y `_legacy\` no tienen
ninguna.

**Dato positivo:** no hay ficheros `.cc` huérfanos del build, pero la comprobación es débil **porque
`src\Core\CMakeLists.txt:2` usa `file(GLOB)`** y por tanto cualquier `.cc` en `src\Core\src\` entra
automáticamente. Es decir, en Core no puede haber un `.cc` no compilado, pero tampoco puede haber uno que
alguien decidiera excluir: compilar o borrar son las únicas opciones (relacionado con COD-16).

### COD-56 · Encoding de la documentación: correcto, con una inconsistencia menor · **INFORMATIVA** · VERIFICADO

Corrijo una impresión inicial errónea: los `.md` de `src\docs` **no** tienen problema de doble codificación.
De los 129 ficheros `.md`, **solo 4 contienen algún marcador de mojibake, y suman 5 marcadores en total**.
La apariencia de doble codificación al volcar los ficheros en consola era un artefacto del code page de
PowerShell, no de los bytes. (El mojibake real sí está en `.kiro\contexto\CHAT.md` y `CHAT_LARGO.md`, pero eso
ya está registrado en `00-layout-real.md` §5 y no es código.)

La única incoherencia: `src\docs\sops\testing-guide.md` **tiene BOM UTF-8**, mientras
`src\docs\sops\coding-standards.md` y `src\docs\sops\error-handling.md` no. Son tres documentos del mismo
directorio con dos convenciones. `INV-INS-04` exige UTF-8 **sin BOM** para los JSON desplegados, no para los
`.md`, así que no hay violación.

---

## 11. Veredicto sobre las invariantes `INV-*` que toca este eje

Las 62 invariantes son del conjunto completo del proyecto; aquí dictamino **solo** las que caen en el eje de
calidad de código y que pude verificar con evidencia. Las que corresponden al Eje 1 (producto) o al Eje 3
(seguridad) las dejo explícitamente sin veredicto en lugar de inventarlo.

| Invariante | Veredicto | Evidencia |
|---|---|---|
| `INV-CORE-01` | **CUMPLE** | `MapFunctions()`/`RegisterFunctions()` solo en `Init()` (`rj2xcl.cc:500-502`), llamado solo desde `xlAutoOpen` (`:641`). `ScheduleDelayedUpdate()`, que podría registrar fuera de contexto, nunca se invoca (COD-05) |
| `INV-CORE-02` | **CUMPLE** | Orden observado: zombie cleanup `:457-476` → `file_watch_service_->Start()` `:480` → `ConnectLanguages()` `:487` |
| `INV-CORE-03` | **CUMPLE** | `g_neven_initialized` en `:617`, comprobado en `:620-625`, reseteado en `:662` |
| `INV-CORE-04` | **NO VERIFICADO** | no se leyó `src\Core\src\rj2xcl.def`; los cuatro exports **sí existen** en `rj2xcl.cc:619, 653, 670, 690` |
| `INV-CR-03` | **PARCIAL** | la validación de versión existe, pero el parseo usa `atoi` sin distinguir fallo de `0` (COD-09, `r_engine_loader.cc:174,186`) |
| `INV-NX-01` | **CUMPLE** | `R4XCL-0-NevenX.R`: 0 bytes >127, sin BOM (verificado byte a byte) |
| `INV-NX-02` | **CUMPLE** | llaves balanceadas (apertura = cierre) |
| `INV-NX-03` | **CUMPLE** (documental) | `R4XCL-0-NevenX.R:8` y firma `:191` |
| `INV-NX-04` | **CUMPLE** | `agrep` y `R4XCL_Error` presentes (`:283-287`) |
| `INV-LR-02` | **VIOLADA** | `library()` en nivel superior en **30 de 63** ficheros (COD-27) |
| `INV-LR-03` | **PARCIAL** | el contrato `R4XCL_` se respeta en la ruta feliz, pero 34 de 63 ficheros no tienen `tryCatch` que lo garantice ante error (COD-29) |
| `INV-LR-04` | **VIOLADA** (al menos 5 ficheros) | sin `DialogosXCL$Descripcion` **ni** `attr(`: `R4XCL-AD-NonParRolCor.R`, `R4XCL-BD-ObtieneDatos.R`, `R4XCL-DS-Wooldridge.R`, `R4XCL-GR-Mapa.R`, `R4XCL-NEVEN-pluto-read.R` (COD-28) |
| `INV-SR-01` / `INV-SR-05` | **NO VERIFICADO** | no se auditó `startup.r` en este eje; dato parcial: ningún `.R` del repositorio tiene BOM, lo que es consistente con `INV-SR-05` |
| `INV-CJ-01` / `INV-CJ-02` | **NO VERIFICADO** | no se inspeccionó `neven_julia.version` ni el script de precompile. **Relevante:** COD-33 (envolver la librería Julia en `module`) exigiría reconstruir la sysimage y revalidar ambas |
| `INV-CJ-03` | **CUMPLE** (indirecto) | los tres `Control*` usan `Common\IPC\pipe.cc`; llamadas directas al API de pipes: 0 / 1 / 2 (COD-10) |
| `INV-SB-01..05` | **NO VERIFICADO** en este eje | son del Eje 3. Advertencia de este eje: COD-37 propone refactorizar el despacho del servidor, lo que **las toca a todas cinco** → condicionar a tests que las fijen primero |
| `INV-TF-01` | **PARCIAL** | `buildSlotElement` definida una vez (`datalab.js:1528`) ✔, pero hay 4 renderers paralelos (COD-41) ✘ |
| `INV-TF-02` | **NO VERIFICADO** | no se auditó el reseteo de `_dlState` en `selectFunction()` |
| `INV-TF-03` | **CUMPLE** (parcial) | ficheros del TaskPane en UTF-8; no se auditaron los scripts de copia |
| `INV-TF-04` | **CUMPLE** | 23 `<script src=>` planos, sin bundler ni transpilador en el árbol. La extracción de COD-40 es compatible |
| `INV-BLD-01` | **CUMPLE** | `src\CMakeLists.txt:8` — `CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>"` |
| `INV-BLD-02` | **CUMPLE** en el `CMakeLists` | `:20` `add_compile_options(/GS /guard:cf)`, `:24` `add_link_options(/DYNAMICBASE /NXCOMPAT /CETCOMPAT)`. **No verificado sobre el binario** (eso requiere inspeccionar `C:\NEVEN\NEVEN64.xll` con el MCP `rea`, trabajo del Eje 3) |
| `INV-BLD-03` | **CUMPLE** | `src\Install\Dist\` no tracked |
| `INV-BLD-04` | **NO VERIFICADO** | no se auditó `Addin\CMakeLists.txt` |
| `INV-TEST-01` | **CUMPLE** | `build_verification_tests.cc` existe con 4 tests; COD-14 (añadir `/W3`) **no lo rompe** porque solo comprueba presencia, no exclusividad |
| `INV-TEST-02` | **CUMPLE** | `src\tests\CMakeLists.txt` copia `mock_engine_backend` en `POST_BUILD` |
| `INV-TEST-03` | **NO VERIFICADO** | no se ejecutaron los tests (COD-21). Indicio favorable: existen 30 mock headers de R/Julia en `src\Include` |
| `INV-INS-01` | **CUMPLE** | ya verificado en `00-layout-real.md` §6; no se encontró ningún secreto nuevo en este eje |
| `INV-CMN-03` | **NO VERIFICADO** en este eje | `MessageValidator::SafeUnframe()` es materia del Eje 3 |

### ¿Alguna invariante debería cambiar?

**No propongo cambiar ninguna.** Dos merecen comentario explícito:

1. **`INV-TF-04` (sin bundlers ni transpiladores)** es la invariante que a primera vista bloquea la solución
   obvia a COD-40 (6 053 líneas de JS inline). **No la bloquea:** dividir el inline en ficheros `.js`
   servidos con `<script src=>` no necesita ningún paso de build. La invariante se mantiene y se respeta.
   Lo que sí impide es introducir módulos ES con `import`/`export`, y por eso la propuesta usa globales
   explícitos declarados en un único punto, no módulos.
2. **`INV-CJ-01`/`INV-CJ-02`** son el coste real de COD-33 (la librería Julia sin `module`). Aquí no digo
   que haya que cambiarlas: digo que **cualquier cambio de namespace en `src\libreria\JULIA` obliga a
   reconstruir `neven_julia.dll` (~1,04 GB) y a reejecutar el script de precompile de forma independiente**,
   y que por eso el ítem va con prioridad baja y con esa condición escrita.

---

## 12. Estado de los hallazgos de código de la auditoría previa

`src\docs\INFORME_AUDITORIA.md` (v1.0, salud 6,0/10, 36 hallazgos). **Limitación declarada:** el informe no
usa identificadores estables en su tabla — una extracción por patrón `CM-[A-Z]{3}-\d{3}` sobre el fichero
devuelve **0 coincidencias**, de modo que **no pude emparejar hallazgo por hallazgo**. Lo que sí pude
verificar son las trazas que la remediación dejó en el código:

| Hallazgo previo | Estado | Evidencia |
|---|---|---|
| `CM-BAJ-004` — `AddTrustedSignature` / `EvaluateScript` sin invocaciones | **RESUELTO** | eliminados, con nota: `src\Common\Security\SandboxVerifier.cc:40` y `:43`; `src\Include\SandboxVerifier.h:48` y `:78` |
| `CM-BAJ-014` — `m_trusted_signatures` nunca consultado | **RESUELTO** | `src\Include\SandboxVerifier.h:90` — "eliminado v2.3" |
| `CM-BAJ-005` — `RemoveUserButton` con cuerpo vacío | **RESUELTO** | `src\Core\include\rj2xcl.h:203` y `src\Core\src\rj2xcl.cc:281` |
| Consola Electron (código muerto) | **RESUELTO** | `src\CMakeLists.txt:124-126` declara la eliminación y apunta a `Common\REPLManager.cc` / `Common\IPC\REPLBridge.cc` como sustituto. No se encontraron fuentes de Electron en el árbol |
| Informes `10..12_codigo_muerto_*.md` de `src\docs\audit\` | **PARCIAL** | el mecanismo de cierre funciona (los tres anteriores lo prueban) pero quedan `deprecated\`, `_legacy\` y los residuos de build (COD-54, COD-55), y aparecen muertos nuevos: `ScheduleDelayedUpdate()` e `instance_` (COD-05) |
| Resto de hallazgos de código del informe v1.0 | **NO VERIFICADO** | sin identificadores estables no es posible el emparejamiento uno a uno. **Recomendación concreta: asignar IDs a la tabla de `INFORME_AUDITORIA.md` antes de la siguiente iteración**, o el informe seguirá sin poderse cerrar |

**Patrón digno de imitación:** las tres resoluciones confirmadas dejaron un comentario en el punto exacto del
código con el ID del hallazgo y la versión (`// CM-BAJ-005: RemoveUserButton eliminado v2.3 — ...`). Eso es
lo que permitió verificarlas cuatro meses después. Debería ser la norma.

---

## 13. Candidatos para el plan de trabajo

Clasificación: **PENDIENTES** = defectos que rompen o pueden romper algo y hay que arreglar.
**POR MEJORAR** = funciona, pero su estructura o su coherencia cuesta mantenerla.
**NUEVAS IDEAS** = no existe hoy y aportaría.

Prioridad propuesta: **P1** (antes de la siguiente release) · **P2** (siguiente ciclo) · **P3** (cuando haya
hueco).

## 13.1 PENDIENTES

| ID | Prioridad | Qué | Rutas afectadas | Invariantes |
|---|---|---|---|---|
| **PEN-01** | **P1** | Envolver los cuatro exports del XLL en `try/catch (...)` y registrar en `neven.log` antes de devolver. COD-01 | `src\Core\src\rj2xcl.cc:619-651, 653-668, 670-686, 690-707` | **No viola ninguna.** Preserva `INV-CORE-01/02/03` (no cambia orden ni contexto) y `INV-CORE-04` (no cambia exports) |
| **PEN-02** | **P1** | Corregir el DOI de `Panko2016`. **El autor debe obtenerlo de la página del editor, no de la memoria.** Verificar también `Quarto2023`. COD-46 | `src\docs\Paper\references.bib`, `src\docs\Paper\arxiv-submission\references.bib` | **Ninguna** |
| **PEN-03** | **P1** | Arreglar el trigger del CI: `branches: [ master ]` en los cuatro puntos, y corregir la ruta del artefacto. COD-19 | `src\.github\workflows\build-and-test.yml:5, 7, 13, 54, 81` | **Ninguna.** Habilita la evaluación automática de `INV-TEST-01` |
| **PEN-04** | **P1** | Resolver las copias del servidor Python: declarar `src\startup\` como única fuente, borrar `src\TaskPane\neven_http_server.py` y `src\ControlPython\startup\neven_http_server.py`, y **corregir `neven-pre-cambios.md:144`**, que hoy señala la copia equivocada. Igual para las 3 variantes de `rag_engine.py`. COD-36 | `src\startup\`, `src\TaskPane\`, `src\ControlPython\startup\`, `src\Install\scripts\`, `.kiro\steering\neven-pre-cambios.md:144` | **Ninguna.** Nota: `C:\NEVEN\taskpane\neven_http_server.py` (112 KB, muerta) es producción viva → **no tocar en esta auditoría**; retirarla exige ventana de mantenimiento |
| **PEN-05** | **P1** | Mover `datalab_handler.py` junto al servidor canónico (`src\startup\`) o declarar formalmente que su origen es `src\ControlPython\startup\` y documentarlo. COD-39 | `src\startup\`, `src\ControlPython\startup\datalab_handler.py`, `.kiro\steering\neven-pre-cambios.md` | **Ninguna** |
| **PEN-06** | **P1** | Migrar los 30 `library()` de nivel superior a `requireNamespace(..., quietly=TRUE)` dentro de `tryCatch`. Un fallo de paquete no debe tumbar el `source()` completo. COD-27 | los 30 `.R` de `src\libreria\R` listados en COD-27 | **Cierra `INV-LR-02`** (hoy violada). Despliegue con `UTF8Encoding($false)` por `INV-SR-05` |
| **PEN-07** | **P1** | Cambiar `vcovHC(type = "HC")` (HC0) por `"HC3"`. Una línea; corrige errores estándar robustos anticonservadores en muestras pequeñas. COD-31 | `src\libreria\R\R4XCL-RG-Lineal.R:124` | **Ninguna** |
| **PEN-08** | **P2** | Añadir `attr(..., DialogosXCL$Descripcion)` a los 5 ficheros sin ningún `attr(`, y auditar individualmente los 8 que usan otra forma. COD-28 | `R4XCL-AD-NonParRolCor.R`, `R4XCL-BD-ObtieneDatos.R`, `R4XCL-DS-Wooldridge.R`, `R4XCL-GR-Mapa.R`, `R4XCL-NEVEN-pluto-read.R` | **Cierra `INV-LR-04`** |
| **PEN-09** | **P2** | Anclar `rapidcheck` a un SHA y añadir `URL_HASH SHA256` a Protobuf y WebView2. COD-15 | `src\CMakeLists.txt:34-37, 52-57, 70-79` | **Ninguna** |
| **PEN-10** | **P2** | Acotar el zombie cleanup a procesos huérfanos (registro de PIDs o JobObject de la sesión previa) en lugar de `taskkill /IM`. COD-02 | `src\Core\src\rj2xcl.cc:457-476` | **`INV-CORE-02` se preserva**: la invariante fija el orden (limpieza antes de `Start()`/`ConnectLanguages()`), no el mecanismo |
| **PEN-11** | **P2** | Hacer `available_` un `std::atomic<bool>`; fijar `max_viewers_`/`max_memory_mb_` antes de lanzar el hilo STA. COD-06 | `src\Common\ViewerManager.h:188, 211-212`, `src\Common\ViewerManager.cc:99, 123, 139, 146` | **Ninguna** |
| **PEN-12** | **P2** | Sustituir `TerminateThread` por "registrar y abandonar el hilo": el proceso termina de todos modos y así no se corrompe el heap de Excel. COD-07 | `src\Common\ViewerManager.cc:155-166` | **Ninguna** |
| **PEN-13** | **P2** | Eliminar `RJ2XCL_Engine::ScheduleDelayedUpdate()` y el miembro muerto `instance_`. Dejar el comentario con ID del hallazgo, como se hizo con `CM-BAJ-005`. COD-05 | `src\Core\src\rj2xcl.cc:60, 538-558`, `src\Core\include\rj2xcl.h:60, 193` | **Ninguna.** Elimina la única ruta que podría registrar funciones fuera de `xlAutoOpen` → **refuerza `INV-CORE-01`** |
| **PEN-14** | **P2** | Añadir `CONFIGURE_DEPENDS` a los tres `file(GLOB)` de fuentes, y convertir los "globs de nombres literales" de ControlR/ControlJulia en `set()`. COD-16 | `src\Core\CMakeLists.txt:2`, `src\NEVEN-SIM\CMakeLists.txt:10`, `src\NEVEN-SIM\tests\CMakeLists.txt:7-8`, `src\ControlR\CMakeLists.txt:53`, `src\ControlJulia\CMakeLists.txt:37` | **Ninguna** |
| **PEN-15** | **P2** | Envolver el cuerpo analítico de los 34 `.R` sin `tryCatch` con `error = function(e) data.frame(R4XCL_Error = conditionMessage(e))`. COD-29 | 34 ficheros de `src\libreria\R` | **Refuerza `INV-LR-03` e `INV-NX-04`** |
| **PEN-16** | **P3** | Corregir `showToast`: una sola definición, firma única con `duration` opcional. COD-42 | `src\TaskPane\audiobook.js:43`, `src\TaskPane\taskpane.html:2336, 2657` | **Ninguna** |
| **PEN-17** | **P3** | Quitar las 5 etiquetas `<script src=>` duplicadas (Plotly, Leaflet, KaTeX ×2, sketch-charts). COD-43 | `src\TaskPane\taskpane.html` | **Ninguna**; `INV-TF-04` intacta |
| **PEN-18** | **P3** | Actualizar las cifras del paper: 342 → 369 tests; revisar "70 procedimientos Julia" (hay 60) y aclarar o retirar "más de 200 funciones numéricas". COD-47, COD-48 | `src\docs\Paper\sections\06_conclusion.tex:11`, `src\docs\Paper\arxiv-submission\sections\06_conclusion.tex:11` | **Ninguna** |
| **PEN-19** | **P3** | Añadir null-check en `xlAutoFree12`. COD-03 | `src\Core\src\rj2xcl.cc:670` | **Ninguna** |
| **PEN-20** | **P3** | Borrar `src\docs\Plan_trabajo\coding-standards.md` (duplicado byte a byte) y dejar `src\docs\sops\` como única fuente. COD-12 | `src\docs\Plan_trabajo\coding-standards.md` | **Ninguna** |
| **PEN-21** | **P3** | Retirar los residuos de build versionados y añadir un test de higiene que los impida. COD-54 | `src\build_log.txt`, `src\build_studio_fix.txt`, `src\ribbon_build{,2,3}.txt`, `src\.gitignore`, `src\tests\repo_hygiene_tests.cc` | **Ninguna**; alinea con el espíritu de `INV-BLD-03` |
| **PEN-22** | **P3** | Consolidar los árboles del paper: retirar `sections_old\` (contiene el artefacto "five directions") y reconciliar `05_discussion.tex` entre `sections\` y `arxiv-submission\`. COD-50 | `src\docs\Paper\sections_old\`, `src\docs\Paper\arxiv-submission\sections\05_discussion.tex` | **Ninguna** |
| **PEN-23** | **P3** | Resolver `src\TaskPane\deprecated\`: borrar los 8 `.R` duplicados y **rescatar `GR_EjemploBasico.Studio.R`**, que solo existe allí. COD-32, COD-55 | `src\TaskPane\deprecated\GR_DataLab_migrated\`, `src\libreria\R\` | **Ninguna** |
| **PEN-24** | **P3** | Citar o retirar las 8 entradas huérfanas del `.bib`. COD-49 | `src\docs\Paper\references.bib` | **Ninguna** |

## 13.2 POR MEJORAR

| ID | Prioridad | Qué | Rutas afectadas | Invariantes |
|---|---|---|---|---|
| **MEJ-01** | **P1** | **Activar avisos del compilador.** `/W3 /permissive- /sdl` global; arreglar la cola de avisos; después evaluar `/W4` y `/WX` por target. Retirar los `_SILENCE_*` que ya no apliquen. COD-14 | `src\CMakeLists.txt:12, 15-25` | **`INV-BLD-01/02` intactas** (no se quita ningún flag). `INV-TEST-01` sigue pasando: `build_verification_tests.cc` comprueba presencia, no exclusividad |
| **MEJ-02** | **P1** | **Dar runner a los 410 tests Python.** Añadir `pytest.ini` (o `pyproject.toml`) con `testpaths`, un `conftest.py` con el `sys.path` del servidor, y un job de CI que los ejecute. COD-22 | raíz de `src\`, `src\TaskPane\tests\` (18 ficheros), `src\tests\test_*.py` (3), `src\.github\workflows\build-and-test.yml` | **Ninguna.** Es el prerrequisito de MEJ-04 |
| **MEJ-03** | **P1** | **Tests para los diez subsistemas sin cobertura**, empezando por los dos de mayor riesgo: (a) `ribbon_connect.h` — test de tabla que verifique que cada `onAction`/`getPressed` de `ribbon_ui.xml` tiene entrada en `GetIDsOfNames` y valor en `DispIds`; (b) `ViewerManager` — ciclo de vida del hilo STA. COD-23 | `src\tests\` (nuevos), `src\Ribbon\ribbon_connect.h`, `src\Ribbon\ribbon_ui.xml`, `src\Common\ViewerManager.{h,cc}` | El test de (a) **convierte `INV-RIBBON-01` en ejecutable**, que hoy solo está documentada. Debe cumplir `INV-TEST-03` (sin Excel) |
| **MEJ-04** | **P2** | **Refactorizar el despacho del servidor HTTP a tabla de rutas** y partir el fichero por áreas (`ai`, `ontology`, `rag`, `charts`, `config`, `db`). Reduce `do_GET` de 400 líneas y `_handle_ai_chat_impl` de 461. COD-37 | `src\startup\neven_http_server.py` (4 901 líneas, 65 endpoints) | **Toca `INV-SB-01, 02, 03, 04, 05`.** Una tabla de rutas las **refuerza** si el rate limiter y la validación de `/api/query` se aplican en el despachador. **Condición dura: escribir primero tests que fijen las cinco** (MEJ-02 es prerrequisito). Sin esos tests, no acometer |
| **MEJ-05** | **P2** | **Extraer los 6 053 líneas de JS inline de `taskpane.html`** a ficheros `.js` por área funcional, cargados con `<script src=>`. COD-40 | `src\TaskPane\taskpane.html` (8 263 líneas, 10 bloques `<script>`) | **`INV-TF-04` se cumple**: sin bundler, sin transpilador, sin módulos ES; globales explícitos. `INV-TF-03`: copiar los nuevos `.js` con `[System.IO.File]::Copy()`. `INV-TF-01`: la extracción es la ocasión de eliminar el renderer de respaldo |
| **MEJ-06** | **P2** | **Unificar los renderers de resultados** en `buildSlotElement`: convertir `renderScriptResult` (`taskpane.js:1219`), `renderScriptResultRS` (`taskpane.html:5327`), el fallback de `taskpane.html:7243` y `_renderBackendResult` (`chart-gallery.js:1646`) en adaptadores que produzcan slots `{name,label,type,value,tier}` y deleguen. Eliminar los `typeof ... === 'function'`. COD-41 | `src\TaskPane\datalab.js:1528`, `taskpane.js:476, 1219`, `taskpane.html:5211, 5327, 7243`, `chart-gallery.js:1646` | **Cierra `INV-TF-01`** (hoy PARCIAL) |
| **MEJ-07** | **P2** | **Actualizar `coding-standards.md` a lo que el código hace**: métodos `PascalCase`, ficheros con el nombre de la clase, `snake_case` para funciones libres y locales, miembros `snake_case_`. Declarar expresamente la excepción `RJ_`/`RJ2XCL` por ABI y los `.cpp` de terceros. **No refactorizar 596 métodos.** COD-11 | `src\docs\sops\coding-standards.md` | **Ninguna** |
| **MEJ-08** | **P2** | **Hacer `MockExcelBridge` programable**: tabla `{xlfn → (código de retorno, XLOPER de salida)}` para poder probar `xlretAbort`, `xlretUncalced` y la conversión de vuelta. COD-24 | `src\Core\include\MockExcelBridge.h`, `src\tests\callback_behavior_tests.cc`, `src\tests\raii_xloper_tests.cc` | **Ninguna**; `INV-TEST-03` se mantiene (sigue sin Excel) |
| **MEJ-09** | **P2** | **Reporte estadístico con supuestos.** Añadir un `TipoOutput` "informe completo" que devuelva estimación + VIF + Breusch-Pagan + normalidad de residuos + Ljung-Box, y una columna `R4XCL_Avisos` en `TipoOutput=1` cuando un supuesto falle. Añadir `confint` y un tamaño de efecto estandarizado donde aplique. COD-30 | `src\libreria\R\R4XCL-RG-Lineal.R`, `-Binaria.R`, `-Poisson.R`, `-Tobit.R`, `-DatosPanel.R`, `-SeriesTiempo.R`, `-2SLS.R` + sus sidecars en `src\Install\functions` | **`INV-NX-03` y `INV-LR-03` intactas** (nuevo valor de `TipoOutput`, misma posición `a2`, mismo contrato `R4XCL_`). **Requiere actualizar `tipo_outputs[]` del sidecar → `INV-SJ-03` (id 0 reservado para ayuda) y `INV-SJ-02` (`function_name_xll` exacto)** |
| **MEJ-10** | **P2** | **Descomponer las cinco funciones de más de 180 líneas**, empezando por `RJ2XCL_Engine::Init()` (187) usando los separadores de comentario que ya la dividen. COD-08 | `src\Core\src\rj2xcl.cc:350`, `src\Core\src\basic_functions.cc:1601`, `src\ControlR\src\convert.cc`, `src\ControlJulia\src\julia_interface.cc:34, 266`, `src\NEVEN-SIM\src\sim_main.cc:280` | **`INV-CORE-02` se preserva**: la secuencia observable no cambia, solo se nombra cada paso |
| **MEJ-11** | **P3** | **Evaluar envolver la librería Julia en `module J4XCL*`** con `export` explícito, para dar frontera de namespace. COD-33 | `src\libreria\JULIA\*.jl` (9 ficheros) | **Toca `INV-CJ-01` e `INV-CJ-02`**: obliga a reconstruir `neven_julia.dll` (~1,04 GB) y a reejecutar el script de precompile de forma independiente antes de `create_sysimage()`. **No se propone sin esa condición escrita.** Prioridad baja por ese coste |
| **MEJ-12** | **P3** | **Extraer a `Common\` el bucle de host de motor** compartido por los tres `Control*` (98 líneas idénticas entre Julia y Python). COD-10 | `src\ControlJulia\src\control_julia.cc`, `src\ControlPython\src\control_python.cc`, `src\ControlR\src\controlr.cc`, `src\Common\` (nuevo) | **`INV-CJ-03` se refuerza** (un solo sitio garantiza el mismo protocolo). `INV-CMN-03` sin cambios |
| **MEJ-13** | **P3** | **Unificar observabilidad del servidor Python**: `logging` en lugar de los 15 `print(`, eliminar los 2 `except:` desnudos, y rotación de `neven.log` (hoy 120 MB). COD-38 | `src\startup\neven_http_server.py` | **Ninguna** |
| **MEJ-14** | **P3** | **Doxygen en los headers grandes**, prioritariamente `rj2xcl.h` (1 `@brief` para 28 miembros), `ribbon_connect.h`, `RuntimeLoader.h`, `GCMonitor.h`, `gdi_graphics_device.h`. COD-13 | `src\Core\include\rj2xcl.h`, `src\Ribbon\ribbon_connect.h`, `src\Common\RuntimeLoader.h`, `src\Common\GCMonitor.h`, `src\ControlR\include\gdi_graphics_device.h` | **Ninguna** |
| **MEJ-15** | **P3** | **Documentar la semántica por rama de `Parametro`** en `JO_Optimizar` (tasa de aprendizaje vs tolerancia) y, si se refactoriza, una función por algoritmo con un único despachador. COD-34 | `src\libreria\JULIA\J4XCL-OP-Optimizacion.jl:28-30, 32, 145` | **`INV-NX-03` intacta** |
| **MEJ-16** | **P3** | **Validación de precondiciones en la librería Julia**: dimensiones y tipos antes de operar, con error por el canal correcto en lugar de cadenas de texto mezcladas con los datos. COD-35 | los 9 `.jl` de `src\libreria\JULIA`, en particular `J4XCL-OP-Optimizacion.jl:191` | **Ninguna** |
| **MEJ-17** | **P3** | **Migrar `include_directories()` global a `target_include_directories()`** y homogeneizar el estilo con el que ya usa `src\Core`. COD-17, COD-18 | `src\CMakeLists.txt:27-29, 84`, `src\build.ps1:72` | **Ninguna** |
| **MEJ-18** | **P3** | **Unificar el encoding de `src\docs\sops\`**: quitar el BOM de `testing-guide.md` para igualarlo a los otros dos. COD-56 | `src\docs\sops\testing-guide.md` | **Ninguna** (`INV-INS-04` aplica a JSON desplegado, no a `.md`) |
| **MEJ-19** | **P3** | **Reemplazar los 6 `atoi()`** por `std::from_chars` o `strtol` con comprobación de error, sobre todo en el parseo de versión de R. COD-09 | `src\ControlR\src\controlr.cc:614`, `r_engine_loader.cc:174, 186`, `rinterface_win.cc:134`, `src\Ribbon\ribbon_connect.h:190, 692` | **Mejora el diagnóstico de `INV-CR-03`** |
| **MEJ-20** | **P3** | **Asignar IDs estables a la tabla de hallazgos de `INFORME_AUDITORIA.md`** y adoptar como norma el comentario en el código con ID + versión, que es lo que permitió verificar `CM-BAJ-004/005/014`. §12 | `src\docs\INFORME_AUDITORIA.md`, `src\docs\audit\` | **Ninguna** |

## 13.3 NUEVAS IDEAS

| ID | Prioridad | Qué | Rutas afectadas | Invariantes |
|---|---|---|---|---|
| **IDEA-01** | **P1** | **Test de invariantes de ontología.** Convertir las `INV-*` verificables mecánicamente en tests GTest/pytest: `INV-NX-01` (ASCII sin BOM del dispatcher), `INV-NX-02` (llaves), `INV-LR-02` (sin `library()` top-level), `INV-LR-04` (`attr` presente), `INV-SJ-01..05` (sidecars válidos, `id` único, `file` basename, `function_name_xll` existe), `INV-INS-04` (JSON sin BOM), `INV-RIBBON-01` (XML ↔ `GetIDsOfNames`). Hoy la ontología es prosa; esto la convierte en una barrera. `repo_hygiene_tests.cc` ya es el patrón a seguir | `src\tests\` (nuevo `ontology_invariants_tests.cc` + `test_ontology_invariants.py`), `src\docs\ontologia\neven-core\*.yaml` | **Ninguna**: solo verifica. Cumple `INV-TEST-03` (todo son ficheros, sin runtimes) |
| **IDEA-02** | **P1** | **Reparar el hook `validate-before-run.ps1`**, que hoy hace `Test-Path` sobre rutas `NEVEN\NEVEN\...` inexistentes y por tanto **aprueba sin validar nada**. Con las rutas corregidas y IDEA-01 detrás, se convierte en la puerta real que el steering dice que es | `.kiro\hooks\validate-before-run.ps1:3, 29, 41, 132` | **Ninguna**; restaura la aplicación práctica de `INV-RIBBON-01/02/03` y `INV-SR-01/02/05` |
| **IDEA-03** | **P2** | **Test de paridad repositorio ↔ producción.** Script que compare hashes de `src\libreria\R` vs `C:\NEVEN\functions`, `src\startup` vs `C:\NEVEN\startup` y los sidecars, y liste lo que está en producción sin origen en el repositorio (hoy: 18 `.py`, 2 `.jl` y 1 `.json` sin origen según `00-layout-real.md` §5). Solo lectura sobre `C:\NEVEN\` | nuevo en `src\scripts\`, lee `src\libreria\R`, `src\Install\functions`, `src\startup`, `C:\NEVEN\` | **Ninguna.** Vigila `INV-CMN-02` (integridad de scripts) sin modificar nada |
| **IDEA-04** | **P2** | **Tests de frontend sin build.** Un `src\TaskPane\tests\runner.html` que cargue los `.js` reales y ejecute asserts en el navegador, más `node --test` para la lógica pura. Cubriría los 30 000 líneas que hoy tienen 0 tests, empezando por `buildSlotElement` con cada tipo de slot | `src\TaskPane\tests\` (nuevo), `src\TaskPane\datalab.js`, `taskpane.js` | **`INV-TF-04` se respeta**: sin bundler, sin transpilador. Depende de MEJ-05 para el código inline |
| **IDEA-05** | **P2** | **Un solo generador de la cifra de tests.** Un script que lea `--gtest_list_tests` + el conteo de pytest y actualice `README.md`, el badge, `Aseguramiento_de_calidad.md` y el steering desde una única fuente. Elimina de raíz las cuatro cifras divergentes (COD-20) | `src\README.md:19, 150, 176`, `src\docs\Mantenimiento\Aseguramiento_de_calidad.md:7`, `.kiro\steering\neven-project-context.md`, nuevo en `src\scripts\` | **Ninguna** |
| **IDEA-06** | **P2** | **Umbral de tamaño de fichero y de función en el CI.** Falla el build si un `.cc`/`.py`/`.js` supera N líneas o una función supera M, con una lista de excepciones explícita y datada. Es la única forma de que `taskpane.html` y `neven_http_server.py` no vuelvan a crecer tras MEJ-04 y MEJ-05 | `src\.github\workflows\build-and-test.yml`, nuevo en `src\scripts\` | **Ninguna** |
| **IDEA-07** | **P2** | **Dependencias de frontend locales con `integrity`.** Vendorizar Plotly, D3, d3-sankey, Leaflet y KaTeX en `src\TaskPane\vendor\` y añadir `integrity` a lo que siga viniendo de CDN. Hace el TaskPane funcional sin red. COD-45 | `src\TaskPane\taskpane.html`, `src\TaskPane\vendor\` (nuevo), `src\Install\Install-NEVEN.ps1` | **`INV-TF-04` se respeta** (copiar ficheros no es empaquetar). Impacto de tamaño en el instalador a evaluar |
| **IDEA-08** | **P3** | **Comprobación de mitigaciones sobre el binario, no sobre el `CMakeLists`.** `build_verification_tests.cc` hoy lee el `CMakeLists.txt`; un test que inspeccione los flags del PE de `NEVEN64.xll` y `NEVENRibbon.dll` cerraría `INV-BLD-02` con evidencia del artefacto. El MCP `rea` (`binary_overview`, `inspect_binary_layout`, `inspect_pe_resources`) sirve para eso, y `inspect_pe_resources` además verificaría `IDR_XML2` de `INV-RIBBON-04` | `src\tests\build_verification_tests.cc`, `src\Build\Dist\` | **Fortalece `INV-BLD-02` e `INV-RIBBON-04`** sin cambiarlas. **Leer solo copias, nunca los binarios en uso por Excel** |
| **IDEA-09** | **P3** | **Cache-busting automático.** Generar el `?v=` de los `<script src=>` desde el hash o la fecha del fichero en el paso de empaquetado, en lugar de a mano con cuatro formatos distintos. COD-44 | `src\TaskPane\taskpane.html`, `src\Install\Build-Setup.ps1` / `Sync-Dist.ps1` | **`INV-TF-04` se respeta** (sustitución de texto en el instalador, no transpilación) |
| **IDEA-10** | **P3** | **Verificación de citas en el CI del paper.** Ejecutar `bib_lint.py` y `verify_citations.py` como parte de la validación del documento, para que un `mismatch` como COD-46 no llegue a camera-ready. Guardar el informe JSON junto al `.tex` | `src\docs\Paper\references.bib`, `src\.github\workflows\` (nuevo job) | **Ninguna** |
| **IDEA-11** | **P3** | **Pedagogía estadística en la salida.** Aprovechando la columna `R4XCL_Avisos` de MEJ-09, emitir un aviso accionable cuando un supuesto falle ("heterocedasticidad detectada: p = 0.003; use TipoOutput=7 para errores robustos"). Convierte el diagnóstico en enseñanza, que es la tesis del proyecto | `src\libreria\R\R4XCL-RG-*.R`, `src\TaskPane\datalab.js:1635` (`_renderPedagogyWarning` **ya existe**) | **`INV-TF-01` se respeta**: `_renderPedagogyWarning` y el tipo `warning_pedagogy` ya pasan por `buildSlotElement` |
| **IDEA-12** | **P3** | **Métrica de duplicación en el CI.** Un detector de bloques repetidos (jscpd o equivalente sin dependencias) que vigile las 98 líneas duplicadas entre `ControlJulia` y `ControlPython` y los renderers paralelos del TaskPane. Pone número a lo que hoy solo se descubre en auditoría | `src\.github\workflows\build-and-test.yml` | **Ninguna** |

---

## 14. Resumen de severidades

| Severidad | Nº | IDs |
|---|---:|---|
| **Crítica** | 0 | — |
| **Alta** | 9 | COD-01, COD-14, COD-19, COD-22, COD-23, COD-36, COD-37, COD-40, COD-46 |
| **Media** | 26 | COD-02, 05, 06, 07, 08, 10, 11, 15, 16, 24, 25, 27, 28, 29, 30, 31, 33, 34, 38, 39, 41, 42, 43, 45, 47, 48 |
| **Baja** | 15 | COD-03, 04, 09, 12, 13, 17, 18, 32, 35, 44, 49, 50, 53, 54, 55 |
| **Informativa** | 6 | COD-20, COD-21, COD-26, COD-51, COD-52, COD-56 |
| **Total** | **56** | |

**Candidatos para el plan de trabajo:** 24 PENDIENTES (7 en P1), 20 POR MEJORAR (3 en P1), 12 NUEVAS IDEAS
(2 en P1). **56 ítems**, todos con rutas concretas y con su relación con las invariantes declarada de forma
explícita.

**Ningún ítem propuesto viola una invariante `INV-*`.** Los tres que la rozan llevan la condición escrita:
MEJ-04 (toca `INV-SB-01..05`, condicionado a tests previos), MEJ-11 (toca `INV-CJ-01/02`, condicionado a
reconstruir la sysimage) y MEJ-09 (toca `INV-SJ-02/03`, requiere actualizar el sidecar). No se propone
cambiar ninguna invariante.











