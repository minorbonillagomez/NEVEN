# NevenX — Diseño Técnico

## Arquitectura completa

```
Excel (usuario escribe =NevenX.R("MR_2SLS", A1:A50, B1:C50, D1:D50))
         │
         ▼
NEVEN64.xll — NevenX_R()
  • Extrae "MR_2SLS" del primer Q parámetro
  • Los rangos R1..R5 llegan como xltypeMulti (tipo Q — ya materializados)
  • Los parámetros P1..P5 llegan como escalares
  • Construye Protobuf: function_call { function="NEVEN$.nevenx_dispatch", args=["MR_2SLS", R1, R2, R3, TipoOutput] }
  • Envía por Named Pipe a ControlR.exe
         │
         ▼
ControlR.exe — RCallSEXP()
  • Recibe function_call con function="NEVEN$.nevenx_dispatch"
  • Llama do.call("NEVEN$.nevenx_dispatch", list("MR_2SLS", data_R1, data_R2, data_R3, TipoOutput=1))
         │
         ▼
R — NEVEN$.nevenx_dispatch("MR_2SLS", data_R1, data_R2, data_R3, TipoOutput=1)
  • Lee C:\NEVEN\functions\*.json buscando id="MR_2SLS" (o "RG_2SLS")
  • Encuentra variable_roles: { "Y": "R1", "Endo": "R2", "Instru": "R3" }
  • Llama do.call("MR_2SLS", list(data_Y=data_R1, data_Endo=data_R2, data_Instru=data_R3, TipoOutput=1))
  • MR_2SLS() ejecuta y retorna data.frame
         │
         ▼
ControlR.exe — SEXPToVariable()
  • Serializa el data.frame a Protobuf Variable
         │
         ▼
NEVEN64.xll — Convert::VariableToXLOPER()
  • Convierte a XLOPER12 y retorna a Excel
         │
         ▼
Excel — muestra el resultado en la celda
```

---

## Implementación C++

### Función `NevenX_R` (nueva, en `basic_functions.cc`)

```cpp
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI
NevenX_R(LPXLOPER12 proceso,
            LPXLOPER12 r1 = nullptr, LPXLOPER12 r2 = nullptr,
            LPXLOPER12 r3 = nullptr, LPXLOPER12 r4 = nullptr,
            LPXLOPER12 r5 = nullptr,
            LPXLOPER12 p1 = nullptr, LPXLOPER12 p2 = nullptr,
            LPXLEXP12 p3 = nullptr, LPXLOPER12 p4 = nullptr,
            LPXLOPER12 p5 = nullptr,
            LPXLOPER12 tipo_output = nullptr) {
    
    // El primer arg es el nombre del proceso — pasa como arg0 de NEVEN$.nevenx_dispatch
    // Los rangos R1..R5 y parámetros P1..P5 pasan como arg1..arg11
    // TipoOutput pasa como arg12
    
    // Construir un XLOPER12 con el nombre del dispatcher
    static XLOPER12 dispatcher_name;
    Convert::StringToXLOPER(&dispatcher_name, "NEVEN$.nevenx_dispatch", false);
    
    return RJ_Call_Generic(
        0,  // language_key = 0 → R
        &dispatcher_name,
        proceso, r1, r2, r3, r4, r5, p1, p2, p3, p4, p5, tipo_output,
        nullptr, nullptr, nullptr  // padding hasta 16
    );
}
```

### Entrada en funcTemplates

```cpp
{ L"NevenX_R", L"UQQQQQQQQQQQQQ",
  L"NevenX.R",
  L"Proceso,DatosY,DatosX,Datos3,Datos4,Datos5,Param1,Param2,Param3,Param4,Param5,TipoOutput",
  L"1", L"NEVEN", L"", L"",
  L"Ejecuta un proceso R del catálogo NEVEN con rangos de Excel",
  L"Nombre del proceso (ej: MR_2SLS, MR_Lineal)",
  L"Rango de datos Y / primer rol",
  L"Rango de datos X / segundo rol",
  L"Rango adicional 3 (opcional)",
  L"Rango adicional 4 (opcional)",
  L"Rango adicional 5 (opcional)",
  L"" },
```

---

## Implementación R — Dispatcher

### `NEVEN$.nevenx_dispatch` (en `R4XCL-0-Interno-1.R` o nuevo `R4XCL-0-NevenX.R`)

```r
.nevenx_dispatch <- function(proceso,
                              R1 = NULL, R2 = NULL, R3 = NULL, R4 = NULL, R5 = NULL,
                              P1 = NULL, P2 = NULL, P3 = NULL, P4 = NULL, P5 = NULL,
                              TipoOutput = 1) {
  
  # 1. Validar que el proceso existe en el entorno
  proceso <- as.character(proceso)
  
  if (!exists(proceso, envir = .GlobalEnv, inherits = TRUE)) {
    return(data.frame(
      R4XCL_Error = paste0("Proceso '", proceso, "' no encontrado. ",
                           "Verifique que el archivo .R esté en C:\\NEVEN\\functions\\")
    ))
  }
  
  fn <- get(proceso, envir = .GlobalEnv, inherits = TRUE)
  
  if (!is.function(fn)) {
    return(data.frame(R4XCL_Error = paste0("'", proceso, "' no es una función.")))
  }
  
  # 2. Leer catálogo para obtener mapeo semántico de rangos
  roles <- .nevenx_get_roles(proceso)
  
  # 3. Construir lista de argumentos con nombres semánticos
  raw_args <- list(R1=R1, R2=R2, R3=R3, R4=R4, R5=R5,
                   P1=P1, P2=P2, P3=P3, P4=P4, P5=P5,
                   TipoOutput=TipoOutput)
  
  named_args <- .nevenx_map_args(raw_args, roles)
  
  # 4. Eliminar NULLs y xltypeMissing
  named_args <- Filter(Negate(is.null), named_args)
  
  # 5. Ejecutar
  tryCatch(
    do.call(fn, named_args),
    error = function(e) {
      data.frame(R4XCL_Error = paste0("Error en ", proceso, ": ", conditionMessage(e)))
    }
  )
}

# Lee el sidecar JSON y retorna el mapeo de roles
.nevenx_get_roles <- function(proceso) {
  catalog_dir <- "C:\\NEVEN\\functions"
  
  # Buscar sidecar: primero por id exacto, luego por función compatible
  json_files <- list.files(catalog_dir, pattern = "\\.json$", full.names = TRUE)
  
  for (f in json_files) {
    tryCatch({
      sidecar <- jsonlite::fromJSON(f)
      if (!is.null(sidecar$id) && sidecar$id == proceso) {
        return(sidecar$variable_roles)
      }
      # También aceptar si el nombre de la función coincide sin prefijo familia
      # ej: proceso="MR_Lineal" pero id en JSON = "RG_Lineal"
      fn_name <- gsub("^(MR_|ST_|AD_|GR_)", "", proceso)
      json_id  <- gsub("^(RG_|ST_|AD_|GR_|DS_|UC_)", "", sidecar$id %||% "")
      if (toupper(fn_name) == toupper(json_id)) {
        return(sidecar$variable_roles)
      }
    }, error = function(e) NULL)
  }
  
  return(NULL)  # Sin sidecar → usar convención por defecto
}

# Mapea R1..R5, P1..P5 a nombres semánticos según variable_roles del sidecar
.nevenx_map_args <- function(raw_args, roles) {
  
  if (is.null(roles)) {
    # Sin sidecar: convención por defecto
    # R1=SetDatosY / data_Y, R2=SetDatosX / data_X, R3=data_Z / data_Instru
    defaults <- list(
      R1 = "data_Y",  R2 = "data_X",  R3 = "data_Z",
      R4 = "data_4",  R5 = "data_5",
      P1 = "Param1",  P2 = "Param2",  P3 = "Param3",
      P4 = "Param4",  P5 = "Param5",
      TipoOutput = "TipoOutput"
    )
    roles <- defaults
  }
  
  # Los variable_roles del JSON mapean nombre_semántico → posición ("R1", "R2", etc.)
  # Invertimos: posición → nombre_semántico
  pos_to_name <- list()
  for (role_name in names(roles)) {
    pos <- roles[[role_name]]
    if (is.character(pos) && nchar(pos) > 0) {
      pos_to_name[[pos]] <- role_name
    }
  }
  
  named <- list()
  for (pos in names(raw_args)) {
    val <- raw_args[[pos]]
    if (is.null(val) || (is.list(val) && length(val) == 0)) next
    
    sem_name <- pos_to_name[[pos]]
    if (!is.null(sem_name)) {
      named[[sem_name]] <- val
    } else if (pos == "TipoOutput") {
      named[["TipoOutput"]] <- as.integer(val)
    }
    # Si no hay mapeo para esta posición y no es NULL, omitir silenciosamente
  }
  
  return(named)
}

# Helper: operador %||% (NULL-coalescing)
`%||%` <- function(a, b) if (!is.null(a)) a else b

# Registrar en el entorno NEVEN
if (exists("NEVEN") && is.environment(NEVEN)) {
  NEVEN$.nevenx_dispatch   <- .nevenx_dispatch
  NEVEN$.nevenx_get_roles  <- .nevenx_get_roles
  NEVEN$.nevenx_map_args   <- .nevenx_map_args
}
```

---

## Mapeo de variable_roles del JSON al dispatcher

El JSON sidecar actual usa este formato:
```json
{
  "variable_roles": {
    "Y":      { "label": "Variable dependiente", "types": ["numeric"] },
    "Endo":   { "label": "Variables endógenas",  "types": ["numeric"] },
    "Instru": { "label": "Instrumentos Z",       "types": ["numeric"] }
  }
}
```

Para `NevenX`, el sidecar necesita agregar el campo `"position"` que indica qué Rn usar:
```json
{
  "variable_roles": {
    "Y":      { "label": "Variable dependiente", "position": "R1" },
    "Endo":   { "label": "Variables endógenas",  "position": "R2" },
    "Instru": { "label": "Instrumentos Z",       "position": "R3" },
    "Exo":    { "label": "Controles exógenos",   "position": "R4", "required": false }
  },
  "parameters": [
    { "name": "NivelAlpha",   "position": "P1", "default": 0.05 },
    { "name": "DiagnosticosF","position": "P2", "default": true  }
  ]
}
```

Los sidecars existentes se actualizan gradualmente. Mientras no tienen `position`, el dispatcher usa la convención por defecto (R1=Y, R2=X, R3=Z).

---

## Ventajas sobre el modelo actual

| Característica | Funciones específicas (hoy) | NevenX (nuevo) |
|---|---|---|
| Agregar función nueva | R + C++ + recompilar | Solo R + JSON |
| IntelliSense | Completo, estático | Genérico (Fase 1), dinámico (Fase 3) |
| Rangos como objetos Excel | ✅ | ✅ |
| Recálculo automático | ✅ | ✅ |
| Extensible por usuario | ❌ | ✅ |
| Extensible por agente IA | ❌ | ✅ |
| Catálogo unificado | Parcial | ✅ mismo JSON para Studio y XLL |
