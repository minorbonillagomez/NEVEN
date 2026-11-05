package com.neven.launcher.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.R
import com.neven.launcher.data.NevenFontFamily as FontFamilyOption
import com.neven.launcher.ui.theme.JetBrainsMonoFontFamily
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.OpenSansFontFamily
import com.neven.launcher.ui.theme.PlayfairFontFamily
import com.neven.launcher.ui.theme.RobotoFontFamily
import com.neven.launcher.ui.theme.SourceCodeProFontFamily
import com.neven.launcher.ui.theme.rememberNevenColors

/**
 * Pantalla de configuración de tipo de fuente
 * 
 * Permite seleccionar entre 4 tipos de fuente:
 * - Serif (default) - Elegante, estilo académico/LaTeX
 * - Sans-serif - Moderno, minimalista
 * - Monospace - Técnico, estilo código
 * - Cursive - Artístico, fluido
 * 
 * Incluye preview en tiempo real de cada fuente
 */
@Composable
fun FontFamilySettingsScreen(
    currentPalette: NevenPalette,
    isDarkMode: Boolean,
    currentFontFamily: FontFamilyOption,
    onFontFamilyChange: (FontFamilyOption) -> Unit,
    onBack: () -> Unit
) {
    // Usar rememberNevenColors para aplicar el color de contraste personalizado
    val colors = rememberNevenColors(currentPalette, isDarkMode)
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
    ) {
            // ═══════════════════════════════════════════════════════════════
            // HEADER
            // ═══════════════════════════════════════════════════════════════
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
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
                
                // Símbolo científico: F (de Font)
                Text(
                    text = "F",
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = FontFamily.Serif
                    ),
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                Text(
                    text = stringResource(R.string.settings_font_family),
                    style = MaterialTheme.typography.headlineMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.textPrimary
                )
            }
            
            HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.15f))
            
            // ═══════════════════════════════════════════════════════════════
            // CONTENIDO
            // ═══════════════════════════════════════════════════════════════
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                // ─────────────────────────────────────────────────────────────
                // SELECTOR DE FUENTE
                // ─────────────────────────────────────────────────────────────
                FontFamilySelector(
                    currentFamily = currentFontFamily,
                    onFamilyChange = onFontFamilyChange,
                    colors = colors
                )
                
                // ─────────────────────────────────────────────────────────────
                // PREVIEW EN TIEMPO REAL
                // ─────────────────────────────────────────────────────────────
                FontFamilyPreview(
                    fontFamily = currentFontFamily,
                    colors = colors
                )
            }
        }
}

/**
 * Selector visual de tipo de fuente con las 4 opciones
 */
@Composable
fun FontFamilySelector(
    currentFamily: FontFamilyOption,
    onFamilyChange: (FontFamilyOption) -> Unit,
    colors: NevenColors
) {
    val cardBg = Color.Transparent
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = cardBg,
                shape = RoundedCornerShape(16.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = colors.textSecondary.copy(alpha = 0.12f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        Text(
            text = stringResource(R.string.settings_font_family),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // Opciones de fuente en columna
        Column(
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            FontFamilyOption.entries.forEach { family ->
                FontFamilyOptionChip(
                    family = family,
                    isSelected = family == currentFamily,
                    colors = colors,
                    onClick = { onFamilyChange(family) }
                )
            }
        }
    }
}

/**
 * Chip individual para cada opción de fuente
 * Estilo: botón seleccionado tiene SOLO BORDE/CONTORNO, el texto NO cambia de color
 */
@Composable
private fun FontFamilyOptionChip(
    family: FontFamilyOption,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    // Seleccionado: fondo transparente, solo borde con color accent
    val backgroundColor = Color.Transparent
    
    val borderColor = if (isSelected) {
        colors.accent
    } else {
        colors.textSecondary.copy(alpha = 0.3f)
    }
    
    // Obtener la FontFamily de Compose correspondiente
    val composeFontFamily = when (family) {
        FontFamilyOption.SERIF -> FontFamily.Serif
        FontFamilyOption.SANS_SERIF -> FontFamily.SansSerif
        FontFamilyOption.MONOSPACE -> FontFamily.Monospace
        FontFamilyOption.CURSIVE -> FontFamily.Cursive
        FontFamilyOption.ROBOTO -> RobotoFontFamily
        FontFamilyOption.OPEN_SANS -> OpenSansFontFamily
        FontFamilyOption.PLAYFAIR -> PlayfairFontFamily
        FontFamilyOption.JETBRAINS_MONO -> JetBrainsMonoFontFamily
        FontFamilyOption.SOURCE_CODE_PRO -> SourceCodeProFontFamily
    }
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))  // Clip primero para ripple correcto
            .clickable(onClick = onClick)      // Clickable ANTES del background para que funcione
            .background(
                color = backgroundColor,
                shape = RoundedCornerShape(12.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = borderColor,
                shape = RoundedCornerShape(12.dp)
            )
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Muestra de la fuente con una letra grande
        Text(
            text = "Aa",
            style = MaterialTheme.typography.headlineSmall.copy(
                fontFamily = composeFontFamily
            ),
            color = if (isSelected) colors.accent else colors.textSecondary,
            modifier = Modifier.width(48.dp)
        )
        
        Spacer(modifier = Modifier.width(16.dp))
        
        Column(modifier = Modifier.weight(1f)) {
            // Nombre de la fuente
            Text(
                text = getFontFamilyName(family),
                style = MaterialTheme.typography.titleMedium.copy(
                    fontFamily = composeFontFamily
                ),
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                color = colors.textSecondary
            )
            
            // Descripción
            Text(
                text = getFontFamilyDescription(family),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary.copy(alpha = 0.7f)
            )
        }
    }
}

/**
 * Obtiene el nombre localizado de la fuente
 */
@Composable
private fun getFontFamilyName(family: FontFamilyOption): String {
    return when (family) {
        FontFamilyOption.SERIF -> stringResource(R.string.font_family_serif)
        FontFamilyOption.SANS_SERIF -> stringResource(R.string.font_family_sans_serif)
        FontFamilyOption.MONOSPACE -> stringResource(R.string.font_family_monospace)
        FontFamilyOption.CURSIVE -> stringResource(R.string.font_family_cursive)
        FontFamilyOption.ROBOTO -> stringResource(R.string.font_family_roboto)
        FontFamilyOption.OPEN_SANS -> stringResource(R.string.font_family_open_sans)
        FontFamilyOption.PLAYFAIR -> stringResource(R.string.font_family_playfair)
        FontFamilyOption.JETBRAINS_MONO -> stringResource(R.string.font_family_jetbrains_mono)
        FontFamilyOption.SOURCE_CODE_PRO -> stringResource(R.string.font_family_source_code_pro)
    }
}

/**
 * Obtiene la descripción localizada de la fuente
 */
@Composable
private fun getFontFamilyDescription(family: FontFamilyOption): String {
    return when (family) {
        FontFamilyOption.SERIF -> stringResource(R.string.font_family_serif_desc)
        FontFamilyOption.SANS_SERIF -> stringResource(R.string.font_family_sans_serif_desc)
        FontFamilyOption.MONOSPACE -> stringResource(R.string.font_family_monospace_desc)
        FontFamilyOption.CURSIVE -> stringResource(R.string.font_family_cursive_desc)
        FontFamilyOption.ROBOTO -> stringResource(R.string.font_family_roboto_desc)
        FontFamilyOption.OPEN_SANS -> stringResource(R.string.font_family_open_sans_desc)
        FontFamilyOption.PLAYFAIR -> stringResource(R.string.font_family_playfair_desc)
        FontFamilyOption.JETBRAINS_MONO -> stringResource(R.string.font_family_jetbrains_mono_desc)
        FontFamilyOption.SOURCE_CODE_PRO -> stringResource(R.string.font_family_source_code_pro_desc)
    }
}

/**
 * Preview en tiempo real del tipo de fuente seleccionado
 */
@Composable
fun FontFamilyPreview(
    fontFamily: FontFamilyOption,
    colors: NevenColors
) {
    val cardBg = Color.Transparent
    
    // Obtener la FontFamily de Compose correspondiente
    val composeFontFamily = when (fontFamily) {
        FontFamilyOption.SERIF -> FontFamily.Serif
        FontFamilyOption.SANS_SERIF -> FontFamily.SansSerif
        FontFamilyOption.MONOSPACE -> FontFamily.Monospace
        FontFamilyOption.CURSIVE -> FontFamily.Cursive
        FontFamilyOption.ROBOTO -> RobotoFontFamily
        FontFamilyOption.OPEN_SANS -> OpenSansFontFamily
        FontFamilyOption.PLAYFAIR -> PlayfairFontFamily
        FontFamilyOption.JETBRAINS_MONO -> JetBrainsMonoFontFamily
        FontFamilyOption.SOURCE_CODE_PRO -> SourceCodeProFontFamily
    }
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = cardBg,
                shape = RoundedCornerShape(16.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = colors.textSecondary.copy(alpha = 0.12f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        Text(
            text = stringResource(R.string.font_family_preview),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // Preview con la fuente seleccionada
        Column(
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Título simulado
            Text(
                text = "NEVEN Launcher",
                style = MaterialTheme.typography.headlineSmall.copy(
                    fontFamily = composeFontFamily
                ),
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            
            // Texto body simulado
            Text(
                text = "El tiempo es la sustancia de la que estoy hecho. El tiempo es un rio que me arrebata, pero yo soy el rio.",
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontFamily = composeFontFamily,
                    lineHeight = 22.sp
                ),
                color = colors.textSecondary
            )
            
            // Números y símbolos
            Text(
                text = "0123456789 + - = / * %",
                style = MaterialTheme.typography.bodyLarge.copy(
                    fontFamily = composeFontFamily
                ),
                color = colors.textSecondary.copy(alpha = 0.7f)
            )
        }
    }
}
