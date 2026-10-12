# Requerimiento de Trabajo: Excel como Frontend de Análisis Estadístico Avanzado con Pluto.jl como Orquestador

**ID:** REQ-002  
**Fecha:** 2026-04-19  
**Versión:** 4.0 (rediseño completo)  
**Estado:** Pendiente de asignación  
**Prioridad:** Alta  
**Relacionado con:** REQ-001 (Integración Tidyverse en Excel)

> **v4.0 — Rediseño arquitectónico desde cero.** Excel actúa exclusivamente como frontend de usuario. Pluto.jl es el único orquestador de cómputo, recibiendo instrucciones desde Excel y distribuyendo tareas entre Julia nativo y R via RCall.jl. Se elimina el backend plumber como componente independiente. Versiones anteriores quedan obsoletas.

---

## 1. Resumen Ejecutivo

Desarrollar un sistema de análisis estadístico avanzado y cómputo científico integrado en Microsoft Excel, bajo la siguiente arquitectura de responsabilidades:

- **Excel** actúa como **frontend exclusivo para el usuario no experto**: entrada de parámetros, selección de rangos, activación de análisis mediante botones, y visualización de resultados en celdas y gráficos. El usuario de negocio nunca sale de Excel ni necesita conocer los lenguajes subyacentes.

- **Pluto.jl** actúa como **orquestador central de cómputo**: recibe los parámetros y datos desde Excel, decide qué lenguaje ejecuta cada tarea, coordina Julia nativo y R (via `RCall.jl`) según las capacidades de cada ecosistema, y devuelve resultados a Excel.

- **Julia y R** actúan como **motores de cómputo especializados** invocados por Pluto: Julia para optimización, simulación y álgebra lineal de alto rendimiento; R para estadística aplicada, econometría, análisis de supervivencia y modelos bayesianos.

Este modelo elimina múltiples backends paralelos, reduce la superficie de integración a un único canal Excel <--> Pluto, y oculta completamente la complejidad técnica detrás de una interfaz Excel familiar.

---

## 2. Principios de Diseño

| Principio | Descripción |
|---|---|
| **Excel como UI, no como orquestador** | Excel solo envía parámetros y recibe resultados. Nunca decide qué lenguaje ejecuta qué tarea. |
| **Pluto como único punto de entrada** | Un solo servidor local. Excel habla exclusivamente con Pluto via HTTP. |
| **R como librería, no como servidor** | R se invoca desde Julia via RCall.jl. No hay servidor plumber independiente en este módulo. |
| **Transparencia para el usuario** | El usuario de negocio no sabe ni necesita saber si su análisis corre en Julia o R. |
| **Modo avanzado opcional** | Usuarios técnicos pueden abrir el notebook Pluto en WebView2 para ver y modificar la lógica. |
| **Reproducibilidad** | Cada análisis queda registrado en un notebook .jl versionable en Git. |

---

## 3. Arquitectura del Sistema

### 3.1 Diagrama general

```
┌──────────────────────────────────────────────────────────────┐
│                      Microsoft Excel                         │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐   │
│   │              Office Add-in Task Pane                 │   │
│   │                                                      │   │
│   │  [Selector de análisis]  [Parámetros]  [Ejecutar]   │   │
│   │                                                      │   │
│   │  [Rango de entrada: A1:D100]  [Rango salida: F1]    │   │
│   │                                                      │   │
│   │  [Estado: ● Julia  ● R]    [Log de ejecución]       │   │
│   │                                                      │   │
│   │  [Modo avanzado: Abrir notebook Pluto ↗]            │   │
│   └──────────────────────────┬───────────────────────────┘   │
│                              │ Office.js API                  │
│   ┌──────────────────────────▼───────────────────────────┐   │
│   │              Excel Data Bridge                       │   │
│   │   rangos --> JSON  -->  POST /api/excel/task             │   │
│   │   resultados JSON  -->  escritura en celdas/imágenes   │   │
│   └──────────────────────────┬───────────────────────────┘   │
└──────────────────────────────┼───────────────────────────────┘
                               │
                    HTTP + WebSocket
                    (único canal)
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                     Pluto.jl Server                          │
│                     localhost:1234  —  Julia 1.10+            │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐    │
│   │           Router de tareas (Julia)                  │    │
│   │  recibe { tarea, parámetros, datos }                │    │
│   │  decide: Julia nativo | R via RCall | combinado     │    │
│   │  devuelve { resultados, imágenes, log }             │    │
│   └───────────┬─────────────────────────┬───────────────┘    │
│               │                         │                    │
│   ┌───────────▼──────────┐  ┌───────────▼──────────────┐     │
│   │   Julia Nativo       │  │   R via RCall.jl          │     │
│   │                      │  │                           │     │
│   │   JuMP.jl            │  │   stats, lme4, survival   │     │
│   │   DifferentialEq.jl  │  │   forecast, psych, car    │     │
│   │   Turing.jl          │  │   Hmisc, rstanarm, plm    │     │
│   │   Distributions.jl   │  │   r2d3, ggplot2           │     │
│   │   Plots.jl           │  │                           │     │
│   │   LinearAlgebra      │  │   (R 4.4.1 embebido)      │     │
│   └──────────────────────┘  └───────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Flujo de una solicitud de análisis

```
1. Usuario configura análisis en Task Pane
   (selecciona tipo, rango de datos, parámetros)

2. Excel Data Bridge lee rango via Office.js
   serializa --> { tarea, parámetros, datos } JSON

3. HTTP POST --> Pluto.jl (localhost:1234)

4. Router de tareas decide motor:
   ├── Julia nativo   --> JuMP, DiffEq, Turing...
   ├── R via RCall    --> lme4, plm, rstanarm...
   └── Combinado      --> optimización Julia + viz R

5. Pluto ejecuta, recalcula reactivamente

6. Respuesta HTTP --> { tabla, imagen, log } --> Excel

7. Excel Data Bridge escribe en celdas e inserta imágenes
```

### 3.3 Modo avanzado (usuario técnico)

El usuario técnico activa una vista WebView2 en el Task Pane que abre el notebook Pluto activo, permitiendo ver y modificar el código de orquestación, añadir lógica personalizada mezclando Julia y R, y guardar notebooks personalizados como plantillas. Este modo es completamente opcional y no visible para el usuario de negocio.

---

## 4. Alcance

### 4.1 Dentro del alcance

**Capa Excel (frontend):**
- Task Pane con selector de análisis, formularios de parámetros y botones de ejecución.
- Indicador de estado: Julia y R embebido (activo / iniciando / error).
- Log de ejecución en tiempo real etiquetado por lenguaje.
- Escritura de resultados tabulares en rangos de celdas.
- Inserción de gráficos como imágenes en la hoja activa.
- Modo avanzado: WebView2 con notebook Pluto para usuarios técnicos.

**Capa Pluto (orquestador):**
- Router de tareas configurable que asigna cada análisis al motor correcto.
- Acceso a Julia nativo y a R via RCall.jl desde un único proceso.
- API HTTP interna que Excel consume.
- Biblioteca de notebooks precargados para todos los análisis disponibles.
- Gestión de sesión y modelos estimados en memoria.

**Análisis disponibles via R embebido (RCall.jl):**
`stats`, `lme4`, `survival`, `forecast`, `psych`, `car`, `Hmisc`, `rstanarm`, `plm`, `r2d3`

**Análisis disponibles via Julia nativo:**
`JuMP.jl`, `DifferentialEquations.jl`, `Turing.jl`, `LinearAlgebra`, `Distributions.jl`, `Plots.jl`

### 4.2 Fuera del alcance (v1)

- Integración con Python (considerada para v2 via PyCall.jl).
- Ejecución distribuida o en clúster.
- Colaboración multiusuario.
- Versiones de Excel anteriores a 2019.
- Deep learning (PyTorch, TensorFlow).
- Gestión de paquetes R o Julia por el usuario final.

---

## 5. Requerimientos Funcionales

### RF-01: Task Pane — Interfaz de Usuario Excel

Interfaz estructurada en tres zonas:

**Zona 1 — Selector de análisis:**
Árbol de categorías con los análisis disponibles, agrupados por:
- Estadística clásica (R) — Modelos lineales avanzados (R) — Series de tiempo (R)
- Econometría de panel (R) — Estadística bayesiana (R / Julia)
- Optimización (Julia) — Simulación y EDOs (Julia) — Álgebra lineal (Julia)
- Visualización avanzada (R / Julia)

**Zona 2 — Configuración:**
- Formulario dinámico según análisis seleccionado.
- Selector de rango de entrada y rango de salida.
- Parámetros específicos (variables, modelos, horizontes, iteraciones).

**Zona 3 — Estado y log:**
- Indicadores: Julia (●/◌/✕) y R embebido (●/◌/✕).
- Log en tiempo real con etiquetas `[Julia]` / `[R]` / `[Pluto]`.
- Botón para abrir notebook Pluto en modo avanzado (WebView2).

---

### RF-02: API de Tareas — Protocolo Excel <--> Pluto

Contrato HTTP único entre Excel y Pluto:

**Request:**
```json
POST localhost:1234/api/excel/task
{
  "task":         "lme4_mixed_model",
  "params":       { "formula": "y ~ x + (1|group)", "family": "gaussian" },
  "data":         { "columns": ["y","x","group"], "rows": [[...]] },
  "output_range": "F1"
}
```

**Response:**
```json
{
  "status":       "ok",
  "result_type":  "dataframe",
  "data":         { "columns": [...], "rows": [[...]] },
  "image_base64": null,
  "log":          "[R] Mixed model converged. AIC: 234.5"
}
```

**Tipos de resultado soportados:**

| result_type | Descripción                        | Destino Excel          |
|-------------|------------------------------------|------------------------|
| `dataframe` | Tabla con encabezados              | Rango de celdas        |
| `scalar`    | Valor único numérico o string      | Celda individual       |
| `vector`    | Array de valores                   | Columna o fila         |
| `image`     | Gráfico PNG en base64              | Imagen incrustada      |
| `multi`     | Tabla + imagen combinadas          | Rango + imagen         |

---

### RF-03: Router de Tareas en Pluto

Módulo Julia que recibe la solicitud de Excel y despacha al motor correcto:

| Categoría de análisis               | Motor        | Justificación                               |
|-------------------------------------|--------------|---------------------------------------------|
| Regresión, ANOVA, correlación       | R (RCall)    | `stats` R — estándar de facto               |
| Efectos mixtos                      | R (RCall)    | `lme4` — más maduro que GLM.jl              |
| Supervivencia                       | R (RCall)    | `survival` — sin equivalente maduro en Julia|
| Series de tiempo ARIMA/ETS          | R (RCall)    | `forecast` — superior a alternativas Julia  |
| Psicometría / factorial             | R (RCall)    | `psych` — sin equivalente en Julia          |
| Diagnóstico de regresión            | R (RCall)    | `car` — sin equivalente directo             |
| Descriptiva avanzada / imputación   | R (RCall)    | `Hmisc` — sin equivalente en Julia          |
| Bayesiano (interfaz formulario)     | R (RCall)    | `rstanarm` — interfaz simplificada          |
| Econometría de panel                | R (RCall)    | `plm` — sin equivalente maduro en Julia     |
| Visualización D3                    | R (RCall)    | `r2d3` — integración nativa                 |
| Optimización matemática             | Julia nativo | `JuMP.jl` — supera a toda alternativa       |
| EDOs / simulación dinámica          | Julia nativo | `DifferentialEquations.jl` — sin competencia|
| Bayesiano avanzado / MCMC           | Julia nativo | `Turing.jl` — velocidad superior            |
| Álgebra lineal gran escala          | Julia nativo | Rendimiento nativo C/Fortran                |
| Monte Carlo intensivo               | Julia nativo | Velocidad de bucles sin overhead            |

El router es configurable via `task_router.toml` sin recompilar el sistema.

---

### RF-04: Catálogo de Análisis Disponibles

#### RF-04.1: Análisis via R (RCall.jl)

**Estadística base (`stats`):**

| Análisis              | Parámetros desde Excel                           | Salida a Excel                            |
|-----------------------|--------------------------------------------------|-------------------------------------------|
| Regresión lineal      | Dependiente, independientes                      | Coeficientes, p-valores, R², IC           |
| Regresión logística   | Dependiente, independientes, familia             | Coeficientes, OR, p-valores               |
| T-test                | Variable, tipo (1 muestra / 2 muestras / pareado)| Estadístico t, p-valor, IC               |
| ANOVA (1 y 2 vías)    | Dependiente, factores                            | Tabla ANOVA, F, p-valor                   |
| Chi-cuadrado          | Dos variables categóricas                        | Estadístico, p-valor, tabla contingencia  |
| Correlación           | Variables, método                                | Matriz correlaciones + p-valores          |

**Modelos de efectos mixtos (`lme4`):**

| Análisis    | Parámetros desde Excel                                     | Salida a Excel                          |
|-------------|------------------------------------------------------------|-----------------------------------------|
| `lmer()`    | Dependiente, efectos fijos, variable de agrupación         | Efectos fijos, varianzas aleatorias, AIC|
| `glmer()`   | Dependiente, efectos fijos, agrupación, familia            | Coeficientes, varianzas, AIC/BIC        |

**Análisis de supervivencia (`survival`):**

| Análisis          | Parámetros desde Excel                           | Salida a Excel                            |
|-------------------|--------------------------------------------------|-------------------------------------------|
| Kaplan-Meier      | Tiempo, censura, grupo                           | Tabla de supervivencia + curva imagen     |
| Log-rank test     | Tiempo, censura, grupo                           | Estadístico, p-valor                      |
| Cox PH            | Tiempo, censura, covariables                     | HR, IC, p-valores, test proporcionalidad  |

**Series de tiempo (`forecast`):**

| Análisis        | Parámetros desde Excel               | Salida a Excel                          |
|-----------------|--------------------------------------|-----------------------------------------|
| `auto.arima()`  | Serie, frecuencia                    | Modelo, coeficientes                    |
| `ets()`         | Serie, frecuencia                    | Parámetros de suavizado                 |
| `forecast()`    | Serie, frecuencia, horizonte         | Tabla de pronóstico + gráfico           |
| `decompose()`   | Serie, frecuencia                    | Tendencia, estacionalidad, residuo      |

**Psicometría (`psych`):**

| Análisis          | Parámetros desde Excel                  | Salida a Excel                          |
|-------------------|-----------------------------------------|-----------------------------------------|
| `describe()`      | Rango de variables                      | Descriptiva: media, SD, skew, kurtosis  |
| `alpha()`         | Rango de ítems de escala                | Alfa de Cronbach, ítems problemáticos   |
| `fa()`            | Variables, nº de factores               | Cargas factoriales, varianza explicada  |
| PCA `principal()` | Variables, nº componentes               | Componentes, cargas, varianza           |
| `corr.test()`     | Rango de variables                      | Matriz de correlaciones + p-valores     |

**Diagnóstico de regresión (`car`):**

| Análisis          | Parámetros desde Excel             | Salida a Excel                        |
|-------------------|------------------------------------|---------------------------------------|
| `vif()`           | Referencia a modelo guardado       | VIF por variable                      |
| `ncvTest()`       | Referencia a modelo                | Estadístico Breusch-Pagan, p-valor    |
| `outlierTest()`   | Referencia a modelo                | Observaciones influyentes             |
| `Anova()` II/III  | Referencia a modelo, tipo          | Tabla ANOVA tipo II o III             |

**Estadística descriptiva e imputación (`Hmisc`):**

| Análisis      | Parámetros desde Excel              | Salida a Excel                          |
|---------------|-------------------------------------|-----------------------------------------|
| `describe()`  | Rango de variables                  | Estadísticos detallados por variable    |
| `impute()`    | Rango, método (media/mediana/moda)  | Dataset imputado en rango de salida     |
| `rcorr()`     | Rango de variables                  | Correlaciones + n + p-valores           |
| `cut2()`      | Variable continua, nº cuantiles     | Variable discretizada en rango salida   |

**Modelos bayesianos (`rstanarm`):**

| Análisis              | Parámetros desde Excel                              | Salida a Excel                          |
|-----------------------|-----------------------------------------------------|-----------------------------------------|
| `stan_lm()`           | Dependiente, independientes, iteraciones, cadenas   | Coeficientes, IC creíbles, R²           |
| `stan_glm()`          | Dependiente, independientes, familia, prior         | Coeficientes, IC creíbles               |
| `posterior_interval()`| Referencia a modelo, nivel de credibilidad          | Intervalos creíbles por parámetro       |
| `pp_check()`          | Referencia a modelo bayesiano                       | Gráfico verificación predictiva         |

> ⚠️ Los modelos bayesianos muestran barra de progreso y permiten cancelación.

**Econometría de panel (`plm`):**

| Análisis       | Parámetros desde Excel                                         | Salida a Excel                                       |
|----------------|----------------------------------------------------------------|------------------------------------------------------|
| `plm()` FE     | Dependiente, independientes, índice entidad, índice tiempo     | Coeficientes, SE, R² within/between/overall          |
| `plm()` RE     | Idem + efectos aleatorios                                      | Idem                                                 |
| `phtest()`     | Referencias a modelos FE y RE                                  | Estadístico Hausman, p-valor, recomendación          |
| `plmtest()`    | Referencia a modelo RE                                         | Estadístico BP, p-valor                              |
| `purtest()`    | Rango de panel, test (LLC/IPS/ADF)                             | Estadístico y p-valor por test                       |

**Visualización D3 (`r2d3`):**

| Plantilla              | Parámetros desde Excel               | Salida                              |
|------------------------|--------------------------------------|-------------------------------------|
| Barras apiladas        | Rango datos, columna grupo           | HTML interactivo en WebView2/imagen |
| Heatmap correlación    | Rango de variables                   | HTML interactivo / imagen           |
| Gráfico de red         | Tabla nodos + tabla enlaces          | HTML interactivo / imagen           |
| Treemap                | Rango con jerarquía y valores        | HTML interactivo / imagen           |
| Líneas con zoom        | Serie temporal, columna fecha        | HTML interactivo / imagen           |

---

#### RF-04.2: Análisis via Julia nativo

**Optimización (`JuMP.jl`):**

| Análisis                      | Parámetros desde Excel                             | Salida a Excel                       |
|-------------------------------|----------------------------------------------------|--------------------------------------|
| Programación lineal (LP)      | Coeficientes objetivo, restricciones               | Variables óptimas, valor objetivo    |
| Programación entera mixta     | Idem + variables enteras/binarias                  | Idem                                 |
| Programación cuadrática       | Matriz Q, vector c, restricciones                  | Variables óptimas, valor objetivo    |
| Programación no lineal        | Función objetivo (notebook), restricciones         | Variables óptimas, valor objetivo    |

**Simulación dinámica (`DifferentialEquations.jl`):**

| Análisis              | Parámetros desde Excel                              | Salida a Excel                       |
|-----------------------|-----------------------------------------------------|--------------------------------------|
| Sistema ODE           | Condiciones iniciales, rango de parámetros          | Trayectoria temporal en rango Excel  |
| Modelo SIR/epidémico  | β, γ, N, condiciones iniciales, horizonte temporal  | Trayectorias S, I, R                 |
| ODE paramétrica       | Rango de parámetros a barrer                        | Tabla de soluciones por parámetro    |

**Estadística bayesiana avanzada (`Turing.jl`):**

| Análisis               | Parámetros desde Excel                       | Salida a Excel                           |
|------------------------|----------------------------------------------|------------------------------------------|
| Regresión bayesiana    | Dependiente, independientes, prior, iter     | Posterior: media, SD, IC 95%             |
| Modelo jerárquico      | Datos, estructura de agrupación (notebook)   | Parámetros por nivel de jerarquía        |
| Comparación de modelos | Referencias a dos modelos Turing             | WAIC, LOO-CV                             |

**Álgebra lineal (`LinearAlgebra`):**

| Análisis                | Parámetros desde Excel       | Salida a Excel                       |
|-------------------------|------------------------------|--------------------------------------|
| Descomposición SVD      | Rango matricial              | Matrices U, Σ, V en rangos Excel     |
| Factorización QR        | Rango matricial              | Matrices Q, R                        |
| Eigenvalores/vectores   | Rango matricial              | Tabla de valores y vectores propios  |
| Sistema lineal Ax = b   | Matriz A, vector b           | Vector solución x                    |
| Norma y número condición| Rango matricial              | Norma, número de condición           |

**Simulación Monte Carlo (`Distributions.jl`):**

| Análisis                  | Parámetros desde Excel                          | Salida a Excel                       |
|---------------------------|-------------------------------------------------|--------------------------------------|
| Simulación distribución   | Distribución, parámetros, nº simulaciones       | Tabla resultados + histograma        |
| Valor en Riesgo (VaR)     | Retornos (rango Excel), nivel de confianza      | VaR, CVaR                            |
| Simulación de escenarios  | Variables, distribuciones, correlaciones        | Tabla de escenarios simulados        |

---

### RF-05: Gestión de Sesión y Modelos

- Pluto mantiene una sesión persistente durante la sesión de Excel.
- Los modelos estimados (R o Julia) se guardan en memoria con nombre asignado por el usuario.
- El Task Pane muestra la lista de modelos activos (nombre, tipo, lenguaje, timestamp).
- Los modelos son referenciables en análisis subsecuentes (ej. `car::vif()` sobre `lm` ya estimado).
- El usuario puede exportar un modelo a un notebook `.jl` para uso posterior.

---

### RF-06: Gestión del Servidor Pluto

- El servidor Pluto.jl inicia automáticamente al activar el Add-in en un proceso background.
- Julia embebe R via `RCall.jl` como proceso gestionado internamente.
- El panel muestra el estado de Julia y R embebido en tiempo real.
- El servidor se detiene limpiamente al cerrar Excel.
- Puerto configurable (default: 1234).
- Detección de servidor activo para evitar inicios duplicados.

---

### RF-07: Modo Avanzado — Notebook Pluto en WebView2

Para usuarios técnicos (científicos de datos, investigadores, analistas cuantitativos):

- Botón **"Abrir en Pluto"** en el Task Pane que expande la vista WebView2 con el notebook activo.
- El notebook muestra el código Julia/R que ejecuta el análisis seleccionado.
- El usuario técnico puede modificar parámetros y lógica directamente en Pluto.
- Los cambios se reflejan en el siguiente análisis ejecutado desde Excel.
- El usuario puede guardar el notebook modificado como plantilla personalizada.
- Vista opcional que no interfiere con el modo básico de formularios.

---

### RF-08: Biblioteca de Notebooks Precargados

| Notebook                         | Motor        | Descripción                                                           |
|----------------------------------|--------------|-----------------------------------------------------------------------|
| `stats_regression.jl`            | R (RCall)    | Regresión lineal/logística con diagnósticos completos                 |
| `lme4_mixed_models.jl`           | R (RCall)    | Efectos mixtos con selección de estructura aleatoria                  |
| `survival_analysis.jl`           | R (RCall)    | Kaplan-Meier, log-rank y Cox con gráficos                             |
| `forecast_arima.jl`              | R (RCall)    | ARIMA automático con pronóstico y bandas de confianza                 |
| `psych_factor_analysis.jl`       | R (RCall)    | PCA y análisis factorial con gráfico de cargas                        |
| `plm_panel_econometrics.jl`      | R (RCall)    | Panel FE/RE con Hausman, Breusch-Pagan y raíz unitaria                |
| `rstanarm_bayes.jl`              | R (RCall)    | Regresión bayesiana con verificación predictiva posterior             |
| `jump_optimization.jl`           | Julia nativo | Optimización LP/MIP/NLP con parámetros configurables desde Excel      |
| `diffeq_simulation.jl`           | Julia nativo | Simulación dinámica con condiciones iniciales desde Excel             |
| `turing_hierarchical.jl`         | Julia nativo | Modelos jerárquicos bayesianos con MCMC                               |
| `montecarlo_risk.jl`             | Julia nativo | Simulación Monte Carlo para análisis de riesgo financiero             |
| `linalg_decomposition.jl`        | Julia nativo | Descomposiciones matriciales sobre rangos de Excel                    |
| `multilang_pipeline.jl`          | R + Julia    | Pipeline: estadística R --> optimización Julia --> resultados a Excel     |

---

### RF-09: Log de Ejecución y Manejo de Errores

- Log en tiempo real con mensajes etiquetados: `[Julia]`, `[R]`, `[Pluto]`.
- Errores de R via `RCall.jl` formateados con stack trace legible.
- Errores de Julia con número de línea del notebook.
- Sugerencias de corrección en lenguaje natural para errores comunes.
- Log exportable como `.txt` para soporte técnico.

---

### RF-10: Sincronización Bidireccional en Tiempo Real (modo avanzado)

- Modo opcional: cambios en celdas de Excel disparan recálculo automático en Pluto.
- Debounce mínimo de 500ms.
- Log indica qué lenguaje está ejecutando en cada momento.
- El usuario puede pausar/reanudar desde el panel.
- Disponible únicamente cuando el modo WebView2 está activo.

---

## 6. Requerimientos No Funcionales

| ID     | Categoría       | Descripción                                                                                       |
|--------|-----------------|---------------------------------------------------------------------------------------------------|
| RNF-01 | Rendimiento     | Análisis R simples (regresión, ANOVA) en < 3 segundos para datasets < 100K filas                 |
| RNF-02 | Rendimiento     | Análisis Julia (JuMP LP, Monte Carlo 10K iter) en < 5 segundos                                   |
| RNF-03 | Rendimiento     | Modelos bayesianos con barra de progreso; tiempo máximo tolerable: 10 min                        |
| RNF-04 | Rendimiento     | Cold start completo (Julia + R embebido) con sysimage en < 60 segundos                           |
| RNF-05 | Rendimiento     | Intercambio Julia <--> R en memoria via RCall; sin archivos intermedios                             |
| RNF-06 | Compatibilidad  | Excel 2019, 2021 y Microsoft 365 (Windows y Mac)                                                 |
| RNF-07 | Compatibilidad  | WebView2 Runtime verificado e instalado por el instalador si está ausente                        |
| RNF-08 | Seguridad       | Ejecución 100% local; sin transmisión de datos a servidores externos                            |
| RNF-09 | Seguridad       | Pluto.jl escucha únicamente en `localhost`                                                       |
| RNF-10 | Instalación     | Instalador único: R 4.4.1 + Julia 1.10+ + todas las dependencias + WebView2 + Add-in            |
| RNF-11 | Usabilidad      | Usuario sin experiencia técnica ejecuta un análisis completo en < 5 minutos desde cero          |
| RNF-12 | Usabilidad      | Todos los errores incluyen sugerencia de corrección en lenguaje natural                          |
| RNF-13 | Mantenibilidad  | Router de tareas configurable via `task_router.toml` sin recompilar                             |
| RNF-14 | Mantenibilidad  | Cada notebook de análisis es independiente y reemplazable sin afectar los demás                 |
| RNF-15 | Reproducibilidad| Todo análisis genera un notebook `.jl` reproducible y ejecutable de forma standalone            |

---

## 7. Criterios de Aceptación

**Infraestructura:**
- [ ] El instalador despliega R, Julia y el Add-in sin intervención manual del usuario.
- [ ] El servidor Pluto inicia con R embebido en < 60 segundos al abrir el Add-in.
- [ ] El panel muestra correctamente el estado de Julia y R en tiempo real.

**Módulos R via RCall:**
- [ ] Una regresión lineal desde formulario devuelve coeficientes y p-valores a Excel.
- [ ] Un modelo `plm` FE con prueba de Hausman escribe resultados correctos en Excel.
- [ ] Una curva de Kaplan-Meier se inserta como imagen en la hoja activa.
- [ ] Un pronóstico ARIMA escribe valores pronosticados e imagen en Excel.
- [ ] Un modelo `rstanarm` muestra progreso y escribe intervalos creíbles en Excel.
- [ ] Una visualización D3 (heatmap) se renderiza en el Task Pane.

**Módulos Julia nativos:**
- [ ] Una optimización LP con JuMP devuelve la solución óptima a Excel.
- [ ] Una simulación ODE (SIR) con condiciones desde Excel escribe trayectorias en Excel.
- [ ] Una simulación Monte Carlo de 100K iteraciones completa en < 5 segundos.
- [ ] Una SVD sobre un rango matricial escribe U, Σ, V en Excel.

**Orquestación:**
- [ ] El router asigna correctamente tareas R a RCall y tareas Julia a Julia nativo.
- [ ] El pipeline `multilang_pipeline.jl` completa y devuelve resultados R + Julia a Excel.
- [ ] El modo WebView2 abre el notebook activo y permite modificar parámetros.
- [ ] Los modelos en sesión son referenciables desde análisis subsecuentes.
- [ ] El log etiqueta mensajes por lenguaje y sugiere correcciones para errores comunes.

---

## 8. Dependencias

- **REQ-001:** Task Pane base y Excel Data Bridge deben estar operativos.
- **R 4.4.1** con paquetes: `stats`, `lme4`, `survival`, `forecast`, `psych`, `car`, `Hmisc`, `rstanarm`, `plm`, `r2d3` y dependencias transitivas.
- **Stan / rstan:** Dependencia de `rstanarm`; incluir binarios precompilados en el instalador.
- **Julia 1.10+** con paquetes: `Pluto`, `RCall`, `JuMP`, `DifferentialEquations`, `Turing`, `Distributions`, `Plots`, `LinearAlgebra`, `HTTP`, `JSON3` y dependencias.
- **WebView2 Runtime:** El instalador verifica su presencia e instala si está ausente.
- **PackageCompiler.jl:** Para sysimage precompilado que reduzca el cold start.
- **Microsoft 365 Developer Account** para pruebas y publicación.

---

## 9. Riesgos

| Riesgo                                                       | Probabilidad | Impacto | Mitigación                                                               |
|--------------------------------------------------------------|--------------|---------|--------------------------------------------------------------------------|
| Cold start Julia + R embebido > 60s en hardware corporativo  | Alta         | Alto    | Sysimage con PackageCompiler.jl; proceso precalentado en background      |
| RCall.jl inestable al cargar paquetes R pesados (rstanarm)   | Media        | Alto    | Cargar R en background al inicio; aislar rstanarm en proceso separado    |
| Compilación Stan falla sin compilador C++ en entorno destino | Alta         | Alto    | Distribuir binarios Stan precompilados en el instalador                  |
| API HTTP Pluto inestable entre versiones menores             | Media        | Alto    | Fijar versión Pluto.jl; envolver con capa de abstracción propia          |
| Conflictos WebSocket Pluto / WebView2 en modo avanzado       | Media        | Medio   | Pruebas tempranas de compatibilidad; fallback a modo polling             |
| Condiciones de carrera en sincronización RT (RF-10)          | Media        | Alto    | Cola de eventos con mutex; RT deshabilitado por defecto                  |
| Tamaño excesivo del instalador (R + Julia + Stan)            | Alta         | Medio   | Descarga lazy de componentes opcionales (rstanarm, Turing)               |
| Conversión de tipos RCall con NA / missing values            | Media        | Medio   | Capa de sanitización de datos antes de cruzar el bridge RCall            |
| Interferencia proceso R compartido con REQ-001 (plumber)     | Media        | Medio   | REQ-001 y REQ-002 coordinan el proceso R compartido via lock de proceso  |

---

## 10. Entregables

1. **Documento de diseño técnico** — arquitectura Excel <--> Pluto <--> Julia/R con diagramas detallados.
2. **Especificación OpenAPI** de la API HTTP interna de Pluto (todos los endpoints de tareas).
3. **Router de tareas** — `task_router.toml` + módulo Julia de despacho.
4. **Biblioteca de 13 notebooks Pluto** con todos los análisis del catálogo RF-08.
5. **Task Pane React** con formularios para todos los análisis de RF-04.
6. **Excel Data Bridge actualizado** con soporte para el protocolo de tareas Pluto.
7. **Instalador unificado** — R + Stan precompilado + Julia + sysimage + Add-in + WebView2.
8. **Suite de pruebas** con datasets de referencia para cada análisis (R y Julia).
9. **Manual de usuario** con guía paso a paso por tipo de análisis.
10. **Documentación técnica** del protocolo Excel <--> Pluto y del sistema de notebooks.

---

## 11. Estimación de Esfuerzo (preliminar)

| Componente                                              | Estimado     |
|---------------------------------------------------------|--------------|
| Diseño técnico completo (arquitectura + API OpenAPI)    | 3 semanas    |
| Servidor Pluto — API HTTP + router de tareas            | 3 semanas    |
| Notebooks R via RCall (7 notebooks — grupo R)           | 4 semanas    |
| Notebooks Julia nativos (6 notebooks — grupo Julia)     | 4 semanas    |
| Task Pane React — formularios todos los análisis        | 5 semanas    |
| Excel Data Bridge — protocolo de tareas con Pluto       | 2 semanas    |
| Gestión de sesión y modelos                             | 1 semana     |
| Modo avanzado WebView2 + sincronización RT              | 2 semanas    |
| Sysimage Julia + RCall embebido + PackageCompiler       | 2 semanas    |
| Instalador unificado (R + Stan + Julia + WebView2)      | 3 semanas    |
| Suite de pruebas + QA                                   | 3 semanas    |
| Documentación técnica + manual de usuario               | 2 semanas    |
| **Total (equipos en paralelo — recomendado)**           | **~20 semanas** |
| **Total (equipo único secuencial)**                     | **~34 semanas** |

> **Nota de paralelismo:** Con dos equipos en paralelo (equipo frontend/bridge + equipo notebooks/backend Pluto), el tiempo real se reduce a ~20 semanas. El cuello de botella es el instalador unificado con Stan precompilado, que requiere validación en múltiples entornos OS y configuraciones corporativas.

---

## 12. Referencias

- [Office Add-ins Documentation — Microsoft](https://learn.microsoft.com/en-us/office/dev/add-ins/)
- [Pluto.jl — plutojl.org](https://plutojl.org/)
- [RCall.jl — github.com/JuliaInterop/RCall.jl](https://github.com/JuliaInterop/RCall.jl)
- [JuMP.jl — jump.dev](https://jump.dev/)
- [DifferentialEquations.jl — docs.sciml.ai](https://docs.sciml.ai/DiffEqDocs/)
- [Turing.jl — turing.ml](https://turing.ml/)
- [PackageCompiler.jl](https://julialang.github.io/PackageCompiler.jl/)
- [lme4 — CRAN](https://cran.r-project.org/web/packages/lme4/)
- [survival — CRAN](https://cran.r-project.org/web/packages/survival/)
- [forecast — Rob Hyndman](https://pkg.robjhyndman.com/forecast/)
- [plm — CRAN](https://cran.r-project.org/web/packages/plm/)
- [rstanarm — mc-stan.org](https://mc-stan.org/rstanarm/)
- [r2d3 — rstudio.github.io](https://rstudio.github.io/r2d3/)
- [Microsoft WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/)
- [REQ-001 — Integración Tidyverse en Excel](./requerimiento_tidyverse_excel.md)

---

*Documento generado el 19 de abril de 2026. Versión 4.0 — Rediseño completo.*  
*Excel como frontend · Pluto.jl como orquestador central · Julia y R como motores especializados.*
