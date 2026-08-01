# NEVEN Development Standard Operating Procedures (SOP)

## 1. Arquitectura del Proyecto
NEVEN sigue un patrón de **Servicios Desacoplados**. El `RJ2XCL_Engine` actúa como orquestador central, delegando responsabilidades a servicios especializados:

- **RibbonService**: Gestión de la interfaz COM de Excel (Botones, Ribbon XML).
- **FileWatchService**: Vigilancia de directorios y recarga en caliente (Hot-Reload) de scripts.
- **LanguageManager**: Gestión del ciclo de vida de motores R y Julia.
- **CallbackDispatcher**: Enrutamiento de llamadas desde lenguajes externos hacia Excel.

## 2. Flujo de Desarrollo
### Añadir una nueva función de Excel
1. Definir la lógica en `basic_functions.h` (si es core) o en los servicios de lenguaje.
2. Asegurar que use `rj2xcl_integration_constants.h` para cualquier trigger de macro.

### Modificar la Comunicación (Pipes)
- La resiliencia está implementada en `LanguageService::Call`. Cualquier error de pipe dispara un reintento automático (`Connect` + `Initialize`).
- El tamaño del buffer es dinámico (8KB inicial, crece hasta 256KB si es necesario).

## 3. Pruebas y Validación
### Ejecutar Suite de Tests
```powershell
cd Build
cmake --build . --config Debug --target neven_tests
ctest -C Debug --output-on-failure
```

### Crear Nuevo Test
- Usar `MockExcelBridge` para simular la API de Excel sin necesidad de abrir la aplicación.
- Verificar conteos de llamadas con `mock_bridge->GetCallCount(xlfn)`.

## 4. Mejores Prácticas (Escuadrón BLAST)
- **RAII**: Usar siempre `std::unique_ptr` o `std::shared_ptr`. Evitar `new/delete` manual.
- **Strings**: No usar strings hardcodeados para integración. Usar `constants::k*`.
- **Thread Safety**: Las llamadas de retorno desde R/Julia deben ser marshalled a través de `HandleCallbackOnThread`.

---
*Documento generado tras el Sprint 5 de modernización.*

## 5. Agregar Función al Catálogo Data Lab

The Data Lab catalog (NEVEN Studio) uses a "two-file" convention: a Studio wrapper and a sidecar JSON.

### Step 1: Create the Studio wrapper

Create `NEVEN/libreria/R/MyFunction.Studio.R`:

```r
MyFunction.Studio <- function(data_X, Param1 = 3L) {
  # Validations
  if (!is.data.frame(data_X)) stop("'data_X' must be a data.frame.")

  # Analysis
  resultado <- list(
    results_table = analyze(data_X, Param1),
    summary_value = 42.5
  )

  # ALWAYS return r_object_to_slots()
  tier_map <- c(results_table = 1L, summary_value = 2L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
```

**Rules:**
- Function name MUST end in `.Studio`
- Input data MUST be received as `data_X` (and optionally `data_Y`, `data_T`, `data_ID`)
- MUST call `r_object_to_slots()` as the return value
- `r_object_to_slots` is already loaded in ControlR startup — do not source it

### Step 2: Create the sidecar JSON

Create `NEVEN/Install/functions/MyFunction.json`:

```json
{
  "id": "MyFunction",
  "family": "AD",
  "family_label": "Análisis de Datos",
  "name": "My Analysis",
  "description": "Brief description.",
  "languages": ["r"],
  "function_name": "MyFunction.Studio",
  "file": "MyFunction.Studio.R",
  "variable_roles": {
    "X": { "label": "Input variables", "types": ["numeric"], "multiple": true, "required": true }
  },
  "parameters": [
    { "name": "Param1", "label": "Parameter 1", "type": "integer", "default": 3, "tier": 1 }
  ]
}
```

**Tier values:** `1` = shown by default, `2` = in "Advanced" collapsible section.
**Parameter types:** `integer`, `boolean`, `select` (with `options` array).

### Step 3: Deploy to production

```powershell
Copy-Item "NEVEN\libreria\R\MyFunction.Studio.R" "C:\NEVEN\functions\" -Force
Copy-Item "NEVEN\Install\functions\MyFunction.json" "C:\NEVEN\functions\" -Force
# Restart NEVEN Studio — catalog updates automatically
```

### Step 4: Validate

Open NEVEN Studio → Data Lab → select the family → verify the function appears → assign columns → execute → check results render correctly.

---
*Section added: July 2026*
