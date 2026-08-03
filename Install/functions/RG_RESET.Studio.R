# ===============================================================================
# NEVEN Data Lab — RESET DE RAMSEY (RG Family)
# Prueba de especificación de forma funcional
# Wooldridge Cap. 9 — Detección de errores de especificación en MCO
# ===============================================================================
# DESCRIPCIÓN:
#   La prueba RESET (Regression Equation Specification Error Test) de Ramsey
#   detecta errores de forma funcional en un modelo de regresión lineal:
#   variables omitidas, transformaciones incorrectas o no-linealidades ignoradas.
#   Si el p-valor es pequeño (< 0.05), el modelo tiene problemas de especificación.
#
# PATRÓN TÉCNICO:
#   - Usa reformulate() — prohibido eval(parse()) por SEC-SEV-006
#   - Requiere: lmtest (ya instalado en NEVEN)
#   - Retorna: r_object_to_slots() con slots tipificados
# ===============================================================================

RG_RESET.Studio <- function(data_Y,
                              data_X,
                              Potencia    = 2L,
                              NivelAlpha  = 0.05) {

  # ── Validaciones de entrada ─────────────────────────────────────────────────
  if (!is.data.frame(data_Y) || nrow(data_Y) == 0)
    stop("'data_Y' debe ser un data.frame con al menos una fila.")
  if (!is.data.frame(data_X) || nrow(data_X) == 0)
    stop("'data_X' debe ser un data.frame con al menos una fila.")
  if (nrow(data_Y) != nrow(data_X))
    stop("'data_Y' y 'data_X' deben tener el mismo número de filas.")

  Potencia   <- as.integer(Potencia)
  NivelAlpha <- as.numeric(NivelAlpha)
  if (is.na(Potencia)   || Potencia < 2L || Potencia > 4L) Potencia   <- 2L
  if (is.na(NivelAlpha) || NivelAlpha <= 0 || NivelAlpha >= 1) NivelAlpha <- 0.05

  # ── Construcción de fórmula con reformulate() (SRS §3.1) ───────────────────
  y_col  <- names(data_Y)[1]
  x_cols <- names(data_X)
  df     <- cbind(data_Y[, y_col, drop = FALSE], data_X)
  df     <- df[complete.cases(df), ]

  fml_base <- reformulate(termlabels = x_cols, response = y_col)

  # ── Paquete lmtest ───────────────────────────────────────────────────────────
  if (!requireNamespace("lmtest", quietly = TRUE))
    stop("El paquete 'lmtest' no está instalado. Use =R.UT_InstalacionWeb() para instalarlo.")

  modelo <- lm(fml_base, data = df)

  # ── Prueba RESET ─────────────────────────────────────────────────────────────
  reset_result <- tryCatch(
    lmtest::resettest(modelo, power = 2:Potencia, type = "fitted"),
    error = function(e) stop(paste("Error en RESET:", conditionMessage(e)))
  )

  # ── Interpretación automática ────────────────────────────────────────────────
  p_val  <- reset_result$p.value
  stat_f <- reset_result$statistic
  df1    <- reset_result$parameter["df1"]
  df2    <- reset_result$parameter["df2"]

  interpretacion <- if (p_val < NivelAlpha) {
    paste0("RECHAZO H0 (p=", round(p_val, 4), " < alpha=", NivelAlpha, "): ",
           "La forma funcional tiene problemas de especificación. ",
           "Considere transformaciones (log, cuadráticos) o variables omitidas.")
  } else {
    paste0("NO SE RECHAZA H0 (p=", round(p_val, 4), " >= alpha=", NivelAlpha, "): ",
           "La forma funcional es adecuada según la prueba RESET.")
  }

  # ── Tabla principal: estadísticos de la prueba ───────────────────────────────
  tabla_reset <- data.frame(
    Estadistico  = c("F", "gl_numerador", "gl_denominador", "p_valor", "alpha", "Decision"),
    Valor        = c(round(stat_f, 4), df1, df2, round(p_val, 6), NivelAlpha,
                     ifelse(p_val < NivelAlpha, "RECHAZAR H0", "No rechazar H0")),
    stringsAsFactors = FALSE
  )

  # ── Tabla secundaria: resumen del modelo base ────────────────────────────────
  sm       <- summary(modelo)
  tabla_lm <- data.frame(
    Estadistico = c("Observaciones", "Variables", "R_cuadrado", "R_cuadrado_ajustado", "F_modelo", "p_modelo"),
    Valor       = c(nrow(df), length(x_cols), round(sm$r.squared, 4),
                    round(sm$adj.r.squared, 4),
                    round(sm$fstatistic[1], 4),
                    round(pf(sm$fstatistic[1], sm$fstatistic[2], sm$fstatistic[3], lower.tail = FALSE), 4)),
    stringsAsFactors = FALSE
  )

  # ── Retorno con r_object_to_slots() ─────────────────────────────────────────
  return(r_object_to_slots(
    list(
      prueba_RESET   = tabla_reset,
      modelo_base    = tabla_lm,
      interpretacion = interpretacion
    ),
    tier_map = c(prueba_RESET = 1L, modelo_base = 1L, interpretacion = 1L)
  ))
}
