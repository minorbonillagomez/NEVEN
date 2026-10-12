# TASKS v2.4 — Dynamic Engine Loading
## Desacoplamiento de motores R y Julia del ciclo de compilación

**Rama:** `feature/dynamic-engine-loading`
**Punto de retorno:** tag `v2.3-stable` (commit `50ffe62`)
**Referencia de diseño:** `docs/Depuracion/Diseño_v2.4_Dynamic_Engine_Loading.md`

---

## FASE 1 — R Engine Loader

### TASK-R-01 — Definir typedefs de la R C API
**Estado:** ⏳ Pendiente
**Archivo:** `ControlR/src/r_engine_loader.h` (nuevo)
**Descripción:** Crear el header con todos los typedefs de punteros a función para las ~50 funciones de la R C API que usa NEVEN. Sin implementación — solo las declaraciones de tipo.
```cpp
typedef void   (*FnRDefParams)(Rstart*);
typedef void   (*FnRSetParams)(Rstart*);
typedef void   (*FnRSetStartTime)(void);
// ... etc
```
**Criterio de éxito:** El header compila sin errores. Cero dependencias de `R64.lib` o headers de R.

---

### TASK-R-02 — Implementar REngineLoader (LoadLibrary)
**Estado:** ⏳ Pendiente
**Archivo:** `ControlR/src/r_engine_loader.cc` (nuevo)
**Dependencias:** TASK-R-01
**Descripción:** Implementar la clase `REngineLoader` con:
- `Load(r_home)` — llama `LoadLibrary("R.dll")` y resuelve cada función con `GetProcAddress`
- `Unload()` — llama `FreeLibrary`
- `GetVersion()` — lee `R_VERSION_MAJOR` y `R_VERSION_MINOR` para compatibilidad
- Validación: si alguna función crítica no se resuelve, fallar con mensaje claro
**Criterio de éxito:** `REngineLoader::Load("C:/Program Files/R/R-4.4.1")` retorna true y todos los punteros quedan resueltos.

---

### TASK-R-03 — Capa de compatibilidad de versión R
**Estado:** ⏳ Pendiente
**Archivo:** `ControlR/src/r_version_compat.cc` (nuevo)
**Dependencias:** TASK-R-02
**Descripción:** Manejar las funciones que cambiaron entre versiones de R:
- `R_ReadConsole`: firma `char*` (R < 4.4) vs `unsigned char*` (R >= 4.4) — detectar en runtime y usar el callback correcto
- `structRstart`: verificar que los campos críticos existen en la versión instalada
- `CharacterMode` enum: confirmar que `LinkDLL` sigue siendo válido
**Criterio de éxito:** El mismo binario ControlR.exe funciona con R 4.4.1 Y con R 4.6.1 sin recompilar.

---

### TASK-R-04 — Actualizar rinterface_win.cc para usar REngineLoader
**Estado:** ⏳ Pendiente
**Archivos:** `ControlR/src/rinterface_win.cc`, `ControlR/src/controlr.cc`
**Dependencias:** TASK-R-02, TASK-R-03
**Descripción:** Reemplazar todas las llamadas directas a funciones R por llamadas a través de los punteros del REngineLoader. Ejemplo:
```cpp
// ANTES: llamada directa (requiere R64.lib)
R_DefParams(Rp);

// DESPUÉS: a través del loader (carga dinámica)
REngineLoader::R_DefParams(Rp);
```
**Criterio de éxito:** El archivo compila sin referencias a R64.lib.

---

### TASK-R-05 — Actualizar CMakeLists.txt de ControlR
**Estado:** ⏳ Pendiente
**Archivo:** `ControlR/CMakeLists.txt`
**Dependencias:** TASK-R-04
**Descripción:**
- Eliminar `target_link_libraries(ControlR PRIVATE R64.lib RGraphApp64.lib)`
- Eliminar `target_include_directories` que apunten a R headers
- Agregar `kernel32` (necesario para LoadLibrary)
- Mantener los demás enlaces (Common, PB, etc.)
**Criterio de éxito:** `cmake --build Build --target ControlR` compila exitosamente sin ningún archivo `.lib` de R.

---

### TASK-R-06 — Test R 4.4.1: verificar paridad funcional
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-R-05
**Descripción:** Con el nuevo ControlR.exe dinámico, verificar:
- `=NEVEN.r("1+1")` → 2 ✓
- `=NEVEN.r("sqrt(144)")` → 12 ✓
- Función de la librería R4XCL: `=R.AD_Descriptiva(datos, 1)` ✓
- Gráfico Plotly: `=NEVEN.v(R.GR_EjemploBasico(...))` ✓
- Todos los 357 tests pasan ✓
**Criterio de éxito:** Comportamiento idéntico a v2.3-stable.

---

### TASK-R-07 — Test R 4.6.1: actualizar SIN recompilar
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-R-06
**Descripción:**
1. Instalar R 4.6.1 en paralelo (sin desinstalar 4.4.1)
2. Actualizar `neven-config.json → NEVEN.R.home` a la ruta de R 4.6.1
3. Reiniciar NEVEN Studio
4. Ejecutar las mismas pruebas que TASK-R-06
5. **Sin recompilar ControlR.exe**
**Criterio de éxito:** Todo funciona con R 4.6.1 usando el mismo binario que con R 4.4.1.

---

## FASE 2 — Julia Engine Loader

### TASK-J-01 — Definir typedefs de la Julia C API
**Estado:** ⏳ Pendiente (espera completar Fase 1)
**Archivo:** `ControlJulia/src/julia_engine_loader.h` (nuevo)
**Descripción:** Typedefs para las ~80 funciones Julia usadas. Especial atención a las que cambiaron:
- `jl_arrayset` → eliminada en Julia 1.10, reemplazada por `jl_array_ptr_set`
- `jl_array_data` → tipo de retorno cambió
- `jl_current_exception` → firma cambió en Julia 1.12
- `jl_options` → struct con campos que varían

---

### TASK-J-02 — Implementar JuliaEngineLoader
**Estado:** ⏳ Pendiente
**Archivo:** `ControlJulia/src/julia_engine_loader.cc` (nuevo)
**Dependencias:** TASK-J-01
**Descripción:** `LoadLibrary("libjulia.dll")` + resolución dinámica. Detectar versión con `jl_ver_major()`/`jl_ver_minor()`.

---

### TASK-J-03 — Capa de compatibilidad de versión Julia
**Estado:** ⏳ Pendiente
**Archivo:** `ControlJulia/src/julia_version_compat.cc` (nuevo)
**Dependencias:** TASK-J-02
**Descripción:** Adapters para:
- `ArraySet(arr, idx, val)` → usa `jl_arrayset` (< 1.10) o `jl_array_ptr_set` (>= 1.10)
- `ArrayData(arr)` → cast correcto según versión
- `CurrentException()` → firma correcta según versión
- `SetOptions()` → solo campos estables de `jl_options`

---

### TASK-J-04 — Actualizar julia_interface.cc para usar JuliaEngineLoader
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-J-02, TASK-J-03
**Descripción:** Equivalente a TASK-R-04 pero para Julia.

---

### TASK-J-05 — Actualizar CMakeLists.txt de ControlJulia
**Estado:** ⏳ Pendiente
**Archivo:** `ControlJulia/CMakeLists.txt`
**Descripción:** Eliminar enlace estático a `libjulia.lib`.

---

### TASK-J-06 — Test Julia 1.12.6: verificar paridad funcional
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-J-05
**Descripción:** Equivalente a TASK-R-06 pero para Julia. `=NEVEN.j("sqrt(144)")` → 12 ✓

---

### TASK-J-07 — Test Julia versión nueva SIN recompilar
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-J-06
**Descripción:** Equivalente a TASK-R-07 pero para Julia. Apuntar config a Julia más nueva y verificar sin recompilar.

---

## FASE 3 — Integración y release

### TASK-INT-01 — Suite de tests completa en rama feature
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-R-06, TASK-J-06
**Descripción:** Ejecutar los 357 tests con los nuevos loaders. Ninguna regresión permitida.
```powershell
cmake --build Build --config Release
ctest -C Release --output-on-failure
```

---

### TASK-INT-02 — Actualizar NEVEN Studio con nuevos binarios
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-INT-01
**Descripción:** Desplegar ControlR.exe y ControlJulia.exe dinámicos a `C:\NEVEN\`. Verificar que NEVEN Studio funciona completo (Data Lab, Benchmark, Run Script).

---

### TASK-INT-03 — Actualizar documentación
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-INT-02
**Descripción:**
- `NEVEN-BOOK.md` → sección de arquitectura actualizada con carga dinámica
- `MANUAL_MANTENIMIENTO.md` → proceso de actualización R/Julia simplificado
- `Estado_del_arte.md` → agregar fila NEVEN v2.4
- `Evaluacion_objetiva.md` → actualizar mantenibilidad (+0.5 por desacoplamiento)

---

### TASK-INT-04 — Merge a main y tag v2.4
**Estado:** ⏳ Pendiente
**Dependencias:** TASK-INT-03
**Descripción:**
```bash
git checkout main
git merge feature/dynamic-engine-loading
git tag -a v2.4-stable -m "NEVEN v2.4 — motores R y Julia desacoplados (Dynamic Engine Loading)"
git push origin main --tags
```

---

## Resumen

| Fase | Tasks | Prioridad |
|:---|:---:|:---|
| Fase 1 — R Engine Loader | 7 (R-01 a R-07) | Alta — empieza aquí |
| Fase 2 — Julia Engine Loader | 7 (J-01 a J-07) | Alta — después de Fase 1 |
| Fase 3 — Integración | 4 (INT-01 a INT-04) | Alta — cierre |
| **Total** | **18** | |

---

## Comando de retorno de emergencia

Si en cualquier momento algo sale mal irreversiblemente:
```bash
git checkout main
# Los binarios de producción en C:\NEVEN\ quedan intactos (v2.3)
# No hay ningún cambio en main hasta TASK-INT-04
```

*Lista de tareas — NEVEN v2.4 / agosto 2026*
