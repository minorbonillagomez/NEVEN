package com.neven.launcher.services

import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.ContentProvider
import android.content.ContentValues
import android.content.Context
import android.content.UriMatcher
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Log

/**
 * ContentProvider que permite comunicación cross-profile para el Sandbox.
 * 
 * Este provider se ejecuta en el Work Profile donde NEVEN es Profile Owner.
 * El perfil personal puede hacer queries para:
 * - Instalar apps en el sandbox (call "install")
 * - Verificar estado del sandbox (query)
 * 
 * La comunicación cross-profile funciona porque:
 * 1. El Profile Owner configura setCrossProfilePackages()
 * 2. El ContentProvider está exportado con el permiso correcto
 * 3. Android permite queries a ContentProviders cross-profile
 */
class SandboxContentProvider : ContentProvider() {
    
    companion object {
        private const val TAG = "SandboxContentProvider"
        
        const val AUTHORITY = "com.neven.launcher.sandbox"
        
        // URIs
        val CONTENT_URI: Uri = Uri.parse("content://$AUTHORITY")
        val URI_STATUS: Uri = Uri.parse("content://$AUTHORITY/status")
        val URI_INSTALL: Uri = Uri.parse("content://$AUTHORITY/install")
        
        // URI matcher codes
        private const val CODE_STATUS = 1
        private const val CODE_INSTALL = 2
        
        // Call methods
        const val METHOD_INSTALL = "install"
        const val METHOD_UNINSTALL = "uninstall"
        const val METHOD_GET_STATUS = "get_status"
        
        // Extras
        const val EXTRA_PACKAGE_NAME = "package_name"
        const val EXTRA_SUCCESS = "success"
        const val EXTRA_ERROR = "error"
        const val EXTRA_IS_PROFILE_OWNER = "is_profile_owner"
        
        private val uriMatcher = UriMatcher(UriMatcher.NO_MATCH).apply {
            addURI(AUTHORITY, "status", CODE_STATUS)
            addURI(AUTHORITY, "install/*", CODE_INSTALL)
        }
    }
    
    private lateinit var devicePolicyManager: DevicePolicyManager
    private lateinit var adminComponent: ComponentName
    
    override fun onCreate(): Boolean {
        val ctx = context ?: return false
        devicePolicyManager = ctx.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        adminComponent = ComponentName(ctx, NevenDeviceAdminReceiver::class.java)
        
        Log.d(TAG, "SandboxContentProvider created")
        
        // Si somos Profile Owner, configurar acceso cross-profile
        if (devicePolicyManager.isProfileOwnerApp(ctx.packageName)) {
            setupCrossProfileAccess(ctx)
        }
        
        return true
    }
    
    /**
     * Configura el acceso cross-profile para este provider
     */
    private fun setupCrossProfileAccess(ctx: Context) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                // Permitir que nuestra app se comunique entre perfiles
                devicePolicyManager.setCrossProfilePackages(adminComponent, setOf(ctx.packageName))
                Log.d(TAG, "Cross-profile packages configured")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error setting up cross-profile access", e)
        }
    }
    
    /**
     * Query para obtener información del sandbox
     */
    override fun query(
        uri: Uri,
        projection: Array<out String>?,
        selection: String?,
        selectionArgs: Array<out String>?,
        sortOrder: String?
    ): Cursor? {
        val ctx = context ?: return null
        
        Log.d(TAG, "query: uri=$uri")
        
        return when (uriMatcher.match(uri)) {
            CODE_STATUS -> {
                // Retornar estado del sandbox
                val cursor = MatrixCursor(arrayOf("is_profile_owner", "package_name"))
                val isProfileOwner = devicePolicyManager.isProfileOwnerApp(ctx.packageName)
                cursor.addRow(arrayOf(if (isProfileOwner) 1 else 0, ctx.packageName))
                cursor
            }
            CODE_INSTALL -> {
                // Intentar instalar el paquete especificado en el URI
                val packageName = uri.lastPathSegment
                if (packageName != null) {
                    val success = installPackage(packageName)
                    val cursor = MatrixCursor(arrayOf("success", "package_name", "error"))
                    cursor.addRow(arrayOf(
                        if (success) 1 else 0,
                        packageName,
                        if (success) null else "Installation failed"
                    ))
                    cursor
                } else {
                    null
                }
            }
            else -> null
        }
    }
    
    /**
     * Call method para operaciones más complejas
     */
    override fun call(method: String, arg: String?, extras: Bundle?): Bundle? {
        val ctx = context ?: return null
        val result = Bundle()
        
        Log.d(TAG, "call: method=$method, arg=$arg")
        
        when (method) {
            METHOD_INSTALL -> {
                val packageName = arg ?: extras?.getString(EXTRA_PACKAGE_NAME)
                if (packageName != null) {
                    val success = installPackage(packageName)
                    result.putBoolean(EXTRA_SUCCESS, success)
                    if (!success) {
                        result.putString(EXTRA_ERROR, "Installation failed")
                    }
                    Log.d(TAG, "Install $packageName: success=$success")
                } else {
                    result.putBoolean(EXTRA_SUCCESS, false)
                    result.putString(EXTRA_ERROR, "No package name provided")
                }
            }
            METHOD_UNINSTALL -> {
                val packageName = arg ?: extras?.getString(EXTRA_PACKAGE_NAME)
                if (packageName != null) {
                    val success = uninstallPackage(packageName)
                    result.putBoolean(EXTRA_SUCCESS, success)
                    if (!success) {
                        result.putString(EXTRA_ERROR, "Uninstallation failed")
                    }
                } else {
                    result.putBoolean(EXTRA_SUCCESS, false)
                    result.putString(EXTRA_ERROR, "No package name provided")
                }
            }
            METHOD_GET_STATUS -> {
                result.putBoolean(EXTRA_IS_PROFILE_OWNER, 
                    devicePolicyManager.isProfileOwnerApp(ctx.packageName))
            }
        }
        
        return result
    }
    
    /**
     * Instala un paquete existente en el Work Profile
     */
    private fun installPackage(packageName: String): Boolean {
        val ctx = context ?: return false
        
        if (!devicePolicyManager.isProfileOwnerApp(ctx.packageName)) {
            Log.e(TAG, "Cannot install - not profile owner")
            return false
        }
        
        return try {
            Log.d(TAG, "Installing $packageName via DevicePolicyManager")
            val success = devicePolicyManager.installExistingPackage(adminComponent, packageName)
            Log.d(TAG, "installExistingPackage($packageName) = $success")
            success
        } catch (e: SecurityException) {
            Log.e(TAG, "SecurityException installing $packageName", e)
            false
        } catch (e: IllegalArgumentException) {
            Log.e(TAG, "Package $packageName not found in personal profile", e)
            false
        } catch (e: Exception) {
            Log.e(TAG, "Error installing $packageName", e)
            false
        }
    }
    
    /**
     * Desinstala un paquete del Work Profile
     */
    private fun uninstallPackage(packageName: String): Boolean {
        val ctx = context ?: return false
        
        if (!devicePolicyManager.isProfileOwnerApp(ctx.packageName)) {
            Log.e(TAG, "Cannot uninstall - not profile owner")
            return false
        }
        
        return try {
            // setApplicationHidden efectivamente "desinstala" la app del perfil
            devicePolicyManager.setApplicationHidden(adminComponent, packageName, true)
            Log.d(TAG, "Hidden (uninstalled) $packageName")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Error uninstalling $packageName", e)
            false
        }
    }
    
    // Required overrides
    override fun getType(uri: Uri): String? = null
    override fun insert(uri: Uri, values: ContentValues?): Uri? = null
    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = 0
    override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = 0
}
