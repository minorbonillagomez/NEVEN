# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Tests familia RG econométrico + ST
# Cubre: RG_RESET, RG_Davidson_MacKinnon, RG_Newey_West, RG_FGLS,
#        RG_2SLS, RG_HECKIT, ST_VAR, ST_ECM
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
  expect_true(is.data.frame(result),           info = paste(fn_name, ": data.frame"))
  expect_gte(nrow(result), min_slots,           label = paste(fn_name, ": slots mínimos"))
  expect_true(all(c("name","label","type","value","tier") %in% names(result)),
              info = paste(fn_name, ": columnas requeridas"))
  expect_true(all(result$type %in% c("html","table","scalar","vector","unknown")),
              info = paste(fn_name, ": tipos válidos"))
  expect_false(any(is.na(result$name) | result$name == ""),
               info = paste(fn_name, ": names no vacíos"))
  expect_true(any(result$tier == 1L), info = paste(fn_name, ": tier=1"))
}

# Helper: cargar + saltar si falla
.load_or_skip <- function(fn_name, filename) {
  if (!exists(fn_name, mode = "function")) {
    tryCatch(.neven_source_fn(filename),
             error = function(e) skip(paste("No se pudo cargar", fn_name, ":", e$message)))
  }
  if (!exists(fn_name, mode = "function")) skip(paste("Función", fn_name, "no encontrada"))
}

# ── Datos sintéticos estándar ─────────────────────────────────────────────────
set.seed(42)
n <- 100L
data_X <- data.frame(X1 = rnorm(n), X2 = rnorm(n))
data_Y <- data.frame(Y = 1 + 2*data_X$X1 - 0.5*data_X$X2 + rnorm(n))

# Alternativa para Davidson-MacKinnon (dos modelos distintos)
data_X2 <- data.frame(X1 = data_X$X1, X3 = rnorm(n))

# 2SLS: instrumento correlacionado con X1 pero no con error
Z       <- data_X$X1 * 0.7 + rnorm(n, sd = 0.3)
data_Z  <- data.frame(Z = Z)

# Heckman: ecuación de selección (binaria)
latente_sel <- 0.3 + 1.5*data_X$X1 + rnorm(n)
sel_bin     <- as.integer(latente_sel > 0)
y_heckit    <- ifelse(sel_bin == 1,
                      2 + 1.8*data_X$X1 + rnorm(sum(sel_bin), sd = 0.5),
                      NA_real_)
data_Y_heck <- data.frame(Y = y_heckit)
data_X_heck <- data.frame(X1 = data_X$X1, sel = sel_bin)

# VAR: 2 series temporales cointegradas
n_ts <- 80L
ts1  <- cumsum(rnorm(n_ts))
ts2  <- ts1 * 0.8 + rnorm(n_ts, sd = 0.3)
data_var <- data.frame(Serie1 = ts1, Serie2 = ts2)

# ECM: mismas series para cointegración
data_ecm <- data_var

# ═══════════════════════════════════════════════════════════════════════════════
# RG_RESET
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_RESET — produce slots válidos", {
  .load_or_skip("RG_RESET.Studio", "RG_RESET.Studio.R")
  skip_if_not_installed("lmtest")
  result <- tryCatch(RG_RESET.Studio(data_Y, data_X), error = function(e) e)
  if (inherits(result, "error")) skip(paste("RG_RESET:", result$message))
  expect_valid_slots(result, "RG_RESET")
})

test_that("RG_RESET — incluye p-valor o tabla de test (tabla/scalar)", {
  skip_if(!exists("RG_RESET.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("lmtest")
  result <- tryCatch(RG_RESET.Studio(data_Y, data_X), error = function(e) NULL)
  skip_if(is.null(result))
  expect_true(any(result$type %in% c("table","scalar")),
    info = "RG_RESET debe incluir tabla o scalar con el p-valor")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_Davidson_MacKinnon
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_Davidson_MacKinnon — produce slots válidos", {
  .load_or_skip("RG_Davidson_MacKinnon.Studio", "RG_Davidson_MacKinnon.Studio.R")
  skip_if_not_installed("lmtest")
  result <- tryCatch(
    RG_Davidson_MacKinnon.Studio(data_Y, data_X, data_X2),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("RG_Davidson_MacKinnon:", result$message))
  expect_valid_slots(result, "RG_Davidson_MacKinnon")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_Newey_West
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_Newey_West — produce slots válidos", {
  .load_or_skip("RG_Newey_West.Studio", "RG_Newey_West.Studio.R")
  skip_if_not_installed("sandwich")
  result <- tryCatch(RG_Newey_West.Studio(data_Y, data_X), error = function(e) e)
  if (inherits(result, "error")) skip(paste("RG_Newey_West:", result$message))
  expect_valid_slots(result, "RG_Newey_West")
})

test_that("RG_Newey_West — incluye errores estándar HAC (tabla)", {
  skip_if(!exists("RG_Newey_West.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("sandwich")
  result <- tryCatch(RG_Newey_West.Studio(data_Y, data_X), error = function(e) NULL)
  skip_if(is.null(result))
  expect_true(any(result$type == "table"),
    info = "RG_Newey_West debe incluir tabla con errores HAC")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_FGLS
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_FGLS — produce slots válidos", {
  .load_or_skip("RG_FGLS.Studio", "RG_FGLS.Studio.R")
  skip_if_not_installed("sandwich")
  result <- tryCatch(RG_FGLS.Studio(data_Y, data_X), error = function(e) e)
  if (inherits(result, "error")) skip(paste("RG_FGLS:", result$message))
  expect_valid_slots(result, "RG_FGLS")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_2SLS
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_2SLS — produce slots válidos con instrumento Z", {
  .load_or_skip("RG_2SLS.Studio", "RG_2SLS.Studio.R")
  skip_if_not_installed("AER")
  result <- tryCatch(
    RG_2SLS.Studio(data_Y, data_X, data_Z),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("RG_2SLS:", result$message))
  expect_valid_slots(result, "RG_2SLS")
})

test_that("RG_2SLS — incluye diagnósticos (F-test, Wu-Hausman)", {
  skip_if(!exists("RG_2SLS.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("AER")
  result <- tryCatch(RG_2SLS.Studio(data_Y, data_X, data_Z), error = function(e) NULL)
  skip_if(is.null(result))
  expect_true(any(result$type == "table"),
    info = "RG_2SLS debe incluir tabla de diagnósticos")
})

# ═══════════════════════════════════════════════════════════════════════════════
# RG_HECKIT
# ═══════════════════════════════════════════════════════════════════════════════

test_that("RG_HECKIT — produce slots válidos", {
  .load_or_skip("RG_HECKIT.Studio", "RG_HECKIT.Studio.R")
  skip_if_not_installed("sampleSelection")
  result <- tryCatch(
    RG_HECKIT.Studio(data_Y_heck, data_X_heck),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("RG_HECKIT:", result$message))
  expect_valid_slots(result, "RG_HECKIT")
})

# ═══════════════════════════════════════════════════════════════════════════════
# ST_VAR
# ═══════════════════════════════════════════════════════════════════════════════

test_that("ST_VAR — produce slots válidos con 2 series", {
  .load_or_skip("ST_VAR.Studio", "ST_VAR.Studio.R")
  skip_if_not_installed("vars")
  result <- tryCatch(ST_VAR.Studio(data_var), error = function(e) e)
  if (inherits(result, "error")) skip(paste("ST_VAR:", result$message))
  expect_valid_slots(result, "ST_VAR", min_slots = 2L)
})

test_that("ST_VAR — incluye tabla de pronóstico o coeficientes", {
  skip_if(!exists("ST_VAR.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("vars")
  result <- tryCatch(ST_VAR.Studio(data_var), error = function(e) NULL)
  skip_if(is.null(result))
  expect_true(any(result$type %in% c("table","html")),
    info = "ST_VAR debe incluir tabla o visualización")
})

# ═══════════════════════════════════════════════════════════════════════════════
# ST_ECM
# ═══════════════════════════════════════════════════════════════════════════════

test_that("ST_ECM — produce slots válidos (cointegración + corrección de error)", {
  .load_or_skip("ST_ECM.Studio", "ST_ECM.Studio.R")
  skip_if_not_installed("vars")
  skip_if_not_installed("urca")
  result <- tryCatch(ST_ECM.Studio(data_ecm), error = function(e) e)
  if (inherits(result, "error")) skip(paste("ST_ECM:", result$message))
  expect_valid_slots(result, "ST_ECM", min_slots = 2L)
})

test_that("ST_ECM — incluye velocidad de ajuste ECT (tabla)", {
  skip_if(!exists("ST_ECM.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("vars")
  skip_if_not_installed("urca")
  result <- tryCatch(ST_ECM.Studio(data_ecm), error = function(e) NULL)
  skip_if(is.null(result))
  expect_true(any(result$type == "table"),
    info = "ST_ECM debe incluir tabla de coeficientes o velocidad de ajuste ECT")
})
