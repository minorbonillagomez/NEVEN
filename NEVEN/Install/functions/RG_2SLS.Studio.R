# ===============================================================================
# NEVEN Data Lab — MÍNIMOS CUADRADOS EN DOS ETAPAS / VARIABLES INSTRUMENTALES
# (RG Family) — 2SLS / IV Regression
# Wooldridge Cap. 15 — Tratamiento de endogeneidad
# ===============================================================================
# DESCRIPCIÓN:
#   2SLS corrige el sesgo de endogeneidad cuando una o más variables explicativas
#   están correlacionadas con el error (por variable omitida, error de medición
#   o causalidad inversa). Se usan instrumentos Z que satisfacen:
#     - Relevancia: corr(Z, X_endo) ≠ 0   (verificado con F > 10 en 1ª etapa)
#     - Exogeneidad: corr(Z, u) = 0       (supuesto no testeable directamente)
#
#   Ejemplo clásico: retorno a la educación con educación endógena
#   e instrumento = educación del padre (Wooldridge: wage2, mroz)
#
# PAQUETE: AER::ivreg (Instrumental Variables Regression)
# ===============================================================================

RG_2SLS.Studio <- function(data_Y,
                             data_Endo,
                             data_Exo       = NULL,
                             data_Instru,
                             NivelAlpha     = 0.05,
                             DiagnosticosF  = TRUE) {

  # ── Validaciones ─────────────────────────────────────────────────────────────
  if (!is.data.frame(data_Y) || nrow(data_Y) == 0)
    stop("'data_Y' debe ser un data.frame con al menos una fila.")
  if (!is.data.frame(data_Endo) || nrow(data_Endo) == 0)
    stop("'data_Endo' (variables endógenas) debe ser un data.frame.")
  if (!is.data.frame(data_Instru) || nrow(data_Instru) == 0)
    stop("'data_Instru' (instrumentos Z) debe ser un data.frame.")
  if (ncol(data_Instru) < ncol(data_Endo))
    stop("Se necesitan al menos tantos instrumentos como variables endógenas (condición de orden).")

  n_endo  <- ncol(data_Endo)
  n_instr <- ncol(data_Instru)
  if (nrow(data_Y) != nrow(data_Endo) || nrow(data_Y) != nrow(data_Instru))
    stop("Todos los data.frames deben tener el mismo número de filas.")

  NivelAlpha <- as.numeric(NivelAlpha)
  if (is.na(NivelAlpha) || NivelAlpha <= 0 || NivelAlpha >= 1) NivelAlpha <- 0.05

  if (!requireNamespace("AER", quietly = TRUE))
    stop("El paquete 'AER' no está instalado. Use =R.UT_InstalacionWeb() para instalarlo.")
  if (!requireNamespace("lmtest", quietly = TRUE))
    stop("El paquete 'lmtest' no está instalado.")

  # ── Construcción del data.frame completo ────────────────────────────────────
  y_col     <- names(data_Y)[1]
  endo_cols <- names(data_Endo)
  inst_cols <- names(data_Instru)

  has_exo <- !is.null(data_Exo) && is.data.frame(data_Exo) && ncol(data_Exo) > 0
  exo_cols <- if (has_exo) names(data_Exo) else character(0)

  df <- cbind(data_Y[, y_col, drop = FALSE], data_Endo, data_Instru)
  if (has_exo) df <- cbind(df, data_Exo)
  df <- df[complete.cases(df), ]
  n  <- nrow(df)

  # ── Fórmula ivreg: y ~ X_endo + X_exo | X_exo + Z ──────────────────────────
  # AER::ivreg usa notación: depvar ~ regressors | instruments
  # El lado derecho del | incluye las exógenas (que se instrumentan a sí mismas)
  # más los instrumentos externos Z

  regressors   <- c(endo_cols, exo_cols)
  instruments  <- c(exo_cols, inst_cols)

  fml_iv <- as.formula(
    paste0(y_col, " ~ ",
           paste(regressors, collapse = " + "),
           " | ",
           paste(instruments, collapse = " + "))
  )

  # ── Estimación 2SLS ──────────────────────────────────────────────────────────
  modelo_iv <- tryCatch(
    AER::ivreg(fml_iv, data = df),
    error = function(e) stop(paste("Error en 2SLS:", conditionMessage(e)))
  )

  sm_iv <- summary(modelo_iv, diagnostics = isTRUE(DiagnosticosF))

  # ── Tabla de coeficientes 2SLS ───────────────────────────────────────────────
  ct <- as.data.frame(sm_iv$coefficients)
  tabla_2sls <- data.frame(
    Variable    = rownames(ct),
    Coeficiente = round(ct[, 1], 6),
    EE          = round(ct[, 2], 6),
    t_stat      = round(ct[, 3], 4),
    p_valor     = round(ct[, 4], 6),
    Sig         = ifelse(ct[, 4] < 0.001, "***",
                  ifelse(ct[, 4] < 0.01,  "**",
                  ifelse(ct[, 4] < 0.05,  "*",
                  ifelse(ct[, 4] < 0.10,  ".", "")))),
    stringsAsFactors = FALSE
  )

  # ── Diagnósticos: F primera etapa + Wu-Hausman + Sargan ─────────────────────
  diag_rows <- list()

  if (isTRUE(DiagnosticosF) && !is.null(sm_iv$diagnostics)) {
    diags <- sm_iv$diagnostics
    for (i in seq_len(nrow(diags))) {
      nm <- rownames(diags)[i]
      # Interpretación directa para cada test
      interp <- switch(nm,
        "Weak instruments" = paste0(
          if (diags[i, "statistic"] >= 10)
            "✓ Instrumentos relevantes (F=%.1f >= 10)"
          else
            "⚠ Instrumentos débiles (F=%.1f < 10). Resultados no confiables."
        ),
        "Wu-Hausman" = paste0(
          if (diags[i, "p-value"] < NivelAlpha)
            "✓ Endogeneidad confirmada (p=%.4f < alpha). 2SLS es necesario."
          else
            "– No se rechaza exogeneidad (p=%.4f). MCO podría ser suficiente."
        ),
        "Sargan" = paste0(
          if (diags[i, "p-value"] > NivelAlpha)
            "✓ Instrumentos válidos (p=%.4f > alpha). No se rechaza exogeneidad de Z."
          else
            "⚠ Test de Sargan rechaza (p=%.4f). Posible instrumento inválido."
        ),
        "—"
      )
      diag_rows[[nm]] <- data.frame(
        Test        = nm,
        Estadistico = round(diags[i, "statistic"], 4),
        gl          = diags[i, "df"],
        p_valor     = round(diags[i, "p-value"], 6),
        Interpretacion = sprintf(interp, diags[i, if (grepl("F=", interp)) "statistic" else "p-value"]),
        stringsAsFactors = FALSE
      )
    }
  }

  tabla_diagnosticos <- if (length(diag_rows) > 0) {
    do.call(rbind, diag_rows)
  } else {
    data.frame(
      Test = "Diagnósticos", Estadistico = NA, gl = NA, p_valor = NA,
      Interpretacion = "Active DiagnosticosF=TRUE para ver F primera etapa, Wu-Hausman y Sargan.",
      stringsAsFactors = FALSE
    )
  }

  # ── Bondad de ajuste ─────────────────────────────────────────────────────────
  tabla_ajuste <- data.frame(
    Estadistico  = c("Observaciones", "Variables_endo", "Instrumentos_ext",
                     "R_cuadrado", "Sigma_residual"),
    Valor        = c(n, n_endo, n_instr - n_endo,
                     round(sm_iv$r.squared, 4),
                     round(sm_iv$sigma, 6)),
    stringsAsFactors = FALSE
  )

  return(r_object_to_slots(
    list(
      coeficientes_2SLS = tabla_2sls,
      diagnosticos_IV   = tabla_diagnosticos,
      bondad_ajuste     = tabla_ajuste
    ),
    tier_map = c(coeficientes_2SLS = 1L, diagnosticos_IV = 1L, bondad_ajuste = 2L)
  ))
}
