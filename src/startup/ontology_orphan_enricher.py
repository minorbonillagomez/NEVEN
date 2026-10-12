#!/usr/bin/env python3
"""
Enriquecedor de huérfanos para NEVEN Ontología.

Este script conecta los nodos huérfanos restantes usando conocimiento
de Wikipedia y traducciones de conceptos al español/inglés.

Fuente: Wikipedia (búsquedas manuales de conceptos relacionados)
"""

import json
import os
from typing import Dict, List, Set, Tuple
from datetime import datetime

# Ruta al grafo de ontología
GRAPH_PATH = r"C:\NEVEN\ontology\econometria\graph.jsonl"

# Conocimiento extraído de Wikipedia para los 17 huérfanos
# Formato: {orphan_id: [(target_id, relation_type), ...]}
ORPHAN_RELATIONS = {
    # concept_effect_modification -> Interaction (statistics) en Wikipedia
    # "Effect modification occurs when the effect of a single exposure on an outcome 
    #  depends on the values of another variable"
    "concept_effect_modification": [
        ("concept_interaction", "related_to"),
        ("concept_moderation", "related_to"),
        ("concept_confounding", "contrasts_with"),
        ("concept_causal_interaction", "related_to"),
        ("model_regression", "applies_to"),
        ("test_interaction_test", "tested_by"),
    ],
    
    # concept_hypercube -> OLAP cube, Latin hypercube sampling en Wikipedia
    # "Term hypercube is sometimes used for data with more than three dimensions"
    # "Latin hypercube sampling is a statistical method for Monte Carlo integration"
    "concept_hypercube": [
        ("technique_latin_hypercube_sampling", "related_to"),
        ("technique_monte_carlo", "used_in"),
        ("concept_multidimensional_data", "related_to"),
        ("technique_sampling", "related_to"),
        ("concept_olap", "related_to"),
    ],
    
    # concept_nominal_categories -> Nominal scale en Wikipedia
    # Variables categóricas sin orden (género, color, tipo)
    "concept_nominal_categories": [
        ("concept_categorical_variable", "is_a"),
        ("concept_ordinal_scale", "contrasts_with"),
        ("model_logistic_regression", "used_in"),
        ("model_multinomial_logit", "used_in"),
        ("technique_dummy_coding", "encoded_by"),
        ("concept_measurement_scale", "part_of"),
    ],
    
    # concept_precision_variable -> Efficiency (statistics) en Wikipedia
    # Variable que aumenta la precisión del estimador sin ser de interés directo
    "concept_precision_variable": [
        ("concept_efficiency", "related_to"),
        ("concept_variance_reduction", "achieves"),
        ("model_regression", "used_in"),
        ("concept_control_variable", "related_to"),
        ("estimator_ols", "improves"),
    ],
    
    # concept_property_cv1 -> Cross-validation properties
    "concept_property_cv1": [
        ("technique_cross_validation", "property_of"),
        ("technique_loocv", "related_to"),
        ("concept_bias_variance_tradeoff", "related_to"),
        ("concept_overfitting", "prevents"),
    ],
    
    # concept_time_invariant_confounding -> Panel analysis en Wikipedia
    # "Fixed effects estimators are not affected by confounding from 
    #  unmeasured time-invariant factors"
    "concept_time_invariant_confounding": [
        ("model_fixed_effects", "controlled_by"),
        ("model_panel_data", "addressed_in"),
        ("concept_confounding", "is_a"),
        ("concept_unobserved_heterogeneity", "related_to"),
        ("model_random_effects", "partially_controlled_by"),
        ("test_hausman", "tested_by"),
    ],
    
    # func_ls -> ls() en R lista objetos en el environment
    "func_ls": [
        ("func_rm", "related_to"),
        ("func_objects", "equivalent_to"),
        ("concept_r_environment", "operates_on"),
        ("package_base", "part_of"),
    ],
    
    # func_q -> q() en R termina la sesión
    "func_q": [
        ("func_quit", "equivalent_to"),
        ("concept_r_session", "terminates"),
        ("package_base", "part_of"),
    ],
    
    # func_range -> range() en R retorna min y max
    "func_range": [
        ("func_min", "related_to"),
        ("func_max", "related_to"),
        ("concept_descriptive_statistics", "computes"),
        ("package_base", "part_of"),
    ],
    
    # func_rstudent -> Studentized residual en Wikipedia
    # "A studentized residual is the ratio of a residual to an estimate 
    #  of its standard deviation"
    "func_rstudent": [
        ("concept_studentized_residual", "computes"),
        ("func_rstandard", "related_to"),
        ("concept_outlier_detection", "used_for"),
        ("model_linear_regression", "diagnoses"),
        ("concept_leverage", "related_to"),
        ("test_outlier_test", "related_to"),
        ("concept_deletion_residual", "related_to"),
    ],
    
    # func_seq -> seq() en R genera secuencias
    "func_seq": [
        ("func_rep", "related_to"),
        ("concept_sequence", "generates"),
        ("package_base", "part_of"),
        ("concept_vector", "creates"),
    ],
    
    # function_fix -> fix() en R edita objetos interactivamente
    "function_fix": [
        ("func_edit", "related_to"),
        ("concept_r_data_frame", "edits"),
        ("package_utils", "part_of"),
    ],
    
    # pattern_log_properties -> List of logarithmic identities en Wikipedia
    # "These are often known as logarithmic properties"
    "pattern_log_properties": [
        ("concept_logarithm", "properties_of"),
        ("concept_log_transformation", "related_to"),
        ("model_log_linear", "used_in"),
        ("concept_elasticity", "interprets"),
        ("func_log", "implemented_by"),
        ("concept_natural_logarithm", "related_to"),
    ],
    
    # shortcut_set_seed -> set.seed() para reproducibilidad
    "shortcut_set_seed": [
        ("func_set_seed", "implements"),
        ("concept_reproducibility", "ensures"),
        ("concept_random_number_generator", "controls"),
        ("technique_bootstrap", "used_with"),
        ("technique_monte_carlo", "used_with"),
    ],
    
    # var_age -> Variable común en datasets econométricos
    "var_age": [
        ("concept_demographic_variable", "is_a"),
        ("concept_continuous_variable", "is_a"),
        ("model_mincer_equation", "used_in"),
        ("concept_human_capital", "proxies"),
    ],
    
    # var_expend -> Expenditure variable en economía
    "var_expend": [
        ("concept_economic_variable", "is_a"),
        ("concept_education_expenditure", "related_to"),
        ("model_education_production_function", "used_in"),
        ("concept_fiscal_policy", "related_to"),
    ],
    
    # var_motheduc -> Mother's education en economía laboral
    "var_motheduc": [
        ("concept_instrument", "used_as"),
        ("concept_intergenerational_mobility", "measures"),
        ("model_wage_equation", "used_in"),
        ("concept_human_capital", "proxies"),
        ("var_fatheduc", "related_to"),
    ],
}


def load_existing_entities(graph_path: str) -> Set[str]:
    """Carga IDs de entidades existentes."""
    entities = set()
    with open(graph_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get('op') == 'create' and 'entity' in obj:
                entities.add(obj['entity']['id'])
    return entities


def load_existing_relations(graph_path: str) -> Set[Tuple[str, str, str]]:
    """Carga relaciones existentes como set de tuplas (from, to, type)."""
    relations = set()
    with open(graph_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get('op') == 'relate' and 'relation' in obj:
                rel = obj['relation']
                relations.add((
                    rel.get('from', ''),
                    rel.get('to', ''),
                    rel.get('type', '')
                ))
    return relations


def enrich_orphans():
    """Agrega relaciones para los nodos huérfanos."""
    
    print("=" * 60)
    print("NEVEN Orphan Enricher - Basado en Wikipedia")
    print("=" * 60)
    
    # Cargar estado actual
    existing_entities = load_existing_entities(GRAPH_PATH)
    existing_relations = load_existing_relations(GRAPH_PATH)
    
    print(f"\nEntidades existentes: {len(existing_entities)}")
    print(f"Relaciones existentes: {len(existing_relations)}")
    
    # Preparar nuevas relaciones
    new_relations = []
    stats = {
        "orphans_processed": 0,
        "relations_added": 0,
        "relations_skipped_exists": 0,
        "relations_skipped_no_target": 0,
        "by_type": {}
    }
    
    for orphan_id, relations in ORPHAN_RELATIONS.items():
        if orphan_id not in existing_entities:
            print(f"  [SKIP] {orphan_id} no existe en la ontología")
            continue
            
        stats["orphans_processed"] += 1
        
        for target_id, rel_type in relations:
            # Verificar si el target existe
            if target_id not in existing_entities:
                stats["relations_skipped_no_target"] += 1
                continue
            
            # Verificar si la relación ya existe
            if (orphan_id, target_id, rel_type) in existing_relations:
                stats["relations_skipped_exists"] += 1
                continue
            
            # Agregar relación
            new_relations.append({
                "op": "relate",
                "relation": {
                    "type": rel_type,
                    "from": orphan_id,
                    "to": target_id
                }
            })
            
            stats["relations_added"] += 1
            stats["by_type"][rel_type] = stats["by_type"].get(rel_type, 0) + 1
    
    # Escribir nuevas relaciones al archivo
    if new_relations:
        with open(GRAPH_PATH, 'a', encoding='utf-8') as f:
            for rel in new_relations:
                f.write(json.dumps(rel, ensure_ascii=False) + '\n')
    
    # Mostrar resultados
    print(f"\n{'='*60}")
    print("RESULTADOS")
    print(f"{'='*60}")
    print(f"Huérfanos procesados: {stats['orphans_processed']}")
    print(f"Relaciones agregadas: {stats['relations_added']}")
    print(f"  - Saltadas (ya existían): {stats['relations_skipped_exists']}")
    print(f"  - Saltadas (target no existe): {stats['relations_skipped_no_target']}")
    
    if stats["by_type"]:
        print(f"\nPor tipo de relación:")
        for rel_type, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
            print(f"  {rel_type}: {count}")
    
    return stats


if __name__ == "__main__":
    enrich_orphans()
