---
id: chart-gallery
title: "Capitulo 18 - Chart Gallery"
sidebar_label: 18. Chart Gallery
sidebar_position: 18
---

# Capitulo 18: Chart Gallery

**Disponible desde:** Agosto 2026

Chart Gallery es una galería interactiva de **325 gráficos profesionales** integrada en NEVEN Studio. Permite explorar, previsualizar y ejecutar visualizaciones en múltiples lenguajes (JavaScript, R, Python, Julia) directamente desde el TaskPane.

---

## 18.1 Qué es Chart Gallery

Chart Gallery integra la biblioteca **anyplot** — una colección curada de 325 gráficos estadísticos y de visualización de datos, cada uno implementado en cuatro lenguajes:

| Lenguaje | Librerías | Gráficos |
|:---|:---|:---|
| **JavaScript** | ECharts, Chart.js, D3.js | 325 |
| **R** | ggplot2, plotly | 325 |
| **Python** | matplotlib, plotly, seaborn | 325 |
| **Julia** | CairoMakie | 325 |

**Total:** 1,300 implementaciones (325 × 4 lenguajes).

---

## 18.2 Acceso a Chart Gallery

```
NEVEN Studio → Tab "Gráficos" → Botón "Chart Gallery"
```

También accesible desde:
- Ribbon NEVEN → Grupo Análisis → Chart Gallery
- Atajo: Ctrl+Shift+G (cuando el TaskPane está abierto)

---

## 18.3 Interfaz de la Galería

### Filtros disponibles

| Filtro | Descripción |
|:---|:---|
| **Búsqueda** | Texto libre para buscar por nombre |
| **Lenguaje** | JavaScript, R, Python, Julia, o Todos |
| **Librería** | ECharts, ggplot2, matplotlib, CairoMakie, etc. |
| **Clasificación** | Estándar o Avanzados |

### Tabs de clasificación

| Tab | Descripción | Cantidad |
|:---|:---|:---|
| **Estándar** | Gráficos con patrón Y~X (barras, líneas, scatter, pie, etc.) | ~135 |
| **Avanzados** | Gráficos con estructuras especiales (sankey, candlestick, treemap, etc.) | ~190 |

---

## 18.4 Tipos de gráficos

### Gráficos Estándar (Tab "Estándar")

Estos gráficos siguen el patrón clásico Y~X y son compatibles con la función "Usar mis datos":

| Familia | Ejemplos |
|:---|:---|
| **Barras** | bar-basic, bar-grouped, bar-stacked, bar-horizontal |
| **Líneas** | line-basic, line-multi, line-smooth, line-step |
| **Área** | area-basic, area-stacked, area-gradient |
| **Dispersión** | scatter-basic, scatter-bubble, scatter-regression |
| **Pastel** | pie-basic, pie-donut, pie-rose |
| **Histogramas** | histogram-basic, histogram-kde, histogram-cumulative |
| **Box plots** | box-basic, box-grouped, box-violin |
| **Otros** | lollipop, stem, ridgeline, density |

### Gráficos Avanzados (Tab "Avanzados")

Estos gráficos requieren estructuras de datos específicas:

| Familia | Ejemplos | Estructura requerida |
|:---|:---|:---|
| **Financieros** | candlestick, ohlc, kagi | Date + OHLC (5 cols) |
| **Flujo** | sankey, chord, alluvial | Source, Target, Value |
| **Jerárquicos** | treemap, sunburst, icicle | Padre, Hijo, Valor |
| **Redes** | network, force, hive | Nodos + Aristas |
| **Geoespaciales** | choropleth, bubble-map | Región + Valor |
| **Multi-eje** | parallel, radar, ternary | N variables |

---

## 18.5 Previsualización y código

Al seleccionar un gráfico de la galería:

1. **Preview** — Imagen estática del gráfico
2. **Código** — Script completo en el lenguaje seleccionado
3. **Botones de acción:**
   - **Copiar código** — Copia al portapapeles
   - **Ejecutar** — Ejecuta el gráfico (JS inmediato, R/Python/Julia via backend)
   - **Usar mis datos** — Inyecta datos de Excel (solo gráficos estándar)
   - **Guardar como** — Guarda en biblioteca personal

---

## 18.6 Ejecutar gráficos

### Gráficos JavaScript (ejecución inmediata)

Los gráficos ECharts, Chart.js y D3.js se ejecutan directamente en el navegador:

```
1. Seleccionar gráfico JavaScript
2. Clic "Ejecutar"
3. El gráfico se renderiza en el panel de preview
4. Interactuar: zoom, hover, tooltips
```

No requiere motores backend — funciona incluso sin R/Python/Julia instalados.

### Gráficos R/Python/Julia (ejecución backend)

Los gráficos ggplot2, matplotlib y CairoMakie requieren el motor correspondiente:

```
1. Seleccionar gráfico R/Python/Julia
2. Verificar que el motor esté activo (indicador verde)
3. Clic "Ejecutar"
4. Esperar procesamiento (2-10 segundos)
5. El gráfico se muestra como imagen PNG
```

**Requisitos:**
- Motor R activo para gráficos ggplot2
- Motor Python activo para matplotlib/plotly/seaborn
- Motor Julia activo para CairoMakie

---

## 18.7 Usar mis datos

La función "Usar mis datos" permite reemplazar los datos de ejemplo del gráfico con datos reales de Excel.

### Flujo de uso

```
1. En Excel: seleccionar rango de datos (ej: A1:C20)
2. Abrir Chart Gallery
3. Ir a Tab "Estándar"
4. Seleccionar un gráfico compatible (ej: bar-basic)
5. Clic botón "Usar mis datos" (morado)
6. El código se modifica automáticamente con tus datos
7. Clic "Ejecutar"
```

### Cómo funciona la inyección

NEVEN detecta la estructura de tus datos:
- **Columna 1:** Categorías (etiquetas del eje X)
- **Columnas 2+:** Series numéricas (valores del eje Y)

El código original se comenta como referencia y se inyectan los datos de Excel:

```javascript
// ══════════════════════════════════════════════════════════════
// DATOS DE EJEMPLO (comentados)
// ══════════════════════════════════════════════════════════════
// const months = ["Jan", "Feb", "Mar", "Apr"];
// const sales = [150, 230, 180, 290];

// ══════════════════════════════════════════════════════════════
// TUS DATOS (inyectados desde Excel: Sheet1!A1:B5)
// Columnas: Producto, Ventas | Filas: 5
// ══════════════════════════════════════════════════════════════
const months = ["Laptop", "Mouse", "Teclado", "Monitor", "Webcam"];
const sales = [1500, 300, 450, 890, 120];

// (resto del código del gráfico)
```

### Limitaciones

- Solo disponible para gráficos **Estándar** (tab Estándar)
- Los gráficos **Avanzados** requieren estructuras específicas
- El mapeo automático asume primera columna = categorías

---

## 18.8 Guardar gráficos personalizados

Puedes guardar gráficos modificados en tu biblioteca personal:

```
1. Modificar el código del gráfico
2. Clic "Guardar como"
3. Ingresar nombre descriptivo
4. El gráfico se guarda en C:\NEVEN\user-charts\
```

### Estructura de archivos guardados

```
C:\NEVEN\user-charts\
├── index.json          ← Catálogo de gráficos del usuario
├── my-sales-chart.js   ← Código del gráfico
├── monthly-report.js
└── ...
```

Los gráficos guardados aparecen en una sección "Mis Gráficos" al inicio de la galería.

---

## 18.9 Enviar a Slide

Los gráficos ejecutados pueden enviarse directamente a PowerPoint:

```
1. Ejecutar el gráfico
2. Clic botón "Enviar a Slide" (ícono de presentación)
3. Se captura el gráfico como imagen
4. Se inserta en la diapositiva activa de PowerPoint
```

**Requisitos:**
- PowerPoint debe estar abierto
- Funciona con gráficos JavaScript y backend

---

## 18.10 Familias de gráficos por librería

### ECharts (JavaScript)

| Categoría | Gráficos |
|:---|:---|
| Básicos | bar, line, pie, scatter |
| Estadísticos | boxplot, histogram, heatmap |
| Financieros | candlestick, k-line |
| Geográficos | map, geo |
| Relaciones | graph, sankey, chord |
| Otros | gauge, funnel, radar, tree |

### ggplot2 (R)

| Categoría | Geometrías |
|:---|:---|
| Básicos | geom_bar, geom_line, geom_point |
| Distribuciones | geom_histogram, geom_density, geom_boxplot |
| Estadísticos | geom_smooth, geom_violin, geom_rug |
| Facetas | facet_wrap, facet_grid |
| Temas | theme_minimal, theme_classic, theme_bw |

### matplotlib/seaborn (Python)

| Categoría | Funciones |
|:---|:---|
| Básicos | plt.bar, plt.plot, plt.scatter |
| Distribuciones | plt.hist, sns.kdeplot, sns.boxplot |
| Matrices | sns.heatmap, plt.imshow |
| Categorías | sns.catplot, sns.swarmplot |
| Regresión | sns.regplot, sns.lmplot |

### CairoMakie (Julia)

| Categoría | Funciones |
|:---|:---|
| Básicos | barplot, lines, scatter |
| Distribuciones | hist, density, boxplot |
| Superficies | surface, contour, heatmap |
| 3D | scatter3d, surface3d |
| Animaciones | record, animate |

---

## 18.11 Atajos de teclado

| Atajo | Acción |
|:---|:---|
| `Ctrl+C` | Copiar código seleccionado |
| `Ctrl+Enter` | Ejecutar gráfico |
| `Esc` | Cerrar preview expandido |
| `←` `→` | Navegar entre gráficos |
| `/` | Enfocar búsqueda |

---

## 18.12 Troubleshooting

**El gráfico JavaScript no se renderiza:**
- Verificar que el código no tenga errores de sintaxis
- Revisar la consola del navegador (F12 → Console)

**El gráfico R/Python/Julia falla:**
- Verificar que el motor esté activo (indicador verde)
- Revisar el mensaje de error en el panel de resultados
- Verificar que las librerías estén instaladas (ragg, ggplot2, matplotlib, etc.)

**"Usar mis datos" no funciona:**
- Solo disponible para gráficos del Tab "Estándar"
- Verificar que haya datos seleccionados en Excel
- La primera columna debe ser texto (categorías)

**El gráfico se ve cortado:**
- Expandir el panel de preview
- Usar el botón de pantalla completa

---

## 18.13 Requisitos de librerías

Para ejecutar gráficos backend, asegúrate de tener instaladas las librerías:

### R
```r
install.packages(c("ggplot2", "ragg", "dplyr", "scales", "tidyr", "tibble"))
```

### Python
```bash
pip install matplotlib plotly seaborn pandas pillow scipy
```

### Julia
```julia
using Pkg
Pkg.add(["CairoMakie", "Colors", "ColorSchemes"])
```

El instalador de NEVEN (`Install-NEVEN.ps1`) instala estas librerías automáticamente.

---

*Documentación actualizada: Agosto 2026*

*Chart Gallery — Agosto 2026*
*Universidad de Costa Rica — Tesis de Maestría*

