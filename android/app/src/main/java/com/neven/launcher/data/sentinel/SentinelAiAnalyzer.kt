package com.neven.launcher.data.sentinel

import android.content.Context
import android.util.Log
import com.google.mlkit.genai.common.FeatureStatus
import com.google.mlkit.genai.summarization.*
import kotlinx.coroutines.guava.await

/**
 * Sentinel Storm AI Analyzer
 * 
 * Utiliza Gemini Nano on-device para interpretar datos barométricos
 * y generar recomendaciones claras para el usuario.
 */
class SentinelAiAnalyzer(private val context: Context) {
    
    companion object {
        private const val TAG = "SentinelAiAnalyzer"
    }
    
    /**
     * Analiza el estado actual del SENTINEL STORM y genera una interpretación
     * amigable con recomendaciones accionables.
     * 
     * @param state Estado actual del Sentinel Storm
     * @return AiStormAnalysis con la interpretación o null si no disponible
     */
    suspend fun analyzeStormData(state: SentinelState): AiStormAnalysis? {
        if (state.currentPressureHpa == 0f) {
            Log.d(TAG, "No hay datos de presión para analizar")
            return null
        }
        
        return try {
            // Construir el texto de contexto meteorológico
            val weatherReport = buildWeatherReport(state)
            
            // Configurar summarizer para obtener interpretación concisa
            val summarizerOptions = SummarizerOptions.builder(context)
                .setInputType(SummarizerOptions.InputType.ARTICLE)
                .setOutputType(SummarizerOptions.OutputType.ONE_BULLET)
                .setLanguage(SummarizerOptions.Language.ENGLISH)
                .build()
            
            val summarizer = Summarization.getClient(summarizerOptions)
            
            try {
                val status = summarizer.checkFeatureStatus().await()
                
                if (status != FeatureStatus.AVAILABLE) {
                    Log.w(TAG, "Gemini Nano no disponible: $status")
                    // Fallback a análisis determinístico
                    return createDeterministicAnalysis(state)
                }
                
                val request = SummarizationRequest.builder(weatherReport).build()
                val result = summarizer.runInference(request).await()
                val aiSummary = result.getSummary() ?: ""
                
                Log.d(TAG, "AI Summary: $aiSummary")
                
                // Crear análisis combinado
                AiStormAnalysis(
                    validEvent = state.riskLevel != StormRiskLevel.LOW,
                    riskLevel = state.riskLevel.name,
                    hazardType = state.hazardType.name,
                    actionableAdvice = if (aiSummary.isNotBlank()) {
                        cleanupAiResponse(aiSummary)
                    } else {
                        getDefaultAdvice(state)
                    },
                    timestamp = System.currentTimeMillis()
                )
                
            } finally {
                summarizer.close()
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Error en análisis AI: ${e.message}", e)
            // Fallback a análisis determinístico
            createDeterministicAnalysis(state)
        }
    }
    
    /**
     * Construye un reporte meteorológico estructurado para el modelo AI
     */
    private fun buildWeatherReport(state: SentinelState): String {
        val riskDescription = when (state.riskLevel) {
            StormRiskLevel.LOW -> "sin riesgo detectado"
            StormRiskLevel.MODERATE -> "riesgo moderado - aviso temprano de posible tormenta"
            StormRiskLevel.HIGH -> "riesgo alto - frente de tormenta severa aproximándose"
            StormRiskLevel.CRITICAL -> "riesgo crítico - posible microrráfaga o tormenta inminente"
        }
        
        val hazardDescription = when (state.hazardType) {
            HazardType.NONE -> "condiciones estables"
            HazardType.COLD_FRONT -> "frente frío en aproximación"
            HazardType.CONVECTIVE_MICROBURST -> "microrráfaga convectiva detectada"
            HazardType.THUNDERSTORM -> "tormenta eléctrica posible"
            HazardType.FALSE_POSITIVE -> "posible falso positivo"
        }
        
        val trendDescription = when {
            state.deltaP3h < -2.5f -> "cayendo rápidamente (${state.deltaP3h} hPa en 3h) - indica tormenta severa"
            state.deltaP3h < -1.5f -> "cayendo moderadamente (${state.deltaP3h} hPa en 3h) - posible cambio climático"
            state.deltaP3h < -0.5f -> "cayendo ligeramente (${state.deltaP3h} hPa en 3h)"
            state.deltaP3h > 1.5f -> "subiendo rápidamente (+${state.deltaP3h} hPa en 3h) - mejora del tiempo"
            state.deltaP3h > 0.5f -> "subiendo ligeramente (+${state.deltaP3h} hPa en 3h)"
            else -> "estable (${state.deltaP3h} hPa en 3h)"
        }
        
        val activityContext = if (state.fsmMode == FsmMode.STATIONARY) {
            "El usuario está en reposo o acampando."
        } else {
            "El usuario está en movimiento (trekking/senderismo)."
        }
        
        return """
            REPORTE METEOROLÓGICO SENTINEL STORM
            
            Datos del sensor barométrico:
            - Presión actual: ${state.currentPressureHpa.toInt()} hPa
            - Presión normalizada (nivel del mar): ${state.normalizedPressureHpa.toInt()} hPa
            - Altitud estimada: ${state.altitudeMeters.toInt()} metros
            - Tendencia de presión: $trendDescription
            - Cambio en 45 minutos: ${state.deltaP45min} hPa
            
            Evaluación de riesgo: $riskDescription
            Tipo de amenaza: $hazardDescription
            
            Contexto: $activityContext
            
            Genera un mensaje breve y claro en español para una persona que hace senderismo 
            o actividades al aire libre. El mensaje debe:
            1. Explicar qué significa el cambio de presión
            2. Indicar si hay peligro y de qué tipo
            3. Dar una recomendación concreta de qué hacer
            
            Sé directo y práctico. Máximo 2-3 oraciones.
        """.trimIndent()
    }
    
    /**
     * Limpia y formatea la respuesta del modelo AI
     */
    private fun cleanupAiResponse(response: String): String {
        return response
            .trim()
            .removePrefix("•")
            .removePrefix("-")
            .removePrefix("*")
            .trim()
            .replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
    }
    
    /**
     * Crea un análisis determinístico como fallback
     */
    private fun createDeterministicAnalysis(state: SentinelState): AiStormAnalysis {
        return AiStormAnalysis(
            validEvent = state.riskLevel != StormRiskLevel.LOW,
            riskLevel = state.riskLevel.name,
            hazardType = state.hazardType.name,
            actionableAdvice = getDefaultAdvice(state),
            timestamp = System.currentTimeMillis()
        )
    }
    
    /**
     * Genera consejos por defecto basados en el estado
     */
    private fun getDefaultAdvice(state: SentinelState): String {
        return when (state.riskLevel) {
            StormRiskLevel.LOW -> {
                if (state.deltaP3h > 0.5f) {
                    "Presión estable o subiendo. Condiciones favorables para actividades al aire libre."
                } else if (state.deltaP3h < -0.5f) {
                    "Ligera caída de presión. Condiciones aceptables, pero mantente atento al cielo."
                } else {
                    "Condiciones atmosféricas estables. Buen momento para tu actividad."
                }
            }
            StormRiskLevel.MODERATE -> {
                when (state.hazardType) {
                    HazardType.COLD_FRONT -> 
                        "Un frente frío se aproxima. En las próximas 2-4 horas podrían llegar lluvias o vientos. Considera acortar tu ruta."
                    HazardType.THUNDERSTORM ->
                        "Posible tormenta en formación. Mantente alejado de crestas y zonas altas. Ten identificado un refugio."
                    else ->
                        "Cambio atmosférico detectado. Monitorea las condiciones y ten un plan B."
                }
            }
            StormRiskLevel.HIGH -> {
                when (state.hazardType) {
                    HazardType.COLD_FRONT ->
                        "Frente de tormenta severa aproximándose. Busca refugio sólido en los próximos 30-60 minutos."
                    HazardType.THUNDERSTORM ->
                        "Alta probabilidad de tormenta eléctrica. Evita zonas expuestas, árboles aislados y agua. Busca refugio ahora."
                    else ->
                        "Condiciones deteriorándose rápidamente. Prioriza tu seguridad y busca refugio próximamente."
                }
            }
            StormRiskLevel.CRITICAL -> {
                when (state.hazardType) {
                    HazardType.CONVECTIVE_MICROBURST ->
                        "¡ALERTA! Posible microrráfaga. Vientos muy fuertes y súbitos en minutos. Busca refugio sólido INMEDIATAMENTE."
                    HazardType.THUNDERSTORM ->
                        "¡PELIGRO INMINENTE! Tormenta eléctrica muy probable. Agáchate en zona baja, lejos de objetos metálicos y agua."
                    else ->
                        "¡EMERGENCIA METEOROLÓGICA! Condiciones peligrosas inminentes. Busca refugio inmediato."
                }
            }
        }
    }
}
