---
inclusion: manual
---

# NEVEN — Instrucciones para Agregar Libros al Sistema de Conocimiento

> **Propósito:** Este documento contiene las instrucciones completas para que cualquier agente de IA pueda agregar un libro al sistema de conocimiento de NEVEN.
> 
> **Cuándo usar:** Cuando el usuario pida agregar, indexar, o procesar un libro/PDF para que NEVEN lo use en sus respuestas.

---

## Resumen del Proceso

Agregar un libro a NEVEN requiere **4 pasos** en este orden:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PASO 1: RAG          → Búsqueda vectorial (chunks en ChromaDB)         │
│  PASO 2: ONTOLOGÍA    → Entidades y relaciones (graph.jsonl)            │
│  PASO 3: CHECKPOINT   → Metadatos para UI (páginas, estado)             │
│  PASO 4: VERIFICACIÓN → Confirmar que todo funciona                     │
└─────────────────────────────────────────────────────────────────────────┘
```

**IMPORTANTE:** El servidor HTTP debe estar corriendo (Excel abierto con NEVEN).

---

## PASO 1: Indexar al RAG

**Qué hace:** Divide el libro en chunks y los indexa en ChromaDB para búsqueda semántica.

**Endpoint:**
```http
POST http://localhost:5555/api/rag/upload
Content-Type: application/json

{
    "file_path": "F:\\ruta\\al\\libro.pdf",
    "domain": "excel"
}
```

**Dominios válidos:**
- `excel` — Funciones, fórmulas, VBA, modelado financiero
- `econometria` — Econometría, series de tiempo, panel data
- `estadistica` — Pruebas estadísticas, probabilidad
- `algebra_lineal` — Matrices, vectores, álgebra lineal

**Respuesta exitosa:**
```json
{
    "status": "ok",
    "doc_id": "nombre_libro.pdf",
    "message": "Document indexed successfully"
}
```

**Tiempo estimado:** 1-10 minutos según tamaño del PDF.

---

## PASO 2: Procesar Ontología (OPCIONAL pero recomendado)

**Qué hace:** Extrae entidades (conceptos, fórmulas, técnicas) y relaciones usando LLM.

**Endpoint:**
```http
POST http://localhost:5555/api/ontology/process
Content-Type: application/json

{
    "file_path": "F:\\ruta\\al\\libro.pdf",
    "domain": "excel",
    "max_pages": 100
}
```

**Parámetros:**
- `max_pages`: Limitar páginas a procesar (recomendado para libros grandes)
- Sin este parámetro procesa todo el libro

**Respuesta exitosa:**
```json
{
    "status": "ok",
    "entities_created": 45,
    "relations_created": 23,
    "pages_processed": 100
}
```

**NOTA:** Este paso **usa tokens del LLM activo**. Para libros grandes, considerar:
- Limitar con `max_pages`
- Procesar solo las secciones más relevantes
- Omitir si el usuario solo quiere búsqueda vectorial

**Tiempo estimado:** 5-30 minutos según páginas y velocidad del LLM.

---

## PASO 3: Crear Checkpoint para UI

**Qué hace:** Crea un archivo JSON con metadatos para que la UI muestre páginas y estado.

**Ubicación:** `C:\NEVEN\docs\ontologia\checkpoints\`

**Formato del nombre de archivo:**
```
{NombreLibro}_excel_{hash12}.json
```

**IMPORTANTE:** 
- NO usar caracteres ilegales en Windows: `: * ? " < > |`
- El `book_name` DENTRO del JSON puede tener caracteres especiales
- El NOMBRE DEL ARCHIVO debe ser "limpio"

**Contenido del checkpoint:**
```json
{
    "book_name": "Nombre del Libro (con acentos: está bien)",
    "domain": "excel",
    "total_pages": 456,
    "processed_pages": 456,
    "status": "completed",
    "entities_created": 45,
    "relations_created": 23,
    "source": "add_book_process"
}
```

**Script Python para crear checkpoint:**
```python
import json
import hashlib
import os
from PyPDF2 import PdfReader

def create_checkpoint(pdf_path, domain, entities=0, relations=0):
    checkpoint_dir = r"C:\NEVEN\docs\ontologia\checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Obtener páginas
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    
    # Nombre del libro
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Nombre limpio para archivo (sin caracteres ilegales)
    safe_name = book_name.replace(":", " -").replace("?", "").replace("*", "")
    
    # Hash único
    file_hash = hashlib.md5(book_name.encode()).hexdigest()[:12]
    
    # Crear checkpoint
    checkpoint_path = os.path.join(checkpoint_dir, f"{safe_name}_{domain}_{file_hash}.json")
    
    checkpoint_data = {
        "book_name": book_name,
        "domain": domain,
        "total_pages": total_pages,
        "processed_pages": total_pages,
        "status": "completed",
        "entities_created": entities,
        "relations_created": relations,
    }
    
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    
    return checkpoint_path
```

---

## PASO 4: Verificación

Después de completar los pasos anteriores, verificar:

### 4.1 Verificar RAG
```http
GET http://localhost:5555/api/rag/list
```
Buscar el libro en la lista de documentos.

### 4.2 Verificar UI
```http
GET http://localhost:5555/api/ontology/books?domain=excel
```
El libro debe aparecer con sus páginas.

### 4.3 Verificar búsqueda
```http
POST http://localhost:5555/api/rag/query
{
    "query": "término del libro",
    "domain": "excel",
    "top_k": 3
}
```
Debe encontrar chunks del libro recién agregado.

---

## Script Completo de Automatización

Existe un script que hace todo el proceso:

```bash
# Solo RAG + Checkpoint (rápido, no usa LLM)
python C:\NEVEN\scripts\add_book.py "F:\ruta\libro.pdf" excel

# RAG + Ontología + Checkpoint (lento, usa LLM)
python C:\NEVEN\scripts\add_book.py "F:\ruta\libro.pdf" excel --ontology

# Con límite de páginas para ontología
python C:\NEVEN\scripts\add_book.py "F:\ruta\libro.pdf" excel --ontology --max-pages 50
```

---

## Convenciones de Nombres

Para evitar duplicados y problemas de matching:

1. **Sin extensión .pdf** en `book_name`
2. **Formato estándar:** `Título del Libro (Autor principal)`
3. **Un solo nombre canónico** por libro
4. **Consistencia** con los checkpoints existentes

**Ejemplos buenos:**
- `Microsoft Excel 365 Bible`
- `Applied Econometrics with R (Kleiber & Zeileis)`
- `Introduccion a la econometria-Wooldridge`

**Ejemplos malos:**
- `libro.pdf` ❌
- `Microsoft_Excel_365_Bible.pdf` ❌
- `EXCEL BIBLE` ❌ (inconsistente con otros)

---

## Troubleshooting

### El servidor no responde
- Verificar que Excel está abierto con NEVEN cargado
- El TaskPane debe estar abierto al menos una vez para iniciar el servidor

### El libro no aparece en la UI
- Verificar que existe el checkpoint en `C:\NEVEN\docs\ontologia\checkpoints\`
- El nombre en el checkpoint debe coincidir con el dominio consultado

### La búsqueda no encuentra el libro
- Verificar que el libro fue indexado al RAG (paso 1)
- Probar con diferentes términos de búsqueda

### Error "File not found"
- Usar rutas absolutas con doble backslash: `F:\\ruta\\libro.pdf`
- Verificar que el archivo existe

### Timeout durante procesamiento
- Para libros grandes (>500 páginas), usar `max_pages`
- El procesamiento de ontología es intensivo en LLM

---

## Ubicaciones de Archivos

| Componente | Ubicación |
|------------|-----------|
| RAG Database | `C:\NEVEN\data\rag_index.duckdb` |
| Ontología Excel | `C:\NEVEN\ontology\excel\graph.jsonl` |
| Ontología Econometría | `C:\NEVEN\ontology\econometria\graph.jsonl` |
| Checkpoints | `C:\NEVEN\docs\ontologia\checkpoints\` |
| Script add_book | `C:\NEVEN\scripts\add_book.py` |
| Servidor HTTP | `C:\NEVEN\startup\neven_http_server.py` |

---

## Flujo de Decisión para el Agente

```
¿El usuario quiere agregar un libro?
    │
    ├─ SÍ → ¿El servidor HTTP está corriendo?
    │       │
    │       ├─ NO → Indicar: "Abre Excel y el TaskPane de NEVEN"
    │       │
    │       └─ SÍ → ¿Qué tipo de procesamiento?
    │               │
    │               ├─ Solo búsqueda rápida → PASO 1 + PASO 3
    │               │
    │               └─ Búsqueda + entidades → PASO 1 + PASO 2 + PASO 3
    │
    └─ NO → Continuar con otra tarea
```

---

## Ejemplo Completo

**Usuario dice:** "Agrega el libro Excel para Científicos que está en F:\libros\"

**Agente ejecuta:**

```python
# 1. Indexar al RAG
POST /api/rag/upload
{"file_path": "F:\\libros\\Excel para Científicos.pdf", "domain": "excel"}

# 2. (Opcional) Procesar ontología
POST /api/ontology/process
{"file_path": "F:\\libros\\Excel para Científicos.pdf", "domain": "excel", "max_pages": 100}

# 3. Crear checkpoint
import json, hashlib, os
from PyPDF2 import PdfReader

pdf_path = r"F:\libros\Excel para Científicos.pdf"
reader = PdfReader(pdf_path)
pages = len(reader.pages)

book_name = "Excel para Científicos"
safe_name = book_name
file_hash = hashlib.md5(book_name.encode()).hexdigest()[:12]

checkpoint = {
    "book_name": book_name,
    "domain": "excel",
    "total_pages": pages,
    "status": "completed",
    "entities_created": 0  # o el número real si se procesó ontología
}

checkpoint_path = f"C:\\NEVEN\\docs\\ontologia\\checkpoints\\{safe_name}_excel_{file_hash}.json"
with open(checkpoint_path, 'w', encoding='utf-8') as f:
    json.dump(checkpoint, f, indent=2, ensure_ascii=False)

# 4. Verificar
GET /api/ontology/books?domain=excel
# Confirmar que el libro aparece con páginas
```

**Agente responde:** "He agregado 'Excel para Científicos' al sistema. El libro tiene X páginas y ya está disponible para búsquedas. ¿Quieres que también procese las entidades de conocimiento? (esto toma más tiempo y usa tokens del LLM)"

---

## Notas Finales

1. **El RAG es obligatorio** — Sin esto, el libro no es buscable
2. **La ontología es opcional** — Mejora las respuestas pero consume tokens
3. **El checkpoint es obligatorio** — Sin esto, la UI no muestra el libro
4. **Siempre verificar** — Confirmar que el proceso completó correctamente
