package com.neven.launcher.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringSetPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Repositorio para guardar las preferencias de calendarios
 * 
 * Almacena qué calendarios están habilitados para mostrar en el widget
 */

private val Context.calendarDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "calendar_preferences"
)

class CalendarPreferencesRepository(private val context: Context) {
    
    companion object {
        private val ENABLED_CALENDARS = stringSetPreferencesKey("enabled_calendars")
        private val HIDDEN_CALENDARS = stringSetPreferencesKey("hidden_calendars")
    }
    
    /**
     * Obtiene los IDs de calendarios ocultos (excluidos)
     * Por defecto, todos los calendarios están visibles
     */
    val hiddenCalendarIds: Flow<Set<String>> = context.calendarDataStore.data
        .map { preferences ->
            preferences[HIDDEN_CALENDARS] ?: emptySet()
        }
    
    /**
     * Oculta un calendario (no lo muestra en el widget)
     */
    suspend fun hideCalendar(calendarId: Long) {
        context.calendarDataStore.edit { preferences ->
            val current = preferences[HIDDEN_CALENDARS] ?: emptySet()
            preferences[HIDDEN_CALENDARS] = current + calendarId.toString()
        }
    }
    
    /**
     * Muestra un calendario (lo incluye en el widget)
     */
    suspend fun showCalendar(calendarId: Long) {
        context.calendarDataStore.edit { preferences ->
            val current = preferences[HIDDEN_CALENDARS] ?: emptySet()
            preferences[HIDDEN_CALENDARS] = current - calendarId.toString()
        }
    }
    
    /**
     * Alterna la visibilidad de un calendario
     */
    suspend fun toggleCalendar(calendarId: Long, isVisible: Boolean) {
        if (isVisible) {
            showCalendar(calendarId)
        } else {
            hideCalendar(calendarId)
        }
    }
    
    /**
     * Resetea todas las preferencias (muestra todos los calendarios)
     */
    suspend fun resetToDefaults() {
        context.calendarDataStore.edit { preferences ->
            preferences.remove(HIDDEN_CALENDARS)
        }
    }
}

/**
 * Modelo de información de un calendario del sistema
 */
data class CalendarInfo(
    val id: Long,
    val displayName: String,
    val accountName: String,
    val accountType: String,
    val color: Int,
    val isVisible: Boolean = true,  // Visible en el sistema
    val isEnabled: Boolean = true   // Habilitado en NEVEN
) {
    /**
     * Nombre amigable para mostrar en la UI
     */
    val friendlyAccountName: String
        get() = when {
            accountType.contains("google", ignoreCase = true) -> "Google"
            accountType.contains("exchange", ignoreCase = true) -> "Outlook"
            accountName.contains("outlook", ignoreCase = true) -> "Outlook"
            accountName.contains("hotmail", ignoreCase = true) -> "Outlook"
            accountName.contains("live.com", ignoreCase = true) -> "Outlook"
            accountName.contains("gmail", ignoreCase = true) -> "Gmail"
            else -> accountName.substringAfter("@").substringBefore(".")
                .replaceFirstChar { it.uppercase() }
        }
    
    /**
     * Icono para el tipo de cuenta
     */
    val accountIcon: String
        get() = when {
            accountType.contains("google", ignoreCase = true) -> "◉"
            accountType.contains("exchange", ignoreCase = true) -> "◈"
            accountName.contains("outlook", ignoreCase = true) -> "◈"
            else -> "◇"
        }
}
