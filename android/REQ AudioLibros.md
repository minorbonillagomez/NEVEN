# Documento de Especificación de Requerimientos de Software (SRS)

**Proyecto:** Nevem Audiobook Suite (PC Studio & Mobile Player)  
**Arquitectura:** Sistema Dual Desacoplado (Procesamiento Pesado en PC / Reproducción Especializada en Móvil)  
**Target PC:** Windows / Linux (Python o C# / .NET / Electron / Rust)  
**Target Móvil:** Android Studio (Kotlin, Jetpack Compose, Media3 / ExoPlayer)  
**Formato de Intercambio Primario:** Contenedor de audio `.m4b` (AAC + QuickTime Chapter Track + Metadatos ID3 / MP4 Atoms)  

---

## 1. Visión General del Sistema

El ecosistema resuelve la generación y consumo autónomo de audiolibros a partir de fuentes documentales (EPUB y PDF) sin depender de servicios en la nube ni suscripciones de pago.

1. **Aplicación PC (Nevem Studio / Synthesizer):** Responsable de la extracción y depuración de texto, segmentación algorítmica por capítulos, síntesis neural local (TTS con modelos ONNX offline tipo Piper o Kokoro), etiquetado de metadatos (portadas, autor, tracks de tiempo) y empaquetado en un archivo único `.m4b`. Incorpora un servidor HTTP local para transferencia inalámbrica directa vía código QR y compatibilidad con transferencia USB.
2. **Aplicación Móvil (Nevem Player / Reader):** Reproductor de voz de alta precisión enfocado en ergonomía de audio-lectura. Cuenta con biblioteca vertical de portadas, navegación por tabla de capítulos nativa, saltos asimétricos, retroceso inteligente por inactividad (*Auto-Rewind*), temporizador de sueño con acelerómetro y persistencia al segundo del punto de escucha por libro.

---

## 2. Requerimientos de la Aplicación de PC (Studio / Synthesizer)

```
+-----------------------------------------------------------------------------------+
|                            FLUJO DE TRABAJO EN PC                                 |
+-----------------------------------------------------------------------------------+
  [EPUB / PDF] 
       │
       ▼
  [Parser & Cleaner] ──> Extrae texto por capítulos, omite pies de página/índices
       │
       ▼
  [Motor TTS Local]  ──> Síntesis paralela offline (Piper / Kokoro ONNX) -> .wav chunks
       │
       ▼
  [FFmpeg Muxer]     ──> Concatena audio a AAC + Graba Chapters Markers + Portada
       │
       ▼
  [Export: .m4b]
       │
       ├─ Transferencia USB / Almacenamiento Local
       └─ Servidor HTTP Local (Genera Código QR para descarga directa en LAN)
```

### 2.1 Requerimientos Funcionales (PC)

#### RF-PC01: Ingesta y Procesamiento de Documentos
* **RF-PC01.1 (EPUB):** Parseo del archivo de tabla de contenidos (`toc.ncx` o archivo `nav.xhtml`) para dividir el libro en capítulos canónicos con sus respectivos títulos textuales.
* **RF-PC01.2 (PDF):** Extracción de texto con filtrado inteligente de encabezados repetitivos, números de pie de página y saltos de línea huérfanos. Detección heurística de capítulos por patrones de fuente o marcadores de sección.
* **RF-PC01.3 (Extracción de Portada):** Extracción automática de la imagen de portada empotrada en el EPUB/PDF. Si no existe, permitir al usuario arrastrar y soltar una imagen personalizada (`.jpg`, `.png`).

#### RF-PC02: Motor de Síntesis de Voz Neuronal Offline
* **RF-PC02.1 (Ejecución 100% Local):** Integración de un motor TTS basado en redes neuronales livianas (recomendado: **Piper TTS** por su velocidad sobre CPU/GPU o **Kokoro TTS** por naturalidad fonética). Prohibida la dependencia de APIs de nube.
* **RF-PC02.2 (Segmentación y Batches):** El texto de cada capítulo debe dividirse en oraciones delimitadas por signos de puntuación (`.`, `!`, `?`) para inferencia por lotes, garantizando que no se corten palabras a mitad de fonema.
* **RF-PC02.3 (Multihilo / Paralelización):** La cola de renderizado debe permitir sintetizar múltiples capítulos en paralelo según los núcleos del procesador o VRAM disponible.

#### RF-PC03: Empaquetado y Creación de Metadatos (.M4B)
* **RF-PC03.1 (Muxing con FFmpeg):** La aplicación utilizará un wrapper de `FFmpeg` para:
  * Codificar las salidas de audio a formato `AAC` (`.m4a` / `.m4b`) a una tasa de bits optimizada para voz (64 kbps a 96 kbps mono/estéreo).
  * Incrustar la imagen de portada en el átomo `covr`.
  * Incrustar etiquetas estándar: `title` (Título del libro), `artist` / `album_artist` (Autor), `composer` (Modelo/Voz TTS utilizada).
* **RF-PC03.2 (Tabla de Capítulos):** Generar el fichero de metadatos de capítulos en formato `FFMETADATA` y empaquetarlo en la pista de capítulos del contenedor MP4 (`chpl` atom) con:
  * `TIMEBASE=1/1000` (resolución en milisegundos).
  * `START` y `END` exactos por cada capítulo procesado.
  * Título legible del capítulo (ej. *"Capítulo 1: El comienzo"*).

#### RF-PC04: Servidor Local de Distribución y Transferencia
* **RF-PC04.1 (Servidor HTTP Embebido):** La aplicación PC debe ser capaz de levantar un servidor HTTP ligero en un puerto configurable (por defecto: `8080`).
* **RF-PC04.2 (Generador de QR):** Al finalizar la compilación del libro, la interfaz mostrará un código QR que codifica la dirección local de descarga directa (ej. `http://192.168.1.X:8080/download/<book_id>`).
* **RF-PC04.3 (Compatibilidad MTP / Cable):** Permitir exportar el archivo `.m4b` directamente a cualquier carpeta del sistema de archivos del usuario para transferencia manual mediante cable USB o sincronización de carpetas de Windows.

---

## 3. Requerimientos de la Aplicación Móvil (Android Player)

### 3.1 Requerimientos Funcionales (Móvil)

#### RF-MOB01: Biblioteca Visual Especializada
* **RF-MOB01.1 (Aspect Ratio de Portadas):** La vista principal desplegará una cuadrícula dinámica con portadas verticales en proporción canónica de libro ($1:1.5$ o $1:1.6$), diferenciándose de reproductores de música convencionales ($1:1$).
* **RF-MOB01.2 (Progreso Visual por Libro):** Cada tarjeta de libro en la biblioteca mostrará:
  * Porcentaje total completado ($0\text{--}100\%$).
  * Tiempo restante acumulado (ej. *"Quedan 2h 45m"*).
  * Indicador de "Completado" al alcanzar el final del último capítulo.

#### RF-MOB02: Reproducción de Audio y Soporte Nativo de Capítulos
* **RF-MOB02.1 (Stack Multimedia):** Uso de **AndroidX Media3 (ExoPlayer)** como motor de audio.
* **RF-MOB02.2 (Parseo de Capítulos M4B):** La aplicación leerá los átomos de metadatos de capítulos del archivo `.m4b` sin requerir archivos `.cue` o `.txt` externos.
* **RF-MOB02.3 (Diálogo de Tabla de Contenidos):** Un botón accesible desde la pantalla de reproducción desplegará la lista completa de capítulos con su duración individual, permitiendo saltar directamente a cualquiera de ellos sin desfasar el reloj global del libro.

#### RF-MOB03: Ergonomía de Voz y Controles Especializados
* **RF-MOB03.1 (Saltos Asimétricos):**
  * Botón de retroceso corto: Salta exactamente **$-15\text{ segundos}$** (diseñado para reescuchar una frase perdida).
  * Botón de avance largo: Salta exactamente **$+30\text{ segundos}$** (diseñado para saltar intros, créditos o pasajes omitibles).
  * Los botones deben responder a eventos táctiles en pantalla y a los controles remotos de auriculares Bluetooth (`KEYCODE_MEDIA_NEXT` / `PREVIOUS` configurables).
* **RF-MOB03.2 (Retroceso Automático Inteligente / Auto-Rewind):**
  Al pulsar *Play* tras un periodo de inactividad, el motor retrocederá automáticamente la posición del audio según la siguiente escala temporal:
  * Si estuvo en pausa $< 10\text{ minutos}$: Retroceso de $0\text{ s}$ a $2\text{ s}$.
  * Si estuvo en pausa entre $10\text{ minutos}$ y $3\text{ horas}$: Retroceso de $10\text{ s}$ a $15\text{ s}$.
  * Si estuvo en pausa $> 3\text{ horas}$ o días: Retroceso de $25\text{ s}$ a $30\text{ s}$.
* **RF-MOB03.3 (Velocidad con Corrección de Tono / Pitch Correction):**
  Control deslizante de velocidad desde $0.5\times$ hasta $3.0\times$ en pasos de $0.05\times$, utilizando algoritmos de *time-stretching* (Sonic / ExoPlayer SoundTouch) para no alterar la tonalidad de la voz.

#### RF-MOB04: Temporizador de Apagado Inteligente (Sleep Timer)
* **RF-MOB04.1 (Modos de Temporizador):** Posibilidad de fijar apagado por:
  * Minutos fijos (15m, 30m, 45m, 60m).
  * "Fin del capítulo actual".
* **RF-MOB04.2 (Shake to Reset):** Integración con el acelerómetro del dispositivo. Durante los últimos 30 segundos antes de detener la reproducción, el audio bajará su volumen progresivamente (*fade-out*); si el usuario sacude suavemente el teléfono, el temporizador se reiniciará sin necesidad de encender la pantalla.

#### RF-MOB05: Persistencia de Posición al Segundo
* **RF-MOB05.1:** La posición absoluta de reproducción en milisegundos (`current_position_ms`) y el capítulo actual se guardarán en una base de datos local SQLite (Room) ante cualquier evento:
  * Pausa manual.
  * Pérdida de foco de audio (llamada entrante o desconexión de audífonos).
  * Cierre forzado de la app o reinicio del sistema operativo.
* **RF-MOB05.2:** Al reabrir el libro, la reproducción se restaurará en la posición exacta guardada (aplicando previamente el algoritmo de Auto-Rewind si procede).

#### RF-MOB06: Ingesta de Archivos en el Celular
* **RF-MOB06.1 (Escáner de QR Wi-Fi):** La app incluirá una opción de "Descargar desde PC" con lector de cámara. Al escanear el QR mostrado en Nevem Studio, la app iniciará una descarga HTTP directa del archivo `.m4b` guardándolo en el directorio interno de la aplicación.
* **RF-MOB06.2 (Selector de Archivos Local / SAF):** Compatibilidad para importar archivos `.m4b` copiados manualmente por cable USB o almacenamiento compartido mediante el *Storage Access Framework* de Android.

---

## 4. Requerimientos No Funcionales (RNF)

* **RNF-01 (Reproducción en Segundo Plano y Notificación Persistente):** La aplicación móvil debe implementar un `MediaSessionService` conforme al estándar de AndroidX Media3, garantizando reproducción continua con la pantalla apagada y controles completos en la barra de notificaciones y pantalla de bloqueo con la carátula visible.
* **RNF-02 (Aislamiento de Recursos en Móvil):** La app móvil no debe requerir conexión a internet para funcionar, salvo durante la transferencia Wi-Fi local contra la PC.
* **RNF-03 (Consumo de Batería en Reproducción):** El reproductor móvil debe delegar la decodificación del flujo AAC al hardware decodificador del SoC (DSP de audio), manteniendo un consumo de batería inferior al $3\%$ por hora de reproducción con pantalla apagada.
* **RNF-04 (Latencia de Inicio de Audio):** La reanudación del archivo `.m4b` desde el almacenamiento interno debe completarse en menos de $150\text{ ms}$.

---

## 5. Modelo de Datos Local Móvil (Esquema Room Sugerido)

```sql
CREATE TABLE books (
    id TEXT PRIMARY KEY NOT NULL,
    file_path TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    narrator TEXT,
    duration_ms INTEGER NOT NULL,
    cover_image_path TEXT,
    last_played_timestamp INTEGER NOT NULL,
    current_position_ms INTEGER NOT NULL DEFAULT 0,
    current_chapter_index INTEGER NOT NULL DEFAULT 0,
    is_completed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE chapters (
    id TEXT PRIMARY KEY NOT NULL,
    book_id TEXT NOT NULL,
    chapter_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    start_time_ms INTEGER NOT NULL,
    end_time_ms INTEGER NOT NULL,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);
```

---

## 6. Criterios de Aceptación y Pruebas Clave

1. **Prueba de Continuidad (Crash Test / Kill App):** Reproducir un libro, cerrar forzosamente la aplicación móvil desde la vista de apps recientes, reabrirla y validar que la reproducción comience en el milisegundo exacto (aplicando el delta de Auto-Rewind).
2. **Prueba de Metadatos M4B:** Un archivo `.m4b` procesado en PC con 20 capítulos debe leerse en Android desplegando de inmediato los 20 nombres de capítulos y permitiendo saltos precisos sin desincronización de audio.
3. **Prueba de Transferencia por QR:** Con la PC y el móvil conectados a la misma red Wi-Fi, escanear el QR desde la app móvil debe completar la descarga del `.m4b` de 200 MB e indexarlo en la biblioteca automáticamente con su carátula vertical.