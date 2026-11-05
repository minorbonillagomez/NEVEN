package com.neven.launcher.ui.notifications

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.data.NotificationPopupSize
import com.neven.launcher.data.ScientificNotification
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * Notificación flotante estilo Paper Científico
 * 
 * Diseño elegante como una hoja de papel académico:
 * - Sombra para efecto de profundidad
 * - Bordes sutiles
 * - Header con nombre del journal
 * - Cuerpo con autor y abstract
 * - Footer con acciones
 * - Botón "CERRAR TODO" cuando hay múltiples popups
 * 
 * El usuario puede arrastrar esta ventana por la pantalla
 */
@Composable
fun FloatingPaperNotification(
    notification: ScientificNotification,
    colors: NevenColors,
    popupSize: NotificationPopupSize,
    renderLatex: Boolean,
    showTimestamp: Boolean,
    quickReplyEnabled: Boolean,
    showDismissAll: Boolean = false,
    popupCount: Int = 1,
    onDismiss: () -> Unit,
    onDismissAll: () -> Unit = {},
    onReply: (String) -> Unit,
    onOpenApp: () -> Unit
) {
    var replyText by remember { mutableStateOf("") }
    var showReplyField by remember { mutableStateOf(false) }
    
    // Calcular dimensiones basadas en el tamaño seleccionado
    val paperWidth = when (popupSize) {
        NotificationPopupSize.COMPACT -> 300.dp
        NotificationPopupSize.NORMAL -> 340.dp
        NotificationPopupSize.EXPANDED -> 380.dp
    }
    
    Box(
        modifier = Modifier
            .width(paperWidth)
            .shadow(
                elevation = 16.dp,
                shape = RoundedCornerShape(4.dp),
                ambientColor = Color.Black.copy(alpha = 0.3f),
                spotColor = Color.Black.copy(alpha = 0.3f)
            )
            .clip(RoundedCornerShape(4.dp))
            .background(colors.background)
            .border(
                width = 1.dp,
                color = colors.textSecondary.copy(alpha = 0.15f),
                shape = RoundedCornerShape(4.dp)
            )
    ) {
        Column {
            // ═══════════════════════════════════════════════════════════════
            // HEADER - Barra de título arrastrable
            // ═══════════════════════════════════════════════════════════════
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(colors.accent.copy(alpha = 0.08f))
                    .padding(horizontal = 16.dp, vertical = 10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Indicador de arrastre + contador si hay múltiples
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "⋮⋮",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textSecondary.copy(alpha = 0.4f)
                        )
                        
                        if (popupCount > 1) {
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "($popupCount)",
                                style = MaterialTheme.typography.labelSmall.copy(
                                    fontFamily = NevenFontFamily,
                                    fontWeight = FontWeight.Medium
                                ),
                                color = colors.accent.copy(alpha = 0.7f)
                            )
                        }
                    }
                    
                    // Nombre del Journal (app)
                    Text(
                        text = notification.journalName,
                        style = MaterialTheme.typography.labelMedium.copy(
                            fontFamily = FontFamily.Serif,
                            letterSpacing = 3.sp,
                            fontWeight = FontWeight.Normal
                        ),
                        color = colors.textSecondary
                    )
                    
                    // Botón cerrar
                    Text(
                        text = "×",
                        modifier = Modifier
                            .clickable { onDismiss() }
                            .padding(4.dp),
                        style = MaterialTheme.typography.titleMedium,
                        color = colors.textSecondary.copy(alpha = 0.6f)
                    )
                }
            }
            
            // Línea decorativa bajo el header
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.dp)
                    .background(colors.textSecondary.copy(alpha = 0.1f))
            )
            
            // ═══════════════════════════════════════════════════════════════
            // CUERPO DEL PAPER
            // ═══════════════════════════════════════════════════════════════
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                when (popupSize) {
                    NotificationPopupSize.COMPACT -> {
                        CompactContent(
                            notification = notification,
                            colors = colors,
                            showTimestamp = showTimestamp,
                            onOpenApp = onOpenApp
                        )
                    }
                    else -> {
                        FullContent(
                            notification = notification,
                            colors = colors,
                            showTimestamp = showTimestamp,
                            maxLines = popupSize.maxLines,
                            onOpenApp = onOpenApp
                        )
                    }
                }
            }
            
            // ═══════════════════════════════════════════════════════════════
            // FOOTER - Acciones
            // ═══════════════════════════════════════════════════════════════
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.dp)
                    .background(colors.textSecondary.copy(alpha = 0.08f))
            )
            
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(colors.accent.copy(alpha = 0.03f))
                    .padding(12.dp)
            ) {
                if (showReplyField && quickReplyEnabled && notification.replyAction != null) {
                    // Campo de respuesta
                    Column {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .border(
                                    width = 1.dp,
                                    color = colors.textSecondary.copy(alpha = 0.2f),
                                    shape = RoundedCornerShape(4.dp)
                                )
                                .background(
                                    colors.background,
                                    RoundedCornerShape(4.dp)
                                )
                                .padding(10.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            BasicTextField(
                                value = replyText,
                                onValueChange = { replyText = it },
                                modifier = Modifier.weight(1f),
                                textStyle = TextStyle(
                                    fontFamily = NevenFontFamily,
                                    fontSize = 14.sp,
                                    color = colors.textPrimary
                                ),
                                cursorBrush = SolidColor(colors.accent),
                                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                                keyboardActions = KeyboardActions(
                                    onSend = {
                                        if (replyText.isNotBlank()) {
                                            onReply(replyText)
                                        }
                                    }
                                ),
                                decorationBox = { innerTextField ->
                                    if (replyText.isEmpty()) {
                                        Text(
                                            text = "Respuesta...",
                                            style = TextStyle(
                                                fontFamily = NevenFontFamily,
                                                fontSize = 14.sp,
                                                fontStyle = FontStyle.Italic,
                                                color = colors.textSecondary.copy(alpha = 0.4f)
                                            )
                                        )
                                    }
                                    innerTextField()
                                }
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.End
                        ) {
                            ActionChip(
                                text = "Cancelar",
                                onClick = { showReplyField = false },
                                colors = colors,
                                isPrimary = false
                            )
                            
                            Spacer(modifier = Modifier.width(8.dp))
                            
                            ActionChip(
                                text = "Enviar",
                                onClick = {
                                    if (replyText.isNotBlank()) {
                                        onReply(replyText)
                                    }
                                },
                                colors = colors,
                                isPrimary = true,
                                enabled = replyText.isNotBlank()
                            )
                        }
                    }
                } else {
                    // Botones de acción
                    Column {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Izquierda: Responder (si aplica)
                            if (quickReplyEnabled && notification.replyAction != null) {
                                ActionChip(
                                    text = "Responder",
                                    onClick = { showReplyField = true },
                                    colors = colors,
                                    isPrimary = false
                                )
                            } else {
                                Spacer(modifier = Modifier.width(1.dp))
                            }
                            
                            // Derecha: Abrir y OK
                            Row {
                                ActionChip(
                                    text = "Abrir",
                                    onClick = onOpenApp,
                                    colors = colors,
                                    isPrimary = false
                                )
                                
                                Spacer(modifier = Modifier.width(8.dp))
                                
                                ActionChip(
                                    text = "OK",
                                    onClick = onDismiss,
                                    colors = colors,
                                    isPrimary = true
                                )
                            }
                        }
                        
                        // Botón "CERRAR TODO" cuando hay múltiples popups
                        if (showDismissAll && popupCount > 1) {
                            Spacer(modifier = Modifier.height(8.dp))
                            
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable { onDismissAll() }
                                    .background(
                                        colors.textSecondary.copy(alpha = 0.08f),
                                        RoundedCornerShape(4.dp)
                                    )
                                    .padding(vertical = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "CERRAR TODO ($popupCount)",
                                    style = MaterialTheme.typography.labelMedium.copy(
                                        fontFamily = NevenFontFamily,
                                        fontWeight = FontWeight.Medium,
                                        letterSpacing = 1.sp
                                    ),
                                    color = colors.textSecondary
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

/**
 * Contenido compacto para popup pequeño
 */
@Composable
private fun CompactContent(
    notification: ScientificNotification,
    colors: NevenColors,
    showTimestamp: Boolean,
    onOpenApp: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onOpenApp() },
        horizontalAlignment = Alignment.Start
    ) {
        // Autor
        Text(
            text = notification.author,
            style = MaterialTheme.typography.titleMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold
            ),
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(6.dp))
        
        // Preview del mensaje
        Text(
            text = notification.content,
            style = MaterialTheme.typography.bodyMedium.copy(
                fontFamily = NevenFontFamily,
                lineHeight = 20.sp
            ),
            color = colors.textPrimary.copy(alpha = 0.85f),
            maxLines = 3,
            overflow = TextOverflow.Ellipsis
        )
        
        if (showTimestamp) {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = notification.timestampShort,
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic
                ),
                color = colors.textSecondary.copy(alpha = 0.5f)
            )
        }
    }
}

/**
 * Contenido completo estilo paper
 */
@Composable
private fun FullContent(
    notification: ScientificNotification,
    colors: NevenColors,
    showTimestamp: Boolean,
    maxLines: Int,
    onOpenApp: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Autor (centrado, destacado)
        Text(
            text = notification.author,
            style = MaterialTheme.typography.titleLarge.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            ),
            color = colors.textPrimary,
            textAlign = TextAlign.Center
        )
        
        // Afiliación
        Text(
            text = notification.affiliation,
            style = MaterialTheme.typography.bodySmall.copy(
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic
            ),
            color = colors.textSecondary.copy(alpha = 0.7f),
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Línea decorativa
        Box(
            modifier = Modifier
                .width(40.dp)
                .height(1.dp)
                .background(colors.textSecondary.copy(alpha = 0.2f))
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        // Etiqueta "Abstract"
        Text(
            text = "Abstract",
            style = MaterialTheme.typography.labelSmall.copy(
                fontFamily = FontFamily.Serif,
                fontStyle = FontStyle.Italic,
                letterSpacing = 1.sp
            ),
            color = colors.textSecondary.copy(alpha = 0.6f)
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Contenido del mensaje
        Text(
            text = notification.content,
            style = MaterialTheme.typography.bodyMedium.copy(
                fontFamily = NevenFontFamily,
                lineHeight = 22.sp
            ),
            color = colors.textPrimary.copy(alpha = 0.9f),
            textAlign = TextAlign.Justify,
            maxLines = maxLines,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onOpenApp() }
        )
        
        if (showTimestamp) {
            Spacer(modifier = Modifier.height(12.dp))
            
            Text(
                text = "Received: ${notification.timestampFormatted}",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic
                ),
                color = colors.textSecondary.copy(alpha = 0.5f)
            )
        }
    }
}

/**
 * Chip de acción estilo académico
 */
@Composable
private fun ActionChip(
    text: String,
    onClick: () -> Unit,
    colors: NevenColors,
    isPrimary: Boolean,
    enabled: Boolean = true
) {
    val backgroundColor = when {
        !enabled -> colors.textSecondary.copy(alpha = 0.1f)
        isPrimary -> colors.accent.copy(alpha = 0.15f)
        else -> Color.Transparent
    }
    
    val textColor = when {
        !enabled -> colors.textSecondary.copy(alpha = 0.4f)
        isPrimary -> colors.accent
        else -> colors.textSecondary
    }
    
    val borderColor = when {
        isPrimary -> colors.accent.copy(alpha = 0.3f)
        else -> colors.textSecondary.copy(alpha = 0.2f)
    }
    
    Text(
        text = text,
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(backgroundColor)
            .border(
                width = 1.dp,
                color = if (enabled) borderColor else Color.Transparent,
                shape = RoundedCornerShape(4.dp)
            )
            .clickable(enabled = enabled) { onClick() }
            .padding(horizontal = 14.dp, vertical = 8.dp),
        style = MaterialTheme.typography.labelMedium.copy(
            fontFamily = NevenFontFamily,
            fontWeight = if (isPrimary) FontWeight.SemiBold else FontWeight.Normal
        ),
        color = textColor
    )
}
