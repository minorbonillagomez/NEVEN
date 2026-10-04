"""
NEVEN RAG - Script de indexación masiva de libros con información de página
"""
import os
import sys
sys.path.insert(0, r"C:\NEVEN\TaskPane")

from rag_engine import RAGEngine, extract_text_with_pages, chunk_text_with_pages

DB_PATH = r"C:\NEVEN\data\rag_index.duckdb"
ONTOLOGY_PATH = r"C:\NEVEN\docs\ontologia"

# Formato: (ruta, dominio, nombre, idioma)
# Idiomas soportados: en, es, fr, de, pt
BOOKS = [
    (r"F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS ECONOMETRIA\wooldridge_j-_2002_econometric_analysis_of_cross_section_and_panel_data.pdf", "econometria", "Wooldridge - Panel Data", "en"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS ECONOMETRIA\Time-Series-Analysis-with-Applications-in-R-Second-Edition.pdf", "econometria", "Time Series Analysis in R", "en"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS ECONOMETRIA\Fundamentals of causal inference using R.pdf", "econometria", "Causal Inference in R", "en"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS ECONOMETRIA\100 Statistical Tests In R by N.D. Lewis.pdf", "estadistica", "100 Statistical Tests in R", "en"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS ECONOMETRIA\An Introduction to Spatial Data Analysis in R.pdf", "econometria", "Spatial Data Analysis in R", "en"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS ECONOMETRIA\A-Portable-Workbook-for-Data-Analysis-R-for-the-Social-Sciences-1766019185.pdf", "estadistica", "R for Social Sciences", "en"),
    (r"C:\Users\Minor Bonilla G\Downloads\CFI-Excel-eBook.pdf", "excel", "CFI Excel eBook", "en"),
    (r"C:\Users\Minor Bonilla G\Downloads\dokumen.pub_microsoft-excel-365-bible-1nbsped-1119835100-9781119835103.pdf", "excel", "Excel 365 Bible", "en"),
    (r"C:\Users\Minor Bonilla G\Downloads\Excel tutorial - Excel basics.pdf", "excel", "Excel Basics Tutorial", "en"),
]

if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    engine = RAGEngine(db_path=DB_PATH, ontology_path=ONTOLOGY_PATH)
    
    for i, (path, domain, name, language) in enumerate(BOOKS, 1):
        print(f"[{i}/{len(BOOKS)}] {name} ({language})...", end=" ", flush=True)
        if not os.path.exists(path):
            print("NOT FOUND")
            continue
        try:
            # Usar el nuevo método que preserva páginas e idioma
            doc_id = engine.add_pdf_with_pages(path, name, domain=domain, language=language)
            # Contar chunks para el log
            pages = extract_text_with_pages(path)
            chunks = chunk_text_with_pages(pages)
            print(f"OK ({len(chunks)} chunks, {len(pages)} paginas)")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    stats = engine.get_stats()
    print(f"\nTotal: {stats['documents']} docs, {stats['chunks']} chunks")
    print(f"Dominios: {stats['domains']}")
    print(f"Archivo: {DB_PATH} ({os.path.getsize(DB_PATH)/1024/1024:.1f} MB)")
    engine.close()
