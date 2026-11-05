package com.neven.launcher.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neven.launcher.R
import com.neven.launcher.data.HapticIntensity
import com.neven.launcher.data.HapticScale
import com.neven.launcher.data.HapticSound
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily

/**
 * Pantalla de configuración de retroalimentación táctil (Haptic Feedback)
 * 
 * Permite configurar:
 * - Escala del elemento seleccionado
 * - Intensidad de vibración
 * - Sonido de selección
 */
@Composable
fun HapticSettingsScreen(
    currentScale: HapticScale,
    currentIntensity: HapticIntensity,
    currentSound: HapticSound,
    onScaleChange: (HapticScale) -> Unit,
    onIntensityChange: (HapticIntensity) -> Unit,
    onSoundChange: (HapticSound) -> Unit,
    colors: NevenColors,
    onBack: () -> Unit
) {
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
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Light
                ),
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Text(
                text = "∿",  // Símbolo de onda/vibración
                style = MaterialTheme.typography.headlineSmall,
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Text(
                text = stringResource(R.string.settings_haptic),
                style = MaterialTheme.typography.headlineSmall.copy(
                    fontFamily = NevenFontFamily
                ),
                color = colors.textPrimary
            )
        }
        
        // Content
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 24.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            // Escala de selección
            HapticScaleSection(
                currentScale = currentScale,
                onScaleChange = onScaleChange,
                colors = colors
            )
            
            // Intensidad de vibración
            HapticIntensitySection(
                currentIntensity = currentIntensity,
                onIntensityChange = onIntensityChange,
                colors = colors
            )
            
            // Sonido de selección
            HapticSoundSection(
                currentSound = currentSound,
                onSoundChange = onSoundChange,
                colors = colors
            )
        }
    }
}

@Composable
private fun HapticScaleSection(
    currentScale: HapticScale,
    onScaleChange: (HapticScale) -> Unit,
    colors: NevenColors
) {
    Column {
        Text(
            text = stringResource(R.string.haptic_scale_title),
            style = MaterialTheme.typography.titleMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            ),
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            HapticScale.entries.forEach { scale ->
                HapticOptionChip(
                    text = when (scale) {
                        HapticScale.SMALL -> stringResource(R.string.haptic_scale_small)
                        HapticScale.MEDIUM -> stringResource(R.string.haptic_scale_medium)
                        HapticScale.LARGE -> stringResource(R.string.haptic_scale_large)
                        HapticScale.EXTRA_LARGE -> stringResource(R.string.haptic_scale_extra_large)
                    },
                    isSelected = scale == currentScale,
                    onClick = { onScaleChange(scale) },
                    colors = colors,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun HapticIntensitySection(
    currentIntensity: HapticIntensity,
    onIntensityChange: (HapticIntensity) -> Unit,
    colors: NevenColors
) {
    Column {
        Text(
            text = stringResource(R.string.haptic_intensity_title),
            style = MaterialTheme.typography.titleMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            ),
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            HapticIntensity.entries.forEach { intensity ->
                HapticOptionChip(
                    text = when (intensity) {
                        HapticIntensity.NONE -> stringResource(R.string.haptic_intensity_none)
                        HapticIntensity.LIGHT -> stringResource(R.string.haptic_intensity_light)
                        HapticIntensity.MEDIUM -> stringResource(R.string.haptic_intensity_medium)
                        HapticIntensity.STRONG -> stringResource(R.string.haptic_intensity_strong)
                    },
                    isSelected = intensity == currentIntensity,
                    onClick = { onIntensityChange(intensity) },
                    colors = colors,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun HapticSoundSection(
    currentSound: HapticSound,
    onSoundChange: (HapticSound) -> Unit,
    colors: NevenColors
) {
    Column {
        Text(
            text = stringResource(R.string.haptic_sound_title),
            style = MaterialTheme.typography.titleMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            ),
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            HapticSound.entries.forEach { sound ->
                HapticOptionChip(
                    text = when (sound) {
                        HapticSound.NONE -> stringResource(R.string.haptic_sound_none)
                        HapticSound.CLICK -> stringResource(R.string.haptic_sound_click)
                        HapticSound.TICK -> stringResource(R.string.haptic_sound_tick)
                        HapticSound.POP -> stringResource(R.string.haptic_sound_pop)
                    },
                    isSelected = sound == currentSound,
                    onClick = { onSoundChange(sound) },
                    colors = colors,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun HapticOptionChip(
    text: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    colors: NevenColors,
    modifier: Modifier = Modifier
) {
    val borderColor = if (isSelected) colors.accent else colors.textSecondary.copy(alpha = 0.3f)
    val borderWidth = if (isSelected) 1.5.dp else 0.5.dp
    
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .border(
                width = borderWidth,
                color = borderColor,
                shape = RoundedCornerShape(8.dp)
            )
            .clickable { onClick() }
            .padding(vertical = 12.dp, horizontal = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            fontSize = 12.sp,
            fontFamily = NevenFontFamily,
            fontWeight = if (isSelected) FontWeight.Medium else FontWeight.Normal,
            color = if (isSelected) colors.accent else colors.textPrimary
        )
    }
}
