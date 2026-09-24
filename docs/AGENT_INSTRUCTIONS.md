# Instrucciones para el Agente IA: Creación de Funciones NevenX

Este documento define el proceso que debe seguir el agente IA de NEVEN
(Excel Consultant, Econometrics Consultant) cuando el usuario solicita
crear una nueva función estadística o de análisis.

---

## Cuándo Aplica Este Proceso

El usuario puede solicitar crear una función de varias formas:

- "Crea una función para calcular el test de Durbin-Watson"
- "Necesito una función de regresión cuantílica"
- "Implementa el método de Heckman para sesgo de selección"
- "Quiero agregar análisis de componentes independientes (ICA)"

---

## Proceso de Creación (7 Pasos)

### Paso 1: Confirmar Requerimientos

Antes de escribir código, confirmar con el usuario:

1. **Nombre descriptivo** de la función
2. **Lenguaje preferido**: R (default), Python, o Julia
3. **Inputs esperados**: ¿Qué variables necesita? (Y, X, series de tiempo, etc.)
4. **Outputs deseados**: ¿Qué resultados debe retornar? (coeficientes, tests, gráficos)
5. **Callable desde Excel**: ¿Solo DataLab o también desde celdas con `=NEVEN.R()`?

**Ejemplo de respuesta al usuario:**
> Voy a crear la función de regresión cuantílica. Confirmo:
> - Lenguaje: R (usando el paquete `quantreg`)
> - Inputs: Variable Y (dependiente), Variables X (independientes), Cuantil (τ)
> - Outputs: Tabla de coeficientes, intervalos de confianza, gráfico de cuantiles
> - Será callable desde Excel con `=NEVEN.R("MR_Quantile", ...)`
> 
> ¿Está correcto?

---

### Paso 2: Determinar Identificadores

Generar los identificadores siguiendo las convenciones:

| Campo | Convención | Ejemplo |
|-------|------------|---------|
| `id` | `{FAMILIA}_{NombreCorto}` | `RG_QuantileRegression` |
| `family` | Código de 2 letras | `RG` |
| `function_name` | `{ID}.Studio` | `RG_QuantileRegression.Studio` |
| `function_name_xll` | Prefijo de familia + nombre | `MR_Quantile` |
| `file` | `{ID}.Studio.{ext}` | `RG_QuantileRegression.Studio.R` |

**Prefijos XLL por familia:**
- `RG` (Regresión) → `MR_*` (Multiple Regression)
- `ST` (Series de Tiempo) → `ST_*`
- `AD` (Análisis de Datos) → `AD_*`
- `TM` (Text Mining) → `TM_*`

---

### Paso 3: Escribir el Código de la Función

Crear el archivo de código siguiendo la estructura estándar de NEVEN:

**Ubicación:** `C:\NEVEN\libreria\R\{file}` (o JULIA/, PYTHON/)

**Estructura R típica:**

```r
# ═══════════════════════════════════════════════════════════════════════════════
# {Nombre de la Función}
# Archivo: {file}
# Familia: {family_label}
# ═══════════════════════════════════════════════════════════════════════════════

{ID}.Studio <- function(SetDatosY, SetDatosX, ..., TipoOutput = 0) {
  
  # ─── Validación de inputs ───
  if (is.null(SetDatosY) || length(SetDatosY) == 0) {
    return(list(status = "error", message = "SetDatosY es requerido"))
  }
  
  # ─── TipoOutput 0: Ayuda ───
  if (TipoOutput == 0) {
    return(list(
      status = "ok",
      type = "help",
      content = list(
        nombre = "{Nombre}",
        descripcion = "{Descripción}",
        parametros = list(...),
        outputs = list(...)
      )
    ))
  }
  
  # ─── Cálculo principal ───
  # ... implementación ...
  
  # ─── Retorno según TipoOutput ───
  if (TipoOutput == 1) {
    return(list(status = "ok", type = "table", content = resultado_tabla))
  }
  
  if (TipoOutput == 2) {
    return(list(status = "ok", type = "vector", content = predicciones))
  }
  
  # Default
  return(list(status = "error", message = paste("TipoOutput", TipoOutput, "no implementado")))
}
```

**Convenciones de retorno:**
- `status`: `"ok"` o `"error"`
- `type`: `"table"`, `"vector"`, `"scalar"`, `"html"`, `"plotly"`, `"help"`
- `content`: El resultado según el tipo

---

### Paso 4: Crear el Archivo Sidecar JSON

Crear el archivo JSON siguiendo el formato documentado en `SIDECAR_FORMAT.md`.

**Ubicación:** `C:\NEVEN\functions\{ID}.json`

**Checklist del sidecar:**

- [ ] `id` único (verificar que no exista)
- [ ] `family` y `family_label` correctos
- [ ] `name` y `description` claros y en español
- [ ] `languages` especifica el lenguaje usado
- [ ] `function_name` coincide con el nombre en el código
- [ ] `file` apunta al archivo correcto
- [ ] `variable_roles` define los inputs para DataLab
- [ ] `parameters` lista los parámetros configurables
- [ ] `tipo_outputs` lista todos los outputs disponibles (empezando con id=0 para ayuda)

**Si es XLL-callable, agregar:**

- [ ] `function_name_xll` con el prefijo correcto de la familia
- [ ] `nevenx_positions` mapeando a0, a1, ... a9

---

### Paso 5: Verificar Consistencia

Antes de guardar, verificar:

1. **El archivo de código existe** en la ubicación correcta
2. **El nombre de la función en el código** coincide con `function_name`
3. **Los parámetros del código** coinciden con `nevenx_positions`
4. **Los TipoOutput implementados** coinciden con `tipo_outputs`
5. **El JSON es válido** (sin errores de sintaxis)
6. **Encoding UTF-8** para caracteres especiales (acentos, eñes)

---

### Paso 6: Guardar Archivos

Guardar ambos archivos:

```
C:\NEVEN\libreria\R\{file}           ← Código de la función
C:\NEVEN\functions\{ID}.json         ← Sidecar con metadata
```

**Importante:** Usar encoding UTF-8 sin BOM al guardar.

---

### Paso 7: Informar al Usuario

Confirmar al usuario que la función fue creada:

> ✅ Función creada exitosamente:
> 
> **Archivos generados:**
> - `C:\NEVEN\libreria\R\RG_QuantileRegression.Studio.R`
> - `C:\NEVEN\functions\RG_QuantileRegression.json`
> 
> **Uso desde Excel:**
> ```
> =NEVEN.R("MR_Quantile", Y, X, 0.5, 1)
> ```
> Donde: Y=variable dependiente, X=independientes, 0.5=cuantil, 1=tabla de coeficientes
> 
> **Uso desde DataLab:**
> La función aparecerá en el catálogo bajo "Regresión" después de recargar.
> 
> **TipoOutputs disponibles:**
> - 0 = Ayuda
> - 1 = Tabla de coeficientes
> - 2 = Predicciones
> - 3 = Gráfico de cuantiles

---

## Plantillas Rápidas

### Plantilla: Sidecar XLL-callable Mínimo

```json
{
  "id": "{ID}",
  "family": "{FAMILIA}",
  "family_label": "{Label}",
  "name": "{Nombre visible}",
  "description": "{Descripción de 1-2 oraciones}",
  "languages": ["r"],
  "function_name": "{ID}.Studio",
  "function_name_xll": "{PREFIJO}_{Nombre}",
  "file": "{ID}.Studio.R",
  "nevenx_positions": {
    "a0": { "name": "SetDatosY", "label": "Variable Y", "type": "range", "required": true, "default": null },
    "a1": { "name": "SetDatosX", "label": "Variables X", "type": "range", "required": true, "default": null }
  },
  "tipo_outputs": [
    { "id": 0, "label": "Ayuda" },
    { "id": 1, "label": "Resultado principal" }
  ]
}
```

### Plantilla: Sidecar DataLab-only Mínimo

```json
{
  "id": "{ID}",
  "family": "GR",
  "family_label": "Graficos",
  "name": "{Nombre visible}",
  "description": "{Descripción}",
  "languages": ["r"],
  "function_name": "{ID}.Studio",
  "file": "{ID}.Studio.R",
  "variable_roles": {
    "X": { "label": "Eje X", "types": ["numeric"], "multiple": false, "required": true },
    "Y": { "label": "Eje Y", "types": ["numeric"], "multiple": true, "required": true }
  },
  "parameters": [
    { "name": "Titulo", "label": "Título", "type": "text", "default": "", "tier": 1 }
  ],
  "tipo_outputs": [
    { "id": 0, "label": "Gráfico interactivo" }
  ]
}
```

---

## Errores Comunes a Evitar

| Error | Consecuencia | Solución |
|-------|--------------|----------|
| JSON inválido | Función no aparece en catálogo | Validar sintaxis JSON |
| `function_name_xll` faltante | No aparece en Diccionario de Excel | Agregar campo si es XLL-callable |
| `file` incorrecto | Error al ejecutar función | Verificar nombre exacto del archivo |
| Encoding corrupto | Caracteres raros (Ã¡, â€") | Guardar siempre en UTF-8 |
| ID duplicado | Conflicto con función existente | Verificar IDs existentes antes de crear |
| Posiciones a0-a9 mal mapeadas | Argumentos en orden incorrecto | Revisar que coincidan con el código |

---

## Verificación Post-Creación

El usuario puede verificar que la función se creó correctamente:

1. **En Task Pane → Ayuda:** Buscar la función por nombre
2. **En Excel:** Probar `=NEVEN.R("{function_name_xll}", ..., 0)` para ver la ayuda
3. **En DataLab:** La función debe aparecer en el catálogo de su familia

Si la función no aparece, verificar:
- El servidor HTTP puede necesitar reinicio (cerrar y abrir Excel)
- El archivo JSON tiene errores de sintaxis
- El `function_name_xll` está presente (para funciones Excel)

---

## Referencias

- `SIDECAR_FORMAT.md` — Formato detallado del JSON
- `C:\NEVEN\functions\*.json` — Ejemplos existentes
- `C:\NEVEN\libreria\R\*.R` — Código de funciones existentes
