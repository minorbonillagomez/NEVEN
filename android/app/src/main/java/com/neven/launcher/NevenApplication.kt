package com.neven.launcher

import android.app.Application

/**
 * NEVEN Launcher Application
 * 
 * A scientific, minimalist launcher with LaTeX typography
 * inspired by academic papers and Scandinavian design.
 */
class NevenApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        instance = this
    }
    
    companion object {
        lateinit var instance: NevenApplication
            private set
    }
}
