package com.neven.launcher.services

import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.CrossProfileApps
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.UserHandle
import android.os.UserManager
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

/**
 * Sandbox Manager para NEVEN
 * 
 * Gestiona el Work Profile y el aislamiento completo de aplicaciones.
 * 
 * Funcionalidades:
 * - Detectar/crear Work Profile
 * - Migrar archivos de apps al sandbox
 * - Instalar/desinstalar apps en Work Profile
 * - Aplicar políticas de aislamiento
 * - Suspender/reanudar apps en el sandbox
 */
class SandboxManager(private val context: Context) {
    
    companion object {
        private const val TAG = "SandboxManager"
        private const val WORK_PROFILE_USER_ID = 10
        
        // Action para instalar app en Work Profile
        const val ACTION_INSTALL_IN_SANDBOX = "com.neven.launcher.action.INSTALL_IN_SANDBOX"
        const val EXTRA_PACKAGE_NAME = "package_name"
        
        // Apps sugeridas para sandbox (redes sociales y alta telemetría)
        val SUGGESTED_SANDBOX_APPS = listOf(
            "com.facebook.katana",           // Facebook
            "com.facebook.orca",             // Messenger
            "com.instagram.android",         // Instagram
            "com.whatsapp",                  // WhatsApp
            "com.linkedin.android",          // LinkedIn
            "com.twitter.android",           // X (Twitter)
            "com.snapchat.android",          // Snapchat
            "com.zhiliaoapp.musically",      // TikTok
            "com.pinterest",                 // Pinterest
            "com.reddit.frontpage",          // Reddit
            "org.telegram.messenger",        // Telegram
            "com.discord",                   // Discord
            "com.google.android.apps.photos", // Google Photos
            "com.google.android.apps.maps",   // Google Maps
            "com.android.chrome",             // Chrome
            "com.amazon.mShop.android.shopping", // Amazon
            "com.spotify.music",              // Spotify
            "com.netflix.mediaclient",        // Netflix
        )
        
        // Carpetas de medios conocidas por app
        val APP_MEDIA_FOLDERS = mapOf(
            "com.whatsapp" to listOf(
                "WhatsApp/Media/WhatsApp Images",
                "WhatsApp/Media/WhatsApp Video",
                "WhatsApp/Media/WhatsApp Audio",
                "WhatsApp/Media/WhatsApp Documents",
                "WhatsApp/Media/WhatsApp Animated Gifs",
                "WhatsApp/Media/WhatsApp Stickers",
                "Pictures/WhatsApp",
                "DCIM/WhatsApp"
            ),
            "com.instagram.android" to listOf(
                "Pictures/Instagram",
                "Movies/Instagram",
                "DCIM/Instagram"
            ),
            "com.facebook.katana" to listOf(
                "Pictures/Facebook",
                "Movies/Facebook",
                "DCIM/Facebook"
            ),
            "com.facebook.orca" to listOf(
                "Pictures/Messenger",
                "Movies/Messenger"
            ),
            "org.telegram.messenger" to listOf(
                "Telegram/Telegram Images",
                "Telegram/Telegram Video",
                "Telegram/Telegram Audio",
                "Telegram/Telegram Documents",
                "Pictures/Telegram"
            ),
            "com.zhiliaoapp.musically" to listOf(
                "Pictures/TikTok",
                "Movies/TikTok",
                "DCIM/TikTok"
            ),
            "com.snapchat.android" to listOf(
                "Pictures/Snapchat",
                "Snapchat",
                "DCIM/Snapchat"
            ),
            "com.twitter.android" to listOf(
                "Pictures/Twitter",
                "Movies/Twitter"
            ),
            "com.linkedin.android" to listOf(
                "Pictures/LinkedIn"
            ),
            "com.discord" to listOf(
                "Pictures/Discord",
                "Download/Discord"
            ),
            "com.pinterest" to listOf(
                "Pictures/Pinterest"
            ),
            "com.reddit.frontpage" to listOf(
                "Pictures/Reddit"
            )
        )
        
        @Volatile
        private var instance: SandboxManager? = null
        
        fun getInstance(context: Context): SandboxManager {
            return instance ?: synchronized(this) {
                instance ?: SandboxManager(context.applicationContext).also { instance = it }
            }
        }
    }
    
    private val devicePolicyManager: DevicePolicyManager by lazy {
        context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
    }
    
    private val userManager: UserManager by lazy {
        context.getSystemService(Context.USER_SERVICE) as UserManager
    }
    
    private val packageManager: PackageManager by lazy {
        context.packageManager
    }
    
    private val adminComponent: ComponentName by lazy {
        ComponentName(context, NevenDeviceAdminReceiver::class.java)
    }
    
    private val crossProfileApps: CrossProfileApps? by lazy {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            context.getSystemService(Context.CROSS_PROFILE_APPS_SERVICE) as? CrossProfileApps
        } else null
    }
    
    /**
     * Detecta si estamos ejecutando en el Work Profile
     */
    fun isRunningInWorkProfile(): Boolean {
        return devicePolicyManager.isProfileOwnerApp(context.packageName)
    }
    
    /**
     * Obtiene el UserHandle del Work Profile si existe
     */
    fun getWorkProfileUserHandle(): UserHandle? {
        val profiles = userManager.userProfiles
        return profiles.find { it != android.os.Process.myUserHandle() }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // DATA CLASSES
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Estado del sandbox
     */
    data class SandboxStatus(
        val hasWorkProfile: Boolean,
        val isProfileOwner: Boolean,
        val workProfileUserId: Int?,
        val isWorkProfileEnabled: Boolean,
        val sandboxedAppsCount: Int
    )
    
    /**
     * Info de una app que puede ir al sandbox
     */
    data class SandboxAppInfo(
        val packageName: String,
        val appName: String,
        val isSuggested: Boolean,
        val isInSandbox: Boolean,
        val isSuspended: Boolean,
        val isInstalledInPersonal: Boolean = true,
        val riskLevel: RiskLevel = RiskLevel.UNKNOWN
    )
    
    enum class RiskLevel {
        LOW,
        MEDIUM,
        HIGH,
        UNKNOWN
    }
    
    /**
     * Información de migración de archivos
     */
    data class MigrationInfo(
        val packageName: String,
        val appName: String,
        val folders: List<FolderInfo>,
        val totalFiles: Int,
        val totalSizeBytes: Long
    ) {
        data class FolderInfo(
            val path: String,
            val fileCount: Int,
            val sizeBytes: Long
        )
    }
    
    /**
     * Etapas de migración
     */
    enum class MigrationStage {
        SCANNING_FILES,
        MIGRATING_FILES,
        INSTALLING_IN_SANDBOX,
        UNINSTALLING_FROM_PERSONAL,
        APPLYING_POLICIES,
        COMPLETED,
        ERROR
    }
    
    /**
     * Resultado de migración
     */
    data class MigrationResult(
        val success: Boolean,
        val filesMigrated: Int,
        val bytesMigrated: Long,
        val stage: MigrationStage,
        val needsAdb: Boolean = false,
        val adbCommands: List<String> = emptyList(),
        val errorMessage: String? = null
    )
    
    // ═══════════════════════════════════════════════════════════════════════════
    // STATUS & DETECTION
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Verifica el estado actual del sandbox
     */
    suspend fun getSandboxStatus(): SandboxStatus = withContext(Dispatchers.IO) {
        val profiles = userManager.userProfiles
        val workProfile = profiles.find { it != android.os.Process.myUserHandle() }
        val workProfileId = workProfile?.let { getUserId(it) }
        
        val isProfileOwner = try {
            devicePolicyManager.isProfileOwnerApp(context.packageName)
        } catch (e: Exception) {
            false
        }
        
        val isEnabled = workProfile?.let {
            try {
                !userManager.isQuietModeEnabled(it)
            } catch (e: Exception) {
                true
            }
        } ?: false
        
        // Contar apps en sandbox
        val sandboxedCount = getSandboxedApps().size
        
        // Si somos Profile Owner, configurar filtros cross-profile
        if (isProfileOwner) {
            setupCrossProfileFilters()
        }
        
        SandboxStatus(
            hasWorkProfile = workProfile != null,
            isProfileOwner = isProfileOwner,
            workProfileUserId = workProfileId,
            isWorkProfileEnabled = isEnabled,
            sandboxedAppsCount = sandboxedCount
        )
    }
    
    /**
     * Configura los filtros de Intent cross-profile para permitir
     * instalación de apps desde el perfil personal.
     */
    private fun setupCrossProfileFilters() {
        try {
            if (!devicePolicyManager.isProfileOwnerApp(context.packageName)) {
                Log.d(TAG, "Not profile owner, skipping cross-profile filter setup")
                return
            }
            
            // Limpiar filtros anteriores
            devicePolicyManager.clearCrossProfileIntentFilters(adminComponent)
            
            // Agregar filtro para ACTION_INSTALL_IN_SANDBOX
            val installFilter = android.content.IntentFilter().apply {
                addAction(ACTION_INSTALL_IN_SANDBOX)
                addCategory(Intent.CATEGORY_DEFAULT)
            }
            
            // FLAG_PARENT_CAN_ACCESS_MANAGED permite que el perfil personal inicie actividades en Work Profile
            devicePolicyManager.addCrossProfileIntentFilter(
                adminComponent,
                installFilter,
                DevicePolicyManager.FLAG_PARENT_CAN_ACCESS_MANAGED
            )
            
            Log.d(TAG, "Cross-profile intent filter configured for ACTION_INSTALL_IN_SANDBOX")
            
            // También configurar setCrossProfilePackages para Android 11+
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    devicePolicyManager.setCrossProfilePackages(adminComponent, setOf(context.packageName))
                    Log.d(TAG, "Cross-profile packages configured")
                } catch (e: Exception) {
                    Log.w(TAG, "Could not set cross-profile packages", e)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error setting up cross-profile filters", e)
        }
    }
    
    /**
     * Obtiene la lista de apps instaladas con info de sandbox
     * 
     * Si estamos en Work Profile: 
     *   - "Aisladas" = apps instaladas localmente en Work Profile
     *   - "Por aislar" = apps sugeridas que podrían existir en Personal
     * Si estamos en perfil Personal:
     *   - Muestra apps locales con estado de si están en sandbox
     */
    suspend fun getInstalledAppsForSandbox(): List<SandboxAppInfo> = withContext(Dispatchers.IO) {
        val isInWorkProfile = isRunningInWorkProfile()
        Log.d(TAG, "getInstalledAppsForSandbox: isInWorkProfile=$isInWorkProfile")
        
        // Apps locales del perfil actual
        val localApps = packageManager.getInstalledApplications(PackageManager.GET_META_DATA)
            .filter { appInfo ->
                (appInfo.flags and android.content.pm.ApplicationInfo.FLAG_SYSTEM) == 0 &&
                appInfo.packageName != context.packageName // Excluir NEVEN
            }
        
        Log.d(TAG, "getInstalledAppsForSandbox: found ${localApps.size} local user apps")
        localApps.forEach { Log.d(TAG, "  - ${it.packageName}") }
        
        if (isInWorkProfile) {
            // Estamos en Work Profile
            // Las apps locales son las "aisladas"
            val sandboxedApps = localApps.map { appInfo ->
                val appName = packageManager.getApplicationLabel(appInfo).toString()
                SandboxAppInfo(
                    packageName = appInfo.packageName,
                    appName = appName,
                    isSuggested = appInfo.packageName in SUGGESTED_SANDBOX_APPS,
                    isInSandbox = true, // Ya están en Work Profile = aisladas
                    isSuspended = false,
                    isInstalledInPersonal = true,
                    riskLevel = if (appInfo.packageName in SUGGESTED_SANDBOX_APPS) RiskLevel.HIGH else RiskLevel.UNKNOWN
                )
            }
            
            // Apps sugeridas que NO están instaladas en Work Profile (potencialmente por aislar)
            val installedPackages = localApps.map { it.packageName }.toSet()
            val suggestedNotInstalled = SUGGESTED_SANDBOX_APPS
                .filter { it !in installedPackages }
                .map { packageName ->
                    SandboxAppInfo(
                        packageName = packageName,
                        appName = getAppNameFromPackage(packageName),
                        isSuggested = true,
                        isInSandbox = false,
                        isSuspended = false,
                        isInstalledInPersonal = true, // Asumimos que sí está en Personal
                        riskLevel = RiskLevel.HIGH
                    )
                }
            
            return@withContext (sandboxedApps + suggestedNotInstalled).sortedWith(
                compareByDescending<SandboxAppInfo> { it.isInSandbox }
                    .thenByDescending { it.isSuggested }
                    .thenBy { it.appName }
            )
        }
        
        // Si estamos en Personal, comportamiento normal
        val sandboxedPackages = getSandboxedAppsPackages()
        
        localApps.map { appInfo ->
            val appName = packageManager.getApplicationLabel(appInfo).toString()
            val isSuggested = appInfo.packageName in SUGGESTED_SANDBOX_APPS
            val isInSandbox = appInfo.packageName in sandboxedPackages
            
            SandboxAppInfo(
                packageName = appInfo.packageName,
                appName = appName,
                isSuggested = isSuggested,
                isInSandbox = isInSandbox,
                isSuspended = false,
                isInstalledInPersonal = true,
                riskLevel = if (isSuggested) RiskLevel.HIGH else RiskLevel.UNKNOWN
            )
        }.sortedWith(
            compareByDescending<SandboxAppInfo> { it.isInSandbox }
                .thenByDescending { it.isSuggested }
                .thenBy { it.appName }
        )
    }
    
    /**
     * Obtiene nombre legible de un package name conocido
     */
    private fun getAppNameFromPackage(packageName: String): String {
        return when (packageName) {
            "com.whatsapp" -> "WhatsApp"
            "com.facebook.katana" -> "Facebook"
            "com.facebook.orca" -> "Messenger"
            "com.instagram.android" -> "Instagram"
            "com.twitter.android" -> "Twitter/X"
            "com.snapchat.android" -> "Snapchat"
            "org.telegram.messenger" -> "Telegram"
            "com.tiktok.android" -> "TikTok"
            "com.zhiliaoapp.musically" -> "TikTok"
            "com.google.android.apps.tachyon" -> "Google Duo"
            "com.discord" -> "Discord"
            "com.linkedin.android" -> "LinkedIn"
            "com.pinterest" -> "Pinterest"
            "com.spotify.music" -> "Spotify"
            "com.amazon.mShop.android.shopping" -> "Amazon"
            "com.ebay.mobile" -> "eBay"
            "com.mercadolibre" -> "MercadoLibre"
            else -> packageName.substringAfterLast(".")
        }
    }
    
    /**
     * Obtiene solo las apps sugeridas que están instaladas
     */
    suspend fun getSuggestedApps(): List<SandboxAppInfo> = withContext(Dispatchers.IO) {
        getInstalledAppsForSandbox().filter { it.isSuggested }
    }
    
    /**
     * Obtiene las apps actualmente en el sandbox
     */
    suspend fun getSandboxedApps(): List<SandboxAppInfo> = withContext(Dispatchers.IO) {
        getInstalledAppsForSandbox().filter { it.isInSandbox }
    }
    
    /**
     * Verifica si una app está instalada en el Work Profile
     * Usa LauncherApps API que funciona cross-profile
     */
    private suspend fun getSandboxedAppsPackages(): Set<String> = withContext(Dispatchers.IO) {
        try {
            val launcherApps = context.getSystemService(Context.LAUNCHER_APPS_SERVICE) as? android.content.pm.LauncherApps
            if (launcherApps == null) {
                Log.w(TAG, "LauncherApps not available")
                return@withContext emptySet()
            }
            
            val workProfile = getWorkProfileUserHandle()
            if (workProfile == null) {
                Log.w(TAG, "Work profile not found")
                return@withContext emptySet()
            }
            
            // Obtener actividades del Work Profile usando LauncherApps
            val activityList = launcherApps.getActivityList(null, workProfile)
            val packages = activityList
                .map { it.applicationInfo.packageName }
                .filter { it != context.packageName } // Excluir NEVEN (siempre está en Work Profile)
                .toSet()
            
            Log.d(TAG, "getSandboxedAppsPackages: found ${packages.size} user packages in work profile")
            packages
        } catch (e: Exception) {
            Log.e(TAG, "Error getting sandbox packages via LauncherApps", e)
            emptySet()
        }
    }
    
    /**
     * Verifica si una app específica está en el sandbox
     */
    suspend fun isAppInSandbox(packageName: String): Boolean = withContext(Dispatchers.IO) {
        packageName in getSandboxedAppsPackages()
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // FILE SCANNING & MIGRATION
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Escanea los archivos de medios de una app
     */
    suspend fun scanAppMediaFiles(packageName: String): MigrationInfo = withContext(Dispatchers.IO) {
        val appName = try {
            val appInfo = packageManager.getApplicationInfo(packageName, 0)
            packageManager.getApplicationLabel(appInfo).toString()
        } catch (e: Exception) {
            packageName
        }
        
        val folders = APP_MEDIA_FOLDERS[packageName] ?: emptyList()
        val storage = Environment.getExternalStorageDirectory()
        
        val folderInfos = mutableListOf<MigrationInfo.FolderInfo>()
        var totalFiles = 0
        var totalSize = 0L
        
        for (folderPath in folders) {
            val folder = File(storage, folderPath)
            if (folder.exists() && folder.isDirectory) {
                val (fileCount, size) = countFilesAndSize(folder)
                if (fileCount > 0) {
                    folderInfos.add(MigrationInfo.FolderInfo(folderPath, fileCount, size))
                    totalFiles += fileCount
                    totalSize += size
                }
            }
        }
        
        MigrationInfo(
            packageName = packageName,
            appName = appName,
            folders = folderInfos,
            totalFiles = totalFiles,
            totalSizeBytes = totalSize
        )
    }
    
    /**
     * Cuenta archivos y tamaño total de una carpeta recursivamente
     */
    private fun countFilesAndSize(folder: File): Pair<Int, Long> {
        var count = 0
        var size = 0L
        
        folder.walkTopDown().forEach { file ->
            if (file.isFile) {
                count++
                size += file.length()
            }
        }
        
        return Pair(count, size)
    }
    
    /**
     * Migra los archivos de una app al storage del Work Profile
     */
    suspend fun migrateFilesToSandbox(
        packageName: String,
        onProgress: (current: Int, total: Int) -> Unit
    ): Pair<Int, Long> = withContext(Dispatchers.IO) {
        val folders = APP_MEDIA_FOLDERS[packageName] ?: return@withContext Pair(0, 0L)
        val storage = Environment.getExternalStorageDirectory()
        
        // Destino en Work Profile: /storage/emulated/10/
        val sandboxStorage = "/storage/emulated/$WORK_PROFILE_USER_ID"
        
        var filesMigrated = 0
        var bytesMigrated = 0L
        var currentFile = 0
        
        // Primero contar total
        var totalFiles = 0
        for (folderPath in folders) {
            val folder = File(storage, folderPath)
            if (folder.exists()) {
                totalFiles += folder.walkTopDown().count { it.isFile }
            }
        }
        
        for (folderPath in folders) {
            val sourceFolder = File(storage, folderPath)
            if (!sourceFolder.exists()) continue
            
            val destFolderPath = "$sandboxStorage/$folderPath"
            
            // Crear carpeta destino
            executeShellCommand("mkdir -p \"$destFolderPath\"")
            
            // Mover archivos
            sourceFolder.walkTopDown().forEach { file ->
                if (file.isFile) {
                    try {
                        val relativePath = file.relativeTo(sourceFolder).path
                        val destPath = "$destFolderPath/$relativePath"
                        
                        // Crear directorio padre si es necesario
                        val destParent = File(destPath).parent
                        if (destParent != null) {
                            executeShellCommand("mkdir -p \"$destParent\"")
                        }
                        
                        // Mover archivo usando shell (para permisos cross-user)
                        val result = executeShellCommand("mv \"${file.absolutePath}\" \"$destPath\"")
                        if (!result.contains("error", ignoreCase = true)) {
                            filesMigrated++
                            bytesMigrated += file.length()
                        }
                    } catch (e: Exception) {
                        Log.w(TAG, "Failed to move file: ${file.path}", e)
                    }
                    
                    currentFile++
                    onProgress(currentFile, totalFiles)
                }
            }
            
            // Limpiar carpeta vacía
            try {
                if (sourceFolder.listFiles()?.isEmpty() == true) {
                    sourceFolder.delete()
                }
            } catch (e: Exception) {
                // Ignorar
            }
        }
        
        Pair(filesMigrated, bytesMigrated)
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // APP INSTALLATION / UNINSTALLATION
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Instala una app en el Work Profile usando DevicePolicyManager.installExistingPackage()
     * 
     * Esta API permite a un Profile Owner instalar una app que ya existe en otro usuario
     * (el perfil personal) directamente en el Work Profile, sin necesidad de ADB.
     * 
     * Estrategia:
     * 1. Si estamos en Work Profile (somos Profile Owner): usar installExistingPackage() directamente
     * 2. Si estamos en perfil personal: usar CrossProfileApps para invocar SandboxInstallActivity
     *    en el Work Profile, que sí tiene permisos de Profile Owner
     * 
     * Requisitos:
     * - NEVEN debe ser Profile Owner del Work Profile
     * - La app debe estar instalada en el perfil personal (user 0)
     */
    suspend fun installAppInSandbox(packageName: String): InstallResult = withContext(Dispatchers.IO) {
        try {
            val isInWorkProfile = isRunningInWorkProfile()
            Log.d(TAG, "installAppInSandbox: running in work profile = $isInWorkProfile")
            
            if (isInWorkProfile) {
                // Estamos en el Work Profile, intentar DevicePolicyManager
                val success = try {
                    devicePolicyManager.installExistingPackage(adminComponent, packageName)
                } catch (e: SecurityException) {
                    Log.e(TAG, "SecurityException installing $packageName (requires Device Owner, not just Profile Owner)", e)
                    false
                } catch (e: IllegalArgumentException) {
                    Log.e(TAG, "Package $packageName not found in personal profile", e)
                    false
                }
                
                if (success) {
                    Log.d(TAG, "installExistingPackage $packageName: SUCCESS")
                    return@withContext InstallResult(success = true, needsAdb = false)
                } else {
                    // installExistingPackage falló - abrir Play Store como alternativa
                    Log.d(TAG, "installExistingPackage failed, opening Play Store for $packageName")
                    return@withContext InstallResult(
                        success = false,
                        needsAdb = false,
                        errorMessage = "OPEN_PLAY_STORE",
                        packageName = packageName
                    )
                }
            }
            
            // Estamos en perfil personal - el ContentProvider cross-profile no funciona directamente
            // Guardar en SharedPreferences locales para mostrar en UI
            Log.d(TAG, "Running in personal profile, saving pending install to local prefs...")
            
            val workProfile = getWorkProfileUserHandle()
            if (workProfile != null) {
                // Guardar en SharedPreferences locales (solo para tracking de UI)
                try {
                    val prefs = context.getSharedPreferences("sandbox_pending_local", Context.MODE_PRIVATE)
                    val pendingSet = prefs.getStringSet("pending_packages", mutableSetOf())?.toMutableSet() ?: mutableSetOf()
                    pendingSet.add(packageName)
                    prefs.edit().putStringSet("pending_packages", pendingSet).apply()
                    Log.d(TAG, "Saved pending install to local prefs: $packageName")
                    
                    // También guardar en archivo en Downloads (compartido entre perfiles)
                    try {
                        val downloadsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
                        val pendingFile = java.io.File(downloadsDir, ".neven_pending_sandbox")
                        
                        // Leer pendientes existentes
                        val existingPackages = if (pendingFile.exists()) {
                            pendingFile.readText().lines().filter { it.isNotBlank() }.toMutableSet()
                        } else {
                            mutableSetOf()
                        }
                        existingPackages.add(packageName)
                        pendingFile.writeText(existingPackages.joinToString("\n"))
                        Log.d(TAG, "Saved pending install to shared Downloads file: $packageName")
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to save to Downloads file", e)
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to save pending install to prefs", e)
                }
                
                // Intentar CrossProfileApps como fallback (puede funcionar si el usuario 
                // cambia al Work Profile pronto)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && crossProfileApps != null) {
                    try {
                        val intent = Intent(ACTION_INSTALL_IN_SANDBOX).apply {
                            component = ComponentName(context.packageName, 
                                "com.neven.launcher.services.SandboxInstallActivity")
                            putExtra(EXTRA_PACKAGE_NAME, packageName)
                            putExtra("action", "install")
                        }
                        
                        crossProfileApps!!.startActivity(intent, workProfile, null)
                        Log.d(TAG, "Started SandboxInstallActivity for $packageName (may execute when Work Profile becomes active)")
                        
                        kotlinx.coroutines.delay(1500)
                        
                        // Verificar si se instaló
                        val installed = isAppInSandbox(packageName)
                        if (installed) {
                            // Remover de pendientes locales
                            try {
                                val prefs = context.getSharedPreferences("sandbox_pending_local", Context.MODE_PRIVATE)
                                val pendingSet = prefs.getStringSet("pending_packages", mutableSetOf())?.toMutableSet() ?: mutableSetOf()
                                pendingSet.remove(packageName)
                                prefs.edit().putStringSet("pending_packages", pendingSet).apply()
                            } catch (e: Exception) { }
                            
                            return@withContext InstallResult(
                                success = true, 
                                needsAdb = false,
                                packageName = packageName
                            )
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "CrossProfileApps failed", e)
                    }
                }
                
                // Reportar como pendiente - la instalación ocurrirá cuando el usuario 
                // abra NEVEN desde el Work Profile
                return@withContext InstallResult(
                    success = true,  // Marcamos como éxito porque está en cola
                    needsAdb = false,
                    packageName = packageName,
                    errorMessage = "PENDING_WORK_PROFILE"
                )
            }
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                // Android 9-10 - solo podemos usar startMainActivity
                val workProfile = getWorkProfileUserHandle()
                
                if (workProfile != null && crossProfileApps != null) {
                    try {
                        // Necesitamos usar la Activity principal
                        // Guardamos el paquete en SharedPreferences para que la Activity lo procese
                        val prefs = context.getSharedPreferences("sandbox_pending", Context.MODE_PRIVATE)
                        prefs.edit().putString("pending_install", packageName).apply()
                        
                        crossProfileApps!!.startMainActivity(
                            ComponentName(context.packageName, 
                                "com.neven.launcher.services.SandboxInstallActivity"),
                            workProfile
                        )
                        
                        Log.d(TAG, "Started main activity in Work Profile, pending install: $packageName")
                        
                        kotlinx.coroutines.delay(1500)
                        
                        // Confiamos en que la Activity hizo su trabajo
                        return@withContext InstallResult(
                            success = true, 
                            needsAdb = false,
                            packageName = packageName
                        )
                    } catch (e: Exception) {
                        Log.e(TAG, "CrossProfileApps failed", e)
                    }
                }
            }
            
            // Fallback: el método cross-profile no funcionó
            Log.w(TAG, "Cross-profile install not available, manual intervention needed")
            InstallResult(
                success = false,
                needsAdb = false,
                errorMessage = "SETUP_CROSS_PROFILE_NEEDED"
            )
        } catch (e: Exception) {
            Log.e(TAG, "Error installing $packageName in sandbox", e)
            InstallResult(success = false, needsAdb = false, errorMessage = e.message)
        }
    }
    
    /**
     * Resultado de instalación
     */
    data class InstallResult(
        val success: Boolean,
        val needsAdb: Boolean = false,
        val adbCommands: List<String> = emptyList(),
        val packageName: String? = null,
        val errorMessage: String? = null
    )
    
    /**
     * Desinstala una app del perfil personal (User 0)
     */
    suspend fun uninstallFromPersonalProfile(packageName: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val result = executeShellCommand("pm uninstall --user 0 $packageName")
            val success = result.contains("Success", ignoreCase = true)
            
            Log.d(TAG, "Uninstall $packageName from personal: ${if (success) "success" else "failed"}")
            success
        } catch (e: Exception) {
            Log.e(TAG, "Error uninstalling $packageName from personal", e)
            false
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // FULL MIGRATION FLOW
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Migración completa de una app al sandbox
     * 
     * Flujo:
     * 1. Escanear archivos
     * 2. Migrar archivos al storage del Work Profile
     * 3. Instalar app en Work Profile usando DevicePolicyManager
     * 4. Desinstalar del perfil personal
     * 5. Aplicar políticas de aislamiento
     */
    suspend fun migrateAppToSandbox(
        packageName: String,
        onProgress: (stage: MigrationStage, progress: Float, message: String) -> Unit
    ): MigrationResult = withContext(Dispatchers.IO) {
        var filesMigrated = 0
        var bytesMigrated = 0L
        
        try {
            // Si estamos en Work Profile, ir directo a instalación (sin migración de archivos)
            if (isRunningInWorkProfile()) {
                onProgress(MigrationStage.INSTALLING_IN_SANDBOX, 0f, "Installing app...")
                val installResult = installAppInSandbox(packageName)
                
                if (installResult.success) {
                    onProgress(MigrationStage.COMPLETED, 1f, "Installed")
                    return@withContext MigrationResult(
                        success = true,
                        filesMigrated = 0,
                        bytesMigrated = 0,
                        stage = MigrationStage.COMPLETED
                    )
                } else {
                    // Falló - propagar el error (OPEN_PLAY_STORE, etc.)
                    return@withContext MigrationResult(
                        success = false,
                        filesMigrated = 0,
                        bytesMigrated = 0,
                        stage = MigrationStage.ERROR,
                        errorMessage = installResult.errorMessage
                    )
                }
            }
            
            // Estamos en perfil Personal - flujo normal con migración de archivos
            // 1. Escanear archivos
            onProgress(MigrationStage.SCANNING_FILES, 0f, "Scanning files...")
            val migrationInfo = scanAppMediaFiles(packageName)
            onProgress(MigrationStage.SCANNING_FILES, 1f, "Found ${migrationInfo.totalFiles} files")
            
            // 2. Migrar archivos
            if (migrationInfo.totalFiles > 0) {
                onProgress(MigrationStage.MIGRATING_FILES, 0f, "Moving files...")
                val (files, bytes) = migrateFilesToSandbox(packageName) { current, total ->
                    val progress = if (total > 0) current.toFloat() / total else 0f
                    onProgress(MigrationStage.MIGRATING_FILES, progress, "Moving $current of $total files")
                }
                filesMigrated = files
                bytesMigrated = bytes
            }
            onProgress(MigrationStage.MIGRATING_FILES, 1f, "Files migrated: $filesMigrated")
            
            // 3. Instalar en sandbox usando DevicePolicyManager
            onProgress(MigrationStage.INSTALLING_IN_SANDBOX, 0f, "Installing in sandbox...")
            val installResult = installAppInSandbox(packageName)
            
            if (installResult.success) {
                // Verificar si la instalación quedó pendiente
                val isPending = installResult.errorMessage == "PENDING_WORK_PROFILE"
                
                onProgress(MigrationStage.INSTALLING_IN_SANDBOX, 1f, 
                    if (isPending) "Installation queued" else "Installed in sandbox")
                
                // Solo desinstalar del perfil personal si la app YA se instaló en el sandbox
                // Si está pendiente, NO desinstalar (el usuario perdería acceso a la app)
                if (!isPending) {
                    // 4. Desinstalar del perfil personal
                    onProgress(MigrationStage.UNINSTALLING_FROM_PERSONAL, 0f, "Removing from main profile...")
                    uninstallFromPersonalProfile(packageName)
                    onProgress(MigrationStage.UNINSTALLING_FROM_PERSONAL, 1f, "Removed")
                    
                    // 5. Aplicar políticas
                    onProgress(MigrationStage.APPLYING_POLICIES, 0f, "Applying isolation policies...")
                    applyIsolationPolicies()
                    onProgress(MigrationStage.APPLYING_POLICIES, 1f, "Policies applied")
                }
                
                onProgress(MigrationStage.COMPLETED, 1f, 
                    if (isPending) "Pending completion from Work Profile" else "Migration complete")
                
                MigrationResult(
                    success = true,
                    filesMigrated = filesMigrated,
                    bytesMigrated = bytesMigrated,
                    stage = MigrationStage.COMPLETED,
                    errorMessage = installResult.errorMessage  // Propagar PENDING_WORK_PROFILE
                )
            } else {
                // Instalación falló
                MigrationResult(
                    success = false,
                    filesMigrated = filesMigrated,
                    bytesMigrated = bytesMigrated,
                    stage = MigrationStage.ERROR,
                    errorMessage = installResult.errorMessage ?: "Failed to install app in sandbox"
                )
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Migration failed for $packageName", e)
            MigrationResult(
                success = false,
                filesMigrated = filesMigrated,
                bytesMigrated = bytesMigrated,
                stage = MigrationStage.ERROR,
                errorMessage = e.message ?: "Unknown error"
            )
        }
    }
    
    /**
     * Remueve una app del sandbox y la restaura al perfil personal
     */
    suspend fun removeAppFromSandbox(
        packageName: String,
        migrateFilesBack: Boolean = true,
        onProgress: (stage: MigrationStage, progress: Float, message: String) -> Unit
    ): MigrationResult = withContext(Dispatchers.IO) {
        var filesMigrated = 0
        var bytesMigrated = 0L
        
        try {
            // 1. Reinstalar en perfil personal
            onProgress(MigrationStage.INSTALLING_IN_SANDBOX, 0f, "Restoring to main profile...")
            
            // Obtener APK del sandbox
            val result = executeShellCommand("pm path --user $WORK_PROFILE_USER_ID $packageName")
            val apkPath = result.lines()
                .firstOrNull { it.startsWith("package:") }
                ?.removePrefix("package:")
                ?.trim()
            
            if (apkPath != null) {
                executeShellCommand("pm install --user 0 \"$apkPath\"")
            }
            onProgress(MigrationStage.INSTALLING_IN_SANDBOX, 1f, "Restored to main profile")
            
            // 2. Migrar archivos de vuelta si se solicita
            if (migrateFilesBack) {
                onProgress(MigrationStage.MIGRATING_FILES, 0f, "Moving files back...")
                // Invertir la migración
                val folders = APP_MEDIA_FOLDERS[packageName] ?: emptyList()
                val sandboxStorage = "/storage/emulated/$WORK_PROFILE_USER_ID"
                val personalStorage = Environment.getExternalStorageDirectory().absolutePath
                
                for (folderPath in folders) {
                    val sourceFolder = "$sandboxStorage/$folderPath"
                    val destFolder = "$personalStorage/$folderPath"
                    
                    executeShellCommand("mkdir -p \"$destFolder\"")
                    executeShellCommand("mv \"$sourceFolder\"/* \"$destFolder\"/ 2>/dev/null || true")
                }
                onProgress(MigrationStage.MIGRATING_FILES, 1f, "Files restored")
            }
            
            // 3. Desinstalar del sandbox
            onProgress(MigrationStage.UNINSTALLING_FROM_PERSONAL, 0f, "Removing from sandbox...")
            executeShellCommand("pm uninstall --user $WORK_PROFILE_USER_ID $packageName")
            onProgress(MigrationStage.UNINSTALLING_FROM_PERSONAL, 1f, "Removed from sandbox")
            
            onProgress(MigrationStage.COMPLETED, 1f, "App restored")
            
            MigrationResult(
                success = true,
                filesMigrated = filesMigrated,
                bytesMigrated = bytesMigrated,
                stage = MigrationStage.COMPLETED
            )
            
        } catch (e: Exception) {
            Log.e(TAG, "Remove from sandbox failed for $packageName", e)
            MigrationResult(
                success = false,
                filesMigrated = 0,
                bytesMigrated = 0,
                stage = MigrationStage.ERROR,
                errorMessage = e.message
            )
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // ISOLATION POLICIES
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Aplica políticas de aislamiento para el Work Profile
     */
    suspend fun applyIsolationPolicies(): Boolean = withContext(Dispatchers.IO) {
        try {
            if (!devicePolicyManager.isProfileOwnerApp(context.packageName)) {
                Log.w(TAG, "Cannot apply policies - not Profile Owner")
                return@withContext false
            }
            
            // Deshabilitar compartir contactos entre perfiles
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                devicePolicyManager.setCrossProfileContactsSearchDisabled(adminComponent, true)
            }
            
            // Deshabilitar compartir calendario
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                devicePolicyManager.setCrossProfileCalendarPackages(adminComponent, emptySet())
            }
            
            Log.d(TAG, "Isolation policies applied")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Error applying isolation policies", e)
            false
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // SUSPEND / UNSUSPEND (Original functionality)
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Suspende una app en el sandbox (requiere ser Profile Owner)
     */
    suspend fun suspendApp(packageName: String): Boolean = withContext(Dispatchers.IO) {
        try {
            if (!devicePolicyManager.isProfileOwnerApp(context.packageName)) {
                Log.w(TAG, "Cannot suspend app - not Profile Owner")
                return@withContext false
            }
            
            val packages = arrayOf(packageName)
            val result = devicePolicyManager.setPackagesSuspended(
                adminComponent,
                packages,
                true
            )
            
            val success = result.isEmpty()
            Log.d(TAG, "Suspend $packageName: ${if (success) "success" else "failed"}")
            success
        } catch (e: Exception) {
            Log.e(TAG, "Error suspending $packageName", e)
            false
        }
    }
    
    /**
     * Reanuda una app suspendida
     */
    suspend fun unsuspendApp(packageName: String): Boolean = withContext(Dispatchers.IO) {
        try {
            if (!devicePolicyManager.isProfileOwnerApp(context.packageName)) {
                Log.w(TAG, "Cannot unsuspend app - not Profile Owner")
                return@withContext false
            }
            
            val packages = arrayOf(packageName)
            val result = devicePolicyManager.setPackagesSuspended(
                adminComponent,
                packages,
                false
            )
            
            val success = result.isEmpty()
            Log.d(TAG, "Unsuspend $packageName: ${if (success) "success" else "failed"}")
            success
        } catch (e: Exception) {
            Log.e(TAG, "Error unsuspending $packageName", e)
            false
        }
    }
    
    /**
     * Activa/desactiva el modo silencioso del Work Profile (congela todo el perfil)
     */
    suspend fun setWorkProfileQuietMode(enabled: Boolean): Boolean = withContext(Dispatchers.IO) {
        try {
            val workProfile = getWorkProfileHandle() ?: return@withContext false
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                userManager.requestQuietModeEnabled(enabled, workProfile)
                true
            } else {
                false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error setting quiet mode", e)
            false
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // UTILITY FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Ejecuta un comando shell y retorna el output
     */
    private fun executeShellCommand(command: String): String {
        return try {
            val process = Runtime.getRuntime().exec(arrayOf("sh", "-c", command))
            val output = process.inputStream.bufferedReader().readText()
            val error = process.errorStream.bufferedReader().readText()
            process.waitFor()
            
            if (error.isNotEmpty() && !error.contains("Warning", ignoreCase = true)) {
                Log.w(TAG, "Shell command error: $error")
            }
            
            output + error
        } catch (e: Exception) {
            Log.e(TAG, "Error executing: $command", e)
            "error: ${e.message}"
        }
    }
    
    /**
     * Obtiene el UserHandle del Work Profile
     */
    private fun getWorkProfileHandle(): UserHandle? {
        return userManager.userProfiles.find { it != android.os.Process.myUserHandle() }
    }
    
    /**
     * Extrae el user ID de un UserHandle
     */
    private fun getUserId(userHandle: UserHandle): Int {
        return try {
            val method = UserHandle::class.java.getMethod("getIdentifier")
            method.invoke(userHandle) as Int
        } catch (e: Exception) {
            userHandle.hashCode()
        }
    }
    
    /**
     * Verifica si NEVEN puede crear un Work Profile
     */
    fun canCreateWorkProfile(): Boolean {
        return try {
            packageManager.hasSystemFeature(PackageManager.FEATURE_MANAGED_USERS)
        } catch (e: Exception) {
            false
        }
    }
    
    /**
     * Inicia el proceso de provisioning del Work Profile
     */
    fun startWorkProfileProvisioning(): Intent {
        return Intent(DevicePolicyManager.ACTION_PROVISION_MANAGED_PROFILE).apply {
            putExtra(
                DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME,
                adminComponent
            )
            putExtra(
                DevicePolicyManager.EXTRA_PROVISIONING_SKIP_ENCRYPTION,
                true
            )
        }
    }
    
    /**
     * Formatea bytes a string legible
     */
    fun formatFileSize(bytes: Long): String {
        return when {
            bytes < 1024 -> "$bytes B"
            bytes < 1024 * 1024 -> "${bytes / 1024} KB"
            bytes < 1024 * 1024 * 1024 -> "${bytes / (1024 * 1024)} MB"
            else -> String.format("%.1f GB", bytes / (1024.0 * 1024 * 1024))
        }
    }
}
