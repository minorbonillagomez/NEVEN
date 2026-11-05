package com.neven.launcher.ui.home

import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.pm.CrossProfileApps
import android.os.Build
import android.widget.Toast
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import com.neven.launcher.R
import com.neven.launcher.data.FavoritesRepository
import com.neven.launcher.data.HapticIntensity
import com.neven.launcher.data.HapticScale
import com.neven.launcher.data.HapticSound
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.services.NevenDeviceAdminReceiver
import com.neven.launcher.ui.components.RemoveFromFavoritesMenu
import com.neven.launcher.ui.components.ScientificClock
import com.neven.launcher.ui.drawer.loadInstalledApps
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.NevenPalette
import kotlinx.coroutines.launch
import java.util.Locale

/**
 * Contenido de la página HOME
 * 
 * Extraído del HomeScreen original para usar dentro del LauncherPager.
 * Contiene:
 * - Reloj científico
 * - Lista de favoritos con Haptic Feedback
 * - Botón de configuración
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun HomePageContent(
    palette: NevenPalette,
    isDarkMode: Boolean,
    colors: NevenColors,
    onOpenSettings: () -> Unit,
    onOpenAppDrawer: () -> Unit,
    onLaunchApp: (String) -> Unit
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    
    // Repositorios
    val favoritesRepository = remember { FavoritesRepository.getInstance(context) }
    val settingsRepository = remember { SettingsRepository.getInstance(context) }
    
    // Detectar si estamos en Work Profile (Privado)
    val isPrivateProfile = remember {
        val dpm = context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        dpm.isProfileOwnerApp(context.packageName)
    }
    
    // CrossProfileApps para cambiar de perfil
    val crossProfileApps = remember {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            context.getSystemService(Context.CROSS_PROFILE_APPS_SERVICE) as? CrossProfileApps
        } else null
    }
    
    // Verificar si hay otro perfil disponible
    val hasOtherProfile = remember {
        crossProfileApps?.targetUserProfiles?.isNotEmpty() == true
    }
    
    // Observar favoritos desde DataStore
    val favoritePackages by favoritesRepository.favoritesFlow.collectAsState(initial = emptySet())
    val maxFavorites by favoritesRepository.maxFavoritesFlow.collectAsState(initial = 8)
    
    // Observar configuración haptic
    val hapticScale by settingsRepository.hapticScaleFlow.collectAsState(initial = HapticScale.LARGE)
    val hapticIntensity by settingsRepository.hapticIntensityFlow.collectAsState(initial = HapticIntensity.MEDIUM)
    val hapticSound by settingsRepository.hapticSoundFlow.collectAsState(initial = HapticSound.NONE)
    
    // TODO: Load from preferences
    val locale by remember { mutableStateOf(Locale("es")) }
    val showSeconds by remember { mutableStateOf(true) }
    
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
            installedApps.take(6).map { FavoriteApp(it.name, it.packageName, 0) }
        } else {
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
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(vertical = 24.dp)
                .padding(end = 44.dp), // Espacio para el alfabeto lateral
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // ═══════════════════════════════════════════════════════════════
            // CLOCK SECTION
            // ═══════════════════════════════════════════════════════════════
            Spacer(modifier = Modifier.height(32.dp))
            
            ScientificClock(
                colors = colors,
                locale = locale,
                showSeconds = showSeconds
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Separator
            Text(
                text = "↫ ⋇ ↬",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.textSecondary.copy(alpha = 0.5f),
                letterSpacing = 8.sp
            )
            
            Spacer(modifier = Modifier.height(20.dp))
            
            // ═══════════════════════════════════════════════════════════════
            // FAVORITE APPS with Haptic Feedback Scaling
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
            
            Spacer(modifier = Modifier.height(16.dp))
        }
        
        // ═══════════════════════════════════════════════════════════════
        // ALFABETO LATERAL DERECHO - Acceso rapido a todas las apps
        // ═══════════════════════════════════════════════════════════════
        HomeAlphabetSidebar(
            colors = colors,
            hapticScale = hapticScale,
            hapticIntensity = hapticIntensity,
            hapticSound = hapticSound,
            onLaunchApp = onLaunchApp
        )
        
        // ═══════════════════════════════════════════════════════════════
        // PROFILE CONTEXT INDICATOR (top left) - Personal/Privado toggle
        // ═══════════════════════════════════════════════════════════════
        // NOTA: Movido al LauncherPager para evitar interferencia con StickyNotesLayer
        
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


// ProfileContextIndicator movido a LauncherPager para evitar interferencia con StickyNotesLayer
