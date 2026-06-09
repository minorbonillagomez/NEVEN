#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# D3.js — Visualizaciones avanzadas en WebView2          +
# Treemap, Sankey, Sunburst, Force Graph                 +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

# .neven_webview_dir() is defined in R4XCL-0-Shared-WebView.R

D3 <- function(SetDatosX, TipoOutput=0)
{
  if (TipoOutput <= 0){
    return(c(
      "[00] Lista de procedimientos",
      "[01] Treemap (jerarquia por columnas categoricas)",
      "[02] Sankey (flujo entre primera y segunda columna)",
      "[03] Sunburst (jerarquia circular)",
      "[04] Force Graph (red de relaciones)",
      "Uso: =NEVEN.v(R.D3(A1:E20, 1))",
      "Datos: encabezados en fila 1, ultima columna numerica = valor"
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

  # Identificar columnas
  col_types <- sapply(datos, function(x) if(is.numeric(x)) "numeric" else "categorical")
  num_cols <- nombres[col_types == "numeric"]
  cat_cols <- nombres[col_types == "categorical"]
  val_col <- if(length(num_cols) > 0) num_cols[1] else NULL

  # --- Serialize data to JSON for embedding in HTML ---
  datos_json <- toJSON(datos, dataframe="rows", auto_unbox=TRUE)

  # --- Common dark-theme CSS shared by all D3 visualizations ---
  css_common <- '
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Segoe UI, sans-serif; background: #1e1e1e; color: #e0e0e0; overflow: hidden; }
    .header { background: #2d2d2d; padding: 8px 16px; border-bottom: 1px solid #444; display: flex; align-items: center; }
    .header .brand { font-weight: 700; font-size: 14px; margin-right: 12px; }
    .header .title { font-size: 13px; color: #aaa; }
    #chart { width: 100%; height: calc(100vh - 40px); }
    .node text { font-size: 11px; fill: #e0e0e0; }
    .link { fill: none; stroke-opacity: 0.4; }
    .tooltip { position: absolute; background: #333; color: #fff; padding: 6px 10px; border-radius: 4px; font-size: 12px; pointer-events: none; }
  '

  if (TipoOutput == 1) {
    # --- TREEMAP: builds a nested hierarchy from categorical columns ---
    # JavaScript uses d3.treemap() to render area-proportional rectangles
    hierarchy_code <- ''
    if (length(cat_cols) >= 1 && !is.null(val_col)) {
      hierarchy_code <- paste0('
        var root = {name: "root", children: []};
        var map = {};
        DATA.forEach(function(d) {
          var path = [', paste0('d["', cat_cols, '"]', collapse=', '), '];
          var val = +d["', val_col, '"] || 1;
          var current = root;
          path.forEach(function(p, i) {
            var key = path.slice(0, i+1).join("/");
            if (!map[key]) {
              var node = {name: String(p), children: []};
              map[key] = node;
              current.children.push(node);
            }
            current = map[key];
          });
          current.value = (current.value || 0) + val;
          delete current.children;
        });
      ')
    } else {
      hierarchy_code <- 'var root = {name:"root", children: DATA.map(function(d,i){return {name:Object.values(d)[0], value: +Object.values(d)[1] || 1};})};'
    }

    html <- paste0('<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>', css_common, '</style></head><body>
<div class="header"><span class="brand">NEVEN</span><span class="title">Treemap</span></div>
<div id="chart"></div>
<script>
var DATA = ', datos_json, ';
', hierarchy_code, '
var width = window.innerWidth, height = window.innerHeight - 40;
var color = d3.scaleOrdinal(d3.schemeTableau10);
var treemap = d3.treemap().size([width, height]).padding(2).round(true);
var hier = d3.hierarchy(root).sum(function(d){return d.value;}).sort(function(a,b){return b.value - a.value;});
treemap(hier);
var svg = d3.select("#chart").append("svg").attr("width", width).attr("height", height);
var cell = svg.selectAll("g").data(hier.leaves()).join("g").attr("transform", function(d){return "translate("+d.x0+","+d.y0+")";});
cell.append("rect").attr("width", function(d){return d.x1-d.x0;}).attr("height", function(d){return d.y1-d.y0;})
  .attr("fill", function(d){return color(d.parent ? d.parent.data.name : d.data.name);}).attr("stroke","#1e1e1e").attr("rx",3);
cell.append("text").attr("x",4).attr("y",14).text(function(d){return d.data.name;}).attr("font-size","11px").attr("fill","#fff");
cell.append("text").attr("x",4).attr("y",28).text(function(d){return d.value;}).attr("font-size","10px").attr("fill","#aaa");
cell.append("title").text(function(d){return d.data.name + ": " + d.value;});
</script></body></html>')

  } else if (TipoOutput == 2) {
    # --- SANKEY: flow diagram between source (col1) and target (col2) ---
    # JavaScript uses d3-sankey plugin to compute node/link positions
    html <- paste0('<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12"></script>
<style>', css_common, '</style></head><body>
<div class="header"><span class="brand">NEVEN</span><span class="title">Sankey</span></div>
<div id="chart"></div>
<script>
var DATA = ', datos_json, ';
var COLS = ', toJSON(nombres, auto_unbox=TRUE), ';
var width = window.innerWidth, height = window.innerHeight - 40;
var nodeSet = new Set();
var links = [];
DATA.forEach(function(d) {
  var src = String(d[COLS[0]]);
  var tgt = String(d[COLS[1]]);
  if (src === tgt) tgt = tgt + " ";
  nodeSet.add(src); nodeSet.add(tgt);
  var val = 1;
  for (var i = 2; i < COLS.length; i++) { if (!isNaN(+d[COLS[i]])) { val = +d[COLS[i]]; break; } }
  links.push({source: src, target: tgt, value: val});
});
var nodes = Array.from(nodeSet).map(function(n){return {name: n};});
var nodeMap = {}; nodes.forEach(function(n,i){nodeMap[n.name]=i;});
links.forEach(function(l){l.source=nodeMap[l.source]; l.target=nodeMap[l.target];});
// Merge duplicate links
var merged = {};
links.forEach(function(l) {
  var key = l.source + "->" + l.target;
  if (merged[key]) merged[key].value += l.value;
  else merged[key] = {source: l.source, target: l.target, value: l.value};
});
links = Object.values(merged);
var sankey = d3.sankey().nodeWidth(20).nodePadding(10).extent([[1,1],[width-1,height-6]]);
var graph = sankey({nodes: nodes.map(function(d){return Object.assign({},d);}), links: links.map(function(d){return Object.assign({},d);})});
var color = d3.scaleOrdinal(d3.schemeTableau10);
var svg = d3.select("#chart").append("svg").attr("width",width).attr("height",height);
svg.append("g").selectAll("rect").data(graph.nodes).join("rect")
  .attr("x",function(d){return d.x0;}).attr("y",function(d){return d.y0;})
  .attr("height",function(d){return d.y1-d.y0;}).attr("width",function(d){return d.x1-d.x0;})
  .attr("fill",function(d){return color(d.name);}).append("title").text(function(d){return d.name+": "+d.value;});
svg.append("g").attr("fill","none").selectAll("path").data(graph.links).join("path")
  .attr("d",d3.sankeyLinkHorizontal()).attr("stroke",function(d){return color(d.source.name);})
  .attr("stroke-width",function(d){return Math.max(1,d.width);}).attr("stroke-opacity",0.4)
  .append("title").text(function(d){return d.source.name+" -> "+d.target.name+": "+d.value;});
svg.append("g").selectAll("text").data(graph.nodes).join("text")
  .attr("x",function(d){return d.x0<width/2?d.x1+6:d.x0-6;})
  .attr("y",function(d){return (d.y1+d.y0)/2;}).attr("dy","0.35em")
  .attr("text-anchor",function(d){return d.x0<width/2?"start":"end";})
  .text(function(d){return d.name;}).attr("font-size","12px").attr("fill","#e0e0e0");
</script></body></html>')

  } else if (TipoOutput == 3) {
    # --- SUNBURST: circular partition layout from hierarchical data ---
    # JavaScript uses d3.partition() and d3.arc() for radial segments
    hierarchy_code <- ''
    if (length(cat_cols) >= 1 && !is.null(val_col)) {
      hierarchy_code <- paste0('
        var root = {name: "NEVEN", children: []};
        var map = {"": root};
        DATA.forEach(function(d) {
          var path = [', paste0('d["', cat_cols, '"]', collapse=', '), '];
          var val = +d["', val_col, '"] || 1;
          var parentKey = "";
          path.forEach(function(p, i) {
            var key = path.slice(0, i+1).join("/");
            if (!map[key]) {
              var node = {name: String(p), children: []};
              map[key] = node;
              map[parentKey].children.push(node);
            }
            parentKey = key;
          });
          map[parentKey].value = (map[parentKey].value || 0) + val;
          if (map[parentKey].children && map[parentKey].children.length === 0) delete map[parentKey].children;
        });
      ')
    } else {
      hierarchy_code <- 'var root = {name:"NEVEN", children: DATA.map(function(d){return {name:Object.values(d)[0], value: +Object.values(d)[1] || 1};})};'
    }

    html <- paste0('<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>', css_common, '</style></head><body>
<div class="header"><span class="brand">NEVEN</span><span class="title">Sunburst</span></div>
<div id="chart"></div>
<script>
var DATA = ', datos_json, ';
', hierarchy_code, '
var width = window.innerWidth, height = window.innerHeight - 40;
var radius = Math.min(width, height) / 2;
var color = d3.scaleOrdinal(d3.quantize(d3.interpolateRainbow, (root.children ? root.children.length : 1) + 1));
var hier = d3.hierarchy(root).sum(function(d){return d.value;}).sort(function(a,b){return b.value-a.value;});
var partition = d3.partition().size([2*Math.PI, radius]);
partition(hier);
var arc = d3.arc().startAngle(function(d){return d.x0;}).endAngle(function(d){return d.x1;})
  .innerRadius(function(d){return d.y0;}).outerRadius(function(d){return d.y1-1;});
var svg = d3.select("#chart").append("svg").attr("width",width).attr("height",height)
  .append("g").attr("transform","translate("+width/2+","+height/2+")");
svg.selectAll("path").data(hier.descendants().filter(function(d){return d.depth;})).join("path")
  .attr("d",arc).attr("fill",function(d){while(d.depth>1)d=d.parent;return color(d.data.name);})
  .attr("stroke","#1e1e1e").attr("stroke-width",1)
  .append("title").text(function(d){return d.data.name+": "+d.value;});
svg.selectAll("text").data(hier.descendants().filter(function(d){return d.depth && (d.y1-d.y0)>20 && (d.x1-d.x0)>0.05;})).join("text")
  .attr("transform",function(d){var x=(d.x0+d.x1)/2*180/Math.PI;var y=(d.y0+d.y1)/2;return "rotate("+(x-90)+") translate("+y+",0) rotate("+(x<180?0:180)+")";})
  .attr("dy","0.35em").attr("text-anchor","middle").text(function(d){return d.data.name;}).attr("font-size","10px").attr("fill","#fff");
</script></body></html>')

  } else if (TipoOutput == 4) {
    # --- FORCE GRAPH: interactive network with draggable nodes ---
    # JavaScript uses d3.forceSimulation() with link/charge/center forces
    html <- paste0('<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>', css_common, '
.node circle { stroke: #1e1e1e; stroke-width: 2px; }
.link line { stroke: #555; stroke-opacity: 0.6; }
</style></head><body>
<div class="header"><span class="brand">NEVEN</span><span class="title">Force Graph</span></div>
<div id="chart"></div>
<script>
var DATA = ', datos_json, ';
var COLS = ', toJSON(nombres, auto_unbox=TRUE), ';
var width = window.innerWidth, height = window.innerHeight - 40;
var nodeSet = new Set();
var links = [];
DATA.forEach(function(d) {
  var src = String(d[COLS[0]]);
  var tgt = String(d[COLS[1]]);
  nodeSet.add(src); nodeSet.add(tgt);
  var val = 1;
  for (var i = 2; i < COLS.length; i++) { if (!isNaN(+d[COLS[i]])) { val = +d[COLS[i]]; break; } }
  links.push({source: src, target: tgt, value: val});
});
var nodes = Array.from(nodeSet).map(function(n){return {id: n};});
var color = d3.scaleOrdinal(d3.schemeTableau10);
var svg = d3.select("#chart").append("svg").attr("width",width).attr("height",height);
var sim = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(function(d){return d.id;}).distance(80))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(width/2, height/2));
var link = svg.append("g").selectAll("line").data(links).join("line")
  .attr("stroke","#555").attr("stroke-opacity",0.6).attr("stroke-width",function(d){return Math.sqrt(d.value);});
var node = svg.append("g").selectAll("g").data(nodes).join("g").call(d3.drag()
  .on("start",function(e,d){if(!e.active)sim.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y;})
  .on("drag",function(e,d){d.fx=e.x;d.fy=e.y;})
  .on("end",function(e,d){if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}));
node.append("circle").attr("r",12).attr("fill",function(d){return color(d.id);});
node.append("text").attr("dx",16).attr("dy","0.35em").text(function(d){return d.id;}).attr("font-size","12px").attr("fill","#e0e0e0");
node.append("title").text(function(d){return d.id;});
sim.on("tick",function(){
  link.attr("x1",function(d){return d.source.x;}).attr("y1",function(d){return d.source.y;})
    .attr("x2",function(d){return d.target.x;}).attr("y2",function(d){return d.target.y;});
  node.attr("transform",function(d){return "translate("+d.x+","+d.y+")";});
});
</script></body></html>')

  } else {
    return("TipoOutput debe ser 1-4")
  }

  ts <- format(Sys.time(), "%Y%m%d_%H%M%S")
  ruta <- file.path(.neven_webview_dir(), paste0("d3_", ts, ".html"))
  writeLines(html, ruta, useBytes = TRUE)
  return(ruta)
}

attr(D3, "description") = list(
  "Visualizaciones D3.js avanzadas: Treemap, Sankey, Sunburst, Force Graph",
  SetDatosX="Rango con encabezados. Columnas categoricas = jerarquia, numerica = valor",
  TipoOutput="0:Procedimientos, 1:Treemap, 2:Sankey, 3:Sunburst, 4:Force Graph"
)
attr(D3, "category") <- "Analisis de Datos"
