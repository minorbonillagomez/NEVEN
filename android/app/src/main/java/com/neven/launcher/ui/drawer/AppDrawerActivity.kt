package com.neven.launcher.ui.drawer

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
import com.neven.launcher.data.FontSizeOption
import com.neven.launcher.data.HapticIntensity
import com.neven.launcher.data.HapticScale
import com.neven.launcher.data.HapticSound
import com.neven.launcher.data.NevenFontFamily
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.data.ThemeMode
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.NevenTheme
import com.neven.launcher.ui.theme.rememberNevenColors

/**
 * NEVEN App Drawer Activity
 * 
 * Full-screen app list with:
 * - Vertical scrolling list (Niagara style)
 * - Lateral alphabet navigation
 * - Long-press for adding to favorites
 * - Swipe down to close
 */
class AppDrawerActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        enableEdgeToEdge()
        WindowCompat.setDecorFitsSystemWindows(window, false)
        
        setContent {
            // Repositorio de settings
            val settingsRepository = remember { SettingsRepository.getInstance(this) }
            
            // Observar preferencias desde DataStore
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
            
            // Observar configuración de retroalimentación táctil
            val hapticScale by settingsRepository.hapticScaleFlow
                .collectAsState(initial = HapticScale.LARGE)
            val hapticIntensity by settingsRepository.hapticIntensityFlow
                .collectAsState(initial = HapticIntensity.MEDIUM)
            val hapticSound by settingsRepository.hapticSoundFlow
                .collectAsState(initial = HapticSound.CLICK)
            
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
                // Usar rememberNevenColors para aplicar el color de contraste personalizado
                val colors = rememberNevenColors(selectedPalette, isDarkMode)
                
                AppDrawerScreen(
                    colors = colors,
                    backgroundType = backgroundType,
                    backgroundImageUri = backgroundImageUri,
                    backgroundPosition = backgroundPosition,
                    backgroundOpacity = backgroundOpacity,
                    backgroundTintEnabled = backgroundTintEnabled,
                    hapticScale = hapticScale,
                    hapticIntensity = hapticIntensity,
                    hapticSound = hapticSound,
                    onAppClick = { app ->
                        launchApp(app.packageName)
                    },
                    onAppLongClick = { app ->
                        // Long-click es manejado dentro de AppDrawerScreen
                        // con menú contextual para agregar a favoritos
                    },
                    onClose = {
                        finish()
                        overridePendingTransition(0, android.R.anim.fade_out)
                    }
                )
            }
        }
    }
    
    private fun launchApp(packageName: String) {
        try {
            val intent = packageManager.getLaunchIntentForPackage(packageName)
            if (intent != null) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(intent)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        super.onBackPressed()
        overridePendingTransition(0, android.R.anim.fade_out)
    }
}
