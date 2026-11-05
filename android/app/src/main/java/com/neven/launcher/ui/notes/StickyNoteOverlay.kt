package com.neven.launcher.ui.notes

import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import com.neven.launcher.data.StickyNote
import com.neven.launcher.data.StickyNoteRepository
import kotlinx.coroutines.launch

/**
 * Capa de overlay que contiene todas las notas de una pagina
 * 
 * Se coloca encima del contenido de la pagina para que las notas
 * puedan flotar sobre cualquier elemento
 */
@Composable
fun StickyNoteOverlay(
    pageIndex: Int,
    onNoteEdit: (StickyNote) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { StickyNoteRepository.getInstance(context) }
    
    // Observar notas de esta pagina
    val notes by repository.getNotesForPage(pageIndex).collectAsState(initial = emptyList())
    
    // Observar opacidad configurada
    val notesOpacity by repository.notesOpacityFlow.collectAsState(initial = 0.9f)
    
    // Tamano del contenedor
    var containerWidth by remember { mutableStateOf(0f) }
    var containerHeight by remember { mutableStateOf(0f) }
    val density = LocalDensity.current
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .onSizeChanged { size ->
                containerWidth = size.width.toFloat()
                containerHeight = size.height.toFloat()
            }
    ) {
        // Renderizar cada nota con key explicito para que Compose
        // maneje correctamente las actualizaciones
        if (containerWidth > 0 && containerHeight > 0) {
            notes.forEach { note ->
                key(note.id) {
                    StickyNoteView(
                        note = note,
                        containerWidth = containerWidth,
                        containerHeight = containerHeight,
                        opacity = notesOpacity,
                        onNoteUpdate = { updatedNote ->
                            scope.launch {
                                // Obtener la nota más reciente del repositorio
                                // y actualizar solo la posición
                                repository.updateNotePosition(
                                    noteId = updatedNote.id,
                                    positionX = updatedNote.positionX,
                                    positionY = updatedNote.positionY
                                )
                            }
                        },
                        onNoteDelete = { noteId ->
                            scope.launch {
                                repository.deleteNote(noteId)
                            }
                        },
                        onNoteTap = { tappedNote ->
                            onNoteEdit(tappedNote)
                        },
                        onBringToFront = { noteId ->
                            scope.launch {
                                repository.bringToFront(noteId)
                            }
                        }
                    )
                }
            }
        }
    }
}
