package com.neven.launcher.ui.settings

import android.app.Activity
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.R
import com.neven.launcher.data.BackgroundPosition
import com.neven.launcher.data.BackgroundType
import com.neven.launcher.data.FontSizeOption
import com.neven.launcher.data.HapticIntensity
import com.neven.launcher.data.HapticScale
import com.neven.launcher.data.HapticSound
import com.neven.launcher.data.NevenFontFamily as FontFamilyOption
import com.neven.launcher.data.SearchEngine
import com.neven.launcher.data.ThemeMode
import com.neven.launcher.ui.components.NevenBackground
import com.neven.launcher.ui.components.SettingsItem
import com.neven.launcher.ui.theme.*
import com.neven.launcher.ui.theme.LocalCustomAccentColor
import java.util.Locale

/**
 * NEVEN Settings Screen - Rediseño con estilo científico sobrio
 * 
 * Lista vertical estilo Microsoft Launcher con estética académica:
 * - Símbolos científicos a la izquierda (un solo color)
 * - Títulos en negrita + descripciones en gris
 * - Espaciado generoso como paper académico
 * - Sin emojis, tipografía serif para símbolos
 * 
 * Secciones:
 * - Motor de búsqueda (∂)
 * - Apariencia (λ)
 * - Tamaño de letra (Aa)
 * - Pantalla de inicio (∘)
 * - Cajón de aplicaciones (≡)
 * - Tiempo de pantalla (τ)
 * - Idioma (ξ)
 * - Acerca de (§)
 */

/**
 * Enum para las pantallas de navegación de Settings
 */
enum class SettingsDestination {
    MAIN,
    SEARCH_ENGINE,
    APPEARANCE,
    FONT_SIZE,
    FONT_FAMILY,
    HOME_SCREEN,
    PAGES,
    APP_DRAWER,
    HAPTIC,
    CALENDAR,
    NOTIFICATIONS,
    STICKY_NOTES,
    AI_DIAGNOSTICS,
    SCREEN_TIME,
    FLOATING_RECENTS,
    LANGUAGE,
    ABOUT
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    currentPalette: NevenPalette,
    isDarkMode: Boolean,
    showSeconds: Boolean,
    currentLanguage: String,
    currentSearchEngine: SearchEngine = SearchEngine.GOOGLE,
    currentThemeMode: ThemeMode = if (isDarkMode) ThemeMode.DARK else ThemeMode.LIGHT,
    maxFavorites: Int = 8,
    currentFontSizeOption: FontSizeOption = FontSizeOption.M,
    // Parámetro de tipo de fuente
    currentFontFamily: FontFamilyOption = FontFamilyOption.SERIF,
    // Parámetros de fondo de pantalla
    backgroundType: BackgroundType = BackgroundType.SOLID,
    backgroundImageUri: String? = null,
    backgroundPosition: BackgroundPosition = BackgroundPosition.CROP,
    backgroundOpacity: Float = 0.4f,
    backgroundTintEnabled: Boolean = false,
    // Parámetro de color de contraste personalizado
    customAccentColor: String = "#D32F2F",
    // Parámetros de retroalimentación táctil
    currentHapticScale: HapticScale = HapticScale.LARGE,
    currentHapticIntensity: HapticIntensity = HapticIntensity.MEDIUM,
    currentHapticSound: HapticSound = HapticSound.CLICK,
    onPaletteChange: (NevenPalette) -> Unit,
    onDarkModeChange: (Boolean) -> Unit,
    onShowSecondsChange: (Boolean) -> Unit,
    onLanguageChange: (String) -> Unit,
    onSearchEngineChange: (SearchEngine) -> Unit = {},
    onThemeModeChange: (ThemeMode) -> Unit = {},
    onMaxFavoritesChange: (Int) -> Unit = {},
    onFontSizeChange: (FontSizeOption) -> Unit = {},
    // Callback de tipo de fuente
    onFontFamilyChange: (FontFamilyOption) -> Unit = {},
    // Callbacks de fondo de pantalla
    onBackgroundTypeChange: (BackgroundType) -> Unit = {},
    onBackgroundImageUriChange: (String?) -> Unit = {},
    onBackgroundPositionChange: (BackgroundPosition) -> Unit = {},
    onBackgroundOpacityChange: (Float) -> Unit = {},
    onBackgroundTintEnabledChange: (Boolean) -> Unit = {},
    // Callback de color de contraste personalizado
    onCustomAccentColorChange: (String) -> Unit = {},
    // Callbacks de retroalimentación táctil
    onHapticScaleChange: (HapticScale) -> Unit = {},
    onHapticIntensityChange: (HapticIntensity) -> Unit = {},
    onHapticSoundChange: (HapticSound) -> Unit = {},
    // Parámetros para sincronizar con pantalla de bloqueo
    syncLockScreen: Boolean = false,
    onSyncLockScreenChange: (Boolean) -> Unit = {},
    onOpenScreenTime: () -> Unit = {},
    onBack: () -> Unit
) {
    // Usar LocalCustomAccentColor para obtener el color de contraste personalizado
    val customAccentColorCompose = LocalCustomAccentColor.current
    val colors = getNevenColors(
        palette = currentPalette,
        darkTheme = isDarkMode,
        customAccentColor = if (currentPalette == NevenPalette.CLASICO) customAccentColorCompose else null
    )
    
    // Estado de navegación interna
    var currentDestination by remember { mutableStateOf(SettingsDestination.MAIN) }
    
    // Usar el mismo fondo que HomeScreen para consistencia visual
    NevenBackground(
        backgroundType = backgroundType,
        imageUri = backgroundImageUri,
        position = backgroundPosition,
        opacity = backgroundOpacity,
        tintEnabled = backgroundTintEnabled,
        tintColor = colors.accent,
        fallbackColor = colors.background,
        isDark = colors.isDark
    ) {
        when (currentDestination) {
            SettingsDestination.MAIN -> {
                SettingsMainScreen(
                    colors = colors,
                    onNavigate = { destination ->
                        if (destination == SettingsDestination.SCREEN_TIME) {
                            onOpenScreenTime()
                        } else {
                            currentDestination = destination
                        }
                    },
                    onBack = onBack
                )
            }
            
            SettingsDestination.SEARCH_ENGINE -> {
                SearchEngineDetailScreen(
                    currentEngine = currentSearchEngine,
                    onEngineChange = onSearchEngineChange,
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.APPEARANCE -> {
                AppearanceDetailScreen(
                    currentPalette = currentPalette,
                    currentMode = currentThemeMode,
                    backgroundType = backgroundType,
                    backgroundImageUri = backgroundImageUri,
                    backgroundPosition = backgroundPosition,
                    backgroundOpacity = backgroundOpacity,
                    backgroundTintEnabled = backgroundTintEnabled,
                    customAccentColor = customAccentColor,
                    syncLockScreen = syncLockScreen,
                    onPaletteChange = onPaletteChange,
                    onModeChange = { mode ->
                        onThemeModeChange(mode)
                        when (mode) {
                            ThemeMode.DARK -> onDarkModeChange(true)
                            ThemeMode.LIGHT -> onDarkModeChange(false)
                            ThemeMode.AUTO -> {}
                        }
                    },
                    onBackgroundTypeChange = onBackgroundTypeChange,
                    onImageSelected = { uri ->
                        onBackgroundImageUriChange(uri?.toString())
                    },
                    onPositionChange = onBackgroundPositionChange,
                    onOpacityChange = onBackgroundOpacityChange,
                    onTintEnabledChange = onBackgroundTintEnabledChange,
                    onCustomAccentColorChange = onCustomAccentColorChange,
                    onSyncLockScreenChange = onSyncLockScreenChange,
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.FONT_SIZE -> {
                FontSizeSettingsScreen(
                    currentPalette = currentPalette,
                    isDarkMode = isDarkMode,
                    currentFontSizeOption = currentFontSizeOption,
                    onFontSizeChange = onFontSizeChange,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.FONT_FAMILY -> {
                FontFamilySettingsScreen(
                    currentPalette = currentPalette,
                    isDarkMode = isDarkMode,
                    currentFontFamily = currentFontFamily,
                    onFontFamilyChange = onFontFamilyChange,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.HOME_SCREEN -> {
                HomeScreenDetailScreen(
                    maxFavorites = maxFavorites,
                    showSeconds = showSeconds,
                    onMaxFavoritesChange = onMaxFavoritesChange,
                    onShowSecondsChange = onShowSecondsChange,
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.PAGES -> {
                PagesSettingsScreen(
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.APP_DRAWER -> {
                AppDrawerDetailScreen(
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.HAPTIC -> {
                HapticSettingsScreen(
                    currentScale = currentHapticScale,
                    currentIntensity = currentHapticIntensity,
                    currentSound = currentHapticSound,
                    onScaleChange = onHapticScaleChange,
                    onIntensityChange = onHapticIntensityChange,
                    onSoundChange = onHapticSoundChange,
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.CALENDAR -> {
                CalendarSettingsScreen(
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.NOTIFICATIONS -> {
                NotificationsSettingsScreen(
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.STICKY_NOTES -> {
                NotesSettingsScreen(
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.AI_DIAGNOSTICS -> {
                AIDiagnosticsScreen(
                    onNavigateBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.SCREEN_TIME -> {
                // Manejado externamente via onOpenScreenTime
                currentDestination = SettingsDestination.MAIN
            }
            
            SettingsDestination.FLOATING_RECENTS -> {
                FloatingRecentsSettingsScreen(
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.LANGUAGE -> {
                LanguageDetailScreen(
                    currentLanguage = currentLanguage,
                    onLanguageChange = onLanguageChange,
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
            
            SettingsDestination.ABOUT -> {
                AboutDetailScreen(
                    colors = colors,
                    onBack = { currentDestination = SettingsDestination.MAIN }
                )
            }
        }
    }
}

/**
 * Pantalla principal de Settings con lista de items científicos
 */
@Composable
private fun SettingsMainScreen(
    colors: NevenColors,
    onNavigate: (SettingsDestination) -> Unit,
    onBack: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
    ) {
        // ═══════════════════════════════════════════════════════════════
        // HEADER
        // ═══════════════════════════════════════════════════════════════
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "<",
                modifier = Modifier
                    .clickable { onBack() }
                    .padding(8.dp),
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Text(
                text = stringResource(R.string.settings_title),
                style = MaterialTheme.typography.headlineMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
        }
        
        Divider(color = colors.textSecondary.copy(alpha = 0.15f))
        
        // ═══════════════════════════════════════════════════════════════
        // LISTA DE SETTINGS - Ordenada alfabéticamente
        // ═══════════════════════════════════════════════════════════════
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
        ) {
            // Acerca de - Símbolo: § (sección)
            item {
                SettingsItem(
                    symbol = "\u00A7",  // §
                    title = stringResource(R.string.settings_about),
                    description = stringResource(R.string.settings_about_desc),
                    onClick = { onNavigate(SettingsDestination.ABOUT) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Apariencia - Símbolo: λ (lambda)
            item {
                SettingsItem(
                    symbol = "\u03BB",  // λ
                    title = stringResource(R.string.settings_appearance),
                    description = stringResource(R.string.settings_appearance_desc),
                    onClick = { onNavigate(SettingsDestination.APPEARANCE) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Botón flotante de recientes - Símbolo: ⊡ (squared dot)
            item {
                SettingsItem(
                    symbol = "\u22A1",  // ⊡
                    title = stringResource(R.string.settings_floating_recents),
                    description = stringResource(R.string.settings_floating_recents_desc),
                    onClick = { onNavigate(SettingsDestination.FLOATING_RECENTS) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Cajón de aplicaciones - Símbolo: ≡ (equivalencia)
            item {
                SettingsItem(
                    symbol = "\u2261",  // ≡
                    title = stringResource(R.string.settings_app_drawer),
                    description = stringResource(R.string.settings_app_drawer_desc),
                    onClick = { onNavigate(SettingsDestination.APP_DRAWER) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Calendarios - Símbolo: ◈ (cuadrado con diamante, usado en Glance)
            item {
                SettingsItem(
                    symbol = "◈",
                    title = stringResource(R.string.settings_calendars),
                    description = stringResource(R.string.settings_calendars_desc),
                    onClick = { onNavigate(SettingsDestination.CALENDAR) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Idioma - Símbolo: ξ (xi)
            item {
                SettingsItem(
                    symbol = "\u03BE",  // ξ
                    title = stringResource(R.string.settings_language),
                    description = stringResource(R.string.settings_language_desc),
                    onClick = { onNavigate(SettingsDestination.LANGUAGE) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Inteligencia Local - Símbolo: Ψ (psi - mente/inteligencia)
            item {
                SettingsItem(
                    symbol = "\u03A8",  // Ψ
                    title = "Inteligencia Local",
                    description = "Gemini Nano / Gemma 4 on-device",
                    onClick = { onNavigate(SettingsDestination.AI_DIAGNOSTICS) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Motor de búsqueda - Símbolo: ∂ (derivada parcial)
            item {
                SettingsItem(
                    symbol = "\u2202",  // ∂
                    title = stringResource(R.string.settings_search_engine),
                    description = stringResource(R.string.settings_search_engine_desc),
                    onClick = { onNavigate(SettingsDestination.SEARCH_ENGINE) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Notas adhesivas - Símbolo: ◊ (diamante/nota)
            item {
                SettingsItem(
                    symbol = "◊",
                    title = "Notas adhesivas",
                    description = "Color, tamaño y límites de Post-its",
                    onClick = { onNavigate(SettingsDestination.STICKY_NOTES) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Notificaciones - Símbolo: ∇ (nabla/gradiente - representa papers científicos)
            item {
                SettingsItem(
                    symbol = "∇",
                    title = stringResource(R.string.settings_notifications),
                    description = stringResource(R.string.settings_notifications_desc),
                    onClick = { onNavigate(SettingsDestination.NOTIFICATIONS) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Páginas - Símbolo: ⊞ (suma directa / páginas múltiples)
            item {
                SettingsItem(
                    symbol = "⊞",
                    title = stringResource(R.string.pages_title),
                    description = stringResource(R.string.pages_desc),
                    onClick = { onNavigate(SettingsDestination.PAGES) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Pantalla de inicio - Símbolo: ∘ (composición)
            item {
                SettingsItem(
                    symbol = "\u2218",  // ∘
                    title = stringResource(R.string.settings_home_screen),
                    description = stringResource(R.string.settings_home_screen_desc),
                    onClick = { onNavigate(SettingsDestination.HOME_SCREEN) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Retroalimentación táctil - Símbolo: ∿ (onda sinusoidal)
            item {
                SettingsItem(
                    symbol = "\u223F",  // ∿
                    title = stringResource(R.string.settings_haptic),
                    description = stringResource(R.string.settings_haptic_desc),
                    onClick = { onNavigate(SettingsDestination.HAPTIC) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Tamaño de letra - Símbolo: Aa
            item {
                SettingsItem(
                    symbol = "Aa",
                    title = stringResource(R.string.settings_font_size),
                    description = stringResource(R.string.settings_font_size_desc),
                    onClick = { onNavigate(SettingsDestination.FONT_SIZE) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Tiempo de pantalla - Símbolo: τ (tau)
            item {
                SettingsItem(
                    symbol = "\u03C4",  // τ
                    title = stringResource(R.string.settings_screen_time),
                    description = stringResource(R.string.settings_screen_time_desc),
                    onClick = { onNavigate(SettingsDestination.SCREEN_TIME) },
                    colors = colors
                )
            }
            
            item { SettingsDivider(colors) }
            
            // Tipo de letra - Símbolo: F (Font)
            item {
                SettingsItem(
                    symbol = "F",
                    title = stringResource(R.string.settings_font_family),
                    description = stringResource(R.string.settings_font_family_desc),
                    onClick = { onNavigate(SettingsDestination.FONT_FAMILY) },
                    colors = colors
                )
            }
            
            // Espaciado inferior
            item {
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}

/**
 * Divisor sutil entre items de settings
 */
@Composable
private fun SettingsDivider(colors: NevenColors) {
    Divider(
        modifier = Modifier.padding(start = 64.dp),
        color = colors.textSecondary.copy(alpha = 0.08f),
        thickness = 1.dp
    )
}

// ═══════════════════════════════════════════════════════════════════════════
// PANTALLAS DE DETALLE
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Pantalla de detalle para Motor de búsqueda
 */
@Composable
private fun SearchEngineDetailScreen(
    currentEngine: SearchEngine,
    onEngineChange: (SearchEngine) -> Unit,
    colors: NevenColors,
    onBack: () -> Unit
) {
    DetailScreenScaffold(
        title = stringResource(R.string.settings_search_engine),
        symbol = "\u2202",
        colors = colors,
        onBack = onBack
    ) {
        SearchEngineSelector(
            currentEngine = currentEngine,
            onEngineChange = onEngineChange,
            colors = colors
        )
    }
}

/**
 * Pantalla de detalle para Apariencia
 * Incluye: modo de tema, paleta colapsable (con color de contraste), y fondo de pantalla
 */
@Composable
private fun AppearanceDetailScreen(
    currentPalette: NevenPalette,
    currentMode: ThemeMode,
    backgroundType: BackgroundType,
    backgroundImageUri: String?,
    backgroundPosition: BackgroundPosition,
    backgroundOpacity: Float,
    backgroundTintEnabled: Boolean,
    customAccentColor: String,
    // Parámetros para sincronizar con pantalla de bloqueo
    syncLockScreen: Boolean = false,
    onPaletteChange: (NevenPalette) -> Unit,
    onModeChange: (ThemeMode) -> Unit,
    onBackgroundTypeChange: (BackgroundType) -> Unit,
    onImageSelected: (Uri?) -> Unit,
    onPositionChange: (BackgroundPosition) -> Unit,
    onOpacityChange: (Float) -> Unit,
    onTintEnabledChange: (Boolean) -> Unit,
    onCustomAccentColorChange: (String) -> Unit,
    onSyncLockScreenChange: (Boolean) -> Unit = {},
    colors: NevenColors,
    onBack: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
    ) {
        // Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "<",
                modifier = Modifier
                    .clickable { onBack() }
                    .padding(8.dp),
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            // Símbolo científico λ
            Text(
                text = "\u03BB",
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Text(
                text = stringResource(R.string.settings_appearance),
                style = MaterialTheme.typography.headlineMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
        }
        
        Divider(color = colors.textSecondary.copy(alpha = 0.15f))
        
        // Contenido scrollable
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            // Selector de modo de tema
            ThemeModeSelector(
                currentMode = currentMode,
                onModeChange = onModeChange,
                colors = colors
            )
            
            // Separador
            Divider(color = colors.textSecondary.copy(alpha = 0.1f))
            
            // Selector de paleta colapsable con cuadrados y color de contraste
            CollapsiblePaletteSelector(
                currentPalette = currentPalette,
                onPaletteChange = onPaletteChange,
                colors = colors,
                customAccentColor = customAccentColor,
                onCustomAccentColorChange = onCustomAccentColorChange
            )
            
            // Separador
            Divider(color = colors.textSecondary.copy(alpha = 0.1f))
            
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
            
            // Espaciado inferior
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

/**
 * Pantalla de detalle para Pantalla de inicio
 */
@Composable
private fun HomeScreenDetailScreen(
    maxFavorites: Int,
    showSeconds: Boolean,
    onMaxFavoritesChange: (Int) -> Unit,
    onShowSecondsChange: (Boolean) -> Unit,
    colors: NevenColors,
    onBack: () -> Unit
) {
    DetailScreenScaffold(
        title = stringResource(R.string.settings_home_screen),
        symbol = "\u2218",
        colors = colors,
        onBack = onBack
    ) {
        Column(
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            // Selector de favoritos
            FavoritesCountSelector(
                currentCount = maxFavorites,
                onCountChange = onMaxFavoritesChange,
                colors = colors
            )
            
            Divider(color = colors.textSecondary.copy(alpha = 0.1f))
            
            // Toggle de segundos
            SettingsToggle(
                title = stringResource(R.string.settings_show_seconds),
                subtitle = "14\u00B3\u2070\u2084\u2085 \u2192 14\u00B3\u2070",
                checked = showSeconds,
                onCheckedChange = onShowSecondsChange,
                colors = colors
            )
        }
    }
}

/**
 * Pantalla de detalle para Cajón de aplicaciones
 */
@Composable
private fun AppDrawerDetailScreen(
    colors: NevenColors,
    onBack: () -> Unit
) {
    DetailScreenScaffold(
        title = stringResource(R.string.settings_app_drawer),
        symbol = "\u2261",
        colors = colors,
        onBack = onBack
    ) {
        // Placeholder para futuras opciones
        Text(
            text = "Opciones del cajón de apps",
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary
        )
    }
}

/**
 * Pantalla de detalle para Idioma
 */
@Composable
private fun LanguageDetailScreen(
    currentLanguage: String,
    onLanguageChange: (String) -> Unit,
    colors: NevenColors,
    onBack: () -> Unit
) {
    DetailScreenScaffold(
        title = stringResource(R.string.settings_language),
        symbol = "\u03BE",
        colors = colors,
        onBack = onBack
    ) {
        LanguageSelector(
            currentLanguage = currentLanguage,
            onLanguageChange = onLanguageChange,
            colors = colors
        )
    }
}

/**
 * Pantalla de detalle para Acerca de
 */
@Composable
private fun AboutDetailScreen(
    colors: NevenColors,
    onBack: () -> Unit
) {
    DetailScreenScaffold(
        title = stringResource(R.string.settings_about),
        symbol = "\u00A7",
        colors = colors,
        onBack = onBack
    ) {
        Column {
            Text(
                text = "NEVEN",
                style = MaterialTheme.typography.headlineSmall,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = stringResource(R.string.app_tagline),
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Creador
            Text(
                text = stringResource(R.string.about_created_by),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Text(
                text = "Minor Bonilla-Gomez",
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = "${stringResource(R.string.settings_version)}: 1.0.0",
                style = MaterialTheme.typography.bodySmall,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // QED symbol
            Text(
                text = "\u220E",  // ∎
                style = MaterialTheme.typography.titleLarge,
                color = colors.textSecondary.copy(alpha = 0.4f)
            )
        }
    }
}

/**
 * Scaffold reutilizable para pantallas de detalle
 */
@Composable
private fun DetailScreenScaffold(
    title: String,
    symbol: String,
    colors: NevenColors,
    onBack: () -> Unit,
    content: @Composable () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
    ) {
        // Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "<",
                modifier = Modifier
                    .clickable { onBack() }
                    .padding(8.dp),
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            // Símbolo científico
            Text(
                text = symbol,
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Text(
                text = title,
                style = MaterialTheme.typography.headlineMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
        }
        
        Divider(color = colors.textSecondary.copy(alpha = 0.15f))
        
        // Contenido
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
        ) {
            content()
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENTES AUXILIARES (Mantenidos para compatibilidad)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Settings section card with subtle stone border
 */
@Composable
fun SettingsSection(
    title: String,
    colors: NevenColors,
    content: @Composable ColumnScope.() -> Unit
) {
    val cardBg = if (colors.isDark) Color(0xFF1B1B1B).copy(alpha = 0.82f) else Color(0xFFFAF9F6).copy(alpha = 0.9f)
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
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            color = colors.textPrimary,
            fontWeight = FontWeight.SemiBold
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        content()
    }
}

/**
 * Clean, subtle toggle setting item
 */
@Composable
fun SettingsToggle(
    title: String,
    subtitle: String? = null,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    colors: NevenColors
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                color = colors.textPrimary
            )
            if (subtitle != null) {
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.textSecondary
                )
            }
        }
        
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = colors.textPrimary,
                checkedTrackColor = colors.textPrimary.copy(alpha = 0.3f),
                uncheckedThumbColor = colors.textSecondary.copy(alpha = 0.6f),
                uncheckedTrackColor = colors.textSecondary.copy(alpha = 0.15f)
            )
        )
    }
}

/**
 * Text-only palette selector (like the year typography style)
 */
@Composable
fun PaletteSelector(
    currentPalette: NevenPalette,
    onPaletteChange: (NevenPalette) -> Unit,
    colors: NevenColors
) {
    LazyRow(
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)
    ) {
        items(NevenPalette.values()) { palette ->
            val isSelected = palette == currentPalette
            
            Text(
                text = if (isSelected) "[ ${palette.displayName} ]" else palette.displayName,
                modifier = Modifier
                    .clickable { onPaletteChange(palette) }
                    .padding(vertical = 6.dp, horizontal = 4.dp),
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                color = if (isSelected) colors.textPrimary else colors.textSecondary.copy(alpha = 0.5f)
            )
        }
    }
}

/**
 * Clean text-driven language selector
 * Aplica el cambio de idioma recreando la Activity para que
 * el cambio sea aplicado correctamente
 */
@Composable
fun LanguageSelector(
    currentLanguage: String,
    onLanguageChange: (String) -> Unit,
    colors: NevenColors
) {
    val context = LocalContext.current
    val languages = listOf(
        "es" to "Español",
        "en" to "English",
        "eo" to "Esperanto"
    )
    
    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        languages.forEach { (code, name) ->
            val isSelected = code == currentLanguage
            
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        // Guardar el idioma en DataStore
                        onLanguageChange(code)
                        
                        // Cambiar el locale del sistema para esta app
                        val locale = Locale(code)
                        Locale.setDefault(locale)
                        
                        // Recrear la Activity para aplicar el cambio de idioma
                        // Esto es necesario porque Android carga los recursos según
                        // la configuración en el momento de crear la Activity
                        (context as? Activity)?.recreate()
                    }
                    .border(
                        width = 0.5.dp, // Borde delgado minimalista
                        color = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.2f),
                        shape = RoundedCornerShape(12.dp)
                    )
                    .background(
                        color = if (isSelected) colors.accent.copy(alpha = 0.1f) else Color.Transparent,
                        shape = RoundedCornerShape(12.dp)
                    )
                    .padding(horizontal = 20.dp, vertical = 16.dp)
            ) {
                Text(
                    text = name,
                    style = MaterialTheme.typography.titleMedium,
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic,
                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                    color = if (isSelected) colors.textPrimary else colors.textSecondary
                )
            }
        }
    }
}

/**
 * Selector para cantidad de favoritos (6-10)
 */
@Composable
fun FavoritesCountSelector(
    currentCount: Int,
    onCountChange: (Int) -> Unit,
    colors: NevenColors
) {
    Column {
        Text(
            text = "${stringResource(R.string.favorites_count)}: $currentCount",
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Row(
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            (6..10).forEach { count ->
                val isSelected = count == currentCount
                
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .background(
                            color = if (isSelected) colors.accent.copy(alpha = 0.15f) else Color.Transparent,
                            shape = RoundedCornerShape(12.dp)
                        )
                        .border(
                            width = 0.5.dp, // Borde delgado minimalista
                            color = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(12.dp)
                        )
                        .clickable { onCountChange(count) },
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = count.toString(),
                        style = MaterialTheme.typography.titleMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                        color = if (isSelected) colors.textPrimary else colors.textSecondary
                    )
                }
            }
        }
    }
}
