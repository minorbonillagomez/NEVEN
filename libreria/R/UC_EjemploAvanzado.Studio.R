# ===============================================================================
# NEVEN Data Lab — EJEMPLO AVANZADO: Funcion con Y~X, grafico y parametros
# ===============================================================================
# Este ejemplo muestra el patron COMPLETO:
#   - Dos roles: Y (dependiente) y X (independientes)
#   - Grafico interactivo con plotly via JSON
#   - Multiples parametros con tier 1 y tier 2
#   - Tabla Stargazer opcional
# ===============================================================================

UC_EjemploAvanzado.Studio <- function(data_Y,
                                        data_X,
                                        Metodo    = 1L,
                                        Escala    = FALSE,
                                        MostrarGrafico = TRUE) {

  # ── Validacion ──────────────────────────────────────────────────────────────
  if (!is.data.frame(data_Y)) stop("'data_Y' debe ser un data.frame.")
  if (!is.data.frame(data_X)) stop("'data_X' debe ser un data.frame.")
  data_Y <- as.data.frame(data_Y)
  data_X <- as.data.frame(data_X)
  if (nrow(data_Y) != nrow(data_X)) stop("data_Y y data_X deben tener el mismo numero de filas.")

  Metodo <- as.integer(Metodo)
  metodos <- c("pearson", "spearman", "kendall")
  if (Metodo < 1L || Metodo > 3L) stop("Metodo: 1=Pearson, 2=Spearman, 3=Kendall.")

  y_col  <- names(data_Y)[1]
  x_cols <- names(data_X)[sapply(data_X, is.numeric)]
  if (length(x_cols) == 0) stop("data_X debe tener columnas numericas.")

  y_vec  <- as.numeric(data_Y[[y_col]])
  if (isTRUE(Escala)) data_X[, x_cols] <- scale(data_X[, x_cols, drop = FALSE])

  # ── Analisis: correlaciones de Y con cada X ──────────────────────────────────
  cor_list <- lapply(x_cols, function(xc) {
    xv   <- as.numeric(data_X[[xc]])
    test <- cor.test(y_vec, xv, method = metodos[Metodo])
    data.frame(
      Variable    = xc,
      Correlacion = round(as.numeric(test$estimate), 4),
      p_value     = round(test$p.value, 4),
      Significancia = ifelse(test$p.value < 0.01, "***",
                      ifelse(test$p.value < 0.05, "**",
                      ifelse(test$p.value < 0.10, "*", ""))),
      stringsAsFactors = FALSE
    )
  })
  cor_df <- do.call(rbind, cor_list)
  cor_df <- cor_df[order(-abs(cor_df$Correlacion)), ]
  rownames(cor_df) <- NULL

  # ── Grafico: barras de correlacion ───────────────────────────────────────────
  html_grafico <- if (isTRUE(MostrarGrafico) && length(x_cols) > 0) {
    tryCatch({
      ord  <- order(cor_df$Correlacion)
      cols <- cor_df$Variable[ord]
      vals <- cor_df$Correlacion[ord]
      colors <- ifelse(vals >= 0, "#d7a538", "#888888")

      traces <- list(list(
        type = "bar", orientation = "h",
        x = vals, y = cols,
        marker = list(color = colors),
        hovertemplate = "%{y}: r=%{x:.4f}<extra></extra>"
      ))
      layout <- list(
        title = list(text = paste0("Correlaciones con ", y_col,
                                   " (", metodos[Metodo], ")"),
                     font = list(color = "#e0e0e0", size = 12)),
        xaxis = list(title = "Correlacion", color = "#888", gridcolor = "#333",
                     zeroline = TRUE, zerolinecolor = "#555",
                     range = c(-1.1, 1.1)),
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
  } else {
    paste0('<html><body><p style="color:#888;padding:8px">Grafico desactivado</p></body></html>')
  }

  # ── Resultado ─────────────────────────────────────────────────────────────
  resultado <- list(
    correlaciones = cor_df,
    grafico       = html_grafico
  )
  tier_map <- c(correlaciones = 1L, grafico = 1L)

  return(r_object_to_slots(resultado, tier_map = tier_map))
}
