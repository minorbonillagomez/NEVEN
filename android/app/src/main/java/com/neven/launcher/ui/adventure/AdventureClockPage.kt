package com.neven.launcher.ui.adventure

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.neven.launcher.data.WeatherRepository
import com.neven.launcher.ui.theme.NevenColors
import com.neven.launcher.ui.theme.NevenFontFamily
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*
import kotlin.math.roundToInt

/**
 * Página de Reloj Aventura
 * 
 * Diseño científico/minimalista con información para actividades al aire libre:
 * - Reloj grande
 * - Clima actual + probabilidad de lluvia
 * - Amanecer y anochecer
 * - Altitud (GPS/barométrico)
 * - Brújula
 */
@Composable
fun AdventureClockPage(
    colors: NevenColors,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    
    // Tiempo actual
    var calendar by remember { mutableStateOf(Calendar.getInstance()) }
    
    // Repositorio de clima
    val weatherRepo = remember { WeatherRepository(context) }
    val cachedWeather by weatherRepo.cachedWeather.collectAsState(initial = null)
    var isLoadingWeather by remember { mutableStateOf(false) }
    
    // Sensores
    var altitude by remember { mutableStateOf<Double?>(null) }
    var compassDegrees by remember { mutableStateOf(0f) }
    var hasCompass by remember { mutableStateOf(false) }
    
    // Permisos
    var hasLocationPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED
        )
    }
    
    val locationPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        hasLocationPermission = permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
                               permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true
    }
    
    // Actualizar reloj cada segundo
    LaunchedEffect(Unit) {
        while (true) {
            calendar = Calendar.getInstance()
            delay(1000L)
        }
    }
    
    // Inicializar sensores
    DisposableEffect(hasLocationPermission) {
        val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        
        // Brújula (acelerómetro + magnetómetro)
        val accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val magnetometer = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)
        
        hasCompass = accelerometer != null && magnetometer != null
        
        val gravity = FloatArray(3)
        val geomagnetic = FloatArray(3)
        
        val compassListener = object : SensorEventListener {
            override fun onSensorChanged(event: SensorEvent) {
                when (event.sensor.type) {
                    Sensor.TYPE_ACCELEROMETER -> {
                        System.arraycopy(event.values, 0, gravity, 0, 3)
                    }
                    Sensor.TYPE_MAGNETIC_FIELD -> {
                        System.arraycopy(event.values, 0, geomagnetic, 0, 3)
                    }
                }
                
                val rotationMatrix = FloatArray(9)
                val orientation = FloatArray(3)
                
                if (SensorManager.getRotationMatrix(rotationMatrix, null, gravity, geomagnetic)) {
                    SensorManager.getOrientation(rotationMatrix, orientation)
                    val azimuth = Math.toDegrees(orientation[0].toDouble()).toFloat()
                    compassDegrees = (azimuth + 360) % 360
                }
            }
            
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        
        accelerometer?.let {
            sensorManager.registerListener(compassListener, it, SensorManager.SENSOR_DELAY_UI)
        }
        magnetometer?.let {
            sensorManager.registerListener(compassListener, it, SensorManager.SENSOR_DELAY_UI)
        }
        
        // Altitud via múltiples fuentes
        var locationListenerRef: LocationListener? = null
        
        if (hasLocationPermission) {
            val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
            
            val locationListener = object : LocationListener {
                override fun onLocationChanged(location: Location) {
                    if (location.hasAltitude()) {
                        altitude = location.altitude
                    }
                }
                override fun onProviderEnabled(provider: String) {}
                override fun onProviderDisabled(provider: String) {}
                @Deprecated("Deprecated in Java")
                override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
            }
            locationListenerRef = locationListener
            
            try {
                // Intentar obtener última ubicación conocida de cualquier proveedor
                @Suppress("MissingPermission")
                val lastGps = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
                @Suppress("MissingPermission")
                val lastNetwork = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
                
                // Usar la ubicación más reciente que tenga altitud
                val bestLocation = listOfNotNull(lastGps, lastNetwork)
                    .filter { it.hasAltitude() }
                    .maxByOrNull { it.time }
                
                if (bestLocation != null) {
                    altitude = bestLocation.altitude
                }
                
                // Solicitar actualizaciones de GPS (más preciso para altitud)
                if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                    @Suppress("MissingPermission")
                    locationManager.requestLocationUpdates(
                        LocationManager.GPS_PROVIDER,
                        3000L,  // Cada 3 segundos
                        5f,     // O cada 5 metros
                        locationListener
                    )
                }
                
                // También solicitar de NETWORK como backup
                if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                    @Suppress("MissingPermission")
                    locationManager.requestLocationUpdates(
                        LocationManager.NETWORK_PROVIDER,
                        5000L,
                        10f,
                        locationListener
                    )
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
        
        onDispose {
            sensorManager.unregisterListener(compassListener)
            // Limpiar listener de ubicación
            if (hasLocationPermission && locationListenerRef != null) {
                try {
                    val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
                    locationManager.removeUpdates(locationListenerRef!!)
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
    }
    
    // Cargar clima
    LaunchedEffect(hasLocationPermission) {
        if (hasLocationPermission && (cachedWeather == null || cachedWeather?.isStale == true)) {
            isLoadingWeather = true
            try {
                val savedLocation = weatherRepo.savedLocation.first()
                if (savedLocation != null) {
                    weatherRepo.fetchWeather(savedLocation.first, savedLocation.second)
                } else {
                    val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
                    @Suppress("MissingPermission")
                    val location = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
                        ?: locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
                    
                    if (location != null) {
                        weatherRepo.saveLocation(location.latitude, location.longitude)
                        weatherRepo.fetchWeather(location.latitude, location.longitude)
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
            isLoadingWeather = false
        }
    }
    
    val hour = calendar.get(Calendar.HOUR_OF_DAY)
    val minute = calendar.get(Calendar.MINUTE)
    val second = calendar.get(Calendar.SECOND)
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 24.dp, vertical = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // ═══════════════════════════════════════════════════════════════
        // TÍTULO
        // ═══════════════════════════════════════════════════════════════
        Text(
            text = "AVENTURA",
            style = MaterialTheme.typography.labelMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Light,
                letterSpacing = 6.sp
            ),
            color = colors.textSecondary.copy(alpha = 0.6f)
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // ═══════════════════════════════════════════════════════════════
        // RELOJ GRANDE
        // ═══════════════════════════════════════════════════════════════
        Text(
            text = String.format("%02d:%02d", hour, minute),
            style = MaterialTheme.typography.displayLarge.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 72.sp
            ),
            color = colors.hourColor
        )
        
        Text(
            text = String.format(":%02d", second),
            style = MaterialTheme.typography.headlineMedium.copy(
                fontFamily = NevenFontFamily,
                fontWeight = FontWeight.Light
            ),
            color = colors.secondColor
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Fecha
        val dateFormat = SimpleDateFormat("EEEE, d MMMM", Locale.getDefault())
        Text(
            text = dateFormat.format(calendar.time).replaceFirstChar { it.uppercase() },
            style = MaterialTheme.typography.bodyLarge.copy(
                fontFamily = NevenFontFamily
            ),
            color = colors.textPrimary
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        // ═══════════════════════════════════════════════════════════════
        // BRÚJULA Y ALTITUD (lado a lado)
        // ═══════════════════════════════════════════════════════════════
        if (!hasLocationPermission) {
            // Solicitar permiso
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        locationPermissionLauncher.launch(
                            arrayOf(
                                Manifest.permission.ACCESS_FINE_LOCATION,
                                Manifest.permission.ACCESS_COARSE_LOCATION
                            )
                        )
                    }
                    .padding(vertical = 16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "⊘",
                    fontSize = 32.sp,
                    color = colors.textSecondary.copy(alpha = 0.5f)
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Toca para permitir ubicación",
                    style = MaterialTheme.typography.bodyMedium.copy(
                        fontFamily = NevenFontFamily
                    ),
                    color = colors.accent
                )
            }
        } else {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Brújula
                if (hasCompass) {
                    CompassWidget(
                        degrees = compassDegrees,
                        colors = colors,
                        modifier = Modifier.size(120.dp)
                    )
                }
                
                // Altitud (GPS o elevación del terreno como fallback)
                val displayAltitude = altitude ?: cachedWeather?.elevation?.takeIf { it > 0 }
                
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "ALTITUD",
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontFamily = NevenFontFamily,
                            letterSpacing = 2.sp
                        ),
                        color = colors.textSecondary
                    )
                    
                    Spacer(modifier = Modifier.height(4.dp))
                    
                    Text(
                        text = displayAltitude?.let { "${it.roundToInt()} m" } ?: "Obteniendo...",
                        style = MaterialTheme.typography.headlineMedium.copy(
                            fontFamily = NevenFontFamily,
                            fontWeight = FontWeight.Light
                        ),
                        color = if (displayAltitude != null) colors.textPrimary else colors.textSecondary.copy(alpha = 0.6f)
                    )
                    
                    Text(
                        text = when {
                            altitude != null -> "GPS"
                            cachedWeather?.elevation != null && cachedWeather!!.elevation > 0 -> "elevación del terreno"
                            else -> "esperando ubicación"
                        },
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontFamily = NevenFontFamily,
                            fontStyle = FontStyle.Italic
                        ),
                        color = colors.textSecondary.copy(alpha = 0.6f)
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        // ═══════════════════════════════════════════════════════════════
        // SENTINEL STORM - ESTACIÓN BAROMÉTRICA
        // ═══════════════════════════════════════════════════════════════
        SentinelStormWidget(
            colors = colors,
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Separador
        Text(
            text = "↫ ⋇ ↬",
            style = MaterialTheme.typography.bodySmall,
            color = colors.textSecondary.copy(alpha = 0.3f),
            letterSpacing = 8.sp
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // ═══════════════════════════════════════════════════════════════
        // DATOS METEOROLÓGICOS
        // ═══════════════════════════════════════════════════════════════
        if (cachedWeather != null) {
            val weather = cachedWeather!!
            
            // Ubicación
            Text(
                text = weather.locationName.uppercase(),
                style = MaterialTheme.typography.labelMedium.copy(
                    fontFamily = NevenFontFamily,
                    letterSpacing = 3.sp
                ),
                color = colors.textSecondary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Temperatura y condición
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center
            ) {
                Text(
                    text = weather.temperatureFormatted,
                    style = MaterialTheme.typography.displaySmall.copy(
                        fontFamily = NevenFontFamily,
                        fontWeight = FontWeight.Light
                    ),
                    color = colors.textPrimary
                )
                
                Spacer(modifier = Modifier.width(16.dp))
                
                Column {
                    Text(
                        text = weather.condition,
                        style = MaterialTheme.typography.bodyLarge.copy(
                            fontFamily = NevenFontFamily
                        ),
                        color = colors.textPrimary
                    )
                    Text(
                        text = "Sensación ${weather.feelsLikeFormatted}",
                        style = MaterialTheme.typography.bodySmall.copy(
                            fontFamily = NevenFontFamily,
                            fontStyle = FontStyle.Italic
                        ),
                        color = colors.textSecondary
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Grid de datos
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                // Probabilidad de lluvia
                AdventureDataItem(
                    label = "LLUVIA",
                    value = "${weather.precipitationProbability}%",
                    colors = colors
                )
                
                // Viento
                AdventureDataItem(
                    label = "VIENTO",
                    value = weather.windFormatted,
                    colors = colors
                )
                
                // Humedad
                AdventureDataItem(
                    label = "HUMEDAD",
                    value = "${weather.humidity}%",
                    colors = colors
                )
            }
            
            Spacer(modifier = Modifier.height(20.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                // Amanecer
                AdventureDataItem(
                    label = "AMANECER",
                    value = weather.sunriseFormatted.ifEmpty { "--:--" },
                    symbol = "↑",
                    colors = colors
                )
                
                // Anochecer
                AdventureDataItem(
                    label = "ANOCHECER",
                    value = weather.sunsetFormatted.ifEmpty { "--:--" },
                    symbol = "↓",
                    colors = colors
                )
                
                // UV
                AdventureDataItem(
                    label = "UV",
                    value = weather.uvIndex.roundToInt().toString(),
                    subtitle = weather.uvDescription,
                    colors = colors
                )
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Condición para aventura
            val conditionColor = when (weather.adventureCondition) {
                "Favorable" -> colors.accent
                "Precaución", "Protección solar" -> colors.hourColor
                else -> colors.textSecondary
            }
            
            Text(
                text = "Condiciones: ${weather.adventureCondition}",
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium
                ),
                color = conditionColor
            )
            
        } else if (isLoadingWeather) {
            Text(
                text = "Obteniendo datos meteorológicos...",
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic
                ),
                color = colors.textSecondary
            )
        }
        
        Spacer(modifier = Modifier.height(32.dp))
    }
}

/**
 * Widget de brújula minimalista
 */
@Composable
private fun CompassWidget(
    degrees: Float,
    colors: NevenColors,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center
    ) {
        // Círculo exterior
        Canvas(modifier = Modifier.fillMaxSize()) {
            val radius = size.minDimension / 2 - 4.dp.toPx()
            
            // Círculo
            drawCircle(
                color = colors.textSecondary.copy(alpha = 0.2f),
                radius = radius,
                style = Stroke(width = 2.dp.toPx())
            )
            
            // Marcas cardinales
            val cardinalRadius = radius + 2.dp.toPx()
            listOf(0f, 90f, 180f, 270f).forEach { angle ->
                val rad = Math.toRadians(angle.toDouble() - 90)
                val innerR = radius - 8.dp.toPx()
                drawLine(
                    color = colors.textSecondary.copy(alpha = 0.5f),
                    start = Offset(
                        center.x + (innerR * kotlin.math.cos(rad)).toFloat(),
                        center.y + (innerR * kotlin.math.sin(rad)).toFloat()
                    ),
                    end = Offset(
                        center.x + (radius * kotlin.math.cos(rad)).toFloat(),
                        center.y + (radius * kotlin.math.sin(rad)).toFloat()
                    ),
                    strokeWidth = 2.dp.toPx()
                )
            }
        }
        
        // Aguja (rota según grados)
        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .rotate(-degrees)
        ) {
            val needleLength = size.minDimension / 2 - 20.dp.toPx()
            
            // Norte (rojo/accent)
            drawLine(
                color = colors.accent,
                start = center,
                end = Offset(center.x, center.y - needleLength),
                strokeWidth = 3.dp.toPx()
            )
            
            // Sur
            drawLine(
                color = colors.textSecondary,
                start = center,
                end = Offset(center.x, center.y + needleLength * 0.6f),
                strokeWidth = 2.dp.toPx()
            )
            
            // Centro
            drawCircle(
                color = colors.textPrimary,
                radius = 4.dp.toPx(),
                center = center
            )
        }
        
        // Letras cardinales
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.SpaceBetween,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "N",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Bold
                ),
                color = colors.accent,
                modifier = Modifier.padding(top = 2.dp)
            )
            Spacer(modifier = Modifier.weight(1f))
            Text(
                text = "S",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily
                ),
                color = colors.textSecondary,
                modifier = Modifier.padding(bottom = 2.dp)
            )
        }
        
        Row(
            modifier = Modifier.fillMaxSize(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "O",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily
                ),
                color = colors.textSecondary,
                modifier = Modifier.padding(start = 2.dp)
            )
            Spacer(modifier = Modifier.weight(1f))
            Text(
                text = "E",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily
                ),
                color = colors.textSecondary,
                modifier = Modifier.padding(end = 2.dp)
            )
        }
        
        // Grados actuales
        Text(
            text = "${degrees.roundToInt()}°",
            style = MaterialTheme.typography.labelSmall.copy(
                fontFamily = NevenFontFamily
            ),
            color = colors.textSecondary.copy(alpha = 0.7f),
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 24.dp)
        )
    }
}

/**
 * Item de datos para aventura
 */
@Composable
private fun AdventureDataItem(
    label: String,
    value: String,
    colors: NevenColors,
    symbol: String? = null,
    subtitle: String? = null
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall.copy(
                fontFamily = NevenFontFamily,
                letterSpacing = 1.sp
            ),
            color = colors.textSecondary.copy(alpha = 0.7f)
        )
        
        Spacer(modifier = Modifier.height(4.dp))
        
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            symbol?.let {
                Text(
                    text = it,
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.accent
                )
                Spacer(modifier = Modifier.width(4.dp))
            }
            
            Text(
                text = value,
                style = MaterialTheme.typography.titleMedium.copy(
                    fontFamily = NevenFontFamily,
                    fontWeight = FontWeight.Medium
                ),
                color = colors.textPrimary
            )
        }
        
        subtitle?.let {
            Text(
                text = it,
                style = MaterialTheme.typography.labelSmall.copy(
                    fontFamily = NevenFontFamily,
                    fontStyle = FontStyle.Italic
                ),
                color = colors.textSecondary.copy(alpha = 0.6f)
            )
        }
    }
}
