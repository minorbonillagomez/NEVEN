package com.neven.launcher.ui.home

import android.content.Context
import android.view.HapticFeedbackConstants
import android.widget.Toast
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.layout.positionInParent
import androidx.compose.ui.layout.positionInRoot
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.BaselineShift
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.R
import com.neven.launcher.data.BackgroundPosition
import com.neven.launcher.data.BackgroundType
import com.neven.launcher.data.FavoritesRepository
import com.neven.launcher.data.HapticIntensity
import com.neven.launcher.data.HapticScale
import com.neven.launcher.data.HapticSound
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.ui.components.NevenBackground
import com.neven.launcher.ui.components.ScientificClock
import com.neven.launcher.ui.components.RemoveFromFavoritesMenu
import com.neven.launcher.ui.drawer.loadInstalledApps
import com.neven.launcher.ui.theme.*
import com.neven.launcher.ui.theme.rememberNevenColors
import kotlinx.coroutines.launch
import java.util.Locale
import kotlin.math.abs

/**
 * NEVEN Home Screen
 * 
 * Main launcher interface with:
 * - Scientific clock at top
 * - Favorite apps in vertical list (editable via long-press)
 * - Swipe up for app drawer
 * - Configurable wallpaper (solid color or image with opacity)
 */
@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun HomeScreen(
    palette: NevenPalette,
    isDarkMode: Boolean,
    onPaletteChange: (NevenPalette) -> Unit,
    onDarkModeChange: (Boolean) -> Unit,
    onOpenSettings: () -> Unit = {},
    onOpenAppDrawer: () -> Unit = {},
    onLaunchApp: (String) -> Unit = {}
) {
    // Usar rememberNevenColors para aplicar el color de contraste personalizado
    val colors = rememberNevenColors(palette, isDarkMode)
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    
    // Repositorios
    val favoritesRepository = remember { FavoritesRepository.getInstance(context) }
    val settingsRepository = remember { SettingsRepository.getInstance(context) }
    
    // Observar favoritos desde DataStore
    val favoritePackages by favoritesRepository.favoritesFlow.collectAsState(initial = emptySet())
    val maxFavorites by favoritesRepository.maxFavoritesFlow.collectAsState(initial = 8)
    
    // Observar configuración de fondo de pantalla
    val backgroundType by settingsRepository.backgroundTypeFlow.collectAsState(initial = BackgroundType.SOLID)
    val backgroundImageUri by settingsRepository.backgroundImageUriFlow.collectAsState(initial = null)
    val backgroundPosition by settingsRepository.backgroundPositionFlow.collectAsState(initial = BackgroundPosition.CROP)
    val backgroundOpacity by settingsRepository.backgroundOpacityFlow.collectAsState(initial = 0.4f)
    val backgroundTintEnabled by settingsRepository.backgroundTintEnabledFlow.collectAsState(initial = false)
    
    // Observar configuración haptic
    val hapticScale by settingsRepository.hapticScaleFlow.collectAsState(initial = HapticScale.LARGE)
    val hapticIntensity by settingsRepository.hapticIntensityFlow.collectAsState(initial = HapticIntensity.MEDIUM)
    val hapticSound by settingsRepository.hapticSoundFlow.collectAsState(initial = HapticSound.NONE)
    
    // TODO: Load from preferences
    var locale by remember { mutableStateOf(Locale("es")) }
    var showSeconds by remember { mutableStateOf(true) }
    
    // Cargar apps instaladas - con actualización dinámica
    var installedApps by remember { mutableStateOf(loadInstalledApps(context.packageManager)) }
    
    // Escuchar cambios en paquetes instalados/desinstalados
    DisposableEffect(Unit) {
        val packageChangeReceiver = object : android.content.BroadcastReceiver() {
            override fun onReceive(ctx: android.content.Context?, intent: android.content.Intent?) {
                installedApps = loadInstalledApps(context.packageManager)
            }
        }
        
        val filter = android.content.IntentFilter().apply {
            addAction(android.content.Intent.ACTION_PACKAGE_ADDED)
            addAction(android.content.Intent.ACTION_PACKAGE_REMOVED)
            addAction(android.content.Intent.ACTION_PACKAGE_REPLACED)
            addAction(android.content.Intent.ACTION_PACKAGE_CHANGED)
            addDataScheme("package")
        }
        
        context.registerReceiver(packageChangeReceiver, filter)
        
        onDispose {
            context.unregisterReceiver(packageChangeReceiver)
        }
    }
    
    // Mapear favoritos a FavoriteApp objects
    val favoriteApps = remember(favoritePackages, installedApps) {
        if (favoritePackages.isEmpty()) {
            // Si no hay favoritos guardados, usar los primeros instalados como default
            installedApps.take(6).map { FavoriteApp(it.name, it.packageName, 0) }
        } else {
            // Mapear package names guardados a apps instaladas
            favoritePackages.mapNotNull { packageName ->
                installedApps.find { it.packageName == packageName }?.let {
                    FavoriteApp(it.name, it.packageName, it.notificationCount)
                }
            }
        }
    }
    
    // Estado para menú contextual
    var showContextMenu by remember { mutableStateOf(false) }
    var selectedApp by remember { mutableStateOf<FavoriteApp?>(null) }
    
    // Fondo con imagen o color sólido usando componente unificado
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
        Box(
            modifier = Modifier
                .fillMaxSize()
                .systemBarsPadding()
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(vertical = 24.dp),  // Reducido de 32dp
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // ═══════════════════════════════════════════════════════════════
                // CLOCK SECTION (Title area)
                // ═══════════════════════════════════════════════════════════════
                Spacer(modifier = Modifier.height(32.dp))  // Reducido de 48dp
                
                ScientificClock(
                    colors = colors,
                    locale = locale,
                    showSeconds = showSeconds
                )
                
                Spacer(modifier = Modifier.height(24.dp))  // Reducido de 48dp
                
                // Separator using LaTeX symbol
                Text(
                    text = "↫ ⋇ ↬",
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.textSecondary.copy(alpha = 0.5f),
                    letterSpacing = 8.sp
                )
                
                Spacer(modifier = Modifier.height(20.dp))  // Reducido de 32dp
                
                // ═══════════════════════════════════════════════════════════════
                // FAVORITE APPS with Haptic Feedback Scaling
                // Al deslizar el dedo, los elementos se escalan y vibran
                // ═══════════════════════════════════════════════════════════════
                HapticFavoritesList(
                    favoriteApps = favoriteApps,
                    maxFavorites = maxFavorites,
                    colors = colors,
                    hapticScale = hapticScale,
                    hapticIntensity = hapticIntensity,
                    hapticSound = hapticSound,
                    onLaunchApp = onLaunchApp,
                    onLongClick = { app ->
                        selectedApp = app
                        showContextMenu = true
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                        .padding(horizontal = 32.dp)
                )
                
                // ═══════════════════════════════════════════════════════════════
                // BOTTOM HINT
                // ═══════════════════════════════════════════════════════════════
                Spacer(modifier = Modifier.height(16.dp))
                
                Text(
                    text = "↑ ${stringResource(R.string.home_swipe_drawer)}",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.textSecondary.copy(alpha = 0.5f),
                    modifier = Modifier
                        .clickable { onOpenAppDrawer() }
                        .padding(8.dp)
                )
                
                Spacer(modifier = Modifier.height(16.dp))
            }
            
            // ═══════════════════════════════════════════════════════════════
            // SETTINGS BUTTON (top right)
            // ═══════════════════════════════════════════════════════════════
            IconButton(
                onClick = onOpenSettings,
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(16.dp)
            ) {
                Text(
                    text = "⊚", // LaTeX circledcirc symbol
                    style = MaterialTheme.typography.titleLarge,
                    color = colors.textSecondary
                )
            }
            
            // ═══════════════════════════════════════════════════════════════
            // CONTEXT MENU - Quitar de favoritos
            // ═══════════════════════════════════════════════════════════════
            selectedApp?.let { app ->
                RemoveFromFavoritesMenu(
                    visible = showContextMenu,
                    appName = app.name,
                    colors = colors,
                    onRemoveFromFavorites = {
                        coroutineScope.launch {
                            val removed = favoritesRepository.removeFavorite(app.packageName)
                            if (removed) {
                                Toast.makeText(
                                    context,
                                    context.getString(R.string.favorites_removed),
                                    Toast.LENGTH_SHORT
                                ).show()
                            }
                        }
                    },
                    onAppInfo = {
                        // Abrir configuración de la app en Android
                        try {
                            val intent = android.content.Intent(
                                android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                android.net.Uri.parse("package:${app.packageName}")
                            )
                            intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                            context.startActivity(intent)
                        } catch (e: Exception) {
                            Toast.makeText(context, "No se pudo abrir configuración", Toast.LENGTH_SHORT).show()
                        }
                        showContextMenu = false
                        selectedApp = null
                    },
                    onDismiss = {
                        showContextMenu = false
                        selectedApp = null
                    }
                )
            }
        }
    }
}

/**
 * Data class for favorite apps
 */
data class FavoriteApp(
    val name: String,
    val packageName: String,
    val notificationCount: Int = 0
)

/**
 * Lista de favoritos con Haptic Feedback Scaling
 * 
 * Al deslizar el dedo verticalmente:
 * - El elemento más cercano se escala según hapticScale
 * - Vibración según hapticIntensity al cambiar de elemento
 * - Sonido según hapticSound al cambiar de elemento
 * - Al soltar se lanza la app seleccionada
 */
@Composable
fun HapticFavoritesList(
    favoriteApps: List<FavoriteApp>,
    maxFavorites: Int,
    colors: NevenColors,
    hapticScale: HapticScale = HapticScale.LARGE,
    hapticIntensity: HapticIntensity = HapticIntensity.MEDIUM,
    hapticSound: HapticSound = HapticSound.NONE,
    onLaunchApp: (String) -> Unit,
    onLongClick: (FavoriteApp) -> Unit,
    modifier: Modifier = Modifier
) {
    val view = LocalView.current
    
    // Estado para tracking del dedo
    var isDragging by remember { mutableStateOf(false) }
    var dragY by remember { mutableStateOf(0f) }
    var highlightedIndex by remember { mutableStateOf(-1) }
    var lastHighlightedIndex by remember { mutableStateOf(-1) }
    
    // Posiciones de cada elemento RELATIVAS al contenedor
    val itemPositions = remember { mutableStateMapOf<Int, Float>() }
    val itemHeights = remember { mutableStateMapOf<Int, Float>() }
    
    // Posición del contenedor en la pantalla
    var containerY by remember { mutableStateOf(0f) }
    
    // ToneGenerator para sonidos (más confiable que AudioManager.playSoundEffect)
    val toneGenerator = remember {
        try {
            android.media.ToneGenerator(android.media.AudioManager.STREAM_SYSTEM, 50)
        } catch (e: Exception) {
            null
        }
    }
    
    // Limpiar ToneGenerator al desmontar
    DisposableEffect(Unit) {
        onDispose {
            toneGenerator?.release()
        }
    }
    
    // Función para reproducir sonido
    fun playHapticSound() {
        if (hapticSound == HapticSound.NONE) return
        
        try {
            val toneType = when (hapticSound) {
                HapticSound.CLICK -> android.media.ToneGenerator.TONE_PROP_BEEP
                HapticSound.TICK -> android.media.ToneGenerator.TONE_CDMA_PIP
                HapticSound.POP -> android.media.ToneGenerator.TONE_PROP_ACK
                HapticSound.NONE -> return
            }
            toneGenerator?.startTone(toneType, 50)  // 50ms de duración
        } catch (e: Exception) {
            // Ignorar errores de audio
        }
    }
    
    // Función para vibrar según intensidad
    fun performHaptic(isConfirm: Boolean = false) {
        if (hapticIntensity == HapticIntensity.NONE) return
        
        val feedbackConstant = when {
            isConfirm -> HapticFeedbackConstants.CONFIRM
            hapticIntensity == HapticIntensity.LIGHT -> HapticFeedbackConstants.CLOCK_TICK
            hapticIntensity == HapticIntensity.MEDIUM -> HapticFeedbackConstants.KEYBOARD_TAP
            hapticIntensity == HapticIntensity.STRONG -> HapticFeedbackConstants.LONG_PRESS
            else -> HapticFeedbackConstants.CLOCK_TICK
        }
        view.performHapticFeedback(feedbackConstant)
    }
    
    // Calcular qué elemento está bajo el dedo
    LaunchedEffect(dragY, isDragging) {
        if (isDragging && itemPositions.isNotEmpty()) {
            var closestIndex = -1
            var closestDistance = Float.MAX_VALUE
            
            itemPositions.forEach { (index, position) ->
                val itemHeight = itemHeights[index] ?: 48f
                val itemCenter = position + itemHeight / 2
                val distance = abs(dragY - itemCenter)
                
                // Seleccionar si el dedo está dentro del área del item
                if (distance < itemHeight * 0.7f && distance < closestDistance) {
                    closestDistance = distance
                    closestIndex = index
                }
            }
            
            if (closestIndex != highlightedIndex) {
                highlightedIndex = closestIndex
                
                // Haptic feedback y sonido al cambiar de elemento
                if (closestIndex >= 0 && lastHighlightedIndex != closestIndex) {
                    performHaptic()
                    playHapticSound()
                    lastHighlightedIndex = closestIndex
                }
            }
        }
    }
    
    Column(
        modifier = modifier
            .onGloballyPositioned { coordinates ->
                containerY = coordinates.positionInRoot().y
            }
            .pointerInput(favoriteApps) {
                detectVerticalDragGestures(
                    onDragStart = { offset ->
                        isDragging = true
                        dragY = offset.y
                        lastHighlightedIndex = -1
                    },
                    onDragEnd = {
                        // Lanzar app si hay una seleccionada
                        if (highlightedIndex >= 0 && highlightedIndex < favoriteApps.size) {
                            performHaptic(isConfirm = true)
                            onLaunchApp(favoriteApps[highlightedIndex].packageName)
                        }
                        isDragging = false
                        highlightedIndex = -1
                    },
                    onDragCancel = {
                        isDragging = false
                        highlightedIndex = -1
                    },
                    onVerticalDrag = { change, _ ->
                        change.consume()
                        dragY = change.position.y
                    }
                )
            },
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        favoriteApps.forEachIndexed { index, app ->
            HapticFavoriteAppItem(
                app = app,
                colors = colors,
                isHighlighted = highlightedIndex == index,
                isDragging = isDragging,
                distanceFromCenter = if (isDragging && highlightedIndex >= 0) {
                    abs(index - highlightedIndex)
                } else 0,
                highlightScale = hapticScale.scale,
                onClick = { onLaunchApp(app.packageName) },
                onLongClick = { onLongClick(app) },
                onPositioned = { positionInParent, height ->
                    // Guardar posición RELATIVA al contenedor Column
                    itemPositions[index] = positionInParent
                    itemHeights[index] = height
                }
            )
        }
        
        // Hint si hay espacio para más favoritos
        if (favoriteApps.size < maxFavorites) {
            Text(
                text = "§ ${stringResource(R.string.home_add_favorite)}",
                style = MaterialTheme.typography.labelSmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary.copy(alpha = 0.4f),
                modifier = Modifier.padding(vertical = 4.dp)
            )
        }
    }
}

/**
 * Item de favorito con soporte para Haptic Feedback Scaling
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun HapticFavoriteAppItem(
    app: FavoriteApp,
    colors: NevenColors,
    isHighlighted: Boolean,
    isDragging: Boolean,
    distanceFromCenter: Int,
    highlightScale: Float = 1.35f,
    onClick: () -> Unit,
    onLongClick: () -> Unit,
    onPositioned: (Float, Float) -> Unit
) {
    // Escala animada basada en si está resaltado
    val targetScale = when {
        isHighlighted -> highlightScale
        isDragging && distanceFromCenter == 1 -> 1f + (highlightScale - 1f) * 0.3f
        isDragging && distanceFromCenter >= 2 -> 0.9f
        else -> 1f
    }
    
    val scale by animateFloatAsState(
        targetValue = targetScale,
        animationSpec = spring(
            dampingRatio = 0.7f,
            stiffness = 400f
        ),
        label = "scale"
    )
    
    // Color del texto basado en si está resaltado
    val textColor = if (isHighlighted) colors.accent else colors.textPrimary
    val indicatorColor = if (isHighlighted) colors.accent else colors.accent.copy(alpha = 0.6f)
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                // Escalar desde la izquierda para que crezca hacia la derecha
                transformOrigin = TransformOrigin(0f, 0.5f)
            }
            .onGloballyPositioned { coordinates ->
                // Usar positionInParent para coordenadas relativas al Column contenedor
                val posInParent = coordinates.positionInParent()
                onPositioned(
                    posInParent.y,
                    coordinates.size.height.toFloat()
                )
            }
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick
            )
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // App indicator
        Text(
            text = if (isHighlighted) "▶" else "▸",
            fontSize = if (isHighlighted) 18.sp else 14.sp,
            fontWeight = if (isHighlighted) FontWeight.Bold else FontWeight.Normal,
            color = indicatorColor
        )
        
        Spacer(modifier = Modifier.width(8.dp))
        
        // App name
        Text(
            text = buildAnnotatedString {
                withStyle(SpanStyle(color = textColor)) {
                    append(app.name)
                }
                
                // Notification badge
                if (app.notificationCount > 0) {
                    withStyle(
                        SpanStyle(
                            color = colors.accent,
                            fontSize = 10.sp,
                            baselineShift = BaselineShift.Superscript
                        )
                    ) {
                        append(" (${app.notificationCount})")
                    }
                }
            },
            fontSize = if (isHighlighted) 18.sp else 15.sp,
            fontWeight = if (isHighlighted) FontWeight.SemiBold else FontWeight.Normal,
            fontFamily = NevenFontFamily
        )
    }
}

/**
 * Single favorite app item (versión simple para compatibilidad)
 * Supports long-click for context menu
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun FavoriteAppItem(
    app: FavoriteApp,
    colors: NevenColors,
    onClick: () -> Unit,
    onLongClick: () -> Unit = {}
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick
            )
            .padding(vertical = 8.dp),  // Restaurado de 6dp a 8dp
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = "▸",
            fontSize = 14.sp,
            color = colors.accent
        )
        
        Spacer(modifier = Modifier.width(8.dp))
        
        Text(
            text = buildAnnotatedString {
                withStyle(SpanStyle(color = colors.textPrimary)) {
                    append(app.name)
                }
                
                if (app.notificationCount > 0) {
                    withStyle(
                        SpanStyle(
                            color = colors.accent,
                            fontSize = 10.sp,
                            baselineShift = BaselineShift.Superscript
                        )
                    ) {
                        append(" (${app.notificationCount})")
                    }
                }
            },
            fontSize = 15.sp,
            fontFamily = NevenFontFamily
        )
    }
}

/**
 * Converts number to superscript Unicode
 */
private fun toSuperscriptNumber(n: Int): String {
    val digits = mapOf(
        '0' to '⁰', '1' to '¹', '2' to '²', '3' to '³', '4' to '⁴',
        '5' to '⁵', '6' to '⁶', '7' to '⁷', '8' to '⁸', '9' to '⁹'
    )
    return n.toString().map { digits[it] ?: it }.joinToString("")
}
