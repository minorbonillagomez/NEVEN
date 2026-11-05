package com.neven.launcher.ui.settings

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.graphics.drawable.toBitmap
import com.neven.launcher.R
import com.neven.launcher.data.NotificationPopupSize
import com.neven.launcher.data.NotificationPreferencesRepository
import com.neven.launcher.services.NevenNotificationListenerService
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

/**
 * Pantalla de configuración de Notificaciones Científicas
 * 
 * Permite configurar:
 * - Activar/desactivar popup científico
 * - Tamaño del popup (Compacto, Normal, Expandido)
 * - Renderizado LaTeX
 * - Mostrar timestamp
 * - Respuesta rápida
 * - Apps excluidas
 */
@Composable
fun NotificationsSettingsScreen(
    colors: NevenColors,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val preferences = remember { NotificationPreferencesRepository(context) }
    
    // Estados de las preferencias
    var popupEnabled by remember { mutableStateOf(true) }
    var popupSize by remember { mutableStateOf(NotificationPopupSize.NORMAL) }
    var renderLatex by remember { mutableStateOf(true) }
    var showTimestamp by remember { mutableStateOf(true) }
    var quickReplyEnabled by remember { mutableStateOf(true) }
    var excludedApps by remember { mutableStateOf(setOf<String>()) }
    var maxPopups by remember { mutableStateOf(3) }
    
    // Estado del permiso de notificaciones
    var hasNotificationAccess by remember { mutableStateOf(false) }
    var hasOverlayPermission by remember { mutableStateOf(false) }
    
    // Cargar preferencias
    LaunchedEffect(Unit) {
        popupEnabled = preferences.popupEnabled.first()
        popupSize = preferences.popupSize.first()
        renderLatex = preferences.renderLatex.first()
        showTimestamp = preferences.showTimestamp.first()
        quickReplyEnabled = preferences.quickReplyEnabled.first()
        excludedApps = preferences.excludedApps.first()
        maxPopups = preferences.maxPopups.first()
        
        // Verificar permisos
        hasNotificationAccess = isNotificationListenerEnabled(context)
        hasOverlayPermission = canDrawOverlays(context)
    }
    
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
            
            // Símbolo científico ∇ (nabla/gradiente - representa notificaciones como papers)
            Text(
                text = "∇",
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Text(
                text = stringResource(R.string.settings_notifications),
                style = MaterialTheme.typography.headlineMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
        }
        
        HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.15f))
        
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // ═══════════════════════════════════════════════════════════════
            // PERMISO DE NOTIFICACIONES
            // ═══════════════════════════════════════════════════════════════
            if (!hasNotificationAccess) {
                item {
                    PermissionCard(
                        title = "Acceso a notificaciones",
                        description = "NEVEN necesita acceso a las notificaciones para mostrar el popup científico",
                        colors = colors,
                        onGrantPermission = {
                            openNotificationListenerSettings(context)
                        }
                    )
                }
                
                item {
                    Spacer(modifier = Modifier.height(8.dp))
                }
            }
            
            // ═══════════════════════════════════════════════════════════════
            // PERMISO DE OVERLAY (Mostrar sobre otras apps)
            // ═══════════════════════════════════════════════════════════════
            if (!hasOverlayPermission) {
                item {
                    PermissionCard(
                        title = "Mostrar sobre otras apps",
                        description = "Necesario para mostrar el popup flotante de notificaciones",
                        colors = colors,
                        onGrantPermission = {
                            openOverlaySettings(context)
                        }
                    )
                }
                
                item {
                    HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
                }
            }
            
            // Estado de conexión del servicio
            if (hasNotificationAccess && hasOverlayPermission) {
                item {
                    ServiceStatusCard(
                        isConnected = NevenNotificationListenerService.isConnected,
                        colors = colors
                    )
                }
                
                item {
                    HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
                }
            }
            
            // ═══════════════════════════════════════════════════════════════
            // POPUP CIENTÍFICO
            // ═══════════════════════════════════════════════════════════════
            item {
                SettingsToggleItem(
                    title = stringResource(R.string.notifications_popup_enabled),
                    description = stringResource(R.string.notifications_popup_enabled_desc),
                    checked = popupEnabled,
                    onCheckedChange = { enabled ->
                        popupEnabled = enabled
                        scope.launch { preferences.setPopupEnabled(enabled) }
                    },
                    colors = colors,
                    enabled = hasNotificationAccess
                )
            }
            
            // ═══════════════════════════════════════════════════════════════
            // TAMAÑO DEL POPUP
            // ═══════════════════════════════════════════════════════════════
            item {
                PopupSizeSelector(
                    currentSize = popupSize,
                    onSizeChange = { size ->
                        popupSize = size
                        scope.launch { preferences.setPopupSize(size) }
                    },
                    colors = colors,
                    enabled = popupEnabled && hasNotificationAccess
                )
            }
            
            item {
                Spacer(modifier = Modifier.height(8.dp))
            }
            
            // ═══════════════════════════════════════════════════════════════
            // MÁXIMO DE POPUPS
            // ═══════════════════════════════════════════════════════════════
            item {
                MaxPopupsSelector(
                    currentMax = maxPopups,
                    onMaxChange = { max ->
                        maxPopups = max
                        scope.launch { preferences.setMaxPopups(max) }
                    },
                    colors = colors,
                    enabled = popupEnabled && hasNotificationAccess
                )
            }
            
            item {
                HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
            }
            
            // ═══════════════════════════════════════════════════════════════
            // OPCIONES DE VISUALIZACIÓN
            // ═══════════════════════════════════════════════════════════════
            item {
                Text(
                    text = "Visualización",
                    style = MaterialTheme.typography.labelLarge,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.accent,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
            }
            
            item {
                SettingsToggleItem(
                    title = stringResource(R.string.notifications_render_latex),
                    description = stringResource(R.string.notifications_render_latex_desc),
                    checked = renderLatex,
                    onCheckedChange = { enabled ->
                        renderLatex = enabled
                        scope.launch { preferences.setRenderLatex(enabled) }
                    },
                    colors = colors,
                    enabled = popupEnabled && hasNotificationAccess
                )
            }
            
            item {
                SettingsToggleItem(
                    title = stringResource(R.string.notifications_show_timestamp),
                    description = stringResource(R.string.notifications_show_timestamp_desc),
                    checked = showTimestamp,
                    onCheckedChange = { enabled ->
                        showTimestamp = enabled
                        scope.launch { preferences.setShowTimestamp(enabled) }
                    },
                    colors = colors,
                    enabled = popupEnabled && hasNotificationAccess
                )
            }
            
            item {
                SettingsToggleItem(
                    title = stringResource(R.string.notifications_quick_reply),
                    description = stringResource(R.string.notifications_quick_reply_desc),
                    checked = quickReplyEnabled,
                    onCheckedChange = { enabled ->
                        quickReplyEnabled = enabled
                        scope.launch { preferences.setQuickReplyEnabled(enabled) }
                    },
                    colors = colors,
                    enabled = popupEnabled && hasNotificationAccess
                )
            }
            
            item {
                HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
            }
            
            // ═══════════════════════════════════════════════════════════════
            // APPS EXCLUIDAS
            // ═══════════════════════════════════════════════════════════════
            item {
                ExcludedAppsSection(
                    excludedApps = excludedApps,
                    onExcludedAppsChange = { apps ->
                        excludedApps = apps
                        scope.launch { preferences.setExcludedApps(apps) }
                    },
                    colors = colors,
                    enabled = popupEnabled && hasNotificationAccess
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
 * Card para solicitar permiso
 */
@Composable
private fun PermissionCard(
    title: String,
    description: String,
    colors: NevenColors,
    onGrantPermission: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = colors.accent.copy(alpha = 0.1f)
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "⚠",
                    style = MaterialTheme.typography.titleLarge,
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.textPrimary
                )
            }
            
            Text(
                text = description,
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Button(
                onClick = onGrantPermission,
                colors = ButtonDefaults.buttonColors(
                    containerColor = colors.accent
                ),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text(
                    text = stringResource(R.string.notifications_grant_permission),
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

/**
 * Card que muestra el estado de conexión del servicio
 */
@Composable
private fun ServiceStatusCard(
    isConnected: Boolean,
    colors: NevenColors
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                if (isConnected) colors.accent.copy(alpha = 0.08f)
                else colors.textSecondary.copy(alpha = 0.08f),
                RoundedCornerShape(8.dp)
            )
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = if (isConnected) "●" else "○",
            style = MaterialTheme.typography.bodyLarge,
            color = if (isConnected) colors.accent else colors.textSecondary
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        Column {
            Text(
                text = if (isConnected) "Servicio conectado" else "Servicio desconectado",
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = colors.textPrimary
            )
            Text(
                text = if (isConnected) "Escuchando notificaciones" else "Reinicia el launcher para reconectar",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
        }
    }
}

/**
 * Item de toggle para settings
 */
@Composable
private fun SettingsToggleItem(
    title: String,
    description: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    colors: NevenColors,
    enabled: Boolean = true
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled) { onCheckedChange(!checked) }
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyLarge,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = if (enabled) colors.textPrimary else colors.textSecondary.copy(alpha = 0.5f)
            )
            
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = if (enabled) colors.textSecondary else colors.textSecondary.copy(alpha = 0.3f)
            )
        }
        
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            enabled = enabled,
            colors = SwitchDefaults.colors(
                checkedThumbColor = colors.accent,
                checkedTrackColor = colors.accent.copy(alpha = 0.3f)
            )
        )
    }
}

/**
 * Selector de tamaño de popup
 */
@Composable
private fun PopupSizeSelector(
    currentSize: NotificationPopupSize,
    onSizeChange: (NotificationPopupSize) -> Unit,
    colors: NevenColors,
    enabled: Boolean = true
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = stringResource(R.string.notifications_popup_size),
            style = MaterialTheme.typography.bodyLarge,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.Medium,
            color = if (enabled) colors.textPrimary else colors.textSecondary.copy(alpha = 0.5f)
        )
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            NotificationPopupSize.values().forEach { size ->
                val isSelected = size == currentSize
                val sizeLabel = when (size) {
                    NotificationPopupSize.COMPACT -> stringResource(R.string.notifications_popup_size_compact)
                    NotificationPopupSize.NORMAL -> stringResource(R.string.notifications_popup_size_normal)
                    NotificationPopupSize.EXPANDED -> stringResource(R.string.notifications_popup_size_expanded)
                }
                
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color.Transparent)
                        .border(
                            width = if (isSelected) 1.dp else 0.5.dp,
                            color = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(8.dp)
                        )
                        .clickable(enabled = enabled) { onSizeChange(size) }
                        .padding(12.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = sizeLabel,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                        color = if (enabled) colors.textSecondary 
                               else colors.textSecondary.copy(alpha = 0.3f)
                    )
                }
            }
        }
    }
}

/**
 * Selector de máximo de popups simultáneos
 */
@Composable
private fun MaxPopupsSelector(
    currentMax: Int,
    onMaxChange: (Int) -> Unit,
    colors: NevenColors,
    enabled: Boolean = true
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = stringResource(R.string.notifications_max_popups),
                    style = MaterialTheme.typography.bodyLarge,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = if (enabled) colors.textPrimary else colors.textSecondary.copy(alpha = 0.5f)
                )
                Text(
                    text = stringResource(R.string.notifications_max_popups_desc),
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = if (enabled) colors.textSecondary else colors.textSecondary.copy(alpha = 0.3f)
                )
            }
            
            // Valor actual destacado
            Text(
                text = currentMax.toString(),
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold
                ),
                color = if (enabled) colors.accent else colors.textSecondary.copy(alpha = 0.3f)
            )
        }
        
        // Selector de valores (1-10)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            (1..10).forEach { value ->
                val isSelected = value == currentMax
                
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(6.dp))
                        .background(Color.Transparent)
                        .border(
                            width = if (isSelected) 1.dp else 0.5.dp,
                            color = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(6.dp)
                        )
                        .clickable(enabled = enabled) { onMaxChange(value) }
                        .padding(vertical = 10.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = value.toString(),
                        style = MaterialTheme.typography.labelMedium.copy(
                            fontFamily = NevenFontFamily,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                        ),
                        color = if (!enabled) colors.textSecondary.copy(alpha = 0.3f)
                               else colors.textSecondary
                    )
                }
            }
        }
    }
}

/**
 * Sección de apps excluidas
 */
@Composable
private fun ExcludedAppsSection(
    excludedApps: Set<String>,
    onExcludedAppsChange: (Set<String>) -> Unit,
    colors: NevenColors,
    enabled: Boolean = true
) {
    val context = LocalContext.current
    var showAppPicker by remember { mutableStateOf(false) }
    
    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.notifications_excluded_apps),
                    style = MaterialTheme.typography.bodyLarge,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = if (enabled) colors.textPrimary else colors.textSecondary.copy(alpha = 0.5f)
                )
                
                Text(
                    text = stringResource(R.string.notifications_excluded_apps_desc),
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = if (enabled) colors.textSecondary else colors.textSecondary.copy(alpha = 0.3f)
                )
            }
            
            TextButton(
                onClick = { showAppPicker = true },
                enabled = enabled
            ) {
                Text(
                    text = "+ Agregar",
                    fontFamily = NevenFontFamily,
                    color = if (enabled) colors.accent else colors.textSecondary.copy(alpha = 0.3f)
                )
            }
        }
        
        // Lista de apps excluidas
        if (excludedApps.isNotEmpty()) {
            excludedApps.forEach { packageName ->
                val appName = try {
                    context.packageManager.getApplicationLabel(
                        context.packageManager.getApplicationInfo(packageName, 0)
                    ).toString()
                } catch (e: Exception) {
                    packageName
                }
                
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(
                            colors.textSecondary.copy(alpha = 0.05f),
                            RoundedCornerShape(8.dp)
                        )
                        .padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = appName,
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary,
                        modifier = Modifier.weight(1f)
                    )
                    
                    Text(
                        text = "×",
                        style = MaterialTheme.typography.titleMedium,
                        color = colors.textSecondary,
                        modifier = Modifier
                            .clickable(enabled = enabled) {
                                onExcludedAppsChange(excludedApps - packageName)
                            }
                            .padding(8.dp)
                    )
                }
            }
        } else {
            Text(
                text = "Sin apps excluidas",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary.copy(alpha = 0.5f)
            )
        }
    }
    
    // Dialog para seleccionar apps
    if (showAppPicker) {
        AppPickerDialog(
            excludedApps = excludedApps,
            onAppSelected = { packageName ->
                onExcludedAppsChange(excludedApps + packageName)
            },
            onDismiss = { showAppPicker = false },
            colors = colors
        )
    }
}

/**
 * Dialog para seleccionar apps a excluir
 */
@Composable
private fun AppPickerDialog(
    excludedApps: Set<String>,
    onAppSelected: (String) -> Unit,
    onDismiss: () -> Unit,
    colors: NevenColors
) {
    val context = LocalContext.current
    val installedApps = remember {
        context.packageManager.getInstalledApplications(PackageManager.GET_META_DATA)
            .filter { it.flags and ApplicationInfo.FLAG_SYSTEM == 0 }
            .filter { it.packageName !in excludedApps }
            .sortedBy { context.packageManager.getApplicationLabel(it).toString() }
    }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = colors.background,
        title = {
            Text(
                text = "Seleccionar app",
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
        },
        text = {
            LazyColumn(
                modifier = Modifier.heightIn(max = 400.dp)
            ) {
                items(installedApps) { appInfo ->
                    val appName = context.packageManager.getApplicationLabel(appInfo).toString()
                    val appIcon = try {
                        context.packageManager.getApplicationIcon(appInfo.packageName)
                            .toBitmap(48, 48)
                            .asImageBitmap()
                    } catch (e: Exception) {
                        null
                    }
                    
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                onAppSelected(appInfo.packageName)
                                onDismiss()
                            }
                            .padding(vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        if (appIcon != null) {
                            androidx.compose.foundation.Image(
                                bitmap = appIcon,
                                contentDescription = appName,
                                modifier = Modifier
                                    .size(32.dp)
                                    .clip(CircleShape)
                            )
                        } else {
                            Box(
                                modifier = Modifier
                                    .size(32.dp)
                                    .background(colors.accent.copy(alpha = 0.2f), CircleShape),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = appName.firstOrNull()?.toString() ?: "?",
                                    color = colors.accent
                                )
                            }
                        }
                        
                        Spacer(modifier = Modifier.width(12.dp))
                        
                        Text(
                            text = appName,
                            style = MaterialTheme.typography.bodyMedium,
                            fontFamily = NevenFontFamily,
                            color = colors.textPrimary
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text(
                    text = "Cancelar",
                    fontFamily = NevenFontFamily,
                    color = colors.accent
                )
            }
        }
    )
}

/**
 * Verifica si el servicio de notificaciones está habilitado
 */
private fun isNotificationListenerEnabled(context: Context): Boolean {
    val cn = ComponentName(context, NevenNotificationListenerService::class.java)
    val flat = Settings.Secure.getString(context.contentResolver, "enabled_notification_listeners")
    return flat?.contains(cn.flattenToString()) == true
}

/**
 * Verifica si tiene permiso para mostrar sobre otras apps
 */
private fun canDrawOverlays(context: Context): Boolean {
    return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
        Settings.canDrawOverlays(context)
    } else {
        true
    }
}

/**
 * Abre la configuración de listeners de notificaciones
 */
private fun openNotificationListenerSettings(context: Context) {
    try {
        val intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    } catch (e: Exception) {
        // Fallback a configuración general
        val intent = Intent(Settings.ACTION_SETTINGS)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    }
}

/**
 * Abre la configuración de overlay (mostrar sobre otras apps)
 */
private fun openOverlaySettings(context: Context) {
    try {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:${context.packageName}")
            )
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
        }
    } catch (e: Exception) {
        // Fallback a configuración general
        val intent = Intent(Settings.ACTION_SETTINGS)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    }
}
