---
id: inicio-rapido
title: Guía de Inicio Rápido
sidebar_label: Inicio Rápido
sidebar_position: 3
---

# NEVEN v3.2 — Guía de Inicio Rápido

**Versión:** 3.2 | **Plataforma:** Windows 10/11 (64-bit) | **Excel:** 2016, 2019 o Microsoft 365

---

## 1. Instalación

### Requisitos previos

| Componente | Requerido | Versión mínima | Descarga |
|:---|:---|:---|:---|
| Microsoft Excel | Sí (64-bit) | 2016+ | Ya instalado |
| R | Sí | 4.4.1+ | https://cran.r-project.org |
| Python | Sí | 3.10+ | https://python.org |
| Julia | Opcional | 1.12.6+ | https://julialang.org |
| Quarto | Opcional | 1.9.18+ | https://quarto.org |

:::note
Python es requerido para NEVEN Studio (TaskPane). Julia y Quarto son opcionales.
:::

### Instalación automatizada (recomendado)

1. Descarga y extrae `NEVEN-v3.2-Setup.zip`
2. Ejecuta PowerShell como Administrador
3. Navega a la carpeta extraída y ejecuta:

```powershell
.\Install-NEVEN.ps1
```

El instalador:
- Copia archivos a `C:\NEVEN\`
- Instala dependencias Python (DuckDB, FastEmbed, MarkItDown, etc.)
- Registra el Ribbon COM
- Configura el XLL en Excel

---

## 2. Verificación rápida

Al abrir Excel debería aparecer la pestaña **NEVEN** en la cinta de opciones.

### Prueba las fórmulas base

```excel
=NEVEN.R("1+1")        → 2
=NEVEN.J("sqrt(144)")  → 12  (si Julia está instalada)
=NEVEN.P("1+1")        → 2
=NEVEN.about()         → Información del proyecto
```

### Abre NEVEN Studio

Haz clic en el botón **NEVEN Studio** del Ribbon o presiona `Ctrl+Shift+N`. Se abre un panel lateral con 7 pestañas:

| Tab | Función |
|-----|---------|
| **SQL** | Consultas DuckDB sobre datos de Excel |
| **Data Studio** | Análisis exploratorio con gráficos |
| **Run Script** | REPL para R, Python y Julia |
| **Data Lab** | Notebooks interactivos |
| **Presentaciones** | Crear slides con Quarto/Impress.js |
| **IA** | Chat con RAG (300+ entidades de conocimiento) |
| **Ayuda** | Documentación integrada (16 capítulos) |

---

## 3. Tu primera fórmula R

NEVEN expone 200+ funciones de R como fórmulas de Excel.

### Ejemplo: Regresión lineal

Con datos en Excel:
- Columna A (filas 2-11): Variable dependiente (Y)
- Columna B (filas 2-11): Variable independiente (X)

```excel
=R.MR_Lineal(A2:A11, B2:B11, 1)
```

El tercer parámetro (`TipoOutput`) controla qué resultado obtener:

| TipoOutput | Resultado |
|:---:|:---|
| 0 | Lista de procedimientos disponibles |
| 1 | Coeficientes del modelo |
| 2 | Resumen completo (R², p-values) |
| 3 | Tabla ANOVA |
| 4 | Residuos |

:::tip
Usa `TipoOutput = 0` en cualquier función para ver qué opciones tiene.
:::

---

## 4. Gráficos interactivos

NEVEN genera gráficos con Plotly, D3.js y Leaflet que se abren en WebView2.

### Dashboard interactivo

Con datos en A1:E11 (con encabezados):

```excel
=NEVEN.v(R.Dashboard(A1:E11, 1))
```

### Otros gráficos

| Fórmula | Resultado |
|:---|:---|
| `=NEVEN.v(R.Pivot(A1:E11, 1))` | Tabla pivote drag-and-drop |
| `=NEVEN.v(R.Esquisse(A1:E11, 1))` | Explorador de datos Plotly |
| `=NEVEN.v(R.D3(A1:E11, 1))` | Treemap D3.js |
| `=NEVEN.v(R.D3(A1:E11, 2))` | Diagrama Sankey |
| `=NEVEN.v(R.Map(A1:D11, 1))` | Mapa Leaflet (requiere lat/lon) |

---

## 5. NEVEN Studio — SQL

Ejecuta consultas SQL sobre datos de Excel usando DuckDB.

### Cargar datos

1. Selecciona un rango en Excel
2. En el tab SQL, haz clic en **Cargar selección**
3. Los datos se cargan como tabla `data`

### Ejecutar consultas

```sql
SELECT * FROM data WHERE columna > 100 ORDER BY otra_columna
```

```sql
SELECT categoria, AVG(ventas) as promedio
FROM data
GROUP BY categoria
HAVING AVG(ventas) > 1000
```

Los resultados se muestran en una tabla interactiva con opción de exportar a CSV.

---

## 6. NEVEN Studio — Chat IA con RAG

El tab **IA** incluye un chat con acceso a 300+ entidades de conocimiento indexadas.

### Cómo funciona

1. Escribe tu pregunta en lenguaje natural
2. El sistema busca contexto relevante en la base de conocimiento (RAG)
3. La IA responde usando ese contexto + tu pregunta

### Ejemplo de preguntas

- "¿Cómo interpreto el R² en una regresión?"
- "¿Qué es la heterocedasticidad y cómo la detecto?"
- "Explica el método de componentes principales"
- "¿Cómo uso la función R.MR_Lineal?"

### Indexar tus propios documentos

En el panel de configuración RAG puedes agregar documentos a la base de conocimiento:

**Formatos soportados:** PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, CSV, JSON, XML, TXT, MD

1. Haz clic en **...** para seleccionar archivo
2. Asigna un dominio (econometría, estadística, excel, etc.)
3. Haz clic en **Indexar**

---

## 7. Funciones Julia (opcional)

Si tienes Julia instalada:

```excel
=NEVEN.j("sqrt(144)")                    → 12
=J.Algebra(A1:C3, 0, 6)                  → Determinante
=J.Estadistica(A1:A20, 0, 1)             → Estadística descriptiva
=J.Optimizar(f, x0, 0, 1)                → Gradiente descendente
```

### Módulos disponibles

| Función | Qué hace |
|:---|:---|
| `J.Algebra` | LU, QR, SVD, eigenvalores, determinante |
| `J.Calculo` | Derivadas, integrales, interpolación |
| `J.Estadistica` | Descriptiva, correlación, t-test |
| `J.KNN` | Clasificación K-Nearest Neighbors |
| `J.Regresion` | Regresión lineal con IC |
| `J.Clustering` | K-Medias con método del codo |
| `J.Optimizar` | Gradiente, Newton, simplex |

:::note
Julia tarda ~5 segundos en cargar gracias a la sysimage precompilada (`neven_julia.dll`).
:::

---

## 8. Funciones Python

Python está completamente integrado (ON por defecto):

```excel
=NEVEN.P("1+1")                          → 2
=NEVEN.P("sum([10,20,30])")              → 60
=NEVEN.P("import math; math.pi")         → 3.14159...
```

Las funciones de usuario Python usan prefijo `P.`:

```excel
=P.MiFuncion(A1, B1)
```

---

## 9. Crear tus propias funciones

### Función R

Crea archivo en `Documentos\NEVEN\functions\mi_funcion.R`:

```r
MiSuma <- function(a, b) a + b

attr(MiSuma, "description") <- list(
  "Suma dos valores",
  a = "Primer valor",
  b = "Segundo valor"
)
attr(MiSuma, "category") <- "Mis Funciones"
```

Usa en Excel: `=R.MiSuma(A1, B1)`

### Función Python

Crea archivo en `Documentos\NEVEN\functions\mi_funcion.py`:

```python
def CalcularIVA(monto, tasa=13.0):
    """Calcula el IVA de un monto.
    
    Args:
        monto: Monto base
        tasa: Porcentaje de IVA (default: 13%)
    """
    return monto * (tasa / 100)
```

Usa en Excel: `=P.CalcularIVA(A1, 13)`

---

## 10. Configuración

El archivo `C:\NEVEN\neven-config.json` controla el comportamiento de NEVEN.

### Secciones principales

```json
{
  "R": { "enabled": true, "home": "" },
  "Julia": { "enabled": true, "home": "" },
  "Python": { "enabled": true },
  "RAG": {
    "enabled": true,
    "minScore": 0.50,
    "topK": 3
  },
  "WebView2": { "maxViewers": 8 },
  "Pluto": { "port": 1234 }
}
```

### Desactivar un lenguaje

Cambia `"enabled": true` a `"enabled": false` en la sección correspondiente.

---

## 11. Solución de problemas rápida

| Problema | Solución |
|:---|:---|
| `#NOMBRE?` en fórmulas | Verificar XLL cargado: Archivo → Opciones → Complementos |
| `#VALOR!` en NEVEN.r() | Cerrar Excel, matar ControlR.exe, reabrir |
| Julia retorna error | Esperar 5 segundos, presionar F9 |
| NEVEN Studio no abre | Verificar servidor HTTP: `http://localhost:5555/health` |
| Chat IA no responde | Revisar configuración de API en neven-config.json |
| Gráfico no se abre | Envolver con `NEVEN.v()`: `=NEVEN.v(R.Pivot(rango, 1))` |

Para problemas complejos consulta el capítulo de [Mantenimiento](mantenimiento).

---

## 12. Recursos adicionales

| Recurso | Ubicación |
|:---|:---|
| Todas las funciones | Tab **Ayuda** en NEVEN Studio |
| Ejemplos en Excel | Carpeta `Ejemplos/` (R, Julia, Python, Quarto) |
| Documentación completa | 16 capítulos en tab Ayuda |
| Diccionario de 200+ funciones | [Diccionario de Funciones](diccionario-funciones) |
| RAG y formatos soportados | [RAG y Ontología](rag-ontologia-metaheuristica) |

---

*NEVEN v3.2 — BukloLAB*
