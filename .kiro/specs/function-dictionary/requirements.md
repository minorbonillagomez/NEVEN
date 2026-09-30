# Documento de Requisitos — Diccionario de Funciones NEVEN

## Introducción

Este documento especifica los requisitos para crear un Diccionario de Funciones completo de NEVEN. El diccionario es un artefacto de documentación que cataloga todas las funciones disponibles para el usuario en Excel, organizadas por lenguaje (R, Julia, Python) y por categoría funcional. Incluye ejemplos con datos ficticios que el usuario puede pegar directamente en Excel para probar cada función.

## Glosario

- **Diccionario**: Documento Markdown (.md) que cataloga todas las funciones de NEVEN con su nombre, descripción, parámetros, categoría y ejemplo de uso.
- **Función_Excel**: Fórmula que el usuario escribe en una celda de Excel para invocar una función de R, Julia o Python (ej: `=R.MR_Lineal(...)`, `=J.Algebra(...)`, `=P.ai_call(...)`).
- **Categoría**: Agrupación temática de funciones (regresión, visualización, series de tiempo, optimización, etc.).
- **Ejemplo_Dummy**: Fórmula completa con datos ficticios embebidos o referencia a un rango de ejemplo que el usuario puede copiar y pegar en Excel para verificar el funcionamiento.
- **TipoOutput**: Parámetro numérico presente en la mayoría de funciones que selecciona el tipo de resultado devuelto (0 = lista de procedimientos disponibles).
- **Librería**: Directorio `libreria/` que contiene los archivos fuente de funciones organizados por lenguaje.
- **Sistema_NEVEN**: El add-in XLL completo incluyendo funciones de sistema, R, Julia y Python.
- **Generador_Diccionario**: Proceso (manual o automatizado) que produce el documento del diccionario a partir de los archivos fuente.

## Requisitos

### Requisito 1: Reorganización de archivos fuente

**Historia de Usuario:** Como desarrollador, quiero que los archivos de funciones Python y Quarto estén organizados en `libreria/PYTHON/` y `libreria/QUARTO/`, para que la estructura del repositorio sea consistente con R y Julia.

#### Criterios de Aceptación

1. WHEN el repositorio es reorganizado, THE Sistema_NEVEN SHALL contener el directorio `libreria/PYTHON/` con los archivos de funciones Python (incluyendo las funciones AI: ai_call, ai_setup, ai_list_prompts y la función quarto_render).
2. WHEN el repositorio es reorganizado, THE Sistema_NEVEN SHALL contener el directorio `libreria/QUARTO/` con los archivos de ejemplo Quarto (.qmd) y documentación de uso.
3. THE Librería SHALL mantener la estructura de cuatro subdirectorios: `R/`, `JULIA/`, `PYTHON/`, `QUARTO/`.

### Requisito 2: Estructura del Diccionario

**Historia de Usuario:** Como usuario de NEVEN en Excel, quiero un documento de referencia completo que liste todas las funciones disponibles, para poder encontrar rápidamente la función que necesito y saber cómo usarla.

#### Criterios de Aceptación

1. THE Diccionario SHALL estar escrito en formato Markdown (.md) en idioma español.
2. THE Diccionario SHALL incluir una tabla de contenidos con enlaces internos a cada sección.
3. THE Diccionario SHALL organizar las funciones en secciones por lenguaje: R, Julia, Python y Sistema.
4. THE Diccionario SHALL incluir para cada función: nombre en Excel, descripción, parámetros con tipos y valores por defecto, categoría y al menos un ejemplo con datos ficticios.
5. THE Diccionario SHALL ubicarse en la ruta `docs/DICCIONARIO_FUNCIONES.md` dentro del repositorio.

### Requisito 3: Documentación de funciones R

**Historia de Usuario:** Como usuario de Excel, quiero ver todas las funciones R disponibles con sus parámetros y ejemplos, para poder ejecutar análisis estadísticos sin necesidad de conocer R.

#### Criterios de Aceptación

1. THE Diccionario SHALL documentar todas las funciones R de la librería (~90 procedimientos en 32 archivos), agrupadas por categoría: Regresión, Análisis de Datos, Series de Tiempo, Gráficos, Matemáticas, Funciones Auxiliares y Datos.
2. WHEN una función R tiene el parámetro TipoOutput, THE Diccionario SHALL listar todos los valores válidos de TipoOutput con su descripción.
3. THE Diccionario SHALL documentar las funciones R interactivas (Pivot, Esquisse, D3, Dashboard, Map) con su sintaxis de invocación via `=NEVEN.v(R.funcion(...))`.
4. WHEN una función R requiere paquetes externos, THE Diccionario SHALL indicar el paquete requerido.

### Requisito 4: Documentación de funciones Julia

**Historia de Usuario:** Como usuario de Excel, quiero ver todas las funciones Julia disponibles con sus procedimientos y ejemplos, para poder ejecutar cálculos matemáticos y de ML desde Excel.

#### Criterios de Aceptación

1. THE Diccionario SHALL documentar todas las funciones Julia (~70 procedimientos en 9 módulos), usando los nombres cortos (aliases): Algebra, Calculo, EDO, Estadistica, KNN, Regresion, Clustering, Optimizar, Transformar, Utilidades.
2. WHEN una función Julia tiene el parámetro TipoOutput, THE Diccionario SHALL listar todos los valores válidos de TipoOutput con la descripción del procedimiento correspondiente.
3. THE Diccionario SHALL incluir la sintaxis de invocación en Excel con el prefijo `=J.` (ej: `=J.Algebra(A1:C3, , 4)` para valores propios).

### Requisito 5: Documentación de funciones Python y AI

**Historia de Usuario:** Como usuario de Excel, quiero ver las funciones Python disponibles (especialmente las de AI), para poder invocar modelos de lenguaje y renderizar documentos Quarto desde Excel.

#### Criterios de Aceptación

1. THE Diccionario SHALL documentar las funciones Python públicas: ai_call, ai_setup, ai_list_prompts y quarto_render.
2. WHEN la función ai_call es documentada, THE Diccionario SHALL incluir la descripción de los parámetros data_str, prompt_name y context, junto con un ejemplo de invocación `=P.ai_call(A1:B10, "analizar", "contexto opcional")`.
3. THE Diccionario SHALL documentar la función quarto_render con sus formatos soportados (html, pdf, docx) y un ejemplo de uso.
4. THE Diccionario SHALL indicar los prerrequisitos de configuración para las funciones AI (neven-config.json, directorio de prompts).

### Requisito 6: Documentación de funciones del Sistema

**Historia de Usuario:** Como usuario de Excel, quiero conocer las funciones del sistema NEVEN (consola, visor, Pluto, Quarto), para poder controlar el entorno desde Excel.

#### Criterios de Aceptación

1. THE Diccionario SHALL documentar las funciones del sistema: NEVEN.r(), NEVEN.j(), NEVEN.v(), NEVEN.q(), NEVEN.pluto.start(), NEVEN.pluto.stop(), NEVEN.pluto.status(), NEVEN.pluto.data(), NEVEN.notebook.open(), NEVEN.notebook.list(), NEVEN.editor(), NEVEN.about(), NEVEN.help().
2. WHEN una función del sistema acepta parámetros, THE Diccionario SHALL documentar cada parámetro con su tipo y propósito.
3. THE Diccionario SHALL incluir un ejemplo funcional para cada función del sistema.

### Requisito 7: Ejemplos con datos ficticios

**Historia de Usuario:** Como usuario de Excel, quiero que cada función tenga un ejemplo con datos ficticios que pueda pegar directamente en Excel, para verificar que la función opera correctamente en mi instalación.

#### Criterios de Aceptación

1. THE Diccionario SHALL incluir al menos un Ejemplo_Dummy para cada función documentada.
2. WHEN un ejemplo requiere datos en un rango de celdas, THE Diccionario SHALL mostrar los datos de ejemplo en formato tabular que el usuario pueda transcribir a Excel.
3. WHEN un ejemplo usa TipoOutput, THE Diccionario SHALL mostrar el ejemplo con TipoOutput=1 (resultado principal) como caso base.
4. THE Diccionario SHALL indicar el resultado esperado o tipo de resultado para cada ejemplo.

### Requisito 8: Índice rápido por categoría

**Historia de Usuario:** Como usuario de Excel, quiero poder buscar funciones por categoría temática (no solo por lenguaje), para encontrar rápidamente la función adecuada para mi análisis.

#### Criterios de Aceptación

1. THE Diccionario SHALL incluir una sección de índice cruzado que agrupe funciones por categoría temática independientemente del lenguaje: Regresión, Clasificación/ML, Clustering, Estadística Descriptiva, Series de Tiempo, Álgebra Lineal, Cálculo Numérico, Optimización, Visualización, Datos/Transformación, Utilidades, AI/LLM.
2. WHEN una función pertenece a una categoría, THE Diccionario SHALL incluir un enlace interno a la documentación completa de esa función.

### Requisito 9: Mantenibilidad del Diccionario

**Historia de Usuario:** Como desarrollador, quiero que el diccionario sea fácil de mantener y actualizar cuando se agreguen nuevas funciones, para que la documentación no quede desactualizada.

#### Criterios de Aceptación

1. THE Diccionario SHALL usar un formato consistente y repetible para cada entrada de función (plantilla uniforme).
2. THE Diccionario SHALL incluir en el encabezado la fecha de última actualización y el conteo total de funciones documentadas.
3. WHEN una función es agregada al sistema, THE Diccionario SHALL poder ser actualizado agregando una nueva entrada siguiendo la plantilla existente sin modificar el resto del documento.
