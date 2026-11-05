package com.neven.launcher.ui.audiobook

import android.app.Activity
import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.rememberAsyncImagePainter
import com.neven.launcher.data.audiobook.Audiobook
import com.neven.launcher.data.audiobook.PlayerState
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import java.io.File

/**
 * Pagina completa de audiolibros para el Launcher.
 * Muestra la biblioteca, el reproductor actual y controles.
 * Esta es una pagina independiente del pager, no una Activity separada.
 */
@Composable
fun AudiobookLauncherPage(
    colors: NevenColors,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val activity = context as? Activity
    
    val viewModel: AudiobookViewModel = viewModel(
        factory = AudiobookViewModelFactory(
            activity?.application ?: return
        )
    )
    
    // Collect states
    val currentAudiobook by viewModel.currentAudiobook.collectAsState()
    val playerState by viewModel.playerState.collectAsState()
    val notes by viewModel.currentNotes.collectAsState()
    
    // Library data
    val inProgressBooks by viewModel.inProgressAudiobooks.collectAsState(initial = emptyList())
    val completedBooks by viewModel.completedAudiobooks.collectAsState(initial = emptyList())
    
    // Dialog states
    var showAddNoteDialog by remember { mutableStateOf(false) }
    var showFullPlayer by remember { mutableStateOf(false) }
    
    // File picker for importing audiobooks
    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        uri?.let { viewModel.importAudiobook(it) }
    }
    
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp)
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Audiolibros",
                style = MaterialTheme.typography.headlineMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            
            Text(
                text = "[+]",
                style = MaterialTheme.typography.titleMedium,
                color = colors.accent,
                modifier = Modifier
                    .clip(RoundedCornerShape(4.dp))
                    .clickable { filePickerLauncher.launch(arrayOf("audio/*")) }
                    .padding(8.dp)
            )
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Reproductor actual (si hay algo reproduciendose)
        currentAudiobook?.let { audiobook ->
            MiniPlayerCard(
                audiobook = audiobook,
                playerState = playerState,
                notesCount = notes.size,
                onPlayPause = { viewModel.togglePlayPause() },
                onSeekForward = { viewModel.seekForward() },
                onSeekBackward = { viewModel.seekBackward() },
                onNextChapter = { viewModel.goToNextChapter() },
                onPreviousChapter = { viewModel.goToPreviousChapter() },
                onAddNote = { showAddNoteDialog = true },
                onExpand = { showFullPlayer = true },
                colors = colors
            )
            
            Spacer(modifier = Modifier.height(24.dp))
        }
        
        // Seccion: En progreso
        if (inProgressBooks.isNotEmpty()) {
            Text(
                text = "En progreso",
                style = MaterialTheme.typography.titleSmall,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(inProgressBooks) { book ->
                    SmallBookCard(
                        audiobook = book,
                        onClick = { viewModel.loadAndPlayAudiobook(book.id) },
                        colors = colors,
                        showProgress = true
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(20.dp))
        }
        
        // Seccion: Completados
        if (completedBooks.isNotEmpty()) {
            Text(
                text = "Completados",
                style = MaterialTheme.typography.titleSmall,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(completedBooks) { book ->
                    SmallBookCard(
                        audiobook = book,
                        onClick = { viewModel.loadAndPlayAudiobook(book.id) },
                        colors = colors,
                        showProgress = false
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(20.dp))
        }
        
        // Estado vacio
        if (inProgressBooks.isEmpty() && completedBooks.isEmpty() && currentAudiobook == null) {
            Spacer(modifier = Modifier.weight(1f))
            
            EmptyLibraryState(
                onImportClick = { filePickerLauncher.launch(arrayOf("audio/*")) },
                colors = colors
            )
            
            Spacer(modifier = Modifier.weight(1f))
        }
        
        Spacer(modifier = Modifier.weight(1f))
        
        // Nota sobre NEVEM Studio
        Text(
            text = "Convierte PDF/EPUB a audiolibro con NEVEM Studio",
            style = MaterialTheme.typography.labelSmall,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary.copy(alpha = 0.5f),
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth()
        )
    }
    
    // Dialogo para agregar nota
    if (showAddNoteDialog && currentAudiobook != null) {
        AddNoteDialog(
            currentPositionMs = playerState.currentPositionMs,
            chapterTitle = playerState.currentChapterTitle.ifEmpty { 
                "Capitulo ${playerState.currentChapterIndex + 1}" 
            },
            onSave = { noteText ->
                viewModel.createNote(noteText)
                showAddNoteDialog = false
            },
            onDismiss = { showAddNoteDialog = false }
        )
    }
    
    // Reproductor completo (modal/dialog)
    if (showFullPlayer && currentAudiobook != null) {
        FullPlayerDialog(
            audiobook = currentAudiobook!!,
            playerState = playerState,
            notes = notes,
            onPlayPause = { viewModel.togglePlayPause() },
            onSeekForward = { viewModel.seekForward() },
            onSeekBackward = { viewModel.seekBackward() },
            onSeekTo = { viewModel.seekTo(it) },
            onSpeedChange = { viewModel.setPlaybackSpeed(it) },
            onAddNote = { showAddNoteDialog = true },
            onNoteClick = { viewModel.goToNote(it) },
            onDeleteNote = { viewModel.deleteNote(it) },
            onNextChapter = { viewModel.goToNextChapter() },
            onPreviousChapter = { viewModel.goToPreviousChapter() },
            onDismiss = { showFullPlayer = false },
            colors = colors
        )
    }
}

/**
 * Tarjeta mini del reproductor actual
 */
@Composable
private fun MiniPlayerCard(
    audiobook: Audiobook,
    playerState: PlayerState,
    notesCount: Int,
    onPlayPause: () -> Unit,
    onSeekForward: () -> Unit,
    onSeekBackward: () -> Unit,
    onNextChapter: () -> Unit,
    onPreviousChapter: () -> Unit,
    onAddNote: () -> Unit,
    onExpand: () -> Unit,
    colors: NevenColors
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onExpand() },
        colors = CardDefaults.cardColors(
            containerColor = colors.textSecondary.copy(alpha = 0.08f)
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Portada pequena
                Box(
                    modifier = Modifier
                        .size(64.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(colors.textSecondary.copy(alpha = 0.1f))
                ) {
                    if (audiobook.coverPath != null && File(audiobook.coverPath).exists()) {
                        Image(
                            painter = rememberAsyncImagePainter(File(audiobook.coverPath)),
                            contentDescription = audiobook.title,
                            modifier = Modifier.fillMaxSize(),
                            contentScale = ContentScale.Crop
                        )
                    } else {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = audiobook.title.take(1).uppercase(),
                                style = MaterialTheme.typography.headlineSmall,
                                fontFamily = NevenFontFamily,
                                color = colors.textSecondary
                            )
                        }
                    }
                }
                
                Spacer(modifier = Modifier.width(12.dp))
                
                // Info
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = audiobook.title,
                        style = MaterialTheme.typography.titleMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Medium,
                        color = colors.textPrimary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    
                    Text(
                        text = audiobook.author,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic,
                        color = colors.textSecondary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    
                    Spacer(modifier = Modifier.height(4.dp))
                    
                    // Progreso
                    val progress = if (playerState.totalDurationMs > 0) {
                        playerState.currentPositionMs.toFloat() / playerState.totalDurationMs.toFloat()
                    } else 0f
                    
                    LinearProgressIndicator(
                        progress = { progress },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(3.dp)
                            .clip(RoundedCornerShape(2.dp)),
                        color = colors.accent,
                        trackColor = colors.textSecondary.copy(alpha = 0.2f)
                    )
                    
                    Spacer(modifier = Modifier.height(2.dp))
                    
                    Text(
                        text = "${formatTime(playerState.currentPositionMs)} / ${formatTime(playerState.totalDurationMs)}",
                        style = MaterialTheme.typography.labelSmall,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Controles - Fila 1: Navegación por capítulos y tiempo
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Capítulo anterior |<<
                MiniControlButton(
                    text = "|«",
                    onClick = onPreviousChapter,
                    colors = colors
                )
                
                // -30s
                MiniControlButton(
                    text = "-30",
                    onClick = onSeekBackward,
                    colors = colors
                )
                
                // Play/Pause
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(CircleShape)
                        .background(colors.accent)
                        .clickable { onPlayPause() },
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = if (playerState.isPlaying) "||" else ">",
                        style = MaterialTheme.typography.titleSmall,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.background
                    )
                }
                
                // +30s
                MiniControlButton(
                    text = "+30",
                    onClick = onSeekForward,
                    colors = colors
                )
                
                // Capítulo siguiente >>|
                MiniControlButton(
                    text = "»|",
                    onClick = onNextChapter,
                    colors = colors
                )
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Controles - Fila 2: Nota
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Nota
                MiniControlButton(
                    text = "[N] Nota",
                    onClick = onAddNote,
                    colors = colors,
                    isAccent = true
                )
                
                // Notas count
                if (notesCount > 0) {
                    Text(
                        text = "$notesCount",
                        style = MaterialTheme.typography.labelSmall,
                        fontFamily = NevenFontFamily,
                        color = colors.accent
                    )
                }
            }
        }
    }
}

@Composable
private fun MiniControlButton(
    text: String,
    onClick: () -> Unit,
    colors: NevenColors,
    isAccent: Boolean = false
) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .border(
                1.dp,
                if (isAccent) colors.accent.copy(alpha = 0.5f) else colors.textSecondary.copy(alpha = 0.3f),
                RoundedCornerShape(6.dp)
            )
            .clickable { onClick() }
            .padding(horizontal = 8.dp, vertical = 6.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            fontFamily = NevenFontFamily,
            color = if (isAccent) colors.accent else colors.textSecondary
        )
    }
}

/**
 * Tarjeta pequena de libro para las listas horizontales
 */
@Composable
private fun SmallBookCard(
    audiobook: Audiobook,
    onClick: () -> Unit,
    colors: NevenColors,
    showProgress: Boolean
) {
    val progress = if (audiobook.totalDurationMs > 0) {
        audiobook.lastPositionMs.toFloat() / audiobook.totalDurationMs.toFloat()
    } else 0f
    
    Column(
        modifier = Modifier
            .width(100.dp)
            .clickable { onClick() }
    ) {
        // Portada
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(0.75f)
                .clip(RoundedCornerShape(6.dp))
                .border(1.dp, colors.textSecondary.copy(alpha = 0.2f), RoundedCornerShape(6.dp))
        ) {
            if (audiobook.coverPath != null && File(audiobook.coverPath).exists()) {
                Image(
                    painter = rememberAsyncImagePainter(File(audiobook.coverPath)),
                    contentDescription = audiobook.title,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            } else {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(colors.textSecondary.copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = audiobook.title.take(1).uppercase(),
                        style = MaterialTheme.typography.titleLarge,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
            }
            
            // Barra de progreso
            if (showProgress && progress > 0) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(3.dp)
                        .align(Alignment.BottomCenter)
                        .background(colors.background.copy(alpha = 0.7f))
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(progress)
                            .fillMaxHeight()
                            .background(colors.accent)
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(6.dp))
        
        // Titulo
        Text(
            text = audiobook.title,
            style = MaterialTheme.typography.labelMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.Medium,
            color = colors.textPrimary,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis
        )
    }
}

/**
 * Estado vacio de la biblioteca
 */
@Composable
private fun EmptyLibraryState(
    onImportClick: () -> Unit,
    colors: NevenColors
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.fillMaxWidth()
    ) {
        Text(
            text = "[  ]",
            style = MaterialTheme.typography.displayMedium,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary.copy(alpha = 0.2f)
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "Sin audiolibros",
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = "Importa archivos M4B para comenzar",
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary.copy(alpha = 0.7f)
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(8.dp))
                .background(colors.accent)
                .clickable { onImportClick() }
                .padding(horizontal = 24.dp, vertical = 12.dp)
        ) {
            Text(
                text = "[+] Importar M4B",
                style = MaterialTheme.typography.labelLarge,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = colors.background
            )
        }
    }
}

/**
 * Dialogo de reproductor completo
 */
@Composable
private fun FullPlayerDialog(
    audiobook: Audiobook,
    playerState: PlayerState,
    notes: List<com.neven.launcher.data.audiobook.AudiobookNote>,
    onPlayPause: () -> Unit,
    onSeekForward: () -> Unit,
    onSeekBackward: () -> Unit,
    onSeekTo: (Long) -> Unit,
    onSpeedChange: (Float) -> Unit,
    onAddNote: () -> Unit,
    onNoteClick: (com.neven.launcher.data.audiobook.AudiobookNote) -> Unit,
    onDeleteNote: (String) -> Unit,
    onNextChapter: () -> Unit,
    onPreviousChapter: () -> Unit,
    onDismiss: () -> Unit,
    colors: NevenColors
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        modifier = Modifier.fillMaxWidth(0.95f),
        containerColor = colors.background,
        title = null,
        text = {
            AudiobookPlayerScreen(
                audiobook = audiobook,
                playerState = playerState,
                notes = notes,
                onPlayPause = onPlayPause,
                onSeekForward = onSeekForward,
                onSeekBackward = onSeekBackward,
                onSeekTo = onSeekTo,
                onSpeedChange = onSpeedChange,
                onAddNote = onAddNote,
                onNoteClick = onNoteClick,
                onDeleteNote = onDeleteNote,
                onShareFragment = { /* TODO: Share from launcher */ },
                onBack = onDismiss,
                onNextChapter = onNextChapter,
                onPreviousChapter = onPreviousChapter,
                modifier = Modifier.heightIn(max = 700.dp)
            )
        },
        confirmButton = {}
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
