"""Analyze new PDF books in LIBROS EXCEL folder."""
import fitz
import os

books = [
    r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\Curso-Practico-Paso-a-Paso-de-Cero-a-Avanzado.pdf',
    r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\dokumen.pub_microsoft-excel-365-bible-1nbsped-1119835100-9781119835103.pdf',
]

for book_path in books:
    print("=" * 70)
    print(f"BOOK: {os.path.basename(book_path)}")
    print("=" * 70)
    
    try:
        doc = fitz.open(book_path)
        print(f"Pages: {len(doc)}")
        print(f"Title: {doc.metadata.get('title', 'N/A')}")
        print(f"Author: {doc.metadata.get('author', 'N/A')}")
        
        # Get TOC
        toc = doc.get_toc()
        if toc:
            print("\nTable of Contents (first 30 entries):")
            for level, title, page in toc[:30]:
                indent = '  ' * (level - 1)
                print(f"{indent}{title} (p.{page})")
        else:
            print("\nNo TOC found. Extracting first pages...")
            for i in range(min(5, len(doc))):
                page = doc[i]
                text = page.get_text()[:800]
                print(f"\n--- Page {i+1} ---")
                print(text)
        
        doc.close()
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n")
