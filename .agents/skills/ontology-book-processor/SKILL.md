---
name: ontology-book-processor
description: Process PDF books to extract structured knowledge and add it to domain-specific ontologies. Use when the user says "procesa el libro", "agregar libro a la ontología", "incorporar PDF", "expandir ontología con libro", "indexar libro", or mentions adding content from books like CFI Excel, Curso Práctico, Excel Bible, Wooldridge, Greene, or Hamilton to the NEVEN knowledge graph.
---

# Skill: Ontology Book Processor

## Purpose

Process PDF books to add them to NEVEN's knowledge system. This involves:
1. **RAG indexing** — Para búsqueda vectorial (obligatorio)
2. **Ontology extraction** — Para entidades y relaciones (opcional, usa LLM)
3. **UI checkpoint** — Para mostrar en la interfaz (obligatorio)

## Prerequisites

- **Servidor HTTP corriendo** en `localhost:5555`
- El servidor se inicia cuando Excel tiene NEVEN cargado y el TaskPane abierto
- Verificar con: `GET http://localhost:5555/api/health`

## When to Use

Activate this skill when:
- User says "Procesa el libro [X]" o "Agrega el libro [X]"
- User adds a new PDF and wants to incorporate it
- User asks to expand an ontology with content from a book
- User mentions "agregar libro", "incorporar PDF", "indexar libro"

---

## PROCESO COMPLETO (4 PASOS)

### PASO 1: Indexar al RAG (OBLIGATORIO)

**Qué hace:** Divide el PDF en chunks y los indexa en ChromaDB.

```http
POST http://localhost:5555/api/rag/upload
Content-Type: application/json

{
    "file_path": "F:\\ruta\\completa\\al\\libro.pdf",
    "domain": "excel"
}
```

**Dominios válidos:**
| Domain | Uso |
|--------|-----|
| `excel` | Funciones Excel, VBA, modelado financiero |
| `econometria` | Econometría, series de tiempo, panel data |
| `estadistica` | Pruebas estadísticas, probabilidad |
| `algebra_lineal` | Matrices, vectores |

**Respuesta exitosa:**
```json
{"status": "ok", "doc_id": "libro.pdf", "message": "Document indexed successfully"}
```

**Tiempo:** 1-10 minutos según tamaño.

---

### PASO 2: Procesar Ontología (OPCIONAL)

**Qué hace:** Extrae entidades (conceptos, fórmulas, técnicas) usando el LLM activo.

**⚠️ IMPORTANTE:** Este paso **consume tokens del LLM**. Preguntar al usuario si desea hacerlo.

```http
POST http://localhost:5555/api/ontology/process
Content-Type: application/json

{
    "file_path": "F:\\ruta\\completa\\al\\libro.pdf",
    "domain": "excel",
    "max_pages": 100
}
```

**Parámetros:**
- `max_pages`: Limitar páginas (recomendado para libros >200 páginas)

**Respuesta exitosa:**
```json
{
    "status": "ok",
    "entities_created": 45,
    "relations_created": 23
}
```

**Tiempo:** 5-30 minutos según páginas.

---

### PASO 3: Crear Checkpoint para UI (OBLIGATORIO)

**Qué hace:** Crea archivo JSON para que la UI muestre el libro con páginas.

**Ubicación:** `C:\NEVEN\docs\ontologia\checkpoints\`

**Código Python:**
```python
import json
import hashlib
import os
from PyPDF2 import PdfReader

def create_checkpoint(pdf_path, domain, entities_created=0, relations_created=0):
    checkpoint_dir = r"C:\NEVEN\docs\ontologia\checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Contar páginas
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    
    # Nombre del libro (sin extensión .pdf)
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Nombre limpio para archivo (sin caracteres ilegales: : * ? " < > |)
    safe_name = book_name.replace(":", " -").replace("?", "").replace("*", "").replace('"', "")
    
    # Hash único
    file_hash = hashlib.md5(book_name.encode()).hexdigest()[:12]
    
    checkpoint_path = os.path.join(checkpoint_dir, f"{safe_name}_{domain}_{file_hash}.json")
    
    checkpoint_data = {
        "book_name": book_name,
        "domain": domain,
        "total_pages": total_pages,
        "processed_pages": total_pages,
        "status": "completed",
        "entities_created": entities_created,
        "relations_created": relations_created,
    }
    
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    
    return checkpoint_path, total_pages
```

---

### PASO 4: Verificación (OBLIGATORIO)

**4.1 Verificar libro en RAG:**
```http
GET http://localhost:5555/api/rag/list
```

**4.2 Verificar en UI:**
```http
GET http://localhost:5555/api/ontology/books?domain=excel
```

**4.3 Probar búsqueda:**
```http
POST http://localhost:5555/api/rag/query
{"query": "término del libro", "domain": "excel", "top_k": 3}
```

---

## SCRIPT AUTOMATIZADO

Existe un script que hace todo:

```bash
# Solo RAG (rápido)
python C:\NEVEN\scripts\add_book.py "F:\ruta\libro.pdf" excel

# RAG + Ontología (usa LLM)
python C:\NEVEN\scripts\add_book.py "F:\ruta\libro.pdf" excel --ontology

# Con límite de páginas
python C:\NEVEN\scripts\add_book.py "F:\ruta\libro.pdf" excel --ontology --max-pages 50
```

---

## FLUJO DE DECISIÓN

```
¿Usuario quiere agregar libro?
│
├─► ¿Servidor HTTP corriendo?
│   │
│   ├─► NO: "Abre Excel con NEVEN y el TaskPane"
│   │
│   └─► SÍ: ¿Qué tipo de procesamiento?
│           │
│           ├─► "Solo búsqueda" → PASO 1 + PASO 3 + PASO 4
│           │
│           └─► "Con entidades" → PASO 1 + PASO 2 + PASO 3 + PASO 4
│
└─► Confirmar al usuario:
    "Libro [X] agregado: Y páginas, Z entidades"
```

---

## CONVENCIONES DE NOMBRES

Para evitar duplicados:

1. **Sin .pdf** en `book_name`
2. **Formato:** `Título del Libro (Autor principal)`
3. **Consistente** con checkpoints existentes

**Ejemplos correctos:**
- `Microsoft Excel 365 Bible`
- `Applied Econometrics with R (Kleiber & Zeileis)`
- `Introduccion a la econometria-Wooldridge`

---

## TROUBLESHOOTING

| Problema | Solución |
|----------|----------|
| Servidor no responde | Abrir Excel + TaskPane NEVEN |
| Libro no aparece en UI | Verificar checkpoint existe |
| Búsqueda no encuentra | Verificar indexación RAG |
| Timeout en ontología | Usar `max_pages` menor |
| Caracteres extraños | Nombre archivo sin `: * ? "` |

---

## UBICACIONES DE ARCHIVOS

| Componente | Ruta |
|------------|------|
| RAG Database | `C:\NEVEN\data\rag_index.duckdb` |
| Ontología Excel | `C:\NEVEN\ontology\excel\graph.jsonl` |
| Ontología Econometría | `C:\NEVEN\ontology\econometria\graph.jsonl` |
| Checkpoints | `C:\NEVEN\docs\ontologia\checkpoints\` |
| Script | `C:\NEVEN\scripts\add_book.py` |

---

## EJEMPLO COMPLETO

**Usuario:** "Agrega el libro Excel para Científicos"

**Agente ejecuta:**

1. **Indexar RAG:**
   ```
   POST /api/rag/upload
   {"file_path": "F:\\libros\\Excel para Científicos.pdf", "domain": "excel"}
   → "Document indexed successfully"
   ```

2. **Preguntar:** "¿Deseas extraer entidades de conocimiento? (toma más tiempo, usa tokens)"

3. **Si SÍ - Procesar ontología:**
   ```
   POST /api/ontology/process
   {"file_path": "...", "domain": "excel", "max_pages": 100}
   → entities_created: 45
   ```

4. **Crear checkpoint:**
   ```python
   create_checkpoint("F:\\libros\\Excel para Científicos.pdf", "excel", 45, 23)
   → 477 páginas
   ```

5. **Verificar:**
   ```
   GET /api/ontology/books?domain=excel
   → Libro aparece con 477 páginas
   ```

6. **Responder:** 
   > "He agregado 'Excel para Científicos' al sistema de conocimiento de NEVEN:
   > - 477 páginas indexadas para búsqueda
   > - 45 entidades extraídas
   > - 23 relaciones creadas
   > 
   > El libro ya está disponible para mejorar las respuestas del Excel Consultant."

---

## NOTAS IMPORTANTES

1. **RAG es obligatorio** — Sin esto no hay búsqueda
2. **Ontología es opcional** — Mejora respuestas pero usa tokens
3. **Checkpoint es obligatorio** — Sin esto la UI no muestra el libro
4. **Siempre verificar** — Confirmar que todo funcionó
5. **Preguntar antes de ontología** — Consume recursos del LLM
