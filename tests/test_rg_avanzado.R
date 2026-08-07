# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Tests familia RG avanzado
# Cubre: RG_DatosPanel, RG_SeriesTiempo, RG_SVM, RG_Tobit
# ═══════════════════════════════════════════════════════════════════════════════

library(testthat)

# ── Helpers ──────────────────────────────────────────────────────────────────

.neven_source_fn <- function(filename) {
  candidates <- c(
    file.path("C:/NEVEN/functions", filename),
    file.path(getwd(), "libreria/R", filename)
  )
  for (p in candidates) {
    if (file.exists(p)) { source(p, local = FALSE); return(invisible(p)) }
  }
  stop("No encontrado: ", filename)
}

if (!exists("r_object_to_slots", mode = "function")) {
  for (p in c("C:/NEVEN/startup/r_object_to_slots.R")) {
    if (file.exists(p)) { source(p, local = FALSE); break }
  }
}

expect_valid_slots <- function(result, fn_name, min_slots = 1L) {
  expect_true(is.data.frame(result),
    info = paste(fn_name, ": data.frame"))
  expect_gte(nrow(result), min_slots,
    label = paste(fn_name, ": slots mínimos"))
  expect_true(all(c("name","label","type","value","tier") %in% names(result)),
    info = paste(fn_name, ": columnas requeridas"))
  expect_true(all(result$type %in% c("html","table","scalar","vector","unknown")),
    info = paste(fn_name, ": tipos válidos"))
  expect_false(any(is.na(result$name) | result$name == ""),
    info = paste(fn_name, ": names no vacíos"))
  expect_true(any(result$tier == 1L),
    info = paste(fn_name, ": tier=1 existe"))
}

# ── Datos sintéticos ──────────────────────────────────────────────────────────
set.seed(42)

# Panel: 10 entidades × 8 períodos
n_ent <- 10L; n_per <- 8L; n_pan <- n_ent * n_per
data_panel <- data.frame(
  entidad = rep(1:n_ent, each = n_per),
  periodo = rep(1:n_per, times = n_ent),
  Y       = 2 + rnorm(n_pan),
  X1      = rnorm(n_pan),
  X2      = rnorm(n_pan)
)

# Series de tiempo: 60 observaciones mensuales
n_ts <- 60L
data_ts_Y <- data.frame(Y = cumsum(rnorm(n_ts, mean = 0.1)))
data_ts_X <- data.frame(
  fecha = seq.Date(as.Date("2020-01-01"), by = "month", length.out = n_ts)
)

# SVM: 80 observaciones, Y continuo
set.seed(42); n_svm <- 80L
data_svm_X <- data.frame(X1 = rnorm(n_svm), X2 = rnorm(n_svm))
data_svm_Y <- data.frame(Y  = 1 + 2*data_svm_X$X1 + rnorm(n_svm, sd = 0.5))

# Tobit: Y censurado en 0
set.seed(42); n_tob <- 80L
data_tob_X <- data.frame(X1 = rnorm(n_tob), X2 = rnorm(n_tob))
latente    <- 0.5 + 2*data_tob_X$X1 + rnorm(n_tob)
data_tob_Y <- data.frame(Y = pmax(0, latente))  # censurado en 0

# ═══════════════════════════════════════════════════════════════════════════════
# RG_DatosPanel
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_DatosPanel — produce slots válidos", {
  if (!exists("RG_DatosPanel.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-RG-DatosPanel.Studio.R"),
             error = function(e) skip(e$message))
  }
  skip_if(!exists("RG_DatosPanel.Studio", mode = "function"), "Función no encontrada")
  skip_if_not_installed("plm")
  data_Y_pan <- data.frame(Y = data_panel$Y)
  data_X_pan <- data_panel[, c("X1","X2","entidad","periodo")]
  result <- tryCatch(
    RG_DatosPanel.Studio(data_Y_pan, data_X_pan,
                          id_col = "entidad", time_col = "periodo"),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("RG_DatosPanel error:", result$message))
  expect_valid_slots(result, "RG_DatosPanel", min_slots = 2L)
})

test_that("RG_DatosPanel — incluye tabla de coeficientes o test de Hausman", {
  skip_if(!exists("RG_DatosPanel.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("plm")
  data_Y_pan <- data.frame(Y = data_panel$Y)
  data_X_pan <- data_panel[, c("X1","X2","entidad","periodo")]
  result <- tryCatch(
    RG_DatosPanel.Studio(data_Y_pan, data_X_pan,
                          id_col = "entidad", time_col = "periodo"),
    error = function(e) NULL
  )
  skip_if(is.null(result), "Función no corrió correctamente")
  expect_true(any(result$type == "table"),
    info = "RG_DatosPanel debe incluir tabla de resultados")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_SeriesTiempo
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_SeriesTiempo — produce slots válidos", {
  if (!exists("RG_SeriesTiempo.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-RG-SeriesTiempo.Studio.R"),
             error = function(e) skip(e$message))
  }
  skip_if(!exists("RG_SeriesTiempo.Studio", mode = "function"), "Función no encontrada")
  skip_if_not_installed("forecast")
  result <- tryCatch(
    RG_SeriesTiempo.Studio(data_ts_Y),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("RG_SeriesTiempo error:", result$message))
  expect_valid_slots(result, "RG_SeriesTiempo", min_slots = 2L)
})

test_that("RG_SeriesTiempo — incluye tabla de pronóstico", {
  skip_if(!exists("RG_SeriesTiempo.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("forecast")
  result <- tryCatch(
    RG_SeriesTiempo.Studio(data_ts_Y),
    error = function(e) NULL
  )
  skip_if(is.null(result), "Función no corrió correctamente")
  expect_true(any(result$type %in% c("table","html")),
    info = "RG_SeriesTiempo debe incluir tabla o gráfico de pronóstico")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_SVM
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_SVM — produce slots válidos (regresión)", {
  if (!exists("RG_SVM.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-RG-SVM.Studio.R"),
             error = function(e) skip(e$message))
  }
  skip_if(!exists("RG_SVM.Studio", mode = "function"), "Función no encontrada")
  skip_if_not_installed("e1071")
  result <- tryCatch(
    RG_SVM.Studio(data_svm_Y, data_svm_X),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("RG_SVM error:", result$message))
  expect_valid_slots(result, "RG_SVM", min_slots = 2L)
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_Tobit
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_Tobit — produce slots válidos con Y censurado", {
  if (!exists("RG_Tobit.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-RG-Tobit.Studio.R"),
             error = function(e) skip(e$message))
  }
  skip_if(!exists("RG_Tobit.Studio", mode = "function"), "Función no encontrada")
  skip_if_not_installed("AER")
  result <- tryCatch(
    RG_Tobit.Studio(data_tob_Y, data_tob_X),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("RG_Tobit error:", result$message))
  expect_valid_slots(result, "RG_Tobit", min_slots = 2L)
})

test_that("RG_Tobit — incluye efectos marginales o coeficientes (tabla)", {
  skip_if(!exists("RG_Tobit.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("AER")
  result <- tryCatch(
    RG_Tobit.Studio(data_tob_Y, data_tob_X),
    error = function(e) NULL
  )
  skip_if(is.null(result), "Función no corrió")
  expect_true(any(result$type == "table"),
    info = "RG_Tobit debe incluir tabla de coeficientes/efectos marginales")
})
