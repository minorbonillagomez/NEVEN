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


---

## Aliases — Nombres cortos para funciones (opcional)

NEVEN permite definir **aliases** para que los usuarios puedan llamar funciones con nombres más cortos.
Por ejemplo: `=NEVEN.R("ACP", ...)` en lugar de `=NEVEN.R("AD_ACP.C", ...)`.

### ¿Cuándo agregar un alias?

- Cuando el nombre completo es largo o redundante (ej: `AD_ClusteringJerarquico.C`)
- Cuando hay nombres alternativos comunes (ej: `PCA` y `ACP` son lo mismo)
- Cuando el usuario lo solicita explícitamente

### Pasos para agregar un alias

**Se deben modificar DOS archivos:**

#### 1. Dispatcher R (`C:\NEVEN\functions\R4XCL-0-NevenX.R`)

Buscar la tabla `.neven_aliases` (alrededor de la línea 205) y agregar la entrada:

```r
.neven_aliases <- list(
    # ... aliases existentes ...
    
    # --- Tu nuevo alias ---
    "MiAlias"       = "MR_MiFuncion",      # alias -> nombre real
    "OtroAlias"     = "MR_MiFuncion",      # puedes tener múltiples aliases
    
    # ... más aliases ...
)
```

**Reglas:**
- La **clave** es el alias (nombre corto que usará el usuario)
- El **valor** es el nombre EXACTO de la función en R (debe existir en `globalenv()`)
- Los aliases son **case-insensitive** (el usuario puede escribir `acp`, `ACP`, `Acp`)
- Un alias solo puede apuntar a UNA función
- Una función puede tener MÚLTIPLES aliases

#### 2. Servidor HTTP (`C:\NEVEN\startup\neven_http_server.py`)

Buscar el diccionario `_function_aliases` (alrededor de la línea 1942) y agregar:

```python
_function_aliases = {
    # ... aliases existentes ...
    
    # --- Tu nuevo alias ---
    "MR_MiFuncion": ["MiAlias", "OtroAlias"],  # función -> lista de aliases
    
    # ... más aliases ...
}
```

**Nota:** Aquí el formato es **inverso** al de R:
- La **clave** es el nombre real de la función (`function_name_xll` del sidecar)
- El **valor** es una **lista** de aliases

Este diccionario se usa para mostrar los aliases en el **Tab Ayuda** del TaskPane.

### Ejemplo completo: agregar alias "Regresion" para MR_Lineal

**En R (`R4XCL-0-NevenX.R`):**
```r
.neven_aliases <- list(
    # ...
    "Lineal"        = "MR_Lineal",
    "LM"            = "MR_Lineal",
    "OLS"           = "MR_Lineal",
    "Regresion"     = "MR_Lineal",   # ← NUEVO
    # ...
)
```

**En Python (`neven_http_server.py`):**
```python
_function_aliases = {
    # ...
    "MR_Lineal": ["Lineal", "LM", "OLS", "Regresion"],  # ← agregar "Regresion"
    # ...
}
```

### Después de agregar aliases

1. **Reiniciar el servidor HTTP:** El TaskPane carga los aliases al iniciar
2. **Reiniciar Excel:** R carga el dispatcher al abrir Excel
3. **Verificar en Tab Ayuda:** La función debe mostrar los aliases (→ Alias1, Alias2)
4. **Probar en Excel:** `=NEVEN.R("MiAlias", datos)` debe funcionar

### Archivos a copiar al repositorio

| Producción | Repositorio |
|------------|-------------|
| `C:\NEVEN\functions\R4XCL-0-NevenX.R` | `NEVEN\libreria\R\R4XCL-0-NevenX.R` |
| `C:\NEVEN\startup\neven_http_server.py` | `NEVEN\TaskPane\neven_http_server.py` |

**Comando para copiar:**
```powershell
[System.IO.File]::Copy("C:\NEVEN\functions\R4XCL-0-NevenX.R", "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\libreria\R\R4XCL-0-NevenX.R", $true)
[System.IO.File]::Copy("C:\NEVEN\startup\neven_http_server.py", "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\TaskPane\neven_http_server.py", $true)
```

### Aliases existentes (referencia rápida)

| Alias | Función Real | Categoría |
|-------|--------------|-----------|
| ACP, PCA | AD_ACP.C | Análisis de Datos |
| KMeans, KMedias | AD_KMedias.C | Análisis de Datos |
| Clustering, HClust | AD_ClusteringJerarquico.C | Análisis de Datos |
| Lineal, LM, OLS | MR_Lineal | Regresión |
| Logistica, Logit | MR_Binario.C | Regresión |
| Panel, PanelData | MR_PanelData.C | Regresión |
| VAR, VectorAR | ST_VAR | Series de Tiempo |
| ECM, Cointegracion | ST_ECM | Series de Tiempo |
| TextMining, NLP, Texto | TM_TextMining | Text Mining |
