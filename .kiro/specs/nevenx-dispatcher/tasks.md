# NevenX — Tareas de Implementación

## Fase 1 — Infraestructura base (sin IntelliSense dinámico)

### Bloque A: C++ XLL

- [ ] **A1** Agregar `NevenX_R()`, `NevenX_J()`, `NevenX_P()` en `Core/src/basic_functions.cc`
  - Firma: `(proceso, R1..R5, P1..P5, TipoOutput)` = 12 parámetros tipo Q + retorno U
  - Reutiliza `RJ_Call_Generic` con target `"NEVEN$.nevenx_dispatch"`
  - language_key: 0=R, 1=Julia, 2=Python

- [ ] **A2** Registrar en `funcTemplates` de `Core/include/basic_functions.h`
  - Tipo: `"UQQQQQQQQQQQQQ"` (U + 13 Q)
  - Nombres de parámetros: `"Proceso,DatosY,DatosX,Datos3,Datos4,Datos5,Param1,Param2,Param3,Param4,Param5,TipoOutput"`

- [ ] **A3** Exportar en `Core/src/rj2xcl.def`

- [ ] **A4** Compilar y verificar sin errores

### Bloque B: Dispatcher R

- [ ] **B1** Crear `C:\NEVEN\functions\R4XCL-0-NevenX.R` con:
  - `.nevenx_dispatch(proceso, R1..R5, P1..P5, TipoOutput)`
  - `.nevenx_get_roles(proceso)` — lee `*.json` de `functions/`
  - `.nevenx_map_args(raw_args, roles)` — mapea posiciones a nombres semánticos
  - Registro en entorno `NEVEN`

- [ ] **B2** Agregar `source("R4XCL-0-NevenX.R")` en el script de startup de R

### Bloque C: Prueba end-to-end

- [ ] **C1** Prueba básica sin sidecar: `=NevenX.R("MR_Lineal", A1:A50, B1:C50, TipoOutput=1)`
  - Usa convención por defecto: R1=data_Y, R2=data_X
  - Debe retornar el mismo resultado que `=R.MR_Lineal(A1:A50, B1:C50, TipoOutput=1)`

- [ ] **C2** Prueba con sidecar existente: `=NevenX.R("RG_Lineal", A1:A50, B1:C50, TipoOutput=1)`
  - Usa el JSON de `R4XCL-RG-Lineal.Studio.R` para mapear roles

- [ ] **C3** Prueba con proceso inexistente — verifica mensaje de error descriptivo

- [ ] **C4** Prueba Julia: `=NevenX.J("J_AD_Descriptiva", A1:D50)`

---

## Fase 2 — Catálogo dinámico y mapeo semántico

- [ ] **D1** Actualizar sidecars JSON existentes con campo `"position"` en `variable_roles`
  - Empezar con: `RG_Lineal`, `RG_2SLS`, `RG_DatosPanel`, `RG_Logistica`, `ST_VAR`, `AD_KMedias`
  - Formato: `"position": "R1"` junto a cada rol

- [ ] **D2** Actualizar `parameters` en sidecars con `"position": "P1"` etc.

- [ ] **D3** Verificar que `.nevenx_get_roles()` lee correctamente los campos `position`

- [ ] **D4** Prueba 2SLS con mapeo semántico completo:
  ```
  =NevenX.R("MR_2SLS", lwage_range, educ_range, z_range, TipoOutput=1)
  ```
  Donde el dispatcher asigna: data_Y=R1, data_Endo=R2, data_Instru=R3

---

## Fase 3 — IntelliSense (Fase A: nombres genéricos)

- [ ] **E1** Actualizar los textos de ayuda en `funcTemplates` para ser más descriptivos
- [ ] **E2** Documentar la convención R1=Y, R2=X, R3=Z en `COMO_AGREGAR_FUNCIONES.md`
- [ ] **E3** Evaluar viabilidad de IntelliSense dinámico completo (tooltip via xlfGetName)

---

## Fase 4 — Integración con agente IA

- [ ] **F1** Actualizar `_run_hint` en `neven_http_server.py` para que el agente sugiera:
  - `=NevenX.R("proceso", rangos)` para funciones existentes en el catálogo
  - Bloque `neven-create-function` para funciones nuevas (ya implementado)

- [ ] **F2** El bloque `neven-create-function` debe generar automáticamente el `.json` además del `.R`
  - El agente incluye `json_content` en la especificación del bloque
  - El endpoint `/api/functions/create` acepta y guarda ambos archivos

- [ ] **F3** Actualizar `functions_catalog.json` con ejemplos de `excel_usage` usando `NevenX.R`

---

## Notas de implementación

**Sobre la firma C++:** El número 13 Q es intencionalmente generoso. `RJ_Call_Generic` ya soporta hasta 16 argumentos. Los parámetros `xltypeMissing` se ignoran automáticamente en el conteo de argumentos reales.

**Sobre el dispatcher R:** El entorno `NEVEN` ya existe en el runtime R de NEVEN (es donde viven todas las funciones R4XCL). Registrar `.nevenx_dispatch` ahí garantiza que está disponible cuando ControlR llama `NEVEN$.nevenx_dispatch`.

**Sobre los sidecars existentes:** No es necesario actualizarlos todos en Fase 1. El dispatcher funciona con convención por defecto hasta que se agregue el campo `position`. La migración puede hacerse gradualmente función por función.

**Sobre Julia y Python:** La arquitectura es idéntica. `NevenX.J` usa `language_key=1` y el dispatcher equivalente en Julia. `NevenX.P` usa `language_key=2` y el dispatcher en Python. Los dispatchers de cada lenguaje siguen el mismo patrón pero adaptados a la sintaxis de cada uno.
