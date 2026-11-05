# Documento de Especificación de Requerimientos de Software (ERS)

## Proyecto: Launcher Neven

### Módulos: Sandbox Isolation, Open Data Engine, Lector RSS y Subsistema de Cápsulas de Conocimiento RAG Dual-Track (On-Device LLM)

## 1. Visión General del Proyecto

**Neven** es un launcher para Android enfocado en la soberanía del usuario, privacidad estricta, orquestación de datos locales y consumo de información libre de manipulación algorítmica.

El sistema se estructura en torno a tres pilares funcionales complementados por una **capa transversal de inferencia local por hardware** (utilizando el acelerador NPU/TPU y el servicio Android AICore / Gemini Nano presente en dispositivos como el Pixel 10 Pro / Pro XL) y un **Subsistema de Cápsulas de Conocimiento Autónomas (Dual-Track Local RAG)**. La inteligencia opera 100% en el dispositivo (*on-device*), sin enviar prompts, telemetría ni datos a servidores externos.

---

## 2. Arquitectura General y Stack Técnico

* **Plataforma objetivo:** Android 11+ (API Level 30 o superior; optimizado con APIs de Android AICore / On-Device GenAI en Android 14+).
* **Lenguaje:** Kotlin.
* **Inyección de Dependencias:** Hilt o Koin.
* **Concurrencia:** Kotlin Coroutines + Flow.
* **Persistencia Local:** Room Database (SQLite) + extensiones vectoriales/FTS locales + Jetpack DataStore para preferencias.
* **Motor de Renderizado Matemático:** Componente nativo/WebView liviano aislado basado en KaTeX local (sin dependencias CDN externas).
* **Motor HTTP / Networking:** Ktor Client / Retrofit con OkHttp (soporte DNS over TLS).
* **Parsing de Feeds:** XmlPullParser nativo sanitizado.
* **Gestión en Segundo Plano:** Android Jetpack WorkManager.
* **Inferencia Local (NPU/TPU):**
  * Primario: Android AICore Service (`GenerativeModel` / Google GenAI SDK local en dispositivos Tensor).
  * Secundario (Fallback agnóstico): MediaPipe GenAI Runtime / Llama.cpp enlazado vía NDK (Vulkan Backend).

---

## 3. Capa Transversal: On-Device LLM Engine (Gemini Nano Core)

### 3.1. Objetivo
Proveer un servicio unificado en el launcher que gestione la disponibilidad, ciclo de vida e inferencia rápida de modelos de lenguaje pequeños (SLM) acelerados en silicio local, garantizando latencias en milisegundos y delimitación estricta de contexto (*grounded context*).

### 3.2. Requerimientos Funcionales Transversales
* **RF-IA-01: Verificación de Aceleración Local:**
  * El launcher debe consultar la disponibilidad del servicio `AICore` al inicio. Si el hardware no cuenta con aceleración de modelo nativa, las funciones de IA se degradan elegantemente o se conmuta al runtime fallback opcional.
* **RF-IA-02: Garantía de Soberanía Cero-Red:**
  * Todo proceso de inferencia, tokenización, lectura de chunks y embeddings debe ejecutarse en el espacio del *Private Compute Core* sin abrir sockets de red.
* **RF-IA-03: Restricción Determinista y Esquemas JSON:**
  * La inferencia analítica debe ejecutarse bajo configuraciones deterministas ($\text{temperature} = 0.0$, $\text{topK} = 1$) y utilizar *ResponseSchema* nativo o prefijado de llaves sintácticas para impedir texto conversacional no estructurado.
* **RF-IA-04: Gestión de Temperatura y Memoria:**
  * La inferencia en lote (ej. durante la sincronización de WorkManager) debe pausarse si la temperatura de la batería supera los $40^\circ\text{C}$ o si el dispositivo se encuentra en modo de ahorro de energía estricto.

---

## 4. Módulo 1: Sandbox Isolation Controller + Enrutamiento Inteligente

### 4.1. Objetivo
Aislar aplicaciones de alta telemetría en un perfil administrado (`WorkProfile`), utilizando el modelo local para auditar intenciones de apertura, clasificar riesgos y ofrecer un punto de entrada por comandos naturales.

### 4.2. Requerimientos Funcionales (RF)
* **RF-SB-01: Detección y Enlace de Perfil Administrado:**
  * Detección automática del `UserHandle` de perfil de trabajo mediante `UserManager.getUserProfiles()`. Soporte para aprovisionamiento o adopción de perfiles preexistentes.
* **RF-SB-02: Categorización Visual y Cajón Hermético:**
  * Agrupación visual independiente de las aplicaciones del sandbox con badges distintivos y separación estricta en el cajón de aplicaciones.
* **RF-SB-03: Control de Estado (Freeze / Deep Sleep):**
  * Disparar el congelamiento de paquetes (`DevicePolicyManager.setPackagesSuspended`) o desactivación del perfil completo mediante un solo gesto o automatización por horario.
* **RF-SB-04: Enrutamiento Contextual con LLM Local (Smart Dispatcher):**
  * Al escribir o dictar un comando en la barra unificada (ej. *"pedir comida a domicilio"* o *"revisar saldo bancario"*), el modelo local clasifica la semántica de la orden, determina si requiere una aplicación contenida en el sandbox y ofrece activarla/descongelarla únicamente por el lapso de uso requerido.
* **RF-SB-05: Auditoría Local de Permisos Críticos:**
  * El LLM local analiza la lista de permisos solicitados por las apps instaladas dentro del sandbox y genera un informe de nivel de riesgo en lenguaje claro sin enviar telemetría a la nube.

---

## 5. Módulo 2: Motor de Datos Abiertos + Síntesis Natural (Open Data Engine)

### 5.1. Objetivo
Ingestar series temporales de portales públicos (REST / JSON / CSV), persistirlas localmente y utilizar el modelo local para traducir consultas en lenguaje natural a queries estructuradas y explicar anomalías numéricas.

### 5.2. Requerimientos Funcionales (RF)
* **RF-OD-01: Gestor de Endpoints Configurables:**
  * Registro de fuentes públicas con URL base, headers, intervalo de refresco y expresión JSONPath objetivo.
* **RF-OD-02: Text-to-JSONPath / Text-to-SQL Asistido por LLM:**
  * El usuario puede pegar un payload de ejemplo de una API pública o formular una pregunta (ej. *"extrae la tasa de interés interbancaria del nodo 'observations'"*), y el modelo local infiere automáticamente el selector JSONPath o genera la query Room/SQLite requerida.
* **RF-OD-03: Almacenamiento Local de Series de Tiempo:**
  * Persistencia en Room (SQLite) de marcas temporales, valores numéricos normalizados y metadatos del indicador.
* **RF-OD-04: Detección de Anomalías y Reporte Ejecutivo:**
  * Durante la ingesta en segundo plano, si un indicador experimenta una variación porcentual superior al umbral configurado ($\vert{}\Delta\vert{} > \theta$), el LLM genera una notificación sintética de una línea contextualizando el cambio histórico.
* **RF-OD-05: Componentes de Visualización Dinámica:**
  * Visualización nativa en Canvas: Sparklines y métricas escalares en el escritorio con tarjeta colapsable de resumen explicativo generado por la NPU.

---

## 6. Módulo 3: Lector RSS Nativo + Resúmenes Ejecutivos en Silicio

### 6.1. Objetivo
Ingestar y renderizar feeds RSS/Atom en texto limpio, utilizando Gemini Nano para generar resúmenes ejecutivos, agrupar temáticas similares y clasificar contenido localmente sin rastreo comercial.

### 6.2. Requerimientos Funcionales (RF)
* **RF-RS-01: Soporte de Formatos y Sanitización Radical:**
  * Parsing nativo de RSS 2.0 y Atom 1.0 con `XmlPullParser`.
  * Sanitización estricta: eliminación de tags `<script>`, `<iframe>`, trackers de píxeles y hojas de estilo inline.
* **RF-RS-02: Generación Local de Resúmenes ("Executive TL;DR"):**
  * Para artículos extensos o preprints técnicos (arXiv), el modelo local procesa el texto plano en el dispositivo y genera una síntesis estructurada en 3 viñetas (*bullet points*) legibles en la vista previa del feed.
* **RF-RS-03: Extracción Semántica de Etiquetas (Zero-Shot Tagging):**
  * El modelo local analiza el contenido y clasifica el artículo en tópicos definidos por el usuario (ej. *Criptografía*, *Macroeconomía*, *Desarrollo Android*) sin depender de los tags provistos por el creador del feed.
* **RF-RS-04: Búsqueda Semántica Vectorial Local:**
  * El LLM / modelo de embeddings local indexa los resúmenes y títulos. El usuario puede buscar por conceptos (ej. *"artículos sobre políticas monetarias restrictivas"*) y encontrar entradas relevantes aunque no contengan exactamente esas palabras literales.
* **RF-RS-05: Soporte OPML y Modo Offline:**
  * Importación/exportación estándar de listas OPML y retención en caché local de los últimos artículos para consumo desconectado.

---

## 7. Módulo 4: Subsistema de Cápsulas de Conocimiento RAG Dual-Track

### 7.1. Objetivo
Soportar bases de conocimiento offline especializadas y auto-contenidas (*Cápsulas*), delegando al usuario la selección explícita del contexto activo para eliminar ambigüedades y maximizar la precisión analítica del modelo local. El subsistema implementa dos vías operativas según la naturaleza del contenido:
1. **Pista Axiomática / Formal (ej. Econometría):** Orientada por Ontologías formales (DAGs), extracción matemática y renderizado KaTeX.
2. **Pista Narrativa / Histórica (ej. "Por qué fracasan los países" de Acemoglu & Robinson):** Orientada por partición jerárquica de Capítulos/Secciones, resúmenes estructurados precalculados y Q&A acotado.

### 7.2. Requerimientos Funcionales - Arquitectura de Cápsulas (Hot-Swapping)
* **RF-KC-01: Formato de Cápsula Desacoplada (.neven):**
  * Cada cápsula debe almacenarse como un paquete o base de datos SQLite autónoma (`capsule_name.db`), incluyendo su esquema ontológico o índice capitular, sus chunks de texto y sus vectores precalculados.
* **RF-KC-02: Montaje Efímero en Memoria (*Hot-Swapping*):**
  * El launcher solo debe mantener en memoria activa los índices de la cápsula seleccionada por el usuario. Al cambiar de cápsula, los recursos de la anterior se liberan, manteniendo el consumo de memoria RAM por debajo de los 80 MB.
* **RF-KC-03: Enfoque Deliberado de Contexto por el Usuario:**
  * La interfaz del launcher debe exigir al usuario la selección explícita de la cápsula y del nodo conceptual o capítulo antes de ejecutar consultas analíticas profundas, garantizando que el espacio de búsqueda no exceda los 500 tokens de contexto recuperado.

### 7.3. Requerimientos Funcionales - Pista Axiomática (Econometría y Modelos Formales)
* **RF-KC-04: Meta-Heurística Ontológica para RAG:**
  * La cápsula formal debe contener un grafo acíclico dirigido (DAG) de conceptos (ej. *Heterocedasticidad*, *Variables Instrumentales*, *MCO*, *Teorema de Gauss-Markov*).
  * La consulta del usuario primero se mapea contra el nodo ontológico correspondiente, podando el espacio documental antes de buscar similitud semántica.
* **RF-KC-05: Preservación Sintáctica KaTeX:**
  * Los chunks de texto indexados deben almacenar las ecuaciones matemáticas formalizadas en KaTeX inline (`$...$`) y display (`$$...$$`).
  * El modelo local debe ser instruido de forma determinista para transcribir y aplicar las fórmulas del contexto sin reescribir subíndices, superíndices ni matrices.
* **RF-KC-06: Renderizado Local de Fórmulas Matemáticas:**
  * El launcher debe incluir un componente de renderizado KaTeX desacoplado de internet para mostrar matrices, integrales y operadores econométricos con fidelidad tipográfica instantánea.

### 7.4. Requerimientos Funcionales - Pista Narrativa (Ensayos e Historia Económica)
* **RF-KC-07: Poda Jerárquica Capitular:**
  * La partición documental no utiliza grafos complejos, sino el árbol jerárquico nativo: `Libro -> Capítulo -> Sección / Caso Histórico`.
  * La búsqueda vectorial y las preguntas Q&A quedan confinadas de forma estricta a los chunks de la sección seleccionada (ej. Cap. 4, Sección *"La Serrata de Venecia"*).
* **RF-KC-08: Resúmenes Ejecutivos Precalculados (0 ms Latency):**
  * Durante la ingesta/compilación de la cápsula ensayística, cada capítulo y sección debe almacenar un resumen precalculado bajo una plantilla fija:
    1. *Tesis Central* (1 oración).
    2. *Evidencia / Caso Histórico* (viñetas de actores y contexto).
    3. *Mecanismo Institucional* (extractivo vs. inclusivo).
  * Al ingresar a una sección, este resumen debe desplegarse inmediatamente sin invocar la NPU ni generar consumo energético.
* **RF-KC-09: Interrogación Puntual sobre el Caso:**
  * Si el usuario realiza una pregunta sobre la sección, Gemini Nano solo procesa los fragmentos de texto de esa sección específica, previniendo la mezcla o contaminación cruzada entre episodios históricos lejanos.
* **RF-KC-10: Índice Analítico Transversal Opcional:**
  * Soporte para etiquetas canónicas transversales (ej. `coyuntura_critica`, `destruccion_creativa`) extraídas del índice temático del libro, permitiendo interrogar fragmentos específicos de múltiples capítulos que compartan el mismo concepto teórico.

---

## 8. Modelo de Datos Actualizado (Room / SQLite)

```sql
-- ============================================================================
-- 1. MÓDULO OPEN DATA
-- ============================================================================
CREATE TABLE open_data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    json_path TEXT NOT NULL,
    refresh_interval_minutes INTEGER NOT NULL DEFAULT 360,
    unit_label TEXT,
    alert_threshold_percent REAL DEFAULT 5.0,
    last_updated INTEGER
);

CREATE TABLE open_data_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,
    metric_value REAL NOT NULL,
    FOREIGN KEY(source_id) REFERENCES open_data_sources(id) ON DELETE CASCADE
);

-- ============================================================================
-- 2. MÓDULO RSS
-- ============================================================================
CREATE TABLE rss_feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    feed_url TEXT UNIQUE NOT NULL,
    site_url TEXT,
    category TEXT DEFAULT 'General',
    last_sync INTEGER
);

CREATE TABLE rss_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    link TEXT UNIQUE NOT NULL,
    author TEXT,
    published_date INTEGER,
    content_plain TEXT,
    ai_summary TEXT,              -- Resumen generado localmente por Gemini Nano
    ai_tags TEXT,                 -- Etiquetas inferidas localmente (JSON array)
    embedding_vector BLOB,        -- Vector para búsqueda semántica local
    is_read INTEGER DEFAULT 0,
    is_bookmarked INTEGER DEFAULT 0,
    FOREIGN KEY(feed_id) REFERENCES rss_feeds(id) ON DELETE CASCADE
);

-- ============================================================================
-- 3. MÓDULO SANDBOX: Registro de Políticas Locales
-- ============================================================================
CREATE TABLE sandbox_app_policies (
    package_name TEXT PRIMARY KEY,
    app_label TEXT NOT NULL,
    auto_freeze_on_leave INTEGER DEFAULT 1,
    risk_level TEXT DEFAULT 'UNKNOWN',
    last_unfrozen INTEGER
);

-- ============================================================================
-- 4. SUBSISTEMA DE CÁPSULAS DE CONOCIMIENTO (DUAL-TRACK RAG)
-- ============================================================================
CREATE TABLE knowledge_capsules (
    id TEXT PRIMARY KEY,          -- ej. "econometria_mco", "why_nations_fail"
    title TEXT NOT NULL,
    author TEXT,
    capsule_type TEXT NOT NULL,   -- 'AXIOMATIC_ONTOLOGY' | 'HIERARCHICAL_ESSAY'
    version TEXT NOT NULL,
    file_path TEXT NOT NULL,
    is_active INTEGER DEFAULT 0
);

-- Pista 1: Ontología Formal (Cápsulas Axiomáticas)
CREATE TABLE ontology_nodes (
    id TEXT PRIMARY KEY,          -- ej. "HETEROCEDASTICIDAD"
    capsule_id TEXT NOT NULL,
    label TEXT NOT NULL,
    parent_concept_id TEXT,
    description TEXT,
    axiomatic_conditions TEXT,    -- Supuestos o fórmulas clave en KaTeX
    associated_tests TEXT,        -- Lista JSON de tests econométricos
    FOREIGN KEY(capsule_id) REFERENCES knowledge_capsules(id) ON DELETE CASCADE
);

-- Pista 2: Partición Jerárquica (Cápsulas Narrativas/Ensayos)
CREATE TABLE book_chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capsule_id TEXT NOT NULL,
    chapter_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary_markdown TEXT,        -- Resumen precalculado a nivel capítulo
    FOREIGN KEY(capsule_id) REFERENCES knowledge_capsules(id) ON DELETE CASCADE
);

CREATE TABLE book_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    section_code TEXT NOT NULL,   -- ej. "ch4_sec2_venecia"
    title TEXT NOT NULL,
    historical_case TEXT,         -- ej. "Venecia - La Serrata"
    precomputed_summary TEXT,     -- Resumen de 3 bloques (Tesis, Evidencia, Mecanismo)
    FOREIGN KEY(chapter_id) REFERENCES book_chapters(id) ON DELETE CASCADE
);

-- Chunks Documentales Comunes para RAG Local
CREATE TABLE capsule_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capsule_id TEXT NOT NULL,
    ontology_node_id TEXT,        -- Vinculado si es Pista Axiomática
    section_id INTEGER,           -- Vinculado si es Pista Narrativa
    content_raw TEXT NOT NULL,    -- Texto con fórmulas en $...$ o $$...$$
    embedding BLOB,               -- Vector cuantizado local
    FOREIGN KEY(capsule_id) REFERENCES knowledge_capsules(id) ON DELETE CASCADE,
    FOREIGN KEY(ontology_node_id) REFERENCES ontology_nodes(id) ON DELETE SET NULL,
    FOREIGN KEY(section_id) REFERENCES book_sections(id) ON DELETE SET NULL
);
```

---

## 9. Criterios de Aceptación Técnicos

1. **Inferencia Local Sin Red:** Todas las funciones de IA (resúmenes RSS, generación de JSONPath, análisis de riesgo de apps y síntesis RAG de cápsulas) deben operar al 100% en modo avión sin fallos ni llamadas externas.
2. **Latencia Sub-Segundo en Prefill y 25-45 t/s en Decoding:** 
   * En consultas de Cápsulas con contexto podado (< 500 tokens), el inicio de respuesta (*Time to First Token*) no debe superar los 400 ms en la TPU del Pixel 10 Pro / Pro XL.
   * La generación de síntesis técnica debe mantener una tasa estable entre 25 y 45 tokens por segundo.
3. **Fidelidad KaTeX Cero-Errores:** Ninguna fórmula recuperada en la Pista Axiomática debe sufrir mutaciones en delimitadores (`$`, `$$`) o caracteres matemáticos al ser procesada por el sintetizador local.
4. **Resúmenes Instantáneos (0 ms) en Ensayos:** La navegación entre capítulos y secciones de libros ensayísticos debe renderizar los resúmenes estructurados de inmediato desde la base de datos local sin invocar el modelo generativo.
5. **Aislamiento Estricto del Sandbox:** Ningún dato analítico, fragmento de libro o consulta proveniente de las cápsulas de conocimiento puede ser visible ni accesible para aplicaciones ejecutándose dentro del perfil de trabajo aislado.
6. **Respeto Térmico y de Batería:** Las tareas pesadas de ingestión o inferencia por lotes deben suspenderse si el dispositivo entra en modo de ahorro de batería o la temperatura del SoC/batería supera los $40^\circ\text{C}$.