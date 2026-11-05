package com.neven.launcher.data.sentinel

import androidx.room.*

/**
 * Sentinel Storm - Modelos de datos para estación barométrica
 * 
 * Sistema de detección de frentes climáticos adversos offline
 */

// ═══════════════════════════════════════════════════════════════════════════
// ENTIDADES DE BASE DE DATOS (ROOM)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Lectura de presión barométrica con normalización
 */
@Entity(tableName = "pressure_readings")
data class PressureReading(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "timestamp") val timestamp: Long,
    @ColumnInfo(name = "raw_pressure_hpa") val rawPressureHpa: Float,
    @ColumnInfo(name = "normalized_pressure_hpa") val normalizedPressureHpa: Float,
    @ColumnInfo(name = "altitude_meters") val altitudeMeters: Float,
    @ColumnInfo(name = "fsm_mode") val fsmMode: String, // STATIONARY o MOVING
    @ColumnInfo(name = "steps_count") val stepsCount: Int
)

/**
 * DAO para lecturas de presión
 */
@Dao
interface PressureReadingDao {
    @Insert
    suspend fun insert(reading: PressureReading): Long
    
    @Query("SELECT * FROM pressure_readings ORDER BY timestamp DESC LIMIT 1")
    suspend fun getLatest(): PressureReading?
    
    @Query("SELECT * FROM pressure_readings WHERE timestamp >= :since ORDER BY timestamp ASC")
    suspend fun getReadingsSince(since: Long): List<PressureReading>
    
    @Query("SELECT * FROM pressure_readings ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getRecentReadings(limit: Int): List<PressureReading>
    
    // Obtener lecturas de las últimas N horas
    @Query("SELECT * FROM pressure_readings WHERE timestamp >= :since ORDER BY timestamp ASC")
    fun getReadingsFlow(since: Long): kotlinx.coroutines.flow.Flow<List<PressureReading>>
    
    // Auto-purgado: eliminar lecturas mayores a 48 horas
    @Query("DELETE FROM pressure_readings WHERE timestamp < :before")
    suspend fun deleteOlderThan(before: Long)
    
    @Query("SELECT COUNT(*) FROM pressure_readings")
    suspend fun getCount(): Int
}

// ═══════════════════════════════════════════════════════════════════════════
// MODELOS DE DOMINIO
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Modo de la FSM (Máquina de Estados Finitos)
 */
enum class FsmMode {
    STATIONARY,  // Campamento/Vivac - Sin movimiento
    MOVING       // Trekking - En desplazamiento
}

/**
 * Nivel de riesgo de tormenta
 */
enum class StormRiskLevel {
    LOW,        // Sin riesgo detectado
    MODERATE,   // Aviso temprano (ΔP₀ ≤ -1.5 hPa en 3h)
    HIGH,       // Frente de tormenta severo (ΔP₀ ≤ -2.5 hPa en 3h)
    CRITICAL    // Microrráfaga/Convección súbita (ΔP₀ ≤ -1.5 hPa en 45min)
}

/**
 * Tipo de amenaza climática
 */
enum class HazardType {
    NONE,
    COLD_FRONT,           // Frente Frío
    CONVECTIVE_MICROBURST,// Microrráfaga Convectiva
    THUNDERSTORM,         // Tormenta Eléctrica
    FALSE_POSITIVE        // Falso Positivo (rebote de satélite, error de sensor)
}

/**
 * Estado actual del Sentinel Storm
 */
data class SentinelState(
    val fsmMode: FsmMode = FsmMode.STATIONARY,
    val currentPressureHpa: Float = 0f,
    val normalizedPressureHpa: Float = 0f,
    val altitudeMeters: Float = 0f,
    val deltaP3h: Float = 0f,        // Cambio de presión en 3 horas
    val deltaP45min: Float = 0f,     // Cambio de presión en 45 minutos
    val riskLevel: StormRiskLevel = StormRiskLevel.LOW,
    val hazardType: HazardType = HazardType.NONE,
    val lastUpdateTimestamp: Long = 0,
    val stepsLast30min: Int = 0,
    val isMonitoring: Boolean = false,
    val aiAnalysis: AiStormAnalysis? = null
)

/**
 * Análisis de IA on-device
 */
data class AiStormAnalysis(
    val validEvent: Boolean,
    val riskLevel: String,
    val hazardType: String,
    val actionableAdvice: String,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * Configuración del Sentinel
 */
data class SentinelConfig(
    val samplingIntervalMinutes: Int = 5,
    val stationaryThresholdSeconds: Int = 600,  // 10 minutos sin movimiento
    val movingStepsThreshold: Int = 40,         // 40 pasos en 2 minutos
    val movingAccelVarianceThreshold: Float = 0.15f, // m/s²
    val alertEarlyWarningHpa: Float = -1.5f,    // ΔP₀ en 3h
    val alertSevereHpa: Float = -2.5f,          // ΔP₀ en 3h
    val alertMicroburstHpa: Float = -1.5f,      // ΔP₀ en 45min
    val enableAiAudit: Boolean = true
)

// ═══════════════════════════════════════════════════════════════════════════
// UTILIDADES DE CÁLCULO
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Fórmula Hipsométrica para normalización de presión a nivel del mar
 * 
 * P₀ = P × (1 - 0.0065×h / 288.15)^(-5.25588)
 * 
 * @param pressureHpa Presión medida en hectopascales
 * @param altitudeMeters Altitud en metros
 * @return Presión normalizada a nivel del mar (hPa)
 */
fun normalizeToSeaLevel(pressureHpa: Float, altitudeMeters: Float): Float {
    val lapseRate = 0.0065 // K/m - Gradiente térmico estándar
    val seaLevelTemp = 288.15 // K - Temperatura estándar a nivel del mar
    val exponent = -5.25588
    
    val factor = 1 - (lapseRate * altitudeMeters) / seaLevelTemp
    return pressureHpa * Math.pow(factor, exponent).toFloat()
}

/**
 * Calcula el cambio de presión entre dos timestamps
 */
fun calculatePressureChange(
    readings: List<PressureReading>,
    currentTime: Long,
    windowMinutes: Int
): Float {
    if (readings.isEmpty()) return 0f
    
    val windowStart = currentTime - (windowMinutes * 60 * 1000L)
    val oldReading = readings.filter { it.timestamp <= windowStart }.maxByOrNull { it.timestamp }
    val currentReading = readings.maxByOrNull { it.timestamp }
    
    return if (oldReading != null && currentReading != null) {
        currentReading.normalizedPressureHpa - oldReading.normalizedPressureHpa
    } else {
        0f
    }
}

/**
 * Evalúa el nivel de riesgo basado en cambios de presión
 */
fun evaluateRiskLevel(deltaP3h: Float, deltaP45min: Float): StormRiskLevel {
    return when {
        deltaP45min <= -1.5f -> StormRiskLevel.CRITICAL  // Microrráfaga
        deltaP3h <= -2.5f -> StormRiskLevel.HIGH         // Tormenta severa
        deltaP3h <= -1.5f -> StormRiskLevel.MODERATE     // Aviso temprano
        else -> StormRiskLevel.LOW
    }
}
