# ===============================================================================
# NEVEN Data Lab — GR_SeriesTiempo.Studio.R
# Gráfico de Serie de Tiempo con opción de línea de tendencia
# ===============================================================================
# Parámetros:
#   data_X           data.frame — rol X (texto o numérico, requerido)
#                                 se usa como eje de tiempo (fecha, período, índice)
#   data_Y           data.frame — rol Y (numérico, requerido)
#   data_Color       data.frame — rol Color/Series (texto, opcional)
#   MostrarLeyenda   logical    — mostrar leyenda (default TRUE)
#   MostrarTendencia logical    — agregar línea de tendencia (default FALSE)
#   TipoTendencia    integer    — 1=Lineal, 2=Polinómica grado 2 (default 1)
#   AnchoLinea       integer    — ancho de línea en píxeles (default 2)
#   Paleta           integer    — paleta de colores: 1=NEVEN, 2=Viridis, 3=Plasma,
#                                4=Set1, 5=Pastel (default 1)
# Retorna: r_object_to_slots(list(grafico = html), tier_map = c(grafico = 1L))
# ===============================================================================

GR_SeriesTiempo.Studio <- function(data_X,
                                    data_Y,
                                    data_Color       = NULL,
                                    MostrarLeyenda   = TRUE,
                                    MostrarTendencia = FALSE,
                                    TipoTendencia    = 1L,
                                    AnchoLinea       = 2L,
                                    Paleta           = 1L) {

  # ── Helper: rechazar columna completamente NA ──────────────────────────────
  .check_col_not_all_na <- function(vec, nombre) {
    if (all(is.na(vec)))
      stop(sprintf("La columna '%s' no contiene valores válidos (solo NA).", nombre))
  }

  # ── 1. Validación de data_X ────────────────────────────────────────────────
  if (!is.data.frame(data_X))
    stop("'data_X' debe ser un data.frame.")
  if (nrow(data_X) == 0)
    stop("El filtro aplicado no retorna filas. Verifique la cláusula WHERE.")

  # ── 2. Validación de data_Y ────────────────────────────────────────────────
  if (!is.data.frame(data_Y))
    stop("'data_Y' debe ser un data.frame.")
  if (nrow(data_Y) == 0)
    stop("El filtro aplicado no retorna filas en data_Y. Verifique la cláusula WHERE.")
  if (nrow(data_X) != nrow(data_Y))
    stop(sprintf(
      "data_X y data_Y deben tener el mismo número de filas (%d vs %d).",
      nrow(data_X), nrow(data_Y)
    ))

  # ── 3. Extracción de x_vec ─────────────────────────────────────────────────
  x_col <- names(data_X)[1]
  x_vec <- data_X[[x_col]]
  .check_col_not_all_na(x_vec, x_col)

  # ── 4. Extracción de y_vec (primera columna numérica de data_Y) ───────────
  num_cols_y <- names(data_Y)[sapply(data_Y, is.numeric)]
  if (length(num_cols_y) == 0)
    stop("'data_Y' no contiene columnas numéricas. Asigne una columna de tipo numérico al rol Y.")
  y_col <- num_cols_y[1]
  y_vec <- as.numeric(data_Y[[y_col]])
  .check_col_not_all_na(y_vec, y_col)

  # ── 5. Parámetros con coerción de tipos ───────────────────────────────────
  AnchoLinea    <- as.integer(AnchoLinea)
  if (is.na(AnchoLinea) || AnchoLinea < 1L) AnchoLinea <- 2L
  Paleta        <- as.integer(Paleta)
  if (is.na(Paleta) || Paleta < 1L || Paleta > 5L) Paleta <- 1L
  TipoTendencia <- as.integer(TipoTendencia)
  if (is.na(TipoTendencia) || !TipoTendencia %in% c(1L, 2L)) TipoTendencia <- 1L

  # ── 6. Paletas de colores para series múltiples ───────────────────────────
  .get_palette <- function(n, paleta_id) {
    palettes <- list(
      # 1 = NEVEN (dorado → gris → variantes)
      `1` = c("#d7a538", "#888888", "#e8c06b", "#b8860b", "#c0a070",
              "#a0896a", "#f0d080", "#706050", "#d4c090", "#505040"),
      # 2 = Viridis
      `2` = c("#440154", "#3b528b", "#21908c", "#5dc963", "#fde725",
              "#31688e", "#35b779", "#90d743", "#443983", "#1f9e89"),
      # 3 = Plasma
      `3` = c("#0d0887", "#7201a8", "#bd3786", "#ed7953", "#fdca26",
              "#5c01a6", "#cc4778", "#f89540", "#46039f", "#b12a90"),
      # 4 = Set1 (categórico)
      `4` = c("#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
              "#a65628", "#f781bf", "#999999", "#e41a1c", "#377eb8"),
      # 5 = Pastel
      `5` = c("#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6",
              "#ffffcc", "#e5d8bd", "#fddaec", "#f2f2f2", "#b3e2cd")
    )
    pal <- palettes[[as.character(paleta_id)]]
    if (is.null(pal)) pal <- palettes[["1"]]
    # Reciclar colores si hay más series que colores
    pal[((seq_len(n) - 1L) %% length(pal)) + 1L]
  }

  # ── 7. Layout base con tema oscuro ────────────────────────────────────────
  layout <- list(
    paper_bgcolor = "#373434",
    plot_bgcolor  = "#373434",
    font          = list(color = "#888"),
    xaxis         = list(
      title         = list(text = x_col, font = list(color = "#888")),
      color         = "#888",
      gridcolor     = "#333",
      zerolinecolor = "#555"
    ),
    yaxis         = list(
      title         = list(text = y_col, font = list(color = "#888")),
      color         = "#888",
      gridcolor     = "#333",
      zerolinecolor = "#555"
    ),
    legend        = list(font = list(color = "#888")),
    margin        = list(t = 50, r = 30, b = 60, l = 60),
    showlegend    = isTRUE(MostrarLeyenda)
  )

  # ── 8. Construir trazas de datos ───────────────────────────────────────────
  traces <- list()

  if (!is.null(data_Color) && is.data.frame(data_Color) && nrow(data_Color) == nrow(data_X)) {
    # ── Modo multi-serie: una traza por grupo ──────────────────────────────
    color_col <- names(data_Color)[1]
    color_vec <- as.character(data_Color[[color_col]])

    grupos  <- unique(color_vec)
    grupos  <- grupos[!is.na(grupos)]
    colores <- .get_palette(length(grupos), Paleta)

    for (i in seq_along(grupos)) {
      g       <- grupos[i]
      idx     <- which(color_vec == g)
      ord_idx <- idx[order(x_vec[idx])]

      traces[[length(traces) + 1L]] <- list(
        type          = "scatter",
        mode          = "lines",
        name          = g,
        x             = x_vec[ord_idx],
        y             = y_vec[ord_idx],
        line          = list(color = colores[i], width = AnchoLinea),
        hovertemplate = paste0("%{x}<br>", y_col, ": %{y:.4g}<extra>", g, "</extra>")
      )
    }

  } else {
    # ── Modo serie única ───────────────────────────────────────────────────
    traces[[1L]] <- list(
      type          = "scatter",
      mode          = "lines",
      name          = y_col,
      x             = x_vec,
      y             = y_vec,
      line          = list(color = "#d7a538", width = AnchoLinea),
      hovertemplate = paste0("%{x}<br>", y_col, ": %{y:.4g}<extra></extra>")
    )
  }

  # ── 9. Traza de tendencia (opcional, siempre después de los datos) ─────────
  if (isTRUE(MostrarTendencia)) {
    idx_seq <- seq_along(x_vec)
    # Eliminar NA pareados para el ajuste
    valid   <- !is.na(y_vec)

    if (sum(valid) >= 3L) {
      fitted_vals <- tryCatch({
        if (TipoTendencia == 2L) {
          # Polinómica grado 2
          fit <- lm(y_vec[valid] ~ poly(idx_seq[valid], 2))
          pred_full <- predict(fit, newdata = data.frame(
            `poly(idx_seq[valid], 2)` = poly(idx_seq, 2)
          ))
          # predict con poly requiere el mismo objeto poly; recalcular sobre todo el rango
          fit2 <- lm(y_vec[valid] ~ poly(idx_seq[valid], 2, raw = TRUE))
          coefs <- coef(fit2)
          # Evaluar manualmente: b0 + b1*x + b2*x^2
          coefs[1] + coefs[2] * idx_seq + coefs[3] * idx_seq^2
        } else {
          # Lineal (default)
          fit <- lm(y_vec[valid] ~ idx_seq[valid])
          coefs <- coef(fit)
          coefs[1] + coefs[2] * idx_seq
        }
      }, error = function(e) NULL)

      if (!is.null(fitted_vals)) {
        if (TipoTendencia == 2L) {
          tend_name <- "Tendencia polinómica"
          dash_type <- "dot"
        } else {
          tend_name <- "Tendencia lineal"
          dash_type <- "dash"
        }

        traces[[length(traces) + 1L]] <- list(
          type          = "scatter",
          mode          = "lines",
          name          = tend_name,
          x             = x_vec,
          y             = fitted_vals,
          line          = list(color = "#888888", width = 1L, dash = dash_type),
          hovertemplate = paste0("%{x}<br>", tend_name, ": %{y:.4g}<extra></extra>")
        )
      }
    }
  }

  # ── 10. Codificación base64 y armado del slot HTML ────────────────────────
  html_plotly <- tryCatch({
    fig_json <- iconv(
      jsonlite::toJSON(list(data = traces, layout = layout),
                       auto_unbox = TRUE, na = "null"),
      from = "UTF-8", to = "UTF-8", sub = "byte"
    )
    paste0('<html><body><neven-plotly>',
           jsonlite::base64_enc(chartr("\n\r", "  ", fig_json)),
           '</neven-plotly></body></html>')
  }, error = function(e) {
    paste0('<html><body><p style="color:#888;padding:8px">',
           'Gráfico no disponible: ', conditionMessage(e),
           '</p></body></html>')
  })

  # ── 11. Retorno con r_object_to_slots ─────────────────────────────────────
  return(r_object_to_slots(
    list(grafico = html_plotly),
    tier_map = c(grafico = 1L)
  ))
}
