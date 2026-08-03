# ===============================================================================
# NEVEN Data Lab -- WOOLDRIDGE BENCHMARK SUITE (DS Family)
# Jeffrey Wooldridge, Introductory Econometrics (6a ed.)
#
# Formato uniforme en los 3 slots: sprintf linea a linea (igual que verificacion)
# Si data_Y y data_X se asignan, el usuario puede modificar la especificacion.
# Si no se asignan, se usa la especificacion canonica del libro.
# ===============================================================================

DS_Wooldridge_Benchmark.Studio <- function(Caso = 1L) {

  Caso <- as.integer(Caso)
  if (is.na(Caso) || Caso < 1L || Caso > 6L)
    stop("'Caso' debe ser un entero de 1 a 6.")

  if (!requireNamespace("wooldridge", quietly = TRUE))
    stop("El paquete 'wooldridge' no esta instalado.")

  # ── Sin variable_roles -- el wrapper no recibe data_Y ni data_X ───────────

  # ── Formato coeficientes con TAB como separador de columnas ─────────────────
  # Tab garantiza alineacion correcta independientemente de la fuente.
  # gsub("[[:cntrl:]]") en la salida de R excluye \t para preservarlos.
  .fmt_ct <- function(ct) {
    vapply(seq_len(nrow(ct)), function(i) {
      sig <- ifelse(ct[i,4] < 0.001, "***",
             ifelse(ct[i,4] < 0.01,  "** ",
             ifelse(ct[i,4] < 0.05,  "*  ",
             ifelse(ct[i,4] < 0.10,  ".  ", "   "))))
      paste(rownames(ct)[i],
            sprintf("%9.4f", ct[i,1]),
            sprintf("%9.4f", ct[i,2]),
            sprintf("%7.3f",  ct[i,3]),
            sprintf("%9.4f", ct[i,4]),
            sig,
            sep = "\t")
    }, character(1))
  }

  # ── Encabezado de tabla con tabs ──────────────────────────────────────────
  .hdr <- function() c(
    paste("Variable", "Estimate", "Std.Err", "t/z", "p-value", "Sig", sep = "\t"),
    paste(rep("-", 66), collapse = "")
  )

  # ── Referencia del libro con tabs ─────────────────────────────────────────
  .ref_rows <- function(rows) {
    vapply(rows, function(r) {
      paste(r[1], r[2], r[3], r[4], r[5], sep = "\t")
    }, character(1))
  }

  # ── Comparacion coeficientes con tabs ────────────────────────────────────
  .ver <- function(cn, cr, fuente) {
    nms <- intersect(names(cn), names(cr))
    filas <- vapply(nms, function(nm) {
      dif <- abs(cn[[nm]] - cr[[nm]])
      paste(nm,
            sprintf("%.4f", cn[[nm]]),
            sprintf("%.4f", cr[[nm]]),
            sprintf("%.2e", dif),
            ifelse(dif < 0.01, "OK", "REVISAR"),
            sep = "\t")
    }, character(1))
    mse <- mean((cn[nms] - cr[nms])^2)
    c(paste0("Verificacion vs. ", fuente), "",
      paste("Variable", "NEVEN", "Libro", "Diferencia", "Estado", sep = "\t"),
      paste(rep("-", 66), collapse = ""),
      filas, "",
      sprintf("MSE total:\t%.2e\t%s",
              mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR")))
  }

  sep <- paste(rep("-", 66), collapse = "")

  # ===========================================================================
  # CASO 1: WAGE1 (Cap. 3)
  # ===========================================================================
  if (Caso == 1L) {
    ds <- wooldridge::wage1
    df <- ds; fml <- wage ~ educ + exper + tenure
    modo <- "Especificacion canonica: wage ~ educ + exper + tenure"
    modelo <- lm(fml, data = df)
    sm <- summary(modelo); ct <- sm$coefficients
    fstat <- sm$fstatistic
    pf_v  <- pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)

    res <- paste(c(
      "Resultado NEVEN | W-001 | WAGE1 | Cap. 3, Ejemplo 3.2",
      modo,
      sprintf("  Obs: %d  |  Var. dep.: %s", nrow(df), as.character(fml[[2]])),
      sep, .hdr(), .fmt_ct(ct), sep,
      "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1",
      sprintf("  R-sq: %.4f   Adj R-sq: %.4f", sm$r.squared, sm$adj.r.squared),
      sprintf("  F-stat: %.2f on %d and %d DF,  p-value: %.4e",
              fstat[1], fstat[2], fstat[3], pf_v),
      sep
    ), collapse = "\n")

    ref_ct <- rbind(
      c("(Intercept)", "-2.8727", "0.7289", "-3.940", "<0.001 ***"),
      c("educ",        " 0.5990", "0.0512", "11.698", "<0.001 ***"),
      c("exper",       " 0.0223", "0.0120", " 1.858", " 0.063  . "),
      c("tenure",      " 0.1693", "0.0222", " 7.630", "<0.001 ***")
    )
    ref <- paste(c(
      "Referencia libro | W-001 | WAGE1 | Cap. 3, Ejemplo 3.2",
      "Especificacion: wage ~ educ + exper + tenure",
      sprintf("  Obs: 526  |  Var. dep.: wage (salario/hora USD)"),
      sep, .hdr(), .ref_rows(ref_ct), sep,
      "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1",
      "  R-sq: 0.3061   Adj R-sq: 0.3006",
      "  F-stat: 55.25 on 3 and 522 DF,  p-value: <2.2e-16",
      "  Nota: +1 anio educ = +$0.60/hora ceteris paribus",
      sep
    ), collapse = "\n")

    ver <- paste(.ver(coef(modelo),
                     c("(Intercept)"=-2.8727,"educ"=0.5990,
                       "exper"=0.0223,"tenure"=0.1693),
                     "Wooldridge Cap. 3, Ej. 3.2"),
                 collapse = "\n")
  }

  # ===========================================================================
  # CASO 2: 401K (Cap. 7)
  # ===========================================================================
  else if (Caso == 2L) {
    ds <- wooldridge::k401k
    df <- ds; fml <- prate ~ mrate + age + totemp
    modo <- "Especificacion canonica: prate ~ mrate + age + totemp"
    modelo <- lm(fml, data = df)
    sm <- summary(modelo); ct <- sm$coefficients
    fstat <- sm$fstatistic
    pf_v  <- pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)

    res <- paste(c(
      "Resultado NEVEN | W-002 | 401K | Cap. 7, Ejemplo 7.12",
      modo,
      sprintf("  Obs: %d  |  Var. dep.: %s", nrow(df), as.character(fml[[2]])),
      sep, .hdr(), .fmt_ct(ct), sep,
      "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1",
      sprintf("  R-sq: %.4f", sm$r.squared),
      sprintf("  F-stat: %.2f on %d and %d DF,  p-value: %.4e",
              fstat[1], fstat[2], fstat[3], pf_v), sep
    ), collapse = "\n")

    ref_ct <- rbind(
      c("(Intercept)", "83.0755",    "0.8777",   " 94.65", "<0.001 ***"),
      c("mrate",       " 5.8611",    "0.5269",   " 11.12", "<0.001 ***"),
      c("age",         " 0.2690",    "0.0455",   "  5.91", "<0.001 ***"),
      c("totemp",      "-0.0000884", "0.0000117","  -7.56", "<0.001 ***")
    )
    ref <- paste(c(
      "Referencia libro | W-002 | 401K | Cap. 7, Ejemplo 7.12",
      "Especificacion: prate ~ mrate + age + totemp",
      "  Obs: 1804  |  Var. dep.: prate (% participacion pension)",
      sep, .hdr(), .ref_rows(ref_ct), sep,
      "  R-sq: 0.1002   F-stat: 66.38 on 3 and 1800 DF",
      "  Nota: +1 en mrate = +5.86 pp en participacion", sep
    ), collapse = "\n")

    ver <- paste(.ver(coef(modelo),
                     c("(Intercept)"=83.0755,"mrate"=5.8611,
                       "age"=0.2690,"totemp"=-8.84e-05),
                     "Wooldridge Cap. 7, Ej. 7.12"),
                 collapse = "\n")
  }

  # ===========================================================================
  # CASO 3: JTRAIN (Cap. 14)
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
    ct <- summary(modelo)$coefficients
    modo <- "Especificacion canonica: lscrap ~ hrsemp + lsales + lemploy | fcode"

    res <- paste(c(
      "Resultado NEVEN | W-003 | JTRAIN | Cap. 14, Ejemplo 14.1",
      modo,
      "  Modelo: Efectos Fijos (within)  |  Var. dep.: lscrap (log desperdicio)",
      sep, .hdr(), .fmt_ct(ct), sep,
      "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1",
      sprintf("  Obs: %d  (45 firmas x 3 anios)", nrow(pdata)), sep
    ), collapse = "\n")

    ref_ct <- rbind(
      c("hrsemp",  "-0.0401", "0.0210", "-1.91", " 0.059  . "),
      c("lsales",  "-0.0512", "0.2045", "-0.25", " 0.803    "),
      c("lemploy", " 0.0469", "0.3587", " 0.13", " 0.896    ")
    )
    ref <- paste(c(
      "Referencia libro | W-003 | JTRAIN | Cap. 14, Ejemplo 14.1",
      "Especificacion: lscrap ~ hrsemp + lsales + lemploy | fcode",
      "  Modelo: Efectos Fijos  |  Obs: 135 (45 firmas x 3 anios)",
      sep, .hdr(), .ref_rows(ref_ct), sep,
      "  Nota: +10% entrenamiento = -0.4% desperdicio (efecto causal)", sep
    ), collapse = "\n")

    ver <- paste(.ver(coef(modelo),
                     c("hrsemp"=-0.0401,"lsales"=-0.0512,"lemploy"=0.0469),
                     "Wooldridge Cap. 14, Ej. 14.1"),
                 collapse = "\n")
  }

  # ===========================================================================
  # CASO 4: SMOKE (Cap. 17)
  # ===========================================================================
  else if (Caso == 4L) {
    if (!requireNamespace("AER", quietly = TRUE))
      stop("El paquete 'AER' no esta instalado.")
    ds     <- wooldridge::smoke
    modelo <- suppressMessages(suppressWarnings(
      AER::tobit(cigs ~ lincome + lcigpric + educ + age + agesq + restaurn,
                 left = 0, data = ds)
    ))
    ct  <- summary(modelo)$coefficients
    ct2 <- ct[rownames(ct) != "Log(scale)", ]
    ll  <- tryCatch(round(logLik(modelo)[[1]], 1), error = function(e) "N/A")
    sig_v <- tryCatch(round(exp(coef(modelo)["Log(scale)"]), 3), error=function(e) "N/A")
    modo <- "Especificacion canonica: cigs ~ lincome+lcigpric+educ+age+agesq+restaurn (Tobit, left=0)"
    res <- paste(c(
      "Resultado NEVEN | W-004 | SMOKE | Cap. 17, Ejemplo 17.2",
      modo,
      sprintf("  Obs: %d  |  Censuradas (cigs=0): %.0f%%  |  Var. dep.: cigs",
              nrow(ds), 100*mean(ds$cigs==0, na.rm=TRUE)),
      sep, .hdr(), .fmt_ct(ct2), sep,
      "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1",
      sprintf("  Log-Likelihood: %s   Sigma: %s", ll, sig_v), sep
    ), collapse = "\n")

    ref_ct <- rbind(
      c("(Intercept)", " -3.6398", "24.079", "-0.15", " 0.880    "),
      c("lincome",     "  0.8803", " 0.728", " 1.21", " 0.228    "),
      c("lcigpric",    " -0.7508", " 5.773", "-0.13", " 0.897    "),
      c("educ",        " -0.5014", " 0.167", "-3.00", " 0.003 ** "),
      c("age",         "  0.7707", " 0.160", " 4.82", "<0.001 ***"),
      c("agesq",       " -0.0090", " 0.002", "-5.17", "<0.001 ***"),
      c("restaurn",    " -2.8251", " 1.112", "-2.54", " 0.011 *  ")
    )
    ref <- paste(c(
      "Referencia libro | W-004 | SMOKE | Cap. 17, Ejemplo 17.2",
      "Especificacion: cigs ~ lincome+lcigpric+educ+age+agesq+restaurn (Tobit, left=0)",
      "  Obs: 807  |  Censuradas: 54%  |  Var. dep.: cigs",
      sep, .hdr(), .ref_rows(ref_ct), sep,
      "  Log-Likelihood: -1376.8   Sigma: 13.817",
      "  Nota: Tobit corrige el sesgo de MCO cuando la mayoria no fuma", sep
    ), collapse = "\n")

    ver <- paste(.ver(
      coef(modelo)[names(coef(modelo)) != "Log(scale)"],
      c("(Intercept)"=-3.6398,"lincome"=0.8803,"lcigpric"=-0.7508,
        "educ"=-0.5014,"age"=0.7707,"agesq"=-0.0090,"restaurn"=-2.8251),
      "Wooldridge Cap. 17, Ej. 17.2"), collapse = "\n")
  }

  # ===========================================================================
  # CASO 5: FERTIL1 (Cap. 10)
  # ===========================================================================
  else if (Caso == 5L) {
    if (!requireNamespace("lmtest", quietly = TRUE))
      stop("El paquete 'lmtest' no esta instalado.")
    ds <- wooldridge::fertil1
    df <- ds; fml <- gfr ~ pe + ww2 + pill + t
    modo <- "Especificacion canonica: gfr ~ pe + ww2 + pill + t"
    modelo <- lm(fml, data = df)
    sm    <- summary(modelo); ct <- sm$coefficients
    fstat <- sm$fstatistic
    pf_v  <- pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)
    reset_str <- tryCatch({
      r <- lmtest::resettest(modelo, power = 2:3, type = "fitted")
      sprintf("  RESET: F=%.3f, df=(%d,%d), p=%.4f  %s",
              r$statistic, r$parameter[1], r$parameter[2], r$p.value,
              ifelse(r$p.value < 0.05, "-> FORMA FUNCIONAL PROBLEMATICA",
                     "-> Forma funcional adecuada"))
    }, error = function(e) "  RESET: no disponible")

    res <- paste(c(
      "Resultado NEVEN | W-005 | FERTIL1 | Cap. 10, Ec. 10.15",
      modo,
      sprintf("  Obs: %d  |  Var. dep.: %s", nrow(df), as.character(fml[[2]])),
      sep, .hdr(), .fmt_ct(ct), sep,
      "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1",
      sprintf("  R-sq: %.4f   Adj R-sq: %.4f", sm$r.squared, sm$adj.r.squared),
      sprintf("  F-stat: %.2f on %d and %d DF,  p-value: %.4e",
              fstat[1], fstat[2], fstat[3], pf_v),
      reset_str, sep
    ), collapse = "\n")

    ref_ct <- rbind(
      c("(Intercept)", "98.6823", "3.2078", "30.77", "<0.001 ***"),
      c("pe",          "-0.0785", "0.0300", "-2.62", " 0.011 *  "),
      c("ww2",         "-24.238", "7.4585", "-3.25", " 0.002 ** "),
      c("pill",        "-31.594", "3.9816", "-7.93", "<0.001 ***"),
      c("t",           " -1.150", "0.1919", "-5.99", "<0.001 ***")
    )
    ref <- paste(c(
      "Referencia libro | W-005 | FERTIL1 | Cap. 10, Ec. 10.15",
      "Especificacion: gfr ~ pe + ww2 + pill + t",
      "  Obs: 72  |  Serie: EEUU 1913-1984  |  Var. dep.: gfr (tasa fertilidad)",
      sep, .hdr(), .ref_rows(ref_ct), sep,
      "  R-sq: 0.6633   Adj R-sq: 0.6464",
      "  Nota: la pildora redujo la fertilidad en ~31.6 puntos", sep
    ), collapse = "\n")

    ver <- paste(.ver(coef(modelo),
                     c("(Intercept)"=98.6823,"pe"=-0.0785,
                       "ww2"=-24.238,"pill"=-31.594,"t"=-1.150),
                     "Wooldridge Cap. 10, Ec. 10.15"),
                 collapse = "\n")
  }

  # ===========================================================================
  # CASO 6: CEOSAL1 (Cap. 9)
  # ===========================================================================
  else {
    ds   <- wooldridge::ceosal1
    x_v  <- ds$salary
    nm_v <- "salary"
    q1   <- quantile(x_v, 0.25); q3 <- quantile(x_v, 0.75); iqr <- q3 - q1
    lsup <- q3 + 1.5 * iqr
    outs <- sort(x_v[x_v > lsup], decreasing = TRUE)
    modo <- "Especificacion: estadistica descriptiva de salary"

    res <- paste(c(
      "Resultado NEVEN | W-006 | CEOSAL1 | Cap. 9",
      modo,
      sep,
      sprintf("  N:        %d", length(x_v)),
      sprintf("  Media:    %.2f", mean(x_v)),
      sprintf("  Mediana:  %.2f", median(x_v)),
      sprintf("  Min:      %.2f   Max: %.2f", min(x_v), max(x_v)),
      sprintf("  Q1:       %.2f", q1),
      sprintf("  Q3:       %.2f", q3),
      sprintf("  IQR:      %.2f", iqr),
      sep,
      sprintf("  Umbral outlier (Q3+1.5*IQR): %.2f", lsup),
      sprintf("  Outliers:  %d observaciones", length(outs)),
      if (length(outs)) sprintf("  Valores:   %s", paste(head(outs,8), collapse="  "))
      else "  (ninguno)", sep
    ), collapse = "\n")

    ref <- paste(c(
      "Referencia libro | W-006 | CEOSAL1 | Cap. 9",
      "Especificacion: estadistica descriptiva de salary (miles USD)",
      sep,
      "  N:        209",
      "  Media:    1281.12",
      "  Mediana:  1037.00",
      "  Min:       223.00   Max: 14822.00",
      "  Q1:        736.00",
      "  Q3:       1534.00",
      "  IQR:       798.00",
      sep,
      "  Umbral outlier (Q3+1.5*IQR): 2731.00",
      "  Outliers:  ~11 CEOs",
      "  Nota: distribucion asimetrica -- usar log(salary) en modelos", sep
    ), collapse = "\n")

    ver <- paste(c(
      "Verificacion vs. Wooldridge Cap. 9", "",
      paste("Estadistico", "NEVEN", "Libro", "Estado", sep = "\t"),
      paste(rep("-", 50), collapse = ""),
      paste("Media:",   sprintf("%.2f", mean(x_v)), "1281.12",
            ifelse(abs(mean(x_v)-1281.12)<5,"OK","REVISAR"), sep = "\t"),
      paste("Mediana:", sprintf("%.2f", median(x_v)), "1037.00",
            ifelse(abs(median(x_v)-1037)<10,"OK","REVISAR"), sep = "\t"),
      paste("Outliers:", length(outs), "~11",
            ifelse(abs(length(outs)-11)<=2,"OK","REVISAR"), sep = "\t")
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
