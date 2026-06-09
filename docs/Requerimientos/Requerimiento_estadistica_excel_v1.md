# Requerimiento de Trabajo: Integración Interactiva de Análisis Estadístico en Excel

**ID:** REQ-002  
**Fecha:** 2026-04-17  
**Estado:** Pendiente de asignación  
**Prioridad:** Alta  
**Relacionado con:** REQ-001 (Integración Tidyverse en Excel)

---

## 1. Resumen Ejecutivo

Desarrollar un módulo complementario al Add-in de Excel definido en REQ-001, que exponga capacidades de **análisis estadístico avanzado** mediante 10 librerías clave de R, incluyendo estadística clásica, modelos de efectos mixtos, análisis de supervivencia, series de tiempo, econometría con datos de panel, estadística bayesiana y visualizaciones interactivas con D3.js.

El objetivo es permitir que usuarios de negocio, analistas y economistas ejecuten análisis estadísticos sofisticados directamente desde Excel, sin salir del entorno que ya conocen.

---

## 2. Contexto y Justificación

El REQ-001 estableció la base de integración R-Excel orientada a transformación de datos con Tidyverse. Este requerimiento extiende esa base hacia el **análisis estadístico**, cubriendo necesidades más avanzadas presentes en equipos de:

- Finanzas y econometría (datos de panel, series de tiempo).
- Investigación y ciencias sociales (efectos mixtos, psicometría).
- Salud y estudios clínicos (análisis de supervivencia).
- Inteligencia de negocio (visualizaciones D3 interactivas).
- Modelado probabilístico (estadística bayesiana).

---

## 3. Librerías en Alcance

| # | Librería       | Categoría                        | Versión mínima |
|---|----------------|----------------------------------|----------------|
| 1 | `stats`        | Estadística base                 | R base (4.4.1) |
| 2 | `lme4`         | Modelos de efectos mixtos        | 1.1-35         |
| 3 | `survival`     | Análisis de supervivencia        | 3.5            |
| 4 | `forecast`     | Series de tiempo                 | 8.21           |
| 5 | `psych`        | Psicometría y análisis factorial | 2.4            |
| 6 | `car`          | Supuestos de regresión           | 3.1            |
| 7 | `Hmisc`        | Estadística descriptiva avanzada | 5.1            |
| 8 | `rstanarm`     | Estadística bayesiana            | 2.21           |
| 9 | `plm`          | Econometría — datos de panel     | 2.6            |
| 10| `r2d3`         | Visualización D3.js desde R      | 0.2.6          |

---

## 4. Alcance

### 4.1 Dentro del alcance

- Panel lateral en Excel (Task Pane) con módulos separados por categoría estadística.
- Formularios interactivos para cada librería sin necesidad de escribir código R.
- Modo avanzado con editor de código R para usuarios técnicos.
- Retorno de resultados tabulares a celdas de Excel.
- Renderizado de gráficos estáticos (ggplot2/base R) como imagen incrustada.
- Renderizado de visualizaciones D3 (r2d3) como HTML interactivo en panel lateral.
- Log de ejecución en tiempo real con mensajes de error legibles.

### 4.2 Fuera del alcance (v1)

- Integración con bases de datos externas (SQL, NoSQL).
- Ejecución distribuida o en clúster.
- Soporte para Stan completo (solo interfaz rstanarm simplificada).
- Versiones de Excel anteriores a 2019.
- Soporte para `fable` (se incluye en iteración futura junto a tidyverse).

---

## 5. Requerimientos Funcionales

### RF-01: Módulo — Estadística Base (`stats`)

Exponer mediante formularios las siguientes funcionalidades:

| Función                  | Descripción                                              |
|--------------------------|----------------------------------------------------------|
| Regresión lineal (`lm`)  | Configurar variable dependiente e independientes         |
| Regresión logística (`glm`) | Selección de familia y link                           |
| T-test                   | Una muestra, dos muestras, pareado                       |
| ANOVA                    | Una vía y dos vías                                       |
| Chi-cuadrado             | Prueba de independencia entre variables categóricas      |
| Correlación              | Pearson, Spearman, Kendall                               |

**Salida esperada:** Tabla de coeficientes, p-valores, R², intervalos de confianza escritos en Excel.

---

### RF-02: Módulo — Modelos de Efectos Mixtos (`lme4`)

| Función   | Descripción                                                    |
|-----------|----------------------------------------------------------------|
| `lmer()`  | Modelo lineal de efectos mixtos                                |
| `glmer()` | Modelo lineal generalizado de efectos mixtos                   |

**Configuración desde formulario:**
- Variable dependiente.
- Efectos fijos (selección múltiple de columnas).
- Efectos aleatorios (selección de variable de agrupación).
- Familia de distribución para `glmer` (binomial, Poisson, etc.).

**Salida esperada:** Tabla de efectos fijos, varianzas de efectos aleatorios, AIC/BIC.

---

### RF-03: Módulo — Análisis de Supervivencia (`survival`)

| Función              | Descripción                                              |
|----------------------|----------------------------------------------------------|
| Kaplan-Meier         | Estimación de curva de supervivencia                     |
| Log-rank test        | Comparación de curvas entre grupos                       |
| Cox Proportional Hazards | Modelo de riesgos proporcionales                    |

**Configuración desde formulario:**
- Variable de tiempo.
- Variable de evento/censura (0/1).
- Variable de grupo (para Kaplan-Meier y log-rank).
- Covariables (para Cox).

**Salida esperada:** Tabla de resultados + curva de supervivencia como imagen en Excel.

---

### RF-04: Módulo — Series de Tiempo (`forecast`)

| Función       | Descripción                                              |
|---------------|----------------------------------------------------------|
| `auto.arima()`| Selección automática de modelo ARIMA                     |
| `ets()`       | Suavizado exponencial                                    |
| `forecast()`  | Generación de pronóstico con intervalos de confianza     |
| `decompose()` | Descomposición de serie en tendencia, estacionalidad, residuo |

**Configuración desde formulario:**
- Selección de columna como serie de tiempo.
- Frecuencia (diaria, mensual, trimestral, anual).
- Horizonte de pronóstico (número de períodos).

**Salida esperada:** Tabla de valores pronosticados + gráfico de serie con pronóstico.

---

### RF-05: Módulo — Psicometría y Análisis Factorial (`psych`)

| Función         | Descripción                                            |
|-----------------|--------------------------------------------------------|
| `describe()`    | Estadística descriptiva avanzada (skewness, kurtosis)  |
| `alpha()`       | Alfa de Cronbach para confiabilidad de escalas         |
| `fa()`          | Análisis factorial exploratorio                        |
| `principal()`   | Análisis de componentes principales (PCA)              |
| `corr.test()`   | Matriz de correlaciones con p-valores                  |

**Salida esperada:** Tablas de resultados escritas en Excel + gráfico de cargas factoriales (opcional).

---

### RF-06: Módulo — Supuestos de Regresión (`car`)

| Función        | Descripción                                             |
|----------------|---------------------------------------------------------|
| `vif()`        | Factor de inflación de varianza (multicolinealidad)     |
| `ncvTest()`    | Prueba de homocedasticidad (Breusch-Pagan)              |
| `outlierTest()`| Detección de outliers en regresión                      |
| `Anova()`      | ANOVA tipo II y III                                     |

**Configuración:** El usuario selecciona un modelo previamente ejecutado (desde RF-01) y aplica las pruebas sobre él.

**Salida esperada:** Tabla de estadísticos y p-valores por prueba.

---

### RF-07: Módulo — Estadística Descriptiva e Imputación (`Hmisc`)

| Función        | Descripción                                             |
|----------------|---------------------------------------------------------|
| `describe()`   | Resumen estadístico detallado por variable              |
| `impute()`     | Imputación de valores faltantes (media, mediana, moda)  |
| `rcorr()`      | Correlaciones con n observaciones y p-valores           |
| `cut2()`       | Discretización de variables continuas en cuantiles      |

**Salida esperada:** Tabla de resumen estadístico y dataset imputado escrito en Excel.

---

### RF-08: Módulo — Estadística Bayesiana (`rstanarm`)

| Función          | Descripción                                           |
|------------------|-------------------------------------------------------|
| `stan_lm()`      | Regresión lineal bayesiana                            |
| `stan_glm()`     | Regresión logística / Poisson bayesiana               |
| `posterior_interval()` | Intervalos creíbles del posterior                |
| `pp_check()`     | Verificación predictiva posterior (gráfico)           |

**Configuración desde formulario:**
- Variable dependiente e independientes.
- Número de iteraciones de MCMC (default: 2000).
- Número de cadenas (default: 4).
- Prior (normal, Cauchy, laplace — selección con valores por defecto).

**Salida esperada:** Tabla de coeficientes con intervalos creíbles + gráfico de distribución posterior.

> ⚠️ **Nota de rendimiento:** Los modelos bayesianos pueden tardar varios minutos. El panel debe mostrar una barra de progreso y permitir cancelar la ejecución.

---

### RF-09: Módulo — Econometría de Datos de Panel (`plm`)

| Función          | Descripción                                           |
|------------------|-------------------------------------------------------|
| `plm()`          | Estimación de modelos de panel (FE, RE, FD)           |
| `phtest()`       | Prueba de Hausman (FE vs RE)                          |
| `plmtest()`      | Prueba de Breusch-Pagan para efectos aleatorios       |
| `purtest()`      | Prueba de raíz unitaria para datos de panel           |
| `pvcm()`         | Coeficientes variables en panel                       |

**Configuración desde formulario:**
- Variable dependiente e independientes.
- Variable de índice de entidad (ej. país, empresa).
- Variable de índice de tiempo (ej. año, trimestre).
- Modelo: Efectos Fijos (`within`), Efectos Aleatorios (`random`), Primeras Diferencias (`fd`).
- Efecto: individual, time, twoways.

**Salida esperada:** Tabla de coeficientes, errores estándar, t-estadísticos, R² within/between/overall + resultados de pruebas de especificación.

---

### RF-10: Módulo — Visualización D3 Interactiva (`r2d3`)

| Funcionalidad               | Descripción                                              |
|-----------------------------|----------------------------------------------------------|
| Gráficos D3 predefinidos    | Biblioteca de plantillas D3 parametrizables              |
| Editor de script D3         | Editor para usuarios avanzados que escriben D3 propio    |
| Renderizado en panel        | Visualización interactiva dentro del Task Pane de Excel  |
| Exportación HTML            | Exportar la visualización como archivo HTML standalone   |

**Plantillas D3 incluidas en v1:**
- Gráfico de barras apiladas.
- Treemap.
- Gráfico de red (nodos y enlaces).
- Heatmap de correlación.
- Gráfico de líneas con zoom y tooltip interactivo.

**Configuración desde formulario:**
- Selección de rango de datos en Excel.
- Selección de plantilla D3.
- Mapeo de columnas a dimensiones visuales (X, Y, color, tamaño, tooltip).

**Salida esperada:** Visualización interactiva D3 renderizada en el panel lateral. Opción de exportar como HTML.

---

### RF-11: Gestión de Modelos

- El sistema debe mantener una sesión R persistente durante la sesión de Excel.
- Los modelos ejecutados (lm, lmer, plm, etc.) deben guardarse en memoria de sesión y ser referenciables por nombre en pasos posteriores (ej. aplicar `car::vif()` sobre un modelo ya estimado).
- El usuario debe poder ver, nombrar y eliminar modelos guardados desde el panel.

---

### RF-12: Modo de Código R Avanzado

- Editor de código R dentro del panel para usuarios técnicos.
- El rango seleccionado en Excel está disponible como variable `df`.
- Acceso a todos los modelos guardados en sesión.
- El resultado (si es `data.frame`) puede escribirse de vuelta a Excel.

---

## 6. Requerimientos No Funcionales

| ID     | Categoría       | Descripción                                                                              |
|--------|-----------------|------------------------------------------------------------------------------------------|
| RNF-01 | Rendimiento     | Operaciones de `stats`, `car`, `Hmisc`, `psych` en < 5 segundos para datasets < 100K filas |
| RNF-02 | Rendimiento     | Modelos bayesianos (`rstanarm`) deben mostrar progreso; tiempo máximo tolerable: 10 min  |
| RNF-03 | Compatibilidad  | Excel 2019, 2021 y Microsoft 365 (Windows y Mac)                                        |
| RNF-04 | Seguridad       | Ejecución 100% local; sin transmisión de datos a servidores externos                    |
| RNF-05 | Instalación     | Instalador único que incluye R 4.4.1 y todas las dependencias                           |
| RNF-06 | Usabilidad      | Usuario sin experiencia en R debe ejecutar una regresión lineal en < 5 minutos           |
| RNF-07 | Mantenibilidad  | Cada módulo de librería debe ser independiente y reemplazable sin afectar los demás      |

---

## 7. Arquitectura Propuesta

```
┌──────────────────────────────────────────────────────┐
│                  Microsoft Excel                     │
│  ┌────────────────────────────────────────────────┐  │
│  │         Office Add-in Task Pane (React)        │  │
│  │                                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │  │
│  │  │  Stats   │  │  Panel   │  │  r2d3 / D3  │  │  │
│  │  │  Modules │  │  Models  │  │  Renderer   │  │  │
│  │  └────┬─────┘  └────┬─────┘  └──────┬──────┘  │  │
│  └───────┼─────────────┼───────────────┼──────────┘  │
│          │   Office.js API             │             │
│  ┌───────▼─────────────▼───────────────▼──────────┐  │
│  │           Excel Data Bridge                    │  │
│  │      (lectura/escritura rangos y hojas)        │  │
└──┴────────────────────┬───────────────────────────┴──┘
                        │ HTTP / IPC
           ┌────────────▼─────────────┐
           │    Backend Local R        │
           │    plumber API (R 4.4.1)  │
           │                          │
           │  /stats   --> stats, car   │
           │  /mixed   --> lme4         │
           │  /survival--> survival     │
           │  /ts      --> forecast     │
           │  /psycho  --> psych, Hmisc │
           │  /bayes   --> rstanarm     │
           │  /panel   --> plm          │
           │  /d3      --> r2d3         │
           └──────────────────────────┘
```

---

## 8. Criterios de Aceptación

- [ ] El usuario puede ejecutar una regresión lineal (`lm`) y ver coeficientes en Excel sin escribir código.
- [ ] Un modelo `plm` de efectos fijos con prueba de Hausman se ejecuta y devuelve resultados a Excel.
- [ ] Una curva de Kaplan-Meier se genera e inserta como imagen en la hoja activa.
- [ ] Un pronóstico ARIMA con horizonte configurable escribe los valores en Excel.
- [ ] Una visualización D3 (heatmap o barras apiladas) se renderiza en el panel lateral.
- [ ] Los modelos estimados persisten en sesión y pueden referenciarse desde otros módulos.
- [ ] El instalador despliega el entorno completo (R + librerías) sin intervención manual del usuario.
- [ ] Los modelos bayesianos muestran barra de progreso y permiten cancelación.

---

## 9. Dependencias

- **REQ-001:** Este módulo extiende el Add-in base definido en REQ-001. El backend R y el Task Pane deben estar operativos.
- **R 4.4.1** con los 10 paquetes instalados y sus dependencias transitivas.
- **Stan / rstan:** Dependencia de `rstanarm`; requiere compilador C++ (incluir en instalador).
- **Microsoft 365 Developer Account** para pruebas y publicación del Add-in.

---

## 10. Riesgos

| Riesgo                                                  | Probabilidad | Impacto | Mitigación                                                       |
|---------------------------------------------------------|--------------|---------|------------------------------------------------------------------|
| Compilación de Stan falla en entornos corporativos      | Alta         | Alto    | Distribuir binarios precompilados de rstan                       |
| Tiempo de carga de `rstanarm` elevado                   | Alta         | Medio   | Cargar en background al iniciar la sesión R                      |
| r2d3 genera HTML que no renderiza en iframe del Add-in  | Media        | Alto    | Evaluar sandboxed WebView2 como renderizador alternativo         |
| plm requiere estructura exacta de datos de panel        | Media        | Medio   | Validar y guiar al usuario con mensajes de error descriptivos    |
| Tamaño del instalador excesivo (Stan + R + librerías)   | Alta         | Medio   | Evaluar descarga lazy de componentes opcionales (ej. rstanarm)   |

---

## 11. Entregables

1. **Diseño técnico detallado** de los 10 módulos estadísticos.
2. **Backend R** con endpoints plumber para cada librería.
3. **Frontend React** con formularios por módulo integrados al Task Pane.
4. **Biblioteca de plantillas D3** con 5 tipos de visualización.
5. **Suite de pruebas** con datasets de referencia por módulo.
6. **Instalador unificado** (R + Stan + librerías + Add-in).
7. **Manual de usuario** con ejemplos por tipo de análisis.
8. **Documentación técnica** de la API plumber interna.

---

## 12. Estimación de Esfuerzo (preliminar)

| Componente                                  | Estimado   |
|---------------------------------------------|------------|
| Diseño técnico y UX de los 10 módulos       | 3 semanas  |
| Backend R — módulos stats, car, Hmisc, psych| 2 semanas  |
| Backend R — lme4, survival, forecast        | 2 semanas  |
| Backend R — plm (panel), rstanarm (bayes)   | 3 semanas  |
| Backend R — r2d3 + biblioteca D3            | 3 semanas  |
| Frontend React — formularios 10 módulos     | 5 semanas  |
| Gestión de modelos en sesión                | 1 semana   |
| Integración, pruebas y QA                   | 3 semanas  |
| Instalador unificado (incl. Stan)           | 2 semanas  |
| Documentación                               | 1 semana   |
| **Total estimado**                          | **25 semanas** |

---

## 13. Referencias

- [stats — R Documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/00Index.html)
- [lme4 — CRAN](https://cran.r-project.org/web/packages/lme4/)
- [survival — CRAN](https://cran.r-project.org/web/packages/survival/)
- [forecast — Rob Hyndman](https://pkg.robjhyndman.com/forecast/)
- [psych — CRAN](https://cran.r-project.org/web/packages/psych/)
- [car — CRAN](https://cran.r-project.org/web/packages/car/)
- [Hmisc — CRAN](https://cran.r-project.org/web/packages/Hmisc/)
- [rstanarm — mc-stan.org](https://mc-stan.org/rstanarm/)
- [plm — CRAN](https://cran.r-project.org/web/packages/plm/)
- [r2d3 — rstudio.github.io](https://rstudio.github.io/r2d3/)
- [REQ-001 — Integración Tidyverse en Excel](./requerimiento_tidyverse_excel.md)

---

*Documento generado el 17 de abril de 2026. Versión 1.0.*
