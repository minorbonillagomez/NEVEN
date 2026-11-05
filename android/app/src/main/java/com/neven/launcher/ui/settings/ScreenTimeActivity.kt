package com.neven.launcher.ui.settings

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.*
import androidx.core.view.WindowCompat
import com.neven.launcher.data.FontSizeOption
import com.neven.launcher.data.NevenFontFamily
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.data.ThemeMode
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.NevenTheme

/**
 * NEVEN Screen Time Activity
 * 
 * Muestra estadísticas de uso de apps:
 * - Tiempo de uso diario
 * - Tiempo de uso semanal
 * - Top apps por uso
 */
class ScreenTimeActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        enableEdgeToEdge()
        WindowCompat.setDecorFitsSystemWindows(window, false)
        
        setContent {
            // Repositorio de settings
            val settingsRepository = remember { SettingsRepository.getInstance(this) }
            
            // Observar preferencias
            val selectedPalette by settingsRepository.paletteFlow
                .collectAsState(initial = NevenPalette.CLASICO)
            val themeMode by settingsRepository.themeModeFlow
                .collectAsState(initial = ThemeMode.DARK)
            val fontSizeScale by settingsRepository.fontSizeScaleFlow
                .collectAsState(initial = 1.0f)
            val customAccentColor by settingsRepository.customAccentColorFlow
                .collectAsState(initial = "#D32F2F")
            val fontFamily by settingsRepository.fontFamilyFlow
                .collectAsState(initial = NevenFontFamily.SERIF)
            
            // Determinar modo oscuro
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
                ScreenTimeScreen(
                    currentPalette = selectedPalette,
                    isDarkMode = isDarkMode,
                    onBack = { finish() }
                )
            }
        }
    }
}
