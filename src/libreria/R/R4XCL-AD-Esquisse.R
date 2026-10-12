#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ESQUISSE — Constructor interactivo de graficos         +
# Genera HTML con controles para explorar datos          +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

# .neven_webview_dir() is defined in R4XCL-0-Shared-WebView.R

Esquisse <- function(SetDatosX, TipoOutput=0)
{
  if (TipoOutput <= 0){
    return(c(
      "[00] Lista de procedimientos",
      "[01] Explorador interactivo de datos (seleccionar ejes, tipo, color)",
      "Uso: =NEVEN.v(R.Esquisse(A1:E20, 1))"
    ))
  }

  library(plotly)
  library(htmlwidgets)
  library(jsonlite)

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

  # Clasificar columnas
  col_types <- sapply(datos, function(x) if(is.numeric(x)) "numeric" else "categorical")
  num_cols <- nombres[col_types == "numeric"]
  cat_cols <- nombres[col_types == "categorical"]

  # --- Serialize data to JSON for embedding in HTML ---
  datos_json <- toJSON(datos, dataframe="rows", auto_unbox=TRUE)

  # --- Generate HTML with embedded data and interactive Plotly controls ---
  # User can select X/Y axes, color grouping, and chart type from dropdowns
  html <- paste0('<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NEVEN - Explorador de Datos</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Segoe UI, sans-serif; background: #1e1e1e; color: #e0e0e0; }
  .toolbar { background: #2d2d2d; padding: 10px 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; border-bottom: 1px solid #444; }
  .toolbar label { font-size: 12px; color: #aaa; margin-right: 4px; }
  .toolbar select { background: #3a3a3a; color: #e0e0e0; border: 1px solid #555; padding: 4px 8px; border-radius: 4px; font-size: 13px; }
  .toolbar .brand { color: #e0e0e0; font-weight: 700; font-size: 14px; margin-right: 16px; }
  #chart { width: 100%; height: calc(100vh - 52px); }
</style>
</head>
<body>
<div class="toolbar">
  <span class="brand">NEVEN</span>
  <label>Eje X:</label><select id="selX"></select>
  <label>Eje Y:</label><select id="selY"></select>
  <label>Color:</label><select id="selColor"><option value="">(ninguno)</option></select>
  <label>Tipo:</label>
  <select id="selType">
    <option value="scatter">Scatter</option>
    <option value="bar">Barras</option>
    <option value="line">Lineas</option>
    <option value="box">Box Plot</option>
    <option value="histogram">Histograma</option>
    <option value="heatmap">Heatmap</option>
  </select>
</div>
<div id="chart"></div>
<script>
var DATA = ', datos_json, ';
var COLS = ', toJSON(nombres, auto_unbox=TRUE), ';
var NUM_COLS = ', toJSON(num_cols, auto_unbox=TRUE), ';
var CAT_COLS = ', toJSON(cat_cols, auto_unbox=TRUE), ';

function populateSelects() {
  var selX = document.getElementById("selX");
  var selY = document.getElementById("selY");
  var selColor = document.getElementById("selColor");
  COLS.forEach(function(c) {
    selX.add(new Option(c, c));
    selY.add(new Option(c, c));
    selColor.add(new Option(c, c));
  });
  if (COLS.length > 0) selX.value = COLS[0];
  if (NUM_COLS.length > 0) selY.value = NUM_COLS[0];
  else if (COLS.length > 1) selY.value = COLS[1];
}

function updateChart() {
  var xCol = document.getElementById("selX").value;
  var yCol = document.getElementById("selY").value;
  var colorCol = document.getElementById("selColor").value;
  var chartType = document.getElementById("selType").value;

  var xVals = DATA.map(function(r) { return r[xCol]; });
  var yVals = DATA.map(function(r) { return r[yCol]; });

  var traces = [];
  var layout = {
    paper_bgcolor: "#1e1e1e", plot_bgcolor: "#2d2d2d",
    font: { color: "#e0e0e0" },
    xaxis: { title: xCol, gridcolor: "#444" },
    yaxis: { title: yCol, gridcolor: "#444" },
    margin: { t: 40, b: 60, l: 60, r: 20 }
  };

  if (colorCol && chartType !== "histogram" && chartType !== "heatmap") {
    var groups = {};
    DATA.forEach(function(r) {
      var g = r[colorCol] || "N/A";
      if (!groups[g]) groups[g] = { x: [], y: [] };
      groups[g].x.push(r[xCol]);
      groups[g].y.push(r[yCol]);
    });
    Object.keys(groups).forEach(function(g) {
      var trace = { x: groups[g].x, y: groups[g].y, name: g };
      if (chartType === "scatter") { trace.type = "scatter"; trace.mode = "markers"; }
      else if (chartType === "bar") { trace.type = "bar"; }
      else if (chartType === "line") { trace.type = "scatter"; trace.mode = "lines+markers"; }
      else if (chartType === "box") { trace.type = "box"; trace.x = groups[g].x; trace.y = groups[g].y; }
      traces.push(trace);
    });
  } else if (chartType === "histogram") {
    traces.push({ x: xVals, type: "histogram", marker: { color: "#636EFA" } });
    layout.yaxis.title = "Frecuencia";
  } else if (chartType === "heatmap") {
    traces.push({ z: [yVals], x: xVals, type: "heatmap", colorscale: "Viridis" });
  } else {
    var trace = { x: xVals, y: yVals };
    if (chartType === "scatter") { trace.type = "scatter"; trace.mode = "markers"; }
    else if (chartType === "bar") { trace.type = "bar"; }
    else if (chartType === "line") { trace.type = "scatter"; trace.mode = "lines+markers"; }
    else if (chartType === "box") { trace.type = "box"; }
    traces.push(trace);
  }

  Plotly.newPlot("chart", traces, layout, { responsive: true });
}

populateSelects();
updateChart();
document.getElementById("selX").onchange = updateChart;
document.getElementById("selY").onchange = updateChart;
document.getElementById("selColor").onchange = updateChart;
document.getElementById("selType").onchange = updateChart;
</script>
</body>
</html>')

  # Guardar HTML
  ts <- format(Sys.time(), "%Y%m%d_%H%M%S")
  ruta <- file.path(.neven_webview_dir(), paste0("esquisse_", ts, ".html"))
  writeLines(html, ruta, useBytes = TRUE)
  return(ruta)
}

attr(Esquisse, "description") = list(
  "Explorador interactivo de datos con seleccion de ejes y tipo de grafico",
  SetDatosX="Rango con encabezados en la primera fila",
  TipoOutput="0:Procedimientos, 1:Explorador interactivo"
)
attr(Esquisse, "category") <- "Analisis de Datos"
