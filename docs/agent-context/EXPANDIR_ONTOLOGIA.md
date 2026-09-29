# Expandir Ontología con PDFs — NEVEN

> El usuario puede agregar libros PDF para expandir el conocimiento de NEVEN.
> Este documento explica el proceso paso a paso.

---

## ¿Qué es esto?

NEVEN tiene ontologías de conocimiento (grafos de conceptos relacionados) que el agente usa para:
- Sugerir técnicas apropiadas según el problema
- Explicar conceptos econométricos
- Recomendar funciones de Excel

El usuario puede **expandir estas ontologías** agregando sus propios libros PDF.

---

## Ubicaciones

| Dominio | Carpeta de PDFs | Ontología |
|---------|-----------------|-----------|
| Econometría | `ONTOLOGIA/LIBROS/` | `memory/ontology/graph.jsonl` |
| Excel/Finanzas | `ONTOLOGIA/LIBROS EXCEL/` | `memory/ontology/graph.jsonl` |
| Estadística | `ONTOLOGIA/LIBROS ESTADISTICA/` | (futuro) |

---

## Proceso simplificado

### Paso 1: Usuario agrega PDF

El usuario coloca el PDF en la carpeta correspondiente:
```
ONTOLOGIA/LIBROS/MiLibro.pdf           <- Econometría
ONTOLOGIA/LIBROS EXCEL/MiLibro.pdf     <- Excel/Finanzas
```

### Paso 2: Usuario solicita procesamiento

El usuario dice algo como:
- "Procesa el libro MiLibro.pdf para la ontología de econometría"
- "Agrega este PDF a la ontología"
- "Incorpora el contenido de MiLibro a NEVEN"

### Paso 3: Agente extrae conocimiento

1. **Leer el schema** de la ontología destino:
   ```
   ONTOLOGIA/[DOMINIO]/memory/ontology/schema.yaml
   ```

2. **Extraer del PDF** por capítulo:
   - **Técnicas** — métodos y procedimientos
   - **Patrones** — estructuras comunes
   - **Mejores prácticas** — recomendaciones profesionales
   - **Errores comunes** — qué evitar
   - **Conceptos** — definiciones y teoría
   - **Funciones** — funciones mencionadas con contexto

3. **Estructurar como entidades JSON**:
   ```json
   {
     "op": "create",
     "entity": {
       "id": "technique_data_validation",
       "type": "Technique",
       "properties": {
         "name": "Validación de Datos",
         "description": "Uso de Data Validation en Excel...",
         "reference": {
           "book": "MiLibro",
           "chapter": "Capítulo 3",
           "pages": "pp. 45-48"
         }
       }
     }
   }
   ```

4. **Crear relaciones**:
   ```json
   {"op": "relate", "from": "technique_data_validation", "rel": "part_of", "to": "domain_excel"}
   ```

5. **Validar y agregar** al `graph.jsonl`

### Paso 4: Reportar resultados

```
✅ Libro procesado: MiLibro.pdf
   Dominio: econometrics
   Entidades agregadas: 47
   Relaciones agregadas: 89
   Nuevos temas: regresión ridge, validación cruzada, ...
   
   Archivo actualizado: ONTOLOGIA/LIBROS/memory/ontology/graph.jsonl
```

---

## Tipos de entidades válidos

| Tipo | Prefijo ID | Ejemplo |
|------|------------|---------|
| Domain | `domain_` | `domain_panel_data` |
| Technique | `technique_` | `technique_fixed_effects` |
| Pattern | `pattern_` | `pattern_two_way_fe` |
| BestPractice | `bp_` | `bp_cluster_robust_se` |
| CommonError | `error_` | `error_omitted_variable` |
| Concept | `concept_` | `concept_endogeneity` |
| Function | `func_` | `func_plm` |

---

## Reglas de calidad

```
□ Cada entidad tiene `name` y `description`
□ Cada entidad tiene `reference` con libro, capítulo, páginas
□ No hay entidades huérfanas (todas conectadas)
□ Las relaciones usan tipos válidos del schema
□ IDs únicos y con prefijo correcto
□ Contenido parafraseado (no copiado textualmente)
```

---

## Ejemplo de invocación

**Usuario:** "Procesa el libro Wooldridge-Introductory-Econometrics.pdf"

**Agente:**
1. Lee `ONTOLOGIA/LIBROS/memory/ontology/schema.yaml`
2. Lee el PDF capítulo por capítulo
3. Extrae conceptos, técnicas, ejemplos
4. Crea entidades JSON con referencias
5. Crea relaciones entre entidades
6. Valida contra el schema
7. Agrega al `graph.jsonl`
8. Reporta estadísticas

---

## Schema de referencia

El schema define qué tipos de entidades y relaciones son válidos. Siempre leerlo antes de procesar:

```
ONTOLOGIA/LIBROS/memory/ontology/schema.yaml          <- Econometría
ONTOLOGIA/LIBROS EXCEL/memory/ontology/schema.yaml    <- Excel
```

---

## Notas importantes

1. **No copiar texto verbatim** — Parafrasear siempre para evitar problemas de copyright
2. **Incluir referencias** — Cada entidad debe tener libro, capítulo, páginas
3. **Validar antes de agregar** — Verificar que tipos y relaciones existan en schema
4. **Backup** — Antes de modificar `graph.jsonl`, hacer copia de respaldo
