# ===============================================================================
# NEVEN Data Lab — Analisis de Texto desde archivo (PDF, TXT, DOCX)
# Usa las funciones de text_analysis.py ya disponibles en C:\NEVEN\functions\
# ===============================================================================
# FLUJO:
#   1. El usuario escribe la ruta del archivo en el parametro "Ruta_Archivo"
#   2. Python extrae el texto automaticamente (PDF/TXT/DOCX)
#   3. Corre analisis completo y retorna slots
#   No requiere datos previos en DuckDB.
# ===============================================================================

import os
import sys
import json

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

try:
    from text_analysis import (
        _get_text, _tokenize, _sentences,
        AnalizarTexto, FrecuenciaPalabras, Sentimiento, ResumirTexto
    )
    _TA_AVAILABLE = True
except ImportError as _e:
    _TA_AVAILABLE = False
    _TA_ERROR = str(_e)


def TM_TextAnalysis_Studio(df_dict: dict, **params) -> list:
    """
    Analisis de texto desde archivo PDF, TXT o DOCX.

    El usuario proporciona la ruta del archivo en el parametro Ruta_Archivo.
    No requiere dataset cargado en DuckDB.
    """
    if not _TA_AVAILABLE:
        return [{"name": "error", "label": "Error de importacion",
                 "type": "scalar",
                 "value": f"No se pudo importar text_analysis.py: {_TA_ERROR}\n"
                          f"Verifique que el archivo existe en C:\\NEVEN\\functions\\",
                 "tier": 1}]

    # ── Parametros ──────────────────────────────────────────────────────────
    ruta       = str(params.get("Ruta_Archivo", "")).strip().strip('"').strip("'")
    n_resumen  = int(params.get("N_Resumen",   5))
    n_palabras = int(params.get("N_Palabras",  25))
    max_pags   = int(params.get("Max_Paginas", 0))

    if not ruta:
        return [{"name": "ayuda", "label": "Instrucciones",
                 "type": "scalar",
                 "value": (
                     "COMO USAR:\n\n"
                     "1. En el campo 'Ruta del archivo' escriba la ruta completa.\n"
                     "   Ejemplos:\n"
                     "     C:\\Users\\Nombre\\Documents\\informe.pdf\n"
                     "     C:\\Users\\Nombre\\Desktop\\articulo.docx\n"
                     "     C:\\Users\\Nombre\\notas.txt\n\n"
                     "2. Formatos soportados: .pdf  .docx  .doc  .txt\n\n"
                     "3. Haga clic en Ejecutar analisis."
                 ),
                 "tier": 1}]

    # ── Extraer texto del archivo ────────────────────────────────────────────
    ext = os.path.splitext(ruta)[1].lower()

    if not os.path.isfile(ruta):
        return [{"name": "error", "label": "Archivo no encontrado",
                 "type": "scalar",
                 "value": (f"No se encontro el archivo:\n{ruta}\n\n"
                           f"Verifique que la ruta sea correcta y el archivo exista."),
                 "tier": 1}]

    if ext not in ('.pdf', '.docx', '.doc', '.txt', '.md'):
        return [{"name": "error", "label": "Formato no soportado",
                 "type": "scalar",
                 "value": (f"Formato '{ext}' no soportado.\n"
                           f"Use: .pdf  .docx  .doc  .txt"),
                 "tier": 1}]

    try:
        texto = _get_text(ruta)
        # Limpiar saltos de línea internos del texto extraído de PDF.
        # PyPDF2 extrae línea a línea del layout físico, generando
        # palabras partidas ("every\nwhere") y oraciones fragmentadas.
        # Regla: si un \n NO está precedido por '.', '!', '?' o un párrafo
        # vacío (\n\n), se une al texto anterior con un espacio.
        import re as _re
        texto = _re.sub(r'(?<![.!?\n])\n(?!\n)', ' ', texto)  # \n medio-oración → espacio
        texto = _re.sub(r'\n{3,}', '\n\n', texto)             # 3+ \n → párrafo simple
        texto = _re.sub(r' {2,}', ' ', texto)                 # espacios múltiples → uno
        # Aplicar limite de paginas si se especifico y es PDF
        if max_pags > 0 and ext == '.pdf':
            try:
                import PyPDF2
                with open(ruta, "rb") as _f:
                    reader = PyPDF2.PdfReader(_f)
                    n_pages = len(reader.pages)
                    limited = min(max_pags, n_pages)
                    texto = ""
                    for i in range(limited):
                        t = reader.pages[i].extract_text()
                        if t:
                            texto += t + "\n"
                    texto = texto.strip()
                    if n_pages > limited:
                        texto += f"\n\n[NOTA: Analisis limitado a {limited} de {n_pages} paginas. Ajuste 'Max paginas PDF' para procesar mas.]"
            except Exception:
                pass  # Si falla el limite, usar texto completo ya extraido
    except Exception as e:
        return [{"name": "error", "label": "Error al leer archivo",
                 "type": "scalar",
                 "value": f"Error al leer {os.path.basename(ruta)}:\n{e}",
                 "tier": 1}]

    if not texto or not texto.strip():
        return [{"name": "error", "label": "Documento vacio",
                 "type": "scalar",
                 "value": "No se pudo extraer texto del archivo. "
                          "Si es un PDF escaneado (imagen), no es posible extraer texto.",
                 "tier": 1}]

    nombre_archivo = os.path.basename(ruta)

    # ── Analisis ────────────────────────────────────────────────────────────
    from collections import Counter
    words    = _tokenize(texto)
    sents    = _sentences(texto)
    total_w  = len(texto.split())
    unique_w = len(set(words))
    n_sents  = len(sents)
    freq     = Counter(words)
    top_freq = freq.most_common(n_palabras)

    # Estadisticas generales
    stats_table = [
        {"Estadistica": "Archivo",                      "Valor": nombre_archivo},
        {"Estadistica": "Formato",                      "Valor": ext.upper()[1:]},
    ]
    # Agregar conteo de paginas para PDF
    if ext == '.pdf':
        try:
            import PyPDF2
            with open(ruta, "rb") as _f:
                n_pags = len(PyPDF2.PdfReader(_f).pages)
            limite_str = f" (limite: {max_pags})" if max_pags > 0 else " (todas)"
            stats_table.append({"Estadistica": "Paginas en PDF", "Valor": str(n_pags) + limite_str})
        except Exception:
            pass
    stats_table += [
        {"Estadistica": "Total palabras",               "Valor": f"{total_w:,}"},
        {"Estadistica": "Vocabulario (sin stopwords)",  "Valor": f"{unique_w:,}"},
        {"Estadistica": "Oraciones",                    "Valor": f"{n_sents:,}"},
        {"Estadistica": "Promedio pal/oracion",         "Valor": str(total_w // max(1, n_sents))},
        {"Estadistica": "Riqueza lexica (%)",           "Valor": f"{unique_w/max(1,total_w)*100:.1f}%"},
        {"Estadistica": "Caracteres totales",           "Valor": f"{len(texto):,}"},
    ]

    # Sentimiento
    pos_words = set("bueno excelente genial perfecto mejor increible positivo exitoso "
                    "logro avance crecimiento beneficio oportunidad ventaja facil "
                    "rapido eficiente good great excellent amazing best success "
                    "growth benefit opportunity easy fast efficient".split())
    neg_words = set("malo peor terrible horrible negativo fracaso perdida problema "
                    "riesgo dificil lento ineficiente error fallo crisis caida "
                    "reduccion bad worst failure loss problem risk difficult slow "
                    "inefficient crisis decline".split())
    pos_c = sum(1 for w in words if w in pos_words)
    neg_c = sum(1 for w in words if w in neg_words)
    tot   = pos_c + neg_c or 1
    score = (pos_c - neg_c) / tot
    label = "Positivo" if score > 0.2 else "Negativo" if score < -0.2 else "Neutro"

    sent_table = [
        {"Metrica": "Clasificacion", "Valor": label},
        {"Metrica": "Puntuacion (-1 a +1)", "Valor": f"{score:.3f}"},
        {"Metrica": "Palabras positivas", "Valor": str(pos_c)},
        {"Metrica": "Palabras negativas", "Valor": str(neg_c)},
    ]

    # Resumen extractivo — formato HTML
    sent_scores = []
    for s in sents[:300]:
        sw    = _tokenize(s)
        score_s = sum(freq.get(w, 0) for w in sw) / max(1, len(sw))
        sent_scores.append((score_s, s))
    sent_scores.sort(reverse=True)

    items_html = "".join(
        f"<li style='margin-bottom:8px;line-height:1.6'>{s.replace(chr(10), ' ').replace(chr(13), ' ')[:300]}</li>"
        for _, s in sent_scores[:n_resumen]
    )
    resumen_md = (
        "<html><body style='font-family:sans-serif;color:#e0e0e0;"
        "background:#2b2b2b;padding:14px;margin:0'>"
        f"<p style='color:#888;font-size:0.85em;margin:0 0 10px'>"
        f"Top {n_resumen} oraciones por relevancia (TF-IDF)</p>"
        f"<ol style='padding-left:20px;margin:0'>{items_html}</ol>"
        "</body></html>"
    )

    # Frecuencias
    freq_table = [{"Palabra": w, "Frecuencia": c} for w, c in top_freq]

    # Grafico de frecuencias
    html_graf = _build_freq_chart(top_freq[:20], nombre_archivo)

    # WordCloud via Plotly scatter (sin dependencias externas)
    html_wordcloud = _build_wordcloud(top_freq[:40], nombre_archivo)

    # Resumen LLM (opcional — requiere AI configurado en neven-config.json)
    resumen_llm_slot = _build_llm_summary(texto, nombre_archivo)

    # ── Slots ────────────────────────────────────────────────────────────────
    slots = [
        {"name": "estadisticas",  "label": f"Estadisticas — {nombre_archivo}",
         "type": "table",   "value": stats_table,  "tier": 1},
        {"name": "sentimiento",   "label": "Analisis de sentimiento",
         "type": "table",   "value": sent_table,   "tier": 1},
    ]
    # Resumen contextual IA primero (si disponible), luego el extractivo
    if resumen_llm_slot:
        slots.append(resumen_llm_slot)
    slots += [
        {"name": "resumen",       "label": "Resumen extractivo (TF-IDF)",
         "type": "html",    "value": resumen_md,   "tier": 1},
        {"name": "grafico_freq",  "label": "Top palabras mas frecuentes",
         "type": "html",    "value": html_graf,    "tier": 1},
        {"name": "wordcloud",     "label": "Nube de palabras",
         "type": "html",    "value": html_wordcloud, "tier": 1},
        {"name": "frecuencias",   "label": "Tabla de frecuencias completa",
         "type": "table",   "value": freq_table,   "tier": 2},
    ]
    if not resumen_llm_slot:
        # Diagnóstico temporal: muestra el error real del LLM
        slots.append({
            "name":  "llm_error",
            "label": "Diagnostico AI",
            "type":  "scalar",
            "value": _debug_llm(),
            "tier":  2,
        })
    return slots


def _build_freq_chart(freq_data: list, titulo: str) -> str:
    import base64
    try:
        words  = list(reversed([w for w, _ in freq_data]))
        counts = list(reversed([c for _, c in freq_data]))
        traces = [{"type": "bar", "orientation": "h",
                   "x": counts, "y": words,
                   "marker": {"color": "#d7a538"},
                   "hovertemplate": "%{y}: %{x}<extra></extra>"}]
        layout = {
            "title": {"text": f"Frecuencia — {titulo}",
                      "font": {"color": "#e0e0e0", "size": 12}},
            "xaxis": {"title": "Frecuencia", "color": "#888", "gridcolor": "#333"},
            "yaxis": {"color": "#888", "automargin": True},
            "paper_bgcolor": "#373434", "plot_bgcolor": "#373434",
            "font": {"color": "#888"},
            "margin": {"t": 50, "r": 20, "b": 50, "l": 130}
        }
        fig_json = json.dumps({"data": traces, "layout": layout})
        encoded  = base64.b64encode(fig_json.encode("utf-8")).decode("ascii")
        return f'<html><body><neven-plotly>{encoded}</neven-plotly></body></html>'
    except Exception as e:
        return (f'<html><body><p style="color:#888;padding:8px">'
                f'Grafico no disponible: {e}</p></body></html>')


def _build_llm_summary(texto: str, nombre_archivo: str) -> dict | None:
    """
    Llama al LLM configurado en neven-config.json para generar un resumen
    contextual del texto ya extraido y limpiado.

    Retorna un slot dict listo para insertar en la lista de resultados,
    o None si AI no esta configurado, no esta disponible o falla.
    Nunca lanza excepcion — degradacion graceful siempre.
    """
    try:
        import urllib.request
        import urllib.error

        # ── Leer configuracion AI ────────────────────────────────────────
        neven_home = os.environ.get("NEVEN_HOME",
                     os.environ.get("RJ2XCL_HOME", "C:\\NEVEN\\"))
        config_path = os.path.join(neven_home, "neven-config.json")

        if not os.path.isfile(config_path):
            return None

        with open(config_path, "r", encoding="utf-8") as _f:
            full_cfg = json.load(_f)

        ai = full_cfg.get("AI", {})
        if not ai.get("enabled", False):
            return None

        endpoint    = ai.get("endpoint", "http://localhost:1234/v1/chat/completions")
        model       = ai.get("model", "local-model")
        max_tokens  = int(ai.get("maxTokens", 2048))
        temperature = float(ai.get("temperature", 0.3))
        timeout     = int(ai.get("timeout", 60))
        api_key     = ai.get("apiKey", "")
        provider    = ai.get("provider", "lmstudio")

        # ── Preparar texto de entrada (max ~500 palabras para modelo nano) ─
        palabras = texto.split()
        max_palabras = 500
        extracto = " ".join(palabras[:max_palabras])
        if len(palabras) > max_palabras:
            extracto += f" [...texto de {len(palabras):,} palabras en total]"

        # Usar max_tokens conservador pero suficiente para respuesta completa
        max_tokens_llm = min(max_tokens, 800)

        prompt = (
            f"Please read the following document excerpt and provide a clear summary in Spanish. "
            f"Identify the main topics, central arguments, and any relevant conclusions. "
            f"Write 3-5 paragraphs. Respond only in Spanish.\n\n"
            f"Document: {nombre_archivo}\n\n"
            f"{extracto}"
        )

        # ── Construir request HTTP ───────────────────────────────────────
        headers = {"Content-Type": "application/json"}
        if api_key and provider not in ("ollama", "lmstudio"):
            headers["Authorization"] = f"Bearer {api_key}"

        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens_llm,
            "temperature": temperature,
        }, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            contenido = data["choices"][0]["message"]["content"].strip()

        if not contenido:
            contenido = "[El modelo no generó respuesta. Verifique que el modelo esté cargado en LMStudio y tenga suficiente contexto.]"

        # ── Convertir Markdown a HTML ────────────────────────────────────
        import re as _re

        def _md_to_html(md: str) -> str:
            """Convierte Markdown basico a HTML para el iframe del slot."""
            # Encabezados
            md = _re.sub(r'^### (.+)$', r'<h3>\1</h3>', md, flags=_re.MULTILINE)
            md = _re.sub(r'^## (.+)$',  r'<h2>\1</h2>', md, flags=_re.MULTILINE)
            md = _re.sub(r'^# (.+)$',   r'<h1>\1</h1>', md, flags=_re.MULTILINE)
            # Negrita e italica
            md = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
            md = _re.sub(r'\*(.+?)\*',     r'<em>\1</em>', md)
            # Listas con guion o asterisco
            md = _re.sub(r'^[\-\*] (.+)$', r'<li>\1</li>', md, flags=_re.MULTILINE)
            md = _re.sub(r'(<li>.*</li>\n?)+',
                         lambda m: '<ul style="padding-left:18px;margin:8px 0">' + m.group(0) + '</ul>',
                         md, flags=_re.DOTALL)
            # Parrafos: bloques separados por linea vacia
            bloques = _re.split(r'\n{2,}', md.strip())
            partes = []
            for b in bloques:
                b = b.strip()
                if not b:
                    continue
                # Ya es un bloque HTML (h1/h2/h3/ul)
                if _re.match(r'^<(h[123]|ul)', b):
                    partes.append(b)
                else:
                    # Saltos simples dentro del parrafo → espacio
                    b = b.replace('\n', ' ')
                    partes.append(f"<p style='margin:0 0 10px;line-height:1.7'>{b}</p>")
            return "\n".join(partes)

        html_body = _md_to_html(contenido)
        html = (
            "<html><body style='font-family:sans-serif;color:#e0e0e0;"
            "background:#2b2b2b;padding:14px;margin:0;"
            "font-size:13px'>"
            f"<p style='color:#d7a538;font-size:0.8em;margin:0 0 12px'>"
            f"Resumen generado por {model}</p>"
            f"{html_body}"
            "</body></html>"
        )

        return {
            "name":  "resumen_llm",
            "label": f"Resumen contextual (IA)",
            "type":  "html",
            "value": html,
            "tier":  1,
        }

    except Exception as _exc:
        # Retornar slot de error visible en lugar de silenciar
        import traceback as _tb
        return {
            "name":  "resumen_llm",
            "label": "Resumen contextual (IA) — error",
            "type":  "scalar",
            "value": f"{type(_exc).__name__}: {_exc}\n\n{_tb.format_exc()[-800:]}",
            "tier":  1,
        }



def _debug_llm() -> str:
    """Captura el error real que hace fallar _build_llm_summary."""
    import traceback
    try:
        import urllib.request
        neven_home = os.environ.get("NEVEN_HOME", os.environ.get("RJ2XCL_HOME", "C:\\NEVEN\\"))
        config_path = os.path.join(neven_home, "neven-config.json")
        if not os.path.isfile(config_path):
            return f"neven-config.json no encontrado en: {neven_home}"
        with open(config_path, "r", encoding="utf-8") as _f:
            full_cfg = json.load(_f)
        ai = full_cfg.get("AI", {})
        if not ai.get("enabled", False):
            return "AI.enabled=false en neven-config.json"
        endpoint = ai.get("endpoint", "http://localhost:1234/v1/chat/completions")
        model    = ai.get("model", "local-model")
        timeout  = int(ai.get("timeout", 60))
        max_tok  = int(ai.get("maxTokens", 2048))
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "Responde solo: hola"}],
            "max_tokens": 20, "temperature": 0.1,
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            endpoint, data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return (f"OK endpoint={endpoint} model={model} max_tokens={max_tok}\n"
                    f"Respuesta prueba: '{content}'\n"
                    f"-> _build_llm_summary fallo por otra razon (ver traceback si aparece)")
    except Exception as e:
        return f"EXCEPCION: {type(e).__name__}: {e}\n{traceback.format_exc()}"


def _build_wordcloud(freq_data: list, titulo: str) -> str:
    """
    Genera una nube de palabras usando Plotly scatter con texto.
    Las palabras se distribuyen en espiral y su tamaño es proporcional
    a su frecuencia. Sin dependencias externas.
    """
    import base64
    import math
    try:
        if not freq_data:
            return '<html><body><p style="color:#888;padding:8px">Sin datos para nube de palabras</p></body></html>'

        max_freq = freq_data[0][1]
        min_size, max_size = 10, 52

        x_vals, y_vals, texts, sizes, colors = [], [], [], [], []
        palette = ["#d7a538", "#e0c060", "#a87820", "#f0d080", "#c89030",
                   "#b8a060", "#e8b840", "#907020", "#d0c050", "#f8e070"]

        # Distribucion en espiral de Arquimedes
        for i, (word, freq) in enumerate(freq_data):
            angle = i * 2.4          # angulo en radianes (golden angle aprox)
            radius = 1.5 + i * 0.45  # radio creciente
            x_vals.append(round(radius * math.cos(angle), 3))
            y_vals.append(round(radius * math.sin(angle), 3))
            texts.append(word)
            # Tamaño proporcional a frecuencia
            size = min_size + (max_size - min_size) * (freq / max_freq) ** 0.6
            sizes.append(round(size, 1))
            colors.append(palette[i % len(palette)])

        trace = {
            "type": "scatter",
            "mode": "text",
            "x": x_vals,
            "y": y_vals,
            "text": texts,
            "textfont": {"size": sizes, "color": colors},
            "hovertemplate": [f"{w}: {c}<extra></extra>" for w, c in freq_data],
            "hoverinfo": "text",
        }
        layout = {
            "title": {"text": f"Nube de palabras — {titulo}",
                      "font": {"color": "#e0e0e0", "size": 12}},
            "xaxis": {"visible": False, "range": [-max(abs(x) for x in x_vals) * 1.2,
                                                   max(abs(x) for x in x_vals) * 1.2]},
            "yaxis": {"visible": False, "range": [-max(abs(y) for y in y_vals) * 1.2,
                                                   max(abs(y) for y in y_vals) * 1.2],
                      "scaleanchor": "x"},
            "paper_bgcolor": "#373434",
            "plot_bgcolor": "#373434",
            "margin": {"t": 40, "r": 10, "b": 10, "l": 10},
            "showlegend": False,
        }
        fig_json = json.dumps({"data": [trace], "layout": layout})
        encoded = base64.b64encode(fig_json.encode("utf-8")).decode("ascii")
        return f'<html><body><neven-plotly>{encoded}</neven-plotly></body></html>'
    except Exception as e:
        return (f'<html><body><p style="color:#888;padding:8px">'
                f'Nube de palabras no disponible: {e}</p></body></html>')
