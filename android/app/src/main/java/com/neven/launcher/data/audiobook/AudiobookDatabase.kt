package com.neven.launcher.data.audiobook

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * Base de datos Room para audiolibros NEVEN
 * 
 * Almacena biblioteca, capitulos, notas y configuracion
 */
@Database(
    entities = [
        Audiobook::class,
        AudiobookChapter::class,
        AudiobookNote::class,
        AudiobookSettings::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AudiobookDatabase : RoomDatabase() {
    
    abstract fun audiobookDao(): AudiobookDao
    
    companion object {
        @Volatile
        private var INSTANCE: AudiobookDatabase? = null
        
        fun getInstance(context: Context): AudiobookDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AudiobookDatabase::class.java,
                    "neven_audiobooks.db"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
