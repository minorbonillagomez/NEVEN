"""
NEVEN RAG Engine - Ontology-Guided Retrieval Augmented Generation
==================================================================
Motor de busqueda semantica con filtrado por ontologia.

Componentes:
- TextEmbedding (fastembed) - Embeddings locales (bge-small-en-v1.5, 384 dim)
- DuckDB + VSS - Almacenamiento y busqueda vectorial
- Ontologia NEVEN - Metaheuristica para filtrar chunks relevantes

Uso:
    engine = RAGEngine()
    engine.add_document("mi_libro.pdf", "econometria")
    results = engine.query("que es regresion lineal", domain="econometria")
"""

import os
import re
import json
import hashlib
import time
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

import duckdb

# Lazy loading de fastembed para evitar carga lenta al importar
_embedding_model = None

def _get_embedding_model():
    """Singleton del modelo de embeddings."""
    global _embedding_model
    if _embedding_model is None:
        from fastembed import TextEmbedding
        # Modelo ligero pero efectivo (67MB, 384 dimensiones)
        _embedding_model = TextEmbedding(model_name='BAAI/bge-small-en-v1.5')
    return _embedding_model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Genera embeddings para una lista de textos."""
    model = _get_embedding_model()
    embeddings = list(model.embed(texts))
    # Convertir numpy.float32 a float nativo de Python para DuckDB
    return [[float(x) for x in emb] for emb in embeddings]


def generate_embedding(text: str) -> List[float]:
    """Genera embedding para un solo texto."""
    return generate_embeddings([text])[0]


def clean_pdf_text(text: str) -> str:
    """
    Limpia texto extraído de PDFs con problemas de encoding.
    
    Problemas comunes:
    - Fuentes Symbol/Math con mapeo incorrecto a Unicode
    - Caracteres de control invisibles
    - Secuencias de guiones/espacios repetidos
    - Ligaduras rotas (fi, fl, ff)
    
    Args:
        text: Texto crudo del PDF
        
    Returns:
        Texto limpio y normalizado
    """
    if not text:
        return text
    
    # 1. Reemplazar caracteres de fuentes matemáticas mal mapeados
    # Estos son comunes en PDFs académicos con fórmulas
    math_replacements = {
        'φ': 'phi',      # phi griego
        'μ': 'mu',       # mu griego
        'σ': 'sigma',    # sigma griego
        'ρ': 'rho',      # rho (correlación)
        'β': 'beta',     # beta
        'α': 'alpha',    # alpha
        'γ': 'gamma',    # gamma
        'δ': 'delta',    # delta
        'ε': 'epsilon',  # epsilon
        'θ': 'theta',    # theta
        'λ': 'lambda',   # lambda
        'π': 'pi',       # pi
        'Σ': 'SUM',      # sumatoria
        'Π': 'PROD',     # productoria
        '∞': 'inf',      # infinito
        '≈': '~',        # aproximado
        '≠': '!=',       # diferente
        '≤': '<=',       # menor o igual
        '≥': '>=',       # mayor o igual
        '→': '->',       # flecha derecha
        '←': '<-',       # flecha izquierda
        '∈': 'in',       # pertenece
        '∂': 'd',        # derivada parcial
        '√': 'sqrt',     # raíz cuadrada
    }
    
    for char, replacement in math_replacements.items():
        text = text.replace(char, replacement)
    
    # 2. Eliminar caracteres de control (excepto newline y tab)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 3. Normalizar espacios múltiples y guiones repetidos
    text = re.sub(r'-{3,}', '---', text)  # Máximo 3 guiones seguidos
    text = re.sub(r'\.{4,}', '...', text)  # Máximo 3 puntos
    text = re.sub(r' {3,}', '  ', text)    # Máximo 2 espacios
    
    # 4. Detectar y marcar texto probablemente corrupto
    # Si hay demasiados caracteres raros seguidos, es texto basura
    # Patrón: más de 5 caracteres no-alfanuméricos consecutivos (excepto espacios y puntuación común)
    text = re.sub(r'[^\w\s.,;:!?()[\]{}"\'-]{6,}', ' [FORMULA] ', text)
    
    # 5. Limpiar secuencias como "( ) Var Yt ( )" que son fórmulas mal extraídas
    # Detectar patrones de fórmulas rotas y simplificar
    text = re.sub(r'\(\s*\)\s*(?=[A-Z])', '', text)  # "( ) Var" -> "Var"
    text = re.sub(r'(?<=[a-z])\s*\(\s*\)\s*(?=[A-Z])', ' ', text)  # "x ( ) Y" -> "x Y"
    
    # 6. Normalizar saltos de línea
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


# ---------------------------------------------------------------------------
# Chunking de documentos
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Divide texto en chunks con overlap para preservar contexto.
    
    Args:
        text: Texto completo del documento
        chunk_size: Tamano aproximado de cada chunk en palabras
        overlap: Palabras de overlap entre chunks
    
    Returns:
        Lista de chunks de texto
    """
    # Limpiar texto
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    
    if len(words) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
        
        # Evitar loop infinito
        if end == len(words):
            break
    
    return chunks


# ---------------------------------------------------------------------------
# Extracción con MarkItDown (Microsoft)
# ---------------------------------------------------------------------------

def extract_with_markitdown(file_path: str) -> str:
    """
    Extrae texto de un archivo usando MarkItDown de Microsoft.
    
    Soporta: PDF, DOCX, XLSX, PPTX, HTML, TXT, MD, y más.
    Preserva estructura como Markdown (headings, tablas, listas).
    
    Args:
        file_path: Ruta al archivo
    
    Returns:
        Texto extraído en formato Markdown
    """
    try:
        from markitdown import MarkItDown
        md = MarkItDown(enable_plugins=False)
        result = md.convert(file_path)
        return result.markdown
    except ImportError:
        raise ImportError("MarkItDown no instalado. Ejecuta: pip install 'markitdown[pdf,docx,xlsx,pptx]'")
    except Exception as e:
        print(f"[RAG] MarkItDown error para {file_path}: {e}")
        raise


def extract_text_with_pages_markitdown(file_path: str) -> List[Dict[str, Any]]:
    """
    Extrae texto de un archivo con información de página usando MarkItDown.
    
    Para PDFs, intenta preservar la estructura de páginas.
    Para otros formatos, retorna todo como "página 1".
    
    Returns:
        Lista de dicts con {page: int, text: str}
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    # Para PDFs, usamos pdfplumber para mantener info de páginas
    # pero procesamos el texto con MarkItDown para mejor estructura
    if suffix == '.pdf':
        try:
            import pdfplumber
            from markitdown import MarkItDown
            
            pages = []
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    text = clean_pdf_text(text)  # Limpiar texto extraído
                    if text.strip():
                        pages.append({"page": i, "text": text})
            
            # Si pdfplumber no extrajo bien, usar MarkItDown como fallback
            if not pages or sum(len(p["text"]) for p in pages) < 100:
                md = MarkItDown(enable_plugins=False)
                result = md.convert(file_path)
                if result.markdown.strip():
                    return [{"page": 1, "text": clean_pdf_text(result.markdown)}]
            
            return pages
            
        except ImportError as e:
            print(f"[RAG] Fallback a MarkItDown simple: {e}")
            pass
        except Exception as e:
            print(f"[RAG] Error pdfplumber, usando MarkItDown: {e}")
            pass
    
    # Para todos los demás formatos, usar MarkItDown directamente
    try:
        from markitdown import MarkItDown
        md = MarkItDown(enable_plugins=False)
        result = md.convert(file_path)
        return [{"page": 1, "text": result.markdown}]
    except ImportError:
        # Fallback a lectura simple para archivos de texto
        if suffix in ['.txt', '.md', '.r', '.py', '.jl', '.json', '.yaml', '.yml']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return [{"page": 1, "text": f.read()}]
        raise ImportError("MarkItDown no instalado. Ejecuta: pip install 'markitdown[pdf,docx,xlsx,pptx]'")


def extract_text_with_pages(file_path: str) -> List[Dict[str, Any]]:
    """
    Extrae texto de un archivo con información de página.
    
    Usa MarkItDown como método principal para mejor estructura.
    Fallback a PyMuPDF si MarkItDown no está disponible.
    
    Returns:
        Lista de dicts con {page: int, text: str}
    """
    # Intentar con MarkItDown primero
    try:
        return extract_text_with_pages_markitdown(file_path)
    except ImportError:
        pass
    except Exception as e:
        print(f"[RAG] MarkItDown falló, usando PyMuPDF: {e}")
    
    # Fallback a implementación original con PyMuPDF
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix != '.pdf':
        # Para archivos de texto, toda es "página 1"
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return [{"page": 1, "text": f.read()}]
    
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text()
            text = clean_pdf_text(text)  # Limpiar texto extraído
            if text.strip():  # Solo páginas con contenido
                pages.append({"page": i, "text": text})
        doc.close()
        return pages
    except ImportError:
        raise ImportError("Ni MarkItDown ni PyMuPDF instalados. Ejecuta: pip install 'markitdown[pdf]' o pip install pymupdf")


def chunk_text_with_pages(pages: List[Dict[str, Any]], chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Divide texto en chunks preservando información de página.
    
    Args:
        pages: Lista de {page: int, text: str}
        chunk_size: Tamaño aproximado de cada chunk en palabras
        overlap: Palabras de overlap entre chunks
    
    Returns:
        Lista de {page: int, page_end: int, text: str}
    """
    chunks = []
    
    for page_data in pages:
        page_num = page_data["page"]
        text = re.sub(r'\s+', ' ', page_data["text"]).strip()
        words = text.split()
        
        if not words:
            continue
        
        if len(words) <= chunk_size:
            chunks.append({
                "page": page_num,
                "page_end": page_num,
                "text": text
            })
        else:
            start = 0
            while start < len(words):
                end = min(start + chunk_size, len(words))
                chunk_text = ' '.join(words[start:end])
                chunks.append({
                    "page": page_num,
                    "page_end": page_num,
                    "text": chunk_text
                })
                start = end - overlap
                if end == len(words):
                    break
    
    return chunks


def extract_text_from_file(file_path: str) -> str:
    """
    Extrae texto de un archivo usando MarkItDown.
    
    Soporta: PDF, DOCX, PPTX, XLSX, EPUB, HTML, CSV, JSON, XML, TXT, MD, etc.
    Usa MarkItDown como método principal para máxima compatibilidad.
    Fallback a PyMuPDF para PDF si MarkItDown no está disponible.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    # Intentar con MarkItDown primero (soporta 20+ formatos incluyendo EPUB)
    try:
        from markitdown import MarkItDown
        md = MarkItDown(enable_plugins=False)
        result = md.convert(file_path)
        if result.markdown.strip():
            return result.markdown
        # Si MarkItDown no extrajo nada, intentar fallbacks
    except ImportError:
        pass  # MarkItDown no instalado, usar fallbacks
    except Exception as e:
        print(f"[RAG] MarkItDown falló para {path.name}: {e}")
        # Continuar con fallbacks
    
    # Fallback: archivos de texto plano
    if suffix in ['.txt', '.md', '.r', '.py', '.jl', '.json', '.yaml', '.yml', '.csv', '.xml']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    # Fallback: PDF con PyMuPDF
    elif suffix == '.pdf':
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                page_text = page.get_text()
                text += clean_pdf_text(page_text) + "\n"
            doc.close()
            return text
        except ImportError:
            raise ImportError("Ni MarkItDown ni PyMuPDF instalados. Ejecuta: pip install 'markitdown[pdf]'")
    
    else:
        raise ValueError(f"Formato no soportado: {suffix}. Instala MarkItDown: pip install 'markitdown[pdf,docx,xlsx,pptx]'")


# ---------------------------------------------------------------------------
# RAG Engine con DuckDB VSS
# ---------------------------------------------------------------------------

class RAGEngine:
    """
    Motor de Ontology-Guided RAG.
    
    Usa DuckDB con extension VSS para almacenamiento y busqueda vectorial.
    La ontologia actua como metaheuristica para filtrar dominios.
    
    IMPORTANTE: La ontologia se recarga automaticamente cuando se detectan
    cambios en el directorio de ontologia (nuevos archivos, modificaciones).
    """
    
    def __init__(self, db_path: str = ":memory:", ontology_path: Optional[str] = None):
        """
        Inicializa el motor RAG.
        
        Args:
            db_path: Ruta a la base DuckDB (":memory:" para en memoria)
            ontology_path: Ruta al directorio de ontologia NEVEN (opcional)
        """
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        
        # Instalar y cargar extension VSS
        self.conn.execute("INSTALL vss")
        self.conn.execute("LOAD vss")
        
        # Crear tablas
        self._init_tables()
        
        # Inicializar ontologia
        self.ontology = {}
        self.ontology_entities = []
        self.ontology_relations = []  # Lista de relaciones {type, from, to}
        self.ontology_graph = {}  # Grafo de adyacencia: entity_id -> {relation_type -> [entity_ids]}
        self.ontology_path = ontology_path
        self._ontology_file_hashes = {}  # Para detectar cambios
        self._last_ontology_scan = 0
        self._ontology_scan_interval = 60  # Segundos entre escaneos
        
        if ontology_path:
            self._load_ontology(ontology_path)
    
    def _get_file_hash(self, filepath: str) -> str:
        """Obtiene hash MD5 de un archivo para detectar cambios."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _scan_ontology_files(self, ontology_path: str) -> Dict[str, str]:
        """Escanea archivos de ontologia y retorna diccionario path -> hash."""
        file_hashes = {}
        path = Path(ontology_path)
        if not path.exists():
            return file_hashes
        
        for pattern in ["**/*.yaml", "**/*.yml", "**/*.jsonl"]:
            for filepath in path.rglob(pattern.split("/")[-1]):
                file_hashes[str(filepath)] = self._get_file_hash(str(filepath))
        
        return file_hashes
    
    def _check_ontology_updates(self):
        """Verifica si hay cambios en la ontologia y recarga si es necesario."""
        if not self.ontology_path:
            return
        
        current_time = time.time()
        if current_time - self._last_ontology_scan < self._ontology_scan_interval:
            return
        
        self._last_ontology_scan = current_time
        current_hashes = self._scan_ontology_files(self.ontology_path)
        
        # Detectar cambios
        if current_hashes != self._ontology_file_hashes:
            new_files = set(current_hashes.keys()) - set(self._ontology_file_hashes.keys())
            modified_files = {
                f for f in current_hashes.keys() & self._ontology_file_hashes.keys()
                if current_hashes[f] != self._ontology_file_hashes[f]
            }
            removed_files = set(self._ontology_file_hashes.keys()) - set(current_hashes.keys())
            
            if new_files or modified_files or removed_files:
                print(f"[RAG] Cambios detectados en ontologia:")
                if new_files:
                    print(f"  + Nuevos: {[Path(f).name for f in new_files]}")
                if modified_files:
                    print(f"  ~ Modificados: {[Path(f).name for f in modified_files]}")
                if removed_files:
                    print(f"  - Eliminados: {[Path(f).name for f in removed_files]}")
                
                # Recargar ontologia
                self._load_ontology(self.ontology_path)
    
    def get_available_domains(self) -> List[str]:
        """Retorna lista de dominios disponibles en la ontologia."""
        self._check_ontology_updates()
        domains = set()
        for entity in self.ontology_entities:
            if entity.get("domain"):
                domains.add(entity["domain"])
        return sorted(list(domains))
    
    def _init_tables(self):
        """Crea las tablas necesarias."""
        # Tabla de documentos
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR PRIMARY KEY,
                filename VARCHAR,
                domain VARCHAR,
                language VARCHAR DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON
            )
        """)
        
        # Tabla de chunks con embeddings
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id VARCHAR PRIMARY KEY,
                doc_id VARCHAR,
                chunk_index INTEGER,
                content TEXT,
                page INTEGER,
                page_end INTEGER,
                embedding FLOAT[384],
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        
        # Crear indice HNSW para busqueda vectorial
        try:
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
                ON chunks USING HNSW (embedding) 
                WITH (metric = 'cosine')
            """)
        except Exception as e:
            # Si el indice ya existe o hay error, continuar
            print(f"[RAG] Nota sobre indice HNSW: {e}")
    
    def _load_ontology(self, ontology_path: str):
        """Carga la ontologia desde archivos YAML y JSONL."""
        try:
            import yaml
        except ImportError:
            print("[RAG] PyYAML no instalado, ontologia deshabilitada")
            return
        
        path = Path(ontology_path)
        if not path.exists():
            print(f"[RAG] Ontologia no encontrada en {ontology_path}")
            return
        
        # Inicializar almacenes
        self.ontology_entities = []
        self.ontology_relations = []
        self.ontology_graph = {}
        
        # Cargar archivos YAML (schemas y ontologias estructuradas)
        for yaml_file in path.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data:
                        key = yaml_file.stem
                        self.ontology[key] = data
                        
                        # Extraer entidades de ontologia Excel
                        if "funciones" in data:
                            for func in data.get("funciones", []):
                                self.ontology_entities.append({
                                    "id": func.get("nombre", "").lower(),
                                    "type": "ExcelFunction",
                                    "name": func.get("nombre", ""),
                                    "description": func.get("descripcion", ""),
                                    "domain": "excel",
                                    "keywords": [func.get("nombre", "").lower()] + 
                                               [p.get("nombre", "").lower() for p in func.get("parametros", [])]
                                })
                        
                        # Extraer categorias de Excel
                        if "categorias" in data:
                            for cat in data.get("categorias", []):
                                self.ontology_entities.append({
                                    "id": cat.get("id", ""),
                                    "type": "ExcelCategory",
                                    "name": cat.get("nombre", ""),
                                    "description": cat.get("descripcion", ""),
                                    "domain": "excel",
                                    "keywords": [cat.get("id", ""), cat.get("nombre", "").lower()]
                                })
            except Exception as e:
                print(f"[RAG] Error cargando {yaml_file}: {e}")
        
        # Cargar grafos JSONL (entidades de conocimiento de econometria, etc.)
        for jsonl_file in path.rglob("*.jsonl"):
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            record = json.loads(line)
                            if record.get("op") == "create" and "entity" in record:
                                entity = record["entity"]
                                
                                # Soportar ambos formatos: properties nested o flat
                                props = entity.get("properties", {})
                                name = entity.get("name") or props.get("name", "")
                                desc = entity.get("description") or props.get("description", "")
                                keywords = entity.get("keywords") or props.get("keywords", [])
                                
                                # Si no hay keywords, extraer del nombre
                                if not keywords and name:
                                    keywords = [w.lower() for w in name.split() if len(w) > 3]
                                
                                self.ontology_entities.append({
                                    "id": entity.get("id", ""),
                                    "type": entity.get("type", ""),
                                    "name": name,
                                    "description": desc,
                                    "domain": entity.get("domain") or jsonl_file.parent.name,
                                    "keywords": keywords
                                })
                            
                            # Cargar relaciones (op: relate)
                            elif record.get("op") == "relate" and "relation" in record:
                                rel = record["relation"]
                                rel_type = rel.get("type", "")
                                from_id = rel.get("from", "")
                                to_id = rel.get("to", "")
                                
                                if from_id and to_id:
                                    self.ontology_relations.append({
                                        "type": rel_type,
                                        "from": from_id,
                                        "to": to_id
                                    })
                                    
                                    # Construir grafo de adyacencia bidireccional
                                    if from_id not in self.ontology_graph:
                                        self.ontology_graph[from_id] = {}
                                    if rel_type not in self.ontology_graph[from_id]:
                                        self.ontology_graph[from_id][rel_type] = []
                                    if to_id not in self.ontology_graph[from_id][rel_type]:
                                        self.ontology_graph[from_id][rel_type].append(to_id)
                                    
                                    # Agregar direccion inversa para traversal bidireccional
                                    if to_id not in self.ontology_graph:
                                        self.ontology_graph[to_id] = {}
                                    inv_type = f"inv_{rel_type}"
                                    if inv_type not in self.ontology_graph[to_id]:
                                        self.ontology_graph[to_id][inv_type] = []
                                    if from_id not in self.ontology_graph[to_id][inv_type]:
                                        self.ontology_graph[to_id][inv_type].append(from_id)
            except Exception as e:
                print(f"[RAG] Error cargando {jsonl_file}: {e}")
        
        print(f"[RAG] Ontologia cargada: {len(self.ontology)} schemas, {len(self.ontology_entities)} entidades, {len(self.ontology_relations)} relaciones")
        
        # Actualizar hashes de archivos para detectar cambios futuros
        self._ontology_file_hashes = self._scan_ontology_files(ontology_path)
    
    def get_related_entities(self, entity_id: str, max_depth: int = 1, 
                            relation_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Obtiene entidades relacionadas usando el grafo de ontologia.
        
        Traversal de relaciones para expandir contexto semántico.
        
        Args:
            entity_id: ID de la entidad inicial
            max_depth: Profundidad máxima de traversal (1 = vecinos directos)
            relation_types: Tipos de relaciones a seguir (None = todas)
        
        Returns:
            Lista de entidades relacionadas con metadata de la relación
        """
        if entity_id not in self.ontology_graph:
            return []
        
        related = []
        visited = {entity_id}
        queue = [(entity_id, 0)]  # (entity_id, depth)
        
        # Crear lookup rápido de entidades por ID
        entity_lookup = {e["id"]: e for e in self.ontology_entities}
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            if current_id not in self.ontology_graph:
                continue
            
            for rel_type, targets in self.ontology_graph[current_id].items():
                # Filtrar por tipo de relación si se especificó
                if relation_types and rel_type not in relation_types:
                    # Permitir relaciones inversas también
                    if not any(rel_type == f"inv_{rt}" for rt in relation_types):
                        continue
                
                for target_id in targets:
                    if target_id not in visited:
                        visited.add(target_id)
                        
                        # Obtener info de la entidad si existe
                        entity_info = entity_lookup.get(target_id, {"id": target_id})
                        
                        related.append({
                            "id": target_id,
                            "name": entity_info.get("name", target_id),
                            "type": entity_info.get("type", "unknown"),
                            "domain": entity_info.get("domain", ""),
                            "relation_type": rel_type,
                            "relation_from": current_id,
                            "depth": depth + 1
                        })
                        
                        # Agregar a cola si no alcanzamos max_depth
                        if depth + 1 < max_depth:
                            queue.append((target_id, depth + 1))
        
        return related
    
    def add_document(self, file_path: str, domain: str = "general", 
                     metadata: Optional[Dict] = None) -> str:
        """
        Agrega un documento al indice RAG.
        
        Args:
            file_path: Ruta al archivo
            domain: Dominio/categoria del documento (para filtrado)
            metadata: Metadatos adicionales
        
        Returns:
            ID del documento
        """
        # Generar ID unico basado en contenido
        text = extract_text_from_file(file_path)
        doc_id = hashlib.md5(text.encode()).hexdigest()[:12]
        
        # Verificar si ya existe
        existing = self.conn.execute(
            "SELECT id FROM documents WHERE id = ?", [doc_id]
        ).fetchone()
        
        if existing:
            print(f"[RAG] Documento ya existe: {doc_id}")
            return doc_id
        
        # Insertar documento
        filename = Path(file_path).name
        self.conn.execute("""
            INSERT INTO documents (id, filename, domain, metadata)
            VALUES (?, ?, ?, ?)
        """, [doc_id, filename, domain, json.dumps(metadata or {})])
        
        # Chunking
        chunks = chunk_text(text)
        print(f"[RAG] Procesando {len(chunks)} chunks para {filename}...")
        
        # Generar embeddings en batch
        embeddings = generate_embeddings(chunks)
        
        # Insertar chunks
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc_id}_{i:04d}"
            self.conn.execute("""
                INSERT INTO chunks (id, doc_id, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, [chunk_id, doc_id, i, chunk, embedding])
        
        print(f"[RAG] Documento agregado: {filename} ({len(chunks)} chunks)")
        return doc_id
    
    def add_text(self, text: str, doc_name: str, domain: str = "general",
                 metadata: Optional[Dict] = None) -> str:
        """
        Agrega texto directamente (sin archivo).
        
        Args:
            text: Texto a indexar
            doc_name: Nombre identificador
            domain: Dominio/categoria
            metadata: Metadatos adicionales
        
        Returns:
            ID del documento
        """
        doc_id = hashlib.md5(text.encode()).hexdigest()[:12]
        
        # Verificar si ya existe
        existing = self.conn.execute(
            "SELECT id FROM documents WHERE id = ?", [doc_id]
        ).fetchone()
        
        if existing:
            return doc_id
        
        # Insertar documento
        self.conn.execute("""
            INSERT INTO documents (id, filename, domain, metadata)
            VALUES (?, ?, ?, ?)
        """, [doc_id, doc_name, domain, json.dumps(metadata or {})])
        
        # Chunking
        chunks = chunk_text(text)
        embeddings = generate_embeddings(chunks)
        
        # Insertar chunks (sin página para texto plano)
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc_id}_{i:04d}"
            self.conn.execute("""
                INSERT INTO chunks (id, doc_id, chunk_index, content, page, page_end, embedding)
                VALUES (?, ?, ?, ?, NULL, NULL, ?)
            """, [chunk_id, doc_id, i, chunk, embedding])
        
        return doc_id

    def add_pdf_with_pages(self, file_path: str, doc_name: str, domain: str = "general",
                          language: str = "en", metadata: Optional[Dict] = None) -> str:
        """
        Agrega un PDF preservando información de página para cada chunk.
        
        Args:
            file_path: Ruta al archivo PDF
            doc_name: Nombre identificador
            domain: Dominio/categoria
            language: Idioma del documento (en, es, fr, de, pt)
            metadata: Metadatos adicionales
        
        Returns:
            ID del documento
        """
        # Extraer páginas
        pages = extract_text_with_pages(file_path)
        all_text = "\n".join(p["text"] for p in pages)
        doc_id = hashlib.md5(all_text.encode()).hexdigest()[:12]
        
        # Verificar si ya existe
        existing = self.conn.execute(
            "SELECT id FROM documents WHERE id = ?", [doc_id]
        ).fetchone()
        
        if existing:
            return doc_id
        
        # Insertar documento con idioma
        self.conn.execute("""
            INSERT INTO documents (id, filename, domain, language, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, [doc_id, doc_name, domain, language, json.dumps(metadata or {})])
        
        # Chunking con páginas
        chunks_with_pages = chunk_text_with_pages(pages)
        chunk_texts = [c["text"] for c in chunks_with_pages]
        embeddings = generate_embeddings(chunk_texts)
        
        # Insertar chunks con información de página
        for i, (chunk_data, embedding) in enumerate(zip(chunks_with_pages, embeddings)):
            chunk_id = f"{doc_id}_{i:04d}"
            self.conn.execute("""
                INSERT INTO chunks (id, doc_id, chunk_index, content, page, page_end, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [chunk_id, doc_id, i, chunk_data["text"], chunk_data["page"], chunk_data["page_end"], embedding])
        
        return doc_id

    def get_available_languages(self) -> List[str]:
        """Retorna lista de idiomas únicos en el índice."""
        result = self.conn.execute(
            "SELECT DISTINCT language FROM documents WHERE language IS NOT NULL"
        ).fetchall()
        return [r[0] for r in result if r[0]]

    def translate_query_for_languages(self, query: str, target_languages: List[str]) -> str:
        """
        Expande la query con traducciones de términos técnicos.
        
        Idiomas soportados: en (inglés), es (español), pt (portugués), fr (francés)
        
        Args:
            query: Pregunta original
            target_languages: Lista de idiomas destino (ej: ['en', 'es', 'pt', 'fr'])
        
        Returns:
            Query expandida con términos en múltiples idiomas
        """
        # Diccionario multilingüe: término -> traducciones en otros idiomas
        # Formato: "término_en_cualquier_idioma": "EN ES PT FR"
        _translations = {
            # === Conceptos de regresión ===
            "heterocedasticidad": "heteroscedasticity hétéroscédasticité heterocedasticidade",
            "heteroscedasticity": "heterocedasticidad hétéroscédasticité heterocedasticidade",
            "hétéroscédasticité": "heteroscedasticity heterocedasticidad heterocedasticidade",
            "heterocedasticidade": "heteroscedasticity heterocedasticidad hétéroscédasticité",
            
            "homocedasticidad": "homoscedasticity homoscédasticité homocedasticidade",
            "homoscedasticity": "homocedasticidad homoscédasticité homocedasticidade",
            
            "multicolinealidad": "multicollinearity multicolinéarité multicolinearidade",
            "multicollinearity": "multicolinealidad multicolinéarité multicolinearidade",
            "multicolinéarité": "multicollinearity multicolinealidad multicolinearidade",
            
            "autocorrelación": "autocorrelation autocorrélation autocorrelação",
            "autocorrelation": "autocorrelación autocorrélation autocorrelação",
            "autocorrélation": "autocorrelation autocorrelación autocorrelação",
            
            "endogeneidad": "endogeneity endogénéité endogeneidade",
            "endogeneity": "endogeneidad endogénéité endogeneidade",
            
            "regresión": "regression régression regressão",
            "regression": "regresión régression regressão",
            "régression": "regression regresión regressão",
            "regressão": "regression regresión régression",
            
            "mínimos cuadrados": "least squares OLS moindres carrés mínimos quadrados MQO",
            "least squares": "mínimos cuadrados MCO moindres carrés mínimos quadrados",
            "moindres carrés": "least squares mínimos cuadrados mínimos quadrados",
            "mínimos quadrados": "least squares mínimos cuadrados moindres carrés",
            
            # === Series de tiempo ===
            "serie temporal": "time series série temporelle série temporal",
            "series temporales": "time series séries temporelles séries temporais",
            "time series": "serie temporal series temporales série temporelle série temporal",
            "série temporelle": "time series serie temporal série temporal",
            
            "estacionariedad": "stationarity stationnarité estacionariedade",
            "stationarity": "estacionariedad stationnarité estacionariedade",
            "stationnarité": "stationarity estacionariedad estacionariedade",
            
            "cointegración": "cointegration cointégration cointegração",
            "cointegration": "cointegración cointégration cointegração",
            "cointégration": "cointegration cointegración cointegração",
            
            "raíz unitaria": "unit root racine unitaire raiz unitária",
            "unit root": "raíz unitaria racine unitaire raiz unitária",
            "racine unitaire": "unit root raíz unitaria raiz unitária",
            
            # === Estadística / PCA ===
            "componentes principales": "principal component analysis PCA ACP analyse en composantes principales",
            "principal component": "componentes principales ACP analyse en composantes principales componentes principais",
            "analyse en composantes principales": "PCA principal component componentes principales ACP",
            "componentes principais": "principal component PCA componentes principales ACP",
            "ACP": "PCA principal component analysis componentes principales",
            "PCA": "ACP análisis de componentes principales analyse en composantes principales",
            
            "análisis factorial": "factor analysis analyse factorielle análise fatorial",
            "factor analysis": "análisis factorial analyse factorielle análise fatorial",
            "analyse factorielle": "factor analysis análisis factorial análise fatorial",
            
            "varianza": "variance variância",
            "variance": "varianza variância",
            "variância": "variance varianza",
            
            "covarianza": "covariance covariância",
            "covariance": "covarianza covariância",
            
            "correlación": "correlation corrélation correlação",
            "correlation": "correlación corrélation correlação",
            "corrélation": "correlation correlación correlação",
            
            "distribución": "distribution distribuição",
            "distribution": "distribución distribuição",
            
            "estimador": "estimator estimateur estimador",
            "estimator": "estimador estimateur",
            "estimateur": "estimator estimador",
            
            "sesgo": "bias biais viés",
            "bias": "sesgo biais viés",
            "biais": "bias sesgo viés",
            "viés": "bias sesgo biais",
            
            # === Panel data ===
            "datos de panel": "panel data données de panel dados em painel",
            "panel data": "datos de panel données de panel dados em painel",
            "données de panel": "panel data datos de panel dados em painel",
            "dados em painel": "panel data datos de panel données de panel",
            
            "efectos fijos": "fixed effects effets fixes efeitos fixos",
            "fixed effects": "efectos fijos effets fixes efeitos fixos",
            "effets fixes": "fixed effects efectos fijos efeitos fixos",
            
            "efectos aleatorios": "random effects effets aléatoires efeitos aleatórios",
            "random effects": "efectos aleatorios effets aléatoires efeitos aleatórios",
            
            # === Causalidad ===
            "inferencia causal": "causal inference inférence causale inferência causal",
            "causal inference": "inferencia causal inférence causale inferência causal",
            "inférence causale": "causal inference inferencia causal inferência causal",
            
            "variable instrumental": "instrumental variable IV variable instrumentale variável instrumental",
            "instrumental variable": "variable instrumental VI variable instrumentale variável instrumental",
            
            # === Excel ===
            "tabla dinámica": "pivot table tableau croisé dynamique tabela dinâmica",
            "pivot table": "tabla dinámica tableau croisé dynamique tabela dinâmica",
            "tableau croisé dynamique": "pivot table tabla dinámica tabela dinâmica",
            "tabela dinâmica": "pivot table tabla dinámica tableau croisé dynamique",
            
            "buscarv": "vlookup recherchev procv",
            "vlookup": "buscarv recherchev procv",
            "recherchev": "vlookup buscarv procv",
            "procv": "vlookup buscarv recherchev",
            
            "fórmula": "formula formule fórmula",
            "formula": "fórmula formule",
            "formule": "formula fórmula",
        }
        
        query_lower = query.lower()
        expansions = []
        
        for source_term, target_term in _translations.items():
            if source_term.lower() in query_lower:
                expansions.append(target_term)
        
        if expansions:
            return query + " " + " ".join(expansions)
        return query
    
    def query(self, question: str, domain: Optional[str] = None,
              top_k: int = 5, use_ontology: bool = True) -> List[Dict]:
        """
        Busca chunks relevantes para una pregunta.
        
        Args:
            question: Pregunta del usuario
            domain: Filtrar por dominio especifico
            top_k: Numero de resultados a retornar
            use_ontology: Si usar ontologia para expandir/filtrar busqueda
        
        Returns:
            Lista de diccionarios con chunks relevantes
        """
        # Generar embedding de la pregunta
        query_embedding = generate_embedding(question)
        
        # Construir query SQL con filtro de dominio opcional
        if domain:
            sql = """
                SELECT 
                    c.id,
                    c.content,
                    c.chunk_index,
                    c.page,
                    c.page_end,
                    d.filename,
                    d.domain,
                    array_cosine_distance(c.embedding, ?::FLOAT[384]) as distance
                FROM chunks c
                JOIN documents d ON c.doc_id = d.id
                WHERE d.domain = ?
                ORDER BY distance ASC
                LIMIT ?
            """
            results = self.conn.execute(sql, [query_embedding, domain, top_k]).fetchall()
        else:
            sql = """
                SELECT 
                    c.id,
                    c.content,
                    c.chunk_index,
                    c.page,
                    c.page_end,
                    d.filename,
                    d.domain,
                    array_cosine_distance(c.embedding, ?::FLOAT[384]) as distance
                FROM chunks c
                JOIN documents d ON c.doc_id = d.id
                ORDER BY distance ASC
                LIMIT ?
            """
            results = self.conn.execute(sql, [query_embedding, top_k]).fetchall()
        
        # Formatear resultados
        return [
            {
                "id": r[0],
                "content": r[1],
                "chunk_index": r[2],
                "page": r[3],
                "page_end": r[4],
                "filename": r[5],
                "domain": r[6],
                "score": 1 - r[7]  # Convertir distancia a similitud
            }
            for r in results
        ]
    
    def query_with_ontology(self, question: str, top_k: int = 5) -> Dict:
        """
        Busqueda guiada por ontologia.
        
        1. Analiza la pregunta para identificar dominios y entidades relevantes
        2. Usa ontologia para determinar filtros y enriquecer contexto
        3. Ejecuta busqueda vectorial filtrada
        
        Args:
            question: Pregunta del usuario
            top_k: Numero de resultados
        
        Returns:
            Dict con resultados, dominios detectados, y entidades relacionadas
        """
        question_lower = question.lower()
        detected_domains = set()
        matched_entities = []
        
        # Keywords por dominio (fallback si no hay entidades)
        domain_keywords = {
            "econometria": ["regresion", "ols", "mco", "econometria", "wooldridge", 
                          "greene", "variable", "estimador", "heterocedasticidad",
                          "panel", "instrumentos", "2sls", "iv", "arima", "var",
                          "serie temporal", "cointegration", "causalidad",
                          "pca", "acp", "principal component", "componentes principales"],
            "estadistica": ["media", "varianza", "probabilidad", "distribucion",
                          "hipotesis", "test", "intervalo", "confianza", "muestreo"],
            "machine_learning": ["clasificacion", "clustering", "neural", "red neuronal",
                               "deep learning", "svm", "random forest", "modelo predictivo"],
            "series_tiempo": ["arima", "var", "cointegracion", "estacionario",
                            "autocorrelacion", "serie temporal", "forecast", "garch"],
            "excel": ["excel", "celda", "formula", "hoja", "rango", "tabla dinamica",
                     "buscarv", "xlookup", "si", "sumar", "contar", "formato"],
            "r": ["rstudio", "tidyverse", "ggplot", "dplyr", "dataframe"],
            "python": ["pandas", "numpy", "matplotlib", "sklearn", "jupyter"],
            "julia": ["julia", "dataframes.jl", "plots.jl", "flux"]
        }
        
        # Mapeo de aliases de dominio para normalizar nombres en diferentes idiomas
        # Mapea dominios detectados a los nombres usados en la base de datos
        domain_aliases = {
            "econometrics": "econometria",
            "economics": "econometria",
            "statistics": "estadistica",
            "stats": "estadistica",
            "time_series": "series_tiempo",
            "timeseries": "series_tiempo",
            "ml": "machine_learning",
        }
        
        # Acrónimos conocidos en estadística/econometría/ML que son cortos pero significativos
        # Estos se buscan como match exacto aunque tengan <=3 caracteres
        known_acronyms = {
            # Curvas y métricas de clasificación
            "roc", "auc", "tpr", "fpr", "tnr", "fnr",
            # Modelos de series de tiempo
            "var", "vec", "ecm", "ar", "ma", "arma", "arch", "dcc",
            # Tests estadísticos
            "adf", "kpss", "bds", "lm", "lrt", "aic", "bic", "hqc",
            # Métodos de estimación
            "ols", "mco", "gls", "wls", "gmm", "iv", "2sls", "3sls", "sur",
            # Análisis multivariado
            "pca", "acp", "ica", "lda", "qda", "cca", "mds",
            # Machine Learning
            "svm", "knn", "ann", "mlp", "rnn", "cnn", "gan", "vae", "gbm", "xgb",
            # Otros
            "vif", "dw", "jb", "ks", "ad", "sw", "bp", "bg", "het", "hac", "nw",
        }
        
        # 1. Buscar coincidencias con entidades de la ontologia
        # Usamos scoring para priorizar matches más específicos
        if hasattr(self, 'ontology_entities') and self.ontology_entities:
            candidates = []  # Lista de (score, entity)
            seen_ids = set()  # Para deduplicar
            
            for entity in self.ontology_entities:
                entity_name = entity.get("name", "").lower()
                entity_id = entity.get("id", "").lower().replace("_", " ")
                entity_keywords = entity.get("keywords", [])
                
                # Skip si ya vimos este ID
                if entity["id"] in seen_ids:
                    continue
                
                score = 0
                
                # Extraer palabras significativas de la pregunta:
                # - Palabras largas (>3 chars)
                # - Acrónimos conocidos (aunque sean cortos)
                query_words = []
                for w in question_lower.split():
                    w_clean = w.strip(".,;:!?()[]{}\"'")
                    if len(w_clean) > 3:
                        query_words.append(w_clean)
                    elif w_clean in known_acronyms:
                        query_words.append(w_clean)
                
                # Match por acrónimo conocido (score alto, match exacto)
                for qw in query_words:
                    if qw in known_acronyms:
                        # Buscar match exacto del acrónimo en nombre, ID o keywords
                        if qw == entity_name or qw in entity_id.split():
                            score = 80  # Alta prioridad para acrónimos exactos
                            break
                        # Buscar en keywords
                        for kw in entity_keywords:
                            kw_lower = kw.lower() if isinstance(kw, str) else str(kw).lower()
                            if qw == kw_lower or qw in kw_lower.split():
                                score = 70
                                break
                        if score > 0:
                            break
                
                # Match por nombre completo (score alto, pero solo si nombre es significativo)
                if score == 0 and entity_name and len(entity_name) > 3 and entity_name in question_lower:
                    score = 100
                
                # Match por ID (score proporcional a palabras que coinciden)
                if score == 0 and entity_id and len(entity_id) > 3:
                    id_parts = entity_id.split()
                    # Solo contar partes de 3+ caracteres
                    matching_parts = [part for part in id_parts if len(part) > 2 and part in question_lower]
                    matches_in_question = len(matching_parts)
                    
                    # Permitir match con 1 palabra si es larga (>7 chars) y específica
                    if matches_in_question >= 2:
                        score = int((matches_in_question / len(id_parts)) * 50)
                    elif matches_in_question == 1 and len(matching_parts[0]) > 7:
                        # Una sola palabra larga es suficiente para match bajo
                        score = 20
                    elif matches_in_question == 1 and len(matching_parts[0]) > 4:
                        # Palabra mediana (5-7 chars) con baja prioridad
                        score = 15
                
                # Match por keywords (bidireccional: kw en query O query_word en kw)
                if score == 0:
                    for kw in entity_keywords:
                        if not kw or len(kw) <= 3:
                            continue
                        kw_lower = kw.lower() if isinstance(kw, str) else str(kw).lower()
                        
                        # Caso 1: keyword está contenido en la pregunta
                        if kw_lower in question_lower:
                            score = min(30, 10 + len(kw_lower))
                            break
                        
                        # Caso 2: alguna palabra de la pregunta está contenida en el keyword
                        # (ej: "hosmer" está en "hosmer-lemeshow")
                        for qw in query_words:
                            if qw in kw_lower:
                                # Score proporcional a cuánto del keyword cubre la palabra
                                coverage = len(qw) / len(kw_lower)
                                score = max(score, int(15 * coverage) + 10)
                        
                        if score > 0:
                            break
                
                if score > 0:
                    candidates.append((score, entity))
                    seen_ids.add(entity["id"])
            
            # Ordenar por score descendente y tomar los mejores
            candidates.sort(key=lambda x: -x[0])
            
            for score, entity in candidates[:10]:
                matched_entities.append({
                    "id": entity["id"],
                    "name": entity.get("name") or entity["id"].replace("_", " ").title(),
                    "type": entity.get("type", "unknown"),
                    "domain": entity.get("domain", "general"),
                    "match_score": score
                })
                if entity.get("domain"):
                    detected_domains.add(entity["domain"])
        
        # 1.5 Expandir contexto usando relaciones de la ontologia
        expanded_entities = []
        if matched_entities and hasattr(self, 'ontology_graph') and self.ontology_graph:
            # Tipos de relaciones útiles para expansión de contexto
            # Seleccionadas por frecuencia y utilidad semántica
            expansion_relations = [
                # Jerárquicas y taxonómicas
                "is_a", "part_of", "component_of", "subtype_of", "instance_of",
                # Uso y dependencia
                "uses", "uses_concept", "uses_method", "uses_function", "uses_estimator",
                "requires", "depends_on", "requires_assumption",
                # Implementación y aplicación
                "implements", "applies_to", "applied_to", "used_in", "used_for", "used_by",
                # Testing y evaluación
                "tests", "tests_for", "tested_by", "evaluated_by", "diagnostic_for",
                # Alternativas y variantes
                "alternative_to", "variant_of", "extension_of", "extends", "generalizes",
                # Propiedades y supuestos
                "assumption_of", "property_of", "has_property", "affected_by",
                # Relaciones generales (usar con cautela por volumen)
                "related_to", "similar_to",
            ]
            
            for entity in matched_entities[:5]:  # Limitar a top 5 para no explotar
                related = self.get_related_entities(
                    entity["id"], 
                    max_depth=1,
                    relation_types=expansion_relations
                )
                for rel in related[:10]:  # Máximo 10 relacionados por entidad
                    expanded_entities.append({
                        "id": rel["id"],
                        "name": rel["name"],
                        "type": rel["type"],
                        "domain": rel["domain"],
                        "via_relation": rel["relation_type"],
                        "via_entity": entity["name"]
                    })
                    # Agregar dominio de entidad relacionada
                    if rel["domain"]:
                        detected_domains.add(rel["domain"])
        
        # 2. Fallback a keywords estaticos si no se encontraron entidades
        if not detected_domains:
            for domain, keywords in domain_keywords.items():
                for kw in keywords:
                    if kw in question_lower:
                        detected_domains.add(domain)
                        break
        
        # 2.5. Normalizar dominios usando aliases (econometrics -> econometria, etc.)
        normalized_domains = set()
        for domain in detected_domains:
            normalized = domain_aliases.get(domain.lower(), domain)
            normalized_domains.add(normalized)
        detected_domains = list(normalized_domains)
        
        # 3. Ejecutar busqueda filtrada por dominios detectados
        if detected_domains:
            all_results = []
            for domain in detected_domains:
                results = self.query(question, domain=domain, top_k=top_k)
                all_results.extend(results)
            
            # Ordenar por score y tomar top_k
            all_results.sort(key=lambda x: x["score"], reverse=True)
            results = all_results[:top_k]
        else:
            # Busqueda general sin filtro
            results = self.query(question, top_k=top_k)
        
        # 4. Limitar entidades coincidentes para no saturar la respuesta
        matched_entities = matched_entities[:10]
        
        return {
            "question": question,
            "detected_domains": detected_domains,
            "ontology_guided": len(detected_domains) > 0 or len(matched_entities) > 0,
            "matched_entities": matched_entities,
            "expanded_entities": expanded_entities[:20],  # Entidades via relaciones
            "results": results
        }
    
    def list_documents(self) -> List[Dict]:
        """Lista todos los documentos indexados."""
        results = self.conn.execute("""
            SELECT d.id, d.filename, d.domain, d.created_at, 
                   COUNT(c.id) as chunk_count
            FROM documents d
            LEFT JOIN chunks c ON d.id = c.doc_id
            GROUP BY d.id, d.filename, d.domain, d.created_at
            ORDER BY d.created_at DESC
        """).fetchall()
        
        return [
            {
                "id": r[0],
                "filename": r[1],
                "domain": r[2],
                "created_at": str(r[3]),
                "chunk_count": r[4]
            }
            for r in results
        ]
    
    def delete_document(self, doc_id: str) -> bool:
        """Elimina un documento y sus chunks."""
        try:
            self.conn.execute("DELETE FROM chunks WHERE doc_id = ?", [doc_id])
            self.conn.execute("DELETE FROM documents WHERE id = ?", [doc_id])
            return True
        except Exception as e:
            print(f"[RAG] Error eliminando documento: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Obtiene estadisticas del indice."""
        doc_count = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        
        domains = self.conn.execute("""
            SELECT domain, COUNT(*) FROM documents GROUP BY domain
        """).fetchall()
        
        return {
            "documents": doc_count,
            "chunks": chunk_count,
            "domains": {d[0]: d[1] for d in domains}
        }
    
    def close(self):
        """Cierra la conexion a la base de datos."""
        self.conn.close()


# ---------------------------------------------------------------------------
# Singleton global para uso desde el servidor HTTP
# ---------------------------------------------------------------------------

_rag_instance: Optional[RAGEngine] = None

def reset_rag_engine():
    """Fuerza recreación del singleton en el próximo get_rag_engine()."""
    global _rag_instance
    if _rag_instance is not None:
        try:
            _rag_instance.close()
        except:
            pass
        _rag_instance = None

def get_rag_engine(db_path: str = None) -> RAGEngine:
    """
    Obtiene la instancia singleton del motor RAG.
    
    Args:
        db_path: Ruta a la base DuckDB. Si es None, usa memoria.
    
    Returns:
        Instancia de RAGEngine
    """
    global _rag_instance
    
    if _rag_instance is None:
        # Determinar ruta de la base de datos
        if db_path is None:
            # Usar directorio de NEVEN si existe
            neven_path = Path("C:/NEVEN/data")
            if neven_path.exists():
                db_path = str(neven_path / "rag_index.duckdb")
            else:
                db_path = ":memory:"
        
        # Determinar ruta de ontologia
        # Prioridad: directorio raíz que contiene todos los dominios
        ontology_path = None
        for candidate in [
            Path("C:/NEVEN/ontology"),               # Raíz de ontologías (carga todos los dominios)
            Path("C:/NEVEN/docs/ontologia"),         # YAMLs P1-P4
            Path(__file__).parent.parent / "docs" / "ontologia",
            Path("F:/ANTIGRAVITY/2026/NEVEN/src/docs/ontologia"),  # Repo (nueva ruta)
        ]:
            if candidate.exists():
                ontology_path = str(candidate)
                print(f"[RAG] Usando ontologia: {ontology_path}")
                break
        
        if ontology_path is None:
            print("[RAG] WARNING: No se encontró directorio de ontología")
        
        _rag_instance = RAGEngine(db_path=db_path, ontology_path=ontology_path)
        print(f"[RAG] Singleton creado: {len(_rag_instance.ontology_entities)} entidades")
    
    return _rag_instance


# ---------------------------------------------------------------------------
# CLI para testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    
    print("=== NEVEN RAG Engine Test ===")
    
    # Crear engine en memoria para test
    engine = RAGEngine()
    
    # Agregar texto de prueba
    test_text = """
    La regresion lineal es un metodo estadistico que permite modelar la relacion 
    entre una variable dependiente y una o mas variables independientes. El metodo 
    de minimos cuadrados ordinarios (MCO u OLS) es el mas comun para estimar los 
    parametros de una regresion lineal.
    
    Los supuestos clasicos del modelo de regresion lineal incluyen: linealidad, 
    exogeneidad estricta, homocedasticidad, no autocorrelacion, y normalidad de 
    los errores. Cuando estos supuestos se violan, los estimadores MCO pueden 
    perder sus propiedades deseables.
    
    La heterocedasticidad ocurre cuando la varianza de los errores no es constante. 
    Esto no sesga los coeficientes pero afecta los errores estandar. Los errores 
    robustos de White permiten hacer inferencia valida en presencia de heterocedasticidad.
    """
    
    doc_id = engine.add_text(test_text, "test_econometria.txt", domain="econometria")
    print(f"Documento agregado: {doc_id}")
    
    # Probar busqueda
    print("\n--- Busqueda: 'que es heterocedasticidad' ---")
    results = engine.query("que es heterocedasticidad", top_k=2)
    for r in results:
        print(f"  Score: {r['score']:.3f} | {r['content'][:100]}...")
    
    # Probar busqueda guiada por ontologia
    print("\n--- Busqueda con ontologia: 'como estimo una regresion' ---")
    results = engine.query_with_ontology("como estimo una regresion", top_k=2)
    print(f"  Dominios detectados: {results['detected_domains']}")
    print(f"  Guiada por ontologia: {results['ontology_guided']}")
    for r in results["results"]:
        print(f"  Score: {r['score']:.3f} | {r['content'][:100]}...")
    
    # Stats
    print("\n--- Estadisticas ---")
    stats = engine.get_stats()
    print(f"  Documentos: {stats['documents']}")
    print(f"  Chunks: {stats['chunks']}")
    print(f"  Dominios: {stats['domains']}")
    
    print("\n=== Test completado ===")
