# Ontología NEVEN v2 — Tareas

## Paso 1 — Auditoría del catálogo existente

- [ ] **1.1** Leer todos los `*.json` sidecars de `C:\NEVEN\functions\` y extraer: `id`, `family`, `name`, `description`, `variable_roles`, `parameters`, `languages`, `file`
- [ ] **1.2** Leer cabeceras de todos los `*.R` XLL (`R4XCL-*.R`) y extraer: nombre de función, parámetros, librerías usadas (`library()` / `requireNamespace()`), `TipoOutput` disponibles
- [ ] **1.3** Construir `functions_catalog.json` — inventario unificado con ambos tipos de función
- [ ] **1.4** Identificar el mapeo XLL ↔ Studio: qué función XLL corresponde a qué Studio (ej: `MR_Lineal` ↔ `RG_Lineal`)

## Paso 2 — Inventario de librerías

- [ ] **2.1** Extraer lista de librerías únicas usadas en todos los archivos de `functions/`
- [ ] **2.2** Por cada librería, documentar funciones adicionales relevantes no expuestas en NEVEN
- [ ] **2.3** Marcar cuáles están instaladas vs cuáles requieren instalación
- [ ] **2.4** Agregar este inventario a `kg_function_map.json` como sección `"libraries"`

## Paso 3 — Catálogo dinámico en el servidor

- [ ] **3.1** Crear `catalog_loader.py` — módulo que lee `*.json` de `functions/` al arrancar y construye el catálogo en memoria
- [ ] **3.2** Integrar el catálogo en `_build_system_prompt()` — el prompt del agente incluye la lista completa de `function_id` disponibles con descripción breve
- [ ] **3.3** Actualizar el `_run_hint` para que el listado de `function_id` venga del catálogo dinámico en lugar de estar hardcodeado
- [ ] **3.4** Agregar instrucciones al agente sobre el árbol de decisión (R3 del spec)

## Paso 4 — Sugerencias con código concreto

- [ ] **4.1** El agente debe incluir en su respuesta la fórmula Excel exacta cuando sugiere una función XLL: `=R.MR_Lineal(A1:A50, B1:C50, TipoOutput=2)`
- [ ] **4.2** Cuando propone un wrapper nuevo, el agente genera el código completo de `MiFuncion.Studio.R` + `MiFuncion.json` siguiendo el protocolo de `COMO_AGREGAR_FUNCIONES.md`
- [ ] **4.3** El agente distingue entre "función disponible ahora" vs "requiere nuevo archivo en functions/"

## Paso 5 — Actualización periódica (mecanismo)

- [ ] **5.1** Documentar en `MANUAL_MANTENIMIENTO.md` el proceso para agregar una función nueva y que el agente la descubra automáticamente
- [ ] **5.2** El endpoint `GET /api/datalab/catalog` ya existe — verificar que retorna el catálogo que usará el agente
