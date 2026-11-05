package com.neven.launcher.ui.notifications

import android.annotation.SuppressLint
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.IBinder
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.view.animation.DecelerateInterpolator
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.LinearLayout
import android.widget.TextView
import com.neven.launcher.R
import com.neven.launcher.ui.markdown.KaTeXAssetLoader
import com.neven.launcher.ui.markdown.MarkdownHtmlGenerator
import com.neven.launcher.data.NotificationPreferencesRepository
import com.neven.launcher.data.ScientificNotification
import com.neven.launcher.data.ConversationMessage
import com.neven.launcher.data.SettingsRepository
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.first
import kotlin.math.abs

/**
 * Servicio para mostrar notificaciones cientificas como ventanas flotantes
 * 
 * Agrupa mensajes de la misma conversacion en un solo popup
 * Soporta chats individuales y grupales
 * 
 * TEMA: Dark moderno con opacidad configurable
 */
class FloatingNotificationService : Service() {
    
    private lateinit var windowManager: WindowManager
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    
    // Popup activo por conversacion (conversationId -> PopupEntry)
    private data class PopupEntry(
        var view: View,
        var params: WindowManager.LayoutParams,
        var notification: ScientificNotification,
        val contentIntent: android.app.PendingIntent?
    )
    
    // Mapa de conversaciones activas
    private val activeConversations = mutableMapOf<String, PopupEntry>()
    private var maxPopups = 3
    private var backgroundOpacity = 0.9f  // Opacidad del fondo oscuro (0.0 - 1.0)
    
    companion object {
        private const val TAG = "FloatingNotifService"
        
        private const val EXTRA_CONVERSATION_ID = "conversation_id"
        private const val EXTRA_NOTIFICATION_KEY = "notification_key"
        private const val EXTRA_PACKAGE_NAME = "package_name"
        private const val EXTRA_APP_NAME = "app_name"
        private const val EXTRA_AUTHOR = "author"
        private const val EXTRA_CONTENT = "content"
        private const val EXTRA_TIMESTAMP = "timestamp"
        private const val EXTRA_NOTIFICATION_ID = "notification_id"
        private const val EXTRA_JOURNAL_NAME = "journal_name"
        private const val EXTRA_AFFILIATION = "affiliation"
        private const val EXTRA_IS_GROUP = "is_group"
        private const val EXTRA_SENDER_IN_GROUP = "sender_in_group"
        private const val ACTION_DISMISS_ALL = "com.neven.launcher.DISMISS_ALL_POPUPS"
        
        // Offset entre popups apilados
        private const val STACK_OFFSET_X = 15
        private const val STACK_OFFSET_Y = 30
        
        // Maximo de mensajes por conversacion
        private const val MAX_MESSAGES_PER_CONVERSATION = 10
        
        // Referencias temporales
        private var pendingContentIntent: android.app.PendingIntent? = null
        
        /**
         * Crea un Intent para mostrar una nueva notificacion
         */
        fun createIntent(context: Context, notification: ScientificNotification): Intent {
            pendingContentIntent = notification.contentIntent
            
            return Intent(context, FloatingNotificationService::class.java).apply {
                putExtra(EXTRA_CONVERSATION_ID, notification.conversationId)
                putExtra(EXTRA_NOTIFICATION_KEY, notification.key)
                putExtra(EXTRA_PACKAGE_NAME, notification.packageName)
                putExtra(EXTRA_APP_NAME, notification.appName)
                putExtra(EXTRA_AUTHOR, notification.author)
                putExtra(EXTRA_CONTENT, notification.content)
                putExtra(EXTRA_TIMESTAMP, notification.timestamp)
                putExtra(EXTRA_NOTIFICATION_ID, notification.id)
                putExtra(EXTRA_JOURNAL_NAME, notification.journalName)
                putExtra(EXTRA_AFFILIATION, notification.affiliation)
                putExtra(EXTRA_IS_GROUP, notification.isGroup)
                putExtra(EXTRA_SENDER_IN_GROUP, notification.senderInGroup)
            }
        }
    }
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "FloatingNotificationService onCreate")
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        
        // IMPORTANTE: Cargar KaTeX assets al iniciar el servicio
        // Los scripts se embeben inline en el HTML porque WebView en overlay
        // no puede cargar desde file:///android_asset/
        KaTeXAssetLoader.loadAssets(this)
        Log.d(TAG, "KaTeX assets loaded: ${KaTeXAssetLoader.isLoaded()}")
        
        // Cargar configuracion
        scope.launch {
            try {
                val prefs = NotificationPreferencesRepository(this@FloatingNotificationService)
                maxPopups = prefs.maxPopups.first()
                Log.d(TAG, "Max popups: $maxPopups")
                
                // Cargar opacidad del tema (invertir para fondo oscuro: más opacidad = más oscuro)
                val settingsRepo = SettingsRepository.getInstance(this@FloatingNotificationService)
                val themeOpacity = settingsRepo.backgroundOpacityFlow.first()
                // La opacidad del tema va de 0.2 a 0.8, la convertimos para el fondo oscuro
                // Mayor opacidad en settings = fondo más translúcido
                backgroundOpacity = 0.7f + (1f - themeOpacity) * 0.25f  // Rango 0.7 - 0.95
                Log.d(TAG, "Background opacity: $backgroundOpacity")
            } catch (e: Exception) {
                Log.e(TAG, "Error loading prefs", e)
            }
        }
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "onStartCommand: action=${intent?.action}")
        
        when (intent?.action) {
            ACTION_DISMISS_ALL -> dismissAllPopups()
            else -> intent?.let { handleNotification(it) }
        }
        return START_NOT_STICKY
    }
    
    private fun handleNotification(intent: Intent) {
        try {
            // Extraer datos
            val conversationId = intent.getStringExtra(EXTRA_CONVERSATION_ID) ?: ""
            val notificationKey = intent.getStringExtra(EXTRA_NOTIFICATION_KEY) ?: ""
            val packageName = intent.getStringExtra(EXTRA_PACKAGE_NAME) ?: ""
            val appName = intent.getStringExtra(EXTRA_APP_NAME) ?: "App"
            val author = intent.getStringExtra(EXTRA_AUTHOR) ?: "Anonimo"
            val content = intent.getStringExtra(EXTRA_CONTENT) ?: ""
            val timestamp = intent.getLongExtra(EXTRA_TIMESTAMP, System.currentTimeMillis())
            val isGroup = intent.getBooleanExtra(EXTRA_IS_GROUP, false)
            val senderInGroup = intent.getStringExtra(EXTRA_SENDER_IN_GROUP)
            
            Log.d(TAG, "Notification - ConvID: $conversationId, Author: $author, IsGroup: $isGroup")
            Log.d(TAG, "Raw content received: '$content'")  // Debug para ver el contenido original
            
            // Guardar referencia
            val contentIntent = pendingContentIntent
            pendingContentIntent = null
            
            // Verificar si ya existe un popup para esta conversacion
            val existingEntry = activeConversations[conversationId]
            
            if (existingEntry != null) {
                // Agregar mensaje al popup existente
                Log.d(TAG, "Adding message to existing conversation: $conversationId")
                addMessageToExistingPopup(existingEntry, content, timestamp, senderInGroup)
            } else {
                // Crear nuevo popup
                Log.d(TAG, "Creating new popup for conversation: $conversationId")
                
                // Si alcanzamos el maximo, remover la conversacion mas antigua
                if (activeConversations.size >= maxPopups) {
                    val oldestKey = activeConversations.keys.firstOrNull()
                    oldestKey?.let { 
                        Log.d(TAG, "Max popups reached, removing oldest: $it")
                        dismissConversation(it) 
                    }
                }
                
                // Crear mensaje inicial
                val formattedContent = ScientificNotification.formatMultimediaContent(content)
                val initialMessage = ConversationMessage(
                    content = formattedContent,
                    timestamp = timestamp,
                    sender = senderInGroup
                )
                
                val notification = ScientificNotification(
                    id = intent.getIntExtra(EXTRA_NOTIFICATION_ID, 0),
                    key = notificationKey,
                    packageName = packageName,
                    appName = appName,
                    author = author,
                    title = null,
                    content = formattedContent,
                    timestamp = timestamp,
                    icon = null,
                    largeIcon = null,
                    contentIntent = contentIntent,
                    replyAction = null,
                    actions = emptyList(),
                    conversationId = conversationId,
                    isGroup = isGroup,
                    senderInGroup = senderInGroup,
                    messages = listOf(initialMessage)
                )
                
                createPopup(notification, contentIntent)
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Error in handleNotification", e)
        }
    }
    
    /**
     * Agrega un mensaje a un popup existente
     */
    @SuppressLint("SetJavaScriptEnabled")
    private fun addMessageToExistingPopup(
        entry: PopupEntry,
        content: String,
        timestamp: Long,
        sender: String?
    ) {
        // Formatear el contenido para multimedia antes de agregar
        val formattedContent = ScientificNotification.formatMultimediaContent(content)
        
        // Agregar mensaje a la notificacion
        val updatedNotification = entry.notification.addMessage(formattedContent, timestamp, sender)
        
        // Limitar mensajes
        val limitedMessages = if (updatedNotification.messages.size > MAX_MESSAGES_PER_CONVERSATION) {
            updatedNotification.messages.takeLast(MAX_MESSAGES_PER_CONVERSATION)
        } else {
            updatedNotification.messages
        }
        
        val finalNotification = updatedNotification.copy(messages = limitedMessages)
        entry.notification = finalNotification
        
        // Actualizar la UI
        updatePopupContent(entry)
        
        // Animar para indicar nuevo mensaje
        animatePulse(entry.view)
        
        Log.d(TAG, "Message added. Total messages: ${finalNotification.messages.size}")
    }
    
    /**
     * Actualiza el contenido del WebView en el popup
     */
    @SuppressLint("SetJavaScriptEnabled")
    private fun updatePopupContent(entry: PopupEntry) {
        val notification = entry.notification
        val view = entry.view
        
        // Actualizar textos
        view.findViewById<TextView>(R.id.tvAuthor)?.text = notification.author
        view.findViewById<TextView>(R.id.tvAffiliation)?.text = notification.affiliation
        view.findViewById<TextView>(R.id.tvTimestamp)?.text = notification.timestampFormatted
        
        // Actualizar contador de mensajes
        val tvPopupCount = view.findViewById<TextView>(R.id.tvPopupCount)
        val msgCount = notification.messageCount
        if (msgCount > 1) {
            tvPopupCount?.visibility = View.VISIBLE
            tvPopupCount?.text = "($msgCount)"
        } else {
            tvPopupCount?.visibility = View.GONE
        }
        
        // Actualizar WebView con el contenido formateado
        val webView = view.findViewById<WebView>(R.id.wvContent)
        webView?.apply {
            val htmlContent = MarkdownHtmlGenerator.generateHtmlForPopup(
                markdown = notification.contentAsMarkdown,
                textColor = "#E8E8E8",    // Texto claro para tema dark
                accentColor = "#C9A227",
                maxLines = if (msgCount > 3) 0 else 6  // Sin limite si hay muchos mensajes
            )
            
            // baseURL ya no es necesario porque scripts son inline
            loadDataWithBaseURL(
                null,
                htmlContent,
                "text/html",
                "UTF-8",
                null
            )
        }
    }
    
    @SuppressLint("SetJavaScriptEnabled")
    private fun createPopup(
        notification: ScientificNotification,
        contentIntent: android.app.PendingIntent?
    ) {
        try {
            val popupIndex = activeConversations.size
            Log.d(TAG, "Creating popup #$popupIndex for: ${notification.conversationId}")
            
            // Inflar la vista
            val inflater = getSystemService(LAYOUT_INFLATER_SERVICE) as LayoutInflater
            val view = inflater.inflate(R.layout.floating_notification, null)
            
            // ═══════════════════════════════════════════════════════════════
            // APLICAR TEMA DARK CON OPACIDAD
            // ═══════════════════════════════════════════════════════════════
            applyDarkTheme(view)
            
            // Configurar contenido
            view.findViewById<TextView>(R.id.tvJournalName)?.text = notification.journalName
            view.findViewById<TextView>(R.id.tvAuthor)?.text = notification.author
            view.findViewById<TextView>(R.id.tvAffiliation)?.text = notification.affiliation
            view.findViewById<TextView>(R.id.tvTimestamp)?.text = notification.timestampFormatted
            
            // Contador inicial
            val tvPopupCount = view.findViewById<TextView>(R.id.tvPopupCount)
            tvPopupCount?.visibility = View.GONE
            
            // Configurar WebView para contenido Markdown/LaTeX
            val webView = view.findViewById<WebView>(R.id.wvContent)
            webView?.apply {
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.loadWithOverviewMode = true
                settings.useWideViewPort = false
                settings.allowContentAccess = true
                settings.allowFileAccess = true
                settings.blockNetworkLoads = false
                settings.loadsImagesAutomatically = true
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                }
                
                // Fondo transparente
                setBackgroundColor(android.graphics.Color.TRANSPARENT)
                
                // Cliente web que permite carga de recursos externos
                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                        return false
                    }
                }
                
                // Generar HTML con Markdown y KaTeX - COLORES PARA TEMA DARK
                val htmlContent = MarkdownHtmlGenerator.generateHtmlForPopup(
                    markdown = notification.contentAsMarkdown,
                    textColor = "#E8E8E8",    // Texto claro para fondo oscuro
                    accentColor = "#C9A227",  // Dorado acento
                    maxLines = 6
                )
                
                // Cargar contenido (baseURL ya no es necesario porque scripts son inline)
                loadDataWithBaseURL(
                    null,
                    htmlContent,
                    "text/html",
                    "UTF-8",
                    null
                )
                
                Log.d(TAG, "WebView loaded with content")
            }
            
            // Configurar parametros de ventana
            val displayMetrics = resources.displayMetrics
            val screenWidth = displayMetrics.widthPixels
            val screenHeight = displayMetrics.heightPixels
            
            val params = WindowManager.LayoutParams(
                (screenWidth * 0.9f).toInt(),
                WindowManager.LayoutParams.WRAP_CONTENT,
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                } else {
                    @Suppress("DEPRECATION")
                    WindowManager.LayoutParams.TYPE_PHONE
                },
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT
            ).apply {
                gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                x = popupIndex * STACK_OFFSET_X
                y = (screenHeight * 0.12f).toInt() + (popupIndex * STACK_OFFSET_Y)
            }
            
            // Configurar arrastre
            setupDragListener(view, params)
            
            // Crear entrada
            val entry = PopupEntry(
                view = view,
                params = params,
                notification = notification,
                contentIntent = contentIntent
            )
            
            // Botones
            setupButtons(view, notification.conversationId, contentIntent, notification.packageName)
            
            // Guardar en el mapa de conversaciones
            activeConversations[notification.conversationId] = entry
            
            // Agregar a WindowManager
            windowManager.addView(view, params)
            Log.d(TAG, "Popup added to WindowManager")
            
            // Animacion de entrada
            animateIn(view)
            
            // Actualizar botones de cerrar todo
            updateDismissAllButtons()
            
        } catch (e: Exception) {
            Log.e(TAG, "Error creating popup", e)
        }
    }
    
    private fun setupButtons(
        view: View, 
        conversationId: String,
        contentIntent: android.app.PendingIntent?,
        packageName: String
    ) {
        // Boton cerrar (X)
        view.findViewById<View>(R.id.btnClose)?.setOnClickListener {
            dismissConversation(conversationId)
        }
        
        // Boton OK
        view.findViewById<View>(R.id.btnOk)?.setOnClickListener {
            dismissConversation(conversationId)
        }
        
        // Boton Abrir
        view.findViewById<View>(R.id.btnOpen)?.setOnClickListener {
            openSourceApp(contentIntent, packageName)
            dismissConversation(conversationId)
        }
        
        // Boton Cerrar Todo
        val btnDismissAll = view.findViewById<View>(R.id.btnDismissAll)
        btnDismissAll?.setOnClickListener {
            dismissAllPopups()
        }
    }
    
    private fun setupDragListener(view: View, params: WindowManager.LayoutParams) {
        var initialX = 0
        var initialY = 0
        var initialTouchX = 0f
        var initialTouchY = 0f
        var isDragging = false
        
        // El header es la zona de arrastre
        val dragHandle = view.findViewById<View>(R.id.headerDragArea) ?: view
        
        dragHandle.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    isDragging = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.rawX - initialTouchX
                    val dy = event.rawY - initialTouchY
                    
                    if (abs(dx) > 10 || abs(dy) > 10) {
                        isDragging = true
                    }
                    
                    if (isDragging) {
                        params.x = initialX + dx.toInt()
                        params.y = initialY + dy.toInt()
                        try {
                            windowManager.updateViewLayout(view, params)
                        } catch (e: Exception) {
                            // Vista ya removida
                        }
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    isDragging
                }
                else -> false
            }
        }
    }
    
    private fun animateIn(view: View) {
        view.alpha = 0f
        view.scaleX = 0.9f
        view.scaleY = 0.9f
        
        view.animate()
            .alpha(1f)
            .scaleX(1f)
            .scaleY(1f)
            .setDuration(200)
            .setInterpolator(DecelerateInterpolator())
            .start()
    }
    
    /**
     * Animacion de pulso para indicar nuevo mensaje
     */
    private fun animatePulse(view: View) {
        view.animate()
            .scaleX(1.02f)
            .scaleY(1.02f)
            .setDuration(100)
            .withEndAction {
                view.animate()
                    .scaleX(1f)
                    .scaleY(1f)
                    .setDuration(100)
                    .start()
            }
            .start()
    }
    
    private fun dismissConversation(conversationId: String) {
        val entry = activeConversations[conversationId] ?: return
        Log.d(TAG, "Dismissing conversation: $conversationId")
        
        entry.view.animate()
            .alpha(0f)
            .scaleX(0.9f)
            .scaleY(0.9f)
            .setDuration(150)
            .setInterpolator(DecelerateInterpolator())
            .withEndAction {
                removePopupView(entry)
                activeConversations.remove(conversationId)
                updateDismissAllButtons()
                
                if (activeConversations.isEmpty()) {
                    stopSelf()
                }
            }
            .start()
    }
    
    private fun dismissAllPopups() {
        Log.d(TAG, "Dismissing ALL conversations (${activeConversations.size})")
        val entriesCopy = activeConversations.values.toList()
        activeConversations.clear()
        
        entriesCopy.forEachIndexed { index, entry ->
            entry.view.animate()
                .alpha(0f)
                .scaleX(0.9f)
                .scaleY(0.9f)
                .setStartDelay((index * 30).toLong())
                .setDuration(150)
                .setInterpolator(DecelerateInterpolator())
                .withEndAction {
                    removePopupView(entry)
                }
                .start()
        }
        
        scope.launch {
            delay(200 + (entriesCopy.size * 30).toLong())
            stopSelf()
        }
    }
    
    private fun removePopupView(entry: PopupEntry) {
        try {
            windowManager.removeView(entry.view)
        } catch (e: Exception) {
            Log.w(TAG, "View already removed")
        }
    }
    
    /**
     * Actualiza los botones "Cerrar Todo" en todos los popups
     */
    private fun updateDismissAllButtons() {
        val total = activeConversations.size
        
        activeConversations.values.forEach { entry ->
            val btnDismissAll = entry.view.findViewById<View>(R.id.btnDismissAll)
            val tvDismissCount = entry.view.findViewById<TextView>(R.id.tvDismissAllCount)
            
            if (total > 1) {
                btnDismissAll?.visibility = View.VISIBLE
                tvDismissCount?.text = "CERRAR TODO ($total)"
            } else {
                btnDismissAll?.visibility = View.GONE
            }
        }
    }
    
    /**
     * Aplica el tema DARK con opacidad al popup
     * Colores claros sobre fondo oscuro translucido
     */
    private fun applyDarkTheme(view: View) {
        // Colores del tema dark
        val bgAlpha = (backgroundOpacity * 255).toInt()
        val darkBgColor = Color.argb(bgAlpha, 24, 24, 24)  // #181818 con opacidad
        val textPrimary = Color.parseColor("#E8E8E8")
        val textSecondary = Color.parseColor("#A0A0A0")
        val accentColor = Color.parseColor("#C9A227")
        val dividerColor = Color.parseColor("#30FFFFFF")
        
        // Fondo principal del popup
        val mainContainer = (view as? ViewGroup)?.getChildAt(0) as? LinearLayout
        mainContainer?.let { container ->
            val bgDrawable = GradientDrawable().apply {
                cornerRadius = 12f * resources.displayMetrics.density
                setColor(darkBgColor)
                setStroke(
                    (1 * resources.displayMetrics.density).toInt(),
                    Color.parseColor("#30FFFFFF")
                )
            }
            container.background = bgDrawable
        }
        
        // Header
        view.findViewById<View>(R.id.headerDragArea)?.setBackgroundColor(Color.parseColor("#10FFFFFF"))
        
        // Textos del header
        view.findViewById<TextView>(R.id.tvJournalName)?.setTextColor(textSecondary)
        view.findViewById<TextView>(R.id.btnClose)?.setTextColor(textSecondary)
        view.findViewById<TextView>(R.id.tvPopupCount)?.setTextColor(accentColor)
        
        // Cuerpo
        view.findViewById<TextView>(R.id.tvAuthor)?.setTextColor(textPrimary)
        view.findViewById<TextView>(R.id.tvAffiliation)?.setTextColor(textSecondary)
        view.findViewById<TextView>(R.id.tvTimestamp)?.setTextColor(textSecondary)
        
        // Botones
        view.findViewById<TextView>(R.id.btnOpen)?.setTextColor(textSecondary)
        view.findViewById<TextView>(R.id.btnOk)?.setTextColor(accentColor)
        view.findViewById<TextView>(R.id.tvDismissAllCount)?.setTextColor(textSecondary)
        
        // Líneas divisoras - hacerlas semitransparentes claras
        // Las Views de 1dp de altura son divisores
    }
    
    private fun openSourceApp(contentIntent: android.app.PendingIntent?, packageName: String) {
        try {
            contentIntent?.send()
        } catch (e: Exception) {
            val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
            if (launchIntent != null) {
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(launchIntent)
            }
        }
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    override fun onDestroy() {
        Log.d(TAG, "Service onDestroy")
        activeConversations.values.forEach { removePopupView(it) }
        activeConversations.clear()
        scope.cancel()
        super.onDestroy()
    }
}
