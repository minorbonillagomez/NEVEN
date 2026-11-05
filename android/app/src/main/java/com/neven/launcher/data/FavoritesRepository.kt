package com.neven.launcher.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Repositorio para gestionar las apps favoritas del usuario.
 * 
 * Funcionalidades:
 * - Persistir lista de package names en DataStore
 * - Cantidad configurable: 6 a 10 apps (default 8)
 * - Agregar/quitar favoritos
 */

// DataStore para favoritos
private val Context.favoritesDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "neven_favorites"
)

class FavoritesRepository(private val context: Context) {
    
    companion object {
        // Claves para DataStore
        private val FAVORITES_KEY = stringSetPreferencesKey("favorite_apps")
        private val MAX_FAVORITES_KEY = intPreferencesKey("max_favorites")
        
        // Valores por defecto
        const val DEFAULT_MAX_FAVORITES = 8
        const val MIN_FAVORITES = 6
        const val MAX_FAVORITES = 10
        
        @Volatile
        private var instance: FavoritesRepository? = null
        
        fun getInstance(context: Context): FavoritesRepository {
            return instance ?: synchronized(this) {
                instance ?: FavoritesRepository(context.applicationContext).also {
                    instance = it
                }
            }
        }
    }
    
    /**
     * Flujo de package names de apps favoritas
     */
    val favoritesFlow: Flow<Set<String>> = context.favoritesDataStore.data.map { prefs ->
        prefs[FAVORITES_KEY] ?: emptySet()
    }
    
    /**
     * Flujo del número máximo de favoritos configurado
     */
    val maxFavoritesFlow: Flow<Int> = context.favoritesDataStore.data.map { prefs ->
        prefs[MAX_FAVORITES_KEY] ?: DEFAULT_MAX_FAVORITES
    }
    
    /**
     * Agrega una app a favoritos si hay espacio disponible
     * @return true si se agregó exitosamente, false si ya estaba o no hay espacio
     */
    suspend fun addFavorite(packageName: String): Boolean {
        var success = false
        context.favoritesDataStore.edit { prefs ->
            val currentFavorites = prefs[FAVORITES_KEY]?.toMutableSet() ?: mutableSetOf()
            val maxFavorites = prefs[MAX_FAVORITES_KEY] ?: DEFAULT_MAX_FAVORITES
            
            if (!currentFavorites.contains(packageName) && currentFavorites.size < maxFavorites) {
                currentFavorites.add(packageName)
                prefs[FAVORITES_KEY] = currentFavorites
                success = true
            }
        }
        return success
    }
    
    /**
     * Quita una app de favoritos
     * @return true si se quitó exitosamente, false si no existía
     */
    suspend fun removeFavorite(packageName: String): Boolean {
        var success = false
        context.favoritesDataStore.edit { prefs ->
            val currentFavorites = prefs[FAVORITES_KEY]?.toMutableSet() ?: mutableSetOf()
            
            if (currentFavorites.contains(packageName)) {
                currentFavorites.remove(packageName)
                prefs[FAVORITES_KEY] = currentFavorites
                success = true
            }
        }
        return success
    }
    
    /**
     * Verifica si una app está en favoritos
     */
    fun isFavoriteFlow(packageName: String): Flow<Boolean> {
        return favoritesFlow.map { favorites ->
            favorites.contains(packageName)
        }
    }
    
    /**
     * Establece el número máximo de favoritos (entre 6 y 10)
     */
    suspend fun setMaxFavorites(max: Int) {
        val validMax = max.coerceIn(MIN_FAVORITES, MAX_FAVORITES)
        context.favoritesDataStore.edit { prefs ->
            prefs[MAX_FAVORITES_KEY] = validMax
            
            // Si hay más favoritos que el nuevo máximo, recortar
            val currentFavorites = prefs[FAVORITES_KEY]?.toMutableSet() ?: mutableSetOf()
            if (currentFavorites.size > validMax) {
                val trimmed = currentFavorites.take(validMax).toSet()
                prefs[FAVORITES_KEY] = trimmed
            }
        }
    }
    
    /**
     * Reordena los favoritos según el orden proporcionado
     */
    suspend fun reorderFavorites(newOrder: List<String>) {
        context.favoritesDataStore.edit { prefs ->
            prefs[FAVORITES_KEY] = newOrder.toSet()
        }
    }
    
    /**
     * Limpia todos los favoritos
     */
    suspend fun clearFavorites() {
        context.favoritesDataStore.edit { prefs ->
            prefs[FAVORITES_KEY] = emptySet()
        }
    }
}
