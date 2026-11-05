package com.neven.launcher.ui.settings

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.provider.CalendarContract
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.neven.launcher.data.CalendarInfo
import com.neven.launcher.data.CalendarPreferencesRepository
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.launch

/**
 * Pantalla de configuración de calendarios
 * Diseño consistente con el resto de pantallas de NEVEN
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CalendarSettingsScreen(
    colors: NevenColors,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { CalendarPreferencesRepository(context) }
    
    val hiddenCalendars by repository.hiddenCalendarIds.collectAsState(initial = emptySet())
    
    val hasPermission = remember {
        ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_CALENDAR
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    val calendars by produceState<List<CalendarInfo>>(
        initialValue = emptyList(),
        key1 = hasPermission
    ) {
        value = if (hasPermission) {
            loadAvailableCalendars(context, hiddenCalendars)
        } else {
            emptyList()
        }
    }
    
    val calendarsWithState = remember(calendars, hiddenCalendars) {
        calendars.map { cal ->
            cal.copy(isEnabled = !hiddenCalendars.contains(cal.id.toString()))
        }
    }
    
    val groupedCalendars = remember(calendarsWithState) {
        calendarsWithState.groupBy { it.accountName }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Calendarios",
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.Default.ArrowBack,
                            contentDescription = "Volver",
                            tint = colors.textPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.Transparent
                )
            )
        },
        containerColor = Color.Transparent
    ) { paddingValues ->
        
        if (!hasPermission) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                    border = BorderStroke(1.dp, colors.textSecondary.copy(alpha = 0.3f))
                ) {
                    Column(
                        modifier = Modifier.padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "Sin acceso al calendario",
                            style = MaterialTheme.typography.titleMedium,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Bold,
                            color = colors.textPrimary
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Otorga permiso desde la página Glance",
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = NevenFontFamily,
                            color = colors.textSecondary
                        )
                    }
                }
            }
        } else if (calendarsWithState.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                    border = BorderStroke(1.dp, colors.textSecondary.copy(alpha = 0.3f))
                ) {
                    Column(
                        modifier = Modifier.padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "No hay calendarios",
                            style = MaterialTheme.typography.titleMedium,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Bold,
                            color = colors.textPrimary
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Sincroniza una cuenta con calendarios",
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = NevenFontFamily,
                            color = colors.textSecondary
                        )
                    }
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                item { Spacer(modifier = Modifier.height(8.dp)) }
                
                groupedCalendars.forEach { (accountName, accountCalendars) ->
                    item(key = "header_$accountName") {
                        Text(
                            text = accountCalendars.firstOrNull()?.friendlyAccountName?.uppercase() ?: accountName.uppercase(),
                            style = MaterialTheme.typography.labelMedium,
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Bold,
                            color = colors.accent,
                            modifier = Modifier.padding(vertical = 8.dp, horizontal = 4.dp)
                        )
                    }
                    
                    items(
                        items = accountCalendars,
                        key = { it.id }
                    ) { calendar ->
                        CalendarItemCard(
                            calendar = calendar,
                            colors = colors,
                            onToggle = { enabled ->
                                scope.launch {
                                    repository.toggleCalendar(calendar.id, enabled)
                                }
                            }
                        )
                    }
                    
                    item(key = "spacer_$accountName") {
                        Spacer(modifier = Modifier.height(16.dp))
                    }
                }
                
                item(key = "outlook_help") {
                    OutlookHelpCard(colors = colors, context = context)
                }
                
                item(key = "footer") {
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Los calendarios desactivados no aparecerán en el widget de Glance.",
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                    Spacer(modifier = Modifier.height(32.dp))
                }
            }
        }
    }
}

@Composable
private fun CalendarItemCard(
    calendar: CalendarInfo,
    colors: NevenColors,
    onToggle: (Boolean) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onToggle(!calendar.isEnabled) },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        border = BorderStroke(
            1.dp,
            if (calendar.isEnabled) colors.accent else colors.textSecondary.copy(alpha = 0.3f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = calendar.displayName,
                style = MaterialTheme.typography.bodyLarge,
                fontFamily = NevenFontFamily,
                fontWeight = if (calendar.isEnabled) FontWeight.Medium else FontWeight.Normal,
                color = if (calendar.isEnabled) colors.textPrimary else colors.textSecondary,
                modifier = Modifier.weight(1f)
            )
            
            Switch(
                checked = calendar.isEnabled,
                onCheckedChange = onToggle,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = colors.accent,
                    checkedTrackColor = colors.accent.copy(alpha = 0.3f),
                    uncheckedThumbColor = colors.textSecondary,
                    uncheckedTrackColor = colors.textSecondary.copy(alpha = 0.2f)
                )
            )
        }
    }
}

@Composable
private fun OutlookHelpCard(
    colors: NevenColors,
    context: Context
) {
    val outlookInstalled = remember {
        try {
            context.packageManager.getPackageInfo("com.microsoft.office.outlook", 0)
            true
        } catch (e: Exception) {
            false
        }
    }
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        border = BorderStroke(1.dp, colors.accent.copy(alpha = 0.5f))
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "¿No ves tu calendario de Outlook?",
                style = MaterialTheme.typography.titleSmall,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = "La app de Outlook no sincroniza automáticamente. Activa la sincronización:",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            val steps = listOf(
                "Abre Outlook",
                "Toca tu foto de perfil",
                "Toca el engranaje ⚙",
                "Selecciona tu cuenta",
                "Activa \"Sincronizar calendarios\""
            )
            
            steps.forEachIndexed { index, step ->
                Row(modifier = Modifier.padding(vertical = 2.dp)) {
                    Text(
                        text = "${index + 1}.",
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        color = colors.accent,
                        modifier = Modifier.width(20.dp)
                    )
                    Text(
                        text = step,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                }
            }
            
            if (outlookInstalled) {
                Spacer(modifier = Modifier.height(12.dp))
                
                OutlinedButton(
                    onClick = {
                        try {
                            val intent = context.packageManager.getLaunchIntentForPackage("com.microsoft.office.outlook")
                            if (intent != null) context.startActivity(intent)
                        } catch (e: Exception) { }
                    },
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White),
                    border = BorderStroke(1.dp, colors.accent),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "Abrir Outlook",
                        fontFamily = NevenFontFamily
                    )
                }
            }
        }
    }
}

private fun loadAvailableCalendars(context: Context, hiddenIds: Set<String>): List<CalendarInfo> {
    val calendars = mutableListOf<CalendarInfo>()
    
    try {
        context.contentResolver.query(
            CalendarContract.Calendars.CONTENT_URI,
            arrayOf(
                CalendarContract.Calendars._ID,
                CalendarContract.Calendars.CALENDAR_DISPLAY_NAME,
                CalendarContract.Calendars.ACCOUNT_NAME,
                CalendarContract.Calendars.ACCOUNT_TYPE,
                CalendarContract.Calendars.CALENDAR_COLOR,
                CalendarContract.Calendars.VISIBLE
            ),
            null,
            null,
            "${CalendarContract.Calendars.ACCOUNT_NAME} ASC, ${CalendarContract.Calendars.CALENDAR_DISPLAY_NAME} ASC"
        )?.use { cursor ->
            val idIdx = cursor.getColumnIndex(CalendarContract.Calendars._ID)
            val displayNameIdx = cursor.getColumnIndex(CalendarContract.Calendars.CALENDAR_DISPLAY_NAME)
            val accountNameIdx = cursor.getColumnIndex(CalendarContract.Calendars.ACCOUNT_NAME)
            val accountTypeIdx = cursor.getColumnIndex(CalendarContract.Calendars.ACCOUNT_TYPE)
            val colorIdx = cursor.getColumnIndex(CalendarContract.Calendars.CALENDAR_COLOR)
            val visibleIdx = cursor.getColumnIndex(CalendarContract.Calendars.VISIBLE)
            
            while (cursor.moveToNext()) {
                val id = cursor.getLong(idIdx)
                calendars.add(
                    CalendarInfo(
                        id = id,
                        displayName = cursor.getString(displayNameIdx) ?: "Calendario",
                        accountName = cursor.getString(accountNameIdx) ?: "",
                        accountType = cursor.getString(accountTypeIdx) ?: "",
                        color = cursor.getInt(colorIdx),
                        isVisible = cursor.getInt(visibleIdx) == 1,
                        isEnabled = !hiddenIds.contains(id.toString())
                    )
                )
            }
        }
    } catch (e: Exception) {
        e.printStackTrace()
    }
    
    return calendars
}
