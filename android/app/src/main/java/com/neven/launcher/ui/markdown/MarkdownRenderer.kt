package com.neven.launcher.ui.markdown

import android.content.Context
import android.graphics.Typeface
import android.text.Spanned
import android.text.style.StyleSpan
import android.util.Log
import android.widget.TextView
import androidx.core.text.buildSpannedString
import io.noties.markwon.Markwon
import io.noties.markwon.ext.strikethrough.StrikethroughPlugin
import io.noties.markwon.ext.tables.TablePlugin
import io.noties.markwon.html.HtmlPlugin
import io.noties.markwon.image.coil.CoilImagesPlugin
import java.util.regex.Pattern

/**
 * NEVEN Markdown Renderer
 * 
 * Renderiza archivos Markdown con soporte para:
 * - Headers (#, ##, ###, etc.)
 * - Listas (-, *, 1., 2.)
 * - Negrita (**texto**) e itálica (*texto*)
 * - Código inline (`code`) y bloques (```)
 * - Links [texto](url)
 * - Imágenes ![alt](url)
 * - Blockquotes (>)
 * - Tablas
 * - Líneas horizontales (---)
 * - Ecuaciones LaTeX inline ($...$) y en bloque ($$...$$)
 * 
 * Usa Markwon como motor de renderizado con plugins para
 * tablas, tachado, HTML y soporte de imágenes con Coil.
 * 
 * Las ecuaciones LaTeX se renderizan como texto formateado
 * usando notación matemática Unicode.
 */
class MarkdownRenderer(context: Context) {
    
    companion object {
        private const val TAG = "MarkdownRenderer"
    }
    
    /**
     * Instancia de Markwon configurada con todos los plugins necesarios
     */
    private val markwon: Markwon = try {
        Markwon.builder(context)
            .usePlugin(TablePlugin.create(context))
            .usePlugin(StrikethroughPlugin.create())
            .usePlugin(HtmlPlugin.create())
            .usePlugin(CoilImagesPlugin.create(context))
            .build()
    } catch (e: Exception) {
        Log.e(TAG, "Error creando Markwon con plugins, usando configuración básica", e)
        // Fallback a Markwon básico sin plugins
        Markwon.create(context)
    }
    
    /**
     * Renderiza contenido Markdown a Spanned para uso en TextView
     * 
     * @param markdown Contenido en formato Markdown
     * @return Spanned con el contenido formateado
     */
    fun render(markdown: String): Spanned {
        return try {
            // Primero procesar LaTeX, luego renderizar Markdown
            val processedMarkdown = processLatex(markdown)
            markwon.toMarkdown(processedMarkdown)
        } catch (e: Exception) {
            Log.e(TAG, "Error al renderizar markdown", e)
            // Retornar texto sin procesar en caso de error
            android.text.SpannedString(markdown)
        }
    }
    
    /**
     * Aplica renderizado directamente a un TextView
     * 
     * @param textView Vista de texto destino
     * @param markdown Contenido en formato Markdown
     */
    fun setMarkdown(textView: TextView, markdown: String) {
        try {
            val processedMarkdown = processLatex(markdown)
            markwon.setMarkdown(textView, processedMarkdown)
        } catch (e: Exception) {
            Log.e(TAG, "Error al aplicar markdown a TextView", e)
            // En caso de error, mostrar el texto sin formato
            textView.text = markdown
        }
    }
    
    /**
     * Procesa ecuaciones LaTeX convirtiéndolas a representación Unicode
     * 
     * Soporta:
     * - Ecuaciones inline: $...$
     * - Ecuaciones en bloque: $$...$$
     * 
     * @param input Texto con posibles ecuaciones LaTeX
     * @return Texto con ecuaciones convertidas a Unicode
     */
    private fun processLatex(input: String): String {
        return try {
            var result = input
            
            // Procesar ecuaciones en bloque primero ($$...$$)
            result = processBlockEquations(result)
            
            // Procesar ecuaciones inline ($...$)
            result = processInlineEquations(result)
            
            result
        } catch (e: Exception) {
            Log.e(TAG, "Error al procesar LaTeX, retornando texto original", e)
            input
        }
    }
    
    /**
     * Procesa ecuaciones LaTeX en bloque ($$...$$)
     */
    private fun processBlockEquations(input: String): String {
        return try {
            val pattern = Pattern.compile("\\$\\$(.+?)\\$\\$", Pattern.DOTALL)
            val matcher = pattern.matcher(input)
            val buffer = StringBuffer()
            
            while (matcher.find()) {
                val latex = matcher.group(1) ?: ""
                val unicode = convertLatexToUnicode(latex.trim())
                // Centrar ecuación en bloque con líneas vacías
                // Escapar caracteres especiales para appendReplacement
                val replacement = "\n\n**$unicode**\n\n".replace("$", "\\$")
                matcher.appendReplacement(buffer, replacement)
            }
            matcher.appendTail(buffer)
            
            buffer.toString()
        } catch (e: Exception) {
            Log.e(TAG, "Error procesando ecuaciones en bloque", e)
            input
        }
    }
    
    /**
     * Procesa ecuaciones LaTeX inline ($...$)
     */
    private fun processInlineEquations(input: String): String {
        return try {
            val pattern = Pattern.compile("\\$([^\\$]+?)\\$")
            val matcher = pattern.matcher(input)
            val buffer = StringBuffer()
            
            while (matcher.find()) {
                val latex = matcher.group(1) ?: ""
                val unicode = convertLatexToUnicode(latex.trim())
                // Escapar caracteres especiales para appendReplacement
                val replacement = "*$unicode*".replace("$", "\\$")
                matcher.appendReplacement(buffer, replacement)
            }
            matcher.appendTail(buffer)
            
            buffer.toString()
        } catch (e: Exception) {
            Log.e(TAG, "Error procesando ecuaciones inline", e)
            input
        }
    }
    
    /**
     * Convierte notación LaTeX a caracteres Unicode
     * 
     * Soporta:
     * - Símbolos griegos (alpha, beta, gamma, etc.)
     * - Fracciones (frac{a}{b})
     * - Sub/superíndices (x^2, x_i)
     * - Raíces (sqrt{x})
     * - Sumatorias (sum)
     * - Integrales (int)
     * - Operadores matemáticos
     * - Matrices básicas
     * 
     * @param latex Expresión LaTeX
     * @return Representación Unicode equivalente
     */
    private fun convertLatexToUnicode(latex: String): String {
        var result = latex
        
        // ═══════════════════════════════════════════════════════════
        // Símbolos griegos minúsculas
        // ═══════════════════════════════════════════════════════════
        val greekLower = mapOf(
            "\\alpha" to "α",
            "\\beta" to "β",
            "\\gamma" to "γ",
            "\\delta" to "δ",
            "\\epsilon" to "ε",
            "\\varepsilon" to "ε",
            "\\zeta" to "ζ",
            "\\eta" to "η",
            "\\theta" to "θ",
            "\\vartheta" to "ϑ",
            "\\iota" to "ι",
            "\\kappa" to "κ",
            "\\lambda" to "λ",
            "\\mu" to "μ",
            "\\nu" to "ν",
            "\\xi" to "ξ",
            "\\pi" to "π",
            "\\varpi" to "ϖ",
            "\\rho" to "ρ",
            "\\varrho" to "ϱ",
            "\\sigma" to "σ",
            "\\varsigma" to "ς",
            "\\tau" to "τ",
            "\\upsilon" to "υ",
            "\\phi" to "φ",
            "\\varphi" to "ϕ",
            "\\chi" to "χ",
            "\\psi" to "ψ",
            "\\omega" to "ω"
        )
        
        // Símbolos griegos mayúsculas
        val greekUpper = mapOf(
            "\\Gamma" to "Γ",
            "\\Delta" to "Δ",
            "\\Theta" to "Θ",
            "\\Lambda" to "Λ",
            "\\Xi" to "Ξ",
            "\\Pi" to "Π",
            "\\Sigma" to "Σ",
            "\\Upsilon" to "Υ",
            "\\Phi" to "Φ",
            "\\Psi" to "Ψ",
            "\\Omega" to "Ω"
        )
        
        // Aplicar reemplazos de símbolos griegos
        greekLower.forEach { (key, value) ->
            result = result.replace(key, value)
        }
        greekUpper.forEach { (key, value) ->
            result = result.replace(key, value)
        }
        
        // ═══════════════════════════════════════════════════════════
        // Operadores y símbolos matemáticos
        // ═══════════════════════════════════════════════════════════
        val operators = mapOf(
            "\\infty" to "∞",
            "\\partial" to "∂",
            "\\nabla" to "∇",
            "\\forall" to "∀",
            "\\exists" to "∃",
            "\\nexists" to "∄",
            "\\emptyset" to "∅",
            "\\varnothing" to "∅",
            "\\in" to "∈",
            "\\notin" to "∉",
            "\\ni" to "∋",
            "\\subset" to "⊂",
            "\\supset" to "⊃",
            "\\subseteq" to "⊆",
            "\\supseteq" to "⊇",
            "\\cup" to "∪",
            "\\cap" to "∩",
            "\\setminus" to "∖",
            "\\times" to "×",
            "\\div" to "÷",
            "\\cdot" to "·",
            "\\pm" to "±",
            "\\mp" to "∓",
            "\\leq" to "≤",
            "\\le" to "≤",
            "\\geq" to "≥",
            "\\ge" to "≥",
            "\\neq" to "≠",
            "\\ne" to "≠",
            "\\approx" to "≈",
            "\\equiv" to "≡",
            "\\sim" to "∼",
            "\\simeq" to "≃",
            "\\propto" to "∝",
            "\\ll" to "≪",
            "\\gg" to "≫",
            "\\rightarrow" to "→",
            "\\to" to "→",
            "\\leftarrow" to "←",
            "\\leftrightarrow" to "↔",
            "\\Rightarrow" to "⇒",
            "\\Leftarrow" to "⇐",
            "\\Leftrightarrow" to "⇔",
            "\\implies" to "⟹",
            "\\iff" to "⟺",
            "\\mapsto" to "↦",
            "\\ldots" to "…",
            "\\cdots" to "⋯",
            "\\vdots" to "⋮",
            "\\ddots" to "⋱",
            "\\prime" to "′",
            "\\angle" to "∠",
            "\\perp" to "⊥",
            "\\parallel" to "∥",
            "\\triangle" to "△",
            "\\square" to "□",
            "\\circ" to "∘",
            "\\bullet" to "•",
            "\\star" to "★",
            "\\ast" to "∗",
            "\\oplus" to "⊕",
            "\\otimes" to "⊗",
            "\\neg" to "¬",
            "\\lnot" to "¬",
            "\\land" to "∧",
            "\\lor" to "∨",
            "\\wedge" to "∧",
            "\\vee" to "∨",
            "\\aleph" to "ℵ",
            "\\Re" to "ℜ",
            "\\Im" to "ℑ",
            "\\wp" to "℘",
            "\\hbar" to "ℏ",
            "\\ell" to "ℓ"
        )
        
        operators.forEach { (key, value) ->
            result = result.replace(key, value)
        }
        
        // ═══════════════════════════════════════════════════════════
        // Integrales y sumatorias
        // ═══════════════════════════════════════════════════════════
        result = result.replace("\\int", "∫")
        result = result.replace("\\iint", "∬")
        result = result.replace("\\iiint", "∭")
        result = result.replace("\\oint", "∮")
        result = result.replace("\\sum", "Σ")
        result = result.replace("\\prod", "Π")
        result = result.replace("\\coprod", "∐")
        
        // ═══════════════════════════════════════════════════════════
        // Fracciones: \frac{num}{den} → num/den
        // ═══════════════════════════════════════════════════════════
        val fracPattern = Pattern.compile("\\\\frac\\{([^}]*)\\}\\{([^}]*)\\}")
        var fracMatcher = fracPattern.matcher(result)
        while (fracMatcher.find()) {
            val num = fracMatcher.group(1) ?: ""
            val den = fracMatcher.group(2) ?: ""
            result = result.replaceFirst("\\\\frac\\{[^}]*\\}\\{[^}]*\\}".toRegex(), "($num/$den)")
            fracMatcher = fracPattern.matcher(result)
        }
        
        // ═══════════════════════════════════════════════════════════
        // Raíces: \sqrt{x} → √x, \sqrt[n]{x} → ⁿ√x
        // ═══════════════════════════════════════════════════════════
        result = result.replace("\\sqrt{([^}]*)}".toRegex()) { match ->
            "√(${match.groupValues[1]})"
        }
        result = result.replace("\\sqrt\\[([^\\]]*)\\]\\{([^}]*)\\}".toRegex()) { match ->
            val n = match.groupValues[1]
            val content = match.groupValues[2]
            "${toSuperscript(n)}√($content)"
        }
        
        // ═══════════════════════════════════════════════════════════
        // Superíndices: x^{...} o x^n
        // ═══════════════════════════════════════════════════════════
        // Primero con llaves: x^{abc}
        result = result.replace("\\^\\{([^}]*)\\}".toRegex()) { match ->
            toSuperscript(match.groupValues[1])
        }
        // Luego simple: x^2 (solo un caracter después de ^)
        result = result.replace("\\^([0-9a-zA-Z])".toRegex()) { match ->
            toSuperscript(match.groupValues[1])
        }
        
        // ═══════════════════════════════════════════════════════════
        // Subíndices: x_{...} o x_n
        // ═══════════════════════════════════════════════════════════
        // Primero con llaves: x_{abc}
        result = result.replace("_\\{([^}]*)\\}".toRegex()) { match ->
            toSubscript(match.groupValues[1])
        }
        // Luego simple: x_2 (solo un caracter después de _)
        result = result.replace("_([0-9a-zA-Z])".toRegex()) { match ->
            toSubscript(match.groupValues[1])
        }
        
        // ═══════════════════════════════════════════════════════════
        // Funciones matemáticas
        // ═══════════════════════════════════════════════════════════
        val functions = listOf(
            "sin", "cos", "tan", "cot", "sec", "csc",
            "arcsin", "arccos", "arctan",
            "sinh", "cosh", "tanh",
            "log", "ln", "exp",
            "lim", "max", "min", "sup", "inf",
            "det", "dim", "ker", "deg"
        )
        functions.forEach { func ->
            result = result.replace("\\\\$func".toRegex(), func)
        }
        
        // ═══════════════════════════════════════════════════════════
        // Limpiar comandos LaTeX restantes
        // ═══════════════════════════════════════════════════════════
        result = result.replace("\\left", "")
        result = result.replace("\\right", "")
        result = result.replace("\\big", "")
        result = result.replace("\\Big", "")
        result = result.replace("\\bigg", "")
        result = result.replace("\\Bigg", "")
        result = result.replace("\\text{([^}]*)}".toRegex()) { it.groupValues[1] }
        result = result.replace("\\mathrm{([^}]*)}".toRegex()) { it.groupValues[1] }
        result = result.replace("\\mathbf{([^}]*)}".toRegex()) { it.groupValues[1] }
        result = result.replace("\\mathit{([^}]*)}".toRegex()) { it.groupValues[1] }
        
        // Eliminar llaves sueltas
        result = result.replace("{", "")
        result = result.replace("}", "")
        
        // Limpiar espacios múltiples
        result = result.replace("\\s+".toRegex(), " ").trim()
        
        return result
    }
    
    /**
     * Convierte caracteres a superíndice Unicode
     */
    private fun toSuperscript(text: String): String {
        val superscriptMap = mapOf(
            '0' to '⁰', '1' to '¹', '2' to '²', '3' to '³', '4' to '⁴',
            '5' to '⁵', '6' to '⁶', '7' to '⁷', '8' to '⁸', '9' to '⁹',
            '+' to '⁺', '-' to '⁻', '=' to '⁼', '(' to '⁽', ')' to '⁾',
            'n' to 'ⁿ', 'i' to 'ⁱ',
            'a' to 'ᵃ', 'b' to 'ᵇ', 'c' to 'ᶜ', 'd' to 'ᵈ', 'e' to 'ᵉ',
            'f' to 'ᶠ', 'g' to 'ᵍ', 'h' to 'ʰ', 'j' to 'ʲ', 'k' to 'ᵏ',
            'l' to 'ˡ', 'm' to 'ᵐ', 'o' to 'ᵒ', 'p' to 'ᵖ', 'r' to 'ʳ',
            's' to 'ˢ', 't' to 'ᵗ', 'u' to 'ᵘ', 'v' to 'ᵛ', 'w' to 'ʷ',
            'x' to 'ˣ', 'y' to 'ʸ', 'z' to 'ᶻ'
        )
        return text.map { superscriptMap[it] ?: it }.joinToString("")
    }
    
    /**
     * Convierte caracteres a subíndice Unicode
     */
    private fun toSubscript(text: String): String {
        val subscriptMap = mapOf(
            '0' to '₀', '1' to '₁', '2' to '₂', '3' to '₃', '4' to '₄',
            '5' to '₅', '6' to '₆', '7' to '₇', '8' to '₈', '9' to '₉',
            '+' to '₊', '-' to '₋', '=' to '₌', '(' to '₍', ')' to '₎',
            'a' to 'ₐ', 'e' to 'ₑ', 'h' to 'ₕ', 'i' to 'ᵢ', 'j' to 'ⱼ',
            'k' to 'ₖ', 'l' to 'ₗ', 'm' to 'ₘ', 'n' to 'ₙ', 'o' to 'ₒ',
            'p' to 'ₚ', 'r' to 'ᵣ', 's' to 'ₛ', 't' to 'ₜ', 'u' to 'ᵤ',
            'v' to 'ᵥ', 'x' to 'ₓ'
        )
        return text.map { subscriptMap[it] ?: it }.joinToString("")
    }
}
