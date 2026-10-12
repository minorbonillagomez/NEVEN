# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio para Clustering Jerárquico
# Requiere: r_object_to_slots.R cargado en el entorno global
# ═══════════════════════════════════════════════════════════════════════════════

#' Wrapper Data Lab para Clustering Jerárquico (hclust).
#'
#' Calcula distancias, ejecuta hclust y retorna asignaciones de cluster,
#' alturas de fusión y estadísticas por cluster.
#'
#' @param data        data.frame con columnas numéricas (rol X).
#' @param K           Número de clusters a cortar (default: 3).
#' @param Escala      Escalar variables antes del análisis (default: TRUE).
#' @param Metodo      Método de enlace: 1=Ward.D2, 2=Complete, 3=Average, 4=Single (default: 1).
#' @param Distancia   Medida de distancia: 1=Euclidiana, 2=Manhattan (default: 1).
#'
#' @return data.frame de slots (name, label, type, value, tier).
#'
AD_ClusteringJerarquico.Studio <- function(data,
                                             K          = 3L,
                                             Escala     = TRUE,
                                             Metodo     = 1L,
                                             Distancia  = 1L) {

  # ── Validaciones ───────────────────────────────────────────────────────────
  if (!is.data.frame(data) && !is.matrix(data)) {
    stop("'data' debe ser un data.frame o matrix.")
  }
  data <- as.data.frame(data)

  num_cols <- sapply(data, is.numeric)
  if (!any(num_cols)) stop("No se encontraron columnas numéricas.")
  data_num <- data[, num_cols, drop = FALSE]

  if (nrow(data_num) < 3) stop("Se requieren al menos 3 observaciones.")

  K         <- as.integer(K)
  Metodo    <- as.integer(Metodo)
  Distancia <- as.integer(Distancia)

  if (K < 2L || K >= nrow(data_num)) {
    stop(paste0("K (", K, ") debe ser >= 2 y < número de filas (", nrow(data_num), ")."))
  }

  metodos    <- c("ward.D2", "complete", "average", "single")
  distancias <- c("euclidean", "manhattan")

  if (Metodo < 1L || Metodo > 4L)    stop("Metodo debe ser 1 (Ward.D2), 2 (Complete), 3 (Average) o 4 (Single).")
  if (Distancia < 1L || Distancia > 2L) stop("Distancia debe ser 1 (Euclidiana) o 2 (Manhattan).")

  # ── Preparación ────────────────────────────────────────────────────────────
  if (isTRUE(Escala)) {
    data_proc <- as.data.frame(scale(data_num))
  } else {
    data_proc <- data_num
  }

  # ── Clustering jerárquico ──────────────────────────────────────────────────
  dist_mat  <- dist(data_proc, method = distancias[Distancia])
  hc        <- hclust(dist_mat, method = metodos[Metodo])
  clusters  <- cutree(hc, k = K)

  # ── Asignaciones ──────────────────────────────────────────────────────────
  asignaciones_df <- data.frame(
    ID      = seq_len(nrow(data_num)),
    Cluster = as.integer(clusters),
    stringsAsFactors = FALSE
  )

  # ── Estadísticas por cluster ───────────────────────────────────────────────
  stats_list <- lapply(seq_len(K), function(k) {
    idx   <- which(clusters == k)
    subdf <- data_num[idx, , drop = FALSE]
    means <- round(colMeans(subdf), 4)
    sds   <- round(apply(subdf, 2, sd), 4)
    row   <- c(Cluster = k, N = length(idx), as.list(means))
    as.data.frame(row, stringsAsFactors = FALSE)
  })
  estadisticas_df <- do.call(rbind, stats_list)
  rownames(estadisticas_df) <- NULL

  # ── Alturas de fusión (últimas K-1 fusiones) ───────────────────────────────
  n_show    <- min(20L, length(hc$height))
  alturas_df <- data.frame(
    Paso   = seq(length(hc$height) - n_show + 1L, length(hc$height)),
    Altura = round(rev(tail(hc$height, n_show)), 4),
    stringsAsFactors = FALSE
  )

  # ── Resumen ────────────────────────────────────────────────────────────────
  tam_clusters <- as.integer(table(clusters))
  resumen_df <- data.frame(
    Cluster    = seq_len(K),
    N          = tam_clusters,
    Pct        = round(tam_clusters / nrow(data_num) * 100, 1),
    stringsAsFactors = FALSE
  )

  # ── Construir resultado ────────────────────────────────────────────────────
  resultado <- list(
    asignaciones       = asignaciones_df,
    resumen_clusters   = resumen_df,
    centroides         = estadisticas_df,
    alturas_fusion     = alturas_df
  )

  tier_map <- c(
    asignaciones     = 1L,
    resumen_clusters = 1L,
    centroides       = 1L,
    alturas_fusion   = 2L
  )

  return(r_object_to_slots(resultado, tier_map = tier_map))
}
