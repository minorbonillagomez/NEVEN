package com.neven.launcher.ui.settings

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.mlkit.genai.common.FeatureStatus
import com.google.mlkit.genai.summarization.*
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.rememberNevenColors
import kotlinx.coroutines.launch
import kotlinx.coroutines.guava.await

/**
 * Pantalla de diagnóstico de IA para NEVEN
 * 
 * Sigue el diseño científico/académico de NEVEN:
 * - Header con símbolo Ψ (psi - mente/inteligencia)
 * - Lista de diagnósticos con estados
 * - Prueba de inferencia
 */
@Composable
fun AIDiagnosticsScreen(
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val colors = rememberNevenColors()
    
    // Estados del diagnóstico
    var aiCoreAvailable by remember { mutableStateOf<Boolean?>(null) }
    var modelName by remember { mutableStateOf<String?>(null) }
    var summarizationStatus by remember { mutableStateOf<String>("Verificando...") }
    var proofreadingStatus by remember { mutableStateOf<String>("Verificando...") }
    var testResult by remember { mutableStateOf<String?>(null) }
    var isTestRunning by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    
    // Ejecutar diagnóstico al iniciar
    LaunchedEffect(Unit) {
        try {
            checkAICapabilities(
                context = context,
                onAiCoreStatus = { available -> aiCoreAvailable = available },
                onModelName = { name -> modelName = name },
                onSummarizationStatus = { status -> summarizationStatus = status },
                onProofreadingStatus = { status -> proofreadingStatus = status },
                onError = { error -> errorMessage = error }
            )
        } catch (e: Exception) {
            errorMessage = "Error durante diagnóstico: ${e.message}"
        }
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
    ) {
        // ═══════════════════════════════════════════════════════════════
        // HEADER - Mismo estilo que otras pantallas de Settings
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
                    .clickable { onNavigateBack() }
                    .padding(8.dp),
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            // Símbolo científico Ψ (psi - mente/inteligencia)
            Text(
                text = "\u03A8",
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Text(
                text = "Inteligencia Local",
                style = MaterialTheme.typography.headlineMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
        }
        
        HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.15f))
        
        // ═══════════════════════════════════════════════════════════════
        // CONTENIDO - Scrollable con padding consistente
        // ═══════════════════════════════════════════════════════════════
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Descripción introductoria
            Text(
                text = "NEVEN utiliza Gemini Nano / Gemma 4 para procesar " +
                       "información 100% localmente en tu dispositivo.",
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary,
                lineHeight = 22.sp
            )
            
            HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
            
            // ═══════════════════════════════════════════════════════════
            // DIAGNÓSTICOS
            // ═══════════════════════════════════════════════════════════
            
            // AICore
            DiagnosticItem(
                symbol = "◉",
                title = "Android AICore",
                status = when (aiCoreAvailable) {
                    true -> "Disponible"
                    false -> "No disponible"
                    null -> "Verificando..."
                },
                statusColor = when (aiCoreAvailable) {
                    true -> Color(0xFF4CAF50)
                    false -> Color(0xFFFF5252)
                    null -> colors.textSecondary
                },
                isLoading = aiCoreAvailable == null,
                colors = colors
            )
            
            // Modelo de IA
            DiagnosticItem(
                symbol = "◈",
                title = "Modelo de IA",
                status = modelName ?: "Detectando...",
                statusColor = when {
                    modelName == null -> colors.textSecondary
                    modelName?.contains("gemma-4") == true -> Color(0xFF4CAF50)
                    modelName?.contains("v4") == true -> Color(0xFF4CAF50)
                    modelName?.contains("nano") == true -> Color(0xFFFFC107)
                    else -> colors.textSecondary
                },
                subtitle = when {
                    modelName?.contains("gemma-4") == true -> "Gemma 4 — Modelo más reciente"
                    modelName?.contains("v4") == true -> "Nano v4 — Versión actualizada"
                    modelName?.contains("nano-v3") == true -> "Considera activar Gemma 4"
                    modelName?.contains("nano") == true -> "Gemini Nano detectado"
                    else -> null
                },
                isLoading = modelName == null,
                colors = colors
            )
            
            // API de Resúmenes
            DiagnosticItem(
                symbol = "∑",
                title = "API de Resúmenes",
                status = when (summarizationStatus) {
                    "AVAILABLE" -> "Disponible"
                    "DOWNLOADABLE" -> "Requiere descarga"
                    "DOWNLOADING" -> "Descargando..."
                    "UNAVAILABLE" -> "No disponible"
                    else -> summarizationStatus
                },
                statusColor = when (summarizationStatus) {
                    "AVAILABLE" -> Color(0xFF4CAF50)
                    "DOWNLOADABLE" -> Color(0xFFFFC107)
                    "DOWNLOADING" -> colors.accent
                    "UNAVAILABLE" -> Color(0xFFFF5252)
                    else -> colors.textSecondary
                },
                isLoading = summarizationStatus == "Verificando..." || summarizationStatus == "DOWNLOADING",
                colors = colors
            )
            
            // API de Corrección
            DiagnosticItem(
                symbol = "∂",
                title = "API de Corrección",
                status = when (proofreadingStatus) {
                    "AVAILABLE" -> "Disponible"
                    "DOWNLOADABLE" -> "Requiere descarga"
                    "DOWNLOADING" -> "Descargando..."
                    "UNAVAILABLE" -> "No disponible"
                    else -> proofreadingStatus
                },
                statusColor = when (proofreadingStatus) {
                    "AVAILABLE" -> Color(0xFF4CAF50)
                    "DOWNLOADABLE" -> Color(0xFFFFC107)
                    "DOWNLOADING" -> colors.accent
                    "UNAVAILABLE" -> Color(0xFFFF5252)
                    else -> colors.textSecondary
                },
                isLoading = proofreadingStatus == "Verificando..." || proofreadingStatus == "DOWNLOADING",
                colors = colors
            )
            
            // Error si existe
            errorMessage?.let { error ->
                HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
                
                Text(
                    text = "⚠ $error",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = FontFamily.Monospace,
                    color = Color(0xFFFF6B6B),
                    lineHeight = 18.sp
                )
            }
            
            HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
            
            // ═══════════════════════════════════════════════════════════
            // PRUEBA DE INFERENCIA
            // ═══════════════════════════════════════════════════════════
            
            Text(
                text = "Prueba de Inferencia",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                color = colors.textPrimary
            )
            
            Text(
                text = "Ejecuta una prueba simple para verificar que el modelo " +
                       "puede generar respuestas correctamente.",
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            // Botón de prueba
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center
            ) {
                TextButton(
                    onClick = {
                        scope.launch {
                            isTestRunning = true
                            testResult = null
                            try {
                                testResult = runInferenceTest(context)
                            } catch (e: Exception) {
                                testResult = "Error: ${e.message}"
                            } finally {
                                isTestRunning = false
                            }
                        }
                    },
                    enabled = aiCoreAvailable == true && 
                              summarizationStatus == "AVAILABLE" && 
                              !isTestRunning
                ) {
                    if (isTestRunning) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp,
                            color = colors.accent
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "Procesando...",
                            fontFamily = NevenFontFamily,
                            color = colors.accent
                        )
                    } else {
                        Text(
                            "[ Ejecutar Prueba ]",
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Bold,
                            color = if (aiCoreAvailable == true && summarizationStatus == "AVAILABLE") 
                                colors.accent 
                            else 
                                colors.textSecondary.copy(alpha = 0.5f)
                        )
                    }
                }
            }
            
            // Resultado de la prueba
            testResult?.let { result ->
                val isError = result.startsWith("Error")
                
                Text(
                    text = if (isError) "Error" else "Resultado",
                    style = MaterialTheme.typography.titleSmall,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.SemiBold,
                    color = if (isError) Color(0xFFFF6B6B) else colors.accent
                )
                
                Text(
                    text = result,
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = FontFamily.Monospace,
                    color = if (isError) Color(0xFFFF6B6B) else colors.textPrimary,
                    lineHeight = 18.sp
                )
            }
            
            HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.1f))
            
            // ═══════════════════════════════════════════════════════════
            // DEVELOPER PREVIEW
            // ═══════════════════════════════════════════════════════════
            
            Text(
                text = "Gemma 4 Developer Preview",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                color = colors.textPrimary
            )
            
            Text(
                text = "Para acceder al modelo Gemma 4 (más potente y eficiente), " +
                       "inscríbete en el programa Developer Preview de AICore.",
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center
            ) {
                TextButton(
                    onClick = {
                        val intent = Intent(Intent.ACTION_VIEW).apply {
                            data = Uri.parse("https://developer.android.com/ai/aicore/developer-preview")
                        }
                        context.startActivity(intent)
                    }
                ) {
                    Text(
                        "[ Abrir Developer Preview ]",
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.accent
                    )
                }
            }
            
            // Espaciado inferior + QED
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "\u220E",  // ∎ QED symbol
                    style = MaterialTheme.typography.titleLarge,
                    color = colors.textSecondary.copy(alpha = 0.4f)
                )
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

/**
 * Item de diagnóstico con estilo científico NEVEN
 */
@Composable
private fun DiagnosticItem(
    symbol: String,
    title: String,
    status: String,
    statusColor: Color,
    subtitle: String? = null,
    isLoading: Boolean = false,
    colors: NevenColors
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top
    ) {
        Row(
            modifier = Modifier.weight(1f),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.Top
        ) {
            // Símbolo científico
            Text(
                text = symbol,
                style = MaterialTheme.typography.titleMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
            
            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontFamily = NevenFontFamily,
                    color = colors.textPrimary
                )
                
                subtitle?.let {
                    Text(
                        text = it,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic,
                        color = colors.textSecondary
                    )
                }
            }
        }
        
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(14.dp),
                    strokeWidth = 2.dp,
                    color = colors.accent
                )
            }
            
            Text(
                text = status,
                style = MaterialTheme.typography.bodySmall,
                fontFamily = FontFamily.Monospace,
                color = statusColor
            )
        }
    }
}

/**
 * Verifica las capacidades de IA del dispositivo
 */
private suspend fun checkAICapabilities(
    context: Context,
    onAiCoreStatus: (Boolean) -> Unit,
    onModelName: (String) -> Unit,
    onSummarizationStatus: (String) -> Unit,
    onProofreadingStatus: (String) -> Unit,
    onError: (String) -> Unit
) {
    try {
        // Verificar Summarization API
        val summarizerOptions = SummarizerOptions.builder(context)
            .setInputType(SummarizerOptions.InputType.ARTICLE)
            .setOutputType(SummarizerOptions.OutputType.ONE_BULLET)
            .setLanguage(SummarizerOptions.Language.ENGLISH)
            .build()
        
        val summarizer = Summarization.getClient(summarizerOptions)
        
        try {
            val status = summarizer.checkFeatureStatus().await()
            val statusName = when (status) {
                FeatureStatus.AVAILABLE -> "AVAILABLE"
                FeatureStatus.DOWNLOADABLE -> "DOWNLOADABLE"
                FeatureStatus.DOWNLOADING -> "DOWNLOADING"
                FeatureStatus.UNAVAILABLE -> "UNAVAILABLE"
                else -> "UNKNOWN"
            }
            onSummarizationStatus(statusName)
            
            // Si está disponible, AICore está funcionando
            when (status) {
                FeatureStatus.AVAILABLE,
                FeatureStatus.DOWNLOADABLE,
                FeatureStatus.DOWNLOADING -> onAiCoreStatus(true)
                else -> onAiCoreStatus(false)
            }
            
            // Intentar obtener el nombre del modelo base
            try {
                val modelNameResult = summarizer.getBaseModelName().await()
                onModelName(modelNameResult ?: "Desconocido")
            } catch (e: Exception) {
                onModelName("No detectado")
            }
            
        } catch (e: Exception) {
            onSummarizationStatus("Error: ${e.message?.take(30)}")
            onAiCoreStatus(false)
        } finally {
            summarizer.close()
        }
        
        // Marcar proofreading como pendiente (depende de AICore)
        onProofreadingStatus("Pendiente")
        
    } catch (e: Exception) {
        onError("Error general: ${e.message}")
        onAiCoreStatus(false)
    }
}

/**
 * Ejecuta una prueba de inferencia con el modelo local
 */
private suspend fun runInferenceTest(context: Context): String {
    val testArticle = """
        The Android operating system has revolutionized mobile computing since its 
        initial release in 2008. Developed by Google, Android is now the world's 
        most popular mobile operating system, running on billions of devices worldwide. 
        The platform is known for its open-source nature, extensive customization options, 
        and vast ecosystem of applications available through the Google Play Store.
        
        Recent versions of Android have introduced significant improvements in privacy, 
        security, and artificial intelligence capabilities. Android 14 and beyond 
        include on-device AI processing through the AICore system service, enabling 
        features like smart text prediction, image recognition, and natural language 
        processing without sending data to the cloud.
    """.trimIndent()
    
    val summarizerOptions = SummarizerOptions.builder(context)
        .setInputType(SummarizerOptions.InputType.ARTICLE)
        .setOutputType(SummarizerOptions.OutputType.ONE_BULLET)
        .setLanguage(SummarizerOptions.Language.ENGLISH)
        .build()
    
    val summarizer = Summarization.getClient(summarizerOptions)
    
    return try {
        val status = summarizer.checkFeatureStatus().await()
        
        if (status != FeatureStatus.AVAILABLE) {
            return "El modelo no está disponible (status: $status). " +
                   "Es posible que necesite descargarse primero."
        }
        
        val request = SummarizationRequest.builder(testArticle).build()
        val result = summarizer.runInference(request).await()
        
        // Obtener el texto del resumen del resultado
        val summaryText = result.getSummary()
        "✓ Inferencia exitosa!\n\nResumen generado:\n$summaryText"
        
    } catch (e: Exception) {
        "Error durante inferencia: ${e.message}"
    } finally {
        summarizer.close()
    }
}
