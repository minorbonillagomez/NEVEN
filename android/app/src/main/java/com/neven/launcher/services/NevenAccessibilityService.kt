package com.neven.launcher.services

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityManager

/**
 * AccessibilityService para NEVEN Launcher.
 * 
 * Permite ejecutar acciones globales como mostrar las apps recientes
 * cuando el gesto del sistema no funciona.
 */
class NevenAccessibilityService : AccessibilityService() {
    
    companion object {
        private const val TAG = "NevenAccessibility"
        const val ACTION_SHOW_RECENTS = "com.neven.launcher.action.SHOW_RECENTS"
        const val ACTION_GO_HOME = "com.neven.launcher.action.GO_HOME"
        const val ACTION_GO_BACK = "com.neven.launcher.action.GO_BACK"
        
        private var instance: NevenAccessibilityService? = null
        
        fun isEnabled(): Boolean {
            val enabled = instance != null
            Log.d(TAG, "isEnabled: $enabled")
            return enabled
        }
        
        /**
         * Envía un broadcast para mostrar recientes
         * Se usa cuando el servicio está en otro proceso
         */
        fun requestShowRecents(context: Context) {
            Log.d(TAG, "requestShowRecents via broadcast")
            val intent = Intent(ACTION_SHOW_RECENTS).apply {
                setPackage(context.packageName)
            }
            context.sendBroadcast(intent)
        }
        
        fun showRecents(): Boolean {
            Log.d(TAG, "showRecents called, instance: ${instance != null}")
            return instance?.let {
                val result = it.performGlobalAction(GLOBAL_ACTION_RECENTS)
                Log.d(TAG, "performGlobalAction RECENTS result: $result")
                result
            } ?: false
        }
        
        fun goHome(): Boolean {
            return instance?.performGlobalAction(GLOBAL_ACTION_HOME) ?: false
        }
        
        fun goBack(): Boolean {
            return instance?.performGlobalAction(GLOBAL_ACTION_BACK) ?: false
        }
        
        /**
         * Verifica si el servicio de accesibilidad está habilitado en el sistema
         */
        fun isAccessibilityServiceEnabled(context: Context): Boolean {
            val am = context.getSystemService(Context.ACCESSIBILITY_SERVICE) as AccessibilityManager
            val enabledServices = am.getEnabledAccessibilityServiceList(AccessibilityServiceInfo.FEEDBACK_ALL_MASK)
            val isEnabled = enabledServices.any { 
                it.resolveInfo.serviceInfo.packageName == context.packageName &&
                it.resolveInfo.serviceInfo.name == NevenAccessibilityService::class.java.name
            }
            Log.d(TAG, "isAccessibilityServiceEnabled: $isEnabled")
            return isEnabled
        }
    }
    
    private val actionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            Log.d(TAG, "Received broadcast: ${intent?.action}")
            when (intent?.action) {
                ACTION_SHOW_RECENTS -> {
                    // Método 1: GLOBAL_ACTION_RECENTS
                    val success = performGlobalAction(GLOBAL_ACTION_RECENTS)
                    Log.d(TAG, "GLOBAL_ACTION_RECENTS result: $success")
                    
                    // Si retorna true pero no hace nada, el sistema lo está ignorando
                    // En ese caso, no hay mucho que hacer desde AccessibilityService
                    // El usuario necesita usar los gestos del sistema o 3-button nav
                }
                ACTION_GO_HOME -> performGlobalAction(GLOBAL_ACTION_HOME)
                ACTION_GO_BACK -> performGlobalAction(GLOBAL_ACTION_BACK)
            }
        }
    }
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "onCreate")
        instance = this
    }
    
    override fun onDestroy() {
        super.onDestroy()
        Log.d(TAG, "onDestroy")
        instance = null
        try {
            unregisterReceiver(actionReceiver)
        } catch (e: Exception) {
            Log.e(TAG, "Error unregistering receiver", e)
        }
    }
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        Log.d(TAG, "onServiceConnected")
        instance = this
        
        // Registrar receiver para acciones via broadcast
        val filter = IntentFilter().apply {
            addAction(ACTION_SHOW_RECENTS)
            addAction(ACTION_GO_HOME)
            addAction(ACTION_GO_BACK)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(actionReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(actionReceiver, filter)
        }
        
        // Configurar el servicio - importante para que funcionen las acciones globales
        val info = AccessibilityServiceInfo().apply {
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS or
                    AccessibilityServiceInfo.DEFAULT
            eventTypes = 0 // No necesitamos eventos, solo acciones globales
            notificationTimeout = 0
        }
        serviceInfo = info
        Log.d(TAG, "Service configured, receiver registered")
    }
    
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // No necesitamos procesar eventos, solo ejecutar acciones globales
    }
    
    override fun onInterrupt() {
        Log.d(TAG, "onInterrupt")
    }
}
