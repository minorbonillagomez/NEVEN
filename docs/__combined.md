<section id='00-portada'>

# NEVEN v2.1

## Sistema Multilenguaje para el Analisis de Datos en Microsoft Excel

$
\text{Excel} \xrightarrow{\text{Named Pipes}} \begin{cases} \text{R 4.4.1} & \text{(Estadistica)} \\ \text{Julia 1.12.6} & \text{(Matematica / ML)} \end{cases} \xrightarrow{\text{WebView2}} \text{Visualizacion Interactiva}
$

**Universidad de Costa Rica**\
Maestria en Matematica Aplicada\
Autor: Minor Bonilla Gomez\
Abril 2026

---

### Que es NEVEN?

NEVEN transforma Microsoft Excel en una plataforma de ciencia de datos. Permite al usuario ejecutar funciones de **R** y **Julia** directamente desde celdas de Excel, visualizar resultados interactivos con **WebView2**, trabajar con notebooks reactivos de **Pluto.jl**, y generar reportes profesionales con **Quarto** -- todo sin salir de Excel.

### Para quien es?

- **El analista de datos** que conoce Excel pero necesita herramientas estadisticas avanzadas
- **El cientifico de datos** que quiere R o Julia pero necesita compartir resultados en Excel
- **El estudiante** que aprende estadistica y quiere experimentar sin programar

### Calificacion del proyecto

$
\text{Score} = \frac{10 + 9.5 + 9.5 + 9.5 + 9.5 + 10 + 10}{7} = \frac{68}{7} = 9.71 \quad \Rightarrow \quad \boxed{9.6/10}
$

| Dimension | Nota |
|:---|:---:|
| Funcionalidad | $10$ |
| Calidad de Codigo | $9.5$ |
| Seguridad | $9.5$ |
| Mantenibilidad | $9.5$ |
| Confiabilidad | $9.5$ |
| Testing | $10$ |
| Documentacion | $10$ |
</section>
<section id='01-introduccion'>

# Capitulo 1: Introduccion

## 1.1 El problema

Excel es la herramienta de analisis de datos mas utilizada del mundo. Sin embargo, sus capacidades estadisticas nativas son limitadas: no tiene regresion logistica, no tiene analisis de componentes principales, no tiene modelos ARIMA.

Por otro lado, R y Julia son lenguajes potentes para estadistica y matematica, pero requieren programacion -- una barrera para muchos profesionales.

$
\underbrace{\text{Excel}}_{\text{Universal pero limitado}} + \underbrace{\text{R + Julia}}_{\text{Potentes pero tecnicos}} = \underbrace{\text{NEVEN}}_{\text{Lo mejor de ambos mundos}}
$

## 1.2 La solucion

NEVEN expone funciones de R y Julia como formulas nativas de Excel. El usuario escribe:

```
=J.Algebra(A1:B2, 0, 6)
```

Y obtiene el determinante de la matriz en su celda -- sin escribir una linea de codigo Julia.

## 1.3 Evolucion del proyecto

| Version | Ano | Logro |
|:---|:---|:---|
| R4XCL | 2023 | R en Excel via BERT (tesis original) |
| NEVEN v1.0 | Ene 2026 | Fork de BERT, R 4.4.1 + Julia 1.12.6 |
| **NEVEN v2.0** | **Abr 2026** | WebView2, Pluto.jl, Quarto, Ribbon COM |
| **NEVEN v2.1** | **Jul 2026** | Python integrado, NEVEN-SIM (Monte Carlo) |

## 1.4 Ecosistema completo

```
+-----------------------------------------------------------+
|                    Microsoft Excel                         |
|                                                           |
|  +----------+  +----------+  +----------+  +--------+    |
|  | R 4.4.1  |  |Julia 1.12|  | Quarto   |  |Pluto.jl|   |
|  |Estadist. |  |Matemat.  |  |Reportes  |  |Notebook|   |
|  +----+-----+  +----+-----+  +----+-----+  +---+----+   |
|       +--------------+-----------+--------------+         |
|                    WebView2 Viewer                         |
|              (Plotly, HTML, Impress.js)                    |
+-----------------------------------------------------------+
```

## 1.5 Comparacion con BERT (proyecto base)

| Capacidad | BERT | NEVEN v2.0 |
|:---|:---:|:---:|
| Funciones R en Excel | si | si |
| Funciones Julia en Excel | si | si |
| Graficos interactivos | no | si |
| Notebooks reactivos | no | si |
| Reportes Quarto | no | si |
| Ribbon nativo | no | si |
| Sandbox de seguridad | no | si |
| Tests automatizados | 0 | 205 |
| Score | ~4/10 | **9.2/10** |
</section>
<section id='02-instalacion'>

# Capitulo 2: Instalacion

## 2.1 Requisitos del sistema

| Componente | Version minima | Descarga |
|:---|:---|:---|
| Windows | 10/11 (64 bits) | -- |
| Microsoft Excel | 2016+ o Microsoft 365 | -- |
| R | 4.4.1 | [cran.r-project.org](https://cran.r-project.org) |
| Julia | 1.12.6 | [julialang.org](https://julialang.org) |
| Pandoc | 3.6 | [github.com/jgm/pandoc](https://github.com/jgm/pandoc/releases) |
| Quarto | 1.9.18 | [quarto.org](https://quarto.org/docs/download) |
| WebView2 Runtime | -- | Preinstalado en Windows 10/11 |

## 2.2 Pasos de instalacion

### Paso 1: Copiar archivos

Copiar el contenido de `Dist/` a `C:\NEVEN\`:

```powershell
Copy-Item "Dist\*" "C:\NEVEN\" -Recurse -Force
```

### Paso 2: Crear junction para Quarto

Quarto 1.9.18 tiene un bug con rutas que contienen espacios. La solucion es un junction:

```cmd
mklink /J C:\Quarto "C:\Program Files\Quarto"
```

### Paso 3: Registrar el Ribbon COM

```powershell
regsvr32 "C:\NEVEN\NEVENRibbon.dll"
```

### Paso 4: Cargar el XLL en Excel

1. Abrir Excel
2. Archivo --> Opciones --> Complementos
3. En "Administrar", seleccionar "Complementos de Excel" --> Ir
4. Examinar --> `C:\NEVEN\NEVEN64.xll`

## 2.3 Verificacion rapida

Despues de la instalacion, verificar en celdas de Excel:

$
\texttt{=NEVEN.r("1+1")} \rightarrow 2 \qquad \texttt{=NEVEN.j("sqrt(144)")} \rightarrow 12
$

## 2.4 Checklist completo

| # | Verificacion | Formula | Resultado esperado |
|:---|:---|:---|:---|
| 1 | R operativo | `=NEVEN.r("1+1")` | $2$ |
| 2 | Julia operativa | `=NEVEN.j("1+1")` | $2$ |
| 3 | WebView2 | `=NEVEN.v("<html><body>OK</body></html>")` | Ventana |
| 4 | Pluto.jl | `=NEVEN.pluto.status()` | "stopped" |
| 5 | Quarto | `=NEVEN.q("C:/NEVEN/quarto/test_report.qmd")` | Reporte |
| 6 | Ribbon | Pestana NEVEN en cinta | 13 botones |

## 2.5 Estructura de directorios

```
C:\NEVEN\
+-- NEVEN64.xll              # Add-in Excel
+-- NEVENRibbon.dll           # Ribbon COM
+-- ControlR.exe               # Motor R
+-- ControlJulia.exe           # Motor Julia
+-- neven-config.json         # Configuracion
+-- neven-languages.json      # R + Julia
+-- startup\                   # Scripts de inicio
+-- notebooks\                 # 15 notebooks Pluto
+-- data\                      # Datasets Excel<-->Pluto
+-- quarto\                    # Documentos .qmd
+-- CreadorPresentaciones\     # Editor Impress.js
+-- crashes\                   # Telemetria local
+-- webview2-data\             # HTML temporales
```

## 2.6 Paquetes R recomendados

```r
install.packages(c(
    "plotly", "htmlwidgets", "ggplot2",
    "lme4", "survival", "psych", "forecast",
    "car", "Hmisc", "rstanarm", "plm",
    "stargazer", "sandwich", "lmtest"
), repos = "https://cran.r-project.org")
```

## 2.7 Paquetes Julia recomendados

```julia
import Pkg
Pkg.add(["Pluto", "Plots", "DataFrames", "CSV",
         "MultivariateStats", "JuMP", "HiGHS"])
```
</section>
<section id='03-arquitectura'>

# Capitulo 3: Arquitectura del Sistema

## 3.1 Vision general

NEVEN se organiza en 4 capas, cada una con responsabilidades claras:

$
\underbrace{\text{Interface Excel}}_{\text{Capa 1}} \rightarrow \underbrace{\text{Servicios Nucleo}}_{\text{Capa 2}} \rightarrow \underbrace{\text{Subsistemas}}_{\text{Capa 3}} \rightarrow \underbrace{\text{Herramientas}}_{\text{Capa 4}}
$

### Capa 1: Interface Excel (XLL)

El punto de entrada. Registra ~200 funciones en Excel, gestiona el ciclo de vida del add-in, y crea la toolbar.

| Componente | Responsabilidad |
|:---|:---|
| `RJ2XCL_Engine` | Singleton principal: Init, Close, callbacks |
| `basic_functions` | ~200 funciones exportadas a Excel |
| `MenuService` | Toolbar CommandBar (legacy, deshabilitado) |
| `NEVENRibbon.dll` | Ribbon COM nativo con iconos |

### Capa 2: Servicios del Nucleo

La logica de negocio: configuracion, lenguajes, seguridad, logging.

| Servicio | Responsabilidad |
|:---|:---|
| `ConfigService` | Lee `neven-config.json`, valida paths, getters tipados |
| `LanguageManager` | Orquesta R y Julia: conexion, health, dispatch |
| `LanguageService` | Un proceso hijo: pipe, timeout, reconnect |
| `SandboxVerifier` | Valida codigo antes de ejecucion |
| `SecurityService` | SHA-256 para integridad de archivos |
| `DiscoveryService` | Detecta R y Julia en el sistema |
| `LogService` | Logging estructurado a archivo |

### Capa 3: Subsistemas Especializados

Los componentes que hacen a NEVEN unico:

| Subsistema | Componentes |
|:---|:---|
| **WebView2** | ViewerManager, ViewerWindow, ContentPipeline, PostMessageBridge |
| **Pluto.jl** | PlutoManager, NotebookLibrary, NotebookExporter |
| **Quarto** | Integrado en `basic_functions.cc` (CreateProcess) |
| **Presentaciones** | PresentationBuilder, CreadorPresentaciones (Impress.js) |

### Capa 4: Herramientas Comunes

Utilidades compartidas por todas las capas:

| Herramienta | Uso |
|:---|:---|
| `Pipe` | Named Pipe wrapper (connect, read, write) |
| `type_conversions` | XLOPER12 <--> Protobuf Variable |
| `json11` | Parser JSON ligero |
| `child_process_log` | Logging para procesos hijo |

## 3.2 Comunicacion entre componentes

$
\text{Excel} \xrightleftharpoons[\text{Protobuf}]{\text{Named Pipe}} \text{ControlR/Julia} \xrightarrow{\text{TSV}} \text{Pluto.jl}
$

El protocolo de comunicacion usa **Protocol Buffers** sobre **Named Pipes**:

1. Excel serializa argumentos como `Variable` (Protobuf)
2. Envia por pipe a ControlR.exe o ControlJulia.exe
3. El proceso hijo ejecuta la funcion R/Julia
4. Serializa el resultado como `Variable`
5. Retorna por pipe al XLL
6. El XLL convierte a `XLOPER12` para Excel

## 3.3 Flujo de inicializacion

```
xlAutoOpen()
  +-- LogService::Initialize()
  +-- ConfigService::Initialize()           <-- neven-config.json
  +-- SecurityService::Initialize()
  +-- LanguageManager::ConfigureLanguages() <-- neven-languages.json
  |    +-- LanguageService[R]::Connect()    --> ControlR.exe
  |    +-- LanguageService[Julia]::Connect() --> ControlJulia.exe
  +-- ViewerManager::Initialize()           <-- WebView2 STA thread
  +-- PlutoManager::Initialize()
  +-- MapFunctions() + xlfRegister          <-- ~200 funciones
  +-- Timer(5s) --> UpdateFunctions()
```

## 3.4 Decisiones arquitectonicas clave

| Decision | Justificacion |
|:---|:---|
| Procesos hijo separados | Crash de R no mata Excel |
| Protobuf para IPC | Versionable, eficiente, agnostico |
| WebView2 en STA thread | COM apartment threading requerido |
| TSV para Excel<-->Pluto | Procesos separados, no comparten memoria |
| Quarto como CreateProcess | No bloquea el pipe, timeout 60s |
| `require_secret_for_access=false` | Pluto 0.20 requiere token; localhost es seguro |
| Junction `C:\Quarto` | Workaround para bug de Sass |


## 3.6 NEVEN-SIM: Modulo de Simulacion (XLL separado)

NEVEN-SIM es un add-in XLL independiente que carga junto a NEVEN64.xll. Proporciona simulacion Monte Carlo, fitting de distribuciones y analisis de sensibilidad.

### Comunicacion Inter-XLL

```
NEVEN-SIM.xll --[xlUDF]--> NEVEN64.xll --[Named Pipe]--> ControlR/Julia
```

NEVEN-SIM usa `xlUDF` para llamar funciones registradas por NEVEN base (`NEVEN.r`, `NEVEN.j`, `NEVEN.v`). No tiene sus propios procesos hijo.

### Componentes

| Componente | Responsabilidad |
|:---|:---|
| `SimBridge` | Relay a R/Julia via xlUDF (lazy detection) |
| `SimEngine` | Orquestador: Fit → Simulate → Analyze |
| `FitService` | Genera codigo R (fitdistrplus) |
| `MonteCarloService` | Genera codigo Julia (Distributions.jl) |
| `SensitivityService` | Spearman rank correlation |
| `SimViewerManager` | Genera HTML y abre viewer |

### Explorador Reactivo

El viewer de NEVEN-SIM incluye un simulador Monte Carlo 100% JavaScript que permite explorar escenarios en tiempo real (<100ms para 200K muestras). Soporta 7 distribuciones, comparacion de escenarios y sliders interactivos.

Referencia completa: **Capitulo 12 - Simulacion Monte Carlo**
</section>
<section id='04-funciones-julia'>

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
</section>
<section id='05-funciones-r'>

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
</section>
<section id='06-pluto-quarto'>

# Capitulo 6: Pluto.jl y Quarto

## 6.1 Pluto.jl -- Notebooks reactivos

Pluto.jl permite trabajar con notebooks Julia interactivos directamente desde Excel. Los notebooks son **reactivos**: al cambiar una celda, todas las celdas dependientes se recalculan automaticamente.

### Flujo basico

```
=NEVEN.pluto.start()                           --> Inicia servidor
=NEVEN.notebook.open("linalg_decomposition")   --> Abre notebook
=NEVEN.pluto.stop()                            --> Detiene servidor
```

### Pipeline de datos Excel --> Pluto

$
\text{Excel} \xrightarrow{\texttt{PLUTO.DATA}} \text{Julia (pipe)} \xrightarrow{\text{TSV}} \text{Pluto.jl}
$

```
=NEVEN.pluto.data(A1:D20, "datos")             --> Envia rango a Julia
=NEVEN.notebook.open("excel_data")             --> Abre dashboard
```

El notebook `excel_data` muestra automaticamente:
- Vista previa de datos (primeras 20 filas)
- Estadisticas descriptivas ($N$, $\bar{x}$, $s$, min, max)
- Seccion editable para analisis personalizado

### PCA desde Excel

En una celda del notebook Pluto:

```julia
using MultivariateStats, LinearAlgebra
num_cols = [j for j in 1:length(headers) if raw_data[1,j] isa Number]
X = Float64[raw_data[i,j] for i in 1:size(raw_data,1), j in num_cols]
model = fit(PCA, X'; maxoutdim=2)
println("Varianza explicada: ",
    round.(principalvars(model) ./ tvar(model) * 100, digits=2), "%")
```

### Grafico en Pluto

```julia
using Plots
labels = [string(raw_data[i,1]) for i in 2:size(raw_data,1)]
vals = [Float64(raw_data[i,2]) for i in 2:size(raw_data,1)]
bar(labels, vals, title="Datos desde Excel", ylabel="Valor")
```

### Notebooks disponibles (15)

| # | Notebook | Categoria |
|:---|:---|:---|
| 1-7 | stats_regression, lme4_mixed_models, survival_analysis, forecast_arima, psych_factor_analysis, plm_panel_econometrics, rstanarm_bayes | R via RCall |
| 8-12 | jump_optimization, diffeq_simulation, turing_hierarchical, montecarlo_risk, linalg_decomposition | Julia nativo |
| 13 | multilang_pipeline | Mixto R+Julia |
| 14 | excel_dashboard | Demo ventas |
| 15 | excel_data | **Generico NxP** |

---

## 6.2 Quarto -- Reportes profesionales

Quarto renderiza documentos `.qmd` a HTML y los muestra en WebView2:

$
\texttt{.qmd} \xrightarrow{\text{Quarto CLI}} \texttt{.html} \xrightarrow{\text{WebView2}} \text{Excel}
$

```
=NEVEN.q("C:/NEVEN/quarto/analisis_ventas.qmd")
```

### Documentos de ejemplo

| Documento | Contenido |
|:---|:---|
| `test_report.qmd` | Reporte basico del sistema |
| `data_report.qmd` | Reporte de datos |
| `analisis_ventas.qmd` | Analisis de negocio |
| `julia_stats.qmd` | Capacidades de Julia |

### Crear un documento Quarto propio

Crear archivo `mi_reporte.qmd` en `C:\NEVEN\quarto\`:

```yaml
---
title: "Mi Reporte"
format:
  html:
    self-contained: true
    theme: none
    minimal: true
---

## Resultados

| Metrica | Valor |
|---------|-------|
| Media   | 42    |
| Std     | 7.3   |
```

Renderizar desde Excel:
```
=NEVEN.q("C:/NEVEN/quarto/mi_reporte.qmd")
```
</section>
<section id='07-webview2-ribbon'>

# Capitulo 7: WebView2 y Ribbon

## 7.1 WebView2 -- Visualizacion embebida

WebView2 (basado en Microsoft Edge Chromium) permite renderizar contenido HTML interactivo en ventanas flotantes asociadas a Excel.

### Dark mode viewer

El viewer WebView2 usa un fondo grafito (#2D2D2D) por defecto, proporcionando un tema oscuro consistente para todas las visualizaciones interactivas (Plotly, D3.js, Leaflet, rpivotTable). Esto reduce la fatiga visual y mejora el contraste de los graficos.

### Modos de uso

| Formula | Contenido |
|:---|:---|
| `=NEVEN.v("<html>...</html>")` | HTML directo (inline) |
| `=NEVEN.v("C:/ruta/archivo.html")` | Archivo HTML local |
| `=NEVEN.v(R.GR_PlotlyView(...))` | Grafico Plotly desde R |
| `=NEVEN.v(R.Pivot(...))` | Tabla pivote interactiva |
| `=NEVEN.v(R.D3(...))` | Visualizacion D3.js |
| `=NEVEN.v(R.Dashboard(...))` | Dashboard todo-en-uno |
| `=NEVEN.v(R.Map(...))` | Mapa interactivo Leaflet |
| `=NEVEN.editor()` | Editor de presentaciones Impress.js |

### Seguridad del viewer

El filtro de navegacion permite solo contenido confiable:

| Permitido | Ejemplo |
|:---|:---|
| `file://` | Archivos HTML locales |
| `about:blank` | Pagina vacia |
| `data:`, `blob:` | Plotly image export, D3.js SVG |
| CDNs confiables | jsdelivr, cloudflare, Google Fonts |
| `localhost:port` | Solo en modo Pluto (Advanced Mode) |

Todo lo demas se bloquea con log de advertencia.

### Funciones del viewer

| Formula | Accion |
|:---|:---|
| `=NEVEN.v.list()` | Lista viewers activos (ej: "viewer-1, viewer-2") |
| `=NEVEN.v.close("viewer-1")` | Cierra un viewer especifico |
| `=NEVEN.v.send("viewer-1", json)` | Envia datos JSON al JavaScript del viewer |

---

## 7.2 Ribbon COM -- Interfaz nativa

La pestana **NEVEN** en la cinta de Excel proporciona acceso directo a todas las funcionalidades:

### Grupos y botones

| Grupo | Boton | Icono | Accion |
|:---|:---|:---|:---|
| **Motores** | Consola R | Logo R | Abre Rgui.exe |
| | Consola Julia | Logo Julia | Abre terminal Julia |
| | Instalar Paquete R | Logo R | Dialogo para instalar paquete desde CRAN |
| | Instalar Paquete Julia | Logo Julia | Dialogo para instalar paquete Julia |
| | Paquetes R | Logo R | Lista paquetes R instalados |
| | Paquetes Julia | Logo Julia | Lista paquetes Julia instalados |
| | Actualizar | (refresh) | Re-registra funciones |
| **Visualizacion** | Abrir HTML | (chart) | Dialogo de seleccion de archivo |
| | Presentaciones | (slides) | Editor Impress.js |
| | Listar Visores | (list) | Muestra viewers activos |
| | Cerrar Visores | (close) | Cierra todas las ventanas WebView2 |
| **Pluto.jl** | Iniciar Pluto | (web) | Arranca servidor Pluto.jl |
| | Notebooks | (folder) | Lista de notebooks disponibles |
| | Detener Pluto | (stop) | Detiene servidor |
| **Quarto** | Renderizar QMD | Logo Quarto | Seleccionar y renderizar .qmd |
| **Configuracion** | Carpeta Scripts | (folder) | Abre `C:\NEVEN\` en explorador |
| | Config JSON | (gear) | Abre `neven-config.json` |
| | Acerca de | Logo NEVEN | Informacion del proyecto |

### Solucion de problemas del Ribbon

Si el Ribbon desaparece despues de un crash de Excel:

```powershell
# Limpiar la lista de add-ins deshabilitados
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\DisabledItems" -Force

# Verificar registro
regsvr32 "C:\NEVEN\NEVENRibbon.dll"
```
</section>
<section id='08-seguridad-testing'>

# Capitulo 8: Seguridad y Testing

## 8.1 Sandbox de seguridad

Cuando el usuario ejecuta codigo arbitrario con `=NEVEN.r("...")` o `=NEVEN.j("...")`, el sandbox bloquea operaciones peligrosas **antes** de enviarlas al motor.

### Patrones bloqueados en R

| Categoria | Comandos bloqueados |
|:---|:---|
| Shell | `system()`, `system2()`, `shell()`, `shell.exec()`, `pipe()` |
| Archivos | `file.remove()`, `unlink()`, `file.rename()` |
| Red | `download.file()`, `url()`, `socketConnection()` |
| Codigo dinamico | `eval(parse())`, `do.call()`, `get()`, `.Call()` |
| Entorno | `Sys.setenv()`, `setwd()` |

### Patrones bloqueados en Julia

| Categoria | Comandos bloqueados |
|:---|:---|
| Shell | `run()`, `pipeline()`, backtick literals |
| Codigo nativo | `ccall()`, `@ccall`, `cglobal()`, `unsafe_*` |
| Codigo dinamico | `eval()`, `Meta.parse()`, `include()` |

### Proteccion contra bypass

$
\texttt{sys tem()} \xrightarrow{\text{strip whitespace}} \texttt{system()} \xrightarrow{\text{match}} \text{BLOQUEADO}
$

- Whitespace stripping normaliza antes de comparar
- String concatenation (`paste0("sys","tem()")`) se detecta
- Case insensitive: `SYSTEM()` = `system()`

### Verificacion de integridad SHA-256

Al iniciar, NEVEN calcula el hash SHA-256 de los scripts criticos (`startup.r`, `startup.jl`) y lo compara con el valor almacenado. Si el hash no coincide, el motor correspondiente no se carga y se registra una advertencia en el log. Esto previene la ejecucion de scripts modificados por terceros.

$
\text{SHA-256}(\texttt{startup.r}) = h_{\text{actual}} \stackrel{?}{=} h_{\text{esperado}} \quad \Rightarrow \quad \begin{cases} \text{OK: cargar motor} \\ \text{FAIL: bloquear + log} \end{cases}
$

:::note
Las funciones registradas (`=R.MR_Lineal(...)`, `=J.Algebra(...)`) **no** pasan por el sandbox -- se ejecutan directamente via el pipe.
:::

## 8.2 Validacion de configuracion

`ConfigService` valida `neven-config.json` al cargar:

- Paths no contienen `..` (path traversal)
- Paths no contienen `|`, `&`, `;`, `` ` `` (command injection)
- `callTimeoutMs` en rango $[0, 1\,800\,000]$
- `maxRetries` en rango $[0, 10]$

## 8.3 Suite de tests

| Categoria | Tests | Cobertura |
|:---|:---:|:---|
| Sandbox (R + Julia + Python) | 109 | Patrones bloqueados, bypass prevention |
| NewFunctionsSandboxTest | 16 | Pivot, D3, Esquisse, Map sandbox validation |
| E2ETest | 8 | Rename verification, config keys, version |
| Property-based (reliability) | 3 | Timeout clamping, error messages |
| Property-based (WebView2) | 5 | Size routing, content detection, config clamping |
| Property-based (Python sandbox) | 3 | 450 iteraciones |
| Config, Security, Discovery | 16 | Singleton, JSON, path validation |
| Type conversions, RAII | 7 | Thread safety, move semantics |
| Reliability (unit) | 35 | Health status, error formats, timeouts |
| Basic functions, COM, callbacks | 27 | Version, bounds, input validation |
| **Total** | **228** | **100% pass rate, 0 regresiones** |

### Property-Based Testing

Los tests PBT verifican propiedades universales con entradas aleatorias:

$
\forall V \in \mathbb{Z}: \text{clamp}(V, 1, 16) = \max(1, \min(16, V))
$

Cada propiedad se verifica con 150 iteraciones minimo usando `std::mt19937`.

## 8.4 Compilacion y ejecucion de tests

```powershell
# Compilar
cmake --build Build --config Release --parallel

# Ejecutar tests
.\Build\tests\Release\rj2xcl_tests.exe
```

Resultado esperado:
```
[==========] 228 tests from 27 test suites ran.
[  PASSED  ] 228 tests.
```
</section>
<section id='09-mantenimiento'>

# Capitulo 9: Mantenimiento y Desarrollo

## 9.1 Compilacion del proyecto

### Requisitos
- Visual Studio 2022 (con "Desarrollo de escritorio con C++")
- CMake 3.15+ (incluido con VS 2022)
- R 4.4.1+ y Julia 1.12.6+ instalados

### Comandos de build

```powershell
# Build completo limpio (recomendado)
powershell -ExecutionPolicy Bypass -File build.ps1 -Clean -Config Release

# O usando CMake directamente:
cmake -S . -B Build -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
cmake --build Build --config Release

# Compilar componentes individuales:
cmake --build Build --config Release --target NEVEN_Core       # XLL
cmake --build Build --config Release --target ControlJulia     # Julia
cmake --build Build --config Release --target ControlR         # R
cmake --build Build --config Release --target ControlPython    # Python
```

### Regenerar libjulia.lib (si Julia se actualiza)

```powershell
cd ControlJulia\lib
.\rebuild-julia-lib.ps1
lib /machine:X64 /def:libjulia.def /out:libjulia.lib
```

> **CRITICO:** Usar el metodo exacto del script `rebuild-julia-lib.ps1`. Otros metodos de parsing producen un `.lib` que compila pero crashea en runtime.

### Despliegue

```powershell
Stop-Process -Name "EXCEL","ControlR","ControlJulia","ControlPython" -Force -ErrorAction SilentlyContinue
taskkill /F /IM msedgewebview2.exe 2>$null
Start-Sleep -Seconds 3

Copy-Item "Build\Core\Release\NEVEN64.dll" "C:\NEVEN\NEVEN64.xll" -Force
Copy-Item "Build\ControlR\Release\ControlR.exe" "C:\NEVEN\ControlR.exe" -Force
Copy-Item "Build\ControlJulia\Release\ControlJulia.exe" "C:\NEVEN\ControlJulia.exe" -Force
Copy-Item "Build\ControlPython\Release\ControlPython.exe" "C:\NEVEN\ControlPython.exe" -Force
Copy-Item "Build\Ribbon\Release\NEVENRibbon.dll" "C:\NEVEN\NEVENRibbon.dll" -Force
regsvr32 /s "C:\NEVEN\NEVENRibbon.dll"
```

## 9.2 Agregar funciones de usuario

### Funcion R

Crear archivo `.R` en `%USERPROFILE%\Documents\NEVEN\functions\`:

```r
MiFuncion <- function(datos, parametro = 0) {
  return(sum(datos) * parametro)
}
attr(MiFuncion, "description") <- list(
  "Mi funcion personalizada",
  datos = "Rango de datos",
  parametro = "Multiplicador"
)
```

### Funcion Julia

Agregar al archivo `functions.jl`:

```julia
function MiCalculo(datos, parametro=0)
    return sum(Float64.(datos)) * parametro
end
```

Recargar con el boton **Actualizar** del Ribbon o `=RJ_UpdateFunctions()`.

## 9.3 Solucion de problemas

| Problema | Solucion |
|:---|:---|
| `#NOMBRE?` en todas las funciones | XLL no cargado --> Archivo --> Opciones --> Complementos |
| Ribbon no aparece | `regsvr32 C:\NEVEN\NEVENRibbon.dll` + limpiar resiliency |
| Excel se congela | `Stop-Process -Name "EXCEL","ControlR","ControlJulia" -Force` |
| Paquete R faltante | `=NEVEN.r("install.packages('nombre')")` |
| Julia exception | Verificar datos del rango (tipos numericos) |
| Pluto no abre | Matar procesos Julia: `Stop-Process -Name "julia" -Force` |

## 9.4 Archivos clave del codigo fuente

| Archivo | Responsabilidad |
|:---|:---|
| `RJ2XCL/src/rj2xcl.cc` | Singleton principal, Init, xlAutoOpen |
| `RJ2XCL/src/basic_functions.cc` | ~200 funciones exportadas |
| `RJ2XCL/src/language_service.cc` | Comunicacion con ControlR/Julia |
| `Common/ViewerManager.cc` | WebView2 lifecycle |
| `Common/PlutoManager.cc` | Pluto.jl lifecycle |
| `Common/ConfigService.cc` | Configuracion centralizada |
| `Common/SandboxVerifier.cc` | Validacion de seguridad |
| `Ribbon/ribbon_connect.h` | Ribbon COM callbacks |
| `startup/startup.jl` | Modulo NEVEN Julia |
| `libreria/JULIA/functions.jl` | Funciones Julia (9 modulos + aliases) |

## 9.5 Fixes criticos (no revertir)

| Fix | Archivo | Impacto si se revierte |
|:---|:---|:---|
| Firma MdCallBack12 | `xlcall_stubs.cc` | Todas las llamadas a Excel API fallan |
| Complex.h para MSVC | `ControlR/include/R_ext/Complex.h` | ControlR.exe crashea |
| thread_local XLOPER12 | `basic_functions.cc` | Corrupcion en recalculo paralelo |
| Startup wait=true | `language_service.cc` | Pipe se desincroniza |
| CharacterMode=LinkDLL | `rinterface_win.cc` | ControlR crashea sin consola |
</section>
<section id='10-ejemplos'>
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
| **Consola** | Abre la consola REPL WebView2 (R, Julia, Python en tabs) |
| **Instalar Paquetes** | Dialogo unificado para instalar paquetes (R, Julia o Python) |
| **Actualizar** | Re-registra funciones R, Julia y Python |
| **Estado** | Muestra estado de conexion de los motores |
| **Abrir Visor** | Abre contenido HTML en el visor WebView2 |
| **Listar Visores** | Lista visores activos |
| **Cerrar Todos** | Cierra todas las ventanas WebView2 |
| **Iniciar Pluto** | Arranca servidor Pluto.jl |
| **Detener** | Detiene servidor Pluto.jl |
| **Biblioteca** | Lista de notebooks disponibles |
| **Nueva Presentacion** | Crea presentacion reveal.js |
| **Diccionario** | Abre el catalogo completo de funciones con ejemplos |
| **Documentacion** | Abre la documentacion de 12 capitulos en el visor |
| **Ajustes** | Abre neven-config.json |
| **Acerca de** | Informacion del proyecto |

------------------------------------------------------------------------

## 8. Recursos y Ejemplos

Los archivos de ejemplo se encuentran organizados en `libreria/EJEMPLOS/`:

| Carpeta | Contenido |
|:---|:---|
| `libreria/EJEMPLOS/Notebooks/` | 15 notebooks Pluto.jl precargados (PCA, algebra lineal, optimizacion, etc.) |
| `libreria/EJEMPLOS/Excel/` | Archivos Excel de ejemplo para probar las funciones NEVEN |
| `libreria/R/` | 32 archivos .R con ~90 funciones estadisticas |
| `libreria/JULIA/` | Funciones Julia (9 modulos, ~70 procedimientos) |
| `libreria/PYTHON/` | Funciones Python (AI, Quarto) |
| `libreria/QUARTO/` | Ejemplos de documentos .qmd |

### Archivos Excel de ejemplo

Los archivos en `libreria/EJEMPLOS/Excel/` contienen datos y formulas listas para usar. Abra cualquiera de ellos con NEVEN cargado para ver las funciones en accion.

### Notebooks Pluto

Los notebooks en `libreria/EJEMPLOS/Notebooks/` cubren:
- Algebra lineal (descomposiciones, sistemas)
- Calculo numerico (integrales, EDOs)
- Estadistica (descriptiva, correlacion)
- Machine Learning (KNN, clustering)
- Optimizacion (gradiente, simplex)

Para usarlos: `=NEVEN.pluto.start()` → `=NEVEN.notebook.open("nombre")`

------------------------------------------------------------------------

*NEVEN v2.0 -- Universidad de Costa Rica -- Tesis de Maestria*
</section>
<section id='11-diccionario-funciones'>


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
</section>
<section id='12-simulacion-montecarlo'>

# Capitulo 12: Simulacion Monte Carlo (NEVEN-SIM)

## 12.1 Introduccion

NEVEN-SIM es un modulo de simulacion estocastica que extiende NEVEN con capacidades de analisis de riesgo al estilo Crystal Ball / @Risk. Opera como un XLL separado (`NEVEN-SIM.xll`) que se carga junto al add-in base.

**Capacidades:**
- Ajuste automatico de distribuciones a datos historicos (7 distribuciones)
- Simulacion Monte Carlo con hasta 10 millones de iteraciones
- Analisis de sensibilidad (Spearman rank correlation)
- Explorador reactivo de escenarios con sliders interactivos
- Exportacion de resultados a CSV

## 12.2 Instalacion

1. Copiar `NEVEN-SIM.xll` a `C:\NEVEN\`
2. Copiar `workspace\sim-report-template.html` a `C:\NEVEN\workspace\`
3. Copiar `libreria\R\neven_sim_fit.R` a `C:\NEVEN\libreria\R\`
4. Copiar `libreria\JULIA\NEVENSim.jl` a `C:\NEVEN\libreria\JULIA\`
5. En Excel: Archivo → Opciones → Complementos → Examinar → `C:\NEVEN\NEVEN-SIM.xll`
6. Instalar dependencias:
   - `=R.instalar("fitdistrplus jsonlite")`
   - `=J.Instalar("Distributions")`

## 12.3 Uso Rapido

### Verificar estado
```
=SIM.Status()
→ "NEVEN-SIM v1.0 | Base: OK | Estado: Inactivo | Supuestos: 0"
```

### Ajustar distribucion a datos
```
=SIM.Fit(A1:A50)
→ "Mejor: weibull(p1=16.29, p2=8.22) AIC=222 | 2: norm(...) | 3: gamma(...)"
```

### Simulacion completa (sin reporte visual)
```
=SIM.QuickRun(A1:A50, "(x) -> x * 1.1", 100000)
```

### Simulacion con reporte interactivo
```
=SIM.QuickRun(A1:A50, "(x) -> x * 1.1", 100000, 1)
```
Abre un viewer con histograma + sliders reactivos.

### Ver muestras simuladas
```
=SIM.Datos(100)
```
Retorna las primeras 100 muestras como array dinamico.

### Exportar a CSV
```
=SIM.Exportar()
→ "OK: 100000 registros -> C:/NEVEN/data/sim_results_20260716_093012.csv"
```

## 12.4 El Modelo

El parametro `modelo` es una funcion anonima de Julia que se aplica a cada muestra:

| Modelo | Significado |
|:---|:---|
| `(x) -> x` | Sin transformacion (distribucion tal cual) |
| `(x) -> x * 1.1` | Crecimiento del 10% |
| `(x) -> x - 500` | Resta un costo fijo |
| `(x) -> max(x - 100, 0)` | Ganancia si supera umbral (tipo opcion) |
| `(x) -> x * 0.3` | Margen del 30% |

## 12.5 Distribuciones Soportadas

El fitting automatico evalua estas distribuciones por AIC:

| Distribucion | Parametros | Restriccion |
|:---|:---|:---|
| Normal | media, desv.std | Ninguna |
| LogNormal | meanlog, sdlog | Datos > 0 |
| Gamma | shape, rate | Datos > 0 |
| Weibull | shape, scale | Datos > 0 |
| Exponencial | rate | Datos > 0 |
| Uniforme | min, max | Ninguna |
| Beta | alpha, beta | Datos en [0,1] |

## 12.6 Explorador Reactivo

El viewer interactivo permite:
- Cambiar distribucion, parametros, modelo e iteraciones con sliders
- Ver el histograma actualizarse en tiempo real (<100ms)
- Guardar escenarios para comparacion
- Superponer dos escenarios en el mismo grafico
- Copiar parametros de escenarios guardados a Excel

**Nota:** La simulacion reactiva usa JavaScript puro (Box-Muller) para respuesta instantanea. La simulacion "real" via `=SIM.QuickRun` usa R (fitting) + Julia (MC) para resultados de produccion.

## 12.7 Arquitectura Tecnica

```
Excel → SIM.QuickRun → FitService (R/fitdistrplus)
                      → MonteCarloService (Julia/Distributions.jl)
                      → HTML report → NEVEN.v() viewer
```

- **SimBridge**: relay via xlUDF a NEVEN base (lazy detection)
- **FitService**: genera codigo R con `fitdistrplus::fitdist()`
- **MonteCarloService**: genera codigo Julia con `Distributions.jl`
- **SensitivityService**: Spearman rank correlation
- **SimViewerManager**: genera HTML + abre viewer

## 12.8 Limitaciones (Phase 1)

- Una sola variable por simulacion (multi-variable en Phase 2)
- `SIM.Datos(N)` limitado a ~3000 registros por tamano del pipe
- Para datos completos usar `SIM.Exportar()` (CSV a disco)
- Explorador reactivo no conectado bidireccional con Excel
- Copulas y series de tiempo en Phase 2

## 12.9 Troubleshooting

| Problema | Solucion |
|:---|:---|
| `SIM.Status()` dice "Base: NO DISPONIBLE" | Verificar que NEVEN64.xll esta cargado |
| `SIM.Fit()` dice "BLOCKED: library()" | Usar `requireNamespace` (ya corregido en v1.0) |
| `SIM.QuickRun()` dice "Julia call failed" | Verificar `=NEVEN.j("1+1")` retorna 2 |
| Excel se cierra al cargar | Verificar que no hay xlUDF en xlAutoOpen |
| `SIM.Exportar()` dice "BLOCKED: open()" | Crear `C:\NEVEN\data\` manualmente |
</section>
