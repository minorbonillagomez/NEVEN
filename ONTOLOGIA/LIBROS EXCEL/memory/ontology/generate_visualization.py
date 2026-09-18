#!/usr/bin/env python3
"""
Genera graph_visualization.html desde graph.jsonl
Ontología de funciones Excel
"""

import json
from pathlib import Path

# Colores por tipo de entidad (adaptados para Excel)
TYPE_COLORS = {
    "ExcelFunction": "#4ade80",      # Verde - funciones
    "Category": "#f59e0b",           # Naranja - categorías
    "Concept": "#d9ab7e",            # Dorado - conceptos
    "BestPractice": "#22d3ee",       # Cyan - mejores prácticas
    "CommonError": "#ef4444",        # Rojo - errores comunes
    "Technique": "#a78bfa",          # Violeta - técnicas
    "Shortcut": "#f472b6",           # Rosa - atajos
    "Feature": "#60a5fa",            # Azul - características
}

# Colores por tipo de relación
REL_COLORS = {
    "belongs_to": "#6b7280",
    "related_to": "#10b981",
    "alternative_to": "#f59e0b",
    "combines_with": "#3b82f6",
    "part_of": "#8b5cf6",
    "requires": "#ec4899",
    "replaces": "#ef4444",
}

def load_graph(jsonl_path):
    """Carga el grafo desde graph.jsonl"""
    entities = {}
    relations = []
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("op") == "create":
                    entity = obj["entity"]
                    entities[entity["id"]] = entity
                elif obj.get("op") == "relate":
                    relations.append({
                        "from": obj["from"],
                        "to": obj["to"],
                        "rel": obj["rel"]
                    })
            except json.JSONDecodeError:
                continue
    
    return entities, relations

def generate_html(entities, relations, output_path):
    """Genera el HTML de visualización"""
    
    # Generar nodos
    nodes_js = []
    for eid, entity in entities.items():
        props = entity.get("properties", {})
        etype = entity.get("type", "Concept")
        color = TYPE_COLORS.get(etype, "#9ca3af")
        
        name = props.get("name", eid)
        description = props.get("description", props.get("definition", props.get("syntax", "")))[:200]
        
        node = {
            "id": eid,
            "label": name[:25] + ("..." if len(name) > 25 else ""),
            "title": f"<b>{name}</b><br><i>{etype}</i><br>{description}",
            "color": {"background": color, "border": color, "highlight": {"background": "#fff", "border": color}},
            "font": {"color": "#fff", "size": 11},
            "shape": "box" if etype == "ExcelFunction" else ("diamond" if etype == "Category" else "dot"),
            "size": 18 if etype == "Category" else 12,
            "type": etype,
            "fullName": name,
            "description": description
        }
        nodes_js.append(node)
    
    # Generar aristas
    edges_js = []
    for rel in relations:
        if rel["from"] in entities and rel["to"] in entities:
            color = REL_COLORS.get(rel["rel"], "#6b7280")
            edge = {
                "from": rel["from"],
                "to": rel["to"],
                "label": rel["rel"].replace("_", " "),
                "color": {"color": color, "opacity": 0.6},
                "font": {"color": "#9da3af", "size": 8, "strokeWidth": 0},
                "arrows": "to",
                "smooth": {"type": "curvedCW", "roundness": 0.2}
            }
            edges_js.append(edge)
    
    # Generar estadísticas por tipo
    type_counts = {}
    for entity in entities.values():
        t = entity.get("type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    
    stats_html = "".join([
        f'<div class="stat-item"><span class="stat-color" style="background:{TYPE_COLORS.get(t, "#9ca3af")}"></span>'
        f'<span class="stat-label">{t}</span><span class="stat-count">{c}</span></div>'
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1])
    ])
    
    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ontología Excel — NEVEN</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {{
      --bg-main: #0f1419;
      --bg-panel: #1a1f26;
      --bg-card: #242b35;
      --border-subtle: #2d3748;
      --border-focus: #4a5568;
      --text-primary: #e2e8f0;
      --text-secondary: #a0aec0;
      --text-muted: #718096;
      --accent: #4ade80;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-main);
      color: var(--text-primary);
      height: 100vh;
      display: flex;
    }}
    #network {{ flex: 1; height: 100%; }}
    #sidebar {{
      width: 380px;
      background: var(--bg-panel);
      border-left: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    .sidebar-header {{
      padding: 16px;
      border-bottom: 1px solid var(--border-subtle);
      background: linear-gradient(135deg, #1a472a 0%, #1a1f26 100%);
    }}
    .sidebar-header h2 {{
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 8px;
      color: var(--accent);
    }}
    .search-box {{
      display: flex;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 8px 12px;
    }}
    .search-box input {{
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-primary);
      font-size: 13px;
    }}
    .stats {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .stat-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      background: var(--bg-card);
      padding: 4px 8px;
      border-radius: 4px;
    }}
    .stat-color {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}
    .stat-label {{ color: var(--text-secondary); }}
    .stat-count {{ color: var(--text-primary); font-weight: 600; }}
    #node-list {{
      flex: 1;
      overflow-y: auto;
      padding: 8px;
    }}
    .node-item {{
      padding: 10px 12px;
      margin-bottom: 4px;
      background: var(--bg-card);
      border-radius: 6px;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s;
    }}
    .node-item:hover {{
      border-color: var(--accent);
    }}
    .node-item-name {{
      font-size: 12px;
      font-weight: 500;
      margin-bottom: 2px;
    }}
    .node-item-type {{
      font-size: 10px;
      color: var(--text-muted);
    }}
    #detail-panel {{
      padding: 16px;
      border-top: 1px solid var(--border-subtle);
      background: var(--bg-card);
      max-height: 200px;
      overflow-y: auto;
      display: none;
    }}
    #detail-panel h3 {{
      font-size: 13px;
      margin-bottom: 8px;
    }}
    #detail-panel p {{
      font-size: 11px;
      color: var(--text-secondary);
      line-height: 1.5;
      font-family: 'Consolas', monospace;
    }}
    .controls {{
      position: absolute;
      bottom: 20px;
      right: 400px;
      display: flex;
      gap: 8px;
      z-index: 10;
    }}
    .control-btn {{
      background: var(--bg-panel);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
    }}
    .control-btn:hover {{
      background: var(--bg-card);
      color: var(--accent);
      border-color: var(--accent);
    }}
  </style>
</head>
<body>
  <div id="network"></div>
  
  <div id="sidebar">
    <div class="sidebar-header">
      <h2>📊 Ontología Excel — NEVEN</h2>
      <div class="search-box">
        <input type="text" id="search" placeholder="Buscar función Excel...">
      </div>
    </div>
    
    <div class="stats">
      {stats_html}
    </div>
    
    <div id="node-list"></div>
    
    <div id="detail-panel">
      <h3 id="detail-name"></h3>
      <p id="detail-desc"></p>
    </div>
  </div>
  
  <div class="controls">
    <button class="control-btn" onclick="network.fit()">🔍 Fit</button>
    <button class="control-btn" onclick="togglePhysics()">⚡ Physics</button>
    <button class="control-btn" onclick="filterByType()">🏷️ Filter</button>
  </div>

<script>
const nodesData = {json.dumps(nodes_js, ensure_ascii=False)};
const edgesData = {json.dumps(edges_js, ensure_ascii=False)};

const nodes = new vis.DataSet(nodesData);
const edges = new vis.DataSet(edgesData);

const container = document.getElementById('network');
const data = {{ nodes, edges }};
const options = {{
  physics: {{
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{
      gravitationalConstant: -80,
      centralGravity: 0.015,
      springLength: 120,
      springConstant: 0.06
    }},
    stabilization: {{ iterations: 200 }}
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 100,
    zoomView: true,
    dragView: true
  }},
  nodes: {{
    borderWidth: 2,
    shadow: true
  }},
  edges: {{
    width: 1,
    shadow: false
  }}
}};

const network = new vis.Network(container, data, options);

// Render node list
const nodeList = document.getElementById('node-list');
const sortedNodes = [...nodesData].sort((a, b) => a.fullName.localeCompare(b.fullName));

sortedNodes.forEach(node => {{
  const div = document.createElement('div');
  div.className = 'node-item';
  div.innerHTML = `
    <div class="node-item-name" style="color:${{node.color.background}}">${{node.fullName}}</div>
    <div class="node-item-type">${{node.type}}</div>
  `;
  div.onclick = () => {{
    network.focus(node.id, {{ scale: 1.5, animation: true }});
    network.selectNodes([node.id]);
    showDetail(node);
  }};
  nodeList.appendChild(div);
}});

// Search
document.getElementById('search').addEventListener('input', (e) => {{
  const query = e.target.value.toLowerCase();
  document.querySelectorAll('.node-item').forEach(item => {{
    const name = item.querySelector('.node-item-name').textContent.toLowerCase();
    item.style.display = name.includes(query) ? '' : 'none';
  }});
}});

// Show detail
function showDetail(node) {{
  document.getElementById('detail-panel').style.display = 'block';
  document.getElementById('detail-name').textContent = node.fullName;
  document.getElementById('detail-name').style.color = node.color.background;
  document.getElementById('detail-desc').textContent = node.description || 'Sin descripción';
}}

network.on('click', (params) => {{
  if (params.nodes.length > 0) {{
    const node = nodesData.find(n => n.id === params.nodes[0]);
    if (node) showDetail(node);
  }}
}});

let physicsEnabled = true;
function togglePhysics() {{
  physicsEnabled = !physicsEnabled;
  network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
}}

let currentTypeFilter = null;
const types = [...new Set(nodesData.map(n => n.type))];
function filterByType() {{
  const idx = currentTypeFilter === null ? 0 : (types.indexOf(currentTypeFilter) + 1) % (types.length + 1);
  currentTypeFilter = idx === types.length ? null : types[idx];
  
  if (currentTypeFilter === null) {{
    nodes.update(nodesData.map(n => ({{ id: n.id, hidden: false }})));
  }} else {{
    nodes.update(nodesData.map(n => ({{ id: n.id, hidden: n.type !== currentTypeFilter }})));
  }}
}}
</script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generado: {output_path}")
    print(f"   Nodos: {len(nodes_js)}")
    print(f"   Aristas: {len(edges_js)}")

if __name__ == "__main__":
    base = Path(__file__).parent
    graph_path = base / "graph.jsonl"
    output_path = base / "graph_visualization.html"
    
    entities, relations = load_graph(graph_path)
    generate_html(entities, relations, output_path)
