package com.neven.launcher.ui.settings

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.graphics.toColorInt
import com.neven.launcher.data.StickyNoteColor
import com.neven.launcher.data.StickyNoteRepository
import com.neven.launcher.data.StickyNoteSize
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.launch

/**
 * Pantalla de configuración de Notas Adhesivas (Post-its)
 * Diseño consistente con el resto de pantallas de NEVEN
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NotesSettingsScreen(
    colors: NevenColors,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { StickyNoteRepository.getInstance(context) }
    
    val defaultColor by repository.defaultColorFlow.collectAsState(initial = StickyNoteColor.YELLOW)
    val defaultSize by repository.defaultSizeFlow.collectAsState(initial = StickyNoteSize.MEDIUM)
    val maxNotesPerPage by repository.maxNotesPerPageFlow.collectAsState(initial = 10)
    val notesEnabled by repository.notesEnabledFlow.collectAsState(initial = true)
    val notesOpacity by repository.notesOpacityFlow.collectAsState(initial = 0.9f)
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Notas Adhesivas",
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.Default.ArrowBack,
                            contentDescription = "Volver",
                            tint = colors.textPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.Transparent
                )
            )
        },
        containerColor = Color.Transparent
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp)
        ) {
            // Toggle Principal - Habilitar/Deshabilitar notas
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                border = BorderStroke(
                    1.dp,
                    if (notesEnabled) colors.accent else colors.textSecondary.copy(alpha = 0.3f)
                )
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable {
                            scope.launch { repository.setNotesEnabled(!notesEnabled) }
                        }
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Notas Adhesivas",
                            style = MaterialTheme.typography.titleMedium,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Bold,
                            color = colors.textPrimary
                        )
                        Text(
                            text = if (notesEnabled) "Habilitadas en todas las páginas" else "Deshabilitadas",
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = NevenFontFamily,
                            color = colors.textSecondary
                        )
                    }
                    
                    Switch(
                        checked = notesEnabled,
                        onCheckedChange = { enabled ->
                            scope.launch { repository.setNotesEnabled(enabled) }
                        },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = colors.accent,
                            checkedTrackColor = colors.accent.copy(alpha = 0.3f),
                            uncheckedThumbColor = colors.textSecondary,
                            uncheckedTrackColor = colors.textSecondary.copy(alpha = 0.2f)
                        )
                    )
                }
            }
            
            if (!notesEnabled) {
                Spacer(modifier = Modifier.height(16.dp))
                
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                    border = BorderStroke(1.dp, colors.textSecondary.copy(alpha = 0.3f))
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "ℹ",
                            style = MaterialTheme.typography.titleMedium,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Bold,
                            color = colors.textSecondary,
                            modifier = Modifier.padding(end = 12.dp)
                        )
                        Text(
                            text = "Las notas no aparecerán hasta que las habilites nuevamente. Tus notas existentes se conservan.",
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = NevenFontFamily,
                            color = colors.textSecondary
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(32.dp))
                return@Column
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Sección: Transparencia
            Text(
                text = "Transparencia",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            Text(
                text = "Opacidad de las notas: ${(notesOpacity * 100).toInt()}%",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "10%",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
                
                Slider(
                    value = notesOpacity,
                    onValueChange = { newValue ->
                        scope.launch { repository.setNotesOpacity(newValue) }
                    },
                    valueRange = 0.1f..1.0f,
                    modifier = Modifier
                        .weight(1f)
                        .padding(horizontal = 8.dp),
                    colors = SliderDefaults.colors(
                        thumbColor = colors.accent,
                        activeTrackColor = colors.accent
                    )
                )
                
                Text(
                    text = "100%",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
            }
            
            // Preview de transparencia - nota adhesiva de muestra
            Spacer(modifier = Modifier.height(12.dp))
            
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp)
                    .clip(RoundedCornerShape(4.dp))
                    .background(
                        Color(defaultColor.hex.toColorInt()).copy(alpha = notesOpacity)
                    )
                    .border(
                        1.dp,
                        Color(0xFF2D2D2D).copy(alpha = 0.3f),
                        RoundedCornerShape(4.dp)
                    )
                    .padding(12.dp)
            ) {
                Column {
                    Text(
                        text = "Nota de ejemplo",
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF2D2D2D),
                        style = MaterialTheme.typography.titleSmall
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Así se verán tus notas adhesivas con ${(notesOpacity * 100).toInt()}% de opacidad.",
                        fontFamily = NevenFontFamily,
                        color = Color(0xFF2D2D2D).copy(alpha = 0.8f),
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Sección: Color por defecto
            Text(
                text = "Color por defecto",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            Text(
                text = "Color inicial para nuevas notas",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(StickyNoteColor.entries) { color ->
                    ColorOptionItem(
                        color = color,
                        isSelected = color == defaultColor,
                        accentColor = colors.accent,
                        onClick = {
                            scope.launch { repository.setDefaultColor(color) }
                        }
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Sección: Tamaño por defecto
            Text(
                text = "Tamaño por defecto",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            Text(
                text = "Tamaño inicial para nuevas notas",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            StickyNoteSize.entries.forEach { size ->
                SizeOptionItem(
                    size = size,
                    isSelected = size == defaultSize,
                    colors = colors,
                    onClick = {
                        scope.launch { repository.setDefaultSize(size) }
                    }
                )
                Spacer(modifier = Modifier.height(8.dp))
            }
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Sección: Máximo de notas
            Text(
                text = "Máximo de notas por página",
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            Text(
                text = "Límite: $maxNotesPerPage notas",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "1",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
                
                Slider(
                    value = maxNotesPerPage.toFloat(),
                    onValueChange = { newValue ->
                        scope.launch { repository.setMaxNotesPerPage(newValue.toInt()) }
                    },
                    valueRange = 1f..20f,
                    steps = 18,
                    modifier = Modifier
                        .weight(1f)
                        .padding(horizontal = 8.dp),
                    colors = SliderDefaults.colors(
                        thumbColor = colors.accent,
                        activeTrackColor = colors.accent
                    )
                )
                
                Text(
                    text = "20",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
            }
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Info de uso
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                border = BorderStroke(1.dp, colors.accent.copy(alpha = 0.5f))
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Cómo usar las notas",
                        style = MaterialTheme.typography.titleSmall,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.textPrimary
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    val instructions = listOf(
                        "Mantén presionado en cualquier página para crear una nota",
                        "Arrastra las notas para moverlas",
                        "Toca una nota para editarla",
                        "Soporta Markdown y ecuaciones LaTeX"
                    )
                    
                    instructions.forEach { instruction ->
                        Row(
                            modifier = Modifier.padding(vertical = 4.dp)
                        ) {
                            Text(
                                text = "•",
                                fontFamily = NevenFontFamily,
                                color = colors.accent,
                                modifier = Modifier.padding(end = 8.dp)
                            )
                            Text(
                                text = instruction,
                                style = MaterialTheme.typography.bodySmall,
                                fontFamily = NevenFontFamily,
                                color = colors.textSecondary
                            )
                        }
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

/**
 * Item de selección de color - círculo con borde
 */
@Composable
private fun ColorOptionItem(
    color: StickyNoteColor,
    isSelected: Boolean,
    accentColor: Color,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.clickable { onClick() }
    ) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(Color(color.hex.toColorInt()))
                .border(
                    width = if (isSelected) 3.dp else 1.dp,
                    color = if (isSelected) accentColor else Color.Gray.copy(alpha = 0.3f),
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            if (isSelected) {
                Icon(
                    imageVector = Icons.Default.Check,
                    contentDescription = "Seleccionado",
                    tint = Color(0xFF2D2D2D),
                    modifier = Modifier.size(24.dp)
                )
            }
        }
        
        Spacer(modifier = Modifier.height(4.dp))
        
        Text(
            text = color.displayName,
            style = MaterialTheme.typography.labelSmall,
            fontFamily = NevenFontFamily,
            color = if (isSelected) accentColor else Color.Gray
        )
    }
}

/**
 * Item de selección de tamaño - Card con solo borde
 */
@Composable
private fun SizeOptionItem(
    size: StickyNoteSize,
    isSelected: Boolean,
    colors: NevenColors,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        border = BorderStroke(
            width = if (isSelected) 2.dp else 1.dp,
            color = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.3f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text(
                    text = size.displayName,
                    style = MaterialTheme.typography.bodyLarge,
                    fontFamily = NevenFontFamily,
                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                    color = if (isSelected) colors.textPrimary else colors.textSecondary
                )
                Text(
                    text = "${size.widthDp} x ${size.heightDp} dp",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
            }
            
            // Preview del tamaño
            Box(
                modifier = Modifier
                    .size(
                        width = (size.widthDp / 4).dp,
                        height = (size.heightDp / 4).dp
                    )
                    .clip(RoundedCornerShape(2.dp))
                    .background(Color(StickyNoteColor.YELLOW.hex.toColorInt()))
                    .border(1.dp, Color.Gray.copy(alpha = 0.3f), RoundedCornerShape(2.dp))
            )
        }
    }
}
