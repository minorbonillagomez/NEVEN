package com.neven.launcher.data

import java.util.UUID

/**
 * Representa una página del launcher
 * 
 * El usuario puede tener múltiples páginas con widgets,
 * con la página HOME siempre en el centro como referencia.
 */
data class LauncherPage(
    val id: String = UUID.randomUUID().toString(),
    val type: PageType,
    val position: Int,  // Relativo a HOME (0). Negativo = izquierda, Positivo = derecha
    val widgets: List<PageWidget> = emptyList(),
    val title: String = ""
)

/**
 * Tipos de página disponibles
 */
enum class PageType {
    HOME,           // Página principal con reloj + favoritos (siempre posición 0)
    WIDGETS,        // Página de widgets personalizables
    CALENDAR,       // Página dedicada al calendario
    NOTES,          // Página de notas rápidas
    GLANCE,         // Página estilo Microsoft Glance (calendario + clima + noticias)
    ADVENTURE,      // Reloj de aventura con brújula, altitud, clima y datos meteorológicos
    AUDIOBOOK       // Biblioteca y reproductor de audiolibros
}

/**
 * Widget dentro de una página
 */
data class PageWidget(
    val id: String = UUID.randomUUID().toString(),
    val type: WidgetType,
    val position: Int = 0,  // Orden vertical en la página
    val config: Map<String, String> = emptyMap()
)

/**
 * Tipos de widgets disponibles
 */
enum class WidgetType {
    CALENDAR,       // Próximos eventos del calendario
    WEATHER,        // Clima actual
    CLOCK,          // Reloj adicional
    NOTES,          // Notas rápidas
    TASKS,          // Lista de tareas
    SHORTCUTS,      // Accesos directos a apps
    MEDIA_PLAYER,   // Controles de reproducción
    SPACER          // Espaciador vacío
}

/**
 * Configuración por defecto de páginas
 */
object DefaultPages {
    
    /**
     * Configuración inicial: solo HOME
     */
    fun getDefaultPages(): List<LauncherPage> = listOf(
        LauncherPage(
            id = "home",
            type = PageType.HOME,
            position = 0,
            title = "Home"
        )
    )
    
    /**
     * Configuración con Glance a la izquierda (estilo Microsoft)
     */
    fun getGlanceSetup(): List<LauncherPage> = listOf(
        LauncherPage(
            id = "glance",
            type = PageType.GLANCE,
            position = -1,
            title = "Glance",
            widgets = listOf(
                PageWidget(type = WidgetType.CALENDAR, position = 0)
                // Weather widget deshabilitado temporalmente
            )
        ),
        LauncherPage(
            id = "home",
            type = PageType.HOME,
            position = 0,
            title = "Home"
        )
    )
    
    /**
     * Configuración completa con Glance + Adventure
     */
    fun getFullSetup(): List<LauncherPage> = listOf(
        LauncherPage(
            id = "glance",
            type = PageType.GLANCE,
            position = -1,
            title = "Glance",
            widgets = listOf(
                PageWidget(type = WidgetType.CALENDAR, position = 0)
            )
        ),
        LauncherPage(
            id = "home",
            type = PageType.HOME,
            position = 0,
            title = "Home"
        ),
        LauncherPage(
            id = "adventure",
            type = PageType.ADVENTURE,
            position = 1,
            title = "Adventure"
        )
    )
    
    /**
     * Crear página de aventura
     */
    fun createAdventurePage(position: Int): LauncherPage = LauncherPage(
        id = "adventure",
        type = PageType.ADVENTURE,
        position = position,
        title = "Adventure"
    )
    
    /**
     * Crear página de audiolibros
     */
    fun createAudiobookPage(position: Int): LauncherPage = LauncherPage(
        id = "audiobook",
        type = PageType.AUDIOBOOK,
        position = position,
        title = "Audiolibros"
    )
    
    /**
     * Crear una nueva página de widgets
     */
    fun createWidgetPage(position: Int): LauncherPage = LauncherPage(
        type = PageType.WIDGETS,
        position = position,
        title = "Página ${if (position > 0) "+$position" else position}"
    )
}
