package com.neven.launcher.ui.notes

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.core.graphics.toColorInt
import com.neven.launcher.data.StickyNote
import com.neven.launcher.data.StickyNoteColor
import com.neven.launcher.data.StickyNoteRepository
import com.neven.launcher.ui.theme.NevenColors
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Dialogo para editar el contenido de un Post-it
 */
@Composable
fun StickyNoteEditorDialog(
    note: StickyNote,
    onSave: (StickyNote) -> Unit,
    onDelete: (String) -> Unit,
    onDismiss: () -> Unit,
    colors: NevenColors
) {
    var content by remember(note.id) { mutableStateOf(note.content) }
    var selectedColor by remember(note.id) { mutableStateOf(note.color) }
    var showDeleteConfirm by remember { mutableStateOf(false) }
    val focusRequester = remember { FocusRequester() }
    
    // Enfocar el campo de texto al abrir
    LaunchedEffect(Unit) {
        delay(100)
        focusRequester.requestFocus()
    }
    
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(
            usePlatformDefaultWidth = false,
            dismissOnBackPress = true,
            dismissOnClickOutside = true
        )
    ) {
        Card(
            modifier = Modifier
                .fillMaxWidth(0.9f)
                .wrapContentHeight(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = colors.background
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Editar Nota",
                        style = MaterialTheme.typography.titleMedium,
                        color = colors.textPrimary
                    )
                    
                    IconButton(
                        onClick = onDismiss,
                        modifier = Modifier.size(32.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Close,
                            contentDescription = "Cerrar",
                            tint = colors.textSecondary
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Area de edicion con fondo del color seleccionado
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(selectedColor.hex.toColorInt()))
                        .padding(12.dp)
                ) {
                    BasicTextField(
                        value = content,
                        onValueChange = { content = it },
                        modifier = Modifier
                            .fillMaxSize()
                            .focusRequester(focusRequester),
                        textStyle = TextStyle(
                            color = Color(0xFF2D2D2D),
                            fontSize = 14.sp,
                            lineHeight = 20.sp
                        ),
                        cursorBrush = SolidColor(Color(0xFF2D2D2D)),
                        decorationBox = { innerTextField ->
                            Box {
                                if (content.isEmpty()) {
                                    Text(
                                        text = "Escribe tu nota aqui...\n\nSoporta **Markdown** y ecuaciones LaTeX: \$E = mc^2\$",
                                        style = TextStyle(
                                            color = Color(0xFF2D2D2D).copy(alpha = 0.4f),
                                            fontSize = 14.sp
                                        )
                                    )
                                }
                                innerTextField()
                            }
                        }
                    )
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Selector de color
                Text(
                    text = "Color",
                    style = MaterialTheme.typography.labelMedium,
                    color = colors.textSecondary
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(StickyNoteColor.entries) { color ->
                        ColorOption(
                            color = color,
                            isSelected = color == selectedColor,
                            onClick = { selectedColor = color },
                            accentColor = colors.accent
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // Botones de accion
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    // Boton eliminar
                    TextButton(
                        onClick = { showDeleteConfirm = true },
                        colors = ButtonDefaults.textButtonColors(
                            contentColor = MaterialTheme.colorScheme.error
                        )
                    ) {
                        Icon(
                            imageVector = Icons.Default.Delete,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Eliminar")
                    }
                    
                    // Boton guardar
                    Button(
                        onClick = {
                            val updatedNote = note
                                .withContent(content)
                                .withColor(selectedColor)
                            onSave(updatedNote)
                            onDismiss()
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = colors.accent
                        )
                    ) {
                        Icon(
                            imageVector = Icons.Default.Check,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Guardar")
                    }
                }
            }
        }
    }
    
    // Dialogo de confirmacion de eliminacion
    if (showDeleteConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirm = false },
            title = { Text("Eliminar nota") },
            text = { Text("Esta accion no se puede deshacer.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        onDelete(note.id)
                        showDeleteConfirm = false
                        onDismiss()
                    },
                    colors = ButtonDefaults.textButtonColors(
                        contentColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Text("Eliminar")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirm = false }) {
                    Text("Cancelar")
                }
            }
        )
    }
}

/**
 * Opcion de color para el selector
 */
@Composable
private fun ColorOption(
    color: StickyNoteColor,
    isSelected: Boolean,
    onClick: () -> Unit,
    accentColor: Color
) {
    Box(
        modifier = Modifier
            .size(36.dp)
            .clip(CircleShape)
            .background(Color(color.hex.toColorInt()))
            .then(
                if (isSelected) {
                    Modifier.border(2.dp, accentColor, CircleShape)
                } else {
                    Modifier.border(1.dp, Color.Gray.copy(alpha = 0.3f), CircleShape)
                }
            )
            .clickable { onClick() },
        contentAlignment = Alignment.Center
    ) {
        if (isSelected) {
            Icon(
                imageVector = Icons.Default.Check,
                contentDescription = "Seleccionado",
                tint = Color(0xFF2D2D2D),
                modifier = Modifier.size(20.dp)
            )
        }
    }
}
