#!/usr/bin/env python3
"""
Genera graph_visualization.html desde los YAMLs de neven-core
Usa vis-network para visualización interactiva del grafo de ontología
"""

import json
import yaml
from pathlib import Path

# Colores por prioridad
PRIORITY_COLORS = {
    1: "#ef4444",  # Rojo - Crítico
    2: "#f97316",  # Naranja - Alto
    3: "#eab308",  # Amarillo - Medio
    4: "#22c55e",  # Verde - Soporte
}

# Colores por tipo de componente (inferido del id)
TYPE_COLORS = {
    "core": "#dc2626",      # Rojo
    "control": "#7c3aed",   # Violeta
    "common": "#2563eb",    # Azul
    "pb": "#0891b2",        # Cyan
    "ribbon": "#059669",    # Verde
    "taskpane": "#d97706",  # Naranja
    "webview": "#be185d",   # Rosa
    "studio": "#4f46e5",    # Indigo
    "http": "#0d9488",      # Teal
    "startup": "#65a30d",   # Lima
    "dispatcher": "#ca8a04", # Amarillo
    "sidecar": "#a855f7",   # Púrpura
    "config": "#6b7280",    # Gris
    "default": "#9ca3af",   # Gris claro
}

def get_type_from_id(comp_id):
    """Infiere el tipo de componente desde su ID"""
    comp_id_lower = comp_id.lower()
    for key in TYPE_COLORS:
        if key in comp_id_lower:
            return key
    return "default"

def load_yamls(yaml_dir):
    """Carga todos los YAMLs de ontología"""
    componentes = []
    
    for yaml_file in sorted(yaml_dir.glob("neven-ontology-*.yaml")):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'componentes' in data:
                    for comp in data['componentes']:
                        comp['_source'] = yaml_file.name
                        componentes.append(comp)
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")
    
    return componentes

def generate_html(componentes, output_path):
    """Genera el HTML de visualización"""
    
    # Crear mapa de IDs
    id_set = {c['id'] for c in componentes}
    
    # Generar nodos
    nodes_js = []
    for comp in componentes:
        comp_id = comp['id']
        comp_type = get_type_from_id(comp_id)
        priority = comp.get('prioridad', 3)
        
        # Color basado en tipo
        color = TYPE_COLORS.get(comp_type, TYPE_COLORS['default'])
        
        # Tamaño basado en prioridad
        size = 25 - (priority * 4)  # P1=21, P2=17, P3=13, P4=9
        
        name = comp.get('nombre', comp_id)
        description = comp.get('descripcion', '')[:300] if comp.get('descripcion') else ''
        
        # Contar invariantes y dependencias
        inv_count = len(comp.get('invariantes', []))
        dep_count = len(comp.get('dependencias', []))
        
        tooltip = f"<b>{name}</b><br><i>Prioridad: {priority}</i>"
        if description:
            tooltip += f"<br>{description[:150]}..."
        tooltip += f"<br>Invariantes: {inv_count} | Deps: {dep_count}"
        
        node = {
            "id": comp_id,
            "label": comp_id.replace('_', '\n'),
            "title": tooltip,
            "color": {"background": color, "border": color, "highlight": {"background": "#fff", "border": color}},
            "font": {"color": "#fff", "size": 10},
            "shape": "box",
            "size": size,
            "type": comp_type,
            "priority": priority,
            "fullName": name,
            "description": description,
            "invariants": inv_count,
            "source": comp.get('_source', '')
        }
        nodes_js.append(node)
    
    # Generar aristas desde dependencias
    edges_js = []
    for comp in componentes:
        comp_id = comp['id']
        deps = comp.get('dependencias', [])
        for dep in deps:
            if dep in id_set:
                edge = {
                    "from": comp_id,
                    "to": dep,
                    "arrows": "to",
                    "color": {"color": "#4b5563", "opacity": 0.6},
                    "smooth": {"type": "curvedCW", "roundness": 0.15}
                }
                edges_js.append(edge)
    
    # Estadísticas por prioridad
    priority_counts = {}
    for comp in componentes:
        p = comp.get('prioridad', 3)
        priority_counts[p] = priority_counts.get(p, 0) + 1
    
    stats_html = "".join([
        f'<div class="stat-item"><span class="stat-color" style="background:{PRIORITY_COLORS.get(p, "#9ca3af")}"></span>'
        f'<span class="stat-label">P{p}</span><span class="stat-count">{c}</span></div>'
        for p, c in sorted(priority_counts.items())
    ])
    
    # Estadísticas por tipo
    type_counts = {}
    for node in nodes_js:
        t = node['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    
    type_stats_html = "".join([
        f'<div class="stat-item"><span class="stat-color" style="background:{TYPE_COLORS.get(t, "#9ca3af")}"></span>'
        f'<span class="stat-label">{t}</span><span class="stat-count">{c}</span></div>'
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]) if t != 'default'
    ])
    
    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NEVEN Core — Arquitectura del Sistema</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {{
      --bg-main: #0f1115;
      --bg-panel: #16181d;
      --bg-card: #1e2028;
      --border-subtle: #2a2d35;
      --border-focus: #3e424c;
      --text-primary: #e6e8ec;
      --text-secondary: #9da3af;
      --text-muted: #656a76;
      --accent: #6366f1;
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
    }}
    .sidebar-header h2 {{
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 4px;
      color: var(--accent);
    }}
    .sidebar-header p {{
      font-size: 11px;
      color: var(--text-muted);
    }}
    .search-box {{
      display: flex;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 8px 12px;
      margin-top: 10px;
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
      padding: 10px 16px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .stats-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 6px;
    }}
    .stats-label {{
      font-size: 9px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }}
    .stat-item {{
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 10px;
      background: var(--bg-card);
      padding: 3px 6px;
      border-radius: 3px;
    }}
    .stat-color {{
      width: 6px;
      height: 6px;
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
      border-color: var(--border-focus);
      background: #252830;
    }}
    .node-item-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2px;
    }}
    .node-item-name {{
      font-size: 11px;
      font-weight: 500;
    }}
    .node-item-priority {{
      font-size: 9px;
      padding: 1px 5px;
      border-radius: 3px;
      font-weight: 600;
    }}
    .node-item-desc {{
      font-size: 10px;
      color: var(--text-muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    #detail-panel {{
      padding: 16px;
      border-top: 1px solid var(--border-subtle);
      background: var(--bg-card);
      max-height: 220px;
      overflow-y: auto;
      display: none;
    }}
    #detail-panel h3 {{
      font-size: 13px;
      margin-bottom: 6px;
    }}
    #detail-panel .detail-meta {{
      font-size: 10px;
      color: var(--text-muted);
      margin-bottom: 8px;
    }}
    #detail-panel p {{
      font-size: 11px;
      color: var(--text-secondary);
      line-height: 1.5;
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
      font-size: 11px;
    }}
    .control-btn:hover {{
      background: var(--bg-card);
      color: var(--text-primary);
    }}
    .legend {{
      position: absolute;
      top: 20px;
      left: 20px;
      background: var(--bg-panel);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 12px;
      font-size: 10px;
      z-index: 10;
    }}
    .legend-title {{
      font-weight: 600;
      margin-bottom: 8px;
      color: var(--text-secondary);
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
    }}
    .legend-color {{
      width: 12px;
      height: 12px;
      border-radius: 3px;
    }}
  </style>
</head>
<body>
  <div id="network"></div>
  
  <div class="legend">
    <div class="legend-title">Prioridad</div>
    <div class="legend-item"><div class="legend-color" style="background:#ef4444"></div> P1 Critico</div>
    <div class="legend-item"><div class="legend-color" style="background:#f97316"></div> P2 Alto</div>
    <div class="legend-item"><div class="legend-color" style="background:#eab308"></div> P3 Medio</div>
    <div class="legend-item"><div class="legend-color" style="background:#22c55e"></div> P4 Soporte</div>
  </div>
  
  <div id="sidebar">
    <div class="sidebar-header">
      <h2>NEVEN Core Architecture</h2>
      <p>{len(componentes)} componentes | {len(edges_js)} dependencias</p>
      <div class="search-box">
        <input type="text" id="search" placeholder="Buscar componente...">
      </div>
    </div>
    
    <div class="stats">
      <div class="stats-label">Por Prioridad</div>
      <div class="stats-row">{stats_html}</div>
      <div class="stats-label" style="margin-top:8px">Por Tipo</div>
      <div class="stats-row">{type_stats_html}</div>
    </div>
    
    <div id="node-list"></div>
    
    <div id="detail-panel">
      <h3 id="detail-name"></h3>
      <div class="detail-meta" id="detail-meta"></div>
      <p id="detail-desc"></p>
    </div>
  </div>
  
  <div class="controls">
    <button class="control-btn" onclick="network.fit()">Fit</button>
    <button class="control-btn" onclick="togglePhysics()">Physics</button>
    <button class="control-btn" onclick="filterByPriority()">Filter P</button>
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
      springConstant: 0.06,
      damping: 0.4
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
    shadow: {{ enabled: true, size: 10, x: 3, y: 3 }}
  }},
  edges: {{
    width: 1.5,
    shadow: false
  }},
  layout: {{
    improvedLayout: true
  }}
}};

const network = new vis.Network(container, data, options);

// Priority colors for badges
const priorityColors = {{ 1: '#ef4444', 2: '#f97316', 3: '#eab308', 4: '#22c55e' }};

// Render node list
const nodeList = document.getElementById('node-list');
const sortedNodes = [...nodesData].sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id));

sortedNodes.forEach(node => {{
  const div = document.createElement('div');
  div.className = 'node-item';
  div.innerHTML = `
    <div class="node-item-header">
      <span class="node-item-name" style="color:${{node.color.background}}">${{node.id}}</span>
      <span class="node-item-priority" style="background:${{priorityColors[node.priority] || '#6b7280'}}">P${{node.priority}}</span>
    </div>
    <div class="node-item-desc">${{node.fullName}}</div>
  `;
  div.onclick = () => {{
    network.focus(node.id, {{ scale: 1.2, animation: true }});
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
    const desc = item.querySelector('.node-item-desc').textContent.toLowerCase();
    item.style.display = (name.includes(query) || desc.includes(query)) ? '' : 'none';
  }});
}});

// Show detail
function showDetail(node) {{
  document.getElementById('detail-panel').style.display = 'block';
  document.getElementById('detail-name').textContent = node.fullName;
  document.getElementById('detail-name').style.color = node.color.background;
  document.getElementById('detail-meta').textContent = `P${{node.priority}} | ${{node.invariants}} invariantes | ${{node.source}}`;
  document.getElementById('detail-desc').textContent = node.description || 'Sin descripcion';
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

let currentPriorityFilter = null;
const priorities = [1, 2, 3, 4];
function filterByPriority() {{
  const idx = currentPriorityFilter === null ? 0 : (priorities.indexOf(currentPriorityFilter) + 1) % (priorities.length + 1);
  currentPriorityFilter = idx === priorities.length ? null : priorities[idx];
  
  if (currentPriorityFilter === null) {{
    nodes.update(nodesData.map(n => ({{ id: n.id, hidden: false }})));
  }} else {{
    nodes.update(nodesData.map(n => ({{ id: n.id, hidden: n.priority !== currentPriorityFilter }})));
  }}
}}

// Initial fit after stabilization
network.once('stabilizationIterationsDone', () => {{
  network.fit();
}});
</script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generado: {output_path}")
    print(f"   Nodos: {len(nodes_js)}")
    print(f"   Aristas: {len(edges_js)}")

if __name__ == "__main__":
    base = Path(__file__).parent
    output_path = base / "graph_visualization.html"
    
    componentes = load_yamls(base)
    print(f"Cargados: {len(componentes)} componentes")
    generate_html(componentes, output_path)
