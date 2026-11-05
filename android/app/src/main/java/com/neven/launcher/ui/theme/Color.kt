package com.neven.launcher.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * NEVEN Launcher - Color Palettes
 * 
 * Each palette has:
 * - backgroundDark / backgroundLight
 * - textPrimary / textSecondary
 * - hourColor (for clock)
 * - minuteColor (superscript)
 * - secondColor (subscript)
 * - accent
 */

// ═══════════════════════════════════════════════════════════════
// CLÁSICO - Academic Red
// ═══════════════════════════════════════════════════════════════
object PaletteClasico {
    val backgroundDark = Color(0xFF1A1A1A)
    val backgroundLight = Color(0xFFFAF9F6)
    
    val textPrimaryDark = Color(0xFFFAF9F6)
    val textPrimaryLight = Color(0xFF1A1A1A)
    
    val textSecondaryDark = Color(0xFFA8A8A8)
    val textSecondaryLight = Color(0xFF6B6B6B)
    
    // Clock colors - Dark mode
    val hourDark = Color(0xFFDC2626)      // Rojo
    val minuteDark = Color(0xFFA8A8A8)    // Gris claro
    val secondDark = Color(0xFF4A4A4A)    // Gris oscuro
    
    // Clock colors - Light mode
    val hourLight = Color(0xFFDC2626)     // Rojo
    val minuteLight = Color(0xFF2D2D2D)   // Gris grafito
    val secondLight = Color(0xFF6B6B6B)   // Gris oscuro medio
    
    val accent = Color(0xFFDC2626)
}

// ═══════════════════════════════════════════════════════════════
// OCÉANO - Deep Blue
// ═══════════════════════════════════════════════════════════════
object PaletteOceano {
    val backgroundDark = Color(0xFF0D1B2A)
    val backgroundLight = Color(0xFFE0FBFC)
    
    val textPrimaryDark = Color(0xFFE0FBFC)
    val textPrimaryLight = Color(0xFF0D1B2A)
    
    val textSecondaryDark = Color(0xFF98C1D9)
    val textSecondaryLight = Color(0xFF3D5A80)
    
    val hourDark = Color(0xFF3D5A80)
    val minuteDark = Color(0xFF98C1D9)
    val secondDark = Color(0xFF1B263B)
    
    val hourLight = Color(0xFF3D5A80)
    val minuteLight = Color(0xFF0D1B2A)
    val secondLight = Color(0xFF3D5A80)
    
    val accent = Color(0xFF3D5A80)
}

// ═══════════════════════════════════════════════════════════════
// BOSQUE - Forest Green
// ═══════════════════════════════════════════════════════════════
object PaletteBosque {
    val backgroundDark = Color(0xFF1B2E1B)
    val backgroundLight = Color(0xFFF4FFF4)
    
    val textPrimaryDark = Color(0xFFF4FFF4)
    val textPrimaryLight = Color(0xFF1B2E1B)
    
    val textSecondaryDark = Color(0xFF95D5B2)
    val textSecondaryLight = Color(0xFF2D6A4F)
    
    val hourDark = Color(0xFF40916C)
    val minuteDark = Color(0xFF95D5B2)
    val secondDark = Color(0xFF1B4332)
    
    val hourLight = Color(0xFF2D6A4F)
    val minuteLight = Color(0xFF1B4332)
    val secondLight = Color(0xFF40916C)
    
    val accent = Color(0xFF2D6A4F)
}

// ═══════════════════════════════════════════════════════════════
// ÁMBAR - Warm Orange
// ═══════════════════════════════════════════════════════════════
object PaletteAmbar {
    val backgroundDark = Color(0xFF1C1410)
    val backgroundLight = Color(0xFFFFF8F0)
    
    val textPrimaryDark = Color(0xFFFFF8F0)
    val textPrimaryLight = Color(0xFF1C1410)
    
    val textSecondaryDark = Color(0xFFFBBF24)
    val textSecondaryLight = Color(0xFF92400E)
    
    val hourDark = Color(0xFFD97706)
    val minuteDark = Color(0xFFFBBF24)
    val secondDark = Color(0xFF78350F)
    
    val hourLight = Color(0xFFD97706)
    val minuteLight = Color(0xFF78350F)
    val secondLight = Color(0xFF92400E)
    
    val accent = Color(0xFFD97706)
}

// ═══════════════════════════════════════════════════════════════
// LAVANDA - Creative Purple
// ═══════════════════════════════════════════════════════════════
object PaletteLavanda {
    val backgroundDark = Color(0xFF1A1625)
    val backgroundLight = Color(0xFFFAF5FF)
    
    val textPrimaryDark = Color(0xFFFAF5FF)
    val textPrimaryLight = Color(0xFF1A1625)
    
    val textSecondaryDark = Color(0xFFC4B5FD)
    val textSecondaryLight = Color(0xFF6D28D9)
    
    val hourDark = Color(0xFF8B5CF6)
    val minuteDark = Color(0xFFC4B5FD)
    val secondDark = Color(0xFF4C1D95)
    
    val hourLight = Color(0xFF7C3AED)
    val minuteLight = Color(0xFF4C1D95)
    val secondLight = Color(0xFF6D28D9)
    
    val accent = Color(0xFF7C3AED)
}

// ═══════════════════════════════════════════════════════════════
// MONOCROMO - Pure Minimal
// ═══════════════════════════════════════════════════════════════
object PaletteMonocromo {
    val backgroundDark = Color(0xFF000000)
    val backgroundLight = Color(0xFFFFFFFF)
    
    val textPrimaryDark = Color(0xFFFFFFFF)
    val textPrimaryLight = Color(0xFF000000)
    
    val textSecondaryDark = Color(0xFF737373)
    val textSecondaryLight = Color(0xFF525252)
    
    val hourDark = Color(0xFFFFFFFF)
    val minuteDark = Color(0xFF737373)
    val secondDark = Color(0xFF404040)
    
    val hourLight = Color(0xFF000000)
    val minuteLight = Color(0xFF404040)
    val secondLight = Color(0xFF737373)
    
    val accent = Color(0xFF525252)
}

// ═══════════════════════════════════════════════════════════════
// KØBENHAVN - Danish Design (Pastel Hygge)
// ═══════════════════════════════════════════════════════════════
object PaletteKobenhavn {
    val backgroundDark = Color(0xFF2C3E4A)    // Gris nórdico
    val backgroundLight = Color(0xFFF5F0EB)   // Lino crudo
    
    val textPrimaryDark = Color(0xFFF5F0EB)   // Lino
    val textPrimaryLight = Color(0xFF2C3E4A)  // Gris nórdico
    
    val textSecondaryDark = Color(0xFF6B8A8A) // Musgo apagado
    val textSecondaryLight = Color(0xFF6B8A8A)
    
    // Acentos escandinavos
    val sandFria = Color(0xFFE8DED5)          // Arena fría
    val nieblaBáltica = Color(0xFFB8C4C8)     // Niebla báltica
    val piedraOscura = Color(0xFF3D5259)      // Piedra oscura
    val musgoApagado = Color(0xFF6B8A8A)      // Musgo
    
    // Clock colors - Dark mode
    val hourDark = Color(0xFFD4B896)          // Roble cálido
    val minuteDark = Color(0xFF6B8A8A)        // Musgo
    val secondDark = Color(0xFF3D5259)        // Piedra
    
    // Clock colors - Light mode
    val hourLight = Color(0xFFC4A77D)         // Roble claro
    val minuteLight = Color(0xFF6B8A8A)       // Musgo
    val secondLight = Color(0xFFB8C4C8)       // Niebla
    
    val accent = Color(0xFFC4A77D)            // Roble
}

// ═══════════════════════════════════════════════════════════════
// Palette Enum for Selection
// ═══════════════════════════════════════════════════════════════
enum class NevenPalette(val displayName: String) {
    CLASICO("Clásico"),
    OCEANO("Océano"),
    BOSQUE("Bosque"),
    AMBAR("Ámbar"),
    LAVANDA("Lavanda"),
    MONOCROMO("Monocromo"),
    KOBENHAVN("København")
}
