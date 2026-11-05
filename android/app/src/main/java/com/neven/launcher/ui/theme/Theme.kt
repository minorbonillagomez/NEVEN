package com.neven.launcher.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.Density
import androidx.core.view.WindowCompat
import com.neven.launcher.R
import com.neven.launcher.data.NevenFontFamily as FontFamilyEnum
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf

/**
 * NEVEN Theme System
 * 
 * Supports 7 color palettes with dark/light modes
 * and custom clock colors for the scientific display.
 * 
 * Incluye soporte para escala global de tamaño de letra (XS/S/M/L/XL/XXL)
 * y color de contraste personalizado para paleta Clásico.
 */

// ════════════════════════════════════════════════════════════════════════════
// FUENTES PERSONALIZADAS (TTF incluidas en la app)
// ════════════════════════════════════════════════════════════════════════════

/** Roboto - Sans-serif moderna de Google */
val RobotoFontFamily = FontFamily(Font(R.font.roboto))

/** Open Sans - Sans-serif limpia y legible */
val OpenSansFontFamily = FontFamily(Font(R.font.opensans))

/** Playfair Display - Serif para títulos elegantes */
val PlayfairFontFamily = FontFamily(Font(R.font.playfairdisplay))

/** JetBrains Mono - Monospace profesional para código */
val JetBrainsMonoFontFamily = FontFamily(Font(R.font.jetbrainsmono))

/** Source Code Pro - Monospace legible de Adobe */
val SourceCodeProFontFamily = FontFamily(Font(R.font.sourcecodepro))

/**
 * CompositionLocal para el factor de escala de fuente.
 * Permite acceder al factor de escala desde cualquier composable.
 */
val LocalFontScale = compositionLocalOf { 1.0f }

/**
 * CompositionLocal para el color de contraste personalizado (paleta Clásico).
 * Valor por defecto: rojo clásico (#D32F2F)
 */
val LocalCustomAccentColor = compositionLocalOf { Color(0xFFD32F2F) }

/**
 * CompositionLocal para la familia de fuentes seleccionada por el usuario.
 * Permite acceder a la fuente configurada desde cualquier composable.
 * Valor por defecto: Serif (estilo académico/LaTeX)
 */
val LocalNevenFontFamily = compositionLocalOf<FontFamily> { FontFamily.Serif }

data class NevenColors(
    val background: Color,
    val textPrimary: Color,
    val textSecondary: Color,
    val hourColor: Color,
    val minuteColor: Color,
    val secondColor: Color,
    val accent: Color,
    val isDark: Boolean
)

/**
 * Convierte una cadena hexadecimal a Color
 */
private fun hexToColorInternal(hex: String): Color {
    return try {
        val cleanHex = hex.removePrefix("#")
        val colorInt = cleanHex.toLong(16)
        Color(
            red = ((colorInt shr 16) and 0xFF) / 255f,
            green = ((colorInt shr 8) and 0xFF) / 255f,
            blue = (colorInt and 0xFF) / 255f
        )
    } catch (e: Exception) {
        Color(0xFFD32F2F) // Rojo por defecto
    }
}

/**
 * Helper composable que obtiene los colores NEVEN con soporte automático
 * para el color de contraste personalizado desde LocalCustomAccentColor.
 * Usar esta función en lugar de getNevenColors() para que el color de contraste
 * se aplique automáticamente cuando la paleta es CLASICO.
 */
@Composable
fun rememberNevenColors(
    palette: NevenPalette = NevenPalette.CLASICO,
    isDarkMode: Boolean = isSystemInDarkTheme()
): NevenColors {
    val customAccentColor = LocalCustomAccentColor.current
    return getNevenColors(
        palette = palette,
        darkTheme = isDarkMode,
        customAccentColor = if (palette == NevenPalette.CLASICO) customAccentColor else null
    )
}

@Composable
fun getNevenColors(
    palette: NevenPalette = NevenPalette.CLASICO,
    darkTheme: Boolean = isSystemInDarkTheme(),
    customAccentColor: Color? = null
): NevenColors {
    return when (palette) {
        NevenPalette.CLASICO -> {
            // Para Clásico, usar el color de contraste personalizado si está disponible
            val accentColor = customAccentColor ?: PaletteClasico.accent
            if (darkTheme) {
                NevenColors(
                    background = PaletteClasico.backgroundDark,
                    textPrimary = PaletteClasico.textPrimaryDark,
                    textSecondary = PaletteClasico.textSecondaryDark,
                    hourColor = accentColor,
                    minuteColor = PaletteClasico.minuteDark,
                    secondColor = PaletteClasico.secondDark,
                    accent = accentColor,
                    isDark = true
                )
            } else {
                NevenColors(
                    background = PaletteClasico.backgroundLight,
                    textPrimary = PaletteClasico.textPrimaryLight,
                    textSecondary = PaletteClasico.textSecondaryLight,
                    hourColor = accentColor,
                    minuteColor = PaletteClasico.minuteLight,
                    secondColor = PaletteClasico.secondLight,
                    accent = accentColor,
                    isDark = false
                )
            }
        }
        
        NevenPalette.OCEANO -> if (darkTheme) {
            NevenColors(
                background = PaletteOceano.backgroundDark,
                textPrimary = PaletteOceano.textPrimaryDark,
                textSecondary = PaletteOceano.textSecondaryDark,
                hourColor = PaletteOceano.hourDark,
                minuteColor = PaletteOceano.minuteDark,
                secondColor = PaletteOceano.secondDark,
                accent = PaletteOceano.accent,
                isDark = true
            )
        } else {
            NevenColors(
                background = PaletteOceano.backgroundLight,
                textPrimary = PaletteOceano.textPrimaryLight,
                textSecondary = PaletteOceano.textSecondaryLight,
                hourColor = PaletteOceano.hourLight,
                minuteColor = PaletteOceano.minuteLight,
                secondColor = PaletteOceano.secondLight,
                accent = PaletteOceano.accent,
                isDark = false
            )
        }
        
        NevenPalette.BOSQUE -> if (darkTheme) {
            NevenColors(
                background = PaletteBosque.backgroundDark,
                textPrimary = PaletteBosque.textPrimaryDark,
                textSecondary = PaletteBosque.textSecondaryDark,
                hourColor = PaletteBosque.hourDark,
                minuteColor = PaletteBosque.minuteDark,
                secondColor = PaletteBosque.secondDark,
                accent = PaletteBosque.accent,
                isDark = true
            )
        } else {
            NevenColors(
                background = PaletteBosque.backgroundLight,
                textPrimary = PaletteBosque.textPrimaryLight,
                textSecondary = PaletteBosque.textSecondaryLight,
                hourColor = PaletteBosque.hourLight,
                minuteColor = PaletteBosque.minuteLight,
                secondColor = PaletteBosque.secondLight,
                accent = PaletteBosque.accent,
                isDark = false
            )
        }
        
        NevenPalette.AMBAR -> if (darkTheme) {
            NevenColors(
                background = PaletteAmbar.backgroundDark,
                textPrimary = PaletteAmbar.textPrimaryDark,
                textSecondary = PaletteAmbar.textSecondaryDark,
                hourColor = PaletteAmbar.hourDark,
                minuteColor = PaletteAmbar.minuteDark,
                secondColor = PaletteAmbar.secondDark,
                accent = PaletteAmbar.accent,
                isDark = true
            )
        } else {
            NevenColors(
                background = PaletteAmbar.backgroundLight,
                textPrimary = PaletteAmbar.textPrimaryLight,
                textSecondary = PaletteAmbar.textSecondaryLight,
                hourColor = PaletteAmbar.hourLight,
                minuteColor = PaletteAmbar.minuteLight,
                secondColor = PaletteAmbar.secondLight,
                accent = PaletteAmbar.accent,
                isDark = false
            )
        }
        
        NevenPalette.LAVANDA -> if (darkTheme) {
            NevenColors(
                background = PaletteLavanda.backgroundDark,
                textPrimary = PaletteLavanda.textPrimaryDark,
                textSecondary = PaletteLavanda.textSecondaryDark,
                hourColor = PaletteLavanda.hourDark,
                minuteColor = PaletteLavanda.minuteDark,
                secondColor = PaletteLavanda.secondDark,
                accent = PaletteLavanda.accent,
                isDark = true
            )
        } else {
            NevenColors(
                background = PaletteLavanda.backgroundLight,
                textPrimary = PaletteLavanda.textPrimaryLight,
                textSecondary = PaletteLavanda.textSecondaryLight,
                hourColor = PaletteLavanda.hourLight,
                minuteColor = PaletteLavanda.minuteLight,
                secondColor = PaletteLavanda.secondLight,
                accent = PaletteLavanda.accent,
                isDark = false
            )
        }
        
        NevenPalette.MONOCROMO -> if (darkTheme) {
            NevenColors(
                background = PaletteMonocromo.backgroundDark,
                textPrimary = PaletteMonocromo.textPrimaryDark,
                textSecondary = PaletteMonocromo.textSecondaryDark,
                hourColor = PaletteMonocromo.hourDark,
                minuteColor = PaletteMonocromo.minuteDark,
                secondColor = PaletteMonocromo.secondDark,
                accent = PaletteMonocromo.accent,
                isDark = true
            )
        } else {
            NevenColors(
                background = PaletteMonocromo.backgroundLight,
                textPrimary = PaletteMonocromo.textPrimaryLight,
                textSecondary = PaletteMonocromo.textSecondaryLight,
                hourColor = PaletteMonocromo.hourLight,
                minuteColor = PaletteMonocromo.minuteLight,
                secondColor = PaletteMonocromo.secondLight,
                accent = PaletteMonocromo.accent,
                isDark = false
            )
        }
        
        NevenPalette.KOBENHAVN -> if (darkTheme) {
            NevenColors(
                background = PaletteKobenhavn.backgroundDark,
                textPrimary = PaletteKobenhavn.textPrimaryDark,
                textSecondary = PaletteKobenhavn.textSecondaryDark,
                hourColor = PaletteKobenhavn.hourDark,
                minuteColor = PaletteKobenhavn.minuteDark,
                secondColor = PaletteKobenhavn.secondDark,
                accent = PaletteKobenhavn.accent,
                isDark = true
            )
        } else {
            NevenColors(
                background = PaletteKobenhavn.backgroundLight,
                textPrimary = PaletteKobenhavn.textPrimaryLight,
                textSecondary = PaletteKobenhavn.textSecondaryLight,
                hourColor = PaletteKobenhavn.hourLight,
                minuteColor = PaletteKobenhavn.minuteLight,
                secondColor = PaletteKobenhavn.secondLight,
                accent = PaletteKobenhavn.accent,
                isDark = false
            )
        }
    }
}

@Composable
fun NevenTheme(
    palette: NevenPalette = NevenPalette.CLASICO,
    darkTheme: Boolean = isSystemInDarkTheme(),
    fontScale: Float = 1.0f,
    fontFamily: FontFamilyEnum = FontFamilyEnum.SERIF,
    customAccentColorHex: String = "#D32F2F",
    content: @Composable () -> Unit
) {
    // Convertir hex a Color
    val customAccentColor = hexToColorInternal(customAccentColorHex)
    
    // Convertir FontFamilyEnum a Compose FontFamily
    val composeFontFamily = when (fontFamily) {
        FontFamilyEnum.SERIF -> FontFamily.Serif
        FontFamilyEnum.SANS_SERIF -> FontFamily.SansSerif
        FontFamilyEnum.MONOSPACE -> FontFamily.Monospace
        FontFamilyEnum.CURSIVE -> FontFamily.Cursive
        FontFamilyEnum.ROBOTO -> RobotoFontFamily
        FontFamilyEnum.OPEN_SANS -> OpenSansFontFamily
        FontFamilyEnum.PLAYFAIR -> PlayfairFontFamily
        FontFamilyEnum.JETBRAINS_MONO -> JetBrainsMonoFontFamily
        FontFamilyEnum.SOURCE_CODE_PRO -> SourceCodeProFontFamily
    }
    
    // Crear tipografía con la fuente seleccionada
    val typography = createNevenTypography(composeFontFamily)
    
    // Obtener colores según paleta, aplicando color personalizado si es Clásico
    val nevenColors = getNevenColors(
        palette = palette,
        darkTheme = darkTheme,
        customAccentColor = if (palette == NevenPalette.CLASICO) customAccentColor else null
    )
    
    val colorScheme = if (darkTheme) {
        darkColorScheme(
            primary = nevenColors.accent,
            onPrimary = nevenColors.textPrimary,
            background = nevenColors.background,
            onBackground = nevenColors.textPrimary,
            surface = nevenColors.background,
            onSurface = nevenColors.textPrimary,
            secondary = nevenColors.textSecondary,
            onSecondary = nevenColors.background
        )
    } else {
        lightColorScheme(
            primary = nevenColors.accent,
            onPrimary = nevenColors.background,
            background = nevenColors.background,
            onBackground = nevenColors.textPrimary,
            surface = nevenColors.background,
            onSurface = nevenColors.textPrimary,
            secondary = nevenColors.textSecondary,
            onSecondary = nevenColors.textPrimary
        )
    }

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = nevenColors.background.toArgb()
            window.navigationBarColor = nevenColors.background.toArgb()
            WindowCompat.getInsetsController(window, view).apply {
                isAppearanceLightStatusBars = !darkTheme
                isAppearanceLightNavigationBars = !darkTheme
            }
        }
    }

    // Aplicar escala de fuente global usando Density modificada
    val currentDensity = LocalDensity.current
    val scaledDensity = Density(
        density = currentDensity.density,
        fontScale = currentDensity.fontScale * fontScale
    )

    CompositionLocalProvider(
        LocalDensity provides scaledDensity,
        LocalFontScale provides fontScale,
        LocalCustomAccentColor provides customAccentColor,
        LocalNevenFontFamily provides composeFontFamily
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = typography,
            content = content
        )
    }
}
