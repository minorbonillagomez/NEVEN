package com.neven.launcher.ui.drawer

import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.graphics.drawable.Drawable
import android.media.AudioManager
import android.widget.Toast
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.layout.positionInParent
import androidx.compose.ui.zIndex
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.material3.ripple
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.R
import com.neven.launcher.data.BackgroundPosition
import com.neven.launcher.data.BackgroundType
import com.neven.launcher.data.FavoritesRepository
import com.neven.launcher.data.HapticIntensity
import com.neven.launcher.data.HapticScale
import com.neven.launcher.data.HapticSound
import com.neven.launcher.ui.components.AddToFavoritesMenu
import com.neven.launcher.ui.components.NevenBackground
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.getNevenColors
import com.neven.launcher.ui.theme.NevenPalette
import kotlinx.coroutines.launch

/**
 * NEVEN App Drawer
 * 
 * Vertical list of all apps (Niagara style)
 * with lateral alphabet for quick navigation.
 * 
 * Long-press en app → menú contextual con "Agregar a favoritos"
 * Usa el mismo fondo personalizado que Home para armonía visual.
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun AppDrawerScreen(
    colors: NevenColors,
    backgroundType: BackgroundType = BackgroundType.SOLID,
    backgroundImageUri: String? = null,
    backgroundPosition: BackgroundPosition = BackgroundPosition.CROP,
    backgroundOpacity: Float = 0.4f,
    backgroundTintEnabled: Boolean = false,
    // Parámetros de retroalimentación táctil
    hapticScale: HapticScale = HapticScale.LARGE,
    hapticIntensity: HapticIntensity = HapticIntensity.MEDIUM,
    hapticSound: HapticSound = HapticSound.CLICK,
    onAppClick: (AppInfo) -> Unit,
    onAppLongClick: (AppInfo) -> Unit,
    onClose: () -> Unit
) {
    val context = LocalContext.current
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()
    
    // Repositorio de favoritos
    val favoritesRepository = remember { FavoritesRepository.getInstance(context) }
    
    // Observar favoritos para saber cuáles ya están
    val favoritePackages by favoritesRepository.favoritesFlow.collectAsState(initial = emptySet())
    val maxFavorites by favoritesRepository.maxFavoritesFlow.collectAsState(initial = 8)
    
    // Load installed apps - con actualización dinámica
    var apps by remember { mutableStateOf(loadInstalledApps(context.packageManager)) }
    
    // Escuchar cambios en paquetes instalados/desinstalados
    DisposableEffect(Unit) {
        val packageChangeReceiver = object : android.content.BroadcastReceiver() {
            override fun onReceive(ctx: android.content.Context?, intent: android.content.Intent?) {
                // Recargar apps cuando hay cambios en paquetes
                apps = loadInstalledApps(context.packageManager)
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
    
    // Group apps by first letter
    val groupedApps = remember(apps) {
        apps.groupBy { it.name.first().uppercaseChar() }
            .toSortedMap()
    }
    
    // Alphabet for lateral navigation
    val alphabet = remember(groupedApps) {
        groupedApps.keys.toList()
    }
    
    // Track which letter is being touched
    var selectedLetter by remember { mutableStateOf<Char?>(null) }
    
    // Estado para menú contextual
    var showContextMenu by remember { mutableStateOf(false) }
    var selectedApp by remember { mutableStateOf<AppInfo?>(null) }
    
    // Fondo unificado con configuración del usuario (armonía visual con Home)
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
            // ═══════════════════════════════════════════════════════════════
            // BOTÓN DE RETORNO (parte superior izquierda)
            // Usamos zIndex alto y clickable con ripple explícito para garantizar
            // que el botón responda correctamente al toque
            // ═══════════════════════════════════════════════════════════════
            Box(
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .zIndex(10f)  // Asegurar que esté encima de otros elementos
                    .padding(start = 16.dp, top = 8.dp)
                    .size(56.dp)  // Área táctil grande para fácil interacción
                    .clip(CircleShape)  // Para mejor feedback visual del ripple
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = ripple(bounded = true),
                        onClick = { onClose() }
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "<",
                    style = MaterialTheme.typography.headlineLarge,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.accent
                )
            }
            
            Row(modifier = Modifier.fillMaxSize()) {
                // ═══════════════════════════════════════════════════════════════
                // MAIN APP LIST (Vertical, like Niagara)
                // ═══════════════════════════════════════════════════════════════
                LazyColumn(
                    state = listState,
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .padding(start = 24.dp, end = 8.dp),
                    contentPadding = PaddingValues(vertical = 48.dp)
                ) {
                    groupedApps.forEach { (letter, appsInGroup) ->
                        // Section header with letter
                        item(key = "header_$letter") {
                            SectionHeader(
                                letter = letter,
                                colors = colors
                            )
                        }
                        
                        // Apps in this section
                        items(
                            items = appsInGroup,
                            key = { it.packageName }
                        ) { app ->
                            val isFavorite = favoritePackages.contains(app.packageName)
                            
                            AppListItem(
                                app = app,
                                isFavorite = isFavorite,
                                colors = colors,
                                onClick = { onAppClick(app) },
                                onLongClick = {
                                    selectedApp = app
                                    showContextMenu = true
                                }
                            )
                        }
                    }
                }
                
                // ═══════════════════════════════════════════════════════════════
                // LATERAL ALPHABET (Right side) - Con Haptic Feedback Scaling
                // ═══════════════════════════════════════════════════════════════
                HapticAlphabetSidebar(
                    alphabet = alphabet,
                    selectedLetter = selectedLetter,
                    colors = colors,
                    hapticScale = hapticScale,
                    hapticIntensity = hapticIntensity,
                    hapticSound = hapticSound,
                    onLetterSelected = { letter ->
                        selectedLetter = letter
                        // Find index of first app starting with this letter
                        val flatList = groupedApps.flatMap { (l, apps) ->
                            listOf("header_$l") + apps.map { it.packageName }
                        }
                        val headerIndex = flatList.indexOf("header_$letter")
                        if (headerIndex >= 0) {
                            coroutineScope.launch {
                                listState.animateScrollToItem(headerIndex)
                            }
                        }
                    },
                    onSelectionEnd = {
                        selectedLetter = null
                    }
                )
            }
            
            // ═══════════════════════════════════════════════════════════════
            // LETTER POPUP (when scrolling alphabet)
            // ═══════════════════════════════════════════════════════════════
            if (selectedLetter != null) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = selectedLetter.toString(),
                        style = MaterialTheme.typography.displayLarge,
                        color = colors.accent.copy(alpha = 0.8f),
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
            
            // ═══════════════════════════════════════════════════════════════
            // SWIPE DOWN HINT (top)
            // ═══════════════════════════════════════════════════════════════
            Text(
                text = "↓",
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .padding(top = 16.dp)
                    .alpha(0.3f),
                style = MaterialTheme.typography.titleLarge,
                color = colors.textSecondary
            )
            
            // ═══════════════════════════════════════════════════════════════
            // CONTEXT MENU - Agregar a favoritos
            // ═══════════════════════════════════════════════════════════════
            selectedApp?.let { app ->
                AddToFavoritesMenu(
                    visible = showContextMenu,
                    appName = app.name,
                    colors = colors,
                    onAddToFavorites = {
                        coroutineScope.launch {
                            val added = favoritesRepository.addFavorite(app.packageName)
                            val message = if (added) {
                                context.getString(R.string.favorites_added)
                            } else {
                                // Ya está en favoritos o se alcanzó el máximo
                                if (favoritePackages.contains(app.packageName)) {
                                    "Ya está en favoritos"
                                } else {
                                    context.getString(R.string.favorites_full)
                                }
                            }
                            Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
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
 * Section header showing the letter
 */
@Composable
fun SectionHeader(
    letter: Char,
    colors: NevenColors
) {
    Text(
        text = letter.toString(),
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 16.dp, horizontal = 8.dp),
        style = MaterialTheme.typography.headlineMedium,
        fontFamily = NevenFontFamily,
        fontWeight = FontWeight.Bold,
        color = colors.accent
    )
}

/**
 * Single app item in the list
 * Supports long-click for context menu
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun AppListItem(
    app: AppInfo,
    isFavorite: Boolean = false,
    colors: NevenColors,
    onClick: () -> Unit,
    onLongClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick
            )
            .padding(vertical = 12.dp, horizontal = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // App indicator (favorito = estrella, normal = bullet)
        Text(
            text = if (isFavorite) "★" else "▸",
            style = MaterialTheme.typography.bodyLarge,
            color = if (isFavorite) colors.accent else colors.textSecondary.copy(alpha = 0.5f)
        )
        
        Spacer(modifier = Modifier.width(16.dp))
        
        // App name
        Text(
            text = app.name,
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            color = colors.textPrimary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
        
        // Notification badge (if any)
        if (app.notificationCount > 0) {
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "⁽${app.notificationCount}⁾",
                fontSize = 12.sp,
                color = colors.accent
            )
        }
    }
}

/**
 * Lateral alphabet for quick navigation
 */
@Composable
fun AlphabetSidebar(
    alphabet: List<Char>,
    selectedLetter: Char?,
    colors: NevenColors,
    onLetterSelected: (Char) -> Unit,
    onSelectionEnd: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxHeight()
            .width(32.dp)
            .padding(vertical = 48.dp)
            .pointerInput(alphabet) {
                detectVerticalDragGestures(
                    onDragEnd = { onSelectionEnd() },
                    onDragCancel = { onSelectionEnd() }
                ) { change, _ ->
                    val y = change.position.y
                    val itemHeight = size.height.toFloat() / alphabet.size
                    val index = (y / itemHeight).toInt().coerceIn(0, alphabet.size - 1)
                    onLetterSelected(alphabet[index])
                }
            },
        verticalArrangement = Arrangement.SpaceEvenly,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        alphabet.forEach { letter ->
            Text(
                text = letter.toString(),
                modifier = Modifier
                    .clickable { onLetterSelected(letter) }
                    .padding(2.dp),
                fontSize = 11.sp,
                fontFamily = NevenFontFamily,
                fontWeight = if (letter == selectedLetter) FontWeight.Bold else FontWeight.Normal,
                color = if (letter == selectedLetter) colors.accent else colors.textSecondary
            )
        }
    }
}

/**
 * Lateral alphabet with Haptic Feedback Scaling
 * 
 * When user drags finger over the alphabet, the selected letter scales up
 * with haptic feedback (vibration) and optional sound effect.
 * Nearby letters also scale slightly for a "fish-eye" effect.
 */
@Composable
fun HapticAlphabetSidebar(
    alphabet: List<Char>,
    selectedLetter: Char?,
    colors: NevenColors,
    hapticScale: HapticScale = HapticScale.LARGE,
    hapticIntensity: HapticIntensity = HapticIntensity.MEDIUM,
    hapticSound: HapticSound = HapticSound.CLICK,
    onLetterSelected: (Char) -> Unit,
    onSelectionEnd: () -> Unit
) {
    val view = LocalView.current
    
    // Estado para tracking del dedo
    var isDragging by remember { mutableStateOf(false) }
    var dragY by remember { mutableStateOf(0f) }
    var highlightedIndex by remember { mutableStateOf(-1) }
    var lastHighlightedIndex by remember { mutableStateOf(-1) }
    
    // Posiciones de cada letra RELATIVAS al contenedor
    val letterPositions = remember { mutableStateMapOf<Int, Float>() }
    val letterHeights = remember { mutableStateMapOf<Int, Float>() }
    
    // ToneGenerator para sonidos (más confiable que AudioManager.playSoundEffect)
    val toneGenerator = remember {
        try {
            android.media.ToneGenerator(AudioManager.STREAM_SYSTEM, 50)
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
    fun playSelectionSound() {
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
    fun performHaptic() {
        if (hapticIntensity == HapticIntensity.NONE) return
        
        val feedbackConstant = when (hapticIntensity) {
            HapticIntensity.LIGHT -> android.view.HapticFeedbackConstants.CLOCK_TICK
            HapticIntensity.MEDIUM -> android.view.HapticFeedbackConstants.KEYBOARD_TAP
            HapticIntensity.STRONG -> android.view.HapticFeedbackConstants.LONG_PRESS
            HapticIntensity.NONE -> return
        }
        view.performHapticFeedback(feedbackConstant)
    }
    
    // Calcular qué letra está bajo el dedo
    LaunchedEffect(dragY, isDragging) {
        if (isDragging && letterPositions.isNotEmpty()) {
            var closestIndex = -1
            var closestDistance = Float.MAX_VALUE
            
            letterPositions.forEach { (index, position) ->
                val letterHeight = letterHeights[index] ?: 20f
                val letterCenter = position + letterHeight / 2
                val distance = kotlin.math.abs(dragY - letterCenter)
                
                // Seleccionar si el dedo está dentro del área de la letra
                if (distance < letterHeight && distance < closestDistance) {
                    closestDistance = distance
                    closestIndex = index
                }
            }
            
            if (closestIndex != highlightedIndex && closestIndex >= 0) {
                highlightedIndex = closestIndex
                onLetterSelected(alphabet[closestIndex])
                
                // Haptic feedback y sonido al cambiar de letra
                if (lastHighlightedIndex != closestIndex) {
                    performHaptic()
                    playSelectionSound()
                    lastHighlightedIndex = closestIndex
                }
            }
        }
    }
    
    Column(
        modifier = Modifier
            .fillMaxHeight()
            .width(56.dp)  // Ancho para touch target
            .padding(vertical = 48.dp)
            .pointerInput(alphabet, hapticScale, hapticIntensity, hapticSound) {
                detectVerticalDragGestures(
                    onDragStart = { offset ->
                        isDragging = true
                        dragY = offset.y
                        lastHighlightedIndex = -1
                    },
                    onDragEnd = {
                        isDragging = false
                        highlightedIndex = -1
                        lastHighlightedIndex = -1
                        onSelectionEnd()
                    },
                    onDragCancel = {
                        isDragging = false
                        highlightedIndex = -1
                        lastHighlightedIndex = -1
                        onSelectionEnd()
                    },
                    onVerticalDrag = { change, _ ->
                        change.consume()
                        dragY = change.position.y
                    }
                )
            },
        verticalArrangement = Arrangement.SpaceEvenly,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        alphabet.forEachIndexed { index, letter ->
            HapticLetterItem(
                letter = letter,
                colors = colors,
                isHighlighted = highlightedIndex == index,
                isDragging = isDragging,
                distanceFromCenter = if (isDragging && highlightedIndex >= 0) {
                    kotlin.math.abs(index - highlightedIndex)
                } else 0,
                highlightScale = hapticScale.scale,
                onClick = {
                    onLetterSelected(letter)
                    performHaptic()
                    playSelectionSound()
                },
                onPositioned = { positionInParent, height ->
                    letterPositions[index] = positionInParent
                    letterHeights[index] = height
                }
            )
        }
    }
}

/**
 * Item de letra con soporte para Haptic Feedback Scaling
 */
@Composable
private fun ColumnScope.HapticLetterItem(
    letter: Char,
    colors: NevenColors,
    isHighlighted: Boolean,
    isDragging: Boolean,
    distanceFromCenter: Int,
    highlightScale: Float = 1.35f,
    onClick: () -> Unit,
    onPositioned: (Float, Float) -> Unit
) {
    // Escala animada basada en si está resaltado y la distancia
    val targetScale = when {
        isHighlighted -> highlightScale
        isDragging && distanceFromCenter == 1 -> 1f + (highlightScale - 1f) * 0.5f  // Vecinos inmediatos
        isDragging && distanceFromCenter == 2 -> 1f + (highlightScale - 1f) * 0.2f  // Segundos vecinos
        isDragging && distanceFromCenter >= 3 -> 0.85f  // Letras lejanas se encogen
        else -> 1f
    }
    
    val scale by animateFloatAsState(
        targetValue = targetScale,
        animationSpec = spring(
            dampingRatio = 0.7f,
            stiffness = 400f
        ),
        label = "letterScale"
    )
    
    // Color del texto basado en si está resaltado
    val textColor by animateColorAsState(
        targetValue = when {
            isHighlighted -> colors.accent
            isDragging && distanceFromCenter <= 2 -> colors.textPrimary
            isDragging -> colors.textSecondary.copy(alpha = 0.5f)
            else -> colors.textSecondary
        },
        animationSpec = tween(100),
        label = "letterColor"
    )
    
    // Tamaño de fuente animado
    val fontSize by animateFloatAsState(
        targetValue = when {
            isHighlighted -> 18f
            isDragging && distanceFromCenter == 1 -> 14f
            isDragging && distanceFromCenter == 2 -> 12f
            else -> 11f
        },
        animationSpec = spring(dampingRatio = 0.7f, stiffness = 400f),
        label = "letterFontSize"
    )
    
    Box(
        modifier = Modifier
            .weight(1f)
            .fillMaxWidth()
            .onGloballyPositioned { coordinates ->
                onPositioned(
                    coordinates.positionInParent().y,
                    coordinates.size.height.toFloat()
                )
            }
            .clickable { onClick() },
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = letter.toString(),
            modifier = Modifier
                .graphicsLayer {
                    scaleX = scale
                    scaleY = scale
                    // Escalar desde la derecha para que crezca hacia la izquierda
                    transformOrigin = TransformOrigin(1f, 0.5f)
                }
                .padding(2.dp),
            fontSize = fontSize.sp,
            fontFamily = NevenFontFamily,
            fontWeight = if (isHighlighted) FontWeight.Bold else FontWeight.Normal,
            color = textColor
        )
    }
}

/**
 * Data class for app information
 */
data class AppInfo(
    val name: String,
    val packageName: String,
    val notificationCount: Int = 0
)

/**
 * Load all installed apps that have a launcher intent
 */
fun loadInstalledApps(packageManager: PackageManager): List<AppInfo> {
    val mainIntent = android.content.Intent(android.content.Intent.ACTION_MAIN, null)
    mainIntent.addCategory(android.content.Intent.CATEGORY_LAUNCHER)
    
    return packageManager.queryIntentActivities(mainIntent, 0)
        .mapNotNull { resolveInfo ->
            try {
                AppInfo(
                    name = resolveInfo.loadLabel(packageManager).toString(),
                    packageName = resolveInfo.activityInfo.packageName
                )
            } catch (e: Exception) {
                null
            }
        }
        .distinctBy { it.packageName }
        .sortedBy { it.name.lowercase() }
}
