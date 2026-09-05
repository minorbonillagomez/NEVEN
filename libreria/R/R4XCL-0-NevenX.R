# =============================================================================
# NEVEN NevenX â€” Dispatcher genÃ©rico de procesos
# =============================================================================
#
# CONVENCIÃ“N UNIVERSAL DE POSICIONES (fija, sin depender de sidecars):
#
#   Pos 1  (A1)  : MÃ©todo       â€” nombre de la funciÃ³n R (string)
#   Pos 2  (A2)  : SetDatosY    â€” variable dependiente Y (rango)
#   Pos 3  (A3)  : SetDatosX    â€” variables independientes X (rango)
#   Pos 4  (A4)  : Escala       â€” 1=SI, 0=NO (default: 0)
#   Pos 5  (A5)  : Filtro       â€” vector filtro 0/1 (rango, opcional)
#   Pos 6  (A6)  : Constante    â€” 1=SI (default), 0=NO
#   Pos 7  (A7)  : Libre_1      â€” tercer rango (ej: Z instrumentos en 2SLS)
#   Pos 8  (A8)  : Libre_2      â€” cuarto rango (ej: X_exo en 2SLS)
#   Pos 9  (A9)  : Libre_3      â€” quinto rango (libre)
#   Pos 10 (A10) : Param_1      â€” parÃ¡metro escalar adicional
#   Pos 11 (A11) : Param_2      â€” parÃ¡metro escalar adicional
#   Pos 12 (A12) : Param_3      â€” parÃ¡metro escalar adicional
#   Pos 13 (A13) : Param_4      â€” parÃ¡metro escalar adicional
#   Pos 14 (A14) : Param_5      â€” parÃ¡metro escalar adicional
#   Pos 15 (A15) : TipoOutput   â€” Ãºltimo parÃ¡metro siempre (default: 1)
#
# EJEMPLOS:
#   =NevenX.R("MR_Lineal", A1:A50, B1:C50)                  â†’ TipoOutput=1
#   =NevenX.R("MR_Lineal", A1:A50, B1:C50, , , , , , , , , , , , 7)  â†’ TipoOutput=7
#   =NevenX.R("MR_Lineal", A1:A50, B1:C50, 1)               â†’ Escala=SI
#   =NevenX.R("MR_2SLS",   A1:A50, B1:C50, , , , D1:D50)    â†’ Z en pos 7
#
# NOMBRES QUE RECIBEN LAS FUNCIONES R (mapeo de posiciÃ³n â†’ parÃ¡metro):
#   A2 â†’ SetDatosY  (funciones XLL legacy) / data_Y (funciones Studio)
#   A3 â†’ SetDatosX  (funciones XLL legacy) / data_X (funciones Studio)
#   A4 â†’ Escala     (0/1)
#   A5 â†’ Filtro     (vector)
#   A6 â†’ Constante  (0/1)
#   A7 â†’ el tercer rol del proceso (Z, Endo, Variable_i, etc.)
#   A8 â†’ el cuarto rol (Exo, Variable_t, etc.)
#   A9 â†’ el quinto rol (libre)
#   A10..A14 â†’ parÃ¡metros escalares adicionales (Param_1..Param_5)
#   A15 â†’ TipoOutput
# =============================================================================

# â”€â”€ Tabla de mapeo universal (posiciÃ³n Aâ†’nombre R) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
.NEVENX_POS_MAP <- c(
  a0  = "proceso_interno",  # a0 = nombre del proceso (ya procesado)
  a1  = "SetDatosY",        # pos 2 = Y
  a2  = "SetDatosX",        # pos 3 = X
  a3  = "Escala",           # pos 4 = Escala (0/1)
  a4  = "Filtro",           # pos 5 = Filtro
  a5  = "Constante",        # pos 6 = Constante (0/1)
  a6  = "Libre_1",          # pos 7 = tercer rango libre
  a7  = "Libre_2",          # pos 8 = cuarto rango libre
  a8  = "Libre_3",          # pos 9 = quinto rango libre
  a9  = "Param_1",          # pos 10
  a10 = "Param_2",          # pos 11
  a11 = "Param_3",          # pos 12
  a12 = "Param_5",          # pos 13
  a13 = "TipoOutput"        # pos 14 â€” SIEMPRE el Ãºltimo (a14 no se usa)
)

# â”€â”€ Mapeo semÃ¡ntico del tercer rol segÃºn el proceso â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# El tercer rango (a6/Libre_1) varÃ­a segÃºn la funciÃ³n:
# - MR_2SLS: Instrumentos / data_Instru
# - MR_PanelData: Variable_i
# - etc.
# Los sidecars JSON pueden sobreescribir esto via "third_role_name"
.NEVENX_THIRD_ROLE <- list(
  "MR_2SLS"      = list(a6 = "SetInstrumentos", a7 = "SetDatosExo"),
  "RG_2SLS"      = list(a6 = "data_Instru",     a7 = "data_Exo"),
  "MR_PanelData" = list(a6 = "Variable_i",      a7 = "Variable_t"),
  "RG_DatosPanel"= list(a6 = "data_I",          a7 = "data_T"),
  "ST_VAR"       = list(a1 = "data_Series"),     # VAR: solo un rango multi-columna
  "ST_ECM"       = list(a1 = "data_Series")
)

# â”€â”€ Leer sidecar .json â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
.nevenx_get_sidecar <- function(proceso) {
  functions_dir <- "C:\\NEVEN\\functions"
  if (!dir.exists(functions_dir)) return(NULL)

  json_files <- list.files(functions_dir, pattern = "\\.json$", full.names = TRUE)
  strip <- function(s) toupper(gsub("^(RG_|ST_|AD_|GR_|DS_|UC_|MR_|J_)", "", s))

  for (f in json_files) {
    tryCatch({
      sidecar <- jsonlite::fromJSON(f, simplifyVector = FALSE)
      sid     <- sidecar[["id"]] %||% ""
      if (identical(sid, proceso))            return(sidecar)
      if (identical(strip(sid), strip(proceso))) return(sidecar)
    }, error = function(e) NULL)
  }
  return(NULL)
}

# â”€â”€ Detectar si un valor es "vacÃ­o" (Missing/NULL/NA/data.frame vacÃ­o) â”€â”€â”€â”€â”€â”€â”€â”€
.nevenx_is_empty <- function(val) {
  if (is.null(val))      return(TRUE)
  if (is.na(val[1]))     return(TRUE)
  if (is.data.frame(val) && (nrow(val) == 0 || ncol(val) == 0)) return(TRUE)
  if (is.character(val) && nchar(trimws(val[1])) == 0) return(TRUE)
  FALSE
}

# â”€â”€ Extraer escalar de XLOPER (puede venir como data.frame 1x1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
.nevenx_as_scalar <- function(val, type_fn = as.numeric, default = NULL) {
  if (.nevenx_is_empty(val)) return(default)
  tryCatch({
    if (is.data.frame(val)) val <- val[1, 1]
    type_fn(val)
  }, error = function(e) default)
}

# â”€â”€ Dispatcher principal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
.nevenx_dispatch <- function(proceso,
                              a0  = NULL, a1  = NULL, a2  = NULL,
                              a3  = NULL, a4  = NULL, a5  = NULL,
                              a6  = NULL, a7  = NULL, a8  = NULL,
                              a9  = NULL, a10 = NULL, a11 = NULL,
                              a12 = NULL, a13 = NULL, a14 = NULL) {

  # â”€â”€ 1. Normalizar nombre del proceso â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  proceso <- trimws(as.character(proceso))
  if (nchar(proceso) == 0)
    return(data.frame(R4XCL_Error = "NevenX: nombre del proceso vacÃ­o."))

  # â”€â”€ 2. Buscar la funciÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  fn <- NULL
  for (env in list(globalenv(), NEVEN, baseenv())) {
    if (exists(proceso, envir = env, inherits = FALSE)) {
      obj <- get(proceso, envir = env, inherits = FALSE)
      if (is.function(obj)) { fn <- obj; break }
    }
  }

  if (is.null(fn)) {
    todos    <- ls(globalenv())
    parecidos <- todos[agrep(proceso, todos, max.distance = 0.3)]
    sug <- if (length(parecidos) > 0)
      paste0(" Â¿Quisiste decir: ", paste(parecidos[1:min(3,length(parecidos))], collapse=", "), "?")
    else ""
    return(data.frame(R4XCL_Error = paste0(
      "NevenX: proceso '", proceso, "' no encontrado.", sug
    )))
  }

  # â”€â”€ 3. Extraer TipoOutput (posiciÃ³n fija: a14) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  TipoOutput <- .nevenx_as_scalar(a13, as.integer, default = 1L)
  # DIAGNOSTICO v2 — ver todos los args
  tryCatch({
    info <- paste0('[NevenX] ', proceso,
      ' | a0=', if(is.null(a0)) 'NULL' else 'DATA',
      ' | a1=', if(is.null(a1)) 'NULL' else 'DATA',
      ' | a11=', if(is.null(a11)) 'NULL' else paste(as.character(a11),collapse='|'),
      ' | a12=', if(is.null(a12)) 'NULL' else paste(as.character(a12),collapse='|'),
      ' | a13=', if(is.null(a13)) 'NULL' else paste(as.character(a13),collapse='|'),
      ' | a14=', if(is.null(a14)) 'NULL' else paste(as.character(a14),collapse='|'))
    write(info, file='C:/NEVEN/nevenx_diag.log', append=TRUE)
  }, error=function(e) NULL)

  # â”€â”€ 4. Mapeo de rangos segÃºn convenciÃ³n universal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  # ConvenciÃ³n fija base: a0=Y, a1=X, a2=Escala, a3=Filtro, a4=Constante, a5..a7=libres
  # Los roles del tercer/cuarto rango dependen del proceso (tabla .NEVENX_THIRD_ROLE)

  # Base: a0=SetDatosY, a1=SetDatosX
  y_name <- "SetDatosY"
  x_name <- "SetDatosX"

  # Si el proceso es una funciÃ³n Studio (.Studio.R), usar nombres data_Y / data_X
  if (grepl("\\.Studio$|^RG_|^ST_|^AD_", proceso)) {
    y_name <- "data_Y"
    x_name <- "data_X"
  }

  # Nombres para los rangos libres (a6, a7, a8)
  libre_names <- list(a6 = "Libre_1", a7 = "Libre_2", a8 = "Libre_3")
  if (proceso %in% names(.NEVENX_THIRD_ROLE)) {
    overrides <- .NEVENX_THIRD_ROLE[[proceso]]
    for (nm in names(overrides)) libre_names[[nm]] <- overrides[[nm]]
    # Si VAR/ECM usan el Y como "data_Series"
    if (!is.null(overrides[["a1"]])) y_name <- overrides[["a1"]]
  }

  # â”€â”€ 5. Construir lista de argumentos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  args <- list()

  # Y (a0)
  if (!.nevenx_is_empty(a0)) args[[y_name]] <- a0

  # X (a1)
  if (!.nevenx_is_empty(a1)) args[[x_name]] <- a1

  # Escala (a2) â€” escalar 0/1
  if (!.nevenx_is_empty(a2)) {
    v <- .nevenx_as_scalar(a2, as.integer)
    if (!is.null(v)) args[["Escala"]] <- v
  }

  # Filtro (a3) â€” rango
  if (!.nevenx_is_empty(a3)) args[["Filtro"]] <- a3

  # Constante (a4) â€” escalar 0/1
  if (!.nevenx_is_empty(a4)) {
    v <- .nevenx_as_scalar(a4, as.integer)
    if (!is.null(v)) args[["Constante"]] <- v
  }

  # Rangos libres (a5, a6, a7)
  libres <- list(a5 = libre_names[["a6"]],
                 a6 = libre_names[["a6"]],
                 a7 = libre_names[["a7"]],
                 a8 = libre_names[["a8"]])
  raw_libres <- list(a5 = a5, a6 = a6, a7 = a7, a8 = a8)
  for (pos in names(raw_libres)) {
    val <- raw_libres[[pos]]
    nm  <- libres[[pos]]
    if (!.nevenx_is_empty(val) && !is.null(nm)) args[[nm]] <- val
  }

  # ParÃ¡metros escalares adicionales (a9..a13)
  extra_params <- list(a9=a9, a10=a10, a11=a11, a12=a12, a13=a13)
  extra_names  <- paste0("Param_", 1:5)
  for (i in seq_along(extra_params)) {
    val <- extra_params[[i]]
    if (!.nevenx_is_empty(val)) {
      v <- .nevenx_as_scalar(val)
      if (!is.null(v)) args[[extra_names[i]]] <- v
    }
  }

  # TipoOutput â€” siempre al final
  args[["TipoOutput"]] <- TipoOutput

  # â”€â”€ 6. Filtrar args que la funciÃ³n no acepta â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  fn_params <- names(formals(fn))
  if (length(fn_params) > 0 && !("..." %in% fn_params)) {
    args <- args[names(args) %in% fn_params]
  }

  # â”€â”€ 7. Ejecutar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  # TipoOutput=0 es especial: retorna la lista de outputs disponibles.
  # Las funciones XLL evalÃºan TipoOutput DESPUÃ‰S de preparar los datos,
  # asÃ­ que si no hay datos los creamos mÃ­nimos (1 fila, 1 col) para
  # que la funciÃ³n llegue al bloque TipoOutput=0 sin error.
  if (isTRUE(TipoOutput == 0L)) {
    if (is.null(args[[y_name]]) || .nevenx_is_empty(args[[y_name]])) {
      # Datos ficticios mÃ­nimos: header + 2 filas numÃ©ricas
      dummy <- data.frame(Y = c(1, 2)); colnames(dummy) <- "Y_dummy"
      dummy_header <- rbind(colnames(dummy), dummy)
      args[[y_name]] <- dummy_header
    }
    if (!is.null(x_name) && (is.null(args[[x_name]]) || .nevenx_is_empty(args[[x_name]]))) {
      dummy <- data.frame(X = c(1, 2)); colnames(dummy) <- "X_dummy"
      dummy_header <- rbind(colnames(dummy), dummy)
      args[[x_name]] <- dummy_header
    }
  }

  tryCatch(
    do.call(fn, args),
    error = function(e) {
      data.frame(R4XCL_Error = paste0("NevenX ['", proceso, "']: ", conditionMessage(e)))
    }
  )
}

# â”€â”€ Registrar en NEVEN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if (exists("NEVEN") && is.environment(NEVEN)) {
  NEVEN$.nevenx_dispatch      <- .nevenx_dispatch
  NEVEN$.nevenx_get_sidecar   <- .nevenx_get_sidecar
  NEVEN$.NEVENX_POS_MAP       <- .NEVENX_POS_MAP
  NEVEN$.NEVENX_THIRD_ROLE    <- .NEVENX_THIRD_ROLE
}

if (!exists("%||%")) {
  `%||%` <- function(a, b) if (!is.null(a) && length(a) > 0) a else b
}

cat("[NevenX] Dispatcher v2 cargado â€” convenciÃ³n universal de posiciones activa\n")
