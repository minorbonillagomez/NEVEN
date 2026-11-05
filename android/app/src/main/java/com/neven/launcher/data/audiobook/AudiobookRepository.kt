package com.neven.launcher.data.audiobook

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import android.net.Uri
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.util.UUID

/**
 * Repositorio para gestionar audiolibros, notas y metadatos.
 * Maneja la sincronizacion de notas con los archivos M4B.
 */
class AudiobookRepository(
    private val context: Context,
    private val dao: AudiobookDao
) {
    private val gson: Gson = GsonBuilder()
        .setPrettyPrinting()
        .create()
    
    // ════════════════════════════════════════════════════════════════
    // AUDIOBOOKS
    // ════════════════════════════════════════════════════════════════
    
    fun getAllAudiobooks(): Flow<List<Audiobook>> = dao.getAllAudiobooks()
    
    fun getInProgressAudiobooks(): Flow<List<Audiobook>> = dao.getInProgressAudiobooks()
    
    fun getCompletedAudiobooks(): Flow<List<Audiobook>> = dao.getCompletedAudiobooks()
    
    suspend fun getAudiobookById(id: String): Audiobook? = dao.getAudiobookById(id)
    
    fun getAudiobookByIdFlow(id: String): Flow<Audiobook?> = dao.getAudiobookByIdFlow(id)
    
    suspend fun getLastPlayedAudiobook(): Audiobook? = dao.getLastPlayedAudiobook()
    
    /**
     * Importa un archivo M4B a la biblioteca.
     * Extrae metadatos, portada y capitulos.
     */
    suspend fun importAudiobook(uri: Uri): Result<Audiobook> = withContext(Dispatchers.IO) {
        try {
            val retriever = MediaMetadataRetriever()
            retriever.setDataSource(context, uri)
            
            // Extraer metadatos basicos
            val title = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_TITLE)
                ?: uri.lastPathSegment?.removeSuffix(".m4b") ?: "Sin titulo"
            val author = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ARTIST)
                ?: retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_AUTHOR)
                ?: "Autor desconocido"
            val durationMs = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
                ?.toLongOrNull() ?: 0L
            
            // Generar ID unico
            val audiobookId = UUID.randomUUID().toString()
            
            // Copiar archivo a almacenamiento interno
            val audiobooksDir = File(context.filesDir, "audiobooks")
            audiobooksDir.mkdirs()
            val destFile = File(audiobooksDir, "$audiobookId.m4b")
            
            context.contentResolver.openInputStream(uri)?.use { input ->
                FileOutputStream(destFile).use { output ->
                    input.copyTo(output)
                }
            }
            
            // Extraer portada
            val coverPath = extractCover(retriever, audiobookId)
            
            // Extraer capitulos usando Media3 MetadataRetriever
            val chapters = extractChaptersWithMedia3(destFile, audiobookId, durationMs)
            
            retriever.release()
            
            // Crear objeto Audiobook
            val audiobook = Audiobook(
                id = audiobookId,
                title = title,
                author = author,
                filePath = destFile.absolutePath,
                coverPath = coverPath,
                totalDurationMs = durationMs,
                totalChapters = chapters.size,
                fileSize = destFile.length()
            )
            
            // Guardar en base de datos
            dao.insertAudiobook(audiobook)
            dao.insertChapters(chapters)
            
            // Intentar importar notas existentes del M4B
            importNotesFromM4b(audiobookId, destFile)
            
            Result.success(audiobook)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * Extrae la portada del audiolibro y la guarda como archivo
     */
    private suspend fun extractCover(
        retriever: MediaMetadataRetriever,
        audiobookId: String
    ): String? = withContext(Dispatchers.IO) {
        try {
            val coverBytes = retriever.embeddedPicture ?: return@withContext null
            
            val coversDir = File(context.filesDir, "audiobook_covers")
            coversDir.mkdirs()
            val coverFile = File(coversDir, "$audiobookId.jpg")
            
            val bitmap = BitmapFactory.decodeByteArray(coverBytes, 0, coverBytes.size)
            FileOutputStream(coverFile).use { out ->
                bitmap.compress(Bitmap.CompressFormat.JPEG, 90, out)
            }
            
            coverFile.absolutePath
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * Extrae los capitulos del M4B usando parseo directo del contenedor MP4.
     * Busca átomos "chpl" (chapter list) para obtener timestamps y títulos reales.
     * Si no hay capitulos definidos, crea uno solo con todo el contenido.
     */
    private suspend fun extractChaptersWithMedia3(
        m4bFile: File,
        audiobookId: String,
        totalDurationMs: Long
    ): List<AudiobookChapter> = withContext(Dispatchers.IO) {
        try {
            // Extraer información de capítulos desde metadata MP4
            val chapters = extractChaptersFromMp4(m4bFile, audiobookId, totalDurationMs)
            
            if (chapters.isNotEmpty()) {
                chapters
            } else {
                android.util.Log.d("AudiobookRepository", "No chapters found, creating single chapter")
                listOf(
                    AudiobookChapter(
                        id = UUID.randomUUID().toString(),
                        audiobookId = audiobookId,
                        index = 0,
                        title = "Contenido completo",
                        startTimeMs = 0L,
                        endTimeMs = totalDurationMs,
                        durationMs = totalDurationMs
                    )
                )
            }
        } catch (e: Exception) {
            android.util.Log.e("AudiobookRepository", "Error extracting chapters", e)
            // Fallback: crear capítulo único
            listOf(
                AudiobookChapter(
                    id = UUID.randomUUID().toString(),
                    audiobookId = audiobookId,
                    index = 0,
                    title = "Contenido completo",
                    startTimeMs = 0L,
                    endTimeMs = totalDurationMs,
                    durationMs = totalDurationMs
                )
            )
        }
    }
    
    /**
     * Extrae capítulos desde un archivo MP4/M4B usando parseo directo.
     * Busca átomos "chpl" (chapter list) en el contenedor MP4.
     */
    private fun extractChaptersFromMp4(
        m4bFile: File,
        audiobookId: String,
        totalDurationMs: Long
    ): List<AudiobookChapter> {
        val chapters = mutableListOf<AudiobookChapter>()
        
        try {
            java.io.RandomAccessFile(m4bFile, "r").use { raf ->
                val fileSize = raf.length()
                var position = 0L
                
                // Buscar el átomo "moov" que contiene metadata
                while (position < fileSize - 8) {
                    raf.seek(position)
                    
                    // Leer tamaño y tipo del átomo
                    val atomSize = raf.readInt().toLong() and 0xFFFFFFFFL
                    val atomTypeBytes = ByteArray(4)
                    raf.read(atomTypeBytes)
                    val atomType = String(atomTypeBytes, Charsets.US_ASCII)
                    
                    if (atomSize == 0L) break // Fin del archivo
                    
                    when (atomType) {
                        "moov" -> {
                            // Buscar dentro de moov
                            parseContainerAtom(raf, position + 8, position + atomSize, audiobookId, chapters, totalDurationMs)
                        }
                    }
                    
                    position += if (atomSize == 1L) {
                        // Extended size
                        raf.seek(position + 8)
                        raf.readLong()
                    } else {
                        atomSize.coerceAtLeast(8)
                    }
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("AudiobookRepository", "Error parsing MP4 chapters", e)
        }
        
        // Ordenar y asignar índices
        return chapters.sortedBy { it.startTimeMs }.mapIndexed { index, chapter ->
            chapter.copy(index = index)
        }
    }
    
    private fun parseContainerAtom(
        raf: java.io.RandomAccessFile,
        start: Long,
        end: Long,
        audiobookId: String,
        chapters: MutableList<AudiobookChapter>,
        totalDurationMs: Long
    ) {
        var position = start
        
        while (position < end - 8) {
            raf.seek(position)
            
            val atomSize = raf.readInt().toLong() and 0xFFFFFFFFL
            val atomTypeBytes = ByteArray(4)
            raf.read(atomTypeBytes)
            val atomType = String(atomTypeBytes, Charsets.US_ASCII)
            
            if (atomSize == 0L) break
            
            when (atomType) {
                "udta", "trak", "mdia", "minf", "stbl" -> {
                    // Átomos contenedores, buscar dentro
                    parseContainerAtom(raf, position + 8, position + atomSize, audiobookId, chapters, totalDurationMs)
                }
                "chpl" -> {
                    // Chapter list atom
                    parseChapterListAtom(raf, position + 8, position + atomSize, audiobookId, chapters, totalDurationMs)
                }
            }
            
            position += atomSize.coerceAtLeast(8)
        }
    }
    
    private fun parseChapterListAtom(
        raf: java.io.RandomAccessFile,
        start: Long,
        end: Long,
        audiobookId: String,
        chapters: MutableList<AudiobookChapter>,
        totalDurationMs: Long
    ) {
        try {
            raf.seek(start)
            
            // Version (1 byte) + flags (3 bytes) + reserved (4 bytes)
            raf.skipBytes(8)
            
            // Número de capítulos (1 byte)
            val chapterCount = raf.readByte().toInt() and 0xFF
            
            android.util.Log.d("AudiobookRepository", "Found $chapterCount chapters in chpl atom")
            
            for (i in 0 until chapterCount) {
                // Timestamp en unidades de 100ns
                val timestamp100ns = raf.readLong()
                val startTimeMs = timestamp100ns / 10000
                
                // Longitud del título (1 byte)
                val titleLength = raf.readByte().toInt() and 0xFF
                
                // Título
                val titleBytes = ByteArray(titleLength)
                raf.read(titleBytes)
                val title = String(titleBytes, Charsets.UTF_8)
                
                // El endTime será el inicio del siguiente capítulo o el final del audio
                val endTimeMs = totalDurationMs // Se corregirá después
                
                chapters.add(
                    AudiobookChapter(
                        id = UUID.randomUUID().toString(),
                        audiobookId = audiobookId,
                        index = i,
                        title = title.ifEmpty { "Capítulo ${i + 1}" },
                        startTimeMs = startTimeMs,
                        endTimeMs = endTimeMs,
                        durationMs = 0 // Se calculará después
                    )
                )
            }
            
            // Corregir endTime y duración
            for (i in 0 until chapters.size) {
                val endTime = if (i < chapters.size - 1) {
                    chapters[i + 1].startTimeMs
                } else {
                    totalDurationMs
                }
                val duration = endTime - chapters[i].startTimeMs
                chapters[i] = chapters[i].copy(endTimeMs = endTime, durationMs = duration)
            }
            
        } catch (e: Exception) {
            android.util.Log.e("AudiobookRepository", "Error parsing chpl atom", e)
        }
    }
    
    /**
     * Extrae los capitulos del M4B (método legacy - ya no usado).
     * Si no hay capitulos definidos, crea uno solo con todo el contenido.
     */
    @Deprecated("Use extractChaptersWithMedia3 instead")
    private fun extractChapters(
        retriever: MediaMetadataRetriever,
        audiobookId: String,
        totalDurationMs: Long
    ): List<AudiobookChapter> {
        // Fallback: crear un capitulo unico
        return listOf(
            AudiobookChapter(
                id = UUID.randomUUID().toString(),
                audiobookId = audiobookId,
                index = 0,
                title = "Contenido completo",
                startTimeMs = 0,
                endTimeMs = totalDurationMs,
                durationMs = totalDurationMs
            )
        )
    }
    
    suspend fun updatePlaybackPosition(
        audiobookId: String,
        positionMs: Long,
        chapterIndex: Int
    ) {
        dao.updatePlaybackPosition(audiobookId, positionMs, chapterIndex)
    }
    
    suspend fun markAsCompleted(audiobookId: String) {
        dao.markAsCompleted(audiobookId)
    }
    
    suspend fun deleteAudiobook(audiobookId: String) {
        val audiobook = dao.getAudiobookById(audiobookId) ?: return
        
        // Eliminar archivos
        audiobook.filePath.let { File(it).delete() }
        audiobook.coverPath?.let { File(it).delete() }
        
        // Eliminar de base de datos (cascade elimina capitulos y notas)
        dao.deleteAudiobookById(audiobookId)
    }
    
    // ════════════════════════════════════════════════════════════════
    // CHAPTERS
    // ════════════════════════════════════════════════════════════════
    
    fun getChaptersForAudiobook(audiobookId: String): Flow<List<AudiobookChapter>> =
        dao.getChaptersForAudiobook(audiobookId)
    
    suspend fun getChapterAtPosition(audiobookId: String, positionMs: Long): AudiobookChapter? =
        dao.getChapterAtPosition(audiobookId, positionMs)
    
    // ════════════════════════════════════════════════════════════════
    // NOTES
    // ════════════════════════════════════════════════════════════════
    
    fun getNotesForAudiobook(audiobookId: String): Flow<List<AudiobookNote>> =
        dao.getNotesForAudiobook(audiobookId)
    
    fun getNotesCountForAudiobook(audiobookId: String): Flow<Int> =
        dao.getNotesCountForAudiobook(audiobookId)
    
    /**
     * Crea una nueva nota y la sincroniza con el archivo M4B
     */
    suspend fun createNote(
        audiobookId: String,
        timestampMs: Long,
        chapterIndex: Int,
        chapterTitle: String,
        noteText: String
    ): AudiobookNote {
        val note = AudiobookNote(
            id = UUID.randomUUID().toString(),
            audiobookId = audiobookId,
            timestampMs = timestampMs,
            chapterIndex = chapterIndex,
            chapterTitle = chapterTitle,
            noteText = noteText
        )
        
        dao.insertNote(note)
        
        // Sincronizar con archivo M4B
        syncNotesToM4b(audiobookId)
        
        return note
    }
    
    suspend fun updateNote(note: AudiobookNote) {
        dao.updateNote(note.copy(updatedAt = System.currentTimeMillis(), isSyncedToFile = false))
        syncNotesToM4b(note.audiobookId)
    }
    
    suspend fun deleteNote(noteId: String) {
        val note = dao.getNoteById(noteId) ?: return
        dao.deleteNoteById(noteId)
        syncNotesToM4b(note.audiobookId)
    }
    
    /**
     * Sincroniza las notas con los metadatos del archivo M4B.
     * Las notas se guardan como JSON en el campo de comentario del M4B.
     */
    private suspend fun syncNotesToM4b(audiobookId: String) = withContext(Dispatchers.IO) {
        try {
            val audiobook = dao.getAudiobookById(audiobookId) ?: return@withContext
            val notes = dao.getNotesForAudiobookSync(audiobookId)
            
            val metadata = AudiobookNotesMetadata(
                audiobookId = audiobookId,
                notes = notes.map { note ->
                    NoteMetadataItem(
                        id = note.id,
                        timestampMs = note.timestampMs,
                        chapterIndex = note.chapterIndex,
                        chapterTitle = note.chapterTitle,
                        noteText = note.noteText,
                        createdAt = note.createdAt
                    )
                }
            )
            
            val jsonMetadata = gson.toJson(metadata)
            
            // TODO: Implementar escritura de metadatos al M4B
            // Por ahora, guardar en archivo JSON separado
            val metadataFile = File(audiobook.filePath.replace(".m4b", "_notes.json"))
            metadataFile.writeText(jsonMetadata)
            
            // Marcar notas como sincronizadas
            notes.forEach { note ->
                dao.updateNoteSyncStatus(note.id, true)
            }
        } catch (e: Exception) {
            // Log error pero no fallar
            e.printStackTrace()
        }
    }
    
    /**
     * Importa notas desde un archivo M4B existente
     */
    private suspend fun importNotesFromM4b(audiobookId: String, m4bFile: File) = withContext(Dispatchers.IO) {
        try {
            // Buscar archivo de notas asociado
            val notesFile = File(m4bFile.absolutePath.replace(".m4b", "_notes.json"))
            if (!notesFile.exists()) return@withContext
            
            val jsonContent = notesFile.readText()
            val metadata = gson.fromJson(jsonContent, AudiobookNotesMetadata::class.java)
            
            // Importar notas
            metadata.notes.forEach { noteItem ->
                val note = AudiobookNote(
                    id = noteItem.id,
                    audiobookId = audiobookId,
                    timestampMs = noteItem.timestampMs,
                    chapterIndex = noteItem.chapterIndex,
                    chapterTitle = noteItem.chapterTitle,
                    noteText = noteItem.noteText,
                    createdAt = noteItem.createdAt,
                    isSyncedToFile = true
                )
                dao.insertNote(note)
            }
        } catch (e: Exception) {
            // Si falla la importacion, continuar sin notas
            e.printStackTrace()
        }
    }
    
    /**
     * Exporta las notas como texto plano para compartir
     */
    suspend fun exportNotesAsText(audiobookId: String): String = withContext(Dispatchers.IO) {
        val audiobook = dao.getAudiobookById(audiobookId) ?: return@withContext ""
        val notes = dao.getNotesForAudiobookSync(audiobookId)
        
        buildString {
            appendLine("Notas de: ${audiobook.title}")
            appendLine("Autor: ${audiobook.author}")
            appendLine("=" .repeat(50))
            appendLine()
            
            notes.forEach { note ->
                val timeFormatted = formatTime(note.timestampMs)
                appendLine("[$timeFormatted] ${note.chapterTitle}")
                appendLine(note.noteText)
                appendLine()
            }
        }
    }
    
    // ════════════════════════════════════════════════════════════════
    // SETTINGS
    // ════════════════════════════════════════════════════════════════
    
    fun getSettings(): Flow<AudiobookSettings?> = dao.getSettings()
    
    suspend fun getSettingsSync(): AudiobookSettings =
        dao.getSettingsSync() ?: AudiobookSettings()
    
    suspend fun saveSettings(settings: AudiobookSettings) {
        dao.saveSettings(settings)
    }
    
    // ════════════════════════════════════════════════════════════════
    // SHARE FRAGMENT
    // ════════════════════════════════════════════════════════════════
    
    /**
     * Extrae un fragmento del audiolibro como MP3 para compartir.
     * Limites: minimo 10 segundos, maximo 3 minutos.
     */
    suspend fun extractFragment(config: ShareFragmentConfig): Result<File> = withContext(Dispatchers.IO) {
        try {
            val audiobook = dao.getAudiobookById(config.audiobookId)
                ?: return@withContext Result.failure(Exception("Audiolibro no encontrado"))
            
            // Validar duracion (10s - 3min)
            val durationMs = config.endTimeMs - config.startTimeMs
            if (durationMs < 10_000 || durationMs > 180_000) {
                return@withContext Result.failure(
                    Exception("La duracion debe ser entre 10 segundos y 3 minutos")
                )
            }
            
            val fragmentsDir = File(context.cacheDir, "fragments")
            fragmentsDir.mkdirs()
            
            val outputFile = File(
                fragmentsDir,
                "${audiobook.title.take(30)} - ${audiobook.author.take(20)} - Fragmento.mp3"
            )
            
            // TODO: Implementar extraccion real con FFmpeg o MediaCodec
            // Por ahora, crear archivo placeholder
            outputFile.writeText("Fragment placeholder")
            
            Result.success(outputFile)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // ════════════════════════════════════════════════════════════════
    // UTILS
    // ════════════════════════════════════════════════════════════════
    
    private fun formatTime(ms: Long): String {
        val totalSeconds = ms / 1000
        val hours = totalSeconds / 3600
        val minutes = (totalSeconds % 3600) / 60
        val seconds = totalSeconds % 60
        
        return if (hours > 0) {
            String.format("%d:%02d:%02d", hours, minutes, seconds)
        } else {
            String.format("%02d:%02d", minutes, seconds)
        }
    }
}
