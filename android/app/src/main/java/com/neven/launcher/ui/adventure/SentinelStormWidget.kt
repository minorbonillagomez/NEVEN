package com.neven.launcher.ui.adventure

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.data.sentinel.*
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.launch
import kotlin.math.roundToInt

/**
 * Sentinel Storm Widget
 * 
 * Widget compacto para mostrar el estado barométrico y alertas de tormentas
 * en la página de Aventura
 */
@Composable
fun SentinelStormWidget(
    colors: NevenColors,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val repository = remember { SentinelRepository.getInstance(context) }
    val state by repository.state.collectAsState()
    val scope = rememberCoroutineScope()
    
    // Estado del análisis AI por demanda
    var isAnalyzing by remember { mutableStateOf(false) }
    var aiAnalysisResult by remember { mutableStateOf<AiStormAnalysis?>(null) }
    
    // Iniciar monitoreo al montar
    LaunchedEffect(Unit) {
        if (repository.hasPressureSensor() && !state.isMonitoring) {
            repository.startMonitoring()
        }
    }
    
    // Color de alerta basado en nivel de riesgo
    val alertColor by animateColorAsState(
        targetValue = when (state.riskLevel) {
            StormRiskLevel.LOW -> colors.textSecondary.copy(alpha = 0.5f)
            StormRiskLevel.MODERATE -> Color(0xFFFFB300) // Amarillo
            StormRiskLevel.HIGH -> Color(0xFFFF5722)     // Naranja
            StormRiskLevel.CRITICAL -> Color(0xFFD32F2F) // Rojo
        },
        animationSpec = tween(500),
        label = "alertColor"
    )
    
    // Animación de pulso para alertas críticas
    val pulseAlpha by rememberInfiniteTransition(label = "pulse").animateFloat(
        initialValue = 0.3f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )
    
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(colors.textSecondary.copy(alpha = 0.05f))
            .border(
                width = 1.dp,
                color = if (state.riskLevel != StormRiskLevel.LOW) 
                    alertColor.copy(alpha = if (state.riskLevel == StormRiskLevel.CRITICAL) pulseAlpha else 0.5f)
                else colors.textSecondary.copy(alpha = 0.1f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(16.dp)
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "SENTINEL STORM",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily,
                    letterSpacing = 2.sp,
                    fontWeight = FontWeight.Medium
                ),
                color = colors.textSecondary
            )
            
            // Indicador de modo FSM
            Text(
                text = if (state.fsmMode == FsmMode.STATIONARY) "⊚ ESTACIONARIO" else "↝ EN MARCHA",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily,
                    fontSize = 10.sp
                ),
                color = colors.textSecondary.copy(alpha = 0.7f)
            )
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        if (!repository.hasPressureSensor()) {
            // Sin sensor de presión
            Text(
                text = "Sensor barométrico no disponible",
                style = MaterialTheme.typography.bodySmall.copy(
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic
                ),
                color = colors.textSecondary.copy(alpha = 0.6f)
            )
        } else if (!state.isMonitoring || state.currentPressureHpa == 0f) {
            // Esperando datos
            Text(
                text = "Inicializando sensores...",
                style = MaterialTheme.typography.bodySmall.copy(
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic
                ),
                color = colors.textSecondary.copy(alpha = 0.6f)
            )
        } else {
            // Datos de presión
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                // Presión actual
                Column {
                    Text(
                        text = "PRESIÓN",
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontFamily = NevenFontFamily,
                            fontSize = 10.sp
                        ),
                        color = colors.textSecondary.copy(alpha = 0.7f)
                    )
                    Text(
                        text = "${state.currentPressureHpa.roundToInt()} hPa",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Light
                        ),
                        color = colors.textPrimary
                    )
                    Text(
                        text = "P₀: ${state.normalizedPressureHpa.roundToInt()} hPa",
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontFamily = NevenFontFamily,
                            fontStyle = FontStyle.Italic
                        ),
                        color = colors.textSecondary.copy(alpha = 0.6f)
                    )
                }
                
                // Tendencia 3h
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        text = "TENDENCIA 3H",
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontFamily = NevenFontFamily,
                            fontSize = 10.sp
                        ),
                        color = colors.textSecondary.copy(alpha = 0.7f)
                    )
                    
                    val trendSymbol = when {
                        state.deltaP3h < -0.5f -> "↓"
                        state.deltaP3h > 0.5f -> "↑"
                        else -> "→"
                    }
                    val trendColor = when {
                        state.deltaP3h < -1.5f -> alertColor
                        state.deltaP3h > 1.5f -> colors.accent
                        else -> colors.textPrimary
                    }
                    
                    Text(
                        text = "$trendSymbol ${String.format("%+.1f", state.deltaP3h)} hPa",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Light
                        ),
                        color = trendColor
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Mini gráfico de tendencia (simplificado)
            PressureTrendMiniGraph(
                deltaP = state.deltaP3h,
                colors = colors,
                alertColor = alertColor,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(40.dp)
            )
            
            // Alerta si hay riesgo
            if (state.riskLevel != StormRiskLevel.LOW) {
                Spacer(modifier = Modifier.height(12.dp))
                
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color.Transparent)
                        .border(
                            width = 0.5.dp,
                            color = alertColor.copy(alpha = 0.7f),
                            shape = RoundedCornerShape(8.dp)
                        )
                        .padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = when (state.riskLevel) {
                            StormRiskLevel.MODERATE -> "⚠"
                            StormRiskLevel.HIGH -> "⛈"
                            StormRiskLevel.CRITICAL -> "⚡"
                            else -> ""
                        },
                        fontSize = 20.sp,
                        color = alertColor
                    )
                    
                    Spacer(modifier = Modifier.width(12.dp))
                    
                    Column {
                        Text(
                            text = when (state.hazardType) {
                                HazardType.COLD_FRONT -> "Frente Frío Aproximándose"
                                HazardType.CONVECTIVE_MICROBURST -> "Microrráfaga Convectiva"
                                HazardType.THUNDERSTORM -> "Tormenta Eléctrica Posible"
                                else -> "Cambio Atmosférico Detectado"
                            },
                            style = MaterialTheme.typography.bodyMedium.copy(
                                fontFamily = NevenFontFamily,
                                fontWeight = FontWeight.Medium
                            ),
                            color = alertColor
                        )
                        
                        Text(
                            text = when (state.riskLevel) {
                                StormRiskLevel.MODERATE -> "Monitorear condiciones"
                                StormRiskLevel.HIGH -> "Buscar refugio próximamente"
                                StormRiskLevel.CRITICAL -> "¡Buscar refugio inmediato!"
                                else -> ""
                            },
                            style = MaterialTheme.typography.bodySmall.copy(
                                fontFamily = NevenFontFamily
                            ),
                            color = colors.textPrimary
                        )
                    }
                }
            }
            
            // Botón para solicitar análisis AI por demanda
            Spacer(modifier = Modifier.height(12.dp))
            
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .border(
                        width = 0.5.dp,
                        color = colors.accent.copy(alpha = 0.5f),
                        shape = RoundedCornerShape(8.dp)
                    )
                    .clickable(enabled = !isAnalyzing && state.currentPressureHpa > 0f) {
                        isAnalyzing = true
                        scope.launch {
                            try {
                                val analyzer = SentinelAiAnalyzer(context)
                                val analysis = analyzer.analyzeStormData(state)
                                aiAnalysisResult = analysis
                            } catch (e: Exception) {
                                aiAnalysisResult = AiStormAnalysis(
                                    validEvent = false,
                                    riskLevel = state.riskLevel.name,
                                    hazardType = state.hazardType.name,
                                    actionableAdvice = "Error al analizar: ${e.message?.take(50)}",
                                    timestamp = System.currentTimeMillis()
                                )
                            } finally {
                                isAnalyzing = false
                            }
                        }
                    }
                    .padding(12.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (isAnalyzing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = colors.accent
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Analizando...",
                        style = MaterialTheme.typography.labelMedium.copy(
                            fontFamily = NevenFontFamily
                        ),
                        color = colors.textSecondary
                    )
                } else {
                    Text(
                        text = "✦",
                        fontSize = 14.sp,
                        color = colors.accent
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Interpretar con IA Local",
                        style = MaterialTheme.typography.labelMedium.copy(
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Medium
                        ),
                        color = colors.accent
                    )
                }
            }
            
            // Mostrar resultado del análisis AI si está disponible
            if (aiAnalysisResult != null) {
                Spacer(modifier = Modifier.height(12.dp))
                
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color.Transparent)
                        .border(
                            width = 0.5.dp,
                            color = colors.accent.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(8.dp)
                        )
                        .padding(12.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "✦",
                                fontSize = 14.sp,
                                color = colors.accent
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Análisis IA Local",
                                style = MaterialTheme.typography.labelSmall.copy(
                                    fontFamily = NevenFontFamily,
                                    fontSize = 10.sp,
                                    letterSpacing = 1.sp
                                ),
                                color = colors.textSecondary.copy(alpha = 0.7f)
                            )
                        }
                        
                        // Botón para cerrar
                        Text(
                            text = "✕",
                            modifier = Modifier
                                .clip(RoundedCornerShape(4.dp))
                                .clickable { aiAnalysisResult = null }
                                .padding(4.dp),
                            fontSize = 12.sp,
                            color = colors.textSecondary.copy(alpha = 0.5f)
                        )
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    // Área de texto con scroll
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(max = 120.dp)
                    ) {
                        val scrollState = rememberScrollState()
                        
                        Text(
                            text = aiAnalysisResult!!.actionableAdvice,
                            style = MaterialTheme.typography.bodySmall.copy(
                                fontFamily = NevenFontFamily,
                                lineHeight = 18.sp
                            ),
                            color = colors.textPrimary.copy(alpha = 0.9f),
                            modifier = Modifier.verticalScroll(scrollState)
                        )
                    }
                }
            }
        }
    }
}

/**
 * Mini gráfico de tendencia de presión
 */
@Composable
private fun PressureTrendMiniGraph(
    deltaP: Float,
    colors: NevenColors,
    alertColor: Color,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height
        val centerY = height / 2
        
        // Línea base (presión estable)
        drawLine(
            color = colors.textSecondary.copy(alpha = 0.2f),
            start = Offset(0f, centerY),
            end = Offset(width, centerY),
            strokeWidth = 1.dp.toPx()
        )
        
        // Línea de tendencia
        val endY = centerY - (deltaP * 10).coerceIn(-height / 2 + 4, height / 2 - 4)
        
        val path = Path().apply {
            moveTo(0f, centerY)
            // Curva suave hacia el punto final
            cubicTo(
                width * 0.3f, centerY,
                width * 0.7f, endY,
                width, endY
            )
        }
        
        drawPath(
            path = path,
            color = if (deltaP < -1.5f) alertColor else colors.accent,
            style = Stroke(width = 2.dp.toPx())
        )
        
        // Punto final
        drawCircle(
            color = if (deltaP < -1.5f) alertColor else colors.accent,
            radius = 4.dp.toPx(),
            center = Offset(width, endY)
        )
    }
}
