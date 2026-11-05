package com.neven.launcher.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * NEVEN Typography System
 * 
 * Uses serif fonts for that scientific, academic aesthetic
 * Similar to Computer Modern (LaTeX default font)
 * 
 * Note: For production, replace with actual Computer Modern fonts
 */

// Default font family (Serif for scientific/academic aesthetic)
val DefaultNevenFontFamily = FontFamily.Serif

/**
 * Obtiene la familia de fuentes configurada por el usuario.
 * Debe usarse dentro de un contexto Composable.
 * 
 * Ejemplo de uso:
 * ```
 * Text(
 *     text = "Hola",
 *     fontFamily = NevenFontFamily
 * )
 * ```
 */
val NevenFontFamily: FontFamily
    @Composable
    get() = LocalNevenFontFamily.current

// Typography Scale following Academic Paper hierarchy
// Now a function to support dynamic font family
fun createNevenTypography(fontFamily: FontFamily = DefaultNevenFontFamily): Typography = Typography(
    // Title - Like Paper Title (for Hour display)
    displayLarge = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 72.sp,
        lineHeight = 80.sp,
        letterSpacing = (-0.5).sp
    ),
    
    // Large Display
    displayMedium = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 56.sp,
        lineHeight = 64.sp,
        letterSpacing = (-0.25).sp
    ),
    
    // Medium Display
    displaySmall = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 44.sp,
        lineHeight = 52.sp,
        letterSpacing = 0.sp
    ),
    
    // Subtitle - Like Paper Subtitle (for Date)
    headlineLarge = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 24.sp,
        lineHeight = 32.sp,
        letterSpacing = 0.sp
    ),
    
    // Section Header
    headlineMedium = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.SemiBold,
        fontSize = 20.sp,
        lineHeight = 28.sp,
        letterSpacing = 0.sp
    ),
    
    // Subsection
    headlineSmall = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 18.sp,
        lineHeight = 26.sp,
        letterSpacing = 0.sp
    ),
    
    // Author/Year - Italic smaller (for Year in words)
    titleLarge = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontStyle = FontStyle.Italic,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.sp
    ),
    
    // App names in list
    titleMedium = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Medium,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.15.sp
    ),
    
    // Secondary titles
    titleSmall = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp
    ),
    
    // Body text
    bodyLarge = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.5.sp
    ),
    
    bodyMedium = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.25.sp
    ),
    
    bodySmall = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.4.sp
    ),
    
    // Labels
    labelLarge = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp
    ),
    
    labelMedium = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Medium,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp
    ),
    
    labelSmall = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Medium,
        fontSize = 10.sp,
        lineHeight = 14.sp,
        letterSpacing = 0.5.sp
    )
)

// Default typography instance for backward compatibility
val NevenTypography = createNevenTypography()

/**
 * Data class that holds clock typography styles
 */
data class ClockTypographyStyles(
    val hour: TextStyle,
    val minutes: TextStyle,
    val seconds: TextStyle,
    val date: TextStyle,
    val year: TextStyle
)

/**
 * Special text styles for the scientific clock
 * Now a function to support dynamic font family
 */
fun createClockTypography(fontFamily: FontFamily = DefaultNevenFontFamily) = ClockTypographyStyles(
    // Hour - Title size, bold
    hour = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 72.sp,
        letterSpacing = (-0.5).sp
    ),
    
    // Minutes - Superscript, 60% of hour size
    minutes = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 43.sp,  // 72 * 0.6
        letterSpacing = 0.sp
    ),
    
    // Seconds - Subscript, 50% of hour size
    seconds = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Light,
        fontSize = 36.sp,  // 72 * 0.5
        letterSpacing = 0.sp
    ),
    
    // Date - Subtitle style
    date = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 24.sp,
        lineHeight = 32.sp,
        letterSpacing = 0.sp
    ),
    
    // Year - Author style, italic
    year = TextStyle(
        fontFamily = fontFamily,
        fontWeight = FontWeight.Normal,
        fontStyle = FontStyle.Italic,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.sp
    )
)

// Default ClockTypography for backward compatibility
object ClockTypography {
    private val default = createClockTypography()
    val hour = default.hour
    val minutes = default.minutes
    val seconds = default.seconds
    val date = default.date
    val year = default.year
}
