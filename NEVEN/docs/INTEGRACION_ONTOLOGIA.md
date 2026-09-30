# Plan de Integración: NEVEN + Ontología Econométrica

**Fecha:** 2026-08-19  
**Estado:** Diseño aprobado — pendiente de implementación  
**Contexto:** Sesión de diseño arquitectural completa documentada en `.kiro/contexto/CHAT.md` y `ONTOLOGIA/LIBROS/CHAT.md`

---

## Visión

La ontología es el **cerebro** de NEVEN. NEVEN es la **máquina**.

La integración conecta el Knowledge Graph econométrico (199 nodos, 399 aristas, 8 frameworks, MIT 14.382/14.384/14.387) con el motor computacional de NEVEN para guiar al usuario desde su **PREGUNTA** hasta una **RESPUESTA** basada en evidencia cuantitativa, con razonamiento metodológico explícito y fundamentación bibliográfica.

```
PREGUNTA → PLANTEO → [DIAGNÓSTICO METODOLÓGICO + EJECUCIÓN] → RESPUESTA
```

---

## Principios de la integración

1. **No romper lo existente.** Toda la integración se añade como capas nuevas encima de la arquitectura actual. Ningún endpoint ni componente existente se modifica en la primera fase.

2. **La responsabilidad es del usuario.** La ontología advierte — no bloquea. Siempre presenta el mejor camino disponible con advertencias explícitas. El usuario decide.

3. **Comprensión antes que uso.** Las advertencias son lecciones contextualizadas con referencia bibliográfica. El lema es "nos interesa más la comprensión que el uso mismo".

4. **Reutilización de componentes existentes.** `buildSlotElement`, `_parse_slots_from_variable`, el sistema de slots `{name, label, type, value, tier}`, el Tab IA con `/api/ai/chat` — todo reutilizado. La ontología se expresa en el idioma que NEVEN ya habla.

---

## Arquitectura de la integración

### Capas nuevas a añadir

```
┌─────────────────────────────────────────────────────────────┐
│                    NEVEN Studio (browser)                    │
│                                                             │
│  Tab IA (existente)          Tab Data Lab (existente)        │
│  └─ /api/ai/chat ──────►    └─ selectFunction(card)         │
│     [AMPLIADO con                └─ renderOntologyPanel()    │
│      contexto ontológico]          [NUEVO]                   │
│                                  └─ runAnalysis()            │
│                                    └─ renderResults()        │
│                                      └─ [advertencias        │
│                                          pedagógicas NUEVO]  │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP localhost:5555
┌──────────────────▼──────────────────────────────────────────┐
│              neven_http_server.py (ControlPython.exe)        │
│                                                             │
│  ENDPOINTS NUEVOS:                                          │
│  GET  /api/kg/method/{function_id}  → nodo del grafo        │
│  POST /api/kg/diagnose              → plan metodológico      │
│  POST /api/kg/profile               → perfil del dataset     │
│                                                             │
│  ENDPOINTS EXTENDIDOS:                                      │
│  POST /api/ai/chat    → contexto ontológico inyectado       │
│  POST /api/datalab/run → slots de advertencia pedagógica    │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              ontology_engine.py  [NUEVO]                     │
│                                                             │
│  - Carga graph.jsonl en memoria al iniciar                  │
│  - get_method_node(function_id) → nodo Method               │
│  - get_assumptions(method_id) → [Assumption nodes]          │
│  - get_concepts(method_id) → [Concept nodes]                │
│  - suggest_from_profile(dataset_profile) → [Method nodes]   │
│  - build_diagnostic_plan(method_id, profile) → plan         │
│  - build_pedagogy_warning(assumption_id, context) → warning │
└──────────────────┬──────────────────────────────────────────┘
                   │ lee
┌──────────────────▼──────────────────────────────────────────┐
│  ONTOLOGIA/LIBROS/memory/ontology/graph.jsonl               │
│  (199 nodos, 399 aristas — fuente de verdad)                │
└─────────────────────────────────────────────────────────────┘
```

---

## Fase 1 — Motor de Conocimiento (ontology_engine.py)

**Archivo nuevo:** `NEVEN/ControlPython/startup/ontology_engine.py`

Este módulo es el único que habla directamente con el grafo JSONL. Todos los demás componentes le piden información a él.

### Responsabilidades

```python
class OntologyEngine:
    """
    Motor de razonamiento sobre el Knowledge Graph econométrico.
    Se carga una sola vez al iniciar el servidor. Lee graph.jsonl en memoria.
    """

    def __init__(self, graph_path: str):
        """Carga graph.jsonl. Construye índices: por id, por tipo, por relación."""
        
    def get_method_node(self, function_id: str) -> dict | None:
        """
        Dado un function_id del catálogo de DataLab (ej: 'RG_OLS'),
        busca el nodo Method correspondiente en el grafo.
        Estrategia: busca por campo 'r_syntax' que contenga function_id,
        o por nombre normalizado.
        """
        
    def get_related_nodes(self, node_id: str, relation: str) -> list[dict]:
        """
        Retorna todos los nodos relacionados desde node_id via 'relation'.
        Ej: get_related_nodes('method_ols', 'requires') → [assumption_homoscedasticity, ...]
        """
        
    def get_assumptions(self, method_id: str) -> list[dict]:
        """Retorna todos los nodos Assumption que el método requires."""
        
    def get_concepts(self, method_id: str) -> list[dict]:
        """Retorna nodos Concept vinculados (adjusts_for, requires)."""
        
    def get_r_functions(self, method_id: str) -> list[dict]:
        """Retorna nodos RFunction vinculados via uses_r_function."""
        
    def suggest_from_profile(self, profile: dict) -> list[dict]:
        """
        Dado un perfil de dataset, sugiere métodos aplicables.
        
        profile = {
            "n_rows": int,
            "n_cols": int,
            "has_time_dimension": bool,    # columna con año/fecha detectada
            "has_spatial_dimension": bool, # columna con lat/lon o shapefile
            "has_panel_structure": bool,   # id + time detectados
            "outcome_type": "continuous" | "binary" | "count" | "ordered",
            "has_instrument": bool,        # variable Z sin rol asignado
        }
        """
        
    def build_diagnostic_plan(self, method_id: str, profile: dict) -> dict:
        """
        Construye el plan metodológico antes de ejecutar.
        
        Retorna:
        {
            "method": {nombre, descripción, r_syntax},
            "rationale": str,          # Por qué este método para este dataset
            "steps": [                 # Secuencia de ejecución
                {"step": 1, "action": "Verificar homocedasticidad", 
                 "r_function": "bptest()", "package": "lmtest"},
                ...
            ],
            "warnings": [              # Advertencias pedagógicas
                {"severity": "medium", "compact": str, "expanded": {...}},
                ...
            ],
            "references": [            # Referencias bibliográficas
                {"book": str, "chapter": str, "pages": str},
                ...
            ]
        }
        """
        
    def build_pedagogy_warning(self, assumption_id: str, 
                                context: dict) -> dict:
        """
        Construye una advertencia pedagógica completa para un supuesto violado.
        
        context = {
            "test_statistic": float,    # valor del estadístico
            "p_value": float,           # p-valor del test
            "threshold": float,         # umbral convencional
            "variable_name": str,       # variable relevante
        }
        
        Retorna estructura de 5 capas:
        {
            "compact": "⚠ Heterocedasticidad detectada — errores HC1. Ver Hanck Cap. 5",
            "phenomenon": str,     # qué está pasando en los datos del usuario
            "implication": str,    # por qué importa para su respuesta
            "action": str,         # lo que NEVEN hará
            "reference": {
                "text": str,       # frase que hace la referencia apetecible
                "book": str,
                "chapter": str,
                "pages": str,
            },
            "reflection_question": str  # pregunta de reflexión opcional
        }
        """
```

### Índices internos que construye al cargar

El grafo se carga una sola vez y se indexa en memoria:

```python
self._nodes_by_id    = {node["id"]: node for node in all_nodes}
self._nodes_by_type  = {"Method": [...], "Concept": [...], ...}
self._edges_from     = {node_id: [(relation, target_id), ...]}
self._edges_to       = {node_id: [(relation, source_id), ...]}
self._function_index = {r_syntax_fragment: node_id}  # búsqueda por función R
```

Carga en memoria: ~200 nodos × ~2KB promedio = ~400KB. Completamente negligible.

---

## Fase 2 — Endpoints nuevos en neven_http_server.py

### GET /api/kg/method/{function_id}

Retorna el nodo Method del grafo correspondiente a la función seleccionada en DataLab.

**Respuesta:**
```json
{
  "status": "ok",
  "method": {
    "id": "method_ols",
    "name": "Ordinary Least Squares (OLS)",
    "description": "Estimador lineal clásico que minimiza...",
    "r_syntax": "lm(score ~ str + english, data = CASchools)",
    "interpretation_guide": "Cada unidad de reducción en...",
    "reference": {"book": "Hanck et al.", "chapter": "Chapter 4 & 6", "pages": "pp. 85-160"}
  },
  "assumptions": [
    {"id": "assumption_homoscedasticity", "name": "Homoscedasticity (Gauss-Markov)", "definition": "..."},
    ...
  ],
  "concepts": [
    {"id": "concept_multicollinearity", "name": "Multicollinearity", ...},
    ...
  ],
  "r_functions": [
    {"id": "rfunc_bptest", "name": "bptest()", "package": "lmtest", "r_syntax": "bptest(lm_model)", ...},
    ...
  ],
  "found": true
}
```

**Si no se encuentra el método:** `"found": false` con `"method": null`. No es un error — no todos los métodos del DataLab tienen nodo en el grafo todavía.

---

### POST /api/kg/profile

Genera el perfil automático del dataset activo en DuckDB.

**Request:** `{}` (sin body — usa el `dataset` en DuckDB)

**Respuesta:**
```json
{
  "status": "ok",
  "profile": {
    "n_rows": 420,
    "n_cols": 8,
    "columns": [
      {"name": "testscr", "type": "DOUBLE", "nulls": 0, "unique": 420},
      {"name": "str",     "type": "DOUBLE", "nulls": 0, "unique": 37},
      {"name": "year",    "type": "VARCHAR","nulls": 0, "unique": 1}
    ],
    "has_time_dimension": false,
    "has_panel_structure": false,
    "has_spatial_dimension": false,
    "outcome_candidates": ["testscr"],
    "numeric_cols": ["testscr", "str", "calw_pct"],
    "categorical_cols": ["year"]
  }
}
```

**Implementación:** Una sola query DuckDB:
```sql
SELECT column_name, column_type, 
       COUNT(*) - COUNT(column_name) AS nulls,
       COUNT(DISTINCT column_name) AS unique_vals
FROM (DESCRIBE dataset) d
LEFT JOIN dataset ON TRUE
GROUP BY column_name, column_type
```

---

### POST /api/kg/diagnose

El endpoint central de la integración. Recibe la función seleccionada + el perfil del dataset y retorna el plan metodológico completo con advertencias pedagógicas.

**Request:**
```json
{
  "function_id": "RG_OLS",
  "profile": { ... }   // del /api/kg/profile, o calculado en el servidor
}
```

**Respuesta:**
```json
{
  "status": "ok",
  "plan": {
    "method_name": "Ordinary Least Squares (OLS)",
    "rationale": "Tu dataset tiene 420 observaciones con variables continuas. OLS es el estimador adecuado para estimar relaciones lineales entre variables continuas bajo los supuestos de Gauss-Markov.",
    "steps": [
      {
        "step": 1,
        "action": "Verificar ausencia de multicolinealidad severa",
        "r_function": "vif()",
        "package": "car",
        "threshold": "VIF < 5"
      },
      {
        "step": 2,
        "action": "Verificar homocedasticidad (Breusch-Pagan)",
        "r_function": "bptest()",
        "package": "lmtest",
        "threshold": "p-valor > 0.05"
      }
    ],
    "warnings": [
      {
        "severity": "info",
        "compact": "ℹ Con N=420 observaciones, los tests diagnósticos tienen alta potencia.",
        "phenomenon": "...",
        "implication": "...",
        "action": "...",
        "reference": {"book": "Hanck et al.", "chapter": "Chapter 5", "pages": "pp. 120-135"},
        "reflection_question": "..."
      }
    ]
  }
}
```

---

## Fase 3 — Panel Ontológico en el Tab Data Lab

### Hook de integración: `selectFunction(card)`

`selectFunction(card)` en `datalab.js` ya llama a `renderColumnPanel`, `renderParameterForm` y `renderDescriptionCard`. Se añade una llamada más:

```javascript
// En selectFunction(card) — AÑADIR al final:
renderOntologyPanel(card);   // ← nueva función
```

### Nueva función: `renderOntologyPanel(card)`

```javascript
async function renderOntologyPanel(card) {
  var panel = document.getElementById('dl-ontology-panel');
  if (!panel) return;
  
  panel.innerHTML = '';  // limpiar
  
  // 1. Consultar el grafo
  var resp = await fetch(_DL_API + '/api/kg/method/' + card.id);
  if (!resp.ok) return;
  var data = await resp.json();
  if (!data.found) {
    // Mostrar panel vacío discreto — no alarmar al usuario
    panel.innerHTML = '<div style="font-size:9px;color:var(--text-secondary);padding:4px">...</div>';
    return;
  }
  
  // 2. Renderizar: descripción del método + supuestos + referencia
  // Panel compacto por defecto, expandible
  renderMethodDescription(panel, data.method);
  renderAssumptionChips(panel, data.assumptions);
}
```

### Estructura del panel ontológico en taskpane.html

Añadir en el Tab Data Lab, después de `#dl-description-card` y antes de `#dl-run-row`:

```html
<!-- Panel Ontológico — aparece al seleccionar una función -->
<div id="dl-ontology-panel" style="display:none">
  
  <!-- Descripción del método (del grafo) -->
  <div id="dl-kg-description" class="card" style="display:none">
    <div class="card-title">Marco Metodológico</div>
    <div id="dl-kg-method-text" style="font-size:11px;line-height:1.6;color:var(--text-primary)"></div>
    <div id="dl-kg-reference" style="font-size:9px;color:var(--text-secondary);margin-top:4px"></div>
  </div>
  
  <!-- Supuestos a verificar (chips) -->
  <div id="dl-kg-assumptions" class="card" style="display:none">
    <div class="card-title">Supuestos del método</div>
    <div id="dl-kg-assumption-chips" style="display:flex;flex-wrap:wrap;gap:4px"></div>
  </div>
  
</div>
```

---

## Fase 4 — Advertencias Pedagógicas en los Resultados

### Cómo funciona

Las funciones `.Studio.R` de NEVEN ya devuelven slots `{name, label, type, value, tier}`. Se añade un slot especial de tipo `"warning_pedagogy"` que el frontend renderiza con la estructura de 5 capas.

**En R** (en las funciones `.Studio.R` que ejecutan tests diagnósticos):
```r
# Si Breusch-Pagan es significativo:
bp_result <- lmtest::bptest(modelo)
if (bp_result$p.value < 0.05) {
  warning_slot <- data.frame(
    name  = "warning_heterocedasticidad",
    label = "Advertencia: Heterocedasticidad",
    type  = "warning_pedagogy",
    value = jsonlite::toJSON(list(
      assumption_id = "assumption_homoscedasticity",
      test_statistic = as.numeric(bp_result$statistic),
      p_value = as.numeric(bp_result$p.value),
      threshold = 0.05,
      variable_name = "residuos del modelo"
    ), auto_unbox = TRUE),
    tier  = 1
  )
}
```

**En Python** (`datalab_handler.py`) — al procesar los slots, si hay uno de tipo `warning_pedagogy`, se enriquece consultando el `OntologyEngine`:

```python
# En handle_run(), después de _parse_slots_from_variable():
slots = self._enrich_with_pedagogy(slots, ontology_engine)
```

```python
def _enrich_with_pedagogy(self, slots, engine):
    """
    Enriquece slots de tipo 'warning_pedagogy' con el contenido 
    pedagógico completo del OntologyEngine.
    """
    enriched = []
    for slot in slots:
        if slot.get("type") == "warning_pedagogy":
            context = slot.get("value", {})
            warning = engine.build_pedagogy_warning(
                context.get("assumption_id", ""),
                context
            )
            slot["value"] = warning
        enriched.append(slot)
    return enriched
```

**En JavaScript** (`buildSlotElement` en `datalab.js`) — nuevo case:

```javascript
case 'warning_pedagogy':
  content = _renderPedagogyWarning(slot.value);
  break;
```

```javascript
function _renderPedagogyWarning(warning) {
  var div = document.createElement('div');
  div.style.cssText = 'border:1px solid rgba(215,165,56,0.4);border-radius:6px;' +
                      'background:rgba(215,165,56,0.06);overflow:hidden';
  
  // Nivel compacto — siempre visible
  var compact = document.createElement('div');
  compact.style.cssText = 'padding:8px 12px;cursor:pointer;display:flex;' +
                          'align-items:center;justify-content:space-between';
  compact.innerHTML = '<span style="font-size:11px;color:var(--accent)">' + 
                      (warning.compact || '') + '</span>' +
                      '<span style="font-size:10px;color:var(--text-secondary)">▼ Expandir</span>';
  
  // Nivel expandido — oculto por defecto
  var expanded = document.createElement('div');
  expanded.style.cssText = 'display:none;padding:10px 14px;border-top:1px solid rgba(215,165,56,0.2)';
  expanded.innerHTML = _buildExpandedWarning(warning);
  
  compact.addEventListener('click', function() {
    var isOpen = expanded.style.display !== 'none';
    expanded.style.display = isOpen ? 'none' : 'block';
    compact.querySelector('span:last-child').textContent = isOpen ? '▼ Expandir' : '▲ Cerrar';
  });
  
  div.appendChild(compact);
  div.appendChild(expanded);
  return div;
}

function _buildExpandedWarning(w) {
  var ref = w.reference || {};
  return [
    '<div style="margin-bottom:8px">',
    '  <div style="font-size:9px;font-weight:600;color:var(--accent);text-transform:uppercase;',
    '       letter-spacing:0.6px;margin-bottom:3px">El fenómeno</div>',
    '  <div style="font-size:11px;line-height:1.6">' + (w.phenomenon || '') + '</div>',
    '</div>',
    '<div style="margin-bottom:8px">',
    '  <div style="font-size:9px;font-weight:600;color:var(--accent);text-transform:uppercase;',
    '       letter-spacing:0.6px;margin-bottom:3px">Por qué importa</div>',
    '  <div style="font-size:11px;line-height:1.6">' + (w.implication || '') + '</div>',
    '</div>',
    '<div style="margin-bottom:8px">',
    '  <div style="font-size:9px;font-weight:600;color:var(--accent);text-transform:uppercase;',
    '       letter-spacing:0.6px;margin-bottom:3px">Lo que NEVEN hará</div>',
    '  <div style="font-size:11px;line-height:1.6">' + (w.action || '') + '</div>',
    '</div>',
    ref.book ? [
    '<div style="margin-bottom:8px;padding:8px;background:rgba(215,165,56,0.06);border-radius:4px">',
    '  <div style="font-size:9px;font-weight:600;color:var(--accent);text-transform:uppercase;',
    '       letter-spacing:0.6px;margin-bottom:3px">Para profundizar</div>',
    '  <div style="font-size:11px;line-height:1.6;font-style:italic">' + (ref.text || '') + '</div>',
    '  <div style="font-size:10px;color:var(--text-secondary);margin-top:4px">',
    '    📖 ' + ref.book + ' · ' + ref.chapter + ' · ' + ref.pages,
    '  </div>',
    '</div>',
    ].join('') : '',
    w.reflection_question ? [
    '<div style="padding:8px;background:rgba(255,255,255,0.03);border-radius:4px;',
    '     border-left:2px solid rgba(215,165,56,0.4)">',
    '  <div style="font-size:9px;font-weight:600;color:var(--accent);text-transform:uppercase;',
    '       letter-spacing:0.6px;margin-bottom:3px">Para reflexionar</div>',
    '  <div style="font-size:11px;line-height:1.6;font-style:italic">' + w.reflection_question + '</div>',
    '</div>',
    ].join('') : '',
  ].join('\n');
}
```

---

## Fase 5 — Integración con el Tab IA (contexto ontológico)

El Tab IA ya tiene `/api/ai/chat` con inyección de contexto del dataset (`_aiAttachDataset`). Se extiende para incluir contexto ontológico cuando hay una función activa en DataLab.

### Nuevo botón en el Tab IA: "+ Contexto Metodológico"

```javascript
// Nuevo botón en el Tab IA:
document.getElementById('ai-use-method-btn').addEventListener('click', _aiAttachMethodContext);

function _aiAttachMethodContext() {
  // Usar la función activa en DataLab (si hay)
  var card = window._dlCurrentCard || (_dlState && _dlState.selectedCard);
  if (!card) { showToast('Seleccione una función en Data Lab primero'); return; }
  
  fetch(_DL_API + '/api/kg/method/' + card.id)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data.found) { showToast('Esta función no tiene nodo en la ontología todavía'); return; }
      
      var lines = [
        'Método activo: ' + data.method.name,
        'Descripción: ' + data.method.description,
        '',
        'Supuestos requeridos:',
      ];
      (data.assumptions || []).forEach(function(a) {
        lines.push('  - ' + a.name + ': ' + a.definition.substring(0, 100) + '...');
      });
      lines.push('');
      lines.push('Referencia: ' + (data.method.reference || {}).book + 
                 ', ' + (data.method.reference || {}).chapter);
      
      _aiState.context = (_aiState.context ? _aiState.context + '\n\n' : '') + lines.join('\n');
      showToast('✓ Contexto metodológico adjuntado al chat IA');
    });
}
```

**En el servidor** (`_handle_ai_chat`): el contexto inyectado como sistema message se extiende para incluir el persona de la ontología:

```python
# Persona extendida cuando hay contexto metodológico:
sys_msg = {"role": "system", "content": (
    "Eres NEVEN Assistant, un analista econométrico experto. "
    "Combinas el conocimiento de la ontología econométrica (Wooldridge, Hanck, "
    "Brumback, MIT 14.382/14.384/14.387) con el acceso directo a R, Julia y Python "
    "a través de NEVEN. Cuando detectes posibles problemas metodológicos, "
    "siempre cita el libro y capítulo relevante. "
    f"Contexto actual:\n\n{context}\n\n"
    "Responde siempre en español. Usa Markdown para formatear tu respuesta."
)}
```

---

## Fase 6 — Formato de proyecto `.buklo`

**Archivo nuevo:** `NEVEN/ControlPython/startup/buklo_manager.py`

```python
class BukloManager:
    """
    Gestiona la serialización y deserialización del formato .buklo.
    Un .buklo es un ZIP con estructura:
    ├── data/
    │   └── dataset.parquet      # Dataset comprimido (READ_PARQUET en DuckDB)
    ├── project/
    │   ├── CHAT.md              # Historia de interacciones con el LLM
    │   ├── plan.json            # Plan metodológico final aprobado
    │   └── metadata.json        # Versión NEVEN, fecha, perfil usuario
    └── MANIFEST.json            # Versión del formato + checksums
    """
    
    BUKLO_VERSION = "1.0"
    
    def save(self, path: str, db, chat_history: str, plan: dict, metadata: dict):
        """
        Exporta el proyecto actual a un archivo .buklo.
        
        1. Exporta DuckDB dataset a Parquet temporal
        2. Comprime en ZIP
        3. Renombra a .buklo
        """
        
    def load(self, path: str) -> dict:
        """
        Abre un .buklo y retorna su contenido.
        Carga el Parquet en DuckDB.
        
        Returns: {
            "metadata": dict,
            "chat_history": str,
            "plan": dict,
            "columns": [str],
            "n_rows": int
        }
        """
```

**Endpoints nuevos:**

```
POST /api/buklo/save   → guarda el proyecto actual como .buklo
POST /api/buklo/load   → abre un .buklo y restaura el estado
GET  /api/buklo/status → estado del proyecto actual (guardado/no guardado)
```

---

## Orden de implementación recomendado

La integración se implementa en 6 fases incrementales. Cada fase es independiente y entregable.

| Fase | Componente | Esfuerzo estimado | Valor inmediato |
|------|-----------|-------------------|-----------------|
| **1** | `ontology_engine.py` — carga del grafo + índices + consultas básicas | 1 sesión | Motor central listo |
| **2** | Endpoints `GET /api/kg/method/{id}` y `POST /api/kg/profile` | 0.5 sesiones | API disponible |
| **3** | Panel ontológico en Data Lab (`renderOntologyPanel`) | 1 sesión | Usuario ve el método al seleccionar función |
| **4** | Advertencias pedagógicas en resultados (`warning_pedagogy`) | 2 sesiones | El lema cobra vida |
| **5** | Tab IA con contexto ontológico | 0.5 sesiones | Chat IA econométricamente informado |
| **6** | Formato `.buklo` (gestor de proyectos) | 1 sesión | Persistencia de proyectos |

**Total estimado:** 6 sesiones de trabajo

**Orden de prioridad para la tesis:** Fase 1 → Fase 2 → Fase 3 → Fase 4. Las fases 5 y 6 son de alto valor pero no son bloqueantes para la demostración del sistema.

---

## Mapeo function_id → nodo del grafo

El DataLab usa `function_id` como `"RG_OLS"`, `"RG_IV"`, `"PAN_FE"`, etc. El grafo usa IDs como `"method_ols"`, `"method_iv"`, `"method_fixed_effects"`. Se necesita una tabla de mapeo explícita.

**Archivo:** `NEVEN/ControlPython/startup/kg_function_map.json`

```json
{
  "RG_OLS":          "method_ols",
  "RG_MCG":          "method_ols",
  "RG_IV":           "method_iv",
  "RG_2SLS":         "method_iv",
  "PAN_FE":          "method_fixed_effects",
  "PAN_RE":          "method_random_effects",
  "PAN_GMM":         "method_dynamic_panel",
  "CAU_DID":         "method_did",
  "CAU_RDD":         "method_rdd",
  "CAU_IPTW":        "method_iptw",
  "CAU_AIPW":        "method_aipw",
  "CAU_PSM":         "method_ps_matching",
  "CAU_HECKMAN":     "method_heckman",
  "LOG_LOGIT":       "method_logit",
  "LOG_PROBIT":      "method_probit",
  "LOG_TOBIT":       "method_tobit",
  "LOG_POISSON":     "method_poisson",
  "LOG_ORDINAL":     "method_ordinal_logit",
  "LOG_MULTINOMIAL": "method_multinomial_logit",
  "ST_ARIMA":        "method_arima",
  "ST_GARCH":        "method_garch",
  "ST_VAR":          "method_var",
  "ESP_SAR":         "method_sar",
  "ESP_SEM":         "method_sem",
  "ESP_SDM":         "method_sdm",
  "MIT_DOUBLEML":    "method_double_ml",
  "MIT_LASSO":       "method_post_lasso",
  "MIT_LATE":        "method_late_wald",
  "MIT_QR":          "method_quantile_regression"
}
```

Este archivo se actualiza cada vez que se añade una función nueva al DataLab o un nuevo agente a la ontología.

---

## Archivos a crear / modificar

### Archivos nuevos
| Archivo | Descripción |
|---------|-------------|
| `NEVEN/ControlPython/startup/ontology_engine.py` | Motor de conocimiento — clase principal |
| `NEVEN/ControlPython/startup/kg_function_map.json` | Mapeo function_id → method_id del grafo |
| `NEVEN/ControlPython/startup/buklo_manager.py` | Gestor del formato .buklo |

### Archivos modificados
| Archivo | Cambios |
|---------|---------|
| `neven_http_server.py` | +3 endpoints nuevos (kg/method, kg/profile, kg/diagnose), +2 buklo endpoints |
| `datalab_handler.py` | `handle_run()` enriquece slots `warning_pedagogy` con `OntologyEngine` |
| `taskpane.html` | Añadir `#dl-ontology-panel`, botón `+ Contexto Metodológico` en Tab IA |
| `datalab.js` | `selectFunction()` llama `renderOntologyPanel()`, `buildSlotElement` maneja `warning_pedagogy` |

### Archivos sin modificar (reutilizados sin cambios)
- `_parse_slots_from_variable` — el nuevo tipo `warning_pedagogy` pasa por el mismo parser
- `buildSlotElement` — se extiende con un nuevo case, no se modifica el código existente
- `_renderPlotlyJSON`, `renderSlotTable` — sin cambios
- El grafo `graph.jsonl` — solo lectura desde `ontology_engine.py`

---

## Restricción de paths

La ontología vive en `F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS\memory\ontology\graph.jsonl`.
NEVEN corre desde `C:\NEVEN\`.

El `ontology_engine.py` debe buscar el grafo en este orden:
1. `neven-config.json > OntologyPath` (configurable)
2. `F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS\memory\ontology\graph.jsonl` (path del repo)
3. `C:\NEVEN\ontology\graph.jsonl` (path de producción — copiar en deploy)

Para producción, añadir al script de deploy: copiar `graph.jsonl` y `schema.yaml` a `C:\NEVEN\ontology\`.

---

*Documento generado: 2026-08-19. Revisar en cada sesión de implementación.*
