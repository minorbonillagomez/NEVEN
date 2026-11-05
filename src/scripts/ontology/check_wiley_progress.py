#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:\NEVEN\startup")

from ontology_manager import get_book_progress

books = [
    ("VBA Numericos", r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS EXCEL\VBAExcel-MNumericos.pdf"),
    ("Wiley Scientists", r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS EXCEL\Wiley - Excel for scientists and engineers numerical methods.pdf"),
    ("Wiley Credit Risk", r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS EXCEL\Wiley - Credit Risk Modeling using Excel and VBA.pdf"),
    ("Wiley Advanced Finance", r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS EXCEL\Wiley - Advanced Modelling in Finance using Excel and VBA.pdf"),
]

print("\nEstado de procesamiento - Libros Wiley Excel")
print("=" * 60)
total_ents = 0
for name, book in books:
    p = get_book_progress(book, "excel")
    status = p.get("status", "?")
    pages = f"{p.get('pages_processed', 0)}/{p.get('total_pages', '?')}"
    ents = p.get("entities_created", 0)
    total_ents += ents
    icon = "✅" if status == "completed" else "⏳" if status == "in_progress" else "❌"
    print(f"{icon} {name}: {status} | {pages} pags | {ents} entidades")

print("=" * 60)
print(f"Total entidades nuevas: {total_ents}")
