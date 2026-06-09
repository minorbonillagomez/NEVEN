# Plan de Integración de Julia 1.12.6 en NEVEN

**Fecha**: 14 abril 2026
**Estado**: Planificación

---

## 1. Diagnóstico Actual

ControlJulia.exe crashea con `STATUS_ENTRYPOINT_NOT_FOUND` (`0xC0000139`).

**Causa raíz**: El código fue escrito para Julia 0.6.x. Julia 1.12.6 tiene cambios significativos de API.

---

## 2. Cambios Necesarios

### 2.1. Versión check en main() (`control_julia.cc`)
```cpp
// ACTUAL (Julia 0.6 hardcodeado):
if (major != 0) return ERROR;
if (minor != 6) return ERROR;

// NECESARIO (Julia 1.x+):
if (major < 1) return ERROR;  // Mínimo Julia 1.0
```

### 2.2. Regenerar libjulia.lib
La lib actual en `ControlJulia/lib/libjulia.lib` fue generada para Julia 0.6.
Necesita regenerarse desde `libjulia.dll` de Julia 1.12.6:
```cmd
dumpbin /exports "%LOCALAPPDATA%\Programs\Julia-1.12.6\bin\libjulia.dll" > libjulia.def
lib /machine:X64 /def:libjulia.def /out:libjulia.lib
```

### 2.3. Headers de Julia
- Headers reales en: `%LOCALAPPDATA%\Programs\Julia-1.12.6\include\julia\`
- Necesitan prioridad sobre los mocks en `Include/julia.h`
- Mismo enfoque que ControlR: `target_include_directories(BEFORE)`

### 2.4. Funciones de API que cambiaron

| Julia 0.6 | Julia 1.x+ | Notas |
|-----------|-----------|-------|
| `jl_get_ptls_states()` | **ELIMINADA** | Ya no se necesita en Julia 1.x |
| `jl_arrayset(arr, val, i)` | `jl_array_ptr_set(arr, i, val)` | Parámetros reordenados |
| `jl_options.use_compilecache` | Verificar si existe | Puede haber cambiado |
| `jl_options.color` | Verificar | |
| `jl_options.handle_signals` | Verificar | |
| `jl_options.use_precompiled` | Verificar | |
| `jl_options.polly` | Verificar | |
| `jl_options.fast_math` | Verificar | |

### 2.5. CMakeLists.txt de ControlJulia
- Agregar auto-detección de JULIA_HOME
- Usar headers reales de Julia 1.12.6
- Regenerar libjulia.lib
- Agregar `prepend_path` para que `libjulia.dll` esté en PATH

### 2.6. Archivos a modificar

| Archivo | Cambios |
|---------|---------|
| `ControlJulia/src/control_julia.cc` | Version check, eliminar `jl_get_ptls_states` |
| `ControlJulia/src/julia_interface.cc` | `jl_arrayset` --> `jl_array_ptr_set`, `jl_options` fields, eliminar `ptls` |
| `ControlJulia/src/JuliaConversion.cpp` | Verificar compatibilidad de tipos |
| `ControlJulia/CMakeLists.txt` | Headers reales, lib regenerada |
| `ControlJulia/lib/libjulia.lib` | Regenerar desde Julia 1.12.6 |
| `Include/julia.h` | Actualizar mock si necesario |

---

## 3. Lecciones de la Integración de R

Aplicar las mismas estrategias que funcionaron con R:

1. **Headers reales primero**: `target_include_directories(BEFORE)` con headers de Julia 1.12.6
2. **Lib regenerada**: Usar `dumpbin` + `lib` para generar `libjulia.lib` desde `libjulia.dll`
3. **Logging extenso**: Agregar logging a `controlr.log` estilo para diagnosticar crashes
4. **Startup con wait=true**: Enviar startup.jl con `wait=true` para mantener pipe sincronizado
5. **Compilar y probar incrementalmente**: Primero que compile, luego que arranque, luego que ejecute

---

## 5. Estado Actual (14 abril 2026)

### Logrado
- ControlJulia.exe compila con Julia 1.12.6 ✅
- Julia 1.12.6 arranca correctamente (version check, pipes) ✅
- Pipe se conecta entre XLL y ControlJulia ✅
- libjulia.lib regenerada para Julia 1.12.6 ✅
- Header de compatibilidad `julia_compat.h` creado ✅
- 50+ cambios de API corregidos (jl_arrayset, ptls, jl_options, etc.) ✅

### Problema Resuelto: JIT Compilation
- Cold start: ~1 minuto para primera llamada (JIT compilation)
- Llamadas siguientes: instantáneas
- Timeout de 10 minutos para acomodar cold start
- Mensaje amigable si excede timeout: "Julia is compiling (JIT). Please wait and press F9"
- **No se necesita sysimage precompilada** — el rendimiento es aceptable

---

*Team Vikingos ⚔️*
