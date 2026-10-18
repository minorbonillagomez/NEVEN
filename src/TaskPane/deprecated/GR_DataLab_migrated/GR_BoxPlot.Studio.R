# ===============================================================================
# NEVEN Data Lab — GR_BoxPlot.Studio: Box Plot (Diagrama de Caja)
# ===============================================================================
# Muestra la distribución estadística (mediana, cuartiles, outliers) por grupo
# o categoría. Soporta agrupación adicional mediante el rol Color.
#
# Parámetros:
#   data_X         data.frame con columna de texto/categórica (grupos, eje X)
#   data_Y         data.frame con columna numérica (valores, eje Y)
#   data_Color     data.frame con columna de texto para agrupación adicional (opt.)
#   MostrarLeyenda lógico — mostrar leyenda en el gráfico
#   MostrarPuntos  lógico — mostrar puntos individuales (TRUE=todos, FALSE=outliers)
#   Paleta         entero 1–5 — paleta de colores (1=NEVEN, 2=Viridis, 3=Plasma,
#                  4=Set1, 5=Pastel)
# ===============================================================================

GR_BoxPlot.Studio <- function(data_X,
                               data_Y,
                               data_Color     = NULL,
                               MostrarLeyenda = TRUE,
                               MostrarPuntos  = FALSE,
                               Paleta         = 1L) {

  # ── Validación de data_X ────────────────────────────────────────────────────
  if (!is.data.frame(data_X))
    stop("'data_X' debe ser un data.frame.")
  if (nrow(data_X) == 0)
    stop("El filtro aplicado no retorna filas. Verifique la cláusula WHERE.")

  # data_X debe tener al menos una columna de tipo texto/carácter o factor
  x_col_idx <- which(sapply(data_X, function(col) {
    is.character(col) || is.factor(col)
  }))
  if (length(x_col_idx) == 0) {
    # Aceptar también columnas numéricas tratadas como categorías (coerción a char)
    x_col_idx <- 1L
  }
  x_col <- names(data_X)[x_col_idx[1]]
  x_vec <- as.character(data_X[[x_col]])

  if (all(is.na(x_vec)))
    stop(sprintf("La columna '%s' no contiene valores válidos (solo NA).", x_col))

  # ── Validación de data_Y ────────────────────────────────────────────────────
  if (!is.data.frame(data_Y))
    stop("'data_Y' debe ser un data.frame.")
  if (nrow(data_Y) == 0)
    stop("El filtro aplicado no retorna filas en data_Y. Verifique la cláusula WHERE.")
  if (nrow(data_Y) != nrow(data_X))
    stop("'data_X' y 'data_Y' deben tener el mismo número de filas.")

  # Extraer primera columna numérica de data_Y
  y_col_idx <- which(sapply(data_Y, is.numeric))
  if (length(y_col_idx) == 0)
    stop("'data_Y' debe contener al menos una columna numérica.")
  y_col <- names(data_Y)[y_col_idx[1]]
  y_vec <- as.numeric(data_Y[[y_col]])

  if (all(is.na(y_vec)))
    stop(sprintf("La columna '%s' no contiene valores válidos (solo NA).", y_col))

  # ── Validación de data_Color (opcional) ─────────────────────────────────────
  color_vec <- NULL
  if (!is.null(data_Color)) {
    if (!is.data.frame(data_Color))
      stop("'data_Color' debe ser un data.frame.")
    if (nrow(data_Color) != nrow(data_X))
      stop("'data_Color' debe tener el mismo número de filas que 'data_X'.")
    c_col <- names(data_Color)[1]
    color_vec <- as.character(data_Color[[c_col]])
    if (all(is.na(color_vec)))
      stop(sprintf("La columna '%s' no contiene valores válidos (solo NA).", c_col))
  }

  # ── Paletas de colores ───────────────────────────────────────────────────────
  Paleta <- as.integer(Paleta)
  if (is.na(Paleta) || Paleta < 1L || Paleta > 5L) Paleta <- 1L

  .paletas <- list(
    # 1 — NEVEN (dorado + complementos oscuros)
    c("#d7a538", "#6b9fbf", "#c45c5c", "#5cb87c", "#9b6bbf",
      "#e07b3a", "#4a8fa8", "#b34d4d", "#4da870", "#7a5aad"),
    # 2 — Viridis
    c("#440154", "#3b528b", "#21908c", "#5dc963", "#fde725",
      "#472d7b", "#27838e", "#46c06f", "#bbdf27", "#fde725"),
    # 3 — Plasma
    c("#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636",
      "#3b049b", "#8f07aa", "#cb3173", "#ed7953", "#fccd25"),
    # 4 — Set1
    c("#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
      "#a65628", "#f781bf", "#999999", "#e41a1c", "#377eb8"),
    # 5 — Pastel
    c("#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6",
      "#ffffcc", "#e5d8bd", "#fddaec", "#f2f2f2", "#fbb4ae")
  )
  colores <- .paletas[[Paleta]]

  # ── Configuración de puntos ──────────────────────────────────────────────────
  boxpoints_val <- if (isTRUE(MostrarPuntos)) "all" else "outliers"

  # ── Tema oscuro estándar ─────────────────────────────────────────────────────
  layout_base <- list(
    paper_bgcolor = "#373434",
    plot_bgcolor  = "#373434",
    font          = list(color = "#888"),
    xaxis         = list(
      color       = "#888",
      gridcolor   = "#333",
      zerolinecolor = "#555",
      title       = list(text = x_col, font = list(color = "#888"))
    ),
    yaxis         = list(
      color       = "#888",
      gridcolor   = "#333",
      zerolinecolor = "#555",
      title       = list(text = y_col, font = list(color = "#888"))
    ),
    legend        = list(font = list(color = "#888")),
    margin        = list(t = 50, r = 30, b = 60, l = 60),
    showlegend    = isTRUE(MostrarLeyenda)
  )

  # ── Construcción de traces ───────────────────────────────────────────────────
  traces <- list()

  if (is.null(color_vec)) {
    # Sin agrupación adicional — un único trace
    traces <- list(list(
      type       = "box",
      x          = x_vec,
      y          = y_vec,
      boxpoints  = boxpoints_val,
      marker     = list(color = "#d7a538"),
      line       = list(color = "#d7a538"),
      fillcolor  = paste0(substr("#d7a538", 1, 7), "66"),
      name       = y_col,
      hovertemplate = paste0("<b>%{x}</b><br>", y_col, ": %{y}<extra></extra>")
    ))
    layout <- layout_base

  } else {
    # Con agrupación adicional — un trace por grupo de Color
    grupos <- sort(unique(color_vec[!is.na(color_vec)]))
    for (i in seq_along(grupos)) {
      grupo   <- grupos[i]
      mascara <- !is.na(color_vec) & color_vec == grupo
      col_hex <- colores[((i - 1L) %% length(colores)) + 1L]

      traces[[i]] <- list(
        type       = "box",
        x          = x_vec[mascara],
        y          = y_vec[mascara],
        name       = grupo,
        boxpoints  = boxpoints_val,
        marker     = list(color = col_hex),
        line       = list(color = col_hex),
        fillcolor  = paste0(substr(col_hex, 1, 7), "66"),
        hovertemplate = paste0("<b>", grupo, "</b><br>%{x}: %{y}<extra></extra>")
      )
    }
    layout <- c(layout_base, list(boxmode = "group"))
  }

  # ── Codificación Plotly → base64 → HTML ─────────────────────────────────────
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

  # ── Retorno ──────────────────────────────────────────────────────────────────
  return(r_object_to_slots(
    list(grafico = html_plotly),
    tier_map = c(grafico = 1L)
  ))
}
