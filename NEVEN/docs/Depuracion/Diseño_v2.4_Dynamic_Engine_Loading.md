# Diseño v2.4 — Dynamic Engine Loading
## Desacoplamiento de motores R y Julia del ciclo de compilación

**Fecha:** 3 de agosto de 2026
**Rama:** `feature/dynamic-engine-loading`
**Punto de retorno:** tag `v2.3-stable` (commit `50ffe62`)

---

## 1. Problema

NEVEN v2.3 acopla los binarios `ControlR.exe` y `ControlJulia.exe` a versiones específicas de R y Julia **en tiempo de compilación**. Para actualizar la versión del motor hay que:

1. Obtener nuevos headers de la versión target
2. Regenerar `.lib` de importación (`rebuild-r-libs.ps1`, `rebuild-julia-libs.ps1`)
3. Corregir incompatibilidades de API (ocurrió con R 4.4.1 y Julia 1.12.6)
4. Recompilar y testear
5. Desplegar

BERT murió porque este ciclo se volvió insostenible. NEVEN tiene el mismo riesgo estructural.

**Python ya resolvió esto** con Stable ABI (`python3.dll`) — ControlPython.exe funciona con cualquier Python 3.x sin cambios.

---

## 2. Inventario de funciones de API

### 2.1 R C API — funciones usadas en ControlR

**Inicialización (las más propensas a cambios entre versiones):**

| Función | Riesgo | Cambió en |
|:---|:---:|:---|
| `R_setStartTime()` | Bajo | Estable desde R 3.x |
| `R_DefParams(Rstart*)` | **Alto** | `structRstart` agregó campos en R 4.x |
| `R_SetParams(Rstart*)` | **Alto** | Depende de `structRstart` |
| `R_set_command_line_arguments()` | Bajo | Estable |
| `setup_Rmainloop()` | Medio | Puede cambiar comportamiento |
| `run_Rmainloop()` | Medio | REPL loop |
| `GA_initapp(0,0)` | Bajo | Windows graphics, estable |
| `Rf_endEmbeddedR(0)` | Bajo | Estable |

**Type system y valores:**

| Función | Riesgo |
|:---|:---|
| `Rf_allocVector`, `Rf_allocMatrix` | Bajo — API estable |
| `Rf_mkChar`, `Rf_mkString` | Bajo |
| `Rf_ScalarReal`, `Rf_ScalarInteger`, etc. | Bajo |
| `R_NilValue`, `R_GlobalEnv` | Bajo — constantes globales |
| `R_CHAR(SEXP)` | Bajo |

**Evaluación:**

| Función | Riesgo |
|:---|:---|
| `R_ParseVector()` | Bajo — estable |
| `R_tryEval()`, `R_tryEvalSilent()` | Bajo |
| `R_curErrorBuf()` | Bajo |

**Callbacks (los más críticos para la integración):**

| Función | Riesgo | Nota |
|:---|:---:|:---|
| `R_ReadConsole` | **Alto** | Firma cambió `char*` → `unsigned char*` en R 4.4.1 |
| `R_WriteConsoleEx` | Medio | Estable pero tipo del 2do arg puede cambiar |
| `R_Busy`, `R_CallBack` | Bajo | Punteros a función simples |

**Conclusión R:** ~8 funciones de riesgo alto/medio, todas en la inicialización y callbacks. El resto es API estable.

---

### 2.2 Julia C API — funciones usadas en ControlJulia

**Inicialización:**

| Función | Riesgo | Nota |
|:---|:---:|:---|
| `jl_init()` | Bajo | Estable desde 1.0 |
| `jl_init_with_image()` | Bajo | Para sysimage — estable |
| `jl_atexit_hook(0)` | Bajo | Estable |

**Evaluación:**

| Función | Riesgo | Nota |
|:---|:---:|:---|
| `jl_eval_string()` | Bajo | API estable |
| `jl_toplevel_eval_in()` | Bajo | Estable |
| `jl_parse_input_line()` | Medio | Puede cambiar |
| `jl_load_file_string()` | Bajo | Estable |

**Tipos y boxing:**

| Función | Riesgo | Nota |
|:---|:---:|:---|
| `jl_box_float64/int64/bool/...` | Bajo | Estable |
| `jl_unbox_float64/int64/...` | Bajo | Estable |
| `jl_is_string/array/nothing/...` | Bajo | Estable |
| `jl_string_ptr/len` | Bajo | Estable |

**Arrays:**

| Función | Riesgo | Nota |
|:---|:---:|:---|
| `jl_alloc_array_1d/2d()` | Bajo | Estable |
| `jl_array_data()` | **Alto** | Cambió el tipo de retorno entre versiones |
| `jl_array_dim/len/ndims` | Bajo | Estable |
| `jl_arrayset()` | **Alto** | **ELIMINADA** en Julia 1.10+ — usar `jl_array_ptr_set()` |
| `jl_array_ptr_ref()` | Medio | Alternativa a arrayset |

**Excepciones:**

| Función | Riesgo | Nota |
|:---|:---:|:---|
| `jl_exception_occurred()` | Bajo | Estable |
| `jl_current_exception()` | **Alto** | Firma cambió en Julia 1.12 |
| `jl_exception_clear()` | Bajo | Estable |
| `JL_TRY / JL_CATCH` | Medio | Macros que dependen de internals |

**Options:**

| Función | Riesgo | Nota |
|:---|:---:|:---|
| `jl_options` | **Alto** | Struct con campos que cambian entre versiones |
| `JL_OPTIONS_*` | **Alto** | Constantes que pueden moverse |

**Conclusión Julia:** ~6 funciones de riesgo alto, concentradas en array management, excepciones y options. Algunas ya fueron **eliminadas** (`jl_arrayset`).

---

## 3. Estrategia de desacoplamiento

### 3.1 Carga dinámica con `LoadLibrary` + `GetProcAddress`

En lugar de enlazar contra `R64.lib` o `libjulia.lib` en tiempo de compilación, cargar el motor en runtime:

```cpp
// ── R Engine Loader ──────────────────────────────────────────────────
class REngineLoader {
public:
    static bool Load(const std::string& r_home) {
        std::string dll_path = r_home + "\\bin\\x64\\R.dll";
        hR_ = LoadLibraryA(dll_path.c_str());
        if (!hR_) return false;

        // Resolver cada función dinámicamente
        R_DefParams     = GetProc<FnRDefParams>("R_DefParams");
        R_SetParams     = GetProc<FnRSetParams>("R_SetParams");
        R_setStartTime  = GetProc<FnVoid>("R_setStartTime");
        setup_Rmainloop = GetProc<FnVoid>("setup_Rmainloop");
        run_Rmainloop   = GetProc<FnVoid>("run_Rmainloop");
        Rf_allocVector  = GetProc<FnAllocVec>("Rf_allocVector");
        // ... todas las demás funciones
        
        return ValidateRequired();
    }

    // Punteros a funciones cargadas dinámicamente
    static inline FnRDefParams     R_DefParams     = nullptr;
    static inline FnRSetParams     R_SetParams     = nullptr;
    // ...

private:
    template<typename T>
    static T GetProc(const char* name) {
        auto fn = reinterpret_cast<T>(GetProcAddress(hR_, name));
        if (!fn) RJ2XCL_LOG_WARN("R API: %s not found", name);
        return fn;
    }
    static inline HMODULE hR_ = nullptr;
};
```

### 3.2 Capa de compatibilidad de versiones

Para las funciones que cambian entre versiones, detectar la versión en runtime y usar la firma correcta:

```cpp
// R_ReadConsole cambió char* → unsigned char* en R 4.4
void SetupReadConsoleCallback(int r_major, int r_minor) {
    if (r_major >= 4 && r_minor >= 4) {
        Rp->ReadConsole = ReadConsole_NewSignature;
    } else {
        Rp->ReadConsole = ReadConsole_OldSignature;
    }
}

// jl_arrayset eliminada en Julia 1.10 — usar jl_array_ptr_set
void JuliaSetArrayElement(jl_array_t* arr, size_t idx, jl_value_t* val) {
    if (julia_minor_ >= 10) {
        jl_array_ptr_set(arr, idx, val);  // nuevo
    } else {
        jl_arrayset(arr, val, idx);       // legacy
    }
}
```

### 3.3 Estructura de archivos nueva

```
ControlR/
  src/
    controlr.cc             ← sin cambios (lógica de pipes)
    rinterface_win.cc       ← sin cambios (callbacks)
    r_engine_loader.cc      ← NUEVO: LoadLibrary + resolución dinámica
    r_engine_loader.h       ← NUEVO: interface + punteros a funciones
    r_version_compat.cc     ← NUEVO: adapters para cambios de versión

ControlJulia/
  src/
    control_julia.cc        ← sin cambios
    julia_interface.cc      ← sin cambios
    julia_engine_loader.cc  ← NUEVO
    julia_engine_loader.h   ← NUEVO
    julia_version_compat.cc ← NUEVO
```

### 3.4 CMakeLists.txt — eliminar dependencias de .lib

```cmake
# ANTES (v2.3): enlace estático contra versión específica
target_link_libraries(ControlR PRIVATE
    ${R_HOME}/bin/x64/R64.lib        # ← ELIMINAR
    ${R_HOME}/bin/x64/RGraphApp64.lib # ← ELIMINAR
)

# DESPUÉS (v2.4): solo Windows API para LoadLibrary
target_link_libraries(ControlR PRIVATE
    kernel32 # LoadLibrary, GetProcAddress, FreeLibrary
)
```

---

## 4. Plan de implementación por fases

### Fase 1 — R Engine Loader (ControlR)
1. Crear `r_engine_loader.h` con todos los typedefs de funciones
2. Crear `r_engine_loader.cc` con `LoadLibrary` y resolución
3. Crear `r_version_compat.cc` con adapters para `R_ReadConsole` y `structRstart`
4. Actualizar `rinterface_win.cc` para usar el loader en lugar de calls directos
5. Actualizar `CMakeLists.txt` de ControlR
6. **Test:** compilar con R 4.4.1 instalado, verificar `=NEVEN.r("1+1") = 2`
7. **Test extra:** instalar R 4.6.1 junto a 4.4.1, apuntar config a 4.6.1, verificar sin recompilar

### Fase 2 — Julia Engine Loader (ControlJulia)
1. Crear `julia_engine_loader.h` con typedefs
2. Crear `julia_engine_loader.cc`
3. Crear `julia_version_compat.cc` — manejar `jl_arrayset` eliminada, `jl_array_data` tipo, `jl_current_exception` firma
4. Actualizar `julia_interface.cc`
5. Actualizar `CMakeLists.txt`
6. **Test:** Julia 1.12.6 existente funciona
7. **Test extra:** apuntar a Julia versión más nueva sin recompilar

### Fase 3 — Testing y validación
- Todos los 357 tests pasan
- `=NEVEN.r("1+1") = 2` con R 4.4.1 y R 4.6.1
- `=NEVEN.j("sqrt(144)") = 12` con Julia 1.12.6 y Julia 1.13+
- NEVEN Studio funcional

### Fase 4 — Merge a main y tag v2.4

---

## 5. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|:---|:---:|:---|
| `structRstart` cambió en R 4.6 | Media | Detectar versión en runtime, usar offset conocido |
| `jl_options` struct cambió en Julia 1.13 | Alta | No leer campos individuales, usar solo los estables |
| Performance overhead de LoadLibrary | Muy baja | LoadLibrary ocurre una sola vez al arrancar |
| Función no exportada en nueva versión | Baja | Validar en `Load()` y fallar con mensaje claro |

---

## 6. Decisión de retorno

Si en cualquier fase el acoplamiento dinámico introduce regresiones no resolvibles en tiempo razonable:

```bash
git checkout main
git tag v2.3-stable  # ya creado — el estado estable actual
```

Los binarios de producción en `C:\NEVEN\` siguen siendo v2.3 hasta que v2.4 pase todos los tests.

---

*Documento de diseño — NEVEN v2.4*
*Rama: `feature/dynamic-engine-loading`*
*Autor: Minor Bonilla Gómez / Kiro*
