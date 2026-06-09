# INFORME DE AUDITORÍA DE CÓDIGO — PROYECTO NEVEN

**Versión:** 1.0  
**Fecha:** 2026-01-XX  
**Auditor:** Análisis estático automatizado  
**Alcance:** Código fuente completo del proyecto NEVEN v2.0.0

---

## 1. Resumen Ejecutivo

### Puntuación de Salud: 6.0 / 10

El proyecto NEVEN presenta una base de código madura con buenas prácticas en manejo de strings y arquitectura modular, pero tiene vulnerabilidades críticas de seguridad en la capa Electron y en la sanitización de entradas para ejecución de procesos externos.

### Conteo por Severidad

| Severidad | Cantidad |
|-----------|----------|
| Crítica   | 8        |
| Alta      | 7        |
| Media     | 5        |
| Baja      | 14       |
| Informativa | 2      |
| **Total** | **36**   |

### Conteo por Categoría

| Categoría       | Hallazgos |
|-----------------|-----------|
| Seguridad       | 20        |
| Arquitectura    | 5         |
| Código Muerto   | 8         |
| Documentación   | 3         |
| **Total**       | **36**    |

### Fortalezas Identificadas: 18

---

## 2. Metodología

### 2.1 Técnicas de Análisis

- **Análisis estático de código fuente** — búsqueda de patrones inseguros mediante expresiones regulares y revisión manual de flujos de datos.
- **Análisis de dependencias** — verificación de versiones de paquetes npm contra CVEs conocidos.
- **Análisis de configuración** — revisión de CMakeLists.txt, workflows CI/CD, .gitignore.
- **Análisis de arquitectura** — mapeo de dependencias inter-módulo via `#include` y `target_link_libraries`.
- **Detección de código muerto** — cruce de definiciones vs. invocaciones en C++, R, Julia y TypeScript.
- **Evaluación de documentación** — verificación de cobertura, consistencia y actualización.

### 2.2 Alcance

| Dimensión | Directorios |
|-----------|-------------|
| C++ | Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Ribbon/, PB/ |
| Scripts | libreria/R/, libreria/JULIA/, startup/ |
| Electron/TypeScript | Console/src/, Console/main.js |
| Configuración | CMakeLists.txt, .github/workflows/, .gitignore, *.json |
| Documentación | docs/ |

### 2.3 Métricas Base

- **Total archivos:** 1,121
- **Total LOC:** 75,843
- **Archivos analizados:** 315
- **Distribución:** C++ 63.8%, TypeScript 10.2%, R 6.8%, Julia 3.1%, Python 2.1%, Otros 14%

### 2.4 Exclusiones

| Categoría | Directorio/Archivo | Justificación |
|-----------|--------------------|---------------|
| TERCEROS | Build/_deps/ | Dependencias descargadas (Protobuf, GTest) |
| TERCEROS | Common/json11/ | Librería JSON de Dropbox (MIT) |
| GENERADO | PB/variable.pb.cc/h | Generado por protoc |
| GENERADO | Console/generated/ | Generado por protoc |
| BINARIO | *.dll, *.exe, *.obj | Archivos compilados |
| TERCEROS | Include/, OfficeTypes/ | Headers SDK externos |

---

## 3. Hallazgos de Seguridad

### Severidad Crítica


#### [SEC-CRI-001] Inyección de comandos en RJ_Q via ruta de archivo de celda Excel

- **Ubicación:** Core/src/basic_functions.cc:387
- **Severidad:** Crítica
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** La función `RJ_Q` (expuesta como `=NEVEN.q()`) recibe una ruta de archivo `.qmd` directamente desde una celda de Excel y la concatena sin sanitización en un command line pasado a `CreateProcessA`. Un atacante puede inyectar comandos arbitrarios usando metacaracteres (`"`, `&`, `|`).
- **Recomendación:** Implementar sanitización de la ruta usando `ValidateInputSecurity()` de `QuartoService` o migrar a `QuartoService::Render()` que ya implementa validaciones parciales. Usar `lpApplicationName` en `CreateProcessA`.

---

#### [SEC-CRI-002] Inyección de comandos en ContentPipeline::ConvertWithPandoc

- **Ubicación:** Common/ContentPipeline.cc:376
- **Severidad:** Crítica
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** `ConvertWithPandoc` concatena `file_path` (proveniente de celda Excel via `RJ_View`) directamente en un command line para `CreateProcessA` sin ninguna validación de seguridad. Permite inyección de comandos OS.
- **Recomendación:** Agregar validación de caracteres peligrosos. Pasar `pandoc_path` como `lpApplicationName`. Implementar allowlist de caracteres válidos para rutas.

---

#### [SEC-CRI-003] Bypass de Sandbox via REPL Console

- **Ubicación:** Common/REPLManager.cc, Console/REPL.ts
- **Severidad:** Crítica
- **Categoría:** Seguridad > Bypass de Sandbox
- **Descripción:** La consola REPL permite ejecución directa de código R/Julia sin pasar por el `SandboxVerifier`. Un usuario con acceso a la consola puede ejecutar `system()`, `run()` y otras funciones bloqueadas en el flujo normal de celdas Excel.
- **Recomendación:** Aplicar `SandboxVerifier` también al flujo REPL, o documentar explícitamente que la consola es un entorno privilegiado con acceso completo.

---

#### [SEC-CRI-004] Bypass de Sandbox via AutoLoader

- **Ubicación:** Common/AutoLoader.cc
- **Severidad:** Crítica
- **Categoría:** Seguridad > Bypass de Sandbox
- **Descripción:** El `AutoLoader` carga y ejecuta archivos R/Julia del directorio de trabajo del usuario sin verificación de sandbox. Un archivo malicioso colocado en el directorio de scripts puede ejecutar código arbitrario al inicio.
- **Recomendación:** Aplicar verificación de sandbox a archivos cargados por AutoLoader, o implementar firma/hash de archivos confiables.

---

#### [SEC-CRI-005] Blocklist de Sandbox permite bypass via funciones no bloqueadas

- **Ubicación:** Common/SandboxVerifier.cc:82-153
- **Severidad:** Crítica
- **Categoría:** Seguridad > Bypass de Sandbox
- **Descripción:** El `SandboxVerifier` usa una blocklist que no cubre todas las funciones peligrosas. En R, funciones como `file.rename()`, `download.file()`, `readLines(pipe(...))` no están bloqueadas. En Julia, `ccall` directo y `unsafe_*` no están completamente cubiertos.
- **Recomendación:** Migrar de blocklist a allowlist para operaciones de I/O y ejecución de sistema. Implementar sandboxing a nivel de proceso (AppContainer en Windows).

---

#### [SEC-CRI-006] Sandbox desactivable via configuración sin protección

- **Ubicación:** Common/ConfigService.cc, neven-config.json
- **Severidad:** Crítica
- **Categoría:** Seguridad > Bypass de Sandbox
- **Descripción:** El sandbox puede desactivarse completamente editando `neven-config.json` (campo `sandbox.enabled`). El archivo de configuración no tiene protección de integridad ni permisos restrictivos.
- **Recomendación:** Implementar verificación de integridad del archivo de configuración. Requerir confirmación interactiva para desactivar sandbox. Registrar en log cuando se desactiva.

---

#### [SEC-CRI-007] Electron 1.8.2 severamente desactualizado — múltiples CVEs críticos

- **Ubicación:** Console/package.json (dependencia `"electron": "^1.8.2"`)
- **Severidad:** Crítica
- **Categoría:** Seguridad > Dependencias vulnerables
- **Descripción:** La versión de Electron 1.8.2 (publicada en 2018) tiene más de 50 CVEs conocidos incluyendo ejecución remota de código (RCE), bypass de sandbox de Chromium, y escalación de privilegios. La versión actual estable es 28+. Electron 1.x no recibe parches de seguridad desde 2019. Además, esta versión no soporta `contextIsolation` ni `sandbox` del renderer, dejando el proceso renderer con acceso completo a Node.js.
- **Recomendación:** Actualizar Electron a la última versión LTS (actualmente v28+). Esto requiere refactorización significativa del código del renderer para usar `contextBridge` y eliminar acceso directo a `remote`.

---

#### [SEC-CRI-008] nodeIntegration habilitado por defecto sin contextIsolation

- **Ubicación:** Console/main.js (BrowserWindow sin webPreferences)
- **Severidad:** Crítica
- **Categoría:** Seguridad > Configuración Electron
- **Descripción:** El `BrowserWindow` se crea sin especificar `webPreferences`, lo que en Electron 1.x significa `nodeIntegration: true` y `contextIsolation: false` por defecto. Esto permite que cualquier contenido cargado en el renderer (incluyendo contenido renderizado via `innerHTML`) ejecute código Node.js arbitrario, incluyendo acceso al filesystem y ejecución de procesos.
- **Recomendación:** Agregar `webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true }`. Migrar la comunicación renderer↔main a usar `contextBridge` + `ipcRenderer`.


### Severidad Alta

#### [SEC-ALT-001] XSS en REPL.ts — innerHTML con datos de usuario sin sanitizar

- **Ubicación:** Console/REPL.ts:45
- **Severidad:** Alta
- **Categoría:** Seguridad > XSS
- **Descripción:** La función `promptUser()` inserta mensajes directamente en el DOM usando `innerHTML += \`<div>${msg}</div>\``. El parámetro `msg` incluye la salida de ejecución de código R/Julia y el eco del input del usuario. Con `nodeIntegration: true`, un XSS aquí permite ejecución de código Node.js (RCE completo).
- **Recomendación:** Usar `textContent` o `createTextNode()` en lugar de `innerHTML`. Si se requiere formato HTML, sanitizar con una librería como DOMPurify.

---

#### [SEC-ALT-002] XSS en alert.ts — innerHTML con contenido de mensajes

- **Ubicación:** Console/src/ui/alert.ts:82,115,121
- **Severidad:** Alta
- **Categoría:** Seguridad > XSS
- **Descripción:** `AlertManager` usa `innerHTML` para renderizar `spec.message` y botones. Si el contenido del mensaje proviene de datos externos (respuestas de pipe, errores de R/Julia), puede inyectar HTML/JS arbitrario.
- **Recomendación:** Sanitizar contenido antes de insertar via innerHTML, o usar APIs DOM seguras.

---

#### [SEC-ALT-003] XSS en dialog.ts — innerHTML con body de diálogos

- **Ubicación:** Console/src/ui/dialog.ts:121,123,130
- **Severidad:** Alta
- **Categoría:** Seguridad > XSS
- **Descripción:** `DialogManager` acepta strings como `body` y `status` y los inserta directamente via `innerHTML`. Si estos valores provienen de respuestas de los motores R/Julia, constituyen un vector XSS.
- **Recomendación:** Validar y sanitizar contenido HTML antes de inserción. Preferir `textContent` para texto plano.

---

#### [SEC-ALT-004] sscanf sin verificación de retorno en ControlPython

- **Ubicación:** ControlPython/src/python_interface.cc:47
- **Severidad:** Alta
- **Categoría:** Seguridad > Strings sin verificación
- **Descripción:** Se usa `sscanf` para parsear la versión de Python sin verificar el valor de retorno. Si `Py_GetVersion()` retorna un formato inesperado, los valores quedan sin inicializar correctamente.
- **Recomendación:** Verificar que `sscanf` retorna 3 antes de usar los valores parseados.

---

#### [SEC-ALT-005] Sanitización incompleta en QuartoService::ValidateInputSecurity

- **Ubicación:** Common/QuartoService.cc:36-56
- **Severidad:** Alta
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** `ValidateInputSecurity()` bloquea `|`, `&`, `;`, `` ` ``, `<`, `>` pero no bloquea comillas dobles (`"`), caracteres de nueva línea (`\n`, `\r`), ni expansión de variables Windows (`%VAR%`).
- **Recomendación:** Agregar `"`, `\n`, `\r`, `%` a caracteres bloqueados. Considerar allowlist en lugar de blocklist.

---

#### [SEC-ALT-006] XSS en editor.ts — innerHTML con contenido Markdown renderizado

- **Ubicación:** Console/src/editor/editor.ts:688,1138
- **Severidad:** Alta
- **Categoría:** Seguridad > XSS
- **Descripción:** El editor renderiza contenido Markdown usando `MD.render()` y lo inserta via `innerHTML`. Si el contenido Markdown proviene de archivos del usuario, puede contener HTML malicioso que se ejecutaría con privilegios Node.js.
- **Recomendación:** Configurar markdown-it con `html: false` para deshabilitar HTML embebido, o sanitizar la salida antes de inserción.

---

#### [SEC-ALT-007] Ausencia de flags de seguridad MSVC en compilación

- **Ubicación:** CMakeLists.txt (raíz), Core/CMakeLists.txt, Common/CMakeLists.txt
- **Severidad:** Alta
- **Categoría:** Seguridad > Configuración de compilación
- **Descripción:** No se especifican flags de seguridad de compilación MSVC: `/GS` (buffer security check), `/DYNAMICBASE` (ASLR), `/NXCOMPAT` (DEP), `/guard:cf` (Control Flow Guard). Aunque MSVC habilita `/GS` y `/DYNAMICBASE` por defecto en Release, `/guard:cf` no está habilitado por defecto y proporciona protección adicional contra ataques de control de flujo.
- **Recomendación:** Agregar explícitamente en el CMakeLists.txt raíz:
  ```cmake
  if(MSVC)
    add_compile_options(/GS /guard:cf)
    add_link_options(/DYNAMICBASE /NXCOMPAT /guard:cf)
  endif()
  ```


### Severidad Media

#### [SEC-MED-001] Datos de configuración JSON pasan a CreateProcessA sin validación

- **Ubicación:** Core/src/language_service.cc:350,753
- **Severidad:** Media
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** `command_arguments_` leído de `neven-config.json` se concatena en command line para `CreateProcessA`. Si un atacante modifica el archivo de configuración, puede inyectar comandos. Riesgo mitigado porque requiere acceso local.
- **Recomendación:** Validar que `command_arguments_` solo contiene flags esperados. Verificar integridad del archivo de configuración.

---

#### [SEC-MED-002] .gitignore insuficiente — no excluye archivos sensibles

- **Ubicación:** .gitignore (raíz del proyecto)
- **Severidad:** Media
- **Categoría:** Seguridad > Configuración
- **Descripción:** El `.gitignore` raíz solo excluye `BERTModule_*.gz`, `notes.md` y `yarn-error.log`. No excluye explícitamente: `Build/`, `node_modules/`, `.env`, `*.pdb`, `neven-config.json` (que puede contener API keys), archivos de crash dump, ni claves privadas. Aunque existen `.gitignore` locales en subdirectorios (Console/, ControlR/, ControlJulia/), la ausencia de exclusiones globales es un riesgo.
- **Recomendación:** Agregar al `.gitignore` raíz: `Build/`, `node_modules/`, `*.pdb`, `*.env`, `*.key`, `*.pem`, `neven-config.json`, `crashes/`.

---

#### [SEC-MED-003] GitHub Actions workflow sin permisos mínimos explícitos

- **Ubicación:** .github/workflows/build-and-test.yml
- **Severidad:** Media
- **Categoría:** Seguridad > CI/CD
- **Descripción:** El workflow no especifica `permissions:` a nivel de job ni de workflow, usando los permisos por defecto del repositorio (que pueden ser amplios). Las actions usadas (`actions/checkout@v4`, `microsoft/setup-msbuild@v2`, `r-lib/actions/setup-r@v2`, `actions/upload-artifact@v4`) usan tags versionados (buena práctica) pero no SHA pinning.
- **Recomendación:** Agregar `permissions: { contents: read }` al workflow. Considerar SHA pinning para actions críticas.

---

#### [SEC-MED-004] Dependencias npm con vulnerabilidades conocidas

- **Ubicación:** Console/package.json
- **Severidad:** Media
- **Categoría:** Seguridad > Dependencias vulnerables
- **Descripción:** Múltiples dependencias están severamente desactualizadas (2017-2018): `rxjs@^5.5.6`, `xterm@^3.2.0`, `monaco-editor@^0.10.1`, `markdown-it@^8.4.0`, `chokidar@^2.0.1`, `typescript@^2.7.2`. Estas versiones tienen vulnerabilidades conocidas de severidad variable (prototype pollution en chokidar, ReDoS en markdown-it).
- **Recomendación:** Actualizar todas las dependencias a versiones actuales como parte de la migración de Electron.

---

#### [SEC-MED-005] XSS en language_interface_r.ts — innerHTML con descripción de paquetes

- **Ubicación:** Console/src/shell/language_interface_r.ts:331
- **Severidad:** Media
- **Categoría:** Seguridad > XSS
- **Descripción:** La descripción de paquetes R se inserta via `innerHTML`. Las descripciones provienen del motor R y podrían contener HTML si un paquete malicioso incluye HTML en su campo DESCRIPTION.
- **Recomendación:** Usar `textContent` para descripciones de paquetes.

---

### Severidad Baja

#### [SEC-BAJ-001] Rutas absolutas hardcodeadas con nombre legacy "RJ2XCL"

- **Ubicación:** Common/CrashHandler.cc:249, Common/ContentPipeline.cc:49,199
- **Severidad:** Baja
- **Categoría:** Seguridad > Rutas sensibles
- **Descripción:** Tres ubicaciones usan `C:\RJ2XCL\` (nombre legacy) para crash dumps y datos temporales. Revelan estructura interna y no son configurables.
- **Recomendación:** Migrar a `C:\NEVEN\` o usar variable de entorno `NEVEN_HOME`.

---

#### [SEC-INF-001] Campo apiKey en neven-config.json — diseño correcto

- **Ubicación:** Install/neven-config.json:43
- **Severidad:** Informativa
- **Categoría:** Seguridad > Credenciales
- **Descripción:** El campo `apiKey` está vacío por defecto. Cuando el usuario lo configura, queda en texto plano. Diseño estándar para herramientas de desarrollo locales.
- **Recomendación:** Documentar que el archivo puede contener API keys y no debe compartirse.

---

#### [SEC-INF-002] electron-reload habilitado en producción

- **Ubicación:** Console/main.js:30
- **Severidad:** Informativa
- **Categoría:** Seguridad > Configuración Electron
- **Descripción:** `require('electron-reload')` está activo sin condicional de entorno. En producción, esto monitorea cambios en el directorio `build/` y recarga la ventana automáticamente, lo cual es innecesario y podría ser explotado si un atacante puede escribir archivos en ese directorio.
- **Recomendación:** Condicionar a `process.env.NODE_ENV === 'development'`.

---

## 4. Hallazgos de Arquitectura


#### [ARQ-MED-001] Módulo Common tiene responsabilidades excesivas (violación SRP)

- **Ubicación:** Common/ (44 archivos .cc/.h)
- **Severidad:** Media
- **Categoría:** Arquitectura > Cohesión
- **Descripción:** El módulo `Common` contiene 44 archivos con responsabilidades muy diversas: IPC (pipe.cc), seguridad (SandboxVerifier, SecurityService), configuración (ConfigService), UI (ViewerManager, WindowManager), logging (LogService), notebooks (NotebookExporter, NotebookLibrary), REPL (REPLManager, REPLBridge), startup (NevenInitOrchestrator, NevenBackgroundConnector), y más. Esto viola el Principio de Responsabilidad Única y dificulta la comprensión y mantenimiento.
- **Recomendación:** Dividir Common en sub-módulos: `Common/IPC/`, `Common/Security/`, `Common/Config/`, `Common/Viewers/`, `Common/Startup/`.

---

#### [ARQ-MED-002] Acoplamiento bidireccional Core ↔ Common

- **Ubicación:** Core/CMakeLists.txt, Common/CMakeLists.txt
- **Severidad:** Media
- **Categoría:** Arquitectura > Dependencias circulares
- **Descripción:** Core depende de Common (`target_link_libraries(NEVEN_Core PRIVATE Common)`), pero Common incluye headers de Core (`${CMAKE_SOURCE_DIR}/Core/include`). Esto crea una dependencia circular a nivel de headers que dificulta la compilación independiente y el testing unitario de Common.
- **Recomendación:** Extraer las interfaces compartidas a un módulo `Interfaces/` que ambos puedan incluir sin dependencia circular.

---

#### [ARQ-BAJ-001] Grafo de dependencias entre módulos

- **Ubicación:** CMakeLists.txt (todos)
- **Severidad:** Baja (informativo)
- **Categoría:** Arquitectura > Dependencias
- **Descripción:** Grafo de dependencias identificado:
  ```
  NEVEN_Core → Common, PB, libprotobuf, WebView2
  Common → PB, libprotobuf, shlwapi, bcrypt, winhttp
  ControlR → Common, PB, libprotobuf (+ R SDK)
  ControlJulia → Common, PB, libprotobuf (+ Julia SDK)
  ControlPython → Common, PB, libprotobuf (+ Python SDK)
  NEVENRibbon → (standalone COM DLL)
  ```
  El diseño es razonablemente modular con PB como capa de serialización compartida.
- **Recomendación:** Documentar el grafo de dependencias en docs/Arquitectura/.

---

#### [ARQ-BAJ-002] Escalabilidad IPC — diseño extensible para nuevos lenguajes

- **Ubicación:** Core/src/language_service.cc, Common/pipe.cc, PB/variable.proto
- **Severidad:** Baja (hallazgo positivo)
- **Categoría:** Arquitectura > Escalabilidad
- **Descripción:** El patrón Named_Pipe + Protobuf está bien abstraído. Agregar un nuevo lenguaje requiere: (1) crear un nuevo `ControlX.exe` que implemente el protocolo Protobuf, (2) agregar una entrada en `neven-config.json`, (3) opcionalmente agregar un `LanguageInterface` en Console. No requiere cambios estructurales en Core ni Common. La adición de Python (ControlPython) demuestra esta extensibilidad.
- **Recomendación:** Ninguna — diseño correcto.

---

#### [ARQ-BAJ-003] Testabilidad buena — MockExcelBridge y abstracción de dependencias

- **Ubicación:** tests/, Core/include/MockExcelBridge.h
- **Severidad:** Baja (hallazgo positivo)
- **Categoría:** Arquitectura > Testabilidad
- **Descripción:** El proyecto tiene 228 tests con GTest v1.14.0. Las dependencias externas (Excel, R, Julia) están abstraídas detrás de interfaces que permiten testing sin estos componentes. `MockExcelBridge` simula la API de Excel para tests unitarios. El CI ejecuta tests sin R ni Julia (`SKIP_LANGUAGE_TARGETS=ON`).
- **Recomendación:** Ninguna — buena práctica de testabilidad.

---

## 5. Hallazgos de Código Muerto

#### [CDM-BAJ-001] ControlPython — módulo completo deprecado pero compilable

- **Ubicación:** ControlPython/ (CMakeLists.txt, src/python_interface.cc, src/control_python.cc)
- **Severidad:** Baja
- **Categoría:** Código Muerto > C++ residual
- **Descripción:** El módulo ControlPython está marcado como deprecado (OFF por defecto via `NEVEN_ENABLE_PYTHON`), pero todo su código fuente permanece en el repositorio y es compilable. Incluye ~500 LOC de interfaz Python que ya no se usa en producción.
- **Recomendación:** Mover a una rama `archive/python` o eliminar del repositorio principal. Mantener solo si hay planes de reactivación.

---

#### [CDM-BAJ-002] Scripts Python residuales en libreria/PYTHON/ y startup/

- **Ubicación:** libreria/PYTHON/quarto_functions.py, libreria/PYTHON/ai_functions.py, startup/startup.py
- **Severidad:** Baja
- **Categoría:** Código Muerto > Scripts residuales
- **Descripción:** Existen 3 archivos Python funcionales que corresponden a la integración deprecada. `startup.py` contiene funciones de IA que podrían estar activas si Python se habilita, pero el módulo está OFF por defecto.
- **Recomendación:** Documentar claramente el estado de estos archivos. Si Python permanece deprecado, archivar.

---

#### [CDM-BAJ-003] Console/src/shell/language_interface_julia-0.7.ts — archivo legacy

- **Ubicación:** Console/src/shell/language_interface_julia-0.7.ts
- **Severidad:** Baja
- **Categoría:** Código Muerto > TypeScript no alcanzable
- **Descripción:** Este archivo implementa una interfaz para Julia 0.7 que está comentada en el import de `renderer.ts` (`//import { Julia07Interface }`). Julia actual es 1.12.6, haciendo este archivo completamente obsoleto.
- **Recomendación:** Eliminar el archivo y la referencia comentada.

---

#### [CDM-BAJ-004] Console — proyecto Electron completo posiblemente abandonado

- **Ubicación:** Console/ (todo el directorio)
- **Severidad:** Baja
- **Categoría:** Código Muerto > Módulo abandonado
- **Descripción:** El proyecto Console (REPL Electron) usa tecnologías de 2017-2018 (Electron 1.8.2, TypeScript 2.7, rxjs 5). El steering file del proyecto lo marca como "pendiente". El proyecto principal ahora usa WebView2 para visualización. Es probable que Console haya sido reemplazado funcionalmente por el sistema WebView2 + REPL integrado.
- **Recomendación:** Evaluar si Console sigue siendo necesario. Si no, archivar o eliminar. Si sí, requiere actualización completa de stack.

---

#### [CDM-BAJ-005] Funciones R con posible duplicación — .neven_webview_dir()

- **Ubicación:** libreria/R/R4XCL-GR-QuickPlot.R:6, R4XCL-GR-PlotlyView.R:6, R4XCL-AD-Pivot.R:6, R4XCL-AD-Map.R:6, R4XCL-AD-Esquisse.R:7, R4XCL-AD-Dashboard.R:7, R4XCL-AD-D3.R:7
- **Severidad:** Baja
- **Categoría:** Código Muerto > Duplicación
- **Descripción:** La función helper `.neven_webview_dir()` está definida idénticamente en 7 archivos R diferentes. Cada archivo define su propia copia local de la misma función.
- **Recomendación:** Extraer a un archivo compartido (ej: `R4XCL-0-Interno-1.R`) y referenciar desde los demás.

---

#### [CDM-BAJ-006] Código comentado en renderer.ts y otros archivos TypeScript

- **Ubicación:** Console/src/renderer.ts (múltiples bloques comentados)
- **Severidad:** Baja
- **Categoría:** Código Muerto > Código comentado
- **Descripción:** `renderer.ts` contiene múltiples bloques de código comentado con `//` incluyendo imports no usados (`Julia07Interface`), funciones deshabilitadas, y un bloque `window["Pause"]` comentado al final. Otros archivos TypeScript tienen patrones similares.
- **Recomendación:** Eliminar código comentado. Usar control de versiones para historial.

---

#### [CDM-BAJ-007] startup/__pycache__/ — artefactos de compilación Python en repositorio

- **Ubicación:** startup/__pycache__/
- **Severidad:** Baja
- **Categoría:** Código Muerto > Artefactos
- **Descripción:** El directorio `__pycache__` contiene bytecode compilado de Python que no debería estar en el repositorio.
- **Recomendación:** Agregar `__pycache__/` al `.gitignore` y eliminar del repositorio.

---

#### [CDM-BAJ-008] Funciones internas R duplicadas entre startup.r y libreria/R/R4XCL-0-Interno-3.R

- **Ubicación:** startup/startup.r, libreria/R/R4XCL-0-Interno-3.R
- **Severidad:** Baja
- **Categoría:** Código Muerto > Duplicación
- **Descripción:** Las funciones `Extraer_outputs`, `.neven_procesar_valor` y `.neven_consolidar` están definidas tanto en `startup.r` como en `R4XCL-0-Interno-3.R` con implementaciones similares. Esto crea confusión sobre cuál versión se usa en producción.
- **Recomendación:** Mantener una sola definición canónica (preferiblemente en startup.r que se carga siempre) y eliminar la duplicada.

---

## 6. Hallazgos de Documentación

#### [DOC-BAJ-001] Inconsistencia terminológica — RJ2XCL vs NEVEN vs BERT

- **Ubicación:** docs/ (múltiples archivos), Console/main.js, código fuente
- **Severidad:** Baja
- **Categoría:** Documentación > Consistencia
- **Descripción:** El proyecto usa tres nombres intercambiablemente: `NEVEN` (nombre actual), `RJ2XCL` (nombre interno C++), y `BERT` (nombre del proyecto original del que se derivó). En Console/main.js los comentarios dicen "BERT", las variables de entorno usan `RJ2XCL_*` y `BERT_*`, y la documentación usa `NEVEN`. Esto dificulta la comprensión para nuevos contribuidores.
- **Recomendación:** Documentar explícitamente la relación entre los tres nombres. Migrar gradualmente variables de entorno a `NEVEN_*` (manteniendo fallbacks).

---

#### [DOC-BAJ-002] Documentación de módulos — cobertura desigual

- **Ubicación:** docs/
- **Severidad:** Baja
- **Categoría:** Documentación > Cobertura
- **Descripción:** La documentación es extensa (14+ documentos en docs/Contexto/, 4 en docs/Arquitectura/, 4 en docs/Mantenimiento/) pero la cobertura es desigual: Core y Common tienen buena documentación, pero ControlR, ControlJulia, Console y Ribbon tienen documentación mínima (solo README.md básicos). Las funciones XLL exportadas no tienen documentación de API unificada.
- **Recomendación:** Crear documentación de API para funciones XLL exportadas. Expandir README de cada módulo con arquitectura interna.

---

#### [DOC-MED-001] Comentarios Doxygen ausentes en mayoría de headers públicos

- **Ubicación:** Common/*.h (mayoría), Core/include/*.h
- **Severidad:** Media
- **Categoría:** Documentación > Comentarios de código
- **Descripción:** De los ~42 headers en Common/, solo los archivos más recientes (NevenProgressiveRegisterExport.h, NevenStartupTypes.h) tienen documentación Doxygen completa con `@brief`, `@param`, `@return`. Los headers más antiguos (pipe.h, ConfigService.h, ViewerManager.h) tienen solo comentarios de licencia sin documentación de API. Los headers de message_utilities.h son una excepción positiva con Doxygen parcial.
- **Recomendación:** Agregar documentación Doxygen a todas las funciones públicas de headers. Priorizar los módulos más usados (pipe.h, ConfigService.h, message_utilities.h).

---

## 7. Fortalezas Identificadas

### Seguridad

| ID | Fortaleza | Ubicación |
|----|-----------|-----------|
| FOR-STR-001 | Uso consistente de funciones seguras de strings (sin strcpy/sprintf/strcat/gets) | Todo el código base |
| FOR-STR-002 | snprintf con sizeof consistente en todos los usos | Common/ContentPipeline, NotebookExporter, json11 |
| FOR-STR-003 | sprintf_s como estándar para formateo en buffers | ControlR, ControlJulia, ControlPython |
| FOR-STR-004 | std::string como tipo predominante (>95% de operaciones) | Todo el código base |
| FOR-CMD-001 | Zombie cleanup usa comandos hardcodeados sin datos externos | Core/src/rj2xcl.cc |
| FOR-CMD-002 | Ribbon ShellExecute usa rutas completamente hardcodeadas | Ribbon/ribbon_connect.h |
| FOR-CMD-003 | PlutoManager construye comando sin datos de usuario directos | Common/PlutoManager.cc |
| FOR-CMD-004 | QuartoService implementa validación de seguridad (parcial) | Common/QuartoService.cc |
| FOR-CMD-005 | No se usa system(), _popen ni WinExec en código propio | Todo el código base |
| FOR-CMD-006 | SandboxVerifier bloquea system/shell en código de usuario | Common/SandboxVerifier.cc |
| FOR-CRE-001 | Ausencia total de credenciales hardcodeadas | Todo el código base |
| FOR-CRE-002 | API key vacía por defecto en plantilla de configuración | Install/neven-config.json |
| FOR-CRE-003 | Enmascaramiento de API key en logs | startup/startup.py |
| FOR-CRE-004 | Rutas resueltas via variables de entorno con fallback | startup/*.py, *.jl, *.r |
| FOR-CRE-005 | SandboxVerifier bloquea acceso a env vars desde scripts | Common/SandboxVerifier.cc |

### Arquitectura

| ID | Fortaleza | Ubicación |
|----|-----------|-----------|
| FOR-ARQ-001 | Diseño IPC extensible (Named Pipes + Protobuf) | Core, Common, ControlR, ControlJulia |
| FOR-ARQ-002 | Testabilidad con MockExcelBridge (228 tests sin Excel/R/Julia) | tests/ |
| FOR-ARQ-003 | CI/CD funcional con GitHub Actions y matrix de configuración | .github/workflows/ |

---

## 8. Recomendaciones Priorizadas


### Prioridad 1 — Impacto Crítico / Esfuerzo Variable

| # | Recomendación | Impacto | Esfuerzo | Resuelve |
|---|---------------|---------|----------|----------|
| 1 | **Sanitizar entradas en CreateProcessA** — Implementar validación de caracteres peligrosos en todas las funciones que construyen command lines con datos de usuario (RJ_Q, ConvertWithPandoc). Usar `lpApplicationName` para separar ejecutable de argumentos. | Elimina 2 RCE críticos | Bajo (1-2 días) | SEC-CRI-001, SEC-CRI-002, SEC-ALT-005 |
| 2 | **Actualizar Electron o eliminar Console** — Si Console sigue siendo necesario, actualizar a Electron 28+ con contextIsolation, sandbox, y contextBridge. Si no, eliminar del repositorio. | Elimina 2 críticos + 5 altos | Alto (2-4 semanas) | SEC-CRI-007, SEC-CRI-008, SEC-ALT-001 a 003, SEC-ALT-006, SEC-MED-005 |
| 3 | **Fortalecer Sandbox** — Migrar de blocklist a allowlist. Aplicar sandbox al flujo REPL. Verificar archivos del AutoLoader. Proteger configuración de sandbox. | Elimina 4 críticos | Medio (1-2 semanas) | SEC-CRI-003, SEC-CRI-004, SEC-CRI-005, SEC-CRI-006 |

### Prioridad 2 — Impacto Alto / Esfuerzo Bajo-Medio

| # | Recomendación | Impacto | Esfuerzo | Resuelve |
|---|---------------|---------|----------|----------|
| 4 | **Agregar flags de seguridad MSVC** — Agregar `/GS`, `/guard:cf`, `/DYNAMICBASE`, `/NXCOMPAT` explícitamente en CMakeLists.txt | Hardening de binarios | Bajo (1 hora) | SEC-ALT-007 |
| 5 | **Mejorar .gitignore** — Agregar exclusiones globales para Build/, node_modules/, *.pdb, __pycache__/, neven-config.json | Previene exposición accidental | Bajo (30 min) | SEC-MED-002, CDM-BAJ-007 |
| 6 | **Agregar permisos mínimos a GitHub Actions** — Especificar `permissions: { contents: read }` | Reduce superficie de ataque CI | Bajo (15 min) | SEC-MED-003 |

### Prioridad 3 — Impacto Medio / Mejora Continua

| # | Recomendación | Impacto | Esfuerzo | Resuelve |
|---|---------------|---------|----------|----------|
| 7 | **Refactorizar módulo Common** — Dividir en sub-módulos por responsabilidad | Mejora mantenibilidad | Medio (1 semana) | ARQ-MED-001 |
| 8 | **Eliminar código muerto** — Archivar ControlPython, eliminar julia-0.7.ts, consolidar funciones R duplicadas | Reduce complejidad | Bajo (2-3 días) | CDM-BAJ-001 a 008 |
| 9 | **Agregar documentación Doxygen** — Documentar funciones públicas de headers principales | Mejora mantenibilidad | Medio (1 semana) | DOC-MED-001, DOC-BAJ-002 |
| 10 | **Unificar nomenclatura** — Documentar relación NEVEN/RJ2XCL/BERT, migrar variables de entorno | Reduce confusión | Bajo (2-3 días) | DOC-BAJ-001, SEC-BAJ-001 |

---

## 9. Anexos

### Anexo A — Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| Total archivos descubiertos | 1,121 |
| Archivos analizados | 315 |
| Archivos excluidos | 806 |
| Total LOC | 75,843 |
| LOC C++ | 48,388 (63.8%) |
| LOC TypeScript | 7,736 (10.2%) |
| LOC R | 5,157 (6.8%) |
| LOC Julia | 2,351 (3.1%) |
| LOC Python | 1,592 (2.1%) |
| LOC Otros | 10,619 (14.0%) |
| Tests unitarios | 228 |
| Módulos principales | 7 (Core, Common, ControlR, ControlJulia, ControlPython, Console, Ribbon) |

### Anexo B — Distribución de Hallazgos por Módulo

| Módulo | Crítica | Alta | Media | Baja | Total |
|--------|---------|------|-------|------|-------|
| Core | 1 | 1 | 1 | 0 | 3 |
| Common | 2 | 2 | 0 | 1 | 5 |
| Console | 2 | 4 | 2 | 3 | 11 |
| ControlPython | 0 | 1 | 0 | 1 | 2 |
| Configuración | 1 | 1 | 2 | 0 | 4 |
| Sandbox | 3 | 0 | 0 | 0 | 3 |
| libreria/R | 0 | 0 | 0 | 2 | 2 |
| Documentación | 0 | 0 | 1 | 2 | 3 |
| Arquitectura | 0 | 0 | 2 | 1 | 3 |

### Anexo C — Herramientas y Versiones

| Herramienta | Versión | Uso |
|-------------|---------|-----|
| CMake | 3.15+ | Build system |
| MSVC | VS 2022 | Compilador C++ |
| Protocol Buffers | v21.12 | Serialización IPC |
| Google Test | v1.14.0 | Testing unitario |
| WebView2 SDK | 1.0.2903.40 | Visor HTML embebido |
| Electron | 1.8.2 ⚠️ | Console REPL (desactualizado) |
| TypeScript | 2.7.2 ⚠️ | Console (desactualizado) |
| R | 4.4.1 | Motor estadístico |
| Julia | 1.12.6 | Motor computacional |

### Anexo D — Archivos Clave Analizados

```
Core/src/basic_functions.cc          — Funciones XLL exportadas (RJ_Q, RJ_View)
Core/src/language_service.cc         — Gestión de procesos hijos
Core/src/rj2xcl.cc                   — Entry point del XLL
Common/ContentPipeline.cc            — Conversión de documentos (Pandoc)
Common/QuartoService.cc              — Renderizado Quarto
Common/SandboxVerifier.cc            — Verificación de sandbox
Common/AutoLoader.cc                 — Carga automática de scripts
Common/ConfigService.cc              — Gestión de configuración
Common/pipe.cc                       — Comunicación IPC
Console/main.js                      — Entry point Electron
Console/src/renderer.ts              — Renderer principal
Console/REPL.ts                      — Controlador REPL
Console/package.json                 — Dependencias npm
CMakeLists.txt                       — Build system raíz
.github/workflows/build-and-test.yml — CI/CD
.gitignore                           — Exclusiones de repositorio
startup/startup.r                    — Script de inicio R
startup/startup.jl                   — Script de inicio Julia
libreria/R/*.R                       — Librería R (33 archivos)
libreria/JULIA/*.jl                  — Librería Julia (5 archivos)
```

---

*Fin del informe de auditoría.*
