# ===============================================================================
# NEVEN Data Lab — MODELO DE HECKMAN (HECKIT) (RG Family)
# Corrección del sesgo de selección muestral
# Wooldridge Cap. 17 — Cuando la muestra no es aleatoria
# ===============================================================================
# DESCRIPCIÓN:
#   El modelo de Heckman (1979) corrige el sesgo de selección cuando los datos
#   que observamos no son una muestra aleatoria de la población de interés.
#
#   Ejemplos clásicos (Wooldridge):
#   - Salarios: solo observamos salarios de quienes trabajan (selección laboral)
#   - Crédito: solo observamos pagos de quienes recibieron préstamo
#   - Educación: solo observamos retornos de quienes completaron la educación
#
#   El modelo en dos etapas (Heckit):
#   1ª etapa (Selección): Probit con variable binaria de selección → razón de Mills λ
#   2ª etapa (Resultado): MCO de la ecuación de interés con λ como regresor adicional
#
#   Si el coeficiente de λ es significativo → hay sesgo de selección.
#
# PAQUETE: sampleSelection::heckit
# ===============================================================================

RG_HECKIT.Studio <- function(data_Y_obs,
                               data_X_outcome,
                               data_S_binary,
                               data_X_selection = NULL,
                               NivelAlpha       = 0.05) {

  # ── Validaciones ─────────────────────────────────────────────────────────────
  if (!is.data.frame(data_Y_obs) || nrow(data_Y_obs) == 0)
    stop("'data_Y_obs' (variable de resultado observada) debe ser un data.frame.")
  if (!is.data.frame(data_X_outcome) || nrow(data_X_outcome) == 0)
    stop("'data_X_outcome' (regresores de la ecuación de resultado) debe ser un data.frame.")
  if (!is.data.frame(data_S_binary) || nrow(data_S_binary) == 0)
    stop("'data_S_binary' (indicador de selección 0/1) debe ser un data.frame.")

  n_obs <- nrow(data_Y_obs)
  if (nrow(data_X_outcome) != n_obs || nrow(data_S_binary) != n_obs)
    stop("Todos los data.frames deben tener el mismo número de filas.")

  NivelAlpha <- as.numeric(NivelAlpha)
  if (is.na(NivelAlpha) || NivelAlpha <= 0 || NivelAlpha >= 1) NivelAlpha <- 0.05

  if (!requireNamespace("sampleSelection", quietly = TRUE))
    stop("El paquete 'sampleSelection' no está instalado. Use =R.UT_InstalacionWeb() para instalarlo.")

  # ── Preparación de variables ─────────────────────────────────────────────────
  y_col  <- names(data_Y_obs)[1]
  s_col  <- names(data_S_binary)[1]
  xo_cols <- names(data_X_outcome)

  has_sel_vars <- !is.null(data_X_selection) &&
                  is.data.frame(data_X_selection) &&
                  ncol(data_X_selection) > 0

  # Si no se proveen regresores adicionales para la selección, usar los mismos
  # que la ecuación de resultado (modelo no identificado por exclusión, solo por
  # la no-linealidad del probit — válido pero menos robusto).
  xs_cols <- if (has_sel_vars) names(data_X_selection) else xo_cols

  # Construir data.frame unificado
  df <- cbind(
    data_Y_obs[, y_col, drop = FALSE],
    data_S_binary[, s_col, drop = FALSE],
    data_X_outcome
  )
  if (has_sel_vars) df <- cbind(df, data_X_selection)
  df <- df[complete.cases(df), ]
  n  <- nrow(df)

  # Asegurar que S sea 0/1
  s_vals <- df[[s_col]]
  if (!all(s_vals %in% c(0, 1, TRUE, FALSE, NA)))
    stop("'data_S_binary' debe contener solo valores 0/1.")
  df[[s_col]] <- as.integer(df[[s_col]])

  # ── Fórmulas con reformulate() ───────────────────────────────────────────────
  # Ecuación de selección: S ~ X_selection
  fml_sel <- reformulate(termlabels = xs_cols, response = s_col)

  # Ecuación de resultado: Y ~ X_outcome
  fml_out <- reformulate(termlabels = xo_cols, response = y_col)

  # ── Estimación Heckit (2 etapas) ─────────────────────────────────────────────
  modelo_heckit <- tryCatch(
    sampleSelection::heckit(
      selection = fml_sel,
      outcome   = fml_out,
      data      = df,
      method    = "2step"
    ),
    error = function(e) stop(paste("Error en Heckit:", conditionMessage(e)))
  )

  sm <- summary(modelo_heckit)

  # ── Tabla: coeficientes de la ecuación de resultado ──────────────────────────
  out_coef <- sm$coefficients[sm$tobitType == "outcome" | names(sm$coefficients) != "rho", , drop = FALSE]
  # sampleSelection summary devuelve una tabla con todas las etapas juntas
  # Extraemos la sección de outcome
  all_coef <- as.data.frame(coef(sm))
  # Coeficientes de la 2ª etapa (resultado)
  outcome_rows <- grep(paste0("^O_|outcome"), rownames(all_coef), value = TRUE)
  if (length(outcome_rows) == 0) {
    # fallback: tomar los primeros nrow de xo_cols + intercept
    nc_out <- length(xo_cols) + 1
    outcome_rows <- rownames(all_coef)[seq_len(min(nc_out, nrow(all_coef)))]
  }

  ct_out <- all_coef[outcome_rows, , drop = FALSE]
  tabla_outcome <- data.frame(
    Variable    = sub("^O_", "", rownames(ct_out)),
    Coeficiente = round(ct_out[, 1], 6),
    EE          = round(ct_out[, 2], 6),
    t_stat      = round(ct_out[, 3], 4),
    p_valor     = round(ct_out[, 4], 6),
    Sig         = ifelse(ct_out[, 4] < 0.001, "***",
                  ifelse(ct_out[, 4] < 0.01,  "**",
                  ifelse(ct_out[, 4] < 0.05,  "*",
                  ifelse(ct_out[, 4] < 0.10,  ".", "")))),
    stringsAsFactors = FALSE
  )

  # ── Tabla: coeficientes de la ecuación de selección (probit 1ª etapa) ────────
  sel_rows <- grep("^S_|selection", rownames(all_coef), value = TRUE)
  ct_sel   <- all_coef[sel_rows, , drop = FALSE]
  tabla_selection <- data.frame(
    Variable    = sub("^S_", "", rownames(ct_sel)),
    Coeficiente = round(ct_sel[, 1], 6),
    EE          = round(ct_sel[, 2], 6),
    t_stat      = round(ct_sel[, 3], 4),
    p_valor     = round(ct_sel[, 4], 6),
    stringsAsFactors = FALSE
  )

  # ── Diagnóstico clave: ¿es significativa la razón de Mills (lambda)? ──────────
  # Si lambda (IMR) es significativa → existe sesgo de selección corregido por Heckman
  lambda_row <- grep("invMillsRatio|lambda|imr|Mills", rownames(all_coef),
                     ignore.case = TRUE, value = TRUE)
  lambda_sig <- FALSE
  lambda_interp <- "Razón de Mills no encontrada en la salida del modelo."

  if (length(lambda_row) > 0) {
    lp <- all_coef[lambda_row[1], 4]
    lambda_sig <- !is.na(lp) && lp < NivelAlpha
    lambda_interp <- if (lambda_sig) {
      paste0("✓ La Razón de Mills Inversa (lambda) es significativa (p=",
             round(lp, 4), " < alpha=", NivelAlpha, "): ",
             "Se confirma sesgo de selección. La corrección de Heckman es necesaria.")
    } else {
      paste0("– La Razón de Mills Inversa (lambda) NO es significativa (p=",
             round(lp, 4), " >= alpha=", NivelAlpha, "): ",
             "No hay evidencia de sesgo de selección. MCO podría ser suficiente.")
    }
  }

  # ── Resumen estadístico ───────────────────────────────────────────────────────
  n_selected  <- sum(df[[s_col]] == 1, na.rm = TRUE)
  n_censored  <- n - n_selected
  pct_obs     <- round(100 * n_selected / n, 1)

  tabla_resumen <- data.frame(
    Estadistico = c("Observaciones_total", "Seleccionadas_(S=1)",
                    "Censuradas_(S=0)", "Pct_observadas",
                    "Identificacion",   "Log_likelihood"),
    Valor       = c(n, n_selected, n_censored,
                    paste0(pct_obs, "%"),
                    if (has_sel_vars) "Por exclusión (recomendado)" else "Solo no-linealidad probit",
                    round(tryCatch(logLik(modelo_heckit)[[1]], error = function(e) NA), 2)),
    stringsAsFactors = FALSE
  )

  return(r_object_to_slots(
    list(
      ecuacion_resultado    = tabla_outcome,
      ecuacion_seleccion    = tabla_selection,
      diagnostico_seleccion = data.frame(Interpretacion = lambda_interp,
                                          stringsAsFactors = FALSE),
      resumen_modelo        = tabla_resumen
    ),
    tier_map = c(
      ecuacion_resultado    = 1L,
      ecuacion_seleccion    = 2L,
      diagnostico_seleccion = 1L,
      resumen_modelo        = 1L
    )
  ))
}
