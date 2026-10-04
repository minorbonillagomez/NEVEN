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


def extract_text_with_pages(file_path: str) -> List[Dict[str, Any]]:
    """
    Extrae texto de un PDF con información de página.
    
    Returns:
        Lista de dicts con {page: int, text: str}
    """
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
            if text.strip():  # Solo páginas con contenido
                pages.append({"page": i, "text": text})
        doc.close()
        return pages
    except ImportError:
        raise ImportError("PyMuPDF (fitz) no instalado. Ejecuta: pip install pymupdf")


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
    Extrae texto de un archivo (txt, md, pdf).
    
    Para PDF usa PyMuPDF si esta disponible, sino retorna error.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix in ['.txt', '.md', '.r', '.py', '.jl', '.json', '.yaml', '.yml']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    elif suffix == '.pdf':
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text
        except ImportError:
            raise ImportError("PyMuPDF (fitz) no instalado. Ejecuta: pip install pymupdf")
    
    else:
        raise ValueError(f"Formato no soportado: {suffix}")


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
                                props = entity.get("properties", {})
                                name = props.get("name", "")
                                desc = props.get("description", "")
                                
                                # Extraer keywords del nombre y descripcion
                                keywords = [w.lower() for w in name.split() if len(w) > 3]
                                
                                self.ontology_entities.append({
                                    "id": entity.get("id", ""),
                                    "type": entity.get("type", ""),
                                    "name": name,
                                    "description": desc,
                                    "domain": jsonl_file.parent.name,
                                    "keywords": keywords
                                })
            except Exception as e:
                print(f"[RAG] Error cargando {jsonl_file}: {e}")
        
        print(f"[RAG] Ontologia cargada: {len(self.ontology)} schemas, {len(self.ontology_entities)} entidades")
        
        # Actualizar hashes de archivos para detectar cambios futuros
        self._ontology_file_hashes = self._scan_ontology_files(ontology_path)
    
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
                          metadata: Optional[Dict] = None) -> str:
        """
        Agrega un PDF preservando información de página para cada chunk.
        
        Args:
            file_path: Ruta al archivo PDF
            doc_name: Nombre identificador
            domain: Dominio/categoria
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
        
        # Insertar documento
        self.conn.execute("""
            INSERT INTO documents (id, filename, domain, metadata)
            VALUES (?, ?, ?, ?)
        """, [doc_id, doc_name, domain, json.dumps(metadata or {})])
        
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
        
        return doc_id
    
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
                          "serie temporal", "cointegration", "causalidad"],
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
        
        # 1. Buscar coincidencias con entidades de la ontologia
        if hasattr(self, 'ontology_entities') and self.ontology_entities:
            for entity in self.ontology_entities:
                entity_name = entity.get("name", "").lower()
                entity_keywords = entity.get("keywords", [])
                
                # Verificar si alguna keyword de la entidad aparece en la pregunta
                if entity_name and entity_name in question_lower:
                    matched_entities.append({
                        "id": entity["id"],
                        "name": entity["name"],
                        "type": entity["type"],
                        "domain": entity["domain"]
                    })
                    detected_domains.add(entity["domain"])
                else:
                    for kw in entity_keywords:
                        if kw and len(kw) > 2 and kw in question_lower:
                            matched_entities.append({
                                "id": entity["id"],
                                "name": entity["name"],
                                "type": entity["type"],
                                "domain": entity["domain"]
                            })
                            detected_domains.add(entity["domain"])
                            break
        
        # 2. Fallback a keywords estaticos si no se encontraron entidades
        if not detected_domains:
            for domain, keywords in domain_keywords.items():
                for kw in keywords:
                    if kw in question_lower:
                        detected_domains.add(domain)
                        break
        
        detected_domains = list(detected_domains)
        
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
        ontology_path = None
        for candidate in [
            Path("C:/NEVEN/docs/ontologia"),
            Path(__file__).parent.parent / "docs" / "ontologia",
            Path("F:/ANTIGRAVITY/2026/NEVEN/NEVEN/docs/ontologia"),
        ]:
            if candidate.exists():
                ontology_path = str(candidate)
                break
        
        _rag_instance = RAGEngine(db_path=db_path, ontology_path=ontology_path)
    
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
