# Plan de Implementación — Agente de Análisis Iterativo

**Fecha:** 2026-08-31  
**Estado:** Diseño aprobado — pendiente de implementación  
**Contexto:** Continuación de la integración NEVEN + Ontología (Fases 1-6 completadas)

---

## Visión

Convertir el Tab IA de NEVEN en un agente de análisis activo que:
1. **Lee los resultados reales** de cada estimación (no solo la estructura del dataset)
2. **Propone correcciones metodológicas** en lenguaje natural con justificación bibliográfica
3. **Ejecuta esas correcciones** con un clic, invocando NEVEN como motor computacional
4. **Registra toda la secuencia** en el `.buklo` como traza auditada del proceso

---

## Componente 1 — Resultados de DataLab como contexto del LLM

### Objetivo
El LLM recibe los coeficientes, p-valores, R², estadísticos de tests y advertencias pedagógicas del último análisis ejecutado. Puede responder sobre **este modelo específico**, no sobre un modelo genérico.

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `TaskPane/datalab.js` | Guardar slots en `window._dlLastSlots` al terminar `runAnalysis()` |
| `TaskPane/taskpane.html` | +botón `+ Resultados` en Tab IA, +función `_aiAttachResults()` |
| `ControlPython/startup/neven_http_server.py` | Extender system message cuando hay contexto de resultados |

---

### Tarea 1.1 — Guardar slots del último análisis (`datalab.js`)

**Punto de inserción:** `runAnalysis()` — justo después de `renderResults(data.slots || [])`.

```javascript
// En runAnalysis(), tras renderResults():
if (data.status === 'ok' && data.slots) {
    window._dlLastSlots      = data.slots;
    window._dlLastFunctionId = _dlState.selectedCard ? _dlState.selectedCard.id : null;
    window._dlLastCard       = _dlState.selectedCard || null;
}
```

**Por qué aquí:** `renderResults` ya recibe los slots. Solo se trata de guardar una referencia en `window` para que el Tab IA pueda accederla.

---

### Tarea 1.2 — Serializar slots a texto estructurado (`taskpane.html`)

**Función nueva:** `_aiAttachResults()`

```javascript
function _aiAttachResults() {
    var slots = window._dlLastSlots;
    if (!slots || !slots.length) {
        showToast('Ejecuta un análisis en Data Lab primero');
        return;
    }

    var card = window._dlLastCard;
    var fnId = window._dlLastFunctionId || 'análisis';
    var lines = [
        '=== RESULTADOS DEL ANÁLISIS ===',
        'Función: ' + (card ? card.name : fnId),
        'ID: ' + fnId,
        ''
    ];

    slots.forEach(function(slot) {
        if (!slot || !slot.name) return;

        // Advertencias pedagógicas (warning_pedagogy)
        if (slot.type === 'warning_pedagogy' && typeof slot.value === 'object') {
            lines.push('⚠ ADVERTENCIA: ' + (slot.value.compact || slot.label));
            return;
        }

        // Tablas (coeficientes, métricas)
        if (slot.type === 'table' && Array.isArray(slot.value)) {
            lines.push('[' + (slot.label || slot.name) + ']');
            var rows = slot.value;
            if (rows.length > 0) {
                var cols = Object.keys(rows[0]);
                lines.push(cols.join(' | '));
                rows.forEach(function(row) {
                    lines.push(cols.map(function(c) {
                        var v = row[c];
                        return v !== null && v !== undefined ? String(v) : '';
                    }).join(' | '));
                });
            }
            lines.push('');
            return;
        }

        // Scalars / métricas individuales
        if (slot.type === 'scalar' && slot.value !== null && slot.value !== undefined) {
            lines.push((slot.label || slot.name) + ': ' + slot.value);
            return;
        }
    });

    var resultsCtx = lines.join('\n').trim();
    _aiState.context = _aiState.context
        ? _aiState.context + '\n\n' + resultsCtx
        : resultsCtx;

    // Actualizar badge
    var ctxCard    = document.getElementById('ai-context-card');
    var ctxSummary = document.getElementById('ai-context-summary');
    if (ctxCard)    ctxCard.style.display = '';
    if (ctxSummary) ctxSummary.textContent =
        (ctxSummary.textContent ? ctxSummary.textContent + ' · ' : '') +
        (card ? card.name.split('(')[0].trim() : fnId);

    showToast('✓ Resultados de "' + (card ? card.name : fnId) + '" adjuntados al chat IA');
}
```

---

### Tarea 1.3 — Botón `+ Resultados` en Tab IA (`taskpane.html`)

**Punto de inserción:** junto a `+ Dataset` y `+ Método` en la toolbar del chat.

```html
<button class="btn btn-secondary" id="ai-use-results-btn"
        title="Incluir resultados del último análisis de Data Lab como contexto">
  + Resultados
</button>
```

**En `initAITab()`:**
```javascript
document.getElementById('ai-use-results-btn').addEventListener('click', _aiAttachResults);
```

---

### Tarea 1.4 — System message extendido para resultados (`neven_http_server.py`)

**En `_handle_ai_chat`** — añadir detección del marcador de resultados:

```python
has_results_context = "=== RESULTADOS DEL ANÁLISIS ===" in context

if has_method_context and has_results_context:
    sys_content = (
        "Eres NEVEN Assistant, un econometrista experto. "
        "Tienes acceso a la estimación real del usuario: coeficientes, "
        "p-valores, tests diagnósticos y advertencias metodológicas. "
        "Responde sobre ESTE modelo específico, no en abstracto. "
        "Si detectas problemas (instrumento débil, heterocedasticidad, "
        "endogeneidad), cita el libro/capítulo relevante y propone la "
        "corrección metodológica concreta. "
        "Cuando sugieras un nuevo análisis, estructúralo en un bloque "
        "```neven-run con el JSON de la llamada. "
        f"Contexto completo:\n\n{context}\n\n"
        "Usa Markdown. Fórmulas con $$...$$. "
        "NUNCA uses \\(...\\) ni \\[...\\]."
    )
```

---

## Componente 2 — Re-cálculos guiados por la discusión (Enfoque A)

### Objetivo
El LLM genera una sugerencia de análisis en JSON estructurado. NEVEN la ejecuta via un endpoint nuevo. Otros servicios externos pueden usar el mismo endpoint para invocar NEVEN programáticamente.

### Schema JSON del análisis programático

```json
{
    "function_id":    "RG_2SLS",
    "language":       "r",
    "column_roles":   {
        "Y": ["lwage"],
        "X": ["educ", "exper"],
        "Z": ["nearc4"]
    },
    "parameters":     {"Escala": false, "Constante": true},
    "filter_clause":  "",
    "source":         "ai_suggestion",
    "context_note":   "Instrumento nearc4 para corregir endogeneidad de educ (Card 1995)"
}
```

**Campos:**
- `function_id`, `language`, `column_roles`, `parameters`, `filter_clause` — idénticos a `/api/datalab/run` (reutilización total)
- `source` — trazabilidad: `"user"` | `"ai_suggestion"` | `"external_api"` | `"script"`
- `context_note` — justificación en texto libre (se guarda en `.buklo`)

---

### Tarea 2.1 — Endpoint `POST /api/ai/run_suggestion` (`neven_http_server.py`)

**Implementación:** wrapper sobre `datalab_handler.handle_run` con validación adicional.

```python
def _handle_ai_run_suggestion(self, body: dict):
    """
    POST /api/ai/run_suggestion — ejecuta un análisis propuesto por el LLM o
    un servicio externo. Reutiliza datalab_handler.handle_run internamente.

    Body: {function_id, language, column_roles, parameters,
           filter_clause, source, context_note}

    Igual que /api/datalab/run pero con campos adicionales de trazabilidad.
    """
    # Validar source
    valid_sources = {"user", "ai_suggestion", "external_api", "script"}
    source = body.get("source", "external_api")
    if source not in valid_sources:
        self._send_error_json(f"source inválido: {source}", 400)
        return

    # Registrar en el log de trazabilidad
    context_note = body.get("context_note", "")
    import logging
    logging.getLogger("neven.api").info(
        f"[run_suggestion] source={source} "
        f"function_id={body.get('function_id','')} "
        f"note={context_note[:80]}"
    )

    # Delegar a handle_run (mismo pipeline completo)
    if not _DATALAB_AVAILABLE:
        self._send_error_json("DataLab no disponible", 503)
        return

    result = _datalab_handler.handle_run(
        body, _config,
        _get_db(), _db_lock,
        self._get_pipe_client
    )

    # Inyectar metadatos de trazabilidad en la respuesta
    result["source"]       = source
    result["context_note"] = context_note

    status_code = 200 if result.get("status") == "ok" else 400
    self._send_json(result, status_code)
```

**En el router POST:**
```python
elif path == 'api/ai/run_suggestion':
    self._handle_ai_run_suggestion(body)
```

---

### Tarea 2.2 — Renderer del bloque `neven-run` en `_renderWithMarked` (`taskpane.html`)

El LLM incluye en su respuesta bloques especiales:

````
```neven-run
{
  "function_id": "RG_2SLS",
  "column_roles": {"Y": ["lwage"], "X": ["educ"], "Z": ["nearc4"]},
  "context_note": "Instrumento nearc4 para corregir endogeneidad"
}
```
````

El renderer los convierte en un card ejecutable en lugar de un bloque de código genérico.

**Post-procesamiento en `_renderWithMarked`** — antes de retornar el HTML:

```javascript
// Detectar y convertir bloques ```neven-run``` a cards ejecutables
html = html.replace(
    /<pre><code class="language-neven-run">([\s\S]+?)<\/code><\/pre>/g,
    function(_, jsonStr) {
        try {
            // marked HTML-encodes el contenido — decodificar
            var decoded = jsonStr
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&quot;/g, '"');
            var suggestion = JSON.parse(decoded);
            return _buildRunSuggestionCard(suggestion);
        } catch(e) {
            return '<pre><code>' + jsonStr + '</code></pre>';
        }
    }
);
```

**Función `_buildRunSuggestionCard(suggestion)`:**

```javascript
function _buildRunSuggestionCard(suggestion) {
    var fnId  = suggestion.function_id || '?';
    var note  = suggestion.context_note || '';
    var dataId = 'neven-run-' + Date.now();

    // Guardar la sugerencia en window para el botón
    window._nevenRunSuggestions = window._nevenRunSuggestions || {};
    window._nevenRunSuggestions[dataId] = suggestion;

    return [
        '<div style="border:1px solid rgba(215,165,56,0.4);border-radius:6px;',
        'background:rgba(215,165,56,0.06);padding:10px 12px;margin:8px 0">',
        '<div style="font-size:9px;font-weight:700;color:var(--accent);',
        'text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px">',
        '⚡ Sugerencia de análisis</div>',
        '<div style="font-size:11px;color:var(--text-primary);margin-bottom:6px">',
        '<strong>' + fnId + '</strong>',
        note ? ' — ' + note : '',
        '</div>',
        '<button onclick="_executeRunSuggestion(\'' + dataId + '\')" ',
        'style="background:var(--accent);color:var(--bg-primary);border:none;',
        'border-radius:4px;padding:5px 14px;font-size:10px;font-weight:700;',
        'cursor:pointer">▶ Ejecutar este análisis</button>',
        '</div>'
    ].join('');
}
```

**Función `_executeRunSuggestion(dataId)`:**

```javascript
function _executeRunSuggestion(dataId) {
    var suggestion = (window._nevenRunSuggestions || {})[dataId];
    if (!suggestion) { showToast('Sugerencia no disponible'); return; }

    suggestion.source = 'ai_suggestion';

    _aiAddMessage('assistant', '⏳ Ejecutando: **' + suggestion.function_id + '**…');

    fetch(API + '/api/ai/run_suggestion', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify(suggestion),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status !== 'ok') {
            _aiAddMessage('error', 'Error al ejecutar: ' + (data.message || 'desconocido'));
            return;
        }

        // Guardar los nuevos slots para el botón + Resultados
        window._dlLastSlots      = data.slots;
        window._dlLastFunctionId = suggestion.function_id;

        // Renderizar los resultados inline en el chat como resumen
        var summary = _buildSlotsSummary(data.slots);
        _aiAddMessage('assistant',
            '✓ **' + suggestion.function_id + '** ejecutado en ' +
            data.execution_time_ms + 'ms\n\n' + summary
        );
    })
    .catch(function(e) { _aiAddMessage('error', 'Error de red: ' + e.message); });
}
```

---

### Tarea 2.3 — Resumen inline de resultados en el chat

**Función `_buildSlotsSummary(slots)`** — versión compacta de los resultados para mostrar en el chat:

```javascript
function _buildSlotsSummary(slots) {
    if (!slots || !slots.length) return '_Sin resultados_';
    var lines = [];
    slots.forEach(function(slot) {
        if (slot.type === 'warning_pedagogy' && typeof slot.value === 'object') {
            lines.push('> ⚠ ' + (slot.value.compact || slot.label));
        } else if (slot.type === 'table' && Array.isArray(slot.value) && slot.tier === 1) {
            lines.push('**' + (slot.label || slot.name) + '**');
            var rows = slot.value.slice(0, 8);  // max 8 filas en el chat
            if (rows.length > 0) {
                var cols = Object.keys(rows[0]);
                lines.push('| ' + cols.join(' | ') + ' |');
                lines.push('| ' + cols.map(function() { return '---'; }).join(' | ') + ' |');
                rows.forEach(function(row) {
                    lines.push('| ' + cols.map(function(c) {
                        return String(row[c] !== null && row[c] !== undefined ? row[c] : '');
                    }).join(' | ') + ' |');
                });
            }
        } else if (slot.type === 'scalar' && slot.tier === 1) {
            lines.push('**' + (slot.label || slot.name) + ':** ' + slot.value);
        }
    });
    return lines.join('\n');
}
```

---

### Tarea 2.4 — Trazabilidad en `.buklo` (extensión futura)

Extender `BukloManager.save()` para aceptar un historial de análisis ejecutados:

```python
# En buklo_manager.py — estructura adicional en project/
_PATH_ANALYSIS_LOG = "project/analysis_log.jsonl"

# Cada análisis ejecutado se registra como:
{
    "timestamp":    "2026-08-31T22:00:00Z",
    "function_id":  "RG_2SLS",
    "source":       "ai_suggestion",
    "context_note": "Instrumento nearc4 para corregir endogeneidad",
    "execution_ms": 1240,
    "n_slots":      5,
    "warnings":     ["assumption_instrument_relevance"]
}
```

---

## Orden de implementación

| Tarea | Componente | Esfuerzo | Valor inmediato |
|-------|-----------|----------|-----------------|
| **1.1** | `_dlLastSlots` en `runAnalysis()` | 5 min | Slots disponibles para el LLM |
| **1.2** | `_aiAttachResults()` en `taskpane.html` | 30 min | LLM ve los coeficientes reales |
| **1.3** | Botón `+ Resultados` en Tab IA | 5 min | UI disponible |
| **1.4** | System message extendido con resultados | 15 min | LLM responde sobre el modelo real |
| **2.1** | Endpoint `POST /api/ai/run_suggestion` | 20 min | API programática funcional |
| **2.2** | Renderer bloque `neven-run` | 45 min | LLM puede proponer análisis ejecutables |
| **2.3** | `_buildSlotsSummary` inline en chat | 20 min | Resultados visibles en el chat |
| **2.4** | Trazabilidad en `.buklo` | 30 min | Auditabilidad del proceso analítico |

**Total estimado: ~3 horas**

**Prioridad:** Tareas 1.1 → 1.3 → 1.2 → 1.4 → 2.1 → 2.2 → 2.3 → 2.4

Las primeras 4 tareas (Componente 1) son independientes del Componente 2 y tienen valor inmediato por sí solas.

---

## Archivos involucrados

### Modificaciones
| Archivo | Tareas |
|---------|--------|
| `TaskPane/datalab.js` | 1.1 |
| `TaskPane/taskpane.html` | 1.2, 1.3, 1.4 parcial, 2.2, 2.3 |
| `ControlPython/startup/neven_http_server.py` | 1.4, 2.1 |

### Sin modificaciones
| Archivo | Por qué |
|---------|---------|
| `datalab_handler.py` | El endpoint nuevo reutiliza `handle_run` sin cambios |
| `ontology_engine.py` | Sin cambios — ya provee el contexto metodológico |
| `buklo_manager.py` | Tarea 2.4 es extensión opcional, no bloqueante |

---

*Documento generado: 2026-08-31. Implementar en la próxima sesión.*
