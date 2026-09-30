# Ontología NEVEN v2 — Catálogo de Funciones + Agente Proactivo

## Objetivo

Evolucionar el agente IA de NEVEN de reactivo a proactivo. En lugar de solo interpretar resultados, el agente puede sugerir y ejecutar correcciones metodológicas concretas usando las funciones ya disponibles en NEVEN — y cuando no existen, proponer su creación siguiendo el protocolo establecido.

---

## Requisitos

### R1 — Catálogo completo en la ontología

**R1.1** La ontología debe contener un nodo por cada función disponible en `C:\NEVEN\functions\`, tanto funciones XLL (`R4XCL-*.R`) como funciones Studio (`*.Studio.R` + `*.json`).

**R1.2** Cada nodo de función debe incluir:
- `function_id` exacto para bloques `neven-run`
- Nombre de la función XLL equivalente si existe (ej: `=R.MR_Lineal`)
- Familia (`RG`, `AD`, `ST`, `GR`, `DS`, `UC`)
- Qué estima / qué hace
- Supuestos que asume
- Librerías R/Python/Julia que requiere
- `column_roles` disponibles (Y, X, Z, Endo, Exo, etc.)
- Parámetros clave y sus valores
- `TipoOutput` disponibles (para funciones XLL)
- Cuándo es metodológicamente apropiada
- Alternativas ontológicas (qué función usar si esta falla un supuesto)

**R1.3** El catálogo debe cargarse dinámicamente desde los `.json` sidecars al arrancar el servidor, sin hardcodear `function_id` en el código. Así cada función nueva en `functions/` aparece automáticamente.

---

### R2 — Inventario de librerías y capacidades latentes

**R2.1** Por cada librería R/Python/Julia usada en `functions/`, documentar en la ontología las funciones adicionales que expone pero que NEVEN aún no tiene implementadas como Studio o XLL.

**R2.2** Esta información alimenta el razonamiento del agente: antes de proponer instalar una librería nueva o escribir código desde cero, el agente verifica si la capacidad ya existe en una librería instalada.

**R2.3** Las fuentes para este inventario son: documentación CRAN, vignettes, y PDFs de referencia de las librerías (cuando estén disponibles localmente).

---

### R3 — Flujo de decisión del agente

El agente debe seguir este árbol de decisión al sugerir una corrección:

```
Diagnóstico del problema metodológico
  │
  ├─► ¿Hay función XLL que lo resuelve con TipoOutput diferente?
  │     SÍ → sugiere =R.FUNCION(rangos, TipoOutput=N) en el chat
  │
  ├─► ¿Hay función Studio que lo resuelve?
  │     SÍ → genera bloque neven-run con function_id y column_roles exactos
  │           ¿Requiere librería no instalada?
  │             SÍ → bloque neven-install previo + neven-run
  │
  ├─► ¿La librería instalada tiene la funcionalidad pero no está expuesta?
  │     SÍ → propone nuevo TipoOutput (código del wrapper mínimo)
  │          O propone MiFuncion.Studio.R + MiFuncion.json siguiendo el protocolo
  │
  └─► ¿Requiere librería nueva?
        SÍ → bloque neven-install + nuevo wrapper siguiendo el protocolo
```

**R3.1** La prioridad es siempre usar lo que ya existe antes de proponer algo nuevo.

**R3.2** Cuando el agente propone un nuevo wrapper, el código debe seguir exactamente el protocolo de `COMO_AGREGAR_FUNCIONES.md`: firma de función, `r_object_to_slots()`, estructura del JSON sidecar.

**R3.3** La sugerencia debe incluir la fórmula Excel lista para copiar-pegar: `=R.FUNCION(A1:A50, B1:C50)` con rangos reales basados en las columnas del contexto del usuario.

---

### R4 — Actualización periódica

**R4.1** El catálogo se regenera automáticamente al arrancar el servidor leyendo `C:\NEVEN\functions\*.json`.

**R4.2** No requiere reiniciar el servidor para detectar funciones nuevas — un endpoint `GET /api/datalab/catalog` ya devuelve el catálogo actualizado y el agente puede consultarlo.

**R4.3** La ontología base (supuestos, referencias bibliográficas, relaciones entre métodos) se versiona en `kg_function_map.json` y el grafo de `ontology_engine.py`. El catálogo dinámico complementa pero no reemplaza esa base.

---

## Arquitectura del sistema resultante

```
neven-config.json → ontology_engine.py (grafo econométrico)
                         ↑
C:\NEVEN\functions\*.json → catálogo dinámico (se lee al arrancar)
                         ↑
PDFs / CRAN docs → inventario de capacidades latentes (manual, versión inicial)

Todo confluye en:
_handle_ai_chat() → _build_system_prompt() con catálogo completo
                  → el agente conoce TODAS las funciones disponibles
                  → sugiere la más apropiada con código exacto
```
