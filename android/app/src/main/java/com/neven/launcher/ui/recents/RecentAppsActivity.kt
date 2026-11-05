package com.neven.launcher.ui.recents

import android.app.ActivityManager
import android.app.usage.UsageStats
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.drawable.Drawable
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkHorizontally
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Home
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.graphics.drawable.toBitmap
import com.neven.launcher.data.NevenFontFamily as FontFamilyOption
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.data.ThemeMode
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.NevenTheme
import kotlin.math.abs
import kotlin.math.roundToInt

// Para mutableFloatStateOf que es experimental en algunas versiones
@Suppress("OPT_IN_USAGE")
private fun mutableFloatStateOf(value: Float) = androidx.compose.runtime.mutableFloatStateOf(value)

/**
 * Activity que muestra las apps recientes en un estilo de carrusel horizontal
 * Se abre como overlay transparente cuando se toca el botón flotante
 */
class RecentAppsActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Verificar permisos antes de mostrar UI
        val hasPermission = hasUsageStatsPermission(this)
        
        setContent {
            // Repositorio de settings para obtener tema y fuente
            val settingsRepository = remember { SettingsRepository.getInstance(this) }
            
            val selectedPalette by settingsRepository.paletteFlow
                .collectAsState(initial = NevenPalette.CLASICO)
            val themeMode by settingsRepository.themeModeFlow
                .collectAsState(initial = ThemeMode.DARK)
            val fontSizeScale by settingsRepository.fontSizeScaleFlow
                .collectAsState(initial = 1.0f)
            val fontFamily by settingsRepository.fontFamilyFlow
                .collectAsState(initial = FontFamilyOption.SERIF)
            val customAccentColor by settingsRepository.customAccentColorFlow
                .collectAsState(initial = "#D32F2F")
            
            val isSystemDark = isSystemInDarkTheme()
            val isDarkMode = when (themeMode) {
                ThemeMode.DARK -> true
                ThemeMode.LIGHT -> false
                ThemeMode.AUTO -> isSystemDark
            }
            
            NevenTheme(
                palette = selectedPalette,
                darkTheme = isDarkMode,
                fontScale = fontSizeScale,
                fontFamily = fontFamily,
                customAccentColorHex = customAccentColor
            ) {
                RecentAppsScreen(
                    initialHasPermission = hasPermission,
                    onAppClick = { packageName ->
                        launchApp(packageName)
                        finish()
                    },
                    onDismiss = { finish() },
                    onRequestPermission = {
                        startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
                    },
                    onKillApp = { packageName ->
                        killApp(packageName)
                    },
                    onKillAll = { packages ->
                        packages.forEach { killApp(it) }
                    },
                    onGoHome = {
                        goHome()
                        finish()
                    }
                )
            }
        }
    }
    
    private fun launchApp(packageName: String) {
        try {
            val intent = packageManager.getLaunchIntentForPackage(packageName)
            if (intent != null) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(intent)
            }
        } catch (e: Exception) {
            android.util.Log.e("RecentApps", "Error launching app: ${e.message}")
        }
    }
    
    private fun killApp(packageName: String) {
        try {
            val activityManager = getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
            activityManager.killBackgroundProcesses(packageName)
        } catch (e: Exception) {
            // Puede fallar si no tenemos permisos, pero al menos lo intentamos
            android.util.Log.e("RecentApps", "Error killing app: ${e.message}")
        }
    }
    
    private fun goHome() {
        try {
            val intent = Intent(Intent.ACTION_MAIN).apply {
                addCategory(Intent.CATEGORY_HOME)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            startActivity(intent)
        } catch (e: Exception) {
            android.util.Log.e("RecentApps", "Error going home: ${e.message}")
        }
    }
}

data class RecentAppInfo(
    val packageName: String,
    val appName: String,
    val icon: Drawable,
    val lastUsed: Long
)

@Composable
fun RecentAppsScreen(
    initialHasPermission: Boolean,
    onAppClick: (String) -> Unit,
    onDismiss: () -> Unit,
    onRequestPermission: () -> Unit,
    onKillApp: (String) -> Unit,
    onKillAll: (List<String>) -> Unit,
    onGoHome: () -> Unit
) {
    val context = LocalContext.current
    var recentApps by remember { mutableStateOf<List<RecentAppInfo>>(emptyList()) }
    var hasPermission by remember { mutableStateOf(initialHasPermission) }
    var isLoading by remember { mutableStateOf(true) }
    var loadError by remember { mutableStateOf<String?>(null) }
    
    // Lista de apps removidas (para animación)
    var removedApps by remember { mutableStateOf<Set<String>>(emptySet()) }
    
    // Cargar apps recientes
    LaunchedEffect(hasPermission) {
        if (hasPermission) {
            try {
                recentApps = getRecentApps(context)
                loadError = null
            } catch (e: Exception) {
                loadError = "Error al cargar apps: ${e.message}"
                android.util.Log.e("RecentApps", "Error loading apps", e)
            }
        }
        isLoading = false
    }
    
    // Filtrar apps removidas
    val visibleApps = recentApps.filter { it.packageName !in removedApps }
    
    // Fondo semi-transparente que cierra al tocar
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.7f))
            .clickable { onDismiss() },
        contentAlignment = Alignment.Center
    ) {
        // Panel de apps recientes
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(Color.Black.copy(alpha = 0.5f))
                .border(1.dp, Color(0xFFD4E600), RoundedCornerShape(16.dp))
                .clickable { /* No cerrar al tocar el panel */ }
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Header con título y botón cerrar todo
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Apps Recientes",
                    color = Color.White,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp
                )
                
                // Botón Cerrar Todo (solo si hay apps)
                if (visibleApps.isNotEmpty()) {
                    OutlinedButton(
                        onClick = {
                            val packagesToKill = visibleApps.map { it.packageName }
                            onKillAll(packagesToKill)
                            removedApps = removedApps + packagesToKill.toSet()
                        },
                        colors = ButtonDefaults.outlinedButtonColors(
                            contentColor = Color.White
                        ),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFD4E600)),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                        modifier = Modifier.height(32.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Delete,
                            contentDescription = null,
                            modifier = Modifier.size(14.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "Cerrar Todo",
                            fontFamily = NevenFontFamily,
                            fontSize = 12.sp
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            when {
                isLoading -> {
                    CircularProgressIndicator(
                        color = Color(0xFFD4E600),
                        modifier = Modifier.size(32.dp)
                    )
                }
                loadError != null -> {
                    Text(
                        text = loadError!!,
                        color = Color(0xFFFF6B6B),
                        fontFamily = NevenFontFamily,
                        fontSize = 12.sp,
                        textAlign = TextAlign.Center
                    )
                }
                !hasPermission -> {
                    // Solicitar permiso
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Text(
                            text = "Se necesita permiso de uso",
                            color = Color.White,
                            fontFamily = NevenFontFamily,
                            textAlign = TextAlign.Center
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedButton(
                            onClick = onRequestPermission,
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = Color(0xFFD4E600)
                            ),
                            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFD4E600))
                        ) {
                            Text(
                                text = "Otorgar permiso",
                                fontFamily = NevenFontFamily
                            )
                        }
                    }
                }
                visibleApps.isEmpty() -> {
                    Text(
                        text = if (recentApps.isEmpty()) "No hay apps recientes" else "Todas las apps cerradas",
                        color = Color.Gray,
                        fontFamily = NevenFontFamily
                    )
                }
                else -> {
                    // Hint de arrastrar
                    Text(
                        text = "↓ Arrastra hacia abajo para cerrar",
                        color = Color.Gray,
                        fontFamily = NevenFontFamily,
                        fontSize = 11.sp
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    // Lista horizontal de apps recientes
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(16.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp)
                    ) {
                        items(visibleApps, key = { it.packageName }) { app ->
                            RecentAppItem(
                                app = app,
                                onClick = { onAppClick(app.packageName) },
                                onSwipeToClose = {
                                    onKillApp(app.packageName)
                                    removedApps = removedApps + app.packageName
                                }
                            )
                        }
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Botón HOME y hint
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Hint para cerrar
                Text(
                    text = "Toca fuera para cerrar",
                    color = Color.Gray,
                    fontFamily = NevenFontFamily,
                    fontSize = 12.sp
                )
                
                // Botón HOME
                OutlinedButton(
                    onClick = onGoHome,
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = Color.White
                    ),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFD4E600)),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                    modifier = Modifier.height(32.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Home,
                        contentDescription = null,
                        modifier = Modifier.size(14.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "HOME",
                        fontFamily = NevenFontFamily,
                        fontSize = 12.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun RecentAppItem(
    app: RecentAppInfo,
    onClick: () -> Unit,
    onSwipeToClose: () -> Unit
) {
    var offsetY by remember { mutableFloatStateOf(0f) }
    var isDragging by remember { mutableStateOf(false) }
    val threshold = 120f // Umbral para cerrar (en píxeles)
    
    // Animación de opacidad basada en el drag
    val alpha by animateFloatAsState(
        targetValue = if (isDragging) {
            (1f - (abs(offsetY) / threshold).coerceIn(0f, 1f) * 0.7f)
        } else 1f,
        animationSpec = tween(100),
        label = "alpha"
    )
    
    // Escala basada en el drag (se hace más pequeño al arrastrar)
    val scale by animateFloatAsState(
        targetValue = if (isDragging) {
            (1f - (abs(offsetY) / threshold).coerceIn(0f, 1f) * 0.3f)
        } else 1f,
        animationSpec = tween(100),
        label = "scale"
    )
    
    Column(
        modifier = Modifier
            .width(72.dp)
            .offset { IntOffset(0, offsetY.roundToInt()) }
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                this.alpha = alpha
            }
            .clip(RoundedCornerShape(12.dp))
            .pointerInput(Unit) {
                detectVerticalDragGestures(
                    onDragStart = { isDragging = true },
                    onDragEnd = {
                        isDragging = false
                        if (offsetY > threshold) {
                            // Se arrastró suficiente hacia abajo - cerrar app
                            onSwipeToClose()
                        }
                        offsetY = 0f
                    },
                    onDragCancel = {
                        isDragging = false
                        offsetY = 0f
                    },
                    onVerticalDrag = { change, dragAmount ->
                        change.consume()
                        // Solo permitir drag hacia abajo
                        if (dragAmount > 0 || offsetY > 0) {
                            offsetY = (offsetY + dragAmount).coerceAtLeast(0f)
                        }
                    }
                )
            }
            .clickable { onClick() }
            .padding(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Icono
        Box {
            val iconBitmap = remember(app.packageName) {
                try {
                    app.icon.toBitmap(96, 96).asImageBitmap()
                } catch (e: Exception) {
                    null
                }
            }
            
            if (iconBitmap != null) {
                Image(
                    bitmap = iconBitmap,
                    contentDescription = app.appName,
                    modifier = Modifier
                        .size(56.dp)
                        .clip(RoundedCornerShape(12.dp))
                )
            } else {
                // Fallback si el icono falla
                Box(
                    modifier = Modifier
                        .size(56.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color.Gray.copy(alpha = 0.3f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = app.appName.take(1).uppercase(),
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 20.sp
                    )
                }
            }
            
            // Indicador de "cerrar" cuando se arrastra
            if (isDragging && offsetY > threshold * 0.5f) {
                Box(
                    modifier = Modifier
                        .matchParentSize()
                        .background(
                            Color(0xFFFF6B6B).copy(alpha = 0.7f),
                            RoundedCornerShape(12.dp)
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Cerrar",
                        tint = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(6.dp))
        
        // Nombre
        Text(
            text = app.appName,
            color = Color.White,
            fontFamily = NevenFontFamily,
            fontSize = 11.sp,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            textAlign = TextAlign.Center
        )
    }
}

/**
 * Verifica si tenemos permiso de UsageStats
 */
private fun hasUsageStatsPermission(context: Context): Boolean {
    val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
    val time = System.currentTimeMillis()
    val stats = usageStatsManager.queryUsageStats(
        UsageStatsManager.INTERVAL_DAILY,
        time - 1000 * 60,
        time
    )
    return stats != null && stats.isNotEmpty()
}

/**
 * Obtiene la lista de apps usadas recientemente
 */
private fun getRecentApps(context: Context): List<RecentAppInfo> {
    return try {
        val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as? UsageStatsManager
            ?: return emptyList()
        val packageManager = context.packageManager
        val time = System.currentTimeMillis()
        
        // Obtener estadísticas de las últimas 24 horas
        val stats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            time - 1000 * 60 * 60 * 24, // 24 horas
            time
        )
        
        if (stats.isNullOrEmpty()) return emptyList()
        
        // Filtrar y ordenar por último uso
        val launcherPackage = context.packageName
        
        stats
            .asSequence()
            .filter { it.lastTimeUsed > 0 }
            .filter { it.packageName != launcherPackage }
            .filter { stat ->
                // Solo apps que tengan launcher intent (no servicios del sistema)
                try {
                    packageManager.getLaunchIntentForPackage(stat.packageName) != null
                } catch (e: Exception) {
                    false
                }
            }
            .sortedByDescending { it.lastTimeUsed }
            .take(10) // Máximo 10 apps
            .mapNotNull { stat ->
                try {
                    val appInfo = packageManager.getApplicationInfo(stat.packageName, 0)
                    val appName = packageManager.getApplicationLabel(appInfo).toString()
                    val icon = packageManager.getApplicationIcon(appInfo)
                    
                    RecentAppInfo(
                        packageName = stat.packageName,
                        appName = appName,
                        icon = icon,
                        lastUsed = stat.lastTimeUsed
                    )
                } catch (e: PackageManager.NameNotFoundException) {
                    // App desinstalada
                    null
                } catch (e: Exception) {
                    android.util.Log.e("RecentApps", "Error loading app ${stat.packageName}: ${e.message}")
                    null
                }
            }
            .toList()
    } catch (e: Exception) {
        android.util.Log.e("RecentApps", "Error in getRecentApps: ${e.message}", e)
        emptyList()
    }
}
