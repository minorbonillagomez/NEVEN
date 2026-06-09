---
id: funciones-r
title: Capitulo 5 -- Funciones R y Graficos
sidebar_label: 5. Funciones R
sidebar_position: 5
---

# Capitulo 5: Funciones R

R es el motor estadistico de NEVEN. La libreria incluye ~90 procedimientos organizados en 34 archivos, cubriendo desde regresion lineal hasta mineria de texto. Todas las funciones siguen el patron **TipoOutput** para seleccionar el procedimiento deseado.

$
\texttt{=R.Funcion(SetDatosY, SetDatosX, Categorica, Filtro, Escala, ..., TipoOutput)}
$

---

## 5.0 Parametros Transversales

Todas las funciones de regresion comparten estos parametros:

| Parametro | Descripcion |
|:---|:---|
| **TipoOutput** | Selecciona el resultado (0=lista de opciones, 1..N-1=resultado especifico, N=extraccion universal) |
| **Filtro** | Vector binario (0=incluir, 1=excluir). Permite analisis de sensibilidad por observacion |
| **Categorica** | 0=auto-deteccion (recomendado), 1=dialogo manual para variables numericas que son categoricas |
| **Escala** | 0=sin escalar, 1=estandarizar variables |

### Auto-deteccion de variables categoricas

NEVEN detecta automaticamente si los datos contienen variables de texto y las convierte a factores (dummies) sin intervencion del usuario. Esto permite usar datasets mixtos (numerico + texto) directamente.

### Funciones de gestion de datos

| Funcion | Descripcion |
|:---|:---|
| `=R.DB_Unicos(rango)` | Retorna valores unicos (distinct) de un rango |
| `=R.DB_Recodificar(datos, viejos, nuevos)` | Sustituye valores en un rango |
| `=R.DB_Union(X, Y, TipoOutput)` | Une dos tablas (inner, outer, left, right, cross join) |
| `=R.DB_Pivote(X, Y, Filtro, TipoOutput)` | Tabla pivote (suma, media, mediana, conteo, sesgo, Jarque-Bera) |

---

## 5.1 Modelos de Regresion (Supervisados)

### Regresion Lineal Multiple -- `R.MR_Lineal`

$
y = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \cdots + \beta_k x_k + \varepsilon
$

| TipoOutput | Procedimiento |
|:---:|:---|
| 0 | Lista de procedimientos |
| 1 | Estimacion del modelo (coeficientes, $R^2$, $F$-test) |
| 2 | $\hat{y}$ estimado |
| 3 | Prediccion fuera de muestra |
| 4 | VIF (Variance Inflation Factor) -- multicolinealidad |
| 5 | Test de Breusch-Pagan (heterocedasticidad) |
| 6 | Errores estandar robustos (HC) |
| 7 | Deteccion de outliers |
| 8 | Residuos |

### Regresion Logistica / Probit -- `R.MR_Binario.C`

$
P(Y=1|X) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 x_1 + \cdots)}}
$

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | Modelo logit/probit |
| 2 | Probabilidades estimadas |
| 3 | Test de Hosmer-Lemeshow |
| 4 | Efectos marginales |

### Regresion Poisson -- `R.MR_Poisson.C`

$
\log(\lambda) = \beta_0 + \beta_1 x_1 + \cdots
$

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | Modelo Poisson |
| 2 | Prediccion dentro de muestra |
| 3 | Prediccion fuera de muestra |

### Regresion Censurada (Tobit) -- `R.MR_Tobit.C`

Para datos con truncamiento (ej: salarios censurados en cero).

### Datos de Panel -- `R.MR_PanelData.C`

$
y_{it} = \alpha_i + \beta x_{it} + \varepsilon_{it}
$

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | Efectos fijos |
| 2 | Efectos aleatorios |
| 3 | Test de Hausman |
| 4 | Test de Breusch-Pagan |
| 5 | Raiz unitaria de panel |

### Arboles de Decision -- `R.AD_ArbolDecision.C`

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | Modelo de arbol |
| 2 | Prediccion |
| 3 | Visualizacion del arbol |

### Support Vector Machines -- `R.MR_SVM`

Kernels disponibles: lineal, polinomial, RBF, sigmoide.

### Modelos Mixtos -- `R.MR_Mixtos`

Modelos lineales de efectos mixtos (lme4).

### Analisis de Supervivencia -- `R.MR_Supervivencia`

Kaplan-Meier, Cox proportional hazards.

### Regresion Bayesiana -- `R.MR_Bayesiana`

Modelos bayesianos via rstanarm.

### Estadistica Base -- `R.MR_EstadisticaBase`

Tests basicos: $t$-test, $\chi^2$, ANOVA, correlacion.

### Supuestos -- `R.MR_Supuestos`

Verificacion de supuestos de regresion: normalidad, homocedasticidad, autocorrelacion.

### Pronostico -- `R.ST_Pronostico`

Modelos de pronostico: ARIMA, suavizamiento exponencial.

---

## 5.2 Analisis No Supervisado

### Componentes Principales (ACP) -- `R.AD_ACP.C`

$
Z = XW, \quad \text{donde } W = \text{eigenvectors de } \Sigma
$

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | Correlaciones |
| 2 | Loadings |
| 3 | Scores |
| 4 | Biplot |
| 5 | $\cos^2$ (calidad de representacion) |
| 6 | Contribuciones |
| 7 | Varianza explicada |

### K-Medias -- `R.AD_KMedias.C`

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | Clusters |
| 2 | Centros |
| 3 | Variabilidad intra-cluster |
| 4 | Estadistico GAP |
| 5 | $K$ optimo |

### Estadistica Descriptiva -- `R.AD_Descriptiva`

Media, mediana, desviacion estandar, cuartiles, asimetria, curtosis.

### Psicometria -- `R.AD_Psicometria`

Analisis factorial, alfa de Cronbach, KMO.

### Mineria de Texto -- `R.TM_TextMining`

Nubes de palabras, frecuencias, matrices termino-documento.

### Correlacion Rolling -- `R.AD_NonParRolCor`

Correlacion no parametrica con ventana deslizante.

---

## 5.3 Series de Tiempo

### Tests y Descomposicion -- `R.ST_SeriesTemporales`

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | Test ADF (Augmented Dickey-Fuller) |
| 2 | Test Phillips-Perron |
| 3 | Test Phillips-Ouliaris |
| 4 | Test Jarque-Bera |
| 5 | Autocorrelacion (ACF/PACF) |
| 6 | Descomposicion |

### Modelos Autorregresivos -- `R.ST_Autoregresivos`

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | ARMA |
| 2 | ARIMA |
| 3 | SARIMA |
| 4 | GARCH |
| 5 | E-GARCH |
| 6 | Prediccion |

### Filtros -- `R.ST_Filtro`

Hodrick-Prescott, Baxter-King, Christiano-Fitzgerald, Butterworth, trigonometrico.

---

## 5.4 Graficos

### Plotly Interactivo -- `R.GR_PlotlyView`

| TipoOutput | Grafico |
|:---:|:---|
| 1 | Lineas + Marcadores |
| 2 | Barras |
| 3 | Scatter |
| 4 | Area |
| 5 | Combinado |

```
=NEVEN.v(R.GR_PlotlyView(A1:C4, 0, 0, "Titulo", 5))
```

### QuickPlot -- `R.GR_QuickPlot`

| TipoOutput | Grafico | Motor |
|:---:|:---|:---|
| 1-6 | Barras, Lineas, Scatter, Histograma, BoxPlot, Pie | R base (PNG) |
| 7-9 | Barras, Lineas, Scatter interactivos | ggplot2 + Plotly (HTML) |

### Mapas -- `R.MP_MapaISO03`

Mapas mundiales con datos por pais (codigo ISO3).

---

## 5.5 Utilidades de Datos

| Funcion | Descripcion |
|:---|:---|
| `R.DB_Pivote` | Tabla pivote con multiples funciones de agregacion |
| `R.DB_Union` | Joins tipo SQL (inner, outer, left, right, cross) |
| `R.DB_Unicos` | Valores unicos de una columna |
| `R.UT_Computo_Vars` | Variables dummy, escalamiento, distancias |
| `R.FX_Distancias` | Euclidiana, Manhattan, Canberra, Minkowski |
| `R.FX_AleatorioUniforme` | Generacion aleatoria $\sim U(a,b)$ |
| `R.FX_AleatorioNormal` | Generacion aleatoria $\sim \mathcal{N}(\mu, \sigma)$ |
| `R.DS_Wooldridge` | Carga datasets del paquete Wooldridge |
| `R.DS_ObtenerDatos` | Carga datos desde archivos |

---

## 5.6 Algebra Lineal -- `R.MM_Algebra.C`

| TipoOutput | Procedimiento |
|:---:|:---|
| 1 | Descomposicion de Cholesky |
| 2 | Eigenvalores y eigenvectores |
| 3 | Factorizacion QR |
| 4 | Inversa |
| 5 | Descomposicion SVD |
| 6 | Diagonal |
| 7 | Transpuesta |

---

## 5.7 Funciones Internas (Core)

Estas funciones son usadas internamente por las demas. No se llaman directamente desde Excel:

| Funcion | Proposito |
|:---|:---|
| `R4XCL_INT_DATOS` | Preprocesamiento: numerico/categorico, filtrado, ponderacion |
| `R4XCL_INT_FUNCION` | Construccion automatica de formulas R desde rangos |
| `R4XCL_INT_FILTRAR` | Filtrado de observaciones |
| `R4XCL_INT_PROCEDIMIENTOS` | Definicion de menus TipoOutput |
| `R4XCL_INT_DIALOGOS` | Descripciones para el Asistente de Funciones |
| `R4XCL_INT_CREARDS` | Guardar modelos en formato RDS |
| `R4XCL_INT_CREAXCL` | Exportar resultados a Excel |

---

## 5.8 Analisis de Datos Interactivo

Estas funciones generan visualizaciones HTML interactivas que se abren en el viewer WebView2 con `=NEVEN.v(...)`. Todas siguen el patron `TipoOutput=0` para listar procedimientos.

### R.Pivot -- Tabla Pivote Interactiva

Firma: `=R.Pivot(SetDatosX, TipoOutput)`

Genera tablas pivote interactivas basadas en la libreria **rpivotTable**.

| TipoOutput | Procedimiento |
|:---:|:---|
| 0 | Lista de procedimientos |
| 1 | Pivot interactivo (drag-and-drop libre) |
| 2 | Pivot con Heatmap |
| 3 | Pivot con barras horizontales |

```
=NEVEN.v(R.Pivot(A1:E20, 1))
```

En el pivot interactivo puede arrastrar columnas a filas, columnas, y seleccionar la agregacion (Count, Sum, Average, etc.).

### R.Esquisse -- Explorador de Datos

Firma: `=R.Esquisse(SetDatosX, TipoOutput)`

Genera un explorador interactivo con selectores para ejes X, Y, color y tipo de grafico. Basado en **Plotly.js**.

| TipoOutput | Procedimiento |
|:---:|:---|
| 0 | Lista de procedimientos |
| 1 | Explorador interactivo con selectores de ejes X, Y, color, tipo |

Tipos disponibles en el explorador: Scatter, Barras, Lineas, Box Plot, Histograma, Heatmap.

```
=NEVEN.v(R.Esquisse(A1:E20, 1))
```

### R.D3 -- Visualizaciones D3.js

Firma: `=R.D3(SetDatosX, TipoOutput)`

Visualizaciones avanzadas con **D3.js v7**. Los datos deben tener columnas categoricas (para jerarquias) y al menos una columna numerica (para valores).

| TipoOutput | Procedimiento |
|:---:|:---|
| 0 | Lista de procedimientos |
| 1 | Treemap |
| 2 | Sankey |
| 3 | Sunburst |
| 4 | Force Graph |

```
=NEVEN.v(R.D3(A1:E20, 1))
```

El Force Graph permite arrastrar nodos interactivamente. El Treemap y Sunburst muestran tooltips al pasar el mouse.

### R.Dashboard -- Dashboard Todo-en-Uno

Firma: `=R.Dashboard(SetDatosX, TipoOutput)`

Combina todas las visualizaciones en una sola pagina con tabs. Basado en **rpivotTable + Plotly.js + D3.js**.

| TipoOutput | Procedimiento |
|:---:|:---|
| 0 | Lista de procedimientos |
| 1 | Dashboard completo con 6 tabs |

Tabs disponibles: Pivot Table, Explorador, Treemap, Sankey, Sunburst, Force Graph. Cada tab se carga al hacer clic (lazy loading).

```
=NEVEN.v(R.Dashboard(A1:E20, 1))
```

### R.Map -- Mapas Interactivos

Firma: `=R.Map(SetDatosX, TipoOutput)`

Mapas interactivos basados en **Leaflet.js** con tiles CartoDB dark. Los datos deben tener: Col1=Latitud, Col2=Longitud, Col3=Etiqueta o Valor, Col4=Popup (opcional).

| TipoOutput | Procedimiento |
|:---:|:---|
| 0 | Lista de procedimientos |
| 1 | Marcadores |
| 2 | Mapa de calor |
| 3 | Circulos proporcionales |

```
=NEVEN.v(R.Map(A1:D10, 1))
```

Detecta automaticamente las columnas de latitud y longitud por nombre (Lat, Lon, Latitude, Longitude).

---

## 5.9 Patron de diseno de funciones R

Todas las funciones R siguen un patron consistente:

```r
MiFuncion <- function(SetDatosX, SetDatosY=NULL, Escala=0,
                       Filtro=0, Categorica=0, TipoOutput=0) {
  if (TipoOutput == 0) return(R4XCL_INT_PROCEDIMIENTOS("MiFuncion"))
  datos <- R4XCL_INT_DATOS(SetDatosX, SetDatosY, Escala, Filtro, Categorica)
  # ... analisis ...
  return(resultado)
}

attr(MiFuncion, "description") <- list(
  "Descripcion de la funcion",
  SetDatosX = "Variables independientes",
  SetDatosY = "Variable dependiente",
  TipoOutput = "0:Procedimientos, 1:Modelo, 2:Prediccion, ..."
)
```

Este patron garantiza:
1. `TipoOutput=0` siempre retorna la lista de procedimientos
2. Los datos se preprocesan uniformemente
3. Las descripciones aparecen en el Asistente de Funciones de Excel (Shift+F3)
