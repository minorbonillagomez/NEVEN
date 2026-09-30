# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN — NEVEN.pluto_read()
# Lee datos exportados desde un notebook Pluto/Julia de vuelta a Excel.
#
# Uso en celda Excel (función dinámica, derrama en rango):
#   =NEVEN.r("NEVEN.pluto_read(\"nombre\")")
#
# El notebook Pluto debe haber llamado previamente:
#   NEVEN.export_data("nombre", mi_dataframe)
#
# Archivo TSV generado en: C:\NEVEN\data\{nombre}.tsv
# ═══════════════════════════════════════════════════════════════════════════════

#' Lee datos exportados desde Pluto de vuelta a Excel
#'
#' @param nombre  Nombre del dataset exportado desde Pluto (sin .tsv).
#' @param dir     Directorio raíz de NEVEN. Por defecto C:/NEVEN/data.
#' @param header  Si el TSV tiene fila de encabezado (default TRUE).
#' @param sep     Separador de columnas (default "\\t" para TSV).
#' @return        Data.frame con los datos, o un mensaje de error en texto.
NEVEN.pluto_read <- function(nombre, dir = NULL, header = TRUE, sep = "\t") {

  # Determinar directorio de datos
  if (is.null(dir)) {
    neven_home <- Sys.getenv("NEVEN_HOME", unset = "C:/NEVEN")
    dir <- file.path(neven_home, "data")
  }

  # Construir ruta al TSV
  tsv_path <- file.path(dir, paste0(nombre, ".tsv"))

  if (!file.exists(tsv_path)) {
    # Intentar variante con guiones bajos (sanitización de Julia)
    safe_name <- gsub("[^A-Za-z0-9_\\-]", "_", nombre)
    tsv_path_alt <- file.path(dir, paste0(safe_name, ".tsv"))
    if (!file.exists(tsv_path_alt)) {
      return(paste0(
        "Error: no se encontró '", nombre, ".tsv' en ", dir, ".\n",
        "Asegúrese de que el notebook Pluto ejecutó NEVEN.export_data(\"",
        nombre, "\", datos) antes de llamar NEVEN.pluto_read."
      ))
    }
    tsv_path <- tsv_path_alt
  }

  # Leer el TSV
  tryCatch({
    df <- read.delim(tsv_path,
                     header    = header,
                     sep       = sep,
                     check.names = FALSE,
                     stringsAsFactors = FALSE,
                     encoding  = "UTF-8",
                     na.strings = c("", "NA", "missing", "nothing"))

    # Intentar convertir columnas numéricas automáticamente
    for (col in names(df)) {
      sup <- suppressWarnings(as.numeric(df[[col]]))
      if (!all(is.na(sup)) && sum(is.na(sup)) <= 0.1 * nrow(df)) {
        df[[col]] <- sup
      }
    }

    return(df)
  }, error = function(e) {
    return(paste0("Error al leer '", tsv_path, "': ", conditionMessage(e)))
  })
}

#' Lista los datasets disponibles exportados desde Pluto
#'
#' @param dir Directorio de datos. Por defecto C:/NEVEN/data.
#' @return    Data.frame con columnas: nombre, tamanio_kb, modificado.
NEVEN.pluto_list <- function(dir = NULL) {
  if (is.null(dir)) {
    neven_home <- Sys.getenv("NEVEN_HOME", unset = "C:/NEVEN")
    dir <- file.path(neven_home, "data")
  }

  if (!dir.exists(dir)) {
    return(data.frame(
      nombre = character(0),
      tamanio_kb = numeric(0),
      modificado = character(0),
      stringsAsFactors = FALSE
    ))
  }

  files <- list.files(dir, pattern = "\\.tsv$", full.names = FALSE)
  if (length(files) == 0) {
    return(data.frame(
      nombre = character(0),
      tamanio_kb = numeric(0),
      modificado = character(0),
      stringsAsFactors = FALSE
    ))
  }

  info <- file.info(file.path(dir, files))
  data.frame(
    nombre    = sub("\\.tsv$", "", files),
    tamanio_kb = round(info$size / 1024, 2),
    modificado = format(info$mtime, "%Y-%m-%d %H:%M:%S"),
    stringsAsFactors = FALSE
  )
}
