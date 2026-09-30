# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio para Maquinas de Soporte Vectorial
# Requiere: r_object_to_slots.R cargado en el entorno global
# ═══════════════════════════════════════════════════════════════════════════════

RG_SVM.Studio <- function(data_Y,
                            data_X,
                            TipoModelo = 1L,
                            Kernel     = 1L,
                            Escala     = TRUE,
                            Costo      = 1.0) {

  if (!is.data.frame(data_Y) && !is.matrix(data_Y)) stop("'data_Y' debe ser un data.frame.")
  if (!is.data.frame(data_X) && !is.matrix(data_X)) stop("'data_X' debe ser un data.frame.")
  if (!requireNamespace("e1071", quietly = TRUE)) stop("Paquete 'e1071' requerido.")

  data_Y <- as.data.frame(data_Y)
  data_X <- as.data.frame(data_X)
  TipoModelo <- as.integer(TipoModelo)
  Kernel     <- as.integer(Kernel)
  Costo      <- as.numeric(Costo)

  if (TipoModelo < 1L || TipoModelo > 2L) stop("TipoModelo: 1=Clasificacion, 2=Regresion.")
  if (Kernel < 1L || Kernel > 4L) stop("Kernel: 1=Lineal, 2=Polinomial, 3=RBF, 4=Sigmoide.")
  if (nrow(data_Y) != nrow(data_X)) stop("data_Y y data_X deben tener el mismo numero de filas.")

  kernels  <- c("linear", "polynomial", "radial", "sigmoid")
  y_col    <- names(data_Y)[1]
  x_cols   <- names(data_X)
  y_raw    <- data_Y[[y_col]]
  is_classif <- TipoModelo == 1L

  if (is_classif) y_raw <- as.factor(y_raw)

  df_model    <- cbind(data_Y[y_col], data_X[x_cols])
  formula_str <- paste(y_col, "~", paste(x_cols, collapse = " + "))

  mod  <- e1071::svm(as.formula(formula_str), data = df_model,
                     kernel = kernels[Kernel], cost = Costo,
                     scale = isTRUE(Escala), probability = is_classif)

  pred <- predict(mod, df_model)

  if (is_classif) {
    cm  <- table(Observado = y_raw, Predicho = pred)
    acc <- round(mean(pred == y_raw, na.rm = TRUE) * 100, 2)
    cm_df <- as.data.frame.matrix(cm)
    cm_df <- cbind(Observado = rownames(cm_df), cm_df)
    rownames(cm_df) <- NULL
    metricas <- data.frame(
      Metrica = c("Exactitud_Pct", "Vectores_Soporte", "N", "Kernel", "Costo"),
      Valor   = c(acc, length(mod$index), nrow(df_model),
                  kernels[Kernel], Costo),
      stringsAsFactors = FALSE
    )
    resultado <- list(matriz_confusion = cm_df, metricas = metricas)
    tier_map  <- c(matriz_confusion = 1L, metricas = 1L)
  } else {
    pred_num <- as.numeric(pred)
    y_num    <- as.numeric(y_raw)
    rmse     <- round(sqrt(mean((y_num - pred_num)^2, na.rm = TRUE)), 4)
    r2       <- round(1 - sum((y_num - pred_num)^2) /
                           sum((y_num - mean(y_num))^2), 4)
    metricas <- data.frame(
      Metrica = c("RMSE", "R_cuadrado", "Vectores_Soporte", "N", "Kernel", "Costo"),
      Valor   = c(rmse, r2, length(mod$index), nrow(df_model),
                  kernels[Kernel], Costo),
      stringsAsFactors = FALSE
    )
    n_show   <- min(50L, nrow(df_model))
    pred_df  <- data.frame(
      ID = seq_len(n_show),
      Observado  = round(y_num[1:n_show], 4),
      Prediccion = round(pred_num[1:n_show], 4),
      stringsAsFactors = FALSE
    )

    html_graf <- tryCatch({
      traces <- list(
        list(type = "scatter", mode = "markers",
             x = round(y_num, 4), y = round(pred_num, 4),
             marker = list(size = 6, color = "#d7a538", opacity = 0.7),
             hoverinfo = "none", showlegend = FALSE),
        list(type = "scatter", mode = "lines",
             x = range(y_num), y = range(y_num),
             line = list(color = "rgba(215,165,56,0.35)", dash = "dash", width = 1),
             showlegend = FALSE, hoverinfo = "none")
      )
      layout <- list(
        title = list(text = "Observado vs Predicho (SVM)",
                     font = list(color = "#e0e0e0", size = 12)),
        xaxis = list(title = "Observado", color = "#888", gridcolor = "#333"),
        yaxis = list(title = "Predicho",  color = "#888", gridcolor = "#333"),
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

    resultado <- list(metricas = metricas, predicciones = pred_df, grafico = html_graf)
    tier_map  <- c(metricas = 1L, predicciones = 2L, grafico = 1L)
  }

  return(r_object_to_slots(resultado, tier_map = tier_map))
}
