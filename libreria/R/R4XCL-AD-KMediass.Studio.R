# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio para K-Medias
# Requiere: r_object_to_slots.R cargado en el entorno global
# ═══════════════════════════════════════════════════════════════════════════════

#' Wrapper Data Lab para el algoritmo de K-Medias.
#'
#' Recibe un data.frame numérico, ejecuta kmeans(), serializa los resultados
#' usando r_object_to_slots() y retorna el data.frame de slots.
#'
#' @param data       data.frame con columnas numéricas (rol X).
#' @param K          Número de clusters (default: 3).
#' @param Escala     Escalar los datos con scale() antes de clustering (default: FALSE).
#' @param TipoModelo Índice del algoritmo: 1=Hartigan-Wong, 2=Lloyd,
#'                   3=Forgy, 4=MacQueen (default: 1).
#' @param Semilla    Semilla aleatoria para reproducibilidad (default: 123456).
#'
#' @return data.frame de slots (name, label, type, value, tier).
#'
AD_KMedias.Studio <- function(data,
                               K          = 3L,
                               Escala     = FALSE,
                               TipoModelo = 1L,
                               Semilla    = 123456L) {
  # ── Validaciones ───────────────────────────────────────────────────────────
  if (!is.data.frame(data) && !is.matrix(data)) {
    stop("'data' debe ser un data.frame o matrix.")
  }
  data <- as.data.frame(data)

  # Conservar solo columnas numéricas
  num_cols <- sapply(data, is.numeric)
  if (!any(num_cols)) {
    stop("No se encontraron columnas numéricas en los datos.")
  }
  data_num <- data[, num_cols, drop = FALSE]

  K <- as.integer(K)
  if (K < 1 || K >= nrow(data_num)) {
    stop(paste0("K (", K, ") debe ser >= 1 y < número de filas (", nrow(data_num), ")."))
  }

  TipoModelo <- as.integer(TipoModelo)
  algoritmos <- c("Hartigan-Wong", "Lloyd", "Forgy", "MacQueen")
  if (TipoModelo < 1 || TipoModelo > 4) {
    stop("TipoModelo debe ser 1 (Hartigan-Wong), 2 (Lloyd), 3 (Forgy) o 4 (MacQueen).")
  }

  # ── Preparación de datos ───────────────────────────────────────────────────
  set.seed(as.integer(Semilla))

  if (isTRUE(Escala)) {
    data_proc <- as.data.frame(scale(data_num))
  } else {
    data_proc <- data_num
  }

  # ── Ejecutar K-Means ───────────────────────────────────────────────────────
  res_km <- kmeans(data_proc, centers = K, algorithm = algoritmos[TipoModelo], nstart = 10L)

  # ── Construir objeto resultado ─────────────────────────────────────────────
  centers_df <- as.data.frame(res_km$centers)
  centers_df <- cbind(Cluster = seq_len(nrow(centers_df)), centers_df)

  resultado <- list(
    centers            = centers_df,
    cluster_assignments = as.integer(res_km$cluster),
    within_ss          = round(sum(res_km$withinss), 4),
    total_ss           = round(res_km$totss, 4),
    between_ss         = round(res_km$betweenss, 4)
  )

  # ── Serializar y retornar ──────────────────────────────────────────────────
  tier_map <- c(
    centers             = 1L,
    cluster_assignments = 1L,
    within_ss           = 2L,
    total_ss            = 2L,
    between_ss          = 2L
  )
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
