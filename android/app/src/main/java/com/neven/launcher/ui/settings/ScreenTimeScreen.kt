package com.neven.launcher.ui.settings

import android.content.pm.PackageManager
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.R
import com.neven.launcher.data.UsageStatsRepository
import com.neven.launcher.ui.theme.CharcoalBackground
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.rememberNevenColors

/**
 * Pantalla de Screen Time
 * 
 * Muestra el tiempo de uso de apps:
 * - Total de hoy
 * - Total de la semana
 * - Top apps por uso
 */

/**
 * Periodo de tiempo para mostrar estadísticas
 */
enum class UsagePeriod(val displayName: String) {
    TODAY("Hoy"),
    WEEK("Semana")
}

@Composable
fun ScreenTimeScreen(
    currentPalette: NevenPalette,
    isDarkMode: Boolean,
    onBack: () -> Unit
) {
    // Usar rememberNevenColors para aplicar el color de contraste personalizado
    val colors = rememberNevenColors(currentPalette, isDarkMode)
    val context = LocalContext.current
    val usageStatsRepository = remember { UsageStatsRepository.getInstance(context) }
    val packageManager = context.packageManager
    
    // Estado de permiso
    var hasPermission by remember { mutableStateOf(usageStatsRepository.hasUsageStatsPermission()) }
    
    // Periodo seleccionado
    var selectedPeriod by remember { mutableStateOf(UsagePeriod.TODAY) }
    
    // Estadísticas
    val todayStats = remember(hasPermission) {
        if (hasPermission) usageStatsRepository.getTopAppsToday(10) else emptyList()
    }
    val weekStats = remember(hasPermission) {
        if (hasPermission) usageStatsRepository.getTopAppsWeek(10) else emptyList()
    }
    val totalToday = remember(hasPermission) {
        if (hasPermission) usageStatsRepository.getTotalUsageToday() else 0L
    }
    val totalWeek = remember(hasPermission) {
        if (hasPermission) usageStatsRepository.getTotalUsageWeek() else 0L
    }
    
    CharcoalBackground(
        backgroundColor = colors.background,
        isDark = colors.isDark
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .systemBarsPadding()
        ) {
            // ═══════════════════════════════════════════════════════════════
            // HEADER - Estilo consistente con otras pantallas
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
                        fontFamily = androidx.compose.ui.text.font.FontFamily.Serif
                    ),
                    color = colors.textPrimary
                )
                
                Spacer(modifier = Modifier.width(16.dp))
                
                // Símbolo científico τ (tau - tiempo)
                Text(
                    text = "\u03C4",
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = androidx.compose.ui.text.font.FontFamily.Serif
                    ),
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                Text(
                    text = stringResource(R.string.settings_screen_time),
                    style = MaterialTheme.typography.headlineMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.textPrimary
                )
            }
            
            HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.15f))
            
            if (!hasPermission) {
                // ═══════════════════════════════════════════════════════════════
                // SOLICITAR PERMISO
                // ═══════════════════════════════════════════════════════════════
                PermissionRequestCard(
                    colors = colors,
                    onRequestPermission = {
                        context.startActivity(usageStatsRepository.getUsageStatsSettingsIntent())
                    },
                    onRefresh = {
                        hasPermission = usageStatsRepository.hasUsageStatsPermission()
                    }
                )
            } else {
                // ═══════════════════════════════════════════════════════════════
                // ESTADÍSTICAS
                // ═══════════════════════════════════════════════════════════════
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Total del día/semana
                    item {
                        TotalUsageCard(
                            totalToday = totalToday,
                            totalWeek = totalWeek,
                            selectedPeriod = selectedPeriod,
                            onPeriodChange = { selectedPeriod = it },
                            usageStatsRepository = usageStatsRepository,
                            colors = colors
                        )
                    }
                    
                    // Lista de apps
                    item {
                        Text(
                            text = stringResource(R.string.screen_time_top_apps),
                            style = MaterialTheme.typography.titleMedium,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.SemiBold,
                            color = colors.textPrimary
                        )
                    }
                    
                    val currentStats = if (selectedPeriod == UsagePeriod.TODAY) todayStats else weekStats
                    
                    items(currentStats) { (packageName, usageTime) ->
                        AppUsageItem(
                            packageName = packageName,
                            usageTime = usageTime,
                            packageManager = packageManager,
                            usageStatsRepository = usageStatsRepository,
                            colors = colors
                        )
                    }
                    
                    // Símbolo QED al final
                    item {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 24.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "∎",
                                style = MaterialTheme.typography.titleLarge,
                                color = colors.textSecondary.copy(alpha = 0.4f)
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * Card para solicitar permiso de uso
 */
@Composable
private fun PermissionRequestCard(
    colors: NevenColors,
    onRequestPermission: () -> Unit,
    onRefresh: () -> Unit
) {
    val cardBg = if (colors.isDark) {
        Color(0xFF1B1B1B).copy(alpha = 0.82f)
    } else {
        Color(0xFFFAF9F6).copy(alpha = 0.9f)
    }
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
            .background(
                color = cardBg,
                shape = RoundedCornerShape(16.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = colors.textSecondary.copy(alpha = 0.12f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Icono
        Text(
            text = "⏱",
            style = MaterialTheme.typography.displayMedium,
            color = colors.accent
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = stringResource(R.string.screen_time_permission_title),
            style = MaterialTheme.typography.titleLarge,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.Bold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = stringResource(R.string.screen_time_permission_desc),
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Botón para abrir configuración
        Button(
            onClick = onRequestPermission,
            colors = ButtonDefaults.buttonColors(
                containerColor = colors.accent,
                contentColor = colors.background
            ),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text(
                text = stringResource(R.string.screen_time_grant_permission),
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold
            )
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        // Botón para refrescar
        TextButton(onClick = onRefresh) {
            Text(
                text = stringResource(R.string.screen_time_refresh),
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary
            )
        }
    }
}

/**
 * Card con el total de uso
 */
@Composable
private fun TotalUsageCard(
    totalToday: Long,
    totalWeek: Long,
    selectedPeriod: UsagePeriod,
    onPeriodChange: (UsagePeriod) -> Unit,
    usageStatsRepository: UsageStatsRepository,
    colors: NevenColors
) {
    val cardBg = if (colors.isDark) {
        Color(0xFF1B1B1B).copy(alpha = 0.82f)
    } else {
        Color(0xFFFAF9F6).copy(alpha = 0.9f)
    }
    
    val currentTotal = if (selectedPeriod == UsagePeriod.TODAY) totalToday else totalWeek
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = cardBg,
                shape = RoundedCornerShape(16.dp)
            )
            .border(
                width = 0.5.dp, // Borde delgado minimalista
                color = colors.textSecondary.copy(alpha = 0.12f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Selector de periodo
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            UsagePeriod.values().forEach { period ->
                val isSelected = period == selectedPeriod
                Box(
                    modifier = Modifier
                        .background(
                            color = if (isSelected) colors.accent.copy(alpha = 0.15f) else Color.Transparent,
                            shape = RoundedCornerShape(8.dp)
                        )
                        .border(
                            width = 0.5.dp, // Borde delgado minimalista
                            color = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(8.dp)
                        )
                        .clickable { onPeriodChange(period) }
                        .padding(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Text(
                        text = getLocalizedPeriod(period),
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                        color = if (isSelected) colors.textPrimary else colors.textSecondary
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(20.dp))
        
        // Total de uso
        Text(
            text = usageStatsRepository.formatUsageTime(currentTotal),
            style = MaterialTheme.typography.displayLarge,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.Bold,
            color = colors.accent,
            fontSize = 48.sp
        )
        
        Text(
            text = stringResource(R.string.screen_time_total),
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary
        )
    }
}

@Composable
private fun getLocalizedPeriod(period: UsagePeriod): String {
    return when (period) {
        UsagePeriod.TODAY -> stringResource(R.string.screen_time_today)
        UsagePeriod.WEEK -> stringResource(R.string.screen_time_week)
    }
}

/**
 * Item de uso de app individual
 */
@Composable
private fun AppUsageItem(
    packageName: String,
    usageTime: Long,
    packageManager: PackageManager,
    usageStatsRepository: UsageStatsRepository,
    colors: NevenColors
) {
    // Intentar obtener el nombre de la app
    val appName = remember(packageName) {
        try {
            val appInfo = packageManager.getApplicationInfo(packageName, 0)
            packageManager.getApplicationLabel(appInfo).toString()
        } catch (e: Exception) {
            packageName.substringAfterLast(".")
        }
    }
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Indicador
        Text(
            text = "▸",
            style = MaterialTheme.typography.bodyLarge,
            color = colors.accent
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        // Nombre de la app
        Text(
            text = appName,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.bodyLarge,
            fontFamily = NevenFontFamily,
            color = colors.textPrimary
        )
        
        // Tiempo de uso
        Text(
            text = usageStatsRepository.formatUsageTime(usageTime),
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary
        )
    }
}

/**
 * Card completa para Settings
 */
@Composable
fun ScreenTimeSettingsCard(
    colors: NevenColors,
    onClick: () -> Unit
) {
    val cardBg = if (colors.isDark) {
        Color(0xFF1B1B1B).copy(alpha = 0.82f)
    } else {
        Color(0xFFFAF9F6).copy(alpha = 0.9f)
    }
    val borderColor = colors.textSecondary.copy(alpha = 0.12f)
    
    Row(
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
            .clickable(onClick = onClick)
            .padding(20.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "§ ${stringResource(R.string.settings_screen_time)}",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = stringResource(R.string.settings_screen_time_desc),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary
            )
        }
        
        Text(
            text = "→",
            style = MaterialTheme.typography.titleLarge,
            color = colors.textSecondary
        )
    }
}
