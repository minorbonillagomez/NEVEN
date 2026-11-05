package com.neven.launcher.util

import android.app.WallpaperManager
import android.content.Context
import android.net.Uri
import android.os.Build

/**
 * Utilidad para establecer wallpapers en el sistema.
 * Permite sincronizar el fondo del launcher con la pantalla de bloqueo.
 */
object WallpaperHelper {
    
    /**
     * Establece el wallpaper de la pantalla de bloqueo
     * @param context Contexto de Android
     * @param imageUri URI de la imagen
     * @return true si tuvo éxito, false si falló
     */
    fun setLockScreenWallpaper(context: Context, imageUri: Uri): Boolean {
        return try {
            val wallpaperManager = WallpaperManager.getInstance(context)
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                // Android 7.0+ permite establecer wallpaper de lock screen separado
                context.contentResolver.openInputStream(imageUri)?.use { inputStream ->
                    wallpaperManager.setStream(
                        inputStream,
                        null,
                        true,
                        WallpaperManager.FLAG_LOCK
                    )
                }
                true
            } else {
                // Android < 7.0 no soporta wallpaper de lock screen separado
                false
            }
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
    
    /**
     * Establece el wallpaper del home screen del sistema
     * @param context Contexto de Android
     * @param imageUri URI de la imagen
     * @return true si tuvo éxito, false si falló
     */
    fun setHomeWallpaper(context: Context, imageUri: Uri): Boolean {
        return try {
            val wallpaperManager = WallpaperManager.getInstance(context)
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                context.contentResolver.openInputStream(imageUri)?.use { inputStream ->
                    wallpaperManager.setStream(
                        inputStream,
                        null,
                        true,
                        WallpaperManager.FLAG_SYSTEM
                    )
                }
                true
            } else {
                context.contentResolver.openInputStream(imageUri)?.use { inputStream ->
                    wallpaperManager.setStream(inputStream)
                }
                true
            }
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
    
    /**
     * Establece el mismo wallpaper en home y lock screen
     * @param context Contexto de Android
     * @param imageUri URI de la imagen
     * @return true si ambos tuvieron éxito, false si alguno falló
     */
    fun setBothWallpapers(context: Context, imageUri: Uri): Boolean {
        val homeResult = setHomeWallpaper(context, imageUri)
        val lockResult = setLockScreenWallpaper(context, imageUri)
        return homeResult && lockResult
    }
    
    /**
     * Verifica si el dispositivo soporta wallpaper de lock screen separado
     * @return true si soporta (Android 7.0+), false si no
     */
    fun supportsLockScreenWallpaper(): Boolean {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.N
    }
}
