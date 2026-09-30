"""Extract TOC and basic info from CFI Excel eBook."""
import fitz

doc = fitz.open(r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\CFI-Excel-eBook.pdf')
print(f'Pages: {len(doc)}')
print(f'Title: {doc.metadata.get("title", "N/A")}')
print(f'Author: {doc.metadata.get("author", "N/A")}')
print()

# Get TOC
toc = doc.get_toc()
print('Table of Contents:')
for level, title, page in toc[:50]:
    indent = '  ' * (level - 1)
    print(f'{indent}{title} (p.{page})')

if not toc:
    print('No TOC found. Extracting first pages text...')
    for i in range(min(5, len(doc))):
        page = doc[i]
        text = page.get_text()[:1000]
        print(f'\n--- Page {i+1} ---')
        print(text)
