---
inclusion: manual
---

# NEVEN — Pipeline Completo: PDF → Markdown → LaTeX → RAG

> **Propósito:** Documentar el pipeline completo para convertir PDFs de libros técnicos en contenido indexable con ecuaciones renderizables en KaTeX.
>
> **Cuándo usar:** Cuando necesites agregar libros con contenido matemático/estadístico al sistema de conocimiento de NEVEN.

---

## Resumen del Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 1: EXTRACCIÓN    │  PDF → Markdown (pymupdf4llm)                      │
│  FASE 2: PRE-PROCESO   │  Fix encoding roto (solo algunos PDFs)             │
│  FASE 3: CONVERSIÓN    │  Unicode → LaTeX (símbolos matemáticos)            │
│  FASE 4: INDEXACIÓN    │  Markdown → RAG (embeddings + chunks)              │
│  FASE 5: ONTOLOGÍA     │  Entidades + Relaciones (opcional, usa LLM)        │
│  FASE 6: CHECKPOINT    │  Metadatos para UI (páginas, estado)               │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tiempo total estimado:** 
- Fases 1-4: 5-15 minutos por libro
- Fase 5 (ontología): 10-60 minutos adicionales (usa LLM)

---

## FASE 1: Extracción PDF → Markdown

### Herramienta: pymupdf4llm

**Por qué pymupdf4llm:**
- Preserva estructura (headers, tablas, listas)
- Extrae ecuaciones como Unicode (α, β, ∑) en lugar de imágenes
- Más rápido y confiable que alternativas (Marker, Nougat, Pix2Text)

**Instalación:**
```bash
pip install pymupdf4llm
```

**Uso básico:**
```python
import pymupdf4llm
from pathlib import Path

pdf_path = r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS ECONOMETRIA\libro.pdf"
output_path = r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS ECONOMETRIA\markdown\libro.md"

# Extraer
md_text = pymupdf4llm.to_markdown(pdf_path)

# Guardar
Path(output_path).write_text(md_text, encoding='utf-8')
print(f"Extraído: {len(md_text):,} caracteres")
```

**Directorio de salida:**
```
ontologia-fuentes/
└── LIBROS ECONOMETRIA/
    ├── *.pdf                    # PDFs originales
    ├── markdown/                # Markdown crudo (con Unicode)
    │   └── *.md
    └── markdown_latex/          # Markdown procesado (con LaTeX)
        └── *.md
```

### Problemas conocidos de extracción

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Timeout | Proceso cuelga | Aumentar timeout, procesar por páginas |
| "float division by zero" | Error en pymupdf | PDF corrupto, intentar re-descargar |
| U+FFFD masivo | Muchos � en output | Pérdida irrecuperable, fuente del PDF rota |

---

## FASE 2: Pre-procesamiento (Condicional)

### ¿Cuándo es necesario?

**Solo para PDFs con encoding de fuente roto.** El caso conocido es Wooldridge (2002).

**Cómo detectarlo:**
```python
# Si el archivo tiene muchos de estos caracteres, necesita fix
suspicious_chars = ['ð', 'Þ', 'þ', '¼', '¤']
with open(md_file, encoding='utf-8') as f:
    content = f.read()
for char in suspicious_chars:
    count = content.count(char)
    if count > 100:
        print(f"ALERTA: {char} aparece {count} veces - posible encoding roto")
```

### Fix para Wooldridge (y similares)

**Herramienta:** `C:\NEVEN\tools\fix_wooldridge.py`

**Mapeo de caracteres:**
| Caracter | Unicode | Significado real |
|----------|---------|------------------|
| ð | U+00F0 | `(` paréntesis izquierdo |
| Þ | U+00DE | `)` paréntesis derecho |
| þ | U+00FE | `+` signo más |
| ¼ | U+00BC | `=` signo igual |
| ¤ | U+00A4 | `ff` ligature |

**Uso:**
```bash
python C:\NEVEN\tools\fix_wooldridge.py input.md output.md --stats
```

**IMPORTANTE:** Ejecutar ANTES de la conversión Unicode→LaTeX.

---

## FASE 3: Conversión Unicode → LaTeX + Limpieza de Artefactos

### Diccionario de Símbolos Estándar

👉 **Ver: `latex-symbol-dictionary.md`** — Referencia canónica de todos los mapeos Unicode→LaTeX

Este diccionario contiene:
- 100+ símbolos matemáticos organizados por categoría
- Códigos Unicode exactos (U+XXXX)
- Comandos LaTeX correspondientes
- Notas sobre caracteres excluidos y por qué
- Instrucciones para agregar nuevos símbolos

### Herramienta: unicode_to_latex.py

**Ubicación:** `C:\NEVEN\tools\unicode_to_latex.py`

**Qué convierte (100+ símbolos):**

| Categoría | Ejemplos |
|-----------|----------|
| Griegas | α→`\alpha`, β→`\beta`, Σ→`\Sigma` |
| Operadores | ∑→`\sum`, ∫→`\int`, ∂→`\partial` |
| Relaciones | ≤→`\leq`, ≥→`\geq`, ≠→`\neq` |
| Flechas | →→`\to`, ⇒→`\Rightarrow` |
| Lógica | ∀→`\forall`, ∃→`\exists` |
| Estimadores | `_β_<sup>ˆ</sup>`→`\hat{\beta}` |
| Superíndices | ²→`^{2}`, `<sup>n</sup>`→`^{n}` |
| Subíndices | ₁→`_{1}`, `<sub>i</sub>`→`_{i}` |

### Limpieza de Artefactos de pymupdf4llm

> **IMPORTANTE:** `pymupdf4llm` introduce artefactos HTML y markdown que deben limpiarse
> ANTES de indexar al RAG. Si no se limpian, aparecerán literalmente en las fuentes
> mostradas al usuario.

**Artefactos que se limpian automáticamente:**

| Artefacto | Origen | Limpieza |
|-----------|--------|----------|
| `<br>`, `<br/>` | Saltos de línea HTML | Se reemplaza por espacio |
| `\langle`, `\rangle` | Conversión previa incorrecta | Se convierte a `<`, `>` |
| `||` repetidos | Tablas markdown rotas | Se limpian |
| ` `` ` múltiples | Código inline roto | Se reducen a uno |
| `___` repetidos | Separadores de tabla | Se eliminan |
| `....` largos | Gráficos/scatter plots | Se truncan a `...` |

**Verificar limpieza:**
```python
# Después de indexar, verificar que no haya artefactos
import duckdb
conn = duckdb.connect(r'C:\NEVEN\data\rag_index.duckdb', read_only=True)
br = conn.execute("SELECT COUNT(*) FROM chunks WHERE content LIKE '%<br>%'").fetchone()[0]
langle = conn.execute("SELECT COUNT(*) FROM chunks WHERE content LIKE '%\\langle%'").fetchone()[0]
print(f'Chunks con <br>: {br}')  # Debe ser 0
print(f'Chunks con \\langle: {langle}')  # Debe ser 0
conn.close()
```

**Uso individual:**
```bash
python C:\NEVEN\tools\unicode_to_latex.py input.md output.md --stats
```

**Uso batch (todos los archivos):**
```bash
python C:\NEVEN\tools\unicode_to_latex.py markdown/ markdown_latex/ --batch --stats
```

### Pipeline automatizado

**Herramienta:** `C:\NEVEN\tools\convert_all_md.py`

Este script detecta automáticamente si un archivo necesita pre-procesamiento:

```bash
python C:\NEVEN\tools\convert_all_md.py
```

**Lo que hace:**
1. Lee todos los `.md` de `markdown/`
2. Si es Wooldridge → aplica `fix_wooldridge.py` primero
3. Aplica `unicode_to_latex.py`
4. Guarda en `markdown_latex/`

---

## FASE 4: Indexación al RAG

### Herramienta: index_markdown_books.py

**Ubicación:** `C:\NEVEN\tools\index_markdown_books.py`

**Qué hace:**
- Lee archivos `.md` de `markdown_latex/`
- Divide en chunks (500 caracteres, 50 overlap)
- Genera embeddings (bge-small-en, 384 dimensiones)
- Guarda en DuckDB (`C:\NEVEN\data\rag_index.duckdb`)

**Uso:**
```bash
# Crear índice nuevo (borra el existente)
python C:\NEVEN\tools\index_markdown_books.py

# Agregar a índice existente
python C:\NEVEN\tools\index_markdown_books.py --append
```

### Configuración de libros

El script tiene un diccionario `BOOK_METADATA` que mapea archivos a metadatos:

```python
BOOK_METADATA = {
    "wooldridge_j-_2002_econometric_analysis....md": 
        ("econometria", "Wooldridge - Panel Data", "en"),
    "An Introduction to Statistical Learning with R.md": 
        ("estadistica", "Introduction to Statistical Learning", "en"),
    # ... etc
}
```

**Para agregar un libro nuevo:**
1. Agregar entrada al diccionario
2. Re-ejecutar el script

---

## FASE 5: Ontología — Entidades y Relaciones (Opcional)

### ¿Qué es la ontología?

La ontología extrae **entidades** (conceptos, fórmulas, técnicas) y **relaciones** entre ellas usando LLM. Esto permite:
- Búsquedas más inteligentes ("¿qué métodos usan OLS?")
- Navegación por conceptos relacionados
- Visualización de grafos de conocimiento

### Estructura de archivos

```
C:\NEVEN\ontology\
├── domains.json           # Lista de dominios disponibles
├── econometria/
│   ├── schema.yaml        # Tipos de entidades válidos
│   └── graph.jsonl        # Entidades y relaciones
├── excel/
│   ├── schema.yaml
│   └── graph.jsonl
└── estadistica/
    ├── schema.yaml
    └── graph.jsonl
```

### Formato de graph.jsonl

Cada línea es un objeto JSON (entidad o relación):

```jsonl
{"type": "entity", "id": "ols_001", "label": "Ordinary Least Squares", "entity_type": "method", "properties": {"abbreviation": "OLS", "domain": "econometria"}}
{"type": "entity", "id": "beta_hat_001", "label": "Beta Hat Estimator", "entity_type": "estimator", "properties": {"formula": "\\hat{\\beta} = (X'X)^{-1}X'y"}}
{"type": "relation", "source": "ols_001", "target": "beta_hat_001", "relation_type": "produces", "properties": {}}
```

### Procesar ontología vía API

**Requisito:** El servidor HTTP debe estar corriendo (Excel + TaskPane abierto).

```http
POST http://localhost:5555/api/ontology/process
Content-Type: application/json

{
    "file_path": "F:\\ruta\\al\\libro.pdf",
    "domain": "econometria",
    "max_pages": 100
}
```

**Respuesta:**
```json
{
    "status": "ok",
    "entities_created": 45,
    "relations_created": 23,
    "pages_processed": 100
}
```

### Procesar ontología manualmente

Si prefieres control manual o no tienes el servidor HTTP:

```python
import sys
sys.path.insert(0, r'C:\NEVEN\startup')
from ontology_manager import OntologyManager

manager = OntologyManager(r'C:\NEVEN\ontology')

# Procesar un libro
manager.process_document(
    file_path=r'F:\...\markdown_latex\libro.md',
    domain='econometria',
    max_pages=100  # Limitar para libros grandes
)

# Ver estadísticas
stats = manager.get_stats('econometria')
print(f"Entidades: {stats['entities']}, Relaciones: {stats['relations']}")
```

### Schema de entidades (schema.yaml)

Define los tipos de entidades válidos para cada dominio:

```yaml
# C:\NEVEN\ontology\econometria\schema.yaml
entity_types:
  - method          # OLS, GMM, IV
  - estimator       # β̂, σ̂²
  - test            # t-test, F-test, Hausman
  - assumption      # homoskedasticity, exogeneity
  - concept         # endogeneity, multicollinearity
  - formula         # ecuaciones importantes
  - dataset         # datasets de ejemplo

relation_types:
  - produces        # method → estimator
  - requires        # method → assumption
  - tests           # test → assumption
  - relates_to      # concept → concept
  - uses            # method → formula
```

### Visualización de la ontología

**Endpoint para obtener grafo:**
```http
GET http://localhost:5555/api/ontology/graph?domain=econometria&format=json
```

**Respuesta (para visualización con D3.js o similar):**
```json
{
    "nodes": [
        {"id": "ols_001", "label": "OLS", "type": "method"},
        {"id": "beta_hat_001", "label": "β̂", "type": "estimator"}
    ],
    "edges": [
        {"source": "ols_001", "target": "beta_hat_001", "type": "produces"}
    ]
}
```

### Consideraciones de costo

⚠️ **La extracción de ontología usa tokens del LLM activo.**

| Tamaño libro | Páginas | Tokens estimados | Tiempo |
|--------------|---------|------------------|--------|
| Pequeño | <100 | ~50K | 5-10 min |
| Mediano | 100-300 | ~150K | 15-30 min |
| Grande | 300-800 | ~400K | 30-60 min |

**Recomendaciones:**
- Usar `max_pages` para limitar procesamiento
- Procesar solo secciones relevantes (teoría, no ejercicios)
- Omitir si solo necesitas búsqueda vectorial (RAG)

---

## FASE 6: Checkpoint para UI

### ¿Qué es un checkpoint?

Un archivo JSON con metadatos del libro para que la UI muestre:
- Nombre del libro
- Páginas totales/procesadas
- Estado (completed, processing, error)
- Entidades/relaciones creadas

### Ubicación

```
C:\NEVEN\docs\ontologia\checkpoints\
├── Wooldridge - Panel Data_econometria_abc123.json
├── Excel 365 Bible_excel_def456.json
└── ...
```

### Formato del checkpoint

```json
{
    "book_name": "Wooldridge - Panel Data",
    "domain": "econometria",
    "total_pages": 752,
    "processed_pages": 752,
    "status": "completed",
    "entities_created": 156,
    "relations_created": 89,
    "source": "pdf-to-rag-pipeline",
    "indexed_at": "2026-08-19T16:30:00Z"
}
```

### Crear checkpoint manualmente

```python
import json
import hashlib
import os
from datetime import datetime

def create_checkpoint(book_name, domain, total_pages, entities=0, relations=0):
    checkpoint_dir = r"C:\NEVEN\docs\ontologia\checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Nombre limpio para archivo
    safe_name = book_name.replace(":", " -").replace("?", "").replace("*", "")
    file_hash = hashlib.md5(book_name.encode()).hexdigest()[:12]
    
    checkpoint_path = os.path.join(
        checkpoint_dir, 
        f"{safe_name}_{domain}_{file_hash}.json"
    )
    
    checkpoint_data = {
        "book_name": book_name,
        "domain": domain,
        "total_pages": total_pages,
        "processed_pages": total_pages,
        "status": "completed",
        "entities_created": entities,
        "relations_created": relations,
        "source": "pdf-to-rag-pipeline",
        "indexed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    
    return checkpoint_path
```

### Verificar checkpoints

```http
GET http://localhost:5555/api/ontology/books?domain=econometria
```

**Respuesta:**
```json
{
    "books": [
        {
            "name": "Wooldridge - Panel Data",
            "pages": 752,
            "status": "completed",
            "entities": 156
        }
    ]
}
```

---

## Pipeline Completo: Paso a Paso

### Agregar UN libro nuevo (completo)

```bash
# 1. Extraer PDF a Markdown
python -c "
import pymupdf4llm
from pathlib import Path
pdf = r'F:\...\nuevo_libro.pdf'
md = pymupdf4llm.to_markdown(pdf)
Path(r'F:\...\markdown\nuevo_libro.md').write_text(md, encoding='utf-8')
"

# 2. Verificar si necesita fix (buscar caracteres sospechosos)
python -c "
with open(r'F:\...\markdown\nuevo_libro.md', encoding='utf-8') as f:
    c = f.read()
for char in ['ð', 'Þ', 'þ', '¼']:
    print(f'{char}: {c.count(char)}')"

# 3. Si necesita fix (más de 100 de algún caracter):
python C:\NEVEN\tools\fix_wooldridge.py nuevo_libro.md nuevo_libro_fixed.md

# 4. Convertir Unicode → LaTeX
python C:\NEVEN\tools\unicode_to_latex.py nuevo_libro.md ../markdown_latex/nuevo_libro.md

# 5. Agregar al BOOK_METADATA en index_markdown_books.py

# 6. Re-indexar al RAG
python C:\NEVEN\tools\index_markdown_books.py

# 7. (Opcional) Procesar ontología - requiere servidor HTTP corriendo
curl -X POST http://localhost:5555/api/ontology/process \
  -H "Content-Type: application/json" \
  -d '{"file_path": "F:\\...\\nuevo_libro.pdf", "domain": "econometria", "max_pages": 100}'

# 8. Crear checkpoint para UI
python -c "
import json, hashlib, os
from datetime import datetime

book_name = 'Nombre del Libro'
domain = 'econometria'
total_pages = 500  # Ajustar

checkpoint_dir = r'C:\NEVEN\docs\ontologia\checkpoints'
os.makedirs(checkpoint_dir, exist_ok=True)

safe_name = book_name.replace(':', ' -')
file_hash = hashlib.md5(book_name.encode()).hexdigest()[:12]

data = {
    'book_name': book_name,
    'domain': domain,
    'total_pages': total_pages,
    'processed_pages': total_pages,
    'status': 'completed',
    'entities_created': 0,
    'relations_created': 0,
    'indexed_at': datetime.utcnow().isoformat() + 'Z'
}

path = os.path.join(checkpoint_dir, f'{safe_name}_{domain}_{file_hash}.json')
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
print(f'Checkpoint: {path}')
"
```

### Agregar libro RÁPIDO (solo RAG, sin ontología)

```bash
# Fases 1-4 solamente
python C:\NEVEN\tools\convert_all_md.py
python C:\NEVEN\tools\index_markdown_books.py
```

### Re-procesar TODOS los libros

```bash
# 1. Asegurar que todos los PDFs están extraídos a markdown/

# 2. Ejecutar pipeline completo
python C:\NEVEN\tools\convert_all_md.py

# 3. Re-indexar
python C:\NEVEN\tools\index_markdown_books.py
```

---

## Verificación

### Verificar conversión LaTeX

```python
# Buscar si quedan símbolos Unicode sin convertir
python -c "
from pathlib import Path
from collections import Counter

orphans = Counter()
for f in Path(r'F:\...\markdown_latex').glob('*.md'):
    for c in f.read_text(encoding='utf-8'):
        if ord(c) > 127:
            orphans[c] += 1

print('Top 10 caracteres no-ASCII restantes:')
for char, count in orphans.most_common(10):
    print(f'  {char!r} U+{ord(char):04X}: {count}')"
```

### Verificar indexación RAG

```python
import duckdb
conn = duckdb.connect(r'C:\NEVEN\data\rag_index.duckdb', read_only=True)
docs = conn.execute('SELECT filename, domain FROM documents').fetchall()
chunks = conn.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
print(f'Documentos: {len(docs)}')
print(f'Chunks: {chunks}')
for d in docs:
    print(f'  {d[0][:50]}... [{d[1]}]')
```

### Verificar búsqueda con LaTeX

```python
import sys
sys.path.insert(0, r'C:\NEVEN\startup')
from rag_engine import get_rag_engine

engine = get_rag_engine(r'C:\NEVEN\data\rag_index.duckdb')
result = engine.query("beta hat estimator", domain="econometria", top_k=2)

for r in result:
    content = r.get('content', r[1] if isinstance(r, tuple) else '')
    if '\\hat' in content or '\\beta' in content:
        print("[CONTIENE LATEX] ✓")
    print(content[:200])
```

---

## Ubicación de Herramientas

| Herramienta | Ubicación | Propósito |
|-------------|-----------|-----------|
| `unicode_to_latex.py` | `C:\NEVEN\tools\` | Conversor Unicode→LaTeX |
| `fix_wooldridge.py` | `C:\NEVEN\tools\` | Fix encoding roto |
| `convert_all_md.py` | `C:\NEVEN\tools\` | Pipeline automatizado |
| `index_markdown_books.py` | `C:\NEVEN\tools\` | Indexador de MD |
| `test_rag_query.py` | `C:\NEVEN\tools\` | Verificación de búsqueda |

---

## Troubleshooting

### "Las ecuaciones no renderizan en KaTeX"

**Causa:** Los símbolos están en Unicode, no LaTeX.

**Solución:** Re-procesar con `convert_all_md.py` y re-indexar.

### "El archivo de Wooldridge tiene paréntesis raros"

**Causa:** Encoding de fuente no estándar (ð=`(`, Þ=`)`)

**Solución:** Ejecutar `fix_wooldridge.py` ANTES de `unicode_to_latex.py`.

### "El proceso de indexación se cuelga"

**Causa:** Documento muy grande genera OOM al crear embeddings.

**Solución:** El script usa batches de 100 chunks. Si aún falla, reducir batch size.

### "Quedan muchos U+FFFD (�)"

**Causa:** Pérdida irrecuperable durante extracción PDF.

**Solución:** No hay fix. El PDF original tiene fuentes que pymupdf no puede interpretar.

### "¼ se convierte a \frac{1}{4} pero debería ser ="

**Causa:** Solo en Wooldridge, ¼ significa `=`.

**Solución:** Ejecutar `fix_wooldridge.py` primero. El conversor base NO convierte ¼ precisamente por este caso.

---

## Decisiones de Diseño

### ¿Por qué Markdown intermedio en lugar de indexar PDF directo?

1. **Inspección:** Podemos ver y corregir el contenido extraído
2. **Post-procesamiento:** Podemos convertir Unicode→LaTeX
3. **Reproducibilidad:** Re-indexar es instantáneo sin re-extraer PDF

### ¿Por qué no convertir ð/Þ/þ a \eth/\TH/\th?

En la mayoría de PDFs, estos caracteres NO aparecen. En Wooldridge, significan paréntesis y +. Convertirlos a LaTeX rompería el texto.

### ¿Por qué excluir ¼ del conversor base?

En Wooldridge (el libro más importante de econometría), ¼ significa `=`. Si lo convertimos a `\frac{1}{4}`, todas las ecuaciones de igualdad se rompen.

### ¿Por qué batches de 100 para embeddings?

Wooldridge tiene 640 chunks. Generar todos los embeddings de una vez causa OOM en algunos sistemas. Batches de 100 son un balance entre velocidad y uso de memoria.

---

## Ejemplo: Output Antes/Después

### ANTES (Unicode crudo, no renderiza en KaTeX)
```
El estimador β̂₁ tiene varianza Var(β̂₁) = σ²/Σ(xᵢ - x̄)²
```

### DESPUÉS (LaTeX, renderiza correctamente)
```
El estimador \hat{\beta}_1 tiene varianza Var(\hat{\beta}_1) = \sigma^2/\sum(x_i - \bar{x})^2
```

---

## Mantenimiento

### Agregar nuevos símbolos al conversor

1. **Consultar** `latex-symbol-dictionary.md` para verificar que no existe
2. **Identificar** el código Unicode (usar `ord(char)` en Python)
3. **Editar** `C:\NEVEN\tools\unicode_to_latex.py`:
   ```python
   # En la sección correspondiente (GREEK_LOWER, MATH_OPERATORS, etc.)
   MATH_OPERATORS['⊛'] = r'\circledast'
   ```
4. **Actualizar** `latex-symbol-dictionary.md` con el nuevo símbolo
5. **Re-procesar** los archivos afectados

### Agregar nuevo libro con encoding roto

1. Analizar qué caracteres están mal mapeados
2. Crear fix específico o extender `fix_wooldridge.py`
3. Agregar al pipeline de `convert_all_md.py`

---

## Resumen Rápido para el Agente

```
¿Usuario quiere agregar libro técnico con ecuaciones?
│
├─ 1. Extraer: pymupdf4llm.to_markdown(pdf) → markdown/
│
├─ 2. Verificar encoding: ¿muchos ð/Þ/þ/¼?
│   └─ Sí → python fix_wooldridge.py input.md output.md
│
├─ 3. Convertir: python unicode_to_latex.py ... → markdown_latex/
│
├─ 4. Indexar RAG: python index_markdown_books.py
│
├─ 5. (Opcional) Ontología: POST /api/ontology/process
│   └─ Requiere servidor HTTP + usa tokens LLM
│
├─ 6. Checkpoint: Crear JSON en checkpoints/ para UI
│
└─ 7. Verificar: 
    ├─ RAG: Buscar "beta hat" → debe encontrar \hat{\beta}
    ├─ Ontología: GET /api/ontology/graph?domain=...
    └─ UI: GET /api/ontology/books?domain=...
```

---

## Diagrama de Flujo Visual

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    PDF      │────▶│  Markdown   │────▶│   LaTeX     │
│  (fuente)   │     │  (Unicode)  │     │  (limpio)   │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      │            fix_wooldridge.py    unicode_to_latex.py
      │             (si necesario)
      │                                       │
      │                                       ▼
      │                              ┌─────────────────┐
      │                              │      RAG        │
      │                              │   (DuckDB +     │
      │                              │   embeddings)   │
      │                              └─────────────────┘
      │                                       │
      ▼                                       │
┌─────────────────┐                          │
│   Ontología     │◀─────────────────────────┘
│  (graph.jsonl)  │         (opcional, usa LLM)
└─────────────────┘
      │
      ▼
┌─────────────────┐
│   Checkpoint    │
│    (UI JSON)    │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│  Visualización  │
│  (TaskPane UI)  │
└─────────────────┘
```
