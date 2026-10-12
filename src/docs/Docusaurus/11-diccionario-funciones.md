---
id: diccionario-funciones
title: Capítulo 11 — Diccionario de Funciones
sidebar_label: 11. Diccionario
sidebar_position: 11
---

# Diccionario de Funciones NEVEN

**Última actualización:** 2026-08-19  
**Versión:** NEVEN v3.2  
**Total de funciones documentadas:** 200+ (R: 90+ procedimientos, Julia: 61 procedimientos, Python/Sistema: 50+ endpoints)

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

```excel
=R.MR_Lineal(A1:A20, B1:D20, , , , , , 1)
```

**Paquetes requeridos:** `stargazer`, `margins`, `usdm`, `lmtest`, `sandwich`

---

#### MR_Binario.C

**Nombre Excel:** `=R.MR_Binario.C(SetDatosY, SetDatosX, Categorica, Filtro, Escala, SetDatosPredecir, TipoModelo, TipoOutput)`

**Descripción:** Estima un modelo de regresión binaria (Logit o Probit) para variables dependientes dicotómicas.

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
| 6-9 | Tests de Breusch-Pagan |
| 10-11 | Tests de dependencia cross-seccional |
| 12 | Test de autocorrelación (Breusch-Godfrey) |
| 13 | Test de raíz unitaria (ADF) |

**Paquetes requeridos:** `plm`, `stargazer`, `tseries`

---

#### MR_SVM

**Nombre Excel:** `=R.MR_SVM(SetDatosY, SetDatosX, Filtro, pkernel, ptype, TipoOutput)`

**Descripción:** Estima un modelo de Support Vector Machine (SVM) para clasificación o regresión.

**Paquetes requeridos:** `e1071`

---

#### MR_2SLS

**Nombre Excel:** `=R.MR_2SLS(SetDatosY, SetDatosX, Instrumentos, TipoOutput)`

**Descripción:** Regresión por mínimos cuadrados en dos etapas (2SLS) para variables endógenas.

**Paquetes requeridos:** `AER`, `stargazer`

---

#### MR_HECKIT

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

#### AD_ClusteringJerarquico

**Nombre Excel:** `=R.AD_ClusteringJerarquico(SetDatosX, Metodo, NumClusters, TipoOutput)`

**Descripción:** Clustering jerárquico aglomerativo con dendrograma.

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

### Funciones Interactivas

:::tip Uso del visor
Las funciones interactivas generan HTML y se visualizan con el visor WebView2.
Sintaxis: `=NEVEN.v(R.funcion(...))`
:::

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

### Series de Tiempo

#### ST_SeriesTemporales

**Nombre Excel:** `=R.ST_SeriesTemporales(SetDatosX, Periodicidad, TipoOutput)`

**Descripción:** Tests y descomposición de series temporales.

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Test de cointegración (Phillips-Ouliaris) |
| 2 | Test de raíz unitaria (ADF) |
| 3 | Test de Phillips-Perron |
| 4 | Test de Jarque-Bera (normalidad) |
| 5 | Autocorrelación (ACF + PACF + límites) |
| 6 | Descomposición aditiva |
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

#### ST_VAR

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

#### ST_ECM

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
| 1-6 | Gráficos R base (barras, líneas, scatter, histograma, box, pie) |
| 7-9 | Gráficos ggplot2 interactivos (barras, líneas, scatter) |

**Paquetes requeridos:** `ggplot2`, `plotly`, `htmlwidgets`

---

#### Gráficos Studio

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

#### FX_AleatorioUniforme / FX_AleatorioNormal

Generación de datos aleatorios con distribución uniforme o normal.

#### FX_Distancias

Calcula la matriz de distancias entre observaciones.

#### FX_Muestreo

Divide un dataset en muestras de entrenamiento y prueba.

---

### Datos

#### DS_Wooldridge

**Nombre Excel:** `=R.DS_Wooldridge()`

**Descripción:** Explora y carga datasets de la librería `wooldridge` (econometría) con interfaz gráfica.

**Paquetes requeridos:** `wooldridge`, `svDialogs`

---

## Funciones Julia

Todas las funciones Julia se invocan con el prefijo `=J.` seguido del nombre corto (alias).

:::info Rendimiento
NEVEN incluye una sysimage precompilada de Julia (`neven_julia.dll`, 415MB) que reduce el tiempo de inicio de minutos a segundos.
:::

### Álgebra Lineal — J.Algebra

**Nombre Excel:** `=J.Algebra(Matriz, VectorB, TipoOutput)`

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Factorización LU |
| 2 | Factorización QR |
| 3 | Descomposición SVD |
| 4 | Valores propios |
| 5 | Vectores propios |
| 6 | Determinante |
| 7 | Rango |
| 8 | Normas (Frobenius, 1, 2, Inf) |
| 9 | Número de condición |
| 10 | Pseudoinversa Moore-Penrose |
| 11 | Traza |
| 12 | Resolver Ax=b |

---

### Cálculo Numérico — J.Calculo

**Nombre Excel:** `=J.Calculo(VectorX, VectorY, Parametro, TipoOutput)`

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Derivada numérica |
| 2 | Integral por trapecio |
| 3 | Integral por Simpson |
| 4 | Raíz por bisección |
| 5-6 | Interpolación (lineal, Lagrange) |
| 7 | Serie de Taylor |

---

### Ecuaciones Diferenciales — J.EDO

**Nombre Excel:** `=J.EDO(VectorX, VectorY, Parametro, TipoOutput)`

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Euler explícito |
| 2 | Runge-Kutta 4 |
| 3 | Sistema de EDOs RK4 |
| 4 | EDO 2do orden RK4 |

---

### Clasificación/KNN — J.KNN

**Nombre Excel:** `=J.KNN(SetDatosX, SetDatosY, K, TipoOutput)`

Clasificación K-Nearest Neighbors con validación leave-one-out.

---

### Regresión Julia — J.Regresion

**Nombre Excel:** `=J.Regresion(SetDatosX, SetDatosY, Parametro, TipoOutput)`

Regresión lineal múltiple con diagnósticos.

---

### Clustering — J.Clustering

**Nombre Excel:** `=J.Clustering(SetDatosX, K, Semilla, TipoOutput)`

Algoritmo K-Medias implementado en Julia.

---

### Estadística — J.Estadistica

**Nombre Excel:** `=J.Estadistica(SetDatosX, SetDatosY, TipoOutput)`

Estadística descriptiva, correlación, normalización y detección de outliers.

---

### Optimización — J.Optimizar

**Nombre Excel:** `=J.Optimizar(Matriz, Vector, Parametro, MaxIter, TipoOutput)`

**TipoOutput:**

| Valor | Resultado |
|-------|-----------|
| 0 | Lista de procedimientos |
| 1 | Descenso de gradiente |
| 2 | Gradiente con momentum |
| 3 | Método de Newton |
| 4 | Sección áurea 1D |
| 5 | Simplex (LP) |
| 6 | NNLS |
| 7 | Programación cuadrática |

---

### Transformación — J.Transformar

Operaciones de transformación y manipulación de datos.

---

### Utilidades — J.Utilidades

Funciones utilitarias generales (fecha, secuencias, aleatorios).

---

## Funciones Python

### AI/LLM

#### ai_call

**Nombre Excel:** `=P.ai_call(data_str, prompt_name, context)`

**Descripción:** Invoca un modelo de lenguaje (LLM) con datos de Excel y un template de prompt. Soporta OpenAI, Azure, Anthropic (Claude), Ollama y LM Studio.

**Placeholders en templates:**
- `{{datos}}` — Se reemplaza con data_str
- `{{resultado}}` — Sinónimo de {{datos}}
- `{{contexto}}` — Se reemplaza con context

**Ejemplo:**

```excel
=P.ai_call(A1:B10, "analizar", "datos de ventas Q1 2024")
```

---

#### ai_setup

**Nombre Excel:** `=NEVEN.v(P.ai_setup())`

Formulario HTML de configuración AI en el visor WebView2.

---

#### ai_list_prompts

**Nombre Excel:** `=P.ai_list_prompts()`

Lista los templates de prompts disponibles.

---

### Quarto

#### quarto_render

**Nombre Excel:** `=P.quarto_render(file_path, format)`

Renderiza un documento Quarto (.qmd). Formatos: html, pdf, docx.

---

## Funciones del Sistema

### Ejecución

| Función | Descripción |
|---------|-------------|
| `=NEVEN.r(expresion)` | Ejecuta expresión R |
| `=NEVEN.j(expresion)` | Ejecuta expresión Julia |
| `=NEVEN.py(expresion)` | Ejecuta expresión Python |
| `=NEVEN.v(expresion)` | Muestra resultado en visor WebView2 |
| `=NEVEN.q(ruta)` | Renderiza documento Quarto |

### Pluto

| Función | Descripción |
|---------|-------------|
| `=NEVEN.pluto.start()` | Inicia servidor Pluto.jl |
| `=NEVEN.pluto.stop()` | Detiene servidor Pluto.jl |
| `=NEVEN.pluto.status()` | Estado del servidor |
| `=NEVEN.pluto.data(rango)` | Envía datos a notebook Pluto |

### Utilidades del Sistema

| Función | Descripción |
|---------|-------------|
| `=NEVEN.notebook.open(ruta)` | Abre notebook Pluto |
| `=NEVEN.notebook.list()` | Lista notebooks disponibles |
| `=NEVEN.editor()` | Abre editor de código |
| `=NEVEN.about()` | Información de versión |
| `=NEVEN.help()` | Ayuda general |

---

## NEVEN Studio

NEVEN Studio es un modo standalone implementado como Office Add-in (HTML/JS) que extiende las capacidades de NEVEN más allá de las fórmulas de celda.

### Tab SQL

Ejecuta consultas SQL sobre datos de Excel utilizando DuckDB embebido.

```sql
SELECT * FROM excel_range('Sheet1!A1:D100')
WHERE valor > 1000
ORDER BY fecha DESC
```

### Tab Data Studio

Entorno de edición visual para transformación de datos con generación automática de código R/Python.

### Tab Run Script

Editor de código con syntax highlighting para R, Julia y Python.

### Tab Data Lab

Pipeline de descubrimiento de datos con:
- **Preguntas:** Motor de lenguaje natural
- **Explorador:** Visualización interactiva de datasets
- **Código:** Generación automática de código

### Tab Presentaciones

Generador de presentaciones HTML con reveal.js.

### Tab IA

Asistente de inteligencia artificial contextual con:
- Integración con Claude, OpenAI, Azure, Ollama
- Contexto automático del rango seleccionado
- Generación de código basada en descripción natural
- Renderizado de fórmulas LaTeX

### Tab Ayuda

Sistema de ayuda con búsqueda semántica sobre 200+ funciones.

---

## API HTTP Endpoints

El servidor HTTP de NEVEN (puerto 5555) expone endpoints para NEVEN Studio y automatización.

### Core Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/run_script` | Ejecuta script R/Julia/Python |
| POST | `/api/sql` | Ejecuta query SQL en DuckDB |
| POST | `/api/load` | Carga datos en DuckDB |
| GET | `/api/tables` | Lista tablas en DuckDB |
| GET | `/api/health` | Estado del servidor |

### AI/Chat Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/ai/chat` | Envía mensaje al LLM con contexto RAG |
| POST | `/api/ai/context` | Recibe contexto de Excel |
| POST | `/api/ai/chart` | Genera gráfico desde descripción |

### Configuration Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/config/ai-profiles` | Lista perfiles de IA |
| POST | `/api/config/ai-profiles` | Crea perfil de IA |
| GET | `/api/config/db-connections` | Lista conexiones DB |
| GET | `/api/config/prompts` | Lista prompts |

### RAG Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/rag/stats` | Estadísticas del índice RAG |
| GET | `/api/rag/documents` | Lista documentos indexados |
| POST | `/api/rag/query` | Consulta semántica al índice |

---

## Índice Cruzado por Categoría

### Regresión

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.MR_Lineal | R | OLS |
| R.MR_Binario.C | R | Logit/Probit |
| R.MR_Poisson.C | R | Poisson |
| R.MR_Tobit.C | R | Tobit |
| R.MR_PanelData.C | R | Datos de panel |
| R.MR_2SLS | R | 2SLS |
| R.MR_HECKIT | R | Heckman |
| J.Regresion | Julia | Regresión lineal |

### Clasificación / ML

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.MR_SVM | R | SVM |
| R.AD_ArbolDeDecision.C | R | Árboles de decisión |
| J.KNN | Julia | K-Nearest Neighbors |

### Clustering

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.AD_KMedias.C | R | K-Medias |
| R.AD_ClusteringJerarquico | R | Jerárquico |
| J.Clustering | Julia | K-Medias |

### Series de Tiempo

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| R.ST_SeriesTemporales | R | Tests y descomposición |
| R.ST_Autoregresivos | R | ARMA, ARIMA, GARCH |
| R.ST_VAR | R | VAR |
| R.ST_ECM | R | ECM |

### Álgebra Lineal

| Función | Lenguaje |
|---------|----------|
| R.MM_Algebra.C | R |
| J.Algebra | Julia |

### Optimización

| Función | Lenguaje |
|---------|----------|
| J.Optimizar | Julia |

### AI / LLM

| Función | Lenguaje | Descripción |
|---------|----------|-------------|
| P.ai_call | Python | Invocar LLM |
| Tab IA (Studio) | Python | Asistente contextual |

---

*Documento generado para NEVEN v3.2 — Add-in XLL políglota para Microsoft Excel*  
*BukloLAB — Tesis de Maestría, Universidad de Costa Rica*
