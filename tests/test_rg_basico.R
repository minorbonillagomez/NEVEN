# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Tests familia RG básico
# Cubre: RG_Lineal, RG_Logistica, RG_ArbolDecision, RG_Poisson
# ═══════════════════════════════════════════════════════════════════════════════

library(testthat)

# ── Helpers ──────────────────────────────────────────────────────────────────

.neven_source_fn <- function(filename) {
  candidates <- c(
    file.path("C:/NEVEN/functions", filename),
    file.path(getwd(), "libreria/R", filename),
    file.path(getwd(), "..", "libreria/R", filename)
  )
  for (p in candidates) {
    if (file.exists(p)) { source(p, local = FALSE); return(invisible(p)) }
  }
  stop("No encontrado: ", filename)
}

if (!exists("r_object_to_slots", mode = "function")) {
  for (p in c("C:/NEVEN/startup/r_object_to_slots.R",
              file.path(getwd(), "startup/r_object_to_slots.R"))) {
    if (file.exists(p)) { source(p, local = FALSE); break }
  }
}

expect_valid_slots <- function(result, fn_name, min_slots = 1L) {
  expect_true(is.data.frame(result),
    info = paste(fn_name, ": resultado debe ser data.frame"))
  expect_gte(nrow(result), min_slots,
    label = paste(fn_name, ": slots mínimos"))
  expect_true(all(c("name","label","type","value","tier") %in% names(result)),
    info = paste(fn_name, ": columnas requeridas"))
  expect_true(all(result$type %in% c("html","table","scalar","vector","unknown")),
    info = paste(fn_name, ": tipos válidos"))
  expect_false(any(is.na(result$name) | result$name == ""),
    info = paste(fn_name, ": nombres no vacíos"))
  expect_true(any(result$tier == 1L),
    info = paste(fn_name, ": al menos un slot tier=1"))
}

# ── Datos sintéticos ──────────────────────────────────────────────────────────
set.seed(42)
n <- 80L
data_X <- data.frame(
  X1 = rnorm(n),
  X2 = rnorm(n),
  X3 = rnorm(n)
)
data_Y     <- data.frame(Y     = 1.5 + 2*data_X$X1 - 0.8*data_X$X2 + rnorm(n, sd = 0.5))
data_Y_bin <- data.frame(Y_bin = as.integer(data_Y$Y > median(data_Y$Y)))
data_Y_cnt <- data.frame(Y_cnt = rpois(n, lambda = 3))

# ═══════════════════════════════════════════════════════════════════════════════
# RG_Lineal
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_Lineal — produce slots válidos", {
  if (!exists("RG_Lineal.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-RG-Lineal.Studio.R"),
             error = function(e) skip(e$message))
  }
  skip_if(!exists("RG_Lineal.Studio", mode = "function"), "Función no encontrada")
  result <- RG_Lineal.Studio(data_Y, data_X)
  expect_valid_slots(result, "RG_Lineal", min_slots = 3L)
})

test_that("RG_Lineal — incluye slot de métricas (tabla)", {
  skip_if(!exists("RG_Lineal.Studio", mode = "function"), "Función no cargada")
  result <- RG_Lineal.Studio(data_Y, data_X)
  expect_true(any(result$type == "table"),
    info = "RG_Lineal debe incluir al menos un slot tipo tabla")
})

test_that("RG_Lineal — incluye gráfico de residuos (html)", {
  skip_if(!exists("RG_Lineal.Studio", mode = "function"), "Función no cargada")
  result <- RG_Lineal.Studio(data_Y, data_X)
  expect_true(any(result$type == "html"),
    info = "RG_Lineal debe incluir slot html (gráfico o tabla stargazer)")
})

test_that("RG_Lineal — funciona sin constante (Constante=FALSE)", {
  skip_if(!exists("RG_Lineal.Studio", mode = "function"), "Función no cargada")
  result <- tryCatch(
    RG_Lineal.Studio(data_Y, data_X, Constante = FALSE),
    error = function(e) e
  )
  expect_false(inherits(result, "error"),
    info = paste("RG_Lineal sin constante no debe fallar:", if(inherits(result,"error")) result$message else "OK"))
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_Logistica
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_Logistica — produce slots válidos con Y binario", {
  if (!exists("RG_Logistica.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-RG-Logistica.Studio.R"),
             error = function(e) skip(e$message))
  }
  skip_if(!exists("RG_Logistica.Studio", mode = "function"), "Función no encontrada")
  result <- RG_Logistica.Studio(data_Y_bin, data_X)
  expect_valid_slots(result, "RG_Logistica", min_slots = 2L)
})

test_that("RG_Logistica — incluye odds ratios o coeficientes (tabla)", {
  skip_if(!exists("RG_Logistica.Studio", mode = "function"), "Función no cargada")
  result <- RG_Logistica.Studio(data_Y_bin, data_X)
  expect_true(any(result$type == "table"),
    info = "RG_Logistica debe incluir tabla de coeficientes/odds ratios")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_ArbolDecision
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_ArbolDecision — produce slots válidos", {
  if (!exists("RG_ArbolDecision.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-RG-ArbolDecision.Studio.R"),
             error = function(e) skip(e$message))
  }
  skip_if(!exists("RG_ArbolDecision.Studio", mode = "function"), "Función no encontrada")
  # Árbol: Y puede ser continuo o binario
  result <- RG_ArbolDecision.Studio(data_Y, data_X)
  expect_valid_slots(result, "RG_ArbolDecision", min_slots = 2L)
})

test_that("RG_ArbolDecision — incluye importancia de variables (tabla)", {
  skip_if(!exists("RG_ArbolDecision.Studio", mode = "function"), "Función no cargada")
  result <- RG_ArbolDecision.Studio(data_Y, data_X)
  expect_true(any(result$type %in% c("table","html")),
    info = "RG_ArbolDecision debe incluir tabla o visualización")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_Poisson
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_Poisson — produce slots válidos con Y de conteo", {
  if (!exists("RG_Poisson.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-RG-Poisson.Studio.R"),
             error = function(e) skip(e$message))
  }
  skip_if(!exists("RG_Poisson.Studio", mode = "function"), "Función no encontrada")
  result <- RG_Poisson.Studio(data_Y_cnt, data_X)
  expect_valid_slots(result, "RG_Poisson", min_slots = 2L)
})

test_that("RG_Poisson — incluye tabla de IRR o coeficientes", {
  skip_if(!exists("RG_Poisson.Studio", mode = "function"), "Función no cargada")
  result <- RG_Poisson.Studio(data_Y_cnt, data_X)
  expect_true(any(result$type == "table"),
    info = "RG_Poisson debe incluir tabla de coeficientes/IRR")
})
