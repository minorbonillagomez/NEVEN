package com.neven.launcher.ui.settings

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.neven.launcher.R
import com.neven.launcher.data.BackgroundPosition
import com.neven.launcher.data.BackgroundType
import com.neven.launcher.data.ThemeMode
import com.neven.launcher.ui.components.AccentColorPresets
import com.neven.launcher.ui.components.ColorPickerDialog
import com.neven.launcher.ui.components.colorToHex
import com.neven.launcher.ui.components.hexToColor
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.NevenPalette

/**
 * Componente de configuración de tema y paleta.
 * 
 * Incluye:
 * - Selector de 7 paletas (acordeón colapsable con cuadrados)
 * - Modo: Claro / Oscuro / Auto
 * - Fondo de pantalla: Color sólido / Imagen
 * - Opacidad con notación científica (λ)
 * - Tinte de paleta
 * - Color de contraste personalizado (para paleta Clásico)
 * 
 * Estilo de botones: seleccionados tienen SOLO BORDE/CONTORNO, sin fondo
 */

/**
 * Selector de modo de tema (Claro / Oscuro / Auto)
 * Estilo: botón seleccionado tiene SOLO BORDE/CONTORNO, fondo transparente
 */
@Composable
fun ThemeModeSelector(
    currentMode: ThemeMode,
    onModeChange: (ThemeMode) -> Unit,
    colors: NevenColors
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = stringResource(R.string.settings_theme_mode),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(4.dp))
        
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            ThemeMode.values().forEach { mode ->
                ThemeModeChip(
                    mode = mode,
                    isSelected = mode == currentMode,
                    colors = colors,
                    onClick = { onModeChange(mode) }
                )
            }
        }
    }
}

/**
 * Chip para selección de modo de tema
 * Estilo: seleccionado = solo borde, el texto NO cambia de color
 */
@Composable
private fun ThemeModeChip(
    mode: ThemeMode,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    // Seleccionado: fondo transparente, solo borde con color accent
    val backgroundColor = Color.Transparent
    
    val borderColor = if (isSelected) {
        colors.accent
    } else {
        colors.textSecondary.copy(alpha = 0.3f)
    }
    
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))    // Clip primero para ripple correcto
            .clickable(onClick = onClick)       // Clickable ANTES del background para que funcione
            .background(
                color = backgroundColor,
                shape = RoundedCornerShape(8.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = borderColor,
                shape = RoundedCornerShape(8.dp)
            )
            .padding(horizontal = 16.dp, vertical = 10.dp)
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            // Símbolo según modo (científico, sin emojis)
            // El texto NO cambia de color al seleccionar, solo el borde
            Text(
                text = when (mode) {
                    ThemeMode.LIGHT -> "L"
                    ThemeMode.DARK -> "D"
                    ThemeMode.AUTO -> "A"
                },
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold,
                color = colors.textSecondary
            )
            
            Text(
                text = getThemeModeLabel(mode),
                style = MaterialTheme.typography.labelLarge,
                fontFamily = NevenFontFamily,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary
            )
        }
    }
}

/**
 * Obtiene el label localizado para el modo de tema
 */
@Composable
private fun getThemeModeLabel(mode: ThemeMode): String {
    return when (mode) {
        ThemeMode.LIGHT -> stringResource(R.string.settings_theme_light)
        ThemeMode.DARK -> stringResource(R.string.settings_theme_dark)
        ThemeMode.AUTO -> stringResource(R.string.settings_theme_auto)
    }
}

/**
 * Selector de paleta COLAPSABLE - acordeón
 * Por defecto muestra solo el nombre de la paleta activa
 * Al tocar se expande mostrando las 7 opciones con cuadrados
 * 
 * Si la paleta seleccionada es CLASICO, muestra opción de color de contraste
 */
@Composable
fun CollapsiblePaletteSelector(
    currentPalette: NevenPalette,
    onPaletteChange: (NevenPalette) -> Unit,
    colors: NevenColors,
    // Parámetros para color de contraste personalizado
    customAccentColor: String = "#D32F2F",
    onCustomAccentColorChange: (String) -> Unit = {}
) {
    var isExpanded by remember { mutableStateOf(false) }
    var showColorPicker by remember { mutableStateOf(false) }
    
    Column(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Header clickable para expandir/colapsar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { isExpanded = !isExpanded }
                .padding(vertical = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = stringResource(R.string.settings_palette),
                    style = MaterialTheme.typography.titleMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.SemiBold,
                    color = colors.textPrimary
                )
                // Mostrar paleta activa cuando está colapsado
                if (!isExpanded) {
                    Text(
                        text = getPaletteLocalizedName(currentPalette),
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic,
                        color = colors.textSecondary
                    )
                }
            }
            
            // Indicador de expandir/colapsar
            Text(
                text = if (isExpanded) "[-]" else "[+]",
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.accent
            )
        }
        
        // Grid de paletas (expandible)
        AnimatedVisibility(
            visible = isExpanded,
            enter = expandVertically(),
            exit = shrinkVertically()
        ) {
            LazyVerticalGrid(
                columns = GridCells.Fixed(4),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 200.dp)
                    .padding(top = 8.dp)
            ) {
                items(NevenPalette.values()) { palette ->
                    PaletteSquareItem(
                        palette = palette,
                        isSelected = palette == currentPalette,
                        colors = colors,
                        onClick = {
                            onPaletteChange(palette)
                            isExpanded = false // Colapsar al seleccionar
                        }
                    )
                }
            }
        }
        
        // Sección de color de contraste (solo para paleta Clásico)
        AnimatedVisibility(
            visible = currentPalette == NevenPalette.CLASICO,
            enter = expandVertically(),
            exit = shrinkVertically()
        ) {
            AccentColorSelector(
                currentColor = customAccentColor,
                onColorChange = onCustomAccentColorChange,
                onCustomClick = { showColorPicker = true },
                colors = colors
            )
        }
    }
    
    // Diálogo de selector de color personalizado
    if (showColorPicker) {
        ColorPickerDialog(
            initialColor = hexToColor(customAccentColor),
            colors = colors,
            onDismiss = { showColorPicker = false },
            onColorSelected = { color ->
                onCustomAccentColorChange(colorToHex(color))
                showColorPicker = false
            }
        )
    }
}

/**
 * Selector de color de contraste para paleta Clásico - COLAPSABLE
 * Por defecto está OCULTO, solo muestra el nombre del color actual
 * Al tocar se expande mostrando los 8 presets + botón personalizado
 */
@Composable
private fun AccentColorSelector(
    currentColor: String,
    onColorChange: (String) -> Unit,
    onCustomClick: () -> Unit,
    colors: NevenColors
) {
    // Estado colapsado por defecto (minimalista)
    var isExpanded by remember { mutableStateOf(false) }
    
    // Obtener nombre del color actual
    val colorName = getAccentColorName(currentColor)
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Header clickable para expandir/colapsar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { isExpanded = !isExpanded }
                .padding(vertical = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = stringResource(R.string.accent_color_title),
                    style = MaterialTheme.typography.bodyMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.SemiBold,
                    color = colors.textPrimary
                )
                // Mostrar color activo cuando está colapsado
                if (!isExpanded) {
                    Text(
                        text = colorName,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic,
                        color = colors.textSecondary
                    )
                }
            }
            
            // Indicador de expandir/colapsar
            Text(
                text = if (isExpanded) "[-]" else "[+]",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.accent
            )
        }
        
        // Fila de presets + botón personalizado (expandible)
        AnimatedVisibility(
            visible = isExpanded,
            enter = expandVertically(),
            exit = shrinkVertically()
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 8 presets de colores (cuadrados)
                AccentColorPresets.all.forEach { (color, hex) ->
                    val isSelected = currentColor.equals(hex, ignoreCase = true)
                    Box(
                        modifier = Modifier
                            .size(28.dp)
                            .clip(RoundedCornerShape(4.dp))
                            .background(color)
                            .border(
                                width = 0.5.dp, // Borde delgado minimalista
                                color = if (isSelected) {
                                    colors.textPrimary
                                } else {
                                    colors.textSecondary.copy(alpha = 0.3f)
                                },
                                shape = RoundedCornerShape(4.dp)
                            )
                            .clickable { 
                                onColorChange(hex)
                                isExpanded = false // Colapsar al seleccionar
                            }
                    )
                }
                
                Spacer(modifier = Modifier.weight(1f))
                
                // Botón "Personalizado..."
                Text(
                    text = stringResource(R.string.accent_color_custom),
                    style = MaterialTheme.typography.labelMedium,
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic,
                    color = colors.accent,
                    modifier = Modifier
                        .clickable { onCustomClick() }
                        .border(
                            width = 0.5.dp, // Borde delgado minimalista
                            color = colors.accent.copy(alpha = 0.5f),
                            shape = RoundedCornerShape(4.dp)
                        )
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }
    }
}

/**
 * Obtiene el nombre del color de contraste actual
 */
@Composable
private fun getAccentColorName(hex: String): String {
    // Buscar en presets
    val presetName = AccentColorPresets.all.find { (_, presetHex) ->
        presetHex.equals(hex, ignoreCase = true)
    }
    
    return when {
        presetName != null -> {
            // Devolver nombre del preset
            when (presetName.second.uppercase()) {
                "#D32F2F" -> stringResource(R.string.accent_color_red)
                "#1976D2" -> stringResource(R.string.accent_color_blue)
                "#388E3C" -> stringResource(R.string.accent_color_green)
                "#F57C00" -> stringResource(R.string.accent_color_orange)
                "#7B1FA2" -> stringResource(R.string.accent_color_purple)
                "#00796B" -> stringResource(R.string.accent_color_teal)
                "#C2185B" -> stringResource(R.string.accent_color_pink)
                "#455A64" -> stringResource(R.string.accent_color_gray)
                else -> stringResource(R.string.accent_color_custom)
            }
        }
        else -> stringResource(R.string.accent_color_custom)
    }
}

/**
 * Item individual de paleta con CUADRADO de preview
 * Estilo: seleccionado = solo borde, el texto NO cambia de color
 */
@Composable
private fun PaletteSquareItem(
    palette: NevenPalette,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    val paletteColors = getPalettePreviewColors(palette)
    
    // Seleccionado: solo borde, sin fondo
    val borderColor = if (isSelected) {
        colors.accent
    } else {
        colors.textSecondary.copy(alpha = 0.2f)
    }
    
    Column(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))    // Clip primero para ripple correcto
            .clickable(onClick = onClick)       // Clickable ANTES del background para que funcione
            .background(
                color = Color.Transparent,
                shape = RoundedCornerShape(8.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = borderColor,
                shape = RoundedCornerShape(8.dp)
            )
            .padding(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Preview de colores (3 CUADRADOS en fila)
        Row(
            horizontalArrangement = Arrangement.spacedBy(2.dp)
        ) {
            paletteColors.forEach { color ->
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .background(color = color, shape = RoundedCornerShape(2.dp))
                        .border(
                            width = 0.5.dp,
                            color = colors.textSecondary.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(2.dp)
                        )
                )
            }
        }
        
        Spacer(modifier = Modifier.height(4.dp))
        
        // Nombre de la paleta - texto NO cambia de color, solo el borde indica selección
        Text(
            text = getPaletteLocalizedName(palette),
            style = MaterialTheme.typography.labelSmall,
            fontFamily = NevenFontFamily,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
            color = colors.textSecondary,
            maxLines = 1
        )
    }
}

/**
 * Obtiene el nombre localizado de la paleta
 */
@Composable
private fun getPaletteLocalizedName(palette: NevenPalette): String {
    return when (palette) {
        NevenPalette.CLASICO -> stringResource(R.string.palette_clasico)
        NevenPalette.OCEANO -> stringResource(R.string.palette_oceano)
        NevenPalette.BOSQUE -> stringResource(R.string.palette_bosque)
        NevenPalette.AMBAR -> stringResource(R.string.palette_ambar)
        NevenPalette.LAVANDA -> stringResource(R.string.palette_lavanda)
        NevenPalette.MONOCROMO -> stringResource(R.string.palette_monocromo)
        NevenPalette.KOBENHAVN -> stringResource(R.string.palette_kobenhavn)
    }
}

/**
 * Obtiene colores de preview para cada paleta
 */
private fun getPalettePreviewColors(palette: NevenPalette): List<Color> {
    return when (palette) {
        NevenPalette.CLASICO -> listOf(
            Color(0xFFDC2626),  // Rojo
            Color(0xFF1A1A1A),  // Negro
            Color(0xFFFAF9F6)   // Blanco
        )
        NevenPalette.OCEANO -> listOf(
            Color(0xFF3D5A80),  // Azul
            Color(0xFF0D1B2A),  // Azul oscuro
            Color(0xFFE0FBFC)   // Azul claro
        )
        NevenPalette.BOSQUE -> listOf(
            Color(0xFF2D6A4F),  // Verde
            Color(0xFF1B2E1B),  // Verde oscuro
            Color(0xFFF4FFF4)   // Verde claro
        )
        NevenPalette.AMBAR -> listOf(
            Color(0xFFD97706),  // Ámbar
            Color(0xFF1C1410),  // Marrón
            Color(0xFFFFF8F0)   // Crema
        )
        NevenPalette.LAVANDA -> listOf(
            Color(0xFF7C3AED),  // Púrpura
            Color(0xFF1A1625),  // Púrpura oscuro
            Color(0xFFFAF5FF)   // Lavanda claro
        )
        NevenPalette.MONOCROMO -> listOf(
            Color(0xFF525252),  // Gris
            Color(0xFF000000),  // Negro
            Color(0xFFFFFFFF)   // Blanco
        )
        NevenPalette.KOBENHAVN -> listOf(
            Color(0xFFC4A77D),  // Roble
            Color(0xFF2C3E4A),  // Gris nórdico
            Color(0xFFF5F0EB)   // Lino
        )
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECCIÓN DE FONDO DE PANTALLA
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Sección completa de configuración de fondo de pantalla
 */
@Composable
fun WallpaperSettingsSection(
    backgroundType: BackgroundType,
    backgroundImageUri: String?,
    backgroundPosition: BackgroundPosition,
    backgroundOpacity: Float,
    backgroundTintEnabled: Boolean,
    onBackgroundTypeChange: (BackgroundType) -> Unit,
    onImageSelected: (Uri?) -> Unit,
    onPositionChange: (BackgroundPosition) -> Unit,
    onOpacityChange: (Float) -> Unit,
    onTintEnabledChange: (Boolean) -> Unit,
    colors: NevenColors,
    // Parámetros para sincronizar con pantalla de bloqueo
    syncLockScreen: Boolean = false,
    onSyncLockScreenChange: (Boolean) -> Unit = {}
) {
    val context = LocalContext.current
    
    // Launcher para seleccionar imagen de galería
    val imagePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            // Tomar permiso persistente para la URI
            try {
                context.contentResolver.takePersistableUriPermission(
                    uri,
                    android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION
                )
            } catch (e: Exception) {
                // Algunos proveedores no soportan permisos persistentes
            }
            onImageSelected(uri)
            onBackgroundTypeChange(BackgroundType.IMAGE)
        }
    }
    
    Column(
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Título de sección
        Text(
            text = stringResource(R.string.settings_wallpaper),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        // Selector: Color sólido / Imagen
        Row(
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Opción: Color sólido
            WallpaperTypeOption(
                label = stringResource(R.string.wallpaper_solid_color),
                isSelected = backgroundType == BackgroundType.SOLID,
                colors = colors,
                onClick = { onBackgroundTypeChange(BackgroundType.SOLID) }
            )
            
            // Opción: Imagen
            WallpaperTypeOption(
                label = stringResource(R.string.wallpaper_image),
                isSelected = backgroundType == BackgroundType.IMAGE,
                colors = colors,
                onClick = { 
                    if (backgroundImageUri != null) {
                        onBackgroundTypeChange(BackgroundType.IMAGE)
                    } else {
                        imagePickerLauncher.launch("image/*")
                    }
                }
            )
        }
        
        // Opciones de imagen (solo si hay imagen o tipo es IMAGE)
        AnimatedVisibility(
            visible = backgroundType == BackgroundType.IMAGE || backgroundImageUri != null,
            enter = expandVertically(),
            exit = shrinkVertically()
        ) {
            Column(
                verticalArrangement = Arrangement.spacedBy(16.dp),
                modifier = Modifier.padding(top = 8.dp)
            ) {
                // Botón para seleccionar/cambiar imagen
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(
                            width = 0.5.dp,
                            color = colors.textSecondary.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(8.dp)
                        )
                        .clickable { imagePickerLauncher.launch("image/*") }
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Texto neutro (no rojo) para mantener diseño minimalista
                    Text(
                        text = stringResource(R.string.wallpaper_select_image),
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                    
                    // Preview pequeño si hay imagen
                    if (backgroundImageUri != null) {
                        AsyncImage(
                            model = backgroundImageUri,
                            contentDescription = null,
                            modifier = Modifier
                                .size(40.dp)
                                .clip(RoundedCornerShape(4.dp)),
                            contentScale = ContentScale.Crop
                        )
                    }
                }
                
                // Selector de posición (solo si hay imagen)
                if (backgroundImageUri != null) {
                    // Posición de imagen
                    ImagePositionSelector(
                        currentPosition = backgroundPosition,
                        onPositionChange = onPositionChange,
                        colors = colors
                    )
                    
                    // Opacidad con notación científica λ
                    OpacitySelector(
                        currentOpacity = backgroundOpacity,
                        onOpacityChange = onOpacityChange,
                        colors = colors
                    )
                    
                    // Tinte de paleta
                    PaletteTintSwitch(
                        isEnabled = backgroundTintEnabled,
                        onToggle = onTintEnabledChange,
                        colors = colors
                    )
                    
                    // Switch para sincronizar con pantalla de bloqueo
                    // Solo disponible en Android 7.0+ (API 24)
                    if (com.neven.launcher.util.WallpaperHelper.supportsLockScreenWallpaper()) {
                        LockScreenSyncSwitch(
                            isEnabled = syncLockScreen,
                            onToggle = { enabled ->
                                onSyncLockScreenChange(enabled)
                                // Si se habilita, aplicar el wallpaper actual al lock screen
                                if (enabled && backgroundImageUri != null) {
                                    val uri = Uri.parse(backgroundImageUri)
                                    val success = com.neven.launcher.util.WallpaperHelper.setLockScreenWallpaper(context, uri)
                                    if (!success) {
                                        android.widget.Toast.makeText(
                                            context,
                                            R.string.wallpaper_error,
                                            android.widget.Toast.LENGTH_SHORT
                                        ).show()
                                    }
                                }
                            },
                            colors = colors
                        )
                    }
                }
            }
        }
    }
}

/**
 * Opción de tipo de fondo (Radio button estilizado)
 * Estilo: seleccionado = solo borde, el texto NO cambia de color
 */
@Composable
private fun WallpaperTypeOption(
    label: String,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))    // Clip primero para ripple correcto
            .clickable(onClick = onClick)       // Clickable ANTES del background para que funcione
            .background(
                color = Color.Transparent,
                shape = RoundedCornerShape(8.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.3f),
                shape = RoundedCornerShape(8.dp)
            )
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        RadioButton(
            selected = isSelected,
            onClick = onClick,
            colors = RadioButtonDefaults.colors(
                selectedColor = colors.accent,
                unselectedColor = colors.textSecondary
            ),
            modifier = Modifier.size(20.dp)
        )
        // Texto NO cambia de color, solo el borde indica selección
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary
        )
    }
}

/**
 * Selector de posición de imagen
 */
@Composable
private fun ImagePositionSelector(
    currentPosition: BackgroundPosition,
    onPositionChange: (BackgroundPosition) -> Unit,
    colors: NevenColors
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = stringResource(R.string.wallpaper_position),
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            BackgroundPosition.values().forEach { position ->
                PositionChip(
                    position = position,
                    isSelected = position == currentPosition,
                    colors = colors,
                    onClick = { onPositionChange(position) }
                )
            }
        }
    }
}

/**
 * Chip para posición de imagen
 * Estilo: seleccionado = solo borde, el texto NO cambia de color
 */
@Composable
private fun PositionChip(
    position: BackgroundPosition,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    val label = when (position) {
        BackgroundPosition.FIT -> stringResource(R.string.wallpaper_fit)
        BackgroundPosition.CROP -> stringResource(R.string.wallpaper_fill)
        BackgroundPosition.CENTER -> stringResource(R.string.wallpaper_center)
    }
    
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))    // Clip primero para ripple correcto
            .clickable(onClick = onClick)       // Clickable ANTES del background para que funcione
            .background(
                color = Color.Transparent,
                shape = RoundedCornerShape(6.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.3f),
                shape = RoundedCornerShape(6.dp)
            )
            .padding(horizontal = 12.dp, vertical = 8.dp)
    ) {
        // Texto NO cambia de color, solo el borde indica selección
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            fontFamily = NevenFontFamily,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
            color = colors.textSecondary
        )
    }
}

/**
 * Selector de opacidad con notación científica λ
 */
@Composable
private fun OpacitySelector(
    currentOpacity: Float,
    onOpacityChange: (Float) -> Unit,
    colors: NevenColors
) {
    // Opciones de opacidad: λ = 0.2, 0.4, 0.6, 0.8
    val opacityOptions = listOf(
        0.2f to stringResource(R.string.wallpaper_opacity_light),
        0.4f to stringResource(R.string.wallpaper_opacity_soft),
        0.6f to stringResource(R.string.wallpaper_opacity_medium),
        0.8f to stringResource(R.string.wallpaper_opacity_dark)
    )
    
    Column(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Título con símbolo lambda
        Text(
            text = stringResource(R.string.wallpaper_opacity_label),
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        // Radio buttons para cada nivel de opacidad
        Column(
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            opacityOptions.forEach { (value, label) ->
                OpacityRadioOption(
                    value = value,
                    label = label,
                    isSelected = currentOpacity == value,
                    colors = colors,
                    onClick = { onOpacityChange(value) }
                )
            }
        }
    }
}

/**
 * Radio button para opción de opacidad
 * El texto NO cambia de color, solo el RadioButton indica selección
 */
@Composable
private fun OpacityRadioOption(
    value: Float,
    label: String,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        RadioButton(
            selected = isSelected,
            onClick = onClick,
            colors = RadioButtonDefaults.colors(
                selectedColor = colors.accent,
                unselectedColor = colors.textSecondary
            ),
            modifier = Modifier.size(20.dp)
        )
        
        // Label con valor de λ - texto NO cambia de color
        Text(
            text = "$label (${String.format("%.1f", value)})",
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary
        )
    }
}

/**
 * Switch para tinte de paleta
 */
@Composable
private fun PaletteTintSwitch(
    isEnabled: Boolean,
    onToggle: (Boolean) -> Unit,
    colors: NevenColors
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = stringResource(R.string.wallpaper_palette_tint),
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            color = colors.textPrimary
        )
        
        Switch(
            checked = isEnabled,
            onCheckedChange = onToggle,
            colors = SwitchDefaults.colors(
                checkedThumbColor = colors.accent,
                checkedTrackColor = colors.accent.copy(alpha = 0.3f),
                uncheckedThumbColor = colors.textSecondary,
                uncheckedTrackColor = colors.textSecondary.copy(alpha = 0.2f)
            )
        )
    }
}

/**
 * Switch para sincronizar fondo con pantalla de bloqueo
 */
@Composable
private fun LockScreenSyncSwitch(
    isEnabled: Boolean,
    onToggle: (Boolean) -> Unit,
    colors: NevenColors
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = stringResource(R.string.sync_lock_screen),
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                color = colors.textPrimary
            )
            Text(
                text = stringResource(R.string.sync_lock_screen_description),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
        }
        
        Switch(
            checked = isEnabled,
            onCheckedChange = onToggle,
            colors = SwitchDefaults.colors(
                checkedThumbColor = colors.accent,
                checkedTrackColor = colors.accent.copy(alpha = 0.3f),
                uncheckedThumbColor = colors.textSecondary,
                uncheckedTrackColor = colors.textSecondary.copy(alpha = 0.2f)
            )
        )
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CARD COMPLETA PARA SETTINGS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Card completa para la sección de tema en Settings
 * Incluye: modo de tema, paleta colapsable (con color de contraste), y fondo de pantalla
 */
@Composable
fun ThemeSettingsCard(
    currentPalette: NevenPalette,
    currentMode: ThemeMode,
    onPaletteChange: (NevenPalette) -> Unit,
    onModeChange: (ThemeMode) -> Unit,
    colors: NevenColors,
    // Parámetros para fondo de pantalla
    backgroundType: BackgroundType = BackgroundType.SOLID,
    backgroundImageUri: String? = null,
    backgroundPosition: BackgroundPosition = BackgroundPosition.CROP,
    backgroundOpacity: Float = 0.4f,
    backgroundTintEnabled: Boolean = false,
    onBackgroundTypeChange: (BackgroundType) -> Unit = {},
    onImageSelected: (Uri?) -> Unit = {},
    onPositionChange: (BackgroundPosition) -> Unit = {},
    onOpacityChange: (Float) -> Unit = {},
    onTintEnabledChange: (Boolean) -> Unit = {},
    // Parámetros para color de contraste personalizado
    customAccentColor: String = "#D32F2F",
    onCustomAccentColorChange: (String) -> Unit = {},
    // Parámetros para sincronizar con pantalla de bloqueo
    syncLockScreen: Boolean = false,
    onSyncLockScreenChange: (Boolean) -> Unit = {}
) {
    val cardBg = if (colors.isDark) {
        Color(0xFF1B1B1B).copy(alpha = 0.82f)
    } else {
        Color(0xFFFAF9F6).copy(alpha = 0.9f)
    }
    val borderColor = colors.textSecondary.copy(alpha = 0.12f)
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = cardBg,
                shape = RoundedCornerShape(16.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = borderColor,
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        // Header
        Text(
            text = "§ ${stringResource(R.string.settings_appearance)}",
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            color = colors.textPrimary,
            fontWeight = FontWeight.SemiBold
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // Selector de modo
        ThemeModeSelector(
            currentMode = currentMode,
            onModeChange = onModeChange,
            colors = colors
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // Selector de paleta COLAPSABLE con color de contraste
        CollapsiblePaletteSelector(
            currentPalette = currentPalette,
            onPaletteChange = onPaletteChange,
            colors = colors,
            customAccentColor = customAccentColor,
            onCustomAccentColorChange = onCustomAccentColorChange
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Separador visual
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(colors.textSecondary.copy(alpha = 0.15f))
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // Sección de fondo de pantalla
        WallpaperSettingsSection(
            backgroundType = backgroundType,
            backgroundImageUri = backgroundImageUri,
            backgroundPosition = backgroundPosition,
            backgroundOpacity = backgroundOpacity,
            backgroundTintEnabled = backgroundTintEnabled,
            onBackgroundTypeChange = onBackgroundTypeChange,
            onImageSelected = onImageSelected,
            onPositionChange = onPositionChange,
            onOpacityChange = onOpacityChange,
            onTintEnabledChange = onTintEnabledChange,
            colors = colors,
            syncLockScreen = syncLockScreen,
            onSyncLockScreenChange = onSyncLockScreenChange
        )
    }
}

// Mantener compatibilidad con EnhancedPaletteSelector anterior si es usado en otro lugar
@Composable
fun EnhancedPaletteSelector(
    currentPalette: NevenPalette,
    onPaletteChange: (NevenPalette) -> Unit,
    colors: NevenColors
) {
    CollapsiblePaletteSelector(
        currentPalette = currentPalette,
        onPaletteChange = onPaletteChange,
        colors = colors
    )
}
