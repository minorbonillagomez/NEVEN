# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Serializador de objetos R a Slots tipificados
# Cargado por startup.r al iniciar ControlR.exe
# ═══════════════════════════════════════════════════════════════════════════════

#' Convierte un objeto R S3 en una lista de Slots para Data Lab.
#'
#' @param obj       Cualquier objeto R S3 con elementos nombrados (lista, data.frame,
#'                  objeto kmeans, lm, etc.). Solo se procesan los elementos del nivel
#'                  superior obtenidos con names(obj).
#' @param tier_map  Vector entero nombrado opcional para anular el tier por defecto (1).
#'                  Ejemplo: c(centers = 1L, within_ss = 2L)
#'
#' @return Data.frame con columnas: name, label, type, value, tier.
#'         Cada fila es un Slot. El campo 'value' contiene JSON serializado como string.
#'
r_object_to_slots <- function(obj, tier_map = NULL) {
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("El paquete 'jsonlite' es necesario para r_object_to_slots.")
  }

  nms <- names(obj)
  if (is.null(nms) || length(nms) == 0) {
    # Objeto sin nombres: tratarlo como un slot único
    nms <- "result"
    obj_list <- list(result = obj)
  } else {
    obj_list <- as.list(obj)
  }

  slots <- vector("list", length(nms))

  for (i in seq_along(nms)) {
    nm  <- nms[i]
    val <- obj_list[[nm]]

    # ── Asignación de tipo (orden de prioridad según Req 9.2) ──────────
    tipo <- .neven_dl_detect_type(val)

    # ── Serialización del valor a JSON ─────────────────────────────────
    val_json <- .neven_dl_serialize_value(val, tipo)

    # ── Tier: default 1, override desde tier_map ───────────────────────
    tier <- 1L
    if (!is.null(tier_map) && !is.na(tier_map[nm])) {
      tier <- as.integer(tier_map[nm])
    }

    slots[[i]] <- list(
      name  = nm,
      label = nm,
      type  = tipo,
      value = val_json,
      tier  = tier
    )
  }

  # Retornar como data.frame para que ControlR lo serialice como Variable arr
  result_df <- do.call(rbind, lapply(slots, as.data.frame, stringsAsFactors = FALSE))
  return(result_df)
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers privados (prefijo .neven_dl_)
# ─────────────────────────────────────────────────────────────────────────────

#' Detecta el tipo semántico de un valor R para Data Lab.
#'
#' Cinco reglas de prioridad (se evalúan en orden):
#'   1. data.frame o matrix           → "table"
#'   2. string con "<html" (ci)       → "html"
#'   3. vector atómico, longitud > 1  → "vector"
#'   4. vector atómico, longitud == 1 → "scalar"
#'   5. cualquier otro                → "unknown"
#'
#' @param val Cualquier objeto R.
#' @return Character(1): uno de "table", "html", "vector", "scalar", "unknown".
#'
.neven_dl_detect_type <- function(val) {
  # Prioridad 1: data.frame o matrix → table
  if (is.data.frame(val) || is.matrix(val)) return("table")

  # Prioridad 2: string que contiene "<html" (case-insensitive) → html
  if (is.character(val) && length(val) == 1) {
    if (grepl("<html", val, ignore.case = TRUE)) return("html")
  }

  # Prioridad 3: vector atómico de longitud > 1 → vector
  if (is.atomic(val) && length(val) > 1) return("vector")

  # Prioridad 4: vector atómico de longitud 1 → scalar
  if (is.atomic(val) && length(val) == 1) return("scalar")

  # Prioridad 5: cualquier otro → unknown
  return("unknown")
}

#' Serializa un valor R al formato JSON adecuado según su tipo semántico.
#'
#' Despacha por tipo usando `switch`:
#'   - `"table"`   → `jsonlite::toJSON` con `dataframe="rows"`
#'   - `"html"`    → `as.character(val)` (pasa el string tal cual)
#'   - `"vector"`  → `jsonlite::toJSON(as.list(val), auto_unbox=FALSE)`
#'   - `"scalar"`  → `jsonlite::toJSON(val, auto_unbox=TRUE)`
#'   - default     → intenta `jsonlite::toJSON`; cae a `print` en error
#'
#' El cuerpo completo está envuelto en `tryCatch` para que cualquier error
#' de serialización devuelva una cadena JSON de error en lugar de propagar.
#'
#' @param val  Objeto R a serializar.
#' @param tipo Character(1): uno de "table", "html", "vector", "scalar", "unknown".
#' @return Character(1) con el valor serializado.
#'
.neven_dl_serialize_value <- function(val, tipo) {
  tryCatch({
    switch(tipo,
      "table" = {
        df <- as.data.frame(val, stringsAsFactors = FALSE)
        jsonlite::toJSON(df, dataframe = "rows", auto_unbox = TRUE, na = "null")
      },
      "html" = {
        as.character(val)
      },
      "vector" = {
        jsonlite::toJSON(as.list(val), auto_unbox = FALSE, na = "null")
      },
      "scalar" = {
        jsonlite::toJSON(val, auto_unbox = TRUE, na = "null")
      },
      {
        tryCatch(
          jsonlite::toJSON(val, auto_unbox = TRUE, na = "null"),
          error = function(e) paste(capture.output(print(val)), collapse = "\n")
        )
      }
    )
  }, error = function(e) {
    paste0('"[Error al serializar: ', gsub('"', '\\"', conditionMessage(e)), ']"')
  })
}

#' Formatea un data.frame de métricas (Metrica, Valor) como texto plano alineado.
#' Metrica alineada a la izquierda, Valor alineado a la derecha.
#'
#' @param m data.frame con columnas Metrica (character) y Valor (character o numeric)
#' @return Character(1) listo para retornar como slot scalar
#'
.neven_fmt_metricas <- function(m) {
  if (!is.data.frame(m) || nrow(m) == 0) return("")
  vals <- as.character(m[[2]])
  keys <- as.character(m[[1]])
  w_k  <- max(nchar(keys))
  w_v  <- max(nchar(vals))
  header <- paste0(formatC("Metrica", width = -w_k),
                   "  ",
                   formatC("Valor",   width =  w_v))
  sep    <- strrep("-", w_k + w_v + 2)
  rows   <- mapply(function(k, v) {
    paste0(formatC(k, width = -w_k), "  ", formatC(v, width = w_v))
  }, keys, vals)
  paste(c(header, sep, rows), collapse = "\n")
}
