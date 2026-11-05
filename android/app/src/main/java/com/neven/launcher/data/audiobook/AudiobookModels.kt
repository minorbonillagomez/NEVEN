package com.neven.launcher.data.audiobook

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * NEVEN Audiobook Data Models
 * 
 * Modelos para el reproductor de audiolibros con soporte para:
 * - Memoria de reproduccion (posicion guardada)
 * - Notas/marcadores embebidos en el archivo M4B
 * - Compartir fragmentos como MP3
 */

/**
 * Representa un audiolibro en la biblioteca
 */
@Entity(tableName = "audiobooks")
data class Audiobook(
    @PrimaryKey
    val id: String,
    val title: String,
    val author: String,
    val filePath: String,
    val coverPath: String? = null,
    val totalDurationMs: Long = 0,
    val totalChapters: Int = 0,
    val fileSize: Long = 0,
    val addedAt: Long = System.currentTimeMillis(),
    
    // Memoria de reproduccion
    val lastPositionMs: Long = 0,
    val lastChapterIndex: Int = 0,
    val lastPlayedAt: Long = 0,
    val isCompleted: Boolean = false,
    val completedAt: Long? = null
)

/**
 * Capitulo de un audiolibro (extraido del M4B)
 */
@Entity(
    tableName = "audiobook_chapters",
    foreignKeys = [
        ForeignKey(
            entity = Audiobook::class,
            parentColumns = ["id"],
            childColumns = ["audiobookId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("audiobookId")]
)
data class AudiobookChapter(
    @PrimaryKey
    val id: String,
    val audiobookId: String,
    val index: Int,
    val title: String,
    val startTimeMs: Long,
    val endTimeMs: Long,
    val durationMs: Long
)

/**
 * Nota/marcador del usuario en un punto especifico del audiolibro.
 * Estas notas se embeben en los metadatos del archivo M4B.
 */
@Entity(
    tableName = "audiobook_notes",
    foreignKeys = [
        ForeignKey(
            entity = Audiobook::class,
            parentColumns = ["id"],
            childColumns = ["audiobookId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("audiobookId")]
)
data class AudiobookNote(
    @PrimaryKey
    val id: String,
    val audiobookId: String,
    val timestampMs: Long,
    val chapterIndex: Int,
    val chapterTitle: String,
    val noteText: String,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis(),
    
    // Para sincronizacion con metadatos del M4B
    val isSyncedToFile: Boolean = false
)

/**
 * Configuracion de reproduccion del usuario
 */
@Entity(tableName = "audiobook_settings")
data class AudiobookSettings(
    @PrimaryKey
    val id: Int = 1, // Singleton
    val playbackSpeed: Float = 1.0f,
    val sleepTimerMinutes: Int = 0, // 0 = desactivado
    val sleepTimerEndOfChapter: Boolean = false,
    val skipSilence: Boolean = false,
    val autoRewindSeconds: Int = 5 // Al reanudar, retroceder X segundos
)

/**
 * Modelo para exportar/importar notas en formato JSON
 * (embebido en metadatos del M4B)
 */
data class AudiobookNotesMetadata(
    val version: Int = 1,
    val audiobookId: String,
    val exportedAt: Long = System.currentTimeMillis(),
    val notes: List<NoteMetadataItem>
)

data class NoteMetadataItem(
    val id: String,
    val timestampMs: Long,
    val chapterIndex: Int,
    val chapterTitle: String,
    val noteText: String,
    val createdAt: Long
)

/**
 * Estado del reproductor
 */
data class PlayerState(
    val isPlaying: Boolean = false,
    val currentPositionMs: Long = 0,
    val totalDurationMs: Long = 0,
    val currentChapterIndex: Int = 0,
    val currentChapterTitle: String = "",
    val playbackSpeed: Float = 1.0f,
    val sleepTimerRemainingMs: Long = 0,
    val isBuffering: Boolean = false
)

/**
 * Configuracion para compartir fragmento
 */
data class ShareFragmentConfig(
    val audiobookId: String,
    val startTimeMs: Long,
    val endTimeMs: Long,
    val includeTitle: Boolean = true,
    val includeCover: Boolean = true,
    val includeNote: String? = null
)
