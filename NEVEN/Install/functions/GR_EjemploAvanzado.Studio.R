# ===============================================================================
# NEVEN Data Lab — EJEMPLO AVANZADO: Gráfico de Burbujas (GR Family)
# ===============================================================================
# INSTRUCCIONES PARA EL USUARIO:
#
# Este archivo muestra el patrón COMPLETO para crear un gráfico en Data Lab.
# A diferencia del ejemplo básico, aquí se demuestran:
#
#   PATRÓN AVANZADO — qué aprenderás de este archivo:
#
#   1. CUATRO ROLES: X e Y (requeridos) + Color y Tamaño (opcionales).
#      Los roles opcionales reciben NULL cuando el usuario no asigna columnas,
#      y el código los maneja con gracia sin lanzar error.
#
#   2. ROLES OPCIONALES GRACEFUL: cada bloque "if (!is.null(...))" muestra
#      cómo detectar si el rol fue asignado o no, y cómo tener un valor
#      por defecto sensato cuando está ausente.
#
#   3. HOVERTEMPLATE PERSONALIZADO: construimos el tooltip dinámicamente
#      según qué roles están presentes — básico (solo X,Y) o completo
#      (X, Y, grupo, tamaño).
#
#   4. NORMALIZACIÓN DE TAMAÑO: cuando el rol Tamaño está presente,
#      escalamos los valores al rango 8–40 píxeles para que las burbujas
#      sean visualmente comparables.
#
#   5. PARÁMETROS TIER 1 Y TIER 2:
#      - Tier 1 (MostrarLeyenda, ModoHover): controles que el usuario ve
#        siempre, porque afectan la legibilidad básica del gráfico.
#      - Tier 2 (Paleta, Opacidad): ajustes estéticos que van en la sección
#        "Detalles técnicos" colapsada — no abruman al usuario casual.
#
#   6. OPACIDAD COMO ENTERO 0–100: el usuario ingresa un valor entero
#      (más intuitivo), y lo convertimos a 0.0–1.0 para Plotly.
#
# REGLAS (aplican a todos los gráficos GR):
#   - La función DEBE terminar en .Studio
#   - Siempre retornar r_object_to_slots()
#   - Para gráficos Plotly: usar <neven-plotly>BASE64</neven-plotly>
#   - Para gráficos Leaflet: retornar HTML puro (ver GR_Mapa.Studio.R)
# ===============================================================================

GR_EjemploAvanzado.Studio <- function(data_X,
                                       data_Y,
                                       data_Color  = NULL,
                                       data_Tamaño = NULL,
                                       MostrarLeyenda = TRUE,
                                       ModoHover      = 1L,
                                       Paleta         = 1L,
                                       Opacidad       = 80L) {

  # ── SECCIÓN 1: Validación de data_X (rol requerido) ─────────────────────────
  # Los roles requeridos deben validarse siempre. Mensajes en español.
  if (!is.data.frame(data_X))
    stop("'data_X' debe ser un data.frame.")
  if (nrow(data_X) == 0)
    stop("El filtro aplicado no retorna filas para el eje X. Verifique la cláusula WHERE.")

  # ── SECCIÓN 2: Validación de data_Y (rol requerido) ─────────────────────────
  if (!is.data.frame(data_Y))
    stop("'data_Y' debe ser un data.frame.")
  if (nrow(data_Y) == 0)
    stop("El filtro aplicado no retorna filas para el eje Y. Verifique la cláusula WHERE.")
  if (nrow(data_X) != nrow(data_Y))
    stop("'data_X' y 'data_Y' deben tener el mismo número de filas.")

  # ── SECCIÓN 3: Extracción de vectores numéricos de X e Y ────────────────────
  x_cols <- names(data_X)[sapply(data_X, is.numeric)]
  if (length(x_cols) == 0)
    stop("'data_X' debe contener al menos una columna numérica para el eje X.")
  x_col <- x_cols[1]
  x_vec <- as.numeric(data_X[[x_col]])

  y_cols <- names(data_Y)[sapply(data_Y, is.numeric)]
  if (length(y_cols) == 0)
    stop("'data_Y' debe contener al menos una columna numérica para el eje Y.")
  y_col <- y_cols[1]
  y_vec <- as.numeric(data_Y[[y_col]])

  # ── SECCIÓN 4: Extracción del rol Color (OPCIONAL) ──────────────────────────
  # PATRÓN CLAVE: comprobamos is.null Y is.data.frame Y ncol > 0.
  # Si el usuario no asigna este rol, data_Color llega como NULL.
  # Si llega como data.frame vacío o sin columnas, lo tratamos como ausente.
  color_vec  <- NULL
  color_name <- NULL
  if (!is.null(data_Color) && is.data.frame(data_Color) && ncol(data_Color) > 0) {
    color_name <- names(data_Color)[1]
    color_vec  <- as.character(data_Color[[color_name]])  # convertir a texto para grupos
    if (nrow(data_Color) != nrow(data_X))
      stop("'data_Color' debe tener el mismo número de filas que 'data_X'.")
  }

  # ── SECCIÓN 5: Extracción y normalización del rol Tamaño (OPCIONAL) ─────────
  # Si el rol está presente, normalizamos al rango 8–40 px.
  # La normalización lineal garantiza que el punto más pequeño tenga 8 px
  # y el más grande 40 px, independientemente de la escala original del dato.
  # Si todos los valores son iguales (rng[1] == rng[2]), usamos tamaño fijo 20.
  size_vec  <- NULL
  size_name <- NULL
  if (!is.null(data_Tamaño) && is.data.frame(data_Tamaño) && ncol(data_Tamaño) > 0) {
    sz_cols <- names(data_Tamaño)[sapply(data_Tamaño, is.numeric)]
    if (length(sz_cols) == 0)
      stop("'data_Tamaño' debe contener al menos una columna numérica.")
    if (nrow(data_Tamaño) != nrow(data_X))
      stop("'data_Tamaño' debe tener el mismo número de filas que 'data_X'.")
    size_name <- sz_cols[1]
    raw_size  <- as.numeric(data_Tamaño[[size_name]])
    rng       <- range(raw_size, na.rm = TRUE)
    if (rng[1] == rng[2]) {
      # Todos los valores son iguales → tamaño fijo intermedio
      size_vec <- rep(20, length(raw_size))
    } else {
      # Normalización lineal al rango [8, 40]
      size_vec <- 8 + (raw_size - rng[1]) / (rng[2] - rng[1]) * 32
    }
    size_vec[is.na(size_vec)] <- 12   # NA → tamaño por defecto
  }

  # ── SECCIÓN 6: Parámetros numéricos con coerción y validación ───────────────
  # Opacidad llega como entero 0–100; Plotly la espera como 0.0–1.0.
  Opacidad <- as.integer(Opacidad)
  if (is.na(Opacidad) || Opacidad < 0L)   Opacidad <- 0L
  if (Opacidad > 100L)                    Opacidad <- 100L
  opacidad_plotly <- Opacidad / 100       # conversión al rango Plotly

  ModoHover <- as.integer(ModoHover)
  if (is.na(ModoHover) || ModoHover < 1L || ModoHover > 2L) ModoHover <- 1L

  Paleta <- as.integer(Paleta)
  if (is.na(Paleta) || Paleta < 1L || Paleta > 5L) Paleta <- 1L

  # ── SECCIÓN 7: Paleta de colores ─────────────────────────────────────────────
  # Cuando hay grupos (color_vec), iteramos sobre la paleta con módulo para
  # no quedarnos sin colores aunque haya más grupos que colores en la paleta.
  paletas <- list(
    `1` = c("#d7a538", "#888888", "#c08820", "#aaaaaa", "#e8c060",
            "#666666", "#f0d080", "#444444"),                          # NEVEN dorado
    `2` = c("#440154", "#3b528b", "#21908d", "#5dc963", "#fde725",
            "#482878", "#27ad81", "#95d840"),                          # Viridis
    `3` = c("#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636",
            "#f0f921", "#cb4679", "#7e03a8"),                          # Plasma
    `4` = c("#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
            "#a65628", "#f781bf", "#999999"),                          # Set1 categórico
    `5` = c("#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6",
            "#ffffcc", "#e5d8bd", "#fddaec")                           # Pastel
  )
  color_palette <- paletas[[as.character(Paleta)]]
  default_color <- color_palette[1]   # color para trace único (sin grupos)

  # ── SECCIÓN 8: Construcción del hovertemplate ─────────────────────────────
  # ModoHover=1 (Básico): solo X e Y — no satura al usuario con información.
  # ModoHover=2 (Completo): añade grupo y tamaño si están presentes.
  # La etiqueta <extra></extra> elimina el nombre del trace del tooltip.
  build_hover <- function(modo, has_color, has_size, x_col, y_col,
                          color_name, size_name) {
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

  # ── SECCIÓN 9: Construcción de trace(s) Plotly ───────────────────────────────
  # DECISIÓN DE DISEÑO: si hay grupos (color_vec presente), creamos UN TRACE
  # por grupo. Esto permite a Plotly manejar la leyenda automáticamente y
  # al usuario hacer clic en la leyenda para mostrar/ocultar grupos.
  # Si no hay grupos, un único trace es más eficiente.
  traces <- list()

  if (!is.null(color_vec)) {
    # ── RAMA: un trace por grupo ──────────────────────────────────────────────
    grupos <- unique(color_vec)
    grupos <- grupos[!is.na(grupos)]

    for (i in seq_along(grupos)) {
      grp       <- grupos[i]
      idx       <- which(color_vec == grp)
      grp_color <- color_palette[((i - 1L) %% length(color_palette)) + 1L]

      # El tamaño del marcador puede ser un escalar (fijo) o un vector (variable)
      marker_size <- if (!is.null(size_vec)) size_vec[idx] else 12

      tr <- list(
        type          = "scatter",
        mode          = "markers",
        name          = as.character(grp),   # etiqueta del grupo en la leyenda
        x             = x_vec[idx],
        y             = y_vec[idx],
        meta          = rep(as.character(grp), length(idx)),  # para %{meta} en hover
        marker        = list(
          color   = grp_color,
          size    = marker_size,
          opacity = opacidad_plotly,
          line    = list(color = "#2a2a2a", width = 0.5)
        ),
        hovertemplate = hover_tmpl,
        showlegend    = isTRUE(MostrarLeyenda)
      )
      traces <- c(traces, list(tr))
    }

    # Filas con NA en color_vec → trace separado sin grupo
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
    # ── RAMA: trace único sin agrupación ─────────────────────────────────────
    # Cuando no hay grupos, un solo trace con el color por defecto de la paleta.
    tr <- list(
      type          = "scatter",
      mode          = "markers",
      name          = y_col,
      x             = x_vec,
      y             = y_vec,
      marker        = list(
        color   = default_color,
        size    = if (!is.null(size_vec)) size_vec else 12,  # vector o escalar
        opacity = opacidad_plotly,
        line    = list(color = "#2a2a2a", width = 0.5)
      ),
      hovertemplate = hover_tmpl,
      showlegend    = isTRUE(MostrarLeyenda)
    )
    traces <- list(tr)
  }

  # ── SECCIÓN 10: Construcción del layout (tema oscuro NEVEN) ─────────────────
  # Mismos colores que todos los demás gráficos GR: coherencia visual.
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
    legend = list(
      font        = list(color = "#888"),
      bgcolor     = "#373434",
      bordercolor = "#555"
    ),
    showlegend = isTRUE(MostrarLeyenda),
    margin     = list(t = 40, r = 30, b = 60, l = 60)
  )

  # ── SECCIÓN 11: Codificación base64 → HTML ───────────────────────────────────
  # Idéntico al patrón de GR_EjemploBasico. El tryCatch es obligatorio:
  # nunca debe romperse la ejecución por un fallo de serialización JSON.
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

  # ── SECCIÓN 12: Retorno con r_object_to_slots() ──────────────────────────────
  # Igual que en el ejemplo básico. El nombre "grafico" aparece como título
  # del slot en Data Lab. tier_map=1L = expandido por defecto.
  return(r_object_to_slots(
    list(grafico = html_plotly),
    tier_map = c(grafico = 1L)
  ))
}
