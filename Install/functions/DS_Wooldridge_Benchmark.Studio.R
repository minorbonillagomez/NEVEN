# ===============================================================================
# NEVEN Data Lab -- WOOLDRIDGE BENCHMARK SUITE (DS Family)
# Jeffrey Wooldridge, Introductory Econometrics (6a ed.)
# Salida: texto plano simple (scalar) renderizado en <pre> por datalab.js
# ===============================================================================

DS_Wooldridge_Benchmark.Studio <- function(Caso = 1L) {

  Caso <- as.integer(Caso)
  if (is.na(Caso) || Caso < 1L || Caso > 6L)
    stop("'Caso' debe ser un entero de 1 a 6.")

  if (!requireNamespace("wooldridge", quietly = TRUE))
    stop("El paquete 'wooldridge' no esta instalado.")

  sep <- paste(rep("-", 60), collapse = "")

  # ===========================================================================
  # CASO 1: WAGE1 -- MCO Multiple (Cap. 3, Ejemplo 3.2)
  # ===========================================================================
  if (Caso == 1L) {
    ds     <- wooldridge::wage1
    modelo <- lm(wage ~ educ + exper + tenure, data = ds)
    sm     <- summary(modelo)

    res <- paste(c(
      "NEVEN | W-001 | WAGE1 | Cap. 3, Ejemplo 3.2",
      "Especificacion: wage ~ educ + exper + tenure",
      sep,
      capture.output(print(sm))
    ), collapse = "\n")

    ref <- paste(c(
      "REFERENCIA | W-001 | WAGE1 | Cap. 3, Ejemplo 3.2",
      "Especificacion: wage ~ educ + exper + tenure",
      sep,
      "Coefficients:",
      "             Estimate Std. Error t value Pr(>|t|)",
      "(Intercept)  -2.8727     0.7289  -3.940  <0.001 ***",
      "educ          0.5990     0.0512  11.698  <0.001 ***",
      "exper         0.0223     0.0120   1.858   0.063  .",
      "tenure        0.1693     0.0222   7.630  <0.001 ***",
      sep,
      "R-squared: 0.3061   Adj. R-squared: 0.3006",
      "F-statistic: 55.25 on 3 and 522 DF,  p-value: < 2.2e-16",
      sep,
      "Interpretacion:",
      "+1 anio educacion = +$0.60/hora (ceteris paribus)"
    ), collapse = "\n")

    cn  <- coef(modelo)
    cr  <- c("(Intercept)"=-2.8727, educ=0.5990, exper=0.0223, tenure=0.1693)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "VERIFICACION | W-001 | Cap. 3, Ejemplo 3.2",
      sep,
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "(Intercept)", cn["(Intercept)"], -2.8727, abs(cn["(Intercept)"] - (-2.8727)),
              ifelse(abs(cn["(Intercept)"] - (-2.8727)) < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "educ",   cn["educ"],   0.5990, abs(cn["educ"]   - 0.5990),  ifelse(abs(cn["educ"]   - 0.5990)  < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "exper",  cn["exper"],  0.0223, abs(cn["exper"]  - 0.0223),  ifelse(abs(cn["exper"]  - 0.0223)  < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "tenure", cn["tenure"], 0.1693, abs(cn["tenure"] - 0.1693),  ifelse(abs(cn["tenure"] - 0.1693)  < 0.01, "OK", "REVISAR")),
      sep,
      sprintf("MSE total: %.2e   %s", mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
    ), collapse = "\n")
  } 401K -- LPM (Cap. 7, Ejemplo 7.12)
  # ===========================================================================
  else if (Caso == 2L) {
    ds     <- wooldridge::k401k
    modelo <- lm(prate ~ mrate + age + totemp, data = ds)
    sm     <- summary(modelo)

    res <- paste(c(
      "NEVEN | W-002 | 401K | Cap. 7, Ejemplo 7.12",
      "Especificacion: prate ~ mrate + age + totemp",
      sep,
      capture.output(print(sm))
    ), collapse = "\n")

    ref <- paste(c(
      "REFERENCIA | W-002 | 401K | Cap. 7, Ejemplo 7.12",
      "Especificacion: prate ~ mrate + age + totemp",
      sep,
      "Coefficients:",
      "              Estimate  Std. Error  t value  Pr(>|t|)",
      "(Intercept)  83.0755      0.8777    94.65   <0.001 ***",
      "mrate         5.8611      0.5269    11.12   <0.001 ***",
      "age           0.2690      0.0455     5.91   <0.001 ***",
      "totemp       -0.0000884   0.0000117  -7.56   <0.001 ***",
      sep,
      "R-squared: 0.1002",
      "F-statistic: 66.38 on 3 and 1800 DF",
      sep,
      "Interpretacion:",
      "+1 en mrate (matching) = +5.86 pp en participacion"
    ), collapse = "\n")

    cn  <- coef(modelo)
    cr  <- c("(Intercept)"=83.0755, mrate=5.8611, age=0.2690, totemp=-8.84e-05)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "VERIFICACION | W-002 | Cap. 7, Ejemplo 7.12",
      sep,
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "(Intercept)", cn["(Intercept)"], 83.0755, abs(cn["(Intercept)"] - 83.0755),
              ifelse(abs(cn["(Intercept)"] - 83.0755) < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "mrate",  cn["mrate"],  5.8611,   abs(cn["mrate"]  - 5.8611),   ifelse(abs(cn["mrate"]  - 5.8611)   < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "age",    cn["age"],    0.2690,   abs(cn["age"]    - 0.2690),   ifelse(abs(cn["age"]    - 0.2690)   < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%.7f  Libro=%.7f  dif=%.2e  %s",
              "totemp", cn["totemp"], -8.84e-05, abs(cn["totemp"] - (-8.84e-05)), ifelse(abs(cn["totemp"] - (-8.84e-05)) < 1e-6, "OK", "REVISAR")),
      sep,
      sprintf("MSE total: %.2e   %s", mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
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
      "NEVEN | W-003 | JTRAIN | Cap. 14, Ejemplo 14.1",
      "Especificacion: lscrap ~ hrsemp + lsales + lemploy | fcode (Efectos Fijos)",
      sep,
      capture.output(print(summary(modelo)))
    ), collapse = "\n")

    ref <- paste(c(
      "REFERENCIA | W-003 | JTRAIN | Cap. 14, Ejemplo 14.1",
      "Especificacion: lscrap ~ hrsemp + lsales + lemploy | fcode",
      "Modelo: Efectos Fijos (within estimator)",
      sep,
      "Coefficients:",
      "         Estimate Std. Error t-stat  Pr(>|t|)",
      "hrsemp   -0.0401    0.0210   -1.91    0.059  .",
      "lsales   -0.0512    0.2045   -0.25    0.803",
      "lemploy   0.0469    0.3587    0.13    0.896",
      sep,
      "Obs: 135 (45 firmas x 3 anios, panel no balanceado)",
      sep,
      "Interpretacion:",
      "+10% entrenamiento = -0.4% desperdicio (efecto causal entre firmas)"
    ), collapse = "\n")

    cn  <- coef(modelo)
    cr  <- c(hrsemp=-0.0401, lsales=-0.0512, lemploy=0.0469)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "VERIFICACION | W-003 | Cap. 14, Ejemplo 14.1",
      sep,
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "hrsemp",  cn["hrsemp"],  -0.0401, abs(cn["hrsemp"]  - (-0.0401)), ifelse(abs(cn["hrsemp"]  - (-0.0401)) < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "lsales",  cn["lsales"],  -0.0512, abs(cn["lsales"]  - (-0.0512)), ifelse(abs(cn["lsales"]  - (-0.0512)) < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "lemploy", cn["lemploy"],  0.0469, abs(cn["lemploy"] -   0.0469),  ifelse(abs(cn["lemploy"] -   0.0469)  < 0.01, "OK", "REVISAR")),
      sep,
      sprintf("MSE total: %.2e   %s", mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
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
      "NEVEN | W-004 | SMOKE | Cap. 17, Ejemplo 17.2",
      "Especificacion: cigs ~ lincome + lcigpric + educ + age + agesq + restaurn (Tobit, left=0)",
      sprintf("Censuradas (cigs=0): %d de %d (%.0f%%)",
              sum(ds$cigs==0, na.rm=TRUE), nrow(ds),
              100*mean(ds$cigs==0, na.rm=TRUE)),
      sep,
      capture.output(print(summary(modelo)))
    ), collapse = "\n")

    ref <- paste(c(
      "REFERENCIA | W-004 | SMOKE | Cap. 17, Ejemplo 17.2",
      "Especificacion: Tobit (left=0)",
      sep,
      "Coefficients:",
      "             Estimate Std. Error z value  Pr(>|z|)",
      "(Intercept)  -3.6398   24.079    -0.15    0.880",
      "lincome       0.8803    0.728     1.21    0.228",
      "lcigpric     -0.7508    5.773    -0.13    0.897",
      "educ         -0.5014    0.167    -3.00    0.003  **",
      "age           0.7707    0.160     4.82   <0.001 ***",
      "agesq        -0.0090    0.002    -5.17   <0.001 ***",
      "restaurn     -2.8251    1.112    -2.54    0.011  *",
      sep,
      "Log-Likelihood: -1376.8   Sigma: 13.817",
      "Obs: 807   Censuradas: 54%",
      sep,
      "Interpretacion:",
      "Tobit corrige el sesgo de MCO cuando la mayoria no fuma (y=0)"
    ), collapse = "\n")

    cn  <- coef(modelo)[setdiff(names(coef(modelo)), "Log(scale)")]
    cr  <- c("(Intercept)"=-3.6398, lincome=0.8803, lcigpric=-0.7508,
             educ=-0.5014, age=0.7707, agesq=-0.0090, restaurn=-2.8251)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "VERIFICACION | W-004 | Cap. 17, Ejemplo 17.2",
      sep,
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "(Intercept)", cn["(Intercept)"], -3.6398, abs(cn["(Intercept)"] - (-3.6398)), ifelse(abs(cn["(Intercept)"] - (-3.6398)) < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "educ",     cn["educ"],     -0.5014, abs(cn["educ"]     - (-0.5014)), ifelse(abs(cn["educ"]     - (-0.5014)) < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "restaurn", cn["restaurn"], -2.8251, abs(cn["restaurn"] - (-2.8251)), ifelse(abs(cn["restaurn"] - (-2.8251)) < 0.01, "OK", "REVISAR")),
      sep,
      sprintf("MSE total: %.2e   %s", mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
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
    sm     <- summary(modelo)

    reset_out <- tryCatch(
      capture.output(lmtest::resettest(modelo, power = 2:3, type = "fitted")),
      error = function(e) "RESET no disponible"
    )

    res <- paste(c(
      "NEVEN | W-005 | FERTIL1 | Cap. 10, Ec. 10.15",
      "Especificacion: gfr ~ pe + ww2 + pill + t",
      sep,
      capture.output(print(sm)),
      sep,
      "Prueba RESET de Ramsey:",
      reset_out
    ), collapse = "\n")

    ref <- paste(c(
      "REFERENCIA | W-005 | FERTIL1 | Cap. 10, Ec. 10.15",
      "Especificacion: gfr ~ pe + ww2 + pill + t",
      sep,
      "Coefficients:",
      "              Estimate Std. Error  t value  Pr(>|t|)",
      "(Intercept)  98.6823     3.2078    30.77   <0.001 ***",
      "pe           -0.0785     0.0300    -2.62    0.011  *",
      "ww2         -24.2381     7.4585    -3.25    0.002  **",
      "pill        -31.5940     3.9816    -7.93   <0.001 ***",
      "t            -1.1502     0.1919    -5.99   <0.001 ***",
      sep,
      "R-squared: 0.6633   Adj. R-squared: 0.6464",
      "F-statistic: 39.1 on 4 and 67 DF",
      sep,
      "Interpretacion:",
      "La pildora redujo la fertilidad en ~31.6 puntos"
    ), collapse = "\n")

    cn  <- coef(modelo)
    cr  <- c("(Intercept)"=98.6823, pe=-0.0785, ww2=-24.238, pill=-31.594, t=-1.150)
    mse <- mean((cn[names(cr)] - cr)^2)
    ver <- paste(c(
      "VERIFICACION | W-005 | Cap. 10, Ec. 10.15",
      sep,
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "(Intercept)", cn["(Intercept)"], 98.6823, abs(cn["(Intercept)"] - 98.6823), ifelse(abs(cn["(Intercept)"] - 98.6823) < 0.1, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "pe",   cn["pe"],   -0.0785, abs(cn["pe"]   - (-0.0785)), ifelse(abs(cn["pe"]   - (-0.0785)) < 0.01, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "ww2",  cn["ww2"],  -24.238, abs(cn["ww2"]  - (-24.238)), ifelse(abs(cn["ww2"]  - (-24.238)) < 0.1,  "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "pill", cn["pill"], -31.594, abs(cn["pill"] - (-31.594)), ifelse(abs(cn["pill"] - (-31.594)) < 0.1,  "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%9.4f  Libro=%9.4f  dif=%.2e  %s",
              "t",    cn["t"],    -1.150,  abs(cn["t"]    - (-1.150)),  ifelse(abs(cn["t"]    - (-1.150))  < 0.01, "OK", "REVISAR")),
      sep,
      sprintf("MSE total: %.2e   %s", mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR"))
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
      "NEVEN | W-006 | CEOSAL1 | Cap. 9",
      "Especificacion: Estadistica descriptiva de salary + outliers IQR",
      sep,
      capture.output(summary(x)),
      sprintf("Q1=%.1f  Q3=%.1f  IQR=%.1f", q1, q3, iqr),
      sprintf("Umbral outlier (Q3+1.5*IQR) = %.1f", lsup),
      sprintf("Outliers detectados: %d", length(outs)),
      if (length(outs)) paste("Valores:", paste(head(outs, 10), collapse=" ")) else "(ninguno)"
    ), collapse = "\n")

    ref <- paste(c(
      "REFERENCIA | W-006 | CEOSAL1 | Cap. 9",
      "Especificacion: Estadistica descriptiva de salary",
      sep,
      "   Min.  1st Qu.   Median     Mean  3rd Qu.     Max.",
      "  223.0    736.0   1037.0   1281.1   1534.0  14822.0",
      sprintf("Q1=736  Q3=1534  IQR=798"),
      "Umbral outlier = 2731",
      "Outliers: ~11 CEOs",
      sep,
      "Interpretacion:",
      "Distribucion asimetrica. Usar log(salary) en modelos."
    ), collapse = "\n")

    ver <- paste(c(
      "VERIFICACION | W-006 | Cap. 9",
      sep,
      sprintf("%-14s  NEVEN=%8.2f  Libro=1281.12  %s",
              "Media:",   mean(x), ifelse(abs(mean(x)   - 1281.12) < 5,  "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%8.2f  Libro=1037.00  %s",
              "Mediana:", median(x), ifelse(abs(median(x) - 1037.00) < 10, "OK", "REVISAR")),
      sprintf("%-14s  NEVEN=%8d  Libro=~11      %s",
              "Outliers:", length(outs), ifelse(abs(length(outs) - 11) <= 2, "OK", "REVISAR")),
      sep,
      "Nota: pequenas diferencias por version del dataset."
    ), collapse = "\n")
  }

  # ── Exportar dataset de Wooldridge como slot table (tier 2) ─────────────────
  # El usuario puede hacer clic en "Cargar en Data Studio" para cargarlo en DuckDB
  # y luego usar las funciones de regresion con esas columnas.
  ds_export <- tryCatch(
    as.data.frame(ds),
    error = function(e) data.frame()
  )

  return(r_object_to_slots(
    list(
      resultado_NEVEN  = res,
      referencia_libro = ref,
      verificacion     = ver,
      dataset_wooldridge = ds_export
    ),
    tier_map = c(resultado_NEVEN = 1L, referencia_libro = 1L,
                 verificacion = 1L, dataset_wooldridge = 2L)
  ))
}
