package com.neven.launcher.ui.home

import android.content.Context
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.PagerState
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import com.neven.launcher.data.*
import com.neven.launcher.ui.adventure.AdventureClockPage
import com.neven.launcher.ui.audiobook.AudiobookLauncherPage
import com.neven.launcher.ui.components.NevenBackground
import com.neven.launcher.ui.glance.GlancePage
import com.neven.launcher.ui.notes.StickyNotesLayer
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.rememberNevenColors
import kotlinx.coroutines.launch
import kotlin.math.absoluteValue

/**
 * NEVEN Launcher Pager
 * 
 * Sistema de múltiples pantallas horizontales con:
 * - Páginas dinámicas configurables por el usuario
 * - Página HOME siempre en el centro como punto de referencia
 * - Indicadores de página en la parte inferior
 * - Soporte para widgets en cada página
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun LauncherPager(
    palette: NevenPalette,
    isDarkMode: Boolean,
    onOpenSettings: () -> Unit,
    onOpenAppDrawer: () -> Unit,
    onLaunchApp: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val colors = rememberNevenColors(palette, isDarkMode)
    val coroutineScope = rememberCoroutineScope()
    
    // Repositorios
    val pagesRepository = remember { PagesRepository.getInstance(context) }
    val settingsRepository = remember { SettingsRepository.getInstance(context) }
    val notesRepository = remember { StickyNoteRepository.getInstance(context) }
    
    // Observar páginas
    val pages by pagesRepository.pagesFlow.collectAsState(initial = DefaultPages.getDefaultPages())
    val homeIndex by pagesRepository.homeIndexFlow.collectAsState(initial = 0)
    
    // Observar configuración de notas (kill switch)
    val notesEnabled by notesRepository.notesEnabledFlow.collectAsState(initial = true)
    
    // Observar configuración de fondo de pantalla
    val backgroundType by settingsRepository.backgroundTypeFlow.collectAsState(initial = BackgroundType.SOLID)
    val backgroundImageUri by settingsRepository.backgroundImageUriFlow.collectAsState(initial = null)
    val backgroundPosition by settingsRepository.backgroundPositionFlow.collectAsState(initial = BackgroundPosition.CROP)
    val backgroundOpacity by settingsRepository.backgroundOpacityFlow.collectAsState(initial = 0.4f)
    val backgroundTintEnabled by settingsRepository.backgroundTintEnabledFlow.collectAsState(initial = false)
    
    // Estado del pager
    val pagerState = rememberPagerState(
        initialPage = homeIndex,
        pageCount = { pages.size }
    )
    
    // Navegar a HOME cuando cambia el índice
    LaunchedEffect(homeIndex) {
        if (homeIndex >= 0 && homeIndex < pages.size) {
            pagerState.scrollToPage(homeIndex)
        }
    }
    
    // Fondo unificado para todas las páginas
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
        Box(modifier = modifier.fillMaxSize()) {
            // Pager horizontal con efecto Page Curl 3D
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.fillMaxSize(),
                beyondViewportPageCount = 0 // No pre-renderizar páginas adyacentes para evitar conflictos de interacción
            ) { pageIndex ->
                val page = pages.getOrNull(pageIndex)
                
                // Calcular el offset de la página actual respecto al centro
                // pageOffset: negativo = página yendo a la izquierda, positivo = viniendo de la derecha
                val pageOffset = ((pagerState.currentPage - pageIndex) + pagerState.currentPageOffsetFraction)
                    .coerceIn(-1f, 1f)
                
                // Envolver cada página con transformación Page Curl y capa de notas
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .graphicsLayer {
                            val maxRotation = 60f // Grados máximos de rotación
                            
                            // Perspectiva de cámara para efecto 3D realista
                            cameraDistance = 12f * density
                            
                            // Rotación sobre eje Y (efecto de pasar página)
                            rotationY = -pageOffset * maxRotation
                            
                            // Pivote dinámico según dirección
                            transformOrigin = when {
                                pageOffset < 0 -> androidx.compose.ui.graphics.TransformOrigin(1f, 0.5f) // Pivote derecho
                                pageOffset > 0 -> androidx.compose.ui.graphics.TransformOrigin(0f, 0.5f) // Pivote izquierdo
                                else -> androidx.compose.ui.graphics.TransformOrigin(0.5f, 0.5f)
                            }
                            
                            // Escala ligeramente para dar profundidad
                            val scale = 1f - (pageOffset.absoluteValue * 0.1f)
                            scaleX = scale
                            scaleY = scale
                            
                            // Transparencia gradual
                            alpha = 1f - (pageOffset.absoluteValue * 0.4f).coerceIn(0f, 0.6f)
                        }
                        .drawWithContent {
                            drawContent()
                            
                            // Sombreado dinámico
                            val absOffset = pageOffset.absoluteValue
                            if (absOffset > 0.01f) {
                                // Sombra de pliegue
                                val shadowAlpha = (absOffset * 0.5f).coerceIn(0f, 0.4f)
                                if (pageOffset < 0) {
                                    // Sombra en el lado derecho (página saliendo)
                                    drawRect(
                                        brush = Brush.horizontalGradient(
                                            colors = listOf(
                                                Color.Transparent,
                                                Color.Black.copy(alpha = shadowAlpha)
                                            ),
                                            startX = size.width * 0.5f,
                                            endX = size.width
                                        )
                                    )
                                } else {
                                    // Sombra en el lado izquierdo (página entrando)
                                    drawRect(
                                        brush = Brush.horizontalGradient(
                                            colors = listOf(
                                                Color.Black.copy(alpha = shadowAlpha),
                                                Color.Transparent
                                            ),
                                            startX = 0f,
                                            endX = size.width * 0.5f
                                        )
                                    )
                                }
                            }
                        }
                ) {
                    // Solo habilitar gestos de notas en la página actual
                    val isCurrentPage = pagerState.currentPage == pageIndex
                    
                    StickyNotesLayer(
                        pageIndex = pageIndex,
                        colors = colors,
                        enabled = notesEnabled && isCurrentPage
                    ) {
                        when (page?.type) {
                            PageType.HOME -> {
                                HomePageContent(
                                    palette = palette,
                                    isDarkMode = isDarkMode,
                                    colors = colors,
                                    onOpenSettings = onOpenSettings,
                                    onOpenAppDrawer = onOpenAppDrawer,
                                    onLaunchApp = onLaunchApp
                                )
                            }
                            
                            PageType.GLANCE -> {
                                GlancePage(
                                    page = page,
                                    colors = colors,
                                    onOpenCalendar = {
                                        // TODO: Abrir app de calendario
                                    }
                                )
                            }
                            
                            PageType.WIDGETS -> {
                                WidgetPageContent(
                                    page = page,
                                    colors = colors
                                )
                            }
                            
                            PageType.CALENDAR -> {
                                CalendarPageContent(
                                    page = page,
                                    colors = colors
                                )
                            }
                            
                            PageType.NOTES -> {
                                NotesPageContent(
                                    page = page,
                                    colors = colors
                                )
                            }
                            
                            PageType.ADVENTURE -> {
                                AdventureClockPage(
                                    colors = colors
                                )
                            }
                            
                            PageType.AUDIOBOOK -> {
                                // Pagina completa de audiolibros
                                AudiobookLauncherPage(
                                    colors = colors
                                )
                            }
                            
                            null -> {
                                // Página vacía
                                Box(modifier = Modifier.fillMaxSize())
                            }
                        }
                    }
                }
            }
            
            // Indicadores de página (solo si hay más de una página)
            if (pages.size > 1) {
                PageIndicators(
                    pageCount = pages.size,
                    currentPage = pagerState.currentPage,
                    homeIndex = homeIndex,
                    colors = colors,
                    onPageClick = { index ->
                        coroutineScope.launch {
                            pagerState.animateScrollToPage(index)
                        }
                    },
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 32.dp)
                        .systemBarsPadding()
                )
            }
            
            // ═══════════════════════════════════════════════════════════════
            // BARRA DE BOTONES SUPERIOR (centrada, fuera del pager)
            // 5 botones: [⊚] [∫] [‡] [∫] [⊗]
            // Posición 1: Cambio de perfil (long press)
            // Posición 3: Settings (tap)
            // ═══════════════════════════════════════════════════════════════
            TopButtonBar(
                colors = colors,
                onOpenSettings = onOpenSettings,
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .systemBarsPadding()
                    .padding(top = 16.dp)
            )
        }
    }
}

/**
 * Barra superior con 5 botones centrados
 * 
 * Layout: [⊚] [∫] [‡] [∫] [⊗]
 * - Posición 1 (⊚): Cambio de perfil con biometría (long press)
 * - Posición 3 (‡): Settings (tap)
 * - Posiciones 2, 4, 5: Señuelos decorativos
 */
@Composable
private fun TopButtonBar(
    colors: NevenColors,
    onOpenSettings: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    
    // Detectar si estamos en Work Profile
    val isPrivateProfile = remember {
        val dpm = context.getSystemService(Context.DEVICE_POLICY_SERVICE) as android.app.admin.DevicePolicyManager
        dpm.isProfileOwnerApp(context.packageName)
    }
    
    // CrossProfileApps para cambiar de perfil
    val crossProfileApps = remember {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
            context.getSystemService(Context.CROSS_PROFILE_APPS_SERVICE) as? android.content.pm.CrossProfileApps
        } else null
    }
    
    val hasOtherProfile = crossProfileApps?.targetUserProfiles?.isNotEmpty() == true
    val profileSymbol = if (isPrivateProfile) "⊛" else "⊚"
    
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Botón 1: Cambio de perfil (solo si hay otro perfil disponible)
        TopBarButton(
            symbol = profileSymbol,
            colors = colors,
            isDecoy = false,
            onClick = { },
            onLongClick = if (hasOtherProfile) {
                {
                    // Lógica de cambio de perfil con biometría
                    crossProfileApps?.let { cpa ->
                        val targetProfile = cpa.targetUserProfiles.firstOrNull()
                        if (targetProfile != null) {
                            if (!isPrivateProfile) {
                                // Personal → Privado: pedir biometría
                                val biometricManager = androidx.biometric.BiometricManager.from(context)
                                val canAuth = biometricManager.canAuthenticate(
                                    androidx.biometric.BiometricManager.Authenticators.BIOMETRIC_WEAK or
                                    androidx.biometric.BiometricManager.Authenticators.DEVICE_CREDENTIAL
                                )
                                if (canAuth == androidx.biometric.BiometricManager.BIOMETRIC_SUCCESS) {
                                    val activity = context as? androidx.fragment.app.FragmentActivity
                                    if (activity != null) {
                                        val executor = androidx.core.content.ContextCompat.getMainExecutor(context)
                                        val prompt = androidx.biometric.BiometricPrompt(
                                            activity, executor,
                                            object : androidx.biometric.BiometricPrompt.AuthenticationCallback() {
                                                override fun onAuthenticationSucceeded(result: androidx.biometric.BiometricPrompt.AuthenticationResult) {
                                                    try {
                                                        cpa.startMainActivity(
                                                            android.content.ComponentName(context.packageName, "com.neven.launcher.ui.home.HomeActivity"),
                                                            targetProfile
                                                        )
                                                    } catch (_: Exception) { }
                                                }
                                            }
                                        )
                                        val info = androidx.biometric.BiometricPrompt.PromptInfo.Builder()
                                            .setTitle("NEVEN")
                                            .setSubtitle("Verificación requerida")
                                            .setAllowedAuthenticators(
                                                androidx.biometric.BiometricManager.Authenticators.BIOMETRIC_WEAK or
                                                androidx.biometric.BiometricManager.Authenticators.DEVICE_CREDENTIAL
                                            )
                                            .build()
                                        prompt.authenticate(info)
                                    }
                                } else {
                                    try {
                                        cpa.startMainActivity(
                                            android.content.ComponentName(context.packageName, "com.neven.launcher.ui.home.HomeActivity"),
                                            targetProfile
                                        )
                                    } catch (_: Exception) { }
                                }
                            } else {
                                // Privado → Personal: sin biometría
                                try {
                                    cpa.startMainActivity(
                                        android.content.ComponentName(context.packageName, "com.neven.launcher.ui.home.HomeActivity"),
                                        targetProfile
                                    )
                                } catch (_: Exception) { }
                            }
                        }
                    }
                }
            } else null
        )
        
        // Botón 2: Señuelo (integral)
        TopBarButton(symbol = "∫", colors = colors, isDecoy = true)
        
        // Botón 3: Settings (funcional con tap)
        TopBarButton(
            symbol = "‡",
            colors = colors,
            isDecoy = false,
            onClick = onOpenSettings
        )
        
        // Botón 4: Señuelo (integral)
        TopBarButton(symbol = "∫", colors = colors, isDecoy = true)
        
        // Botón 5: Señuelo
        TopBarButton(symbol = "⊗", colors = colors, isDecoy = true)
    }
}

/**
 * Botón individual de la barra superior
 */
@Composable
private fun TopBarButton(
    symbol: String,
    colors: NevenColors,
    isDecoy: Boolean,
    onClick: (() -> Unit)? = null,
    onLongClick: (() -> Unit)? = null
) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(colors.textSecondary.copy(alpha = 0.1f))
            .border(
                width = 0.5.dp,
                color = colors.textSecondary.copy(alpha = 0.2f),
                shape = RoundedCornerShape(20.dp)
            )
            .then(
                when {
                    onClick != null && onLongClick == null -> Modifier.clickable { onClick() }
                    onLongClick != null -> Modifier.pointerInput(Unit) {
                        detectTapGestures(onLongPress = { onLongClick() })
                    }
                    else -> Modifier
                }
            )
            .padding(horizontal = 12.dp, vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = symbol,
            style = MaterialTheme.typography.titleLarge,
            color = if (isDecoy) colors.textSecondary.copy(alpha = 0.5f) else colors.textSecondary
        )
    }
}

/**
 * Indicadores de página estilo dots
 */
@Composable
private fun PageIndicators(
    pageCount: Int,
    currentPage: Int,
    homeIndex: Int,
    colors: NevenColors,
    onPageClick: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        repeat(pageCount) { index ->
            val isSelected = index == currentPage
            val isHome = index == homeIndex
            
            Box(
                modifier = Modifier
                    .size(if (isHome) 10.dp else 8.dp)
                    .clip(CircleShape)
                    .background(
                        when {
                            isSelected -> colors.accent
                            isHome -> colors.accent.copy(alpha = 0.5f)
                            else -> colors.textSecondary.copy(alpha = 0.3f)
                        }
                    )
            )
        }
    }
}

/**
 * Contenido placeholder para página de widgets genérica
 */
@Composable
private fun WidgetPageContent(
    page: LauncherPage,
    colors: NevenColors
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        androidx.compose.material3.Text(
            text = "Widgets",
            style = androidx.compose.material3.MaterialTheme.typography.headlineMedium,
            color = colors.textSecondary.copy(alpha = 0.5f)
        )
    }
}

/**
 * Contenido placeholder para página de calendario dedicada
 */
@Composable
private fun CalendarPageContent(
    page: LauncherPage,
    colors: NevenColors
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        androidx.compose.material3.Text(
            text = "Calendario",
            style = androidx.compose.material3.MaterialTheme.typography.headlineMedium,
            color = colors.textSecondary.copy(alpha = 0.5f)
        )
    }
}

/**
 * Contenido placeholder para página de notas
 */
@Composable
private fun NotesPageContent(
    page: LauncherPage,
    colors: NevenColors
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        androidx.compose.material3.Text(
            text = "Notas",
            style = androidx.compose.material3.MaterialTheme.typography.headlineMedium,
            color = colors.textSecondary.copy(alpha = 0.5f)
        )
    }
}


/**
 * Transformación Page Curl 3D - Efecto de pasar página de libro
 * 
 * Implementa RF-TR01 y RF-TR02 del documento de especificación:
 * - Rotación 3D sobre el eje Y con pivote en el borde
 * - Compensación de traslación para giro rígido
 * - Sombreado dinámico de pliegue y sombra proyectada
 * 
 * @param pageOffset Offset de la página respecto al centro (-1.0 a 1.0)
 */
private fun Modifier.pageCurlTransformation(pageOffset: Float): Modifier = this
    .graphicsLayer {
        val width = size.width
        val height = size.height
        
        // Ángulo máximo de rotación (90 grados)
        val maxRotation = 90f
        
        // Página saliente (yendo hacia la izquierda): offset negativo
        // Página entrante (viniendo desde la derecha): offset positivo
        val rotation = -pageOffset * maxRotation
        
        // RF-TR01: Bisagra de Pivote Dinámica
        when {
            pageOffset < 0 -> {
                // Página saliendo hacia la izquierda - pivote en borde derecho
                transformOrigin = androidx.compose.ui.graphics.TransformOrigin(1f, 0.5f)
            }
            pageOffset > 0 -> {
                // Página entrando desde la derecha - pivote en borde izquierdo
                transformOrigin = androidx.compose.ui.graphics.TransformOrigin(0f, 0.5f)
            }
            else -> {
                // Página centrada
                transformOrigin = androidx.compose.ui.graphics.TransformOrigin(0.5f, 0.5f)
            }
        }
        
        // RF-TR01: Compensación de traslación
        // Anular el desplazamiento horizontal nativo para que gire sobre el lomo
        translationX = -width * pageOffset
        
        // RF-TR01: Perspectiva de cámara
        // cameraDistance calibrada para evitar aberraciones ópticas
        cameraDistance = width * 14f / density
        
        // Rotación sobre el eje Y
        rotationY = rotation
        
        // Reducir alpha gradualmente conforme la página se aleja
        alpha = 1f - (pageOffset.absoluteValue * 0.3f).coerceIn(0f, 0.5f)
    }
    .drawWithContent {
        drawContent()
        
        val width = size.width
        val absOffset = pageOffset.absoluteValue
        
        // RF-TR02: Sombreado Dinámico (solo si hay offset)
        if (absOffset > 0.01f) {
            when {
                pageOffset < 0 -> {
                    // Página saliente - Sombra de pliegue en el lado derecho
                    // α_fold = |p| * 0.75
                    val alphaFold = (absOffset * 0.75f).coerceIn(0f, 0.6f)
                    
                    drawRect(
                        brush = Brush.horizontalGradient(
                            colors = listOf(
                                Color.Transparent,
                                Color.Black.copy(alpha = alphaFold)
                            ),
                            startX = width * 0.4f,
                            endX = width
                        )
                    )
                }
                pageOffset > 0 -> {
                    // Página entrante - Sombra proyectada en el lado izquierdo
                    // α_cast = (1.0 - |p|) * 0.50
                    val alphaCast = ((1f - absOffset) * 0.50f).coerceIn(0f, 0.4f)
                    
                    drawRect(
                        brush = Brush.horizontalGradient(
                            colors = listOf(
                                Color.Black.copy(alpha = alphaCast),
                                Color.Transparent
                            ),
                            startX = 0f,
                            endX = width * 0.3f
                        )
                    )
                }
            }
        }
    }
