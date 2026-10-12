# NEVEN-SIM: Especificación Técnica y Requerimientos de Arquitectura
**Módulo de Simulación Estocástica, Series Temporales y Análisis de Riesgo para NEVEN**

---

## 1. Introducción y Propósito
**NEVEN-SIM** es el módulo especializado de simulación, análisis de riesgo bajo incertidumbre y proyección predictiva diseñado para integrarse de manera transparente en la infraestructura de **NEVEN**. Su propósito es democratizar el acceso al análisis estocástico de alto rendimiento directamente dentro de Microsoft Excel, superando las limitaciones tradicionales de velocidad, usabilidad y audibilidad que presentan herramientas propietarias heredadas como Oracle Crystal Ball.

A través del **WebViewer** incorporado en NEVEN, este módulo proporciona un sandbox de modelado interactivo y reactivo de nivel científico, apilando tres tecnologías líderes para optimizar cada etapa del flujo de trabajo:

┌──────────────────────────────────────────────┐
│                 EXCEL + NEVEN                │
└──────┬────────────────────────────────┬──────┘
       │ (Llamadas / Datos)             ▲ (Resultados / Reportes)
       ▼                                │
┌──────────────────────────────────────────────────────────────┐
│                        WEBVIEWER (UI)                        │
│     Espacio de trabajo reactivo, Selección de rangos,        │
│         Ajuste de parámetros mediante Sliders, Plots         │
└─┬────────────────────────────────▲───────────────────────────┘
  │ JSON / Protobuf                │ Protobuf (Payloads de Simulación)
  ▼                                │
┌──────────────────────────────────────────────────────────────┐
│                 PYTHON (Orquestador / Pegamento)             │
│     Coordina el flujo de datos, API interna, Serialización   │
└──────┬────────────────────────────────────────────────▲──────┘
       │                                                │
       │ (Series Históricas)                            │ (Coeficientes ARIMA / Cópulas)
       ▼                                                │
┌──────────────────────────────┐                ┌───────┴──────────────────────┐
│        R (Estadística)       │                │    JULIA (Motor Numérico)    │
│  Ajuste de distribuciones,   │                │   Simulación de Montecarlo,  │
│  Auto-ARIMA, Redes Neuronales│                │ Cópulas nativas, JIT masivo  │
└──────────────────────────────┘                └──────────────────────────────┘


---

## 2. Definición del Flujo de Trabajo (Workflow)

El proceso operativo de **NEVEN-SIM** se divide en cuatro fases perfectamente delimitadas:

[Selección en Excel] ──> [Ajuste & Tuning en WebViewer] ──> [Simulación de Alto Impacto] ──> [Análisis & Reportes]


### Fase 1: Selección y Entrada de Datos
1. El usuario selecciona un rango de celdas en Excel que contiene datos históricos o define directamente una celda como variable de entrada ("Supuesto" o *Assumption*). Puede tratarse de datos estáticos transversales o de una serie de tiempo cronológica.
2. El WebViewer captura esta entrada a través de la infraestructura actual de comunicación de NEVEN.

### Fase 2: Ajuste de Distribuciones, Series Temporales y Tuning Reactivo (R + WebViewer)
1. **Modelos Estáticos:** Los datos históricos se envían a R, el cual ejecuta algoritmos de ajuste (`fitdistrplus`) y devuelve las distribuciones candidatas con sus pruebas de bondad de ajuste (Kolmogorov-Smirnov, Anderson-Darling).
2. **Modelos Temporales (Predictor):** Si la entrada es una serie de tiempo, R ejecuta de forma automatizada modelos predictivos como Auto-ARIMA (`forecast` / `fable`) o Redes Neuronales autorregresivas (`nnetar`), extrayendo los coeficientes óptimos y la varianza del error.
3. **Tuning Reactivo (Modo Sandbox):** El WebViewer renderiza de forma interactiva la curva o trayectoria sugerida. El usuario puede modificar los parámetros de la distribución o el modelo predictivo mediante barras de selección (*sliders*) en el WebViewer, redibujando la PDF o las bandas de confianza en tiempo real antes de la simulación.

### Fase 3: Ejecución de la Simulación y Estructuración de Dependencias (Julia)
1. La configuración aceptada se serializa y se transmite al motor de **Julia**.
2. **Modelado de Dependencias (Cópulas):** Si el modelo financiero posee variables correlacionadas (supuestos dependientes), Julia asume la construcción matemática de la distribución conjunta utilizando librerías nativas de cópulas para garantizar la coherencia multivariante en el muestreo.
3. **Inferencia de Montecarlo:** Julia precompila las funciones estocásticas y corre de manera masiva los millones de escenarios requeridos a velocidad nativa. En esta primera fase, se utiliza el puente actual de NEVEN para resolver las celdas dependientes directamente en Excel.

### Fase 4: Visualización y Reportes Quarto (WebViewer)
1. Los arrays masivos de resultados de simulación y proyecciones temporales se transmiten a gran velocidad de vuelta a Python mediante cargas útiles (payloads) de **Protobuf**.
2. Python genera la visualización dinámica (histogramas interactivos, gráficos de dispersión, abanicos de trayectorias temporales y gráficos de Tornado de sensibilidad mediante correlación de rangos de Spearman) en el WebViewer.
3. El usuario puede compilar con un solo clic un reporte final auditable en PDF o HTML utilizando la suite de **Quarto** ya integrada en NEVEN.

---

## 3. División Tecnológica de Responsabilidades

Para asegurar la modularidad y escalabilidad del sistema, cada tecnología del backend de NEVEN se especializa en un área donde posee una ventaja comparativa insuperable:

### 3.1. Julia: Motor Numérico y Modelado de Dependencias Avanzado
*   **Rol:** Procesamiento estocástico de alta velocidad, paralelización nativa y muestreo conjunto.
*   **Responsabilidades:**
    *   Generación de vectores aleatorios correlacionados mediante estructuras matemáticas complejas (Cópulas).
    *   Ejecución de simulaciones Montecarlo masivas y trayectorias dinámicas multoperíodo con compilación JIT.
    *   Algoritmos de optimización bajo incertidumbre (metaheurísticas/genéticos para emular la funcionalidad de OptQuest).
*   **Librerías Clave:** `Distributions.jl`, `Copulas.jl`, `BiCopulas.jl`, `Random.jl`, `LoopVectorization.jl`, `BlackBoxOptim.jl`.

### 3.2. R: Rigor Estadístico e Inferencia Predictiva Automatizada
*   **Rol:** Análisis matemático, ajuste de datos y modelado predictivo temporal.
*   **Responsabilidades:**
    *   Ajuste paramétrico de datos históricos transversales y pruebas de bondad de ajuste.
    *   Identificación, diferenciación y estimación automática de modelos de series de tiempo (Auto-ARIMA).
    *   Modelado de patrones no lineales en series temporales mediante aproximaciones de redes neuronales.
*   **Librerías Clave:** `fitdistrplus`, `forecast`, `fable`, `nnetar`.

### 3.3. Python: Orquestación, Serialización y Servicios WebViewer
*   **Rol:** Sistema nervioso central y canal de integración.
*   **Responsabilidades:**
    *   Gestión de la comunicación bidireccional entre la hoja de Excel, la interfaz del WebViewer y los lenguajes analíticos.
    *   Intermediación de llamadas remotas, control de estados y transformación de formatos.
    *   Definición e instrumentación de esquemas de datos estructurados para canalizar información masiva a gran velocidad.
*   **Librerías Clave:** `protobuf` (para la definición del protocolo de datos), `FastAPI` / `websockets` (para la comunicación síncrona/asíncrona con el WebViewer).

## 4. Diseño del Protocolo de Datos (Protobuf Schema)

Para garantizar que el transporte de millones de muestras simuladas y trayectorias temporales complejas entre Julia, Python, R y el WebViewer no sature la memoria ni el procesador, se propone un esquema robusto y tipado basado en **Protocol Buffers**.

```protobuf
syntax = "proto3";

package neven_sim;

// Definición de un supuesto de entrada (input de simulación estática o temporal)
message Assumption {
  string name = 1;
  string type = 2; // "STATIC_DISTRIBUTION" o "TIME_SERIES"
  string distribution_or_model_type = 3; // e.g., "Normal", "Triangular", "ARIMA", "NNETAR"
  repeated double parameters = 4; // Parámetros correspondientes (e.g., [mean, std_dev] o coeficientes del modelo)
  repeated double historical_data = 5; // Serie histórica original
  
  // Estructura para el manejo de dependencias por cópulas
  bool has_dependencies = 6;
  string copula_type = 7; // e.g., "Gaussian", "Clayton", "Gumbel"
  repeated string dependency_targets = 8; // Variables con las que se correlaciona
  repeated double dependency_parameters = 9; // Parámetros de la matriz de dependencia o cópula
}

// Resultados consolidados de una variable de pronóstico u output de simulación
message ForecastResult {
  string name = 1;
  repeated double simulated_values = 2; // El array masivo de resultados simulados (caso estático)
  repeated double simulated_trajectories = 3; // Matriz aplanada (Iteraciones x Tiempo) para series de tiempo
  double mean = 4;
  double median = 5;
  double std_dev = 6;
  double min = 7;
  double max = 8;
  repeated double percentiles = 9; // Percentiles calculados del 1% al 99%
}

// Orquestación completa de un caso de simulación (Payload Principal)
message SimulationPayload {
  string simulation_id = 1;
  int32 iterations = 2;
  int32 time_horizon = 3; // Número de períodos hacia el futuro a simular (para series temporales)
  repeated Assumption assumptions = 4;
  repeated ForecastResult forecasts = 5;
  repeated double sensitivity_coefficients = 6; // Coeficientes de correlación de Spearman para Tornado
}

## 5. Diseño de Interfaz de Usuario (UI/UX) para WebViewer

La interfaz del WebViewer de NEVEN-SIM actuará como un entorno de escritorio integrado dentro de Excel, estructurado en tres paneles funcionales responsivos:

┌────────────────────────────────────────────────────────────────────────┐
│ NEVEN-SIM WORKSPACE                                              [ X ] │
├──────────────────────────────────────┬─────────────────────────────────┤
│ PANEL IZQUIERDO: CONFIGURACIÓN       │ PANEL DERECHO: VISUALIZACIÓN    │
│                                      │                                 │
│ [ Supuestos ] [ Pronósticos ]        │  Abanico de Proyección Temporal │
│ Variable Activa: Demanda_Proyectada  │  ┌───────────────────────────┐  │
│ Tipo: Serie Temporal (Auto-ARIMA)    │  │                 _..---    │  │
│ Rango Excel: $C$2:$C$48              │  │       _..---''''          │  │
│                                      │  │───────----------------────│  │
│ Ajuste Fino (Tuning Real-Time):      │  │       ````----....____    │  │
│ p (AR)     [─────o──────────] 1      │  └───────────────────────────┘  │
│ d (Diff)   [──o─────────────] 1      │     (Bandas de Confianza / VaR) │
│ q (MA)     [───────────o────] 2      │                                 │
│                                      │  Percentiles de Decisión (Final)│
│ Dependencias (Cópula Activa):        │  * 10%: $9,120                  │
│ [x] Vincular con Precio_Petróleo     │  * 50%: $14,200 (Mediana)       │
│ Tipo: Clayton Copula (Cola Inf.)     │  * 90%: $21,500                 │
├──────────────────────────────────────┴─────────────────────────────────┤
│ [ EJECUTAR SIMULACIÓN (1,000,000 Iteraciones en Julia) ]               │
└────────────────────────────────────────────────────────────────────────┘

Controles Reactivos Dinámicos: Los deslizadores (sliders) de los parámetros recalculan y actualizan la densidad de probabilidad (PDF) o los abanicos de proyección temporal mostrados en el panel derecho de forma asíncrona, enviando el micro-ajuste de manera instantánea para redibujar la gráfica sin congelar la interfaz ni la hoja de cálculo.

Análisis Multivariable Tornado: Visualización dinámica de barras apiladas de sensibilidad que mide el impacto relativo de cada supuesto sobre la variabilidad del pronóstico mediante correlación de rango de Spearman.

## 6. Estrategia de Implementación por Fases

Para mitigar riesgos técnicos e iterar de forma controlada, el desarrollo se dividirá en dos fases fundamentales:

# Fase 1: MVP Funcional e Integración Base (Enfoque Actual)
Objetivo: Construir la funcionalidad estocástica y predictiva sin alterar la arquitectura central de NEVEN.

Alcance:

Desarrollar el flujo básico en el WebViewer para seleccionar rangos de datos históricos transversales o temporales en Excel.

Configurar el pipeline de R en el backend para ejecutar el ajuste estadístico básico y la estimación automatizada de series de tiempo mediante Auto-ARIMA.

Implementar el modelado de dependencias mediante cópulas gaussianas/arquímedes y la generación de muestras masivas en Julia a través de Protobuf.

Utilizar las llamadas nativas de NEVEN para actualizar el recálculo de fórmulas de Excel en las iteraciones de Montecarlo.

Presentar resultados finales y gráficos interactivos básicos en el WebViewer.

# Fase 2: Optimización Extrema e Interfaces Reactivas (Aceleración Científica)
Objetivo: Maximizar el rendimiento y la velocidad de simulación bajo alta exigencia computational.

Alcance:

Paralelización de Escenarios en Julia: Ejecutar hilos de procesamiento asíncronos para separar el motor de cálculo de los tiempos de espera de Excel.

Modelos Avanzados de ML en R: Incorporar redes neuronales recurrentes o modelos de machine learning avanzados para la estimación de series temporales complejas con alta volatilidad.

Evaluación de Fórmulas Fuera de Excel (Fase Opcional): Estructurar un parser lógico en Python/Julia que traduzca las fórmulas financieras clave de Excel a funciones puras compiladas de Julia para evaluarlas en memoria a velocidades óptimas, evitando el cuello de botella físico de la hoja de cálculo.

Gráficos Interactivos de Alta Fidelidad: Integrar Plotly o D3.js en la interfaz del WebViewer para permitir manipulaciones avanzadas (zoom, aislamiento de colas de probabilidad, cálculo dinámico de valor en riesgo o VaR sobre la gráfica en caliente).