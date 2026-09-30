"""Analyze Excel 365 Bible TOC in detail."""
import fitz

doc = fitz.open(r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\dokumen.pub_microsoft-excel-365-bible-1nbsped-1119835100-9781119835103.pdf')
print(f"Pages: {len(doc)}")
print(f"Title: {doc.metadata.get('title', 'N/A')}")
print(f"Author: {doc.metadata.get('author', 'N/A')}")

toc = doc.get_toc()
print(f"\nTotal TOC entries: {len(toc)}")
print("\nFull Table of Contents:")
for level, title, page in toc[:100]:
    indent = '  ' * (level - 1)
    print(f"{indent}{title} (p.{page})")
