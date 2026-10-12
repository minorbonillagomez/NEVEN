# NEVEN v2.0 -- Guia de Ejemplos para el Usuario

**Universidad de Costa Rica -- Tesis de Maestria**

Ejemplos listos para copiar y pegar en celdas de Excel.

------------------------------------------------------------------------

## Verificacion Rapida

```
=NEVEN.r("1+1")        --> 2
=NEVEN.j("sqrt(144)")  --> 12
=NEVEN.about()         --> Informacion del proyecto
=NEVEN.help()          --> Lista completa de funciones
```

------------------------------------------------------------------------

## 1. Julia -- Funciones con Rangos de Excel

Todas las funciones Julia usan `TipoOutput=0` para ver los procedimientos disponibles.

### 1.1 Utilidades y generacion de datos

| Formula | Resultado |
|:---|:---|
| `=J.Utilidades(0,0,0,0)` | Lista de procedimientos |
| `=J.Utilidades(0,0,0,1)` | Fecha y hora actual |
| `=J.Utilidades(1,100,1,2)` | Secuencia de 1 a 100 |
| `=J.Utilidades(A1,B1,C1,2)` | Secuencia de A1 a B1 con paso C1 |
| `=J.Utilidades(50,0,1,3)` | 50 aleatorios Normal(0,1) |
| `=J.Utilidades(A1,B1,C1,3)` | A1 aleatorios Normal(media=B1, sd=C1) |
| `=J.Utilidades(50,0,10,4)` | 50 aleatorios Uniforme(0,10) |

### 1.2 Algebra lineal

Matriz en A1:B2:

| Formula | Resultado |
|:---|:---|
| `=J.Algebra(A1:B2,0,0)` | Lista de 12 procedimientos |
| `=J.Algebra(A1:B2,0,6)` | Determinante |
| `=J.Algebra(A1:B2,0,4)` | Valores propios |
| `=J.Algebra(A1:B2,0,5)` | Vectores propios |
| `=J.Algebra(A1:B2,0,7)` | Rango |
| `=J.Algebra(A1:B2,0,11)` | Traza |
| `=J.Algebra(A1:B2,0,10)` | Pseudoinversa Moore-Penrose |
| `=J.Algebra(A1:B2,0,1)` | Factorizacion LU |
| `=J.Algebra(A1:B2,0,2)` | Factorizacion QR |
| `=J.Algebra(A1:B2,0,3)` | Descomposicion SVD |
| `=J.Algebra(A1:B2,0,9)` | Numero de condicion |
| `=J.Algebra(A1:B2,C1:C2,12)` | Resolver sistema Ax=b |

### 1.3 Calculo numerico

Firma: `=J.Calculo(VectorX, VectorY, Parametro, TipoOutput)`

El tercer argumento **Parametro** cambia de significado segun el procedimiento:

| TipoOutput | Procedimiento | Parametro significa |
|:---|:---|:---|
| 1 | Derivada numerica | No usado (poner 0) |
| 2 | Integral Trapecio | No usado (poner 0) |
| 3 | Integral Simpson | No usado (poner 0) |
| 4 | Raiz por Biseccion | Tolerancia (ej: 0.0001) |
| 5 | Interpolacion Lineal | Punto x donde evaluar |
| 6 | Interpolacion Lagrange | Punto x donde evaluar |
| 7 | Serie de Taylor | Punto x donde evaluar |

**Derivada, Integrales, Interpolacion** -- X en A1:A5, Y en B1:B5 (ejemplo: X=0,1,2,3,4 y Y=0,1,4,9,16 --> Y=X2):

| Formula | Resultado |
|:---|:---|
| `=J.Calculo(A1:A5,B1:B5,0,0)` | Lista de 7 procedimientos |
| `=J.Calculo(A1:A5,B1:B5,0,1)` | Derivada numerica --> {0, 2, 4, 6, 8} (aprox 2X) |
| `=J.Calculo(A1:A5,B1:B5,0,2)` | Integral Trapecio --> 22 |
| `=J.Calculo(A1:A5,B1:B5,0,3)` | Integral Simpson --> 21.33 (aprox 64/3) |
| `=J.Calculo(A1:A5,B1:B5,2.5,5)` | Interpolacion lineal en x=2.5 --> 6.5 |
| `=J.Calculo(A1:A5,B1:B5,2.5,6)` | Interpolacion Lagrange en x=2.5 --> 6.25 (exacto) |

**Biseccion** -- encontrar raiz de f(x) en un intervalo:

Datos: A1=0, A2=2 (intervalo), B1=-1, B2=3 (valores f(0)=-1, f(2)=3):
| Formula | Resultado |
|:---|:---|
| `=J.Calculo(A1:A2,B1:B2,0.0001,4)` | Raiz por biseccion --> 0.5 (donde f cruza cero) |

**Serie de Taylor** -- evaluar polinomio con coeficientes:

Datos: A1=0 (centro), B1=1, B2=0, B3=0.5 (coefs de 1 + 0x + 0.5x2 = cos(x) aprox):
| Formula | Resultado |
|:---|:---|
| `=J.Calculo(A1:A1,B1:B3,1.0,7)` | Taylor en x=1.0 --> 1.5 (1 + 0 + 0.5) |

### 1.4 Ecuaciones diferenciales

Firma: `=J.EDO(VectorX, VectorY, Parametro, TipoOutput)`

- **VectorX**: intervalo de tiempo [t0, tf]
- **VectorY**: condiciones iniciales
- **Parametro**: paso de integracion h -- controla la precision del metodo numerico. Valores mas pequenos (0.001) dan mayor precision pero mas filas de resultado. Valor tipico: 0.01

Datos en la hoja:

| Celda | Valor | Significado |
|:---|:---|:---|
| A1 | 0 | Tiempo inicial (t0) |
| A2 | 5 | Tiempo final (tf) |
| B1 | 1 | Condicion inicial y(0)=1 |
| B2 | 0 | Condicion inicial y'(0)=0 (para EDOs de 2do orden) |

| Formula | Resultado |
|:---|:---|
| `=J.EDO(A1:A2,B1:B2,0.01,0)` | Lista de 4 procedimientos |
| `=J.EDO(A1:A2,B1:B2,0.01,1)` | Euler explicito dy/dt=-y --> tabla [t, y] (y decae de 1 a ~0.007) |

**Nota:** Siempre usar B1:B2 como rango, poner B2=0. Los procedimientos 2, 3 y 4 estan en desarrollo.

### 1.5 Estadistica descriptiva

Firma: `=J.Estadistica(SetDatosX, SetDatosY, TipoOutput)`

Datos de ejemplo en A1:C10 (3 columnas, 10 registros):

| | A (Edad) | B (Peso) | C (Altura) |
|---|---|---|---|
| 1 | 25 | 70 | 170 |
| 2 | 30 | 85 | 175 |
| 3 | 22 | 60 | 165 |
| 4 | 35 | 90 | 180 |
| 5 | 28 | 75 | 172 |
| 6 | 40 | 95 | 178 |
| 7 | 23 | 65 | 168 |
| 8 | 33 | 80 | 176 |
| 9 | 27 | 72 | 171 |
| 10 | 31 | 88 | 177 |

| Formula | Resultado |
|:---|:---|
| `=J.Estadistica(A1:C10,0,0)` | Lista de 8 procedimientos |
| `=J.Estadistica(A1:C10,0,1)` | Descriptiva --> N, Media, Std, Min, Q1, Mediana, Q3, Max por columna |
| `=J.Estadistica(A1:C10,0,2)` | Matriz de correlacion 3x3 (Edad-Peso ~0.95) |
| `=J.Estadistica(A1:C10,0,3)` | Matriz de covarianza 3x3 |
| `=J.Estadistica(A1:A10,B1:B10,4)` | Test t de Student entre Edad y Peso |
| `=J.Estadistica(A1:C10,0,5)` | Normalizacion MinMax (valores entre 0 y 1) |
| `=J.Estadistica(A1:C10,0,6)` | Estandarizacion Z-Score (media=0, std=1) |
| `=J.Estadistica(A1:A10,0,7)` | Percentiles de Edad (1,5,10,25,50,75,90,95,99) |
| `=J.Estadistica(A1:C10,0,8)` | Deteccion de outliers IQR --> Q1, Q3, IQR, #outliers por columna |

### 1.6 KNN -- Clasificacion

Firma: `=J.KNN(SetDatosX, SetDatosY, K, TipoOutput)`

Usar el dataset Iris. Columnas A:D = medidas, E = especie (1, 2, 3):

| | A (SepalL) | B (SepalW) | C (PetalL) | D (PetalW) | E (Especie) |
|---|---|---|---|---|---|
| 1 | 5.1 | 3.5 | 1.4 | 0.2 | 1 |
| 2 | 4.9 | 3.0 | 1.4 | 0.2 | 1 |
| 3 | 7.0 | 3.2 | 4.7 | 1.4 | 2 |
| 4 | 6.4 | 3.2 | 4.5 | 1.5 | 2 |
| 5 | 6.3 | 3.3 | 6.0 | 2.5 | 3 |
| 6 | 5.8 | 2.7 | 5.1 | 1.9 | 3 |
| 7 | 5.0 | 3.4 | 1.5 | 0.2 | 1 |
| 8 | 6.7 | 3.1 | 4.4 | 1.4 | 2 |
| 9 | 6.3 | 2.5 | 5.0 | 1.9 | 3 |
| 10 | 5.4 | 3.9 | 1.7 | 0.4 | 1 |

X = A1:D10, Y = E1:E10:

| Formula | Resultado |
|:---|:---|
| `=J.KNN(A1:D10,E1:E10,3,0)` | Lista de 5 procedimientos |
| `=J.KNN(A1:D10,E1:E10,3,1)` | Clasificacion KNN (K=3) --> accuracy y predicciones |
| `=J.KNN(A1:D10,E1:E10,3,2)` | Precision, Recall y F1 por clase |
| `=J.KNN(A1:D10,E1:E10,3,3)` | Matriz de confusion 3x3 |
| `=J.KNN(A1:D10,E1:E10,3,4)` | Tabla real vs predicho |
| `=J.KNN(A1:D10,E1:E10,3,5)` | Distancia al vecino mas cercano |

**Nota:** K=3 es el valor tipico. Probar con K=1, K=5, K=7 para comparar accuracy.

### 1.7 Regresion lineal

Firma: `=J.Regresion(SetDatosX, SetDatosY, Parametro, TipoOutput)`

Usar los mismos datos Iris: X = A1:D10 (medidas), Y = E1:E10 (especie):

| Formula | Resultado |
|:---|:---|
| `=J.Regresion(A1:D10,E1:E10,0,0)` | Lista de 5 procedimientos |
| `=J.Regresion(A1:D10,E1:E10,0,1)` | Coeficientes + R2 |
| `=J.Regresion(A1:D10,E1:E10,0,2)` | Valores ajustados (prediccion) |
| `=J.Regresion(A1:D10,E1:E10,0,3)` | Residuos |
| `=J.Regresion(A1:D10,E1:E10,0,4)` | Resumen completo (R2, MSE, SE, t-stats) |
| `=J.Regresion(A1:D10,E1:E10,0,5)` | Intervalos de confianza 95% |

### 1.8 Clustering K-Medias

Firma: `=J.Clustering(SetDatosX, K, Semilla, TipoOutput)`

Usar las 4 columnas numericas de Iris (sin la columna de especie):

X = A1:D10:

| Formula | Resultado |
|:---|:---|
| `=J.Clustering(A1:D10,3,12345,0)` | Lista de 6 procedimientos |
| `=J.Clustering(A1:D10,3,12345,1)` | Asignacion de clusters (K=3) --> vector con cluster de cada fila |
| `=J.Clustering(A1:D10,3,12345,2)` | Centros de clusters --> matriz 3x4 |
| `=J.Clustering(A1:D10,3,12345,3)` | Asignacion de clusters (igual que 1) |
| `=J.Clustering(A1:D10,3,12345,4)` | WCSS (Within-Cluster Sum of Squares) |
| `=J.Clustering(A1:D10,6,12345,5)` | Metodo del codo (K=1..6) --> vector de WCSS |
| `=J.Clustering(A1:D10,3,12345,6)` | Descriptivas por cluster (media y std) |

**Nota sobre parametros:**
- **K**: numero de clusters deseados
- **Semilla**: semilla aleatoria para reproducibilidad
- Con datos Iris completos (150 registros), K=3 deberia separar las 3 especies

### 1.9 Optimizacion

Firma: `=J.Optimizar(Matriz, Vector, Parametro, MaxIter, TipoOutput)`

- **Matriz**: matriz A del problema (o intervalo para seccion aurea)
- **Vector**: vector b (costos, restricciones)
- **Parametro**: tasa de aprendizaje o tolerancia
- **MaxIter**: maximo de iteraciones

**Problema cuadratico** -- minimizar 0.5x'Ax - b'x:

Matriz A en A1:B2 (simetrica definida positiva), vector b en C1:C2:

| | A | B | C |
|---|---|---|---|
| 1 | 4 | 1 | 1 |
| 2 | 1 | 3 | 2 |

Solucion exacta: x = [0.0909, 0.6364]

| Formula | Resultado |
|:---|:---|
| `=J.Optimizar(A1:B2,C1:C2,0,0,0)` | Lista de 7 procedimientos |
| `=J.Optimizar(A1:B2,C1:C2,0.01,1000,1)` | Descenso de gradiente --> [0.091, 0.636] |
| `=J.Optimizar(A1:B2,C1:C2,0.01,1000,2)` | Gradiente con momentum --> [0.091, 0.636] |
| `=J.Optimizar(A1:B2,C1:C2,0,0,3)` | Metodo de Newton (1 paso, exacto) --> [0.091, 0.636] |

**Seccion aurea** -- encuentra el minimo de f(x)=x2 en un intervalo:

Intervalo en A1:A2 (ej: A1=-5, A2=5). La funcion f(x)=x2 esta predefinida en el codigo:

| Formula | Resultado |
|:---|:---|
| `=J.Optimizar(A1:A2,0,0.0001,100,4)` | Seccion aurea --> 0 (minimo de x2) |

**Programacion lineal (Simplex)** -- maximizar beneficio con restricciones:

Problema: Maximizar `5x1 + 4x2` sujeto a:
- `6x1 + 4x2 <= 24` (restriccion de recurso 1)
- `x1 + 2x2 <= 6` (restriccion de recurso 2)
- `x1, x2 >= 0`

Preparar los datos en la hoja:

Matriz de restricciones [A|b] en A1:C2 (coeficientes + lado derecho):

| | A (coef x1) | B (coef x2) | C (lado derecho) |
|---|---|---|---|
| 1 | 6 | 4 | 24 |
| 2 | 1 | 2 | 6 |

Vector de costos (funcion objetivo) en D1:D2:

| | D (costos) |
|---|---|
| 1 | 5 |
| 2 | 4 |

| Formula | Resultado |
|:---|:---|
| `=J.Optimizar(A1:C2,D1:D2,0,100,5)` | Simplex --> [3, 1.5] (beneficio maximo = 21) |

**Nota:** La condicion x1, x2 >= 0 es implicita en el metodo Simplex (no requiere parametro adicional).

**Minimos cuadrados no-negativos (NNLS)** -- resolver Ax aprox b con x>=0:

Problema: Encontrar x que minimice ||Ax - b||2 con la restriccion de que todos los valores de x sean no-negativos. Util cuando las variables representan cantidades fisicas (pesos, concentraciones, proporciones).

Usar misma matriz A en A1:B2 y vector b en C1:C2:

| | A | B | C (b) |
|---|---|---|---|
| 1 | 4 | 1 | 1 |
| 2 | 1 | 3 | 2 |

La solucion sin restriccion seria [0.091, 0.636]. Con restriccion x>=0, el resultado es similar porque ambos valores ya son positivos.

| Formula | Resultado |
|:---|:---|
| `=J.Optimizar(A1:B2,C1:C2,0.001,1000,6)` | NNLS --> [0.091, 0.636] (x>=0 satisfecho) |

**Nota:** El tercer parametro (0.001) es la tasa de aprendizaje del algoritmo iterativo. Valores mas pequenos dan mayor precision pero requieren mas iteraciones.

**Programacion cuadratica (QP)** -- minimizar 0.5x'Qx + c'x con x>=0:

Problema: Minimizar una funcion cuadratica con restricciones de no-negatividad. Ejemplo: minimizar el costo de una mezcla de dos ingredientes donde Q representa las interacciones y c los costos lineales.

Usar misma matriz Q en A1:B2 (interacciones) y vector c en C1:C2 (costos lineales):

| | A (Q) | B (Q) | C (costos) |
|---|---|---|---|
| 1 | 4 | 1 | 1 |
| 2 | 1 | 3 | 2 |

El algoritmo busca x>=0 que minimice: 0.5*[x1,x2]*Q*[x1,x2]' + c'*[x1,x2]

| Formula | Resultado |
|:---|:---|
| `=J.Optimizar(A1:B2,C1:C2,0.01,1000,7)` | QP --> [0, 0] (minimo en el origen con x>=0) |

**Nota:** El resultado [0, 0] es correcto porque con costos positivos (c=[1,2]) y Q definida positiva, el minimo con x>=0 esta en el origen. Para obtener soluciones no triviales, usar costos negativos (ej: c=[-5, -4]).

### 1.10 Transformacion de datos

Datos en A1:D20:

| Formula | Resultado |
|:---|:---|
| `=J.Transformar(A1:D20,0,0,0)` | Lista de 6 procedimientos |
| `=J.Transformar(A1:D20,0,0,1)` | Transponer matriz |
| `=J.Transformar(A1:D20,2,0,2)` | Ordenar por columna 2 |
| `=J.Transformar(A1:D20,1,0,5)` | Valores unicos de columna 1 |
| `=J.Transformar(A1:D20,1,0,6)` | Tabla de frecuencias columna 1 |

### 1.11 Enviar datos a Pluto

```
=NEVEN.pluto.data(A1:D20, "datos")             --> Envia rango a Julia
=NEVEN.notebook.open("excel_data")             --> Abre dashboard con datos
```

------------------------------------------------------------------------

## 2. R -- Estadistica y Graficos con Rangos

### 2.1 Plotly interactivo desde rango

Datos en A1:C4 (encabezados en fila 1):

| Formula | Resultado |
|:---|:---|
| `=R.GR_PlotlyView(A1:C4,0,0,"Titulo",0)` | Lista de procedimientos |
| `=NEVEN.v(R.GR_PlotlyView(A1:C4,0,0,"Titulo",1))` | Lineas + Marcadores |
| `=NEVEN.v(R.GR_PlotlyView(A1:C4,0,0,"Titulo",2))` | Barras |
| `=NEVEN.v(R.GR_PlotlyView(A1:C4,0,0,"Titulo",3))` | Scatter |
| `=NEVEN.v(R.GR_PlotlyView(A1:C4,0,0,"Titulo",4))` | Area |
| `=NEVEN.v(R.GR_PlotlyView(A1:C4,0,0,"Titulo",5))` | Combinado |

### 2.2 QuickPlot -- R base (rapido, PNG)

| Formula | Resultado |
|:---|:---|
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",1))` | Barras agrupadas |
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",2))` | Lineas multiserie |
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",3))` | Scatter |
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",4))` | Histograma |
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",5))` | Box Plot |
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",6))` | Pie (circular) |

### 2.3 QuickPlot -- ggplot2 + Plotly (interactivo)

| Formula | Resultado |
|:---|:---|
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",7))` | ggplot2 Barras |
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",8))` | ggplot2 Lineas |
| `=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",9))` | ggplot2 Scatter |

### 2.4 Estadistica directa

| Formula | Resultado |
|:---|:---|
| `=NEVEN.r("mean(c(10,20,30,40,50))")` | Media |
| `=NEVEN.r("sd(c(10,20,30,40,50))")` | Desviacion estandar |
| `=NEVEN.r("cor(c(1,2,3,4,5), c(2,4,5,4,5))")` | Correlacion |
| `=NEVEN.r("t.test(c(10,20,30), c(15,25,35))$p.value")` | Test t (p-value) |

### 2.5 ggplot2 avanzado

```
=NEVEN.v(NEVEN.r("library(ggplot2); library(plotly); p <- ggplot(mtcars, aes(wt, mpg, color=factor(cyl))) + geom_point(size=3) + ggtitle('Motor Trend Cars'); f <- 'C:/NEVEN/webview2-data/mtcars.html'; htmlwidgets::saveWidget(ggplotly(p), f, selfcontained=TRUE); f"))
```

------------------------------------------------------------------------

## 3. R -- Analisis de Datos Interactivo

### 3.1 Tabla Pivote (rpivotTable)

Firma: `=R.Pivot(SetDatosX, TipoOutput)`

Datos de ejemplo en A1:E11 (ventas por region):

| | A (Region) | B (Producto) | C (Vendedor) | D (Ventas) | E (Trimestre) |
|---|---|---|---|---|---|
| 1 | Region | Producto | Vendedor | Ventas | Trimestre |
| 2 | Norte | Laptop | Ana | 1500 | Q1 |
| 3 | Sur | Tablet | Carlos | 800 | Q1 |
| 4 | Norte | Laptop | Ana | 2200 | Q2 |
| 5 | Este | Monitor | Luis | 950 | Q1 |
| 6 | Sur | Laptop | Carlos | 1800 | Q2 |
| 7 | Norte | Tablet | Ana | 600 | Q3 |
| 8 | Este | Laptop | Luis | 2100 | Q3 |
| 9 | Sur | Monitor | Carlos | 750 | Q3 |
| 10 | Norte | Laptop | Ana | 2500 | Q4 |
| 11 | Este | Tablet | Luis | 900 | Q4 |

| Formula | Resultado |
|:---|:---|
| `=R.Pivot(A1:E11, 0)` | Lista de procedimientos |
| `=NEVEN.v(R.Pivot(A1:E11, 1))` | Pivot interactivo (drag-and-drop libre) |
| `=NEVEN.v(R.Pivot(A1:E11, 2))` | Pivot con Heatmap |
| `=NEVEN.v(R.Pivot(A1:E11, 3))` | Pivot con barras horizontales |

**Nota:** En el pivot interactivo puede arrastrar columnas a filas, columnas, y seleccionar la agregacion (Count, Sum, Average, etc.).

### 3.2 Explorador de Datos (Plotly.js)

Firma: `=R.Esquisse(SetDatosX, TipoOutput)`

Genera un explorador interactivo con selectores para ejes X, Y, color y tipo de grafico.

| Formula | Resultado |
|:---|:---|
| `=R.Esquisse(A1:E11, 0)` | Lista de procedimientos |
| `=NEVEN.v(R.Esquisse(A1:E11, 1))` | Explorador interactivo |

**Tipos disponibles en el explorador:** Scatter, Barras, Lineas, Box Plot, Histograma, Heatmap. Seleccione el tipo y los ejes desde los controles en la barra superior.

### 3.3 Visualizaciones D3.js

Firma: `=R.D3(SetDatosX, TipoOutput)`

Visualizaciones avanzadas con D3.js. Los datos deben tener columnas categoricas (para jerarquias) y al menos una columna numerica (para valores).

| Formula | Resultado |
|:---|:---|
| `=R.D3(A1:E11, 0)` | Lista de procedimientos |
| `=NEVEN.v(R.D3(A1:E11, 1))` | Treemap (jerarquia por Region/Producto/Vendedor) |
| `=NEVEN.v(R.D3(A1:E11, 2))` | Sankey (flujo Region --> Producto) |
| `=NEVEN.v(R.D3(A1:E11, 3))` | Sunburst (jerarquia circular) |
| `=NEVEN.v(R.D3(A1:E11, 4))` | Force Graph (red de relaciones) |

**Nota:** El Force Graph permite arrastrar nodos interactivamente. El Treemap y Sunburst muestran tooltips al pasar el mouse.

### 3.4 Dashboard Todo-en-Uno

Firma: `=R.Dashboard(SetDatosX, TipoOutput)`

Combina Pivot + Explorador + Treemap + Sankey + Sunburst + Force Graph en una sola pagina con tabs.

| Formula | Resultado |
|:---|:---|
| `=R.Dashboard(A1:E11, 0)` | Lista de procedimientos |
| `=NEVEN.v(R.Dashboard(A1:E11, 1))` | Dashboard completo (6 tabs) |

**Tabs disponibles:** Pivot Table, Explorador, Treemap, Sankey, Sunburst, Force Graph. Cada tab se carga al hacer clic (lazy loading).

### 3.5 Mapas Interactivos (Leaflet.js)

Firma: `=R.Map(SetDatosX, TipoOutput)`

Datos: Col1=Latitud, Col2=Longitud, Col3=Etiqueta o Valor, Col4=Popup (opcional).

Datos de ejemplo en A1:D6 (ciudades de Costa Rica):

| | A (Lat) | B (Lon) | C (Ciudad) | D (Poblacion) |
|---|---|---|---|---|
| 1 | Lat | Lon | Ciudad | Poblacion |
| 2 | 9.93 | -84.08 | San Jose | 350000 |
| 3 | 10.00 | -84.12 | Heredia | 130000 |
| 4 | 10.01 | -83.85 | Cartago | 155000 |
| 5 | 10.47 | -84.01 | Alajuela | 290000 |
| 6 | 9.86 | -83.92 | Paraiso | 60000 |

| Formula | Resultado |
|:---|:---|
| `=R.Map(A1:D6, 0)` | Lista de procedimientos |
| `=NEVEN.v(R.Map(A1:D6, 1))` | Mapa con marcadores |
| `=NEVEN.v(R.Map(A1:D6, 2))` | Mapa de calor |
| `=NEVEN.v(R.Map(A1:D6, 3))` | Circulos proporcionales (tamano = poblacion) |

**Nota:** El mapa usa tiles CartoDB oscuros (dark theme). Detecta automaticamente las columnas de latitud y longitud por nombre (Lat, Lon, Latitude, Longitude).

------------------------------------------------------------------------

## 4. Quarto -- Reportes Profesionales

| Formula | Resultado |
|:---|:---|
| `=NEVEN.q("C:/NEVEN/quarto/test_report.qmd")` | Reporte basico |
| `=NEVEN.q("C:/NEVEN/quarto/data_report.qmd")` | Reporte de datos |
| `=NEVEN.q("C:/NEVEN/quarto/analisis_ventas.qmd")` | Analisis de ventas |
| `=NEVEN.q("C:/NEVEN/quarto/julia_stats.qmd")` | Capacidades Julia |

------------------------------------------------------------------------

## 5. Pluto.jl -- Notebooks Interactivos

### 5.1 Flujo basico

```
=NEVEN.pluto.start()                           --> Inicia servidor
=NEVEN.notebook.open("linalg_decomposition")   --> Abre notebook
=NEVEN.pluto.stop()                            --> Detiene servidor
```

### 5.2 Enviar datos de Excel a Pluto

```
=NEVEN.pluto.data(A1:D20, "datos")             --> Envia rango a Julia
=NEVEN.notebook.open("excel_data")             --> Abre dashboard con datos
```

### 5.3 Codigo Julia para celdas Pluto

**PCA:**
```julia
using MultivariateStats, LinearAlgebra
num_cols = [j for j in 1:length(headers) if raw_data[1,j] isa Number]
X = Float64[raw_data[i,j] for i in 1:size(raw_data,1), j in num_cols]
model = fit(PCA, X'; maxoutdim=2)
println("Varianza explicada: ", round.(principalvars(model) ./ tvar(model) * 100, digits=2), "%")
```

**Grafico:**
```julia
using Plots
labels = [string(raw_data[i,1]) for i in 2:size(raw_data,1)]
vals = [Float64(raw_data[i,2]) for i in 2:size(raw_data,1)]
bar(labels, vals, title="Datos desde Excel", ylabel="Valor")
```

------------------------------------------------------------------------

## 6. WebView2 -- Visualizacion Directa

| Formula | Resultado |
|:---|:---|
| `=NEVEN.v("<html><body><h1>Hola</h1></body></html>")` | HTML directo |
| `=NEVEN.v("C:/ruta/archivo.html")` | Archivo HTML |
| `=NEVEN.editor()` | Editor de presentaciones Impress.js |

------------------------------------------------------------------------

## 7. Ribbon -- Botones Disponibles

| Boton | Accion |
|:---|:---|
| **Consola R** | Abre Rgui.exe |
| **Consola Julia** | Abre terminal Julia |
| **Actualizar** | Re-registra funciones R y Julia |
| **Abrir HTML** | Dialogo para seleccionar archivo HTML |
| **Presentaciones** | Editor Impress.js en WebView2 |
| **Cerrar Visores** | Cierra todas las ventanas WebView2 |
| **Iniciar Pluto** | Arranca servidor Pluto.jl |
| **Notebooks** | Lista de notebooks disponibles |
| **Detener Pluto** | Detiene servidor Pluto.jl |
| **Renderizar QMD** | Seleccionar y renderizar documento Quarto |
| **Carpeta Scripts** | Abre C:\NEVEN en el explorador |
| **Config JSON** | Abre neven-config.json en editor |
| **Acerca de** | Informacion del proyecto |

------------------------------------------------------------------------

## 8. Migracion de nombres -- RJ2XCL a NEVEN

La siguiente tabla muestra el mapeo completo de nombres de formulas entre la version anterior (RJ2XCL) y la version actual (NEVEN):

| Nombre anterior (RJ2XCL) | Nombre nuevo (NEVEN) |
|:---|:---|
| `=RJ2XCL.VIEW(...)` | `=NEVEN.v(...)` |
| `=RJ2XCL.VIEWER.CLOSE(...)` | `=NEVEN.v.close(...)` |
| `=RJ2XCL.VIEWER.LIST()` | `=NEVEN.v.list()` |
| `=RJ2XCL.VIEWER.SEND(...)` | `=NEVEN.v.send(...)` |
| `=RJ2XCL.R(...)` | `=NEVEN.r(...)` |
| `=RJ2XCL.J(...)` | `=NEVEN.j(...)` |
| `=RJ2XCL.PLUTO.START()` | `=NEVEN.pluto.start()` |
| `=RJ2XCL.PLUTO.STOP()` | `=NEVEN.pluto.stop()` |
| `=RJ2XCL.PLUTO.DATA(...)` | `=NEVEN.pluto.data(...)` |
| `=RJ2XCL.NOTEBOOK.OPEN(...)` | `=NEVEN.notebook.open(...)` |
| `=RJ2XCL.QUARTO(...)` | `=NEVEN.q(...)` |
| `=RJ2XCL.ABOUT()` | `=NEVEN.about()` |
| `=RJ2XCL.HELP()` | `=NEVEN.help()` |
| `=RJ2XCL.EDITOR()` | `=NEVEN.editor()` |

**Otros cambios:**

| Elemento | Anterior | Nuevo |
|:---|:---|:---|
| Directorio de instalacion | `C:\RJ2XCL\` | `C:\NEVEN\` |
| Archivo de configuracion | `rj2xcl-config.json` | `neven-config.json` |
| Binario XLL | `RJ2XCL64.xll` | `NEVEN64.xll` |
| Ribbon DLL | `RJ2XCLRibbon.dll` | `NEVENRibbon.dll` |
| Variable de entorno | `RJ2XCL_HOME` | `NEVEN_HOME` |

**Nota:** Los alias cortos `R.` y `J.` para funciones de R y Julia no cambian (ej: `=R.GR_PlotlyView(...)`, `=J.Algebra(...)`).

------------------------------------------------------------------------

*NEVEN v2.0 -- Universidad de Costa Rica -- Tesis de Maestria*