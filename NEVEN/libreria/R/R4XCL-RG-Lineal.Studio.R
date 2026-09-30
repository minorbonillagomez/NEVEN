# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio para Regresion Lineal
# Requiere: r_object_to_slots.R cargado en el entorno global
# ═══════════════════════════════════════════════════════════════════════════════

RG_Lineal.Studio <- function(data_Y,
                               data_X,
                               Escala    = FALSE,
                               Constante = TRUE) {

  if (!is.data.frame(data_Y) && !is.matrix(data_Y)) stop("'data_Y' debe ser un data.frame.")
  if (!is.data.frame(data_X) && !is.matrix(data_X)) stop("'data_X' debe ser un data.frame.")
  data_Y <- as.data.frame(data_Y)
  data_X <- as.data.frame(data_X)

  num_Y <- sapply(data_Y, is.numeric)
  num_X <- sapply(data_X, is.numeric)
  if (!any(num_Y)) stop("data_Y debe tener al menos una columna numerica.")
  if (!any(num_X)) stop("data_X debe tener al menos una columna numerica.")

  y_col <- names(data_Y)[which(num_Y)[1]]
  x_cols <- names(data_X)[num_X]

  if (nrow(data_Y) != nrow(data_X)) stop("data_Y y data_X deben tener el mismo numero de filas.")
  if (nrow(data_Y) < length(x_cols) + 2L) stop("Observaciones insuficientes para el modelo.")

  if (isTRUE(Escala)) {
    data_X[, x_cols] <- scale(data_X[, x_cols, drop = FALSE])
  }

  y_vec <- data_Y[[y_col]]
  formula_str <- if (isTRUE(Constante)) {
    paste(y_col, "~", paste(x_cols, collapse = " + "))
  } else {
    paste(y_col, "~ 0 +", paste(x_cols, collapse = " + "))
  }

  df_model <- cbind(data_Y[y_col], data_X[x_cols])
  mod <- lm(as.formula(formula_str), data = df_model)
  s   <- summary(mod)

  # Coeficientes
  coef_mat <- as.data.frame(s$coefficients)
  coef_mat <- cbind(Variable = rownames(coef_mat), coef_mat)
  colnames(coef_mat) <- c("Variable", "Estimado", "Error_Std", "t_value", "p_value")
  rownames(coef_mat) <- NULL
  coef_mat[, 2:5] <- lapply(coef_mat[, 2:5], function(x) round(as.numeric(x), 4))

  # Metricas globales
  metricas <- data.frame(
    Metrica = c("R_cuadrado", "R_cuad_ajustado", "F_estadistico", "p_value_F",
                "RSE", "AIC", "BIC", "N", "K"),
    Valor   = c(
      round(s$r.squared, 4),
      round(s$adj.r.squared, 4),
      round(s$fstatistic[1], 4),
      round(pf(s$fstatistic[1], s$fstatistic[2], s$fstatistic[3], lower.tail = FALSE), 4),
      round(s$sigma, 4),
      round(AIC(mod), 4),
      round(BIC(mod), 4),
      nrow(df_model),
      length(x_cols)
    ),
    stringsAsFactors = FALSE
  )

  # Fitted vs residuos (primeras 50 obs)
  n_show <- min(50L, nrow(df_model))
  fitted_df <- data.frame(
    ID       = seq_len(n_show),
    Observado = round(y_vec[1:n_show], 4),
    Ajustado  = round(fitted(mod)[1:n_show], 4),
    Residuo   = round(residuals(mod)[1:n_show], 4),
    stringsAsFactors = FALSE
  )

  # Grafico residuos vs ajustados
  html_residuos <- tryCatch({
    cp1  <- round(fitted(mod), 4)
    cp2  <- round(residuals(mod), 4)
    traces <- list(list(
      type = "scatter", mode = "markers",
      x = cp1, y = cp2,
      marker = list(size = 6, color = "#d7a538", opacity = 0.7),
      hovertext = paste0("Ajust: ", cp1, " | Resid: ", cp2),
      hoverinfo = "text", showlegend = FALSE
    ), list(
      type = "scatter", mode = "lines",
      x = range(cp1), y = c(0, 0),
      line = list(color = "rgba(215,165,56,0.4)", width = 1, dash = "dash"),
      showlegend = FALSE, hoverinfo = "none"
    ))
    layout <- list(
      title = list(text = "Residuos vs Valores Ajustados",
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = "Valores ajustados", color = "#888",
                   gridcolor = "#333", zerolinecolor = "#555"),
      yaxis = list(title = "Residuos", color = "#888",
                   gridcolor = "#333", zeroline = TRUE, zerolinecolor = "#555"),
      paper_bgcolor = "#373434", plot_bgcolor = "#373434",
      font = list(color = "#888"), margin = list(t = 50, r = 20, b = 50, l = 60)
    )
    fig_json <- iconv(jsonlite::toJSON(list(data = traces, layout = layout),
                                        auto_unbox = TRUE, na = "null"),
                      from = "UTF-8", to = "UTF-8", sub = "byte")
    paste0('<html><body><neven-plotly>',
           jsonlite::base64_enc(chartr("\n\r", "  ", fig_json)),
           '</neven-plotly></body></html>')
  }, error = function(e) {
    paste0('<html><body><p style="color:#888;padding:8px">Grafico no disponible</p></body></html>')
  })

  # Tabla científica — texto plano estilo consola R (sin stargazer, sin encoding issues)
  tabla_cientifica_txt <- tryCatch({
    paste(capture.output(print(summary(mod))), collapse = "\n")
  }, error = function(e) {
    paste("Error al generar resumen del modelo:", conditionMessage(e))
  })

  # ── Diagnósticos para advertencias pedagógicas ──────────────────────────────
  # Cada advertencia es un slot de tipo "warning_pedagogy".
  # El servidor Python lo enriquece con el contenido del Knowledge Graph.
  # El slot lleva el assumption_id y el contexto numérico del test.

  warnings_list <- list()

  # 1. Test de Breusch-Pagan (heterocedasticidad)
  bp_warning <- tryCatch({
    if (requireNamespace("lmtest", quietly = TRUE)) {
      bp <- lmtest::bptest(mod)
      bp_pval <- as.numeric(bp$p.value)
      bp_stat <- as.numeric(bp$statistic)
      if (!is.na(bp_pval) && bp_pval < 0.05) {
        # Heterocedasticidad detectada — emitir advertencia
        ctx <- list(
          assumption_id      = "assumption_homoscedasticity",
          test_statistic     = round(bp_stat, 4),
          p_value            = round(bp_pval, 6),
          threshold          = 0.05,
          variable_name      = "los residuos del modelo",
          correction_applied = "HC1"
        )
        list(
          name  = "warning_heterocedasticidad",
          label = "\u26a0 Heterocedasticidad detectada",
          type  = "warning_pedagogy",
          value = jsonlite::toJSON(ctx, auto_unbox = TRUE),
          tier  = 1L
        )
      } else NULL
    } else NULL
  }, error = function(e) NULL)
  if (!is.null(bp_warning)) warnings_list <- c(warnings_list, list(bp_warning))

  # 2. Test de VIF (multicolinealidad) — solo cuando hay 2+ regresores
  vif_warning <- tryCatch({
    if (length(x_cols) >= 2 && requireNamespace("car", quietly = TRUE)) {
      vif_vals <- car::vif(mod)
      max_vif  <- max(vif_vals, na.rm = TRUE)
      if (!is.na(max_vif) && max_vif > 5) {
        ctx <- list(
          assumption_id      = "assumption_no_multicollinearity",
          test_statistic     = round(max_vif, 4),
          p_value            = NULL,
          threshold          = 5,
          variable_name      = names(which.max(vif_vals)),
          correction_applied = ""
        )
        list(
          name  = "warning_multicolinealidad",
          label = "\u26a0 Multicolinealidad elevada",
          type  = "warning_pedagogy",
          value = jsonlite::toJSON(ctx, auto_unbox = TRUE, null = "null"),
          tier  = 1L
        )
      } else NULL
    } else NULL
  }, error = function(e) NULL)
  if (!is.null(vif_warning)) warnings_list <- c(warnings_list, list(vif_warning))

  # ── Construir resultado final con advertencias al frente (tier 1) ────────────
  resultado <- list(
    tabla_cientifica = tabla_cientifica_txt,
    coeficientes     = coef_mat,
    metricas         = local({
      m <- metricas; vals <- as.character(m[[2]]); keys <- as.character(m[[1]])
      w_k <- max(nchar(keys)); w_v <- max(nchar(vals))
      paste(c(paste0(formatC("Metrica",width=-w_k),"  ",formatC("Valor",width=w_v)),
              strrep("-",w_k+w_v+2),
              mapply(function(k,v) paste0(formatC(k,width=-w_k),"  ",formatC(v,width=w_v)),keys,vals)),
            collapse="\n")
    }),
    residuos         = fitted_df,
    grafico          = html_residuos
  )
  tier_map <- c(tabla_cientifica = 1L, coeficientes = 2L,
                metricas = 1L, residuos = 2L, grafico = 1L)
  slots_df <- r_object_to_slots(resultado, tier_map = tier_map)

  # Convertir advertencias a data.frame y prepender (aparecen antes de los resultados)
  if (length(warnings_list) > 0) {
    warn_df <- do.call(rbind, lapply(warnings_list, function(w) {
      as.data.frame(w, stringsAsFactors = FALSE)
    }))
    slots_df <- rbind(warn_df, slots_df)
  }

  return(slots_df)
}
