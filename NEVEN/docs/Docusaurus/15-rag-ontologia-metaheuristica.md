---
id: rag-ontologia-metaheuristica
title: "Capitulo 15 - RAG con Ontología como Metaheurística"
sidebar_label: 15. RAG y Ontología
sidebar_position: 15
---

# Capitulo 15: RAG con Ontología como Metaheurística

**Disponible desde:** Agosto 2026 (NEVEN v2.7)

NEVEN incluye un sistema de **Retrieval Augmented Generation (RAG)** que usa la ontología del proyecto como **metaheurística de búsqueda**. Esta arquitectura innovadora mejora significativamente la precisión y velocidad de las respuestas del asistente de IA.

---

## 15.1 ¿Qué problema resuelve?

### Sin RAG
El modelo de lenguaje responde basándose solo en su entrenamiento. Las respuestas pueden ser:
- Desactualizadas (el modelo no conoce libros nuevos)
- Genéricas (no específicas al dominio del usuario)
- No verificables (no hay fuentes)

### Con RAG
El modelo consulta una base de conocimiento antes de responder:
- Respuestas fundamentadas en libros de referencia
- Fuentes verificables (libro, página, score de relevancia)
- Conocimiento específico del dominio

### Con RAG + Ontología (NEVEN)
La ontología **guía la búsqueda** para que sea más rápida y precisa:
- Detecta el dominio de la pregunta automáticamente
- Expande la query con sinónimos y términos relacionados
- Filtra la búsqueda al dominio relevante (reduce espacio de búsqueda)
- Traduce entre idiomas (EN/ES/PT/FR)

---

## 15.2 Flujo: AGENTE → ONTOLOGÍA → RAG → AGENTE

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. USUARIO PREGUNTA                          │
│              "¿Qué es el análisis de componentes principales?"  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. ONTOLOGÍA GUÍA                            │
│  - Detecta entidad: "ACP" → entity[PCA, domain=econometria]     │
│  - Detecta dominio: "econometria"                               │
│  - Expande query: + "PCA", "principal components", "reducción"  │
│  - Traduce: ES→EN, EN→ES bidireccional                          │
│  - 213 entidades de 6 schemas YAML guían la búsqueda            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. RAG BUSCA                                 │
│  - Genera embedding de la query expandida (bge-small-en-v1.5)   │
│  - Filtra chunks por dominio detectado                          │
│  - Búsqueda vectorial en DuckDB + VSS                           │
│  - Retorna top-K chunks con score > minScore                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. AGENTE RESPONDE                           │
│  - Recibe chunks como contexto adicional                        │
│  - Genera respuesta fundamentada en las fuentes                 │
│  - TaskPane muestra popup con fuentes (libro, página, score)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 15.3 Ontología como Metaheurística

### ¿Qué es una metaheurística?

Una metaheurística es una estrategia de alto nivel que **guía la búsqueda** en un espacio de soluciones. En lugar de buscar exhaustivamente, usa conocimiento del problema para:
1. **Reducir el espacio de búsqueda** (poda)
2. **Dirigir la búsqueda** hacia regiones prometedoras
3. **Explorar vecindarios** de soluciones buenas

### Cómo la ontología actúa como metaheurística

| Aspecto | RAG tradicional | NEVEN RAG |
|:---|:---|:---|
| **Espacio de búsqueda** | Todos los chunks (3,700+) | Solo chunks del dominio (~300-800) |
| **Query expansion** | Solo embeddings | Embeddings + sinónimos de ontología |
| **Conocimiento del dominio** | Ninguno | 213 entidades con relaciones |
| **Multi-idioma** | Requiere modelo multilingüe | Diccionario de traducción bidireccional |

### Analogía con metaheurísticas clásicas

| Metaheurística | Equivalente en NEVEN RAG |
|:---|:---|
| **Espacio de soluciones** | Todos los chunks indexados |
| **Función objetivo** | Similaridad coseno con query |
| **Vecindario** | Chunks del mismo dominio |
| **Heurística de poda** | Filtrado por dominio detectado |
| **Operador de variación** | Expansión de query con sinónimos |

---

## 15.4 Componentes técnicos

### Motor de embeddings

```python
# fastembed con modelo bge-small-en-v1.5
from fastembed import TextEmbedding
model = TextEmbedding(model_name='BAAI/bge-small-en-v1.5')
# 384 dimensiones, 67MB, funciona sin GPU
```

### Base de datos vectorial

```python
# DuckDB con extensión VSS (Vector Similarity Search)
import duckdb
conn = duckdb.connect('rag_index.duckdb')
conn.execute("INSTALL vss; LOAD vss;")
```

### Extracción de documentos

```python
# MarkItDown de Microsoft (primario) + PyMuPDF (fallback)
from markitdown import MarkItDown
md = MarkItDown(enable_plugins=False)
result = md.convert("libro.pdf")
# Preserva estructura: headings, tablas, listas
```

### Ontología YAML

```yaml
# docs/ontologia/neven-core/neven-ontology-p2.yaml
schema: neven-p2
version: "1.0"
domain: estadistica
entities:
  - id: proc_pca_001
    name: "PCA"
    aliases: ["ACP", "principal component analysis", "componentes principales"]
    type: procedure
    description: "Análisis de Componentes Principales"
```

---

## 15.5 Métricas del sistema

| Métrica | Valor |
|:---|:---|
| Documentos indexados | 10 libros PDF |
| Chunks totales | 3,709 |
| Tamaño del índice | ~13 MB (DuckDB) |
| Modelo de embeddings | bge-small-en-v1.5 (67MB, 384 dims) |
| Idiomas soportados | EN, ES, PT, FR |
| Entidades de ontología | 213 (de 6 schemas YAML) |
| Dominios | excel, econometria, estadistica, neven |

---

## 15.6 Configuración

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
|:---|:---|:---|
| `enabled` | Activar/desactivar RAG | true |
| `topK` | Número de chunks a retornar | 3 |
| `minScore` | Score mínimo de relevancia (0-1) | 0.5 |
| `ontologyPath` | Ruta a las ontologías | docs/ontologia |
| `indexPath` | Ruta al índice DuckDB | data/rag_index.duckdb |

---

## 15.7 Indexar documentos

### Desde NEVEN Studio

1. Abrir pestaña **RAG** en NEVEN Studio
2. Click en **Indexar Documento**
3. Seleccionar archivo (PDF, DOCX, XLSX, PPTX)
4. Elegir dominio

### Formatos soportados

| Formato | Extractor | Notas |
|:---|:---|:---|
| PDF | MarkItDown | Preserva estructura, tablas |
| DOCX | MarkItDown | Headings, estilos |
| XLSX | MarkItDown | Tablas como Markdown |
| PPTX | MarkItDown | Diapositivas como secciones |
| TXT/MD | Directo | Sin procesamiento |

### API REST

```bash
# Indexar documento
POST /api/rag/upload
{
  "file_path": "C:\\Users\\...\\mi_libro.pdf",
  "domain": "econometria"
}

# Consultar RAG
POST /api/rag/query
{
  "query": "¿Qué es regresión lineal?",
  "domain": "econometria",
  "top_k": 5
}

# Ver documentos indexados
GET /api/rag/documents

# Estadísticas
GET /api/rag/stats
```

---

## 15.8 Expandir la ontología

### Regla de oro

> **NUNCA editar archivos YAML existentes directamente.**
> La ontología usa formato append-only.

### Crear archivo nuevo (recomendado)

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

### Agregar entidades a archivo existente

Solo agregar **al final** del bloque `entities`:

```yaml
# AGREGAR AL FINAL de neven-ontology-p2.yaml
  - id: proc_mi_funcion_nuevo
    name: "MI.FUNCION"
    aliases: ["mi funcion", "my function"]
    type: procedure
    domain: estadistica
    description: "Nueva función agregada"
```

### Validar antes de guardar

```powershell
python -c "import yaml; yaml.safe_load(open('mi-archivo.yaml', encoding='utf-8'))"
```

### Errores comunes de YAML

```yaml
# MAL - escapes inválidos en comillas dobles
path: "C:\NEVEN\functions"

# BIEN - usar comillas simples para paths Windows
path: 'C:\NEVEN\functions'

# MAL - falta espacio después de :
key:value

# BIEN
key: value
```

---

## 15.9 Troubleshooting

### "RAG Engine no disponible"
```powershell
pip install fastembed duckdb pyyaml
# El primer uso descarga el modelo (~67MB)
```

### "0 chunks encontrados"
- Verificar documentos indexados: `GET /api/rag/documents`
- Verificar dominio de la query coincide con documentos
- Bajar `minScore` en config (ej: 0.3)

### "Ontología no carga entidades"
```powershell
# Validar YAML
python -c "import yaml; yaml.safe_load(open('archivo.yaml'))"
```
- Usar comillas simples para paths Windows
- Verificar espacios después de `:` en mappings

### Respuestas sin fuentes
- Verificar `RAG.enabled = true` en config
- Verificar `RAG.minScore` no es muy alto
- Revisar logs en `C:\NEVEN\neven.log`

---

## 15.10 Arquitectura de archivos

```
C:\NEVEN\
├── startup/
│   ├── neven_http_server.py    # Servidor HTTP (endpoints RAG)
│   ├── rag_engine.py           # Motor RAG con MarkItDown
│   ├── ontology_engine.py      # Carga ontologías YAML
│   └── ontology_manager.py     # Gestión de entidades
├── docs/
│   └── ontologia/
│       ├── neven-core/         # Ontología del sistema
│       │   ├── neven-ontology-p1.yaml
│       │   ├── neven-ontology-p2.yaml
│       │   ├── neven-ontology-p3.yaml
│       │   └── neven-ontology-p4.yaml
│       ├── econometrics/       # Términos econométricos
│       │   ├── schema.yaml
│       │   └── graph.jsonl
│       └── excel-functions/    # Funciones de Excel
│           └── excel-functions-ontology.yaml
├── data/
│   └── rag_index.duckdb        # Índice vectorial
└── neven-config.json           # Configuración RAG
```

---

## 15.11 Contribución académica

El uso de la ontología como metaheurística para RAG es una **contribución novel** de NEVEN:

1. **Reducción del espacio de búsqueda**: Filtra por dominio detectado semánticamente
2. **Expansión semántica**: Usa sinónimos y relaciones de la ontología
3. **Multi-idioma sin modelo multilingüe**: Diccionario de traducción bidireccional
4. **Verificabilidad**: Fuentes con página y score visible al usuario

Esta arquitectura podría aplicarse a otros sistemas RAG donde existe conocimiento estructurado del dominio.

---

*NEVEN v2.7 — RAG con Ontología como Metaheurística*
*Agosto 2026*
