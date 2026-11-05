package com.neven.launcher.ui.components

import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import coil.compose.AsyncImage
import com.neven.launcher.R
import com.neven.launcher.data.BackgroundPosition
import com.neven.launcher.data.BackgroundType
import com.neven.launcher.ui.theme.CharcoalBackground

/**
 * Componente reutilizable de fondo para NEVEN Launcher.
 * 
 * Soporta:
 * - Color sólido (paleta)
 * - Imagen de fondo (drawable o galería)
 * - Overlay de opacidad (λ)
 * - Tinte de paleta opcional
 * 
 * Usado en HomeScreen y todas las pantallas de Settings para
 * mantener consistencia visual.
 */
@Composable
fun NevenBackground(
    backgroundType: BackgroundType,
    imageUri: String?,
    position: BackgroundPosition,
    opacity: Float,
    tintEnabled: Boolean,
    tintColor: Color,
    fallbackColor: Color,
    isDark: Boolean,
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit
) {
    Box(modifier = modifier.fillMaxSize()) {
        // Capa 1: Color de fondo base (siempre presente)
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(fallbackColor)
        )
        
        // Capa 2: Imagen de fondo (si está configurada)
        if (backgroundType == BackgroundType.IMAGE && imageUri != null) {
            // Determinar ContentScale según posición
            val contentScale = when (position) {
                BackgroundPosition.FIT -> ContentScale.Fit
                BackgroundPosition.CROP -> ContentScale.Crop
                BackgroundPosition.CENTER -> ContentScale.None
            }
            
            // Detectar si es un recurso drawable o una URI externa
            val isDrawableResource = imageUri.startsWith("android.resource://")
            
            if (isDrawableResource) {
                // Para recursos drawable, usar painterResource directamente
                Image(
                    painter = painterResource(id = R.drawable.fondo_default),
                    contentDescription = null,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = contentScale
                )
            } else {
                // Para URIs externas (galería), usar Coil
                AsyncImage(
                    model = Uri.parse(imageUri),
                    contentDescription = null,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = contentScale
                )
            }
            
            // Capa 3: Overlay oscuro con opacidad λ
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = opacity))
            )
            
            // Capa 4: Tinte de paleta (opcional)
            if (tintEnabled) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(tintColor.copy(alpha = 0.15f))
                )
            }
        } else {
            // Sin imagen: efecto sutil de fondo
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(
                        if (isDark) {
                            fallbackColor.copy(alpha = 0.95f)
                        } else {
                            fallbackColor
                        }
                    )
            )
        }
        
        // Contenido sobre el fondo
        content()
    }
}

/**
 * Versión simplificada que usa CharcoalBackground cuando no hay imagen
 */
@Composable
fun NevenBackgroundWithCharcoal(
    backgroundType: BackgroundType,
    imageUri: String?,
    position: BackgroundPosition,
    opacity: Float,
    tintEnabled: Boolean,
    tintColor: Color,
    fallbackColor: Color,
    isDark: Boolean,
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit
) {
    if (backgroundType == BackgroundType.IMAGE && imageUri != null) {
        NevenBackground(
            backgroundType = backgroundType,
            imageUri = imageUri,
            position = position,
            opacity = opacity,
            tintEnabled = tintEnabled,
            tintColor = tintColor,
            fallbackColor = fallbackColor,
            isDark = isDark,
            modifier = modifier,
            content = content
        )
    } else {
        CharcoalBackground(
            backgroundColor = fallbackColor,
            isDark = isDark,
            content = { content() }
        )
    }
}
