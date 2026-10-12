"""
NEVEN Ontology Enricher - Post-procesador para agregar relaciones faltantes

Este script analiza entidades huerfanas y genera relaciones basadas en:
1. Similitud de nombres (fuzzy matching)
2. Co-ocurrencia en el mismo libro/capitulo
3. Tipos de entidades compatibles
"""

import os
import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict


def load_graph(domain: str = "econometria") -> Tuple[Dict, List]:
    """Load nodes and edges from graph.jsonl"""
    graph_path = os.path.join(r"C:\NEVEN\ontology", domain, "graph.jsonl")
    
    nodes = {}  # id -> node
    edges = []  # list of (from, to, type)
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                op = entry.get("op")
                
                if op == "create":
                    entity = entry.get("entity", {})
                    entity_id = entity.get("id", "")
                    if entity_id:
                        nodes[entity_id] = entity
                
                elif op == "relate":
                    relation = entry.get("relation", {})
                    from_id = relation.get("from", "")
                    to_id = relation.get("to", "")
                    rel_type = relation.get("type", "related_to")
                    if from_id and to_id:
                        edges.append((from_id, to_id, rel_type))
            except json.JSONDecodeError:
                continue
    
    return nodes, edges


def find_orphans(nodes: Dict, edges: List) -> Set[str]:
    """Find nodes without any connections"""
    connected = set()
    for from_id, to_id, _ in edges:
        connected.add(from_id)
        connected.add(to_id)
    
    orphans = set(nodes.keys()) - connected
    return orphans


def get_type_from_id(node_id: str) -> str:
    """Extract entity type from ID prefix"""
    prefixes = {
        "concept_": "Concept",
        "model_": "Model",
        "test_": "Test",
        "estimator_": "Estimator",
        "tech_": "Technique",
        "func_": "Function",
        "pkg_": "Package",
        "pattern_": "Pattern",
        "bp_": "BestPractice",
        "assumption_": "Assumption",
    }
    for prefix, entity_type in prefixes.items():
        if node_id.startswith(prefix):
            return entity_type
    return "Unknown"


def suggest_relations(orphan_id: str, nodes: Dict, existing_edges: Set) -> List[Tuple[str, str, str]]:
    """Suggest relations for an orphan node based on heuristics"""
    suggestions = []
    
    orphan = nodes.get(orphan_id, {})
    orphan_type = get_type_from_id(orphan_id)
    orphan_name = orphan.get("properties", {}).get("name", "").lower()
    orphan_desc = orphan.get("properties", {}).get("description", "").lower()
    
    # Words in orphan's name/description
    orphan_words = set((orphan_name + " " + orphan_desc).split())
    orphan_words = {w for w in orphan_words if len(w) > 3}  # Filter short words
    
    # Type-based relation suggestions
    type_relations = {
        ("Test", "Concept"): "tests",
        ("Test", "Assumption"): "tests",
        ("Model", "Estimator"): "uses",
        ("Model", "Assumption"): "requires",
        ("Estimator", "Model"): "used_by",
        ("Technique", "Model"): "used_by",
        ("Function", "Package"): "part_of",
    }
    
    for other_id, other_node in nodes.items():
        if other_id == orphan_id:
            continue
        
        # Skip if relation already exists
        if (orphan_id, other_id) in existing_edges or (other_id, orphan_id) in existing_edges:
            continue
        
        other_type = get_type_from_id(other_id)
        other_name = other_node.get("properties", {}).get("name", "").lower()
        other_desc = other_node.get("properties", {}).get("description", "").lower()
        other_words = set((other_name + " " + other_desc).split())
        other_words = {w for w in other_words if len(w) > 3}
        
        # Check word overlap
        overlap = orphan_words & other_words
        if len(overlap) >= 2:
            # Determine relation type
            rel_type = type_relations.get((orphan_type, other_type), "related_to")
            suggestions.append((orphan_id, other_id, rel_type))
            
            # Limit suggestions per orphan
            if len(suggestions) >= 3:
                break
    
    return suggestions


def enrich_ontology(domain: str = "econometria", dry_run: bool = True) -> Dict:
    """Main enrichment function"""
    print(f"[Enricher] Loading graph for domain: {domain}")
    nodes, edges = load_graph(domain)
    
    print(f"[Enricher] Nodes: {len(nodes)}, Edges: {len(edges)}")
    
    # Find orphans
    orphans = find_orphans(nodes, edges)
    print(f"[Enricher] Orphan nodes: {len(orphans)} ({len(orphans)/len(nodes)*100:.1f}%)")
    
    if len(orphans) == 0:
        return {"status": "ok", "message": "No orphans found", "new_relations": 0}
    
    # Build existing edges set for quick lookup
    existing_edges = set()
    for from_id, to_id, _ in edges:
        existing_edges.add((from_id, to_id))
        existing_edges.add((to_id, from_id))
    
    # Generate suggestions
    new_relations = []
    for orphan_id in list(orphans)[:500]:  # Limit to 500 orphans per run
        suggestions = suggest_relations(orphan_id, nodes, existing_edges)
        for from_id, to_id, rel_type in suggestions:
            new_relations.append({
                "op": "relate",
                "relation": {
                    "type": rel_type,
                    "from": from_id,
                    "to": to_id
                }
            })
            # Add to existing to avoid duplicates
            existing_edges.add((from_id, to_id))
            existing_edges.add((to_id, from_id))
    
    print(f"[Enricher] Generated {len(new_relations)} new relations")
    
    if dry_run:
        print("[Enricher] DRY RUN - not writing to file")
        # Show sample
        print("\nSample relations:")
        for rel in new_relations[:10]:
            print(f"  {rel['relation']['from']} --{rel['relation']['type']}--> {rel['relation']['to']}")
    else:
        # Append to graph.jsonl
        graph_path = os.path.join(r"C:\NEVEN\ontology", domain, "graph.jsonl")
        with open(graph_path, 'a', encoding='utf-8') as f:
            for rel in new_relations:
                f.write(json.dumps(rel, ensure_ascii=False) + "\n")
        print(f"[Enricher] Wrote {len(new_relations)} relations to {graph_path}")
    
    return {
        "status": "ok",
        "orphans_found": len(orphans),
        "new_relations": len(new_relations),
        "dry_run": dry_run
    }


if __name__ == "__main__":
    import sys
    
    domain = sys.argv[1] if len(sys.argv) > 1 else "econometria"
    dry_run = "--apply" not in sys.argv
    
    result = enrich_ontology(domain, dry_run=dry_run)
    print(f"\nResult: {result}")
    
    if dry_run:
        print("\nPara aplicar los cambios, ejecuta:")
        print(f"  python ontology_enricher.py {domain} --apply")
