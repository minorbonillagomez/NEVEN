package com.neven.launcher.services

import android.app.Activity
import android.app.admin.DevicePolicyManager
import android.content.BroadcastReceiver
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Toast

/**
 * Activity transparente que recibe Intents cross-profile para instalar apps en el Work Profile.
 * 
 * Esta Activity se ejecuta en el Work Profile cuando es invocada desde el perfil personal
 * usando CrossProfileApps.startActivity(). Dado que en el Work Profile somos Profile Owner,
 * podemos usar DevicePolicyManager.installExistingPackage() para instalar la app.
 * 
 * NOTA: En Android moderno, las Activities en usuarios no-activos no pueden ejecutar código
 * de forma confiable. Por eso también existe SandboxInstallReceiver como alternativa.
 */
class SandboxInstallActivity : Activity() {
    
    companion object {
        private const val TAG = "SandboxInstallActivity"
        const val EXTRA_PACKAGE_NAME = "package_name"
        const val EXTRA_ACTION = "action"
        
        const val ACTION_INSTALL = "install"
        const val ACTION_UNINSTALL = "uninstall"
        const val ACTION_SETUP_FILTERS = "setup_filters"
        
        const val RESULT_INSTALL_SUCCESS = 100
        const val RESULT_INSTALL_FAILED = 101
        const val RESULT_NOT_PROFILE_OWNER = 102
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        Log.d(TAG, "SandboxInstallActivity onCreate started")
        
        val devicePolicyManager = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        val adminComponent = ComponentName(this, NevenDeviceAdminReceiver::class.java)
        val isProfileOwner = devicePolicyManager.isProfileOwnerApp(this.packageName)
        
        Log.d(TAG, "SandboxInstallActivity started. isProfileOwner=$isProfileOwner")
        
        // Si somos Profile Owner, siempre configurar los filtros cross-profile
        if (isProfileOwner) {
            setupCrossProfileFilters(devicePolicyManager, adminComponent)
            // IMPORTANTE: Procesar instalaciones pendientes del archivo compartido
            processPendingInstalls(devicePolicyManager, adminComponent)
        }
        
        // Intentar obtener el paquete del Intent
        var packageName = intent.getStringExtra(EXTRA_PACKAGE_NAME)
        val action = intent.getStringExtra(EXTRA_ACTION) ?: ACTION_INSTALL
        
        // Si no viene en el Intent, revisar SharedPreferences (para Android 9-10 con startMainActivity)
        if (packageName.isNullOrEmpty()) {
            val prefs = getSharedPreferences("sandbox_pending", Context.MODE_PRIVATE)
            packageName = prefs.getString("pending_install", null)
            // Limpiar el pending
            prefs.edit().remove("pending_install").apply()
        }
        
        // Si aún no hay paquete, revisar el clipboard (compartido entre perfiles)
        if (packageName.isNullOrEmpty() && isProfileOwner) {
            try {
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
                val clipData = clipboard.primaryClip
                if (clipData != null && clipData.itemCount > 0) {
                    val text = clipData.getItemAt(0).text?.toString()
                    // Verificar que tenga el formato esperado: neven_sandbox_install:com.package.name
                    if (text != null && text.startsWith("neven_sandbox_install:")) {
                        packageName = text.removePrefix("neven_sandbox_install:")
                        Log.d(TAG, "Found package in clipboard: $packageName")
                        // Limpiar el clipboard
                        clipboard.setPrimaryClip(android.content.ClipData.newPlainText("", ""))
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Could not read clipboard", e)
            }
        }
        
        Log.d(TAG, "Action=$action, package=$packageName")
        
        // Si no hay paquete para instalar, solo terminamos (era solo setup de filtros)
        if (packageName.isNullOrEmpty()) {
            Log.d(TAG, "No package to install, finishing (filters configured)")
            if (isProfileOwner) {
                Toast.makeText(this, "Sandbox activo", Toast.LENGTH_SHORT).show()
            }
            finish()
            return
        }
        
        // Verificar que somos Profile Owner
        if (!isProfileOwner) {
            // En el perfil personal, simplemente cerramos sin mensaje de error
            // porque "NEVEN SANDBOX" solo tiene sentido en el Work Profile
            Log.d(TAG, "Not profile owner - this is expected in personal profile, closing silently")
            finish()
            return
        }
        
        when (action) {
            ACTION_INSTALL -> {
                try {
                    Log.d(TAG, "Calling installExistingPackage for $packageName")
                    val success = devicePolicyManager.installExistingPackage(adminComponent, packageName)
                    Log.d(TAG, "installExistingPackage($packageName) = $success")
                    
                    if (success) {
                        Toast.makeText(this, "$packageName instalado en Sandbox", Toast.LENGTH_SHORT).show()
                        setResult(RESULT_INSTALL_SUCCESS)
                    } else {
                        Toast.makeText(this, "Error instalando $packageName", Toast.LENGTH_SHORT).show()
                        setResult(RESULT_INSTALL_FAILED)
                    }
                } catch (e: SecurityException) {
                    Log.e(TAG, "SecurityException installing $packageName", e)
                    Toast.makeText(this, "Error de permisos: ${e.message}", Toast.LENGTH_LONG).show()
                    setResult(RESULT_INSTALL_FAILED)
                } catch (e: IllegalArgumentException) {
                    Log.e(TAG, "IllegalArgumentException - package not found in other profile", e)
                    Toast.makeText(this, "Paquete no encontrado en perfil personal", Toast.LENGTH_LONG).show()
                    setResult(RESULT_INSTALL_FAILED)
                } catch (e: Exception) {
                    Log.e(TAG, "Error installing $packageName", e)
                    Toast.makeText(this, "Error: ${e.message}", Toast.LENGTH_LONG).show()
                    setResult(RESULT_INSTALL_FAILED)
                }
            }
            ACTION_UNINSTALL -> {
                Toast.makeText(this, "Desinstalar desde Settings > Apps", Toast.LENGTH_SHORT).show()
                setResult(RESULT_OK)
            }
            ACTION_SETUP_FILTERS -> {
                // Ya se configuraron arriba
                Toast.makeText(this, "Filtros cross-profile configurados", Toast.LENGTH_SHORT).show()
                setResult(RESULT_OK)
            }
        }
        
        finish()
    }
    
    /**
     * Procesa las instalaciones pendientes.
     * Intenta leer del clipboard si hay paquete pendiente.
     */
    private fun processPendingInstalls(dpm: DevicePolicyManager, adminComponent: ComponentName) {
        Log.d(TAG, "SandboxInstallActivity opened in Work Profile - checking for pending installs")
        
        // No mostrar toast aquí - se mostrará después si hay o no instalación
    }
    
    /**
     * Configura los filtros de Intent cross-profile para permitir
     * instalación de apps desde el perfil personal.
     */
    private fun setupCrossProfileFilters(dpm: DevicePolicyManager, adminComponent: ComponentName) {
        try {
            // Limpiar filtros anteriores
            dpm.clearCrossProfileIntentFilters(adminComponent)
            
            // Agregar filtro para ACTION_INSTALL_IN_SANDBOX
            val installFilter = IntentFilter().apply {
                addAction(SandboxManager.ACTION_INSTALL_IN_SANDBOX)
                addCategory(Intent.CATEGORY_DEFAULT)
            }
            
            // FLAG_PARENT_CAN_ACCESS_MANAGED permite que el perfil personal inicie actividades en Work Profile
            dpm.addCrossProfileIntentFilter(
                adminComponent,
                installFilter,
                DevicePolicyManager.FLAG_PARENT_CAN_ACCESS_MANAGED
            )
            
            Log.d(TAG, "Cross-profile intent filter configured for ACTION_INSTALL_IN_SANDBOX")
            
            // También configurar setCrossProfilePackages para Android 11+
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    dpm.setCrossProfilePackages(adminComponent, setOf(this.packageName))
                    Log.d(TAG, "Cross-profile packages configured")
                } catch (e: Exception) {
                    Log.w(TAG, "Could not set cross-profile packages", e)
                }
            }
            
            // Configurar INTERACT_ACROSS_PROFILES para nuestra app
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    // Usar setCrossProfileCallerIdDisabled para habilitar comunicación
                    @Suppress("DEPRECATION")
                    dpm.setCrossProfileCallerIdDisabled(adminComponent, false)
                    @Suppress("DEPRECATION")
                    dpm.setCrossProfileContactsSearchDisabled(adminComponent, false)
                    Log.d(TAG, "Cross-profile caller ID and contacts search enabled")
                } catch (e: Exception) {
                    Log.w(TAG, "Could not configure cross-profile settings", e)
                }
            }
            
            // Marcar que los filtros están configurados
            val setupManager = SandboxSetupManager(this)
            setupManager.markCrossProfileFiltersConfigured()
            
        } catch (e: Exception) {
            Log.e(TAG, "Error setting up cross-profile filters", e)
        }
    }
}

/**
 * BroadcastReceiver que puede instalar apps en el Work Profile.
 * A diferencia de la Activity, los BroadcastReceivers pueden ejecutarse
 * en usuarios no activos.
 */
class SandboxInstallReceiver : BroadcastReceiver() {
    
    companion object {
        private const val TAG = "SandboxInstallReceiver"
        const val ACTION_INSTALL_IN_SANDBOX = "com.neven.launcher.action.BROADCAST_INSTALL_IN_SANDBOX"
        const val EXTRA_PACKAGE_NAME = "package_name"
    }
    
    override fun onReceive(context: Context, intent: Intent) {
        Log.d(TAG, "SandboxInstallReceiver onReceive")
        
        val packageName = intent.getStringExtra(EXTRA_PACKAGE_NAME)
        if (packageName.isNullOrEmpty()) {
            Log.w(TAG, "No package name provided")
            return
        }
        
        val devicePolicyManager = context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        val adminComponent = ComponentName(context, NevenDeviceAdminReceiver::class.java)
        
        if (!devicePolicyManager.isProfileOwnerApp(context.packageName)) {
            Log.e(TAG, "Not profile owner, cannot install")
            return
        }
        
        try {
            Log.d(TAG, "Installing $packageName via receiver")
            val success = devicePolicyManager.installExistingPackage(adminComponent, packageName)
            Log.d(TAG, "installExistingPackage result: $success")
            
            // Guardar resultado para que el perfil personal lo lea
            val prefs = context.getSharedPreferences("sandbox_install_result", Context.MODE_PRIVATE)
            prefs.edit()
                .putString("last_package", packageName)
                .putBoolean("last_success", success)
                .putLong("last_timestamp", System.currentTimeMillis())
                .apply()
                
        } catch (e: Exception) {
            Log.e(TAG, "Error installing $packageName", e)
        }
    }
}
