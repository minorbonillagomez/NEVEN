# ===============================================================================
# NEVEN Data Lab — WOOLDRIDGE BENCHMARK SUITE (DS Family)
# Validación de precisión estadística contra los ejemplos canónicos del libro
# Jeffrey Wooldridge, Introductory Econometrics (6ª ed.)
# ===============================================================================
# PROPÓSITO:
#   Ejecuta 6 modelos con los datasets y especificaciones exactas del libro.
#   Las variables Y y X vienen preseleccionadas según el ejemplo canónico.
#   El usuario puede modificarlas para explorar especificaciones alternativas.
#
#   Si data_Y y data_X NO se asignan → usa las variables del libro (default).
#   Si data_Y y data_X SÍ se asignan → usa las del usuario (experimental).
#
# SALIDA: texto puro via capture.output() — igual que la consola de R.
# ===============================================================================

DS_Wooldridge_Benchmark.Studio <- function(data_Y  = NULL,
                                             data_X  = NULL,
                                             Caso    = 1L) {

  Caso <- as.integer(Caso)
  if (is.na(Caso) || Caso < 1L || Caso > 6L)
    stop("'Caso' debe ser un entero de 1 a 6.")

  if (!requireNamespace("wooldridge", quietly = TRUE))
    stop("El paquete 'wooldridge' no está instalado.")

  # ── Helper: capture.output limpio de caracteres de control ───────────────────
  # Usa [[:cntrl:]] (clase POSIX) para eliminar caracteres de control.
  # Preserva \n y \t que son válidos. Evita \x00 que R prohíbe en código fuente.
  .to_text <- function(...) {
    lines <- capture.output(...)
    lines <- enc2utf8(lines)
    # [[:cntrl:]] = caracteres ASCII 0-31 y 127; luego restauramos newlines
    lines <- gsub("[[:cntrl:]]", " ", lines)
    paste(lines, collapse = "\n")
  }

  # ── Helper: detecta si el usuario asignó columnas (no NULL, no vacío) ─────────
  .tiene_datos <- function(d) {
    !is.null(d) && is.data.frame(d) && nrow(d) > 0 && ncol(d) > 0
  }

  # ── Helper: comparación coeficiente a coeficiente ────────────────────────────
  .comparar_coefs <- function(coefs_neven, coefs_ref, fuente) {
    nms <- intersect(names(coefs_neven), names(coefs_ref))
    if (length(nms) == 0) return("Sin coeficientes en comun para comparar.")
    filas <- vapply(nms, function(nm) {
      cn <- coefs_neven[[nm]]; cr <- coefs_ref[[nm]]; dif <- abs(cn - cr)
      sprintf("  %-18s  NEVEN: %10.6f  |  Libro: %10.6f  |  D: %.2e  %s",
              nm, cn, cr, dif, ifelse(dif^2 < 1e-7, "OK", "REVISAR"))
    }, character(1))
    mse <- mean((coefs_neven[nms] - coefs_ref[nms])^2)
    paste0("=== VERIFICACION vs. ", fuente, " ===\n\n",
           paste(filas, collapse = "\n"),
           sprintf("\n\nMSE total: %.2e  %s  (umbral: 1e-7)",
                   mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR")))
  }

  # ── Referencia del libro (texto literal) ─────────────────────────────────────
  .ref <- list(
    `1` = paste(c(
      "=== REFERENCIA: Wooldridge, Cap. 3, Ejemplo 3.2 ===",
      "Dataset: WAGE1 - salarios por hora, educacion y experiencia",
      "",
      "Call: lm(wage ~ educ + exper + tenure)",
      "Coefficients:",
      "  (Intercept)    educ    exper   tenure",
      "    -2.8727     0.5990   0.0223   0.1693",
      "",
      "R-squared: 0.3061   Adj. R-squared: 0.3006",
      "F-statistic: 55.25 on 3 and 522 DF,  p-value: < 2.2e-16",
      "",
      "Interpretacion Wooldridge:",
      "  Un anio adicional de educacion aumenta el salario en $0.60/hora.",
      "  Un anio de experiencia agrega $0.022/hora, la tenencia $0.169/hora."
    ), collapse = "\n"),

    `2` = paste(c(
      "=== REFERENCIA: Wooldridge, Cap. 7, Ejemplo 7.12 ===",
      "Dataset: 401K - participacion en plan de pension",
      "",
      "Modelo Lineal de Probabilidad: prate ~ mrate + age + totemp",
      "Coeficientes principales:",
      "  mrate:    5.8611  (tasa de matching del empleador)",
      "  age:      0.2690  (antiguedad del plan)",
      "  totemp: -0.0000884 (empleados totales)",
      "",
      "R-squared: 0.1002",
      "",
      "Interpretacion: Un incremento de 1 en mrate aumenta la participacion 5.86 pp."
    ), collapse = "\n"),

    `3` = paste(c(
      "=== REFERENCIA: Wooldridge, Cap. 14, Ejemplo 14.1 ===",
      "Dataset: JTRAIN - entrenamiento laboral 1987-1989 (panel)",
      "",
      "Efectos Fijos (within): lscrap ~ hrsemp + lsales + lemploy | fcode",
      "Coef. hrsemp: -0.0401   SE: 0.0210   t: -1.91",
      "",
      "Obs: 135 (45 firmas x 3 anios, panel no balanceado)",
      "",
      "Interpretacion: 10% mas en horas de entrenamiento reduce el desperdicio ~0.4%."
    ), collapse = "\n"),

    `4` = paste(c(
      "=== REFERENCIA: Wooldridge, Cap. 17, Ejemplo 17.2 ===",
      "Dataset: SMOKE - cigarrillos fumados por dia (censurado en cero)",
      "",
      "Tobit: cigs ~ lincome + lcigpric + educ + age + agesq + restaurn",
      "Coeficientes principales:",
      "  lincome:  0.880   lcigpric: -0.751   educ: -0.501",
      "  restaurn: -2.825  (restricciones en restaurantes)",
      "",
      "Log-Likelihood: -1376.8   Sigma: 13.817",
      "",
      "Nota: 54% de la muestra no fuma. Tobit corrige el sesgo de MCO."
    ), collapse = "\n"),

    `5` = paste(c(
      "=== REFERENCIA: Wooldridge, Cap. 10, Ec. 10.15 ===",
      "Dataset: FERTIL1 - tasa de fertilidad EEUU 1913-1984",
      "",
      "lm(gfr ~ pe + ww2 + pill + t)",
      "Coeficientes:",
      "  pe: -0.0785   ww2: -24.238   pill: -31.594   t: -1.150",
      "",
      "R-squared: 0.663",
      "",
      "Interpretacion: La pildora redujo la fertilidad en ~31.6 puntos."
    ), collapse = "\n"),

    `6` = paste(c(
      "=== REFERENCIA: Wooldridge, Cap. 9 ===",
      "Dataset: CEOSAL1 - salarios de CEO (miles USD)",
      "",
      "salary: N=209   Media=1281.12   Mediana=1037",
      "Min=223   Max=14822   Q1=736   Q3=1534   IQR=798",
      "Outliers (>Q3 + 1.5*IQR = 2731): aprox. 11 CEOs",
      "",
      "Nota: Distribucion fuertemente asimetrica. Usar log(salary) es estandar."
    ), collapse = "\n")
  )

  # ══════════════════════════════════════════════════════════════════════════════
  # DESPACHO POR CASO
  # ══════════════════════════════════════════════════════════════════════════════

  if (Caso == 1L) {
    # ── W-001: WAGE1 — MCO múltiple (Cap. 3) ─────────────────────────────────
    ds <- wooldridge::wage1

    if (.tiene_datos(data_Y) && .tiene_datos(data_X)) {
      # Modo usuario: combinar datos enviados desde Data Studio
      y_col  <- names(data_Y)[1]
      x_cols <- names(data_X)
      df     <- cbind(data_Y, data_X)
      fml    <- reformulate(termlabels = x_cols, response = y_col)
      nota   <- paste0("Especificacion del usuario: ", y_col, " ~ ",
                       paste(x_cols, collapse = " + "))
    } else {
      # Modo default: especificacion canonica del libro
      df     <- ds
      fml    <- wage ~ educ + exper + tenure
      nota   <- "Especificacion canonica Wooldridge Cap. 3, Ejemplo 3.2"
    }
    modelo <- lm(fml, data = df)
    resultado_neven <- paste0(nota, "\n\n", .to_text(summary(modelo)))
    coefs_ref <- c("(Intercept)" = -2.8727, "educ" = 0.5990,
                   "exper" = 0.0223, "tenure" = 0.1693)
    comparacion <- if (.tiene_datos(data_Y)) {
      "Modo usuario: comparacion con referencia no aplica para especificacion personalizada."
    } else {
      .comparar_coefs(coef(modelo), coefs_ref, "Cap. 3, Ejemplo 3.2")
    }
  }

  else if (Caso == 2L) {
    # ── W-002: 401K — LPM (Cap. 7) ───────────────────────────────────────────
    ds <- wooldridge::k401k
    if (.tiene_datos(data_Y) && .tiene_datos(data_X)) {
      y_col <- names(data_Y)[1]; x_cols <- names(data_X)
      df    <- cbind(data_Y, data_X)
      fml   <- reformulate(x_cols, response = y_col)
      nota  <- paste0("Especificacion del usuario: ", y_col, " ~ ",
                      paste(x_cols, collapse = " + "))
    } else {
      df   <- ds; fml <- prate ~ mrate + age + totemp
      nota <- "Especificacion canonica Wooldridge Cap. 7, Ejemplo 7.12"
    }
    modelo <- lm(fml, data = df)
    resultado_neven <- paste0(nota, "\n\n", .to_text(summary(modelo)))
    coefs_ref <- c("(Intercept)" = 83.0755, "mrate" = 5.8611,
                   "age" = 0.2690, "totemp" = -8.84e-05)
    comparacion <- if (.tiene_datos(data_Y)) {
      "Modo usuario: comparacion no aplica."
    } else {
      .comparar_coefs(coef(modelo), coefs_ref, "Cap. 7, Ejemplo 7.12")
    }
  }

  else if (Caso == 3L) {
    # ── W-003: JTRAIN — Panel Efectos Fijos (Cap. 14) ─────────────────────────
    if (!requireNamespace("plm", quietly = TRUE))
      stop("El paquete 'plm' no esta instalado.")
    ds    <- wooldridge::jtrain
    pdata <- plm::pdata.frame(ds, index = c("fcode", "year"))
    if (.tiene_datos(data_Y) && .tiene_datos(data_X)) {
      y_col <- names(data_Y)[1]; x_cols <- names(data_X)
      pdata2 <- plm::pdata.frame(cbind(data_Y, data_X, ds[, c("fcode","year")]),
                                  index = c("fcode","year"))
      fml    <- reformulate(x_cols, response = y_col)
      nota   <- paste0("Especificacion del usuario: ", y_col, " ~ ",
                       paste(x_cols, collapse = " + "), " | fcode")
      modelo <- plm::plm(fml, data = pdata2, model = "within", effect = "individual")
    } else {
      nota   <- "Especificacion canonica Wooldridge Cap. 14, Ejemplo 14.1"
      modelo <- plm::plm(lscrap ~ hrsemp + lsales + lemploy,
                         data = pdata, model = "within", effect = "individual")
    }
    resultado_neven <- paste0(nota, "\n\n", .to_text(summary(modelo)))
    coefs_ref <- c("hrsemp" = -0.0401, "lsales" = -0.0512, "lemploy" = 0.0469)
    comparacion <- if (.tiene_datos(data_Y)) {
      "Modo usuario: comparacion no aplica."
    } else {
      .comparar_coefs(coef(modelo), coefs_ref, "Cap. 14, Ejemplo 14.1")
    }
  }

  else if (Caso == 4L) {
    # ── W-004: SMOKE — Tobit (Cap. 17) ───────────────────────────────────────
    if (!requireNamespace("AER", quietly = TRUE))
      stop("El paquete 'AER' no esta instalado.")
    ds <- wooldridge::smoke
    if (.tiene_datos(data_Y) && .tiene_datos(data_X)) {
      y_col <- names(data_Y)[1]; x_cols <- names(data_X)
      df    <- cbind(data_Y, data_X)
      fml   <- reformulate(x_cols, response = y_col)
      nota  <- paste0("Modo usuario (Tobit, censura en 0): ", y_col, " ~ ",
                      paste(x_cols, collapse = " + "))
      modelo <- AER::tobit(fml, left = 0, data = df)
    } else {
      nota   <- "Especificacion canonica Wooldridge Cap. 17, Ejemplo 17.2"
      modelo <- AER::tobit(cigs ~ lincome + lcigpric + educ + age + agesq + restaurn,
                           left = 0, data = ds)
    }
    resultado_neven <- paste0(nota, "\n\n", .to_text(summary(modelo)))
    coefs_ref <- c("(Intercept)" = -3.6398, "lincome" = 0.8803,
                   "lcigpric" = -0.7508, "educ" = -0.5014,
                   "age" = 0.7707, "agesq" = -0.0090, "restaurn" = -2.8251)
    comparacion <- if (.tiene_datos(data_Y)) {
      "Modo usuario: comparacion no aplica."
    } else {
      .comparar_coefs(coef(modelo)[names(coef(modelo)) != "Log(scale)"],
                      coefs_ref, "Cap. 17, Ejemplo 17.2")
    }
  }

  else if (Caso == 5L) {
    # ── W-005: FERTIL1 — Serie de tiempo + RESET (Cap. 10) ────────────────────
    if (!requireNamespace("lmtest", quietly = TRUE))
      stop("El paquete 'lmtest' no esta instalado.")
    ds <- wooldridge::fertil1
    if (.tiene_datos(data_Y) && .tiene_datos(data_X)) {
      y_col <- names(data_Y)[1]; x_cols <- names(data_X)
      df    <- cbind(data_Y, data_X)
      fml   <- reformulate(x_cols, response = y_col)
      nota  <- paste0("Especificacion del usuario: ", y_col, " ~ ",
                      paste(x_cols, collapse = " + "))
    } else {
      df <- ds; fml <- gfr ~ pe + ww2 + pill + t
      nota <- "Especificacion canonica Wooldridge Cap. 10, Ec. 10.15"
    }
    modelo   <- lm(fml, data = df)
    reset_sm <- tryCatch(
      .to_text(lmtest::resettest(modelo, power = 2:3, type = "fitted")),
      error = function(e) paste("RESET no disponible:", e$message)
    )
    resultado_neven <- paste0(nota, "\n\n", .to_text(summary(modelo)),
                              "\n\n--- Prueba RESET de Ramsey ---\n", reset_sm)
    coefs_ref <- c("(Intercept)" = 98.6823, "pe" = -0.0785,
                   "ww2" = -24.238, "pill" = -31.594, "t" = -1.150)
    comparacion <- if (.tiene_datos(data_Y)) {
      "Modo usuario: comparacion no aplica."
    } else {
      .comparar_coefs(coef(modelo), coefs_ref, "Cap. 10, Ec. 10.15")
    }
  }

  else {
    # ── W-006: CEOSAL1 — Descriptiva + outliers (Cap. 9) ──────────────────────
    ds <- wooldridge::ceosal1
    var_nm <- if (.tiene_datos(data_Y)) names(data_Y)[1] else "salary"
    x_vec  <- if (.tiene_datos(data_Y)) data_Y[[1]] else ds$salary

    q1 <- quantile(x_vec, 0.25); q3 <- quantile(x_vec, 0.75); iqr <- q3 - q1
    lim_sup  <- q3 + 1.5 * iqr
    outliers <- x_vec[x_vec > lim_sup]

    resultado_neven <- paste(c(
      paste0("Variable analizada: ", var_nm),
      "",
      "Summary:",
      .to_text(summary(x_vec)),
      "",
      sprintf("Q1: %.1f   Q3: %.1f   IQR: %.1f", q1, q3, iqr),
      sprintf("Umbral outlier superior (Q3 + 1.5*IQR): %.1f", lim_sup),
      sprintf("Outliers detectados: %d", length(outliers)),
      if (length(outliers) > 0)
        paste0("Valores: ", paste(sort(outliers, decreasing = TRUE), collapse = "  "))
      else ""
    ), collapse = "\n")

    ref_media  <- 1281.12; ref_median <- 1037; ref_out <- 11
    comparacion <- paste(c(
      "=== VERIFICACION vs. Wooldridge Cap. 9 ===",
      sprintf("  Media:    NEVEN %.2f  |  Ref: %.2f  |  %s",
              mean(x_vec), ref_media,
              ifelse(abs(mean(x_vec) - ref_media) < 5, "OK", "REVISAR")),
      sprintf("  Mediana:  NEVEN %.1f  |  Ref: %.1f  |  %s",
              median(x_vec), ref_median,
              ifelse(abs(median(x_vec) - ref_median) < 10, "OK", "REVISAR")),
      sprintf("  Outliers: NEVEN %d       |  Ref: ~%d     |  %s",
              length(outliers), ref_out,
              ifelse(abs(length(outliers) - ref_out) <= 2, "OK", "REVISAR"))
    ), collapse = "\n")
  }

  # ── Retorno ──────────────────────────────────────────────────────────────────
  return(r_object_to_slots(
    list(
      resultado_NEVEN  = resultado_neven,
      referencia_libro = .ref[[as.character(Caso)]],
      verificacion     = comparacion
    ),
    tier_map = c(resultado_NEVEN = 1L, referencia_libro = 1L, verificacion = 1L)
  ))
}
