# Plan de Implementación: Diccionario de Funciones NEVEN

## Resumen

Crear un documento de referencia completo (`docs/DICCIONARIO_FUNCIONES.md`) que catalogue todas las funciones disponibles en NEVEN organizadas por lenguaje y categoría, con ejemplos ejecutables en Excel. Incluye la reorganización del directorio `libreria/` para incorporar subdirectorios PYTHON/ y QUARTO/.

## Tareas

- [x] 1. Reorganizar directorio `libreria/`
  - [x] 1.1 Crear subdirectorio `libreria/PYTHON/` y mover/crear archivos de funciones Python
    - Crear `libreria/PYTHON/ai_functions.py` con las funciones ai_call, ai_setup, ai_list_prompts (copiar desde `startup/startup.py` las funciones públicas AI)
    - Crear `libreria/PYTHON/quarto_functions.py` (copiar desde `Ejemplos/Python/quarto_functions.py`)
    - Crear `libreria/PYTHON/README.md` con descripción del contenido
    - _Requisitos: 1.1, 1.3_

  - [x] 1.2 Crear subdirectorio `libreria/QUARTO/` con archivos de ejemplo y documentación
    - Crear `libreria/QUARTO/ejemplo_basico.qmd` con un ejemplo mínimo de documento Quarto
    - Crear `libreria/QUARTO/README.md` con instrucciones de uso de Quarto desde Excel
    - _Requisitos: 1.2, 1.3_

- [x] 2. Crear estructura base del diccionario
  - [x] 2.1 Crear `docs/DICCIONARIO_FUNCIONES.md` con encabezado, metadatos y tabla de contenidos
    - Incluir fecha de última actualización y conteo total de funciones
    - Crear tabla de contenidos con enlaces internos a cada sección principal
    - Definir la plantilla uniforme para cada entrada de función (nombre Excel, descripción, parámetros, ejemplo, resultado)
    - Incluir sección introductoria explicando la convención de prefijos (R., J., P., NEVEN.)
    - _Requisitos: 2.1, 2.2, 2.3, 2.5, 9.1, 9.2_

- [x] 3. Documentar funciones R — Categoría Regresión
  - [x] 3.1 Documentar funciones de regresión: MR_Lineal, MR_Binaria, MR_Poisson, MR_Tobit, MR_DatosPanel, MR_SVM, MR_ArbolDecision
    - Leer cada archivo R4XCL-RG-*.R para extraer parámetros, TipoOutput y descripciones
    - Para cada función: nombre Excel (`=R.MR_Lineal(...)`), descripción, tabla de parámetros con tipos y defaults
    - Listar todos los valores de TipoOutput con su descripción (ej: 0=procedimientos, 1=modelo estimado, 2=predicción, etc.)
    - Incluir ejemplo con datos dummy embebidos y resultado esperado
    - _Requisitos: 3.1, 3.2, 7.1, 7.3, 7.4_

- [x] 4. Documentar funciones R — Categoría Análisis de Datos
  - [x] 4.1 Documentar funciones de análisis: AD_ACP, AD_KMedias, AD_NonParRolCor, AD_TextMining
    - Leer archivos R4XCL-AD-*.R (excluyendo interactivos)
    - Documentar parámetros, TipoOutput y ejemplos
    - _Requisitos: 3.1, 3.2, 7.1, 7.3, 7.4_

  - [x] 4.2 Documentar funciones R interactivas: Pivot, Esquisse, D3, Dashboard, Map
    - Leer archivos R4XCL-AD-Pivot.R, R4XCL-AD-Esquisse.R, R4XCL-AD-D3.R, R4XCL-AD-Dashboard.R, R4XCL-AD-Map.R
    - Documentar sintaxis de invocación via `=NEVEN.v(R.funcion(...))`
    - Indicar que estas funciones abren un visor HTML interactivo
    - _Requisitos: 3.1, 3.3, 7.1_

- [x] 5. Documentar funciones R — Categorías restantes
  - [x] 5.1 Documentar funciones de Series de Tiempo (R4XCL-RG-SeriesTiempo.R)
    - Extraer parámetros, TipoOutput y ejemplos
    - _Requisitos: 3.1, 3.2, 7.1, 7.3, 7.4_

  - [x] 5.2 Documentar funciones de Gráficos: Graficacion, Interactivos, Mapa, PlotlyView, QuickPlot
    - Leer archivos R4XCL-GR-*.R
    - Documentar parámetros y ejemplos
    - _Requisitos: 3.1, 7.1, 7.4_

  - [x] 5.3 Documentar funciones de Matemáticas y Álgebra Lineal (R4XCL-MT-AlgebraLineal.R)
    - Extraer parámetros, TipoOutput y ejemplos
    - _Requisitos: 3.1, 3.2, 7.1, 7.3, 7.4_

  - [x] 5.4 Documentar funciones Auxiliares: Aleatorios, Calculos, Pivote, Ayuda, InstalaPaqueterias
    - Leer archivos R4XCL-FX-*.R, R4XCL-UT-*.R, R4XCL-0-UT-*.R
    - Documentar parámetros y ejemplos
    - Indicar paquetes externos requeridos donde aplique
    - _Requisitos: 3.1, 3.4, 7.1, 7.4_

  - [x] 5.5 Documentar funciones de Datos: ObtieneDatos, Wooldridge
    - Leer archivos R4XCL-BD-*.R, R4XCL-DS-*.R
    - Documentar datasets disponibles y cómo accederlos
    - _Requisitos: 3.1, 7.1_

- [x] 6. Checkpoint — Verificar sección R completa
  - Verificar que todas las ~90 funciones R están documentadas
  - Verificar formato consistente en todas las entradas
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Documentar funciones Julia
  - [x] 7.1 Documentar módulo Álgebra (JM_Algebra → `=J.Algebra(...)`)
    - Leer functions.jl, sección MÓDULO 1
    - Documentar los 12 procedimientos (TipoOutput 1-12): LU, QR, SVD, valores propios, vectores propios, determinante, rango, normas, condición, pseudoinversa, traza, resolver Ax=b
    - Incluir ejemplo con matriz 3x3 dummy
    - _Requisitos: 4.1, 4.2, 4.3, 7.1, 7.3, 7.4_

  - [x] 7.2 Documentar módulo Cálculo (JM_Calculo → `=J.Calculo(...)`)
    - Leer functions.jl, sección MÓDULO 2
    - Documentar los 7 procedimientos: derivada numérica, integral trapecio, Simpson, bisección, interpolación lineal, Lagrange, Taylor
    - Incluir ejemplo con vectores X,Y dummy
    - _Requisitos: 4.1, 4.2, 4.3, 7.1, 7.3, 7.4_

  - [x] 7.3 Documentar módulo EDO (JM_EDO → `=J.EDO(...)`)
    - Leer functions.jl, sección MÓDULO 3
    - Documentar los 4 procedimientos: Euler, RK4, sistema EDOs, EDO 2do orden
    - Incluir ejemplo con intervalo [0,1] y condición inicial
    - _Requisitos: 4.1, 4.2, 4.3, 7.1, 7.3, 7.4_

  - [x] 7.4 Documentar módulo Estadística (JML_Estadistica → `=J.Estadistica(...)`)
    - Leer functions.jl, sección MÓDULO 6
    - Documentar los 8 procedimientos: descriptiva, correlación, covarianza, test t, MinMax, ZScore, percentiles, outliers IQR
    - Incluir ejemplo con datos numéricos dummy
    - _Requisitos: 4.1, 4.2, 4.3, 7.1, 7.3, 7.4_

  - [x] 7.5 Documentar módulo Clasificación/KNN (JML_Clasificacion → `=J.KNN(...)`)
    - Leer functions.jl, sección MÓDULO 4
    - Documentar los 6 procedimientos: KNN clasificación, regresión lineal, predicción, coeficientes+R², residuos, matriz de confusión
    - _Requisitos: 4.1, 4.2, 4.3, 7.1, 7.3, 7.4_

  - [x] 7.6 Documentar módulo Clustering (JML_Clustering → `=J.Clustering(...)`)
    - Leer functions.jl, sección MÓDULO 5
    - Documentar los 6 procedimientos: K-Medias completo, centros, asignación, WCSS, método del codo, descriptivas por cluster
    - _Requisitos: 4.1, 4.2, 4.3, 7.1, 7.3, 7.4_

  - [x] 7.7 Documentar módulo Optimización (JO_Optimizar → `=J.Optimizar(...)`)
    - Leer functions.jl, sección MÓDULO 7
    - Documentar los 7 procedimientos: descenso gradiente, momentum, Newton, sección áurea, simplex, NNLS, programación cuadrática
    - _Requisitos: 4.1, 4.2, 4.3, 7.1, 7.3, 7.4_

  - [x] 7.8 Documentar módulo Transformar (JC_Transformar → `=J.Transformar(...)`)
    - Leer functions.jl, sección MÓDULO 8
    - Documentar los 6 procedimientos: transponer, ordenar, filtrar, seleccionar columnas, valores únicos, frecuencias
    - _Requisitos: 4.1, 4.2, 4.3, 7.1, 7.3, 7.4_

  - [x] 7.9 Documentar módulo Conectividad y funciones adicionales de los archivos .jl separados
    - Leer J4XCL-CN-Conectividad.jl, J4XCL-ML-Aprendizaje.jl, J4XCL-MT-Matematicas.jl, J4XCL-OP-Optimizacion.jl
    - Documentar funciones adicionales no cubiertas en functions.jl
    - _Requisitos: 4.1, 4.2, 4.3, 7.1_

- [x] 8. Checkpoint — Verificar sección Julia completa
  - Verificar que todos los módulos Julia están documentados (~70 procedimientos)
  - Verificar consistencia de formato con sección R
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Documentar funciones Python y AI
  - [x] 9.1 Documentar función ai_call (`=P.ai_call(...)`)
    - Parámetros: data_str (rango de datos), prompt_name (nombre del template), context (contexto opcional)
    - Ejemplo: `=P.ai_call(A1:B10, "analizar", "datos de ventas Q1")`
    - Documentar prerrequisitos: neven-config.json con sección AI configurada, directorio de prompts
    - Documentar placeholders disponibles en templates: {{resultado}}, {{datos}}, {{contexto}}
    - _Requisitos: 5.1, 5.2, 5.4, 7.1, 7.4_

  - [x] 9.2 Documentar función ai_setup (`=P.ai_setup()`)
    - Sin parámetros, abre formulario de configuración en WebView2
    - Ejemplo: `=NEVEN.v(P.ai_setup())`
    - _Requisitos: 5.1, 5.4, 7.1_

  - [x] 9.3 Documentar función ai_list_prompts (`=P.ai_list_prompts()`)
    - Sin parámetros, retorna lista de prompts disponibles
    - Ejemplo: `=P.ai_list_prompts()`
    - _Requisitos: 5.1, 7.1_

  - [x] 9.4 Documentar función quarto_render (`=P.quarto_render(...)`)
    - Parámetros: file_path (ruta al .qmd), format (html/pdf/docx, default html)
    - Ejemplo: `=P.quarto_render("C:\Users\usuario\doc.qmd", "pdf")`
    - Indicar prerrequisito: Quarto CLI instalado
    - _Requisitos: 5.1, 5.3, 7.1, 7.4_

- [x] 10. Documentar funciones del Sistema
  - [x] 10.1 Documentar funciones de ejecución: NEVEN.r(), NEVEN.j(), NEVEN.v(), NEVEN.q()
    - NEVEN.r(expresión) — ejecuta expresión R y retorna resultado
    - NEVEN.j(expresión) — ejecuta expresión Julia y retorna resultado
    - NEVEN.v(expresión) — ejecuta y muestra resultado en visor HTML
    - NEVEN.q(ruta) — renderiza documento Quarto
    - Incluir ejemplo funcional para cada una
    - _Requisitos: 6.1, 6.2, 6.3, 7.1_

  - [x] 10.2 Documentar funciones Pluto: NEVEN.pluto.start(), .stop(), .status(), .data()
    - Documentar parámetros y flujo de uso (start → data → stop)
    - Incluir ejemplo de pipeline Excel→Pluto
    - _Requisitos: 6.1, 6.2, 6.3, 7.1_

  - [x] 10.3 Documentar funciones de utilidad: NEVEN.notebook.open(), .list(), NEVEN.editor(), NEVEN.about(), NEVEN.help()
    - Documentar parámetros donde aplique
    - Incluir ejemplo para cada función
    - _Requisitos: 6.1, 6.2, 6.3, 7.1_

- [x] 11. Crear índice cruzado por categoría
  - [x] 11.1 Crear sección de índice que agrupe funciones por categoría temática
    - Categorías: Regresión, Clasificación/ML, Clustering, Estadística Descriptiva, Series de Tiempo, Álgebra Lineal, Cálculo Numérico, Optimización, Visualización, Datos/Transformación, Utilidades, AI/LLM
    - Cada entrada con enlace interno a la documentación completa de la función
    - Incluir funciones de todos los lenguajes en cada categoría (ej: Regresión incluye R.MR_Lineal y J.KNN con TipoOutput=2)
    - _Requisitos: 8.1, 8.2_

- [x] 12. Revisión final y validación
  - [x] 12.1 Verificar completitud y consistencia del diccionario
    - Confirmar que el conteo total de funciones en el encabezado es correcto
    - Verificar que todos los enlaces internos de la tabla de contenidos funcionan
    - Verificar que el formato de cada entrada sigue la plantilla uniforme
    - Confirmar que todos los requisitos (1-9) están cubiertos
    - _Requisitos: 9.1, 9.2, 9.3_
  - Ensure all tests pass, ask the user if questions arise.

## Notas

- Este es un feature de documentación pura — no requiere cambios en código C++
- El diccionario debe escribirse en español
- Los ejemplos deben usar datos ficticios que el usuario pueda pegar directamente en Excel
- Para funciones con TipoOutput, usar TipoOutput=1 como caso base en los ejemplos
- Leer los archivos fuente reales (.R, .jl, .py) para extraer nombres, parámetros y descripciones exactas
- La plantilla de cada función debe ser: Nombre Excel, Descripción, Parámetros (tabla), Ejemplo, Resultado esperado
