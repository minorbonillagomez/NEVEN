# ===============================================================================
# NEVEN Data Lab — MÍNIMOS CUADRADOS EN DOS ETAPAS / VARIABLES INSTRUMENTALES
# (RG Family) — 2SLS / IV Regression
# Wooldridge Cap. 15 — Tratamiento de endogeneidad
# ===============================================================================
# DESCRIPCIÓN:
#   2SLS corrige el sesgo de endogeneidad cuando una o más variables explicativas
#   están correlacionadas con el error (por variable omitida, error de medición
#   o causalidad inversa). Se usan instrumentos Z que satisfacen:
#     - Relevancia: corr(Z, X_endo) ≠ 0   (verificado con F > 10 en 1ª etapa)
#     - Exogeneidad: corr(Z, u) = 0       (supuesto no testeable directamente)
#
#   Ejemplo clásico: retorno a la educación con educación endógena
#   e instrumento = educación del padre (Wooldridge: wage2, mroz)
#
# PAQUETE: AER::ivreg (Instrumental Variables Regression)
# ===============================================================================

RG_2SLS.Studio <- function(data_Y,
                             data_Endo,
                             data_Exo       = NULL,
                             data_Instru,
                             NivelAlpha     = 0.05,
                             DiagnosticosF  = TRUE) {

  # ── Validaciones ─────────────────────────────────────────────────────────────
  if (!is.data.frame(data_Y) || nrow(data_Y) == 0)
    stop("'data_Y' debe ser un data.frame con al menos una fila.")
  if (!is.data.frame(data_Endo) || nrow(data_Endo) == 0)
    stop("'data_Endo' (variables endógenas) debe ser un data.frame.")
  if (!is.data.frame(data_Instru) || nrow(data_Instru) == 0)
    stop("'data_Instru' (instrumentos Z) debe ser un data.frame.")
  if (ncol(data_Instru) < ncol(data_Endo))
    stop("Se necesitan al menos tantos instrumentos como variables endógenas (condición de orden).")

  n_endo  <- ncol(data_Endo)
  n_instr <- ncol(data_Instru)
  if (nrow(data_Y) != nrow(data_Endo) || nrow(data_Y) != nrow(data_Instru))
    stop("Todos los data.frames deben tener el mismo número de filas.")

  NivelAlpha <- as.numeric(NivelAlpha)
  if (is.na(NivelAlpha) || NivelAlpha <= 0 || NivelAlpha >= 1) NivelAlpha <- 0.05

  if (!requireNamespace("AER", quietly = TRUE))
    stop("El paquete 'AER' no está instalado. Use =R.UT_InstalacionWeb() para instalarlo.")
  if (!requireNamespace("lmtest", quietly = TRUE))
    stop("El paquete 'lmtest' no está instalado.")

  # ── Construcción del data.frame completo ────────────────────────────────────
  y_col     <- names(data_Y)[1]
  endo_cols <- names(data_Endo)
  inst_cols <- names(data_Instru)

  has_exo <- !is.null(data_Exo) && is.data.frame(data_Exo) && ncol(data_Exo) > 0
  exo_cols <- if (has_exo) names(data_Exo) else character(0)

  df <- cbind(data_Y[, y_col, drop = FALSE], data_Endo, data_Instru)
  if (has_exo) df <- cbind(df, data_Exo)
  df <- df[complete.cases(df), ]
  n  <- nrow(df)

  # ── Fórmula ivreg: y ~ X_endo + X_exo | X_exo + Z ──────────────────────────
  # AER::ivreg usa notación: depvar ~ regressors | instruments
  # El lado derecho del | incluye las exógenas (que se instrumentan a sí mismas)
  # más los instrumentos externos Z

  regressors   <- c(endo_cols, exo_cols)
  instruments  <- c(exo_cols, inst_cols)

  fml_iv <- as.formula(
    paste0(y_col, " ~ ",
           paste(regressors, collapse = " + "),
           " | ",
           paste(instruments, collapse = " + "))
  )

  # ── Estimación 2SLS ──────────────────────────────────────────────────────────
  modelo_iv <- tryCatch(
    AER::ivreg(fml_iv, data = df),
    error = function(e) stop(paste("Error en 2SLS:", conditionMessage(e)))
  )

  sm_iv <- summary(modelo_iv, diagnostics = isTRUE(DiagnosticosF))

  # ── Tabla científica 2SLS — texto plano estilo consola R ─────────────────────
  tabla_cientifica_2sls <- tryCatch({
    paste(capture.output(print(sm_iv)), collapse = "\n")
  }, error = function(e) {
    paste("Error al generar resumen 2SLS:", conditionMessage(e))
  })

  # ── Tabla de coeficientes 2SLS (para referencia en tier 2) ──────────────────
  ct <- as.data.frame(sm_iv$coefficients)
  tabla_2sls <- data.frame(
    Variable    = rownames(ct),
    Coeficiente = round(ct[, 1], 6),
    EE          = round(ct[, 2], 6),
    t_stat      = round(ct[, 3], 4),
    p_valor     = round(ct[, 4], 6),
    Sig         = ifelse(ct[, 4] < 0.001, "***",
                  ifelse(ct[, 4] < 0.01,  "**",
                  ifelse(ct[, 4] < 0.05,  "*",
                  ifelse(ct[, 4] < 0.10,  ".", "")))),
    stringsAsFactors = FALSE
  )

  # ── Diagnósticos: F primera etapa + Wu-Hausman + Sargan ─────────────────────
  diag_rows <- list()

  if (isTRUE(DiagnosticosF) && !is.null(sm_iv$diagnostics)) {
    diags <- sm_iv$diagnostics
    for (i in seq_len(nrow(diags))) {
      nm  <- rownames(diags)[i]
      # Manejar NA en estadístico y p-valor (ej: Sargan exactamente identificado)
      stat_val <- diags[i, "statistic"]
      pval_val <- diags[i, "p-value"]
      stat_safe <- if (!is.na(stat_val)) round(stat_val, 4) else NA
      pval_safe <- if (!is.na(pval_val)) round(pval_val, 6) else NA

      # Grados de libertad: df1/df2 (AER >= 1.2-9) o df (versiones anteriores)
      gl_val <- if ("df1" %in% colnames(diags)) {
        df1 <- diags[i, "df1"]; df2 <- diags[i, "df2"]
        if (!is.na(df1) && !is.na(df2)) paste0(df1, "/", df2)
        else if (!is.na(df1)) as.character(df1)
        else NA
      } else if ("df" %in% colnames(diags)) {
        diags[i, "df"]
      } else NA

      # Interpretación — omitir si faltan datos
      interp <- if (is.na(stat_safe) && is.na(pval_safe)) {
        switch(nm,
          "Sargan" = "Modelo exactamente identificado: test de Sargan no aplica (0 grados de libertad).",
          paste0("Test ", nm, " no disponible.")
        )
      } else {
        switch(nm,
          "Weak instruments" = if (!is.na(stat_safe) && stat_safe >= 10)
            sprintf("Instrumentos relevantes (F=%.1f >= 10)", stat_safe)
          else
            sprintf("ADVERTENCIA: Instrumentos debiles (F=%.1f < 10). Resultados no confiables.", stat_safe),
          "Wu-Hausman" = if (!is.na(pval_safe) && pval_safe < NivelAlpha)
            sprintf("Endogeneidad confirmada (p=%.4f < alpha). 2SLS es necesario.", pval_safe)
          else
            sprintf("No se rechaza exogeneidad (p=%.4f). MCO podria ser suficiente.", pval_safe),
          "Sargan" = if (!is.na(pval_safe) && pval_safe > NivelAlpha)
            sprintf("Instrumentos validos (p=%.4f > alpha). No se rechaza exogeneidad de Z.", pval_safe)
          else
            sprintf("ADVERTENCIA: Sargan rechaza (p=%.4f). Posible instrumento invalido.", pval_safe),
          paste0("Test ", nm)
        )
      }

      diag_rows[[nm]] <- data.frame(
        Test           = nm,
        Estadistico    = stat_safe,
        gl             = gl_val,
        p_valor        = pval_safe,
        Interpretacion = interp,
        stringsAsFactors = FALSE
      )
    }
  }

  # ── Diagnósticos como texto plano (evita problemas de encoding en tablas) ────
  diag_texto <- if (length(diag_rows) > 0) {
    tbl <- do.call(rbind, diag_rows)
    paste(capture.output(print(tbl, row.names = FALSE)), collapse = "\n")
  } else {
    "Activar DiagnosticosF=TRUE para ver F primera etapa, Wu-Hausman y Sargan."
  }

  # ── Bondad de ajuste — texto plano con alineación ───────────────────────────
  tabla_ajuste <- data.frame(
    Estadistico  = c("Observaciones", "Variables_endo", "Instrumentos_ext",
                     "R_cuadrado", "Sigma_residual"),
    Valor        = c(n, n_endo, n_instr - n_endo,
                     round(sm_iv$r.squared, 4),
                     round(sm_iv$sigma, 6)),
    stringsAsFactors = FALSE
  )

  bondad_txt <- local({
    m <- tabla_ajuste; vals <- as.character(m[[2]]); keys <- as.character(m[[1]])
    w_k <- max(nchar(keys)); w_v <- max(nchar(vals))
    paste(c(paste0(formatC("Estadistico",width=-w_k),"  ",formatC("Valor",width=w_v)),
            strrep("-",w_k+w_v+2),
            mapply(function(k,v) paste0(formatC(k,width=-w_k),"  ",formatC(v,width=w_v)),keys,vals)),
          collapse="\n")
  })

  # ── Gráfico residuos vs ajustados ────────────────────────────────────────────
  html_graf <- tryCatch({
    fit_vals <- round(fitted(modelo_iv), 4)
    res_vals <- round(residuals(modelo_iv), 4)
    n_show   <- min(length(fit_vals), 300L)
    traces <- list(
      list(type="scatter", mode="markers",
           x=fit_vals[1:n_show], y=res_vals[1:n_show],
           marker=list(size=5, color="#d7a538", opacity=0.6),
           hovertext=paste0("Ajust:",fit_vals[1:n_show]," Resid:",res_vals[1:n_show]),
           hoverinfo="text", showlegend=FALSE),
      list(type="scatter", mode="lines",
           x=range(fit_vals), y=c(0,0),
           line=list(color="rgba(215,165,56,0.4)",width=1,dash="dash"),
           showlegend=FALSE, hoverinfo="none")
    )
    layout <- list(
      title=list(text="2SLS: Residuos vs Valores Ajustados",
                 font=list(color="#e0e0e0",size=12)),
      xaxis=list(title="Valores ajustados",color="#888",gridcolor="#333",zerolinecolor="#555"),
      yaxis=list(title="Residuos",color="#888",gridcolor="#333",zeroline=TRUE,zerolinecolor="#555"),
      paper_bgcolor="#373434", plot_bgcolor="#373434",
      font=list(color="#888"), margin=list(t=50,r=20,b=50,l=60)
    )
    fig_json <- iconv(jsonlite::toJSON(list(data=traces,layout=layout),
                                        auto_unbox=TRUE, na="null"),
                      from="UTF-8", to="UTF-8", sub="byte")
    paste0('<html><body><neven-plotly>',
           jsonlite::base64_enc(chartr("\n\r","  ",fig_json)),
           '</neven-plotly></body></html>')
  }, error = function(e) {
    paste0('<html><body><p style="color:#888;padding:8px">Grafico no disponible</p></body></html>')
  })

  return(r_object_to_slots(
    list(
      tabla_cientifica  = tabla_cientifica_2sls,
      diagnosticos_IV   = diag_texto,
      bondad_ajuste     = bondad_txt,
      grafico           = html_graf,
      coeficientes_2SLS = tabla_2sls
    ),
    tier_map = c(tabla_cientifica=1L, diagnosticos_IV=1L,
                 bondad_ajuste=1L, grafico=1L, coeficientes_2SLS=2L)
  ))
}
