#!/usr/bin/env python3
"""
NEVEN Classification Diagnostics Enricher
Agrega conceptos de diagnóstico para modelos de clasificación.
"""

import json
from pathlib import Path
from datetime import datetime

GRAPH_PATH = Path("C:/NEVEN/ontology/econometria/graph.jsonl")

# Entidades de diagnóstico de clasificación
CLASSIFICATION_ENTITIES = [
    # Tests de bondad de ajuste
    {
        "id": "test_hosmer_lemeshow",
        "type": "Test",
        "name": "Test de Hosmer-Lemeshow",
        "description": "Prueba de bondad de ajuste para modelos de regresión logística. Compara las probabilidades predichas con las frecuencias observadas agrupando las observaciones en deciles.",
        "domain": "econometria",
        "keywords": ["hosmer-lemeshow", "hosmer lemeshow", "bondad de ajuste", "goodness of fit", "logistic"],
        "source": "Classification-Enricher"
    },
    {
        "id": "concept_goodness_of_fit_test",
        "type": "Concept",
        "name": "Prueba de Bondad de Ajuste",
        "description": "Evaluación estadística de qué tan bien un modelo se ajusta a los datos observados. En clasificación, compara predicciones con resultados reales.",
        "domain": "econometria",
        "keywords": ["bondad de ajuste", "goodness of fit", "model fit"],
        "source": "Classification-Enricher"
    },
    # Curva ROC y AUC
    {
        "id": "concept_roc_curve",
        "type": "Concept",
        "name": "Curva ROC",
        "description": "Receiver Operating Characteristic. Gráfico que muestra la tasa de verdaderos positivos vs falsos positivos para diferentes umbrales de clasificación.",
        "domain": "econometria",
        "keywords": ["roc", "receiver operating characteristic", "curva roc"],
        "source": "Classification-Enricher"
    },
    {
        "id": "metric_auc",
        "type": "Metric",
        "name": "AUC (Área Bajo la Curva ROC)",
        "description": "Area Under the ROC Curve. Métrica que resume el rendimiento del clasificador. AUC=1 es perfecto, AUC=0.5 es aleatorio.",
        "domain": "econometria",
        "keywords": ["auc", "area under curve", "auroc", "roc-auc"],
        "source": "Classification-Enricher"
    },
    # Matriz de confusión y métricas derivadas
    {
        "id": "concept_confusion_matrix",
        "type": "Concept",
        "name": "Matriz de Confusión",
        "description": "Tabla que muestra verdaderos positivos (TP), verdaderos negativos (TN), falsos positivos (FP) y falsos negativos (FN) de un clasificador.",
        "domain": "econometria",
        "keywords": ["matriz de confusion", "confusion matrix", "tabla de contingencia"],
        "source": "Classification-Enricher"
    },
    {
        "id": "metric_sensitivity",
        "type": "Metric",
        "name": "Sensibilidad (Recall)",
        "description": "Tasa de verdaderos positivos. Proporción de positivos reales correctamente identificados. Sensibilidad = TP / (TP + FN).",
        "domain": "econometria",
        "keywords": ["sensibilidad", "sensitivity", "recall", "true positive rate", "tpr"],
        "source": "Classification-Enricher"
    },
    {
        "id": "metric_specificity",
        "type": "Metric",
        "name": "Especificidad",
        "description": "Tasa de verdaderos negativos. Proporción de negativos reales correctamente identificados. Especificidad = TN / (TN + FP).",
        "domain": "econometria",
        "keywords": ["especificidad", "specificity", "true negative rate", "tnr"],
        "source": "Classification-Enricher"
    },
    {
        "id": "metric_precision",
        "type": "Metric",
        "name": "Precisión (Valor Predictivo Positivo)",
        "description": "Proporción de predicciones positivas que son correctas. Precisión = TP / (TP + FP).",
        "domain": "econometria",
        "keywords": ["precision", "positive predictive value", "ppv"],
        "source": "Classification-Enricher"
    },
    {
        "id": "metric_f1_score",
        "type": "Metric",
        "name": "F1 Score",
        "description": "Media armónica de precisión y recall. F1 = 2 * (Precisión * Recall) / (Precisión + Recall). Balancea ambas métricas.",
        "domain": "econometria",
        "keywords": ["f1", "f1-score", "f-score", "f measure"],
        "source": "Classification-Enricher"
    },
    {
        "id": "metric_accuracy",
        "type": "Metric",
        "name": "Exactitud (Accuracy)",
        "description": "Proporción de predicciones correctas. Accuracy = (TP + TN) / Total. Puede ser engañosa con clases desbalanceadas.",
        "domain": "econometria",
        "keywords": ["accuracy", "exactitud", "tasa de acierto"],
        "source": "Classification-Enricher"
    },
    # Brier Score y calibración
    {
        "id": "metric_brier_score",
        "type": "Metric",
        "name": "Brier Score",
        "description": "Error cuadrático medio de las probabilidades predichas. Brier = (1/n) * Σ(p_i - o_i)². Menor es mejor, 0 es perfecto.",
        "domain": "econometria",
        "keywords": ["brier score", "brier", "probabilistic forecast"],
        "source": "Classification-Enricher"
    },
    {
        "id": "concept_calibration",
        "type": "Concept",
        "name": "Calibración de Probabilidades",
        "description": "Qué tan bien las probabilidades predichas reflejan las frecuencias reales. Un modelo calibrado predice P=0.7 para eventos que ocurren 70% del tiempo.",
        "domain": "econometria",
        "keywords": ["calibration", "calibracion", "reliability diagram"],
        "source": "Classification-Enricher"
    },
    # Tipos de errores
    {
        "id": "concept_type_i_error",
        "type": "Concept",
        "name": "Error Tipo I (Falso Positivo)",
        "description": "Rechazar la hipótesis nula cuando es verdadera. En clasificación, predecir positivo cuando el valor real es negativo.",
        "domain": "econometria",
        "keywords": ["error tipo i", "type i error", "falso positivo", "false positive", "alpha"],
        "source": "Classification-Enricher"
    },
    {
        "id": "concept_type_ii_error",
        "type": "Concept",
        "name": "Error Tipo II (Falso Negativo)",
        "description": "No rechazar la hipótesis nula cuando es falsa. En clasificación, predecir negativo cuando el valor real es positivo.",
        "domain": "econometria",
        "keywords": ["error tipo ii", "type ii error", "falso negativo", "false negative", "beta"],
        "source": "Classification-Enricher"
    },
    # Log-likelihood y pseudo R²
    {
        "id": "metric_log_likelihood",
        "type": "Metric",
        "name": "Log-Verosimilitud",
        "description": "Logaritmo de la función de verosimilitud. Mide qué tan probable es observar los datos dado el modelo. Mayor (menos negativo) es mejor.",
        "domain": "econometria",
        "keywords": ["log-likelihood", "log likelihood", "verosimilitud", "likelihood"],
        "source": "Classification-Enricher"
    },
    {
        "id": "metric_pseudo_r2_mcfadden",
        "type": "Metric",
        "name": "Pseudo R² de McFadden",
        "description": "1 - (LL_modelo / LL_nulo). Análogo al R² para modelos de clasificación. Valores 0.2-0.4 indican buen ajuste.",
        "domain": "econometria",
        "keywords": ["pseudo r2", "mcfadden r2", "likelihood ratio index"],
        "source": "Classification-Enricher"
    },
    # Validación cruzada
    {
        "id": "tech_cross_validation",
        "type": "Technique",
        "name": "Validación Cruzada",
        "description": "Técnica para evaluar modelos dividiendo datos en k folds. Cada fold sirve una vez como test mientras los demás entrenan.",
        "domain": "econometria",
        "keywords": ["cross-validation", "validacion cruzada", "k-fold", "cv"],
        "source": "Classification-Enricher"
    },
    {
        "id": "tech_stratified_cv",
        "type": "Technique",
        "name": "Validación Cruzada Estratificada",
        "description": "Validación cruzada que mantiene la proporción de clases en cada fold. Importante para clases desbalanceadas.",
        "domain": "econometria",
        "keywords": ["stratified cv", "validacion estratificada", "stratified k-fold"],
        "source": "Classification-Enricher"
    },
    # Umbral de clasificación
    {
        "id": "concept_classification_threshold",
        "type": "Concept",
        "name": "Umbral de Clasificación",
        "description": "Valor de probabilidad a partir del cual se predice la clase positiva. Por defecto 0.5, pero puede ajustarse según costos de errores.",
        "domain": "econometria",
        "keywords": ["threshold", "umbral", "cutoff", "punto de corte"],
        "source": "Classification-Enricher"
    },
    # Funciones R
    {
        "id": "rfunc_hoslem_test",
        "type": "RFunction",
        "name": "hoslem.test()",
        "description": "Función del paquete ResourceSelection que realiza el test de Hosmer-Lemeshow.",
        "domain": "econometria",
        "keywords": ["hoslem.test", "resourceselection"],
        "source": "Classification-Enricher"
    },
    {
        "id": "rfunc_roc",
        "type": "RFunction",
        "name": "roc()",
        "description": "Función del paquete pROC para calcular y graficar curvas ROC.",
        "domain": "econometria",
        "keywords": ["roc", "proc", "curva roc"],
        "source": "Classification-Enricher"
    },
    {
        "id": "rfunc_confusionMatrix",
        "type": "RFunction",
        "name": "confusionMatrix()",
        "description": "Función del paquete caret que calcula matriz de confusión y múltiples métricas de clasificación.",
        "domain": "econometria",
        "keywords": ["confusionmatrix", "caret"],
        "source": "Classification-Enricher"
    },
]

# Relaciones entre las entidades
CLASSIFICATION_RELATIONS = [
    # Hosmer-Lemeshow
    ("test_hosmer_lemeshow", "is_a", "concept_goodness_of_fit_test"),
    ("test_hosmer_lemeshow", "applies_to", "model_logit"),
    ("test_hosmer_lemeshow", "evaluates", "concept_calibration"),
    ("rfunc_hoslem_test", "performs", "test_hosmer_lemeshow"),
    
    # ROC y AUC
    ("metric_auc", "derived_from", "concept_roc_curve"),
    ("concept_roc_curve", "uses", "metric_sensitivity"),
    ("concept_roc_curve", "uses", "metric_specificity"),
    ("rfunc_roc", "computes", "concept_roc_curve"),
    
    # Matriz de confusión
    ("metric_sensitivity", "derived_from", "concept_confusion_matrix"),
    ("metric_specificity", "derived_from", "concept_confusion_matrix"),
    ("metric_precision", "derived_from", "concept_confusion_matrix"),
    ("metric_accuracy", "derived_from", "concept_confusion_matrix"),
    ("metric_f1_score", "combines", "metric_precision"),
    ("metric_f1_score", "combines", "metric_sensitivity"),
    ("rfunc_confusionMatrix", "computes", "concept_confusion_matrix"),
    
    # Errores
    ("concept_type_i_error", "related_to", "metric_specificity"),
    ("concept_type_ii_error", "related_to", "metric_sensitivity"),
    
    # Calibración
    ("concept_calibration", "measured_by", "metric_brier_score"),
    ("concept_calibration", "tested_by", "test_hosmer_lemeshow"),
    
    # Log-likelihood
    ("metric_pseudo_r2_mcfadden", "uses", "metric_log_likelihood"),
    ("metric_log_likelihood", "evaluates", "model_logit"),
    
    # Validación
    ("tech_stratified_cv", "is_a", "tech_cross_validation"),
    ("tech_cross_validation", "evaluates", "metric_accuracy"),
    
    # Conexiones con entidades existentes
    ("concept_roc_curve", "related_to", "model_logit"),
    ("concept_roc_curve", "related_to", "model_probit"),
    ("metric_auc", "related_to", "model_logit"),
    ("concept_confusion_matrix", "related_to", "model_logit"),
    ("concept_classification_threshold", "affects", "metric_sensitivity"),
    ("concept_classification_threshold", "affects", "metric_specificity"),
]


def load_existing_ids():
    """Carga los IDs existentes en el grafo."""
    existing = set()
    if GRAPH_PATH.exists():
        with open(GRAPH_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if record.get("op") == "create" and "entity" in record:
                        existing.add(record["entity"]["id"])
                except:
                    pass
    return existing


def main():
    print("=" * 70)
    print("NEVEN Classification Diagnostics Enricher")
    print("Hosmer-Lemeshow, ROC-AUC, Matriz de Confusión, etc.")
    print("=" * 70)
    
    existing_ids = load_existing_ids()
    print(f"\nEntidades existentes: {len(existing_ids)}")
    
    # Contar relaciones existentes
    relation_count = 0
    if GRAPH_PATH.exists():
        with open(GRAPH_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if record.get("op") == "relate":
                        relation_count += 1
                except:
                    pass
    print(f"Relaciones existentes: {relation_count}")
    
    # Agregar entidades
    entities_created = 0
    entities_skipped = 0
    
    print(f"\n[1/2] Creando entidades de diagnóstico de clasificación...")
    with open(GRAPH_PATH, 'a', encoding='utf-8') as f:
        for entity in CLASSIFICATION_ENTITIES:
            if entity["id"] in existing_ids:
                entities_skipped += 1
                continue
            
            record = {
                "op": "create",
                "entity": entity,
                "timestamp": datetime.now().isoformat()
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            existing_ids.add(entity["id"])
            entities_created += 1
            print(f"  + {entity['id']}: {entity['name']}")
    
    # Agregar relaciones
    relations_created = 0
    relations_skipped = 0
    relations_missing_target = 0
    
    print(f"\n[2/2] Creando relaciones...")
    with open(GRAPH_PATH, 'a', encoding='utf-8') as f:
        for from_id, rel_type, to_id in CLASSIFICATION_RELATIONS:
            # Verificar que ambos extremos existen
            if from_id not in existing_ids:
                relations_missing_target += 1
                continue
            if to_id not in existing_ids:
                relations_missing_target += 1
                print(f"  ! {from_id} -> {to_id}: target no existe")
                continue
            
            record = {
                "op": "relate",
                "relation": {
                    "from": from_id,
                    "to": to_id,
                    "type": rel_type
                },
                "timestamp": datetime.now().isoformat()
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            relations_created += 1
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESULTADOS")
    print("=" * 70)
    print(f"Entidades creadas:    {entities_created}")
    print(f"Entidades saltadas:   {entities_skipped} (ya existían)")
    print(f"Relaciones creadas:   {relations_created}")
    print(f"Relaciones saltadas:  {relations_missing_target} (target no existe)")


if __name__ == "__main__":
    main()
