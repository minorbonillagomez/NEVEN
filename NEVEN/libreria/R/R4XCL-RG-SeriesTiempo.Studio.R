# ===============================================================================
# NEVEN Data Lab — Wrapper Studio para Analisis de Series de Tiempo
# Requiere: r_object_to_slots.R cargado en el entorno global
# ===============================================================================

RG_SeriesTiempo.Studio <- function(data_Y,
                                     data_X        = NULL,
                                     Periodicidad  = 1L,
                                     TipoAnalisis  = 1L,
                                     Rezagos       = 12L) {

  # Validaciones
  if (!is.data.frame(data_Y) && !is.matrix(data_Y)) stop("'data_Y' debe ser un data.frame.")
  data_Y <- as.data.frame(data_Y)
  y_col  <- names(data_Y)[1]
  y_vec  <- as.numeric(data_Y[[y_col]])
  y_vec  <- na.omit(y_vec)

  if (length(y_vec) < 10) stop("Se requieren al menos 10 observaciones.")

  Periodicidad <- as.integer(Periodicidad)
  TipoAnalisis <- as.integer(TipoAnalisis)
  Rezagos      <- as.integer(Rezagos)

  freqs <- c(1L, 4L, 12L, 52L, 365L)
  if (Periodicidad < 1L || Periodicidad > 5L) stop("Periodicidad: 1=Anual 2=Trimestral 3=Mensual 4=Semanal 5=Diaria.")

  y_ts <- ts(y_vec, frequency = freqs[Periodicidad])

  tiene_X <- !is.null(data_X) && is.data.frame(data_X) && ncol(data_X) > 0 && nrow(data_X) == nrow(data_Y)

  # ── Estadisticas descriptivas basicas ────────────────────────────────────
  stats_df <- data.frame(
    Estadistico = c("N", "Media", "Mediana", "Desv_Std", "Min", "Max",
                    "Asimetria", "Curtosis"),
    Valor = c(
      length(y_vec),
      round(mean(y_vec), 4),
      round(median(y_vec), 4),
      round(sd(y_vec), 4),
      round(min(y_vec), 4),
      round(max(y_vec), 4),
      round(mean((y_vec - mean(y_vec))^3) / sd(y_vec)^3, 4),
      round(mean((y_vec - mean(y_vec))^4) / sd(y_vec)^4, 4)
    ),
    stringsAsFactors = FALSE
  )

  # ── Prueba de Raiz Unitaria (ADF) ─────────────────────────────────────────
  test_adf <- tryCatch({
    if (!requireNamespace("tseries", quietly = TRUE)) stop("tseries requerido")
    a <- tseries::adf.test(y_ts)
    data.frame(
      Prueba    = "Augmented Dickey-Fuller",
      Estadistico = round(as.numeric(a$statistic), 4),
      p_value   = round(a$p.value, 4),
      Hipotesis = "H0: La serie tiene raiz unitaria (no estacionaria)",
      Conclusion = if (a$p.value < 0.05) "Rechaza H0: Serie ESTACIONARIA (p<0.05)"
                   else "No rechaza H0: Serie NO estacionaria (p>=0.05)",
      stringsAsFactors = FALSE
    )
  }, error = function(e) {
    data.frame(Prueba="ADF", Estadistico=NA, p_value=NA,
               Hipotesis="", Conclusion=paste("No disponible:", conditionMessage(e)),
               stringsAsFactors = FALSE)
  })

  # ── Autocorrelacion (ACF y PACF) ──────────────────────────────────────────
  max_lag <- min(Rezagos, floor(length(y_vec) / 3))
  acf_vals  <- acf(y_ts, lag.max = max_lag, plot = FALSE)$acf[-1]
  pacf_vals <- pacf(y_ts, lag.max = max_lag, plot = FALSE)$acf

  lags <- seq_len(length(acf_vals))
  ci   <- round(1.96 / sqrt(length(y_vec)), 4)

  acf_df <- data.frame(
    Rezago = lags,
    ACF    = round(acf_vals, 4),
    PACF   = round(pacf_vals[seq_len(length(acf_vals))], 4),
    Limite_IC = ci,
    stringsAsFactors = FALSE
  )

  # ── Grafico de la serie temporal ──────────────────────────────────────────
  html_serie <- tryCatch({
    n   <- length(y_vec)
    idx <- seq_len(n)
    traces <- list(list(
      type = "scatter", mode = "lines",
      x = idx, y = round(y_vec, 4),
      line = list(color = "#d7a538", width = 1.5),
      hovertemplate = "t=%{x}: %{y}<extra></extra>",
      showlegend = FALSE
    ))
    layout <- list(
      title = list(text = paste0("Serie: ", y_col),
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = "Periodo", color = "#888", gridcolor = "#333"),
      yaxis = list(title = y_col, color = "#888", gridcolor = "#333"),
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

  # ── Grafico ACF/PACF ──────────────────────────────────────────────────────
  html_acf <- tryCatch({
    traces2 <- list(
      list(type = "bar", x = lags, y = round(acf_vals, 4),
           marker = list(color = "#d7a538"), name = "ACF",
           hovertemplate = "Rezago %{x}: ACF=%{y:.4f}<extra></extra>"),
      list(type = "scatter", mode = "lines",
           x = range(lags), y = c(ci, ci),
           line = list(color = "rgba(215,165,56,0.35)", dash = "dash", width = 1),
           showlegend = FALSE, hoverinfo = "none"),
      list(type = "scatter", mode = "lines",
           x = range(lags), y = c(-ci, -ci),
           line = list(color = "rgba(215,165,56,0.35)", dash = "dash", width = 1),
           showlegend = FALSE, hoverinfo = "none")
    )
    layout2 <- list(
      title = list(text = "Funcion de Autocorrelacion (ACF)",
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = "Rezago", color = "#888", gridcolor = "#333"),
      yaxis = list(title = "ACF", color = "#888", gridcolor = "#333",
                   zeroline = TRUE, zerolinecolor = "#555"),
      paper_bgcolor = "#373434", plot_bgcolor = "#373434",
      font = list(color = "#888"), margin = list(t = 50, r = 20, b = 50, l = 60)
    )
    fig2_json <- iconv(jsonlite::toJSON(list(data = traces2, layout = layout2),
                                         auto_unbox = TRUE, na = "null"),
                       from = "UTF-8", to = "UTF-8", sub = "byte")
    paste0('<html><body><neven-plotly>',
           jsonlite::base64_enc(chartr("\n\r", "  ", fig2_json)),
           '</neven-plotly></body></html>')
  }, error = function(e) {
    paste0('<html><body><p style="color:#888;padding:8px">ACF no disponible</p></body></html>')
  })

  resultado <- list(
    serie_temporal  = html_serie,
    estadisticas    = stats_df,
    prueba_adf      = test_adf,
    autocorrelacion = acf_df,
    acf_grafico     = html_acf
  )
  tier_map <- c(
    serie_temporal  = 1L,
    estadisticas    = 1L,
    prueba_adf      = 1L,
    autocorrelacion = 2L,
    acf_grafico     = 1L
  )

  # ── Regresion dinamica Y_t ~ X_t (si se proporcionaron variables X) ────────
  if (tiene_X) {
    data_X  <- as.data.frame(data_X)
    num_X   <- sapply(data_X, is.numeric)
    x_cols  <- names(data_X)[num_X]

    if (length(x_cols) > 0) {
      df_reg <- cbind(data_Y[y_col], data_X[x_cols])
      formula_str <- paste(y_col, "~", paste(x_cols, collapse = " + "))
      mod_dyn <- tryCatch(lm(as.formula(formula_str), data = df_reg), error = function(e) NULL)

      if (!is.null(mod_dyn)) {
        s_dyn <- summary(mod_dyn)

        coef_dyn <- as.data.frame(s_dyn$coefficients)
        coef_dyn <- cbind(Variable = rownames(coef_dyn), coef_dyn)
        colnames(coef_dyn) <- c("Variable","Estimado","Error_Std","t_value","p_value")
        rownames(coef_dyn) <- NULL
        coef_dyn[,2:5] <- lapply(coef_dyn[,2:5], function(x) round(as.numeric(x), 4))

        metr_dyn <- data.frame(
          Metrica = c("R_cuadrado","R_cuad_ajustado","F_estadistico","p_value_F","AIC","N"),
          Valor   = c(round(s_dyn$r.squared,4), round(s_dyn$adj.r.squared,4),
                      round(s_dyn$fstatistic[1],4),
                      round(pf(s_dyn$fstatistic[1],s_dyn$fstatistic[2],s_dyn$fstatistic[3],lower.tail=FALSE),4),
                      round(AIC(mod_dyn),4), nrow(df_reg)),
          stringsAsFactors = FALSE
        )

        # Stargazer para la regresion dinamica
        html_sg <- tryCatch({
          if (!requireNamespace("stargazer", quietly=TRUE)) stop("stargazer requerido")
          raw <- capture.output(stargazer::stargazer(mod_dyn, type="html",
                                                      title=paste0("Regresion Dinamica: ",y_col," ~ X_t"),
                                                      dep.var.labels=y_col,
                                                      covariate.labels=x_cols, out=NULL))
          style <- paste0("<style>body{background:#373434;color:#e0e0e0;font-family:'Segoe UI',sans-serif;",
                          "font-size:12px;padding:8px}table{border-collapse:collapse;width:100%}",
                          "td,th{padding:4px 8px;border-bottom:1px solid #555}",
                          "td:first-child{text-align:left}td:not(:first-child){text-align:center}",
                          "p{color:#888;font-size:10px}</style>")
          iconv(paste0("<html><head>",style,"</head><body>",paste(raw,collapse="\n"),"</body></html>"),
                from="UTF-8",to="UTF-8",sub="byte")
        }, error=function(e) {
          paste0("<html><body><p style='color:#888;padding:8px'>Stargazer no disponible</p></body></html>")
        })

        resultado$tabla_regresion  <- html_sg
        resultado$coef_regresion   <- coef_dyn
        resultado$metricas_regresion <- metr_dyn
        tier_map <- c(tier_map,
                      tabla_regresion    = 1L,
                      coef_regresion     = 2L,
                      metricas_regresion = 1L)
      }
    }
  }

  return(r_object_to_slots(resultado, tier_map = tier_map))
}
