package com.neven.launcher.ui.notes

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Note
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Widgets
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Popup
import androidx.compose.ui.window.PopupProperties
import com.neven.launcher.ui.theme.NevenColors
import kotlin.math.roundToInt

/**
 * Accion disponible en el menu contextual de la pagina
 */
data class PageAction(
    val id: String,
    val title: String,
    val icon: ImageVector,
    val onClick: () -> Unit
)

/**
 * Menu contextual que aparece con long-press en una pagina
 * 
 * Muestra acciones disponibles como crear notas, etc.
 * Diseñado para ser extensible con mas acciones en el futuro.
 */
@Composable
fun PageActionMenu(
    isVisible: Boolean,
    position: Offset,
    actions: List<PageAction>,
    onDismiss: () -> Unit,
    colors: NevenColors
) {
    if (!isVisible) return
    
    Popup(
        onDismissRequest = onDismiss,
        properties = PopupProperties(
            focusable = true,
            dismissOnBackPress = true,
            dismissOnClickOutside = true
        ),
        offset = IntOffset(
            x = position.x.roundToInt() - 80, // Centrar horizontalmente
            y = position.y.roundToInt() - 20
        )
    ) {
        Card(
            modifier = Modifier
                .width(180.dp)
                .shadow(8.dp, RoundedCornerShape(12.dp)),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(
                containerColor = colors.background
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
        ) {
            Column(
                modifier = Modifier.padding(8.dp)
            ) {
                actions.forEachIndexed { index, action ->
                    PageActionItem(
                        action = action,
                        colors = colors,
                        onDismiss = onDismiss
                    )
                    
                    if (index < actions.size - 1) {
                        Divider(
                            modifier = Modifier.padding(vertical = 4.dp),
                            color = colors.textSecondary.copy(alpha = 0.1f)
                        )
                    }
                }
            }
        }
    }
}

/**
 * Item individual del menu
 */
@Composable
private fun PageActionItem(
    action: PageAction,
    colors: NevenColors,
    onDismiss: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .clickable {
                action.onClick()
                onDismiss()
            }
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Start
    ) {
        Icon(
            imageVector = action.icon,
            contentDescription = action.title,
            tint = colors.accent,
            modifier = Modifier.size(20.dp)
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        Text(
            text = action.title,
            style = MaterialTheme.typography.bodyMedium,
            color = colors.textPrimary
        )
    }
}

/**
 * Acciones predefinidas para el menu
 */
object PageActions {
    fun createNote(onClick: () -> Unit) = PageAction(
        id = "create_note",
        title = "Nueva nota",
        icon = Icons.Default.Note,
        onClick = onClick
    )
    
    // Acciones futuras
    fun addWidget(onClick: () -> Unit) = PageAction(
        id = "add_widget",
        title = "Agregar widget",
        icon = Icons.Default.Widgets,
        onClick = onClick
    )
    
    fun pageSettings(onClick: () -> Unit) = PageAction(
        id = "page_settings",
        title = "Configurar pagina",
        icon = Icons.Default.Settings,
        onClick = onClick
    )
}
