package com.neven.launcher.data

import android.app.AppOpsManager
import android.app.usage.UsageStats
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Process
import android.provider.Settings
import java.util.Calendar

/**
 * Repositorio para gestionar estadísticas de uso de apps (Screen Time).
 * 
 * Funcionalidades:
 * - Obtener tiempo de uso por app (hoy, semana)
 * - Verificar/solicitar permiso PACKAGE_USAGE_STATS
 */
class UsageStatsRepository(private val context: Context) {
    
    companion object {
        @Volatile
        private var instance: UsageStatsRepository? = null
        
        fun getInstance(context: Context): UsageStatsRepository {
            return instance ?: synchronized(this) {
                instance ?: UsageStatsRepository(context.applicationContext).also {
                    instance = it
                }
            }
        }
    }
    
    private val usageStatsManager: UsageStatsManager? by lazy {
        context.getSystemService(Context.USAGE_STATS_SERVICE) as? UsageStatsManager
    }
    
    // ═══════════════════════════════════════════════════════════════
    // VERIFICACIÓN DE PERMISOS
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Verifica si el permiso de estadísticas de uso está otorgado
     */
    fun hasUsageStatsPermission(): Boolean {
        val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as? AppOpsManager
            ?: return false
        
        val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            appOps.unsafeCheckOpNoThrow(
                AppOpsManager.OPSTR_GET_USAGE_STATS,
                Process.myUid(),
                context.packageName
            )
        } else {
            @Suppress("DEPRECATION")
            appOps.checkOpNoThrow(
                AppOpsManager.OPSTR_GET_USAGE_STATS,
                Process.myUid(),
                context.packageName
            )
        }
        
        return mode == AppOpsManager.MODE_ALLOWED
    }
    
    /**
     * Crea un intent para abrir la pantalla de permisos de uso
     */
    fun getUsageStatsSettingsIntent(): Intent {
        return Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
    }
    
    // ═══════════════════════════════════════════════════════════════
    // ESTADÍSTICAS DE USO - HOY
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Obtiene las estadísticas de uso de hoy
     * @return Mapa de packageName a tiempo de uso en milisegundos
     */
    fun getTodayUsageStats(): Map<String, Long> {
        if (!hasUsageStatsPermission()) {
            return emptyMap()
        }
        
        val calendar = Calendar.getInstance()
        val endTime = calendar.timeInMillis
        
        calendar.set(Calendar.HOUR_OF_DAY, 0)
        calendar.set(Calendar.MINUTE, 0)
        calendar.set(Calendar.SECOND, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        val startTime = calendar.timeInMillis
        
        return getUsageStatsBetween(startTime, endTime)
    }
    
    // ═══════════════════════════════════════════════════════════════
    // ESTADÍSTICAS DE USO - SEMANA
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Obtiene las estadísticas de uso de la última semana
     * @return Mapa de packageName a tiempo de uso en milisegundos
     */
    fun getWeekUsageStats(): Map<String, Long> {
        if (!hasUsageStatsPermission()) {
            return emptyMap()
        }
        
        val calendar = Calendar.getInstance()
        val endTime = calendar.timeInMillis
        
        calendar.add(Calendar.DAY_OF_YEAR, -7)
        calendar.set(Calendar.HOUR_OF_DAY, 0)
        calendar.set(Calendar.MINUTE, 0)
        calendar.set(Calendar.SECOND, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        val startTime = calendar.timeInMillis
        
        return getUsageStatsBetween(startTime, endTime)
    }
    
    // ═══════════════════════════════════════════════════════════════
    // ESTADÍSTICAS DE USO - RANGO PERSONALIZADO
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Obtiene estadísticas de uso entre dos timestamps
     */
    private fun getUsageStatsBetween(startTime: Long, endTime: Long): Map<String, Long> {
        val statsManager = usageStatsManager ?: return emptyMap()
        
        val usageStatsList: List<UsageStats> = statsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startTime,
            endTime
        ) ?: return emptyMap()
        
        // Agrupar por package y sumar tiempo
        return usageStatsList
            .filter { it.totalTimeInForeground > 0 }
            .groupBy { it.packageName }
            .mapValues { (_, stats) ->
                stats.sumOf { it.totalTimeInForeground }
            }
            .toList()
            .sortedByDescending { it.second }
            .toMap()
    }
    
    // ═══════════════════════════════════════════════════════════════
    // UTILIDADES
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Formatea milisegundos a string legible (e.g., "2h 30m", "45m")
     */
    fun formatUsageTime(milliseconds: Long): String {
        val totalMinutes = milliseconds / 60000
        val hours = totalMinutes / 60
        val minutes = totalMinutes % 60
        
        return when {
            hours > 0 && minutes > 0 -> "${hours}h ${minutes}m"
            hours > 0 -> "${hours}h"
            minutes > 0 -> "${minutes}m"
            else -> "<1m"
        }
    }
    
    /**
     * Obtiene el tiempo de uso total de hoy en milisegundos
     */
    fun getTotalUsageToday(): Long {
        return getTodayUsageStats().values.sum()
    }
    
    /**
     * Obtiene el tiempo de uso total de la semana en milisegundos
     */
    fun getTotalUsageWeek(): Long {
        return getWeekUsageStats().values.sum()
    }
    
    /**
     * Obtiene las N apps más usadas hoy
     */
    fun getTopAppsToday(limit: Int = 5): List<Pair<String, Long>> {
        return getTodayUsageStats()
            .toList()
            .sortedByDescending { it.second }
            .take(limit)
    }
    
    /**
     * Obtiene las N apps más usadas esta semana
     */
    fun getTopAppsWeek(limit: Int = 5): List<Pair<String, Long>> {
        return getWeekUsageStats()
            .toList()
            .sortedByDescending { it.second }
            .take(limit)
    }
}
