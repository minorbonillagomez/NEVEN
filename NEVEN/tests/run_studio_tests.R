#!/usr/bin/env Rscript
# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN — Runner de tests Studio (Tarea 15)
# Ejecuta todos los test_*.R de la familia Studio y reporta un resumen.
#
# Uso:
#   Rscript tests/run_studio_tests.R              # desde raíz del repo
#   source("tests/run_studio_tests.R")            # desde R interactivo
# ═══════════════════════════════════════════════════════════════════════════════

if (!requireNamespace("testthat", quietly = TRUE)) {
  stop("Instala testthat: install.packages('testthat')")
}
library(testthat)

# ── Configurar directorio de trabajo ─────────────────────────────────────────
# Detectar raíz del repo: busca tests/ + libreria/R/ desde getwd() hacia arriba
.find_repo_root <- function() {
  # 1. Intentar extraer --file= del commandArgs
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- args[startsWith(args, "--file=")]
  if (length(file_arg) > 0L) {
    candidate <- tryCatch(
      dirname(dirname(normalizePath(sub("--file=", "", file_arg[1L])))),
      error = function(e) NULL
    )
    if (!is.null(candidate) && dir.exists(file.path(candidate, "tests")))
      return(candidate)
  }
  # 2. Caminar desde getwd() hacia arriba buscando tests/ + libreria/
  wd <- normalizePath(getwd())
  for (i in seq_len(5L)) {
    if (dir.exists(file.path(wd, "tests")) && dir.exists(file.path(wd, "libreria")))
      return(wd)
    parent <- dirname(wd)
    if (parent == wd) break
    wd <- parent
  }
  # 3. Fallback: directorio actual
  normalizePath(getwd())
}
script_dir <- .find_repo_root()
# Si terminamos dentro de tests/, subir un nivel
if (basename(script_dir) == "tests") script_dir <- dirname(script_dir)
cat("Directorio base:", script_dir, "\n\n")

# ── Lista de archivos de test Studio ─────────────────────────────────────────
test_files <- c(
  "tests/test_ad_funciones.R",
  "tests/test_rg_basico.R",
  "tests/test_rg_avanzado.R",
  "tests/test_rg_econometrico.R",
  "tests/test_gr_funciones.R"
)

# ── Ejecutar ──────────────────────────────────────────────────────────────────
cat("═══════════════════════════════════════════════════════════\n")
cat("  NEVEN Studio — Tests de Wrappers .Studio() (Tarea 15)\n")
cat("═══════════════════════════════════════════════════════════\n\n")

resultados <- list()
total_pass <- 0L; total_fail <- 0L; total_skip <- 0L; total_warn <- 0L

for (tf in test_files) {
  ruta <- file.path(script_dir, tf)
  if (!file.exists(ruta)) {
    cat("⚠️  ARCHIVO NO ENCONTRADO:", ruta, "\n")
    next
  }

  cat("──────────────────────────────────────────────────────────\n")
  cat("▶", basename(tf), "\n")

  res <- tryCatch(
    testthat::test_file(ruta, reporter = "minimal"),
    error = function(e) {
      cat("  ❌ ERROR AL CARGAR:", conditionMessage(e), "\n")
      NULL
    }
  )

  if (!is.null(res)) {
    df <- as.data.frame(res)
    p  <- sum(df$passed,  na.rm = TRUE)
    f  <- sum(df$failed,  na.rm = TRUE)
    s  <- sum(df$skipped, na.rm = TRUE)
    w  <- sum(df$warning, na.rm = TRUE)
    total_pass <- total_pass + p
    total_fail <- total_fail + f
    total_skip <- total_skip + s
    total_warn <- total_warn + w
    status_icon <- if (f > 0) "❌" else if (s == (p + s) && p == 0) "⏭" else "✅"
    cat(sprintf("  %s  pass=%-3d  fail=%-3d  skip=%-3d  warn=%-3d\n",
                status_icon, p, f, s, w))
    resultados[[tf]] <- list(pass=p, fail=f, skip=s, warn=w)
  }
}

# ── Resumen final ─────────────────────────────────────────────────────────────
cat("\n═══════════════════════════════════════════════════════════\n")
cat("  RESUMEN FINAL\n")
cat("═══════════════════════════════════════════════════════════\n")
cat(sprintf("  ✅ PASS:  %d\n", total_pass))
cat(sprintf("  ❌ FAIL:  %d\n", total_fail))
cat(sprintf("  ⏭ SKIP:  %d  (paquetes no instalados o wrappers no cargados)\n", total_skip))
cat(sprintf("  ⚠️  WARN:  %d\n", total_warn))
cat("───────────────────────────────────────────────────────────\n")
cat(sprintf("  TOTAL:   %d tests\n", total_pass + total_fail + total_skip))
cat("═══════════════════════════════════════════════════════════\n\n")

if (total_fail > 0) {
  cat("⚠️  Hay tests fallando. Revisar la salida de testthat arriba.\n")
} else if (total_pass == 0 && total_skip > 0) {
  cat("ℹ️  Todos los tests fueron omitidos. Verificar que:\n")
  cat("   1. Los paquetes R necesarios están instalados.\n")
  cat("   2. Los archivos .Studio.R están en C:/NEVEN/functions/\n")
  cat("   3. r_object_to_slots.R está en C:/NEVEN/startup/\n")
} else {
  cat("✅ Todos los tests ejecutados pasaron.\n")
}

# Retornar código de salida no cero si hay fallos (útil para CI)
if (total_fail > 0) quit(status = 1L) else quit(status = 0L)
