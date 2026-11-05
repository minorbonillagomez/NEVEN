#!/usr/bin/env python3
"""Verificar integracion completa de libros Wiley en ontologia."""
import sys
import json
sys.path.insert(0, r"C:\NEVEN\startup")

from ontology_manager import list_processed_books, get_manager

print("=" * 70)
print("VERIFICACION INTEGRACION LIBROS WILEY")
print("=" * 70)

# 1. Lista de libros procesados
print("\n1. LIBROS PROCESADOS (via list_processed_books)")
print("-" * 50)
books = list_processed_books(domain_id="excel")
wiley_books = [b for b in books if "wiley" in b["book_name"].lower() or "vba" in b["book_name"].lower()]

for b in wiley_books:
    print(f"  {b['book_name']}")
    print(f"    Entidades: {b['entity_count']} | Paginas: {b.get('pages', '?')}")

print(f"\nTotal libros Wiley/VBA: {len(wiley_books)}")

# 2. Verificar entidades en memoria
print("\n2. ENTIDADES EN MEMORIA (via get_manager)")
print("-" * 50)
manager = get_manager()
manager.ensure_loaded("excel")
entities = manager._entities.get("excel", {})

# Contar por libro fuente
books_count = {}
for eid, entity in entities.items():
    source = entity.properties.get("source_book")
    if not source:
        ref = entity.properties.get("reference", {})
        source = ref.get("book") if isinstance(ref, dict) else None
    if source:
        books_count[source] = books_count.get(source, 0) + 1

# Filtrar Wiley/VBA
wiley_sources = {k: v for k, v in books_count.items() 
                 if "wiley" in k.lower() or "vba" in k.lower() or "credit" in k.lower() or "advanced" in k.lower()}

for source, count in sorted(wiley_sources.items(), key=lambda x: -x[1]):
    print(f"  {source}: {count} entidades")

print(f"\nTotal entidades Wiley/VBA: {sum(wiley_sources.values())}")

# 3. Verificar relaciones
print("\n3. RELACIONES DE ENTIDADES WILEY")
print("-" * 50)
relations = manager._relations.get("excel", [])
wiley_entity_ids = set()

for eid, entity in entities.items():
    source = entity.properties.get("source_book")
    if not source:
        ref = entity.properties.get("reference", {})
        source = ref.get("book") if isinstance(ref, dict) else None
    if source and ("wiley" in source.lower() or "vba" in source.lower() or "credit" in source.lower()):
        wiley_entity_ids.add(eid)

# Contar relaciones que involucran entidades Wiley
wiley_relations = 0
for rel in relations:
    if rel.from_id in wiley_entity_ids or rel.to_id in wiley_entity_ids:
        wiley_relations += 1

print(f"Entidades Wiley: {len(wiley_entity_ids)}")
print(f"Relaciones que involucran Wiley: {wiley_relations}")

# 4. Mostrar ejemplos de entidades
print("\n4. EJEMPLOS DE ENTIDADES WILEY")
print("-" * 50)
sample_ids = list(wiley_entity_ids)[:5]
for eid in sample_ids:
    entity = entities.get(eid)
    if entity:
        print(f"  ID: {eid}")
        print(f"    Nombre: {entity.properties.get('name', '?')}")
        print(f"    Tipo: {entity.type}")
        ref = entity.properties.get("reference", {})
        if ref:
            print(f"    Libro: {ref.get('book', '?')}")
        print()

print("=" * 70)
print("VERIFICACION COMPLETADA")
print("=" * 70)
