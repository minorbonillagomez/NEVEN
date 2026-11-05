package com.neven.launcher.ui.audiobook

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import com.neven.launcher.data.audiobook.Audiobook
import com.neven.launcher.ui.theme.NevenFontFamily
import com.neven.launcher.ui.theme.rememberNevenColors
import java.io.File

/**
 * Pantalla de biblioteca de audiolibros.
 * Muestra libros en progreso y completados.
 */
@Composable
fun AudiobookLibraryScreen(
    inProgressBooks: List<Audiobook>,
    completedBooks: List<Audiobook>,
    onBookClick: (Audiobook) -> Unit,
    onImportClick: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    val colors = rememberNevenColors()
    
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
                modifier = Modifier.clickable { onBack() }
            )
            
            Text(
                text = "Biblioteca",
                style = MaterialTheme.typography.headlineMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            
            Text(
                text = "[+]",
                style = MaterialTheme.typography.titleMedium,
                color = colors.accent,
                modifier = Modifier.clickable { onImportClick() }
            )
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            // Seccion: En progreso
            if (inProgressBooks.isNotEmpty()) {
                item {
                    Text(
                        text = "En progreso",
                        style = MaterialTheme.typography.titleMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Medium,
                        color = colors.textPrimary
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        items(inProgressBooks) { book ->
                            AudiobookCard(
                                audiobook = book,
                                onClick = { onBookClick(book) },
                                colors = colors,
                                showProgress = true
                            )
                        }
                    }
                }
            }
            
            // Seccion: Completados
            if (completedBooks.isNotEmpty()) {
                item {
                    Text(
                        text = "Completados",
                        style = MaterialTheme.typography.titleMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Medium,
                        color = colors.textPrimary
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        items(completedBooks) { book ->
                            AudiobookCard(
                                audiobook = book,
                                onClick = { onBookClick(book) },
                                colors = colors,
                                showProgress = false
                            )
                        }
                    }
                }
            }
            
            // Estado vacio
            if (inProgressBooks.isEmpty() && completedBooks.isEmpty()) {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 64.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "[  ]",
                                style = MaterialTheme.typography.displayMedium,
                                fontFamily = NevenFontFamily,
                                color = colors.textSecondary.copy(alpha = 0.3f)
                            )
                            
                            Spacer(modifier = Modifier.height(16.dp))
                            
                            Text(
                                text = "No hay audiolibros",
                                style = MaterialTheme.typography.titleMedium,
                                fontFamily = NevenFontFamily,
                                color = colors.textSecondary
                            )
                            
                            Spacer(modifier = Modifier.height(8.dp))
                            
                            Text(
                                text = "Toca [+] para importar un archivo M4B",
                                style = MaterialTheme.typography.bodyMedium,
                                fontFamily = NevenFontFamily,
                                fontStyle = FontStyle.Italic,
                                color = colors.textSecondary.copy(alpha = 0.7f)
                            )
                        }
                    }
                }
            }
            
            // Informacion de transferencia
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = colors.textSecondary.copy(alpha = 0.05f)
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Text(
                            text = "Transferir desde PC",
                            style = MaterialTheme.typography.titleSmall,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Medium,
                            color = colors.textPrimary
                        )
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Text(
                            text = "Usa NEVEM Studio para convertir PDF/EPUB a audiolibro y transferirlo a este dispositivo mediante codigo QR.",
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = NevenFontFamily,
                            color = colors.textSecondary
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun AudiobookCard(
    audiobook: Audiobook,
    onClick: () -> Unit,
    colors: com.neven.launcher.ui.theme.NevenColors,
    showProgress: Boolean,
    modifier: Modifier = Modifier
) {
    val progress = if (audiobook.totalDurationMs > 0) {
        audiobook.lastPositionMs.toFloat() / audiobook.totalDurationMs.toFloat()
    } else 0f
    
    Column(
        modifier = modifier
            .width(140.dp)
            .clickable { onClick() }
    ) {
        // Portada
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(0.7f)
                .clip(RoundedCornerShape(8.dp))
                .border(1.dp, colors.textSecondary.copy(alpha = 0.2f), RoundedCornerShape(8.dp))
        ) {
            if (audiobook.coverPath != null && File(audiobook.coverPath).exists()) {
                Image(
                    painter = rememberAsyncImagePainter(File(audiobook.coverPath)),
                    contentDescription = audiobook.title,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            } else {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(colors.textSecondary.copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = audiobook.title.take(1).uppercase(),
                        style = MaterialTheme.typography.headlineLarge,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
            }
            
            // Barra de progreso
            if (showProgress && progress > 0) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(4.dp)
                        .align(Alignment.BottomCenter)
                        .background(colors.background.copy(alpha = 0.8f))
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(progress)
                            .fillMaxHeight()
                            .background(colors.accent)
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Titulo
        Text(
            text = audiobook.title,
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.Medium,
            color = colors.textPrimary,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis
        )
        
        // Autor
        Text(
            text = audiobook.author,
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
        
        // Duracion restante
        if (showProgress && audiobook.totalDurationMs > 0) {
            val remainingMs = audiobook.totalDurationMs - audiobook.lastPositionMs
            Text(
                text = "${formatDuration(remainingMs)} restante",
                style = MaterialTheme.typography.labelSmall,
                fontFamily = NevenFontFamily,
                color = colors.accent
            )
        }
    }
}

private fun formatDuration(ms: Long): String {
    val totalMinutes = ms / 1000 / 60
    val hours = totalMinutes / 60
    val minutes = totalMinutes % 60
    
    return if (hours > 0) {
        "${hours}h ${minutes}m"
    } else {
        "${minutes}m"
    }
}
