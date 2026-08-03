#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# INSTALAR PAQUETES
#
# Instala un conjunto de paquetes de R con una interfaz grafica.
#
# Esta función permite al usuario seleccionar paquetes de una lista
# predefinida a traves de una ventana de dialogo. Se utiliza un repositorio
# CRAN especifico para asegurar la reproducibilidad (WEB) también se 
# incluye la opción de instalar desde un repositorio local
# No devuelve un valor, pero instala los paquetes seleccionados.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

UT_INSTALACION_LOCAL <- function(directorio, TipoOutput = 0) {
  # =========================================================================
  # CM-BAJ-014: Función reescrita v2.3 — versiones 2017-2018 incompatibles con R 4.4.1
  # Esta función instalaba paquetes desde .tar.gz locales con versiones obsoletas.
  # Reemplazada por instalación desde CRAN con versiones actuales.
  # =========================================================================

  tiempo_inicio <- Sys.time()
  Procedimientos <- R4XCL_INT_PROCEDIMIENTOS()

  if (TipoOutput == 0) {
    return(Procedimientos$INSTALA)
  }

  # Catálogo actualizado de paquetes por grupo — versiones tomadas de CRAN (agosto 2026)
  grupos <- list(
    `1`  = c("svMisc", "svGUI", "svDialogs"),
    `2`  = c("devtools", "R6", "httr", "digest", "rstudioapi"),
    `3`  = c("rworldmap", "raster", "terra", "maptools"),
    `4`  = c("stargazer"),
    `5`  = c("plm", "sandwich", "lmtest", "zoo"),
    `6`  = c("rpart.plot"),
    `7`  = c("margins", "ResourceSelection", "pbapply"),
    `8`  = c("tm"),
    `9`  = c("SnowballC"),
    `10` = c("wordcloud", "RColorBrewer"),
    `11` = c("PerformanceAnalytics", "xts", "quadprog"),
    `12` = c("rlang"),
    `13` = c("stargazer"),
    `14` = c("dummies"),
    `15` = c("wooldridge"),
    `16` = c("dplyr", "dbplyr", "dtplyr"),
    `17` = c("e1071")
  )

  paquetes <- grupos[[as.character(TipoOutput)]]

  if (is.null(paquetes)) {
    return(paste0("TipoOutput ", TipoOutput, " no válido. Use 0 para ver procedimientos."))
  }

  df_errores <- data.frame(Resultado = character(), stringsAsFactors = FALSE)

  for (pkg in paquetes) {
    resultado <- tryCatch({
      if (!requireNamespace(pkg, quietly = TRUE)) {
        install.packages(pkg, repos = "https://cloud.r-project.org", quiet = TRUE)
      }
      paste0("✓ [", pkg, "] instalado/disponible.")
    }, error = function(e) {
      paste0("✗ [", pkg, "] error: ", e$message)
    })
    df_errores <- rbind(df_errores, data.frame(Resultado = resultado, stringsAsFactors = FALSE))
    cat(resultado, "\n")
  }

  tiempo_fin <- Sys.time()
  seg <- as.numeric(difftime(tiempo_fin, tiempo_inicio, units = "secs"))
  msg <- paste0("Proceso completado en ", floor(seg / 60), "m ", round(seg %% 60), "s")
  df_errores <- rbind(df_errores,
                      data.frame(Resultado = c("----------", msg), stringsAsFactors = FALSE))
  return(df_errores)
}

UT_INSTALACION_WEB <- function() 
{
  
  # 0. Guardar y restaurar la configuracion de repositorios
  
  old_repos <- getOption("repos")
  on.exit(options(repos = old_repos))
  
  repositorio_cran <- "https://packagemanager.rstudio.com/cran/2022-05-06"
  
  options(repos = c(CRAN = repositorio_cran))
  options(install.packages.compile.from.source = "always")
  
  paquetes=c("svDialogs")
  
  # 1. Verificar si el paquete svDialogs esta instalado
  if (!requireNamespace(paquetes, quietly = TRUE)) 
    {
      install.packages(paquetes_no_instalados, dependencies = TRUE)
      library(paquete, character.only = TRUE)
    }
  

  # Lista de paquetes disponibles para la seleccion del usuario
  paquetes_disponibles <- c(
    "svGUI", 
    "svMIsc",
    "svDialogstcltk",
    "dplyr",
    "ggplot2",
    "readr",
    "tidyr",
    "lubridate",
    "rmarkdown",
    "knitr",
    "shiny",
    "renv",
    "devtools",
    "rworldmap",
    "stargazer",
    "plm",
    "usdm",
    "margins",
    "rpart.plot",
    "ResourceSelection",
    "tm",
    "SnowballC",
    "wordcloud",
    "RColorBrewer",
    "PerformanceAnalytics",
    "rlang",
    "dummies",
    "wooldridge",
    "e1071",
    "xgboost"
  )
  
  elementoActual=1
  
  # Definir el repositorio CRAN con snapshot
  repositorio_cran <- "https://packagemanager.rstudio.com/cran/2018-03-15"
  
  # Anadir la opcion para instalar todos los paquetes
  opciones_disponibles <- c("*** Instalar todos los paquetes ***", paquetes_disponibles)
  
  # 2. Abrir un cuadro de dialogo para que el usuario seleccione los paquetes
  opciones_seleccion <- svDialogs::dlg_list(
    choices = opciones_disponibles,
    multiple = TRUE,
    title = "Seleccione los paquetes que desea instalar"
  )$res
  
  # Verificar si el usuario cancelo la seleccion
  if (is.null(opciones_seleccion) || length(opciones_seleccion) == 0) {
    svDialogs::dlg_message("Proceso cancelado por el usuario.", type = "ok", gui = "info")$res
    return(invisible(NULL))
  }
  
  # Determinar la lista final de paquetes a instalar
  if ("*** Instalar todos los paquetes ***" %in% opciones_seleccion) {
    paquetes_a_instalar <- paquetes_disponibles
    print(paquetes_a_instalar)
  } else {
    paquetes_a_instalar <- opciones_seleccion
    print(paquetes_a_instalar)
  }
  
  nPaquetes=length(paquetes_a_instalar)
  
  # 3. Guardar y restaurar la configuracion de repositorios
  old_repos <- getOption("repos")
  on.exit(options(repos = old_repos))
  
  options(repos = c(CRAN = repositorio_cran))
  
  svDialogs::dlg_message(
    sprintf("Iniciando la instalacion desde el repositorio:\n %s", repositorio_cran),
    title = "Inicio del proceso"
  )$res
  
  # 4. Bucle de instalacion con dialogos de progreso y error
  
  for (paquete in paquetes_a_instalar) {
    
    # El mensaje del cafe aparece ANTES de iniciar la instalacion de cada paquete
    svDialogs::dlg_message(
      sprintf("Disfrute de un cafe (costarricense) mientras trabajamos por usted en la instalacion de los paquetes seleccionados.\n\nAhora vamos a instalar: %s", paste(paquete,"[",elementoActual,"/",nPaquetes,"]")),
      title = "R4XCL Procesando su solicitud"
    )$res
    
    elementoActual=elementoActual+1
    
    # Validacion: ¿El paquete ya esta instalado?
    if (requireNamespace(paquete, quietly = TRUE)) {
      svDialogs::dlg_message(
        sprintf("El paquete '%s' ya esta instalado. Saltando la instalacion.", paquete),
        title = "R4XCL Paquete ya existente"
      )$res
      next # Pasa al siguiente paquete
    }
    
    # Manejo de errores durante la instalacion
    tryCatch({
      install.packages(paquete, dependencies = TRUE)
      svDialogs::dlg_message(
        sprintf("El paquete '%s' se instalo con exito.", paquete),
        title = "R4XCL Instalacion exitosa"
      )$res
    },
    error = function(e) {
      svDialogs::dlg_message(
        sprintf("Error al instalar el paquete '%s': %s", paquete, e$message),
        title = "R4XCL Error de instalacion",
        type = "ok",
        gui = "warning"
      )$res
    })
    
    
  }
  
  # Mensaje final de proceso completado
  svDialogs::dlg_message("Proceso de instalacion completado.", title = "Finalizado")$res
}
