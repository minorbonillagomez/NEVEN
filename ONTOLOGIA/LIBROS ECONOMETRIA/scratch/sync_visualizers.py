import json
import re

# 1. Load full graph
graph_items = []
node_counts = {}
edge_count = 0

with open('memory/ontology/graph.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        graph_items.append(item)
        if item.get('op') == 'create':
            t = item['entity']['type']
            node_counts[t] = node_counts.get(t, 0) + 1
        elif item.get('op') == 'relate':
            edge_count += 1

total_nodes = sum(node_counts.values())
total_edges = edge_count

print(f"Graph stats: {total_nodes} nodes, {total_edges} edges.")
print("Node counts by type:", node_counts)

raw_graph_json = json.dumps(graph_items, ensure_ascii=False)

# 2. Update graph_visualization.html (2D)
with open('memory/ontology/graph_visualization.html', 'r', encoding='utf-8') as f:
    html_2d = f.read()

# Replace rawGraph
pattern_2d = r'const rawGraph = \[.*?\];\n'
match_2d = re.search(pattern_2d, html_2d, re.DOTALL)
if match_2d:
    html_2d = html_2d[:match_2d.start()] + f'const rawGraph = {raw_graph_json};\n' + html_2d[match_2d.end():]
    print("Replaced rawGraph in graph_visualization.html")
else:
    print("ERROR: rawGraph pattern not found in graph_visualization.html")

# Update 2D legend
legend_2d_old = r'<h3>Leyenda Ontológica \(.*?\)</h3>\s*<div class="legend-grid">.*?</div>\s*</div>'
legend_2d_new = f'''<h3>Leyenda Ontológica ({total_nodes} Nodos / {total_edges} Aristas)</h3>
        <div class="legend-grid">
          <div class="legend-item"><div class="legend-color" style="background: var(--nordic-method);"></div><span>Métodos ({node_counts.get('Method', 0)})</span></div>
          <div class="legend-item"><div class="legend-color" style="background: var(--nordic-concept);"></div><span>Conceptos ({node_counts.get('Concept', 0)})</span></div>
          <div class="legend-item"><div class="legend-color" style="background: var(--nordic-assumption);"></div><span>Supuestos ({node_counts.get('Assumption', 0)})</span></div>
          <div class="legend-item"><div class="legend-color" style="background: var(--nordic-framework);"></div><span>Marcos ({node_counts.get('Framework', 0)})</span></div>
          <div class="legend-item"><div class="legend-color" style="background: var(--nordic-package);"></div><span>Paquetes ({node_counts.get('RPackage', 0)})</span></div>
          <div class="legend-item"><div class="legend-color" style="background: var(--nordic-function);"></div><span>Funciones ({node_counts.get('RFunction', 0)})</span></div>
          <div class="legend-item"><div class="legend-color" style="background: var(--nordic-dataset);"></div><span>Datasets ({node_counts.get('Dataset', 0)})</span></div>
        </div>
      </div>'''

html_2d = re.sub(legend_2d_old, legend_2d_new, html_2d, flags=re.DOTALL)

with open('memory/ontology/graph_visualization.html', 'w', encoding='utf-8') as f:
    f.write(html_2d)
print("Updated memory/ontology/graph_visualization.html successfully.")

# 3. Update graph_visualization_3d.html (3D)
with open('memory/ontology/graph_visualization_3d.html', 'r', encoding='utf-8') as f:
    html_3d = f.read()

# Replace rawGraph in 3D
pattern_3d = r'const rawGraph = \[.*?\];\n'
match_3d = re.search(pattern_3d, html_3d, re.DOTALL)
if match_3d:
    html_3d = html_3d[:match_3d.start()] + f'const rawGraph = {raw_graph_json};\n' + html_3d[match_3d.end():]
    print("Replaced rawGraph in graph_visualization_3d.html")
else:
    print("ERROR: rawGraph pattern not found in graph_visualization_3d.html")

# Update HUD header
hud_old = r'<div id="hud-header">\s*<h1>Ontología Econométrica & Causal 3D</h1>\s*<p>.*?</p>\s*</div>'
hud_new = f'''<div id="hud-header">
    <h1>Ontología Econométrica & Causal 3D</h1>
    <p>{total_nodes} Entidades Indexadas — {total_edges} Vínculos Teóricos & Empíricos</p>
  </div>'''
html_3d = re.sub(hud_old, hud_new, html_3d, flags=re.DOTALL)

# Update cluster pills to include MIT 14.384
cluster_old = r'<div class="cluster-pills">.*?</div>'
cluster_new = '''<div class="cluster-pills">
          <button class="cluster-pill" onclick="directSelectNode('framework_graduate_time_series')">📈 MIT 14.384 Series</button>
          <button class="cluster-pill" onclick="directSelectNode('framework_mostly_harmless_bigdata')">⚡ MIT 14.387 Big Data</button>
          <button class="cluster-pill" onclick="directSelectNode('framework_graduate_econometrics_core')">🏛️ MIT 14.382 Core</button>
          <button class="cluster-pill" onclick="directSelectNode('framework_potential_outcomes')">🎯 Inferencia Causal</button>
          <button class="cluster-pill" onclick="directSelectNode('framework_microeconometrics')">📊 Microeconometría</button>
          <button class="cluster-pill" onclick="directSelectNode('framework_spatial_econometrics')">🗺️ Econometría Espacial</button>
        </div>'''
html_3d = re.sub(cluster_old, cluster_new, html_3d, flags=re.DOTALL)

# Update 3D legend
legend_3d_old = r'<h3>Leyenda Ontológica \(.*?\)</h3>\s*<div class="legend-grid">.*?</div>\s*</div>'
legend_3d_new = f'''<h3>Leyenda Ontológica ({total_nodes} Nodos / {total_edges} Aristas)</h3>
        <div class="legend-grid">
          <div class="legend-item" onclick="filterEntities('Method')"><div class="legend-color" style="background: var(--vibrant-method); color: var(--vibrant-method);"></div><span>Métodos ({node_counts.get('Method', 0)})</span></div>
          <div class="legend-item" onclick="filterEntities('Concept')"><div class="legend-color" style="background: var(--vibrant-concept); color: var(--vibrant-concept);"></div><span>Conceptos ({node_counts.get('Concept', 0)})</span></div>
          <div class="legend-item" onclick="filterEntities('Assumption')"><div class="legend-color" style="background: var(--vibrant-assumption); color: var(--vibrant-assumption);"></div><span>Supuestos ({node_counts.get('Assumption', 0)})</span></div>
          <div class="legend-item" onclick="filterEntities('Framework')"><div class="legend-color" style="background: var(--vibrant-framework); color: var(--vibrant-framework);"></div><span>Marcos ({node_counts.get('Framework', 0)})</span></div>
          <div class="legend-item" onclick="filterEntities('RPackage')"><div class="legend-color" style="background: var(--vibrant-package); color: var(--vibrant-package);"></div><span>Paquetes ({node_counts.get('RPackage', 0)})</span></div>
          <div class="legend-item" onclick="filterEntities('RFunction')"><div class="legend-color" style="background: var(--vibrant-function); color: var(--vibrant-function);"></div><span>Funciones ({node_counts.get('RFunction', 0)})</span></div>
          <div class="legend-item" onclick="filterEntities('Dataset')"><div class="legend-color" style="background: var(--vibrant-dataset); color: var(--vibrant-dataset);"></div><span>Datasets ({node_counts.get('Dataset', 0)})</span></div>
        </div>
      </div>'''
html_3d = re.sub(legend_3d_old, legend_3d_new, html_3d, flags=re.DOTALL)

with open('memory/ontology/graph_visualization_3d.html', 'w', encoding='utf-8') as f:
    f.write(html_3d)
print("Updated memory/ontology/graph_visualization_3d.html successfully.")
