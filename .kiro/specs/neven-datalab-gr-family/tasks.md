# Implementation Plan: Familia GR (Gráficos) en NEVEN Data Lab

## Overview

Crear los 16 archivos de la familia GR (8 wrappers `.Studio.R` + 8 sidecars `.json`) más la plantilla de extensibilidad (2 archivos adicionales). No se modifica ningún archivo de infraestructura existente. Los wrappers Plotly siguen el patrón: validación → construcción Plotly → codificación base64 → `r_object_to_slots`. El wrapper de mapas (`GR_Mapa`) adapta la función `R.Map` existente (Leaflet.js) al patrón Studio: en lugar de guardar a disco y retornar una ruta, retorna el HTML directamente como slot `html`.

## Tasks

- [x] 1. Crear los sidecars JSON de los 7 tipos de gráfico GR
  - Crear `NEVEN/Install/functions/GR_Scatter.json` con `family:"GR"`, roles X (numeric, req) + Y (numeric, req) + Color (numeric/text, opt) + Tamaño (numeric, opt) + Texto (text, opt), parámetros Titulo, MostrarLeyenda (tier 1), Paleta (tier 2)
  - Crear `NEVEN/Install/functions/GR_Barras.json` con roles X (text/numeric, req) + Y (numeric, req) + Color (text, opt), parámetros Titulo, MostrarLeyenda, Orientacion (select: Vertical/Horizontal, tier 1), Paleta (tier 2)
  - Crear `NEVEN/Install/functions/GR_Lineas.json` con roles X (numeric/text, req) + Y (numeric, req) + Color (text, opt), parámetros Titulo, MostrarLeyenda (tier 1), AnchoLinea (integer, default 2, tier 2), Paleta (tier 2)
  - Crear `NEVEN/Install/functions/GR_Histograma.json` con rol X (numeric, req), parámetros Titulo (tier 1), Bins (integer, default 30, tier 1), MostrarDensidad (boolean, default false, tier 2), Paleta (tier 2)
  - Crear `NEVEN/Install/functions/GR_BoxPlot.json` con roles X (text, req) + Y (numeric, req) + Color (text, opt), parámetros Titulo, MostrarLeyenda, MostrarPuntos (boolean, default false, tier 2)
  - Crear `NEVEN/Install/functions/GR_Correlaciones.json` con rol X (numeric, multiple:true, req), parámetros Titulo (tier 1), Metodo (select: Pearson/Spearman/Kendall, default 1, tier 1), MostrarValores (boolean, default true, tier 1), Paleta (tier 2)
  - Crear `NEVEN/Install/functions/GR_SeriesTiempo.json` con roles X (numeric/text, req) + Y (numeric, req) + Color (text, opt), parámetros Titulo, MostrarLeyenda, MostrarTendencia (boolean, default false, tier 1), TipoTendencia (select: Lineal/Polinómica, default 1, tier 2), AnchoLinea (integer, default 2, tier 2)
  - Crear `NEVEN/Install/functions/GR_Mapa.json` con roles Lat (numeric, req) + Lon (numeric, req) + Etiqueta (text, opt) + Valor (numeric, opt), parámetros Titulo (tier 1), TipoMapa (select: Marcadores/Mapa de calor/Círculos proporcionales, default 1, tier 1); wikipedia_url: https://es.wikipedia.org/wiki/Leaflet_(software)
  - Cada sidecar debe incluir `"wikipedia_url"` apuntando a la página de Wikipedia correspondiente (scatter plot, gráfico de barras, etc.)
  - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 7.1, 7.2, 10.2_

  - [ ]* 1.1 Prueba de smoke — validez y completitud de los 8 sidecars
    - Verificar que los 8 archivos JSON existen en `NEVEN/Install/functions/`
    - Verificar que cada uno tiene todos los campos requeridos del esquema Sidecar_GR
    - Verificar que `"family": "GR"` y `"family_label": "Gráficos"` en los 8 archivos
    - _Requisitos: 7.1, 7.5, 10.2_

- [x] 2. Implementar `GR_Scatter.Studio.R` — Scatter Plot
  - Crear `NEVEN/libreria/R/GR_Scatter.Studio.R` con función `GR_Scatter.Studio(data_X, data_Y, data_Color=NULL, data_Tamaño=NULL, data_Texto=NULL, Titulo="", MostrarLeyenda=TRUE, Paleta=1L)`
  - Validar que `data_X` y `data_Y` son data.frames, igual número de filas, columnas numéricas; lanzar `stop()` con mensajes en español si no se cumplen
  - Validar que las columnas no son todo-NA con el helper `.check_col_not_all_na()`
  - Extraer vectores `x_vec`, `y_vec`; si `data_Color` está presente, extraer `color_vec` para colorear puntos
  - Si `data_Tamaño` está presente, extraer `size_vec` numérico para escalar el marcador
  - Si `data_Texto` está presente, extraer `text_vec` para etiquetas hover
  - Construir trace `scatter` con `mode="markers"`, `marker=list(color=color_vec o "#d7a538", size=size_vec o 6)`
  - Construir layout con `title`, `xaxis`, `yaxis`, tema oscuro estándar, `showlegend=MostrarLeyenda`
  - Aplicar paleta según `Paleta`: 1=colores NEVEN (#d7a538/#888), 2=Viridis, 3=Plasma, 4=Set1, 5=Pastel
  - Codificar con `jsonlite::base64_enc(chartr("\n\r","  ", fig_json))` dentro de `tryCatch`
  - Retornar `r_object_to_slots(list(grafico = html_plotly), tier_map = c(grafico = 1L))`
  - _Requisitos: 5.1, 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2_

  - [ ]* 2.1 Prueba de propiedad — Propiedad 1 y 2 para GR_Scatter
    - **Propiedad 1: Slot de salida único tipo html con patrón neven-plotly**
    - **Propiedad 2: JSON Plotly válido en el slot (round-trip base64)**
    - Generar data.frames numéricos aleatorios (≥3 filas, 2+ cols), llamar a `GR_Scatter.Studio`, verificar: 1 slot, type="html", contiene `<neven-plotly>`, base64 decodificado es JSON con campos `data` y `layout`
    - Configurar con mínimo 100 iteraciones con `quickcheck`
    - _Requisitos: 4.2, 6.2, 6.3_

  - [ ]* 2.2 Prueba de propiedad — Propiedad 3 y 4 para GR_Scatter
    - **Propiedad 3: Tema oscuro preservado**
    - **Propiedad 4: Validación de input — rechazo de entradas inválidas**
    - Para entradas válidas: verificar `paper_bgcolor="#373434"`, `plot_bgcolor="#373434"`, `font.color="#888"` en el layout
    - Para entradas inválidas (no data.frame, 0 filas): verificar que se lanza `stop()` con mensaje no vacío en español
    - _Requisitos: 6.4, 6.5_

- [x] 3. Implementar `GR_Barras.Studio.R` — Gráfico de Barras
  - Crear `NEVEN/libreria/R/GR_Barras.Studio.R` con función `GR_Barras.Studio(data_X, data_Y, data_Color=NULL, Titulo="", MostrarLeyenda=TRUE, Orientacion=1L, Paleta=1L)`
  - Validar `data_X` (data.frame, 0 filas), `data_Y` (data.frame, columna numérica), mismo nrow
  - Validar que columna de `data_Y` no es todo-NA
  - Extraer `x_vec` (categórico o numérico), `y_vec` (numérico)
  - Si `data_Color` está presente, construir barras agrupadas (`barmode="group"`) con una traza por grupo; si no, una traza única
  - Aplicar `Orientacion`: 1=Vertical (type="bar"), 2=Horizontal (type="bar", orientation="h", intercambiar x↔y)
  - Construir layout con tema oscuro, `barmode="group"` si hay Color, `showlegend=MostrarLeyenda`
  - Codificar y retornar con el patrón estándar
  - _Requisitos: 5.2, 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2_

  - [ ]* 3.1 Prueba de propiedad — Propiedades 1, 2, 3 para GR_Barras
    - Generar data.frames con columna categórica (X) y numérica (Y) aleatorias
    - Verificar: 1 slot html, neven-plotly, JSON válido con data+layout, tema oscuro en layout
    - 100 iteraciones
    - _Requisitos: 4.2, 6.2, 6.3, 6.4_

- [x] 4. Implementar `GR_Lineas.Studio.R` — Gráfico de Líneas
  - Crear `NEVEN/libreria/R/GR_Lineas.Studio.R` con función `GR_Lineas.Studio(data_X, data_Y, data_Color=NULL, Titulo="", MostrarLeyenda=TRUE, AnchoLinea=2L, Paleta=1L)`
  - Validar `data_X`, `data_Y`, mismo nrow, columnas no todo-NA
  - Extraer `x_vec`, `y_vec`
  - Si `data_Color` está presente: agrupar filas por valor de `color_vec`, crear una traza `scatter` mode="lines" por grupo
  - Si `data_Color` es NULL: una traza única con `line=list(color="#d7a538", width=AnchoLinea)`
  - Ordenar datos por `x_vec` antes de graficar (evitar líneas que cruzan)
  - Construir layout con tema oscuro, `showlegend=MostrarLeyenda`
  - Codificar y retornar con el patrón estándar
  - _Requisitos: 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2_

  - [ ]* 4.1 Prueba de propiedad — Propiedades 1, 2, 3 para GR_Lineas
    - Generar pares (x_num, y_num) aleatorios con variación de nrow, con y sin Color
    - Verificar: 1 slot html, neven-plotly, JSON válido, tema oscuro
    - 100 iteraciones
    - _Requisitos: 4.2, 6.2, 6.4_

- [x] 5. Implementar `GR_Histograma.Studio.R` — Histograma
  - Crear `NEVEN/libreria/R/GR_Histograma.Studio.R` con función `GR_Histograma.Studio(data_X, Titulo="", Bins=30L, MostrarDensidad=FALSE, Paleta=1L)`
  - Validar `data_X` (data.frame, columna numérica, no todo-NA, ≥2 filas)
  - `Bins` debe ser entero positivo (≥1); si ≤0, usar default 30
  - Extraer `x_vec` numérico
  - Construir trace `histogram` con `nbinsx=Bins`, `marker=list(color="#d7a538", line=list(color="#373434", width=1))`
  - Si `MostrarDensidad=TRUE`, añadir `histnorm="probability density"` a la traza
  - Construir layout con tema oscuro, sin eje Y explícito (Plotly lo calcula automáticamente)
  - Codificar y retornar con el patrón estándar
  - _Requisitos: 5.4, 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2_

  - [ ]* 5.1 Prueba de propiedad — Propiedades 1, 2, 3 para GR_Histograma
    - Generar vectores numéricos aleatorios de distintos tamaños y distribuciones
    - Verificar: 1 slot html, neven-plotly, JSON válido, tema oscuro
    - Incluir caso Bins aleatorio entre 1 y 200
    - 100 iteraciones
    - _Requisitos: 4.2, 6.2, 6.4_

- [x] 6. Implementar `GR_BoxPlot.Studio.R` — Box Plot
  - Crear `NEVEN/libreria/R/GR_BoxPlot.Studio.R` con función `GR_BoxPlot.Studio(data_X, data_Y, data_Color=NULL, Titulo="", MostrarLeyenda=TRUE, MostrarPuntos=FALSE, Paleta=1L)`
  - Validar `data_X` (data.frame, columna texto para grupos), `data_Y` (data.frame, columna numérica), mismo nrow, no todo-NA
  - Extraer `x_vec` (categórico, usado como `x` en el trace box), `y_vec` (numérico)
  - Construir trace `box` con `x=x_vec, y=y_vec`, `boxpoints="all"` si `MostrarPuntos=TRUE` else `"outliers"`
  - Si `data_Color` está presente, colorear cajas por grupo con `marker=list(color=...)`
  - Construir layout con tema oscuro, `showlegend=MostrarLeyenda`, `boxmode="group"` si hay Color
  - Codificar y retornar con el patrón estándar
  - _Requisitos: 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2_

  - [ ]* 6.1 Prueba de propiedad — Propiedades 1, 2, 3 para GR_BoxPlot
    - Generar datos con columna categórica (X) y numérica (Y) de distintos grupos
    - Verificar: 1 slot html, neven-plotly, JSON válido, tema oscuro
    - 100 iteraciones
    - _Requisitos: 4.2, 6.2, 6.4_

- [x] 7. Implementar `GR_Correlaciones.Studio.R` — Mapa de Correlaciones
  - Crear `NEVEN/libreria/R/GR_Correlaciones.Studio.R` con función `GR_Correlaciones.Studio(data_X, Titulo="", Metodo=1L, MostrarValores=TRUE, Paleta=1L)`
  - Validar que `data_X` es data.frame con ≥2 columnas numéricas; si hay < 2, lanzar `stop("Se requieren al menos 2 columnas numéricas para el mapa de correlaciones.")`
  - Seleccionar columnas numéricas de `data_X` (descartar no numéricas con advertencia)
  - Calcular matriz de correlaciones con `cor(data_num, method=c("pearson","spearman","kendall")[Metodo], use="complete.obs")`
  - Construir trace `heatmap` con `z=cor_matrix`, `x=colnames`, `y=colnames`, `colorscale` según paleta, `zmin=-1, zmax=1`
  - Si `MostrarValores=TRUE`, añadir `text=round(cor_matrix, 2)`, `texttemplate="%{text}"` para mostrar valores en las celdas
  - Construir layout con tema oscuro, sin `showlegend` (heatmap tiene colorbar propia)
  - Codificar y retornar con el patrón estándar
  - _Requisitos: 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 9.3_

  - [ ]* 7.1 Prueba de propiedad — Propiedades 1, 2, 3 para GR_Correlaciones
    - Generar matrices numéricas de distintos tamaños (2-20 columnas, 10-200 filas)
    - Verificar: 1 slot html, neven-plotly, JSON válido, tema oscuro
    - 100 iteraciones
    - _Requisitos: 4.2, 6.2, 6.4_

  - [ ]* 7.2 Prueba unitaria — error con < 2 columnas numéricas
    - Llamar a `GR_Correlaciones.Studio` con 1 columna numérica
    - Verificar que se lanza error con mensaje exacto "Se requieren al menos 2 columnas numéricas..."
    - _Requisitos: 9.3_

- [x] 8. Implementar `GR_SeriesTiempo.Studio.R` — Serie de Tiempo
  - Crear `NEVEN/libreria/R/GR_SeriesTiempo.Studio.R` con función `GR_SeriesTiempo.Studio(data_X, data_Y, data_Color=NULL, Titulo="", MostrarLeyenda=TRUE, MostrarTendencia=FALSE, TipoTendencia=1L, AnchoLinea=2L, Paleta=1L)`
  - Validar `data_X` (data.frame, columna texto o numérica para tiempo), `data_Y` (data.frame, columna numérica), mismo nrow, no todo-NA
  - Extraer `x_vec` (texto o numérico, se usa como eje X temporal), `y_vec` numérico
  - Si `data_Color` está presente, agrupar por `color_vec` y crear una traza `scatter` mode="lines" por grupo
  - Si `data_Color` es NULL, una traza única mode="lines" con color "#d7a538", width=AnchoLinea
  - Si `MostrarTendencia=TRUE`:
    - `TipoTendencia=1` (Lineal): añadir traza de regresión lineal (`lm(y_vec ~ seq_along(x_vec))`), color "#888", linetype="dash"
    - `TipoTendencia=2` (Polinómica grado 2): usar `lm(y_vec ~ poly(seq_along(x_vec), 2))`, color "#888", linetype="dot"
  - Construir layout con tema oscuro, `showlegend=MostrarLeyenda`
  - Codificar y retornar con el patrón estándar
  - _Requisitos: 5.7, 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2_

  - [ ]* 8.1 Prueba de propiedad — Propiedades 1, 2, 3 para GR_SeriesTiempo
    - Generar pares tiempo/valor aleatorios, con y sin tendencia, con y sin Color
    - Verificar: 1 slot html, neven-plotly, JSON válido, tema oscuro
    - 100 iteraciones
    - _Requisitos: 4.2, 6.2, 6.4_

- [x] 8.5. Implementar `GR_Mapa.Studio.R` — Mapa Interactivo (Leaflet.js)
  - Crear `NEVEN/libreria/R/GR_Mapa.Studio.R` con función `GR_Mapa.Studio(data_Lat, data_Lon, data_Etiqueta=NULL, data_Valor=NULL, Titulo="", TipoMapa=1L)`
  - Validar que `data_Lat` y `data_Lon` son data.frames con columna numérica, mismo nrow, no todo-NA; lanzar `stop()` con mensajes descriptivos en español
  - Extraer `lat_vec` y `lon_vec` numéricos; calcular `center_lat` y `center_lon` con `mean(..., na.rm=TRUE)`
  - Si `data_Etiqueta` está presente, extraer `label_vec` (texto); si no, usar `"Punto"` como etiqueta genérica
  - Si `data_Valor` está presente, extraer `value_vec` numérico para heatmap e intensidad de círculos
  - Serializar los datos a JSON con `jsonlite::toJSON(datos, dataframe="rows", auto_unbox=TRUE)` para embeber en el HTML
  - Construir HTML con Leaflet.js desde CDN (mismos CDN que la función `R.Map` original): `leaflet@1.9.4` y `leaflet-heat@0.2.0`
  - Aplicar tiles CartoDB dark: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
  - Construir código JavaScript para el tipo de mapa seleccionado por `TipoMapa`:
    - `TipoMapa=1` (Marcadores): `L.marker([lat, lon]).addTo(map).bindPopup(label).bindTooltip(label)` por cada fila
    - `TipoMapa=2` (Mapa de calor): `L.heatLayer([[lat, lon, valor], ...], {radius: 25, blur: 15}).addTo(map)` usando `value_vec` como intensidad
    - `TipoMapa=3` (Círculos proporcionales): `L.circleMarker([lat, lon], {radius: escala(valor), fillColor: "#d7a538", ...})` con radio proporcional al valor normalizado entre 5 y 40
  - Construir HTML completo con header NEVEN dark (`background: #2d2d2d`), `#map` fullscreen, y script de inicialización Leaflet
  - **No codificar en base64** — Leaflet usa HTML puro (no formato `<neven-plotly>`); retornar el HTML directamente como string
  - Retornar `r_object_to_slots(list(mapa = html_leaflet), tier_map = c(mapa = 1L))` dentro de `tryCatch` que retorna slot HTML de error en caso de fallo
  - _Requisitos: 5.8 (nuevo), 6.1, 6.2, 6.4, 6.5, 9.1, 9.2_

  - [ ]* 8.5.1 Prueba unitaria — GR_Mapa retorna slot html con leaflet
    - Crear data.frame de prueba con lat/lon válidos (5 ciudades de Costa Rica)
    - Verificar para cada TipoMapa (1, 2, 3): 1 slot de tipo "html", `value` contiene `"leaflet"`, `value` contiene `"L.map"`, no contiene `"<neven-plotly>"`
    - _Requisitos: 6.2_

  - [ ]* 8.5.2 Prueba unitaria — GR_Mapa rechaza lat/lon inválidos
    - Llamar con columna de latitudes todo-NA → verificar `stop()` con mensaje en español
    - Llamar con 0 filas → verificar `stop()` con mensaje "El filtro aplicado no retorna filas..."
    - _Requisitos: 6.5, 9.1, 9.2_

- [x] 9. Punto de revisión — Verificar los 8 wrappers y sidecars
  - Asegurar que todos los tests pasan, preguntar al usuario si hay dudas.
  - Verificar que cada wrapper Plotly puede ser llamado con un data.frame mínimo (3 filas, tipos correctos)
  - Verificar que `GR_Mapa.Studio` retorna HTML con `L.map(` y tiles CartoDB
  - Verificar que el patrón `<neven-plotly>BASE64</neven-plotly>` está presente en los 7 wrappers Plotly
  - Verificar que `GR_Mapa` retorna HTML Leaflet puro (sin `<neven-plotly>`)
  - Verificar consistencia de tema oscuro en todos los gráficos generados

- [ ] 10. Implementar pruebas de propiedades transversales
  - [ ]* 10.1 Prueba de propiedad — Propiedad 4: Validación de input en todos los wrappers
    - **Propiedad 4: Validación de input — rechazo de entradas inválidas**
    - Para cada uno de los 7 wrappers: generar entradas inválidas (no data.frame, 0 filas, NULL)
    - Verificar que TODOS lanzan `stop()` con mensaje en español no vacío
    - 100 iteraciones por wrapper
    - _Requisitos: 6.5, 9.2_

  - [ ]* 10.2 Prueba de propiedad — Propiedad 5: Columnas todo-NA rechazadas
    - **Propiedad 5: Columnas todo-NA rechazadas con mensaje descriptivo**
    - Para cada wrapper que usa vectores numéricos: generar data.frame donde la columna asignada es toda NA
    - Verificar que el error contiene el nombre de la columna afectada
    - _Requisitos: 9.1_

  - [ ]* 10.3 Prueba de propiedad — Propiedad 10: Error Plotly produce HTML de error
    - **Propiedad 10: Error en construcción Plotly produce HTML de error — no excepción propagada**
    - Inyectar un fallo en la construcción del spec Plotly (mock de `jsonlite::toJSON` que falla)
    - Verificar que el wrapper retorna un slot html con mensaje de error incrustado, sin propagar excepción
    - _Requisitos: 9.4_

- [x] 11. Crear las plantillas de extensibilidad para usuarios (GR_EjemploBasico y GR_EjemploAvanzado)
  - Crear `NEVEN/Install/functions/GR_EjemploBasico.Studio.R`:
    - Función `GR_EjemploBasico.Studio(data_X, data_Y, Titulo="", Paleta=1L)`
    - Implementar un scatter plot mínimo funcional (2 roles, 2 parámetros)
    - Añadir bloque de comentarios inicial con 5 pasos para crear un gráfico propio
    - Comentar cada sección: validación, extracción de vectores, construcción trace, construcción layout, codificación base64, retorno con r_object_to_slots
  - Crear `NEVEN/Install/functions/GR_EjemploBasico.json`:
    - `"id": "GR_EjemploBasico"`, `"family": "GR"`, `"family_label": "Gráficos"`
    - Roles `X` (numeric, req) y `Y` (numeric, req)
    - Parámetros: `Titulo` (text, tier 1), `Paleta` (select: NEVEN/Viridis/Plasma, tier 2)
    - Comentarios inline en cada campo JSON explicando su propósito
  - Crear `NEVEN/Install/functions/GR_EjemploAvanzado.Studio.R`:
    - Función `GR_EjemploAvanzado.Studio(data_X, data_Y, data_Color=NULL, data_Tamaño=NULL, Titulo="", MostrarLeyenda=TRUE, ModoHover=1L, Paleta=1L, Opacidad=80L)`
    - Implementar un gráfico de burbujas (scatter con tamaño variable y color) — muestra el patrón completo con 4 roles y parámetros tier 1 + tier 2
    - Mostrar cómo construir tooltips personalizados con `hovertemplate`
    - Mostrar cómo manejar roles opcionales (data_Color y data_Tamaño pueden ser NULL)
    - Comentar cada decisión de diseño: por qué se ordena, cómo se normaliza el tamaño, cómo se aplica la opacidad
  - Crear `NEVEN/Install/functions/GR_EjemploAvanzado.json`:
    - `"id": "GR_EjemploAvanzado"`, `"family": "GR"`, `"family_label": "Gráficos"`
    - Roles: `X` (numeric, req), `Y` (numeric, req), `Color` (text/numeric, opt), `Tamaño` (numeric, opt)
    - Parámetros: `Titulo` (text, tier 1), `MostrarLeyenda` (boolean, default true, tier 1), `ModoHover` (select: Basico/Completo, tier 1), `Paleta` (select, tier 2), `Opacidad` (integer 0-100, default 80, tier 2)
  - _Requisitos: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 11.1 Prueba unitaria — GR_EjemploBasico es funcional
    - Llamar con data.frame de prueba (10 filas, 2 cols numéricas)
    - Verificar: 1 slot html, contiene `<neven-plotly>`, JSON decodificado tiene `data` y `layout`
    - _Requisitos: 8.3_

  - [ ]* 11.2 Prueba unitaria — GR_EjemploAvanzado es funcional con roles opcionales
    - Llamar con solo X + Y (sin Color ni Tamaño) → verificar que funciona
    - Llamar con X + Y + Color + Tamaño → verificar que funciona con 4 roles
    - Verificar que el hover personalizado está presente en el JSON Plotly
    - _Requisitos: 8.3, 8.4_

- [x] 12. Punto de revisión final — Integración completa
  - Asegurar que todos los tests pasan, preguntar al usuario si hay dudas.
  - Verificar que los 20 archivos GR (8 wrappers + 8 sidecars + 4 plantillas) están creados
  - Verificar que el catálogo retorna la familia "Gráficos" con los 10 tipos de gráfico (8 + GR_EjemploBasico + GR_EjemploAvanzado)
  - Verificar que ningún archivo de infraestructura existente fue modificado (`datalab_handler.py`, `datalab.js`, `r_object_to_slots.R`, `taskpane.html`)

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1 - Sidecars JSON (8 archivos)"]
    },
    {
      "wave": 2,
      "tasks": [
        "2 - GR_Scatter.Studio.R",
        "3 - GR_Barras.Studio.R",
        "4 - GR_Lineas.Studio.R",
        "5 - GR_Histograma.Studio.R",
        "6 - GR_BoxPlot.Studio.R",
        "7 - GR_Correlaciones.Studio.R",
        "8 - GR_SeriesTiempo.Studio.R",
        "8.5 - GR_Mapa.Studio.R"
      ]
    },
    {
      "wave": 3,
      "tasks": ["9 - Punto de revisión intermedio"]
    },
    {
      "wave": 4,
      "tasks": [
        "10 - Pruebas de propiedades transversales",
        "11 - Plantilla de extensibilidad"
      ]
    },
    {
      "wave": 5,
      "tasks": ["12 - Punto de revisión final"]
    }
  ]
}
```

Tarea 1 es prerequisito para todas las demás. Las tareas 2-8.5 son independientes entre sí. No hay dependencias en ningún archivo de infraestructura existente.

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para una implementación MVP más rápida.
- Todos los wrappers GR son independientes entre sí — se pueden implementar en cualquier orden.
- El patrón de validación y codificación base64 es idéntico en los 7 wrappers; copiar y adaptar desde `GR_Scatter.Studio.R` es el flujo recomendado.
- Las pruebas de propiedad requieren instalar `quickcheck` desde CRAN: `install.packages("quickcheck")`.
- Los sidecars deben crearse antes que los wrappers para poder usar el Data Lab durante el desarrollo.
- El helper `.check_col_not_all_na()` puede definirse en cada wrapper o extraerse a un archivo compartido `GR_utils.R` cargado en el startup de ControlR.
- `GR_Mapa.Studio.R` es el único wrapper de la familia GR que **no usa `<neven-plotly>`** — genera HTML Leaflet.js directamente. El slot sigue siendo de tipo `html` y se renderiza en `<iframe srcdoc>` exactamente igual que los demás. La función `R.Map` existente (`R4XCL-AD-Map.R`) contiene toda la lógica de mapa; `GR_Mapa.Studio.R` la adapta al patrón Studio retornando el HTML como string en lugar de escribirlo a disco.
