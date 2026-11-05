package com.neven.launcher.ui.markdown

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.neven.launcher.R
import com.neven.launcher.data.BackgroundPosition
import com.neven.launcher.data.BackgroundType
import com.neven.launcher.ui.components.NevenBackground
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * Opacidad por defecto para el visor Markdown (85%)
 * 
 * Esta opacidad es más alta que el launcher principal para mejorar
 * la legibilidad durante la lectura de documentos académicos/científicos.
 */
private const val MARKDOWN_VIEWER_DEFAULT_OPACITY = 0.85f

/**
 * NEVEN Markdown Viewer Screen
 * 
 * Pantalla de visualización de archivos Markdown con soporte LaTeX via KaTeX.
 * 
 * Diseño científico/académico:
 * - Header con símbolo "§" + nombre del archivo
 * - Botón "<" para volver
 * - Fondo translúcido con opacidad 85% para mejor legibilidad
 * - Tipografía serif para el contenido
 * - Ecuaciones LaTeX renderizadas con KaTeX
 * - Buen espaciado entre secciones
 * 
 * El contenido se renderiza usando WebView + marked.js + KaTeX
 * para soporte completo de ecuaciones matemáticas.
 */
@Suppress("UNUSED_PARAMETER")
@Composable
fun MarkdownViewerScreen(
    content: String,
    fileName: String,
    colors: NevenColors,
    backgroundType: BackgroundType = BackgroundType.SOLID,
    backgroundImageUri: String? = null,
    backgroundPosition: BackgroundPosition = BackgroundPosition.CROP,
    @Suppress("unused") backgroundOpacity: Float = MARKDOWN_VIEWER_DEFAULT_OPACITY,
    backgroundTintEnabled: Boolean = false,
    onBack: () -> Unit
) {
    // Usar opacidad fija de 85% para el visor (mejor legibilidad)
    val readerOpacity = MARKDOWN_VIEWER_DEFAULT_OPACITY
    
    // Usar el mismo fondo que Settings para consistencia visual
    // pero con opacidad aumentada para lectura
    NevenBackground(
        backgroundType = backgroundType,
        imageUri = backgroundImageUri,
        position = backgroundPosition,
        opacity = readerOpacity,
        tintEnabled = backgroundTintEnabled,
        tintColor = colors.accent,
        fallbackColor = colors.background,
        isDark = colors.isDark
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .systemBarsPadding()
        ) {
            // ═══════════════════════════════════════════════════════════
            // HEADER
            // ═══════════════════════════════════════════════════════════
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Botón volver
                Text(
                    text = "<",
                    modifier = Modifier
                        .clickable { onBack() }
                        .padding(8.dp),
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = FontFamily.Serif
                    ),
                    color = colors.textPrimary
                )
                
                Spacer(modifier = Modifier.width(16.dp))
                
                // Símbolo científico § (sección)
                Text(
                    text = "\u00A7",
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = FontFamily.Serif
                    ),
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                // Nombre del archivo (sin extensión)
                Text(
                    text = fileName.removeSuffix(".md"),
                    style = MaterialTheme.typography.headlineMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.textPrimary,
                    maxLines = 1
                )
            }
            
            Divider(color = colors.textSecondary.copy(alpha = 0.15f))
            
            // ═══════════════════════════════════════════════════════════
            // CONTENIDO MARKDOWN CON KATEX
            // ═══════════════════════════════════════════════════════════
            if (content.isBlank()) {
                // Estado vacío
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = stringResource(R.string.markdown_empty_file),
                        style = MaterialTheme.typography.bodyLarge,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
            } else {
                // Contenido renderizado con WebView + KaTeX
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp)
                ) {
                    // WebView con Markdown + KaTeX para ecuaciones LaTeX
                    MarkdownWebView(
                        markdown = content,
                        textColor = colors.textPrimary,
                        backgroundColor = colors.background,
                        accentColor = colors.accent,
                        modifier = Modifier.fillMaxSize()
                    )
                }
            }
        }
    }
}

/**
 * Versión simplificada de la pantalla para preview
 */
@Composable
fun MarkdownViewerScreenSimple(
    content: String,
    fileName: String,
    colors: NevenColors,
    onBack: () -> Unit
) {
    MarkdownViewerScreen(
        content = content,
        fileName = fileName,
        colors = colors,
        backgroundType = BackgroundType.SOLID,
        backgroundImageUri = null,
        backgroundPosition = BackgroundPosition.CROP,
        backgroundOpacity = MARKDOWN_VIEWER_DEFAULT_OPACITY,
        backgroundTintEnabled = false,
        onBack = onBack
    )
}
