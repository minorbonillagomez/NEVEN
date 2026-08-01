# ===============================================================================
# NEVEN Data Lab — Wrapper Studio para Regresion Tobit
# Requiere: r_object_to_slots.R cargado en el entorno global
# ===============================================================================

RG_Tobit.Studio <- function(data_Y,
                               data_X,
                               Limite_Inferior = 0,
                               Limite_Superior = 999999,
                               Escala          = FALSE) {

  if (!requireNamespace("VGAM", quietly = TRUE)) stop("Paquete 'VGAM' requerido.")

  if (!is.data.frame(data_Y) && !is.matrix(data_Y)) stop("'data_Y' debe ser un data.frame.")
  if (!is.data.frame(data_X) && !is.matrix(data_X)) stop("'data_X' debe ser un data.frame.")
  data_Y <- as.data.frame(data_Y)
  data_X <- as.data.frame(data_X)

  if (nrow(data_Y) != nrow(data_X)) stop("data_Y y data_X deben tener el mismo numero de filas.")

  y_col  <- names(data_Y)[1]
  num_X  <- sapply(data_X, is.numeric)
  if (!any(num_X)) stop("data_X debe tener al menos una columna numerica.")
  x_cols <- names(data_X)[num_X]

  y_vec  <- as.numeric(data_Y[[y_col]])
  if (all(is.na(y_vec))) stop("data_Y no contiene valores validos.")

  if (isTRUE(Escala)) data_X[, x_cols] <- scale(data_X[, x_cols, drop = FALSE])

  # Resolver limites: -999999 = -Inf, 999999 = +Inf
  li <- as.numeric(Limite_Inferior)
  ls <- as.numeric(Limite_Superior)
  if (li <= -999990) li <- -Inf
  if (ls >=  999990) ls <-  Inf

  tipo_censura <- if (is.infinite(li) && is.infinite(ls)) {
    stop("Debe especificar al menos un limite de censura.")
  } else if (!is.infinite(li) && is.infinite(ls)) {
    paste0("Censura inferior en ", li)
  } else if (is.infinite(li) && !is.infinite(ls)) {
    paste0("Censura superior en ", ls)
  } else {
    paste0("Censura doble: [", li, ", ", ls, "]")
  }

  df_model    <- cbind(data_Y[y_col], data_X[x_cols])
  formula_str <- paste(y_col, "~", paste(x_cols, collapse = " + "))

  # Porcentaje de observaciones censuradas
  n_total      <- nrow(df_model)
  cens_inf     <- if (!is.infinite(li)) sum(y_vec <= li, na.rm = TRUE) else 0L
  cens_sup     <- if (!is.infinite(ls)) sum(y_vec >= ls, na.rm = TRUE) else 0L

  # Ajuste del modelo Tobit con VGAM::tobit
  mod <- VGAM::vglm(
    as.formula(formula_str),
    family  = VGAM::tobit(Lower = li, Upper = ls),
    data    = df_model
  )

  # Coeficientes (excluir el parametro de escala "loglink(sd)")
  coef_all <- VGAM::coef(mod)
  coef_se  <- sqrt(diag(VGAM::vcov(mod)))
  z_vals   <- coef_all / coef_se
  p_vals   <- 2 * pnorm(-abs(z_vals))

  # Filtrar solo coeficientes de media (no de escala)
  coef_names <- names(coef_all)
  is_mean    <- !grepl("log\\(sigma\\)|loglink|:2$", coef_names)
  coef_df    <- data.frame(
    Variable  = gsub(":1$", "", coef_names[is_mean]),
    Estimado  = round(coef_all[is_mean], 4),
    Error_Std = round(coef_se[is_mean], 4),
    z_value   = round(z_vals[is_mean], 4),
    p_value   = round(p_vals[is_mean], 4),
    stringsAsFactors = FALSE
  )
  rownames(coef_df) <- NULL

  # Efectos marginales aproximados (factor de escala Mills)
  fit_mean  <- VGAM::fitted(mod)[, 1]  # media latente E[Y*]
  sigma_hat <- exp(coef_all[!is_mean][1])
  phi_arg   <- (li - fit_mean) / sigma_hat
  mfx_scale <- pnorm(-phi_arg)
  mfx_df    <- coef_df
  mfx_df$Efecto_Marginal <- round(coef_df$Estimado * mean(mfx_scale, na.rm = TRUE), 4)

  # Metricas
  log_lik    <- as.numeric(VGAM::logLik(mod))
  aic_val    <- -2 * log_lik + 2 * length(coef_all)
  bic_val    <- -2 * log_lik + log(n_total) * length(coef_all)

  metricas <- data.frame(
    Metrica = c("Log_Verosimilitud", "AIC", "BIC",
                "Tipo_Censura",
                "Pct_Censuradas_Inf", "Pct_Censuradas_Sup",
                "Sigma", "N"),
    Valor   = c(round(log_lik, 4), round(aic_val, 4), round(bic_val, 4),
                tipo_censura,
                paste0(round(cens_inf/n_total*100,2), "% (n=", cens_inf, ")"),
                paste0(round(cens_sup/n_total*100,2), "% (n=", cens_sup, ")"),
                round(sigma_hat, 4),
                n_total),
    stringsAsFactors = FALSE
  )

  # Grafico observado vs predicho (media latente)
  html_graf <- tryCatch({
    fit_vals <- round(VGAM::fitted(mod)[, 1], 4)
    n_show   <- min(100L, length(y_vec))
    ord      <- order(y_vec[1:n_show])
    traces <- list(
      list(type = "scatter", mode = "markers",
           x = seq_len(n_show), y = y_vec[ord[1:n_show]],
           marker = list(size = 5, color = "#888", opacity = 0.6),
           name = "Observado", hoverinfo = "none"),
      list(type = "scatter", mode = "lines",
           x = seq_len(n_show), y = fit_vals[ord[1:n_show]],
           line = list(color = "#d7a538", width = 2),
           name = "Predicho (E[Y*])", hoverinfo = "none")
    )
    layout <- list(
      title = list(text = "Tobit: Observado vs Predicho",
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = "Observaciones (ordenadas)", color = "#888", gridcolor = "#333"),
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

  resultado <- list(
    coeficientes       = coef_df,
    efectos_marginales = mfx_df,
    metricas           = metricas,
    grafico            = html_graf
  )
  tier_map <- c(coeficientes = 1L, efectos_marginales = 1L,
                metricas = 1L, grafico = 1L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
