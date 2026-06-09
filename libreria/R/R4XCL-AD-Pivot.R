#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# PIVOT TABLE INTERACTIVA (rpivotTable + WebView2)      +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

# .neven_webview_dir() is defined in R4XCL-0-Shared-WebView.R

Pivot <- function(SetDatosX, TipoOutput=0)
{
  if (TipoOutput <= 0){
    return(c(
      "[00] Lista de procedimientos",
      "[01] Pivot interactivo (drag-and-drop libre)",
      "[02] Pivot con Heatmap",
      "[03] Pivot con barras horizontales",
      "Uso: =NEVEN.v(R.Pivot(A1:E20, 1))"
    ))
  }

  # Cargar rpivotTable
  if (!requireNamespace("rpivotTable", quietly = TRUE)) {
    install.packages("rpivotTable", repos = "https://cran.r-project.org", quiet = TRUE)
  }
  library(rpivotTable)
  library(htmlwidgets)

  # Convertir rango Excel a dataframe con encabezados
  nombres <- as.character(SetDatosX[1,])
  datos <- data.frame(SetDatosX[-1,, drop=FALSE], stringsAsFactors=FALSE)
  colnames(datos) <- nombres

  # Convertir columnas numericas
  for (i in 1:ncol(datos)) {
    num_vals <- suppressWarnings(as.numeric(datos[,i]))
    if (sum(is.na(num_vals)) <= sum(is.na(datos[,i]))) {
      datos[,i] <- num_vals
    }
  }

  # Generar pivot segun TipoOutput
  if (TipoOutput == 1) {
    p <- rpivotTable(datos)
  } else if (TipoOutput == 2) {
    p <- rpivotTable(datos, rendererName = "Heatmap")
  } else if (TipoOutput == 3) {
    p <- rpivotTable(datos, rendererName = "Table Barchart")
  } else {
    p <- rpivotTable(datos)
  }

  # Guardar como HTML
  ts <- format(Sys.time(), "%Y%m%d_%H%M%S")
  ruta <- file.path(.neven_webview_dir(), paste0("pivot_", ts, ".html"))
  saveWidget(p, ruta, selfcontained = TRUE)
  return(ruta)
}

attr(Pivot, "description") = list(
  "Tabla pivote interactiva con drag-and-drop en WebView2",
  SetDatosX="Rango con encabezados en la primera fila",
  TipoOutput="0:Procedimientos, 1:Libre, 2:Heatmap, 3:Barras"
)
attr(Pivot, "category") <- "Analisis de Datos"
