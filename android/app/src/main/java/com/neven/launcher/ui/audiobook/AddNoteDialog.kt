package com.neven.launcher.ui.audiobook

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.rememberNevenColors

/**
 * Dialogo para agregar una nota en el punto actual de reproduccion.
 * Las notas se guardan en el archivo M4B como metadatos.
 */
@Composable
fun AddNoteDialog(
    currentPositionMs: Long,
    chapterTitle: String,
    onSave: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val colors = rememberNevenColors()
    var noteText by remember { mutableStateOf("") }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = colors.background,
        shape = RoundedCornerShape(12.dp),
        title = {
            Column {
                Text(
                    text = "Agregar Nota",
                    style = MaterialTheme.typography.titleLarge,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = colors.textPrimary
                )
                
                Spacer(modifier = Modifier.height(4.dp))
                
                Text(
                    text = "* ${formatTime(currentPositionMs)} - $chapterTitle",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic,
                    color = colors.textSecondary
                )
            }
        },
        text = {
            Column {
                Text(
                    text = "Escribe tu nota sobre este momento:",
                    style = MaterialTheme.typography.bodyMedium,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
                
                Spacer(modifier = Modifier.height(12.dp))
                
                OutlinedTextField(
                    value = noteText,
                    onValueChange = { noteText = it },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(120.dp),
                    placeholder = {
                        Text(
                            text = "Ej: Concepto importante sobre...",
                            fontFamily = NevenFontFamily,
                            fontStyle = FontStyle.Italic
                        )
                    },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = colors.accent,
                        unfocusedBorderColor = colors.textSecondary.copy(alpha = 0.3f),
                        focusedTextColor = colors.textPrimary,
                        unfocusedTextColor = colors.textPrimary
                    ),
                    textStyle = LocalTextStyle.current.copy(fontFamily = NevenFontFamily)
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = "Esta nota se guardara en el archivo M4B y podra ser compartida con otros usuarios.",
                    style = MaterialTheme.typography.labelSmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary.copy(alpha = 0.7f)
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    if (noteText.isNotBlank()) {
                        onSave(noteText.trim())
                    }
                },
                enabled = noteText.isNotBlank()
            ) {
                Text(
                    text = "Guardar",
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = if (noteText.isNotBlank()) colors.accent else colors.textSecondary
                )
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(
                    text = "Cancelar",
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
            }
        }
    )
}

private fun formatTime(ms: Long): String {
    if (ms <= 0) return "0:00"
    
    val totalSeconds = ms / 1000
    val hours = totalSeconds / 3600
    val minutes = (totalSeconds % 3600) / 60
    val seconds = totalSeconds % 60
    
    return if (hours > 0) {
        String.format("%d:%02d:%02d", hours, minutes, seconds)
    } else {
        String.format("%d:%02d", minutes, seconds)
    }
}
