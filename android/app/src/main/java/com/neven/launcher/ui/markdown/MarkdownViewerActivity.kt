package com.neven.launcher.ui.markdown

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.*
import androidx.core.view.WindowCompat
import com.neven.launcher.R
import com.neven.launcher.data.BackgroundPosition
import com.neven.launcher.data.BackgroundType
import com.neven.launcher.data.NevenFontFamily
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.data.ThemeMode
import com.neven.launcher.ui.theme.NevenPalette
import com.neven.launcher.ui.theme.NevenTheme
import com.neven.launcher.ui.theme.getNevenColors
import java.io.BufferedReader
import java.io.InputStreamReader

/**
 * NEVEN Markdown Viewer Activity
 * 
 * Activity principal para visualizar archivos .md (Markdown) con soporte LaTeX.
 * 
 * Funcionalidades:
 * - Recibe URI del archivo via Intent (ACTION_VIEW)
 * - Lee el contenido del archivo
 * - Lo renderiza con MarkdownViewerScreen
 * - Soporta ecuaciones LaTeX inline ($...$) y en bloque ($$...$$)
 * 
 * Intent filters:
 * - android.intent.action.VIEW para archivos .md
 * - MIME types: text/markdown, text/x-markdown, text/plain con extensión .md
 * 
 * El activity usa el mismo tema y fondo translúcido del launcher principal
 * para mantener consistencia visual.
 */
class MarkdownViewerActivity : ComponentActivity() {
    
    companion object {
        private const val TAG = "MarkdownViewerActivity"
        
        /**
         * Opacidad por defecto para el visor Markdown (85%)
         * Mayor que el launcher para mejorar legibilidad durante lectura
         */
        private const val READER_DEFAULT_OPACITY = 0.85f
        
        /**
         * Crea un Intent para abrir un archivo Markdown
         * 
         * @param context Contexto de Android
         * @param uri URI del archivo .md
         * @return Intent configurado para abrir MarkdownViewerActivity
         */
        fun createIntent(context: android.content.Context, uri: Uri): Intent {
            return Intent(context, MarkdownViewerActivity::class.java).apply {
                action = Intent.ACTION_VIEW
                data = uri
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        try {
            Log.d(TAG, "onCreate iniciado")
            
            enableEdgeToEdge()
            WindowCompat.setDecorFitsSystemWindows(window, false)
            
            // Obtener URI del archivo desde el Intent
            val fileUri = intent?.data
            Log.d(TAG, "URI recibida: $fileUri")
            
            // Verificar que hay una URI válida antes de continuar
            if (fileUri == null) {
                Log.e(TAG, "No se recibió URI del archivo")
                showError(getString(R.string.markdown_error_no_file))
                finish()
                return
            }
            
            val fileName = extractFileName(fileUri)
            Log.d(TAG, "Nombre del archivo: $fileName")
            
            // Leer contenido del archivo
            val content = readFileContent(fileUri)
            Log.d(TAG, "Contenido leído: ${content?.length ?: 0} caracteres")
            
            // Si no se pudo leer el contenido, terminar
            if (content == null) {
                Log.e(TAG, "No se pudo leer el contenido del archivo")
                finish()
                return
            }
            
            setContent {
            // Repositorio de configuraciones
            val settingsRepository = remember { SettingsRepository.getInstance(this) }
            
            // Observar preferencias desde DataStore
            val selectedPalette by settingsRepository.paletteFlow
                .collectAsState(initial = NevenPalette.CLASICO)
            val themeMode by settingsRepository.themeModeFlow
                .collectAsState(initial = ThemeMode.DARK)
            val fontSizeScale by settingsRepository.fontSizeScaleFlow
                .collectAsState(initial = 1.0f)
            val customAccentColor by settingsRepository.customAccentColorFlow
                .collectAsState(initial = "#D32F2F")
            val fontFamily by settingsRepository.fontFamilyFlow
                .collectAsState(initial = NevenFontFamily.SERIF)
            
            // Configuración de fondo
            val backgroundType by settingsRepository.backgroundTypeFlow
                .collectAsState(initial = BackgroundType.SOLID)
            val backgroundImageUri by settingsRepository.backgroundImageUriFlow
                .collectAsState(initial = null)
            val backgroundPosition by settingsRepository.backgroundPositionFlow
                .collectAsState(initial = BackgroundPosition.CROP)
            // Nota: backgroundOpacity del settings se ignora - el visor usa 85% fijo
            val backgroundTintEnabled by settingsRepository.backgroundTintEnabledFlow
                .collectAsState(initial = false)
            
            // Determinar modo oscuro
            val isSystemDark = isSystemInDarkTheme()
            val isDarkMode = when (themeMode) {
                ThemeMode.DARK -> true
                ThemeMode.LIGHT -> false
                ThemeMode.AUTO -> isSystemDark
            }
            
            // Obtener colores según paleta actual
            val colors = getNevenColors(
                palette = selectedPalette,
                darkTheme = isDarkMode,
                customAccentColor = if (selectedPalette == NevenPalette.CLASICO) {
                    hexToColor(customAccentColor)
                } else null
            )
            
            NevenTheme(
                palette = selectedPalette,
                darkTheme = isDarkMode,
                fontScale = fontSizeScale,
                fontFamily = fontFamily,
                customAccentColorHex = customAccentColor
            ) {
                // Usar opacidad 85% para el visor MD (mejor legibilidad)
                MarkdownViewerScreen(
                    content = content,
                    fileName = fileName,
                    colors = colors,
                    backgroundType = backgroundType,
                    backgroundImageUri = backgroundImageUri,
                    backgroundPosition = backgroundPosition,
                    backgroundOpacity = READER_DEFAULT_OPACITY,
                    backgroundTintEnabled = backgroundTintEnabled,
                    onBack = { finish() }
                )
            }
        }
        
        Log.d(TAG, "setContent completado exitosamente")
        
        } catch (e: Exception) {
            // Capturar cualquier error inesperado y mostrar mensaje
            Log.e(TAG, "Error fatal en onCreate: ${e.message}", e)
            e.printStackTrace()
            Toast.makeText(
                this,
                "Error al abrir: ${e.localizedMessage ?: e.message ?: "Error desconocido"}",
                Toast.LENGTH_LONG
            ).show()
            finish()
        }
    }
    
    /**
     * Extrae el nombre del archivo desde la URI
     * 
     * @param uri URI del archivo
     * @return Nombre del archivo o "Documento" si no se puede extraer
     */
    private fun extractFileName(uri: Uri?): String {
        if (uri == null) {
            Log.d(TAG, "extractFileName: URI es null, retornando nombre por defecto")
            return getString(R.string.markdown_document)
        }
        
        return try {
            // Intentar obtener nombre desde el path
            val path = uri.path
            Log.d(TAG, "extractFileName: path = $path")
            if (path != null) {
                val segments = path.split("/")
                val lastSegment = segments.lastOrNull()
                if (!lastSegment.isNullOrBlank()) {
                    Log.d(TAG, "extractFileName: nombre extraído = $lastSegment")
                    return lastSegment
                }
            }
            
            // Intentar obtener desde lastPathSegment
            val lastPathSegment = uri.lastPathSegment
            Log.d(TAG, "extractFileName: lastPathSegment = $lastPathSegment")
            lastPathSegment ?: getString(R.string.markdown_document)
        } catch (e: Exception) {
            Log.e(TAG, "Error al extraer nombre del archivo", e)
            getString(R.string.markdown_document)
        }
    }
    
    /**
     * Lee el contenido de un archivo desde su URI
     * 
     * @param uri URI del archivo a leer
     * @return Contenido del archivo como String, o null si hay error
     */
    private fun readFileContent(uri: Uri?): String? {
        if (uri == null) {
            Log.e(TAG, "readFileContent: URI es null")
            showError(getString(R.string.markdown_error_no_file))
            return null
        }
        
        return try {
            Log.d(TAG, "Intentando leer archivo: $uri")
            contentResolver.openInputStream(uri)?.use { inputStream ->
                BufferedReader(InputStreamReader(inputStream, Charsets.UTF_8)).use { reader ->
                    val content = reader.readText()
                    Log.d(TAG, "Archivo leído exitosamente: ${content.length} caracteres")
                    content
                }
            } ?: run {
                Log.e(TAG, "openInputStream retornó null")
                showError(getString(R.string.markdown_error_reading))
                null
            }
        } catch (e: SecurityException) {
            Log.e(TAG, "Error de permisos al leer archivo", e)
            showError(getString(R.string.markdown_error_permission))
            null
        } catch (e: Exception) {
            Log.e(TAG, "Error inesperado al leer archivo: ${e.message}", e)
            showError(getString(R.string.markdown_error_reading))
            null
        }
    }
    
    /**
     * Muestra un mensaje de error al usuario
     */
    private fun showError(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }
    
    /**
     * Convierte cadena hexadecimal a Color de Compose
     */
    private fun hexToColor(hex: String): androidx.compose.ui.graphics.Color {
        return try {
            val cleanHex = hex.removePrefix("#")
            val colorInt = cleanHex.toLong(16)
            androidx.compose.ui.graphics.Color(
                red = ((colorInt shr 16) and 0xFF) / 255f,
                green = ((colorInt shr 8) and 0xFF) / 255f,
                blue = (colorInt and 0xFF) / 255f
            )
        } catch (e: Exception) {
            androidx.compose.ui.graphics.Color(0xFFD32F2F)
        }
    }
}
