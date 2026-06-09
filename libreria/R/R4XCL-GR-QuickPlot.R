#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# QUICK PLOT — Genera graficos R base en WebView2       +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

# .neven_webview_dir() is defined in R4XCL-0-Shared-WebView.R

GR_QuickPlot <- function(SetDatosX, SetDatosY=NULL, TipoGrafico=0, Titulo="RJ2XCL Chart", TipoOutput=0)
{
  if (TipoOutput <= 0){
    return(c(
      "[01] Barras",
      "[02] Lineas",
      "[03] Scatter",
      "[04] Histograma",
      "[05] Box Plot",
      "[06] Pie",
      "[07] ggplot2 Barras",
      "[08] ggplot2 Lineas",
      "[09] ggplot2 Scatter"
    ))
  }

  # Parsear datos del rango Excel
  nombres <- as.character(SetDatosX[1,])
  datos <- data.frame(SetDatosX[-1,, drop=FALSE], stringsAsFactors=FALSE)
  colnames(datos) <- nombres
  x_vals <- as.character(datos[,1])
  for (i in 2:ncol(datos)) datos[,i] <- as.numeric(datos[,i])

  # Generar nombre unico
  ts <- format(Sys.time(), "%Y%m%d_%H%M%S")
  ruta <- file.path(.neven_webview_dir(), paste0("quickplot_", ts, ".png"))

  # Dimensiones
  ancho <- 800
  alto <- 600

  if (TipoOutput <= 6) {
    # R base graphics → PNG
    png(ruta, width=ancho, height=alto, res=96)

    if (TipoOutput == 1) {
      # Barras
      mat <- as.matrix(datos[, -1, drop=FALSE])
      rownames(mat) <- x_vals
      barplot(t(mat), beside=TRUE, main=Titulo, col=rainbow(ncol(mat)),
              legend.text=nombres[-1], args.legend=list(x="topright"))
    } else if (TipoOutput == 2) {
      # Lineas
      plot(1:length(x_vals), datos[,2], type="b", main=Titulo,
           xlab=nombres[1], ylab="Valor", col="blue", pch=19, xaxt="n")
      axis(1, at=1:length(x_vals), labels=x_vals)
      if (ncol(datos) >= 3) {
        cols <- c("blue","red","green","purple","orange")
        for (i in 3:ncol(datos)) {
          lines(1:length(x_vals), datos[,i], type="b", col=cols[(i-1) %% length(cols) + 1], pch=19)
        }
        legend("topright", legend=nombres[-1], col=cols[1:(ncol(datos)-1)], lty=1, pch=19)
      }
    } else if (TipoOutput == 3) {
      # Scatter
      plot(datos[,2], datos[,min(3,ncol(datos))], main=Titulo,
           xlab=nombres[2], ylab=nombres[min(3,ncol(datos))],
           col="darkblue", pch=19, cex=1.5)
    } else if (TipoOutput == 4) {
      # Histograma
      hist(datos[,2], main=Titulo, xlab=nombres[2], col="steelblue", border="white")
    } else if (TipoOutput == 5) {
      # Box Plot
      boxplot(datos[,-1, drop=FALSE], main=Titulo, col=rainbow(ncol(datos)-1))
    } else if (TipoOutput == 6) {
      # Pie
      pie(datos[,2], labels=x_vals, main=Titulo, col=rainbow(length(x_vals)))
    }

    dev.off()
    return(ruta)

  } else {
    # ggplot2 → Plotly → HTML
    library(ggplot2)
    library(plotly)
    library(htmlwidgets)

    # Reshape para ggplot
    df_long <- data.frame(
      x = rep(x_vals, ncol(datos)-1),
      valor = unlist(datos[,-1]),
      serie = rep(nombres[-1], each=nrow(datos)),
      stringsAsFactors = FALSE
    )
    df_long$valor <- as.numeric(df_long$valor)

    if (TipoOutput == 7) {
      p <- ggplot(df_long, aes(x=x, y=valor, fill=serie)) +
        geom_col(position="dodge") + ggtitle(Titulo) + theme_minimal()
    } else if (TipoOutput == 8) {
      p <- ggplot(df_long, aes(x=x, y=valor, color=serie, group=serie)) +
        geom_line(linewidth=1) + geom_point(size=3) + ggtitle(Titulo) + theme_minimal()
    } else if (TipoOutput == 9) {
      p <- ggplot(datos, aes_string(x=nombres[2], y=nombres[min(3,ncol(datos))])) +
        geom_point(size=3, color="darkblue") + ggtitle(Titulo) + theme_minimal()
    }

    ruta_html <- file.path(.neven_webview_dir(), paste0("quickplot_", ts, ".html"))
    saveWidget(ggplotly(p), ruta_html, selfcontained=TRUE)
    return(ruta_html)
  }
}

attr(GR_QuickPlot, "description") = list(
  "Genera graficos rapidos para WebView2 (R base + ggplot2)",
  SetDatosX="Rango con encabezados",
  SetDatosY="No utilizado",
  TipoGrafico="No utilizado",
  Titulo="Titulo del grafico",
  TipoOutput="0:Procedimientos, 1-6:R base (Barras/Lineas/Scatter/Hist/Box/Pie), 7-9:ggplot2"
)
