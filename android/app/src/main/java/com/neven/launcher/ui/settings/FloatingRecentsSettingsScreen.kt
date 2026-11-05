package com.neven.launcher.ui.settings

import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Process
import android.provider.Settings
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.services.FloatingRecentsService
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.launch

/**
 * Verifica si la app tiene permiso de acceso a estadísticas de uso
 */
private fun checkUsageStatsPermission(context: Context): Boolean {
    val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
    val mode = appOps.checkOpNoThrow(
        AppOpsManager.OPSTR_GET_USAGE_STATS,
        Process.myUid(),
        context.packageName
    )
    return mode == AppOpsManager.MODE_ALLOWED
}

/**
 * Pantalla de configuración del botón flotante de recientes
 * Diseño consistente con el resto de pantallas de NEVEN
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FloatingRecentsSettingsScreen(
    colors: NevenColors,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val settingsRepository = remember { SettingsRepository.getInstance(context) }
    val scope = rememberCoroutineScope()
    
    val isEnabled by settingsRepository.floatingRecentsEnabledFlow.collectAsState(initial = false)
    
    var hasOverlayPermission by remember { mutableStateOf(Settings.canDrawOverlays(context)) }
    var hasUsageStatsPermission by remember { mutableStateOf(checkUsageStatsPermission(context)) }
    
    LaunchedEffect(Unit) {
        while (true) {
            kotlinx.coroutines.delay(1000)
            hasOverlayPermission = Settings.canDrawOverlays(context)
            hasUsageStatsPermission = checkUsageStatsPermission(context)
        }
    }
    
    LaunchedEffect(isEnabled, hasOverlayPermission) {
        if (isEnabled && hasOverlayPermission) {
            FloatingRecentsService.start(context)
        } else {
            FloatingRecentsService.stop(context)
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Botón Flotante",
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.Default.ArrowBack,
                            contentDescription = "Volver",
                            tint = colors.textPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.Transparent
                )
            )
        },
        containerColor = Color.Transparent
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp)
        ) {
            // Toggle Principal
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                border = BorderStroke(
                    1.dp, 
                    if (isEnabled && hasOverlayPermission) colors.accent
                    else colors.textSecondary.copy(alpha = 0.3f)
                )
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable(enabled = hasOverlayPermission) {
                            scope.launch {
                                settingsRepository.setFloatingRecentsEnabled(!isEnabled)
                            }
                        }
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Botón Flotante de Recientes",
                            style = MaterialTheme.typography.titleMedium,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Bold,
                            color = colors.textPrimary
                        )
                        Text(
                            text = when {
                                !hasOverlayPermission -> "Falta permiso de overlay"
                                isEnabled -> "Activo - toca el botón para ver recientes"
                                else -> "Desactivado"
                            },
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = NevenFontFamily,
                            color = colors.textSecondary
                        )
                    }
                    
                    Switch(
                        checked = isEnabled,
                        onCheckedChange = { enabled ->
                            if (hasOverlayPermission) {
                                scope.launch {
                                    settingsRepository.setFloatingRecentsEnabled(enabled)
                                }
                            }
                        },
                        enabled = hasOverlayPermission,
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = colors.accent,
                            checkedTrackColor = colors.accent.copy(alpha = 0.3f),
                            uncheckedThumbColor = colors.textSecondary,
                            uncheckedTrackColor = colors.textSecondary.copy(alpha = 0.2f)
                        )
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Seccion: Permisos requeridos
            Text(
                text = "Permisos requeridos",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            Text(
                text = "Necesarios para que el botón funcione",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Permiso de overlay
            PermissionCard(
                title = "Mostrar sobre otras apps",
                description = "Permite que el botón aparezca sobre todo",
                isGranted = hasOverlayPermission,
                colors = colors,
                onClick = {
                    val intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:${context.packageName}")
                    )
                    context.startActivity(intent)
                }
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Permiso de estadísticas de uso
            PermissionCard(
                title = "Acceso a estadísticas de uso",
                description = "Necesario para ver apps recientes",
                isGranted = hasUsageStatsPermission,
                colors = colors,
                onClick = {
                    val intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
                    context.startActivity(intent)
                }
            )
            
            if (!hasOverlayPermission) {
                Spacer(modifier = Modifier.height(16.dp))
                
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                    border = BorderStroke(1.dp, colors.accent.copy(alpha = 0.5f))
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.Top
                    ) {
                        Text(
                            text = "!",
                            style = MaterialTheme.typography.titleMedium,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Bold,
                            color = colors.accent,
                            modifier = Modifier.padding(end = 12.dp)
                        )
                        Text(
                            text = "Habilita el permiso de overlay para que el botón flotante aparezca sobre todas las apps. El permiso de estadísticas de uso es opcional pero recomendado para ver las apps recientes.",
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = NevenFontFamily,
                            color = colors.textSecondary
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Info de uso
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                border = BorderStroke(1.dp, colors.accent.copy(alpha = 0.5f))
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Cómo funciona",
                        style = MaterialTheme.typography.titleSmall,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.textPrimary
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    val instructions = listOf(
                        "El botón aparece sobre todas las apps",
                        "Arrastra el botón para moverlo",
                        "Toca el botón para ver apps recientes",
                        "Útil cuando los gestos del sistema no funcionan"
                    )
                    
                    instructions.forEach { instruction ->
                        Row(
                            modifier = Modifier.padding(vertical = 4.dp)
                        ) {
                            Text(
                                text = "•",
                                fontFamily = NevenFontFamily,
                                color = colors.accent,
                                modifier = Modifier.padding(end = 8.dp)
                            )
                            Text(
                                text = instruction,
                                style = MaterialTheme.typography.bodySmall,
                                fontFamily = NevenFontFamily,
                                color = colors.textSecondary
                            )
                        }
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

/**
 * Card de permiso - solo borde, sin relleno
 */
@Composable
private fun PermissionCard(
    title: String,
    description: String,
    isGranted: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        border = BorderStroke(
            1.dp,
            if (isGranted) colors.accent else colors.textSecondary.copy(alpha = 0.3f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(Color.Transparent, RoundedCornerShape(20.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = if (isGranted) Icons.Default.Check else Icons.Default.Warning,
                    contentDescription = null,
                    tint = if (isGranted) colors.accent else colors.textSecondary,
                    modifier = Modifier.size(24.dp)
                )
            }
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = colors.textPrimary
                )
                Text(
                    text = if (isGranted) "Habilitado ✓" else "Toca para configurar",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = if (isGranted) colors.accent else colors.textSecondary
                )
            }
        }
    }
}
