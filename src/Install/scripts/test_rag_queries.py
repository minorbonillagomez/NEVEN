#!/usr/bin/env python3
"""
Test del RAG con queries que deberían beneficiarse de las nuevas fuentes.
"""

import sys
sys.path.insert(0, r'C:\NEVEN\startup')

from rag_engine import get_rag_engine

def test_query(rag, query, test_name):
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"Query: {query}")
    print('='*70)
    
    result = rag.query_with_ontology(query)
    
    matched = result.get('matched_entities', [])
    expanded = result.get('expanded_entities', [])
    
    print(f"\nEntidades encontradas directamente: {len(matched)}")
    for ent in matched[:5]:
        source = ent.get('source', 'Original')
        name = ent.get('name', ent.get('id', 'unknown'))
        print(f"  - {name} [{source}]")
    
    print(f"\nEntidades expandidas via relaciones: {len(expanded)}")
    for ent in expanded[:5]:
        source = ent.get('source', 'Original')
        name = ent.get('name', ent.get('id', 'unknown'))
        print(f"  - {name} [{source}]")
    
    # Verificar si hay entidades de las nuevas fuentes
    sources_found = set()
    for ent in matched + expanded:
        src = ent.get('source', 'Original')
        sources_found.add(src)
    
    print(f"\nFuentes utilizadas: {', '.join(sources_found)}")
    return sources_found


def main():
    print("Inicializando RAG Engine...")
    rag = get_rag_engine()
    
    print(f"\nEstado del RAG:")
    print(f"  Entidades cargadas: {len(rag.ontology_entities)}")
    print(f"  Relaciones cargadas: {len(rag.ontology_relations)}")
    print(f"  Nodos en grafo: {len(rag.ontology_graph)}")
    
    all_sources = set()
    
    # Test 1: Tests no paramétricos (MathWorld)
    sources = test_query(
        rag,
        "Qué test no paramétrico uso para comparar dos muestras independientes?",
        "Tests no paramétricos (MathWorld)"
    )
    all_sources.update(sources)
    
    # Test 2: Maximum Likelihood (Statlect)
    sources = test_query(
        rag,
        "Cuáles son las propiedades del estimador de máxima verosimilitud?",
        "Maximum Likelihood (Statlect)"
    )
    all_sources.update(sources)
    
    # Test 3: Desigualdades probabilísticas (MathWorld)
    sources = test_query(
        rag,
        "Qué dice la desigualdad de Chebyshev?",
        "Desigualdades (MathWorld)"
    )
    all_sources.update(sources)
    
    # Test 4: Convergencia (Statlect)
    sources = test_query(
        rag,
        "Cuál es la diferencia entre convergencia en probabilidad y convergencia en distribución?",
        "Convergencia (Statlect)"
    )
    all_sources.update(sources)
    
    # Test 5: Bootstrap (MathWorld)
    sources = test_query(
        rag,
        "Cómo funciona el método bootstrap?",
        "Bootstrap (MathWorld)"
    )
    all_sources.update(sources)
    
    # Test 6: Correlación (MathWorld)
    sources = test_query(
        rag,
        "Qué diferencia hay entre correlación de Pearson y Spearman?",
        "Correlación (MathWorld)"
    )
    all_sources.update(sources)
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print('='*70)
    print(f"Fuentes utilizadas en total: {', '.join(all_sources)}")
    
    if 'MathWorld' in all_sources and 'Statlect' in all_sources:
        print("\n✅ RAG está usando las TRES fuentes de conocimiento")
    elif 'MathWorld' in all_sources or 'Statlect' in all_sources:
        print("\n⚠️ RAG está usando ALGUNAS de las nuevas fuentes")
    else:
        print("\n❌ RAG NO está usando las nuevas fuentes")


if __name__ == "__main__":
    main()
