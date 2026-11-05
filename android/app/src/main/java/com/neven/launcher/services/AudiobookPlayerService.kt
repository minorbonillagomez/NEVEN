package com.neven.launcher.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.os.CountDownTimer
import androidx.core.app.NotificationCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService
import com.neven.launcher.R
import com.neven.launcher.data.audiobook.AudiobookChapter
import com.neven.launcher.data.audiobook.PlayerState
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Servicio de reproduccion de audiolibros usando Media3.
 * Soporta reproduccion en segundo plano con controles de notificacion.
 */
class AudiobookPlayerService : MediaSessionService() {
    
    private var player: ExoPlayer? = null
    private var mediaSession: MediaSession? = null
    private var sleepTimer: CountDownTimer? = null
    
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    
    private val _playerState = MutableStateFlow(PlayerState())
    val playerState: StateFlow<PlayerState> = _playerState.asStateFlow()
    
    private val _currentAudiobookId = MutableStateFlow<String?>(null)
    val currentAudiobookId: StateFlow<String?> = _currentAudiobookId.asStateFlow()
    
    // Callback para notificar posición al destruir servicio (para que ViewModel pueda guardar)
    private var onDestroyCallback: ((audiobookId: String?, positionMs: Long) -> Unit)? = null
    
    companion object {
        const val CHANNEL_ID = "neven_audiobook_channel"
        const val NOTIFICATION_ID = 1001
        
        const val ACTION_PLAY = "com.neven.launcher.ACTION_PLAY"
        const val ACTION_PAUSE = "com.neven.launcher.ACTION_PAUSE"
        const val ACTION_SKIP_FORWARD = "com.neven.launcher.ACTION_SKIP_FORWARD"
        const val ACTION_SKIP_BACK = "com.neven.launcher.ACTION_SKIP_BACK"
        const val ACTION_STOP = "com.neven.launcher.ACTION_STOP"
        
        const val EXTRA_AUDIOBOOK_PATH = "audiobook_path"
        const val EXTRA_AUDIOBOOK_ID = "audiobook_id"
        const val EXTRA_START_POSITION = "start_position"
        
        // Singleton para acceso desde la UI
        @Volatile
        private var instance: AudiobookPlayerService? = null
        
        fun getInstance(): AudiobookPlayerService? = instance
    }
    
    override fun onCreate() {
        super.onCreate()
        instance = this
        android.util.Log.d("AudiobookPlayerService", "onCreate() - Service created, instance set")
        createNotificationChannel()
        initializePlayer()
    }
    
    override fun onDestroy() {
        android.util.Log.d("AudiobookPlayerService", "onDestroy() - Service destroyed")
        
        // Notificar posición final antes de destruir
        val currentPos = player?.currentPosition ?: 0
        val audiobookId = _currentAudiobookId.value
        android.util.Log.d("AudiobookPlayerService", "onDestroy - Saving position: $currentPos for audiobook: $audiobookId")
        onDestroyCallback?.invoke(audiobookId, currentPos)
        
        instance = null
        sleepTimer?.cancel()
        mediaSession?.run {
            player.release()
            release()
        }
        player?.release()
        super.onDestroy()
    }
    
    /**
     * Establece callback para ser notificado cuando el servicio se destruye.
     * Permite al ViewModel guardar la posición final.
     */
    fun setOnDestroyCallback(callback: (audiobookId: String?, positionMs: Long) -> Unit) {
        onDestroyCallback = callback
    }
    
    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? {
        return mediaSession
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "NEVEN Audiolibros",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Reproduccion de audiolibros"
                setShowBadge(false)
            }
            
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
    
    private fun initializePlayer() {
        player = ExoPlayer.Builder(this).build().apply {
            addListener(playerListener)
        }
        
        mediaSession = MediaSession.Builder(this, player!!)
            .build()
    }
    
    private val playerListener = object : Player.Listener {
        override fun onIsPlayingChanged(isPlaying: Boolean) {
            updatePlayerState()
        }
        
        override fun onPlaybackStateChanged(playbackState: Int) {
            updatePlayerState()
            
            if (playbackState == Player.STATE_ENDED) {
                // Notificar que termino
                serviceScope.launch {
                    _playerState.emit(_playerState.value.copy(isPlaying = false))
                }
            }
        }
        
        override fun onPositionDiscontinuity(
            oldPosition: Player.PositionInfo,
            newPosition: Player.PositionInfo,
            reason: Int
        ) {
            updatePlayerState()
        }
    }
    
    private fun updatePlayerState() {
        player?.let { p ->
            serviceScope.launch {
                _playerState.emit(
                    PlayerState(
                        isPlaying = p.isPlaying,
                        currentPositionMs = p.currentPosition,
                        totalDurationMs = p.duration.coerceAtLeast(0),
                        currentChapterIndex = 0, // TODO: Calcular desde capitulos
                        currentChapterTitle = "",
                        playbackSpeed = p.playbackParameters.speed,
                        isBuffering = p.playbackState == Player.STATE_BUFFERING
                    )
                )
            }
        }
    }
    
    // ════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ════════════════════════════════════════════════════════════════
    
    fun loadAudiobook(audiobookId: String, filePath: String, startPositionMs: Long = 0) {
        android.util.Log.d("AudiobookPlayerService", "loadAudiobook() - id: $audiobookId, path: $filePath, startPos: $startPositionMs")
        _currentAudiobookId.value = audiobookId
        
        player?.apply {
            // Convertir ruta de archivo a URI correcto
            val file = java.io.File(filePath)
            val uri = if (file.exists()) {
                android.util.Log.d("AudiobookPlayerService", "File exists, using Uri.fromFile")
                android.net.Uri.fromFile(file)
            } else {
                android.util.Log.w("AudiobookPlayerService", "File does NOT exist! Trying Uri.parse")
                android.net.Uri.parse(filePath)
            }
            
            android.util.Log.d("AudiobookPlayerService", "Loading media with URI: $uri")
            val mediaItem = MediaItem.fromUri(uri)
            setMediaItem(mediaItem)
            prepare()
            seekTo(startPositionMs)
        }
    }
    
    fun play() {
        android.util.Log.d("AudiobookPlayerService", "play() called, player: $player")
        player?.play()
    }
    
    fun pause() {
        android.util.Log.d("AudiobookPlayerService", "pause() called, player: $player")
        player?.pause()
    }
    
    fun togglePlayPause() {
        android.util.Log.d("AudiobookPlayerService", "togglePlayPause() called, player: $player, isPlaying: ${player?.isPlaying}")
        player?.let {
            if (it.isPlaying) pause() else play()
        }
    }
    
    fun seekTo(positionMs: Long) {
        player?.seekTo(positionMs)
    }
    
    fun seekForward(seconds: Int = 30) {
        android.util.Log.d("AudiobookPlayerService", "seekForward($seconds) called, position before: ${player?.currentPosition}")
        player?.let {
            val newPosition = (it.currentPosition + seconds * 1000).coerceAtMost(it.duration)
            android.util.Log.d("AudiobookPlayerService", "Seeking to: $newPosition")
            it.seekTo(newPosition)
        }
    }
    
    fun seekBackward(seconds: Int = 30) {
        android.util.Log.d("AudiobookPlayerService", "seekBackward($seconds) called, position before: ${player?.currentPosition}")
        player?.let {
            val newPosition = (it.currentPosition - seconds * 1000).coerceAtLeast(0)
            android.util.Log.d("AudiobookPlayerService", "Seeking to: $newPosition")
            it.seekTo(newPosition)
        }
    }
    
    fun setPlaybackSpeed(speed: Float) {
        player?.setPlaybackSpeed(speed.coerceIn(0.5f, 2.0f))
    }
    
    /**
     * Obtiene el capítulo actual basado en la posición de reproducción.
     */
    fun getCurrentChapter(chapters: List<AudiobookChapter>): AudiobookChapter? {
        val currentPos = player?.currentPosition ?: return null
        return chapters.find { chapter ->
            currentPos >= chapter.startTimeMs && currentPos < chapter.endTimeMs
        }
    }

    fun getCurrentPosition(): Long = player?.currentPosition ?: 0
    
    fun getDuration(): Long = player?.duration ?: 0
    
    fun isPlaying(): Boolean = player?.isPlaying == true
    
    /**
     * Navega al capítulo especificado por índice.
     * Salta al inicio del capítulo.
     */
    fun goToChapter(chapterIndex: Int, chapters: List<AudiobookChapter>) {
        if (chapterIndex < 0 || chapterIndex >= chapters.size) {
            android.util.Log.w("AudiobookPlayerService", "goToChapter: Invalid index $chapterIndex, chapters size: ${chapters.size}")
            return
        }
        
        val chapter = chapters[chapterIndex]
        android.util.Log.d("AudiobookPlayerService", "goToChapter($chapterIndex): ${chapter.title} at ${chapter.startTimeMs}ms")
        seekTo(chapter.startTimeMs)
    }
    
    /**
     * Navega al siguiente capítulo.
     * @return true si navegó exitosamente, false si ya estaba en el último capítulo
     */
    fun goToNextChapter(chapters: List<AudiobookChapter>): Boolean {
        val currentPos = player?.currentPosition ?: return false
        val currentChapter = getCurrentChapter(chapters) ?: return false
        
        val nextIndex = currentChapter.index + 1
        if (nextIndex >= chapters.size) {
            android.util.Log.d("AudiobookPlayerService", "goToNextChapter: Already at last chapter")
            return false
        }
        
        goToChapter(nextIndex, chapters)
        return true
    }
    
    /**
     * Navega al capítulo anterior.
     * Si está a más de 3 segundos del inicio del capítulo actual, va al inicio del capítulo actual.
     * Si está cerca del inicio, va al capítulo anterior.
     * @return true si navegó exitosamente, false si ya estaba en el primer capítulo
     */
    fun goToPreviousChapter(chapters: List<AudiobookChapter>): Boolean {
        val currentPos = player?.currentPosition ?: return false
        val currentChapter = getCurrentChapter(chapters) ?: return false
        
        // Si está a más de 3 segundos del inicio del capítulo, volver al inicio del capítulo actual
        if (currentPos - currentChapter.startTimeMs > 3000) {
            android.util.Log.d("AudiobookPlayerService", "goToPreviousChapter: Going to start of current chapter ${currentChapter.index}")
            seekTo(currentChapter.startTimeMs)
            return true
        }
        
        // Si está cerca del inicio, ir al capítulo anterior
        val prevIndex = currentChapter.index - 1
        if (prevIndex < 0) {
            android.util.Log.d("AudiobookPlayerService", "goToPreviousChapter: Already at first chapter, going to start")
            seekTo(0)
            return true
        }
        
        goToChapter(prevIndex, chapters)
        return true
    }
    
    // ════════════════════════════════════════════════════════════════
    // SLEEP TIMER
    // ════════════════════════════════════════════════════════════════
    
    fun startSleepTimer(minutes: Int) {
        sleepTimer?.cancel()
        
        if (minutes <= 0) {
            _playerState.value = _playerState.value.copy(sleepTimerRemainingMs = 0)
            return
        }
        
        sleepTimer = object : CountDownTimer(minutes * 60 * 1000L, 1000) {
            override fun onTick(millisUntilFinished: Long) {
                _playerState.value = _playerState.value.copy(
                    sleepTimerRemainingMs = millisUntilFinished
                )
            }
            
            override fun onFinish() {
                pause()
                _playerState.value = _playerState.value.copy(sleepTimerRemainingMs = 0)
            }
        }.start()
    }
    
    fun cancelSleepTimer() {
        sleepTimer?.cancel()
        sleepTimer = null
        _playerState.value = _playerState.value.copy(sleepTimerRemainingMs = 0)
    }
    
    // ════════════════════════════════════════════════════════════════
    // NOTIFICATION
    // ════════════════════════════════════════════════════════════════
    
    private fun buildNotification(title: String, author: String): Notification {
        val playPauseIntent = PendingIntent.getService(
            this,
            0,
            Intent(this, AudiobookPlayerService::class.java).apply {
                action = if (player?.isPlaying == true) ACTION_PAUSE else ACTION_PLAY
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        val skipBackIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, AudiobookPlayerService::class.java).apply {
                action = ACTION_SKIP_BACK
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        val skipForwardIntent = PendingIntent.getService(
            this,
            2,
            Intent(this, AudiobookPlayerService::class.java).apply {
                action = ACTION_SKIP_FORWARD
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(author)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .addAction(R.drawable.ic_launcher_foreground, "-30s", skipBackIntent)
            .addAction(
                R.drawable.ic_launcher_foreground,
                if (player?.isPlaying == true) "Pausa" else "Play",
                playPauseIntent
            )
            .addAction(R.drawable.ic_launcher_foreground, "+30s", skipForwardIntent)
            .setStyle(
                androidx.media.app.NotificationCompat.MediaStyle()
                    .setShowActionsInCompactView(0, 1, 2)
            )
            .setOngoing(true)
            .build()
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_PLAY -> play()
            ACTION_PAUSE -> pause()
            ACTION_SKIP_FORWARD -> seekForward()
            ACTION_SKIP_BACK -> seekBackward()
            ACTION_STOP -> {
                pause()
                stopSelf()
            }
        }
        return super.onStartCommand(intent, flags, startId)
    }
}
