# ===============================================================================
# NEVEN Data Lab -- WOOLDRIDGE BENCHMARK SUITE (DS Family)
# Jeffrey Wooldridge, Introductory Econometrics (6a ed.)
# Formato: texto plano ASCII puro (sprintf/paste), sin Unicode especial
# ===============================================================================

DS_Wooldridge_Benchmark.Studio <- function(Caso = 1L) {

  Caso <- as.integer(Caso)
  if (is.na(Caso) || Caso < 1L || Caso > 6L)
    stop("'Caso' debe ser un entero de 1 a 6.")

  if (!requireNamespace("wooldridge", quietly = TRUE))
    stop("El paquete 'wooldridge' no esta instalado.")

  # ── Helper: tabla de coeficientes en ASCII puro ───────────────────────────────
  # Patron identico al de verificacion: sprintf con separadores de guiones simples.
  # Sin Unicode, sin caracteres especiales -- solo ASCII 32-126.
  .coef_table <- function(ct, titulo, extra_lines = character(0)) {
    sep  <- paste(rep("-", 72), collapse = "")
    hdr  <- sprintf("  %-18s  %10s  %10s  %8s  %10s",
                    "Variable", "Estimate", "Std.Err", "t/z", "p-value")
    rows <- vapply(seq_len(nrow(ct)), function(i) {
      sig <- ifelse(ct[i,4] < 0.001, "***",
             ifelse(ct[i,4] < 0.01,  "** ",
             ifelse(ct[i,4] < 0.05,  "*  ",
             ifelse(ct[i,4] < 0.10,  ".  ", "   "))))
      sprintf("  %-18s  %10.4f  %10.4f  %8.3f  %10.4f %s",
              rownames(ct)[i], ct[i,1], ct[i,2], ct[i,3], ct[i,4], sig)
    }, character(1))
    c(sep, titulo, sep, hdr,
      paste(rep("-", 72), collapse = ""),
      rows,
      paste(rep("-", 72), collapse = ""),
      "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1",
      extra_lines,
      sep)
  }

  # ── Helper: comparacion coeficientes ─────────────────────────────────────────
  .comparar <- function(cn, cr, fuente) {
    nms <- intersect(names(cn), names(cr))
    if (!length(nms)) return("Sin coeficientes en comun.")
    sep   <- paste(rep("-", 72), collapse = "")
    hdr   <- sprintf("  %-18s  %10s  %10s  %10s  %s",
                     "Variable", "NEVEN", "Libro", "Diferencia", "Estado")
    filas <- vapply(nms, function(nm) {
      dif <- abs(cn[[nm]] - cr[[nm]])
      sprintf("  %-18s  %10.4f  %10.4f  %10.2e  %s",
              nm, cn[[nm]], cr[[nm]], dif,
              ifelse(dif < 0.01, "OK", "REVISAR"))
    }, character(1))
    mse <- mean((cn[nms] - cr[nms])^2)
    c(sep,
      paste0("  VERIFICACION vs. ", fuente),
      sep, hdr,
      paste(rep("-", 72), collapse = ""),
      filas,
      paste(rep("-", 72), collapse = ""),
      sprintf("  MSE total: %.2e   %s  (umbral: 1e-7)",
              mse, ifelse(mse < 1e-7, "PARIDAD ESTADISTICA OK", "REVISAR")),
      sep)
  }

  # ── Helper unificado de referencia del libro ─────────────────────────────────
  # Mismo formato que verificacion: sprintf, guiones, sin Unicode
  .ref_coefs <- function(titulo, call_str, coefs_mat, r2 = NULL,
                         f_str = NULL, n_str = NULL, nota = NULL) {
    sep <- paste(rep("-", 72), collapse = "")
    hdr <- sprintf("  %-18s  %10s  %10s  %8s  %10s",
                   "Variable", "Estimate", "Std.Err", "t/z", "p-value")
    rows <- vapply(seq_len(nrow(coefs_mat)), function(i) {
      sprintf("  %-18s  %10.4f  %10.4f  %8.3f  %s",
              coefs_mat[i, "var"], as.numeric(coefs_mat[i, "est"]),
              as.numeric(coefs_mat[i, "se"]),  as.numeric(coefs_mat[i, "t"]),
              coefs_mat[i, "pstr"])
    }, character(1))
    extra <- c(paste(rep("-", 72), collapse = ""),
               "  Signif: *** p<0.001  ** p<0.01  * p<0.05  . p<0.1")
    if (!is.null(r2))    extra <- c(extra, sprintf("  R-squared:  %.4f", r2))
    if (!is.null(f_str)) extra <- c(extra, paste0("  F-stat:     ", f_str))
    if (!is.null(n_str)) extra <- c(extra, paste0("  Obs:        ", n_str))
    if (!is.null(nota))  extra <- c(extra, paste0("  Nota:       ", nota))
    c(sep, titulo, paste0("  Call: ", call_str), sep,
      hdr, paste(rep("-", 72), collapse = ""),
      rows, extra, sep)
  }

  # ===========================================================================
  # CASO 1: WAGE1 -- MCO Multiple (Cap. 3)
  # ===========================================================================
  if (Caso == 1L) {
    ds     <- wooldridge::wage1
    modelo <- lm(wage ~ educ + exper + tenure, data = ds)
    sm     <- summary(modelo); ct <- sm$coefficients
    fstat  <- sm$fstatistic
    pf_val <- pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)

    res_lines <- .coef_table(ct, "  NEVEN: WAGE1 -- MCO Multiple",
      c(sprintf("  R-squared:  %.4f   Adj R-sq: %.4f", sm$r.squared, sm$adj.r.squared),
        sprintf("  F-stat:     %.2f on %d and %d DF,  p-value: %.4e",
                fstat[1], fstat[2], fstat[3], pf_val),
        sprintf("  Obs: %d", nrow(ds))))

    ref_mat <- rbind(
      c(var="(Intercept)", est="-2.8727", se="0.7289",  t="-3.940", pstr="<0.001 ***"),
      c(var="educ",        est=" 0.5990", se="0.0512",  t="11.698", pstr="<0.001 ***"),
      c(var="exper",       est=" 0.0223", se="0.0120",  t=" 1.858", pstr="0.063  .  "),
      c(var="tenure",      est=" 0.1693", se="0.0222",  t=" 7.630", pstr="<0.001 ***")
    )
    ref_lines <- .ref_coefs(
      "  REFERENCIA: Wooldridge Cap. 3, Ejemplo 3.2",
      "lm(wage ~ educ + exper + tenure)   Dataset: WAGE1",
      ref_mat, r2 = 0.3061,
      f_str = "55.25 on 3 and 522 DF,  p-value: <2.2e-16",
      n_str = "526",
      nota  = "1 anio mas de educ = +$0.60/hora (ceteris paribus)")

    ver_lines <- .comparar(coef(modelo),
      c("(Intercept)" = -2.8727, "educ" = 0.5990,
        "exper" = 0.0223, "tenure" = 0.1693),
      "Wooldridge Cap. 3, Ejemplo 3.2")
  }

  # ===========================================================================
  # CASO 2: 401K -- LPM (Cap. 7)
  # ===========================================================================
  else if (Caso == 2L) {
    ds     <- wooldridge::k401k
    modelo <- lm(prate ~ mrate + age + totemp, data = ds)
    sm     <- summary(modelo); ct <- sm$coefficients
    fstat  <- sm$fstatistic
    pf_val <- pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)

    res_lines <- .coef_table(ct, "  NEVEN: 401K -- Modelo Lineal de Probabilidad",
      c(sprintf("  R-squared:  %.4f", sm$r.squared),
        sprintf("  F-stat:     %.2f on %d and %d DF,  p-value: %.4e",
                fstat[1], fstat[2], fstat[3], pf_val),
        sprintf("  Obs: %d", nrow(ds))))

    ref_mat <- rbind(
      c(var="(Intercept)", est="83.0755",   se=" 0.8777", t=" 94.65", pstr="<0.001 ***"),
      c(var="mrate",       est=" 5.8611",   se=" 0.5269", t=" 11.12", pstr="<0.001 ***"),
      c(var="age",         est=" 0.2690",   se=" 0.0455", t="  5.91", pstr="<0.001 ***"),
      c(var="totemp",      est="-0.0000884",se=" 0.0000117",t="-7.56",pstr="<0.001 ***")
    )
    ref_lines <- .ref_coefs(
      "  REFERENCIA: Wooldridge Cap. 7, Ejemplo 7.12",
      "lm(prate ~ mrate + age + totemp)   Dataset: 401K",
      ref_mat, r2 = 0.1002,
      f_str = "66.38 on 3 and 1800 DF",
      n_str = "1804",
      nota  = "+1 en mrate = +5.86 pp en participacion")

    ver_lines <- .comparar(coef(modelo),
      c("(Intercept)" = 83.0755, "mrate" = 5.8611,
        "age" = 0.2690, "totemp" = -8.84e-05),
      "Wooldridge Cap. 7, Ejemplo 7.12")
  }

  # ===========================================================================
  # CASO 3: JTRAIN -- Panel Efectos Fijos (Cap. 14)
  # ===========================================================================
  else if (Caso == 3L) {
    if (!requireNamespace("plm", quietly = TRUE))
      stop("El paquete 'plm' no esta instalado.")
    ds     <- wooldridge::jtrain
    pdata  <- suppressMessages(suppressWarnings(
      plm::pdata.frame(ds, index = c("fcode", "year"))
    ))
    modelo <- suppressMessages(suppressWarnings(
      plm::plm(lscrap ~ hrsemp + lsales + lemploy,
               data = pdata, model = "within", effect = "individual")
    ))
    ct <- summary(modelo)$coefficients

    res_lines <- .coef_table(ct, "  NEVEN: JTRAIN -- Panel Efectos Fijos (within)",
      c(sprintf("  Obs: %d  (45 firmas x 3 anios)", nrow(pdata[!is.na(pdata$lscrap),])),
        "  Modelo: within (efectos fijos individuales por firma)"))

    ref_mat <- rbind(
      c(var="hrsemp",  est="-0.0401", se="0.0210", t="-1.91", pstr="0.059  .  "),
      c(var="lsales",  est="-0.0512", se="0.2045", t="-0.25", pstr="0.803     "),
      c(var="lemploy", est=" 0.0469", se="0.3587", t=" 0.13", pstr="0.896     ")
    )
    ref_lines <- .ref_coefs(
      "  REFERENCIA: Wooldridge Cap. 14, Ejemplo 14.1",
      "plm(lscrap ~ hrsemp + lsales + lemploy | fcode)   Dataset: JTRAIN",
      ref_mat,
      n_str = "135 (45 firmas x 3 anios, panel no balanceado)",
      nota  = "+10% entrenamiento = -0.4% desperdicio (efecto causal)")

    ver_lines <- .comparar(coef(modelo),
      c("hrsemp" = -0.0401, "lsales" = -0.0512, "lemploy" = 0.0469),
      "Wooldridge Cap. 14, Ejemplo 14.1")
  }

  # ===========================================================================
  # CASO 4: SMOKE -- Tobit (Cap. 17)
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
    sig <- tryCatch(round(exp(coef(modelo)["Log(scale)"]), 3), error = function(e) "N/A")
    cens_pct <- round(100 * mean(ds$cigs == 0, na.rm = TRUE))

    res_lines <- .coef_table(ct2, "  NEVEN: SMOKE -- Tobit (censura en cero)",
      c(sprintf("  Log-Likelihood: %s   Sigma: %s", ll, sig),
        sprintf("  Obs: %d   Censuradas (cigs=0): %d%%", nrow(ds), cens_pct)))

    ref_mat <- rbind(
      c(var="(Intercept)", est=" -3.6398", se="24.079", t="-0.15", pstr="0.880     "),
      c(var="lincome",     est="  0.8803", se=" 0.728", t=" 1.21", pstr="0.228     "),
      c(var="lcigpric",    est=" -0.7508", se=" 5.773", t="-0.13", pstr="0.897     "),
      c(var="educ",        est=" -0.5014", se=" 0.167", t="-3.00", pstr="0.003  ** "),
      c(var="age",         est="  0.7707", se=" 0.160", t=" 4.82", pstr="<0.001 ***"),
      c(var="agesq",       est=" -0.0090", se=" 0.002", t="-5.17", pstr="<0.001 ***"),
      c(var="restaurn",    est=" -2.8251", se=" 1.112", t="-2.54", pstr="0.011  *  ")
    )
    ref_lines <- .ref_coefs(
      "  REFERENCIA: Wooldridge Cap. 17, Ejemplo 17.2",
      "tobit(cigs ~ lincome+lcigpric+educ+age+agesq+restaurn, left=0)   Dataset: SMOKE",
      ref_mat,
      n_str = "807   Censuradas: 54%",
      nota  = "Tobit corrige el sesgo de MCO cuando la mayoria no fuma")

    ver_lines <- .comparar(
      coef(modelo)[names(coef(modelo)) != "Log(scale)"],
      c("(Intercept)" = -3.6398, "lincome" = 0.8803, "lcigpric" = -0.7508,
        "educ" = -0.5014, "age" = 0.7707, "agesq" = -0.0090, "restaurn" = -2.8251),
      "Wooldridge Cap. 17, Ejemplo 17.2")
  }

  # ===========================================================================
  # CASO 5: FERTIL1 -- Serie de Tiempo + RESET (Cap. 10)
  # ===========================================================================
  else if (Caso == 5L) {
    if (!requireNamespace("lmtest", quietly = TRUE))
      stop("El paquete 'lmtest' no esta instalado.")
    ds     <- wooldridge::fertil1
    modelo <- lm(gfr ~ pe + ww2 + pill + t, data = ds)
    sm     <- summary(modelo); ct <- sm$coefficients
    fstat  <- sm$fstatistic
    pf_val <- pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)

    reset_str <- tryCatch({
      r <- lmtest::resettest(modelo, power = 2:3, type = "fitted")
      sprintf("F = %.3f, df = (%d, %d), p-valor = %.4f  %s",
              r$statistic, r$parameter[1], r$parameter[2], r$p.value,
              ifelse(r$p.value < 0.05, "-> FORMA FUNCIONAL PROBLEMATICA",
                     "-> Forma funcional adecuada"))
    }, error = function(e) paste("No disponible:", e$message))

    sep <- paste(rep("-", 72), collapse = "")
    res_lines <- c(
      .coef_table(ct, "  NEVEN: FERTIL1 -- Serie de Tiempo",
        c(sprintf("  R-squared:  %.4f   Adj R-sq: %.4f", sm$r.squared, sm$adj.r.squared),
          sprintf("  F-stat:     %.2f on %d and %d DF,  p-value: %.4e",
                  fstat[1], fstat[2], fstat[3], pf_val),
          sprintf("  Obs: %d", nrow(ds)))),
      sep, "  PRUEBA RESET DE RAMSEY", sep,
      paste0("  ", reset_str), sep
    )

    ref_mat <- rbind(
      c(var="(Intercept)", est="98.6823", se="3.2078", t="30.77", pstr="<0.001 ***"),
      c(var="pe",          est="-0.0785", se="0.0300", t="-2.62", pstr="0.010  *  "),
      c(var="ww2",         est="-24.238", se="7.458",  t="-3.25", pstr="0.002  ** "),
      c(var="pill",        est="-31.594", se="3.982",  t="-7.93", pstr="<0.001 ***"),
      c(var="t",           est=" -1.150", se="0.192",  t="-5.99", pstr="<0.001 ***")
    )
    ref_lines <- .ref_coefs(
      "  REFERENCIA: Wooldridge Cap. 10, Ecuacion 10.15",
      "lm(gfr ~ pe + ww2 + pill + t)   Dataset: FERTIL1",
      ref_mat, r2 = 0.6633,
      f_str = "34.45 on 4 and 67 DF",
      n_str = "72",
      nota  = "La pildora redujo la fertilidad en ~31.6 puntos")

    ver_lines <- .comparar(coef(modelo),
      c("(Intercept)" = 98.6823, "pe" = -0.0785,
        "ww2" = -24.238, "pill" = -31.594, "t" = -1.150),
      "Wooldridge Cap. 10, Ec. 10.15")
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
    sep  <- paste(rep("-", 72), collapse = "")

    res_lines <- c(
      sep, "  NEVEN: CEOSAL1 -- Estadistica Descriptiva", sep,
      sprintf("  Variable:   salary (salario anual, miles USD)   N = %d", length(x)),
      sep,
      sprintf("  Media:      %8.2f", mean(x)),
      sprintf("  Mediana:    %8.2f", median(x)),
      sprintf("  Min:        %8.2f   Max: %.2f", min(x), max(x)),
      sprintf("  Q1:         %8.2f", q1),
      sprintf("  Q3:         %8.2f", q3),
      sprintf("  IQR:        %8.2f", iqr),
      sep,
      sprintf("  Umbral outlier (Q3 + 1.5*IQR): %.2f", lsup),
      sprintf("  Outliers detectados:            %d observaciones", length(outs)),
      if (length(outs))
        paste0("  Valores top: ", paste(head(outs, 8), collapse = "  "))
      else "  Sin outliers",
      sep
    )

    ref_lines <- c(
      sep, "  REFERENCIA: Wooldridge Cap. 9 -- CEOSAL1", sep,
      sprintf("  Variable:   salary (salario anual, miles USD)   N = 209"),
      sep,
      sprintf("  Media:      %8.2f", 1281.12),
      sprintf("  Mediana:    %8.2f", 1037.00),
      sprintf("  Min:        %8.2f   Max: %.2f", 223.00, 14822.00),
      sprintf("  Q1:         %8.2f", 736.00),
      sprintf("  Q3:         %8.2f", 1534.00),
      sprintf("  IQR:        %8.2f", 798.00),
      sep,
      "  Umbral outlier (Q3 + 1.5*IQR): 2731.00",
      "  Outliers detectados:            ~11 CEOs",
      sep,
      "  Nota: distribucion asimetrica -- usar log(salary) es el estandar"
    )

    ver_lines <- c(
      sep, "  VERIFICACION vs. Wooldridge Cap. 9", sep,
      sprintf("  %-18s  %10s  %10s  %10s  %s",
              "Estadistico", "NEVEN", "Libro", "Diferencia", "Estado"),
      paste(rep("-", 72), collapse = ""),
      sprintf("  %-18s  %10.2f  %10.2f  %10.2f  %s",
              "Media", mean(x), 1281.12, abs(mean(x) - 1281.12),
              ifelse(abs(mean(x) - 1281.12) < 5, "OK", "REVISAR")),
      sprintf("  %-18s  %10.2f  %10.2f  %10.2f  %s",
              "Mediana", median(x), 1037.00, abs(median(x) - 1037),
              ifelse(abs(median(x) - 1037) < 10, "OK", "REVISAR")),
      sprintf("  %-18s  %10d  %10s  %10s  %s",
              "N outliers", length(outs), "~11", "---",
              ifelse(abs(length(outs) - 11) <= 2, "OK", "REVISAR")),
      sep
    )
  }

  # ── Retorno ──────────────────────────────────────────────────────────────────
  return(r_object_to_slots(
    list(
      resultado_NEVEN  = paste(res_lines,  collapse = "\n"),
      referencia_libro = paste(ref_lines,  collapse = "\n"),
      verificacion     = paste(ver_lines,  collapse = "\n")
    ),
    tier_map = c(resultado_NEVEN = 1L, referencia_libro = 1L, verificacion = 1L)
  ))
}
