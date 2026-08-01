# ===============================================================================
# NEVEN Data Lab — EJEMPLO CON LIBRERIA EXTERNA: ACP con FactoMineR
# ===============================================================================
# PROPOSITO DE ESTE EJEMPLO:
#   Muestra como integrar una libreria externa (FactoMineR) en una funcion
#   personalizada para Data Lab.
#
# LIBRERIA: FactoMineR — una de las librerias mas completas para analisis
#   factorial en R. Mas potente que princomp() / prcomp() porque entrega
#   contribuciones, cos2 y calidad de representacion automaticamente.
#
# PATRON DEMOSTRADO:
#   1. requireNamespace() para verificar/cargar libreria externa
#   2. Extraccion de resultados ricos del objeto PCA
#   3. Biplot con variables e individuos en el mismo grafico
#   4. Uso de colores por contribucion
# ===============================================================================

UC_EjemploFactoMineR.Studio <- function(data_X,
                                          N_Comp       = 0L,
                                          Escala       = TRUE,
                                          Top_Variables = 10L) {

  # ── Verificar libreria externa ───────────────────────────────────────────────
  if (!requireNamespace("FactoMineR", quietly = TRUE)) {
    stop("Libreria 'FactoMineR' no instalada. ",
         "Instale con: install.packages('FactoMineR')")
  }

  # ── Validaciones ────────────────────────────────────────────────────────────
  if (!is.data.frame(data_X) && !is.matrix(data_X)) stop("'data_X' debe ser un data.frame.")
  data_X <- as.data.frame(data_X)
  num_cols  <- sapply(data_X, is.numeric)
  data_num  <- data_X[, num_cols, drop = FALSE]
  if (ncol(data_num) < 2) stop("Se requieren al menos 2 columnas numericas.")
  if (nrow(data_num) < 3) stop("Se requieren al menos 3 observaciones.")

  N_Comp        <- as.integer(N_Comp)
  Top_Variables <- as.integer(Top_Variables)
  max_comp      <- min(nrow(data_num) - 1L, ncol(data_num))
  if (N_Comp <= 0L || N_Comp > max_comp) N_Comp <- max_comp

  # ── ACP con FactoMineR ───────────────────────────────────────────────────────
  # FactoMineR::PCA retorna un objeto S3 rico con resultados para variables
  # e individuos, incluyendo contribuciones y cos^2 (calidad de representacion)
  res_pca <- FactoMineR::PCA(
    data_num,
    ncp   = N_Comp,
    scale.unit = isTRUE(Escala),
    graph = FALSE   # No abrir ventana grafica
  )

  # ── Varianza explicada ────────────────────────────────────────────────────────
  eig <- as.data.frame(res_pca$eig)
  varianza_df <- data.frame(
    Componente        = paste0("CP", seq_len(N_Comp)),
    Valor_Propio      = round(eig[1:N_Comp, "eigenvalue"], 4),
    Varianza_Pct      = round(eig[1:N_Comp, "percentage of variance"], 2),
    Varianza_Acum_Pct = round(eig[1:N_Comp, "cumulative percentage of variance"], 2),
    stringsAsFactors  = FALSE
  )

  # ── Coordenadas de variables (correlaciones con los CP) ─────────────────────
  # FactoMineR llama a esto "var$coord"
  nc2       <- min(2L, N_Comp)
  var_coord <- as.data.frame(res_pca$var$coord[, 1:nc2, drop = FALSE])
  colnames(var_coord) <- paste0("CP", seq_len(nc2))
  var_coord <- cbind(Variable = rownames(var_coord), var_coord,
                     stringsAsFactors = FALSE)
  rownames(var_coord) <- NULL

  # ── Contribuciones de variables a CP1 y CP2 ─────────────────────────────────
  var_contrib <- as.data.frame(res_pca$var$contrib[, 1:nc2, drop = FALSE])
  colnames(var_contrib) <- paste0("Contrib_CP", seq_len(nc2))
  var_contrib <- cbind(Variable = rownames(var_contrib), var_contrib,
                       stringsAsFactors = FALSE)
  rownames(var_contrib) <- NULL
  var_contrib[, 2:ncol(var_contrib)] <- lapply(
    var_contrib[, 2:ncol(var_contrib), drop = FALSE], round, 2
  )

  # ── Calidad de representacion (cos2) ─────────────────────────────────────────
  var_cos2 <- as.data.frame(res_pca$var$cos2[, 1:nc2, drop = FALSE])
  colnames(var_cos2) <- paste0("Cos2_CP", seq_len(nc2))
  var_cos2 <- cbind(Variable = rownames(var_cos2), var_cos2,
                    stringsAsFactors = FALSE)
  rownames(var_cos2) <- NULL

  # ── Scores (coordenadas de individuos) ───────────────────────────────────────
  ind_coord <- as.data.frame(res_pca$ind$coord[, 1:nc2, drop = FALSE])
  colnames(ind_coord) <- paste0("CP", seq_len(nc2))
  ind_coord <- cbind(ID = seq_len(nrow(ind_coord)),
                     round(ind_coord, 4),
                     stringsAsFactors = FALSE)

  # ── Biplot interactivo: variables + individuos ────────────────────────────────
  pct1 <- varianza_df$Varianza_Pct[1]
  pct2 <- if (N_Comp >= 2) varianza_df$Varianza_Pct[2] else 0

  html_biplot <- tryCatch({
    # Coordenadas de variables (usar las del circulo de correlaciones)
    vc   <- as.matrix(res_pca$var$coord[, 1:nc2, drop = FALSE])
    vnms <- rownames(vc)
    # Limitar a Top_Variables mas importantes (por cos2 total en CP1+CP2)
    cos2_sum <- rowSums(as.matrix(res_pca$var$cos2[, 1:nc2, drop = FALSE]))
    top_idx  <- order(-cos2_sum)[1:min(Top_Variables, length(cos2_sum))]
    vc_top   <- vc[top_idx, , drop = FALSE]
    vnms_top <- vnms[top_idx]

    # Calidad de representacion → escala de color para variables
    contrib_cp1 <- res_pca$var$contrib[top_idx, 1]
    max_c       <- max(contrib_cp1, 1)
    var_alpha   <- round(0.4 + 0.6 * contrib_cp1 / max_c, 2)

    # Individuos
    ic   <- as.matrix(res_pca$ind$coord[, 1:nc2, drop = FALSE])
    ind_cos2 <- rowSums(as.matrix(res_pca$ind$cos2[, 1:nc2, drop = FALSE]))

    traces <- list()

    # Traza 1: circulo unitario
    theta <- seq(0, 2 * pi, length.out = 100)
    traces[[1]] <- list(
      type = "scatter", mode = "lines",
      x = round(cos(theta), 4), y = round(sin(theta), 4),
      line = list(color = "rgba(215,165,56,0.2)", width = 1),
      showlegend = FALSE, hoverinfo = "none",
      xaxis = "x2", yaxis = "y2"
    )

    # Traza 2: individuos (eje principal)
    traces[[2]] <- list(
      type = "scatter", mode = "markers",
      x = round(ic[, 1], 4),
      y = round(if (nc2 >= 2) ic[, 2] else rep(0, nrow(ic)), 4),
      marker = list(size = 6, color = "#888", opacity = 0.6,
                    colorscale = "Viridis",
                    color = round(ind_cos2, 3)),
      text = paste0("ID ", seq_len(nrow(ic))),
      hoverinfo = "text",
      name = "Individuos",
      xaxis = "x", yaxis = "y"
    )

    # Trazas 3+: vectores de variables (eje secundario)
    for (i in seq_len(nrow(vc_top))) {
      traces[[length(traces) + 1]] <- list(
        type = "scatter", mode = "lines+markers+text",
        x = c(0, round(vc_top[i, 1], 4)),
        y = c(0, round(if (nc2 >= 2) vc_top[i, 2] else 0, 4)),
        line   = list(color = sprintf("rgba(215,165,56,%s)", var_alpha[i]), width = 2),
        marker = list(size = c(4, 8), color = "#d7a538"),
        text   = c("", vnms_top[i]),
        textposition = "top center",
        textfont = list(size = 10, color = "#e0e0e0"),
        showlegend = FALSE, hoverinfo = "none",
        xaxis = "x2", yaxis = "y2"
      )
    }

    layout <- list(
      title = list(text = paste0("Biplot FactoMineR — CP1 (", pct1,
                                  "%) vs CP2 (", pct2, "%)"),
                   font = list(color = "#e0e0e0", size = 12)),
      # Eje de individuos
      xaxis  = list(title = paste0("CP1 (", pct1, "%)"), domain = c(0, 1),
                    color = "#888", gridcolor = "#333", zerolinecolor = "#555"),
      yaxis  = list(title = paste0("CP2 (", pct2, "%)"),
                    color = "#888", gridcolor = "#333", zerolinecolor = "#555"),
      # Eje superpuesto para variables (circulo unitario)
      xaxis2 = list(overlaying = "x", side = "top",
                    range = c(-1.4, 1.4), showgrid = FALSE,
                    showticklabels = FALSE, zeroline = FALSE),
      yaxis2 = list(overlaying = "y", side = "right",
                    range = c(-1.4, 1.4), showgrid = FALSE,
                    showticklabels = FALSE, zeroline = FALSE),
      paper_bgcolor = "#373434", plot_bgcolor = "#373434",
      font = list(color = "#888"), margin = list(t = 50, r = 60, b = 50, l = 60)
    )

    fig_json <- iconv(jsonlite::toJSON(list(data = traces, layout = layout),
                                        auto_unbox = TRUE, na = "null"),
                      from = "UTF-8", to = "UTF-8", sub = "byte")
    paste0('<html><body><neven-plotly>',
           jsonlite::base64_enc(chartr("\n\r", "  ", fig_json)),
           '</neven-plotly></body></html>')
  }, error = function(e) {
    paste0('<html><body><p style="color:#888;padding:8px">Biplot no disponible: ',
           conditionMessage(e), '</p></body></html>')
  })

  # ── Resultado ─────────────────────────────────────────────────────────────
  resultado <- list(
    varianza_explicada = varianza_df,
    biplot             = html_biplot,
    coordenadas_vars   = var_coord,
    contribuciones     = var_contrib,
    calidad_repr       = var_cos2,
    scores_individuos  = ind_coord
  )
  tier_map <- c(
    varianza_explicada = 1L,
    biplot             = 1L,
    coordenadas_vars   = 1L,
    contribuciones     = 2L,
    calidad_repr       = 2L,
    scores_individuos  = 2L
  )
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
