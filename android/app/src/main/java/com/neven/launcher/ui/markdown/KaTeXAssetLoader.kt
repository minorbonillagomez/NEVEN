package com.neven.launcher.ui.markdown

import android.content.Context
import android.util.Log

/**
 * Carga los archivos de KaTeX desde assets y los mantiene en cache
 */
object KaTeXAssetLoader {
    
    private const val TAG = "KaTeXAssetLoader"
    
    private var katexCss: String? = null
    private var katexJs: String? = null
    private var markedJs: String? = null
    private var autoRenderJs: String? = null
    
    /**
     * Carga todos los assets de KaTeX
     */
    fun loadAssets(context: Context) {
        if (katexCss != null) return // Ya cargado
        
        try {
            katexCss = loadAsset(context, "katex/katex.min.css")
            katexJs = loadAsset(context, "katex/katex.min.js")
            markedJs = loadAsset(context, "katex/marked.min.js")
            autoRenderJs = loadAsset(context, "katex/auto-render.min.js")
            Log.d(TAG, "KaTeX assets loaded successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Error loading KaTeX assets", e)
        }
    }
    
    private fun loadAsset(context: Context, path: String): String {
        return context.assets.open(path).bufferedReader().use { it.readText() }
    }
    
    fun getKatexCss(): String = katexCss ?: ""
    fun getKatexJs(): String = katexJs ?: ""
    fun getMarkedJs(): String = markedJs ?: ""
    fun getAutoRenderJs(): String = autoRenderJs ?: ""
    
    fun isLoaded(): Boolean = katexCss != null
}
