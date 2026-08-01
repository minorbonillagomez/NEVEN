---
id: neven-studio
title: "Capitulo 13 - NEVEN Studio Standalone"
sidebar_label: 13. NEVEN Studio
sidebar_position: 13
---

# Capitulo 13: NEVEN Studio Standalone

**Disponible desde:** Julio 2026

NEVEN Studio Standalone es el modo de operación de NEVEN **sin Microsoft Excel**. Abre una interfaz web completa en el navegador del sistema que permite ejecutar análisis estadísticos, cargar datos y usar el catálogo de funciones Data Lab — todo sin necesitar una licencia de Excel.

---

## 13.1 Arranque rápido

```
1. Doble clic en:   C:\NEVEN\taskpane\NEVEN Studio.vbs
2. Se abre el navegador en:  http://localhost:5555
3. Listo.
```

---

## 13.2 Pestañas del Studio

| Pestaña | Función |
|:---|:---|
| **Data Lab** | Análisis punto-y-clic sin código (18 funciones) |
| **Run Script** | Editor de código R / Julia / Python con ejecución directa |
| **Data Studio** | Carga de archivos CSV, Parquet, JSON → tabla `dataset` |
| **AI** | Integración con LMStudio para interpretación de resultados |

---

## 13.3 Data Lab

El Data Lab expone el catálogo de funciones analíticas de NEVEN mediante una interfaz guiada.

### Flujo de uso

```
1. Cargar datos
   Data Studio → "Cargar archivo" → seleccionar CSV / Parquet / JSON
   (o enviar desde Excel via Bridge)

2. Seleccionar función
   Data Lab → dropdown "Familia" → lista de funciones

3. Asignar columnas a roles
   Panel de columnas: clic en columna → clic en rol (X, Y, T, ID)

4. Configurar parámetros
   Controles automáticos según tipo (spinner, checkbox, dropdown)

5. Ejecutar
   Clic en "Ejecutar análisis"

6. Ver resultados
   Slots tipificados: tablas, gráficos HTML, escalares, vectores
```

### Familias disponibles

| Familia | Código | Funciones |
|:---|:---|:---|
| Análisis de Datos | **AD** | K-Medias, Componentes Principales (PCA), Clustering Jerárquico |
| Regresión | **RG** | Lineal, Logística, Árbol de Decisión, Datos Panel, Poisson, Series de Tiempo, SVM, Tobit |
| Conjuntos de Datos | **DS** | Wooldridge (115 datasets de econometría) |
| Text Mining | **TM** | Análisis de texto (PDF, DOCX, TXT) |
| Mis Funciones | **UC** | Plantillas para funciones personalizadas |

### Resultados (Slots)

Los resultados se presentan en secciones tipificadas:

| Tipo | Presentación |
|:---|:---|
| `table` | Tabla HTML con scroll |
| `html` | Gráfico interactivo Plotly en iframe |
| `scalar` | Valor en `<pre>` |
| `vector` | Lista en `<pre>` |

Los resultados **Tier 1** aparecen expandidos por defecto.
Los resultados **Tier 2** aparecen en la sección "Detalles técnicos" colapsada.

---

## 13.4 Run Script

Ejecuta código directamente en los motores de lenguaje.

```
Pestaña "Run Script"
  → Seleccionar lenguaje: R | Julia | Python
  → Escribir código
  → Clic "Ejecutar"
  → Ver resultado
```

**Ejemplo R:**
```r
df <- data.frame(x = 1:5, y = c(2,4,5,4,5))
cor(df$x, df$y)
```

**Ejemplo Python:**
```python
import duckdb
conn = duckdb.connect()
conn.execute("SELECT COUNT(*) FROM dataset").fetchone()
```

---

## 13.5 Data Studio

Permite cargar datos al `dataset` activo que usa el Data Lab.

| Formato | Soporte |
|:---|:---|
| CSV | ✅ Auto-detección de separador y encoding |
| Parquet | ✅ |
| JSON | ✅ (array de objetos) |
| Excel (via Bridge) | ✅ Desde NEVEN para Excel |

Los datos se almacenan en **DuckDB in-memory** como la tabla `dataset`.

---

## 13.6 Text Mining con IA

La función **TM → Text Analysis** produce:

1. **Estadísticas léxicas** — total palabras, vocabulario, riqueza léxica
2. **Análisis de sentimiento** — positivo / neutro / negativo
3. **Resumen contextual (IA)** — generado por LMStudio (si está activo)
4. **Resumen extractivo (TF-IDF)** — top N oraciones por relevancia
5. **Gráfico de frecuencias** — barras horizontales Plotly
6. **Nube de palabras** — espiral de Arquímedes con Plotly

### Configurar LMStudio

En `C:\NEVEN\neven-config.json`:

```json
"AI": {
  "enabled": true,
  "provider": "lmstudio",
  "model": "nvidia/nemotron-3-nano-4b",
  "endpoint": "http://localhost:1234/v1/chat/completions",
  "maxTokens": 1000,
  "temperature": 0.3,
  "timeout": 120
}
```

Si LMStudio no está corriendo, el slot de resumen IA simplemente no aparece — los demás resultados funcionan normalmente.

---

## 13.7 Agregar funciones propias

Cualquier usuario puede agregar sus propias funciones al catálogo Data Lab con dos archivos:

**Archivo 1: `MiFuncion.Studio.R`**
```r
MiFuncion.Studio <- function(data_X, Param1 = 3L) {
  resultado <- list(
    tabla = mi_analisis(data_X),
    valor = 42.5
  )
  tier_map <- c(tabla = 1L, valor = 2L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
```

**Archivo 2: `MiFuncion.json`**
```json
{
  "id": "MiFuncion",
  "family": "UC",
  "family_label": "Mis Funciones",
  "name": "Mi Análisis",
  "description": "Descripción breve.",
  "languages": ["r"],
  "function_name": "MiFuncion.Studio",
  "file": "MiFuncion.Studio.R",
  "variable_roles": {
    "X": { "label": "Variables", "types": ["numeric"], "multiple": true, "required": true }
  },
  "parameters": [
    { "name": "Param1", "label": "Parámetro", "type": "integer", "default": 3, "tier": 1 }
  ]
}
```

Copiar ambos archivos a `C:\NEVEN\functions\` y reiniciar NEVEN Studio.

Ver guía completa: `C:\NEVEN\functions\COMO_AGREGAR_FUNCIONES.md`

---

## 13.8 Diferencias con NEVEN para Excel

| Característica | NEVEN Excel | NEVEN Studio |
|:---|:---:|:---:|
| Requiere Excel | ✅ | ❌ |
| Funciones como fórmulas `=R.func()` | ✅ | ❌ |
| Data Lab punto-y-clic | ❌ | ✅ |
| Run Script (R/Julia/Python) | Parcial | ✅ |
| Carga de archivos CSV/Parquet | ❌ | ✅ |
| AI / LMStudio integration | Parcial | ✅ |
| WebView2 Viewer | ✅ | ❌ |
| Pluto.jl Notebooks | ✅ | ❌ |
| Quarto Reportes | ✅ | ❌ |
| Ribbon COM nativo | ✅ | ❌ |
| Mismos motores R/Julia/Python | ✅ | ✅ |
| Mismos binarios C++ | ✅ | ✅ |

Ambos modos se instalan juntos — la misma instalación en `C:\NEVEN\` sirve para los dos.

---

*NEVEN Studio Standalone — Julio 2026*
*Universidad de Costa Rica — Tesis de Maestría*
