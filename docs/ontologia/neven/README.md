# Ontología NEVEN - Documentación del Proyecto

## Propósito

Esta ontología documenta la arquitectura, componentes, flujos de datos y patrones del proyecto NEVEN. Su objetivo es:

1. **Guiar el desarrollo** — Antes de modificar un componente, consultar sus dependencias
2. **Acelerar onboarding** — Nuevos desarrolladores entienden la arquitectura rápidamente
3. **Prevenir regresiones** — Ver qué puede romperse antes de hacer cambios
4. **Preservar conocimiento** — El "por qué" de las decisiones queda documentado

## Cómo usar

### Antes de modificar código

1. Buscar el componente en la ontología
2. Ver sus dependencias (`depends_on`, `communicates_with`)
3. Ver qué lo configura (`configured_by`)
4. Revisar workarounds relacionados
5. Consultar patrones que implementa

### Ejemplo: Modificar rag_engine.py

```
Componente: comp_rag_engine
├── depends_on: comp_duckdb
├── called_by: comp_http_server
├── implements: pattern_jsonl_ontology
└── has_workaround: workaround_db_lock

⚠️ CUIDADO: 
- No abrir DuckDB directamente si el servidor está corriendo
- Usar endpoint HTTP /api/rag/upload en su lugar
```

## Estructura

```
C:\NEVEN\ontology\neven\
├── schema.yaml     # Tipos de entidades y relaciones
├── graph.jsonl     # Entidades y relaciones del proyecto
└── README.md       # Este archivo
```

## Tipos de entidades

| Tipo | Descripción | Ejemplos |
|------|-------------|----------|
| **Component** | Componente arquitectónico | NEVEN64.xll, ControlR.exe |
| **ConfigFile** | Archivo de configuración | neven-config.json |
| **Directory** | Directorio importante | C:\NEVEN\startup |
| **DataFlow** | Flujo de datos entre componentes | Excel → R |
| **Pattern** | Patrón de diseño usado | Singleton, Named Pipes |
| **Workaround** | Issue conocido con solución | Junction Quarto |
| **ExposedFunction** | Función visible al usuario | NEVEN.r() |
| **BuildTarget** | Artefacto de compilación | NEVEN64.xll |

## Relaciones

| Relación | Significado |
|----------|-------------|
| `depends_on` | A no funciona sin B |
| `communicates_with` | A envía/recibe datos de B |
| `configures` | A define comportamiento de B |
| `contains` | A contiene a B (directorio/archivo) |
| `implements` | A implementa el patrón B |
| `workaround_for` | A es solución para issue de B |

## Cómo agregar entidades

Formato JSONL (una operación por línea):

```jsonl
{"op": "create", "entity": {"id": "comp_nuevo", "type": "Component", "properties": {...}}}
{"op": "relate", "relation": {"type": "depends_on", "from": "comp_nuevo", "to": "comp_existente"}}
```

### Convenciones de IDs

- Componentes: `comp_nombre`
- Configuración: `config_nombre`
- Directorios: `dir_nombre`
- Flujos: `flow_origen_to_destino`
- Patrones: `pattern_nombre`
- Workarounds: `workaround_nombre`
- Funciones: `func_nombre`
- Builds: `build_nombre`

## Mantenimiento

### Cuándo actualizar

- Al agregar un nuevo componente
- Al cambiar dependencias entre componentes
- Al descubrir un workaround importante
- Al deprecar o eliminar funcionalidad

### Quién actualiza

El agente AI debe actualizar esta ontología como parte del proceso de desarrollo. Los humanos pueden agregar conocimiento que el agente no infiere automáticamente.

## Integración con NEVEN

Esta ontología se carga junto con las de Excel y Econometría. Es consultable desde:

- TaskPane → Config → Conocimiento → Dominio "neven"
- API: `GET /api/ontology/search?q=term&domain=neven`
- Python: `from ontology_manager import search_knowledge; search_knowledge("ControlR", domain="neven")`

## Historial

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2026-08-19 | 1.0 | Creación inicial con arquitectura base |

---

*NEVEN — Universidad de Costa Rica, Tesis de Maestría*
