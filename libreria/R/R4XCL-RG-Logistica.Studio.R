# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio para Regresion Logistica
# Requiere: r_object_to_slots.R cargado en el entorno global
# ═══════════════════════════════════════════════════════════════════════════════

RG_Logistica.Studio <- function(data_Y,
                                  data_X,
                                  TipoModelo = 1L,
                                  Escala     = FALSE) {

  if (!is.data.frame(data_Y) && !is.matrix(data_Y)) stop("'data_Y' debe ser un data.frame.")
  if (!is.data.frame(data_X) && !is.matrix(data_X)) stop("'data_X' debe ser un data.frame.")
  data_Y <- as.data.frame(data_Y)
  data_X <- as.data.frame(data_X)
  TipoModelo <- as.integer(TipoModelo)

  links <- c("logit", "probit")
  if (TipoModelo < 1L || TipoModelo > 2L) stop("TipoModelo: 1=Logit, 2=Probit.")

  num_X <- sapply(data_X, is.numeric)
  if (!any(num_X)) stop("data_X debe tener al menos una columna numerica.")
  y_col  <- names(data_Y)[1]
  x_cols <- names(data_X)[num_X]
  if (nrow(data_Y) != nrow(data_X)) stop("data_Y y data_X deben tener el mismo numero de filas.")

  y_vec <- data_Y[[y_col]]
  vals  <- unique(y_vec[!is.na(y_vec)])
  if (!all(vals %in% c(0L, 1L, 0.0, 1.0))) {
    stop(paste0("data_Y debe contener UNICAMENTE valores 0 y 1. ",
                "Se encontraron: ", paste(sort(unique(vals)), collapse=", ")))
  }
  y_vec <- as.integer(y_vec)

  if (isTRUE(Escala)) data_X[, x_cols] <- scale(data_X[, x_cols, drop = FALSE])

  df_model <- cbind(data_Y[y_col], data_X[x_cols])
  formula_str <- paste(y_col, "~", paste(x_cols, collapse = " + "))
  mod <- glm(as.formula(formula_str), data = df_model,
             family = binomial(link = links[TipoModelo]))
  s   <- summary(mod)

  # Coeficientes con odds-ratio
  coef_mat <- as.data.frame(s$coefficients)
  coef_mat <- cbind(Variable = rownames(coef_mat), coef_mat)
  colnames(coef_mat) <- c("Variable", "Estimado", "Error_Std", "z_value", "p_value")
  rownames(coef_mat) <- NULL
  coef_mat$Odds_Ratio <- round(exp(as.numeric(coef_mat$Estimado)), 4)
  coef_mat[, 2:5] <- lapply(coef_mat[, 2:5], function(x) round(as.numeric(x), 4))

  # Metricas
  prob_pred <- fitted(mod)
  pred_bin  <- as.integer(prob_pred >= 0.5)
  accuracy  <- round(mean(pred_bin == y_vec, na.rm = TRUE) * 100, 2)
  null_dev  <- round(mod$null.deviance, 4)
  res_dev   <- round(mod$deviance, 4)
  mcfadden  <- round(1 - res_dev / null_dev, 4)

  metricas <- data.frame(
    Metrica = c("AIC", "BIC", "Deviance_Nula", "Deviance_Residual",
                "McFadden_R2", "Exactitud_Pct", "N"),
    Valor   = c(round(AIC(mod), 4), round(BIC(mod), 4),
                null_dev, res_dev, mcfadden, accuracy, nrow(df_model)),
    stringsAsFactors = FALSE
  )

  # Tabla de clasificacion
  n_show <- min(50L, nrow(df_model))
  pred_df <- data.frame(
    ID          = seq_len(n_show),
    Observado   = y_vec[1:n_show],
    Probabilidad = round(prob_pred[1:n_show], 4),
    Prediccion  = pred_bin[1:n_show],
    stringsAsFactors = FALSE
  )

  # Grafico probabilidades predichas
  html_prob <- tryCatch({
    ord  <- order(prob_pred)
    px   <- round(prob_pred[ord], 4)
    py   <- y_vec[ord]
    traces <- list(
      list(type = "scatter", mode = "markers",
           x = seq_along(px), y = py,
           marker = list(size = 5, color = "#888", opacity = 0.5),
           name = "Observado", hoverinfo = "none"),
      list(type = "scatter", mode = "lines",
           x = seq_along(px), y = px,
           line = list(color = "#d7a538", width = 2),
           name = "P(Y=1)", hoverinfo = "none")
    )
    layout <- list(
      title = list(text = "Probabilidades Predichas vs Observado",
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = "Observaciones (ordenadas)", color = "#888",
                   gridcolor = "#333", zerolinecolor = "#555"),
      yaxis = list(title = "Probabilidad", range = c(-0.05, 1.05),
                   color = "#888", gridcolor = "#333"),
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

  # Stargazer: tabla cientifica HTML
  html_stargazer <- tryCatch({
    if (!requireNamespace("stargazer", quietly = TRUE)) stop("stargazer requerido")
    raw_lines <- capture.output(
      stargazer::stargazer(mod, type = "html",
                           title   = paste0("Regresion ", toupper(links[TipoModelo])),
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
    full_html <- paste0("<html><head>", style, "</head><body>", html_body, "</body></html>")
    iconv(full_html, from = "UTF-8", to = "UTF-8", sub = "byte")
  }, error = function(e) {
    paste0("<html><body><p style='color:#888;padding:8px'>Tabla Stargazer no disponible: ",
           conditionMessage(e), "</p></body></html>")
  })

  resultado <- list(
    tabla_cientifica = html_stargazer,
    coeficientes     = coef_mat,
    metricas         = metricas,
    predicciones     = pred_df,
    grafico          = html_prob
  )
  tier_map <- c(tabla_cientifica = 1L, coeficientes = 2L,
                metricas = 1L, predicciones = 2L, grafico = 1L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
