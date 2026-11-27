"""A-08 (SEC-07): el HTML que producen los motores se inserta solo mediante
NEVENHtmlSandbox (iframe con sandbox sin allow-same-origin). Las pruebas de comportamiento
corren en node (tests/js/html_sandbox_check.js); aqui se vigila que ningun sitio del TaskPane
vuelva a insertar HTML de motor sin la politica y que las salidas legitimas sigan en su sitio."""
import pathlib
import re
import shutil
import subprocess

import pytest

_SRC = pathlib.Path(__file__).resolve().parents[1]
_TP = _SRC / "TaskPane"
_JS_CHECK = _SRC / "tests" / "js" / "html_sandbox_check.js"


def _read(name):
    return (_TP / name).read_text(encoding="utf-8")


def _code_lines(text):
    """Lineas de codigo sin comentarios de linea o de bloque (los comentarios pueden nombrar la politica)."""
    return [(i + 1, l) for i, l in enumerate(text.splitlines()) if not l.strip().startswith(("//", "*", "/*"))]


@pytest.mark.skipif(not shutil.which("node"), reason="node no esta en el PATH")
def test_comportamiento_del_modulo_en_node():
    r = subprocess.run(["node", str(_JS_CHECK)], capture_output=True, timeout=60)
    out = (r.stdout + r.stderr).decode("utf-8", "replace")
    assert r.returncode == 0, out
    assert "todos los casos pasaron" in out


def test_ningun_sitio_concede_allow_same_origin():
    for f in _TP.iterdir():
        if f.suffix in (".js", ".html") and f.name != "neven-docs.html":
            for n, line in _code_lines(f.read_text(encoding="utf-8", errors="replace")):
                assert "allow-same-origin" not in line, f"{f.name}:{n}: {line.strip()}"


def test_la_politica_es_unica_y_sin_same_origin():
    js = _read("html-sandbox.js")
    assert "var SANDBOX = 'allow-scripts allow-downloads';" in js
    # sandbox se fija antes que srcdoc en applyTo
    body = js[js.index("function applyTo"):js.index("function createFrame")]
    assert body.index("'sandbox'") < body.index("'srcdoc'")


@pytest.mark.parametrize("name", ["datalab.js", "chart-gallery.js", "taskpane.js", "taskpane.html"])
def test_los_sitios_no_asignan_srcdoc_ni_escriben_en_iframes_a_mano(name):
    for n, line in _code_lines(_read(name)):
        assert not re.search(r"\.srcdoc\s*=|setAttribute\(\s*['\"]srcdoc", line), f"{name}:{n}: {line.strip()}"
        assert "iframe.contentDocument" not in line, f"{name}:{n}: {line.strip()}"
        assert "iframe.contentWindow.document" not in line, f"{name}:{n}: {line.strip()}"
        assert not re.search(r"iframe\.sandbox\s*=", line), f"{name}:{n}: {line.strip()}"


def test_el_html_de_motor_no_se_escribe_en_ventanas_propias():
    for name in ("taskpane.js", "taskpane.html"):
        for n, line in _code_lines(_read(name)):
            assert "win.document.write(htmlContent)" not in line, f"{name}:{n}"
    assert "NEVENHtmlSandbox.openInWindow(" in _read("taskpane.js")
    assert _read("taskpane.html").count("NEVENHtmlSandbox.openInWindow(") == 2


def test_los_sitios_usan_el_modulo():
    assert "NEVENHtmlSandbox.createFrame(slot.value)" in _read("datalab.js")
    assert "NEVENHtmlSandbox.createFrame(html" in _read("chart-gallery.js")
    tj = _read("taskpane.js")
    assert "NEVENHtmlSandbox.applyTo(iframe, res.html)" in tj
    assert "NEVENHtmlSandbox.applyTo(iframe, htmlContent)" in tj
    assert "NEVENHtmlSandbox.exportImage(iframe, title, 'png')" in tj
    assert "NEVENHtmlSandbox.applyTo(iframe, htmlContent)" in _read("taskpane.html")


def test_html_sandbox_se_carga_antes_que_los_consumidores():
    html = _read("taskpane.html")
    pos = html.index('src="html-sandbox.js')
    for other in ("datalab.js", "taskpane.js", "chart-gallery.js"):
        assert pos < html.index(f'src="{other}'), other


def test_iframe_estatico_de_run_script_tiene_sandbox():
    html = _read("taskpane.html")
    m = re.search(r'<iframe id="script-iframe"[^>]*>', html)
    assert m and 'sandbox="allow-scripts allow-downloads"' in m.group(0)


def test_salidas_legitimas_siguen_en_la_pagina_padre():
    """Plotly interactivo, PNG/SVG, Enviar a Slide y tablas con CSV no pasan por el iframe:
    se reutilizan buildSlotElement y _renderPlotlyJSON tal cual."""
    dl = _read("datalab.js")
    case_html = dl[dl.index("case 'html':"):dl.index("case 'warning_pedagogy':")]
    assert case_html.index("_renderPlotlyJSON(slot.value, slot.name)") < case_html.index("NEVENHtmlSandbox.createFrame")
    plotly = dl[dl.index("function _renderPlotlyJSON"):]
    assert "Plotly.newPlot(divId" in plotly
    assert "Plotly.downloadImage(divId" in plotly and "format: 'png'" in plotly and "format: 'svg'" in plotly
    assert "Enviar a Slide" in plotly
    assert "function renderSlotTable" in dl and ".csv" in dl
    assert "function buildSlotElement" in dl


def test_el_modulo_no_lee_el_token_ni_hace_peticiones():
    js = "\n".join(l for _, l in _code_lines(_read("html-sandbox.js")))
    assert "neven-token" not in js and "X-NEVEN-Token" not in js
    bridge = js[js.index("var BRIDGE"):js.index("function report")]
    assert "fetch" not in bridge and "XMLHttpRequest" not in bridge and "localStorage" not in bridge

def test_los_scripts_modificados_invalidan_la_cache():
    """Los .js se sirven sin cabecera de cache: el ?v= debe cambiar para no mantener allow-same-origin."""
    html = _read("taskpane.html")
    for name in ("datalab.js", "chart-gallery.js", "taskpane.js"):
        assert f'{name}?v=20260927a08' in html, name
