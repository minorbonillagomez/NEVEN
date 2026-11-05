package com.neven.launcher.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.R
import com.neven.launcher.data.FontSizeOption
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.ui.theme.*
import com.neven.launcher.ui.theme.rememberNevenColors
import kotlinx.coroutines.launch

/**
 * Pantalla de configuración de tamaño de letra
 * 
 * Permite seleccionar entre 6 tamaños:
 * - XS (0.75x) - Muy pequeño
 * - S (0.875x) - Pequeño
 * - M (1.0x) - Mediano (por defecto)
 * - L (1.125x) - Grande
 * - XL (1.25x) - Muy grande
 * - XXL (1.5x) - Extra grande
 * 
 * Incluye preview en tiempo real del tamaño seleccionado
 */
@Composable
fun FontSizeSettingsScreen(
    currentPalette: NevenPalette,
    isDarkMode: Boolean,
    currentFontSizeOption: FontSizeOption,
    onFontSizeChange: (FontSizeOption) -> Unit,
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
                
                // Símbolo científico: Aa (tamaño de letra)
                Text(
                    text = "Aa",
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = FontFamily.Serif
                    ),
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                Text(
                    text = stringResource(R.string.settings_font_size),
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
                verticalArrangement = Arrangement.spacedBy(32.dp)
            ) {
                // ─────────────────────────────────────────────────────────────
                // SELECTOR DE TAMAÑO
                // ─────────────────────────────────────────────────────────────
                FontSizeSelector(
                    currentOption = currentFontSizeOption,
                    onOptionChange = onFontSizeChange,
                    colors = colors
                )
                
                // ─────────────────────────────────────────────────────────────
                // PREVIEW EN TIEMPO REAL
                // ─────────────────────────────────────────────────────────────
                FontSizePreview(
                    fontSizeOption = currentFontSizeOption,
                    colors = colors
                )
            }
        }
}

/**
 * Selector visual de tamaño de letra con las 6 opciones
 */
@Composable
fun FontSizeSelector(
    currentOption: FontSizeOption,
    onOptionChange: (FontSizeOption) -> Unit,
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
            text = stringResource(R.string.settings_font_size_select),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // Grid de opciones 3x2
        Column(
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Primera fila: XS, S, M
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                FontSizeOption.values().take(3).forEach { option ->
                    FontSizeOptionChip(
                        option = option,
                        isSelected = option == currentOption,
                        colors = colors,
                        onClick = { onOptionChange(option) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }
            
            // Segunda fila: L, XL, XXL
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                FontSizeOption.values().drop(3).forEach { option ->
                    FontSizeOptionChip(
                        option = option,
                        isSelected = option == currentOption,
                        colors = colors,
                        onClick = { onOptionChange(option) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }
    }
}

/**
 * Chip individual para cada opción de tamaño
 * Estilo: botón seleccionado tiene SOLO BORDE/CONTORNO, el texto NO cambia de color
 */
@Composable
private fun FontSizeOptionChip(
    option: FontSizeOption,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    // Seleccionado: fondo transparente, solo borde con color accent
    // No seleccionado: fondo transparente, borde gris sutil
    val backgroundColor = Color.Transparent
    
    val borderColor = if (isSelected) {
        colors.accent
    } else {
        colors.textSecondary.copy(alpha = 0.3f)
    }
    
    Column(
        modifier = modifier
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
            .padding(vertical = 16.dp, horizontal = 12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        // Nombre de la opción (XS, S, M, L, XL, XXL)
        // El texto NO cambia de color, solo el borde indica selección
        Text(
            text = option.name,
            style = MaterialTheme.typography.titleLarge,
            fontFamily = NevenFontFamily,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
            color = colors.textSecondary
        )
        
        // Descripción localizada
        Text(
            text = getFontSizeDescription(option),
            style = MaterialTheme.typography.labelSmall,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary.copy(alpha = 0.7f)
        )
    }
}

/**
 * Obtiene la descripción para cada tamaño
 */
@Composable
private fun getFontSizeDescription(option: FontSizeOption): String {
    return when (option) {
        FontSizeOption.XS -> stringResource(R.string.font_size_xs)
        FontSizeOption.S -> stringResource(R.string.font_size_s)
        FontSizeOption.M -> stringResource(R.string.font_size_m)
        FontSizeOption.L -> stringResource(R.string.font_size_l)
        FontSizeOption.XL -> stringResource(R.string.font_size_xl)
        FontSizeOption.XXL -> stringResource(R.string.font_size_xxl)
    }
}

/**
 * Preview en tiempo real del tamaño de letra seleccionado
 */
@Composable
fun FontSizePreview(
    fontSizeOption: FontSizeOption,
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
            text = stringResource(R.string.settings_font_size_preview),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // Preview de texto con el tamaño aplicado
        val scale = fontSizeOption.scale
        
        Column(
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Título simulado
            Text(
                text = stringResource(R.string.font_size_preview_title),
                style = MaterialTheme.typography.headlineSmall.copy(
                    fontSize = (18 * scale).sp
                ),
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            
            // Texto body simulado
            Text(
                text = stringResource(R.string.font_size_preview_body),
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontSize = (14 * scale).sp,
                    lineHeight = (20 * scale).sp
                ),
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            // Etiqueta simulada
            Text(
                text = stringResource(R.string.font_size_preview_label),
                style = MaterialTheme.typography.labelMedium.copy(
                    fontSize = (12 * scale).sp
                ),
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary.copy(alpha = 0.7f)
            )
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Indicador de escala
        Text(
            text = "${stringResource(R.string.font_size_scale)}: ${(scale * 100).toInt()}%",
            style = MaterialTheme.typography.labelSmall,
            fontFamily = NevenFontFamily,
            color = colors.accent
        )
    }
}
