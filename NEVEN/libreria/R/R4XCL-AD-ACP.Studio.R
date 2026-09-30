# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio para Análisis de Componentes Principales
# Requiere: r_object_to_slots.R cargado en el entorno global
# ═══════════════════════════════════════════════════════════════════════════════

#' Wrapper Data Lab para ACP.
#'
#' Ejecuta princomp() sobre el data.frame recibido y retorna los resultados
#' estructurados como slots tipificados para Data Lab, incluyendo gráficos
#' interactivos (círculo de correlaciones y plano factorial de individuos).
#'
#' @param data          data.frame con columnas numéricas (rol X).
#' @param Escala        Escalar variables con scale() (default: TRUE).
#' @param N_Componentes Componentes a retener (0 = todos, default: 0).
#'
#' @return data.frame de slots (name, label, type, value, tier).
#'
AD_ACP.Studio <- function(data,
                           Escala          = TRUE,
                           N_Componentes   = 0L) {

  # ── Validaciones ───────────────────────────────────────────────────────────
  if (!is.data.frame(data) && !is.matrix(data)) stop("'data' debe ser un data.frame o matrix.")
  data     <- as.data.frame(data)
  num_cols <- sapply(data, is.numeric)
  if (!any(num_cols)) stop("No se encontraron columnas numéricas.")
  data_num <- data[, num_cols, drop = FALSE]
  if (nrow(data_num) < 3) stop("Se requieren al menos 3 observaciones para ACP.")
  if (ncol(data_num) < 2) stop("Se requieren al menos 2 variables numéricas para ACP.")

  N_Componentes <- as.integer(N_Componentes)
  max_comp      <- min(nrow(data_num) - 1L, ncol(data_num))
  if (N_Componentes <= 0L || N_Componentes > max_comp) N_Componentes <- max_comp

  # ── Preparación ────────────────────────────────────────────────────────────
  data_proc <- if (isTRUE(Escala)) as.data.frame(scale(data_num)) else data_num

  # ── ACP ────────────────────────────────────────────────────────────────────
  res_pca <- princomp(data_proc, cor = TRUE)

  # ── Varianza explicada ─────────────────────────────────────────────────────
  eigenvalues <- round(res_pca$sdev^2, 4)
  var_prop    <- round(eigenvalues / sum(eigenvalues) * 100, 2)
  var_acum    <- round(cumsum(var_prop), 2)
  nc          <- N_Componentes

  varianza_df <- data.frame(
    Componente        = paste0("CP", seq_len(nc)),
    Valor_Propio      = eigenvalues[1:nc],
    Varianza_Pct      = var_prop[1:nc],
    Varianza_Acum_Pct = var_acum[1:nc],
    stringsAsFactors  = FALSE
  )

  # ── Cargas ─────────────────────────────────────────────────────────────────
  loadings_mat <- unclass(res_pca$loadings)[, 1:nc, drop = FALSE]
  loadings_df  <- cbind(
    Variable = rownames(loadings_mat),
    as.data.frame(round(loadings_mat, 4), stringsAsFactors = FALSE),
    stringsAsFactors = FALSE
  )
  colnames(loadings_df)[-1] <- paste0("CP", seq_len(nc))
  rownames(loadings_df) <- NULL

  # ── Scores (primeros 2 CP) ─────────────────────────────────────────────────
  nc2       <- min(2L, nc)
  scores_df <- cbind(
    ID = seq_len(nrow(data_num)),
    as.data.frame(round(res_pca$scores[, 1:nc2, drop = FALSE], 4)),
    stringsAsFactors = FALSE
  )
  colnames(scores_df)[-1] <- paste0("CP", seq_len(nc2))

  # ── Correlación original ───────────────────────────────────────────────────
  cor_df <- cbind(
    Variable = rownames(cor(data_num)),
    as.data.frame(round(cor(data_num), 4)),
    stringsAsFactors = FALSE
  )
  rownames(cor_df) <- NULL

  # ── Gráfico: Círculo de correlaciones — JSON plotly construido manualmente ──
  html_circulo <- tryCatch({
    sdev      <- res_pca$sdev[1:nc2]
    vc        <- t(apply(loadings_mat[, 1:nc2, drop = FALSE], 1, function(r) r * sdev))
    var_names <- rownames(loadings_mat)
    pct1      <- var_prop[1]
    pct2      <- if (nc2 >= 2) var_prop[2] else 0

    # Círculo unitario
    theta  <- seq(0, 2 * pi, length.out = 100)
    cx     <- round(cos(theta), 4)
    cy     <- round(sin(theta), 4)

    traces <- list()

    # Traza 1: círculo
    traces[[1]] <- list(
      type = "scatter", mode = "lines",
      x = cx, y = cy,
      line = list(color = "rgba(215,165,56,0.25)", width = 1),
      showlegend = FALSE, hoverinfo = "none"
    )

    # Trazas: vectores de variables
    for (i in seq_len(nrow(vc))) {
      x_end <- vc[i, 1]
      y_end <- if (nc2 >= 2) vc[i, 2] else 0
      traces[[length(traces) + 1]] <- list(
        type = "scatter", mode = "lines+markers+text",
        x = c(0, x_end), y = c(0, y_end),
        line   = list(color = "#d7a538", width = 2),
        marker = list(size = c(4, 8), color = "#d7a538"),
        text   = c("", var_names[i]),
        textposition = "top center",
        textfont = list(size = 11, color = "#e0e0e0"),
        showlegend = FALSE, hoverinfo = "none"
      )
    }

    layout <- list(
      title = list(text = paste0("Circulo de Correlaciones (CP1=", pct1, "%, CP2=", pct2, "%)"),
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = paste0("CP1 (", pct1, "%)"), range = c(-1.4, 1.4),
                   zeroline = TRUE, zerolinecolor = "#555", gridcolor = "#333", color = "#888"),
      yaxis = list(title = paste0("CP2 (", pct2, "%)"), range = c(-1.4, 1.4),
                   zeroline = TRUE, zerolinecolor = "#555", gridcolor = "#333", color = "#888"),
      paper_bgcolor = "#373434", plot_bgcolor = "#373434",
      font = list(color = "#888"), margin = list(t = 50, r = 20, b = 50, l = 60)
    )

    fig_json <- jsonlite::toJSON(list(data = traces, layout = layout),
                                  auto_unbox = TRUE, na = "null")
    fig_json <- iconv(fig_json, from = "UTF-8", to = "UTF-8", sub = "byte")
    paste0('<html><body><neven-plotly>', jsonlite::base64_enc(chartr("\n\r", "  ", fig_json)), '</neven-plotly></body></html>')

  }, error = function(e) {
    paste0('<html><body><p style="color:#888;padding:8px">Círculo no disponible: ',
           conditionMessage(e), '</p></body></html>')
  })

  # ── Gráfico: Plano factorial de individuos — JSON plotly manual ─────────────
  html_individuos <- tryCatch({
    sc   <- as.data.frame(res_pca$scores[, 1:nc2, drop = FALSE])
    ids  <- seq_len(nrow(sc))
    pct1 <- var_prop[1]
    pct2 <- if (nc2 >= 2) var_prop[2] else 0
    cp1  <- round(sc[, 1], 4)
    cp2  <- if (nc2 >= 2) round(sc[, 2], 4) else rep(0, nrow(sc))

    traces2 <- list(list(
      type = "scatter", mode = "markers+text",
      x = cp1, y = cp2,
      text = as.character(ids),
      textposition = "top center",
      textfont = list(size = 9, color = "#888"),
      marker = list(size = 8, color = "#d7a538",
                    line = list(color = "#373434", width = 1)),
      hovertext = paste0("ID ", ids, " | CP1: ", cp1, " | CP2: ", cp2),
      hoverinfo = "text",
      showlegend = FALSE
    ))

    layout2 <- list(
      title = list(text = paste0("Plano Factorial - Individuos (CP1=", pct1, "%, CP2=", pct2, "%)"),
                   font = list(color = "#e0e0e0", size = 12)),
      xaxis = list(title = paste0("CP1 (", pct1, "%)"),
                   zeroline = TRUE, zerolinecolor = "#555", gridcolor = "#333", color = "#888"),
      yaxis = list(title = paste0("CP2 (", pct2, "%)"),
                   zeroline = TRUE, zerolinecolor = "#555", gridcolor = "#333", color = "#888"),
      paper_bgcolor = "#373434", plot_bgcolor = "#373434",
      font = list(color = "#888"), margin = list(t = 50, r = 20, b = 50, l = 60)
    )

    fig2_json <- jsonlite::toJSON(list(data = traces2, layout = layout2),
                                   auto_unbox = TRUE, na = "null")
    fig2_json <- iconv(fig2_json, from = "UTF-8", to = "UTF-8", sub = "byte")
    paste0('<html><body><neven-plotly>', jsonlite::base64_enc(chartr("\n\r", "  ", fig2_json)), '</neven-plotly></body></html>')

  }, error = function(e) {
    paste0('<html><body><p style="color:#888;padding:8px">Plano no disponible: ',
           conditionMessage(e), '</p></body></html>')
  })

  # ── Construir resultado ────────────────────────────────────────────────────
  resultado <- list(
    varianza_explicada  = varianza_df,
    cargas              = loadings_df,
    circulo_variables   = html_circulo,
    plano_individuos    = html_individuos,
    scores              = scores_df,
    correlacion         = cor_df
  )

  tier_map <- c(
    varianza_explicada  = 1L,
    cargas              = 1L,
    circulo_variables   = 1L,
    plano_individuos    = 1L,
    scores              = 2L,
    correlacion         = 2L
  )

  return(r_object_to_slots(resultado, tier_map = tier_map))
}
