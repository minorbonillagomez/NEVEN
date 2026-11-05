package com.neven.launcher.ui.notifications

import android.graphics.Typeface
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.style.RelativeSizeSpan
import android.text.style.StyleSpan
import android.text.style.StrikethroughSpan
import android.text.style.TypefaceSpan

/**
 * Renderizador simple de Markdown a Spannable
 * 
 * Soporta:
 * - # Header 1, ## Header 2, ### Header 3
 * - **negrita** y __negrita__
 * - *cursiva* y _cursiva_
 * - ~~tachado~~
 * - `código inline`
 * - $LaTeX$ (muestra como código/monospace)
 * - Listas con - o *
 * 
 * No usa WebView, ideal para popups ligeros
 */
object SimpleMarkdownRenderer {
    
    /**
     * Convierte texto con Markdown simple a Spannable
     */
    fun render(text: String): Spanned {
        val builder = SpannableStringBuilder()
        val lines = text.split("\n")
        
        lines.forEachIndexed { index, line ->
            if (index > 0) builder.append("\n")
            
            when {
                // Headers
                line.startsWith("### ") -> {
                    val content = line.removePrefix("### ")
                    appendWithSpan(builder, content, 
                        StyleSpan(Typeface.BOLD),
                        RelativeSizeSpan(1.1f))
                }
                line.startsWith("## ") -> {
                    val content = line.removePrefix("## ")
                    appendWithSpan(builder, content,
                        StyleSpan(Typeface.BOLD),
                        RelativeSizeSpan(1.2f))
                }
                line.startsWith("# ") -> {
                    val content = line.removePrefix("# ")
                    appendWithSpan(builder, content,
                        StyleSpan(Typeface.BOLD),
                        RelativeSizeSpan(1.3f))
                }
                // Listas
                line.trimStart().startsWith("- ") || line.trimStart().startsWith("* ") -> {
                    val indent = line.takeWhile { it == ' ' || it == '\t' }
                    val content = line.trimStart().removePrefix("- ").removePrefix("* ")
                    builder.append(indent)
                    builder.append("• ")
                    appendInlineFormatting(builder, content)
                }
                // Línea normal
                else -> {
                    appendInlineFormatting(builder, line)
                }
            }
        }
        
        return builder
    }
    
    /**
     * Procesa formatos inline: negrita, cursiva, código, LaTeX, tachado
     */
    private fun appendInlineFormatting(builder: SpannableStringBuilder, text: String) {
        var remaining = text
        
        while (remaining.isNotEmpty()) {
            when {
                // LaTeX: $...$
                remaining.startsWith("$") && remaining.indexOf("$", 1) > 0 -> {
                    val endIndex = remaining.indexOf("$", 1)
                    val latex = remaining.substring(1, endIndex)
                    appendWithSpan(builder, "[$latex]", 
                        TypefaceSpan("monospace"),
                        StyleSpan(Typeface.ITALIC))
                    remaining = remaining.substring(endIndex + 1)
                }
                // Código inline: `...`
                remaining.startsWith("`") && remaining.indexOf("`", 1) > 0 -> {
                    val endIndex = remaining.indexOf("`", 1)
                    val code = remaining.substring(1, endIndex)
                    appendWithSpan(builder, code, TypefaceSpan("monospace"))
                    remaining = remaining.substring(endIndex + 1)
                }
                // Negrita: **...** o __...__
                remaining.startsWith("**") && remaining.indexOf("**", 2) > 0 -> {
                    val endIndex = remaining.indexOf("**", 2)
                    val bold = remaining.substring(2, endIndex)
                    appendWithSpan(builder, bold, StyleSpan(Typeface.BOLD))
                    remaining = remaining.substring(endIndex + 2)
                }
                remaining.startsWith("__") && remaining.indexOf("__", 2) > 0 -> {
                    val endIndex = remaining.indexOf("__", 2)
                    val bold = remaining.substring(2, endIndex)
                    appendWithSpan(builder, bold, StyleSpan(Typeface.BOLD))
                    remaining = remaining.substring(endIndex + 2)
                }
                // Cursiva: *...* o _..._
                remaining.startsWith("*") && !remaining.startsWith("**") && remaining.indexOf("*", 1) > 0 -> {
                    val endIndex = remaining.indexOf("*", 1)
                    val italic = remaining.substring(1, endIndex)
                    appendWithSpan(builder, italic, StyleSpan(Typeface.ITALIC))
                    remaining = remaining.substring(endIndex + 1)
                }
                remaining.startsWith("_") && !remaining.startsWith("__") && remaining.indexOf("_", 1) > 0 -> {
                    val endIndex = remaining.indexOf("_", 1)
                    val italic = remaining.substring(1, endIndex)
                    appendWithSpan(builder, italic, StyleSpan(Typeface.ITALIC))
                    remaining = remaining.substring(endIndex + 1)
                }
                // Tachado: ~~...~~
                remaining.startsWith("~~") && remaining.indexOf("~~", 2) > 0 -> {
                    val endIndex = remaining.indexOf("~~", 2)
                    val strikethrough = remaining.substring(2, endIndex)
                    appendWithSpan(builder, strikethrough, StrikethroughSpan())
                    remaining = remaining.substring(endIndex + 2)
                }
                // Caracter normal
                else -> {
                    builder.append(remaining[0])
                    remaining = remaining.substring(1)
                }
            }
        }
    }
    
    /**
     * Agrega texto con uno o más spans
     */
    private fun appendWithSpan(builder: SpannableStringBuilder, text: String, vararg spans: Any) {
        val start = builder.length
        builder.append(text)
        val end = builder.length
        
        spans.forEach { span ->
            builder.setSpan(span, start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        }
    }
}
