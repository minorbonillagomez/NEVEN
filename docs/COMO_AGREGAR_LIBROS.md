# NEVEN — Cómo Agregar Libros al Sistema de Conocimiento

> **Versión:** 1.0  
> **Fecha:** 2026-08-19  
> **Autor:** Minor Bonilla Gómez  

---

## Arquitectura del Sistema de Conocimiento

NEVEN tiene **tres componentes** que trabajan juntos para gestionar el conocimiento de los libros:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUJO DE PROCESAMIENTO DE LIBROS                      │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   PDF/DOCX   │
                              │   (Libro)    │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
           ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
           │    1. RAG      │ │  2. ONTOLOGÍA  │ │ 3. CHECKPOINT  │
           │   (ChromaDB)   │ │  (graph.jsonl) │ │    (.json)     │
           └────────────────┘ └────────────────┘ └────────────────┘
                    │                │                    │
                    │                │                    │
                    ▼                ▼                    ▼
           ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
           │   Búsqueda     │ │   Expansión    │ │   UI Books     │
           │   Vectorial    │ │   por Grafos   │ │   (páginas)    │
           └────────────────┘ └────────────────┘ └────────────────┘
```

### 1. RAG (Retrieval-Augmented Generation)
- **Qué hace:** Divide el libro en chunks y los indexa en ChromaDB
- **Endpoint:** `POST /api/rag/upload`
- **Resultado:** Permite búsqueda semántica sobre el contenido
- **Archivos:** `C:\NEVEN\rag\chroma_db\` (base de datos vectorial)

### 2. Ontología (Grafo de Conocimiento)
- **Qué hace:** Extrae entidades (conceptos, fórmulas, técnicas) y relaciones usando LLM
- **Endpoint:** `POST /api/ontology/process`
- **Resultado:** Enriquece búsquedas expandiendo por relaciones
- **Archivos:** `C:\NEVEN\docs\ontologia\<domain>\graph.jsonl`

### 3. Checkpoint (Metadatos UI)
- **Qué hace:** Guarda progreso de procesamiento y metadatos del libro
- **Resultado:** La UI muestra cantidad de páginas y estado de procesamiento
- **Archivos:** `C:\NEVEN\docs\ontologia\checkpoints\<book>_<domain>_<hash>.json`

---

## Proceso Completo para Agregar un Libro

### Paso 1: Preparar el archivo

1. Colocar el PDF en la carpeta del dominio correspondiente:
   - Econometría: `ontologia-fuentes/LIBROS ECONOMETRIA/`
   - Excel: `ontologia-fuentes/LIBROS EXCEL/`
   - Álgebra: `ontologia-fuentes/ALGEBRA/`

2. Verificar que el PDF sea legible (no escaneado sin OCR)

### Paso 2: Indexar al RAG

```http
POST http://localhost:5555/api/rag/upload
Content-Type: application/json

{
    "file_path": "F:\\ANTIGRAVITY\\2026\\NEVEN\\ontologia-fuentes\\LIBROS ECONOMETRIA\\MiLibro.pdf",
    "domain": "econometria"
}
```

**Respuesta exitosa:**
```json
{
    "status": "ok",
    "doc_id": "MiLibro.pdf",
    "message": "Document indexed successfully"
}
```

**Qué sucede internamente:**
1. El PDF se extrae con MarkItDown
2. El texto se divide en chunks (~500 tokens cada uno)
3. Cada chunk se embebe con el modelo de embeddings
4. Los vectores se almacenan en ChromaDB con metadata (domain, filename)

### Paso 3: Procesar para Ontología (Opcional pero recomendado)

```http
POST http://localhost:5555/api/ontology/process
Content-Type: application/json

{
    "file_path": "F:\\ANTIGRAVITY\\2026\\NEVEN\\ontologia-fuentes\\LIBROS ECONOMETRIA\\MiLibro.pdf",
    "domain": "econometria",
    "max_pages": 50
}
```

**Qué sucede internamente:**
1. El PDF se extrae y divide en chunks de ~4000 caracteres
2. Cada chunk se envía al LLM con el prompt de extracción
3. El LLM extrae entidades (conceptos, fórmulas, técnicas) y relaciones
4. Las entidades se guardan en `graph.jsonl`
5. Se crea/actualiza el checkpoint con progreso

**Nota:** Este proceso usa tokens del LLM. Para libros grandes, usar `max_pages` para limitar.

### Paso 4: Crear Checkpoint para UI

Si solo se indexó al RAG (sin ontología), crear checkpoint manualmente para que la UI muestre las páginas:

```powershell
# Obtener número de páginas
$pdf = "F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS ECONOMETRIA\MiLibro.pdf"
python -c "from PyPDF2 import PdfReader; print(len(PdfReader('$pdf').pages))"

# Crear checkpoint
$hash = (Get-FileHash $pdf -Algorithm MD5).Hash.Substring(0, 12).ToLower()
$checkpoint = @{
    file_path = $pdf
    domain = "econometria"
    total_pages = 300  # <-- Número real de páginas
    processed_pages = 300
    status = "completed"
    entities_created = 0  # 0 si solo RAG
    relations_created = 0
} | ConvertTo-Json

$checkpointPath = "C:\NEVEN\docs\ontologia\checkpoints\MiLibro_econometria_$hash.json"
[System.IO.File]::WriteAllText($checkpointPath, $checkpoint)
```

### Paso 5: Verificar

1. **RAG indexado:**
   ```http
   GET http://localhost:5555/api/rag/list
   ```

2. **UI actualizada:**
   ```http
   GET http://localhost:5555/api/ontology/books?domain=econometrics
   ```

3. **Búsqueda funciona:**
   ```http
   POST http://localhost:5555/api/rag/query
   {"query": "concepto del libro", "domain": "econometria", "top_k": 5}
   ```

---

## Dominios Disponibles

| Dominio | ID | Descripción |
|---------|-----|-------------|
| Excel | `excel` | Funciones, fórmulas, técnicas de Excel |
| Econometría | `econometria` | Econometría, series de tiempo, panel data |
| Estadística | `estadistica` | Pruebas estadísticas, métodos |
| Álgebra Lineal | `algebra_lineal` | Matrices, vectores, transformaciones |

---

## Estructura de Archivos

```
C:\NEVEN\
├── rag\
│   └── chroma_db\           # Base de datos vectorial
├── docs\
│   └── ontologia\
│       ├── checkpoints\     # Metadatos de libros procesados
│       │   ├── Libro1_econometria_abc123.json
│       │   └── Libro2_excel_def456.json
│       ├── excel\
│       │   └── graph.jsonl  # Entidades y relaciones
│       └── econometria\
│           └── graph.jsonl
└── startup\
    └── neven_http_server.py # Servidor HTTP (puerto 5555)
```

---

## Troubleshooting

### La UI muestra "? págs"

**Causa:** No existe checkpoint para el libro.

**Solución:** Crear checkpoint manualmente (ver Paso 4).

### El libro no aparece en la lista de libros

**Causa:** `list_processed_books()` busca entidades con `source_book` en graph.jsonl.

**Solución:** 
- Procesar el libro con ontología (Paso 3), o
- Mejorar `list_processed_books()` para también leer de checkpoints

### La búsqueda no encuentra contenido del libro

**Causa:** El libro no está indexado en RAG.

**Solución:** Ejecutar Paso 2 (indexar al RAG).

### El libro está en RAG pero las relaciones no funcionan

**Causa:** El libro no fue procesado para ontología.

**Solución:** Ejecutar Paso 3 (procesar ontología) — requiere tokens LLM.

---

## Script de Automatización Completo

```python
#!/usr/bin/env python3
"""
add_book.py — Script para agregar un libro completo a NEVEN
Uso: python add_book.py <path_to_pdf> <domain>
"""
import sys
import os
import json
import hashlib
import requests
from PyPDF2 import PdfReader

def add_book(pdf_path: str, domain: str, process_ontology: bool = False):
    """
    Agrega un libro al sistema de conocimiento de NEVEN.
    
    Args:
        pdf_path: Ruta absoluta al PDF
        domain: Dominio (econometria, excel, estadistica, algebra_lineal)
        process_ontology: Si True, también procesa entidades (usa tokens LLM)
    """
    base_url = "http://localhost:5555"
    
    # 1. Verificar archivo
    if not os.path.isfile(pdf_path):
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return False
    
    book_name = os.path.basename(pdf_path)
    print(f"📚 Procesando: {book_name}")
    
    # 2. Obtener número de páginas
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        print(f"   Páginas: {total_pages}")
    except Exception as e:
        print(f"⚠️  No se pudo leer páginas: {e}")
        total_pages = 0
    
    # 3. Indexar al RAG
    print("🔄 Indexando al RAG...")
    try:
        resp = requests.post(f"{base_url}/api/rag/upload", json={
            "file_path": pdf_path,
            "domain": domain
        }, timeout=300)
        result = resp.json()
        if result.get("status") == "ok":
            print(f"   ✅ RAG: {result.get('message')}")
        else:
            print(f"   ❌ RAG error: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ❌ RAG error: {e}")
        return False
    
    # 4. Procesar ontología (opcional)
    entities_created = 0
    relations_created = 0
    if process_ontology:
        print("🔄 Procesando ontología (esto puede tardar varios minutos)...")
        try:
            resp = requests.post(f"{base_url}/api/ontology/process", json={
                "file_path": pdf_path,
                "domain": domain,
                "max_pages": 100  # Limitar para no gastar muchos tokens
            }, timeout=1800)
            result = resp.json()
            if result.get("status") == "ok":
                entities_created = result.get("entities_created", 0)
                relations_created = result.get("relations_created", 0)
                print(f"   ✅ Ontología: {entities_created} entidades, {relations_created} relaciones")
            else:
                print(f"   ⚠️  Ontología: {result.get('error')}")
        except Exception as e:
            print(f"   ⚠️  Ontología error: {e}")
    
    # 5. Crear checkpoint
    print("🔄 Creando checkpoint...")
    checkpoint_dir = r"C:\NEVEN\docs\ontologia\checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Hash del archivo para identificación única
    with open(pdf_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()[:12]
    
    checkpoint_name = os.path.splitext(book_name)[0]
    checkpoint_path = os.path.join(checkpoint_dir, f"{checkpoint_name}_{domain}_{file_hash}.json")
    
    checkpoint_data = {
        "file_path": pdf_path,
        "domain": domain,
        "total_pages": total_pages,
        "processed_pages": total_pages,
        "status": "completed",
        "entities_created": entities_created,
        "relations_created": relations_created
    }
    
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2)
    
    print(f"   ✅ Checkpoint: {os.path.basename(checkpoint_path)}")
    
    # 6. Resumen
    print()
    print("═" * 50)
    print(f"✅ Libro agregado exitosamente: {book_name}")
    print(f"   Dominio: {domain}")
    print(f"   Páginas: {total_pages}")
    print(f"   RAG: ✅ Indexado")
    print(f"   Ontología: {'✅ ' + str(entities_created) + ' entidades' if process_ontology else '⏭️  No procesado'}")
    print(f"   UI: ✅ Checkpoint creado")
    print("═" * 50)
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python add_book.py <path_to_pdf> <domain> [--ontology]")
        print("Dominios: econometria, excel, estadistica, algebra_lineal")
        print("Flags: --ontology = también procesar entidades (usa tokens LLM)")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    domain = sys.argv[2]
    process_ontology = "--ontology" in sys.argv
    
    add_book(pdf_path, domain, process_ontology)
```

---

## Mejoras Pendientes

1. **Integración automática:** Actualmente RAG y Ontología son procesos separados. Ideal: un solo endpoint que haga ambos.

2. **UI unificada:** La UI debería mostrar libros tanto de RAG como de ontología.

3. **Progreso en tiempo real:** Implementar WebSocket para mostrar progreso de procesamiento.

4. **Validación de duplicados:** Detectar si un libro ya está indexado antes de procesarlo.

---

## Referencias

- **Ontology Manager:** `src/ControlPython/startup/ontology_manager.py`
- **HTTP Server:** `src/ControlPython/startup/neven_http_server.py`
- **RAG Engine:** `src/ControlPython/startup/rag_engine.py`
- **Checkpoints:** `C:\NEVEN\docs\ontologia\checkpoints\`
