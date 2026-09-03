# Plan de Implementación — Exportación de Informe Analítico

**Fecha:** 2026-09-01  
**Estado:** Diseño aprobado — pendiente de implementación  
**Dependencia:** PLAN_HISTORIAL_MODELOS.md (el historial debe existir primero)

---

## Visión

Al finalizar su sesión de trabajo, el usuario puede exportar un **informe analítico completo** que narra el proceso: qué se estimó, por qué se modificó, qué se encontró y qué se concluyó. El informe se genera automáticamente a partir del historial de modelos y la conversación con el agente.

El informe se almacena en el archivo `.buklo` como registro auditado del proceso.

---

## Lógica de exportación en cascada

NEVEN detecta las herramientas disponibles y usa la mejor opción:

```
¿Quarto instalado?
    SÍ → genera report.qmd → renderiza a report.pdf (Quarto)
    NO →
        ¿pdflatex o xelatex disponible?
            SÍ → genera report.tex → compila a report.pdf (LaTeX)
            NO → genera report.tex solo (usuario compila en Overleaf u otro)
```

**El usuario siempre recibe algo útil.** La calidad del output escala con las herramientas disponibles pero nunca falla.

---

## Estructura del informe generado

```latex
% report.tex / report.qmd

1. Introducción
   - Pregunta de investigación (de los primeros mensajes del CHAT.md)
   - Dataset: nombre, N observaciones, variables principales

2. Estrategia metodológica
   Para cada modelo en analysis_log:
   - Especificación (Y ~ X | instrumentos si aplica)
   - Tabla de resultados (tabla_cientifica en texto plano dentro de verbatim)
   - Diagnósticos y advertencias detectadas
   - Motivación del cambio al siguiente modelo (context_note del historial)

3. Modelo final seleccionado
   - Especificación y justificación
   - Tabla de coeficientes completa
   - Métricas de ajuste
   - Interpretación econométrica

4. Conclusiones
   - Respuesta a la pregunta de investigación
   - Limitaciones reconocidas durante el análisis

Apéndice A — Historial completo de modelos
Apéndice B — Extractos de la discusión con el agente
```

---

## Tareas de implementación

### Tarea 1 — Detectar herramientas disponibles en el servidor

**Archivo:** `neven_http_server.py`  
**Nuevo endpoint:** `GET /api/export/capabilities`

```python
def _handle_export_capabilities(self):
    """Detecta qué herramientas de exportación están disponibles."""
    import shutil, subprocess

    # Quarto
    quarto = shutil.which("quarto")
    quarto_version = None
    if quarto:
        try:
            r = subprocess.run([quarto, "--version"],
                               capture_output=True, text=True, timeout=5)
            quarto_version = r.stdout.strip()
        except Exception:
            quarto = None

    # pdflatex / xelatex
    pdflatex  = shutil.which("pdflatex")
    xelatex   = shutil.which("xelatex")
    latex_bin = xelatex or pdflatex  # xelatex preferido (mejor soporte UTF-8)

    # Mejor opción disponible
    if quarto:
        best = "quarto"
    elif latex_bin:
        best = "latex"
    else:
        best = "tex_only"

    self._send_json({
        "status":          "ok",
        "best":            best,
        "quarto":          bool(quarto),
        "quarto_version":  quarto_version,
        "latex":           bool(latex_bin),
        "latex_bin":       latex_bin,
    })
```

---

### Tarea 2 — Generar el contenido del informe via LLM

**El LLM genera el documento** — no código hardcodeado. Esto garantiza narrativa coherente.

**Nuevo endpoint:** `POST /api/export/generate`

```python
def _handle_export_generate(self, body: dict):
    """
    Genera el contenido del informe usando el LLM.
    
    Body: {
        format:         "qmd" | "tex"
        analysis_log:   [...] 
        chat_history:   "..."
        dataset_info:   {name, n_rows, n_cols, columns}
        title:          "Análisis de Regresión — wage1"  (opcional)
    }
    
    Retorna: { status, content: str, format: str }
    """
```

**System prompt para generación del informe:**

```python
system_prompt = f"""Eres un asistente académico especializado en econometría.
Genera un informe técnico en formato {fmt} ({"Quarto Markdown" if fmt=="qmd" else "LaTeX"})
que documente el siguiente análisis econométrico.

El informe debe:
1. Narrar el proceso analítico en orden cronológico
2. Explicar la motivación de cada cambio de especificación
3. Presentar los resultados principales en tablas verbatim
4. Interpretar los hallazgos en términos económicos
5. Incluir las advertencias metodológicas detectadas

Historial de modelos:
{serialize_log(analysis_log)}

Extracto de la discusión con el agente:
{chat_summary}

Dataset: {dataset_info['name']} — {dataset_info['n_rows']} obs × {dataset_info['n_cols']} vars

{"Usa sintaxis Quarto/R Markdown válida." if fmt=="qmd" else "Usa LaTeX estándar. Usa paquetes: geometry, booktabs, hyperref, inputenc, fontenc. Usa verbatim para las tablas de resultados."}
Idioma: español.
"""
```

---

### Tarea 3 — Compilar a PDF

**Archivo:** `neven_http_server.py`  
**Nuevo endpoint:** `POST /api/export/compile`

```python
def _handle_export_compile(self, body: dict):
    """
    Compila el contenido generado a PDF.
    
    Body: {
        content:  str  (contenido .tex o .qmd)
        format:   "tex" | "qmd"
        filename: "report"
    }
    
    Retorna: { status, pdf_path: str, log: str }
    """
    import tempfile, subprocess, shutil, os

    fmt      = body.get("format", "tex")
    content  = body.get("content", "")
    filename = body.get("filename", "report")
    tmp_dir  = tempfile.mkdtemp(prefix="neven_export_")

    try:
        if fmt == "qmd":
            qmd_path = os.path.join(tmp_dir, filename + ".qmd")
            pdf_path = os.path.join(tmp_dir, filename + ".pdf")
            with open(qmd_path, "w", encoding="utf-8") as f:
                f.write(content)
            result = subprocess.run(
                ["quarto", "render", qmd_path, "--to", "pdf"],
                capture_output=True, text=True, timeout=120, cwd=tmp_dir
            )
        else:  # tex
            tex_path = os.path.join(tmp_dir, filename + ".tex")
            pdf_path = os.path.join(tmp_dir, filename + ".pdf")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(content)
            latex_bin = shutil.which("xelatex") or shutil.which("pdflatex")
            # Dos pasadas para referencias cruzadas
            for _ in range(2):
                result = subprocess.run(
                    [latex_bin, "-interaction=nonstopmode",
                     "-output-directory", tmp_dir, tex_path],
                    capture_output=True, text=True, timeout=120, cwd=tmp_dir
                )

        if os.path.isfile(pdf_path):
            # Leer el PDF y retornarlo como base64
            import base64
            with open(pdf_path, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
            self._send_json({
                "status":   "ok",
                "pdf_b64":  pdf_b64,
                "log":      result.stdout[-2000:] if result else ""
            })
        else:
            self._send_json({
                "status":  "error",
                "message": "La compilación no generó PDF",
                "log":     result.stderr[-2000:] if result else ""
            })
    except Exception as exc:
        self._send_json({"status": "error", "message": str(exc)})
    finally:
        import shutil as _sh
        _sh.rmtree(tmp_dir, ignore_errors=True)
```

---

### Tarea 4 — UI: botón "Finalizar y exportar" en Data Studio

**Archivo:** `taskpane.html`

**Botón en la card de Proyecto (junto a 💾 y 📂):**

```html
<button class="btn btn-secondary" id="btn-export-report"
        title="Generar informe del análisis y guardar en el proyecto">
  📄 Exportar informe
</button>
```

**Flujo JS `_exportReport()`:**

```javascript
async function _exportReport() {
    // 1. Verificar que hay historial
    var history = window._dlModelHistory || [];
    if (!history.length) {
        showToast('Ejecuta al menos un análisis antes de exportar'); return;
    }

    var btn = document.getElementById('btn-export-report');
    btn.disabled = true; btn.textContent = '⏳ Generando...';

    try {
        // 2. Detectar capacidades
        var caps = await fetch(API + '/api/export/capabilities').then(r => r.json());

        // 3. Elegir formato
        var fmt = caps.best === 'quarto' ? 'qmd' : 'tex';

        // 4. Generar contenido via LLM
        var gen = await fetch(API + '/api/export/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                format:       fmt,
                analysis_log: history.map(function(m) {
                    return {id:m.id, label:m.label, function_id:m.function_id,
                            source:m.source, context_note:m.context_note,
                            column_roles:m.column_roles, metrics_text:m.metrics_text};
                }),
                chat_history: typeof _aiState !== 'undefined'
                    ? _aiState.messages.slice(0,20)
                        .map(function(m){return m.role+': '+m.content.substring(0,200)}).join('\n')
                    : '',
                dataset_info: {
                    name:    document.getElementById('data-info').textContent || 'dataset',
                    n_rows:  (window._dlState && window._dlState.datasetColumns)
                             ? window._dlState.datasetColumns.length : 0,
                    columns: (window._dlState && window._dlState.datasetColumns || [])
                             .map(function(c){ return typeof c==='object'?c.name:c; })
                }
            })
        }).then(r => r.json());

        if (gen.status !== 'ok') throw new Error(gen.message);

        btn.textContent = '⏳ Compilando PDF...';

        // 5. Compilar a PDF (si es posible)
        var compiled = null;
        if (caps.best !== 'tex_only') {
            compiled = await fetch(API + '/api/export/compile', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: gen.content, format: fmt, filename: 'report'})
            }).then(r => r.json());
        }

        // 6. Guardar en el .buklo actual (si hay proyecto guardado)
        // El contenido .tex/.qmd y el PDF (si existe) se incluyen en el próximo save

        window._exportedReport = {
            format:  fmt,
            content: gen.content,
            pdf_b64: compiled && compiled.status === 'ok' ? compiled.pdf_b64 : null
        };

        // 7. Ofrecer descarga del PDF o del .tex
        if (window._exportedReport.pdf_b64) {
            _downloadBase64('report.pdf', 'application/pdf', window._exportedReport.pdf_b64);
            showToast('✓ Informe PDF generado y descargado');
        } else {
            _downloadText('report.' + fmt, gen.content);
            showToast('✓ Informe .' + fmt + ' generado (sin compilador PDF disponible)');
        }

    } catch(e) {
        showToast('✗ Error al exportar: ' + e.message);
    } finally {
        btn.disabled = false; btn.textContent = '📄 Exportar informe';
    }
}

function _downloadBase64(filename, mime, b64) {
    var a = document.createElement('a');
    a.href = 'data:' + mime + ';base64,' + b64;
    a.download = filename;
    a.click();
}

function _downloadText(filename, text) {
    var blob = new Blob([text], {type: 'text/plain;charset=utf-8'});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
}
```

---

### Tarea 5 — Integrar el informe en el `.buklo`

**Extensión de `buklo_manager.py`:**

```python
_PATH_REPORT_TEX = "project/report.tex"
_PATH_REPORT_QMD = "project/report.qmd"
_PATH_REPORT_PDF = "project/report.pdf"

# En save(): incluir el informe si existe
if report_content:
    fmt = report_format or "tex"
    path_key = _PATH_REPORT_QMD if fmt == "qmd" else _PATH_REPORT_TEX
    zf.writestr(path_key, report_content.encode("utf-8"))
if report_pdf_bytes:
    zf.write_bytes(_PATH_REPORT_PDF, report_pdf_bytes)
```

**Estructura final del `.buklo`:**

```
mi_proyecto.buklo (ZIP)
├── MANIFEST.json
├── data/
│   └── dataset.parquet
└── project/
    ├── CHAT.md
    ├── plan.json
    ├── metadata.json
    ├── analysis_log.jsonl     ← historial de modelos
    ├── report.tex             ← informe en LaTeX (siempre)
    ├── report.qmd             ← informe en Quarto (si disponible)
    └── report.pdf             ← PDF compilado (si compilador disponible)
```

---

## Orden de implementación

| Tarea | Archivo | Esfuerzo | Dependencia |
|-------|---------|----------|-------------|
| **1** | `neven_http_server.py` | 20 min | PLAN_HISTORIAL_MODELOS completo |
| **2** | `neven_http_server.py` | 30 min | depende de Tarea 1 |
| **3** | `neven_http_server.py` | 30 min | depende de Tarea 2 |
| **4** | `taskpane.html` | 45 min | depende de Tarea 2 + 3 |
| **5** | `buklo_manager.py` + `taskpane.html` | 20 min | depende de Tarea 4 |

**Total estimado: ~2.5 horas**

**Prerrequisito:** PLAN_HISTORIAL_MODELOS.md implementado.

---

## Nota sobre el LLM como generador del informe

El LLM genera el contenido narrativo — no código hardcodeado. Ventajas:
- La narrativa es coherente con el análisis específico del usuario
- Se adapta automáticamente al número y tipo de modelos
- Puede incorporar el razonamiento de la discusión del chat
- No requiere templates fijos que se desactualizan

El servidor solo orquesta: prepara el contexto, llama al LLM, recibe el `.tex`/`.qmd`, compila. El LLM hace el trabajo intelectual de redacción.

---

*Documento generado: 2026-09-01.*
