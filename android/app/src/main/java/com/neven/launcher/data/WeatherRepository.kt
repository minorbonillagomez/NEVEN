package com.neven.launcher.data

import android.content.Context
import android.location.Geocoder
import android.location.Location
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.doublePreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale

/**
 * Repositorio para datos del clima usando Open-Meteo API (gratuita, sin API key)
 * 
 * API: https://open-meteo.com/
 */

private val Context.weatherDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "weather_preferences"
)

class WeatherRepository(private val context: Context) {
    
    companion object {
        private val CACHED_TEMP = doublePreferencesKey("cached_temp")
        private val CACHED_CONDITION = stringPreferencesKey("cached_condition")
        private val CACHED_LOCATION = stringPreferencesKey("cached_location")
        private val CACHED_WEATHER_CODE = stringPreferencesKey("cached_weather_code")
        private val CACHED_TIMESTAMP = longPreferencesKey("cached_timestamp")
        private val SAVED_LAT = doublePreferencesKey("saved_lat")
        private val SAVED_LON = doublePreferencesKey("saved_lon")
        
        // Datos de aventura
        private val CACHED_HUMIDITY = stringPreferencesKey("cached_humidity")
        private val CACHED_WIND_SPEED = doublePreferencesKey("cached_wind_speed")
        private val CACHED_FEELS_LIKE = doublePreferencesKey("cached_feels_like")
        private val CACHED_SUNRISE = stringPreferencesKey("cached_sunrise")
        private val CACHED_SUNSET = stringPreferencesKey("cached_sunset")
        private val CACHED_PRECIP_PROB = stringPreferencesKey("cached_precip_prob")
        private val CACHED_UV_INDEX = doublePreferencesKey("cached_uv_index")
        private val CACHED_ELEVATION = doublePreferencesKey("cached_elevation")
        
        // Cache válido por 30 minutos
        private const val CACHE_DURATION_MS = 30 * 60 * 1000L
    }
    
    /**
     * Obtiene el clima cacheado
     */
    val cachedWeather: Flow<WeatherData?> = context.weatherDataStore.data.map { prefs ->
        val timestamp = prefs[CACHED_TIMESTAMP] ?: 0L
        val temp = prefs[CACHED_TEMP]
        val condition = prefs[CACHED_CONDITION]
        val location = prefs[CACHED_LOCATION]
        val weatherCode = prefs[CACHED_WEATHER_CODE]
        
        if (temp != null && condition != null && location != null) {
            WeatherData(
                temperature = temp,
                condition = condition,
                locationName = location,
                weatherCode = weatherCode ?: "0",
                timestamp = timestamp,
                isStale = System.currentTimeMillis() - timestamp > CACHE_DURATION_MS,
                // Datos de aventura
                humidity = prefs[CACHED_HUMIDITY]?.toIntOrNull() ?: 0,
                windSpeed = prefs[CACHED_WIND_SPEED] ?: 0.0,
                feelsLike = prefs[CACHED_FEELS_LIKE] ?: temp,
                sunrise = prefs[CACHED_SUNRISE] ?: "",
                sunset = prefs[CACHED_SUNSET] ?: "",
                precipitationProbability = prefs[CACHED_PRECIP_PROB]?.toIntOrNull() ?: 0,
                uvIndex = prefs[CACHED_UV_INDEX] ?: 0.0,
                elevation = prefs[CACHED_ELEVATION] ?: 0.0
            )
        } else {
            null
        }
    }
    
    /**
     * Ubicación guardada
     */
    val savedLocation: Flow<Pair<Double, Double>?> = context.weatherDataStore.data.map { prefs ->
        val lat = prefs[SAVED_LAT]
        val lon = prefs[SAVED_LON]
        if (lat != null && lon != null) Pair(lat, lon) else null
    }
    
    /**
     * Guarda la ubicación del usuario
     */
    suspend fun saveLocation(lat: Double, lon: Double) {
        context.weatherDataStore.edit { prefs ->
            prefs[SAVED_LAT] = lat
            prefs[SAVED_LON] = lon
        }
    }
    
    /**
     * Obtiene el clima desde Open-Meteo API
     */
    suspend fun fetchWeather(latitude: Double, longitude: Double): Result<WeatherData> {
        return withContext(Dispatchers.IO) {
            try {
                // Construir URL de Open-Meteo API con datos adicionales para aventura
                val url = URL(
                    "https://api.open-meteo.com/v1/forecast?" +
                    "latitude=$latitude&longitude=$longitude" +
                    "&current=temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m,apparent_temperature" +
                    "&daily=sunrise,sunset,precipitation_probability_max,uv_index_max" +
                    "&timezone=auto" +
                    "&forecast_days=1"
                )
                
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "GET"
                connection.connectTimeout = 10000
                connection.readTimeout = 10000
                
                val responseCode = connection.responseCode
                if (responseCode == HttpURLConnection.HTTP_OK) {
                    val response = connection.inputStream.bufferedReader().readText()
                    val json = JSONObject(response)
                    
                    // Elevación del terreno (Open-Meteo la incluye en la respuesta)
                    val elevation = json.optDouble("elevation", 0.0)
                    
                    val current = json.getJSONObject("current")
                    val temperature = current.getDouble("temperature_2m")
                    val weatherCode = current.getInt("weather_code")
                    val humidity = current.optInt("relative_humidity_2m", 0)
                    val windSpeed = current.optDouble("wind_speed_10m", 0.0)
                    val feelsLike = current.optDouble("apparent_temperature", temperature)
                    
                    // Datos diarios para aventura
                    val daily = json.optJSONObject("daily")
                    val sunrise = daily?.optJSONArray("sunrise")?.optString(0) ?: ""
                    val sunset = daily?.optJSONArray("sunset")?.optString(0) ?: ""
                    val precipProb = daily?.optJSONArray("precipitation_probability_max")?.optInt(0) ?: 0
                    val uvIndex = daily?.optJSONArray("uv_index_max")?.optDouble(0) ?: 0.0
                    
                    // Obtener nombre de ubicación
                    val locationName = getLocationName(latitude, longitude)
                    
                    // Decodificar código de clima
                    val condition = decodeWeatherCode(weatherCode)
                    
                    val weatherData = WeatherData(
                        temperature = temperature,
                        condition = condition,
                        locationName = locationName,
                        weatherCode = weatherCode.toString(),
                        timestamp = System.currentTimeMillis(),
                        isStale = false,
                        // Datos adicionales para aventura
                        humidity = humidity,
                        windSpeed = windSpeed,
                        feelsLike = feelsLike,
                        sunrise = sunrise,
                        sunset = sunset,
                        precipitationProbability = precipProb,
                        uvIndex = uvIndex,
                        elevation = elevation
                    )
                    
                    // Guardar en cache
                    cacheWeather(weatherData)
                    
                    Result.success(weatherData)
                } else {
                    Result.failure(Exception("HTTP Error: $responseCode"))
                }
            } catch (e: Exception) {
                e.printStackTrace()
                Result.failure(e)
            }
        }
    }
    
    /**
     * Obtiene el nombre de la ubicación usando Geocoder
     */
    private fun getLocationName(lat: Double, lon: Double): String {
        return try {
            val geocoder = Geocoder(context, Locale.getDefault())
            @Suppress("DEPRECATION")
            val addresses = geocoder.getFromLocation(lat, lon, 1)
            if (!addresses.isNullOrEmpty()) {
                addresses[0].locality ?: addresses[0].subAdminArea ?: addresses[0].adminArea ?: "Ubicación"
            } else {
                "Ubicación"
            }
        } catch (e: Exception) {
            "Ubicación"
        }
    }
    
    /**
     * Guarda el clima en cache
     */
    private suspend fun cacheWeather(data: WeatherData) {
        context.weatherDataStore.edit { prefs ->
            prefs[CACHED_TEMP] = data.temperature
            prefs[CACHED_CONDITION] = data.condition
            prefs[CACHED_LOCATION] = data.locationName
            prefs[CACHED_WEATHER_CODE] = data.weatherCode
            prefs[CACHED_TIMESTAMP] = data.timestamp
            // Datos de aventura
            prefs[CACHED_HUMIDITY] = data.humidity.toString()
            prefs[CACHED_WIND_SPEED] = data.windSpeed
            prefs[CACHED_FEELS_LIKE] = data.feelsLike
            prefs[CACHED_SUNRISE] = data.sunrise
            prefs[CACHED_SUNSET] = data.sunset
            prefs[CACHED_PRECIP_PROB] = data.precipitationProbability.toString()
            prefs[CACHED_UV_INDEX] = data.uvIndex
            prefs[CACHED_ELEVATION] = data.elevation
        }
    }
    
    /**
     * Decodifica el código WMO a descripción legible
     * https://open-meteo.com/en/docs#weathervariables
     */
    private fun decodeWeatherCode(code: Int): String {
        return when (code) {
            0 -> "Despejado"
            1 -> "Mayormente despejado"
            2 -> "Parcialmente nublado"
            3 -> "Nublado"
            45, 48 -> "Neblina"
            51, 53, 55 -> "Llovizna"
            56, 57 -> "Llovizna helada"
            61, 63, 65 -> "Lluvia"
            66, 67 -> "Lluvia helada"
            71, 73, 75 -> "Nieve"
            77 -> "Granizo"
            80, 81, 82 -> "Chubascos"
            85, 86 -> "Nieve intensa"
            95 -> "Tormenta"
            96, 99 -> "Tormenta con granizo"
            else -> "Desconocido"
        }
    }
}

/**
 * Modelo de datos del clima
 */
data class WeatherData(
    val temperature: Double,
    val condition: String,
    val locationName: String,
    val weatherCode: String,
    val timestamp: Long,
    val isStale: Boolean = false,
    // Datos adicionales para modo aventura
    val humidity: Int = 0,
    val windSpeed: Double = 0.0,
    val feelsLike: Double = temperature,
    val sunrise: String = "",
    val sunset: String = "",
    val precipitationProbability: Int = 0,
    val uvIndex: Double = 0.0,
    val elevation: Double = 0.0  // Elevación del terreno en metros
) {
    /**
     * Temperatura formateada
     */
    val temperatureFormatted: String
        get() = "${temperature.toInt()}°"
    
    /**
     * Sensación térmica formateada
     */
    val feelsLikeFormatted: String
        get() = "${feelsLike.toInt()}°"
    
    /**
     * Hora de amanecer formateada (HH:mm)
     */
    val sunriseFormatted: String
        get() = sunrise.takeLast(5) // "2024-01-01T06:30" -> "06:30"
    
    /**
     * Hora de anochecer formateada (HH:mm)
     */
    val sunsetFormatted: String
        get() = sunset.takeLast(5)
    
    /**
     * Velocidad del viento formateada
     */
    val windFormatted: String
        get() = "${windSpeed.toInt()} km/h"
    
    /**
     * Índice UV con descripción
     */
    val uvDescription: String
        get() = when {
            uvIndex < 3 -> "Bajo"
            uvIndex < 6 -> "Moderado"
            uvIndex < 8 -> "Alto"
            uvIndex < 11 -> "Muy alto"
            else -> "Extremo"
        }
    
    /**
     * Ícono del clima basado en código WMO
     */
    val weatherIcon: String
        get() = when (weatherCode.toIntOrNull() ?: 0) {
            0 -> "☀"           // Despejado
            1 -> "🌤"          // Mayormente despejado
            2 -> "⛅"          // Parcialmente nublado
            3 -> "☁"           // Nublado
            45, 48 -> "🌫"     // Neblina
            51, 53, 55 -> "🌧"  // Llovizna
            56, 57 -> "🌧"      // Llovizna helada
            61, 63, 65 -> "🌧"  // Lluvia
            66, 67 -> "🌧"      // Lluvia helada
            71, 73, 75 -> "❄"  // Nieve
            77 -> "🌨"          // Granizo
            80, 81, 82 -> "🌦"  // Chubascos
            85, 86 -> "❄"      // Nieve intensa
            95 -> "⛈"          // Tormenta
            96, 99 -> "⛈"      // Tormenta con granizo
            else -> "◌"        // Desconocido
        }
    
    /**
     * Símbolo científico del clima (alternativa minimalista)
     */
    val weatherSymbol: String
        get() = when (weatherCode.toIntOrNull() ?: 0) {
            0 -> "◉"           // Sol
            1, 2 -> "◐"        // Parcialmente
            3 -> "●"           // Nublado
            45, 48 -> "≋"      // Neblina
            51, 53, 55, 61, 63, 65 -> "∴"  // Lluvia
            71, 73, 75, 77, 85, 86 -> "✱"  // Nieve
            80, 81, 82 -> "∵"  // Chubascos
            95, 96, 99 -> "⚡"  // Tormenta
            else -> "◌"
        }
    
    /**
     * Indicador de condiciones para aventura
     */
    val adventureCondition: String
        get() = when {
            precipitationProbability > 70 -> "No recomendado"
            precipitationProbability > 40 -> "Precaución"
            uvIndex > 8 -> "Protección solar"
            windSpeed > 40 -> "Viento fuerte"
            temperature < 5 -> "Frío intenso"
            temperature > 35 -> "Calor extremo"
            else -> "Favorable"
        }
}
