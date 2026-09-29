#+++++++++++++++++++++++++++++++++++++++++++++++++++++++    
# ANALISIS DE COMPONENTES PRINCIPALES                  +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

AD_ACP.C <- function(
                     SetDatosX, 
                     Escala=0,
                     Filtro=NULL,
                     TipoOutput=0, 
                     SetDatosPredecir=NULL
                     )
{
  
  # PerformanceAnalytics se carga solo cuando se necesita (TipoOutput==3)
  
  #-------------------------->>>   
  # VALIDACIONES
  #-------------------------->>>  
  #  
  # if (!is.data.frame(SetDatosX)) {
  #                                 stop("Error: SetDatosX debe ser un data frame.")
  #                                }

  #-------------------------->>>   
  # [1] PREPARACION DE DATOS Y PARAMETROS  
  #-------------------------->>>  
  
  Procedimientos = R4XCL_INT_PROCEDIMIENTOS()

  DT = R4XCL_INT_DATOS(
                        SetDatosX=SetDatosX,
                        Escala=Escala,
                        Filtro=Filtro
                      )

  
  P  = ncol(DT)
  N  = nrow(DT)
  
  #-------------------------->>> 
  # [2] PROCEDIMIENTO ANALITICO
  #-------------------------->>> 
  
  res.pca   = princomp(DT,cor = TRUE)
  
  #-------------------------->>> 
  # [3] PREPARACION DE RESULTADOS
  #-------------------------->>> 
  
  if (TipoOutput <= 0){
    
    OutPut = Procedimientos$ACP
    
  }else if(TipoOutput == 1){
    
    OutPut =  cor(DT)
    
  }else if(TipoOutput == 2){
    
    OutPut =  cov(DT)
    
  }else if(TipoOutput == 3){   
    
    if (!requireNamespace("PerformanceAnalytics", quietly=TRUE)) {
      OutPut <- "Paquete PerformanceAnalytics no instalado. Ejecute: =R.instalar(\"PerformanceAnalytics\")"
    } else {
      library(PerformanceAnalytics)
      BERT.graphics.device(cell = T)
      chart.Correlation(DT, histogram=TRUE)
      dev.off()
      OutPut =  "Grafico de Correlaciones Ejecutado"
    }
    
  }else if(TipoOutput == 4){
    
    A       = res.pca$loadings
    SIGMA_2 = res.pca$sdev^2
    OutPut  = rbind(A,SIGMA_2)  
    
  }else if(TipoOutput == 5){ 
    
    #:::::::::::::::::::::::::::::::    
    # Coordenadas de Individuos
    #:::::::::::::::::::::::::::::::
    
    OutPut =  res.pca$scores
    
  }else if(TipoOutput == 6){ 
    
    #:::::::::::::::::::::::::::::::    
    # COS^2 de Individuos
    #:::::::::::::::::::::::::::::::
    
    # PCA CENTROS DE GRAVEDAD
    getd2 = function(x_i, center, scale){return(sum(((x_i-center)/scale)^2))}
    
    x_i   = res.pca$scores
    
    cos2  = function(x_i, d2){return(x_i^2/d2)}
    
    center= res.pca$center
    scale = res.pca$scale
    
    d2    = apply(DT,1,getd2, center, scale)
    
    OutPut= apply(x_i, 2, cos2, d2)
    
  }else if(TipoOutput == 7){   
    
    #:::::::::::::::::::::::::::::::
    # Contribucion de individuos
    #:::::::::::::::::::::::::::::::
    
    x_i   = res.pca$scores
    
    contrib <- function(x_i, comp.sdev, n.ind){100*(1/n.ind)*x_i^2/comp.sdev^2}
    
    OutPut = t(apply(x_i, 1, contrib, res.pca$sdev, nrow(x_i)))    
    
  }else if(TipoOutput == 8){  
    
    #:::::::::::::::::::::::::::::::    
    # Coordenadas de Variables
    #:::::::::::::::::::::::::::::::
    
    OutPut = cbind("Valores Propios"=res.pca$sdev^2,
                   "Aporte a la Varianza"=res.pca$sdev^2/sum(res.pca$sdev^2),
                   "Aporte Acumulado"=cumsum(res.pca$sdev^2/sum(res.pca$sdev^2)))
    
  }else if(TipoOutput == 9){    
    
    #:::::::::::::::::::::::::::::::    
    # COS^2 de variables
    #:::::::::::::::::::::::::::::::
    
    var_coord_func <- function(loadings, comp.sdev){loadings*comp.sdev}
    
    loadings  <- res.pca$loadings
    sdev      <- res.pca$sdev
    var.coord <- t(apply(loadings, MARGIN = 1, var_coord_func, sdev)) 
    OutPut    <- var.coord^2
    
  }else if(TipoOutput == 10){     
    
    #:::::::::::::::::::::::::::::::
    # Contribucion de variables
    #:::::::::::::::::::::::::::::::
    
    contrib   <- function(var.cos2, comp.cos2){var.cos2*100/comp.cos2}
    var_coord_func <- function(loadings, comp.sdev){loadings*comp.sdev}
    
    loadings  <- res.pca$loadings
    sdev      <- res.pca$sdev
    var.coord <- t(apply(loadings, MARGIN = 1, var_coord_func, sdev)) 
    var.cos2  <- var.coord^2 
    comp.cos2 <- apply(var.cos2, MARGIN = 2, FUN = sum)
    
    OutPut    <- t(apply(var.cos2, MARGIN = 1, contrib, comp.cos2))
    
  }else if(TipoOutput == 11){  
    
    if(missing(SetDatosPredecir)){
      
      OutPut <- res.pca$scores
      
    }else{
      
      DatosX <- SetDatosPredecir[-1,]
      DatosX <- matrix(as.numeric(DatosX), nrow=nrow(DatosX), ncol=p)
      DatosX <- data.frame(DatosX)
      colnames(DatosX)[1:p]=nombresX[1:p]
      
      A <- predict(res.pca, newdata = ind.sup)
      OutPut <- data.frame("R4XCL_PrediccionFueraDeMuestra"= A)
      
    } 
    
  }else if(TipoOutput == 12){    
    BERT.graphics.device(cell = T)
    biplot(res.pca, scale = 0)
    dev.off()
    OutPut <- "Biplot Ejecutado"
    
  }else if(TipoOutput == 13){
    
    OutPut <- Extraer_outputs(res.pca, "AD_ACP")
    
  }else if(TipoOutput == 99){
    # ═══════════════════════════════════════════════════════════════════════════
    # TipoOutput=99: Gráfico embebido como Shape en Excel
    # Genera biplot de ACP como PNG y retorna marcador especial para C++
    # ═══════════════════════════════════════════════════════════════════════════
    
    tryCatch({
      # Generar nombre único basado en timestamp
      chart_name <- paste0("ACP_", format(Sys.time(), "%H%M%S"))
      temp_file <- paste0("C:/NEVEN/temp/nevenx_", chart_name, ".png")
      
      # Dimensiones del gráfico
      width_px <- 500
      height_px <- 400
      
      # Generar biplot usando ggplot2 para mejor calidad
      if (requireNamespace("ggplot2", quietly = TRUE)) {
        library(ggplot2)
        
        # Extraer datos para el biplot
        scores <- as.data.frame(res.pca$scores[, 1:2])
        colnames(scores) <- c("PC1", "PC2")
        scores$id <- seq_len(nrow(scores))
        
        loadings <- as.data.frame(unclass(res.pca$loadings)[, 1:2])
        colnames(loadings) <- c("PC1", "PC2")
        loadings$variable <- rownames(loadings)
        
        # Escalar loadings para visualización
        scale_factor <- max(abs(scores$PC1), abs(scores$PC2)) / 
                        max(abs(loadings$PC1), abs(loadings$PC2)) * 0.8
        loadings$PC1 <- loadings$PC1 * scale_factor
        loadings$PC2 <- loadings$PC2 * scale_factor
        
        # Varianza explicada
        var_exp <- round(res.pca$sdev^2 / sum(res.pca$sdev^2) * 100, 1)
        
        # Crear biplot
        p <- ggplot() +
          # Puntos (individuos)
          geom_point(data = scores, aes(x = PC1, y = PC2), 
                     color = "#3498db", size = 2, alpha = 0.7) +
          geom_text(data = scores, aes(x = PC1, y = PC2, label = id),
                    vjust = -0.5, size = 2.5, color = "#2c3e50") +
          # Flechas (variables)
          geom_segment(data = loadings, 
                       aes(x = 0, y = 0, xend = PC1, yend = PC2),
                       arrow = arrow(length = unit(0.2, "cm")),
                       color = "#e74c3c", linewidth = 0.8) +
          geom_text(data = loadings, aes(x = PC1, y = PC2, label = variable),
                    vjust = -0.3, hjust = 0.5, size = 3, color = "#c0392b", fontface = "bold") +
          # Ejes y tema
          geom_hline(yintercept = 0, linetype = "dashed", color = "gray50", linewidth = 0.3) +
          geom_vline(xintercept = 0, linetype = "dashed", color = "gray50", linewidth = 0.3) +
          labs(title = "Biplot ACP",
               x = paste0("PC1 (", var_exp[1], "%)"),
               y = paste0("PC2 (", var_exp[2], "%)")) +
          theme_minimal() +
          theme(
            plot.title = element_text(hjust = 0.5, size = 12, face = "bold"),
            panel.grid.minor = element_blank()
          )
        
        # Guardar como PNG
        ggsave(temp_file, p, width = width_px/96, height = height_px/96, dpi = 96)
        
      } else {
        # Fallback: usar biplot base de R
        png(temp_file, width = width_px, height = height_px, res = 96)
        biplot(res.pca, scale = 0, main = "Biplot ACP")
        dev.off()
      }
      
      # Retornar marcador especial que C++ detectará
      OutPut <- data.frame(
        NEVEN_EMBED_CHART = temp_file,
        NEVEN_CHART_NAME = chart_name,
        NEVEN_CHART_WIDTH = width_px,
        NEVEN_CHART_HEIGHT = height_px,
        stringsAsFactors = FALSE
      )
      
    }, error = function(e) {
      OutPut <<- data.frame(R4XCL_Error = paste0("Error generando gráfico: ", conditionMessage(e)))
    })
    
  }else if(TipoOutput > 99){   
    
    OutPut <- "Revisar parámetros disponibles" 
    
  }  
  
  #-------------------------->>>   
  # [4] RESULTADO FINAL
  #-------------------------->>> 
  
  return(OutPut)
  
}

attr(AD_ACP.C, "description") = 
  list(
        Detalle          = "Análisis de Componentes Principales [ACP]",
        SetDatosX        = "Datos por Analizar",
        Escala           = "Escalar datos? 1:SI, 0:NO (0:Default)",
        Filtro           = "0:Incluir registro, 1:Excluir registro (0:Default)", 
        TipoOutput       = "1:Matriz de Correlación, 2:Coordenadas: Variables, 3:Coordenadas: Individuos, 4:COS^2: INDs, 5:Contribuci?n:INDs, 6:Valores Propios, 7:COS^2: VARs, 8:Contribuci?n:VARs, 9:Predicci?n, 10:Gr?fico VARs|INDs", 
        SetDatosPredecir = "Computar datos fuera de muestra"
      )