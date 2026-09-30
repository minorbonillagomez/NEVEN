#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# DASHBOARD — Pivot + Explorador + D3 en tabs             +
# Todo-en-uno para analisis de datos en WebView2          +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

# .neven_webview_dir() is defined in R4XCL-0-Shared-WebView.R

Dashboard <- function(SetDatosX, TipoOutput=0)
{
  if (TipoOutput <= 0){
    return(c(
      "[00] Lista de procedimientos",
      "[01] Dashboard completo (Pivot + Explorador + Treemap + Sankey + Sunburst + Force)",
      "Uso: =NEVEN.v(R.Dashboard(A1:E20, 1))",
      "Datos: encabezados en fila 1, al menos 1 columna numerica"
    ))
  }

  library(jsonlite)
  library(rpivotTable)
  library(htmlwidgets)

  # Convertir rango Excel a dataframe
  nombres <- as.character(SetDatosX[1,])
  datos <- data.frame(SetDatosX[-1,, drop=FALSE], stringsAsFactors=FALSE)
  colnames(datos) <- nombres

  for (i in 1:ncol(datos)) {
    num_vals <- suppressWarnings(as.numeric(datos[,i]))
    if (sum(is.na(num_vals)) <= sum(is.na(datos[,i]))) datos[,i] <- num_vals
  }

  col_types <- sapply(datos, function(x) if(is.numeric(x)) "numeric" else "categorical")
  num_cols <- nombres[col_types == "numeric"]
  cat_cols <- nombres[col_types == "categorical"]
  val_col <- if(length(num_cols) > 0) num_cols[1] else NULL

  # --- Serialize data and column metadata to JSON ---
  datos_json <- toJSON(datos, dataframe="rows", auto_unbox=TRUE)
  cols_json <- toJSON(nombres, auto_unbox=TRUE)
  num_json <- toJSON(num_cols, auto_unbox=TRUE)

  # --- Generate rpivotTable widget and extract its HTML for embedding ---
  pivot_widget <- rpivotTable(datos)
  pivot_tmp <- tempfile(fileext=".html")
  saveWidget(pivot_widget, pivot_tmp, selfcontained=TRUE)
  pivot_html <- paste(readLines(pivot_tmp, warn=FALSE), collapse="\n")
  unlink(pivot_tmp)

  # --- Build D3 hierarchy JS code from categorical/numeric columns ---
  hier_code <- ''
  if (length(cat_cols) >= 1 && !is.null(val_col)) {
    hier_code <- paste0('
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
    hier_code <- 'var root = {name:"root", children: DATA.map(function(d){return {name:Object.values(d)[0], value: +Object.values(d)[1] || 1};})};'
  }

  # --- Generate multi-tab HTML dashboard ---
  # Tab 0: rpivotTable (iframe), Tab 1: Plotly explorer with axis/type selectors
  # Tabs 2-5: D3 visualizations (Treemap, Sankey, Sunburst, Force Graph)
  html <- paste0('<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NEVEN Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Segoe UI, sans-serif; background: #1e1e1e; color: #e0e0e0; }
  .header { background: #2d2d2d; padding: 8px 16px; display: flex; align-items: center; border-bottom: 1px solid #444; }
  .header .brand { font-weight: 700; font-size: 15px; margin-right: 16px; color: #fff; }
  .header .subtitle { font-size: 12px; color: #888; }
  .tabs { background: #2d2d2d; display: flex; border-bottom: 2px solid #444; }
  .tab { padding: 10px 20px; cursor: pointer; color: #aaa; font-size: 13px; border-bottom: 2px solid transparent; transition: all 0.2s; }
  .tab:hover { color: #e0e0e0; background: #353535; }
  .tab.active { color: #fff; border-bottom-color: #4fc3f7; background: #353535; }
  .panel { display: none; width: 100%; height: calc(100vh - 82px); overflow: auto; }
  .panel.active { display: block; }
  .panel iframe { width: 100%; height: 100%; border: none; }
  .toolbar { background: #333; padding: 8px 12px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .toolbar label { font-size: 11px; color: #888; }
  .toolbar select { background: #3a3a3a; color: #e0e0e0; border: 1px solid #555; padding: 3px 6px; border-radius: 3px; font-size: 12px; }
  #explorerChart { width: 100%; height: calc(100vh - 130px); }
  #treemapSvg, #sankeySvg, #sunburstSvg, #forceSvg { width: 100%; height: calc(100vh - 82px); }
</style>
</head>
<body>
<div class="header">
  <span class="brand">NEVEN</span>
  <span class="subtitle">Dashboard - ', ncol(datos), ' columnas, ', nrow(datos), ' registros</span>
</div>
<div class="tabs">
  <div class="tab active" onclick="showTab(0)">Pivot Table</div>
  <div class="tab" onclick="showTab(1)">Explorador</div>
  <div class="tab" onclick="showTab(2)">Treemap</div>
  <div class="tab" onclick="showTab(3)">Sankey</div>
  <div class="tab" onclick="showTab(4)">Sunburst</div>
  <div class="tab" onclick="showTab(5)">Force Graph</div>
</div>

<!-- Tab 0: Pivot -->
<div class="panel active" id="panel0">
  <iframe srcdoc="', gsub('"', '&quot;', pivot_html), '"></iframe>
</div>

<!-- Tab 1: Explorer (Plotly) -->
<div class="panel" id="panel1">
  <div class="toolbar">
    <label>X:</label><select id="selX"></select>
    <label>Y:</label><select id="selY"></select>
    <label>Color:</label><select id="selColor"><option value="">(ninguno)</option></select>
    <label>Tipo:</label>
    <select id="selType">
      <option value="scatter">Scatter</option>
      <option value="bar">Barras</option>
      <option value="line">Lineas</option>
      <option value="box">Box Plot</option>
      <option value="histogram">Histograma</option>
    </select>
  </div>
  <div id="explorerChart"></div>
</div>

<!-- Tab 2: Treemap -->
<div class="panel" id="panel2"><svg id="treemapSvg"></svg></div>

<!-- Tab 3: Sankey -->
<div class="panel" id="panel3"><svg id="sankeySvg"></svg></div>

<!-- Tab 4: Sunburst -->
<div class="panel" id="panel4"><svg id="sunburstSvg"></svg></div>

<!-- Tab 5: Force Graph -->
<div class="panel" id="panel5"><svg id="forceSvg"></svg></div>

<script>
var DATA = ', datos_json, ';
var COLS = ', cols_json, ';
var NUM_COLS = ', num_json, ';

function showTab(idx) {
  document.querySelectorAll(".tab").forEach(function(t,i){t.classList.toggle("active",i===idx);});
  document.querySelectorAll(".panel").forEach(function(p,i){p.classList.toggle("active",i===idx);});
  if (idx === 1 && !window._explorerInit) { initExplorer(); window._explorerInit = true; }
  if (idx === 2 && !window._treemapInit) { initTreemap(); window._treemapInit = true; }
  if (idx === 3 && !window._sankeyInit) { initSankey(); window._sankeyInit = true; }
  if (idx === 4 && !window._sunburstInit) { initSunburst(); window._sunburstInit = true; }
  if (idx === 5 && !window._forceInit) { initForce(); window._forceInit = true; }
}

// Explorer
function initExplorer() {
  var selX=document.getElementById("selX"), selY=document.getElementById("selY"), selC=document.getElementById("selColor");
  COLS.forEach(function(c){selX.add(new Option(c,c));selY.add(new Option(c,c));selC.add(new Option(c,c));});
  if(COLS.length>0)selX.value=COLS[0];
  if(NUM_COLS.length>0)selY.value=NUM_COLS[0]; else if(COLS.length>1)selY.value=COLS[1];
  updateExplorer();
  selX.onchange=selY.onchange=selC.onchange=document.getElementById("selType").onchange=updateExplorer;
}
function updateExplorer(){
  var xC=document.getElementById("selX").value,yC=document.getElementById("selY").value;
  var cC=document.getElementById("selColor").value,tp=document.getElementById("selType").value;
  var xV=DATA.map(function(r){return r[xC];}),yV=DATA.map(function(r){return r[yC];});
  var traces=[],layout={paper_bgcolor:"#1e1e1e",plot_bgcolor:"#2d2d2d",font:{color:"#e0e0e0"},
    xaxis:{title:xC,gridcolor:"#444"},yaxis:{title:yC,gridcolor:"#444"},margin:{t:30,b:50,l:50,r:20}};
  if(cC&&tp!=="histogram"){
    var g={};DATA.forEach(function(r){var k=r[cC]||"N/A";if(!g[k])g[k]={x:[],y:[]};g[k].x.push(r[xC]);g[k].y.push(r[yC]);});
    Object.keys(g).forEach(function(k){var t={x:g[k].x,y:g[k].y,name:k};
      if(tp==="scatter"){t.type="scatter";t.mode="markers";}else if(tp==="bar")t.type="bar";
      else if(tp==="line"){t.type="scatter";t.mode="lines+markers";}else if(tp==="box"){t.type="box";}
      traces.push(t);});
  }else if(tp==="histogram"){traces.push({x:xV,type:"histogram"});layout.yaxis.title="Frecuencia";}
  else{var t={x:xV,y:yV};if(tp==="scatter"){t.type="scatter";t.mode="markers";}else if(tp==="bar")t.type="bar";
    else if(tp==="line"){t.type="scatter";t.mode="lines+markers";}else if(tp==="box")t.type="box";traces.push(t);}
  Plotly.newPlot("explorerChart",traces,layout,{responsive:true});
}

// Treemap
function initTreemap(){
  ', hier_code, '
  var el=document.getElementById("panel2"),w=el.clientWidth,h=el.clientHeight;
  var color=d3.scaleOrdinal(d3.schemeTableau10);
  var treemap=d3.treemap().size([w,h]).padding(2).round(true);
  var hier=d3.hierarchy(root).sum(function(d){return d.value;}).sort(function(a,b){return b.value-a.value;});
  treemap(hier);
  var svg=d3.select("#treemapSvg").attr("width",w).attr("height",h);
  var cell=svg.selectAll("g").data(hier.leaves()).join("g").attr("transform",function(d){return "translate("+d.x0+","+d.y0+")";});
  cell.append("rect").attr("width",function(d){return d.x1-d.x0;}).attr("height",function(d){return d.y1-d.y0;})
    .attr("fill",function(d){return color(d.parent?d.parent.data.name:d.data.name);}).attr("stroke","#1e1e1e").attr("rx",3);
  cell.append("text").attr("x",4).attr("y",14).text(function(d){return d.data.name;}).attr("font-size","11px").attr("fill","#fff");
  cell.append("text").attr("x",4).attr("y",28).text(function(d){return d.value;}).attr("font-size","10px").attr("fill","#aaa");
  cell.append("title").text(function(d){return d.data.name+": "+d.value;});
}

// Sankey
function initSankey(){
  var el=document.getElementById("panel3"),w=el.clientWidth,h=el.clientHeight;
  var nodeSet=new Set(),links=[];
  DATA.forEach(function(d){var s=String(d[COLS[0]]),t=String(d[COLS[1]]);if(s===t)t+=" ";
    nodeSet.add(s);nodeSet.add(t);var v=1;for(var i=2;i<COLS.length;i++){if(!isNaN(+d[COLS[i]])){v=+d[COLS[i]];break;}}
    links.push({source:s,target:t,value:v});});
  var nodes=Array.from(nodeSet).map(function(n){return{name:n};});
  var nm={};nodes.forEach(function(n,i){nm[n.name]=i;});
  links.forEach(function(l){l.source=nm[l.source];l.target=nm[l.target];});
  var merged={};links.forEach(function(l){var k=l.source+"->"+l.target;if(merged[k])merged[k].value+=l.value;else merged[k]={source:l.source,target:l.target,value:l.value};});
  links=Object.values(merged);
  var sankey=d3.sankey().nodeWidth(20).nodePadding(10).extent([[1,1],[w-1,h-6]]);
  var graph=sankey({nodes:nodes.map(function(d){return Object.assign({},d);}),links:links.map(function(d){return Object.assign({},d);})});
  var color=d3.scaleOrdinal(d3.schemeTableau10);
  var svg=d3.select("#sankeySvg").attr("width",w).attr("height",h);
  svg.append("g").selectAll("rect").data(graph.nodes).join("rect")
    .attr("x",function(d){return d.x0;}).attr("y",function(d){return d.y0;})
    .attr("height",function(d){return d.y1-d.y0;}).attr("width",function(d){return d.x1-d.x0;})
    .attr("fill",function(d){return color(d.name);}).append("title").text(function(d){return d.name+": "+d.value;});
  svg.append("g").attr("fill","none").selectAll("path").data(graph.links).join("path")
    .attr("d",d3.sankeyLinkHorizontal()).attr("stroke",function(d){return color(d.source.name);})
    .attr("stroke-width",function(d){return Math.max(1,d.width);}).attr("stroke-opacity",0.4)
    .append("title").text(function(d){return d.source.name+" -> "+d.target.name+": "+d.value;});
  svg.append("g").selectAll("text").data(graph.nodes).join("text")
    .attr("x",function(d){return d.x0<w/2?d.x1+6:d.x0-6;}).attr("y",function(d){return(d.y1+d.y0)/2;})
    .attr("dy","0.35em").attr("text-anchor",function(d){return d.x0<w/2?"start":"end";})
    .text(function(d){return d.name;}).attr("font-size","12px").attr("fill","#e0e0e0");
}

// Sunburst
function initSunburst(){
  ', hier_code, '
  root.name = "NEVEN";
  var el=document.getElementById("panel4"),w=el.clientWidth,h=el.clientHeight;
  var radius=Math.min(w,h)/2;
  var color=d3.scaleOrdinal(d3.quantize(d3.interpolateRainbow,(root.children?root.children.length:1)+1));
  var hier2=d3.hierarchy(root).sum(function(d){return d.value;}).sort(function(a,b){return b.value-a.value;});
  var partition=d3.partition().size([2*Math.PI,radius]);
  partition(hier2);
  var arc=d3.arc().startAngle(function(d){return d.x0;}).endAngle(function(d){return d.x1;})
    .innerRadius(function(d){return d.y0;}).outerRadius(function(d){return d.y1-1;});
  var svg=d3.select("#sunburstSvg").attr("width",w).attr("height",h)
    .append("g").attr("transform","translate("+w/2+","+h/2+")");
  svg.selectAll("path").data(hier2.descendants().filter(function(d){return d.depth;})).join("path")
    .attr("d",arc).attr("fill",function(d){while(d.depth>1)d=d.parent;return color(d.data.name);})
    .attr("stroke","#1e1e1e").attr("stroke-width",1)
    .append("title").text(function(d){return d.data.name+": "+d.value;});
  svg.selectAll("text").data(hier2.descendants().filter(function(d){return d.depth&&(d.y1-d.y0)>20&&(d.x1-d.x0)>0.05;})).join("text")
    .attr("transform",function(d){var x=(d.x0+d.x1)/2*180/Math.PI;var y=(d.y0+d.y1)/2;return "rotate("+(x-90)+") translate("+y+",0) rotate("+(x<180?0:180)+")";})
    .attr("dy","0.35em").attr("text-anchor","middle").text(function(d){return d.data.name;}).attr("font-size","10px").attr("fill","#fff");
}

// Force Graph
function initForce(){
  var el=document.getElementById("panel5"),w=el.clientWidth,h=el.clientHeight;
  var nodeSet=new Set(),links=[];
  DATA.forEach(function(d){var s=String(d[COLS[0]]),t=String(d[COLS[1]]);
    nodeSet.add(s);nodeSet.add(t);var v=1;for(var i=2;i<COLS.length;i++){if(!isNaN(+d[COLS[i]])){v=+d[COLS[i]];break;}}
    links.push({source:s,target:t,value:v});});
  var nodes=Array.from(nodeSet).map(function(n){return{id:n};});
  var color=d3.scaleOrdinal(d3.schemeTableau10);
  var svg=d3.select("#forceSvg").attr("width",w).attr("height",h);
  var sim=d3.forceSimulation(nodes)
    .force("link",d3.forceLink(links).id(function(d){return d.id;}).distance(80))
    .force("charge",d3.forceManyBody().strength(-200))
    .force("center",d3.forceCenter(w/2,h/2));
  var link=svg.append("g").selectAll("line").data(links).join("line")
    .attr("stroke","#555").attr("stroke-opacity",0.6).attr("stroke-width",function(d){return Math.sqrt(d.value);});
  var node=svg.append("g").selectAll("g").data(nodes).join("g").call(d3.drag()
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
}
</script>
</body>
</html>')

  ts <- format(Sys.time(), "%Y%m%d_%H%M%S")
  ruta <- file.path(.neven_webview_dir(), paste0("dashboard_", ts, ".html"))
  writeLines(html, ruta, useBytes = TRUE)
  return(ruta)
}

attr(Dashboard, "description") = list(
  "Dashboard todo-en-uno: Pivot + Explorador + Treemap + Sankey + Sunburst + Force Graph",
  SetDatosX="Rango con encabezados en la primera fila",
  TipoOutput="0:Procedimientos, 1:Dashboard completo"
)
attr(Dashboard, "category") <- "Analisis de Datos"
