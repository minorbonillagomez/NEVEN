package com.neven.launcher.data.sentinel

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.sqrt

/**
 * Sentinel Storm Repository
 * 
 * Gestiona la lectura de sensores, almacenamiento y análisis
 * de datos barométricos para detección de tormentas
 */
class SentinelRepository private constructor(context: Context) {
    
    companion object {
        private const val TAG = "SentinelRepository"
        private const val HOURS_48_MS = 48 * 60 * 60 * 1000L
        private const val HOURS_24_MS = 24 * 60 * 60 * 1000L
        private const val HOURS_3_MS = 3 * 60 * 60 * 1000L
        private const val MIN_45_MS = 45 * 60 * 1000L
        
        @Volatile
        private var INSTANCE: SentinelRepository? = null
        
        fun getInstance(context: Context): SentinelRepository {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: SentinelRepository(context).also { INSTANCE = it }
            }
        }
    }
    
    private val appContext = context.applicationContext
    private val database = SentinelDatabase.getInstance(appContext)
    private val dao = database.pressureReadingDao()
    private val sensorManager = appContext.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    
    // Scope para corrutinas
    private val repositoryScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    
    // Estado actual del Sentinel
    private val _state = MutableStateFlow(SentinelState())
    val state: StateFlow<SentinelState> = _state.asStateFlow()
    
    // Configuración
    private val _config = MutableStateFlow(SentinelConfig())
    val config: StateFlow<SentinelConfig> = _config.asStateFlow()
    
    // Variables de seguimiento
    private var lastStepCount = 0
    private var stepsInWindow = 0
    private var lastStepTimestamp = 0L
    private var currentAltitude = 0f
    private var fixedAltitude: Float? = null // Altitud fijada en modo estacionario
    private var lastMovementTimestamp = System.currentTimeMillis()
    
    // Listeners de sensores
    private var pressureListener: SensorEventListener? = null
    private var stepListener: SensorEventListener? = null
    private var accelListener: SensorEventListener? = null
    
    // Buffer de presión para media truncada
    private val pressureBuffer = mutableListOf<Float>()
    
    /**
     * Verifica si el dispositivo tiene sensor de presión
     */
    fun hasPressureSensor(): Boolean {
        return sensorManager.getDefaultSensor(Sensor.TYPE_PRESSURE) != null
    }
    
    /**
     * Inicia el monitoreo de sensores
     */
    fun startMonitoring() {
        Log.d(TAG, "Starting Sentinel Storm monitoring")
        
        if (!hasPressureSensor()) {
            Log.w(TAG, "Device does not have pressure sensor")
            return
        }
        
        // Sensor de presión
        val pressureSensor = sensorManager.getDefaultSensor(Sensor.TYPE_PRESSURE)
        pressureListener = object : SensorEventListener {
            override fun onSensorChanged(event: SensorEvent) {
                if (event.sensor.type == Sensor.TYPE_PRESSURE) {
                    onPressureReading(event.values[0])
                }
            }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        sensorManager.registerListener(
            pressureListener,
            pressureSensor,
            SensorManager.SENSOR_DELAY_NORMAL
        )
        
        // Contador de pasos (bajo consumo)
        val stepSensor = sensorManager.getDefaultSensor(Sensor.TYPE_STEP_COUNTER)
        if (stepSensor != null) {
            stepListener = object : SensorEventListener {
                override fun onSensorChanged(event: SensorEvent) {
                    if (event.sensor.type == Sensor.TYPE_STEP_COUNTER) {
                        onStepCount(event.values[0].toInt())
                    }
                }
                override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
            }
            sensorManager.registerListener(
                stepListener,
                stepSensor,
                SensorManager.SENSOR_DELAY_NORMAL
            )
        }
        
        // Acelerómetro para detectar movimiento
        val accelSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        if (accelSensor != null) {
            accelListener = object : SensorEventListener {
                override fun onSensorChanged(event: SensorEvent) {
                    if (event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
                        onAccelerometerReading(event.values)
                    }
                }
                override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
            }
            sensorManager.registerListener(
                accelListener,
                accelSensor,
                SensorManager.SENSOR_DELAY_NORMAL
            )
        }
        
        _state.value = _state.value.copy(isMonitoring = true)
    }
    
    /**
     * Detiene el monitoreo
     */
    fun stopMonitoring() {
        Log.d(TAG, "Stopping Sentinel Storm monitoring")
        
        pressureListener?.let { sensorManager.unregisterListener(it) }
        stepListener?.let { sensorManager.unregisterListener(it) }
        accelListener?.let { sensorManager.unregisterListener(it) }
        
        pressureListener = null
        stepListener = null
        accelListener = null
        
        _state.value = _state.value.copy(isMonitoring = false)
    }
    
    /**
     * Actualiza la altitud desde GPS
     */
    fun updateAltitude(altitudeMeters: Float) {
        currentAltitude = altitudeMeters
        
        // En modo MOVING, actualizar altitud
        // En modo STATIONARY, mantener la altitud fijada
        if (_state.value.fsmMode == FsmMode.MOVING) {
            _state.value = _state.value.copy(altitudeMeters = altitudeMeters)
        }
    }
    
    /**
     * Procesa lectura de presión
     */
    private fun onPressureReading(pressureHpa: Float) {
        // Agregar al buffer para media truncada
        pressureBuffer.add(pressureHpa)
        
        // Cuando tenemos 5 lecturas, calcular media truncada
        if (pressureBuffer.size >= 5) {
            val sorted = pressureBuffer.sorted()
            // Descartar mínimo y máximo, promediar los 3 centrales
            val truncatedMean = sorted.subList(1, sorted.size - 1).average().toFloat()
            pressureBuffer.clear()
            
            repositoryScope.launch {
                processPressureSample(truncatedMean)
            }
        }
    }
    
    /**
     * Procesa muestra de presión (después de media truncada)
     */
    private suspend fun processPressureSample(rawPressure: Float) = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()
        val fsmMode = _state.value.fsmMode
        
        // Usar altitud fijada en modo estacionario, o actual en modo moving
        val altitude = if (fsmMode == FsmMode.STATIONARY) {
            fixedAltitude ?: currentAltitude
        } else {
            currentAltitude
        }
        
        // Normalizar presión a nivel del mar
        val normalizedPressure = normalizeToSeaLevel(rawPressure, altitude)
        
        // Guardar lectura en base de datos
        val reading = PressureReading(
            timestamp = now,
            rawPressureHpa = rawPressure,
            normalizedPressureHpa = normalizedPressure,
            altitudeMeters = altitude,
            fsmMode = fsmMode.name,
            stepsCount = stepsInWindow
        )
        dao.insert(reading)
        
        // Auto-purgado de lecturas antiguas (> 48h)
        dao.deleteOlderThan(now - HOURS_48_MS)
        
        // Obtener lecturas recientes para análisis
        val recentReadings = dao.getReadingsSince(now - HOURS_24_MS)
        
        // Calcular cambios de presión
        val deltaP3h = calculatePressureChange(recentReadings, now, 180) // 3 horas
        val deltaP45min = calculatePressureChange(recentReadings, now, 45)  // 45 minutos
        
        // Evaluar riesgo
        val riskLevel = evaluateRiskLevel(deltaP3h, deltaP45min)
        val hazardType = determineHazardType(riskLevel, deltaP3h, deltaP45min)
        
        // Actualizar estado
        _state.value = _state.value.copy(
            currentPressureHpa = rawPressure,
            normalizedPressureHpa = normalizedPressure,
            altitudeMeters = altitude,
            deltaP3h = deltaP3h,
            deltaP45min = deltaP45min,
            riskLevel = riskLevel,
            hazardType = hazardType,
            lastUpdateTimestamp = now,
            stepsLast30min = stepsInWindow
        )
        
        Log.d(TAG, "Pressure: ${rawPressure}hPa, Normalized: ${normalizedPressure}hPa, " +
                   "ΔP(3h): ${deltaP3h}hPa, Risk: $riskLevel")
    }
    
    /**
     * Determina el tipo de amenaza basado en el nivel de riesgo
     */
    private fun determineHazardType(
        riskLevel: StormRiskLevel,
        deltaP3h: Float,
        deltaP45min: Float
    ): HazardType {
        return when (riskLevel) {
            StormRiskLevel.CRITICAL -> HazardType.CONVECTIVE_MICROBURST
            StormRiskLevel.HIGH -> {
                if (deltaP45min < -0.5f) HazardType.THUNDERSTORM
                else HazardType.COLD_FRONT
            }
            StormRiskLevel.MODERATE -> HazardType.COLD_FRONT
            StormRiskLevel.LOW -> HazardType.NONE
        }
    }
    
    /**
     * Procesa conteo de pasos
     */
    private fun onStepCount(totalSteps: Int) {
        val now = System.currentTimeMillis()
        
        if (lastStepCount > 0) {
            val stepsDelta = totalSteps - lastStepCount
            if (stepsDelta > 0 && stepsDelta < 100) { // Filtrar valores anómalos
                stepsInWindow += stepsDelta
                lastMovementTimestamp = now
            }
        }
        lastStepCount = totalSteps
        
        // Resetear ventana cada 2 minutos
        if (now - lastStepTimestamp > 120_000) {
            evaluateFsmMode()
            stepsInWindow = 0
            lastStepTimestamp = now
        }
    }
    
    /**
     * Procesa lectura de acelerómetro
     */
    private fun onAccelerometerReading(values: FloatArray) {
        // Calcular magnitud RMS
        val magnitude = sqrt(values[0] * values[0] + values[1] * values[1] + values[2] * values[2])
        
        // Si hay movimiento significativo (más de 10.5 m/s² incluyendo gravedad)
        if (magnitude > 10.5f) {
            lastMovementTimestamp = System.currentTimeMillis()
        }
    }
    
    /**
     * Evalúa y actualiza el modo de la FSM
     */
    private fun evaluateFsmMode() {
        val now = System.currentTimeMillis()
        val config = _config.value
        val currentMode = _state.value.fsmMode
        
        val timeSinceMovement = now - lastMovementTimestamp
        val isStationary = timeSinceMovement > config.stationaryThresholdSeconds * 1000L
        val isMoving = stepsInWindow >= config.movingStepsThreshold
        
        val newMode = when {
            isMoving -> FsmMode.MOVING
            isStationary -> FsmMode.STATIONARY
            else -> currentMode
        }
        
        if (newMode != currentMode) {
            Log.d(TAG, "FSM mode changed: $currentMode -> $newMode")
            
            when (newMode) {
                FsmMode.STATIONARY -> {
                    // Fijar altitud actual
                    fixedAltitude = currentAltitude
                    Log.d(TAG, "Altitude fixed at: ${fixedAltitude}m")
                }
                FsmMode.MOVING -> {
                    // Liberar altitud fijada
                    fixedAltitude = null
                }
            }
            
            _state.value = _state.value.copy(fsmMode = newMode)
        }
    }
    
    /**
     * Obtiene el historial de presión para gráficos
     */
    suspend fun getPressureHistory(hours: Int = 24): List<PressureReading> = withContext(Dispatchers.IO) {
        val since = System.currentTimeMillis() - (hours * 60 * 60 * 1000L)
        dao.getReadingsSince(since)
    }
    
    /**
     * Fuerza una lectura inmediata
     */
    fun forceReading() {
        if (pressureBuffer.isNotEmpty()) {
            val avg = pressureBuffer.average().toFloat()
            pressureBuffer.clear()
            repositoryScope.launch {
                processPressureSample(avg)
            }
        }
    }
}
