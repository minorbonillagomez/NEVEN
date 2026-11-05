"""
NEVEN RAG - Indexación de libros de Álgebra Lineal
Agrega libros al índice existente SIN borrar la DB.
"""
import os
import sys
sys.path.insert(0, r"C:\NEVEN\startup")

from rag_engine import RAGEngine, extract_text_with_pages, chunk_text_with_pages

DB_PATH = r"C:\NEVEN\data\rag_index.duckdb"
ONTOLOGY_PATH = r"C:\NEVEN\ontology"

# Libros de Álgebra Lineal
BOOKS = [
    (r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\ALGEBRA\Introduction to Linear Algebra by Gilbert Strang (z-lib.org).pdf", 
     "algebra_lineal", "Introduction to Linear Algebra - Strang", "en"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\ALGEBRA\algebra lineal en excel.pdf", 
     "algebra_lineal", "Algebra Lineal en Excel", "es"),
]

if __name__ == "__main__":
    # NO borramos la DB - agregamos incrementalmente
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB no existe en {DB_PATH}")
        print("Ejecuta primero index_books.py para crear la DB base")
        sys.exit(1)
    
    print(f"Abriendo DB existente: {DB_PATH}")
    engine = RAGEngine(db_path=DB_PATH, ontology_path=ONTOLOGY_PATH)
    
    # Stats antes
    stats_before = engine.get_stats()
    print(f"Estado actual: {stats_before['documents']} docs, {stats_before['chunks']} chunks")
    print(f"Dominios: {stats_before['domains']}")
    print()
    
    for i, (path, domain, name, language) in enumerate(BOOKS, 1):
        print(f"[{i}/{len(BOOKS)}] {name} ({language})...", end=" ", flush=True)
        if not os.path.exists(path):
            print("NOT FOUND")
            continue
        try:
            doc_id = engine.add_pdf_with_pages(path, name, domain=domain, language=language)
            pages = extract_text_with_pages(path)
            chunks = chunk_text_with_pages(pages)
            print(f"OK ({len(chunks)} chunks, {len(pages)} paginas)")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Stats después
    stats_after = engine.get_stats()
    print(f"\n=== Resultado ===")
    print(f"Antes:   {stats_before['chunks']} chunks")
    print(f"Despues: {stats_after['chunks']} chunks")
    print(f"Agregados: {stats_after['chunks'] - stats_before['chunks']} chunks")
    print(f"Dominios: {stats_after['domains']}")
    print(f"Archivo: {DB_PATH} ({os.path.getsize(DB_PATH)/1024/1024:.1f} MB)")
    engine.close()
