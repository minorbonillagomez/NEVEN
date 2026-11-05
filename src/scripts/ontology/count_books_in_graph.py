#!/usr/bin/env python3
"""Count entities per book in graph.jsonl."""
import json
from collections import defaultdict

graph_file = r"C:\NEVEN\ontology\excel\graph.jsonl"
books = defaultdict(int)
no_book = 0

with open(graph_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            if entry.get("op") == "create":
                entity = entry.get("entity", {})
                props = entity.get("properties", {})
                
                # Try source_book first
                source = props.get("source_book")
                
                # Try reference.book
                if not source:
                    ref = props.get("reference", {})
                    if isinstance(ref, dict):
                        source = ref.get("book")
                
                if source:
                    books[source] += 1
                else:
                    no_book += 1
        except:
            pass

print("=" * 70)
print("ENTIDADES POR LIBRO EN GRAPH.JSONL")
print("=" * 70)

print(f"\nLibros encontrados: {len(books)}")
print(f"Entidades con libro: {sum(books.values())}")
print(f"Entidades sin libro: {no_book}")

print("\n--- Por libro (ordenado por cantidad) ---")
for book, count in sorted(books.items(), key=lambda x: -x[1])[:20]:
    print(f"  {count:4d} - {book[:60]}")

if len(books) > 20:
    print(f"  ... y {len(books) - 20} libros mas")
