package com.neven.launcher.ui.audiobook

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.neven.launcher.data.audiobook.ShareFragmentConfig
import com.neven.launcher.ui.theme.NevenTheme

/**
 * Activity para el reproductor de audiolibros.
 * 
 * Puede iniciarse desde:
 * - La pagina de audiolibros del launcher
 * - Un intent con ruta de archivo M4B
 * - La notificacion de reproduccion
 */
class AudiobookActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        
        // Obtener ID de audiolibro del intent si viene de alguna parte
        val initialAudiobookId = intent.getStringExtra(EXTRA_AUDIOBOOK_ID)
        
        setContent {
            NevenTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AudiobookNavigation(
                        initialAudiobookId = initialAudiobookId,
                        onExit = { finish() }
                    )
                }
            }
        }
    }
    
    companion object {
        const val EXTRA_AUDIOBOOK_ID = "audiobook_id"
    }
}

@Composable
private fun AudiobookNavigation(
    initialAudiobookId: String?,
    onExit: () -> Unit
) {
    val viewModel: AudiobookViewModel = viewModel(
        factory = AudiobookViewModelFactory(
            (androidx.compose.ui.platform.LocalContext.current as Activity).application
        )
    )
    
    // Collect states
    val uiState by viewModel.uiState.collectAsState()
    val currentAudiobook by viewModel.currentAudiobook.collectAsState()
    val playerState by viewModel.playerState.collectAsState()
    val notes by viewModel.currentNotes.collectAsState()
    val shareFragmentState by viewModel.shareFragmentState.collectAsState()
    
    // Library data
    val inProgressBooks by viewModel.inProgressAudiobooks.collectAsState(initial = emptyList())
    val completedBooks by viewModel.completedAudiobooks.collectAsState(initial = emptyList())
    
    // Navigation state
    var currentScreen by remember { 
        mutableStateOf<Screen>(
            if (initialAudiobookId != null) Screen.Player(initialAudiobookId) 
            else Screen.Library
        )
    }
    
    // Dialog states
    var showAddNoteDialog by remember { mutableStateOf(false) }
    
    // File picker for importing audiobooks
    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        uri?.let { viewModel.importAudiobook(it) }
    }
    
    // Load audiobook when going to player screen
    LaunchedEffect(currentScreen) {
        if (currentScreen is Screen.Player) {
            val playerId = (currentScreen as Screen.Player).audiobookId
            viewModel.loadAndPlayAudiobook(playerId)
        }
    }
    
    when (val screen = currentScreen) {
        is Screen.Library -> {
            AudiobookLibraryScreen(
                inProgressBooks = inProgressBooks,
                completedBooks = completedBooks,
                onBookClick = { audiobook ->
                    currentScreen = Screen.Player(audiobook.id)
                },
                onImportClick = {
                    filePickerLauncher.launch(arrayOf("audio/*"))
                },
                onBack = onExit
            )
        }
        
        is Screen.Player -> {
            val audiobook = currentAudiobook
            if (audiobook != null) {
                AudiobookPlayerScreen(
                    audiobook = audiobook,
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
                    onShareFragment = { 
                        currentScreen = Screen.ShareFragment(
                            ShareFragmentConfig(
                                audiobookId = audiobook.id,
                                startTimeMs = playerState.currentPositionMs,
                                endTimeMs = (playerState.currentPositionMs + 30_000)
                                    .coerceAtMost(playerState.totalDurationMs)
                            )
                        )
                    },
                    onBack = { 
                        viewModel.pause()
                        currentScreen = Screen.Library 
                    }
                )
                
                // Add Note Dialog
                if (showAddNoteDialog) {
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
            }
        }
        
        is Screen.ShareFragment -> {
            val audiobook = currentAudiobook
            if (audiobook != null) {
                ShareFragmentScreen(
                    audiobook = audiobook,
                    currentPositionMs = screen.config.startTimeMs,
                    totalDurationMs = playerState.totalDurationMs,
                    shareState = shareFragmentState,
                    onStartTimeChange = { /* Handled internally */ },
                    onEndTimeChange = { /* Handled internally */ },
                    onPreview = { /* TODO: Preview audio */ },
                    onShare = { startMs, endMs, includeTitle, includeCover, note ->
                        viewModel.executeShareFragment(
                            startTimeMs = startMs,
                            endTimeMs = endMs,
                            includeTitle = includeTitle,
                            includeCover = includeCover,
                            note = note
                        )
                    },
                    onCancel = { 
                        viewModel.cancelShareFragment()
                        currentScreen = Screen.Player(screen.config.audiobookId)
                    }
                )
            }
        }
    }
}

private sealed class Screen {
    object Library : Screen()
    data class Player(val audiobookId: String) : Screen()
    data class ShareFragment(val config: ShareFragmentConfig) : Screen()
}
