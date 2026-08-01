# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio para Arbol de Decision
# Requiere: r_object_to_slots.R cargado en el entorno global
# ═══════════════════════════════════════════════════════════════════════════════

RG_ArbolDecision.Studio <- function(data_Y,
                                      data_X,
                                      TipoModelo = 1L,
                                      MaxProf    = 5L,
                                      MinObs     = 10L) {

  if (!is.data.frame(data_Y) && !is.matrix(data_Y)) stop("'data_Y' debe ser un data.frame.")
  if (!is.data.frame(data_X) && !is.matrix(data_X)) stop("'data_X' debe ser un data.frame.")
  data_Y <- as.data.frame(data_Y)
  data_X <- as.data.frame(data_X)
  TipoModelo <- as.integer(TipoModelo)
  MaxProf    <- as.integer(MaxProf)
  MinObs     <- as.integer(MinObs)

  if (TipoModelo < 1L || TipoModelo > 2L) stop("TipoModelo: 1=Clasificacion, 2=Regresion.")
  if (nrow(data_Y) != nrow(data_X)) stop("data_Y y data_X deben tener el mismo numero de filas.")
  if (nrow(data_Y) < MinObs * 2L) stop("Observaciones insuficientes.")

  if (!requireNamespace("rpart", quietly = TRUE)) stop("Paquete 'rpart' requerido.")

  y_col  <- names(data_Y)[1]
  x_cols <- names(data_X)
  y_vec  <- data_Y[[y_col]]

  is_classif <- TipoModelo == 1L
  if (is_classif) y_vec <- as.factor(y_vec)

  df_model    <- cbind(data_Y[y_col], data_X[x_cols])
  formula_str <- paste(y_col, "~", paste(x_cols, collapse = " + "))
  method_str  <- if (is_classif) "class" else "anova"

  ctrl <- rpart::rpart.control(maxdepth = MaxProf, minsplit = MinObs)
  mod  <- rpart::rpart(as.formula(formula_str), data = df_model,
                       method = method_str, control = ctrl)

  # Importancia de variables
  if (!is.null(mod$variable.importance) && length(mod$variable.importance) > 0) {
    imp <- mod$variable.importance / sum(mod$variable.importance) * 100
    importancia_df <- data.frame(
      Variable   = names(imp),
      Importancia_Pct = round(imp, 2),
      stringsAsFactors = FALSE
    )
    importancia_df <- importancia_df[order(-importancia_df$Importancia_Pct), ]
    rownames(importancia_df) <- NULL
  } else {
    importancia_df <- data.frame(Variable = x_cols, Importancia_Pct = NA_real_,
                                  stringsAsFactors = FALSE)
  }

  # Reglas del arbol (texto)
  reglas_txt <- paste(capture.output(print(mod)), collapse = "\n")
  if (nchar(reglas_txt) > 2000) reglas_txt <- substr(reglas_txt, 1, 2000)

  # Metricas
  if (is_classif) {
    pred    <- predict(mod, type = "class")
    acc     <- round(mean(pred == y_vec, na.rm = TRUE) * 100, 2)
    n_nodos <- nrow(mod$frame)
    metricas <- data.frame(
      Metrica = c("Exactitud_Pct", "N_nodos", "N_hojas", "Profundidad_max", "N"),
      Valor   = c(acc,
                  n_nodos,
                  sum(mod$frame$var == "<leaf>"),
                  MaxProf,
                  nrow(df_model)),
      stringsAsFactors = FALSE
    )
  } else {
    pred    <- predict(mod)
    rmse    <- round(sqrt(mean((as.numeric(y_vec) - pred)^2, na.rm = TRUE)), 4)
    r2      <- round(1 - sum((as.numeric(y_vec) - pred)^2) /
                         sum((as.numeric(y_vec) - mean(as.numeric(y_vec)))^2), 4)
    metricas <- data.frame(
      Metrica = c("RMSE", "R_cuadrado", "N_nodos", "N_hojas", "N"),
      Valor   = c(rmse, r2, nrow(mod$frame),
                  sum(mod$frame$var == "<leaf>"), nrow(df_model)),
      stringsAsFactors = FALSE
    )
  }

  # Grafico importancia
  html_imp <- tryCatch({
    if (all(is.na(importancia_df$Importancia_Pct))) stop("Sin importancia")
    ord  <- order(importancia_df$Importancia_Pct)
    vars <- importancia_df$Variable[ord]
    vals <- importancia_df$Importancia_Pct[ord]
    traces <- list(list(
      type = "bar", orientation = "h",
      x = vals, y = vars,
      marker = list(color = "#d7a538"),
      hovertemplate = "%{y}: %{x:.2f}%<extra></extra>"
    ))
    layout <- list(
      title = list(text = "Importancia de Variables (%)",
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = "Importancia (%)", color = "#888", gridcolor = "#333"),
      yaxis = list(color = "#888", automargin = TRUE),
      paper_bgcolor = "#373434", plot_bgcolor = "#373434",
      font = list(color = "#888"), margin = list(t = 50, r = 20, b = 50, l = 120)
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

  resultado <- list(
    importancia = importancia_df,
    metricas    = metricas,
    grafico_imp = html_imp,
    reglas      = reglas_txt
  )
  tier_map <- c(importancia = 1L, metricas = 1L, grafico_imp = 1L, reglas = 2L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
