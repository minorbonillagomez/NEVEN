package com.neven.launcher.ui.home

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.*
import androidx.core.view.WindowCompat
import androidx.fragment.app.FragmentActivity
import com.neven.launcher.data.NevenFontFamily
import com.neven.launcher.data.PagesRepository
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.data.ThemeMode
import com.neven.launcher.ui.drawer.AppDrawerActivity
import com.neven.launcher.ui.settings.SettingsActivity
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.NevenTheme
import kotlinx.coroutines.launch

/**
 * NEVEN Launcher Home Activity
 * 
 * The main launcher activity that displays:
 * - Horizontal pager with multiple pages
 * - Home page: Scientific clock + Favorite apps
 * - Glance page: Calendar widget + Weather
 * - User-customizable widget pages
 */
class HomeActivity : FragmentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Enable edge-to-edge display
        enableEdgeToEdge()
        WindowCompat.setDecorFitsSystemWindows(window, false)
        
        setContent {
            // Repositorios
            val settingsRepository = remember { SettingsRepository.getInstance(this) }
            val pagesRepository = remember { PagesRepository.getInstance(this) }
            val coroutineScope = rememberCoroutineScope()
            
            // Inicializar páginas con Glance si es primera vez
            LaunchedEffect(Unit) {
                pagesRepository.pagesFlow.collect { currentPages ->
                    // Si solo hay HOME, agregar Glance (solo la primera vez)
                    if (currentPages.size == 1 && currentPages.first().type == com.neven.launcher.data.PageType.HOME) {
                        pagesRepository.initializeWithGlance()
                    }
                    return@collect
                }
            }
            
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
                // Usar el nuevo LauncherPager con múltiples páginas
                LauncherPager(
                    palette = selectedPalette,
                    isDarkMode = isDarkMode,
                    onOpenSettings = {
                        val intent = Intent(this, SettingsActivity::class.java)
                        startActivity(intent)
                    },
                    onOpenAppDrawer = {
                        val intent = Intent(this, AppDrawerActivity::class.java)
                        intent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                        startActivity(intent)
                        overridePendingTransition(android.R.anim.fade_in, 0)
                    },
                    onLaunchApp = { packageName ->
                        launchApp(packageName)
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
            } else {
                Toast.makeText(this, "No se pudo abrir la aplicación", Toast.LENGTH_SHORT).show()
            }
        } catch (e: Exception) {
            Toast.makeText(this, "Error al abrir la aplicación", Toast.LENGTH_SHORT).show()
        }
    }
    
    override fun onResume() {
        super.onResume()
        // Nothing special needed on resume anymore
    }
    
    // Prevent back button from closing the launcher
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        // Do nothing - launcher should not close on back press
    }
}
