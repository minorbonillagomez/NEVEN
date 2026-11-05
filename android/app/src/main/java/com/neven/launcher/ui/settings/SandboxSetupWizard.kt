package com.neven.launcher.ui.settings

import android.app.Activity
import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.neven.launcher.services.SandboxSetupManager
import com.neven.launcher.services.SandboxSetupManager.Companion.SetupState
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.launch

/**
 * Wizard de configuración del Sandbox.
 * 
 * Guía al usuario paso a paso para:
 * 1. Crear el Work Profile (si no existe)
 * 2. Configurar NEVEN como Profile Owner
 * 3. Habilitar permisos cross-profile
 */
@Composable
fun SandboxSetupWizard(
    colors: NevenColors,
    onSetupComplete: () -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val setupManager = remember { SandboxSetupManager(context) }
    val scope = rememberCoroutineScope()
    
    var setupStatus by remember { mutableStateOf<SandboxSetupManager.SetupStatus?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    
    // Launcher para el provisioning del Work Profile
    val provisioningLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        scope.launch {
            // Recargar estado después del provisioning
            isLoading = true
            setupStatus = setupManager.checkSetupStatus()
            isLoading = false
            
            if (result.resultCode == Activity.RESULT_OK) {
                // Provisioning exitoso
                if (setupStatus?.state == SetupState.FULLY_CONFIGURED) {
                    onSetupComplete()
                }
            }
        }
    }
    
    // Cargar estado inicial
    LaunchedEffect(Unit) {
        setupStatus = setupManager.checkSetupStatus()
        isLoading = false
    }
    
    Dialog(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    width = 1.dp,
                    color = colors.textSecondary.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(20.dp)
                )
                .background(colors.background, RoundedCornerShape(20.dp))
                .padding(24.dp)
        ) {
            // Header
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
                        text = "Configurar Sandbox",
                        style = MaterialTheme.typography.titleLarge,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = colors.textPrimary
                    )
                    Text(
                        text = "Aislamiento total de aplicaciones",
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        fontStyle = FontStyle.Italic,
                        color = colors.textSecondary
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            if (isLoading) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = colors.accent)
                }
            } else {
                setupStatus?.let { status ->
                    when (status.state) {
                        SetupState.NO_WORK_PROFILE -> {
                            SetupStepContent(
                                stepNumber = 1,
                                totalSteps = 3,
                                title = "Crear Perfil de Trabajo",
                                description = "El Sandbox utiliza un Perfil de Trabajo separado para aislar completamente las aplicaciones. " +
                                        "Sus archivos, datos y actividad quedarán separados de tu perfil personal.",
                                benefits = listOf(
                                    "Las fotos y videos de WhatsApp no aparecerán en tu galería",
                                    "Las apps no podrán acceder a tus contactos personales",
                                    "Puedes congelar todas las apps del sandbox con un toque"
                                ),
                                buttonText = "Crear Perfil de Trabajo",
                                colors = colors,
                                onAction = {
                                    if (setupManager.canCreateWorkProfile()) {
                                        val intent = setupManager.createWorkProfileWithNeven()
                                        provisioningLauncher.launch(intent)
                                    } else {
                                        errorMessage = "No se puede crear el Perfil de Trabajo. " +
                                                "Es posible que ya exista uno administrado por otra app."
                                    }
                                }
                            )
                        }
                        
                        SetupState.PROVISIONING_NEEDED,
                        SetupState.WORK_PROFILE_EXISTS -> {
                            SetupStepContent(
                                stepNumber = 2,
                                totalSteps = 3,
                                title = "Configurar NEVEN como Administrador",
                                description = "Ya existe un Perfil de Trabajo pero NEVEN necesita ser configurado como su administrador " +
                                        "para poder instalar y gestionar apps en el Sandbox.",
                                benefits = listOf(
                                    "NEVEN podrá mover apps al Sandbox automáticamente",
                                    "Podrás congelar/descongelar apps aisladas",
                                    "Control total sobre el aislamiento"
                                ),
                                buttonText = "Configurar Administrador",
                                colors = colors,
                                onAction = {
                                    // Si ya hay Work Profile, necesitamos hacer provisioning
                                    // Esto requerirá eliminar el perfil existente primero
                                    errorMessage = "Ya existe un Perfil de Trabajo administrado por otra app.\n\n" +
                                            "Para usar el Sandbox de NEVEN, ve a:\n" +
                                            "Ajustes → Usuarios → Perfil de trabajo → Eliminar\n\n" +
                                            "Luego vuelve aquí para crear uno nuevo con NEVEN."
                                }
                            )
                            
                            Spacer(modifier = Modifier.height(12.dp))
                            
                            // Botón para usuarios que ya tienen todo configurado (migración)
                            OutlinedButton(
                                onClick = {
                                    scope.launch {
                                        // Intentar verificar de nuevo con más detalle
                                        setupManager.markProvisioningCompleted()
                                        isLoading = true
                                        setupStatus = setupManager.checkSetupStatus()
                                        isLoading = false
                                        
                                        if (setupStatus?.state == SetupState.FULLY_CONFIGURED) {
                                            onSetupComplete()
                                        }
                                    }
                                },
                                modifier = Modifier.fillMaxWidth(),
                                colors = ButtonDefaults.outlinedButtonColors(
                                    contentColor = colors.textSecondary
                                ),
                                border = ButtonDefaults.outlinedButtonBorder.copy(
                                    brush = androidx.compose.ui.graphics.SolidColor(colors.textSecondary.copy(alpha = 0.3f))
                                ),
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Text(
                                    text = "Ya tengo NEVEN como Profile Owner",
                                    fontFamily = NevenFontFamily,
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                        }
                        
                        SetupState.CROSS_PROFILE_NEEDED,
                        SetupState.PROFILE_OWNER_SET -> {
                            SetupStepContent(
                                stepNumber = 3,
                                totalSteps = 3,
                                title = "Configurar Permisos",
                                description = "NEVEN necesita permisos para comunicarse entre el perfil personal y el de trabajo. " +
                                        "Esto permite mover apps al Sandbox desde esta pantalla.",
                                benefits = listOf(
                                    "Instalación automática de apps en el Sandbox",
                                    "Migración de archivos sin intervención manual",
                                    "Experiencia fluida y transparente"
                                ),
                                buttonText = "Configurar Permisos",
                                colors = colors,
                                onAction = {
                                    // Los permisos se configuran desde el Work Profile
                                    // Necesitamos iniciar nuestra Activity allí
                                    scope.launch {
                                        val success = configureCrossProfileFromPersonal(context, setupManager)
                                        if (success) {
                                            setupStatus = setupManager.checkSetupStatus()
                                            if (setupStatus?.state == SetupState.FULLY_CONFIGURED) {
                                                onSetupComplete()
                                            }
                                        } else {
                                            errorMessage = "No se pudieron configurar los permisos. " +
                                                    "Intenta abrir NEVEN desde el Perfil de Trabajo (icono con maletín)."
                                        }
                                    }
                                }
                            )
                        }
                        
                        SetupState.FULLY_CONFIGURED -> {
                            SetupCompleteContent(
                                colors = colors,
                                onDismiss = onSetupComplete
                            )
                        }
                        
                        SetupState.ERROR -> {
                            SetupErrorContent(
                                errorMessage = status.errorMessage ?: "Error desconocido",
                                colors = colors,
                                onRetry = {
                                    scope.launch {
                                        isLoading = true
                                        setupStatus = setupManager.checkSetupStatus()
                                        isLoading = false
                                    }
                                }
                            )
                        }
                        
                        else -> {
                            Text(
                                text = "Estado: ${status.state}",
                                color = colors.textSecondary
                            )
                        }
                    }
                }
            }
            
            // Mostrar error si hay
            errorMessage?.let { error ->
                Spacer(modifier = Modifier.height(16.dp))
                
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(
                            width = 0.5.dp,
                            color = Color(0xFFE57373).copy(alpha = 0.5f),
                            shape = RoundedCornerShape(12.dp)
                        )
                        .padding(12.dp)
                ) {
                    Text(
                        text = "⚠ Aviso",
                        style = MaterialTheme.typography.labelMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFFE57373)
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = error,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
                
                Spacer(modifier = Modifier.height(12.dp))
                
                TextButton(
                    onClick = { errorMessage = null },
                    modifier = Modifier.align(Alignment.End)
                ) {
                    Text(
                        text = "Entendido",
                        fontFamily = NevenFontFamily,
                        color = colors.accent
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Botón cancelar
            if (setupStatus?.state != SetupState.FULLY_CONFIGURED) {
                TextButton(
                    onClick = onDismiss,
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                ) {
                    Text(
                        text = "Cancelar",
                        fontFamily = NevenFontFamily,
                        color = colors.textSecondary
                    )
                }
            }
        }
    }
}

@Composable
private fun SetupStepContent(
    stepNumber: Int,
    totalSteps: Int,
    title: String,
    description: String,
    benefits: List<String>,
    buttonText: String,
    colors: NevenColors,
    onAction: () -> Unit
) {
    Column {
        // Indicador de paso
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            repeat(totalSteps) { index ->
                val isActive = index + 1 == stepNumber
                val isPast = index + 1 < stepNumber
                
                Box(
                    modifier = Modifier
                        .size(if (isActive) 32.dp else 24.dp)
                        .clip(CircleShape)
                        .background(
                            when {
                                isActive -> colors.accent
                                isPast -> colors.accent.copy(alpha = 0.5f)
                                else -> colors.textSecondary.copy(alpha = 0.2f)
                            }
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "${index + 1}",
                        style = MaterialTheme.typography.labelMedium,
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Bold,
                        color = if (isActive || isPast) Color.White else colors.textSecondary
                    )
                }
                
                if (index < totalSteps - 1) {
                    Box(
                        modifier = Modifier
                            .width(40.dp)
                            .height(2.dp)
                            .background(
                                if (index + 1 < stepNumber) colors.accent.copy(alpha = 0.5f)
                                else colors.textSecondary.copy(alpha = 0.2f)
                            )
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Título del paso
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        // Descripción
        Text(
            text = description,
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary,
            lineHeight = MaterialTheme.typography.bodySmall.lineHeight * 1.4f
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Beneficios
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    width = 0.5.dp,
                    color = colors.accent.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(12.dp)
                )
                .padding(12.dp)
        ) {
            benefits.forEach { benefit ->
                Row(
                    modifier = Modifier.padding(vertical = 4.dp),
                    verticalAlignment = Alignment.Top
                ) {
                    Text(
                        text = "✓",
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.accent
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = benefit,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = NevenFontFamily,
                        color = colors.textPrimary
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Botón de acción
        Button(
            onClick = onAction,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(
                containerColor = colors.accent,
                contentColor = Color.White
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                text = buttonText,
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(vertical = 4.dp)
            )
        }
    }
}

@Composable
private fun SetupCompleteContent(
    colors: NevenColors,
    onDismiss: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Icono de éxito
        Box(
            modifier = Modifier
                .size(80.dp)
                .clip(CircleShape)
                .background(colors.accent.copy(alpha = 0.1f)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "✓",
                style = MaterialTheme.typography.headlineLarge,
                color = colors.accent
            )
        }
        
        Spacer(modifier = Modifier.height(20.dp))
        
        Text(
            text = "¡Sandbox Configurado!",
            style = MaterialTheme.typography.titleLarge,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.Bold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Text(
            text = "El Sandbox está listo. Ahora puedes aislar aplicaciones " +
                    "para que sus archivos y datos queden completamente separados de tu perfil personal.",
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
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
                text = "Comenzar a usar",
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(vertical = 4.dp)
            )
        }
    }
}

@Composable
private fun SetupErrorContent(
    errorMessage: String,
    colors: NevenColors,
    onRetry: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "⚠",
            style = MaterialTheme.typography.headlineLarge,
            color = Color(0xFFE57373)
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "Error de configuración",
            style = MaterialTheme.typography.titleMedium,
            fontFamily = NevenFontFamily,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = errorMessage,
            style = MaterialTheme.typography.bodySmall,
            fontFamily = NevenFontFamily,
            color = colors.textSecondary,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(20.dp))
        
        OutlinedButton(
            onClick = onRetry,
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = colors.accent
            )
        ) {
            Text(
                text = "Reintentar",
                fontFamily = NevenFontFamily
            )
        }
    }
}

/**
 * Intenta configurar cross-profile desde el perfil personal.
 * Esto requiere comunicación con el Work Profile.
 */
private suspend fun configureCrossProfileFromPersonal(
    context: android.content.Context,
    setupManager: SandboxSetupManager
): Boolean {
    return try {
        // Intentar usar CrossProfileApps para iniciar nuestra Activity en Work Profile
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
            val crossProfileApps = context.getSystemService(android.content.Context.CROSS_PROFILE_APPS_SERVICE) 
                as? android.content.pm.CrossProfileApps
            
            val userManager = context.getSystemService(android.content.Context.USER_SERVICE) as android.os.UserManager
            val profiles = userManager.userProfiles
            val workProfile = profiles.find { it != android.os.Process.myUserHandle() }
            
            if (crossProfileApps != null && workProfile != null) {
                // Iniciar SandboxInstallActivity en Work Profile para que configure los permisos
                val intent = Intent("com.neven.launcher.action.INSTALL_IN_SANDBOX").apply {
                    component = android.content.ComponentName(
                        context.packageName,
                        "com.neven.launcher.services.SandboxInstallActivity"
                    )
                    putExtra("action", "setup_filters")
                }
                
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
                    crossProfileApps.startActivity(intent, workProfile, null)
                } else {
                    crossProfileApps.startMainActivity(
                        android.content.ComponentName(
                            context.packageName,
                            "com.neven.launcher.services.SandboxInstallActivity"
                        ),
                        workProfile
                    )
                }
                
                // Esperar un momento
                kotlinx.coroutines.delay(2000)
                
                // Verificar si se configuró
                val newStatus = setupManager.checkSetupStatus()
                return newStatus.state == SandboxSetupManager.Companion.SetupState.FULLY_CONFIGURED
            }
        }
        false
    } catch (e: Exception) {
        android.util.Log.e("SandboxSetupWizard", "Error configuring cross-profile", e)
        false
    }
}
