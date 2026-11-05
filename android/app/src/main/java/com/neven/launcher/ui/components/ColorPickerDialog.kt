package com.neven.launcher.ui.components

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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.neven.launcher.R
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * Diálogo de selección de color personalizado con sliders RGB.
 * Diseño científico y sobrio sin emojis.
 */
@Composable
fun ColorPickerDialog(
    initialColor: Color,
    colors: NevenColors,
    onDismiss: () -> Unit,
    onColorSelected: (Color) -> Unit
) {
    // Estados para RGB
    var red by remember { mutableFloatStateOf(initialColor.red) }
    var green by remember { mutableFloatStateOf(initialColor.green) }
    var blue by remember { mutableFloatStateOf(initialColor.blue) }
    
    // Color resultante
    val resultColor = Color(red, green, blue)
    
    val dialogBg = if (colors.isDark) {
        Color(0xFF1B1B1B)
    } else {
        Color(0xFFFAF9F6)
    }
    
    Dialog(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    color = dialogBg,
                    shape = RoundedCornerShape(16.dp)
                )
                .border(
                    width = 0.5.dp, // Borde delgado minimalista
                    color = colors.textSecondary.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(16.dp)
                )
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Título
            Text(
                text = stringResource(R.string.color_picker_title),
                style = MaterialTheme.typography.titleLarge,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            
            // Preview del color
            Column(
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    text = stringResource(R.string.color_picker_preview),
                    style = MaterialTheme.typography.labelMedium,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Cuadrado de preview
                    Box(
                        modifier = Modifier
                            .size(56.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(resultColor)
                            .border(
                                width = 0.5.dp, // Borde delgado minimalista
                                color = colors.textSecondary.copy(alpha = 0.3f),
                                shape = RoundedCornerShape(8.dp)
                            )
                    )
                    
                    // Valor hexadecimal
                    Text(
                        text = colorToHex(resultColor),
                        style = MaterialTheme.typography.bodyLarge,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Medium,
                        color = colors.textPrimary
                    )
                }
            }
            
            // Sliders RGB
            Column(
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Red
                ColorSlider(
                    label = "R",
                    value = red,
                    onValueChange = { red = it },
                    sliderColor = Color.Red,
                    colors = colors
                )
                
                // Green
                ColorSlider(
                    label = "G",
                    value = green,
                    onValueChange = { green = it },
                    sliderColor = Color.Green,
                    colors = colors
                )
                
                // Blue
                ColorSlider(
                    label = "B",
                    value = blue,
                    onValueChange = { blue = it },
                    sliderColor = Color.Blue,
                    colors = colors
                )
            }
            
            // Botones
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp, Alignment.End)
            ) {
                // Cancelar
                TextButton(
                    onClick = onDismiss,
                    modifier = Modifier
                        .border(
                            width = 0.5.dp, // Borde delgado minimalista
                            color = colors.textSecondary.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(8.dp)
                        )
                ) {
                    Text(
                        text = stringResource(R.string.notes_cancel),
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
                
                // Aplicar
                TextButton(
                    onClick = { onColorSelected(resultColor) },
                    modifier = Modifier
                        .border(
                            width = 0.5.dp, // Borde delgado minimalista
                            color = colors.accent,
                            shape = RoundedCornerShape(8.dp)
                        )
                ) {
                    Text(
                        text = stringResource(R.string.color_picker_apply),
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.accent
                    )
                }
            }
        }
    }
}

/**
 * Slider individual para un canal de color (R, G o B)
 */
@Composable
private fun ColorSlider(
    label: String,
    value: Float,
    onValueChange: (Float) -> Unit,
    sliderColor: Color,
    colors: NevenColors
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Label
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.Bold,
            color = sliderColor.copy(alpha = 0.8f),
            modifier = Modifier.width(24.dp)
        )
        
        // Slider
        Slider(
            value = value,
            onValueChange = onValueChange,
            valueRange = 0f..1f,
            modifier = Modifier.weight(1f),
            colors = SliderDefaults.colors(
                thumbColor = sliderColor,
                activeTrackColor = sliderColor,
                inactiveTrackColor = sliderColor.copy(alpha = 0.2f)
            )
        )
        
        // Valor numérico (0-255)
        Text(
            text = (value * 255).toInt().toString().padStart(3, ' '),
            style = MaterialTheme.typography.labelMedium,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary,
            modifier = Modifier.width(32.dp)
        )
    }
}

/**
 * Convierte un Color a su representación hexadecimal
 */
fun colorToHex(color: Color): String {
    val r = (color.red * 255).toInt()
    val g = (color.green * 255).toInt()
    val b = (color.blue * 255).toInt()
    return String.format("#%02X%02X%02X", r, g, b)
}

/**
 * Convierte una cadena hexadecimal a Color
 */
fun hexToColor(hex: String): Color {
    return try {
        val cleanHex = hex.removePrefix("#")
        val colorInt = cleanHex.toLong(16)
        Color(
            red = ((colorInt shr 16) and 0xFF) / 255f,
            green = ((colorInt shr 8) and 0xFF) / 255f,
            blue = (colorInt and 0xFF) / 255f
        )
    } catch (e: Exception) {
        Color(0xFFD32F2F) // Rojo por defecto
    }
}

/**
 * Presets de colores científicos para el selector
 */
object AccentColorPresets {
    val RED = Color(0xFFD32F2F)           // Rojo - default
    val COBALT_BLUE = Color(0xFF1976D2)   // Azul cobalto
    val EMERALD = Color(0xFF388E3C)       // Verde esmeralda
    val ORANGE = Color(0xFFF57C00)        // Naranja
    val CYAN = Color(0xFF0097A7)          // Cyan
    val MAGENTA = Color(0xFFC2185B)       // Magenta
    val GOLD = Color(0xFFFFA000)          // Dorado
    val WHITE = Color(0xFFFFFFFF)         // Blanco
    
    val all = listOf(
        RED to "#D32F2F",
        COBALT_BLUE to "#1976D2",
        EMERALD to "#388E3C",
        ORANGE to "#F57C00",
        CYAN to "#0097A7",
        MAGENTA to "#C2185B",
        GOLD to "#FFA000",
        WHITE to "#FFFFFF"
    )
}
