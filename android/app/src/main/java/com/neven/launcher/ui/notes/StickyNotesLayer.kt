package com.neven.launcher.ui.notes

import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalViewConfiguration
import com.neven.launcher.data.StickyNote
import com.neven.launcher.data.StickyNoteRepository
import com.neven.launcher.ui.theme.NevenColors
import kotlinx.coroutines.launch

/**
 * Capa completa de notas adhesivas para una pagina
 * 
 * Incluye:
 * - Deteccion de long-press para mostrar menu de acciones
 * - Overlay de notas existentes
 * - Editor de notas
 */
@Composable
fun StickyNotesLayer(
    pageIndex: Int,
    colors: NevenColors,
    enabled: Boolean = true,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { StickyNoteRepository.getInstance(context) }
    val viewConfiguration = LocalViewConfiguration.current
    val longPressTimeoutMs = viewConfiguration.longPressTimeoutMillis
    
    // Estados
    var showActionMenu by remember { mutableStateOf(false) }
    var menuPosition by remember { mutableStateOf(Offset.Zero) }
    var editingNote by remember { mutableStateOf<StickyNote?>(null) }
    
    // Tamano del contenedor para calcular posiciones relativas
    var containerWidth by remember { mutableStateOf(0f) }
    var containerHeight by remember { mutableStateOf(0f) }
    
    // Acciones disponibles en el menu
    val menuActions = remember(pageIndex) {
        listOf(
            PageActions.createNote {
                // Crear nota en la posicion del long-press
                scope.launch {
                    val relX = (menuPosition.x / containerWidth).coerceIn(0.05f, 0.7f)
                    val relY = (menuPosition.y / containerHeight).coerceIn(0.05f, 0.7f)
                    
                    val newNote = repository.createNote(
                        pageIndex = pageIndex,
                        positionX = relX,
                        positionY = relY
                    )
                    
                    // Abrir editor inmediatamente
                    newNote?.let { editingNote = it }
                }
            }
            // Agregar mas acciones en el futuro:
            // PageActions.addWidget { /* TODO */ },
            // PageActions.pageSettings { /* TODO */ }
        )
    }
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .onSizeChanged { size ->
                containerWidth = size.width.toFloat()
                containerHeight = size.height.toFloat()
            }
            .then(
                if (enabled) {
                    // Usar gesto manual para NO bloquear los gestos del sistema
                    // Solo detectar long-press fuera de las zonas de gestos del sistema
                    Modifier.pointerInput(pageIndex, longPressTimeoutMs) {
                        awaitEachGesture {
                            // Esperar el primer toque
                            val down = awaitFirstDown(requireUnconsumed = false, pass = PointerEventPass.Initial)
                            val position = down.position
                            
                            // ZONAS PROTEGIDAS para gestos del sistema:
                            // - Borde inferior (swipe up para home/recientes): últimos 15% de la pantalla
                            // - Bordes laterales (swipe para atrás): primeros/últimos 50px
                            val isInBottomGestureZone = position.y > size.height * 0.85f
                            val isInSideGestureZone = position.x < 50f || position.x > size.width - 50f
                            
                            // Si está en zona de gestos del sistema, NO consumir el evento
                            if (isInBottomGestureZone || isInSideGestureZone) {
                                // No consumir - dejar que el sistema maneje el gesto
                                return@awaitEachGesture
                            }
                            
                            // Fuera de zonas protegidas: detectar long-press manualmente
                            var longPressTriggered = false
                            
                            // Iniciar timer para long-press
                            val startTime = System.currentTimeMillis()
                            
                            // Usamos el loop del gesto para detectar long-press
                            do {
                                val event = awaitPointerEvent(PointerEventPass.Initial)
                                val currentChange = event.changes.firstOrNull() ?: break
                                val currentPosition = currentChange.position
                                
                                // Si se movió mucho, cancelar
                                val distance = (currentPosition - position).getDistance()
                                if (distance > 20f) {
                                    break
                                }
                                
                                // Verificar si pasó el tiempo de long-press
                                if (!longPressTriggered && System.currentTimeMillis() - startTime > longPressTimeoutMs) {
                                    longPressTriggered = true
                                    // Activar menú
                                    menuPosition = position
                                    showActionMenu = true
                                }
                            } while (event.changes.any { it.pressed })
                        }
                    }
                } else {
                    Modifier
                }
            )
    ) {
        // Contenido de la pagina
        content()
        
        // Overlay de notas (si esta habilitado)
        if (enabled) {
            StickyNoteOverlay(
                pageIndex = pageIndex,
                onNoteEdit = { note ->
                    editingNote = note
                }
            )
        }
    }
    
    // Menu de acciones (long-press)
    PageActionMenu(
        isVisible = showActionMenu,
        position = menuPosition,
        actions = menuActions,
        onDismiss = { showActionMenu = false },
        colors = colors
    )
    
    // Editor de notas
    editingNote?.let { note ->
        StickyNoteEditorDialog(
            note = note,
            onSave = { updatedNote ->
                scope.launch {
                    repository.updateNote(updatedNote)
                }
            },
            onDelete = { noteId ->
                scope.launch {
                    repository.deleteNote(noteId)
                }
            },
            onDismiss = { editingNote = null },
            colors = colors
        )
    }
}
