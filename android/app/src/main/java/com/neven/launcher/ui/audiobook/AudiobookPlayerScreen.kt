package com.neven.launcher.ui.audiobook

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.rememberAsyncImagePainter
import com.neven.launcher.data.audiobook.Audiobook
import com.neven.launcher.data.audiobook.AudiobookNote
import com.neven.launcher.data.audiobook.PlayerState
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.rememberNevenColors
import java.io.File

/**
 * Pantalla principal del reproductor de audiolibros.
 * Diseno consistente con el estilo NEVEN (academico/LaTeX).
 * Layout: Portada grande centrada + controles en la parte inferior.
 */
@Composable
fun AudiobookPlayerScreen(
    audiobook: Audiobook,
    playerState: PlayerState,
    notes: List<AudiobookNote>,
    onPlayPause: () -> Unit,
    onSeekForward: () -> Unit,
    onSeekBackward: () -> Unit,
    onSeekTo: (Long) -> Unit,
    onSpeedChange: (Float) -> Unit,
    onAddNote: () -> Unit,
    onNoteClick: (AudiobookNote) -> Unit,
    onDeleteNote: (String) -> Unit,
    onShareFragment: () -> Unit,
    onBack: () -> Unit,
    onNextChapter: () -> Unit = {},
    onPreviousChapter: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val colors = rememberNevenColors()
    var showNotesPanel by remember { mutableStateOf(false) }
    var showSpeedSelector by remember { mutableStateOf(false) }
    var showSleepTimer by remember { mutableStateOf(false) }
    var showSecondaryControls by remember { mutableStateOf(false) }
    
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(colors.background)
            .padding(horizontal = 20.dp, vertical = 16.dp)
    ) {
        // ════════════════════════════════════════════════════════════════
        // HEADER MINIMO - Solo botón de volver y título
        // ════════════════════════════════════════════════════════════════
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "<<",
                style = MaterialTheme.typography.titleMedium,
                color = colors.textSecondary,
                modifier = Modifier
                    .clip(RoundedCornerShape(4.dp))
                    .clickable { onBack() }
                    .padding(8.dp)
            )
            
            Text(
                text = "NEVEN Audiolibros",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                color = colors.textPrimary
            )
            
            // Espacio reservado para mantener centrado el título
            Spacer(modifier = Modifier.width(48.dp))
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // ════════════════════════════════════════════════════════════════
        // PORTADA GRANDE CENTRADA - ~45% de la pantalla
        // ════════════════════════════════════════════════════════════════
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(0.45f)
                .padding(horizontal = 24.dp),
            contentAlignment = Alignment.Center
        ) {
            if (audiobook.coverPath != null && File(audiobook.coverPath).exists()) {
                Image(
                    painter = rememberAsyncImagePainter(File(audiobook.coverPath)),
                    contentDescription = audiobook.title,
                    modifier = Modifier
                        .fillMaxHeight()
                        .aspectRatio(0.7f)
                        .clip(RoundedCornerShape(12.dp))
                        .border(1.dp, colors.textSecondary.copy(alpha = 0.3f), RoundedCornerShape(12.dp)),
                    contentScale = ContentScale.Crop
                )
            } else {
                // Portada placeholder
                Box(
                    modifier = Modifier
                        .fillMaxHeight()
                        .aspectRatio(0.7f)
                        .clip(RoundedCornerShape(12.dp))
                        .background(colors.textSecondary.copy(alpha = 0.1f))
                        .border(1.dp, colors.textSecondary.copy(alpha = 0.3f), RoundedCornerShape(12.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = audiobook.title.take(1).uppercase(),
                        style = MaterialTheme.typography.displayLarge,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // ════════════════════════════════════════════════════════════════
        // METADATOS - Título, Autor, Capítulo actual
        // ════════════════════════════════════════════════════════════════
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = audiobook.title,
                style = MaterialTheme.typography.titleLarge,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary,
                textAlign = TextAlign.Center,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = audiobook.author,
                style = MaterialTheme.typography.bodyLarge,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary,
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Capítulo actual
            Text(
                text = playerState.currentChapterTitle.ifEmpty { "Capitulo ${playerState.currentChapterIndex + 1}" },
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                color = colors.accent,
                textAlign = TextAlign.Center
            )
        }
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // ════════════════════════════════════════════════════════════════
        // BARRA DE PROGRESO
        // ════════════════════════════════════════════════════════════════
        Column(modifier = Modifier.fillMaxWidth()) {
            Slider(
                value = if (playerState.totalDurationMs > 0) {
                    playerState.currentPositionMs.toFloat() / playerState.totalDurationMs.toFloat()
                } else 0f,
                onValueChange = { value ->
                    onSeekTo((value * playerState.totalDurationMs).toLong())
                },
                colors = SliderDefaults.colors(
                    thumbColor = colors.accent,
                    activeTrackColor = colors.accent,
                    inactiveTrackColor = colors.textSecondary.copy(alpha = 0.2f)
                ),
                modifier = Modifier.fillMaxWidth()
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = formatTime(playerState.currentPositionMs),
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
                Text(
                    text = formatTime(playerState.totalDurationMs),
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // ════════════════════════════════════════════════════════════════
        // CONTROLES PRINCIPALES (EN LA PARTE INFERIOR)
        // Layout: [|<<] [-30s] [PLAY/PAUSE] [+30s] [>>|]
        // ════════════════════════════════════════════════════════════════
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 4.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Capítulo anterior |<<
            IconButton(
                onClick = { 
                    android.util.Log.d("AudiobookPlayer", "Previous chapter button clicked!")
                    onPreviousChapter() 
                },
                modifier = Modifier.size(40.dp)
            ) {
                Text(
                    text = "|«",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.textSecondary
                )
            }
            
            // -30s
            IconButton(
                onClick = { 
                    android.util.Log.d("AudiobookPlayer", "-30s button clicked!")
                    onSeekBackward() 
                },
                modifier = Modifier.size(44.dp)
            ) {
                Text(
                    text = "-30",
                    style = MaterialTheme.typography.bodyMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = colors.textSecondary
                )
            }
            
            // Play/Pause (boton principal grande)
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(colors.accent)
                    .clickable { onPlayPause() },
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = if (playerState.isPlaying) "||" else ">",
                    style = MaterialTheme.typography.headlineMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.background
                )
            }
            
            // +30s
            IconButton(
                onClick = { 
                    android.util.Log.d("AudiobookPlayer", "+30s button clicked!")
                    onSeekForward() 
                },
                modifier = Modifier.size(44.dp)
            ) {
                Text(
                    text = "+30",
                    style = MaterialTheme.typography.bodyMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = colors.textSecondary
                )
            }
            
            // Capítulo siguiente >>|
            IconButton(
                onClick = { 
                    android.util.Log.d("AudiobookPlayer", "Next chapter button clicked!")
                    onNextChapter() 
                },
                modifier = Modifier.size(40.dp)
            ) {
                Text(
                    text = "»|",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.textSecondary
                )
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // ════════════════════════════════════════════════════════════════
        // CONTROLES SECUNDARIOS COLAPSABLES
        // ════════════════════════════════════════════════════════════════
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = colors.textSecondary.copy(alpha = 0.05f)
            ),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                // Encabezado colapsable
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { showSecondaryControls = !showSecondaryControls },
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Opciones",
                        style = MaterialTheme.typography.labelMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                    
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        // Mostrar velocidad actual siempre visible
                        Text(
                            text = "${playerState.playbackSpeed}x",
                            style = MaterialTheme.typography.labelMedium,
                            fontFamily = NevenFontFamily,
                            color = colors.accent
                        )
                        
                        // Timer si está activo
                        if (playerState.sleepTimerRemainingMs > 0) {
                            Text(
                                text = "| ${formatTime(playerState.sleepTimerRemainingMs)}",
                                style = MaterialTheme.typography.labelMedium,
                                fontFamily = NevenFontFamily,
                                color = colors.textSecondary
                            )
                        }
                        
                        Text(
                            text = if (showSecondaryControls) "^" else "v",
                            style = MaterialTheme.typography.bodyMedium,
                            color = colors.textSecondary
                        )
                    }
                }
                
                // Contenido expandido
                if (showSecondaryControls) {
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // Velocidad
                        TextButton(onClick = { showSpeedSelector = true }) {
                            Text(
                                text = "[${playerState.playbackSpeed}x] Velocidad",
                                style = MaterialTheme.typography.bodySmall,
                                fontFamily = NevenFontFamily,
                                color = colors.textSecondary
                            )
                        }
                        
                        // Separador
                        Text(text = "|", color = colors.textSecondary.copy(alpha = 0.3f))
                        
                        // Agregar nota
                        TextButton(onClick = onAddNote) {
                            Text(
                                text = "[N] Nota",
                                style = MaterialTheme.typography.bodySmall,
                                fontFamily = NevenFontFamily,
                                color = colors.accent
                            )
                        }
                        
                        // Separador
                        Text(text = "|", color = colors.textSecondary.copy(alpha = 0.3f))
                        
                        // Sleep Timer
                        TextButton(onClick = { showSleepTimer = true }) {
                            val timerText = if (playerState.sleepTimerRemainingMs > 0) {
                                "[T] ${formatTime(playerState.sleepTimerRemainingMs)}"
                            } else {
                                "[T] Timer"
                            }
                            Text(
                                text = timerText,
                                style = MaterialTheme.typography.bodySmall,
                                fontFamily = NevenFontFamily,
                                color = colors.textSecondary
                            )
                        }
                    }
                    
                    // Panel de notas
                    if (notes.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(12.dp))
                        
                        HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { showNotesPanel = !showNotesPanel },
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "[N] Mis Notas (${notes.size})",
                                style = MaterialTheme.typography.labelMedium,
                                fontFamily = NevenFontFamily,
                                color = colors.textPrimary
                            )
                            
                            Text(
                                text = if (showNotesPanel) "^" else "v",
                                style = MaterialTheme.typography.bodySmall,
                                color = colors.textSecondary
                            )
                        }
                        
                        if (showNotesPanel) {
                            Spacer(modifier = Modifier.height(8.dp))
                            
                            LazyColumn(
                                modifier = Modifier.heightIn(max = 150.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                items(notes) { note ->
                                    NoteItem(
                                        note = note,
                                        onClick = { onNoteClick(note) },
                                        onDelete = { onDeleteNote(note.id) },
                                        colors = colors
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Espacio flexible para empujar todo hacia arriba
        Spacer(modifier = Modifier.weight(0.05f))
    }
    
    // Dialogo selector de velocidad
    if (showSpeedSelector) {
        SpeedSelectorDialog(
            currentSpeed = playerState.playbackSpeed,
            onSpeedSelected = { speed ->
                onSpeedChange(speed)
                showSpeedSelector = false
            },
            onDismiss = { showSpeedSelector = false },
            colors = colors
        )
    }
    
    // Dialogo sleep timer
    if (showSleepTimer) {
        SleepTimerDialog(
            onTimerSet = { /* TODO */ },
            onDismiss = { showSleepTimer = false },
            colors = colors
        )
    }
}

@Composable
private fun ControlButton(
    text: String,
    onClick: () -> Unit,
    colors: com.neven.launcher.ui.theme.NevenColors,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .size(56.dp)
            .clip(CircleShape)
            .border(1.dp, colors.textSecondary.copy(alpha = 0.3f), CircleShape)
            .clickable { 
                android.util.Log.d("AudiobookPlayer", "ControlButton clicked: $text")
                onClick() 
            },
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary,
            fontSize = 11.sp
        )
    }
}

@Composable
private fun NoteItem(
    note: AudiobookNote,
    onClick: () -> Unit,
    onDelete: () -> Unit,
    colors: com.neven.launcher.ui.theme.NevenColors,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(4.dp))
            .background(colors.background)
            .border(1.dp, colors.textSecondary.copy(alpha = 0.2f), RoundedCornerShape(4.dp))
            .clickable { onClick() }
            .padding(10.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "* ",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.accent
                )
                Text(
                    text = formatTime(note.timestampMs),
                    style = MaterialTheme.typography.labelSmall,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = colors.textPrimary
                )
                Text(
                    text = " - ${note.chapterTitle}",
                    style = MaterialTheme.typography.labelSmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
            
            Spacer(modifier = Modifier.height(2.dp))
            
            Text(
                text = "> ${note.noteText}",
                style = MaterialTheme.typography.labelSmall,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
        
        TextButton(
            onClick = onDelete,
            contentPadding = PaddingValues(4.dp)
        ) {
            Text(
                text = "[x]",
                style = MaterialTheme.typography.labelSmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
        }
    }
}

@Composable
private fun SpeedSelectorDialog(
    currentSpeed: Float,
    onSpeedSelected: (Float) -> Unit,
    onDismiss: () -> Unit,
    colors: com.neven.launcher.ui.theme.NevenColors
) {
    val speeds = listOf(0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 1.75f, 2.0f)
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = "Velocidad de reproduccion",
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            )
        },
        text = {
            Column {
                speeds.forEach { speed ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSpeedSelected(speed) }
                            .padding(vertical = 12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "${speed}x",
                            fontFamily = NevenFontFamily,
                            color = if (speed == currentSpeed) colors.accent else colors.textPrimary
                        )
                        
                        if (speed == currentSpeed) {
                            Text(
                                text = "*",
                                fontFamily = NevenFontFamily,
                                color = colors.accent
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Cerrar", fontFamily = NevenFontFamily)
            }
        },
        containerColor = colors.background
    )
}

@Composable
private fun SleepTimerDialog(
    onTimerSet: (Int) -> Unit,
    onDismiss: () -> Unit,
    colors: com.neven.launcher.ui.theme.NevenColors
) {
    val options = listOf(
        0 to "Desactivar",
        15 to "15 minutos",
        30 to "30 minutos",
        45 to "45 minutos",
        60 to "1 hora",
        -1 to "Fin del capitulo"
    )
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = "Sleep Timer",
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            )
        },
        text = {
            Column {
                options.forEach { (minutes, label) ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                onTimerSet(minutes)
                                onDismiss()
                            }
                            .padding(vertical = 12.dp)
                    ) {
                        Text(
                            text = label,
                            fontFamily = NevenFontFamily,
                            color = colors.textPrimary
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Cerrar", fontFamily = NevenFontFamily)
            }
        },
        containerColor = colors.background
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
