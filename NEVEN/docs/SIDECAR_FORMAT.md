# Formato de Archivos Sidecar JSON para Funciones NevenX

Este documento describe el formato JSON requerido para registrar funciones en NEVEN.
Los archivos sidecar permiten que las funciones aparezcan en el Diccionario de Funciones
del Task Pane y sean ejecutables desde Excel o DataLab.

---

## Tipos de Funciones

| Tipo | Descripción | Campos adicionales |
|------|-------------|-------------------|
| **DataLab-only** | Solo ejecutable desde NEVEN Studio (Task Pane) | Campos base |
| **XLL-callable** | Ejecutable desde celdas Excel con `=NEVEN.R()` | `function_name_xll`, `nevenx_positions` |

---

## Estructura Base (Todos los Campos)

```json
{
  "id": "RG_Lineal",
  "family": "RG",
  "family_label": "Regresion",
  "name": "Regresion Lineal",
  "description": "Descripcion clara de que hace la funcion...",
  "wikipedia_url": "https://es.wikipedia.org/wiki/...",
  "languages": ["r"],
  "function_name": "RG_Lineal.Studio",
  "function_name_xll": "MR_Lineal",
  "file": "R4XCL-RG-Lineal.Studio.R",
  "variable_roles": { ... },
  "parameters": [ ... ],
  "nevenx_positions": { ... },
  "tipo_outputs": [ ... ],
  "dependencies": { ... }
}
```

---

## Campos Requeridos

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | string | Identificador unico (sin espacios, usar guion bajo) |
| `family` | string | Codigo de familia: `RG`, `AD`, `ST`, `TM`, `GR`, `DS`, `UC` |
| `family_label` | string | Nombre legible de la familia |
| `name` | string | Nombre de la funcion para mostrar al usuario |
| `description` | string | Descripcion de 1-2 oraciones |
| `languages` | array | Lenguajes soportados: `["r"]`, `["python"]`, `["julia"]` |
| `function_name` | string | Nombre de la funcion en el codigo fuente |
| `file` | string | Archivo que contiene la implementacion |
| `tipo_outputs` | array | Lista de outputs disponibles con id y label |

## Campos Opcionales

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `wikipedia_url` | string | URL de Wikipedia para referencia |
| `variable_roles` | object | Roles de variables para DataLab (X, Y, Color, etc.) |
| `parameters` | array | Parametros configurables en DataLab |
| `dependencies` | object | Paquetes requeridos por lenguaje |

## Campos para Funciones XLL-callable

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `function_name_xll` | string | **REQUERIDO** para aparecer en Diccionario. Nombre usado en `=NEVEN.R("nombre", ...)` |
| `nevenx_positions` | object | **REQUERIDO** para XLL. Mapeo de posiciones a0, a1, ... a9 |

---

## Familias Disponibles

| Codigo | Label | Descripcion |
|--------|-------|-------------|
| `RG` | Regresion | Modelos de regresion (lineal, logistica, panel, etc.) |
| `AD` | Analisis de Datos | Clustering, PCA, arboles de decision |
| `ST` | Series de Tiempo | ARIMA, VAR, ECM, cointegration |
| `TM` | Text Mining | Analisis de texto, NLP |
| `GR` | Graficos | Visualizaciones (solo DataLab) |
| `DS` | Datasets | Datasets de ejemplo (Wooldridge, etc.) |
| `UC` | Use Cases | Ejemplos de uso completos |

---

## Detalle: `variable_roles`

Define como el usuario asigna columnas de datos en DataLab.

```json
"variable_roles": {
  "Y": {
    "label": "Variable dependiente (Y)",
    "types": ["numeric"],
    "multiple": false,
    "required": true
  },
  "X": {
    "label": "Variables independientes (X)",
    "types": ["numeric"],
    "multiple": true,
    "required": true
  },
  "Color": {
    "label": "Variable de agrupacion (opcional)",
    "types": ["text"],
    "multiple": false,
    "required": false
  }
}
```

| Propiedad | Tipo | Descripcion |
|-----------|------|-------------|
| `label` | string | Descripcion para el usuario |
| `types` | array | Tipos aceptados: `"numeric"`, `"text"` |
| `multiple` | boolean | Si acepta multiples columnas |
| `required` | boolean | Si es obligatorio |

---

## Detalle: `parameters`

Parametros configurables por el usuario en DataLab.

```json
"parameters": [
  {
    "name": "Escala",
    "label": "Escalar variables X",
    "type": "boolean",
    "default": false,
    "tier": 1
  },
  {
    "name": "Metodo",
    "label": "Metodo de estimacion",
    "type": "select",
    "default": 1,
    "tier": 1,
    "options": [
      { "value": 1, "label": "OLS" },
      { "value": 2, "label": "GLS" },
      { "value": 3, "label": "2SLS" }
    ]
  }
]
```

| Propiedad | Tipo | Descripcion |
|-----------|------|-------------|
| `name` | string | Nombre interno (usado en codigo) |
| `label` | string | Etiqueta para el usuario |
| `type` | string | `"boolean"`, `"integer"`, `"numeric"`, `"select"`, `"palette"` |
| `default` | any | Valor por defecto |
| `tier` | integer | 1=basico, 2=avanzado (controla visibilidad) |
| `options` | array | Solo para type="select" |

---

## Detalle: `nevenx_positions` (Solo XLL-callable)

Mapea las posiciones de argumentos en la formula Excel `=NEVEN.R("funcion", a0, a1, ..., TipoOutput)`.

```json
"nevenx_positions": {
  "a0": { "name": "SetDatosY",  "label": "Variable dependiente Y",   "type": "range",   "required": true,  "default": null },
  "a1": { "name": "SetDatosX",  "label": "Variables independientes", "type": "range",   "required": true,  "default": null },
  "a3": { "name": "Escala",     "label": "Estandarizar (0=No, 1=Si)","type": "boolean", "required": false, "default": 0 },
  "a4": { "name": "Filtro",     "label": "Excluir observaciones",    "type": "range",   "required": false, "default": null }
}
```

**Posiciones disponibles:** `a0` a `a9` (maximo 10 argumentos)

| Propiedad | Tipo | Descripcion |
|-----------|------|-------------|
| `name` | string | Nombre del parametro (usado internamente) |
| `label` | string | Descripcion para el usuario |
| `type` | string | `"range"` (rango Excel), `"boolean"` (0/1), `"numeric"`, `"text"` |
| `required` | boolean | Si es obligatorio |
| `default` | any | Valor por defecto (null para rangos opcionales) |

**Nota:** Las posiciones no necesitan ser consecutivas. Puedes usar a0, a1, a3, a5 saltando a2 y a4.

---

## Detalle: `tipo_outputs`

Lista de outputs disponibles. El usuario selecciona cual quiere con el ultimo argumento.

```json
"tipo_outputs": [
  { "id": 0,  "label": "Ayuda -- parametros de entrada y outputs disponibles" },
  { "id": 1,  "label": "Tabla OLS con stargazer (IC 95%)" },
  { "id": 2,  "label": "Prediccion dentro de muestra (Y ajustado)" },
  { "id": 11, "label": "Resumen summary() basico" },
  { "id": 13, "label": "Metricas estructuradas (Seccion, Parametro, Metrica, Valor)" }
]
```

**Convencion de IDs:**
- `0` = Ayuda/documentacion
- `1-10` = Outputs principales
- `11+` = Outputs secundarios/tecnicos

---

## Detalle: `dependencies`

Paquetes requeridos por lenguaje (opcional pero recomendado).

```json
"dependencies": {
  "R": ["plm", "stargazer", "jsonlite"],
  "Julia": [],
  "Python": ["pandas", "statsmodels"]
}
```

---

## Ejemplos Completos

### Ejemplo 1: Funcion XLL-callable (Regresion)

```json
{
  "id": "RG_MiRegresion",
  "family": "RG",
  "family_label": "Regresion",
  "name": "Mi Regresion Personalizada",
  "description": "Implementa un modelo de regresion con caracteristicas especiales.",
  "wikipedia_url": "https://es.wikipedia.org/wiki/Regresi%C3%B3n_lineal",
  "languages": ["r"],
  "function_name": "RG_MiRegresion.Studio",
  "function_name_xll": "MR_MiRegresion",
  "file": "RG_MiRegresion.Studio.R",
  "variable_roles": {
    "Y": { "label": "Variable dependiente", "types": ["numeric"], "multiple": false, "required": true },
    "X": { "label": "Variables independientes", "types": ["numeric"], "multiple": true, "required": true }
  },
  "parameters": [
    { "name": "Robusto", "label": "Errores robustos", "type": "boolean", "default": false, "tier": 1 }
  ],
  "nevenx_positions": {
    "a0": { "name": "SetDatosY", "label": "Variable Y", "type": "range", "required": true, "default": null },
    "a1": { "name": "SetDatosX", "label": "Variables X", "type": "range", "required": true, "default": null },
    "a2": { "name": "Robusto", "label": "Errores robustos (0/1)", "type": "boolean", "required": false, "default": 0 }
  },
  "tipo_outputs": [
    { "id": 0, "label": "Ayuda" },
    { "id": 1, "label": "Tabla de coeficientes" },
    { "id": 2, "label": "Predicciones" }
  ],
  "dependencies": { "R": ["sandwich", "lmtest"], "Julia": [], "Python": [] }
}
```

### Ejemplo 2: Funcion DataLab-only (Grafico)

```json
{
  "id": "GR_MiGrafico",
  "family": "GR",
  "family_label": "Graficos",
  "name": "Mi Grafico Personalizado",
  "description": "Genera una visualizacion interactiva con Plotly.",
  "languages": ["r"],
  "function_name": "GR_MiGrafico.Studio",
  "file": "GR_MiGrafico.Studio.R",
  "variable_roles": {
    "X": { "label": "Eje X", "types": ["numeric", "text"], "multiple": false, "required": true },
    "Y": { "label": "Eje Y", "types": ["numeric"], "multiple": true, "required": true }
  },
  "parameters": [
    { "name": "Titulo", "label": "Titulo del grafico", "type": "text", "default": "", "tier": 1 },
    { "name": "Paleta", "label": "Paleta de colores", "type": "palette", "default": 1, "tier": 1 }
  ],
  "tipo_outputs": [
    { "id": 0, "label": "Grafico interactivo Plotly" }
  ]
}
```

---

## Ubicacion de Archivos

| Archivo | Ubicacion |
|---------|-----------|
| Sidecar JSON | `C:\NEVEN\functions\{ID}.json` |
| Codigo R | `C:\NEVEN\libreria\R\{file}` |
| Codigo Julia | `C:\NEVEN\libreria\JULIA\{file}` |
| Codigo Python | `C:\NEVEN\libreria\PYTHON\{file}` |

---

## Validacion

Un sidecar valido debe cumplir:

1. **JSON valido** — Sin errores de sintaxis
2. **ID unico** — No repetir IDs existentes
3. **Archivo existe** — El `file` referenciado debe existir
4. **XLL consistente** — Si tiene `function_name_xll`, debe tener `nevenx_positions`
5. **Encoding UTF-8** — Guardar siempre en UTF-8 sin BOM

---

## Notas para el Agente IA

Cuando crees una nueva funcion:

1. El `id` debe ser unico y seguir el patron `{FAMILIA}_{NombreDescriptivo}`
2. El `function_name_xll` debe seguir el patron existente de la familia:
   - Regresion: `MR_*` (Multiple Regression)
   - Series de Tiempo: `ST_*`
   - Analisis de Datos: `AD_*`
   - Text Mining: `TM_*`
3. Siempre incluir `tipo_outputs` con al menos id=0 para ayuda
4. Usar encoding UTF-8 al guardar el archivo
5. Verificar que el archivo de codigo (.R, .py, .jl) exista antes de crear el sidecar

Ver `AGENT_INSTRUCTIONS.md` para el proceso completo de creacion de funciones.
