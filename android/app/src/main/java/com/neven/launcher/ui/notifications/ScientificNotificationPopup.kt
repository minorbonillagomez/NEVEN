package com.neven.launcher.ui.notifications

import android.content.Intent
import android.os.Bundle
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.neven.launcher.data.NotificationPopupSize
import com.neven.launcher.data.ScientificNotification
import com.neven.launcher.ui.markdown.MarkdownWebView
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * Popup de notificación estilo Paper Científico
 * 
 * Diseño basado en publicaciones académicas LaTeX:
 * - TÍTULO: Nombre de la aplicación (journal)
 * - AUTOR: Remitente del mensaje
 * - AFILIACIÓN: Tipo de servicio
 * - ABSTRACT: Contenido del mensaje
 * - RECEIVED: Timestamp
 * 
 * Soporta renderizado de LaTeX via KaTeX
 */
@Composable
fun ScientificNotificationPopup(
    notification: ScientificNotification,
    colors: NevenColors,
    popupSize: NotificationPopupSize,
    renderLatex: Boolean,
    showTimestamp: Boolean,
    quickReplyEnabled: Boolean,
    onDismiss: () -> Unit,
    onReply: (String) -> Unit,
    onOpenApp: () -> Unit
) {
    val context = LocalContext.current
    var replyText by remember { mutableStateOf("") }
    var showReplyField by remember { mutableStateOf(false) }
    
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(
            dismissOnBackPress = true,
            dismissOnClickOutside = true,
            usePlatformDefaultWidth = false
        )
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth(popupSize.widthFraction)
                .clip(RoundedCornerShape(8.dp))
                .background(colors.background.copy(alpha = 0.97f))
                .border(
                    width = 1.dp,
                    color = colors.textSecondary.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(8.dp)
                )
        ) {
            Column(
                modifier = Modifier
                    .padding(24.dp)
                    .verticalScroll(rememberScrollState()),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                when (popupSize) {
                    NotificationPopupSize.COMPACT -> {
                        CompactPaperLayout(
                            notification = notification,
                            colors = colors,
                            showTimestamp = showTimestamp,
                            onOpenApp = onOpenApp
                        )
                    }
                    NotificationPopupSize.NORMAL, NotificationPopupSize.EXPANDED -> {
                        FullPaperLayout(
                            notification = notification,
                            colors = colors,
                            renderLatex = renderLatex,
                            showTimestamp = showTimestamp,
                            maxLines = popupSize.maxLines,
                            onOpenApp = onOpenApp
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(20.dp))
                
                // ═══════════════════════════════════════════════════════════
                // BOTONES DE ACCIÓN
                // ═══════════════════════════════════════════════════════════
                if (quickReplyEnabled && notification.replyAction != null) {
                    if (showReplyField) {
                        // Campo de texto para responder
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .border(
                                    width = 1.dp,
                                    color = colors.textSecondary.copy(alpha = 0.3f),
                                    shape = RoundedCornerShape(4.dp)
                                )
                                .padding(8.dp),
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
                                            text = "Escribe tu respuesta...",
                                            style = TextStyle(
                                                fontFamily = NevenFontFamily,
                                                fontSize = 14.sp,
                                                fontStyle = FontStyle.Italic,
                                                color = colors.textSecondary.copy(alpha = 0.5f)
                                            )
                                        )
                                    }
                                    innerTextField()
                                }
                            )
                            
                            Spacer(modifier = Modifier.width(8.dp))
                            
                            Text(
                                text = "ENVIAR",
                                modifier = Modifier
                                    .clickable {
                                        if (replyText.isNotBlank()) {
                                            onReply(replyText)
                                        }
                                    }
                                    .padding(8.dp),
                                style = MaterialTheme.typography.labelMedium.copy(
                                    fontFamily = NevenFontFamily,
                                    fontWeight = FontWeight.Bold,
                                    letterSpacing = 1.sp
                                ),
                                color = if (replyText.isNotBlank()) colors.accent else colors.textSecondary
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(12.dp))
                        
                        // Botón cancelar respuesta
                        PaperButton(
                            text = "CANCELAR",
                            onClick = { showReplyField = false },
                            colors = colors,
                            isPrimary = false
                        )
                    } else {
                        // Botones principales con respuesta rápida
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceEvenly
                        ) {
                            PaperButton(
                                text = "RESPONDER",
                                onClick = { showReplyField = true },
                                colors = colors,
                                isPrimary = false
                            )
                            
                            PaperButton(
                                text = "ABRIR",
                                onClick = onOpenApp,
                                colors = colors,
                                isPrimary = false
                            )
                            
                            PaperButton(
                                text = "OK",
                                onClick = onDismiss,
                                colors = colors,
                                isPrimary = true
                            )
                        }
                    }
                } else {
                    // Botones sin respuesta rápida
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        PaperButton(
                            text = "ABRIR",
                            onClick = onOpenApp,
                            colors = colors,
                            isPrimary = false
                        )
                        
                        PaperButton(
                            text = "OK",
                            onClick = onDismiss,
                            colors = colors,
                            isPrimary = true
                        )
                    }
                }
            }
        }
    }
}

/**
 * Layout compacto (4x2) - Solo lo esencial
 */
@Composable
private fun CompactPaperLayout(
    notification: ScientificNotification,
    colors: NevenColors,
    showTimestamp: Boolean,
    onOpenApp: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onOpenApp() },
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Journal (app name)
        Text(
            text = notification.journalName,
            style = MaterialTheme.typography.labelMedium.copy(
                fontFamily = FontFamily.Serif,
                fontWeight = FontWeight.Normal,
                letterSpacing = 4.sp
            ),
            color = colors.textSecondary
        )
        
        // Línea decorativa
        Spacer(modifier = Modifier.height(4.dp))
        Box(
            modifier = Modifier
                .width(60.dp)
                .height(1.dp)
                .background(colors.textSecondary.copy(alpha = 0.3f))
        )
        Spacer(modifier = Modifier.height(8.dp))
        
        // Autor
        Text(
            text = notification.author,
            style = MaterialTheme.typography.titleMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            ),
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Preview del mensaje
        Text(
            text = notification.getPreview(80),
            style = MaterialTheme.typography.bodyMedium.copy(
                fontFamily = NevenFontFamily
            ),
            color = colors.textPrimary.copy(alpha = 0.85f),
            textAlign = TextAlign.Center,
            maxLines = 2,
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
                color = colors.textSecondary.copy(alpha = 0.6f)
            )
        }
    }
}

/**
 * Layout completo estilo paper científico
 */
@Composable
private fun FullPaperLayout(
    notification: ScientificNotification,
    colors: NevenColors,
    renderLatex: Boolean,
    showTimestamp: Boolean,
    maxLines: Int,
    onOpenApp: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // ═══════════════════════════════════════════════════════════
        // HEADER - JOURNAL NAME
        // ═══════════════════════════════════════════════════════════
        Text(
            text = notification.journalName,
            style = MaterialTheme.typography.titleSmall.copy(
                fontFamily = FontFamily.Serif,
                fontWeight = FontWeight.Normal,
                letterSpacing = 6.sp
            ),
            color = colors.textSecondary
        )
        
        // Línea decorativa doble
        Spacer(modifier = Modifier.height(8.dp))
        Column {
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.6f)
                    .height(1.dp)
                    .background(colors.textSecondary.copy(alpha = 0.4f))
            )
            Spacer(modifier = Modifier.height(2.dp))
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.6f)
                    .height(1.dp)
                    .background(colors.textSecondary.copy(alpha = 0.2f))
            )
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // ═══════════════════════════════════════════════════════════
        // AUTOR
        // ═══════════════════════════════════════════════════════════
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
            color = colors.textSecondary,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // ═══════════════════════════════════════════════════════════
        // ABSTRACT
        // ═══════════════════════════════════════════════════════════
        // Título "Abstract"
        Text(
            text = "— Abstract —",
            style = MaterialTheme.typography.labelMedium.copy(
                fontFamily = FontFamily.Serif,
                fontWeight = FontWeight.Normal,
                letterSpacing = 2.sp
            ),
            color = colors.textSecondary.copy(alpha = 0.7f)
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        // Contenido del mensaje
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onOpenApp() }
        ) {
            if (renderLatex && (notification.content.contains("$") || notification.content.contains("\\("))) {
                // Renderizar con KaTeX si tiene símbolos LaTeX
                MarkdownWebView(
                    markdown = notification.contentAsMarkdown,
                    textColor = colors.textPrimary,
                    backgroundColor = colors.background,
                    accentColor = colors.accent,
                    modifier = Modifier.heightIn(max = (maxLines * 24).dp)
                )
            } else {
                // Texto plano
                Text(
                    text = notification.content,
                    style = MaterialTheme.typography.bodyMedium.copy(
                        fontFamily = NevenFontFamily,
                        lineHeight = 22.sp
                    ),
                    color = colors.textPrimary.copy(alpha = 0.9f),
                    textAlign = TextAlign.Justify,
                    maxLines = maxLines,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
        
        // ═══════════════════════════════════════════════════════════
        // TIMESTAMP
        // ═══════════════════════════════════════════════════════════
        if (showTimestamp) {
            Spacer(modifier = Modifier.height(16.dp))
            
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.4f)
                    .height(1.dp)
                    .background(colors.textSecondary.copy(alpha = 0.15f))
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = notification.timestampFormatted,
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic
                ),
                color = colors.textSecondary.copy(alpha = 0.6f)
            )
        }
    }
}

/**
 * Botón estilo paper científico
 */
@Composable
private fun PaperButton(
    text: String,
    onClick: () -> Unit,
    colors: NevenColors,
    isPrimary: Boolean
) {
    Text(
        text = "[ $text ]",
        modifier = Modifier
            .clickable { onClick() }
            .padding(horizontal = 16.dp, vertical = 8.dp),
        style = MaterialTheme.typography.labelMedium.copy(
            fontFamily = NevenFontFamily,
            fontWeight = if (isPrimary) FontWeight.Bold else FontWeight.Normal,
            letterSpacing = 1.sp
        ),
        color = if (isPrimary) colors.accent else colors.textSecondary
    )
}
