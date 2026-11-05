package com.neven.launcher.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * NEVEN Settings Item - Componente reutilizable para items de configuración
 * 
 * Estilo científico/académico sobrio:
 * - Símbolo a la izquierda en tipografía serif (un solo color)
 * - Título en negrita + descripción en gris debajo
 * - Espaciado generoso como paper académico
 * - Sin emojis, sin colores múltiples
 */
@Composable
fun SettingsItem(
    symbol: String,        // Símbolo científico: ∂, λ, Aa, ∘, ≡, τ, ξ, §
    title: String,         // Título principal
    description: String,   // Descripción secundaria
    onClick: () -> Unit,   // Acción al hacer click
    colors: NevenColors,   // Colores del tema actual
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 20.dp, horizontal = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // ═══════════════════════════════════════════════════════════════
        // SÍMBOLO CIENTÍFICO
        // Tipografía serif, un solo color (primario de la paleta)
        // ═══════════════════════════════════════════════════════════════
        Box(
            modifier = Modifier.width(48.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = symbol,
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif,
                    fontWeight = FontWeight.Normal,
                    fontSize = 24.sp
                ),
                color = colors.accent  // Un solo color: el acento de la paleta
            )
        }
        
        Spacer(modifier = Modifier.width(16.dp))
        
        // ═══════════════════════════════════════════════════════════════
        // TEXTO: TÍTULO Y DESCRIPCIÓN
        // ═══════════════════════════════════════════════════════════════
        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            // Título en negrita
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.SemiBold
                ),
                color = colors.textPrimary
            )
            
            // Descripción en gris
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall.copy(
                    fontFamily = NevenFontFamily
                ),
                color = colors.textSecondary
            )
        }
        
        // ═══════════════════════════════════════════════════════════════
        // FLECHA DE NAVEGACIÓN
        // ═══════════════════════════════════════════════════════════════
        Text(
            text = ">",
            style = MaterialTheme.typography.titleMedium.copy(
                fontFamily = FontFamily.Serif
            ),
            color = colors.textSecondary.copy(alpha = 0.5f)
        )
    }
}

/**
 * Versión compacta del SettingsItem para listas más densas
 */
@Composable
fun SettingsItemCompact(
    symbol: String,
    title: String,
    onClick: () -> Unit,
    colors: NevenColors,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 14.dp, horizontal = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Símbolo
        Box(
            modifier = Modifier.width(40.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = symbol,
                style = MaterialTheme.typography.titleLarge.copy(
                    fontFamily = FontFamily.Serif,
                    fontWeight = FontWeight.Normal
                ),
                color = colors.accent
            )
        }
        
        Spacer(modifier = Modifier.width(12.dp))
        
        // Título
        Text(
            text = title,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.bodyLarge.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            ),
            color = colors.textPrimary
        )
        
        // Flecha
        Text(
            text = ">",
            style = MaterialTheme.typography.bodyLarge.copy(
                fontFamily = FontFamily.Serif
            ),
            color = colors.textSecondary.copy(alpha = 0.5f)
        )
    }
}
