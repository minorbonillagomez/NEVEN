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
# NEVEN: MOTOR DE EXTRACCIÓN DE OUTPUTS (Interno - No modificar)
# =========================================================================

Extraer_outputs <- function(objeto, nombre_modelo = NULL, verbose = FALSE) {
   if (is.null(nombre_modelo)) nombre_modelo <- deparse(substitute(objeto))
   outputs <- list()
   es_s4 <- isS4(objeto)
   es_s3 <- !es_s4
   
   # Campos a omitir (grandes y sin valor interpretativo para el usuario)
   omitir <- c("model", "effects", "qr", "x", "y", "fitted.values")
   
   if (es_s4) {
      for (s in slotNames(objeto)) outputs[[s]] <- .neven_procesar_valor(slot(objeto, s))
   }
   if (es_s3) {
      for (comp in names(objeto)) {
         if (comp %in% omitir) next
         outputs[[comp]] <- .neven_procesar_valor(objeto[[comp]])
      }
   }
   
   resumen <- tryCatch(summary(objeto), error = function(e) NULL)
   if (!is.null(resumen)) {
      if (!is.null(resumen$coefficients)) outputs[["Summary_Stats"]] <- .neven_procesar_valor(resumen$coefficients)
      if (!is.null(resumen$sigma)) {
         outputs[["Residual_Error"]] <- data.frame(Parametro = "Sigma", Metrica = "Value", Valor = as.character(resumen$sigma))
         if (!is.null(resumen$df)) outputs[["Degrees_of_Freedom"]] <- data.frame(Parametro = c("Model_DF", "Residual_DF", "Total_DF"), Metrica = "DF", Valor = as.character(resumen$df[1:3]))
      }
      if (!is.null(resumen$r.squared)) outputs[["R_Squared"]] <- data.frame(Parametro = c("Multiple_R2", "Adjusted_R2"), Metrica = "Value", Valor = as.character(c(resumen$r.squared, resumen$adj.r.squared)))
      fstat <- resumen$fstatistic
      if (!is.null(fstat)) {
         p_val_f <- pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)
         outputs[["F_Statistic"]] <- data.frame(Parametro = c("F_Value", "DF_Num", "DF_Den", "p_value"), Metrica = "Stat", Valor = as.character(c(fstat[1], fstat[2], fstat[3], p_val_f)))
      }
   }
   
   for (gen in c("AIC", "BIC")) {
      val <- tryCatch(get(gen)(objeto), error = function(e) NULL)
      if (!is.null(val)) outputs[[gen]] <- .neven_procesar_valor(val)
   }
   
   return(.neven_consolidar(outputs, nombre_modelo))
}

.neven_procesar_valor <- function(valor) {
   if (is.null(valor) || length(valor) == 0) return(NULL)
   if (is.matrix(valor) || is.data.frame(valor)) {
      df_tmp <- as.data.frame(valor)
      return(data.frame(Parametro = rep(rownames(df_tmp), each = ncol(df_tmp)), Metrica = rep(colnames(df_tmp), times = nrow(df_tmp)), Valor = as.character(unlist(df_tmp, use.names = FALSE)), stringsAsFactors = FALSE))
   }
   if (is.atomic(valor)) {
      return(data.frame(Parametro = if(!is.null(names(valor))) names(valor) else as.character(seq_along(valor)), Metrica = "Value", Valor = as.character(valor), stringsAsFactors = FALSE))
   }
   return(NULL)
}

.neven_consolidar <- function(lista_outputs, nombre_modelo) {
   lista_limpia <- Filter(function(x) is.data.frame(x) && nrow(x) > 0, lista_outputs)
   if (length(lista_limpia) == 0) return(data.frame(Modelo=character(), Seccion=character(), Parametro=character(), Metrica=character(), Valor=character()))
   lista_final <- lapply(names(lista_limpia), function(nom) { item <- lista_limpia[[nom]]; item$Seccion <- nom; item$Modelo <- nombre_modelo; return(item) })
   df_res <- do.call(rbind, lista_final)
   rownames(df_res) <- NULL
   return(df_res[, c("Modelo", "Seccion", "Parametro", "Metrica", "Valor")])
}
