# ===============================================================================
# NEVEN Data Lab — MÍNIMOS CUADRADOS GENERALIZADOS FACTIBLES (FGLS) (RG Family)
# Corrección de heterocedasticidad por estructura modelada
# Wooldridge Cap. 8 — Cuando la varianza de los errores sigue una estructura
# ===============================================================================
# DESCRIPCIÓN:
#   FGLS (Feasible Generalized Least Squares) es eficiente cuando la
#   heterocedasticidad sigue una estructura que puede estimarse. A diferencia
#   de Newey-West (que solo corrige los EE), FGLS transforma los datos para
#   obtener coeficientes más eficientes (menor varianza).
#
#   Estrategia implementada (Wooldridge):
#   1. Estimar MCO y obtener residuos
#   2. Regresar log(res²) sobre las X para estimar log(sigma²)
#   3. Obtener pesos w = 1/exp(fitted)
#   4. Estimar WLS (MCO ponderado) con esos pesos
#
#   Cuándo usar: datos de corte transversal con heterocedasticidad
#   cuya varianza depende de los regresores.
# ===============================================================================

RG_FGLS.Studio <- function(data_Y,
                             data_X,
                             NivelAlpha = 0.05) {

  # ── Validaciones ─────────────────────────────────────────────────────────────
  if (!is.data.frame(data_Y) || nrow(data_Y) == 0)
    stop("'data_Y' debe ser un data.frame con al menos una fila.")
  if (!is.data.frame(data_X) || nrow(data_X) == 0)
    stop("'data_X' debe ser un data.frame con al menos una fila.")
  if (nrow(data_Y) != nrow(data_X))
    stop("'data_Y' y 'data_X' deben tener el mismo número de filas.")

  NivelAlpha <- as.numeric(NivelAlpha)
  if (is.na(NivelAlpha) || NivelAlpha <= 0 || NivelAlpha >= 1) NivelAlpha <- 0.05

  y_col  <- names(data_Y)[1]
  x_cols <- names(data_X)
  df     <- cbind(data_Y[, y_col, drop = FALSE], data_X)
  df     <- df[complete.cases(df), ]
  n      <- nrow(df)

  # ── Paso 1: MCO inicial ──────────────────────────────────────────────────────
  fml      <- reformulate(termlabels = x_cols, response = y_col)
  ols_base <- lm(fml, data = df)
  res_ols  <- residuals(ols_base)

  # ── Paso 2: modelar log(u²) ~ X para estimar estructura de varianza ──────────
  log_u2   <- log(res_ols^2 + 1e-10)   # 1e-10 para evitar log(0)
  df_aux   <- data_X
  df_aux$.log_u2 <- log_u2

  fml_var  <- reformulate(termlabels = x_cols, response = ".log_u2")
  var_model <- lm(fml_var, data = df_aux)

  # ── Paso 3: calcular pesos w = 1/exp(fitted) ─────────────────────────────────
  h_hat  <- fitted(var_model)
  pesos  <- 1 / exp(h_hat)
  pesos  <- pesos / mean(pesos)   # normalizar para estabilidad numérica

  # ── Paso 4: WLS (equivalente a FGLS) ────────────────────────────────────────
  fgls_modelo <- lm(fml, data = df, weights = pesos)
  sm_fgls     <- summary(fgls_modelo)
  sm_ols      <- summary(ols_base)

  # ── Tabla FGLS ──────────────────────────────────────────────────────────────
  ct_fgls <- as.data.frame(sm_fgls$coefficients)
  tabla_fgls <- data.frame(
    Variable    = rownames(ct_fgls),
    Coef_FGLS   = round(ct_fgls[, 1], 6),
    EE_FGLS     = round(ct_fgls[, 2], 6),
    t_stat      = round(ct_fgls[, 3], 4),
    p_valor     = round(ct_fgls[, 4], 6),
    Sig         = ifelse(ct_fgls[, 4] < 0.001, "***",
                  ifelse(ct_fgls[, 4] < 0.01,  "**",
                  ifelse(ct_fgls[, 4] < 0.05,  "*",
                  ifelse(ct_fgls[, 4] < 0.10,  ".", "")))),
    stringsAsFactors = FALSE
  )

  # ── Tabla OLS para comparación ────────────────────────────────────────────
  ct_ols <- as.data.frame(sm_ols$coefficients)
  tabla_ols <- data.frame(
    Variable  = rownames(ct_ols),
    Coef_OLS  = round(ct_ols[, 1], 6),
    EE_OLS    = round(ct_ols[, 2], 6),
    t_OLS     = round(ct_ols[, 3], 4),
    p_OLS     = round(ct_ols[, 4], 6),
    stringsAsFactors = FALSE
  )

  # ── Bondad de ajuste comparativa ─────────────────────────────────────────────
  tabla_ajuste <- data.frame(
    Estadistico      = c("R_cuadrado", "R_cuadrado_ajust", "AIC", "BIC", "Observaciones"),
    MCO              = c(round(sm_ols$r.squared, 4),
                         round(sm_ols$adj.r.squared, 4),
                         round(AIC(ols_base), 2),
                         round(BIC(ols_base), 2),
                         n),
    FGLS             = c(round(sm_fgls$r.squared, 4),
                         round(sm_fgls$adj.r.squared, 4),
                         round(AIC(fgls_modelo), 2),
                         round(BIC(fgls_modelo), 2),
                         n),
    stringsAsFactors = FALSE
  )

  # ── Test de Breusch-Pagan post-FGLS para validar corrección ─────────────────
  nota_bp <- ""
  if (requireNamespace("lmtest", quietly = TRUE)) {
    bp_fgls <- tryCatch(
      lmtest::bptest(fgls_modelo),
      error = function(e) NULL
    )
    if (!is.null(bp_fgls)) {
      nota_bp <- paste0(
        " | Breusch-Pagan post-FGLS: p=", round(bp_fgls$p.value, 4),
        if (bp_fgls$p.value < NivelAlpha) " (aún hay heterocedasticidad residual)"
        else " (heterocedasticidad corregida)"
      )
    }
  }

  nota <- paste0(
    "FGLS implementado como WLS con pesos w=1/exp(log_var_hat). ",
    "Estrategia: Wooldridge Cap. 8 (estimación en 2 pasos). ",
    "Muestra: ", n, " obs.", nota_bp
  )

  return(r_object_to_slots(
    list(
      coeficientes_FGLS  = tabla_fgls,
      coeficientes_OLS   = tabla_ols,
      bondad_de_ajuste   = tabla_ajuste,
      nota               = nota
    ),
    tier_map = c(coeficientes_FGLS = 1L, coeficientes_OLS = 2L,
                 bondad_de_ajuste  = 1L, nota = 1L)
  ))
}
