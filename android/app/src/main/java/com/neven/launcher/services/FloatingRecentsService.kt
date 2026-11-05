package com.neven.launcher.services

import android.annotation.SuppressLint
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import androidx.lifecycle.setViewTreeLifecycleOwner
import androidx.savedstate.SavedStateRegistry
import androidx.savedstate.SavedStateRegistryController
import androidx.savedstate.SavedStateRegistryOwner
import androidx.savedstate.setViewTreeSavedStateRegistryOwner
import com.neven.launcher.R
import com.neven.launcher.data.SettingsRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/**
 * Servicio flotante que muestra un botón draggable sobre todo el sistema
 * para acceder a las aplicaciones recientes.
 * 
 * Usa AccessibilityService para invocar GLOBAL_ACTION_RECENTS
 */
class FloatingRecentsService : Service(), LifecycleOwner, SavedStateRegistryOwner {
    
    private var windowManager: WindowManager? = null
    private var floatingView: View? = null
    private var layoutParams: WindowManager.LayoutParams? = null
    
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    
    // Lifecycle management for Compose
    private val lifecycleRegistry = LifecycleRegistry(this)
    private val savedStateRegistryController = SavedStateRegistryController.create(this)
    
    override val lifecycle: Lifecycle get() = lifecycleRegistry
    override val savedStateRegistry: SavedStateRegistry get() = savedStateRegistryController.savedStateRegistry
    
    companion object {
        private var instance: FloatingRecentsService? = null
        
        fun isRunning(): Boolean = instance != null
        
        fun start(context: Context) {
            if (!isRunning()) {
                context.startService(Intent(context, FloatingRecentsService::class.java))
            }
        }
        
        fun stop(context: Context) {
            context.stopService(Intent(context, FloatingRecentsService::class.java))
        }
    }
    
    override fun onCreate() {
        super.onCreate()
        instance = this
        
        savedStateRegistryController.performRestore(null)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_CREATE)
        
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        createFloatingButton()
        
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_START)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_RESUME)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        instance = null
        
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_PAUSE)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_STOP)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_DESTROY)
        
        floatingView?.let {
            try {
                windowManager?.removeView(it)
            } catch (e: Exception) { }
        }
        serviceScope.cancel()
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    @SuppressLint("ClickableViewAccessibility")
    private fun createFloatingButton() {
        // Layout params para overlay
        val type = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }
        
        layoutParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 0
            y = 400
        }
        
        // Crear ComposeView
        val composeView = ComposeView(this).apply {
            setViewTreeLifecycleOwner(this@FloatingRecentsService)
            setViewTreeSavedStateRegistryOwner(this@FloatingRecentsService)
            
            setContent {
                FloatingRecentsButton(
                    onTap = { triggerRecents() },
                    onDrag = { deltaX, deltaY ->
                        updatePosition(deltaX.toInt(), deltaY.toInt())
                    }
                )
            }
        }
        
        floatingView = composeView
        
        try {
            windowManager?.addView(floatingView, layoutParams)
        } catch (e: Exception) {
            e.printStackTrace()
            stopSelf()
        }
    }
    
    private fun updatePosition(deltaX: Int, deltaY: Int) {
        val params = layoutParams ?: return
        params.x = params.x + deltaX
        params.y = params.y + deltaY
        try {
            windowManager?.updateViewLayout(floatingView, params)
        } catch (e: Exception) { }
    }
    
    private fun triggerRecents() {
        // Abrir nuestra propia pantalla de apps recientes
        val intent = Intent(this, com.neven.launcher.ui.recents.RecentAppsActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        startActivity(intent)
    }
}

/**
 * Botón flotante draggable con Compose
 */
@Composable
private fun FloatingRecentsButton(
    onTap: () -> Unit,
    onDrag: (Float, Float) -> Unit
) {
    var isDragging by remember { mutableStateOf(false) }
    
    Box(
        modifier = Modifier
            .size(56.dp)
            .pointerInput(Unit) {
                detectDragGestures(
                    onDragStart = { isDragging = true },
                    onDragEnd = { isDragging = false },
                    onDragCancel = { isDragging = false },
                    onDrag = { change, dragAmount ->
                        change.consume()
                        onDrag(dragAmount.x, dragAmount.y)
                    }
                )
            }
            .pointerInput(Unit) {
                detectTapGestures(
                    onTap = { if (!isDragging) onTap() }
                )
            }
            .background(
                color = Color.Black.copy(alpha = 0.6f),
                shape = CircleShape
            )
            .border(
                width = 2.dp,
                color = Color(0xFFD4E600), // Color accent de NEVEN
                shape = CircleShape
            ),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            painter = painterResource(id = R.drawable.ic_recents),
            contentDescription = "Apps recientes",
            tint = Color.White,
            modifier = Modifier.size(28.dp)
        )
    }
}
