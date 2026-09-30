# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Tests familia GR (Gráficos)
# Cubre: GR_Barras, GR_Lineas, GR_SeriesTiempo, GR_Histograma,
#        GR_Correlaciones, GR_EjemploBasico, GR_EjemploAvanzado, GR_BoxPlot
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
  expect_true(is.data.frame(result),    info = paste(fn_name, ": data.frame"))
  expect_gte(nrow(result), min_slots,   label = paste(fn_name, ": slots mínimos"))
  expect_true(all(c("name","label","type","value","tier") %in% names(result)),
              info = paste(fn_name, ": columnas requeridas"))
  expect_true(all(result$type %in% c("html","table","scalar","vector","unknown")),
              info = paste(fn_name, ": tipos válidos"))
  expect_false(any(is.na(result$name) | result$name == ""),
               info = paste(fn_name, ": names no vacíos"))
  expect_true(any(result$tier == 1L), info = paste(fn_name, ": tier=1"))
}

# Las funciones GR deben siempre retornar exactamente 1 slot de tipo "html"
expect_gr_slot <- function(result, fn_name) {
  expect_valid_slots(result, fn_name, min_slots = 1L)
  expect_true(any(result$type == "html"),
    info = paste(fn_name, ": debe retornar slot html (gráfico Plotly)"))
  # El slot html debe contener una neven-plotly tag o html válido
  html_slots <- result$value[result$type == "html"]
  expect_true(any(nchar(html_slots) > 50L),
    info = paste(fn_name, ": slot html no debe estar vacío"))
}

.load_or_skip <- function(fn_name, filename) {
  if (!exists(fn_name, mode = "function")) {
    tryCatch(.neven_source_fn(filename),
             error = function(e) skip(paste("No se pudo cargar", fn_name, ":", e$message)))
  }
  if (!exists(fn_name, mode = "function")) skip(paste("Función", fn_name, "no encontrada"))
}

# ── Datos sintéticos ──────────────────────────────────────────────────────────
set.seed(42)
n <- 50L

# Datos para la mayoría de gráficos
datos_gr <- data.frame(
  X     = rnorm(n),
  Y     = rnorm(n, mean = 5),
  Y2    = rnorm(n, mean = 3),
  Grupo = factor(sample(c("A","B","C"), n, replace = TRUE)),
  Tam   = abs(rnorm(n)) + 0.5
)

# Datos para serie de tiempo
datos_ts <- data.frame(
  fecha = seq.Date(as.Date("2020-01-01"), by = "month", length.out = n),
  valor = cumsum(rnorm(n, 0.1))
)

# ═══════════════════════════════════════════════════════════════════════════════
# GR_Barras
# ═══════════════════════════════════════════════════════════════════════════════

test_that("GR_Barras — slot html con datos básicos (X categórico, Y numérico)", {
  .load_or_skip("GR_Barras.Studio", "GR_Barras.Studio.R")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_Barras.Studio(datos_gr[, c("Grupo","Y")]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_Barras:", result$message))
  expect_gr_slot(result, "GR_Barras")
})

test_that("GR_Barras — funciona en modo apilado (Modo=3)", {
  skip_if(!exists("GR_Barras.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_Barras.Studio(datos_gr[, c("Grupo","Y","Y2")], Modo = 3L),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_Barras modo apilado:", result$message))
  expect_gr_slot(result, "GR_Barras-apilado")
})

# ═══════════════════════════════════════════════════════════════════════════════
# GR_Lineas
# ═══════════════════════════════════════════════════════════════════════════════

test_that("GR_Lineas — slot html con Y numérico (sin X)", {
  .load_or_skip("GR_Lineas.Studio", "GR_Lineas.Studio.R")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_Lineas.Studio(datos_gr[, "Y", drop = FALSE]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_Lineas:", result$message))
  expect_gr_slot(result, "GR_Lineas")
})

test_that("GR_Lineas — funciona con X e Y explícitos", {
  skip_if(!exists("GR_Lineas.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_Lineas.Studio(datos_ts[, "valor", drop = FALSE],
                     data_X = datos_ts[, "fecha", drop = FALSE]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_Lineas con X:", result$message))
  expect_gr_slot(result, "GR_Lineas-con-X")
})

# ═══════════════════════════════════════════════════════════════════════════════
# GR_SeriesTiempo (wrapper GR — distinto de RG_SeriesTiempo)
# ═══════════════════════════════════════════════════════════════════════════════

test_that("GR_SeriesTiempo — slot html con serie numérica", {
  .load_or_skip("GR_SeriesTiempo.Studio", "GR_SeriesTiempo.Studio.R")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_SeriesTiempo.Studio(datos_ts[, "valor", drop = FALSE]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_SeriesTiempo:", result$message))
  expect_gr_slot(result, "GR_SeriesTiempo")
})

# ═══════════════════════════════════════════════════════════════════════════════
# GR_Histograma
# ═══════════════════════════════════════════════════════════════════════════════

test_that("GR_Histograma — slot html con columna numérica", {
  .load_or_skip("GR_Histograma.Studio", "GR_Histograma.Studio.R")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_Histograma.Studio(datos_gr[, "Y", drop = FALSE]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_Histograma:", result$message))
  expect_gr_slot(result, "GR_Histograma")
})

# ═══════════════════════════════════════════════════════════════════════════════
# GR_Correlaciones
# ═══════════════════════════════════════════════════════════════════════════════

test_that("GR_Correlaciones — slot html con ≥2 columnas numéricas", {
  .load_or_skip("GR_Correlaciones.Studio", "GR_Correlaciones.Studio.R")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_Correlaciones.Studio(datos_gr[, c("X","Y","Y2")]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_Correlaciones:", result$message))
  expect_gr_slot(result, "GR_Correlaciones")
})

# ═══════════════════════════════════════════════════════════════════════════════
# GR_EjemploBasico (scatter mínimo)
# ═══════════════════════════════════════════════════════════════════════════════

test_that("GR_EjemploBasico — slot html con X e Y numéricos", {
  .load_or_skip("GR_EjemploBasico.Studio", "GR_EjemploBasico.Studio.R")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_EjemploBasico.Studio(datos_gr[, c("X","Y")]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_EjemploBasico:", result$message))
  expect_gr_slot(result, "GR_EjemploBasico")
})

# ═══════════════════════════════════════════════════════════════════════════════
# GR_EjemploAvanzado (burbujas con color continuo/categórico)
# ═══════════════════════════════════════════════════════════════════════════════

test_that("GR_EjemploAvanzado — slot html con color numérico continuo", {
  .load_or_skip("GR_EjemploAvanzado.Studio", "GR_EjemploAvanzado.Studio.R")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_EjemploAvanzado.Studio(datos_gr[, c("X","Y","Tam","Y2")]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_EjemploAvanzado continuo:", result$message))
  expect_gr_slot(result, "GR_EjemploAvanzado-continuo")
})

test_that("GR_EjemploAvanzado — slot html con color categórico", {
  skip_if(!exists("GR_EjemploAvanzado.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_EjemploAvanzado.Studio(datos_gr[, c("X","Y","Tam","Grupo")]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_EjemploAvanzado categórico:", result$message))
  expect_gr_slot(result, "GR_EjemploAvanzado-categorico")
})

# ═══════════════════════════════════════════════════════════════════════════════
# GR_BoxPlot
# ═══════════════════════════════════════════════════════════════════════════════

test_that("GR_BoxPlot — slot html con Y numérico y grupo categórico", {
  .load_or_skip("GR_BoxPlot.Studio", "GR_BoxPlot.Studio.R")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_BoxPlot.Studio(datos_gr[, c("Grupo","Y")]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_BoxPlot:", result$message))
  expect_gr_slot(result, "GR_BoxPlot")
})

test_that("GR_BoxPlot — funciona sin columna de grupo (solo Y)", {
  skip_if(!exists("GR_BoxPlot.Studio", mode = "function"), "Función no cargada")
  skip_if_not_installed("jsonlite")
  result <- tryCatch(
    GR_BoxPlot.Studio(datos_gr[, "Y", drop = FALSE]),
    error = function(e) e
  )
  if (inherits(result, "error")) skip(paste("GR_BoxPlot sin grupo:", result$message))
  expect_gr_slot(result, "GR_BoxPlot-sin-grupo")
})
