package com.neven.launcher.ui.settings

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.neven.launcher.R
import com.neven.launcher.services.SandboxManager
import com.neven.launcher.services.SandboxSetupManager
import com.neven.launcher.ui.theme.*
import kotlinx.coroutines.launch

/**
 * Pantalla de configuración del Sandbox
 * 
 * Permite al usuario:
 * - Ver apps en el sandbox vs perfil personal
 * - Migrar apps completas al sandbox (archivos + instalación)
 * - Remover apps del sandbox
 * - Activar/desactivar el modo silencioso del perfil completo
 * 
 * Símbolo científico: ⊘ (conjunto vacío con diagonal - aislamiento)
 */
@Composable
fun SandboxSettingsScreen(
    colors: NevenColors,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val sandboxManager = remember { SandboxManager.getInstance(context) }
    val setupManager = remember { SandboxSetupManager(context) }
    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }
    
    // Estados
    var sandboxStatus by remember { mutableStateOf<SandboxManager.SandboxStatus?>(null) }
    var setupStatus by remember { mutableStateOf<SandboxSetupManager.SetupStatus?>(null) }
    var sandboxedApps by remember { mutableStateOf<List<SandboxManager.SandboxAppInfo>>(emptyList()) }
    var suggestedApps by remember { mutableStateOf<List<SandboxManager.SandboxAppInfo>>(emptyList()) }
    var otherApps by remember { mutableStateOf<List<SandboxManager.SandboxAppInfo>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    var showOtherApps by remember { mutableStateOf(false) }
    
    // Estado de diálogos
    var showSetupWizard by remember { mutableStateOf(false) }
    var showMigrationDialog by remember { mutableStateOf(false) }
    var showProgressDialog by remember { mutableStateOf(false) }
    var showCrossProfileSetupDialog by remember { mutableStateOf(false) }
    var selectedAppForMigration by remember { mutableStateOf<SandboxManager.SandboxAppInfo?>(null) }
    var migrationInfo by remember { mutableStateOf<SandboxManager.MigrationInfo?>(null) }
    var migrationProgress by remember { mutableStateOf(0f) }
    var migrationMessage by remember { mutableStateOf("") }
    var migrationStage by remember { mutableStateOf(SandboxManager.MigrationStage.SCANNING_FILES) }
    
    // Strings
    val migrationCompleteMsg = stringResource(R.string.sandbox_migration_complete)
    val migrationErrorMsg = stringResource(R.string.sandbox_migration_error)
    
    // Función para recargar datos
    suspend fun refreshData() {
        isLoading = true
        setupStatus = setupManager.checkSetupStatus()
        sandboxStatus = sandboxManager.getSandboxStatus()
        
        // Solo cargar apps si el sandbox está configurado
        if (setupStatus?.state == SandboxSetupManager.Companion.SetupState.FULLY_CONFIGURED) {
            val allApps = sandboxManager.getInstalledAppsForSandbox()
            sandboxedApps = allApps.filter { it.isInSandbox }
            suggestedApps = allApps.filter { it.isSuggested && !it.isInSandbox }
            otherApps = allApps.filter { !it.isSuggested && !it.isInSandbox }
        }
        isLoading = false
    }
    
    // Cargar datos iniciales
    LaunchedEffect(Unit) {
        refreshData()
    }
    
    // Función para iniciar migración
    fun startMigration(app: SandboxManager.SandboxAppInfo) {
        scope.launch {
            // Escanear archivos primero
            migrationInfo = sandboxManager.scanAppMediaFiles(app.packageName)
            selectedAppForMigration = app
            showMigrationDialog = true
        }
    }
    
    // Función para ejecutar migración
    fun executeMigration() {
        val app = selectedAppForMigration ?: return
        showMigrationDialog = false
        showProgressDialog = true
        migrationProgress = 0f
        
        scope.launch {
            try {
                val result = sandboxManager.migrateAppToSandbox(app.packageName) { stage, progress, message ->
                    migrationStage = stage
                    migrationProgress = progress
                    migrationMessage = message
                }
                
                showProgressDialog = false
                
                if (result.success) {
                    // Verificar si fue instalación directa o quedó pendiente
                    if (result.errorMessage == "PENDING_WORK_PROFILE") {
                        // La instalación quedó en cola - mostrar diálogo con instrucciones
                        showCrossProfileSetupDialog = true
                    } else {
                        snackbarHostState.showSnackbar(migrationCompleteMsg)
                    }
                    // Esperar un momento para que LauncherApps actualice su cache
                    kotlinx.coroutines.delay(500)
                    refreshData()
                } else if (result.errorMessage == "SETUP_CROSS_PROFILE_NEEDED") {
                    // Mostrar diálogo de configuración cross-profile
                    showCrossProfileSetupDialog = true
                } else if (result.errorMessage == "OPEN_PLAY_STORE") {
                    // installExistingPackage no funciona (requiere Device Owner)
                    // Abrir Play Store para que el usuario instale manualmente
                    val pkgName = app.packageName
                    try {
                        val intent = android.content.Intent(
                            android.content.Intent.ACTION_VIEW,
                            android.net.Uri.parse("market://details?id=$pkgName")
                        )
                        intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                        context.startActivity(intent)
                        snackbarHostState.showSnackbar("Instala la app desde Play Store")
                    } catch (e: Exception) {
                        // Play Store no disponible, abrir en navegador
                        val webIntent = android.content.Intent(
                            android.content.Intent.ACTION_VIEW,
                            android.net.Uri.parse("https://play.google.com/store/apps/details?id=$pkgName")
                        )
                        webIntent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                        context.startActivity(webIntent)
                    }
                    refreshData()
                } else {
                    snackbarHostState.showSnackbar("$migrationErrorMsg: ${result.errorMessage}")
                    refreshData()
                }
            } catch (e: Exception) {
                showProgressDialog = false
                snackbarHostState.showSnackbar("Error: ${e.message}")
                refreshData()
            }
        }
    }
    
    // Función para remover del sandbox
    fun removeFromSandbox(app: SandboxManager.SandboxAppInfo) {
        showProgressDialog = true
        migrationProgress = 0f
        migrationMessage = "Removing from sandbox..."
        
        scope.launch {
            val result = sandboxManager.removeAppFromSandbox(
                app.packageName,
                migrateFilesBack = true
            ) { stage, progress, message ->
                migrationStage = stage
                migrationProgress = progress
                migrationMessage = message
            }
            
            showProgressDialog = false
            
            if (result.success) {
                snackbarHostState.showSnackbar("${app.appName} restored")
            } else {
                snackbarHostState.showSnackbar("Error: ${result.errorMessage}")
            }
            
            refreshData()
        }
    }
    
    Scaffold(
        snackbarHost = {
            SnackbarHost(hostState = snackbarHostState) { data ->
                Snackbar(
                    snackbarData = data,
                    containerColor = colors.accent,
                    contentColor = Color.White,
                    shape = RoundedCornerShape(8.dp)
                )
            }
        },
        containerColor = Color.Transparent
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .systemBarsPadding()
        ) {
            // ═══════════════════════════════════════════════════════════════
            // HEADER
            // ═══════════════════════════════════════════════════════════════
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "<",
                    modifier = Modifier
                        .clickable { onBack() }
                        .padding(8.dp),
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = FontFamily.Serif
                    ),
                    color = colors.textPrimary
                )
                
                Spacer(modifier = Modifier.width(16.dp))
                
                Text(
                    text = "⊘",
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = FontFamily.Serif
                    ),
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                Text(
                    text = stringResource(R.string.settings_sandbox),
                    style = MaterialTheme.typography.headlineMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.textPrimary
                )
            }
            
            HorizontalDivider(color = colors.textSecondary.copy(alpha = 0.15f))
            
            // ═══════════════════════════════════════════════════════════════
            // CONTENIDO
            // ═══════════════════════════════════════════════════════════════
            if (isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = colors.accent)
                }
            } else {
                // Verificar si el sandbox necesita configuración
                val needsSetup = setupStatus?.state != SandboxSetupManager.Companion.SetupState.FULLY_CONFIGURED
                
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(24.dp),
                    verticalArrangement = Arrangement.spacedBy(24.dp)
                ) {
                    // Mostrar tarjeta de configuración si es necesario
                    if (needsSetup) {
                        item {
                            SandboxSetupCard(
                                setupStatus = setupStatus,
                                colors = colors,
                                onSetupClick = { showSetupWizard = true }
                            )
                        }
                    }
                    
                    // Toggle congelar todo (solo si está configurado)
                    if (!needsSetup) {
                        item {
                            SandboxStatusCard(
                                status = sandboxStatus,
                                colors = colors,
                                onToggleQuietMode = { enabled ->
                                    scope.launch {
                                        sandboxManager.setWorkProfileQuietMode(enabled)
                                        sandboxStatus = sandboxManager.getSandboxStatus()
                                    }
                                }
                            )
                        }
                    }
                    
                    // Apps en el Sandbox (solo si está configurado)
                    if (!needsSetup && sandboxedApps.isNotEmpty()) {
                        item {
                            SandboxedAppsSection(
                                apps = sandboxedApps,
                                colors = colors,
                                onRemoveFromSandbox = { removeFromSandbox(it) }
                            )
                        }
                    }
                    
                    // Apps sugeridas (solo si está configurado)
                    if (!needsSetup && suggestedApps.isNotEmpty()) {
                        item {
                            SuggestedAppsSection(
                                apps = suggestedApps,
                                colors = colors,
                                onMigrateApp = { startMigration(it) }
                            )
                        }
                    }
                    
                    // Otras apps (solo si está configurado)
                    if (!needsSetup) {
                        item {
                            OtherAppsSection(
                                apps = otherApps,
                                showAllApps = showOtherApps,
                                colors = colors,
                                onMigrateApp = { startMigration(it) },
                                onToggleShowAll = { showOtherApps = !showOtherApps }
                            )
                        }
                    }
                    
                    // Info
                    item {
                        SandboxInfoCard(colors = colors)
                    }
                    
                    item {
                        Spacer(modifier = Modifier.height(32.dp))
                    }
                }
            }
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // DIÁLOGOS
    // ═══════════════════════════════════════════════════════════════════════════
    
    // Wizard de configuración
    if (showSetupWizard) {
        SandboxSetupWizard(
            colors = colors,
            onSetupComplete = {
                showSetupWizard = false
                scope.launch { refreshData() }
            },
            onDismiss = { showSetupWizard = false }
        )
    }
    
    // Diálogo de confirmación de migración
    if (showMigrationDialog && selectedAppForMigration != null && migrationInfo != null) {
        MigrationConfirmDialog(
            app = selectedAppForMigration!!,
            migrationInfo = migrationInfo!!,
            colors = colors,
            sandboxManager = sandboxManager,
            onConfirm = { executeMigration() },
            onDismiss = { 
                showMigrationDialog = false
                selectedAppForMigration = null
            }
        )
    }
    
    // Diálogo de progreso
    if (showProgressDialog) {
        MigrationProgressDialog(
            stage = migrationStage,
            progress = migrationProgress,
            message = migrationMessage,
            colors = colors
        )
    }
    
    // Diálogo de configuración cross-profile
    if (showCrossProfileSetupDialog) {
        CrossProfileSetupDialog(
            colors = colors,
            onDismiss = { 
                showCrossProfileSetupDialog = false 
                scope.launch { refreshData() }
            }
        )
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENTES DE SECCIÓN
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Tarjeta con toggle para congelar todo el perfil
 */
@Composable
private fun SandboxStatusCard(
    status: SandboxManager.SandboxStatus?,
    colors: NevenColors,
    onToggleQuietMode: (Boolean) -> Unit
) {
    if (status?.hasWorkProfile == true && status.isProfileOwner) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    width = 0.5.dp,
                    color = colors.textSecondary.copy(alpha = 0.12f),
                    shape = RoundedCornerShape(16.dp)
                )
                .padding(20.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = stringResource(R.string.sandbox_freeze_all),
                        style = MaterialTheme.typography.titleMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.SemiBold,
                        color = colors.textPrimary
                    )
                    Text(
                        text = stringResource(R.string.sandbox_freeze_all_desc),
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic,
                        color = colors.textSecondary
                    )
                }
                
                Switch(
                    checked = !status.isWorkProfileEnabled,
                    onCheckedChange = { onToggleQuietMode(it) },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = colors.accent,
                        checkedTrackColor = colors.accent.copy(alpha = 0.5f),
                        uncheckedThumbColor = colors.textSecondary,
                        uncheckedTrackColor = colors.textSecondary.copy(alpha = 0.3f)
                    )
                )
            }
        }
    }
}

/**
 * Tarjeta de configuración inicial del Sandbox
 */
@Composable
private fun SandboxSetupCard(
    setupStatus: SandboxSetupManager.SetupStatus?,
    colors: NevenColors,
    onSetupClick: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                width = 1.dp,
                color = colors.accent.copy(alpha = 0.3f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "⊘",
                style = MaterialTheme.typography.headlineSmall.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Column {
                Text(
                    text = "Configurar Sandbox",
                    style = MaterialTheme.typography.titleMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.SemiBold,
                    color = colors.textPrimary
                )
                Text(
                    text = when (setupStatus?.state) {
                        SandboxSetupManager.Companion.SetupState.NO_WORK_PROFILE -> 
                            "Crea un Perfil de Trabajo para aislar apps"
                        SandboxSetupManager.Companion.SetupState.PROVISIONING_NEEDED,
                        SandboxSetupManager.Companion.SetupState.WORK_PROFILE_EXISTS ->
                            "Configura NEVEN como administrador"
                        SandboxSetupManager.Companion.SetupState.CROSS_PROFILE_NEEDED ->
                            "Configura permisos de comunicación"
                        else -> "Configuración necesaria"
                    },
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic,
                    color = colors.textSecondary
                )
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "El Sandbox permite aislar aplicaciones como WhatsApp, Instagram o TikTok " +
                    "para que sus archivos y datos queden completamente separados de tu perfil personal.",
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary,
            lineHeight = MaterialTheme.typography.bodySmall.lineHeight * 1.3f
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Beneficios en lista
        Column {
            listOf(
                "✓ Las fotos de WhatsApp no aparecerán en tu galería",
                "✓ Las apps no accederán a tus contactos personales",
                "✓ Congela todas las apps del sandbox con un toque"
            ).forEach { benefit ->
                Text(
                    text = benefit,
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.accent,
                    modifier = Modifier.padding(vertical = 2.dp)
                )
            }
        }
        
        Spacer(modifier = Modifier.height(20.dp))
        
        Button(
            onClick = onSetupClick,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(
                containerColor = colors.accent,
                contentColor = Color.White
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                text = "Configurar ahora",
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(vertical = 4.dp)
            )
        }
    }
}

/**
 * Sección de apps en el sandbox
 */
@Composable
private fun SandboxedAppsSection(
    apps: List<SandboxManager.SandboxAppInfo>,
    colors: NevenColors,
    onRemoveFromSandbox: (SandboxManager.SandboxAppInfo) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                width = 0.5.dp,
                color = colors.accent.copy(alpha = 0.3f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        Text(
            text = stringResource(R.string.sandbox_in_sandbox),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        Text(
            text = stringResource(R.string.sandbox_in_sandbox_desc),
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        apps.forEach { app ->
            SandboxedAppItem(
                app = app,
                colors = colors,
                onRemove = { onRemoveFromSandbox(app) }
            )
            
            if (app != apps.last()) {
                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 8.dp),
                    color = colors.textSecondary.copy(alpha = 0.08f)
                )
            }
        }
    }
}

/**
 * Item de app en sandbox con opción de remover
 */
@Composable
private fun SandboxedAppItem(
    app: SandboxManager.SandboxAppInfo,
    colors: NevenColors,
    onRemove: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Indicador de sandbox
        Text(
            text = "⊘",
            style = MaterialTheme.typography.titleMedium.copy(
                fontFamily = FontFamily.Serif
            ),
            color = colors.accent
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = app.appName,
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = colors.textPrimary
            )
            Text(
                text = stringResource(R.string.sandbox_app_isolated),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.accent
            )
        }
        
        // Botón remover
        OutlinedButton(
            onClick = onRemove,
            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = colors.textSecondary
            ),
            border = ButtonDefaults.outlinedButtonBorder(enabled = true).copy(
                brush = androidx.compose.ui.graphics.SolidColor(colors.textSecondary.copy(alpha = 0.3f))
            )
        ) {
            Text(
                text = stringResource(R.string.sandbox_remove),
                style = MaterialTheme.typography.labelSmall,
                fontFamily = NevenFontFamily
            )
        }
    }
}

/**
 * Sección de apps sugeridas
 */
@Composable
private fun SuggestedAppsSection(
    apps: List<SandboxManager.SandboxAppInfo>,
    colors: NevenColors,
    onMigrateApp: (SandboxManager.SandboxAppInfo) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                width = 0.5.dp,
                color = colors.textSecondary.copy(alpha = 0.12f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        Text(
            text = stringResource(R.string.sandbox_suggested_apps),
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        Text(
            text = stringResource(R.string.sandbox_suggested_apps_desc),
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Italic,
            color = colors.textSecondary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        apps.forEach { app ->
            MigratableAppItem(
                app = app,
                colors = colors,
                onMigrate = { onMigrateApp(app) }
            )
            
            if (app != apps.last()) {
                HorizontalDivider(
                    modifier = Modifier.padding(start = 40.dp, top = 8.dp, bottom = 8.dp),
                    color = colors.textSecondary.copy(alpha = 0.08f)
                )
            }
        }
    }
}

/**
 * Item de app que puede migrarse
 */
@Composable
private fun MigratableAppItem(
    app: SandboxManager.SandboxAppInfo,
    colors: NevenColors,
    onMigrate: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .clickable { onMigrate() }
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = app.appName,
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Medium,
                color = colors.textPrimary
            )
            Text(
                text = app.packageName,
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary.copy(alpha = 0.7f)
            )
        }
        
        // Botón migrar
        OutlinedButton(
            onClick = onMigrate,
            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = colors.accent
            ),
            border = ButtonDefaults.outlinedButtonBorder(enabled = true).copy(
                brush = androidx.compose.ui.graphics.SolidColor(colors.accent.copy(alpha = 0.5f))
            )
        ) {
            Text(
                text = stringResource(R.string.sandbox_migrate),
                style = MaterialTheme.typography.labelSmall,
                fontFamily = NevenFontFamily
            )
        }
    }
}

/**
 * Sección de otras aplicaciones
 */
@Composable
private fun OtherAppsSection(
    apps: List<SandboxManager.SandboxAppInfo>,
    showAllApps: Boolean,
    colors: NevenColors,
    onMigrateApp: (SandboxManager.SandboxAppInfo) -> Unit,
    onToggleShowAll: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                width = 0.5.dp,
                color = colors.textSecondary.copy(alpha = 0.12f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onToggleShowAll() },
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = stringResource(R.string.sandbox_other_apps),
                    style = MaterialTheme.typography.titleMedium,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.SemiBold,
                    color = colors.textPrimary
                )
                Text(
                    text = stringResource(R.string.sandbox_other_apps_count, apps.size),
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic,
                    color = colors.textSecondary
                )
            }
            
            Text(
                text = if (showAllApps) "−" else "+",
                style = MaterialTheme.typography.headlineSmall.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
        }
        
        AnimatedVisibility(
            visible = showAllApps,
            enter = fadeIn() + expandVertically(),
            exit = fadeOut() + shrinkVertically()
        ) {
            Column {
                Spacer(modifier = Modifier.height(16.dp))
                
                apps.forEach { app ->
                    MigratableAppItem(
                        app = app,
                        colors = colors,
                        onMigrate = { onMigrateApp(app) }
                    )
                    
                    if (app != apps.last()) {
                        HorizontalDivider(
                            modifier = Modifier.padding(start = 40.dp, top = 8.dp, bottom = 8.dp),
                            color = colors.textSecondary.copy(alpha = 0.08f)
                        )
                    }
                }
            }
        }
    }
}

/**
 * Tarjeta informativa sobre el sandbox
 */
@Composable
private fun SandboxInfoCard(colors: NevenColors) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                width = 0.5.dp,
                color = colors.accent.copy(alpha = 0.2f),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(20.dp)
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "ℹ",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontFamily = FontFamily.Serif
                ),
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Text(
                text = stringResource(R.string.sandbox_info_title),
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                color = colors.textPrimary
            )
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Text(
            text = stringResource(R.string.sandbox_info_desc),
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary,
            lineHeight = MaterialTheme.typography.bodySmall.lineHeight * 1.4f
        )
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DIÁLOGOS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Diálogo de confirmación de migración
 */
@Composable
private fun MigrationConfirmDialog(
    app: SandboxManager.SandboxAppInfo,
    migrationInfo: SandboxManager.MigrationInfo,
    colors: NevenColors,
    sandboxManager: SandboxManager,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    width = 1.dp,
                    color = colors.textSecondary.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(16.dp)
                )
                .background(colors.background, RoundedCornerShape(16.dp))
                .padding(24.dp)
        ) {
            // Header
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "⊘",
                    style = MaterialTheme.typography.headlineSmall.copy(
                        fontFamily = FontFamily.Serif
                    ),
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                Text(
                    text = stringResource(R.string.sandbox_migrate_title),
                    style = MaterialTheme.typography.titleLarge,
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold,
                    color = colors.textPrimary
                )
            }
            
            Spacer(modifier = Modifier.height(20.dp))
            
            // Nombre de la app
            Text(
                text = app.appName,
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Info de archivos
            if (migrationInfo.totalFiles > 0) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(
                            width = 0.5.dp,
                            color = colors.textSecondary.copy(alpha = 0.15f),
                            shape = RoundedCornerShape(8.dp)
                        )
                        .padding(12.dp)
                ) {
                    Text(
                        text = stringResource(R.string.sandbox_migrate_files_found),
                        style = MaterialTheme.typography.labelMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.SemiBold,
                        color = colors.textPrimary
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    Text(
                        text = "• ${migrationInfo.totalFiles} ${stringResource(R.string.sandbox_migrate_files)}",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                    Text(
                        text = "• ${sandboxManager.formatFileSize(migrationInfo.totalSizeBytes)}",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
                
                Spacer(modifier = Modifier.height(16.dp))
            }
            
            // Descripción de acciones
            Text(
                text = stringResource(R.string.sandbox_migrate_actions),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Advertencia
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(
                        width = 0.5.dp,
                        color = colors.accent.copy(alpha = 0.3f),
                        shape = RoundedCornerShape(8.dp)
                    )
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "⚠",
                    style = MaterialTheme.typography.titleMedium,
                    color = colors.accent
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.sandbox_migrate_warning),
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = NevenFontFamily,
                    color = colors.textSecondary
                )
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Botones
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                OutlinedButton(
                    onClick = onDismiss,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = colors.textSecondary
                    ),
                    border = ButtonDefaults.outlinedButtonBorder(enabled = true).copy(
                        brush = androidx.compose.ui.graphics.SolidColor(colors.textSecondary.copy(alpha = 0.3f))
                    )
                ) {
                    Text(
                        text = stringResource(R.string.sandbox_cancel),
                        fontFamily = NevenFontFamily
                    )
                }
                
                OutlinedButton(
                    onClick = onConfirm,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = colors.accent
                    ),
                    border = ButtonDefaults.outlinedButtonBorder(enabled = true).copy(
                        brush = androidx.compose.ui.graphics.SolidColor(colors.accent)
                    )
                ) {
                    Text(
                        text = stringResource(R.string.sandbox_migrate_button),
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

/**
 * Diálogo de progreso de migración
 */
@Composable
private fun MigrationProgressDialog(
    stage: SandboxManager.MigrationStage,
    progress: Float,
    message: String,
    colors: NevenColors
) {
    Dialog(onDismissRequest = { /* No se puede cancelar */ }) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    width = 1.dp,
                    color = colors.textSecondary.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(16.dp)
                )
                .background(colors.background, RoundedCornerShape(16.dp))
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = stringResource(R.string.sandbox_migrating),
                style = MaterialTheme.typography.titleMedium,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                color = colors.textPrimary
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Barra de progreso
            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
                color = colors.accent,
                trackColor = colors.textSecondary.copy(alpha = 0.2f)
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = "${(progress * 100).toInt()}%",
                style = MaterialTheme.typography.labelMedium,
                fontFamily = NevenFontFamily,
                color = colors.accent
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = message,
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary,
                textAlign = TextAlign.Center
            )
        }
    }
}


/**
 * Diálogo que guía al usuario para completar instalaciones pendientes.
 * Incluye un botón para abrir NEVEN en el Work Profile directamente.
 */
@Composable
private fun CrossProfileSetupDialog(
    colors: NevenColors,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    
    Dialog(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    width = 1.dp,
                    color = colors.textSecondary.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(16.dp)
                )
                .background(colors.background, RoundedCornerShape(16.dp))
                .padding(24.dp)
        ) {
            // Header con icono
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "⊘",
                    style = MaterialTheme.typography.headlineMedium.copy(
                        fontFamily = FontFamily.Serif
                    ),
                    color = colors.accent
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                Column {
                    Text(
                        text = "Instalación pendiente",
                        style = MaterialTheme.typography.titleLarge,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.textPrimary
                    )
                    Text(
                        text = "Un paso más para completar",
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic,
                        color = colors.accent
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(20.dp))
            
            Text(
                text = "La app está lista para aislarse. Para completar:",
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = NevenFontFamily,
                color = colors.textSecondary,
                lineHeight = MaterialTheme.typography.bodyMedium.lineHeight * 1.3f
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Pasos
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(
                        width = 0.5.dp,
                        color = colors.accent.copy(alpha = 0.3f),
                        shape = RoundedCornerShape(8.dp)
                    )
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(verticalAlignment = Alignment.Top) {
                    Text(
                        text = "1.",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.accent,
                        modifier = Modifier.width(24.dp)
                    )
                    Text(
                        text = "Ve a tu carpeta de Trabajo (Work Profile)",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                }
                Row(verticalAlignment = Alignment.Top) {
                    Text(
                        text = "2.",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.accent,
                        modifier = Modifier.width(24.dp)
                    )
                    Text(
                        text = "Abre NEVEN (tiene icono con maletín)",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                }
                Row(verticalAlignment = Alignment.Top) {
                    Text(
                        text = "3.",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.accent,
                        modifier = Modifier.width(24.dp)
                    )
                    Text(
                        text = "La app se instalará automáticamente en el Sandbox",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Nota
            Text(
                text = "Tip: Desliza hacia arriba en el cajón de apps para ver la carpeta de Trabajo.",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary.copy(alpha = 0.8f)
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Botón - Entendido
            Button(
                onClick = onDismiss,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = colors.accent,
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = "Entendido",
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(vertical = 4.dp)
                )
            }
        }
    }
}
