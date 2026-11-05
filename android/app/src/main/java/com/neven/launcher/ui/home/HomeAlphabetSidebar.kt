package com.neven.launcher.ui.home

import android.content.pm.PackageManager
import android.media.AudioManager
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.background
import androidx.compose.foundation.basicMarquee
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.layout.positionInParent
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.data.HapticIntensity
import com.neven.launcher.data.HapticScale
import com.neven.launcher.data.HapticSound
import com.neven.launcher.ui.drawer.AppInfo
import com.neven.launcher.ui.drawer.loadInstalledApps
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * Barra lateral alfabetica para HOME con popup de apps
 * 
 * Muestra todas las letras del alfabeto en el lado derecho.
 * Al deslizar o tocar una letra, aparece un panel con las apps
 * que empiezan con esa letra.
 * 
 * Incluye efectos hapticos (vibracion, sonido, escala) como
 * en el drawer de aplicaciones.
 */
@Composable
fun HomeAlphabetSidebar(
    colors: NevenColors,
    hapticScale: HapticScale = HapticScale.LARGE,
    hapticIntensity: HapticIntensity = HapticIntensity.MEDIUM,
    hapticSound: HapticSound = HapticSound.NONE,
    onLaunchApp: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val view = LocalView.current
    val packageManager = context.packageManager
    
    // Cargar todas las apps instaladas - con actualización dinámica
    var allApps by remember { mutableStateOf(loadInstalledApps(packageManager)) }
    
    // Escuchar cambios en paquetes instalados/desinstalados
    DisposableEffect(Unit) {
        val packageChangeReceiver = object : android.content.BroadcastReceiver() {
            override fun onReceive(ctx: android.content.Context?, intent: android.content.Intent?) {
                allApps = loadInstalledApps(packageManager)
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
    
    // Generar alfabeto basado en las apps disponibles
    val alphabet = remember(allApps) {
        allApps.map { it.name.first().uppercaseChar() }
            .distinct()
            .filter { it.isLetter() }
            .sorted()
    }
    
    // Estado de seleccion
    var selectedLetter by remember { mutableStateOf<Char?>(null) }
    var isDragging by remember { mutableStateOf(false) }
    var dragY by remember { mutableStateOf(0f) }
    var highlightedIndex by remember { mutableStateOf(-1) }
    var lastHighlightedIndex by remember { mutableStateOf(-1) }
    
    // Posiciones de cada letra
    val letterPositions = remember { mutableStateMapOf<Int, Float>() }
    val letterHeights = remember { mutableStateMapOf<Int, Float>() }
    
    // Apps filtradas por letra seleccionada
    val filteredApps = remember(selectedLetter, allApps) {
        if (selectedLetter != null) {
            allApps.filter { 
                it.name.first().uppercaseChar() == selectedLetter 
            }
        } else {
            emptyList()
        }
    }
    
    // ToneGenerator para sonidos
    val toneGenerator = remember {
        try {
            android.media.ToneGenerator(AudioManager.STREAM_SYSTEM, 50)
        } catch (e: Exception) {
            null
        }
    }
    
    DisposableEffect(Unit) {
        onDispose {
            toneGenerator?.release()
        }
    }
    
    // Funciones de feedback
    fun playSelectionSound() {
        if (hapticSound == HapticSound.NONE) return
        try {
            val toneType = when (hapticSound) {
                HapticSound.CLICK -> android.media.ToneGenerator.TONE_PROP_BEEP
                HapticSound.TICK -> android.media.ToneGenerator.TONE_CDMA_PIP
                HapticSound.POP -> android.media.ToneGenerator.TONE_PROP_ACK
                HapticSound.NONE -> return
            }
            toneGenerator?.startTone(toneType, 50)
        } catch (e: Exception) { }
    }
    
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
    
    // Calcular letra bajo el dedo
    LaunchedEffect(dragY, isDragging) {
        if (isDragging && letterPositions.isNotEmpty()) {
            var closestIndex = -1
            var closestDistance = Float.MAX_VALUE
            
            letterPositions.forEach { (index, position) ->
                val letterHeight = letterHeights[index] ?: 20f
                val letterCenter = position + letterHeight / 2
                val distance = kotlin.math.abs(dragY - letterCenter)
                
                if (distance < letterHeight && distance < closestDistance) {
                    closestDistance = distance
                    closestIndex = index
                }
            }
            
            if (closestIndex != highlightedIndex && closestIndex >= 0 && closestIndex < alphabet.size) {
                highlightedIndex = closestIndex
                selectedLetter = alphabet[closestIndex]
                
                if (lastHighlightedIndex != closestIndex) {
                    performHaptic()
                    playSelectionSound()
                    lastHighlightedIndex = closestIndex
                }
            }
        }
    }
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .then(
                // Detectar toque fuera del panel para cerrarlo
                if (selectedLetter != null) {
                    Modifier.pointerInput(Unit) {
                        detectTapGestures {
                            // Cerrar el panel al tocar fuera
                            selectedLetter = null
                        }
                    }
                } else Modifier
            )
    ) {
        // Panel de apps (aparece cuando hay letra seleccionada)
        AnimatedVisibility(
            visible = selectedLetter != null && filteredApps.isNotEmpty(),
            enter = fadeIn(tween(150)) + slideInHorizontally(tween(150)) { it },
            exit = fadeOut(tween(150)) + slideOutHorizontally(tween(150)) { it },
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .padding(end = 48.dp) // Espacio para el alfabeto
                .widthIn(max = 220.dp)
        ) {
            AppListPanel(
                letter = selectedLetter,
                apps = filteredApps,
                colors = colors,
                hapticScale = hapticScale,
                hapticIntensity = hapticIntensity,
                hapticSound = hapticSound,
                onAppClick = { packageName ->
                    selectedLetter = null
                    onLaunchApp(packageName)
                },
                onDismiss = {
                    selectedLetter = null
                }
            )
        }
        
        // Alfabeto lateral derecho
        Column(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .fillMaxHeight()
                .width(40.dp)
                .padding(vertical = 60.dp, horizontal = 4.dp)
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
                            // Mantener selectedLetter para que el usuario pueda ver las apps
                        },
                        onDragCancel = {
                            isDragging = false
                            highlightedIndex = -1
                            lastHighlightedIndex = -1
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
                AlphabetLetterItem(
                    letter = letter,
                    colors = colors,
                    isHighlighted = highlightedIndex == index,
                    isSelected = selectedLetter == letter && !isDragging,
                    isDragging = isDragging,
                    distanceFromCenter = if (isDragging && highlightedIndex >= 0) {
                        kotlin.math.abs(index - highlightedIndex)
                    } else 0,
                    highlightScale = hapticScale.scale,
                    onClick = {
                        selectedLetter = if (selectedLetter == letter) null else letter
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
}

/**
 * Panel que muestra las apps de una letra como Wheel Picker giratorio
 */
@Composable
private fun AppListPanel(
    letter: Char?,
    apps: List<AppInfo>,
    colors: NevenColors,
    hapticScale: HapticScale,
    hapticIntensity: HapticIntensity,
    hapticSound: HapticSound,
    onAppClick: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val view = LocalView.current
    
    // Estado del wheel picker
    var selectedIndex by remember(apps) { mutableStateOf(0) }
    var dragOffset by remember { mutableStateOf(0f) }
    var lastSelectedIndex by remember { mutableStateOf(-1) }
    
    // ToneGenerator para sonidos
    val toneGenerator = remember {
        try {
            android.media.ToneGenerator(AudioManager.STREAM_SYSTEM, 50)
        } catch (e: Exception) {
            null
        }
    }
    
    DisposableEffect(Unit) {
        onDispose {
            toneGenerator?.release()
        }
    }
    
    fun playSelectionSound() {
        if (hapticSound == HapticSound.NONE) return
        try {
            val toneType = when (hapticSound) {
                HapticSound.CLICK -> android.media.ToneGenerator.TONE_PROP_BEEP
                HapticSound.TICK -> android.media.ToneGenerator.TONE_CDMA_PIP
                HapticSound.POP -> android.media.ToneGenerator.TONE_PROP_ACK
                HapticSound.NONE -> return
            }
            toneGenerator?.startTone(toneType, 50)
        } catch (e: Exception) { }
    }
    
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
    
    // Feedback cuando cambia la seleccion
    LaunchedEffect(selectedIndex) {
        if (lastSelectedIndex != selectedIndex && lastSelectedIndex >= 0) {
            performHaptic()
            playSelectionSound()
        }
        lastSelectedIndex = selectedIndex
    }
    
    Column(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(colors.background.copy(alpha = 0.45f)) // 45% transparencia
            .pointerInput(Unit) {
                // Consumir toques dentro del panel para no cerrarlo
                detectTapGestures { }
            }
            .padding(vertical = 8.dp, horizontal = 4.dp)
            .width(180.dp)
    ) {
        // Header con la letra
        if (letter != null) {
            Text(
                text = letter.toString(),
                style = MaterialTheme.typography.headlineSmall,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.accent,
                modifier = Modifier
                    .padding(horizontal = 12.dp, vertical = 4.dp)
                    .align(Alignment.CenterHorizontally)
            )
        }
        
        // Wheel Picker de apps
        Box(
            modifier = Modifier
                .height(200.dp)
                .fillMaxWidth()
                .pointerInput(apps) {
                    detectVerticalDragGestures(
                        onDragEnd = {
                            // Ajustar al item mas cercano
                            dragOffset = 0f
                        },
                        onVerticalDrag = { change, dragAmount ->
                            change.consume()
                            dragOffset += dragAmount
                            
                            // Calcular nuevo indice basado en el drag
                            val itemHeight = 50f
                            val indexChange = (dragOffset / itemHeight).toInt()
                            if (indexChange != 0) {
                                val newIndex = (selectedIndex - indexChange).coerceIn(0, apps.size - 1)
                                if (newIndex != selectedIndex) {
                                    selectedIndex = newIndex
                                }
                                dragOffset = dragOffset % itemHeight
                            }
                        }
                    )
                },
            contentAlignment = Alignment.Center
        ) {
            // Indicador de seleccion central - solo borde, sin fondo, centrado
            Box(
                modifier = Modifier
                    .align(Alignment.Center)
                    .width(160.dp)
                    .height(48.dp)
                    .border(
                        width = 1.5.dp,
                        color = colors.accent.copy(alpha = 0.6f),
                        shape = RoundedCornerShape(8.dp)
                    )
            )
            
            // Items del wheel - usar Box con posicionamiento manual
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                // Mostrar items visibles (2 arriba, centro, 2 abajo)
                val visibleRange = 2
                val itemHeight = 48.dp
                
                for (offset in -visibleRange..visibleRange) {
                    val itemIndex = selectedIndex + offset
                    if (itemIndex in apps.indices) {
                        Box(
                            modifier = Modifier
                                .offset(y = itemHeight * offset)
                                .height(itemHeight)
                                .fillMaxWidth(),
                            contentAlignment = Alignment.Center
                        ) {
                            WheelPickerItem(
                                app = apps[itemIndex],
                                colors = colors,
                                distanceFromCenter = kotlin.math.abs(offset),
                                hapticScale = hapticScale,
                                isCenter = offset == 0,
                                onClick = {
                                    if (offset == 0) {
                                        // Item central - abrir app
                                        performHaptic()
                                        playSelectionSound()
                                        onAppClick(apps[itemIndex].packageName)
                                    } else {
                                        // Seleccionar este item
                                        selectedIndex = itemIndex
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }
        
        // Hint
        Text(
            text = "^ desliza | toca para abrir v",
            style = MaterialTheme.typography.labelSmall,
            color = colors.textSecondary.copy(alpha = 0.5f),
            modifier = Modifier
                .padding(top = 4.dp)
                .align(Alignment.CenterHorizontally)
        )
    }
}

/**
 * Item del Wheel Picker con efecto 3D
 */
@Composable
private fun WheelPickerItem(
    app: AppInfo,
    colors: NevenColors,
    distanceFromCenter: Int,
    hapticScale: HapticScale,
    isCenter: Boolean,
    onClick: () -> Unit
) {
    // Escala basada en la distancia del centro - efecto más pronunciado
    val baseScale = hapticScale.scale.coerceAtLeast(1.4f) // Mínimo 1.4x para item central
    val scale = when (distanceFromCenter) {
        0 -> baseScale // Item central muy grande
        1 -> 0.75f     // Más pequeño
        else -> 0.55f  // Mucho más pequeño
    }
    
    // Opacidad basada en la distancia - más contraste
    val alpha = when (distanceFromCenter) {
        0 -> 1f
        1 -> 0.55f
        else -> 0.3f
    }
    
    // Rotacion 3D simulando perspectiva del wheel - más pronunciada
    val rotationX = when (distanceFromCenter) {
        0 -> 0f
        1 -> 35f  // Más rotación
        else -> 55f
    }
    
    val animatedScale by animateFloatAsState(
        targetValue = scale,
        animationSpec = spring(dampingRatio = 0.7f, stiffness = 300f),
        label = "wheelItemScale"
    )
    
    Box(
        modifier = Modifier
            .height(48.dp)
            .fillMaxWidth()
            .graphicsLayer {
                scaleX = animatedScale
                scaleY = animatedScale
                this.alpha = alpha
                this.rotationX = rotationX * (if (distanceFromCenter > 0) -1 else 1).toFloat()
                cameraDistance = 12f * density
            }
            .clickable(onClick = onClick)
            .padding(horizontal = 12.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = app.name,
            style = if (isCenter) MaterialTheme.typography.titleMedium else MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            fontWeight = if (isCenter) FontWeight.Bold else FontWeight.Normal,
            color = if (isCenter) colors.textPrimary else colors.textSecondary.copy(alpha = 0.7f),
            fontSize = if (isCenter) 18.sp else 13.sp,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            softWrap = false,
            textAlign = TextAlign.Center,
            modifier = Modifier
                .fillMaxWidth()
                .wrapContentHeight(Alignment.CenterVertically)
                .basicMarquee(
                    iterations = if (isCenter) Int.MAX_VALUE else 0,
                    initialDelayMillis = 1500,
                    velocity = 30.dp
                )
        )
    }
}

/**
 * Item de letra en el alfabeto lateral
 */
@Composable
private fun ColumnScope.AlphabetLetterItem(
    letter: Char,
    colors: NevenColors,
    isHighlighted: Boolean,
    isSelected: Boolean,
    isDragging: Boolean,
    distanceFromCenter: Int,
    highlightScale: Float = 1.35f,
    onClick: () -> Unit,
    onPositioned: (Float, Float) -> Unit
) {
    val targetScale = when {
        isHighlighted -> highlightScale
        isDragging && distanceFromCenter == 1 -> 1f + (highlightScale - 1f) * 0.5f
        isDragging && distanceFromCenter == 2 -> 1f + (highlightScale - 1f) * 0.2f
        isDragging && distanceFromCenter >= 3 -> 0.85f
        isSelected -> 1.2f
        else -> 1f
    }
    
    val scale by animateFloatAsState(
        targetValue = targetScale,
        animationSpec = spring(dampingRatio = 0.7f, stiffness = 400f),
        label = "letterScale"
    )
    
    val textColor = when {
        isHighlighted || isSelected -> colors.accent
        isDragging && distanceFromCenter <= 2 -> colors.textPrimary
        isDragging -> colors.textSecondary.copy(alpha = 0.5f)
        else -> colors.textSecondary
    }
    
    val fontSize = when {
        isHighlighted -> 16f
        isDragging && distanceFromCenter == 1 -> 13f
        isDragging && distanceFromCenter == 2 -> 11f
        isSelected -> 13f
        else -> 10f
    }
    
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
                    transformOrigin = TransformOrigin(1f, 0.5f)
                },
            fontSize = fontSize.sp,
            fontFamily = NevenFontFamily,
            fontWeight = if (isHighlighted || isSelected) FontWeight.Bold else FontWeight.Normal,
            color = textColor
        )
    }
}
