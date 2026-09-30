# ===============================================================================
# NEVEN Data Lab — GR_Scatter: Gráfico de Dispersión Interactivo
# ===============================================================================
# Familia:  GR (Gráficos)
# Función:  GR_Scatter.Studio
# Sidecar:  GR_Scatter.json
# Plotly:   scatter con mode="markers", tema oscuro NEVEN
# ===============================================================================

GR_Scatter.Studio <- function(data_X,
                               data_Y,
                               data_Color  = NULL,
                               data_Tamaño = NULL,
                               data_Texto  = NULL,
                               MostrarLeyenda = TRUE,
                               Paleta      = 1L) {

  # ── Helper interno: rechazar columnas todo-NA ────────────────────────────────
  .check_col_not_all_na <- function(vec, nombre) {
    if (all(is.na(vec)))
      stop(sprintf("La columna '%s' no contiene valores válidos (solo NA).", nombre))
  }

  # ── Validación de data_X ─────────────────────────────────────────────────────
  if (!is.data.frame(data_X))
    stop("'data_X' debe ser un data.frame.")
  if (nrow(data_X) == 0)
    stop("El filtro aplicado no retorna filas. Verifique la cláusula WHERE.")

  # ── Validación de data_Y ─────────────────────────────────────────────────────
  if (!is.data.frame(data_Y))
    stop("'data_Y' debe ser un data.frame.")
  if (nrow(data_Y) == 0)
    stop("El filtro aplicado no retorna filas. Verifique la cláusula WHERE.")

  # ── Validación de dimensiones ────────────────────────────────────────────────
  if (nrow(data_X) != nrow(data_Y))
    stop("'data_X' y 'data_Y' deben tener el mismo número de filas.")

  # ── Extraer columna numérica de data_X ───────────────────────────────────────
  x_cols <- names(data_X)[sapply(data_X, is.numeric)]
  if (length(x_cols) == 0)
    stop("'data_X' debe contener al menos una columna numérica para el eje X.")
  x_col <- x_cols[1]
  x_vec <- as.numeric(data_X[[x_col]])
  .check_col_not_all_na(x_vec, x_col)

  # ── Extraer columna numérica de data_Y ───────────────────────────────────────
  y_cols <- names(data_Y)[sapply(data_Y, is.numeric)]
  if (length(y_cols) == 0)
    stop("'data_Y' debe contener al menos una columna numérica para el eje Y.")
  y_col <- y_cols[1]
  y_vec <- as.numeric(data_Y[[y_col]])
  .check_col_not_all_na(y_vec, y_col)

  # ── Paletas de color ─────────────────────────────────────────────────────────
  Paleta <- as.integer(Paleta)
  if (is.na(Paleta) || Paleta < 1L || Paleta > 5L) Paleta <- 1L

  paletas <- list(
    `1` = c("#d7a538", "#888888", "#c08820", "#aaaaaa", "#e8c060", "#666666", "#f0d080", "#444444"),
    `2` = c("#440154", "#3b528b", "#21908d", "#5dc963", "#fde725",
            "#482878", "#27ad81", "#95d840"),
    `3` = c("#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636",
            "#f0f921", "#cb4679", "#7e03a8"),
    `4` = c("#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
            "#a65628", "#f781bf", "#999999"),
    `5` = c("#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6",
            "#ffffcc", "#e5d8bd", "#fddaec")
  )
  color_palette <- paletas[[as.character(Paleta)]]
  default_color <- color_palette[1]   # color base (dorado NEVEN en paleta 1)

  # ── Extraer data_Color (opcional) ────────────────────────────────────────────
  color_vec  <- NULL
  color_name <- NULL
  if (!is.null(data_Color) && is.data.frame(data_Color) && ncol(data_Color) > 0) {
    color_name <- names(data_Color)[1]
    color_vec  <- data_Color[[color_name]]
  }

  # ── Extraer data_Tamaño (opcional) ───────────────────────────────────────────
  size_vec <- NULL
  if (!is.null(data_Tamaño) && is.data.frame(data_Tamaño) && ncol(data_Tamaño) > 0) {
    sz_cols <- names(data_Tamaño)[sapply(data_Tamaño, is.numeric)]
    if (length(sz_cols) > 0) {
      raw_size <- as.numeric(data_Tamaño[[sz_cols[1]]])
      # Escalar al rango 5–30
      rng <- range(raw_size, na.rm = TRUE)
      if (rng[1] == rng[2]) {
        size_vec <- rep(12, length(raw_size))
      } else {
        size_vec <- 5 + (raw_size - rng[1]) / (rng[2] - rng[1]) * 25
      }
      size_vec[is.na(size_vec)] <- 6
    }
  }

  # ── Extraer data_Texto (opcional) ────────────────────────────────────────────
  text_vec <- NULL
  if (!is.null(data_Texto) && is.data.frame(data_Texto) && ncol(data_Texto) > 0) {
    text_vec <- as.character(data_Texto[[names(data_Texto)[1]]])
  }

  # ── Construcción del hovertemplate ───────────────────────────────────────────
  if (!is.null(text_vec)) {
    hover_tmpl <- paste0(x_col, ": %{x}<br>", y_col, ": %{y}<br>%{text}<extra></extra>")
  } else {
    hover_tmpl <- paste0(x_col, ": %{x}<br>", y_col, ": %{y}<extra></extra>")
  }

  # ── Construcción de trace(s) Plotly ──────────────────────────────────────────
  traces <- list()

  if (!is.null(color_vec)) {
    # Un trace por cada nivel/valor único de color
    grupos <- unique(color_vec)
    grupos <- grupos[!is.na(grupos)]

    for (i in seq_along(grupos)) {
      grp      <- grupos[i]
      idx      <- which(color_vec == grp)
      grp_color <- color_palette[((i - 1L) %% length(color_palette)) + 1L]

      marker_cfg <- list(
        color   = grp_color,
        size    = if (!is.null(size_vec)) size_vec[idx] else 6,
        opacity = 0.85,
        line    = list(color = "#2a2a2a", width = 0.5)
      )

      tr <- list(
        type             = "scatter",
        mode             = "markers",
        name             = as.character(grp),
        x                = x_vec[idx],
        y                = y_vec[idx],
        marker           = marker_cfg,
        hovertemplate    = hover_tmpl,
        showlegend       = isTRUE(MostrarLeyenda)
      )
      if (!is.null(text_vec)) tr$text <- text_vec[idx]
      traces <- c(traces, list(tr))
    }

    # Filas NA en color_vec → traza separada
    na_idx <- which(is.na(color_vec))
    if (length(na_idx) > 0) {
      tr_na <- list(
        type          = "scatter",
        mode          = "markers",
        name          = "(sin grupo)",
        x             = x_vec[na_idx],
        y             = y_vec[na_idx],
        marker        = list(color = "#888888", size = 6, opacity = 0.7,
                             line = list(color = "#2a2a2a", width = 0.5)),
        hovertemplate = hover_tmpl,
        showlegend    = isTRUE(MostrarLeyenda)
      )
      if (!is.null(text_vec)) tr_na$text <- text_vec[na_idx]
      traces <- c(traces, list(tr_na))
    }

  } else {
    # Trace único sin agrupación
    marker_cfg <- list(
      color   = default_color,
      size    = if (!is.null(size_vec)) size_vec else 6,
      opacity = 0.85,
      line    = list(color = "#2a2a2a", width = 0.5)
    )

    tr <- list(
      type          = "scatter",
      mode          = "markers",
      name          = y_col,
      x             = x_vec,
      y             = y_vec,
      marker        = marker_cfg,
      hovertemplate = hover_tmpl,
      showlegend    = isTRUE(MostrarLeyenda)
    )
    if (!is.null(text_vec)) tr$text <- text_vec
    traces <- list(tr)
  }

  # ── Construcción del layout ──────────────────────────────────────────────────
  layout <- list(
    paper_bgcolor = "#373434",
    plot_bgcolor  = "#373434",
    font          = list(color = "#888"),
    xaxis = list(
      title      = list(text = x_col, font = list(color = "#888")),
      color      = "#888",
      gridcolor  = "#333",
      zerolinecolor = "#555"
    ),
    yaxis = list(
      title      = list(text = y_col, font = list(color = "#888")),
      color      = "#888",
      gridcolor  = "#333",
      zerolinecolor = "#555"
    ),
    legend = list(
      font       = list(color = "#888"),
      bgcolor    = "#373434",
      bordercolor = "#555"
    ),
    showlegend = isTRUE(MostrarLeyenda),
    margin     = list(t = 50, r = 30, b = 60, l = 60)
  )

  # ── Codificación base64 + construcción HTML ──────────────────────────────────
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

  # ── Retorno estándar ─────────────────────────────────────────────────────────
  return(r_object_to_slots(
    list(grafico = html_plotly),
    tier_map = c(grafico = 1L)
  ))
}
