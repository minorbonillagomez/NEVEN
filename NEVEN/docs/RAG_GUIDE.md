# NEVEN RAG Engine — Guía del Usuario

## Flujo: AGENTE → ONTOLOGÍA → RAG → AGENTE

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. USUARIO PREGUNTA                          │
│              "¿Qué es el análisis de componentes principales?"  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. ONTOLOGÍA GUÍA                            │
│  - Detecta dominio: "econometria"                               │
│  - Expande query: "ACP" → "PCA", "principal components"         │
│  - 213 entidades de 6 schemas YAML guían la búsqueda            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. RAG BUSCA                                 │
│  - Genera embedding de la query expandida                       │
│  - Busca en DuckDB con filtro de dominio                        │
│  - Retorna top-K chunks con score > minScore                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. AGENTE RESPONDE                           │
│  - Recibe chunks como contexto                                  │
│  - Genera respuesta fundamentada en las fuentes                 │
│  - Muestra popup con fuentes (libro, página, score)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Indexar Documentos

### Desde NEVEN Studio (TaskPane)

1. Abrir pestaña **RAG** en NEVEN Studio
2. Click en **Indexar Documento**
3. Seleccionar archivo (PDF, DOCX, XLSX, PPTX)
4. Elegir dominio (econometria, estadistica, excel, o crear nuevo)
5. Esperar indexación (usa MarkItDown para mejor extracción)

### Desde código (Python)

```python
from rag_engine import RAGEngine

engine = RAGEngine()
engine.add_document(
    file_path="mi_libro.pdf",
    domain="econometria",
    metadata={"author": "Wooldridge", "year": 2020}
)
```

### Formatos soportados

| Formato | Extensión | Dependencia | Calidad |
|---------|-----------|-------------|---------|
| PDF | .pdf | markitdown[pdf], pdfplumber | ★★★★★ |
| Word | .docx | markitdown[docx] | ★★★★★ |
| PowerPoint | .pptx | markitdown[pptx] | ★★★★☆ |
| Excel nuevo | .xlsx | markitdown[xlsx] | ★★★★☆ |
| Excel legacy | .xls | markitdown[xls] | ★★★☆☆ |
| EPUB | .epub | ebooklib | ★★★★★ |
| HTML | .html, .htm | (built-in) | ★★★★☆ |
| CSV | .csv | (built-in) | ★★★★★ |
| JSON | .json | (built-in) | ★★★★★ |
| XML | .xml | (built-in) | ★★★★☆ |
| Texto / Markdown | .txt, .md | (built-in) | ★★★★★ |
| ZIP | .zip | (built-in, itera contenido) | ★★★☆☆ |

> Todos los formatos funcionan **100% offline**, sin APIs externas.

---

## Expandir la Ontología

### Regla de oro: NUNCA editar archivos existentes directamente

La ontología usa formato **append-only**. Para agregar entidades:

### 1. Crear archivo nuevo (recomendado)

```yaml
# docs/ontologia/mi-dominio/mi-extension.yaml
schema: mi-dominio-extension
version: "1.0"
domain: mi_dominio
entities:
  - id: ent_mi_concepto_001
    name: "Mi Concepto"
    aliases: ["concepto", "my concept"]
    type: concept
    description: "Descripción del concepto"
```

### 2. Agregar entidades a archivo existente

Si necesitas agregar a un archivo existente, **solo agregar al final**:

```yaml
# AGREGAR AL FINAL de neven-ontology-p2.yaml
  - id: proc_mi_funcion_nuevo
    name: "MI.FUNCION"
    aliases: ["mi funcion", "my function"]
    type: procedure
    domain: estadistica
    description: "Nueva función agregada"
```

### 3. Validar ANTES de guardar

```powershell
python -c "import yaml; yaml.safe_load(open('mi-archivo.yaml', encoding='utf-8'))"
```

### Errores comunes a evitar

```yaml
# ❌ MAL - escapes inválidos en comillas dobles
path: "C:\NEVEN\functions"

# ✅ BIEN - usar comillas simples para paths Windows
path: 'C:\NEVEN\functions'

# ❌ MAL - falta espacio después de :
key:value

# ✅ BIEN
key: value
```

---

## Estructura de Archivos

```
C:\NEVEN\
├── startup/
│   ├── neven_http_server.py    # Servidor HTTP (incluye endpoints RAG)
│   ├── rag_engine.py           # Motor RAG con MarkItDown
│   ├── ontology_engine.py      # Carga y consulta ontologías
│   └── ontology_manager.py     # Gestión de entidades
├── docs/
│   └── ontologia/
│       ├── neven-core/         # Ontología del sistema NEVEN
│       ├── econometrics/       # Términos econométricos
│       └── excel-functions/    # Funciones de Excel
├── data/
│   └── rag_index.duckdb        # Índice vectorial (se crea automáticamente)
└── neven-config.json           # Configuración RAG
```

---

## Configuración RAG

En `neven-config.json`:

```json
{
  "RAG": {
    "enabled": true,
    "topK": 3,
    "minScore": 0.5,
    "ontologyPath": "C:\\NEVEN\\docs\\ontologia",
    "indexPath": "C:\\NEVEN\\data\\rag_index.duckdb"
  }
}
```

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `enabled` | Activar/desactivar RAG | true |
| `topK` | Número de chunks a retornar | 3 |
| `minScore` | Score mínimo de relevancia (0-1) | 0.5 |
| `ontologyPath` | Ruta a las ontologías | docs/ontologia |
| `indexPath` | Ruta al índice DuckDB | data/rag_index.duckdb |

---

## Endpoints API

### GET /api/rag/stats
Estadísticas del índice RAG.

### GET /api/rag/documents
Lista de documentos indexados.

### POST /api/rag/upload
Indexar un documento nuevo.
```json
{
  "file_path": "C:\\Users\\...\\mi_libro.pdf",
  "domain": "econometria"
}
```

### GET /api/rag/browse
Abre el explorador de archivos nativo de Windows y retorna la ruta seleccionada.
```json
{
  "status": "ok",
  "path": "C:\\Users\\Minor\\Documents\\libro.pdf",
  "filename": "libro.pdf"
}
```

### POST /api/rag/query
Consultar el RAG.
```json
{
  "query": "¿Qué es regresión lineal?",
  "domain": "econometria",
  "top_k": 5
}
```

### POST /api/rag/delete
Eliminar un documento del índice.
```json
{
  "document_id": "abc123..."
}
```

---

## Dependencias Python

El RAG requiere estos paquetes (se instalan automáticamente con el instalador):

```
fastembed                           # Embeddings locales (bge-small-en-v1.5)
duckdb                              # Base de datos vectorial con VSS
pyyaml                              # Parsing de ontologías YAML
markitdown[pdf,docx,xlsx,pptx,xls]  # Extracción: PDF, DOCX, PPTX, XLSX, XLS
ebooklib                            # Extracción de EPUB
pdfplumber                          # Extracción de páginas PDF (preserva numeración)
pymupdf                             # Fallback para PDFs
```

> HTML, CSV, JSON, XML, TXT, MD y ZIP no requieren dependencias adicionales.

---

## Troubleshooting

### "RAG Engine no disponible"
- Verificar que `fastembed` está instalado: `pip install fastembed`
- El primer uso descarga el modelo de embeddings (~67MB)

### "0 chunks encontrados"
- Verificar que hay documentos indexados: GET /api/rag/documents
- Verificar el dominio de la query coincide con los documentos
- Bajar minScore en neven-config.json (ej: 0.3)

### "Ontología no carga entidades"
- Validar YAML: `python -c "import yaml; yaml.safe_load(open('archivo.yaml'))"`
- Revisar escapes en paths Windows (usar comillas simples)
- Verificar espacios después de `:` en todos los mappings

---

*NEVEN v3.2 — RAG con Ontología como Metaheurística*
*Agosto 2026*
