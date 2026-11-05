package com.neven.launcher.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import com.neven.launcher.ui.theme.NevenPalette
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Repositorio para gestionar configuraciones del launcher.
 * 
 * Incluye:
 * - Motor de búsqueda preferido
 * - Tema/Paleta seleccionada
 * - Modo oscuro/claro/auto
 * - Idioma
 * - Mostrar segundos en reloj
 * - Tamaño de letra global
 * - Fondo de pantalla (color sólido o imagen)
 */

// DataStore para settings
private val Context.settingsDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "neven_settings"
)

/**
 * Motores de búsqueda disponibles
 */
enum class SearchEngine(val displayName: String, val baseUrl: String) {
    GOOGLE("Google", "https://www.google.com/search?q="),
    BING("Bing", "https://www.bing.com/search?q="),
    DUCKDUCKGO("DuckDuckGo", "https://duckduckgo.com/?q="),
    ECOSIA("Ecosia", "https://www.ecosia.org/search?q=")
}

/**
 * Modos de tema disponibles
 */
enum class ThemeMode(val displayName: String) {
    LIGHT("Claro"),
    DARK("Oscuro"),
    AUTO("Auto")
}

/**
 * Opciones de tamaño de letra global
 * Cada opción tiene un factor de escala asociado
 */
enum class FontSizeOption(val scale: Float) {
    XS(0.75f),    // Muy pequeño
    S(0.875f),    // Pequeño
    M(1.0f),      // Mediano (por defecto)
    L(1.125f),    // Grande
    XL(1.25f),    // Muy grande
    XXL(1.5f)     // Extra grande
}

/**
 * Tipo de fondo de pantalla
 */
enum class BackgroundType {
    SOLID,  // Color sólido de la paleta
    IMAGE   // Imagen de galería
}

/**
 * Posición de la imagen de fondo
 */
enum class BackgroundPosition {
    FIT,    // Ajustar (sin recortar)
    CROP,   // Rellenar (recortar para llenar)
    CENTER  // Centrar (tamaño original)
}

/**
 * Tipos de fuente disponibles para el launcher
 * Incluye fuentes del sistema y fuentes personalizadas (TTF)
 */
enum class NevenFontFamily(val displayName: String) {
    SERIF("Serif"),                    // Sistema - Serif clásico (LaTeX style)
    SANS_SERIF("Sans-serif"),          // Sistema - Moderno limpio
    MONOSPACE("Monospace"),            // Sistema - Técnico/código
    CURSIVE("Cursive"),                // Sistema - Elegante/artístico
    ROBOTO("Roboto"),                  // Google - Sans moderna
    OPEN_SANS("Open Sans"),            // Google - Sans limpia
    PLAYFAIR("Playfair Display"),      // Google - Serif títulos
    JETBRAINS_MONO("JetBrains Mono"),  // JetBrains - Mono profesional
    SOURCE_CODE_PRO("Source Code Pro") // Adobe - Mono legible
}

/**
 * Escala del elemento seleccionado en listas haptic
 */
enum class HapticScale(val scale: Float, val displayName: String) {
    SMALL(1.15f, "Pequeño"),
    MEDIUM(1.25f, "Mediano"),
    LARGE(1.35f, "Grande"),
    EXTRA_LARGE(1.5f, "Extra grande")
}

/**
 * Intensidad de vibración haptic
 */
enum class HapticIntensity(val displayName: String) {
    NONE("Ninguna"),
    LIGHT("Suave"),
    MEDIUM("Media"),
    STRONG("Fuerte")
}

/**
 * Sonidos de selección haptic
 */
enum class HapticSound(val displayName: String) {
    NONE("Ninguno"),
    CLICK("Click"),
    TICK("Tick"),
    POP("Pop")
}

class SettingsRepository(private val context: Context) {
    
    companion object {
        // Claves para DataStore
        private val SEARCH_ENGINE_KEY = stringPreferencesKey("search_engine")
        private val PALETTE_KEY = stringPreferencesKey("palette")
        private val THEME_MODE_KEY = stringPreferencesKey("theme_mode")
        private val LANGUAGE_KEY = stringPreferencesKey("language")
        private val SHOW_SECONDS_KEY = booleanPreferencesKey("show_seconds")
        private val MAX_FAVORITES_KEY = intPreferencesKey("max_favorites")
        private val FONT_SIZE_OPTION_KEY = stringPreferencesKey("font_size_option")
        private val FONT_SIZE_SCALE_KEY = floatPreferencesKey("font_size_scale")
        
        // Claves para fondo de pantalla
        private val BACKGROUND_TYPE_KEY = stringPreferencesKey("background_type")
        private val BACKGROUND_IMAGE_URI_KEY = stringPreferencesKey("background_image_uri")
        private val BACKGROUND_POSITION_KEY = stringPreferencesKey("background_position")
        private val BACKGROUND_OPACITY_KEY = floatPreferencesKey("background_opacity")
        private val BACKGROUND_TINT_ENABLED_KEY = booleanPreferencesKey("background_tint_enabled")
        
        // Clave para color de contraste personalizado (paleta Clásico)
        private val CUSTOM_ACCENT_COLOR_KEY = stringPreferencesKey("custom_accent_color")
        
        // Clave para tipo de fuente
        private val FONT_FAMILY_KEY = stringPreferencesKey("font_family")
        
        // Clave para sincronizar fondo con pantalla de bloqueo
        private val SYNC_LOCK_SCREEN_WALLPAPER_KEY = booleanPreferencesKey("sync_lock_screen_wallpaper")
        
        // Claves para configuración haptic
        private val HAPTIC_SCALE_KEY = stringPreferencesKey("haptic_scale")
        private val HAPTIC_INTENSITY_KEY = stringPreferencesKey("haptic_intensity")
        private val HAPTIC_SOUND_KEY = stringPreferencesKey("haptic_sound")
        
        // Clave para botón flotante de recientes
        private val FLOATING_RECENTS_ENABLED_KEY = booleanPreferencesKey("floating_recents_enabled")
        
        // Valores por defecto
        private const val DEFAULT_SEARCH_ENGINE = "GOOGLE"
        private const val DEFAULT_PALETTE = "CLASICO"
        private const val DEFAULT_THEME_MODE = "DARK"
        private const val DEFAULT_LANGUAGE = "es"
        private const val DEFAULT_SHOW_SECONDS = true
        private const val DEFAULT_MAX_FAVORITES = 8
        private const val DEFAULT_FONT_SIZE_OPTION = "M"
        private const val DEFAULT_FONT_SIZE_SCALE = 1.0f
        
        // Valores por defecto para fondo de pantalla
        private const val DEFAULT_BACKGROUND_TYPE = "IMAGE"  // Usar imagen por defecto
        private const val DEFAULT_BACKGROUND_POSITION = "CROP"
        private const val DEFAULT_BACKGROUND_OPACITY = 0.6f  // Medio (λ = 0.6)
        private const val DEFAULT_BACKGROUND_TINT_ENABLED = false
        
        // URI especial para el fondo predeterminado incluido en la app
        const val DEFAULT_BACKGROUND_RESOURCE = "android.resource://com.neven.launcher/drawable/fondo_default"
        
        // Valor por defecto para color de contraste (rojo clásico)
        private const val DEFAULT_CUSTOM_ACCENT_COLOR = "#D32F2F"
        
        // Valor por defecto para tipo de fuente (Serif - académico)
        private const val DEFAULT_FONT_FAMILY = "SERIF"
        
        // Valor por defecto para sincronizar lock screen
        private const val DEFAULT_SYNC_LOCK_SCREEN = false
        
        // Valores por defecto para haptic
        private const val DEFAULT_HAPTIC_SCALE = "LARGE"
        private const val DEFAULT_HAPTIC_INTENSITY = "MEDIUM"
        private const val DEFAULT_HAPTIC_SOUND = "NONE"
        
        // Valor por defecto para botón flotante
        private const val DEFAULT_FLOATING_RECENTS_ENABLED = false
        
        @Volatile
        private var instance: SettingsRepository? = null
        
        fun getInstance(context: Context): SettingsRepository {
            return instance ?: synchronized(this) {
                instance ?: SettingsRepository(context.applicationContext).also {
                    instance = it
                }
            }
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // MOTOR DE BÚSQUEDA
    // ═══════════════════════════════════════════════════════════════
    
    val searchEngineFlow: Flow<SearchEngine> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[SEARCH_ENGINE_KEY] ?: DEFAULT_SEARCH_ENGINE
        try {
            SearchEngine.valueOf(name)
        } catch (e: Exception) {
            SearchEngine.GOOGLE
        }
    }
    
    suspend fun setSearchEngine(engine: SearchEngine) {
        context.settingsDataStore.edit { prefs ->
            prefs[SEARCH_ENGINE_KEY] = engine.name
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // PALETA DE COLORES
    // ═══════════════════════════════════════════════════════════════
    
    val paletteFlow: Flow<NevenPalette> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[PALETTE_KEY] ?: DEFAULT_PALETTE
        try {
            NevenPalette.valueOf(name)
        } catch (e: Exception) {
            NevenPalette.CLASICO
        }
    }
    
    suspend fun setPalette(palette: NevenPalette) {
        context.settingsDataStore.edit { prefs ->
            prefs[PALETTE_KEY] = palette.name
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // MODO DE TEMA (Claro/Oscuro/Auto)
    // ═══════════════════════════════════════════════════════════════
    
    val themeModeFlow: Flow<ThemeMode> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[THEME_MODE_KEY] ?: DEFAULT_THEME_MODE
        try {
            ThemeMode.valueOf(name)
        } catch (e: Exception) {
            ThemeMode.DARK
        }
    }
    
    suspend fun setThemeMode(mode: ThemeMode) {
        context.settingsDataStore.edit { prefs ->
            prefs[THEME_MODE_KEY] = mode.name
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // IDIOMA
    // ═══════════════════════════════════════════════════════════════
    
    val languageFlow: Flow<String> = context.settingsDataStore.data.map { prefs ->
        prefs[LANGUAGE_KEY] ?: DEFAULT_LANGUAGE
    }
    
    suspend fun setLanguage(language: String) {
        context.settingsDataStore.edit { prefs ->
            prefs[LANGUAGE_KEY] = language
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // MOSTRAR SEGUNDOS
    // ═══════════════════════════════════════════════════════════════
    
    val showSecondsFlow: Flow<Boolean> = context.settingsDataStore.data.map { prefs ->
        prefs[SHOW_SECONDS_KEY] ?: DEFAULT_SHOW_SECONDS
    }
    
    suspend fun setShowSeconds(show: Boolean) {
        context.settingsDataStore.edit { prefs ->
            prefs[SHOW_SECONDS_KEY] = show
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // MÁXIMO DE FAVORITOS
    // ═══════════════════════════════════════════════════════════════
    
    val maxFavoritesFlow: Flow<Int> = context.settingsDataStore.data.map { prefs ->
        prefs[MAX_FAVORITES_KEY] ?: DEFAULT_MAX_FAVORITES
    }
    
    suspend fun setMaxFavorites(max: Int) {
        val validMax = max.coerceIn(6, 10)
        context.settingsDataStore.edit { prefs ->
            prefs[MAX_FAVORITES_KEY] = validMax
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // TAMAÑO DE LETRA
    // ═══════════════════════════════════════════════════════════════
    
    val fontSizeOptionFlow: Flow<FontSizeOption> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[FONT_SIZE_OPTION_KEY] ?: DEFAULT_FONT_SIZE_OPTION
        try {
            FontSizeOption.valueOf(name)
        } catch (e: Exception) {
            FontSizeOption.M
        }
    }
    
    val fontSizeScaleFlow: Flow<Float> = context.settingsDataStore.data.map { prefs ->
        prefs[FONT_SIZE_SCALE_KEY] ?: DEFAULT_FONT_SIZE_SCALE
    }
    
    suspend fun setFontSize(option: FontSizeOption) {
        context.settingsDataStore.edit { prefs ->
            prefs[FONT_SIZE_OPTION_KEY] = option.name
            prefs[FONT_SIZE_SCALE_KEY] = option.scale
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // UTILIDADES
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Genera la URL de búsqueda completa para un query dado
     */
    fun getSearchUrl(engine: SearchEngine, query: String): String {
        return engine.baseUrl + java.net.URLEncoder.encode(query, "UTF-8")
    }
    
    // ═══════════════════════════════════════════════════════════════
    // FONDO DE PANTALLA
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Tipo de fondo: SOLID (color de paleta) o IMAGE (imagen de galería)
     */
    val backgroundTypeFlow: Flow<BackgroundType> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[BACKGROUND_TYPE_KEY] ?: DEFAULT_BACKGROUND_TYPE
        try {
            BackgroundType.valueOf(name)
        } catch (e: Exception) {
            BackgroundType.SOLID
        }
    }
    
    suspend fun setBackgroundType(type: BackgroundType) {
        context.settingsDataStore.edit { prefs ->
            prefs[BACKGROUND_TYPE_KEY] = type.name
        }
    }
    
    /**
     * URI de la imagen de fondo seleccionada
     */
    val backgroundImageUriFlow: Flow<String?> = context.settingsDataStore.data.map { prefs ->
        // Si no hay URI guardada, usar el fondo predeterminado incluido
        prefs[BACKGROUND_IMAGE_URI_KEY] ?: DEFAULT_BACKGROUND_RESOURCE
    }
    
    suspend fun setBackgroundImageUri(uri: String?) {
        context.settingsDataStore.edit { prefs ->
            if (uri != null) {
                prefs[BACKGROUND_IMAGE_URI_KEY] = uri
            } else {
                prefs.remove(BACKGROUND_IMAGE_URI_KEY)
            }
        }
    }
    
    /**
     * Posición de la imagen: FIT, CROP, CENTER
     */
    val backgroundPositionFlow: Flow<BackgroundPosition> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[BACKGROUND_POSITION_KEY] ?: DEFAULT_BACKGROUND_POSITION
        try {
            BackgroundPosition.valueOf(name)
        } catch (e: Exception) {
            BackgroundPosition.CROP
        }
    }
    
    suspend fun setBackgroundPosition(position: BackgroundPosition) {
        context.settingsDataStore.edit { prefs ->
            prefs[BACKGROUND_POSITION_KEY] = position.name
        }
    }
    
    /**
     * Opacidad del overlay oscuro (λ): 0.2, 0.4, 0.6, 0.8
     */
    val backgroundOpacityFlow: Flow<Float> = context.settingsDataStore.data.map { prefs ->
        prefs[BACKGROUND_OPACITY_KEY] ?: DEFAULT_BACKGROUND_OPACITY
    }
    
    suspend fun setBackgroundOpacity(opacity: Float) {
        // Validar que sea uno de los valores permitidos
        val validOpacity = when {
            opacity <= 0.2f -> 0.2f
            opacity <= 0.4f -> 0.4f
            opacity <= 0.6f -> 0.6f
            else -> 0.8f
        }
        context.settingsDataStore.edit { prefs ->
            prefs[BACKGROUND_OPACITY_KEY] = validOpacity
        }
    }
    
    /**
     * Tinte de paleta habilitado (aplica tinte sutil del color primario)
     */
    val backgroundTintEnabledFlow: Flow<Boolean> = context.settingsDataStore.data.map { prefs ->
        prefs[BACKGROUND_TINT_ENABLED_KEY] ?: DEFAULT_BACKGROUND_TINT_ENABLED
    }
    
    suspend fun setBackgroundTintEnabled(enabled: Boolean) {
        context.settingsDataStore.edit { prefs ->
            prefs[BACKGROUND_TINT_ENABLED_KEY] = enabled
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // COLOR DE CONTRASTE PERSONALIZADO (para paleta Clásico)
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Color de contraste/acento personalizado para la paleta Clásico.
     * Almacenado como cadena hexadecimal (ej: "#D32F2F").
     * Default: rojo (#D32F2F)
     */
    val customAccentColorFlow: Flow<String> = context.settingsDataStore.data.map { prefs ->
        prefs[CUSTOM_ACCENT_COLOR_KEY] ?: DEFAULT_CUSTOM_ACCENT_COLOR
    }
    
    suspend fun setCustomAccentColor(hexColor: String) {
        context.settingsDataStore.edit { prefs ->
            prefs[CUSTOM_ACCENT_COLOR_KEY] = hexColor
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // TIPO DE FUENTE
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Tipo de fuente seleccionado para todo el launcher.
     * Opciones: SERIF (default), SANS_SERIF, MONOSPACE, CURSIVE
     */
    val fontFamilyFlow: Flow<NevenFontFamily> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[FONT_FAMILY_KEY] ?: DEFAULT_FONT_FAMILY
        try {
            NevenFontFamily.valueOf(name)
        } catch (e: Exception) {
            NevenFontFamily.SERIF
        }
    }
    
    suspend fun setFontFamily(family: NevenFontFamily) {
        context.settingsDataStore.edit { prefs ->
            prefs[FONT_FAMILY_KEY] = family.name
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // SINCRONIZAR FONDO CON PANTALLA DE BLOQUEO
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Si está habilitado, el fondo de pantalla del launcher también se aplica
     * a la pantalla de bloqueo del sistema.
     */
    val syncLockScreenWallpaperFlow: Flow<Boolean> = context.settingsDataStore.data.map { prefs ->
        prefs[SYNC_LOCK_SCREEN_WALLPAPER_KEY] ?: DEFAULT_SYNC_LOCK_SCREEN
    }
    
    suspend fun setSyncLockScreenWallpaper(sync: Boolean) {
        context.settingsDataStore.edit { prefs ->
            prefs[SYNC_LOCK_SCREEN_WALLPAPER_KEY] = sync
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // CONFIGURACIÓN HAPTIC FEEDBACK
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Escala del elemento seleccionado durante navegación haptic
     */
    val hapticScaleFlow: Flow<HapticScale> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[HAPTIC_SCALE_KEY] ?: DEFAULT_HAPTIC_SCALE
        try {
            HapticScale.valueOf(name)
        } catch (e: Exception) {
            HapticScale.LARGE
        }
    }
    
    suspend fun setHapticScale(scale: HapticScale) {
        context.settingsDataStore.edit { prefs ->
            prefs[HAPTIC_SCALE_KEY] = scale.name
        }
    }
    
    /**
     * Intensidad de vibración durante navegación haptic
     */
    val hapticIntensityFlow: Flow<HapticIntensity> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[HAPTIC_INTENSITY_KEY] ?: DEFAULT_HAPTIC_INTENSITY
        try {
            HapticIntensity.valueOf(name)
        } catch (e: Exception) {
            HapticIntensity.MEDIUM
        }
    }
    
    suspend fun setHapticIntensity(intensity: HapticIntensity) {
        context.settingsDataStore.edit { prefs ->
            prefs[HAPTIC_INTENSITY_KEY] = intensity.name
        }
    }
    
    /**
     * Sonido de selección durante navegación haptic
     */
    val hapticSoundFlow: Flow<HapticSound> = context.settingsDataStore.data.map { prefs ->
        val name = prefs[HAPTIC_SOUND_KEY] ?: DEFAULT_HAPTIC_SOUND
        try {
            HapticSound.valueOf(name)
        } catch (e: Exception) {
            HapticSound.NONE
        }
    }
    
    suspend fun setHapticSound(sound: HapticSound) {
        context.settingsDataStore.edit { prefs ->
            prefs[HAPTIC_SOUND_KEY] = sound.name
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // BOTÓN FLOTANTE DE RECIENTES
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Estado del botón flotante de recientes
     */
    val floatingRecentsEnabledFlow: Flow<Boolean> = context.settingsDataStore.data.map { prefs ->
        prefs[FLOATING_RECENTS_ENABLED_KEY] ?: DEFAULT_FLOATING_RECENTS_ENABLED
    }
    
    suspend fun setFloatingRecentsEnabled(enabled: Boolean) {
        context.settingsDataStore.edit { prefs ->
            prefs[FLOATING_RECENTS_ENABLED_KEY] = enabled
        }
    }
}
