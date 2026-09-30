# NEVEN v3.0 — Taxonomía de Viewers por Estructura de Datos

## Contexto

El Task Pane de NEVEN v3.0 incluye un tab "Viewers" que permite al usuario visualizar datos cargados (CSV, Parquet, o eventualmente rangos de Excel). Sin embargo, no todos los datos se pueden graficar directamente — dependiendo de su estructura, requieren un proceso previo de transformación.

Este documento define la taxonomía de datos que NEVEN reconoce y cómo cada tipo fluye hacia la visualización.

---

## Taxonomía de Estructuras de Datos

### 1. Corte Transversal (CT)

**Definición:** Una muestra de tamaño N observada en un único momento del tiempo. No tiene orden inherente.

**Características:**
- N registros, M variables
- Sin dimensión temporal
- Sin ordenamiento natural
- Típicamente N es grande (miles o millones)

**Problema para graficación:** No se pueden graficar N=3,000,000 puntos directamente. Se requiere un proceso de reducción dimensional o agrupamiento.

**Procesos de transformación válidos (N → K):**

| Proceso | Entrada | Salida | Uso en viewer |
|---------|---------|--------|---------------|
| K-Means | N filas × M cols | K centroides × M cols | Scatter de clusters, radar por grupo |
| ACP/PCA | N × M | N × 2 (o 3) componentes | Scatter 2D/3D (sample de N) |
| GROUP BY | N filas | K grupos con métricas | Barras, tabla |
| KNN | N filas | N clasificados | Scatter coloreado por clase (sample) |
| Histograma | N valores | B bins con frecuencia | Barras de distribución |
| Correlación | N × M | M×M matriz | Heatmap + scatter pares |

**Regla:** Para CT, antes de la graficación típicamente existe un proceso que transforma N → K donde K << N.

---

### 2. Serie de Tiempo (ST)

**Definición:** Uno o varios registros observados en diferentes momentos del tiempo. El tiempo provee el ordenamiento natural.

**Características:**
- T observaciones ordenadas cronológicamente
- Una o más variables medidas en cada t
- El eje X siempre es el tiempo
- No requiere reducción (T es naturalmente acotado por el periodo)

**Procesos opcionales:**
- Suavizado (media móvil)
- Descomposición (tendencia + estacionalidad + ruido)
- Detección de cambios estructurales

**Viewers directos:**
- Línea temporal (una o varias series superpuestas)
- Área apilada
- Sparklines por variable
- Bandas de confianza

**Flujo:** CSV → Mapear columna tiempo → Graficar directo

---

### 3. Geoespacial (GS)

**Definición:** Datos que contienen coordenadas geográficas (latitud, longitud) asociadas a variables cuantitativas o categóricas.

**Características:**
- Requiere obligatoriamente: columna LAT + columna LON
- Una o más variables asociadas a cada ubicación
- Puede ser CT+GS (puntos de venta) o ST+GS (trayectorias)

**Viewers directos:**
- Mapa de puntos (color por valor)
- Mapa de calor (heatmap geoespacial)
- Mapa de burbujas (tamaño por valor)
- Mapa con series temporales en popup (si tiene dimensión temporal)

**Flujo:** CSV → Mapear LAT/LON/Valor → Graficar directo (con sample si N > 10K)

---

### 4. Relacional (REL)

**Definición:** Datos que representan conexiones entre entidades o secuencias de eventos con inicio/fin.

**Características:**
- Requiere: columna Origen + columna Destino (para grafos)
- O bien: columna Tarea + Inicio + Fin (para Gantt)
- Puede incluir pesos o categorías

**Sub-tipos:**

| Sub-tipo | Columnas requeridas | Viewer |
|----------|-------------------|--------|
| Grafo | Origen, Destino, [Peso] | Network (D3.js force-directed) |
| Gantt | Tarea, Inicio, Fin, [Categoría] | Timeline horizontal |

**Flujo:** CSV → Mapear columnas → Graficar directo

---

## Diseño del Tab Viewers

### UI: Sub-tabs por familia

```
┌─────────────────────────────────────────────┐
│  VIEWERS                                     │
├─────────────────────────────────────────────┤
│  [Corte Transversal] [Series] [Geo] [Relac] │
├─────────────────────────────────────────────┤
│                                             │
│  Contenido según sub-tab seleccionado        │
│                                             │
└─────────────────────────────────────────────┘
```

### Sub-tab: Corte Transversal (CT)

```
┌─────────────────────────────────────────┐
│  Proceso de transformación:              │
│  [K-Means ▼] [ACP ▼] [GROUP BY ▼]      │
│                                          │
│  Parámetros:                             │
│    K-Means: K = [___5___]               │
│    ACP: Componentes = [__2__]           │
│    GROUP BY: Columna = [Region ▼]       │
│              Métrica = [SUM ▼]          │
│              Sobre = [Ventas ▼]         │
│                                          │
│  [Ejecutar transformación]               │
│                                          │
│  ┌─────────────────────────────────────┐│
│  │  Gráfico resultado (Plotly)         ││
│  └─────────────────────────────────────┘│
│                                          │
│  Tabla de resultados (K filas)           │
└─────────────────────────────────────────┘
```

**Endpoints requeridos:**
- `POST /api/viewer/ct/kmeans` → {k} → retorna centroides + asignaciones (sample)
- `POST /api/viewer/ct/pca` → {n_components} → retorna coordenadas + varianza
- `POST /api/viewer/ct/groupby` → ya existe en /api/groupby

---

### Sub-tab: Series de Tiempo (ST)

```
┌─────────────────────────────────────────┐
│  Columna tiempo: [Fecha ▼]              │
│  Variables a graficar: [☑Ventas ☑Costos]│
│  Tipo: [Línea ▼] [Área ▼] [Barras ▼]  │
│                                          │
│  [Graficar]                              │
│                                          │
│  ┌─────────────────────────────────────┐│
│  │  Gráfico temporal (Plotly)          ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

**Endpoints requeridos:**
- `POST /api/viewer/st` → {time_col, value_cols, chart_type} → retorna datos temporales

---

### Sub-tab: Geoespacial (GS)

```
┌─────────────────────────────────────────┐
│  Latitud: [Lat ▼]                       │
│  Longitud: [Lon ▼]                      │
│  Valor/Color: [Ventas ▼]               │
│  Tipo mapa: [Scatter ▼] [Heat] [Bubble]│
│                                          │
│  [Generar Mapa]                          │
│                                          │
│  ┌─────────────────────────────────────┐│
│  │  Mapa Leaflet.js                    ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

**Endpoints requeridos:**
- `POST /api/viewer/geo` → {lat_col, lon_col, val_col, map_type, sample_size} → retorna puntos (max 10K)

---

### Sub-tab: Relacional (REL)

```
┌─────────────────────────────────────────┐
│  Tipo: [Grafo ▼] [Gantt ▼]             │
│                                          │
│  Grafo:                                  │
│    Origen: [From ▼]                     │
│    Destino: [To ▼]                      │
│    Peso: [Amount ▼] (opcional)          │
│                                          │
│  Gantt:                                  │
│    Tarea: [Task ▼]                      │
│    Inicio: [Start ▼]                    │
│    Fin: [End ▼]                         │
│    Categoría: [Team ▼] (opcional)       │
│                                          │
│  [Generar]                               │
│                                          │
│  ┌─────────────────────────────────────┐│
│  │  D3.js / Plotly                     ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

**Endpoints requeridos:**
- `POST /api/viewer/graph` → {source_col, target_col, weight_col} → retorna nodos + aristas
- `POST /api/viewer/gantt` → {task_col, start_col, end_col, cat_col} → retorna tareas con fechas

---

## Detección Automática de Tipo

El servidor puede sugerir automáticamente el tipo de datos basado en heurísticas:

| Señal | Tipo sugerido |
|-------|--------------|
| Columnas "lat"/"latitude" + "lon"/"longitude" | GS |
| Columna tipo DATE/TIMESTAMP como primaria | ST |
| Columnas "from"/"source" + "to"/"target"/"dest" | REL (Grafo) |
| Columnas "start"/"inicio" + "end"/"fin" | REL (Gantt) |
| Todo numérico sin patrón especial | CT |
| Mix numérico + categórico | CT |

El endpoint `/api/analyze` ya detecta tipos de columnas. Se puede extender para sugerir la familia:

```json
// Response de /api/analyze (extendido)
{
  "status": "ok",
  "statistics": [...],
  "suggested_type": "GS",
  "suggested_mapping": {
    "lat_col": "Latitud",
    "lon_col": "Longitud",
    "val_col": "Ventas"
  }
}
```

---

## Principios de Diseño

1. **CT requiere transformación obligatoria antes de graficar** — no se grafican N puntos crudos
2. **ST y GS van directo** — el mapeo de columnas es suficiente
3. **REL va directo** — solo necesita indicar las columnas de relación
4. **El server hace el trabajo pesado** — DuckDB para agregación, Python para K-Means/ACP
5. **El viewer solo recibe K puntos** — nunca más de 10K datos para el frontend
6. **Sample inteligente** — para scatter de correlación usar `USING SAMPLE 5000 ROWS` de DuckDB
7. **Los viewers existentes (v2.1) siguen funcionando** — `=P.Geodata()`, `=P.Dashboard()` etc. no se eliminan

---

## Plan de Implementación (por prioridad)

### Prioridad 1: ST (Serie de Tiempo)
- Más directa — solo mapear columna tiempo + variables
- El gráfico es un simple line chart con Plotly
- Endpoint: `/api/viewer/st`

### Prioridad 2: GS (Geoespacial)  
- También directa — mapear lat/lon/valor
- Reutiliza Leaflet.js del geo_visualization.py existente
- Endpoint: `/api/viewer/geo`

### Prioridad 3: CT con GROUP BY
- Ya funciona en el tab principal (Data Studio)
- Solo mover/duplicar la UI al sub-tab CT

### Prioridad 4: CT con K-Means / ACP
- Requiere ejecutar sklearn desde el server
- Endpoint: `/api/viewer/ct/kmeans`, `/api/viewer/ct/pca`

### Prioridad 5: REL (Grafo + Gantt)
- Reutiliza network_graph.py y timeline_viewer.py
- Endpoint: `/api/viewer/graph`, `/api/viewer/gantt`

---

## Relación con v2.1

Los viewers v2.1 (`=P.Geodata()`, `=P.Dashboard()`, `=P.Timeline()`, `=P.Red()`) siguen generando HTML que se abre con `=NEVEN.v()`. La taxonomía descrita aquí aplica al **Task Pane v3.0** donde los datos ya están en DuckDB y el viewer se genera dinámicamente desde el server.

En v3.0 completa (con Office.js + sideload), el usuario:
1. Selecciona rango en Excel → datos van a DuckDB
2. El Task Pane detecta el tipo de datos (CT/ST/GS/REL)
3. Sugiere el viewer apropiado
4. El usuario confirma o ajusta el mapeo de columnas
5. El server genera la visualización → se renderiza en el iframe

No se elimina ninguna funcionalidad v2.1. El Task Pane es un layer adicional de interactividad.
