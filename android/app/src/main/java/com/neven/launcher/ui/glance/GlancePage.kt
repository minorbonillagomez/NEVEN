package com.neven.launcher.ui.glance

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.provider.CalendarContract
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.neven.launcher.R
import com.neven.launcher.data.CalendarPreferencesRepository
import com.neven.launcher.data.LauncherPage
import com.neven.launcher.data.WidgetType
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import java.text.SimpleDateFormat
import java.util.*

/**
 * Página Glance estilo Microsoft Launcher
 * 
 * Muestra información contextual:
 * - Widget de calendario (próximos eventos)
 * - Widget de clima (futuro)
 * - Notas rápidas (futuro)
 */
@Composable
fun GlancePage(
    page: LauncherPage,
    colors: NevenColors,
    onOpenCalendar: () -> Unit
) {
    val context = LocalContext.current
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
            .padding(horizontal = 24.dp, vertical = 32.dp)
    ) {
        // Fecha actual (sin título "Glance")
        val currentDate = remember {
            SimpleDateFormat("EEEE, d MMMM", Locale.getDefault()).format(Date())
                .replaceFirstChar { it.uppercase() }
        }
        
        Text(
            text = currentDate,
            style = MaterialTheme.typography.headlineMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Light,
                letterSpacing = 1.sp
            ),
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        // Widgets según configuración
        page.widgets.forEach { widget ->
            when (widget.type) {
                WidgetType.CALENDAR -> {
                    CalendarWidget(
                        colors = colors,
                        onEventClick = { /* TODO */ },
                        onOpenCalendar = onOpenCalendar
                    )
                }
                // Weather ahora está integrado en el reloj de HOME
                WidgetType.WEATHER -> {
                    // No mostrar en Glance
                }
                else -> {
                    // Widget no soportado aún
                }
            }
            
            Spacer(modifier = Modifier.height(24.dp))
        }
        
        // Si no hay widgets, mostrar el calendario por defecto
        if (page.widgets.isEmpty()) {
            CalendarWidget(
                colors = colors,
                onEventClick = { /* TODO */ },
                onOpenCalendar = onOpenCalendar
            )
        }
    }
}

/**
 * Widget de Calendario
 * 
 * Muestra los próximos eventos del calendario del dispositivo
 * Respeta las preferencias del usuario sobre qué calendarios mostrar
 */
@Composable
fun CalendarWidget(
    colors: NevenColors,
    maxEvents: Int = 5,
    onEventClick: (CalendarEvent) -> Unit,
    onOpenCalendar: () -> Unit
) {
    val context = LocalContext.current
    val calendarPrefs = remember { CalendarPreferencesRepository(context) }
    
    // Calendarios ocultos por el usuario
    val hiddenCalendars by calendarPrefs.hiddenCalendarIds.collectAsState(initial = emptySet())
    
    // Estado del permiso
    var hasPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_CALENDAR
            ) == PackageManager.PERMISSION_GRANTED
        )
    }
    
    // Launcher para solicitar permiso
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        hasPermission = isGranted
    }
    
    // Cargar eventos (se recarga cuando cambia el permiso o los calendarios ocultos)
    val events by produceState<List<CalendarEvent>>(
        initialValue = emptyList(),
        key1 = hasPermission,
        key2 = hiddenCalendars
    ) {
        value = if (hasPermission) {
            loadCalendarEvents(context, maxEvents, hiddenCalendars)
        } else {
            emptyList()
        }
    }
    
    Column(
        modifier = Modifier.fillMaxWidth()
    ) {
        // Header del widget
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onOpenCalendar() },
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "◈",  // Símbolo de calendario científico
                    fontSize = 20.sp,
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                Text(
                    text = stringResource(R.string.calendar_title),
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Medium
                    ),
                    color = colors.textPrimary
                )
            }
            
            Text(
                text = "→",
                style = MaterialTheme.typography.titleMedium,
                color = colors.textSecondary
            )
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Contenido del widget
        if (!hasPermission) {
            // Sin permiso - mostrar botón para solicitar
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        // Solicitar permiso de calendario
                        permissionLauncher.launch(Manifest.permission.READ_CALENDAR)
                    }
                    .padding(vertical = 12.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "📅",
                    fontSize = 32.sp
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = stringResource(R.string.calendar_no_permission),
                    style = MaterialTheme.typography.bodyMedium.copy(
                        fontFamily = NevenFontFamily
                    ),
                    color = colors.accent,
                    fontWeight = FontWeight.Medium
                )
                
                Spacer(modifier = Modifier.height(4.dp))
                
                Text(
                    text = "Toca aquí para permitir acceso",
                    style = MaterialTheme.typography.bodySmall.copy(
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic
                    ),
                    color = colors.textSecondary
                )
            }
        } else if (events.isEmpty()) {
            // Sin eventos - mostrar mensaje y ayuda para Outlook
            Column(
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = stringResource(R.string.calendar_no_events),
                    style = MaterialTheme.typography.bodyMedium.copy(
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic
                    ),
                    color = colors.textSecondary
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Mini ayuda para Outlook
                OutlookSyncMiniHelp(
                    colors = colors,
                    context = context
                )
            }
        } else {
            // Lista de eventos agrupados por día
            val groupedEvents = events.groupBy { it.getDayOfYear() }
            
            groupedEvents.forEach { (_, dayEvents) ->
                // Encabezado del día
                val firstEvent = dayEvents.first()
                
                Text(
                    text = firstEvent.fullDateFormatted,
                    style = MaterialTheme.typography.labelMedium.copy(
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.SemiBold,
                        letterSpacing = 0.5.sp
                    ),
                    color = colors.accent,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
                
                // Eventos de ese día
                dayEvents.forEach { event ->
                    CalendarEventItem(
                        event = event,
                        colors = colors,
                        onClick = { onEventClick(event) }
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                }
                
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

/**
 * Item de evento de calendario
 */
@Composable
private fun CalendarEventItem(
    event: CalendarEvent,
    colors: NevenColors,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.Top
    ) {
        // Indicador de tiempo
        Column(
            modifier = Modifier.width(60.dp),
            horizontalAlignment = Alignment.End
        ) {
            Text(
                text = event.timeFormatted,
                style = MaterialTheme.typography.bodySmall.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium
                ),
                color = colors.accent
            )
            
            if (event.isAllDay) {
                Text(
                    text = "Todo el día",
                    style = MaterialTheme.typography.labelSmall.copy(
                        fontFamily = NevenFontFamily
                    ),
                    color = colors.textSecondary,
                    fontSize = 10.sp
                )
            }
        }
        
        Spacer(modifier = Modifier.width(16.dp))
        
        // Línea vertical decorativa con color del calendario
        Box(
            modifier = Modifier
                .width(3.dp)
                .height(44.dp)
                .padding(vertical = 2.dp)
        ) {
            val lineColor = if (event.calendarColor != 0) {
                androidx.compose.ui.graphics.Color(event.calendarColor)
            } else {
                colors.accent
            }
            androidx.compose.foundation.Canvas(modifier = Modifier.fillMaxSize()) {
                drawLine(
                    color = lineColor,
                    start = androidx.compose.ui.geometry.Offset(size.width / 2, 0f),
                    end = androidx.compose.ui.geometry.Offset(size.width / 2, size.height),
                    strokeWidth = 3f
                )
            }
        }
        
        Spacer(modifier = Modifier.width(16.dp))
        
        // Detalles del evento
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = event.title,
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Normal
                ),
                color = colors.textPrimary,
                maxLines = 2
            )
            
            if (event.location.isNotEmpty()) {
                Text(
                    text = "⌖ ${event.location}",
                    style = MaterialTheme.typography.bodySmall.copy(
                        fontFamily = NevenFontFamily
                    ),
                    color = colors.textSecondary,
                    maxLines = 1
                )
            }
            
            // Indicador del calendario (sin tiempo relativo, ya que se muestra en el encabezado)
            if (event.calendarDisplayName.isNotEmpty()) {
                Text(
                    text = event.calendarDisplayName,
                    style = MaterialTheme.typography.labelSmall.copy(
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic
                    ),
                    color = colors.textSecondary.copy(alpha = 0.6f)
                )
            }
        }
    }
}

/**
 * Modelo de evento de calendario
 */
data class CalendarEvent(
    val id: Long,
    val title: String,
    val startTime: Long,
    val endTime: Long,
    val location: String = "",
    val isAllDay: Boolean = false,
    val calendarColor: Int = 0,
    val calendarName: String = "",
    val accountName: String = ""
) {
    val timeFormatted: String
        get() {
            return if (isAllDay) {
                "∞"
            } else {
                SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(startTime))
            }
        }
    
    /**
     * Fecha del evento formateada
     * Muestra: "Hoy", "Mañana", o "Lun 28" para otros días
     */
    val dateFormatted: String
        get() {
            val now = Calendar.getInstance()
            val eventDate = Calendar.getInstance().apply { timeInMillis = startTime }
            
            return when {
                // Mismo día
                now.get(Calendar.YEAR) == eventDate.get(Calendar.YEAR) &&
                now.get(Calendar.DAY_OF_YEAR) == eventDate.get(Calendar.DAY_OF_YEAR) -> "Hoy"
                
                // Mañana
                now.get(Calendar.YEAR) == eventDate.get(Calendar.YEAR) &&
                now.get(Calendar.DAY_OF_YEAR) + 1 == eventDate.get(Calendar.DAY_OF_YEAR) -> "Mañana"
                
                // Otro día - mostrar día de la semana y número
                else -> {
                    SimpleDateFormat("EEE d", Locale.getDefault()).format(Date(startTime))
                        .replaceFirstChar { it.uppercase() }
                }
            }
        }
    
    /**
     * Fecha completa para mostrar en el encabezado de grupo
     * Ejemplo: "Lunes, 28 de octubre"
     */
    val fullDateFormatted: String
        get() {
            val now = Calendar.getInstance()
            val eventDate = Calendar.getInstance().apply { timeInMillis = startTime }
            
            return when {
                now.get(Calendar.YEAR) == eventDate.get(Calendar.YEAR) &&
                now.get(Calendar.DAY_OF_YEAR) == eventDate.get(Calendar.DAY_OF_YEAR) -> "Hoy"
                
                now.get(Calendar.YEAR) == eventDate.get(Calendar.YEAR) &&
                now.get(Calendar.DAY_OF_YEAR) + 1 == eventDate.get(Calendar.DAY_OF_YEAR) -> "Mañana"
                
                else -> SimpleDateFormat("EEEE, d 'de' MMMM", Locale.getDefault())
                    .format(Date(startTime))
                    .replaceFirstChar { it.uppercase() }
            }
        }
    
    val relativeTime: String
        get() {
            val now = System.currentTimeMillis()
            val diff = startTime - now
            
            return when {
                diff < 0 -> "En curso"
                diff < 60 * 60 * 1000 -> "En ${diff / (60 * 1000)} min"
                diff < 24 * 60 * 60 * 1000 -> "Hoy"
                diff < 48 * 60 * 60 * 1000 -> "Mañana"
                else -> {
                    SimpleDateFormat("EEE d", Locale.getDefault()).format(Date(startTime))
                }
            }
        }
    
    /**
     * Nombre corto del calendario para mostrar en la UI
     * Ejemplo: "Outlook" o "Gmail" en vez del email completo
     */
    val calendarDisplayName: String
        get() {
            return when {
                accountName.contains("outlook", ignoreCase = true) -> "Outlook"
                accountName.contains("hotmail", ignoreCase = true) -> "Outlook"
                accountName.contains("live.com", ignoreCase = true) -> "Outlook"
                accountName.contains("gmail", ignoreCase = true) -> "Gmail"
                accountName.contains("google", ignoreCase = true) -> "Google"
                calendarName.isNotEmpty() -> calendarName.take(15)
                else -> ""
            }
        }
    
    /**
     * Obtener el día del año para agrupar eventos
     */
    fun getDayOfYear(): Int {
        val cal = Calendar.getInstance().apply { timeInMillis = startTime }
        return cal.get(Calendar.YEAR) * 1000 + cal.get(Calendar.DAY_OF_YEAR)
    }
}

/**
 * Cargar eventos del calendario del dispositivo
 * Lee de TODOS los calendarios sincronizados (Gmail, Outlook, Samsung, etc.)
 * excepto los que el usuario haya ocultado en la configuración
 */
private fun loadCalendarEvents(
    context: Context, 
    maxEvents: Int,
    hiddenCalendarIds: Set<String> = emptySet()
): List<CalendarEvent> {
    val events = mutableListOf<CalendarEvent>()
    
    try {
        // Primero, obtener información de todos los calendarios disponibles
        val calendarsMap = mutableMapOf<Long, Pair<String, String>>() // calendarId -> (displayName, accountName)
        
        context.contentResolver.query(
            CalendarContract.Calendars.CONTENT_URI,
            arrayOf(
                CalendarContract.Calendars._ID,
                CalendarContract.Calendars.CALENDAR_DISPLAY_NAME,
                CalendarContract.Calendars.ACCOUNT_NAME,
                CalendarContract.Calendars.VISIBLE
            ),
            "${CalendarContract.Calendars.VISIBLE} = 1", // Solo calendarios visibles
            null,
            null
        )?.use { cursor ->
            val idIdx = cursor.getColumnIndex(CalendarContract.Calendars._ID)
            val displayNameIdx = cursor.getColumnIndex(CalendarContract.Calendars.CALENDAR_DISPLAY_NAME)
            val accountNameIdx = cursor.getColumnIndex(CalendarContract.Calendars.ACCOUNT_NAME)
            
            while (cursor.moveToNext()) {
                val calId = cursor.getLong(idIdx)
                // Solo incluir calendarios que no estén ocultos por el usuario
                if (!hiddenCalendarIds.contains(calId.toString())) {
                    val displayName = cursor.getString(displayNameIdx) ?: ""
                    val accountName = cursor.getString(accountNameIdx) ?: ""
                    calendarsMap[calId] = Pair(displayName, accountName)
                }
            }
        }
        
        // Si todos los calendarios están ocultos, retornar vacío
        if (calendarsMap.isEmpty()) {
            return emptyList()
        }
        
        val now = System.currentTimeMillis()
        val endRange = now + (7 * 24 * 60 * 60 * 1000) // Próximos 7 días
        
        val projection = arrayOf(
            CalendarContract.Events._ID,
            CalendarContract.Events.TITLE,
            CalendarContract.Events.DTSTART,
            CalendarContract.Events.DTEND,
            CalendarContract.Events.EVENT_LOCATION,
            CalendarContract.Events.ALL_DAY,
            CalendarContract.Events.CALENDAR_COLOR,
            CalendarContract.Events.CALENDAR_ID
        )
        
        // Filtrar solo eventos de calendarios habilitados
        val calendarIdsList = calendarsMap.keys.joinToString(",")
        val selection = "${CalendarContract.Events.DTSTART} >= ? AND " +
                       "${CalendarContract.Events.DTSTART} <= ? AND " +
                       "${CalendarContract.Events.CALENDAR_ID} IN ($calendarIdsList)"
        val selectionArgs = arrayOf(now.toString(), endRange.toString())
        val sortOrder = "${CalendarContract.Events.DTSTART} ASC"
        
        context.contentResolver.query(
            CalendarContract.Events.CONTENT_URI,
            projection,
            selection,
            selectionArgs,
            sortOrder
        )?.use { cursor ->
            val idIndex = cursor.getColumnIndex(CalendarContract.Events._ID)
            val titleIndex = cursor.getColumnIndex(CalendarContract.Events.TITLE)
            val startIndex = cursor.getColumnIndex(CalendarContract.Events.DTSTART)
            val endIndex = cursor.getColumnIndex(CalendarContract.Events.DTEND)
            val locationIndex = cursor.getColumnIndex(CalendarContract.Events.EVENT_LOCATION)
            val allDayIndex = cursor.getColumnIndex(CalendarContract.Events.ALL_DAY)
            val colorIndex = cursor.getColumnIndex(CalendarContract.Events.CALENDAR_COLOR)
            val calendarIdIndex = cursor.getColumnIndex(CalendarContract.Events.CALENDAR_ID)
            
            while (cursor.moveToNext() && events.size < maxEvents) {
                val calendarId = cursor.getLong(calendarIdIndex)
                val calendarInfo = calendarsMap[calendarId]
                
                // Solo incluir si el calendario está en nuestro mapa (no oculto)
                if (calendarInfo != null) {
                    val event = CalendarEvent(
                        id = cursor.getLong(idIndex),
                        title = cursor.getString(titleIndex) ?: "Sin título",
                        startTime = cursor.getLong(startIndex),
                        endTime = cursor.getLong(endIndex),
                        location = cursor.getString(locationIndex) ?: "",
                        isAllDay = cursor.getInt(allDayIndex) == 1,
                        calendarColor = cursor.getInt(colorIndex),
                        calendarName = calendarInfo.first,
                        accountName = calendarInfo.second
                    )
                    events.add(event)
                }
            }
        }
    } catch (e: Exception) {
        e.printStackTrace()
    }
    
    return events
}

/**
 * Mini ayuda para sincronizar Outlook
 * Aparece en la página Glance cuando no hay eventos
 */
@Composable
private fun OutlookSyncMiniHelp(
    colors: NevenColors,
    context: Context
) {
    // Verificar si Outlook está instalado
    val outlookInstalled = remember {
        try {
            context.packageManager.getPackageInfo("com.microsoft.office.outlook", 0)
            true
        } catch (e: Exception) {
            false
        }
    }
    
    if (!outlookInstalled) return
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable {
                // Abrir Outlook
                try {
                    val intent = context.packageManager.getLaunchIntentForPackage("com.microsoft.office.outlook")
                    if (intent != null) {
                        context.startActivity(intent)
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            .padding(vertical = 8.dp)
    ) {
        Text(
            text = "¿Usas Outlook?",
            style = MaterialTheme.typography.labelMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium
            ),
            color = colors.accent
        )
        
        Spacer(modifier = Modifier.height(4.dp))
        
        Text(
            text = "Activa \"Sincronizar calendarios\" en Outlook → Configuración → tu cuenta",
            style = MaterialTheme.typography.labelSmall.copy(
                fontFamily = NevenFontFamily
            ),
            color = colors.textSecondary
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Abrir Outlook",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium
                ),
                color = colors.accent
            )
            
            Text(
                text = " →",
                style = MaterialTheme.typography.labelSmall,
                color = colors.accent
            )
        }
    }
}
