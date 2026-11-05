package com.neven.launcher.services

import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.UserManager
import android.provider.Settings
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Gestiona la configuración inicial del Sandbox.
 * 
 * Guía al usuario a través de los pasos necesarios para habilitar
 * el aislamiento completo de apps sin necesidad de ADB.
 * 
 * Flujo de configuración:
 * 1. Verificar/crear Work Profile
 * 2. Configurar NEVEN como Profile Owner (requiere provisioning)
 * 3. Configurar permisos cross-profile
 * 4. Listo para usar
 */
class SandboxSetupManager(private val context: Context) {
    
    companion object {
        private const val TAG = "SandboxSetupManager"
        
        // Estados del setup
        enum class SetupState {
            NOT_STARTED,           // No se ha iniciado la configuración
            NO_WORK_PROFILE,       // No existe Work Profile
            WORK_PROFILE_EXISTS,   // Existe pero NEVEN no es Profile Owner
            PROVISIONING_NEEDED,   // Necesita provisioning para ser Profile Owner
            PROFILE_OWNER_SET,     // NEVEN es Profile Owner
            CROSS_PROFILE_NEEDED,  // Falta configurar cross-profile
            FULLY_CONFIGURED,      // Todo configurado y listo
            ERROR                  // Error en la configuración
        }
        
        // Pasos del wizard
        enum class SetupStep(val stepNumber: Int, val titleRes: Int, val descRes: Int) {
            WELCOME(0, 0, 0),
            CREATE_WORK_PROFILE(1, 0, 0),
            SET_PROFILE_OWNER(2, 0, 0),
            CONFIGURE_PERMISSIONS(3, 0, 0),
            COMPLETE(4, 0, 0)
        }
    }
    
    private val devicePolicyManager: DevicePolicyManager by lazy {
        context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
    }
    
    private val userManager: UserManager by lazy {
        context.getSystemService(Context.USER_SERVICE) as UserManager
    }
    
    private val adminComponent: ComponentName by lazy {
        ComponentName(context, NevenDeviceAdminReceiver::class.java)
    }
    
    /**
     * Información del estado actual del setup
     */
    data class SetupStatus(
        val state: SetupState,
        val currentStep: SetupStep,
        val hasWorkProfile: Boolean,
        val isProfileOwner: Boolean,
        val hasCrossProfileAccess: Boolean,
        val workProfileUserId: Int?,
        val errorMessage: String? = null,
        val canProceedAutomatically: Boolean = false
    )
    
    /**
     * Verifica el estado actual de la configuración del Sandbox
     */
    suspend fun checkSetupStatus(): SetupStatus = withContext(Dispatchers.IO) {
        try {
            // 1. Verificar si existe Work Profile
            val profiles = userManager.userProfiles
            val workProfile = profiles.find { it != android.os.Process.myUserHandle() }
            val hasWorkProfile = workProfile != null
            val workProfileUserId = workProfile?.let { getUserId(it) }
            
            Log.d(TAG, "checkSetupStatus: hasWorkProfile=$hasWorkProfile, workProfileUserId=$workProfileUserId")
            
            // 2. Si hay Work Profile, verificar si NEVEN es Profile Owner
            val isProfileOwnerOfWorkProfile = if (hasWorkProfile) {
                // Verificar usando múltiples métodos (no podemos usar dumpsys desde la app)
                val isOwner = checkIfNevenIsProfileOwnerViaMultiMethod()
                Log.d(TAG, "checkSetupStatus: isProfileOwnerViaMultiMethod=$isOwner")
                isOwner
            } else {
                false
            }
            
            // Determinar estado
            val (state, step, canProceed) = when {
                !hasWorkProfile -> Triple(
                    SetupState.NO_WORK_PROFILE,
                    SetupStep.CREATE_WORK_PROFILE,
                    true
                )
                !isProfileOwnerOfWorkProfile -> Triple(
                    SetupState.PROVISIONING_NEEDED,
                    SetupStep.SET_PROFILE_OWNER,
                    true
                )
                else -> Triple(
                    SetupState.FULLY_CONFIGURED,
                    SetupStep.COMPLETE,
                    false
                )
            }
            
            Log.d(TAG, "checkSetupStatus: state=$state")
            
            SetupStatus(
                state = state,
                currentStep = step,
                hasWorkProfile = hasWorkProfile,
                isProfileOwner = isProfileOwnerOfWorkProfile,
                hasCrossProfileAccess = isProfileOwnerOfWorkProfile,
                workProfileUserId = workProfileUserId,
                canProceedAutomatically = canProceed
            )
        } catch (e: Exception) {
            Log.e(TAG, "Error checking setup status", e)
            SetupStatus(
                state = SetupState.ERROR,
                currentStep = SetupStep.WELCOME,
                hasWorkProfile = false,
                isProfileOwner = false,
                hasCrossProfileAccess = false,
                workProfileUserId = null,
                errorMessage = e.message
            )
        }
    }
    
    /**
     * Verifica si NEVEN es Profile Owner del Work Profile.
     * 
     * Estrategia multi-método porque no tenemos acceso a dumpsys desde la app:
     * 1. Verificar SharedPreferences (flag guardado cuando provisioning completó)
     * 2. Verificar si CrossProfileApps puede listar targets al Work Profile
     * 3. Verificar si hay un Work Profile y NEVEN puede interactuar con él
     */
    private fun checkIfNevenIsProfileOwnerViaMultiMethod(): Boolean {
        Log.d(TAG, "checkIfNevenIsProfileOwnerViaMultiMethod: starting checks")
        
        // Método 1: Verificar flag de provisioning completado
        val prefs = context.getSharedPreferences("sandbox_setup", Context.MODE_PRIVATE)
        val provisioningCompleted = prefs.getBoolean("provisioning_completed", false)
        Log.d(TAG, "checkIfNevenIsProfileOwnerViaMultiMethod: provisioningCompleted=$provisioningCompleted")
        
        if (provisioningCompleted) {
            return true
        }
        
        // Método 2: Verificar con CrossProfileApps si podemos acceder al Work Profile
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val crossProfileApps = context.getSystemService(Context.CROSS_PROFILE_APPS_SERVICE) 
                    as? android.content.pm.CrossProfileApps
                
                if (crossProfileApps != null) {
                    val targetProfiles = crossProfileApps.targetUserProfiles
                    Log.d(TAG, "checkIfNevenIsProfileOwnerViaMultiMethod: targetProfiles=${targetProfiles.size}")
                    
                    if (targetProfiles.isNotEmpty()) {
                        // Si tenemos perfiles target, significa que hay configuración cross-profile
                        // lo cual solo es posible si NEVEN es Profile Owner
                        Log.d(TAG, "checkIfNevenIsProfileOwnerViaMultiMethod: has target profiles, marking as configured")
                        // Guardar para futuras verificaciones
                        prefs.edit().putBoolean("provisioning_completed", true).apply()
                        return true
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error checking CrossProfileApps", e)
        }
        
        // Método 3: Verificar si existe un Work Profile con DevicePolicyManager metadata
        try {
            val profiles = userManager.userProfiles
            val workProfile = profiles.find { it != android.os.Process.myUserHandle() }
            
            if (workProfile != null) {
                // Verificar si el Work Profile está gestionado (tiene Profile Owner)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    // En Android R+ usamos isManagedProfile() que no recibe parámetros
                    // pero se llama en el contexto del perfil actual, así que verificamos
                    // si podemos comunicarnos con el work profile
                    val workProfileId = getUserId(workProfile)
                    Log.d(TAG, "checkIfNevenIsProfileOwnerViaMultiMethod: workProfileId=$workProfileId")
                    
                    // Verificar si NEVEN tiene las capacidades de Profile Owner
                    // intentando una operación que solo Profile Owner puede hacer
                    val canManage = checkIfCanManageWorkProfile()
                    Log.d(TAG, "checkIfNevenIsProfileOwnerViaMultiMethod: canManage=$canManage")
                    
                    if (canManage) {
                        prefs.edit().putBoolean("provisioning_completed", true).apply()
                        return true
                    }
                } else {
                    // En versiones anteriores, si hay Work Profile asumimos que NEVEN lo gestiona
                    // porque el usuario tuvo que pasar por el provisioning
                    Log.d(TAG, "checkIfNevenIsProfileOwnerViaMultiMethod: pre-R device with work profile")
                    prefs.edit().putBoolean("provisioning_completed", true).apply()
                    return true
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error checking work profile status", e)
        }
        
        Log.d(TAG, "checkIfNevenIsProfileOwnerViaMultiMethod: all checks failed, returning false")
        return false
    }
    
    /**
     * Intenta verificar si podemos gestionar el Work Profile
     * haciendo una operación que solo Profile Owner puede hacer
     */
    private fun checkIfCanManageWorkProfile(): Boolean {
        return try {
            // Intentar obtener paquetes cross-profile (solo funciona si somos Profile Owner)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                // Este método lanzará excepción si no somos Profile Owner
                devicePolicyManager.getCrossProfilePackages(adminComponent)
                true
            } else {
                // En versiones anteriores, verificar si tenemos el adminComponent activo
                devicePolicyManager.isAdminActive(adminComponent)
            }
        } catch (e: SecurityException) {
            Log.d(TAG, "checkIfCanManageWorkProfile: SecurityException - not profile owner")
            false
        } catch (e: Exception) {
            Log.e(TAG, "checkIfCanManageWorkProfile: unexpected error", e)
            false
        }
    }
    
    /**
     * Verifica si tenemos acceso cross-profile configurado
     */
    private fun checkCrossProfileAccess(): Boolean {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                val crossProfilePackages = devicePolicyManager.getCrossProfilePackages(adminComponent)
                crossProfilePackages.contains(context.packageName)
            } else {
                // En versiones anteriores asumimos que está configurado si somos Profile Owner
                true
            }
        } catch (e: Exception) {
            false
        }
    }
    
    /**
     * Obtiene el user ID de un UserHandle
     */
    private fun getUserId(userHandle: android.os.UserHandle): Int {
        return try {
            val method = userHandle.javaClass.getMethod("getIdentifier")
            method.invoke(userHandle) as Int
        } catch (e: Exception) {
            -1
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // PASO 1: Crear Work Profile
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Inicia el proceso de creación del Work Profile con NEVEN como Profile Owner.
     * 
     * Usa ACTION_PROVISION_MANAGED_PROFILE que:
     * - Crea el Work Profile automáticamente
     * - Configura NEVEN como Profile Owner
     * - Todo en un solo paso con UI del sistema
     */
    fun createWorkProfileWithNeven(): Intent {
        return Intent(DevicePolicyManager.ACTION_PROVISION_MANAGED_PROFILE).apply {
            putExtra(
                DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME,
                adminComponent
            )
            // Opcional: skip la pantalla de confirmación de encriptación si ya está encriptado
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                putExtra(DevicePolicyManager.EXTRA_PROVISIONING_SKIP_ENCRYPTION, true)
            }
        }
    }
    
    /**
     * Verifica si el dispositivo soporta Work Profiles
     */
    fun isWorkProfileSupported(): Boolean {
        return context.packageManager.hasSystemFeature("android.software.managed_users")
    }
    
    /**
     * Verifica si se puede crear un Work Profile (no existe uno ya)
     */
    fun canCreateWorkProfile(): Boolean {
        val profiles = userManager.userProfiles
        // Si solo hay un perfil (el personal), podemos crear el Work Profile
        return profiles.size == 1 && isWorkProfileSupported()
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // PASO 2: Ya cubierto por ACTION_PROVISION_MANAGED_PROFILE
    // El provisioning configura automáticamente a NEVEN como Profile Owner
    // ═══════════════════════════════════════════════════════════════════════════
    
    // ═══════════════════════════════════════════════════════════════════════════
    // PASO 3: Configurar permisos Cross-Profile (se hace desde Work Profile)
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Configura los permisos cross-profile.
     * DEBE llamarse desde el contexto del Work Profile (donde somos Profile Owner).
     */
    fun configureCrossProfilePermissions(): Boolean {
        if (!devicePolicyManager.isProfileOwnerApp(context.packageName)) {
            Log.w(TAG, "Not profile owner, cannot configure cross-profile permissions")
            return false
        }
        
        return try {
            // Limpiar filtros anteriores
            devicePolicyManager.clearCrossProfileIntentFilters(adminComponent)
            
            // Agregar filtro para nuestra action de instalación
            val installFilter = android.content.IntentFilter().apply {
                addAction(SandboxManager.ACTION_INSTALL_IN_SANDBOX)
                addCategory(Intent.CATEGORY_DEFAULT)
            }
            
            devicePolicyManager.addCrossProfileIntentFilter(
                adminComponent,
                installFilter,
                DevicePolicyManager.FLAG_PARENT_CAN_ACCESS_MANAGED
            )
            
            // Configurar paquetes cross-profile en Android 11+
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                devicePolicyManager.setCrossProfilePackages(adminComponent, setOf(context.packageName))
            }
            
            Log.d(TAG, "Cross-profile permissions configured successfully")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Error configuring cross-profile permissions", e)
            false
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // UTILIDADES
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Marca el provisioning como completado.
     * Llamar cuando sabemos que NEVEN es Profile Owner (después de provisioning exitoso).
     */
    fun markProvisioningCompleted() {
        val prefs = context.getSharedPreferences("sandbox_setup", Context.MODE_PRIVATE)
        prefs.edit().putBoolean("provisioning_completed", true).apply()
        Log.d(TAG, "markProvisioningCompleted: flag set to true")
    }
    
    /**
     * Resetea el estado de provisioning (útil para testing/debug)
     */
    fun resetProvisioningState() {
        val prefs = context.getSharedPreferences("sandbox_setup", Context.MODE_PRIVATE)
        prefs.edit().remove("provisioning_completed").apply()
        Log.d(TAG, "resetProvisioningState: flag removed")
    }
    
    /**
     * Verifica si el provisioning fue marcado como completado
     */
    fun isProvisioningMarkedComplete(): Boolean {
        val prefs = context.getSharedPreferences("sandbox_setup", Context.MODE_PRIVATE)
        return prefs.getBoolean("provisioning_completed", false)
    }
    
    /**
     * Verifica si los filtros cross-profile están configurados
     * (necesario para que las instalaciones funcionen desde el perfil personal)
     */
    fun areCrossProfileFiltersConfigured(): Boolean {
        val prefs = context.getSharedPreferences("sandbox_setup", Context.MODE_PRIVATE)
        return prefs.getBoolean("cross_profile_filters_configured", false)
    }
    
    /**
     * Marca los filtros cross-profile como configurados
     */
    fun markCrossProfileFiltersConfigured() {
        val prefs = context.getSharedPreferences("sandbox_setup", Context.MODE_PRIVATE)
        prefs.edit().putBoolean("cross_profile_filters_configured", true).apply()
        Log.d(TAG, "markCrossProfileFiltersConfigured: flag set to true")
    }
    
    /**
     * Abre la configuración del sistema para Work Profiles
     */
    fun openWorkProfileSettings(): Intent {
        return Intent(Settings.ACTION_SYNC_SETTINGS).apply {
            // Esto abre configuración general, el usuario puede navegar a Work Profile
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
    }
    
    /**
     * Intent para abrir configuración de administradores de dispositivo
     */
    fun openDeviceAdminSettings(): Intent {
        return Intent(Settings.ACTION_SECURITY_SETTINGS).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
    }
}
