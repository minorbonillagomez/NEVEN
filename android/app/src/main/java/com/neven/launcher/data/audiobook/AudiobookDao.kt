package com.neven.launcher.data.audiobook

import androidx.room.*
import kotlinx.coroutines.flow.Flow

/**
 * DAO para operaciones de base de datos de audiolibros
 */
@Dao
interface AudiobookDao {
    
    // ════════════════════════════════════════════════════════════════
    // AUDIOBOOKS
    // ════════════════════════════════════════════════════════════════
    
    @Query("SELECT * FROM audiobooks ORDER BY lastPlayedAt DESC")
    fun getAllAudiobooks(): Flow<List<Audiobook>>
    
    @Query("SELECT * FROM audiobooks WHERE id = :id")
    suspend fun getAudiobookById(id: String): Audiobook?
    
    @Query("SELECT * FROM audiobooks WHERE id = :id")
    fun getAudiobookByIdFlow(id: String): Flow<Audiobook?>
    
    @Query("SELECT * FROM audiobooks WHERE isCompleted = 0 ORDER BY lastPlayedAt DESC LIMIT 1")
    suspend fun getLastPlayedAudiobook(): Audiobook?
    
    @Query("SELECT * FROM audiobooks WHERE isCompleted = 0 ORDER BY lastPlayedAt DESC")
    fun getInProgressAudiobooks(): Flow<List<Audiobook>>
    
    @Query("SELECT * FROM audiobooks WHERE isCompleted = 1 ORDER BY completedAt DESC")
    fun getCompletedAudiobooks(): Flow<List<Audiobook>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAudiobook(audiobook: Audiobook)
    
    @Update
    suspend fun updateAudiobook(audiobook: Audiobook)
    
    @Query("""
        UPDATE audiobooks 
        SET lastPositionMs = :positionMs, 
            lastChapterIndex = :chapterIndex, 
            lastPlayedAt = :timestamp 
        WHERE id = :audiobookId
    """)
    suspend fun updatePlaybackPosition(
        audiobookId: String,
        positionMs: Long,
        chapterIndex: Int,
        timestamp: Long = System.currentTimeMillis()
    )
    
    @Query("""
        UPDATE audiobooks 
        SET isCompleted = 1, 
            completedAt = :timestamp 
        WHERE id = :audiobookId
    """)
    suspend fun markAsCompleted(audiobookId: String, timestamp: Long = System.currentTimeMillis())
    
    @Query("UPDATE audiobooks SET isCompleted = 0, completedAt = NULL WHERE id = :audiobookId")
    suspend fun markAsNotCompleted(audiobookId: String)
    
    @Delete
    suspend fun deleteAudiobook(audiobook: Audiobook)
    
    @Query("DELETE FROM audiobooks WHERE id = :audiobookId")
    suspend fun deleteAudiobookById(audiobookId: String)
    
    // ════════════════════════════════════════════════════════════════
    // CHAPTERS
    // ════════════════════════════════════════════════════════════════
    
    @Query("SELECT * FROM audiobook_chapters WHERE audiobookId = :audiobookId ORDER BY `index`")
    fun getChaptersForAudiobook(audiobookId: String): Flow<List<AudiobookChapter>>
    
    @Query("SELECT * FROM audiobook_chapters WHERE audiobookId = :audiobookId ORDER BY `index`")
    suspend fun getChaptersForAudiobookSync(audiobookId: String): List<AudiobookChapter>
    
    @Query("""
        SELECT * FROM audiobook_chapters 
        WHERE audiobookId = :audiobookId AND startTimeMs <= :positionMs 
        ORDER BY startTimeMs DESC 
        LIMIT 1
    """)
    suspend fun getChapterAtPosition(audiobookId: String, positionMs: Long): AudiobookChapter?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChapters(chapters: List<AudiobookChapter>)
    
    @Query("DELETE FROM audiobook_chapters WHERE audiobookId = :audiobookId")
    suspend fun deleteChaptersForAudiobook(audiobookId: String)
    
    // ════════════════════════════════════════════════════════════════
    // NOTES
    // ════════════════════════════════════════════════════════════════
    
    @Query("SELECT * FROM audiobook_notes WHERE audiobookId = :audiobookId ORDER BY timestampMs")
    fun getNotesForAudiobook(audiobookId: String): Flow<List<AudiobookNote>>
    
    @Query("SELECT * FROM audiobook_notes WHERE audiobookId = :audiobookId ORDER BY timestampMs")
    suspend fun getNotesForAudiobookSync(audiobookId: String): List<AudiobookNote>
    
    @Query("SELECT * FROM audiobook_notes WHERE id = :noteId")
    suspend fun getNoteById(noteId: String): AudiobookNote?
    
    @Query("SELECT COUNT(*) FROM audiobook_notes WHERE audiobookId = :audiobookId")
    fun getNotesCountForAudiobook(audiobookId: String): Flow<Int>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNote(note: AudiobookNote)
    
    @Update
    suspend fun updateNote(note: AudiobookNote)
    
    @Query("UPDATE audiobook_notes SET isSyncedToFile = :synced WHERE id = :noteId")
    suspend fun updateNoteSyncStatus(noteId: String, synced: Boolean)
    
    @Delete
    suspend fun deleteNote(note: AudiobookNote)
    
    @Query("DELETE FROM audiobook_notes WHERE id = :noteId")
    suspend fun deleteNoteById(noteId: String)
    
    @Query("DELETE FROM audiobook_notes WHERE audiobookId = :audiobookId")
    suspend fun deleteAllNotesForAudiobook(audiobookId: String)
    
    @Query("SELECT * FROM audiobook_notes WHERE isSyncedToFile = 0")
    suspend fun getUnsyncedNotes(): List<AudiobookNote>
    
    // ════════════════════════════════════════════════════════════════
    // SETTINGS
    // ════════════════════════════════════════════════════════════════
    
    @Query("SELECT * FROM audiobook_settings WHERE id = 1")
    fun getSettings(): Flow<AudiobookSettings?>
    
    @Query("SELECT * FROM audiobook_settings WHERE id = 1")
    suspend fun getSettingsSync(): AudiobookSettings?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun saveSettings(settings: AudiobookSettings)
}
