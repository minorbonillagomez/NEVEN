#!/usr/bin/env python3
"""
convert_anyplot.py — Convierte el repositorio anyplot en ontología de gráficos para NEVEN

Este script procesa la carpeta plots/ de anyplot y genera archivos YAML de ontología
bilingües (ES/EN) compatibles con el sistema RAG de NEVEN.

Uso:
    python convert_anyplot.py --input external/anyplot/plots --output docs/ontologia/graficos

Salida:
    - Un archivo YAML por cada tipo de gráfico
    - Un archivo _catalog.yaml con el índice completo
    - Traducciones en español e inglés para todos los campos
"""

import os
import re
import yaml
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

# ============================================================================
# DICCIONARIO DE TRADUCCIONES BASE
# ============================================================================

# Traducciones de tipos de gráficos comunes (ampliable)
CHART_TRANSLATIONS = {
    # Básicos
    "scatter": {"en": "Scatter Plot", "es": "Diagrama de Dispersión"},
    "bar": {"en": "Bar Chart", "es": "Gráfico de Barras"},
    "line": {"en": "Line Chart", "es": "Gráfico de Líneas"},
    "area": {"en": "Area Chart", "es": "Gráfico de Área"},
    "pie": {"en": "Pie Chart", "es": "Gráfico Circular"},
    "donut": {"en": "Donut Chart", "es": "Gráfico de Dona"},
    "histogram": {"en": "Histogram", "es": "Histograma"},
    "heatmap": {"en": "Heatmap", "es": "Mapa de Calor"},
    "box": {"en": "Box Plot", "es": "Diagrama de Caja"},
    "violin": {"en": "Violin Plot", "es": "Diagrama de Violín"},
    
    # Distribución
    "density": {"en": "Density Plot", "es": "Gráfico de Densidad"},
    "ridgeline": {"en": "Ridgeline Plot", "es": "Gráfico de Crestas"},
    "swarm": {"en": "Swarm Plot", "es": "Diagrama de Enjambre"},
    "strip": {"en": "Strip Plot", "es": "Diagrama de Tiras"},
    "raincloud": {"en": "Raincloud Plot", "es": "Diagrama de Nube de Lluvia"},
    
    # Correlación/Relación
    "bubble": {"en": "Bubble Chart", "es": "Gráfico de Burbujas"},
    "contour": {"en": "Contour Plot", "es": "Gráfico de Contorno"},
    "hexbin": {"en": "Hexbin Plot", "es": "Diagrama Hexagonal"},
    
    # Comparación
    "lollipop": {"en": "Lollipop Chart", "es": "Gráfico de Piruleta"},
    "dumbbell": {"en": "Dumbbell Chart", "es": "Gráfico de Mancuerna"},
    "bullet": {"en": "Bullet Chart", "es": "Gráfico de Bala"},
    "radar": {"en": "Radar Chart", "es": "Gráfico de Radar"},
    
    # Temporal
    "timeseries": {"en": "Time Series", "es": "Serie Temporal"},
    "candlestick": {"en": "Candlestick Chart", "es": "Gráfico de Velas"},
    "gantt": {"en": "Gantt Chart", "es": "Diagrama de Gantt"},
    "sparkline": {"en": "Sparkline", "es": "Minigráfico"},
    
    # Jerárquico/Redes
    "treemap": {"en": "Treemap", "es": "Mapa de Árbol"},
    "sunburst": {"en": "Sunburst Chart", "es": "Gráfico de Explosión Solar"},
    "sankey": {"en": "Sankey Diagram", "es": "Diagrama de Sankey"},
    "chord": {"en": "Chord Diagram", "es": "Diagrama de Cuerdas"},
    "network": {"en": "Network Graph", "es": "Grafo de Red"},
    "dendrogram": {"en": "Dendrogram", "es": "Dendrograma"},
    
    # Geográficos
    "choropleth": {"en": "Choropleth Map", "es": "Mapa Coroplético"},
    "map": {"en": "Map", "es": "Mapa"},
    
    # Estadísticos
    "qq": {"en": "Q-Q Plot", "es": "Gráfico Q-Q"},
    "pp": {"en": "P-P Plot", "es": "Gráfico P-P"},
    "roc": {"en": "ROC Curve", "es": "Curva ROC"},
    "confusion": {"en": "Confusion Matrix", "es": "Matriz de Confusión"},
    "forest": {"en": "Forest Plot", "es": "Gráfico de Bosque"},
    "funnel": {"en": "Funnel Plot", "es": "Gráfico de Embudo"},
    "residual": {"en": "Residual Plot", "es": "Gráfico de Residuos"},
    
    # Otros
    "waterfall": {"en": "Waterfall Chart", "es": "Gráfico de Cascada"},
    "waffle": {"en": "Waffle Chart", "es": "Gráfico de Waffle"},
    "wordcloud": {"en": "Word Cloud", "es": "Nube de Palabras"},
    "venn": {"en": "Venn Diagram", "es": "Diagrama de Venn"},
    "gauge": {"en": "Gauge Chart", "es": "Gráfico de Medidor"},
    "polar": {"en": "Polar Chart", "es": "Gráfico Polar"},
    "ternary": {"en": "Ternary Plot", "es": "Diagrama Ternario"},
    "parallel": {"en": "Parallel Coordinates", "es": "Coordenadas Paralelas"},
    "surface": {"en": "3D Surface", "es": "Superficie 3D"},
}

# Traducciones de dominios/tags
DOMAIN_TRANSLATIONS = {
    "statistics": {"en": "Statistics", "es": "Estadística"},
    "general": {"en": "General", "es": "General"},
    "finance": {"en": "Finance", "es": "Finanzas"},
    "science": {"en": "Science", "es": "Ciencia"},
    "machine-learning": {"en": "Machine Learning", "es": "Aprendizaje Automático"},
    "biology": {"en": "Biology", "es": "Biología"},
    "medicine": {"en": "Medicine", "es": "Medicina"},
    "engineering": {"en": "Engineering", "es": "Ingeniería"},
    "geography": {"en": "Geography", "es": "Geografía"},
    "business": {"en": "Business", "es": "Negocios"},
    "time-series": {"en": "Time Series", "es": "Series Temporales"},
    "distribution": {"en": "Distribution", "es": "Distribución"},
    "comparison": {"en": "Comparison", "es": "Comparación"},
    "correlation": {"en": "Correlation", "es": "Correlación"},
    "composition": {"en": "Composition", "es": "Composición"},
    "ranking": {"en": "Ranking", "es": "Clasificación"},
    "flow": {"en": "Flow", "es": "Flujo"},
    "hierarchy": {"en": "Hierarchy", "es": "Jerarquía"},
    "network": {"en": "Network", "es": "Red"},
    "geospatial": {"en": "Geospatial", "es": "Geoespacial"},
}

# Traducciones de tipos de datos
DATA_TYPE_TRANSLATIONS = {
    "numeric": {"en": "Numeric", "es": "Numérico"},
    "categorical": {"en": "Categorical", "es": "Categórico"},
    "continuous": {"en": "Continuous", "es": "Continuo"},
    "discrete": {"en": "Discrete", "es": "Discreto"},
    "temporal": {"en": "Temporal", "es": "Temporal"},
    "bivariate": {"en": "Bivariate", "es": "Bivariado"},
    "multivariate": {"en": "Multivariate", "es": "Multivariado"},
    "ordinal": {"en": "Ordinal", "es": "Ordinal"},
    "binary": {"en": "Binary", "es": "Binario"},
    "text": {"en": "Text", "es": "Texto"},
    "hierarchical": {"en": "Hierarchical", "es": "Jerárquico"},
    "network": {"en": "Network", "es": "Red"},
    "geospatial": {"en": "Geospatial", "es": "Geoespacial"},
}

# Traducciones de características/features
FEATURE_TRANSLATIONS = {
    "basic": {"en": "Basic", "es": "Básico"},
    "interactive": {"en": "Interactive", "es": "Interactivo"},
    "animated": {"en": "Animated", "es": "Animado"},
    "2d": {"en": "2D", "es": "2D"},
    "3d": {"en": "3D", "es": "3D"},
    "correlation": {"en": "Correlation", "es": "Correlación"},
    "regression": {"en": "Regression", "es": "Regresión"},
    "trend": {"en": "Trend", "es": "Tendencia"},
    "grouped": {"en": "Grouped", "es": "Agrupado"},
    "stacked": {"en": "Stacked", "es": "Apilado"},
    "normalized": {"en": "Normalized", "es": "Normalizado"},
    "horizontal": {"en": "Horizontal", "es": "Horizontal"},
    "vertical": {"en": "Vertical", "es": "Vertical"},
    "multi": {"en": "Multiple", "es": "Múltiple"},
}

# ============================================================================
# TRADUCCIÓN AUTOMÁTICA (fallback)
# ============================================================================

def translate_text(text: str, target: str = "es") -> str:
    """
    Traduce texto de inglés a español usando reglas simples.
    Para producción, se puede integrar con API de traducción.
    """
    if target == "en":
        return text  # Ya está en inglés
    
    # Traducciones directas comunes en descripciones
    translations = {
        "comparing": "comparando",
        "displaying": "mostrando",
        "showing": "mostrando",
        "analyzing": "analizando",
        "visualizing": "visualizando",
        "plotting": "graficando",
        "relationship": "relación",
        "distribution": "distribución",
        "correlation": "correlación",
        "comparison": "comparación",
        "data": "datos",
        "values": "valores",
        "variables": "variables",
        "categories": "categorías",
        "points": "puntos",
        "bars": "barras",
        "lines": "líneas",
        "colors": "colores",
        "axis": "eje",
        "chart": "gráfico",
        "plot": "diagrama",
        "graph": "gráfico",
    }
    
    result = text.lower()
    for en, es in translations.items():
        result = result.replace(en, es)
    
    return result

def get_chart_name_translation(spec_id: str) -> Dict[str, str]:
    """
    Obtiene traducción del nombre del gráfico basado en su ID.
    """
    # Extraer tipo base del ID (ej: 'scatter-basic' -> 'scatter')
    base_type = spec_id.split('-')[0]
    
    if base_type in CHART_TRANSLATIONS:
        base = CHART_TRANSLATIONS[base_type]
    else:
        # Fallback: capitalizar el ID
        base = {
            "en": spec_id.replace('-', ' ').title(),
            "es": spec_id.replace('-', ' ').title()
        }
    
    # Añadir variante si existe
    parts = spec_id.split('-')
    if len(parts) > 1:
        variant = parts[1]
        if variant in FEATURE_TRANSLATIONS:
            return {
                "en": f"{FEATURE_TRANSLATIONS[variant]['en']} {base['en']}",
                "es": f"{base['es']} {FEATURE_TRANSLATIONS[variant]['es']}"
            }
    
    return base

# ============================================================================
# PARSER DE SPECIFICATION.MD
# ============================================================================

def parse_specification_md(md_path: Path) -> Dict[str, Any]:
    """
    Extrae información estructurada del archivo specification.md
    """
    result = {
        "description": "",
        "applications": [],
        "data_requirements": [],
        "notes": [],
        "good_version": []
    }
    
    if not md_path.exists():
        return result
    
    content = md_path.read_text(encoding='utf-8')
    
    # Parsear secciones
    sections = re.split(r'\n##\s+', content)
    
    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue
        
        header = lines[0].lower()
        body = '\n'.join(lines[1:]).strip()
        
        if 'description' in header:
            result["description"] = body
        elif 'applications' in header or 'application' in header:
            # Extraer lista de aplicaciones
            result["applications"] = [
                line.strip().lstrip('- ').strip()
                for line in body.split('\n')
                if line.strip().startswith('-')
            ]
        elif 'data' in header:
            # Extraer requisitos de datos
            for line in body.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('`'):
                    result["data_requirements"].append(line.strip().lstrip('- ').strip())
        elif 'notes' in header or 'note' in header:
            result["notes"] = [
                line.strip().lstrip('- ').strip()
                for line in body.split('\n')
                if line.strip().startswith('-')
            ]
        elif 'good version' in header:
            result["good_version"] = [
                line.strip().lstrip('- ').strip()
                for line in body.split('\n')
                if line.strip().startswith('-')
            ]
    
    return result

# ============================================================================
# PARSER DE SPECIFICATION.YAML
# ============================================================================

def parse_specification_yaml(yaml_path: Path) -> Dict[str, Any]:
    """
    Extrae información del archivo specification.yaml
    """
    result = {
        "spec_id": "",
        "title": "",
        "tags": {},
        "created": "",
        "updated": ""
    }
    
    if not yaml_path.exists():
        return result
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data:
                result.update(data)
    except Exception as e:
        print(f"Warning: Error parsing {yaml_path}: {e}")
    
    return result

# ============================================================================
# DETECTOR DE IMPLEMENTACIONES
# ============================================================================

def detect_implementations(plot_dir: Path) -> Dict[str, Dict[str, str]]:
    """
    Detecta las implementaciones disponibles para un tipo de gráfico.
    Retorna diccionario: {lenguaje: {libreria: ruta_relativa}}
    """
    impl_dir = plot_dir / "implementations"
    implementations = {}
    
    if not impl_dir.exists():
        return implementations
    
    # Mapeo de extensiones a lenguajes
    ext_to_lang = {
        '.py': 'python',
        '.R': 'r',
        '.r': 'r',
        '.jl': 'julia',
        '.js': 'javascript',
        '.ts': 'javascript',
        '.tsx': 'javascript'
    }
    
    # Escanear subdirectorios de implementaciones
    for lang_dir in impl_dir.iterdir():
        if not lang_dir.is_dir():
            continue
        
        lang_name = lang_dir.name
        implementations[lang_name] = {}
        
        for impl_file in lang_dir.iterdir():
            if impl_file.is_file():
                # Extraer nombre de librería del archivo
                lib_name = impl_file.stem  # ej: 'matplotlib', 'plotly'
                rel_path = impl_file.relative_to(plot_dir.parent.parent)
                implementations[lang_name][lib_name] = str(rel_path).replace('\\', '/')
    
    return implementations

# ============================================================================
# INFERENCIA DE USO
# ============================================================================

def infer_use_when(spec_id: str, tags: Dict, description: str) -> Dict[str, List[str]]:
    """
    Infiere cuándo usar este gráfico basado en su ID, tags y descripción.
    Retorna traducciones bilingües.
    """
    use_when = {"en": [], "es": []}
    avoid_when = {"en": [], "es": []}
    
    # Reglas basadas en tipo de gráfico
    base_type = spec_id.split('-')[0]
    
    if base_type == "scatter":
        use_when["en"].extend([
            "Exploring relationship between two continuous variables",
            "Detecting correlations (positive, negative, none)",
            "Identifying outliers in bivariate data"
        ])
        use_when["es"].extend([
            "Explorar relación entre dos variables continuas",
            "Detectar correlaciones (positiva, negativa, ninguna)",
            "Identificar valores atípicos en datos bivariados"
        ])
        avoid_when["en"].extend(["Categorical variables (use bar chart)", "Time series (use line chart)"])
        avoid_when["es"].extend(["Variables categóricas (usar gráfico de barras)", "Series temporales (usar gráfico de líneas)"])
    
    elif base_type == "bar":
        use_when["en"].extend([
            "Comparing values across categories",
            "Showing rankings or distributions",
            "Displaying discrete data"
        ])
        use_when["es"].extend([
            "Comparar valores entre categorías",
            "Mostrar rankings o distribuciones",
            "Visualizar datos discretos"
        ])
        avoid_when["en"].extend(["Continuous data over time (use line chart)", "Part-to-whole relationships (use pie)"])
        avoid_when["es"].extend(["Datos continuos en el tiempo (usar líneas)", "Relaciones parte-todo (usar circular)"])
    
    elif base_type == "line":
        use_when["en"].extend([
            "Showing trends over time",
            "Displaying continuous data changes",
            "Comparing multiple series"
        ])
        use_when["es"].extend([
            "Mostrar tendencias en el tiempo",
            "Visualizar cambios en datos continuos",
            "Comparar múltiples series"
        ])
    
    elif base_type == "heatmap":
        use_when["en"].extend([
            "Visualizing matrix data",
            "Showing correlations between variables",
            "Displaying density patterns"
        ])
        use_when["es"].extend([
            "Visualizar datos matriciales",
            "Mostrar correlaciones entre variables",
            "Mostrar patrones de densidad"
        ])
    
    elif base_type in ["box", "violin"]:
        use_when["en"].extend([
            "Comparing distributions across groups",
            "Identifying outliers and spread",
            "Showing median, quartiles, and range"
        ])
        use_when["es"].extend([
            "Comparar distribuciones entre grupos",
            "Identificar valores atípicos y dispersión",
            "Mostrar mediana, cuartiles y rango"
        ])
    
    elif base_type == "histogram":
        use_when["en"].extend([
            "Showing frequency distribution of continuous data",
            "Understanding data shape (normal, skewed, bimodal)",
            "Identifying common values and outliers"
        ])
        use_when["es"].extend([
            "Mostrar distribución de frecuencia de datos continuos",
            "Entender la forma de los datos (normal, sesgada, bimodal)",
            "Identificar valores comunes y atípicos"
        ])
    
    elif base_type == "pie" or base_type == "donut":
        use_when["en"].extend([
            "Showing part-to-whole relationships",
            "Displaying composition with few categories (≤6)",
            "Emphasizing proportions"
        ])
        use_when["es"].extend([
            "Mostrar relaciones parte-todo",
            "Visualizar composición con pocas categorías (≤6)",
            "Enfatizar proporciones"
        ])
        avoid_when["en"].extend(["Many categories (>6)", "Comparing values (use bar)"])
        avoid_when["es"].extend(["Muchas categorías (>6)", "Comparar valores (usar barras)"])
    
    # Si no hay reglas específicas, usar descripción
    if not use_when["en"] and description:
        use_when["en"].append(description[:200])
        use_when["es"].append(description[:200])  # TODO: traducir
    
    return {"use_when": use_when, "avoid_when": avoid_when}

# ============================================================================
# INFERENCIA DE REQUISITOS DE DATOS
# ============================================================================

def infer_data_requirements(spec_id: str, tags: Dict) -> Dict[str, Any]:
    """
    Infiere los requisitos de datos basado en el tipo de gráfico.
    """
    base_type = spec_id.split('-')[0]
    
    requirements = {
        "min_columns": 1,
        "max_columns": None,
        "column_types": [],
        "recommended_rows": {"min": 10, "max": 1000}
    }
    
    # Inferir por tipo
    if base_type == "scatter":
        requirements.update({
            "min_columns": 2,
            "column_types": ["numeric", "numeric"],
            "recommended_rows": {"min": 20, "max": 5000}
        })
    elif base_type == "bar":
        requirements.update({
            "min_columns": 2,
            "column_types": ["categorical", "numeric"],
            "recommended_rows": {"min": 3, "max": 30}
        })
    elif base_type == "line":
        requirements.update({
            "min_columns": 2,
            "column_types": ["numeric|temporal", "numeric"],
            "recommended_rows": {"min": 10, "max": 10000}
        })
    elif base_type == "histogram":
        requirements.update({
            "min_columns": 1,
            "column_types": ["numeric"],
            "recommended_rows": {"min": 30, "max": 100000}
        })
    elif base_type == "heatmap":
        requirements.update({
            "min_columns": 3,
            "column_types": ["categorical|numeric", "categorical|numeric", "numeric"],
            "recommended_rows": {"min": 10, "max": 10000}
        })
    elif base_type in ["box", "violin"]:
        requirements.update({
            "min_columns": 2,
            "column_types": ["categorical", "numeric"],
            "recommended_rows": {"min": 30, "max": 10000}
        })
    elif base_type in ["pie", "donut"]:
        requirements.update({
            "min_columns": 2,
            "column_types": ["categorical", "numeric"],
            "recommended_rows": {"min": 2, "max": 10}
        })
    
    return requirements

# ============================================================================
# GENERADOR DE KEYWORDS
# ============================================================================

def generate_keywords(spec_id: str, tags: Dict, description: str) -> Dict[str, List[str]]:
    """
    Genera keywords bilingües para búsqueda RAG.
    """
    keywords = {"en": [], "es": []}
    
    # Desde el ID
    parts = spec_id.replace('-', ' ').split()
    for part in parts:
        if part in CHART_TRANSLATIONS:
            keywords["en"].append(CHART_TRANSLATIONS[part]["en"].lower())
            keywords["es"].append(CHART_TRANSLATIONS[part]["es"].lower())
        elif part in FEATURE_TRANSLATIONS:
            keywords["en"].append(FEATURE_TRANSLATIONS[part]["en"].lower())
            keywords["es"].append(FEATURE_TRANSLATIONS[part]["es"].lower())
        else:
            keywords["en"].append(part)
            keywords["es"].append(part)
    
    # Desde tags
    if tags:
        for tag_category, tag_values in tags.items():
            if isinstance(tag_values, list):
                for tag in tag_values:
                    if tag in DOMAIN_TRANSLATIONS:
                        keywords["en"].append(DOMAIN_TRANSLATIONS[tag]["en"].lower())
                        keywords["es"].append(DOMAIN_TRANSLATIONS[tag]["es"].lower())
                    elif tag in DATA_TYPE_TRANSLATIONS:
                        keywords["en"].append(DATA_TYPE_TRANSLATIONS[tag]["en"].lower())
                        keywords["es"].append(DATA_TYPE_TRANSLATIONS[tag]["es"].lower())
                    else:
                        keywords["en"].append(tag)
                        keywords["es"].append(tag)
    
    # Eliminar duplicados manteniendo orden
    keywords["en"] = list(dict.fromkeys(keywords["en"]))
    keywords["es"] = list(dict.fromkeys(keywords["es"]))
    
    return keywords

# ============================================================================
# GENERADOR DE ONTOLOGÍA
# ============================================================================

def generate_ontology_yaml(plot_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Genera el archivo YAML de ontología para un tipo de gráfico.
    """
    spec_id = plot_dir.name
    
    # Parsear fuentes
    md_data = parse_specification_md(plot_dir / "specification.md")
    yaml_data = parse_specification_yaml(plot_dir / "specification.yaml")
    
    # Detectar implementaciones
    implementations = detect_implementations(plot_dir)
    
    # Obtener nombre traducido
    name_i18n = get_chart_name_translation(spec_id)
    
    # Inferir uso
    usage = infer_use_when(spec_id, yaml_data.get("tags", {}), md_data["description"])
    
    # Inferir requisitos de datos
    data_reqs = infer_data_requirements(spec_id, yaml_data.get("tags", {}))
    
    # Generar keywords
    keywords = generate_keywords(spec_id, yaml_data.get("tags", {}), md_data["description"])
    
    # Construir ontología
    ontology = {
        "entity_type": "ChartType",
        "id": spec_id,
        
        # Nombre bilingüe
        "name": {
            "en": yaml_data.get("title", name_i18n["en"]),
            "es": name_i18n["es"]
        },
        
        # Descripción bilingüe
        "description": {
            "en": md_data["description"],
            "es": md_data["description"]  # TODO: traducción real
        },
        
        # Aliases para búsqueda
        "aliases": {
            "en": [spec_id, spec_id.replace('-', ' '), name_i18n["en"].lower()],
            "es": [spec_id, spec_id.replace('-', ' '), name_i18n["es"].lower()]
        },
        
        # Cuándo usar / no usar
        "use_when": usage["use_when"],
        "avoid_when": usage["avoid_when"],
        
        # Aplicaciones de ejemplo
        "applications": {
            "en": md_data["applications"][:5] if md_data["applications"] else [],
            "es": md_data["applications"][:5] if md_data["applications"] else []  # TODO: traducir
        },
        
        # Requisitos de datos
        "data_requirements": data_reqs,
        
        # Tags originales de anyplot
        "tags": yaml_data.get("tags", {}),
        
        # Keywords para RAG
        "keywords": keywords,
        
        # Implementaciones disponibles
        "implementations": implementations,
        
        # Notas técnicas
        "notes": md_data["notes"][:3] if md_data["notes"] else [],
        
        # Metadatos
        "source": "anyplot",
        "anyplot_updated": yaml_data.get("updated", ""),
    }
    
    return ontology

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Convierte anyplot a ontología NEVEN")
    parser.add_argument("--input", "-i", required=True, help="Directorio de plots de anyplot")
    parser.add_argument("--output", "-o", required=True, help="Directorio de salida para ontologías")
    parser.add_argument("--limit", "-l", type=int, default=0, help="Limitar número de gráficos (0=todos)")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return 1
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Procesar cada tipo de gráfico
    catalog = []
    plot_dirs = sorted(input_dir.iterdir())
    
    if args.limit > 0:
        plot_dirs = plot_dirs[:args.limit]
    
    print(f"Processing {len(list(plot_dirs))} chart types...")
    
    for i, plot_dir in enumerate(sorted(input_dir.iterdir())):
        if not plot_dir.is_dir():
            continue
        
        if args.limit > 0 and i >= args.limit:
            break
        
        spec_id = plot_dir.name
        print(f"  [{i+1}] {spec_id}")
        
        try:
            ontology = generate_ontology_yaml(plot_dir, output_dir)
            
            # Guardar YAML individual
            output_file = output_dir / f"{spec_id}.yaml"
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(ontology, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            # Añadir al catálogo
            catalog.append({
                "id": spec_id,
                "name": ontology["name"],
                "implementations": list(ontology["implementations"].keys()),
                "tags": ontology.get("tags", {}).get("plot_type", [])
            })
            
        except Exception as e:
            print(f"    Error processing {spec_id}: {e}")
    
    # Guardar catálogo
    catalog_file = output_dir / "_catalog.yaml"
    with open(catalog_file, 'w', encoding='utf-8') as f:
        yaml.dump({
            "version": "1.0",
            "source": "anyplot",
            "total_charts": len(catalog),
            "charts": catalog
        }, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"\n✓ Generated {len(catalog)} ontology files in {output_dir}")
    print(f"✓ Catalog saved to {catalog_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())
