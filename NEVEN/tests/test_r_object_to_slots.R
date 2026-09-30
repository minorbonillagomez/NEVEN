# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Tests para r_object_to_slots.R
# Tasks 9.1, 9.2, 9.3 del spec neven-data-lab
# ═══════════════════════════════════════════════════════════════════════════════

library(testthat)

# ── Cargar el serializador ───────────────────────────────────────────────────
# Solo cargar si las funciones no están ya disponibles en el entorno global
# (el runner externo run_tests_9.R ya hace source() antes de llamar test_file).
if (!exists("r_object_to_slots", mode = "function")) {
  # Buscar en orden de precedencia:
  #   1. Relativo al archivo de test (testthat cambia cwd al dir del test)
  #   2. Relativo a la raíz del proyecto (cuando se lanza desde la raíz)
  #   3. Ruta de producción estándar
  test_dir <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) getwd())
  candidate_paths <- c(
    file.path(test_dir, "..", "startup", "r_object_to_slots.R"),
    file.path(getwd(), "NEVEN", "startup", "r_object_to_slots.R"),
    file.path(getwd(), "startup", "r_object_to_slots.R"),
    "C:\\NEVEN\\startup\\r_object_to_slots.R"
  )
  found <- FALSE
  for (p in candidate_paths) {
    if (file.exists(p)) {
      source(p, local = FALSE)
      found <- TRUE
      break
    }
  }
  if (!found) {
    stop("No se encontró r_object_to_slots.R. ",
         "Ajuste el directorio de trabajo (setwd) o copie el archivo a C:\\NEVEN\\startup\\")
  }
}

# ── Guard: jsonlite necesario para la mayoría de los tests ──────────────────
skip_if_not_installed("jsonlite")

# ═══════════════════════════════════════════════════════════════════════════════
# Task 9.1 — Tests unitarios estándar
# ═══════════════════════════════════════════════════════════════════════════════

test_that("9.1 — data.frame se detecta como tipo 'table'", {
  obj    <- list(tabla = data.frame(x = 1:3, y = c("a", "b", "c")))
  slots  <- r_object_to_slots(obj)
  expect_equal(slots$type[slots$name == "tabla"], "table")
})

test_that("9.1 — matrix se detecta como tipo 'table'", {
  obj   <- list(mat = matrix(1:9, nrow = 3))
  slots <- r_object_to_slots(obj)
  expect_equal(slots$type[slots$name == "mat"], "table")
})

test_that("9.1 — string con '<html' (minúsculas) se detecta como tipo 'html'", {
  html_str <- "<html><body><p>Hola</p></body></html>"
  obj      <- list(contenido = html_str)
  slots    <- r_object_to_slots(obj)
  expect_equal(slots$type[slots$name == "contenido"], "html")
})

test_that("9.1 — string con '<HTML' (mayúsculas) se detecta como tipo 'html' (case-insensitive)", {
  html_str <- "<HTML><BODY><P>Hola</P></BODY></HTML>"
  obj      <- list(contenido = html_str)
  slots    <- r_object_to_slots(obj)
  expect_equal(slots$type[slots$name == "contenido"], "html")
})

test_that("9.1 — vector atómico de longitud > 1 se detecta como tipo 'vector'", {
  obj   <- list(numeros = c(1.1, 2.2, 3.3, 4.4))
  slots <- r_object_to_slots(obj)
  expect_equal(slots$type[slots$name == "numeros"], "vector")
})

test_that("9.1 — escalar atómico (longitud 1) se detecta como tipo 'scalar'", {
  obj   <- list(valor = 42L)
  slots <- r_object_to_slots(obj)
  expect_equal(slots$type[slots$name == "valor"], "scalar")
})

test_that("9.1 — lista anidada se detecta como tipo 'unknown'", {
  obj   <- list(estructura = list(a = 1, b = list(c = 2)))
  slots <- r_object_to_slots(obj)
  expect_equal(slots$type[slots$name == "estructura"], "unknown")
})

test_that("9.1 — tier por defecto es 1L para todos los slots", {
  obj   <- list(a = 1L, b = c(1, 2), c = data.frame(x = 1))
  slots <- r_object_to_slots(obj)
  expect_true(all(slots$tier == 1L))
})

test_that("9.1 — tier_map hace override correctamente: c(a=2L) → slot 'a' tiene tier 2", {
  obj      <- list(a = 1L, b = 2L, c = 3L)
  tier_map <- c(a = 2L)
  slots    <- r_object_to_slots(obj, tier_map = tier_map)
  expect_equal(slots$tier[slots$name == "a"], 2L)
  expect_equal(slots$tier[slots$name == "b"], 1L)
  expect_equal(slots$tier[slots$name == "c"], 1L)
})

test_that("9.1 — round-trip de nombres: names(obj) == slots$name", {
  obj   <- list(alpha = 1L, beta = "texto", gamma = c(1, 2, 3))
  slots <- r_object_to_slots(obj)
  expect_equal(slots$name, names(obj))
})

# ═══════════════════════════════════════════════════════════════════════════════
# Task 9.2 — Property 2: .neven_dl_detect_type asigna el tipo correcto
#            para 6 tipos de input distintos según orden de prioridad
#
# **Validates: Requirements 9.2**
# ═══════════════════════════════════════════════════════════════════════════════

test_that("9.2 — Property 2: data.frame → 'table'", {
  input    <- data.frame(col1 = 1:5, col2 = letters[1:5])
  resultado <- .neven_dl_detect_type(input)
  expect_equal(resultado, "table")
})

test_that("9.2 — Property 2: matrix → 'table'", {
  input    <- matrix(1:4, nrow = 2, ncol = 2)
  resultado <- .neven_dl_detect_type(input)
  expect_equal(resultado, "table")
})

test_that("9.2 — Property 2: string HTML completo → 'html'", {
  input    <- "<html><body></body></html>"
  resultado <- .neven_dl_detect_type(input)
  expect_equal(resultado, "html")
})

test_that("9.2 — Property 2: vector numérico length > 1 → 'vector'", {
  input    <- c(1, 2, 3)
  resultado <- .neven_dl_detect_type(input)
  expect_equal(resultado, "vector")
})

test_that("9.2 — Property 2: entero escalar (length 1) → 'scalar'", {
  input    <- 42L
  resultado <- .neven_dl_detect_type(input)
  expect_equal(resultado, "scalar")
})

test_that("9.2 — Property 2: lista anidada → 'unknown'", {
  input    <- list(a = 1, b = 2)
  resultado <- .neven_dl_detect_type(input)
  expect_equal(resultado, "unknown")
})

# Verificación adicional de que data.frame tiene prioridad sobre la lógica
# de vector atómico (data.frame es también una lista atómica, pero se detecta
# como 'table' ANTES de llegar a la regla de vector).
test_that("9.2 — Property 2: data.frame tiene prioridad sobre reglas de vector/scalar", {
  df_1fila <- data.frame(x = 1)   # length == 1 col, pero sigue siendo table
  df_1col  <- data.frame(x = 1:3) # vector de longitud > 1, pero sigue siendo table
  expect_equal(.neven_dl_detect_type(df_1fila), "table")
  expect_equal(.neven_dl_detect_type(df_1col),  "table")
})

# ═══════════════════════════════════════════════════════════════════════════════
# Task 9.3 — Property 3: tier por defecto == 1L para 5 listas nombradas distintas
#            cuando no se provee tier_map
#
# **Validates: Requirements 9.3**
# ═══════════════════════════════════════════════════════════════════════════════

test_that("9.3 — Property 3 [lista 1]: escalares mixtos → todos tier == 1L", {
  obj   <- list(a = 1, b = "hello")
  slots <- r_object_to_slots(obj)
  expect_true(all(slots$tier == 1L),
              info = "Fallo en lista 1: list(a=1, b='hello')")
})

test_that("9.3 — Property 3 [lista 2]: data.frame + vector → todos tier == 1L", {
  obj   <- list(x = data.frame(col = 1:3), y = c(1, 2, 3))
  slots <- r_object_to_slots(obj)
  expect_true(all(slots$tier == 1L),
              info = "Fallo en lista 2: list(x=data.frame(col=1:3), y=c(1,2,3))")
})

test_that("9.3 — Property 3 [lista 3]: booleanos → todos tier == 1L", {
  obj   <- list(p = TRUE, q = FALSE)
  slots <- r_object_to_slots(obj)
  expect_true(all(slots$tier == 1L),
              info = "Fallo en lista 3: list(p=TRUE, q=FALSE)")
})

test_that("9.3 — Property 3 [lista 4]: matrix + entero → todos tier == 1L", {
  obj   <- list(m = matrix(1:4, 2, 2), n = 42L)
  slots <- r_object_to_slots(obj)
  expect_true(all(slots$tier == 1L),
              info = "Fallo en lista 4: list(m=matrix(1:4,2,2), n=42L)")
})

test_that("9.3 — Property 3 [lista 5]: HTML + lista anidada → todos tier == 1L", {
  obj   <- list(alpha = "<html>test</html>", beta = list(nested = 1))
  slots <- r_object_to_slots(obj)
  expect_true(all(slots$tier == 1L),
              info = "Fallo en lista 5: list(alpha='<html>test</html>', beta=list(nested=1))")
})
