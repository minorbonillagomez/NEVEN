# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Tests familia AD (Análisis de Datos)
# Cubre: AD_KMedias, AD_ACP, AD_ClusteringJerarquico
# ═══════════════════════════════════════════════════════════════════════════════

library(testthat)

# ── Helpers ──────────────────────────────────────────────────────────────────

# Rutas de búsqueda para el entorno NEVEN
.neven_source <- function(filename) {
  candidates <- c(
    file.path("C:/NEVEN/startup", filename),
    file.path("C:/NEVEN/functions", filename),
    file.path(getwd(), "startup", filename),
    file.path(getwd(), "..", "startup", filename)
  )
  for (p in candidates) {
    if (file.exists(p)) { source(p, local = FALSE); return(invisible(p)) }
  }
  stop("No se encontró: ", filename)
}

.neven_source_fn <- function(filename) {
  candidates <- c(
    file.path("C:/NEVEN/functions", filename),
    file.path(getwd(), "libreria/R", filename),
    file.path(getwd(), "..", "libreria/R", filename)
  )
  for (p in candidates) {
    if (file.exists(p)) { source(p, local = FALSE); return(invisible(p)) }
  }
  stop("No se encontró función: ", filename)
}

# Cargar infraestructura base
if (!exists("r_object_to_slots", mode = "function")) {
  .neven_source("r_object_to_slots.R")
}

# ── Validador genérico de slots ───────────────────────────────────────────────
expect_valid_slots <- function(result, fn_name, min_slots = 1L) {
  expect_true(is.data.frame(result),
    info = paste(fn_name, ": resultado debe ser data.frame"))
  expect_gte(nrow(result), min_slots,
    label = paste(fn_name, ": debe tener al menos", min_slots, "slot(s)"))
  expect_true(all(c("name","label","type","value","tier") %in% names(result)),
    info = paste(fn_name, ": columnas name/label/type/value/tier requeridas"))
  expect_true(all(result$type %in% c("html","table","scalar","vector","unknown")),
    info = paste(fn_name, ": tipos deben ser html/table/scalar/vector/unknown"))
  expect_false(any(is.na(result$name) | result$name == ""),
    info = paste(fn_name, ": ningún slot debe tener name vacío o NA"))
  expect_true(any(result$tier == 1L),
    info = paste(fn_name, ": debe haber al menos 1 slot con tier=1"))
}

# ── Datos sintéticos estándar ─────────────────────────────────────────────────
set.seed(42)
n <- 60L
datos_numericos <- data.frame(
  V1 = rnorm(n, mean = 10, sd = 2),
  V2 = rnorm(n, mean =  5, sd = 1),
  V3 = rnorm(n, mean = 20, sd = 5),
  V4 = rnorm(n, mean =  0, sd = 1)
)

# ═══════════════════════════════════════════════════════════════════════════════
# AD_KMedias
# ═══════════════════════════════════════════════════════════════════════════════

test_that("AD_KMedias — carga y llama sin error con K=3", {
  skip_if_not(.neven_source_fn_exists <- function(f)
    any(file.exists(c(
      file.path("C:/NEVEN/functions", f),
      file.path(getwd(), "libreria/R", f)
    ))), "Archivo Studio no encontrado")
  if (!exists("AD_KMediass.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-AD-KMediass.Studio.R"),
             error = function(e) skip(paste("No se pudo cargar AD_KMedias:", e$message)))
  }
  fn <- if (exists("AD_KMediass.Studio")) AD_KMediass.Studio else
        if (exists("AD_KMedias.Studio"))  AD_KMedias.Studio  else
        skip("Función AD_KMedias.Studio no encontrada")
  result <- fn(datos_numericos, K = 3L)
  expect_valid_slots(result, "AD_KMedias", min_slots = 2L)
})

test_that("AD_KMedias — slots incluyen asignaciones de cluster (tabla)", {
  skip_if(!exists("AD_KMediass.Studio") && !exists("AD_KMedias.Studio"),
          "Función no cargada")
  fn <- if (exists("AD_KMediass.Studio")) AD_KMediass.Studio else AD_KMedias.Studio
  result <- fn(datos_numericos, K = 3L)
  has_table <- any(result$type == "table")
  expect_true(has_table, info = "Debe haber al menos un slot tipo 'table'")
})

# ═══════════════════════════════════════════════════════════════════════════════
# AD_ACP
# ═══════════════════════════════════════════════════════════════════════════════

test_that("AD_ACP — carga y llama sin error", {
  if (!exists("AD_ACP.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-AD-ACP.Studio.R"),
             error = function(e) skip(paste("No se pudo cargar AD_ACP:", e$message)))
  }
  skip_if(!exists("AD_ACP.Studio", mode = "function"), "Función AD_ACP.Studio no encontrada")
  result <- AD_ACP.Studio(datos_numericos)
  expect_valid_slots(result, "AD_ACP", min_slots = 3L)
})

test_that("AD_ACP — incluye slot de varianza explicada (tabla o scalar)", {
  skip_if(!exists("AD_ACP.Studio", mode = "function"), "Función no cargada")
  result <- AD_ACP.Studio(datos_numericos)
  expect_true(any(result$type %in% c("table", "html")),
    info = "AD_ACP debe retornar al menos un slot de tipo table o html")
})

test_that("AD_ACP — no falla con N_Componentes explícito", {
  skip_if(!exists("AD_ACP.Studio", mode = "function"), "Función no cargada")
  result <- tryCatch(
    AD_ACP.Studio(datos_numericos, N_Componentes = 2L),
    error = function(e) e
  )
  expect_false(inherits(result, "error"),
    info = paste("AD_ACP con N_Componentes=2 no debe fallar:", if(inherits(result,"error")) result$message else "OK"))
})

# ═══════════════════════════════════════════════════════════════════════════════
# AD_ClusteringJerarquico
# ═══════════════════════════════════════════════════════════════════════════════

test_that("AD_ClusteringJerarquico — carga y llama sin error", {
  if (!exists("AD_ClusteringJerarquico.Studio", mode = "function")) {
    tryCatch(.neven_source_fn("R4XCL-AD-ClusteringJerarquico.Studio.R"),
             error = function(e) skip(paste("No se pudo cargar ClusteringJerarquico:", e$message)))
  }
  skip_if(!exists("AD_ClusteringJerarquico.Studio", mode = "function"),
          "Función AD_ClusteringJerarquico.Studio no encontrada")
  result <- AD_ClusteringJerarquico.Studio(datos_numericos)
  expect_valid_slots(result, "AD_ClusteringJerarquico", min_slots = 2L)
})

test_that("AD_ClusteringJerarquico — retorna slots de asignaciones y centroides (tabla)", {
  skip_if(!exists("AD_ClusteringJerarquico.Studio", mode = "function"), "Función no cargada")
  result <- AD_ClusteringJerarquico.Studio(datos_numericos)
  # El wrapper genera asignaciones, resumen_clusters, centroides, alturas_fusion
  expect_true(any(result$type == "table"),
    info = "ClusteringJerarquico debe incluir slots tipo tabla")
  expect_true(any(result$name == "asignaciones" | result$name == "centroides"),
    info = "ClusteringJerarquico debe incluir slot 'asignaciones' o 'centroides'")
})
