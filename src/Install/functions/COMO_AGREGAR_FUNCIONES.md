# Cómo agregar tus propias funciones a NEVEN Data Lab

## Concepto

Cualquier función analítica que quieras exponer en Data Lab necesita solo **dos archivos**:

1. **`MiFuncion.Studio.R`** — el código R que ejecuta el análisis
2. **`MiFuncion.json`** — el sidecar que describe la interfaz (inputs, parámetros)

Copia ambos a `C:\NEVEN\functions\` y reinicia NEVEN Studio. Tu función aparece
automáticamente en la familia que hayas indicado en el sidecar.

---

## Estructura del wrapper R

```r
# El nombre de la función DEBE terminar en .Studio
MiFuncion.Studio <- function(data_X,          # columnas asignadas al rol X
                               data_Y = NULL,  # columnas asignadas al rol Y (opcional)
                               Param1 = 3L,    # parámetros definidos en el sidecar
                               Param2 = TRUE) {

  # 1. Validaciones básicas
  if (!is.data.frame(data_X)) stop("'data_X' debe ser un data.frame.")

  # 2. Tu análisis aquí
  resultado_tabla <- data.frame(...)
  resultado_html  <- '<html>...<neven-plotly>BASE64</neven-plotly>...</html>'

  # 3. SIEMPRE retornar r_object_to_slots()
  resultado <- list(
    mi_tabla   = resultado_tabla,   # tipo table
    mi_grafico = resultado_html,    # tipo html (con neven-plotly)
    mi_escalar = 42.5               # tipo scalar
  )
  tier_map <- c(mi_tabla = 1L, mi_grafico = 1L, mi_escalar = 2L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
```

**Reglas importantes:**
- `tier = 1` → se muestra expandido por defecto
- `tier = 2` → se muestra en la sección "Detalles técnicos" (colapsada)
- Los gráficos deben usar el formato `<neven-plotly>BASE64</neven-plotly>`
- El nombre del archivo y de la función deben coincidir exactamente

---

## Estructura del sidecar JSON

```json
{
  "id": "MiFuncion",
  "family": "UC",
  "family_label": "Mis Funciones",
  "name": "Nombre visible en Data Lab",
  "description": "Descripción que aparece al seleccionar la función.",
  "wikipedia_url": "https://es.wikipedia.org/wiki/...",
  "languages": ["r"],
  "function_name": "MiFuncion.Studio",
  "file": "MiFuncion.Studio.R",
  "variable_roles": {
    "X": {
      "label": "Variables de entrada",
      "types": ["numeric"],
      "multiple": true,
      "required": true
    }
  },
  "parameters": [
    {
      "name": "NombreParam",
      "label": "Etiqueta visible",
      "type": "integer",
      "default": 3,
      "tier": 1
    }
  ]
}
```

**Tipos de parámetro disponibles:**
| type      | Control UI           | Ejemplo default |
|-----------|---------------------|-----------------|
| `integer` | Spinner numérico     | `3`             |
| `boolean` | Checkbox             | `true`/`false`  |
| `select`  | Dropdown con options | `1`             |

**Tipos de roles disponibles:**
| types       | Filtra columnas...                    |
|-------------|---------------------------------------|
| `["numeric"]` | Solo numéricas                      |
| `["text"]`    | Solo texto/categorías                |
| `["numeric","text"]` | Cualquier tipo              |

---

## Familias predefinidas

| family | family_label         | Uso recomendado          |
|--------|---------------------|--------------------------|
| `AD`   | Análisis de Datos   | Clustering, reducción dim |
| `RG`   | Regresión           | Modelos predictivos       |
| `ST`   | Series de Tiempo    | Series temporales, panel  |
| `DS`   | Conjuntos de Datos  | Cargadores de datasets    |
| `UC`   | Mis Funciones       | **Tus funciones propias** |
| Otro   | Lo que definas      | Crea tu propia familia    |

---

## Archivos de ejemplo incluidos

| Archivo | Qué muestra |
|---------|-------------|
| `UC_EjemploBasico.Studio.R` | Patrón mínimo — estadísticas descriptivas |
| `UC_EjemploBasico.json`     | Sidecar con un solo rol X y un parámetro  |
| `UC_EjemploAvanzado.Studio.R` | Patrón completo — roles Y~X, gráfico plotly, select |
| `UC_EjemploAvanzado.json`     | Sidecar con dos roles y tres parámetros   |

---

## Gráficos con Plotly

Para incluir un gráfico interactivo, usa este patrón en tu wrapper R:

```r
html_grafico <- tryCatch({
  # Construir el spec JSON de plotly
  traces <- list(list(
    type = "scatter", mode = "markers",
    x = mi_x, y = mi_y,
    marker = list(color = "#d7a538", size = 8)
  ))
  layout <- list(
    title = list(text = "Mi Grafico", font = list(color = "#e0e0e0")),
    paper_bgcolor = "#373434", plot_bgcolor = "#373434",
    font = list(color = "#888")
  )
  fig_json <- iconv(
    jsonlite::toJSON(list(data = traces, layout = layout),
                     auto_unbox = TRUE, na = "null"),
    from = "UTF-8", to = "UTF-8", sub = "byte"
  )
  paste0('<html><body><neven-plotly>',
         jsonlite::base64_enc(chartr("\n\r", "  ", fig_json)),
         '</neven-plotly></body></html>')
}, error = function(e) {
  paste0('<html><body><p>Grafico no disponible: ', conditionMessage(e), '</p></body></html>')
})
```

---

## Soporte multi-lenguaje (próximamente)

El sistema está preparado para funciones en Python (`.Studio.py`) y Julia (`.Studio.jl`).
El campo `"languages": ["r", "python"]` en el sidecar activará el selector de idioma.