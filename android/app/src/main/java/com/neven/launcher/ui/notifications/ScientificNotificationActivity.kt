package com.neven.launcher.ui.notifications

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.*
import com.neven.launcher.data.NotificationPopupSize
import com.neven.launcher.data.NotificationPreferencesRepository
import com.neven.launcher.data.ScientificNotification
import com.neven.launcher.data.SettingsRepository
import com.neven.launcher.ui.theme.NevenTheme
import com.neven.launcher.ui.theme.getNevenColors
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking

/**
 * Activity que muestra el popup de notificación científica
 * 
 * Se muestra como un diálogo flotante sobre otras apps
 * cuando llega una notificación elegible
 */
class ScientificNotificationActivity : ComponentActivity() {
    
    companion object {
        private const val EXTRA_NOTIFICATION_KEY = "notification_key"
        private const val EXTRA_PACKAGE_NAME = "package_name"
        private const val EXTRA_APP_NAME = "app_name"
        private const val EXTRA_AUTHOR = "author"
        private const val EXTRA_CONTENT = "content"
        private const val EXTRA_TIMESTAMP = "timestamp"
        private const val EXTRA_NOTIFICATION_ID = "notification_id"
        
        // Para la respuesta rápida
        private var pendingReplyAction: PendingIntent? = null
        private var pendingReplyInput: android.app.RemoteInput? = null
        private var pendingContentIntent: PendingIntent? = null
        
        /**
         * Crea un Intent para mostrar la notificación científica
         */
        fun createIntent(
            context: Context,
            notification: ScientificNotification
        ): Intent {
            // Guardar los objetos de respuesta para uso posterior
            pendingReplyAction = notification.replyAction?.actionIntent
            pendingReplyInput = notification.replyAction?.remoteInput
            pendingContentIntent = notification.contentIntent
            
            return Intent(context, ScientificNotificationActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or 
                        Intent.FLAG_ACTIVITY_CLEAR_TOP or
                        Intent.FLAG_ACTIVITY_SINGLE_TOP
                putExtra(EXTRA_NOTIFICATION_KEY, notification.key)
                putExtra(EXTRA_PACKAGE_NAME, notification.packageName)
                putExtra(EXTRA_APP_NAME, notification.appName)
                putExtra(EXTRA_AUTHOR, notification.author)
                putExtra(EXTRA_CONTENT, notification.content)
                putExtra(EXTRA_TIMESTAMP, notification.timestamp)
                putExtra(EXTRA_NOTIFICATION_ID, notification.id)
            }
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Configurar ventana como diálogo flotante
        setupFloatingWindow()
        
        // Extraer datos del intent
        val notificationKey = intent.getStringExtra(EXTRA_NOTIFICATION_KEY) ?: ""
        val packageName = intent.getStringExtra(EXTRA_PACKAGE_NAME) ?: ""
        val appName = intent.getStringExtra(EXTRA_APP_NAME) ?: "App"
        val author = intent.getStringExtra(EXTRA_AUTHOR) ?: "Anónimo"
        val content = intent.getStringExtra(EXTRA_CONTENT) ?: ""
        val timestamp = intent.getLongExtra(EXTRA_TIMESTAMP, System.currentTimeMillis())
        val notificationId = intent.getIntExtra(EXTRA_NOTIFICATION_ID, 0)
        
        // Reconstruir el objeto de notificación
        val notification = ScientificNotification(
            id = notificationId,
            key = notificationKey,
            packageName = packageName,
            appName = appName,
            author = author,
            title = null,
            content = content,
            timestamp = timestamp,
            icon = null,
            largeIcon = null,
            contentIntent = pendingContentIntent,
            replyAction = if (pendingReplyAction != null && pendingReplyInput != null) {
                com.neven.launcher.data.ReplyAction(
                    actionIntent = pendingReplyAction!!,
                    remoteInput = pendingReplyInput!!,
                    label = "Responder"
                )
            } else null,
            actions = emptyList()
        )
        
        setContent {
            // Obtener preferencias
            val settingsRepo = remember { SettingsRepository.getInstance(this) }
            val notifPrefs = remember { NotificationPreferencesRepository(this) }
            
            val palette by settingsRepo.paletteFlow.collectAsState(
                initial = runBlocking { settingsRepo.paletteFlow.first() }
            )
            val themeMode by settingsRepo.themeModeFlow.collectAsState(
                initial = runBlocking { settingsRepo.themeModeFlow.first() }
            )
            val fontSizeScale by settingsRepo.fontSizeScaleFlow.collectAsState(
                initial = 1.0f
            )
            val fontFamily by settingsRepo.fontFamilyFlow.collectAsState(
                initial = com.neven.launcher.data.NevenFontFamily.SERIF
            )
            val customAccentColor by settingsRepo.customAccentColorFlow.collectAsState(
                initial = "#D32F2F"
            )
            val isDark = themeMode == com.neven.launcher.data.ThemeMode.DARK ||
                        (themeMode == com.neven.launcher.data.ThemeMode.AUTO && 
                         android.content.res.Configuration.UI_MODE_NIGHT_YES == 
                         (resources.configuration.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK))
            val popupSize by notifPrefs.popupSize.collectAsState(
                initial = NotificationPopupSize.NORMAL
            )
            val renderLatex by notifPrefs.renderLatex.collectAsState(initial = true)
            val showTimestamp by notifPrefs.showTimestamp.collectAsState(initial = true)
            val quickReplyEnabled by notifPrefs.quickReplyEnabled.collectAsState(initial = true)
            
            val colors = getNevenColors(palette, isDark)
            
            NevenTheme(
                palette = palette,
                darkTheme = isDark,
                fontScale = fontSizeScale,
                fontFamily = fontFamily,
                customAccentColorHex = customAccentColor
            ) {
                ScientificNotificationPopup(
                    notification = notification,
                    colors = colors,
                    popupSize = popupSize,
                    renderLatex = renderLatex,
                    showTimestamp = showTimestamp,
                    quickReplyEnabled = quickReplyEnabled,
                    onDismiss = {
                        finish()
                    },
                    onReply = { replyText ->
                        sendReply(replyText)
                        finish()
                    },
                    onOpenApp = {
                        openSourceApp()
                        finish()
                    }
                )
            }
        }
    }
    
    /**
     * Configura la ventana como diálogo flotante
     */
    private fun setupFloatingWindow() {
        window.apply {
            // Hacer la ventana flotante
            setBackgroundDrawableResource(android.R.color.transparent)
            
            // Configurar layout params
            attributes = attributes.apply {
                // Permitir que se muestre sobre otras apps
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                }
                
                // Dimming del fondo
                dimAmount = 0.6f
                flags = flags or WindowManager.LayoutParams.FLAG_DIM_BEHIND
                
                // No tomar foco completo
                flags = flags or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            }
        }
    }
    
    /**
     * Envía una respuesta rápida a la notificación
     */
    private fun sendReply(text: String) {
        val replyAction = pendingReplyAction
        val remoteInput = pendingReplyInput
        
        if (replyAction != null && remoteInput != null) {
            try {
                // Construir el intent de respuesta usando android.app.RemoteInput
                val intent = Intent()
                val results = Bundle()
                results.putCharSequence(remoteInput.resultKey, text)
                android.app.RemoteInput.addResultsToIntent(arrayOf(remoteInput), intent, results)
                
                // Enviar
                replyAction.send(this, 0, intent)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
    
    /**
     * Abre la aplicación de origen
     */
    private fun openSourceApp() {
        try {
            pendingContentIntent?.send()
        } catch (e: Exception) {
            // Si falla, intentar abrir la app directamente
            val packageName = intent.getStringExtra(EXTRA_PACKAGE_NAME)
            if (packageName != null) {
                val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
                if (launchIntent != null) {
                    startActivity(launchIntent)
                }
            }
        }
    }
    
    // Removido onPause que cerraba el popup inmediatamente
    // El popup se cerrará solo cuando el usuario lo descarte explícitamente
    // o toque fuera de él (manejado en el Composable)
}
