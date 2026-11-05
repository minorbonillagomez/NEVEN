#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:\NEVEN\startup")

from rag_engine import get_rag_engine

engine = get_rag_engine()

# Buscar conceptos de los libros Wiley
queries = [
    "Black-Scholes option pricing VBA",
    "Newton Raphson numerical method Excel",
    "credit risk default probability",
    "Monte Carlo simulation VBA",
]

for query in queries:
    print(f"\nQuery: {query}")
    print("=" * 60)
    
    results = engine.query(query, top_k=5, use_ontology=True)
    
    # Mostrar chunks encontrados
    chunks = results.get("chunks", [])[:3]
    for i, r in enumerate(chunks, 1):
        doc = r.get("doc_name", "?")[:45]
        score = r.get("score", 0)
        print(f"  {i}. {doc} (score: {score:.2f})")
    
    # Mostrar entidades matched
    matched = results.get("matched_entities", [])
    expanded = results.get("expanded_entities", [])
    print(f"\n  Matched: {len(matched)} | Expanded: {len(expanded)}")
    
    for e in matched[:3]:
        name = e.get("name", "?")
        etype = e.get("type", "?")
        score = e.get("score", 0)
        print(f"    - {name} ({etype}) score={score}")
