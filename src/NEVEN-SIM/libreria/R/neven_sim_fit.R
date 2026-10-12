# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN-SIM: Distribution Fitting Service for R
# ═══════════════════════════════════════════════════════════════════════════════
#
# Provides automatic distribution fitting using fitdistrplus.
# Called by NEVEN-SIM.xll via the SimBridge (=NEVEN.r() relay).
#
# Required packages: fitdistrplus, MASS
# Optional: jsonlite (for structured output)
#
# Copyright (c) 2026 NEVEN Project — GPL v3

#' Ajusta multiples distribuciones candidatas a un vector de datos.
#'
#' @param data_vec Numeric vector de datos historicos.
#' @return JSON string con resultados de ajuste ranqueados por AIC.
#'
#' @details
#' Distribuciones candidatas: Normal, LogNormal, Gamma, Weibull,
#' Exponencial, Uniforme, Beta.
#' 
#' Solo intenta distribuciones validas para los datos:
#' - LogNormal/Gamma/Weibull requieren datos positivos
#' - Beta requiere datos en [0, 1]
.neven_sim_fit <- function(data_vec) {
    if (!requireNamespace("fitdistrplus", quietly = TRUE)) {
        return("[ERROR] Paquete 'fitdistrplus' no instalado. Use =R.instalar(\"fitdistrplus\")")
    }
    library(fitdistrplus)

    # Determinar candidatos validos
    candidates <- c("norm", "exp", "unif")
    if (min(data_vec) > 0) {
        candidates <- c(candidates, "lnorm", "gamma", "weibull")
    }
    if (min(data_vec) >= 0 && max(data_vec) <= 1) {
        candidates <- c(candidates, "beta")
    }

    results <- list()
    for (dist in candidates) {
        tryCatch({
            fit <- fitdist(data_vec, dist)
            gof <- gofstat(fit)
            results[[dist]] <- list(
                params = as.list(fit$estimate),
                aic = fit$aic,
                bic = fit$bic,
                ks_stat = gof$ks,
                ad_stat = ifelse(is.null(gof$ad), NA, gof$ad)
            )
        }, error = function(e) NULL)
    }

    if (length(results) == 0) {
        return("[ERROR] No se pudo ajustar ninguna distribucion")
    }

    # Retornar como JSON si jsonlite esta disponible
    if (requireNamespace("jsonlite", quietly = TRUE)) {
        return(jsonlite::toJSON(results, auto_unbox = TRUE))
    }

    # Fallback: formato texto estructurado
    entries <- sapply(names(results), function(n) {
        r <- results[[n]]
        params_str <- paste(names(r$params), round(unlist(r$params), 6),
                            sep = "=", collapse = ",")
        paste(n, params_str, round(r$aic, 2), round(r$ks_stat, 6), sep = "|")
    })
    paste(entries, collapse = ";;")
}


#' Ajusta una distribucion especifica a los datos.
#'
#' @param data_vec Numeric vector de datos.
#' @param dist_name Nombre de la distribucion (ej: "norm", "gamma").
#' @return String con parametros ajustados o error.
.neven_sim_fit_one <- function(data_vec, dist_name) {
    if (!requireNamespace("fitdistrplus", quietly = TRUE)) {
        return("[ERROR] Paquete 'fitdistrplus' no instalado")
    }
    library(fitdistrplus)

    tryCatch({
        fit <- fitdist(data_vec, dist_name)
        gof <- gofstat(fit)
        params_str <- paste(names(fit$estimate), round(fit$estimate, 6),
                            sep = "=", collapse = ", ")
        paste0(dist_name, ": ", params_str,
               " | AIC=", round(fit$aic, 2),
               " | KS=", round(gof$ks, 6))
    }, error = function(e) {
        paste0("[ERROR] ", dist_name, ": ", e$message)
    })
}


#' Resumen grafico del ajuste (genera HTML con histograma + PDF superpuesta).
#'
#' @param data_vec Datos historicos.
#' @param dist_name Distribucion a graficar.
#' @return HTML string para WebView2.
.neven_sim_fit_plot <- function(data_vec, dist_name) {
    if (!requireNamespace("fitdistrplus", quietly = TRUE)) {
        return("[ERROR] fitdistrplus no instalado")
    }
    library(fitdistrplus)

    tryCatch({
        fit <- fitdist(data_vec, dist_name)
        
        # Generar datos para la curva PDF
        x_range <- seq(min(data_vec), max(data_vec), length.out = 200)
        pdf_func <- match.fun(paste0("d", dist_name))
        pdf_vals <- do.call(pdf_func, c(list(x_range), as.list(fit$estimate)))

        # Retornar como JSON para Plotly en el WebViewer
        if (requireNamespace("jsonlite", quietly = TRUE)) {
            result <- list(
                histogram_data = data_vec,
                pdf_x = x_range,
                pdf_y = pdf_vals,
                dist_name = dist_name,
                params = as.list(fit$estimate),
                aic = fit$aic
            )
            return(jsonlite::toJSON(result, auto_unbox = TRUE))
        }
        return("OK")
    }, error = function(e) {
        paste0("[ERROR] ", e$message)
    })
}
