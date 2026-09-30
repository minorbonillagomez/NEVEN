# Requirements Document

## Introduction

NEVEN Data Lab ya dispone de familias analíticas (AD, RG, DS, TM, UC). Este documento especifica la nueva familia **GR (Gráficos)**, que añade creación de gráficos interactivos guiados al Data Lab usando la infraestructura exactamente existente: wrappers `.Studio.R` + sidecars `.json`, `r_object_to_slots`, `datalab_handler.py` y el componente `<neven-plotly>` ya integrado.

El usuario carga datos en DuckDB vía la pestaña Data Studio, luego va a Data Lab, selecciona la familia Gráficos, elige un tipo de gráfico, asigna columnas a los roles visuales (X, Y, Color, etc.), configura parámetros estéticos y hace clic en "Ejecutar análisis". El panel de resultados muestra el gráfico Plotly interactivo en el slot de tipo `html`.

La familia GR es totalmente extensible por el usuario: cualquier persona puede añadir `MiGrafico.Chart.R` + `MiGrafico.json` con `"family": "GR"` para incorporar tipos de gráfico propios.

---

## Glossary

- **Familia_GR**: Agrupación de funciones con `"family": "GR"` y `"family_label": "Gráficos"` que aparece en el selector de familias del Data Lab.
- **Wrapper_GR**: Función R con nombre `{ID}.Studio` en un archivo `{ID}.Studio.R` que construye un gráfico Plotly y retorna un único slot de tipo `html`.
- **Sidecar_GR**: Archivo `.json` colocado junto al Wrapper_GR que declara `"family": "GR"`, los roles de variable (`X`, `Y`, `Color`, `Tamaño`, `Texto`) y los parámetros de configuración visual.
- **Rol_Visual**: Slot de asignación de columnas con semántica gráfica — `X` (eje horizontal / grupo / tiempo), `Y` (valores numéricos), `Color` (agrupación/color), `Tamaño` (tamaño de puntos, numérico), `Texto` (etiquetas de puntos).
- **Slot_HTML_Plotly**: El único slot de salida de un Wrapper_GR, de tipo `html`, cuyo valor es `<html><body><neven-plotly>BASE64</neven-plotly></body></html>` donde BASE64 es el JSON Plotly codificado en base64.
- **Tema_Oscuro**: Paleta de colores estándar de NEVEN: `paper_bgcolor="#373434"`, `plot_bgcolor="#373434"`, `font color="#888"`, acento `"#d7a538"`.
- **Plantilla_Extensibilidad**: Par de archivos `GR_EjemploPersonalizado.Studio.R` + `GR_EjemploPersonalizado.json` que sirven de punto de partida documentado para usuarios que quieran añadir gráficos propios.
- **Catálogo**: El endpoint `GET /api/datalab/catalog` existente que ya descubre todos los sidecars; no requiere modificación para incluir la familia GR.
- **DataLabHandler**: El módulo Python `datalab_handler.py` existente que ya procesa ejecuciones para cualquier `family`; no requiere modificación.
- **r_object_to_slots**: Función R del startup de ControlR que serializa el resultado de un wrapper a slots tipados; no requiere modificación.

---

## Requirements

### Requisito 1: Descubrimiento y selección de la familia GR

**Historia de usuario:** Como usuario de NEVEN Data Lab, quiero ver la familia "Gráficos" en el selector de familias, para poder acceder a los tipos de gráfico sin configuración adicional.

#### Criterios de aceptación

1. WHEN la Data_Lab carga el catálogo vía `GET /api/datalab/catalog`, THE Catálogo SHALL incluir todos los sidecars con `"family": "GR"` agrupados bajo la etiqueta `"family_label": "Gráficos"`.
2. WHEN el usuario selecciona la familia "Gráficos" en el selector de familias, THE Data_Lab SHALL mostrar únicamente las Function_Cards cuyo campo `family` sea `"GR"`.
3. THE Data_Lab SHALL mostrar para cada Function_Card GR su `name` y `description` provenientes del Sidecar_GR correspondiente.
4. IF no existen sidecars con `"family": "GR"` en `C:\NEVEN\functions\`, THEN THE Catálogo SHALL retornar un catálogo sin la familia GR y THE Data_Lab SHALL no mostrar la familia "Gráficos" en el selector.
5. WHEN el usuario añade un nuevo par `MiGrafico.Studio.R` + `MiGrafico.json` con `"family": "GR"` en `C:\NEVEN\functions\` y recarga el catálogo, THE Data_Lab SHALL mostrar el nuevo tipo de gráfico en la familia "Gráficos" sin reiniciar NEVEN.

---

### Requisito 2: Roles de variable para gráficos

**Historia de usuario:** Como usuario de NEVEN Data Lab, quiero asignar columnas del dataset a roles visuales (X, Y, Color, etc.), para que el gráfico utilice las columnas correctas sin que yo escriba código.

#### Criterios de aceptación

1. WHEN el usuario selecciona una función de la familia GR, THE Column_Panel SHALL mostrar exactamente los roles de variable definidos en el Sidecar_GR de esa función, con sus etiquetas en español.
2. WHEN un rol tiene `"required": true` y el usuario hace clic en Ejecutar sin asignarlo, THE Data_Lab SHALL mostrar un mensaje de validación en español identificando el rol sin asignar y SHALL NOT enviar la solicitud al servidor.
3. WHEN un rol tiene `"required": false`, THE Data_Lab SHALL mostrar el rol como opcional y SHALL permitir la ejecución sin que ese rol esté asignado.
4. WHEN un rol tiene `"types": ["numeric"]`, THE Column_Panel SHALL permitir únicamente la asignación de columnas cuyo tipo DuckDB sea numérico (INTEGER, DOUBLE, FLOAT, DECIMAL, BIGINT).
5. WHEN un rol tiene `"types": ["text"]`, THE Column_Panel SHALL permitir únicamente la asignación de columnas cuyo tipo DuckDB sea texto o categórico (VARCHAR, TEXT, CHAR).
6. WHEN un rol tiene `"types": ["numeric", "text"]`, THE Column_Panel SHALL permitir la asignación de cualquier columna independientemente de su tipo DuckDB.
7. WHERE un rol tiene `"multiple": true`, THE Column_Panel SHALL permitir asignar más de una columna a ese rol.

---

### Requisito 3: Parámetros de configuración visual

**Historia de usuario:** Como usuario de NEVEN Data Lab, quiero configurar los parámetros estéticos de cada gráfico (título, paleta, leyenda, etc.) desde el formulario de parámetros, para personalizar la visualización sin editar código R.

#### Criterios de aceptación

1. WHEN el usuario selecciona una función de la familia GR, THE Parameter_Form SHALL renderizar un control por cada entrada del array `parameters` del Sidecar_GR, usando el `label` como etiqueta visible.
2. THE Parameter_Form SHALL soportar los tipos de parámetro: `integer` → spinner numérico, `boolean` → checkbox, `select` → dropdown con las `options` del sidecar.
3. THE Parameter_Form SHALL inicializar cada control al valor `default` definido en el Sidecar_GR.
4. WHEN un parámetro tiene `"tier": 2`, THE Parameter_Form SHALL renderizar ese control dentro de una sección colapsable "Parámetros avanzados" que está colapsada por defecto.
5. IF el usuario introduce un valor no entero en un control `integer`, THEN THE Parameter_Form SHALL mostrar un error de validación en ese control y SHALL NOT permitir el envío del formulario.
6. THE Parameter_Form SHALL incluir como mínimo los siguientes parámetros en cada tipo de gráfico que corresponda: `Titulo` (text, tier 1), `MostrarLeyenda` (boolean, default true, tier 1), `Paleta` (select con opciones de paleta Plotly, tier 2).

---

### Requisito 4: Ejecución y retorno de un slot HTML Plotly

**Historia de usuario:** Como usuario de NEVEN Data Lab, quiero hacer clic en "Ejecutar análisis" y ver el gráfico interactivo en el panel de resultados, para explorar mis datos visualmente sin instalar software adicional.

#### Criterios de aceptación

1. WHEN el usuario hace clic en "Ejecutar análisis" con todos los roles requeridos asignados, THE Data_Lab SHALL POST a `/api/datalab/run` con `function_id`, `language`, `column_roles`, `parameters` y `filter_clause`.
2. WHEN THE DataLabHandler ejecuta un Wrapper_GR en ControlR, THE Wrapper_GR SHALL retornar exactamente un slot con `"type": "html"` cuyo valor comience con `<html>` y contenga el patrón `<neven-plotly>BASE64</neven-plotly>`.
3. WHEN THE Results_Panel recibe el slot de tipo `html` de un Wrapper_GR, THE Results_Panel SHALL renderizarlo usando `<iframe srcdoc>` para que el gráfico Plotly interactivo funcione correctamente.
4. IF un Wrapper_GR lanza una excepción R, THEN THE DataLabHandler SHALL retornar un objeto JSON con `"status": "error"` y el mensaje de error en R, y THE Data_Lab SHALL mostrar ese mensaje en el área de error del Results_Panel.
5. WHEN la ejecución está en curso, THE Data_Lab SHALL deshabilitar el botón "Ejecutar análisis" y mostrar un indicador de carga, y SHALL re-habilitarlo al recibir la respuesta o al producirse un error.

---

### Requisito 5: Catálogo inicial — 7 tipos de gráfico

**Historia de usuario:** Como usuario de NEVEN Data Lab, quiero encontrar los tipos de gráfico más comunes (scatter, barras, líneas, histograma, boxplot, correlaciones, series de tiempo) ya disponibles, para empezar a visualizar mis datos inmediatamente.

#### Criterios de aceptación

1. THE Catálogo SHALL incluir una Function_Card con `"id": "GR_Scatter"`, `"family": "GR"`, nombre visible "Scatter Plot", roles `X` (numérico, requerido) y `Y` (numérico, requerido), con `Color` como rol opcional.
2. THE Catálogo SHALL incluir una Function_Card con `"id": "GR_Barras"`, `"family": "GR"`, nombre visible "Gráfico de Barras", rol `X` (text/numeric, requerido) y `Y` (numérico, requerido), con `Color` como agrupación opcional.
3. THE Catálogo SHALL incluir una Function_Card con `"id": "GR_Lineas"`, `"family": "GR"`, nombre visible "Gráfico de Líneas", roles `X` (numeric/text, requerido) y `Y` (numérico, requerido), con `Color` para series opcional.
4. THE Catálogo SHALL incluir una Function_Card con `"id": "GR_Histograma"`, `"family": "GR"`, nombre visible "Histograma", rol `X` (numérico, requerido) y parámetro `Bins` (integer, default 30).
5. THE Catálogo SHALL incluir una Function_Card con `"id": "GR_BoxPlot"`, `"family": "GR"`, nombre visible "Box Plot", roles `X` (text, requerido para grupos) y `Y` (numérico, requerido), con `Color` opcional.
6. THE Catálogo SHALL incluir una Function_Card con `"id": "GR_Correlaciones"`, `"family": "GR"`, nombre visible "Mapa de Correlaciones", rol `X` (numérico, múltiple, requerido, mínimo 2 columnas) sin rol `Y`.
7. THE Catálogo SHALL incluir una Function_Card con `"id": "GR_SeriesTiempo"`, `"family": "GR"`, nombre visible "Serie de Tiempo", roles `X` (text/numeric, requerido, columna de tiempo) y `Y` (numérico, requerido), con parámetro `MostrarTendencia` (boolean, default false).

---

### Requisito 6: Arquitectura del Wrapper_GR

**Historia de usuario:** Como ingeniero de NEVEN, quiero que los Wrapper_GR sigan el mismo patrón que los demás wrappers Studio, para que no se requieran cambios en la infraestructura existente (datalab_handler.py, datalab.js, r_object_to_slots.R, taskpane.html).

#### Criterios de aceptación

1. THE Wrapper_GR SHALL ser un archivo R nombrado `{ID}.Studio.R` que define una función `{ID}.Studio()` con parámetros `data_X` (siempre presente), y opcionalmente `data_Y`, `data_Color`, `data_Tamaño`, `data_Texto`, más los parámetros de configuración definidos en el Sidecar_GR.
2. THE Wrapper_GR SHALL retornar `r_object_to_slots(list(grafico = html_plotly), tier_map = c(grafico = 1L))` donde `html_plotly` es la cadena HTML con el patrón `<neven-plotly>BASE64</neven-plotly>`.
3. THE Wrapper_GR SHALL construir el gráfico codificando el spec JSON de Plotly en base64 con `jsonlite::base64_enc(chartr("\n\r", "  ", fig_json))` dentro de un `tryCatch` que retorna HTML de error en caso de fallo.
4. THE Wrapper_GR SHALL aplicar el Tema_Oscuro estándar: `paper_bgcolor="#373434"`, `plot_bgcolor="#373434"`, `font=list(color="#888")`, con el acento `"#d7a538"` para elementos principales.
5. THE Wrapper_GR SHALL validar al inicio que `data_X` es un `data.frame` y que las columnas tienen los tipos esperados, lanzando `stop()` con mensaje descriptivo en caso de error.
6. THE DataLabHandler existente SHALL ejecutar Wrapper_GR sin modificación, ya que el campo `"family": "GR"` en el sidecar es suficiente para el enrutamiento.

---

### Requisito 7: Esquema del Sidecar_GR

**Historia de usuario:** Como ingeniero de NEVEN, quiero que los sidecars de la familia GR sigan el esquema estándar del Data Lab con los roles visuales específicos de gráficos, para garantizar consistencia y validación automática.

#### Criterios de aceptación

1. THE Sidecar_GR SHALL contener los campos requeridos estándar: `id`, `family` (= `"GR"`), `family_label` (= `"Gráficos"`), `name`, `description`, `languages` (= `["r"]`), `function_name`, `file`, `variable_roles`, `parameters`.
2. THE Sidecar_GR SHALL usar únicamente los siguientes nombres de rol en `variable_roles`: `X`, `Y`, `Color`, `Tamaño`, `Texto` — con las restricciones de tipo y multiplicidad apropiadas para cada tipo de gráfico.
3. WHEN el campo `wikipedia_url` está presente en el Sidecar_GR, THE Data_Lab SHALL mostrarlo como enlace informativo en la tarjeta de la función; si no está presente, no se mostrará ningún enlace.
4. FOR ALL Sidecar_GR que el endpoint de catálogo lee exitosamente, validar el JSON contra el esquema y re-serializarlo SHALL producir un documento con los mismos valores de campo (estabilidad de round-trip).
5. IF un Sidecar_GR tiene `"family": "GR"` pero carece de algún campo requerido, THEN THE HTTP_Server SHALL omitir esa entrada del catálogo y registrar una advertencia con el nombre del archivo y la razón del rechazo.

---

### Requisito 8: Plantilla de extensibilidad para usuarios

**Historia de usuario:** Como usuario avanzado de NEVEN, quiero una plantilla documentada de un gráfico GR mínimo, para poder crear mis propios tipos de gráfico siguiendo el mismo patrón sin entender el código fuente interno.

#### Criterios de aceptación

1. THE Catálogo SHALL incluir un archivo `GR_EjemploPersonalizado.Studio.R` en `NEVEN/Install/functions/` que implementa un scatter plot mínimo usando el patrón GR completo, con comentarios explicativos en cada sección.
2. THE Catálogo SHALL incluir un archivo `GR_EjemploPersonalizado.json` en `NEVEN/Install/functions/` con `"family": "GR"`, un rol `X` y un rol `Y` numéricos, y dos parámetros (uno tier 1, uno tier 2), con comentarios inline explicando cada campo.
3. THE Plantilla_Extensibilidad SHALL ser funcional como gráfico en Data Lab sin modificaciones — el usuario puede copiarla, renombrarla y modificarla para crear variantes.
4. WHEN el usuario copia `GR_EjemploPersonalizado.Studio.R` y `GR_EjemploPersonalizado.json` a `C:\NEVEN\functions\`, cambia el `id` y `function_name` en el JSON y el nombre de la función en el R, y recarga el catálogo, THE Data_Lab SHALL mostrar el nuevo gráfico personalizado en la familia "Gráficos".

---

### Requisito 9: Manejo de errores en gráficos GR

**Historia de usuario:** Como usuario de NEVEN Data Lab, quiero ver mensajes de error claros cuando un gráfico no se puede generar, para saber exactamente qué corregir sin recurrir a herramientas de desarrollo.

#### Criterios de aceptación

1. IF las columnas asignadas al rol `X` o `Y` contienen únicamente valores `NA` después de filtrar, THEN THE Wrapper_GR SHALL lanzar `stop()` con el mensaje "La columna '{nombre}' no contiene valores válidos (solo NA)." antes de intentar construir el gráfico.
2. IF el número de filas después de aplicar el filtro WHERE es cero, THEN THE Wrapper_GR SHALL lanzar `stop()` con el mensaje "El filtro aplicado no retorna filas. Verifique la cláusula WHERE." antes de intentar construir el gráfico.
3. IF `GR_Correlaciones.Studio` recibe menos de 2 columnas numéricas en `data_X`, THEN THE Wrapper_GR SHALL lanzar `stop()` con el mensaje "Se requieren al menos 2 columnas numéricas para el mapa de correlaciones."
4. WHEN la construcción del gráfico Plotly falla dentro del `tryCatch`, THE Wrapper_GR SHALL retornar un slot HTML con el mensaje de error incrustado en el HTML: `<p style="color:#888;padding:8px">Gráfico no disponible: {mensaje}</p>`, permitiendo que el Results_Panel lo muestre sin colapsar la ejecución entera.
5. IF ControlR no está disponible cuando el usuario hace clic en "Ejecutar análisis", THEN THE Data_Lab SHALL mostrar el mensaje "Motor R no disponible. Verifique que NEVEN esté iniciado correctamente." en el área de error del Results_Panel.

---

### Requisito 10: Ubicación de archivos y convención de nombres

**Historia de usuario:** Como ingeniero de NEVEN, quiero que los archivos de la familia GR sigan las convenciones de ubicación y nombres del proyecto, para que el sistema de descubrimiento automático los encuentre correctamente.

#### Criterios de aceptación

1. THE Wrapper_GR SHALL estar ubicado en `NEVEN/libreria/R/` con el nombre `{ID}.Studio.R` donde `{ID}` es el identificador del gráfico (ej: `GR_Scatter.Studio.R`).
2. THE Sidecar_GR SHALL estar ubicado en `NEVEN/Install/functions/` con el nombre `{ID}.json` (ej: `GR_Scatter.json`).
3. THE Plantilla_Extensibilidad SHALL estar ubicada en `NEVEN/Install/functions/` con el nombre `GR_EjemploPersonalizado.Studio.R` y `GR_EjemploPersonalizado.json`.
4. WHEN el sistema de despliegue copia los archivos de `NEVEN/Install/functions/` a `C:\NEVEN\functions\` y los archivos de `NEVEN/libreria/R/` a `C:\NEVEN\libreria\R\`, THE Catálogo SHALL descubrir todos los sidecars GR automáticamente en el siguiente inicio de NEVEN Studio.
5. THE Wrapper_GR `file` field en el Sidecar_GR SHALL referenciar el nombre de archivo exacto del wrapper en el directorio `C:\NEVEN\libreria\R\`, usando solo el nombre de archivo sin ruta.
