# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio para Regresion de Poisson
# Requiere: r_object_to_slots.R cargado en el entorno global
# ═══════════════════════════════════════════════════════════════════════════════

RG_Poisson.Studio <- function(data_Y,
                                data_X,
                                Escala    = FALSE,
                                Constante = TRUE) {

  if (!is.data.frame(data_Y) && !is.matrix(data_Y)) stop("'data_Y' debe ser un data.frame.")
  if (!is.data.frame(data_X) && !is.matrix(data_X)) stop("'data_X' debe ser un data.frame.")
  data_Y <- as.data.frame(data_Y)
  data_X <- as.data.frame(data_X)

  y_col  <- names(data_Y)[1]
  num_X  <- sapply(data_X, is.numeric)
  x_cols <- names(data_X)[num_X]
  if (!any(num_X)) stop("data_X debe tener al menos una columna numerica.")
  if (nrow(data_Y) != nrow(data_X)) stop("data_Y y data_X deben tener el mismo numero de filas.")

  y_vec <- as.numeric(data_Y[[y_col]])
  if (any(y_vec < 0, na.rm = TRUE)) stop("data_Y debe contener valores no negativos (conteos).")

  if (isTRUE(Escala)) data_X[, x_cols] <- scale(data_X[, x_cols, drop = FALSE])

  df_model    <- cbind(data_Y[y_col], data_X[x_cols])
  formula_str <- paste(y_col, "~", paste(x_cols, collapse = " + "))
  if (!isTRUE(Constante)) formula_str <- paste(y_col, "~ 0 +", paste(x_cols, collapse = " + "))

  mod <- glm(as.formula(formula_str), data = df_model, family = poisson(link = "log"))
  s   <- summary(mod)

  # Coeficientes con IRR (Incidence Rate Ratio)
  coef_mat <- as.data.frame(s$coefficients)
  coef_mat <- cbind(Variable = rownames(coef_mat), coef_mat)
  colnames(coef_mat) <- c("Variable", "Estimado", "Error_Std", "z_value", "p_value")
  rownames(coef_mat) <- NULL
  coef_mat$IRR <- round(exp(as.numeric(coef_mat$Estimado)), 4)
  coef_mat[, 2:5] <- lapply(coef_mat[, 2:5], function(x) round(as.numeric(x), 4))

  # Prueba de sobredispersion
  pred_vals <- fitted(mod)
  pearson   <- sum((y_vec - pred_vals)^2 / pred_vals, na.rm = TRUE)
  dispersion <- round(pearson / mod$df.residual, 4)

  metricas <- data.frame(
    Metrica = c("AIC", "BIC", "Deviance_Nula", "Deviance_Residual",
                "Dispersion", "N"),
    Valor   = c(round(AIC(mod), 4), round(BIC(mod), 4),
                round(mod$null.deviance, 4), round(mod$deviance, 4),
                dispersion, nrow(df_model)),
    stringsAsFactors = FALSE
  )
  if (dispersion > 1.5) {
    metricas <- rbind(metricas, data.frame(
      Metrica = "Alerta",
      Valor   = "Posible sobredispersion (dispersion > 1.5): considere Binomial Negativa",
      stringsAsFactors = FALSE
    ))
  }

  # Observado vs predicho
  n_show  <- min(50L, nrow(df_model))
  pred_df <- data.frame(
    ID         = seq_len(n_show),
    Observado  = round(y_vec[1:n_show], 0),
    Prediccion = round(pred_vals[1:n_show], 2),
    stringsAsFactors = FALSE
  )

  # Grafico
  html_graf <- tryCatch({
    ord  <- order(pred_vals)
    px   <- round(pred_vals[ord], 4)
    py   <- y_vec[ord]
    traces <- list(
      list(type = "scatter", mode = "markers",
           x = seq_along(py), y = py,
           marker = list(size = 5, color = "#888", opacity = 0.6),
           name = "Observado", hoverinfo = "none"),
      list(type = "scatter", mode = "lines",
           x = seq_along(px), y = px,
           line = list(color = "#d7a538", width = 2),
           name = "Predicho", hoverinfo = "none")
    )
    layout <- list(
      title = list(text = "Conteos Observados vs Predichos (Poisson)",
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = "Observaciones (ordenadas)", color = "#888", gridcolor = "#333"),
      yaxis = list(title = "Conteo", color = "#888", gridcolor = "#333"),
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

  # Stargazer
  html_stargazer <- tryCatch({
    if (!requireNamespace("stargazer", quietly = TRUE)) stop("stargazer requerido")
    raw_lines <- capture.output(
      stargazer::stargazer(mod, type = "html",
                           title = "Regresion de Poisson",
                           dep.var.labels = y_col,
                           covariate.labels = x_cols,
                           out = NULL)
    )
    style <- paste0(
      "<style>",
      "body{background:#373434;color:#e0e0e0;font-family:'Segoe UI',sans-serif;font-size:12px;padding:8px}",
      "table{border-collapse:collapse;width:100%}",
      "td,th{padding:4px 8px;border-bottom:1px solid #555}",
      "td:first-child{text-align:left}",
      "td:not(:first-child){text-align:center}",
      "p{color:#888;font-size:10px}",
      "</style>"
    )
    html_body <- paste(raw_lines, collapse = "\n")
    iconv(paste0("<html><head>", style, "</head><body>", html_body, "</body></html>"),
          from = "UTF-8", to = "UTF-8", sub = "byte")
  }, error = function(e) {
    paste0("<html><body><p style='color:#888;padding:8px'>Stargazer no disponible</p></body></html>")
  })

  resultado <- list(
    tabla_cientifica = html_stargazer,
    coeficientes     = coef_mat,
    metricas         = metricas,
    predicciones     = pred_df,
    grafico          = html_graf
  )
  tier_map <- c(tabla_cientifica = 1L, coeficientes = 2L,
                metricas = 1L, predicciones = 2L, grafico = 1L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
