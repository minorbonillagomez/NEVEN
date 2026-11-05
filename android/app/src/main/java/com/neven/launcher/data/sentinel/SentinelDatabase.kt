package com.neven.launcher.data.sentinel

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * Base de datos Room para Sentinel Storm
 * 
 * Almacena historial de lecturas de presión barométrica
 * con auto-purgado cada 48 horas
 */
@Database(
    entities = [PressureReading::class],
    version = 1,
    exportSchema = false
)
abstract class SentinelDatabase : RoomDatabase() {
    
    abstract fun pressureReadingDao(): PressureReadingDao
    
    companion object {
        @Volatile
        private var INSTANCE: SentinelDatabase? = null
        
        fun getInstance(context: Context): SentinelDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    SentinelDatabase::class.java,
                    "sentinel_storm.db"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
