---
id: funciones-julia
title: Capitulo 4 -- Funciones Julia
sidebar_label: 4. Funciones Julia
sidebar_position: 4
---

# Capitulo 4: Funciones Julia

Julia es el motor matematico y de machine learning de NEVEN. Todas las funciones siguen el patron **TipoOutput**: el ultimo argumento selecciona que procedimiento ejecutar. Use `TipoOutput=0` para ver la lista completa.

$
\texttt{=J.Funcion(datos, parametros, TipoOutput)}
$

## 4.0 Activacion de Julia

Julia utiliza compilacion JIT (Just-In-Time) que requiere tiempo la primera vez. Para evitar retrasos al abrir Excel, Julia se activa **bajo demanda**:

1. Abra Excel normalmente (R y Python se conectan instantaneamente)
2. Cuando necesite funciones Julia, haga clic en **"Actualizar"** en la pestana NEVEN del Ribbon (grupo Motores)
3. Espere ~30-60 segundos mientras Julia compila las funciones
4. Las funciones `=J.*` quedan disponibles para toda la sesion

> **Ejecucion directa:** Puede ejecutar codigo Julia sin activar las funciones registradas usando `=NEVEN.j("codigo")`. Por ejemplo: `=NEVEN.j("sqrt(144)")` retorna 12 inmediatamente.

## 4.1 Utilidades y generacion de datos

**Firma:** `=J.Utilidades(P1, P2, P3, TipoOutput)`

| Formula | Resultado |
|:---|:---|
| `=J.Utilidades(0,0,0,0)` | Lista de procedimientos |
| `=J.Utilidades(0,0,0,1)` | Fecha y hora actual |
| `=J.Utilidades(1,100,1,2)` | Secuencia $\{1, 2, 3, \ldots, 100\}$ |
| `=J.Utilidades(A1,B1,C1,2)` | Secuencia de $A_1$ a $B_1$ con paso $C_1$ |
| `=J.Utilidades(50,0,1,3)` | 50 valores $\sim \mathcal{N}(0, 1)$ |
| `=J.Utilidades(A1,B1,C1,3)` | $A_1$ valores $\sim \mathcal{N}(\mu=B_1, \sigma=C_1)$ |
| `=J.Utilidades(50,0,10,4)` | 50 valores $\sim \text{Uniforme}(0, 10)$ |

## 4.2 Algebra lineal

**Firma:** `=J.Algebra(Matriz, VectorB, TipoOutput)`

Ejemplo: matriz $A = \begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}$ en celdas A1:B2.

| Formula | Resultado |
|:---|:---|
| `=J.Algebra(A1:B2,0,0)` | Lista de 12 procedimientos |
| `=J.Algebra(A1:B2,0,6)` | $\det(A) = -2$ |
| `=J.Algebra(A1:B2,0,4)` | Valores propios $\lambda_1, \lambda_2$ |
| `=J.Algebra(A1:B2,0,5)` | Vectores propios |
| `=J.Algebra(A1:B2,0,7)` | $\text{rango}(A) = 2$ |
| `=J.Algebra(A1:B2,0,11)` | $\text{tr}(A) = 5$ |
| `=J.Algebra(A1:B2,0,10)` | Pseudoinversa $A^+$ (Moore-Penrose) |
| `=J.Algebra(A1:B2,0,1)` | Factorizacion $PA = LU$ |
| `=J.Algebra(A1:B2,0,2)` | Factorizacion $A = QR$ |
| `=J.Algebra(A1:B2,0,3)` | Descomposicion $A = U\Sigma V^T$ (SVD) |
| `=J.Algebra(A1:B2,0,9)` | Numero de condicion $\kappa(A)$ |
| `=J.Algebra(A1:B2,C1:C2,12)` | Resolver $Ax = b$ |

## 4.3 Calculo numerico

**Firma:** `=J.Calculo(VectorX, VectorY, Parametro, TipoOutput)`

El tercer argumento **Parametro** cambia de significado:

| TipoOutput | Procedimiento | Parametro |
|:---:|:---|:---|
| 1 | Derivada numerica | No usado (0) |
| 2 | Integral (Trapecio) | No usado (0) |
| 3 | Integral (Simpson) | No usado (0) |
| 4 | Raiz (Biseccion) | Tolerancia (ej: $10^{-4}$) |
| 5 | Interpolacion lineal | Punto $x_0$ donde evaluar |
| 6 | Interpolacion Lagrange | Punto $x_0$ donde evaluar |
| 7 | Serie de Taylor | Punto $x_0$ donde evaluar |

**Ejemplo:** $f(x) = x^2$ con $X = \{0,1,2,3,4\}$, $Y = \{0,1,4,9,16\}$:

| Formula | Resultado |
|:---|:---|
| `=J.Calculo(A1:A5,B1:B5,0,1)` | Derivada $\approx \{0, 2, 4, 6, 8\}$ (es decir, $2x$) |
| `=J.Calculo(A1:A5,B1:B5,0,2)` | $\int_0^4 x^2\,dx \approx 22$ (Trapecio) |
| `=J.Calculo(A1:A5,B1:B5,0,3)` | $\int_0^4 x^2\,dx \approx 21.33$ (Simpson, $= \frac{64}{3}$) |
| `=J.Calculo(A1:A5,B1:B5,2.5,5)` | $f(2.5) \approx 6.5$ (interpolacion lineal) |
| `=J.Calculo(A1:A5,B1:B5,2.5,6)` | $f(2.5) = 6.25$ (Lagrange, exacto) |

## 4.4 Ecuaciones diferenciales

**Firma:** `=J.EDO(Intervalo, CondicionesIniciales, PasoH, TipoOutput)`

- **Intervalo**: $[t_0, t_f]$ en dos celdas (ej: A1=0, A2=5)
- **Condiciones iniciales**: $y(0)$ en dos celdas (ej: B1=1, B2=0)
- **PasoH**: paso de integracion $h$ -- mas pequeno = mas preciso

| Formula | Resultado |
|:---|:---|
| `=J.EDO(A1:A2,B1:B2,0.01,1)` | Euler explicito para $\frac{dy}{dt} = -y$ --> tabla $[t, y]$ |

:::note
Los procedimientos 2-4 (RK4, oscilador, EDO 2do orden) estan en desarrollo por un bug de scope en Julia 1.12.
:::

## 4.5 Estadistica descriptiva

**Firma:** `=J.Estadistica(Datos, DatosY, TipoOutput)`

Datos de ejemplo (Edad, Peso, Altura) en A1:C10:

| Formula | Resultado |
|:---|:---|
| `=J.Estadistica(A1:C10,0,1)` | $N$, $\bar{x}$, $s$, min, $Q_1$, mediana, $Q_3$, max por columna |
| `=J.Estadistica(A1:C10,0,2)` | Matriz de correlacion $\rho_{ij}$ |
| `=J.Estadistica(A1:C10,0,3)` | Matriz de covarianza $\Sigma$ |
| `=J.Estadistica(A1:A10,B1:B10,4)` | Test $t$ de Student: $\bar{x}_1 - \bar{x}_2$, $t$, $gl$, $SE$ |
| `=J.Estadistica(A1:C10,0,5)` | Normalizacion Min-Max: $x' = \frac{x - \min}{\max - \min}$ |
| `=J.Estadistica(A1:C10,0,6)` | Estandarizacion $Z$: $z = \frac{x - \bar{x}}{s}$ |
| `=J.Estadistica(A1:A10,0,7)` | Percentiles: $P_1, P_5, P_{10}, P_{25}, P_{50}, P_{75}, P_{90}, P_{95}, P_{99}$ |
| `=J.Estadistica(A1:C10,0,8)` | Outliers IQR: $Q_1, Q_3, IQR, n_{\text{outliers}}$ |

## 4.6 Clasificacion KNN

**Firma:** `=J.KNN(DatosX, DatosY, K, TipoOutput)`

Usar dataset Iris: 4 medidas en A:D, especie (1,2,3) en E.

| Formula | Resultado |
|:---|:---|
| `=J.KNN(A1:D10,E1:E10,3,1)` | Clasificacion KNN ($K=3$) --> accuracy y predicciones |
| `=J.KNN(A1:D10,E1:E10,3,2)` | Precision, Recall, $F_1$ por clase |
| `=J.KNN(A1:D10,E1:E10,3,3)` | Matriz de confusion |
| `=J.KNN(A1:D10,E1:E10,3,4)` | Tabla real vs predicho |
| `=J.KNN(A1:D10,E1:E10,3,5)` | Distancia al vecino mas cercano |

$
F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}
$

## 4.7 Regresion lineal

**Firma:** `=J.Regresion(DatosX, DatosY, Parametro, TipoOutput)`

$
\hat{y} = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \cdots + \beta_p x_p
$

| Formula | Resultado |
|:---|:---|
| `=J.Regresion(A1:D10,E1:E10,0,1)` | Coeficientes $\beta_i$ y $R^2$ |
| `=J.Regresion(A1:D10,E1:E10,0,2)` | Valores ajustados $\hat{y}$ |
| `=J.Regresion(A1:D10,E1:E10,0,3)` | Residuos $e = y - \hat{y}$ |
| `=J.Regresion(A1:D10,E1:E10,0,4)` | Resumen: $R^2$, $R^2_{adj}$, MSE, RMSE, $SE(\beta)$, $t$-stats |
| `=J.Regresion(A1:D10,E1:E10,0,5)` | Intervalos de confianza 95%: $\beta_i \pm 1.96 \cdot SE(\beta_i)$ |

## 4.8 Clustering K-Medias

**Firma:** `=J.Clustering(Datos, K, Semilla, TipoOutput)`

$
\text{WCSS} = \sum_{k=1}^{K} \sum_{x_i \in C_k} \|x_i - \mu_k\|^2
$

| Formula | Resultado |
|:---|:---|
| `=J.Clustering(A1:D10,3,12345,1)` | Asignacion de clusters ($K=3$) |
| `=J.Clustering(A1:D10,3,12345,2)` | Centros $\mu_k$ (matriz $K \times p$) |
| `=J.Clustering(A1:D10,3,12345,4)` | WCSS |
| `=J.Clustering(A1:D10,6,12345,5)` | Metodo del codo ($K=1\ldots6$) |
| `=J.Clustering(A1:D10,3,12345,6)` | Descriptivas por cluster ($\bar{x}$, $s$) |

## 4.9 Optimizacion

**Firma:** `=J.Optimizar(Matriz, Vector, Parametro, MaxIter, TipoOutput)`

### Problema cuadratico

Minimizar $\frac{1}{2}x^T A x - b^T x$ con $A = \begin{pmatrix} 4 & 1 \\ 1 & 3 \end{pmatrix}$, $b = \begin{pmatrix} 1 \\ 2 \end{pmatrix}$:

Solucion exacta: $x^* = A^{-1}b = \begin{pmatrix} 1/11 \\ 7/11 \end{pmatrix} \approx \begin{pmatrix} 0.091 \\ 0.636 \end{pmatrix}$

| Formula | Resultado |
|:---|:---|
| `=J.Optimizar(A1:B2,C1:C2,0.01,1000,1)` | Descenso de gradiente --> $[0.091, 0.636]$ |
| `=J.Optimizar(A1:B2,C1:C2,0.01,1000,2)` | Gradiente con momentum --> $[0.091, 0.636]$ |
| `=J.Optimizar(A1:B2,C1:C2,0,0,3)` | Newton (1 paso, exacto) --> $[0.091, 0.636]$ |

### Programacion lineal (Simplex)

Maximizar $5x_1 + 4x_2$ sujeto a $6x_1 + 4x_2 \leq 24$, $x_1 + 2x_2 \leq 6$, $x_1, x_2 \geq 0$:

$
x^* = (3, 1.5), \quad Z^* = 5(3) + 4(1.5) = 21
$

| Formula | Resultado |
|:---|:---|
| `=J.Optimizar(A1:C2,D1:D2,0,100,5)` | Simplex --> $[3, 1.5]$ (beneficio = 21) |

:::note
La condicion $x \geq 0$ es implicita en el metodo Simplex.
:::

## 4.10 Transformacion de datos

**Firma:** `=J.Transformar(Datos, Columna, Valor, TipoOutput)`

| Formula | Resultado |
|:---|:---|
| `=J.Transformar(A1:D20,0,0,1)` | Transponer $A^T$ |
| `=J.Transformar(A1:D20,2,0,2)` | Ordenar por columna 2 |
| `=J.Transformar(A1:D20,1,0,5)` | Valores unicos de columna 1 |
| `=J.Transformar(A1:D20,1,0,6)` | Tabla de frecuencias |
