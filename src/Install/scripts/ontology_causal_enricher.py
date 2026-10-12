"""
NEVEN Ontology Causal Concepts Enricher
=======================================
Conecta entidades huérfanas de causalidad usando conocimiento de Wikipedia.

Conceptos cubiertos:
- Confounder, Collider, Mediator (DAG causal)
- Counterfactual distribution
- Instrumental variables assumptions
- State-space models
- Incidental parameters problem

Fuentes:
- https://en.wikipedia.org/wiki/Confounding
- https://en.wikipedia.org/wiki/Collider_(statistics)
- https://en.wikipedia.org/wiki/Mediation_(statistics)
- Conocimiento de libros de econometría (Wooldridge, Angrist-Pischke)
"""

import json
from pathlib import Path
from collections import defaultdict

# Conocimiento extraído de Wikipedia y libros de econometría
CAUSAL_KNOWLEDGE = {
    # Confounder - relacionado con sesgo, DAG, backdoor, regresión
    "confounder": {
        "related_concepts": [
            "sesgo", "bias", "omitted variable", "variable omitida",
            "backdoor", "dag", "causal", "observational",
            "selection", "endogen", "correlation", "spurious"
        ],
        "relation_type": "related_to"
    },
    
    # Collider - relacionado con sesgo de selección, Berkson's paradox
    "collider": {
        "related_concepts": [
            "selection bias", "sesgo de selección", "berkson",
            "conditioning", "dag", "causal", "backdoor",
            "endogen", "sample selection"
        ],
        "relation_type": "related_to"
    },
    
    # Mediator - relacionado con efectos indirectos, path analysis
    "mediator": {
        "related_concepts": [
            "indirect effect", "efecto indirecto", "direct effect",
            "path analysis", "causal", "mechanism", "channel",
            "treatment effect", "intervention"
        ],
        "relation_type": "related_to"
    },
    
    # Counterfactual - relacionado con potential outcomes, Rubin
    "counterfactual": {
        "related_concepts": [
            "potential outcome", "rubin", "causal effect",
            "treatment effect", "ate", "att", "neyman",
            "missing data", "selection"
        ],
        "relation_type": "related_to"
    },
    
    # State-space - relacionado con Kalman, series de tiempo
    "state-space": {
        "related_concepts": [
            "kalman", "filter", "time series", "serie temporal",
            "arima", "var", "dynamic", "latent", "unobserved"
        ],
        "relation_type": "uses"
    },
    
    # Wold decomposition - relacionado con series de tiempo, MA
    "wold": {
        "related_concepts": [
            "moving average", "ma", "stationary", "estacionario",
            "time series", "arma", "innovation", "white noise"
        ],
        "relation_type": "related_to"
    },
    
    # Incidental parameters - relacionado con panel data, fixed effects
    "incidental parameter": {
        "related_concepts": [
            "panel data", "fixed effect", "efecto fijo",
            "neyman", "scott", "bias", "inconsistent",
            "logit", "probit", "nonlinear"
        ],
        "relation_type": "related_to"
    },
    
    # Sequential exogeneity - relacionado con panel dinámico, GMM
    "sequential exogeneity": {
        "related_concepts": [
            "dynamic panel", "gmm", "arellano", "bond",
            "lagged", "predetermined", "strict exogeneity"
        ],
        "relation_type": "requires"
    },
    
    # Monotonicity - relacionado con LATE, instrumental variables
    "monotonicity": {
        "related_concepts": [
            "late", "local average treatment", "instrumental",
            "complier", "defier", "imbens", "angrist"
        ],
        "relation_type": "required_for"
    },
    
    # Compliers/Defiers - relacionado con IV, LATE
    "complier": {
        "related_concepts": [
            "instrumental variable", "late", "treatment effect",
            "monotonicity", "iv", "2sls", "wald"
        ],
        "relation_type": "related_to"
    },
    
    # Cross-fitting - relacionado con machine learning, double ML
    "cross-fitting": {
        "related_concepts": [
            "machine learning", "double ml", "debiased",
            "sample splitting", "cross validation", "lasso"
        ],
        "relation_type": "uses"
    },
    
    # Regularization bias - relacionado con penalización, ML
    "regularization": {
        "related_concepts": [
            "lasso", "ridge", "penalty", "shrinkage",
            "machine learning", "bias", "variance tradeoff"
        ],
        "relation_type": "causes"
    },
    
    # Spatial spillover - relacionado con econometría espacial
    "spatial spillover": {
        "related_concepts": [
            "spatial", "neighbor", "spillover", "sar",
            "spatial lag", "contagion", "network"
        ],
        "relation_type": "related_to"
    },
    
    # Effect modification - relacionado con heterogeneidad
    "effect modification": {
        "related_concepts": [
            "heterogeneity", "interaction", "subgroup",
            "treatment effect", "moderator", "cate"
        ],
        "relation_type": "related_to"
    }
}

# Paquetes R especializados
R_PACKAGES_CAUSAL = {
    "hdm": ["lasso", "high dimensional", "double selection", "post-lasso"],
    "doubleml": ["double machine learning", "debiased", "neyman orthogonal", "cross-fitting"],
    "estimatr": ["robust standard error", "cluster", "iv", "2sls", "heteroscedasticity"],
    "counterfactual": ["counterfactual", "distributional", "quantile", "decomposition"],
    "fwildclusterboot": ["wild bootstrap", "cluster robust", "few clusters", "inference"],
    "kfas": ["kalman filter", "state space", "time series", "structural"],
    "svars": ["structural var", "svar", "identification", "impulse response"]
}


def load_graph(graph_path):
    """Carga entidades y relaciones del grafo."""
    entities = {}
    relations = []
    connected = set()
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get('op') == 'create' and 'entity' in rec:
                    e = rec['entity']
                    entities[e['id']] = e
                elif rec.get('op') == 'relate':
                    r = rec['relation']
                    relations.append(r)
                    connected.add(r['from'])
                    connected.add(r['to'])
            except:
                continue
    
    return entities, relations, connected


def normalize(text):
    """Normaliza texto para búsqueda."""
    import re
    return re.sub(r'[_\-\(\)\[\]]', ' ', text.lower()).strip()


def find_matches(keywords, entities, min_match=1):
    """Encuentra entidades que matchean keywords."""
    matches = []
    for eid, ent in entities.items():
        name = normalize(ent.get('properties', {}).get('name', eid))
        desc = normalize(ent.get('properties', {}).get('description', ''))
        text = name + ' ' + desc
        
        match_count = 0
        for kw in keywords:
            if kw.lower() in text:
                match_count += 1
        
        if match_count >= min_match:
            matches.append((eid, match_count))
    
    # Ordenar por número de matches
    matches.sort(key=lambda x: -x[1])
    return [m[0] for m in matches]


def main():
    graph_path = Path("C:/NEVEN/ontology/econometria/graph.jsonl")
    
    print("=== Causal Concepts Enricher ===")
    print("Fuente: Wikipedia + libros econometría")
    print()
    
    # Cargar grafo
    entities, relations, connected = load_graph(str(graph_path))
    orphans = {eid: entities[eid] for eid in entities if eid not in connected}
    
    print(f"Entidades: {len(entities)}")
    print(f"Huérfanos: {len(orphans)}")
    print()
    
    # Set de pares existentes
    existing = set()
    for r in relations:
        existing.add((r['from'], r['to']))
        existing.add((r['to'], r['from']))
    
    new_relations = []
    
    # Procesar huérfanos usando conocimiento causal
    for eid, ent in orphans.items():
        name = normalize(ent.get('properties', {}).get('name', eid))
        
        # Buscar en conocimiento causal
        for concept_key, knowledge in CAUSAL_KNOWLEDGE.items():
            if concept_key in name or concept_key.replace('-', ' ') in name:
                keywords = knowledge['related_concepts']
                rel_type = knowledge['relation_type']
                
                matches = find_matches(keywords, entities, min_match=1)
                
                if matches:
                    print(f"\n{ent.get('properties', {}).get('name', eid)}:")
                    
                    for target_id in matches[:8]:
                        if target_id == eid:
                            continue
                        if (eid, target_id) in existing:
                            continue
                        
                        target_name = entities[target_id].get('properties', {}).get('name', target_id)
                        new_relations.append({
                            'type': rel_type,
                            'from': eid,
                            'to': target_id
                        })
                        existing.add((eid, target_id))
                        existing.add((target_id, eid))
                        print(f"  + {rel_type} -> {target_name}")
                break
        
        # Buscar paquetes R
        pkg_name = ent.get('properties', {}).get('name', '').lower()
        if ent.get('type') == 'RPackage' and pkg_name in R_PACKAGES_CAUSAL:
            keywords = R_PACKAGES_CAUSAL[pkg_name]
            matches = find_matches(keywords, entities, min_match=1)
            
            if matches:
                print(f"\nRPackage {pkg_name}:")
                
                for target_id in matches[:8]:
                    if target_id == eid:
                        continue
                    if (eid, target_id) in existing:
                        continue
                    
                    target_name = entities[target_id].get('properties', {}).get('name', target_id)
                    new_relations.append({
                        'type': 'implements',
                        'from': eid,
                        'to': target_id
                    })
                    existing.add((eid, target_id))
                    existing.add((target_id, eid))
                    print(f"  + implements -> {target_name}")
    
    # Resumen
    print(f"\n=== Resumen ===")
    print(f"Nuevas relaciones: {len(new_relations)}")
    
    if new_relations:
        # Contar por tipo
        by_type = defaultdict(int)
        for r in new_relations:
            by_type[r['type']] += 1
        print("Por tipo:")
        for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
        
        # Guardar
        print(f"\nGuardando en {graph_path}...")
        with open(graph_path, 'a', encoding='utf-8') as f:
            for rel in new_relations:
                rec = {'op': 'relate', 'relation': rel}
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        print("Listo!")


if __name__ == "__main__":
    main()
