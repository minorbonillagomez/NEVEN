# ===============================================================================
# NEVEN Data Lab — GR_Mapa: Mapa Interactivo (Leaflet.js)
# ===============================================================================
# Familia:  GR (Gráficos)
# Función:  GR_Mapa.Studio
# Sidecar:  GR_Mapa.json
# Motor:    Leaflet.js (no Plotly) — HTML puro, sin codificación base64
# Nota:     Adaptado de R4XCL-AD-Map.R. Retorna HTML como string (slot "mapa")
#           en lugar de escribir a disco.
# ===============================================================================

GR_Mapa.Studio <- function(data_Lat,
                            data_Lon,
                            data_Etiqueta = NULL,
                            data_Valor    = NULL,
                            TipoMapa      = 1L) {

  # ── Helper interno: rechazar columnas todo-NA ────────────────────────────────
  .check_col_not_all_na <- function(vec, nombre) {
    if (all(is.na(vec)))
      stop(sprintf("La columna '%s' no contiene valores válidos (solo NA).", nombre))
  }

  # ── Validación de data_Lat ───────────────────────────────────────────────────
  if (!is.data.frame(data_Lat))
    stop("'data_Lat' debe ser un data.frame.")
  if (nrow(data_Lat) == 0)
    stop("El filtro aplicado no retorna filas. Verifique la cláusula WHERE.")

  lat_cols <- names(data_Lat)[sapply(data_Lat, is.numeric)]
  if (length(lat_cols) == 0)
    stop("'data_Lat' debe contener al menos una columna numérica con valores de latitud.")

  # ── Validación de data_Lon ───────────────────────────────────────────────────
  if (!is.data.frame(data_Lon))
    stop("'data_Lon' debe ser un data.frame.")
  if (nrow(data_Lon) == 0)
    stop("El filtro aplicado no retorna filas. Verifique la cláusula WHERE.")

  lon_cols <- names(data_Lon)[sapply(data_Lon, is.numeric)]
  if (length(lon_cols) == 0)
    stop("'data_Lon' debe contener al menos una columna numérica con valores de longitud.")

  # ── Validación de dimensiones ────────────────────────────────────────────────
  if (nrow(data_Lat) != nrow(data_Lon))
    stop("'data_Lat' y 'data_Lon' deben tener el mismo número de filas.")

  # ── Extraer vectores lat / lon ───────────────────────────────────────────────
  lat_col <- lat_cols[1]
  lon_col <- lon_cols[1]
  lat_vec <- as.numeric(data_Lat[[lat_col]])
  lon_vec <- as.numeric(data_Lon[[lon_col]])

  .check_col_not_all_na(lat_vec, lat_col)
  .check_col_not_all_na(lon_vec, lon_col)

  # ── TipoMapa: normalizar y validar ───────────────────────────────────────────
  TipoMapa <- as.integer(TipoMapa)
  if (is.na(TipoMapa) || TipoMapa < 1L || TipoMapa > 3L) TipoMapa <- 1L

  # ── Construir data.frame combinado ───────────────────────────────────────────
  datos <- data.frame(lat = lat_vec, lon = lon_vec, stringsAsFactors = FALSE)

  if (!is.null(data_Etiqueta) && is.data.frame(data_Etiqueta) && ncol(data_Etiqueta) > 0) {
    datos$etiqueta <- as.character(data_Etiqueta[[names(data_Etiqueta)[1]]])
  }

  if (!is.null(data_Valor) && is.data.frame(data_Valor) && ncol(data_Valor) > 0) {
    val_cols <- names(data_Valor)[sapply(data_Valor, is.numeric)]
    if (length(val_cols) > 0)
      datos$valor <- as.numeric(data_Valor[[val_cols[1]]])
  }

  # ── Centrar el mapa ──────────────────────────────────────────────────────────
  center_lat <- mean(lat_vec, na.rm = TRUE)
  center_lon <- mean(lon_vec, na.rm = TRUE)

  # ── Serializar datos a JSON para embeber en HTML ─────────────────────────────
  datos_json <- jsonlite::toJSON(datos, dataframe = "rows", auto_unbox = TRUE)

  # ── CDN resources ────────────────────────────────────────────────────────────
  leaflet_css <- "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.css"
  leaflet_js  <- "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.js"
  heat_js     <- "https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js"

  # ── Código JavaScript según TipoMapa ─────────────────────────────────────────
  has_etiqueta <- "etiqueta" %in% names(datos)
  has_valor    <- "valor"    %in% names(datos)

  if (TipoMapa == 1L) {
    # Marcadores: L.marker con popup y tooltip por fila
    label_expr <- if (has_etiqueta) 'd["etiqueta"] != null ? String(d["etiqueta"]) : "Punto"' else '"Punto"'
    marker_code <- paste0('
      DATA.forEach(function(d) {
        var lat = +d["lat"], lon = +d["lon"];
        if (isNaN(lat) || isNaN(lon)) return;
        var label = ', label_expr, ';
        L.marker([lat, lon]).addTo(map).bindPopup(label).bindTooltip(label);
      });
    ')

  } else if (TipoMapa == 2L) {
    # Mapa de calor: L.heatLayer usando "valor" como intensidad
    valor_expr <- if (has_valor) '+d["valor"] || 1' else '1'
    marker_code <- paste0('
      var heat = [];
      DATA.forEach(function(d) {
        var lat = +d["lat"], lon = +d["lon"];
        if (isNaN(lat) || isNaN(lon)) return;
        var val = ', valor_expr, ';
        heat.push([lat, lon, val]);
      });
      L.heatLayer(heat, {radius: 25, blur: 15, maxZoom: 17}).addTo(map);
    ')

  } else {
    # TipoMapa == 3L: Círculos proporcionales a "valor", radio normalizado 5-40
    valor_expr  <- if (has_valor) '+d["valor"]' else '1'
    label_expr  <- if (has_etiqueta) 'd["etiqueta"] != null ? String(d["etiqueta"]) : "Punto"' else '"Punto"'
    marker_code <- paste0('
      var vals = DATA.map(function(d) { return ', valor_expr, '; });
      var minVal = Math.min.apply(null, vals.filter(function(v){ return !isNaN(v); }));
      var maxVal = Math.max.apply(null, vals.filter(function(v){ return !isNaN(v); }));
      var rangeVal = maxVal - minVal;
      DATA.forEach(function(d) {
        var lat = +d["lat"], lon = +d["lon"];
        if (isNaN(lat) || isNaN(lon)) return;
        var val = ', valor_expr, ';
        var radius = (rangeVal > 0) ? 5 + ((val - minVal) / rangeVal) * 35 : 12;
        var label = ', label_expr, ';
        L.circleMarker([lat, lon], {
          radius: radius,
          fillColor: "#d7a538",
          color: "#1e88e5",
          weight: 1,
          opacity: 1,
          fillOpacity: 0.7
        }).addTo(map).bindPopup(label + (', if (has_valor) '"<br><b>" + val + "</b>"' else '""', ')).bindTooltip(label);
      });
    ')
  }

  # ── Construcción del HTML completo ───────────────────────────────────────────
  html_leaflet <- tryCatch({
    paste0('<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NEVEN - Mapa</title>
<link rel="stylesheet" href="', leaflet_css, '"/>
<script src="', leaflet_js, '"></script>
<script src="', heat_js, '"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #1e1e1e; }
  .header {
    background: #2d2d2d;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid #444;
    height: 40px;
  }
  .header .brand {
    font-family: Segoe UI, sans-serif;
    font-weight: 700;
    font-size: 14px;
    color: #fff;
    margin-right: 12px;
  }
  .header .info {
    font-family: Segoe UI, sans-serif;
    font-size: 12px;
    color: #888;
  }
  #map { width: 100%; height: calc(100vh - 40px); }
</style>
</head>
<body>
<div class="header">
  <span class="brand">NEVEN</span>
  <span class="info">Mapa \u2014 ', nrow(datos), ' punto', if (nrow(datos) != 1) 's' else '', '</span>
</div>
<div id="map"></div>
<script>
var DATA = ', datos_json, ';
var map = L.map("map").setView([', center_lat, ', ', center_lon, '], 6);
L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
  attribution: "NEVEN | \u00a9 CartoDB",
  maxZoom: 19
}).addTo(map);
', marker_code, '
</script>
</body>
</html>')
  }, error = function(e) {
    paste0('<html><body><p style="color:#888;font-family:Segoe UI,sans-serif;padding:16px">',
           'Mapa no disponible: ', conditionMessage(e),
           '</p></body></html>')
  })

  # ── Retorno estándar (slot "mapa", no "grafico") ──────────────────────────────
  return(r_object_to_slots(
    list(mapa = html_leaflet),
    tier_map = c(mapa = 1L)
  ))
}
