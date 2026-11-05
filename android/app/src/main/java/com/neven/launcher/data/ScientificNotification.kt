package com.neven.launcher.data

import android.app.Notification
import android.app.PendingIntent
import android.app.RemoteInput
import android.graphics.drawable.Drawable
import android.graphics.drawable.Icon
import android.service.notification.StatusBarNotification
import java.text.SimpleDateFormat
import java.util.*

/**
 * Representa un mensaje individual dentro de una conversacion
 */
data class ConversationMessage(
    val content: String,
    val timestamp: Long,
    val sender: String? = null  // null para chats 1:1, nombre del sender para grupos
) {
    val timeFormatted: String
        get() = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(timestamp))
}

/**
 * Modelo de notificacion cientifica
 * 
 * Representa una notificacion en formato de paper academico:
 * - Title (Journal): Nombre de la aplicacion
 * - Author: Remitente del mensaje (o nombre del grupo)
 * - Abstract: Contenido del mensaje (o thread de mensajes)
 * - Received: Timestamp
 * 
 * Soporta agrupacion de mensajes de la misma conversacion
 */
data class ScientificNotification(
    val id: Int,
    val key: String,
    val packageName: String,
    val appName: String,
    val author: String,
    val title: String?,
    val content: String,
    val timestamp: Long,
    val icon: Icon?,
    val largeIcon: Icon?,
    val contentIntent: PendingIntent?,
    val replyAction: ReplyAction?,
    val actions: List<NotificationAction>,
    // Nuevos campos para agrupacion
    val conversationId: String = "",        // Identificador unico de la conversacion
    val isGroup: Boolean = false,           // Si es un chat grupal
    val senderInGroup: String? = null,      // Quien envio el mensaje (solo en grupos)
    val messages: List<ConversationMessage> = emptyList()  // Thread de mensajes
) {
    /**
     * Nombre de la app formateado para el "Journal" del paper
     * Ejemplo: "WhatsApp" → "W H A T S A P P"
     */
    val journalName: String
        get() = appName.uppercase().toList().joinToString(" ")
    
    /**
     * Afiliacion basada en el tipo de app y si es grupo
     */
    val affiliation: String
        get() {
            val baseAffiliation = when {
                packageName.contains("whatsapp", ignoreCase = true) -> "Mensajeria Instantanea"
                packageName.contains("telegram", ignoreCase = true) -> "Comunicaciones Cifradas"
                packageName.contains("messenger", ignoreCase = true) -> "Redes Sociales"
                packageName.contains("sms", ignoreCase = true) || 
                packageName.contains("messaging", ignoreCase = true) ||
                packageName.contains("mms", ignoreCase = true) -> "Telecomunicaciones"
                packageName.contains("gmail", ignoreCase = true) ||
                packageName.contains("mail", ignoreCase = true) -> "Correspondencia Digital"
                packageName.contains("slack", ignoreCase = true) -> "Colaboracion Empresarial"
                packageName.contains("discord", ignoreCase = true) -> "Comunicaciones Gaming"
                packageName.contains("teams", ignoreCase = true) -> "Productividad Corporativa"
                packageName.contains("signal", ignoreCase = true) -> "Privacidad Criptografica"
                else -> "Notificaciones"
            }
            
            return if (isGroup) {
                "Symposium de $baseAffiliation"
            } else {
                "Dept. de $baseAffiliation"
            }
        }
    
    /**
     * Timestamp formateado estilo academico
     * Para threads, muestra rango de tiempo
     */
    val timestampFormatted: String
        get() {
            if (messages.size > 1) {
                val first = messages.minOf { it.timestamp }
                val last = messages.maxOf { it.timestamp }
                val timeFirst = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(first))
                val timeLast = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(last))
                val date = SimpleDateFormat("MMM d, yyyy", Locale.getDefault()).format(Date(last))
                return "Received: $timeFirst - $timeLast | $date"
            }
            
            val time = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(timestamp))
            val date = SimpleDateFormat("MMM d, yyyy", Locale.getDefault()).format(Date(timestamp))
            return "Received: $time | $date"
        }
    
    /**
     * Timestamp corto para modo compacto
     */
    val timestampShort: String
        get() {
            val now = System.currentTimeMillis()
            val diff = now - timestamp
            
            return when {
                diff < 60_000 -> "Ahora"
                diff < 3600_000 -> "${diff / 60_000} min"
                diff < 86400_000 -> SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(timestamp))
                else -> SimpleDateFormat("d MMM", Locale.getDefault()).format(Date(timestamp))
            }
        }
    
    /**
     * Contenido formateado como Markdown
     * Para threads, formatea todos los mensajes
     * IMPORTANTE: Salto de linea despues del timestamp para que el Markdown se renderice correctamente
     */
    val contentAsMarkdown: String
        get() {
            if (messages.isEmpty()) return content
            
            return messages.joinToString("\n\n") { msg ->
                if (isGroup && msg.sender != null) {
                    // Salto de linea despues del header para que el contenido se renderice como Markdown
                    "**[${msg.timeFormatted} | ${msg.sender}]**\n${msg.content}"
                } else {
                    // Salto de linea despues del header para que el contenido se renderice como Markdown
                    "**[${msg.timeFormatted}]**\n${msg.content}"
                }
            }
        }
    
    /**
     * Numero de mensajes en la conversacion
     */
    val messageCount: Int
        get() = if (messages.isEmpty()) 1 else messages.size
    
    /**
     * Agrega un nuevo mensaje a la conversacion
     * Retorna una nueva instancia con el mensaje agregado
     * El contenido se formatea automáticamente para detectar multimedia
     */
    fun addMessage(newContent: String, newTimestamp: Long, sender: String? = null): ScientificNotification {
        // Formatear el contenido para detectar multimedia
        val formattedContent = Companion.formatMultimediaContent(newContent)
        
        val newMessage = ConversationMessage(
            content = formattedContent,
            timestamp = newTimestamp,
            sender = sender
        )
        
        val updatedMessages = if (messages.isEmpty()) {
            // Si es el primer mensaje, agregar el actual tambien
            listOf(
                ConversationMessage(content, timestamp, senderInGroup),
                newMessage
            )
        } else {
            messages + newMessage
        }
        
        return copy(
            messages = updatedMessages,
            timestamp = newTimestamp,  // Actualizar al mas reciente
            content = newContent       // El ultimo contenido
        )
    }
    
    /**
     * Preview del contenido (primeras líneas)
     */
    fun getPreview(maxLength: Int = 100): String {
        return if (content.length > maxLength) {
            content.take(maxLength).substringBeforeLast(' ') + "..."
        } else {
            content
        }
    }
    
    companion object {
        /**
         * Crea una ScientificNotification desde un StatusBarNotification
         */
        fun fromStatusBarNotification(
            sbn: StatusBarNotification,
            appName: String
        ): ScientificNotification {
            val notification = sbn.notification
            val extras = notification.extras
            
            // Extraer informacion del mensaje
            val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString()
            val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: ""
            val bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString()
            val subText = extras.getCharSequence(Notification.EXTRA_SUB_TEXT)?.toString()
            val summaryText = extras.getCharSequence(Notification.EXTRA_SUMMARY_TEXT)?.toString()
            
            // Detectar si es un grupo
            // En WhatsApp/Telegram, el subText suele contener el nombre del grupo
            // O el titulo es el grupo y el texto contiene "Sender: mensaje"
            val isGroup = detectIfGroup(sbn.packageName, title, text, subText, summaryText)
            
            // Extraer autor y sender segun sea grupo o chat individual
            val (author, senderInGroup, cleanContent) = if (isGroup) {
                extractGroupInfo(sbn.packageName, title, text, bigText, subText)
            } else {
                // Para chats individuales, también formatear el contenido multimedia
                Triple(title ?: "Anonimo", null, formatMultimediaContent(bigText ?: text))
            }
            
            // Generar ID de conversacion unico
            // Normalizar el autor para evitar duplicados por diferencias menores
            val normalizedAuthor = normalizeConversationKey(author)
            val conversationId = "${sbn.packageName}:$normalizedAuthor"
            
            // Extraer acciones de respuesta
            val replyAction = extractReplyAction(notification)
            val actions = extractActions(notification)
            
            // Crear mensaje inicial
            val initialMessage = ConversationMessage(
                content = cleanContent,
                timestamp = sbn.postTime,
                sender = senderInGroup
            )
            
            return ScientificNotification(
                id = sbn.id,
                key = sbn.key,
                packageName = sbn.packageName,
                appName = appName,
                author = author,
                title = subText,
                content = cleanContent,
                timestamp = sbn.postTime,
                icon = notification.smallIcon,
                largeIcon = notification.getLargeIcon(),
                contentIntent = notification.contentIntent,
                replyAction = replyAction,
                actions = actions,
                conversationId = conversationId,
                isGroup = isGroup,
                senderInGroup = senderInGroup,
                messages = listOf(initialMessage)
            )
        }
        
        /**
         * Detecta si la notificacion es de un chat grupal
         */
        private fun detectIfGroup(
            packageName: String,
            title: String?,
            text: String?,
            subText: String?,
            summaryText: String?
        ): Boolean {
            // WhatsApp: grupos tienen subText con cantidad de mensajes o nombre
            // El texto contiene "Sender: mensaje" pattern
            if (packageName.contains("whatsapp", ignoreCase = true)) {
                // Si el texto contiene ":", probablemente es grupo
                if (text?.contains(":") == true && !text.contains("http")) {
                    val colonIndex = text.indexOf(":")
                    // Verificar que antes del : hay un nombre corto (< 30 chars)
                    if (colonIndex in 1..30) {
                        return true
                    }
                }
                // Si hay summaryText, generalmente es grupo
                if (!summaryText.isNullOrBlank()) return true
            }
            
            // Telegram: similar pattern
            if (packageName.contains("telegram", ignoreCase = true)) {
                if (text?.contains(":") == true) {
                    val colonIndex = text.indexOf(":")
                    if (colonIndex in 1..30) {
                        return true
                    }
                }
            }
            
            // Discord: los canales/servidores son como grupos
            if (packageName.contains("discord", ignoreCase = true)) {
                if (!subText.isNullOrBlank()) return true
            }
            
            // Slack: canales son grupos
            if (packageName.contains("slack", ignoreCase = true)) {
                if (title?.startsWith("#") == true) return true
            }
            
            return false
        }
        
        /**
         * Extrae informacion de un chat grupal
         * @return Triple(nombreGrupo, senderDelMensaje, contenidoLimpio)
         */
        private fun extractGroupInfo(
            packageName: String,
            title: String?,
            text: String?,
            bigText: String?,
            subText: String?
        ): Triple<String, String?, String> {
            val content = bigText ?: text ?: ""
            
            // WhatsApp pattern: "Sender: mensaje"
            if (packageName.contains("whatsapp", ignoreCase = true) || 
                packageName.contains("telegram", ignoreCase = true)) {
                
                val colonIndex = content.indexOf(":")
                if (colonIndex in 1..30) {
                    val sender = content.substring(0, colonIndex).trim()
                    var message = content.substring(colonIndex + 1).trim()
                    
                    // Detectar y formatear contenido multimedia
                    message = formatMultimediaContent(message)
                    
                    // El grupo es el title (limpiando posibles "(N mensajes)")
                    val groupName = title?.replace(Regex("\\s*\\(\\d+\\s*(nuevos?\\s+)?mensajes?\\)", RegexOption.IGNORE_CASE), "")
                        ?.replace(Regex("\\s*\\(\\d+\\s*(new\\s+)?messages?\\)", RegexOption.IGNORE_CASE), "")
                        ?.trim() ?: "Grupo"
                    
                    return Triple(groupName, sender, message)
                }
            }
            
            // Discord/Slack: title es el canal, subText puede tener info adicional
            if (packageName.contains("discord", ignoreCase = true) ||
                packageName.contains("slack", ignoreCase = true)) {
                return Triple(title ?: "Canal", subText, content)
            }
            
            // Fallback: title es el grupo, no hay sender identificado
            return Triple(title ?: "Grupo", null, formatMultimediaContent(content))
        }
        
        /**
         * Detecta y formatea contenido multimedia en mensajes
         * Usa notación LaTeX científica con badges estilo fracción en caja
         * 
         * Diseño: $\boxed{\frac{\textbf{X}}{\text{xx}}}$
         * - Letra principal en negrita arriba
         * - Abreviatura en texto normal abajo
         * - Todo dentro de una caja
         * 
         * Esta función es pública para poder usarse desde otros componentes
         */
        fun formatMultimediaContent(content: String): String {
            // Si el contenido está vacío, retornar vacío
            if (content.isBlank()) {
                return content
            }
            
            var formatted = content
            
            // Badges LaTeX científicos para cada tipo de multimedia
            val BADGE_FIGURA = "\$\\boxed{\\frac{\\textbf{F}}{\\text{ig}}}\$"      // Imagen/Foto
            val BADGE_VIDEO = "\$\\boxed{\\frac{\\textbf{V}}{\\text{id}}}\$"       // Video
            val BADGE_AUDIO = "\$\\boxed{\\frac{\\textbf{A}}{\\text{ud}}}\$"       // Audio
            val BADGE_LINK = "\$\\boxed{\\frac{\\textbf{L}}{\\text{in}}}\$"        // Link/Enlace
            val BADGE_DOC = "\$\\boxed{\\frac{\\textbf{D}}{\\text{oc}}}\$"         // Documento
            val BADGE_VOZ = "\$\\boxed{\\frac{\\textbf{V}}{\\text{oz}}}\$"         // Nota de voz
            val BADGE_GIF = "\$\\boxed{\\frac{\\textbf{G}}{\\text{if}}}\$"         // GIF animado
            val BADGE_STICKER = "\$\\boxed{\\frac{\\textbf{S}}{\\text{tk}}}\$"     // Sticker
            val BADGE_UBICACION = "\$\\boxed{\\frac{\\textbf{U}}{\\text{bi}}}\$"   // Ubicación
            val BADGE_CONTACTO = "\$\\boxed{\\frac{\\textbf{C}}{\\text{to}}}\$"    // Contacto
            
            // Detectar indicadores de multimedia de WhatsApp/Telegram
            val multimediaPatterns = mapOf(
                // Imágenes
                Regex("📷\\s*Photo", RegexOption.IGNORE_CASE) to "$BADGE_FIGURA *Imagen adjunta*",
                Regex("📷\\s*Foto", RegexOption.IGNORE_CASE) to "$BADGE_FIGURA *Imagen adjunta*",
                Regex("📷", RegexOption.IGNORE_CASE) to BADGE_FIGURA,
                Regex("<Imagen>", RegexOption.IGNORE_CASE) to "$BADGE_FIGURA *Imagen adjunta*",
                Regex("<Image>", RegexOption.IGNORE_CASE) to "$BADGE_FIGURA *Imagen adjunta*",
                Regex("\\[Imagen\\]", RegexOption.IGNORE_CASE) to "$BADGE_FIGURA *Imagen adjunta*",
                Regex("\\[Image\\]", RegexOption.IGNORE_CASE) to "$BADGE_FIGURA *Imagen adjunta*",
                Regex("imagen omitida", RegexOption.IGNORE_CASE) to "$BADGE_FIGURA *Imagen omitida*",
                Regex("image omitted", RegexOption.IGNORE_CASE) to "$BADGE_FIGURA *Imagen omitida*",
                
                // Videos
                Regex("🎥\\s*Video", RegexOption.IGNORE_CASE) to "$BADGE_VIDEO *Video adjunto*",
                Regex("🎥", RegexOption.IGNORE_CASE) to BADGE_VIDEO,
                Regex("<Video>", RegexOption.IGNORE_CASE) to "$BADGE_VIDEO *Video adjunto*",
                Regex("\\[Video\\]", RegexOption.IGNORE_CASE) to "$BADGE_VIDEO *Video adjunto*",
                Regex("video omitido", RegexOption.IGNORE_CASE) to "$BADGE_VIDEO *Video omitido*",
                Regex("video omitted", RegexOption.IGNORE_CASE) to "$BADGE_VIDEO *Video omitido*",
                
                // Audio
                Regex("🎵\\s*Audio", RegexOption.IGNORE_CASE) to "$BADGE_AUDIO *Audio adjunto*",
                Regex("🎵", RegexOption.IGNORE_CASE) to BADGE_AUDIO,
                Regex("<Audio>", RegexOption.IGNORE_CASE) to "$BADGE_AUDIO *Audio adjunto*",
                Regex("\\[Audio\\]", RegexOption.IGNORE_CASE) to "$BADGE_AUDIO *Audio adjunto*",
                
                // Documentos
                Regex("📄\\s*Document", RegexOption.IGNORE_CASE) to "$BADGE_DOC *Documento adjunto*",
                Regex("📄\\s*Documento", RegexOption.IGNORE_CASE) to "$BADGE_DOC *Documento adjunto*",
                Regex("📄", RegexOption.IGNORE_CASE) to BADGE_DOC,
                Regex("<Document>", RegexOption.IGNORE_CASE) to "$BADGE_DOC *Documento adjunto*",
                Regex("<Documento>", RegexOption.IGNORE_CASE) to "$BADGE_DOC *Documento adjunto*",
                
                // Ubicación
                Regex("📍\\s*Location", RegexOption.IGNORE_CASE) to "$BADGE_UBICACION *Ubicación compartida*",
                Regex("📍\\s*Ubicación", RegexOption.IGNORE_CASE) to "$BADGE_UBICACION *Ubicación compartida*",
                Regex("📍", RegexOption.IGNORE_CASE) to BADGE_UBICACION,
                Regex("<Location>", RegexOption.IGNORE_CASE) to "$BADGE_UBICACION *Ubicación compartida*",
                Regex("<Ubicación>", RegexOption.IGNORE_CASE) to "$BADGE_UBICACION *Ubicación compartida*",
                
                // Notas de voz
                Regex("🎤\\s*Voice\\s*message", RegexOption.IGNORE_CASE) to "$BADGE_VOZ *Mensaje de voz*",
                Regex("🎤\\s*Mensaje\\s*de\\s*voz", RegexOption.IGNORE_CASE) to "$BADGE_VOZ *Mensaje de voz*",
                Regex("🎤", RegexOption.IGNORE_CASE) to BADGE_VOZ,
                Regex("audio omitido", RegexOption.IGNORE_CASE) to "$BADGE_VOZ *Audio omitido*",
                Regex("audio omitted", RegexOption.IGNORE_CASE) to "$BADGE_VOZ *Audio omitido*",
                
                // GIFs - múltiples formatos que usa WhatsApp
                Regex("<GIF>", RegexOption.IGNORE_CASE) to "$BADGE_GIF *GIF animado*",
                Regex("\\[GIF\\]", RegexOption.IGNORE_CASE) to "$BADGE_GIF *GIF animado*",
                Regex("GIF omitido", RegexOption.IGNORE_CASE) to "$BADGE_GIF *GIF omitido*",
                Regex("GIF omitted", RegexOption.IGNORE_CASE) to "$BADGE_GIF *GIF omitido*",
                Regex("🎬\\s*GIF", RegexOption.IGNORE_CASE) to "$BADGE_GIF *GIF animado*",
                Regex("🎞️\\s*GIF", RegexOption.IGNORE_CASE) to "$BADGE_GIF *GIF animado*",
                Regex("🎞\\s*GIF", RegexOption.IGNORE_CASE) to "$BADGE_GIF *GIF animado*",
                Regex("🎬", RegexOption.IGNORE_CASE) to BADGE_GIF,
                Regex("🎞️", RegexOption.IGNORE_CASE) to BADGE_GIF,
                Regex("🎞", RegexOption.IGNORE_CASE) to BADGE_GIF,
                
                // Stickers - múltiples formatos que usa WhatsApp
                Regex("<Sticker>", RegexOption.IGNORE_CASE) to "$BADGE_STICKER *Sticker*",
                Regex("\\[Sticker\\]", RegexOption.IGNORE_CASE) to "$BADGE_STICKER *Sticker*",
                Regex("sticker omitido", RegexOption.IGNORE_CASE) to "$BADGE_STICKER *Sticker omitido*",
                Regex("sticker omitted", RegexOption.IGNORE_CASE) to "$BADGE_STICKER *Sticker omitido*",
                Regex("🏷️\\s*Sticker", RegexOption.IGNORE_CASE) to "$BADGE_STICKER *Sticker*",
                Regex("🏷\\s*Sticker", RegexOption.IGNORE_CASE) to "$BADGE_STICKER *Sticker*",
                Regex("🏷️", RegexOption.IGNORE_CASE) to BADGE_STICKER,
                Regex("🏷", RegexOption.IGNORE_CASE) to BADGE_STICKER,
                // WhatsApp a veces usa estos emojis para stickers
                Regex("😀\\s*Sticker", RegexOption.IGNORE_CASE) to "$BADGE_STICKER *Sticker*",
                Regex("Sticker", RegexOption.IGNORE_CASE) to "$BADGE_STICKER *Sticker*",
                Regex("GIF", RegexOption.IGNORE_CASE) to "$BADGE_GIF *GIF animado*",
                
                // Contactos
                Regex("📇\\s*Contact", RegexOption.IGNORE_CASE) to "$BADGE_CONTACTO *Contacto compartido*",
                Regex("📇\\s*Contacto", RegexOption.IGNORE_CASE) to "$BADGE_CONTACTO *Contacto compartido*",
                Regex("📇", RegexOption.IGNORE_CASE) to BADGE_CONTACTO,
                Regex("<Contact>", RegexOption.IGNORE_CASE) to "$BADGE_CONTACTO *Contacto compartido*",
                Regex("<Contacto>", RegexOption.IGNORE_CASE) to "$BADGE_CONTACTO *Contacto compartido*"
            )
            
            for ((pattern, replacement) in multimediaPatterns) {
                formatted = formatted.replace(pattern, replacement)
            }
            
            // Detectar URLs y formatearlas con badge LaTeX + link Markdown
            // Pattern para URLs que no estén ya en formato Markdown [texto](url)
            val urlPattern = Regex("(?<!\\]\\()\\b(https?://[\\w\\-._~:/?#\\[\\]@!$&'()*+,;=%]+)", RegexOption.IGNORE_CASE)
            formatted = formatted.replace(urlPattern) { matchResult ->
                val url = matchResult.value
                // Extraer dominio para mostrar
                val domain = try {
                    url.replace(Regex("^https?://"), "")
                        .substringBefore("/")
                        .substringBefore("?")
                } catch (e: Exception) {
                    "link"
                }
                // Badge LaTeX para links
                "\$\\boxed{\\frac{\\textbf{L}}{\\text{in}}}\$ [$domain]($url)"
            }
            
            return formatted
        }
        
        /**
         * Normaliza el nombre de la conversacion para generar IDs consistentes
         * 
         * Maneja casos especiales de WhatsApp y otras apps de mensajeria:
         * - "Grupo: Persona" → extrae "Grupo" como clave
         * - "Grupo (N mensajes): Persona" → extrae "Grupo" como clave
         * - "Grupo (N nuevos mensajes): Persona" → extrae "Grupo" como clave
         * - Elimina emojis y caracteres especiales
         * - Normaliza espacios y capitalización
         */
        private fun normalizeConversationKey(name: String): String {
            var normalized = name.trim()
            
            // 1. Extraer solo el nombre del grupo/contacto base
            // Pattern: "NombreGrupo: Sender" o "NombreGrupo (N mensajes): Sender"
            // Queremos solo "NombreGrupo"
            
            // Primero eliminar el pattern "(N mensajes)" o "(N nuevos mensajes)"
            normalized = normalized
                .replace(Regex("\\s*\\(\\d+\\s*(nuevos?\\s+)?mensajes?\\)", RegexOption.IGNORE_CASE), "")
                .replace(Regex("\\s*\\(\\d+\\s*(new\\s+)?messages?\\)", RegexOption.IGNORE_CASE), "")
            
            // Si hay ":", tomar solo la parte antes (nombre del grupo/chat)
            // Pero solo si el ":" aparece como separador de grupo:sender, no como parte de un link
            val colonIndex = normalized.indexOf(":")
            if (colonIndex > 0 && colonIndex < 50) {
                // Verificar que no sea parte de un URL (http: o https:)
                val beforeColon = normalized.substring(0, colonIndex).lowercase()
                if (!beforeColon.endsWith("http") && !beforeColon.endsWith("https")) {
                    normalized = normalized.substring(0, colonIndex)
                }
            }
            
            // 2. Limpiar el nombre resultante
            return normalized
                .trim()
                .lowercase()
                .replace(Regex("\\s+"), " ")           // Multiples espacios a uno
                .replace(Regex("[^a-záéíóúñü0-9\\s]", RegexOption.IGNORE_CASE), "") // Alfanumerico + acentos
                .replace(" ", "_")                     // Espacios a guion bajo
                .take(50)                              // Limitar longitud
                .ifEmpty { "unknown" }
        }
        
        /**
         * Extrae la accion de respuesta rapida si existe
         */
        private fun extractReplyAction(notification: Notification): ReplyAction? {
            notification.actions?.forEach { action ->
                action.remoteInputs?.forEach { remoteInput ->
                    if (remoteInput.allowFreeFormInput) {
                        return ReplyAction(
                            actionIntent = action.actionIntent,
                            remoteInput = remoteInput,
                            label = action.title?.toString() ?: "Responder"
                        )
                    }
                }
            }
            return null
        }
        
        /**
         * Extrae las acciones disponibles
         */
        private fun extractActions(notification: Notification): List<NotificationAction> {
            return notification.actions?.map { action ->
                NotificationAction(
                    title = action.title?.toString() ?: "",
                    actionIntent = action.actionIntent,
                    icon = action.getIcon()
                )
            } ?: emptyList()
        }
    }
}

/**
 * Acción de respuesta rápida
 */
data class ReplyAction(
    val actionIntent: PendingIntent,
    val remoteInput: RemoteInput,
    val label: String
)

/**
 * Acción de notificación genérica
 */
data class NotificationAction(
    val title: String,
    val actionIntent: PendingIntent?,
    val icon: Icon?
)
