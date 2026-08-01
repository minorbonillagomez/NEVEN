# ===============================================================================
# NEVEN Data Lab — EJEMPLO BÁSICO: Gráfico Personalizado (GR Family)
# ===============================================================================
# INSTRUCCIONES PARA EL USUARIO:
#
# Este archivo muestra el patrón MÍNIMO para crear un gráfico en Data Lab.
# Pasos:
#   1. Copia este archivo a C:\NEVEN\functions\ con un nuevo nombre
#      Ejemplo: MiGrafico.Studio.R
#   2. Copia el archivo GR_EjemploBasico.json a C:\NEVEN\functions\
#      con el mismo nuevo nombre: MiGrafico.json
#   3. Edita ambos archivos:
#      - En el .R: cambia el nombre de la función y adapta el gráfico
#      - En el .json: cambia "id" y "function_name" al nuevo nombre
#   4. Reinicia NEVEN Studio
#   5. Tu gráfico aparece en Data Lab bajo la familia "Gráficos"
#
# REGLAS:
#   - La función DEBE terminar en .Studio
#   - Siempre retornar r_object_to_slots()
#   - Para gráficos Plotly: usar <neven-plotly>BASE64</neven-plotly>
#   - Para gráficos Leaflet: retornar HTML puro (ver GR_Mapa.Studio.R)
# ===============================================================================

GR_EjemploBasico.Studio <- function(data_X,
                                     data_Y,
                                     MostrarLeyenda = TRUE,
                                     Paleta         = 1L) {

  # ── SECCIÓN 1: Validación de data_X ─────────────────────────────────────────
  # Siempre verifica que la entrada sea un data.frame y tenga filas.
  # El mensaje de error debe estar en español y ser descriptivo.
  if (!is.data.frame(data_X))
    stop("'data_X' debe ser un data.frame.")
  if (nrow(data_X) == 0)
    stop("El filtro aplicado no retorna filas para el eje X. Verifique la cláusula WHERE.")

  # ── SECCIÓN 2: Validación de data_Y ─────────────────────────────────────────
  # data_Y debe tener el mismo número de filas que data_X para que el par
  # (x_vec[i], y_vec[i]) tenga sentido como punto en el scatter.
  if (!is.data.frame(data_Y))
    stop("'data_Y' debe ser un data.frame.")
  if (nrow(data_Y) == 0)
    stop("El filtro aplicado no retorna filas para el eje Y. Verifique la cláusula WHERE.")
  if (nrow(data_X) != nrow(data_Y))
    stop("'data_X' y 'data_Y' deben tener el mismo número de filas.")

  # ── SECCIÓN 3: Extracción de vectores numéricos ──────────────────────────────
  # Tomamos la PRIMERA columna numérica de cada rol.
  # Si no hay ninguna columna numérica, lanzamos un error claro.
  x_cols <- names(data_X)[sapply(data_X, is.numeric)]
  if (length(x_cols) == 0)
    stop("'data_X' debe contener al menos una columna numérica para el eje X.")
  x_col <- x_cols[1]                           # columna a usar
  x_vec <- as.numeric(data_X[[x_col]])

  y_cols <- names(data_Y)[sapply(data_Y, is.numeric)]
  if (length(y_cols) == 0)
    stop("'data_Y' debe contener al menos una columna numérica para el eje Y.")
  y_col <- y_cols[1]                           # columna a usar
  y_vec <- as.numeric(data_Y[[y_col]])

  # ── SECCIÓN 4: Paleta de color ───────────────────────────────────────────────
  # Definimos 5 paletas. Para un scatter de un solo color, usamos colors[1].
  # En un gráfico más avanzado (ver GR_EjemploAvanzado), iteraríamos sobre
  # colors[i] para cada grupo.
  Paleta <- as.integer(Paleta)
  if (is.na(Paleta) || Paleta < 1L || Paleta > 5L) Paleta <- 1L

  paletas <- list(
    `1` = c("#d7a538", "#888888", "#c08820", "#aaaaaa", "#e8c060"),  # NEVEN dorado
    `2` = c("#440154", "#3b528b", "#21908d", "#5dc963", "#fde725"),  # Viridis
    `3` = c("#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636"),  # Plasma
    `4` = c("#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"),  # Set1 categórico
    `5` = c("#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6")   # Pastel
  )
  # Para un scatter de un solo trace, siempre usamos el primer color de la paleta
  color_trace <- paletas[[as.character(Paleta)]][1]

  # ── SECCIÓN 5: Construcción del trace Plotly ─────────────────────────────────
  # Un "trace" es la unidad básica de datos en Plotly.
  # type="scatter" + mode="markers" = gráfico de dispersión (puntos).
  # hovertemplate controla qué aparece al pasar el mouse sobre un punto.
  traces <- list(
    list(
      type          = "scatter",
      mode          = "markers",
      name          = y_col,                                           # etiqueta en leyenda
      x             = x_vec,
      y             = y_vec,
      marker        = list(
        color   = color_trace,                                         # color del punto
        size    = 8,                                                   # tamaño fijo
        opacity = 0.85,
        line    = list(color = "#2a2a2a", width = 0.5)                # borde oscuro
      ),
      hovertemplate = paste0(x_col, ": %{x}<br>", y_col, ": %{y}<extra></extra>"),
      showlegend    = isTRUE(MostrarLeyenda)
    )
  )

  # ── SECCIÓN 6: Construcción del layout (tema oscuro NEVEN) ──────────────────
  # Todos los gráficos GR usan el mismo tema oscuro para consistencia visual:
  #   - paper_bgcolor y plot_bgcolor: "#373434" (gris oscuro)
  #   - font color: "#888" (gris claro)
  #   - gridcolor: "#333"
  # NO cambies estos colores en tus propias funciones si quieres mantener
  # la coherencia visual con el resto de Data Lab.
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
    margin     = list(t = 40, r = 30, b = 60, l = 60)
  )

  # ── SECCIÓN 7: Codificación base64 → HTML ────────────────────────────────────
  # Plotly en NEVEN se transmite como JSON codificado en base64, embebido en
  # la etiqueta <neven-plotly>. El tryCatch garantiza que un error de
  # serialización no rompa la ejecución — retorna un mensaje de error HTML
  # en su lugar, que se muestra limpiamente en el panel de Data Lab.
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

  # ── SECCIÓN 8: Retorno con r_object_to_slots() ───────────────────────────────
  # SIEMPRE retorna usando r_object_to_slots().
  # - El nombre del slot ("grafico") es el que aparece como título en Data Lab.
  # - tier_map=1L → se muestra expandido por defecto.
  # - tier_map=2L → aparece en la sección "Detalles técnicos" (colapsada).
  return(r_object_to_slots(
    list(grafico = html_plotly),
    tier_map = c(grafico = 1L)
  ))
}
