"""
NEVEN Ontology Knowledge Enricher
=================================
Enriquece entidades huérfanas usando conocimiento predefinido.
NO usa APIs externas - todo el conocimiento está codificado aquí.

Uso:
    python ontology_knowledge_enricher.py [--domain econometria] [--dry-run]
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


# Paquetes de R y sus capacidades (conocimiento de CRAN + libros)
R_PACKAGES = {
    # Base y diagnósticos
    "stats": ["linear regression", "t test", "anova", "correlation", "mco", "ols"],
    "car": ["vif", "variance inflation", "heteroscedasticity", "diagnostics"],
    "lmtest": ["breusch pagan", "durbin watson", "reset test", "wald test", "coeftest"],
    "sandwich": ["robust standard errors", "hac", "newey west", "heteroscedasticity consistent"],
    "mass": ["robust regression", "negative binomial", "glm", "rlm", "stepaic"],
    
    # Econometría aplicada (Wooldridge, Greene)
    "aer": ["instrumental variables", "2sls", "tobit", "ivreg", "endogeneity"],
    "plm": ["panel data", "fixed effects", "random effects", "hausman test", "pooled ols"],
    "sampleselection": ["heckman", "selection model", "sample selection", "heckit"],
    "systemfit": ["sur", "3sls", "simultaneous equations", "system estimation"],
    "gmm": ["generalized method of moments", "gmm", "moment conditions", "overidentification"],
    
    # Series de tiempo (Hamilton)
    "tsa": ["time series", "arima", "periodogram"],
    "vars": ["var", "vector autoregression", "granger causality", "impulse response"],
    "tseries": ["unit root", "adf test", "kpss test", "stationarity"],
    "forecast": ["arima", "forecast", "exponential smoothing"],
    "urca": ["cointegration", "johansen", "unit root", "vecm"],
    
    # Inferencia causal
    "rdrobust": ["regression discontinuity", "rdd", "local polynomial"],
    "matchit": ["propensity score", "matching", "nearest neighbor", "cem"],
    "dagitty": ["dag", "causal diagram", "instrumental variables", "backdoor"],
    "mediation": ["mediation analysis", "indirect effects", "causal mediation"],
    
    # Encuestas y muestreo
    "survey": ["survey design", "weighted regression", "complex sampling", "stratified"],
    
    # Espacial
    "sf": ["spatial features", "geospatial", "simple features", "gis"],
    "spdep": ["spatial autocorrelation", "moran test", "spatial weights", "neighbors"],
    "spatialreg": ["spatial regression", "sar", "spatial lag", "spatial error", "sem"],
    
    # Machine Learning / Clasificación
    "nnet": ["neural network", "multinomial logit", "multinom", "feed forward"],
    "randomforest": ["random forest", "classification", "variable importance"],
    "glmnet": ["lasso", "ridge", "elastic net", "regularization", "penalized"],
    
    # Otros econométricos
    "quantreg": ["quantile regression", "median regression", "rq"],
    "survival": ["survival analysis", "cox model", "hazard", "kaplan meier"],
    "boot": ["bootstrap", "resampling", "confidence interval"],
    "mgcv": ["gam", "generalized additive", "smooth", "spline"]
}

# Supuestos econométricos y conceptos relacionados
ASSUMPTIONS = {
    "homoscedasticity": ["constant variance", "heteroscedasticity", "white test", "breusch pagan"],
    "no_multicollinearity": ["vif", "variance inflation", "collinearity", "condition number"],
    "parallel_trends": ["difference in differences", "did", "treatment effect"],
    "positivity": ["propensity score", "overlap", "common support"],
    "ignorability": ["selection on observables", "unconfoundedness", "cia"]
}


def load_graph(graph_path: str) -> Tuple[Dict[str, dict], Set[str]]:
    """Carga entidades y IDs conectados."""
    entities = {}
    connected = set()
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("op") == "create" and "entity" in rec:
                    e = rec["entity"]
                    eid = e.get("id", "")
                    if eid and eid not in entities:
                        entities[eid] = e
                elif rec.get("op") == "relate":
                    r = rec["relation"]
                    connected.add(r.get("from", ""))
                    connected.add(r.get("to", ""))
            except:
                continue
    
    return entities, connected


def normalize(text: str) -> str:
    """Normaliza para búsqueda."""
    import re
    return re.sub(r'[_\-\(\)\[\]]', ' ', text.lower()).strip()


def find_matches(keywords: List[str], entities: Dict[str, dict]) -> List[str]:
    """Encuentra entidades que contienen alguna keyword."""
    matches = []
    for eid, ent in entities.items():
        name = normalize(ent.get("properties", {}).get("name", eid))
        desc = normalize(ent.get("properties", {}).get("description", ""))
        text = name + " " + desc
        
        for kw in keywords:
            kw_words = kw.split()
            if len(kw_words) >= 2:
                # Para frases, verificar que todas las palabras estén
                if all(w in text for w in kw_words):
                    matches.append(eid)
                    break
            elif kw in text:
                matches.append(eid)
                break
    
    return matches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="econometria")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    graph_path = Path(f"C:/NEVEN/ontology/{args.domain}/graph.jsonl")
    if not graph_path.exists():
        print(f"ERROR: {graph_path} not found")
        return
    
    print("=== Knowledge-Based Enricher ===")
    
    # Cargar
    entities, connected = load_graph(str(graph_path))
    orphans = [eid for eid in entities if eid not in connected]
    print(f"Entities: {len(entities)}, Orphans: {len(orphans)}")
    
    # Set para evitar duplicados
    existing = set()
    with open(graph_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '"relate"' in line:
                try:
                    r = json.loads(line)["relation"]
                    existing.add((r["from"], r["to"]))
                except:
                    pass
    
    new_rels = []
    
    # Procesar paquetes R huérfanos
    for eid in orphans:
        ent = entities[eid]
        if ent.get("type") != "RPackage":
            continue
        
        pkg_name = ent.get("properties", {}).get("name", "").lower()
        if pkg_name not in R_PACKAGES:
            continue
        
        keywords = R_PACKAGES[pkg_name]
        matches = find_matches(keywords, entities)
        
        print(f"\n{pkg_name}: {len(matches)} matches")
        
        for target_id in matches[:10]:
            if target_id == eid:
                continue
            if (eid, target_id) in existing:
                continue
            
            target_name = entities[target_id].get("properties", {}).get("name", target_id)
            new_rels.append({"type": "implements", "from": eid, "to": target_id})
            existing.add((eid, target_id))
            print(f"  + implements -> {target_name}")
    
    # Procesar supuestos econométricos huérfanos
    for eid in orphans:
        ent = entities[eid]
        if ent.get("type") != "Assumption":
            continue
        
        # Buscar en el diccionario de supuestos
        for assumption_key, keywords in ASSUMPTIONS.items():
            if assumption_key in eid.lower():
                matches = find_matches(keywords, entities)
                print(f"\n{eid}: {len(matches)} matches")
                
                for target_id in matches[:8]:
                    if target_id == eid:
                        continue
                    if (eid, target_id) in existing:
                        continue
                    
                    target_name = entities[target_id].get("properties", {}).get("name", target_id)
                    new_rels.append({"type": "tested_by", "from": eid, "to": target_id})
                    existing.add((eid, target_id))
                    print(f"  + tested_by -> {target_name}")
                break
    
    # Resumen
    print(f"\n=== Summary ===")
    print(f"New relations: {len(new_rels)}")
    
    # Guardar
    if not args.dry_run and new_rels:
        print(f"\nAppending to {graph_path}...")
        with open(graph_path, 'a', encoding='utf-8') as f:
            for rel in new_rels:
                rec = {"op": "relate", "relation": rel}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("Done!")
    elif args.dry_run:
        print("[DRY-RUN] No changes")


if __name__ == "__main__":
    main()
