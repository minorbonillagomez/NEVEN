# Diccionario de Funciones NEVEN

**Última actualización:** 2026-08-19  
**Versión:** NEVEN v3.2  
**Total de funciones documentadas:** 200+ (R: 90+ procedimientos, Julia: 61 procedimientos, Python/Sistema: 50+ endpoints)

---

## Tabla de Contenidos

- [Introducción](#introducción)
- [Convención de Prefijos](#convención-de-prefijos)
- [Funciones R](#funciones-r)
  - [Regresión](#regresión)
  - [Análisis de Datos](#análisis-de-datos)
  - [Funciones Interactivas](#funciones-interactivas)
  - [Series de Tiempo](#series-de-tiempo)
  - [Gráficos](#gráficos)
  - [Matemáticas y Álgebra Lineal](#matemáticas-y-álgebra-lineal)
  - [Funciones Auxiliares](#funciones-auxiliares)
  - [Datos](#datos)
- [Funciones Julia](#funciones-julia)
  - [Álgebra Lineal — J.Algebra](#álgebra-lineal--jalgebra)
  - [Cálculo Numérico — J.Calculo](#cálculo-numérico--jcalculo)
  - [Ecuaciones Diferenciales — J.EDO](#ecuaciones-diferenciales--jedo)
  - [Clasificación/KNN — J.KNN](#clasificaciónknn--jknn)
  - [Regresión Julia — J.Regresion](#regresión-julia--jregresion)
  - [Clustering — J.Clustering](#clustering--jclustering)
  - [Estadística — J.Estadistica](#estadística--jestadistica)
  - [Optimización — J.Optimizar](#optimización--joptimizar)
  - [Transformación — J.Transformar](#transformación--jtransformar)
  - [Utilidades — J.Utilidades](#utilidades--jutilidades)
- [Funciones Python](#funciones-python)
  - [AI/LLM](#aillm)
  - [Quarto](#quarto)
- [Funciones del Sistema](#funciones-del-sistema)
  - [Ejecución](#ejecución)
  - [Pluto](#pluto)
  - [Utilidades del Sistema](#utilidades-del-sistema)
- [NEVEN Studio](#neven-studio)
  - [Tab SQL](#tab-sql)
  - [Tab Data Studio](#tab-data-studio)
  - [Tab Run Script](#tab-run-script)
  - [Tab Data Lab](#tab-data-lab)
  - [Tab Presentaciones](#tab-presentaciones)
  - [Tab IA](#tab-ia)
  - [Tab Ayuda](#tab-ayuda)
- [API HTTP Endpoints](#api-http-endpoints)
  - [Core Endpoints](#core-endpoints)
  - [AI/Chat Endpoints](#aichat-endpoints)
  - [Configuration Endpoints](#configuration-endpoints)
  - [RAG Endpoints](#rag-endpoints)
  - [Data Lab Endpoints](#data-lab-endpoints)
- [Índice Cruzado por Categoría](#índice-cruzado-por-categoría)

---

## Introducción

Este diccionario cataloga todas las funciones disponibles en NEVEN v3.2 para el usuario de Excel. NEVEN es un add-in XLL políglota que integra tres motores de scripting:

- **R 4.4.1** — Estadística, econometría, visualización
- **Julia 1.12.6** — Cálculo numérico, optimización, machine learning
- **Python 3.12** — AI/LLM, automatización, conectividad

Cada función se invoca como una fórmula de celda usando el prefijo correspondiente al lenguaje. El parámetro `TipoOutput` (presente en la mayoría de funciones) permite seleccionar qué resultado devolver; use `TipoOutput=0` para ver la lista de procedimientos disponibles.

### Modos de uso

NEVEN ofrece dos modos de interacción:

1. **Fórmulas de celda** — Funciones UDF invocadas desde celdas de Excel
2. **NEVEN Studio** — Interfaz standalone con 7 tabs especializados (SQL, Data Studio, Run Script, Data Lab, Presentaciones, IA, Ayuda)

## Convención de Prefijos

| Prefijo | Lenguaje | Ejemplo |
|---------|----------|---------|
| `=R.` | R | `=R.MR_Lineal(A1:A20, B1:D20, , , , , , 1)` |
| `=J.` | Julia | `=J.Algebra(A1:C3, , 4)` |
| `=P.` | Python | `=P.ai_call(A1:B10, "analizar")` |
| `=NEVEN.` | Sistema | `=NEVEN.r("summary(cars)")` |

Para funciones que generan visualizaciones HTML, use el visor: `=NEVEN.v(R.funcion(...))`.

---

## Funciones R

### Regresión

#### MR_Lineal

**Nombre Excel:** `=R.MR_Lineal(SetDatosY, SetDatosX, Categorica, Escala, Filtro, SetDatosPredecir, Constante, TipoOutput, Ponderadores)`

**Descripción:** Estima un modelo de regresión lineal múltiple por mínimos cuadrados ordinarios (OLS).

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosY | rango | (requerido) | Variable dependiente (con encabezado) |
| SetDatosX | rango | (requerido) | Variables independientes (con encabezados) |
| Categorica | número | 0 | Columnas categóricas (0=ninguna) |
| Escala | número | 0 | Estandarizar datos (0=No, 1=Sí) |
| Filtro | rango | 0 | Vector filtro (0=incluir, 1=excluir) |
| SetDatosPredecir | rango | NULL | Datos para predicción fuera de muestra |
| Constante | número | 1 | Incluir intercepto (1=Sí, 0=No) |
| TipoOutput | número | 1 | Tipo de resultado (ver tabla) |
| Ponderadores | rango | NULL | Pesos para regresión ponderada |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos disponibles |
| 1 | Modelo estimado (tabla stargazer con IC 95%) |
| 2 | Predicción dentro de muestra |
| 3 | Predicción fuera de muestra |
| 4 | Efectos marginales |
| 5 | Factor de inflación de varianza (VIF) |
| 6 | Test de heterocedasticidad (Breusch-Pagan) |
| 7 | Errores estándar robustos |
| 8 | Observaciones de influencia |
| 9 | Información de ejecución |
| 11 | Resumen del modelo (summary) |
| 12 | Residuos |

**Ejemplo:**

```
=R.MR_Lineal(A1:A20, B1:D20, , , , , , 1)
```

**Paquetes requeridos:** `stargazer`, `margins`, `usdm`, `lmtest`, `sandwich`

---

#### MR_Binario.C

**Nombre Excel:** `=R.MR_Binario.C(SetDatosY, SetDatosX, Categorica, Filtro, Escala, SetDatosPredecir, TipoModelo, TipoOutput)`

**Descripción:** Estima un modelo de regresión binaria (Logit o Probit) para variables dependientes dicotómicas.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosY | rango | (requerido) | Variable dependiente binaria (0/1) |
| SetDatosX | rango | (requerido) | Variables independientes |
| Categorica | número | 0 | Columnas categóricas |
| Filtro | rango | 0 | Vector filtro |
| Escala | número | 0 | Estandarizar datos |
| SetDatosPredecir | rango | NULL | Datos para predicción |
| TipoModelo | número | 0 | 0=Logit, 1=Probit |
| TipoOutput | número | 1 | Tipo de resultado |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Modelo estimado (stargazer) |
| 2 | Probabilidad estimada (dentro de muestra) |
| 3 | Predicción fuera de muestra |
| 4 | Test de Hosmer-Lemeshow |
| 5 | Efectos marginales |
| 6 | ANOVA (Chi-cuadrado) |
| 7 | Dataset del modelo |
| 8 | Información de ejecución |

**Paquetes requeridos:** `stargazer`, `ResourceSelection`, `margins`

---

#### MR_Poisson.C

**Nombre Excel:** `=R.MR_Poisson.C(SetDatosY, SetDatosX, Categorica, Filtro, TipoOutput, SetDatosPredecir, Constante)`

**Descripción:** Estima un modelo de regresión Poisson para datos de conteo.

**Paquetes requeridos:** `stargazer`, `sandwich`, `margins`

---

#### MR_Tobit.C

**Nombre Excel:** `=R.MR_Tobit.C(SetDatosY, SetDatosX, Categorica, Filtro, DirTruncamiento, ValorTruncamiento, TipoOutput, SetDatosPredecir)`

**Descripción:** Estima un modelo Tobit para variables dependientes censuradas/truncadas.

**Paquetes requeridos:** `VGAM`, `ResourceSelection`, `margins`

---

#### MR_PanelData.C

**Nombre Excel:** `=R.MR_PanelData.C(SetDatosY, SetDatosX, Variable_i, Variable_t, Filtro, TipoOutput)`

**Descripción:** Estima modelos de datos de panel (pooling, within, between, random effects).

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Comparación de modelos (OLS, Pooling, Within, Between, Random) |
| 2 | Efectos fijos individuales |
| 3 | Test F (Within vs OLS) |
| 4 | Test de Hausman (Within vs Random) |
| 5 | Test F (efectos temporales) |
| 6-9 | Tests de Breusch-Pagan (tiempo, individual, two-ways) |
| 10-11 | Tests de dependencia cross-seccional |
| 12 | Test de autocorrelación (Breusch-Godfrey) |
| 13 | Test de raíz unitaria (ADF) |
| 14 | Información de ejecución |
| 15 | Dataset del modelo |

**Paquetes requeridos:** `plm`, `stargazer`, `tseries`

---

#### MR_SVM

**Nombre Excel:** `=R.MR_SVM(SetDatosY, SetDatosX, Filtro, pkernel, ptype, TipoOutput)`

**Descripción:** Estima un modelo de Support Vector Machine (SVM) para clasificación o regresión.

**Paquetes requeridos:** `e1071`

---

#### MR_2SLS (Nuevo en v3.2)

**Nombre Excel:** `=R.MR_2SLS(SetDatosY, SetDatosX, Instrumentos, TipoOutput)`

**Descripción:** Regresión por mínimos cuadrados en dos etapas (2SLS) para variables endógenas.

**Paquetes requeridos:** `AER`, `stargazer`

---

#### MR_HECKIT (Nuevo en v3.2)

**Nombre Excel:** `=R.MR_HECKIT(SetDatosY, SetDatosX, SetDatosSeleccion, TipoOutput)`

**Descripción:** Modelo de selección de Heckman (corrección de sesgo de selección).

**Paquetes requeridos:** `sampleSelection`, `stargazer`

---

#### AD_ArbolDeDecision.C

**Nombre Excel:** `=R.AD_ArbolDeDecision.C(SetDatosY, SetDatosX, Categorica, Escala, Filtro, TipoOutput, SetDatosPredecir)`

**Descripción:** Construye un árbol de decisión para clasificación o regresión.

**Paquetes requeridos:** `rpart`, `rpart.plot`

---

### Análisis de Datos

#### AD_ACP.C

**Nombre Excel:** `=R.AD_ACP.C(SetDatosX, Escala, Filtro, TipoOutput, SetDatosPredecir)`

**Descripción:** Análisis de Componentes Principales (PCA) para reducción de dimensionalidad.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Matriz de correlación |
| 2 | Matriz de covarianza |
| 3 | Gráfico de correlaciones |
| 4 | Loadings + varianza explicada |
| 5 | Coordenadas de individuos (scores) |
| 6 | COS² de individuos |
| 7 | Contribución de individuos |
| 8 | Valores propios y varianza acumulada |
| 9 | COS² de variables |
| 10 | Contribución de variables |
| 11 | Proyección fuera de muestra |
| 12 | Biplot |

**Paquetes requeridos:** `PerformanceAnalytics`

---

#### AD_KMedias.C

**Nombre Excel:** `=R.AD_KMedias.C(SetDatosX, Escala, Filtro, K, Koptimo, Semilla, TipoModelo, TipoOutput)`

**Descripción:** Algoritmo de K-Medias para agrupamiento (clustering).

**Paquetes requeridos:** `cluster`

---

#### AD_ClusteringJerarquico (Nuevo en v3.2)

**Nombre Excel:** `=R.AD_ClusteringJerarquico(SetDatosX, Metodo, NumClusters, TipoOutput)`

**Descripción:** Clustering jerárquico aglomerativo con dendrograma.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Dendrograma |
| 2 | Asignación de clusters |
| 3 | Estadísticas por cluster |
| 4 | Matriz de distancias |

**Paquetes requeridos:** `cluster`, `dendextend`

---

#### AD_NonParRolCor

**Nombre Excel:** `=R.AD_NonParRolCor(SetDatosX, MCSim, Np, Widthwin, prob)`

**Descripción:** Correlación rodante no paramétrica con significancia estadística (Monte Carlo).

**Paquetes requeridos:** `NonParRolCor`, `gtools`, `pracma`, `doParallel`

---

#### TM_TextMining

**Nombre Excel:** `=R.TM_TextMining(RUTA_FL, RUTA_SW, MAXWORDS, QPALABRASRESUMEN, IDIOMA, TipoOutput)`

**Descripción:** Análisis de minería de texto con nube de palabras y frecuencias.

**Paquetes requeridos:** `tm`, `SnowballC`, `wordcloud`, `RColorBrewer`

---

#### TM_TextAnalysis (Nuevo en v3.2)

**Nombre Excel:** `=R.TM_TextAnalysis(SetDatosTexto, Idioma, TipoOutput)`

**Descripción:** Análisis de sentimiento y extracción de entidades de texto.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Análisis de sentimiento |
| 2 | Extracción de entidades |
| 3 | Resumen automático |
| 4 | Frecuencia de n-gramas |

**Paquetes requeridos:** `tidytext`, `textdata`, `sentimentr`

---

### Funciones Interactivas

> Las funciones interactivas generan HTML y se visualizan con el visor WebView2.
> Sintaxis: `=NEVEN.v(R.funcion(...))`

#### Pivot

**Nombre Excel:** `=NEVEN.v(R.Pivot(SetDatosX, TipoOutput))`

**Descripción:** Tabla pivote interactiva con drag-and-drop (rpivotTable).

**Paquetes requeridos:** `rpivotTable`, `htmlwidgets`

---

#### Esquisse

**Nombre Excel:** `=NEVEN.v(R.Esquisse(SetDatosX, TipoOutput))`

**Descripción:** Explorador interactivo de datos con selección de ejes, tipo de gráfico y color.

**Paquetes requeridos:** `plotly`, `htmlwidgets`, `jsonlite`

---

#### D3, Dashboard, Map

**Nombre Excel:** `=NEVEN.v(R.D3(...))`, `=NEVEN.v(R.Dashboard(...))`, `=NEVEN.v(R.Map(...))`

**Descripción:** Funciones interactivas adicionales para visualización D3.js, dashboards y mapas geográficos.

---

### Series de Tiempo

#### ST_SeriesTemporales

**Nombre Excel:** `=R.ST_SeriesTemporales(SetDatosX, Periodicidad, TipoOutput)`

**Descripción:** Tests y descomposición de series temporales (cointegración, raíz unitaria, autocorrelación).

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Test de cointegración (Phillips-Ouliaris) |
| 2 | Test de raíz unitaria (ADF) |
| 3 | Test de Phillips-Perron |
| 4 | Test de Jarque-Bera (normalidad) |
| 5 | Autocorrelación (ACF + PACF + límites) |
| 6 | Descomposición aditiva (tendencia, estacional, residuo) |
| 7 | Descomposición multiplicativa |

**Paquetes requeridos:** `tseries`

---

#### ST_Autoregresivos

**Nombre Excel:** `=R.ST_Autoregresivos(SetDatosX, Periodicidad, TipoOutput, OrdenP, OrdenD, OrdenQ)`

**Descripción:** Modelos autoregresivos: ARMA, ARIMA, GARCH.

**Paquetes requeridos:** `tseries`

---

#### ST_Filtro

**Nombre Excel:** `=R.ST_Filtro(SetDatosX, Periodicidad, TipoModelo, Drift, RaizUnitaria, TipoOutput)`

**Descripción:** Aplica filtros de series de tiempo (Hodrick-Prescott, Baxter-King, etc.).

**Paquetes requeridos:** `tseries`, `mFilter`

---

#### ST_VAR (Nuevo en v3.2)

**Nombre Excel:** `=R.ST_VAR(SetDatosX, Lags, TipoOutput)`

**Descripción:** Modelo VAR (Vector Autoregressive) para sistemas de series temporales.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Coeficientes del modelo |
| 2 | Impulso-respuesta |
| 3 | Descomposición de varianza |
| 4 | Test de causalidad de Granger |

**Paquetes requeridos:** `vars`, `stargazer`

---

#### ST_ECM (Nuevo en v3.2)

**Nombre Excel:** `=R.ST_ECM(SetDatosY, SetDatosX, TipoOutput)`

**Descripción:** Modelo de corrección de errores (ECM) para cointegración.

**Paquetes requeridos:** `urca`, `stargazer`

---

### Gráficos

#### GR_QuickPlot

**Nombre Excel:** `=R.GR_QuickPlot(SetDatosX, SetDatosY, TipoGrafico, Titulo, TipoOutput)`

**Descripción:** Genera gráficos rápidos (R base y ggplot2) para visualización en WebView2.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Barras (R base) |
| 2 | Líneas (R base) |
| 3 | Scatter (R base) |
| 4 | Histograma (R base) |
| 5 | Box Plot (R base) |
| 6 | Pie (R base) |
| 7 | ggplot2 Barras (interactivo) |
| 8 | ggplot2 Líneas (interactivo) |
| 9 | ggplot2 Scatter (interactivo) |

**Paquetes requeridos:** `ggplot2`, `plotly`, `htmlwidgets`

---

#### Gráficos Studio (Nuevo en v3.2)

Las siguientes funciones están disponibles en NEVEN Studio para generación de gráficos interactivos:

| Función | Descripción |
|---------|-------------|
| `GR_Barras` | Gráfico de barras Plotly |
| `GR_BoxPlot` | Box plot interactivo |
| `GR_Correlaciones` | Matriz de correlaciones con heatmap |
| `GR_Histograma` | Histograma con distribución |
| `GR_Lineas` | Gráfico de líneas temporal |
| `GR_Mapa` | Mapa geográfico interactivo |
| `GR_Scatter` | Scatter plot con regresión |
| `GR_SeriesTiempo` | Gráfico de series temporales |

---

### Matemáticas y Álgebra Lineal

#### MM_Algebra.C

**Nombre Excel:** `=R.MM_Algebra.C(SetDatosX, TipoOutput)`

**Descripción:** Operaciones de álgebra lineal sobre matrices.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Factorización Cholesky |
| 2 | Valores propios |
| 3 | Vectores propios |
| 4 | Descomposición QR |
| 5 | Matriz inversa |
| 6 | Descomposición SVD (U) |
| 7 | Diagonal |
| 8 | Transpuesta |

---

### Funciones Auxiliares

#### FX_AleatorioUniforme

**Nombre Excel:** `=R.FX_AleatorioUniforme(N, Min, Max, Semilla, Histograma)`

**Descripción:** Genera N datos aleatorios con distribución uniforme.

---

#### FX_AleatorioNormal

**Nombre Excel:** `=R.FX_AleatorioNormal(N, Mu, Sigma, Semilla, Histograma)`

**Descripción:** Genera N datos aleatorios con distribución normal.

---

#### FX_Distancias

**Nombre Excel:** `=R.FX_Distancias(SetDatosX, pEscalaDatos, pTipoDistancia, pPotenciaMinkowski)`

**Descripción:** Calcula la matriz de distancias entre observaciones.

---

#### FX_Muestreo

**Nombre Excel:** `=R.FX_Muestreo(SetDatos, Semilla, Porc_Muestral, TipoOutput)`

**Descripción:** Divide un dataset en muestras de entrenamiento y prueba.

---

### Datos

#### DS_Wooldridge

**Nombre Excel:** `=R.DS_Wooldridge()`

**Descripción:** Explora y carga datasets de la librería `wooldridge` (econometría) con interfaz gráfica.

**Paquetes requeridos:** `wooldridge`, `svDialogs`

---

#### DS_ObtenerDatos

**Nombre Excel:** `=R.DS_ObtenerDatos(pTotalPaquetes)`

**Descripción:** Obtiene datasets de paquetes R instalados mediante diálogo interactivo.

---

## Funciones Julia

Todas las funciones Julia se invocan con el prefijo `=J.` seguido del nombre corto (alias).

> **Nota sobre rendimiento:** NEVEN incluye una sysimage precompilada de Julia (`neven_julia.dll`, 415MB) que reduce el tiempo de inicio de minutos a segundos.

### Álgebra Lineal — J.Algebra

**Nombre Excel:** `=J.Algebra(Matriz, VectorB, TipoOutput)`

**Descripción:** Operaciones avanzadas de álgebra lineal.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Factorización LU (L y U separadas por NaN) |
| 2 | Factorización QR (Q y R separadas por NaN) |
| 3 | Descomposición SVD (valores singulares) |
| 4 | Valores propios |
| 5 | Vectores propios |
| 6 | Determinante |
| 7 | Rango |
| 8 | Normas (Frobenius, 1, 2, Inf) |
| 9 | Número de condición |
| 10 | Pseudoinversa Moore-Penrose |
| 11 | Traza |
| 12 | Resolver Ax=b (requiere VectorB) |

---

### Cálculo Numérico — J.Calculo

**Nombre Excel:** `=J.Calculo(VectorX, VectorY, Parametro, TipoOutput)`

**Descripción:** Métodos numéricos de cálculo: derivadas, integrales, raíces, interpolación.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Derivada numérica (diferencias finitas) |
| 2 | Integral por trapecio |
| 3 | Integral por Simpson |
| 4 | Raíz por bisección |
| 5 | Interpolación lineal en punto Parametro |
| 6 | Interpolación de Lagrange en punto Parametro |
| 7 | Serie de Taylor evaluada en Parametro |

---

### Ecuaciones Diferenciales — J.EDO

**Nombre Excel:** `=J.EDO(VectorX, VectorY, Parametro, TipoOutput)`

**Descripción:** Resolución numérica de ecuaciones diferenciales ordinarias.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Euler explícito (dy/dt = -y) |
| 2 | Runge-Kutta 4 (dy/dt = -y) |
| 3 | Sistema de EDOs RK4 (oscilador) |
| 4 | EDO 2do orden RK4 (y'' + y = 0) |

---

### Clasificación/KNN — J.KNN

**Nombre Excel:** `=J.KNN(SetDatosX, SetDatosY, K, TipoOutput)`

**Descripción:** Clasificación K-Nearest Neighbors con validación leave-one-out.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Clasificación con accuracy |
| 2 | Precisión, recall y F1 por clase |
| 3 | Matriz de confusión |
| 4 | Predicciones (real vs predicho) |
| 5 | Distancias al vecino más cercano |

---

### Regresión Julia — J.Regresion

**Nombre Excel:** `=J.Regresion(SetDatosX, SetDatosY, Parametro, TipoOutput)`

**Descripción:** Regresión lineal múltiple con diagnósticos.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Coeficientes + R² |
| 2 | Valores ajustados (predicción) |
| 3 | Residuos |
| 4 | Resumen completo (SE, t-stats, R²adj) |
| 5 | Intervalos de confianza 95% |

---

### Clustering — J.Clustering

**Nombre Excel:** `=J.Clustering(SetDatosX, K, Semilla, TipoOutput)`

**Descripción:** Algoritmo K-Medias implementado en Julia.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Asignación de clusters |
| 2 | Centros de clusters |
| 3 | Asignación (igual que 1) |
| 4 | WCSS (variabilidad intra-cluster) |
| 5 | Método del codo (WCSS para K=1..K) |
| 6 | Descriptivas por cluster (media, desviación) |

---

### Estadística — J.Estadistica

**Nombre Excel:** `=J.Estadistica(SetDatosX, SetDatosY, TipoOutput)`

**Descripción:** Estadística descriptiva, correlación, normalización y detección de outliers.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Descriptiva completa (N, Media, Std, Min, Q1, Mediana, Q3, Max) |
| 2 | Matriz de correlación |
| 3 | Matriz de covarianza |
| 4 | Test t de Student (dos muestras) |
| 5 | Normalización Min-Max [0,1] |
| 6 | Estandarización Z-Score |
| 7 | Percentiles (1, 5, 10, 25, 50, 75, 90, 95, 99) |
| 8 | Detección de outliers IQR (Q1, Q3, IQR, #outliers) |

---

### Optimización — J.Optimizar

**Nombre Excel:** `=J.Optimizar(Matriz, Vector, Parametro, MaxIter, TipoOutput)`

**Descripción:** Algoritmos de optimización numérica.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Descenso de gradiente (min ½x'Ax - b'x) |
| 2 | Gradiente con momentum |
| 3 | Método de Newton (1 paso: A\b) |
| 4 | Sección áurea 1D (min x² en [a,b]) |
| 5 | Simplex (programación lineal) |
| 6 | Mínimos cuadrados no-negativos (NNLS) |
| 7 | Programación cuadrática (min ½x'Qx + c'x, x≥0) |

---

### Transformación — J.Transformar

**Nombre Excel:** `=J.Transformar(Datos, Columna, Valor, TipoOutput)`

**Descripción:** Operaciones de transformación y manipulación de datos.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Transponer |
| 2 | Ordenar por columna |
| 3 | Filtrar filas (donde columna == Valor) |
| 4 | Seleccionar columnas |
| 5 | Valores únicos |
| 6 | Tabla de frecuencias |

---

### Utilidades — J.Utilidades

**Nombre Excel:** `=J.Utilidades(P1, P2, P3, TipoOutput)`

**Descripción:** Funciones utilitarias generales.

**TipoOutput:**

| Valor | Resultado | P1 | P2 | P3 |
|-------|-----------|----|----|-----|
| 0 | Lista de procedimientos | — | — | — |
| 1 | Fecha y hora actual | — | — | — |
| 2 | Secuencia numérica | inicio | fin | paso |
| 3 | Aleatorios Normal | N | media | desviación |
| 4 | Aleatorios Uniforme | N | min | max |
| 5 | Redondear datos | datos/valor | decimales | — |

---

## Funciones Python

Las funciones Python se invocan con el prefijo `=P.`.

### AI/LLM

#### ai_call

**Nombre Excel:** `=P.ai_call(data_str, prompt_name, context)`

**Descripción:** Invoca un modelo de lenguaje (LLM) con datos de Excel y un template de prompt. Soporta OpenAI, Azure, Anthropic (Claude), Ollama y LM Studio.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| data_str | rango/texto | (requerido) | Datos de Excel (se convierten a texto) |
| prompt_name | texto | (requerido) | Nombre del template (sin .txt) |
| context | texto | "" | Contexto adicional opcional |

**Placeholders en templates:**
- `{{datos}}` — Se reemplaza con data_str
- `{{resultado}}` — Sinónimo de {{datos}}
- `{{contexto}}` — Se reemplaza con context

**Ejemplo:**

```
=P.ai_call(A1:B10, "analizar", "datos de ventas Q1 2024")
```

---

#### ai_setup

**Nombre Excel:** `=NEVEN.v(P.ai_setup())`

**Descripción:** Genera un formulario HTML de configuración AI que se muestra en el visor WebView2.

---

#### ai_list_prompts

**Nombre Excel:** `=P.ai_list_prompts()`

**Descripción:** Lista los nombres de todos los templates de prompts disponibles.

---

### Quarto

#### quarto_render

**Nombre Excel:** `=P.quarto_render(file_path, format)`

**Descripción:** Renderiza un documento Quarto (.qmd) y retorna la ruta del archivo generado.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| file_path | texto | (requerido) | Ruta completa al archivo .qmd |
| format | texto | "html" | Formato: html, pdf o docx |

---

## Funciones del Sistema

Las funciones del sistema se invocan con el prefijo `=NEVEN.`.

### Ejecución

#### NEVEN.r()

**Nombre Excel:** `=NEVEN.r(expresion)`

**Descripción:** Ejecuta una expresión R y retorna el resultado a la celda de Excel.

**Ejemplo:**

```
=NEVEN.r("mean(c(1,2,3,4,5))")
```

---

#### NEVEN.j()

**Nombre Excel:** `=NEVEN.j(expresion)`

**Descripción:** Ejecuta una expresión Julia y retorna el resultado a la celda de Excel.

---

#### NEVEN.py() (Nuevo en v3.2)

**Nombre Excel:** `=NEVEN.py(expresion)`

**Descripción:** Ejecuta una expresión Python y retorna el resultado a la celda de Excel.

---

#### NEVEN.v()

**Nombre Excel:** `=NEVEN.v(expresion)`

**Descripción:** Ejecuta una expresión y muestra el resultado en el visor HTML (WebView2).

---

#### NEVEN.q()

**Nombre Excel:** `=NEVEN.q(ruta)`

**Descripción:** Renderiza un documento Quarto (.qmd) y muestra el resultado.

---

### Pluto

#### NEVEN.pluto.start()

**Descripción:** Inicia el servidor Pluto.jl para notebooks reactivos de Julia.

---

#### NEVEN.pluto.stop()

**Descripción:** Detiene el servidor Pluto.jl.

---

#### NEVEN.pluto.status()

**Descripción:** Consulta el estado actual del servidor Pluto.

---

#### NEVEN.pluto.data()

**Nombre Excel:** `=NEVEN.pluto.data(rango)`

**Descripción:** Envía datos de Excel a un notebook Pluto activo via TSV.

---

### Utilidades del Sistema

#### NEVEN.notebook.open()

**Descripción:** Abre un notebook Pluto específico.

---

#### NEVEN.notebook.list()

**Descripción:** Lista los notebooks Pluto disponibles.

---

#### NEVEN.editor()

**Descripción:** Abre el editor de código integrado.

---

#### NEVEN.about()

**Descripción:** Muestra información sobre la versión de NEVEN instalada.

---

#### NEVEN.help()

**Descripción:** Muestra la ayuda general de NEVEN.

---

## NEVEN Studio

NEVEN Studio es un modo standalone implementado como Office Add-in (HTML/JS) que extiende las capacidades de NEVEN más allá de las fórmulas de celda. Se comunica con un servidor HTTP Python (puerto 5555).

### Tab SQL

**Descripción:** Permite ejecutar consultas SQL sobre datos de Excel utilizando DuckDB embebido.

**Características:**
- Motor DuckDB embebido con soporte SQL completo
- Carga automática de datos desde rangos de Excel
- Autocompletado de tablas y columnas
- Exportación de resultados a CSV/Excel

**Ejemplo:**

```sql
-- Cargar datos desde rango de Excel
SELECT * FROM excel_range('Sheet1!A1:D100')
WHERE valor > 1000
ORDER BY fecha DESC
```

---

### Tab Data Studio

**Descripción:** Entorno de edición visual para transformación de datos con generación automática de código R/Python.

**Características:**
- Interfaz drag-and-drop para transformaciones
- Preview de datos en tiempo real
- Generación de código reproducible
- Integración con el motor R

---

### Tab Run Script

**Descripción:** Editor de código con soporte para R, Julia y Python.

**Características:**
- Syntax highlighting para R, Julia, Python
- Ejecución de scripts completos o por sección
- Visualización de resultados en panel lateral
- Guardado de scripts en el filesystem

---

### Tab Data Lab

**Descripción:** Pipeline de descubrimiento de datos con tres sub-tabs.

**Sub-tabs:**
- **Preguntas:** Motor de lenguaje natural para consultas sobre datos
- **Explorador:** Visualización interactiva de datasets cargados
- **Código:** Generación automática de código R/Python basada en preguntas

**Características:**
- Integración con motor RAG para contexto semántico
- Traducción automática de términos técnicos (ES↔EN↔PT↔FR)
- Generación de visualizaciones Plotly
- Descarga de resultados en múltiples formatos

---

### Tab Presentaciones

**Descripción:** Generador de presentaciones HTML autocontenidas usando reveal.js.

**Características:**
- Creación de slides desde datos de Excel
- Inserción de gráficos Plotly
- Temas personalizables
- Exportación a HTML standalone

---

### Tab IA

**Descripción:** Asistente de inteligencia artificial contextual.

**Características:**
- Integración con Claude (Anthropic), OpenAI, Azure, Ollama
- Contexto automático del rango seleccionado en Excel
- Generación de código R/Julia/Python basada en descripción natural
- Explicación de resultados estadísticos
- Renderizado de fórmulas LaTeX
- Historial de conversación persistente

**Proveedores soportados:**
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Azure OpenAI
- Ollama (modelos locales)
- LM Studio (modelos locales)

---

### Tab Ayuda

**Descripción:** Sistema de ayuda integrado con búsqueda semántica.

**Características:**
- Búsqueda semántica sobre 200+ funciones
- Ejemplos interactivos ejecutables
- Acceso al motor RAG para consultas contextuales
- Documentación de paquetes R/Julia requeridos

---

## API HTTP Endpoints

El servidor HTTP de NEVEN (puerto 5555) expone los siguientes endpoints para NEVEN Studio y automatización.

### Core Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/run_script` | Ejecuta script R/Julia/Python |
| POST | `/api/sql` | Ejecuta query SQL en DuckDB |
| POST | `/api/load` | Carga datos en DuckDB |
| POST | `/api/load_file` | Carga archivo CSV/Parquet/JSON |
| GET | `/api/tables` | Lista tablas en DuckDB |
| GET | `/api/health` | Estado del servidor |
| POST | `/api/shutdown` | Apagado limpio del servidor |

### AI/Chat Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/ai/chat` | Envía mensaje al LLM con contexto RAG |
| POST | `/api/ai/context` | Recibe contexto de Excel para el Tab IA |
| POST | `/api/ai/chart` | Genera gráfico HTML desde descripción |

### Configuration Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/config/ai-profiles` | Lista perfiles de IA |
| POST | `/api/config/ai-profiles` | Crea perfil de IA |
| POST | `/api/config/ai-profiles/{id}/activate` | Activa perfil |
| POST | `/api/config/ai-profiles/{id}/test` | Prueba conexión |
| GET | `/api/config/db-connections` | Lista conexiones DB |
| POST | `/api/config/db-connections` | Crea conexión DB |
| GET | `/api/config/prompts` | Lista prompts disponibles |
| POST | `/api/config/prompts` | Guarda prompt |
| POST | `/api/config/reload` | Recarga configuración |

### RAG Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/rag/stats` | Estadísticas del índice RAG |
| GET | `/api/rag/documents` | Lista documentos indexados |
| POST | `/api/rag/query` | Consulta semántica al índice |
| POST | `/api/rag/index` | Indexa nuevo documento |
| DELETE | `/api/rag/documents/{id}` | Elimina documento del índice |

### Data Lab Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/datalab/question` | Responde pregunta en lenguaje natural |
| POST | `/api/datalab/code` | Genera código desde descripción |
| GET | `/api/datalab/datasets` | Lista datasets cargados |

### Ontology Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/ontology/domains` | Lista dominios de ontología |
| GET | `/api/ontology/domain/{id}/stats` | Estadísticas de dominio |
| GET | `/api/ontology/search?q=term` | Búsqueda en knowledge graph |

### Package Manager Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/packages/status` | Estado de paquetes R/Julia |
| GET | `/api/packages/function/{id}` | Info de función específica |
| POST | `/api/packages/install` | Instala paquete |

---

## Índice Cruzado por Categoría

### Regresión

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.MR_Lineal | R | Regresión lineal múltiple (OLS) |
| R.MR_Binario.C | R | Regresión logística/probit |
| R.MR_Poisson.C | R | Regresión Poisson (conteo) |
| R.MR_Tobit.C | R | Regresión Tobit (censurada) |
| R.MR_PanelData.C | R | Datos de panel |
| R.MR_2SLS | R | Mínimos cuadrados en 2 etapas |
| R.MR_HECKIT | R | Modelo de selección de Heckman |
| J.Regresion | Julia | Regresión lineal con diagnósticos |

### Clasificación / Machine Learning

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.MR_SVM | R | Support Vector Machine |
| R.AD_ArbolDeDecision.C | R | Árboles de decisión |
| J.KNN | Julia | K-Nearest Neighbors |

### Clustering

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.AD_KMedias.C | R | K-Medias (R) |
| R.AD_ClusteringJerarquico | R | Clustering jerárquico |
| J.Clustering | Julia | K-Medias (Julia) |

### Estadística Descriptiva

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.AD_ACP.C | R | Análisis de Componentes Principales |
| R.DB_Pivote | R | Tablas agrupadas con agregación |
| J.Estadistica | Julia | Descriptiva, correlación, tests |

### Series de Tiempo

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.ST_SeriesTemporales | R | Tests y descomposición |
| R.ST_Autoregresivos | R | ARMA, ARIMA, GARCH |
| R.ST_Filtro | R | Filtros HP, BK, CF, BW, TR |
| R.ST_VAR | R | Vectores autoregresivos |
| R.ST_ECM | R | Modelo de corrección de errores |

### Álgebra Lineal

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.MM_Algebra.C | R | Operaciones matriciales (R) |
| J.Algebra | Julia | Álgebra lineal avanzada |

### Cálculo Numérico

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| J.Calculo | Julia | Derivadas, integrales, raíces |
| J.EDO | Julia | Ecuaciones diferenciales |

### Optimización

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| J.Optimizar | Julia | Gradiente, Newton, Simplex, NNLS, QP |

### Visualización

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.GR_QuickPlot | R | Gráficos rápidos (R base + ggplot2) |
| R.Pivot | R | Tabla pivote interactiva |
| R.Esquisse | R | Explorador interactivo de datos |
| GR_* (Studio) | R | Gráficos Plotly interactivos |

### Text Mining

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.TM_TextMining | R | Minería de texto, nube de palabras |
| R.TM_TextAnalysis | R | Análisis de sentimiento |

### AI / LLM

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| P.ai_call | Python | Invocar modelo de lenguaje |
| P.ai_setup | Python | Configurar AI |
| P.ai_list_prompts | Python | Listar prompts disponibles |
| Tab IA (Studio) | Python | Asistente AI contextual |

### Datos / Transformación

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.DS_Wooldridge | R | Datasets de econometría |
| J.Transformar | Julia | Transponer, ordenar, filtrar |
| Tab SQL (Studio) | SQL | Consultas SQL sobre Excel |

---

## Plantilla para nuevas funciones

Para agregar una nueva función al diccionario, copie esta plantilla:

```markdown
#### NombreFuncion

**Nombre Excel:** `=PREFIJO.NombreFuncion(param1, param2, TipoOutput)`

**Descripción:** Breve descripción de lo que hace la función.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| param1 | tipo | default | descripción |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Resultado principal |

**Ejemplo:**

\```
=PREFIJO.NombreFuncion(A1:A10, , 1)
\```

**Resultado esperado:** Descripción del resultado.

**Paquetes requeridos:** `paquete1`, `paquete2`
```

---

*Documento generado para NEVEN v3.2 — Add-in XLL políglota para Microsoft Excel*  
*BukloLAB — Tesis de Maestría, Universidad de Costa Rica*
