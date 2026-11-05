"""
NEVEN RAG - Script de indexación de libros Markdown (post-procesados con LaTeX)
===============================================================================
Indexa los archivos .md de markdown_latex/ que ya tienen Unicode convertido a LaTeX.

Uso:
    python index_markdown_books.py [--append]
    
    Sin --append: elimina el índice existente y crea uno nuevo
    Con --append: agrega a un índice existente
"""
import os
import sys
import hashlib
import argparse
from pathlib import Path

# Agregar path de NEVEN
sys.path.insert(0, r"C:\NEVEN\startup")
from rag_engine import RAGEngine, chunk_text, generate_embeddings

# Configuración
DB_PATH = r"C:\NEVEN\data\rag_index.duckdb"
ONTOLOGY_PATH = r"C:\NEVEN\docs\ontologia"
MARKDOWN_DIR = Path(r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS ECONOMETRIA\markdown_latex")

# Mapeo de archivos a metadatos (dominio, nombre amigable, idioma)
BOOK_METADATA = {
    "100 Statistical Tests In R by N.D. Lewis.md": 
        ("estadistica", "100 Statistical Tests in R", "en"),
    "A-Portable-Workbook-for-Data-Analysis-R-for-the-Social-Sciences-1766019185.md": 
        ("estadistica", "R for Social Sciences", "en"),
    "AER.md": 
        ("econometria", "Applied Econometrics with R", "en"),
    "An Introduction to Spatial Data Analysis in R.md": 
        ("econometria", "Spatial Data Analysis in R", "en"),
    "An Introduction to Statistical Learning with R.md": 
        ("estadistica", "Introduction to Statistical Learning", "en"),
    "Fundamentals of causal inference using R.md": 
        ("econometria", "Causal Inference in R", "en"),
    "ITER.md": 
        ("econometria", "Introduction to Econometrics with R", "en"),
    "MIT_14.382_Econometrics.md": 
        ("econometria", "MIT Econometrics 14.382", "en"),
    "MIT_14.384_Time_Series_Analysis.md": 
        ("econometria", "MIT Time Series Analysis 14.384", "en"),
    "Time-Series-Analysis-with-Applications-in-R-Second-Edition.md": 
        ("econometria", "Time Series Analysis with R", "en"),
    "wooldridge_j-_2002_econometric_analysis_of_cross_section_and_panel_data.md": 
        ("econometria", "Wooldridge - Panel Data", "en"),
}


def add_markdown_document(engine: RAGEngine, file_path: Path, domain: str, 
                          name: str, language: str) -> str:
    """
    Agrega un documento Markdown al índice RAG.
    
    Args:
        engine: Instancia de RAGEngine
        file_path: Ruta al archivo .md
        domain: Dominio (econometria, estadistica, etc.)
        name: Nombre amigable del documento
        language: Idioma (en, es, etc.)
    
    Returns:
        ID del documento
    """
    # Leer contenido
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Generar ID basado en contenido
    doc_id = hashlib.md5(text.encode()).hexdigest()[:12]
    
    # Verificar si ya existe
    existing = engine.conn.execute(
        "SELECT id FROM documents WHERE id = ?", [doc_id]
    ).fetchone()
    
    if existing:
        print(f"Ya existe: {name}")
        return doc_id
    
    # Insertar documento con metadata
    import json
    metadata = {
        "source": str(file_path),
        "language": language,
        "format": "markdown_latex",
        "name": name
    }
    
    engine.conn.execute("""
        INSERT INTO documents (id, filename, domain, metadata)
        VALUES (?, ?, ?, ?)
    """, [doc_id, file_path.name, domain, json.dumps(metadata)])
    
    # Chunking
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    
    # Generar embeddings en batches de 100 para evitar memory issues
    BATCH_SIZE = 100
    total_chunks = len(chunks)
    
    for batch_start in range(0, total_chunks, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_chunks)
        batch_chunks = chunks[batch_start:batch_end]
        
        # Generar embeddings para este batch
        embeddings = generate_embeddings(batch_chunks)
        
        # Insertar chunks
        for i, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
            chunk_idx = batch_start + i
            chunk_id = f"{doc_id}_{chunk_idx:04d}"
            engine.conn.execute("""
                INSERT INTO chunks (id, doc_id, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, [chunk_id, doc_id, chunk_idx, chunk, embedding])
        
        # Mostrar progreso para documentos grandes
        if total_chunks > 200:
            print(f"  [{batch_end}/{total_chunks}]", end="", flush=True)
    
    if total_chunks > 200:
        print(" ", end="")  # Nueva línea después del progreso
    
    return doc_id


def main():
    parser = argparse.ArgumentParser(description='Indexar libros Markdown en RAG')
    parser.add_argument('--append', action='store_true', 
                       help='Agregar a índice existente (no eliminar)')
    args = parser.parse_args()
    
    # Preparar directorio
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Si no es append, eliminar índice existente
    if not args.append and os.path.exists(DB_PATH):
        print(f"Eliminando índice existente: {DB_PATH}")
        os.remove(DB_PATH)
    
    # Crear engine
    print(f"Inicializando RAG engine...")
    engine = RAGEngine(db_path=DB_PATH, ontology_path=ONTOLOGY_PATH)
    
    # Procesar cada archivo
    md_files = sorted(MARKDOWN_DIR.glob("*.md"))
    total_chunks = 0
    
    for i, md_file in enumerate(md_files, 1):
        filename = md_file.name
        
        if filename in BOOK_METADATA:
            domain, name, language = BOOK_METADATA[filename]
        else:
            domain = "general"
            name = filename.replace(".md", "")
            language = "en"
        
        print(f"[{i}/{len(md_files)}] {name}...", end=" ", flush=True)
        
        try:
            # Leer para contar chunks
            with open(md_file, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks = chunk_text(text)
            
            # Indexar
            doc_id = add_markdown_document(engine, md_file, domain, name, language)
            total_chunks += len(chunks)
            print(f"OK ({len(chunks)} chunks)")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Estadísticas
    stats = engine.get_stats()
    print(f"\n{'=' * 60}")
    print(f"RESUMEN:")
    print(f"{'=' * 60}")
    print(f"Documentos: {stats['documents']}")
    print(f"Chunks: {stats['chunks']}")
    print(f"Dominios: {stats['domains']}")
    print(f"Archivo: {DB_PATH}")
    if os.path.exists(DB_PATH):
        size_mb = os.path.getsize(DB_PATH) / 1024 / 1024
        print(f"Tamaño: {size_mb:.1f} MB")
    
    engine.close()
    print("\nIndexación completada.")


if __name__ == '__main__':
    main()
