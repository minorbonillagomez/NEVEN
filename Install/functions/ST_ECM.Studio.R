# ===============================================================================
# NEVEN Data Lab — MODELO DE CORRECCIÓN DE ERROR (ECM / VECM) (ST Family)
# Dinámica de corto plazo con equilibrio de largo plazo
# Wooldridge Cap. 18 / Engle-Granger (1987) / Johansen (1988)
# ===============================================================================
# DESCRIPCIÓN:
#   Un ECM captura la dinámica de ajuste hacia un equilibrio de largo plazo entre
#   series cointegradas. La idea: aunque las series tengan tendencias individuales,
#   una combinación lineal de ellas es estacionaria (cointegración).
#
#   Flujo implementado (Wooldridge / Engle-Granger 2 etapas):
#   1. Verificar estacionariedad: prueba ADF en niveles y primeras diferencias
#   2. Verificar cointegración: Johansen (trace y eigenvalue)
#   3. Si hay cointegración → estimar VECM vía Johansen
#      Si no hay cointegración → VAR en diferencias
#
#   El término de corrección de error (ECT) mide la velocidad de ajuste:
#   negativo y significativo → el sistema se ajusta al equilibrio
#
# PAQUETES: vars + urca (prueba Johansen)
# ===============================================================================

ST_ECM.Studio <- function(data_Series,
                            MaxRezagos   = 8L,
                            CriterioSel  = 2L,
                            NivelCoint   = 1L,
                            TipoPrueba   = 1L) {

  # ── Validaciones ─────────────────────────────────────────────────────────────
  if (!is.data.frame(data_Series) || nrow(data_Series) == 0)
    stop("'data_Series' debe ser un data.frame con al menos 2 series de tiempo como columnas.")
  if (ncol(data_Series) < 2)
    stop("El ECM requiere al menos 2 series cointegradas.")

  MaxRezagos  <- as.integer(MaxRezagos);  if (is.na(MaxRezagos) || MaxRezagos < 1) MaxRezagos <- 8L
  CriterioSel <- as.integer(CriterioSel); if (is.na(CriterioSel) || CriterioSel < 1 || CriterioSel > 4) CriterioSel <- 2L
  NivelCoint  <- as.integer(NivelCoint);  if (is.na(NivelCoint) || NivelCoint < 1 || NivelCoint > 3)  NivelCoint <- 1L
  TipoPrueba  <- as.integer(TipoPrueba);  if (is.na(TipoPrueba) || TipoPrueba < 1 || TipoPrueba > 2)  TipoPrueba <- 1L

  if (!requireNamespace("vars", quietly = TRUE))
    stop("El paquete 'vars' no está instalado.")
  if (!requireNamespace("urca", quietly = TRUE))
    stop("El paquete 'urca' no está instalado. Use =R.UT_InstalacionWeb() para instalarlo.")

  df     <- data_Series[complete.cases(data_Series), ]
  n      <- nrow(df)
  k      <- ncol(df)
  nms    <- names(df)
  mat    <- as.matrix(df)
  if (!is.numeric(mat)) stop("Todas las columnas deben ser numéricas.")

  alpha_str <- switch(NivelCoint, "1" = "10pct", "2" = "5pct", "3" = "1pct", "5pct")
  crit_str  <- switch(CriterioSel, "1" = "AIC(n)", "2" = "SC(n)", "3" = "HQ(n)", "4" = "FPE", "SC(n)")
  tipo_johansen <- switch(TipoPrueba, "1" = "trace", "2" = "eigen", "trace")

  # ── Paso 1: Prueba ADF de raíz unitaria para cada serie ──────────────────────
  adf_rows <- lapply(nms, function(nm) {
    x      <- mat[, nm]
    # ADF en niveles
    adf_lev <- tryCatch(
      urca::ur.df(x, type = "trend", selectlags = "BIC"),
      error = function(e) NULL
    )
    # ADF en primeras diferencias
    adf_dif <- tryCatch(
      urca::ur.df(diff(x), type = "drift", selectlags = "BIC"),
      error = function(e) NULL
    )
    stat_lev <- if (!is.null(adf_lev)) round(adf_lev@teststat[1], 4) else NA
    stat_dif <- if (!is.null(adf_dif)) round(adf_dif@teststat[1], 4) else NA
    cv_lev   <- if (!is.null(adf_lev)) round(adf_lev@cval["tau3", "5pct"], 4) else NA
    cv_dif   <- if (!is.null(adf_dif)) round(adf_dif@cval["tau2", "5pct"], 4) else NA

    data.frame(
      Serie         = nm,
      ADF_niveles   = stat_lev,
      VC_5pct_niv   = cv_lev,
      RU_nivel      = ifelse(!is.na(stat_lev) & !is.na(cv_lev),
                             ifelse(stat_lev > cv_lev, "Sí (no estac.)", "No (estac.)"), NA),
      ADF_diferencia = stat_dif,
      VC_5pct_dif   = cv_dif,
      RU_diferencia  = ifelse(!is.na(stat_dif) & !is.na(cv_dif),
                              ifelse(stat_dif > cv_dif, "Aún no estac.", "I(1) confirmado"), NA),
      stringsAsFactors = FALSE
    )
  })
  tabla_adf <- do.call(rbind, adf_rows)

  # ── Paso 2: Selección del número de rezagos ───────────────────────────────────
  max_p <- min(MaxRezagos, floor(n / (k + 2)))
  sel   <- tryCatch(
    vars::VARselect(mat, lag.max = max_p, type = "const"),
    error = function(e) NULL
  )
  p_opt <- if (!is.null(sel)) sel$selection[[crit_str]] else 2L
  p_opt <- max(1L, p_opt)

  # ── Paso 3: Prueba de cointegración de Johansen ──────────────────────────────
  johansen <- tryCatch(
    urca::ca.jo(mat, type = tipo_johansen, K = p_opt, spec = "longrun",
                ecdet = "const"),
    error = function(e) stop(paste("Error en Johansen:", conditionMessage(e)))
  )

  # Tabla de estadísticos de la prueba Johansen
  john_stat <- round(johansen@teststat, 4)
  john_cv   <- johansen@cval
  r_names   <- paste0("r<=", seq(0, k - 1))
  tabla_johansen <- data.frame(
    Hipotesis  = r_names,
    Estadistico = john_stat,
    CV_10pct   = round(john_cv[, "10pct"], 4),
    CV_5pct    = round(john_cv[, "5pct"],  4),
    CV_1pct    = round(john_cv[, "1pct"],  4),
    stringsAsFactors = FALSE
  )

  # Determinar rango de cointegración
  cv_col  <- alpha_str
  r_coint <- 0L
  for (i in seq_len(nrow(tabla_johansen))) {
    if (john_stat[i] > john_cv[i, cv_col]) r_coint <- r_coint + 1L
  }

  hay_coint <- r_coint > 0

  # ── Paso 4a: Si hay cointegración → VECM ─────────────────────────────────────
  modelo_nota <- ""
  tabla_ect   <- NULL

  if (hay_coint) {
    vecm_result <- tryCatch({
      vecm_obj <- vars::vec2var(johansen, r = r_coint)
      sm_vecm  <- summary(vecm_obj)

      # Extraer término ECT por ecuación
      ect_rows <- lapply(nms, function(nm) {
        eq <- vecm_obj$varresult[[nm]]
        if (is.null(eq)) return(NULL)
        ct  <- summary(eq)$coefficients
        ect <- ct[grep("ect|ECT", rownames(ct), ignore.case = TRUE), , drop = FALSE]
        if (nrow(ect) == 0) return(NULL)
        data.frame(
          Ecuacion       = nm,
          ECT_coef       = round(ect[1, 1], 6),
          ECT_EE         = round(ect[1, 2], 6),
          ECT_t          = round(ect[1, 3], 4),
          ECT_p          = round(ect[1, 4], 6),
          Sig            = ifelse(ect[1, 4] < 0.001, "***",
                           ifelse(ect[1, 4] < 0.01,  "**",
                           ifelse(ect[1, 4] < 0.05,  "*",
                           ifelse(ect[1, 4] < 0.10,  ".", "")))),
          Velocidad_ajuste = ifelse(
            ect[1, 1] < 0 & ect[1, 4] < 0.05,
            paste0("Ajuste negativo significativo (", round(ect[1, 1] * 100, 1), "% por período)"),
            "No significativo o positivo"
          ),
          stringsAsFactors = FALSE
        )
      })
      do.call(rbind, Filter(Negate(is.null), ect_rows))
    }, error = function(e) NULL)

    tabla_ect   <- vecm_result
    modelo_nota <- paste0(
      "VECM estimado con r=", r_coint, " vector(es) de cointegración (Johansen, alpha=",
      alpha_str, "). El ECT negativo y significativo indica ajuste hacia el equilibrio de largo plazo."
    )
  } else {
    modelo_nota <- paste0(
      "No se encontró cointegración (r=0 al ", alpha_str, "). ",
      "Se recomienda estimar un VAR en primeras diferencias. Use ST_VAR con las series diferenciadas."
    )
    tabla_ect <- data.frame(
      Ecuacion = "—", ECT_coef = NA, ECT_EE = NA, ECT_t = NA, ECT_p = NA,
      Sig = "—", Velocidad_ajuste = modelo_nota,
      stringsAsFactors = FALSE
    )
  }

  # ── Resumen ───────────────────────────────────────────────────────────────────
  tabla_resumen <- data.frame(
    Estadistico = c("Observaciones", "Series_k", "Rezagos_p", "Tipo_prueba_Johansen",
                    "Nivel_significancia", "Rango_cointegracion", "Cointegradas"),
    Valor       = c(n, k, p_opt, tipo_johansen, alpha_str, r_coint,
                    ifelse(hay_coint, paste0("Sí (r=", r_coint, ")"), "No")),
    stringsAsFactors = FALSE
  )

  return(r_object_to_slots(
    list(
      resumen_ECM     = tabla_resumen,
      raiz_unitaria   = tabla_adf,
      johansen_test   = tabla_johansen,
      terminos_ECT    = tabla_ect
    ),
    tier_map = c(resumen_ECM = 1L, raiz_unitaria = 1L,
                 johansen_test = 1L, terminos_ECT = 1L)
  ))
}
