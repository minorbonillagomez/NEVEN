# SPEC: Sistema de Gráficos IA Multi-Librería

**Fecha:** Setiembre 2026  
**Autor:** Minor Bonilla Gómez + Kiro  
**Estado:** Diseño  
**Prioridad:** ALTA

---

## 1. Visión

> El usuario selecciona datos en Excel, pide un gráfico en lenguaje natural, y obtiene una visualización interactiva que puede enviar directamente al Creador de Presentaciones.

**Flujo completo:**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   EXCEL     │───▶│  NEVEN      │───▶│   AGENTE    │───▶│  WEBVIEW    │───▶│ PRESENTACIÓN│
│  (datos)    │    │  STUDIO     │    │   (LLM)     │    │ (gráfico)   │    │   (slide)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                  │                  │                  │
     │              Captura rango      Elige librería     Renderiza HTML     "Enviar a Slide"
     │              + prompt           + genera código    + interactividad    → Impress.js
```

---

## 2. Librerías Soportadas

El agente puede elegir entre estas librerías según el tipo de visualización:

| Librería | CDN | Mejor para | Sintaxis |
|:---|:---|:---|:---|
| **Plotly.js** | `https://cdn.plot.ly/plotly-2.27.0.min.js` | Científicos, 3D, heatmaps | JSON declarativo |
| **Chart.js** | `https://cdn.jsdelivr.net/npm/chart.js` | Simples, elegantes | Config object |
| **ECharts** | `https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js` | Dashboards, grandes datos | JSON option |
| **ApexCharts** | `https://cdn.jsdelivr.net/npm/apexcharts` | Modernos, responsivos | Config object |
| **D3.js** | `https://d3js.org/d3.v7.min.js` | Personalizados, grafos | Imperativo |
| **Vega-Lite** | `https://cdn.jsdelivr.net/npm/vega-lite@5` | Declarativo, gramática | JSON spec |
| **Leaflet** | `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js` | Mapas geográficos | API objetos |
| **Three.js** | `https://unpkg.com/three@0.160.0/build/three.module.js` | 3D inmersivo | Scene graph |

---

## 3. Selección Inteligente de Librería

El agente analiza los datos y la solicitud para elegir la mejor librería:

### Matriz de decisión

| Tipo de datos | Solicitud | Librería recomendada |
|:---|:---|:---|
| Series de tiempo | Líneas, tendencias | Plotly, ApexCharts |
| Categorías | Barras, columnas | Chart.js, ECharts |
| Proporciones | Pastel, donut | Chart.js, ApexCharts |
| Correlaciones | Heatmap, matriz | Plotly |
| Distribuciones | Histograma, box plot | Plotly |
| Geográficos | Mapa, ubicaciones | Leaflet |
| Redes/Grafos | Nodos, conexiones | D3.js |
| Flujos | Sankey, chord | D3.js |
| 3D | Superficie, scatter 3D | Plotly, Three.js |
| Dashboard | Múltiples gráficos | ECharts |
| Exploratorio | Análisis rápido | Vega-Lite |

### Reglas de selección

```python
def select_library(data_type, chart_type, data_size):
    # Regla 1: Mapas siempre con Leaflet
    if data_type == "geographic":
        return "Leaflet"
    
    # Regla 2: Grafos/redes siempre con D3
    if chart_type in ["network", "sankey", "chord", "tree"]:
        return "D3.js"
    
    # Regla 3: 3D con Plotly (más fácil) o Three.js (más control)
    if chart_type in ["surface", "scatter3d", "mesh"]:
        return "Plotly" if data_size < 10000 else "Three.js"
    
    # Regla 4: Dashboards multi-gráfico con ECharts
    if chart_type == "dashboard":
        return "ECharts"
    
    # Regla 5: Gráficos científicos con Plotly
    if chart_type in ["heatmap", "contour", "histogram2d", "boxplot"]:
        return "Plotly"
    
    # Regla 6: Gráficos simples con Chart.js (más ligero)
    if chart_type in ["bar", "line", "pie", "doughnut"] and data_size < 1000:
        return "Chart.js"
    
    # Regla 7: Datos grandes con ECharts (mejor rendimiento)
    if data_size > 5000:
        return "ECharts"
    
    # Default: ApexCharts (balance entre features y simplicidad)
    return "ApexCharts"
```

---

## 4. Arquitectura Técnica

### 4.1 Captura de Rango (Office.js)

```javascript
// taskpane.js
async function captureSelectedRangeForChart() {
    return await Excel.run(async (context) => {
        const selection = context.workbook.getSelectedRange();
        selection.load(["values", "address", "columnCount", "rowCount"]);
        await context.sync();
        
        // Detectar si primera fila son headers
        const values = selection.values;
        const hasHeaders = detectHeaders(values[0]);
        
        return {
            address: selection.address,
            values: values,
            headers: hasHeaders ? values[0] : null,
            data: hasHeaders ? values.slice(1) : values,
            columns: selection.columnCount,
            rows: selection.rowCount - (hasHeaders ? 1 : 0)
        };
    });
}

function detectHeaders(firstRow) {
    // Si la primera fila tiene más strings que números, son headers
    const strings = firstRow.filter(v => typeof v === 'string' && isNaN(v)).length;
    return strings > firstRow.length / 2;
}
```

### 4.2 Detección de Intención de Gráfico

```javascript
// taskpane.js
function detectChartIntent(prompt) {
    const chartKeywords = {
        line: /línea|linea|line|tendencia|serie|temporal/i,
        bar: /barra|bar|columna|column/i,
        pie: /pastel|pie|torta|circular|proporción/i,
        scatter: /dispersión|scatter|puntos|correlación/i,
        heatmap: /calor|heat|matriz|correlación/i,
        map: /mapa|map|ubicación|geográfico|coordenadas/i,
        histogram: /histograma|distribución|frecuencia/i,
        boxplot: /caja|box|bigotes|whisker|outlier/i,
        network: /red|network|grafo|nodos|conexiones/i,
        sankey: /flujo|sankey|flow/i,
        treemap: /árbol|treemap|jerárquico/i,
        radar: /radar|araña|spider/i,
        funnel: /embudo|funnel|conversión/i,
        gauge: /medidor|gauge|velocímetro/i,
        surface: /superficie|3d|tridimensional/i
    };
    
    const genericChart = /gráfico|grafico|gráfica|grafica|chart|visualiza|dibuja|muestra|plot/i;
    
    if (!genericChart.test(prompt)) {
        return null; // No es una solicitud de gráfico
    }
    
    for (const [type, regex] of Object.entries(chartKeywords)) {
        if (regex.test(prompt)) {
            return type;
        }
    }
    
    return "auto"; // El agente decidirá basándose en los datos
}
```

### 4.3 System Prompt para el Agente

```python
# neven_ai_service.py

CHART_GENERATION_PROMPT = """
Eres un experto en visualización de datos. Tu tarea es generar código HTML autocontenido 
con gráficos interactivos basados en los datos proporcionados.

## LIBRERÍAS DISPONIBLES (elige la más apropiada):

1. **Plotly.js** - Para gráficos científicos, 3D, heatmaps, estadísticos
   CDN: https://cdn.plot.ly/plotly-2.27.0.min.js

2. **Chart.js** - Para gráficos simples y elegantes (barras, líneas, pastel)
   CDN: https://cdn.jsdelivr.net/npm/chart.js

3. **ECharts** - Para dashboards, grandes volúmenes de datos
   CDN: https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js

4. **ApexCharts** - Para gráficos modernos y responsivos
   CDN: https://cdn.jsdelivr.net/npm/apexcharts

5. **D3.js** - Para visualizaciones personalizadas, grafos, diagramas de flujo
   CDN: https://d3js.org/d3.v7.min.js

6. **Leaflet** - Para mapas geográficos
   CDN: https://unpkg.com/leaflet@1.9.4/dist/leaflet.js
   CSS: https://unpkg.com/leaflet@1.9.4/dist/leaflet.css

## REGLAS OBLIGATORIAS:

1. Genera HTML COMPLETO y autocontenido (<!DOCTYPE html> hasta </html>)
2. Incluye el CDN de la librería en un <script src="...">
3. Los datos deben estar EMBEBIDOS en el código (const data = [...])
4. El gráfico debe ser INTERACTIVO (hover, tooltips, zoom si aplica)
5. Incluye título descriptivo y leyenda cuando sea apropiado
6. Usa colores profesionales y accesibles
7. El contenedor debe tener width: 100% y height: 100vh
8. NO incluyas explicaciones, SOLO el código HTML

## DATOS DEL USUARIO:

Rango: {range_address}
Headers: {headers}
Datos:
{data_json}

## SOLICITUD:

{user_prompt}

## RESPUESTA:

Genera el HTML completo:
"""
```

### 4.4 Renderizado en WebView

```javascript
// taskpane.js
function renderChartInPreview(htmlContent) {
    const previewContainer = document.getElementById('chart-preview');
    
    // Crear iframe sandboxed para ejecutar el código
    const iframe = document.createElement('iframe');
    iframe.style.width = '100%';
    iframe.style.height = '500px';
    iframe.style.border = 'none';
    iframe.sandbox = 'allow-scripts allow-same-origin';
    
    previewContainer.innerHTML = '';
    previewContainer.appendChild(iframe);
    
    // Escribir el HTML en el iframe
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    doc.open();
    doc.write(htmlContent);
    doc.close();
    
    // Agregar botón "Enviar a Slide"
    addSendToSlideButton(previewContainer, htmlContent);
}

function addSendToSlideButton(container, htmlContent) {
    const btn = document.createElement('button');
    btn.className = 'send-to-slide-btn';
    btn.innerHTML = '📊 Enviar a Slide';
    btn.onclick = () => sendChartToPresentation(htmlContent);
    container.appendChild(btn);
}
```

### 4.5 Integración con Creador de Presentaciones

```javascript
// taskpane.js
function sendChartToPresentation(htmlContent) {
    // El Creador de Presentaciones ya soporta iframes
    // Solo necesitamos enviar el HTML como un objeto embebido
    
    const slideObject = {
        type: 'chart',
        content: htmlContent,
        title: 'Gráfico generado por IA',
        timestamp: new Date().toISOString()
    };
    
    // Enviar al tab de Presentaciones
    window.postMessage({
        action: 'addSlideObject',
        payload: slideObject
    }, '*');
    
    // Cambiar a la pestaña de Presentaciones
    switchToTab('presentations');
    
    showToast('Gráfico enviado a la presentación');
}
```

---

## 5. Interfaz de Usuario

### 5.1 Flujo en Tab IA

```
┌─────────────────────────────────────────────────────────────────┐
│ Tab IA                                                    [X]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Chat history...]                                              │
│                                                                 │
│  Usuario: grafica estos datos como barras                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │              [GRÁFICO INTERACTIVO]                      │   │
│  │                                                         │   │
│  │              (Plotly/Chart.js/etc.)                     │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [📊 Enviar a Slide]  [💾 Guardar PNG]  [📋 Copiar HTML]       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [Escribe tu mensaje...]                              [Enviar] │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Indicador de Selección

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Rango seleccionado: Sheet1!A1:D50 (50 filas × 4 columnas)  │
│  Headers: Fecha, Ventas, Costos, Margen                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Ejemplos de Uso

### Ejemplo 1: Gráfico de líneas simple

**Usuario selecciona:** A1:B12 (Meses y Ventas)
**Usuario escribe:** "Gráfico de líneas de las ventas"

**Agente genera:** Chart.js con línea suavizada, tooltips, título "Ventas Mensuales"

### Ejemplo 2: Mapa de ubicaciones

**Usuario selecciona:** A1:C20 (Nombre, Latitud, Longitud)
**Usuario escribe:** "Mapa con las ubicaciones de las tiendas"

**Agente genera:** Leaflet con marcadores, popup con nombre, zoom automático

### Ejemplo 3: Dashboard

**Usuario selecciona:** A1:E100 (datos de ventas completos)
**Usuario escribe:** "Dashboard con ventas por región, por mes, y top productos"

**Agente genera:** ECharts con 3 gráficos coordinados, filtros interactivos

### Ejemplo 4: Heatmap de correlaciones

**Usuario selecciona:** A1:J11 (matriz numérica)
**Usuario escribe:** "Mapa de calor de correlaciones"

**Agente genera:** Plotly heatmap con escala de colores, valores en hover

---

## 7. Implementación por Fases

### Fase 1: MVP (1 semana)
- [ ] `captureSelectedRangeForChart()` en taskpane.js
- [ ] `detectChartIntent()` para keywords básicas
- [ ] System prompt `CHART_GENERATION_PROMPT`
- [ ] Renderizado en iframe con botones de acción
- [ ] Soporte para Plotly y Chart.js

### Fase 2: Multi-librería (1 semana)
- [ ] Agregar ECharts, ApexCharts, D3.js
- [ ] Lógica de selección inteligente
- [ ] Detección automática de tipo de datos
- [ ] Leaflet para mapas

### Fase 3: Integración Presentaciones (3 días)
- [ ] `sendChartToPresentation()` funcional
- [ ] Objeto embebido en Impress.js
- [ ] Controles de escala/posición en slide

### Fase 4: Mejoras UX (ongoing)
- [ ] Exportar PNG/SVG
- [ ] Copiar HTML al portapapeles
- [ ] Historial de gráficos generados
- [ ] Galería de ejemplos/templates

---

## 8. Consideraciones Técnicas

### Seguridad
- El HTML generado se ejecuta en iframe sandboxed
- Solo se permiten CDNs de librerías conocidas
- Los datos nunca salen de la máquina local

### Rendimiento
- Chart.js para datasets pequeños (<1000 puntos)
- ECharts para datasets grandes (>5000 puntos)
- Lazy loading de CDNs según librería seleccionada

### Compatibilidad
- WebView2 soporta ES6+, Canvas, WebGL
- Todas las librerías listadas funcionan en WebView2

---

## 9. Métricas de Éxito

| Métrica | Objetivo |
|:---|:---|
| Tiempo de generación | < 10 segundos |
| Tasa de éxito (gráfico válido) | > 90% |
| Satisfacción del usuario | > 4/5 |
| Uso de "Enviar a Slide" | > 30% de gráficos generados |

---

*NEVEN v2.5 — Sistema de Gráficos IA Multi-Librería*
*Universidad de Costa Rica — Setiembre 2026*
