# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Script de migración: attr(fn, "description") → sidecar JSON
# Uso: Rscript migrate_attr_to_json.R [directorio]
# ═══════════════════════════════════════════════════════════════════════════════

if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop("El paquete 'jsonlite' es necesario. Instálelo con: install.packages('jsonlite')")
}

# ── Directorio de trabajo ────────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)
functions_dir <- if (length(args) >= 1 && nchar(args[1]) > 0) {
  args[1]
} else {
  "C:\\NEVEN\\functions"
}

if (!dir.exists(functions_dir)) {
  stop(paste0("El directorio no existe: ", functions_dir))
}

cat(sprintf("Directorio: %s\n", functions_dir))

# ── Mapeo de prefijos a familias ─────────────────────────────────────────────
PREFIX_FAMILY_MAP <- c(
  "R4XCL-AD-" = "AD",
  "R4XCL-RG-" = "RG",
  "R4XCL-GR-" = "GR",
  "R4XCL-MT-" = "MT",
  "R4XCL-FX-" = "FX"
)

derive_family <- function(filename) {
  bn <- basename(filename)
  for (prefix in names(PREFIX_FAMILY_MAP)) {
    if (startsWith(bn, prefix)) {
      return(PREFIX_FAMILY_MAP[[prefix]])
    }
  }
  return("GENERAL")
}

# ── Generación de sidecar ────────────────────────────────────────────────────
generate_sidecar <- function(r_file) {
  # Comprobar si ya existe el .json (skip)
  json_path <- sub("\\.R$", ".json", r_file, ignore.case = TRUE)
  if (file.exists(json_path)) {
    cat(sprintf("[SKIP] %s — ya existe %s\n", basename(r_file), basename(json_path)))
    return("skipped")
  }

  # Cargar el .R en entorno limpio
  env <- new.env(parent = emptyenv())
  tryCatch(
    sys.source(r_file, envir = env),
    error = function(e) {
      cat(sprintf("[ERROR] %s — no se pudo cargar: %s\n", basename(r_file), conditionMessage(e)))
      return(NULL)
    }
  )

  # Buscar funciones con attr(fn, "description")
  fn_names <- ls(env)
  found_any <- FALSE
  description <- ""

  for (fn_name in fn_names) {
    obj <- get(fn_name, envir = env)
    if (is.function(obj)) {
      desc_attr <- attr(obj, "description")
      if (!is.null(desc_attr)) {
        found_any <- TRUE
        # Extraer description: puede ser string directo o lista con $Detalle
        if (is.list(desc_attr)) {
          description <- if (!is.null(desc_attr$Detalle)) as.character(desc_attr$Detalle) else ""
        } else {
          description <- as.character(desc_attr)
        }
        break  # Usar la primera función con descripción
      }
    }
  }

  # Derivar familia desde nombre del archivo
  family <- derive_family(r_file)
  file_basename <- basename(r_file)
  id <- sub("\\.[Rr]$", "", file_basename)

  # Construir el sidecar
  sidecar <- list(
    id             = id,
    family         = family,
    family_label   = switch(family,
      AD = "Análisis de Datos", RG = "Regresión",
      GR = "Gráficos",          MT = "Métodos",
      FX = "Funciones",         "General"
    ),
    name           = id,
    description    = description,
    languages      = list("r"),
    function_name  = id,
    file           = file_basename,
    variable_roles = list(),
    parameters     = list()
  )

  # Serializar y escribir
  json_str <- jsonlite::toJSON(sidecar, pretty = TRUE, auto_unbox = TRUE, null = "null")
  writeLines(json_str, json_path)
  cat(sprintf("[OK] %s → %s\n", basename(r_file), basename(json_path)))
  return("processed")
}

# ── Loop principal ────────────────────────────────────────────────────────────
r_files <- list.files(functions_dir, pattern = "\\.[Rr]$", full.names = TRUE)

processed <- 0L
skipped   <- 0L
failed    <- 0L

for (r_file in r_files) {
  result <- tryCatch(
    generate_sidecar(r_file),
    error = function(e) {
      cat(sprintf("[FAILED] %s — %s\n", basename(r_file), conditionMessage(e)))
      "failed"
    }
  )
  if (is.null(result) || identical(result, "failed")) {
    failed <- failed + 1L
  } else if (identical(result, "skipped")) {
    skipped <- skipped + 1L
  } else {
    processed <- processed + 1L
  }
}

# ── Resumen final ─────────────────────────────────────────────────────────────
cat(sprintf("\n── Resumen ──────────────────────────────────\n"))
cat(sprintf("  Procesados : %d\n", processed))
cat(sprintf("  Saltados   : %d\n", skipped))
cat(sprintf("  Fallidos   : %d\n", failed))
cat(sprintf("─────────────────────────────────────────────\n"))
