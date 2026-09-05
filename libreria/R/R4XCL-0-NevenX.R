# =============================================================================
# NEVEN NevenX -- Dispatcher generico de procesos v5
# =============================================================================
# CONVENCION UNIVERSAL DE POSICIONES (verificada empiricamente):
#   Pos 1  (proceso) : Metodo
#   Pos 2  (a0)      : SetDatosY / data_Y
#   Pos 3  (a1)      : SetDatosX / data_X
#   Pos 4  (a2)      : TipoOutput  (entero, default 1) -- SIEMPRE pos 4
#   Pos 5  (a3)      : Escala      (0/1, default 0)
#   Pos 6  (a4)      : Filtro      (rango, opcional)
#   Pos 7  (a5)      : Constante   (0/1, default 1)
#   Pos 8  (a6)      : Libre_1     (tercer rango, ej: Z instrumentos)
#   Pos 9  (a7)      : Libre_2     (cuarto rango)
#   Pos 10 (a8)      : Libre_3     (quinto rango)
#   Pos 11 (a9)      : Param_1     (escalar adicional)
#   Pos 12 (a10)     : Param_2     (escalar adicional)
#   Pos 13 (a11)     : Param_3     (escalar adicional)
#
# TIPOOUTPUT=0 -- IntelliSense dinamico:
#   Retorna DOS tablas desde el sidecar JSON del proceso:
#   Tabla 1: parametros de entrada (posicion, nombre, descripcion, tipo, default)
#   Tabla 2: TipoOutputs disponibles (id, descripcion)
# =============================================================================

.NEVENX_THIRD_ROLE <- list(
  "MR_2SLS"         = list(a6 = "SetInstrumentos", a7 = "SetDatosExo"),
  "RG_2SLS"         = list(a6 = "data_Instru",     a7 = "data_Exo"),
  "MR_PanelData"    = list(a6 = "Variable_i",      a7 = "Variable_t"),
  "MR_PanelData.C"  = list(a6 = "Variable_i",      a7 = "Variable_t"),
  "RG_DatosPanel"   = list(a6 = "data_I",          a7 = "data_T"),
  "ST_VAR"          = list(a0 = "data_Series"),
  "ST_ECM"          = list(a0 = "data_Series")
)

.NEVENX_POS_LABELS <- list(
  a0  = list(name="SetDatosY",  label="Variable dependiente Y",               type="range",   default="requerido"),
  a1  = list(name="SetDatosX",  label="Variables independientes X",            type="range",   default="requerido"),
  a3  = list(name="Escala",     label="Estandarizar variables X (0=No, 1=Si)", type="boolean", default="0"),
  a4  = list(name="Filtro",     label="Excluir observaciones (0=incluir)",     type="range",   default="NULL"),
  a5  = list(name="Constante",  label="Incluir intercepto (0=No, 1=Si)",      type="boolean", default="1"),
  a6  = list(name="Libre_1",    label="Rango libre 1",                         type="range",   default="NULL"),
  a7  = list(name="Libre_2",    label="Rango libre 2",                         type="range",   default="NULL"),
  a8  = list(name="Libre_3",    label="Rango libre 3",                         type="range",   default="NULL"),
  a9  = list(name="Param_1",    label="Parametro escalar 1",                   type="scalar",  default="NULL"),
  a10 = list(name="Param_2",    label="Parametro escalar 2",                   type="scalar",  default="NULL"),
  a11 = list(name="Param_3",    label="Parametro escalar 3",                   type="scalar",  default="NULL")
)

.nevenx_is_empty <- function(val) {
  if (is.null(val)) return(TRUE)
  if (length(val) == 0) return(TRUE)
  if (is.data.frame(val) && (nrow(val) == 0 || ncol(val) == 0)) return(TRUE)
  if (is.character(val) && nchar(trimws(paste(val, collapse=""))) == 0) return(TRUE)
  v1 <- tryCatch(val[1,1], error=function(e) val[1])
  if (is.na(v1)) return(TRUE)
  FALSE
}

.nevenx_as_scalar <- function(val, type_fn = as.numeric, default = NULL) {
  if (.nevenx_is_empty(val)) return(default)
  tryCatch({
    v <- if (is.data.frame(val)) val[1,1] else val[1]
    type_fn(v)
  }, error = function(e) default)
}

.nevenx_load_sidecar <- function(proceso) {
  neven_home <- Sys.getenv("NEVEN_HOME", "C:/NEVEN")
  fn_dir <- file.path(neven_home, "functions")
  jsons <- list.files(fn_dir, pattern="\\.json$", full.names=TRUE)
  result <- NULL
  for (jf in jsons) {
    tryCatch({
      j <- jsonlite::fromJSON(jf, simplifyVector=FALSE)
      xll_name <- j[["function_name_xll"]]
      if (!is.null(xll_name) && trimws(xll_name) == proceso) {
        result <- j
      }
    }, error=function(e) NULL)
    if (!is.null(result)) break
  }
  result
}

.nevenx_ayuda <- function(proceso, sidecar, libre_map) {
  pos_labels <- .NEVENX_POS_LABELS

  # Sobreescribir con nevenx_positions del sidecar si existe
  if (!is.null(sidecar)) {
    np <- sidecar[["nevenx_positions"]]
    if (!is.null(np)) {
      for (slot in names(np)) {
        entry <- np[[slot]]
        def_raw <- entry[["default"]]
        req <- entry[["required"]]
        def_label <- if (isTRUE(req)) "requerido" else if (is.null(def_raw)) "NULL" else as.character(def_raw)
        pos_labels[[slot]] <- list(
          name    = entry[["name"]],
          label   = entry[["label"]],
          type    = entry[["type"]],
          default = def_label
        )
      }
    }
    # Sobreescribir nombres de rangos libres con THIRD_ROLE
    for (slot in c("a6","a7","a8")) {
      nm <- libre_map[[slot]]
      if (!is.null(nm) && !grepl("^Libre_", nm)) {
        if (!is.null(pos_labels[[slot]])) {
          pos_labels[[slot]][["name"]] <- nm
        }
      }
    }
  }

  # --- Tabla 1: parametros de entrada ---
  pos_nums <- c(a0=2, a1=3, a3=5, a4=6, a5=7, a6=8, a7=9, a8=10, a9=11, a10=12, a11=13)

  rows <- list()
  rows[[1]] <- data.frame(
    Posicion    = "---",
    Nombre      = "PARAMETROS DE ENTRADA",
    Descripcion = paste0("=NevenX.R(\"", proceso, "\", ...)"),
    Tipo        = "---",
    Default     = "---",
    stringsAsFactors = FALSE
  )
  rows[[2]] <- data.frame(
    Posicion    = "4",
    Nombre      = "TipoOutput",
    Descripcion = "Tipo de resultado (ver tabla siguiente)",
    Tipo        = "entero",
    Default     = "1",
    stringsAsFactors = FALSE
  )
  for (slot in names(pos_nums)) {
    info <- pos_labels[[slot]]
    if (is.null(info)) next
    rows[[length(rows)+1]] <- data.frame(
      Posicion    = as.character(pos_nums[[slot]]),
      Nombre      = info[["name"]],
      Descripcion = info[["label"]],
      Tipo        = info[["type"]],
      Default     = info[["default"]],
      stringsAsFactors = FALSE
    )
  }
  t1 <- do.call(rbind, rows)
  t1 <- t1[order(as.integer(ifelse(t1$Posicion == "---", "0", t1$Posicion))), ]
  rownames(t1) <- NULL

  # --- Separador ---
  sep <- data.frame(Posicion="", Nombre="", Descripcion="", Tipo="", Default="",
                    stringsAsFactors=FALSE)

  # --- Tabla 2: TipoOutputs disponibles ---
  t2_rows <- list()
  t2_rows[[1]] <- data.frame(
    Posicion    = "---",
    Nombre      = "TIPOOUTPUTS DISPONIBLES",
    Descripcion = paste0("Usar en Pos 4 de =NevenX.R(\"", proceso, "\", ...)"),
    Tipo        = "---",
    Default     = "---",
    stringsAsFactors = FALSE
  )

  to_list <- if (!is.null(sidecar)) sidecar[["tipo_outputs"]] else NULL
  if (!is.null(to_list) && length(to_list) > 0) {
    for (item in to_list) {
      t2_rows[[length(t2_rows)+1]] <- data.frame(
        Posicion    = as.character(item[["id"]]),
        Nombre      = "",
        Descripcion = item[["label"]],
        Tipo        = "",
        Default     = "",
        stringsAsFactors = FALSE
      )
    }
  } else {
    t2_rows[[2]] <- data.frame(
      Posicion="?", Nombre="", Descripcion="Sin sidecar -- llamar con datos para ver outputs",
      Tipo="", Default="", stringsAsFactors=FALSE
    )
  }
  t2 <- do.call(rbind, t2_rows)
  rownames(t2) <- NULL

  rbind(t1, sep, t2)
}

.nevenx_dispatch <- function(proceso,
    a0=NULL, a1=NULL, a2=NULL, a3=NULL, a4=NULL,
    a5=NULL, a6=NULL, a7=NULL, a8=NULL, a9=NULL,
    a10=NULL, a11=NULL, a12=NULL, a13=NULL, a14=NULL) {

  proceso <- trimws(as.character(proceso))
  if (nchar(proceso) == 0) {
    return(data.frame(R4XCL_Error = "NevenX: nombre del proceso vacio."))
  }

  # Buscar funcion en globalenv y NEVEN
  fn <- NULL
  envs <- list(globalenv())
  if (exists("NEVEN", envir=globalenv(), inherits=FALSE) &&
      is.environment(get("NEVEN", envir=globalenv(), inherits=FALSE))) {
    envs <- c(envs, list(get("NEVEN", envir=globalenv(), inherits=FALSE)))
  }
  for (env in envs) {
    if (exists(proceso, envir=env, inherits=FALSE)) {
      obj <- get(proceso, envir=env, inherits=FALSE)
      if (is.function(obj)) {
        fn <- obj
        break
      }
    }
  }
  if (is.null(fn)) {
    todos <- ls(globalenv())
    parecidos <- todos[agrep(proceso, todos, max.distance=0.3)]
    sug <- if (length(parecidos) > 0) {
      paste0(" Quisiste decir: ", paste(parecidos[1:min(3,length(parecidos))], collapse=", "), "?")
    } else {
      ""
    }
    return(data.frame(R4XCL_Error = paste0("NevenX: proceso '", proceso, "' no encontrado.", sug)))
  }

  # TipoOutput -- posicion a2 (pos 4) -- FIJA
  # EXCEPCION: si a0 es escalar (no data.frame) significa que el usuario
  # llamo sin datos (ej: =NevenX.R("MR_Lineal",,, 0)) y Excel comprimo
  # las comas vacias -- el escalar aterriza en a0.
  TipoOutput <- .nevenx_as_scalar(a2, as.integer, default=1L)
  if (!is.null(a0) && !is.data.frame(a0) && is.numeric(a0) && length(a0) == 1) {
    TipoOutput <- as.integer(a0)
    a0 <- NULL
    a1 <- NULL
  }

  # Nombres de Y y X segun tipo de funcion
  y_name <- "SetDatosY"
  x_name <- "SetDatosX"
  if (grepl("\\.Studio$|^RG_|^ST_|^AD_", proceso)) {
    y_name <- "data_Y"
    x_name <- "data_X"
  }

  # Nombres para rangos libres (fallback hardcodeado)
  libre_map <- list(a6="Libre_1", a7="Libre_2", a8="Libre_3")
  if (proceso %in% names(.NEVENX_THIRD_ROLE)) {
    overrides <- .NEVENX_THIRD_ROLE[[proceso]]
    for (nm in names(overrides)) {
      libre_map[[nm]] <- overrides[[nm]]
    }
    if (!is.null(overrides[["a0"]])) {
      y_name <- overrides[["a0"]]
    }
  }

  # TipoOutput=0 -- retornar ayuda desde sidecar
  if (isTRUE(TipoOutput == 0L)) {
    sidecar <- tryCatch(
      .nevenx_load_sidecar(proceso),
      error = function(e) NULL
    )
    resultado <- tryCatch(
      .nevenx_ayuda(proceso, sidecar, libre_map),
      error = function(e) data.frame(
        R4XCL_Error = paste0("NevenX ayuda: ", conditionMessage(e))
      )
    )
    return(resultado)
  }

  # -------------------------------------------------------------------------
  # Flujo normal (TipoOutput != 0)
  # -------------------------------------------------------------------------

  args <- list()
  if (!.nevenx_is_empty(a0)) args[[y_name]] <- a0
  if (!.nevenx_is_empty(a1)) args[[x_name]] <- a1

  if (!.nevenx_is_empty(a3)) {
    v <- .nevenx_as_scalar(a3, as.integer)
    if (!is.null(v)) args[["Escala"]] <- v
  }

  # Filtro: recortar al mismo nrow que Y si el rango es mas grande
  if (!.nevenx_is_empty(a4)) {
    filtro_df <- a4
    if (is.data.frame(filtro_df) && !.nevenx_is_empty(a0) && is.data.frame(a0)) {
      nY <- nrow(a0)
      if (nrow(filtro_df) > nY) {
        filtro_df <- filtro_df[seq_len(nY), , drop=FALSE]
      }
    }
    args[["Filtro"]] <- filtro_df
  }

  if (!.nevenx_is_empty(a5)) {
    v <- .nevenx_as_scalar(a5, as.integer)
    if (!is.null(v)) args[["Constante"]] <- v
  }

  for (pos in c("a6","a7","a8")) {
    val <- tryCatch(get(pos, envir=environment(), inherits=FALSE), error=function(e) NULL)
    if (!.nevenx_is_empty(val) && !is.null(libre_map[[pos]])) {
      args[[libre_map[[pos]]]] <- val
    }
  }

  extra_pos   <- c("a9","a10","a11")
  extra_names <- paste0("Param_", 1:3)
  for (i in seq_along(extra_pos)) {
    val <- tryCatch(get(extra_pos[i], envir=environment(), inherits=FALSE), error=function(e) NULL)
    if (!.nevenx_is_empty(val)) {
      v <- .nevenx_as_scalar(val)
      if (!is.null(v)) args[[extra_names[i]]] <- v
    }
  }

  args[["TipoOutput"]] <- TipoOutput

  # Filtrar solo parametros que la funcion acepta
  fn_params <- names(formals(fn))
  if (length(fn_params) > 0 && !("..." %in% fn_params)) {
    args <- args[names(args) %in% fn_params]
  }

  tryCatch(
    do.call(fn, args),
    error = function(e) data.frame(
      R4XCL_Error = paste0("NevenX ['", proceso, "']: ", conditionMessage(e))
    )
  )
}

if (exists("NEVEN", envir=globalenv(), inherits=FALSE) &&
    is.environment(get("NEVEN", envir=globalenv(), inherits=FALSE))) {
  neven_env <- get("NEVEN", envir=globalenv(), inherits=FALSE)
  assign(".nevenx_dispatch",      .nevenx_dispatch,      envir=neven_env)
  assign(".NEVENX_THIRD_ROLE",    .NEVENX_THIRD_ROLE,    envir=neven_env)
  assign(".nevenx_load_sidecar",  .nevenx_load_sidecar,  envir=neven_env)
  assign(".nevenx_ayuda",         .nevenx_ayuda,         envir=neven_env)
}

cat("[NevenX] Dispatcher v5 listo -- TipoOutput=0 con sidecar unificado\n")
