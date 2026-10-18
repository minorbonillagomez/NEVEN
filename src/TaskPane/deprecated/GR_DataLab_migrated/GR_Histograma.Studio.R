# ===============================================================================
# NEVEN Data Lab — GR_Histograma: Histograma univariado (Plotly)
# ===============================================================================
# Distribucion de frecuencias de una variable numerica.
# Muestra la forma de la distribucion, moda y dispersion.
#
# Parametros:
#   data_X          data.frame con la columna numerica a distribuir (rol X)
#   Bins            Numero de intervalos (bins); default 30; si <=0 se usa 30
#   MostrarDensidad Si TRUE, agrega histnorm="probability density" a la traza
#   Paleta          Paleta de colores: 1=NEVEN(dorado), 2=Viridis, 3=Plasma,
#                   4=Set1(categorico), 5=Pastel
#
# Retorna:
#   r_object_to_slots(list(grafico = html_plotly), tier_map = c(grafico = 1L))
#   El slot "grafico" es de tipo "html" con el patron:
#   <html><body><neven-plotly>BASE64</neven-plotly></body></html>
# ===============================================================================

GR_Histograma.Studio <- function(data_X,
                                   Bins            = 30L,
                                   MostrarDensidad = FALSE,
                                   Paleta          = 1L) {

  # ── Validacion de data_X ────────────────────────────────────────────────────
  if (!is.data.frame(data_X))
    stop("'data_X' debe ser un data.frame.")

  data_X <- as.data.frame(data_X)

  if (nrow(data_X) == 0)
    stop("El filtro aplicado no retorna filas. Verifique la clausula WHERE.")

  # Detectar primera columna numerica
  num_cols <- names(data_X)[sapply(data_X, is.numeric)]
  if (length(num_cols) == 0)
    stop("'data_X' no contiene columnas numericas. Asigne una columna de tipo numerico al rol X.")

  x_col <- num_cols[1]
  x_vec <- as.numeric(data_X[[x_col]])

  # Verificar que no sea todo-NA
  if (all(is.na(x_vec)))
    stop(sprintf("La columna '%s' no contiene valores validos (solo NA).", x_col))

  # Validar que hay al menos 2 filas con datos validos
  if (sum(!is.na(x_vec)) < 2)
    stop(sprintf("La columna '%s' requiere al menos 2 valores no-NA para construir un histograma.", x_col))

  # ── Validacion de Bins ──────────────────────────────────────────────────────
  Bins <- suppressWarnings(as.integer(Bins))
  if (is.na(Bins) || Bins <= 0L) Bins <- 30L

  # ── Paleta de colores ───────────────────────────────────────────────────────
  # Colores de relleno de barra segun paleta seleccionada
  .paleta_colores <- c(
    "#d7a538",   # 1 = NEVEN dorado
    "#1f77b4",   # 2 = Viridis (azul representativo)
    "#9b59b6",   # 3 = Plasma (purpura representativo)
    "#e74c3c",   # 4 = Set1  (rojo representativo)
    "#f39c12"    # 5 = Pastel (naranja pastel representativo)
  )

  Paleta    <- suppressWarnings(as.integer(Paleta))
  if (is.na(Paleta) || Paleta < 1L || Paleta > length(.paleta_colores)) Paleta <- 1L
  bar_color <- .paleta_colores[Paleta]

  # ── Construccion del trace Plotly ───────────────────────────────────────────
  trace <- list(
    type   = "histogram",
    x      = x_vec,
    nbinsx = Bins,
    name   = x_col,
    marker = list(
      color = bar_color,
      line  = list(color = "#373434", width = 1)
    ),
    hovertemplate = "%{x}: %{y}<extra></extra>"
  )

  # Densidad de probabilidad opcional
  if (isTRUE(MostrarDensidad)) {
    trace[["histnorm"]] <- "probability density"
  }

  traces <- list(trace)

  # ── Layout con tema oscuro estandar ─────────────────────────────────────────
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
      color      = "#888",
      gridcolor  = "#333",
      zerolinecolor = "#555"
    ),
    showlegend = FALSE,
    margin     = list(t = 50, r = 30, b = 60, l = 60)
  )

  # ── Codificacion base64 dentro de tryCatch ──────────────────────────────────
  html_plotly <- tryCatch({
    fig_json <- iconv(
      jsonlite::toJSON(list(data = traces, layout = layout),
                       auto_unbox = TRUE, na = "null"),
      from = "UTF-8", to = "UTF-8", sub = "byte"
    )
    paste0(
      '<html><body><neven-plotly>',
      jsonlite::base64_enc(chartr("\n\r", "  ", fig_json)),
      '</neven-plotly></body></html>'
    )
  }, error = function(e) {
    paste0(
      '<html><body><p style="color:#888;padding:8px">',
      'Grafico no disponible: ', conditionMessage(e),
      '</p></body></html>'
    )
  })

  # ── Retorno estandar ─────────────────────────────────────────────────────────
  return(r_object_to_slots(
    list(grafico = html_plotly),
    tier_map = c(grafico = 1L)
  ))
}
