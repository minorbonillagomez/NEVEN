# Auditoría de Seguridad C++ — NEVEN

**Fecha:** 2026-01-XX  
**Alcance:** Core/, Common/, ControlR/, ControlJulia/, ControlPython/  
**Archivos analizados:** ~120 archivos (.cc, .h, .cpp)

---

## Resumen Ejecutivo

| Severidad | Hallazgos |
|-----------|-----------|
| **Crítica** | 4 |
| **Alta** | 5 |
| **Media** | 4 |
| **Baja** | 2 |
| **Total** | 15 |

---

## Hallazgos de Seguridad

---

### [SEC-CRI-001] Secreto de Pluto hardcodeado y logging de credenciales
- **Archivo:** Common/PlutoManager.cc:56
- **Severidad:** Crítica
- **Descripción:** El secreto de autenticación de Pluto está hardcodeado como `"rj2xcl"` y además se loguea en texto plano. Adicionalmente, `require_secret_for_access=false` desactiva completamente la autenticación de Pluto, permitiendo acceso no autorizado al servidor de notebooks.
- **Código:**
```cpp
// Fixed secret for Pluto — allows us to construct URLs deterministically
pluto_secret_ = "rj2xcl";

RJ2XCL_LOG_INFO("PlutoManager initialized (port %d, secret=%s)", port_, pluto_secret_.c_str());

// En BuildPlutoCommand():
<< "require_secret_for_access=false)\"";
```
- **Recomendación:** Generar un secreto aleatorio por sesión (UUID o token criptográfico), no loguearlo en texto plano, y habilitar `require_secret_for_access=true`. Almacenar el secreto en memoria protegida y pasarlo al viewer de forma segura.

---

### [SEC-CRI-002] Sandbox basado en patrones — bypass documentado
- **Archivo:** Common/SandboxVerifier.cc:22-24
- **Severidad:** Crítica
- **Descripción:** El propio código documenta que el sandbox es bypasseable: *"Pattern-based blocking can be bypassed by sufficiently motivated attackers."* El sandbox usa string matching en lowercase, lo cual puede ser evadido mediante encoding Unicode, concatenación de strings en el lenguaje destino, o uso de APIs alternativas no listadas. No hay sandboxing a nivel de OS (AppContainer, restricted tokens, Job Objects con restricciones).
- **Código:**
```cpp
/**
 * LIMITATIONS:
 * Pattern-based blocking can be bypassed by sufficiently motivated attackers.
 * This layer raises the bar against casual/accidental misuse and malicious
 * workbooks, but is NOT a full sandbox. For production hardening, consider
 * OS-level sandboxing (AppContainer, restricted tokens).
 */
```
- **Recomendación:** Implementar sandboxing a nivel de OS: usar AppContainer o Restricted Tokens para los procesos hijo (ControlR.exe, ControlJulia.exe). Configurar Job Objects con restricciones de red y filesystem. El pattern matching actual es una buena primera capa pero no debe ser la única defensa.

---

### [SEC-CRI-003] ShellExecute con rutas hardcodeadas sin validación
- **Archivo:** Ribbon/ribbon_connect.h:331-379
- **Severidad:** Crítica
- **Descripción:** Múltiples llamadas a `ShellExecuteA` con rutas hardcodeadas (`C:\NEVEN\`, `C:\NEVEN\neven-config.json`) y ejecutables sin ruta completa (`Rgui.exe`, `julia.exe`). Un atacante podría colocar un ejecutable malicioso en el PATH o en `C:\NEVEN\` para ejecutar código arbitrario. Además, `ShellExecuteA` con `"explore"` y `"open"` puede ser explotado si el archivo destino es un .exe disfrazado.
- **Código:**
```cpp
ShellExecuteA(NULL, "open", "Rgui.exe", NULL, NULL, SW_SHOWNORMAL);
ShellExecuteA(NULL, "open", "julia.exe", NULL, NULL, SW_SHOWNORMAL);
ShellExecuteA(NULL, "explore", "C:\\NEVEN\\", NULL, NULL, SW_SHOWNORMAL);
ShellExecuteA(NULL, "open", "C:\\NEVEN\\neven-config.json", NULL, NULL, SW_SHOWNORMAL);
```
- **Recomendación:** Usar rutas absolutas verificadas para todos los ejecutables. Validar que el archivo destino existe y tiene la extensión esperada antes de llamar a ShellExecute. Usar `CreateProcess` con ruta completa en lugar de `ShellExecute` para ejecutables. Verificar la firma digital de los ejecutables antes de lanzarlos.

---

### [SEC-CRI-004] CreateProcess con input de usuario en Quarto sin sanitización completa
- **Archivo:** Core/src/basic_functions.cc:387-399
- **Severidad:** Crítica
- **Descripción:** La función `RJ_Quarto` construye un command line concatenando `qmd_path` (que proviene de una celda de Excel) directamente en el comando de CreateProcess. Aunque QuartoService.cc tiene `ValidateInputSecurity`, la función legacy en basic_functions.cc NO la usa. Un usuario malicioso podría inyectar comandos via el path del archivo .qmd.
- **Código:**
```cpp
std::string command = "\"" + quarto_exe + "\" render \"" + qmd_path + "\" --to html";
// ...
strncpy_s(cmd_buf, command.c_str(), sizeof(cmd_buf) - 1);
if (!CreateProcessA(nullptr, cmd_buf, nullptr, nullptr, FALSE, ...))
```
- **Recomendación:** Aplicar la misma validación de `ValidateInputSecurity` (bloqueo de `|`, `&`, `;`, `` ` ``, `<`, `>`, `..`) antes de construir el command line. Mejor aún: usar la API de QuartoService que ya tiene estas validaciones en lugar de la función legacy. Considerar usar un array de argumentos en lugar de concatenación de strings.

---

### [SEC-ALT-001] Protobuf ParseFromArray sin validación de tamaño
- **Archivo:** Common/message_utilities.cc:57-59
- **Severidad:** Alta
- **Descripción:** La función `Unframe` lee un `int32_t` del buffer como tamaño del mensaje y lo pasa directamente a `ParseFromArray` sin validar que: (1) `bytes` no sea negativo, (2) `bytes` no exceda `len - sizeof(int32_t)`, (3) el buffer tenga suficiente espacio. Un mensaje malformado podría causar lectura fuera de límites.
- **Código:**
```cpp
bool Unframe(google::protobuf::Message &message, const char *data, uint32_t len) {
    int32_t bytes;
    memcpy(reinterpret_cast<void*>(&bytes), data, sizeof(int32_t));
    return message.ParseFromArray(data + sizeof(int32_t), bytes);
}
```
- **Recomendación:** Validar que `len >= sizeof(int32_t)`, que `bytes >= 0`, y que `bytes <= len - sizeof(int32_t)` antes de llamar a `ParseFromArray`. Retornar `false` si alguna condición falla:
```cpp
if (len < sizeof(int32_t)) return false;
int32_t bytes;
memcpy(&bytes, data, sizeof(int32_t));
if (bytes < 0 || static_cast<uint32_t>(bytes) > len - sizeof(int32_t)) return false;
return message.ParseFromArray(data + sizeof(int32_t), bytes);
```

---

### [SEC-ALT-002] ReadFile/WriteFile en pipe.cc sin validación previa de handle
- **Archivo:** Common/pipe.cc:69
- **Severidad:** Alta
- **Descripción:** La función `StartRead()` llama a `ReadFile(handle_, ...)` verificando solo `reading_`, `error_` y `connected_`, pero no valida explícitamente que `handle_` sea válido antes de la operación. Si `connected_` se establece en `true` pero el handle se invalida por una condición de carrera, se produciría un comportamiento indefinido. Similarmente, `NextWrite()` en línea 152 escribe sin verificar `handle_`.
- **Código:**
```cpp
int Pipe::StartRead() {
  if (reading_ || error_ || !connected_) return 0;
  reading_ = true;
  ResetEvent(read_io_.hEvent);
  ReadFile(handle_, read_buffer_, buffer_size_, 0, &read_io_);
  return 0;
}
```
- **Recomendación:** Agregar validación explícita del handle antes de operaciones I/O:
```cpp
if (handle_ == INVALID_HANDLE_VALUE || !handle_) return -1;
```
Considerar usar `UniqueHandle` (ya existente en el proyecto) para gestionar el handle del pipe y prevenir uso después de cierre.

---

### [SEC-ALT-003] Memory leak en rinterface_win.cc — allocaciones sin delete
- **Archivo:** ControlR/src/rinterface_win.cc:144-153
- **Severidad:** Alta
- **Descripción:** Se asignan `new structRstart`, `new char[MAX_PATH]` (x2) al inicio de `RLoop()` pero nunca se liberan. Dado que `RLoop` es el loop principal de R que corre indefinidamente, estos buffers se pierden al terminar el proceso. Aunque el OS los libera al cerrar el proceso, es una mala práctica y podría causar problemas si la función se refactoriza para ser re-invocable.
- **Código:**
```cpp
Rstart Rp = new structRstart;
char *local_rhome = new char[MAX_PATH];
char *local_ruser = new char[MAX_PATH];
// ... nunca se llama delete[] ni delete
```
- **Recomendación:** Usar variables automáticas (stack) o smart pointers:
```cpp
structRstart rp_storage;
Rstart Rp = &rp_storage;
std::array<char, MAX_PATH> local_rhome_buf{};
char* local_rhome = local_rhome_buf.data();
```

---

### [SEC-ALT-004] sscanf sin width specifier en ControlPython
- **Archivo:** ControlPython/src/python_interface.cc:47
- **Severidad:** Alta
- **Descripción:** Se usa `sscanf(version, "%d.%d.%d", ...)` para parsear la versión de Python. Aunque en este caso los especificadores `%d` son seguros (leen enteros, no strings), el patrón general de usar sscanf sin validación del string de entrada es riesgoso. Si `Py_GetVersion()` retornara un formato inesperado, los punteros quedarían sin inicializar (aunque se pre-inicializan a 0).
- **Código:**
```cpp
void PythonGetVersion(int32_t *major, int32_t *minor, int32_t *patch) {
  const char* version = Py_GetVersion();
  *major = 0; *minor = 0; *patch = 0;
  if (version) {
    sscanf(version, "%d.%d.%d", major, minor, patch);
  }
}
```
- **Recomendación:** Verificar el valor de retorno de `sscanf` para confirmar que se parsearon los 3 campos esperados:
```cpp
if (version) {
    if (sscanf(version, "%d.%d.%d", major, minor, patch) != 3) {
        *major = 0; *minor = 0; *patch = 0;
    }
}
```

---

### [SEC-ALT-005] ContentPipeline CreateProcess con const_cast sin validación
- **Archivo:** Common/ContentPipeline.cc:378
- **Severidad:** Alta
- **Descripción:** Se usa `const_cast<char*>(cmd.c_str())` para pasar a `CreateProcessA`, lo cual es técnicamente undefined behavior ya que `CreateProcessA` puede modificar el buffer del command line. Además, el `cmd` se construye concatenando `pandoc_path` y `file_path` sin la validación de seguridad que sí tiene QuartoService.
- **Código:**
```cpp
BOOL created = CreateProcessA(
    NULL,
    const_cast<char*>(cmd.c_str()),  // UB: CreateProcessA may modify this buffer
    NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL,
    &si, &pi);
```
- **Recomendación:** Usar un buffer mutable como ya se hace en otros lugares del código:
```cpp
std::vector<char> cmd_buf(cmd.begin(), cmd.end());
cmd_buf.push_back('\0');
CreateProcessA(NULL, cmd_buf.data(), ...);
```
Además, aplicar validación de input similar a `ValidateInputSecurity` para `file_path`.

---

### [SEC-MED-001] Memory leak en gdi_graphics_device — png_clsid nunca se libera
- **Archivo:** ControlR/src/gdi_graphics_device.cc:211
- **Severidad:** Media
- **Descripción:** Se asigna `new CLSID(...)` para almacenar el codec PNG, pero este puntero se retorna como `void*` y nunca se libera explícitamente. Es un leak de tamaño fijo (16 bytes) que ocurre una sola vez, pero indica un patrón de gestión de memoria inseguro.
- **Código:**
```cpp
png_clsid = new CLSID(pImageCodecInfo[j].Clsid);
// ...
free(pImageCodecInfo);
if (png_clsid) return (void*)png_clsid;
```
- **Recomendación:** Usar una variable estática en lugar de allocación dinámica, ya que el CLSID del codec PNG no cambia:
```cpp
static CLSID png_clsid_storage;
png_clsid_storage = pImageCodecInfo[j].Clsid;
return &png_clsid_storage;
```

---

### [SEC-MED-002] type_conversions.h — allocaciones new WCHAR[] delegadas a Excel
- **Archivo:** Core/include/type_conversions.h:76, 100, 473, 527
- **Severidad:** Media
- **Descripción:** Múltiples allocaciones con `new WCHAR[]` y `new XLOPER12[]` que se marcan con `xlbitDLLFree` para que Excel las libere via `xlAutoFree12`. Este es el patrón correcto para el Excel SDK, pero si `xlAutoFree12` no se implementa correctamente o Excel no llama al callback, se producen memory leaks. El patrón es inherente al diseño del XLL SDK.
- **Código:**
```cpp
WCHAR *wide_string = new WCHAR[wide_char_count + 1];
// ...
target->xltype = xltypeStr;
if (flag_dll_free) target->xltype |= xlbitDLLFree;
target->val.str = wide_string;
```
- **Recomendación:** Verificar que `xlAutoFree12` está correctamente implementado y cubre todos los tipos (xltypeStr, xltypeMulti, xltypeRef). Considerar un allocator pool para reducir fragmentación. Este es un riesgo inherente al modelo de memoria del Excel SDK — documentar el contrato claramente.

---

### [SEC-MED-003] Buffer sprintf_s en ControlR/ControlJulia con tamaño fijo
- **Archivo:** ControlR/src/controlr.cc:627, ControlJulia/src/control_julia.cc:571
- **Severidad:** Media
- **Descripción:** Se usa `sprintf_s(buffer, "%s-M", State().pipename.c_str())` con un buffer de tamaño `MAX_PATH` (260 chars). Si `pipename` excede ~256 caracteres, se truncaría. Aunque en la práctica los pipe names son cortos (~30 chars), no hay validación explícita del tamaño.
- **Código:**
```cpp
char buffer[MAX_PATH];
sprintf_s(buffer, "%s-M", State().pipename.c_str());
uintptr_t thread_handle = _beginthreadex(0, 0, ManagementThreadFunction, buffer, 0, 0);
```
- **Recomendación:** Usar `std::string` y pasar un puntero estable al thread, o validar que `pipename.length() < MAX_PATH - 3` antes de formatear. Alternativamente, usar `snprintf` con verificación del valor de retorno.

---

### [SEC-MED-004] Thread recibe puntero a buffer local en stack
- **Archivo:** ControlR/src/controlr.cc:627-629, ControlJulia/src/control_julia.cc:571-573
- **Severidad:** Media
- **Descripción:** El buffer local `char buffer[MAX_PATH]` se pasa como argumento al thread via `_beginthreadex`. Si la función que contiene el buffer retorna antes de que el thread lea el dato, se produce un use-after-free. En la práctica funciona porque el thread lee inmediatamente, pero es un patrón frágil.
- **Código:**
```cpp
char buffer[MAX_PATH];
sprintf_s(buffer, "%s-M", State().pipename.c_str());
uintptr_t thread_handle = _beginthreadex(0, 0, ManagementThreadFunction, buffer, 0, 0);
```
- **Recomendación:** Usar memoria dinámica (heap) para el argumento del thread, o usar un `std::string` almacenado en un lugar con lifetime adecuado:
```cpp
char* buffer = _strdup(pipe_name_with_suffix.c_str());
_beginthreadex(0, 0, ManagementThreadFunction, buffer, 0, 0);
// ManagementThreadFunction debe hacer free(data) al inicio
```

---

### [SEC-BAJ-001] Logging de información sensible en PlutoManager
- **Archivo:** Common/PlutoManager.cc:67
- **Severidad:** Baja
- **Descripción:** Se loguea el secreto de Pluto en texto plano. Aunque el secreto actual es trivial ("rj2xcl"), si se mejora a un token real, el logging lo expondría en archivos de log.
- **Código:**
```cpp
RJ2XCL_LOG_INFO("PlutoManager initialized (port %d, secret=%s)", port_, pluto_secret_.c_str());
```
- **Recomendación:** No loguear secretos. Usar `RJ2XCL_LOG_INFO("PlutoManager initialized (port %d)", port_)` sin incluir el secreto.

---

### [SEC-BAJ-002] SecurityService permite ejecución sin hash file
- **Archivo:** Common/SecurityService.cc:37-40
- **Severidad:** Baja
- **Descripción:** Si no existe un archivo `.sha256` junto al script, `VerifyScriptIntegrity` retorna `true` (permite ejecución). Esto significa que la verificación de integridad es opt-in y no protege scripts que no tengan hash pre-calculado.
- **Código:**
```cpp
std::ifstream hash_file(hash_path);
if (!hash_file.is_open()) {
    // No hash file — allow execution but log for audit trail
    return true;
}
```
- **Recomendación:** Considerar un modo "strict" configurable donde scripts sin hash sean bloqueados. Agregar logging cuando se permite ejecución sin verificación para mantener trazabilidad de auditoría.

---

## Prácticas Positivas de Seguridad

Las siguientes buenas prácticas fueron identificadas durante la auditoría:

### ✅ Uso consistente de funciones seguras de strings
- **strcpy_s**, **sprintf_s**, **strncpy_s**, **vsprintf_s** se usan en lugar de las variantes inseguras en todo el código base.
- **snprintf** con tamaño de buffer explícito en ContentPipeline, json11, NotebookExporter.
- No se encontró ningún uso de `strcpy`, `sprintf`, `strcat`, `gets` sin bounds checking.

### ✅ UniqueHandle — RAII para handles de Windows
- **Archivo:** Common/UniqueHandle.h
- Wrapper RAII completo con move semantics, prevención de copia, y validación `is_valid()`.
- Usado consistentemente en QuartoService, language_service, y otros módulos.

### ✅ Validación de INVALID_HANDLE_VALUE
- Todas las llamadas a `CreateFileA`, `CreateNamedPipeA`, `FindFirstFileA` verifican contra `INVALID_HANDLE_VALUE` antes de usar el handle.
- El patrón `if (!handle || handle == INVALID_HANDLE_VALUE)` es consistente.

### ✅ Smart pointers para gestión de servicios
- `std::shared_ptr<LanguageService>` para servicios de lenguaje.
- `std::unique_ptr` para RibbonService, FileWatchService, ExcelBridge, CallbackDispatcher.
- `std::make_shared` y `std::make_unique` usados correctamente.

### ✅ SecurityService con SHA-256 para integridad de scripts
- Verificación de integridad basada en BCrypt SHA-256.
- RAII wrappers para handles de BCrypt (BcryptAlgDeleter, BcryptHashDeleter).

### ✅ SandboxVerifier con múltiples capas de detección
- Normalización case-insensitive.
- Stripping de whitespace para prevenir bypass por espacios.
- Detección de bypass por concatenación (paste, string interpolation).
- Cobertura de R, Julia y Python con ~80 patrones bloqueados.

### ✅ QuartoService con validación de input
- `ValidateInputSecurity` bloquea path traversal (`..`) y caracteres de inyección (`|`, `&`, `;`, `` ` ``, `<`, `>`).
- Validación de extensión (.qmd) y formato (html/pdf/docx whitelist).
- Timeout configurable para procesos externos.

### ✅ Job Objects para control de procesos hijo
- Los procesos hijo se asignan a Job Objects de Windows, permitiendo terminación grupal.
- Zombie cleanup al inicio mata procesos huérfanos de sesiones anteriores.

### ✅ Pipe reconnection con manejo de errores
- El callback pipe implementa reconexión automática en caso de `ERROR_BROKEN_PIPE`.
- Buffer dinámico que crece en caso de `ERROR_MORE_DATA` (hasta 256KB).

### ✅ Protobuf para serialización tipada
- Uso de Protocol Buffers en lugar de parsing manual de texto.
- Framing con longitud prefijada para delimitar mensajes.

---

## Recomendaciones Prioritarias

1. **[Inmediata]** Corregir SEC-CRI-001: Generar secreto aleatorio y habilitar autenticación en Pluto.
2. **[Inmediata]** Corregir SEC-ALT-001: Agregar validación de bounds en `Unframe()`.
3. **[Corto plazo]** Corregir SEC-CRI-004: Unificar la validación de input de Quarto en un solo punto.
4. **[Corto plazo]** Corregir SEC-ALT-005: Eliminar `const_cast` y usar buffer mutable.
5. **[Mediano plazo]** Evaluar SEC-CRI-002: Implementar AppContainer o Restricted Tokens para procesos hijo.
6. **[Mediano plazo]** Corregir SEC-CRI-003: Resolver rutas de ejecutables de forma segura.
