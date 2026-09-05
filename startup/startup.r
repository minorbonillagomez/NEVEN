# NEVEN Startup Script for R
# Copyright (c) 2026 NEVEN Project - GPL v3

NEVEN <- new.env(parent = globalenv())

NEVEN$install.application.pointer <- function(p) { assign("application.pointer", p, envir = NEVEN); invisible(NULL) }

# Graphics device compatibility layer
# Saves plot as PNG and stores path for retrieval after dev.off()
BERT.graphics.device <- function(cell = FALSE, width = 800, height = 600, ...) {
  temp_dir <- file.path(Sys.getenv("USERPROFILE"), "Documents", "NEVEN", "graphics")
  if (!dir.exists(temp_dir)) dir.create(temp_dir, recursive = TRUE)
  fname <- file.path(temp_dir, paste0("neven_plot_", format(Sys.time(), "%Y%m%d_%H%M%S"), "_", sample(1000:9999, 1), ".png"))
  png(filename = fname, width = width, height = height, res = 96)
  assign(".neven.last.plot", fname, envir = .GlobalEnv)
}

# Helper: get the path of the last generated plot (Windows backslashes)
NEVEN.last.plot <- function() {
  if (exists(".neven.last.plot", envir = .GlobalEnv)) {
    return(gsub("/", "\\\\", get(".neven.last.plot", envir = .GlobalEnv)))
  }
  return("")
}

NEVEN$list.functions <- function() {
  funcs <- list()
  for (name in ls(globalenv())) {
    obj <- get(name, envir = globalenv())
    if (is.function(obj)) {
      entry <- list()
      entry$name <- name
      entry$flags <- 0
      args_info <- list()
      fargs <- formals(obj)
      if (!is.null(fargs)) {
        for (aname in names(fargs)) {
          arg_entry <- list(name = aname)
          defval <- fargs[[aname]]
          if (!missing(defval) && !is.symbol(defval)) { arg_entry[["default"]] <- defval }
          args_info[[length(args_info) + 1]] <- arg_entry
        }
      }
      entry$arguments <- args_info
      desc_attr <- attr(obj, "description")
      cat_attr <- attr(obj, "category")
      if (!is.null(desc_attr) || !is.null(cat_attr)) {
        entry$attributes <- list(description = desc_attr, category = if (!is.null(cat_attr)) cat_attr else "Exported R Functions")
      }
      funcs[[length(funcs) + 1]] <- entry
    }
  }
  return(funcs)
}

cat("NEVEN R startup complete\n")

# =========================================================================
# CM-BAJ-011/012: Extraer_outputs y helpers .neven_* eliminados v2.3
# La versiÃ³n canÃ³nica vive en libreria/R/R4XCL-0-Interno-3.R
# y se carga automÃ¡ticamente por el AutoLoader antes que este startup.
# =========================================================================

# â”€â”€ Data Lab: Serializador de slots â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
local({
  sr_path <- tryCatch(
    file.path(dirname(sys.frame(1)$ofile), "r_object_to_slots.R"),
    error = function(e) NA_character_
  )
  if (is.na(sr_path) || !file.exists(sr_path)) {
    # Fallback: buscar en el directorio estÃ¡ndar de producciÃ³n
    sr_path <- "C:\\NEVEN\\startup\\r_object_to_slots.R"
  }
  if (file.exists(sr_path)) {
    source(sr_path, local = FALSE)
    cat("NEVEN Data Lab: r_object_to_slots cargado\n")
  } else {
    warning("r_object_to_slots.R no encontrado â€” Data Lab no disponible")
  }
})

# â”€â”€ Pre-carga de paquetes para funciones econometricas avanzadas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Evita que la primera llamada al Benchmark o a las funciones avanzadas tarde
# mas de lo permitido por el timeout del Named Pipe, causando cierre del canal.
# Los paquetes se cargan silenciosamente -- si no estan instalados se ignoran.
local({
  pkgs_econometria <- c("lmtest", "sandwich", "AER", "sampleSelection",
                         "vars", "urca", "plm", "wooldridge")
  for (pkg in pkgs_econometria) {
    tryCatch(
      suppressMessages(suppressWarnings(
        requireNamespace(pkg, quietly = TRUE)
      )),
      error = function(e) invisible(NULL)
    )
  }
  cat("NEVEN: paquetes econometria precargados\n")
})

# PLUTO.READ: leer datos exportados desde Pluto de vuelta a Excel
source(file.path(Sys.getenv('NEVEN_HOME', 'C:/NEVEN'), 'startup', 'R4XCL-NEVEN-pluto-read.R'), local=FALSE)

# NevenX: dispatcher genérico de procesos (NevenX.R / NevenX.J / NevenX.P)
local({
  nx_path <- file.path(Sys.getenv('NEVEN_HOME', 'C:/NEVEN'), 'functions', 'R4XCL-0-NevenX.R')
  if (file.exists(nx_path)) {
    source(nx_path, local = FALSE)
  } else {
    cat("[NevenX] R4XCL-0-NevenX.R no encontrado — NevenX.R/J/P no disponible\n")
  }
})
