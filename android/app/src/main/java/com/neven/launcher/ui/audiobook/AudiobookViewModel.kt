package com.neven.launcher.ui.audiobook

import android.app.Application
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.net.Uri
import android.os.IBinder
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.neven.launcher.data.audiobook.*
import com.neven.launcher.services.AudiobookPlayerService
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * ViewModel para la pantalla de audiolibros.
 * Gestiona la biblioteca, reproduccion y notas.
 */
class AudiobookViewModel(
    application: Application,
    private val repository: AudiobookRepository
) : AndroidViewModel(application) {
    
    // ════════════════════════════════════════════════════════════════
    // STATE
    // ════════════════════════════════════════════════════════════════
    
    private val _uiState = MutableStateFlow(AudiobookUiState())
    val uiState: StateFlow<AudiobookUiState> = _uiState.asStateFlow()
    
    private val _currentAudiobook = MutableStateFlow<Audiobook?>(null)
    val currentAudiobook: StateFlow<Audiobook?> = _currentAudiobook.asStateFlow()
    
    private val _playerState = MutableStateFlow(PlayerState())
    val playerState: StateFlow<PlayerState> = _playerState.asStateFlow()
    
    private var playerService: AudiobookPlayerService? = null
    private var serviceBound = false
    
    // Biblioteca
    val allAudiobooks: Flow<List<Audiobook>> = repository.getAllAudiobooks()
    val inProgressAudiobooks: Flow<List<Audiobook>> = repository.getInProgressAudiobooks()
    val completedAudiobooks: Flow<List<Audiobook>> = repository.getCompletedAudiobooks()
    
    // Notas del audiolibro actual
    private val _currentNotes = MutableStateFlow<List<AudiobookNote>>(emptyList())
    val currentNotes: StateFlow<List<AudiobookNote>> = _currentNotes.asStateFlow()
    
    // Capitulos del audiolibro actual
    private val _currentChapters = MutableStateFlow<List<AudiobookChapter>>(emptyList())
    val currentChapters: StateFlow<List<AudiobookChapter>> = _currentChapters.asStateFlow()
    
    // Job para polling de posición del reproductor
    private var positionPollingJob: Job? = null
    
    // Settings
    val settings: Flow<AudiobookSettings?> = repository.getSettings()
    
    // ════════════════════════════════════════════════════════════════
    // SERVICE CONNECTION
    // ════════════════════════════════════════════════════════════════
    
    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            // MediaSessionService puede tardar en inicializarse
            // Reintentar obtener la instancia
            viewModelScope.launch {
                var retries = 0
                while (retries < 10 && playerService == null) {
                    playerService = AudiobookPlayerService.getInstance()
                    if (playerService == null) {
                        kotlinx.coroutines.delay(100)
                        retries++
                    }
                }
                
                serviceBound = playerService != null
                android.util.Log.d("AudiobookViewModel", "Service connected: $serviceBound, retries: $retries")
                
                // Observar estado del reproductor y iniciar polling de posición
                playerService?.let { svc ->
                    launch {
                        svc.playerState.collect { state ->
                            // Actualizar capítulo actual basado en posición
                            val chapters = _currentChapters.value
                            val currentChapter = chapters.find { chapter ->
                                state.currentPositionMs >= chapter.startTimeMs && 
                                state.currentPositionMs < chapter.endTimeMs
                            }
                            
                            _playerState.value = state.copy(
                                currentChapterIndex = currentChapter?.index ?: 0,
                                currentChapterTitle = currentChapter?.title ?: ""
                            )
                            
                            // Gestionar polling de posición según estado de reproducción
                            if (state.isPlaying) {
                                startPositionPolling()
                            } else {
                                stopPositionPolling()
                            }
                        }
                    }
                }
            }
        }
        
        override fun onServiceDisconnected(name: ComponentName?) {
            android.util.Log.d("AudiobookViewModel", "Service disconnected")
            playerService = null
            serviceBound = false
            stopPositionPolling()
        }
    }
    
    /**
     * Inicia polling de posición cada 300ms mientras se reproduce.
     * Actualiza la barra de progreso en tiempo real.
     */
    private fun startPositionPolling() {
        if (positionPollingJob?.isActive == true) return
        
        positionPollingJob = viewModelScope.launch {
            while (isActive) {
                playerService?.let { svc ->
                    val currentPos = svc.getCurrentPosition()
                    val duration = svc.getDuration()
                    val isPlaying = svc.isPlaying()
                    
                    // Actualizar capítulo actual basado en posición
                    val chapters = _currentChapters.value
                    val currentChapter = chapters.find { chapter ->
                        currentPos >= chapter.startTimeMs && currentPos < chapter.endTimeMs
                    }
                    
                    _playerState.value = _playerState.value.copy(
                        currentPositionMs = currentPos,
                        totalDurationMs = duration.coerceAtLeast(0),
                        isPlaying = isPlaying,
                        currentChapterIndex = currentChapter?.index ?: _playerState.value.currentChapterIndex,
                        currentChapterTitle = currentChapter?.title ?: _playerState.value.currentChapterTitle
                    )
                }
                delay(300) // Polling cada 300ms para actualización fluida
            }
        }
    }
    
    /**
     * Detiene el polling de posición.
     */
    private fun stopPositionPolling() {
        positionPollingJob?.cancel()
        positionPollingJob = null
    }
    
    init {
        bindPlayerService()
    }
    
    private fun bindPlayerService() {
        val context = getApplication<Application>()
        val intent = Intent(context, AudiobookPlayerService::class.java)
        
        // Iniciar el servicio primero (importante para MediaSessionService)
        try {
            context.startForegroundService(intent)
        } catch (e: Exception) {
            context.startService(intent)
        }
        
        // Luego hacer bind
        context.bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
        android.util.Log.d("AudiobookViewModel", "Binding to player service...")
    }
    
    override fun onCleared() {
        super.onCleared()
        
        // Guardar posición antes de destruir el ViewModel
        viewModelScope.launch {
            saveCurrentPosition()
        }
        
        stopPositionPolling()
        
        if (serviceBound) {
            try {
                getApplication<Application>().unbindService(serviceConnection)
            } catch (e: Exception) {
                android.util.Log.e("AudiobookViewModel", "Error unbinding service", e)
            }
            serviceBound = false
        }
    }
    
    /**
     * Guarda la posición actual de reproducción en la base de datos.
     */
    private suspend fun saveCurrentPosition() {
        _currentAudiobook.value?.let { book ->
            val currentPosition = playerService?.getCurrentPosition() ?: _playerState.value.currentPositionMs
            if (currentPosition > 0) {
                repository.updatePlaybackPosition(
                    book.id,
                    currentPosition,
                    _playerState.value.currentChapterIndex
                )
                android.util.Log.d("AudiobookViewModel", "Position saved: $currentPosition for book: ${book.id}")
            }
        }
    }
    
    // ════════════════════════════════════════════════════════════════
    // BIBLIOTECA
    // ════════════════════════════════════════════════════════════════
    
    fun importAudiobook(uri: Uri) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            repository.importAudiobook(uri).fold(
                onSuccess = { audiobook ->
                    _uiState.update { it.copy(isLoading = false) }
                },
                onFailure = { error ->
                    _uiState.update { it.copy(isLoading = false, error = error.message) }
                }
            )
        }
    }
    
    fun deleteAudiobook(audiobookId: String) {
        viewModelScope.launch {
            repository.deleteAudiobook(audiobookId)
            
            // Si era el actual, limpiar
            if (_currentAudiobook.value?.id == audiobookId) {
                _currentAudiobook.value = null
                playerService?.pause()
            }
        }
    }
    
    // ════════════════════════════════════════════════════════════════
    // REPRODUCCION
    // ════════════════════════════════════════════════════════════════
    
    fun loadAndPlayAudiobook(audiobookId: String) {
        android.util.Log.d("AudiobookViewModel", "loadAndPlayAudiobook() called with id: $audiobookId")
        
        viewModelScope.launch {
            val audiobook = repository.getAudiobookById(audiobookId) ?: run {
                android.util.Log.e("AudiobookViewModel", "Audiobook not found: $audiobookId")
                return@launch
            }
            _currentAudiobook.value = audiobook
            android.util.Log.d("AudiobookViewModel", "Audiobook loaded: ${audiobook.title}, path: ${audiobook.filePath}")
            
            // Cargar notas y capitulos
            repository.getNotesForAudiobook(audiobookId).collect { notes ->
                _currentNotes.value = notes
            }
        }
        
        viewModelScope.launch {
            val audiobook = repository.getAudiobookById(audiobookId) ?: return@launch
            
            repository.getChaptersForAudiobook(audiobookId).collect { chapters ->
                _currentChapters.value = chapters
            }
        }
        
        viewModelScope.launch {
            val audiobook = repository.getAudiobookById(audiobookId) ?: return@launch
            val settings = repository.getSettingsSync()
            
            // Esperar a que el servicio esté listo
            var service = playerService
            var retries = 0
            while (service == null && retries < 20) {
                android.util.Log.d("AudiobookViewModel", "Waiting for service... retry $retries")
                kotlinx.coroutines.delay(100)
                service = playerService ?: AudiobookPlayerService.getInstance()
                playerService = service
                retries++
            }
            
            if (service == null) {
                android.util.Log.e("AudiobookViewModel", "Service still null after retries!")
                return@launch
            }
            
            android.util.Log.d("AudiobookViewModel", "Service ready, loading audiobook...")
            
            // Calcular posicion de inicio (con auto-rewind)
            val startPosition = if (audiobook.lastPositionMs > 0) {
                (audiobook.lastPositionMs - settings.autoRewindSeconds * 1000).coerceAtLeast(0)
            } else {
                0
            }
            
            android.util.Log.d("AudiobookViewModel", "Calling service.loadAudiobook() with path: ${audiobook.filePath}")
            service.loadAudiobook(
                audiobookId = audiobook.id,
                filePath = audiobook.filePath,
                startPositionMs = startPosition
            )
            service.setPlaybackSpeed(settings.playbackSpeed)
            service.play()
        }
    }
    
    fun play() {
        android.util.Log.d("AudiobookViewModel", "play() called, service: $playerService")
        playerService?.play()
    }
    
    fun pause() {
        android.util.Log.d("AudiobookViewModel", "pause() called, service: $playerService")
        viewModelScope.launch {
            playerService?.pause()
            
            // Guardar posición inmediatamente al pausar
            saveCurrentPosition()
        }
    }
    
    fun togglePlayPause() {
        android.util.Log.d("AudiobookViewModel", "togglePlayPause() called, service: $playerService, bound: $serviceBound")
        if (playerService == null) {
            android.util.Log.w("AudiobookViewModel", "Service is null! Trying to get instance again...")
            playerService = AudiobookPlayerService.getInstance()
        }
        playerService?.togglePlayPause()
    }
    
    fun seekTo(positionMs: Long) {
        android.util.Log.d("AudiobookViewModel", "seekTo($positionMs) called, service: $playerService")
        playerService?.seekTo(positionMs)
    }
    
    fun seekForward(seconds: Int = 30) {
        android.util.Log.d("AudiobookViewModel", "seekForward($seconds) called, service: $playerService")
        playerService?.seekForward(seconds)
    }
    
    fun seekBackward(seconds: Int = 30) {
        android.util.Log.d("AudiobookViewModel", "seekBackward($seconds) called, service: $playerService")
        playerService?.seekBackward(seconds)
    }
    
    fun setPlaybackSpeed(speed: Float) {
        viewModelScope.launch {
            playerService?.setPlaybackSpeed(speed)
            repository.saveSettings(repository.getSettingsSync().copy(playbackSpeed = speed))
        }
    }
    
    fun startSleepTimer(minutes: Int) {
        playerService?.startSleepTimer(minutes)
    }
    
    fun cancelSleepTimer() {
        playerService?.cancelSleepTimer()
    }
    
    // ════════════════════════════════════════════════════════════════
    // NAVEGACION DE CAPITULOS
    // ════════════════════════════════════════════════════════════════
    
    /**
     * Navega al siguiente capítulo.
     * Si ya está en el último capítulo, no hace nada.
     */
    fun goToNextChapter() {
        val chapters = _currentChapters.value
        if (chapters.isEmpty()) {
            android.util.Log.w("AudiobookViewModel", "goToNextChapter: No chapters available")
            return
        }
        
        android.util.Log.d("AudiobookViewModel", "goToNextChapter: ${chapters.size} chapters available")
        playerService?.goToNextChapter(chapters)
    }
    
    /**
     * Navega al capítulo anterior.
     * Si está a más de 3s del inicio del capítulo actual, vuelve al inicio del capítulo.
     * Si está cerca del inicio, va al capítulo anterior.
     * Si ya está en el primer capítulo, va al inicio.
     */
    fun goToPreviousChapter() {
        val chapters = _currentChapters.value
        if (chapters.isEmpty()) {
            android.util.Log.w("AudiobookViewModel", "goToPreviousChapter: No chapters available")
            return
        }
        
        android.util.Log.d("AudiobookViewModel", "goToPreviousChapter: ${chapters.size} chapters available")
        playerService?.goToPreviousChapter(chapters)
    }
    
    /**
     * Navega a un capítulo específico por su índice.
     */
    fun goToChapter(chapterIndex: Int) {
        val chapters = _currentChapters.value
        if (chapters.isEmpty()) {
            android.util.Log.w("AudiobookViewModel", "goToChapter: No chapters available")
            return
        }
        
        android.util.Log.d("AudiobookViewModel", "goToChapter($chapterIndex): ${chapters.size} chapters available")
        playerService?.goToChapter(chapterIndex, chapters)
    }
    
    // ════════════════════════════════════════════════════════════════
    // NOTAS
    // ════════════════════════════════════════════════════════════════
    
    fun createNote(noteText: String) {
        viewModelScope.launch {
            val audiobook = _currentAudiobook.value ?: return@launch
            val position = playerService?.getCurrentPosition() ?: 0
            val chapter = repository.getChapterAtPosition(audiobook.id, position)
            
            repository.createNote(
                audiobookId = audiobook.id,
                timestampMs = position,
                chapterIndex = chapter?.index ?: 0,
                chapterTitle = chapter?.title ?: "Desconocido",
                noteText = noteText
            )
        }
    }
    
    fun updateNote(note: AudiobookNote, newText: String) {
        viewModelScope.launch {
            repository.updateNote(note.copy(noteText = newText))
        }
    }
    
    fun deleteNote(noteId: String) {
        viewModelScope.launch {
            repository.deleteNote(noteId)
        }
    }
    
    fun goToNote(note: AudiobookNote) {
        seekTo(note.timestampMs)
    }
    
    fun exportNotesAsText(): String {
        var result = ""
        viewModelScope.launch {
            _currentAudiobook.value?.let { book ->
                result = repository.exportNotesAsText(book.id)
            }
        }
        return result
    }
    
    // ════════════════════════════════════════════════════════════════
    // COMPARTIR FRAGMENTO
    // ════════════════════════════════════════════════════════════════
    
    private val _shareFragmentState = MutableStateFlow<ShareFragmentState>(ShareFragmentState.Idle)
    val shareFragmentState: StateFlow<ShareFragmentState> = _shareFragmentState.asStateFlow()
    
    fun prepareShareFragment(startTimeMs: Long, endTimeMs: Long) {
        _shareFragmentState.value = ShareFragmentState.Preparing(startTimeMs, endTimeMs)
    }
    
    fun cancelShareFragment() {
        _shareFragmentState.value = ShareFragmentState.Idle
    }
    
    fun executeShareFragment(
        startTimeMs: Long,
        endTimeMs: Long,
        includeTitle: Boolean = true,
        includeCover: Boolean = true,
        note: String? = null
    ) {
        viewModelScope.launch {
            val audiobook = _currentAudiobook.value ?: return@launch
            
            _shareFragmentState.value = ShareFragmentState.Processing
            
            val config = ShareFragmentConfig(
                audiobookId = audiobook.id,
                startTimeMs = startTimeMs,
                endTimeMs = endTimeMs,
                includeTitle = includeTitle,
                includeCover = includeCover,
                includeNote = note
            )
            
            repository.extractFragment(config).fold(
                onSuccess = { file ->
                    _shareFragmentState.value = ShareFragmentState.Ready(file)
                },
                onFailure = { error ->
                    _shareFragmentState.value = ShareFragmentState.Error(error.message ?: "Error desconocido")
                }
            )
        }
    }
    
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
}

/**
 * Estado de la UI de audiolibros
 */
data class AudiobookUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val currentScreen: AudiobookScreen = AudiobookScreen.Library
)

enum class AudiobookScreen {
    Library,
    Player,
    Notes,
    ShareFragment
}

/**
 * Estado del proceso de compartir fragmento
 */
sealed class ShareFragmentState {
    object Idle : ShareFragmentState()
    data class Preparing(val startTimeMs: Long, val endTimeMs: Long) : ShareFragmentState()
    object Processing : ShareFragmentState()
    data class Ready(val file: java.io.File) : ShareFragmentState()
    data class Error(val message: String) : ShareFragmentState()
}
