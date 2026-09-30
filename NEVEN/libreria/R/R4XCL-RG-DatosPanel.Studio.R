# ===============================================================================
# NEVEN Data Lab — Wrapper Studio para Regresion con Datos de Panel
# Requiere: r_object_to_slots.R cargado en el entorno global
# ===============================================================================

RG_DatosPanel.Studio <- function(data_Y,
                                   data_X,
                                   data_I,
                                   data_T,
                                   TipoModelo = 1L,
                                   Escala     = FALSE) {

  if (!requireNamespace("plm", quietly = TRUE)) stop("Paquete 'plm' requerido.")

  # Validaciones basicas
  for (nm in c("data_Y","data_X","data_I","data_T")) {
    obj <- get(nm)
    if (!is.data.frame(obj) && !is.matrix(obj)) stop(paste0("'", nm, "' debe ser un data.frame."))
  }
  data_Y <- as.data.frame(data_Y)
  data_X <- as.data.frame(data_X)
  data_I <- as.data.frame(data_I)
  data_T <- as.data.frame(data_T)

  TipoModelo <- as.integer(TipoModelo)
  if (TipoModelo < 1L || TipoModelo > 3L) stop("TipoModelo: 1=Efectos Fijos, 2=Efectos Aleatorios, 3=Pooled OLS.")

  n_rows <- nrow(data_Y)
  if (!all(c(nrow(data_X), nrow(data_I), nrow(data_T)) == n_rows)) {
    stop("Todos los data.frames deben tener el mismo numero de filas.")
  }

  y_col  <- names(data_Y)[1]
  x_cols <- names(data_X)
  i_col  <- names(data_I)[1]
  t_col  <- names(data_T)[1]

  num_X <- sapply(data_X, is.numeric)
  if (!any(num_X)) stop("data_X debe tener al menos una columna numerica.")
  x_cols <- x_cols[num_X]

  if (isTRUE(Escala)) data_X[, x_cols] <- scale(data_X[, x_cols, drop = FALSE])

  # Construir data.frame de panel
  df_panel <- cbind(
    data_Y[y_col],
    data_X[x_cols],
    setNames(data_I[1], "individuo"),
    setNames(data_T[1], "tiempo")
  )

  modelos_plm <- c("within", "random", "pooling")
  formula_str <- paste(y_col, "~", paste(x_cols, collapse = " + "))

  pd  <- plm::pdata.frame(df_panel, index = c("individuo", "tiempo"))
  mod <- plm::plm(as.formula(formula_str), data = pd,
                  model = modelos_plm[TipoModelo])
  s   <- summary(mod)

  # Coeficientes
  coef_mat <- as.data.frame(s$coefficients)
  coef_mat <- cbind(Variable = rownames(coef_mat), coef_mat)
  colnames(coef_mat) <- c("Variable", "Estimado", "Error_Std", "t_value", "p_value")
  rownames(coef_mat) <- NULL
  coef_mat[, 2:5] <- lapply(coef_mat[, 2:5], function(x) round(as.numeric(x), 4))

  # Metricas
  r2_within  <- tryCatch(round(s$r.squared["rsq"], 4), error = function(e) NA)
  r2_overall <- tryCatch(round(s$r.squared["adjrsq"], 4), error = function(e) NA)
  tipo_str   <- c("Efectos Fijos (Within)", "Efectos Aleatorios", "Pooled OLS")[TipoModelo]

  n_ind <- length(unique(df_panel$individuo))
  n_per <- length(unique(df_panel$tiempo))

  metricas <- data.frame(
    Metrica = c("Tipo_Modelo", "R2_Within", "R2_Ajustado",
                "N_Individuos", "N_Periodos", "N_Total"),
    Valor   = c(tipo_str,
                as.character(r2_within),
                as.character(r2_overall),
                n_ind, n_per, n_rows),
    stringsAsFactors = FALSE
  )

  # Stargazer
  # Tabla científica — texto plano estilo consola R
  html_stargazer <- tryCatch({
    paste(capture.output(print(summary(mod))), collapse = "\n")
  }, error = function(e) {
    paste("Error al generar resumen del modelo:", conditionMessage(e))
  })

  # Grafico residuos
  html_res <- tryCatch({
    res_vals  <- round(as.numeric(residuals(mod)), 4)
    fit_vals  <- round(as.numeric(fitted(mod)), 4)
    traces <- list(
      list(type = "scatter", mode = "markers",
           x = fit_vals, y = res_vals,
           marker = list(size = 5, color = "#d7a538", opacity = 0.6),
           hovertemplate = "Ajust:%{x} Resid:%{y}<extra></extra>",
           showlegend = FALSE),
      list(type = "scatter", mode = "lines",
           x = range(fit_vals), y = c(0, 0),
           line = list(color = "rgba(215,165,56,0.3)", dash = "dash", width = 1),
           showlegend = FALSE, hoverinfo = "none")
    )
    layout <- list(
      title = list(text = "Residuos vs Valores Ajustados",
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = "Ajustado", color = "#888", gridcolor = "#333"),
      yaxis = list(title = "Residuo", color = "#888", gridcolor = "#333",
                   zeroline = TRUE, zerolinecolor = "#555"),
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

  resultado <- list(
    tabla_cientifica = html_stargazer,
    coeficientes     = coef_mat,
    metricas         = local({
      m <- metricas; vals <- as.character(m[[2]]); keys <- as.character(m[[1]])
      w_k <- max(nchar(keys)); w_v <- max(nchar(vals))
      paste(c(paste0(formatC("Metrica",width=-w_k),"  ",formatC("Valor",width=w_v)),
              strrep("-",w_k+w_v+2),
              mapply(function(k,v) paste0(formatC(k,width=-w_k),"  ",formatC(v,width=w_v)),keys,vals)),
            collapse="\n")
    }),
    grafico          = html_res
  )
  tier_map <- c(tabla_cientifica = 1L, coeficientes = 2L,
                metricas = 1L, grafico = 1L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
