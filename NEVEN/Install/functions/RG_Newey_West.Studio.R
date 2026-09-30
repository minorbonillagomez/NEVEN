# ===============================================================================
# NEVEN Data Lab — ESTIMADOR NEWEY-WEST HAC (RG Family)
# Errores estándar robustos a heterocedasticidad Y autocorrelación
# Wooldridge Cap. 12/15 — Corrección HAC (Heteroscedasticity-Autocorrelation Consistent)
# ===============================================================================
# DESCRIPCIÓN:
#   El estimador Newey-West (1987) produce errores estándar robustos cuando
#   los residuos del modelo MCO presentan heterocedasticidad de forma desconocida
#   Y/O autocorrelación serial (común en series de tiempo y datos de panel).
#   Los coeficientes no cambian — solo cambian los errores estándar, t-stats y p-valores.
#
#   Cuándo usar: series de tiempo, datos longitudinales, o cuando
#   Breusch-Pagan o Durbin-Watson indican problemas.
#
# PATRÓN TÉCNICO:
#   - reformulate() para la fórmula — prohibido eval(parse())
#   - Requiere: sandwich + lmtest (ya instalados en NEVEN)
# ===============================================================================

RG_Newey_West.Studio <- function(data_Y,
                                  data_X,
                                  Rezagos    = NULL,
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

  if (!requireNamespace("sandwich", quietly = TRUE))
    stop("El paquete 'sandwich' no está instalado.")
  if (!requireNamespace("lmtest", quietly = TRUE))
    stop("El paquete 'lmtest' no está instalado.")

  # ── Modelo MCO base ──────────────────────────────────────────────────────────
  fml    <- reformulate(termlabels = x_cols, response = y_col)
  modelo <- lm(fml, data = df)

  # ── Número de rezagos: regla de Newey-West si no se especifica ───────────────
  # Regla estándar: floor(4 * (n/100)^(2/9))
  lag_nw <- if (is.null(Rezagos) || is.na(as.integer(Rezagos))) {
    max(1L, floor(4 * (n / 100) ^ (2 / 9)))
  } else {
    as.integer(Rezagos)
  }
  lag_nw <- max(1L, min(lag_nw, floor(n / 4)))

  # ── Matriz de varianza-covarianza HAC (Newey-West) ───────────────────────────
  vcov_nw   <- sandwich::NeweyWest(modelo, lag = lag_nw, prewhite = FALSE)
  coeftest_nw <- lmtest::coeftest(modelo, vcov = vcov_nw)

  # ── Tabla de coeficientes robustos ───────────────────────────────────────────
  ct <- as.data.frame(coeftest_nw)
  tabla_coef_robusto <- data.frame(
    Variable    = rownames(ct),
    Coeficiente = round(ct[, 1], 6),
    EE_HAC      = round(ct[, 2], 6),
    t_stat      = round(ct[, 3], 4),
    p_valor     = round(ct[, 4], 6),
    Sig         = ifelse(ct[, 4] < 0.001, "***",
                  ifelse(ct[, 4] < 0.01,  "**",
                  ifelse(ct[, 4] < 0.05,  "*",
                  ifelse(ct[, 4] < 0.10,  ".", "")))),
    stringsAsFactors = FALSE
  )

  # ── Tabla de coeficientes MCO originales para comparación ───────────────────
  sm_ols <- summary(modelo)
  ct_ols <- as.data.frame(sm_ols$coefficients)
  tabla_coef_ols <- data.frame(
    Variable    = rownames(ct_ols),
    Coeficiente = round(ct_ols[, 1], 6),
    EE_OLS      = round(ct_ols[, 2], 6),
    t_stat      = round(ct_ols[, 3], 4),
    p_valor     = round(ct_ols[, 4], 6),
    stringsAsFactors = FALSE
  )

  # ── Nota metodológica ────────────────────────────────────────────────────────
  nota <- paste0(
    "Estimador Newey-West HAC con ", lag_nw, " rezago(s). ",
    "Los coeficientes son idénticos al MCO; solo cambian los errores estándar. ",
    "Significancia: *** p<0.001, ** p<0.01, * p<0.05, . p<0.10. ",
    "Muestra efectiva: ", n, " observaciones."
  )

  return(r_object_to_slots(
    list(
      coeficientes_HAC = tabla_coef_robusto,
      coeficientes_OLS = tabla_coef_ols,
      nota             = nota
    ),
    tier_map = c(coeficientes_HAC = 1L, coeficientes_OLS = 2L, nota = 1L)
  ))
}
