---
id: graficos-rapidos
title: "Capitulo 19 - Graficos Rapidos (Quick Plots)"
sidebar_label: 19. Graficos Rapidos
sidebar_position: 19
---

# Capitulo 19: Graficos Rapidos (Quick Plots)

**Disponible desde:** Agosto 2026

Quick Plots es una herramienta de visualización inmediata integrada en NEVEN Studio. Permite crear gráficos profesionales en segundos directamente desde datos seleccionados en Excel, sin escribir código.

---

## 19.1 Qué es Quick Plots

Quick Plots transforma datos de Excel en gráficos interactivos con un solo clic. A diferencia de los gráficos nativos de Excel, Quick Plots:

- Genera gráficos **Plotly** interactivos (zoom, hover, pan)
- Detecta automáticamente el tipo de datos
- Sugiere el gráfico más apropiado
- Permite exportar como PNG, SVG o enviar a PowerPoint

---

## 19.2 Acceso a Quick Plots

```
NEVEN Studio → Tab "Gráficos" → Sección "Gráfico Rápido"
```

También accesible desde:
- Ribbon NEVEN → Grupo Análisis → Gráfico Rápido
- Menú contextual en Excel (clic derecho en selección)

---

## 19.3 Flujo de uso básico

```
1. En Excel: seleccionar rango de datos con headers
   (ej: A1:C20 con columnas "Mes", "Ventas", "Gastos")

2. Abrir NEVEN Studio → Tab "Gráficos"

3. Los datos aparecen automáticamente en la sección Quick Plots

4. Seleccionar tipo de gráfico:
   - Barras | Líneas | Área | Dispersión | Pastel | Serie de Tiempo

5. Clic "Crear Gráfico"

6. El gráfico interactivo aparece en el panel de resultados
```

---

## 19.4 Tipos de gráficos disponibles

| Tipo | Icono | Uso recomendado |
|:---|:---|:---|
| **Barras** | 📊 | Comparar categorías |
| **Líneas** | 📈 | Tendencias temporales |
| **Área** | 📉 | Tendencias con volumen |
| **Dispersión** | ⚬ | Correlación entre variables |
| **Pastel** | 🥧 | Composición porcentual |
| **Serie de Tiempo** | 📅 | Datos con fechas + tendencia |

---

## 19.5 Detección automática de datos

Quick Plots analiza la selección de Excel y detecta:

| Detección | Acción |
|:---|:---|
| Primera fila con texto | → Headers (nombres de columnas) |
| Columna con texto | → Categorías (eje X) |
| Columnas numéricas | → Series (eje Y) |
| Columna con fechas | → Habilita "Serie de Tiempo" |

### Ejemplo de detección

```
Selección: A1:C5

| Producto | Ventas | Gastos |
|----------|--------|--------|
| Laptop   | 1500   | 800    |
| Mouse    | 300    | 50     |
| Teclado  | 450    | 120    |
| Monitor  | 890    | 400    |

Detección:
- Headers: "Producto", "Ventas", "Gastos"
- Categorías: columna "Producto" (texto)
- Series: "Ventas" y "Gastos" (numéricas)
- Filas: 4
```

---

## 19.6 Panel de descripción

Antes de crear el gráfico, Quick Plots muestra un panel informativo:

```
┌─────────────────────────────────────────────┐
│ 📊 Datos detectados                         │
│                                             │
│ Rango: Sheet1!A1:C5                         │
│ Filas: 4 (sin header)                       │
│ Columnas: 3                                 │
│                                             │
│ Estructura:                                 │
│ • Categorías: Producto (4 valores únicos)   │
│ • Serie 1: Ventas (rango: 300 - 1500)       │
│ • Serie 2: Gastos (rango: 50 - 800)         │
│                                             │
│ Tipo sugerido: Barras agrupadas             │
└─────────────────────────────────────────────┘
```

---

## 19.7 Serie de Tiempo con tendencia

Cuando los datos incluyen una columna de fechas, el botón "Serie de Tiempo" se habilita:

```
1. Seleccionar datos con columna de fechas
   (ej: Fecha, Valor)

2. Clic "Serie de Tiempo"

3. Quick Plots genera:
   - Línea de datos originales
   - Línea de tendencia (regresión lineal)
   - Banda de confianza (95%)

4. Leyenda indica:
   - "Datos" (serie original)
   - "Tendencia" (línea de regresión)
```

### Opciones de tendencia

| Opción | Descripción |
|:---|:---|
| **Lineal** | Regresión lineal simple (default) |
| **Polinómica** | Ajuste polinómico grado 2-5 |
| **Media móvil** | Promedio móvil de N períodos |
| **Suavizado** | LOESS / LOWESS |

---

## 19.8 Interactividad de los gráficos

Los gráficos Quick Plots son completamente interactivos:

| Acción | Resultado |
|:---|:---|
| **Hover** | Muestra tooltip con valores exactos |
| **Zoom** | Scroll o arrastrar para hacer zoom |
| **Pan** | Arrastrar para mover el área visible |
| **Selección** | Clic en leyenda para mostrar/ocultar series |
| **Reset** | Doble clic para volver a vista inicial |

### Barra de herramientas Plotly

Cada gráfico incluye la barra de herramientas estándar de Plotly:

| Botón | Función |
|:---|:---|
| 📷 | Descargar como PNG |
| 🔍+ | Zoom in |
| 🔍- | Zoom out |
| ↔️ | Pan |
| 🏠 | Reset axes |
| ✂️ | Selección de área |

---

## 19.9 Exportación

### Descargar imagen

```
Gráfico renderizado → Barra Plotly → Icono cámara (📷)
→ Se descarga PNG a carpeta de descargas
```

### Enviar a PowerPoint

```
Gráfico renderizado → Botón "Enviar a Slide"
→ Captura el gráfico como imagen
→ Inserta en diapositiva activa de PowerPoint
```

**Requisitos:** PowerPoint debe estar abierto con una presentación activa.

### Copiar al portapapeles

```
Gráfico renderizado → Clic derecho → "Copiar imagen"
→ Pegar en Word, PowerPoint, email, etc.
```

---

## 19.10 Personalización rápida

Quick Plots permite ajustes básicos sin código:

| Opción | Ubicación |
|:---|:---|
| **Título** | Campo de texto sobre el gráfico |
| **Colores** | Selector de paleta (8 opciones) |
| **Leyenda** | Toggle mostrar/ocultar |
| **Gridlines** | Toggle mostrar/ocultar |

### Paletas de colores disponibles

| Paleta | Colores |
|:---|:---|
| **Default** | Azul, naranja, verde, rojo, morado |
| **Viridis** | Gradiente verde-amarillo-azul |
| **Pastel** | Colores suaves |
| **Bold** | Colores saturados |
| **Monochrome** | Escala de grises |
| **Corporate** | Azul corporativo |
| **Nature** | Verdes y marrones |
| **Warm** | Rojos, naranjas, amarillos |

---

## 19.11 Diferencias con Chart Gallery

| Característica | Quick Plots | Chart Gallery |
|:---|:---|:---|
| **Propósito** | Visualización inmediata | Explorar y aprender |
| **Código visible** | No | Sí (editable) |
| **Tipos de gráficos** | 6 básicos | 325 avanzados |
| **Lenguajes** | Solo JavaScript (Plotly) | JS, R, Python, Julia |
| **Personalización** | Básica (UI) | Total (código) |
| **Curva de aprendizaje** | Cero | Requiere conocer código |

**Recomendación:**
- Usa **Quick Plots** para visualizaciones rápidas del día a día
- Usa **Chart Gallery** para gráficos publicables o aprender nuevas técnicas

---

## 19.12 Integración con Data Lab

Los datos cargados en Quick Plots están disponibles para Data Lab:

```
1. Cargar datos en Quick Plots (desde Excel)
2. Los datos se almacenan como `dataset` en DuckDB
3. Ir a Tab "Data Lab"
4. Las columnas detectadas aparecen en el panel de variables
5. Ejecutar análisis sobre los mismos datos
```

Esto permite un flujo de trabajo integrado:
```
Excel → Quick Plots (visualizar) → Data Lab (analizar)
```

---

## 19.13 Atajos de teclado

| Atajo | Acción |
|:---|:---|
| `Ctrl+G` | Crear gráfico (cuando hay datos cargados) |
| `Ctrl+1` | Tipo: Barras |
| `Ctrl+2` | Tipo: Líneas |
| `Ctrl+3` | Tipo: Área |
| `Ctrl+4` | Tipo: Dispersión |
| `Ctrl+5` | Tipo: Pastel |
| `Ctrl+6` | Tipo: Serie de Tiempo |

---

## 19.14 Troubleshooting

**No aparecen datos en Quick Plots:**
- Verificar que haya una selección activa en Excel
- La selección debe tener al menos 2 filas (header + 1 dato)
- Verificar conexión Excel-TaskPane (indicador verde)

**El gráfico no se genera:**
- Verificar que haya al menos una columna numérica
- Para gráficos de pastel, solo se usa la primera serie numérica

**Serie de Tiempo deshabilitada:**
- La primera columna debe contener fechas reconocibles
- Formatos válidos: dd/mm/yyyy, yyyy-mm-dd, mm/dd/yyyy

**Los colores no cambian:**
- Regenerar el gráfico después de cambiar la paleta
- Algunas paletas no aplican a todos los tipos de gráficos

---

## 19.15 Ejemplos de uso

### Ejemplo 1: Ventas por producto (Barras)

```
Datos Excel:
| Producto | Q1    | Q2    | Q3    | Q4    |
|----------|-------|-------|-------|-------|
| Laptop   | 1200  | 1350  | 1100  | 1500  |
| Mouse    | 300   | 280   | 320   | 350   |
| Teclado  | 450   | 420   | 480   | 510   |

→ Quick Plots → Barras
→ Resultado: Barras agrupadas con 4 series (Q1-Q4)
```

### Ejemplo 2: Tendencia de temperatura (Serie de Tiempo)

```
Datos Excel:
| Fecha      | Temperatura |
|------------|-------------|
| 2026-01-01 | 22.5        |
| 2026-01-02 | 23.1        |
| 2026-01-03 | 21.8        |
| ...        | ...         |

→ Quick Plots → Serie de Tiempo
→ Resultado: Línea con tendencia lineal y banda de confianza
```

### Ejemplo 3: Distribución de gastos (Pastel)

```
Datos Excel:
| Categoría    | Monto |
|--------------|-------|
| Salarios     | 45000 |
| Alquiler     | 12000 |
| Servicios    | 3500  |
| Marketing    | 8000  |
| Otros        | 2500  |

→ Quick Plots → Pastel
→ Resultado: Gráfico circular con porcentajes en hover
```

---

*Documentación actualizada: Agosto 2026*

*Quick Plots — Agosto 2026*
*Universidad de Costa Rica — Tesis de Maestría*

