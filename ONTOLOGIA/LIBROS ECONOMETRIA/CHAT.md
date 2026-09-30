# Bitácora de Desarrollo: Ontología de Econometría & Inferencia Causal en R

Este documento contiene el historial cronológico estructurado, las acciones solicitadas, los problemas identificados, las soluciones técnicas alcanzadas y el estado del arte del proyecto para permitir la transferencia completa de contexto a otro modelo de inteligencia artificial.

---

## 1. Visión General del Proyecto

- **Objetivo**: Construir una ontología formal, rigurosa y conectada que modele el conocimiento de **Inferencia Causal, Econometría (Microeconometría, Series de Tiempo, Econometría Espacial) y Modelos Lineales Generalizados**, vinculando marcos epistemológicos, supuestos matemáticos de identificación, sesgos/conceptos analíticos, métodos de estimación, paquetes de R y funciones ejecutables.
- **Espacio de Trabajo**: `c:\Users\mboni\Desktop\LIBROS`
- **Componentes Clave**:
  - **Esquema de Ontología**: `memory/ontology/schema.yaml`
  - **Grafo Ontológico (Knowledge Graph)**: `memory/ontology/graph.jsonl`
  - **Visualizador 2D Minimalista**: `memory/ontology/graph_visualization.html` (Vis.js, paleta nórdica danesa/grafito)
  - **Visualizador 3D Cyber / WebGL**: `memory/ontology/graph_visualization_3d.html` (Three.js / 3D Force Graph)

---

## 2. Cronología de Solicitudes del Usuario y Acciones Realizadas

### Fase 1: Visualización Inicial y Estilo
1. **Solicitud**: `"no hay contenido"`
   - *Problema*: Al abrir el archivo HTML localmente mediante `file://`, el navegador bloqueaba las llamadas `fetch('graph.jsonl')` por políticas CORS del navegador.
   - *Solución*: Se incrustó directamente la estructura del dataset dentro de los archivos HTML (`rawGraph = [...]`), logrando visualizadores 100% autocontenidos (*self-contained*).
2. **Solicitud**: `"En lugar de tonos azules, emplea tonos gris grafito, son mucho más amigables. Para colores utiliza colores pastel, emulemos el minimalismo Danes"`
   - *Solución*: Se rediseñó la interfaz 2D con fondo grafito carbón mate (`#141518`, `#1a1b1f`) y paleta nórdica pastel en `schema.yaml` / `graph_visualization.html`.
3. **Solicitud**: `"los botones debe ser minimalistas. Los tonos verdes degradan el enfoque minimalista"` y controles de navegación D-Pad.
   - *Solución*: Se eliminaron contrastes verdes estridentes; se incorporó un D-Pad y botones ultraplanos y sutiles.

### Fase 2: Creación del Visualizador 3D y Paleta Cyber
4. **Solicitud**: `"crees que usando HTML5 podamos hacer algo más interactivo en 3D?"` y `"luce genial, ahora podemos aplicar colores vivos en lugar de los minimalistas"`
   - *Solución*: Se creó `graph_visualization_3d.html` utilizando `3d-force-graph` (WebGL / Three.js), partículas cinemáticas en aristas, rotación orbital 360° y paleta viva Cyber/Neón de alto contraste.

### Fase 3: Auditoría y Refinamiento Ontológico
5. **Solicitud**: `"Estamos listos con la visualización, pero debemos refinar la ontologia"` y `"al visualizar la ontología noté que hay varios elementos aislados que no deberían estarlo. Por ejemplo note que Vector Autoregression está aislado, pero ese es un concepto relacionado a las series de tiempo"`.
   - *Problema*: Existían 18 nodos huérfanos/desconectados en el grafo.
   - *Solución*:
     - Se amplió `schema.yaml` con predicados: `evaluates`, `alternative_to`, y flexibilidad en `part_of`.
     - Se crearon conexiones estructurales completas: `method_var` se conectó a `framework_time_series`, `concept_stationarity`, `concept_cointegration`, `rpkg_vars` y funciones `VAR()`, `causality()`.
     - Auditoría verificada: **0 nodos aislados** (97 entidades, 131 aristas).
6. **Solicitud**: `"ST_READ me parece que es un nodo desconectado de Series de Tiempo. Adicionalmente al seleccionar cada nodo deberia mostrarse una explicacion para que el usuario pueda tener mayor acceso conceptual"`.
   - *Clarificación metodológica*: `st_read` no es de series de tiempo, sino de Econometría Espacial / Simple Features (`sf`).
   - *Solución*: Se conectó `st_read()` a `rpkg_sf`, `framework_spatial_econometrics`, y modelos espaciales `SAR` / `SEM`. Se diseñó el acceso conceptual detallado al hacer clic en nodos.

### Fase 4: Depuración de la Visualización 3D y Definiciones
7. **Solicitud**: `"el grafo no se muestra"`, `"no aparecen las definiciones de los nodos"` y `"todo luce genial, pero solo aparece TITULO, no aparece Definición Conceptual & Teórica, Relevancia Metodológica, Vínculos en el Grafo"`.
   - *Problema*: En el visualizador 3D, el motor WebGL mutaba los objetos en el callback `onNodeClick` y los selectores del DOM estático perdían los datos de las definiciones teóricas.
   - *Solución*:
     - Se unificó la arquitectura del visualizador 3D con la del 2D.
     - Se implementó un mapeo directo por ID inmutable (`nodesMap[node.id]`).
     - Se estructuró la tarjeta `#details-card` con: Título (`#card-title`), Tipo (`#card-type`), Caja de definición con borde dinámico (`.definition-box`, `#def-header`, `#card-desc`) y lista de relaciones (`#card-rels`).

### Fase 5: Ajuste Metodológico en Modelos de Respuesta Binaria (Logit/Probit)
8. **Solicitud**: `"La relacion Binary tiene un error, Logit y Probit son BINARY y ambos se estiman con glm()"`
   - *Diagnóstico*: En versiones previas, `method_logit` y `method_probit` tenían una relación incorrecta `adjusts_for` hacia `concept_binary_outcome` y faltaba vincular el paquete base `stats`.
   - *Solución Aplicada*:
     - `method_logit` y `method_probit` ahora tienen relación `requires -> concept_binary_outcome`.
     - Ambos métodos usan `uses_r_function -> rfunc_glm`.
     - Ambos son alternativas directas entre sí: `method_logit alternative_to method_probit`.
     - Se añadió la entidad `rpkg_stats` (`stats`) y la relación `rfunc_glm implemented_in_r_package rpkg_stats`.
     - Ambos forman parte de `framework_microeconometrics`.

### Fase 6: Enriquecimiento Total de Definiciones e Interactividad en Visualización 3D
9. **Solicitud**: `"tenemos un problema con el archivo de visualizacion 3D. Se espera que cada nodo contenga ademas del titulo la informacion necesaria para que el usuario pueda tener definiciones y entender su contenido"`
   - *Diagnóstico*: El visualizador 3D solo mostraba el título y tipo en los tooltips al pasar el cursor (`nodeLabel`), no incluía etiquetas de texto 3D visibles en el espacio WebGL, los vínculos no eran interactivos y faltaban cajas contextuales de relevancia metodológica y HUD dinámico.
   - *Solución Implementada en `graph_visualization_3d.html`*:
     - **Tooltips Flotantes Enriquecidos (`nodeLabel`)**: Cada nodo muestra ahora una tarjeta glassmorphism con: Nombre, Badge de Tipo de Entidad con color neón, Rol contextual (ej. *Supuesto de Identificación Causal*, *Paquete CRAN*, *Función R*), Definición Teórica/Metodológica completa y conteo de vínculos.
     - **Etiquetas 3D en Escena (Sprites Canvas WebGL)**: Se renderizaron sprites 3D nítidos con el nombre de cada nodo bajo su esfera con botón para alternar `🏷️ Etiquetas 3D (ON/OFF)`.
     - **Resaltado de Subgrafo Conectado**: Al posarse o hacer clic en un nodo, se iluminan sus vecinos directos y aristas con flujo de partículas cian, atenuando el resto del grafo.
     - **Panel Lateral `#details-card` Completo**: Título, Badge, Metadatos de R (`library(...)`), Definición Conceptual, Bloque de *Relevancia Metodológica* y lista de relaciones organizadas (salientes y entrantes) con **chips cliqueables** para saltar instantáneamente entre nodos interconectados.
     - **Filtros por Entidad y Enfoques Temáticos**: Botones de filtrado rápido (`Framework`, `Method`, `Concept`, `Assumption`, `RPackage`, `RFunction`) y accesos a clusters (*Inferencia Causal*, *Microeconometría*, *Series de Tiempo*, *Econometría Espacial*,### Fase 7: Corrección Crítica del Render 3D (Inyección de Three.js & Resiliencia de Sprites)
75. **Solicitud**: `"no se muestran los nodos ni las imagenes"`
   - *Diagnóstico*: Al cargar `graph_visualization_3d.html`, la pantalla permanecía en negro y no se renderizaban los nodos. El bundle genérico de CDN `unpkg.com/3d-force-graph` no exponía la instancia global de `THREE` en el ámbito de ventana antes de invocar `nodeThreeObject`, generando un fallo por `ReferenceError` no capturado en `new THREE.CanvasTexture()`.
   - *Solución Técnica Aplicada*:
     - **Carga Explícita de Dependencia**: Se importó `three@0.169.0/build/three.min.js` de forma prioritaria antes de `3d-force-graph@1.73.0`.
     - **Manejo Defensivo de Sprites**: Se envolvió `createTextSprite()` en bloques `try/catch` con verificación estricta (`typeof THREE === 'undefined'`) para devolver `null` de manera segura sin interrumpir el bucle de renderizado WebGL.
     - **Secuencia de Inicialización Robusta**: Se configuró `show3DLabels = false` durante la carga inicial para garantizar el render instantáneo de nodos y aristas; la inyección de sprites 3D se activa de manera diferida (2.5 s) una vez estabilizada la simulación de fuerzas físicas.
     - **Verificación**: Validación integral y automatizada de dependencias, datos `rawGraph` embebidos y controladores de eventos.

### Fase 8: Expansión Ontológica Integral (Multicolinealidad, Gauss-Markov, Endogeneidad, SUTVA, RDD, Heckman y Raíz Unitaria)
76. **Solicitud**: `"revisando el grafico veo que la ontologia no contiene elementos como MULTICOLINEALIDAD puedes revisar porque tenemos elementos tan importantes ausentes? La ontologia no puede presentar este tipo de omisiones"`
   - *Diagnóstico*: La ontología inicial se había estructurado trazando de forma vertical los marcos teóricos avanzados, omitiendo pilares epistemológicos fundamentales de la econometría clásica (Gauss-Markov), diagnósticos de colinealidad en R, supuestos de identificación causal de Rubin y diseños cuasiexperimentales.
   - *Solución Técnica e Implementación*:
     - **20 Nuevas Entidades Canónicas**:
       - *Conceptos*: `concept_multicollinearity` (Multicolinealidad), `concept_endogeneity` (Endogeneidad), `concept_selection_bias` (Sesgo de Selección), `concept_unit_root` (Raíz Unitaria).
       - *Supuestos*: `assumption_no_multicollinearity` (No Multicolinealidad Perfecta / Gauss-Markov), `assumption_sutva` (SUTVA de Rubin), `assumption_instrument_relevance` (Relevancia $F > 10$), `assumption_exclusion_restriction` (Restricción de Exclusión).
       - *Métodos*: `method_rdd` (Regression Discontinuity Design), `method_heckman` (Modelo de Selección de Heckman / Heckit), `method_aipw` (Augmented IPTW / Doblemente Robusto).
       - *Paquetes R*: `rpkg_car` (Companion to Applied Regression), `rpkg_rdrobust` (Inferencia RDD), `rpkg_sampleselection` (sampleSelection).
       - *Funciones R*: `rfunc_vif` (`vif()`), `rfunc_resettest` (`resettest()`), `rfunc_rdrobust` (`rdrobust()`), `rfunc_heckit` (`heckit()`), `rfunc_adf_test` (`adf.test()`), `rfunc_kpss_test` (`kpss.test()`).
     - **Relaciones y Red**: Se generaron 46 nuevas aristas relacionales (`requires`, `evaluates`, `adjusts_for`, `implemented_in_r_package`, `uses_r_function`, `part_of`).
     - **Auditoría Estricta**: **118 entidades, 182 relaciones, 0 errores de esquema, 0 nodos aislados**.
     - **Sincronización Total**: Dataset `rawGraph` inyectado y sincronizado en `graph_visualization.html` (2D) y `graph_visualization_3d.html` (3D).

---

## 3. Arquitectura Ontológica Actual

### A. Tipos de Entidades (`schema.yaml`)
1. **`Framework` (5)**:
   - `framework_potential_outcomes` (Neyman-Rubin)
   - `framework_dags` (Pearl)
   - `framework_microeconometrics` (Wooldridge)
   - `framework_spatial_econometrics` (Anselin)
   - `framework_time_series` (Box-Jenkins / Cryer & Chan)
2. **`Method` (27)**: `OLS`, `Fixed Effects`, `Random Effects`, `IV/2SLS`, `IPTW`, `G-computation`, `PS Matching`, `MSM`, `DiD`, `AIPW / Doubly Robust`, `RDD (Regression Discontinuity)`, `Heckman Selection (Heckit)`, `VAR`, `ARIMA`, `GARCH`, `Poisson`, `Tobit`, `Logit`, `Probit`, `Ordinal Logit`, `Multinomial Logit`, `SAR`, `SEM`, `SUR`, `GMM`, `Dynamic Panel GMM`, `Moderación`.
3. **`Concept` (20)**: `Multicollinearity`, `Endogeneity`, `Selection Bias`, `Unit Root (I(1))`, `Confounder`, `Collider`, `Mediator`, `Omitted Variable Bias`, `Serial Correlation`, `Heteroscedasticity`, `Stationarity`, `Cointegration`, `Spatial Autocorrelation`, `Spatial Spillover`, `Binary Outcome`, `Ordered Categorical Scale`, `Nominal Multi-Category`, `Overdispersion`, `Time-Invariant Confounding`, `Sequential Exogeneity`.
4. **`Assumption` (9)**: `No Perfect Multicollinearity (Gauss-Markov)`, `Strict Exogeneity`, `Conditional Ignorability`, `Positivity / Overlap`, `Parallel Trends`, `Homoscedasticity Gauss-Markov`, `SUTVA`, `Instrument Relevance`, `Exclusion Restriction`.
5. **`RPackage` (22)**: `stats`, `car`, `rdrobust`, `sampleSelection`, `survey`, `dagitty`, `MatchIt`, `mediation`, `AER`, `plm`, `sandwich`, `lmtest`, `sf`, `spdep`, `spatialreg`, `vars`, `tseries`, `TSA`, `systemfit`, `gmm`, `MASS`, `nnet`.
6. **`RFunction` (35)**: `vif()`, `resettest()`, `rdrobust()`, `heckit()`, `adf.test()`, `kpss.test()`, `glm()`, `svyglm()`, `matchit()`, `mediate()`, `ivreg()`, `adjustmentSets()`, `dispersiontest()`, `tobit()`, `arima()`, `eacf()`, `garch()`, `VAR()`, `causality()`, `plm()`, `coeftest()`, `dwtest()`, `bptest()`, `vcovHAC()`, `phtest()`, `pgmm()`, `moran.test()`, `nb2listw()`, `st_read()`, `lagsarlm()`, `errorsarlm()`, `systemfit()`, `gmm()`, `polr()`, `multinom()`.

### B. Relaciones Válidas (`schema.yaml`)
- `requires`: [Method, Framework] $\rightarrow$ [Assumption, Concept]
- `adjusts_for`: [Method] $\rightarrow$ [Concept]
- `produces_bias_if_adjusted`: [Method] $\rightarrow$ [Concept]
- `evaluates`: [RFunction, Method] $\rightarrow$ [Assumption, Concept]
- `alternative_to`: [Method] $\rightarrow$ [Method]
- `implemented_in_r_package`: [Method, RFunction] $\rightarrow$ [RPackage]
- `uses_r_function`: [Method] $\rightarrow$ [RFunction]
- `part_of`: [Concept, Method, Assumption, RPackage, RFunction] $\rightarrow$ [Framework, Concept]

---

### Fase 10: Auditoría Neuroquirúrgica, Indexación de Datasets Canónicos, Sintaxis en R y Referencias Bibliográficas
78. **Solicitud**: `"estas seguro que esos son los unicos faltantes? Realiza una segunda validacion para estar seguros que no hay faltantes. Insisto, en esta fase debemos ser tan precisos como un neurocirujano. Hay elementos como los ejemplos en R, tablas de estimaciones que deberíamos tambien indexar y hacer parte de nuestra ontología..."`
   - *Diagnóstico*: La auditoría inicial omitía métodos nucleares descubiertos al inspeccionar la totalidad de los 7 PDFs (`pypdfium2`), así como los datasets empíricos que dan origen a las tablas de estimaciones canónicas de los libros y la referencia exacta de capítulo y páginas.
   - *Solución Técnica Aplicada*:
     - **Extensión del Esquema (`schema.yaml`)**:
       - Nuevo tipo de entidad: `Dataset` (requiere `name`, `package`, `description`, `reference`).
       - Nuevas propiedades transversales: `reference` (`book`, `chapter`, `pages`), `r_syntax`, `dataset` e `interpretation_guide`.
       - Nuevo predicado relacional: `uses_dataset` (`[Method, RFunction] -> [Dataset]`).
     - **Indexación de 10 Datasets Canónicos**: `CASchools` (AER), `CigarettesSW` (AER), `Fatalities` (AER), `HMDA` (AER), `mroz` (sampleSelection), `jtrain` (wooldridge), `card` (wooldridge), `columbus` (spdep), `oilfilters` (TSA), `cref` (TSA).
     - **Enriquecimiento Textual y Teórico Total**: Cada uno de los 133 nodos cuenta ahora con su libro, capítulo y páginas exactas, sintaxis ejecutable en R y guía de interpretación del coeficiente/estadístico.
     - **Auditoría Maestra**: **133 entidades, 234 relaciones, 0 errores de esquema, 0 nodos aislados**.
     - **Sincronización de Interfaces**: Visualizadores 2D (`graph_visualization.html`) y 3D (`graph_visualization_3d.html`) actualizados con renderizado de tarjetas bibliográficas, bloques de código en R e interpretación.

### Fase 11: Corrección de Transmutación de Enlaces WebGL y Restauración de Detalles en 3D
79. **Solicitud**: `"tenemos el mismo problema de antes con la visualizacion 3D no se muestran los detalles"`
   - *Diagnóstico*: En la visualización 3D, el motor WebGL `3d-force-graph` transmuta las referencias `source` y `target` (y `from`/`to`) de strings a objetos de nodo completos `{ id: "...", x, y, z }` durante la simulación de fuerzas. Al hacer comparaciones estrictas (`e.from === nodeId`), la función `showDetails()` fallaba en resolver las relaciones e interrumpía la actualización del panel lateral.
   - *Solución Técnica Aplicada*:
     - **Función Normalizadora `getEndpointId(endpoint)`**: Extrae de forma segura el ID inmutable (`endpoint.id` si es objeto o el string primitivo si no ha mutado).
     - **Renderizado Robusto de `showDetails()`**: Protección de selectores DOM contra valores nulos/indefinidos y renderizado completo de Citas Bibliográficas, Código R, Datasets, Interpretación y chips de relaciones interactivas.
     - **Tooltip Flotante Neón (`nodeLabel`)**: Inyección de tarjetas glassmorphism en el espacio 3D al pasar el cursor sobre las esferas.
     - **Verificación**: Comprobación de selectores e integridad de carga al 100%.

### Fase 12: Barra de Búsqueda Reactiva con Dropdown en Vivo, Textos Dinámicos Expansibles y Modo de Fijación (Pin/Lock)
80. **Solicitud**: `"ya funciona, pero antes era posible buscar un tema con la barra navegadora, ahora no está disponible. Adicionalmente los espacios para el texto deben ser dinamicos para evitar que se trunque el texto que se está mostrando. Adicionalmente es importante que el usuario pueda FIJAR el texto para evitar que se mueva mientras navega el grafo"`
   - *Diagnóstico*: El menú desplegable de sugerencias sufría de recorte por el scroll general (`overflow-y: auto`) del sidebar. Asimismo, el modo de fijación no bloqueaba los eventos de clic en el espacio 3D, y se requerían contenedores elásticos sin límites de longitud.
   - *Solución Técnica Aplicada*:
     - **Arquitectura de Panel Dividida (`.sidebar-top-sticky` + `.sidebar-scrollable`)**: La barra de búsqueda se aloja en un contenedor superior fijo e independiente con `z-index: 1000`, permitiendo que el `#search-dropdown` flote libremente sobre la pantalla sin ser recortado.
     - **Dropdown de Búsqueda Reactiva (133 entidades)**: Búsqueda instantánea por Nombre, Concepto, Definición, Libro, Capítulo y Dataset con badges coloreados y selección por clic / <kbd>Enter</kbd>.
     - **Modo Fijar / Lock Estricto (`isPinned`)**: El botón `📌 Fijar` / `🔒 Bloqueado` previene cualquier cambio accidental en el `#details-card` al orbitar, rotar o hacer clic en la escena 3D.
     - **Renderizado Dinámico sin Truncamiento**: Textos con `word-break: break-word` y `white-space: pre-wrap` para lectura integral.
     - **Sincronización Total**: Implementado y verificado en `graph_visualization_3d.html` (3D) y `graph_visualization.html` (2D).

### Fase 13: Instalación de Extensiones para Renderizado LaTeX/KaTeX y Estandarización Notacional
81. **Solicitud**: `"debes instalar algun componente en el editor para que los fragmentos de LATEX se rendericen adecuadamente en tus respuestas, ahora se ven como codigo, no como ecuaciones por ejemplo..."`
   - *Diagnóstico*: El entorno del editor no contaba con motores de renderizado KaTeX para la previsualización de ecuaciones matemáticas en documentos `.md`. Asimismo, en la ventana de chat, el código LaTeX crudo (`\frac`, `\text`) genera ruido visual si el cliente Markdown no lo interpreta nativamente.
   - *Solución Técnica Aplicada*:
     - **Instalación de Extensiones en el Editor**: Instaladas con éxito `goessner.mdmath` (v2.7.4) y `yzhang.markdown-all-in-one` (v3.6.3).
     - **Estandarización Notacional en Chat**: Presentación de fórmulas con notación tipográfica Unicode de alta legibilidad (ej: `Var(β̂_j) = σ² / [SST_j · (1 - R_j²)]`) para visualización instantánea y limpia sin código LaTeX crudo en el chat, preservando KaTeX en reportes y documentos HTML.

### Fase 14: Integración de MIT 14.387 (Applied Econometrics: Mostly Harmless Big Data - Angrist & Chernozhukov)
82. **Solicitud**: `"comencemos por 14.387 / Applied Econometrics: Mostly Harmless Big Data"`
   - *Diagnóstico*: La ontología carecía de la formulación de frontera de posgrado del MIT sobre efectos de tratamiento heterogéneos (LATE, supuestos de monotonía, compliers) y econometría de alta dimensión / Big Data (Double/Debiased ML, Ortogonalidad de Neyman, Post-Double-Selection Lasso, Cross-Fitting).
   - *Solución Técnica Aplicada*:
     - **22 Nuevas Entidades Canónicas de Posgrado**:
       - *Framework (1)*: `framework_mostly_harmless_bigdata` (MIT 14.387 - Angrist & Chernozhukov).
       - *Datasets (3)*: `dataset_ak91` (Angrist & Krueger 1991 - QOB en Censo 1980), `dataset_401k` (Chernozhukov & Hansen 2004 - 401(k) en SIPP), `dataset_penn46` (Pennsylvania Reemployment Bonus Experiment).
       - *Métodos (4)*: `method_late_wald` (LATE / Estimador Wald de Angrist & Imbens), `method_double_ml` (Double/Debiased Machine Learning), `method_post_lasso` (Post-Double-Selection Lasso), `method_fuzzy_rdd` (Fuzzy RDD).
       - *Conceptos (5)*: `concept_late` (Local Average Treatment Effect), `concept_complier` (Compliers / Always-Takers / Never-Takers / Defiers), `concept_neyman_orthogonality` (Ortogonalidad de Neyman), `concept_cross_fitting` (Sample Splitting & K-Fold Cross-Fitting), `concept_regularization_bias` (Sesgo de Regularización).
       - *Supuestos (2)*: `assumption_monotonicity` (Monotonía / No-Defiers), `assumption_neyman_orthogonality` (Ortogonalidad del Score Causal).
       - *Paquetes R (3)*: `rpkg_hdm` (High-Dimensional Metrics), `rpkg_doubleml` (DoubleML), `rpkg_estimatr` (estimatr).
       - *Funciones R (4)*: `rfunc_rlasso` (`rlasso()`), `rfunc_rlasso_iv` (`rlassoIV()`), `rfunc_double_ml_plr` (`DoubleMLPLR$new()`), `rfunc_iv_robust` (`iv_robust()`).
     - **59 Nuevas Relaciones Relacionales**: Interconexiones completas (`part_of`, `requires`, `adjusts_for`, `alternative_to`, `uses_r_function`, `implemented_in_r_package`, `uses_dataset`, `evaluates`).
     - **Agente Especialista Creado**: `.agents/skills/mit-applied-econometrics-agent/SKILL.md` con directrices metodológicas completas para LATE, DML, cross-fitting y Post-Lasso en R.
     - **Auditoría Maestra**: **155 entidades, 293 relaciones, 0 errores de esquema, 0 nodos aislados**.
     - **Sincronización Total de Visualizadores**: Inyección de `rawGraph` actualizada en `graph_visualization.html` (2D) y `graph_visualization_3d.html` (3D), con nuevos botones de filtro, clusters temáticos y leyendas dinámicas.

### Fase 15: Integración de MIT 14.382 (Econometrics Graduate Core & Semiparametric Theory - Victor Chernozhukov)
83. **Solicitud**: `"procedamos con el siguiente curso"`
   - *Diagnóstico*: La ontología requería la teoría nuclear de posgrado en estimadores de M, análisis contrafáctico y regresión de distribución (Chernozhukov, Fernández-Val & Melly 2013), regresión cuantílica de Koenker, GMM no lineal con ecuaciones de Euler (Hansen-Singleton) y métodos de remuestreo robustos (Wild Cluster Bootstrap) para resolver problemas de pocos clusters y parámetros incidentales.
   - *Solución Técnica Aplicada*:
     - **22 Nuevas Entidades Canónicas**:
       - *Framework (1)*: `framework_graduate_econometrics_core` (MIT 14.382 - Chernozhukov).
       - *Datasets (3)*: `dataset_growth` (Barro-Lee 1994), `dataset_fish` (Katherine Graddy 1995 Fulton Fish Market), `dataset_gun_violence` (Ayres & Donohue 2003 Guns panel).
       - *Métodos (4)*: `method_distribution_regression` (Distribution Regression & Counterfactuals), `method_quantile_regression` (Regresión Cuantílica), `method_nonlinear_gmm` (Nonlinear GMM & Euler Equations), `method_liml_jive` (LIML / JIVE para muchos instrumentos débiles).
       - *Conceptos (5)*: `concept_counterfactual_distribution`, `concept_m_estimation`, `concept_wild_bootstrap`, `concept_incidental_parameters` (Neyman-Scott), `concept_simultaneous_inference` (Romano-Wolf / FWER).
       - *Supuestos (2)*: `assumption_gmm_identification` (Identificación Global GMM), `assumption_quantile_monotonicity` (Monotonía Estricta de Cuantiles).
       - *Paquetes R (3)*: `rpkg_quantreg`, `rpkg_counterfactual`, `rpkg_fwildclusterboot`.
       - *Funciones R (4)*: `rfunc_rq` (`rq()`), `rfunc_counterfactual` (`counterfactual()`), `rfunc_gmm_nonlinear` (`gmm()` no lineal), `rfunc_boottest` (`boottest()`).
     - **54 Nuevas Relaciones Relacionales**: Interconexiones completas (`part_of`, `requires`, `adjusts_for`, `alternative_to`, `uses_r_function`, `implemented_in_r_package`, `uses_dataset`, `evaluates`).
     - **Agente Especialista Actualizado**: `.agents/skills/mit-applied-econometrics-agent/SKILL.md` enriquecido con directrices para M-Estimation, cuantiles, descomposición contrafáctica y wild bootstrap.
     - **Auditoría Maestra**: **177 entidades, 347 relaciones, 0 errores de esquema, 0 nodos aislados**.
     - **Sincronización Total**: Dataset `rawGraph` actualizado en `graph_visualization.html` (2D) y `graph_visualization_3d.html` (3D), con nuevos botones temáticos `🏛️ MIT 14.382 Core` y `⚡ MIT 14.387 Big Data`.

### Fase 16: Integración de MIT 14.384 (Time Series Analysis & Macroeconometrics - Anna Mikusheva)
84. **Solicitud**: `"perfecto avancemos con el 3er curso"`
   - *Diagnóstico*: La ontología en series de tiempo requería la formalización de frontera macroeconométrica del MIT en Vectores Autorregresivos Estructurales (SVAR), identificación de shocks económicos primitivos (Sims / Blanchard-Quah / Proxy-SVAR), Cointegración Multivariada de Johansen (VECM), Modelos de Estado-Espacio con Filtro de Kalman recursivo (KFAS) y Modelos de Factores Dinámicos en alta dimensión (Stock-Watson / Bai-Ng).
   - *Solución Técnica Aplicada*:
     - **22 Nuevas Entidades Canónicas**:
       - *Framework (1)*: `framework_graduate_time_series` (MIT 14.384 - Mikusheva).
       - *Datasets (3)*: `dataset_us_macro_sw` (Stock & Watson / urca), `dataset_oil_shocks` (Kilian 2009 / AER), `dataset_monetary_shocks` (Gertler & Karadi 2015 / AER).
       - *Métodos (4)*: `method_svar_identification` (SVAR y Shocks Estructurales), `method_vecm_johansen` (VECM y Johansen MLE), `method_kalman_filter` (Filtro de Kalman en Estado-Espacio), `method_factor_models_ts` (Dynamic Factor Models).
       - *Conceptos (5)*: `concept_structural_shock`, `concept_irf_fevd` (IRF y FEVD), `concept_johansen_cointegration`, `concept_state_space_kalman`, `concept_wold_decomposition`.
       - *Supuestos (2)*: `assumption_svar_orthogonality`, `assumption_cointegrating_rank`.
       - *Paquetes R (3)*: `rpkg_urca`, `rpkg_kfas`, `rpkg_svars`.
       - *Funciones R (4)*: `rfunc_svar` (`SVAR()`), `rfunc_cajo` (`ca.jo()`), `rfunc_kfas_filter` (`KFS()`), `rfunc_irf_bootstrap` (`irf()`).
     - **52 Nuevas Relaciones Relacionales**: Interconexiones completas (`part_of`, `requires`, `adjusts_for`, `alternative_to`, `uses_r_function`, `implemented_in_r_package`, `uses_dataset`, `evaluates`).
     - **Agente Especialista Actualizado**: `.agents/skills/time-series-agent/SKILL.md` enriquecido para unificar el texto de Cryer & Chan con la macroeconometría estructural de MIT 14.384.
     - **Auditoría Maestra**: **199 entidades, 399 relaciones, 0 errores de esquema, 0 nodos aislados**.
     - **Sincronización Total de Visualizadores**: Inyección de `rawGraph` en `graph_visualization.html` (2D) y `graph_visualization_3d.html` (3D), con nuevos botones temáticos `📈 MIT 14.384 Series`, `🏛️ MIT 14.382 Core` y `⚡ MIT 14.387 Big Data`.

---

## 3. Arquitectura Ontológica Actual

### A. Tipos de Entidades (`schema.yaml`)
1. **`Framework` (8)**: `Potential Outcomes (Neyman-Rubin)`, `DAGs (Pearl)`, `Microeconometría (Wooldridge)`, `Econometría Espacial (Anselin/Bivand)`, `Series de Tiempo (Cryer & Chan)`, `Applied Econometrics & Big Data (MIT 14.387 - Angrist & Chernozhukov)`, `Graduate Econometrics Core (MIT 14.382 - Chernozhukov)`, `Graduate Time Series & Macroeconometrics (MIT 14.384 - Mikusheva)`.
2. **`Dataset` (19)**: `CASchools`, `CigarettesSW`, `Fatalities`, `HMDA`, `mroz`, `jtrain`, `card`, `columbus`, `oilfilters`, `cref`, `ak91`, `401k`, `penn46`, `growth`, `fish`, `gun_violence`, `us_macro_sw`, `oil_shocks`, `monetary_shocks`.
3. **`Method` (40)**: `OLS`, `IV/2SLS`, `Fixed Effects`, `Random Effects`, `Dynamic Panel GMM`, `Differences-in-Differences`, `RDD`, `Heckman Selection`, `Tobit`, `Poisson`, `Logit`, `Probit`, `Ordinal Logit`, `Multinomial Logit`, `IPTW`, `AIPW`, `G-computation`, `PS Matching`, `MSM`, `Front-Door Method`, `ARIMA`, `GARCH`, `VAR`, `Spatial Lag (SAR)`, `Spatial Error (SEM)`, `Spatial Durbin (SDM)`, `SUR`, `GMM`, `LATE (Wald)`, `Double/Debiased ML`, `Post-Double-Selection Lasso`, `Fuzzy RDD`, `Distribution Regression`, `Quantile Regression`, `Nonlinear GMM (Euler)`, `LIML & JIVE`, `SVAR Identification`, `VECM Johansen`, `Kalman Filter & State-Space`, `Dynamic Factor Models`.
4. **`Concept` (37)**: `Multicollinearity`, `Endogeneity`, `Confounder`, `Collider`, `Mediator`, `Selection Bias`, `Omitted Variable Bias`, `Heteroscedasticity`, `Serial Correlation`, `Stationarity`, `Unit Root (I(1))`, `Cointegration`, `Spatial Autocorrelation`, `Spatial Spillover`, `Time-Invariant Confounding`, `Sequential Exogeneity`, `Overdispersion`, `Binary Outcome`, `Ordered Categorical Scale`, `Nominal Multi-Category`, `Effect Modification`, `Precision Variable`, `Local Average Treatment Effect (LATE)`, `Compliers Typology`, `Neyman Orthogonality`, `Cross-Fitting K-Fold`, `Regularization Bias`, `Counterfactual Distribution`, `M-Estimation`, `Wild Cluster Bootstrap`, `Incidental Parameters Problem`, `Simultaneous Inference`, `Structural Shock`, `IRF & FEVD`, `Johansen Cointegrating Rank`, `State-Space Representation`, `Wold Decomposition Theorem`.
5. **`Assumption` (16)**: `Homoscedasticity Gauss-Markov`, `No Perfect Multicollinearity`, `Strict Exogeneity`, `Parallel Trends`, `Positivity / Overlap`, `Conditional Ignorability`, `SUTVA`, `Instrument Relevance`, `Exclusion Restriction`, `Stationarity / Unit Root Absence`, `Monotonicity (No-Defiers)`, `Neyman Orthogonality of Score`, `GMM Global Identification`, `Strict Quantile Monotonicity`, `SVAR Structural Orthogonality`, `Cointegrating Rank Condition`.
6. **`RPackage` (31)**: `stats`, `car`, `lmtest`, `sandwich`, `AER`, `plm`, `sampleSelection`, `rdrobust`, `survey`, `dagitty`, `MatchIt`, `mediation`, `TSA`, `vars`, `tseries`, `sf`, `spdep`, `spatialreg`, `systemfit`, `gmm`, `MASS`, `nnet`, `hdm`, `DoubleML`, `estimatr`, `quantreg`, `Counterfactual`, `fwildclusterboot`, `urca`, `KFAS`, `svars`.
7. **`RFunction` (48)**: `vif()`, `resettest()`, `bptest()`, `dwtest()`, `coeftest()`, `vcovHAC()`, `ivreg()`, `tobit()`, `dispersiontest()`, `heckit()`, `rdrobust()`, `plm()`, `phtest()`, `pgmm()`, `adf.test()`, `kpss.test()`, `arima()`, `eacf()`, `garch()`, `VAR()`, `causality()`, `st_read()`, `nb2listw()`, `moran.test()`, `localmoran()`, `lagsarlm()`, `errorsarlm()`, `svyglm()`, `matchit()`, `mediate()`, `adjustmentSets()`, `glm()`, `polr()`, `multinom()`, `systemfit()`, `gmm()`, `rlasso()`, `rlassoIV()`, `DoubleMLPLR$new()`, `iv_robust()`, `rq()`, `counterfactual()`, `gmm() [Nonlinear]`, `boottest()`, `SVAR()`, `ca.jo()`, `KFS()`, `irf() [Bootstrap]`.

### B. Relaciones Válidas (`schema.yaml`)
- `requires`: [Method, Framework] $\rightarrow$ [Assumption, Concept]
- `adjusts_for`: [Method] $\rightarrow$ [Concept]
- `produces_bias_if_adjusted`: [Method] $\rightarrow$ [Concept]
- `evaluates`: [RFunction, Method] $\rightarrow$ [Assumption, Concept]
- `alternative_to`: [Method] $\rightarrow$ [Method]
- `implemented_in_r_package`: [Method, RFunction, Dataset] $\rightarrow$ [RPackage]
- `uses_r_function`: [Method] $\rightarrow$ [RFunction]
- `uses_dataset`: [Method, RFunction] $\rightarrow$ [Dataset]
- `part_of`: [Concept, Method, Assumption, RPackage, RFunction, Dataset] $\rightarrow$ [Framework, Concept]

---

## 4. Estado de los Archivos del Proyecto

| Archivo / Directorio | Propósito | Estado |
|---|---|---|
| `memory/ontology/schema.yaml` | Reglas formales de tipado (incluye Dataset, reference, r_syntax, interpretation_guide). | Validado y al día |
| `memory/ontology/graph.jsonl` | Grafo de conocimiento con **199 entidades y 399 relaciones (0 nodos aislados)**. | Validado y al día |
| `memory/ontology/graph_visualization.html` | Visualizador 2D en Vis.js con estética nórdica/grafito, panel de citas bibliográficas, código R y datasets. | 100% Sincronizado (199 nodos / 399 aristas) |
| `memory/ontology/graph_visualization_3d.html` | Visualizador 3D WebGL (Three.js) con estética Cyber, panel de citas bibliográficas, código R, datasets y botones temáticos MIT. | 100% Sincronizado (199 nodos / 399 aristas) |
| `.agents/rules/shared_ontology.md` | Regla global de compartición ontológica unificada para todos los agentes (8 agentes registrados). | Activo |
| `.agents/skills/` (8 carpetas) | 8 agentes especialistas instanciados por libro y cursos de posgrado MIT con directrices y funciones en R. | Activos y Operativos |

---

## 5. Instrucciones para la Continuación con Otro Modelo

Al reanudar o transferir esta tarea a un nuevo modelo:
1. **Regla de Cero CORS**: Todos los archivos HTML de visualización deben ser 100% autónomos (*self-contained*). Inyectar el dataset `rawGraph` dentro del script.
2. **Sincronización Bidireccional**: Cualquier adición a `memory/ontology/graph.jsonl` debe cumplir con `memory/ontology/schema.yaml` y propagarse tanto a `graph_visualization.html` (2D) como a `graph_visualization_3d.html` (3D).
3. **Estándar de Rigor Bibliográfico**: Toda nueva entidad debe incluir su campo `reference` con `book`, `chapter` y `pages`, y en caso de métodos o funciones, `r_syntax`, `dataset` e `interpretation_guide`.




---

## Sesión 2026-08-19 — Diseño Arquitectural: Integración de la Ontología con NEVEN

**Participantes:** Minor Bonilla Gómez + Kiro (Claude Sonnet 4.6)  
**Duración:** Sesión de diseño conceptual — sin cambios de código  
**Naturaleza:** Decisiones arquitecturales de alto nivel. Todo lo aquí documentado define el rumbo del proyecto a futuro.

---

### Decisión 1 — La ontología es el CEREBRO de NEVEN

**Planteamiento original de Minor:**
> "NEVEN es una MÁQUINA que computa. La ontología será el CEREBRO que orienta la modelación de los datos que ocurrirá en NEVEN. Le estamos dando un cerebro de posgrado a nuestra máquina."

**Validación arquitectural:**
La separación motor computacional (NEVEN) / capa de razonamiento (ontología) es correcta y defendible. No mezcla "qué se computa" con "qué debería computarse". El grafo con relaciones semánticas explícitas (`requires`, `adjusts_for`, `produces_bias_if_adjusted`) ya tiene el esqueleto de un motor de razonamiento — no es solo una base de datos de métodos.

**Consecuencia de diseño:** La ontología no es un catálogo estático. Es un sistema de razonamiento que se consulta en tiempo de ejecución para orientar decisiones metodológicas.

---

### Decisión 2 — Flujo unificado para usuarios expertos y legos

**Planteamiento:**
Ambos tipos de usuario enfrentan la misma estructura de problema:

```
PREGUNTA → PLANTEO → OPERACION → RESPUESTA
```

- **PREGUNTA**: el usuario tiene un problema que busca resolver con evidencia cuantitativa
- **PLANTEO**: el usuario ya tiene los datos, pero no sabe cómo operarlos
- **OPERACION**: donde participan la ontología (razonamiento) y NEVEN (ejecución)
- **RESPUESTA**: el usuario ofrece evidencia basada en resultados cuantitativos

Lo que varía entre experto y lego es el grado de comprensión técnica en la capa de OPERACION, no la estructura del flujo. Un solo pipeline, dos configuraciones de profundidad de presentación.

**Modelo de interacción elegido: Modo A**
El usuario interactúa con un motor de IA (LLM) que consulta la ontología para orientar el plan metodológico. El LLM traduce lenguaje natural a nodos del grafo, independientemente del nivel técnico del usuario.

---

### Decisión 3 — OPERACION se divide en dos subfases explícitas

```
OPERACION = DIAGNÓSTICO METODOLÓGICO + EJECUCIÓN
```

**Diagnóstico metodológico** (la ontología trabaja aquí):
- Evalúa simultáneamente: la pregunta del usuario + la estructura de los datos + las relaciones del grafo
- Produce un **plan metodológico** antes de ejecutar nada
- El plan es visible y aprobable por el usuario antes de ejecutar

**Ejecución** (NEVEN trabaja aquí):
- Verificación de supuestos
- Estimación del modelo
- Tests diagnósticos post-estimación

El plan metodológico es lo que hace auditable el proceso — no es una caja negra que produce resultados, es un sistema que razona explícitamente sobre qué método usar y por qué.

---

### Decisión 4 — Las advertencias son educación, no bloqueos

**Planteamiento de Minor:**
> "La ontología debe responder con la opción 1: realizar una advertencia explícita sobre las limitaciones de forma que sea el usuario el que decida si mejora o mantiene su planteamiento. La responsabilidad es del usuario, no de la herramienta."

**Consecuencia de diseño:** Las advertencias no son mensajes de error. Son conocimiento de la ontología expuesto al usuario. Cuando la ontología advierte sobre un instrumento débil (F < 10), está usando exactamente el contenido del nodo `assumption_instrument_relevance` del grafo.

**Estructura de advertencia en dos niveles:**

**Nivel compacto** (siempre visible):
```
⚠ Heterocedasticidad detectada — errores estándar corregidos con HC1. Ver Hanck Cap. 5
```

**Nivel expandido** (al hacer clic — orientado a comprensión, no solo información):
1. **El fenómeno** — qué está pasando en los datos del usuario (lenguaje accesible)
2. **La implicación** — por qué importa para la respuesta que busca (específica, no genérica)
3. **Lo que NEVEN hará** — la acción correctiva explicada
4. **La referencia** — libro, capítulo, páginas, con una frase que haga la referencia apetecible
5. **Una pregunta de reflexión** — invita al usuario a pensar antes de continuar

La pregunta de reflexión es la capa más importante: no pregunta si sabe econometría, pregunta si comprende su propio problema.

---

### Decisión 5 — El lema del proyecto

> **"Nos interesa más la comprensión que el uso mismo."**

**Consecuencias de diseño concretas:**

- El plan metodológico es una **narrativa** que explica el razonamiento, no una lista técnica de pasos
- Las advertencias expandidas tienen estructura pedagógica con 5 capas (ver arriba)
- El nivel de detalle de la presentación es **configurable por el usuario** (perfil experto/lego autodeclarado), devolviendo la responsabilidad al usuario y reconociendo el riesgo del efecto Dunning-Kruger
- El contenido subyacente es idéntico para ambos perfiles — solo varía la presentación

---

### Decisión 6 — Fuentes de datos unificadas en DuckDB

NEVEN ya tiene tres fuentes de datos que convergen en DuckDB:
1. **Excel** — acceso directo a celdas desde NEVEN Core
2. **CSV/archivos planos** — carga desde NEVEN Studio
3. **DB externa → DuckDB** — consultas SQL desde el tab SQL de NEVEN Studio

El diagnóstico metodológico puede **inspecionar directamente la estructura de los datos** sin que el usuario los describa manualmente. Lo que la capa de diagnóstico extrae:

| Dimensión | Para qué sirve |
|-----------|---------------|
| N filas, K columnas | Viabilidad de métodos con requisitos mínimos de muestra |
| Tipos de variables | Determinar familia de modelos (OLS, Logit, Poisson, POLR) |
| Dimensión temporal | Activa métodos de panel y series de tiempo |
| Dimensión espacial | Activa rama de econometría espacial |
| Valores faltantes | Advertencias sobre sesgo de selección y truncamiento |
| Distribución de variables clave | Verificación de supuestos antes de ejecutar |

Esto es un **perfil del dataset** — construible con una sola pasada DuckDB antes de consultar el grafo.

---

### Decisión 7 — Formato de proyecto persistente: archivo `.buklo`

**Planteamiento de Minor:**
> "El archivo .buklo contiene todos los datos e interacciones para que el usuario pueda levantarlo en otro momento."

**Especificación técnica acordada:**

Un `.buklo` es un ZIP con extensión propia que contiene:
- **Datos**: dataset exportado en formato Parquet (compresión ~10x respecto a CSV original)
- **Historia**: `CHAT.md` con todas las interacciones del usuario con el LLM
- **Plan**: `plan.json` con el plan metodológico final aprobado
- **Metadata**: `metadata.json` con versión de NEVEN, fecha, perfil del usuario

**Flujo de apertura:**
```
Abrir .buklo
  → descomprime en directorio temporal
  → importa Parquet a DuckDB (READ_PARQUET())
  → carga CHAT.md como contexto del LLM
  → presenta el plan metodológico del estado anterior
  → usuario retoma en segundos
```

**Nota técnica:** Parquet comprime mejor que DuckDB nativo, es portable entre versiones, y DuckDB lo lee directamente. Un CSV de 200MB → ~15-20MB en Parquet comprimido.

**Nota de producto:** Registrar la extensión `.buklo` en el instalador de NEVEN para que Windows la abra automáticamente con doble clic.

---

### Decisión 8 — Documentación oficial de paquetes R como capa de ejecución

**Planteamiento de Minor:**
> "Todas las librerías de R tienen la documentación de las funciones incorporadas en cada paquete. ¿Podemos incluir dentro de la ontología aquella documentación facilitada en las librerías de R nombradas tanto en los cursos del MIT como en los libros? Con esto tendríamos un hilo perfecto de conducción entre el concepto y la ejecución."

**Validación:** La idea cierra el último gap de la cadena pedagógica:

```
Concepto teórico (ontología)
    → Método estadístico (ontología)
        → Función R concreta (ontología, nodo RFunction)
            → Documentación técnica oficial (CRAN)  ← cierra el hilo
                → Ejecución en NEVEN
```

**Implementación acordada:**
- No almacenar el texto completo en el grafo (evita problemas de licencia y desactualización)
- Almacenar el **enlace canónico a CRAN** en el campo `official_docs.cran_url` del nodo `RFunction`
- Extraer el contenido en tiempo de ejecución cuando se necesita presentar al usuario
- Fuente: `https://cran.r-project.org/web/packages/<pkg>/<pkg>.pdf` — predecible y permanente

**Extensión del schema acordada:**
```yaml
RFunction:
  optional: [..., official_docs]  # nuevo campo

# official_docs estructura:
official_docs:
  arguments: [{name, type, description}]
  return_value: string
  see_also: [function_ids]
  examples: [string]
  cran_url: string
```

**La cadena pedagógica completa resultante:**
```
ADVERTENCIA COMPACTA → expandir →
ADVERTENCIA EXPANDIDA (5 capas) → "Ver función" →
DOCUMENTACIÓN TÉCNICA (CRAN, argumentos, ejemplos) → ejecutar →
NEVEN corre la función en ControlR
```

Ningún paso es una caja negra. El usuario puede seguir la cadena completa desde "¿qué pasó con mis datos?" hasta "¿qué hizo exactamente el software y por qué?".

---

### Decisión 9 — La ontología es un sistema abierto por diseño

**Planteamiento de Minor:**
> "Podemos permitir que nuestra ontología crezca en el tiempo si facilitamos adherir nuevos agentes y elementos a la ontología. Eso debemos dejarlo plasmado."

**Dominios candidatos identificados para expansión futura:**

| Dominio | Agente propuesto | Fuente sugerida |
|---------|-----------------|-----------------|
| Machine Learning predictivo | `ml-predictive-agent` | ISLR (James et al.) / ESL (Hastie et al.) |
| Análisis exploratorio de datos | `eda-agent` | R for Data Science (Wickham) |
| Estadística bayesiana | `bayesian-agent` | Statistical Rethinking (McElreath) |
| Evaluación de impacto / RCTs | `impact-evaluation-agent` | Running Randomized Evaluations (Glennerster) |
| Econometría financiera | `financial-econometrics-agent` | Tsay - Analysis of Financial Time Series |
| Text as data / NLP econométrico | `text-data-agent` | Gentzkow, Kelly & Taddy |

**Nota:** Esta lista no es exhaustiva ni obligatoria. Es una señal de que el sistema tiene dirección de crecimiento pensada. Ver `shared_ontology.md` para el protocolo formal de extensión.

---

### Estado al cierre de esta sesión

**Decisiones tomadas:** 9 decisiones arquitecturales documentadas  
**Código producido:** 0 (sesión de diseño puro)  
**Próximo paso inmediato:** Redactar el plan de integración formal de NEVEN con la ontología

**Pendientes que derivan de esta sesión:**
- [ ] Plan de integración NEVEN ↔ Ontología (arquitectura técnica detallada)
- [ ] Actualizar `shared_ontology.md` con principio de extensibilidad y protocolo de crecimiento
- [ ] Definir el schema de `metadata.json` del archivo `.buklo`
- [ ] Extender `schema.yaml` con el campo `official_docs` en `RFunction`
- [ ] Definir qué información mínima necesita el LLM del usuario en la fase de PLANTEO
- [ ] Diseñar el perfil de dataset (las queries DuckDB que generan el perfil automático)
