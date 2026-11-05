package com.neven.launcher.services

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Boot Receiver for NEVEN Launcher
 * 
 * Ensures the launcher is ready after device boot
 */
class BootReceiver : BroadcastReceiver() {
    
    override fun onReceive(context: Context?, intent: Intent?) {
        if (intent?.action == Intent.ACTION_BOOT_COMPLETED ||
            intent?.action == "android.intent.action.QUICKBOOT_POWERON") {
            // Launcher will be started by the system when user unlocks
            // We can use this to pre-load data if needed
        }
    }
}
