# Directriz de Arquitectura Multi-Agente: Ontología Unificada Compartida

Todos los agentes y skills especializados del proyecto comparten una **Única Fuente de Verdad Ontológica**:

1. **Esquema Formal**: `memory/ontology/schema.yaml`
2. **Grafo de Conocimiento (Knowledge Graph)**: `memory/ontology/graph.jsonl`
3. **Visualizadores Oficiales**: 
   - 2D: `memory/ontology/graph_visualization.html`
   - 3D: `memory/ontology/graph_visualization_3d.html`

---

## Principios Fundamentales del Sistema Multi-Agente

1. **Interoperabilidad Conceptual**: Ningún agente puede definir términos, supuestos, métodos o relaciones de forma aislada. Todo concepto debe estar formalizado en `schema.yaml` y registrado en `graph.jsonl`.
2. **Cero Nodos Aislados**: Toda nueva entidad incorporada por cualquier agente debe tener vínculos explícitos (`part_of`, `requires`, `evaluates`, `adjusts_for`, `uses_r_function`, `implemented_in_r_package`).
3. **Sincronización Bidireccional**: Cuando un agente proponga o refine conceptos de su respectivo libro, estos deben integrarse inmediatamente al grafo general y sincronizarse con los visualizadores 2D y 3D.
4. **Validación Cruzada**:
   - Agente Clásico / Econometría $\leftrightarrow$ Agente Inferencia Causal (p. ej. OLS vs. Matching / IPTW / RDD / DiD).
   - Agente Microeconometría $\leftrightarrow$ Agente Espacial / Series de Tiempo (p. ej. correlación contemporánea vs. autocorrelación espacial / serial).
   - Agente MIT Big Data $\leftrightarrow$ Agente Inferencia Causal (p. ej. LATE/Compliers y Double ML vs. IPTW/MSM).

---

## Agentes Especialistas Activos (8)
1. `classical-econometrics-agent` (Hanck et al. / Introduction to Econometrics with R)
2. `aer-applied-econometrics-agent` (Kleiber & Zeileis / Applied Econometrics with R)
3. `microeconometrics-panel-agent` (Wooldridge / Cross Section and Panel Data)
4. `time-series-agent` (Cryer & Chan / Time Series Analysis with Applications in R)
5. `spatial-econometrics-agent` (Anselin, Bivand, Pebesma / Spatial Data Analysis in R)
6. `causal-inference-agent` (Brumback / Fundamentals of Causal Inference using R)
7. `social-sciences-glm-agent` (R for Social Sciences / Generalized Linear Models)
8. `mit-applied-econometrics-agent` (MIT 14.387 / Applied Econometrics: Mostly Harmless Big Data - Angrist & Chernozhukov)


---

## Principio de Diseño: Sistema Abierto por Diseño

**Fecha de formalización:** 2026-08-19

La ontología de NEVEN es un **sistema abierto por diseño, no por omisión**. No está incompleta — está en su versión inicial. La diferencia es importante porque define la actitud correcta hacia sus límites actuales: no son deudas técnicas a corregir, son espacios de crecimiento planificados.

> *La ontología no pretende ser exhaustiva desde su versión inicial. Pretende ser correcta, coherente y extensible. Cada nuevo dominio de análisis se incorpora como un agente especializado que respeta el schema existente y conecta sus entidades al grafo central mediante las relaciones ya definidas. La cobertura crece; la arquitectura no cambia.*

---

## Protocolo de Extensión — Cómo Agregar un Nuevo Agente

Para que cualquier persona (colaborador, estudiante, continuador del proyecto) pueda agregar un nuevo dominio sin romper lo existente, se sigue este protocolo:

### Pasos obligatorios

1. **Identificar la fuente académica de referencia** del nuevo dominio.  
   Debe ser un libro o curso con ISBN/URL verificable. No se acepta documentación informal como fuente principal.

2. **Crear el directorio del agente:**
   ```
   .agents/skills/<nombre-agente>/SKILL.md
   ```
   Usar el formato estándar: frontmatter YAML con `name` y `description`, secciones de Misión, Entidades Nucleares y Directrices Metodológicas.

3. **Agregar las entidades nuevas al grafo:**  
   Añadir operaciones `{"op": "create", ...}` en `memory/ontology/graph.jsonl` respetando los tipos definidos en `schema.yaml`.

4. **Conectar cada entidad nueva al grafo existente:**  
   Cada entidad nueva debe tener al menos una relación con el grafo existente (`part_of`, `requires`, `evaluates`, `uses_r_function`, `implemented_in_r_package`).  
   **Regla absoluta: cero nodos aislados.**

5. **Extender el schema solo si es estrictamente necesario:**  
   Si se necesita un tipo de nodo o relación que `schema.yaml` no contempla, extenderlo con documentación explícita del motivo. Si `Method` cubre el caso, no crear `Algorithm` como tipo nuevo.

6. **Sincronizar los visualizadores:**  
   Ejecutar `scratch/sync_visualizers.py` para actualizar `graph_visualization.html` (2D) y `graph_visualization_3d.html` (3D).

7. **Verificar la auditoría:**  
   El grafo resultante debe cumplir: 0 errores de schema, 0 nodos aislados.

---

## Contrato de Compatibilidad — Invariantes del Sistema

Estas tres reglas no se negocian. Son la garantía de que el sistema permanece coherente a medida que crece:

### Regla 1 — El schema es el contrato
Los tipos de nodo y relaciones definidos en `schema.yaml` son el contrato de interoperabilidad entre agentes. Nuevos tipos requieren justificación explícita y no pueden reemplazar tipos existentes. Si un tipo existente cubre el caso, úsalo.

### Regla 2 — Los IDs son permanentes
Una vez que un nodo existe en `graph.jsonl` con un ID, ese ID no cambia nunca. Los agentes nuevos pueden referenciar IDs existentes con total confianza. Nunca se elimina un nodo — solo se enriquece con nuevas propiedades o relaciones.

### Regla 3 — Las referencias son verificables
Toda entidad nueva debe tener una referencia a una fuente académica real con libro (o curso), capítulo y páginas. Esto no es opcional — es lo que permite que las advertencias pedagógicas del sistema NEVEN estén fundamentadas en literatura que el usuario puede consultar.

---

## Dominios Candidatos para Expansión Futura

Lista orientativa, no exhaustiva ni obligatoria. Documenta la dirección de crecimiento pensada:

| Agente propuesto | Dominio | Fuente de referencia sugerida |
|-----------------|---------|-------------------------------|
| `ml-predictive-agent` | Machine Learning predictivo | ISLR (James et al.) / ESL (Hastie et al.) |
| `eda-agent` | Análisis exploratorio de datos | R for Data Science (Wickham) |
| `bayesian-agent` | Estadística bayesiana | Statistical Rethinking (McElreath) |
| `impact-evaluation-agent` | Evaluación de impacto / RCTs | Running Randomized Evaluations (Glennerster) |
| `financial-econometrics-agent` | Econometría financiera | Tsay - Analysis of Financial Time Series |
| `text-data-agent` | Text as data / NLP econométrico | Gentzkow, Kelly & Taddy |

---

## Extensión del Schema Pendiente (aprobada en sesión 2026-08-19)

El campo `official_docs` en el tipo `RFunction` fue aprobado para documentar el enlace canónico a CRAN de cada función. Pendiente de implementar en `schema.yaml`:

```yaml
RFunction:
  required: [name, package, description]
  optional: [reference, r_syntax, interpretation_guide, official_docs]

# Estructura de official_docs:
# official_docs:
#   arguments: [{name, type, description}]
#   return_value: string
#   see_also: [function_ids]
#   examples: [string]
#   cran_url: string   ← URL canónica predecible de CRAN
```

La `cran_url` sigue el patrón:
```
https://cran.r-project.org/web/packages/<pkg>/<pkg>.pdf
```

El contenido se obtiene en tiempo de ejecución — no se almacena en el grafo para evitar problemas de licencia y desactualización.
