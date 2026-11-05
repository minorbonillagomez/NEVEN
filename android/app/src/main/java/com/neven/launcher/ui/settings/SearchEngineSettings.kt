package com.neven.launcher.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.neven.launcher.R
import com.neven.launcher.data.SearchEngine
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * Componente de configuración del motor de búsqueda.
 * 
 * Opciones disponibles:
 * - Google
 * - Bing
 * - DuckDuckGo
 * - Ecosia
 */
@Composable
fun SearchEngineSelector(
    currentEngine: SearchEngine,
    onEngineChange: (SearchEngine) -> Unit,
    colors: NevenColors
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Título de sección
        Text(
            text = stringResource(R.string.settings_search_engine),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Opciones de motor de búsqueda
        SearchEngine.values().forEach { engine ->
            SearchEngineOption(
                engine = engine,
                isSelected = engine == currentEngine,
                colors = colors,
                onClick = { onEngineChange(engine) }
            )
        }
    }
}

/**
 * Opción individual de motor de búsqueda
 * Estilo: botón seleccionado tiene SOLO BORDE/CONTORNO, el texto NO cambia de color
 */
@Composable
private fun SearchEngineOption(
    engine: SearchEngine,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    // Seleccionado: fondo transparente, solo borde con color accent
    // No seleccionado: fondo transparente, borde gris sutil
    val backgroundColor = Color.Transparent
    
    val borderColor = if (isSelected) {
        colors.accent
    } else {
        colors.textSecondary.copy(alpha = 0.15f)
    }
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))   // Clip primero para ripple correcto
            .clickable(onClick = onClick)      // Clickable ANTES del background para que funcione
            .background(
                color = backgroundColor,
                shape = RoundedCornerShape(8.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = borderColor,
                shape = RoundedCornerShape(8.dp)
            )
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Radio button
        RadioButton(
            selected = isSelected,
            onClick = onClick,
            colors = RadioButtonDefaults.colors(
                selectedColor = colors.accent,
                unselectedColor = colors.textSecondary
            )
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        Column {
            // Nombre del motor - texto NO cambia de color, solo el borde indica selección
            Text(
                text = engine.displayName,
                style = MaterialTheme.typography.bodyLarge,
                fontFamily = NevenFontFamily,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                color = colors.textPrimary
            )
            
            // Descripción breve
            Text(
                text = getEngineDescription(engine),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary
            )
        }
    }
}

/**
 * Obtiene la descripción del motor de búsqueda
 */
private fun getEngineDescription(engine: SearchEngine): String {
    return when (engine) {
        SearchEngine.GOOGLE -> "Resultados rápidos y completos"
        SearchEngine.BING -> "Integración con Microsoft"
        SearchEngine.DUCKDUCKGO -> "Privacidad sin seguimiento"
        SearchEngine.ECOSIA -> "Planta árboles al buscar"
    }
}

/**
 * Card completa para la sección de motor de búsqueda en Settings
 */
@Composable
fun SearchEngineSettingsCard(
    currentEngine: SearchEngine,
    onEngineChange: (SearchEngine) -> Unit,
    colors: NevenColors
) {
    val cardBg = if (colors.isDark) {
        Color(0xFF1B1B1B).copy(alpha = 0.82f)
    } else {
        Color(0xFFFAF9F6).copy(alpha = 0.9f)
    }
    val borderColor = colors.textSecondary.copy(alpha = 0.12f)
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = cardBg,
                shape = RoundedCornerShape(16.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = borderColor,
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        // Header con símbolo de sección
        Text(
            text = "§ ${stringResource(R.string.settings_search_engine)}",
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            color = colors.textPrimary,
            fontWeight = FontWeight.SemiBold
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Selector
        SearchEngineSelector(
            currentEngine = currentEngine,
            onEngineChange = onEngineChange,
            colors = colors
        )
    }
}
