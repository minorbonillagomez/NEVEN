---
id: ontologias-excel-consultant
title: "Capitulo 14 - Ontologías y Excel Consultant"
sidebar_label: 14. Ontologías y Excel Consultant
sidebar_position: 14
---

# Capitulo 14: Sistema de Ontologías y Excel Consultant

**Disponible desde:** Agosto 2026

NEVEN incluye un sistema de conocimiento estructurado basado en **ontologías dinámicas** y un modo especializado de IA llamado **Excel Consultant** que permite auditar, documentar y optimizar hojas de cálculo.

---

## 14.1 Arquitectura del conocimiento

```
┌─────────────────────────────────────────────────────────────┐
│                     ONTOLOGIA/                              │
│  ┌──────────────────┬──────────────────┬──────────────────┐ │
│  │  LIBROS EXCEL    │     NEVEN        │     LIBROS       │ │
│  │                  │                  │                  │ │
│  │ • 113 funciones  │ • 40+ funciones  │ • Econometría    │ │
│  │   nativas Excel  │   R/Julia/Python │   teórica        │ │
│  │ • CFI, Curso     │ • Dinámico       │ • Wooldridge     │ │
│  │   Práctico, etc. │                  │   Greene, etc.   │ │
│  └──────────────────┴──────────────────┴──────────────────┘ │
│                            │                                │
│                            ▼                                │
│                    graph.jsonl                              │
│                  (append-only)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 14.2 Ubicación de ontologías

Las ontologías viven **fuera del repositorio git** para permitir personalización por usuario:

| Dominio | Ubicación | Contenido |
|:---|:---|:---|
| Excel nativo | `ONTOLOGIA/LIBROS EXCEL/` | 113 funciones de Excel |
| NEVEN | `ONTOLOGIA/NEVEN/` | Funciones R/Julia/Python agregadas |
| Econometría | `ONTOLOGIA/LIBROS/` | Conceptos teóricos |

Cada dominio tiene:
- `memory/ontology/schema.yaml` — define tipos de entidades
- `memory/ontology/graph.jsonl` — grafo de conocimiento

---

## 14.3 Formato graph.jsonl

Una línea = una operación. Append-only, nunca modificar.

**Crear entidad:**
```json
{"op": "create", "entity": {"id": "func_vlookup", "type": "ExcelFunction", "properties": {"name": "BUSCARV", "category": "Búsqueda", "description": "Busca un valor en la primera columna..."}}}
```

**Crear relación:**
```json
{"op": "relate", "from": "func_vlookup", "rel": "part_of", "to": "domain_lookup"}
```

---

## 14.4 Excel Consultant

El Excel Consultant es un modo especializado de IA que analiza hojas de cálculo.

### Activación

1. En NEVEN Studio → pestaña **AI**
2. Clic en **"Analizar Hoja"**
3. El agente recibe metadatos de la hoja activa

### Capacidades

| Función | Descripción |
|:---|:---|
| **Auditoría** | Detecta errores, fórmulas frágiles, hardcoding |
| **Documentación** | Explica qué hace cada sección de la hoja |
| **Optimización** | Sugiere fórmulas más eficientes |
| **Educación** | Enseña sobre funciones desconocidas |
| **Creación** | Escribe funciones R/Julia/Python nuevas |

### Ejemplo de uso

```
Usuario: "¿Qué hace esta hoja?"

Excel Consultant:
Esta hoja calcula un presupuesto mensual con:
- Columna A: Categorías de gastos
- Columna B: Presupuesto estimado (SUMA de B2:B15)
- Columna C: Gasto real (SUMAR.SI.CONJUNTO...)
- Columna D: Varianza = B-C

Problemas detectados:
1. C5 tiene un valor fijo ($1500) en lugar de fórmula
2. D3 usa referencia absoluta incorrecta ($B$3 debería ser B3)

Sugerencias:
- Considerar SUMIFS en lugar de múltiples SUMAR.SI
```

---

## 14.5 Expansión de ontologías

El usuario puede agregar libros PDF para expandir el conocimiento:

1. Colocar PDF en `ONTOLOGIA/{dominio}/`
2. En NEVEN Studio, escribir: *"procesa el libro CursoPractico.pdf"*
3. El agente extrae funciones y las agrega a `graph.jsonl`

### Libros procesados (Agosto 2026)

| Libro | Funciones extraídas |
|:---|:---|
| CFI Excel Book.pdf | 45 funciones |
| Curso Práctico Excel.pdf | 38 funciones |
| Excel Bible 2021.pdf | 30 funciones |

---

## 14.6 Ontología dinámica

Cuando el agente crea una nueva función para el usuario, automáticamente:

1. Guarda el archivo en `libreria/{R|JULIA|PYTHON}/`
2. Agrega la entidad a `ONTOLOGIA/NEVEN/memory/ontology/graph.jsonl`
3. Crea relaciones con categorías y conceptos relacionados

Esto significa que **la ontología crece con el uso**.

---

## 14.7 Troubleshooting

**El Excel Consultant no reconoce funciones:**
- Verificar que `graph.jsonl` existe en el dominio correcto
- Ejecutar validación: cada línea debe ser JSON válido

**Error al procesar libros:**
- Solo se procesan PDFs (no DOCX, EPUB)
- El agente parafrasea contenido (compliance de derechos de autor)

**Funciones nuevas no aparecen en la ontología:**
- Verificar que el agente tenga acceso de escritura a `ONTOLOGIA/`
- Revisar si hay errores de JSON en la última línea de `graph.jsonl`

---

*Documentación actualizada: 20 de agosto de 2026*
