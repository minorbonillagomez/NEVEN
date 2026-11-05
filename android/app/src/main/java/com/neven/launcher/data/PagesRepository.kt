package com.neven.launcher.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import org.json.JSONArray
import org.json.JSONObject

/**
 * Repositorio para gestionar las páginas del launcher
 */
class PagesRepository private constructor(private val context: Context) {
    
    companion object {
        private val Context.pagesDataStore: DataStore<Preferences> by preferencesDataStore(name = "launcher_pages")
        
        private val PAGES_KEY = stringPreferencesKey("pages_json")
        
        @Volatile
        private var instance: PagesRepository? = null
        
        fun getInstance(context: Context): PagesRepository {
            return instance ?: synchronized(this) {
                instance ?: PagesRepository(context.applicationContext).also { instance = it }
            }
        }
    }
    
    /**
     * Flow de páginas actuales
     */
    val pagesFlow: Flow<List<LauncherPage>> = context.pagesDataStore.data.map { preferences ->
        val pagesJson = preferences[PAGES_KEY]
        if (pagesJson != null) {
            try {
                parsePagesFromJson(pagesJson)
            } catch (e: Exception) {
                DefaultPages.getDefaultPages()
            }
        } else {
            DefaultPages.getDefaultPages()
        }
    }
    
    /**
     * Flow del índice de la página HOME (para el pager)
     */
    val homeIndexFlow: Flow<Int> = pagesFlow.map { pages ->
        pages.indexOfFirst { it.type == PageType.HOME }.coerceAtLeast(0)
    }
    
    /**
     * Guardar páginas
     */
    suspend fun savePages(pages: List<LauncherPage>) {
        context.pagesDataStore.edit { preferences ->
            preferences[PAGES_KEY] = pagesToJson(pages)
        }
    }
    
    /**
     * Agregar página a la izquierda de HOME
     */
    suspend fun addPageLeft(page: LauncherPage) {
        context.pagesDataStore.edit { preferences ->
            val currentPages = getCurrentPages(preferences)
            val homeIndex = currentPages.indexOfFirst { it.type == PageType.HOME }
            
            val newPages = currentPages.toMutableList()
            val newPage = page.copy(position = -1 - (homeIndex))
            newPages.add(homeIndex.coerceAtLeast(0), newPage)
            
            val reindexed = reindexPages(newPages)
            preferences[PAGES_KEY] = pagesToJson(reindexed)
        }
    }
    
    /**
     * Agregar página a la derecha de HOME
     */
    suspend fun addPageRight(page: LauncherPage) {
        context.pagesDataStore.edit { preferences ->
            val currentPages = getCurrentPages(preferences)
            val homeIndex = currentPages.indexOfFirst { it.type == PageType.HOME }
            
            val newPages = currentPages.toMutableList()
            val newPage = page.copy(position = currentPages.size - homeIndex)
            newPages.add(homeIndex + 1, newPage)
            
            val reindexed = reindexPages(newPages)
            preferences[PAGES_KEY] = pagesToJson(reindexed)
        }
    }
    
    /**
     * Eliminar página (no se puede eliminar HOME)
     */
    suspend fun removePage(pageId: String) {
        context.pagesDataStore.edit { preferences ->
            val currentPages = getCurrentPages(preferences)
            val pageToRemove = currentPages.find { it.id == pageId }
            
            if (pageToRemove?.type == PageType.HOME) return@edit
            
            val newPages = currentPages.filter { it.id != pageId }
            val reindexed = reindexPages(newPages)
            preferences[PAGES_KEY] = pagesToJson(reindexed)
        }
    }
    
    /**
     * Actualizar widgets de una página
     */
    suspend fun updatePageWidgets(pageId: String, widgets: List<PageWidget>) {
        context.pagesDataStore.edit { preferences ->
            val currentPages = getCurrentPages(preferences)
            val newPages = currentPages.map { page ->
                if (page.id == pageId) page.copy(widgets = widgets) else page
            }
            preferences[PAGES_KEY] = pagesToJson(newPages)
        }
    }
    
    /**
     * Inicializar con configuración Glance (estilo Microsoft)
     */
    suspend fun initializeWithGlance() {
        savePages(DefaultPages.getGlanceSetup())
    }
    
    /**
     * Inicializar con configuración completa (Glance + Adventure)
     */
    suspend fun initializeWithFullSetup() {
        savePages(DefaultPages.getFullSetup())
    }
    
    /**
     * Agregar página de aventura
     */
    suspend fun addAdventurePage() {
        context.pagesDataStore.edit { preferences ->
            val currentPages = getCurrentPages(preferences)
            
            // Verificar si ya existe una página de aventura
            if (currentPages.any { it.type == PageType.ADVENTURE }) return@edit
            
            val homeIndex = currentPages.indexOfFirst { it.type == PageType.HOME }
            val position = currentPages.size - homeIndex
            
            val newPages = currentPages.toMutableList()
            newPages.add(DefaultPages.createAdventurePage(position))
            
            val reindexed = reindexPages(newPages)
            preferences[PAGES_KEY] = pagesToJson(reindexed)
        }
    }
    
    /**
     * Agregar página de audiolibros
     */
    suspend fun addAudiobookPage() {
        context.pagesDataStore.edit { preferences ->
            val currentPages = getCurrentPages(preferences)
            
            // Verificar si ya existe una página de audiolibros
            if (currentPages.any { it.type == PageType.AUDIOBOOK }) return@edit
            
            val homeIndex = currentPages.indexOfFirst { it.type == PageType.HOME }
            val position = currentPages.size - homeIndex
            
            val newPages = currentPages.toMutableList()
            newPages.add(DefaultPages.createAudiobookPage(position))
            
            val reindexed = reindexPages(newPages)
            preferences[PAGES_KEY] = pagesToJson(reindexed)
        }
    }
    
    /**
     * Resetear a configuración por defecto
     */
    suspend fun resetToDefault() {
        savePages(DefaultPages.getDefaultPages())
    }
    
    private fun getCurrentPages(preferences: Preferences): List<LauncherPage> {
        val pagesJson = preferences[PAGES_KEY]
        return if (pagesJson != null) {
            try {
                parsePagesFromJson(pagesJson)
            } catch (e: Exception) {
                DefaultPages.getDefaultPages()
            }
        } else {
            DefaultPages.getDefaultPages()
        }
    }
    
    private fun reindexPages(pages: List<LauncherPage>): List<LauncherPage> {
        val homeIndex = pages.indexOfFirst { it.type == PageType.HOME }
        return pages.mapIndexed { index, page ->
            page.copy(position = index - homeIndex)
        }
    }
    
    // ══════════════════════════════════════════════════════════════════════════
    // JSON Serialization (usando org.json de Android)
    // ══════════════════════════════════════════════════════════════════════════
    
    private fun pagesToJson(pages: List<LauncherPage>): String {
        val array = JSONArray()
        pages.forEach { page ->
            val obj = JSONObject().apply {
                put("id", page.id)
                put("type", page.type.name)
                put("position", page.position)
                put("title", page.title)
                
                val widgetsArray = JSONArray()
                page.widgets.forEach { widget ->
                    val widgetObj = JSONObject().apply {
                        put("id", widget.id)
                        put("type", widget.type.name)
                        put("position", widget.position)
                        
                        val configObj = JSONObject()
                        widget.config.forEach { (key, value) ->
                            configObj.put(key, value)
                        }
                        put("config", configObj)
                    }
                    widgetsArray.put(widgetObj)
                }
                put("widgets", widgetsArray)
            }
            array.put(obj)
        }
        return array.toString()
    }
    
    private fun parsePagesFromJson(json: String): List<LauncherPage> {
        val pages = mutableListOf<LauncherPage>()
        val array = JSONArray(json)
        
        for (i in 0 until array.length()) {
            val obj = array.getJSONObject(i)
            
            val widgets = mutableListOf<PageWidget>()
            val widgetsArray = obj.optJSONArray("widgets") ?: JSONArray()
            
            for (j in 0 until widgetsArray.length()) {
                val widgetObj = widgetsArray.getJSONObject(j)
                
                val config = mutableMapOf<String, String>()
                val configObj = widgetObj.optJSONObject("config")
                if (configObj != null) {
                    configObj.keys().forEach { key ->
                        config[key] = configObj.optString(key, "")
                    }
                }
                
                widgets.add(
                    PageWidget(
                        id = widgetObj.getString("id"),
                        type = WidgetType.valueOf(widgetObj.getString("type")),
                        position = widgetObj.optInt("position", 0),
                        config = config
                    )
                )
            }
            
            pages.add(
                LauncherPage(
                    id = obj.getString("id"),
                    type = PageType.valueOf(obj.getString("type")),
                    position = obj.getInt("position"),
                    title = obj.optString("title", ""),
                    widgets = widgets
                )
            )
        }
        
        return pages
    }
}
