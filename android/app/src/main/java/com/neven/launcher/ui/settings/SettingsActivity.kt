package com.neven.launcher.ui.settings

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.*
import androidx.core.view.WindowCompat
import com.neven.launcher.data.BackgroundPosition
import com.neven.launcher.data.BackgroundType
import com.neven.launcher.data.FavoritesRepository
import com.neven.launcher.data.FontSizeOption
import com.neven.launcher.data.HapticIntensity
import com.neven.launcher.data.HapticScale
import com.neven.launcher.data.HapticSound
import com.neven.launcher.data.NevenFontFamily
import com.neven.launcher.data.SearchEngine
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.data.ThemeMode
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.NevenTheme
import kotlinx.coroutines.launch

/**
 * NEVEN Settings Activity
 * 
 * Configuraciones expandidas estilo Microsoft Launcher con diseño científico:
 * - Motor de búsqueda
 * - Tema/Paleta
 * - Fondo de pantalla (color sólido o imagen con opacidad λ)
 * - Tamaño de letra (XS/S/M/L/XL/XXL)
 * - Pantalla de inicio
 * - Cajón de apps
 * - Screen Time
 * - Idioma
 * - Acerca de
 */
class SettingsActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        enableEdgeToEdge()
        WindowCompat.setDecorFitsSystemWindows(window, false)
        
        setContent {
            // Repositorios
            val settingsRepository = remember { SettingsRepository.getInstance(this) }
            val favoritesRepository = remember { FavoritesRepository.getInstance(this) }
            val coroutineScope = rememberCoroutineScope()
            
            // Observar preferencias desde DataStore
            val selectedPalette by settingsRepository.paletteFlow
                .collectAsState(initial = NevenPalette.CLASICO)
            val themeMode by settingsRepository.themeModeFlow
                .collectAsState(initial = ThemeMode.DARK)
            val showSeconds by settingsRepository.showSecondsFlow
                .collectAsState(initial = true)
            val currentLanguage by settingsRepository.languageFlow
                .collectAsState(initial = "es")
            val searchEngine by settingsRepository.searchEngineFlow
                .collectAsState(initial = SearchEngine.GOOGLE)
            val maxFavorites by favoritesRepository.maxFavoritesFlow
                .collectAsState(initial = 8)
            val fontSizeOption by settingsRepository.fontSizeOptionFlow
                .collectAsState(initial = FontSizeOption.M)
            val fontSizeScale by settingsRepository.fontSizeScaleFlow
                .collectAsState(initial = 1.0f)
            val fontFamily by settingsRepository.fontFamilyFlow
                .collectAsState(initial = NevenFontFamily.SERIF)
            
            // Observar configuración de fondo de pantalla
            val backgroundType by settingsRepository.backgroundTypeFlow
                .collectAsState(initial = BackgroundType.SOLID)
            val backgroundImageUri by settingsRepository.backgroundImageUriFlow
                .collectAsState(initial = null)
            val backgroundPosition by settingsRepository.backgroundPositionFlow
                .collectAsState(initial = BackgroundPosition.CROP)
            val backgroundOpacity by settingsRepository.backgroundOpacityFlow
                .collectAsState(initial = 0.4f)
            val backgroundTintEnabled by settingsRepository.backgroundTintEnabledFlow
                .collectAsState(initial = false)
            
            // Observar color de contraste personalizado
            val customAccentColor by settingsRepository.customAccentColorFlow
                .collectAsState(initial = "#D32F2F")
            
            // Observar configuración de sincronizar con pantalla de bloqueo
            val syncLockScreen by settingsRepository.syncLockScreenWallpaperFlow
                .collectAsState(initial = false)
            
            // Observar configuración de retroalimentación táctil
            val hapticScale by settingsRepository.hapticScaleFlow
                .collectAsState(initial = HapticScale.LARGE)
            val hapticIntensity by settingsRepository.hapticIntensityFlow
                .collectAsState(initial = HapticIntensity.MEDIUM)
            val hapticSound by settingsRepository.hapticSoundFlow
                .collectAsState(initial = HapticSound.CLICK)
            
            // Determinar si usar modo oscuro basado en themeMode
            val isSystemDark = isSystemInDarkTheme()
            val isDarkMode = when (themeMode) {
                ThemeMode.DARK -> true
                ThemeMode.LIGHT -> false
                ThemeMode.AUTO -> isSystemDark
            }
            
            NevenTheme(
                palette = selectedPalette,
                darkTheme = isDarkMode,
                fontScale = fontSizeScale,
                fontFamily = fontFamily,
                customAccentColorHex = customAccentColor
            ) {
                SettingsScreen(
                    currentPalette = selectedPalette,
                    isDarkMode = isDarkMode,
                    showSeconds = showSeconds,
                    currentLanguage = currentLanguage,
                    currentSearchEngine = searchEngine,
                    currentThemeMode = themeMode,
                    maxFavorites = maxFavorites,
                    currentFontSizeOption = fontSizeOption,
                    currentFontFamily = fontFamily,
                    // Parámetros de fondo de pantalla
                    backgroundType = backgroundType,
                    backgroundImageUri = backgroundImageUri,
                    backgroundPosition = backgroundPosition,
                    backgroundOpacity = backgroundOpacity,
                    backgroundTintEnabled = backgroundTintEnabled,
                    // Parámetro de color de contraste personalizado
                    customAccentColor = customAccentColor,
                    // Parámetros de retroalimentación táctil
                    currentHapticScale = hapticScale,
                    currentHapticIntensity = hapticIntensity,
                    currentHapticSound = hapticSound,
                    onPaletteChange = { palette ->
                        coroutineScope.launch {
                            settingsRepository.setPalette(palette)
                        }
                    },
                    onDarkModeChange = { dark ->
                        // Este callback ya no se usa directamente, 
                        // usamos onThemeModeChange en su lugar
                    },
                    onShowSecondsChange = { show ->
                        coroutineScope.launch {
                            settingsRepository.setShowSeconds(show)
                        }
                    },
                    onLanguageChange = { language ->
                        coroutineScope.launch {
                            settingsRepository.setLanguage(language)
                        }
                    },
                    onSearchEngineChange = { engine ->
                        coroutineScope.launch {
                            settingsRepository.setSearchEngine(engine)
                        }
                    },
                    onThemeModeChange = { mode ->
                        coroutineScope.launch {
                            settingsRepository.setThemeMode(mode)
                        }
                    },
                    onMaxFavoritesChange = { max ->
                        coroutineScope.launch {
                            favoritesRepository.setMaxFavorites(max)
                        }
                    },
                    onFontSizeChange = { option ->
                        coroutineScope.launch {
                            settingsRepository.setFontSize(option)
                        }
                    },
                    onFontFamilyChange = { family ->
                        coroutineScope.launch {
                            settingsRepository.setFontFamily(family)
                        }
                    },
                    // Callbacks de fondo de pantalla
                    onBackgroundTypeChange = { type ->
                        coroutineScope.launch {
                            settingsRepository.setBackgroundType(type)
                        }
                    },
                    onBackgroundImageUriChange = { uri ->
                        coroutineScope.launch {
                            settingsRepository.setBackgroundImageUri(uri)
                        }
                    },
                    onBackgroundPositionChange = { position ->
                        coroutineScope.launch {
                            settingsRepository.setBackgroundPosition(position)
                        }
                    },
                    onBackgroundOpacityChange = { opacity ->
                        coroutineScope.launch {
                            settingsRepository.setBackgroundOpacity(opacity)
                        }
                    },
                    onBackgroundTintEnabledChange = { enabled ->
                        coroutineScope.launch {
                            settingsRepository.setBackgroundTintEnabled(enabled)
                        }
                    },
                    // Callback de color de contraste personalizado
                    onCustomAccentColorChange = { hexColor ->
                        coroutineScope.launch {
                            settingsRepository.setCustomAccentColor(hexColor)
                        }
                    },
                    // Callbacks de retroalimentación táctil
                    onHapticScaleChange = { scale ->
                        coroutineScope.launch {
                            settingsRepository.setHapticScale(scale)
                        }
                    },
                    onHapticIntensityChange = { intensity ->
                        coroutineScope.launch {
                            settingsRepository.setHapticIntensity(intensity)
                        }
                    },
                    onHapticSoundChange = { sound ->
                        coroutineScope.launch {
                            settingsRepository.setHapticSound(sound)
                        }
                    },
                    // Parámetros para sincronizar con pantalla de bloqueo
                    syncLockScreen = syncLockScreen,
                    onSyncLockScreenChange = { sync ->
                        coroutineScope.launch {
                            settingsRepository.setSyncLockScreenWallpaper(sync)
                        }
                    },
                    onOpenScreenTime = {
                        val intent = Intent(this, ScreenTimeActivity::class.java)
                        startActivity(intent)
                    },
                    onBack = { finish() }
                )
            }
        }
    }
}
