# ===============================================================================
# NEVEN Data Lab — Cargador de Datasets Wooldridge
# Este wrapper NO analiza datos; serializa el dataset para que Python
# lo cargue en DuckDB, haciéndolo disponible para análisis posteriores.
# Requiere: r_object_to_slots.R, jsonlite
# ===============================================================================

DS_Wooldridge.Studio <- function(Dataset = "wage1") {

  if (!requireNamespace("wooldridge", quietly = TRUE)) {
    stop("Paquete 'wooldridge' requerido. Instale con: install.packages('wooldridge')")
  }

  Dataset <- as.character(Dataset)

  # Validar que el dataset existe
  available <- data(package = "wooldridge")$results[, "Item"]
  if (!(Dataset %in% available)) {
    stop(paste0("Dataset '", Dataset, "' no encontrado en el paquete wooldridge. ",
                "Datasets disponibles: ", paste(head(available, 10), collapse=", "), "..."))
  }

  # Cargar el dataset
  env <- new.env(parent = emptyenv())
  data(list = Dataset, package = "wooldridge", envir = env)
  df <- get(Dataset, envir = env)
  df <- as.data.frame(df)

  # Extraer descripcion del dataset
  descripciones <- list(
    wage1       = "Salarios, educacion y experiencia de trabajadores de EEUU (1976)",
    mroz        = "Participacion laboral femenina, horas y salarios (1975)",
    crime1      = "Criminalidad individual, arresto y condena (NLS 1986)",
    gpa1        = "Calificaciones universitarias y variables socioeconómicas",
    bwght       = "Peso al nacer y factores de riesgo (NLSY 1988)",
    beauty      = "Salarios y atractivo fisico (Hamermesh & Biddle)",
    card        = "Retornos a la educacion con variable instrumental (Card 1995)",
    hprice1     = "Precios de viviendas y caracteristicas del vecindario",
    kielmc      = "Efecto de incinerador sobre precios de casas",
    wage2       = "Salarios, IQ, educacion y experiencia (NLS 1980)",
    jtrain      = "Impacto de entrenamiento laboral sobre salarios",
    beveridge   = "Curva de Beveridge: vacantes y desempleo EEUU",
    intdef      = "Tasas de interes y deficit fiscal EEUU (series anuales)",
    hseinv      = "Inversion en vivienda y precios relativos EEUU",
    fertil3     = "Fertilidad y politica economica EEUU 1913-1984",
    approval    = "Aprobacion presidencial y variables macroeconomicas",
    airfare     = "Tarifas aereas y competencia de rutas EEUU",
    alcohol     = "Consumo de alcohol y salarios (NLSY)",
    catholic    = "Efecto de escuelas católicas en logros academicos",
    affairs     = "Frecuencia de aventuras extramatrimoniales (Fair 1978)"
  )

  desc <- if (Dataset %in% names(descripciones)) {
    descripciones[[Dataset]]
  } else {
    paste0("Dataset '", Dataset, "' del paquete wooldridge (Introduccion a la Econometria)")
  }

  # Preview: primeras 20 filas
  n_show  <- min(20L, nrow(df))
  preview <- df[1:n_show, , drop = FALSE]

  # Metadata
  col_types <- sapply(df, function(x) {
    if (is.numeric(x)) "numeric" else if (is.logical(x)) "logical" else "text"
  })
  col_info <- data.frame(
    Columna = names(df),
    Tipo    = col_types,
    N_NAs   = sapply(df, function(x) sum(is.na(x))),
    stringsAsFactors = FALSE
  )
  rownames(col_info) <- NULL

  # Serializar el dataset completo como JSON para que Python lo cargue en DuckDB
  # Se usa un marcador especial __NEVEN_LOAD_DATASET__ para que el handler
  # lo detecte y lo inserte en DuckDB en lugar de mostrarlo como slot normal
  dataset_json <- jsonlite::toJSON(df, dataframe = "rows", auto_unbox = TRUE,
                                    na = "null", digits = 6)
  dataset_b64  <- jsonlite::base64_enc(
    iconv(as.character(dataset_json), from = "UTF-8", to = "UTF-8", sub = "byte")
  )

  load_marker <- paste0(
    '<html><body><neven-load-dataset name="', Dataset, '">',
    dataset_b64,
    '</neven-load-dataset></body></html>'
  )

  resultado <- list(
    carga_dataset  = load_marker,
    columnas       = col_info,
    preview        = preview
  )

  tier_map <- c(carga_dataset = 1L, columnas = 1L, preview = 1L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
