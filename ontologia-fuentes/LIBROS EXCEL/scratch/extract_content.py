"""Extract detailed content from CFI Excel eBook for ontology."""
import fitz
import json

doc = fitz.open(r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\CFI-Excel-eBook.pdf')

# Extract text from key sections
sections = {
    "shortcuts": (6, 13),
    "basic_formulas": (14, 27),
    "advanced_formulas": (28, 38),
    "date_time": (40, 59),
    "financial": (60, 87),
    "logical": (94, 127),
    "lookup": (128, 156),
    "statistical": (166, 205),
}

for section_name, (start, end) in sections.items():
    print(f"\n{'='*60}")
    print(f"SECTION: {section_name.upper()} (pages {start}-{end})")
    print('='*60)
    
    text = ""
    for page_num in range(start-1, min(end, len(doc))):
        page = doc[page_num]
        text += page.get_text() + "\n"
    
    # Print first 2000 chars of each section
    print(text[:2500])
    print(f"\n[... {len(text)} total chars in section ...]")
