package com.neven.launcher.ui.audiobook

import android.content.Context
import android.content.Intent
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.neven.launcher.data.audiobook.Audiobook
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.rememberNevenColors
import java.io.File

/**
 * Pantalla para compartir un fragmento del audiolibro como MP3.
 * Permite seleccionar intervalo de tiempo (10s - 3min).
 */
@Composable
fun ShareFragmentScreen(
    audiobook: Audiobook,
    currentPositionMs: Long,
    totalDurationMs: Long,
    shareState: ShareFragmentState,
    onStartTimeChange: (Long) -> Unit,
    onEndTimeChange: (Long) -> Unit,
    onPreview: () -> Unit,
    onShare: (startMs: Long, endMs: Long, includeTitle: Boolean, includeCover: Boolean, note: String?) -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier
) {
    val colors = rememberNevenColors()
    val context = LocalContext.current
    
    // Estado local
    var startTimeMs by remember { mutableStateOf(currentPositionMs) }
    var endTimeMs by remember { mutableStateOf((currentPositionMs + 30_000).coerceAtMost(totalDurationMs)) }
    var includeTitle by remember { mutableStateOf(true) }
    var includeCover by remember { mutableStateOf(true) }
    var noteText by remember { mutableStateOf("") }
    
    val durationMs = endTimeMs - startTimeMs
    val isValidDuration = durationMs in 10_000..180_000
    
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(colors.background)
            .padding(24.dp)
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "<<",
                style = MaterialTheme.typography.titleMedium,
                color = colors.textSecondary,
                modifier = Modifier.clickable { onCancel() }
            )
            
            Text(
                text = "Compartir Fragmento",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.width(24.dp))
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Info del libro
        Text(
            text = audiobook.title,
            style = MaterialTheme.typography.titleLarge,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.Bold,
            color = colors.textPrimary
        )
        
        Text(
            text = audiobook.author,
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        // Selector de intervalo
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = colors.textSecondary.copy(alpha = 0.05f)
            ),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "Selecciona el intervalo:",
                    style = MaterialTheme.typography.titleSmall,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = colors.textPrimary
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Tiempo de inicio
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Inicio:",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                    
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = formatTime(startTimeMs),
                            style = MaterialTheme.typography.bodyLarge,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Medium,
                            color = colors.textPrimary
                        )
                        
                        Spacer(modifier = Modifier.width(8.dp))
                        
                        TextButton(onClick = { startTimeMs = currentPositionMs }) {
                            Text(
                                text = "[Usar actual]",
                                style = MaterialTheme.typography.labelMedium,
                                fontFamily = NevenFontFamily,
                                color = colors.accent
                            )
                        }
                    }
                }
                
                // Slider de inicio
                Slider(
                    value = startTimeMs.toFloat() / totalDurationMs.toFloat(),
                    onValueChange = { value ->
                        startTimeMs = (value * totalDurationMs).toLong()
                        if (endTimeMs <= startTimeMs) {
                            endTimeMs = (startTimeMs + 30_000).coerceAtMost(totalDurationMs)
                        }
                    },
                    colors = SliderDefaults.colors(
                        thumbColor = colors.accent,
                        activeTrackColor = colors.accent
                    )
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Tiempo de fin
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Fin:",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                    
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = formatTime(endTimeMs),
                            style = MaterialTheme.typography.bodyLarge,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Medium,
                            color = colors.textPrimary
                        )
                        
                        Spacer(modifier = Modifier.width(8.dp))
                        
                        // Botones rapidos
                        TextButton(onClick = { 
                            endTimeMs = (startTimeMs + 30_000).coerceAtMost(totalDurationMs)
                        }) {
                            Text("+30s", fontFamily = NevenFontFamily, color = colors.accent)
                        }
                        
                        TextButton(onClick = { 
                            endTimeMs = (startTimeMs + 60_000).coerceAtMost(totalDurationMs)
                        }) {
                            Text("+1m", fontFamily = NevenFontFamily, color = colors.accent)
                        }
                    }
                }
                
                // Slider de fin
                Slider(
                    value = endTimeMs.toFloat() / totalDurationMs.toFloat(),
                    onValueChange = { value ->
                        val newEnd = (value * totalDurationMs).toLong()
                        if (newEnd > startTimeMs) {
                            endTimeMs = newEnd
                        }
                    },
                    colors = SliderDefaults.colors(
                        thumbColor = colors.accent,
                        activeTrackColor = colors.accent
                    )
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // Duracion resultante
                val durationColor = if (isValidDuration) colors.accent else colors.hourColor
                Text(
                    text = "Duracion: ${formatTime(durationMs)}",
                    style = MaterialTheme.typography.bodyMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = durationColor,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
                
                if (!isValidDuration) {
                    Text(
                        text = if (durationMs < 10_000) "Minimo 10 segundos" else "Maximo 3 minutos",
                        style = MaterialTheme.typography.labelSmall,
                        fontFamily = NevenFontFamily,
                        color = colors.hourColor,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Opciones
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = colors.textSecondary.copy(alpha = 0.05f)
            ),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "Incluir:",
                    style = MaterialTheme.typography.titleSmall,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium,
                    color = colors.textPrimary
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { includeTitle = !includeTitle }
                        .padding(vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Checkbox(
                        checked = includeTitle,
                        onCheckedChange = { includeTitle = it },
                        colors = CheckboxDefaults.colors(
                            checkedColor = colors.accent
                        )
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Titulo y autor",
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                }
                
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { includeCover = !includeCover }
                        .padding(vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Checkbox(
                        checked = includeCover,
                        onCheckedChange = { includeCover = it },
                        colors = CheckboxDefaults.colors(
                            checkedColor = colors.accent
                        )
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Portada como caratula",
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // Nota opcional
                OutlinedTextField(
                    value = noteText,
                    onValueChange = { noteText = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = {
                        Text(
                            text = "Nota (opcional)",
                            fontFamily = NevenFontFamily
                        )
                    },
                    placeholder = {
                        Text(
                            text = "Ej: Esta parte es muy interesante...",
                            fontFamily = NevenFontFamily,
                            fontStyle = FontStyle.Italic
                        )
                    },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = colors.accent
                    ),
                    maxLines = 2
                )
            }
        }
        
        Spacer(modifier = Modifier.weight(1f))
        
        // Botones de accion
        when (shareState) {
            is ShareFragmentState.Idle,
            is ShareFragmentState.Preparing -> {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    OutlinedButton(
                        onClick = onPreview,
                        modifier = Modifier.weight(1f),
                        enabled = isValidDuration
                    ) {
                        Text(
                            text = "[>] Vista previa",
                            fontFamily = NevenFontFamily
                        )
                    }
                    
                    Button(
                        onClick = {
                            onShare(
                                startTimeMs,
                                endTimeMs,
                                includeTitle,
                                includeCover,
                                noteText.ifBlank { null }
                            )
                        },
                        modifier = Modifier.weight(1f),
                        enabled = isValidDuration,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = colors.accent
                        )
                    ) {
                        Text(
                            text = "Compartir .mp3",
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            }
            
            is ShareFragmentState.Processing -> {
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator(color = colors.accent)
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Generando fragmento...",
                            fontFamily = NevenFontFamily,
                            color = colors.textSecondary
                        )
                    }
                }
            }
            
            is ShareFragmentState.Ready -> {
                LaunchedEffect(shareState.file) {
                    shareFile(context, shareState.file, audiobook.title)
                }
                
                Text(
                    text = "Fragmento listo para compartir",
                    fontFamily = NevenFontFamily,
                    color = colors.accent,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
            }
            
            is ShareFragmentState.Error -> {
                Text(
                    text = "Error: ${shareState.message}",
                    fontFamily = NevenFontFamily,
                    color = colors.hourColor,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}

private fun shareFile(context: Context, file: File, title: String) {
    val uri = FileProvider.getUriForFile(
        context,
        "${context.packageName}.fileprovider",
        file
    )
    
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "audio/mpeg"
        putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_SUBJECT, "Fragmento de: $title")
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    
    context.startActivity(Intent.createChooser(intent, "Compartir fragmento"))
}

private fun formatTime(ms: Long): String {
    if (ms <= 0) return "0:00"
    
    val totalSeconds = ms / 1000
    val hours = totalSeconds / 3600
    val minutes = (totalSeconds % 3600) / 60
    val seconds = totalSeconds % 60
    
    return if (hours > 0) {
        String.format("%d:%02d:%02d", hours, minutes, seconds)
    } else {
        String.format("%d:%02d", minutes, seconds)
    }
}
