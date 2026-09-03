# Plan de Implementación — Historial de Modelos

**Fecha:** 2026-09-01  
**Estado:** Diseño aprobado — pendiente de implementación  
**Contexto:** Extensión del Agente de Análisis Iterativo (PLAN_AGENTE_ANALISIS.md)

---

## Visión

Cada modelo estimado durante una sesión de trabajo se acumula en un historial etiquetado. El botón `+ Resultados` pasa **todos los modelos** al LLM, permitiendo comparaciones como:

> *"El coeficiente de `educ` era 0.092 en OLS (Modelo 1) y subió a 0.262 en 2SLS (Modelo 3) — la endogeneidad subestimaba el retorno a la educación en un 65%."*

El historial se guarda en el archivo `.buklo` como `project/analysis_log.jsonl` — trazabilidad auditada del proceso analítico.

---

## Estructura del historial en memoria (JavaScript)

```javascript
window._dlModelHistory = [
  {
    id:           1,
    label:        "Modelo 1",
    function_id:  "RG_Lineal",
    timestamp:    "2026-09-01T22:00:00Z",
    source:       "user",           // "user" | "ai_suggestion"
    context_note: "",
    column_roles: {"Y":["lwage"],"X":["educ","exper"]},
    parameters:   {"Escala":false},
    slots:        [...],            // slots completos
    metrics_text: "..."             // texto serializado de métricas (para LLM)
  },
  {
    id:           2,
    label:        "Modelo 2",
    function_id:  "RG_2SLS",
    source:       "ai_suggestion",
    context_note: "Corregir endogeneidad de educ con nearc4",
    column_roles: {"Y":["lwage"],"Endo":["educ"],"Exo":["exper"],"Instru":["nearc4"]},
    ...
  }
]
```

---

## Estructura en `.buklo`

```
mi_proyecto.buklo (ZIP)
├── MANIFEST.json
├── data/
│   └── dataset.parquet
└── project/
    ├── CHAT.md
    ├── plan.json
    ├── metadata.json
    └── analysis_log.jsonl       ← NUEVO (una línea JSON por modelo)
```

Cada línea de `analysis_log.jsonl` es un modelo compacto (sin los slots completos):

```json
{"id":1,"label":"Modelo 1","function_id":"RG_Lineal","timestamp":"...","source":"user","context_note":"","column_roles":{"Y":["lwage"],"X":["educ","exper"]},"metrics":{"R_cuadrado":0.316,"AIC":637.1},"n_slots":6}
{"id":2,"label":"Modelo 2","function_id":"RG_2SLS","timestamp":"...","source":"ai_suggestion","context_note":"Corregir endogeneidad de educ","column_roles":{"Y":["lwage"],"Endo":["educ"],"Exo":["exper"],"Instru":["nearc4"]},"metrics":{"R_cuadrado":0.189,"sigma":0.406},"n_slots":5}
```

Formato JSONL porque es append-only — no requiere reescribir el archivo para añadir un modelo.

---

## Tareas de implementación

### Tarea 1 — Acumular modelos en `_dlModelHistory` (datalab.js + taskpane.html)

**Hay dos puntos donde se guarda `_dlLastSlots` — ambos deben acumular también en el historial.**

**Punto A — `datalab.js` línea 1313** (análisis ejecutado por el usuario desde el DataLab):

```javascript
// Reemplazar:
window._dlLastSlots      = data.slots || [];
window._dlLastFunctionId = _dlState.selectedCard ? _dlState.selectedCard.id : null;
window._dlLastCard       = _dlState.selectedCard || null;

// Por:
window._dlLastSlots      = data.slots || [];
window._dlLastFunctionId = _dlState.selectedCard ? _dlState.selectedCard.id : null;
window._dlLastCard       = _dlState.selectedCard || null;
// Acumular en historial
_dlAddToHistory({
    function_id:  window._dlLastFunctionId,
    source:       'user',
    context_note: '',
    column_roles: Object.assign({}, _dlState.columnRoles || {}),
    parameters:   Object.assign({}, _dlState.parameters  || {}),
    slots:        data.slots || []
});
```

**Punto B — `taskpane.html` línea 2767** (análisis ejecutado desde el chat via `_executeRunSuggestion`):

```javascript
// Reemplazar:
window._dlLastSlots      = data.slots || [];
window._dlLastFunctionId = suggestion.function_id || null;
window._dlLastCard       = null;

// Por:
window._dlLastSlots      = data.slots || [];
window._dlLastFunctionId = suggestion.function_id || null;
window._dlLastCard       = null;
// Acumular en historial
_dlAddToHistory({
    function_id:  suggestion.function_id || 'unknown',
    source:       suggestion.source       || 'ai_suggestion',
    context_note: suggestion.context_note || '',
    column_roles: suggestion.column_roles || {},
    parameters:   suggestion.parameters   || {},
    slots:        data.slots || []
});
```

**Función `_dlAddToHistory(entry)` — añadir en `taskpane.html`:**

```javascript
function _dlAddToHistory(entry) {
    window._dlModelHistory = window._dlModelHistory || [];
    var id = window._dlModelHistory.length + 1;

    // Extraer métricas compactas de los slots (para el log y el LLM)
    var metrics = {};
    var metrics_lines = [];
    (entry.slots || []).forEach(function(slot) {
        if (slot.type === 'scalar' && slot.name === 'metricas' ||
            (slot.type === 'scalar' && (slot.tier === 1 || slot.tier === '1'))) {
            // Guardar texto de métricas para el LLM
            if (typeof slot.value === 'string' && slot.value.length < 500) {
                metrics_lines.push(slot.value);
            }
        }
    });

    window._dlModelHistory.push({
        id:           id,
        label:        'Modelo ' + id,
        function_id:  entry.function_id,
        timestamp:    new Date().toISOString(),
        source:       entry.source       || 'user',
        context_note: entry.context_note || '',
        column_roles: entry.column_roles || {},
        parameters:   entry.parameters   || {},
        slots:        entry.slots        || [],
        metrics_text: metrics_lines.join('\n')
    });
}
```

**Reinicio del historial cuando se carga un nuevo dataset** — en `_loadFromContent()` en `taskpane.html`:

```javascript
// Al inicio de _loadFromContent, añadir:
window._dlModelHistory   = [];   // nuevo dataset = nueva sesión de modelos
window._dlLastSlots      = [];
window._dlLastFunctionId = null;
window._dlLastCard       = null;
```

---

### Tarea 2 — Actualizar `_aiAttachResults()` para serializar el historial completo

**Punto de inserción:** reemplazar la función completa en `taskpane.html`.

```javascript
function _aiAttachResults() {
    var history = window._dlModelHistory || [];
    // Fallback: si no hay historial pero hay _dlLastSlots (compatibilidad)
    if (!history.length && window._dlLastSlots && window._dlLastSlots.length) {
        // Construir entrada de historial on-the-fly para el modelo actual
        _dlAddToHistory({
            function_id:  window._dlLastFunctionId || 'análisis',
            source:       'user',
            context_note: '',
            column_roles: {},
            parameters:   {},
            slots:        window._dlLastSlots
        });
        history = window._dlModelHistory || [];
    }
    if (!history.length) {
        showToast('Ejecuta un análisis en Data Lab primero');
        return;
    }

    var lines = ['=== HISTORIAL DE MODELOS ===', ''];

    history.forEach(function(model) {
        lines.push('--- ' + model.label + ': ' + model.function_id + ' ---');
        if (model.source === 'ai_suggestion' && model.context_note) {
            lines.push('Motivación: ' + model.context_note);
        }
        // Especificación
        var roles = Object.keys(model.column_roles || {}).map(function(k) {
            var cols = model.column_roles[k];
            return k + ': [' + (Array.isArray(cols) ? cols.join(', ') : cols) + ']';
        }).join(' | ');
        if (roles) lines.push('Especificación: ' + roles);

        // Métricas y coeficientes principales
        var slots = model.slots || [];
        slots.forEach(function(slot) {
            if (!slot) return;
            if (slot.type === 'warning_pedagogy') {
                var c = (typeof slot.value === 'object' && slot.value)
                    ? (slot.value.compact || slot.label) : slot.label;
                lines.push('⚠ ' + c);
                return;
            }
            if (slot.type === 'scalar' && (slot.tier === 1 || slot.tier === '1')) {
                var val = slot.value;
                if (val !== null && val !== undefined && String(val).length < 300) {
                    lines.push((slot.label || slot.name) + ':\n' + val);
                }
            }
        });
        lines.push('');
    });

    // Incluir columnas del dataset activo
    if (window._dlState && window._dlState.datasetColumns && window._dlState.datasetColumns.length > 0) {
        var allCols = window._dlState.datasetColumns.map(function(c) {
            return typeof c === 'object' ? c.name : c;
        });
        lines.push('Columnas disponibles en el dataset: ' + allCols.join(', '));
        lines.push('IMPORTANTE: usa EXACTAMENTE estos nombres de columna en cualquier sugerencia.');
        lines.push('');
    }

    var ctx = lines.join('\n').trim();
    _aiState.context = _aiState.context ? _aiState.context + '\n\n' + ctx : ctx;

    var ctxCard    = document.getElementById('ai-context-card');
    var ctxSummary = document.getElementById('ai-context-summary');
    if (ctxCard)    ctxCard.style.display = '';
    if (ctxSummary) ctxSummary.textContent =
        history.length + ' modelo' + (history.length > 1 ? 's' : '') + ' en historial';

    showToast('✓ Historial de ' + history.length + ' modelo(s) adjuntado al chat IA');
}
```

---

### Tarea 3 — Añadir `has_history_context` en `neven_http_server.py`

**En `_handle_ai_chat`**, añadir detección del historial y persona orientada a comparación:

```python
has_history_context = "=== HISTORIAL DE MODELOS ===" in context

if has_history_context:
    sys_content = (
        "Eres NEVEN Assistant, un econometrista experto. "
        "Tienes acceso al historial completo de modelos estimados en esta sesión. "
        "Puedes comparar especificaciones, coeficientes y métricas entre modelos. "
        "Cuando compares, cita los números reales de cada modelo y lo que implican. "
        "Si hay un modelo OLS y uno 2SLS, explica qué revela la diferencia sobre endogeneidad. "
        + _run_hint +
        f"Historial de modelos:\n\n{context}\n\n"
        + _fmt
    )
```

**Nota:** `has_history_context` tiene precedencia sobre `has_results_context` — si hay historial, se usa esa persona.

---

### Tarea 4 — Extender `buklo_manager.py` para `analysis_log.jsonl`

**En `buklo_manager.py`:**

```python
_PATH_ANALYSIS_LOG = "project/analysis_log.jsonl"

# En save(): añadir el log al ZIP
def save(self, path, db, db_lock, chat_history="", plan={}, metadata={},
         analysis_log=None):   # ← nuevo parámetro
    ...
    # Serializar analysis_log como JSONL
    log_content = ""
    if analysis_log:
        import json as _json
        log_lines = []
        for entry in analysis_log:
            # Guardar solo los campos compactos (sin slots completos)
            compact = {
                "id":           entry.get("id"),
                "label":        entry.get("label"),
                "function_id":  entry.get("function_id"),
                "timestamp":    entry.get("timestamp"),
                "source":       entry.get("source"),
                "context_note": entry.get("context_note", ""),
                "column_roles": entry.get("column_roles", {}),
                "n_slots":      len(entry.get("slots", [])),
                "metrics_text": entry.get("metrics_text", "")[:500],
            }
            log_lines.append(_json.dumps(compact, ensure_ascii=False))
        log_content = "\n".join(log_lines)
    zf.writestr(_PATH_ANALYSIS_LOG, log_content.encode("utf-8"))

# En load(): retornar analysis_log como lista
def _do_load(self, ...):
    ...
    analysis_log = []
    if _PATH_ANALYSIS_LOG in names:
        try:
            log_text = zf.read(_PATH_ANALYSIS_LOG).decode("utf-8")
            for line in log_text.strip().split("\n"):
                if line.strip():
                    analysis_log.append(json.loads(line))
        except Exception:
            pass
    
    return {
        ...
        "analysis_log": analysis_log,
        ...
    }
```

**En `taskpane.html`** — al abrir un `.buklo`, restaurar el historial:

```javascript
// En _bukloLoadFromPath(), tras data.status === 'ok':
if (data.analysis_log && data.analysis_log.length > 0) {
    // Restaurar el historial sin los slots completos (solo metadatos)
    window._dlModelHistory = data.analysis_log.map(function(entry) {
        return Object.assign({slots: []}, entry);
    });
    showToast('✓ Historial de ' + data.analysis_log.length + ' modelo(s) restaurado');
}
```

**En `_handle_buklo_save`** (`neven_http_server.py`) — leer el historial del body:

```python
# El frontend envía el historial serializado
analysis_log = body.get("analysis_log", [])
result = mgr.save(..., analysis_log=analysis_log)
```

**En `btn-buklo-save`** (`taskpane.html`) — incluir el historial al guardar:

```javascript
// Añadir al body del POST /api/buklo/save:
analysis_log: (window._dlModelHistory || []).map(function(m) {
    return {
        id: m.id, label: m.label, function_id: m.function_id,
        timestamp: m.timestamp, source: m.source,
        context_note: m.context_note, column_roles: m.column_roles,
        n_slots: (m.slots||[]).length, metrics_text: m.metrics_text || ''
    };
})
```

---

## Orden de implementación

| Tarea | Archivo(s) | Esfuerzo | Dependencia |
|-------|-----------|----------|-------------|
| **1** | `datalab.js` + `taskpane.html` | 30 min | ninguna |
| **2** | `taskpane.html` | 20 min | depende de Tarea 1 |
| **3** | `neven_http_server.py` | 15 min | depende de Tarea 2 |
| **4** | `buklo_manager.py` + `taskpane.html` | 30 min | depende de Tarea 1 |

**Total estimado: ~95 minutos**

**Prioridad:** Tareas 1→2→3 en una sola sesión. Tarea 4 se puede hacer en la misma sesión o en la siguiente.

---

## Archivos a modificar

| Archivo | Tareas |
|---------|--------|
| `TaskPane/datalab.js` | 1A |
| `TaskPane/taskpane.html` | 1B, 2, 4 (parcial) |
| `ControlPython/startup/neven_http_server.py` | 3, 4 (parcial) |
| `ControlPython/startup/buklo_manager.py` | 4 |

## Archivos sin modificar

| Archivo | Por qué |
|---------|---------|
| `datalab_handler.py` | El pipeline R no cambia |
| `ontology_engine.py` | Sin cambios |
| `*.Studio.R` | Sin cambios |

---

*Documento generado: 2026-09-01. Implementar en la próxima sesión comenzando por Tarea 1.*
