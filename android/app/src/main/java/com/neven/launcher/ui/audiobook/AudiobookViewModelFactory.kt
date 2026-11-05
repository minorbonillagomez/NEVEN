package com.neven.launcher.ui.audiobook

import android.app.Application
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.neven.launcher.data.audiobook.AudiobookDatabase
import com.neven.launcher.data.audiobook.AudiobookRepository

/**
 * Factory para crear AudiobookViewModel con las dependencias necesarias.
 */
class AudiobookViewModelFactory(
    private val application: Application
) : ViewModelProvider.Factory {
    
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(AudiobookViewModel::class.java)) {
            val database = AudiobookDatabase.getInstance(application)
            val repository = AudiobookRepository(application, database.audiobookDao())
            return AudiobookViewModel(application, repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}
