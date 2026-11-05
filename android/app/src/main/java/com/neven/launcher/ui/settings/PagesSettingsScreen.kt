package com.neven.launcher.ui.settings

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.neven.launcher.R
import com.neven.launcher.data.DefaultPages
import com.neven.launcher.data.PageType
import com.neven.launcher.data.PagesRepository
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.launch

/**
 * Pantalla de configuración de páginas del launcher
 * 
 * Permite activar/desactivar las diferentes páginas:
 * - Glance (calendario + eventos)
 * - Adventure (brújula, altitud, meteorología)
 */
@Composable
fun PagesSettingsScreen(
    colors: NevenColors,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val pagesRepository = remember { PagesRepository.getInstance(context) }
    
    // Observar páginas actuales
    val pages by pagesRepository.pagesFlow.collectAsState(initial = emptyList())
    
    // Estados derivados
    val hasGlance = pages.any { it.type == PageType.GLANCE }
    val hasAdventure = pages.any { it.type == PageType.ADVENTURE }
    val hasAudiobook = pages.any { it.type == PageType.AUDIOBOOK }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
    ) {
        // Header
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
                    fontFamily = FontFamily.Serif
                ),
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            // Símbolo científico ⊞ (suma directa / páginas)
            Text(
                text = "⊞",
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Text(
                text = stringResource(R.string.pages_title),
                style = MaterialTheme.typography.headlineMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
        }
        
        Divider(color = colors.textSecondary.copy(alpha = 0.15f))
        
        // Contenido
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            // Descripción
            Text(
                text = "Configura las páginas disponibles en tu launcher. Desliza horizontalmente desde HOME para acceder a ellas.",
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic
                ),
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // ═══════════════════════════════════════════════════════════════
            // GLANCE PAGE
            // ═══════════════════════════════════════════════════════════════
            PageToggleItem(
                title = stringResource(R.string.pages_glance),
                symbol = "◈",
                description = stringResource(R.string.pages_glance_desc),
                isEnabled = hasGlance,
                onToggle = { enabled ->
                    scope.launch {
                        if (enabled) {
                            // Agregar Glance a la izquierda de HOME
                            pagesRepository.addPageLeft(DefaultPages.getGlanceSetup().first { it.type == PageType.GLANCE })
                        } else {
                            // Eliminar Glance
                            val glancePage = pages.find { it.type == PageType.GLANCE }
                            glancePage?.let { pagesRepository.removePage(it.id) }
                        }
                    }
                },
                colors = colors
            )
            
            Divider(color = colors.textSecondary.copy(alpha = 0.1f))
            
            // ═══════════════════════════════════════════════════════════════
            // ADVENTURE PAGE
            // ═══════════════════════════════════════════════════════════════
            PageToggleItem(
                title = stringResource(R.string.pages_adventure),
                symbol = "⊕",
                description = stringResource(R.string.pages_adventure_desc),
                isEnabled = hasAdventure,
                onToggle = { enabled ->
                    scope.launch {
                        if (enabled) {
                            pagesRepository.addAdventurePage()
                        } else {
                            val adventurePage = pages.find { it.type == PageType.ADVENTURE }
                            adventurePage?.let { pagesRepository.removePage(it.id) }
                        }
                    }
                },
                colors = colors
            )
            
            Divider(color = colors.textSecondary.copy(alpha = 0.1f))
            
            // ═══════════════════════════════════════════════════════════════
            // AUDIOBOOK PAGE
            // ═══════════════════════════════════════════════════════════════
            PageToggleItem(
                title = "Audiolibros",
                symbol = "♪",
                description = "Biblioteca y reproductor de audiolibros M4B con notas y memoria de reproduccion",
                isEnabled = hasAudiobook,
                onToggle = { enabled ->
                    scope.launch {
                        if (enabled) {
                            pagesRepository.addAudiobookPage()
                        } else {
                            val audiobookPage = pages.find { it.type == PageType.AUDIOBOOK }
                            audiobookPage?.let { pagesRepository.removePage(it.id) }
                        }
                    }
                },
                colors = colors
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Nota sobre navegación
            Text(
                text = stringResource(R.string.pages_navigation_note),
                style = MaterialTheme.typography.bodySmall.copy(
                    fontFamily = NevenFontFamily
                ),
                color = colors.textSecondary.copy(alpha = 0.7f)
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Configuración completa
            OutlinedButton(
                onClick = {
                    scope.launch {
                        pagesRepository.initializeWithFullSetup()
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = colors.accent
                )
            ) {
                Text(
                    text = stringResource(R.string.pages_activate_all),
                    style = MaterialTheme.typography.labelMedium.copy(
                        fontFamily = NevenFontFamily
                    )
                )
            }
            
            TextButton(
                onClick = {
                    scope.launch {
                        pagesRepository.resetToDefault()
                    }
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = stringResource(R.string.pages_reset_default),
                    style = MaterialTheme.typography.labelSmall.copy(
                        fontFamily = NevenFontFamily
                    ),
                    color = colors.textSecondary
                )
            }
        }
    }
}

/**
 * Item de toggle para una página
 */
@Composable
private fun PageToggleItem(
    title: String,
    symbol: String,
    description: String,
    isEnabled: Boolean,
    onToggle: (Boolean) -> Unit,
    colors: NevenColors
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onToggle(!isEnabled) }
            .padding(vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Símbolo
        Text(
            text = symbol,
            style = MaterialTheme.typography.headlineSmall.copy(
                fontFamily = FontFamily.Serif
            ),
            color = if (isEnabled) colors.accent else colors.textSecondary.copy(alpha = 0.4f),
            modifier = Modifier.width(40.dp)
        )
        
        Spacer(modifier = Modifier.width(16.dp))
        
        // Textos
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium
                ),
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall.copy(
                    fontFamily = NevenFontFamily
                ),
                color = colors.textSecondary
            )
        }
        
        Spacer(modifier = Modifier.width(16.dp))
        
        // Switch
        Switch(
            checked = isEnabled,
            onCheckedChange = onToggle,
            colors = SwitchDefaults.colors(
                checkedThumbColor = colors.accent,
                checkedTrackColor = colors.accent.copy(alpha = 0.3f),
                uncheckedThumbColor = colors.textSecondary,
                uncheckedTrackColor = colors.textSecondary.copy(alpha = 0.2f)
            )
        )
    }
}
