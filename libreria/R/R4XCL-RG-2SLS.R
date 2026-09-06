#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# MODELO 2SLS -- VARIABLES INSTRUMENTALES (IV)
# Wooldridge, Cap. 15
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

MR_2SLS <- function(
    SetDatosY,
    SetDatosX,
    Escala         = 0,
    Filtro         = 0,
    Constante      = 1,
    SetInstrumentos,
    SetDatosExo    = NULL,
    NivelAlpha     = 0.05,
    TipoOutput     = 1
)
{
  #-------------------------->>>
  # [1] PREPARACION DE DATOS Y PARAMETROS
  #-------------------------->>>

  Procedimientos <- R4XCL_INT_PROCEDIMIENTOS()

  # Preparar Y y X endogenas
  DT_Y <- R4XCL_INT_DATOS(
    SetDatosY = SetDatosY,
    SetDatosX = SetDatosX,
    Escala    = Escala,
    Filtro    = Filtro
  )

  NombreY    <- colnames(DT_Y)[1]
  NombreEndo <- colnames(DT_Y)[-1]
  pNObs      <- nrow(DT_Y)

  # Preparar instrumentos: quitar header (primera fila)
  if (!is.null(SetInstrumentos) && is.data.frame(SetInstrumentos) && nrow(SetInstrumentos) > 1) {
    NombreZ <- as.character(SetInstrumentos[1, ])
    Z       <- SetInstrumentos[-1, , drop = FALSE]
    Z       <- as.data.frame(lapply(Z, function(x) as.numeric(as.character(x))))
    colnames(Z) <- NombreZ
  } else {
    return(data.frame(R4XCL_Error = "MR_2SLS: SetInstrumentos es requerido y debe tener al menos 2 filas (header + datos)."))
  }

  # Preparar variables exogenas de control (opcional)
  if (!is.null(SetDatosExo) && is.data.frame(SetDatosExo) && nrow(SetDatosExo) > 1) {
    NombreExo <- as.character(SetDatosExo[1, ])
    Exo       <- SetDatosExo[-1, , drop = FALSE]
    Exo       <- as.data.frame(lapply(Exo, function(x) as.numeric(as.character(x))))
    colnames(Exo) <- NombreExo
  } else {
    Exo       <- NULL
    NombreExo <- character(0)
  }

  # Construir data.frame completo para la estimacion
  DT_full <- DT_Y
  if (!is.null(Exo)) {
    for (col in colnames(Exo)) DT_full[[col]] <- Exo[[col]]
  }
  for (col in colnames(Z)) DT_full[[col]] <- Z[[col]]

  # Construir formulas para ivreg
  # Forma: Y ~ X_endo + X_exo | X_exo + Z
  lhs       <- NombreY
  endo_vars <- paste(NombreEndo, collapse = " + ")
  exo_vars  <- if (length(NombreExo) > 0) paste(NombreExo, collapse = " + ") else NULL
  z_vars    <- paste(colnames(Z), collapse = " + ")

  if (Constante == 0) {
    rhs_struct <- if (!is.null(exo_vars)) paste(endo_vars, exo_vars, sep = " + ") else endo_vars
    rhs_iv     <- if (!is.null(exo_vars)) paste(exo_vars, z_vars, sep = " + ") else z_vars
    formula_str <- paste0(lhs, " ~ ", rhs_struct, " - 1 | ", rhs_iv, " - 1")
  } else {
    rhs_struct <- if (!is.null(exo_vars)) paste(endo_vars, exo_vars, sep = " + ") else endo_vars
    rhs_iv     <- if (!is.null(exo_vars)) paste(exo_vars, z_vars, sep = " + ") else z_vars
    formula_str <- paste0(lhs, " ~ ", rhs_struct, " | ", rhs_iv)
  }

  formula_iv <- as.formula(formula_str)

  #-------------------------->>>
  # [2] ESTIMACION 2SLS
  #-------------------------->>>

  if (!requireNamespace("AER", quietly = TRUE)) {
    return(data.frame(R4XCL_Error = "MR_2SLS: paquete AER no instalado. Instalar con install.packages('AER')."))
  }

  Modelo2SLS <- tryCatch(
    AER::ivreg(formula_iv, data = DT_full),
    error = function(e) stop(paste("Error en estimacion 2SLS:", conditionMessage(e)))
  )

  # Primera etapa (para diagnostico de instrumentos debiles)
  PrimeraEtapa <- tryCatch({
    fe_vars <- if (!is.null(exo_vars)) paste(exo_vars, z_vars, sep = " + ") else z_vars
    fe_formula <- as.formula(paste0(NombreEndo[1], " ~ ", fe_vars))
    lm(fe_formula, data = DT_full)
  }, error = function(e) NULL)

  #-------------------------->>>
  # [3] DIAGNOSTICOS
  #-------------------------->>>

  # F de primera etapa (instrumentos debiles: F < 10 segun Staiger-Stock)
  F_stat <- tryCatch({
    if (!is.null(PrimeraEtapa)) summary(PrimeraEtapa)$fstatistic[1] else NA
  }, error = function(e) NA)

  # Test Wu-Hausman (endogeneidad)
  WuHausman <- tryCatch(
    summary(Modelo2SLS, diagnostics = TRUE)$diagnostics,
    error = function(e) NULL
  )

  #-------------------------->>>
  # [4] PREPARACION DE RESULTADOS
  #-------------------------->>>

  if (TipoOutput <= 0) {

    OutPut <- Procedimientos$INST_2SLS

  } else if (TipoOutput == 1) {

    # Tabla 2SLS con stargazer
    if (!requireNamespace("stargazer", quietly = TRUE)) {
      OutPut <- data.frame("R4XCL_ModeloEstimado" = capture.output(summary(Modelo2SLS)))
    } else {
      library(stargazer)
      OutPut <- data.frame("R4XCL_ModeloEstimado" = stargazer(
        Modelo2SLS, type = "text",
        ci = TRUE, ci.level = (1 - NivelAlpha),
        single.row = TRUE, align = TRUE
      ))
    }

  } else if (TipoOutput == 2) {

    # Prediccion dentro de muestra
    OutPut <- data.frame("R4XCL_PrediccionDentroDeMuestra" = fitted(Modelo2SLS))

  } else if (TipoOutput == 3) {

    # Test de endogeneidad Wu-Hausman
    if (!is.null(WuHausman)) {
      OutPut <- data.frame(
        "R4XCL_Diagnostico" = rownames(WuHausman),
        "Estadistico" = round(WuHausman[, "statistic"], 4),
        "P_valor"     = round(WuHausman[, "p-value"],   4)
      )
    } else {
      OutPut <- data.frame("R4XCL_Diagnostico" = capture.output(summary(Modelo2SLS, diagnostics = TRUE)))
    }

  } else if (TipoOutput == 4) {

    # Test de instrumentos debiles (F primera etapa)
    f_val  <- round(as.numeric(F_stat), 4)
    alerta <- if (!is.na(f_val) && f_val < 10) "ALERTA: instrumentos debiles (F < 10)" else "Instrumentos adecuados (F >= 10)"
    OutPut <- data.frame(
      "R4XCL_InstrumentosDebiles" = c(
        paste0("F primera etapa: ", f_val),
        alerta,
        "Referencia: Staiger & Stock (1997): F >= 10"
      )
    )

  } else if (TipoOutput == 5) {

    # Test de sobreidentificacion Sargan (solo si hay mas instrumentos que endogenas)
    n_endo <- length(NombreEndo)
    n_z    <- ncol(Z)
    if (n_z > n_endo) {
      OutPut <- tryCatch({
        if (!requireNamespace("lmtest", quietly = TRUE)) {
          data.frame("R4XCL_Sargan" = "Instalar paquete lmtest para este test")
        } else {
          resid_2sls <- residuals(Modelo2SLS)
          sargan_lm  <- lm(as.formula(paste("resid_2sls ~", paste(colnames(Z), collapse = " + "))), data = DT_full)
          n          <- length(resid_2sls)
          R2         <- summary(sargan_lm)$r.squared
          sargan_stat <- n * R2
          df_sargan  <- n_z - n_endo
          p_sargan   <- 1 - pchisq(sargan_stat, df = df_sargan)
          data.frame(
            "R4XCL_Sargan" = c(
              paste0("Estadistico Sargan: ", round(sargan_stat, 4)),
              paste0("Grados de libertad: ", df_sargan),
              paste0("P-valor: ", round(p_sargan, 4)),
              if (p_sargan > NivelAlpha) "Instrumentos validos (no se rechaza H0)" else "ALERTA: instrumentos invalidos (se rechaza H0)"
            )
          )
        }
      }, error = function(e) data.frame("R4XCL_Sargan" = paste("Error:", conditionMessage(e))))
    } else {
      OutPut <- data.frame("R4XCL_Sargan" = "Modelo exactamente identificado: test Sargan no aplicable (n_Z = n_endo).")
    }

  } else if (TipoOutput == 9) {

    # Informacion de ejecucion
    OutPut <- data.frame(
      "R4XCL_InfoEjecucion" = c(
        paste0("Formula: ", formula_str),
        paste0("N observaciones: ", pNObs),
        paste0("Variables endogenas: ", paste(NombreEndo, collapse = ", ")),
        paste0("Instrumentos Z: ", paste(colnames(Z), collapse = ", ")),
        if (length(NombreExo) > 0) paste0("Controles exogenos: ", paste(NombreExo, collapse = ", ")) else "Sin controles exogenos",
        paste0("Alpha: ", NivelAlpha)
      )
    )

  } else {

    OutPut <- data.frame("R4XCL_Error" = paste0("TipoOutput=", TipoOutput, " no disponible. Use TipoOutput=0 para ver opciones."))

  }

  #-------------------------->>>
  # [4] RESULTADO FINAL
  #-------------------------->>>

  return(OutPut)
}

DialogosXCL <- R4XCL_INT_DIALOGOS()

attr(MR_2SLS, DialogosXCL$Descripcion) =

  list(
    Detalle.2SLS     = "Estimacion 2SLS para correccion de endogeneidad",
    SetDatosY        = DialogosXCL$SetDatosY,
    SetDatosX        = "Variables endogenas X (rango con header)",
    Escala           = DialogosXCL$Escala,
    Filtro           = DialogosXCL$Filtro,
    Constante        = DialogosXCL$Constante,
    SetInstrumentos  = "Instrumentos externos Z (rango con header, requerido)",
    SetDatosExo      = "Variables exogenas de control (rango con header, opcional)",
    NivelAlpha       = "Nivel de significancia (default: 0.05)",
    TipoOutput       = "1=Tabla 2SLS, 2=Prediccion, 3=Wu-Hausman, 4=F instrumentos, 5=Sargan, 9=Info"
  )

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# FIN DE PROCEDIMIENTO
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
