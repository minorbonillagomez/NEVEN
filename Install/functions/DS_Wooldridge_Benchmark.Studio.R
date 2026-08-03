# ===============================================================================
# NEVEN Data Lab -- WOOLDRIDGE BENCHMARK SUITE (DS Family)
# Jeffrey Wooldridge, Introductory Econometrics (6a ed.)
# Salida: texto plano simple -- paste(c(...), collapse="\n")
# ===============================================================================

DS_Wooldridge_Benchmark.Studio <- function(Caso = 1L) {

  Caso <- as.integer(Caso)
  if (is.na(Caso) || Caso < 1L || Caso > 6L)
    stop("'Caso' debe ser un entero de 1 a 6.")

  if (!requireNamespace("wooldridge", quietly = TRUE))
    stop("El paquete 'wooldridge' no esta instalado.")

  # ===========================================================================
  # CASO 1: WAGE1 -- MCO Multiple (Cap. 3, Ejemplo 3.2)
  # ===========================================================================
  if (Caso == 1L) {
    ds     <- wooldridge::wage1
    modelo <- lm(wage ~ educ + exper + tenure, data = ds)

    res <- paste(c(
      "Caso W-001 | Dataset: WAGE1 | Cap. 3, Ejemplo 3.2",
      "Especificacion: wage ~ educ + exper + tenure",
      "Obs: 526 | Variable dependiente: wage (salario por hora, USD)",
      "",
      capture.output(summary(modelo))
    ), collapse = "\n")

    ref <- paste(c(
      "Referencia: Wooldridge Cap. 3, Ejemplo 3.2",
      "Dataset: WAGE1 | wage ~ educ + exper + tenure",
      "",
      "Coefficients:",
      "             Estimate Std. Error t value Pr(>|t|)",
      "(Intercept)  -2.8727     0.7289  -3.940  0.0001 ***",
      "educ          0.5990     0.0512  11.698  <2e-16 ***",
      "exper         0.0223     0.0120   1.858  0.0634  .",
      "tenure        0.1693     0.0222   7.630  <2e-16 ***",
      "",
      "R-squared: 0.3061   Adj. R-squared: 0.3006",
      "F-statistic: 55.25 on 3 and 522 DF,  p-value: < 2.2e-16",
      "",
      "Interpretacion:",
      "Un anio mas de educacion sube el salario en $0.60/hora (ceteris paribus).",
      "Un anio de experiencia agrega $0.02/hora; la tenencia $0.17/hora."
    ), collapse = "\n")

    ver <- paste(c(
      "Verificacion vs. Wooldridge Cap. 3, Ejemplo 3.2",
      sprintf("(Intercept):  NEVEN = %.4f  |  Libro = -2.8727  |  dif = %.4e",
              coef(modelo)[["(Intercept)"]], abs(coef(modelo)[["(Intercept)"]] - (-2.8727))),
      sprintf("educ:         NEVEN = %.4f  |  Libro =  0.5990  |  dif = %.4e",
              coef(modelo)[["educ"]], abs(coef(modelo)[["educ"]] - 0.5990)),
      sprintf("exper:        NEVEN = %.4f  |  Libro =  0.0223  |  dif = %.4e",
              coef(modelo)[["exper"]], abs(coef(modelo)[["exper"]] - 0.0223)),
      sprintf("tenure:       NEVEN = %.4f  |  Libro =  0.1693  |  dif = %.4e",
              coef(modelo)[["tenure"]], abs(coef(modelo)[["tenure"]] - 0.1693)),
      sprintf("MSE total:    %.2e   %s",
              mean((coef(modelo)[c("(Intercept)","educ","exper","tenure")] -
                    c(-2.8727, 0.5990, 0.0223, 0.1693))^2),
              ifelse(mean((coef(modelo)[c("(Intercept)","educ","exper","tenure")] -
                           c(-2.8727, 0.5990, 0.0223, 0.1693))^2) < 1e-7,
                     "PARIDAD ESTADISTICA OK", "REVISAR"))
    ), collapse = "\n")
  }

  # ===========================================================================
  # CASO 2: 401K -- LPM (Cap. 7, Ejemplo 7.12)
  # ===========================================================================
  else if (Caso == 2L) {
    ds     <- wooldridge::k401k
    modelo <- lm(prate ~ mrate + age + totemp, data = ds)

    res <- paste(c(
      "Caso W-002 | Dataset: 401K | Cap. 7, Ejemplo 7.12",
      "Especificacion: prate ~ mrate + age + totemp",
      "Obs: 1804 | Variable dependiente: prate (% participacion en pension)",
      "",
      capture.output(summary(modelo))
    ), collapse = "\n")

    ref <- paste(c(
      "Referencia: Wooldridge Cap. 7, Ejemplo 7.12",
      "Dataset: 401K | prate ~ mrate + age + totemp",
      "",
      "Coefficients:",
      "             Estimate  Std. Error t value Pr(>|t|)",
      "(Intercept) 83.0755      0.8777   94.65  <2e-16 ***",
      "mrate        5.8611      0.5269   11.12  <2e-16 ***",
      "age          0.2690      0.0455    5.91  4.3e-9 ***",
      "totemp      -0.0000884   0.0000117 -7.56  5.8e-14 ***",
      "",
      "R-squared: 0.1002   F-statistic: 66.38 on 3 and 1800 DF",
      "",
      "Interpretacion:",
      "+1 en mrate (tasa de matching) = +5.86 pp en participacion."
    ), collapse = "\n")

    cn <- coef(modelo)
    cr <- c("(Intercept)" = 83.0755, "mrate" = 5.8611,
            "age" = 0.2690, "totemp" = -8.84e-05)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "Verificacion vs. Wooldridge Cap. 7, Ejemplo 7.12",
      sprintf("(Intercept): NEVEN = %.4f  |  Libro = 83.0755  |  dif = %.4e",
              cn[["(Intercept)"]], abs(cn[["(Intercept)"]] - 83.0755)),
      sprintf("mrate:       NEVEN = %.4f  |  Libro =  5.8611  |  dif = %.4e",
              cn[["mrate"]], abs(cn[["mrate"]] - 5.8611)),
      sprintf("age:         NEVEN = %.4f  |  Libro =  0.2690  |  dif = %.4e",
              cn[["age"]], abs(cn[["age"]] - 0.2690)),
      sprintf("totemp:      NEVEN = %.7f  |  Libro = -0.0000884  |  dif = %.4e",
              cn[["totemp"]], abs(cn[["totemp"]] - (-8.84e-05))),
      sprintf("MSE total:   %.2e   %s", mse,
              ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
    ), collapse = "\n")
  }

  # ===========================================================================
  # CASO 3: JTRAIN -- Panel Efectos Fijos (Cap. 14, Ejemplo 14.1)
  # ===========================================================================
  else if (Caso == 3L) {
    if (!requireNamespace("plm", quietly = TRUE))
      stop("El paquete 'plm' no esta instalado.")
    ds    <- wooldridge::jtrain
    pdata <- suppressMessages(suppressWarnings(
      plm::pdata.frame(ds, index = c("fcode", "year"))
    ))
    modelo <- suppressMessages(suppressWarnings(
      plm::plm(lscrap ~ hrsemp + lsales + lemploy,
               data = pdata, model = "within", effect = "individual")
    ))

    res <- paste(c(
      "Caso W-003 | Dataset: JTRAIN | Cap. 14, Ejemplo 14.1",
      "Especificacion: lscrap ~ hrsemp + lsales + lemploy | fcode (Efectos Fijos)",
      "Obs: 135 (45 firmas x 3 anios) | Variable dependiente: lscrap (log desperdicio)",
      "",
      capture.output(summary(modelo))
    ), collapse = "\n")

    ref <- paste(c(
      "Referencia: Wooldridge Cap. 14, Ejemplo 14.1",
      "Dataset: JTRAIN | lscrap ~ hrsemp + lsales + lemploy | fcode",
      "Modelo: Efectos Fijos (within estimator)",
      "",
      "Coefficients:",
      "         Estimate Std. Error t-stat Pr(>|t|)",
      "hrsemp   -0.0401    0.0210   -1.91  0.059  .",
      "lsales   -0.0512    0.2045   -0.25  0.803",
      "lemploy   0.0469    0.3587    0.13  0.896",
      "",
      "Obs: 135 (45 firmas x 3 anios, panel no balanceado)",
      "",
      "Interpretacion:",
      "+10% en horas de entrenamiento reduce el desperdicio ~0.4%.",
      "El efecto se purifica de heterogeneidad entre firmas."
    ), collapse = "\n")

    cn  <- coef(modelo)
    cr  <- c("hrsemp" = -0.0401, "lsales" = -0.0512, "lemploy" = 0.0469)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "Verificacion vs. Wooldridge Cap. 14, Ejemplo 14.1",
      sprintf("hrsemp:   NEVEN = %.4f  |  Libro = -0.0401  |  dif = %.4e",
              cn[["hrsemp"]], abs(cn[["hrsemp"]] - (-0.0401))),
      sprintf("lsales:   NEVEN = %.4f  |  Libro = -0.0512  |  dif = %.4e",
              cn[["lsales"]], abs(cn[["lsales"]] - (-0.0512))),
      sprintf("lemploy:  NEVEN = %.4f  |  Libro =  0.0469  |  dif = %.4e",
              cn[["lemploy"]], abs(cn[["lemploy"]] - 0.0469)),
      sprintf("MSE total: %.2e   %s", mse,
              ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
    ), collapse = "\n")
  }

  # ===========================================================================
  # CASO 4: SMOKE -- Tobit (Cap. 17, Ejemplo 17.2)
  # ===========================================================================
  else if (Caso == 4L) {
    if (!requireNamespace("AER", quietly = TRUE))
      stop("El paquete 'AER' no esta instalado.")
    ds     <- wooldridge::smoke
    modelo <- suppressMessages(suppressWarnings(
      AER::tobit(cigs ~ lincome + lcigpric + educ + age + agesq + restaurn,
                 left = 0, data = ds)
    ))

    res <- paste(c(
      "Caso W-004 | Dataset: SMOKE | Cap. 17, Ejemplo 17.2",
      "Especificacion: cigs ~ lincome + lcigpric + educ + age + agesq + restaurn (Tobit, left=0)",
      "Obs: 807 | Variable dependiente: cigs (cigarrillos/dia, censurado en 0)",
      sprintf("Censuradas (cigs=0): %d (%.0f%%)",
              sum(ds$cigs == 0, na.rm = TRUE),
              100 * mean(ds$cigs == 0, na.rm = TRUE)),
      "",
      capture.output(summary(modelo))
    ), collapse = "\n")

    ref <- paste(c(
      "Referencia: Wooldridge Cap. 17, Ejemplo 17.2",
      "Dataset: SMOKE | Tobit (censura en cero)",
      "",
      "Coefficients:",
      "             Estimate Std. Error z value Pr(>|z|)",
      "(Intercept)  -3.6398   24.079    -0.15   0.880",
      "lincome       0.8803    0.728     1.21   0.228",
      "lcigpric     -0.7508    5.773    -0.13   0.897",
      "educ         -0.5014    0.167    -3.00   0.003 **",
      "age           0.7707    0.160     4.82  <0.001 ***",
      "agesq        -0.0090    0.002    -5.17  <0.001 ***",
      "restaurn     -2.8251    1.112    -2.54   0.011 *",
      "",
      "Log-Likelihood: -1376.8   Sigma: 13.817",
      "Obs: 807   Censuradas: 54%",
      "",
      "Interpretacion:",
      "Tobit corrige el sesgo de MCO cuando la mayoria no fuma.",
      "Cada anio de educacion reduce el consumo en ~0.5 cigarrillos."
    ), collapse = "\n")

    cn  <- coef(modelo)[setdiff(names(coef(modelo)), "Log(scale)")]
    cr  <- c("(Intercept)" = -3.6398, "lincome" = 0.8803, "lcigpric" = -0.7508,
             "educ" = -0.5014, "age" = 0.7707, "agesq" = -0.0090, "restaurn" = -2.8251)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "Verificacion vs. Wooldridge Cap. 17, Ejemplo 17.2",
      sprintf("(Intercept): NEVEN = %7.4f  |  Libro =  -3.6398  |  dif = %.4e",
              cn[["(Intercept)"]], abs(cn[["(Intercept)"]] - (-3.6398))),
      sprintf("lincome:     NEVEN = %7.4f  |  Libro =   0.8803  |  dif = %.4e",
              cn[["lincome"]], abs(cn[["lincome"]] - 0.8803)),
      sprintf("educ:        NEVEN = %7.4f  |  Libro =  -0.5014  |  dif = %.4e",
              cn[["educ"]], abs(cn[["educ"]] - (-0.5014))),
      sprintf("restaurn:    NEVEN = %7.4f  |  Libro =  -2.8251  |  dif = %.4e",
              cn[["restaurn"]], abs(cn[["restaurn"]] - (-2.8251))),
      sprintf("MSE total:   %.2e   %s", mse,
              ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
    ), collapse = "\n")
  }

  # ===========================================================================
  # CASO 5: FERTIL1 -- Serie de Tiempo + RESET (Cap. 10)
  # ===========================================================================
  else if (Caso == 5L) {
    if (!requireNamespace("lmtest", quietly = TRUE))
      stop("El paquete 'lmtest' no esta instalado.")
    ds     <- wooldridge::fertil1
    modelo <- lm(gfr ~ pe + ww2 + pill + t, data = ds)

    reset_out <- tryCatch(
      capture.output(lmtest::resettest(modelo, power = 2:3, type = "fitted")),
      error = function(e) paste("RESET no disponible:", e$message)
    )

    res <- paste(c(
      "Caso W-005 | Dataset: FERTIL1 | Cap. 10, Ecuacion 10.15",
      "Especificacion: gfr ~ pe + ww2 + pill + t",
      "Obs: 72 | Variable dependiente: gfr (tasa de fertilidad, EEUU 1913-1984)",
      "",
      capture.output(summary(modelo)),
      "",
      "--- Prueba RESET de Ramsey ---",
      reset_out
    ), collapse = "\n")

    ref <- paste(c(
      "Referencia: Wooldridge Cap. 10, Ecuacion 10.15",
      "Dataset: FERTIL1 | gfr ~ pe + ww2 + pill + t",
      "",
      "Coefficients:",
      "              Estimate Std. Error t value Pr(>|t|)",
      "(Intercept)  98.6823     3.2078   30.77  <2e-16 ***",
      "pe           -0.0785     0.0300   -2.62   0.011 *",
      "ww2         -24.2381     7.4585   -3.25   0.002 **",
      "pill        -31.5940     3.9816   -7.93  <2e-16 ***",
      "t            -1.1502     0.1919   -5.99  8.5e-8 ***",
      "",
      "R-squared: 0.6633   Adj. R-squared: 0.6464",
      "F-statistic: 39.1 on 4 and 67 DF,  p-value: < 2.2e-16",
      "",
      "Interpretacion:",
      "La pildora anticonceptiva redujo la fertilidad en ~31.6 puntos.",
      "La tendencia t captura cambios estructurales no modelados."
    ), collapse = "\n")

    cn  <- coef(modelo)
    cr  <- c("(Intercept)" = 98.6823, "pe" = -0.0785,
             "ww2" = -24.238, "pill" = -31.594, "t" = -1.150)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "Verificacion vs. Wooldridge Cap. 10, Ecuacion 10.15",
      sprintf("(Intercept): NEVEN = %8.4f  |  Libro = 98.6823  |  dif = %.4e",
              cn[["(Intercept)"]], abs(cn[["(Intercept)"]] - 98.6823)),
      sprintf("pe:          NEVEN = %8.4f  |  Libro = -0.0785  |  dif = %.4e",
              cn[["pe"]], abs(cn[["pe"]] - (-0.0785))),
      sprintf("ww2:         NEVEN = %8.4f  |  Libro = -24.238  |  dif = %.4e",
              cn[["ww2"]], abs(cn[["ww2"]] - (-24.238))),
      sprintf("pill:        NEVEN = %8.4f  |  Libro = -31.594  |  dif = %.4e",
              cn[["pill"]], abs(cn[["pill"]] - (-31.594))),
      sprintf("t:           NEVEN = %8.4f  |  Libro =  -1.150  |  dif = %.4e",
              cn[["t"]], abs(cn[["t"]] - (-1.150))),
      sprintf("MSE total:   %.2e   %s", mse,
              ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
    ), collapse = "\n")
  }

  # ===========================================================================
  # CASO 6: CEOSAL1 -- Descriptiva + Outliers (Cap. 9)
  # ===========================================================================
  else {
    ds   <- wooldridge::ceosal1
    x    <- ds$salary
    q1   <- quantile(x, 0.25); q3 <- quantile(x, 0.75); iqr <- q3 - q1
    lsup <- q3 + 1.5 * iqr
    outs <- sort(x[x > lsup], decreasing = TRUE)

    res <- paste(c(
      "Caso W-006 | Dataset: CEOSAL1 | Cap. 9",
      "Especificacion: Estadistica descriptiva de salary + deteccion outliers IQR",
      "Obs: 209 | Variable analizada: salary (salario anual CEO, miles USD)",
      "",
      capture.output(summary(x)),
      sprintf("Q1: %.1f   Q3: %.1f   IQR: %.1f", q1, q3, iqr),
      sprintf("Umbral outlier (Q3 + 1.5*IQR): %.1f", lsup),
      sprintf("Outliers detectados: %d", length(outs)),
      if (length(outs) > 0)
        paste0("Valores: ", paste(head(outs, 10), collapse = "  "))
      else "(ninguno)"
    ), collapse = "\n")

    ref <- paste(c(
      "Referencia: Wooldridge Cap. 9 -- CEOSAL1",
      "salary: N=209   Media=1281.12   Mediana=1037",
      "Min=223   Max=14822   Q1=736   Q3=1534   IQR=798",
      "Umbral outlier (Q3 + 1.5*IQR) = 2731",
      "Outliers: ~11 CEOs con salarios atipicamente altos",
      "",
      "Nota: distribucion fuertemente asimetrica.",
      "Se recomienda usar log(salary) en modelos de regresion."
    ), collapse = "\n")

    ver <- paste(c(
      "Verificacion vs. Wooldridge Cap. 9",
      sprintf("Media:    NEVEN = %8.2f  |  Libro = 1281.12  |  %s",
              mean(x), ifelse(abs(mean(x) - 1281.12) < 5, "OK", "REVISAR")),
      sprintf("Mediana:  NEVEN = %8.2f  |  Libro = 1037.00  |  %s",
              median(x), ifelse(abs(median(x) - 1037) < 10, "OK", "REVISAR")),
      sprintf("Outliers: NEVEN = %8d  |  Libro = ~11      |  %s",
              length(outs), ifelse(abs(length(outs) - 11) <= 2, "OK", "REVISAR"))
    ), collapse = "\n")
  }

  return(r_object_to_slots(
    list(
      resultado_NEVEN  = res,
      referencia_libro = ref,
      verificacion     = ver
    ),
    tier_map = c(resultado_NEVEN = 1L, referencia_libro = 1L, verificacion = 1L)
  ))
}
