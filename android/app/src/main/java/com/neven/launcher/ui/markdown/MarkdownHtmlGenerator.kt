package com.neven.launcher.ui.markdown

import android.content.Context
import androidx.core.content.ContextCompat
import com.neven.launcher.R

/**
 * Generador de HTML con Markdown y KaTeX para notificaciones cientificas
 * Los scripts se embeben inline para funcionar en WebView overlay - 100% offline
 */
object MarkdownHtmlGenerator {
    
    data class PopupColors(
        val textColor: String = "#1A1A1A",
        val accentColor: String = "#C9A227",
        val backgroundColor: String = "#FAFAF8"
    )
    
    fun getColorsFromContext(context: Context): PopupColors {
        return try {
            val textColor = ContextCompat.getColor(context, R.color.scientific_text)
            val accentColor = ContextCompat.getColor(context, R.color.scientific_accent)
            PopupColors(
                textColor = colorIntToHex(textColor),
                accentColor = colorIntToHex(accentColor)
            )
        } catch (e: Exception) {
            PopupColors()
        }
    }
    
    fun colorIntToHex(color: Int): String {
        val r = (color shr 16) and 0xFF
        val g = (color shr 8) and 0xFF
        val b = color and 0xFF
        return String.format("#%02X%02X%02X", r, g, b)
    }
    
    /**
     * Genera HTML con KaTeX INLINE para renderizar LaTeX
     * IMPORTANTE: Los scripts se embeben directamente en el HTML
     * porque WebView en overlay no puede cargar desde file:///android_asset/
     */
    fun generateHtmlForPopup(
        markdown: String,
        textColor: String = "#1A1A1A",
        accentColor: String = "#C9A227",
        @Suppress("UNUSED_PARAMETER") maxLines: Int = 0
    ): String {
        // Verificar que KaTeX este cargado
        if (!KaTeXAssetLoader.isLoaded()) {
            // Fallback sin KaTeX
            return generateFallbackHtml(markdown, textColor)
        }
        
        val escapedMarkdown = escapeForJs(markdown)
        val css = buildCss(textColor, accentColor)
        val js = buildJs(escapedMarkdown)
        
        // Obtener scripts inline desde el loader
        val katexCss = KaTeXAssetLoader.getKatexCss()
        val markedJs = KaTeXAssetLoader.getMarkedJs()
        val katexJs = KaTeXAssetLoader.getKatexJs()
        val autoRenderJs = KaTeXAssetLoader.getAutoRenderJs()
        
        return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>$katexCss</style>
<style>$css</style>
</head>
<body>
<div id="content"></div>
<script>$markedJs</script>
<script>$katexJs</script>
<script>$autoRenderJs</script>
<script>$js</script>
</body>
</html>"""
    }
    
    /**
     * HTML sin KaTeX para cuando los assets no estan cargados
     */
    private fun generateFallbackHtml(markdown: String, textColor: String): String {
        val escapedHtml = markdown
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        
        return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/aaaakshat/cm-web-fonts@latest/fonts.css">
<style>
body { font-family: 'Computer Modern Serif', 'CMU Serif', Georgia, serif; color: $textColor; padding: 8px; }
</style>
</head>
<body>$escapedHtml</body>
</html>"""
    }
    
    private fun buildCss(textColor: String, accentColor: String): String {
        return """
@import url('https://cdn.jsdelivr.net/gh/aaaakshat/cm-web-fonts@latest/fonts.css');
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: transparent !important; }
body {
    font-family: 'Computer Modern Serif', 'CMU Serif', 'Latin Modern Roman', Georgia, serif;
    color: $textColor;
    padding: 4px 0;
    line-height: 1.6;
    font-size: 14px;
    word-wrap: break-word;
}
h1, h2, h3 { color: $textColor; font-weight: 600; margin: 0.4em 0 0.2em; font-family: 'Computer Modern Serif', 'CMU Serif', Georgia, serif; }
h1 { font-size: 1.25em; }
h2 { font-size: 1.15em; }
h3 { font-size: 1.05em; }
p { margin: 0.3em 0; }
strong { font-weight: 600; }
em { font-style: italic; }
code {
    background: ${textColor}10;
    padding: 1px 4px;
    border-radius: 3px;
    font-family: 'Computer Modern Typewriter', monospace;
    font-size: 0.9em;
}
pre {
    background: ${textColor}08;
    padding: 8px 10px;
    border-radius: 4px;
    overflow-x: auto;
    margin: 0.4em 0;
    border-left: 2px solid $accentColor;
}
pre code { background: transparent; padding: 0; }
blockquote {
    border-left: 2px solid $accentColor;
    padding-left: 10px;
    margin: 0.4em 0;
    color: ${textColor}aa;
    font-style: italic;
}
ul, ol { margin: 0.3em 0; padding-left: 1.4em; }
li { margin: 0.15em 0; }
a { color: $accentColor; text-decoration: none; }
hr { border: none; border-top: 1px solid ${textColor}15; margin: 0.6em 0; }
.katex-display { margin: 0.5em 0; overflow-x: auto; }
.katex { font-size: 1.1em; }
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-thumb { background: ${textColor}25; border-radius: 3px; }
        """.trimIndent()
    }
    
    private fun buildJs(escapedMarkdown: String): String {
        val d = "\$"
        return """
var md = '$escapedMarkdown';
var retries = 0;

function render() {
    if (typeof marked === 'undefined' || typeof katex === 'undefined' || typeof renderMathInElement === 'undefined') {
        if (retries++ < 50) {
            setTimeout(render, 50);
        } else {
            fallback();
        }
        return;
    }
    try {
        marked.setOptions({ gfm: true, breaks: true });
        document.getElementById('content').innerHTML = marked.parse(md);
        renderMathInElement(document.getElementById('content'), {
            delimiters: [
                {left: '${d}${d}', right: '${d}${d}', display: true},
                {left: '${d}', right: '${d}', display: false}
            ],
            throwOnError: false
        });
    } catch(e) {
        fallback();
    }
}

function fallback() {
    var html = md.replace(/\\n/g, '<br>');
    document.getElementById('content').innerHTML = '<p>' + html + '</p>';
}

render();
        """.trimIndent()
    }
    
    private fun escapeForJs(text: String): String {
        // Primero normalizar bloques LaTeX multilinea
        // Los bloques $$...$$ con saltos de linea internos deben colapsarse a una sola linea
        val normalizedText = normalizeLatexBlocks(text)
        
        return normalizedText
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\r\n", "\\n")
            .replace("\r", "\\n")
            .replace("\n", "\\n")
            .replace("</script>", "<\\/script>")
    }
    
    /**
     * Normaliza bloques LaTeX multilinea colapsandolos a una sola linea
     * Ejemplo:
     *   $$
     *   E = mc^2
     *   $$
     * Se convierte a:
     *   $$E = mc^2$$
     */
    private fun normalizeLatexBlocks(text: String): String {
        var result = text
        
        // Patron para bloques $$ ... $$ (display math) que pueden tener saltos de linea
        // Captura todo entre $$ y $$ incluyendo saltos de linea
        val displayPattern = Regex("""\$\$\s*([\s\S]*?)\s*\$\$""")
        result = displayPattern.replace(result) { match ->
            val content = match.groupValues[1]
                .replace("\r\n", " ")
                .replace("\r", " ")
                .replace("\n", " ")
                .replace(Regex("\\s+"), " ")  // Multiples espacios a uno solo
                .trim()
            "\$\$$content\$\$"
        }
        
        return result
    }
    
    data class MessageData(
        val time: String,
        val sender: String?,
        val content: String
    )
}
