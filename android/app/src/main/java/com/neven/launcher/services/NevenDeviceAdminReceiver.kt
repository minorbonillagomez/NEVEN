package com.neven.launcher.services

import android.app.admin.DeviceAdminReceiver
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.util.Log

/**
 * Device Admin Receiver para NEVEN Sandbox
 * 
 * Este componente permite a NEVEN actuar como Profile Owner del Work Profile,
 * habilitando el control de apps en el sandbox (freeze/unfreeze).
 * 
 * Para configurar como Profile Owner (durante desarrollo):
 * adb shell dpm set-profile-owner --user [work_profile_user_id] com.neven.launcher/.services.NevenDeviceAdminReceiver
 */
class NevenDeviceAdminReceiver : DeviceAdminReceiver() {
    
    companion object {
        private const val TAG = "NevenDeviceAdmin"
    }
    
    override fun onEnabled(context: Context, intent: Intent) {
        super.onEnabled(context, intent)
        Log.d(TAG, "Device admin enabled for NEVEN Sandbox")
        
        // Configurar filtros cross-profile para permitir instalación desde perfil personal
        setupCrossProfileIntentFilters(context)
    }
    
    override fun onDisabled(context: Context, intent: Intent) {
        super.onDisabled(context, intent)
        Log.d(TAG, "Device admin disabled")
    }
    
    override fun onProfileProvisioningComplete(context: Context, intent: Intent) {
        super.onProfileProvisioningComplete(context, intent)
        Log.d(TAG, "Work Profile provisioning complete - Sandbox ready")
        
        // Marcar el provisioning como completado para que la detección funcione
        val setupManager = SandboxSetupManager(context)
        setupManager.markProvisioningCompleted()
        Log.d(TAG, "Provisioning marked as complete in SharedPreferences")
        
        // Configurar filtros cross-profile
        setupCrossProfileIntentFilters(context)
    }
    
    /**
     * Configura los filtros de Intent cross-profile para permitir que
     * la app del perfil personal pueda comunicarse con el Work Profile.
     */
    private fun setupCrossProfileIntentFilters(context: Context) {
        val dpm = context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        val adminComponent = ComponentName(context, NevenDeviceAdminReceiver::class.java)
        
        // Verificar que somos Profile Owner
        if (!dpm.isProfileOwnerApp(context.packageName)) {
            Log.w(TAG, "Not profile owner, cannot setup cross-profile filters")
            return
        }
        
        try {
            // Limpiar filtros anteriores
            dpm.clearCrossProfileIntentFilters(adminComponent)
            
            // Agregar filtro para ACTION_INSTALL_IN_SANDBOX
            // Permite que el perfil personal envíe este intent al Work Profile
            val installFilter = IntentFilter().apply {
                addAction(SandboxManager.ACTION_INSTALL_IN_SANDBOX)
                addCategory(Intent.CATEGORY_DEFAULT)
            }
            
            // FLAG_PARENT_CAN_ACCESS_MANAGED = permite que el perfil personal inicie actividades en el Work Profile
            dpm.addCrossProfileIntentFilter(
                adminComponent,
                installFilter,
                DevicePolicyManager.FLAG_PARENT_CAN_ACCESS_MANAGED
            )
            
            Log.d(TAG, "Cross-profile intent filters configured successfully")
            
            // También habilitar el acceso cross-profile para nuestra app
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    // Permitir que nuestra app se comunique entre perfiles
                    val packages = setOf(context.packageName)
                    dpm.setCrossProfilePackages(adminComponent, packages)
                    Log.d(TAG, "Cross-profile package access configured for ${context.packageName}")
                } catch (e: Exception) {
                    Log.w(TAG, "Could not set cross-profile packages", e)
                }
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Error setting up cross-profile intent filters", e)
        }
    }
}
