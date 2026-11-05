# NEVEN — Espacio de Ontologías

Este directorio contiene las ontologías del proyecto NEVEN, organizadas por dominio.

## Estructura

```
ontologia/
├── README.md                 ← Este archivo
├── neven-core/               ← Ontología de arquitectura del proyecto
│   ├── neven-ontology-p1.yaml   (Core, Ribbon, ControlR, Common, startup.r)
│   ├── neven-ontology-p2.yaml   (NevenX dispatcher, Studio backend, sidecars, libreria R)
│   ├── neven-ontology-p3.yaml   (ControlJulia, AgentService, TaskPane frontend)
│   └── neven-ontology-p4.yaml   (Build/CMake, tests, instalador, CreadorPresentaciones)
│
├── econometrics/             ← Ontología econométrica (grafo de conocimiento)
│   ├── schema.yaml              (tipos: Method, Concept, Assumption, RFunction, Dataset)
│   ├── graph.jsonl              (598 nodos — Wooldridge, inferencia causal)
│   ├── graph_aer_update.jsonl   (extensión AER)
│   ├── graph_ts_update.jsonl    (extensión series de tiempo)
│   ├── graph_visualization.html (visualización 2D interactiva)
│   └── graph_visualization_3d.html (visualización 3D)
│
└── excel-functions/          ← Ontología de funciones de Microsoft Excel
    └── excel-functions-ontology.yaml   (523 funciones, 14 categorías)
```

## Ontologías disponibles

### 1. NEVEN Core (`neven-core/`)

**Propósito:** Fuente de verdad estructurada para el agente validador. Define componentes, invariantes técnicas, dependencias y reglas de despliegue del proyecto NEVEN.

**Contenido:**
| Paquete | Archivo | Componentes | Descripción |
|---------|---------|-------------|-------------|
| P1 - Críticos | `neven-ontology-p1.yaml` | 5 | Core XLL, Ribbon, ControlR, Common, startup.r |
| P2 - Activos | `neven-ontology-p2.yaml` | 4 | NevenX dispatcher, Studio backend, sidecars, libreria R |
| P3 - Ocasionales | `neven-ontology-p3.yaml` | 3 | ControlJulia, AgentService, TaskPane frontend |
| P4 - Soporte | `neven-ontology-p4.yaml` | 4 | Build/CMake, tests, instalador, CreadorPresentaciones |

**Uso:** Consultar antes de modificar componentes arquitecturales. Contiene invariantes (INV-*) que nunca deben violarse.

### 2. Econometrics (`econometrics/`)

**Propósito:** Grafo de conocimiento econométrico extraído de libros de referencia (Wooldridge, AER, Series de Tiempo). Define métodos, conceptos, supuestos, funciones R y datasets.

**Contenido:**
| Archivo | Nodos | Descripción |
|---------|-------|-------------|
| `schema.yaml` | — | Define tipos (Method, Concept, Assumption, RFunction, Dataset) y relaciones |
| `graph.jsonl` | 598 | Grafo principal — Wooldridge + inferencia causal |
| `graph_aer_update.jsonl` | 9 | Extensión Applied Econometrics with R |
| `graph_ts_update.jsonl` | 11 | Extensión análisis de series de tiempo |
| `graph_visualization.html` | — | Visualización 2D interactiva |
| `graph_visualization_3d.html` | — | Visualización 3D |

**Tipos de nodos:**
- `Method` — Técnicas econométricas (OLS, 2SLS, GMM, Panel, etc.)
- `Concept` — Conceptos teóricos (endogeneidad, heteroscedasticidad, etc.)
- `Assumption` — Supuestos estadísticos (Gauss-Markov, exogeneidad, etc.)
- `RFunction` — Funciones de R implementadas
- `RPackage` — Paquetes de R utilizados
- `Dataset` — Conjuntos de datos de ejemplo

**Relaciones:**
- `requires` — Método requiere supuesto/concepto
- `adjusts_for` — Método corrige por concepto
- `alternative_to` — Métodos alternativos
- `implemented_in_r_package` — Implementación en R

**Uso:** Referencia para el agente IA, documentación de métodos estadísticos, y navegación del conocimiento econométrico.

**Fuente original:** `F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS\memory\ontology\`

### 3. Excel Functions (`excel-functions/`)

**Propósito:** Catálogo completo de funciones de Microsoft Excel con sintaxis, parámetros, tipos y relaciones.

**Contenido:**
| Archivo | Funciones | Categorías | Tamaño |
|---------|-----------|------------|--------|
| `excel-functions-ontology.yaml` | 523 | 14 | ~317 KB |

**Categorías:**
1. Destacadas (10) — SUMA, SI, BUSCARX, FILTRAR
2. Matemáticas/Trigonometría (~65)
3. Estadísticas (~110)
4. Búsqueda/Referencia (~36)
5. Lógicas (~20) — incluye LAMBDA, LET, MAP, REDUCE
6. Texto (~42)
7. Fecha/Hora (~24)
8. Financieras (~55)
9. Ingeniería (~54)
10. Base de Datos (12)
11. Cubos (7)
12. Información (~21)
13. Web (3)
14. Compatibilidad (~39)

**Uso:** Referencia para autocompletado, ayuda contextual, validación de fórmulas, y documentación de usuario.

## Agregar nuevas ontologías

Para agregar una nueva ontología:

1. Crear un directorio con nombre descriptivo: `ontologia/<dominio>/`
2. Agregar archivos YAML/JSONL siguiendo el formato existente
3. Actualizar este README.md con la documentación
4. Actualizar el hook `.kiro/hooks/load-ontology-context.json` si se requiere carga automática

## Formatos soportados

- **YAML** — Ontologías estructuradas (neven-core, excel-functions)
- **JSONL** — Grafos de conocimiento (econometrics) — un nodo/relación por línea

Ver archivos existentes como referencia de estructura.
