#!/usr/bin/env python3
"""Normalize book names in graph.jsonl to eliminate duplicates."""
import json
import os
import shutil
from datetime import datetime

GRAPH_FILE = r"C:\NEVEN\ontology\excel\graph.jsonl"
BACKUP_FILE = GRAPH_FILE + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Canonical book names mapping
# Format: variations -> canonical name
BOOK_MAPPINGS = {
    # VBA Metodos Numericos
    "VBAExcel-MNumericos.pdf": "VBA Excel Metodos Numericos",
    "VBAExcel-MNumericos": "VBA Excel Metodos Numericos",
    "VBA para Excel": "VBA Excel Metodos Numericos",
    
    # Wiley Excel for Scientists
    "Wiley - Excel for scientists and engineers numerical methods.pdf": "Excel for Scientists and Engineers (Wiley)",
    "Wiley - Excel for scientists and engineers numerical methods": "Excel for Scientists and Engineers (Wiley)",
    "Excel for scientists and engineers numerical methods.pdf": "Excel for Scientists and Engineers (Wiley)",
    "Excel for scientists and engineers numerical methods": "Excel for Scientists and Engineers (Wiley)",
    "Excel for Scientists and Engineers Numerical Methods": "Excel for Scientists and Engineers (Wiley)",
    "Excel for Scientists and Engineers: Numerical Methods": "Excel for Scientists and Engineers (Wiley)",
    "Excel for Scientists and Engineers": "Excel for Scientists and Engineers (Wiley)",
    
    # Wiley Credit Risk
    "Wiley - Credit Risk Modeling using Excel and VBA.pdf": "Credit Risk Modeling (Wiley)",
    "Wiley - Credit Risk Modeling using Excel and VBA": "Credit Risk Modeling (Wiley)",
    "Credit Risk Modeling using Excel and VBA": "Credit Risk Modeling (Wiley)",
    
    # Wiley Advanced Finance
    "Wiley - Advanced Modelling in Finance using Excel and VBA.pdf": "Advanced Modelling in Finance (Wiley)",
    "Wiley - Advanced Modelling in Finance using Excel and VBA": "Advanced Modelling in Finance (Wiley)",
    "Advanced Modelling in Finance using Excel and VBA": "Advanced Modelling in Finance (Wiley)",
    "Advanced Modelling in Finance": "Advanced Modelling in Finance (Wiley)",
}

def normalize_book_name(name):
    """Normalize a book name using the mapping."""
    if not name:
        return name
    # Direct lookup
    if name in BOOK_MAPPINGS:
        return BOOK_MAPPINGS[name]
    # Case-insensitive lookup
    name_lower = name.lower()
    for variant, canonical in BOOK_MAPPINGS.items():
        if variant.lower() == name_lower:
            return canonical
    return name

def main():
    print("=" * 70)
    print("NORMALIZING BOOK NAMES IN GRAPH.JSONL")
    print("=" * 70)
    
    # Backup original file
    print(f"\n1. Creating backup: {BACKUP_FILE}")
    shutil.copy2(GRAPH_FILE, BACKUP_FILE)
    
    # Read and process
    print("\n2. Processing entries...")
    updated_lines = []
    stats = {
        "total": 0,
        "entities": 0,
        "normalized_source_book": 0,
        "normalized_reference_book": 0,
        "unchanged": 0
    }
    
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            stats["total"] += 1
            line = line.strip()
            if not line:
                updated_lines.append(line)
                continue
            
            try:
                entry = json.loads(line)
                modified = False
                
                if entry.get("op") == "create":
                    stats["entities"] += 1
                    entity = entry.get("entity", {})
                    props = entity.get("properties", {})
                    
                    # Normalize source_book
                    if "source_book" in props:
                        old_name = props["source_book"]
                        new_name = normalize_book_name(old_name)
                        if new_name != old_name:
                            props["source_book"] = new_name
                            modified = True
                            stats["normalized_source_book"] += 1
                    
                    # Normalize reference.book
                    ref = props.get("reference", {})
                    if isinstance(ref, dict) and "book" in ref:
                        old_name = ref["book"]
                        new_name = normalize_book_name(old_name)
                        if new_name != old_name:
                            ref["book"] = new_name
                            modified = True
                            stats["normalized_reference_book"] += 1
                
                if modified:
                    updated_lines.append(json.dumps(entry, ensure_ascii=False))
                else:
                    updated_lines.append(line)
                    if entry.get("op") == "create":
                        stats["unchanged"] += 1
                        
            except json.JSONDecodeError:
                updated_lines.append(line)
    
    # Write updated file
    print("\n3. Writing updated file...")
    with open(GRAPH_FILE, 'w', encoding='utf-8') as f:
        for line in updated_lines:
            f.write(line + '\n')
    
    # Print stats
    print("\n4. Statistics:")
    print(f"   Total lines: {stats['total']}")
    print(f"   Entity entries: {stats['entities']}")
    print(f"   Normalized source_book: {stats['normalized_source_book']}")
    print(f"   Normalized reference.book: {stats['normalized_reference_book']}")
    print(f"   Unchanged entities: {stats['unchanged']}")
    
    print("\n5. Verifying results...")
    # Re-count books
    books = {}
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("op") == "create":
                    props = entry.get("entity", {}).get("properties", {})
                    source = props.get("source_book")
                    if not source:
                        ref = props.get("reference", {})
                        source = ref.get("book") if isinstance(ref, dict) else None
                    if source:
                        books[source] = books.get(source, 0) + 1
            except:
                pass
    
    print(f"\n   Books after normalization: {len(books)}")
    print("\n   Counts:")
    for book, count in sorted(books.items(), key=lambda x: -x[1]):
        print(f"     {count:4d} - {book}")
    
    print("\n" + "=" * 70)
    print("NORMALIZATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
