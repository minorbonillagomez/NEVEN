---
id: python-ejemplos
title: Capitulo 16 -- Python en NEVEN
sidebar_label: 16. Python
sidebar_position: 16
---

# Capitulo 16: Python en NEVEN

Python es el tercer motor de scripting de NEVEN, integrado via **Stable ABI** (`python3.dll`), lo que garantiza compatibilidad con cualquier version 3.10+. Ofrece acceso a todo el ecosistema de Data Science: numpy, pandas, matplotlib, scikit-learn, y mas.

---

## 16.0 Formas de usar Python en NEVEN

| Modo | Descripcion | Cuando usar |
|:---|:---|:---|
| `=NEVEN.py("codigo")` | Ejecutar Python desde celda Excel | Calculos rapidos, funciones matematicas |
| `=NEVEN.p("funcion", args)` | Llamar funcion Python registrada | Funciones de la libreria Py. |
| **NEVEN Studio / Run Script** | Editor de scripts con salida interactiva | Scripts de mas de una linea |
| **NEVEN Studio / Data Lab** | Analisis estadistico sin codigo | Wrappers Studio de Python |

---

## 16.1 Ejecucion directa desde Excel

### `=NEVEN.py()` -- Codigo Python en celda

Ejecuta cualquier expresion Python y retorna el resultado a la celda.

**Ejemplos basicos:**

| Formula | Resultado |
|:---|:---|
| `=NEVEN.py("2 ** 10")` | 1024 |
| `=NEVEN.py("import math; math.pi")` | 3.14159... |
| `=NEVEN.py("sum(range(1, 101))")` | 5050 |
| `=NEVEN.py("len('NEVEN')")` | 5 |
| `=NEVEN.py("' '.join(['R','Julia','Python'])")` | R Julia Python |

**Con datos de Excel:**

Para pasar rangos de Excel a Python, use `=NEVEN.p()` con funciones registradas (ver seccion 16.2). Para calculos simples, use constantes directamente:

```
=NEVEN.py("import numpy as np; np.sqrt(2)")        → 1.41421
=NEVEN.py("import numpy as np; np.log(np.e)")      → 1.0
=NEVEN.py("import datetime; datetime.date.today()") → fecha actual
```

### `=NEVEN.p()` -- Funciones de la libreria Python

Llama a funciones Python registradas, pasando rangos de Excel como argumentos.

**Firma:** `=NEVEN.p("nombre_funcion", arg1, arg2, ...)`

---

## 16.2 Graficos con matplotlib -- `=NEVEN.chart.p()`

Genera graficos como imagenes incrustadas en la hoja de Excel usando matplotlib.

**Firma:** `=NEVEN.chart.p(rango_datos, tipo_grafico, nombre, ancho, alto)`

| tipo_grafico | Grafico |
|:---:|:---|
| 1 | Lineas |
| 2 | Barras |
| 3 | Scatter |
| 4 | Histograma |
| 5 | Pie |
| 6 | BoxPlot |
| 7 | Heatmap |

**Ejemplos:**

```excel
=NEVEN.chart.p(A1:B10, 3, "Scatter", 600, 400)
=NEVEN.chart.p(A1:A20, 4, "Histograma", 500, 350)
=NEVEN.chart.p(A1:C5, 2, "Barras", 600, 400)
```

> El grafico se incrusta directamente en la hoja como una imagen Shape, sin abrir ventanas externas.

---

## 16.3 IA y LLM -- Funciones `Py.ai_*`

Integracion con modelos de lenguaje via la libreria `ai_functions.py`.

### `Py.ai_call` -- Llamar al modelo configurado

**Firma:** `=NEVEN.p("ai_call", prompt)`

```excel
=NEVEN.p("ai_call", "Explica la regresion lineal en 2 lineas")
=NEVEN.p("ai_call", "Traduce a ingles: " & A1)
=NEVEN.p("ai_call", "Resume el siguiente texto: " & A1)
```

> Requiere un modelo configurado en NEVEN Studio (tab IA > Configuracion).

### `Py.ai_apply_template` -- Plantillas de prompts

Aplica una plantilla predefinida al texto de entrada.

**Firma:** `=NEVEN.p("ai_apply_template", nombre_plantilla, texto)`

| Plantilla | Descripcion |
|:---|:---|
| `explain` | Explica el concepto o codigo |
| `generate` | Genera codigo Python |
| `review` | Revisa codigo buscando bugs |
| `document` | Genera documentacion |
| `summarize` | Resume texto |
| `translate` | Traduce entre lenguajes |

**Ejemplos:**

```excel
=NEVEN.p("ai_apply_template", "explain", A1)
=NEVEN.p("ai_apply_template", "summarize", A1)
=NEVEN.p("ai_apply_template", "review", A1)
```

### `Py.ai_get_config` -- Estado de la configuracion IA

```excel
=NEVEN.p("ai_get_config")
```

Retorna: modelo activo, si esta configurado, plantillas disponibles.

---

## 16.4 Quarto -- Funciones `Py.quarto_*`

Renderizado de documentos `.qmd` desde Excel via Python.

### `Py.quarto_render` -- Renderizar documento

**Firma:** `=NEVEN.p("quarto_render", ruta_qmd, formato)`

| Formato | Resultado |
|:---|:---|
| `"html"` | Pagina HTML interactiva |
| `"pdf"` | PDF (requiere LaTeX) |
| `"docx"` | Documento Word |
| `"revealjs"` | Presentacion HTML |

**Ejemplos:**

```excel
=NEVEN.p("quarto_render", "C:\NEVEN\docs\reporte.qmd", "html")
=NEVEN.p("quarto_render", "C:\NEVEN\docs\reporte.qmd", "docx")
```

### `Py.quarto_check` -- Verificar instalacion

```excel
=NEVEN.p("quarto_check")
```

Retorna version de Quarto instalada.

### `Py.quarto_preview` -- Vista previa en navegador

```excel
=NEVEN.p("quarto_preview", "C:\NEVEN\docs\reporte.qmd")
```

Inicia servidor de preview en `http://localhost:4200`.

---

## 16.5 NEVEN Studio con Python

### Run Script (Python)

El tab **Run Script** de NEVEN Studio permite ejecutar scripts Python multi-linea con salida interactiva.

Ejemplo de script:

```python
import numpy as np
import pandas as pd

# Cargar datos desde DuckDB
data = query("SELECT * FROM dataset")

# Analisis
media = np.mean(data['valor'])
desv  = np.std(data['valor'])

print(f"Media: {media:.2f}")
print(f"Desviacion: {desv:.2f}")
```

La salida aparece en el panel inferior. Graficos generados con matplotlib se muestran automaticamente en el visor WebView2.

### Data Lab (wrappers Python)

Algunas funciones del Data Lab tienen implementacion en Python ademas de R:

| Funcion | Archivo | Motor |
|:---|:---|:---|
| Text Mining | `TM_TextAnalysis.Studio.py` | Python |
| Mis Funciones (basica) | `UC_EjemploBasico.Studio.py` | Python |
| Mis Funciones (avanzada) | `UC_EjemploAvanzado.Studio.py` | Python |

---

## 16.6 Gestion de paquetes

### Instalar paquetes desde Excel

```excel
=NEVEN.py("import subprocess; subprocess.run(['pip','install','seaborn'])")
```

### Verificar paquete disponible

```excel
=NEVEN.py("import importlib; importlib.util.find_spec('seaborn') is not None")
```

### Paquetes preinstalados con NEVEN

Los siguientes paquetes se instalan automaticamente con NEVEN:

| Paquete | Uso |
|:---|:---|
| `numpy` | Algebra lineal, arrays numericos |
| `pandas` | Manipulacion de datos tabulares |
| `matplotlib` | Graficos estaticos |
| `scikit-learn` | Machine learning |
| `duckdb` | Base de datos vectorial y SQL |
| `fastembed` | Embeddings locales para RAG |
| `pyyaml` | Parsing de ontologias YAML |
| `markitdown[pdf,docx,xlsx,pptx,xls]` | Extraccion de documentos |
| `ebooklib` | Soporte EPUB |
| `openai` | API OpenAI / LMStudio |
| `httpx` | HTTP async para llamadas IA |

---

## 16.7 Configuracion

Python se configura en `neven-config.json`:

```json
{
  "NEVEN": {
    "Python": {
      "home": "C:/Users/Usuario/AppData/Local/Programs/Python/Python312",
      "enabled": true,
      "minMajor": 3,
      "minMinor": 10,
      "maxMajor": 99
    }
  }
}
```

> NEVEN detecta Python automaticamente en el PATH del sistema. Solo es necesario especificar `home` si tiene multiples versiones instaladas.

---

## 16.8 Diferencias respecto a R y Julia

| Aspecto | R | Julia | Python |
|:---|:---:|:---:|:---:|
| Funciones estadisticas | Si (primario) | Si | Limitado |
| Machine Learning | Si | Si | Si (sklearn) |
| Graficos desde Excel | Si (Plotly/ggplot) | No | Si (matplotlib) |
| Integracion IA | No | No | Si (ai_functions) |
| Quarto nativo | Si | Si | Si |
| Startup rapido | Si | Si (sysimage) | Si |
| Data Lab wrappers | 18 funciones | 2 funciones | 3 funciones |
