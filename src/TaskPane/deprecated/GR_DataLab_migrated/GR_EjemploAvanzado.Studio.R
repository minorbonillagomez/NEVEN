# ===============================================================================
# NEVEN Data Lab - EJEMPLO AVANZADO: Grafico de Burbujas (GR Family)
# ===============================================================================
# Roles:
#   data_X       data.frame - eje X (numerico, requerido)
#   data_Y       data.frame - eje Y (numerico, requerido)
#   data_Color   data.frame - agrupacion/color (texto, opcional)
#   data_Tamano  data.frame - tamano de burbujas (numerico, opcional)
# Parametros:
#   MostrarLeyenda logical  - mostrar leyenda (default TRUE)
#   ModoHover     integer   - 1=Basico, 2=Completo (default 1)
#   Paleta        integer   - 1=NEVEN, 2=Viridis, 3=Plasma, 4=Set1, 5=Pastel
#   Opacidad      integer   - 0-100 (default 80)
# ===============================================================================

GR_EjemploAvanzado.Studio <- function(data_X,
                                       data_Y,
                                       data_Color  = NULL,
                                       data_Tamano = NULL,
                                       MostrarLeyenda = TRUE,
                                       ModoHover      = 1L,
                                       Paleta         = 1L,
                                       Opacidad       = 80L) {

  # -- Validacion de data_X --------------------------------------------------
  if (!is.data.frame(data_X))
    stop("'data_X' debe ser un data.frame.")
  if (nrow(data_X) == 0)
    stop("El filtro aplicado no retorna filas para el eje X.")

  # -- Validacion de data_Y --------------------------------------------------
  if (!is.data.frame(data_Y))
    stop("'data_Y' debe ser un data.frame.")
  if (nrow(data_Y) == 0)
    stop("El filtro aplicado no retorna filas para el eje Y.")
  if (nrow(data_X) != nrow(data_Y))
    stop("'data_X' y 'data_Y' deben tener el mismo numero de filas.")

  # -- Extraccion de vectores numericos de X e Y ----------------------------
  x_cols <- names(data_X)[sapply(data_X, is.numeric)]
  if (length(x_cols) == 0)
    stop("'data_X' debe contener al menos una columna numerica para el eje X.")
  x_col <- x_cols[1]
  x_vec <- as.numeric(data_X[[x_col]])

  y_cols <- names(data_Y)[sapply(data_Y, is.numeric)]
  if (length(y_cols) == 0)
    stop("'data_Y' debe contener al menos una columna numerica para el eje Y.")
  y_col <- y_cols[1]
  y_vec <- as.numeric(data_Y[[y_col]])

  # -- Rol Color (OPCIONAL) --------------------------------------------------
  # Si Color es numerico: colorscale continua (un solo trace con marker.color=vector)
  # Si Color es texto: un trace por grupo (comportamiento de agrupacion)
  color_vec    <- NULL
  color_name   <- NULL
  color_is_num <- FALSE
  if (!is.null(data_Color) && is.data.frame(data_Color) && ncol(data_Color) > 0) {
    color_name <- names(data_Color)[1]
    if (nrow(data_Color) != nrow(data_X))
      stop("'data_Color' debe tener el mismo numero de filas que 'data_X'.")
    col_raw <- data_Color[[color_name]]
    if (is.numeric(col_raw)) {
      color_vec    <- as.numeric(col_raw)
      color_is_num <- TRUE
    } else {
      color_vec <- as.character(col_raw)
    }
  }

  # -- Rol Tamano (OPCIONAL) -------------------------------------------------
  size_vec  <- NULL
  size_name <- NULL
  if (!is.null(data_Tamano) && is.data.frame(data_Tamano) && ncol(data_Tamano) > 0) {
    sz_cols <- names(data_Tamano)[sapply(data_Tamano, is.numeric)]
    if (length(sz_cols) == 0)
      stop("'data_Tamano' debe contener al menos una columna numerica.")
    if (nrow(data_Tamano) != nrow(data_X))
      stop("'data_Tamano' debe tener el mismo numero de filas que 'data_X'.")
    size_name <- sz_cols[1]
    raw_size  <- as.numeric(data_Tamano[[size_name]])
    rng       <- range(raw_size, na.rm = TRUE)
    if (rng[1] == rng[2]) {
      size_vec <- rep(20, length(raw_size))
    } else {
      size_vec <- 8 + (raw_size - rng[1]) / (rng[2] - rng[1]) * 32
    }
    size_vec[is.na(size_vec)] <- 12
  }

  # -- Parametros numericos --------------------------------------------------
  Opacidad <- as.integer(Opacidad)
  if (is.na(Opacidad) || Opacidad < 0L)  Opacidad <- 0L
  if (Opacidad > 100L)                   Opacidad <- 100L
  opacidad_plotly <- Opacidad / 100

  ModoHover <- as.integer(ModoHover)
  if (is.na(ModoHover) || ModoHover < 1L || ModoHover > 2L) ModoHover <- 1L

  Paleta <- as.integer(Paleta)
  if (is.na(Paleta) || Paleta < 1L || Paleta > 5L) Paleta <- 1L

  # -- Paleta de colores -----------------------------------------------------
  paletas <- list(
    `1` = c("#d7a538","#888888","#c08820","#aaaaaa","#e8c060","#666666","#f0d080","#444444"),
    `2` = c("#440154","#3b528b","#21908d","#5dc963","#fde725","#482878","#27ad81","#95d840"),
    `3` = c("#0d0887","#6a00a8","#b12a90","#e16462","#fca636","#f0f921","#cb4679","#7e03a8"),
    `4` = c("#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00","#a65628","#f781bf","#999999"),
    `5` = c("#fbb4ae","#b3cde3","#ccebc5","#decbe4","#fed9a6","#ffffcc","#e5d8bd","#fddaec")
  )
  color_palette <- paletas[[as.character(Paleta)]]
  default_color <- color_palette[1]

  # -- Hovertemplate ---------------------------------------------------------
  build_hover <- function(modo, has_color, has_size, x_col, y_col, color_name, size_name) {
    base <- paste0(x_col, ": %{x}<br>", y_col, ": %{y}")
    if (modo == 2L) {
      if (has_color) base <- paste0(base, "<br>Grupo: %{meta}")
      if (has_size)  base <- paste0(base, "<br>", size_name, ": %{marker.size:.1f}")
    }
    paste0(base, "<extra></extra>")
  }

  hover_tmpl <- build_hover(
    modo       = ModoHover,
    has_color  = !is.null(color_vec),
    has_size   = !is.null(size_vec),
    x_col      = x_col,
    y_col      = y_col,
    color_name = color_name,
    size_name  = size_name
  )

  # -- Construccion de traces ------------------------------------------------
  traces <- list()

  if (!is.null(color_vec) && !color_is_num) {
    # ── Color categorico: un trace por grupo ──────────────────────────────
    grupos <- unique(color_vec)
    grupos <- grupos[!is.na(grupos)]

    for (i in seq_along(grupos)) {
      grp       <- grupos[i]
      idx       <- which(color_vec == grp)
      grp_color <- color_palette[((i - 1L) %% length(color_palette)) + 1L]

      tr <- list(
        type          = "scatter",
        mode          = "markers",
        name          = as.character(grp),
        x             = x_vec[idx],
        y             = y_vec[idx],
        meta          = rep(as.character(grp), length(idx)),
        marker        = list(
          color   = grp_color,
          size    = if (!is.null(size_vec)) size_vec[idx] else 12,
          opacity = opacidad_plotly,
          line    = list(color = "#2a2a2a", width = 0.5)
        ),
        hovertemplate = hover_tmpl,
        showlegend    = isTRUE(MostrarLeyenda)
      )
      traces <- c(traces, list(tr))
    }

    na_idx <- which(is.na(color_vec))
    if (length(na_idx) > 0) {
      tr_na <- list(
        type          = "scatter",
        mode          = "markers",
        name          = "(sin grupo)",
        x             = x_vec[na_idx],
        y             = y_vec[na_idx],
        marker        = list(
          color   = "#888888",
          size    = if (!is.null(size_vec)) size_vec[na_idx] else 12,
          opacity = opacidad_plotly,
          line    = list(color = "#2a2a2a", width = 0.5)
        ),
        hovertemplate = paste0(x_col, ": %{x}<br>", y_col, ": %{y}<extra></extra>"),
        showlegend    = isTRUE(MostrarLeyenda)
      )
      traces <- c(traces, list(tr_na))
    }

  } else {
    # ── Trace unico: sin color, o color numerico continuo ─────────────────
    # Seleccionar colorscale segun paleta
    colorscale_map <- list(
      `1` = list(list(0,"#444444"), list(0.5,"#888888"), list(1,"#d7a538")),
      `2` = list(list(0,"#440154"), list(0.5,"#21908c"), list(1,"#fde725")),
      `3` = list(list(0,"#0d0887"), list(0.5,"#b12a90"), list(1,"#f0f921")),
      `4` = list(list(0,"#e41a1c"), list(0.5,"#4daf4a"), list(1,"#377eb8")),
      `5` = list(list(0,"#fbb4ae"), list(0.5,"#ccebc5"), list(1,"#b3cde3"))
    )
    cs_key <- as.character(Paleta)
    colorscale <- if (cs_key %in% names(colorscale_map)) colorscale_map[[cs_key]] else colorscale_map[["1"]]

    marker_def <- list(
      size    = if (!is.null(size_vec)) size_vec else 12,
      opacity = opacidad_plotly,
      line    = list(color = "#2a2a2a", width = 0.5)
    )

    if (isTRUE(color_is_num)) {
      marker_def$color      <- color_vec
      marker_def$colorscale <- colorscale
      marker_def$showscale  <- TRUE
      marker_def$colorbar   <- list(
        title      = color_name,
        tickfont   = list(color = "#888", size = 9L),
        titlefont  = list(color = "#888", size = 10L),
        bgcolor    = "#373434",
        bordercolor= "#555"
      )
    } else {
      marker_def$color <- default_color
    }

    tr <- list(
      type          = "scatter",
      mode          = "markers",
      name          = y_col,
      x             = x_vec,
      y             = y_vec,
      marker        = marker_def,
      hovertemplate = hover_tmpl,
      showlegend    = isTRUE(MostrarLeyenda)
    )
    traces <- list(tr)
  }

  # -- Layout ----------------------------------------------------------------
  layout <- list(
    paper_bgcolor = "#373434",
    plot_bgcolor  = "#373434",
    font          = list(color = "#888"),
    xaxis = list(
      title         = list(text = x_col, font = list(color = "#888")),
      color         = "#888",
      gridcolor     = "#333",
      zerolinecolor = "#555"
    ),
    yaxis = list(
      title         = list(text = y_col, font = list(color = "#888")),
      color         = "#888",
      gridcolor     = "#333",
      zerolinecolor = "#555"
    ),
    legend     = list(font = list(color = "#888"), bgcolor = "#373434", bordercolor = "#555"),
    showlegend = isTRUE(MostrarLeyenda),
    margin     = list(t = 40, r = 30, b = 60, l = 60)
  )

  # -- Codificacion base64 -> HTML -------------------------------------------
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
           'Grafico no disponible: ', conditionMessage(e),
           '</p></body></html>')
  })

  return(r_object_to_slots(
    list(grafico = html_plotly),
    tier_map = c(grafico = 1L)
  ))
}
