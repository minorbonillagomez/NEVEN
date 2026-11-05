package com.neven.launcher.ui.markdown

import android.annotation.SuppressLint
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.viewinterop.AndroidView

/**
 * NEVEN Markdown WebView con soporte KaTeX
 * 
 * Componente que renderiza contenido Markdown con ecuaciones LaTeX
 * usando WebView + marked.js + KaTeX.
 * 
 * Características:
 * - Renderizado completo de Markdown con marked.js
 * - Ecuaciones LaTeX con KaTeX (inline $ y bloque $$)
 * - Fondo transparente para mantener estética del launcher
 * - Colores dinámicos según paleta activa
 * - Tipografía serif académica
 * 
 * @param markdown Contenido en formato Markdown con LaTeX
 * @param textColor Color del texto principal
 * @param backgroundColor Color de fondo (para elementos como code blocks)
 * @param accentColor Color de acento para links y elementos destacados
 * @param modifier Modificador de Compose
 */
@SuppressLint("SetJavaScriptEnabled")
@Composable
fun MarkdownWebView(
    markdown: String,
    textColor: Color,
    backgroundColor: Color,
    accentColor: Color,
    modifier: Modifier = Modifier
) {
    // Generar HTML con el contenido Markdown y KaTeX
    val htmlContent = remember(markdown, textColor, accentColor) {
        generateHtmlWithKaTeX(markdown, textColor, backgroundColor, accentColor)
    }
    
    AndroidView(
        factory = { context ->
            WebView(context).apply {
                // Configurar WebView
                settings.javaScriptEnabled = true
                settings.loadWithOverviewMode = true
                settings.useWideViewPort = true
                settings.domStorageEnabled = true
                
                // Fondo transparente para ver el fondo del launcher
                setBackgroundColor(android.graphics.Color.TRANSPARENT)
                
                // Cliente web básico
                webViewClient = WebViewClient()
                
                // Cargar contenido HTML
                loadDataWithBaseURL(
                    "https://cdn.jsdelivr.net",
                    htmlContent,
                    "text/html",
                    "UTF-8",
                    null
                )
            }
        },
        update = { webView ->
            // Actualizar contenido si cambia
            webView.loadDataWithBaseURL(
                "https://cdn.jsdelivr.net",
                htmlContent,
                "text/html",
                "UTF-8",
                null
            )
        },
        modifier = modifier
    )
}

/**
 * Genera documento HTML completo con Markdown renderizado y soporte KaTeX
 * 
 * Incluye:
 * - KaTeX CSS y JS desde CDN
 * - marked.js para parsear Markdown
 * - auto-render para ecuaciones automáticas
 * - CSS personalizado que coincide con tema NEVEN
 * 
 * @param markdown Contenido Markdown
 * @param textColor Color del texto
 * @param bgColor Color de fondo
 * @param accent Color de acento
 * @return HTML completo listo para cargar en WebView
 */
private fun generateHtmlWithKaTeX(
    markdown: String,
    textColor: Color,
    @Suppress("UNUSED_PARAMETER") bgColor: Color,
    accent: Color
): String {
    val textHex = colorToHex(textColor)
    val accentHex = colorToHex(accent)
    
    // Escapar el contenido Markdown para JavaScript
    val escapedMarkdown = escapeForJs(markdown)
    
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <!-- KaTeX CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" 
          integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" 
          crossorigin="anonymous">
    
    <style>
        /* Reset y base */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html, body {
            background: transparent !important;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: 'Times New Roman', 'Georgia', serif;
            color: $textHex;
            padding: 0 4px 24px 4px;
            line-height: 1.7;
            font-size: 17px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: $textHex;
            font-weight: 600;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            line-height: 1.3;
        }
        
        h1 { font-size: 1.8em; border-bottom: 1px solid ${textHex}33; padding-bottom: 0.3em; }
        h2 { font-size: 1.5em; border-bottom: 1px solid ${textHex}22; padding-bottom: 0.2em; }
        h3 { font-size: 1.3em; }
        h4 { font-size: 1.1em; }
        
        /* Párrafos */
        p {
            margin: 1em 0;
            text-align: justify;
        }
        
        /* Links */
        a {
            color: $accentHex;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        /* Código inline */
        code {
            background: ${textHex}15;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        /* Bloques de código */
        pre {
            background: rgba(0, 0, 0, 0.25);
            padding: 12px 16px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1em 0;
            border-left: 3px solid $accentHex;
        }
        
        pre code {
            background: transparent;
            padding: 0;
            font-size: 0.85em;
            line-height: 1.5;
        }
        
        /* Blockquotes */
        blockquote {
            border-left: 3px solid $accentHex;
            padding-left: 16px;
            margin: 1em 0;
            color: ${textHex}cc;
            font-style: italic;
        }
        
        /* Listas */
        ul, ol {
            margin: 1em 0;
            padding-left: 2em;
        }
        
        li {
            margin: 0.3em 0;
        }
        
        /* Tablas */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            font-size: 0.95em;
        }
        
        th, td {
            border: 1px solid ${textHex}33;
            padding: 8px 12px;
            text-align: left;
        }
        
        th {
            background: ${textHex}10;
            font-weight: 600;
        }
        
        tr:nth-child(even) {
            background: ${textHex}05;
        }
        
        /* Línea horizontal */
        hr {
            border: none;
            border-top: 1px solid ${textHex}25;
            margin: 2em 0;
        }
        
        /* Imágenes */
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1em 0;
        }
        
        /* KaTeX - Ecuaciones */
        .katex {
            font-size: 1.1em;
            color: $textHex;
        }
        
        .katex-display {
            overflow-x: auto;
            overflow-y: hidden;
            padding: 0.5em 0;
            margin: 1em 0;
        }
        
        .katex-display > .katex {
            text-align: center;
        }
        
        /* Strong y emphasis */
        strong, b {
            font-weight: 700;
        }
        
        em, i {
            font-style: italic;
        }
        
        /* Strikethrough */
        del, s {
            text-decoration: line-through;
            opacity: 0.7;
        }
        
        /* Contenedor principal */
        #content {
            max-width: 100%;
        }
        
        /* Scrollbar personalizada (webkit) */
        ::-webkit-scrollbar {
            width: 4px;
            height: 4px;
        }
        
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
            background: ${textHex}40;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div id="content"></div>
    
    <!-- Scripts al final del body para asegurar carga correcta -->
    <script src="https://cdn.jsdelivr.net/npm/marked@12.0.1/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    
    <script>
        // Función para inicializar cuando todo esté listo
        function initRender() {
            try {
                // Verificar que las librerías estén cargadas
                if (typeof marked === 'undefined') {
                    throw new Error('marked.js no cargado');
                }
                if (typeof katex === 'undefined') {
                    throw new Error('KaTeX no cargado');
                }
                if (typeof renderMathInElement === 'undefined') {
                    throw new Error('KaTeX auto-render no cargado');
                }
                
                // Contenido Markdown
                const markdown = '$escapedMarkdown';
                
                // Configurar marked
                marked.setOptions({
                    gfm: true,
                    breaks: true
                });
                
                // Renderizar Markdown a HTML
                const htmlContent = marked.parse(markdown);
                document.getElementById('content').innerHTML = htmlContent;
                
                // Renderizar ecuaciones LaTeX con KaTeX
                renderMathInElement(document.getElementById('content'), {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '$', right: '$', display: false}
                    ],
                    throwOnError: false,
                    errorColor: '#cc0000',
                    strict: false
                });
                
            } catch (e) {
                console.error('Error:', e);
                document.getElementById('content').innerHTML = 
                    '<p style="color: #ff6b6b;">Error: ' + e.message + '</p>';
            }
        }
        
        // Ejecutar cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initRender);
        } else {
            // DOM ya cargado, esperar un momento para los scripts
            setTimeout(initRender, 100);
        }
    </script>
</body>
</html>
    """.trimIndent()
}

/**
 * Convierte Color de Compose a formato hexadecimal CSS
 * 
 * @param color Color de Compose
 * @return String en formato "#RRGGBB"
 */
private fun colorToHex(color: Color): String {
    val argb = color.toArgb()
    val r = (argb shr 16) and 0xFF
    val g = (argb shr 8) and 0xFF
    val b = argb and 0xFF
    return String.format("#%02X%02X%02X", r, g, b)
}

/**
 * Escapa caracteres especiales para inserción segura en JavaScript
 * 
 * NOTA: NO escapamos $ porque lo necesitamos para ecuaciones LaTeX ($...$)
 * En su lugar, usamos comillas simples para el string en JS
 * 
 * @param text Texto a escapar
 * @return Texto escapado para string de JS
 */
private fun escapeForJs(text: String): String {
    return text
        .replace("\\", "\\\\")          // Backslashes primero
        .replace("'", "\\'")            // Comillas simples
        .replace("\r\n", "\\n")         // Windows line endings
        .replace("\r", "\\n")           // Old Mac line endings  
        .replace("\n", "\\n")           // Unix line endings
        .replace("</script>", "<\\/script>")  // Evitar cerrar tag script
}
