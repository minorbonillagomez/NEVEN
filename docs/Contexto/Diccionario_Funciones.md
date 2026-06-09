# Diccionario de Funciones NEVEN

**Última actualización:** 2025-01-15  
**Total de funciones documentadas:** 95 (R: 32 funciones, Julia: 52 procedimientos en 11 módulos, Python: 4 funciones, Sistema: 13 funciones)

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
  - [ai_call](#ai_call)
  - [ai_setup](#ai_setup)
  - [ai_list_prompts](#ai_list_prompts)
  - [quarto_render](#quarto_render)
- [Funciones del Sistema](#funciones-del-sistema)
  - [Ejecución](#ejecución)
  - [Pluto](#pluto)
  - [Utilidades del Sistema](#utilidades-del-sistema)
- [Índice Cruzado por Categoría](#índice-cruzado-por-categoría)

---

## Introducción

Este diccionario cataloga todas las funciones disponibles en NEVEN para el usuario de Excel. Cada función se invoca como una fórmula de celda usando el prefijo correspondiente al lenguaje. El parámetro `TipoOutput` (presente en la mayoría de funciones) permite seleccionar qué resultado devolver; use `TipoOutput=0` para ver la lista de procedimientos disponibles.

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

Datos dummy (A1:D20):

| Y | X1 | X2 | X3 |
|---|----|----|-----|
| 10 | 2 | 5 | 1 |
| 15 | 3 | 8 | 2 |
| 20 | 5 | 12 | 3 |

**Resultado esperado:** Tabla con coeficientes, errores estándar, intervalos de confianza y R².

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

**Ejemplo:**

```
=R.MR_Binario.C(A1:A30, B1:C30, , , , , 0, 1)
```

**Resultado esperado:** Tabla Logit con coeficientes, significancia y pseudo-R².

**Paquetes requeridos:** `stargazer`, `ResourceSelection`, `margins`

---

#### MR_Poisson.C

**Nombre Excel:** `=R.MR_Poisson.C(SetDatosY, SetDatosX, Categorica, Filtro, TipoOutput, SetDatosPredecir, Constante)`

**Descripción:** Estima un modelo de regresión Poisson para datos de conteo.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosY | rango | (requerido) | Variable de conteo |
| SetDatosX | rango | (requerido) | Variables independientes |
| Categorica | número | 0 | Columnas categóricas |
| Filtro | rango | 0 | Vector filtro |
| TipoOutput | número | 0 | Tipo de resultado |
| SetDatosPredecir | rango | NULL | Datos para predicción |
| Constante | número | 1 | Incluir intercepto |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Modelo estimado |
| 2 | Predicción en muestra |
| 3 | Predicción fuera de muestra |
| 4 | Efectos marginales |
| 5 | Bondad de ajuste (deviance) |
| 6 | Dataset del modelo |
| 7 | Información de ejecución |

**Ejemplo:**

```
=R.MR_Poisson.C(A1:A25, B1:C25, , , 1)
```

**Resultado esperado:** Tabla con coeficientes Poisson y errores robustos.

**Paquetes requeridos:** `stargazer`, `sandwich`, `margins`

---

#### MR_Tobit.C

**Nombre Excel:** `=R.MR_Tobit.C(SetDatosY, SetDatosX, Categorica, Filtro, DirTruncamiento, ValorTruncamiento, TipoOutput, SetDatosPredecir)`

**Descripción:** Estima un modelo Tobit para variables dependientes censuradas/truncadas.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosY | rango | (requerido) | Variable censurada |
| SetDatosX | rango | (requerido) | Variables independientes |
| Categorica | número | 0 | Columnas categóricas |
| Filtro | rango | 0 | Vector filtro |
| DirTruncamiento | número | 1 | Dirección: 1=superior, -1=inferior |
| ValorTruncamiento | número | 1 | Valor del punto de censura |
| TipoOutput | número | 0 | Tipo de resultado |
| SetDatosPredecir | rango | NULL | Datos para predicción |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Modelo estimado (summary) |
| 2 | Predicción en muestra |
| 3 | Predicción fuera de muestra |
| 4 | Especificación del modelo |
| 5 | Dataset del modelo |
| 6 | Información de ejecución |

**Ejemplo:**

```
=R.MR_Tobit.C(A1:A30, B1:C30, , , 1, 100, 1)
```

**Resultado esperado:** Resumen del modelo Tobit con coeficientes y significancia.

**Paquetes requeridos:** `VGAM`, `ResourceSelection`, `margins`

---

#### MR_PanelData.C

**Nombre Excel:** `=R.MR_PanelData.C(SetDatosY, SetDatosX, Variable_i, Variable_t, Filtro, TipoOutput)`

**Descripción:** Estima modelos de datos de panel (pooling, within, between, random effects).

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosY | rango | (requerido) | Variable dependiente |
| SetDatosX | rango | (requerido) | Variables independientes |
| Variable_i | rango | (requerido) | Identificador de individuo |
| Variable_t | rango | (requerido) | Identificador de tiempo |
| Filtro | rango | NULL | Vector filtro |
| TipoOutput | número | 1 | Tipo de resultado |

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

**Ejemplo:**

```
=R.MR_PanelData.C(A1:A100, B1:C100, D1:D100, E1:E100, , 1)
```

**Resultado esperado:** Tabla comparativa de 6 modelos de panel con coeficientes.

**Paquetes requeridos:** `plm`, `stargazer`, `tseries`

---

#### MR_SVM

**Nombre Excel:** `=R.MR_SVM(SetDatosY, SetDatosX, Filtro, pkernel, ptype, TipoOutput)`

**Descripción:** Estima un modelo de Support Vector Machine (SVM) para clasificación o regresión.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosY | rango | (requerido) | Variable dependiente |
| SetDatosX | rango | (requerido) | Variables independientes |
| Filtro | rango | NULL | Vector filtro |
| pkernel | número | NULL | 1=linear, 2=polynomial, 3=radial basis, 4=sigmoid |
| ptype | número | NULL | 1=C-classification, 2=nu-classification, 3=one-classification, 4=eps-regression, 5=nu-regression |
| TipoOutput | número | 0 | Tipo de resultado |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Predicción (Y estimado) |

**Ejemplo:**

```
=R.MR_SVM(A1:A50, B1:D50, , 3, 4, 1)
```

**Resultado esperado:** Vector de valores predichos por el SVM.

**Paquetes requeridos:** `e1071`

---

#### AD_ArbolDeDecision.C

**Nombre Excel:** `=R.AD_ArbolDeDecision.C(SetDatosY, SetDatosX, Categorica, Escala, Filtro, TipoOutput, SetDatosPredecir)`

**Descripción:** Construye un árbol de decisión para clasificación o regresión.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosY | rango | (requerido) | Variable dependiente |
| SetDatosX | rango | (requerido) | Variables independientes |
| Categorica | número | 0 | Columnas categóricas |
| Escala | número | 0 | Estandarizar datos |
| Filtro | rango | 0 | Vector filtro |
| TipoOutput | número | 0 | Tipo de resultado |
| SetDatosPredecir | rango | NULL | Datos para predicción |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Gráfico del árbol |
| 2 | Splits (divisiones) |
| 3 | Splits categóricos |
| 4 | Tabla de complejidad (CP) |
| 5 | Frame del modelo |
| 6 | Asignación de nodos |
| 7 | Parámetros de control |
| 8 | Predicción fuera de muestra |

**Ejemplo:**

```
=R.AD_ArbolDeDecision.C(A1:A40, B1:D40, , , , 1)
```

**Resultado esperado:** Gráfico visual del árbol de decisión.

**Paquetes requeridos:** `rpart`, `rpart.plot`

---

### Análisis de Datos

#### AD_ACP.C

**Nombre Excel:** `=R.AD_ACP.C(SetDatosX, Escala, Filtro, TipoOutput, SetDatosPredecir)`

**Descripción:** Análisis de Componentes Principales (PCA) para reducción de dimensionalidad.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos numéricos (con encabezados) |
| Escala | número | 0 | Estandarizar (0=No, 1=Sí) |
| Filtro | rango | NULL | Vector filtro |
| TipoOutput | número | 0 | Tipo de resultado |
| SetDatosPredecir | rango | NULL | Datos para proyección |

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

**Ejemplo:**

```
=R.AD_ACP.C(A1:E20, 1, , 8)
```

**Resultado esperado:** Tabla con valores propios, aporte a la varianza y acumulado.

**Paquetes requeridos:** `PerformanceAnalytics`

---

#### AD_KMedias.C

**Nombre Excel:** `=R.AD_KMedias.C(SetDatosX, Escala, Filtro, K, Koptimo, Semilla, TipoModelo, TipoOutput)`

**Descripción:** Algoritmo de K-Medias para agrupamiento (clustering).

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos numéricos |
| Escala | número | 0 | Estandarizar datos |
| Filtro | rango | 0 | Vector filtro |
| K | número | 3 | Número de clusters |
| Koptimo | número | 10 | K máximo para método del codo |
| Semilla | número | 123456 | Semilla aleatoria |
| TipoModelo | número | 1 | 1=Hartigan-Wong, 2=Lloyd, 3=Forgy, 4=MacQueen |
| TipoOutput | número | 0 | Tipo de resultado |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Cluster asignado a cada observación |
| 2 | Centros de los clusters |
| 3 | Variabilidad dentro de cada cluster |
| 4 | Variabilidad total (intra/entre clases) |
| 5 | Factores de escalamiento (mu, sigma) |
| 6 | Gap statistic (K óptimo) |
| 7 | Método del codo (WCSS por K) |
| 9 | Información de ejecución |

**Ejemplo:**

```
=R.AD_KMedias.C(A1:D50, 1, , 3, 10, 123456, 1, 1)
```

**Resultado esperado:** Vector con el cluster asignado (1, 2 o 3) para cada observación.

**Paquetes requeridos:** `cluster`

---

#### AD_KmediasClasificar

**Nombre Excel:** `=R.AD_KmediasClasificar(SetDatosPredecir, Escala, Centroides, FactorMu, FactorSigma)`

**Descripción:** Clasifica nuevas observaciones usando centroides previamente calculados con K-Medias.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosPredecir | rango | (requerido) | Nuevos datos a clasificar |
| Escala | número | 0 | Aplicar escalamiento |
| Centroides | rango | NULL | Centros obtenidos de K-Medias |
| FactorMu | número | 0 | Media de escalamiento original |
| FactorSigma | número | 1 | Desviación de escalamiento original |

**Ejemplo:**

```
=R.AD_KmediasClasificar(A1:D10, 1, F1:I4, 0, 1)
```

**Resultado esperado:** Cluster asignado para cada nueva observación.

---

#### AD_NonParRolCor

**Nombre Excel:** `=R.AD_NonParRolCor(SetDatosX, MCSim, Np, Widthwin, prob)`

**Descripción:** Correlación rodante no paramétrica con significancia estadística (Monte Carlo).

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Dos series de tiempo (2 columnas) |
| MCSim | número | (requerido) | Número de simulaciones Monte Carlo |
| Np | número | (requerido) | Número de procesadores |
| Widthwin | número | (requerido) | Ancho de ventana rodante |
| prob | número | (requerido) | Nivel de significancia |

**Ejemplo:**

```
=R.AD_NonParRolCor(A1:B200, 1000, 2, 30, 0.95)
```

**Resultado esperado:** Gráfico de correlación rodante con bandas de confianza.

**Paquetes requeridos:** `NonParRolCor`, `gtools`, `pracma`, `doParallel`

---

#### TM_TextMining

**Nombre Excel:** `=R.TM_TextMining(RUTA_FL, RUTA_SW, MAXWORDS, QPALABRASRESUMEN, IDIOMA, TipoOutput)`

**Descripción:** Análisis de minería de texto con nube de palabras y frecuencias.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| RUTA_FL | texto | NULL | Ruta al archivo de texto |
| RUTA_SW | texto | NULL | Ruta a archivo de stop words |
| MAXWORDS | número | 200 | Máximo de palabras en nube |
| QPALABRASRESUMEN | número | 100 | Palabras en resumen |
| IDIOMA | número | 1 | 1=Español, 2=Inglés |
| TipoOutput | número | 0 | Tipo de resultado |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Información |
| 1 | Nube de palabras (gráfico) |
| 2 | Tabla de frecuencias |
| 3 | Gráfico de barras (top 10) |
| 4 | Términos frecuentes |

**Ejemplo:**

```
=R.TM_TextMining("C:\datos\texto.txt", , 100, 50, 1, 2)
```

**Resultado esperado:** Tabla con las 50 palabras más frecuentes y su conteo.

**Paquetes requeridos:** `tm`, `SnowballC`, `wordcloud`, `RColorBrewer`

---

### Funciones Interactivas

> Las funciones interactivas generan HTML y se visualizan con el visor WebView2.
> Sintaxis: `=NEVEN.v(R.funcion(...))`

#### Pivot

**Nombre Excel:** `=NEVEN.v(R.Pivot(SetDatosX, TipoOutput))`

**Descripción:** Tabla pivote interactiva con drag-and-drop (rpivotTable).

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos con encabezados |
| TipoOutput | número | 0 | 0=Procedimientos, 1=Libre, 2=Heatmap, 3=Barras |

**Ejemplo:**

```
=NEVEN.v(R.Pivot(A1:E20, 1))
```

**Resultado esperado:** Visor HTML con tabla pivote interactiva.

**Paquetes requeridos:** `rpivotTable`, `htmlwidgets`

---

#### Esquisse

**Nombre Excel:** `=NEVEN.v(R.Esquisse(SetDatosX, TipoOutput))`

**Descripción:** Explorador interactivo de datos con selección de ejes, tipo de gráfico y color.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos con encabezados |
| TipoOutput | número | 0 | 0=Procedimientos, 1=Explorador interactivo |

**Ejemplo:**

```
=NEVEN.v(R.Esquisse(A1:F30, 1))
```

**Resultado esperado:** Visor HTML con controles para explorar datos (scatter, barras, líneas, box, histograma, heatmap).

**Paquetes requeridos:** `plotly`, `htmlwidgets`, `jsonlite`

---

#### D3, Dashboard, Map

**Nombre Excel:** `=NEVEN.v(R.D3(...))`, `=NEVEN.v(R.Dashboard(...))`, `=NEVEN.v(R.Map(...))`

**Descripción:** Funciones interactivas adicionales para visualización D3.js, dashboards y mapas geográficos. Abren un visor HTML interactivo.

---

### Series de Tiempo

#### ST_SeriesTemporales

**Nombre Excel:** `=R.ST_SeriesTemporales(SetDatosX, Periodicidad, TipoOutput)`

**Descripción:** Tests y descomposición de series temporales (cointegración, raíz unitaria, autocorrelación).

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Serie(s) de tiempo |
| Periodicidad | número | 1 | 1=Anual, 2=Semestral, 3=Trimestral, 4=Mensual |
| TipoOutput | número | 0 | Tipo de resultado |

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

**Ejemplo:**

```
=R.ST_SeriesTemporales(A1:A100, 4, 2)
```

**Resultado esperado:** Resultado del test ADF con estadístico y p-valor.

**Paquetes requeridos:** `tseries`

---

#### ST_Autoregresivos

**Nombre Excel:** `=R.ST_Autoregresivos(SetDatosX, Periodicidad, TipoOutput, OrdenP, OrdenD, OrdenQ)`

**Descripción:** Modelos autoregresivos: ARMA, ARIMA, GARCH.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Serie de tiempo |
| Periodicidad | número | 1 | Periodicidad de los datos |
| TipoOutput | número | 0 | Tipo de resultado |
| OrdenP | número | (requerido) | Orden AR |
| OrdenD | número | (requerido) | Orden de diferenciación |
| OrdenQ | número | (requerido) | Orden MA |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | ARMA (resumen) |
| 1.1 | ARMA (predicción 6 periodos) |
| 2 | ARIMA (resumen) |
| 2.1 | ARIMA (predicción 6 periodos) |
| 4 | GARCH (resumen) |
| 4.1 | GARCH (predicción) |

**Ejemplo:**

```
=R.ST_Autoregresivos(A1:A120, 4, 2, 1, 1, 1)
```

**Resultado esperado:** Resumen del modelo ARIMA(1,1,1).

**Paquetes requeridos:** `tseries`

---

#### ST_Filtro

**Nombre Excel:** `=R.ST_Filtro(SetDatosX, Periodicidad, TipoModelo, Drift, RaizUnitaria, TipoOutput)`

**Descripción:** Aplica filtros de series de tiempo (Hodrick-Prescott, Baxter-King, etc.).

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Serie de tiempo |
| Periodicidad | número | 1 | 1=Anual, 2=Semestral, 3=Trimestral, 4=Mensual |
| TipoModelo | número | 1 | 1=HP, 2=Baxter-King, 3=Christiano-Fitzgerald, 4=Butterworth, 5=Trigonométrico |
| Drift | número | 0 | Presencia de drift (0=No, 1=Sí) |
| RaizUnitaria | número | 0 | Presencia de raíz unitaria (0=No, 1=Sí) |
| TipoOutput | número | 0 | 0=Procedimientos, >0=Tendencia+Ciclo+Lambda |

**Ejemplo:**

```
=R.ST_Filtro(A1:A80, 3, 1, 0, 0, 1)
```

**Resultado esperado:** Matriz con columnas: tendencia, ciclo y lambda.

**Paquetes requeridos:** `tseries`, `mFilter`

---

### Gráficos

#### GR_QuickPlot

**Nombre Excel:** `=R.GR_QuickPlot(SetDatosX, SetDatosY, TipoGrafico, Titulo, TipoOutput)`

**Descripción:** Genera gráficos rápidos (R base y ggplot2) para visualización en WebView2.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos con encabezados |
| SetDatosY | rango | NULL | No utilizado |
| TipoGrafico | número | 0 | No utilizado |
| Titulo | texto | "RJ2XCL Chart" | Título del gráfico |
| TipoOutput | número | 0 | Tipo de gráfico |

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

**Ejemplo:**

```
=NEVEN.v(R.GR_QuickPlot(A1:C10, , , "Ventas 2024", 7))
```

**Resultado esperado:** Gráfico de barras interactivo (Plotly) en el visor.

**Paquetes requeridos:** `ggplot2`, `plotly`, `htmlwidgets`

---

#### GR_Graficos.D

**Nombre Excel:** `=R.GR_Graficos.D(SetDatosY, SetDatosX, Categorica)`

**Descripción:** Generador de gráficos con selección interactiva del tipo (diálogo).

**Ejemplo:**

```
=R.GR_Graficos.D(A1:A30, B1:C30, 1)
```

**Resultado esperado:** Gráfico seleccionado por el usuario (boxplot, scatter, etc.).

---

#### GR_GraficoInteractivo

**Nombre Excel:** `=R.GR_GraficoInteractivo(TipoOutput)`

**Descripción:** Crea un gráfico de mapa de árbol (treemap) interactivo con Plotly.

**Paquetes requeridos:** `plotly`, `highcharter`, `htmlwidgets`

---

### Matemáticas y Álgebra Lineal

#### MM_Algebra.C

**Nombre Excel:** `=R.MM_Algebra.C(SetDatosX, TipoOutput)`

**Descripción:** Operaciones de álgebra lineal sobre matrices.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Matriz numérica |
| TipoOutput | número | 0 | Tipo de operación |

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

**Ejemplo:**

```
=R.MM_Algebra.C(A1:C3, 2)
```

Datos dummy (matriz 3×3):

| 4 | 2 | 1 |
|---|---|---|
| 2 | 5 | 3 |
| 1 | 3 | 6 |

**Resultado esperado:** Vector con los 3 valores propios de la matriz.

---

### Funciones Auxiliares

#### FX_AleatorioUniforme

**Nombre Excel:** `=R.FX_AleatorioUniforme(N, Min, Max, Semilla, Histograma)`

**Descripción:** Genera N datos aleatorios con distribución uniforme.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| N | número | (requerido) | Cantidad de datos |
| Min | número | 0 | Valor mínimo |
| Max | número | 1 | Valor máximo |
| Semilla | número | NULL | Semilla aleatoria |
| Histograma | número | 0 | 0=Datos, 1=Histograma |

**Ejemplo:**

```
=R.FX_AleatorioUniforme(100, 0, 10, 42, 0)
```

**Resultado esperado:** Vector de 100 valores aleatorios entre 0 y 10.

---

#### FX_AleatorioNormal

**Nombre Excel:** `=R.FX_AleatorioNormal(N, Mu, Sigma, Semilla, Histograma)`

**Descripción:** Genera N datos aleatorios con distribución normal.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| N | número | 100 | Cantidad de datos |
| Mu | número | 0 | Media |
| Sigma | número | 1 | Desviación estándar |
| Semilla | número | 123456 | Semilla aleatoria |
| Histograma | número | 0 | 0=Datos, 1=Histograma |

**Ejemplo:**

```
=R.FX_AleatorioNormal(200, 50, 10, 42, 0)
```

**Resultado esperado:** Vector de 200 valores normales con media 50 y desviación 10.

---

#### FX_Distancias

**Nombre Excel:** `=R.FX_Distancias(SetDatosX, pEscalaDatos, pTipoDistancia, pPotenciaMinkowski)`

**Descripción:** Calcula la matriz de distancias entre observaciones.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos numéricos |
| pEscalaDatos | número | 1 | Normalizar (0=No, 1=Sí) |
| pTipoDistancia | número | 1 | 1=Euclidea, 2=Máxima, 3=Manhattan, 4=Canberra, 5=Binaria, 6=Minkowski |
| pPotenciaMinkowski | número | 2 | Potencia para Minkowski |

**Ejemplo:**

```
=R.FX_Distancias(A1:C20, 1, 1, 2)
```

**Resultado esperado:** Matriz simétrica de distancias euclídeas (20×20).

---

#### FX_Muestreo

**Nombre Excel:** `=R.FX_Muestreo(SetDatos, Semilla, Porc_Muestral, TipoOutput)`

**Descripción:** Divide un dataset en muestras de entrenamiento y prueba.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatos | rango | (requerido) | Datos completos |
| Semilla | número | (requerido) | Semilla aleatoria |
| Porc_Muestral | número | (requerido) | Proporción para entrenamiento (0-1) |
| TipoOutput | número | 0 | 0=Entrenamiento, 1=Prueba |

**Ejemplo:**

```
=R.FX_Muestreo(A1:D100, 42, 0.7, 0)
```

**Resultado esperado:** 70% de los datos seleccionados aleatoriamente para entrenamiento.

---

#### UT_Computo_Vars

**Nombre Excel:** `=R.UT_Computo_Vars(SetDatosX)`

**Descripción:** Transformaciones de variables: dummies, estandarización, distancias (selección interactiva).

**Ejemplo:**

```
=R.UT_Computo_Vars(A1:C30)
```

**Resultado esperado:** Variables transformadas según la opción seleccionada.

**Paquetes requeridos:** `dummies`

---

#### DB_Pivote

**Nombre Excel:** `=R.DB_Pivote(SetDatosX, SetDatosY, Filtro, TipoOutput)`

**Descripción:** Tabla agrupada (pivot) con funciones de agregación.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos completos |
| SetDatosY | rango | (requerido) | Columna(s) de agrupación |
| Filtro | rango | 0 | Vector filtro |
| TipoOutput | número | 1 | Función de agregación |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de opciones |
| 1 | Suma |
| 2 | Media |
| 3 | Mediana |
| 4 | Conteo |
| 5 | Sesgo |
| 6 | p-valor Jarque-Bera |
| 7 | Cuantil (solicita umbral) |

**Ejemplo:**

```
=R.DB_Pivote(A1:D50, E1:E50, , 2)
```

**Resultado esperado:** Tabla con medias agrupadas por la variable de clasificación.

---

#### DB_Union

**Nombre Excel:** `=R.DB_Union(SetDatosX, SetDatosY, TipoOutput)`

**Descripción:** Une dos tablas usando diferentes tipos de join (selección interactiva de llaves).

**TipoOutput:** 0=Opciones, 1=Inner, 2=Outer, 3=Cross, 4=Left, 5=Right

**Ejemplo:**

```
=R.DB_Union(A1:C20, E1:G15, 1)
```

**Resultado esperado:** Tabla resultante del inner join.

---

### Datos

#### DS_Wooldridge

**Nombre Excel:** `=R.DS_Wooldridge()`

**Descripción:** Explora y carga datasets de la librería `wooldridge` (econometría) con interfaz gráfica.

**Ejemplo:**

```
=R.DS_Wooldridge()
```

**Resultado esperado:** Dataset seleccionado por el usuario (ej: `wage1`, `mroz`, `hprice1`).

**Paquetes requeridos:** `wooldridge`, `svDialogs`

---

#### DS_ObtenerDatos

**Nombre Excel:** `=R.DS_ObtenerDatos(pTotalPaquetes)`

**Descripción:** Obtiene datasets de paquetes R instalados mediante diálogo interactivo.

**Ejemplo:**

```
=R.DS_ObtenerDatos(1)
```

**Resultado esperado:** Dataset seleccionado del paquete elegido.

---

## Funciones Julia

Todas las funciones Julia se invocan con el prefijo `=J.` seguido del nombre corto (alias).

### Álgebra Lineal — J.Algebra

**Nombre Excel:** `=J.Algebra(Matriz, VectorB, TipoOutput)`

**Descripción:** Operaciones avanzadas de álgebra lineal.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| Matriz | rango | (requerido) | Matriz numérica |
| VectorB | rango | nothing | Vector b para resolver Ax=b |
| TipoOutput | número | 0 | Procedimiento a ejecutar |

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

**Ejemplo:**

```
=J.Algebra(A1:C3, , 4)
```

Datos dummy (A1:C3):

| 4 | 2 | 1 |
|---|---|---|
| 2 | 5 | 3 |
| 1 | 3 | 6 |

**Resultado esperado:** Vector con los 3 valores propios: [1.27, 4.0, 9.73] (aproximado).

---

### Cálculo Numérico — J.Calculo

**Nombre Excel:** `=J.Calculo(VectorX, VectorY, Parametro, TipoOutput)`

**Descripción:** Métodos numéricos de cálculo: derivadas, integrales, raíces, interpolación.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| VectorX | rango | (requerido) | Puntos X (o intervalo [a,b]) |
| VectorY | rango | nothing | Puntos Y (o coeficientes) |
| Parametro | número | 0.0 | Punto de evaluación o tolerancia |
| TipoOutput | número | 0 | Procedimiento |

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

**Ejemplo:**

```
=J.Calculo(A1:A10, B1:B10, , 2)
```

Datos dummy (X en A, Y en B): puntos de una función f(x)=x²

| X | Y |
|---|---|
| 0 | 0 |
| 1 | 1 |
| 2 | 4 |
| 3 | 9 |
| 4 | 16 |

**Resultado esperado:** Integral por trapecio ≈ 32.0

---

### Ecuaciones Diferenciales — J.EDO

**Nombre Excel:** `=J.EDO(VectorX, VectorY, Parametro, TipoOutput)`

**Descripción:** Resolución numérica de ecuaciones diferenciales ordinarias.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| VectorX | rango | (requerido) | Intervalo [t0, tf] |
| VectorY | rango | (requerido) | Condición(es) inicial(es) |
| Parametro | número | 0.01 | Paso h |
| TipoOutput | número | 0 | Método |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Euler explícito (dy/dt = -y) |
| 2 | Runge-Kutta 4 (dy/dt = -y) |
| 3 | Sistema de EDOs RK4 (oscilador) |
| 4 | EDO 2do orden RK4 (y'' + y = 0) |

**Ejemplo:**

```
=J.EDO(A1:A2, B1:B1, 0.1, 2)
```

Datos: A1=0, A2=1 (intervalo [0,1]), B1=1 (y₀=1), paso h=0.1

**Resultado esperado:** Tabla [t, y] con solución numérica de dy/dt=-y → y(t)=e^(-t).

---

### Clasificación/KNN — J.KNN

**Nombre Excel:** `=J.KNN(SetDatosX, SetDatosY, K, TipoOutput)`

**Descripción:** Clasificación K-Nearest Neighbors con validación leave-one-out.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Features (variables predictoras) |
| SetDatosY | rango | (requerido) | Etiquetas de clase |
| K | número | 3 | Número de vecinos |
| TipoOutput | número | 0 | Tipo de resultado |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Clasificación con accuracy |
| 2 | Precisión, recall y F1 por clase |
| 3 | Matriz de confusión |
| 4 | Predicciones (real vs predicho) |
| 5 | Distancias al vecino más cercano |

**Ejemplo:**

```
=J.KNN(A1:C30, D1:D30, 5, 1)
```

**Resultado esperado:** "Accuracy: 86.67%" seguido de predicciones por observación.

---

### Regresión Julia — J.Regresion

**Nombre Excel:** `=J.Regresion(SetDatosX, SetDatosY, Parametro, TipoOutput)`

**Descripción:** Regresión lineal múltiple con diagnósticos.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Variables independientes |
| SetDatosY | rango | (requerido) | Variable dependiente |
| Parametro | número | 0 | No utilizado |
| TipoOutput | número | 0 | Tipo de resultado |

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Coeficientes + R² |
| 2 | Valores ajustados (predicción) |
| 3 | Residuos |
| 4 | Resumen completo (SE, t-stats, R²adj) |
| 5 | Intervalos de confianza 95% |

**Ejemplo:**

```
=J.Regresion(A1:B20, C1:C20, , 1)
```

**Resultado esperado:** "R2 = 0.85", "Intercepto = 2.34", "B1 = 1.56", "B2 = -0.42"

---

### Clustering — J.Clustering

**Nombre Excel:** `=J.Clustering(SetDatosX, K, Semilla, TipoOutput)`

**Descripción:** Algoritmo K-Medias implementado en Julia.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos numéricos |
| K | número | 3 | Número de clusters |
| Semilla | número | 12345 | Semilla aleatoria |
| TipoOutput | número | 0 | Tipo de resultado |

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

**Ejemplo:**

```
=J.Clustering(A1:D50, 3, 42, 1)
```

**Resultado esperado:** Vector con cluster asignado (1, 2 o 3) para cada observación.

---

### Estadística — J.Estadistica

**Nombre Excel:** `=J.Estadistica(SetDatosX, SetDatosY, TipoOutput)`

**Descripción:** Estadística descriptiva, correlación, normalización y detección de outliers.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| SetDatosX | rango | (requerido) | Datos numéricos |
| SetDatosY | rango | nothing | Segunda muestra (para test t) |
| TipoOutput | número | 0 | Tipo de resultado |

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

**Ejemplo:**

```
=J.Estadistica(A1:C50, , 1)
```

**Resultado esperado:** Tabla con estadísticas descriptivas para cada columna.

---

### Optimización — J.Optimizar

**Nombre Excel:** `=J.Optimizar(Matriz, Vector, Parametro, MaxIter, TipoOutput)`

**Descripción:** Algoritmos de optimización numérica.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| Matriz | rango | (requerido) | Matriz Q (o restricciones para Simplex) |
| Vector | rango | nothing | Vector b (o costos c) |
| Parametro | número | 0.01 | Learning rate o tolerancia |
| MaxIter | número | 1000 | Máximo de iteraciones |
| TipoOutput | número | 0 | Algoritmo |

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

**Ejemplo:**

```
=J.Optimizar(A1:C3, D1:D3, 0.01, 500, 1)
```

Datos: A=matriz definida positiva 3×3, D=vector b

**Resultado esperado:** Vector x que minimiza ½x'Ax - b'x.

---

### Transformación — J.Transformar

**Nombre Excel:** `=J.Transformar(Datos, Columna, Valor, TipoOutput)`

**Descripción:** Operaciones de transformación y manipulación de datos.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| Datos | rango | (requerido) | Datos a transformar |
| Columna | número | 1 | Columna de referencia |
| Valor | cualquiera | nothing | Valor para filtrado |
| TipoOutput | número | 0 | Operación |

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

**Ejemplo:**

```
=J.Transformar(A1:D20, 2, , 2)
```

**Resultado esperado:** Datos ordenados por la columna 2.

---

### Utilidades — J.Utilidades

**Nombre Excel:** `=J.Utilidades(P1, P2, P3, TipoOutput)`

**Descripción:** Funciones utilitarias generales.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| P1 | número | 0 | Parámetro 1 (varía según TipoOutput) |
| P2 | número | 0 | Parámetro 2 |
| P3 | número | 0 | Parámetro 3 |
| TipoOutput | número | 0 | Función |

**TipoOutput:**

| Valor | Resultado | P1 | P2 | P3 |
|-------|-----------|----|----|-----|
| 0 | Lista de procedimientos | — | — | — |
| 1 | Fecha y hora actual | — | — | — |
| 2 | Secuencia numérica | inicio | fin | paso |
| 3 | Aleatorios Normal | N | media | desviación |
| 4 | Aleatorios Uniforme | N | min | max |
| 5 | Redondear datos | datos/valor | decimales | — |

**Ejemplo:**

```
=J.Utilidades(100, 0, 1, 3)
```

**Resultado esperado:** Vector de 100 valores aleatorios N(0,1).

---

## Funciones Python

Las funciones Python se invocan con el prefijo `=P.`.

### ai_call

**Nombre Excel:** `=P.ai_call(data_str, prompt_name, context)`

**Descripción:** Invoca un modelo de lenguaje (LLM) con datos de Excel y un template de prompt. Soporta OpenAI, Azure, Ollama y LM Studio.

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

**Prerrequisitos:**
- `neven-config.json` con sección `"AI"` configurada (enabled: true, apiKey, model, endpoint)
- Directorio de prompts con archivos `.txt` (por defecto: `%USERPROFILE%\Documents\NEVEN\prompts\`)

**Ejemplo:**

```
=P.ai_call(A1:B10, "analizar", "datos de ventas Q1 2024")
```

**Resultado esperado:** Texto generado por el LLM analizando los datos según el template "analizar.txt".

---

### ai_setup

**Nombre Excel:** `=NEVEN.v(P.ai_setup())`

**Descripción:** Genera un formulario HTML de configuración AI que se muestra en el visor WebView2. Permite configurar proveedor, API key, modelo, endpoint y parámetros.

**Parámetros:** Ninguno.

**Ejemplo:**

```
=NEVEN.v(P.ai_setup())
```

**Resultado esperado:** Formulario interactivo de configuración en el visor.

---

### ai_list_prompts

**Nombre Excel:** `=P.ai_list_prompts()`

**Descripción:** Lista los nombres de todos los templates de prompts disponibles en el directorio configurado.

**Parámetros:** Ninguno.

**Ejemplo:**

```
=P.ai_list_prompts()
```

**Resultado esperado:** "analizar, resumir, traducir, clasificar" (lista separada por comas).

---

### quarto_render

**Nombre Excel:** `=P.quarto_render(file_path, format)`

**Descripción:** Renderiza un documento Quarto (.qmd) y retorna la ruta del archivo generado. Abre automáticamente el resultado.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| file_path | texto | (requerido) | Ruta completa al archivo .qmd |
| format | texto | "html" | Formato: html, pdf o docx |

**Prerrequisitos:**
- Quarto CLI instalado y accesible en PATH
- Para PDF: LaTeX/TinyTeX instalado

**Ejemplo:**

```
=P.quarto_render("C:\Users\usuario\Documents\reporte.qmd", "pdf")
```

**Resultado esperado:** "C:\Users\usuario\Documents\reporte.pdf" (ruta al archivo generado).

---

## Funciones del Sistema

Las funciones del sistema se invocan con el prefijo `=NEVEN.`.

### Ejecución

#### NEVEN.r()

**Nombre Excel:** `=NEVEN.r(expresion)`

**Descripción:** Ejecuta una expresión R y retorna el resultado a la celda de Excel.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| expresion | texto | Código R a ejecutar |

**Ejemplo:**

```
=NEVEN.r("mean(c(1,2,3,4,5))")
```

**Resultado esperado:** 3

---

#### NEVEN.j()

**Nombre Excel:** `=NEVEN.j(expresion)`

**Descripción:** Ejecuta una expresión Julia y retorna el resultado a la celda de Excel.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| expresion | texto | Código Julia a ejecutar |

**Ejemplo:**

```
=NEVEN.j("sum([1,2,3,4,5])")
```

**Resultado esperado:** 15

---

#### NEVEN.v()

**Nombre Excel:** `=NEVEN.v(expresion)`

**Descripción:** Ejecuta una expresión y muestra el resultado en el visor HTML (WebView2). Ideal para gráficos interactivos y tablas HTML.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| expresion | texto/función | Expresión que retorna HTML o ruta a archivo HTML |

**Ejemplo:**

```
=NEVEN.v(R.Pivot(A1:E20, 1))
=NEVEN.v(P.ai_setup())
```

**Resultado esperado:** Se abre el visor WebView2 con el contenido HTML.

---

#### NEVEN.q()

**Nombre Excel:** `=NEVEN.q(ruta)`

**Descripción:** Renderiza un documento Quarto (.qmd) y muestra el resultado.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| ruta | texto | Ruta al archivo .qmd |

**Ejemplo:**

```
=NEVEN.q("C:\Users\usuario\reporte.qmd")
```

**Resultado esperado:** Documento renderizado y abierto.

---

### Pluto

#### NEVEN.pluto.start()

**Nombre Excel:** `=NEVEN.pluto.start()`

**Descripción:** Inicia el servidor Pluto.jl para notebooks reactivos de Julia.

**Ejemplo:**

```
=NEVEN.pluto.start()
```

**Resultado esperado:** "Pluto server started on port 1234"

---

#### NEVEN.pluto.stop()

**Nombre Excel:** `=NEVEN.pluto.stop()`

**Descripción:** Detiene el servidor Pluto.jl.

**Ejemplo:**

```
=NEVEN.pluto.stop()
```

**Resultado esperado:** "Pluto server stopped"

---

#### NEVEN.pluto.status()

**Nombre Excel:** `=NEVEN.pluto.status()`

**Descripción:** Consulta el estado actual del servidor Pluto.

**Ejemplo:**

```
=NEVEN.pluto.status()
```

**Resultado esperado:** "Running on port 1234" o "Not running"

---

#### NEVEN.pluto.data()

**Nombre Excel:** `=NEVEN.pluto.data(rango)`

**Descripción:** Envía datos de Excel a un notebook Pluto activo via TSV.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| rango | rango | Datos a enviar al notebook |

**Ejemplo (pipeline completo):**

```
Paso 1: =NEVEN.pluto.start()
Paso 2: =NEVEN.pluto.data(A1:D50)
Paso 3: (trabajar en Pluto)
Paso 4: =NEVEN.pluto.stop()
```

**Resultado esperado:** "Data sent: 50 rows x 4 columns"

---

### Utilidades del Sistema

#### NEVEN.notebook.open()

**Nombre Excel:** `=NEVEN.notebook.open(ruta)`

**Descripción:** Abre un notebook Pluto específico.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| ruta | texto | Ruta al archivo .jl del notebook |

**Ejemplo:**

```
=NEVEN.notebook.open("C:\Users\usuario\notebooks\analisis.jl")
```

---

#### NEVEN.notebook.list()

**Nombre Excel:** `=NEVEN.notebook.list()`

**Descripción:** Lista los notebooks Pluto disponibles.

**Ejemplo:**

```
=NEVEN.notebook.list()
```

**Resultado esperado:** Lista de archivos .jl en el directorio de notebooks.

---

#### NEVEN.editor()

**Nombre Excel:** `=NEVEN.editor()`

**Descripción:** Abre el editor de código integrado (Monaco/VS Code embebido).

**Ejemplo:**

```
=NEVEN.editor()
```

**Resultado esperado:** Se abre la ventana del editor.

---

#### NEVEN.about()

**Nombre Excel:** `=NEVEN.about()`

**Descripción:** Muestra información sobre la versión de NEVEN instalada.

**Ejemplo:**

```
=NEVEN.about()
```

**Resultado esperado:** "NEVEN v1.0 — R 4.4.1, Julia 1.12.6"

---

#### NEVEN.help()

**Nombre Excel:** `=NEVEN.help()`

**Descripción:** Muestra la ayuda general de NEVEN con enlaces a documentación.

**Ejemplo:**

```
=NEVEN.help()
```

**Resultado esperado:** Texto con instrucciones básicas y enlaces.

---

## Índice Cruzado por Categoría

### Regresión

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.MR_Lineal](#mr_lineal) | R | Regresión lineal múltiple (OLS) |
| [R.MR_Binario.C](#mr_binarioc) | R | Regresión logística/probit |
| [R.MR_Poisson.C](#mr_poissonc) | R | Regresión Poisson (conteo) |
| [R.MR_Tobit.C](#mr_tobitc) | R | Regresión Tobit (censurada) |
| [R.MR_PanelData.C](#mr_paneldatac) | R | Datos de panel |
| [J.Regresion](#regresión-julia--jregresion) | Julia | Regresión lineal con diagnósticos |
| [J.KNN (TipoOutput=2)](#clasificaciónknn--jknn) | Julia | Regresión lineal via clasificación |

### Clasificación / Machine Learning

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.MR_SVM](#mr_svm) | R | Support Vector Machine |
| [R.AD_ArbolDeDecision.C](#ad_arboldedecisionc) | R | Árboles de decisión |
| [J.KNN](#clasificaciónknn--jknn) | Julia | K-Nearest Neighbors |
| [J.Regresion](#regresión-julia--jregresion) | Julia | Regresión lineal |

### Clustering

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.AD_KMedias.C](#ad_kmediasc) | R | K-Medias (R) |
| [R.AD_KmediasClasificar](#ad_kmediasclasificar) | R | Clasificación con centroides |
| [J.Clustering](#clustering--jclustering) | Julia | K-Medias (Julia) |

### Estadística Descriptiva

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.AD_ACP.C](#ad_acpc) | R | Análisis de Componentes Principales |
| [R.DB_Pivote](#db_pivote) | R | Tablas agrupadas con agregación |
| [J.Estadistica](#estadística--jestadistica) | Julia | Descriptiva, correlación, tests |

### Series de Tiempo

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.ST_SeriesTemporales](#st_seriestemporales) | R | Tests y descomposición |
| [R.ST_Autoregresivos](#st_autoregresivos) | R | ARMA, ARIMA, GARCH |
| [R.ST_Filtro](#st_filtro) | R | Filtros HP, BK, CF, BW, TR |

### Álgebra Lineal

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.MM_Algebra.C](#mm_algebrac) | R | Operaciones matriciales (R) |
| [J.Algebra](#álgebra-lineal--jalgebra) | Julia | Álgebra lineal avanzada |

### Cálculo Numérico

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [J.Calculo](#cálculo-numérico--jcalculo) | Julia | Derivadas, integrales, raíces, interpolación |
| [J.EDO](#ecuaciones-diferenciales--jedo) | Julia | Ecuaciones diferenciales (Euler, RK4) |

### Optimización

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [J.Optimizar](#optimización--joptimizar) | Julia | Gradiente, Newton, Simplex, NNLS, QP |

### Visualización

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.GR_QuickPlot](#gr_quickplot) | R | Gráficos rápidos (R base + ggplot2) |
| [R.GR_Graficos.D](#gr_graficosd) | R | Gráficos con selección interactiva |
| [R.Pivot](#pivot) | R | Tabla pivote interactiva |
| [R.Esquisse](#esquisse) | R | Explorador interactivo de datos |
| [R.GR_GraficoInteractivo](#gr_graficointeractivo) | R | Treemap interactivo |

### Datos / Transformación

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.DB_Union](#db_union) | R | Joins entre tablas |
| [R.FX_Muestreo](#fx_muestreo) | R | División train/test |
| [R.UT_Computo_Vars](#ut_computo_vars) | R | Dummies, estandarización, distancias |
| [R.DS_Wooldridge](#ds_wooldridge) | R | Datasets de econometría |
| [J.Transformar](#transformación--jtransformar) | Julia | Transponer, ordenar, filtrar, únicos |

### Utilidades

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [R.FX_AleatorioUniforme](#fx_aleatoriouniforme) | R | Generación aleatoria uniforme |
| [R.FX_AleatorioNormal](#fx_aleatorionormal) | R | Generación aleatoria normal |
| [R.FX_Distancias](#fx_distancias) | R | Matrices de distancia |
| [J.Utilidades](#utilidades--jutilidades) | Julia | Fecha, secuencias, aleatorios |
| [R.AD_NonParRolCor](#ad_nonparrolcor) | R | Correlación rodante no paramétrica |
| [R.TM_TextMining](#tm_textmining) | R | Minería de texto |

### AI / LLM

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| [P.ai_call](#ai_call) | Python | Invocar modelo de lenguaje |
| [P.ai_setup](#ai_setup) | Python | Configurar AI |
| [P.ai_list_prompts](#ai_list_prompts) | Python | Listar prompts disponibles |
| [P.quarto_render](#quarto_render) | Python | Renderizar documentos Quarto |

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

*Documento generado para NEVEN — Add-in XLL para Microsoft Excel*  
*Universidad de Costa Rica — Tesis de Maestría*
