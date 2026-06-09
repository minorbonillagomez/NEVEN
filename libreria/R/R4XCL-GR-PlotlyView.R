#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# PLOTLY + WEBVIEW2 VIEWER                              +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

# .neven_webview_dir() is defined in R4XCL-0-Shared-WebView.R

GR_PlotlyView <- function(SetDatosX, SetDatosY=NULL, TipoGrafico=0, Titulo="RJ2XCL Chart", TipoOutput=0)
{
  library(plotly)
  library(htmlwidgets)

  if (TipoOutput <= 0){
    return(c("[01] Lineas","[02] Barras","[03] Scatter","[04] Area","[05] Combinado"))
  }

  nombres <- as.character(SetDatosX[1,])
  datos <- data.frame(SetDatosX[-1,, drop=FALSE], stringsAsFactors=FALSE)
  colnames(datos) <- nombres

  # First column = labels (keep as character), rest = numeric values
  x_vals <- as.character(datos[,1])
  for (i in 2:ncol(datos)) datos[,i] <- as.numeric(datos[,i])
  p <- plot_ly()

  if (TipoOutput == 1){
    for (i in 2:ncol(datos)) p <- add_trace(p, x=x_vals, y=datos[,i], type='scatter', mode='lines+markers', name=nombres[i])
  } else if (TipoOutput == 2){
    for (i in 2:ncol(datos)) p <- add_trace(p, x=x_vals, y=datos[,i], type='bar', name=nombres[i])
  } else if (TipoOutput == 3){
    p <- add_trace(p, x=x_vals, y=datos[,2], type='scatter', mode='markers', name=nombres[2])
  } else if (TipoOutput == 4){
    for (i in 2:ncol(datos)) p <- add_trace(p, x=x_vals, y=datos[,i], type='scatter', mode='lines', fill='tozeroy', name=nombres[i])
  } else if (TipoOutput == 5){
    p <- add_trace(p, x=x_vals, y=datos[,2], type='scatter', mode='lines+markers', name=nombres[2])
    if (ncol(datos) >= 3) for (i in 3:ncol(datos)) p <- add_trace(p, x=x_vals, y=datos[,i], type='bar', name=nombres[i])
  }

  p <- layout(p, title=Titulo, xaxis=list(title=nombres[1]), yaxis=list(title="Valor"))

  # Use unique filename per render to force WebView2 reload
  ts <- format(Sys.time(), "%Y%m%d_%H%M%S")
  ruta <- file.path(.neven_webview_dir(), paste0("plotly_", ts, ".html"))
  saveWidget(p, ruta, selfcontained=TRUE)
  return(ruta)
}

attr(GR_PlotlyView, "description") = list(
  "Genera graficos Plotly interactivos para WebView2",
  SetDatosX="Rango con encabezados",
  SetDatosY="No utilizado",
  TipoGrafico="No utilizado",
  Titulo="Titulo del grafico",
  TipoOutput="0:Procedimientos, 1:Lineas, 2:Barras, 3:Scatter, 4:Area, 5:Combinado"
)
