# ===============================================================================
# NEVEN Data Lab — J-TEST DAVIDSON-MACKINNON (RG Family)
# Selección entre modelos no anidados
# Wooldridge Cap. 9 — Selección de modelo cuando los modelos compiten
# ===============================================================================
# DESCRIPCIÓN:
#   El J-test de Davidson-MacKinnon (1981) permite elegir entre dos modelos
#   lineales no anidados. El modelo A incluye las variables del modelo B y
#   viceversa. Si solo un modelo resulta significativo, ese es el preferido.
#   Si ambos o ninguno son significativos, el test es inconcluso.
#
#   Aplicación típica: elegir entre especificaciones alternativas de una
#   ecuación salarial, de demanda o de producción.
#
# PATRÓN TÉCNICO:
#   - Dos fórmulas construidas con reformulate() — prohibido eval(parse())
#   - Requiere: lmtest (ya instalado en NEVEN)
#   - Retorna: r_object_to_slots()
# ===============================================================================

RG_Davidson_MacKinnon.Studio <- function(data_Y,
                                          data_X_A,
                                          data_X_B,
                                          NivelAlpha = 0.05) {

  # ── Validaciones ─────────────────────────────────────────────────────────────
  if (!is.data.frame(data_Y) || nrow(data_Y) == 0)
    stop("'data_Y' debe ser un data.frame con al menos una fila.")
  if (!is.data.frame(data_X_A) || nrow(data_X_A) == 0)
    stop("'data_X_A' debe ser un data.frame con al menos una fila.")
  if (!is.data.frame(data_X_B) || nrow(data_X_B) == 0)
    stop("'data_X_B' debe ser un data.frame con al menos una fila.")
  if (nrow(data_Y) != nrow(data_X_A) || nrow(data_Y) != nrow(data_X_B))
    stop("'data_Y', 'data_X_A' y 'data_X_B' deben tener el mismo número de filas.")

  NivelAlpha <- as.numeric(NivelAlpha)
  if (is.na(NivelAlpha) || NivelAlpha <= 0 || NivelAlpha >= 1) NivelAlpha <- 0.05

  y_col    <- names(data_Y)[1]
  xa_cols  <- names(data_X_A)
  xb_cols  <- names(data_X_B)

  df <- cbind(data_Y[, y_col, drop = FALSE], data_X_A, data_X_B)
  df <- df[complete.cases(df), ]

  if (!requireNamespace("lmtest", quietly = TRUE))
    stop("El paquete 'lmtest' no está instalado.")

  # ── Modelos base A y B con reformulate() ────────────────────────────────────
  fml_A <- reformulate(termlabels = xa_cols, response = y_col)
  fml_B <- reformulate(termlabels = xb_cols, response = y_col)

  modelo_A <- lm(fml_A, data = df)
  modelo_B <- lm(fml_B, data = df)

  # ── J-test en ambas direcciones ───────────────────────────────────────────────
  # Dirección A vs B: ¿los fitted de B agregan información al modelo A?
  # Si t-stat es significativo → B aporta algo que A no tiene → A es incompleto
  jtest_AvB <- tryCatch(
    lmtest::jtest(modelo_A, modelo_B),
    error = function(e) stop(paste("Error en J-test A vs B:", conditionMessage(e)))
  )

  # Dirección B vs A
  jtest_BvA <- tryCatch(
    lmtest::jtest(modelo_B, modelo_A),
    error = function(e) stop(paste("Error en J-test B vs A:", conditionMessage(e)))
  )

  # ── Extracción de resultados ─────────────────────────────────────────────────
  # jtest retorna una tabla con 2 filas: [1] = modelo original, [2] = con fitted rival
  p_AvB <- jtest_AvB[2, "Pr(>|t|)"]
  p_BvA <- jtest_BvA[2, "Pr(>|t|)"]
  t_AvB <- jtest_AvB[2, "t"]
  t_BvA <- jtest_BvA[2, "t"]

  sig_AvB <- p_AvB < NivelAlpha
  sig_BvA <- p_BvA < NivelAlpha

  decision <- if (sig_AvB && !sig_BvA) {
    "Preferir MODELO B: los fitted de B son significativos en A, pero no al revés."
  } else if (!sig_AvB && sig_BvA) {
    "Preferir MODELO A: los fitted de A son significativos en B, pero no al revés."
  } else if (sig_AvB && sig_BvA) {
    "TEST INCONCLUSO: ambos modelos son significativos. Ninguno domina al otro."
  } else {
    "TEST INCONCLUSO: ningún modelo es significativo. Ambos son igualmente (in)adecuados."
  }

  # ── Tabla resumen del J-test ──────────────────────────────────────────────────
  tabla_jtest <- data.frame(
    Direccion   = c("A vs B (¿B aporta sobre A?)", "B vs A (¿A aporta sobre B?)"),
    t_stat      = round(c(t_AvB, t_BvA), 4),
    p_valor     = round(c(p_AvB, p_BvA), 6),
    Significativo = c(
      ifelse(sig_AvB, paste0("Sí (p<", NivelAlpha, ")"), paste0("No (p>=", NivelAlpha, ")")),
      ifelse(sig_BvA, paste0("Sí (p<", NivelAlpha, ")"), paste0("No (p>=", NivelAlpha, ")"))
    ),
    stringsAsFactors = FALSE
  )

  # ── Tabla comparativa de modelos ────────────────────────────────────────────
  sm_A <- summary(modelo_A)
  sm_B <- summary(modelo_B)

  tabla_comparativa <- data.frame(
    Estadistico       = c("Observaciones", "Variables", "R_cuadrado", "R_cuadrado_ajust", "AIC", "BIC"),
    Modelo_A          = c(nrow(df), length(xa_cols),
                          round(sm_A$r.squared, 4), round(sm_A$adj.r.squared, 4),
                          round(AIC(modelo_A), 2),  round(BIC(modelo_A), 2)),
    Modelo_B          = c(nrow(df), length(xb_cols),
                          round(sm_B$r.squared, 4), round(sm_B$adj.r.squared, 4),
                          round(AIC(modelo_B), 2),  round(BIC(modelo_B), 2)),
    stringsAsFactors = FALSE
  )

  return(r_object_to_slots(
    list(
      jtest_resultados   = tabla_jtest,
      comparativa_modelos = tabla_comparativa,
      decision            = decision
    ),
    tier_map = c(jtest_resultados = 1L, comparativa_modelos = 1L, decision = 1L)
  ))
}
