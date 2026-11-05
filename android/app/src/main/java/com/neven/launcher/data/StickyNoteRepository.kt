package com.neven.launcher.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * DataStore para notas adhesivas
 */
private val Context.stickyNotesDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "neven_sticky_notes"
)

/**
 * Repositorio para gestionar las notas adhesivas (Post-its)
 */
class StickyNoteRepository(private val context: Context) {
    
    companion object {
        // Claves para DataStore
        private val NOTES_KEY = stringSetPreferencesKey("sticky_notes")
        private val DEFAULT_COLOR_KEY = stringPreferencesKey("default_color")
        private val DEFAULT_SIZE_KEY = stringPreferencesKey("default_size")
        private val MAX_NOTES_PER_PAGE_KEY = intPreferencesKey("max_notes_per_page")
        private val NOTES_ENABLED_KEY = booleanPreferencesKey("notes_enabled")
        private val NOTES_OPACITY_KEY = floatPreferencesKey("notes_opacity")
        
        // Valores por defecto
        val DEFAULT_COLOR = StickyNoteColor.YELLOW
        val DEFAULT_SIZE = StickyNoteSize.MEDIUM
        const val DEFAULT_MAX_NOTES = 10
        const val MIN_MAX_NOTES = 1
        const val MAX_MAX_NOTES = 20
        const val DEFAULT_NOTES_ENABLED = true
        const val DEFAULT_NOTES_OPACITY = 0.9f
        
        @Volatile
        private var instance: StickyNoteRepository? = null
        
        fun getInstance(context: Context): StickyNoteRepository {
            return instance ?: synchronized(this) {
                instance ?: StickyNoteRepository(context.applicationContext).also {
                    instance = it
                }
            }
        }
    }
    
    /**
     * Flujo de todas las notas
     */
    val allNotesFlow: Flow<List<StickyNote>> = context.stickyNotesDataStore.data.map { prefs ->
        val notesSet = prefs[NOTES_KEY] ?: emptySet()
        notesSet.mapNotNull { StickyNote.deserialize(it) }
            .sortedBy { it.zIndex }
    }
    
    /**
     * Flujo de notas para una pagina especifica
     */
    fun getNotesForPage(pageIndex: Int): Flow<List<StickyNote>> {
        return allNotesFlow.map { notes ->
            notes.filter { it.pageIndex == pageIndex }
                .sortedBy { it.zIndex }
        }
    }
    
    /**
     * Flujo del color por defecto
     */
    val defaultColorFlow: Flow<StickyNoteColor> = context.stickyNotesDataStore.data.map { prefs ->
        val colorName = prefs[DEFAULT_COLOR_KEY]
        if (colorName != null) {
            try {
                StickyNoteColor.valueOf(colorName)
            } catch (e: Exception) {
                DEFAULT_COLOR
            }
        } else {
            DEFAULT_COLOR
        }
    }
    
    /**
     * Flujo del tamano por defecto
     */
    val defaultSizeFlow: Flow<StickyNoteSize> = context.stickyNotesDataStore.data.map { prefs ->
        val sizeName = prefs[DEFAULT_SIZE_KEY]
        if (sizeName != null) {
            try {
                StickyNoteSize.valueOf(sizeName)
            } catch (e: Exception) {
                DEFAULT_SIZE
            }
        } else {
            DEFAULT_SIZE
        }
    }
    
    /**
     * Flujo del maximo de notas por pagina
     */
    val maxNotesPerPageFlow: Flow<Int> = context.stickyNotesDataStore.data.map { prefs ->
        prefs[MAX_NOTES_PER_PAGE_KEY] ?: DEFAULT_MAX_NOTES
    }
    
    /**
     * Flujo de si las notas estan habilitadas (kill switch)
     */
    val notesEnabledFlow: Flow<Boolean> = context.stickyNotesDataStore.data.map { prefs ->
        prefs[NOTES_ENABLED_KEY] ?: DEFAULT_NOTES_ENABLED
    }
    
    /**
     * Flujo de la opacidad/transparencia de las notas (0.0 a 1.0)
     */
    val notesOpacityFlow: Flow<Float> = context.stickyNotesDataStore.data.map { prefs ->
        prefs[NOTES_OPACITY_KEY] ?: DEFAULT_NOTES_OPACITY
    }
    
    /**
     * Crea una nueva nota
     */
    suspend fun createNote(
        pageIndex: Int,
        positionX: Float,
        positionY: Float,
        color: StickyNoteColor? = null,
        size: StickyNoteSize? = null
    ): StickyNote? {
        var createdNote: StickyNote? = null
        
        context.stickyNotesDataStore.edit { prefs ->
            val notesSet = prefs[NOTES_KEY]?.toMutableSet() ?: mutableSetOf()
            val existingNotes = notesSet.mapNotNull { StickyNote.deserialize(it) }
            
            // Verificar limite por pagina
            val maxNotes = prefs[MAX_NOTES_PER_PAGE_KEY] ?: DEFAULT_MAX_NOTES
            val notesOnPage = existingNotes.count { it.pageIndex == pageIndex }
            
            if (notesOnPage >= maxNotes) {
                return@edit // No crear mas notas
            }
            
            // Obtener color y tamano por defecto si no se especifican
            val noteColor = color ?: run {
                val colorName = prefs[DEFAULT_COLOR_KEY]
                if (colorName != null) {
                    try { StickyNoteColor.valueOf(colorName) } catch (e: Exception) { DEFAULT_COLOR }
                } else DEFAULT_COLOR
            }
            
            val noteSize = size ?: run {
                val sizeName = prefs[DEFAULT_SIZE_KEY]
                if (sizeName != null) {
                    try { StickyNoteSize.valueOf(sizeName) } catch (e: Exception) { DEFAULT_SIZE }
                } else DEFAULT_SIZE
            }
            
            // Calcular zIndex (el mas alto + 1)
            val maxZIndex = existingNotes.filter { it.pageIndex == pageIndex }
                .maxOfOrNull { it.zIndex } ?: 0
            
            val note = StickyNote(
                pageIndex = pageIndex,
                positionX = positionX,
                positionY = positionY,
                color = noteColor,
                size = noteSize,
                zIndex = maxZIndex + 1
            )
            
            notesSet.add(note.serialize())
            prefs[NOTES_KEY] = notesSet
            createdNote = note
        }
        
        return createdNote
    }
    
    /**
     * Actualiza una nota existente
     */
    suspend fun updateNote(note: StickyNote) {
        context.stickyNotesDataStore.edit { prefs ->
            val notesSet = prefs[NOTES_KEY]?.toMutableSet() ?: mutableSetOf()
            
            // Encontrar y reemplazar la nota
            val existingNotes = notesSet.mapNotNull { StickyNote.deserialize(it) }
            val updatedNotes = existingNotes.map { 
                if (it.id == note.id) note else it 
            }
            
            prefs[NOTES_KEY] = updatedNotes.map { it.serialize() }.toSet()
        }
    }
    
    /**
     * Actualiza solo la posicion de una nota (preserva el contenido)
     */
    suspend fun updateNotePosition(noteId: String, positionX: Float, positionY: Float) {
        context.stickyNotesDataStore.edit { prefs ->
            val notesSet = prefs[NOTES_KEY]?.toMutableSet() ?: mutableSetOf()
            
            // Encontrar la nota y actualizar solo la posicion
            val existingNotes = notesSet.mapNotNull { StickyNote.deserialize(it) }
            val updatedNotes = existingNotes.map { note ->
                if (note.id == noteId) {
                    note.withPosition(positionX, positionY)
                } else {
                    note
                }
            }
            
            prefs[NOTES_KEY] = updatedNotes.map { it.serialize() }.toSet()
        }
    }
    
    /**
     * Elimina una nota
     */
    suspend fun deleteNote(noteId: String) {
        context.stickyNotesDataStore.edit { prefs ->
            val notesSet = prefs[NOTES_KEY]?.toMutableSet() ?: mutableSetOf()
            val existingNotes = notesSet.mapNotNull { StickyNote.deserialize(it) }
            val filteredNotes = existingNotes.filter { it.id != noteId }
            
            prefs[NOTES_KEY] = filteredNotes.map { it.serialize() }.toSet()
        }
    }
    
    /**
     * Trae una nota al frente (actualiza zIndex)
     */
    suspend fun bringToFront(noteId: String) {
        context.stickyNotesDataStore.edit { prefs ->
            val notesSet = prefs[NOTES_KEY]?.toMutableSet() ?: mutableSetOf()
            val existingNotes = notesSet.mapNotNull { StickyNote.deserialize(it) }
            
            val targetNote = existingNotes.find { it.id == noteId } ?: return@edit
            val maxZIndex = existingNotes.filter { it.pageIndex == targetNote.pageIndex }
                .maxOfOrNull { it.zIndex } ?: 0
            
            val updatedNotes = existingNotes.map {
                if (it.id == noteId) it.copy(zIndex = maxZIndex + 1) else it
            }
            
            prefs[NOTES_KEY] = updatedNotes.map { it.serialize() }.toSet()
        }
    }
    
    /**
     * Establece el color por defecto
     */
    suspend fun setDefaultColor(color: StickyNoteColor) {
        context.stickyNotesDataStore.edit { prefs ->
            prefs[DEFAULT_COLOR_KEY] = color.name
        }
    }
    
    /**
     * Establece el tamano por defecto
     */
    suspend fun setDefaultSize(size: StickyNoteSize) {
        context.stickyNotesDataStore.edit { prefs ->
            prefs[DEFAULT_SIZE_KEY] = size.name
        }
    }
    
    /**
     * Establece el maximo de notas por pagina
     */
    suspend fun setMaxNotesPerPage(max: Int) {
        val validMax = max.coerceIn(MIN_MAX_NOTES, MAX_MAX_NOTES)
        context.stickyNotesDataStore.edit { prefs ->
            prefs[MAX_NOTES_PER_PAGE_KEY] = validMax
        }
    }
    
    /**
     * Habilita o deshabilita las notas adhesivas (kill switch)
     */
    suspend fun setNotesEnabled(enabled: Boolean) {
        context.stickyNotesDataStore.edit { prefs ->
            prefs[NOTES_ENABLED_KEY] = enabled
        }
    }
    
    /**
     * Establece la opacidad/transparencia de las notas (0.0 a 1.0)
     */
    suspend fun setNotesOpacity(opacity: Float) {
        val validOpacity = opacity.coerceIn(0.1f, 1.0f)
        context.stickyNotesDataStore.edit { prefs ->
            prefs[NOTES_OPACITY_KEY] = validOpacity
        }
    }
    
    /**
     * Elimina todas las notas de una pagina
     */
    suspend fun clearNotesFromPage(pageIndex: Int) {
        context.stickyNotesDataStore.edit { prefs ->
            val notesSet = prefs[NOTES_KEY]?.toMutableSet() ?: mutableSetOf()
            val existingNotes = notesSet.mapNotNull { StickyNote.deserialize(it) }
            val filteredNotes = existingNotes.filter { it.pageIndex != pageIndex }
            
            prefs[NOTES_KEY] = filteredNotes.map { it.serialize() }.toSet()
        }
    }
}
