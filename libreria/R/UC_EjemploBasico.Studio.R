# ===============================================================================
# NEVEN Data Lab — EJEMPLO BASICO: Funcion Personalizada (User Contributed)
# ===============================================================================
# INSTRUCCIONES PARA EL USUARIO:
#
# Este archivo muestra el patron MINIMO para crear una funcion en Data Lab.
# Pasos:
#   1. Copia este archivo a C:\NEVEN\functions\
#   2. Copia el archivo UC_EjemploBasico.json a C:\NEVEN\functions\
#   3. Reinicia NEVEN Studio
#   4. Tu funcion aparece en Data Lab bajo la familia "Mis Funciones (UC)"
#
# REGLAS:
#   - La funcion se llama exactamente igual que el archivo pero sin ".Studio.R"
#     Ejemplo: UC_EjemploBasico.Studio.R → funcion UC_EjemploBasico.Studio()
#   - Debe recibir data_X (y opcionalmente data_Y) como data.frames
#   - Debe retornar r_object_to_slots(resultado, tier_map=...)
#   - Requiere r_object_to_slots.R (ya esta cargado en NEVEN)
# ===============================================================================

UC_EjemploBasico.Studio <- function(data_X,
                                      Precision = 2L) {

  # ── Validacion ──────────────────────────────────────────────────────────────
  if (!is.data.frame(data_X) && !is.matrix(data_X)) stop("'data_X' debe ser un data.frame.")
  data_X    <- as.data.frame(data_X)
  num_cols  <- sapply(data_X, is.numeric)
  data_num  <- data_X[, num_cols, drop = FALSE]
  Precision <- as.integer(Precision)
  if (ncol(data_num) == 0) stop("No hay columnas numericas en los datos.")

  # ── Analisis: estadisticas descriptivas ─────────────────────────────────────
  stats_list <- lapply(names(data_num), function(col) {
    x <- data_num[[col]]
    x <- x[!is.na(x)]
    data.frame(
      Variable  = col,
      N         = length(x),
      Media     = round(mean(x), Precision),
      Mediana   = round(median(x), Precision),
      Desv_Std  = round(sd(x), Precision),
      Min       = round(min(x), Precision),
      Max       = round(max(x), Precision),
      stringsAsFactors = FALSE
    )
  })
  stats_df <- do.call(rbind, stats_list)
  rownames(stats_df) <- NULL

  # ── Resultado: usar r_object_to_slots() para serializar ─────────────────────
  resultado <- list(
    estadisticas = stats_df
  )
  tier_map <- c(estadisticas = 1L)

  return(r_object_to_slots(resultado, tier_map = tier_map))
}
