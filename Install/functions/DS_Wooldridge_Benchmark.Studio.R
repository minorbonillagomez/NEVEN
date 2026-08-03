# ===============================================================================
# NEVEN Data Lab — WOOLDRIDGE BENCHMARK SUITE (DS Family)
# Jeffrey Wooldridge, Introductory Econometrics (6a ed.)
# Sin variable_roles — carga sus propios datasets internamente
# ===============================================================================

DS_Wooldridge_Benchmark.Studio <- function(Caso = 1L) {

  Caso <- as.integer(Caso)
  if (is.na(Caso) || Caso < 1L || Caso > 6L)
    stop("'Caso' debe ser un entero de 1 a 6.")

  if (!requireNamespace("wooldridge", quietly = TRUE))
    stop("El paquete 'wooldridge' no esta instalado.")

  # ── Helper: formato tabla de coeficientes igual al libro ─────────────────────
  # Produce texto con la misma estructura que la referencia manual
  .fmt_coefs <- function(modelo, titulo) {
    ct <- summary(modelo)$coefficients
    sm <- summary(modelo)
    lines <- c(
      titulo,
      "",
      sprintf("Call: %s", deparse(formula(modelo))),
      "",
      "Coefficients:",
      sprintf("  %-20s %10s %10s %8s %10s",
              "Variable", "Estimate", "Std.Error", "t value", "Pr(>|t|)"),
      sprintf("  %-20s %10s %10s %8s %10s",
              "--------", "--------", "---------", "-------", "--------")
    )
    for (i in seq_len(nrow(ct))) {
      sig <- ifelse(ct[i, 4] < 0.001, "***",
             ifelse(ct[i, 4] < 0.01,  "**",
             ifelse(ct[i, 4] < 0.05,  "*",
             ifelse(ct[i, 4] < 0.10,  ".", ""))))
      lines <- c(lines,
        sprintf("  %-20s %10.4f %10.4f %8.3f %10.4f %s",
                rownames(ct)[i], ct[i,1], ct[i,2], ct[i,3], ct[i,4], sig))
    }
    lines <- c(lines, "  ---")
    lines <- c(lines, "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1")
    lines <- c(lines, "")
    lines <- c(lines,
      sprintf("  R-squared:     %.4f   Adj. R-squared: %.4f",
              sm$r.squared, sm$adj.r.squared))
    fstat <- sm$fstatistic
    if (!is.null(fstat)) {
      pf_val <- pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)
      lines <- c(lines,
        sprintf("  F-statistic: %.2f on %d and %d DF,  p-value: %.4e",
                fstat[1], fstat[2], fstat[3], pf_val))
    }
    lines <- c(lines,
      sprintf("  Observaciones: %d   Variables: %d",
              nrow(modelo$model), ncol(modelo$model) - 1))
    paste(lines, collapse = "\n")
  }

  # ── Helper: comparacion numerica ─────────────────────────────────────────────
  .comparar <- function(coefs_neven, coefs_ref, fuente) {
    nms <- intersect(names(coefs_neven), names(coefs_ref))
    if (length(nms) == 0) return("Sin coeficientes en comun para comparar.")
    filas <- vapply(nms, function(nm) {
      cn <- coefs_neven[[nm]]; cr <- coefs_ref[[nm]]; dif <- abs(cn - cr)
      sprintf("  %-20s  NEVEN: %9.4f  |  Libro: %9.4f  |  D: %.2e  %s",
              nm, cn, cr, dif, ifelse(dif < 0.01, "OK", "REVISAR"))
    }, character(1))
    mse <- mean((coefs_neven[nms] - coefs_ref[nms])^2)
    paste0(
      "=== VERIFICACION vs. ", fuente, " ===\n\n",
      paste(filas, collapse = "\n"),
      sprintf("\n\nMSE total: %.2e  %s  (umbral de referencia: 1e-7)",
              mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA" , "REVISAR"))
    )
  }

  # ── Referencias del libro ─────────────────────────────────────────────────────
  .ref <- list(
    `1` = paste(c(
      "=== REFERENCIA: Wooldridge Cap. 3, Ejemplo 3.2 ===",
      "",
      "Call: lm(wage ~ educ + exper + tenure)   Dataset: WAGE1",
      "",
      "Coefficients:",
      sprintf("  %-20s %10s %10s %8s %10s",
              "Variable", "Estimate", "Std.Error", "t value", "Pr(>|t|)"),
      sprintf("  %-20s %10s %10s %8s %10s",
              "--------", "--------", "---------", "-------", "--------"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "(Intercept)", -2.8727, 0.7289, -3.940, "<0.001 ***"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "educ",         0.5990, 0.0512, 11.698, "<0.001 ***"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "exper",        0.0223, 0.0120,  1.858, "0.063  ."),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "tenure",       0.1693, 0.0222,  7.630, "<0.001 ***"),
      "  ---",
      "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1",
      "",
      "  R-squared:     0.3061   Adj. R-squared: 0.3006",
      "  F-statistic: 55.25 on 3 and 522 DF,  p-value: < 2.2e-16",
      "  Observaciones: 526",
      "",
      "Interpretacion:",
      "  Un anio mas de educacion aumenta el salario en $0.60/hora (ceteris paribus).",
      "  Un anio de experiencia agrega $0.02/hora; la tenencia $0.17/hora."
    ), collapse = "\n"),

    `2` = paste(c(
      "=== REFERENCIA: Wooldridge Cap. 7, Ejemplo 7.12 ===",
      "",
      "Call: lm(prate ~ mrate + age + totemp)   Dataset: 401K",
      "",
      "Coefficients:",
      sprintf("  %-20s %10s %10s %8s %10s",
              "Variable", "Estimate", "Std.Error", "t value", "Pr(>|t|)"),
      sprintf("  %-20s %10s %10s %8s %10s",
              "--------", "--------", "---------", "-------", "--------"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "(Intercept)",  83.0755, 0.8777,  94.65, "<0.001 ***"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "mrate",         5.8611, 0.5269,  11.12, "<0.001 ***"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "age",           0.2690, 0.0455,   5.91, "<0.001 ***"),
      sprintf("  %-20s %10.7f %10.7f %8.3f %10s", "totemp",     -0.0000884, 0.0000117, -7.56, "<0.001 ***"),
      "  ---",
      "",
      "  R-squared: 0.1002",
      "  F-statistic: 66.38 on 3 and 1,800 DF",
      "",
      "Interpretacion:",
      "  Un incremento de 1 en la tasa de matching (mrate) aumenta",
      "  la participacion en el plan en 5.86 puntos porcentuales."
    ), collapse = "\n"),

    `3` = paste(c(
      "=== REFERENCIA: Wooldridge Cap. 14, Ejemplo 14.1 ===",
      "",
      "Call: plm(lscrap ~ hrsemp + lsales + lemploy | fcode)   Dataset: JTRAIN",
      "Modelo: Efectos Fijos (within estimator)",
      "",
      "Coefficients:",
      sprintf("  %-20s %10s %10s %8s %10s",
              "Variable", "Estimate", "Std.Error", "t value", "Pr(>|t|)"),
      sprintf("  %-20s %10s %10s %8s %10s",
              "--------", "--------", "---------", "-------", "--------"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "hrsemp",  -0.0401, 0.0210, -1.91, "0.059  ."),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "lsales",  -0.0512, 0.2045, -0.25, "0.803"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "lemploy",  0.0469, 0.3587,  0.13, "0.896"),
      "  ---",
      "",
      "  Observaciones: 135 (45 firmas x 3 anios, panel no balanceado)",
      "",
      "Interpretacion:",
      "  Un aumento del 10% en horas de entrenamiento reduce el desperdicio ~0.4%.",
      "  El efecto causal se purifica de la heterogeneidad entre firmas."
    ), collapse = "\n"),

    `4` = paste(c(
      "=== REFERENCIA: Wooldridge Cap. 17, Ejemplo 17.2 ===",
      "",
      "Call: tobit(cigs ~ lincome + lcigpric + educ + age + agesq + restaurn, left=0)",
      "Dataset: SMOKE",
      "",
      "Coefficients:",
      sprintf("  %-20s %10s %10s %8s %10s",
              "Variable", "Estimate", "Std.Error", "t value", "Pr(>|t|)"),
      sprintf("  %-20s %10s %10s %8s %10s",
              "--------", "--------", "---------", "-------", "--------"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "(Intercept)", -3.6398, 24.079, -0.15, "0.880"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "lincome",      0.8803,  0.728,  1.21, "0.228"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "lcigpric",    -0.7508,  5.773, -0.13, "0.897"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "educ",        -0.5014,  0.167, -3.00, "0.003 **"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "age",          0.7707,  0.160,  4.82, "<0.001 ***"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "agesq",       -0.0090,  0.002, -5.17, "<0.001 ***"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "restaurn",    -2.8251,  1.112, -2.54, "0.011 *"),
      "  ---",
      "",
      "  Log-Likelihood: -1376.8   Sigma: 13.817",
      "  Observaciones: 807  (54% censuradas en cero)",
      "",
      "Interpretacion:",
      "  Tobit corrige el sesgo de MCO cuando la mayoria no fuma (y=0).",
      "  Cada anio adicional de educacion reduce el consumo en ~0.5 cigarrillos."
    ), collapse = "\n"),

    `5` = paste(c(
      "=== REFERENCIA: Wooldridge Cap. 10, Ecuacion 10.15 ===",
      "",
      "Call: lm(gfr ~ pe + ww2 + pill + t)   Dataset: FERTIL1",
      "",
      "Coefficients:",
      sprintf("  %-20s %10s %10s %8s %10s",
              "Variable", "Estimate", "Std.Error", "t value", "Pr(>|t|)"),
      sprintf("  %-20s %10s %10s %8s %10s",
              "--------", "--------", "---------", "-------", "--------"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "(Intercept)",  98.6823, 3.2078, 30.77, "<0.001 ***"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "pe",           -0.0785, 0.0300, -2.62, "0.010 *"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "ww2",         -24.238,  7.458,  -3.25, "0.002 **"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "pill",        -31.594,  3.982,  -7.93, "<0.001 ***"),
      sprintf("  %-20s %10.4f %10.4f %8.3f %10s", "t",            -1.150,  0.192,  -5.99, "<0.001 ***"),
      "  ---",
      "",
      "  R-squared: 0.6633   Adj. R-squared: 0.6464",
      "  Observaciones: 72",
      "",
      "Interpretacion:",
      "  La pildora anticonceptiva redujo la tasa de fertilidad en ~31.6 puntos.",
      "  La tendencia t captura cambios estructurales no modelados."
    ), collapse = "\n"),

    `6` = paste(c(
      "=== REFERENCIA: Wooldridge Cap. 9 — CEOSAL1 ===",
      "",
      "Variable: salary (salario anual, miles USD)   N=209",
      "",
      "  Media:      1281.12",
      "  Mediana:    1037.00",
      "  Min:         223.00",
      "  Max:       14822.00",
      "  Q1:          736.00",
      "  Q3:         1534.00",
      "  IQR:         798.00",
      "",
      "  Umbral outlier (Q3 + 1.5*IQR):  2731.00",
      "  Outliers detectados:             ~11 CEOs",
      "",
      "Interpretacion:",
      "  Distribucion fuertemente asimetrica a la derecha.",
      "  Usar log(salary) es el estandar en modelos de salarios CEO."
    ), collapse = "\n")
  )

  # ════════════════════════════════════════════════════════════════════════════
  # EJECUCION POR CASO
  # ════════════════════════════════════════════════════════════════════════════

  if (Caso == 1L) {
    ds     <- wooldridge::wage1
    modelo <- lm(wage ~ educ + exper + tenure, data = ds)
    resultado_neven <- .fmt_coefs(modelo, "=== NEVEN: WAGE1 — lm(wage ~ educ + exper + tenure) ===")
    comparacion <- .comparar(coef(modelo),
                             c("(Intercept)" = -2.8727, "educ" = 0.5990,
                               "exper" = 0.0223, "tenure" = 0.1693),
                             "Wooldridge Cap. 3, Ejemplo 3.2")
  }

  else if (Caso == 2L) {
    ds     <- wooldridge::k401k
    modelo <- lm(prate ~ mrate + age + totemp, data = ds)
    resultado_neven <- .fmt_coefs(modelo, "=== NEVEN: 401K — lm(prate ~ mrate + age + totemp) ===")
    comparacion <- .comparar(coef(modelo),
                             c("(Intercept)" = 83.0755, "mrate" = 5.8611,
                               "age" = 0.2690, "totemp" = -8.84e-05),
                             "Wooldridge Cap. 7, Ejemplo 7.12")
  }

  else if (Caso == 3L) {
    if (!requireNamespace("plm", quietly = TRUE))
      stop("El paquete 'plm' no esta instalado.")
    ds    <- wooldridge::jtrain
    pdata <- plm::pdata.frame(ds, index = c("fcode", "year"))
    modelo <- plm::plm(lscrap ~ hrsemp + lsales + lemploy,
                       data = pdata, model = "within", effect = "individual")
    sm    <- summary(modelo)
    ct    <- sm$coefficients
    lines <- c(
      "=== NEVEN: JTRAIN — Panel Efectos Fijos (within) ===",
      "Call: plm(lscrap ~ hrsemp + lsales + lemploy | fcode)",
      "",
      "Coefficients:",
      sprintf("  %-20s %10s %10s %8s %10s",
              "Variable", "Estimate", "Std.Error", "t value", "Pr(>|t|)"),
      sprintf("  %-20s %10s %10s %8s %10s",
              "--------", "--------", "---------", "-------", "--------")
    )
    for (i in seq_len(nrow(ct))) {
      sig <- ifelse(ct[i, 4] < 0.001, "***",
             ifelse(ct[i, 4] < 0.01,  "**",
             ifelse(ct[i, 4] < 0.05,  "*",
             ifelse(ct[i, 4] < 0.10,  ".", ""))))
      lines <- c(lines,
        sprintf("  %-20s %10.4f %10.4f %8.3f %10.4f %s",
                rownames(ct)[i], ct[i,1], ct[i,2], ct[i,3], ct[i,4], sig))
    }
    lines <- c(lines, "", sprintf("  Observaciones: %d", nrow(ds[!is.na(ds$lscrap),])))
    resultado_neven <- paste(lines, collapse = "\n")
    comparacion <- .comparar(coef(modelo),
                             c("hrsemp" = -0.0401, "lsales" = -0.0512, "lemploy" = 0.0469),
                             "Wooldridge Cap. 14, Ejemplo 14.1")
  }

  else if (Caso == 4L) {
    if (!requireNamespace("AER", quietly = TRUE))
      stop("El paquete 'AER' no esta instalado.")
    ds     <- wooldridge::smoke
    modelo <- AER::tobit(cigs ~ lincome + lcigpric + educ + age + agesq + restaurn,
                         left = 0, data = ds)
    sm     <- summary(modelo)
    ct     <- sm$coefficients
    lines  <- c(
      "=== NEVEN: SMOKE — Tobit (censura en cero) ===",
      "Call: tobit(cigs ~ lincome + lcigpric + educ + age + agesq + restaurn, left=0)",
      "",
      "Coefficients:",
      sprintf("  %-20s %10s %10s %8s %10s",
              "Variable", "Estimate", "Std.Error", "t value", "Pr(>|t|)"),
      sprintf("  %-20s %10s %10s %8s %10s",
              "--------", "--------", "---------", "-------", "--------")
    )
    for (nm in setdiff(rownames(ct), "Log(scale)")) {
      sig <- ifelse(ct[nm, 4] < 0.001, "***",
             ifelse(ct[nm, 4] < 0.01,  "**",
             ifelse(ct[nm, 4] < 0.05,  "*",
             ifelse(ct[nm, 4] < 0.10,  ".", ""))))
      lines <- c(lines,
        sprintf("  %-20s %10.4f %10.4f %8.3f %10.4f %s",
                nm, ct[nm,1], ct[nm,2], ct[nm,3], ct[nm,4], sig))
    }
    ll  <- tryCatch(round(logLik(modelo)[[1]], 1), error = function(e) NA)
    sig <- tryCatch(round(exp(coef(modelo)["Log(scale)"]), 3), error = function(e) NA)
    lines <- c(lines, "",
               sprintf("  Log-Likelihood: %s   Sigma: %s", ll, sig),
               sprintf("  Obs: %d  Censuradas: %d (%.0f%%)",
                       nrow(ds), sum(ds$cigs == 0, na.rm = TRUE),
                       100 * mean(ds$cigs == 0, na.rm = TRUE)))
    resultado_neven <- paste(lines, collapse = "\n")
    comparacion <- .comparar(
      coef(modelo)[setdiff(names(coef(modelo)), "Log(scale)")],
      c("(Intercept)" = -3.6398, "lincome" = 0.8803, "lcigpric" = -0.7508,
        "educ" = -0.5014, "age" = 0.7707, "agesq" = -0.0090, "restaurn" = -2.8251),
      "Wooldridge Cap. 17, Ejemplo 17.2"
    )
  }

  else if (Caso == 5L) {
    if (!requireNamespace("lmtest", quietly = TRUE))
      stop("El paquete 'lmtest' no esta instalado.")
    ds     <- wooldridge::fertil1
    modelo <- lm(gfr ~ pe + ww2 + pill + t, data = ds)
    reset  <- tryCatch({
      r <- lmtest::resettest(modelo, power = 2:3, type = "fitted")
      sprintf("  F = %.3f, df = (%d, %d), p-valor = %.4f  %s",
              r$statistic, r$parameter[1], r$parameter[2], r$p.value,
              ifelse(r$p.value < 0.05, "-> FORMA FUNCIONAL PROBLEMATICA",
                     "-> Forma funcional adecuada"))
    }, error = function(e) paste("  No disponible:", e$message))
    resultado_neven <- paste(c(
      .fmt_coefs(modelo, "=== NEVEN: FERTIL1 — lm(gfr ~ pe + ww2 + pill + t) ==="),
      "",
      "--- Prueba RESET de Ramsey ---",
      reset
    ), collapse = "\n")
    comparacion <- .comparar(coef(modelo),
                             c("(Intercept)" = 98.6823, "pe" = -0.0785,
                               "ww2" = -24.238, "pill" = -31.594, "t" = -1.150),
                             "Wooldridge Cap. 10, Ec. 10.15")
  }

  else {
    ds    <- wooldridge::ceosal1
    x     <- ds$salary
    q1    <- quantile(x, 0.25); q3 <- quantile(x, 0.75); iqr <- q3 - q1
    lsup  <- q3 + 1.5 * iqr
    outs  <- sort(x[x > lsup], decreasing = TRUE)
    resultado_neven <- paste(c(
      "=== NEVEN: CEOSAL1 — Estadistica Descriptiva ===",
      "Variable: salary (salario anual, miles USD)",
      "",
      sprintf("  Media:      %.2f", mean(x)),
      sprintf("  Mediana:    %.2f", median(x)),
      sprintf("  Min:        %.2f   Max: %.2f", min(x), max(x)),
      sprintf("  Q1:         %.2f", q1),
      sprintf("  Q3:         %.2f", q3),
      sprintf("  IQR:        %.2f", iqr),
      "",
      sprintf("  Umbral outlier (Q3 + 1.5*IQR): %.2f", lsup),
      sprintf("  Outliers detectados:            %d observaciones", length(outs)),
      if (length(outs) > 0)
        paste0("  Valores: ", paste(head(outs, 10), collapse = "  "),
               if (length(outs) > 10) " ..." else "")
      else "  (sin outliers)"
    ), collapse = "\n")
    ref_m <- 1281.12; ref_med <- 1037; ref_out <- 11
    comparacion <- paste(c(
      "=== VERIFICACION vs. Wooldridge Cap. 9 ===",
      "",
      sprintf("  Media:    NEVEN %8.2f  |  Ref: %8.2f  |  %s",
              mean(x), ref_m, ifelse(abs(mean(x) - ref_m) < 5, "OK", "REVISAR")),
      sprintf("  Mediana:  NEVEN %8.2f  |  Ref: %8.2f  |  %s",
              median(x), ref_med, ifelse(abs(median(x) - ref_med) < 10, "OK", "REVISAR")),
      sprintf("  Outliers: NEVEN %8d  |  Ref: %8s  |  %s",
              length(outs), paste0("~", ref_out),
              ifelse(abs(length(outs) - ref_out) <= 2, "OK", "REVISAR"))
    ), collapse = "\n")
  }

  return(r_object_to_slots(
    list(
      resultado_NEVEN  = resultado_neven,
      referencia_libro = .ref[[as.character(Caso)]],
      verificacion     = comparacion
    ),
    tier_map = c(resultado_NEVEN = 1L, referencia_libro = 1L, verificacion = 1L)
  ))
}
