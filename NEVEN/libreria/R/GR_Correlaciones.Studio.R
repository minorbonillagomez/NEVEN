# ===============================================================================
# NEVEN Data Lab — GR_Correlaciones.Studio: Mapa de Correlaciones
# ===============================================================================
# Genera un heatmap interactivo de la matriz de correlaciones entre variables
# numéricas. Soporta los métodos Pearson, Spearman y Kendall. Las celdas pueden
# mostrar el valor numérico redondeado a 2 decimales.
#
# Parámetros:
#   data_X         data.frame con ≥2 columnas numéricas (columnas no numéricas
#                  se omiten silenciosamente)
#   Metodo         entero 1–3 — método de correlación:
#                    1 = Pearson (lineal, default)
#                    2 = Spearman (rangos)
#                    3 = Kendall (tau)
#   MostrarValores lógico — mostrar el valor de correlación en cada celda
#   Paleta         entero 1–5 — paleta de colores del heatmap:
#                    1 = RdBu invertida (divergente, recomendada para correlaciones)
#                    2 = Viridis
#                    3 = Plasma
#                    4 = Portland
#                    5 = Picnic
# ===============================================================================

GR_Correlaciones.Studio <- function(data_X,
                                    Metodo         = 1L,
                                    MostrarValores = TRUE,
                                    Paleta         = 1L) {

  # ── Validación de data_X ─────────────────────────────────────────────────────
  if (!is.data.frame(data_X))
    stop("'data_X' debe ser un data.frame.")
  if (nrow(data_X) == 0)
    stop("El filtro aplicado no retorna filas. Verifique la cláusula WHERE.")

  # ── Extraer solo columnas numéricas (omitir no-numéricas silenciosamente) ────
  num_cols <- names(data_X)[sapply(data_X, is.numeric)]
  if (length(num_cols) < 2L)
    stop("Se requieren al menos 2 columnas numéricas para el mapa de correlaciones.")

  data_num <- data_X[, num_cols, drop = FALSE]

  # ── Validación y normalización de Metodo ─────────────────────────────────────
  Metodo <- as.integer(Metodo)
  if (is.na(Metodo) || Metodo < 1L || Metodo > 3L) Metodo <- 1L
  metodo_str <- c("pearson", "spearman", "kendall")[Metodo]

  # ── Cálculo de la matriz de correlaciones ─────────────────────────────────────
  cor_matrix <- cor(data_num, method = metodo_str, use = "complete.obs")

  col_names <- colnames(cor_matrix)

  # ── Definición de colorscales ────────────────────────────────────────────────
  # Paleta 1: RdBu invertida (azul=correlación positiva, rojo=negativa)
  # Invertir RdBu: el -1 queda en azul oscuro, el +1 en rojo oscuro
  cs_rdbu_rev <- list(
    list(0,   "#67001f"),   # rojo oscuro  → -1
    list(0.1, "#b2182b"),
    list(0.2, "#d6604d"),
    list(0.3, "#f4a582"),
    list(0.4, "#fddbc7"),
    list(0.5, "#f7f7f7"),   # blanco neutro → 0
    list(0.6, "#d1e5f0"),
    list(0.7, "#92c5de"),
    list(0.8, "#4393c3"),
    list(0.9, "#2166ac"),
    list(1,   "#053061")    # azul oscuro  → +1
  )

  cs_viridis <- list(
    list(0,   "#440154"),
    list(0.25, "#3b528b"),
    list(0.5,  "#21908d"),
    list(0.75, "#5dc963"),
    list(1,    "#fde725")
  )

  cs_plasma <- list(
    list(0,    "#0d0887"),
    list(0.25, "#7e03a8"),
    list(0.5,  "#cb4679"),
    list(0.75, "#f89441"),
    list(1,    "#f0f921")
  )

  cs_portland <- list(
    list(0,    "#0c3383"),
    list(0.25, "#0a88ba"),
    list(0.5,  "#f2d338"),
    list(0.75, "#f28f38"),
    list(1,    "#d91e1e")
  )

  cs_picnic <- list(
    list(0,    "#0000ff"),
    list(0.25, "#7f7fff"),
    list(0.5,  "#ffffff"),
    list(0.75, "#ff7f7f"),
    list(1,    "#ff0000")
  )

  Paleta <- as.integer(Paleta)
  if (is.na(Paleta) || Paleta < 1L || Paleta > 5L) Paleta <- 1L

  colorscale <- switch(as.character(Paleta),
    "1" = cs_rdbu_rev,
    "2" = cs_viridis,
    "3" = cs_plasma,
    "4" = cs_portland,
    "5" = cs_picnic,
    cs_rdbu_rev
  )

  # ── Construcción del trace heatmap ───────────────────────────────────────────
  trace <- list(
    type        = "heatmap",
    z           = cor_matrix,
    x           = col_names,
    y           = col_names,
    zmin        = -1,
    zmax        = 1,
    colorscale  = colorscale,
    hovertemplate = "%{y} × %{x}: %{z:.3f}<extra></extra>"
  )

  # Mostrar valores en celdas si se solicita
  if (isTRUE(MostrarValores)) {
    trace$text         <- round(cor_matrix, 2)
    trace$texttemplate <- "%{text}"
    trace$textfont     <- list(color = "#ffffff", size = 10)
  }

  traces <- list(trace)

  # ── Layout con tema oscuro NEVEN ─────────────────────────────────────────────
  layout <- list(
    paper_bgcolor = "#373434",
    plot_bgcolor  = "#373434",
    font          = list(color = "#888"),
    xaxis         = list(
      color          = "#888",
      tickangle      = -45,
      gridcolor      = "#444",
      zerolinecolor  = "#555"
    ),
    yaxis         = list(
      color          = "#888",
      gridcolor      = "#444",
      zerolinecolor  = "#555"
    ),
    showlegend    = FALSE,
    margin        = list(t = 50, r = 30, b = 120, l = 120)
  )

  # ── Codificación base64 + construcción HTML ───────────────────────────────────
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

  # ── Retorno estándar ──────────────────────────────────────────────────────────
  return(r_object_to_slots(
    list(grafico = html_plotly),
    tier_map = c(grafico = 1L)
  ))
}
