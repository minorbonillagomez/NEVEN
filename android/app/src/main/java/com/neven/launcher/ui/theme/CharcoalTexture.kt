package com.neven.launcher.ui.theme

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PointMode
import androidx.compose.ui.graphics.StrokeCap
import kotlin.random.Random

/**
 * NEVEN Charcoal / Slate Stone Textured Background
 * 
 * Provides a tactile, dark charcoal stone surface effect:
 * 1. Base palette background color
 * 2. Vignette radial gradient for physical depth
 * 3. Deterministic mineral & carbon fleck grain
 */
@Composable
fun CharcoalBackground(
    modifier: Modifier = Modifier,
    backgroundColor: Color,
    isDark: Boolean = true,
    content: @Composable BoxScope.() -> Unit
) {
    // Generate deterministic stone noise particles based on fixed seeds
    val lightMineralFlecks = remember(isDark) {
        val random = Random(101)
        List(1400) {
            Offset(random.nextFloat(), random.nextFloat())
        }
    }
    val darkCarbonFlecks = remember(isDark) {
        val random = Random(202)
        List(1800) {
            Offset(random.nextFloat(), random.nextFloat())
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(backgroundColor)
    ) {
        // Charcoal stone texture layer
        Canvas(modifier = Modifier.fillMaxSize()) {
            val width = size.width
            val height = size.height
            if (width > 0f && height > 0f) {
                // 1. Radial depth vignette
                val vignetteBrush = Brush.radialGradient(
                    colors = if (isDark) {
                        listOf(
                            Color.White.copy(alpha = 0.035f),
                            Color.Transparent,
                            Color.Black.copy(alpha = 0.45f)
                        )
                    } else {
                        listOf(
                            Color.White.copy(alpha = 0.35f),
                            Color.Transparent,
                            Color.Black.copy(alpha = 0.08f)
                        )
                    },
                    center = Offset(width / 2f, height * 0.35f),
                    radius = maxOf(width, height) * 0.9f
                )
                drawRect(brush = vignetteBrush)

                // 2. Light mineral flecks
                val lightColor = if (isDark) Color.White.copy(alpha = 0.045f) else Color.White.copy(alpha = 0.12f)
                val lightPoints = lightMineralFlecks.map {
                    Offset(it.x * width, it.y * height)
                }
                drawPoints(
                    points = lightPoints,
                    pointMode = PointMode.Points,
                    color = lightColor,
                    strokeWidth = 2.5f,
                    cap = StrokeCap.Round
                )

                // 3. Dark carbon specks
                val darkColor = if (isDark) Color.Black.copy(alpha = 0.22f) else Color.Black.copy(alpha = 0.07f)
                val darkPoints = darkCarbonFlecks.map {
                    Offset(it.x * width, it.y * height)
                }
                drawPoints(
                    points = darkPoints,
                    pointMode = PointMode.Points,
                    color = darkColor,
                    strokeWidth = 3f,
                    cap = StrokeCap.Round
                )
            }
        }

        content()
    }
}
