package com.neven.launcher.services

import android.app.Notification
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.neven.launcher.data.NotificationPreferencesRepository
import com.neven.launcher.data.ScientificNotification
import com.neven.launcher.ui.notifications.FloatingNotificationService
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first

/**
 * NEVEN Notification Listener Service
 * 
 * Escucha notificaciones para:
 * 1. Mostrar badges científicos en las apps (superíndice)
 * 2. Mostrar popup de notificación estilo paper científico
 */
class NevenNotificationListenerService : NotificationListenerService() {
    
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var notificationPrefs: NotificationPreferencesRepository? = null
    
    companion object {
        private const val TAG = "NevenNotifService"
        
        var isConnected: Boolean = false
            private set
        
        private val _notificationCounts = MutableStateFlow<Map<String, Int>>(emptyMap())
        val notificationCounts: StateFlow<Map<String, Int>> = _notificationCounts.asStateFlow()
        
        /**
         * Get notification count for a specific package
         */
        fun getNotificationCount(packageName: String): Int {
            return _notificationCounts.value[packageName] ?: 0
        }
        
        /**
         * Format count as superscript for display
         * e.g., 5 -> "⁽⁵⁾"
         */
        fun formatAsSuperscript(count: Int): String {
            if (count <= 0) return ""
            val superscriptDigits = mapOf(
                '0' to '⁰', '1' to '¹', '2' to '²', '3' to '³', '4' to '⁴',
                '5' to '⁵', '6' to '⁶', '7' to '⁷', '8' to '⁸', '9' to '⁹'
            )
            val superNum = count.toString().map { superscriptDigits[it] ?: it }.joinToString("")
            return "⁽$superNum⁾"
        }
    }
    
    // Apps de mensajería que muestran popup científico
    private val messagingApps = setOf(
        "com.whatsapp",
        "com.whatsapp.w4b",
        "org.telegram.messenger",
        "org.telegram.messenger.web",
        "com.facebook.orca",
        "com.facebook.mlite",
        "com.google.android.apps.messaging",
        "com.samsung.android.messaging",
        "com.android.mms",
        "com.google.android.gm",
        "com.microsoft.office.outlook",
        "com.slack",
        "com.discord",
        "com.Slack",
        "org.thoughtcrime.securesms", // Signal
        "com.viber.voip",
        "jp.naver.line.android",
        "com.microsoft.teams"
    )
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Service onCreate")
        notificationPrefs = NotificationPreferencesRepository(this)
    }
    
    override fun onDestroy() {
        Log.d(TAG, "Service onDestroy")
        super.onDestroy()
        scope.cancel()
    }
    
    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn?.let { notification ->
            Log.d(TAG, "Notification received from: ${notification.packageName}")
            
            // Actualizar contador de badges
            updateNotificationCount(notification.packageName, getCount(notification.packageName) + 1)
            
            // Verificar si debe mostrar popup cientifico
            scope.launch {
                val shouldShow = shouldShowScientificPopup(notification)
                Log.d(TAG, "Should show popup for ${notification.packageName}: $shouldShow")
                
                if (shouldShow) {
                    showScientificPopup(notification)
                }
            }
        }
    }
    
    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        sbn?.let {
            Log.d(TAG, "Notification removed from: ${it.packageName}")
            val newCount = (getCount(it.packageName) - 1).coerceAtLeast(0)
            updateNotificationCount(it.packageName, newCount)
        }
    }
    
    override fun onListenerConnected() {
        super.onListenerConnected()
        isConnected = true
        Log.d(TAG, "Listener CONNECTED")
        
        // Load current notifications
        try {
            val count = activeNotifications?.size ?: 0
            Log.d(TAG, "Active notifications: $count")
            
            activeNotifications?.forEach { sbn ->
                val pkg = sbn.packageName
                val current = _notificationCounts.value[pkg] ?: 0
                _notificationCounts.value = _notificationCounts.value + (pkg to current + 1)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading active notifications", e)
        }
    }
    
    override fun onListenerDisconnected() {
        super.onListenerDisconnected()
        isConnected = false
        Log.d(TAG, "Listener DISCONNECTED")
    }
    
    /**
     * Verifica si tiene permiso para mostrar overlays
     */
    private fun canDrawOverlays(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Settings.canDrawOverlays(this)
        } else {
            true
        }
    }
    
    /**
     * Determina si debe mostrar el popup cientifico para esta notificacion
     */
    private suspend fun shouldShowScientificPopup(sbn: StatusBarNotification): Boolean {
        // Verificar permiso de overlay
        if (!canDrawOverlays()) {
            Log.w(TAG, "No overlay permission")
            return false
        }
        
        // Verificar si el popup esta habilitado
        val prefs = notificationPrefs ?: run {
            Log.w(TAG, "Preferences not initialized")
            return false
        }
        
        val popupEnabled = prefs.popupEnabled.first()
        if (!popupEnabled) {
            Log.d(TAG, "Popup disabled in preferences")
            return false
        }
        
        // Verificar si la app esta en la lista de mensajeria
        val isMessagingApp = messagingApps.contains(sbn.packageName)
        Log.d(TAG, "Is messaging app (${sbn.packageName}): $isMessagingApp")
        if (!isMessagingApp) return false
        
        // Verificar si la app esta excluida
        val excludedApps = prefs.excludedApps.first()
        if (excludedApps.contains(sbn.packageName)) {
            Log.d(TAG, "App is excluded: ${sbn.packageName}")
            return false
        }
        
        // Verificar que sea una notificacion con mensaje (no solo un badge)
        val extras = sbn.notification.extras
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()
        val bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString()
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString()
        
        Log.d(TAG, "Notification content - Title: $title, Text: $text, BigText: ${bigText?.take(50)}")
        
        // Debe tener contenido de texto (no levantar popup solo por multimedia)
        if (text.isNullOrBlank() && bigText.isNullOrBlank()) {
            Log.d(TAG, "No text content, skipping")
            return false
        }
        
        // No mostrar para notificaciones de grupo o resumen
        if (sbn.notification.flags and Notification.FLAG_GROUP_SUMMARY != 0) {
            Log.d(TAG, "Is group summary, skipping")
            return false
        }
        
        // No mostrar para notificaciones de servicio en primer plano
        if (sbn.notification.flags and Notification.FLAG_FOREGROUND_SERVICE != 0) {
            Log.d(TAG, "Is foreground service, skipping")
            return false
        }
        
        Log.d(TAG, "All checks passed, will show popup")
        return true
    }
    
    /**
     * Muestra el popup de notificacion cientifica como ventana flotante
     */
    private fun showScientificPopup(sbn: StatusBarNotification) {
        try {
            Log.d(TAG, "Creating scientific popup for: ${sbn.packageName}")
            
            // Obtener nombre de la app
            val appName = try {
                val appInfo = packageManager.getApplicationInfo(sbn.packageName, 0)
                packageManager.getApplicationLabel(appInfo).toString()
            } catch (e: PackageManager.NameNotFoundException) {
                sbn.packageName.substringAfterLast('.')
            }
            
            // Crear objeto de notificacion cientifica
            val scientificNotification = ScientificNotification.fromStatusBarNotification(sbn, appName)
            Log.d(TAG, "Scientific notification created: author=${scientificNotification.author}, content=${scientificNotification.content.take(50)}")
            
            // Lanzar el servicio de ventana flotante
            val intent = FloatingNotificationService.createIntent(this, scientificNotification)
            startService(intent)
            Log.d(TAG, "FloatingNotificationService started")
            
        } catch (e: Exception) {
            Log.e(TAG, "Error showing scientific popup", e)
        }
    }
    
    private fun getCount(packageName: String): Int {
        return _notificationCounts.value[packageName] ?: 0
    }
    
    private fun updateNotificationCount(packageName: String, count: Int) {
        _notificationCounts.value = if (count > 0) {
            _notificationCounts.value + (packageName to count)
        } else {
            _notificationCounts.value - packageName
        }
    }
}
