#!/usr/bin/env python3
"""Test that forensic analysis benefits from Wiley book knowledge."""
import sys
sys.path.insert(0, r"C:\NEVEN\startup")

from ontology_manager import get_excel_function, search_knowledge

print("=" * 70)
print("TEST: ENRIQUECIMIENTO FORENSE CON LIBROS WILEY")
print("=" * 70)

# Test 1: Native Excel functions
print("\n1. FUNCIONES EXCEL NATIVAS")
print("-" * 50)
native_functions = ["VLOOKUP", "INDEX", "SUMIF", "NPV", "IRR", "PV", "PMT"]
for func in native_functions:
    info = get_excel_function(func)
    if info:
        book = info.get("source_book", "N/A")
        ftype = info.get("type", "?")
        print(f"  {func}: {ftype} | Libro: {book}")
    else:
        print(f"  {func}: NO ENCONTRADO")

# Test 2: VBA functions from Wiley books
print("\n2. FUNCIONES VBA DE LIBROS WILEY")
print("-" * 50)
vba_functions = ["BSd1", "BlackScholes", "NewtonRaphson", "MonteCarlo"]
for func in vba_functions:
    info = get_excel_function(func)
    if info:
        book = info.get("source_book", "N/A")
        ftype = info.get("type", "?")
        desc = info.get("description", "")[:60]
        print(f"  {func}: {ftype}")
        print(f"    Libro: {book}")
        print(f"    Desc: {desc}...")
    else:
        print(f"  {func}: NO ENCONTRADO")

# Test 3: Search for financial concepts
print("\n3. BUSQUEDA DE CONCEPTOS FINANCIEROS")
print("-" * 50)
concepts = ["Black-Scholes", "credit risk", "Newton Raphson", "Monte Carlo"]
for concept in concepts:
    results = search_knowledge(concept, domain="excel")
    print(f"  '{concept}': {len(results)} resultados")
    for r in results[:2]:
        print(f"    - {r['name']} ({r['type']})")

# Test 4: Verify entity types
print("\n4. TIPOS DE ENTIDADES EN ONTOLOGIA EXCEL")
print("-" * 50)
from ontology_manager import get_manager
manager = get_manager()
manager.ensure_loaded("excel")
entities = manager._entities.get("excel", {})

type_counts = {}
for e in entities.values():
    t = e.type
    type_counts[t] = type_counts.get(t, 0) + 1

for t, c in sorted(type_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {c:4d} - {t}")

print("\n" + "=" * 70)
print("TEST COMPLETADO")
print("=" * 70)
