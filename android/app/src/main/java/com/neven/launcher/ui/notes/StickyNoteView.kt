package com.neven.launcher.ui.notes

import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChange
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.zIndex
import androidx.core.graphics.toColorInt
import com.neven.launcher.data.StickyNote
import com.neven.launcher.data.StickyNoteColor
import com.neven.launcher.ui.markdown.KaTeXAssetLoader
import com.neven.launcher.ui.markdown.MarkdownHtmlGenerator
import kotlin.math.abs
import kotlin.math.roundToInt

/**
 * Vista de un Post-it / Nota adhesiva
 * 
 * Caracteristicas:
 * - Aspecto de nota adhesiva con esquina doblada
 * - Sombra sutil para efecto 3D
 * - Arrastrrable para mover
 * - Tap para editar
 * - Renderiza Markdown/LaTeX
 */
@Composable
fun StickyNoteView(
    note: StickyNote,
    containerWidth: Float,
    containerHeight: Float,
    opacity: Float = 0.9f,
    onNoteUpdate: (StickyNote) -> Unit,
    onNoteDelete: (String) -> Unit,
    onNoteTap: (StickyNote) -> Unit,
    onBringToFront: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val density = LocalDensity.current
    
    // Convertir posicion relativa a pixeles
    val noteWidth = with(density) { note.size.widthDp.dp.toPx() }
    val noteHeight = with(density) { note.size.heightDp.dp.toPx() }
    
    var offsetX by remember(note.id, note.positionX) { 
        mutableStateOf(note.positionX * containerWidth) 
    }
    var offsetY by remember(note.id, note.positionY) { 
        mutableStateOf(note.positionY * containerHeight) 
    }
    var isDragging by remember { mutableStateOf(false) }
    
    // Color del post-it con opacidad configurada
    val backgroundColor = Color(note.color.hex.toColorInt()).copy(alpha = opacity)
    val darkerColor = backgroundColor.copy(
        red = (backgroundColor.red * 0.9f).coerceIn(0f, 1f),
        green = (backgroundColor.green * 0.9f).coerceIn(0f, 1f),
        blue = (backgroundColor.blue * 0.9f).coerceIn(0f, 1f),
        alpha = opacity
    )
    
    // Umbral para distinguir tap de drag (en pixels)
    val tapThreshold = with(density) { 10.dp.toPx() }
    var totalDragDistance by remember { mutableStateOf(0f) }
    
    Box(
        modifier = modifier
            .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
            .width(note.size.widthDp.dp)
            .height(note.size.heightDp.dp)
            .zIndex(note.zIndex.toFloat() + if (isDragging) 1000f else 0f)
            .graphicsLayer {
                // Sombra mas pronunciada si esta siendo arrastrado
                shadowElevation = if (isDragging) 12f else 4f
            }
            .shadow(
                elevation = if (isDragging) 12.dp else 4.dp,
                shape = RoundedCornerShape(4.dp),
                clip = false
            )
            .pointerInput(note.id) {
                // Gesto unificado: distingue tap de drag por distancia
                awaitEachGesture {
                    val down = awaitFirstDown(requireUnconsumed = false)
                    totalDragDistance = 0f
                    var wasDragging = false
                    
                    onBringToFront(note.id)
                    
                    while (true) {
                        val event = awaitPointerEvent(PointerEventPass.Main)
                        val change = event.changes.firstOrNull() ?: break
                        
                        if (!change.pressed) {
                            // Dedo levantado
                            if (!wasDragging && totalDragDistance < tapThreshold) {
                                // Fue un tap - abrir editor
                                onNoteTap(note)
                            } else if (wasDragging) {
                                // Fin del drag - guardar posicion
                                isDragging = false
                                val relX = (offsetX / containerWidth).coerceIn(0f, 1f - (noteWidth / containerWidth))
                                val relY = (offsetY / containerHeight).coerceIn(0f, 1f - (noteHeight / containerHeight))
                                onNoteUpdate(note.withPosition(relX, relY))
                            }
                            break
                        }
                        
                        val dragAmount = change.positionChange()
                        totalDragDistance += abs(dragAmount.x) + abs(dragAmount.y)
                        
                        if (totalDragDistance >= tapThreshold) {
                            // Cambio a modo drag
                            if (!wasDragging) {
                                wasDragging = true
                                isDragging = true
                            }
                            
                            // Mover la nota
                            val newX = (offsetX + dragAmount.x).coerceIn(0f, containerWidth - noteWidth)
                            val newY = (offsetY + dragAmount.y).coerceIn(0f, containerHeight - noteHeight)
                            offsetX = newX
                            offsetY = newY
                            change.consume()
                        }
                    }
                }
            }
    ) {
        // Fondo del post-it con forma de nota adhesiva
        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(4.dp))
                .background(backgroundColor)
        ) {
            // Contenido del post-it
            if (note.content.isNotEmpty()) {
                StickyNoteContent(
                    content = note.content,
                    backgroundColor = note.color,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(top = 20.dp, start = 8.dp, end = 8.dp, bottom = 8.dp)
                )
            } else {
                // Placeholder para nota vacia
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(top = 20.dp, start = 8.dp, end = 8.dp, bottom = 8.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "Toca para escribir...",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.Gray.copy(alpha = 0.5f)
                    )
                }
            }
            
            // Boton eliminar (X) en esquina superior izquierda
            // Usamos Box con pointerInput para evitar propagacion de eventos
            Box(
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(2.dp)
                    .size(22.dp)
                    .clip(CircleShape)
                    .background(Color(0xFF666666).copy(alpha = 0.85f))
                    .pointerInput(note.id) {
                        awaitEachGesture {
                            val down = awaitFirstDown(requireUnconsumed = false)
                            down.consume()
                            val up = waitForUpOrCancellation()
                            if (up != null) {
                                up.consume()
                                onNoteDelete(note.id)
                            }
                        }
                    },
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "x",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
            }
            
            // Esquina doblada (efecto visual)
            Box(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .size(16.dp)
            ) {
                androidx.compose.foundation.Canvas(modifier = Modifier.fillMaxSize()) {
                    drawFoldedCorner(darkerColor)
                }
            }
        }
    }
}

/**
 * Dibuja la esquina doblada del post-it
 */
private fun DrawScope.drawFoldedCorner(color: Color) {
    val path = Path().apply {
        moveTo(size.width, 0f)
        lineTo(0f, 0f)
        lineTo(size.width, size.height)
        close()
    }
    drawPath(path, color)
}

/**
 * Contenido del Post-it con soporte Markdown/LaTeX
 */
@Composable
private fun StickyNoteContent(
    content: String,
    backgroundColor: StickyNoteColor,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    
    // Cargar KaTeX si no esta cargado
    LaunchedEffect(Unit) {
        if (!KaTeXAssetLoader.isLoaded()) {
            KaTeXAssetLoader.loadAssets(context)
        }
    }
    
    // Determinar color de texto segun fondo
    val textColor = when (backgroundColor) {
        StickyNoteColor.YELLOW, StickyNoteColor.CREAM, StickyNoteColor.WHITE -> "#2D2D2D"
        else -> "#1A1A1A"
    }
    
    AndroidView(
        factory = { ctx ->
            WebView(ctx).apply {
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.loadWithOverviewMode = true
                settings.useWideViewPort = false
                
                setBackgroundColor(android.graphics.Color.TRANSPARENT)
                
                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                        return true // No navegar a links
                    }
                }
            }
        },
        update = { webView ->
            val htmlContent = generateStickyNoteHtml(
                content = content,
                textColor = textColor,
                bgColor = backgroundColor.hex
            )
            
            webView.loadDataWithBaseURL(
                null,
                htmlContent,
                "text/html",
                "UTF-8",
                null
            )
        },
        modifier = modifier
    )
}

/**
 * Genera HTML para el contenido del Post-it
 */
private fun generateStickyNoteHtml(
    content: String,
    textColor: String,
    bgColor: String
): String {
    // Si KaTeX esta cargado, usar el generador completo
    if (KaTeXAssetLoader.isLoaded()) {
        return MarkdownHtmlGenerator.generateHtmlForPopup(
            markdown = content,
            textColor = textColor,
            accentColor = "#C9A227",
            maxLines = 0
        ).replace(
            "background: transparent !important",
            "background: transparent !important"
        )
    }
    
    // Fallback sin KaTeX - usa tipografía LaTeX (Computer Modern)
    val escapedContent = content
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/aaaakshat/cm-web-fonts@latest/fonts.css">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: transparent !important; }
body {
    font-family: 'Computer Modern Serif', 'CMU Serif', 'Latin Modern Roman', Georgia, serif;
    color: $textColor;
    font-size: 13px;
    line-height: 1.4;
    word-wrap: break-word;
}
</style>
</head>
<body>$escapedContent</body>
</html>"""
}
