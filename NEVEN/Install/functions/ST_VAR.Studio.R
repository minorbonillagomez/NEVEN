# ===============================================================================
# NEVEN Data Lab — VECTORES AUTORREGRESIVOS (VAR) (ST Family)
# Análisis dinámico de sistemas de series de tiempo
# Wooldridge Cap. 18 / Lütkepohl (2005)
# ===============================================================================
# DESCRIPCIÓN:
#   Un modelo VAR(p) modela cada variable como función de sus propios rezagos
#   y los rezagos de todas las demás variables del sistema. No impone restricciones
#   de exogeneidad — todas las variables son endógenas.
#
#   Usos típicos:
#   - Pronóstico de sistemas macroeconómicos (PIB, inflación, tipo de cambio)
#   - Funciones de impulso-respuesta: ¿cómo responde Y a un shock en X?
#   - Descomposición de varianza del error de pronóstico (FEVD)
#
#   Selección del orden p: se prueba AIC, BIC, HQ y FPE
#
# PAQUETE: vars (Pfaff 2008)
# ===============================================================================

ST_VAR.Studio <- function(data_Series,
                            MaxRezagos    = 8L,
                            CriterioSel   = 1L,
                            TipoConst     = 1L,
                            HorizontePron = 4L) {

  # ── Validaciones ─────────────────────────────────────────────────────────────
  if (!is.data.frame(data_Series) || nrow(data_Series) == 0)
    stop("'data_Series' debe ser un data.frame con las series de tiempo como columnas.")
  if (ncol(data_Series) < 2)
    stop("VAR requiere al menos 2 series. Para una sola serie, use ST_SeriesTiempo.")

  MaxRezagos    <- as.integer(MaxRezagos);    if (is.na(MaxRezagos) || MaxRezagos < 1) MaxRezagos <- 8L
  CriterioSel   <- as.integer(CriterioSel);  if (is.na(CriterioSel) || CriterioSel < 1 || CriterioSel > 4) CriterioSel <- 1L
  TipoConst     <- as.integer(TipoConst);    if (is.na(TipoConst) || TipoConst < 1 || TipoConst > 3) TipoConst <- 1L
  HorizontePron <- as.integer(HorizontePron); if (is.na(HorizontePron) || HorizontePron < 1) HorizontePron <- 4L

  if (!requireNamespace("vars", quietly = TRUE))
    stop("El paquete 'vars' no está instalado. Use =R.UT_InstalacionWeb() para instalarlo.")

  df <- data_Series[complete.cases(data_Series), ]
  n  <- nrow(df)
  k  <- ncol(df)
  series_names <- names(df)

  # Convertir a matriz numérica
  mat <- as.matrix(df)
  if (!is.numeric(mat)) stop("Todas las columnas deben ser numéricas.")

  # ── Tipo de constante ─────────────────────────────────────────────────────────
  tipo_str <- switch(TipoConst,
    "1" = "const",     # VAR con constante (estándar)
    "2" = "trend",     # VAR con tendencia
    "3" = "both",      # constante + tendencia
    "const"
  )

  # ── Criterio de selección de rezagos ─────────────────────────────────────────
  criterio_str <- switch(CriterioSel,
    "1" = "AIC(n)",
    "2" = "SC(n)",    # BIC
    "3" = "HQ(n)",    # Hannan-Quinn
    "4" = "FPE",
    "AIC(n)"
  )

  # ── Selección del orden óptimo ────────────────────────────────────────────────
  sel_result <- tryCatch(
    vars::VARselect(mat, lag.max = min(MaxRezagos, floor(n / (k + 1))),
                    type = tipo_str),
    error = function(e) stop(paste("Error en VARselect:", conditionMessage(e)))
  )

  p_optimo <- sel_result$selection[[criterio_str]]

  # ── Estimación VAR(p) ─────────────────────────────────────────────────────────
  modelo_var <- tryCatch(
    vars::VAR(mat, p = p_optimo, type = tipo_str),
    error = function(e) stop(paste("Error en VAR:", conditionMessage(e)))
  )

  # ── Tabla de criterios de información por número de rezagos ─────────────────
  crit_df <- as.data.frame(t(sel_result$criteria))
  colnames(crit_df) <- c("AIC", "BIC_SC", "HQ", "FPE")
  crit_df$Rezagos   <- seq_len(nrow(crit_df))
  crit_df$Optimo    <- crit_df$Rezagos == p_optimo

  tabla_criterios <- crit_df[, c("Rezagos", "AIC", "BIC_SC", "HQ", "FPE", "Optimo")]
  tabla_criterios <- lapply(tabla_criterios, function(x) if (is.numeric(x)) round(x, 4) else x)
  tabla_criterios <- as.data.frame(tabla_criterios, stringsAsFactors = FALSE)

  # ── Tabla de coeficientes por ecuación ───────────────────────────────────────
  coef_list <- lapply(series_names, function(nm) {
    eq   <- modelo_var$varresult[[nm]]
    ct   <- summary(eq)$coefficients
    data.frame(
      Ecuacion    = nm,
      Regresor    = rownames(ct),
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
  })
  tabla_coef <- do.call(rbind, coef_list)

  # ── Pronóstico ───────────────────────────────────────────────────────────────
  pron <- tryCatch({
    pred <- predict(modelo_var, n.ahead = HorizontePron, ci = 0.95)
    pron_list <- lapply(series_names, function(nm) {
      p    <- pred$fcst[[nm]]
      data.frame(
        Serie     = nm,
        Horizonte = seq_len(HorizontePron),
        Pron      = round(p[, "fcst"], 4),
        LI_95     = round(p[, "lower"], 4),
        LS_95     = round(p[, "upper"], 4),
        stringsAsFactors = FALSE
      )
    })
    do.call(rbind, pron_list)
  }, error = function(e) {
    data.frame(Serie = "Error", Horizonte = NA, Pron = NA, LI_95 = NA, LS_95 = NA,
               stringsAsFactors = FALSE)
  })

  # ── Resumen del modelo ────────────────────────────────────────────────────────
  tabla_resumen <- data.frame(
    Estadistico = c("Observaciones", "Series_k", "Rezagos_p",
                    "Tipo_constante", "Criterio_seleccion", "Parametros_totales"),
    Valor       = c(n, k, p_optimo, tipo_str, criterio_str,
                    p_optimo * k^2 + k * (TipoConst > 0)),
    stringsAsFactors = FALSE
  )

  return(r_object_to_slots(
    list(
      resumen_VAR        = tabla_resumen,
      criterios_rezagos  = tabla_criterios,
      coeficientes       = tabla_coef,
      pronostico         = pron
    ),
    tier_map = c(resumen_VAR = 1L, criterios_rezagos = 1L,
                 coeficientes = 2L, pronostico = 1L)
  ))
}
