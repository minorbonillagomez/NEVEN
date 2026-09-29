# Contexto para Agentes de IA — NEVEN

> **INSTRUCCIÓN OBLIGATORIA:** Antes de realizar CUALQUIER cambio en el código de NEVEN, 
> lee los documentos en esta carpeta en el orden indicado.

---

## Fuentes de conocimiento

NEVEN tiene DOS tipos de documentación para agentes:

| Tipo | Ubicación | Propósito |
|------|-----------|-----------|
| **Instrucciones operativas** | `C:\NEVEN\docs\agent-context\` | Cómo hacer cambios |
| **Ontologías** | `C:\NEVEN\docs\ontologia\` | Conocimiento estructurado del dominio |

---

## Orden de lectura obligatorio

### Antes de CUALQUIER cambio:

| # | Documento | Propósito |
|---|-----------|-----------|
| 1 | `CHECKLIST_PRE_CAMBIOS.md` | Verificaciones antes de modificar cualquier archivo |
| 2 | `INVARIANTES.md` | Reglas técnicas que NUNCA deben violarse |
| 3 | `COMO_AGREGAR_FUNCIONES.md` | Proceso para agregar nueva funcionalidad |
| 4 | `ALIASES.md` | Sistema de nombres cortos y cómo extenderlo |
| 5 | `EXPANDIR_ONTOLOGIA.md` | Proceso para agregar PDFs a las ontologías |

### Según el tipo de tarea:

| Si la tarea involucra... | Consultar también |
|--------------------------|-------------------|
| Agregar libro/PDF a ontología | `EXPANDIR_ONTOLOGIA.md` + schema del dominio |
| Arquitectura C++, pipes, COM | `ontologia/neven-core/neven-ontology-p1.yaml` |
| Dispatcher R, sidecars, HTTP server | `ontologia/neven-core/neven-ontology-p2.yaml` |
| Julia, TaskPane frontend | `ontologia/neven-core/neven-ontology-p3.yaml` |
| Build, tests, instalador | `ontologia/neven-core/neven-ontology-p4.yaml` |
| Conceptos econométricos | `ontologia/econometrics/schema.yaml` + `graph.jsonl` |
| Funciones de Excel | `ontologia/excel-functions/excel-functions-ontology.yaml` |

---

## ¿Qué es NEVEN?

NEVEN es un add-in para Microsoft Excel que integra R, Julia y Python como motores de scripting. 
Permite ejecutar funciones estadísticas, modelos de ML y visualizaciones desde celdas de Excel.

**Componentes principales:**
- `NEVEN64.xll` — Add-in XLL cargado por Excel
- `ControlR.exe` — Proceso que ejecuta código R
- `ControlJulia.exe` — Proceso que ejecuta código Julia
- `ControlPython.exe` — Proceso que ejecuta código Python
- `NEVEN Studio` — TaskPane con UI para análisis interactivo

---

## Ubicaciones importantes

| Qué | Ruta |
|-----|------|
| Funciones R/Julia | `C:\NEVEN\functions\` |
| Sidecars JSON | `C:\NEVEN\functions\*.json` |
| Servidor HTTP | `C:\NEVEN\startup\neven_http_server.py` |
| TaskPane UI | `C:\NEVEN\TaskPane\` |
| Configuración | `C:\NEVEN\neven-config.json` |

---

## Regla de oro

**Si no estás seguro de cómo hacer algo, lee los documentos en esta carpeta PRIMERO.**

Los errores más comunes ocurren por:
1. No verificar invariantes (ej: BOM en archivos R)
2. No usar el nombre exacto de función (`function_name_xll`)
3. Modificar solo uno de los dos archivos cuando se requieren ambos (aliases)

---

## Contacto

Este proyecto es la tesis de maestría de Minor Bonilla Gómez, Universidad de Costa Rica.
