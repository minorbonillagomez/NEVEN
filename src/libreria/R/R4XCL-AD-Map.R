#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# MAP — Mapas interactivos con Leaflet.js en WebView2    +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

# .neven_webview_dir() is defined in R4XCL-0-Shared-WebView.R

Map <- function(SetDatosX, TipoOutput=0)
{
  if (TipoOutput <= 0){
    return(c(
      "[00] Lista de procedimientos",
      "[01] Mapa de marcadores (lat, lon, etiqueta)",
      "[02] Mapa de calor (lat, lon, valor)",
      "[03] Mapa de circulos proporcionales (lat, lon, valor)",
      "Uso: =NEVEN.v(R.Map(A1:D20, 1))",
      "Datos: Col1=Latitud, Col2=Longitud, Col3=Etiqueta/Valor, Col4=Popup(opcional)"
    ))
  }

  library(jsonlite)

  # Convertir rango Excel a dataframe
  nombres <- as.character(SetDatosX[1,])
  datos <- data.frame(SetDatosX[-1,, drop=FALSE], stringsAsFactors=FALSE)
  colnames(datos) <- nombres

  for (i in 1:ncol(datos)) {
    num_vals <- suppressWarnings(as.numeric(datos[,i]))
    if (sum(is.na(num_vals)) <= sum(is.na(datos[,i]))) datos[,i] <- num_vals
  }

  # Detectar columnas de lat/lon
  lat_col <- NULL; lon_col <- NULL; label_col <- NULL; value_col <- NULL
  for (n in nombres) {
    nl <- tolower(n)
    if (is.null(lat_col) && (nl %in% c("lat","latitud","latitude","y"))) lat_col <- n
    if (is.null(lon_col) && (nl %in% c("lon","lng","longitud","longitude","x"))) lon_col <- n
  }
  # Fallback: first two numeric columns = lat, lon
  if (is.null(lat_col) || is.null(lon_col)) {
    num_idx <- which(sapply(datos, is.numeric))
    if (length(num_idx) >= 2) {
      lat_col <- nombres[num_idx[1]]
      lon_col <- nombres[num_idx[2]]
    }
  }
  if (is.null(lat_col) || is.null(lon_col)) return("Error: no se encontraron columnas de latitud/longitud")

  # Label/value: first non-lat/lon column
  remaining <- setdiff(nombres, c(lat_col, lon_col))
  if (length(remaining) > 0) {
    label_col <- remaining[1]
    if (length(remaining) > 1) value_col <- remaining[2]
  }

  # Center map
  center_lat <- mean(datos[[lat_col]], na.rm=TRUE)
  center_lon <- mean(datos[[lon_col]], na.rm=TRUE)

  # --- Serialize point data to JSON for embedding in HTML ---
  datos_json <- toJSON(datos, dataframe="rows", auto_unbox=TRUE)

  # --- CDN resources: Leaflet.js for maps, leaflet-heat for heatmaps ---
  leaflet_css <- "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.css"
  leaflet_js <- "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.js"
  heat_js <- "https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js"

  # --- Generate JavaScript code for the selected map visualization ---
  marker_code <- ""
  if (TipoOutput == 1) {
    # Markers: L.marker() with popup and tooltip per data point
    marker_code <- paste0('
      DATA.forEach(function(d) {
        var lat = +d["', lat_col, '"], lon = +d["', lon_col, '"];
        if (isNaN(lat) || isNaN(lon)) return;
        var label = ', if(!is.null(label_col)) paste0('String(d["', label_col, '"])') else '"Punto"', ';
        var popup = label;
        ', if(!is.null(value_col)) paste0('popup += "<br><b>" + d["', value_col, '"] + "</b>";') else '', '
        L.marker([lat, lon]).addTo(map).bindPopup(popup).bindTooltip(label);
      });
    ')
  } else if (TipoOutput == 2) {
    # Heatmap: L.heatLayer() renders intensity from lat/lon/value triples
    marker_code <- paste0('
      var heat = [];
      DATA.forEach(function(d) {
        var lat = +d["', lat_col, '"], lon = +d["', lon_col, '"];
        if (isNaN(lat) || isNaN(lon)) return;
        var val = ', if(!is.null(label_col) && is.numeric(datos[[label_col]])) paste0('+d["', label_col, '"] || 1') else '1', ';
        heat.push([lat, lon, val]);
      });
      L.heatLayer(heat, {radius: 25, blur: 15, maxZoom: 17}).addTo(map);
    ')
  } else if (TipoOutput == 3) {
    # Proportional circles: L.circleMarker() with radius scaled to value
    marker_code <- paste0('
      var maxVal = 0;
      DATA.forEach(function(d) {
        var v = ', if(!is.null(label_col) && is.numeric(datos[[label_col]])) paste0('+d["', label_col, '"]') else '1', ';
        if (v > maxVal) maxVal = v;
      });
      DATA.forEach(function(d) {
        var lat = +d["', lat_col, '"], lon = +d["', lon_col, '"];
        if (isNaN(lat) || isNaN(lon)) return;
        var val = ', if(!is.null(label_col) && is.numeric(datos[[label_col]])) paste0('+d["', label_col, '"]') else '1', ';
        var radius = Math.max(5, (val / maxVal) * 40);
        var label = ', if(!is.null(label_col)) paste0('String(d["', label_col, '"])') else '"Punto"', ';
        L.circleMarker([lat, lon], {radius: radius, fillColor: "#4fc3f7", color: "#1e88e5", weight: 1, fillOpacity: 0.7})
          .addTo(map).bindPopup(label + ": " + val).bindTooltip(label);
      });
    ')
  }

  html <- paste0('<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NEVEN - Mapa</title>
<link rel="stylesheet" href="', leaflet_css, '"/>
<script src="', leaflet_js, '"></script>
<script src="', heat_js, '"></script>
<style>
  * { margin: 0; padding: 0; }
  body { background: #1e1e1e; }
  .header { background: #2d2d2d; padding: 8px 16px; display: flex; align-items: center; border-bottom: 1px solid #444; }
  .header .brand { font-family: Segoe UI, sans-serif; font-weight: 700; font-size: 14px; color: #fff; margin-right: 12px; }
  .header .info { font-family: Segoe UI, sans-serif; font-size: 12px; color: #888; }
  #map { width: 100%; height: calc(100vh - 40px); }
</style>
</head>
<body>
<div class="header">
  <span class="brand">NEVEN</span>
  <span class="info">Mapa - ', nrow(datos), ' puntos</span>
</div>
<div id="map"></div>
<script>
var DATA = ', datos_json, ';
var map = L.map("map").setView([', center_lat, ', ', center_lon, '], 6);
L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
  attribution: "NEVEN | CartoDB",
  maxZoom: 19
}).addTo(map);
', marker_code, '
</script>
</body>
</html>')

  ts <- format(Sys.time(), "%Y%m%d_%H%M%S")
  ruta <- file.path(.neven_webview_dir(), paste0("map_", ts, ".html"))
  writeLines(html, ruta, useBytes = TRUE)
  return(ruta)
}

attr(Map, "description") = list(
  "Mapas interactivos con Leaflet.js en WebView2",
  SetDatosX="Rango: Col1=Lat, Col2=Lon, Col3=Etiqueta/Valor, Col4=Popup(opcional)",
  TipoOutput="0:Procedimientos, 1:Marcadores, 2:Mapa de calor, 3:Circulos proporcionales"
)
attr(Map, "category") <- "Analisis de Datos"
