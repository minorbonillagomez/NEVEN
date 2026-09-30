# Design — Familia GR (Gráficos) en NEVEN Data Lab

## Overview

La familia GR añade visualización interactiva guiada a NEVEN Data Lab sin modificar ningún componente de infraestructura existente. Cada tipo de gráfico es un par de archivos: un wrapper R (`.Studio.R`) y un sidecar JSON (`.json`) con `"family": "GR"`. El sistema de descubrimiento de catálogo, el handler Python, el serializador R y el renderizador WebView2 ya los manejan de forma nativa.

### Principio de diseño central

> Los Wrapper_GR son ciudadanos de primera clase del ecosistema Studio. No existe código especial para GR. La familia existe porque los sidecars dicen `"family": "GR"` y los wrappers retornan un slot `html` con `<neven-plotly>`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  NEVEN Studio (WebView2 / taskpane.html)                        │
│                                                                 │
│  Data Lab Tab                                                   │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Familia     │  │  Column_Panel     │  │  Results_Panel   │   │
│  │ "Gráficos"  │  │  Roles: X, Y,    │  │  ┌────────────┐  │   │
│  │ [GR_Scatter]│  │  Color, Tamaño,  │  │  │<iframe     │  │   │
│  │ [GR_Barras] │  │  Texto          │  │  │ srcdoc>    │  │   │
│  │ [GR_Lineas] │  └──────────────────┘  │  │<neven-     │  │   │
│  │ ...         │  ┌──────────────────┐  │  │ plotly>    │  │   │
│  └─────────────┘  │ Parameter_Form   │  │  └────────────┘  │   │
│                   │ Titulo, Paleta,  │  └──────────────────┘   │
│                   │ MostrarLeyenda  │                           │
│                   └──────────────────┘                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ POST /api/datalab/run
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  HTTP Server (datalab_handler.py) — SIN CAMBIOS                 │
│  Lee sidecar → construye código R → llama ControlR via pipe     │
└────────────────────────────┬────────────────────────────────────┘
                             │ Named Pipe → ControlR.exe
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ControlR.exe (R 4.4.1 embebido)                                │
│                                                                 │
│  source("GR_Scatter.Studio.R")                                  │
│  GR_Scatter.Studio(data_X=df_x, data_Y=df_y, ...)              │
│  → r_object_to_slots(list(grafico=html_plotly), tier_map=...)   │
│  → [{ name:"grafico", type:"html", value:"<html>...", tier:1 }] │
└─────────────────────────────────────────────────────────────────┘
```

**Componentes que NO cambian:** `datalab_handler.py`, `datalab.js`, `r_object_to_slots.R`, `taskpane.html`, endpoints existentes.

---

## Components and Interfaces

### 3.1 Wrappers R (Wrapper_GR)

Cada wrapper sigue la misma interfaz:

```r
{ID}.Studio <- function(
  data_X,              # data.frame: rol X (siempre presente)
  data_Y     = NULL,   # data.frame: rol Y (cuando aplica)
  data_Color = NULL,   # data.frame: rol Color (cuando aplica)
  data_Tamaño = NULL,  # data.frame: rol Tamaño (cuando aplica)
  data_Texto  = NULL,  # data.frame: rol Texto (cuando aplica)
  Titulo     = "",
  MostrarLeyenda = TRUE,
  Paleta     = 1L,
  # ... parámetros específicos del gráfico
) {
  # 1. Validación de inputs
  # 2. Extracción de vectores de columnas
  # 3. Construcción del spec Plotly (traces + layout)
  # 4. Codificación base64 dentro de tryCatch
  # 5. Retorno con r_object_to_slots
}
```

**Reglas de validación comunes (todas las funciones GR):**

```r
# Validar data_X
if (!is.data.frame(data_X)) stop("'data_X' debe ser un data.frame.")
if (nrow(data_X) == 0)      stop("El filtro aplicado no retorna filas. Verifique la cláusula WHERE.")

# Validar columna sin NAs (donde aplique)
.check_col_not_all_na <- function(vec, nombre) {
  if (all(is.na(vec))) stop(sprintf("La columna '%s' no contiene valores válidos (solo NA).", nombre))
}
```

**Patrón de codificación Plotly (idéntico en los 7 wrappers):**

```r
html_plotly <- tryCatch({
  fig_json <- iconv(
    jsonlite::toJSON(list(data = traces, layout = layout),
                     auto_unbox = TRUE, na = "null"),
    from = "UTF-8", to = "UTF-8", sub = "byte"
  )
  paste0('<html><body><neven-plotly>',
         jsonlite::base64_enc(chartr("\n\r", "  ", fig_json)),
         '</neven-plotly></body></html>')
}, error = function(e) {
  paste0('<html><body><p style="color:#888;padding:8px">',
         'Gráfico no disponible: ', conditionMessage(e),
         '</p></body></html>')
})

return(r_object_to_slots(
  list(grafico = html_plotly),
  tier_map = c(grafico = 1L)
))
```

**Tema oscuro estándar (constante en todos los wrappers):**

```r
.GR_LAYOUT_BASE <- list(
  paper_bgcolor = "#373434",
  plot_bgcolor  = "#373434",
  font          = list(color = "#888"),
  xaxis         = list(color = "#888", gridcolor = "#333", zerolinecolor = "#555"),
  yaxis         = list(color = "#888", gridcolor = "#333", zerolinecolor = "#555"),
  legend        = list(font = list(color = "#888")),
  margin        = list(t = 50, r = 30, b = 60, l = 60)
)
```

### 3.2 Sidecars JSON (Sidecar_GR)

Estructura común a todos los sidecars GR:

```json
{
  "id":           "GR_{Nombre}",
  "family":       "GR",
  "family_label": "Gráficos",
  "name":         "Nombre visible en Data Lab",
  "description":  "Descripción de una línea.",
  "wikipedia_url": "https://es.wikipedia.org/wiki/...",
  "languages":    ["r"],
  "function_name": "GR_{Nombre}.Studio",
  "file":          "GR_{Nombre}.Studio.R",
  "variable_roles": { /* roles específicos del gráfico */ },
  "parameters":   [ /* parámetros específicos */ ]
}
```

### 3.3 Infraestructura existente (sin cambios)

| Componente | Función en GR | Cambios |
|---|---|---|
| `GET /api/datalab/catalog` | Descubre sidecars GR automáticamente | Ninguno |
| `POST /api/datalab/run` | Ejecuta wrappers GR | Ninguno |
| `datalab_handler.py` | Enruta ejecución a ControlR | Ninguno |
| `r_object_to_slots.R` | Serializa `list(grafico=html)` a slot | Ninguno |
| `<neven-plotly>` WebComponent | Renderiza JSON Plotly base64 | Ninguno |
| `<iframe srcdoc>` rendering | Aísla el HTML del gráfico | Ninguno |

---

## Data Models

### 4.1 Inventario de archivos GR

| Archivo | Directorio | Descripción |
|---|---|---|
| `GR_Scatter.Studio.R` | `NEVEN/libreria/R/` | Scatter plot (X numérico, Y numérico) |
| `GR_Scatter.json` | `NEVEN/Install/functions/` | Sidecar del scatter |
| `GR_Barras.Studio.R` | `NEVEN/libreria/R/` | Bar chart horizontal/vertical |
| `GR_Barras.json` | `NEVEN/Install/functions/` | Sidecar de barras |
| `GR_Lineas.Studio.R` | `NEVEN/libreria/R/` | Line chart con series |
| `GR_Lineas.json` | `NEVEN/Install/functions/` | Sidecar de líneas |
| `GR_Histograma.Studio.R` | `NEVEN/libreria/R/` | Histograma univariado |
| `GR_Histograma.json` | `NEVEN/Install/functions/` | Sidecar del histograma |
| `GR_BoxPlot.Studio.R` | `NEVEN/libreria/R/` | Box plot por grupos |
| `GR_BoxPlot.json` | `NEVEN/Install/functions/` | Sidecar del boxplot |
| `GR_Correlaciones.Studio.R` | `NEVEN/libreria/R/` | Heatmap de correlaciones |
| `GR_Correlaciones.json` | `NEVEN/Install/functions/` | Sidecar del heatmap |
| `GR_SeriesTiempo.Studio.R` | `NEVEN/libreria/R/` | Serie temporal con tendencia |
| `GR_SeriesTiempo.json` | `NEVEN/Install/functions/` | Sidecar de series de tiempo |
| `GR_EjemploPersonalizado.Studio.R` | `NEVEN/Install/functions/` | Plantilla para usuarios |
| `GR_EjemploPersonalizado.json` | `NEVEN/Install/functions/` | Sidecar plantilla |

### 4.2 Roles de variable por tipo de gráfico

| Función | X | Y | Color | Tamaño | Texto |
|---|---|---|---|---|---|
| GR_Scatter | numeric, req | numeric, req | numeric/text, opt | numeric, opt | text, opt |
| GR_Barras | text/numeric, req | numeric, req | text, opt | — | — |
| GR_Lineas | numeric/text, req | numeric, req | text, opt | — | — |
| GR_Histograma | numeric, req | — | — | — | — |
| GR_BoxPlot | text, req | numeric, req | text, opt | — | — |
| GR_Correlaciones | numeric, multi, req≥2 | — | — | — | — |
| GR_SeriesTiempo | text/numeric, req | numeric, req | text, opt | — | — |

### 4.3 Parámetros comunes y específicos

**Parámetros tier 1 comunes (todos los gráficos):**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `Titulo` | text | `""` | Título del gráfico |
| `MostrarLeyenda` | boolean | `true` | Mostrar leyenda en el gráfico |

**Parámetros tier 2 comunes:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `Paleta` | select | `1` | Paleta de colores: 1=NEVEN, 2=Viridis, 3=Plasma, 4=Set1, 5=Pastel |
| `AnchoLinea` | integer | `2` | Ancho de línea (solo Líneas, SeriesTiempo) |
| `Opacidad` | integer | `80` | Opacidad de relleno 0-100 |

**Parámetros específicos:**

| Función | Parámetro | Tipo | Default | Tier |
|---|---|---|---|---|
| GR_Barras | `Orientacion` | select | 1 (Vertical) | 1 |
| GR_Histograma | `Bins` | integer | 30 | 1 |
| GR_Histograma | `MostrarDensidad` | boolean | false | 2 |
| GR_BoxPlot | `MostrarPuntos` | boolean | false | 2 |
| GR_Correlaciones | `Metodo` | select | 1 (Pearson) | 1 |
| GR_Correlaciones | `MostrarValores` | boolean | true | 1 |
| GR_SeriesTiempo | `MostrarTendencia` | boolean | false | 1 |
| GR_SeriesTiempo | `TipoTendencia` | select | 1 (Lineal) | 2 |

### 4.4 Estructura del slot de salida

Todos los Wrapper_GR retornan exactamente esta estructura de slots:

```json
[
  {
    "name":  "grafico",
    "label": "Gráfico",
    "type":  "html",
    "value": "<html><body><neven-plotly>BASE64_JSON_PLOTLY</neven-plotly></body></html>",
    "tier":  1
  }
]
```

El JSON Plotly decodificado del BASE64 tiene siempre la estructura:

```json
{
  "data":   [ /* array de traces Plotly */ ],
  "layout": {
    "paper_bgcolor": "#373434",
    "plot_bgcolor":  "#373434",
    "font": { "color": "#888" },
    "title": { "text": "...", "font": { "color": "#e0e0e0" } }
  }
}
```

---

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe cumplirse en todas las ejecuciones válidas del sistema — esencialmente, una afirmación formal sobre lo que el sistema debe hacer. Las propiedades sirven de puente entre las especificaciones legibles por humanos y las garantías de correctitud verificables automáticamente.*

### Property 1: Slot de salida único tipo html con patrón neven-plotly

*Para cualquier* Wrapper_GR de la familia GR y *para cualquier* `data.frame` de entrada con valores válidos (sin filas vacías, tipos correctos), al llamar al wrapper se debe retornar exactamente una lista con un slot cuyo `type` sea `"html"` y cuyo `value` contenga la subcadena `"<neven-plotly>"`.

**Validates: Requirements 4.2, 6.2**

### Property 2: JSON Plotly válido en el slot de salida (round-trip base64)

*Para cualquier* Wrapper_GR y *para cualquier* `data.frame` de entrada válido, el valor del slot html contiene un bloque `<neven-plotly>BASE64</neven-plotly>` cuyo BASE64 decodificado es un JSON con los campos `"data"` (array) y `"layout"` (objeto) bien formados.

**Validates: Requirements 6.3, 4.2**

### Property 3: Tema oscuro preservado en todo gráfico generado

*Para cualquier* Wrapper_GR y *para cualquier* `data.frame` de entrada válido, el JSON Plotly decodificado del slot de salida contiene `layout.paper_bgcolor = "#373434"`, `layout.plot_bgcolor = "#373434"` y `layout.font.color = "#888"`.

**Validates: Requirements 6.4**

### Property 4: Validación de input — rechazo de entradas inválidas

*Para cualquier* Wrapper_GR, *si* `data_X` no es un `data.frame` o es un `data.frame` vacío (0 filas), *entonces* la llamada al wrapper debe lanzar un error con `stop()` cuyo mensaje es una cadena no vacía en español.

**Validates: Requirements 6.5, 9.2**

### Property 5: Columnas todo-NA rechazadas con mensaje descriptivo

*Para cualquier* Wrapper_GR que use vectores numéricos del rol X o Y, *si* todas las filas de la columna asignada son `NA`, *entonces* el wrapper debe lanzar `stop()` con un mensaje que contiene el nombre de la columna afectada.

**Validates: Requirements 9.1**

### Property 6: Filtrado correcto de columnas por tipo en Column_Panel

*Para cualquier* catálogo de función GR con roles de tipo `["numeric"]`, `["text"]` o `["numeric","text"]`, y *para cualquier* dataset con mezcla de tipos de columna, el conjunto de columnas asignables a un rol debe ser exactamente el subconjunto de columnas cuyo tipo DuckDB es compatible con los tipos declarados en el rol.

**Validates: Requirements 2.4, 2.5, 2.6**

### Property 7: Formulario de parámetros refleja exactamente el sidecar (round-trip default→control)

*Para cualquier* Sidecar_GR con N parámetros, el Parameter_Form renderizado debe contener exactamente N controles cuyos valores iniciales son iguales a los valores `default` declarados en el sidecar.

**Validates: Requirements 3.1, 3.3**

### Property 8: Catálogo incluye todos los sidecars GR válidos

*Para cualquier* directorio con N sidecars GR válidos (campos requeridos presentes, JSON bien formado), el endpoint `GET /api/datalab/catalog` debe retornar exactamente N entradas con `family = "GR"`.

**Validates: Requirements 1.1, 1.5**

### Property 9: Validación de roles requeridos — detección de todos los vacíos

*Para cualquier* función GR con M roles `required: true` y *si* K de esos roles (K ≥ 1) no tienen columna asignada, *entonces* la validación del formulario debe detectar e informar exactamente K roles vacíos antes de enviar la solicitud.

**Validates: Requirements 2.2**

### Property 10: Error en construcción Plotly produce HTML de error — no excepción propagada

*Para cualquier* Wrapper_GR y *para cualquier* fallo interno en la construcción del gráfico Plotly (dentro del bloque `tryCatch`), el wrapper debe retornar un slot de tipo `html` válido cuyo `value` contiene el mensaje de error incrustado en HTML — la excepción no debe propagarse al llamador.

**Validates: Requirements 9.4**

---

## Error Handling

### Errores de validación en wrapper (antes de construir el gráfico)

Todos los errores de validación usan `stop()` con mensajes en español. El `datalab_handler.py` captura estos errores y retorna `{"status": "error", "message": "..."}`.

| Condición | Mensaje |
|---|---|
| `data_X` no es data.frame | `"'data_X' debe ser un data.frame."` |
| `data_X` tiene 0 filas | `"El filtro aplicado no retorna filas. Verifique la cláusula WHERE."` |
| Columna todo-NA | `"La columna '{nombre}' no contiene valores válidos (solo NA)."` |
| GR_Correlaciones < 2 cols | `"Se requieren al menos 2 columnas numéricas para el mapa de correlaciones."` |
| Columna no numérica en rol numérico | `"La columna '{nombre}' no es numérica. Asigne una columna de tipo numérico al rol {rol}."` |

### Errores en construcción Plotly (tryCatch)

Cualquier error dentro del bloque de construcción del gráfico produce el slot HTML de error:

```r
paste0('<html><body><p style="color:#888;padding:8px">',
       'Gráfico no disponible: ', conditionMessage(e),
       '</p></body></html>')
```

Esto garantiza que el Results_Panel siempre recibe un slot HTML renderizable.

### Errores de infraestructura (Data Lab UI)

| Condición | Comportamiento UI |
|---|---|
| ControlR no disponible | Mensaje en Results_Panel: "Motor R no disponible. Verifique que NEVEN esté iniciado correctamente." |
| Catálogo no accesible | Mensaje en interfaz + botón Reintentar |
| Rol requerido sin asignar | Mensaje de validación en español junto al rol vacío |

---

## Testing Strategy

### Enfoque dual: pruebas unitarias + pruebas de propiedad

Las funciones GR son funciones R puras (dado un data.frame, retornan una lista de slots) — el dominio de entrada varía significativamente (distintos tipos de datos, columnas, tamaños). Esto hace que las pruebas basadas en propiedades sean apropiadas para validar correctitud general.

**Librería de pruebas de propiedad:** `quickcheck` (CRAN) para R — permite generar data.frames aleatorios y verificar propiedades universales con mínimo 100 iteraciones por propiedad.

**Librería de pruebas unitarias:** `testthat` (CRAN) para casos específicos y casos borde.

### Pruebas de propiedad (property-based tests)

Cada propiedad de la sección anterior debe implementarse como un test `quickcheck`:

```r
# Tag: Feature: neven-datalab-gr-family, Property 1: Slot de salida único tipo html
test_that("GR_Scatter retorna exactamente 1 slot html con neven-plotly", {
  qc_property(
    forall(
      df = gen_numeric_df(min_rows = 3, min_cols = 2),
      function(df) {
        result <- GR_Scatter.Studio(data_X = df[, 1, drop=FALSE],
                                     data_Y = df[, 2, drop=FALSE])
        slots  <- r_object_to_slots(result)  # ya aplicado en el wrapper
        # El wrapper retorna directamente la lista de slots
        expect_length(result, 1)
        expect_equal(result[[1]]$type,  "html")
        expect_true(grepl("<neven-plotly>", result[[1]]$value, fixed = TRUE))
      }
    ),
    tests = 100
  )
})
```

Cada propiedad se configura con mínimo **100 iteraciones**. La anotación de tag se incluye como comentario sobre el test.

### Pruebas unitarias (example-based tests)

Casos específicos no cubiertos por las propiedades:

- **GR_Correlaciones con < 2 columnas** → verifica mensaje de error exacto (Req. 9.3)
- **GR_SeriesTiempo con MostrarTendencia=TRUE** → verifica que se incluye traza de tendencia
- **Slot html con tier=1** → verifica que el Results_Panel usa `<iframe srcdoc>`
- **Parámetro tier=2** → verifica que aparece en sección colapsable
- **Rol `required=false` no asignado** → verifica que la ejecución procede sin error
- **Catálogo vacío (sin sidecars GR)** → verifica que la familia no aparece en el selector

### Pruebas de integración (smoke tests)

Para la correctitud de archivos de configuración:

- Verificar existencia de los 7 sidecars GR en `NEVEN/Install/functions/`
- Verificar que cada sidecar tiene todos los campos requeridos del esquema
- Verificar que cada wrapper `.Studio.R` define la función con el nombre correcto
- Verificar que los archivos de la plantilla de extensibilidad existen y son funcionales

### Cobertura de requisitos

| Requisito | Tipo de prueba | Propiedad/Test |
|---|---|---|
| Req 1.1, 1.5 | Property | Propiedad 8 |
| Req 2.2 | Property | Propiedad 9 |
| Req 2.4, 2.5, 2.6 | Property | Propiedad 6 |
| Req 3.1, 3.3 | Property | Propiedad 7 |
| Req 4.2, 6.2 | Property | Propiedad 1 |
| Req 6.3 | Property | Propiedad 2 |
| Req 6.4 | Property | Propiedad 3 |
| Req 6.5, 9.2 | Property | Propiedad 4 |
| Req 9.1 | Property | Propiedad 5 |
| Req 9.4 | Property | Propiedad 10 |
| Req 9.3 | Example | test unitario GR_Correlaciones |
| Req 5.1–5.7 | Smoke | verificación de catálogo |
| Req 10.1–10.5 | Smoke | verificación de archivos |
