# Documento de Especificación de Requerimientos de Software (SRS)

**Proyecto:** Nevem Launcher Suite  
**Módulos Incluidos:**  
1. *Módulo UI/UX:* Motor de Transición 3D "Paso de Página Realista con Sombreado Dinámico"  
2. *Módulo Táctico:* "Sentinel Storm" — Estación Micro-Meteorológica Barométrica Offline con Auditoría de IA On-Device  
**Target:** Android Studio (Kotlin), Android 14+ (API 34+), arquitectura optimizada para Google Pixel y dispositivos de alto rendimiento.  

---

## PARTE 1: Módulo de Transición Visual — "Realistic Book Page Curl"

### 1.1 Objetivo
Implementar en el launcher Nevem una transición de cambio de pantalla fluida a 60/120 Hz que simule el arqueo y pliegue de una hoja de libro físico, integrando profundidad de cámara, rotación en el eje $Y$ y sombreado direccional físico.

### 1.2 Requerimientos Técnicos

#### RF-TR01: Transformación Geométrica 3D
* **Bisagra de Pivote Dinámica:**
  * Página saliente (desplazamiento a la izquierda, $p \in [-1.0, 0.0]$): Anclar `pivotX = width`, `pivotY = height * 0.5f`.
  * Página entrante (desplazamiento desde la derecha, $p \in [0.0, 1.0]$): Anclar `pivotX = 0f`, `pivotY = height * 0.5f`.
* **Compensación de Traslación:** Debe anularse el desplazamiento horizontal nativo mediante:
  $$\text{translationX} = -\text{width} \cdot p$$
  garantizando que la página gire rígidamente sobre el lomo virtual en lugar de deslizarse como una tarjeta plana.
* **Perspectiva de Cámara:** Calibrar `cameraDistance = width * 14f` para evitar aberraciones ópticas en widgets e iconos en ángulos próximos a los $90^\circ$.

#### RF-TR02: Renderizado de Sombreado Dinámico
* **Sombra de Pliegue (Página Saliente):** Proyectar un gradiente lineal horizontal oscuro en el cuadrante derecho ($x \in [0.4 \cdot \text{width}, \text{width}]$) proporcional al ángulo de giro:
  $$\alpha_{\text{fold}} = |p| \cdot 0.75$$
* **Sombra Proyectada (Página Subyacente):** Proyectar un degradado suave sobre el borde izquierdo de la página que queda al fondo para simular la sombra arrojada por la hoja superior:
  $$\alpha_{\text{cast}} = (1.0 - |p|) \cdot 0.50$$
* **Rendimiento:** El cómputo del degradado debe ejecutarse directamente en la GPU (usando `drawWithContent` con `Brush.horizontalGradient` en Compose o `ColorDrawable`/shaders en ViewPager2) con cero asignaciones de memoria en el ciclo de dibujo.

---

## PARTE 2: Módulo Táctico — "Sentinel Storm" (Barómetro Offline + IA On-Device)

### 2.1 Visión General
Sistema autónomo de detección de frentes climáticos adversos para expedición y montaña sin conexión celular ni consumo de APIs remotas. Resuelve el desacoplamiento entre el cambio de altitud topográfico y la caída barométrica meteorológica mediante una máquina de estados cinemática (FSM) y audita las anomalías críticas con el modelo de IA on-device (Gemini Nano / LiteRT).

### 2.2 Arquitectura del Sistema

```
                      +-----------------------------+
                      | Hardware: Sensor Hub & GNSS |
                      +-----------------------------+
                                     │
                 Muestreo cada 5 min │ (WakeLock parcial <= 3s)
                                     ▼
        +─────────────────────────────────────────────────────────+
        |        Máquina de Estados Cinemática (FSM)              |
        |  - ¿Movimiento activo? (Pasos / RMS Aceleración)        |
        |    -> MODO EN MARCHA: Corrige cota h vía GNSS L5        |
        |    -> MODO ESTACIONARIO: Congela h; GNSS al 100% OFF    |
        +─────────────────────────────────────────────────────────+
                                     │
                                     ▼
        +─────────────────────────────────────────────────────────+
        |             Normalización Hipsométrica                  |
        |    P0 = P * (1 - (0.0065 * h) / 288.15) ^ -5.255        |
        |    Persistencia en SQLite / Room (búfer móvil 24h)      |
        +─────────────────────────────────────────────────────────+
                                     │
                     ¿dP0/dt excede umbral crítico?
                                     │
                                     ├─ NO ──> Retorno a Deep Sleep
                                     ▼ SÍ
        +─────────────────────────────────────────────────────────+
        |            Capa de Inferencia: IA On-Device             |
        |  1. Audita consistencia física (detecta falsos rebotes)  |
        |  2. Genera diagnóstico y recomendaciones tácticas       |
        +─────────────────────────────────────────────────────────+
                                     │
                                     ▼
        +─────────────────────────────────────────────────────────+
        |         Notificación Local y Alarma Sonora              |
        +─────────────────────────────────────────────────────────+
```

### 2.3 Requerimientos Funcionales

#### RF-SS01: Ingesta de Sensores de Bajo Consumo
* **Presión:** Ráfaga de 5 lecturas de `Sensor.TYPE_PRESSURE` promediadas mediante media truncada (descartando el máximo y mínimo) para eliminar ruido electromagnético.
* **Inercia:** Monitoreo del contador de pasos por hardware (`Sensor.TYPE_STEP_COUNTER`) y aceleración triaxial RMS.
* **Geolocalización:** Activación puntual de `FusedLocationProviderClient` con modo de máxima exactitud (L1+L5) únicamente durante transiciones de estado requeridas.

#### RF-SS02: Máquina de Estados Finitos (FSM)
1. **Modo Estacionario (Campamento / Vivac):**
   * *Entrada:* Inmovilidad sostenida durante $\ge 600\text{ s}$ ($\text{cadencia} = 0$).
   * *Acción:* Apaga el módem GNSS por completo ($0 \text{ mA}$). Fija la altitud en $h_{\text{fija}}$.
   * *Cómputo:* El $100\%$ de la variación de $\Delta P$ se adjudica a variación atmosférica directa.
2. **Modo En Marcha (Trekking / Desplazamiento):**
   * *Entrada:* $\ge 40$ pasos acumulados en 120 s o varianza de aceleración $> 0.15 \text{ m/s}^2$.
   * *Acción:* Activa un pulso GNSS de máximo 3 segundos cada 10 minutos para recalcular la altitud real $h$.
   * *Cómputo:* Resuelve $P_0$ descontando la ganancia o pérdida métrica del terreno.

#### RF-SS03: Formulación Matemática de Normalización
Toda lectura de presión bruta $P$ en pascales o hectopascales debe convertirse a presión normalizada a nivel del mar ($P_0$):

$$P_0 = P \cdot \left(1 - \frac{0.0065 \cdot h}{288.15}\right)^{-5.25588}$$

Donde $h$ es la altitud ortométrica/elipsoidal en metros.

#### RF-SS04: Reglas Heurísticas de Tormenta
* **Aviso Temprano:** $\Delta P_{0(3\text{h})} \le -1.5 \text{ hPa}$.
* **Frente de Tormenta Severo:** $\Delta P_{0(3\text{h})} \le -2.5 \text{ hPa}$.
* **Microrráfaga / Convección Súbita:** $\Delta P_{0(45\text{min})} \le -1.5 \text{ hPa}$.

#### RF-SS05: Auditoría con IA On-Device (AICore / LiteRT)
Cuando la tasa de cambio de presión cruza el umbral de Nivel 2 o Nivel 3, el servicio en segundo plano invoca al modelo de lenguaje local pasando un payload estructurado en JSON.

* **Contrato de Entrada (JSON al Modelo Local):**
```json
{
  "timestamp": 1730441400,
  "fsm_mode": "ESTACIONARIO",
  "raw_pressure_current_hpa": 782.4,
  "delta_p_raw_3h": -2.8,
  "delta_p0_normalized_3h": -2.7,
  "altitude_meters": 2150.0,
  "steps_last_30min": 0,
  "ambient_light_lux_drop_ratio": 0.65
}
```

* **Instrucción de Sistema para el Modelo:**
```text
Actúa como un meteorólogo táctico y auditor de datos inerciales.
Analiza el payload JSON recibido:
1. Comprueba si los datos físicos son coherentes (ej. si hay caída de presión pero la altitud GNSS subió sin pasos detectados, señala anomalía por rebote de satélite).
2. Determina el nivel de riesgo real para montañistas.
3. Devuelve estrictamente un objeto JSON con:
   - "valid_event": boolean
   - "risk_level": "BAJO" | "MODERADO" | "ALTO" | "CRITICO"
   - "hazard_type": "Frente Frío" | "Microrráfaga Convectiva" | "Tormenta Eléctrica" | "Falso Positivo"
   - "actionable_advice": Instrucción clara de seguridad en máximo 2 frases.
```

---

## 3. Requerimientos No Funcionales y Eficiencia Energética

1. **Autonomía:** El servicio en segundo plano no debe sobrepasar el $1.5\%$ de uso de batería en periodos de 24 horas continuas (ejecución mediante `AlarmManager.setExactAndAllowWhileIdle()` combinada con retención en modo Doze).
2. **Aislamiento Total de Red:** La aplicación se compilará sin la directiva `<uses-permission android:name="android.permission.INTERNET" />`, garantizando seguridad y confidencialidad absoluta en entornos remotos.
3. **Persistencia Local:** Uso de base de datos Room con auto-purgado circular cada 48 horas para mantener el footprint de almacenamiento por debajo de 5 MB.
4. **Resiliencia Operativa:** Implementación de un `BroadcastReceiver` con filtro para `ACTION_BOOT_COMPLETED` y `ACTION_MY_PACKAGE_REPLACED` para reactivar el monitoreo barométrico sin intervención del usuario tras un reinicio del dispositivo.