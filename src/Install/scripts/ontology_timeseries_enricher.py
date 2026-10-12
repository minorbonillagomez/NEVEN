#!/usr/bin/env python3
"""
NEVEN Time Series Enricher
Agrega conceptos de series de tiempo faltantes a la ontología.
"""

import json
from pathlib import Path
from datetime import datetime

GRAPH_PATH = Path("C:/NEVEN/ontology/econometria/graph.jsonl")

# Entidades de series de tiempo a agregar
TIMESERIES_ENTITIES = [
    # Correlograma y funciones de autocorrelación
    {
        "id": "concept_correlograma",
        "type": "Concept",
        "name": "Correlograma",
        "description": "Gráfico que muestra la función de autocorrelación (ACF) o autocorrelación parcial (PACF) de una serie de tiempo. Útil para identificar el orden de modelos ARIMA.",
        "domain": "econometria",
        "keywords": ["correlograma", "correlogram", "grafico acf", "grafico pacf"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "concept_acf",
        "type": "Concept",
        "name": "Función de Autocorrelación (ACF)",
        "description": "Mide la correlación entre una serie de tiempo y sus valores rezagados. El ACF en el rezago k es la correlación entre Yt e Yt-k.",
        "domain": "econometria",
        "keywords": ["acf", "autocorrelation function", "funcion de autocorrelacion"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "concept_pacf",
        "type": "Concept",
        "name": "Función de Autocorrelación Parcial (PACF)",
        "description": "Mide la correlación entre Yt e Yt-k después de eliminar el efecto de los rezagos intermedios. Útil para identificar el orden p de un modelo AR.",
        "domain": "econometria",
        "keywords": ["pacf", "partial autocorrelation", "autocorrelacion parcial"],
        "source": "TimeSeries-Enricher"
    },
    # Modelos ARIMA
    {
        "id": "model_arima",
        "type": "Model",
        "name": "Modelo ARIMA",
        "description": "Modelo Autorregresivo Integrado de Media Móvil. Combina componentes AR(p), diferenciación I(d) y MA(q) para modelar series de tiempo no estacionarias.",
        "domain": "econometria",
        "keywords": ["arima", "autoregressive integrated moving average"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "model_ar",
        "type": "Model",
        "name": "Modelo Autorregresivo AR(p)",
        "description": "Modelo donde el valor actual depende linealmente de sus p valores pasados más un término de error.",
        "domain": "econometria",
        "keywords": ["ar", "autoregressive", "autorregresivo"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "model_ma",
        "type": "Model",
        "name": "Modelo de Media Móvil MA(q)",
        "description": "Modelo donde el valor actual depende linealmente de q errores pasados.",
        "domain": "econometria",
        "keywords": ["ma", "moving average", "media movil"],
        "source": "TimeSeries-Enricher"
    },
    # Tests de raíz unitaria
    {
        "id": "test_adf",
        "type": "Test",
        "name": "Test Dickey-Fuller Aumentado (ADF)",
        "description": "Prueba de raíz unitaria que determina si una serie de tiempo es estacionaria. H0: la serie tiene raíz unitaria (no estacionaria).",
        "domain": "econometria",
        "keywords": ["adf", "dickey-fuller", "augmented dickey-fuller", "raiz unitaria"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "test_kpss",
        "type": "Test",
        "name": "Test KPSS",
        "description": "Prueba de estacionariedad. H0: la serie es estacionaria. Complemento del test ADF.",
        "domain": "econometria",
        "keywords": ["kpss", "kwiatkowski", "phillips", "schmidt", "shin"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "test_phillips_perron",
        "type": "Test",
        "name": "Test Phillips-Perron",
        "description": "Prueba de raíz unitaria robusta a heterocedasticidad y autocorrelación en los errores.",
        "domain": "econometria",
        "keywords": ["phillips-perron", "pp test", "raiz unitaria"],
        "source": "TimeSeries-Enricher"
    },
    # Conceptos adicionales
    {
        "id": "concept_raiz_unitaria",
        "type": "Concept",
        "name": "Raíz Unitaria",
        "description": "Una serie tiene raíz unitaria si su polinomio característico tiene una raíz igual a 1. Indica no estacionariedad y la necesidad de diferenciar.",
        "domain": "econometria",
        "keywords": ["raiz unitaria", "unit root", "no estacionariedad"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "concept_diferenciacion",
        "type": "Concept",
        "name": "Diferenciación",
        "description": "Técnica para convertir una serie no estacionaria en estacionaria. La primera diferencia es Δyt = yt - yt-1.",
        "domain": "econometria",
        "keywords": ["diferenciacion", "differencing", "primera diferencia"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "concept_white_noise",
        "type": "Concept",
        "name": "Ruido Blanco",
        "description": "Proceso estocástico con media cero, varianza constante y sin autocorrelación. Los residuos de un buen modelo deben ser ruido blanco.",
        "domain": "econometria",
        "keywords": ["ruido blanco", "white noise", "innovaciones"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "test_ljung_box",
        "type": "Test",
        "name": "Test Ljung-Box",
        "description": "Prueba si un grupo de autocorrelaciones son conjuntamente cero. Útil para verificar si los residuos son ruido blanco.",
        "domain": "econometria",
        "keywords": ["ljung-box", "box-pierce", "portmanteau"],
        "source": "TimeSeries-Enricher"
    },
    # Funciones R
    {
        "id": "rfunc_acf",
        "type": "RFunction",
        "name": "acf()",
        "description": "Función de R que calcula y grafica la función de autocorrelación de una serie de tiempo.",
        "domain": "econometria",
        "keywords": ["acf", "r function"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "rfunc_pacf",
        "type": "RFunction",
        "name": "pacf()",
        "description": "Función de R que calcula y grafica la función de autocorrelación parcial de una serie de tiempo.",
        "domain": "econometria",
        "keywords": ["pacf", "r function"],
        "source": "TimeSeries-Enricher"
    },
    {
        "id": "rfunc_adf_test",
        "type": "RFunction",
        "name": "adf.test()",
        "description": "Función del paquete tseries que realiza el test Dickey-Fuller Aumentado.",
        "domain": "econometria",
        "keywords": ["adf.test", "tseries"],
        "source": "TimeSeries-Enricher"
    },
]

# Relaciones entre las entidades
TIMESERIES_RELATIONS = [
    # Correlograma
    ("concept_correlograma", "visualizes", "concept_acf"),
    ("concept_correlograma", "visualizes", "concept_pacf"),
    ("concept_correlograma", "used_for", "model_arima"),
    
    # ACF y PACF
    ("concept_acf", "related_to", "concept_pacf"),
    ("concept_acf", "detects", "concept_autocorrelacion"),
    ("concept_pacf", "identifies_order_of", "model_ar"),
    ("concept_acf", "identifies_order_of", "model_ma"),
    
    # ARIMA y componentes
    ("model_arima", "contains", "model_ar"),
    ("model_arima", "contains", "model_ma"),
    ("model_arima", "requires", "concept_diferenciacion"),
    ("model_ar", "related_to", "concept_autocorrelacion"),
    
    # Estacionariedad
    ("concept_raiz_unitaria", "indicates", "concept_estacionariedad"),
    ("concept_diferenciacion", "removes", "concept_raiz_unitaria"),
    ("test_adf", "tests_for", "concept_raiz_unitaria"),
    ("test_kpss", "tests_for", "concept_estacionariedad"),
    ("test_phillips_perron", "tests_for", "concept_raiz_unitaria"),
    
    # Ruido blanco
    ("concept_white_noise", "related_to", "concept_acf"),
    ("test_ljung_box", "tests_for", "concept_white_noise"),
    
    # Funciones R
    ("rfunc_acf", "computes", "concept_acf"),
    ("rfunc_pacf", "computes", "concept_pacf"),
    ("rfunc_adf_test", "performs", "test_adf"),
    
    # Conexiones con entidades existentes
    ("concept_correlograma", "related_to", "concept_autocorrelacion"),
    ("concept_correlograma", "related_to", "concept_estacionariedad"),
    ("model_arima", "related_to", "concept_estacionariedad"),
    ("test_adf", "related_to", "test_durbin_watson"),
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
    print("NEVEN Time Series Enricher")
    print("Conceptos de series de tiempo: ACF, PACF, Correlograma, ARIMA, etc.")
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
    
    print(f"\n[1/2] Creando entidades de series de tiempo...")
    with open(GRAPH_PATH, 'a', encoding='utf-8') as f:
        for entity in TIMESERIES_ENTITIES:
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
        for from_id, rel_type, to_id in TIMESERIES_RELATIONS:
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
