# ===============================================================================
# NEVEN Data Lab — GR_Barras: Grafico de Barras
# ===============================================================================
# Roles:
#   data_X     : data.frame con columna categorica o numerica (eje X)
#                opcional — si no se asigna, usa indice 1..N
#   data_Y     : data.frame con columna numerica (eje Y / valores)
#   data_Color : data.frame opcional con columna texto (agrupacion)
# Parametros:
#   Titulo         : titulo del grafico (default "")
#   MostrarLeyenda : mostrar leyenda (default TRUE)
#   Modo           : 1=Vertical agrupado, 2=Horizontal agrupado,
#                    3=Vertical apilado, 4=Horizontal apilado (default 1)
#   MostrarValores : mostrar etiquetas de valor sobre las barras (default FALSE)
#   Ordenar        : 1=Original, 2=Mayor a menor, 3=Menor a mayor (default 1)
#   Paleta         : 1=NEVEN, 2=Viridis, 3=Plasma, 4=Set1, 5=Pastel (default 1)
# ===============================================================================

GR_Barras.Studio <- function(data_X,
                              data_Y,
                              data_Color     = NULL,
                              Titulo         = "",
                              MostrarLeyenda = TRUE,
                              Modo           = 1L,
                              MostrarValores = FALSE,
                              Ordenar        = 1L,
                              Paleta         = 1L) {

  # -- Helpers ------------------------------------------------------------------
  .check_col_not_all_na <- function(vec, nombre) {
    if (all(is.na(vec)))
      stop(sprintf("La columna '%s' no contiene valores validos (solo NA).", nombre))
  }

  .get_palette <- function(paleta_id, n) {
    paletas <- list(
      `1` = c("#d7a538","#888888","#c0392b","#2980b9","#27ae60",
              "#8e44ad","#e67e22","#16a085","#2c3e50","#f39c12"),
      `2` = c("#440154","#31688e","#35b779","#fde725",
              "#21908c","#5dc963","#bddf26","#addc30","#6ece58","#b5de2b"),
      `3` = c("#0d0887","#6a00a8","#b12a90","#e16462",
              "#fca636","#f0f921","#cc4778","#7e03a8","#ed7953","#fdca26"),
      `4` = c("#e41a1c","#377eb8","#4daf4a","#984ea3",
              "#ff7f00","#ffff33","#a65628","#f781bf","#999999","#66c2a5"),
      `5` = c("#fbb4ae","#b3cde3","#ccebc5","#decbe4",
              "#fed9a6","#ffffcc","#e5d8bd","#fddaec","#f2f2f2","#8dd3c7")
    )
    key  <- as.character(as.integer(paleta_id))
    cols <- if (key %in% names(paletas)) paletas[[key]] else paletas[["1"]]
    cols[((seq_len(n) - 1L) %% length(cols)) + 1L]
  }

  # -- Validacion data_X --------------------------------------------------------
  if (!is.data.frame(data_X)) stop("'data_X' debe ser un data.frame.")
  data_X <- as.data.frame(data_X)
  if (nrow(data_X) == 0) stop("El filtro no retorna filas. Verifique la clausula WHERE.")

  # -- Validacion data_Y --------------------------------------------------------
  if (!is.data.frame(data_Y)) stop("'data_Y' debe ser un data.frame.")
  data_Y <- as.data.frame(data_Y)
  if (nrow(data_Y) == 0) stop("'data_Y' no contiene filas.")
  if (nrow(data_X) != nrow(data_Y))
    stop("'data_X' y 'data_Y' deben tener el mismo numero de filas.")

  y_num_cols <- names(data_Y)[sapply(data_Y, is.numeric)]
  if (length(y_num_cols) == 0)
    stop("'data_Y' debe contener al menos una columna numerica.")

  # -- Extraccion de vectores ---------------------------------------------------
  x_col_name <- names(data_X)[1]
  x_vec      <- data_X[[x_col_name]]

  # Con multiples Y y sin Color, creamos una traza por columna Y
  # Con Color asignado usamos solo la primera Y (agrupacion por color ya crea multiples trazas)
  if (!is.null(data_Color) || length(y_num_cols) == 1L) {
    y_col_name <- y_num_cols[1]
    y_vec      <- as.numeric(data_Y[[y_col_name]])
    .check_col_not_all_na(y_vec, y_col_name)
    multi_y <- FALSE
  } else {
    # Verificar que todas las columnas Y sean validas
    for (yc in y_num_cols) {
      .check_col_not_all_na(as.numeric(data_Y[[yc]]), yc)
    }
    y_col_name <- y_num_cols[1]  # referencia para etiquetas de ejes
    y_vec      <- as.numeric(data_Y[[y_col_name]])
    multi_y    <- TRUE
  }

  # -- Coercion de parametros ---------------------------------------------------
  Modo           <- as.integer(Modo)
  if (!Modo %in% 1L:4L) Modo <- 1L
  Ordenar        <- as.integer(Ordenar)
  if (!Ordenar %in% 1L:3L) Ordenar <- 1L
  MostrarValores <- isTRUE(MostrarValores)

  # Derivar orientacion y barmode desde Modo
  # Modo 1: vertical agrupado | 2: horizontal agrupado
  # Modo 3: vertical apilado  | 4: horizontal apilado
  es_horizontal <- Modo %in% c(2L, 4L)
  es_apilado    <- Modo %in% c(3L, 4L)
  barmode       <- if (es_apilado) "stack" else "group"
  orientacion   <- if (es_horizontal) "h" else "v"

  # Posicion de etiquetas segun orientacion
  text_position <- if (es_horizontal) "auto" else "outside"

  # -- Ordenamiento ------------------------------------------------------------
  # Con o sin grupos, ordenamos por valor Y (suma por categoría si hay grupos)
  if (Ordenar %in% c(2L, 3L)) {
    if (!is.null(data_Color)) {
      # Con grupos: ordenar por suma total de Y por categoría X
      agg <- tapply(y_vec, x_vec, sum, na.rm = TRUE)
      if (Ordenar == 2L) {
        cat_order <- names(sort(agg, decreasing = TRUE))
      } else {
        cat_order <- names(sort(agg, decreasing = FALSE))
      }
      orden_idx <- order(match(as.character(x_vec), cat_order))
    } else {
      if (Ordenar == 2L) {
        orden_idx <- order(y_vec, decreasing = TRUE)
      } else {
        orden_idx <- order(y_vec, decreasing = FALSE)
      }
    }
  } else {
    orden_idx <- seq_along(x_vec)
  }
  x_vec <- x_vec[orden_idx]
  y_vec <- y_vec[orden_idx]

  # -- Construccion de traces ---------------------------------------------------
  if (!is.null(data_Color)) {
    data_Color <- as.data.frame(data_Color)
    if (nrow(data_Color) != nrow(data_X))
      stop("'data_Color' debe tener el mismo numero de filas que 'data_X'.")
    color_vec  <- as.character(data_Color[[1]])[orden_idx]
    grupos     <- unique(color_vec)
    grupo_cols <- .get_palette(Paleta, length(grupos))

    traces <- lapply(seq_along(grupos), function(i) {
      g     <- grupos[i]
      mask  <- color_vec == g
      x_g   <- x_vec[mask]
      y_g   <- y_vec[mask]

      tr <- list(
        type      = "bar",
        name      = g,
        marker    = list(color = grupo_cols[i])
      )

      if (es_horizontal) {
        tr$orientation   <- "h"
        tr$x             <- y_g
        tr$y             <- x_g
        tr$hovertemplate <- paste0(g, "<br>%{y}: %{x:.4g}<extra></extra>")
        if (MostrarValores) {
          tr$text          <- format(round(y_g, 2), big.mark = ",", scientific = FALSE)
          tr$textposition  <- text_position
          tr$textfont      <- list(color = "#ccc", size = 9L)
        }
      } else {
        tr$x             <- x_g
        tr$y             <- y_g
        tr$hovertemplate <- paste0(g, "<br>%{x}: %{y:.4g}<extra></extra>")
        if (MostrarValores) {
          tr$text          <- format(round(y_g, 2), big.mark = ",", scientific = FALSE)
          tr$textposition  <- text_position
          tr$textfont      <- list(color = "#ccc", size = 9L)
        }
      }
      tr
    })

  } else {
    # Traza unica (o multiples Y)
    default_cols <- .get_palette(Paleta, length(y_num_cols))

    if (isTRUE(multi_y)) {
      # Una traza por columna Y
      traces <- lapply(seq_along(y_num_cols), function(i) {
        yc    <- y_num_cols[i]
        yv    <- as.numeric(data_Y[[yc]])[orden_idx]
        tr    <- list(type = "bar", name = yc,
                      marker = list(color = default_cols[i]))
        if (es_horizontal) {
          tr$orientation   <- "h"
          tr$x             <- yv
          tr$y             <- x_vec
          tr$hovertemplate <- paste0(yc, "<br>%{y}: %{x:.4g}<extra></extra>")
          if (MostrarValores) {
            tr$text        <- format(round(yv, 2), big.mark = ",", scientific = FALSE)
            tr$textposition <- text_position
            tr$textfont     <- list(color = "#ccc", size = 9L)
          }
        } else {
          tr$x             <- x_vec
          tr$y             <- yv
          tr$hovertemplate <- paste0(yc, "<br>%{x}: %{y:.4g}<extra></extra>")
          if (MostrarValores) {
            tr$text        <- format(round(yv, 2), big.mark = ",", scientific = FALSE)
            tr$textposition <- text_position
            tr$textfont     <- list(color = "#ccc", size = 9L)
          }
        }
        tr
      })
    } else {
      tr <- list(
        type   = "bar",
        name   = y_col_name,
        marker = list(color = default_cols[1])
      )
      if (es_horizontal) {
        tr$orientation   <- "h"
        tr$x             <- y_vec
        tr$y             <- x_vec
        tr$hovertemplate <- "%{y}: %{x:.4g}<extra></extra>"
        if (MostrarValores) {
          tr$text         <- format(round(y_vec, 2), big.mark = ",", scientific = FALSE)
          tr$textposition <- text_position
          tr$textfont     <- list(color = "#ccc", size = 9L)
        }
      } else {
        tr$x             <- x_vec
        tr$y             <- y_vec
        tr$hovertemplate <- "%{x}: %{y:.4g}<extra></extra>"
        if (MostrarValores) {
          tr$text         <- format(round(y_vec, 2), big.mark = ",", scientific = FALSE)
          tr$textposition <- text_position
          tr$textfont     <- list(color = "#ccc", size = 9L)
        }
      }
      traces <- list(tr)
    }
  }

  # -- Layout -------------------------------------------------------------------
  titulo_texto <- if (nchar(trimws(as.character(Titulo))) > 0) as.character(Titulo) else NULL

  layout <- list(
    paper_bgcolor = "#373434",
    plot_bgcolor  = "#373434",
    font          = list(color = "#888"),
    barmode       = barmode,
    showlegend    = isTRUE(MostrarLeyenda),
    xaxis         = list(
      color         = "#888",
      gridcolor     = "#333",
      zerolinecolor = "#555"
    ),
    yaxis         = list(
      color         = "#888",
      gridcolor     = "#333",
      zerolinecolor = "#555"
    ),
    legend        = list(font = list(color = "#888")),
    margin        = list(t = 50, r = 30, b = 60, l = 60)
  )

  # Dar espacio extra arriba cuando se muestran etiquetas fuera de la barra
  if (MostrarValores && !es_horizontal && !es_apilado)
    layout$yaxis$range <- list(0, max(y_vec, na.rm = TRUE) * 1.15)

  if (!is.null(titulo_texto))
    layout$title <- list(text = titulo_texto, font = list(color = "#e0e0e0", size = 14L))

  # -- Codificacion base64 ------------------------------------------------------
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
