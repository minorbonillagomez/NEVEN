# NevenX — Dispatcher Genérico de Procesos

## Contexto

NEVEN hoy tiene dos mecanismos para llamar código desde Excel:

1. **Funciones específicas del XLL** (`=R.MR_Lineal`, `=R.MR_2SLS`, etc.) — cada función está registrada en C++ con su firma fija. Agregar una función nueva requiere escribir R + registrar en el XLL + recompilar.

2. **Función genérica de código** (`=NEVEN.r("codigo R")`) — evalúa una expresión arbitraria. Flexible pero sin IntelliSense, sin rangos dinámicos en la firma, y el código va como string.

`NevenX` es un tercer mecanismo que combina lo mejor de ambos: una función genérica con parámetros reales de Excel (rangos que se actualizan, IntelliSense dinámico) pero que despacha a un **proceso** identificado por nombre — sin recompilar el XLL.

---

## Propuesta

Tres funciones nuevas en el XLL:

```
=NevenX.R("proceso", R1, R2, R3, R4, R5, P1, P2, P3, P4, P5, TipoOutput)
=NevenX.J("proceso", R1, R2, R3, R4, R5, P1, P2, P3, P4, P5, TipoOutput)
=NevenX.P("proceso", R1, R2, R3, R4, R5, P1, P2, P3, P4, P5, TipoOutput)
```

Donde:
- `"proceso"` — string con el nombre de la función a despachar (ej: `"MR_2SLS"`)
- `R1..R5` — hasta 5 rangos opcionales de Excel (XLOPER12 tipo Q — rangos reales, no strings)
- `P1..P5` — hasta 5 parámetros escalares opcionales (strings o números)
- `TipoOutput` — entero que controla el tipo de resultado

---

## Requisitos

### R1 — Firma con rangos reales

**R1.1** `R1..R5` deben ser parámetros de tipo `Q` en la firma del XLL. Excel pasa el rango materializado como `xltypeMulti` antes de llamar la función. Las referencias se actualizan si el usuario mueve columnas. El recálculo automático funciona igual que en las funciones específicas.

**R1.2** `P1..P5` deben ser de tipo `Q` también, aceptando strings o números escalares.

**R1.3** `TipoOutput` debe ser de tipo `Q` (entero o string).

**R1.4** Todos los parámetros excepto `"proceso"` deben ser opcionales (`xltypeMissing` si no se pasan). La función debe ser invocable con solo `=NevenX.R("proceso", R1)`.

---

### R2 — Despacho por nombre de proceso

**R2.1** El primer parámetro `"proceso"` es un string que identifica la función R/Julia/Python a ejecutar. No es código arbitrario — es un nombre que se busca en el entorno cargado (`NEVEN$proceso` o `R_GlobalEnv`).

**R2.2** El mecanismo de despacho usa `RJ_Call_Generic` existente, pasando `"proceso"` como el parámetro `func` y los rangos/parámetros como `arg0..argN`. No se escribe código R en la celda de Excel.

**R2.3** El proceso debe estar pre-cargado en el entorno R/Julia/Python. Si el nombre no existe, retornar un error descriptivo: `"Proceso 'MR_2SLS' no encontrado. Verifique que el archivo esté en C:\NEVEN\functions\"`.

**R2.4** El proceso recibe los datos con nombres semánticos según el catálogo. Ver R4.

---

### R3 — IntelliSense dinámico

**R3.1** Cuando el usuario escribe el nombre del proceso, el sistema muestra dinámicamente los nombres de los parámetros correspondientes en la barra de fórmulas de Excel.

**R3.2** La fuente de información para el IntelliSense es el catálogo JSON de `C:\NEVEN\functions\*.json` — el mismo que ya usa DataLab. No se duplica información.

**R3.3** El mecanismo técnico para IntelliSense dinámico en Excel es la función `xlfGetName` / `xlfRegister` con parámetro de ayuda que llama de vuelta al XLL. La implementación específica debe explorarse durante el diseño técnico detallado — es la parte más compleja del spec.

**R3.4** Si el nombre del proceso no está en el catálogo, el IntelliSense muestra la firma genérica: `R1=Datos1, R2=Datos2, R3=Datos3, R4=Datos4, R5=Datos5, P1=Param1, ...`

---

### R4 — Mapeo semántico de rangos

**R4.1** El catálogo define qué posición (R1, R2, R3...) corresponde a qué rol para cada proceso. Esta información viene del campo `variable_roles` del `.json` sidecar.

Ejemplo para `MR_2SLS`:
```json
{ "variable_roles": { "Y": "R1", "Endo": "R2", "Instru": "R3", "Exo": "R4" } }
```

**R4.2** El XLL usa este mapeo para pasar los datos al proceso con los nombres correctos. En lugar de pasar `arg0, arg1, arg2`, pasa `data_Y=arg0, data_Endo=arg1, data_Instru=arg2`. El proceso R los recibe con sus nombres esperados.

**R4.3** Para procesos sin sidecar JSON (creados por el usuario o el agente), se usa la convención por defecto: `R1=data_X, R2=data_Y, R3=data_Z`, `P1=Param1`, `P2=Param2`, `TipoOutput=TipoOutput`.

---

### R5 — Catálogo dinámico como fuente única de verdad

**R5.1** El mismo catálogo JSON que alimenta:
- DataLab (Studio) para la UI de parámetros
- El agente IA para sugerencias de `neven-run`
- El IntelliSense de `NevenX.R`

**R5.2** Agregar una función nueva al catálogo (`MiFuncion.json` + `MiFuncion.R` en `functions/`) la hace disponible automáticamente en los tres contextos sin recompilar el XLL.

**R5.3** El catálogo se carga en memoria al arrancar ControlR. Un endpoint `GET /api/datalab/catalog` ya lo expone y puede usarse para el IntelliSense.

---

### R6 — Compatibilidad

**R6.1** `NevenX.R/J/P` son funciones **adicionales** — no reemplazan las funciones específicas existentes (`R.MR_Lineal`, etc.). Ambas coexisten.

**R6.2** Las funciones específicas existentes no se modifican ni eliminan. Su ciclo de vida es independiente.

**R6.3** El sandbox existente aplica a `NevenX.*` de la misma forma que a las funciones específicas — el proceso invocado ya fue validado al ser cargado, no se valida código arbitrario en el momento de la llamada.

---

### R7 — Experiencia del usuario para funciones nuevas

**R7.1** El flujo de agregar una función nueva sin recompilar el XLL es:
1. Crear `MiFuncion.R` en `C:\NEVEN\functions\` (siguiendo el protocolo)
2. Crear `MiFuncion.json` en `C:\NEVEN\functions\` (con `variable_roles` y `parameters`)
3. Reiniciar NEVEN Studio (para recargar el catálogo en R)
4. Usar `=NevenX.R("MiFuncion", datos_Y, datos_X, TipoOutput=1)`

**R7.2** El agente IA puede ejecutar los pasos 1 y 2 automáticamente vía el endpoint `/api/functions/create`. El usuario solo necesita hacer el paso 3 (reiniciar) y 4 (usar la función).

---

## Diseño técnico a resolver

### DT1 — Cuántos rangos y parámetros son suficientes

La función más demandante del catálogo actual es `MR_PanelData` con 4 rangos obligatorios (Y, X, i, t). Para dejar margen a funciones futuras, **5 rangos + 5 parámetros escalares + TipoOutput = 12 parámetros** es suficiente.

Firma C++ resultante: `"UQQQQQQQQQQQQQ"` = U + 13 Q = función + proceso + 5 rangos + 5 params + TipoOutput.

### DT2 — IntelliSense dinámico

Esta es la parte técnicamente más compleja. Opciones:

**Opción A — Tooltip via xlfGetName:** El XLL registra `NevenX.R` con un argumento de ayuda que llama de vuelta a una función C++ que retorna la descripción dinámica según el valor del primer parámetro. Limitación: Excel no siempre actualiza el tooltip en tiempo real mientras se edita.

**Opción B — Function Wizard personalizado:** Interceptar el diálogo de argumentos de función vía COM para mostrar nombres dinámicos. Más trabajo pero experiencia completa.

**Opción C — Convención de nombres fijos + documentación:** R1=Datos_Y, R2=Datos_X, R3=Datos_Z siempre, sin dinamismo. El usuario consulta el catálogo o DataLab para ver los roles. Mínimo esfuerzo, menor UX.

La recomendación es empezar con **Opción C** para tener la funcionalidad completa, e iterar hacia A/B si el uso lo justifica.

### DT3 — Mapeo de parámetros en el despachador R

El despachador necesita saber que `R1` es `data_Y` para `MR_2SLS`. Opciones:

**Opción A — Wrapper R por proceso:** `NevenX.R` llama a `NEVEN$.dispatch("MR_2SLS", R1, R2, R3, ...)` y `.dispatch` busca en el catálogo cómo mapear los rangos y llama `do.call("MR_2SLS", list(data_Y=R1, data_Endo=R2, data_Instru=R3))`.

**Opción B — Mapeo en el XLL:** El XLL lee el catálogo JSON y agrega los nombres semánticos al Protobuf antes de enviar a ControlR.

La Opción A es más simple y mantiene la lógica en R donde el catálogo también vive. La Opción B evita un round-trip pero acopla el XLL al formato JSON.

Recomendación: **Opción A** — un dispatcher R que lee el catálogo y hace `do.call` con nombres correctos.

---

## Plan de implementación

### Fase 1 — Infraestructura (sin IntelliSense dinámico)
- [ ] Agregar `NevenX_R`, `NevenX_J`, `NevenX_P` en `basic_functions.cc` reutilizando `RJ_Call_Generic`
- [ ] Registrar en `funcTemplates` con firma `UQQQQQQQQQQQQQ`
- [ ] Crear dispatcher R `NEVEN$.nevenx_dispatch(proceso, R1..R5, P1..P5, TipoOutput)` en `R4XCL-0-Interno-1.R`
- [ ] Deploy y prueba: `=NevenX.R("MR_Lineal", A1:A50, B1:C50, TipoOutput=1)`

### Fase 2 — Catálogo dinámico
- [ ] El dispatcher R lee `C:\NEVEN\functions\*.json` para mapear posiciones a nombres semánticos
- [ ] `=NevenX.R("MR_2SLS", Y, X_endo, Z, TipoOutput=2)` usa los roles correctos automáticamente

### Fase 3 — IntelliSense (Opción A primero)
- [ ] Tooltip estático con nombres genéricos (R1=Datos_Y, R2=Datos_X, etc.)
- [ ] Evaluar si se implementa IntelliSense dinámico completo

### Fase 4 — Integración con agente IA
- [ ] El agente sugiere `=NevenX.R("MR_2SLS", ...)` con las columnas reales del contexto
- [ ] El bloque `neven-create-function` genera automáticamente el `.json` junto con el `.R`
