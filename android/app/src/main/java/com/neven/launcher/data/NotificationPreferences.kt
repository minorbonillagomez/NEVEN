package com.neven.launcher.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.core.stringSetPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Repositorio de preferencias para notificaciones científicas
 * 
 * Almacena configuración del popup estilo paper científico
 */

private val Context.notificationPrefsDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "notification_preferences"
)

class NotificationPreferencesRepository(private val context: Context) {
    
    companion object {
        private val POPUP_SIZE = stringPreferencesKey("popup_size")
        private val POPUP_ENABLED = booleanPreferencesKey("popup_enabled")
        private val RENDER_LATEX = booleanPreferencesKey("render_latex")
        private val SHOW_TIMESTAMP = booleanPreferencesKey("show_timestamp")
        private val EXCLUDED_APPS = stringSetPreferencesKey("excluded_apps")
        private val QUICK_REPLY_ENABLED = booleanPreferencesKey("quick_reply_enabled")
        private val MAX_POPUPS = stringPreferencesKey("max_popups")
    }
    
    /**
     * Tamaño del popup (COMPACT, NORMAL, EXPANDED)
     */
    val popupSize: Flow<NotificationPopupSize> = context.notificationPrefsDataStore.data.map { prefs ->
        val sizeStr = prefs[POPUP_SIZE] ?: NotificationPopupSize.NORMAL.name
        try {
            NotificationPopupSize.valueOf(sizeStr)
        } catch (e: Exception) {
            NotificationPopupSize.NORMAL
        }
    }
    
    /**
     * Si el popup científico está habilitado
     */
    val popupEnabled: Flow<Boolean> = context.notificationPrefsDataStore.data.map { prefs ->
        prefs[POPUP_ENABLED] ?: true
    }
    
    /**
     * Si debe renderizar LaTeX en los mensajes
     */
    val renderLatex: Flow<Boolean> = context.notificationPrefsDataStore.data.map { prefs ->
        prefs[RENDER_LATEX] ?: true
    }
    
    /**
     * Si debe mostrar el timestamp
     */
    val showTimestamp: Flow<Boolean> = context.notificationPrefsDataStore.data.map { prefs ->
        prefs[SHOW_TIMESTAMP] ?: true
    }
    
    /**
     * Apps excluidas del popup científico
     */
    val excludedApps: Flow<Set<String>> = context.notificationPrefsDataStore.data.map { prefs ->
        prefs[EXCLUDED_APPS] ?: emptySet()
    }
    
    /**
     * Si está habilitada la respuesta rápida
     */
    val quickReplyEnabled: Flow<Boolean> = context.notificationPrefsDataStore.data.map { prefs ->
        prefs[QUICK_REPLY_ENABLED] ?: true
    }
    
    /**
     * Máximo de popups simultáneos (1-10)
     */
    val maxPopups: Flow<Int> = context.notificationPrefsDataStore.data.map { prefs ->
        prefs[MAX_POPUPS]?.toIntOrNull() ?: 3
    }
    
    suspend fun setPopupSize(size: NotificationPopupSize) {
        context.notificationPrefsDataStore.edit { prefs ->
            prefs[POPUP_SIZE] = size.name
        }
    }
    
    suspend fun setPopupEnabled(enabled: Boolean) {
        context.notificationPrefsDataStore.edit { prefs ->
            prefs[POPUP_ENABLED] = enabled
        }
    }
    
    suspend fun setRenderLatex(enabled: Boolean) {
        context.notificationPrefsDataStore.edit { prefs ->
            prefs[RENDER_LATEX] = enabled
        }
    }
    
    suspend fun setShowTimestamp(show: Boolean) {
        context.notificationPrefsDataStore.edit { prefs ->
            prefs[SHOW_TIMESTAMP] = show
        }
    }
    
    suspend fun setExcludedApps(apps: Set<String>) {
        context.notificationPrefsDataStore.edit { prefs ->
            prefs[EXCLUDED_APPS] = apps
        }
    }
    
    suspend fun addExcludedApp(packageName: String) {
        context.notificationPrefsDataStore.edit { prefs ->
            val current = prefs[EXCLUDED_APPS] ?: emptySet()
            prefs[EXCLUDED_APPS] = current + packageName
        }
    }
    
    suspend fun removeExcludedApp(packageName: String) {
        context.notificationPrefsDataStore.edit { prefs ->
            val current = prefs[EXCLUDED_APPS] ?: emptySet()
            prefs[EXCLUDED_APPS] = current - packageName
        }
    }
    
    suspend fun setQuickReplyEnabled(enabled: Boolean) {
        context.notificationPrefsDataStore.edit { prefs ->
            prefs[QUICK_REPLY_ENABLED] = enabled
        }
    }
    
    suspend fun setMaxPopups(max: Int) {
        context.notificationPrefsDataStore.edit { prefs ->
            prefs[MAX_POPUPS] = max.coerceIn(1, 10).toString()
        }
    }
}

/**
 * Tamaños disponibles para el popup de notificación
 */
enum class NotificationPopupSize(
    val displayName: String,
    val description: String,
    val widthFraction: Float,
    val maxLines: Int
) {
    COMPACT(
        displayName = "Compacto",
        description = "4×2 · Solo título y preview",
        widthFraction = 0.85f,
        maxLines = 2
    ),
    NORMAL(
        displayName = "Normal",
        description = "4×4 · Formato paper completo",
        widthFraction = 0.90f,
        maxLines = 6
    ),
    EXPANDED(
        displayName = "Expandido",
        description = "6×4 · Paper con más espacio",
        widthFraction = 0.95f,
        maxLines = 12
    )
}
