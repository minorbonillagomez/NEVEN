package com.neven.launcher.ui.components

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.BaselineShift
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.neven.launcher.data.WeatherRepository
import com.neven.launcher.latex.DateFormatter
import com.neven.launcher.latex.NumberToWords
import com.neven.launcher.ui.theme.ClockTypography
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.util.*

/**
 * NEVEN Scientific Clock
 * 
 * Displays time in scientific notation: HH^mm_ss
 * With academic paper hierarchy for date and year
 * Now includes weather below the year in a minimalist format
 * 
 * Visual hierarchy (like Elsevier/IEEE papers):
 * - TITLE: Hour (large, bold, colored)
 * - SUBTITLE: Date (medium, regular)
 * - AUTHOR: Year in words (small, spaced)
 * - FOOTER: Weather (minimal, subtle)
 * 
 * All elements share the same width forming a rectangular block.
 */
@Composable
fun ScientificClock(
    modifier: Modifier = Modifier,
    colors: NevenColors,
    locale: Locale = Locale.getDefault(),
    showSeconds: Boolean = true
) {
    var calendar by remember { mutableStateOf(Calendar.getInstance()) }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    
    // Weather repository
    val weatherRepo = remember { WeatherRepository(context) }
    val cachedWeather by weatherRepo.cachedWeather.collectAsState(initial = null)
    
    // Verificar permiso de ubicación
    val hasLocationPermission = remember {
        ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    // Update every second
    LaunchedEffect(Unit) {
        while (true) {
            calendar = Calendar.getInstance()
            delay(1000L)
        }
    }
    
    // Cargar clima si tenemos permiso y el cache está vacío o obsoleto
    LaunchedEffect(hasLocationPermission) {
        if (hasLocationPermission && (cachedWeather == null || cachedWeather?.isStale == true)) {
            fetchWeatherSilently(context, weatherRepo)
        }
    }
    
    val hour = calendar.get(Calendar.HOUR_OF_DAY)
    val minute = calendar.get(Calendar.MINUTE)
    val second = calendar.get(Calendar.SECOND)
    
    // Usar IntrinsicSize.Max para que todos los elementos tengan el mismo ancho
    Column(
        modifier = modifier
            .padding(horizontal = 24.dp)
            .width(IntrinsicSize.Max),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // ═══════════════════════════════════════════════════════════════
        // TIME: Scientific notation HH^mm_ss (más grande)
        // ═══════════════════════════════════════════════════════════════
        Box(
            modifier = Modifier.fillMaxWidth(),
            contentAlignment = Alignment.Center
        ) {
            ScientificTime(
                hour = hour,
                minute = minute,
                second = second,
                hourColor = colors.hourColor,
                minuteColor = colors.minuteColor,
                secondColor = colors.secondColor,
                showSeconds = showSeconds
            )
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        // ═══════════════════════════════════════════════════════════════
        // DATE: Más pequeño para equilibrar
        // ═══════════════════════════════════════════════════════════════
        Text(
            text = DateFormatter.getFormattedDate(calendar, locale),
            fontSize = 18.sp,
            fontWeight = FontWeight.Normal,
            fontFamily = NevenFontFamily,
            color = colors.textPrimary,
            textAlign = TextAlign.Center,
            letterSpacing = 1.sp,
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(6.dp))
        
        // ═══════════════════════════════════════════════════════════════
        // YEAR: Sin itálica, con más espaciado entre letras
        // ═══════════════════════════════════════════════════════════════
        val yearColor = remember(colors.hourColor, colors.isDark) {
            val factor = if (colors.isDark) 0.65f else 0.75f
            Color(
                red = colors.hourColor.red * factor,
                green = colors.hourColor.green * factor,
                blue = colors.hourColor.blue * factor,
                alpha = colors.hourColor.alpha
            )
        }
        
        Text(
            text = DateFormatter.getYearInWords(calendar, locale).uppercase(),
            fontSize = 12.sp,
            fontWeight = FontWeight.Normal,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Normal,
            color = yearColor,
            textAlign = TextAlign.Center,
            letterSpacing = 4.sp,
            modifier = Modifier.fillMaxWidth()
        )
        
        // ═══════════════════════════════════════════════════════════════
        // WEATHER: Minimalista, solo temperatura y condición
        // ═══════════════════════════════════════════════════════════════
        if (cachedWeather != null) {
            val weather = cachedWeather!!
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = "${weather.temperatureFormatted} · ${weather.condition}",
                fontSize = 11.sp,
                fontWeight = FontWeight.Normal,
                fontFamily = NevenFontFamily,
                fontStyle = FontStyle.Italic,
                color = colors.textSecondary.copy(alpha = 0.6f),
                textAlign = TextAlign.Center,
                letterSpacing = 1.sp,
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        // Actualizar clima al tocar
                        scope.launch {
                            fetchWeatherSilently(context, weatherRepo)
                        }
                    }
            )
        }
    }
}

/**
 * Obtiene el clima silenciosamente (sin mostrar errores)
 */
private suspend fun fetchWeatherSilently(
    context: Context,
    weatherRepo: WeatherRepository
) {
    try {
        val savedLocation = weatherRepo.savedLocation.first()
        
        if (savedLocation != null) {
            weatherRepo.fetchWeather(savedLocation.first, savedLocation.second)
        } else {
            val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as? android.location.LocationManager
            
            @Suppress("MissingPermission")
            val location = locationManager?.getLastKnownLocation(android.location.LocationManager.NETWORK_PROVIDER)
                ?: locationManager?.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER)
            
            if (location != null) {
                weatherRepo.saveLocation(location.latitude, location.longitude)
                weatherRepo.fetchWeather(location.latitude, location.longitude)
            }
        }
    } catch (e: Exception) {
        // Silenciosamente ignorar errores
    }
}

/**
 * Renders time in scientific notation with Minutes (superscript) and Seconds (subscript)
 * stacked in the same vertical column to the right of the Hour.
 * 
 * Layout:
 *    mm  (Minutes - Top)
 * HH
 *    ss  (Seconds - Bottom)
 */
@Composable
fun ScientificTime(
    hour: Int,
    minute: Int,
    second: Int,
    hourColor: Color,
    minuteColor: Color,
    secondColor: Color,
    showSeconds: Boolean = true
) {
    val hourString = String.format("%02d", hour)
    val minuteString = String.format("%02d", minute)
    val secondString = String.format("%02d", second)
    
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center
    ) {
        // Hour (HH) - Más grande
        Text(
            text = hourString,
            color = hourColor,
            fontSize = 84.sp,  // Incrementado de 72sp
            fontWeight = FontWeight.Bold,
            fontFamily = NevenFontFamily,
            lineHeight = 84.sp
        )
        
        Spacer(modifier = Modifier.width(4.dp))
        
        // Stacked Minutes and Seconds in the same vertical column
        Column(
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.Start
        ) {
            // Minutes (Superscript - Top)
            Text(
                text = minuteString,
                color = minuteColor,
                fontSize = 36.sp,  // Incrementado proporcionalmente
                fontWeight = FontWeight.Medium,
                fontFamily = NevenFontFamily,
                lineHeight = 36.sp
            )
            
            // Seconds (Subscript - Bottom)
            if (showSeconds) {
                Text(
                    text = secondString,
                    color = secondColor,
                    fontSize = 32.sp,  // Incrementado proporcionalmente
                    fontWeight = FontWeight.Normal,
                    fontFamily = NevenFontFamily,
                    lineHeight = 32.sp
                )
            }
        }
    }
}

/**
 * Preview helper - simulates clock at specific time
 */
@Composable
fun ScientificClockPreview(
    hour: Int = 14,
    minute: Int = 30,
    second: Int = 45,
    colors: NevenColors,
    locale: Locale = Locale("es")
) {
    val calendar = Calendar.getInstance().apply {
        set(Calendar.HOUR_OF_DAY, hour)
        set(Calendar.MINUTE, minute)
        set(Calendar.SECOND, second)
    }
    
    Column(
        modifier = Modifier
            .padding(horizontal = 24.dp)
            .width(IntrinsicSize.Max),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier.fillMaxWidth(),
            contentAlignment = Alignment.Center
        ) {
            ScientificTime(
                hour = hour,
                minute = minute,
                second = second,
                hourColor = colors.hourColor,
                minuteColor = colors.minuteColor,
                secondColor = colors.secondColor,
                showSeconds = true
            )
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Text(
            text = DateFormatter.getFormattedDate(calendar, locale),
            fontSize = 18.sp,
            fontWeight = FontWeight.Normal,
            fontFamily = NevenFontFamily,
            color = colors.textPrimary,
            textAlign = TextAlign.Center,
            letterSpacing = 1.sp,
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(6.dp))
        
        val yearColor = remember(colors.hourColor, colors.isDark) {
            val factor = if (colors.isDark) 0.65f else 0.75f
            Color(
                red = colors.hourColor.red * factor,
                green = colors.hourColor.green * factor,
                blue = colors.hourColor.blue * factor,
                alpha = colors.hourColor.alpha
            )
        }
        
        Text(
            text = DateFormatter.getYearInWords(calendar, locale).uppercase(),
            fontSize = 12.sp,
            fontWeight = FontWeight.Normal,
            fontFamily = NevenFontFamily,
            fontStyle = FontStyle.Normal,
            color = yearColor,
            textAlign = TextAlign.Center,
            letterSpacing = 4.sp,
            modifier = Modifier.fillMaxWidth()
        )
    }
}
