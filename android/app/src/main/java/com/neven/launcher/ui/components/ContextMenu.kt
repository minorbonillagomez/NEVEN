package com.neven.launcher.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Popup
import androidx.compose.ui.window.PopupProperties
import com.neven.launcher.R
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * Menú contextual estilo NEVEN (minimalista, académico)
 * 
 * Usado para:
 * - Long-press en apps del drawer → "Agregar a favoritos"
 * - Long-press en favoritos del home → "Quitar de favoritos"
 */

/**
 * Opción del menú contextual
 */
data class ContextMenuOption(
    val id: String,
    val label: String,
    val icon: String = "▸" // Símbolo LaTeX por defecto
)

/**
 * Menú contextual popup
 */
@Composable
fun NevenContextMenu(
    visible: Boolean,
    options: List<ContextMenuOption>,
    colors: NevenColors,
    onOptionSelected: (String) -> Unit,
    onDismiss: () -> Unit
) {
    if (visible) {
        Popup(
            alignment = Alignment.Center,
            onDismissRequest = onDismiss,
            properties = PopupProperties(focusable = true)
        ) {
            ContextMenuContent(
                options = options,
                colors = colors,
                onOptionSelected = { id ->
                    onOptionSelected(id)
                    onDismiss()
                },
                onDismiss = onDismiss
            )
        }
    }
}

/**
 * Contenido del menú contextual
 */
@Composable
private fun ContextMenuContent(
    options: List<ContextMenuOption>,
    colors: NevenColors,
    onOptionSelected: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val cardBg = if (colors.isDark) {
        Color(0xFF1B1B1B).copy(alpha = 0.95f)
    } else {
        Color(0xFFFAF9F6).copy(alpha = 0.98f)
    }
    val borderColor = colors.textSecondary.copy(alpha = 0.2f)
    
    Column(
        modifier = Modifier
            .background(
                color = cardBg,
                shape = RoundedCornerShape(12.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = borderColor,
                shape = RoundedCornerShape(12.dp)
            )
            .padding(8.dp)
            .widthIn(min = 180.dp, max = 280.dp)
    ) {
        options.forEachIndexed { index, option ->
            ContextMenuItem(
                option = option,
                colors = colors,
                onClick = { onOptionSelected(option.id) }
            )
            
            // Separador sutil entre opciones
            if (index < options.lastIndex) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                        .height(1.dp)
                        .background(colors.textSecondary.copy(alpha = 0.1f))
                )
            }
        }
    }
}

/**
 * Ítem individual del menú
 */
@Composable
private fun ContextMenuItem(
    option: ContextMenuOption,
    colors: NevenColors,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Símbolo LaTeX
        Text(
            text = option.icon,
            style = MaterialTheme.typography.bodyMedium,
            color = colors.accent
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        // Label
        Text(
            text = option.label,
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textPrimary
        )
    }
}

/**
 * Menú contextual predefinido para agregar a favoritos
 */
@Composable
fun AddToFavoritesMenu(
    visible: Boolean,
    appName: String,
    colors: NevenColors,
    onAddToFavorites: () -> Unit,
    onAppInfo: () -> Unit,
    onDismiss: () -> Unit
) {
    val options = listOf(
        ContextMenuOption(
            id = "add_favorite",
            label = stringResource(R.string.menu_add_favorite),
            icon = "★"
        ),
        ContextMenuOption(
            id = "app_info",
            label = stringResource(R.string.menu_app_info),
            icon = "ⓘ"
        )
    )
    
    NevenContextMenu(
        visible = visible,
        options = options,
        colors = colors,
        onOptionSelected = { id ->
            when (id) {
                "add_favorite" -> onAddToFavorites()
                "app_info" -> onAppInfo()
            }
        },
        onDismiss = onDismiss
    )
}

/**
 * Menú contextual predefinido para quitar de favoritos
 */
@Composable
fun RemoveFromFavoritesMenu(
    visible: Boolean,
    appName: String,
    colors: NevenColors,
    onRemoveFromFavorites: () -> Unit,
    onAppInfo: () -> Unit,
    onDismiss: () -> Unit
) {
    val options = listOf(
        ContextMenuOption(
            id = "remove_favorite",
            label = stringResource(R.string.menu_remove_favorite),
            icon = "☆"
        ),
        ContextMenuOption(
            id = "app_info",
            label = stringResource(R.string.menu_app_info),
            icon = "ⓘ"
        )
    )
    
    NevenContextMenu(
        visible = visible,
        options = options,
        colors = colors,
        onOptionSelected = { id ->
            when (id) {
                "remove_favorite" -> onRemoveFromFavorites()
                "app_info" -> onAppInfo()
            }
        },
        onDismiss = onDismiss
    )
}

/**
 * Estado para manejar el menú contextual
 */
@Composable
fun rememberContextMenuState(): ContextMenuState {
    return remember { ContextMenuState() }
}

class ContextMenuState {
    var isVisible by mutableStateOf(false)
        private set
    
    var selectedItem: String? by mutableStateOf(null)
        private set
    
    fun show(itemId: String) {
        selectedItem = itemId
        isVisible = true
    }
    
    fun dismiss() {
        isVisible = false
        selectedItem = null
    }
}
