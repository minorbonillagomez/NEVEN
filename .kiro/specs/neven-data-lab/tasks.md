# Implementation Plan: NEVEN Data Lab

## Overview

Data Lab V1 introduces a new tab in NEVEN Studio Standalone that exposes R analytical functions through a guided point-and-click interface. The implementation spans nine core components: the R serializer (`r_object_to_slots.R`), the K-Means Studio wrapper, the K-Means sidecar JSON, the migration script, the Python `DataLabHandler`, two route additions to the HTTP server, the Data Lab tab in `taskpane.html`, and the `datalab.js` UI module.

The scope has since been expanded beyond V1 with a full catalog of analytical function families: UC (ejemplos para usuarios, plantillas de funciones personalizadas), AD (análisis de datos — ACP y Clustering Jerárquico), RG (regresión — ocho modelos), DS (conjuntos de datos de Wooldridge), y TM (text mining en Python). La documentación de extensibilidad (`COMO_AGREGAR_FUNCIONES.md`) también fue creada. En total el catálogo cubre 17 funciones adicionales más allá del K-Means original.

## Tasks

- [x] 1. Crear `r_object_to_slots.R` — serializador R de slots tipificados
  - [x] 1.1 Crear el archivo `NEVEN/startup/r_object_to_slots.R` con la función pública `r_object_to_slots(obj, tier_map = NULL)`
  - [x] 1.2 Implementar `.neven_dl_detect_type(val)` con las cinco reglas de prioridad: `data.frame`/`matrix` → `"table"`, string con `<html` → `"html"`, vector atómico longitud > 1 → `"vector"`, vector atómico longitud 1 → `"scalar"`, cualquier otro → `"unknown"`
  - [x] 1.3 Implementar `.neven_dl_serialize_value(val, tipo)` con `switch` por tipo: `table` usa `jsonlite::toJSON(as.data.frame(val), dataframe="rows", auto_unbox=TRUE, na="null")`; `html` pasa el string tal cual; `vector` usa `jsonlite::toJSON(as.list(val))`; `scalar` usa `jsonlite::toJSON(val, auto_unbox=TRUE)`; `unknown` intenta toJSON y cae a `paste(capture.output(print(val)))` en caso de error
  - [x] 1.4 En `r_object_to_slots`, manejar objetos sin nombres (`names(obj) == NULL`) envolviéndolos en `list(result = obj)` con nombre `"result"`
  - [x] 1.5 Aplicar `tier_map` como override: `tier <- 1L`; si `!is.null(tier_map) && !is.na(tier_map[nm])` entonces `tier <- as.integer(tier_map[nm])`
  - [x] 1.6 Retornar el resultado como `data.frame` vía `do.call(rbind, lapply(slots, as.data.frame, stringsAsFactors=FALSE))` para que ControlR lo serialice como `Variable(arr)`
  - [x] 1.7 Agregar el bloque `source()` al final de `NEVEN/startup/startup.r` para cargar `r_object_to_slots.R` al arrancar ControlR, con fallback a `C:\NEVEN\startup\r_object_to_slots.R` y `warning()` si no se encuentra

- [x] 2. Crear `AD_KMedias.Studio.R` — wrapper K-Means para Data Lab
  - [x] 2.1 Crear el archivo `NEVEN/libreria/R/R4XCL-AD-KMediass.Studio.R` con la función `AD_KMedias.Studio(data, K=3L, Escala=FALSE, TipoModelo=1L, Semilla=123456L)`
  - [x] 2.2 Implementar validaciones: `data` debe ser `data.frame` o `matrix`; conservar solo columnas numéricas (`sapply(data, is.numeric)`); validar que `any(num_cols)` sea TRUE; validar `K >= 1` y `K < nrow(data_num)`; validar `TipoModelo` en `1:4`
  - [x] 2.3 Implementar la preparación de datos: `set.seed(as.integer(Semilla))`; si `Escala == TRUE` aplicar `scale(data_num)`; construir `data_proc`
  - [x] 2.4 Ejecutar `kmeans(data_proc, centers=K, algorithm=algoritmos[TipoModelo], nstart=10L)` donde `algoritmos <- c("Hartigan-Wong","Lloyd","Forgy","MacQueen")`
  - [x] 2.5 Construir el objeto `resultado`: `centers` como `data.frame` de centroides con columna `Cluster` primera; `cluster_assignments` como `as.integer(res_km$cluster)`; `within_ss`, `total_ss`, `between_ss` redondeados a 4 decimales
  - [x] 2.6 Definir `tier_map <- c(centers=1L, cluster_assignments=1L, within_ss=2L, total_ss=2L, between_ss=2L)` y retornar `r_object_to_slots(resultado, tier_map=tier_map)`

- [x] 3. Crear `R4XCL-AD-KMediass.json` — sidecar JSON para K-Means
  - [x] 3.1 Crear el archivo `NEVEN/Install/functions/R4XCL-AD-KMediass.json` con los campos de identificación: `"id": "AD_KMedias"`, `"family": "AD"`, `"family_label": "Análisis de Datos"`, `"name": "K-Medias"`, `"description"`, `"languages": ["r"]`, `"function_name": "AD_KMedias.Studio"`, `"file": "R4XCL-AD-KMediass.Studio.R"`
  - [x] 3.2 Agregar `variable_roles` con el rol `X`: `"label": "Variables activas"`, `"types": ["numeric"]`, `"multiple": true`, `"required": true`
  - [x] 3.3 Agregar `parameters`: `K` (integer, default 3, tier 1), `Escala` (boolean, default false, tier 1), `TipoModelo` (select, default 1, tier 1, options Hartigan-Wong/Lloyd/Forgy/MacQueen con values 1/2/3/4), `Semilla` (integer, default 123456, tier 2)
  - [x] 3.4 Verificar que el JSON es sintácticamente válido y contiene todos los campos obligatorios definidos en `REQUIRED_SIDECAR_FIELDS`

- [x] 4. Crear `migrate_attr_to_json.R` — script de migración one-shot
  - [x] 4.1 Crear el archivo `NEVEN/scripts/migrate_attr_to_json.R` que lee el directorio desde `commandArgs(trailingOnly=TRUE)[1]` con fallback a `"C:\\NEVEN\\functions"`; verificar que el directorio existe con `dir.exists`
  - [x] 4.2 Implementar `PREFIX_FAMILY_MAP` con los cinco prefijos y `derive_family(filename)` con loop sobre `names(PREFIX_FAMILY_MAP)` usando `startsWith`; retornar `"GENERAL"` si no hay match
  - [x] 4.3 Implementar `generate_sidecar(r_file)`: comprobar si ya existe el `.json` con `file.exists` (skip con `cat("[SKIP]...")`); cargar el `.R` en entorno limpio con `sys.source(r_file, envir=env)`; buscar funciones con `attr(fn, "description")`; extraer `description` de string directo o desde `$Detalle` si es lista
  - [x] 4.4 Construir el sidecar con `variable_roles = list()` y `parameters = list()` vacíos; serializar con `jsonlite::toJSON(pretty=TRUE, auto_unbox=TRUE, null="null")`; escribir con `writeLines`
  - [x] 4.5 Implementar el loop principal con contadores `processed`, `skipped`, `failed` y el resumen final con `cat(sprintf(...))` para cada contador (Req 11.6)

- [x] 5. Crear `datalab_handler.py` — clase Python DataLabHandler
  - [x] 5.1 Crear el archivo `NEVEN/ControlPython/startup/datalab_handler.py` con la clase `DataLabHandler` e importaciones: `os`, `json`, `time`, `threading`; definir constantes `FUNCTIONS_DIR_DEFAULT = r"C:\NEVEN\functions"`, `CATALOG_TIMEOUT_MS = 2000`, y el set `REQUIRED_SIDECAR_FIELDS`
  - [x] 5.2 Implementar `handle_catalog(self, config)`: leer `functions_dir` de config; retornar catálogo vacío con advertencia si `not os.path.isdir(functions_dir)`; listar archivos `.json` con `os.listdir`; verificar timeout `(time.time()*1000 - start_ms) > CATALOG_TIMEOUT_MS` en cada iteración
  - [x] 5.3 En `handle_catalog`: validar campos obligatorios; validar que params `type=="select"` tengan `options` con `value` y `label` (advertencia, no rechazo); agregar advertencia (sin rechazar) si el archivo fuente indicado en `"file"` no existe; inyectar `card["_source_file"] = fpath`
  - [x] 5.4 En `handle_catalog`: agrupar con `catalog.setdefault(lang, {}).setdefault(family, []).append(card)` para cada idioma; retornar `{"status":"ok","catalog":catalog,"warnings":warnings,"scan_time_ms":scan_time}`
  - [x] 5.5 Implementar `handle_run(self, body, config, db, db_lock, get_pipe_client)`: extraer campos; retornar `VALIDATION_ERROR` si `function_id` vacío o `language != "r"`; verificar tabla `dataset` en DuckDB bajo `db_lock`; retornar `NO_DATASET` si falla; construir `all_columns` deduplicando desde `column_roles`; retornar `VALIDATION_ERROR` si `all_columns` vacío
  - [x] 5.6 En `handle_run`: construir SQL con columnas entre comillas dobles y `WHERE filter_clause` opcional; ejecutar con `db_lock`; retornar `FILTER_ERROR` con mensaje de excepción DuckDB si falla
  - [x] 5.7 En `handle_run`: serializar filas a JSON (`json.dumps(rows_as_dicts, default=str)`); escapar `\` y `'`; llamar `_build_r_script`; obtener `client = get_pipe_client("r")` (retornar `ENGINE_UNAVAILABLE` en `KeyError`); llamar `client.send_code(r_lines, wait=True)` (retornar `ENGINE_UNAVAILABLE` en timeout, `R_ERROR` en otros errores)
  - [x] 5.8 En `handle_run`: convertir resultado con `variable_to_python(var)` y `_parse_slots_from_variable(raw)`; retornar `{"status":"ok","slots":slots,"execution_time_ms":exec_time}`
  - [x] 5.9 Implementar `_build_r_script(self, function_id, column_roles, parameters, json_escaped, col_names)`: generar líneas `data_json`, `fromJSON`, `as.data.frame`, `data_X`; construir llamada al wrapper con parámetros nombrados (bool → `TRUE`/`FALSE`, str → comillas simples, número → literal); la última línea asigna `result <- {function_id}.Studio(data_X, ...)`
  - [x] 5.10 Implementar `_parse_slots_from_variable(self, raw)`: construir `idx = {c.lower(): i for i, c in enumerate(cols)}`; iterar rows; deserializar `value` con `json.loads` si es string; retornar lista de dicts Slot; retornar `[]` ante cualquier `KeyError`, `IndexError` o `json.JSONDecodeError`

- [x] 6. Modificar `neven_http_server.py` — agregar rutas Data Lab
  - [x] 6.1 Agregar bloque de importación condicional después de los imports existentes: `try: from datalab_handler import DataLabHandler as _DataLabHandler; _datalab_handler = _DataLabHandler(); _DATALAB_AVAILABLE = True` / `except ImportError: _DATALAB_AVAILABLE = False`
  - [x] 6.2 Agregar la clave `"functions_dir": r"C:\NEVEN\functions"` al diccionario `DEFAULT_CONFIG`
  - [x] 6.3 Agregar rama en `do_GET` antes del bloque de archivos estáticos: `if path == 'api/datalab/catalog':` verificar `_DATALAB_AVAILABLE` (retornar 503 si no); llamar `handle_catalog(_config)` y `self._send_json(result)`; `return`
  - [x] 6.4 Agregar rama `elif path == 'api/datalab/run':` en `do_POST` (después de `api/rpivot`): verificar `_DATALAB_AVAILABLE`; llamar `handle_run(body, _config, _get_db(), _db_lock, self._get_pipe_client)`; `status_code = 200 if result.get("status") == "ok" else 400`; `self._send_json(result, status_code)`

- [x] 7. Modificar `taskpane.html` — agregar pestaña Data Lab
  - [x] 7.1 Agregar `<div class="tab" data-tab="data-lab">Data Lab</div>` en la barra de tabs, después del tab `data-tab="run-script"` existente
  - [x] 7.2 Agregar el `div.tab-content#data-lab` completo antes del cierre `</body>`: incluir `#dl-no-dataset`, `#dl-selector-card` (familia dropdown + spinner + bloque de error con botón Reintentar + lista de funciones + row de idioma), `#dl-column-panel` (lista de columnas + slots de roles), `#dl-param-card` (tier1 + `<details id="dl-param-advanced">` para avanzados), `#dl-filter-card`, `#dl-run-row`, `#dl-results-panel`
  - [x] 7.3 Agregar `<script src="datalab.js"></script>` antes del cierre `</body>`, después de los scripts existentes
  - [x] 7.4 En el listener de tabs existente agregar: `if (tab.dataset.tab === 'data-lab') { setTimeout(onDataLabTabActivated, 50); }` para disparar la introspección del dataset al activar la pestaña

- [x] 8. Crear `datalab.js` — módulo JavaScript para Data Lab UI
  - [x] 8.1 Crear `NEVEN/TaskPane/datalab.js` con `_DL_API = window.location.origin` y el objeto `_dlState` con campos: `catalog`, `selectedCard`, `columnRoles`, `parameters`, `datasetColumns`, `language`, `pendingColumn`
  - [x] 8.2 Implementar `initDataLab()`: registrar listeners para `dl-retry-catalog`, `dl-family-select`, `dl-run-btn`; llamar `loadCatalog()`
  - [x] 8.3 Implementar `onDataLabTabActivated()`: `await introspectDataset()`; `await loadCatalog()` solo si `_dlState.catalog` es null
  - [x] 8.4 Implementar `loadCatalog()`: mostrar spinner; ocultar error; `fetch('/api/datalab/catalog')`; en éxito llamar `renderFamilyDropdown`; en error mostrar `dl-catalog-error` con texto y botón Reintentar visible
  - [x] 8.5 Implementar `renderFamilyDropdown(catalog)`: deduplicar familias iterando `Object.values(catalog)` → `Object.entries(lang)`; poblar `#dl-family-select`; habilitar select
  - [x] 8.6 Implementar `onFamilyChange()`: llamar `clearFunctionSelection()`; recolectar cards de todos los idiomas para la familia seleccionada; renderizar un `<button>` por función con nombre y descripción en `#dl-function-list`
  - [x] 8.7 Implementar `selectFunction(card)`: actualizar estado; resaltar botón; llamar `renderLanguageSelector`, `renderColumnPanel`, `renderParameterForm`; mostrar `dl-filter-card` y `dl-run-row`; llamar `updateRunButtonState()`
  - [x] 8.8 Implementar `clearFunctionSelection()`: resetear `_dlState`; ocultar todos los paneles; limpiar `dl-results-content`
  - [x] 8.9 Implementar `introspectDataset()`: `POST /api/query` con `SELECT * FROM dataset LIMIT 0`; `POST /api/analyze`; poblar `_dlState.datasetColumns` con `{name, type}` (`'numeric'` o `'text'`); mostrar/ocultar `dl-no-dataset`; retornar `true`/`false`
  - [x] 8.10 Implementar `renderColumnPanel(card)`: crear un `div.dl-col-chip` por columna con listener `onColumnChipClick`; crear un `div.dl-role-slot` por Variable_Role con label (`*` si required), `div#dl-role-chips-{roleKey}`, `div#dl-role-err-{roleKey}`, listener `onRoleSlotClick`
  - [x] 8.11 Implementar `onColumnChipClick(colName, colType)`: resetear bordes; resaltar chip; guardar `_dlState.pendingColumn`
  - [x] 8.12 Implementar `onRoleSlotClick(roleKey, roleDef)`: verificar `pendingColumn`; validar tipo contra `roleDef.types`; manejar `multiple: false` (reemplazar) vs `multiple: true` (agregar sin duplicar); limpiar `pendingColumn`; `renderRoleChips`; `updateRunButtonState()`
  - [x] 8.13 Implementar `renderRoleChips(roleKey)`: limpiar contenedor; crear chip por columna con botón `×` que llama `removeRoleColumn`
  - [x] 8.14 Implementar `removeRoleColumn(roleKey, colName)`: filtrar array; `renderRoleChips`; `updateRunButtonState()`
  - [x] 8.15 Implementar `renderParameterForm(card)`: por cada parámetro inicializar `_dlState.parameters[name] = default`; crear fila con label + control según tipo: `integer` → `<input type="number" step="1">` con validación (null si no-entero); `boolean` → `<input type="checkbox">`; `select` → `<select>` con options; tier 1 → `dl-param-tier1`; tier 2 → `dl-param-tier2`; mostrar/ocultar `dl-param-advanced`
  - [x] 8.16 Implementar `renderLanguageSelector(card)`: si `languages.length <= 1` → ocultar row y fijar `_dlState.language`; si > 1 → mostrar row, poblar select, listener actualiza `_dlState.language`
  - [x] 8.17 Implementar `updateRunButtonState()`: deshabilitar si sin `selectedCard` o sin `datasetColumns`; deshabilitar si `validateRoles(false)` es false; deshabilitar si algún parámetro es `null`
  - [x] 8.18 Implementar `validateRoles(showErrors)`: verificar que cada rol `required: true` tiene `length > 0` asignado; llamar `showRoleError` si `showErrors`; retornar booleano
  - [x] 8.19 Implementar `runAnalysis()`: validar roles; deshabilitar botón + mostrar spinner; construir body; `POST /api/datalab/run`; en error mostrar en `dl-results-error`; en éxito `renderResults(data.slots)`; en finally re-habilitar botón
  - [x] 8.20 Implementar `renderResults(slots)`: limpiar contenedor; separar tier1 y tier2; renderizar tier1 directamente con `buildSlotElement`; si hay tier2, crear `<details>` sin `open` con `<summary>Detalles técnicos</summary>`
  - [x] 8.21 Implementar `buildSlotElement(slot)`: heading con `slot.label || slot.name`; según `slot.type`: `table` → `renderSlotTable`; `html` → `<iframe srcdoc sandbox="allow-scripts allow-same-origin">`; `vector`/`scalar`/`text`/default → `<pre>` con valor como string
  - [x] 8.22 Implementar `renderSlotTable(rows)`: si vacío retornar `<p>Sin datos.</p>`; `<table class="data-table">` con `<thead>` y `<tbody>` envueltos en `<div style="overflow:auto;max-height:300px">`

- [x] 9. Tests para el serializador R y el handler Python
  - [x] 9.1 Crear `NEVEN/tests/test_r_object_to_slots.R` con `testthat`: tests de detección de tipo para `data.frame`, `matrix`, string `<html>` (case-insensitive), vector length > 1, escalar, lista anidada; tests de tier por defecto = `1L`; test de override con `tier_map`; test de round-trip de nombres (`names(obj)` == `slots$name`)
  - [x] 9.2 Escribir test de propiedad (Property 2) en `testthat` para `.neven_dl_detect_type`: verificar para 6 tipos de input distintos que el tipo asignado es el correcto según orden de prioridad
  - [x] 9.3 Escribir test de propiedad (Property 3) en `testthat`: construir 5 listas nombradas distintas y verificar `all(r_object_to_slots(obj)$tier == 1L)` en cada una
  - [x] 9.4 Crear `NEVEN/tests/test_datalab_handler.py` con `pytest` y fixtures `tmp_path`: `test_handle_catalog_empty_dir`, `test_handle_catalog_valid_sidecar`, `test_handle_catalog_missing_field`, `test_handle_catalog_invalid_json`, `test_handle_catalog_nonexistent_dir`, `test_handle_catalog_select_param_no_options`
  - [x] 9.5 Agregar tests para `handle_run` en `test_datalab_handler.py`: `test_handle_run_missing_function_id` → VALIDATION_ERROR; `test_handle_run_unsupported_language` → VALIDATION_ERROR; `test_handle_run_no_dataset` → NO_DATASET; `test_handle_run_no_columns_assigned` → VALIDATION_ERROR; `test_handle_run_invalid_filter` → FILTER_ERROR; `test_handle_run_engine_unavailable` → ENGINE_UNAVAILABLE
  - [x] 9.6 Escribir test de propiedad (Property 1) con `hypothesis`: `@given(st.lists(sidecar_strategy(), min_size=0, max_size=20))` donde `sidecar_strategy` genera sidecars válidos e inválidos; verificar que solo los válidos aparecen en el catálogo y los inválidos están en `warnings`
  - [x] 9.7 Escribir test de propiedad (Property 6) con `hypothesis`: `@given(st.text().filter(lambda s: s.strip()))` para filter_clause; mock db que lanza en `WHERE`; verificar que `pipe_client.send_code` nunca es invocado
  - [x] 9.8 Escribir test de propiedad (Property 8) con `hypothesis`: `@given(slot_list_strategy())` con slots de tipos y valores variados; verificar que `json.dumps({"status":"ok","slots":slots})` no lanza excepción

- [x] 10. Familia UC — funciones de ejemplo y guía de extensibilidad
  - [x] 10.1 Crear `NEVEN/libreria/R/UC_EjemploBasico.Studio.R` con la función `UC_EjemploBasico.Studio(data_X, Precision=2L)`: calcular estadísticas descriptivas (N, Media, Mediana, Desv_Std, Min, Max) por columna numérica; retornar `r_object_to_slots(list(estadisticas=stats_df), tier_map=c(estadisticas=1L))`
  - [x] 10.2 Crear `NEVEN/Install/functions/UC_EjemploBasico.json`: `"id": "UC_EjemploBasico"`, `"family": "UC"`, `"family_label": "Mis Funciones"`, rol X numérico múltiple requerido, parámetro `Precision` (integer, default 2, tier 1)
  - [x] 10.3 Crear `NEVEN/libreria/R/UC_EjemploAvanzado.Studio.R` con la función `UC_EjemploAvanzado.Studio(data_Y, data_X, Metodo=1L, Escala=FALSE, MostrarGrafico=TRUE)`: correlaciones de Y con cada X (Pearson/Spearman/Kendall), tabla de resultados con `Correlacion`, `p_value`, `Significancia`; gráfico de barras horizontales con plotly serializado como `<neven-plotly>BASE64</neven-plotly>`; retornar tier 1 para ambos slots
  - [x] 10.4 Crear `NEVEN/Install/functions/UC_EjemploAvanzado.json`: roles Y (numérico, single, requerido) y X (numérico, múltiple, requerido); parámetros `Metodo` (select Pearson/Spearman/Kendall, tier 1), `MostrarGrafico` (boolean, tier 1), `Escala` (boolean, tier 2)
  - [x] 10.5 Crear `NEVEN/libreria/R/UC_EjemploFactoMineR.Studio.R` con la función `UC_EjemploFactoMineR.Studio(data_X, N_Comp=0L, Escala=TRUE, Top_Variables=10L)`: verificar `requireNamespace("FactoMineR")`; ejecutar `FactoMineR::PCA()`; retornar slots: `varianza_explicada` (table, tier 1), `biplot` (html con neven-plotly, tier 1), `coordenadas_vars` (table, tier 1), `contribuciones` (table, tier 2), `calidad_repr` (table, tier 2), `scores_individuos` (table, tier 2)
  - [x] 10.6 Crear `NEVEN/Install/functions/UC_EjemploFactoMineR.json`: rol X numérico múltiple requerido; parámetros `N_Comp` (integer, default 0, tier 1), `Escala` (boolean, default true, tier 1), `Top_Variables` (integer, default 10, tier 2)
  - [x] 10.7 Crear `NEVEN/Install/functions/COMO_AGREGAR_FUNCIONES.md`: guía en español que explica la convención de dos archivos (`.Studio.R` + `.json`), estructura del wrapper con `r_object_to_slots`, estructura del sidecar JSON con todos los tipos de parámetro y roles, tabla de familias predefinidas, patrón de gráfico con `<neven-plotly>`, y referencia a los tres archivos de ejemplo UC

- [x] 11. Familia AD — funciones adicionales de Análisis de Datos
  - [x] 11.1 Crear `NEVEN/libreria/R/R4XCL-AD-ACP.Studio.R` con la función `AD_ACP.Studio(data_X, Escala=TRUE, N_Componentes=0L)`: ejecutar `prcomp(data_num, scale.=Escala)`; retornar slots: varianza explicada (table, tier 1), cargas por componente (table, tier 1), biplot interactivo con plotly (html, tier 1), scores de individuos (table, tier 2)
  - [x] 11.2 Crear `NEVEN/Install/functions/R4XCL-AD-ACP.json`: `"id": "AD_ACP"`, `"family": "AD"`, `"family_label": "Análisis de Datos"`, `"name": "Componentes Principales"`, rol X numérico múltiple requerido; parámetros `Escala` (boolean, default true, tier 1), `N_Componentes` (integer, default 0, tier 1)
  - [x] 11.3 Crear `NEVEN/libreria/R/R4XCL-AD-ClusteringJerarquico.Studio.R` con la función `AD_ClusteringJerarquico.Studio(data_X, K=3L, Escala=TRUE, Metodo=1L, Distancia=1L)`: calcular matriz de distancias (`dist()` con euclidiana o manhattan); ejecutar `hclust()`; cortar árbol con `cutree(hclust_obj, k=K)`; retornar slots: tabla de asignaciones de clusters (tier 1), tabla de tamaños por cluster (tier 1), dendrograma como html con plotly (tier 1), matriz de distancias entre centroides (tier 2)
  - [x] 11.4 Crear `NEVEN/Install/functions/R4XCL-AD-ClusteringJerarquico.json`: `"id": "AD_ClusteringJerarquico"`, `"family": "AD"`, rol X numérico múltiple requerido; parámetros `K` (integer, default 3, tier 1), `Escala` (boolean, default true, tier 1), `Metodo` (select Ward.D2/Complete/Average/Single con values 1/2/3/4, tier 1), `Distancia` (select Euclidiana/Manhattan, tier 2)

- [x] 12. Familia RG — funciones de Regresión
  - [x] 12.1 Crear `NEVEN/libreria/R/R4XCL-RG-Lineal.Studio.R` con la función `RG_Lineal.Studio(data_Y, data_X, Escala=FALSE, Constante=TRUE)`: ajustar `lm()`; retornar slots: tabla de coeficientes con p-values y significancia (table, tier 1), métricas de ajuste R², R² ajustado, AIC, BIC, RMSE (table, tier 1), gráfico de residuos vs valores ajustados con plotly (html, tier 1), estadístico F y p-value global (scalar, tier 2)
  - [x] 12.2 Crear `NEVEN/Install/functions/R4XCL-RG-Lineal.json`: `"id": "RG_Lineal"`, `"family": "RG"`, `"family_label": "Regresion"`, roles Y (numérico, single) y X (numérico, múltiple); parámetros `Escala` (boolean, default false, tier 1), `Constante` (boolean, default true, tier 1)
  - [x] 12.3 Crear `NEVEN/libreria/R/R4XCL-RG-Logistica.Studio.R` con la función `RG_Logistica.Studio(data_Y, data_X, ...)`: ajustar `glm(..., family=binomial)`; retornar coeficientes con odds ratios, métricas de clasificación (accuracy, AUC, matriz de confusión), curva ROC como html
  - [x] 12.4 Crear `NEVEN/Install/functions/R4XCL-RG-Logistica.json`: `"id": "RG_Logistica"`, `"family": "RG"`, roles Y (numérico/texto, single) y X (numérico, múltiple)
  - [x] 12.5 Crear `NEVEN/libreria/R/R4XCL-RG-ArbolDecision.Studio.R` con la función `RG_ArbolDecision.Studio(data_Y, data_X, ...)`: ajustar árbol de decisión con `rpart`; retornar importancia de variables, reglas del árbol como tabla, visualización del árbol como html
  - [x] 12.6 Crear `NEVEN/Install/functions/R4XCL-RG-ArbolDecision.json`: `"id": "RG_ArbolDecision"`, `"family": "RG"`
  - [x] 12.7 Crear `NEVEN/libreria/R/R4XCL-RG-DatosPanel.Studio.R` con la función `RG_DatosPanel.Studio(data_Y, data_X, data_ID, data_T, ...)`: ajustar modelo de efectos fijos o aleatorios con `plm`; retornar coeficientes, test de Hausman
  - [x] 12.8 Crear `NEVEN/Install/functions/R4XCL-RG-DatosPanel.json`: `"id": "RG_DatosPanel"`, `"family": "RG"`, roles Y, X, ID (individuo), T (tiempo)
  - [x] 12.9 Crear `NEVEN/libreria/R/R4XCL-RG-Poisson.Studio.R` con la función `RG_Poisson.Studio(data_Y, data_X, ...)`: ajustar `glm(..., family=poisson)`; retornar coeficientes con IRR (incidence rate ratios), bondad de ajuste, estadístico de sobredispersión
  - [x] 12.10 Crear `NEVEN/Install/functions/R4XCL-RG-Poisson.json`: `"id": "RG_Poisson"`, `"family": "RG"`, roles Y (numérico, conteo) y X (numérico, múltiple)
  - [x] 12.11 Crear `NEVEN/libreria/R/R4XCL-RG-SeriesTiempo.Studio.R` con la función `RG_SeriesTiempo.Studio(data_Y, ...)`: ajustar modelo ARIMA automático con `forecast::auto.arima()`; retornar pronóstico, métricas de error, gráfico de serie y pronóstico con plotly
  - [x] 12.12 Crear `NEVEN/Install/functions/R4XCL-RG-SeriesTiempo.json`: `"id": "RG_SeriesTiempo"`, `"family": "RG"`, rol Y (numérico, single)
  - [x] 12.13 Crear `NEVEN/libreria/R/R4XCL-RG-SVM.Studio.R` con la función `RG_SVM.Studio(data_Y, data_X, ...)`: ajustar SVM con `e1071::svm()`; retornar métricas de clasificación/regresión, parámetros del kernel, vectores de soporte
  - [x] 12.14 Crear `NEVEN/Install/functions/R4XCL-RG-SVM.json`: `"id": "RG_SVM"`, `"family": "RG"`, roles Y y X
  - [x] 12.15 Crear `NEVEN/libreria/R/R4XCL-RG-Tobit.Studio.R` con la función `RG_Tobit.Studio(data_Y, data_X, ...)`: ajustar modelo Tobit con `AER::tobit()`; retornar coeficientes, efectos marginales, métricas de ajuste de log-verosimilitud
  - [x] 12.16 Crear `NEVEN/Install/functions/R4XCL-RG-Tobit.json`: `"id": "RG_Tobit"`, `"family": "RG"`, roles Y (censurada) y X (covariables)

- [x] 13. Familia DS — función de dataset Wooldridge
  - [x] 13.1 Crear `NEVEN/libreria/R/R4XCL-DS-Wooldridge.Studio.R` con la función `DS_Wooldridge.Studio(Dataset="wage1")`: cargar el dataset desde el paquete `wooldridge` con `data(list=Dataset, package="wooldridge", envir=env)`; retornar slots: los datos como tabla (tier 1), resumen descriptivo del dataset (table, tier 2), metadata (nombre, N filas, N columnas como scalars, tier 2)
  - [x] 13.2 Crear `NEVEN/Install/functions/R4XCL-DS-Wooldridge.json`: `"id": "DS_Wooldridge"`, `"family": "DS"`, `"family_label": "Conjuntos de Datos"`, `"name": "Datos Wooldridge"`, `"variable_roles": {}` (sin roles — esta función no consume columnas del dataset activo); parámetro `Dataset` (select con los datasets disponibles del paquete wooldridge, default `"wage1"`, tier 1)

- [x] 14. Familia TM — función de análisis de texto en Python
  - [x] 14.1 Crear `NEVEN/Install/functions/TM_TextAnalysis.Studio.py` con la función `TM_TextAnalysis(Ruta_Archivo="", Max_Paginas=0, N_Resumen=5, N_Palabras=25)`: leer documento PDF (con `pypdf`), TXT o DOCX según extensión; calcular estadísticas léxicas (palabras totales, únicas, oraciones, riqueza léxica); análisis de sentimiento básico; resumen extractivo (top N oraciones por TF-IDF); frecuencia de palabras con gráfico de barras plotly; retornar slots vía la convención Python equivalente a `r_object_to_slots`
  - [x] 14.2 Crear `NEVEN/Install/functions/TM_TextAnalysis.json`: `"id": "TM_TextAnalysis"`, `"family": "TM"`, `"family_label": "Text Mining"`, `"languages": ["python"]`, `"function_name": "TM_TextAnalysis"`, `"file": "TM_TextAnalysis.Studio.py"`, `"variable_roles": {}` (sin roles — usa parámetro de ruta en lugar de columnas del dataset); parámetros `Ruta_Archivo` (type `"text"`, tier 1), `Max_Paginas` (integer, default 0, tier 1), `N_Resumen` (integer, default 5, tier 2), `N_Palabras` (integer, default 25, tier 2)

- [ ] 15. Tests para las nuevas funciones del catálogo expandido
  - [ ] 15.1 Crear `NEVEN/tests/test_uc_funciones.R` con `testthat`: tests unitarios para `UC_EjemploBasico.Studio` (verificar columnas del data.frame de salida, manejo de NAs, error con datos no numéricos); tests para `UC_EjemploAvanzado.Studio` (verificar tabla de correlaciones, slot de gráfico tipo html, manejo de Y y X con distinto número de filas)
  - [ ] 15.2 Agregar tests en `test_uc_funciones.R` para `UC_EjemploFactoMineR.Studio`: verificar que el slot `varianza_explicada` tiene columnas `Componente`, `Varianza_Pct`, `Varianza_Acum_Pct`; verificar que `biplot` es tipo html; verificar manejo de error cuando FactoMineR no está instalado (mock con `requireNamespace`)
  - [ ] 15.3 Crear `NEVEN/tests/test_ad_funciones.R` con `testthat`: tests para `AD_ACP.Studio` (varianza acumulada ≤ 100%, número de componentes respetado); tests para `AD_ClusteringJerarquico.Studio` (K clusters en la asignación, manejo de Métodos 1-4, manejo de Distancias 1-2)
  - [ ] 15.4 Crear `NEVEN/tests/test_rg_funciones.R` con `testthat`: tests para `RG_Lineal.Studio` (coeficientes con nombres de columnas X, R² en rango [0,1], slot de residuos presente); tests para `RG_Logistica.Studio` (odds ratios positivos, AUC en rango [0,1]); tests para `RG_Poisson.Studio` (IRR > 0)
  - [ ] 15.5 Crear `NEVEN/tests/test_ds_wooldridge.R` con `testthat`: verificar que `DS_Wooldridge.Studio("wage1")` retorna una tabla con N > 0 filas y columnas esperadas del dataset wage1; verificar que un nombre de dataset inválido retorna error descriptivo; verificar que el slot de metadata contiene el nombre del dataset
  - [ ] 15.6 Crear `NEVEN/tests/test_tm_textanalysis.py` con `pytest`: tests para `TM_TextAnalysis` con un archivo TXT de prueba (verificar slots de estadísticas léxicas, resumen y frecuencia de palabras); test de manejo de archivo inexistente (retornar error descriptivo, no excepción no controlada); test de archivo PDF con `Max_Paginas=1`

- [x] 16. Mejoras a `TM_TextAnalysis.Studio.py` — resumen LLM, WordCloud y corrección de saltos de línea
  - [x] 16.1 Corregir saltos de línea en texto extraído de PDF: aplicar regex `(?<![.!?\n])\n(?!\n)` → espacio para unir palabras partidas por layout físico del PDF (PyPDF2 extrae línea a línea); colapsar 3+ `\n` → `\n\n`; eliminar espacios múltiples
  - [x] 16.2 Cambiar slot `resumen` de `type: scalar` a `type: html`; construir lista `<ol>` con cada oración como `<li>` con `line-height:1.6`; limpiar `\n` residuales en cada oración antes de insertarla
  - [x] 16.3 Implementar `_build_llm_summary(texto, nombre_archivo)`: leer config AI desde `neven-config.json`; truncar texto a 500 palabras (límite de contexto del modelo nano); construir prompt bilingüe (instrucciones en inglés, respuesta en español); llamar `urllib.request` al endpoint LMStudio; retornar slot `resumen_llm` tipo `html` con Markdown convertido a HTML; degradación graceful — retorna `None` si LMStudio no está disponible
  - [x] 16.4 Implementar `_md_to_html(md)`: convertir encabezados `#`/`##`/`###`, negrita `**`, itálica `*`, listas `-`/`*`, y párrafos separados por `\n\n` a HTML limpio con estilos del tema oscuro de NEVEN
  - [x] 16.5 Insertar slot `resumen_llm` antes del `resumen` extractivo TF-IDF cuando el LLM responde; si no responde, omitir silenciosamente (sin slot de error en producción)
  - [x] 16.6 Implementar `_build_wordcloud(freq_data, titulo)`: distribuir las 40 palabras más frecuentes en espiral de Arquímedes usando Plotly scatter con texto; tamaño de fuente proporcional a frecuencia (escala raíz); paleta de colores dorada NEVEN; retornar slot `wordcloud` tipo `html` vía `<neven-plotly>`
  - [x] 16.7 Agregar slot `wordcloud` ("Nube de palabras") a la lista de resultados, tier 1, después del gráfico de barras de frecuencia

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "3", "4", "7"] },
    { "wave": 2, "tasks": ["2"] },
    { "wave": 3, "tasks": ["5"] },
    { "wave": 4, "tasks": ["6", "8"] },
    { "wave": 5, "tasks": ["9"] },
    { "wave": 6, "tasks": ["10", "11", "12", "13", "14"] },
    { "wave": 7, "tasks": ["15", "16"] }
  ]
}
```

## Notes

- Los archivos de producción se copian a `C:\NEVEN\` durante el despliegue; los paths relativos del repositorio son los que se editan durante el desarrollo.
- `r_object_to_slots.R` se carga en el startup de ControlR.exe — cualquier cambio requiere reiniciar ControlR para tener efecto.
- La integración end-to-end (JS → Python → R → ControlR) no está cubierta por los tests automatizados de esta tarea; los tests de la tarea 9 son unit/property tests que usan mocks para el pipe client y DuckDB.
- El sidecar JSON debe copiarse a `C:\NEVEN\functions\` para que `handle_catalog` lo descubra en producción.
- `migrate_attr_to_json.R` es un script one-shot; no se integra en el build ni en los tests automatizados.
- Las funciones UC (tareas 10.1–10.6) sirven como plantillas de referencia para usuarios que deseen agregar sus propias funciones al catálogo. `COMO_AGREGAR_FUNCIONES.md` (tarea 10.7) documenta el patrón completo.
- Las funciones RG de la tarea 12 dependen de paquetes externos (plm, AER, e1071, rpart, forecast); se asume que están instalados en el entorno R de producción.
- `DS_Wooldridge.Studio` (tarea 13) no requiere un dataset cargado en DuckDB — es una función de carga, no de análisis. El handler Python maneja el caso donde `variable_roles` es `{}` y `column_roles` está vacío sin retornar `VALIDATION_ERROR`.
- `TM_TextAnalysis.Studio.py` (tarea 14) es la primera función Python del catálogo. El resumen LLM (tarea 16) requiere LMStudio corriendo localmente con un modelo cargado.
- Los tests de la tarea 15 son el único trabajo pendiente en el spec; todas las demás tareas (1–14, 16) están completadas.
- El límite de 500 palabras en el extracto enviado al LLM (tarea 16) está condicionado por la ventana de contexto del modelo `nvidia/nemotron-3-nano-4b` (~4096 tokens). Modelos con mayor contexto pueden usar extractos más largos.
